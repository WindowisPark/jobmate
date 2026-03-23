from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class UserMessageIn(BaseModel):
    type: str = "user_message"
    content: str
    timestamp: datetime | None = None


class AgentTypingEvent(BaseModel):
    type: str = "agent_typing"
    agent_id: str
    office_action: str


class AgentMessageChunk(BaseModel):
    type: str = "agent_message_chunk"
    agent_id: str
    chunk: str
    is_final: bool = False


class ToolCallStart(BaseModel):
    type: str = "tool_call_start"
    agent_id: str
    tool_name: str
    office_action: str


class ToolCallResult(BaseModel):
    type: str = "tool_call_result"
    agent_id: str
    tool_name: str
    result_summary: str
    office_action: str = "idle"


class AgentReaction(BaseModel):
    type: str = "agent_reaction"
    agent_id: str
    emoji: str


class OfficeAgentState(BaseModel):
    action: str
    position: dict[str, int]


class OfficeStateEvent(BaseModel):
    type: str = "office_state"
    agents: dict[str, OfficeAgentState]


class MessageOut(BaseModel):
    id: UUID
    conversation_id: UUID
    sender_type: str
    agent_id: str | None = None
    content: str
    emotion_tag: str | None = None
    created_at: datetime
