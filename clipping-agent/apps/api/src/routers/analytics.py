from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from clippy_models import Clip
from clippy_database.models.clip import ClipModel
from clippy_database.models.analytics import AnalyticsEventModel
from ..dependencies.db import get_db

router = APIRouter()


@router.post("/{clip_id}/analytics", response_model=dict)
async def record_analytics(clip_id: UUID, request: Request, db: AsyncSession = Depends(get_db)):
    body = await request.json()
    event = AnalyticsEventModel(
        clip_id=clip_id,
        tenant_id=request.state.tenant_id,
        platform=body.get("platform", "unknown"),
        views=body.get("views", 0),
        likes=body.get("likes", 0),
        shares=body.get("shares", 0),
        comments=body.get("comments", 0),
        watch_time_seconds=body.get("watch_time_seconds", 0),
        completion_rate=body.get("completion_rate", 0),
        ctr=body.get("ctr", 0),
    )
    db.add(event)
    await db.commit()
    return {"ok": True}


@router.get("/overview", response_model=dict)
async def get_analytics_overview(request: Request, db: AsyncSession = Depends(get_db)):
    total_clips = await db.scalar(select(func.count(ClipModel.id)))
    total_views_result = await db.execute(select(func.coalesce(func.sum(AnalyticsEventModel.views), 0)))
    total_views = total_views_result.scalar()
    total_likes_result = await db.execute(select(func.coalesce(func.sum(AnalyticsEventModel.likes), 0)))
    total_likes = total_likes_result.scalar()

    return {
        "total_clips": total_clips or 0,
        "total_views": total_views or 0,
        "total_likes": total_likes or 0,
        "total_shares": 0,
        "average_completion_rate": 0,
    }
