from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor

import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.routers import journal as journal_router
from app.routers.data_import import _trade_store_ref


def _trade(
    trade_id: str,
    *,
    ticker: str = "MSFT",
    category: str = "trend_following",
    strategy_tag: str = "momentum",
    regime: str = "bull",
    pnl: float | None = 100.0,
    confidence: float = 0.8,
    entry_time: str = "2026-01-01T09:30:00",
) -> dict:
    return {
        "trade_id": trade_id,
        "ticker": ticker,
        "direction": "long",
        "entry_price": 100.0,
        "exit_price": 110.0 if pnl is not None else None,
        "size": 1.0,
        "entry_time": entry_time,
        "exit_time": "2026-01-02T16:00:00",
        "strategy_tag": strategy_tag,
        "category": category,
        "regime": regime,
        "pnl": pnl,
        "factors": {"signal_alignment": 0.8},
        "action": "strong_execution",
        "confidence": confidence,
        "metadata": {"source": "test"},
    }


@pytest.fixture(autouse=True)
def reset_trade_store():
    _trade_store_ref.clear()
    yield
    _trade_store_ref.clear()


def _seed_trades() -> None:
    _trade_store_ref.extend(
        [
            _trade("t-1", ticker="MSFT", category="trend_following", strategy_tag="momentum", regime="bull", pnl=120.0, confidence=0.9, entry_time="2026-01-05T09:30:00"),
            _trade("t-2", ticker="SPY", category="mean_reversion", strategy_tag="hedge", regime="bear", pnl=-40.0, confidence=0.7, entry_time="2026-01-20T09:30:00"),
            _trade("t-3", ticker="MSFT", category="trend_following", strategy_tag="swing", regime="bull", pnl=0.0, confidence=0.5, entry_time="2026-02-03T09:30:00"),
        ]
    )


def _set_journal_dir(client: TestClient, tmp_path) -> None:
    client.app.state.trading_journal_dir = tmp_path / "journal"


def _journal_client(tmp_path) -> TestClient:
    app = create_app(db_path=tmp_path / "trading_journal.db", demo_bundle_path=False)
    app.state.trading_journal_dir = tmp_path / "journal"
    return TestClient(app)


def test_trades_returns_list(client):
    _seed_trades()

    response = client.get("/api/trading/trades")
    filtered = client.get("/api/trading/trades?ticker=SPY")

    assert response.status_code == 200
    assert len(response.json()["trades"]) == 3
    assert response.json()["total"] == 3
    assert filtered.json()["total"] == 1


def test_trades_filter_by_ticker(client):
    _seed_trades()

    response = client.get("/api/trading/trades?ticker=msft")

    assert response.status_code == 200
    assert response.json()["total"] == 2
    assert {trade["ticker"] for trade in response.json()["trades"]} == {"MSFT"}


def test_trades_filter_by_category(client):
    _seed_trades()

    response = client.get("/api/trading/trades?category=mean_reversion")

    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert response.json()["trades"][0]["trade_id"] == "t-2"


def test_trades_filter_by_strategy_tag(client):
    _seed_trades()

    response = client.get("/api/trading/trades?strategy_tag=swing")

    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert response.json()["trades"][0]["trade_id"] == "t-3"


def test_trades_filter_by_outcome_win(client):
    _seed_trades()

    response = client.get("/api/trading/trades?outcome=win")

    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert response.json()["trades"][0]["trade_id"] == "t-1"


def test_trades_filter_by_outcome_loss(client):
    _seed_trades()

    response = client.get("/api/trading/trades?outcome=loss")

    assert response.status_code == 200
    assert response.json()["total"] == 2
    assert {trade["trade_id"] for trade in response.json()["trades"]} == {"t-2", "t-3"}


def test_trades_limit_and_offset(client):
    _seed_trades()

    response = client.get("/api/trading/trades?limit=1&offset=1")

    assert response.status_code == 200
    assert response.json()["total"] == 3
    assert [trade["trade_id"] for trade in response.json()["trades"]] == ["t-2"]


