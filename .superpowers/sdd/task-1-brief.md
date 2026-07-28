# Task 1: Project Scaffold + Docker Compose Infrastructure

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

## Steps

### Step 1: Create root project files

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

### Step 2: Create Docker Compose infrastructure file

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

### Step 3: Create full Docker Compose file

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

### Step 4: Create Makefile

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

### Step 5: Verify infrastructure starts

Run: `docker compose -f docker-compose.infra.yml up -d`
Expected: All services start without errors.
Run: `docker compose -f docker-compose.infra.yml ps`
Expected: 7 services showing "Up" or "healthy".

## Global Constraints

- All Python packages use `pyproject.toml` (hatchling), no `setup.py`
- Every Python app/package has `src/` layout
- No hardcoded configuration — everything via YAML + env vars
- Every Docker Compose service must be independently scalable
- Logging goes to stdout/stderr
