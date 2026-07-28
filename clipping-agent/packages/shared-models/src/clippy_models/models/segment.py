from datetime import datetime
from pydantic import BaseModel, Field
from uuid import UUID, uuid4


class SceneBoundary(BaseModel):
    start: float
    end: float
    label: str = ""


class SpeakerSegment(BaseModel):
    speaker_id: str
    start: float
    end: float


class ConversationSegment(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    video_id: UUID
    start_time: float
    end_time: float
    text: str
    speaker_id: str | None = None
    segment_type: str | None = None
    context: dict = {}
    created_at: datetime = Field(default_factory=datetime.utcnow)
