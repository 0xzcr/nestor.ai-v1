from __future__ import annotations

import asyncio
from typing import Iterable

import google.generativeai as genai


def format_query_for_embedding(query: str) -> str:
    return f"query: {query.strip()}"


def format_document_for_embedding(content: str, title: str | None = None) -> str:
    return content.strip()


async def embed_texts(
    texts: Iterable[str],
    *,
    api_key: str,
    model: str,
    output_dimensionality: int,
) -> list[list[float]]:
    """Embed texts using Google's Gemini embedding-001 model (wrapped async)."""
    def _embed_sync() -> list[list[float]]:
        genai.configure(api_key=api_key)
        text_list = list(texts)
        embeddings = []
        
        for text in text_list:
            result = genai.embed_content(
                model=model,
                content=text,
                task_type="semantic_similarity"
            )
            embeddings.append(result["embedding"])
        
        return embeddings
    
    # Run sync function in thread pool to avoid blocking event loop
    return await asyncio.to_thread(_embed_sync)
