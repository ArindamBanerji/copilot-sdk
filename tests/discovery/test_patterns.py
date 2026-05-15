from types import SimpleNamespace

import numpy as np

from copilot_sdk.discovery import DiscoveryAlert
from copilot_sdk.discovery.patterns import (
    AnomalyCoOccurrencePattern,
    CentroidCorrelationPattern,
    ConservationAlignmentPattern,
    TransferOpportunityPattern,
)


class FakeScorer:
    def __init__(self, centroids=None, phase="A", alpha=0.0):
        self.gae_scorer = SimpleNamespace(centroids=centroids)
        self._phase = phase
        self._alpha = alpha

    def get_phase(self):
        return self._phase

    def get_alpha(self):
        return self._alpha


def test_centroid_correlation_fires_for_similar_centroids():
    pattern = CentroidCorrelationPattern(min_similarity=0.99)
    longer = np.zeros((1, 3, 5))
    longer[:, :, :3] = 1.0
    copilots = {
        "left": FakeScorer(np.ones((2, 2, 3))),
        "right": FakeScorer(longer),
    }

    alerts = pattern.discover(copilots)

    assert len(alerts) == 1
    assert isinstance(alerts[0], DiscoveryAlert)
    assert alerts[0].evidence["similarity"] >= 0.99


def test_centroid_correlation_skips_wrong_or_missing_centroids():
    pattern = CentroidCorrelationPattern(min_similarity=0.1)
    copilots = {
        "missing": FakeScorer(None),
        "flat": FakeScorer(np.ones((3,))),
        "zero": FakeScorer(np.zeros((1, 1, 2))),
    }

    assert pattern.discover(copilots) == []


def test_conservation_alignment_fires_for_same_phase():
    pattern = ConservationAlignmentPattern()

    alerts = pattern.discover({
        "left": FakeScorer(phase="B"),
        "right": FakeScorer(phase="B"),
        "other": FakeScorer(phase="A"),
    })

    assert len(alerts) == 1
    assert alerts[0].evidence["phase"] == "B"


def test_transfer_opportunity_requires_mapping():
    pattern = TransferOpportunityPattern(accuracy_gap=0.2)
    copilots = {
        "source": FakeScorer(alpha=0.9),
        "target": FakeScorer(alpha=0.2),
    }

    assert pattern.discover(copilots) == []


def test_transfer_opportunity_fires_with_alpha_gap():
    pattern = TransferOpportunityPattern(accuracy_gap=0.2)
    copilots = {
        "source": FakeScorer(alpha=0.9),
        "target": FakeScorer(alpha=0.2),
    }

    alerts = pattern.discover(
        copilots,
        category_mappings={"source->target": {"a": "b"}},
    )

    assert len(alerts) == 1
    assert alerts[0].evidence["gap"] == 0.7


def test_anomaly_co_occurrence_fires_for_two_low_alpha_scorers():
    pattern = AnomalyCoOccurrencePattern(alpha_threshold=0.5)

    alerts = pattern.discover({
        "left": FakeScorer(alpha=0.1),
        "right": FakeScorer(alpha=0.2),
        "healthy": FakeScorer(alpha=0.8),
    })

    assert len(alerts) == 1
    assert set(alerts[0].evidence["affected"]) == {"left", "right"}


def test_single_low_alpha_has_no_anomaly():
    pattern = AnomalyCoOccurrencePattern(alpha_threshold=0.5)

    assert pattern.discover({
        "left": FakeScorer(alpha=0.1),
        "healthy": FakeScorer(alpha=0.8),
    }) == []


def test_all_pattern_alerts_are_discovery_alerts():
    pattern_alerts = [
        *CentroidCorrelationPattern(min_similarity=0.9).discover({
            "left": FakeScorer(np.ones((1, 1, 2))),
            "right": FakeScorer(np.ones((1, 1, 2))),
        }),
        *ConservationAlignmentPattern().discover({
            "left": FakeScorer(phase="A"),
            "right": FakeScorer(phase="A"),
        }),
        *TransferOpportunityPattern(accuracy_gap=0.1).discover(
            {"left": FakeScorer(alpha=0.8), "right": FakeScorer(alpha=0.2)},
            category_mappings={"left->right": {"a": "b"}},
        ),
        *AnomalyCoOccurrencePattern(alpha_threshold=0.5).discover({
            "left": FakeScorer(alpha=0.1),
            "right": FakeScorer(alpha=0.2),
        }),
    ]

    assert pattern_alerts
    assert all(isinstance(alert, DiscoveryAlert) for alert in pattern_alerts)
