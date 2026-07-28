import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.memory import EpisodicMemory, SemanticMemory


class MemoryService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def store_episodic(
        self,
        agent_id: uuid.UUID,
        company_id: uuid.UUID,
        event_type: str,
        content: str,
        task_id: uuid.UUID | None = None,
        metadata: dict | None = None,
    ) -> EpisodicMemory:
        memory = EpisodicMemory(
            agent_id=agent_id,
            company_id=company_id,
            task_id=task_id,
            event_type=event_type,
            content=content,
            metadata_=metadata,
        )
        self.db.add(memory)
        return memory

    async def store_knowledge(
        self,
        company_id: uuid.UUID,
        knowledge_type: str,
        content: str,
        confidence: float = 0.5,
        source: str | None = None,
    ) -> SemanticMemory:
        memory = SemanticMemory(
            company_id=company_id,
            knowledge_type=knowledge_type,
            content=content,
            confidence=confidence,
            source=source,
        )
        self.db.add(memory)
        return memory

    async def search_episodic(
        self,
        company_id: uuid.UUID,
        query: str,
        limit: int = 10,
    ) -> list[EpisodicMemory]:
        result = await self.db.execute(
            select(EpisodicMemory)
            .where(EpisodicMemory.company_id == company_id)
            .where(EpisodicMemory.content.ilike(f"%{query}%"))
            .order_by(EpisodicMemory.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def search_semantic(
        self,
        company_id: uuid.UUID,
        query: str,
        limit: int = 10,
    ) -> list[SemanticMemory]:
        result = await self.db.execute(
            select(SemanticMemory)
            .where(SemanticMemory.company_id == company_id)
            .where(SemanticMemory.content.ilike(f"%{query}%"))
            .order_by(SemanticMemory.confidence.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_recent(
        self,
        agent_id: uuid.UUID,
        limit: int = 10,
    ) -> list[EpisodicMemory]:
        result = await self.db.execute(
            select(EpisodicMemory)
            .where(EpisodicMemory.agent_id == agent_id)
            .order_by(EpisodicMemory.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
