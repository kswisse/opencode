# Clippy v1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the v1 MVP of Clippy — an AI clipping agent that ingests videos, transcribes/analyzes them, scores segments for virality, generates clips with subtitles, and learns from performance.

**Architecture:** Distributed system with FastAPI gateway, Temporal workflow engine for video pipelines, NATS event bus, PostgreSQL + Qdrant for storage, MinIO for object storage, and Next.js frontend. Everything runs via Docker Compose for local dev, designed for Kubernetes deployment.

**Tech Stack:** Python 3.12, FastAPI, Temporal.io Python SDK, NATS.py, SQLAlchemy async + Alembic, Pydantic v2, Next.js 14, Tailwind CSS, TanStack Query, Docker Compose.

## Global Constraints

- All Python packages use `pyproject.toml` (setuptools or hatchling), no `setup.py` or `requirements.txt`
- Every Python app/package has `src/` layout (not flat)
- All database access uses async SQLAlchemy 2.0 style
- All Pydantic models use `model_validator` / `field_validator` (v2 style)
- No hardcoded configuration — everything via YAML + env vars
- Every shared package is installable via `pip install -e packages/<name>` in dev
- Frontend uses Next.js 14 App Router, TypeScript strict mode
- Frontend must not use any state management beyond TanStack Query + React state
- Every Docker Compose service must be independently scalable
- All file paths use `/` separators (cross-platform compatible in Docker)
- Logging goes to stdout/stderr (12-factor app), never to files

---

## File Structure

### Root
```
clipping-agent/
├── pyproject.toml                 # Workspace root (optional, mostly for tooling)
├── docker-compose.yml             # Full stack (all services)
├── docker-compose.infra.yml       # Only infra (DB, Redis, MinIO, etc.)
├── .env.example
├── .gitignore
├── Makefile                       # Common commands
│
├── apps/
│   ├── api/
│   │   ├── pyproject.toml
│   │   ├── Dockerfile
│   │   └── src/
│   │       ├── __init__.py
│   │       ├── main.py            # FastAPI app factory
│   │       ├── config.py          # Service-specific config
│   │       ├── routers/
│   │       │   ├── __init__.py
│   │       │   ├── videos.py
│   │       │   ├── candidates.py
│   │       │   ├── clips.py
│   │       │   ├── analytics.py
│   │       │   └── profile.py
│   │       ├── dependencies/
│   │       │   ├── __init__.py
│   │       │   ├── db.py
│   │       │   └── auth.py
│   │       └── middleware/
│   │           ├── __init__.py
│   │           ├── tenant.py
│   │           └── error_handler.py
│   │
│   ├── frontend/                   # Next.js app
│   │   ├── package.json
│   │   ├── tsconfig.json
│   │   ├── next.config.ts
│   │   ├── tailwind.config.ts
│   │   ├── Dockerfile
│   │   └── src/
│   │       ├── app/
│   │       │   ├── layout.tsx
│   │       │   ├── page.tsx
│   │       │   └── (dashboard)/
│   │       │       ├── layout.tsx
│   │       │       ├── page.tsx
│   │       │       ├── upload/page.tsx
│   │       │       ├── videos/page.tsx
│   │       │       ├── videos/[id]/page.tsx
│   │       │       ├── clips/page.tsx
│   │       │       ├── clips/[id]/page.tsx
│   │       │       ├── analytics/page.tsx
│   │       │       └── settings/page.tsx
│   │       ├── components/
│   │       │   ├── ui/            # Primitives
│   │       │   ├── layout/        # Sidebar, Topbar, etc.
│   │       │   ├── upload/
│   │       │   ├── pipeline/
│   │       │   ├── candidates/
│   │       │   ├── clips/
│   │       │   ├── analytics/
│   │       │   └── settings/
│   │       ├── hooks/
│   │       ├── lib/
│   │       ├── providers/
│   │       └── styles/
│   │
│   └── worker/
│       ├── pyproject.toml
│       ├── Dockerfile
│       └── src/
│           ├── __init__.py
│           ├── main.py             # Worker entrypoint
│           ├── config.py
│           ├── workflows/
│           │   ├── __init__.py
│           │   ├── clip_pipeline.py
│           │   └── analytics.py
│           └── activities/
│               ├── __init__.py
│               ├── download.py
│               ├── transcribe.py
│               ├── scene_detect.py
│               ├── speaker_detect.py
│               ├── segment.py
│               ├── llm_analyze.py
│               ├── score.py
│               ├── generate_clip.py
│               ├── generate_subtitle.py
│               └── analytics.py
│
└── packages/
    ├── shared-models/
    │   ├── pyproject.toml
    │   └── src/
    │       ├── __init__.py
    │       ├── models/
    │       │   ├── __init__.py
    │       │   ├── video.py
    │       │   ├── clip.py
    │       │   ├── transcript.py
    │       │   ├── segment.py
    │       │   ├── analysis.py
    │       │   ├── scoring.py
    │       │   └── profile.py
    │       └── events.py           # NATS event schemas
    │
    ├── config/
    │   ├── pyproject.toml
    │   └── src/
    │       ├── __init__.py
    │       └── loader.py           # YAML + env config loader
    │
    ├── storage/
    │   ├── pyproject.toml
    │   └── src/
    │       ├── __init__.py
    │       └── client.py           # MinIO/S3 abstraction
    │
    ├── database/
    │   ├── pyproject.toml
    │   └── src/
    │       ├── __init__.py
    │       ├── engine.py           # Async engine + session factory
    │       ├── models/
    │       │   ├── __init__.py
    │       │   ├── base.py
    │       │   ├── video.py
    │       │   ├── pipeline.py
    │       │   ├── transcript.py
    │       │   ├── scene.py
    │       │   ├── segment.py
    │       │   ├── analysis.py
    │       │   ├── candidate.py
    │       │   ├── clip.py
    │       │   ├── analytics.py
    │       │   └── learning.py
    │       └── migrations/         # Alembic
    │           ├── env.py
    │           ├── alembic.ini
    │           └── versions/
    │
    ├── vectordb/
    │   ├── pyproject.toml
    │   └── src/
    │       ├── __init__.py
    │       └── client.py           # Qdrant wrapper
    │
    ├── events/
    │   ├── pyproject.toml
    │   └── src/
    │       ├── __init__.py
    │       └── nats_client.py      # NATS pub/sub wrapper
    │
    └── logging/
        ├── pyproject.toml
        └── src/
            ├── __init__.py
            └── logger.py           # Structured logging setup
```

---

## Task List

### Task 1: Project Scaffold + Docker Compose Infrastructure

**Files:**
- Create: `clipping-agent/pyproject.toml`
- Create: `clipping-agent/.env.example`
- Create: `clipping-agent/.gitignore`
- Create: `clipping-agent/docker-compose.yml`
- Create: `clipping-agent/docker-compose.infra.yml`
- Create: `clipping-agent/Makefile`

**Interfaces:**
- Consumes: (nothing — first task)
- Produces: Running infrastructure (PostgreSQL, Redis, MinIO, Qdrant, NATS, Temporal)

- [ ] **Step 1: Create root project files**

Write `clipping-agent/pyproject.toml`:
```toml
[tool.ruff]
line-length = 100
target-version = "py312"

[tool.ruff.lint]
select = ["E", "F", "I", "N", "W"]

[tool.mypy]
python_version = "3.12"
strict = true
```

Write `clipping-agent/.env.example`:
```env
# Infrastructure
POSTGRES_DSN=postgresql+asyncpg://clippy:clippy@postgres:5432/clippy
REDIS_URL=redis://redis:6379/0
NATS_SERVERS=nats://nats:4222
QDRANT_HOST=qdrant
QDRANT_PORT=6333

# Storage
STORAGE_PROVIDER=minio
MINIO_ENDPOINT=http://minio:9000
MINIO_ACCESS_KEY=clippy
MINIO_SECRET_KEY=clippy_secret
MINIO_REGION=us-east-1

# Temporal
TEMPORAL_HOST=temporal:7233
TEMPORAL_NAMESPACE=clippy-default

# LLM
LLM_PROVIDER=openai
OPENAI_API_KEY=

# App
API_PORT=8000
FRONTEND_PORT=3000
```

Write `clipping-agent/.gitignore`:
```
__pycache__/
*.pyc
.env
.venv/
node_modules/
.next/
dist/
*.egg-info/
.pytest_cache/
```

- [ ] **Step 2: Create Docker Compose infrastructure file**

Write `clipping-agent/docker-compose.infra.yml`:
```yaml
version: "3.9"

services:
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: clippy
      POSTGRES_PASSWORD: clippy
      POSTGRES_DB: clippy
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U clippy"]
      interval: 5s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 5s
      retries: 5

  minio:
    image: minio/minio:latest
    command: server /data --console-address ":9001"
    ports:
      - "9000:9000"
      - "9001:9001"
    environment:
      MINIO_ROOT_USER: clippy
      MINIO_ROOT_PASSWORD: clippy_secret
    volumes:
      - minio_data:/data
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9000/minio/health/live"]
      interval: 5s
      timeout: 5s
      retries: 5

  qdrant:
    image: qdrant/qdrant:latest
    ports:
      - "6333:6333"
    volumes:
      - qdrant_data:/qdrant/storage
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:6333/healthz"]
      interval: 5s
      timeout: 5s
      retries: 5

  nats:
    image: nats:latest
    command: -js
    ports:
      - "4222:4222"
      - "8222:8222"
    healthcheck:
      test: ["CMD", "nats", "server", "ping"]
      interval: 5s
      timeout: 5s
      retries: 5

  temporal:
    image: temporalio/auto-setup:latest
    ports:
      - "7233:7233"
      - "8233:8233"
    environment:
      DB: postgres12
      DB_PORT: 5432
      POSTGRES_USER: clippy
      POSTGRES_PASSWORD: clippy
      POSTGRES_DB: temporal
      POSTGRES_SEEDS: postgres
    depends_on:
      postgres:
        condition: service_healthy

  temporal-ui:
    image: temporalio/ui:latest
    ports:
      - "8233:8080"
    environment:
      TEMPORAL_ADDRESS: temporal:7233
    depends_on:
      - temporal

volumes:
  postgres_data:
  minio_data:
  qdrant_data:
```

