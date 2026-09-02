from __future__ import annotations
from typing import Awaitable, Callable
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send
from .dependencies import require_auth

class AuthMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        request = Request(scope, receive=receive)
        try:
            scope.setdefault("state", {})["user"] = await require_auth(request)
        except HTTPException as exc:
            await JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})(scope, receive, send)
            return
        except Exception:
            await JSONResponse(status_code=500, content={"detail": "Internal server error"})(scope, receive, send)
            return
        await self.app(scope, receive, send)
