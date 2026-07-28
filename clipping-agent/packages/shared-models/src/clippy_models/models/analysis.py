from datetime import datetime
from pydantic import BaseModel, Field
from uuid import UUID, uuid4


class Signal(BaseModel):
    type: str  # controversial, surprise, punchline, educational, etc.
    confidence: float
    detail: str = ""


class AnalysisResult(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    segment_id: UUID
    model: str = ""
    signals: list[Signal] = []
    embedding: list[float] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)
