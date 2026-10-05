import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_db, get_current_user
from src.models.user import User
from src.services.background_job_service import BackgroundJobService

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("/{job_id}")
async def get_job(
    job_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Get a background job by ID.
    """
    service = BackgroundJobService(db)
    job = await service.get_job(job_id)
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return {
        "id": str(job.id),
        "goal_id": str(job.goal_id),
        "job_type": job.job_type,
        "status": job.status,
        "payload": job.payload,
        "result": job.result,
        "error_message": job.error_message,
        "retry_count": job.retry_count,
        "max_retries": job.max_retries,
        "worker_id": job.worker_id,
        "created_at": job.created_at.isoformat() if job.created_at else None,
        "started_at": job.started_at.isoformat() if job.started_at else None,
        "completed_at": job.completed_at.isoformat() if job.completed_at else None,
    }


@router.get("/project/{project_id}")
async def get_project_jobs(
    project_id: uuid.UUID,
    status: str | None = Query(None, description="Filter by status"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Get background jobs for a project.
    """
    service = BackgroundJobService(db)
    jobs = await service.get_jobs_by_project(
        project_id=project_id,
        status=status,
        limit=limit,
        offset=offset,
    )
    
    return {
        "jobs": [
            {
                "id": str(job.id),
                "goal_id": str(job.goal_id),
                "job_type": job.job_type,
                "status": job.status,
                "created_at": job.created_at.isoformat() if job.created_at else None,
                "completed_at": job.completed_at.isoformat() if job.completed_at else None,
            }
            for job in jobs
        ],
        "total": len(jobs),
    }


@router.get("/project/{project_id}/stats")
async def get_project_job_stats(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Get job statistics for a project.
    """
    service = BackgroundJobService(db)
    stats = await service.get_job_stats(project_id)
    return stats


@router.post("/{job_id}/retry")
async def retry_job(
    job_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Retry a failed job.
    """
    service = BackgroundJobService(db)
    
    try:
        job = await service.retry_job(job_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return {
        "id": str(job.id),
        "status": job.status,
        "message": "Job queued for retry",
    }


@router.post("/{job_id}/cancel")
async def cancel_job(
    job_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Cancel a queued job.
    """
    service = BackgroundJobService(db)
    
    try:
        job = await service.cancel_job(job_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return {
        "id": str(job.id),
        "status": job.status,
        "message": "Job cancelled",
    }


@router.delete("/cleanup")
async def cleanup_old_jobs(
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Clean up old completed/failed jobs.
    """
    service = BackgroundJobService(db)
    deleted_count = await service.cleanup_old_jobs(days)
    
    return {
        "deleted_count": deleted_count,
        "message": f"Deleted {deleted_count} old jobs",
    }
