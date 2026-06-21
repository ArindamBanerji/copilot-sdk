"""Category-level promotion state for Trading."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any


class PromotionStage(str, Enum):
    PAPER = "paper"
    SMALL_LIVE = "small_live"
    FULL_LIVE = "full_live"


@dataclass(frozen=True)
class StageConfig:
    stage: PromotionStage
    min_decisions: int
    min_accuracy: float
    conservation_required: bool
    max_sizing_pct: float


STAGE_CONFIGS = {
    PromotionStage.PAPER: StageConfig(PromotionStage.PAPER, 50, 0.55, False, 0.0),
    PromotionStage.SMALL_LIVE: StageConfig(PromotionStage.SMALL_LIVE, 100, 0.58, True, 2.0),
    PromotionStage.FULL_LIVE: StageConfig(PromotionStage.FULL_LIVE, 200, 0.60, True, 5.0),
}

STAGE_ORDER = [
    PromotionStage.PAPER,
    PromotionStage.SMALL_LIVE,
    PromotionStage.FULL_LIVE,
]


@dataclass
class PromotionState:
    category: str
    current_stage: PromotionStage = PromotionStage.PAPER
    decisions_in_stage: int = 0
    accuracy_in_stage: float = 0.0
    promoted_at: str | None = None
    demoted_at: str | None = None
    promotion_history: list[dict[str, Any]] = field(default_factory=list)
    stage_start_count: int = 0


class PromotionStateStore:
    """File-backed state store for category promotion stage and history."""

    def __init__(self, persist_path: str | Path | None = None) -> None:
        self._states: dict[str, PromotionState] = {}
        self._path = Path(persist_path) if persist_path else None
        if self._path and self._path.exists():
            self._load()

    def _load(self) -> None:
        if self._path is None:
            return
        try:
            payload = json.loads(self._path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return
        if not isinstance(payload, dict):
            return
        for category, state_dict in payload.items():
            if not isinstance(state_dict, dict):
                continue
            try:
                current_stage = PromotionStage(str(state_dict.get("current_stage", PromotionStage.PAPER.value)))
            except ValueError:
                current_stage = PromotionStage.PAPER
            history = state_dict.get("promotion_history", [])
            self._states[str(category)] = PromotionState(
                category=str(category),
                current_stage=current_stage,
                decisions_in_stage=int(state_dict.get("decisions_in_stage", 0) or 0),
                accuracy_in_stage=float(state_dict.get("accuracy_in_stage", 0.0) or 0.0),
                promoted_at=state_dict.get("promoted_at") if state_dict.get("promoted_at") else None,
                demoted_at=state_dict.get("demoted_at") if state_dict.get("demoted_at") else None,
                promotion_history=history if isinstance(history, list) else [],
                stage_start_count=int(state_dict.get("stage_start_count", 0) or 0),
            )

    def _save(self) -> None:
        if self._path is None:
            return
        data = {
            category: {
                "current_stage": state.current_stage.value,
                "decisions_in_stage": state.decisions_in_stage,
                "accuracy_in_stage": state.accuracy_in_stage,
                "promoted_at": state.promoted_at,
                "demoted_at": state.demoted_at,
                "promotion_history": state.promotion_history,
                "stage_start_count": state.stage_start_count,
            }
            for category, state in sorted(self._states.items())
        }
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")

    def get(self, category: str) -> PromotionState:
        key = str(category)
        if key not in self._states:
            self._states[key] = PromotionState(category=key)
        return self._states[key]

    def all(self) -> list[PromotionState]:
        return [self._states[key] for key in sorted(self._states)]

    def save(self) -> None:
        self._save()
