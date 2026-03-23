import json

from app.services.llm_service import generate_response

SYSTEM_PROMPT = """\
너는 전문 이력서/자소서 첨삭 전문가야. 주어진 내용을 분석해서 아래 JSON 형식으로만 응답해.

{
  "overall_score": 1~10 점수,
  "strengths": ["강점1", "강점2"],
  "improvements": ["개선점1: 구체적 설명", "개선점2: 구체적 설명"],
  "rewritten_sections": ["수정 제안1", "수정 제안2"]
}

JSON만 반환해. 다른 텍스트 없이."""


async def resume_feedback(
    content: str,
    doc_type: str = "resume",
) -> dict:
    """이력서 또는 자소서에 대한 피드백을 생성합니다."""
    doc_label = "이력서" if doc_type == "resume" else "자소서"
    user_msg = f"다음 {doc_label}를 첨삭해줘:\n\n{content}"

    raw = await generate_response(SYSTEM_PROMPT, user_msg)

    try:
        cleaned = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        return json.loads(cleaned)
    except (json.JSONDecodeError, KeyError):
        return {
            "overall_score": 5,
            "strengths": ["내용 분석 중 오류가 발생했습니다"],
            "improvements": ["다시 시도해주세요"],
            "rewritten_sections": [],
        }
