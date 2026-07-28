from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime


class AgentCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    agent_type: str = Field(..., min_length=1, max_length=100)
    system_prompt: str | None = None
    model: str = "gpt-4o-mini"
    capabilities: list[str] = Field(default_factory=list)
    config: dict | None = None


class AgentResponse(BaseModel):
    id: UUID
    name: str
    agent_type: str
    status: str
    model: str
    performance_score: float
    total_tasks: int
    successful_tasks: int
    created_at: datetime

    model_config = {"from_attributes": True}


class AgentListResponse(BaseModel):
    agents: list[AgentResponse]
    total: int
