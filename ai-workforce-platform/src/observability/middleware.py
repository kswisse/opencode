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
            set_request_id(None)

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
