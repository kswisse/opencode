import uuid
import time

from opentelemetry import trace
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.agent import Agent, AgentCapability
from src.schemas.agent import AgentCreate
from src.observability.logging import get_logger
from src.observability.metrics import DB_QUERIES

tracer = trace.get_tracer("agent_factory")


AGENT_TEMPLATES = {
    "researcher": {
        "system_prompt": "You are a research specialist. Find accurate, relevant information and summarize findings clearly.",
        "capabilities": ["research", "analysis", "summarization"],
    },
    "writer": {
        "system_prompt": "You are a content writer. Create engaging, well-structured content based on provided briefs.",
        "capabilities": ["writing", "editing", "content_creation"],
    },
    "coder": {
        "system_prompt": "You are a software engineer. Write clean, efficient code and follow best practices.",
        "capabilities": ["programming", "debugging", "code_review"],
    },
    "analyst": {
        "system_prompt": "You are a data analyst. Analyze data, identify patterns, and provide actionable insights.",
        "capabilities": ["data_analysis", "visualization", "statistics"],
    },
    "marketer": {
        "system_prompt": "You are a marketing specialist. Create marketing strategies and campaigns.",
        "capabilities": ["marketing", "seo", "social_media"],
    },
    "general": {
        "system_prompt": "You are a helpful AI assistant. Complete tasks accurately and efficiently.",
        "capabilities": ["general_task"],
    },
}


class AgentFactory:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.log = get_logger("agent_factory")

    async def create_agent(
        self,
        company_id: uuid.UUID,
        request: AgentCreate,
    ) -> Agent:
        with tracer.start_as_current_span("agent_factory.create_agent") as span:
            span.set_attribute("company_id", str(company_id))
            span.set_attribute("agent_type", request.agent_type)

            template = AGENT_TEMPLATES.get(request.agent_type, AGENT_TEMPLATES["general"])
            system_prompt = request.system_prompt or template["system_prompt"]

            agent = Agent(
                company_id=company_id,
                name=request.name,
                agent_type=request.agent_type,
                status="idle",
                system_prompt=system_prompt,
                model=request.model,
                config=request.config,
            )
            self.db.add(agent)
            await self.db.flush()
            DB_QUERIES.labels(operation="insert").inc()

            for cap_name in (request.capabilities or template["capabilities"]):
                cap = AgentCapability(
                    agent_id=agent.id,
                    capability_name=cap_name,
                    proficiency="competent",
                )
                self.db.add(cap)

            self.log.info(
                "agent_created",
                agent_id=str(agent.id),
                agent_type=request.agent_type,
                name=request.name,
            )

            return agent

    async def get_agent(self, agent_id: uuid.UUID) -> Agent | None:
        with tracer.start_as_current_span("agent_factory.get_agent"):
            result = await self.db.execute(select(Agent).where(Agent.id == agent_id))
            DB_QUERIES.labels(operation="select").inc()
            return result.scalar_one_or_none()

    async def list_agents(
        self, company_id: uuid.UUID, limit: int = 20, offset: int = 0
    ) -> list[Agent]:
        with tracer.start_as_current_span("agent_factory.list_agents"):
            result = await self.db.execute(
                select(Agent)
                .where(Agent.company_id == company_id)
                .offset(offset)
                .limit(limit)
            )
            DB_QUERIES.labels(operation="select").inc()
            return list(result.scalars().all())

    async def find_available_agent(
        self, company_id: uuid.UUID, capabilities_needed: list[str]
    ) -> Agent | None:
        with tracer.start_as_current_span("agent_factory.find_available_agent") as span:
            span.set_attribute("company_id", str(company_id))

            result = await self.db.execute(
                select(Agent)
                .where(Agent.company_id == company_id, Agent.status == "idle")
            )
            DB_QUERIES.labels(operation="select").inc()
            agents = list(result.scalars().all())

            for agent in agents:
                caps_result = await self.db.execute(
                    select(AgentCapability).where(AgentCapability.agent_id == agent.id)
                )
                DB_QUERIES.labels(operation="select").inc()
                agent_caps = [c.capability_name for c in caps_result.scalars().all()]
                if all(cap in agent_caps for cap in capabilities_needed):
                    return agent
            return None
