from pydantic import BaseModel


class AgentOut(BaseModel):
    id: str
    name: str
    role: str
    personality: str
    avatar_url: str


class AgentStatus(BaseModel):
    id: str
    name: str
    current_action: str = "idle"
    position: dict[str, int] = {"x": 0, "y": 0}
