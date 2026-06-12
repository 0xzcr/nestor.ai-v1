from __future__ import annotations

import logging
from typing import Any

from qdrant_client import AsyncQdrantClient
from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    MatchValue,
    PayloadSchemaType,
    PointStruct,
    VectorParams,
)

from backend.config import get_settings
from backend.models.chunk import Chunk

logger = logging.getLogger(__name__)

PRELOADED_COLLECTION = "anatomy_preloaded"
USER_UPLOADS_COLLECTION = "anatomy_user_uploads"
QUERY_CACHE_COLLECTION = "query_cache"


def create_qdrant_client() -> AsyncQdrantClient:
    settings = get_settings()
    return AsyncQdrantClient(url=settings.qdrant_url, api_key=settings.qdrant_api_key)


async def ensure_collections(client: AsyncQdrantClient) -> None:
    settings = get_settings()
    collections = {
        PRELOADED_COLLECTION: VectorParams(
            size=settings.embedding_dimensions,
            distance=Distance.COSINE,
        ),
        USER_UPLOADS_COLLECTION: VectorParams(
            size=settings.embedding_dimensions,
            distance=Distance.COSINE,
        ),
        QUERY_CACHE_COLLECTION: VectorParams(
            size=settings.embedding_dimensions,
            distance=Distance.COSINE,
        ),
    }
    existing = {item.name for item in (await client.get_collections()).collections}
    for name, vectors in collections.items():
        if name not in existing:
            await client.create_collection(collection_name=name, vectors_config=vectors)

    await client.create_payload_index(PRELOADED_COLLECTION, "source", PayloadSchemaType.KEYWORD)
    await client.create_payload_index(PRELOADED_COLLECTION, "chapter", PayloadSchemaType.KEYWORD)
    await client.create_payload_index(PRELOADED_COLLECTION, "section", PayloadSchemaType.TEXT)
    await client.create_payload_index(PRELOADED_COLLECTION, "page_ref", PayloadSchemaType.TEXT)
    await client.create_payload_index(PRELOADED_COLLECTION, "chunk_id", PayloadSchemaType.KEYWORD)

    await client.create_payload_index(USER_UPLOADS_COLLECTION, "user_id", PayloadSchemaType.KEYWORD)
    await client.create_payload_index(USER_UPLOADS_COLLECTION, "filename", PayloadSchemaType.KEYWORD)
    await client.create_payload_index(USER_UPLOADS_COLLECTION, "page_ref", PayloadSchemaType.TEXT)
    await client.create_payload_index(USER_UPLOADS_COLLECTION, "chunk_id", PayloadSchemaType.KEYWORD)

    await client.create_payload_index(QUERY_CACHE_COLLECTION, "query_hash", PayloadSchemaType.KEYWORD)
    await client.create_payload_index(QUERY_CACHE_COLLECTION, "answer_json", PayloadSchemaType.TEXT)
    await client.create_payload_index(QUERY_CACHE_COLLECTION, "created_at", PayloadSchemaType.INTEGER)


def build_user_filter(current_user_id: str) -> Filter:
    return Filter(
        must=[FieldCondition(key="user_id", match=MatchValue(value=current_user_id))]
    )


def assert_user_filter(user_filter: Filter | None) -> None:
    if user_filter is None or not user_filter.must:
        raise AssertionError("anatomy_user_uploads queries require a user_id filter.")
    has_user_id = any(
        condition.key == "user_id" and isinstance(condition.match, MatchValue)
        for condition in user_filter.must
        if isinstance(condition, FieldCondition)
    )
    if not has_user_id:
        raise AssertionError("anatomy_user_uploads queries require a user_id filter.")


def _to_chunk(payload: dict[str, Any], score: float, source_override: str | None = None) -> Chunk:
    return Chunk(
        chunk_id=payload["chunk_id"],
        source=source_override or payload.get("source", "user_upload"),
        source_display=payload.get("source_display", payload.get("filename", "Unknown source")),
        page_ref=payload.get("page_ref", "Unknown page"),
        text=payload["text"],
        score=score,
    )


async def fetch_from_qdrant_preloaded(
    query_embedding: list[float],
    source: str,
    qdrant_client: AsyncQdrantClient,
    limit: int = 8,
) -> list[Chunk]:
    results = await qdrant_client.search(
        collection_name=PRELOADED_COLLECTION,
        query_vector=query_embedding,
        query_filter=Filter(must=[FieldCondition(key="source", match=MatchValue(value=source))]),
        limit=limit,
    )
    return [_to_chunk(result.payload, result.score, source_override=source) for result in results]


async def fetch_from_user_uploads(
    query_embedding: list[float],
    user_id: str,
    qdrant_client: AsyncQdrantClient,
    limit: int = 8,
) -> list[Chunk]:
    user_filter = build_user_filter(user_id)
    assert_user_filter(user_filter)
    results = await qdrant_client.search(
        collection_name=USER_UPLOADS_COLLECTION,
        query_vector=query_embedding,
        query_filter=user_filter,
        limit=limit,
    )
    return [_to_chunk(result.payload, result.score, source_override="user_upload") for result in results]


async def user_has_uploads(user_id: str, qdrant_client: AsyncQdrantClient) -> bool:
    user_filter = build_user_filter(user_id)
    assert_user_filter(user_filter)
    points, _ = await qdrant_client.scroll(
        collection_name=USER_UPLOADS_COLLECTION,
        scroll_filter=user_filter,
        limit=1,
        with_payload=False,
        with_vectors=False,
    )
    return bool(points)
