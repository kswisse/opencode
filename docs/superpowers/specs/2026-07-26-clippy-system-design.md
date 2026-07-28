# Clippy — AI Clipping Agent: System Design Document

**Date:** 2026-07-26
**Status:** Draft
**Author:** System Architecture Team

---

## 1. Overview

Clippy is an AI-powered clipping agent SaaS that ingests long-form videos (YouTube, Twitch,
podcasts, local uploads), automatically identifies viral moments, generates edited clips with
subtitles, and continuously improves through a learning loop.

### Core Philosophy

- **Distributed by default** — every component runs independently, no single-process assumptions
- **Local dev, cloud production** — Docker Compose for development, Kubernetes-ready architecture
- **API-first, event-driven** — services communicate via REST + NATS event bus
- **Multi-tenant from day one** — all data scoped by tenant_id
- **Learning loop** — prediction vs actual performance feedback improves scoring over time

### MVP Scope (v0.1) — "Full Flywheel (Trimmed)"

| Build | Defer |
|---|---|
| Video ingestion (YouTube, local, podcast) | Auto-editing engine (face tracking, zoom, blur) |
| Transcription (Whisper) | Thumbnail suggestion |
| Scene detection | Advanced subtitle animations/themes |
| Speaker detection (diarization) | Multi-platform caption format |
| Conversation segmentation | |
| LLM understanding / analysis | |
| Virality scoring (predictions) | |
| Basic clip generation (ffmpeg) | |
| Basic subtitle generation (burn-in) | |
| Basic analytics (views, likes, watch time) | |
| Learning loop (predicted vs actual) | |

---

## 2. Architecture Diagram

```
                          ┌─────────────┐
                          │   Browser    │
                          │  (Next.js)   │
                          └──────┬──────┘
                                 │ REST + WebSocket
                                 ▼
┌──────────────────────────────────────────────────────┐
│                    FastAPI Gateway                     │
│  - REST endpoints            - WebSocket push          │
│  - Auth (NextAuth.js)        - Rate limiting           │
│  - Tenant resolution          - Request validation      │
└─────────────────────┬────────────────────────────────┘
                      │
         ┌────────────┼────────────┐
         ▼            ▼            ▼
┌──────────────┐ ┌──────────┐ ┌──────────┐
│  PostgreSQL  │ │  Redis   │ │  Qdrant  │
│  (primary DB)│ │ (cache)  │ │(vectors) │
└──────────────┘ └──────────┘ └──────────┘
                      │
         ┌────────────┴────────────┐
         ▼                         ▼
┌──────────────────┐    ┌──────────────────┐
│  Temporal Server │    │  NATS JetStream   │
│ (workflow orche- │    │  (event bus)      │
│  stration)       │    │                   │
└────────┬─────────┘    └────────┬─────────┘
         │                       │
         ▼                       ▼
┌──────────────────────────────────────────────────────┐
│                 Temporal Worker                       │
│  ┌─────────┐ ┌──────────┐ ┌────────┐ ┌───────────┐  │
│  │ Download │ │Transcribe│ │ Scene  │ │  Speaker  │  │
│  │ Activity │ │ Activity │ │ Detect │ │  Detect   │  │
│  └─────────┘ └──────────┘ └────────┘ └───────────┘  │
│  ┌─────────┐ ┌──────────┐ ┌────────┐ ┌───────────┐  │
│  │ Segment │ │ LLM      │ │ Score  │ │  Generate │  │
│  │ Activity│ │ Activity │ │Activity│ │  Activity │  │
│  └─────────┘ └──────────┘ └────────┘ └───────────┘  │
│  ┌─────────┐ ┌──────────┐                             │
│  │Subtitle │ │  Auto    │                             │
│  │Activity │ │  Edit    │                             │
│  └─────────┘ └──────────┘                             │
└──────────────────────────────────────────────────────┘
                      │
                      ▼
              ┌──────────────┐
              │   MinIO / S3  │
              │ (object store)│
              └──────────────┘
```

---

## 3. Technology Stack

