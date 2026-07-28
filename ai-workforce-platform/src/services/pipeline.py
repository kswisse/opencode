import uuid
from sqlalchemy.ext.asyncio import AsyncSession

from src.services.ceo_agent import CEODecomposeAgent
from src.services.agent_factory import AgentFactory
from src.services.task_scheduler import TaskScheduler
from src.services.memory_service import MemoryService
from src.schemas.agent import AgentCreate


class Pipeline:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def execute_goal(
        self,
        company_id: uuid.UUID,
        goal_text: str,
        constraints: dict | None = None,
    ) -> dict:
        ceo = CEODecomposeAgent(self.db)
        project = await ceo.decompose(company_id, goal_text, constraints)

        factory = AgentFactory(self.db)
        agent_names = ["Research Agent", "Analysis Agent", "Execution Agent"]
        agents = []
        for name in agent_names:
            agent = await factory.create_agent(
                company_id,
                AgentCreate(name=name, agent_type="general"),
            )
            agents.append(agent)

        scheduler = TaskScheduler(self.db)
        await scheduler.execute_project(project.id)

        memory = MemoryService(self.db)
        await memory.store_knowledge(
            company_id=company_id,
            knowledge_type="goal_completed",
            content=f"Completed goal: {goal_text}",
            confidence=0.8,
            source="pipeline",
        )

        return {
            "project_id": str(project.id),
            "agents_created": len(agents),
            "status": "completed",
        }
