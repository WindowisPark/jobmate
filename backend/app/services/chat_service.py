from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.graph import build_graph
from app.agents.state import JobMateState


async def process_user_message(
    db: AsyncSession,
    user_id: UUID,
    conversation_id: UUID,
    content: str,
) -> list[dict]:
    """사용자 메시지를 처리하고 에이전트 응답을 생성한다."""
    graph = build_graph()

    initial_state: JobMateState = {
        "messages": [],
        "user_message": content,
        "emotion": "",
        "emotion_intensity": 0,
        "intent": "",
        "active_agents": [],
        "agent_responses": [],
        "conversation_id": str(conversation_id),
        "user_id": str(user_id),
    }

    result = await graph.ainvoke(initial_state)
    return result.get("agent_responses", [])