- [ ] **Step 3: Create full Docker Compose file**

Write `clipping-agent/docker-compose.yml`:
```yaml
version: "3.9"

include:
  - docker-compose.infra.yml

services:
  api:
    build:
      context: .
      dockerfile: apps/api/Dockerfile
    ports:
      - "8000:8000"
    environment:
      - POSTGRES_DSN=postgresql+asyncpg://clippy:clippy@postgres:5432/clippy
      - REDIS_URL=redis://redis:6379/0
      - NATS_SERVERS=nats://nats:4222
      - STORAGE_PROVIDER=minio
      - MINIO_ENDPOINT=http://minio:9000
      - MINIO_ACCESS_KEY=clippy
      - MINIO_SECRET_KEY=clippy_secret
      - TEMPORAL_HOST=temporal:7233
      - TEMPORAL_NAMESPACE=clippy-default
    volumes:
      - ./apps/api/src:/app/src:ro
      - ./packages:/packages:ro
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
      nats:
        condition: service_healthy
      temporal:
        condition: service_started

  worker:
    build:
      context: .
      dockerfile: apps/worker/Dockerfile
    environment:
      - POSTGRES_DSN=postgresql+asyncpg://clippy:clippy@postgres:5432/clippy
      - NATS_SERVERS=nats://nats:4222
      - STORAGE_PROVIDER=minio
      - MINIO_ENDPOINT=http://minio:9000
      - MINIO_ACCESS_KEY=clippy
      - MINIO_SECRET_KEY=clippy_secret
      - TEMPORAL_HOST=temporal:7233
      - TEMPORAL_NAMESPACE=clippy-default
      - QDRANT_HOST=qdrant
      - QDRANT_PORT=6333
    volumes:
      - ./apps/worker/src:/app/src:ro
      - ./packages:/packages:ro
    depends_on:
      postgres:
        condition: service_healthy
      nats:
        condition: service_healthy
      temporal:
        condition: service_started

  frontend:
    build:
      context: .
      dockerfile: apps/frontend/Dockerfile
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=http://localhost:8000
    volumes:
      - ./apps/frontend/src:/app/src:ro
    depends_on:
      - api
```

- [ ] **Step 4: Create Makefile**

Write `clipping-agent/Makefile`:
```makefile
.PHONY: infra up down build test lint

infra:
	docker compose -f docker-compose.infra.yml up -d

up:
	docker compose up --build -d

down:
	docker compose down

build:
	docker compose build

test:
	cd apps/api && pytest
	cd apps/worker && pytest

lint:
	ruff check apps/ packages/
	mypy apps/ packages/
```

- [ ] **Step 5: Verify infrastructure starts**

Run: `docker compose -f docker-compose.infra.yml up -d`
Expected: All services start without errors.
Run: `docker compose -f docker-compose.infra.yml ps`
Expected: 7 services showing "Up" or "healthy".

- [ ] **Step 6: Commit**

```bash
git init
git add -A
git commit -m "chore: scaffold project with Docker Compose infrastructure"
```

---

### Task 2: Shared Models Package

**Files:**
- Create: `packages/shared-models/pyproject.toml`
- Create: `packages/shared-models/src/__init__.py`
- Create: `packages/shared-models/src/models/__init__.py`
- Create: `packages/shared-models/src/models/video.py`
- Create: `packages/shared-models/src/models/clip.py`
- Create: `packages/shared-models/src/models/transcript.py`
- Create: `packages/shared-models/src/models/segment.py`
- Create: `packages/shared-models/src/models/analysis.py`
- Create: `packages/shared-models/src/models/scoring.py`
- Create: `packages/shared-models/src/models/profile.py`
- Create: `packages/shared-models/src/events.py`

**Interfaces:**
- Consumes: Nothing
- Produces: All Pydantic models consumed by API, Worker, and Frontend

- [ ] **Step 1: Write pyproject.toml**

Write `packages/shared-models/pyproject.toml`:
```toml
[project]
name = "clippy-models"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "pydantic>=2.0",
    "pydantic-settings>=2.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build]
packages = ["src"]
```

- [ ] **Step 2: Write video models**

Write `packages/shared-models/src/models/video.py`:
```python
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field
from uuid import UUID, uuid4


class SourceType(str, Enum):
    YOUTUBE = "youtube"
    TWITCH = "twitch"
    PODCAST = "podcast"
    LOCAL = "local"


class VideoStatus(str, Enum):
    PENDING = "pending"
    DOWNLOADING = "downloading"
    PROCESSING = "processing"
    READY = "ready"
    FAILED = "failed"


class PipelineStepName(str, Enum):
    DOWNLOAD = "download"
    TRANSCRIBE = "transcribe"
    ANALYZE = "analyze"
    SCORE = "score"
    GENERATE = "generate"
    DONE = "done"


class Video(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    tenant_id: UUID
    title: str = ""
    source_type: SourceType
    source_url: str | None = None
    status: VideoStatus = VideoStatus.PENDING
    storage_key: str | None = None
    thumbnail_key: str | None = None
    duration_seconds: float | None = None
    file_size_bytes: int | None = None
    metadata: dict = {}
    error_message: str | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class VideoCreateResponse(BaseModel):
    id: UUID
    upload_url: str | None = None
    upload_fields: dict | None = None


class VideoConfirmRequest(BaseModel):
    storage_key: str
    source_type: SourceType
    source_url: str | None = None
    metadata: dict = {}


class VideoListResponse(BaseModel):
    videos: list[Video]
    total: int
```

- [ ] **Step 3: Write clip models**

Write `packages/shared-models/src/models/clip.py`:
```python
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field
from uuid import UUID, uuid4


class ClipCandidateStatus(str, Enum):
    PROPOSED = "proposed"
    APPROVED = "approved"
    REJECTED = "rejected"
    GENERATED = "generated"


class ScoreSet(BaseModel):
    virality: float = 0.0
    retention: float = 0.0
    hook: float = 0.0
    emotion: float = 0.0
    shareability: float = 0.0
    educational: float = 0.0


class ClipCandidate(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    video_id: UUID
    segment_ids: list[UUID] = []
    start_time: float
    end_time: float
    summary: str = ""
    scores: ScoreSet = Field(default_factory=ScoreSet)
    predicted_score: float = 0.0
    actual_score: float | None = None
    status: ClipCandidateStatus = ClipCandidateStatus.PROPOSED
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Clip(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    candidate_id: UUID
    video_id: UUID
    storage_key: str
    subtitle_key: str | None = None
    duration_seconds: float | None = None
    subtitle_style: str = "default"
    file_format: str = "mp4"
    resolution: str = "1080x1920"
    thumbnail_url: str | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
```

- [ ] **Step 4: Write transcript, segment, and analysis models**

Write `packages/shared-models/src/models/transcript.py`:
```python
from datetime import datetime
from pydantic import BaseModel, Field
from uuid import UUID, uuid4


class TranscriptSegment(BaseModel):
    start: float
    end: float
    text: str
    speaker_id: str | None = None
    confidence: float = 0.0


class Transcript(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    video_id: UUID
    language: str | None = None
    segments: list[TranscriptSegment] = []
    raw_output: dict = {}
    created_at: datetime = Field(default_factory=datetime.utcnow)
```

Write `packages/shared-models/src/models/segment.py`:
```python
from datetime import datetime
from pydantic import BaseModel, Field
from uuid import UUID, uuid4


class SceneBoundary(BaseModel):
    start: float
    end: float
    label: str = ""


class SpeakerSegment(BaseModel):
    speaker_id: str
    start: float
    end: float


class ConversationSegment(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    video_id: UUID
    start_time: float
    end_time: float
    text: str
    speaker_id: str | None = None
    segment_type: str | None = None
    context: dict = {}
    created_at: datetime = Field(default_factory=datetime.utcnow)
```

Write `packages/shared-models/src/models/analysis.py`:
```python
from datetime import datetime
from pydantic import BaseModel, Field
from uuid import UUID, uuid4


class Signal(BaseModel):
    type: str  # controversial, surprise, punchline, educational, etc.
    confidence: float
    detail: str = ""


class AnalysisResult(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    segment_id: UUID
    model: str = ""
    signals: list[Signal] = []
    embedding: list[float] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)
```

Write `packages/shared-models/src/models/scoring.py`:
```python
from pydantic import BaseModel


class ScoringWeights(BaseModel):
    virality: float = 1.0
    retention: float = 0.9
    hook: float = 0.8
    emotion: float = 0.7
    shareability: float = 0.6
    educational: float = 0.4


class LearningInsight(BaseModel):
    signal_type: str
    weight_before: float
    weight_after: float
    delta: float
    confidence: float
```

Write `packages/shared-models/src/models/profile.py`:
```python
from pydantic import BaseModel, Field
from uuid import UUID


class BrandColors(BaseModel):
    primary: str = "#3b82f6"
    secondary: str = "#1e40af"


class SubtitleStyle(BaseModel):
    font: str = "Inter"
    color: str = "#ffffff"
    position: str = "bottom"
    background_opacity: float = 0.5


class AutoEditPreferences(BaseModel):
    zoom_style: str = "static"
    background_blur: bool = False
    silence_removal: bool = True


class CreatorProfile(BaseModel):
    id: UUID
    name: str = ""
    brand_colors: BrandColors = Field(default_factory=BrandColors)
    subtitle_style: SubtitleStyle = Field(default_factory=SubtitleStyle)
    preferred_duration: int = 60
    auto_edit_preferences: AutoEditPreferences = Field(default_factory=AutoEditPreferences)
```

- [ ] **Step 5: Write event schemas**

