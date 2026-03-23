async def analyze_market(
    job_field: str,
    region: str | None = None,
) -> dict:
    """직군별 채용 트렌드를 분석합니다."""
    # TODO: 채용공고 데이터 기반 트렌드 분석
    return {
        "field": job_field,
        "trend": "mock",
        "demand_level": "unknown",
        "avg_salary_range": None,
        "top_skills": [],
        "insights": [],
    }
