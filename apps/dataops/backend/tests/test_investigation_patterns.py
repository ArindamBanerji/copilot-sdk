from __future__ import annotations

import math
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.graph_contract import DATAOPS_GRAPH_CONTRACT
from app.graph_queries import DataOpsGraphClient
from app.services.investigation_comparators import (
    BreadthPolicy,
    ContentRulePolicy,
    MajorityBranchPolicy,
    RandomBranchPolicy,
    SinglePassPolicy,
    expected_pattern_category,
)
from app.services.investigation_loop import DataOpsFactorProvider, InvestigationLoop
from app.services.investigation_patterns import (
    CONTRACT_EDGE_TYPES,
    DATAOPS_PATTERN_CATEGORIES,
    FACTOR_NAMES,
    PATTERN_REGISTRY,
    build_default_investigation_patterns,
)
from app.services.investigation_router import InvestigationRouter
from apps.dataops.backend.scripts.measure_rho_dataops import measure
from apps.dataops.backend.scripts.validate_use_cases import run_scenarios
from copilot_sdk.scoring.presets.dataops import DataOpsPreset


class StaticDataOpsScorer:
    def __init__(self) -> None:
        preset = DataOpsPreset()
        self.centroids = preset.bootstrap_centroids
        self.categories = list(preset.shape.category_names)
        self.actions = list(preset.shape.action_names)
        self.tau = 0.1


def test_patterns_instantiate_with_expected_categories(dataops_data_dir: Path) -> None:
    patterns = build_default_investigation_patterns(dataops_data_dir)
    assert [pattern.category for pattern in patterns] == list(DATAOPS_PATTERN_CATEGORIES)


def test_each_pattern_exposes_distinct_evidence_keys(dataops_data_dir: Path) -> None:
    patterns = build_default_investigation_patterns(dataops_data_dir)
    key_sets = [tuple(pattern.evidence_keys()) for pattern in patterns]
    assert len(set(key_sets)) == 5
    assert all(key_sets)


@pytest.mark.asyncio
async def test_patterns_return_non_empty_fixture_evidence(dataops_data_dir: Path) -> None:
    alert = _fixture_alert(dataops_data_dir, "ALERT-TIRE-001")
    graph = DataOpsGraphClient(fallback_dir=dataops_data_dir / "fallback")
    for pattern in build_default_investigation_patterns(dataops_data_dir):
        evidence = await pattern.execute(alert, graph)
        assert evidence["evidence_keys"] == pattern.evidence_keys()
        assert any(evidence.get(key) is not None for key in pattern.evidence_keys())


def test_pattern_registry_has_all_five_patterns() -> None:
    assert sorted(PATTERN_REGISTRY) == sorted(DATAOPS_PATTERN_CATEGORIES)


def test_router_computes_valid_category_distances(dataops_data_dir: Path) -> None:
    router = InvestigationRouter(build_default_investigation_patterns(dataops_data_dir))
    distances = router.category_distances(_vector(_fixture_alert(dataops_data_dir, "ALERT-TIRE-001")), StaticDataOpsScorer())
    assert sorted(distances) == sorted(DATAOPS_PATTERN_CATEGORIES)
    assert all(math.isfinite(value) for value in distances.values())


@pytest.mark.asyncio
async def test_investigation_loop_completes_on_fixture_alert(dataops_data_dir: Path) -> None:
    alert = _fixture_alert(dataops_data_dir, "ALERT-TIRE-001")
    patterns = build_default_investigation_patterns(dataops_data_dir)
    loop = InvestigationLoop(StaticDataOpsScorer(), InvestigationRouter(patterns), DataOpsFactorProvider(), L_max=3)
    result = await loop.investigate(alert, DataOpsGraphClient(fallback_dir=dataops_data_dir / "fallback"))
    assert result.steps >= 1
    assert result.trace[0].evidence_keys
    assert result.v_final


def test_investigate_endpoint_returns_valid_result(client: TestClient) -> None:
    response = client.post("/api/dataops/investigate", json={"alert_id": "ALERT-TIRE-001"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["policy"] == "dataops_vld"
    assert payload["steps"] >= 1
    assert payload["trace"][0]["evidence_keys"]


def test_patterns_use_existing_dataops_schema_edges(dataops_data_dir: Path) -> None:
    contract_edges = {edge.label for edge in DATAOPS_GRAPH_CONTRACT.edge_types}
    assert contract_edges == CONTRACT_EDGE_TYPES
    for pattern in build_default_investigation_patterns(dataops_data_dir):
        assert pattern.selected_edge in contract_edges


def test_comparator_policies_select_valid_patterns(dataops_data_dir: Path) -> None:
    alert = _fixture_alert(dataops_data_dir, "ALERT-TIRE-001")
    patterns = build_default_investigation_patterns(dataops_data_dir)
    router = InvestigationRouter(patterns)
    scorer = StaticDataOpsScorer()
    assert SinglePassPolicy().select(alert, patterns, router, scorer) is None
    assert ContentRulePolicy().select(alert, patterns, router, scorer).category_name == expected_pattern_category(alert)
    assert MajorityBranchPolicy().select(alert, patterns, router, scorer).category_name in DATAOPS_PATTERN_CATEGORIES
    assert RandomBranchPolicy(seed=1).select(alert, patterns, router, scorer).category_name in DATAOPS_PATTERN_CATEGORIES
    assert BreadthPolicy().select(alert, patterns, router, scorer).category_name == DATAOPS_PATTERN_CATEGORIES[0]


def test_rho_measurement_reports_valid_baselines(dataops_data_dir: Path) -> None:
    report = measure(dataops_data_dir)
    assert report["status"] == "OK"
    assert report["alerts"] >= 10
    assert 0.0 <= report["rho_VLD"] <= 1.0
    assert 0.0 <= report["rho_majority"] <= 1.0
    assert 0.0 <= report["rho_random"] <= 1.0


@pytest.mark.asyncio
async def test_schema_change_scenario_trace_matches_narrative(dataops_data_dir: Path) -> None:
    report = await run_scenarios(dataops_data_dir)
    scenario = report["schema_change_cascade"]
    assert scenario["matched_expected_narrative"] is True
    assert "schema_change_type" in scenario["evidence_keys"]
    assert "affected_systems_count" in scenario["evidence_keys"]


@pytest.mark.asyncio
async def test_recurring_scenario_trace_matches_narrative(dataops_data_dir: Path) -> None:
    report = await run_scenarios(dataops_data_dir)
    scenario = report["recurring_vs_novel"]
    assert scenario["matched_expected_narrative"] is True
    assert "known_pattern" in scenario["trace_categories"]
    assert "pattern_match_confidence" in scenario["evidence_keys"]


def _fixture_alert(data_dir: Path, alert_id: str) -> dict:
    payload = __import__("json").load((data_dir / "fallback" / "alerts.json").open(encoding="utf-8"))
    return next(alert for alert in payload["alerts"] if alert["alert_id"] == alert_id)


def _vector(alert: dict) -> list[float]:
    factors = alert.get("factors") or {}
    return [float(factors.get(name, 0.0) or 0.0) for name in FACTOR_NAMES]
