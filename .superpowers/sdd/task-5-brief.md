# Task 5: Worker Service — Temporal Workflow + Activities

**Files to create:**

### Scaffolding
- `apps/worker/pyproject.toml`
- `apps/worker/Dockerfile`
- `apps/worker/src/__init__.py`
- `apps/worker/src/main.py`
- `apps/worker/src/config.py`

### Workflows
- `apps/worker/src/workflows/__init__.py`
- `apps/worker/src/workflows/clip_pipeline.py`

### Activities
- `apps/worker/src/activities/__init__.py`
- `apps/worker/src/activities/download.py`
- `apps/worker/src/activities/transcribe.py`
- `apps/worker/src/activities/scene_detect.py`
- `apps/worker/src/activities/speaker_detect.py`
- `apps/worker/src/activities/segment.py`
- `apps/worker/src/activities/llm_analyze.py`
- `apps/worker/src/activities/score.py`
- `apps/worker/src/activities/generate_clip.py`
- `apps/worker/src/activities/generate_subtitle.py`

## File Contents

### apps/worker/pyproject.toml
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

### apps/worker/Dockerfile
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

### apps/worker/src/main.py
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

### apps/worker/src/config.py
```python
# Local config overrides for Worker service
```

### apps/worker/src/workflows/clip_pipeline.py
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

        download_result = await workflow.execute_activity(
            "download_video",
            video_id,
            start_to_close_timeout=timedelta(hours=2),
            retry_policy=retry_policy,
        )

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

        segments = await workflow.execute_activity(
            "segment_conversation",
            video_id,
            start_to_close_timeout=timedelta(minutes=10),
            retry_policy=retry_policy,
        )

        analysis = await workflow.execute_activity(
            "llm_analyze",
            video_id,
            start_to_close_timeout=timedelta(minutes=30),
            retry_policy=retry_policy,
        )

        candidates = await workflow.execute_activity(
            "score_segments",
            video_id,
            start_to_close_timeout=timedelta(minutes=10),
            retry_policy=retry_policy,
        )

        return {"video_id": str(video_id), "candidates": candidates}
```

### Activity implementations

Each activity follows this pattern. For v0.1, implement as much logic as possible:

**download.py** — Use yt-dlp if video has source_url, otherwise assume already in storage:
```python
import os
import subprocess
import tempfile
from pathlib import Path
from temporalio import activity
from clippy_config import ClippyConfig
from clippy_storage import StorageBackend
from clippy_events import NATSClient
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

            if video.source_url:
                with tempfile.TemporaryDirectory() as tmpdir:
                    import uuid
                    local_id = uuid.uuid4()
                    output_path = os.path.join(tmpdir, f"{local_id}.mp4")
                    subprocess.run(
                        ["yt-dlp", "-f", "best", "-o", output_path, video.source_url],
                        check=True, capture_output=True, text=True, timeout=7200,
                    )
                    storage_key = f"raw-videos/{video_id}.mp4"
                    await self.storage.upload("raw-videos", storage_key, output_path)
                    video.storage_key = storage_key
                    await db.commit()

        return {"video_id": video_id, "status": "downloaded"}
```

**transcribe.py** — Use faster-whisper if available, otherwise return stub:
```python
from temporalio import activity
from clippy_config import ClippyConfig
from clippy_storage import StorageBackend
from clippy_events import NATSClient


class TranscribeActivity:
    def __init__(self, storage: StorageBackend, nats: NATSClient, config: ClippyConfig):
        self.storage = storage
        self.nats = nats
        self.config = config

    @activity.defn(name="transcribe_audio")
    async def execute(self, video_id: str) -> dict:
        activity.logger.info(f"Transcribing video {video_id}")
        return {"video_id": video_id, "segments": []}
```

**scene_detect.py** — Use PySceneDetect if available:
```python
from temporalio import activity
from clippy_config import ClippyConfig
from clippy_storage import StorageBackend
from clippy_events import NATSClient


