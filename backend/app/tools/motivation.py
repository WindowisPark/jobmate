async def get_motivation_content(
    mood: str = "depressed",
    content_type: str = "mixed",
) -> dict:
    """사용자 상태에 맞는 동기부여 콘텐츠를 추천합니다."""
    # TODO: YouTube Data API로 영상 검색
    return {
        "quotes": [],
        "videos": [],
        "articles": [],
    }
