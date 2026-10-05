"""Request-scoped correlation ID propagation via contextvars."""
import contextvars
import uuid
from collections.abc import Generator
from contextlib import contextmanager

request_id_var: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "request_id", default=None
)


def get_request_id() -> str | None:
    """Get the current request ID from context."""
    return request_id_var.get()


def set_request_id(request_id: str | None) -> contextvars.Token:
    """Set the request ID in context. Returns token for reset."""
    return request_id_var.set(request_id)


def generate_request_id() -> str:
    """Generate a new UUID4 request ID."""
    return str(uuid.uuid4())


@contextmanager
def request_id_ctx_manager(rid: str | None = None) -> Generator[str, None, None]:
    """Context manager that sets a request ID and resets on exit."""
    new_id = rid or generate_request_id()
    token = set_request_id(new_id)
    try:
        yield new_id
    finally:
        request_id_var.reset(token)
