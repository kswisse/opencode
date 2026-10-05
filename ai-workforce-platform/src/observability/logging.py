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
