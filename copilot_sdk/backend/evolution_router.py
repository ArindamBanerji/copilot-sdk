"""FastAPI evolution router factory backed by SDK AgentEvolver."""

from __future__ import annotations

from typing import Any, Callable

from fastapi import APIRouter, Query, Request

from copilot_sdk.evolution import (
    AgentEvolver,
    DefaultPromotionGate,
    DefaultShadowRunner,
    InMemoryEvolutionLedger,
    PromptVariantEvolver,
)
from copilot_sdk.backend.models import (
    EvolutionSummaryResponse,
    EvolutionHistoryResponse,
    EvolutionPromotedResponse,
    EvolutionVariantsResponse,
)
from copilot_sdk.state.cached_static import cached_static


def create_evolution_router(
    graph_store_factory: Callable[[], Any] | None = None,
    domain: str = "unknown",
    evolver_factory: Callable[[], AgentEvolver | PromptVariantEvolver] | None = None,
    variant_provider: Callable[[], list[dict[str, Any]]] | None = None,
) -> APIRouter:
    if graph_store_factory is not None and not callable(graph_store_factory):
        raise TypeError("graph_store_factory must be callable or None")
    if evolver_factory is not None and not callable(evolver_factory):
        raise TypeError("evolver_factory must be callable or None")

    router = APIRouter(prefix="/api/evolution", tags=["evolution"])
    evolver_cache: dict[str, AgentEvolver | PromptVariantEvolver | None] = {"evolver": None}

    def _get_evolver() -> AgentEvolver | PromptVariantEvolver:
        if evolver_cache["evolver"] is None:
            if evolver_factory is not None:
                evolver_cache["evolver"] = evolver_factory()
            else:
                graph_store = graph_store_factory() if graph_store_factory is not None else None
                ledger = InMemoryEvolutionLedger(evolution_store=graph_store, domain=domain)
                evolver_cache["evolver"] = AgentEvolver(
                    ledger=ledger,
                    shadow_runner=DefaultShadowRunner(),
                    promotion_gate=DefaultPromotionGate(),
                )
        return evolver_cache["evolver"]

    @router.get("/variants", response_model=EvolutionVariantsResponse)
    def variants() -> dict[str, Any]:
        evolver = _get_evolver()
        prompt_summary = _prompt_summary(evolver)
        if prompt_summary is not None:
            # Prompt variants are inventory.  They are not promoted rules;
            # exposing configured baselines as active rules falsely implies
            # that evolution has changed production behavior.
            active_rules = []
            promoted_rules = [
                str(item["id"])
                for item in prompt_summary["variants"]
                if item.get("status") == "promoted"
            ]
        else:
            active_rules = sorted(evolver.get_active_rules())
            promoted_rules = evolver.get_promoted_rules()
        variants_payload = _provided_variants(variant_provider)
        if not variants_payload and prompt_summary is not None:
            variants_payload = prompt_summary["variants"]
        return {
            "domain": domain,
            "variants": variants_payload,
            "active_rules": active_rules,
            "promoted_rules": promoted_rules,
            "total_active": len(active_rules),
            "total_promoted": len(promoted_rules),
        }

    @router.get("/history", response_model=EvolutionHistoryResponse)
    def history(
        rule_name: str | None = None,
        limit: int = Query(50, ge=0, le=500),
    ) -> dict[str, Any]:
        evolver = _get_evolver()
        if isinstance(evolver, PromptVariantEvolver):
            events = []
        else:
            events = evolver.get_evolution_history(rule_name=rule_name, limit=limit)
        return {
            "domain": domain,
            "events": events,
            "count": len(events),
        }

    @router.get("/promoted", response_model=EvolutionPromotedResponse)
    @cached_static("evolution-promoted", copilot=domain)
    def promoted(request: Request) -> dict[str, Any]:
        evolver = _get_evolver()
        if isinstance(evolver, PromptVariantEvolver):
            promoted = [
                item["id"]
                for item in _prompt_summary(evolver)["variants"]
                if item.get("status") == "promoted"
            ]
        else:
            promoted = evolver.get_promoted_rules()
        return {
            "domain": domain,
            "promoted": promoted,
        }

    @router.get("/summary", response_model=EvolutionSummaryResponse)
    def summary() -> dict[str, Any]:
        evolver = _get_evolver()
        prompt_summary = _prompt_summary(evolver)
        if prompt_summary is None:
            return {
                "domain": domain,
                "evolution_enabled": True,
                "inventory": {"active": sorted(evolver.get_active_rules()), "shadow": []},
            }
        provider = getattr(getattr(evolver, "config", None), "conservation_state_provider", None)
        conservation_state: Any = {"status": "UNKNOWN"}
        if provider is not None:
            try:
                conservation_state = provider()
            except Exception:
                pass
        active = [item for item in prompt_summary["variants"] if item.get("status") == "active"]
        shadow = [item for item in prompt_summary["variants"] if item.get("status") == "shadow"]
        return {
            "domain": domain,
            "evolution_enabled": True,
            "conservation_state": conservation_state,
            "active_variant": active[0]["id"] if active else None,
            "inventory": {"active": active, "shadow": shadow},
            **prompt_summary,
        }

    return router