class SceneDetectActivity:
    def __init__(self, storage: StorageBackend, nats: NATSClient, config: ClippyConfig):
        self.storage = storage
        self.nats = nats
        self.config = config

    @activity.defn(name="detect_scenes")
    async def execute(self, video_id: str) -> dict:
        activity.logger.info(f"Detecting scenes for video {video_id}")
        return {"video_id": video_id, "scenes": []}
```

**speaker_detect.py** — Use pyannote if available:
```python
from temporalio import activity
from clippy_config import ClippyConfig
from clippy_storage import StorageBackend
from clippy_events import NATSClient


class SpeakerDetectActivity:
    def __init__(self, storage: StorageBackend, nats: NATSClient, config: ClippyConfig):
        self.storage = storage
        self.nats = nats
        self.config = config

    @activity.defn(name="detect_speakers")
    async def execute(self, video_id: str) -> dict:
        activity.logger.info(f"Detecting speakers for video {video_id}")
        return {"video_id": video_id, "speakers": []}
```

**segment.py** — Merge transcript segments into conversation segments:
```python
from temporalio import activity
from clippy_config import ClippyConfig
from clippy_storage import StorageBackend
from clippy_events import NATSClient
from clippy_database import create_engine, get_session
from clippy_database.models.transcript import TranscriptModel
from clippy_database.models.segment import ConversationSegmentModel
from sqlalchemy import select
import uuid
from datetime import datetime


class SegmentActivity:
    def __init__(self, storage: StorageBackend, nats: NATSClient, config: ClippyConfig):
        self.storage = storage
        self.nats = nats
        self.config = config

    @activity.defn(name="segment_conversation")
    async def execute(self, video_id: str) -> dict:
        engine = create_engine(self.config.database.dsn)
        session_factory = get_session(engine)

        async with session_factory() as db:
            result = await db.execute(
                select(TranscriptModel).where(TranscriptModel.video_id == video_id)
            )
            transcript = result.scalar_one_or_none()
            if not transcript or not transcript.segments:
                return {"video_id": video_id, "segments": []}

            raw_segments = transcript.segments if isinstance(transcript.segments, list) else []
            created = []
            for seg in raw_segments:
                model = ConversationSegmentModel(
                    id=uuid.uuid4(),
                    video_id=video_id,
                    start_time=seg.get("start", 0),
                    end_time=seg.get("end", 0),
                    text=seg.get("text", ""),
                    speaker_id=seg.get("speaker_id"),
                )
                db.add(model)
                created.append({
                    "id": str(model.id),
                    "start": model.start_time,
                    "end": model.end_time,
                    "text": model.text,
                })
            await db.commit()

        return {"video_id": video_id, "segments": created}
```

**llm_analyze.py** — Call OpenAI API:
```python
from temporalio import activity
from clippy_config import ClippyConfig
from clippy_storage import StorageBackend
from clippy_events import NATSClient


class LLMAnalyzeActivity:
    def __init__(self, storage: StorageBackend, nats: NATSClient, config: ClippyConfig):
        self.storage = storage
        self.nats = nats
        self.config = config

    @activity.defn(name="llm_analyze")
    async def execute(self, video_id: str) -> dict:
        activity.logger.info(f"Analyzing video {video_id} with LLM")
        return {"video_id": video_id, "analysis": []}
```

**score.py** — Implement scoring logic with weights from config:
```python
from temporalio import activity
from clippy_config import ClippyConfig
from clippy_storage import StorageBackend
from clippy_events import NATSClient
from clippy_vectordb import VectorDB
from clippy_database import create_engine, get_session
from clippy_database.models.segment import ConversationSegmentModel
from clippy_database.models.candidate import ClipCandidateModel
from sqlalchemy import select
import uuid


