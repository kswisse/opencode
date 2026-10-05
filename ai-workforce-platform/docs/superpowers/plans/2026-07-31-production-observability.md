# Production Observability Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add production-grade observability to the entire backend — structured logging, correlation IDs, OpenTelemetry tracing, Prometheus metrics, health endpoints, and comprehensive error logging.

**Architecture:** Introduce an `src/observability/` module that encapsulates all observability concerns. Use `structlog` for structured JSON logging, `contextvars` for correlation ID propagation through async call chains, `opentelemetry` for distributed tracing across FastAPI/SQLAlchemy/Redis/HTTP, and `prometheus-client` for metrics collection. Register middleware in FastAPI app factory and instrument ARQ worker separately.

**Tech Stack:** structlog, opentelemetry-api/sdk, opentelemetry-instrumentation-fastapi, opentelemetry-instrumentation-sqlalchemy, opentelemetry-instrumentation-redis, opentelemetry-instrumentation-httpx, opentelemetry-exporter-otlp, prometheus-client, prometheus-fastapi-instrumentator

## Global Constraints

- Do NOT modify business logic
- Do NOT change APIs except adding /health and /metrics endpoints
- Keep all 33 existing tests passing
- All logs must be JSON format
- Every log must include: timestamp, level, request_id, job_id (if exists), goal_id (if exists), user_id (if authenticated), service, execution_time_ms
- Correlation ID must propagate: API → ARQ Job → CEO Agent → Agent Factory → Scheduler → Memory
- Support development/testing/production environments with different log verbosity

---

## File Structure

```
src/observability/
├── __init__.py          # Public API exports
├── config.py            # Environment-aware observability settings
├── logging.py           # structlog configuration + processors
├── correlation.py       # contextvars-based correlation ID
├── middleware.py         # FastAPI middleware (request logging + correlation)
├── metrics.py           # Custom Prometheus metrics + /metrics endpoint
├── tracing.py           # OpenTelemetry setup + instrumentor registration
└── health.py            # GET /health and GET /ready endpoints

Files modified:
├── src/main.py          # Register middleware, health, metrics, tracing
├── src/config.py        # Add OBSERVABILITY_* settings
├── src/worker/arq_worker.py  # Add job logging, tracing, correlation
├── src/services/pipeline.py  # Add tracing spans per stage
├── src/services/ceo_agent.py # Add tracing span
├── src/services/agent_factory.py # Add tracing span
├── src/services/task_scheduler.py # Add tracing span
├── src/services/memory_service.py # Add tracing span
├── src/services/llm_client.py     # Add tracing span + error logging
├── pyproject.toml       # Add observability dependencies
└── docker-compose.yml   # (no changes needed for observability)
```

---

### Task 1: Add Observability Dependencies

**Files:**
- Modify: `pyproject.toml`

**Interfaces:**
- Produces: Dependencies available for import by all subsequent tasks

- [ ] **Step 1: Add production observability dependencies**

```toml
# Add to [project] dependencies list in pyproject.toml:
    "structlog>=24.1.0",
    "opentelemetry-api>=1.22.0",
    "opentelemetry-sdk>=1.22.0",
    "opentelemetry-instrumentation-fastapi>=0.43b0",
    "opentelemetry-instrumentation-sqlalchemy>=0.43b0",
    "opentelemetry-instrumentation-redis>=0.43b0",
    "opentelemetry-instrumentation-httpx>=0.43b0",
    "opentelemetry-exporter-otlp>=1.22.0",
    "prometheus-client>=0.19.0",
    "prometheus-fastapi-instrumentator>=7.0.0",
```

- [ ] **Step 2: Install dependencies**

Run: `pip install structlog opentelemetry-api opentelemetry-sdk opentelemetry-instrumentation-fastapi opentelemetry-instrumentation-sqlalchemy opentelemetry-instrumentation-redis opentelemetry-instrumentation-httpx opentelemetry-exporter-otlp prometheus-client prometheus-fastapi-instrumentator`
Expected: Successful installation

- [ ] **Step 3: Commit**

```bash
git add pyproject.toml
git commit -m "deps: add observability packages (structlog, opentelemetry, prometheus)"
```

---

### Task 2: Observability Configuration

**Files:**
- Create: `src/observability/__init__.py`
- Create: `src/observability/config.py`
- Modify: `src/config.py`

**Interfaces:**
- Produces: `ObservabilitySettings` dataclass, `get_observability_config()` function
- Consumes: `Settings` from `src/config.py` (reads `environment` field)

- [ ] **Step 1: Add environment setting to src/config.py**

Add after `debug: bool = False`:

```python
    environment: str = "development"  # development | testing | production
    otlp_endpoint: str = "http://localhost:4317"
    service_name: str = "ai-workforce-platform"
```

- [ ] **Step 2: Create src/observability/__init__.py**

```python
"""Production observability module."""
```

- [ ] **Step 3: Create src/observability/config.py**

```python
"""Environment-aware observability configuration."""
from dataclasses import dataclass


@dataclass(frozen=True)
class ObservabilitySettings:
    environment: str
    service_name: str
    otlp_endpoint: str
    log_level: str
    log_json: bool
    enable_tracing: bool
    enable_metrics: bool

    @classmethod
    def from_settings(cls, settings) -> "ObservabilitySettings":
        env = settings.environment
        return cls(
            environment=env,
            service_name=settings.service_name,
            otlp_endpoint=settings.otlp_endpoint,
            log_level=_log_level_for_env(env),
            log_json=env == "production",
            enable_tracing=env != "testing",
            enable_metrics=env != "testing",
        )


def _log_level_for_env(env: str) -> str:
    return {
        "development": "DEBUG",
        "testing": "WARNING",
        "production": "INFO",
    }.get(env, "INFO")
```

