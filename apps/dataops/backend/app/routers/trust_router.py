"""DataOps trust-profile endpoint backed by the scorer fingerprint."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from fastapi import APIRouter, HTTPException

from copilot_sdk.backend.conservation_utils import compute_conservation_status_payload


def create_trust_router(
    domain: str,
    scorer_provider: Callable[[], Any],
    perturbation_provider: Callable[[], Any] | None = None,
) -> APIRouter:
    """Create a router that exposes learned factor reliability for ``domain``."""

    router = APIRouter()

    @router.get(f"/{domain}/trust")
    def trust_profile() -> dict[str, Any]:
        scorer = scorer_provider()
        try:
            fingerprint = _as_mapping(scorer.fingerprint())
            factors = _factor_payload(fingerprint.get("factors"))
            if not factors:
                raise RuntimeError("scorer fingerprint has no factors")

            perturbation = perturbation_provider() if perturbation_provider is not None else None
            overlay = perturbation.overlay(factors) if perturbation is not None else None
            if overlay is not None:
                for factor in factors:
                    if factor["name"] in overlay["factors"]:
                        factor["dk_weight"] = float(overlay["factors"][factor["name"]])
                        factor["label"] = _trust_label(factor["dk_weight"])
                factors.sort(key=lambda factor: (-factor["dk_weight"], factor["name"]))
                for rank, factor in enumerate(factors, start=1):
                    factor["rank"] = rank

            trajectory = _as_mapping(scorer.trajectory())
            graph_store = getattr(scorer, "graph_store", None)
            conservation = compute_conservation_status_payload(domain, graph_store)
            weights = [factor["dk_weight"] for factor in factors]
            highest = factors[0]
            lowest = factors[-1]
            narrative = (
                f"The system has learned that {highest['name']} "
                f"({highest['dk_weight']:.2f}) is the most predictive source. "
                f"{lowest['name']} ({lowest['dk_weight']:.2f}) is the noisiest; "
                "decisions based on it alone are less reliable."
            )
            return {
                "domain": domain,
                "factors": factors,
                "overall_trust": round(sum(weights) / len(weights), 3),
                "conservation_status": str(conservation.get("status", "UNAVAILABLE")),
                "verified_decisions": int(fingerprint.get("decisions_analyzed", 0) or 0),
                "iks": _optional_float(trajectory.get("current_iks")),
                "narrative": narrative,
                "evidence_tier": "synthetic",
                "evidence_label": "synthetic / modelled - not measured",
                "evidence_basis": "scorer fingerprint and current trajectory; no verified outcome claim",
            }
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(status_code=503, detail="Trust profile unavailable") from exc

    return router


def _factor_payload(raw_factors: Any) -> list[dict[str, Any]]:
    factors: list[dict[str, Any]] = []
    for raw in raw_factors or []:
        factor = _as_mapping(raw)
        name = str(factor.get("name", "")).strip()
        if not name:
            continue
        weight = _bounded_float(factor.get("weight", factor.get("dk_weight", 0.0)))
        factors.append(
            {
                "name": name,
                "dk_weight": weight,
                "label": _trust_label(weight),
            }
        )
    factors.sort(key=lambda factor: (-factor["dk_weight"], factor["name"]))
    for rank, factor in enumerate(factors, start=1):
        factor["rank"] = rank
    return factors


def _trust_label(weight: float) -> str:
    if weight > 0.7:
        return "reliable"
    if weight >= 0.3:
        return "moderate"
    return "noisy"


def _as_mapping(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    return {
        key: getattr(value, key)
        for key in ("name", "weight", "dk_weight", "factors", "decisions_analyzed", "current_iks")
        if hasattr(value, key)
    }


def _bounded_float(value: Any) -> float:
    try:
        return max(0.0, min(1.0, float(value)))
    except (TypeError, ValueError):
        return 0.0


def _optional_float(value: Any) -> float | None:
    try:
        return float(value) if value is not None else None
    except (TypeError, ValueError):
        return None
