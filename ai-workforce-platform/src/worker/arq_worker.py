import json
import time
import uuid
from datetime import datetime, timezone
from typing import Any

from arq import cron
from arq.connections import RedisSettings
from arq.worker import Worker
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from opentelemetry import trace

from src.config import settings
from src.database import Base
from src.models.background_job import BackgroundJob
from src.models.task import Task, Project
from src.models.agent import Agent
from src.services.llm_client import llm_client
from src.services.agent_factory import AgentFactory
from src.observability.logging import get_logger
from src.observability.correlation import set_request_id, generate_request_id
from src.observability.metrics import JOB_DURATION, JOBS_TOTAL

tracer = trace.get_tracer("arq.worker")

# Database setup for worker
engine = create_async_engine(settings.database_url, echo=settings.debug)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


TASK_EXECUTION_PROMPT = """You are an AI worker executing a specific task.

Task: {task_name}
Description: {task_description}
Project Context: {project_goal}

Complete this task by providing a detailed output. Be specific and actionable."""


async def execute_task_job(ctx: dict[str, Any], job_id: str, task_id: str) -> dict[str, Any]:
    """
    Execute a single task as a background job.
    """
    worker_id = ctx.get("worker_id", str(uuid.uuid4()))
    log = get_logger("worker.execute_task")

    # Generate a correlation ID for this job run
    rid = generate_request_id()
    set_request_id(rid)

    # Extract goal_id from payload if available
    goal_id = ctx.get("job_kwargs", {}).get("goal_id")

    start = time.monotonic()

    with tracer.start_as_current_span("execute_task_job") as span:
        span.set_attribute("job_id", job_id)
        span.set_attribute("task_id", task_id)
        span.set_attribute("worker_id", worker_id)
        if goal_id:
            span.set_attribute("goal_id", goal_id)

        log.info(
            "job_started",
            job_id=job_id,
            task_id=task_id,
            worker_id=worker_id,
            goal_id=goal_id,
        )

        async with async_session() as db:
            try:
                # Get the background job
                job_result = await db.execute(
                    select(BackgroundJob).where(BackgroundJob.id == uuid.UUID(job_id))
                )
                job = job_result.scalar_one_or_none()

                if not job:
                    JOBS_TOTAL.labels(job_type="execute_task", status="not_found").inc()
                    log.error("job_not_found", job_id=job_id)
                    return {"error": f"Job {job_id} not found"}

                # Update job status to running
                job.status = "running"
                job.worker_id = worker_id
                job.started_at = datetime.now(timezone.utc)
                await db.commit()

                log.info(
                    "job_running",
                    job_id=job_id,
                    task_id=task_id,
                    goal_id=str(job.goal_id) if job.goal_id else None,
                )

                # Get the task
                task_result = await db.execute(
                    select(Task).where(Task.id == uuid.UUID(task_id))
                )
                task = task_result.scalar_one_or_none()

                if not task:
                    job.status = "failed"
                    job.error_message = f"Task {task_id} not found"
                    job.completed_at = datetime.now(timezone.utc)
                    await db.commit()
                    JOBS_TOTAL.labels(job_type="execute_task", status="failed").inc()
                    log.error("task_not_found", job_id=job_id, task_id=task_id)
                    return {"error": f"Task {task_id} not found"}

                # Get project context
                project_result = await db.execute(
                    select(Project).where(Project.id == task.project_id)
                )
                project = project_result.scalar_one()

                log.info(
                    "pipeline_stage",
                    stage="agent_selection",
                    job_id=job_id,
                    project_id=str(project.id),
                    goal_id=str(project.company_id),
                )

                # Find an available agent
                factory = AgentFactory(db)
                agent = await factory.find_available_agent(
                    company_id=project.company_id,
                    capabilities_needed=[],
                )

                if not agent:
                    job.status = "failed"
                    job.error_message = "No available agent found"
                    job.completed_at = datetime.now(timezone.utc)
                    await db.commit()
                    JOBS_TOTAL.labels(job_type="execute_task", status="failed").inc()
                    log.error("no_agent_available", job_id=job_id)
                    return {"error": "No available agent found"}

                # Update task status
                task.assigned_agent_id = agent.id
                task.status = "running"
                await db.flush()

                log.info(
                    "pipeline_stage",
                    stage="llm_execution",
                    job_id=job_id,
                    agent_id=str(agent.id),
                    agent_name=agent.name,
                )

                # Execute the task with LLM
                prompt = TASK_EXECUTION_PROMPT.format(
                    task_name=task.name,
                    task_description=task.description or "",
                    project_goal=project.goal_text,
                )

                response = await llm_client.json(
                    prompt,
                    system_prompt=agent.system_prompt or "Complete the given task.",
                )

                # Update task with result
                task.output = response
                task.status = "completed"
                task.completed_at = datetime.now(timezone.utc)

                # Update agent stats
                agent.total_tasks += 1
                agent.successful_tasks += 1

                # Update job status
                job.status = "completed"
                job.result = response
                job.completed_at = datetime.now(timezone.utc)

                await db.commit()

                duration_ms = (time.monotonic() - start) * 1000

                JOBS_TOTAL.labels(job_type="execute_task", status="completed").inc()
                JOB_DURATION.labels(job_type="execute_task", status="completed").observe(duration_ms / 1000)

                log.info(
                    "job_completed",
                    job_id=job_id,
                    task_id=task_id,
                    agent_id=str(agent.id),
                    duration_ms=round(duration_ms, 2),
                )

                return {
                    "job_id": job_id,
                    "task_id": task_id,
                    "status": "completed",
                    "agent_id": str(agent.id),
                }

            except Exception as e:
                await db.rollback()

                duration_ms = (time.monotonic() - start) * 1000

                log.error(
                    "job_failed",
                    job_id=job_id,
                    task_id=task_id,
                    error=str(e),
                    duration_ms=round(duration_ms, 2),
                    exc_info=True,
                )

                # Update job with error
                try:
                    job_result = await db.execute(
                        select(BackgroundJob).where(BackgroundJob.id == uuid.UUID(job_id))
                    )
                    job = job_result.scalar_one_or_none()

                    if job:
                        job.error_message = str(e)
                        job.retry_count += 1

                        if job.retry_count < job.max_retries:
                            job.status = "retrying"
                            JOBS_TOTAL.labels(job_type="execute_task", status="retrying").inc()
                        else:
                            job.status = "failed"
                            JOBS_TOTAL.labels(job_type="execute_task", status="failed").inc()

                        job.completed_at = datetime.now(timezone.utc)
                        await db.commit()

                except Exception as inner_e:
                    log.error("job_error_update_failed", job_id=job_id, error=str(inner_e))

                JOB_DURATION.labels(job_type="execute_task", status="failed").observe(duration_ms / 1000)
                raise


