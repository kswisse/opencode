import uuid
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_db, get_current_user
from src.schemas.goal import GoalSubmit, GoalResponse
from src.schemas.auth import TokenData
from src.services.ceo_agent import CEODecomposeAgent

router = APIRouter(prefix="/goals", tags=["goals"])


@router.post("", response_model=GoalResponse)
async def submit_goal(
    body: GoalSubmit,
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    company_id = uuid.UUID(current_user.company_id)
    agent = CEODecomposeAgent(db)
    project = await agent.decompose(company_id, body.goal_text, body.constraints)
    return GoalResponse(
        id=project.id,
        company_id=project.company_id,
        goal_text=project.goal_text,
        status=project.status,
        created_at=project.created_at,
    )
