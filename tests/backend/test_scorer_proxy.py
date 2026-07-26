from __future__ import annotations

import threading
from concurrent.futures import ThreadPoolExecutor
from types import SimpleNamespace
from pathlib import Path
import pytest

from copilot_sdk.backend import scorer_proxy as scorer_proxy_module
from copilot_sdk.backend.scorer_proxy import FreshScorerProxy
from copilot_sdk.graph import SQLiteGraphStore
from copilot_sdk.scoring.scorer import CompoundingScorer


TRADING_FACTORS = {
    "signal_alignment": 0.82,
    "market_regime": 0.88,
    "position_sizing": 0.76,
    "timing_quality": 0.34,
    "risk_reward_actual": 0.67,
    "emotional_indicator": 0.71,
}


@pytest.fixture(autouse=True)
def _test_profile_for_proxy_scorers(monkeypatch):
    original = CompoundingScorer.from_preset

    def from_preset(*args, **kwargs):
        kwargs.setdefault("profile", "test")
        return original(*args, **kwargs)

    monkeypatch.setattr(CompoundingScorer, "from_preset", from_preset)


def _graph_store(db_path: str | Path):
    store = SQLiteGraphStore(str(db_path), domain="trading")
    store.penalty_ratio = 2.0
    return store


class FakeScorer:  # MOCK-OK: proxy construction/cache sentinel, real scorer paths covered above
    def __init__(self, label: str = "fake") -> None:
        self.label = label
        self.calls: list[str] = []
        self._counter = 0
        self._lock = threading.Lock()

    def score(self, factors, category, metadata=None):
        with self._lock:
            self._counter += 1
            decision_id = f"{self.label}-{self._counter}"
        self.calls.append("score")
        return SimpleNamespace(
            decision_id=decision_id,
            action="strong_execution",
            category=category,
            factors=dict(factors),
        )

    def learn(
        self,
        decision_id,
        actual_action,
        outcome="confirmed",
        *,
        consolidate=False,
        context=None,
    ):
        self.calls.append("learn")
        return SimpleNamespace(decision_id=decision_id, outcome=outcome)

    def fingerprint(self):
        self.calls.append("fingerprint")
        return {"factors": []}

    def trajectory(self):
        self.calls.append("trajectory")
        return {"points": []}

    def get_phase(self):
        self.calls.append("get_phase")
        return "A"

    def get_alpha(self):
        self.calls.append("get_alpha")
        return 0.0


def test_fresh_scorer_proxy_exposes_required_methods(tmp_path):
    proxy = FreshScorerProxy("trading", tmp_path / "proxy.db", _graph_store, profile="test")

    for name in (
        "score",
        "score_read_only",
        "learn",
        "fingerprint",
        "trajectory",
        "get_phase",
        "get_alpha",
        "get_dk_weights",
        "get_verified_count",
    ):
        assert callable(getattr(proxy, name))


def test_fresh_scorer_proxy_scores_and_learns(tmp_path):
    proxy = FreshScorerProxy("trading", tmp_path / "proxy.db", _graph_store, profile="test")

    score = proxy.score(TRADING_FACTORS, "trend_following")
    learn = proxy.learn(score.decision_id, score.action)

    assert score.category == "trend_following"
    assert score.action in {"strong_execution", "partial_execution", "poor_execution"}
    assert learn.decision_id == score.decision_id
    assert proxy.graph_store.count_verified("trading") == 1


def test_fresh_scorer_proxy_uses_shared_graph_store(tmp_path):
    proxy = FreshScorerProxy("trading", tmp_path / "proxy.db", _graph_store, profile="test")

    scorer_one = proxy._scorer()
    scorer_two = proxy._scorer()

    assert scorer_one is scorer_two
    assert scorer_one._graph_store is proxy.graph_store
    assert scorer_two._graph_store is proxy.graph_store


