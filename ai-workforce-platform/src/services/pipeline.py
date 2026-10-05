import uuid
import time

from opentelemetry import trace
from sqlalchemy.ext.asyncio import AsyncSession

from src.services.ceo_agent import CEODecomposeAgent
from src.services.agent_factory import AgentFactory
from src.services.task_scheduler import TaskScheduler
from src.services.memory_service import MemoryService
from src.schemas.agent import AgentCreate
from src.observability.logging import get_logger
from src.observability.metrics import PIPELINE_SUCCESS, PIPELINE_FAILURE

tracer = trace.get_tracer("pipeline")


class Pipeline:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.log = get_logger("pipeline")

    async def execute_goal(
        self,
        company_id: uuid.UUID,
        goal_text: str,
        constraints: dict | None = None,
    ) -> dict:
        start = time.monotonic()

        with tracer.start_as_current_span("pipeline.execute_goal") as span:
            span.set_attribute("company_id", str(company_id))
            span.set_attribute("goal_text", goal_text[:200])

            self.log.info(
                "pipeline_started",
                company_id=str(company_id),
                goal_text=goal_text[:100],
            )

            try:
                # Stage 1: CEO Agent decomposes goal
                with tracer.start_as_current_span("ceo_agent.decompose"):
                    self.log.info(
                        "pipeline_stage",
                        stage="ceo_agent_decompose",
                        company_id=str(company_id),
                    )
                    ceo = CEODecomposeAgent(self.db)
                    project = await ceo.decompose(company_id, goal_text, constraints)

                # Stage 2: Agent Factory creates agents
                with tracer.start_as_current_span("agent_factory.create_agents"):
                    self.log.info(
                        "pipeline_stage",
                        stage="agent_factory",
                        project_id=str(project.id),
                    )
                    factory = AgentFactory(self.db)
                    agent_names = ["Research Agent", "Analysis Agent", "Execution Agent"]
                    agents = []
                    for name in agent_names:
                        agent = await factory.create_agent(
                            company_id,
                            AgentCreate(name=name, agent_type="general"),
                        )
                        agents.append(agent)

                # Stage 3: Scheduler executes project
                with tracer.start_as_current_span("scheduler.execute_project"):
                    self.log.info(
                        "pipeline_stage",
                        stage="task_scheduler",
                        project_id=str(project.id),
                        task_count=len(agents),
                    )
                    scheduler = TaskScheduler(self.db)
                    await scheduler.execute_project(project.id)

                # Stage 4: Memory stores knowledge
                with tracer.start_as_current_span("memory.store_knowledge"):
                    self.log.info(
                        "pipeline_stage",
                        stage="memory_store",
                        company_id=str(company_id),
                    )
                    memory = MemoryService(self.db)
                    await memory.store_knowledge(
                        company_id=company_id,
                        knowledge_type="goal_completed",
                        content=f"Completed goal: {goal_text}",
                        confidence=0.8,
                        source="pipeline",
                    )

                duration_ms = (time.monotonic() - start) * 1000
                PIPELINE_SUCCESS.inc()

                self.log.info(
                    "pipeline_completed",
                    project_id=str(project.id),
                    agents_created=len(agents),
                    duration_ms=round(duration_ms, 2),
                )

                return {
                    "project_id": str(project.id),
                    "agents_created": len(agents),
                    "status": "completed",
                }

            except Exception as e:
                duration_ms = (time.monotonic() - start) * 1000
                PIPELINE_FAILURE.inc()

                self.log.error(
                    "pipeline_failed",
                    error=str(e),
                    company_id=str(company_id),
                    duration_ms=round(duration_ms, 2),
                    exc_info=True,
                )
                raise
