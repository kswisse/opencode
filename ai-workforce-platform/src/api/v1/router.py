from fastapi import APIRouter

from src.api.v1.auth import router as auth_router
from src.api.v1.goals import router as goals_router
from src.api.v1.agents import router as agents_router
from src.api.v1.tasks import router as tasks_router
from src.api.v1.memory import router as memory_router
from src.api.v1.jobs import router as jobs_router

api_v1_router = APIRouter(prefix="/api/v1")
api_v1_router.include_router(auth_router)
api_v1_router.include_router(goals_router)
api_v1_router.include_router(agents_router)
api_v1_router.include_router(tasks_router)
api_v1_router.include_router(memory_router)
api_v1_router.include_router(jobs_router)