### Backend
| Component | Technology | Rationale |
|---|---|---|
| API Gateway | FastAPI | Async, Pydantic validation, OpenAPI auto-docs |
| Workflow Engine | Temporal | Long-running video pipelines, retry, state persistence |
| Event Bus | NATS JetStream | Lightweight, persistent, pub/sub for cross-service events |
| Database | PostgreSQL 16 | Relational data, JSONB for flexible schemas |
| Vector Store | Qdrant | Embedding storage for RAG on clip patterns |
| Cache | Redis 7 | Session cache, rate limiting, task queue fallback |
| Object Storage | MinIO → S3 | S3-compatible API, local dev with MinIO |

### AI/ML
| Component | Technology |
|---|---|
| Speech-to-Text | Whisper (whisper.cpp or faster-whisper) |
| Speaker Diarization | PyAnnote audio |
| Scene Detection | PySceneDetect + ffmpeg |
| LLM Analysis | OpenAI GPT-4o / Anthropic Claude (pluggable) |
| Embeddings | OpenAI text-embedding-3-small / local |
| Score Prediction | Custom ML model (scikit-learn / XGBoost) |

### Frontend
| Component | Technology |
|---|---|
| Framework | Next.js 14 (App Router) |
| Styling | Tailwind CSS |
| State Management | TanStack Query (server), React state (client) |
| Charts | Recharts |
| WebSocket | Native WebSocket + custom hook |
| Video Player | HTML5 `<video>` + HLS.js |

### Infrastructure
| Component | Technology |
|---|---|
| Containers | Docker Compose (dev), Kubernetes (prod) |
| IaC | Terraform (future) |
| CI/CD | GitHub Actions |

---

## 4. Data Flow — Video Pipeline

### 4.1 Upload Flow

```
Browser                     API                    MinIO
  │                          │                      │
  │  POST /videos/upload-url │                      │
  │  ──────────────────────► │                      │
  │  ◄──── { url, fields } ──│                      │
  │                          │                      │
  │  PUT file (presigned)    │                      │
  │  ──────────────────────────────────────────────► │
  │  ◄──── 200 OK ────────────────────────────────── │
  │                          │                      │
  │  POST /videos/confirm    │                      │
  │  ──────────────────────► │                      │
  │                          │── store metadata ──► DB
  │                          │── start workflow ──► Temporal
  │  ◄── { video_id } ───────│                      │
```

### 4.2 Pipeline Flow (Temporal Workflow)

```
Workflow: ClipPipelineWorkflow

Activity 1: download_video
  Input:  storage_key (from MinIO) or YouTube URL
  Output: local file path → upload raw video to MinIO
  Error:  retry 3x, fail workflow if all retries exhausted

Activity 2: transcribe_audio
  Input:  MinIO path of raw video
  Output: List[TranscriptSegment] (text, start, end, confidence)
  GPU:    yes (whisper.cpp)

Activity 3: detect_scenes [parallel with 2]
  Input:  MinIO path of raw video  
  Output: List[SceneBoundary] (start, end, label)
  GPU:    no (PySceneDetect)

Activity 4: detect_speakers [parallel with 2]
  Input:  MinIO path of raw video
  Output: List[SpeakerSegment] (speaker_id, start, end)
  GPU:    yes (PyAnnote)

Activity 5: segment_conversation
  Input:  transcript + scenes + speakers
  Output: List[ConversationSegment]
  Logic:  Merge all three signals into coherent segments

Activity 6: llm_analyze
  Input:  ConversationSegment[]
  Output: AnalysisResult[] (signals detected, embeddings)
  Logic:  For each segment, LLM identifies virality signals
          (conflict, surprise, punchline, value, etc.)

Activity 7: score_segments
  Input:  AnalysisResult[]
  Output: ClipCandidate[] (with scores)
  Logic:  Weighted scoring model → virality, retention, hook, etc.
          Embedding similarity to known viral patterns in Qdrant

Activity 8: generate_clips
  Input:  ClipCandidate[] (approved ones → actual clips)
  Output: Clip[] (video files in MinIO)
  Logic:  ffmpeg cut + format conversion

Activity 9: generate_subtitles
  Input:  Clip[] + transcript
  Output: Subtitle files (.srt, .ass, burned-in mp4)
```

### 4.3 Event Flow (NATS)

```
After each activity completes:
  Worker ──publish──► NATS ──► API (WebSocket push to browser)

Events:
  video.ingested        → { video_id, storage_key }
  transcription.done    → { video_id, segment_count }
  analysis.done         → { video_id, candidate_count }
  clips.generated       → { video_id, clip_ids[] }
  clip.approved         → { clip_id, video_id }
  clip.published        → { clip_id, platform }
  analytics.recorded    → { clip_id, views, likes }
```

