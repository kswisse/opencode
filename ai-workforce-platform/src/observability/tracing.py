"""OpenTelemetry distributed tracing setup."""
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.sdk.resources import Resource, SERVICE_NAME

from src.observability.config import ObservabilitySettings


def setup_tracing(settings: ObservabilitySettings) -> None:
    """Initialize OpenTelemetry tracer provider and instrumentors."""
    if not settings.enable_tracing:
        return

    resource = Resource.create({SERVICE_NAME: settings.service_name})
    provider = TracerProvider(resource=resource)
    trace.set_tracer_provider(provider)

    # Export to OTLP collector (if available)
    try:
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
        exporter = OTLPSpanExporter(endpoint=settings.otlp_endpoint, insecure=True)
        provider.add_span_processor(BatchSpanProcessor(exporter))
    except Exception:
        # OTLP exporter not available — fall back to console for dev
        if settings.environment == "development":
            provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))

    # Auto-instrument httpx (used by LLM client and any HTTP calls)
    try:
        from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
        HTTPXClientInstrumentor().instrument()
    except Exception:
        pass  # httpx instrumentation optional


def instrument_fastapi(app) -> None:
    """Instrument a FastAPI app with OpenTelemetry."""
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    FastAPIInstrumentor.instrument_app(app)


def instrument_sqlalchemy(engine) -> None:
    """Instrument SQLAlchemy engine for query-level tracing."""
    from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
    # For async engines, instrument the underlying sync_engine
    target_engine = getattr(engine, "sync_engine", engine)
    SQLAlchemyInstrumentor().instrument(engine=target_engine)


def get_tracer(name: str = __name__) -> trace.Tracer:
    """Get an OpenTelemetry tracer."""
    return trace.get_tracer(name)