async def enqueue_task_execution(
    db: AsyncSession,
    project_id: uuid.UUID,
    task_id: uuid.UUID,
    job_type: str = "execute_task",
    payload: dict | None = None,
    request_id: str | None = None,
) -> BackgroundJob:
    """
    Enqueue a task execution job.
    """
    from src.observability.correlation import get_request_id

    job = BackgroundJob(
        goal_id=project_id,
        job_type=job_type,
        status="queued",
        payload=payload or {"task_id": str(task_id)},
        max_retries=3,
        request_id=request_id or get_request_id(),
    )
    db.add(job)
    await db.flush()

    return job


# ARQ Worker Settings
class WorkerSettings:
    """ARQ Worker configuration."""

    functions = [execute_task_job]
    redis_settings = RedisSettings.from_dsn(settings.redis_url)
    max_jobs = 10
    job_timeout = 300  # 5 minutes
    poll_delay = 0.5
    max_tries = 3
    retry_delay = 60  # 1 minute

    async def on_startup(self, ctx: dict[str, Any]) -> None:
        """Called when worker starts."""
        worker_id = str(uuid.uuid4())
        ctx["worker_id"] = worker_id
        log = get_logger("worker")
        log.info("worker_started", worker_id=worker_id)

    async def on_shutdown(self, ctx: dict[str, Any]) -> None:
        """Called when worker shuts down."""
        log = get_logger("worker")
        log.info("worker_shutdown", worker_id=ctx.get("worker_id"))

    async def on_job_start(self, ctx: dict[str, Any], job_id: str) -> None:
        """Called when a job starts."""
        log = get_logger("worker")
        log.info("job_starting", job_id=job_id, worker_id=ctx.get("worker_id"))

    async def on_job_end(self, ctx: dict[str, Any], job_id: str, result: Any) -> None:
        """Called when a job ends."""
        log = get_logger("worker")
        log.info("job_ended", job_id=job_id, result_type=type(result).__name__)


# Health check function
async def health_check() -> dict[str, Any]:
    """Health check for the worker."""
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# Cron jobs (optional)
async def cleanup_old_jobs(ctx: dict[str, Any]) -> None:
    """Clean up old completed/failed jobs older than 30 days."""
    log = get_logger("worker.cron")
    async with async_session() as db:
        try:
            log.info("cleanup_started")
        except Exception as e:
            log.error("cleanup_failed", error=str(e))


# Worker configuration with cron jobs
class WorkerSettingsWithCron(WorkerSettings):
    """Worker settings with scheduled cron jobs."""

    cron_jobs = [
        cron(
            cleanup_old_jobs,
            hour=3,
            minute=0,
            run_at_startup=False,
        ),
    ]
