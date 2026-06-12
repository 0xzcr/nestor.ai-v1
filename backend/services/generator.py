import asyncio
import json
import random
import re

import httpx

from backend.config import get_settings
from backend.models.chunk import Chunk

GENERATION_SYSTEM_PROMPT = """
You are an anatomy tutor. You have been given a numbered set of source chunks retrieved from trusted anatomy textbooks.

STRICT RULES — violating any of these is a critical failure:
- Answer ONLY using information present in the provided source chunks.
- Every sentence in your explanation MUST reference at least one chunk by its exact CHUNK_ID.
- If the source chunks do not contain sufficient information to answer the question, respond with confidence: "insufficient" and leave explanation empty.
- NEVER use your own anatomical knowledge.
- NEVER infer, extrapolate, or assume beyond what the chunks explicitly state.
- NEVER say "based on my knowledge", "generally", or "typically" without a chunk citation.
- If two chunks state conflicting information, include both in conflicting_sources and note the conflict.
- Do not add markdown formatting inside JSON string values.

Respond ONLY with valid JSON matching this exact schema. No markdown fences, no preamble:
{
  "direct_answer": "one to two sentence direct answer to the question",
  "explanation": [
    {
      "claim": "a single factual statement",
      "chunk_id": "exact CHUNK_ID this came from",
      "quote": "the exact phrase from the chunk that supports this claim"
    }
  ],
  "confidence": "high | medium | low | insufficient",
  "conflicting_sources": null
}

confidence meanings:
- high: all claims are directly stated in chunks, no inference needed
- medium: most claims are direct, one or two required minor inference
- low: significant inference was needed, treat answer with caution
- insufficient: chunks do not contain enough information to answer
""".strip()

settings = get_settings()


def format_chunks_for_prompt(chunks: list[Chunk]) -> str:
    formatted = "SOURCE CHUNKS:\n\n"
    for chunk in chunks:
        formatted += f"[{chunk.chunk_id}] Source: {chunk.source_display}, {chunk.page_ref}\n"
        formatted += f"{chunk.text}\n\n"
    return formatted


def parse_generation_response(raw: str) -> dict:
    clean = raw.strip()
    clean = re.sub(r"^```json\s*", "", clean)
    clean = re.sub(r"^```\s*", "", clean)
    clean = re.sub(r"\s*```$", "", clean)
    clean = clean.strip()
    try:
        return json.loads(clean)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Model returned non-JSON output: {raw[:200]}") from exc


async def call_cerebras_with_retry(
    prompt: str,
    system: str,
    max_retries: int = 3,
    temperature: int = 0,
) -> str:
    """Call Cerebras API for generation with retry logic and error handling."""
    settings = get_settings()
    
    if not settings.cerebras_api_key:
        raise RuntimeError("CEREBRAS_API_KEY is not configured.")
    
    for attempt in range(max_retries):
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    "https://api.cerebras.ai/v1/messages",
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {settings.cerebras_api_key}",
                    },
                    json={
                        "model": "claude-3.5-sonnet",
                        "max_tokens": 2048,
                        "temperature": temperature,
                        "system": system,
                        "messages": [
                            {"role": "user", "content": prompt}
                        ],
                    },
                )
                response.raise_for_status()
                payload = response.json()
                
                # Extract text from Cerebras response
                if "content" not in payload or not payload["content"]:
                    raise ValueError(f"Invalid Cerebras response: {payload}")
                
                return payload["content"][0]["text"]
        except Exception as exc:
            if "429" in str(exc) or "rate_limit" in str(exc).lower():
                if attempt == max_retries - 1:
                    raise RuntimeError(f"Cerebras rate limit exceeded after {max_retries} retries.") from exc
                wait = (2**attempt) + random.uniform(0, 1)
                await asyncio.sleep(wait)
            elif "401" in str(exc) or "unauthorized" in str(exc).lower():
                raise RuntimeError("Cerebras API key is invalid or expired.") from exc
            else:
                raise
    raise RuntimeError("Max retries exceeded for Cerebras API call.")


async def generate_answer(query: str, chunks: list[Chunk], gemini_call) -> dict:
    prompt = f"QUESTION:\n{query}\n\n{format_chunks_for_prompt(chunks)}"
    raw_response = await gemini_call(prompt=prompt, system=GENERATION_SYSTEM_PROMPT, temperature=0)
    try:
        return parse_generation_response(raw_response)
    except ValueError:
        retry_system = (
            f"{GENERATION_SYSTEM_PROMPT}\n\nYour previous response was not valid JSON. "
            "You MUST respond with only a JSON object, no other text."
        )
        try:
            retry_raw = await gemini_call(prompt=prompt, system=retry_system, temperature=0)
            return parse_generation_response(retry_raw)
        except ValueError:
            return {
                "direct_answer": "",
                "explanation": [],
                "confidence": "insufficient",
                "conflicting_sources": None,
                "message": "The model returned an invalid response format.",
            }
