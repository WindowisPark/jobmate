import importlib
import json
from unittest.mock import AsyncMock

# app.tools 패키지가 같은 이름의 함수를 export 해서 모듈은 importlib 로 잡는다
rf = importlib.import_module("app.tools.resume_feedback")


async def test_resume_feedback_returns_structure(monkeypatch):
    fake = json.dumps(
        {
            "overall_score": 7,
            "strengths": ["구체적인 수치"],
            "improvements": ["요약 문단 추가"],
            "rewritten_sections": [],
        },
        ensure_ascii=False,
    )
    monkeypatch.setattr(rf, "generate_response", AsyncMock(return_value=fake))

    result = await rf.resume_feedback(content="테스트 이력서 내용")
    assert "overall_score" in result
    assert "strengths" in result
    assert "improvements" in result
