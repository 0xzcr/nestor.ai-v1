import os
import tempfile
from uuid import uuid4

import fitz
from llama_index.core import Document
from llama_index.core.node_parser import SentenceSplitter
from qdrant_client.models import PointStruct

from backend.models.chunk import Chunk
from backend.services.embeddings import format_document_for_embedding
from backend.services.qdrant_client import USER_UPLOADS_COLLECTION


def is_scanned_pdf(pdf_path: str) -> bool:
    doc = fitz.open(pdf_path)
    total_chars = 0
    for page in doc:
        total_chars += len(page.get_text())
    avg_chars_per_page = total_chars / max(len(doc), 1)
    return avg_chars_per_page < 100


def chunk_document(text: str, source_id: str, filename: str) -> list[Chunk]:
    splitter = SentenceSplitter(
        chunk_size=500,
        chunk_overlap=50,
        paragraph_separator="\n\n",
    )
    nodes = splitter.get_nodes_from_documents([Document(text=text)])
    chunks: list[Chunk] = []
    for index, node in enumerate(nodes):
        chunk_id = f"{source_id}_{index:04d}"
        chunks.append(
            Chunk(
                chunk_id=chunk_id,
                source="user_upload",
                source_display=f"User upload: {filename}",
                page_ref=f"Section {index + 1}",
                text=node.text,
                score=0.0,
            )
        )
    return chunks


async def ingest_pdf(
    file_path: str,
    user_id: str,
    filename: str,
    embed_batch,
    qdrant_client,
) -> int:
    if is_scanned_pdf(file_path):
        raise ValueError("SCANNED_PDF")

    doc = fitz.open(file_path)
    full_text = "\n\n".join([page.get_text() for page in doc])
    chunks = chunk_document(full_text, f"upload_{user_id[:8]}", filename)
    texts = [format_document_for_embedding(chunk.text, filename) for chunk in chunks]
    embeddings = await embed_batch(texts)

    points = [
        PointStruct(
            id=str(uuid4()),
            vector=embedding,
            payload={
                "user_id": user_id,
                "chunk_id": chunk.chunk_id,
                "filename": filename,
                "source_display": chunk.source_display,
                "text": chunk.text,
                "page_ref": chunk.page_ref,
            },
        )
        for chunk, embedding in zip(chunks, embeddings)
    ]
    await qdrant_client.upsert(collection_name=USER_UPLOADS_COLLECTION, points=points)
    os.remove(file_path)
    return len(chunks)


async def persist_upload_to_temp(upload_file) -> str:
    suffix = ".pdf"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
        while chunk := await upload_file.read(1024 * 1024):
            temp_file.write(chunk)
    await upload_file.seek(0)
    return temp_file.name
