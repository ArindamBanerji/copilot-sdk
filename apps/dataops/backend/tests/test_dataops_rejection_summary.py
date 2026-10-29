"""DataOps evolution rejection-summary route contracts."""

from __future__ import annotations

from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from copilot_sdk.evolution import PromptVariantEvolver
from copilot_sdk.demo.preseed import DemoPreseed
from copilot_sdk.graph import InMemoryGraphStore

from app.evolution.evolver_config import (
    DATAOPS_EVOLVER_CONFIG,
    get_dataops_variant_specs,
)
from app.routers.evolution_router import (
    _canonical_rejection_reason,
    create_dataops_evolution_router,
)


def _evolver() -> PromptVariantEvolver:
    service = PromptVariantEvolver(config=DATAOPS_EVOLVER_CONFIG)
    service.register_variants(get_dataops_variant_specs())
    return service


def _client(
    *,
    evolver: PromptVariantEvolver | None = None,
    graph: Any = None,
    include_persisted: bool = False,
) -> TestClient:
    app = FastAPI()
    app.include_router(
        create_dataops_evolution_router(
            evolver=evolver or _evolver(),
            graph_store_factory=(lambda: graph) if graph is not None else None,
            include_persisted_rejections=include_persisted,
        )
    )
    return TestClient(app)


def _persisted_payload() -> dict[str, Any]:
    reasons = [
        "conservation",
        "conservation",
        "conservation",
        "correctness_floor",
        "correctness_floor",
        "variance_stability",
    ]
    return {
        "total_tested": 6,
        "total_promoted": 0,
        "total_rejected": 6,
        "rejection_breakdown": {
            "correctness_floor": 2,
            "conservation": 3,
            "variance_stability": 1,
        },
        "rejected_variants": [
            {
                "variant_id": f"DATAOPS_REJECT_{index:02d}",
                "reason": reason,
                "detail": f"DataOps rejection {index}",
                "provenance": "synthetic",
            }
            for index, reason in enumerate(reasons, start=1)
        ],
        "provenance": "synthetic",
    }


def test_rejection_summary_returns_200() -> None:
    response = _client().get("/api/dataops/evolution/rejection-summary")
    assert response.status_code == 200


def test_rejection_summary_reads_persisted_preseed() -> None:
    graph = InMemoryGraphStore()
    preseed = DemoPreseed(seed=20260711, graph_store=graph, profile="test")
    preseed.preseed_dataops()

    body = _client(graph=graph, include_persisted=True).get(
        "/api/dataops/evolution/rejection-summary"
    ).json()

    assert body["total_rejected"] == 6
    assert body["rejected_variants"]
    assert body["provenance"] == "synthetic"


def test_rejection_summary_breakdown_has_all_reasons() -> None:
    graph = InMemoryGraphStore(domain="dataops")
    graph.save_evolution("dataops", "preseed_rejection_summary", _persisted_payload())

    breakdown = _client(graph=graph, include_persisted=True).get(
        "/api/dataops/evolution/rejection-summary"
    ).json()["rejection_breakdown"]

    assert breakdown == {
        "correctness_floor": 2,
        "conservation": 3,
        "variance_stability": 1,
    }


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("conservation_gate_red", "conservation"),
        ("insufficient_improvement", "correctness_floor"),
        ("unstable_improvement", "variance_stability"),
    ],
)
def test_canonical_rejection_reason(raw: str, expected: str) -> None:
    assert _canonical_rejection_reason(raw) == expected


def test_log_returns_variant_entries() -> None:
    body = _client().get("/api/dataops/evolution/log").json()

    assert len(body) == 4
    assert all(entry["kind"] == "variant" for entry in body)
    assert {entry["id"] for entry in body} == {
        "AUTO_APPROVE_THRESHOLD_v1",
        "AUTO_APPROVE_THRESHOLD_v2",
        "SCHEDULING_CRITERIA_v1",
        "SCHEDULING_CRITERIA_v2",
    }


def test_active_returns_current_variant_info() -> None:
    body = _client().get("/api/dataops/evolution/active").json()

    assert body["variant"]["status"] == "active"
    assert body["active_variants"]
    assert body["domain"] == "dataops"
    assert isinstance(body["parameter_adjustments"], dict)


def test_empty_graph_returns_empty_summary() -> None:
    graph = InMemoryGraphStore(domain="dataops")

    body = _client(graph=graph, include_persisted=True).get(
        "/api/dataops/evolution/rejection-summary"
    ).json()

    assert body == {
        "total_tested": 0,
        "total_promoted": 0,
        "total_rejected": 0,
        "rejection_breakdown": {
            "correctness_floor": 0,
            "conservation": 0,
            "variance_stability": 0,
        },
        "rejected_variants": [],
        "provenance": "learned",
    }
