async def industry_insight(
    industry: str,
    topic: str | None = None,
) -> dict:
    """업계 현실 조언과 인사이트를 제공합니다."""
    # TODO: Gemini로 업계 인사이트 생성
    return {
        "industry": industry,
        "insights": [],
        "tips": [],
        "common_mistakes": [],
    }
