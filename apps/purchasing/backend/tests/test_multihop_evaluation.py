from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "evaluate_multihop_stage1.py"
DATA_PATH = ROOT / "data" / "purchasing_multihop_stage1.json"
RESULTS_PATH = ROOT / "data" / "purchasing_multihop_stage1_results.json"
REPORT_PATH = ROOT / "data" / "purchasing_multihop_stage1_report.md"

spec = importlib.util.spec_from_file_location("purchasing_multihop_eval", SCRIPT_PATH)
assert spec is not None and spec.loader is not None
mh = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mh
spec.loader.exec_module(mh)


def scenarios() -> list[dict]:
    return mh.load_scenarios()


def by_kind(kind: str) -> dict:
    return next(s for s in scenarios() if s["branching_kind"] == kind and not s.get("surface_only_resolvable"))


def test_scenario_graph_store_loads_scenario() -> None:
    scenario = scenarios()[0]
    store = mh.ScenarioGraphStore(scenario)
    assert store.scenario["scenario_id"] == scenario["scenario_id"]
    assert store.available_by_step
    assert store.hops


def test_scenario_graph_store_returns_different_evidence_for_correct_vs_misleading() -> None:
    scenario = next(s for s in scenarios() if s.get("misleading_branches"))
    store = mh.ScenarioGraphStore(scenario)
    correct = scenario["correct_branches"]["1"][0]
    misleading = next(b for b in scenario["misleading_branches"] if b != correct)
    correct_ev = store.get_evidence(correct, 1)
    misleading_ev = store.get_evidence(misleading, 1)
    assert correct_ev["correct_branch"] is True
    assert misleading_ev["misleading_branch"] is True
    assert correct_ev["factor_new_value"] != misleading_ev["factor_new_value"]


def test_single_pass_uses_only_surface_factors() -> None:
    scenario = by_kind("score_keyed")
    mu = mh.build_centroids(scenarios())
    result = mh.single_pass(scenario, mu)
    expected_action = mh.score_best(mh.surface_vector(scenario), mu)[0]
    assert result.action == expected_action
    assert result.trace == []
    assert len(mh.surface_vector(scenario)) == 6


def test_breadth_reads_all_branches_up_to_budget() -> None:
    scenario = by_kind("content_keyed")
    mu = mh.build_centroids(scenarios())
    result = mh.breadth(scenario, mu)
    spent = sum(mh.read_cost(scenario, str(step["branch_name"])) for step in result.trace)
    assert spent <= int(scenario["budget"])
    assert len(result.trace) >= 1


def test_content_rule_uses_correct_branches() -> None:
    scenario = by_kind("score_keyed")
    mu = mh.build_centroids(scenarios())
    result = mh.content_rule(scenario, mu)
    read_branches = {step["branch_name"] for step in result.trace}
    correct = {branch for branches in scenario["correct_branches"].values() for branch in branches}
    assert read_branches <= correct
    assert result.correct is True


def test_vld_produces_trace_with_at_least_one_step() -> None:
    scenario = by_kind("score_keyed")
    mu = mh.build_centroids(scenarios())
    result = mh.vld(scenario, mu)
    assert result.arm == "vld"
    assert len(result.trace) >= 1


def test_flat_control_vld_no_better_than_single_pass() -> None:
    rows = mh.evaluate_all(scenarios())
    flat_ids = {s["scenario_id"] for s in scenarios() if s.get("surface_only_resolvable")}
    for scenario_id in flat_ids:
        sp = next(r for r in rows if r["scenario_id"] == scenario_id and r["arm"] == "single_pass")
        vld = next(r for r in rows if r["scenario_id"] == scenario_id and r["arm"] == "vld")
        assert not (vld["correct"] and not sp["correct"])


def test_rho_050_vld_near_chance() -> None:
    rows = mh.evaluate_all(scenarios())
    rho50_ids = {
        s["scenario_id"]
        for s in scenarios()
        if s["branching_kind"] == "score_keyed" and abs(float(s["rho_planted"]) - 0.5) < 1e-9
    }
    vld_rows = [r for r in rows if r["scenario_id"] in rho50_ids and r["arm"] == "vld"]
    acc = mh.accuracy(vld_rows)
    assert abs(acc - (1 / 6)) <= 0.20


def test_all_40_instances_evaluated() -> None:
    rows = mh.evaluate_all(scenarios())
    assert len({r["scenario_id"] for r in rows}) == 40


def test_results_json_has_160_rows(tmp_path) -> None:
    rows = mh.evaluate_all(scenarios())
    mh.write_outputs(rows)
    data = json.loads(RESULTS_PATH.read_text(encoding="utf-8"))
    assert len(data) == 160
    assert {r["arm"] for r in data} == {"single_pass", "breadth", "content_rule", "vld"}
    assert all(r.get("provenance") == "sample" for r in data)


def test_enriched_centroids_used() -> None:
    mu_enriched = mh.build_centroids(scenarios())
    mu_surface = mh.build_surface_centroids(scenarios())
    assert mu_enriched.shape == (6, 6)
    assert float(np.linalg.norm(mu_enriched - mu_surface)) > 0.0


def test_report_generated_and_non_empty() -> None:
    rows = mh.evaluate_all(scenarios())
    summary = mh.write_outputs(rows)
    assert summary["acceptance_test"] == "PASS"
    assert REPORT_PATH.exists()
    assert REPORT_PATH.stat().st_size > 500

