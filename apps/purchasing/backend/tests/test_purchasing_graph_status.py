from __future__ import annotations

import uuid
from pathlib import Path
from typing import Any, cast

import pytest
from copilot_sdk.graph import InMemoryGraphStore
from fastapi.testclient import TestClient

from app.graph_status import (
    PurchasingActiveAGEGraphStore,
    PurchasingActiveGraphConfig,
    PurchasingActiveGraphConfigError,
    create_purchasing_active_graph_store,
)
from app.main import create_app


PURCHASING_FACTORS = {
    "expected_demand": 0.72,
    "day_of_week": 0.2,
    "weather_forecast": 0.35,
    "event_flag": 0.1,
    "historical_waste": 0.18,
    "supplier_lead_time": 0.45,
    "price_memory_index": 0.50,
}


def test_graph_status_default_memory(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    _clear_active_env(monkeypatch)
    _configure_explicit_memory(tmp_path, monkeypatch)
    client = TestClient(create_app(db_path=tmp_path / "purchasing.db", demo_bundle_path=False))

    response = client.get("/api/purchasing/graph/status")

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

    client = TestClient(create_app(db_path=tmp_path / "purchasing.db", demo_bundle_path=False))
    payload = client.get("/api/purchasing/graph/status").json()

    assert payload["active_backend"] == "memory"
    assert payload["ignored_generic_graph_env"] is True
    assert "secret" not in str(payload)


@pytest.mark.parametrize(
    ("env", "message"),
    [
        ({"PURCHASING_ACTIVE_GRAPH_BACKEND": "neo4j"}, "memory' or 'age"),
        (
            {
                "PURCHASING_ACTIVE_GRAPH_BACKEND": "age",
                "PURCHASING_ACTIVE_AGE_GRAPH": "protocol_v2_test",
                "PURCHASING_ACTIVE_AGE_DOMAIN": "purchasing",
                "PURCHASING_ACTIVE_AGE_TEST_MODE": "1",
            },
            "DSN",
        ),
        (
            {
                "PURCHASING_ACTIVE_GRAPH_BACKEND": "age",
                "PURCHASING_ACTIVE_AGE_DSN": "postgresql://example/test",
                "PURCHASING_ACTIVE_AGE_DOMAIN": "purchasing",
                "PURCHASING_ACTIVE_AGE_TEST_MODE": "1",
            },
            "GRAPH",
        ),
        (
            {
                "PURCHASING_ACTIVE_GRAPH_BACKEND": "age",
                "PURCHASING_ACTIVE_AGE_DSN": "postgresql://example/test",
                "PURCHASING_ACTIVE_AGE_GRAPH": " ",
                "PURCHASING_ACTIVE_AGE_DOMAIN": "purchasing",
                "PURCHASING_ACTIVE_AGE_TEST_MODE": "1",
            },
            "GRAPH",
        ),
        (
            {
                "PURCHASING_ACTIVE_GRAPH_BACKEND": "age",
                "PURCHASING_ACTIVE_AGE_DSN": " ",
                "PURCHASING_ACTIVE_AGE_GRAPH": "protocol_v2_test",
                "PURCHASING_ACTIVE_AGE_DOMAIN": "purchasing",
                "PURCHASING_ACTIVE_AGE_TEST_MODE": "1",
            },
            "DSN",
        ),
        (
        {
            "PURCHASING_ACTIVE_GRAPH_BACKEND": "age",
            "PURCHASING_ACTIVE_AGE_DSN": "postgresql://example/test",
            "PURCHASING_ACTIVE_AGE_GRAPH": "protocol_v2_test",
            "PURCHASING_ACTIVE_AGE_DOMAIN": "purchasing",
        },
        "TEST_MODE",
    ),
        (
            {
                "PURCHASING_ACTIVE_GRAPH_BACKEND": "age",
                "PURCHASING_ACTIVE_AGE_DSN": "postgresql://example/test",
                "PURCHASING_ACTIVE_AGE_GRAPH": "protocol_v2_test",
                "PURCHASING_ACTIVE_AGE_DOMAIN": "trading",
                "PURCHASING_ACTIVE_AGE_TEST_MODE": "1",
            },
            "purchasing",
        ),
        (
            {
                "PURCHASING_ACTIVE_GRAPH_BACKEND": "age",
                "PURCHASING_ACTIVE_AGE_DSN": "postgresql://example/test",
                "PURCHASING_ACTIVE_AGE_GRAPH": "protocol_v2_test",
                "PURCHASING_ACTIVE_AGE_DOMAIN": " ",
                "PURCHASING_ACTIVE_AGE_TEST_MODE": "1",
            },
            "blank",
        ),
        (
            {
                "PURCHASING_ACTIVE_GRAPH_BACKEND": "age",
                "PURCHASING_ACTIVE_AGE_DSN": "postgresql://example/test",
                "PURCHASING_ACTIVE_AGE_GRAPH": "unreviewed_product_graph",
                "PURCHASING_ACTIVE_AGE_DOMAIN": "purchasing",
                "PURCHASING_ACTIVE_AGE_TEST_MODE": "0",
            },
            "allow-listed",
        ),
        (
            {
                "PURCHASING_ACTIVE_GRAPH_BACKEND": "age",
                "PURCHASING_ACTIVE_AGE_DSN": "postgresql://example/test",
                "PURCHASING_ACTIVE_AGE_GRAPH": "protocol_v2_test",
                "PURCHASING_ACTIVE_AGE_DOMAIN": "purchasing",
                "PURCHASING_ACTIVE_AGE_TEST_MODE": "1",
                "PURCHASING_SHADOW_AGE": "1",
            },
            "conflicts",
        ),
    ],
)
def test_active_age_config_guards(env: dict[str, str], message: str):
    with pytest.raises(PurchasingActiveGraphConfigError, match=message):
        PurchasingActiveGraphConfig.from_env(env)


def test_product_like_config_validates_but_store_construction_is_blocked():
    with pytest.raises(PurchasingActiveGraphConfigError, match="allow-listed"):
        PurchasingActiveGraphConfig.from_env(
            {
                "PURCHASING_ACTIVE_GRAPH_BACKEND": "age",
                "PURCHASING_ACTIVE_AGE_DSN": "postgresql://example/product",
                "PURCHASING_ACTIVE_AGE_GRAPH": "governed_copilot_graph",
                "PURCHASING_ACTIVE_AGE_DOMAIN": "purchasing",
                "PURCHASING_ACTIVE_AGE_TEST_MODE": "0",
            }
        )


def test_requested_age_status_detects_memory_and_redacts_dsn(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    _set_active_age_env(monkeypatch, dsn="postgresql://postgres:secret@example/db?password=other")
    client = TestClient(
        create_app(
            db_path=tmp_path / "purchasing.db",
            demo_bundle_path=False,
            active_store_factory=lambda **_: InMemoryGraphStore(domain="purchasing"),
        )
    )

    payload = client.get("/api/purchasing/graph/status").json()

    assert payload["active_backend"] == "memory"
    assert payload["age_active"] is False
    assert payload["last_error"] is not None
    assert payload["cutover_ready"] is False
    assert payload["graph_kind"] == "test"
    assert payload["active_domain"] == "purchasing"
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
    _set_active_age_env(monkeypatch, dsn=disposable_age.dsn)
    monkeypatch.setenv("PURCHASING_ACTIVE_AGE_GRAPH", disposable_age.graph)
    fake = disposable_age.store("purchasing")
    client = TestClient(
        create_app(
            db_path=tmp_path / "purchasing.db",
            demo_bundle_path=False,
            active_store_factory=lambda **_: fake,
        )
    )

    score = _score(client)
    decision_id = score["decision_id"]
    assert decision_id in {row["decision_id"] for row in fake.get_all_decisions("purchasing")}
    assert fake.get_decision(decision_id, domain="purchasing")["decision_id"] == decision_id

    learn = _learn(client, decision_id, score["action"])
    assert learn["decision_id"] == decision_id
    assert fake.get_decision(decision_id, domain="purchasing")["status"] == "confirmed"
    assert len([row for row in fake.get_verified_decisions("purchasing") if row["decision_id"] == decision_id]) == 1

    duplicate = client.post(
        "/api/learn",
        json={"decision_id": decision_id, "actual_action": score["action"]},
    )
    assert duplicate.status_code == 400


@pytest.mark.age
def test_read_routes_do_not_create_decisions_under_active_age(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    disposable_age,
):
    _set_active_age_env(monkeypatch, dsn=disposable_age.dsn)
    monkeypatch.setenv("PURCHASING_ACTIVE_AGE_GRAPH", disposable_age.graph)
    fake = disposable_age.store("purchasing")
    client = TestClient(
        create_app(
            db_path=tmp_path / "purchasing.db",
            demo_bundle_path=False,
            active_store_factory=lambda **_: fake,
        )
    )

    before = fake.count_decisions("purchasing")
    for path in (
        "/api/purchasing/evidence/summary",
        "/api/purchasing/evidence/decisions",
        "/api/purchasing/status",
        "/api/context/today-summary",
        "/api/context/items",
    ):
        response = client.get(path)
        assert response.status_code == 200
    assert fake.count_decisions("purchasing") == before


@pytest.mark.age
def test_retired_sqlite_rollback_is_rejected_without_reconciliation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    disposable_age,
):
    _set_active_age_env(monkeypatch, dsn=disposable_age.dsn)
    monkeypatch.setenv("PURCHASING_ACTIVE_AGE_GRAPH", disposable_age.graph)
    fake = disposable_age.store("purchasing")
    active_client = TestClient(
        create_app(
            db_path=tmp_path / "active.sqlite",
            demo_bundle_path=False,
            active_store_factory=lambda **_: fake,
        )
    )
    active_score = _score(active_client)
    assert active_score["decision_id"] in {row["decision_id"] for row in fake.get_all_decisions("purchasing")}

    _clear_active_env(monkeypatch)
    _configure_explicit_sqlite(tmp_path, monkeypatch)
    sqlite_db = tmp_path / "rollback.sqlite"
    with pytest.raises(ValueError, match="invalid backend|must be.*memory"):
        create_app(db_path=sqlite_db, demo_bundle_path=False)
    assert not sqlite_db.exists()
    assert active_score["decision_id"] in {row["decision_id"] for row in fake.get_all_decisions("purchasing")}


def test_active_store_constructs_with_factory_after_guards():
    config = _active_config()
    calls: list[dict[str, Any]] = []

    def factory(**kwargs):
        calls.append(kwargs)
        return InMemoryGraphStore(domain="purchasing")

    active = create_purchasing_active_graph_store(config, store_factory=factory)

    assert isinstance(active, PurchasingActiveAGEGraphStore)
    assert calls == [
        {
            "backend": "age",
            "domain": "purchasing",
            "dsn": "postgresql://example/test",
            "graph_name": "protocol_v2_test",
            "env": {},
            "test_mode": True,
            "profile": "test",
        }
    ]


def test_direct_store_construction_rejects_shadow_conflict(monkeypatch: pytest.MonkeyPatch):
    config = _active_config()
    monkeypatch.setenv("PURCHASING_SHADOW_AGE", "1")
    called = False

    def factory(**kwargs):
        nonlocal called
        called = True
        return InMemoryGraphStore(domain="purchasing")

    with pytest.raises(PurchasingActiveGraphConfigError, match="conflicts"):
        create_purchasing_active_graph_store(config, store_factory=factory)
    assert called is False


def _score(client: TestClient) -> dict[str, Any]:
    response = client.post(
        "/api/score",
        json={"category": "protein", "factors": PURCHASING_FACTORS},
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


def _active_config() -> PurchasingActiveGraphConfig:
    return PurchasingActiveGraphConfig.from_env(
        {
            "PURCHASING_ACTIVE_GRAPH_BACKEND": "age",
            "PURCHASING_ACTIVE_AGE_DSN": "postgresql://example/test",
            "PURCHASING_ACTIVE_AGE_GRAPH": "protocol_v2_test",
            "PURCHASING_ACTIVE_AGE_DOMAIN": "purchasing",
            "PURCHASING_ACTIVE_AGE_TEST_MODE": "1",
        }
    )


def _configure_explicit_sqlite(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    config_path = tmp_path / "graph_config.toml"
    config_path.write_text(
        """[defaults]
backend = \"sqlite\"
expected_backend = \"sqlite\"
dsn = \"\"
graph = \"soc_graph\"

[copilot.purchasing]
domain = \"purchasing\"
backend = \"sqlite\"
expected_backend = \"sqlite\"
prefix = \"PUR-\"
graph = \"soc_graph\"
""",
        encoding="utf-8",
    )
    monkeypatch.setenv("GRAPH_CONFIG_PATH", str(config_path))
    monkeypatch.setenv("PURCHASING_ACTIVE_GRAPH_BACKEND", "sqlite")


def _set_active_age_env(monkeypatch: pytest.MonkeyPatch, *, dsn: str = "postgresql://example/test") -> None:
    _clear_active_env(monkeypatch)
    monkeypatch.setenv("PURCHASING_ACTIVE_GRAPH_BACKEND", "age")
    monkeypatch.setenv("PURCHASING_ACTIVE_AGE_DSN", dsn)
    monkeypatch.setenv("PURCHASING_ACTIVE_AGE_GRAPH", "protocol_v2_test")
    monkeypatch.setenv("PURCHASING_ACTIVE_AGE_DOMAIN", "purchasing")
    monkeypatch.setenv("PURCHASING_ACTIVE_AGE_TEST_MODE", "1")


def _clear_active_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for key in (
        "PURCHASING_ACTIVE_GRAPH_BACKEND",
        "PURCHASING_ACTIVE_AGE_DSN",
        "PURCHASING_ACTIVE_AGE_GRAPH",
        "PURCHASING_ACTIVE_AGE_DOMAIN",
        "PURCHASING_ACTIVE_AGE_TEST_MODE",
        "PURCHASING_SHADOW_AGE",
        "GRAPH_BACKEND",
        "GRAPH_DSN",
        "GRAPH_NAME",
        "GRAPH_DOMAIN",
        "AGE_DSN",
        "AGE_GRAPH_NAME",
        "GRAPH_CONFIG_PATH",
        "PURCHASING_SHARED_GRAPH_AUTHORIZED",
    ):
        monkeypatch.delenv(key, raising=False)


def test_shared_graph_authorization_is_derived_from_domain_and_graph() -> None:
    base = {
        "PURCHASING_ACTIVE_GRAPH_BACKEND": "age",
        "PURCHASING_ACTIVE_AGE_DSN": "postgresql://example/shared",
        "PURCHASING_ACTIVE_AGE_GRAPH": "soc_graph",
        "PURCHASING_ACTIVE_AGE_DOMAIN": "purchasing",
    }
    config = PurchasingActiveGraphConfig.from_env(base)
    assert config.shared_graph_authorization == "purchasing:soc_graph"
    active = create_purchasing_active_graph_store(config, store_factory=lambda **_: InMemoryGraphStore(domain="purchasing"))
    assert isinstance(active, PurchasingActiveAGEGraphStore)
    assert active.generate_decision_id("purchasing").startswith("PUR-")


def _configure_explicit_memory(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    config_path = tmp_path / "graph_config.toml"
    config_path.write_text(
        """[defaults]
backend = \"memory\"
expected_backend = \"memory\"
dsn = \"\"
graph = \"soc_graph\"

[copilot.purchasing]
domain = \"purchasing\"
backend = \"memory\"
expected_backend = \"memory\"
prefix = \"PUR-\"
graph = \"soc_graph\"
""",
        encoding="utf-8",
    )
    monkeypatch.setenv("GRAPH_CONFIG_PATH", str(config_path))
    monkeypatch.setenv("PURCHASING_ACTIVE_GRAPH_BACKEND", "memory")


@pytest.mark.parametrize("backend", ["sqlite", "unsupported_backend"])
def test_retired_backend_is_rejected_before_factory(backend: str) -> None:
    with pytest.raises(ValueError, match="must be.*memory"):
        PurchasingActiveGraphConfig.from_env({"PURCHASING_ACTIVE_GRAPH_BACKEND": backend})
    config = PurchasingActiveGraphConfig(requested_backend=backend)
    with pytest.raises(ValueError, match="must be.*memory"):
        create_purchasing_active_graph_store(
            config, store_factory=lambda **_: pytest.fail("retired backend reached factory"),
        )


def test_memory_is_rejected_for_production(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PURCHASING_PROFILE", "production")
    with pytest.raises(ValueError, match="production requires AGE"):
        create_purchasing_active_graph_store(
            PurchasingActiveGraphConfig(requested_backend="memory"),
            store_factory=lambda **_: pytest.fail("production memory reached factory"),
        )


def test_requested_age_without_store_reports_unknown() -> None:
    from types import SimpleNamespace
    from app.graph_status import build_purchasing_graph_status

    payload = build_purchasing_graph_status(SimpleNamespace(
        purchasing_active_graph_config=PurchasingActiveGraphConfig(
            requested_backend="age", graph="soc_graph",
        ),
        purchasing_selected_graph_store=None,
    ))
    assert payload["active_backend"] == "unknown"
    assert payload["age_active"] is False
    assert payload["memory_authoritative"] is False
    assert payload["cutover_ready"] is False
    assert payload["last_error"] is not None

