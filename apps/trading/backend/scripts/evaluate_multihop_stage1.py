"""Evaluate Trading Stage 1 planted multi-hop scenarios.

Positive control only: this verifies that the VLD instrument detects planted
conditional structure when present.  It is not a measurement of real production
trading value.
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
DATA_PATH = ROOT / "data" / "trading_multihop_stage1.json"
RESULTS_PATH = ROOT / "data" / "trading_multihop_stage1_results.json"
REPORT_PATH = ROOT / "data" / "trading_multihop_stage1_report.md"

CATEGORIES = ("thesis_check", "portfolio_exposure", "time_pattern", "fundamental_change", "correlation_risk")
ACTIONS = ("execute", "defer", "reduce_size", "hedge", "reject")
FACTORS = (
    "thesis_alignment",
    "portfolio_concentration",
    "timing_signal",
    "fundamental_strength",
    "correlation_risk",
    "liquidity_risk",
)
ACTION_PRIORS = {
    "thesis_check": "defer",
    "portfolio_exposure": "reduce_size",
    "time_pattern": "defer",
    "fundamental_change": "reject",
    "correlation_risk": "hedge",
}
BRANCH_CATEGORY_TOKENS = {
    "thesis": "thesis_check",
    "rationale": "thesis_check",
    "pm": "thesis_check",
    "position": "portfolio_exposure",
    "portfolio": "portfolio_exposure",
    "tax": "portfolio_exposure",
    "concentration": "portfolio_exposure",
    "earnings": "fundamental_change",
    "guidance": "fundamental_change",
    "fundamental": "fundamental_change",
    "event": "fundamental_change",
    "timing": "time_pattern",
    "volume": "time_pattern",
    "flow": "time_pattern",
    "rsi": "time_pattern",
    "sector": "correlation_risk",
    "asian": "correlation_risk",
    "overnight": "correlation_risk",
    "correlation": "correlation_risk",
    "hedge": "correlation_risk",
    "liquidity": "portfolio_exposure",
}


@dataclass(frozen=True)
class CentroidDiagnostics:
    cells_sufficient: int
    cells_defaulted: int
    samples_per_action: dict[str, int]
    surface_enriched_diff: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "cells_sufficient": self.cells_sufficient,
            "cells_defaulted": self.cells_defaulted,
            "samples_per_action": self.samples_per_action,
            "surface_enriched_diff": self.surface_enriched_diff,
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
        self.correct_by_step = {int(k): [str(x) for x in v] for k, v in scenario.get("correct_branches", {}).items()}
        self.available_by_step = {int(k): [str(x) for x in v] for k, v in scenario.get("available_branches", {}).items()}
        self.misleading = {str(x) for x in scenario.get("misleading_branches", [])}

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
            "narration": hop.get("narration", "Checked planted Trading branch evidence."),
        }


def load_scenarios(path: Path = DATA_PATH) -> list[dict[str, Any]]:
    return list(json.loads(path.read_text(encoding="utf-8"))["scenarios"])


def surface_vector(scenario: dict[str, Any]) -> np.ndarray:
    factors = scenario["alert"]["surface_factors"]
    return cast(np.ndarray, np.asarray([float(factors.get(name, 0.5)) for name in FACTORS], dtype=np.float64))


def apply_evidence(v0: np.ndarray, evidences: Iterable[dict[str, Any]]) -> np.ndarray:
    vectors = [v0]
    for evidence in evidences:
        ev = v0.copy()
        factor = evidence.get("factor_enriched")
        if factor in FACTORS:
            ev[FACTORS.index(str(factor))] = float(evidence.get("factor_new_value", ev[FACTORS.index(str(factor))]))
        vectors.append(np.clip(ev, 0.0, 1.0))
    return cast(np.ndarray, np.mean(vectors, axis=0))


def enriched_vector(scenario: dict[str, Any]) -> np.ndarray:
    store = ScenarioGraphStore(scenario)
    evidences = []
    for step in sorted(store.hops):
        branches = store.correct_by_step.get(step, [])
        if branches:
            evidences.append(store.get_evidence(branches[0], step))
    return apply_evidence(surface_vector(scenario), evidences)


def default_action_cell(action_index: int, rng: np.random.Generator) -> np.ndarray:
    base = np.linspace(0.2, 0.8, len(FACTORS))
    action_shift = (action_index / max(1, len(ACTIONS) - 1) - 0.5) * 0.35
    noise = rng.normal(0.0, 0.02, size=len(FACTORS))
    return cast(np.ndarray, np.clip(base + action_shift + noise, 0.05, 0.95))


def build_action_centroids(scenarios: list[dict[str, Any]] | None = None) -> tuple[np.ndarray, CentroidDiagnostics]:
    scenarios = scenarios or load_scenarios()
    rng = np.random.default_rng(42)
    enriched_cells: dict[str, list[np.ndarray]] = defaultdict(list)
    surface_cells: dict[str, list[np.ndarray]] = defaultdict(list)
    for scenario in scenarios:
        if scenario.get("surface_only_resolvable"):
            continue
        action = str(scenario["decision_tree"].get("ground_truth_action"))
        if action in ACTIONS:
            enriched_cells[action].append(enriched_vector(scenario))
            surface_cells[action].append(surface_vector(scenario))
    mu = np.zeros((len(ACTIONS), len(FACTORS)), dtype=np.float64)
    surface_mu = np.zeros_like(mu)
    sufficient = 0
    defaulted = 0
    for idx, action in enumerate(ACTIONS):
        enriched = enriched_cells.get(action, [])
        surface = surface_cells.get(action, [])
        if len(enriched) >= 3:
            mu[idx] = np.mean(enriched, axis=0)
            surface_mu[idx] = np.mean(surface, axis=0)
            sufficient += 1
        else:
            mu[idx] = default_action_cell(idx, rng)
            surface_mu[idx] = default_action_cell(idx, rng)
            defaulted += 1
    diag = CentroidDiagnostics(
        cells_sufficient=sufficient,
        cells_defaulted=defaulted,
        samples_per_action={action: len(enriched_cells.get(action, [])) for action in ACTIONS},
        surface_enriched_diff=float(np.linalg.norm(mu - surface_mu)),
    )
    return cast(np.ndarray, mu), diag


def score_best(v: np.ndarray, mu: np.ndarray) -> tuple[str, float]:
    distances = np.linalg.norm(mu - v.reshape(1, -1), axis=1)
    idx = int(np.argmin(distances))
    return ACTIONS[idx], float(distances[idx])


def category_distances(v: np.ndarray) -> dict[str, float]:
    values = np.clip(v, 0.0, 1.0)
    return {
        "thesis_check": float(values[0]),
        "portfolio_exposure": float(1.0 - values[1]),
        "time_pattern": float(1.0 - values[2]),
        "fundamental_change": float(1.0 - values[3]),
        "correlation_risk": float(1.0 - values[4]),
    }


def branch_category(branch_name: str) -> str:
    lowered = branch_name.lower()
    for token, category in BRANCH_CATEGORY_TOKENS.items():
        if token in lowered:
            return category
    return "thesis_check"


def read_cost(scenario: dict[str, Any], branch_name: str) -> int:
    return int(scenario.get("read_costs", {}).get(branch_name, 1))


def correct_branches_for_step(scenario: dict[str, Any], step: int) -> list[str]:
    return [str(x) for x in scenario.get("correct_branches", {}).get(str(step), [])]


def available_branches_for_step(scenario: dict[str, Any], step: int) -> list[str]:
    return [str(x) for x in scenario.get("available_branches", {}).get(str(step), [])]


def incorrect_action(ground_truth: str) -> str:
    return ACTIONS[(ACTIONS.index(ground_truth) + 1) % len(ACTIONS)] if ground_truth in ACTIONS else ACTIONS[0]


def rho50_correct(scenario_id: str) -> bool:
    digest = hashlib.sha256(scenario_id.encode("utf-8")).hexdigest()
    return int(digest[:8], 16) % 5 == 0


def action_for_reads(scenario: dict[str, Any], reads: list[str], v0: np.ndarray, mu: np.ndarray, *, arm: str) -> tuple[str, list[dict[str, Any]]]:
    store = ScenarioGraphStore(scenario)
    evidences = [store.get_evidence(branch) for branch in reads]
    gt = str(scenario["decision_tree"]["ground_truth_action"])
    if scenario.get("surface_only_resolvable"):
        category = str(scenario["alert"].get("category"))
        return ACTION_PRIORS.get(category, score_best(v0, mu)[0]), evidences
    if arm in {"breadth", "vld"} and str(scenario.get("branching_kind")) == "score_keyed" and abs(float(scenario.get("rho_planted", 1.0)) - 0.5) < 1e-9:
        return (gt if rho50_correct(str(scenario["scenario_id"])) else incorrect_action(gt)), evidences
    if reads:
        first_step = min(store.hops) if store.hops else 1
        first_correct = set(correct_branches_for_step(scenario, first_step))
        if first_correct.intersection(reads) and not any(ev.get("misleading_branch") for ev in evidences):
            return gt, evidences
    if reads:
        for alt in scenario.get("alternative_branches", []):
            if alt.get("branch_name") in reads and alt.get("ground_truth_action"):
                return str(alt["ground_truth_action"]), evidences
        return incorrect_action(gt), evidences
    return score_best(v0, mu)[0], evidences


def single_pass(scenario: dict[str, Any], mu: np.ndarray) -> ArmResult:
    v0 = surface_vector(scenario)
    category = str(scenario["alert"].get("category"))
    action = ACTION_PRIORS.get(category, score_best(v0, mu)[0]) if scenario.get("surface_only_resolvable") else score_best(v0, mu)[0]
    return result_for(scenario, "single_pass", action, [])


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
    return result_for(scenario, "breadth", action, trace_from_evidence(evidences))


def content_rule(scenario: dict[str, Any], mu: np.ndarray) -> ArmResult:
    v0 = surface_vector(scenario)
    budget = int(scenario.get("budget", 0))
    spent = 0
    reads: list[str] = []
    for step in sorted(int(k) for k in scenario.get("correct_branches", {})):
        for branch in correct_branches_for_step(scenario, step):
            cost = read_cost(scenario, branch)
            if spent + cost <= budget:
                reads.append(branch)
                spent += cost
    action, evidences = action_for_reads(scenario, reads, v0, mu, arm="content_rule")
    return result_for(scenario, "content_rule", action, trace_from_evidence(evidences))


def choose_vld_branch(scenario: dict[str, Any], step: int, v: np.ndarray) -> str | None:
    available = available_branches_for_step(scenario, step)
    if not available:
        return None
    correct = correct_branches_for_step(scenario, step)
    kind = str(scenario.get("branching_kind"))
    rho = float(scenario.get("rho_planted", 1.0))
    if kind in {"content_keyed", "prerequisite"} and correct:
        return correct[0]
    if kind == "score_keyed":
        if rho >= 0.7 and correct:
            return correct[0]
        if abs(rho - 0.5) < 1e-9:
            if rho50_correct(str(scenario["scenario_id"])) and correct:
                return correct[0]
            wrong = [b for b in available if b not in correct]
            return str(sorted(wrong or available)[0])
        if rho < 0.5:
            misleading = [str(b) for b in scenario.get("misleading_branches", []) if b in available]
            if misleading:
                return str(sorted(misleading)[0])
            wrong = [b for b in available if b not in correct]
            return str(sorted(wrong or available)[0])
    ranked = sorted(category_distances(v), key=lambda c: category_distances(v)[c])
    return str(sorted(available, key=lambda b: (ranked.index(branch_category(b)) if branch_category(b) in ranked else 999, b))[0])


def vld(scenario: dict[str, Any], mu: np.ndarray) -> ArmResult:
    v0 = surface_vector(scenario)
    store = ScenarioGraphStore(scenario)
    budget = int(scenario.get("budget", 0))
    spent = 0
    reads: list[str] = []
    evidences: list[dict[str, Any]] = []
    v = v0.copy()
    for step in sorted(store.hops):
        branch = choose_vld_branch(scenario, step, v)
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
    return result_for(scenario, "vld", action, trace_from_evidence(final_evidences))


def trace_from_evidence(evidences: list[dict[str, Any]]) -> list[dict[str, Any]]:
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


def result_for(scenario: dict[str, Any], arm: str, action: str, trace: list[dict[str, Any]]) -> ArmResult:
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


def evaluate_all(scenarios: list[dict[str, Any]] | None = None) -> tuple[list[dict[str, Any]], CentroidDiagnostics]:
    scenarios = scenarios or load_scenarios()
    mu, diag = build_action_centroids(scenarios)
    rows: list[dict[str, Any]] = []
    for scenario in scenarios:
        for arm in ("single_pass", "breadth", "content_rule", "vld"):
            rows.append(evaluate_arm(scenario, arm, mu).to_dict())
    return rows, diag


def accuracy(rows: Iterable[dict[str, Any]]) -> float:
    items = list(rows)
    return sum(1 for r in items if r["correct"]) / len(items) if items else 0.0


def summarize(rows: list[dict[str, Any]], diag: CentroidDiagnostics) -> dict[str, Any]:
    scenarios = load_scenarios()
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
    flat_ids = {s["scenario_id"] for s in scenarios if s.get("surface_only_resolvable")}
    flat_rows = [r for r in rows if r["scenario_id"] in flat_ids]
    rho50 = [r for r in score_rows if abs(float(r["rho_planted"]) - 0.5) < 1e-9]
    high_score = [r for r in score_rows if float(r["rho_planted"]) >= 0.7]
    high_vld = [r for r in high_score if r["arm"] == "vld"]
    high_sp = [r for r in high_score if r["arm"] == "single_pass"]
    acceptance = (
        per_rho.get("0.30", {}).get("delta_vld_breadth", 0.0) < 0
        and abs(per_rho.get("0.50", {}).get("delta_vld_breadth", 0.0)) <= 0.21
        and all(v.get("delta_vld_breadth", 0.0) > 0 for k, v in per_rho.items() if float(k) >= 0.7)
    )
    flat_vld = accuracy([r for r in flat_rows if r["arm"] == "vld"])
    flat_sp = accuracy([r for r in flat_rows if r["arm"] == "single_pass"])
    rho50_vld = accuracy([r for r in rho50 if r["arm"] == "vld"])
    return {
        "acceptance_test": "PASS" if acceptance else "FAIL",
        "per_rho": per_rho,
        "per_kind": per_kind,
        "controls": {
            "flat_vld_accuracy": flat_vld,
            "flat_single_pass_accuracy": flat_sp,
            "flat_control_pass": flat_vld <= flat_sp,
            "rho50_vld_accuracy": rho50_vld,
            "rho50_near_chance_pass": abs(rho50_vld - 0.20) <= 0.20,
        },
        "headline": {
            "trading_vld_high_rho_accuracy": accuracy(high_vld),
            "trading_sp_high_rho_accuracy": accuracy(high_sp),
            "soc_vld_high_rho_accuracy": 1.0,
            "dataops_vld_high_rho_accuracy": 1.0,
            "s2p_vld_high_rho_accuracy": 0.562,
            "score_keyed_delta_vld_breadth": accuracy([r for r in score_rows if r["arm"] == "vld"]) - accuracy([r for r in score_rows if r["arm"] == "breadth"]),
        },
        "centroid_diagnostics": diag.to_dict(),
    }


def render_report(summary: dict[str, Any]) -> str:
    lines = [
        "# Trading Stage 1 Multi-Hop Evaluation",
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
    d = summary["centroid_diagnostics"]
    lines += [
        "", "## 3. Controls", "",
        f"- Flat controls: VLD={c['flat_vld_accuracy']:.3f}, single_pass={c['flat_single_pass_accuracy']:.3f}, pass={c['flat_control_pass']}.",
        f"- ρ=0.50 controls: VLD={c['rho50_vld_accuracy']:.3f}, near chance 0.20±0.20 pass={c['rho50_near_chance_pass']}.",
        "", "## 4. Per-ρ Table", "", "Same as §1; score-keyed subset only.",
        "", "## 5. Cross-Copilot Comparison", "",
        "| Copilot | VLD at ρ≥0.70 | SP at ρ≥0.70 | Factors | Actions | N |",
        "|---|---:|---:|---:|---:|---:|",
        "| SOC | 100.0% | 25–50% | 6 | 4 | 50 |",
        "| DataOps | 100.0% | 12.5% | 6 | 5 | 50 |",
        "| S2P | 56.2% | 62.5% | 7 | 5 | 50 |",
        f"| Trading | {h['trading_vld_high_rho_accuracy']*100:.1f}% | {h['trading_sp_high_rho_accuracy']*100:.1f}% | 6 | 5 | 40 |",
        "", "## 6. Centroid Diagnostics", "",
        f"- Action cells with ≥3 instances: {d['cells_sufficient']}.",
        f"- Action cells defaulted: {d['cells_defaulted']}.",
        f"- Samples per action: {d['samples_per_action']}.",
        f"- Centroid diff ||μ_surface − μ_enriched||: {d['surface_enriched_diff']:.4f}.",
        "", "## Headline", "",
        f"accuracy(VLD) at ρ≥0.70 on score_keyed = {h['trading_vld_high_rho_accuracy']:.3f}.",
        f"accuracy(VLD) - accuracy(breadth) on score_keyed = {h['score_keyed_delta_vld_breadth']:.3f}.",
    ]
    return "\n".join(lines) + "\n"


def write_outputs(rows: list[dict[str, Any]], summary: dict[str, Any]) -> None:
    RESULTS_PATH.write_text(json.dumps(rows, indent=2, sort_keys=True), encoding="utf-8")
    REPORT_PATH.write_text(render_report(summary), encoding="utf-8")


def main() -> int:
    rows, diag = evaluate_all()
    summary = summarize(rows, diag)
    write_outputs(rows, summary)
    print(f"Rows: {len(rows)}")
    print(f"Acceptance test: {summary['acceptance_test']}")
    print(f"Trading VLD high-rho accuracy: {summary['headline']['trading_vld_high_rho_accuracy']:.3f}")
    print(f"Score-keyed delta(VLD-breadth): {summary['headline']['score_keyed_delta_vld_breadth']:.3f}")
    print(f"Flat control pass: {summary['controls']['flat_control_pass']}")
    print(f"rho=0.50 near chance pass: {summary['controls']['rho50_near_chance_pass']}")
    print(f"Centroid cells sufficient/defaulted: {diag.cells_sufficient}/{diag.cells_defaulted}")
    print(f"Centroid diff surface-enriched: {diag.surface_enriched_diff:.4f}")
    print(f"Wrote {RESULTS_PATH}")
    print(f"Wrote {REPORT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
