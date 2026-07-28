import uuid
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_db
from src.schemas.goal import GoalSubmit, GoalResponse
from src.services.ceo_agent import CEODecomposeAgent

router = APIRouter(prefix="/goals", tags=["goals"])


@router.post("", response_model=GoalResponse)
async def submit_goal(
    body: GoalSubmit,
    company_id: uuid.UUID = Depends(lambda: uuid.uuid4()),
    db: AsyncSession = Depends(get_db),
):
    agent = CEODecomposeAgent(db)
    project = await agent.decompose(company_id, body.goal_text, body.constraints)
    return GoalResponse(
        id=project.id,
        company_id=project.company_id,
        goal_text=project.goal_text,
        status=project.status,
        created_at=project.created_at,
    )
