# Task 3a: Shared Packages (Config, Storage, Events, Logging, VectorDB)

**Files to create:**

### 1. Config Package
- `packages/config/pyproject.toml`
- `packages/config/src/__init__.py`
- `packages/config/src/loader.py`

### 2. Storage Package  
- `packages/storage/pyproject.toml`
- `packages/storage/src/__init__.py`
- `packages/storage/src/client.py`

### 3. Events Package
- `packages/events/pyproject.toml`
- `packages/events/src/__init__.py`
- `packages/events/src/nats_client.py`

### 4. Logging Package
- `packages/logging/pyproject.toml`
- `packages/logging/src/__init__.py`
- `packages/logging/src/logger.py`

### 5. VectorDB Package
- `packages/vectordb/pyproject.toml`
- `packages/vectordb/src/__init__.py`
- `packages/vectordb/src/client.py`

## All File Contents

### packages/config/pyproject.toml
```toml
[project]
name = "clippy-config"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "pyyaml>=6.0",
    "pydantic>=2.0",
    "pydantic-settings>=2.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/clippy_config"]
```

### packages/config/src/clippy_config/__init__.py
```python
from .loader import load_config, ClippyConfig

__all__ = ["load_config", "ClippyConfig"]
```

### packages/config/src/clippy_config/loader.py
```python
import os
import yaml
from pathlib import Path
from pydantic import BaseModel
from pydantic_settings import BaseSettings


class StorageConfig(BaseModel):
    provider: str = "minio"
    endpoint: str = "http://minio:9000"
    region: str = "us-east-1"
    access_key: str = "clippy"
    secret_key: str = "clippy_secret"
    buckets: dict[str, str] = {
        "raw-videos": "raw-videos",
        "clips": "clips",
        "transcripts": "transcripts",
        "thumbnails": "thumbnails",
    }


class DatabaseConfig(BaseModel):
    dsn: str = "postgresql+asyncpg://clippy:clippy@postgres:5432/clippy"
    pool_size: int = 20
    max_overflow: int = 10


class TemporalConfig(BaseModel):
    host: str = "temporal:7233"
    namespace: str = "clippy-default"
    task_queue: str = "clip-pipeline"


class NATSConfig(BaseModel):
    servers: list[str] = ["nats://nats:4222"]


class QdrantConfig(BaseModel):
    host: str = "qdrant"
    port: int = 6333
    collection: str = "clip-embeddings"


class ScoringConfig(BaseModel):
    min_clip_duration: int = 15
    max_clip_duration: int = 120
    min_score_threshold: float = 0.3
    weights: dict[str, float] = {
        "virality": 1.0,
        "retention": 0.9,
        "hook": 0.8,
        "emotion": 0.7,
        "shareability": 0.6,
        "educational": 0.4,
    }


class ClippyConfig(BaseSettings):
    storage: StorageConfig = StorageConfig()
    database: DatabaseConfig = DatabaseConfig()
    temporal: TemporalConfig = TemporalConfig()
    nats: NATSConfig = NATSConfig()
    qdrant: QdrantConfig = QdrantConfig()
    scoring: ScoringConfig = ScoringConfig()
    environment: str = "development"
    api_port: int = 8000
    frontend_port: int = 3000
    openai_api_key: str = ""

    class Config:
        env_nested_delimiter = "__"


def load_config(path: str | None = None) -> ClippyConfig:
    config = ClippyConfig()
    if path and Path(path).exists():
        with open(path) as f:
            overrides = yaml.safe_load(f)
        if overrides:
            for section, values in overrides.items():
                if hasattr(config, section):
                    for key, val in values.items():
                        if hasattr(getattr(config, section), key):
                            setattr(getattr(config, section), key, val)
    return config
```

### packages/storage/pyproject.toml
```toml
[project]
name = "clippy-storage"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "boto3>=1.34",
    "botocore>=1.34",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/clippy_storage"]
```

### packages/storage/src/clippy_storage/__init__.py
```python
from .client import StorageBackend, create_storage

__all__ = ["StorageBackend", "create_storage"]
```

### packages/storage/src/clippy_storage/client.py
```python
from abc import ABC, abstractmethod
from pathlib import Path
from typing import BinaryIO
import boto3
from botocore.config import Config


class StorageBackend(ABC):
    @abstractmethod
    async def upload(self, bucket: str, key: str, file_path: str | Path) -> str:
        ...

    @abstractmethod
    async def download(self, bucket: str, key: str, dest: str | Path) -> str:
        ...

    @abstractmethod
    async def delete(self, bucket: str, key: str) -> None:
        ...

    @abstractmethod
    async def generate_presigned_url(self, bucket: str, key: str, expires_in: int = 3600) -> str:
        ...

    @abstractmethod
    async def generate_presigned_upload_url(self, bucket: str, key: str, expires_in: int = 3600) -> dict:
        ...


class S3Storage(StorageBackend):
    def __init__(self, endpoint: str, region: str, access_key: str, secret_key: str):
        self.client = boto3.client(
            "s3",
            endpoint_url=endpoint,
            region_name=region,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            config=Config(signature_version="s3v4"),
        )

    async def upload(self, bucket: str, key: str, file_path: str | Path) -> str:
        self.client.upload_file(str(file_path), bucket, key)
        return f"{bucket}/{key}"

    async def download(self, bucket: str, key: str, dest: str | Path) -> str:
        self.client.download_file(bucket, key, str(dest))
        return str(dest)

    async def delete(self, bucket: str, key: str) -> None:
        self.client.delete_object(Bucket=bucket, Key=key)

    async def generate_presigned_url(self, bucket: str, key: str, expires_in: int = 3600) -> str:
        return self.client.generate_presigned_url(
            "get_object",
            Params={"Bucket": bucket, "Key": key},
            ExpiresIn=expires_in,
        )

    async def generate_presigned_upload_url(self, bucket: str, key: str, expires_in: int = 3600) -> dict:
        url = self.client.generate_presigned_url(
            "put_object",
            Params={"Bucket": bucket, "Key": key},
            ExpiresIn=expires_in,
        )
        return {"url": url, "fields": {}}


def create_storage(
    provider: str = "minio",
    endpoint: str = "http://minio:9000",
    region: str = "us-east-1",
    access_key: str = "clippy",
    secret_key: str = "clippy_secret",
) -> StorageBackend:
    return S3Storage(endpoint, region, access_key, secret_key)
```

