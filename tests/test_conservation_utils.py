from __future__ import annotations

from copilot_sdk.backend.conservation_utils import compute_conservation_metrics


class _Shape:
    n_categories = 5


class _Preset:
    shape = _Shape()
    penalty_ratio = 1.0


class _Store:
    domain = "soc"

    def __init__(self, verified: int, correct: int, total: int, categories_with_data: int) -> None:
        self.verified = verified
        self.correct = correct
        self.total = total
        self.categories_with_data = categories_with_data

    def count_verified(self, domain: str) -> int:
        return self.verified

    def count_correct(self, domain: str) -> int:
        return self.correct

    def count_verified_decisions(self, domain: str) -> int:
        return self.total

    def count_categories_with_n(self, domain: str, n: int) -> int:
        return self.categories_with_data


class _State:
    _preset = _Preset()

    def __init__(self, store: _Store) -> None:
        self.graph_store = store


def _metrics(verified: int, correct: int, total: int, categories_with_data: int):
    return compute_conservation_metrics(_State(_Store(verified, correct, total, categories_with_data)), domain="soc")


def test_alpha_low_verification():
    metrics = _metrics(50, 45, 600, 5)

    assert metrics["alpha"] == 1.0
    assert metrics["V"] == 50


def test_theta_min_floor():
    low_verification = _metrics(50, 45, 600, 5)
    high_verification = _metrics(50, 45, 50, 5)

    assert low_verification["theta_min"] == high_verification["theta_min"]


def test_alpha_high_verification():
    metrics = _metrics(590, 560, 600, 5)

    assert metrics["alpha"] == 1.0
    assert metrics["q"] == 560 / 590