def test_trades_aggregate_stats_computed(client):
    _seed_trades()

    response = client.get("/api/trading/trades")
    filtered = client.get("/api/trading/trades?ticker=MSFT")

    aggregate = response.json()["aggregate"]
    filtered_aggregate = filtered.json()["aggregate"]
    assert aggregate["total_trades"] == 3
    assert aggregate["total_pnl"] == 80.0
    assert round(aggregate["avg_confidence"], 4) == 0.7
    assert filtered_aggregate["total_pnl"] == 120.0


def test_trades_empty_returns_empty_list(client):
    response = client.get("/api/trading/trades?limit=50")

    assert response.status_code == 200
    assert response.json()["trades"] == []
    assert response.json()["total"] == 0


def test_trades_aggregate_win_rate_is_wins_over_total(client):
    _seed_trades()

    response = client.get("/api/trading/trades")

    assert response.json()["aggregate"]["win_rate"] == 1 / 3


def test_trade_detail_found(client):
    _seed_trades()

    response = client.get("/api/trading/trades/t-1")

    assert response.status_code == 200
    assert response.json()["trade_id"] == "t-1"
    assert response.json()["ticker"] == "MSFT"


def test_trade_detail_not_found_404(client):
    response = client.get("/api/trading/trades/missing")

    assert response.status_code == 404
    assert response.json() == {"error": "Trade not found"}


def test_trade_detail_includes_factors(client):
    _seed_trades()

    response = client.get("/api/trading/trades/t-1")

    assert response.status_code == 200
    assert response.json()["factors"]["signal_alignment"] == 0.8


def test_analytics_group_by_category(client):
    _seed_trades()

    response = client.get("/api/trading/analytics?group_by=category")

    assert response.status_code == 200
    groups = {group["key"]: group for group in response.json()["groups"]}
    assert groups["trend_following"]["count"] == 2
    assert groups["mean_reversion"]["count"] == 1


def test_analytics_group_by_ticker(client):
    _seed_trades()

    response = client.get("/api/trading/analytics?group_by=ticker")

    groups = {group["key"]: group for group in response.json()["groups"]}
    assert groups["MSFT"]["count"] == 2
    assert groups["SPY"]["count"] == 1


def test_analytics_group_by_strategy(client):
    _seed_trades()

    response = client.get("/api/trading/analytics?group_by=strategy_tag")

    groups = {group["key"]: group for group in response.json()["groups"]}
    assert groups["momentum"]["count"] == 1
    assert groups["hedge"]["count"] == 1


def test_analytics_group_by_month(client):
    _seed_trades()

    response = client.get("/api/trading/analytics?group_by=month")

    groups = {group["key"]: group for group in response.json()["groups"]}
    assert groups["2026-01"]["count"] == 2
    assert groups["2026-02"]["count"] == 1


def test_analytics_with_filters(client):
    _seed_trades()

    response = client.get("/api/trading/analytics?group_by=ticker&category=trend_following")

    assert response.status_code == 200
    assert response.json()["total"] == 2
    assert {group["key"] for group in response.json()["groups"]} == {"MSFT"}


def test_analytics_win_rate_correct(client):
    _seed_trades()

    response = client.get("/api/trading/analytics?group_by=regime")

    groups = {group["key"]: group for group in response.json()["groups"]}
    assert groups["bull"]["win_rate"] == 0.5
    assert groups["bear"]["win_rate"] == 0.0


def test_analytics_empty_group(client):
    response = client.get("/api/trading/analytics?group_by=category")

    assert response.status_code == 200
    assert response.json() == {"group_by": "category", "groups": [], "total": 0}


def test_create_manual_entry(client, tmp_path):
    _set_journal_dir(client, tmp_path)

    response = client.post(
        "/api/trading/journal/entry",
        json={"ticker": "AAPL", "category": "trend_following", "reflection": "clean breakout"},
    )

    assert response.status_code == 201
    assert response.json()["created"] is True
    assert response.json()["entry_id"]


def test_created_entry_appears_in_list(client, tmp_path):
    _set_journal_dir(client, tmp_path)
    created = client.post("/api/trading/journal/entry", json={"ticker": "AAPL"}).json()

    response = client.get("/api/trading/trades")

    assert response.status_code == 200
    assert any(trade["trade_id"] == created["entry_id"] for trade in response.json()["trades"])