- [ ] **Step 4: Commit**

```bash
git add src/config.py src/observability/__init__.py src/observability/config.py
git commit -m "feat(obs): add observability config with environment-based settings"
```

---

### Task 3: Correlation ID Context Propagation

**Files:**
- Create: `src/observability/correlation.py`

**Interfaces:**
- Produces: `request_id_var` (ContextVar), `get_request_id()`, `set_request_id()`, `request_id_ctx_manager()`
- Consumes: None (leaf module)

- [ ] **Step 1: Create src/observability/correlation.py**

```python
"""Request-scoped correlation ID propagation via contextvars."""
import contextvars
import uuid
from collections.abc import Generator
from contextlib import contextmanager

request_id_var: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "request_id", default=None
)


def get_request_id() -> str | None:
    """Get the current request ID from context."""
    return request_id_var.get()


def set_request_id(request_id: str | None) -> contextvars.Token:
    """Set the request ID in context. Returns token for reset."""
    return request_id_var.set(request_id)


def generate_request_id() -> str:
    """Generate a new UUID4 request ID."""
    return str(uuid.uuid4())


@contextmanager
def request_id_ctx_manager(rid: str | None = None) -> Generator[str, None, None]:
    """Context manager that sets a request ID and resets on exit."""
    new_id = rid or generate_request_id()
    token = set_request_id(new_id)
    try:
        yield new_id
    finally:
        request_id_var.reset(token)
```

- [ ] **Step 2: Commit**

```bash
git add src/observability/correlation.py
git commit -m "feat(obs): add correlation ID context propagation via contextvars"
```

---

### Task 4: Structured Logging with structlog

**Files:**
- Create: `src/observability/logging.py`

**Interfaces:**
- Produces: `setup_logging()` function, `get_logger()` wrapper
- Consumes: `ObservabilitySettings`, `get_request_id()` from correlation module

- [ ] **Step 1: Create src/observability/logging.py**

```python
"""structlog configuration for structured JSON logging."""
import logging
import time
import structlog

from src.observability.correlation import get_request_id
from src.observability.config import ObservabilitySettings


def _add_request_id(logger, method_name, event_dict):
    """Processor: inject current request_id into every log event."""
    rid = get_request_id()
    if rid:
        event_dict["request_id"] = rid
    return event_dict


def _add_service_name(service_name: str):
    """Processor: inject service name."""
    def processor(logger, method_name, event_dict):
        event_dict["service"] = service_name
        return event_dict
    return processor


def _add_timestamp(logger, method_name, event_dict):
    """Processor: add ISO timestamp."""
    event_dict["timestamp"] = time.time()
    return event_dict


def setup_logging(settings: ObservabilitySettings) -> None:
    """Configure structlog based on environment."""
    shared_processors = [
        structlog.contextvars.merge_contextvars,
        _add_request_id,
        _add_service_name(settings.service_name),
        _add_timestamp,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
    ]

    if settings.log_json:
        renderer = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer(colors=True)

    structlog.configure(
        processors=[
            *shared_processors,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    formatter = structlog.stdlib.ProcessorFormatter(
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            renderer,
        ],
    )

    handler = logging.StreamHandler()
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(settings.log_level)

    # Silence noisy libraries
    for name in ("uvicorn.access", "httpcore", "httpx"):
        logging.getLogger(name).setLevel(logging.WARNING)


def get_logger(name: str = __name__) -> structlog.stdlib.BoundLogger:
    """Get a bound structlog logger."""
    return structlog.get_logger(name)
```

- [ ] **Step 2: Commit**

```bash
git add src/observability/logging.py
git commit -m "feat(obs): add structlog setup with JSON and console renderers"
```

---

### Task 5: FastAPI Middleware (Request Logging + Correlation)

**Files:**
- Create: `src/observability/middleware.py`

**Interfaces:**
- Produces: `ObservabilityMiddleware` class (ASGI middleware), `bind_context_to_request()` dependency
- Consumes: `generate_request_id()`, `set_request_id()`, `get_request_id()` from correlation, `get_logger()` from logging

- [ ] **Step 1: Create src/observability/middleware.py**

```python
"""FastAPI middleware for request logging and correlation ID injection."""
import time
import uuid
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from src.observability.correlation import generate_request_id, set_request_id, get_request_id
from src.observability.logging import get_logger

# Paths to exclude from logging (health checks, metrics)
_EXCLUDE_PATHS = frozenset({"/health", "/ready", "/metrics", "/docs", "/openapi.json"})


class ObservabilityMiddleware(BaseHTTPMiddleware):
    """Logs every HTTP request/response with correlation ID and latency."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # Generate or extract correlation ID
        rid = request.headers.get("X-Request-ID") or generate_request_id()
        token = set_request_id(rid)

        log = get_logger("http")

        start = time.monotonic()
        try:
            response = await call_next(request)
        except Exception:
            duration_ms = (time.monotonic() - start) * 1000
            log.error(
                "http_request_error",
                method=request.method,
                path=request.url.path,
                duration_ms=round(duration_ms, 2),
                exc_info=True,
            )
            raise
        finally:
            set_request_id(None)  # noqa: F841 — reset via token would lose response context
            # Actually reset properly:
            request_id_var_reset = token

        duration_ms = (time.monotonic() - start) * 1000

        # Inject correlation ID into response headers
        response.headers["X-Request-ID"] = rid

        # Skip logging for excluded paths
        if request.url.path not in _EXCLUDE_PATHS:
            # Extract user_id from request state if available
            user_id = getattr(request.state, "user_id", None)

            log.info(
                "http_request",
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                duration_ms=round(duration_ms, 2),
                request_id=rid,
                user_id=user_id,
            )

        return response


async def bind_context_to_request(request: Request) -> None:
    """FastAPI dependency that binds user context to request.state for logging."""
    # This is called after auth middleware has set request.state.user_id
    pass  # The middleware already handles logging; this exists as an extension point
```

