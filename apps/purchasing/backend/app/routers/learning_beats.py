"""Purchasing learning and evidence beats backed by live graph state."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

from copilot_sdk.backend.graph_access import GRAPH_CONNECTION_ERRORS


DOMAIN = "purchasing"
TARGET_VERIFIED = 20
LOGGER = logging.getLogger(__name__)
# Infrastructure errors that indicate dependency unavailability. RuntimeError
# remains part of this boundary because existing scorer/store adapters use it
# for offline reads. Programming errors such as TypeError and ValueError are
# intentionally excluded so they propagate instead of appearing degraded.
_INFRA_ERRORS = (*GRAPH_CONNECTION_ERRORS, RuntimeError)
VALID_CONSERVATION_STATES = {
    "GREEN",
    "AMBER",
    "RED",
    "BOOTSTRAP",
    "COLD_START",
    "CALIBRATING",
    "UNKNOWN",
}


class LearningHeroResponse(BaseModel):
    domain: str
    mirror_open: dict[str, str]
    continuity_close: dict[str, str]
    verified_count: int
    iks: float = 0.0
    conservation_status: str
    source: str = "graphstore"
    data_available: bool = True
    degraded: bool = False
    verified_available: bool = True
    trajectory_available: bool = True
    iks_available: bool = True
    conservation_available: bool = True


class SignalGateResponse(BaseModel):
    domain: str
    gate: str
    reliable: bool
    verified_count: int
    accuracy: float
    minimum_verified: int
    reason: str
    data_available: bool = True


class ProofLedgerResponse(BaseModel):
    domain: str
    entries: list[dict[str, Any]]
    competence_curve: list[dict[str, Any]]
    verified_count: int
    correct_count: int
    source: str = "graphstore"
    data_available: bool = True


class SelfPauseResponse(BaseModel):
    domain: str
    paused: bool
    drift_detected: bool
    reason: str
    verified_count: int
    accuracy: float
    data_available: bool = True


class RampResponse(BaseModel):
    domain: str
    state: str
    verified_count: int
    target_verified: int
    remaining_verified: int
    estimated_decisions_to_competence: int
    iks: float = 0.0
    conservation_status: str
    data_available: bool = True
    degraded: bool = False
    trajectory_available: bool = True
    iks_available: bool = True
    conservation_available: bool = True


def create_learning_beats_router(state_provider: Any) -> APIRouter:
    router = APIRouter(prefix="/api/purchasing", tags=["purchasing-learning-beats"])

    @router.get(
        "/learning/hero",
        response_model=LearningHeroResponse,
    )
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
            data_available=stats["data_available"],
        )

    @router.get("/evidence/proof-ledger", response_model=ProofLedgerResponse)
    def proof_ledger() -> ProofLedgerResponse:
        graph = _graph_store(state_provider)
        rows = _verified(graph)
        data_available = rows is not None
        rows = rows or []
        entries = [_entry(row) for row in rows[-25:]]
        curve = [{"verified_count": index, "accuracy": _accuracy(rows[:index])} for index in range(1, len(rows) + 1)]
        correct = sum(1 for row in rows if row.get("is_correct") is True)
        return ProofLedgerResponse(
            domain=DOMAIN,
            entries=entries,
            competence_curve=curve,
            verified_count=len(rows),
            correct_count=correct,
            data_available=data_available,
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
            data_available=stats["data_available"],
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
            **{key: stats[key] for key in (
                "iks", "conservation_status", "data_available", "degraded",
                "trajectory_available", "iks_available", "conservation_available",
            )},
        )

    return router


def _graph_store(state_provider: Any) -> Any | None:
    candidate = state_provider() if callable(state_provider) else state_provider
    return getattr(candidate, "graph_store", None) or getattr(candidate, "_graph_store", None)


def _verified(graph: Any) -> list[dict[str, Any]] | None:
    getter = getattr(graph, "get_verified_decisions", None)
    if not callable(getter):
        return None
    try:
        rows = getter(DOMAIN)
    except _INFRA_ERRORS as exc:
        LOGGER.warning("Purchasing verified-history read failed: %s", exc)
        return None
    return [row for row in rows if isinstance(row, dict)] if isinstance(rows, list) else None


def _stats(state_provider: Any) -> dict[str, Any]:
    graph = _graph_store(state_provider)
    rows = _verified(graph)
    verified_available = rows is not None
    rows = rows or []
    correct = sum(1 for row in rows if row.get("is_correct") is True)
    scorer = state_provider() if callable(state_provider) else state_provider
    trajectory = getattr(scorer, "trajectory", None)
    try:
        raw_payload = trajectory() if callable(trajectory) else None
    except _INFRA_ERRORS as exc:
        LOGGER.warning("Purchasing learning trajectory read failed: %s", exc)
        raw_payload = None
    trajectory_available = isinstance(raw_payload, dict)
    if raw_payload is not None and not trajectory_available:
        LOGGER.warning(
            "Purchasing learning trajectory returned malformed data: %s",
            type(raw_payload).__name__,
        )
    payload = raw_payload if trajectory_available else {}
    status = getattr(scorer, "get_conservation_status", None)
    state = "UNAVAILABLE"
    conservation_available = False
    if callable(status):
        try:
            raw_state = status()
        except _INFRA_ERRORS as exc:
            LOGGER.warning("Purchasing conservation-state read failed: %s", exc)
        else:
            normalized_state = str(raw_state).strip().upper() if isinstance(raw_state, str) else ""
            if normalized_state in VALID_CONSERVATION_STATES:
                state = normalized_state
                conservation_available = True
            elif raw_state is not None:
                LOGGER.warning(
                    "Purchasing conservation-state read returned malformed data: %s",
                    type(raw_state).__name__,
                )
    else:
        getter = getattr(graph, "get_latest_conservation_statuses", None)
        if callable(getter):
            try:
                statuses = getter([DOMAIN])
            except _INFRA_ERRORS as exc:
                LOGGER.warning("Purchasing graph conservation read failed: %s", exc)
            else:
                if isinstance(statuses, list) and not statuses:
                    state = "BOOTSTRAP"
                    conservation_available = True
                elif isinstance(statuses, list) and isinstance(statuses[0], dict):
                    raw_state = statuses[0].get("status")
                    normalized_state = str(raw_state).strip().upper() if isinstance(raw_state, str) else ""
                    if normalized_state in VALID_CONSERVATION_STATES:
                        state = normalized_state
                        conservation_available = True
                    else:
                        LOGGER.warning("Purchasing graph conservation read returned a malformed status")
                elif statuses is not None:
                    LOGGER.warning(
                        "Purchasing graph conservation read returned malformed data: %s",
                        type(statuses).__name__,
                    )
    degraded = not verified_available or not conservation_available or not trajectory_available
    iks = _number(payload.get("current_iks"))
    iks_available = trajectory_available and iks is not None
    degraded = degraded or not iks_available
    result = {
        "verified_count": len(rows),
        "accuracy": _accuracy(rows),
        "iks": iks if iks is not None else 0.0,
        "conservation_status": "UNAVAILABLE" if degraded else str(state or "BOOTSTRAP").upper(),
        "verified_available": verified_available,
        "trajectory_available": trajectory_available,
        "iks_available": iks_available,
        "conservation_available": conservation_available,
        "data_available": not degraded,
        "degraded": degraded,
    }
    return result


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
