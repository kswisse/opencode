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
