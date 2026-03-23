async def search_jobs(
    keywords: list[str],
    location: str | None = None,
    career_level: str = "신입",
    limit: int = 5,
) -> dict:
    """사람인 API와 공공데이터포털에서 채용공고를 검색합니다."""
    # TODO: 사람인 Open API 호출
    # TODO: 공공데이터포털 API 호출
    # TODO: 결과 병합 및 정렬
    return {
        "source": "mock",
        "total": 0,
        "jobs": [],
    }
