"""WP-4 unified evolution telemetry contract tests."""

import json
from urllib.error import URLError
from urllib.request import urlopen
from typing import Any, cast

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from copilot_sdk.backend.evolution_router import build_evolution_summary
from copilot_sdk.backend.self_computation_router import create_self_computation_router
from copilot_sdk.evolution import PromptVariantEvolver, VariantSpec
from copilot_sdk.graph.memory_store import InMemoryGraphStore


COPILOTS = [
    (8001, "soc"),
    (8002, "s2p"),
    (8010, "trading"),
    (8020, "purchasing"),
    (8030, "dataops"),
]
REQUIRED_KEYS = {"domain", "evolution_enabled", "schema_version"}
ENABLED_KEYS = {"conservation_state", "inventory", "variant_stats"}
VALID_EVENT_TYPES = {"generated", "shadow", "promoted", "rejected"}


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
        "active_variant",
        "inventory",
        "variant_stats",
        "recent_events",
        "schema_version",
    }


def _summary(port: int) -> dict:
    try:
        with urlopen(
            f"http://127.0.0.1:{port}/api/self/evolution/summary", timeout=3
        ) as response:
            return cast(dict[str, Any], json.loads(response.read()))
    except (OSError, URLError) as exc:
        pytest.skip(f"copilot on port {port} is not running: {exc}")


def test_summary_schema_version() -> None:
    for port, _domain in COPILOTS:
        assert _summary(port)["schema_version"] == 1


def test_summary_has_required_keys() -> None:
    for port, _domain in COPILOTS:
        summary = _summary(port)
        assert REQUIRED_KEYS <= set(summary)
        if summary["evolution_enabled"]:
            assert ENABLED_KEYS <= set(summary)


def test_summary_event_types_valid() -> None:
    for port, _domain in COPILOTS:
        events = _summary(port).get("recent_events", [])
        assert all(event.get("event_type") in VALID_EVENT_TYPES for event in events)


def test_summary_domain_matches() -> None:
    for port, domain in COPILOTS:
        assert _summary(port)["domain"] == domain


def test_summary_cross_copilot_parity() -> None:
    summaries = [_summary(port) for port, _domain in COPILOTS]
    assert {frozenset(summary) for summary in summaries} == {
        frozenset(summaries[0])
    }
