import json

from app.services.llm_service import generate_response

SYSTEM_PROMPT = """\
너는 면접관 역할을 하는 모의 면접 코치야. 주어진 직무와 조건에 맞는 면접 질문을 생성해.
아래 JSON 형식으로만 응답해.

{
  "questions": [
    {"question": "질문 내용", "category": "인성/기술/경험/상황", "tip": "답변 팁"},
    ...
  ],
  "general_tips": ["면접 전반적인 팁1", "팁2"]
}

질문은 3~5개 생성해. JSON만 반환해."""


async def mock_interview(
    job_title: str,
    company_type: str | None = None,
    difficulty: str = "medium",
) -> dict:
    """모의 면접 질문을 생성하고 답변에 피드백합니다."""
    company_info = f" ({company_type})" if company_type else ""
    diff_label = {"easy": "기초", "medium": "중급", "hard": "심화"}.get(difficulty, "중급")
    user_msg = f"직무: {job_title}{company_info}, 난이도: {diff_label} 면접 질문을 만들어줘."

    raw = await generate_response(SYSTEM_PROMPT, user_msg)

    try:
        cleaned = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        return json.loads(cleaned)
    except (json.JSONDecodeError, KeyError):
        return {
            "questions": [
                {"question": "자기소개를 해주세요.", "category": "기본", "tip": "1분 내로 핵심만"},
                {"question": f"{job_title} 직무에 지원한 이유는?", "category": "동기", "tip": "구체적 경험 연결"},
            ],
            "general_tips": ["면접 전 회사에 대해 충분히 조사하세요", "STAR 기법으로 답변을 구조화하세요"],
        }
