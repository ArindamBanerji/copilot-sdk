from __future__ import annotations

from pathlib import Path

from copilot_sdk.backend.scorer_proxy import FreshScorerProxy
from copilot_sdk.graph import SQLiteGraphStore


TRADING_FACTORS = {
    "conviction": 0.82,
    "research_depth": 0.88,
    "technical_signal": 0.76,
    "position_size": 0.34,
    "time_horizon": 0.67,
    "market_regime": 0.71,
}


def _graph_store(db_path: str | Path):
    store = SQLiteGraphStore(str(db_path), domain="trading")
    store.penalty_ratio = 2.0
    return store


def test_fresh_scorer_proxy_exposes_required_methods(tmp_path):
    proxy = FreshScorerProxy("trading", tmp_path / "proxy.db", _graph_store)

    for name in ("score", "learn", "fingerprint", "trajectory", "get_phase", "get_alpha"):
        assert callable(getattr(proxy, name))


def test_fresh_scorer_proxy_scores_and_learns(tmp_path):
    proxy = FreshScorerProxy("trading", tmp_path / "proxy.db", _graph_store)

    score = proxy.score(TRADING_FACTORS, "equity_long")
    learn = proxy.learn(score.decision_id, score.action)

    assert score.category == "equity_long"
    assert score.action in {"buy", "hold", "sell"}
    assert learn.decision_id == score.decision_id
    assert proxy.graph_store.count_verified("trading") == 1


def test_fresh_scorer_proxy_phase_and_alpha(tmp_path):
    proxy = FreshScorerProxy("trading", tmp_path / "proxy.db", _graph_store)

    assert proxy.get_phase() in {"A", "B"}
    assert isinstance(proxy.get_alpha(), float)


def test_app_mains_no_longer_define_local_fresh_proxy():
    repo_root = Path(__file__).resolve().parents[2]
    main_files = [
        repo_root / "apps" / "trading" / "backend" / "app" / "main.py",
        repo_root / "apps" / "purchasing" / "backend" / "app" / "main.py",
        repo_root / "apps" / "dataops" / "backend" / "app" / "main.py",
    ]

    for path in main_files:
        assert "class _FreshScorerProxy" not in path.read_text(encoding="utf-8")
