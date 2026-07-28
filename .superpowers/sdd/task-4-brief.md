# Task 4: API Service — FastAPI Application

**Files to create:**
- `apps/api/pyproject.toml`
- `apps/api/Dockerfile`
- `apps/api/src/__init__.py`
- `apps/api/src/main.py`
- `apps/api/src/config.py`
- `apps/api/src/routers/__init__.py`
- `apps/api/src/routers/videos.py`
- `apps/api/src/routers/candidates.py`
- `apps/api/src/routers/clips.py`
- `apps/api/src/routers/analytics.py`
- `apps/api/src/dependencies/__init__.py`
- `apps/api/src/dependencies/db.py`
- `apps/api/src/middleware/__init__.py`
- `apps/api/src/middleware/tenant.py`

## File Contents

### apps/api/pyproject.toml
```toml
[project]
name = "clippy-api"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "fastapi>=0.110",
    "uvicorn[standard]>=0.28",
    "websockets>=12.0",
    "clippy-models>=0.1.0",
    "clippy-config>=0.1.0",
    "clippy-storage>=0.1.0",
    "clippy-database>=0.1.0",
    "clippy-events>=0.1.0",
    "clippy-logging>=0.1.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

### apps/api/Dockerfile
```dockerfile
FROM python:3.12-slim

WORKDIR /app
COPY apps/api/pyproject.toml .
RUN pip install --no-cache-dir .