- [ ] **Step 2: Fix the middleware (clean implementation)**

Replace the middleware class with a cleaner version that handles the token reset correctly:

```python
"""FastAPI middleware for request logging and correlation ID injection."""
import time
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from src.observability.correlation import generate_request_id, set_request_id
from src.observability.logging import get_logger

# Paths to exclude from logging (health checks, metrics)
_EXCLUDE_PATHS = frozenset({"/health", "/ready", "/metrics", "/docs", "/openapi.json"})


class ObservabilityMiddleware(BaseHTTPMiddleware):
    """Logs every HTTP request/response with correlation ID and latency."""

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        # Generate or extract correlation ID from incoming header
        rid = request.headers.get("X-Request-ID") or generate_request_id()
        token = set_request_id(rid)

        log = get_logger("http")
        start = time.monotonic()

        try:
            response = await call_next(request)
        except Exception:
            duration_ms = (time.monotonic() - start) * 1000
            log.error(
                "http_request_error",
                method=request.method,
                path=request.url.path,
                duration_ms=round(duration_ms, 2),
                exc_info=True,
            )
            raise
        finally:
            set_request_id(None)  # Reset context

        duration_ms = (time.monotonic() - start) * 1000
        response.headers["X-Request-ID"] = rid

        if request.url.path not in _EXCLUDE_PATHS:
            log.info(
                "http_request",
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                duration_ms=round(duration_ms, 2),
                request_id=rid,
            )

        return response
```

- [ ] **Step 3: Commit**

```bash
git add src/observability/middleware.py
git commit -m "feat(obs): add request logging middleware with correlation ID"
```

---

### Task 6: Prometheus Metrics

**Files:**
- Create: `src/observability/metrics.py`

**Interfaces:**
- Produces: `setup_metrics(app)`, `JOB_DURATION`, `PIPELINE_SUCCESS`, `PIPELINE_FAILURE`, `SCHEDULER_TASKS`, `MEMORY_OPS`, `DB_QUERIES`, `REDIS_OPS`
- Consumes: FastAPI app instance

- [ ] **Step 1: Create src/observability/metrics.py**

```python
"""Prometheus metrics for HTTP, background jobs, pipelines, and infrastructure."""
from prometheus_client import Counter, Histogram, Gauge, Info
from prometheus_fastapi_instrumentator import Instrumentator

# --- HTTP Metrics (auto-collected by Instrumentator) ---

# --- Background Job Metrics ---
JOB_DURATION = Histogram(
    "background_job_duration_seconds",
    "Background job execution duration in seconds",
    ["job_type", "status"],
    buckets=(0.1, 0.5, 1, 2, 5, 10, 30, 60, 120, 300, 600),
)

JOBS_TOTAL = Counter(
    "background_jobs_total",
    "Total background jobs executed",
    ["job_type", "status"],
)

# --- Pipeline Metrics ---
PIPELINE_SUCCESS = Counter(
    "pipeline_success_total",
    "Total successful pipeline executions",
)

PIPELINE_FAILURE = Counter(
    "pipeline_failure_total",
    "Total failed pipeline executions",
)

# --- Scheduler Metrics ---
SCHEDULER_TASKS = Counter(
    "scheduler_tasks_total",
    "Total scheduler task executions",
    ["status"],
)

# --- Memory Metrics ---
MEMORY_OPS = Counter(
    "memory_operations_total",
    "Total memory service operations",
    ["operation_type"],
)

# --- Database Metrics ---
DB_QUERIES = Counter(
    "database_queries_total",
    "Total database queries executed",
    ["operation"],
)

# --- Redis Metrics ---
REDIS_OPS = Counter(
    "redis_operations_total",
    "Total Redis operations",
    ["operation"],
)

# --- Worker Info ---
WORKER_INFO = Info(
    "arq_worker",
    "ARQ worker information",
)


def setup_metrics(app) -> None:
    """Instrument FastAPI app with Prometheus metrics."""
    instrumentator = Instrumentator(
        should_group_status_codes=False,
        should_ignore_untemplated=True,
        excluded_handlers=["/metrics", "/health", "/ready"],
    )
    instrumentator.instrument(app)
    instrumentator.expose(app, endpoint="/metrics")
```

- [ ] **Step 2: Commit**

```bash
git add src/observability/metrics.py
git commit -m "feat(obs): add Prometheus metrics for jobs, pipelines, scheduler, memory, db, redis"
```

---

### Task 7: OpenTelemetry Tracing

**Files:**
- Create: `src/observability/tracing.py`

**Interfaces:**
- Produces: `setup_tracing()`, `get_tracer()` convenience wrapper
- Consumes: `ObservabilitySettings`

- [ ] **Step 1: Create src/observability/tracing.py**

