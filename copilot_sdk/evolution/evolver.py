"""AgentEvolver orchestration primitives."""

from __future__ import annotations

import uuid
from copy import copy
from typing import Any

from copilot_sdk.evolution.gate import DefaultPromotionGate
from copilot_sdk.evolution.ledger import InMemoryEvolutionLedger
from copilot_sdk.evolution.protocol import EvolutionEvent, EvolutionLedger, PromotionGate, ShadowRunner
from copilot_sdk.evolution.shadow import DefaultShadowRunner


class AgentEvolver:
    def __init__(
        self,
        ledger: EvolutionLedger | None = None,
        shadow_runner: ShadowRunner | None = None,
        promotion_gate: PromotionGate | None = None,
    ) -> None:
        self.ledger = ledger or InMemoryEvolutionLedger()
        self.shadow_runner = shadow_runner or DefaultShadowRunner()
        self.promotion_gate = promotion_gate or DefaultPromotionGate()
        self._active_rules: dict[str, Any] = {}

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
        return rule.__class__.__name__

    def _variant_id(self, variant: Any) -> str:
        if isinstance(variant, dict):
            value = variant.get("variant_id")
            if value:
                return str(value)
        value = getattr(variant, "variant_id", None)
        if value:
            return str(value)
        return f"variant-{uuid.uuid4().hex[:12]}"
