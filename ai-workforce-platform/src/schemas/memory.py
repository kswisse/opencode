from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime


class MemoryCreate(BaseModel):
    content: str = Field(..., min_length=1)
    event_type: str | None = None
    knowledge_type: str | None = None
    metadata: dict | None = None


class MemoryResponse(BaseModel):
    id: UUID
    content: str
    event_type: str | None
    knowledge_type: str | None
    confidence: float
    source: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class MemorySearchRequest(BaseModel):
    query: str = Field(..., min_length=1)
    limit: int = Field(default=10, ge=1, le=100)
    memory_type: str = Field(default="all")


class MemorySearchResponse(BaseModel):
    results: list[MemoryResponse]
    total: int
