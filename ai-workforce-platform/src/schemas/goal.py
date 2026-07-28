from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime


class GoalSubmit(BaseModel):
    goal_text: str = Field(..., min_length=10, max_length=5000)
    priority: str = Field(default="medium")
    constraints: dict | None = None


class GoalResponse(BaseModel):
    id: UUID
    company_id: UUID
    goal_text: str
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ProjectResponse(BaseModel):
    id: UUID
    name: str
    goal_text: str
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}
