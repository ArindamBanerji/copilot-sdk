"""Conservation-gated category promotion engine for Trading."""

from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone
from typing import Any

from copilot_sdk.scoring.presets.trading import TradingPreset

from app.services.promotion_state import (
    STAGE_CONFIGS,
    STAGE_ORDER,
    PromotionStage,
    PromotionState,
    PromotionStateStore,
)


DEMOTION_WINDOW = 20
DEMOTION_FLOOR = 0.50


class PromotionEngine:
    """Conservation-gated strategy promotion pipeline."""

    def __init__(
        self,
        graph_store: Any,
        preset: Any | None = None,
        conservation_status: dict[str, Any] | None = None,
        *,
        state_store: PromotionStateStore | None = None,
        domain: str = "trading",
    ) -> None:
        self._store = graph_store
        self._preset = preset or TradingPreset()
        self._conservation = conservation_status or {}
        self._states = state_store or PromotionStateStore()
        self._domain = domain
        self._categories = tuple(self._preset.shape.category_names)

    def evaluate(self, category: str) -> dict[str, Any]:
        """Evaluate category readiness for the next promotion stage."""

        state = self.get_state(category)
        self._refresh_state_metrics(state)
        if state.current_stage != PromotionStage.PAPER:
            conservation = _category_status(self._conservation, category)
            if conservation == "RED":
                self.demote(category, "conservation RED")
                state = self.get_state(category)
                self._refresh_state_metrics(state)

        next_stage = _next_stage(state.current_stage)
        evidence = self._evidence(state)
        if next_stage is None:
            return self._evaluation_payload(
                state,
                next_stage=None,
                ready=False,
                blockers=[],
                evidence=evidence,
                recommendation="Fully promoted.",
            )

        config = STAGE_CONFIGS[state.current_stage]
        blockers = self._blockers(state, config)
        ready = len(blockers) == 0
        recommendation = (
            _ready_recommendation(state, next_stage, evidence)
            if ready
            else _blocked_recommendation(blockers)
        )
        return self._evaluation_payload(
            state,
            next_stage=next_stage,
            ready=ready,
            blockers=blockers,
            evidence=evidence,
            recommendation=recommendation,
        )

    def promote(self, category: str, confirmed_by: str = "trader") -> dict[str, Any]:
        """Promote a category after trader confirmation."""

        evaluation = self.evaluate(category)
        if not evaluation["ready"] or evaluation["next_stage"] is None:
            raise ValueError(str(evaluation["recommendation"]))

        state = self.get_state(category)
        from_stage = state.current_stage
        to_stage = PromotionStage(str(evaluation["next_stage"]))
        now = _now()
        event = {
            "action": "promote",
            "category": category,
            "from_stage": from_stage.value,
            "to_stage": to_stage.value,
            "confirmed_by": confirmed_by,
            "timestamp": now,
            "evidence": evaluation["evidence"],
        }
        total_verified = len(self._category_decisions(category))
        state.current_stage = to_stage
        state.decisions_in_stage = 0
        state.accuracy_in_stage = 0.0
        state.promoted_at = now
        state.demoted_at = None
        state.stage_start_count = total_verified
        state.promotion_history.append(event)
        self._states.save()
        return {
            "promoted": True,
            "category": category,
            "from_stage": from_stage.value,
            "current_stage": to_stage.value,
            "history_entry": event,
        }

    def demote(self, category: str, reason: str) -> dict[str, Any]:
        """Demote a category to the previous stage."""

        state = self.get_state(category)
        from_stage = state.current_stage
        to_stage = _previous_stage(from_stage)
        if from_stage == to_stage:
            return {
                "demoted": False,
                "category": category,
                "from_stage": from_stage.value,
                "current_stage": to_stage.value,
                "reason": "already at lowest stage",
                "history_entry": None,
            }
        now = _now()
        event = {
            "action": "demote",
            "category": category,
            "from_stage": from_stage.value,
            "to_stage": to_stage.value,
            "reason": reason,
            "timestamp": now,
            "evidence": self._evidence(state),
        }
        state.current_stage = to_stage
        state.decisions_in_stage = 0
        state.accuracy_in_stage = 0.0
        state.demoted_at = now
        state.stage_start_count = len(self._category_decisions(category))
        state.promotion_history.append(event)
        self._states.save()
        return {
            "demoted": from_stage != to_stage,
            "category": category,
            "from_stage": from_stage.value,
            "current_stage": to_stage.value,
            "reason": reason,
            "history_entry": event,
        }

    def get_state(self, category: str) -> PromotionState:
        return self._states.get(str(category))

    def dashboard(self) -> list[dict[str, Any]]:
        """Return all configured categories with readiness and sizing caps."""

        return [self.evaluate(category) for category in self._categories]

    def _blockers(self, state: PromotionState, config: Any) -> list[str]:
        blockers: list[str] = []
        if state.decisions_in_stage < config.min_decisions:
            blockers.append(f"Need {config.min_decisions - state.decisions_in_stage} more decisions.")
        if state.accuracy_in_stage < config.min_accuracy:
            blockers.append(f"Need accuracy of at least {_percent(config.min_accuracy)}.")
        conservation = _category_status(self._conservation, state.category)
        if config.conservation_required and conservation != "GREEN":
            blockers.append(f"Conservation {conservation}.")
        return blockers

    def _refresh_state_metrics(self, state: PromotionState) -> None:
        decisions = self._category_decisions(state.category)
        stage_decisions = decisions[state.stage_start_count :]
        state.decisions_in_stage = len(stage_decisions)
        state.accuracy_in_stage = _accuracy(stage_decisions)
        if (
            state.current_stage != PromotionStage.PAPER
            and state.decisions_in_stage >= DEMOTION_WINDOW
            and state.accuracy_in_stage < DEMOTION_FLOOR
        ):
            self.demote(state.category, "accuracy below sustained floor")

    def _category_decisions(self, category: str) -> list[dict[str, Any]]:
        reader = getattr(self._store, "get_verified_decisions", None)
        if not callable(reader):
            return []
        decisions = reader(domain=self._domain)
        rows = [
            decision
            for decision in decisions
            if isinstance(decision, dict) and str(decision.get("category") or "") == category
        ]
        return sorted(rows, key=_decision_sort_key)

    def _evidence(self, state: PromotionState) -> dict[str, Any]:
        config = STAGE_CONFIGS[state.current_stage]
        conservation = _category_status(self._conservation, state.category)
        return {
            "decisions_in_stage": state.decisions_in_stage,
            "accuracy_in_stage": state.accuracy_in_stage,
            "min_decisions": config.min_decisions,
            "min_accuracy": config.min_accuracy,
            "conservation_status": conservation,
            "max_sizing_pct": config.max_sizing_pct,
        }

    def _evaluation_payload(
        self,
        state: PromotionState,
        *,
        next_stage: PromotionStage | None,
        ready: bool,
        blockers: list[str],
        evidence: dict[str, Any],
        recommendation: str,
    ) -> dict[str, Any]:
        config = STAGE_CONFIGS[state.current_stage]
        return {
            "category": state.category,
            "current_stage": state.current_stage.value,
            "current_stage_label": _stage_label(state.current_stage),
            "next_stage": next_stage.value if next_stage else None,
            "next_stage_label": _stage_label(next_stage) if next_stage else None,
            "ready": ready,
            "evidence": evidence,
            "recommendation": recommendation,
            "blockers": blockers,
            "max_sizing_pct": config.max_sizing_pct,
            "state": _state_payload(state),
        }


