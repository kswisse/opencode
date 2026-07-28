from uuid import UUID
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

TENANT_ID = UUID("00000000-0000-0000-0000-000000000001")


class TenantMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request.state.tenant_id = TENANT_ID
        response = await call_next(request)
        return response
