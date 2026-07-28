from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from clippy_config import ClippyConfig
from clippy_logging import setup_logging, get_logger
from clippy_database import create_engine, get_session, init_db
from clippy_storage import create_storage
from clippy_events import NATSClient
from .routers import videos, candidates, clips, analytics
from .middleware.tenant import TenantMiddleware

config = ClippyConfig()
logger = get_logger("clippy-api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging(config.environment)
    engine = create_engine(config.database.dsn)
    app.state.db_engine = engine
    app.state.db_session = get_session(engine)

    await init_db(engine)
    app.state.storage = create_storage(
        provider=config.storage.provider,
        endpoint=config.storage.endpoint,
        access_key=config.storage.access_key,
        secret_key=config.storage.secret_key,
    )

    nats = NATSClient(config.nats.servers)
    await nats.connect()
    app.state.nats = nats

    logger.info("application_started", environment=config.environment)
    yield

    await nats.close()
    await engine.dispose()


app = FastAPI(title="Clippy API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(TenantMiddleware)

app.include_router(videos.router, prefix="/videos", tags=["Videos"])
app.include_router(candidates.router, prefix="/candidates", tags=["Candidates"])
app.include_router(clips.router, prefix="/clips", tags=["Clips"])
app.include_router(analytics.router, prefix="/analytics", tags=["Analytics"])
