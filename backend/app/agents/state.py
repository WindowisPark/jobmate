from typing import Annotated, Literal, TypedDict

from langgraph.graph import add_messages


class AgentResponse(TypedDict):
    agent_id: str
    content: str
    tool_calls: list[dict] | None
    delay_ms: int
    response_type: Literal["message", "reaction"]


class TaskStep(TypedDict):
    step_id: int
    agent_id: str
    role: Literal["primary", "assist"]
    action_hint: str
    depends_on: list[int]
    tool_hint: str | None


class JobMateState(TypedDict):
    messages: Annotated[list, add_messages]
    user_message: str
    conversation_history: list[dict]  # DB에서 로드한 이전 대화 히스토리
    emotion: str
    emotion_intensity: int
    intent: str
    active_agents: list[str]
    agent_responses: list[AgentResponse]
    conversation_id: str
    user_id: str
    # Phase 2: 사용자 직무 프리퍼런스
    user_preferences: dict | None
    # Phase 3: 감정 이력 요약
    emotion_history_summary: str
    # Phase 1: Planner 오케스트레이터
    task_plan: list[TaskStep]
    step_results: dict[int, str]
    current_step: int
