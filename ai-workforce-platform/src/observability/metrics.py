"""Prometheus metrics for HTTP, background jobs, pipelines, and infrastructure."""
from prometheus_client import Counter, Histogram, Info
from prometheus_fastapi_instrumentator import Instrumentator

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
