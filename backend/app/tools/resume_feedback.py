async def resume_feedback(
    content: str,
    doc_type: str = "resume",
) -> dict:
    """이력서 또는 자소서에 대한 피드백을 생성합니다."""
    # TODO: Gemini로 첨삭 피드백 생성
    return {
        "overall_score": 0,
        "strengths": [],
        "improvements": [],
        "rewritten_sections": [],
    }
