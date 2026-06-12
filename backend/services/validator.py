from backend.models.chunk import Chunk


def validate_citations(response: dict, retrieved_chunks: list[Chunk]) -> tuple[bool, list[str]]:
    chunk_map = {chunk.chunk_id: chunk.text for chunk in retrieved_chunks}
    issues: list[str] = []

    for item in response.get("explanation", []):
        chunk_id = item.get("chunk_id", "")
        quote = item.get("quote", "")
        claim = item.get("claim", "")

        if chunk_id not in chunk_map:
            issues.append(f"Claim '{claim[:50]}...' references non-existent chunk: {chunk_id}")
            continue

        chunk_text = chunk_map[chunk_id].lower()
        if quote.lower() not in chunk_text and quote[:15].lower() not in chunk_text:
            issues.append(f"Quote not found in chunk {chunk_id}: '{quote[:60]}...'")

    return len(issues) == 0, issues


def apply_validation_result(response: dict, is_valid: bool, issues: list[str]) -> dict:
    if not is_valid:
        if response.get("confidence") == "high":
            response["confidence"] = "medium"
        response["validation_warnings"] = issues
    return response
