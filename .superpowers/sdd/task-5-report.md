# Task 5 Report: Worker Service — Temporal Workflow + Activities

## Status: DONE

## Files Created (17 files)

### Scaffolding (5 files)
- `apps/worker/pyproject.toml` — Project config with temporalio, openai, and all clippy-* deps; includes `[tool.hatch.build.targets.wheel] packages = ["src/"]` to fix hatchling file discovery
- `apps/worker/Dockerfile` — python:3.12-slim with ffmpeg, pip install
- `apps/worker/src/__init__.py` — Empty package init
- `apps/worker/src/main.py` — Async main: connects Temporal client, NATS, DB, storage, vector DB; registers 9 activities + workflow; runs worker
- `apps/worker/src/config.py` — Placeholder for local config overrides

### Workflows (2 files)
- `apps/worker/src/workflows/__init__.py` — Empty package init
- `apps/worker/src/workflows/clip_pipeline.py` — `ClipPipelineWorkflow`: 7 sequential activity steps (download → transcribe → scenes → speakers → segment → LLM analyze → score) with retry policy and timeouts

### Activities (9 files)
- `apps/worker/src/activities/__init__.py` — Empty package init
- `download.py` — Fetches video via yt-dlp if `source_url` exists, uploads to storage, persists `storage_key`
- `transcribe.py` — Stub (returns `{"segments": []}`)
- `scene_detect.py` — Stub (returns `{"scenes": []}`)
- `speaker_detect.py` — Stub (returns `{"speakers": []}`)
- `segment.py` — Reads transcript from DB, creates `ConversationSegmentModel` rows
- `llm_analyze.py` — Stub (returns `{"analysis": []}`)
- `score.py` — Reads segments from DB, scores with config weights, creates `ClipCandidateModel` rows
- `generate_clip.py` — Stub (returns clip key path)
- `generate_subtitle.py` — Stub (returns SRT key path)

All activities use class-based dependency injection (`__init__` with `storage`, `nats`, `config`), `@activity.defn(name=...)` decorators, and async `execute` methods.

## Verification Results

### `pip install -e .` — SUCCESS
Editable install completed. Required dependencies (temporalio, openai, all clippy-* packages) resolved.

### `python -c "from src.main import main; print('Worker imports OK')"` — OK
Main module imports without error.

### All activities + workflow import — OK
All 9 activity classes and `ClipPipelineWorkflow` import cleanly.

## Concerns
- `[tool.hatch.build.targets.wheel]` needed to be added (project name `clippy-worker` doesn't match `src/` layout); skipped the `[tool.hatch.build]` section as instructed
- Activities with real logic (download, segment, score) reference DB/storage models that must exist from shared packages — verified they import
- Stub activities (transcribe, scene_detect, speaker_detect, llm_analyze, generate_clip, generate_subtitle) return placeholder data — intentional for v0.1
- `download.py` calls `yt-dlp` via subprocess and `import uuid` inline — yt-dlp is not a dependency (stub in v0.1)
- `segment.py` and `score.py` use async SQLAlchemy patterns consistent with the rest of the codebase
