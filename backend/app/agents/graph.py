import logging

from langgraph.graph import StateGraph, START, END

from app.agents.state import JobMateState, AgentResponse
from app.agents.router import analyze_emotion, route_agents
from app.agents.nodes import seo_yeon, jun_ho, ha_eun, min_su

logger = logging.getLogger(__name__)

AGENT_MODULES = {
    "seo_yeon": seo_yeon,
    "jun_ho": jun_ho,
    "ha_eun": ha_eun,
    "min_su": min_su,
}


async def run_agents(state: JobMateState) -> dict:
    """선택된 에이전트들을 순차 실행하고 응답을 수집한다."""
    active = state.get("active_agents", [])
    responses: list[AgentResponse] = []

    for i, agent_id in enumerate(active):
        module = AGENT_MODULES.get(agent_id)
        if module is None:
            continue
        is_primary = i == 0
        try:
            response = await module.run(state, is_primary=is_primary)
            responses.append(response)
        except Exception as e:
            logger.error(f"Agent {agent_id} failed: {e}", exc_info=True)
            responses.append(AgentResponse(
                agent_id=agent_id,
                content="죄송해요, 잠시 오류가 발생했어요. 다시 말씀해주시겠어요?",
                tool_calls=None,
                delay_ms=0,
                response_type="message",
            ))

    return {"agent_responses": responses}


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
    graph.add_node("route_agents", route_agents)
    graph.add_node("run_agents", run_agents)
    graph.add_node("compose_responses", compose_responses)

    graph.add_edge(START, "analyze_emotion")
    graph.add_edge("analyze_emotion", "route_agents")
    graph.add_edge("route_agents", "run_agents")
    graph.add_edge("run_agents", "compose_responses")
    graph.add_edge("compose_responses", END)

    return graph.compile()
