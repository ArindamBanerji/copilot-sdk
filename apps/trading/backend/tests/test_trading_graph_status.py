from __future__ import annotations

from pathlib import Path
from typing import Any, cast

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
from copilot_sdk.graph import InMemoryGraphStore
from copilot_sdk.graph.legacy_signal_filter import LegacySignalFilteringGraphStore


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


def test_graph_status_default_memory(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    _clear_active_env(monkeypatch)
    _configure_explicit_memory(tmp_path, monkeypatch)
    client = TestClient(create_app(db_path=tmp_path / "trading.db", demo_bundle_path=False))

    response = client.get("/api/trading/graph/status")

    assert response.status_code == 200
    payload = response.json()
    assert payload["active_backend"] == "memory"
    assert payload["requested_backend"] == "memory"
    assert payload["memory_authoritative"] is True
    assert payload["age_active"] is False
    assert payload["migration_backfill_status"] == "not_in_scope"
    assert payload["receipt_mapping_status"] == "excluded_first_cutover"
    assert payload["active_graph_name"] is None
    assert "password" not in str(payload).lower()


def test_graph_status_ignores_generic_graph_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    _clear_active_env(monkeypatch)
    _configure_explicit_memory(tmp_path, monkeypatch)
    monkeypatch.setenv("GRAPH_BACKEND", "age")
    monkeypatch.setenv("GRAPH_DSN", "postgresql://postgres:secret@example/db")
    monkeypatch.setenv("GRAPH_NAME", "protocol_v2_test")

    client = TestClient(create_app(db_path=tmp_path / "trading.db", demo_bundle_path=False))
    payload = client.get("/api/trading/graph/status").json()

    assert payload["active_backend"] == "memory"
    assert payload["ignored_generic_graph_env"] is True
    assert "secret" not in str(payload)


@pytest.mark.parametrize(
    ("env", "message"),
    [
        ({"TRADING_ACTIVE_GRAPH_BACKEND": "neo4j"}, "memory' or 'age"),
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
            "protocol_v2_test",
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
    with pytest.raises(TradingActiveGraphConfigError, match="allow-listed"):
        TradingActiveGraphConfig.from_env(
            {
                "TRADING_ACTIVE_GRAPH_BACKEND": "age",
                "TRADING_ACTIVE_AGE_DSN": "postgresql://example/product",
                "TRADING_ACTIVE_AGE_GRAPH": "governed_copilot_graph",
                "TRADING_ACTIVE_AGE_DOMAIN": "trading",
                "TRADING_ACTIVE_AGE_TEST_MODE": "0",
            }
        )


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
    active = create_trading_active_graph_store(config, store_factory=lambda **_: InMemoryGraphStore(domain="trading"))
    assert isinstance(active, TradingActiveAGEGraphStore)
    assert active.active_phase == "shared_graph"


@pytest.mark.parametrize("authorization", [None, "soc:soc_graph"])
def test_shared_soc_graph_uses_derived_authorization(authorization):
    env = {
        "TRADING_ACTIVE_GRAPH_BACKEND": "age",
        "TRADING_ACTIVE_AGE_DSN": "postgresql://example/product",
        "TRADING_ACTIVE_AGE_GRAPH": "soc_graph",
        "TRADING_ACTIVE_AGE_DOMAIN": "trading",
        "TRADING_ACTIVE_AGE_TEST_MODE": "0",
    }
    if authorization is not None:
        env["TRADING_SHARED_GRAPH_AUTHORIZED"] = authorization
    config = TradingActiveGraphConfig.from_env(env)
    assert config.shared_graph_authorization == "trading:soc_graph"


def test_generic_graph_backend_age_does_not_downgrade(monkeypatch, tmp_path):
    _clear_active_env(monkeypatch)
    monkeypatch.setenv("GRAPH_BACKEND", "age")
    with pytest.raises(ValueError):
        _graph_store(tmp_path / "trading.db")


def test_requested_age_status_detects_memory_and_redacts_dsn(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    _set_active_age_env(monkeypatch, dsn="postgresql://postgres:secret@example/db?password=other")
    client = TestClient(
        create_app(
            db_path=tmp_path / "trading.db",
            demo_bundle_path=False,
            active_store_factory=lambda **_: InMemoryGraphStore(domain="trading"),
        )
    )

    payload = client.get("/api/trading/graph/status").json()

    assert payload["active_backend"] == "memory"
    assert payload["age_active"] is False
    assert payload["last_error"] is not None
    assert payload["cutover_ready"] is False
    assert payload["graph_kind"] == "test"
    assert payload["active_domain"] == "trading"
    assert payload["active_test_mode"] is True
    assert payload["migration_backfill_status"] == "not_in_scope"
    assert payload["receipt_mapping_status"] == "excluded_first_cutover"
    assert "secret" not in str(payload)
    assert "password=other" not in str(payload)


@pytest.mark.age
def test_active_age_score_learn_and_duplicate_invariant(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    disposable_age,
):
    client, fake = _active_client(tmp_path, monkeypatch, disposable_age)

    score = _score(client)
    decision_id = score["decision_id"]
    assert decision_id in {row["decision_id"] for row in fake.get_all_decisions("trading")}
    assert fake.get_decision(decision_id, domain="trading")["decision_id"] == decision_id

    learn = _learn(client, decision_id, score["action"])
    assert learn["decision_id"] == decision_id
    assert fake.get_decision(decision_id, domain="trading")["status"] == "confirmed"
    assert len([row for row in fake.get_verified_decisions("trading") if row["decision_id"] == decision_id]) == 1

    duplicate = client.post(
        "/api/learn",
        json={"decision_id": decision_id, "actual_action": score["action"]},
    )
    assert duplicate.status_code == 400


@pytest.mark.age
def test_social_score_as_and_webhook_auto_score_write_active_age_decisions(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    disposable_age,
):
    client, fake = _active_client(tmp_path, monkeypatch, disposable_age)

    social = client.post(
        "/api/trading/score-as",
        json={"category": "trend_following", "factors": TRADING_FACTORS, "trader_id": "alice"},
    )
    assert social.status_code == 200
    social_payload = social.json()
    assert social_payload["decision_id"] in {row["decision_id"] for row in fake.get_all_decisions("trading")}
    assert fake.get_decision(social_payload["decision_id"], domain="trading")["metadata"]["trader_id"] == "alice"

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
    assert webhook_payload["decision_id"] in {row["decision_id"] for row in fake.get_all_decisions("trading")}
    assert fake.get_decision(webhook_payload["decision_id"], domain="trading")["metadata"]["source"] == "tradingview_webhook"


@pytest.mark.age
def test_prescore_and_read_like_routes_do_not_create_decisions_under_active_age(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    disposable_age,
):
    client, fake = _active_client(tmp_path, monkeypatch, disposable_age)

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


@pytest.mark.age
def test_retired_sqlite_rollback_is_rejected_without_reconciliation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    disposable_age,
):
    active_client, fake = _active_client(tmp_path, monkeypatch, disposable_age)
    active_score = _score(active_client)
    assert active_score["decision_id"] in {row["decision_id"] for row in fake.get_all_decisions("trading")}

    _clear_active_env(monkeypatch)
    _configure_explicit_sqlite(tmp_path, monkeypatch)
    sqlite_db = tmp_path / "rollback.sqlite"
    with pytest.raises(ValueError, match="invalid backend|must be.*memory"):
        create_app(db_path=sqlite_db, demo_bundle_path=False)
    assert not sqlite_db.exists()
    assert active_score["decision_id"] in {row["decision_id"] for row in fake.get_all_decisions("trading")}


def test_active_store_constructs_with_factory_after_guards():
    config = _active_config()
    calls: list[dict[str, Any]] = []

    def factory(**kwargs):
        calls.append(kwargs)
        return InMemoryGraphStore(domain="trading")

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
            "profile": "test",
        }
    ]


def test_direct_store_construction_rejects_shadow_conflict(monkeypatch: pytest.MonkeyPatch):
    config = _active_config()
    monkeypatch.setenv("TRADING_SHADOW_AGE", "1")
    called = False

    def factory(**kwargs):
        nonlocal called
        called = True
        return InMemoryGraphStore(domain="trading")

    with pytest.raises(TradingActiveGraphConfigError, match="conflicts"):
        create_trading_active_graph_store(config, store_factory=factory)
    assert called is False


def _active_client(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    disposable_age,
) -> tuple[TestClient, Any]:
    _set_active_age_env(monkeypatch, dsn=disposable_age.dsn)
    monkeypatch.setenv("TRADING_ACTIVE_AGE_GRAPH", disposable_age.graph)
    fake = disposable_age.store("trading")
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
    return cast(dict[str, Any], response.json())


def _learn(client: TestClient, decision_id: str, actual_action: str) -> dict[str, Any]:
    response = client.post(
        "/api/learn",
        json={"decision_id": decision_id, "actual_action": actual_action},
    )
    assert response.status_code == 200
    return cast(dict[str, Any], response.json())


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


def _configure_explicit_sqlite(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Supply a retired backend to verify fail-closed rejection."""
    config_path = tmp_path / "graph_config.toml"
    config_path.write_text(
        """[defaults]
backend = \"sqlite\"
expected_backend = \"sqlite\"
dsn = \"\"
graph = \"soc_graph\"

[copilot.trading]
domain = \"trading\"
backend = \"sqlite\"
expected_backend = \"sqlite\"
prefix = \"TRD-\"
graph = \"soc_graph\"
""",
        encoding="utf-8",
    )
    monkeypatch.setenv("GRAPH_CONFIG_PATH", str(config_path))
    monkeypatch.setenv("TRADING_ACTIVE_GRAPH_BACKEND", "sqlite")


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


def _configure_explicit_memory(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Select the disposable memory backend for these status tests."""
    config_path = tmp_path / "graph_config.toml"
    config_path.write_text(
        """[defaults]
backend = \"memory\"
expected_backend = \"memory\"
dsn = \"\"
graph = \"soc_graph\"

[copilot.trading]
domain = \"trading\"
backend = \"memory\"
expected_backend = \"memory\"
prefix = \"TRD-\"
graph = \"soc_graph\"
""",
        encoding="utf-8",
    )
    monkeypatch.setenv("GRAPH_CONFIG_PATH", str(config_path))
    monkeypatch.setenv("TRADING_ACTIVE_GRAPH_BACKEND", "memory")


@pytest.mark.parametrize("backend", ["sqlite", "unsupported_backend"])
def test_retired_backend_is_rejected_before_factory(backend: str) -> None:
    with pytest.raises(ValueError, match="must be.*memory"):
        TradingActiveGraphConfig.from_env({"TRADING_ACTIVE_GRAPH_BACKEND": backend})
    config = TradingActiveGraphConfig(requested_backend=backend)
    with pytest.raises(ValueError, match="must be.*memory"):
        create_trading_active_graph_store(
            config, store_factory=lambda **_: pytest.fail("retired backend reached factory"),
        )


def test_memory_is_rejected_for_production(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TRADING_PROFILE", "production")
    with pytest.raises(ValueError, match="production requires AGE"):
        create_trading_active_graph_store(
            TradingActiveGraphConfig(requested_backend="memory"),
            store_factory=lambda **_: pytest.fail("production memory reached factory"),
        )


def test_requested_age_without_store_reports_unknown() -> None:
    from types import SimpleNamespace
    from app.graph_status import build_trading_graph_status

    payload = build_trading_graph_status(SimpleNamespace(
        trading_active_graph_config=TradingActiveGraphConfig(
            requested_backend="age", graph="soc_graph",
        ),
        trading_selected_graph_store=None,
    ))
    assert payload["active_backend"] == "unknown"
    assert payload["age_active"] is False
    assert payload["memory_authoritative"] is False
    assert payload["cutover_ready"] is False
    assert payload["last_error"] is not None

