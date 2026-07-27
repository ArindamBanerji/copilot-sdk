"""Purchasing verification route with kitchen-language reason codes."""

from __future__ import annotations

from dataclasses import asdict, is_dataclass
from typing import Any, Callable

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict

from copilot_sdk.backend.conservation_utils import compute_conservation_status_payload
from copilot_sdk.scoring.presets.purchasing import PurchasingPreset


DOMAIN = "purchasing"
REASON_CODES: dict[str, str] = {
    "supplier_preference": "Chose preferred supplier",
    "price_override": "Found better price",
    "seasonal_adjustment": "Seasonal menu change",
    "manager_directive": "Manager instruction",
    "quality_concern": "Quality issue flagged",
    "par_adjustment": "Par levels changed",
    "other": "Other",
}


class VerifyRequest(BaseModel):
    decision_id: str
    actual_action: str
    reason_code: str
    notes: str | None = None


class VerifyResponse(BaseModel):
    model_config = ConfigDict(extra="allow")

    decision_id: str
    recommended_action: str
    actual_action: str
    is_override: bool
    reason_code: str
    notes: str | None = None
    conservation_status: str
    conservation_q: float
    verified_count: int
    metadata: dict[str, Any]
    reward: float | None = None
    reward_raw: float | None = None
    iks_before: float | None = None
    iks_after: float | None = None
    centroid_delta: float | None = None
    decisions_total: int | None = None
    outcome: str | None = None


ScorerProvider = Callable[[], Any] | Any


def create_verify_router(scorer_provider: ScorerProvider) -> APIRouter:
    router = APIRouter(prefix="/api/purchasing/verify", tags=["purchasing-verify"])
    preset = PurchasingPreset()
    valid_actions = set(preset.shape.action_names)

    @router.get("/reason-codes")
    def reason_codes() -> dict[str, Any]:
        return {
            "reason_codes": [
                {"code": code, "label": label}
                for code, label in REASON_CODES.items()
            ],
            "count": len(REASON_CODES),
        }

    @router.post("", response_model=VerifyResponse)
    def verify(request: VerifyRequest) -> dict[str, Any]:
        decision_id = request.decision_id.strip()
        actual_action = request.actual_action.strip()
        reason_code = request.reason_code.strip()
        if not decision_id:
            raise HTTPException(status_code=400, detail="decision_id is required")
        if actual_action not in valid_actions:
            raise HTTPException(status_code=400, detail=f"Invalid actual_action: {actual_action}")
        if reason_code not in REASON_CODES:
            raise HTTPException(status_code=400, detail=f"Invalid reason_code: {reason_code}")

        state = _state(scorer_provider)
        store = _store_for(state)
        if store is None or not callable(getattr(store, "get_decision", None)):
            raise HTTPException(status_code=500, detail="Verification requires a graph store")

        decision = store.get_decision(decision_id, domain=DOMAIN)
        if decision is None:
            raise HTTPException(status_code=404, detail=f"Unknown decision: {decision_id}")
        if _already_verified(store, decision_id, decision):
            raise HTTPException(status_code=409, detail=f"Decision already verified: {decision_id}")

        recommended_action = str(decision.get("recommended_action") or decision.get("action") or "")
        metadata = {
            "reason_code": reason_code,
            "reason_label": REASON_CODES[reason_code],
            "notes": request.notes,
            "source": "purchasing_verify",
        }
        try:
            learn_result = _learn_with_context(
                state,
                decision_id=decision_id,
                actual_action=actual_action,
                context=metadata,
            )
            learn_payload = _learn_payload(learn_result)
            if _is_conservation_paused(learn_payload):
                _record_paused_outcome(
                    store,
                    decision_id=decision_id,
                    actual_action=actual_action,
                    actual_index=preset.shape.action_names.index(actual_action),
                    is_correct=actual_action == recommended_action,
                    context=metadata,
                )
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=f"Unknown decision: {decision_id}") from exc
        except AssertionError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except ValueError as exc:
            if "already exists" in str(exc).lower():
                raise HTTPException(status_code=409, detail=f"Decision already verified: {decision_id}") from exc
            raise HTTPException(status_code=400, detail=str(exc)) from exc

        conservation = compute_conservation_status_payload(DOMAIN, state)
        verified_count = int(conservation.get("verified_count") or 0)
        correct_count = int(conservation.get("correct_count") or 0)
        q = correct_count / verified_count if verified_count else 0.0
        response = {
            "decision_id": decision_id,
            "recommended_action": recommended_action,
            "actual_action": actual_action,
            "is_override": actual_action != recommended_action,
            "reason_code": reason_code,
            "notes": request.notes,
            "conservation_status": str(conservation.get("status") or "RED"),
            "conservation_q": float(q),
            "verified_count": verified_count,
            "metadata": metadata,
        }
        response.update(learn_payload)
        return response

    return router


def _state(provider: ScorerProvider) -> Any:
    return provider() if callable(provider) else provider


def _store_for(state: Any) -> Any | None:
    return getattr(state, "graph_store", None) or getattr(state, "_graph_store", None)


def _already_verified(store: Any, decision_id: str, decision: dict[str, Any]) -> bool:
    if str(decision.get("status") or "").lower() in {"confirmed", "overridden"}:
        return True
    get_verified = getattr(store, "get_verified_decisions", None)
    if not callable(get_verified):
        return False
    verified = get_verified(DOMAIN)
    return any(str(row.get("decision_id") or "") == decision_id for row in verified or [])


def _learn_with_context(
    state: Any,
    *,
    decision_id: str,
    actual_action: str,
    context: dict[str, Any],
) -> Any:
    learn = getattr(state, "learn", None)
    if callable(learn):
        return learn(
            decision_id,
            actual_action,
            "confirmed",
            context=context,
        )

    scorer_factory = getattr(state, "_scorer", None)
    if callable(scorer_factory):
        scorer = scorer_factory()
        return scorer.learn(
            decision_id,
            actual_action,
            "confirmed",
            context=context,
        )
    raise RuntimeError("Verification requires a scorer with learn()")


def _is_conservation_paused(payload: dict[str, Any]) -> bool:
    return payload.get("status") == "paused" and payload.get("reason") == "conservation_red"


def _record_paused_outcome(
    store: Any,
    *,
    decision_id: str,
    actual_action: str,
    actual_index: int,
    is_correct: bool,
    context: dict[str, Any],
) -> None:
    write_outcome = getattr(store, "write_outcome", None)
    if not callable(write_outcome):
        return
    write_outcome(
        decision_id=decision_id,
        actual_action=actual_action,
        is_correct=is_correct,
        domain=DOMAIN,
        metadata={
            "actual_index": actual_index,
            "outcome": "confirmed",
            "context": context,
        },
    )


def _learn_payload(learn_result: Any) -> dict[str, Any]:
    if learn_result is None:
        return {}
    if is_dataclass(learn_result):
        return asdict(learn_result)
    if isinstance(learn_result, dict):
        return dict(learn_result)
    return {
        key: getattr(learn_result, key)
        for key in (
            "reward",
            "reward_raw",
            "iks_before",
            "iks_after",
            "centroid_delta",
            "decisions_total",
            "outcome",
        )
        if hasattr(learn_result, key)
    }
