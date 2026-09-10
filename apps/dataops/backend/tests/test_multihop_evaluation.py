from __future__ import annotations

import json
import importlib.util
import sys
from pathlib import Path
from types import ModuleType
from typing import Any, cast

SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "evaluate_multihop_stage1.py"
spec = importlib.util.spec_from_file_location("dataops_evaluate_multihop_stage1", SCRIPT_PATH)
assert spec is not None and spec.loader is not None
mh = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mh
spec.loader.exec_module(mh)
mh = cast(Any, mh)


def _scenario(kind: str | None = None, *, rho: float | None = None, flat: bool | None = None) -> dict[str, Any]:
    for scenario in mh.load_scenarios():
        if kind is not None and scenario["branching_kind"] != kind:
            continue
        if rho is not None and abs(float(scenario.get("rho_planted", 0.0)) - rho) > 1e-9:
            continue
        if flat is not None and bool(scenario.get("surface_only_resolvable")) is not flat:
            continue
        return dict(scenario)
    raise AssertionError("scenario not found")


def test_scenario_graph_store_loads_scenario_without_error() -> None:
    scenario = _scenario("score_keyed")
    store = mh.ScenarioGraphStore(scenario)
    assert store.scenario["scenario_id"] == scenario["scenario_id"]
    assert store.hops
    assert store.available_by_step


def test_scenario_graph_store_returns_different_correct_and_misleading_evidence() -> None:
    scenario = _scenario("score_keyed")
    store = mh.ScenarioGraphStore(scenario)
    correct = scenario["correct_branches"]["1"][0]
    misleading = scenario["misleading_branches"][0]
    correct_ev = store.get_evidence(correct, 1)
    misleading_ev = store.get_evidence(misleading, 1)
    assert correct_ev["correct_branch"] is True
    assert misleading_ev["misleading_branch"] is True
    assert correct_ev["factor_new_value"] != misleading_ev["factor_new_value"]


def test_single_pass_arm_uses_only_surface_factors() -> None:
    scenario = _scenario("score_keyed")
    mu = mh.build_centroids([scenario])
    result = mh.single_pass(scenario, mu)
    assert result.arm == "single_pass"
    assert result.trace == []


def test_breadth_arm_reads_all_branches_up_to_budget() -> None:
    scenario = _scenario("score_keyed")
    mu = mh.build_centroids(mh.load_scenarios())
    result = mh.breadth(scenario, mu)
    spent = sum(mh.read_cost(scenario, str(step["branch_name"])) for step in result.trace)
    assert spent <= int(scenario["budget"])
    assert len(result.trace) >= 1


def test_content_rule_arm_uses_correct_branches() -> None:
    scenario = _scenario("score_keyed", rho=0.7)
    mu = mh.build_centroids(mh.load_scenarios())
    result = mh.content_rule(scenario, mu)
    correct = {b for values in scenario["correct_branches"].values() for b in values}
    assert {str(step["branch_name"]) for step in result.trace}.issubset(correct)
    assert result.correct is True


def test_vld_arm_produces_trace_with_at_least_one_step() -> None:
    scenario = _scenario("score_keyed", rho=0.7)
    mu = mh.build_centroids(mh.load_scenarios())
    result = mh.vld(scenario, mu)
    assert result.arm == "vld"
    assert len(result.trace) >= 1


def test_flat_control_vld_not_better_than_single_pass() -> None:
    rows = mh.evaluate_all()
    flat_ids = {s["scenario_id"] for s in mh.load_scenarios() if s.get("surface_only_resolvable")}
    flat = [r for r in rows if r["scenario_id"] in flat_ids]
    assert mh.accuracy([r for r in flat if r["arm"] == "vld"]) <= mh.accuracy([r for r in flat if r["arm"] == "single_pass"])


def test_rho50_vld_near_chance() -> None:
    rows = mh.evaluate_all()
    rho50 = [r for r in rows if r["branching_kind"] == "score_keyed" and abs(float(r["rho_planted"]) - 0.5) < 1e-9 and r["arm"] == "vld"]
    assert 0.05 <= mh.accuracy(rho50) <= 0.35


def test_all_50_instances_evaluated_without_crash() -> None:
    rows = mh.evaluate_all()
    assert len(rows) == 200
    assert len({r["scenario_id"] for r in rows}) == 50
    assert {r["arm"] for r in rows} == {"single_pass", "breadth", "content_rule", "vld"}


def test_results_json_has_expected_structure() -> None:
    rows = mh.evaluate_all()
    summary = mh.write_outputs(rows)
    data = json.loads(mh.RESULTS_PATH.read_text(encoding="utf-8"))
    assert len(data) == 200
    assert {"scenario_id", "branching_kind", "rho_planted", "arm", "action", "correct", "ground_truth_action", "trace"}.issubset(data[0])
    assert summary["acceptance_test"] in {"PASS", "FAIL"}
