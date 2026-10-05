import uuid
import time

from opentelemetry import trace
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.task import Project, Task, TaskDependency
from src.services.llm_client import llm_client
from src.observability.logging import get_logger

tracer = trace.get_tracer("ceo_agent")

DECOMPOSITION_PROMPT = """You are a CEO Agent for an AI workforce platform.

Given a high-level goal, decompose it into:
1. A list of projects (max 5)
2. Each project contains tasks (max 10 per project)
3. Dependencies between tasks (which tasks must complete before others)
4. Priority for each task (1=highest, 5=lowest)
5. Wave number (tasks in same wave can run in parallel)

Goal: {goal_text}

Constraints: {constraints}

Respond with JSON:
{{
  "projects": [
    {{
      "name": "Project Name",
      "tasks": [
        {{
          "name": "Task Name",
          "description": "What this task does",
          "priority": 1,
          "depends_on": ["Task Name it depends on"],
          "wave": 1
        }}
      ]
    }}
  ]
}}"""


class CEODecomposeAgent:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.log = get_logger("ceo_agent")

    async def decompose(
        self,
        company_id: uuid.UUID,
        goal_text: str,
        constraints: dict | None = None,
    ) -> Project:
        start = time.monotonic()

        with tracer.start_as_current_span("ceo_agent.decompose") as span:
            span.set_attribute("company_id", str(company_id))
            self.log.info("decompose_started", company_id=str(company_id))

            response = await llm_client.json(
                DECOMPOSITION_PROMPT.format(
                    goal_text=goal_text,
                    constraints=str(constraints or {}),
                ),
                system_prompt="You are a strategic planning agent. Decompose goals into actionable tasks.",
            )

            first_project = response["projects"][0]
            project = Project(
                company_id=company_id,
                name=first_project["name"],
                goal_text=goal_text,
                status="planning",
            )
            self.db.add(project)
            await self.db.flush()

            task_map: dict[str, uuid.UUID] = {}
            for task_data in first_project["tasks"]:
                task = Task(
                    project_id=project.id,
                    name=task_data["name"],
                    description=task_data.get("description", ""),
                    priority=task_data.get("priority", 3),
                    wave_number=task_data.get("wave", 1),
                    status="pending",
                )
                self.db.add(task)
                await self.db.flush()
                task_map[task_data["name"]] = task.id

            for task_data in first_project["tasks"]:
                for dep_name in task_data.get("depends_on", []):
                    if dep_name in task_map:
                        dep = TaskDependency(
                            task_id=task_map[task_data["name"]],
                            depends_on_id=task_map[dep_name],
                        )
                        self.db.add(dep)

            project.status = "active"

            duration_ms = (time.monotonic() - start) * 1000
            self.log.info(
                "decompose_completed",
                project_id=str(project.id),
                task_count=len(first_project["tasks"]),
                duration_ms=round(duration_ms, 2),
            )

            return project