def test_create_entry_validates_required_fields(client, tmp_path):
    _set_journal_dir(client, tmp_path)

    response = client.post("/api/trading/journal/entry", json={"category": "trend_following"})

    assert response.status_code in {400, 422}


def test_update_reflection(client, tmp_path):
    _set_journal_dir(client, tmp_path)
    entry_id = client.post("/api/trading/journal/entry", json={"ticker": "AAPL"}).json()["entry_id"]

    update = client.put(
        f"/api/trading/journal/entry/{entry_id}/reflection",
        json={"reflection": "followed plan"},
    )
    detail = client.get(f"/api/trading/trades/{entry_id}")

    assert update.status_code == 200
    assert detail.json()["reflection"] == "followed plan"
    assert detail.json()["notes"] == "followed plan"


def test_reflection_on_imported_trade(client, tmp_path):
    _set_journal_dir(client, tmp_path)
    _seed_trades()

    response = client.put(
        "/api/trading/journal/entry/t-1/reflection",
        json={"reflection": "imported trade review"},
    )
    detail = client.get("/api/trading/trades/t-1")

    assert response.status_code == 200
    assert detail.json()["reflection"] == "imported trade review"


def test_reflection_preserved_on_update(client, tmp_path):
    _set_journal_dir(client, tmp_path)
    entry_id = client.post("/api/trading/journal/entry", json={"ticker": "AAPL"}).json()["entry_id"]

    client.put(f"/api/trading/journal/entry/{entry_id}/reflection", json={"reflection": "first"})
    client.put(f"/api/trading/journal/entry/{entry_id}/reflection", json={"reflection": "second"})
    detail = client.get(f"/api/trading/trades/{entry_id}")
    overlay = json.loads((tmp_path / "journal" / "journal_reflections.json").read_text(encoding="utf-8"))

    assert detail.json()["reflection"] == "second"
    assert [row["reflection"] for row in overlay[entry_id]["history"]] == ["first", "second"]


def test_add_tags(client, tmp_path):
    _set_journal_dir(client, tmp_path)
    entry_id = client.post("/api/trading/journal/entry", json={"ticker": "AAPL"}).json()["entry_id"]

    response = client.put(
        f"/api/trading/journal/entry/{entry_id}/tags",
        json={"tags": ["earnings", "setup-A"]},
    )
    detail = client.get(f"/api/trading/trades/{entry_id}")

    assert response.status_code == 200
    assert detail.json()["tags"] == ["earnings", "setup-A"]


def test_tags_filter(client, tmp_path):
    _set_journal_dir(client, tmp_path)
    first = client.post("/api/trading/journal/entry", json={"ticker": "AAPL"}).json()["entry_id"]
    second = client.post("/api/trading/journal/entry", json={"ticker": "MSFT"}).json()["entry_id"]
    client.put(f"/api/trading/journal/entry/{first}/tags", json={"tags": ["earnings"]})
    client.put(f"/api/trading/journal/entry/{second}/tags", json={"tags": ["setup-B"]})

    response = client.get("/api/trading/trades?tag=earnings")

    assert response.status_code == 200
    assert [trade["trade_id"] for trade in response.json()["trades"]] == [first]


def test_search_by_reflection_text(client, tmp_path):
    _set_journal_dir(client, tmp_path)
    entry_id = client.post(
        "/api/trading/journal/entry",
        json={"ticker": "AAPL", "reflection": "revenge trade after loss"},
    ).json()["entry_id"]

    response = client.get("/api/trading/trades?search=revenge")

    assert response.status_code == 200
    assert [trade["trade_id"] for trade in response.json()["trades"]] == [entry_id]


def test_search_by_ticker(client, tmp_path):
    _set_journal_dir(client, tmp_path)
    entry_id = client.post("/api/trading/journal/entry", json={"ticker": "AAPL"}).json()["entry_id"]

    response = client.get("/api/trading/trades?search=AAPL")

    assert response.status_code == 200
    assert [trade["trade_id"] for trade in response.json()["trades"]] == [entry_id]


