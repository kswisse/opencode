# Task 2: Shared Models Package

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
- Consumes: (nothing — first package)
- Produces: All Pydantic models consumed by API, Worker, and Frontend

## All File Contents

### packages/shared-models/pyproject.toml
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

### packages/shared-models/src/models/video.py
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

### packages/shared-models/src/models/clip.py
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

### packages/shared-models/src/models/transcript.py
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

### packages/shared-models/src/models/segment.py
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

### packages/shared-models/src/models/analysis.py
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

### packages/shared-models/src/models/scoring.py
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

### packages/shared-models/src/models/profile.py
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

### packages/shared-models/src/events.py
```python
from pydantic import BaseModel
from uuid import UUID
from datetime import datetime


class PipelineEvent(BaseModel):
    event_type: str
    video_id: UUID
    tenant_id: UUID
    step_name: str | None = None
    step_status: str | None = None
    error_message: str | None = None
    timestamp: datetime = datetime.utcnow()


class ClipEvent(BaseModel):
    event_type: str
    clip_id: UUID
    video_id: UUID
    tenant_id: UUID
    platform: str | None = None
    timestamp: datetime = datetime.utcnow()
```

### packages/shared-models/src/models/__init__.py
```python
from .video import Video, VideoCreateResponse, VideoConfirmRequest, VideoListResponse, SourceType, VideoStatus, PipelineStepName
from .clip import Clip, ClipCandidate, ScoreSet, ClipCandidateStatus
from .transcript import Transcript, TranscriptSegment
from .segment import ConversationSegment, SceneBoundary, SpeakerSegment
from .analysis import AnalysisResult, Signal
from .scoring import ScoringWeights, LearningInsight
from .profile import CreatorProfile, BrandColors, SubtitleStyle, AutoEditPreferences
```

### packages/shared-models/src/__init__.py
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

## Steps

- [ ] Step 1: Create all the files listed above under `C:\Opencode\clipping-agent\packages\shared-models\`
- [ ] Step 2: Install the package and verify imports work
- [ ] Step 3: Self-review

Run: `cd C:\Opencode\clipping-agent\packages\shared-models && pip install -e . && python -c "from clippy_models import Video; print(Video(tenant_id='00000000-0000-0000-0000-000000000001', source_type='youtube'))"`

## Global Constraints

- All Python packages use `pyproject.toml` (hatchling), no `setup.py`
- Every Python app/package has `src/` layout
- All Pydantic models use v2 style (model_validator/field_validator where applicable)
