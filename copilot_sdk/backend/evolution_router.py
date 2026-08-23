"""FastAPI evolution router factory backed by SDK AgentEvolver."""

from __future__ import annotations

from typing import Any, Callable

from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel, Field

from copilot_sdk.evolution import (
    AgentEvolver,
    DefaultPromotionGate,
    DefaultShadowRunner,
    InMemoryEvolutionLedger,
    PromptVariantEvolver,
)
from copilot_sdk.backend.models import (
    EvolutionOutcomeResponse,
    EvolutionPromotionResponse,
    EvolutionSummaryResponse,
    EvolutionHistoryResponse,
    EvolutionPromotedResponse,
    EvolutionVariantsResponse,
)
from copilot_sdk.state.cached_static import cached_static


class EvolutionOutcomeRequest(BaseModel):
    variant_id: str = Field(min_length=1)
    success: bool
    decision_id: str = Field(min_length=1)


class EvolutionPromotionRequest(BaseModel):
    family: str | None = None


def create_evolution_router(
    graph_store_factory: Callable[[], Any] | None = None,
    domain: str = "unknown",
    evolver_factory: Callable[[], Any] | None = None,
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
                try:
                    evolver_cache["evolver"] = evolver_factory()
                except Exception as exc:
                    raise HTTPException(status_code=503, detail=f"Graph store unavailable: {exc}") from exc
                if evolver_cache["evolver"] is None:
                    raise HTTPException(status_code=503, detail="Graph store unavailable")
            else:
                if graph_store_factory is not None:
                    try:
                        graph_store = graph_store_factory()
                    except Exception as exc:
                        raise HTTPException(status_code=503, detail=f"Graph store unavailable: {exc}") from exc
                    if graph_store is None:
                        raise HTTPException(status_code=503, detail="Graph store unavailable")
                else:
                    graph_store = None
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

    @router.post("/record-outcome", response_model=EvolutionOutcomeResponse)
    def record_outcome(request: EvolutionOutcomeRequest) -> dict[str, Any]:
        """Record one verified outcome against the app's live evolver."""
        evolver = _get_evolver()
        recorder = getattr(evolver, "record_outcome", None)
        if not callable(recorder):
            recorder = getattr(evolver, "record_verified_outcome", None)
        if not callable(recorder):
            raise HTTPException(status_code=501, detail="evolver does not support outcomes")
        try:
            recorder(request.variant_id, request.success)
        except (KeyError, ValueError) as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        stats = _variant_stats(evolver, request.variant_id)
        return {
            "domain": domain,
            "decision_id": request.decision_id,
            "variant_id": request.variant_id,
            "success": request.success,
            "recorded": True,
            "stats": stats,
        }

    @router.post("/check-promotion", response_model=EvolutionPromotionResponse)
    def check_promotion(request: EvolutionPromotionRequest | None = None) -> dict[str, Any]:
        """Explicitly evaluate promotion using the evolver's live gate/provider."""
        evolver = _get_evolver()
        family = request.family if request is not None else None
        checker = getattr(evolver, "check_for_promotion", None)
        if not callable(checker):
            raise HTTPException(status_code=501, detail="evolver does not support promotion checks")
        try:
            result = checker(family=family)
        except TypeError:
            result = checker()
        result = dict(result or {})
        promoted = bool(result.get("promoted") or result.get("promoted_id"))
        eligible = bool(result.get("promotable", promoted))
        return {
            "domain": domain,
            "promoted": promoted,
            "eligible": eligible,
            "blocked": not eligible,
            "reason": result.get("reason") or result.get("message"),
            "result": result,
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


def _variant_stats(evolver: Any, variant_id: str) -> dict[str, Any] | None:
    summary = getattr(evolver, "get_summary", None)
    if callable(summary):
        for variant in summary().get("variants", []):
            if str(variant.get("id") or variant.get("variant_id")) == variant_id:
                return {
                    "variant_id": variant_id,
                    "successes": variant.get("successes", 0),
                    "failures": variant.get("failures", 0),
                    "total": variant.get("total", 0),
                    "success_rate": variant.get("success_rate", 0.0),
                }
    store = getattr(evolver, "store", None)
    if store is not None:
        try:
            stats = store.get_global_stats(variant_id)
            return {
                "variant_id": variant_id,
                "successes": stats.successes,
                "failures": stats.failures,
                "total": stats.total,
                "success_rate": stats.success_rate,
            }
        except (KeyError, ValueError):
            return None
    return None


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
    conservation_payload = _read_conservation_payload(provider)
    conservation_state = str(
        conservation_payload.get("status") or "UNKNOWN"
    ).upper()
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
        "provider_source": conservation_payload.get("source"),
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
    return str(_read_conservation_payload(provider).get("status") or "UNKNOWN").upper()


def _read_conservation_payload(provider: Any) -> dict[str, Any]:
    if provider is None:
        return {"status": "UNKNOWN"}
    try:
        state = provider() if callable(provider) else provider.get_state()
        if isinstance(state, dict):
            return dict(state)
        return {"status": str(state or "UNKNOWN").upper()}
    except Exception:
        return {"status": "UNKNOWN"}


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
