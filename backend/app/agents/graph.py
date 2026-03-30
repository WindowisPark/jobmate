import logging

from langgraph.graph import StateGraph, START, END

from app.agents.state import JobMateState, AgentResponse
from app.agents.router import analyze_emotion
from app.agents.planner import plan_tasks
from app.agents.nodes import seo_yeon, jun_ho, ha_eun, min_su

logger = logging.getLogger(__name__)

AGENT_MODULES = {
    "seo_yeon": seo_yeon,
    "jun_ho": jun_ho,
    "ha_eun": ha_eun,
    "min_su": min_su,
}


async def execute_step(state: JobMateState) -> dict:
    """현재 step의 에이전트를 실행하고 결과를 저장한다."""
    task_plan = state.get("task_plan", [])
    current_step = state.get("current_step", 0)
    step_results = dict(state.get("step_results", {}))
    responses = list(state.get("agent_responses", []))

    if current_step >= len(task_plan):
        return {"current_step": current_step}

    step = task_plan[current_step]
    agent_id = step["agent_id"]
    is_primary = step["role"] == "primary"

    module = AGENT_MODULES.get(agent_id)
    if module is None:
        logger.warning(f"Unknown agent: {agent_id}")
        return {"current_step": current_step + 1, "step_results": step_results}

    # depends_on 결과를 컨텍스트에 주입
    dep_context = ""
    for dep_id in step.get("depends_on", []):
        dep_result = step_results.get(dep_id)
        if dep_result:
            dep_step = next((s for s in task_plan if s["step_id"] == dep_id), None)
            dep_agent = dep_step["agent_id"] if dep_step else "unknown"
            dep_context += f"\n[{dep_agent}의 이전 응답]: {dep_result[:500]}\n"

    # 선행 결과가 있으면 user_message에 컨텍스트 추가
    enriched_state = dict(state)
    if dep_context:
        enriched_state["user_message"] = (
            state["user_message"] + "\n\n--- 이전 단계 참고 정보 ---" + dep_context
        )

    try:
        response = await module.run(enriched_state, is_primary=is_primary)
        responses.append(response)
        step_results[step["step_id"]] = response["content"]
    except Exception as e:
        logger.error(f"Agent {agent_id} failed at step {current_step}: {e}", exc_info=True)
        error_response = AgentResponse(
            agent_id=agent_id,
            content="죄송해요, 잠시 오류가 발생했어요. 다시 말씀해주시겠어요?",
            tool_calls=None,
            delay_ms=0,
            response_type="message",
        )
        responses.append(error_response)
        step_results[step["step_id"]] = error_response["content"]

    return {
        "agent_responses": responses,
        "step_results": step_results,
        "current_step": current_step + 1,
    }


def should_continue(state: JobMateState) -> str:
    """더 실행할 step이 있는지 확인한다."""
    task_plan = state.get("task_plan", [])
    current_step = state.get("current_step", 0)

    if current_step < len(task_plan):
        return "execute_step"
    return "compose_responses"


async def compose_responses(state: JobMateState) -> dict:
    """에이전트 응답에 딜레이를 설정한다."""
    responses = state.get("agent_responses", [])
    for i, resp in enumerate(responses):
        if i == 0:
            resp["delay_ms"] = 0
        else:
            resp["delay_ms"] = 800 + (i * 700)
    return {"agent_responses": responses}


def build_graph() -> StateGraph:
    """JobMate LangGraph 그래프를 빌드한다."""
    graph = StateGraph(JobMateState)

    graph.add_node("analyze_emotion", analyze_emotion)
    graph.add_node("plan_tasks", plan_tasks)
    graph.add_node("execute_step", execute_step)
    graph.add_node("compose_responses", compose_responses)

    graph.add_edge(START, "analyze_emotion")
    graph.add_edge("analyze_emotion", "plan_tasks")
    graph.add_edge("plan_tasks", "execute_step")

    # 조건부 엣지: 더 실행할 step이 있으면 루프
    graph.add_conditional_edges(
        "execute_step",
        should_continue,
        {
            "execute_step": "execute_step",
            "compose_responses": "compose_responses",
        },
    )

    graph.add_edge("compose_responses", END)

    return graph.compile()