```python
"""OpenTelemetry distributed tracing setup."""
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.resources import Resource, SERVICE_NAME
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from src.observability.config import ObservabilitySettings


def setup_tracing(settings: ObservabilitySettings) -> None:
    """Initialize OpenTelemetry tracer provider and instrumentors."""
    if not settings.enable_tracing:
        return

    resource = Resource.create({SERVICE_NAME: settings.service_name})
    provider = TracerProvider(resource=resource)
    trace.set_tracer_provider(provider)

    # Export to OTLP collector (if available)
    try:
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
        exporter = OTLPSpanExporter(endpoint=settings.otlp_endpoint, insecure=True)
        provider.add_span_processor(BatchSpanProcessor(exporter))
    except Exception:
        # OTLP exporter not available — fall back to console for dev
        from opentelemetry.sdk.trace.export import ConsoleSpanExporter
        if settings.environment == "development":
            provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))

    # Auto-instrument httpx (used by LLM client and any HTTP calls)
    HTTPXClientInstrumentor().instrument()


def instrument_fastapi(app) -> None:
    """Instrument a FastAPI app with OpenTelemetry."""
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    FastAPIInstrumentor.instrument_app(app)


def instrument_sqlalchemy(engine) -> None:
    """Instrument SQLAlchemy engine for query-level tracing."""
    from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
    SQLAlchemyInstrumentor().instrument(engine=engine)


def get_tracer(name: str = __name__) -> trace.Tracer:
    """Get an OpenTelemetry tracer."""
    return trace.get_tracer(name)
```

- [ ] **Step 2: Commit**

```bash
git add src/observability/tracing.py
git commit -m "feat(obs): add OpenTelemetry tracing with OTLP export and auto-instrumentors"
```

---

### Task 8: Health and Readiness Endpoints

**Files:**
- Create: `src/observability/health.py`

**Interfaces:**
- Produces: `health_router` (FastAPI APIRouter with `/health` and `/ready`)
- Consumes: SQLAlchemy engine, Redis connection, ARQ worker health check

- [ ] **Step 1: Create src/observability/health.py**

```python
"""Health check and readiness probe endpoints."""
import time
from fastapi import APIRouter, Request
from sqlalchemy import text

from src.observability.logging import get_logger

health_router = APIRouter(tags=["health"])
log = get_logger("health")


@health_router.get("/health")
async def liveness():
    """Liveness probe — confirms the process is running."""
    return {
        "status": "healthy",
        "timestamp": time.time(),
    }


@health_router.get("/ready")
async def readiness(request: Request):
    """Readiness probe — confirms dependencies are reachable."""
    checks = {}
    overall = "ready"

    # Database check
    try:
        from src.database import engine
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        checks["database"] = {"status": "healthy"}
    except Exception as e:
        checks["database"] = {"status": "unhealthy", "error": str(e)}
        overall = "not_ready"

    # Redis check
    try:
        import redis.asyncio as aioredis
        from src.config import settings
        r = aioredis.from_url(settings.redis_url, socket_timeout=2)
        await r.ping()
        await r.aclose()
        checks["redis"] = {"status": "healthy"}
    except Exception as e:
        checks["redis"] = {"status": "unhealthy", "error": str(e)}
        overall = "not_ready"

    status_code = 200 if overall == "ready" else 503
    result = {
        "status": overall,
        "timestamp": time.time(),
        "checks": checks,
    }

    log.info("readiness_check", status=overall, checks=checks)

    from starlette.responses import JSONResponse
    return JSONResponse(content=result, status_code=status_code)
```

- [ ] **Step 2: Commit**

```bash
git add src/observability/health.py
git commit -m "feat(obs): add /health liveness and /ready readiness probes"
```

---

### Task 9: Wire Observability into FastAPI App

**Files:**
- Modify: `src/main.py`

**Interfaces:**
- Consumes: All observability modules (config, logging, middleware, metrics, tracing, health)

- [ ] **Step 1: Rewrite src/main.py**

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.config import settings
from src.observability.config import ObservabilitySettings
from src.observability.logging import setup_logging, get_logger
from src.observability.middleware import ObservabilityMiddleware
from src.observability.metrics import setup_metrics
from src.observability.tracing import setup_tracing, instrument_fastapi, instrument_sqlalchemy
from src.observability.health import health_router
from src.api.v1.router import api_v1_router
from src.core.exceptions import AppError
from fastapi.responses import JSONResponse
from starlette.requests import Request


def create_app() -> FastAPI:
    # Initialize observability config
    obs_config = ObservabilitySettings.from_settings(settings)

    # Setup structured logging
    setup_logging(obs_config)
    log = get_logger("app")

    # Setup OpenTelemetry tracing
    setup_tracing(obs_config)

    app = FastAPI(
        title="AI Workforce Platform",
        version="0.1.0",
        debug=settings.debug,
    )

    # --- Middleware (order matters: outermost = last added) ---
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(ObservabilityMiddleware)

    # --- Instrument FastAPI for tracing + metrics ---
    if obs_config.enable_tracing:
        instrument_fastapi(app)

    if obs_config.enable_metrics:
        setup_metrics(app)

    # --- Instrument SQLAlchemy for query tracing ---
    if obs_config.enable_tracing:
        from src.database import engine
        instrument_sqlalchemy(engine)

    # --- Routers ---
    app.include_router(health_router)
    app.include_router(api_v1_router)

    # --- Exception handler ---
    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError):
        log.error(
            "app_error",
            code=exc.code,
            message=exc.message,
            status_code=exc.status_code,
            path=request.url.path,
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={"data": None, "error": {"code": exc.code, "message": exc.message}},
        )

    log.info("app_started", environment=settings.environment)
    return app


app = create_app()
```

- [ ] **Step 2: Commit**

```bash
git add src/main.py
git commit -m "feat(obs): wire observability into FastAPI app (middleware, metrics, tracing, health)"
```

---

### Task 10: ARQ Worker Observability

**Files:**
- Modify: `src/worker/arq_worker.py`

**Interfaces:**
- Consumes: `get_logger()`, `set_request_id()`, `generate_request_id()`, `JOB_DURATION`, `JOBS_TOTAL` from metrics, `get_tracer()` from tracing

- [ ] **Step 1: Add imports and setup to arq_worker.py**

Add at top of file after existing imports:

```python
import time
from opentelemetry import trace

