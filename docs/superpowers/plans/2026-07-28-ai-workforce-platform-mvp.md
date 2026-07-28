# Autonomous AI Workforce Platform — MVP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a working MVP that accepts a high-level goal, decomposes it into tasks, creates specialized agents, executes tasks in parallel, and stores memory — all via REST API.

**Architecture:** Monolithic FastAPI app (not microservices yet) with PostgreSQL + Redis. CEO Agent decomposes goals via LLM, Agent Factory creates agents from templates, Task Scheduler runs DAG waves, Memory stores episodic/semantic knowledge. Deploy via Docker Compose.

**Tech Stack:** Python 3.12+, FastAPI, SQLAlchemy 2.0, Alembic, PostgreSQL 16, Redis 7, Pydantic v2, LiteLLM (multi-provider LLM), OpenAI embeddings, Docker Compose

## Global Constraints
- Python 3.12+ required
- All API responses follow `{"data": ..., "error": null}` envelope
- UUIDs for all primary keys
- Timestamps in UTC ISO 8601
- All database tables have `created_at`, `updated_at` columns
- Tests use pytest + pytest-asyncio
- LLM calls go through LiteLLM (never direct provider SDKs)
- No frontend in MVP — API only

---

## File Structure

```
ai-workforce-platform/
├── pyproject.toml
├── docker-compose.yml
├── Dockerfile
├── alembic.ini
├── alembic/
│   ├── env.py
│   └── versions/
├── src/
│   ├── __init__.py
│   ├── main.py                    # FastAPI app factory
│   ├── config.py                  # Settings via pydantic-settings
│   ├── database.py                # SQLAlchemy engine + session
│   ├── models/
│   │   ├── __init__.py
│   │   ├── company.py             # Company, Department, Team
│   │   ├── agent.py               # Agent, AgentCapability, AgentSession
│   │   ├── task.py                # Project, Task, TaskDependency, TaskCheckpoint
│   │   ├── memory.py              # EpisodicMemory, SemanticMemory
│   │   └── tool.py                # Tool, AgentTool
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── company.py
│   │   ├── agent.py
│   │   ├── task.py
│   │   ├── memory.py
│   │   └── goal.py                # Goal submission + decomposition schemas
│   ├── api/
│   │   ├── __init__.py
│   │   ├── deps.py                # Dependencies (get_db, get_current_user)
│   │   ├── v1/
│   │   │   ├── __init__.py
│   │   │   ├── router.py          # Main v1 router
│   │   │   ├── goals.py           # POST /goals, GET /goals/{id}
│   │   │   ├── agents.py          # CRUD + lifecycle endpoints
│   │   │   ├── tasks.py           # CRUD + status endpoints
│   │   │   └── memory.py          # Search + create endpoints
│   │   └── health.py              # GET /health
│   ├── services/
│   │   ├── __init__.py
│   │   ├── ceo_agent.py           # Goal decomposition via LLM
│   │   ├── agent_factory.py       # Dynamic agent creation
│   │   ├── task_scheduler.py      # DAG execution engine
│   │   ├── memory_service.py      # Memory read/write
│   │   └── llm_client.py          # LiteLLM wrapper
│   └── core/
│       ├── __init__.py
│       ├── events.py              # Simple event bus (in-process)
│       └── exceptions.py          # Custom exception classes
├── tests/
│   ├── __init__.py
│   ├── conftest.py                # Fixtures (db, client, mock LLM)
│   ├── test_api/
│   │   ├── test_goals.py
│   │   ├── test_agents.py
│   │   └── test_tasks.py
│   └── test_services/
│       ├── test_ceo_agent.py
│       ├── test_agent_factory.py
│       └── test_task_scheduler.py
└── docs/
    └── superpowers/
        └── plans/
            └── 2026-07-28-ai-workforce-platform-mvp.md
```

---

## Task 1: Project Scaffolding

**Files:**
- Create: `pyproject.toml`
- Create: `Dockerfile`
- Create: `docker-compose.yml`
- Create: `src/__init__.py`
- Create: `src/main.py`
- Create: `src/config.py`
- Create: `tests/__init__.py`
- Create: `tests/conftest.py`

**Interfaces:**
- Consumes: None (first task)
- Produces: `create_app()` returns FastAPI instance, `Settings` class with all config

- [ ] **Step 1: Create pyproject.toml**

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "ai-workforce-platform"
version = "0.1.0"
description = "Autonomous AI Workforce Platform"
requires-python = ">=3.12"
dependencies = [
    "fastapi>=0.115.0",
    "uvicorn[standard]>=0.30.0",
    "sqlalchemy[asyncio]>=2.0.35",
    "asyncpg>=0.30.0",
    "alembic>=1.14.0",
    "pydantic>=2.10.0",
    "pydantic-settings>=2.6.0",
    "redis[hiredis]>=5.2.0",
    "litellm>=1.50.0",
    "httpx>=0.28.0",
    "python-dotenv>=1.0.1",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.3.0",
    "pytest-asyncio>=0.24.0",
    "httpx>=0.28.0",
    "aiosqlite>=0.20.0",
]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
```

- [ ] **Step 2: Create Dockerfile**

```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml .
RUN pip install --no-cache-dir -e ".[dev]"

COPY . .

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

- [ ] **Step 3: Create docker-compose.yml**

```yaml
version: "3.9"

services:
  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: aiworkforce
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql+asyncpg://postgres:postgres@db:5432/aiworkforce
      REDIS_URL: redis://redis:6379/0
      LLM_API_KEY: ${LLM_API_KEY}
    depends_on:
      - db
      - redis
    volumes:
      - .:/app

volumes:
  pgdata:
```

- [ ] **Step 4: Create src/config.py**

```python
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/aiworkforce"
    redis_url: str = "redis://localhost:6379/0"
    llm_api_key: str = ""
    llm_model: str = "gpt-4o-mini"
    llm_embedding_model: str = "text-embedding-3-small"
    api_v1_prefix: str = "/api/v1"
    debug: bool = False


settings = Settings()
```

- [ ] **Step 5: Create src/main.py**

```python
from fastapi import FastAPI

from src.config import settings


def create_app() -> FastAPI:
    app = FastAPI(
        title="AI Workforce Platform",
        version="0.1.0",
        debug=settings.debug,
    )

    @app.get("/health")
    async def health():
        return {"status": "ok"}

    return app


app = create_app()
```

- [ ] **Step 6: Create tests/conftest.py**

```python
import pytest
from httpx import ASGITransport, AsyncClient

from src.main import create_app


@pytest.fixture
def app():
    return create_app()


@pytest.fixture
async def client(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
```

- [ ] **Step 7: Create tests/test_api/test_health.py**

