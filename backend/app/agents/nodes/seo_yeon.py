from app.agents.profiles import AGENT_PROFILES
from app.agents.state import AgentResponse, JobMateState
from app.services.llm_service import generate_response


async def run(state: JobMateState, is_primary: bool = True) -> AgentResponse:
    profile = AGENT_PROFILES["seo_yeon"]
    context = (
        f"현재 사용자의 감정: {state['emotion']} (강도: {state['emotion_intensity']})\n"
        f"대화 의도: {state['intent']}\n"
    )
    if not is_primary:
        context += "너는 보조 역할이야. 짧게 한마디만 덧붙여줘 (1~2문장).\n"

    system = profile["system_prompt"] + "\n\n" + context
    content = await generate_response(system, state["user_message"])

    return AgentResponse(
        agent_id="seo_yeon",
        content=content,
        tool_calls=None,
        delay_ms=0 if is_primary else 1500,
        response_type="message",
    )