def test_fresh_scorer_proxy_close_helper_leaves_shared_store_open(tmp_path):
    proxy = FreshScorerProxy("trading", tmp_path / "proxy.db", _graph_store, profile="test")
    scorer = proxy._scorer()

    proxy._close_scorer_store(scorer)
    score = proxy.score(TRADING_FACTORS, "trend_following")
    proxy.fingerprint()
    learn = proxy.learn(score.decision_id, score.action)

    assert learn.decision_id == score.decision_id
    assert proxy.graph_store.count_verified("trading") == 1


def test_fresh_scorer_proxy_sequential_scores_share_store(tmp_path):
    proxy = FreshScorerProxy("trading", tmp_path / "proxy.db", _graph_store, profile="test")

    first = proxy.score(TRADING_FACTORS, "trend_following")
    second = proxy.score(TRADING_FACTORS, "trend_following")

    assert first.decision_id != second.decision_id
    assert len(proxy.graph_store.get_all_decisions("trading")) == 2


def test_fresh_scorer_proxy_phase_and_alpha(tmp_path):
    proxy = FreshScorerProxy("trading", tmp_path / "proxy.db", _graph_store, profile="test")

    assert proxy.get_phase() in {"A", "B"}
    assert isinstance(proxy.get_alpha(), float)


def test_fresh_scorer_proxy_uses_rlock(tmp_path):
    proxy = FreshScorerProxy("trading", tmp_path / "proxy.db", _graph_store, profile="test")

    assert isinstance(proxy._lock, type(threading.RLock()))


def test_fresh_scorer_proxy_starts_empty_and_caches_after_first_call(tmp_path, monkeypatch):
    fake = FakeScorer()
    monkeypatch.setattr(  # MOCK-OK: isolates proxy lazy construction, not learning behavior
        scorer_proxy_module.CompoundingScorer,
        "from_preset",
        lambda *args, **kwargs: fake,
    )
    first_proxy = FreshScorerProxy("trading", tmp_path / "first.db", _graph_store, profile="test")
    second_proxy = FreshScorerProxy("trading", tmp_path / "second.db", _graph_store, profile="test")

    assert first_proxy._scorer_instance is None
    assert second_proxy._scorer_instance is None

    first_proxy.get_phase()

    assert first_proxy._scorer_instance is fake
    assert second_proxy._scorer_instance is None


def test_fresh_scorer_proxy_constructs_scorer_once_per_proxy(tmp_path, monkeypatch):
    calls = []
    fake = FakeScorer()

    def fake_from_preset(*args, **kwargs):
        calls.append((args, kwargs))
        return fake

    monkeypatch.setattr(scorer_proxy_module.CompoundingScorer, "from_preset", fake_from_preset)  # MOCK-OK: verifies one construction call
    proxy = FreshScorerProxy("trading", tmp_path / "proxy.db", _graph_store, profile="test")

    score = proxy.score(TRADING_FACTORS, "trend_following")
    proxy.learn(score.decision_id, score.action)
    proxy.fingerprint()
    proxy.trajectory()
    proxy.get_phase()
    proxy.get_alpha()

    assert len(calls) == 1
    assert calls[0][0] == ("trading",)
    assert calls[0][1]["graph_store"] is proxy.graph_store
    assert calls[0][1]["evolve"] is True
    assert calls[0][1]["consolidation_enabled"] is True
    assert fake.calls == [
        "score",
        "learn",
        "fingerprint",
        "trajectory",
        "get_phase",
        "get_alpha",
    ]


def test_fresh_scorer_proxy_read_methods_do_not_reconstruct_scorer(tmp_path, monkeypatch):
    calls = []
    fake = FakeScorer()

    def fake_from_preset(*args, **kwargs):
        calls.append((args, kwargs))
        return fake

    monkeypatch.setattr(scorer_proxy_module.CompoundingScorer, "from_preset", fake_from_preset)  # MOCK-OK: verifies cached read methods
    proxy = FreshScorerProxy("trading", tmp_path / "proxy.db", _graph_store, profile="test")

    proxy.score(TRADING_FACTORS, "trend_following")
    proxy.fingerprint()
    proxy.trajectory()
    proxy.get_phase()
    proxy.get_alpha()

    assert len(calls) == 1


