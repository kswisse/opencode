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