---

## 5. Database Schema

### Core Tables

```sql
-- Multi-tenant root
CREATE TABLE tenants (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name        VARCHAR(255) NOT NULL,
    slug        VARCHAR(100) UNIQUE NOT NULL,
    config      JSONB DEFAULT '{}',
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- Raw video metadata
CREATE TABLE videos (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID REFERENCES tenants(id),
    source_type     VARCHAR(20) NOT NULL CHECK (source_type IN ('youtube','twitch','podcast','local')),
    source_url      TEXT,
    status          VARCHAR(20) NOT NULL DEFAULT 'pending'
                    CHECK (status IN ('pending','downloading','processing','ready','failed')),
    storage_key     TEXT,
    thumbnail_key   TEXT,
    duration_seconds INTEGER,
    file_size_bytes  BIGINT,
    metadata        JSONB DEFAULT '{}',
    error_message   TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Pipeline execution trace (per Temporal workflow)
CREATE TABLE pipeline_runs (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    video_id    UUID REFERENCES videos(id),
    workflow_id VARCHAR(255) NOT NULL,
    status      VARCHAR(20) NOT NULL,
    steps       JSONB DEFAULT '[]',
    started_at  TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    error       TEXT
);

-- Full transcript (1:1 with video)
CREATE TABLE transcripts (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    video_id    UUID REFERENCES videos(id) UNIQUE,
    language    VARCHAR(10),
    segments    JSONB NOT NULL,  -- [{start, end, text, speaker_id, confidence}]
    raw_output  JSONB,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- Scene boundaries
CREATE TABLE scenes (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    video_id    UUID REFERENCES videos(id),
    boundaries  JSONB NOT NULL,  -- [{start, end, label}]
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- Conversation segments (merged analysis units)
CREATE TABLE segments (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    video_id        UUID REFERENCES videos(id),
    start_time      DOUBLE PRECISION NOT NULL,
    end_time        DOUBLE PRECISION NOT NULL,
    text            TEXT,
    speaker_id      VARCHAR(50),
    segment_type    VARCHAR(50),
    context         JSONB DEFAULT '{}',
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- LLM analysis output per segment
CREATE TABLE analysis_results (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    segment_id  UUID REFERENCES segments(id),
    model       VARCHAR(100) NOT NULL,
    signals     JSONB NOT NULL,  -- [{type, confidence, detail}]
    embedding   vector(1536),    -- pgvector
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- Clip candidates (proposed clips with scores)
CREATE TABLE clip_candidates (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    video_id        UUID REFERENCES videos(id),
    segment_ids     UUID[],
    start_time      DOUBLE PRECISION NOT NULL,
    end_time        DOUBLE PRECISION NOT NULL,
    summary         TEXT,
    scores          JSONB NOT NULL,
    predicted_score DOUBLE PRECISION,
    actual_score    DOUBLE PRECISION,
    status          VARCHAR(20) DEFAULT 'proposed'
                    CHECK (status IN ('proposed','approved','rejected','generated')),
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Generated clips
CREATE TABLE clips (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    candidate_id      UUID REFERENCES clip_candidates(id),
    video_id          UUID REFERENCES videos(id),
    storage_key       TEXT NOT NULL,
    subtitle_key      TEXT,
    duration_seconds  DOUBLE PRECISION,
    subtitle_style    VARCHAR(50) DEFAULT 'default',
    file_format       VARCHAR(10) DEFAULT 'mp4',
    resolution        VARCHAR(20) DEFAULT '1080x1920',
    created_at        TIMESTAMPTZ DEFAULT NOW()
);

-- Analytics events (append-only)
CREATE TABLE analytics_events (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    clip_id             UUID REFERENCES clips(id),
    tenant_id           UUID REFERENCES tenants(id),
    platform            VARCHAR(50) NOT NULL,
    views               INTEGER DEFAULT 0,
    likes               INTEGER DEFAULT 0,
    shares              INTEGER DEFAULT 0,
    comments            INTEGER DEFAULT 0,
    watch_time_seconds  DOUBLE PRECISION DEFAULT 0,
    completion_rate     DOUBLE PRECISION DEFAULT 0,
    ctr                 DOUBLE PRECISION DEFAULT 0,
    recorded_at         TIMESTAMPTZ DEFAULT NOW(),
    created_at          TIMESTAMPTZ DEFAULT NOW()
);

-- Learning history (model weight adjustments)
CREATE TABLE learning_history (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    analyzed_at         TIMESTAMPTZ DEFAULT NOW(),
    prediction_version  VARCHAR(50) NOT NULL,
    insights            JSONB NOT NULL,
    created_at          TIMESTAMPTZ DEFAULT NOW()
);
```

