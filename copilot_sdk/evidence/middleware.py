"""Optional Starlette middleware for evidence headers."""

from __future__ import annotations

from typing import Any, cast

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from .gate import EvidenceGate


class EvidenceGateMiddleware(BaseHTTPMiddleware):
    """Attach the evaluated tier and honest label to an API response."""

    def __init__(
        self,
        app: Any,
        gate: EvidenceGate,
        claim_id: str,
        context: str = "demo",
    ) -> None:
        super().__init__(app)
        self.gate = gate
        self.claim_id = claim_id
        self.context = context

    async def dispatch(self, request: Request, call_next: Any) -> Response:
        response = cast(Response, await call_next(request))
        result = self.gate.check(self.claim_id, self.context)
        response.headers["X-Evidence-Tier"] = result.tier.name
        response.headers["X-Evidence-Label"] = result.label
        response.headers["X-Evidence-Gate"] = "passed" if result.passed else "blocked"
        return response
