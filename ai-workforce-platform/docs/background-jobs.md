# ARQ Background Worker System

## Overview

This document describes the implementation of the ARQ background worker system for the AI Workforce Platform. The system provides durable, queryable background job processing with proper error handling and retry logic.

## Architecture

### Components

1. **BackgroundJob Model** (`src/models/background_job.py`)
   - Database model for tracking background jobs
   - Stores job status, results, errors, and metadata
   - Indexed for efficient querying

2. **ARQ Worker** (`src/worker/arq_worker.py`)
   - Async Redis-based job queue using ARQ
   - Handles task execution with LLM integration
   - Supports job retries and error handling

3. **BackgroundJob Service** (`src/services/background_job_service.py`)
   - Service layer for job management
   - Provides CRUD operations and statistics
   - Handles job lifecycle (enqueue, retry, cancel)

4. **API Endpoints** (`src/api/v1/jobs.py`)
   - REST API for job management
   - Endpoints for getting, retrying, and cancelling jobs
   - Project-level job statistics

## Database Schema

### BackgroundJob Table

```sql
CREATE TABLE background_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    goal_id UUID NOT NULL REFERENCES projects(id),
    job_type VARCHAR(100) NOT NULL,
    status VARCHAR(50) DEFAULT 'queued' NOT NULL,
    payload JSON,
    result JSON,
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    worker_id VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes
CREATE INDEX ix_background_jobs_status ON background_jobs(status);
CREATE INDEX ix_background_jobs_goal_id ON background_jobs(goal_id);
CREATE INDEX ix_background_jobs_created_at ON background_jobs(created_at);
CREATE INDEX ix_background_jobs_job_type ON background_jobs(job_type);
```

### Job Status Flow

```
queued → running → completed
                  → failed → retrying → queued
                  → cancelled
```

## API Endpoints

### Get Job by ID
```
GET /api/v1/jobs/{job_id}
```

### Get Project Jobs
```
GET /api/v1/jobs/project/{project_id}
Query Parameters:
  - status: Filter by status
  - limit: Max jobs to return (default: 50)
  - offset: Offset for pagination
```

### Get Project Job Stats
```
GET /api/v1/jobs/project/{project_id}/stats
```

### Retry Job
```
POST /api/v1/jobs/{job_id}/retry
```

### Cancel Job
```
POST /api/v1/jobs/{job_id}/cancel
```

### Cleanup Old Jobs
```
DELETE /api/v1/jobs/cleanup
Query Parameters:
  - days: Number of days to keep (default: 30)
```

## Worker Configuration

### WorkerSettings Class

```python
class WorkerSettings:
    functions = [execute_task_job]
    redis_settings = RedisSettings.from_dsn(settings.redis_url)
    max_jobs = 10
    job_timeout = 300  # 5 minutes
    poll_delay = 0.5
    max_tries = 3
    retry_delay = 60  # 1 minute
```

### Running the Worker

```bash
# Using Python script
python -m src.worker.run_worker

# Using ARQ command
arq src.worker.arq_worker.WorkerSettings
```

## Usage Examples

### Enqueue a Task Execution

```python
from src.services.background_job_service import BackgroundJobService
import uuid

async def enqueue_task(db, project_id, task_id):
    service = BackgroundJobService(db)
    job = await service.enqueue_task_execution(
        project_id=project_id,
        task_id=task_id,
    )
    return job
```

### Get Job Statistics

```python
async def get_stats(db, project_id):
    service = BackgroundJobService(db)
    stats = await service.get_job_stats(project_id)
    return stats
    # Returns: {
    #     "total_jobs": 10,
    #     "by_status": {
    #         "queued": 2,
    #         "running": 1,
    #         "completed": 5,
    #         "failed": 1,
    #         "retrying": 1
    #     },
    #     "avg_duration_seconds": 45.2
    # }
```

## Error Handling

### Job Execution Errors

1. **LLM API Failures**: Jobs retry with exponential backoff
2. **Agent Unavailable**: Jobs fail with descriptive error messages
3. **Database Errors**: Jobs are marked as failed and logged

### Retry Logic

- Default max retries: 3
- Retry delay: 60 seconds
- Exponential backoff supported
- Manual retry via API endpoint

## Monitoring and Observability

### Job Metrics

- Total jobs by status
- Average execution duration
- Success/failure rates
- Worker utilization

### Logging

- Job start/end events
- Error messages and stack traces
- Worker ID tracking for distributed systems

## Integration with Existing System

### Project Relationship

The `BackgroundJob` model has a foreign key to the `projects` table, linking jobs to specific projects/goals. This allows:

- Project-level job tracking
- Aggregated statistics per project
- Cleanup of old jobs per project

### Task Execution Flow

1. API enqueues job via `BackgroundJobService`
2. ARQ worker picks up job from Redis
3. Worker executes task with LLM
4. Results stored in job and task records
5. Job status updated to completed/failed

## Testing

### Unit Tests

- `tests/test_services/test_background_job_service.py`
- `tests/test_api/test_jobs.py`

### Test Coverage

- Job CRUD operations
- Status transitions
- Error handling
- API endpoint responses

## Deployment

### Prerequisites

1. Redis server running
2. PostgreSQL database
3. ARQ package installed

### Environment Variables

```bash
DATABASE_URL=postgresql+asyncpg://user:pass@localhost/db
REDIS_URL=redis://localhost:6379/0
```

### Docker

The worker can be deployed as a separate container:

```dockerfile
FROM python:3.12-slim

WORKDIR /app
COPY . .
RUN pip install -e .

CMD ["arq", "src.worker.arq_worker.WorkerSettings"]
```

## Future Enhancements

1. **Job Prioritization**: Add priority levels for job ordering
2. **Scheduled Jobs**: Cron-based job scheduling
3. **Job Dependencies**: Chain jobs with dependencies
4. **Resource Limits**: CPU/memory limits per job
5. **Webhooks**: Job completion notifications
6. **Admin Dashboard**: Visual job monitoring interface
