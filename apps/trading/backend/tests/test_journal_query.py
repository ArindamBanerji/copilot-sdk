from __future__ import annotations

from datetime import date

import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.routers.data_import import _trade_store_ref
from app.services.journal_query import JournalQueryService


def _trade(
    trade_id: str,
    *,
    category: str = "mean_reversion",
    regime: str = "ranging",
    action: str = "strong_execution",
    pnl: float = 100.0,
    confidence: float = 0.9,
    entry_time: str = "2026-04-15T09:30:00",
    factors: dict[str, float] | None = None,
) -> dict:
    return {
        "trade_id": trade_id,
        "ticker": "MSFT",
        "category": category,
        "regime": regime,
        "action": action,
        "pnl": pnl,
        "confidence": confidence,
        "entry_time": entry_time,
        "factors": factors or {"rsi": 0.7, "signal_alignment": 0.8},
    }


@pytest.fixture(autouse=True)
def reset_store():
    _trade_store_ref.clear()
    yield
    _trade_store_ref.clear()


def _service() -> JournalQueryService:
    return JournalQueryService(today=date(2026, 7, 3))


def _trades() -> list[dict]:
    return [
        _trade("t-1", pnl=120.0, entry_time="2026-04-15T09:30:00"),
        _trade("t-2", category="trend_following", regime="trending", pnl=30.0, entry_time="2026-05-10T09:30:00", factors={"rsi": 0.4}),
        _trade("t-3", category="mean_reversion", regime="ranging", pnl=-60.0, confidence=0.5, entry_time="2026-01-10T09:30:00"),
    ]


def test_category_filter_mean_reversion():
    result = _service().query("mean_reversion trades", _trades())

    assert result["parsed"]["category"] == "mean_reversion"
    assert result["count"] == 2


def test_regime_filter_ranging():
    result = _service().query("in ranging markets", _trades())

    assert result["parsed"]["regime"] == "ranging"
    assert result["count"] == 2


def test_last_quarter_date_range():
    result = _service().query("last quarter", _trades())

    assert result["parsed"]["date_range"] == ["2026-04-01", "2026-06-30"]
    assert result["count"] == 2


def test_this_month_date_range():
    result = _service().query("this month", _trades())

    assert result["parsed"]["date_range"] == ["2026-07-01", "2026-07-31"]
    assert result["count"] == 0


def test_combined_filter():
    result = _service().query("mean_reversion in ranging last quarter", _trades())

    assert result["parsed"]["category"] == "mean_reversion"
    assert result["parsed"]["regime"] == "ranging"
    assert result["parsed"]["date_range"] == ["2026-04-01", "2026-06-30"]
    assert [row["trade_id"] for row in result["results"]] == ["t-1"]


def test_factor_filter():
    result = _service().query("RSI weight > 0.5", _trades())

    assert result["parsed"]["factor"] == {"name": "rsi", "operator": ">", "value": 0.5}
    assert {row["trade_id"] for row in result["results"]} == {"t-1", "t-3"}


def test_best_performing_setups_sort_descending():
    result = _service().query("best performing setups", _trades())

    assert result["parsed"]["performance"] == "best"
    assert [row["trade_id"] for row in result["results"]] == ["t-1", "t-2", "t-3"]


def test_empty_query_returns_all():
    result = _service().query("", _trades())

    assert result["parsed"] == {}
    assert result["count"] == 3
    assert not result["warnings"]


def test_nonsense_query_returns_all_with_warning():
    result = _service().query("purple moon thesis", _trades())

    assert result["parsed"] == {}
    assert result["count"] == 3
    assert result["warnings"] == ["No journal filters matched; showing all trades."]


def test_endpoint_returns_shape(tmp_path):
    _trade_store_ref.extend(_trades())
    app = create_app(db_path=tmp_path / "trading_journal_query.db", demo_bundle_path=False)
    app.state.trading_journal_dir = tmp_path / "journal"
    client = TestClient(app)

    response = client.post("/api/trading/journal/query", json={"question": "mean_reversion in ranging"})

    assert response.status_code == 200
    payload = response.json()
    assert {"query", "parsed", "results", "count", "summary"} <= set(payload)
    assert payload["parsed"]["category"] == "mean_reversion"
