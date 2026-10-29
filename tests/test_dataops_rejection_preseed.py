"""DataOps preseed rejection evidence contracts."""

from __future__ import annotations

import pytest

from copilot_sdk.demo.preseed import CopilotPreseedResult, DemoPreseed
from copilot_sdk.graph import InMemoryGraphStore


@pytest.fixture(scope="module")
def dataops_preseed() -> tuple[DemoPreseed, CopilotPreseedResult]:
    graph = InMemoryGraphStore()
    preseed = DemoPreseed(seed=20260711, graph_store=graph, profile="test")
    return preseed, preseed.preseed_dataops()


def test_preseed_dataops_includes_six_rejected_variants(dataops_preseed) -> None:
    _, result = dataops_preseed

    assert len(result.rejected_variants) == 6
    assert {entry["reason"] for entry in result.rejected_variants} == {
        "conservation",
        "correctness_floor",
        "variance_stability",
    }


def test_preseed_dataops_persists_rejection_summary(dataops_preseed) -> None:
    preseed, _ = dataops_preseed

    payload = preseed.graph_store.get_evolution(
        "dataops",
        "preseed_rejection_summary",
    )

    assert payload is not None
    assert payload["total_rejected"] == 6
    assert payload["rejection_breakdown"] == {
        "correctness_floor": 2,
        "conservation": 3,
        "variance_stability": 1,
    }


def test_preseed_rejection_ids_are_dataops_specific_and_unique(dataops_preseed) -> None:
    _, result = dataops_preseed
    identifiers = [entry["variant_id"] for entry in result.rejected_variants]

    assert len(set(identifiers)) == 6
    assert all(identifier.startswith("DATAOPS_REJECT_") for identifier in identifiers)
    assert not {
        "AUTO_APPROVE_THRESHOLD_v1",
        "AUTO_APPROVE_THRESHOLD_v2",
        "SCHEDULING_CRITERIA_v1",
        "SCHEDULING_CRITERIA_v2",
    }.intersection(identifiers)
