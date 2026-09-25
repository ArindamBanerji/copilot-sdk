from __future__ import annotations

import uuid
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.graph_status import (
    DataOpsActiveAGEGraphStore,
    DataOpsActiveGraphConfig,
    DataOpsActiveGraphConfigError,
    create_dataops_active_graph_store,
)
from app.main import create_app
from app.graph_queries import DataOpsGraphClient
from copilot_sdk.scoring.presets.dataops import DataOpsPreset
from copilot_sdk.graph.memory_store import InMemoryGraphStore


DATAOPS_FACTORS = {
    "impact_scope": 0.82,
    "source_reliability": 0.78,
    "recurrence_frequency": 0.65,
    "downstream_urgency": 0.74,
    "data_freshness": 0.42,
    "business_criticality": 0.88,
}


def test_graph_status_default_sqlite(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    _clear_active_env(monkeypatch)
    _configure_explicit_sqlite(tmp_path, monkeypatch)
    client = TestClient(create_app(db_path=tmp_path / "dataops.db", demo_bundle_path=False))

    response = client.get("/api/dataops/graph/status")

    assert response.status_code == 200
    payload = response.json()
    assert payload["active_backend"] == "sqlite"
    assert payload["requested_backend"] == "sqlite"
    assert payload["sqlite_authoritative"] is True
    assert payload["age_active"] is False
    assert payload["active_domain"] == "dataops"
    assert payload["active_graph_name"] is None
    assert payload["operational_graph_client_status"] == "separate_dataops_graph_client"


def test_graph_status_ignores_generic_graph_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    _clear_active_env(monkeypatch)
    _configure_explicit_sqlite(tmp_path, monkeypatch)
    monkeypatch.setenv("GRAPH_BACKEND", "age")
    monkeypatch.setenv("GRAPH_DSN", "postgresql://postgres:secret@example/db")
    monkeypatch.setenv("GRAPH_NAME", "protocol_v2_test")

    client = TestClient(create_app(db_path=tmp_path / "dataops.db", demo_bundle_path=False))
    payload = client.get("/api/dataops/graph/status").json()

    assert payload["active_backend"] == "sqlite"
    assert payload["ignored_generic_graph_env"] is True
    assert "secret" not in str(payload)


@pytest.mark.parametrize(
    ("env", "message"),
    [
        ({"DATAOPS_ACTIVE_GRAPH_BACKEND": "neo4j"}, "sqlite' or 'age"),
        (
            {
                "DATAOPS_ACTIVE_GRAPH_BACKEND": "age",
                "DATAOPS_ACTIVE_AGE_GRAPH": "protocol_v2_test",
                "DATAOPS_ACTIVE_AGE_DOMAIN": "dataops",
                "DATAOPS_ACTIVE_AGE_TEST_MODE": "1",
            },
            "DSN",
        ),
        (
            {
                "DATAOPS_ACTIVE_GRAPH_BACKEND": "age",
                "DATAOPS_ACTIVE_AGE_DSN": "postgresql://example/test",
                "DATAOPS_ACTIVE_AGE_DOMAIN": "dataops",
                "DATAOPS_ACTIVE_AGE_TEST_MODE": "1",
            },
            "GRAPH",
        ),
        (
            {
                "DATAOPS_ACTIVE_GRAPH_BACKEND": "age",
                "DATAOPS_ACTIVE_AGE_DSN": "postgresql://example/test",
                "DATAOPS_ACTIVE_AGE_GRAPH": " ",
                "DATAOPS_ACTIVE_AGE_DOMAIN": "dataops",
                "DATAOPS_ACTIVE_AGE_TEST_MODE": "1",
            },
            "GRAPH",
        ),
        (
            {
                "DATAOPS_ACTIVE_GRAPH_BACKEND": "age",
                "DATAOPS_ACTIVE_AGE_DSN": " ",
                "DATAOPS_ACTIVE_AGE_GRAPH": "protocol_v2_test",
                "DATAOPS_ACTIVE_AGE_DOMAIN": "dataops",
                "DATAOPS_ACTIVE_AGE_TEST_MODE": "1",
            },
            "DSN",
        ),
        (
            {
                "DATAOPS_ACTIVE_GRAPH_BACKEND": "age",
                "DATAOPS_ACTIVE_AGE_DSN": "postgresql://example/test",
                "DATAOPS_ACTIVE_AGE_GRAPH": "protocol_v2_test",
                "DATAOPS_ACTIVE_AGE_DOMAIN": "dataops",
            },
            "TEST_MODE",
        ),
        (
            {
                "DATAOPS_ACTIVE_GRAPH_BACKEND": "age",
                "DATAOPS_ACTIVE_AGE_DSN": "postgresql://example/test",
                "DATAOPS_ACTIVE_AGE_GRAPH": "protocol_v2_test",
                "DATAOPS_ACTIVE_AGE_DOMAIN": "trading",
                "DATAOPS_ACTIVE_AGE_TEST_MODE": "1",
            },
            "dataops",
        ),
        (
            {
                "DATAOPS_ACTIVE_GRAPH_BACKEND": "age",
                "DATAOPS_ACTIVE_AGE_DSN": "postgresql://example/test",
                "DATAOPS_ACTIVE_AGE_GRAPH": "protocol_v2_test",
                "DATAOPS_ACTIVE_AGE_DOMAIN": " ",
                "DATAOPS_ACTIVE_AGE_TEST_MODE": "1",
            },
            "blank",
        ),
        (
            {
                "DATAOPS_ACTIVE_GRAPH_BACKEND": "age",
                "DATAOPS_ACTIVE_AGE_DSN": "postgresql://example/test",
                "DATAOPS_ACTIVE_AGE_GRAPH": "unreviewed_product_graph",
                "DATAOPS_ACTIVE_AGE_DOMAIN": "dataops",
            },
            "allow-listed",
        ),
        (
            {
                "DATAOPS_ACTIVE_GRAPH_BACKEND": "age",
                "DATAOPS_ACTIVE_AGE_DSN": "postgresql://example/test",
                "DATAOPS_ACTIVE_AGE_GRAPH": "governed_copilot_graph",
                "DATAOPS_ACTIVE_AGE_DOMAIN": "dataops",
            },
            "allow-listed",
        ),
    ],
)
def test_active_age_config_guards(env: dict[str, str], message: str):
    with pytest.raises(DataOpsActiveGraphConfigError, match=message):
        DataOpsActiveGraphConfig.from_env(env)


def test_product_like_config_can_be_live_test_opted_in_for_construction():
    config = DataOpsActiveGraphConfig.from_env(
        {
            "DATAOPS_ACTIVE_GRAPH_BACKEND": "age",
            "DATAOPS_ACTIVE_AGE_DSN": "postgresql://example/product",
            "DATAOPS_ACTIVE_AGE_GRAPH": "soc_graph",
            "DATAOPS_ACTIVE_AGE_DOMAIN": "dataops",
            "DATAOPS_ACTIVE_LIVE_AGE_TEST": "1",
        }
    )

    assert config.graph_kind() == "product"
    active = create_dataops_active_graph_store(config, store_factory=lambda **_: InMemoryGraphStore(domain="dataops"))
    assert isinstance(active, DataOpsActiveAGEGraphStore)


def test_active_age_status_redacts_dsn_and_reports_test_mode(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    _set_active_age_env(monkeypatch, dsn="postgresql://postgres:secret@example/db?password=other")
    client = TestClient(
        create_app(
            db_path=tmp_path / "dataops.db",
            demo_bundle_path=False,
            active_store_factory=lambda **_: InMemoryGraphStore(domain="dataops"),
        )
    )

    payload = client.get("/api/dataops/graph/status").json()

    assert payload["active_backend"] == "age"
    assert payload["age_active"] is True
    assert payload["graph_kind"] == "test"
    assert payload["active_domain"] == "dataops"
    assert payload["active_test_mode"] is True
    assert payload["migration_backfill_status"] == "not_in_scope"
    assert payload["receipt_mapping_status"] == "excluded_first_cutover"
    assert "secret" not in str(payload)
    assert "password=other" not in str(payload)


def test_dataops_preset_shape_is_canonical():
    preset = DataOpsPreset()
    assert len(preset.shape.category_names) == 6
    assert preset.shape.n_categories == 6
    assert preset.shape.n_actions == 5
    assert preset.shape.n_factors == 6


@pytest.mark.age
def test_active_age_score_learn_and_duplicate_invariant(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    disposable_age,
):
    client, fake = _active_client(tmp_path, monkeypatch, disposable_age)

    score = _score(client)
    decision_id = score["decision_id"]
    assert decision_id in {row["decision_id"] for row in fake.get_all_decisions("dataops")}
    assert fake.get_decision(decision_id, domain="dataops")["decision_id"] == decision_id
    assert fake.get_decision(decision_id, domain="dataops")["domain"] == "dataops"
    assert fake.get_decision(decision_id, domain="dataops")["metadata"]["source"] == "dataops_active_age_score"

    learn = _learn(client, decision_id, score["action"])
    assert learn["decision_id"] == decision_id
    assert fake.get_decision(decision_id, domain="dataops")["status"] == "confirmed"
    assert len([row for row in fake.get_verified_decisions("dataops") if row["decision_id"] == decision_id]) == 1

    duplicate = client.post(
        "/api/learn",
        json={"decision_id": decision_id, "actual_action": score["action"]},
    )
    assert duplicate.status_code == 400


@pytest.mark.age
def test_read_and_operational_routes_do_not_create_scorer_decisions_under_active_age(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    disposable_age,
):
    async def _empty_graph_query(self: DataOpsGraphClient, query: str) -> list[dict[str, Any]]:
        # Network is intentionally unavailable in this store-selection test;
        # keep the operational topology reads deterministic without AGE I/O.
        return []

    monkeypatch.setattr(DataOpsGraphClient, "_run_graph", _empty_graph_query)
    client, fake = _active_client(tmp_path, monkeypatch, disposable_age)

    before = fake.count_decisions("dataops")
    for path in (
        "/health",
        "/api/dataops/graph/status",
        "/api/context/pipelines",
        "/api/context/alerts",
        "/api/dataops/health",
    ):
        response = client.get(path)
        assert response.status_code == (503 if path == "/health" else 200)
    assert fake.count_decisions("dataops") == before


@pytest.mark.age
def test_rollback_to_sqlite_proves_no_hidden_reconciliation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    disposable_age,
):
    active_client, fake = _active_client(tmp_path, monkeypatch, disposable_age)
    active_score = _score(active_client)
    assert active_score["decision_id"] in {row["decision_id"] for row in fake.get_all_decisions("dataops")}

    _clear_active_env(monkeypatch)
    _configure_explicit_sqlite(tmp_path, monkeypatch)
    sqlite_db = tmp_path / "rollback.sqlite"
    sqlite_client = TestClient(create_app(db_path=sqlite_db, demo_bundle_path=False))
    sqlite_score = _score(sqlite_client)
    _learn(sqlite_client, sqlite_score["decision_id"], sqlite_score["action"])

    status = sqlite_client.get("/api/dataops/graph/status").json()
    assert status["active_backend"] == "sqlite"
    assert status["age_active"] is False
    assert active_score["decision_id"] in {row["decision_id"] for row in fake.get_all_decisions("dataops")}
    assert _sqlite_decision_count(sqlite_db) == 1


def test_active_store_constructs_with_factory_after_guards():
    config = _active_config()
    calls: list[dict[str, Any]] = []

    def factory(**kwargs):
        calls.append(kwargs)
        return InMemoryGraphStore(domain="dataops")

    active = create_dataops_active_graph_store(config, store_factory=factory)

    assert isinstance(active, DataOpsActiveAGEGraphStore)
    assert calls == [
        {
            "backend": "age",
            "domain": "dataops",
            "dsn": "postgresql://example/test",
            "graph_name": "protocol_v2_test",
            "env": {},
            "test_mode": True,
            "profile": "test",
        }
    ]


def test_operational_graph_client_uses_injected_graphconfig_without_env_mutation():
    source = (Path(__file__).resolve().parents[1] / "app" / "graph_queries.py").read_text(
        encoding="utf-8"
    )
    assert 'GraphConfig.load("dataops", profile=profile)' in source
    assert "self.graph_config = active_config" in source
    assert "os.environ" not in source


def test_dataops_active_source_uses_only_dataops_active_prefix():
    source = (Path(__file__).resolve().parents[1] / "app" / "graph_status.py").read_text(
        encoding="utf-8"
    )
    assert "DATAOPS_ACTIVE" in source
    assert "TRADING_ACTIVE" not in source
    assert "PURCHASING_ACTIVE" not in source


def test_main_uses_graph_factory_for_dataops_wiring():
    source = (Path(__file__).resolve().parents[1] / "app" / "main.py").read_text(
        encoding="utf-8"
    )
    assert "from copilot_sdk.graph.factory import create_graph_store" in source


def _active_client(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    disposable_age,
) -> tuple[TestClient, Any]:
    _set_active_age_env(monkeypatch, dsn=disposable_age.dsn)
    monkeypatch.setenv("DATAOPS_ACTIVE_AGE_GRAPH", disposable_age.graph)
    fake = disposable_age.store("dataops")
    client = TestClient(
        create_app(
            db_path=tmp_path / "dataops.db",
            demo_bundle_path=False,
            active_store_factory=lambda **_: fake,
        )
    )
    return client, fake


def _score(client: TestClient) -> dict[str, Any]:
    response = client.post(
        "/api/score",
        json={"category": "quality_anomaly", "factors": DATAOPS_FACTORS},
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


def _active_config() -> DataOpsActiveGraphConfig:
    return DataOpsActiveGraphConfig.from_env(
        {
            "DATAOPS_ACTIVE_GRAPH_BACKEND": "age",
            "DATAOPS_ACTIVE_AGE_DSN": "postgresql://example/test",
            "DATAOPS_ACTIVE_AGE_GRAPH": "protocol_v2_test",
            "DATAOPS_ACTIVE_AGE_DOMAIN": "dataops",
            "DATAOPS_ACTIVE_AGE_TEST_MODE": "1",
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

[copilot.dataops]
domain = \"dataops\"
backend = \"sqlite\"
expected_backend = \"sqlite\"
prefix = \"DOPS-\"
graph = \"soc_graph\"
""",
        encoding="utf-8",
    )
    monkeypatch.setenv("GRAPH_CONFIG_PATH", str(config_path))
    monkeypatch.setenv("DATAOPS_ACTIVE_GRAPH_BACKEND", "sqlite")


def _set_active_age_env(monkeypatch: pytest.MonkeyPatch, *, dsn: str = "postgresql://example/test") -> None:
    _clear_active_env(monkeypatch)
    monkeypatch.setenv("DATAOPS_ACTIVE_GRAPH_BACKEND", "age")
    monkeypatch.setenv("DATAOPS_ACTIVE_AGE_DSN", dsn)
    monkeypatch.setenv("DATAOPS_ACTIVE_AGE_GRAPH", "protocol_v2_test")
    monkeypatch.setenv("DATAOPS_ACTIVE_AGE_DOMAIN", "dataops")
    monkeypatch.setenv("DATAOPS_ACTIVE_AGE_TEST_MODE", "1")


def _clear_active_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for key in (
        "DATAOPS_ACTIVE_GRAPH_BACKEND",
        "DATAOPS_ACTIVE_AGE_DSN",
        "DATAOPS_ACTIVE_AGE_GRAPH",
        "DATAOPS_ACTIVE_AGE_DOMAIN",
        "DATAOPS_ACTIVE_AGE_TEST_MODE",
        "DATAOPS_ACTIVE_LIVE_AGE_TEST",
        "GRAPH_BACKEND",
        "GRAPH_DSN",
        "GRAPH_NAME",
        "GRAPH_DOMAIN",
        "AGE_DSN",
        "AGE_GRAPH_NAME",
        "GRAPH_CONFIG_PATH",
        "DATAOPS_SHARED_GRAPH_AUTHORIZED",
    ):
        monkeypatch.delenv(key, raising=False)


def _sqlite_decision_count(db_path: Path) -> int:
    from copilot_sdk.graph import InMemoryGraphStore, SQLiteGraphStore

    store = SQLiteGraphStore(db_path, domain="dataops")
    try:
        return store.count_decisions("dataops")
    finally:
        store.close()




def test_shared_graph_authorization_is_derived_from_domain_and_graph() -> None:
    base = {
        "DATAOPS_ACTIVE_GRAPH_BACKEND": "age",
        "DATAOPS_ACTIVE_AGE_DSN": "postgresql://example/shared",
        "DATAOPS_ACTIVE_AGE_GRAPH": "soc_graph",
        "DATAOPS_ACTIVE_AGE_DOMAIN": "dataops",
    }
    config = DataOpsActiveGraphConfig.from_env(base)
    assert config.shared_graph_authorization == "dataops:soc_graph"
    active = create_dataops_active_graph_store(config, store_factory=lambda **_: InMemoryGraphStore(domain="dataops"))
    assert isinstance(active, DataOpsActiveAGEGraphStore)
    assert active.generate_decision_id("dataops").startswith("DOPS-")
