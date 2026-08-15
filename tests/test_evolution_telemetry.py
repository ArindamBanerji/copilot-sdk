"""WP-4 unified evolution telemetry contract tests."""

import json
import importlib
import sys
from pathlib import Path
from typing import Any, cast

from fastapi import FastAPI
from fastapi.testclient import TestClient

from copilot_sdk.backend.evolution_router import build_evolution_summary
from copilot_sdk.backend.self_computation_router import create_self_computation_router
from copilot_sdk.evolution import PromptVariantEvolver, VariantSpec
from copilot_sdk.graph.memory_store import InMemoryGraphStore


ROOT = Path(__file__).resolve().parents[1]
COPILOTS = ["soc", "s2p", "trading", "purchasing", "dataops"]
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
        "provider_source",
        "active_variant",
        "inventory",
        "variant_stats",
        "recent_events",
        "schema_version",
    }


def _summary(domain: str) -> dict[str, Any]:
    """Read one copilot's contract through its in-process application."""
    for name in list(sys.modules):
        if name == "app" or name.startswith("app."):
            del sys.modules[name]

    if domain in {"trading", "purchasing", "dataops"}:
        backend = ROOT / "apps" / domain / "backend"
    elif domain == "s2p":
        backend = ROOT.parent / "s2p-copilot" / "backend"
    else:
        backend = ROOT.parent / "gen-ai-roi-demo-v4-v50" / "backend"

    sys.path.insert(0, str(backend))
    try:
        if domain == "soc":
            from copilot_sdk.backend.self_computation_router import create_self_computation_router
            from app.services.evolver import get_sdk_evolver

            app = FastAPI()
            app.include_router(
                create_self_computation_router(
                    InMemoryGraphStore(domain="soc"),
                    domain="soc",
                    evolver_provider=get_sdk_evolver,
                )
            )
        else:
            module = importlib.import_module("app.main")
        if domain in {"trading", "purchasing", "dataops"}:
            app = module.create_app(db_path=":memory:", demo_bundle_path=False)
        elif domain == "s2p":
            app = module.app
        with TestClient(app) as client:
            response = client.get("/api/self/evolution/summary")
            assert response.status_code == 200
            return cast(dict[str, Any], json.loads(response.text))
    finally:
        sys.path.remove(str(backend))


def test_summary_schema_version() -> None:
    for domain in COPILOTS:
        assert _summary(domain)["schema_version"] == 1


def test_summary_has_required_keys() -> None:
    for domain in COPILOTS:
        summary = _summary(domain)
        assert REQUIRED_KEYS <= set(summary)
        if summary["evolution_enabled"]:
            assert ENABLED_KEYS <= set(summary)


def test_summary_event_types_valid() -> None:
    for domain in COPILOTS:
        events = _summary(domain).get("recent_events", [])
        assert all(event.get("event_type") in VALID_EVENT_TYPES for event in events)


def test_summary_domain_matches() -> None:
    for domain in COPILOTS:
        assert _summary(domain)["domain"] == domain


def test_summary_cross_copilot_parity() -> None:
    summaries = [_summary(domain) for domain in COPILOTS]
    assert {frozenset(summary) for summary in summaries} == {
        frozenset(summaries[0])
    }
