import json

from app.services.llm_service import generate_response

SYSTEM_PROMPT = """\
너는 현직자 관점에서 업계 인사이트를 공유하는 멘토야. 주어진 업종/주제에 대해 현실적인 조언을 해줘.
아래 JSON 형식으로만 응답해.

{
  "industry": "업종명",
  "insights": ["인사이트1", "인사이트2", "인사이트3"],
  "tips": ["실무 팁1", "팁2"],
  "common_mistakes": ["흔한 실수1", "실수2"],
  "reality_check": "업계 현실 한마디"
}

한국 취업 시장 기준으로 솔직하고 현실적으로 답변해. JSON만 반환해."""


async def industry_insight(
    industry: str,
    topic: str | None = None,
) -> dict:
    """업계 현실 조언과 인사이트를 제공합니다."""
    topic_info = f", 주제: {topic}" if topic else ""
    user_msg = f"'{industry}' 업계{topic_info}에 대한 현실적인 인사이트를 알려줘."

    raw = await generate_response(SYSTEM_PROMPT, user_msg)

    try:
        cleaned = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        return json.loads(cleaned)
    except (json.JSONDecodeError, KeyError):
        return {
            "industry": industry,
            "insights": ["인사이트 생성 중 오류가 발생했습니다"],
            "tips": [],
            "common_mistakes": [],
            "reality_check": "다시 시도해주세요.",
        }
