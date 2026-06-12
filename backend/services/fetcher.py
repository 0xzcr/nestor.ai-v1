import asyncio
import logging

from backend.services.qdrant_client import fetch_from_qdrant_preloaded, fetch_from_user_uploads

logger = logging.getLogger(__name__)


async def fetch_all_sources(
    sub_questions: list[str],
    sources: list[str],
    user_id: str,
    query_embedding: list[float],
    qdrant_client,
    has_user_uploads: bool,
) -> list[dict]:
    tasks = []

    if "openstax" in sources:
        tasks.append(fetch_from_qdrant_preloaded(query_embedding, "openstax", qdrant_client))
    if "ncbi" in sources:
        tasks.append(fetch_from_qdrant_preloaded(query_embedding, "ncbi", qdrant_client))
    if "teachmeanatomy" in sources:
        tasks.append(fetch_from_qdrant_preloaded(query_embedding, "teachmeanatomy", qdrant_client))
    if has_user_uploads:
        tasks.append(fetch_from_user_uploads(query_embedding, user_id, qdrant_client))

    results = await asyncio.gather(
        *[asyncio.wait_for(task, timeout=2.0) for task in tasks],
        return_exceptions=True,
    )

    chunks = []
    for result in results:
        if isinstance(result, Exception):
            if isinstance(result, asyncio.TimeoutError):
                logger.warning("Source fetch timed out; continuing with remaining sources.")
            else:
                logger.exception("Source fetch failed: %s", result)
            continue
        chunks.extend(result)

    return chunks
