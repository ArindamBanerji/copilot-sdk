from __future__ import annotations

import pytest

from app.context_router import _was_correct
from app.routers.data_import import _trade_store_ref
from copilot_sdk.scoring.presets.trading import TradingPreset


@pytest.fixture(autouse=True)
def reset_trade_store():
    _trade_store_ref.clear()
    yield
    _trade_store_ref.clear()


def _trade(index: int, **overrides):
    payload = {
        "trade_id": f"t-{index}",
        "category": "trend_following",
        "verified": True,
        "pnl": 10.0,
    }
    payload.update(overrides)
    return payload


def _breakdown(client):
    response = client.get("/api/context/conservation-breakdown")
    assert response.status_code == 200
    return response.json()


def _category(payload, name):
    return next(category for category in payload["categories"] if category["category"] == name)


def test_endpoint_200_empty(client):
    payload = _breakdown(client)

    assert payload["total_categories"] == 5
    assert len(payload["categories"]) == 5
    assert {category["status"] for category in payload["categories"]} == {"BOOTSTRAP"}


def test_5_categories_present(client):
    payload = _breakdown(client)

    assert [category["category"] for category in payload["categories"]] == list(
        TradingPreset().shape.category_names
    )


def test_empty_categories_bootstrap(client):
    payload = _breakdown(client)

    for category in payload["categories"]:
        assert category["total_trades"] == 0
        assert category["verified"] == 0
        assert category["correct"] == 0
        assert category["status"] == "BOOTSTRAP"
        assert category["can_trade"] is True


def test_with_trades_not_bootstrap(client):
    _trade_store_ref.extend(_trade(index, category="trend_following") for index in range(20))

    category = _category(_breakdown(client), "trend_following")

    assert category["verified"] == 20
    assert category["status"] != "BOOTSTRAP"


def test_overall_safe_when_no_red(client):
    _trade_store_ref.extend(_trade(index, category="trend_following") for index in range(20))

    payload = _breakdown(client)

    assert payload["red_categories"] == 0
    assert payload["overall_safe"] is True


def test_has_theta_min_proxy(client):
    payload = _breakdown(client)

    for category in payload["categories"]:
        assert category["theta_min_proxy"] > 0


def test_has_penalty_ratio(client):
    payload = _breakdown(client)

    assert payload["penalty_ratio"] == 3.0


def test_has_methodology_note(client):
    payload = _breakdown(client)

    assert "Simplified" in payload["methodology"] or "proxy" in payload["methodology"]
    assert "/api/conservation/status" in payload["methodology"]


def test_red_amber_green_counts_sum(client):
    payload = _breakdown(client)

    assert (
        payload["red_categories"]
        + payload["amber_categories"]
        + payload["green_categories"]
        <= payload["total_categories"]
    )


def test_can_trade_false_when_red(client):
    _trade_store_ref.extend(
        _trade(index, category="income_strategy", pnl=-10.0) for index in range(20)
    )

    category = _category(_breakdown(client), "income_strategy")

    assert category["status"] == "RED"
    assert category["can_trade"] is False


def test_note_present_for_amber_or_red(client):
    _trade_store_ref.extend(
        _trade(index, category="income_strategy", pnl=-10.0) for index in range(20)
    )

    category = _category(_breakdown(client), "income_strategy")

    assert category["status"] in {"AMBER", "RED"}
    assert "conservation" in category["note"]


def test_route_mounted(client):
    paths = {route.path for route in client.app.routes}

    assert "/api/context/conservation-breakdown" in paths


def test_was_correct_uses_pnl_positive():
    assert _was_correct({"pnl": 1.0, "verification_score": 0.0}) is True
    assert _was_correct({"pnl": -1.0, "verification_score": 1.0}) is False


def test_was_correct_uses_verification_score_when_pnl_missing():
    assert _was_correct({"verification_score": 0.5}) is True
    assert _was_correct({"verification_score": 0.49}) is False


def test_was_correct_handles_bad_numeric_values():
    assert _was_correct({"pnl": "not-a-number", "verification_score": "bad"}) is False
    assert _was_correct({"pnl": None, "verification_score": None}) is False
