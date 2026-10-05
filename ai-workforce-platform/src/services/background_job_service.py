import uuid
from datetime import datetime, timezone, timedelta
from typing import Any

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.background_job import BackgroundJob
from src.worker.arq_worker import enqueue_task_execution


class BackgroundJobService:
    """Service for managing background jobs."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def enqueue_task_execution(
        self,
        project_id: uuid.UUID,
        task_id: uuid.UUID,
        payload: dict | None = None,
    ) -> BackgroundJob:
        """
        Enqueue a task execution job.
        
        Args:
            project_id: Project ID
            task_id: Task ID
            payload: Optional payload data
            
        Returns:
            BackgroundJob instance
        """
        from src.observability.correlation import get_request_id
        job = await enqueue_task_execution(
            db=self.db,
            project_id=project_id,
            task_id=task_id,
            job_type="execute_task",
            payload=payload,
            request_id=get_request_id(),
        )
        return job
    
    async def get_job(self, job_id: uuid.UUID) -> BackgroundJob | None:
        """
        Get a background job by ID.
        
        Args:
            job_id: Job ID
            
        Returns:
            BackgroundJob or None
        """
        result = await self.db.execute(
            select(BackgroundJob).where(BackgroundJob.id == job_id)
        )
        return result.scalar_one_or_none()
    
    async def get_jobs_by_project(
        self,
        project_id: uuid.UUID,
        status: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[BackgroundJob]:
        """
        Get background jobs for a project.
        
        Args:
            project_id: Project ID
            status: Optional status filter
            limit: Max jobs to return
            offset: Offset for pagination
            
        Returns:
            List of BackgroundJob instances
        """
        query = select(BackgroundJob).where(
            BackgroundJob.goal_id == project_id
        )
        
        if status:
            query = query.where(BackgroundJob.status == status)
        
        query = query.order_by(BackgroundJob.created_at.desc())
        query = query.offset(offset).limit(limit)
        
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def get_job_stats(self, project_id: uuid.UUID) -> dict[str, Any]:
        """
        Get job statistics for a project.
        
        Args:
            project_id: Project ID
            
        Returns:
            Dict with job statistics
        """
        # Count by status
        status_counts = {}
        for status in ["queued", "running", "completed", "failed", "retrying"]:
            result = await self.db.execute(
                select(func.count(BackgroundJob.id)).where(
                    BackgroundJob.goal_id == project_id,
                    BackgroundJob.status == status,
                )
            )
            status_counts[status] = result.scalar() or 0
        
        # Get average duration for completed jobs
        result = await self.db.execute(
            select(
                func.avg(
                    func.extract("epoch", BackgroundJob.completed_at) -
                    func.extract("epoch", BackgroundJob.started_at)
                )
            ).where(
                BackgroundJob.goal_id == project_id,
                BackgroundJob.status == "completed",
                BackgroundJob.started_at.isnot(None),
                BackgroundJob.completed_at.isnot(None),
            )
        )
        avg_duration = result.scalar()
        
        return {
            "total_jobs": sum(status_counts.values()),
            "by_status": status_counts,
            "avg_duration_seconds": float(avg_duration) if avg_duration else None,
        }
    
    async def retry_job(self, job_id: uuid.UUID) -> BackgroundJob | None:
        """
        Retry a failed job.
        
        Args:
            job_id: Job ID
            
        Returns:
            Updated BackgroundJob or None
        """
        job = await self.get_job(job_id)
        if not job:
            return None
        
        if job.status not in ["failed", "retrying"]:
            raise ValueError(f"Cannot retry job in status: {job.status}")
        
        job.status = "queued"
        job.error_message = None
        job.started_at = None
        job.completed_at = None
        job.worker_id = None
        
        await self.db.flush()
        return job
    
    async def cancel_job(self, job_id: uuid.UUID) -> BackgroundJob | None:
        """
        Cancel a queued job.
        
        Args:
            job_id: Job ID
            
        Returns:
            Updated BackgroundJob or None
        """
        job = await self.get_job(job_id)
        if not job:
            return None
        
        if job.status != "queued":
            raise ValueError(f"Cannot cancel job in status: {job.status}")
        
        job.status = "cancelled"
        job.completed_at = datetime.now(timezone.utc)
        
        await self.db.flush()
        return job
    
    async def cleanup_old_jobs(self, days: int = 30) -> int:
        """
        Clean up old completed/failed jobs.
        
        Args:
            days: Number of days to keep
            
        Returns:
            Number of jobs deleted
        """
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        result = await self.db.execute(
            select(BackgroundJob).where(
                BackgroundJob.status.in_(["completed", "failed", "cancelled"]),
                BackgroundJob.completed_at < cutoff_date,
            )
        )
        old_jobs = list(result.scalars().all())
        
        for job in old_jobs:
            await self.db.delete(job)
        
        await self.db.flush()
        return len(old_jobs)
