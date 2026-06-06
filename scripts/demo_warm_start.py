"""Run a local warm-start transfer demo.

Usage:
    python scripts/demo_warm_start.py
"""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any

from copilot_sdk.scoring.scorer import CompoundingScorer
from copilot_sdk.transfer import SharedPatternRegistry, TransferPattern


SOURCE_COPILOT = "dataops"
TARGET_COPILOT = "trading"


def build_transfer_registry() -> SharedPatternRegistry:
    registry = SharedPatternRegistry()
    registry.register(
        TransferPattern(
            pattern_id="",
            source_copilot=SOURCE_COPILOT,
            pattern_type="centroid_delta",
            category="freshness_violation",
            action="strong_execution",
            win_rate=0.78,
            centroid_delta=[0.05, 0.03, 0.04, 0.02, 0.01, 0.03, 0.0, 0.0, 0.0, 0.0],
            confidence=0.86,
            metadata={
                "source_rule": "freshness_violation_signal",
                "source_action": "auto_approve",
                "target_action": "strong_execution",
            },
        )
    )
    registry.register(
        TransferPattern(
            pattern_id="",
            source_copilot=SOURCE_COPILOT,
            pattern_type="centroid_delta",
            category="pipeline_failure",
            action="partial_execution",
            win_rate=0.72,
            centroid_delta=[0.02, 0.04, 0.01, 0.03, 0.05, 0.02, 0.0, 0.0, 0.0, 0.0],
            confidence=0.81,
            metadata={
                "source_rule": "pipeline_failure_risk",
                "source_action": "investigate",
                "target_action": "partial_execution",
            },
        )
    )
    return registry


def run_demo() -> dict[str, Any]:
    db_dir = Path(tempfile.mkdtemp())
    source = CompoundingScorer.from_preset(
        SOURCE_COPILOT,
        db_path=str(db_dir / f"{SOURCE_COPILOT}.db"),
    )
    target = CompoundingScorer.from_preset(
        TARGET_COPILOT,
        db_path=str(db_dir / f"{TARGET_COPILOT}.db"),
    )
    try:
        registry = build_transfer_registry()
        factors = {
            name: 0.5
            for name in target._preset.shape.factor_names
        }
        before = target.score(factors, "trend_following")
        summary = target.warm_start(
            registry,
            category_mapping={
                "freshness_violation": "trend_following",
                "pipeline_failure": "mean_reversion",
            },
            blend_weight=0.35,
        )
        after = target.score(factors, "trend_following")
        return {
            "source_copilot": source._preset.name,
            "target_copilot": target._preset.name,
            "applied": summary["applied"],
            "source_copilots": summary["source_copilots"],
            "score": summary["score"],
            "before_action": before.action,
            "before_confidence": before.confidence,
            "after_action": after.action,
            "after_confidence": after.confidence,
        }
    finally:
        source.graph_store.close()
        target.graph_store.close()


def main() -> int:
    summary = run_demo()
    print("WARM START TRANSFER COMPLETE")
    print(f"source_copilot={summary['source_copilot']}")
    print(f"target_copilot={summary['target_copilot']}")
    print(f"applied={summary['applied']}")
    print(f"source_copilots={','.join(summary['source_copilots'])}")
    print(f"score={summary['score']:.4f}")
    print(
        "before_action=%s before_confidence=%.4f"
        % (summary["before_action"], summary["before_confidence"])
    )
    print(
        "after_action=%s after_confidence=%.4f"
        % (summary["after_action"], summary["after_confidence"])
    )
    return 0 if int(summary["applied"]) > 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
