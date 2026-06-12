from dataclasses import dataclass, field


@dataclass
class Chunk:
    chunk_id: str
    source: str
    source_display: str
    page_ref: str
    text: str
    score: float
    reranker_score: float = field(default=0.0)
