"""Persisted market tags restore the real throttle across app restarts."""
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.services.regime_monitor import RegimeMonitor
from copilot_sdk.graph.sqlite_store import SQLiteGraphStore


def seed_tags(path: Path, volatile_count: int) -> None:
    store = SQLiteGraphStore(path, domain="trading")
    try:
        for index, regime in enumerate(["trending"] * 40 + ["volatile"] * volatile_count):
            store.write_decision("trading", "trend_following", "hold", 0.8, {"signal_alignment": 0.5},
                                 metadata={"decision_id": f"regime-{index:03}", "created_at": index + 1,
                                           "regime_tag": regime})
    finally:
        store.close()


@pytest.mark.parametrize("volatile_count,active", [(15, True), (20, False)])
def test_sqlite_reopen_replays_active_and_stabilized_state(tmp_path: Path, volatile_count: int, active: bool) -> None:
    path = tmp_path / "regime.db"
    seed_tags(path, volatile_count)
    store = SQLiteGraphStore(path, domain="trading")
    try:
        rows = store.get_all_decisions("trading")
        monitor = RegimeMonitor()
        assert monitor.restore(list(reversed(rows))) == 40 + volatile_count
        assert monitor.is_regime_break is active
        assert monitor.current_regime == "volatile"
        before = monitor.status()
        monitor.restore(rows)
        assert monitor.status() == before  # Repeat restoration is not cumulative.
        assert len(store.get_all_decisions("trading")) == len(rows)
    finally:
        store.close()


def test_app_startup_restores_throttle_endpoint(tmp_path: Path) -> None:
    path = tmp_path / "startup.db"
    seed_tags(path, 15)
    for _ in range(2):
        app = create_app(db_path=path, demo_bundle_path=False, profile="test")
        with TestClient(app) as client:
            body = client.get("/api/trading/regime-status").json()
            assert body["current_regime"] == "volatile"
            assert body["regime_break_active"] is True
            assert body["decisions_in_new_regime"] == 15
            assert body["autonomy_level"] == "restricted"
            assert body["restrictions"]
            assert app.state.l5_startup_status["regime_decisions_replayed"] == 55


def test_untagged_and_other_domain_rows_do_not_invent_regimes() -> None:
    monitor = RegimeMonitor()
    assert monitor.restore([{}, {"domain": "s2p", "metadata": {"regime_tag": "volatile"}}]) == 0
    assert monitor.current_regime is None


def test_bad_chronology_fails_without_clearing_existing_state() -> None:
    monitor = RegimeMonitor()
    monitor.record("trending")
    with pytest.raises(ValueError):
        monitor.restore([{"decision_id": "bad", "metadata": {"regime_tag": "volatile"}}])
    assert monitor.current_regime == "trending"
