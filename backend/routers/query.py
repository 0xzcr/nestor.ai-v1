import asyncio
import json

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse

from models.query import QueryRequest
from routers.auth import CurrentUser, get_current_user
from services.cache import (
    get_exact_cache,
    get_semantic_cache,
    set_exact_cache,
    set_semantic_cache,
)
from services.fetcher import fetch_all_sources
from services.generator import generate_answer
from services.qdrant_client import user_has_uploads
from services.query_analyzer import analyze_query
from services.reranker import rerank_chunks
from services.validator import apply_validation_result, validate_citations

router = APIRouter(prefix="", tags=["query"])


def insufficient_response() -> dict:
    return {
        "confidence": "insufficient",
        "message": "This question couldn't be answered from the available sources. Try uploading a relevant textbook chapter.",
        "direct_answer": "",
        "explanation": [],
        "conflicting_sources": None,
    }


async def run_query_pipeline(request: QueryRequest, current_user: CurrentUser, app_state) -> dict:
    user_id = current_user.id
    query_embedding = await app_state.embed_text(request.query)

    cached = await get_exact_cache(request.query, app_state.redis_client)
    if cached:
        return cached

    cached = await get_semantic_cache(
        query_embedding,
        app_state.qdrant_client,
        threshold=app_state.settings.query_cache_semantic_threshold,
    )
    if cached:
        return cached

    has_uploads = await user_has_uploads(user_id, app_state.qdrant_client)
    analysis = await analyze_query(request.query, app_state.call_cerebras_safe, has_user_uploads=has_uploads)
    if not analysis["is_anatomy"]:
        return {"error": "out_of_scope", "message": "This product covers anatomy only."}

    chunks = await fetch_all_sources(
        analysis["sub_questions"],
        analysis["sources_needed"],
        user_id,
        query_embedding,
        app_state.qdrant_client,
        has_uploads,
    )

    top_chunks = rerank_chunks(request.query, chunks)
    if len(top_chunks) < 2:
        return insufficient_response()

    response = await generate_answer(request.query, top_chunks, app_state.call_cerebras_safe)
    is_valid, issues = validate_citations(response, top_chunks)
    response = apply_validation_result(response, is_valid, issues)

    await set_exact_cache(request.query, response, app_state.redis_client)
    await set_semantic_cache(request.query, query_embedding, response, app_state.qdrant_client)
    return response


@router.post("/query")
async def query(
    request: QueryRequest,
    http_request: Request,
    current_user: CurrentUser = Depends(get_current_user),
):
    return await run_query_pipeline(request, current_user, http_request.app.state)


@router.post("/query/stream")
async def query_stream(
    request: QueryRequest,
    http_request: Request,
    current_user: CurrentUser = Depends(get_current_user),
):
    async def event_generator():
        yield f"data: {json.dumps({'type': 'answer_start'})}\n\n"
        response = await run_query_pipeline(request, current_user, http_request.app.state)
        if response.get("error"):
            yield f"data: {json.dumps({'type': 'error', 'data': response})}\n\n"
            yield f"data: {json.dumps({'type': 'done'})}\n\n"
            return

        yield f"data: {json.dumps({'type': 'answer_text', 'text': response.get('direct_answer', response.get('message', ''))})}\n\n"
        yield f"data: {json.dumps({'type': 'citations', 'data': response})}\n\n"
        yield f"data: {json.dumps({'type': 'done'})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