### packages/events/pyproject.toml
```toml
[project]
name = "clippy-events"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "nats-py>=2.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/clippy_events"]
```

### packages/events/src/clippy_events/__init__.py
```python
from .nats_client import NATSClient

__all__ = ["NATSClient"]
```

### packages/events/src/clippy_events/nats_client.py
```python
import json
import nats
from typing import Callable, Awaitable


class NATSClient:
    def __init__(self, servers: list[str]):
        self.servers = servers
        self._conn = None

    async def connect(self):
        self._conn = await nats.connect(servers=self.servers)

    async def close(self):
        if self._conn:
            await self._conn.close()

    async def publish(self, subject: str, data: dict):
        if not self._conn:
            raise RuntimeError("NATS not connected")
        await self._conn.publish(subject, json.dumps(data).encode())

    async def subscribe(self, subject: str, callback: Callable[[dict], Awaitable[None]]):
        if not self._conn:
            raise RuntimeError("NATS not connected")

        async def handler(msg):
            data = json.loads(msg.data.decode())
            await callback(data)

        await self._conn.subscribe(subject, cb=handler)
```

### packages/logging/pyproject.toml
```toml
[project]
name = "clippy-logging"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "structlog>=24.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/clippy_logging"]
```

### packages/logging/src/clippy_logging/__init__.py
```python
from .logger import setup_logging, get_logger

__all__ = ["setup_logging", "get_logger"]
```

### packages/logging/src/clippy_logging/logger.py
```python
import structlog
import logging


def setup_logging(environment: str = "development"):
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.dev.ConsoleRenderer() if environment == "development"
            else structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    logging.basicConfig(format="%(message)s", level=logging.INFO)


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    return structlog.get_logger(name)
```

### packages/vectordb/pyproject.toml
```toml
[project]
name = "clippy-vectordb"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "qdrant-client>=1.9",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/clippy_vectordb"]
```

### packages/vectordb/src/clippy_vectordb/__init__.py
```python
from .client import VectorDB

__all__ = ["VectorDB"]
```

### packages/vectordb/src/clippy_vectordb/client.py
```python
from qdrant_client import QdrantClient
from qdrant_client.http import models


class VectorDB:
    def __init__(self, host: str, port: int, collection: str, vector_size: int = 1536):
        self.client = QdrantClient(host=host, port=port)
        self.collection = collection
        self.vector_size = vector_size

    async def ensure_collection(self):
        collections = self.client.get_collections().collections
        names = [c.name for c in collections]
        if self.collection not in names:
            self.client.create_collection(
                collection_name=self.collection,
                vectors_config=models.VectorParams(
                    size=self.vector_size,
                    distance=models.Distance.COSINE,
                ),
            )

    async def upsert(self, point_id: str, vector: list[float], payload: dict | None = None):
        self.client.upsert(
            collection_name=self.collection,
            points=[models.PointStruct(id=point_id, vector=vector, payload=payload or {})],
        )

    async def search(self, vector: list[float], limit: int = 10) -> list[models.ScoredPoint]:
        return self.client.search(
            collection_name=self.collection,
            query_vector=vector,
            limit=limit,
        )
```

## Steps

Create the following directories with `src/clippy_*` structure (matching Task 2 pattern):
- `packages/config/src/clippy_config/`
- `packages/storage/src/clippy_storage/`
- `packages/events/src/clippy_events/`
- `packages/logging/src/clippy_logging/`
- `packages/vectordb/src/clippy_vectordb/`

Then for each package:
1. Install with `pip install -e packages/<name>`
2. Verify imports work

Verification commands to run after all installed:
```bash
python -c "from clippy_config import ClippyConfig; c=ClippyConfig(); print('config OK:', c.environment)"
python -c "from clippy_storage import create_storage; s=create_storage(); print('storage OK:', type(s).__name__)"
python -c "from clippy_logging import setup_logging; setup_logging(); print('logging OK')"
```
(nats and vectordb cannot be verified without running infrastructure, but should import successfully)

## Global Constraints
- All packages use `pyproject.toml` with hatchling
- Each package uses `src/clippy_<name>/` layout (standard hatchling src-layout)
- No hardcoded configuration