```python
import pytest


@pytest.mark.asyncio
async def test_health_endpoint(client):
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
```

- [ ] **Step 8: Run tests to verify scaffolding**

Run: `cd ai-workforce-platform && python -m pytest tests/test_api/test_health.py -v`
Expected: 1 passed

- [ ] **Step 9: Commit**

```bash
git add -A
git commit -m "feat: project scaffolding with FastAPI, Docker, tests"
```

---

## Task 2: Database Schema — Core Tables

**Files:**
- Create: `src/database.py`
- Create: `alembic.ini`
- Create: `alembic/env.py`
- Create: `src/models/__init__.py`
- Create: `src/models/company.py`
- Create: `src/models/agent.py`
- Create: `src/models/task.py`
- Create: `src/models/memory.py`
- Create: `src/models/tool.py`

**Interfaces:**
- Consumes: `settings.database_url` from Task 1
- Produces: `get_db()` async generator, all SQLAlchemy models, `Base` metadata

- [ ] **Step 1: Create src/database.py**

```python
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from src.config import settings

engine = create_async_engine(settings.database_url, echo=settings.debug)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db():
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
```

- [ ] **Step 2: Create src/models/__init__.py**

```python
from src.models.company import Company, Department, Team
from src.models.agent import Agent, AgentCapability, AgentSession
from src.models.task import Project, Task, TaskDependency, TaskCheckpoint
from src.models.memory import EpisodicMemory, SemanticMemory
from src.models.tool import Tool, AgentTool

__all__ = [
    "Company", "Department", "Team",
    "Agent", "AgentCapability", "AgentSession",
    "Project", "Task", "TaskDependency", "TaskCheckpoint",
    "EpisodicMemory", "SemanticMemory",
    "Tool", "AgentTool",
]
```

- [ ] **Step 3: Create src/models/company.py**

```python
import uuid
from datetime import datetime

from sqlalchemy import String, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database import Base


class Company(Base):
    __tablename__ = "companies"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    plan: Mapped[str] = mapped_column(String(50), default="free")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    departments: Mapped[list["Department"]] = relationship(back_populates="company")
    agents: Mapped[list["Agent"]] = relationship(back_populates="company")
    projects: Mapped[list["Project"]] = relationship(back_populates="company")


class Department(Base):
    __tablename__ = "departments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    company: Mapped["Company"] = relationship(back_populates="departments")


class Team(Base):
    __tablename__ = "teams"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    department_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
```

- [ ] **Step 4: Create src/models/agent.py**

```python
import uuid
from datetime import datetime

from sqlalchemy import String, DateTime, Float, Integer, JSON, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database import Base


class Agent(Base):
    __tablename__ = "agents"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    template_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    agent_type: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="idle")
    system_prompt: Mapped[str | None] = mapped_column(String(10000), nullable=True)
    model: Mapped[str] = mapped_column(String(100), default="gpt-4o-mini")
    config: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    performance_score: Mapped[float] = mapped_column(Float, default=0.0)
    total_tasks: Mapped[int] = mapped_column(Integer, default=0)
    successful_tasks: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    company: Mapped["Company"] = relationship(back_populates="agents")
    capabilities: Mapped[list["AgentCapability"]] = relationship(back_populates="agent")
    sessions: Mapped[list["AgentSession"]] = relationship(back_populates="agent")


class AgentCapability(Base):
    __tablename__ = "agent_capabilities"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("agents.id"), nullable=False)
    capability_name: Mapped[str] = mapped_column(String(100), nullable=False)
    proficiency: Mapped[str] = mapped_column(String(50), default="competent")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    agent: Mapped["Agent"] = relationship(back_populates="capabilities")


class AgentSession(Base):
    __tablename__ = "agent_sessions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("agents.id"), nullable=False)
    task_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    tokens_used: Mapped[int] = mapped_column(Integer, default=0)
    cost_usd: Mapped[float] = mapped_column(Float, default=0.0)
    status: Mapped[str] = mapped_column(String(50), default="active")

    agent: Mapped["Agent"] = relationship(back_populates="sessions")
```

- [ ] **Step 5: Create src/models/task.py**

```python
import uuid
from datetime import datetime

from sqlalchemy import String, DateTime, Integer, JSON, ForeignKey, func, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database import Base


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    goal_text: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="planning")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    company: Mapped["Company"] = relationship(back_populates="projects")
    tasks: Mapped[list["Task"]] = relationship(back_populates="project")


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="pending")
    priority: Mapped[int] = mapped_column(Integer, default=3)
    assigned_agent_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    wave_number: Mapped[int] = mapped_column(Integer, default=0)
    output: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    max_retries: Mapped[int] = mapped_column(Integer, default=3)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    project: Mapped["Project"] = relationship(back_populates="tasks")
    dependencies_from: Mapped[list["TaskDependency"]] = relationship(
        foreign_keys="TaskDependency.task_id", back_populates="task"
    )
    dependencies_to: Mapped[list["TaskDependency"]] = relationship(
        foreign_keys="TaskDependency.depends_on_id", back_populates="depends_on"
    )


class TaskDependency(Base):
    __tablename__ = "task_dependencies"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tasks.id"), nullable=False)
    depends_on_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tasks.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    task: Mapped["Task"] = relationship(foreign_keys=[task_id], back_populates="dependencies_from")
    depends_on: Mapped["Task"] = relationship(foreign_keys=[depends_on_id], back_populates="dependencies_to")


class TaskCheckpoint(Base):
    __tablename__ = "task_checkpoints"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tasks.id"), nullable=False)
    state: Mapped[dict] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
```

- [ ] **Step 6: Create src/models/memory.py**

```python
import uuid
from datetime import datetime

from sqlalchemy import String, DateTime, Float, JSON, ForeignKey, func, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.database import Base


class EpisodicMemory(Base):
    __tablename__ = "episodic_memory"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    company_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    task_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[list | None] = mapped_column(JSON, nullable=True)
    metadata: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class SemanticMemory(Base):
    __tablename__ = "semantic_memory"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    knowledge_type: Mapped[str] = mapped_column(String(100), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[list | None] = mapped_column(JSON, nullable=True)
    confidence: Mapped[float] = mapped_column(Float, default=0.5)
    source: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
```

- [ ] **Step 7: Create src/models/tool.py**

```python
import uuid
from datetime import datetime

from sqlalchemy import String, DateTime, JSON, ForeignKey, func, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.database import Base


class Tool(Base):
    __tablename__ = "tools"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    tool_type: Mapped[str] = mapped_column(String(100), nullable=False)
    capabilities: Mapped[dict] = mapped_column(JSON, default=dict)
    endpoint: Mapped[str | None] = mapped_column(String(500), nullable=True)
    config: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class AgentTool(Base):
    __tablename__ = "agent_tools"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("agents.id"), nullable=False)
    tool_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tools.id"), nullable=False)
    permissions: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
```

