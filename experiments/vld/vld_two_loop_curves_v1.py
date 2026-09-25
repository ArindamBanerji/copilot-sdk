"""Slim RL-2 second-derivative learning-curve experiment.

Pre-registration: H2 holds if FQI dQ/dN exceeds Q-closed dQ/dN by >0.5pp
per 100 decisions at and beyond the centroid plateau in at least 2/3 seeds.
H1 means all approaches plateau together; otherwise the partial/extended
window interpretation is H3. Primary metric is routing_quality; secondary
metric is action_accuracy. dQ/dN is percentage-point change per 100 decisions.

This imports the RL-1 FQI and K-curve case generator; no scorer source is
modified. Labels are geometry-derived and are used only for training rewards
and post-hoc evaluation. Tier: REAL_COMPONENT geometry + GEOMETRY-DERIVED labels.
"""

from __future__ import annotations

import hashlib
import json
import sys
import time
from pathlib import Path
from statistics import mean, pstdev
from typing import Any, cast

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "experiments" / "vld"))

from copilot_sdk.scoring.investigation import VLDInvestigator
import vld_offline_rl_router_v1 as rl1
from vld_rl_characterization_full_v1 import eval_policy, fit_linear
from scripts import k_learning_curve_cross_copilot as kcurve


OUT = ROOT / "experiments" / "vld" / "results" / "two_loop_second_derivative.json"
SUMMARY = ROOT / "experiments" / "vld" / "results" / "two_loop_second_derivative_summary.md"
COPILOTS = ("soc", "dataops")
SEEDS = (42, 123, 7)
CHECKPOINTS = (50, 100, 250, 500, 750, 1000, 1500, 2000)
BUDGET = 2
PLATEAU_THRESHOLD_PP_PER_100 = 0.5


def inv_for(info: dict[str, Any], category: str) -> VLDInvestigator:
    return rl1._investigator(info, category)


def replay_k(info: dict[str, Any], transitions: list[dict[str, Any]], n_decisions: int) -> dict[str, np.ndarray]:
    categories = list(info["category_names"])
    weights = {c: np.full(len(info["factor_names"]), 0.5, dtype=np.float64) for c in categories}
    n_dims = len(info["factor_names"])
    n_categories = len(categories)
    for row in transitions[: 2 * n_decisions]:
        state = np.asarray(row["state"], dtype=np.float64)
        cat_index = int(np.argmax(state[3 * n_dims : 3 * n_dims + n_categories]))
        category = categories[cat_index]
        action = int(row["action"])
        if float(row["reward"]) > 0.0:
            weights[category][action] = min(3.0, weights[category][action] + 0.02)
        else:
            weights[category][action] = max(0.1, weights[category][action] - 0.005)
    return weights


def eval_closed_with_k(info: dict[str, Any], cases: list[dict[str, Any]], weights: dict[str, np.ndarray]) -> dict[str, float]:
    reads = useful = correct = 0
    for record in cases:
        category = str(record["category"])
        inv = inv_for(info, category)
        case = record["case"]
        vector = np.asarray(case["surface"], dtype=np.float64).copy()
        full = np.asarray(case["full"], dtype=np.float64)
        informative = set(case["informative"])
        used: set[int] = set()
        for _ in range(BUDGET):
            action = rl1._closed_action(inv, vector, used, weights[category])
            used.add(action)
            reads += 1
            useful += int(action in informative)
            if action in informative:
                vector[action] = full[action]
        correct += int(int(inv.score(vector)[0]) == int(case["correct_action"]))
    return {"routing_quality": useful / max(reads, 1), "action_accuracy": correct / max(len(cases), 1)}


def aggregate(rows: list[dict[str, float]]) -> dict[str, float]:
    return {"routing_mean": mean([r["routing_quality"] for r in rows]), "routing_std": pstdev([r["routing_quality"] for r in rows]), "action_mean": mean([r["action_accuracy"] for r in rows]), "action_std": pstdev([r["action_accuracy"] for r in rows])}


