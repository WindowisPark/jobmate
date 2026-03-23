import json

from app.services.llm_service import generate_response

SYSTEM_PROMPT = """\
너는 취업 시장 분석 전문가야. 주어진 직군의 채용 트렌드를 분석해서 아래 JSON 형식으로만 응답해.

{
  "field": "직군명",
  "trend": "상승/안정/하락 중 하나",
  "demand_level": "높음/보통/낮음 중 하나",
  "avg_salary_range": "연봉 범위 (예: '3,500만~5,000만')",
  "top_skills": ["필요 스킬1", "스킬2", "스킬3"],
  "insights": ["인사이트1", "인사이트2", "인사이트3"]
}

실제 한국 취업 시장 기준으로 현실적으로 답변해. JSON만 반환해."""


async def analyze_market(
    job_field: str,
    region: str | None = None,
) -> dict:
    """직군별 채용 트렌드를 분석합니다."""
    region_info = f" (지역: {region})" if region else ""
    user_msg = f"'{job_field}'{region_info} 직군의 현재 채용 시장 트렌드를 분석해줘."

    raw = await generate_response(SYSTEM_PROMPT, user_msg)

    try:
        cleaned = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        return json.loads(cleaned)
    except (json.JSONDecodeError, KeyError):
        return {
            "field": job_field,
            "trend": "분석 불가",
            "demand_level": "확인 필요",
            "avg_salary_range": None,
            "top_skills": [],
            "insights": ["시장 분석 중 오류가 발생했습니다. 다시 시도해주세요."],
        }