Write `packages/shared-models/src/events.py`:
```python
from pydantic import BaseModel
from uuid import UUID
from datetime import datetime


class PipelineEvent(BaseModel):
    event_type: str  # pipeline.step_update, pipeline.completed, pipeline.failed
    video_id: UUID
    tenant_id: UUID
    step_name: str | None = None
    step_status: str | None = None
    error_message: str | None = None
    timestamp: datetime = datetime.utcnow()


class ClipEvent(BaseModel):
    event_type: str  # clip.generated, clip.approved, clip.published
    clip_id: UUID
    video_id: UUID
    tenant_id: UUID
    platform: str | None = None
    timestamp: datetime = datetime.utcnow()
```

- [ ] **Step 6: Write package `__init__.py`**

Write `packages/shared-models/src/__init__.py`:
```python
from .models.video import Video, VideoCreateResponse, VideoConfirmRequest, VideoListResponse, SourceType, VideoStatus, PipelineStepName
from .models.clip import Clip, ClipCandidate, ScoreSet, ClipCandidateStatus
from .models.transcript import Transcript, TranscriptSegment
from .models.segment import ConversationSegment, SceneBoundary, SpeakerSegment
from .models.analysis import AnalysisResult, Signal
from .models.scoring import ScoringWeights, LearningInsight
from .models.profile import CreatorProfile, BrandColors, SubtitleStyle, AutoEditPreferences
from .events import PipelineEvent, ClipEvent

__all__ = [
    "Video", "VideoCreateResponse", "VideoConfirmRequest", "VideoListResponse",
    "SourceType", "VideoStatus", "PipelineStepName",
    "Clip", "ClipCandidate", "ScoreSet", "ClipCandidateStatus",
    "Transcript", "TranscriptSegment",
    "ConversationSegment", "SceneBoundary", "SpeakerSegment",
    "AnalysisResult", "Signal",
    "ScoringWeights", "LearningInsight",
    "CreatorProfile", "BrandColors", "SubtitleStyle", "AutoEditPreferences",
    "PipelineEvent", "ClipEvent",
]
```

- [ ] **Step 7: Verify models import correctly**

Run: `cd packages/shared-models && pip install -e . && python -c "from clippy_models import Video; print(Video(tenant_id='00000000-0000-0000-0000-000000000001', source_type='youtube'))"`
Expected: No import errors, model created successfully.

- [ ] **Step 8: Commit**

```bash
git add packages/shared-models/
git commit -m "feat: add shared Pydantic models package"
```

---

### Task 3: Config + Storage + Database + Events + Logging Packages

**Files:**
- Create: `packages/config/pyproject.toml`, `packages/config/src/__init__.py`, `packages/config/src/loader.py`
- Create: `packages/storage/pyproject.toml`, `packages/storage/src/__init__.py`, `packages/storage/src/client.py`
- Create: `packages/database/pyproject.toml`, `packages/database/src/__init__.py`, `packages/database/src/engine.py`
- Create: `packages/database/src/models/base.py`, `packages/database/src/models/video.py`, `packages/database/src/models/pipeline.py`, `packages/database/src/models/transcript.py`, `packages/database/src/models/scene.py`, `packages/database/src/models/segment.py`, `packages/database/src/models/analysis.py`, `packages/database/src/models/candidate.py`, `packages/database/src/models/clip.py`, `packages/database/src/models/analytics_entry.py`, `packages/database/src/models/learning.py`
- Create: `packages/database/src/migrations/env.py`, `packages/database/src/migrations/alembic.ini`
- Create: `packages/events/pyproject.toml`, `packages/events/src/__init__.py`, `packages/events/src/nats_client.py`
- Create: `packages/logging/pyproject.toml`, `packages/logging/src/__init__.py`, `packages/logging/src/logger.py`
- Create: `packages/vectordb/pyproject.toml`, `packages/vectordb/src/__init__.py`, `packages/vectordb/src/client.py`

**Interfaces:**
- Consumes: `clippy-models` (Task 2)
- Produces: All shared infrastructure packages used by API and Worker

- [ ] **Step 1: Write config package**

Write `packages/config/pyproject.toml`:
```toml
[project]
name = "clippy-config"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "pyyaml>=6.0",
    "pydantic>=2.0",
    "pydantic-settings>=2.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

Write `packages/config/src/__init__.py`:
```python
from .loader import load_config, ClippyConfig

__all__ = ["load_config", "ClippyConfig"]
```

Write `packages/config/src/loader.py`:
```python
import os
import yaml
from pathlib import Path
from pydantic import BaseModel
from pydantic_settings import BaseSettings


class StorageConfig(BaseModel):
    provider: str = "minio"
    endpoint: str = "http://minio:9000"
    region: str = "us-east-1"
    access_key: str = "clippy"
    secret_key: str = "clippy_secret"
    buckets: dict[str, str] = {
        "raw-videos": "raw-videos",
        "clips": "clips",
        "transcripts": "transcripts",
        "thumbnails": "thumbnails",
    }


class DatabaseConfig(BaseModel):
    dsn: str = "postgresql+asyncpg://clippy:clippy@postgres:5432/clippy"
    pool_size: int = 20
    max_overflow: int = 10


class TemporalConfig(BaseModel):
    host: str = "temporal:7233"
    namespace: str = "clippy-default"
    task_queue: str = "clip-pipeline"


class NATSConfig(BaseModel):
    servers: list[str] = ["nats://nats:4222"]


class QdrantConfig(BaseModel):
    host: str = "qdrant"
    port: int = 6333
    collection: str = "clip-embeddings"


class ScoringConfig(BaseModel):
    min_clip_duration: int = 15
    max_clip_duration: int = 120
    min_score_threshold: float = 0.3
    weights: dict[str, float] = {
        "virality": 1.0,
        "retention": 0.9,
        "hook": 0.8,
        "emotion": 0.7,
        "shareability": 0.6,
        "educational": 0.4,
    }


class ClippyConfig(BaseSettings):
    storage: StorageConfig = StorageConfig()
    database: DatabaseConfig = DatabaseConfig()
    temporal: TemporalConfig = TemporalConfig()
    nats: NATSConfig = NATSConfig()
    qdrant: QdrantConfig = QdrantConfig()
    scoring: ScoringConfig = ScoringConfig()
    environment: str = "development"
    api_port: int = 8000
    frontend_port: int = 3000
    openai_api_key: str = ""

    class Config:
        env_nested_delimiter = "__"


def load_config(path: str | None = None) -> ClippyConfig:
    config = ClippyConfig()
    if path and Path(path).exists():
        with open(path) as f:
            overrides = yaml.safe_load(f)
        if overrides:
            for section, values in overrides.items():
                if hasattr(config, section):
                    for key, val in values.items():
                        if hasattr(getattr(config, section), key):
                            setattr(getattr(config, section), key, val)
    return config
```

- [ ] **Step 2: Write storage package**

Write `packages/storage/pyproject.toml`:
```toml
[project]
name = "clippy-storage"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "boto3>=1.34",
    "botocore>=1.34",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

Write `packages/storage/src/__init__.py`:
```python
from .client import StorageBackend, S3Storage, MinioStorage, create_storage

__all__ = ["StorageBackend", "S3Storage", "MinioStorage", "create_storage"]
```

Write `packages/storage/src/client.py`:
```python
import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import BinaryIO
import boto3
from botocore.config import Config


class StorageBackend(ABC):
    @abstractmethod
    async def upload(self, bucket: str, key: str, file_path: str | Path) -> str:
        ...

    @abstractmethod
    async def download(self, bucket: str, key: str, dest: str | Path) -> str:
        ...

    @abstractmethod
    async def delete(self, bucket: str, key: str) -> None:
        ...

    @abstractmethod
    async def generate_presigned_url(self, bucket: str, key: str, expires_in: int = 3600) -> str:
        ...

    @abstractmethod
    async def generate_presigned_upload_url(self, bucket: str, key: str, expires_in: int = 3600) -> dict:
        ...


class S3Storage(StorageBackend):
    def __init__(self, endpoint: str, region: str, access_key: str, secret_key: str):
        self.client = boto3.client(
            "s3",
            endpoint_url=endpoint,
            region_name=region,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            config=Config(signature_version="s3v4"),
        )

    async def upload(self, bucket: str, key: str, file_path: str | Path) -> str:
        self.client.upload_file(str(file_path), bucket, key)
        return f"{bucket}/{key}"

    async def download(self, bucket: str, key: str, dest: str | Path) -> str:
        self.client.download_file(bucket, key, str(dest))
        return str(dest)

    async def delete(self, bucket: str, key: str) -> None:
        self.client.delete_object(Bucket=bucket, Key=key)

    async def generate_presigned_url(self, bucket: str, key: str, expires_in: int = 3600) -> str:
        return self.client.generate_presigned_url(
            "get_object",
            Params={"Bucket": bucket, "Key": key},
            ExpiresIn=expires_in,
        )

    async def generate_presigned_upload_url(self, bucket: str, key: str, expires_in: int = 3600) -> dict:
        url = self.client.generate_presigned_url(
            "put_object",
            Params={"Bucket": bucket, "Key": key},
            ExpiresIn=expires_in,
        )
        return {"url": url, "fields": {}}


MinioStorage = S3Storage  # S3-compatible API, same interface


def create_storage(
    provider: str = "minio",
    endpoint: str = "http://minio:9000",
    region: str = "us-east-1",
    access_key: str = "clippy",
    secret_key: str = "clippy_secret",
) -> StorageBackend:
    return S3Storage(endpoint, region, access_key, secret_key)
```

- [ ] **Step 3: Write database models (SQLAlchemy ORM)**

Write `packages/database/pyproject.toml`:
```toml
[project]
name = "clippy-database"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "sqlalchemy[asyncio]>=2.0",
    "asyncpg>=0.29",
    "alembic>=1.13",
    "clippy-models>=0.1.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

Write `packages/database/src/__init__.py`:
```python
from .engine import create_engine, get_session, init_db