def test_search_by_tag(client, tmp_path):
    _set_journal_dir(client, tmp_path)
    entry_id = client.post("/api/trading/journal/entry", json={"ticker": "AAPL"}).json()["entry_id"]
    client.put(f"/api/trading/journal/entry/{entry_id}/tags", json={"tags": ["earnings"]})

    response = client.get("/api/trading/trades?search=earnings")

    assert response.status_code == 200
    assert [trade["trade_id"] for trade in response.json()["trades"]] == [entry_id]


def test_search_no_matches(client, tmp_path):
    _set_journal_dir(client, tmp_path)
    client.post("/api/trading/journal/entry", json={"ticker": "AAPL"})

    response = client.get("/api/trading/trades?search=nonexistent")

    assert response.status_code == 200
    assert response.json()["trades"] == []
    assert response.json()["total"] == 0


def test_manual_entries_persist_across_requests(tmp_path):
    with _journal_client(tmp_path) as first:
        entry_id = first.post("/api/trading/journal/entry", json={"ticker": "AAPL"}).json()["entry_id"]

    with _journal_client(tmp_path) as second:
        response = second.get("/api/trading/trades")

    assert any(trade["trade_id"] == entry_id for trade in response.json()["trades"])


def test_reflections_persist_across_requests(tmp_path):
    with _journal_client(tmp_path) as first:
        entry_id = first.post("/api/trading/journal/entry", json={"ticker": "AAPL"}).json()["entry_id"]
        first.put(f"/api/trading/journal/entry/{entry_id}/reflection", json={"reflection": "persistent note"})

    with _journal_client(tmp_path) as second:
        detail = second.get(f"/api/trading/trades/{entry_id}")

    assert detail.status_code == 200
    assert detail.json()["reflection"] == "persistent note"


def test_concurrent_appends_no_data_loss(client, tmp_path):
    _set_journal_dir(client, tmp_path)

    def post_entry(i: int) -> int:
        response = client.post("/api/trading/journal/entry", json={"ticker": f"T{i:02d}"})
        return response.status_code

    with ThreadPoolExecutor(max_workers=5) as pool:
        statuses = list(pool.map(post_entry, range(10)))

    response = client.get("/api/trading/trades?limit=20")
    tickers = {trade["ticker"] for trade in response.json()["trades"]}

    assert statuses == [201] * 10
    assert {f"T{i:02d}" for i in range(10)} <= tickers


def test_corrupted_json_preserved(client, tmp_path):
    _set_journal_dir(client, tmp_path)
    journal_dir = tmp_path / "journal"
    journal_dir.mkdir()
    entries_path = journal_dir / "journal_entries.json"
    entries_path.write_text("{not valid json", encoding="utf-8")

    response = client.post("/api/trading/journal/entry", json={"ticker": "AAPL"})

    corrupt_files = list(journal_dir.glob("journal_entries.json.corrupt.*"))
    saved_entries = json.loads(entries_path.read_text(encoding="utf-8"))
    assert response.status_code == 201
    assert len(corrupt_files) == 1
    assert corrupt_files[0].read_text(encoding="utf-8") == "{not valid json"
    assert saved_entries[0]["ticker"] == "AAPL"


def test_search_none_does_not_match_missing_fields(client, tmp_path):
    _set_journal_dir(client, tmp_path)
    client.post("/api/trading/journal/entry", json={"ticker": "AAPL"})

    response = client.get("/api/trading/trades?search=none")

    assert response.status_code == 200
    assert response.json()["trades"] == []


def test_write_permission_error_returns_500(client, tmp_path, monkeypatch):
    _set_journal_dir(client, tmp_path)

    def fail_write(*_args, **_kwargs):
        raise OSError("disk is read-only")

    monkeypatch.setattr(journal_router, "_write_json_atomic_unlocked", fail_write)

    response = client.post("/api/trading/journal/entry", json={"ticker": "AAPL"})

    assert response.status_code == 500
    assert response.json()["error"] == "Failed to write journal"
