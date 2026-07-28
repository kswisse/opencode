from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field
from uuid import UUID, uuid4


class ClipCandidateStatus(str, Enum):
    PROPOSED = "proposed"
    APPROVED = "approved"
    REJECTED = "rejected"
    GENERATED = "generated"


class ScoreSet(BaseModel):
    virality: float = 0.0
    retention: float = 0.0
    hook: float = 0.0
    emotion: float = 0.0
    shareability: float = 0.0
    educational: float = 0.0


class ClipCandidate(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    video_id: UUID
    segment_ids: list[UUID] = []
    start_time: float
    end_time: float
    summary: str = ""
    scores: ScoreSet = Field(default_factory=ScoreSet)
    predicted_score: float = 0.0
    actual_score: float | None = None
    status: ClipCandidateStatus = ClipCandidateStatus.PROPOSED
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Clip(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    candidate_id: UUID
    video_id: UUID
    storage_key: str
    subtitle_key: str | None = None
    duration_seconds: float | None = None
    subtitle_style: str = "default"
    file_format: str = "mp4"
    resolution: str = "1080x1920"
    thumbnail_url: str | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
