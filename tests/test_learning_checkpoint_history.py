"""Complete and legacy learning-checkpoint history contracts."""
import logging

import numpy as np
import pytest
from gae.learning import CalibrationProfile, WeightUpdate

from copilot_sdk.framework.learning_state import load_from_graph, make_state, save_state
from copilot_sdk.graph import InMemoryGraphStore


def _save_checkpoint(graph: InMemoryGraphStore) -> None:
    state = make_state(np.ones((2, 2)), ["a", "b"], CalibrationProfile(), 7)
    state.history = [WeightUpdate(
        7, 1705312200.0, 0, "approve", 1,
        np.array([0.1, 0.2]), np.array([0.01, 0.02]),
        np.full((2, 2), 0.75), np.ones((2, 2)), 0.1, 0.8,
    )]
    save_state(state, {"source": "observations"}, graph, "trading")


def test_checkpoint_preserves_nonzero_historical_weights() -> None:
    graph = InMemoryGraphStore()
    _save_checkpoint(graph)
    loaded = load_from_graph(graph, "trading", CalibrationProfile())
    update = loaded.history[0]
    np.testing.assert_array_equal(update.W_before, np.full((2, 2), 0.75))
    np.testing.assert_array_equal(update.W_after, np.ones((2, 2)))
    np.testing.assert_array_equal(update.factor_vector, [0.1, 0.2])
    np.testing.assert_array_equal(update.delta_applied, [0.01, 0.02])
    assert (update.decision_number, update.timestamp, update.action_index,
            update.action_name, update.outcome, update.alpha_effective,
            update.confidence_at_decision) == (7, 1705312200.0, 0, "approve", 1, 0.1, 0.8)


def test_legacy_checkpoint_missing_previous_weights_warns_and_loads_zeros(
    caplog: pytest.LogCaptureFixture,
) -> None:
    graph = InMemoryGraphStore()
    _save_checkpoint(graph)
    legacy = graph.get_evolution("trading", "learning_state")
    assert legacy is not None
    legacy["history"][0].pop("W_before", None)
    graph.save_evolution("trading", "learning_state", legacy)
    with caplog.at_level(logging.WARNING, logger="copilot_sdk.framework.learning_state"):
        loaded = load_from_graph(graph, "trading", CalibrationProfile())
    assert len(loaded.history) == 1
    np.testing.assert_array_equal(loaded.history[0].W_before, np.zeros((2, 2)))
    assert "W_before" in caplog.text
    assert "legacy" in caplog.text.lower()

