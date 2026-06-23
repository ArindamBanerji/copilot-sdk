"""Archetype API router for generated bootstrap presets."""

from __future__ import annotations

from typing import Any

import numpy as np
from fastapi import APIRouter, HTTPException, Request

from copilot_sdk.generators.archetype import ArchetypeGenerator
from copilot_sdk.scoring.presets.dataops import DataOpsPreset
from copilot_sdk.scoring.presets.purchasing import PurchasingPreset
from copilot_sdk.scoring.presets.soc import SOCPreset
from copilot_sdk.scoring.presets.trading import TradingPreset


_ARCHETYPE_DOMAINS = {
    "security_operations": "soc",
    "source_to_pay": "purchasing",
    "dataops": "dataops",
    "financial_services": "trading",
}


def create_archetype_router() -> APIRouter:
    router = APIRouter(prefix="/api/archetypes", tags=["Archetypes"])

    @router.get("")
    def list_archetypes(domain: str | None = None) -> list[dict[str, Any]]:
        rows = [_archetype_summary(name) for name in ArchetypeGenerator.list_archetypes()]
        if domain:
            wanted = str(domain).strip().lower()
            rows = [row for row in rows if row["domain"] == wanted]
        return rows

    @router.get("/current")
    def get_current_archetype(request: Request) -> dict[str, str]:
        current = getattr(request.app.state, "current_archetype", "default")
        return {"current": str(current or "default")}

    @router.get("/{name}")
    def get_archetype(name: str) -> dict[str, Any]:
        return _archetype_detail(name)

    @router.post("/apply/{name}")
    def apply_archetype(name: str, request: Request) -> dict[str, Any]:
        detail = _archetype_detail(name)
        event = {
            "name": name,
            "domain": detail["domain"],
            "shape": detail["shape"],
            "note": "Bootstrap centroids replaced. Learning restarts.",
        }
        applied = getattr(request.app.state, "archetype_applications", [])
        applied.append(event)
        request.app.state.archetype_applications = applied
        request.app.state.current_archetype = name
        return {
            "applied": True,
            "archetype": name,
            "current": name,
            "domain": detail["domain"],
            "preset": detail,
            "conservation_note": "Bootstrap centroids replaced. Learning restarts.",
        }

    return router


def _archetype_summary(name: str) -> dict[str, Any]:
    preset = _preset_or_404(name)
    return {
        "name": name,
        "domain": _ARCHETYPE_DOMAINS.get(name, name),
        "description": _description_for(name),
        "expected_initial_accuracy": float(preset.expected_initial_accuracy),
        "categories": list(preset.shape.category_names),
        "actions": list(preset.shape.action_names),
        "factors": list(preset.shape.factor_names),
    }


def _archetype_detail(name: str) -> dict[str, Any]:
    preset = _preset_or_404(name)
    return {
        **_archetype_summary(name),
        "shape": list(preset.shape.tensor_shape),
        "penalty_ratio": float(preset.penalty_ratio),
        "eta_confirm": float(preset.eta_confirm),
        "eta_override": float(preset.eta_override),
        "temperature": float(preset.temperature),
        "centroids": _json_centroids(preset.bootstrap_centroids),
        "calibration_note": _calibration_note_for(name),
        "calibration_notes": [
            _calibration_note_for(name),
            "Generated bootstrap centroids are a starting prior.",
            "Learning restarts from this template and must be validated by decisions.",
        ],
    }


def _preset_or_404(name: str):
    try:
        return ArchetypeGenerator.from_archetype(name, overrides=_domain_overrides(name))
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


def _domain_overrides(name: str) -> dict[str, Any] | None:
    domain = _ARCHETYPE_DOMAINS.get(name)
    preset_by_domain = {
        "soc": SOCPreset,
        "purchasing": PurchasingPreset,
        "dataops": DataOpsPreset,
        "trading": TradingPreset,
    }
    preset_cls = preset_by_domain.get(str(domain))
    if preset_cls is None:
        return None
    preset = preset_cls()
    return {
        "categories": list(preset.shape.category_names),
        "actions": list(preset.shape.action_names),
        "factors": list(preset.shape.factor_names),
        "penalty_ratio": float(preset.penalty_ratio),
    }


def _json_centroids(value: Any) -> list[Any]:
    return np.asarray(value, dtype=float).tolist()


def _description_for(name: str) -> str:
    descriptions = {
        "security_operations": "Security operations response patterns and investigation actions.",
        "source_to_pay": "Invoice, supplier, and payment exception handling patterns.",
        "dataops": "Data pipeline, quality, freshness, and operational incident patterns.",
        "financial_services": "Trading and financial exception review patterns.",
    }
    return descriptions.get(name, f"Generated archetype {name}")


def _calibration_note_for(name: str) -> str:
    notes = {
        "security_operations": "Tuned for high-cost investigation and containment environments.",
        "source_to_pay": "Tuned for invoice, supplier, and payment exception workflows.",
        "dataops": "Tuned for data quality, freshness, and operational incident workflows.",
        "financial_services": "Tuned for financial exception review and regulated trading workflows.",
    }
    return notes.get(name, "Tuned for the selected industry workflow.")
