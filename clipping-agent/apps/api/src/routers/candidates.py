from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from clippy_models import ClipCandidate, Clip, ScoreSet
from clippy_database.models.candidate import ClipCandidateModel
from clippy_database.models.clip import ClipModel
from ..dependencies.db import get_db
import uuid
from datetime import datetime

router = APIRouter()


def candidate_to_pydantic(c: ClipCandidateModel) -> ClipCandidate:
    return ClipCandidate(
        id=c.id,
        video_id=c.video_id,
        segment_ids=c.segment_ids or [],
        start_time=c.start_time,
        end_time=c.end_time,
        summary=c.summary,
        scores=ScoreSet(**c.scores) if c.scores else ScoreSet(),
        predicted_score=c.predicted_score or 0.0,
        actual_score=c.actual_score,
        status=c.status,
        created_at=c.created_at,
    )


@router.get("/video/{video_id}", response_model=dict)
async def get_candidates(video_id: UUID, request: Request, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(ClipCandidateModel).where(
            ClipCandidateModel.video_id == video_id,
        ).order_by(ClipCandidateModel.predicted_score.desc())
    )
    candidates = result.scalars().all()
    return {"candidates": [candidate_to_pydantic(c) for c in candidates]}


@router.post("/{candidate_id}/approve", response_model=dict)
async def approve_candidate(candidate_id: UUID, request: Request, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(ClipCandidateModel).where(ClipCandidateModel.id == candidate_id)
    )
    candidate = result.scalar_one_or_none()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    candidate.status = "approved"
    await db.commit()

    clip_id = uuid.uuid4()
    clip = ClipModel(
        id=clip_id,
        candidate_id=candidate_id,
        video_id=candidate.video_id,
        storage_key=f"clips/{candidate_id}.mp4",
    )
    db.add(clip)
    await db.commit()
    await db.refresh(clip)

    return {"clip": Clip(
        id=clip.id,
        candidate_id=clip.candidate_id,
        video_id=clip.video_id,
        storage_key=clip.storage_key,
        subtitle_key=clip.subtitle_key,
        duration_seconds=clip.duration_seconds,
        subtitle_style=clip.subtitle_style,
        file_format=clip.file_format,
        resolution=clip.resolution,
        created_at=clip.created_at,
    )}


@router.post("/{candidate_id}/reject", response_model=dict)
async def reject_candidate(candidate_id: UUID, request: Request, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(ClipCandidateModel).where(ClipCandidateModel.id == candidate_id)
    )
    candidate = result.scalar_one_or_none()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    candidate.status = "rejected"
    await db.commit()
    return {"ok": True}
