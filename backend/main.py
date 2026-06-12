import asyncio
from contextlib import asynccontextmanager

import redis.asyncio as redis
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config import get_settings
from backend.routers import query as query_router
from backend.routers import upload as upload_router
from backend.services.embeddings import embed_texts, format_query_for_embedding
from backend.services.generator import call_cerebras_with_retry
from backend.services.qdrant_client import create_qdrant_client, ensure_collections

settings = get_settings()

# Validate required API keys at startup
if not settings.google_api_key:
    raise RuntimeError("GOOGLE_API_KEY environment variable is required for embeddings.")
if not settings.cerebras_api_key:
    raise RuntimeError("CEREBRAS_API_KEY environment variable is required for generation.")


@asynccontextmanager
async def lifespan(app_instance: FastAPI):
    app_instance.state.settings = settings
    app_instance.state.cerebras_semaphore = asyncio.Semaphore(10)  # Rate limit Cerebras calls
    app_instance.state.qdrant_client = create_qdrant_client()
    app_instance.state.redis_client = redis.from_url(settings.redis_url, decode_responses=True)
    await ensure_collections(app_instance.state.qdrant_client)

    async def embed_text(text: str) -> list[float]:
        response = await embed_texts(
            [format_query_for_embedding(text)],
            api_key=settings.google_api_key,
            model=settings.embedding_model,
            output_dimensionality=settings.embedding_dimensions,
        )
        return response[0]

    async def embed_batch(texts: list[str]) -> list[list[float]]:
        response = await embed_texts(
            texts,
            api_key=settings.google_api_key,
            model=settings.embedding_model,
            output_dimensionality=settings.embedding_dimensions,
        )
        return response

    async def call_cerebras_safe(prompt: str, system: str, temperature: int = 0) -> str:
        async with app_instance.state.cerebras_semaphore:
            return await call_cerebras_with_retry(prompt=prompt, system=system, temperature=temperature)

    app_instance.state.embed_text = embed_text
    app_instance.state.embed_batch = embed_batch
    app_instance.state.call_cerebras_safe = call_cerebras_safe
    yield
    await app_instance.state.qdrant_client.close()
    await app_instance.state.redis_client.close()


app = FastAPI(title="nestor.ai anatomy rag", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(query_router.router)
app.include_router(upload_router.router)
