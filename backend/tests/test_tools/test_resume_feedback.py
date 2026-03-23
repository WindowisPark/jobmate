from app.tools.resume_feedback import resume_feedback


async def test_resume_feedback_returns_structure():
    result = await resume_feedback(content="테스트 이력서 내용")
    assert "overall_score" in result
    assert "strengths" in result
    assert "improvements" in result