__all__ = ["create_engine", "get_session", "init_db"]
```

Write `packages/database/src/engine.py`:
```python
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
```

Write `packages/database/src/models/base.py`:
```python
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass
```

Write `packages/database/src/models/video.py`:
```python
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, BigInteger, DateTime, ForeignKey, Text, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base
from clippy_models import SourceType, VideoStatus


class VideoModel(Base):
    __tablename__ = "videos"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), default="")
    source_type: Mapped[SourceType] = mapped_column(SAEnum(SourceType), nullable=False)
    source_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[VideoStatus] = mapped_column(SAEnum(VideoStatus), default=VideoStatus.PENDING)
    storage_key: Mapped[str | None] = mapped_column(String(512), nullable=True)
    thumbnail_key: Mapped[str | None] = mapped_column(String(512), nullable=True)
    duration_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)
    file_size_bytes: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    metadata: Mapped[dict] = mapped_column(JSONB, default=dict)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    pipeline_runs = relationship("PipelineRunModel", back_populates="video")
    transcripts = relationship("TranscriptModel", back_populates="video", uselist=False)
    segments = relationship("ConversationSegmentModel", back_populates="video")
    candidates = relationship("ClipCandidateModel", back_populates="video")
    clips = relationship("ClipModel", back_populates="video")
```

Write `packages/database/src/models/pipeline.py`:
```python
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base


class PipelineRunModel(Base):
    __tablename__ = "pipeline_runs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    video_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("videos.id"), nullable=False)
    workflow_id: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    steps: Mapped[dict] = mapped_column(JSONB, default=list)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)

    video = relationship("VideoModel", back_populates="pipeline_runs")
```

Write `packages/database/src/models/transcript.py`:
```python
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base


class TranscriptModel(Base):
    __tablename__ = "transcripts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    video_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("videos.id"), unique=True, nullable=False)
    language: Mapped[str | None] = mapped_column(String(10), nullable=True)
    segments: Mapped[dict] = mapped_column(JSONB, nullable=False)  # list of TranscriptSegment
    raw_output: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    video = relationship("VideoModel", back_populates="transcripts")
```

Write remaining model files similarly (scene, segment, analysis, candidate, clip, analytics, learning).

For brevity in the plan, each follows the same pattern:
- SQLAlchemy model with UUID primary key
- JSONB for flexible data
- ForeignKey relationships
- Timestamps

- [ ] **Step 4: Write events package**

Write `packages/events/pyproject.toml`:
```toml
[project]
name = "clippy-events"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "nats-py>=2.0",
    "clippy-models>=0.1.0",
]
```

Write `packages/events/src/nats_client.py`:
```python
import json
import nats
from typing import Callable, Awaitable
from clippy_models import PipelineEvent


class NATSClient:
    def __init__(self, servers: list[str]):
        self.servers = servers
        self._conn = None

    async def connect(self):
        self._conn = await nats.connect(servers=self.servers)

    async def close(self):
        if self._conn:
            await self._conn.close()

    async def publish(self, subject: str, data: dict):
        if not self._conn:
            raise RuntimeError("NATS not connected")
        await self._conn.publish(subject, json.dumps(data).encode())

    async def subscribe(self, subject: str, callback: Callable[[dict], Awaitable[None]]):
        if not self._conn:
            raise RuntimeError("NATS not connected")

        async def handler(msg):
            data = json.loads(msg.data.decode())
            await callback(data)

        await self._conn.subscribe(subject, cb=handler)

    async def publish_pipeline_event(self, event: PipelineEvent):
        await self.publish(f"pipeline.{event.event_type}", event.model_dump())
```

- [ ] **Step 5: Write logging package**

Write `packages/logging/pyproject.toml`:
```toml
[project]
name = "clippy-logging"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "structlog>=24.0",
]
```

Write `packages/logging/src/logger.py`:
```python
import structlog
import logging


def setup_logging(environment: str = "development"):
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.dev.ConsoleRenderer() if environment == "development"
            else structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    logging.basicConfig(format="%(message)s", level=logging.INFO)


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    return structlog.get_logger(name)
```

- [ ] **Step 6: Write vectordb package**

Write `packages/vectordb/pyproject.toml`:
```toml
[project]
name = "clippy-vectordb"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "qdrant-client>=1.9",
]
```

Write `packages/vectordb/src/client.py`:
```python
from qdrant_client import QdrantClient
from qdrant_client.http import models


class VectorDB:
    def __init__(self, host: str, port: int, collection: str, vector_size: int = 1536):
        self.client = QdrantClient(host=host, port=port)
        self.collection = collection
        self.vector_size = vector_size

    async def ensure_collection(self):
        collections = self.client.get_collections().collections
        names = [c.name for c in collections]
        if self.collection not in names:
            self.client.create_collection(
                collection_name=self.collection,
                vectors_config=models.VectorParams(
                    size=self.vector_size,
                    distance=models.Distance.COSINE,
                ),
            )

    async def upsert(self, point_id: str, vector: list[float], payload: dict | None = None):
        self.client.upsert(
            collection_name=self.collection,
            points=[models.PointStruct(id=point_id, vector=vector, payload=payload or {})],
        )

    async def search(self, vector: list[float], limit: int = 10) -> list[models.ScoredPoint]:
        return self.client.search(
            collection_name=self.collection,
            query_vector=vector,
            limit=limit,
        )
```

- [ ] **Step 7: Install all packages and verify imports**

Run:
```powershell
cd packages/config; pip install -e .; cd ../..
cd packages/storage; pip install -e .; cd ../..
cd packages/database; pip install -e .; cd ../..
cd packages/events; pip install -e .; cd ../..
cd packages/logging; pip install -e .; cd ../..
cd packages/vectordb; pip install -e .; cd ../..
python -c "from clippy_config import ClippyConfig; c=ClippyConfig(); print(c.environment)"
python -c "from clippy_storage import create_storage; s=create_storage(); print(type(s).__name__)"
python -c "from clippy_logging import setup_logging; setup_logging(); print('ok')"
```

- [ ] **Step 8: Commit**

```bash
git add packages/config/ packages/storage/ packages/database/ packages/events/ packages/logging/ packages/vectordb/
git commit -m "feat: add shared infrastructure packages"
```

---

### Task 4: API Service — FastAPI Application

**Files:**
- Create: `apps/api/pyproject.toml`
- Create: `apps/api/Dockerfile`
- Create: `apps/api/src/__init__.py`
- Create: `apps/api/src/main.py`
- Create: `apps/api/src/config.py`
- Create: `apps/api/src/routers/__init__.py`
- Create: `apps/api/src/routers/videos.py`
- Create: `apps/api/src/routers/candidates.py`
- Create: `apps/api/src/routers/clips.py`
- Create: `apps/api/src/routers/analytics.py`
- Create: `apps/api/src/dependencies/__init__.py`
- Create: `apps/api/src/dependencies/db.py`
- Create: `apps/api/src/middleware/tenant.py`

**Interfaces:**
- Consumes: `clippy-models`, `clippy-config`, `clippy-storage`, `clippy-database`, `clippy-events`, `clippy-logging`
- Produces: Running FastAPI server at :8000

- [ ] **Step 1: Write pyproject.toml and Dockerfile**

Write `apps/api/pyproject.toml`:
```toml
[project]
name = "clippy-api"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "fastapi>=0.110",
    "uvicorn[standard]>=0.28",
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

Write `apps/api/Dockerfile`:
```dockerfile
FROM python:3.12-slim

WORKDIR /app
COPY apps/api/pyproject.toml .
RUN pip install --no-cache-dir .

COPY packages/ /packages
RUN pip install --no-cache-dir /packages/*/

COPY apps/api/src/ ./src/

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

- [ ] **Step 2: Write FastAPI application entrypoint**

Write `apps/api/src/main.py`:
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

- [ ] **Step 3: Write middleware**

Write `apps/api/src/middleware/tenant.py`:
```python
from uuid import UUID
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request


TENANT_ID = UUID("00000000-0000-0000-0000-000000000001")  # Dev tenant


class TenantMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # In production, extract from JWT; for dev use hardcoded tenant
        request.state.tenant_id = TENANT_ID
        response = await call_next(request)
        return response
```

- [ ] **Step 4: Write dependencies**

Write `apps/api/src/dependencies/db.py`:
```python
from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession


async def get_db(request: Request) -> AsyncSession:
    session_factory = request.app.state.db_session
    async with session_factory() as session:
        yield session
```

- [ ] **Step 5: Write video router**

Write `apps/api/src/routers/videos.py`:
```python
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from clippy_models import (
    Video, VideoCreateResponse, VideoConfirmRequest, VideoListResponse,
    SourceType, VideoStatus, PipelineStep, PipelineStepName,
)
from clippy_database.models.video import VideoModel
from clippy_database.models.pipeline import PipelineRunModel
from ..dependencies.db import get_db

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
    from datetime import datetime

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

    # TODO: Start Temporal workflow (see Task 5 Worker service)

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

- [ ] **Step 6: Write candidate, clip, and analytics stubs**

Write `apps/api/src/routers/candidates.py`:
```python
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from clippy_models import ClipCandidate, Clip
from clippy_database.models.candidate import ClipCandidateModel
from clippy_database.models.clip import ClipModel
from ..dependencies.db import get_db

router = APIRouter()


@router.get("/video/{video_id}", response_model=dict)
async def get_candidates(video_id: UUID, request: Request, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(ClipCandidateModel).where(
            ClipCandidateModel.video_id == video_id,
            ClipCandidateModel.tenant_id == request.state.tenant_id,
        ).order_by(ClipCandidateModel.predicted_score.desc())
    )
    candidates = result.scalars().all()
    return {"candidates": [c.to_pydantic() for c in candidates]}


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

    # TODO: Generate clip via Temporal
    clip = Clip(
        candidate_id=candidate_id,
        video_id=candidate.video_id,
        storage_key=f"clips/{candidate_id}.mp4",
    )
    return {"clip": clip}


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

Write `apps/api/src/routers/clips.py` and `apps/api/src/routers/analytics.py` with similar CRUD patterns.

- [ ] **Step 7: Verify API starts**

Run: `cd apps/api && pip install -e . && python -c "from src.main import app; print('API imports OK')"`
Then start with infra running: `docker compose -f docker-compose.infra.yml up -d` then `uvicorn apps.api.src.main:app --host 0.0.0.0 --port 8000` (or use Docker Compose full stack).

Verify: `curl http://localhost:8000/docs` returns Swagger UI.

