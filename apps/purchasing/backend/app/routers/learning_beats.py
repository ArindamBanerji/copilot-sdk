"""Purchasing learning and evidence beats backed by live graph state."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel


DOMAIN = "purchasing"
TARGET_VERIFIED = 20


class LearningHeroResponse(BaseModel):
    domain: str
    mirror_open: dict[str, str]
    continuity_close: dict[str, str]
    verified_count: int
    iks: float | None
    conservation_status: str
    source: str = "graphstore"


class SignalGateResponse(BaseModel):
    domain: str
    gate: str
    reliable: bool
    verified_count: int
    accuracy: float
    minimum_verified: int
    reason: str


class ProofLedgerResponse(BaseModel):
    domain: str
    entries: list[dict[str, Any]]
    competence_curve: list[dict[str, Any]]
    verified_count: int
    correct_count: int
    source: str = "graphstore"


class SelfPauseResponse(BaseModel):
    domain: str
    paused: bool
    drift_detected: bool
    reason: str
    verified_count: int
    accuracy: float


class RampResponse(BaseModel):
    domain: str
    state: str
    verified_count: int
    target_verified: int
    remaining_verified: int
    estimated_decisions_to_competence: int
    iks: float | None
    conservation_status: str


def create_learning_beats_router(state_provider: Any) -> APIRouter:
    router = APIRouter(prefix="/api/purchasing", tags=["purchasing-learning-beats"])

    @router.get("/learning/hero", response_model=LearningHeroResponse)
    def hero() -> LearningHeroResponse:
        stats = _stats(state_provider)
        return LearningHeroResponse(
            domain=DOMAIN,
            mirror_open={"title": "Mirror open", "message": "Purchasing is learning from verified decisions."},
            continuity_close={"title": "Continuity close", "message": "The next decision carries forward measured judgment."},
            **stats,
        )

    @router.get("/diagnostics/signal-gate", response_model=SignalGateResponse)
    def signal_gate() -> SignalGateResponse:
        stats = _stats(state_provider)
        minimum = 5
        reliable = stats["verified_count"] >= minimum and stats["accuracy"] >= 0.5
        return SignalGateResponse(
            domain=DOMAIN,
            gate="OPEN" if reliable else "CALIBRATING",
            reliable=reliable,
            verified_count=stats["verified_count"],
            accuracy=stats["accuracy"],
            minimum_verified=minimum,
            reason="Sufficient verified signal" if reliable else "Accumulate verified decisions before trusting the signal",
        )

    @router.get("/evidence/proof-ledger", response_model=ProofLedgerResponse)
    def proof_ledger() -> ProofLedgerResponse:
        graph = _graph_store(state_provider)
        rows = _verified(graph)
        entries = [_entry(row) for row in rows[-25:]]
        curve = [{"verified_count": index, "accuracy": _accuracy(rows[:index])} for index in range(1, len(rows) + 1)]
        correct = sum(1 for row in rows if row.get("is_correct") is True)
        return ProofLedgerResponse(
            domain=DOMAIN,
            entries=entries,
            competence_curve=curve,
            verified_count=len(rows),
            correct_count=correct,
        )

    @router.get("/learning/self-pause", response_model=SelfPauseResponse)
    def self_pause() -> SelfPauseResponse:
        stats = _stats(state_provider)
        drift = stats["verified_count"] > 0 and stats["accuracy"] < 0.5
        return SelfPauseResponse(
            domain=DOMAIN,
            paused=drift,
            drift_detected=drift,
            reason="Manager drift detected; pause and review evidence" if drift else "No manager drift detected",
            verified_count=stats["verified_count"],
            accuracy=stats["accuracy"],
        )

    @router.get("/diagnostics/ramp", response_model=RampResponse)
    @router.get("/competence/ramp", response_model=RampResponse)
    def ramp() -> RampResponse:
        stats = _stats(state_provider)
        remaining = max(TARGET_VERIFIED - stats["verified_count"], 0)
        return RampResponse(
            domain=DOMAIN,
            state="MEASURED" if remaining == 0 else "ACCUMULATING",
            verified_count=stats["verified_count"],
            target_verified=TARGET_VERIFIED,
            remaining_verified=remaining,
            estimated_decisions_to_competence=remaining,
            **{key: stats[key] for key in ("iks", "conservation_status")},
        )

    return router


def _graph_store(state_provider: Any) -> Any | None:
    candidate = state_provider() if callable(state_provider) else state_provider
    return getattr(candidate, "graph_store", None) or getattr(candidate, "_graph_store", None)


def _verified(graph: Any) -> list[dict[str, Any]]:
    getter = getattr(graph, "get_verified_decisions", None)
    if not callable(getter):
        return []
    try:
        rows = getter(DOMAIN)
    except Exception:
        return []
    return [row for row in rows if isinstance(row, dict)] if isinstance(rows, list) else []


def _stats(state_provider: Any) -> dict[str, Any]:
    graph = _graph_store(state_provider)
    rows = _verified(graph)
    correct = sum(1 for row in rows if row.get("is_correct") is True)
    scorer = state_provider() if callable(state_provider) else state_provider
    trajectory = getattr(scorer, "trajectory", None)
    payload = trajectory() if callable(trajectory) else {}
    payload = payload if isinstance(payload, dict) else {}
    status = getattr(scorer, "get_conservation_status", None)
    if callable(status):
        state = status()
    else:
        state = "BOOTSTRAP"
        getter = getattr(graph, "get_latest_conservation_statuses", None)
        if callable(getter):
            try:
                statuses = getter(DOMAIN)
                if statuses:
                    state = statuses[0].get("status", state)
            except Exception:
                pass
    return {
        "verified_count": len(rows),
        "accuracy": _accuracy(rows),
        "iks": _number(payload.get("current_iks")),
        "conservation_status": str(state or "BOOTSTRAP").upper(),
    }


def _accuracy(rows: list[dict[str, Any]]) -> float:
    return round(sum(1 for row in rows if row.get("is_correct") is True) / len(rows), 4) if rows else 0.0


def _number(value: Any) -> float | None:
    try:
        return float(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def _entry(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "decision_id": str(row.get("decision_id") or ""),
        "category": str(row.get("category") or ""),
        "is_correct": row.get("is_correct"),
        "verified_at": row.get("verified_at") or row.get("created_at"),
    }
