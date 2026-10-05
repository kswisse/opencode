from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.requests import Request

from src.config import settings
from src.observability.config import ObservabilitySettings
from src.observability.logging import setup_logging, get_logger
from src.observability.middleware import ObservabilityMiddleware
from src.observability.metrics import setup_metrics
from src.observability.tracing import setup_tracing, instrument_fastapi, instrument_sqlalchemy
from src.observability.health import health_router
from src.api.v1.router import api_v1_router
from src.core.exceptions import AppError


def create_app() -> FastAPI:
    # Initialize observability config
    obs_config = ObservabilitySettings.from_settings(settings)

    # Setup structured logging
    setup_logging(obs_config)
    log = get_logger("app")

    # Setup OpenTelemetry tracing
    setup_tracing(obs_config)

    app = FastAPI(
        title="AI Workforce Platform",
        version="0.1.0",
        debug=settings.debug,
    )

    # --- Middleware (order matters: outermost = last added) ---
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(ObservabilityMiddleware)

    # --- Instrument FastAPI for tracing + metrics ---
    if obs_config.enable_tracing:
        instrument_fastapi(app)

    if obs_config.enable_metrics:
        setup_metrics(app)

    # --- Instrument SQLAlchemy for query tracing ---
    if obs_config.enable_tracing:
        from src.database import engine
        instrument_sqlalchemy(engine)

    # --- Routers ---
    app.include_router(health_router)
    app.include_router(api_v1_router)

    # --- Exception handlers ---
    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError):
        log.error(
            "app_error",
            code=exc.code,
            message=exc.message,
            status_code=exc.status_code,
            path=request.url.path,
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={"data": None, "error": {"code": exc.code, "message": exc.message}},
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        log.error(
            "unhandled_exception",
            path=request.url.path,
            method=request.method,
            error=str(exc),
            exc_info=True,
        )
        return JSONResponse(
            status_code=500,
            content={"data": None, "error": {"code": "INTERNAL_ERROR", "message": "Internal server error"}},
        )

    log.info("app_started", environment=settings.environment)
    return app


app = create_app()