- [ ] **Step 8: Commit**

```bash
git add apps/api/
git commit -m "feat: add FastAPI service with video, candidate, clip, analytics endpoints"
```

---

### Task 5: Worker Service — Temporal Workflow + Activities

**Files:**
- Create: `apps/worker/pyproject.toml`
- Create: `apps/worker/Dockerfile`
- Create: `apps/worker/src/__init__.py`
- Create: `apps/worker/src/main.py`
- Create: `apps/worker/src/config.py`
- Create: `apps/worker/src/workflows/__init__.py`
- Create: `apps/worker/src/workflows/clip_pipeline.py`
- Create: `apps/worker/src/workflows/analytics.py`
- Create: `apps/worker/src/activities/__init__.py`
- Create: `apps/worker/src/activities/download.py`
- Create: `apps/worker/src/activities/transcribe.py`
- Create: `apps/worker/src/activities/scene_detect.py`
- Create: `apps/worker/src/activities/speaker_detect.py`
- Create: `apps/worker/src/activities/segment.py`
- Create: `apps/worker/src/activities/llm_analyze.py`
- Create: `apps/worker/src/activities/score.py`
- Create: `apps/worker/src/activities/generate_clip.py`
- Create: `apps/worker/src/activities/generate_subtitle.py`

**Interfaces:**
- Consumes: All shared packages + Temporal Server + NATS + MinIO
- Produces: Running Temporal worker that processes video pipelines

- [ ] **Step 1: Write pyproject.toml and Dockerfile**

Write `apps/worker/pyproject.toml`:
```toml
[project]
name = "clippy-worker"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "temporalio>=1.7",
    "openai>=1.0",
    "clippy-models>=0.1.0",
    "clippy-config>=0.1.0",
    "clippy-storage>=0.1.0",
    "clippy-database>=0.1.0",
    "clippy-events>=0.1.0",
    "clippy-logging>=0.1.0",
    "clippy-vectordb>=0.1.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

Write `apps/worker/Dockerfile`:
```dockerfile
FROM python:3.12-slim

RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY apps/worker/pyproject.toml .
RUN pip install --no-cache-dir .

COPY packages/ /packages
RUN pip install --no-cache-dir /packages/*/

COPY apps/worker/src/ ./src/

CMD ["python", "-m", "src.main"]
```

- [ ] **Step 2: Write worker entrypoint**

Write `apps/worker/src/main.py`:
```python
import asyncio
from temporalio.client import Client
from temporalio.worker import Worker
from clippy_config import ClippyConfig
from clippy_logging import setup_logging, get_logger
from clippy_database import create_engine, get_session
from clippy_storage import create_storage
from clippy_events import NATSClient
from clippy_vectordb import VectorDB

from .workflows.clip_pipeline import ClipPipelineWorkflow
from .activities.download import DownloadActivity
from .activities.transcribe import TranscribeActivity
from .activities.scene_detect import SceneDetectActivity
from .activities.speaker_detect import SpeakerDetectActivity
from .activities.segment import SegmentActivity
from .activities.llm_analyze import LLMAnalyzeActivity
from .activities.score import ScoreActivity
from .activities.generate_clip import GenerateClipActivity
from .activities.generate_subtitle import GenerateSubtitleActivity


async def main():
    config = ClippyConfig()
    setup_logging(config.environment)
    logger = get_logger("clippy-worker")

    engine = create_engine(config.database.dsn)
    db_session = get_session(engine)

    storage = create_storage(
        provider=config.storage.provider,
        endpoint=config.storage.endpoint,
        access_key=config.storage.access_key,
        secret_key=config.storage.secret_key,
    )

    nats = NATSClient(config.nats.servers)
    await nats.connect()

    vectordb = VectorDB(config.qdrant.host, config.qdrant.port, config.qdrant.collection)
    await vectordb.ensure_collection()

    client = await Client.connect(config.temporal.host, namespace=config.temporal.namespace)

    activities = [
        DownloadActivity(storage, nats, config),
        TranscribeActivity(storage, nats, config),
        SceneDetectActivity(storage, nats, config),
        SpeakerDetectActivity(storage, nats, config),
        SegmentActivity(storage, nats, config),
        LLMAnalyzeActivity(storage, nats, config),
        ScoreActivity(storage, nats, config, vectordb),
        GenerateClipActivity(storage, nats, config),
        GenerateSubtitleActivity(storage, nats, config),
    ]

    worker = Worker(
        client=client,
        task_queue=config.temporal.task_queue,
        workflows=[ClipPipelineWorkflow],
        activities=[a.execute for a in activities],
    )

    logger.info("worker_started", task_queue=config.temporal.task_queue)
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
```

- [ ] **Step 3: Write Temporal workflow definition**

Write `apps/worker/src/workflows/clip_pipeline.py`:
```python
from datetime import timedelta
from temporalio import workflow
from temporalio.common import RetryPolicy

with workflow.unsafe.imports_passed_through():
    from uuid import UUID


@workflow.defn
class ClipPipelineWorkflow:
    @workflow.run
    async def run(self, video_id: UUID, tenant_id: UUID) -> dict:
        retry_policy = RetryPolicy(maximum_attempts=3)

        # Step 1: Download
        workflow.logger.info(f"Starting pipeline for video {video_id}")
        download_result = await workflow.execute_activity(
            "download_video",
            video_id,
            start_to_close_timeout=timedelta(hours=2),
            retry_policy=retry_policy,
        )

        # Step 2-4: Transcribe, Scene Detect, Speaker Detect (sequential for simplicity)
        transcript = await workflow.execute_activity(
            "transcribe_audio",
            video_id,
            start_to_close_timeout=timedelta(hours=2),
            retry_policy=retry_policy,
        )

        scenes = await workflow.execute_activity(
            "detect_scenes",
            video_id,
            start_to_close_timeout=timedelta(minutes=30),
            retry_policy=retry_policy,
        )

        speakers = await workflow.execute_activity(
            "detect_speakers",
            video_id,
            start_to_close_timeout=timedelta(minutes=30),
            retry_policy=retry_policy,
        )

        # Step 5: Segment
        segments = await workflow.execute_activity(
            "segment_conversation",
            video_id,
            start_to_close_timeout=timedelta(minutes=10),
            retry_policy=retry_policy,
        )

        # Step 6: LLM Analyze
        analysis = await workflow.execute_activity(
            "llm_analyze",
            video_id,
            start_to_close_timeout=timedelta(minutes=30),
            retry_policy=retry_policy,
        )

        # Step 7: Score
        candidates = await workflow.execute_activity(
            "score_segments",
            video_id,
            start_to_close_timeout=timedelta(minutes=10),
            retry_policy=retry_policy,
        )

        return {"video_id": str(video_id), "candidates": candidates}
```

- [ ] **Step 4: Write activities (stubs with real implementations)**

Each activity follows this pattern:

```python
from temporalio import activity
from clippy_config import ClippyConfig
from clippy_storage import StorageBackend
from clippy_events import NATSClient


class DownloadActivity:
    def __init__(self, storage: StorageBackend, nats: NATSClient, config: ClippyConfig):
        self.storage = storage
        self.nats = nats
        self.config = config

    @activity.defn(name="download_video")
    async def execute(self, video_id: str) -> dict:
        activity.logger.info(f"Downloading video {video_id}")
        # TODO: implement actual download logic
        return {"video_id": video_id, "status": "downloaded"}
```

Activity implementations for v0.1:
- **download**: For YouTube URLs, use `yt-dlp`. For local uploads, already in MinIO.
- **transcribe**: Use `whisper.cpp` or `faster-whisper` via subprocess.
- **scene_detect**: Use `scenedetect` library via subprocess.
- **speaker_detect**: Use `pyannote.audio` for diarization.
- **segment**: Merge transcript + scenes + speakers into coherent segments.
- **llm_analyze**: Call OpenAI API with structured prompt to detect virality signals.
- **score**: Weighted scoring + Qdrant similarity boost.
- **generate_clip**: `ffmpeg` cut based on start/end times.
- **generate_subtitle**: Use `ffmpeg` to burn subtitles or generate .srt files.

- [ ] **Step 5: Verify worker imports**

Run: `cd apps/worker && pip install -e . && python -c "from src.main import main; print('Worker imports OK')"`

- [ ] **Step 6: Commit**

```bash
git add apps/worker/
git commit -m "feat: add Temporal worker with pipeline workflow and activity stubs"
```

---

### Task 6: Frontend — Next.js Application Shell

**Files:**
- Create: `apps/frontend/package.json`
- Create: `apps/frontend/tsconfig.json`
- Create: `apps/frontend/next.config.ts`
- Create: `apps/frontend/tailwind.config.ts`
- Create: `apps/frontend/postcss.config.js`
- Create: `apps/frontend/Dockerfile`
- Create: `apps/frontend/src/app/layout.tsx`
- Create: `apps/frontend/src/app/page.tsx`
- Create: `apps/frontend/src/app/globals.css`
- Create: `apps/frontend/src/providers/query-provider.tsx`
- Create: `apps/frontend/src/lib/api-types.ts`
- Create: `apps/frontend/src/lib/api.ts`
- Create: `apps/frontend/src/lib/websocket.ts`
- Create: `apps/frontend/src/components/ui/button.tsx`
- Create: `apps/frontend/src/components/ui/card.tsx`
- Create: `apps/frontend/src/components/ui/badge.tsx`
- Create: `apps/frontend/src/components/layout/sidebar.tsx`
- Create: `apps/frontend/src/app/(dashboard)/layout.tsx`
- Create: `apps/frontend/src/app/(dashboard)/page.tsx`

**Interfaces:**
- Consumes: FastAPI backend (Task 4)
- Produces: Running Next.js app at :3000

- [ ] **Step 1: Scaffold Next.js project**

Run:
```powershell
cd apps/frontend
npm init -y
npm install next@14 react react-dom @tanstack/react-query recharts
npm install -D typescript @types/react @types/node tailwindcss postcss autoprefixer
npx tailwindcss init -p
```

Write `apps/frontend/package.json`:
```json
{
  "name": "clippy-frontend",
  "version": "0.1.0",
  "private": true,
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "lint": "next lint"
  },
  "dependencies": {
    "next": "^14.0.0",
    "react": "^18.0.0",
    "react-dom": "^18.0.0",
    "@tanstack/react-query": "^5.0.0",
    "recharts": "^2.0.0"
  },
  "devDependencies": {
    "typescript": "^5.0.0",
    "@types/react": "^18.0.0",
    "@types/node": "^20.0.0",
    "tailwindcss": "^3.0.0",
    "postcss": "^8.0.0",
    "autoprefixer": "^10.0.0"
  }
}
```

- [ ] **Step 2: Write config files**

Write `apps/frontend/tsconfig.json`:
```json
{
  "compilerOptions": {
    "target": "ES2017",
    "lib": ["dom", "dom.iterable", "esnext"],
    "allowJs": true,
    "skipLibCheck": true,
    "strict": true,
    "noEmit": true,
    "esModuleInterop": true,
    "module": "esnext",
    "moduleResolution": "bundler",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "jsx": "preserve",
    "incremental": true,
    "plugins": [{ "name": "next" }],
    "paths": {
      "@/*": ["./src/*"]
    }
  },
  "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx", ".next/types/**/*.ts"],
  "exclude": ["node_modules"]
}
```

Write `apps/frontend/next.config.ts`:
```typescript
import type { NextConfig } from 'next'

