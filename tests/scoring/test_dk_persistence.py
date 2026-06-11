import math

import pytest

from copilot_sdk.scoring.dk_persistence import (
    DKWelfordTracker,
    WelfordAccumulator,
    persist_dk_after_reestimate,
)


def _batch_mean_m2(vectors: list[list[float]]) -> tuple[list[float], list[float]]:
    dimension = len(vectors[0])
    means = [
        sum(vector[index] for vector in vectors) / len(vectors)
        for index in range(dimension)
    ]
    m2 = [
        sum((vector[index] - means[index]) ** 2 for vector in vectors)
        for index in range(dimension)
    ]
    return means, m2


def _populated_tracker() -> DKWelfordTracker:
    tracker = DKWelfordTracker()
    tracker.update([1.0, 2.0, 3.0], True)
    tracker.update([2.0, 4.0, 6.0], False)
    tracker.update([3.0, 6.0, 9.0], True)
    return tracker


def test_welford_accumulator_math() -> None:
    vectors = [[1.0, 2.0], [2.0, 4.0], [4.0, 8.0]]
    accumulator = WelfordAccumulator()

    for vector in vectors:
        accumulator.update(vector)

    state = accumulator.to_state()
    expected_mean, expected_m2 = _batch_mean_m2(vectors)
    assert state["n"] == 3
    assert state["mean"] == pytest.approx(expected_mean)
    assert state["m2"] == pytest.approx(expected_m2)


@pytest.mark.parametrize(
    "bad_vector",
    [
        "123",
        b"123",
        {"a": 1.0},
        [],
        [1.0, "x"],
        [1.0, math.inf],
        [[1.0], [2.0]],
    ],
)
def test_welford_accumulator_rejects_bad_vectors(bad_vector: object) -> None:
    accumulator = WelfordAccumulator()

    with pytest.raises((TypeError, ValueError)):
        accumulator.update(bad_vector)  # type: ignore[arg-type]


def test_welford_accumulator_rejects_dimension_change() -> None:
    accumulator = WelfordAccumulator()
    accumulator.update([1.0, 2.0])

    with pytest.raises(ValueError):
        accumulator.update([1.0, 2.0, 3.0])


def test_welford_accumulator_state_roundtrip() -> None:
    accumulator = WelfordAccumulator()
    accumulator.update([1.0, 2.0])
    accumulator.update([3.0, 6.0])

    restored = WelfordAccumulator.from_state(accumulator.to_state())

    assert restored.to_state() == accumulator.to_state()


def test_welford_confirmed_overridden_split() -> None:
    tracker = _populated_tracker()

    assert tracker.n_confirmed == 2
    assert tracker.n_overridden == 1
    assert tracker.n_all == 3
    state = tracker.to_welford_state()
    assert state["confirmed_mean"] == pytest.approx([2.0, 4.0, 6.0])
    assert state["overridden_mean"] == pytest.approx([2.0, 4.0, 6.0])
    assert state["all_mean"] == pytest.approx([2.0, 4.0, 6.0])


def test_welford_tracker_rejects_unknown_correctness() -> None:
    tracker = DKWelfordTracker()

    with pytest.raises(TypeError):
        tracker.update([1.0, 2.0], None)  # type: ignore[arg-type]


def test_welford_state_shape_matches_storage_contract() -> None:
    tracker = _populated_tracker()
    state = tracker.to_welford_state()

    assert set(state) == {
        "confirmed_mean",
        "confirmed_m2",
        "overridden_mean",
        "overridden_m2",
        "all_mean",
        "all_m2",
        "n_all",
    }
    lengths = {
        len(state[key])  # type: ignore[arg-type]
        for key in (
            "confirmed_mean",
            "confirmed_m2",
            "overridden_mean",
            "overridden_m2",
            "all_mean",
            "all_m2",
        )
    }
    assert lengths == {3}
    assert state["n_all"] == 3


def test_welford_tracker_state_roundtrip() -> None:
    tracker = _populated_tracker()
    restored = DKWelfordTracker.from_welford_state(
        tracker.to_welford_state(),
        n_confirmed=tracker.n_confirmed,
        n_overridden=tracker.n_overridden,
    )

    assert restored.n_confirmed == tracker.n_confirmed
    assert restored.n_overridden == tracker.n_overridden
    assert restored.n_all == tracker.n_all
    assert restored.to_welford_state() == tracker.to_welford_state()


def test_welford_tracker_copy_safety() -> None:
    tracker = _populated_tracker()
    state = tracker.to_welford_state()
    state["confirmed_mean"][0] = 999.0  # type: ignore[index]

    fresh_state = tracker.to_welford_state()
    assert fresh_state["confirmed_mean"][0] != 999.0  # type: ignore[index]


