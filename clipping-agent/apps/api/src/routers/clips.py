from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from clippy_models import Clip
from clippy_database.models.clip import ClipModel
from ..dependencies.db import get_db

router = APIRouter()


def clip_to_pydantic(c: ClipModel) -> Clip:
    return Clip(
        id=c.id,
        candidate_id=c.candidate_id,
        video_id=c.video_id,
        storage_key=c.storage_key,
        subtitle_key=c.subtitle_key,
        duration_seconds=c.duration_seconds,
        subtitle_style=c.subtitle_style,
        file_format=c.file_format,
        resolution=c.resolution,
        created_at=c.created_at,
    )


@router.get("", response_model=dict)
async def list_clips(request: Request, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(ClipModel).order_by(ClipModel.created_at.desc())
    )
    clips = result.scalars().all()
    return {"clips": [clip_to_pydantic(c) for c in clips]}


@router.get("/{clip_id}", response_model=dict)
async def get_clip(clip_id: UUID, request: Request, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(ClipModel).where(ClipModel.id == clip_id)
    )
    clip = result.scalar_one_or_none()
    if not clip:
        raise HTTPException(status_code=404, detail="Clip not found")
    return {"clip": clip_to_pydantic(clip)}