const nextConfig: NextConfig = {
  output: 'standalone',
  images: {
    remotePatterns: [
      { protocol: 'http', hostname: 'localhost', port: '9000' },
      { protocol: 'https', hostname: '**.amazonaws.com' },
    ],
  },
}

export default nextConfig
```

- [ ] **Step 3: Write global styles and root layout**

Write `apps/frontend/src/app/globals.css`:
```css
@tailwind base;
@tailwind components;
@tailwind utilities;

:root {
  --surface-0: #0a0a0a;
  --surface-1: #141414;
  --surface-2: #1c1c1c;
  --surface-3: #252525;
  --border: #2a2a2a;
  --text-primary: #f5f5f5;
  --text-secondary: #a0a0a0;
  --text-tertiary: #6b6b6b;
  --accent: #3b82f6;
  --accent-hover: #2563eb;
  --success: #22c55e;
  --warning: #eab308;
  --danger: #ef4444;
}

body {
  margin: 0;
  padding: 0;
  background-color: var(--surface-0);
  color: var(--text-primary);
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
}
```

Write `apps/frontend/src/app/layout.tsx`:
```tsx
import type { Metadata } from 'next'
import './globals.css'
import { QueryProvider } from '@/providers/query-provider'

export const metadata: Metadata = {
  title: 'Clippy - AI Clipping Agent',
  description: 'Automatically detect and generate viral clips from your videos',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <QueryProvider>{children}</QueryProvider>
      </body>
    </html>
  )
}
```

Write `apps/frontend/src/providers/query-provider.tsx`:
```tsx
'use client'

import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useState } from 'react'

export function QueryProvider({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(
    () => new QueryClient({
      defaultOptions: {
        queries: {
          staleTime: 30 * 1000,
          retry: 2,
        },
      },
    })
  )

  return (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  )
}
```

- [ ] **Step 4: Write API client**

Write `apps/frontend/src/lib/api-types.ts`:
```typescript
export interface Video {
  id: string
  tenant_id: string
  title: string
  source_type: 'youtube' | 'twitch' | 'podcast' | 'local'
  source_url?: string
  status: 'pending' | 'downloading' | 'processing' | 'ready' | 'failed'
  duration_seconds?: number
  file_size_bytes?: number
  thumbnail_url?: string
  metadata: Record<string, unknown>
  error_message?: string
  created_at: string
  updated_at: string
}

export interface PipelineStep {
  name: string
  label: string
  status: 'pending' | 'active' | 'completed' | 'failed'
  started_at?: string
  completed_at?: string
  error_message?: string
}

export interface ScoreSet {
  virality: number
  retention: number
  hook: number
  emotion: number
  shareability: number
  educational: number
}

export interface ClipCandidate {
  id: string
  video_id: string
  start_time: number
  end_time: number
  duration_seconds: number
  summary: string
  scores: ScoreSet
  predicted_score: number
  status: 'proposed' | 'approved' | 'rejected' | 'generated'
  created_at: string
}

export interface Clip {
  id: string
  candidate_id: string
  video_id: string
  title: string
  duration_seconds?: number
  download_url: string
  thumbnail_url?: string
  created_at: string
}

export interface AnalyticsOverview {
  total_clips: number
  total_views: number
  total_likes: number
  total_shares: number
  average_completion_rate: number
}

export interface CreatorProfile {
  id: string
  name: string
  brand_colors: { primary: string; secondary: string }
  subtitle_style: { font: string; color: string; position: string; background_opacity: number }
  preferred_duration: number
}
```

Write `apps/frontend/src/lib/api.ts`:
```typescript
export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message)
    this.name = 'ApiError'
  }
}

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

async function request<T>(method: string, path: string, body?: unknown): Promise<T> {
  const headers: Record<string, string> = {}
  if (body) {
    headers['Content-Type'] = 'application/json'
  }

  const res = await fetch(`${BASE_URL}${path}`, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  })

  if (!res.ok) {
    throw new ApiError(res.status, await res.text())
  }

  return res.json()
}

export const api = {
  get: <T>(path: string) => request<T>('GET', path),
  post: <T>(path: string, body?: unknown) => request<T>('POST', path, body),
  patch: <T>(path: string, body: unknown) => request<T>('PATCH', path, body),
  delete: <T>(path: string) => request<T>('DELETE', path),
}
```

- [ ] **Step 5: Write sidebar and dashboard layout**

Write `apps/frontend/src/components/layout/sidebar.tsx`:
```tsx
'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'

const navItems = [
  { href: '/dashboard/videos', label: 'Videos', icon: '🎬' },
  { href: '/dashboard/clips', label: 'Clips', icon: '✂️' },
  { href: '/dashboard/analytics', label: 'Analytics', icon: '📊' },
  { href: '/dashboard/settings', label: 'Settings', icon: '⚙️' },
]

