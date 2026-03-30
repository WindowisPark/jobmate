from app.agents.profiles import AGENT_PROFILES
from app.agents.state import AgentResponse, JobMateState
from app.services.llm_service import generate_response_with_tools
from app.tools import ALL_TOOLS
from app.tools.schemas import get_tools_for_agent

# DB 세션이 필요한 도구 목록
_DB_AWARE_TOOLS = {"search_jobs", "save_job_preferences"}


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

    context += "필요한 경우 도구를 사용해서 정확한 정보를 제공해. 도구 결과를 자연스럽게 설명해줘.\n"

    system = profile["system_prompt"] + "\n\n" + context
    tools = get_tools_for_agent(profile["tools"]) if is_primary else []

    history = state.get("conversation_history", [])
    user_id = state.get("user_id", "")

    async def execute_tool(name: str, args: dict) -> dict:
        fn = ALL_TOOLS.get(name)
        if fn is None:
            return {"error": f"알 수 없는 도구: {name}"}
        if name in _DB_AWARE_TOOLS:
            args["user_id"] = user_id
        return await fn(**args)

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
