import uuid
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_db, get_current_user
from src.schemas.agent import AgentCreate, AgentResponse, AgentListResponse
from src.schemas.auth import TokenData
from src.services.agent_factory import AgentFactory
from src.core.exceptions import NotFoundError

router = APIRouter(prefix="/agents", tags=["agents"])


@router.post("", response_model=AgentResponse)
async def create_agent(
    body: AgentCreate,
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    company_id = uuid.UUID(current_user.company_id)
    factory = AgentFactory(db)
    agent = await factory.create_agent(company_id, body)
    return agent


@router.get("", response_model=AgentListResponse)
async def list_agents(
    current_user: TokenData = Depends(get_current_user),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    company_id = uuid.UUID(current_user.company_id)
    factory = AgentFactory(db)
    agents = await factory.list_agents(company_id, limit, offset)
    return AgentListResponse(agents=agents, total=len(agents))


@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(
    agent_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    factory = AgentFactory(db)
    agent = await factory.get_agent(agent_id)
    if not agent:
        raise NotFoundError("Agent", str(agent_id))
    return agent
