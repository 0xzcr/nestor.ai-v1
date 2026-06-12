import json
from typing import Any

from backend.models.query import QueryAnalysis
from backend.services.source_router import derive_sources

QUERY_ANALYSIS_SYSTEM_PROMPT = """
You are an anatomy query classifier. Extract structured metadata from the user's anatomy question.
Respond ONLY with valid JSON. No markdown, no explanation, no preamble.

Output this exact schema:
{
  "region": "upper_limb | lower_limb | thorax | abdomen | pelvis | head_neck | back | general",
  "system": "musculoskeletal | nervous | cardiovascular | respiratory | digestive | urinary | reproductive | lymphatic | integumentary | general",
  "concept_type": "structural | clinical | embryological | histological | surface | general",
  "complexity": "simple | compound",
  "sub_questions": ["array of sub-questions if compound, or single original question if simple"],
  "is_anatomy": true | false,
  "sources_needed": ["openstax", "ncbi", "teachmeanatomy"]
}

If is_anatomy is false, the question is outside scope. Still return the full schema with is_anatomy: false.
""".strip()


async def analyze_query(query: str, gemini_call, has_user_uploads: bool = False) -> dict[str, Any]:
    raw = await gemini_call(prompt=query, system=QUERY_ANALYSIS_SYSTEM_PROMPT, temperature=0)
    data = json.loads(raw)
    parsed = QueryAnalysis(**data).model_dump()
    parsed["sources_needed"] = derive_sources(parsed["concept_type"], has_user_uploads)
    if parsed["complexity"] == "simple" and not parsed["sub_questions"]:
        parsed["sub_questions"] = [query]
    return parsed
