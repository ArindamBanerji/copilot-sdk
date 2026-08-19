"""Optional FastAPI router for pilot qualification reports."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from typing import Any

from fastapi import APIRouter, Query

from .checks import QualificationCheck
from .gate import QualificationGate


def create_qualification_router(
    gate: QualificationGate,
    checks_factory: Callable[[str], Iterable[QualificationCheck]],
    copilots: Iterable[str] = ("trading", "purchasing", "dataops", "soc", "s2p"),
) -> APIRouter:
    router = APIRouter(prefix="/api/pilot", tags=["pilot-qualification"])
    known = tuple(copilots)

    @router.get("/qualify")
    def qualify(copilot: str = Query(...)) -> dict[str, Any]:
        if copilot not in known:
            return {"copilot": copilot, "passed": False, "error": "unknown copilot"}
        return gate.run(copilot, checks_factory(copilot)).to_dict()

    @router.get("/qualify/all")
    def qualify_all() -> dict[str, Any]:
        reports = [gate.run(copilot, checks_factory(copilot)).to_dict() for copilot in known]
        return {"reports": reports, "passed": all(report["passed"] for report in reports)}

    return router
