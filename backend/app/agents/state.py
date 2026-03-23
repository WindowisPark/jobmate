from typing import Annotated, Literal, TypedDict

from langgraph.graph import add_messages


class AgentResponse(TypedDict):
    agent_id: str
    content: str
    tool_calls: list[dict] | None
    delay_ms: int
    response_type: Literal["message", "reaction"]


class JobMateState(TypedDict):
    messages: Annotated[list, add_messages]
    user_message: str
    emotion: str
    emotion_intensity: int
    intent: str
    active_agents: list[str]
    agent_responses: list[AgentResponse]
    conversation_id: str
    user_id: str
