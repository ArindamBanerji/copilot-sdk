from __future__ import annotations

import uuid
from pathlib import Path
from typing import Any

import pytest
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


def test_graph_status_default_sqlite(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    _clear_active_env(monkeypatch)
    client = TestClient(create_app(db_path=tmp_path / "purchasing.db", demo_bundle_path=False))

    response = client.get("/api/purchasing/graph/status")

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

    client = TestClient(create_app(db_path=tmp_path / "purchasing.db", demo_bundle_path=False))
    payload = client.get("/api/purchasing/graph/status").json()

    assert payload["active_backend"] == "sqlite"
    assert payload["ignored_generic_graph_env"] is True
    assert "secret" not in str(payload)


@pytest.mark.parametrize(
    ("env", "message"),
    [
        ({"PURCHASING_ACTIVE_GRAPH_BACKEND": "neo4j"}, "sqlite' or 'age"),
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
                "PURCHASING_ACTIVE_AGE_GRAPH": "soc_graph",
                "PURCHASING_ACTIVE_AGE_DOMAIN": "purchasing",
                "PURCHASING_ACTIVE_AGE_TEST_MODE": "1",
            },
            "soc_graph",
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
    config = PurchasingActiveGraphConfig.from_env(
        {
            "PURCHASING_ACTIVE_GRAPH_BACKEND": "age",
            "PURCHASING_ACTIVE_AGE_DSN": "postgresql://example/product",
            "PURCHASING_ACTIVE_AGE_GRAPH": "governed_copilot_graph",
            "PURCHASING_ACTIVE_AGE_DOMAIN": "purchasing",
            "PURCHASING_ACTIVE_AGE_TEST_MODE": "0",
        }
    )

    assert config.graph_kind() == "product"
    with pytest.raises(PurchasingActiveGraphConfigError, match="product AGE writes remain blocked"):
        create_purchasing_active_graph_store(config, store_factory=lambda **_: FakeAGEStore())


def test_active_age_status_redacts_dsn_and_reports_test_mode(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    _set_active_age_env(monkeypatch, dsn="postgresql://postgres:secret@example/db?password=other")
    client = TestClient(
        create_app(
            db_path=tmp_path / "purchasing.db",
            demo_bundle_path=False,
            active_store_factory=lambda **_: FakeAGEStore(),
        )
    )

    payload = client.get("/api/purchasing/graph/status").json()

    assert payload["active_backend"] == "age"
    assert payload["age_active"] is True
    assert payload["graph_kind"] == "test"
    assert payload["active_domain"] == "purchasing"
    assert payload["active_test_mode"] is True
    assert payload["migration_backfill_status"] == "not_in_scope"
    assert payload["receipt_mapping_status"] == "excluded_first_cutover"
    assert "secret" not in str(payload)
    assert "password=other" not in str(payload)


def test_active_age_score_learn_and_duplicate_invariant(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    _set_active_age_env(monkeypatch)
    fake = FakeAGEStore()
    client = TestClient(
        create_app(
            db_path=tmp_path / "purchasing.db",
            demo_bundle_path=False,
            active_store_factory=lambda **_: fake,
        )
    )

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


def test_read_routes_do_not_create_decisions_under_active_age(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    _set_active_age_env(monkeypatch)
    fake = FakeAGEStore()
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


def test_rollback_to_sqlite_proves_no_hidden_reconciliation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    _set_active_age_env(monkeypatch)
    fake = FakeAGEStore()
    active_client = TestClient(
        create_app(
            db_path=tmp_path / "active.sqlite",
            demo_bundle_path=False,
            active_store_factory=lambda **_: fake,
        )
    )
    active_score = _score(active_client)
    assert active_score["decision_id"] in fake.decisions

    _clear_active_env(monkeypatch)
    sqlite_db = tmp_path / "rollback.sqlite"
    sqlite_client = TestClient(create_app(db_path=sqlite_db, demo_bundle_path=False))
    sqlite_score = _score(sqlite_client)
    _learn(sqlite_client, sqlite_score["decision_id"], sqlite_score["action"])

    status = sqlite_client.get("/api/purchasing/graph/status").json()
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
        }
    ]


def test_direct_store_construction_rejects_shadow_conflict(monkeypatch: pytest.MonkeyPatch):
    config = _active_config()
    monkeypatch.setenv("PURCHASING_SHADOW_AGE", "1")
    called = False

    def factory(**kwargs):
        nonlocal called
        called = True
        return FakeAGEStore()

    with pytest.raises(PurchasingActiveGraphConfigError, match="conflicts"):
        create_purchasing_active_graph_store(config, store_factory=factory)
    assert called is False


def _score(client: TestClient) -> dict[str, Any]:
    response = client.post(
        "/api/score",
        json={"category": "protein", "factors": PURCHASING_FACTORS},
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
    ):
        monkeypatch.delenv(key, raising=False)


def _sqlite_decision_count(db_path: Path) -> int:
    from copilot_sdk.graph import SQLiteGraphStore

    store = SQLiteGraphStore(db_path, domain="purchasing")
    try:
        return store.count_decisions("purchasing")
    finally:
        store.close()


class FakeAGEStore:  # MOCK-OK: AGE protocol compliance without external AGE
    domain = "purchasing"

    def __init__(self) -> None:
        self.decisions: dict[str, dict[str, Any]] = {}
        self.outcomes: dict[str, list[dict[str, Any]]] = {}
        self.centroids: list[dict[str, Any]] = []

    def generate_decision_id(self, domain: str) -> str:
        assert domain == self.domain
        return uuid.uuid4().hex[:12]

    def write_governed_decision(
        self,
        decision_id: str,
        domain: str,
        category: str,
        category_index: int,
        recommended_action: str,
        recommended_index: int,
        confidence: float,
        probabilities: list[float],
        factor_vector: list[float],
        factor_names: list[str],
        source: str = "score",
        scorer_version: str = "",
        preset_version: str = "",
        factor_schema_version: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> None:
        assert domain == self.domain
        kwargs = {
            "decision_id": decision_id,
            "domain": domain,
            "category": category,
            "category_index": category_index,
            "recommended_action": recommended_action,
            "recommended_index": recommended_index,
            "confidence": confidence,
            "probabilities": probabilities,
            "factor_vector": factor_vector,
            "factor_names": factor_names,
            "source": source,
            "scorer_version": scorer_version,
            "preset_version": preset_version,
            "factor_schema_version": factor_schema_version,
            "metadata": metadata,
        }
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

    def save_centroids(self, domain: str, category: str, centroids: Any, metadata: dict[str, Any] | None = None, **kwargs: Any) -> None:
        self.centroids.append({"domain": domain, "category": category, "metadata": metadata or {}, **kwargs})

    def get_centroid_checkpoints(self, domain: str, **kwargs: Any) -> list[dict[str, Any]]:
        return list(self.centroids)

    def get_verified_decisions(self, domain: str) -> list[dict[str, Any]]:
        return [dict(decision) for decision in self.decisions.values() if decision.get("status") in {"confirmed", "overridden"}]

    def get_all_decisions(self, domain: str) -> list[dict[str, Any]]:
        return [dict(decision) for decision in self.decisions.values()]

    def get_decisions(self, domain: str, category: str | None = None, limit: int = 400) -> list[dict[str, Any]]:
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