def _state_payload(state: PromotionState) -> dict[str, Any]:
    payload = asdict(state)
    payload["current_stage"] = state.current_stage.value
    return payload


def _accuracy(decisions: list[dict[str, Any]]) -> float:
    if not decisions:
        return 0.0
    correct = sum(1 for decision in decisions if bool(decision.get("is_correct")))
    return round(correct / len(decisions), 4)


def _category_status(conservation_status: dict[str, Any], category: str) -> str:
    categories = conservation_status.get("categories")
    value: Any = None
    if isinstance(categories, dict):
        value = categories.get(category)
    if value is None:
        value = conservation_status.get(category)
    if isinstance(value, dict):
        value = value.get("status") or value.get("conservation_status")
    if value is None:
        value = conservation_status.get("status") or conservation_status.get("conservation_status")
    text = str(value or "UNKNOWN").strip().upper()
    return text if text else "UNKNOWN"


def _next_stage(stage: PromotionStage) -> PromotionStage | None:
    index = STAGE_ORDER.index(stage)
    if index >= len(STAGE_ORDER) - 1:
        return None
    return STAGE_ORDER[index + 1]


def _previous_stage(stage: PromotionStage) -> PromotionStage:
    index = STAGE_ORDER.index(stage)
    return STAGE_ORDER[max(0, index - 1)]


def _stage_label(stage: PromotionStage | None) -> str | None:
    if stage is None:
        return None
    return {
        PromotionStage.PAPER: "paper trading",
        PromotionStage.SMALL_LIVE: "small position",
        PromotionStage.FULL_LIVE: "full position",
    }[stage]


def _ready_recommendation(
    state: PromotionState,
    next_stage: PromotionStage,
    evidence: dict[str, Any],
) -> str:
    conservation = evidence["conservation_status"]
    return (
        f"Ready to promote to {_stage_label(next_stage)}. "
        f"{state.decisions_in_stage} trades, {_percent(state.accuracy_in_stage)}, {conservation}."
    )


def _blocked_recommendation(blockers: list[str]) -> str:
    if not blockers:
        return "Keep collecting verified decisions."
    return " ".join(blockers)


def _percent(value: float) -> str:
    return f"{round(float(value) * 100)}%"


def _decision_sort_key(decision: dict[str, Any]) -> tuple[float, str]:
    created = decision.get("created_at") or decision.get("verified_at") or 0.0
    try:
        timestamp = float(created)
    except (TypeError, ValueError):
        timestamp = 0.0
    return timestamp, str(decision.get("decision_id") or "")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()
