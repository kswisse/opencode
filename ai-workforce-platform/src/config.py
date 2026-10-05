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
    jwt_secret_key: str  # No default - must be set via JWT_SECRET_KEY env var
    jwt_algorithm: str = "HS256"
    jwt_expiry_minutes: int = 60
    environment: str = "development"  # development | testing | production
    otlp_endpoint: str = "http://localhost:4317"
    service_name: str = "ai-workforce-platform"


settings = Settings()
