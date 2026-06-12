SOURCE_ROUTING = {
    "structural": ["openstax", "ncbi"],
    "clinical": ["teachmeanatomy", "ncbi"],
    "embryological": ["ncbi", "openstax"],
    "histological": ["ncbi", "openstax"],
    "surface": ["teachmeanatomy", "openstax"],
    "general": ["openstax", "ncbi"],
}


def derive_sources(concept_type: str, has_user_uploads: bool) -> list[str]:
    sources = SOURCE_ROUTING.get(concept_type, SOURCE_ROUTING["general"]).copy()
    if has_user_uploads and "user_upload" not in sources:
        sources.append("user_upload")
    return sources[:3] if not has_user_uploads else sources