def test_fresh_scorer_proxy_keeps_proxy_instances_isolated(tmp_path, monkeypatch):
    created = []

    def fake_from_preset(*args, **kwargs):
        scorer = FakeScorer(label=f"fake-{len(created)}")
        created.append((scorer, kwargs["graph_store"]))
        return scorer

    monkeypatch.setattr(scorer_proxy_module.CompoundingScorer, "from_preset", fake_from_preset)  # MOCK-OK: verifies proxy instance isolation
    first = FreshScorerProxy("trading", tmp_path / "one.db", _graph_store, profile="test")
    second = FreshScorerProxy("trading", tmp_path / "two.db", _graph_store, profile="test")

    first_score = first.score(TRADING_FACTORS, "trend_following")
    second_score = second.score(TRADING_FACTORS, "trend_following")

    assert len(created) == 2
    assert first._scorer_instance is created[0][0]
    assert second._scorer_instance is created[1][0]
    assert first._scorer_instance is not second._scorer_instance
    assert created[0][1] is first.graph_store
    assert created[1][1] is second.graph_store
    assert first_score.decision_id.startswith("fake-0-")
    assert second_score.decision_id.startswith("fake-1-")


def test_fresh_scorer_proxy_concurrent_scores_share_cached_scorer(tmp_path):
    proxy = FreshScorerProxy("trading", tmp_path / "proxy.db", _graph_store, profile="test")

    with ThreadPoolExecutor(max_workers=4) as executor:
        results = list(
            executor.map(
                lambda _: proxy.score(TRADING_FACTORS, "trend_following"),
                range(4),
            )
        )

    decision_ids = {result.decision_id for result in results}
    assert len(decision_ids) == 4
    assert len(proxy.graph_store.get_all_decisions("trading")) == 4


def test_fresh_scorer_proxy_interleaved_score_learn_score_uses_shared_state(tmp_path):
    proxy = FreshScorerProxy("trading", tmp_path / "proxy.db", _graph_store, profile="test")

    first = proxy.score(TRADING_FACTORS, "trend_following")
    learn = proxy.learn(first.decision_id, first.action)
    second = proxy.score(TRADING_FACTORS, "trend_following")

    assert learn.decision_id == first.decision_id
    assert first.decision_id != second.decision_id
    assert proxy.graph_store.count_verified("trading") == 1
    assert len(proxy.graph_store.get_all_decisions("trading")) == 2


def test_scorer_proxy_serialized(tmp_path):
    proxy = FreshScorerProxy("trading", tmp_path / "proxy.db", _graph_store, profile="test")

    def score_once(index: int):
        factors = dict(TRADING_FACTORS)
        factors["timing_quality"] = 0.25 + (index * 0.02)
        return proxy.score(factors, "trend_following")

    with ThreadPoolExecutor(max_workers=8) as executor:
        results = list(executor.map(score_once, range(16)))

    assert len({result.decision_id for result in results}) == 16
    assert len(proxy.graph_store.get_all_decisions("trading")) == 16


def test_scorer_proxy_score_and_learn(tmp_path):
    proxy = FreshScorerProxy("trading", tmp_path / "proxy.db", _graph_store, profile="test")

    def score_and_learn(index: int):
        factors = dict(TRADING_FACTORS)
        factors["signal_alignment"] = 0.55 + (index * 0.01)
        result = proxy.score(factors, "trend_following")
        return proxy.learn(
            result.decision_id,
            result.action,
            context={"worker": index},
        )

    with ThreadPoolExecutor(max_workers=8) as executor:
        results = list(executor.map(score_and_learn, range(8)))

    assert len({result.decision_id for result in results}) == 8
    assert proxy.graph_store.count_verified("trading") == 8


def test_app_mains_no_longer_define_local_fresh_proxy():
    repo_root = Path(__file__).resolve().parents[2]
    main_files = [
        repo_root / "apps" / "trading" / "backend" / "app" / "main.py",
        repo_root / "apps" / "purchasing" / "backend" / "app" / "main.py",
        repo_root / "apps" / "dataops" / "backend" / "app" / "main.py",
    ]

    for path in main_files:
        assert "class _FreshScorerProxy" not in path.read_text(encoding="utf-8")
