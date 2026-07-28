from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field
from uuid import UUID, uuid4


class SourceType(str, Enum):
    YOUTUBE = "youtube"
    TWITCH = "twitch"
    PODCAST = "podcast"
    LOCAL = "local"


class VideoStatus(str, Enum):
    PENDING = "pending"
    DOWNLOADING = "downloading"
    PROCESSING = "processing"
    READY = "ready"
    FAILED = "failed"


class PipelineStepName(str, Enum):
    DOWNLOAD = "download"
    TRANSCRIBE = "transcribe"
    ANALYZE = "analyze"
    SCORE = "score"
    GENERATE = "generate"
    DONE = "done"


class Video(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    tenant_id: UUID
    title: str = ""
    source_type: SourceType
    source_url: str | None = None
    status: VideoStatus = VideoStatus.PENDING
    storage_key: str | None = None
    thumbnail_key: str | None = None
    duration_seconds: float | None = None
    file_size_bytes: int | None = None
    metadata: dict = {}
    error_message: str | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class VideoCreateResponse(BaseModel):
    id: UUID
    upload_url: str | None = None
    upload_fields: dict | None = None


class VideoConfirmRequest(BaseModel):
    storage_key: str
    source_type: SourceType
    source_url: str | None = None
    metadata: dict = {}


class VideoListResponse(BaseModel):
    videos: list[Video]
    total: int
