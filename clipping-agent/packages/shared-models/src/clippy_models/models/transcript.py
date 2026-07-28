from datetime import datetime
from pydantic import BaseModel, Field
from uuid import UUID, uuid4


class TranscriptSegment(BaseModel):
    start: float
    end: float
    text: str
    speaker_id: str | None = None
    confidence: float = 0.0


class Transcript(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    video_id: UUID
    language: str | None = None
    segments: list[TranscriptSegment] = []
    raw_output: dict = {}
    created_at: datetime = Field(default_factory=datetime.utcnow)
