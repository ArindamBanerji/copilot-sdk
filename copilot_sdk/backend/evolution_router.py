"""FastAPI evolution router factory backed by GAE evolution."""

from __future__ import annotations

import inspect
import sys
from pathlib import Path
from typing import Any, Callable

from fastapi import APIRouter


def _ensure_gae_path() -> None:
    workspace = Path(__file__).resolve().parents[3]
    gae_path = workspace / "graph-attention-engine-v50"
    if gae_path.exists() and str(gae_path) not in sys.path:
        sys.path.insert(0, str(gae_path))


_ensure_gae_path()

from gae import evolution


ENGINE_VARIANTS = {"gae": "gae.evolution", "component": "get_recent_events"}
ENGINE_PATTERNS = {"gae": "gae.evolution", "component": "get_evolution_summary"}


def create_evolution_router(
    domain: str,
    ledger_provider: Callable[[], Any] | Any | None = None,
) -> APIRouter:
    """Create a domain-parametric evolution router."""

    router = APIRouter()

    @router.get("/evolution/variants")
    async def variants(limit: int = 20) -> dict[str, Any]:
        client = await _resolve_ledger(ledger_provider)
        events = await _recent_events(client, limit=limit)
        return {
            "engine": ENGINE_VARIANTS,
            "domain": domain,
            "variants": [_variant_payload(event) for event in events],
        }

    @router.get("/evolution/patterns")
    async def patterns(limit: int = 20) -> dict[str, Any]:
        client = await _resolve_ledger(ledger_provider)
        events = await _recent_events(client, limit=limit)
        summary = await _summary(client)
        return {
            "engine": ENGINE_PATTERNS,
            "domain": domain,
            "patterns": [_pattern_payload(event) for event in events if _has_pattern(event)],
            "summary": summary,
        }

    return router


async def _resolve_ledger(ledger_provider: Callable[[], Any] | Any | None) -> Any:
    if callable(ledger_provider):
        value = ledger_provider()
    else:
        value = ledger_provider
    if inspect.isawaitable(value):
        return await value
    return value


async def _recent_events(client: Any, limit: int = 20) -> list[dict[str, Any]]:
    if client is None:
        return []
    try:
        return await evolution.get_recent_events(client, limit=limit)
    except Exception:
        return []


async def _summary(client: Any) -> dict[str, Any]:
    if client is None:
        return _empty_summary()
    try:
        return await evolution.get_evolution_summary(client)
    except Exception:
        return _empty_summary()


def _variant_payload(event: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": event.get("id"),
        "variant_id": event.get("variant_id"),
        "event_type": event.get("event_type"),
        "artifact_type": event.get("artifact_type"),
        "description": event.get("description") or "",
        "impact": event.get("impact") or "operational",
        "magnitude": _number(event.get("magnitude")),
        "timestamp": event.get("timestamp"),
        "timestamp_epoch": int(event.get("timestamp_epoch") or 0),
        "metadata": event.get("metadata") or {},
    }


def _pattern_payload(event: dict[str, Any]) -> dict[str, Any]:
    return {
        "variant_id": event.get("variant_id"),
        "source_copilot": event.get("source_copilot"),
        "source_rule": event.get("source_rule"),
        "warm_start_prior": event.get("warm_start_prior") or {},
        "artifact_type": event.get("artifact_type"),
        "description": event.get("description") or "",
    }


def _has_pattern(event: dict[str, Any]) -> bool:
    return bool(
        event.get("source_copilot")
        or event.get("source_rule")
        or event.get("warm_start_prior")
    )


def _empty_summary() -> dict[str, Any]:
    return {
        "variants_generated": 0,
        "variants_promoted": 0,
        "variants_rejected": 0,
        "variants_rolled_back": 0,
        "shadow_batches": 0,
        "shadow_started": 0,
        "by_artifact_type": {},
        "avg_shadow_win_rate": 0.0,
        "total_shadow_decisions": 0,
    }


def _number(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0
