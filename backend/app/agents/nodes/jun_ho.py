from app.agents.nodes._tool_exec import make_tool_executor
from app.agents.profiles import AGENT_PROFILES
from app.agents.state import AgentResponse, JobMateState
from app.services.llm_service import generate_response_with_tools
from app.tools.schemas import get_tools_for_agent


async def run(state: JobMateState, is_primary: bool = True) -> AgentResponse:
    profile = AGENT_PROFILES["jun_ho"]
    context = (
        f"현재 사용자의 감정: {state['emotion']} (강도: {state['emotion_intensity']})\n"
        f"대화 의도: {state['intent']}\n"
    )
    if not is_primary:
        context += "너는 보조 역할이야. 짧게 한마디만 덧붙여줘 (1~2문장).\n"

    # 프리퍼런스 컨텍스트 주입
    prefs = state.get("user_preferences")
    if prefs:
        pref_lines = []
        if prefs.get("job_field"):
            pref_lines.append(f"관심 직무: {prefs['job_field']}")
        if prefs.get("location"):
            pref_lines.append(f"희망 근무지: {prefs['location']}")
        if prefs.get("career_level"):
            pref_lines.append(f"경력: {prefs['career_level']}")
        if prefs.get("keywords"):
            pref_lines.append(f"관심 키워드: {', '.join(prefs['keywords'])}")
        if pref_lines:
            context += "사용자의 저장된 직무 선호도:\n" + "\n".join(pref_lines) + "\n"
            context += "검색 시 이 선호도를 참고해줘. 사용자가 새로운 선호를 말하면 save_job_preferences 도구로 저장해줘.\n"
    else:
        context += "사용자의 저장된 직무 선호도가 없어. 대화 중 직무, 지역, 경력 등을 파악하면 save_job_preferences 도구로 저장해줘.\n"

    context += (
        "필요한 경우 도구를 사용해서 정확한 정보를 제공해. 도구 결과를 자연스럽게 설명해줘.\n"
    )

    system = profile["system_prompt"] + "\n\n" + context
    tools = get_tools_for_agent(profile["tools"]) if is_primary else []

    history = state.get("conversation_history", [])
    execute_tool = make_tool_executor(state.get("user_id", ""))

    content, tool_records = await generate_response_with_tools(
        system, state["user_message"], tools, execute_tool, history=history
    )

    return AgentResponse(
        agent_id="jun_ho",
        content=content,
        tool_calls=tool_records,
        delay_ms=0 if is_primary else 1500,
        response_type="message",
    )
