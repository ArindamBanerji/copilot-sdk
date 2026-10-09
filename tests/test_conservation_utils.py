from __future__ import annotations

from typing import Any, cast

import pytest

from copilot_sdk.backend import conservation_utils as conservation_utils_module
from copilot_sdk.backend.conservation_utils import (
    QUALITY_WINDOW_SIZE,
    _rolling_q,
    compute_conservation_status_payload,
    compute_conservation_metrics,
)


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
        category_count = max(categories_with_data, 1)
        self.decisions = [
            {
                "decision_id": f"d-{index:04d}",
                "created_at": float(index),
                "category": f"category-{index % category_count}",
                "outcome": "confirmed" if index < correct else "overridden",
                "is_correct": index < correct,
            }
            for index in range(verified)
        ]

    def count_verified(self, domain: str) -> int:
        return self.verified

    def count_correct(self, domain: str) -> int:
        return self.correct

    def count_verified_decisions(self, domain: str) -> int:
        return self.total

    def count_categories_with_n(self, domain: str, n: int) -> int:
        return self.categories_with_data

    def get_verified_decisions(self, domain: str) -> list[dict]:
        return list(self.decisions)


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
    assert metrics["V"] == 590
    assert metrics["q"] == 370 / QUALITY_WINDOW_SIZE


def _ordered_rows(total: int, *, first_incorrect: int = 0) -> list[dict]:
    return [
        {
            "decision_id": f"row-{index:04d}",
            "created_at": float(index),
            "category": "category-0",
            "outcome": "overridden" if index < first_incorrect else "confirmed",
            "is_correct": index >= first_incorrect,
        }
        for index in range(total)
    ]


def test_rolling_q_uses_all_399_verified_decisions():
    rows = _ordered_rows(399, first_incorrect=99)

    assert _rolling_q(rows) == pytest.approx(300 / 399)


def test_rolling_q_uses_exact_400_verified_window():
    rows = _ordered_rows(400, first_incorrect=100)

    assert _rolling_q(rows) == pytest.approx(300 / 400)


def test_rolling_q_at_401_uses_only_last_400():
    rows = _ordered_rows(401, first_incorrect=1)

    assert _rolling_q(rows) == 1.0


def test_rolling_q_rejects_non_positive_window():
    with pytest.raises(ValueError, match="window_size must be positive"):
        _rolling_q(_ordered_rows(1), window_size=0)


def _recent_degradation_rows() -> list[dict]:
    outcomes = ([True] * 500) + ([False] * 400)
    return [
        {
            "decision_id": f"degradation-{index:04d}",
            "created_at": float(index),
            "category": "category-0",
            "outcome": "confirmed" if correct else "overridden",
            "is_correct": correct,
        }
        for index, correct in enumerate(outcomes)
    ]


def _status_for_rows(rows: list[dict]) -> dict[str, Any]:
    return cast(
        dict[str, Any],
        compute_conservation_status_payload(
            "trading",
            {
                "verified_count": len(rows),
                "correct_count": sum(bool(row["is_correct"]) for row in rows),
                "total_categories": 1,
                "categories_with_data": 1,
                "verified_decisions": rows,
            },
        ),
    )


def test_rolling_q_with_reverse_ordered_input():
    rows = list(reversed(_recent_degradation_rows()))

    status = _status_for_rows(rows)

    assert status["q"] == 0.0
    assert status["V"] == 900
    assert status["status"] == "RED"


def test_rolling_q_with_chronological_input():
    status = _status_for_rows(_recent_degradation_rows())

    assert status["q"] == 0.0
    assert status["V"] == 900
    assert status["status"] == "RED"


def test_status_fails_closed_without_decision_rows():
    status = compute_conservation_status_payload(
        "trading",
        {
            "verified_count": 10,
            "correct_count": 10,
            "total_categories": 1,
            "categories_with_data": 1,
        },
    )

    assert status["conservation_mode"] == "unavailable"
    assert status["conservation_applicable"] is False
    assert status["passed"] is False
    assert status["status"] != "GREEN"


def test_retired_count_helper_removed():
    assert not hasattr(conservation_utils_module, "_rolling_q" + "_from_counts")
