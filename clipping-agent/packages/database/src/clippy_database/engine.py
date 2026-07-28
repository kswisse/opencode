from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession


def create_engine(dsn: str, pool_size: int = 20, max_overflow: int = 10):
    engine = create_async_engine(dsn, pool_size=pool_size, max_overflow=max_overflow)
    return engine


def get_session(engine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(engine, expire_on_commit=False)


async def init_db(engine):
    from .models.base import Base
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
