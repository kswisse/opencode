from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from clippy_models import (
    Video, VideoCreateResponse, VideoConfirmRequest, VideoListResponse,
    SourceType, VideoStatus,
)
from clippy_database.models.video import VideoModel
from clippy_database.models.pipeline import PipelineRunModel
from ..dependencies.db import get_db
from datetime import datetime

router = APIRouter()


@router.post("/upload-url", response_model=VideoCreateResponse)
async def get_upload_url(request: Request):
    storage = request.app.state.storage
    import uuid
    video_id = uuid.uuid4()
    key = f"raw-videos/{video_id}.mp4"
    upload_info = await storage.generate_presigned_upload_url("raw-videos", key)
    return VideoCreateResponse(id=video_id, **upload_info)


@router.post("/confirm", response_model=Video)
async def confirm_video(body: VideoConfirmRequest, request: Request, db: AsyncSession = Depends(get_db)):
    import uuid
    video_id = uuid.uuid4()
    tenant_id = request.state.tenant_id

    model = VideoModel(
        id=video_id,
        tenant_id=tenant_id,
        source_type=body.source_type,
        source_url=body.source_url,
        storage_key=body.storage_key,
        status=VideoStatus.PENDING,
        metadata=body.metadata,
    )
    db.add(model)
    await db.commit()
    await db.refresh(model)

    return Video(
        id=model.id,
        tenant_id=model.tenant_id,
        title=model.title,
        source_type=model.source_type,
        source_url=model.source_url,
        status=model.status,
        storage_key=model.storage_key,
        metadata=model.metadata,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


@router.get("", response_model=VideoListResponse)
async def list_videos(request: Request, db: AsyncSession = Depends(get_db), status: str | None = None):
    tenant_id = request.state.tenant_id
    query = select(VideoModel).where(VideoModel.tenant_id == tenant_id).order_by(VideoModel.created_at.desc())
    if status:
        query = query.where(VideoModel.status == VideoStatus(status))
    result = await db.execute(query)
    rows = result.scalars().all()

    videos = [
        Video(
            id=v.id, tenant_id=v.tenant_id, title=v.title,
            source_type=v.source_type, source_url=v.source_url,
            status=v.status, storage_key=v.storage_key,
            duration_seconds=v.duration_seconds, file_size_bytes=v.file_size_bytes,
            metadata=v.metadata, error_message=v.error_message,
            created_at=v.created_at, updated_at=v.updated_at,
        )
        for v in rows
    ]
    return VideoListResponse(videos=videos, total=len(videos))


@router.get("/{video_id}", response_model=dict)
async def get_video(video_id: UUID, request: Request, db: AsyncSession = Depends(get_db)):
    tenant_id = request.state.tenant_id
    result = await db.execute(
        select(VideoModel).where(VideoModel.id == video_id, VideoModel.tenant_id == tenant_id)
    )
    model = result.scalar_one_or_none()
    if not model:
        raise HTTPException(status_code=404, detail="Video not found")

    pipeline_result = await db.execute(
        select(PipelineRunModel).where(PipelineRunModel.video_id == video_id)
    )
    pipeline = pipeline_result.scalar_one_or_none()
    steps = pipeline.steps if pipeline else []

    video = Video(
        id=model.id, tenant_id=model.tenant_id, title=model.title,
        source_type=model.source_type, source_url=model.source_url,
        status=model.status, storage_key=model.storage_key,
        duration_seconds=model.duration_seconds, file_size_bytes=model.file_size_bytes,
        metadata=model.metadata, error_message=model.error_message,
        created_at=model.created_at, updated_at=model.updated_at,
    )
    return {"video": video, "pipeline": steps}
