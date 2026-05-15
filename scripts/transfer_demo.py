"""Run a local cross-copilot warm-start demo."""

from __future__ import annotations

import tempfile
from pathlib import Path

from copilot_sdk.scoring.scorer import CompoundingScorer
from copilot_sdk.transfer import SharedPatternRegistry, TransferPattern


def main() -> int:
    registry = SharedPatternRegistry()
    registry.register(
        TransferPattern(
            pattern_id="",
            source_copilot="dataops",
            pattern_type="centroid_delta",
            category="freshness_violation",
            action="auto_approve",
            win_rate=0.74,
            centroid_delta=[0.06, 0.02, 0.01, 0.03, 0.02, 0.01, 0.04],
            confidence=0.82,
            metadata={"source_rule": "freshness_violation_signal"},
        )
    )

    db_path = Path(tempfile.mkdtemp()) / "s2p-transfer-demo.db"
    scorer = CompoundingScorer.from_preset("s2p", db_path=str(db_path))
    factors = {
        name: 0.5
        for name in scorer._preset.shape.factor_names
    }
    before = scorer.score(factors, "price_variance")
    summary = scorer.warm_start(
        registry,
        category_mapping={"freshness_violation": "price_variance"},
        blend_weight=0.4,
    )
    after = scorer.score(factors, "price_variance")

    print("TRANSFER COMPLETE")
    print(f"source_copilots={','.join(summary['source_copilots'])}")
    print(f"applied={summary['applied']}")
    print(f"score={summary['score']:.4f}")
    print(f"before_action={before.action} before_confidence={before.confidence:.4f}")
    print(f"after_action={after.action} after_confidence={after.confidence:.4f}")
    scorer.graph_store.close()
    scorer.store.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