---

## 6. API Design

### REST Endpoints

```
Videos
  POST   /videos/upload-url         → { url, fields } (presigned)
  POST   /videos/confirm            → { video: Video }
  GET    /videos                    → { videos: Video[], total: int }
  GET    /videos/{id}               → { video: Video, pipeline: PipelineStep[] }
  DELETE /videos/{id}

Candidates
  GET    /videos/{id}/candidates    → { candidates: ClipCandidate[] }
  POST   /candidates/{id}/approve   → { clip: Clip }
  POST   /candidates/{id}/reject    → { ok: boolean }
  POST   /candidates/batch/approve  → { clips: Clip[] }
  POST   /candidates/batch/reject   → { ok: boolean }

Clips
  GET    /clips                     → { clips: Clip[] }
  GET    /clips/{id}                → { clip: Clip }
  POST   /clips/{id}/publish        → { ok: boolean }

Analytics
  POST   /clips/{id}/analytics      → { ok: boolean }
  GET    /analytics/overview        → AnalyticsOverview

Profile
  GET    /profile                   → CreatorProfile
  PATCH  /profile                   → CreatorProfile
```

### WebSocket
```
WS /ws/videos/{video_id}
  Events:
    pipeline.step_update  → { step: PipelineStep }
    pipeline.completed    → { video_id: string }
    pipeline.failed       → { video_id: string, error: string }
```

---

## 7. Project Structure

```
clipping-agent/
├── pyproject.toml
├── docker-compose.yml
├── docker-compose.infra.yml
├── .env.example
│
├── apps/
│   ├── api/                     # FastAPI REST + WebSocket
│   │   ├── pyproject.toml
│   │   ├── Dockerfile
│   │   └── src/
│   │       ├── main.py
│   │       ├── routers/
│   │       ├── dependencies/
│   │       └── middleware/
│   │
│   ├── frontend/                # Next.js
│   │   ├── package.json
│   │   ├── Dockerfile
│   │   └── src/
│   │       ├── app/
│   │       ├── components/
│   │       ├── hooks/
│   │       └── lib/
│   │
│   └── worker/                  # Temporal Worker
│       ├── pyproject.toml
│       ├── Dockerfile
│       └── src/
│           ├── main.py
│           ├── workflows/
│           │   ├── clip_pipeline.py
│           │   └── analytics.py
│           └── activities/
│               ├── ingestion/
│               ├── transcription/
│               ├── scene_detection/
│               ├── speaker_detection/
│               ├── segmentation/
│               ├── llm_analysis/
│               ├── scoring/
│               ├── clip_generation/
│               ├── subtitle_generation/
│               └── analytics/
│
├── packages/
│   ├── shared-models/           # Pydantic models
│   ├── config/                  # YAML config loader
│   ├── storage/                 # MinIO/S3 abstraction
│   ├── database/                # SQLAlchemy async + migrations
│   ├── vectordb/                # Qdrant wrapper
│   ├── events/                  # NATS client
│   └── logging/                 # Structured logging
│
└── docs/
    ├── frontend-architecture.md
    ├── clippy-design-system.md
    └── superpowers/specs/
        ├── 2026-07-26-clippy-system-design.md   (this file)
        └── 2026-07-26-clippy-ux-architecture.md
```

---

## 8. Deployment Architecture

### Development (Docker Compose)

```yaml
services:
  postgres:       # PostgreSQL 16
  redis:          # Redis 7
  qdrant:         # Qdrant vector store
  minio:          # S3-compatible storage
  nats:           # NATS JetStream
  temporal:       # Temporal Server
  temporal-ui:    # Temporal Web UI
  api:            # FastAPI (hot-reload)
  frontend:       # Next.js (hot-reload)
  worker:         # Temporal Worker
```

### Production (Kubernetes)

