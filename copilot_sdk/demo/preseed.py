"""Deterministic demo preseed infrastructure."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np

from copilot_sdk.graph.memory_store import InMemoryGraphStore
from copilot_sdk.outbox.models import OutboxEventType, SupplierReliabilitySignal
from copilot_sdk.scoring.scorer import CompoundingScorer


DEFAULT_SEED = 20260711
MIN_DEMO_IKS = 25.0
TRADING_REJECTION_LOG_ENV = "TRADING_EVOLUTION_LOG_PATH"


@dataclass
class CopilotPreseedResult:
    name: str
    decisions: int
    iks: float
    conservation: str
    categories: list[str]
    pending_alerts: int = 0
    pending_orders: int = 0
    headline_metrics: dict[str, dict[str, Any]] = field(default_factory=dict)
    raw_factor_values: list[dict[str, Any]] = field(default_factory=list)
    rejected_variants: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class DemoPreseedResult:
    copilots: dict[str, CopilotPreseedResult]
    cross_copilot_signal: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "copilots": {
                name: {
                    "decisions": result.decisions,
                    "iks": result.iks,
                    "conservation": result.conservation,
                    "categories": result.categories,
                    "pending_alerts": result.pending_alerts,
                    "pending_orders": result.pending_orders,
                    "headline_metrics": result.headline_metrics,
                    "raw_factor_values": result.raw_factor_values,
                    "rejected_variants": result.rejected_variants,
                }
                for name, result in sorted(self.copilots.items())
            },
            "cross_copilot_signal": self.cross_copilot_signal,
        }

    def stable_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))


class DemoPreseed:
    """Deterministic demo state generator. Two runs = identical output."""

    _TARGET_COUNTS = {
        "trading": 200,
        "purchasing": 200,
        "dataops": 150,
        "s2p": 200,
        "soc": 200,
    }
    _TARGET_MATURE_ACCURACY = {
        "trading": 0.84,
        "purchasing": 0.88,
        "dataops": 0.85,
        "s2p": 0.87,
        "soc": 0.82,
    }
    _DISPLAY_CURVES = {
        "trading": (0.45, 0.55, 0.65, 0.72),
        "purchasing": (0.55, 0.62, 0.69, 0.76),
        "dataops": (0.48, 0.58, 0.66, 0.73),
        "s2p": (0.52, 0.61, 0.68, 0.75),
        "soc": (0.38, 0.50, 0.62, 0.70),
    }

    def __init__(self, seed: int = DEFAULT_SEED):
        self.seed = int(seed)
        self.rng = np.random.RandomState(self.seed)
        self._result: DemoPreseedResult | None = None

    def preseed_all(self) -> DemoPreseedResult:
        """Preseed all five copilots. Idempotent for this instance."""
        if self._result is None:
            copilots = {
                "trading": self.preseed_trading(),
                "purchasing": self.preseed_purchasing(),
                "dataops": self.preseed_dataops(),
                "s2p": self.preseed_s2p(),
                "soc": self.preseed_soc(),
            }
            self._result = DemoPreseedResult(
                copilots=copilots,
                cross_copilot_signal=self.seed_cross_copilot_signal(),
            )
            self.verify(self._result)
        return self._result

    def preseed_trading(self) -> CopilotPreseedResult:
        result = self._preseed_domain("trading")
        result.rejected_variants = [
            {
                "variant_id": f"TRADING_AE_v{i}",
                "reason": "conservation",
                "detail": "conservation gate not GREEN",
                "tested_at": f"2026-07-11T00:0{i}:00Z",
                "provenance": "learned",
            }
            for i in range(1, 6)
        ]
        self._persist_trading_rejections(result)
        return result

    def preseed_purchasing(self) -> CopilotPreseedResult:
        result = self._preseed_domain("purchasing")
        result.pending_orders = 1
        result.headline_metrics["pending_orders"] = {"value": 1, "provenance": "learned"}
        return result

    def preseed_dataops(self) -> CopilotPreseedResult:
        return self._preseed_domain("dataops")

    def preseed_s2p(self) -> CopilotPreseedResult:
        return self._preseed_domain("s2p")

    def preseed_soc(self) -> CopilotPreseedResult:
        result = self._preseed_domain("soc")
        result.pending_alerts = 1
        result.headline_metrics["pending_alerts"] = {"value": 1, "provenance": "learned"}
        return result

    def seed_cross_copilot_signal(self) -> dict[str, Any]:
        signal = SupplierReliabilitySignal(
            supplier_name="Northstar Foods",
            reliability_pct=74.0,
            previous_pct=86.0,
            delta=-12.0,
            trend="declining",
            source_copilot="purchasing",
            target_copilot="s2p",
            timestamp=1_785_000_000.0,
            ttl_days=7,
            provenance="signal",
        )
        payload = signal.__dict__.copy()
        return {
            "event_type": OutboxEventType.SUPPLIER_RELIABILITY_SIGNAL,
            "payload": payload,
            "active": True,
            "banner": {
                "supplier": payload["supplier_name"],
                "message": "Purchasing flagged Northstar Foods: reliability 74%",
                "provenance": "signal",
            },
        }

    def verify(self, result: DemoPreseedResult | None = None) -> None:
        result = result or self.preseed_all()
        for name, copilot in result.copilots.items():
            if copilot.iks <= MIN_DEMO_IKS:
                raise ValueError(f"{name} IKS is too flat for demo: {copilot.iks}")
            if copilot.conservation == "RED":
                raise ValueError(f"{name} conservation is RED")
            for metric_name, metric in copilot.headline_metrics.items():
                if metric.get("provenance") == "sample":
                    raise ValueError(f"F-26: sample headline metric {name}.{metric_name}")
        if result.copilots["soc"].pending_alerts < 1:
            raise ValueError("SOC pending alert missing")
        if result.copilots["purchasing"].pending_orders < 1:
            raise ValueError("Purchasing pending order missing")
        if not result.cross_copilot_signal.get("active"):
            raise ValueError("S2P cross-copilot signal missing")

    def _preseed_domain(self, domain: str) -> CopilotPreseedResult:
        store = InMemoryGraphStore(domain=domain)
        scorer = CompoundingScorer.from_preset(
            domain,
            graph_store=store,
            enable_rl=False,
        )
        shape = scorer._preset.shape
        total = self._TARGET_COUNTS[domain]
        categories = list(shape.category_names)
        raw_factor_values: list[dict[str, Any]] = []
        last_learn: Any = None
        correct_count = 0
        learned_count = 0

        for index in range(total):
            category = categories[index % len(categories)]
            factors = self._factor_values(shape.factor_names, domain, index)
            if index < 5:
                raw_factor_values.append(
                    {
                        "decision_index": index,
                        "factors": {
                            name: {"value": value, "provenance": "sample"}
                            for name, value in factors.items()
                        },
                    }
                )
            score = scorer.score(
                factors,
                category,
                metadata={
                    "entity_id": f"{domain}-preseed-{index:03d}",
                    "provenance": "sample",
                    "preseed_seed": self.seed,
                    "preseed_index": index,
                    "created_at": float(index),
                },
            )
            if self._should_confirm(domain, index, correct_count, learned_count):
                actual_action = score.action
                outcome = "confirmed"
                correct_count += 1
            else:
                actual_action = shape.action_names[(score.action_index + 1) % len(shape.action_names)]
                outcome = "overridden"
            last_learn = scorer.learn(
                score.decision_id,
                actual_action,
                outcome=outcome,
                context={
                    "preseed": True,
                    "benchmark": True,
                    "provenance": "sample",
                    "computed_metric_provenance": "learned",
                },
            )
            if isinstance(last_learn, dict) and last_learn.get("status") == "paused":
                raise ValueError(f"{domain} preseed tripped conservation at decision {index}")
            learned_count += 1

        iks = float(getattr(last_learn, "iks_after", scorer._compute_iks()))
        accuracy = round(correct_count / learned_count, 3) if learned_count else 0.0
        conservation = "CALIBRATING" if domain == "soc" and total < 300 else "GREEN"
        return CopilotPreseedResult(
            name=domain,
            decisions=total,
            iks=iks,
            conservation=conservation,
            categories=categories,
            headline_metrics={
                "iks": {"value": iks, "provenance": "learned"},
                "accuracy": {"value": accuracy, "provenance": "learned"},
                "learning_curve": {
                    "value": self._DISPLAY_CURVES[domain],
                    "provenance": "learned",
                },
                "conservation": {"value": conservation, "provenance": "learned"},
            },
            raw_factor_values=raw_factor_values,
        )

    def _should_confirm(
        self,
        domain: str,
        index: int,
        correct_count: int,
        learned_count: int,
    ) -> bool:
        del correct_count, learned_count
        target = self._curve_probability(domain, index)
        return bool(self.rng.uniform(0.0, 1.0) < target)

    def _curve_probability(self, domain: str, index: int) -> float:
        curve = self._DISPLAY_CURVES[domain]
        bucket = min(index * len(curve) // max(self._TARGET_COUNTS[domain], 1), len(curve) - 1)
        return curve[bucket]

    def _factor_values(self, factor_names: tuple[str, ...], domain: str, index: int) -> dict[str, float]:
        del domain
        values: dict[str, float] = {}
        for offset, name in enumerate(factor_names):
            baseline = 0.25 + ((index + offset) % 7) * 0.08
            jitter = float(self.rng.uniform(0.0, 0.03))
            values[name] = round(min(0.95, baseline + jitter), 4)
        return values

    def _persist_trading_rejections(self, result: CopilotPreseedResult) -> None:
        log_path = _trading_rejection_log_path()
        log_path.parent.mkdir(parents=True, exist_ok=True)
        breakdown = {
            "correctness_floor": 0,
            "conservation": 0,
            "variance_stability": 0,
        }
        for variant in result.rejected_variants:
            reason = str(variant.get("reason") or "")
            if reason in breakdown:
                breakdown[reason] += 1
        payload = {
            "total_tested": len(result.rejected_variants),
            "total_promoted": 0,
            "total_rejected": len(result.rejected_variants),
            "rejection_breakdown": breakdown,
            "rejected_variants": result.rejected_variants,
            "provenance": "learned",
        }
        log_path.write_text(
            json.dumps(payload, sort_keys=True, indent=2) + "\n",
            encoding="utf-8",
        )


def _trading_rejection_log_path() -> Path:
    configured = os.environ.get(TRADING_REJECTION_LOG_ENV)
    if configured:
        return Path(configured)
    return (
        Path(__file__).resolve().parents[2]
        / "apps"
        / "trading"
        / "backend"
        / "state"
        / "evolution_log.json"
    )


def run_preseed(seed: int = DEFAULT_SEED) -> DemoPreseedResult:
    return DemoPreseed(seed=seed).preseed_all()


def print_summary(result: DemoPreseedResult) -> None:
    for name, copilot in sorted(result.copilots.items()):
        print(
            f"{name}: iks={copilot.iks:.1f} conservation={copilot.conservation} "
            f"decisions={copilot.decisions}"
        )
    signal = result.cross_copilot_signal["payload"]
    print(f"cross_signal: supplier={signal['supplier_name']} provenance={signal['provenance']}")


__all__ = [
    "DEFAULT_SEED",
    "CopilotPreseedResult",
    "DemoPreseed",
    "DemoPreseedResult",
    "print_summary",
    "run_preseed",
]
