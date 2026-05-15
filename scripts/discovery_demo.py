"""Run a local advisory discovery demo without live backends."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from copilot_sdk.discovery import (  # noqa: E402
    AnomalyCoOccurrencePattern,
    CentroidCorrelationPattern,
    ConservationAlignmentPattern,
    DiscoveryEngine,
    TransferOpportunityPattern,
)
from copilot_sdk.scoring.scorer import CompoundingScorer  # noqa: E402


def main() -> int:
    trading = CompoundingScorer.from_preset("trading", db_path=":memory:")
    s2p = CompoundingScorer.from_preset("s2p", db_path=":memory:")

    _shape_centroids(trading, value=0.42)
    _shape_centroids(s2p, value=0.40)

    engine = DiscoveryEngine(
        patterns=[
            CentroidCorrelationPattern(min_similarity=0.80),
            ConservationAlignmentPattern(),
            TransferOpportunityPattern(accuracy_gap=0.10),
            AnomalyCoOccurrencePattern(alpha_threshold=0.50),
        ]
    )
    engine.register_copilot("trading", trading)
    engine.register_copilot("s2p", s2p)

    mappings = {
        "trading->s2p": {"equity_long": "price_variance"},
        "s2p->trading": {"price_variance": "equity_long"},
    }
    alerts = engine.sweep(category_mappings=mappings)
    digest = engine.get_digest(min_confidence=0.5)

    print(f"Discovery alerts: {len(alerts)}")
    for alert in alerts:
        names = ", ".join(alert.source_copilots)
        print(f"- [{alert.pattern_type}] {alert.title} ({names}) confidence={alert.confidence:.2f}")
    print(f"Digest alerts: {len(digest)}")
    print("DISCOVERY COMPLETE")
    return 0


def _shape_centroids(scorer: CompoundingScorer, value: float) -> None:
    centroids = np.asarray(scorer.gae_scorer.centroids, dtype=np.float64)
    scorer.gae_scorer.centroids = np.full_like(centroids, value, dtype=np.float64)


if __name__ == "__main__":
    raise SystemExit(main())
