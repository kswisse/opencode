import asyncio
import uuid
import time
from datetime import datetime, timezone

from opentelemetry import trace
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.task import Task, TaskDependency, Project
from src.models.agent import Agent
from src.services.llm_client import llm_client
from src.services.agent_factory import AgentFactory
from src.observability.logging import get_logger
from src.observability.metrics import SCHEDULER_TASKS, DB_QUERIES

tracer = trace.get_tracer("task_scheduler")


TASK_EXECUTION_PROMPT = """You are an AI worker executing a specific task.

Task: {task_name}
Description: {task_description}
Project Context: {project_goal}

Complete this task by providing a detailed output. Be specific and actionable."""


class TaskScheduler:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.log = get_logger("task_scheduler")

    async def execute_project(self, project_id: uuid.UUID) -> None:
        with tracer.start_as_current_span("scheduler.execute_project") as span:
            span.set_attribute("project_id", str(project_id))

            result = await self.db.execute(
                select(Task).where(Task.project_id == project_id)
            )
            DB_QUERIES.labels(operation="select").inc()
            all_tasks = list(result.scalars().all())

            self.log.info(
                "execute_project_started",
                project_id=str(project_id),
                task_count=len(all_tasks),
            )

            waves = self._compute_waves(all_tasks)
            for wave_num in sorted(waves.keys()):
                wave_tasks = waves[wave_num]
                await self._execute_wave(wave_tasks)

    def _compute_waves(self, tasks: list[Task]) -> dict[int, list[Task]]:
        waves: dict[int, list[Task]] = {}
        for task in tasks:
            wave = task.wave_number
            if wave not in waves:
                waves[wave] = []
            waves[wave].append(task)
        return waves

    async def _execute_wave(self, tasks: list[Task]) -> None:
        coros = [self._execute_single_task(task) for task in tasks]
        await asyncio.gather(*coros, return_exceptions=True)

    async def _execute_single_task(self, task: Task) -> Task:
        start = time.monotonic()

        with tracer.start_as_current_span("scheduler.execute_task") as span:
            span.set_attribute("task_id", str(task.id))
            span.set_attribute("task_name", task.name)

            deps_met = await self._check_dependencies_met(task)
            if not deps_met:
                task.status = "blocked"
                SCHEDULER_TASKS.labels(status="blocked").inc()
                self.log.info("task_blocked", task_id=str(task.id))
                return task

            agent = await self._assign_agent(task)
            if not agent:
                task.status = "failed"
                task.error = "No available agent"
                SCHEDULER_TASKS.labels(status="failed").inc()
                self.log.error("task_no_agent", task_id=str(task.id))
                return task

            task.assigned_agent_id = agent.id
            task.status = "running"
            await self.db.flush()

            self.log.info(
                "task_running",
                task_id=str(task.id),
                agent_id=str(agent.id),
            )

            try:
                project_result = await self.db.execute(
                    select(Project).where(Project.id == task.project_id)
                )
                DB_QUERIES.labels(operation="select").inc()
                project = project_result.scalar_one()

                prompt = TASK_EXECUTION_PROMPT.format(
                    task_name=task.name,
                    task_description=task.description or "",
                    project_goal=project.goal_text,
                )

                response = await llm_client.json(
                    prompt,
                    system_prompt=agent.system_prompt or "Complete the given task.",
                )

                task.output = response
                task.status = "completed"
                task.completed_at = datetime.now(timezone.utc)

                agent.total_tasks += 1
                agent.successful_tasks += 1

                duration_ms = (time.monotonic() - start) * 1000
                SCHEDULER_TASKS.labels(status="completed").inc()

                self.log.info(
                    "task_completed",
                    task_id=str(task.id),
                    duration_ms=round(duration_ms, 2),
                )

            except Exception as e:
                task.error = str(e)
                task.retry_count += 1
                if task.retry_count < task.max_retries:
                    task.status = "pending"
                else:
                    task.status = "failed"

                duration_ms = (time.monotonic() - start) * 1000
                SCHEDULER_TASKS.labels(status="failed").inc()

                self.log.error(
                    "task_failed",
                    task_id=str(task.id),
                    error=str(e),
                    duration_ms=round(duration_ms, 2),
                    exc_info=True,
                )

            return task

    async def _check_dependencies_met(self, task: Task) -> bool:
        result = await self.db.execute(
            select(TaskDependency).where(TaskDependency.task_id == task.id)
        )
        DB_QUERIES.labels(operation="select").inc()
        deps = result.scalars().all()

        for dep in deps:
            dep_result = await self.db.execute(
                select(Task).where(Task.id == dep.depends_on_id)
            )
            DB_QUERIES.labels(operation="select").inc()
            dep_task = dep_result.scalar_one_or_none()
            if dep_task and dep_task.status != "completed":
                return False
        return True

    async def _assign_agent(self, task: Task) -> Agent | None:
        factory = AgentFactory(self.db)
        return await factory.find_available_agent(
            company_id=uuid.uuid4(),
            capabilities_needed=[],
        )