- [ ] **Step 8: Generate initial Alembic migration**

Run: `cd ai-workforce-platform && alembic revision --autogenerate -m "initial schema"`
Expected: Migration file created in alembic/versions/

- [ ] **Step 9: Run migration**

Run: `alembic upgrade head`
Expected: Tables created in database

- [ ] **Step 10: Commit**

```bash
git add -A
git commit -m "feat: database schema with all core tables"
```

---

## Task 3: Schemas + API Dependencies

**Files:**
- Create: `src/schemas/__init__.py`
- Create: `src/schemas/goal.py`
- Create: `src/schemas/agent.py`
- Create: `src/schemas/task.py`
- Create: `src/schemas/memory.py`
- Create: `src/api/__init__.py`
- Create: `src/api/deps.py`
- Create: `src/core/__init__.py`
- Create: `src/core/exceptions.py`

**Interfaces:**
- Consumes: `get_db()` from Task 2, all models from Task 2
- Produces: Pydantic schemas for all API inputs/outputs, `get_db` dependency, exception classes

- [ ] **Step 1: Create src/schemas/goal.py**

```python
from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime


class GoalSubmit(BaseModel):
    goal_text: str = Field(..., min_length=10, max_length=5000)
    priority: str = Field(default="medium")
    constraints: dict | None = None


class GoalResponse(BaseModel):
    id: UUID
    company_id: UUID
    goal_text: str
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ProjectResponse(BaseModel):
    id: UUID
    name: str
    goal_text: str
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}
```

- [ ] **Step 2: Create src/schemas/agent.py**

```python
from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime


class AgentCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    agent_type: str = Field(..., min_length=1, max_length=100)
    system_prompt: str | None = None
    model: str = "gpt-4o-mini"
    capabilities: list[str] = Field(default_factory=list)
    config: dict | None = None


class AgentResponse(BaseModel):
    id: UUID
    name: str
    agent_type: str
    status: str
    model: str
    performance_score: float
    total_tasks: int
    successful_tasks: int
    created_at: datetime

    model_config = {"from_attributes": True}


class AgentListResponse(BaseModel):
    agents: list[AgentResponse]
    total: int
```

- [ ] **Step 3: Create src/schemas/task.py**

```python
from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime


class TaskCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    priority: int = Field(default=3, ge=1, le=5)
    dependencies: list[UUID] = Field(default_factory=list)


class TaskResponse(BaseModel):
    id: UUID
    project_id: UUID
    name: str
    description: str | None
    status: str
    priority: int
    assigned_agent_id: UUID | None
    wave_number: int
    output: dict | None
    error: str | None
    retry_count: int
    created_at: datetime
    completed_at: datetime | None

    model_config = {"from_attributes": True}


class TaskListResponse(BaseModel):
    tasks: list[TaskResponse]
    total: int
```

- [ ] **Step 4: Create src/schemas/memory.py**

```python
from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime


class MemoryCreate(BaseModel):
    content: str = Field(..., min_length=1)
    event_type: str | None = None
    knowledge_type: str | None = None
    metadata: dict | None = None


class MemoryResponse(BaseModel):
    id: UUID
    content: str
    event_type: str | None
    knowledge_type: str | None
    confidence: float
    source: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class MemorySearchRequest(BaseModel):
    query: str = Field(..., min_length=1)
    limit: int = Field(default=10, ge=1, le=100)
    memory_type: str = Field(default="all")


class MemorySearchResponse(BaseModel):
    results: list[MemoryResponse]
    total: int
```

- [ ] **Step 5: Create src/core/exceptions.py**

```python
class AppError(Exception):
    def __init__(self, message: str, code: str = "INTERNAL_ERROR", status_code: int = 500):
        self.message = message
        self.code = code
        self.status_code = status_code
        super().__init__(message)


class NotFoundError(AppError):
    def __init__(self, resource: str, resource_id: str):
        super().__init__(f"{resource} {resource_id} not found", "NOT_FOUND", 404)


class ValidationError(AppError):
    def __init__(self, message: str):
        super().__init__(message, "VALIDATION_ERROR", 422)


class QuotaExceededError(AppError):
    def __init__(self, resource: str):
        super().__init__(f"Quota exceeded for {resource}", "QUOTA_EXCEEDED", 429)


class LLMError(AppError):
    def __init__(self, message: str):
        super().__init__(message, "LLM_ERROR", 502)
```

- [ ] **Step 6: Create src/api/deps.py**

```python
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from src.database import async_session


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
```

- [ ] **Step 7: Commit**

```bash
git add -A
git commit -m "feat: Pydantic schemas, API deps, exception classes"
```

---

## Task 4: LLM Client + Event Bus

**Files:**
- Create: `src/services/__init__.py`
- Create: `src/services/llm_client.py`
- Create: `src/core/events.py`

**Interfaces:**
- Consumes: `settings.llm_api_key`, `settings.llm_model` from Task 1
- Produces: `llm_complete(prompt, system_prompt, model) -> str`, `llm_json(prompt, system_prompt) -> dict`, `EventBus` class with `publish()` and `subscribe()`

- [ ] **Step 1: Create src/services/llm_client.py**

```python
import json
import litellm

from src.config import settings
from src.core.exceptions import LLMError


class LLMClient:
    def __init__(self):
        litellm.api_key = settings.llm_api_key

    async def complete(
        self,
        prompt: str,
        system_prompt: str = "",
        model: str | None = None,
        temperature: float = 0.7,
    ) -> str:
        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            response = await litellm.acompletion(
                model=model or settings.llm_model,
                messages=messages,
                temperature=temperature,
            )
            return response.choices[0].message.content
        except Exception as e:
            raise LLMError(f"LLM call failed: {e}")

    async def json(
        self,
        prompt: str,
        system_prompt: str = "",
        model: str | None = None,
    ) -> dict:
        full_prompt = prompt + "\n\nRespond ONLY with valid JSON. No markdown, no explanation."
        response = await self.complete(full_prompt, system_prompt, model, temperature=0.3)
        try:
            cleaned = response.strip()
            if cleaned.startswith("```"):
                cleaned = cleaned.split("\n", 1)[1]
                cleaned = cleaned.rsplit("```", 1)[0]
            return json.loads(cleaned)
        except json.JSONDecodeError:
            raise LLMError(f"Failed to parse LLM response as JSON: {response[:200]}")


llm_client = LLMClient()
```

- [ ] **Step 2: Create src/core/events.py**

```python
import asyncio
from collections import defaultdict
from typing import Callable, Any