```
Each service → separate Deployment + Service
  - Stateless: api, frontend, worker → HPA auto-scaling
  - Stateful: postgres, redis, qdrant, minio, nats, temporal

Networking:
  - Ingress → api (REST) + frontend (static)
  - Internal: worker → temporal, nats (cluster-internal)
  - Storage: PVC for DBs, S3 for object storage
```

---

## 9. Learning Loop Design

### How it works

1. **Prediction:** When scoring segments, the system predicts virality scores
2. **Publication:** Creator publishes clip to YouTube/TikTok/etc.
3. **Collection:** Analytics data comes back (views, likes, watch time, CTR)
4. **Comparison:** `predicted_score` vs `actual_score` (composite metric)
5. **Adjustment:** Weight adjustments moved to `learning_history`

### Feedback Schema

```json
{
  "prediction_version": "v1.2",
  "insights": [
    {
      "signal_type": "controversial_statement",
      "weight_before": 0.8,
      "weight_after": 0.85,
      "delta": 0.05,
      "confidence": 0.92
    },
    {
      "signal_type": "educational_moment",
      "weight_before": 0.6,
      "weight_after": 0.55,
      "delta": -0.05,
      "confidence": 0.78
    }
  ]
}
```

### Qdrant Usage

- Store embeddings of successful clips (high actual_score)
- Store embeddings of unsuccessful clips (low actual_score)
- When scoring new segments, compute similarity to successful clusters
- Boost score for segments near known viral patterns

---

## 10. Configuration (YAML)

```yaml
# config/default.yaml
project:
  name: "clippy"
  environment: "development"

storage:
  provider: "minio"  # minio | s3
  endpoint: "http://minio:9000"
  region: "us-east-1"
  buckets:
    raw-videos: "raw-videos"
    clips: "clips"
    transcripts: "transcripts"
    thumbnails: "thumbnails"

database:
  dsn: "postgresql+asyncpg://clippy:clippy@postgres:5432/clippy"
  pool_size: 20
  max_overflow: 10

redis:
  url: "redis://redis:6379/0"

temporal:
  host: "temporal:7233"
  namespace: "clippy-default"
  task_queue: "clip-pipeline"

nats:
  servers: ["nats://nats:4222"]

qdrant:
  host: "qdrant"
  port: 6333
  collection: "clip-embeddings"

workers:
  pools:
    gpu:
      max_concurrent: 1
      activities:
        - transcribe_audio
        - detect_speakers
        - llm_analyze
    cpu:
      max_concurrent: 4
      activities:
        - download_video
        - detect_scenes
        - segment_conversation
        - generate_clips
        - generate_subtitles

scoring:
  weights:
    virality: 1.0
    retention: 0.9
    hook: 0.8
    emotion: 0.7
    shareability: 0.6
    educational: 0.4
  min_clip_duration: 15     # seconds
  max_clip_duration: 120    # seconds
  min_score_threshold: 0.3  # discard below this
```

---

## 11. Key Design Decisions

| Decision | Choice | Alternative Considered | Rationale |
|---|---|---|---|
| Workflow Engine | Temporal | Celery, Prefect | Long-running pipelines, built-in retry, state persistence, visibility UI |
| Event Bus | NATS | RabbitMQ, Kafka, Redis pub/sub | Lightweight, persistent streams, good DX, small resource footprint |
| Object Storage | MinIO → S3 | Local filesystem | Stateless workers, shared access, presigned URLs for browser |
| LLM Provider | Pluggable (OpenAI default) | Single provider | Avoid vendor lock-in, swap models per cost/quality needs |
| Vector Store | Qdrant | Pinecone, Weaviate, pgvector | Self-hostable, good performance for 1536d embeddings, Docker-friendly |
| Scoring Model | Custom (scikit-learn) | Pre-built API | Full control, on-prem capability, learning loop needs custom training |

---

## 12. Scalability Considerations

- **Video processing:** Workers scale horizontally — each worker polls Temporal for tasks
- **GPU contention:** GPU pool limited to 1 concurrent — queue naturally managed by Temporal
- **Storage:** MinIO can scale to petabytes; presigned URLs offload bandwidth from API
- **Database:** UUID PKs enable sharding; JSONB avoids schema locks for flexible data
- **Event bus:** NATS handles millions of messages/sec; events are small (JSON payloads)
- **Multi-tenant:** All queries scoped by tenant_id; future: connection pooling per tenant tier