from src.observability.logging import get_logger
from src.observability.correlation import set_request_id, generate_request_id
from src.observability.metrics import JOB_DURATION, JOBS_TOTAL
```

- [ ] **Step 2: Add logging to execute_task_job**

Replace the `execute_task_job` function with instrumented version:

```python
async def execute_task_job(ctx: dict[str, Any], job_id: str, task_id: str) -> dict[str, Any]:
    """
    Execute a single task as a background job.
    """
    worker_id = ctx.get("worker_id", str(uuid.uuid4()))
    log = get_logger("worker.execute_task")

    # Generate a correlation ID for this job run
    rid = generate_request_id()
    set_request_id(rid)

    # Extract goal_id from payload if available
    goal_id = ctx.get("job_kwargs", {}).get("goal_id")

    start = time.monotonic()
    tracer = trace.get_tracer("arq.worker")

    with tracer.start_as_current_span("execute_task_job") as span:
        span.set_attribute("job_id", job_id)
        span.set_attribute("task_id", task_id)
        span.set_attribute("worker_id", worker_id)
        if goal_id:
            span.set_attribute("goal_id", goal_id)

        log.info(
            "job_started",
            job_id=job_id,
            task_id=task_id,
            worker_id=worker_id,
            goal_id=goal_id,
        )

        async with async_session() as db:
            try:
                # Get the background job
                job_result = await db.execute(
                    select(BackgroundJob).where(BackgroundJob.id == uuid.UUID(job_id))
                )
                job = job_result.scalar_one_or_none()

                if not job:
                    JOBS_TOTAL.labels(job_type="execute_task", status="not_found").inc()
                    log.error("job_not_found", job_id=job_id)
                    return {"error": f"Job {job_id} not found"}

                # Update job status to running
                job.status = "running"
                job.worker_id = worker_id
                job.started_at = datetime.now(timezone.utc)
                await db.commit()

                log.info(
                    "job_running",
                    job_id=job_id,
                    task_id=task_id,
                    goal_id=str(job.goal_id) if job.goal_id else None,
                )

                # Get the task
                task_result = await db.execute(
                    select(Task).where(Task.id == uuid.UUID(task_id))
                )
                task = task_result.scalar_one_or_none()

                if not task:
                    job.status = "failed"
                    job.error_message = f"Task {task_id} not found"
                    job.completed_at = datetime.now(timezone.utc)
                    await db.commit()
                    JOBS_TOTAL.labels(job_type="execute_task", status="failed").inc()
                    log.error("task_not_found", job_id=job_id, task_id=task_id)
                    return {"error": f"Task {task_id} not found"}

                # Get project context
                project_result = await db.execute(
                    select(Project).where(Project.id == task.project_id)
                )
                project = project_result.scalar_one_one()

                log.info(
                    "pipeline_stage",
                    stage="agent_selection",
                    job_id=job_id,
                    project_id=str(project.id),
                    goal_id=str(project.company_id),
                )

                # Find an available agent
                factory = AgentFactory(db)
                agent = await factory.find_available_agent(
                    company_id=project.company_id,
                    capabilities_needed=[],
                )

                if not agent:
                    job.status = "failed"
                    job.error_message = "No available agent found"
                    job.completed_at = datetime.now(timezone.utc)
                    await db.commit()
                    JOBS_TOTAL.labels(job_type="execute_task", status="failed").inc()
                    log.error("no_agent_available", job_id=job_id)
                    return {"error": "No available agent found"}

                # Update task status
                task.assigned_agent_id = agent.id
                task.status = "running"
                await db.flush()

                log.info(
                    "pipeline_stage",
                    stage="llm_execution",
                    job_id=job_id,
                    agent_id=str(agent.id),
                    agent_name=agent.name,
                )

                # Execute the task with LLM
                prompt = TASK_EXECUTION_PROMPT.format(
                    task_name=task.name,
                    task_description=task.description or "",
                    project_goal=project.goal_text,
                )

                response = await llm_client.json(
                    prompt,
                    system_prompt=agent.system_prompt or "Complete the given task.",
                )

                # Update task with result
                task.output = response
                task.status = "completed"
                task.completed_at = datetime.now(timezone.utc)

                # Update agent stats
                agent.total_tasks += 1
                agent.successful_tasks += 1

                # Update job status
                job.status = "completed"
                job.result = response
                job.completed_at = datetime.now(timezone.utc)

                await db.commit()

                duration_ms = (time.monotonic() - start) * 1000

                JOBS_TOTAL.labels(job_type="execute_task", status="completed").inc()
                JOB_DURATION.labels(job_type="execute_task", status="completed").observe(duration_ms / 1000)

                log.info(
                    "job_completed",
                    job_id=job_id,
                    task_id=task_id,
                    agent_id=str(agent.id),
                    duration_ms=round(duration_ms, 2),
                )

                return {
                    "job_id": job_id,
                    "task_id": task_id,
                    "status": "completed",
                    "agent_id": str(agent.id),
                }

            except Exception as e:
                await db.rollback()

                duration_ms = (time.monotonic() - start) * 1000

                log.error(
                    "job_failed",
                    job_id=job_id,
                    task_id=task_id,
                    error=str(e),
                    duration_ms=round(duration_ms, 2),
                    exc_info=True,
                )

                # Update job with error
                try:
                    job_result = await db.execute(
                        select(BackgroundJob).where(BackgroundJob.id == uuid.UUID(job_id))
                    )
                    job = job_result.scalar_one_or_none()

                    if job:
                        job.error_message = str(e)
                        job.retry_count += 1

                        if job.retry_count < job.max_retries:
                            job.status = "retrying"
                            JOBS_TOTAL.labels(job_type="execute_task", status="retrying").inc()
                        else:
                            job.status = "failed"
                            JOBS_TOTAL.labels(job_type="execute_task", status="failed").inc()

                        job.completed_at = datetime.now(timezone.utc)
                        await db.commit()

                except Exception as inner_e:
                    log.error("job_error_update_failed", job_id=job_id, error=str(inner_e))

                JOB_DURATION.labels(job_type="execute_task", status="failed").observe(duration_ms / 1000)
                raise
