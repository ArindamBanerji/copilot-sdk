"""Proof that evolution summary schemas can be exercised without AGE."""

from typing import Any

from fastapi import FastAPI
from fastapi.testclient import TestClient
import psycopg
import pytest

from copilot_sdk.backend.evolution_router import create_evolution_router
from copilot_sdk.backend.self_computation_router import create_self_computation_router
from copilot_sdk.evolution import PromptVariantEvolver, VariantSpec
from copilot_sdk.graph.protocol import GraphStore


class MinimalGraphStore(GraphStore):
    """Small GraphStore boundary double for the summary routes under test."""

    domain = "experiment"

    def __init__(self) -> None:
        self.calls: list[str] = []

    def get_verified_decisions(self, domain: str) -> list[dict[str, Any]]:
        self.calls.append(f"get_verified_decisions:{domain}")
        return []


def test_evolution_schema_contract_without_age(monkeypatch: pytest.MonkeyPatch) -> None:
    store = MinimalGraphStore()
    assert isinstance(store, GraphStore)
    connection_attempts: list[tuple[Any, ...]] = []

    def reject_connection(*args: Any, **kwargs: Any) -> None:
        connection_attempts.append(args)
        connection_attempts.append(tuple(kwargs.items()))
        raise AssertionError("database connection attempted by schema contract")

    monkeypatch.setattr(psycopg, "connect", reject_connection)
    evolver = PromptVariantEvolver()
    evolver.register_variants(
        [
            VariantSpec(
                id="baseline-v1",
                family="experiment",
                version=1,
                template="baseline",
                status="active",
            )
        ]
    )

    app = FastAPI()
    app.include_router(
        create_evolution_router(
            graph_store_factory=lambda: store,
            domain="experiment",
            evolver_factory=lambda: evolver,
        )
    )
    app.include_router(
        create_self_computation_router(
            store,
            domain="experiment",
            evolver_provider=lambda: evolver,
        )
    )

    with TestClient(app) as client:
        evolution_response = client.get("/api/evolution/summary")
        self_response = client.get("/api/self/evolution/summary")

    assert evolution_response.status_code == 200
    assert self_response.status_code == 200
    payload = self_response.json()
    assert payload["domain"] == "experiment"
    assert payload["schema_version"] == 1
    assert payload["evolution_enabled"] is True
    assert {"conservation_state", "inventory", "variant_stats"} <= set(payload)
    assert payload["active_variant"]["id"] == "baseline-v1"
    assert store.calls == []
    assert connection_attempts == []

    print({
        "evolution_summary": evolution_response.json(),
        "self_evolution_summary": payload,
    })
