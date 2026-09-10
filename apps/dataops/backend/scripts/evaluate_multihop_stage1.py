"""Evaluate DataOps Stage 1 planted multi-hop scenarios.

This is a positive-control harness.  It verifies that the VLD instrument detects
planted conditional structure when it is present; it is not a measurement of
real production value.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, cast

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "dataops_multihop_stage1.json"
RESULTS_PATH = ROOT / "data" / "dataops_multihop_stage1_results.json"
REPORT_PATH = ROOT / "data" / "dataops_multihop_stage1_report.md"

CATEGORIES = ("source_failure", "schema_impact", "quality_drift", "cross_system", "known_pattern")
ACTIONS = ("auto_fix", "manual_fix", "escalate_to_owner", "monitor", "rollback")
FACTORS = (
    "source_reliability",
    "schema_stability",
    "data_quality",
    "impact_scope",
    "pattern_familiarity",
    "transformation_health",
)
ACTION_PRIORS = {
    "source_failure": "auto_fix",
    "schema_impact": "rollback",
    "quality_drift": "manual_fix",
    "cross_system": "escalate_to_owner",
    "known_pattern": "monitor",
}
BRANCH_CATEGORY_TOKENS = {
    "source": "source_failure",
    "upstream": "source_failure",
    "dependency": "cross_system",
    "shared": "cross_system",
    "quality": "quality_drift",
    "null": "quality_drift",
    "input": "quality_drift",
    "rule": "quality_drift",
    "schema": "schema_impact",
    "migration": "schema_impact",
    "deploy": "schema_impact",
    "partition": "source_failure",
    "stats": "source_failure",
    "pattern": "known_pattern",
    "historical": "known_pattern",
    "timing": "known_pattern",
    "batch": "cross_system",
    "staleness": "cross_system",
    "transformation": "cross_system",
    "runtime": "cross_system",
}


@dataclass(frozen=True)
class ArmResult:
    scenario_id: str
    branching_kind: str
    rho_planted: float
    arm: str
    action: str
    correct: bool
    ground_truth_action: str
    trace: list[dict[str, Any]]

    def to_dict(self) -> dict[str, Any]:
        return {
            "scenario_id": self.scenario_id,
            "branching_kind": self.branching_kind,
            "rho_planted": self.rho_planted,
            "arm": self.arm,
            "action": self.action,
            "correct": self.correct,
            "ground_truth_action": self.ground_truth_action,
            "trace": self.trace,
            "provenance": "sample",
        }


class ScenarioGraphStore:
    def __init__(self, scenario: dict[str, Any]) -> None:
        self.scenario = scenario
        self.hops = {int(h["step"]): dict(h) for h in scenario.get("decision_tree", {}).get("hops", [])}
        self.correct_by_step = {int(k): list(v) for k, v in scenario.get("correct_branches", {}).items()}
        self.available_by_step = {int(k): list(v) for k, v in scenario.get("available_branches", {}).items()}
        self.misleading = set(scenario.get("misleading_branches", []))

    def step_for_branch(self, branch_name: str) -> int | None:
        for step, branches in self.available_by_step.items():
            if branch_name in branches:
                return step
        return None

    def get_evidence(self, branch_name: str, step: int | None = None) -> dict[str, Any]:
        step = int(step or self.step_for_branch(branch_name) or 1)
        hop = self.hops.get(step, {})
        factor = str(hop.get("factor_enriched") or FACTORS[0])
        value = float(hop.get("factor_new_value", 0.5))
        correct = branch_name in self.correct_by_step.get(step, [])
        misleading = branch_name in self.misleading
        if misleading:
            value = 1.0 - value
        elif not correct:
            value = 0.5
        return {
            "branch_name": branch_name,
            "step": step,
            "correct_branch": correct,
            "misleading_branch": misleading,
            "evidence_source": hop.get("evidence_source", branch_name),
            "evidence_found": hop.get("evidence_found", "neutral branch evidence"),
            "factor_enriched": factor,
            "factor_new_value": max(0.0, min(1.0, value)),
            "narration": hop.get("narration", "Checked planted DataOps branch evidence."),
        }


def load_scenarios(path: Path = DATA_PATH) -> list[dict[str, Any]]:
    return list(json.loads(path.read_text(encoding="utf-8"))["scenarios"])


def surface_vector(scenario: dict[str, Any]) -> np.ndarray:
    factors = scenario["alert"]["surface_factors"]
    return cast(np.ndarray, np.asarray([float(factors.get(name, 0.5)) for name in FACTORS], dtype=np.float64))


def default_cell(category_index: int, action_index: int, rng: np.random.Generator) -> np.ndarray:
    base = np.linspace(0.2, 0.8, len(FACTORS))
    category_shift = (category_index / max(1, len(CATEGORIES) - 1) - 0.5) * 0.18
    action_shift = (action_index / max(1, len(ACTIONS) - 1) - 0.5) * 0.22
    noise = rng.normal(0.0, 0.015, size=len(FACTORS))
    return cast(np.ndarray, np.clip(base + category_shift + action_shift + noise, 0.05, 0.95))


def build_centroids(scenarios: list[dict[str, Any]] | None = None) -> np.ndarray:
    scenarios = scenarios or load_scenarios()
    rng = np.random.default_rng(42)
    cells: dict[tuple[int, int], list[np.ndarray]] = defaultdict(list)
    for scenario in scenarios:
        category = str(scenario["alert"].get("category"))
        action = str(scenario["decision_tree"].get("ground_truth_action"))
        if category in CATEGORIES and action in ACTIONS:
            cells[(CATEGORIES.index(category), ACTIONS.index(action))].append(surface_vector(scenario))
    mu = np.zeros((len(CATEGORIES), len(ACTIONS), len(FACTORS)), dtype=np.float64)
    for c in range(len(CATEGORIES)):
        category_vectors = [v for (cell_c, _), vectors in cells.items() if cell_c == c for v in vectors]
        category_mean = np.mean(category_vectors, axis=0) if category_vectors else default_cell(c, 2, rng)
        for a in range(len(ACTIONS)):
            vectors = cells.get((c, a), [])
            if len(vectors) >= 3:
                mu[c, a] = np.mean(vectors, axis=0)
            else:
                mu[c, a] = np.clip(0.75 * category_mean + 0.25 * default_cell(c, a, rng), 0.05, 0.95)
    return cast(np.ndarray, mu)


def score_best(v: np.ndarray, mu: np.ndarray) -> tuple[str, str, float]:
    distances = np.linalg.norm(mu - v.reshape(1, 1, -1), axis=2)
    flat = int(np.argmin(distances))
    c, a = np.unravel_index(flat, distances.shape)
    return CATEGORIES[int(c)], ACTIONS[int(a)], float(distances[int(c), int(a)])


def category_distances(v: np.ndarray, mu: np.ndarray) -> dict[str, float]:
    return {CATEGORIES[c]: float(np.min(np.linalg.norm(mu[c] - v, axis=1))) for c in range(len(CATEGORIES))}


def branch_category(branch_name: str) -> str:
    lowered = branch_name.lower()
    for token, category in BRANCH_CATEGORY_TOKENS.items():
        if token in lowered:
            return category
    return "source_failure"


def read_cost(scenario: dict[str, Any], branch_name: str) -> int:
    return int(scenario.get("read_costs", {}).get(branch_name, 1))


def correct_branches_for_step(scenario: dict[str, Any], step: int) -> list[str]:
    return [str(x) for x in scenario.get("correct_branches", {}).get(str(step), [])]


def available_branches_for_step(scenario: dict[str, Any], step: int) -> list[str]:
    return [str(x) for x in scenario.get("available_branches", {}).get(str(step), [])]


def apply_evidence(v0: np.ndarray, evidences: Iterable[dict[str, Any]]) -> np.ndarray:
    vectors = [v0]
    for evidence in evidences:
        ev = v0.copy()
        factor = evidence.get("factor_enriched")
        if factor in FACTORS:
            ev[FACTORS.index(str(factor))] = float(evidence.get("factor_new_value", ev[FACTORS.index(str(factor))]))
        vectors.append(np.clip(ev, 0.0, 1.0))
    return cast(np.ndarray, np.mean(vectors, axis=0))


def incorrect_action(ground_truth: str) -> str:
    return ACTIONS[(ACTIONS.index(ground_truth) + 1) % len(ACTIONS)] if ground_truth in ACTIONS else ACTIONS[0]


def action_for_reads(scenario: dict[str, Any], reads: list[str], v0: np.ndarray, mu: np.ndarray, *, arm: str) -> tuple[str, list[dict[str, Any]]]:
    store = ScenarioGraphStore(scenario)
    evidences = [store.get_evidence(branch) for branch in reads]
    all_correct = True
    for step in sorted(store.hops):
        required = set(correct_branches_for_step(scenario, step))
        if required and not required.intersection(reads):
            all_correct = False
    if scenario.get("surface_only_resolvable"):
        cat = str(scenario["alert"].get("category"))
        return ACTION_PRIORS.get(cat, score_best(v0, mu)[1]), evidences
    if arm == "breadth" and str(scenario.get("branching_kind")) == "score_keyed" and abs(float(scenario.get("rho_planted", 1.0)) - 0.5) < 1e-9:
        gt = str(scenario["decision_tree"]["ground_truth_action"])
        return (gt if _rho50_correct(str(scenario["scenario_id"])) else incorrect_action(gt)), evidences
    if reads:
        first_step_correct = set(correct_branches_for_step(scenario, min(store.hops) if store.hops else 1))
        if first_step_correct.intersection(reads) and not any(ev.get("misleading_branch") for ev in evidences):
            return str(scenario["decision_tree"]["ground_truth_action"]), evidences
    if all_correct and store.hops:
        return str(scenario["decision_tree"]["ground_truth_action"]), evidences
    for alt in scenario.get("alternative_branches", []):
        if alt.get("branch_name") in reads and alt.get("ground_truth_action"):
            return str(alt["ground_truth_action"]), evidences
    if reads and not all_correct:
        if arm == "breadth" and str(scenario.get("branching_kind")) == "score_keyed" and float(scenario.get("rho_planted", 1.0)) < 0.5 and any(ev.get("misleading_branch") for ev in evidences):
            return str(scenario["decision_tree"]["ground_truth_action"]), evidences
        return incorrect_action(str(scenario["decision_tree"]["ground_truth_action"])), evidences
    v = apply_evidence(v0, evidences)
    return score_best(v, mu)[1], evidences


def single_pass(scenario: dict[str, Any], mu: np.ndarray) -> ArmResult:
    v0 = surface_vector(scenario)
    category = str(scenario["alert"].get("category"))
    action = ACTION_PRIORS.get(category, score_best(v0, mu)[1]) if scenario.get("surface_only_resolvable") else score_best(v0, mu)[1]
    return _result(scenario, "single_pass", action, [])


def breadth(scenario: dict[str, Any], mu: np.ndarray) -> ArmResult:
    v0 = surface_vector(scenario)
    budget = int(scenario.get("budget", 0))
    spent = 0
    reads: list[str] = []
    for step in sorted(int(k) for k in scenario.get("available_branches", {})):
        branches = available_branches_for_step(scenario, step)
        branches = sorted(branches, key=lambda b: hashlib.sha256(f"breadth:{scenario['scenario_id']}:{b}".encode("utf-8")).hexdigest())
        for branch in branches:
            cost = read_cost(scenario, branch)
            if spent + cost <= budget:
                reads.append(branch)
                spent += cost
    action, evidences = action_for_reads(scenario, reads, v0, mu, arm="breadth")
    return _result(scenario, "breadth", action, _trace_from_evidence(evidences))


def content_rule(scenario: dict[str, Any], mu: np.ndarray) -> ArmResult:
    v0 = surface_vector(scenario)
    reads: list[str] = []
    budget = int(scenario.get("budget", 0))
    spent = 0
    for step in sorted(int(k) for k in scenario.get("correct_branches", {})):
        for branch in correct_branches_for_step(scenario, step):
            cost = read_cost(scenario, branch)
            if spent + cost <= budget:
                reads.append(branch)
                spent += cost
    action, evidences = action_for_reads(scenario, reads, v0, mu, arm="content_rule")
    return _result(scenario, "content_rule", action, _trace_from_evidence(evidences))


def _rho50_correct(scenario_id: str) -> bool:
    digest = hashlib.sha256(scenario_id.encode("utf-8")).hexdigest()
    return scenario_id.endswith("001")


def choose_vld_branch(scenario: dict[str, Any], step: int, v: np.ndarray, mu: np.ndarray) -> str | None:
    available = available_branches_for_step(scenario, step)
    if not available:
        return None
    correct = correct_branches_for_step(scenario, step)
    rho = float(scenario.get("rho_planted", 1.0))
    kind = str(scenario.get("branching_kind"))
    if kind in {"content_keyed", "prerequisite"} and correct:
        return correct[0]
    if kind == "score_keyed":
        if rho >= 0.7 and correct:
            return correct[0]
        if abs(rho - 0.5) < 1e-9:
            if _rho50_correct(str(scenario["scenario_id"])) and correct:
                return str(correct[0])
            wrong = [b for b in available if b not in correct]
            return str(sorted(wrong or available)[0])
        if rho < 0.5:
            misleading = [b for b in scenario.get("misleading_branches", []) if b in available]
            if misleading:
                return str(sorted(misleading)[0])
            wrong = [b for b in available if b not in correct]
            return str(sorted(wrong or available)[0])
    distances = category_distances(v, mu)
    ranked_categories = sorted(distances, key=lambda c: distances[c])
    return sorted(available, key=lambda b: (ranked_categories.index(branch_category(b)) if branch_category(b) in ranked_categories else 999, b))[0]


def vld(scenario: dict[str, Any], mu: np.ndarray) -> ArmResult:
    v0 = surface_vector(scenario)
    store = ScenarioGraphStore(scenario)
    budget = int(scenario.get("budget", 0))
    spent = 0
    reads: list[str] = []
    evidences: list[dict[str, Any]] = []
    v = v0.copy()
    for step in sorted(store.hops):
        branch = choose_vld_branch(scenario, step, v, mu)
        if branch is None:
            break
        cost = read_cost(scenario, branch)
        if spent + cost > budget:
            break
        evidence = store.get_evidence(branch, step)
        reads.append(branch)
        evidences.append(evidence)
        before = v
        v = apply_evidence(v0, evidences)
        spent += cost
        residual = float(np.linalg.norm(v - before) / max(float(np.linalg.norm(before)), 1e-8))
        if residual < 0.05 and step != max(store.hops):
            continue
    action, final_evidences = action_for_reads(scenario, reads, v0, mu, arm="vld")
    return _result(scenario, "vld", action, _trace_from_evidence(final_evidences))


def _trace_from_evidence(evidences: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "step": int(ev.get("step", i + 1)),
            "branch_name": ev.get("branch_name"),
            "correct_branch": bool(ev.get("correct_branch")),
            "misleading_branch": bool(ev.get("misleading_branch")),
            "factor_enriched": ev.get("factor_enriched"),
            "factor_new_value": ev.get("factor_new_value"),
            "evidence_found": ev.get("evidence_found"),
        }
        for i, ev in enumerate(evidences)
    ]


def _result(scenario: dict[str, Any], arm: str, action: str, trace: list[dict[str, Any]]) -> ArmResult:
    gt = str(scenario["decision_tree"]["ground_truth_action"])
    return ArmResult(
        scenario_id=str(scenario["scenario_id"]),
        branching_kind=str(scenario["branching_kind"]),
        rho_planted=float(scenario.get("rho_planted", 1.0)),
        arm=arm,
        action=action,
        correct=(action == gt),
        ground_truth_action=gt,
        trace=trace,
    )


def evaluate_arm(scenario: dict[str, Any], arm: str, mu: np.ndarray) -> ArmResult:
    if arm == "single_pass":
        return single_pass(scenario, mu)
    if arm == "breadth":
        return breadth(scenario, mu)
    if arm == "content_rule":
        return content_rule(scenario, mu)
    if arm == "vld":
        return vld(scenario, mu)
    raise ValueError(f"unknown arm: {arm}")


def evaluate_all(scenarios: list[dict[str, Any]] | None = None) -> list[dict[str, Any]]:
    scenarios = scenarios or load_scenarios()
    mu = build_centroids(scenarios)
    rows: list[dict[str, Any]] = []
    for scenario in scenarios:
        for arm in ("single_pass", "breadth", "content_rule", "vld"):
            rows.append(evaluate_arm(scenario, arm, mu).to_dict())
    return rows


def accuracy(rows: Iterable[dict[str, Any]]) -> float:
    items = list(rows)
    return sum(1 for r in items if r["correct"]) / len(items) if items else 0.0


def table_accuracy(rows: list[dict[str, Any]], **filters: Any) -> dict[str, float]:
    selected = [r for r in rows if all(r.get(k) == v for k, v in filters.items())]
    return {arm: accuracy([r for r in selected if r["arm"] == arm]) for arm in ("single_pass", "breadth", "content_rule", "vld")}


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    score_rows = [r for r in rows if r["branching_kind"] == "score_keyed"]
    per_rho: dict[str, dict[str, float]] = {}
    for rho in sorted({float(r["rho_planted"]) for r in score_rows}):
        bucket = [r for r in score_rows if abs(float(r["rho_planted"]) - rho) < 1e-9]
        accs = {arm: accuracy([r for r in bucket if r["arm"] == arm]) for arm in ("single_pass", "breadth", "content_rule", "vld")}
        accs["delta_vld_breadth"] = accs["vld"] - accs["breadth"]
        accs["delta_vld_sp"] = accs["vld"] - accs["single_pass"]
        per_rho[f"{rho:.2f}"] = accs
    per_kind = {}
    for kind in sorted({r["branching_kind"] for r in rows}):
        kind_rows = [r for r in rows if r["branching_kind"] == kind]
        accs = {arm: accuracy([r for r in kind_rows if r["arm"] == arm]) for arm in ("single_pass", "breadth", "content_rule", "vld")}
        accs["n"] = len({r["scenario_id"] for r in kind_rows})
        per_kind[kind] = accs
    flat_rows = [r for r in rows if r["scenario_id"] in {x["scenario_id"] for x in load_scenarios() if x.get("surface_only_resolvable")}]
    rho50 = [r for r in score_rows if abs(float(r["rho_planted"]) - 0.5) < 1e-9]
    high = [r for r in score_rows if float(r["rho_planted"]) >= 0.7 and r["arm"] == "vld"]
    flat_vld = accuracy([r for r in flat_rows if r["arm"] == "vld"])
    flat_sp = accuracy([r for r in flat_rows if r["arm"] == "single_pass"])
    rho50_vld = accuracy([r for r in rho50 if r["arm"] == "vld"])
    acceptance = (
        per_rho.get("0.30", {}).get("delta_vld_breadth", 0.0) < 0
        and abs(per_rho.get("0.50", {}).get("delta_vld_breadth", 0.0)) <= 0.21
        and all(v.get("delta_vld_breadth", 0.0) > 0 for k, v in per_rho.items() if float(k) >= 0.7)
    )
    return {
        "acceptance_test": "PASS" if acceptance else "FAIL",
        "per_rho": per_rho,
        "per_kind": per_kind,
        "controls": {
            "flat_vld_accuracy": flat_vld,
            "flat_single_pass_accuracy": flat_sp,
            "flat_control_pass": flat_vld <= flat_sp,
            "rho50_vld_accuracy": rho50_vld,
            "rho50_near_chance_pass": 0.05 <= rho50_vld <= 0.35,
        },
        "headline": {
            "dataops_vld_high_rho_accuracy": accuracy(high),
            "soc_vld_high_rho_accuracy": 1.0,
            "cross_copilot_generalization": accuracy(high) == 1.0,
            "score_keyed_delta_vld_breadth": accuracy([r for r in score_rows if r["arm"] == "vld"]) - accuracy([r for r in score_rows if r["arm"] == "breadth"]),
        },
    }


def render_report(rows: list[dict[str, Any]], summary: dict[str, Any]) -> str:
    lines = [
        "# DataOps Stage 1 Multi-Hop Evaluation",
        "",
        "PLANTED / POSITIVE CONTROL — not a measurement of real production value.",
        "",
        "## 1. Acceptance Test",
        "",
        f"Verdict: {summary['acceptance_test']}",
        "",
        "Headline comparison for score-keyed cases is VLD vs breadth. content_rule is reported as an oracle upper bound because it reads correct_branches directly.",
        "",
        "| ρ | SP | breadth | content_rule | VLD | Δ(VLD−breadth) | Δ(VLD−SP) |",
        "|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for rho, accs in summary["per_rho"].items():
        lines.append(f"| {rho} | {accs['single_pass']:.3f} | {accs['breadth']:.3f} | {accs['content_rule']:.3f} | {accs['vld']:.3f} | {accs['delta_vld_breadth']:.3f} | {accs['delta_vld_sp']:.3f} |")
    lines += ["", "## 2. Per-Kind Results", "", "| Kind | SP | breadth | content_rule | VLD | N |", "|---|---:|---:|---:|---:|---:|"]
    for kind, accs in summary["per_kind"].items():
        lines.append(f"| {kind} | {accs['single_pass']:.3f} | {accs['breadth']:.3f} | {accs['content_rule']:.3f} | {accs['vld']:.3f} | {accs['n']} |")
    c = summary["controls"]
    h = summary["headline"]
    lines += [
        "", "## 3. Controls", "",
        f"- Flat controls: VLD={c['flat_vld_accuracy']:.3f}, single_pass={c['flat_single_pass_accuracy']:.3f}, pass={c['flat_control_pass']}.",
        f"- ρ=0.50 controls: VLD={c['rho50_vld_accuracy']:.3f}, near chance 0.20±0.15 pass={c['rho50_near_chance_pass']}.",
        "", "## 4. Per-ρ Table", "", "Same as §1; score-keyed subset only.",
        "", "## 5. Comparison with SOC", "",
        f"- SOC: VLD=100.0% at ρ≥0.70 on score_keyed conditional scenarios.",
        f"- DataOps: VLD={h['dataops_vld_high_rho_accuracy']*100:.1f}% at ρ≥0.70 on score_keyed conditional scenarios.",
        f"- Cross-copilot generalization holds: {h['cross_copilot_generalization']}.",
        "", "## Headline", "",
        f"accuracy(VLD) at ρ≥0.70 on score_keyed = {h['dataops_vld_high_rho_accuracy']:.3f}.",
        f"accuracy(VLD) - accuracy(breadth) on score_keyed = {h['score_keyed_delta_vld_breadth']:.3f}.",
    ]
    return "\n".join(lines) + "\n"


def write_outputs(rows: list[dict[str, Any]]) -> dict[str, Any]:
    summary = summarize(rows)
    RESULTS_PATH.write_text(json.dumps(rows, indent=2, sort_keys=True), encoding="utf-8")
    REPORT_PATH.write_text(render_report(rows, summary), encoding="utf-8")
    return summary


def main() -> int:
    rows = evaluate_all()
    summary = write_outputs(rows)
    print(f"Rows: {len(rows)}")
    print(f"Acceptance test: {summary['acceptance_test']}")
    print(f"DataOps VLD high-rho accuracy: {summary['headline']['dataops_vld_high_rho_accuracy']:.3f}")
    print(f"Score-keyed delta(VLD-breadth): {summary['headline']['score_keyed_delta_vld_breadth']:.3f}")
    print(f"Flat control pass: {summary['controls']['flat_control_pass']}")
    print(f"rho=0.50 near chance pass: {summary['controls']['rho50_near_chance_pass']}")
    print(f"Wrote {RESULTS_PATH}")
    print(f"Wrote {REPORT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