class FakeScorer:
    def __init__(self, weights: list[list[float]] | None) -> None:
        self._weights = weights
        self.calls = 0

    def get_dk_weights(self) -> list[list[float]] | None:
        self.calls += 1
        return self._weights

    def __getattribute__(self, name: str) -> object:
        if name == "_dk_weights":
            raise AssertionError("private _dk_weights must not be accessed")
        return object.__getattribute__(self, name)


class FakeLearningStore:
    def __init__(self, *, fail: bool = False) -> None:
        self.fail = fail
        self.calls: list[dict[str, object]] = []

    def update_dk_weights(self, **kwargs: object) -> None:
        if self.fail:
            raise RuntimeError("boom")
        self.calls.append(kwargs)


def test_persist_dk_reads_from_scorer() -> None:
    scorer = FakeScorer([[1.0, 0.5], [0.8, 1.2]])
    store = FakeLearningStore()
    tracker = DKWelfordTracker()
    tracker.update([1.0, 2.0], True)

    assert persist_dk_after_reestimate(
        domain="trading",
        scorer=scorer,
        learning_store=store,
        welford_tracker=tracker,
    )

    assert scorer.calls == 1
    assert store.calls[0]["weight_tensor"] == [[1.0, 0.5], [0.8, 1.2]]


def test_persist_dk_writes_welford_state() -> None:
    scorer = FakeScorer([[1.0, 0.5]])
    store = FakeLearningStore()
    tracker = _populated_tracker()

    assert persist_dk_after_reestimate(
        domain="trading",
        scorer=scorer,
        learning_store=store,
        welford_tracker=tracker,
        entity_group="desk-a",
    )

    call = store.calls[0]
    assert call["domain"] == "trading"
    assert call["n_decisions_used"] == 3
    assert call["n_confirmed"] == 2
    assert call["n_overridden"] == 1
    assert call["entity_group"] == "desk-a"
    assert call["welford_state"] == tracker.to_welford_state()
    assert isinstance(call["computed_at"], float)


def test_persist_dk_no_store_silent() -> None:
    tracker = _populated_tracker()

    assert not persist_dk_after_reestimate(
        domain="trading",
        scorer=FakeScorer([[1.0]]),
        learning_store=None,
        welford_tracker=tracker,
    )


def test_persist_dk_no_weights_silent() -> None:
    store = FakeLearningStore()

    assert not persist_dk_after_reestimate(
        domain="trading",
        scorer=FakeScorer(None),
        learning_store=store,
        welford_tracker=_populated_tracker(),
    )
    assert store.calls == []


def test_persist_dk_no_tracker_or_empty_tracker_does_not_write() -> None:
    store = FakeLearningStore()
    scorer = FakeScorer([[1.0]])

    assert not persist_dk_after_reestimate(
        domain="trading",
        scorer=scorer,
        learning_store=store,
        welford_tracker=None,
    )
    assert not persist_dk_after_reestimate(
        domain="trading",
        scorer=scorer,
        learning_store=store,
        welford_tracker=DKWelfordTracker(),
    )
    assert store.calls == []


def test_persist_dk_nonfatal_on_l5_failure() -> None:
    assert not persist_dk_after_reestimate(
        domain="trading",
        scorer=FakeScorer([[1.0]]),
        learning_store=FakeLearningStore(fail=True),
        welford_tracker=_populated_tracker(),
    )


def test_persist_dk_does_not_mutate_tracker_or_scorer() -> None:
    weights = [[1.0, 0.5]]
    scorer = FakeScorer(weights)
    store = FakeLearningStore()
    tracker = _populated_tracker()
    before_state = tracker.to_welford_state()

    assert persist_dk_after_reestimate(
        domain="trading",
        scorer=scorer,
        learning_store=store,
        welford_tracker=tracker,
    )

    store.calls[0]["weight_tensor"][0][0] = 999.0  # type: ignore[index]
    store.calls[0]["welford_state"]["all_mean"][0] = 999.0  # type: ignore[index]
    assert weights == [[1.0, 0.5]]
    assert tracker.to_welford_state() == before_state


def test_persist_dk_does_not_access_private_dk_weights() -> None:
    store = FakeLearningStore()
    tracker = _populated_tracker()

    assert persist_dk_after_reestimate(
        domain="trading",
        scorer=FakeScorer([[1.0, 2.0]]),
        learning_store=store,
        welford_tracker=tracker,
    )