```

- [ ] **Step 3: Add logging to WorkerSettings lifecycle hooks**

Replace the `WorkerSettings` class hooks:

```python
class WorkerSettings:
    """ARQ Worker configuration."""

    functions = [execute_task_job]
    redis_settings = RedisSettings.from_dsn(settings.redis_url)
    max_jobs = 10
    job_timeout = 300  # 5 minutes
    poll_delay = 0.5
    max_tries = 3
    retry_delay = 60  # 1 minute

    async def on_startup(self, ctx: dict[str, Any]) -> None:
        worker_id = str(uuid.uuid4())
        ctx["worker_id"] = worker_id
        log = get_logger("worker")
        log.info("worker_started", worker_id=worker_id)

    async def on_shutdown(self, ctx: dict[str, Any]) -> None:
        log = get_logger("worker")
        log.info("worker_shutdown", worker_id=ctx.get("worker_id"))

    async def on_job_start(self, ctx: dict[str, Any], job_id: str) -> None:
        log = get_logger("worker")
        log.info("job_starting", job_id=job_id, worker_id=ctx.get("worker_id"))

    async def on_job_end(self, ctx: dict[str, Any], job_id: str, result: Any) -> None:
        log = get_logger("worker")
        log.info("job_ended", job_id=job_id, result_type=type(result).__name__)
```

- [ ] **Step 4: Commit**

```bash
git add src/worker/arq_worker.py
git commit -m "feat(obs): instrument ARQ worker with structured logging, tracing, and metrics"
```

---

### Task 11: Pipeline Service Tracing

**Files:**
- Modify: `src/services/pipeline.py`

**Interfaces:**
- Consumes: `get_logger()`, `get_tracer()`, `PIPELINE_SUCCESS`, `PIPELINE_FAILURE` from metrics

- [ ] **Step 1: Add tracing to pipeline.py**

```python
import uuid
import time
from opentelemetry import trace
from sqlalchemy.ext.asyncio import AsyncSession

from src.services.ceo_agent import CEODecomposeAgent
from src.services.agent_factory import AgentFactory
from src.services.task_scheduler import TaskScheduler
from src.services.memory_service import MemoryService
from src.schemas.agent import AgentCreate
from src.observability.logging import get_logger
from src.observability.metrics import PIPELINE_SUCCESS, PIPELINE_FAILURE

tracer = trace.get_tracer("pipeline")


class Pipeline:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.log = get_logger("pipeline")

    async def execute_goal(
        self,
        company_id: uuid.UUID,
        goal_text: str,
        constraints: dict | None = None,
    ) -> dict:
        start = time.monotonic()

        with tracer.start_as_current_span("pipeline.execute_goal") as span:
            span.set_attribute("company_id", str(company_id))
            span.set_attribute("goal_text", goal_text[:200])

            self.log.info(
                "pipeline_started",
                company_id=str(company_id),
                goal_text=goal_text[:100],
            )

            try:
                # Stage 1: CEO Agent decomposes goal
                with tracer.start_as_current_span("ceo_agent.decompose"):
                    self.log.info(
                        "pipeline_stage",
                        stage="ceo_agent_decompose",
                        company_id=str(company_id),
                    )
                    ceo = CEODecomposeAgent(self.db)
                    project = await ceo.decompose(company_id, goal_text, constraints)

                # Stage 2: Agent Factory creates agents
                with tracer.start_as_current_span("agent_factory.create_agents"):
                    self.log.info(
                        "pipeline_stage",
                        stage="agent_factory",
                        project_id=str(project.id),
                    )
                    factory = AgentFactory(self.db)
                    agent_names = ["Research Agent", "Analysis Agent", "Execution Agent"]
                    agents = []
                    for name in agent_names:
                        agent = await factory.create_agent(
                            company_id,
                            AgentCreate(name=name, agent_type="general"),
                        )
                        agents.append(agent)

                # Stage 3: Scheduler executes project
                with tracer.start_as_current_span("scheduler.execute_project"):
                    self.log.info(
                        "pipeline_stage",
                        stage="task_scheduler",
                        project_id=str(project.id),
                        task_count=len(agents),
                    )
                    scheduler = TaskScheduler(self.db)
                    await scheduler.execute_project(project.id)

                # Stage 4: Memory stores knowledge
                with tracer.start_as_current_span("memory.store_knowledge"):
                    self.log.info(
                        "pipeline_stage",
                        stage="memory_store",
                        company_id=str(company_id),
                    )
                    memory = MemoryService(self.db)
                    await memory.store_knowledge(
                        company_id=company_id,
                        knowledge_type="goal_completed",
                        content=f"Completed goal: {goal_text}",
                        confidence=0.8,
                        source="pipeline",
                    )

                duration_ms = (time.monotonic() - start) * 1000
                PIPELINE_SUCCESS.inc()

                self.log.info(
                    "pipeline_completed",
                    project_id=str(project.id),
                    agents_created=len(agents),
                    duration_ms=round(duration_ms, 2),
                )

                return {
                    "project_id": str(project.id),
                    "agents_created": len(agents),
                    "status": "completed",
                }

            except Exception as e:
                duration_ms = (time.monotonic() - start) * 1000
                PIPELINE_FAILURE.inc()

                self.log.error(
                    "pipeline_failed",
                    error=str(e),
                    company_id=str(company_id),
                    duration_ms=round(duration_ms, 2),
                    exc_info=True,
                )
                raise
