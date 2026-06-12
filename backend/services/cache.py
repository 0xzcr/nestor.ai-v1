import hashlib
import json
import time
from uuid import uuid4

from qdrant_client.models import PointStruct


def _query_hash(query: str) -> str:
    return hashlib.sha256(query.lower().strip().encode()).hexdigest()


async def get_exact_cache(query: str, redis_client) -> dict | None:
    cached = await redis_client.get(f"query:{_query_hash(query)}")
    if cached:
        return json.loads(cached)
    return None


async def set_exact_cache(
    query: str,
    answer: dict,
    redis_client,
    ttl_seconds: int = 604800,
) -> None:
    await redis_client.setex(f"query:{_query_hash(query)}", ttl_seconds, json.dumps(answer))


async def get_semantic_cache(
    query_embedding: list[float],
    qdrant_client,
    threshold: float = 0.92,
) -> dict | None:
    results = await qdrant_client.search(
        collection_name="query_cache",
        query_vector=query_embedding,
        limit=1,
        score_threshold=threshold,
    )
    if results and results[0].score >= threshold:
        return json.loads(results[0].payload["answer_json"])
    return None


async def set_semantic_cache(
    query: str,
    query_embedding: list[float],
    answer: dict,
    qdrant_client,
) -> None:
    payload = {
        "query_hash": _query_hash(query),
        "answer_json": json.dumps(answer),
        "created_at": int(time.time()),
    }
    await qdrant_client.upsert(
        collection_name="query_cache",
        points=[PointStruct(id=str(uuid4()), vector=query_embedding, payload=payload)],
    )