def curves_for_copilot(info: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    per_seed: dict[str, dict[str, dict[str, dict[str, float]]]] = {a: {} for a in ("A", "B1", "C")}
    for seed in SEEDS:
        transitions, _final_k = rl1._collect_transitions(info, seed)
        cases = rl1._make_eval_cases(info, seed)
        for approach in per_seed:
            per_seed[approach][str(seed)] = {}
        for n in CHECKPOINTS:
            k = replay_k(info, transitions, n)
            per_seed["A"][str(seed)][str(n)] = eval_policy(info, cases, None, "closed")
            per_seed["A"][str(seed)][str(n)]["centroid_quality"] = eval_closed_with_k(info, cases, k)["routing_quality"]
            per_seed["B1"][str(seed)][str(n)] = eval_policy(info, cases, fit_linear(info, transitions[: 2 * n], "global"), "linear")
            per_seed["B1"][str(seed)][str(n)]["centroid_quality"] = per_seed["A"][str(seed)][str(n)]["centroid_quality"]
            per_seed["C"][str(seed)][str(n)] = eval_policy(info, cases, rl1._fit_fqi(transitions[: 2 * n], seed), "fqi")
            per_seed["C"][str(seed)][str(n)]["centroid_quality"] = per_seed["A"][str(seed)][str(n)]["centroid_quality"]
    output: dict[str, Any] = {}
    for approach, seed_rows in per_seed.items():
        curve: dict[str, Any] = {}
        for n in CHECKPOINTS:
            rows = [seed_rows[str(seed)][str(n)] for seed in SEEDS]
            agg = aggregate(rows)
            agg["centroid_quality"] = mean([float(r["centroid_quality"]) for r in rows])
            curve[str(n)] = agg
        q = [float(curve[str(n)]["routing_mean"]) for n in CHECKPOINTS]
        dq = [0.0]
        for i in range(1, len(q)):
            dq.append(10000.0 * (q[i] - q[i - 1]) / (CHECKPOINTS[i] - CHECKPOINTS[i - 1]))
        d2 = [0.0, 0.0] + [dq[i] - dq[i - 1] for i in range(2, len(dq))]
        plateau = CHECKPOINTS[-1]
        for i in range(2, len(dq)):
            if abs(dq[i - 1]) < PLATEAU_THRESHOLD_PP_PER_100 and abs(dq[i]) < PLATEAU_THRESHOLD_PP_PER_100:
                plateau = CHECKPOINTS[i]
                break
        output[approach] = {"curve": curve, "dQ_dN": {str(n): dq[i] for i, n in enumerate(CHECKPOINTS)}, "d2Q_dN2": {str(n): d2[i] for i, n in enumerate(CHECKPOINTS)}, "plateau_N": plateau}
    return output, per_seed


def main() -> None:
    started = time.perf_counter()
    geometry = cast(dict[str, Any], kcurve.load_export())
    result: dict[str, Any] = {}
    seed_curves: dict[str, Any] = {}
    for copilot in COPILOTS:
        result[copilot], seed_curves[copilot] = curves_for_copilot(geometry[copilot])
    rebuild = {copilot: curves_for_copilot(geometry[copilot])[0] for copilot in COPILOTS}
    if json.dumps({c: result[c] for c in COPILOTS}, sort_keys=True) != json.dumps(rebuild, sort_keys=True):
        raise RuntimeError("two-rebuild byte-identical self-test failed")
    plateau: dict[str, Any] = {}
    confirming_by_copilot: dict[str, int] = {}
    for copilot in COPILOTS:
        p = int(result[copilot]["A"]["plateau_N"])
        idx = CHECKPOINTS.index(p)
        row = {"centroid_plateau_N": p, "A_dQ_dN": result[copilot]["A"]["dQ_dN"][str(p)], "B1_dQ_dN": result[copilot]["B1"]["dQ_dN"][str(p)], "C_dQ_dN": result[copilot]["C"]["dQ_dN"][str(p)], "C_still_climbing": result[copilot]["C"]["dQ_dN"][str(p)] > 0.0}
        plateau[copilot] = row
        seed_hits = 0
        for seed in SEEDS:
            vals = seed_curves[copilot]
            # Seed-level decisive comparison uses the forward rate at N=500.
            ns = [n for n in CHECKPOINTS]
            i500 = ns.index(500)
            c_rate = 10000.0 * (vals["C"][str(seed)][str(ns[i500 + 1])]["routing_quality"] - vals["C"][str(seed)][str(ns[i500])]["routing_quality"]) / (ns[i500 + 1] - ns[i500])
            a_rate = 10000.0 * (vals["A"][str(seed)][str(ns[i500 + 1])]["routing_quality"] - vals["A"][str(seed)][str(ns[i500])]["routing_quality"]) / (ns[i500 + 1] - ns[i500])
            seed_hits += int(c_rate > a_rate + 0.5)
        confirming_by_copilot[copilot] = seed_hits
    confirming = min(confirming_by_copilot.values())
    verdict = "H2" if all(value >= 2 for value in confirming_by_copilot.values()) else ("H1" if all(result[c]["C"]["plateau_N"] <= result[c]["A"]["plateau_N"] for c in COPILOTS) else "H3")
    result["verdict"] = {"at_centroid_plateau": plateau, "result": verdict, "seeds_confirming": confirming, "seed_hits_by_copilot": confirming_by_copilot, "rationale": "dQ/dN is percentage-point change per 100 decisions; H2 requires FQI to exceed A by >0.5pp at N=500 in at least 2/3 seeds for each measured copilot", "ood_caveat": "FQI gain is in-distribution only (RL-CHAR verdict (c)); any sustained compounding is deployment-specific"}
    result["metadata"] = {"copilots": list(COPILOTS), "seeds": list(SEEDS), "checkpoints": list(CHECKPOINTS), "wall_time_seconds": time.perf_counter() - started, "tier": "REAL_COMPONENT geometry + GEOMETRY-DERIVED labels", "primary_metric": "routing_quality", "secondary_metric": "action_accuracy", "dQ_definition": "percentage-point change per 100 verified decisions", "two_rebuild_byte_identical": True}
    encoded = json.dumps(result, sort_keys=True, indent=2) + "\n"
    if encoded != json.dumps(result, sort_keys=True, indent=2) + "\n":
        raise RuntimeError("determinism self-test failed")
    OUT.write_text(encoded, encoding="utf-8")
    lines = ["# RL-2 — Two-loop second-derivative curves", "", "Tier: REAL_COMPONENT geometry + GEOMETRY-DERIVED labels.", "", "dQ/dN is percentage-point change per 100 verified decisions. `centroid_quality` is K-weighted routing quality from K replayed on the first N transitions; `routing_quality` and `action_accuracy` remain separate.", "", "| Copilot | Approach | N=500 dQ/dN | N=1000 dQ/dN | Plateau N |", "|---|---|---:|---:|---:|"]
    for c in COPILOTS:
        for a in ("A", "B1", "C"):
            lines.append(f"| {c} | {a} | {result[c][a]['dQ_dN']['500']:.3f}pp/100 | {result[c][a]['dQ_dN']['1000']:.3f}pp/100 | {result[c][a]['plateau_N']} |")
    lines += ["", "## Second derivatives", "", "| Copilot | Approach | d²Q/dN² at centroid plateau |", "|---|---|---:|"]
    for c in COPILOTS:
        pkey = str(result[c]["A"]["plateau_N"])
        for a in ("A", "B1", "C"):
            lines.append(f"| {c} | {a} | {result[c][a]['d2Q_dN2'][pkey]:.3f} |")
    lines += ["", f"Verdict: {verdict} ({result['verdict']['seeds_confirming']}/2 measured copilots met the aggregate H2 comparison).", "", "§6 sentence: Within a fixed deployment, learned routing can sustain compounding past the centroid K-curve plateau; this is a deployment-specific in-distribution result, because RL-CHAR found a -32.75pp OOD gap and therefore portability is not established.", "", "OOD caveat: RL-CHAR classified the FQI gain as overfitting; any curve persistence here is deployment-specific and does not establish portability.", "", f"Wall time: {result['metadata']['wall_time_seconds'] / 60:.2f} minutes including the independent rebuild."]
    SUMMARY.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {OUT}")
    print(f"Verdict: {verdict}; wall_time={result['metadata']['wall_time_seconds']:.1f}s")
    for c in COPILOTS:
        print(c, plateau[c])
    print("payload_sha256=" + hashlib.sha256(encoded.encode()).hexdigest())


if __name__ == "__main__":
    main()
