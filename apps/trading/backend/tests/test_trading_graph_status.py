from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.graph_status import (
    TradingActiveAGEGraphStore,
    TradingActiveGraphConfig,
    TradingActiveGraphConfigError,
    create_trading_active_graph_store,
)
from app.main import create_app
from app.main import _graph_store
from copilot_sdk.graph import SQLiteGraphStore


TRADING_FACTORS = {
    "signal_alignment": 0.82,
    "market_regime": 0.88,
    "position_sizing": 0.76,
    "timing_quality": 0.64,
    "risk_reward_actual": 0.67,
    "emotional_indicator": 0.71,
    "signal_confidence": 0.50,
    "options_delta_exposure": 0.50,
    "options_iv_percentile": 0.50,
    "options_gamma_risk": 0.50,
}


def test_graph_status_default_sqlite(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    _clear_active_env(monkeypatch)
    client = TestClient(create_app(db_path=tmp_path / "trading.db", demo_bundle_path=False))

    response = client.get("/api/trading/graph/status")

    assert response.status_code == 200
    payload = response.json()
    assert payload["active_backend"] == "sqlite"
    assert payload["requested_backend"] == "sqlite"
    assert payload["sqlite_authoritative"] is True
    assert payload["age_active"] is False
    assert payload["migration_backfill_status"] == "not_in_scope"
    assert payload["receipt_mapping_status"] == "excluded_first_cutover"
    assert payload["active_graph_name"] is None
    assert "password" not in str(payload).lower()


def test_graph_status_ignores_generic_graph_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    _clear_active_env(monkeypatch)
    monkeypatch.setenv("GRAPH_BACKEND", "age")
    monkeypatch.setenv("GRAPH_DSN", "postgresql://postgres:secret@example/db")
    monkeypatch.setenv("GRAPH_NAME", "protocol_v2_test")

    client = TestClient(create_app(db_path=tmp_path / "trading.db", demo_bundle_path=False))
    payload = client.get("/api/trading/graph/status").json()

    assert payload["active_backend"] == "sqlite"
    assert payload["ignored_generic_graph_env"] is True
    assert "secret" not in str(payload)


@pytest.mark.parametrize(
    ("env", "message"),
    [
        ({"TRADING_ACTIVE_GRAPH_BACKEND": "neo4j"}, "sqlite' or 'age"),
        (
            {
                "TRADING_ACTIVE_GRAPH_BACKEND": "age",
                "TRADING_ACTIVE_AGE_GRAPH": "protocol_v2_test",
                "TRADING_ACTIVE_AGE_DOMAIN": "trading",
                "TRADING_ACTIVE_AGE_TEST_MODE": "1",
            },
            "DSN",
        ),
        (
            {
                "TRADING_ACTIVE_GRAPH_BACKEND": "age",
                "TRADING_ACTIVE_AGE_DSN": "postgresql://example/test",
                "TRADING_ACTIVE_AGE_DOMAIN": "trading",
                "TRADING_ACTIVE_AGE_TEST_MODE": "1",
            },
            "GRAPH",
        ),
        (
            {
                "TRADING_ACTIVE_GRAPH_BACKEND": "age",
                "TRADING_ACTIVE_AGE_DSN": "postgresql://example/test",
                "TRADING_ACTIVE_AGE_GRAPH": " ",
                "TRADING_ACTIVE_AGE_DOMAIN": "trading",
                "TRADING_ACTIVE_AGE_TEST_MODE": "1",
            },
            "GRAPH",
        ),
        (
            {
                "TRADING_ACTIVE_GRAPH_BACKEND": "age",
                "TRADING_ACTIVE_AGE_DSN": " ",
                "TRADING_ACTIVE_AGE_GRAPH": "protocol_v2_test",
                "TRADING_ACTIVE_AGE_DOMAIN": "trading",
                "TRADING_ACTIVE_AGE_TEST_MODE": "1",
            },
            "DSN",
        ),
        (
            {
                "TRADING_ACTIVE_GRAPH_BACKEND": "age",
                "TRADING_ACTIVE_AGE_DSN": "postgresql://example/test",
                "TRADING_ACTIVE_AGE_GRAPH": "soc_graph",
                "TRADING_ACTIVE_AGE_DOMAIN": "trading",
                "TRADING_ACTIVE_AGE_TEST_MODE": "1",
            },
            "soc_graph",
        ),
        (
            {
                "TRADING_ACTIVE_GRAPH_BACKEND": "age",
                "TRADING_ACTIVE_AGE_DSN": "postgresql://example/test",
                "TRADING_ACTIVE_AGE_GRAPH": "protocol_v2_test",
                "TRADING_ACTIVE_AGE_DOMAIN": "trading",
            },
            "TEST_MODE",
        ),
        (
            {
                "TRADING_ACTIVE_GRAPH_BACKEND": "age",
                "TRADING_ACTIVE_AGE_DSN": "postgresql://example/test",
                "TRADING_ACTIVE_AGE_GRAPH": "protocol_v2_test",
                "TRADING_ACTIVE_AGE_DOMAIN": "purchasing",
                "TRADING_ACTIVE_AGE_TEST_MODE": "1",
            },
            "trading",
        ),
        (
            {
                "TRADING_ACTIVE_GRAPH_BACKEND": "age",
                "TRADING_ACTIVE_AGE_DSN": "postgresql://example/test",
                "TRADING_ACTIVE_AGE_GRAPH": "protocol_v2_test",
                "TRADING_ACTIVE_AGE_DOMAIN": " ",
                "TRADING_ACTIVE_AGE_TEST_MODE": "1",
            },
            "blank",
        ),
        (
            {
                "TRADING_ACTIVE_GRAPH_BACKEND": "age",
                "TRADING_ACTIVE_AGE_DSN": "postgresql://example/test",
                "TRADING_ACTIVE_AGE_GRAPH": "unreviewed_product_graph",
                "TRADING_ACTIVE_AGE_DOMAIN": "trading",
                "TRADING_ACTIVE_AGE_TEST_MODE": "0",
            },
            "allow-listed",
        ),
        (
            {
                "TRADING_ACTIVE_GRAPH_BACKEND": "age",
                "TRADING_ACTIVE_AGE_DSN": "postgresql://example/test",
                "TRADING_ACTIVE_AGE_GRAPH": "protocol_v2_test",
                "TRADING_ACTIVE_AGE_DOMAIN": "trading",
                "TRADING_ACTIVE_AGE_TEST_MODE": "1",
                "TRADING_SHADOW_AGE": "1",
            },
            "conflicts",
        ),
    ],
)
def test_active_age_config_guards(env: dict[str, str], message: str):
    with pytest.raises(TradingActiveGraphConfigError, match=message):
        TradingActiveGraphConfig.from_env(env)


def test_product_like_config_validates_but_store_construction_is_blocked():
    config = TradingActiveGraphConfig.from_env(
        {
            "TRADING_ACTIVE_GRAPH_BACKEND": "age",
            "TRADING_ACTIVE_AGE_DSN": "postgresql://example/product",
            "TRADING_ACTIVE_AGE_GRAPH": "governed_copilot_graph",
            "TRADING_ACTIVE_AGE_DOMAIN": "trading",
            "TRADING_ACTIVE_AGE_TEST_MODE": "0",
        }
    )

    assert config.graph_kind() == "product"
    with pytest.raises(TradingActiveGraphConfigError, match="product AGE writes remain blocked"):
        create_trading_active_graph_store(config, store_factory=lambda **_: FakeAGEStore())


def test_shared_soc_graph_requires_exact_trading_authorization():
    config = TradingActiveGraphConfig.from_env(
        {
            "TRADING_ACTIVE_GRAPH_BACKEND": "age",
            "TRADING_ACTIVE_AGE_DSN": "postgresql://example/product",
            "TRADING_ACTIVE_AGE_GRAPH": "soc_graph",
            "TRADING_ACTIVE_AGE_DOMAIN": "trading",
            "TRADING_ACTIVE_AGE_TEST_MODE": "0",
            "TRADING_SHARED_GRAPH_AUTHORIZED": "trading:soc_graph",
        }
    )
    active = create_trading_active_graph_store(config, store_factory=lambda **_: FakeAGEStore())
    assert isinstance(active, TradingActiveAGEGraphStore)
    assert active.active_phase == "shared_graph"


@pytest.mark.parametrize("authorization", [None, "soc:soc_graph"])
def test_shared_soc_graph_rejects_missing_or_wrong_domain_authorization(authorization):
    env = {
        "TRADING_ACTIVE_GRAPH_BACKEND": "age",
        "TRADING_ACTIVE_AGE_DSN": "postgresql://example/product",
        "TRADING_ACTIVE_AGE_GRAPH": "soc_graph",
        "TRADING_ACTIVE_AGE_DOMAIN": "trading",
        "TRADING_ACTIVE_AGE_TEST_MODE": "0",
    }
    if authorization is not None:
        env["TRADING_SHARED_GRAPH_AUTHORIZED"] = authorization
    with pytest.raises(TradingActiveGraphConfigError, match="TRADING_SHARED_GRAPH_AUTHORIZED=trading:soc_graph"):
        TradingActiveGraphConfig.from_env(env)


def test_generic_graph_backend_age_still_downgrades_to_sqlite(monkeypatch, tmp_path):
    _clear_active_env(monkeypatch)
    monkeypatch.setenv("GRAPH_BACKEND", "age")
    store = _graph_store(tmp_path / "trading.db")
    try:
        assert isinstance(store, SQLiteGraphStore)
    finally:
        store.close()


def test_active_age_status_redacts_dsn_and_reports_test_mode(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    _set_active_age_env(monkeypatch, dsn="postgresql://postgres:secret@example/db?password=other")
    client = TestClient(
        create_app(
            db_path=tmp_path / "trading.db",
            demo_bundle_path=False,
            active_store_factory=lambda **_: FakeAGEStore(),
        )
    )

    payload = client.get("/api/trading/graph/status").json()

    assert payload["active_backend"] == "age"
    assert payload["age_active"] is True
    assert payload["graph_kind"] == "test"
    assert payload["active_domain"] == "trading"
    assert payload["active_test_mode"] is True
    assert payload["migration_backfill_status"] == "not_in_scope"
    assert payload["receipt_mapping_status"] == "excluded_first_cutover"
    assert "secret" not in str(payload)
    assert "password=other" not in str(payload)


def test_active_age_score_learn_and_duplicate_invariant(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    client, fake = _active_client(tmp_path, monkeypatch)

    score = _score(client)
    decision_id = score["decision_id"]
    assert decision_id in fake.decisions
    assert fake.decisions[decision_id]["decision_id"] == decision_id

    learn = _learn(client, decision_id, score["action"])
    assert learn["decision_id"] == decision_id
    assert fake.decisions[decision_id]["status"] == "confirmed"
    assert len(fake.outcomes[decision_id]) == 1

    duplicate = client.post(
        "/api/learn",
        json={"decision_id": decision_id, "actual_action": score["action"]},
    )
    assert duplicate.status_code == 400


def test_social_score_as_and_webhook_auto_score_write_active_age_decisions(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    client, fake = _active_client(tmp_path, monkeypatch)

    social = client.post(
        "/api/trading/score-as",
        json={"category": "trend_following", "factors": TRADING_FACTORS, "trader_id": "alice"},
    )
    assert social.status_code == 200
    social_payload = social.json()
    assert social_payload["decision_id"] in fake.decisions
    assert fake.decisions[social_payload["decision_id"]]["metadata"]["trader_id"] == "alice"

    webhook = client.post(
        "/api/trading/webhook/tradingview",
        json={
            "ticker": "AAPL",
            "action": "buy",
            "price": 150.25,
            "strategy": "RSI_Oversold",
            "category": "mean_reversion",
            "auto_score": True,
            "indicators": {"rsi": 28.5, "macd": -0.3, "atr": 2.1, "volume": 1_500_000},
        },
    )
    assert webhook.status_code == 200
    webhook_payload = webhook.json()
    assert webhook_payload["scored"] is True
    assert webhook_payload["decision_id"] in fake.decisions
    assert fake.decisions[webhook_payload["decision_id"]]["metadata"]["source"] == "tradingview_webhook"


def test_prescore_and_read_like_routes_do_not_create_decisions_under_active_age(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    client, fake = _active_client(tmp_path, monkeypatch)

    before = fake.count_decisions("trading")
    for method, path, json_body in (
        ("POST", "/api/trading/prescore", {"ticker": "AAPL", "category": "trend_following"}),
        ("GET", "/api/trading/webhook/config", None),
        ("GET", "/api/trading/webhook/history", None),
        ("GET", "/api/trading/social", None),
        ("GET", "/api/trading/regime", None),
    ):
        if method == "POST":
            response = client.post(path, json=json_body)
        else:
            response = client.get(path)
        assert response.status_code == 200
    assert fake.count_decisions("trading") == before


def test_rollback_to_sqlite_proves_no_hidden_reconciliation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    active_client, fake = _active_client(tmp_path, monkeypatch)
    active_score = _score(active_client)
    assert active_score["decision_id"] in fake.decisions

    _clear_active_env(monkeypatch)
    sqlite_db = tmp_path / "rollback.sqlite"
    sqlite_client = TestClient(create_app(db_path=sqlite_db, demo_bundle_path=False))
    sqlite_score = _score(sqlite_client)
    _learn(sqlite_client, sqlite_score["decision_id"], sqlite_score["action"])

    status = sqlite_client.get("/api/trading/graph/status").json()
    assert status["active_backend"] == "sqlite"
    assert status["age_active"] is False
    assert active_score["decision_id"] in fake.decisions
    assert _sqlite_decision_count(sqlite_db) == 1


def test_active_store_constructs_with_factory_after_guards():
    config = _active_config()
    calls: list[dict[str, Any]] = []

    def factory(**kwargs):
        calls.append(kwargs)
        return FakeAGEStore()

    active = create_trading_active_graph_store(config, store_factory=factory)

    assert isinstance(active, TradingActiveAGEGraphStore)
    assert calls == [
        {
            "backend": "age",
            "domain": "trading",
            "dsn": "postgresql://example/test",
            "graph_name": "protocol_v2_test",
            "env": {},
            "test_mode": True,
        }
    ]


def test_direct_store_construction_rejects_shadow_conflict(monkeypatch: pytest.MonkeyPatch):
    config = _active_config()
    monkeypatch.setenv("TRADING_SHADOW_AGE", "1")
    called = False

    def factory(**kwargs):
        nonlocal called
        called = True
        return FakeAGEStore()

    with pytest.raises(TradingActiveGraphConfigError, match="conflicts"):
        create_trading_active_graph_store(config, store_factory=factory)
    assert called is False


def _active_client(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[TestClient, "FakeAGEStore"]:
    _set_active_age_env(monkeypatch)
    fake = FakeAGEStore()
    client = TestClient(
        create_app(
            db_path=tmp_path / "trading.db",
            demo_bundle_path=False,
            active_store_factory=lambda **_: fake,
        )
    )
    return client, fake


def _score(client: TestClient) -> dict[str, Any]:
    response = client.post(
        "/api/score",
        json={"category": "trend_following", "factors": TRADING_FACTORS},
    )
    assert response.status_code == 200
    return response.json()


def _learn(client: TestClient, decision_id: str, actual_action: str) -> dict[str, Any]:
    response = client.post(
        "/api/learn",
        json={"decision_id": decision_id, "actual_action": actual_action},
    )
    assert response.status_code == 200
    return response.json()


def _active_config() -> TradingActiveGraphConfig:
    return TradingActiveGraphConfig.from_env(
        {
            "TRADING_ACTIVE_GRAPH_BACKEND": "age",
            "TRADING_ACTIVE_AGE_DSN": "postgresql://example/test",
            "TRADING_ACTIVE_AGE_GRAPH": "protocol_v2_test",
            "TRADING_ACTIVE_AGE_DOMAIN": "trading",
            "TRADING_ACTIVE_AGE_TEST_MODE": "1",
        }
    )


def _set_active_age_env(monkeypatch: pytest.MonkeyPatch, *, dsn: str = "postgresql://example/test") -> None:
    _clear_active_env(monkeypatch)
    monkeypatch.setenv("TRADING_ACTIVE_GRAPH_BACKEND", "age")
    monkeypatch.setenv("TRADING_ACTIVE_AGE_DSN", dsn)
    monkeypatch.setenv("TRADING_ACTIVE_AGE_GRAPH", "protocol_v2_test")
    monkeypatch.setenv("TRADING_ACTIVE_AGE_DOMAIN", "trading")
    monkeypatch.setenv("TRADING_ACTIVE_AGE_TEST_MODE", "1")


def _clear_active_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for key in (
        "TRADING_ACTIVE_GRAPH_BACKEND",
        "TRADING_ACTIVE_AGE_DSN",
        "TRADING_ACTIVE_AGE_GRAPH",
        "TRADING_ACTIVE_AGE_DOMAIN",
        "TRADING_ACTIVE_AGE_TEST_MODE",
        "TRADING_SHARED_GRAPH_AUTHORIZED",
        "TRADING_SHADOW_AGE",
        "GRAPH_BACKEND",
        "GRAPH_DSN",
        "GRAPH_NAME",
        "GRAPH_DOMAIN",
        "AGE_DSN",
        "AGE_GRAPH_NAME",
    ):
        monkeypatch.delenv(key, raising=False)


def _sqlite_decision_count(db_path: Path) -> int:
    from copilot_sdk.graph import SQLiteGraphStore

    store = SQLiteGraphStore(db_path, domain="trading")
    try:
        return store.count_decisions("trading")
    finally:
        store.close()


class FakeAGEStore:  # MOCK-OK: AGE protocol compliance without external AGE
    domain = "trading"

    def __init__(self) -> None:
        self.decisions: dict[str, dict[str, Any]] = {}
        self.outcomes: dict[str, list[dict[str, Any]]] = {}
        self.centroids: list[dict[str, Any]] = []

    def write_governed_decision(self, **kwargs: Any) -> None:
        decision_id = str(kwargs["decision_id"])
        if decision_id in self.decisions and self.decisions[decision_id] != kwargs:
            raise ValueError("conflicting decision")
        self.decisions[decision_id] = {
            **kwargs,
            "status": "pending",
            "recommended_action": kwargs["recommended_action"],
            "action": kwargs["recommended_action"],
            "factors": {
                name: value
                for name, value in zip(kwargs["factor_names"], kwargs["factor_vector"])
            },
            "metadata": dict(kwargs.get("metadata") or {}),
        }

    def get_decision(self, decision_id: str) -> dict[str, Any] | None:
        decision = self.decisions.get(decision_id)
        return dict(decision) if decision is not None else None

    def write_outcome(
        self,
        decision_id: str,
        actual_action: str,
        is_correct: bool,
        metadata: dict[str, Any] | None = None,
        domain: str | None = None,
    ) -> None:
        if decision_id not in self.decisions:
            raise KeyError(decision_id)
        if decision_id in self.outcomes:
            raise ValueError("outcome already exists")
        outcome = {
            "decision_id": decision_id,
            "actual_action": actual_action,
            "is_correct": bool(is_correct),
            "metadata": dict(metadata or {}),
        }
        self.outcomes[decision_id] = [outcome]
        decision = self.decisions[decision_id]
        decision["actual_action"] = actual_action
        decision["is_correct"] = bool(is_correct)
        decision["outcome"] = "confirmed" if is_correct else "overridden"
        decision["status"] = decision["outcome"]
        decision["outcome_metadata"] = dict(metadata or {})

    def load_latest_centroids(self, domain: str) -> Any | None:
        return None

    def save_centroids(
        self,
        domain: str,
        category: str,
        centroids: Any,
        metadata: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> None:
        self.centroids.append({"domain": domain, "category": category, "metadata": metadata or {}, **kwargs})

    def get_centroid_checkpoints(self, domain: str, **kwargs: Any) -> list[dict[str, Any]]:
        return list(self.centroids)

    def get_verified_decisions(self, domain: str) -> list[dict[str, Any]]:
        return [
            dict(decision)
            for decision in self.decisions.values()
            if decision.get("status") in {"confirmed", "overridden"}
        ]

    def get_all_decisions(self, domain: str) -> list[dict[str, Any]]:
        return [dict(decision) for decision in self.decisions.values()]

    def get_decisions(
        self,
        domain: str,
        category: str | None = None,
        limit: int = 400,
    ) -> list[dict[str, Any]]:
        decisions = self.get_all_decisions(domain)
        if category is not None:
            decisions = [decision for decision in decisions if decision.get("category") == category]
        return decisions[:limit]

    def count_decisions(self, domain: str) -> int:
        return len(self.decisions)

    def count_verified(self, domain: str) -> int:
        return len(self.get_verified_decisions(domain))

    def count_verified_decisions(self, domain: str) -> int:
        return self.count_verified(domain)

    def count_correct(self, domain: str) -> int:
        return sum(1 for decision in self.decisions.values() if decision.get("is_correct") is True)

    def count_archived(self, domain: str) -> int:
        return 0

    def archive_old_decisions(self, domain: str, keep_recent: int = 800) -> int:
        return 0

    def get_evolution_events(self, domain: str, **kwargs: Any) -> list[dict[str, Any]]:
        return []

    def close(self) -> None:
        return None
