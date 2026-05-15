from types import SimpleNamespace

import numpy as np

from copilot_sdk.discovery import (
    AnomalyCoOccurrencePattern,
    CentroidCorrelationPattern,
    ConservationAlignmentPattern,
    DiscoveryAlert,
    DiscoveryEngine,
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


def test_register_copilot():
    engine = DiscoveryEngine(patterns=[])
    engine.register_copilot("alpha", FakeScorer())

    assert engine.sweep() == []


def test_sweep_empty_returns_empty():
    engine = DiscoveryEngine(patterns=[CentroidCorrelationPattern()])

    assert engine.sweep() == []
    assert engine.alert_count == 0


def test_single_copilot_has_no_pairwise_or_anomaly_alerts():
    engine = DiscoveryEngine(
        patterns=[CentroidCorrelationPattern(), AnomalyCoOccurrencePattern()]
    )
    engine.register_copilot("one", FakeScorer(np.ones((1, 1, 2)), alpha=0.1))

    assert engine.sweep() == []


def test_two_copilots_return_deterministic_alert():
    engine = DiscoveryEngine(patterns=[ConservationAlignmentPattern()])
    engine.register_copilot("left", FakeScorer(phase="B"))
    engine.register_copilot("right", FakeScorer(phase="B"))

    alerts = engine.sweep()

    assert len(alerts) == 1
    assert alerts[0].pattern_type == "conservation_alignment"


def test_digest_filters_confidence():
    engine = DiscoveryEngine(patterns=[])
    engine._alerts.extend([
        DiscoveryAlert(pattern_type="low", confidence=0.2),
        DiscoveryAlert(pattern_type="high", confidence=0.8),
    ])

    digest = engine.get_digest(min_confidence=0.5)

    assert [alert.pattern_type for alert in digest] == ["high"]


def test_alert_auto_id_status_created_at():
    alert = DiscoveryAlert(pattern_type="example", confidence=2.0)

    assert alert.alert_id.startswith("DISC-")
    assert alert.status == "advisory"
    assert alert.created_at > 0
    assert alert.confidence == 1.0


def test_sweep_alert_ids_unique():
    engine = DiscoveryEngine(patterns=[ConservationAlignmentPattern()])
    engine.register_copilot("left", FakeScorer(phase="B"))
    engine.register_copilot("right", FakeScorer(phase="B"))

    first = engine.sweep()
    second = engine.sweep()
    ids = [alert.alert_id for alert in first + second]

    assert len(ids) == len(set(ids))


def test_clear_removes_all_alerts():
    engine = DiscoveryEngine(patterns=[ConservationAlignmentPattern()])
    engine.register_copilot("left", FakeScorer(phase="B"))
    engine.register_copilot("right", FakeScorer(phase="B"))
    engine.sweep()

    engine.clear()

    assert engine.alert_count == 0
    assert engine.get_digest() == []
