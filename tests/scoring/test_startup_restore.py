from __future__ import annotations

import numpy as np

from copilot_sdk.graph.memory_store import InMemoryGraphStore
from copilot_sdk.scoring.dk_persistence import DKWelfordTracker
from copilot_sdk.scoring.scorer import CompoundingScorer
from copilot_sdk.scoring.startup_restore import restore_l5_runtime_state


def _welford_state() -> dict[str, object]:
    return {
        "confirmed_mean": [1.0, 2.0],
        "confirmed_m2": [0.5, 0.5],
        "overridden_mean": [3.0, 4.0],
        "overridden_m2": [0.25, 0.25],
        "all_mean": [2.0, 3.0],
        "all_m2": [1.0, 1.0],
        "n_all": 4,
    }


def _s2p_scorer() -> CompoundingScorer:
    return CompoundingScorer.from_preset(
        "s2p",
        graph_store=InMemoryGraphStore(domain="s2p"),
    )


def test_startup_loads_dk_and_welford_from_l5() -> None:
    scorer = _s2p_scorer()
    store = scorer.graph_store
    state = _welford_state()
    weights = [[0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3] for _ in range(5)]
    store.update_dk_weights(
        "s2p",
        weights,
        4,
        123.0,
        welford_state=state,
        n_confirmed=2,
        n_overridden=2,
    )

    status = restore_l5_runtime_state(domain="s2p", scorer=scorer, learning_store=store)

    assert status["dk_source"] == "l5"
    assert status["welford_source"] == "l5"
    assert scorer.get_dk_weights() == [[*row, 1.0] for row in weights]
    tracker = status["welford_tracker"]
    assert isinstance(tracker, DKWelfordTracker)
    assert tracker.n_all == 4
    assert tracker.n_confirmed == 2
    assert tracker.n_overridden == 2
    assert tracker.to_welford_state() == state


def test_startup_loads_centroids_from_l5() -> None:
    scorer = _s2p_scorer()
    store = scorer.graph_store
    before = np.asarray(scorer.gae_scorer.centroids, dtype=np.float64).copy()
    vector = [0.91, 0.82, 0.73, 0.64, 0.55, 0.46, 0.37]
    category = scorer._preset.shape.category_names[0]
    action = scorer._preset.shape.action_names[0]
    store.update_centroid("s2p", category, action, vector, 0.1)

    status = restore_l5_runtime_state(domain="s2p", scorer=scorer, learning_store=store)

    assert status["centroid_source"] == "l5"
    assert status["centroids_loaded"] is True
    after = np.asarray(scorer.gae_scorer.centroids, dtype=np.float64)
    assert not np.array_equal(after, before)
    np.testing.assert_allclose(after[0, 0, :], [*vector, 0.5])


def test_startup_loads_conservation_from_l5() -> None:
    scorer = _s2p_scorer()
    store = scorer.graph_store
    store.update_conservation_state(
        "s2p",
        status="GREEN",
        alpha=0.2,
        q=0.9,
        V=10,
        theta_min=0.7,
        product=0.18,
        old_status=None,
        baseline_product=0.0,
        relative_threshold=0.0,
        complacency_flag="false",
        categories_total=5,
        categories_with_data=5,
        caused_by_decision_id="d1",
    )

    status = restore_l5_runtime_state(domain="s2p", scorer=scorer, learning_store=store)

    assert status["conservation_source"] == "l5"
    assert status["conservation_state"]["status"] == "GREEN"


def test_startup_conservation_none_is_expected() -> None:
    scorer = _s2p_scorer()

    status = restore_l5_runtime_state(
        domain="s2p",
        scorer=scorer,
        learning_store=scorer.graph_store,
    )

    assert status["conservation_source"] == "missing"


def test_startup_l5_unavailable_falls_back() -> None:
    scorer = _s2p_scorer()

    status = restore_l5_runtime_state(domain="s2p", scorer=scorer, learning_store=None)

    assert status["dk_source"] == "missing"
    assert status["welford_source"] == "missing"
    assert status["centroid_source"] == "missing"
    assert status["conservation_source"] == "missing"


def test_startup_l5_read_failure_does_not_crash() -> None:
    class FailingStore:
        def get_dk_weights(self, _domain: str) -> None:
            raise RuntimeError("dk unavailable")

        def get_centroids(self, _domain: str) -> None:
            raise RuntimeError("centroids unavailable")

        def get_conservation_state(self, _domain: str) -> None:
            raise RuntimeError("conservation unavailable")

    scorer = _s2p_scorer()

    status = restore_l5_runtime_state(
        domain="s2p",
        scorer=scorer,
        learning_store=FailingStore(),
    )

    assert status["dk_source"] == "error"
    assert status["welford_source"] == "error"
    assert status["centroid_source"] == "error"
    assert status["conservation_source"] == "error"


def test_scorer_restore_rejects_bad_dk_shape() -> None:
    scorer = _s2p_scorer()

    try:
        scorer.load_dk_weights_from_l5([[1.0, 2.0]])
    except ValueError as exc:
        assert "DK weight shape" in str(exc)
    else:
        raise AssertionError("bad DK weight shape was accepted")


def test_invalid_centroid_restore_reports_error_without_crashing() -> None:
    class MalformedCentroidStore:
        def get_dk_weights(self, _domain: str) -> None:
            return None

        def get_centroids(self, _domain: str) -> list[dict[str, object]]:
            return [
                {
                    "category": "invoice_processing",
                    "action": "approve",
                    "vector_json": [1.0, 2.0],
                }
            ]

        def get_conservation_state(self, _domain: str) -> None:
            return None

    scorer = _s2p_scorer()

    status = restore_l5_runtime_state(
        domain="s2p",
        scorer=scorer,
        learning_store=MalformedCentroidStore(),
    )

    assert status["centroid_source"] == "error"
    assert status["centroids_loaded"] is False