COPY packages/ /packages
RUN pip install --no-cache-dir /packages/*/

COPY apps/api/src/ ./src/

EXPOSE 8000
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### apps/api/src/main.py
```python
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
```

### apps/api/src/__init__.py
```python
```

### apps/api/src/config.py
```python
# Local config overrides for API service
# Main config is loaded from clippy_config package
```

### apps/api/src/routers/__init__.py
```python
```

### apps/api/src/routers/videos.py
```python
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from clippy_models import (
    Video, VideoCreateResponse, VideoConfirmRequest, VideoListResponse,
    SourceType, VideoStatus,
)
from clippy_database.models.video import VideoModel
from clippy_database.models.pipeline import PipelineRunModel
from ..dependencies.db import get_db
from datetime import datetime

router = APIRouter()


@router.post("/upload-url", response_model=VideoCreateResponse)
async def get_upload_url(request: Request):
    storage = request.app.state.storage
    import uuid
    video_id = uuid.uuid4()
    key = f"raw-videos/{video_id}.mp4"
    upload_info = await storage.generate_presigned_upload_url("raw-videos", key)
    return VideoCreateResponse(id=video_id, **upload_info)


@router.post("/confirm", response_model=Video)
async def confirm_video(body: VideoConfirmRequest, request: Request, db: AsyncSession = Depends(get_db)):
    import uuid
    video_id = uuid.uuid4()
    tenant_id = request.state.tenant_id

    model = VideoModel(
        id=video_id,
        tenant_id=tenant_id,
        source_type=body.source_type,
        source_url=body.source_url,
        storage_key=body.storage_key,
        status=VideoStatus.PENDING,
        metadata=body.metadata,
    )
    db.add(model)
    await db.commit()
    await db.refresh(model)

    return Video(
        id=model.id,
        tenant_id=model.tenant_id,
        title=model.title,
        source_type=model.source_type,
        source_url=model.source_url,
        status=model.status,
        storage_key=model.storage_key,
        metadata=model.metadata,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


@router.get("", response_model=VideoListResponse)
async def list_videos(request: Request, db: AsyncSession = Depends(get_db), status: str | None = None):
    tenant_id = request.state.tenant_id
    query = select(VideoModel).where(VideoModel.tenant_id == tenant_id).order_by(VideoModel.created_at.desc())
    if status:
        query = query.where(VideoModel.status == VideoStatus(status))
    result = await db.execute(query)
    rows = result.scalars().all()

    videos = [
        Video(
            id=v.id, tenant_id=v.tenant_id, title=v.title,
            source_type=v.source_type, source_url=v.source_url,
            status=v.status, storage_key=v.storage_key,
            duration_seconds=v.duration_seconds, file_size_bytes=v.file_size_bytes,
            metadata=v.metadata, error_message=v.error_message,
            created_at=v.created_at, updated_at=v.updated_at,
        )
        for v in rows
    ]
    return VideoListResponse(videos=videos, total=len(videos))


@router.get("/{video_id}", response_model=dict)
async def get_video(video_id: UUID, request: Request, db: AsyncSession = Depends(get_db)):
    tenant_id = request.state.tenant_id
    result = await db.execute(
        select(VideoModel).where(VideoModel.id == video_id, VideoModel.tenant_id == tenant_id)
    )
    model = result.scalar_one_or_none()
    if not model:
        raise HTTPException(status_code=404, detail="Video not found")

    pipeline_result = await db.execute(
        select(PipelineRunModel).where(PipelineRunModel.video_id == video_id)
    )
    pipeline = pipeline_result.scalar_one_or_none()
    steps = pipeline.steps if pipeline else []

    video = Video(
        id=model.id, tenant_id=model.tenant_id, title=model.title,
        source_type=model.source_type, source_url=model.source_url,
        status=model.status, storage_key=model.storage_key,
        duration_seconds=model.duration_seconds, file_size_bytes=model.file_size_bytes,
        metadata=model.metadata, error_message=model.error_message,
        created_at=model.created_at, updated_at=model.updated_at,
    )
    return {"video": video, "pipeline": steps}
```

### apps/api/src/routers/candidates.py
```python
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from clippy_models import ClipCandidate, Clip, ScoreSet
from clippy_database.models.candidate import ClipCandidateModel
from clippy_database.models.clip import ClipModel
from ..dependencies.db import get_db
import uuid
from datetime import datetime

router = APIRouter()


def candidate_to_pydantic(c: ClipCandidateModel) -> ClipCandidate:
    return ClipCandidate(
        id=c.id,
        video_id=c.video_id,
        segment_ids=c.segment_ids or [],
        start_time=c.start_time,
        end_time=c.end_time,
        summary=c.summary,
        scores=ScoreSet(**c.scores) if c.scores else ScoreSet(),
        predicted_score=c.predicted_score or 0.0,
        actual_score=c.actual_score,
        status=c.status,
        created_at=c.created_at,
    )


@router.get("/video/{video_id}", response_model=dict)
async def get_candidates(video_id: UUID, request: Request, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(ClipCandidateModel).where(
            ClipCandidateModel.video_id == video_id,
        ).order_by(ClipCandidateModel.predicted_score.desc())
    )
    candidates = result.scalars().all()
    return {"candidates": [candidate_to_pydantic(c) for c in candidates]}


@router.post("/{candidate_id}/approve", response_model=dict)
async def approve_candidate(candidate_id: UUID, request: Request, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(ClipCandidateModel).where(ClipCandidateModel.id == candidate_id)
    )
    candidate = result.scalar_one_or_none()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    candidate.status = "approved"
    await db.commit()

    clip_id = uuid.uuid4()
    clip = ClipModel(
        id=clip_id,
        candidate_id=candidate_id,
        video_id=candidate.video_id,
        storage_key=f"clips/{candidate_id}.mp4",
    )
    db.add(clip)
    await db.commit()
    await db.refresh(clip)

    return {"clip": Clip(
        id=clip.id,
        candidate_id=clip.candidate_id,
        video_id=clip.video_id,
        storage_key=clip.storage_key,
        subtitle_key=clip.subtitle_key,
        duration_seconds=clip.duration_seconds,
        subtitle_style=clip.subtitle_style,
        file_format=clip.file_format,
        resolution=clip.resolution,
        created_at=clip.created_at,
    )}


@router.post("/{candidate_id}/reject", response_model=dict)
async def reject_candidate(candidate_id: UUID, request: Request, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(ClipCandidateModel).where(ClipCandidateModel.id == candidate_id)
    )
    candidate = result.scalar_one_or_none()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    candidate.status = "rejected"
    await db.commit()
    return {"ok": True}
```

### apps/api/src/routers/clips.py
```python
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from clippy_models import Clip
from clippy_database.models.clip import ClipModel
from ..dependencies.db import get_db

router = APIRouter()


def clip_to_pydantic(c: ClipModel) -> Clip:
    return Clip(
        id=c.id,
        candidate_id=c.candidate_id,
        video_id=c.video_id,
        storage_key=c.storage_key,
        subtitle_key=c.subtitle_key,
        duration_seconds=c.duration_seconds,
        subtitle_style=c.subtitle_style,
        file_format=c.file_format,
        resolution=c.resolution,
        created_at=c.created_at,
    )


@router.get("", response_model=dict)
async def list_clips(request: Request, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(ClipModel).order_by(ClipModel.created_at.desc())
    )
    clips = result.scalars().all()
    return {"clips": [clip_to_pydantic(c) for c in clips]}


@router.get("/{clip_id}", response_model=dict)
async def get_clip(clip_id: UUID, request: Request, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(ClipModel).where(ClipModel.id == clip_id)
    )
    clip = result.scalar_one_or_none()
    if not clip:
        raise HTTPException(status_code=404, detail="Clip not found")
    return {"clip": clip_to_pydantic(clip)}
```

### apps/api/src/routers/analytics.py
```python
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from clippy_models import Clip
from clippy_database.models.clip import ClipModel
from clippy_database.models.analytics import AnalyticsEventModel
from ..dependencies.db import get_db

router = APIRouter()


@router.post("/{clip_id}/analytics", response_model=dict)
async def record_analytics(clip_id: UUID, request: Request, db: AsyncSession = Depends(get_db)):
    body = await request.json()
    event = AnalyticsEventModel(
        clip_id=clip_id,
        tenant_id=request.state.tenant_id,
        platform=body.get("platform", "unknown"),
        views=body.get("views", 0),
        likes=body.get("likes", 0),
        shares=body.get("shares", 0),
        comments=body.get("comments", 0),
        watch_time_seconds=body.get("watch_time_seconds", 0),
        completion_rate=body.get("completion_rate", 0),
        ctr=body.get("ctr", 0),
    )
    db.add(event)
    await db.commit()
    return {"ok": True}


@router.get("/overview", response_model=dict)
async def get_analytics_overview(request: Request, db: AsyncSession = Depends(get_db)):
    total_clips = await db.scalar(select(func.count(ClipModel.id)))
    total_views_result = await db.execute(select(func.coalesce(func.sum(AnalyticsEventModel.views), 0)))
    total_views = total_views_result.scalar()
    total_likes_result = await db.execute(select(func.coalesce(func.sum(AnalyticsEventModel.likes), 0)))
    total_likes = total_likes_result.scalar()

    return {
        "total_clips": total_clips or 0,
        "total_views": total_views or 0,
        "total_likes": total_likes or 0,
        "total_shares": 0,
        "average_completion_rate": 0,
    }
```

### apps/api/src/dependencies/__init__.py
```python
```

### apps/api/src/dependencies/db.py
```python
from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession


async def get_db(request: Request) -> AsyncSession:
    session_factory = request.app.state.db_session
    async with session_factory() as session:
        yield session
```

### apps/api/src/middleware/__init__.py
```python
```

### apps/api/src/middleware/tenant.py
```python
from uuid import UUID
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

TENANT_ID = UUID("00000000-0000-0000-0000-000000000001")


class TenantMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request.state.tenant_id = TENANT_ID
        response = await call_next(request)
        return response
```

## Steps

1. Create all files under `C:\Opencode\clipping-agent\apps\api\`
2. Install the package: `pip install -e .`
3. Verify import works: `python -c "from src.main import app; print(f'FastAPI app created: {app.title}')"`
4. Verify routers registered: `python -c "from src.main import app; print([r.path for r in app.routes])"`

## Global Constraints
- FastAPI with async endpoints
- Dependency injection via Depends()
- All DB access via async SQLAlchemy sessions
- Tenant middleware for multi-tenant
- Pydantic models for request/response validation
