"""ASGI middleware that establishes the request tenant context."""

from __future__ import annotations

from copilot_sdk.config.tenant import TenantConfig, reset_tenant_id, set_tenant_id
from starlette.requests import Request
from starlette.types import ASGIApp, Receive, Scope, Send


class TenantMiddleware:
    """Extract ``X-Tenant-Id`` without changing endpoint signatures."""

    def __init__(self, app: ASGIApp, config: TenantConfig | None = None) -> None:
        self.app = app
        self.config = config or TenantConfig.load()

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        request = Request(scope, receive=receive)
        tenant_id = self.config.tenant_from_headers(request.headers)
        token = set_tenant_id(tenant_id)
        scope.setdefault("state", {})["tenant_id"] = tenant_id
        try:
            await self.app(scope, receive, send)
        finally:
            reset_tenant_id(token)
