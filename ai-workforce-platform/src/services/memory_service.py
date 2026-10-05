import uuid
import time

from opentelemetry import trace
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.memory import EpisodicMemory, SemanticMemory
from src.observability.logging import get_logger
from src.observability.metrics import MEMORY_OPS, DB_QUERIES

tracer = trace.get_tracer("memory_service")


class MemoryService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.log = get_logger("memory_service")

    async def store_episodic(
        self,
        agent_id: uuid.UUID,
        company_id: uuid.UUID,
        event_type: str,
        content: str,
        task_id: uuid.UUID | None = None,
        metadata: dict | None = None,
    ) -> EpisodicMemory:
        with tracer.start_as_current_span("memory.store_episodic"):
            memory = EpisodicMemory(
                agent_id=agent_id,
                company_id=company_id,
                task_id=task_id,
                event_type=event_type,
                content=content,
                metadata_=metadata,
            )
            self.db.add(memory)
            MEMORY_OPS.labels(operation_type="store_episodic").inc()
            DB_QUERIES.labels(operation="insert").inc()

            self.log.info(
                "episodic_stored",
                agent_id=str(agent_id),
                event_type=event_type,
            )
            return memory

    async def store_knowledge(
        self,
        company_id: uuid.UUID,
        knowledge_type: str,
        content: str,
        confidence: float = 0.5,
        source: str | None = None,
    ) -> SemanticMemory:
        with tracer.start_as_current_span("memory.store_knowledge"):
            memory = SemanticMemory(
                company_id=company_id,
                knowledge_type=knowledge_type,
                content=content,
                confidence=confidence,
                source=source,
            )
            self.db.add(memory)
            MEMORY_OPS.labels(operation_type="store_knowledge").inc()
            DB_QUERIES.labels(operation="insert").inc()

            self.log.info(
                "knowledge_stored",
                knowledge_type=knowledge_type,
                confidence=confidence,
            )
            return memory

    async def search_episodic(
        self,
        company_id: uuid.UUID,
        query: str,
        limit: int = 10,
    ) -> list[EpisodicMemory]:
        with tracer.start_as_current_span("memory.search_episodic"):
            result = await self.db.execute(
                select(EpisodicMemory)
                .where(EpisodicMemory.company_id == company_id)
                .where(EpisodicMemory.content.ilike(f"%{query}%"))
                .order_by(EpisodicMemory.created_at.desc())
                .limit(limit)
            )
            DB_QUERIES.labels(operation="select").inc()
            MEMORY_OPS.labels(operation_type="search_episodic").inc()
            return list(result.scalars().all())

    async def search_semantic(
        self,
        company_id: uuid.UUID,
        query: str,
        limit: int = 10,
    ) -> list[SemanticMemory]:
        with tracer.start_as_current_span("memory.search_semantic"):
            result = await self.db.execute(
                select(SemanticMemory)
                .where(SemanticMemory.company_id == company_id)
                .where(SemanticMemory.content.ilike(f"%{query}%"))
                .order_by(SemanticMemory.confidence.desc())
                .limit(limit)
            )
            DB_QUERIES.labels(operation="select").inc()
            MEMORY_OPS.labels(operation_type="search_semantic").inc()
            return list(result.scalars().all())

    async def get_recent(
        self,
        agent_id: uuid.UUID,
        limit: int = 10,
    ) -> list[EpisodicMemory]:
        with tracer.start_as_current_span("memory.get_recent"):
            result = await self.db.execute(
                select(EpisodicMemory)
                .where(EpisodicMemory.agent_id == agent_id)
                .order_by(EpisodicMemory.created_at.desc())
                .limit(limit)
            )
            DB_QUERIES.labels(operation="select").inc()
            MEMORY_OPS.labels(operation_type="get_recent").inc()
            return list(result.scalars().all())
