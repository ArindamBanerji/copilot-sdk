from __future__ import annotations

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
from copilot_sdk.scoring.presets.dataops import DataOpsPreset


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
                "DATAOPS_ACTIVE_AGE_GRAPH": "soc_graph",
                "DATAOPS_ACTIVE_AGE_DOMAIN": "dataops",
                "DATAOPS_ACTIVE_AGE_TEST_MODE": "1",
            },
            "soc_graph",
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
            "product AGE writes remain blocked",
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
            "DATAOPS_ACTIVE_AGE_GRAPH": "governed_copilot_graph",
            "DATAOPS_ACTIVE_AGE_DOMAIN": "dataops",
            "DATAOPS_ACTIVE_LIVE_AGE_TEST": "1",
        }
    )

    assert config.graph_kind() == "product"
    active = create_dataops_active_graph_store(config, store_factory=lambda **_: FakeAGEStore())
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
            active_store_factory=lambda **_: FakeAGEStore(),
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


def test_active_age_score_learn_and_duplicate_invariant(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    client, fake = _active_client(tmp_path, monkeypatch)

    score = _score(client)
    decision_id = score["decision_id"]
    assert decision_id in fake.decisions
    assert fake.decisions[decision_id]["decision_id"] == decision_id
    assert fake.decisions[decision_id]["domain"] == "dataops"
    assert fake.decisions[decision_id]["source"] == "dataops_active_age_score"

    learn = _learn(client, decision_id, score["action"])
    assert learn["decision_id"] == decision_id
    assert fake.decisions[decision_id]["status"] == "confirmed"
    assert len(fake.outcomes[decision_id]) == 1

    duplicate = client.post(
        "/api/learn",
        json={"decision_id": decision_id, "actual_action": score["action"]},
    )
    assert duplicate.status_code == 400


def test_read_and_operational_routes_do_not_create_scorer_decisions_under_active_age(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    client, fake = _active_client(tmp_path, monkeypatch)

    before = fake.count_decisions("dataops")
    for path in (
        "/health",
        "/api/dataops/graph/status",
        "/api/context/pipelines",
        "/api/context/alerts",
        "/api/dataops/health",
    ):
        response = client.get(path)
        assert response.status_code == 200
    assert fake.count_decisions("dataops") == before


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

    status = sqlite_client.get("/api/dataops/graph/status").json()
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
        }
    ]


def test_operational_graph_client_source_does_not_reference_dataops_active_env():
    source = Path("apps/dataops/backend/app/graph_queries.py").read_text(encoding="utf-8")
    assert "DATAOPS_ACTIVE" not in source


def test_dataops_active_source_uses_only_dataops_active_prefix():
    source = Path("apps/dataops/backend/app/graph_status.py").read_text(encoding="utf-8")
    assert "DATAOPS_ACTIVE" in source
    assert "TRADING_ACTIVE" not in source
    assert "PURCHASING_ACTIVE" not in source


def test_main_does_not_depend_on_graph_factory_for_dataops_active_wiring():
    source = Path("apps/dataops/backend/app/main.py").read_text(encoding="utf-8")
    assert "copilot_sdk.graph.factory" not in source


def _active_client(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[TestClient, "FakeAGEStore"]:
    _set_active_age_env(monkeypatch)
    fake = FakeAGEStore()
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
    ):
        monkeypatch.delenv(key, raising=False)


def _sqlite_decision_count(db_path: Path) -> int:
    from copilot_sdk.graph import SQLiteGraphStore

    store = SQLiteGraphStore(db_path, domain="dataops")
    try:
        return store.count_decisions("dataops")
    finally:
        store.close()


class FakeAGEStore:  # MOCK-OK: AGE protocol compliance without external AGE
    domain = "dataops"

    def __init__(self) -> None:
        self.decisions: dict[str, dict[str, Any]] = {}
        self.outcomes: dict[str, list[dict[str, Any]]] = {}
        self.centroids: list[dict[str, Any]] = []
        self.evolution_events: list[dict[str, Any]] = []

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

    def count_archived(self, domain: str) -> int:
        return 0

    def archive_old_decisions(self, domain: str, keep_recent: int = 800) -> int:
        return 0

    def save_evolution_event(self, **kwargs: Any) -> None:
        self.evolution_events.append(dict(kwargs))

    def get_evolution_events(self, domain: str, **kwargs: Any) -> list[dict[str, Any]]:
        return list(self.evolution_events)

    def close(self) -> None:
        return None