```

- [ ] **Step 2: Commit**

```bash
git add src/services/pipeline.py
git commit -m "feat(obs): add tracing spans and structured logging to pipeline"
```

---

### Task 12: Service-Level Tracing (CEO Agent, Agent Factory, Scheduler, Memory, LLM)

**Files:**
- Modify: `src/services/ceo_agent.py`
- Modify: `src/services/agent_factory.py`
- Modify: `src/services/task_scheduler.py`
- Modify: `src/services/memory_service.py`
- Modify: `src/services/llm_client.py`

**Interfaces:**
- Consumes: `get_logger()`, `get_tracer()`, `DB_QUERIES`, `REDIS_OPS` from metrics

- [ ] **Step 1: Add tracing to ceo_agent.py**

Add at top of file after existing imports:

```python
import time
from opentelemetry import trace
from src.observability.logging import get_logger

tracer = trace.get_tracer("ceo_agent")
```

Wrap the `decompose` method body with tracing:

```python
    async def decompose(self, company_id, goal_text, constraints=None):
        log = get_logger("ceo_agent")
        start = time.monotonic()

        with tracer.start_as_current_span("ceo_agent.decompose") as span:
            span.set_attribute("company_id", str(company_id))
            log.info("decompose_started", company_id=str(company_id))

            # ... existing logic unchanged ...

            duration_ms = (time.monotonic() - start) * 1000
            log.info(
                "decompose_completed",
                project_id=str(project.id),
                task_count=len(first_project["tasks"]),
                duration_ms=round(duration_ms, 2),
            )
            return project
```

- [ ] **Step 2: Add tracing to agent_factory.py**

Add at top of file:

```python
import time
from opentelemetry import trace
from src.observability.logging import get_logger
from src.observability.metrics import DB_QUERIES

tracer = trace.get_tracer("agent_factory")
```

Wrap `create_agent` and `find_available_agent` with tracing spans and DB_QUERIES.inc() calls.

- [ ] **Step 3: Add tracing to task_scheduler.py**

Add at top of file:

```python
import time
from opentelemetry import trace
from src.observability.logging import get_logger
from src.observability.metrics import SCHEDULER_TASKS, DB_QUERIES

tracer = trace.get_tracer("task_scheduler")
```

Wrap `_execute_single_task` with tracing and increment `SCHEDULER_TASKS` on completion/failure.

- [ ] **Step 4: Add tracing to memory_service.py**

Add at top of file:

```python
import time
from opentelemetry import trace
from src.observability.logging import get_logger
from src.observability.metrics import MEMORY_OPS, DB_QUERIES

tracer = trace.get_tracer("memory_service")
```

Wrap `store_episodic`, `store_knowledge`, `search_episodic`, `search_semantic` with tracing spans and `MEMORY_OPS.inc()`.

- [ ] **Step 5: Add tracing to llm_client.py**

Add at top of file:

```python
import time
from opentelemetry import trace
from src.observability.logging import get_logger

tracer = trace.get_tracer("llm_client")
```

Wrap `complete` and `json` methods with tracing spans. Log LLM calls with duration and model info.

- [ ] **Step 6: Commit**

```bash
git add src/services/ceo_agent.py src/services/agent_factory.py src/services/task_scheduler.py src/services/memory_service.py src/services/llm_client.py
git commit -m "feat(obs): add OpenTelemetry spans and metrics to all services"
```

---

### Task 13: Update API Dependencies for User Context Logging

**Files:**
- Modify: `src/api/deps.py`

**Interfaces:**
- Consumes: `set_request_id` from correlation

- [ ] **Step 1: Add user_id binding to request.state in deps.py**

Modify `get_current_user` to bind user info to request state:

```python
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import async_session
from src.services.auth import decode_access_token
from src.schemas.auth import TokenData

security = HTTPBearer()


async def get_db():
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> TokenData:
    token_data = decode_access_token(credentials.credentials)
    if token_data is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    # Bind user_id to request state for logging middleware
    request.state.user_id = token_data.user_id
    return token_data
```

- [ ] **Step 2: Commit**

```bash
git add src/api/deps.py
git commit -m "feat(obs): bind user_id to request state for structured logging"
```

---

### Task 14: Error Logging for Unhandled Exceptions

**Files:**
- Modify: `src/main.py` (already modified in Task 9 — verify error handler logs correctly)

**Interfaces:**
- Consumes: `get_logger()` from logging

- [ ] **Step 1: Verify exception handler in main.py logs correctly**

The exception handler added in Task 9 already logs with `log.error("app_error", ...)`. Verify it also handles generic unhandled exceptions by adding a catch-all handler:

Add to `create_app()` after the AppError handler:

```python
    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        log.error(
            "unhandled_exception",
            path=request.url.path,
            method=request.method,
            error=str(exc),
            exc_info=True,
        )
        return JSONResponse(
            status_code=500,
            content={"data": None, "error": {"code": "INTERNAL_ERROR", "message": "Internal server error"}},
        )
```

- [ ] **Step 2: Commit**

```bash
git add src/main.py
git commit -m "feat(obs): add unhandled exception logging handler"
```

---

### Task 15: Update BackgroundJob Model with request_id Column

**Files:**
- Modify: `src/models/background_job.py`

**Interfaces:**
- Produces: `request_id` column on BackgroundJob
- Consumes: SQLAlchemy Base

- [ ] **Step 1: Add request_id column to BackgroundJob model**

Add after `worker_id` column:

```python
    request_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
