"""WP-4 unified evolution telemetry contract tests."""

from typing import Any, cast

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from copilot_sdk.backend.evolution_router import build_evolution_summary
from copilot_sdk.backend.self_computation_router import create_self_computation_router
from copilot_sdk.evolution import PromptVariantEvolver, VariantSpec
from copilot_sdk.graph.memory_store import InMemoryGraphStore
from tests.evolution_contract_helpers import make_contract_app


COPILOTS = ["soc", "s2p", "trading", "purchasing", "dataops"]
REQUIRED_KEYS = {"domain", "evolution_enabled", "schema_version"}
ENABLED_KEYS = {"conservation_state", "inventory", "variant_stats"}
VALID_EVENT_TYPES = {"generated", "shadow", "promoted", "rejected"}


@pytest.fixture(autouse=True)
def _block_age_connections(monkeypatch: pytest.MonkeyPatch) -> None:
    """Trap psycopg connections so these contract tests cannot contact AGE."""
    try:
        import psycopg
    except ImportError:
        return

    def _blocked(*args: object, **kwargs: object) -> None:
        raise AssertionError("Contract test attempted AGE connection via psycopg.connect")

    monkeypatch.setattr(psycopg, "connect", _blocked)


def test_sdk_normalizer_schema() -> None:
    evolver = PromptVariantEvolver()
    evolver.register_variants(
        [
            VariantSpec(
                id="baseline-v1",
                family="baseline",
                version=1,
                template="baseline",
                status="active",
            ),
            VariantSpec(
                id="candidate-v2",
                family="baseline",
                version=2,
                template="candidate",
                status="shadow",
            ),
        ]
    )

    summary = build_evolution_summary(evolver, "test")

    assert summary["schema_version"] == 1
    assert summary["domain"] == "test"
    assert summary["active_variant"] == {
        "id": "baseline-v1",
        "family": "baseline",
        "version": 1,
    }
    assert len(summary["inventory"]["active"]) == 1
    assert len(summary["inventory"]["shadow"]) == 1


def test_self_summary_endpoint_shape() -> None:
    evolver = PromptVariantEvolver()
    evolver.register_variants(
        [
            VariantSpec(
                id="endpoint-v1",
                family="endpoint",
                version=1,
                template="endpoint",
                status="active",
            )
        ]
    )
    app = FastAPI()
    app.include_router(
        create_self_computation_router(
            InMemoryGraphStore(domain="endpoint"),
            domain="endpoint",
            evolver_provider=lambda: evolver,
        )
    )

    response = TestClient(app).get("/api/self/evolution/summary")
    payload = response.json()

    assert response.status_code == 200
    assert payload["schema_version"] == 1
    assert payload["domain"] == "endpoint"
    assert payload["active_variant"]["id"] == "endpoint-v1"
    assert set(payload) == {
        "domain",
        "evolution_enabled",
        "conservation_state",
        "provider_source",
        "active_variant",
        "inventory",
        "variant_stats",
        "recent_events",
        "schema_version",
    }


def _contract_payload(domain: str) -> dict[str, Any]:
    app = make_contract_app(domain)
    with TestClient(app) as client:
        response = client.get("/api/self/evolution/summary")
        assert response.status_code == 200
        return cast(dict[str, Any], response.json())


def test_contract_schema_version() -> None:
    for domain in COPILOTS:
        assert _contract_payload(domain)["schema_version"] == 1


def test_contract_has_required_keys() -> None:
    for domain in COPILOTS:
        payload = _contract_payload(domain)
        assert REQUIRED_KEYS <= set(payload)
        if payload["evolution_enabled"]:
            assert ENABLED_KEYS <= set(payload)


def test_contract_event_types_valid() -> None:
    for domain in COPILOTS:
        events = _contract_payload(domain).get("recent_events", [])
        assert all(event.get("event_type") in VALID_EVENT_TYPES for event in events)


def test_contract_domain_matches() -> None:
    for domain in COPILOTS:
        assert _contract_payload(domain)["domain"] == domain


def test_contract_cross_copilot_parity() -> None:
    payloads = [_contract_payload(domain) for domain in COPILOTS]
    assert {frozenset(payload) for payload in payloads} == {
        frozenset(payloads[0])
    }
