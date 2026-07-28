import asyncio
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.task import Task, TaskDependency, Project
from src.models.agent import Agent
from src.services.llm_client import llm_client
from src.services.agent_factory import AgentFactory


TASK_EXECUTION_PROMPT = """You are an AI worker executing a specific task.

Task: {task_name}
Description: {task_description}
Project Context: {project_goal}

Complete this task by providing a detailed output. Be specific and actionable."""


class TaskScheduler:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def execute_project(self, project_id: uuid.UUID) -> None:
        result = await self.db.execute(
            select(Task).where(Task.project_id == project_id)
        )
        all_tasks = list(result.scalars().all())

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
        deps_met = await self._check_dependencies_met(task)
        if not deps_met:
            task.status = "blocked"
            return task

        agent = await self._assign_agent(task)
        if not agent:
            task.status = "failed"
            task.error = "No available agent"
            return task

        task.assigned_agent_id = agent.id
        task.status = "running"
        await self.db.flush()

        try:
            project_result = await self.db.execute(
                select(Project).where(Project.id == task.project_id)
            )
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

        except Exception as e:
            task.error = str(e)
            task.retry_count += 1
            if task.retry_count < task.max_retries:
                task.status = "pending"
            else:
                task.status = "failed"

        return task

    async def _check_dependencies_met(self, task: Task) -> bool:
        result = await self.db.execute(
            select(TaskDependency).where(TaskDependency.task_id == task.id)
        )
        deps = result.scalars().all()

        for dep in deps:
            dep_result = await self.db.execute(
                select(Task).where(Task.id == dep.depends_on_id)
            )
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
