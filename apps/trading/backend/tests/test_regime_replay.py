"""Persisted market tags restore the real throttle across app restarts."""
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.services.regime_monitor import RegimeMonitor
from copilot_sdk.config import GraphConfig
from copilot_sdk.graph.factory import create_graph_store


def seed_tags(volatile_count: int) -> list[str]:
    store = create_graph_store(config=GraphConfig.load("trading", profile="test"))
    decision_ids = []
    try:
        for index, regime in enumerate(["trending"] * 40 + ["volatile"] * volatile_count):
            decision_ids.append(store.write_decision("trading", "trend_following", "hold", 0.8, {"signal_alignment": 0.5},
                                 metadata={"regime_tag": regime, "regime_metadata": {"tagged_at": index + 1}}))
        return decision_ids
    finally:
        store.close()


@pytest.mark.parametrize("volatile_count,active", [(15, True), (20, False)])
def test_age_reopen_replays_active_and_stabilized_state(trading_live_age_graph, volatile_count: int, active: bool) -> None:
    if trading_live_age_graph is None:
        pytest.skip("Requires AGE for restart durability")
    decision_ids = seed_tags(volatile_count)
    store = create_graph_store(config=GraphConfig.load("trading", profile="test"))
    try:
        rows = store.get_all_decisions("trading")
        assert {row["decision_id"] for row in rows} == set(decision_ids)
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


def test_app_startup_restores_throttle_endpoint(tmp_path: Path, trading_live_age_graph) -> None:
    # Requires AGE: each app instance reconnects to independently persisted state.
    if trading_live_age_graph is None:
        pytest.skip("Requires AGE for restart durability")
    path = tmp_path / "startup-state"
    store = create_graph_store(config=GraphConfig.load("trading", profile="test"))
    try:
        for index, regime in enumerate(["trending"] * 40 + ["volatile"] * 15):
            store.write_decision(
                "trading", "trend_following", "hold", 0.8, {"signal_alignment": 0.5},
                metadata={"regime_tag": regime, "regime_metadata": {"tagged_at": index + 1}},
            )
    finally:
        store.close()
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
