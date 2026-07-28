from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession


async def get_db(request: Request) -> AsyncSession:
    session_factory = request.app.state.db_session
    async with session_factory() as session:
        yield session
