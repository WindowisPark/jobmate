from langgraph.graph import StateGraph, START, END

from app.agents.state import JobMateState
from app.agents.router import analyze_emotion, route_agents


async def run_agents(state: JobMateState) -> dict:
    """선택된 에이전트들을 실행하고 응답을 생성한다."""
    # TODO: 각 에이전트 노드 실행 + Tool Calling
    return {"agent_responses": []}


async def compose_responses(state: JobMateState) -> dict:
    """에이전트 응답을 정렬하고 딜레이를 설정한다."""
    # TODO: primary 먼저, 보조는 딜레이 추가
    return {}


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