export function Sidebar() {
  const pathname = usePathname()

  return (
    <aside className="w-60 h-screen fixed left-0 top-0 bg-[#0a0a0a] border-r border-[#2a2a2a] flex flex-col">
      <div className="h-16 flex items-center justify-center border-b border-[#2a2a2a]">
        <span className="text-xl font-bold text-[#3b82f6]">Clippy</span>
      </div>
      <nav className="flex-1 p-4 space-y-1">
        {navItems.map((item) => {
          const isActive = pathname.startsWith(item.href)
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center gap-3 px-3 py-2.5 rounded-md text-sm transition-colors ${
                isActive
                  ? 'bg-[#1c1c1c] text-[#3b82f6]'
                  : 'text-[#a0a0a0] hover:bg-[#141414] hover:text-[#f5f5f5]'
              }`}
            >
              <span>{item.icon}</span>
              <span>{item.label}</span>
            </Link>
          )
        })}
      </nav>
      <div className="p-4 border-t border-[#2a2a2a]">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-full bg-[#252525] flex items-center justify-center text-sm">
            C
          </div>
          <span className="text-sm text-[#a0a0a0]">Creator</span>
        </div>
      </div>
    </aside>
  )
}
```

Write `apps/frontend/src/app/(dashboard)/layout.tsx`:
```tsx
import { Sidebar } from '@/components/layout/sidebar'

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-[#0a0a0a]">
      <Sidebar />
      <main className="ml-60 p-8">{children}</main>
    </div>
  )
}
```

Write `apps/frontend/src/app/(dashboard)/page.tsx` — redirects to /dashboard/videos.

- [ ] **Step 6: Verify frontend builds**

Run:
```powershell
cd apps/frontend
npm install
npm run build
```
Expected: Build succeeds, no TypeScript errors.

- [ ] **Step 7: Commit**

```bash
git add apps/frontend/
git commit -m "feat: add Next.js frontend shell with sidebar, routing, API client"
```

---

### Task 7: Frontend Pages — Upload + Videos + Pipeline

**Files:**
- Create: `apps/frontend/src/app/(dashboard)/upload/page.tsx`
- Create: `apps/frontend/src/app/(dashboard)/videos/page.tsx`
- Create: `apps/frontend/src/app/(dashboard)/videos/[id]/page.tsx`
- Create: `apps/frontend/src/components/upload/upload-zone.tsx`
- Create: `apps/frontend/src/components/upload/url-input.tsx`
- Create: `apps/frontend/src/components/pipeline/pipeline-stepper.tsx`
- Create: `apps/frontend/src/components/candidates/candidate-card.tsx`
- Create: `apps/frontend/src/components/candidates/candidate-grid.tsx`
- Create: `apps/frontend/src/components/candidates/score-badge.tsx`
- Create: `apps/frontend/src/hooks/use-pipeline.ts`
- Create: `apps/frontend/src/hooks/use-candidates.ts`

**Interfaces:**
- Consumes: API client (Task 6)
- Produces: Core user workflow pages

- [ ] **Step 1: Write Upload page**

Write `apps/frontend/src/components/upload/upload-zone.tsx`:
```tsx
'use client'

import { useState, useCallback } from 'react'

interface UploadZoneProps {
  onFileSelected: (file: File) => void
  onUrlSubmit: (url: string) => void
}

export function UploadZone({ onFileSelected, onUrlSubmit }: UploadZoneProps) {
  const [isDragging, setIsDragging] = useState(false)
  const [url, setUrl] = useState('')

  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(e.type === 'dragenter' || e.type === 'dragover')
  }, [])

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
    const file = e.dataTransfer.files[0]
    if (file) onFileSelected(file)
  }, [onFileSelected])

  return (
    <div className="space-y-6">
      <div
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        className={`border-2 border-dashed rounded-xl p-12 text-center transition-colors cursor-pointer ${
          isDragging ? 'border-[#3b82f6] bg-blue-500/5' : 'border-[#3a3a3a] hover:border-[#5a5a5a]'
        }`}
      >
        <div className="text-2xl mb-4">📁</div>
        <p className="text-[#f5f5f5] font-medium mb-1">
          Drop video here or click to browse
        </p>
        <p className="text-sm text-[#6b6b6b]">MP4, MOV, AVI up to 4GB</p>
      </div>

      <div className="relative">
        <div className="absolute inset-0 flex items-center">
          <div className="w-full border-t border-[#2a2a2a]" />
        </div>
        <div className="relative flex justify-center">
          <span className="px-4 text-sm text-[#6b6b6b] bg-[#0a0a0a]">or paste a URL</span>
        </div>
      </div>

      <div className="flex gap-3">
        <input
          type="url"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          placeholder="https://youtube.com/watch?v=..."
          className="flex-1 h-10 px-3 rounded-md bg-[#1c1c1c] border border-[#2a2a2a] text-sm text-[#f5f5f5] placeholder:text-[#6b6b6b] focus:outline-none focus:border-[#3b82f6]"
        />
        <button
          onClick={() => url && onUrlSubmit(url)}
          disabled={!url}
          className="h-10 px-6 rounded-md bg-[#3b82f6] text-white text-sm font-medium disabled:opacity-50 hover:bg-[#2563eb]"
        >
          Import
        </button>
      </div>
    </div>
  )
}
```

- [ ] **Step 2: Write pipeline stepper component**

Write `apps/frontend/src/components/pipeline/pipeline-stepper.tsx`:
```tsx
'use client'

const STEPS = [
  { name: 'download', label: 'Download' },
  { name: 'transcribe', label: 'Transcribe' },
  { name: 'analyze', label: 'Analyze' },
  { name: 'score', label: 'Score' },
  { name: 'generate', label: 'Generate' },
  { name: 'done', label: 'Done' },
]

interface PipelineStep {
  name: string
  status: 'pending' | 'active' | 'completed' | 'failed'
}

interface PipelineStepperProps {
  steps: PipelineStep[]
}

export function PipelineStepper({ steps }: PipelineStepperProps) {
  const stepMap = new Map(steps.map((s) => [s.name, s]))

  return (
    <div className="flex items-center gap-0">
      {STEPS.map((step, i) => {
        const status = stepMap.get(step.name)?.status || 'pending'
        const isLast = i === STEPS.length - 1

        return (
          <div key={step.name} className="flex items-center">
            <div className="flex items-center gap-2">
              <div
                className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-medium transition-colors ${
                  status === 'completed' ? 'bg-[#22c55e] text-white' :
                  status === 'active' ? 'bg-[#3b82f6] text-white animate-pulse' :
                  status === 'failed' ? 'bg-[#ef4444] text-white' :
                  'bg-[#252525] text-[#6b6b6b]'
                }`}
              >
                {status === 'completed' ? '✓' :
                 status === 'failed' ? '✗' : i + 1}
              </div>
              <span
                className={`text-xs ${
                  status === 'completed' ? 'text-[#22c55e]' :
                  status === 'active' ? 'text-[#3b82f6]' :
                  status === 'failed' ? 'text-[#ef4444]' :
                  'text-[#6b6b6b]'
                }`}
              >
                {step.label}
              </span>
            </div>
            {!isLast && (
              <div
                className={`w-8 h-0.5 mx-2 ${
                  status === 'completed' ? 'bg-[#22c55e]' : 'bg-[#2a2a2a]'
                }`}
              />
            )}
          </div>
        )
      })}
    </div>
  )
}
```

- [ ] **Step 3: Write candidate card and score badge**

Write `apps/frontend/src/components/candidates/score-badge.tsx`:
```tsx
interface ScoreBadgeProps {
  label: string
  value: number
}

export function ScoreBadge({ label, value }: ScoreBadgeProps) {
  const color =
    value >= 85 ? '#22c55e' :
    value >= 70 ? '#eab308' :
    '#ef4444'

  return (
    <span
      className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-semibold"
      style={{ backgroundColor: `${color}15`, color }}
    >
      {Math.round(value)}
      <span className="opacity-70 font-normal">{label}</span>
    </span>
  )
}
```

Write `apps/frontend/src/components/candidates/candidate-card.tsx`:
```tsx
'use client'

import type { ClipCandidate } from '@/lib/api-types'
import { ScoreBadge } from './score-badge'

interface CandidateCardProps {
  candidate: ClipCandidate
  onApprove: (id: string) => void
  onReject: (id: string) => void
  onPreview: (id: string) => void
}

export function CandidateCard({ candidate, onApprove, onReject, onPreview }: CandidateCardProps) {
  const topScores = Object.entries(candidate.scores)
    .sort(([, a], [, b]) => b - a)
    .slice(0, 3)

  return (
    <div className="rounded-lg bg-[#141414] border border-[#2a2a2a] overflow-hidden hover:shadow-lg hover:-translate-y-0.5 transition-all">
      <div
        className="relative aspect-video bg-[#1c1c1c] cursor-pointer"
        onClick={() => onPreview(candidate.id)}
      >
        {candidate.thumbnail_url && (
          <img
            src={candidate.thumbnail_url}
            alt={candidate.summary}
            className="w-full h-full object-cover"
          />
        )}
        <span className="absolute top-2 left-2 px-2 py-0.5 rounded bg-black/70 text-xs text-white">
          {Math.round(candidate.duration_seconds)}s
        </span>
      </div>

      <div className="p-3 space-y-2">
        <p className="text-sm text-[#f5f5f5] line-clamp-1">{candidate.summary}</p>

        <div className="flex flex-wrap gap-1">
          {topScores.map(([key, value]) => (
            <ScoreBadge key={key} label={key} value={value} />
          ))}
        </div>

        <div className="flex gap-2 pt-2 border-t border-[#2a2a2a]">
          <button
            onClick={() => onApprove(candidate.id)}
            className="flex-1 h-9 rounded-md bg-[#22c55e]/10 text-[#22c55e] text-sm font-medium hover:bg-[#22c55e]/20 transition-colors"
          >
            Approve
          </button>
          <button
            onClick={() => onReject(candidate.id)}
            className="flex-1 h-9 rounded-md border border-[#ef4444]/30 text-[#ef4444] text-sm font-medium hover:bg-[#ef4444]/10 transition-colors"
          >
            Reject
          </button>
        </div>
      </div>
    </div>
  )
}
```

- [ ] **Step 4: Write video detail page (pipeline + candidates)**

Write `apps/frontend/src/hooks/use-pipeline.ts`:
```typescript
'use client'

import { useEffect, useState, useCallback } from 'react'

interface PipelineEvent {
  type: 'pipeline.step_update' | 'pipeline.completed' | 'pipeline.failed'
  video_id: string
  step_name?: string
  step_status?: string
  error?: string
}

export function usePipeline(videoId: string | undefined) {
  const [steps, setSteps] = useState<Record<string, string>>({})
  const [status, setStatus] = useState<'connected' | 'disconnected' | 'reconnecting'>('disconnected')
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!videoId) return

    let ws: WebSocket
    let reconnectTimeout: NodeJS.Timeout
    let attempt = 0

    function connect() {
      setStatus('reconnecting')
      ws = new WebSocket(`ws://localhost:8000/ws/videos/${videoId}`)

      ws.onopen = () => {
        setStatus('connected')
        attempt = 0
      }

      ws.onmessage = (event) => {
        const data: PipelineEvent = JSON.parse(event.data)
        if (data.type === 'pipeline.step_update' && data.step_name && data.step_status) {
          setSteps((prev) => ({ ...prev, [data.step_name!]: data.step_status! }))
        } else if (data.type === 'pipeline.failed' && data.error) {
          setError(data.error)
        }
      }

      ws.onclose = () => {
        setStatus('disconnected')
        const delay = Math.min(1000 * Math.pow(2, attempt), 30000)
        attempt++
        reconnectTimeout = setTimeout(connect, delay)
      }

      ws.onerror = () => ws.close()
    }

    connect()

    return () => {
      clearTimeout(reconnectTimeout)
      ws?.close()
    }
  }, [videoId])

  return { steps, status, error }
}
```

Write `apps/frontend/src/app/(dashboard)/videos/[id]/page.tsx`:
```tsx
'use client'

import { useParams } from 'next/navigation'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '@/lib/api'
import { PipelineStepper } from '@/components/pipeline/pipeline-stepper'
import { CandidateCard } from '@/components/candidates/candidate-card'
import { usePipeline } from '@/hooks/use-pipeline'

