# Task 3b: Database Package (SQLAlchemy Models + Engine)

**Files to create:**

### Package scaffolding
- `packages/database/pyproject.toml`
- `packages/database/src/clippy_database/__init__.py`
- `packages/database/src/clippy_database/engine.py`

### SQLAlchemy Models
- `packages/database/src/clippy_database/models/__init__.py`
- `packages/database/src/clippy_database/models/base.py`
- `packages/database/src/clippy_database/models/video.py`
- `packages/database/src/clippy_database/models/pipeline.py`
- `packages/database/src/clippy_database/models/transcript.py`
- `packages/database/src/clippy_database/models/scene.py`
- `packages/database/src/clippy_database/models/segment.py`
- `packages/database/src/clippy_database/models/analysis.py`
- `packages/database/src/clippy_database/models/candidate.py`
- `packages/database/src/clippy_database/models/clip.py`
- `packages/database/src/clippy_database/models/analytics.py`
- `packages/database/src/clippy_database/models/learning.py`

## File Contents

### packages/database/pyproject.toml
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

[tool.hatch.build.targets.wheel]
packages = ["src/clippy_database"]
```

### packages/database/src/clippy_database/__init__.py
```python
from .engine import create_engine, get_session, init_db

__all__ = ["create_engine", "get_session", "init_db"]
```

### packages/database/src/clippy_database/engine.py
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

### packages/database/src/clippy_database/models/__init__.py
```python
from .base import Base
from .video import VideoModel
from .pipeline import PipelineRunModel
from .transcript import TranscriptModel
from .scene import SceneModel
from .segment import ConversationSegmentModel
from .analysis import AnalysisResultModel
from .candidate import ClipCandidateModel
from .clip import ClipModel
from .analytics import AnalyticsEventModel
from .learning import LearningHistoryModel
```

### packages/database/src/clippy_database/models/base.py
```python
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass
```

### packages/database/src/clippy_database/models/video.py
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

### packages/database/src/clippy_database/models/pipeline.py
```python
import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, ForeignKey, Text
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

### packages/database/src/clippy_database/models/transcript.py
```python
import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base


class TranscriptModel(Base):
    __tablename__ = "transcripts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    video_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("videos.id"), unique=True, nullable=False)
    language: Mapped[str | None] = mapped_column(String(10), nullable=True)
    segments: Mapped[dict] = mapped_column(JSONB, nullable=False)
    raw_output: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    video = relationship("VideoModel", back_populates="transcripts")
```

### packages/database/src/clippy_database/models/scene.py
```python
import uuid
from datetime import datetime
from sqlalchemy import DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column
from .base import Base


class SceneModel(Base):
    __tablename__ = "scenes"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    video_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("videos.id"), nullable=False)
    boundaries: Mapped[dict] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
```

### packages/database/src/clippy_database/models/segment.py
```python
import uuid
from datetime import datetime
from sqlalchemy import String, Float, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base


class ConversationSegmentModel(Base):
    __tablename__ = "segments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    video_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("videos.id"), nullable=False)
    start_time: Mapped[float] = mapped_column(Float, nullable=False)
    end_time: Mapped[float] = mapped_column(Float, nullable=False)
    text: Mapped[str | None] = mapped_column(Text, nullable=True)
    speaker_id: Mapped[str | None] = mapped_column(String(50), nullable=True)
    segment_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    context: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    video = relationship("VideoModel", back_populates="segments")
```

### packages/database/src/clippy_database/models/analysis.py
```python
import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column
from .base import Base


class AnalysisResultModel(Base):
    __tablename__ = "analysis_results"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    segment_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("segments.id"), nullable=False)
    model: Mapped[str] = mapped_column(String(100), default="")
    signals: Mapped[dict] = mapped_column(JSONB, nullable=False)
    embedding: Mapped[dict] = mapped_column(JSONB, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
```

### packages/database/src/clippy_database/models/candidate.py
```python
import uuid
from datetime import datetime
from sqlalchemy import String, Float, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base


class ClipCandidateModel(Base):
    __tablename__ = "clip_candidates"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    video_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("videos.id"), nullable=False)
    segment_ids: Mapped[dict] = mapped_column(JSONB, default=list)
    start_time: Mapped[float] = mapped_column(Float, nullable=False)
    end_time: Mapped[float] = mapped_column(Float, nullable=False)
    summary: Mapped[str] = mapped_column(Text, default="")
    scores: Mapped[dict] = mapped_column(JSONB, nullable=False)
    predicted_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    actual_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="proposed")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    video = relationship("VideoModel", back_populates="candidates")
```

### packages/database/src/clippy_database/models/clip.py
```python
import uuid
from datetime import datetime
from sqlalchemy import String, Float, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base


class ClipModel(Base):
    __tablename__ = "clips"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    candidate_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("clip_candidates.id"), nullable=False)
    video_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("videos.id"), nullable=False)
    storage_key: Mapped[str] = mapped_column(String(512), nullable=False)
    subtitle_key: Mapped[str | None] = mapped_column(String(512), nullable=True)
    duration_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)
    subtitle_style: Mapped[str] = mapped_column(String(50), default="default")
    file_format: Mapped[str] = mapped_column(String(10), default="mp4")
    resolution: Mapped[str] = mapped_column(String(20), default="1080x1920")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    video = relationship("VideoModel", back_populates="clips")
```

### packages/database/src/clippy_database/models/analytics.py
```python
import uuid
from datetime import datetime
from sqlalchemy import String, Integer, Float, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from .base import Base


class AnalyticsEventModel(Base):
    __tablename__ = "analytics_events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    clip_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("clips.id"), nullable=False)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    platform: Mapped[str] = mapped_column(String(50), nullable=False)
    views: Mapped[int] = mapped_column(Integer, default=0)
    likes: Mapped[int] = mapped_column(Integer, default=0)
    shares: Mapped[int] = mapped_column(Integer, default=0)
    comments: Mapped[int] = mapped_column(Integer, default=0)
    watch_time_seconds: Mapped[float] = mapped_column(Float, default=0)
    completion_rate: Mapped[float] = mapped_column(Float, default=0)
    ctr: Mapped[float] = mapped_column(Float, default=0)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
```

### packages/database/src/clippy_database/models/learning.py
```python
import uuid
from datetime import datetime
from sqlalchemy import String, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column
from .base import Base


class LearningHistoryModel(Base):
    __tablename__ = "learning_history"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    prediction_version: Mapped[str] = mapped_column(String(50), nullable=False)
    insights: Mapped[dict] = mapped_column(JSONB, nullable=False)
    analyzed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
```

## Steps

1. Create all files under `C:\Opencode\clipping-agent\packages\database\`
2. Install the package: `pip install -e .`
3. Verify import works: `python -c "from clippy_database import create_engine; print('DB OK')"`
4. Verify all models import: `python -c "from clippy_database.models import VideoModel, ClipCandidateModel, ClipModel; print('All models OK')"`

## Global Constraints
- Use async SQLAlchemy 2.0 style (Mapped, mapped_column)
- UUID primary keys for all models
- JSONB for flexible/semi-structured data
- Proper ForeignKey relationships
