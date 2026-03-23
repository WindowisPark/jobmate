from app.agents.state import JobMateState

# Intent → Primary agent + optional assistants
INTENT_ROUTING = {
    "resume_interview": {"primary": "seo_yeon", "assist": ["min_su"]},
    "job_search": {"primary": "jun_ho", "assist": ["seo_yeon"]},
    "mental_care": {"primary": "ha_eun", "assist": ["min_su"]},
    "career_advice": {"primary": "min_su", "assist": ["seo_yeon"]},
    "general": {"primary": "ha_eun", "assist": []},
}


async def analyze_emotion(state: JobMateState) -> dict:
    """사용자 메시지의 감정을 분석하고 의도를 분류한다."""
    # TODO: Gemini로 감정 + 의도 분석
    # 임시 기본값
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
    if intensity >= 4 and emotion in ("anxious", "depressed", "angry"):
        if "ha_eun" not in active:
            active.insert(0, "ha_eun")

    # 보조 에이전트 추가 (50% 확률 시뮬레이션은 추후 구현)
    active.extend(routing.get("assist", []))

    return {"active_agents": active}