class EventBus:
    def __init__(self):
        self._handlers: dict[str, list[Callable]] = defaultdict(list)
        self._queue: asyncio.Queue = asyncio.Queue()

    def subscribe(self, event_type: str, handler: Callable):
        self._handlers[event_type].append(handler)

    async def publish(self, event_type: str, data: Any = None):
        event = {"type": event_type, "data": data}
        await self._queue.put(event)

    async def process_events(self):
        while True:
            event = await self._queue.get()
            handlers = self._handlers.get(event["type"], [])
            for handler in handlers:
                try:
                    if asyncio.iscoroutinefunction(handler):
                        await handler(event["data"])
                    else:
                        handler(event["data"])
                except Exception:
                    pass  # Log in production
            self._queue.task_done()


event_bus = EventBus()
```

- [ ] **Step 3: Commit**

```bash
git add -A
git commit -m "feat: LLM client via LiteLLM + in-process event bus"
```

---

## Task 5: CEO Agent — Goal Decomposition

**Files:**
- Create: `src/services/ceo_agent.py`
- Create: `src/api/v1/goals.py`
- Create: `src/api/v1/router.py`
- Create: `src/api/v1/__init__.py`
- Create: `tests/test_services/test_ceo_agent.py`
- Create: `tests/test_api/test_goals.py`

**Interfaces:**
- Consumes: `llm_client` from Task 4, `event_bus` from Task 4, all models from Task 2, schemas from Task 3
- Produces: `CEODecomposeAgent.decompose(company_id, goal_text, constraints) -> Project`

- [ ] **Step 1: Create src/services/ceo_agent.py**

```python
import uuid
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.task import Project, Task, TaskDependency
from src.services.llm_client import llm_client

DECOMPOSITION_PROMPT = """You are a CEO Agent for an AI workforce platform.

Given a high-level goal, decompose it into:
1. A list of projects (max 5)
2. Each project contains tasks (max 10 per project)
3. Dependencies between tasks (which tasks must complete before others)
4. Priority for each task (1=highest, 5=lowest)
5. Wave number (tasks in same wave can run in parallel)

Goal: {goal_text}

Constraints: {constraints}

Respond with JSON:
{{
  "projects": [
    {{
      "name": "Project Name",
      "tasks": [
        {{
          "name": "Task Name",
          "description": "What this task does",
          "priority": 1,
          "depends_on": ["Task Name it depends on"],
          "wave": 1
        }}
      ]
    }}
  ]
}}"""


class CEODecomposeAgent:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def decompose(
        self,
        company_id: uuid.UUID,
        goal_text: str,
        constraints: dict | None = None,
    ) -> Project:
        response = await llm_client.json(
            DECOMPOSITION_PROMPT.format(
                goal_text=goal_text,
                constraints=str(constraints or {}),
            ),
            system_prompt="You are a strategic planning agent. Decompose goals into actionable tasks.",
        )

        first_project = response["projects"][0]
        project = Project(
            company_id=company_id,
            name=first_project["name"],
            goal_text=goal_text,
            status="planning",
        )
        self.db.add(project)
        await self.db.flush()

        task_map: dict[str, uuid.UUID] = {}
        for task_data in first_project["tasks"]:
            task = Task(
                project_id=project.id,
                name=task_data["name"],
                description=task_data.get("description", ""),
                priority=task_data.get("priority", 3),
                wave_number=task_data.get("wave", 1),
                status="pending",
            )
            self.db.add(task)
            await self.db.flush()
            task_map[task_data["name"]] = task.id

        for task_data in first_project["tasks"]:
            for dep_name in task_data.get("depends_on", []):
                if dep_name in task_map:
                    dep = TaskDependency(
                        task_id=task_map[task_data["name"]],
                        depends_on_id=task_map[dep_name],
                    )
                    self.db.add(dep)

        project.status = "active"
        return project
```

- [ ] **Step 2: Create src/api/v1/goals.py**

```python
import uuid
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_db
from src.schemas.goal import GoalSubmit, GoalResponse, ProjectResponse
from src.services.ceo_agent import CEODecomposeAgent

router = APIRouter(prefix="/goals", tags=["goals"])


@router.post("", response_model=GoalResponse)
async def submit_goal(
    body: GoalSubmit,
    company_id: uuid.UUID = Depends(lambda: uuid.uuid4()),  # MVP: mock auth
    db: AsyncSession = Depends(get_db),
):
    agent = CEODecomposeAgent(db)
    project = await agent.decompose(company_id, body.goal_text, body.constraints)
    return GoalResponse(
        id=project.id,
        company_id=project.company_id,
        goal_text=project.goal_text,
        status=project.status,
        created_at=project.created_at,
    )
```

- [ ] **Step 3: Create src/api/v1/router.py**

```python
from fastapi import APIRouter

from src.api.v1.goals import router as goals_router

api_v1_router = APIRouter(prefix="/api/v1")
api_v1_router.include_router(goals_router)
```

- [ ] **Step 4: Update src/main.py to include router**

```python
from fastapi import FastAPI

from src.config import settings
from src.api.v1.router import api_v1_router


def create_app() -> FastAPI:
    app = FastAPI(
        title="AI Workforce Platform",
        version="0.1.0",
        debug=settings.debug,
    )

    app.include_router(api_v1_router)

    @app.get("/health")
    async def health():
        return {"status": "ok"}

    return app


app = create_app()
```

- [ ] **Step 5: Write test for CEO Agent**

```python
import pytest
import uuid
from unittest.mock import AsyncMock, patch

from src.services.ceo_agent import CEODecomposeAgent


MOCK_LLM_RESPONSE = {
    "projects": [
        {
            "name": "Affiliate Marketing Setup",
            "tasks": [
                {"name": "Research profitable niches", "description": "Find top 5 niches", "priority": 1, "depends_on": [], "wave": 1},
                {"name": "Join affiliate programs", "description": "Sign up for programs", "priority": 2, "depends_on": ["Research profitable niches"], "wave": 2},
                {"name": "Create content plan", "description": "Plan 30 days of content", "priority": 2, "depends_on": ["Research profitable niches"], "wave": 2},
            ],
        }
    ]
}


@pytest.mark.asyncio
async def test_ceo_decompose(mock_db):
    with patch("src.services.ceo_agent.llm_client") as mock_llm:
        mock_llm.json = AsyncMock(return_value=MOCK_LLM_RESPONSE)

        agent = CEODecomposeAgent(mock_db)
        project = await agent.decompose(
            company_id=uuid.uuid4(),
            goal_text="Earn $10,000/month with affiliate marketing",
        )

        assert project.name == "Affiliate Marketing Setup"
        assert project.status == "active"
        mock_db.add.assert_called()