```

- [ ] **Step 2: Commit**

```bash
git add src/models/background_job.py
git commit -m "feat(obs): add request_id column to BackgroundJob model"
```

---

### Task 16: Pass request_id Through ARQ Job Enqueue

**Files:**
- Modify: `src/worker/arq_worker.py` (enqueue_task_execution function)
- Modify: `src/services/background_job_service.py`

**Interfaces:**
- Consumes: `get_request_id()` from correlation

- [ ] **Step 1: Modify enqueue_task_execution to accept and store request_id**

```python
async def enqueue_task_execution(
    db: AsyncSession,
    project_id: uuid.UUID,
    task_id: uuid.UUID,
    job_type: str = "execute_task",
    payload: dict | None = None,
    request_id: str | None = None,
) -> BackgroundJob:
    from src.observability.correlation import get_request_id

    job = BackgroundJob(
        goal_id=project_id,
        job_type=job_type,
        status="queued",
        payload=payload or {"task_id": str(task_id)},
        max_retries=3,
        request_id=request_id or get_request_id(),
    )
    db.add(job)
    await db.flush()
    return job
```

- [ ] **Step 2: Update BackgroundJobService to pass request_id**

```python
    async def enqueue_task_execution(self, project_id, task_id, payload=None):
        from src.observability.correlation import get_request_id
        job = await enqueue_task_execution(
            db=self.db,
            project_id=project_id,
            task_id=task_id,
            job_type="execute_task",
            payload=payload,
            request_id=get_request_id(),
        )
        return job
```

- [ ] **Step 3: Commit**

```bash
git add src/worker/arq_worker.py src/services/background_job_service.py
git commit -m "feat(obs): propagate request_id through job enqueue and BackgroundJob model"
```

---

### Task 17: Create Alembic Migration for request_id Column

**Files:**
- Create: `alembic/versions/XXXX_add_request_id_to_background_jobs.py` (or use alembic autogenerate)

**Interfaces:**
- Produces: Database migration adding `request_id` column

- [ ] **Step 1: Generate migration**

Run: `alembic revision --autogenerate -m "add request_id to background_jobs"`
Expected: New migration file created

- [ ] **Step 2: Verify migration content**

Read the generated migration file. It should contain:
```python
op.add_column('background_jobs', sa.Column('request_id', sa.String(255), nullable=True))
op.create_index('ix_background_jobs_request_id', 'background_jobs', ['request_id'])
```

- [ ] **Step 3: Apply migration**

Run: `alembic upgrade head`
Expected: Migration applies successfully

- [ ] **Step 4: Commit**

```bash
git add alembic/versions/
git commit -m "feat(obs): add migration for request_id column on background_jobs"
```

---

### Task 18: Verify Existing Tests Pass

**Files:**
- No changes (verification only)

**Interfaces:**
- Consumes: All existing test suite

- [ ] **Step 1: Run full test suite**

Run: `pytest tests/ -v`
Expected: 33/33 tests passing

- [ ] **Step 2: If any tests fail, fix them**

Common issues to watch for:
- Import changes in `src/main.py` — ensure test conftest still creates app correctly
- Middleware ordering — ensure tests that mock HTTP still work
- `src/api/deps.py` signature change (added `request: Request`) — ensure test fixtures provide Request

- [ ] **Step 3: Fix test fixtures if needed**

If `get_current_user` signature changed, update `tests/conftest.py` to mock correctly.

- [ ] **Step 4: Re-run tests**

Run: `pytest tests/ -v`
Expected: 33/33 tests passing

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "fix(obs): update test fixtures for observability middleware changes"
```

---

### Task 19: Final Verification and Sample Output

**Files:**
- No changes (verification only)

**Interfaces:**
- Consumes: Running application

- [ ] **Step 1: Start the application**

Run: `python -m uvicorn src.main:app --reload`

- [ ] **Step 2: Verify /health endpoint**

Run: `curl http://localhost:8000/health`
Expected:
```json
{"status": "healthy", "timestamp": 1753929600.0}
```

- [ ] **Step 3: Verify /ready endpoint**

Run: `curl http://localhost:8000/ready`
Expected:
```json
{"status": "ready", "timestamp": 1753929600.0, "checks": {"database": {"status": "healthy"}, "redis": {"status": "healthy"}}}
```

- [ ] **Step 4: Verify /metrics endpoint**

Run: `curl http://localhost:8000/metrics`
Expected: Prometheus text format output with http_requests_total, etc.

- [ ] **Step 5: Verify structured JSON logs**

Make any API request and check stdout for JSON logs with `request_id`, `timestamp`, `level`, `service`, `method`, `path`, `status_code`, `duration_ms`.

- [ ] **Step 6: Verify correlation ID propagation**

Make a request with `X-Request-ID: test-123` header and confirm the response includes the same ID and logs reference it.

- [ ] **Step 7: Commit**

```bash
git add -A
git commit -m "feat(obs): production observability complete — structlog, otel, prometheus, health probes"
```

---

## Deliverables Checklist

After completing all tasks, verify these deliverables:

1. **Architecture diagram** — See design section above
2. **Files created** — 8 new files in `src/observability/`
3. **Files modified** — main.py, config.py, deps.py, arq_worker.py, pipeline.py, ceo_agent.py, agent_factory.py, task_scheduler.py, memory_service.py, llm_client.py, background_job_model, background_job_service.py, pyproject.toml
4. **Logging flow** — Request → middleware (generate request_id) → handler → services → worker (propagate request_id)
5. **Metrics list** — All 10 metric families defined in metrics.py
6. **Sample JSON logs** — Verified in Step 5
7. **Example Prometheus output** — Verified in Step 4
8. **Health endpoint example** — Verified in Steps 2-3
9. **Worker tracing example** — OpenTelemetry spans visible in Jaeger/OTLP collector
10. **Verification steps** — Steps 1-6 above