class ScoreActivity:
    def __init__(self, storage: StorageBackend, nats: NATSClient, config: ClippyConfig, vectordb: VectorDB):
        self.storage = storage
        self.nats = nats
        self.config = config
        self.vectordb = vectordb

    @activity.defn(name="score_segments")
    async def execute(self, video_id: str) -> list[dict]:
        engine = create_engine(self.config.database.dsn)
        session_factory = get_session(engine)

        async with session_factory() as db:
            result = await db.execute(
                select(ConversationSegmentModel).where(
                    ConversationSegmentModel.video_id == video_id
                ).order_by(ConversationSegmentModel.start_time)
            )
            segments = result.scalars().all()

            weights = self.config.scoring.weights
            min_duration = self.config.scoring.min_clip_duration
            max_duration = self.config.scoring.max_clip_duration

            candidates = []
            for seg in segments:
                duration = seg.end_time - seg.start_time
                if duration < min_duration or duration > max_duration:
                    continue

                # Basic scoring based on heuristics
                text_len = len(seg.text or "")
                score = {
                    "virality": min(100, text_len * 0.5),
                    "retention": min(100, duration * 2),
                    "hook": min(100, text_len * 0.3),
                    "emotion": 50.0,
                    "shareability": min(100, text_len * 0.4),
                    "educational": 50.0,
                }

                predicted = sum(
                    score.get(k, 0) * w
                    for k, w in weights.items()
                ) / sum(weights.values())

                candidate = ClipCandidateModel(
                    id=uuid.uuid4(),
                    video_id=video_id,
                    segment_ids=[seg.id],
                    start_time=seg.start_time,
                    end_time=seg.end_time,
                    summary=(seg.text or "")[:100],
                    scores=score,
                    predicted_score=predicted,
                )
                db.add(candidate)
                candidates.append({
                    "id": str(candidate.id),
                    "start": candidate.start_time,
                    "end": candidate.end_time,
                    "score": predicted,
                })

            await db.commit()

        return candidates
```

**generate_clip.py** — Use ffmpeg to cut video:
```python
import os
import subprocess
import tempfile
from temporalio import activity
from clippy_config import ClippyConfig
from clippy_storage import StorageBackend
from clippy_events import NATSClient


class GenerateClipActivity:
    def __init__(self, storage: StorageBackend, nats: NATSClient, config: ClippyConfig):
        self.storage = storage
        self.nats = nats
        self.config = config

    @activity.defn(name="generate_clip")
    async def execute(self, video_id: str, candidate_id: str, start_time: float, end_time: float) -> dict:
        activity.logger.info(f"Generating clip {candidate_id} from video {video_id}")
        return {"candidate_id": candidate_id, "clip_key": f"clips/{candidate_id}.mp4"}
```

**generate_subtitle.py** — Generate SRT file:
```python
from temporalio import activity
from clippy_config import ClippyConfig
from clippy_storage import StorageBackend
from clippy_events import NATSClient


class GenerateSubtitleActivity:
    def __init__(self, storage: StorageBackend, nats: NATSClient, config: ClippyConfig):
        self.storage = storage
        self.nats = nats
        self.config = config

    @activity.defn(name="generate_subtitle")
    async def execute(self, clip_key: str, segments: list[dict]) -> dict:
        activity.logger.info(f"Generating subtitles for {clip_key}")
        return {"clip_key": clip_key, "subtitle_key": clip_key.replace(".mp4", ".srt")}
```

## Steps

1. Create all directories and files under `C:\Opencode\clipping-agent\apps\worker\`
2. Install the package: `pip install -e .`
3. Verify import: `python -c "from src.main import main; print('Worker imports OK')"`
4. Verify all activities import: `python -c "from src.activities.download import DownloadActivity; print('Activities OK')"`

## Global Constraints
- Temporal SDK for workflow/activity definitions
- Activities are classes with __init__ for dependency injection
- All DB access via async SQLAlchemy
- Each activity is a single file in src/activities/
