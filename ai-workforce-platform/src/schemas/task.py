from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime


class TaskCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    priority: int = Field(default=3, ge=1, le=5)
    dependencies: list[UUID] = Field(default_factory=list)


class TaskResponse(BaseModel):
    id: UUID
    project_id: UUID
    name: str
    description: str | None
    status: str
    priority: int
    assigned_agent_id: UUID | None
    wave_number: int
    output: dict | None
    error: str | None
    retry_count: int
    created_at: datetime
    completed_at: datetime | None

    model_config = {"from_attributes": True}


class TaskListResponse(BaseModel):
    tasks: list[TaskResponse]
    total: int