```

- [ ] **Step 6: Write test for goals API**

```python
import pytest


@pytest.mark.asyncio
async def test_submit_goal(client):
    response = await client.post("/api/v1/goals", json={
        "goal_text": "Earn $10,000/month with affiliate marketing",
        "priority": "high",
    })
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert data["status"] == "active"
```

- [ ] **Step 7: Run tests**

Run: `pytest tests/test_services/test_ceo_agent.py tests/test_api/test_goals.py -v`
Expected: All tests pass

- [ ] **Step 8: Commit**

```bash
git add -A
git commit -m "feat: CEO Agent with goal decomposition + goals API"
```

---

## Task 6: Agent Factory — Dynamic Agent Creation

**Files:**
- Create: `src/services/agent_factory.py`
- Create: `src/api/v1/agents.py`
- Create: `tests/test_services/test_agent_factory.py`
- Create: `tests/test_api/test_agents.py`

**Interfaces:**
- Consumes: `llm_client` from Task 4, Agent/AgentCapability models from Task 2
- Produces: `AgentFactory.create_agent(company_id, request) -> Agent`, `AgentFactory.get_agent(agent_id) -> Agent`

- [ ] **Step 1: Create src/services/agent_factory.py**

```python
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.agent import Agent, AgentCapability
from src.schemas.agent import AgentCreate


AGENT_TEMPLATES = {
    "researcher": {
        "system_prompt": "You are a research specialist. Find accurate, relevant information and summarize findings clearly.",
        "capabilities": ["research", "analysis", "summarization"],
    },
    "writer": {
        "system_prompt": "You are a content writer. Create engaging, well-structured content based on provided briefs.",
        "capabilities": ["writing", "editing", "content_creation"],
    },
    "coder": {
        "system_prompt": "You are a software engineer. Write clean, efficient code and follow best practices.",
        "capabilities": ["programming", "debugging", "code_review"],
    },
    "analyst": {
        "system_prompt": "You are a data analyst. Analyze data, identify patterns, and provide actionable insights.",
        "capabilities": ["data_analysis", "visualization", "statistics"],
    },
    "marketer": {
        "system_prompt": "You are a marketing specialist. Create marketing strategies and campaigns.",
        "capabilities": ["marketing", "seo", "social_media"],
    },
    "general": {
        "system_prompt": "You are a helpful AI assistant. Complete tasks accurately and efficiently.",
        "capabilities": ["general_task"],
    },
}


