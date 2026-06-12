from sentence_transformers import CrossEncoder

from backend.models.chunk import Chunk

reranker_model = CrossEncoder("BAAI/bge-reranker-v2-m3")


def rerank_chunks(query: str, chunks: list[Chunk], top_k: int = 5) -> list[Chunk]:
    if not chunks:
        return []

    pairs = [(query, chunk.text) for chunk in chunks]
    scores = reranker_model.predict(pairs)

    for chunk, score in zip(chunks, scores):
        chunk.reranker_score = float(score)

    ranked = sorted(chunks, key=lambda c: c.reranker_score, reverse=True)
    filtered = [chunk for chunk in ranked if chunk.reranker_score > 0.3]
    return filtered[:top_k]
