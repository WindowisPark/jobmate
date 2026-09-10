from app.agents.nodes._tool_exec import make_tool_executor
from app.agents.profiles import AGENT_PROFILES
from app.agents.state import AgentResponse, JobMateState
from app.services.application_service import format_application_context
from app.services.llm_service import generate_response_with_tools
from app.tools.schemas import get_tools_for_agent


async def run(state: JobMateState, is_primary: bool = True) -> AgentResponse:
    profile = AGENT_PROFILES["min_su"]
    context = (
        f"현재 사용자의 감정: {state['emotion']} (강도: {state['emotion_intensity']})\n"
        f"대화 의도: {state['intent']}\n"
    )
    if not is_primary:
        context += "너는 보조 역할이야. 짧게 한마디만 덧붙여줘 (1~2문장).\n"
    context += (
        "필요한 경우 도구를 사용해서 정확한 정보를 제공해. 도구 결과를 자연스럽게 설명해줘.\n"
    )

    # 내 지원 현황을 안다는 것이 이 방의 존재 이유다. 에이전트마다 보는 관점이 다르다.
    tracker = format_application_context(state.get("application_summary") or {}, "min_su")
    if tracker:
        context += tracker + "\n"

    system = profile["system_prompt"] + "\n\n" + context
    tools = get_tools_for_agent(profile["tools"]) if is_primary else []

    history = state.get("conversation_history", [])
    execute_tool = make_tool_executor(state.get("user_id", ""))

    content, tool_records = await generate_response_with_tools(
        system, state["user_message"], tools, execute_tool, history=history
    )

    return AgentResponse(
        agent_id="min_su",
        content=content,
        tool_calls=tool_records,
        delay_ms=0 if is_primary else 1500,
        response_type="message",
    )