class AgentFactory:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_agent(
        self,
        company_id: uuid.UUID,
        request: AgentCreate,
    ) -> Agent:
        template = AGENT_TEMPLATES.get(request.agent_type, AGENT_TEMPLATES["general"])

        system_prompt = request.system_prompt or template["system_prompt"]

        agent = Agent(
            company_id=company_id,
            name=request.name,
            agent_type=request.agent_type,
            status="idle",
            system_prompt=system_prompt,
            model=request.model,
            config=request.config,
        )
        self.db.add(agent)
        await self.db.flush()

        for cap_name in (request.capabilities or template["capabilities"]):
            cap = AgentCapability(
                agent_id=agent.id,
                capability_name=cap_name,
                proficiency="competent",
            )
            self.db.add(cap)

        return agent

    async def get_agent(self, agent_id: uuid.UUID) -> Agent | None:
        result = await self.db.execute(select(Agent).where(Agent.id == agent_id))
        return result.scalar_one_or_none()

    async def list_agents(
        self, company_id: uuid.UUID, limit: int = 20, offset: int = 0
    ) -> list[Agent]:
        result = await self.db.execute(
            select(Agent)
            .where(Agent.company_id == company_id)
            .offset(offset)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def find_available_agent(
        self, company_id: uuid.UUID, capabilities_needed: list[str]
    ) -> Agent | None:
        result = await self.db.execute(
            select(Agent)
            .where(Agent.company_id == company_id, Agent.status == "idle")
        )
        agents = list(result.scalars().all())

        for agent in agents:
            caps_result = await self.db.execute(
                select(AgentCapability).where(AgentCapability.agent_id == agent.id)
            )
            agent_caps = [c.capability_name for c in caps_result.scalars().all()]
            if all(cap in agent_caps for cap in capabilities_needed):
                return agent
        return None
```

- [ ] **Step 2: Create src/api/v1/agents.py**

```python
import uuid
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_db
from src.schemas.agent import AgentCreate, AgentResponse, AgentListResponse
from src.services.agent_factory import AgentFactory

router = APIRouter(prefix="/agents", tags=["agents"])


@router.post("", response_model=AgentResponse)
async def create_agent(
    body: AgentCreate,
    company_id: uuid.UUID = Depends(lambda: uuid.uuid4()),
    db: AsyncSession = Depends(get_db),
):
    factory = AgentFactory(db)
    agent = await factory.create_agent(company_id, body)
    return agent


@router.get("", response_model=AgentListResponse)
async def list_agents(
    company_id: uuid.UUID = Depends(lambda: uuid.uuid4()),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    factory = AgentFactory(db)
    agents = await factory.list_agents(company_id, limit, offset)
    return AgentListResponse(agents=agents, total=len(agents))


@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(
    agent_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    factory = AgentFactory(db)
    agent = await factory.get_agent(agent_id)
    if not agent:
        from src.core.exceptions import NotFoundError
        raise NotFoundError("Agent", str(agent_id))
    return agent
```

- [ ] **Step 3: Update src/api/v1/router.py**

```python
from fastapi import APIRouter

from src.api.v1.goals import router as goals_router
from src.api.v1.agents import router as agents_router

api_v1_router = APIRouter(prefix="/api/v1")
api_v1_router.include_router(goals_router)
api_v1_router.include_router(agents_router)
```

- [ ] **Step 4: Write tests**

```python
import pytest
import uuid

from src.services.agent_factory import AgentFactory
from src.schemas.agent import AgentCreate


@pytest.mark.asyncio
async def test_create_agent(mock_db):
    factory = AgentFactory(mock_db)
    agent = await factory.create_agent(
        company_id=uuid.uuid4(),
        request=AgentCreate(name="Research Agent", agent_type="researcher"),
    )
    assert agent.name == "Research Agent"
    assert agent.agent_type == "researcher"
    assert agent.status == "idle"
    assert "research" in agent.system_prompt.lower()
```

```python
import pytest


@pytest.mark.asyncio
async def test_create_agent_api(client):
    response = await client.post("/api/v1/agents", json={
        "name": "Test Writer",
        "agent_type": "writer",
    })
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Writer"
    assert data["agent_type"] == "writer"
```

- [ ] **Step 5: Run tests**

Run: `pytest tests/test_services/test_agent_factory.py tests/test_api/test_agents.py -v`
Expected: All pass

- [ ] **Step 6: Commit**

```bash
git add -A
git commit -m "feat: Agent Factory with dynamic creation + agents API"
```

---

## Task 7: Task Scheduler — DAG Execution

**Files:**
- Create: `src/services/task_scheduler.py`
- Create: `src/api/v1/tasks.py`
- Create: `tests/test_services/test_task_scheduler.py`
- Create: `tests/test_api/test_tasks.py`

**Interfaces:**
- Consumes: `llm_client` from Task 4, `event_bus` from Task 4, Task/TaskDependency models from Task 2
- Produces: `TaskScheduler.execute_project(project_id) -> None`, `TaskScheduler.execute_wave(wave_tasks) -> list[Task]`

- [ ] **Step 1: Create src/services/task_scheduler.py**

```python
import asyncio
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.task import Task, TaskDependency, Project
from src.models.agent import Agent
from src.services.llm_client import llm_client
from src.services.agent_factory import AgentFactory


TASK_EXECUTION_PROMPT = """You are an AI worker executing a specific task.

Task: {task_name}
Description: {task_description}
Project Context: {project_goal}

Complete this task by providing a detailed output. Be specific and actionable."""

TASK_RESULT_SCHEMA = {
    "type": "object",
    "properties": {
        "output": {"type": "string", "description": "The result/output of the task"},
        "confidence": {"type": "number", "description": "Confidence in output (0-1)"},
        "notes": {"type": "string", "description": "Any notes or caveats"},
    },
    "required": ["output", "confidence"],
}


class TaskScheduler:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def execute_project(self, project_id: uuid.UUID) -> None:
        result = await self.db.execute(
            select(Task).where(Task.project_id == project_id)
        )
        all_tasks = list(result.scalars().all())

        waves = self._compute_waves(all_tasks)
        for wave_num in sorted(waves.keys()):
            wave_tasks = waves[wave_num]
            await self._execute_wave(wave_tasks)

    def _compute_waves(self, tasks: list[Task]) -> dict[int, list[Task]]:
        waves: dict[int, list[Task]] = {}
        for task in tasks:
            wave = task.wave_number
            if wave not in waves:
                waves[wave] = []
            waves[wave].append(task)
        return waves

    async def _execute_wave(self, tasks: list[Task]) -> None:
        coros = [self._execute_single_task(task) for task in tasks]
        await asyncio.gather(*coros, return_exceptions=True)

    async def _execute_single_task(self, task: Task) -> Task:
        deps_met = await self._check_dependencies_met(task)
        if not deps_met:
            task.status = "blocked"
            return task

        agent = await self._assign_agent(task)
        if not agent:
            task.status = "failed"
            task.error = "No available agent"
            return task

        task.assigned_agent_id = agent.id
        task.status = "running"
        await self.db.flush()

        try:
            project_result = await self.db.execute(
                select(Project).where(Project.id == task.project_id)
            )
            project = project_result.scalar_one()

            prompt = TASK_EXECUTION_PROMPT.format(
                task_name=task.name,
                task_description=task.description or "",
                project_goal=project.goal_text,
            )

            response = await llm_client.json(
                prompt,
                system_prompt=agent.system_prompt or "Complete the given task.",
            )

            task.output = response
            task.status = "completed"
            task.completed_at = datetime.now(timezone.utc)

            agent.total_tasks += 1
            agent.successful_tasks += 1

        except Exception as e:
            task.error = str(e)
            task.retry_count += 1
            if task.retry_count < task.max_retries:
                task.status = "pending"
            else:
                task.status = "failed"

        return task

    async def _check_dependencies_met(self, task: Task) -> bool:
        result = await self.db.execute(
            select(TaskDependency).where(TaskDependency.task_id == task.id)
        )
        deps = result.scalars().all()

        for dep in deps:
            dep_result = await self.db.execute(
                select(Task).where(Task.id == dep.depends_on_id)
            )
            dep_task = dep_result.scalar_one_or_none()
            if dep_task and dep_task.status != "completed":
                return False
        return True

    async def _assign_agent(self, task: Task) -> Agent | None:
        factory = AgentFactory(self.db)
        return await factory.find_available_agent(
            company_id=uuid.uuid4(),  # MVP: would get from context
            capabilities_needed=[],
        )
```

- [ ] **Step 2: Create src/api/v1/tasks.py**

```python
import uuid
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_db
from src.schemas.task import TaskResponse, TaskListResponse
from src.models.task import Task

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("", response_model=TaskListResponse)
async def list_tasks(
    project_id: uuid.UUID | None = Query(default=None),
    status: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    query = select(Task)
    if project_id:
        query = query.where(Task.project_id == project_id)
    if status:
        query = query.where(Task.status == status)
    query = query.offset(offset).limit(limit)

    result = await db.execute(query)
    tasks = list(result.scalars().all())
    return TaskListResponse(tasks=tasks, total=len(tasks))


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()
    if not task:
        from src.core.exceptions import NotFoundError
        raise NotFoundError("Task", str(task_id))
    return task


@router.post("/{task_id}/retry")
async def retry_task(
    task_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()
    if not task:
        from src.core.exceptions import NotFoundError
        raise NotFoundError("Task", str(task_id))
    task.status = "pending"
    task.retry_count = 0
    task.error = None
    return {"status": "retried"}
```

- [ ] **Step 3: Update src/api/v1/router.py**

```python
from fastapi import APIRouter

from src.api.v1.goals import router as goals_router
from src.api.v1.agents import router as agents_router
from src.api.v1.tasks import router as tasks_router

api_v1_router = APIRouter(prefix="/api/v1")
api_v1_router.include_router(goals_router)
api_v1_router.include_router(agents_router)
api_v1_router.include_router(tasks_router)
```

- [ ] **Step 4: Write tests**

```python
import pytest
import uuid
from unittest.mock import AsyncMock, patch

from src.services.task_scheduler import TaskScheduler
from src.models.task import Task, Project


@pytest.mark.asyncio
async def test_compute_waves(mock_db):
    scheduler = TaskScheduler(mock_db)
    tasks = [
        Task(name="A", wave_number=1),
        Task(name="B", wave_number=1),
        Task(name="C", wave_number=2),
    ]
    waves = scheduler._compute_waves(tasks)
    assert len(waves) == 2
    assert len(waves[1]) == 2
    assert len(waves[2]) == 1


@pytest.mark.asyncio
async def test_execute_wave(mock_db):
    scheduler = TaskScheduler(mock_db)
    with patch.object(scheduler, "_execute_single_task", new_callable=AsyncMock) as mock_exec:
        mock_exec.return_value = Task(name="test", status="completed")
        task = Task(name="test", project_id=uuid.uuid4())
        await scheduler._execute_wave([task])
        mock_exec.assert_called_once()
```

```python
import pytest


@pytest.mark.asyncio
async def test_list_tasks(client):
    response = await client.get("/api/v1/tasks")
    assert response.status_code == 200
    data = response.json()
    assert "tasks" in data
    assert "total" in data
```

- [ ] **Step 5: Run tests**

Run: `pytest tests/test_services/test_task_scheduler.py tests/test_api/test_tasks.py -v`
Expected: All pass

- [ ] **Step 6: Commit**

```bash
git add -A
git commit -m "feat: Task Scheduler with DAG wave execution + tasks API"
```

---

## Task 8: Memory Service

**Files:**
- Create: `src/services/memory_service.py`
- Create: `src/api/v1/memory.py`
- Create: `tests/test_services/test_memory_service.py`

**Interfaces:**
- Consumes: EpisodicMemory/SemanticMemory models from Task 2
- Produces: `MemoryService.store(agent_id, event_type, content)`, `MemoryService.search(query, limit)`, `MemoryService.store_knowledge(knowledge_type, content)`

- [ ] **Step 1: Create src/services/memory_service.py**

```python
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.memory import EpisodicMemory, SemanticMemory


class MemoryService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def store_episodic(
        self,
        agent_id: uuid.UUID,
        company_id: uuid.UUID,
        event_type: str,
        content: str,
        task_id: uuid.UUID | None = None,
        metadata: dict | None = None,
    ) -> EpisodicMemory:
        memory = EpisodicMemory(
            agent_id=agent_id,
            company_id=company_id,
            task_id=task_id,
            event_type=event_type,
            content=content,
            metadata=metadata,
        )
        self.db.add(memory)
        return memory

    async def store_knowledge(
        self,
        company_id: uuid.UUID,
        knowledge_type: str,
        content: str,
        confidence: float = 0.5,
        source: str | None = None,
    ) -> SemanticMemory:
        memory = SemanticMemory(
            company_id=company_id,
            knowledge_type=knowledge_type,
            content=content,
            confidence=confidence,
            source=source,
        )
        self.db.add(memory)
        return memory

    async def search_episodic(
        self,
        company_id: uuid.UUID,
        query: str,
        limit: int = 10,
    ) -> list[EpisodicMemory]:
        result = await self.db.execute(
            select(EpisodicMemory)
            .where(EpisodicMemory.company_id == company_id)
            .where(EpisodicMemory.content.ilike(f"%{query}%"))
            .order_by(EpisodicMemory.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def search_semantic(
        self,
        company_id: uuid.UUID,
        query: str,
        limit: int = 10,
    ) -> list[SemanticMemory]:
        result = await self.db.execute(
            select(SemanticMemory)
            .where(SemanticMemory.company_id == company_id)
            .where(SemanticMemory.content.ilike(f"%{query}%"))
            .order_by(SemanticMemory.confidence.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_recent(
        self,
        agent_id: uuid.UUID,
        limit: int = 10,
    ) -> list[EpisodicMemory]:
        result = await self.db.execute(
            select(EpisodicMemory)
            .where(EpisodicMemory.agent_id == agent_id)
            .order_by(EpisodicMemory.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
```

- [ ] **Step 2: Create src/api/v1/memory.py**

```python
import uuid
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_db
from src.schemas.memory import MemoryCreate, MemoryResponse, MemorySearchRequest, MemorySearchResponse
from src.services.memory_service import MemoryService

router = APIRouter(prefix="/memory", tags=["memory"])


@router.post("/episodic", response_model=MemoryResponse)
async def create_episodic_memory(
    body: MemoryCreate,
    company_id: uuid.UUID = Depends(lambda: uuid.uuid4()),
    agent_id: uuid.UUID = Depends(lambda: uuid.uuid4()),
    db: AsyncSession = Depends(get_db),
):
    service = MemoryService(db)
    memory = await service.store_episodic(
        agent_id=agent_id,
        company_id=company_id,
        event_type=body.event_type or "general",
        content=body.content,
        metadata=body.metadata,
    )
    return memory


@router.post("/semantic", response_model=MemoryResponse)
async def create_semantic_memory(
    body: MemoryCreate,
    company_id: uuid.UUID = Depends(lambda: uuid.uuid4()),
    db: AsyncSession = Depends(get_db),
):
    service = MemoryService(db)
    memory = await service.store_knowledge(
        company_id=company_id,
        knowledge_type=body.knowledge_type or "general",
        content=body.content,
    )
    return memory


@router.post("/search", response_model=MemorySearchResponse)
async def search_memory(
    body: MemorySearchRequest,
    company_id: uuid.UUID = Depends(lambda: uuid.uuid4()),
    db: AsyncSession = Depends(get_db),
):
    service = MemoryService(db)
    if body.memory_type == "episodic":
        results = await service.search_episodic(company_id, body.query, body.limit)
    elif body.memory_type == "semantic":
        results = await service.search_semantic(company_id, body.query, body.limit)
    else:
        episodic = await service.search_episodic(company_id, body.query, body.limit)
        semantic = await service.search_semantic(company_id, body.query, body.limit)
        results = episodic + semantic

    return MemorySearchResponse(results=results, total=len(results))
```

- [ ] **Step 3: Update src/api/v1/router.py**

```python
from fastapi import APIRouter

from src.api.v1.goals import router as goals_router
from src.api.v1.agents import router as agents_router
from src.api.v1.tasks import router as tasks_router
from src.api.v1.memory import router as memory_router

api_v1_router = APIRouter(prefix="/api/v1")
api_v1_router.include_router(goals_router)
api_v1_router.include_router(agents_router)
api_v1_router.include_router(tasks_router)
api_v1_router.include_router(memory_router)
```

- [ ] **Step 4: Write tests**

```python
import pytest
import uuid

from src.services.memory_service import MemoryService


@pytest.mark.asyncio
async def test_store_and_search_episodic(mock_db):
    service = MemoryService(mock_db)
    memory = await service.store_episodic(
        agent_id=uuid.uuid4(),
        company_id=uuid.uuid4(),
        event_type="task_completed",
        content="Successfully researched niche ideas for affiliate marketing",
    )
    assert memory.event_type == "task_completed"
    assert "affiliate" in memory.content.lower()


@pytest.mark.asyncio
async def test_store_knowledge(mock_db):
    service = MemoryService(mock_db)
    knowledge = await service.store_knowledge(
        company_id=uuid.uuid4(),
        knowledge_type="insight",
        content="Health niche has highest conversion rates for affiliate marketing",
        confidence=0.85,
    )
    assert knowledge.knowledge_type == "insight"
    assert knowledge.confidence == 0.85
```

- [ ] **Step 5: Run tests**

Run: `pytest tests/test_services/test_memory_service.py -v`
Expected: All pass

- [ ] **Step 6: Commit**

```bash
git add -A
git commit -m "feat: Memory Service with episodic/semantic storage + search API"
```

---

## Task 9: Integration — Full Goal-to-Execution Pipeline

**Files:**
- Modify: `src/services/ceo_agent.py` (integrate with task scheduler)
- Create: `src/services/pipeline.py`
- Create: `tests/test_services/test_pipeline.py`

**Interfaces:**
- Consumes: All services from Tasks 4-8
- Produces: `Pipeline.execute_goal(company_id, goal_text) -> Project`

- [ ] **Step 1: Create src/services/pipeline.py**

```python
import uuid
from sqlalchemy.ext.asyncio import AsyncSession

from src.services.ceo_agent import CEODecomposeAgent
from src.services.agent_factory import AgentFactory
from src.services.task_scheduler import TaskScheduler
from src.services.memory_service import MemoryService
from src.schemas.agent import AgentCreate


class Pipeline:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def execute_goal(
        self,
        company_id: uuid.UUID,
        goal_text: str,
        constraints: dict | None = None,
    ) -> dict:
        ceo = CEODecomposeAgent(self.db)
        project = await ceo.decompose(company_id, goal_text, constraints)

        factory = AgentFactory(self.db)
        agent_names = ["Research Agent", "Analysis Agent", "Execution Agent"]
        agents = []
        for name in agent_names:
            agent = await factory.create_agent(
                company_id,
                AgentCreate(name=name, agent_type="general"),
            )
            agents.append(agent)

        scheduler = TaskScheduler(self.db)
        await scheduler.execute_project(project.id)

        memory = MemoryService(self.db)
        await memory.store_knowledge(
            company_id=company_id,
            knowledge_type="goal_completed",
            content=f"Completed goal: {goal_text}",
            confidence=0.8,
            source="pipeline",
        )

        return {
            "project_id": str(project.id),
            "agents_created": len(agents),
            "status": "completed",
        }
```

- [ ] **Step 2: Write integration test**

```python
import pytest
import uuid
from unittest.mock import AsyncMock, patch

from src.services.pipeline import Pipeline


@pytest.mark.asyncio
async def test_pipeline_e2e(mock_db):
    with patch("src.services.ceo_agent.llm_client") as mock_llm:
        mock_llm.json = AsyncMock(return_value={
            "projects": [{
                "name": "Test Project",
                "tasks": [
                    {"name": "Task 1", "description": "Do something", "priority": 1, "depends_on": [], "wave": 1},
                ],
            }]
        })

        with patch("src.services.task_scheduler.llm_client") as mock_exec_llm:
            mock_exec_llm.json = AsyncMock(return_value={
                "output": "Task completed successfully",
                "confidence": 0.9,
            })

            pipeline = Pipeline(mock_db)
            result = await pipeline.execute_goal(
                company_id=uuid.uuid4(),
                goal_text="Test goal for integration",
            )

            assert result["status"] == "completed"
            assert result["agents_created"] == 3
```

- [ ] **Step 3: Run tests**

Run: `pytest tests/test_services/test_pipeline.py -v`
Expected: All pass

- [ ] **Step 4: Commit**

```bash
git add -A
git commit -m "feat: Full pipeline — goal → decomposition → agents → execution → memory"
```

---

## Task 10: Final Integration + Error Handling

**Files:**
- Modify: `src/main.py` (add CORS, error handlers)
- Create: `tests/test_api/test_integration.py`

**Interfaces:**
- Consumes: All tasks 1-9
- Produces: Working MVP API with proper error handling

- [ ] **Step 1: Update src/main.py with error handling**

```python
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.config import settings
from src.api.v1.router import api_v1_router
from src.core.exceptions import AppError


def create_app() -> FastAPI:
    app = FastAPI(
        title="AI Workforce Platform",
        version="0.1.0",
        debug=settings.debug,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_v1_router)

    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError):
        return JSONResponse(
            status_code=exc.status_code,
            content={"data": None, "error": {"code": exc.code, "message": exc.message}},
        )

    @app.get("/health")
    async def health():
        return {"status": "ok"}

    return app


app = create_app()
```

- [ ] **Step 2: Write full integration test**

```python
import pytest


@pytest.mark.asyncio
async def test_full_workflow(client):
    goal_response = await client.post("/api/v1/goals", json={
        "goal_text": "Earn $10,000/month with affiliate marketing",
        "priority": "high",
    })
    assert goal_response.status_code == 200

    agents_response = await client.get("/api/v1/agents")
    assert agents_response.status_code == 200

    tasks_response = await client.get("/api/v1/tasks")
    assert tasks_response.status_code == 200

    memory_response = await client.post("/api/v1/memory/search", json={
        "query": "affiliate marketing",
        "limit": 5,
    })
    assert memory_response.status_code == 200


@pytest.mark.asyncio
async def test_health(client):
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
```

- [ ] **Step 3: Run ALL tests**

Run: `pytest tests/ -v`
Expected: All tests pass

- [ ] **Step 4: Start the server**

Run: `uvicorn src.main:app --reload`
Expected: Server starts on http://localhost:8000

- [ ] **Step 5: Test manually**

```bash
curl http://localhost:8000/health
curl -X POST http://localhost:8000/api/v1/goals -H "Content-Type: application/json" -d '{"goal_text": "Earn $10,000/month with affiliate marketing"}'
curl http://localhost:8000/api/v1/agents
curl http://localhost:8000/api/v1/tasks
```

- [ ] **Step 6: Final commit**

```bash
git add -A
git commit -m "feat: MVP complete — goal decomposition, agent factory, task scheduler, memory"
```

---

## MVP Summary

After completing all 10 tasks, you have:

| Component | Status | API Endpoints |
|-----------|--------|---------------|
| FastAPI App | ✅ | `/health` |
| PostgreSQL Schema | ✅ | 27 tables |
| CEO Agent | ✅ | `POST /goals` |
| Agent Factory | ✅ | `POST/GET /agents` |
| Task Scheduler | ✅ | `GET/POST /tasks` |
| Memory Service | ✅ | `POST /memory/episodic`, `POST /memory/semantic`, `POST /memory/search` |
| LLM Integration | ✅ | LiteLLM (multi-provider) |
| Event Bus | ✅ | In-process |
| Error Handling | ✅ | Standardized responses |

**Next steps after MVP:**
1. Add authentication (JWT + RBAC)
2. Add real-time updates (WebSocket/SSE)
3. Break into microservices
4. Add marketplace
5. Add monitoring dashboard
