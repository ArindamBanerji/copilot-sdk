"""AgentEvolver orchestration primitives."""

from __future__ import annotations

import uuid
from copy import copy
from dataclasses import dataclass
from typing import Any

from copilot_sdk.evolution.gate import DefaultPromotionGate
from copilot_sdk.evolution.ledger import InMemoryEvolutionLedger
from copilot_sdk.evolution.protocol import EvolutionEvent, EvolutionLedger, PromotionGate, ShadowRunner
from copilot_sdk.evolution.shadow import DefaultShadowRunner


@dataclass(frozen=True)
class PlateauConfig:
    plateau_window: int = 10
    min_improvement_rate: float = 0.2
    plateau_cooldown: int = 50

    @property
    def enabled(self) -> bool:
        return self.plateau_window > 0 and self.min_improvement_rate > 0


class AgentEvolver:
    def __init__(
        self,
        ledger: EvolutionLedger | None = None,
        shadow_runner: ShadowRunner | None = None,
        promotion_gate: PromotionGate | None = None,
        plateau_config: PlateauConfig | None = None,
    ) -> None:
        self.ledger = ledger or InMemoryEvolutionLedger()
        self.shadow_runner = shadow_runner or DefaultShadowRunner()
        self.promotion_gate = promotion_gate or DefaultPromotionGate()
        self.plateau_config = plateau_config or PlateauConfig()
        self._active_rules: dict[str, Any] = {}
        self._plateau_cooldowns: dict[str, int] = {}
        self._plateau_event_counts: dict[str, int] = {}

    def register_rule(self, rule: Any) -> None:
        self._active_rules[self._rule_name(rule)] = rule

    def get_active_rules(self) -> dict[str, Any]:
        return copy(self._active_rules)

    def evolve(
        self,
        rule_name: str,
        decisions: list[dict[str, Any]],
        conservation_state: dict[str, Any] | None = None,
        seed: Any | None = None,
    ) -> dict[str, Any]:
        baseline = self._active_rules.get(rule_name)
        if baseline is None:
            return {
                "promoted": False,
                "reason": "not_registered",
                "variant_id": None,
                "shadow_results": None,
                "gate_result": None,
            }

        plateau_result = self._plateau_result(rule_name)
        if plateau_result is not None:
            return plateau_result

        try:
            variant = baseline.generate_variant(seed) if hasattr(baseline, "generate_variant") else baseline
        except Exception as exc:
            variant_id = f"variant-{uuid.uuid4().hex[:12]}"
            metadata = {
                "reason": "generation_failed",
                "error": str(exc),
                "seed": seed,
            }
            self._record("rejected", rule_name, variant_id, metadata=metadata)
            return {
                "promoted": False,
                "reason": "generation_failed",
                "variant_id": variant_id,
                "shadow_results": {},
                "gate_result": {},
            }
        variant_id = self._variant_id(variant)
        self._record("variant_generated", rule_name, variant_id)
        self._record("shadow_started", rule_name, variant_id)
        shadow_results = self.shadow_runner.run_shadow(variant, decisions, baseline=baseline)
        self._record("shadow_completed", rule_name, variant_id, metadata=shadow_results)
        gate_result = self.promotion_gate.evaluate(shadow_results, conservation_state=conservation_state)
        if gate_result["promoted"]:
            self._active_rules[rule_name] = variant
            self._record("promoted", rule_name, variant_id, metadata=gate_result)
        else:
            self._record("rejected", rule_name, variant_id, metadata=gate_result)
        return {
            "promoted": bool(gate_result["promoted"]),
            "reason": gate_result["reason"],
            "variant_id": variant_id,
            "shadow_results": shadow_results,
            "gate_result": gate_result,
        }

    def get_evolution_history(
        self,
        rule_name: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        return self.ledger.get_events(rule_name=rule_name, limit=limit)

    def get_promoted_rules(self) -> list[str]:
        return self.ledger.get_promoted_rules()

    def reset(self) -> None:
        self.ledger.reset()

    def _record(
        self,
        event_type: str,
        rule_name: str,
        variant_id: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        self.ledger.append(
            EvolutionEvent(
                event_type=event_type,
                rule_name=rule_name,
                variant_id=variant_id,
                metadata=metadata or {},
            )
        )

    def _rule_name(self, rule: Any) -> str:
        name = getattr(rule, "name", None)
        if name:
            return str(name)
        return str(rule.__class__.__name__)

    def _variant_id(self, variant: Any) -> str:
        if isinstance(variant, dict):
            value = variant.get("variant_id")
            if value:
                return str(value)
        value = getattr(variant, "variant_id", None)
        if value:
            return str(value)
        return f"variant-{uuid.uuid4().hex[:12]}"

    def _plateau_result(self, rule_name: str) -> dict[str, Any] | None:
        if not self.plateau_config.enabled:
            return None

        cooldown = int(self._plateau_cooldowns.get(rule_name, 0))
        if cooldown > 0:
            remaining = max(cooldown - 1, 0)
            self._plateau_cooldowns[rule_name] = remaining
            return self._skipped_result(
                rule_name,
                plateau_detected=False,
                cooldown_remaining=remaining,
            )

        improvement_events = self._improvement_events(rule_name)
        if len(improvement_events) < self.plateau_config.plateau_window:
            return None
        if self._plateau_event_counts.get(rule_name) == len(improvement_events):
            return None

        recent_events = improvement_events[-self.plateau_config.plateau_window :]
        positive_count = sum(1 for event in recent_events if event["positive"])
        improvement_rate = positive_count / len(recent_events)
        if improvement_rate >= self.plateau_config.min_improvement_rate:
            return None

        cooldown = max(int(self.plateau_config.plateau_cooldown), 0)
        self._plateau_cooldowns[rule_name] = cooldown
        self._plateau_event_counts[rule_name] = len(improvement_events)
        metadata = {
            "improvement_rate": improvement_rate,
            "positive_gain_count": positive_count,
            "recent_event_count": len(recent_events),
            "plateau_window": self.plateau_config.plateau_window,
            "min_improvement_rate": self.plateau_config.min_improvement_rate,
            "cooldown": cooldown,
        }
        self._record("plateau_detected", rule_name, "plateau", metadata=metadata)
        return self._skipped_result(
            rule_name,
            plateau_detected=True,
            cooldown_remaining=cooldown,
            metadata=metadata,
        )

    def _skipped_result(
        self,
        rule_name: str,
        *,
        plateau_detected: bool,
        cooldown_remaining: int,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return {
            "promoted": False,
            "reason": "plateau_cooldown",
            "variant_id": None,
            "shadow_results": None,
            "gate_result": None,
            "plateau_detected": plateau_detected,
            "cooldown_remaining": cooldown_remaining,
            "metadata": metadata or {},
        }

    def _improvement_events(self, rule_name: str) -> list[dict[str, Any]]:
        events = self.ledger.get_events(rule_name=rule_name, limit=1000)
        improvement_events: list[dict[str, Any]] = []
        for event in events:
            metadata = event.get("metadata") if isinstance(event, dict) else None
            if not isinstance(metadata, dict):
                continue
            positive = _positive_improvement(metadata)
            if positive is None:
                continue
            improvement_events.append({"event": event, "positive": positive})
        return improvement_events


def _positive_improvement(metadata: dict[str, Any]) -> bool | None:
    for key in ("gain", "improvement", "gain_pp", "improvement_pp", "superiority_pp"):
        if key in metadata:
            try:
                return float(metadata[key]) > 0.0
            except (TypeError, ValueError):
                return None
    for key in ("better", "win"):
        if key in metadata:
            return bool(metadata[key])
    if "accuracy" in metadata and "baseline_accuracy" in metadata:
        try:
            return float(metadata["accuracy"]) > float(metadata["baseline_accuracy"])
        except (TypeError, ValueError):
            return None
    return None
