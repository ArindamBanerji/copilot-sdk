"""Trading-specific agent evolution service.

This module composes the SDK evolution primitives without modifying scorer,
GraphStore, DK, centroid, or promotion-stage systems.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from datetime import datetime, timezone
import random
from statistics import pstdev
from typing import Any, Callable

from copilot_sdk.evolution import AgentEvolver, DefaultPromotionGate, DefaultShadowRunner
from copilot_sdk.scoring.presets.trading import TradingPreset


MIN_SHADOW_BATCHES = 3
MIN_IMPROVEMENT_PP = 5.0
MAX_VARIANCE_PP = 10.0
MIN_MULTIPLIER = 0.1
MAX_MULTIPLIER = 2.0


TRADING_FACTOR_NAMES = list(TradingPreset().shape.factor_names)


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _conservation_green(state: Any) -> bool:
    if isinstance(state, str):
        return state.strip().upper() == "GREEN"
    if isinstance(state, dict):
        for key in ("status", "state", "phase"):
            value = state.get(key)
            if isinstance(value, str):
                return value.strip().upper() == "GREEN"
        if state.get("overall_safe") is True or state.get("overallSafe") is True:
            return True
    return False


def _default_conservation_state() -> dict[str, str]:
    return {"status": "unknown", "note": "conservation service not configured"}


class TradingVariantGenerator:
    """Generates Trading-specific factor-weight variants."""

    def __init__(self, factor_names: list[str] | tuple[str, ...], seed: int = 42) -> None:
        self.factor_names = list(factor_names)
        self._rng = random.Random(seed)
        self._counter = 0

    def generate(self) -> dict[str, Any]:
        self._counter += 1
        count = self._rng.randint(1, min(3, len(self.factor_names)))
        factors = self._rng.sample(self.factor_names, count)
        adjustments: dict[str, float] = {}
        for factor in factors:
            magnitude = self._rng.uniform(0.10, 0.30)
            direction = -1.0 if self._rng.random() < 0.5 else 1.0
            multiplier = 1.0 + direction * magnitude
            adjustments[factor] = round(max(MIN_MULTIPLIER, min(MAX_MULTIPLIER, multiplier)), 4)
        variant_id = f"trd-ae-{self._counter:04d}"
        return {
            "variant_id": variant_id,
            "description": f"Trading factor perturbation {self._counter}",
            "adjustments": adjustments,
            "factor_weight_adjustments": dict(adjustments),
            "category_thresholds": None,
            "regime_condition": None,
            "created_at": _now_iso(),
        }


@dataclass
class _VariantRule:
    variant: dict[str, Any]
    shadow_store: Any | None = None

    @property
    def variant_id(self) -> str:
        return str(self.variant.get("variant_id") or "unknown")

    def predict(self, decision: dict[str, Any]) -> Any:
        self._record_shadow_read(decision)
        if "variant_action" in decision:
            return decision.get("variant_action")
        if decision.get("variant_correct") is True:
            return decision.get("actual_action") or decision.get("action")
        if decision.get("variant_correct") is False:
            return decision.get("wrong_action") or "__variant_wrong__"
        adjusted_score = self.score(decision)
        if decision.get("score_mode") is True:
            return adjusted_score
        threshold = float(decision.get("variant_threshold", decision.get("threshold", 0.5)))
        return decision.get("positive_action", "strong_execution") if adjusted_score >= threshold else decision.get("negative_action", "partial_execution")

    def score(self, decision: dict[str, Any]) -> float:
        try:
            adjusted = float(decision.get("base_score", 0.0))
        except (TypeError, ValueError):
            adjusted = 0.0
        factors = decision.get("factors")
        if not isinstance(factors, dict):
            factors = decision
        adjustments = self.variant.get("factor_weight_adjustments") or self.variant.get("adjustments") or {}
        if isinstance(adjustments, dict):
            for factor, multiplier in adjustments.items():
                if factor in factors:
                    try:
                        factor_value = float(factors[factor])
                        multiplier_value = float(multiplier)
                    except (TypeError, ValueError):
                        continue
                    adjusted += factor_value * (multiplier_value - 1.0)
        return adjusted

    def _record_shadow_read(self, decision: dict[str, Any]) -> None:
        store = self.shadow_store
        if store is None:
            return
        recorder = getattr(store, "record_shadow_read", None)
        if callable(recorder):
            recorder(decision)
            return
        reads = getattr(store, "reads", None)
        if isinstance(reads, list):
            reads.append(decision)
            return
        try:
            setattr(store, "used_for_shadow", True)
        except Exception:
            return


@dataclass
class _BaselineRule:
    scorer: Any

    def predict(self, decision: dict[str, Any]) -> Any:
        if "baseline_action" in decision:
            return decision.get("baseline_action")
        if decision.get("baseline_correct") is True:
            return decision.get("actual_action") or decision.get("action")
        if decision.get("baseline_correct") is False:
            return decision.get("wrong_action") or "__baseline_wrong__"
        predictor = getattr(self.scorer, "predict", None)
        if callable(predictor):
            return predictor(decision)
        return decision.get("recommended_action") or decision.get("action")


@dataclass
class TradingAgentEvolver:
    """Trading-specific evolver using SDK evolution primitives."""

    baseline_scorer: Any
    store_factory: Callable[[], Any]
    factor_names: list[str] | tuple[str, ...] = field(default_factory=lambda: list(TRADING_FACTOR_NAMES))
    conservation_provider: Callable[[], Any] = _default_conservation_state

    def __post_init__(self) -> None:
        self._baseline = self.baseline_scorer
        self._store_factory = self.store_factory
        self._factor_names = list(self.factor_names)
        self._generator = TradingVariantGenerator(self._factor_names)
        self._shadow = DefaultShadowRunner(min_decisions=1)
        self._gate = DefaultPromotionGate(
            superiority_threshold_pp=MIN_IMPROVEMENT_PP,
            accuracy_floor=0.0,
            min_shadow_decisions=1,
        )
        self._sdk_evolver = AgentEvolver(
            shadow_runner=self._shadow,
            promotion_gate=self._gate,
        )
        self._variants: dict[str, dict[str, Any]] = {}
        self._results: dict[str, list[dict[str, Any]]] = {}
        self._log: list[dict[str, Any]] = []
        self._active_variant: dict[str, Any] | None = None
        self._last_shadow_store: Any | None = None

    @property
    def sdk_evolver(self) -> AgentEvolver:
        return self._sdk_evolver

    @property
    def last_shadow_store(self) -> Any | None:
        return self._last_shadow_store

    def generate_variant(self) -> dict[str, Any]:
        variant = self._generator.generate()
        self._variants[str(variant["variant_id"])] = variant
        self._log.append({
            "event_type": "variant_generated",
            "variant_id": variant["variant_id"],
            "status": "pending",
            "created_at": variant["created_at"],
            "variant": deepcopy(variant),
        })
        return deepcopy(variant)

    def shadow_test(
        self,
        variant: dict[str, Any],
        decisions: list[dict[str, Any]],
        batch_size: int = 50,
    ) -> dict[str, Any]:
        variant_id = str(variant.get("variant_id") or "")
        if not variant_id:
            raise ValueError("variant_id is required")
        if variant_id not in self._variants:
            self._variants[variant_id] = deepcopy(variant)

        shadow_store = self._store_factory()
        self._last_shadow_store = shadow_store
        if shadow_store is self._baseline:
            raise ValueError("shadow store must be isolated from baseline scorer")
        primary_store = getattr(self._baseline, "graph_store", None)
        if primary_store is not None and shadow_store is primary_store:
            raise ValueError("shadow store must not be primary store")

        batch_number = len(self._results.get(variant_id, [])) + 1
        batch = list(decisions[: max(1, int(batch_size))])
        shadow = self._shadow.run_shadow(
            _VariantRule(variant, shadow_store=shadow_store),
            batch,
            baseline=_BaselineRule(self._baseline),
        )
        variant_accuracy = float(shadow.get("accuracy") or 0.0)
        baseline_accuracy = float(shadow.get("baseline_accuracy") or 0.0)
        improvement_pp = round((variant_accuracy - baseline_accuracy) * 100.0, 4)
        conservation_state = self.conservation_provider()
        conservation_safe = _conservation_green(conservation_state)
        result = {
            "variant_id": variant_id,
            "batch_number": batch_number,
            "decisions_tested": int(shadow.get("total") or len(batch)),
            "variant_accuracy": round(variant_accuracy, 4),
            "baseline_accuracy": round(baseline_accuracy, 4),
            "improvement_pp": improvement_pp,
            "conservation_safe": conservation_safe,
            "conservation_state": conservation_state,
            "shadow_store_isolated": shadow_store is not self._baseline and shadow_store is not primary_store,
        }
        self._results.setdefault(variant_id, []).append(result)
        self._log.append({
            "event_type": "shadow_completed",
            "variant_id": variant_id,
            "status": "evaluating",
            "created_at": _now_iso(),
            "result": deepcopy(result),
        })
        return deepcopy(result)

    def check_promotion(self, variant_id: str) -> dict[str, Any]:
        results = list(self._results.get(str(variant_id), []))
        batches = len(results)
        if batches < MIN_SHADOW_BATCHES:
            return {
                "promotable": False,
                "reason": "insufficient_batches",
                "batches": batches,
            }
        improvements = [float(result["improvement_pp"]) for result in results]
        if any(value < MIN_IMPROVEMENT_PP for value in improvements):
            return {
                "promotable": False,
                "reason": "insufficient_improvement",
                "batches": batches,
            }
        conservation_state = self.conservation_provider()
        if not _conservation_green(conservation_state):
            return {
                "promotable": False,
                "reason": "conservation_not_green",
                "batches": batches,
            }
        variance_pp = pstdev(improvements) if len(improvements) > 1 else 0.0
        if variance_pp >= MAX_VARIANCE_PP:
            return {
                "promotable": False,
                "reason": "unstable_improvement",
                "batches": batches,
                "variance_pp": round(variance_pp, 4),
            }
        aggregate_shadow = {
            "sufficient": True,
            "total": sum(int(result["decisions_tested"]) for result in results),
            "accuracy": sum(float(result["variant_accuracy"]) for result in results) / batches,
            "baseline_accuracy": sum(float(result["baseline_accuracy"]) for result in results) / batches,
        }
        gate_result = self._gate.evaluate(aggregate_shadow, conservation_state=conservation_state)
        return {
            "promotable": bool(gate_result.get("promoted")),
            "reason": "promotable" if gate_result.get("promoted") else str(gate_result.get("reason")),
            "batches": batches,
            "variance_pp": round(variance_pp, 4),
            "avg_improvement_pp": round(sum(improvements) / batches, 4),
            "gate_result": gate_result,
        }

    def promote(self, variant_id: str) -> dict[str, Any]:
        variant_id = str(variant_id)
        check = self.check_promotion(variant_id)
        if not check.get("promotable"):
            return {
                "promoted": False,
                "reason": check.get("reason", "not_promotable"),
                "adjustments": {},
                "check": check,
            }
        conservation_state = self.conservation_provider()
        if not _conservation_green(conservation_state):
            return {
                "promoted": False,
                "reason": "conservation_not_green",
                "adjustments": {},
                "check": check,
            }
        variant = self._variants.get(variant_id)
        if not variant:
            return {
                "promoted": False,
                "reason": "variant_not_found",
                "adjustments": {},
                "check": check,
            }
        self._active_variant = deepcopy(variant)
        self._log.append({
            "event_type": "promoted",
            "variant_id": variant_id,
            "status": "promoted",
            "created_at": _now_iso(),
            "check": deepcopy(check),
        })
        return {
            "promoted": True,
            "reason": "promoted",
            "adjustments": dict(variant.get("adjustments") or {}),
            "check": check,
        }

    def evolution_log(self) -> list[dict[str, Any]]:
        variants = []
        for variant_id, variant in self._variants.items():
            results = self._results.get(variant_id, [])
            improvements = [float(result["improvement_pp"]) for result in results]
            status = "promoted" if self._active_variant and self._active_variant.get("variant_id") == variant_id else "evaluating"
            if not results:
                status = "pending"
            variants.append({
                "variant_id": variant_id,
                "description": variant.get("description", ""),
                "created_at": variant.get("created_at"),
                "adjustments": dict(variant.get("adjustments") or {}),
                "batches": len(results),
                "avg_improvement_pp": round(sum(improvements) / len(improvements), 4) if improvements else 0.0,
                "status": status,
                "results": deepcopy(results),
            })
        return variants

    def active_variant(self) -> dict[str, Any] | None:
        return deepcopy(self._active_variant) if self._active_variant else None


class _DefaultBaseline:
    graph_store = object()

    def predict(self, decision: dict[str, Any]) -> Any:
        return decision.get("recommended_action") or decision.get("action")


def create_default_trading_evolver() -> TradingAgentEvolver:
    return TradingAgentEvolver(
        baseline_scorer=_DefaultBaseline(),
        store_factory=lambda: object(),
        factor_names=TRADING_FACTOR_NAMES,
    )
