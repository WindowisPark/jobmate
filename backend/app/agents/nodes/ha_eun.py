from app.agents.profiles import AGENT_PROFILES
from app.agents.state import AgentResponse, JobMateState
from app.services.llm_service import generate_response


async def run(state: JobMateState, is_primary: bool = True) -> AgentResponse:
    profile = AGENT_PROFILES["ha_eun"]
    context = (
        f"현재 사용자의 감정: {state['emotion']} (강도: {state['emotion_intensity']})\n"
        f"대화 의도: {state['intent']}\n"
    )
    if not is_primary:
        context += "너는 보조 역할이야. 짧게 한마디만 덧붙여줘 (1~2문장).\n"

    if state.get("emotion_intensity", 0) >= 4 and state.get("emotion") in (
        "anxious", "depressed", "angry", "frustrated"
    ):
        context += "사용자가 매우 힘든 상태야. 공감을 먼저 하고, 호흡 운동을 제안해줘.\n"

    system = profile["system_prompt"] + "\n\n" + context
    content = await generate_response(system, state["user_message"])

    return AgentResponse(
        agent_id="ha_eun",
        content=content,
        tool_calls=None,
        delay_ms=0 if is_primary else 1500,
        response_type="message",
    )