export default function VideoDetailPage() {
  const { id } = useParams<{ id: string }>()
  const queryClient = useQueryClient()

  const { data, isLoading } = useQuery({
    queryKey: ['video', id],
    queryFn: () => api.get<{ video: any; pipeline: any[] }>(`/videos/${id}`),
  })

  const { data: candidatesData } = useQuery({
    queryKey: ['candidates', id],
    queryFn: () => api.get<{ candidates: any[] }>(`/candidates/video/${id}`),
    enabled: data?.video.status === 'ready',
  })

  const pipelineSteps = usePipeline(id)

  const approveMutation = useMutation({
    mutationFn: (candidateId: string) => api.post(`/candidates/${candidateId}/approve`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['candidates', id] }),
  })

  if (isLoading) return <div className="text-[#a0a0a0]">Loading...</div>
  if (!data) return <div className="text-[#ef4444]">Video not found</div>

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-xl font-semibold text-[#f5f5f5]">
          {data.video.title || 'Untitled Video'}
        </h1>
        <p className="text-sm text-[#6b6b6b] mt-1">
          {data.video.source_type} · {Math.round(data.video.duration_seconds / 60)} min
        </p>
      </div>

      <div className="bg-[#141414] rounded-lg border border-[#2a2a2a] p-4">
        <PipelineStepper steps={data.pipeline} />
      </div>

      {pipelineSteps.status === 'connected' && (
        <div className="text-xs text-[#22c55e] flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-[#22c55e]" />
          Live
        </div>
      )}

      {candidatesData && (
        <div className="space-y-4">
          <h2 className="text-lg font-semibold text-[#f5f5f5]">
            Clip Candidates ({candidatesData.candidates.length})
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {candidatesData.candidates.map((candidate) => (
              <CandidateCard
                key={candidate.id}
                candidate={candidate}
                onApprove={(id) => approveMutation.mutate(id)}
                onReject={(id) => api.post(`/candidates/${id}/reject`)}
                onPreview={(id) => console.log('preview', id)}
              />
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
```

- [ ] **Step 5: Write upload page**

Write `apps/frontend/src/app/(dashboard)/upload/page.tsx`:
```tsx
'use client'

import { useRouter } from 'next/navigation'
import { api } from '@/lib/api'
import { UploadZone } from '@/components/upload/upload-zone'

export default function UploadPage() {
  const router = useRouter()

  const handleFile = async (file: File) => {
    const { id, upload_url } = await api.post<{ id: string; upload_url: string }>('/videos/upload-url')
    if (upload_url) {
      await fetch(upload_url, { method: 'PUT', body: file })
    }
    const video = await api.post('/videos/confirm', {
      storage_key: `raw-videos/${id}.mp4`,
      source_type: 'local',
      metadata: { filename: file.name },
    })
    router.push(`/dashboard/videos/${video.id}`)
  }

  const handleUrl = async (url: string) => {
    const video = await api.post('/videos/confirm', {
      storage_key: url,
      source_type: url.includes('youtube') ? 'youtube' : 'twitch',
      source_url: url,
    })
    router.push(`/dashboard/videos/${video.id}`)
  }

  return (
    <div className="max-w-2xl mx-auto pt-16">
      <h1 className="text-2xl font-semibold text-[#f5f5f5] mb-2">Upload Video</h1>
      <p className="text-sm text-[#6b6b6b] mb-8">
        Drop a video file or paste a YouTube/Twitch URL to start clipping
      </p>
      <UploadZone onFileSelected={handleFile} onUrlSubmit={handleUrl} />
    </div>
  )
}
```

- [ ] **Step 6: Remaining page stubs**

Write `apps/frontend/src/app/(dashboard)/videos/page.tsx` (list view).
Write `apps/frontend/src/app/(dashboard)/clips/page.tsx` (clip list).
Write `apps/frontend/src/app/(dashboard)/clips/[id]/page.tsx` (clip detail with player).
Write `apps/frontend/src/app/(dashboard)/analytics/page.tsx` (basic overview).
Write `apps/frontend/src/app/(dashboard)/settings/page.tsx` (creator profile form).

- [ ] **Step 7: Build and verify**

Run: `cd apps/frontend && npm run build`
Expected: Build succeeds with no errors.

- [ ] **Step 8: Commit**

```bash
git add apps/frontend/
git commit -m "feat: add upload, pipeline, candidates pages with real-time WebSocket"
```

---

### Task 8: Integration Test — Full Pipeline End-to-End

**Files:**
- Modify: Ensure all Docker Compose services work together
- Create: `apps/worker/src/activities/download.py` (real yt-dlp/ffmpeg implementation)
- Create: `apps/worker/src/activities/generate_clip.py` (real ffmpeg cut implementation)
- Test: Manual end-to-end verification

**Interfaces:**
- Consumes: All previous tasks
- Produces: Verified end-to-end flow

- [ ] **Step 1: Implement real download activity**

Write `apps/worker/src/activities/download.py`:
```python
import os
import subprocess
import tempfile
from pathlib import Path
from temporalio import activity
from clippy_config import ClippyConfig
from clippy_storage import StorageBackend
from clippy_events import NATSClient, PipelineEvent
from clippy_database import create_engine, get_session
from clippy_database.models.video import VideoModel
from sqlalchemy import select


class DownloadActivity:
    def __init__(self, storage: StorageBackend, nats: NATSClient, config: ClippyConfig):
        self.storage = storage
        self.nats = nats
        self.config = config

    @activity.defn(name="download_video")
    async def execute(self, video_id: str) -> dict:
        engine = create_engine(self.config.database.dsn)
        session_factory = get_session(engine)

        async with session_factory() as db:
            result = await db.execute(select(VideoModel).where(VideoModel.id == video_id))
            video = result.scalar_one_or_none()
            if not video:
                raise ValueError(f"Video {video_id} not found")

            source_url = video.source_url
            if not source_url and video.storage_key:
                # Already in MinIO (local upload)
                activity.logger.info(f"Video {video_id} already in storage, skipping download")
                return {"video_id": video_id, "status": "already_stored"}

            # Download from URL using yt-dlp
            with tempfile.TemporaryDirectory() as tmpdir:
                output_path = os.path.join(tmpdir, f"{video_id}.mp4")
                try:
                    subprocess.run(
                        ["yt-dlp", "-f", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
                         "-o", output_path, source_url],
                        check=True, capture_output=True, text=True, timeout=7200,
                    )
                except subprocess.CalledProcessError as e:
                    raise RuntimeError(f"yt-dlp failed: {e.stderr}")

                # Upload to MinIO
                storage_key = f"raw-videos/{video_id}.mp4"
                await self.storage.upload("raw-videos", storage_key, output_path)

                # Update video status
                video.storage_key = storage_key
                video.status = "processing"
                await db.commit()

        await self.nats.publish_pipeline_event(PipelineEvent(
            event_type="pipeline.step_update",
            video_id=video_id,
            step_name="download",
            step_status="completed",
        ))

        return {"video_id": video_id, "status": "downloaded"}
```

- [ ] **Step 2: Implement real clip generation activity**

Write `apps/worker/src/activities/generate_clip.py`:
```python
import os
import subprocess
import tempfile
from temporalio import activity
from clippy_config import ClippyConfig
from clippy_storage import StorageBackend
from clippy_events import NATSClient, PipelineEvent
from clippy_database import create_engine, get_session
from clippy_database.models.candidate import ClipCandidateModel
from sqlalchemy import select


class GenerateClipActivity:
    def __init__(self, storage: StorageBackend, nats: NATSClient, config: ClippyConfig):
        self.storage = storage
        self.nats = nats
        self.config = config

    @activity.defn(name="generate_clip")
    async def execute(self, video_id: str, candidate_id: str) -> dict:
        engine = create_engine(self.config.database.dsn)
        session_factory = get_session(engine)

        async with session_factory() as db:
            result = await db.execute(
                select(ClipCandidateModel).where(ClipCandidateModel.id == candidate_id)
            )
            candidate = result.scalar_one_or_none()
            if not candidate:
                raise ValueError(f"Candidate {candidate_id} not found")

            # Download raw video from MinIO
            with tempfile.TemporaryDirectory() as tmpdir:
                raw_path = os.path.join(tmpdir, "input.mp4")
                clip_path = os.path.join(tmpdir, "output.mp4")

                await self.storage.download("raw-videos", f"raw-videos/{video_id}.mp4", raw_path)

                # ffmpeg cut
                start = candidate.start_time
                duration = candidate.end_time - candidate.start_time
                subprocess.run(
                    ["ffmpeg", "-i", raw_path,
                     "-ss", str(start), "-t", str(duration),
                     "-c", "copy", clip_path],
                    check=True, capture_output=True, text=True,
                )

                # Upload clip to MinIO
                clip_key = f"clips/{candidate_id}.mp4"
                await self.storage.upload("clips", clip_key, clip_path)

        await self.nats.publish_pipeline_event(PipelineEvent(
            event_type="clip.generated",
            video_id=video_id,
            step_name="generate",
            step_status="completed",
        ))

        return {"candidate_id": candidate_id, "clip_key": clip_key}
```

- [ ] **Step 3: Start full stack and verify**

Run: `docker compose up --build -d`

Verify:
1. All 10 services start (postgres, redis, minio, qdrant, nats, temporal, temporal-ui, api, frontend, worker)
2. API responds: `curl http://localhost:8000/docs` → 200
3. Frontend loads: `curl http://localhost:3000` → 200
4. Upload presigned URL: `curl -X POST http://localhost:8000/videos/upload-url` → 200 with URL
5. Confirm video: `curl -X POST http://localhost:8000/videos/confirm` → 201
6. List videos: `curl http://localhost:8000/videos` → 200 with list

- [ ] **Step 4: Commit**

```bash
git add .
git commit -m "feat: integrate full stack end-to-end with Docker Compose"
```

---

## Implementation Summary

| Task | Description | Effort |
|------|-------------|--------|
| 1 | Project scaffold + Docker Compose infra | Small |
| 2 | Shared Pydantic models | Medium |
| 3 | Config, Storage, Database, Events, Logging, VectorDB packages | Large |
| 4 | FastAPI service with all REST endpoints | Large |
| 5 | Temporal Worker + pipeline workflow + activity stubs | Large |
| 6 | Next.js app shell + sidebar + routing + API client | Medium |
| 7 | Frontend upload, pipeline, candidates pages | Large |
| 8 | Integration — real activities + end-to-end verification | Medium |
