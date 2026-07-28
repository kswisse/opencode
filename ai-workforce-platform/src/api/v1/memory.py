import uuid
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_db
from src.schemas.memory import MemoryCreate, MemoryResponse, MemorySearchRequest, MemorySearchResponse
from src.services.memory_service import MemoryService

router = APIRouter(prefix="/memory", tags=["memory"])


@router.post("/episodic", response_model=MemoryResponse)
async def create_episodic_memory(
    body: MemoryCreate,
    company_id: uuid.UUID = Depends(lambda: uuid.uuid4()),
    agent_id: uuid.UUID = Depends(lambda: uuid.uuid4()),
    db: AsyncSession = Depends(get_db),
):
    service = MemoryService(db)
    memory = await service.store_episodic(
        agent_id=agent_id,
        company_id=company_id,
        event_type=body.event_type or "general",
        content=body.content,
        metadata=body.metadata,
    )
    return memory


@router.post("/semantic", response_model=MemoryResponse)
async def create_semantic_memory(
    body: MemoryCreate,
    company_id: uuid.UUID = Depends(lambda: uuid.uuid4()),
    db: AsyncSession = Depends(get_db),
):
    service = MemoryService(db)
    memory = await service.store_knowledge(
        company_id=company_id,
        knowledge_type=body.knowledge_type or "general",
        content=body.content,
    )
    return memory


@router.post("/search", response_model=MemorySearchResponse)
async def search_memory(
    body: MemorySearchRequest,
    company_id: uuid.UUID = Depends(lambda: uuid.uuid4()),
    db: AsyncSession = Depends(get_db),
):
    service = MemoryService(db)
    if body.memory_type == "episodic":
        results = await service.search_episodic(company_id, body.query, body.limit)
    elif body.memory_type == "semantic":
        results = await service.search_semantic(company_id, body.query, body.limit)
    else:
        episodic = await service.search_episodic(company_id, body.query, body.limit)
        semantic = await service.search_semantic(company_id, body.query, body.limit)
        results = episodic + semantic

    return MemorySearchResponse(results=results, total=len(results))
