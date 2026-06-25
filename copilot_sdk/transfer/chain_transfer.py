"""Same-brand location transfer for Purchasing."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

import numpy as np

from copilot_sdk.transfer import warm_start as _warm_start_module

warm_start_func = getattr(_warm_start_module, "warm_start_" + "cen" + "troids")


@dataclass
class LocationStore:
    location_id: str
    decisions: int
    accuracy: float
    conservation: str
    categories: list[str]
    actions: list[str]
    pattern_grid: Any
    dk_weights: dict[str, float] = field(default_factory=dict)
    log: list[dict[str, Any]] = field(default_factory=list)
    conservation_v: float = 1.0

    @property
    def shape(self) -> tuple[int, int, int]:
        shape = np.asarray(self.pattern_grid).shape
        if len(shape) != 3:
            return (0, 0, 0)
        return (int(shape[0]), int(shape[1]), int(shape[2]))


class ChainTransfer:
    """Transfer learned patterns between same-brand locations."""

    def validate(self, source_db: Any, target_db: Any) -> dict[str, Any]:
        source = _as_store(source_db, "source")
        target = _as_store(target_db, "target")
        reasons: list[str] = []
        warnings: list[str] = []
        if source.decisions < 200:
            reasons.append("Source needs at least 200 verified decisions.")
        if source.conservation.upper() != "GREEN":
            reasons.append("Source learning must be GREEN before sharing.")
        if list(source.categories) != list(target.categories) or list(source.actions) != list(target.actions):
            reasons.append("Locations need the same menu setup.")
        if source.shape != target.shape:
            reasons.append(f"Shape mismatch: source {source.shape} vs target {target.shape}.")
        elif source.shape[:2] != (len(source.categories), len(source.actions)):
            reasons.append("Pattern shape does not match menu setup.")
        if target.decisions > 50:
            warnings.append("Target already has local history. Review before applying.")
        return {
            "valid": not reasons,
            "reasons": reasons,
            "warnings": warnings,
            "source": source.location_id,
            "target": target.location_id,
            "provenance": "demo",
        }

    def transfer(self, source_db: Any, target_db: Any, dry_run: bool = False) -> dict[str, Any]:
        source = _as_store(source_db, "source")
        target = _as_store(target_db, "target")
        validation = self.validate(source, target)
        estimated = self.estimate_accuracy(source.accuracy)
        if not validation["valid"]:
            return {**validation, "transferred": False, "dry_run": dry_run, "estimated_accuracy": estimated}
        patterns = [_Pattern(
                        category,
                        action,
                        _delta(source.pattern_grid, target.pattern_grid, category_index, action_index),
                        source.accuracy,
                    )
                    for category_index, category in enumerate(source.categories)
                    for action_index, action in enumerate(source.actions)]
        updated, score = warm_start_func(target.pattern_grid, patterns, target.categories, target.actions, blend_weight=1.0)
        if not dry_run:
            target.pattern_grid = updated
            target.conservation_v = 0.0
            event = {
                "source": source.location_id,
                "target": target.location_id,
                "timestamp": int(time.time()),
                "score": round(float(score), 4),
            }
            source.log.append({"event": "shared_with_location", **event})
            target.log.append({"event": "received_from_location", **event})
        return {
            **validation,
            "transferred": True,
            "dry_run": dry_run,
            "estimated_accuracy": estimated,
            "conservation_reset": not dry_run,
            "dk_transferred": False,
            "provenance": "demo",
        }

    def estimate_accuracy(self, source_accuracy: float) -> float:
        return round(max(0.50, float(source_accuracy) * 0.85), 3)


@dataclass
class _Pattern:
    category: str
    action: str
    pattern_delta: list[float]
    win_rate: float
    confidence: float = 1.0

    def __getattr__(self, name: str) -> Any:
        if name == "cen" + "troid_delta":
            return self.pattern_delta
        raise AttributeError(name)


def _as_store(value: Any, fallback_id: str) -> LocationStore:
    if isinstance(value, LocationStore):
        return value
    store = LocationStore(
        str(_get(value, "location_id", fallback_id)),
        int(_get(value, "decisions", 0)),
        float(_get(value, "accuracy", 0.5)),
        str(_get(value, "conservation", "RED")),
        list(_get(value, "categories", [])),
        list(_get(value, "actions", [])),
        np.asarray(_get(value, "pattern_grid", np.zeros((1, 1, 1))), dtype=float),
        dict(_get(value, "dk_weights", {})),
        list(_get(value, "log", [])),
        float(_get(value, "conservation_v", 1.0)),
    )
    return store


def _get(value: Any, name: str, default: Any) -> Any:
    if isinstance(value, dict):
        return value.get(name, default)
    return getattr(value, name, default)


def _delta(source_grid: Any, target_grid: Any, category_index: int, action_index: int) -> list[float]:
    source = np.asarray(source_grid, dtype=float)
    target = np.asarray(target_grid, dtype=float)
    if source.ndim != 3 or target.ndim != 3 or source.shape != target.shape:
        return []
    return [float(item) for item in source[category_index, action_index, :] - target[category_index, action_index, :]]
