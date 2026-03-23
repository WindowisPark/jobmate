import json

from app.agents.state import JobMateState
from app.services.llm_service import generate_response

# Intent → Primary agent + optional assistants
INTENT_ROUTING = {
    "resume_interview": {"primary": "seo_yeon", "assist": ["min_su"]},
    "job_search": {"primary": "jun_ho", "assist": ["seo_yeon"]},
    "mental_care": {"primary": "ha_eun", "assist": ["min_su"]},
    "career_advice": {"primary": "min_su", "assist": ["seo_yeon"]},
    "general": {"primary": "ha_eun", "assist": []},
}

ANALYSIS_PROMPT = """\
너는 사용자 메시지를 분석하는 시스템이야. 아래 형식의 JSON만 반환해.

{
  "emotion": "neutral" | "anxious" | "depressed" | "angry" | "hopeful" | "frustrated",
  "emotion_intensity": 1~5,
  "intent": "resume_interview" | "job_search" | "mental_care" | "career_advice" | "general"
}

intent 판단 기준:
- resume_interview: 이력서, 자소서, 면접, 포트폴리오 관련
- job_search: 채용공고, 회사 추천, 취업 시장 관련
- mental_care: 감정 토로, 힘듦, 불안, 스트레스, 위로 필요
- career_advice: 진로 고민, 직무 선택, 커리어 방향
- general: 위에 해당 안 되는 일반 대화

JSON만 반환해. 다른 텍스트 없이."""


async def analyze_emotion(state: JobMateState) -> dict:
    """사용자 메시지의 감정을 분석하고 의도를 분류한다."""
    user_message = state["user_message"]

    raw = await generate_response(ANALYSIS_PROMPT, user_message)

    try:
        # JSON 파싱 (```json ... ``` 래핑 제거)
        cleaned = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        result = json.loads(cleaned)
        return {
            "emotion": result.get("emotion", "neutral"),
            "emotion_intensity": result.get("emotion_intensity", 2),
            "intent": result.get("intent", "general"),
        }
    except (json.JSONDecodeError, KeyError):
        return {
            "emotion": "neutral",
            "emotion_intensity": 2,
            "intent": "general",
        }


async def route_agents(state: JobMateState) -> dict:
    """감정과 의도에 따라 참여할 에이전트를 결정한다."""
    intent = state.get("intent", "general")
    emotion = state.get("emotion", "neutral")
    intensity = state.get("emotion_intensity", 2)

    routing = INTENT_ROUTING.get(intent, INTENT_ROUTING["general"])
    active = [routing["primary"]]

    # 감정 강도가 높으면 하은이 즉시 개입
    if intensity >= 4 and emotion in ("anxious", "depressed", "angry", "frustrated"):
        if "ha_eun" not in active:
            active.insert(0, "ha_eun")

    # 보조 에이전트 추가
    for assist_id in routing.get("assist", []):
        if assist_id not in active:
            active.append(assist_id)

    return {"active_agents": active}
