from pydantic import BaseModel
from uuid import UUID
from datetime import datetime


class PipelineEvent(BaseModel):
    event_type: str
    video_id: UUID
    tenant_id: UUID
    step_name: str | None = None
    step_status: str | None = None
    error_message: str | None = None
    timestamp: datetime = datetime.utcnow()


class ClipEvent(BaseModel):
    event_type: str
    clip_id: UUID
    video_id: UUID
    tenant_id: UUID
    platform: str | None = None
    timestamp: datetime = datetime.utcnow()