def _provided_variants(provider: Callable[[], list[dict[str, Any]]] | None) -> list[dict[str, Any]]:
    if provider is None:
        return []
    try:
        return list(provider() or [])
    except Exception:
        return []


def _prompt_summary(evolver: AgentEvolver | PromptVariantEvolver) -> dict[str, Any] | None:
    """Normalize PromptVariantEvolver inventory without changing legacy behavior."""

    if not isinstance(evolver, PromptVariantEvolver):
        return None
    return dict(evolver.get_summary())


def build_evolution_summary(evolver: Any, domain: str) -> dict[str, Any]:
    """Normalize SDK and copilot-specific evolvers to WP-4 telemetry."""
    if evolver is None:
        return {
            "domain": domain,
            "evolution_enabled": False,
            "schema_version": 1,
        }

    variants = _evolver_variants(evolver)
    active = [item for item in variants if item.get("status") == "active"]
    shadow = [item for item in variants if item.get("status") == "shadow"]
    provider = getattr(getattr(evolver, "config", None), "conservation_state_provider", None)
    if provider is None:
        provider = getattr(evolver, "conservation_provider", None)
    conservation_state = _read_conservation_status(provider)
    active_variant = None
    if active:
        active_variant = {
            key: active[0].get(key)
            for key in ("id", "family", "version")
        }

    return {
        "domain": domain,
        "evolution_enabled": True,
        "conservation_state": conservation_state,
        "active_variant": active_variant,
        "inventory": {"active": active, "shadow": shadow},
        "variant_stats": [
            {
                "variant_id": item.get("id"),
                "successes": item.get("successes", 0),
                "total": item.get("total", 0),
                "success_rate": item.get("success_rate", 0.0),
            }
            for item in variants
        ],
        "recent_events": _recent_evolution_events(evolver),
        "schema_version": 1,
    }


def _evolver_variants(evolver: Any) -> list[dict[str, Any]]:
    summary = getattr(evolver, "get_summary", None)
    if callable(summary):
        raw = summary().get("variants", [])
    else:
        registered = getattr(evolver, "registered_variants", None)
        raw = registered() if callable(registered) else []
    normalized: list[dict[str, Any]] = []
    for item in raw or []:
        if hasattr(item, "__dict__"):
            item = vars(item)
        if not isinstance(item, dict):
            continue
        normalized.append(
            {
                "id": item.get("id", item.get("variant_id")),
                "family": item.get("family", "default"),
                "version": item.get("version", "1"),
                "status": item.get("status", "active"),
                "successes": item.get("successes", item.get("success", 0)),
                "total": item.get("total", 0),
                "success_rate": item.get("success_rate", 0.0),
            }
        )
    return normalized


def _read_conservation_status(provider: Any) -> str:
    if provider is None:
        return "UNKNOWN"
    try:
        state = provider() if callable(provider) else provider.get_state()
        if isinstance(state, dict):
            state = state.get("status", state.get("state", "UNKNOWN"))
        return str(state or "UNKNOWN").upper()
    except Exception:
        return "UNKNOWN"


def _recent_evolution_events(evolver: Any) -> list[dict[str, Any]]:
    history = getattr(evolver, "get_evolution_history", None)
    if not callable(history):
        return []
    try:
        events = history(limit=20)
    except TypeError:
        events = history()
    except Exception:
        return []
    valid = {"generated", "shadow", "promoted", "rejected"}
    normalized: list[dict[str, Any]] = []
    for event in events or []:
        if not isinstance(event, dict):
            continue
        event_type = str(event.get("event_type", event.get("type", ""))).lower()
        if event_type not in valid:
            continue
        normalized.append(
            {
                "event_type": event_type,
                "variant_id": event.get("variant_id"),
                "reason": event.get("reason"),
                "timestamp": event.get("timestamp", event.get("created_at")),
                "metrics": event.get("metrics", {}),
            }
        )
    return normalized
