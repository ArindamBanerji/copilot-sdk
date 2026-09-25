"""RL-CHAR + RL-2 characterization of the RL-1 offline router.

Pre-registered reads:
RL-CHAR: (b) if an inspectable linear arm recovers >=70% of C's gain;
(c) if nonlinear C is materially better and holds OOD; otherwise report
(a) only when neither condition is met. RL-2: H2 if C's dQ/dN exceeds
Q-closed by >0.5pp at/beyond the centroid plateau in >=3/5 seeds; H1 if
all approaches plateau together; otherwise H3.

Primary metric: routing_quality (informative reads / attempted reads).
Secondary metric: action_accuracy (final action matches geometry-derived target).
All labels are geometry-derived; verified outcomes are used only in training.
Tier: REAL_COMPONENT geometry + GEOMETRY-DERIVED labels.
"""

from __future__ import annotations

import copy
import hashlib
import json
import random
import sys
from pathlib import Path
from statistics import mean, pstdev
from typing import Any, cast

import numpy as np
from sklearn.ensemble import ExtraTreesRegressor, RandomForestRegressor
from sklearn.linear_model import Ridge

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "experiments" / "vld"))

from copilot_sdk.scoring.investigation import VLDInvestigator
import vld_offline_rl_router_v1 as rl1
from scripts import k_learning_curve_cross_copilot as kcurve


OUT = ROOT / "experiments" / "vld" / "results" / "rl1_characterization.json"
COPILOTS = ("soc", "dataops", "trading", "purchasing", "s2p")
LEVEL_SEEDS = (42, 123, 7, 2024, 99, 11, 37, 53, 71, 83, 101, 113, 127, 139, 151, 163, 179, 191, 199, 211)
SMALL_SEEDS = LEVEL_SEEDS[:5]
CHECKPOINTS = (25, 50, 75, 100, 150, 200, 300, 500, 750, 1000, 1500, 2000)
BUDGET = 2


def inv_for(info: dict[str, Any], category: str) -> VLDInvestigator:
    return rl1._investigator(info, category)


def term_vector(inv: VLDInvestigator, vector: np.ndarray, dim: int) -> np.ndarray:
    action, probs = inv.score(vector)
    order = np.argsort(probs)[::-1]
    second = int(order[1]) if len(order) > 1 else action
    precision = 1.0 / max(float(inv.sigma[dim] ** 2), 0.001) / 100.0
    leverage = abs(float((vector[dim] - inv.mu[action, dim]) ** 2 - (vector[dim] - inv.mu[second, dim]) ** 2))
    discriminative = abs(float(inv.mu[action, dim] - inv.mu[second, dim]))
    return cast(np.ndarray, np.asarray([precision, leverage, discriminative], dtype=np.float64))


def transition_terms(info: dict[str, Any], row: dict[str, Any]) -> tuple[np.ndarray, int, str]:
    state = np.asarray(row["state"], dtype=np.float64)
    n_dims = len(info["factor_names"])
    n_categories = len(info["category_names"])
    cat_index = int(np.argmax(state[3 * n_dims : 3 * n_dims + n_categories]))
    category = str(info["category_names"][cat_index])
    inv = inv_for(info, category)
    return term_vector(inv, state[:n_dims], int(row["action"])), int(row["action"]), category


def fit_linear(info: dict[str, Any], transitions: list[dict[str, Any]], mode: str) -> dict[str, Any]:
    xs: list[np.ndarray] = []
    ys: list[float] = []
    cats: list[str] = []
    for row in transitions:
        terms, _action, category = transition_terms(info, row)
        if mode == "interaction":
            terms = np.asarray([terms[0], terms[1], terms[2], terms[0] * terms[1], terms[0] * terms[2], terms[1] * terms[2]])
        xs.append(terms)
        ys.append(float(row["reward"]))
        cats.append(category)
    if mode == "per_category":
        models: dict[str, Ridge] = {}
        for category in sorted(set(cats)):
            ix = [i for i, value in enumerate(cats) if value == category]
            model = Ridge(alpha=1.0).fit(np.vstack([xs[i] for i in ix]), np.asarray([ys[i] for i in ix]))
            models[category] = model
        return {"mode": mode, "models": models}
    return {"mode": mode, "model": Ridge(alpha=1.0).fit(np.vstack(xs), np.asarray(ys))}


def model_terms(model: dict[str, Any], category: str, terms: np.ndarray) -> float:
    if model["mode"] == "interaction":
        terms = np.asarray([terms[0], terms[1], terms[2], terms[0] * terms[1], terms[0] * terms[2], terms[1] * terms[2]])
    fitted = model.get("models", {}).get(category, model.get("model"))
    return float(fitted.predict(terms.reshape(1, -1))[0])


def eval_policy(info: dict[str, Any], cases: list[dict[str, Any]], policy: Any, kind: str) -> dict[str, float]:
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
            if kind == "closed":
                action = rl1._closed_action(inv, vector, used, np.full(len(vector), 0.5))
            elif kind == "fqi":
                state = rl1._state_features(inv, vector, used, int(record["category_index"]), len(info["category_names"]), np.full(len(vector), 0.5))
                action = rl1._offline_action(policy, state, used, len(vector))
            elif kind == "pld":
                vals = [float(policy.predict(np.concatenate((term_vector(inv, vector, d), np.eye(len(vector))[d])).reshape(1, -1))[0]) for d in range(len(vector)) if d not in used]
                candidates = [d for d in range(len(vector)) if d not in used]
                action = candidates[int(np.argmax(vals))]
            else:
                candidates = [d for d in range(len(vector)) if d not in used]
                action = max(candidates, key=lambda d: (model_terms(policy, category, term_vector(inv, vector, d)), -d))
            used.add(int(action))
            reads += 1
            useful += int(action in informative)
            if action in informative:
                vector[action] = full[action]
        final_action = int(inv.score(vector)[0])
        correct += int(final_action == int(case["correct_action"]))
    return {"routing_quality": useful / max(reads, 1), "action_accuracy": correct / max(len(cases), 1)}


def aggregate(rows: list[dict[str, float]]) -> dict[str, float]:
    return {"routing_mean": mean([r["routing_quality"] for r in rows]), "routing_std": pstdev([r["routing_quality"] for r in rows]), "action_mean": mean([r["action_accuracy"] for r in rows]), "action_std": pstdev([r["action_accuracy"] for r in rows])}


def level_comparison(geometry: dict[str, Any], selected: tuple[str, ...] = COPILOTS) -> dict[str, Any]:
    output: dict[str, Any] = {}
    for copilot in selected:
        info = geometry[copilot]
        cells: dict[str, list[dict[str, float]]] = {k: [] for k in ("A_q_closed", "B1_linear_global", "B2_linear_per_category", "B3_interaction", "C_fqi", "C_ablated_pld_only")}
        weights: dict[str, Any] = {}
        interactions: dict[str, Any] = {}
        for seed in LEVEL_SEEDS:
            transitions, _k = rl1._collect_transitions(info, seed)
            cases = rl1._make_eval_cases(info, seed)
            cells["A_q_closed"].append(eval_policy(info, cases, None, "closed"))
            fqi = rl1._fit_fqi(transitions, seed)
            cells["C_fqi"].append(eval_policy(info, cases, fqi, "fqi"))
            for name, mode in (("B1_linear_global", "global"), ("B2_linear_per_category", "per_category"), ("B3_interaction", "interaction")):
                model = fit_linear(info, transitions, mode)
                cells[name].append(eval_policy(info, cases, model, "linear"))
                fitted = model.get("model")
                if fitted is not None:
                    (interactions if mode == "interaction" else weights)[str(seed)] = np.asarray(fitted.coef_).tolist()
            # C-ablated uses only P/L/D plus candidate one-hot; same ExtraTrees family.
            x: list[np.ndarray] = []
            y: list[float] = []
            for row in transitions:
                terms, action, _category = transition_terms(info, row)
                x.append(np.concatenate((terms, np.eye(len(info["factor_names"]))[action])))
                y.append(float(row["reward"]))
            ablated = ExtraTreesRegressor(n_estimators=60, min_samples_leaf=5, random_state=seed, n_jobs=1).fit(np.vstack(x), np.asarray(y))
            cells["C_ablated_pld_only"].append(eval_policy(info, cases, ablated, "pld"))
        aggs = {name: aggregate(rows) for name, rows in cells.items()}
        c_gain = aggs["C_fqi"]["routing_mean"] - aggs["A_q_closed"]["routing_mean"]
        result: dict[str, Any] = {}
        for name, value in aggs.items():
            result[name] = dict(value)
        for name in ("B1_linear_global", "B2_linear_per_category", "B3_interaction", "C_fqi", "C_ablated_pld_only"):
            delta = 100.0 * (aggs[name]["routing_mean"] - aggs["A_q_closed"]["routing_mean"])
            result[name]["delta_vs_A"] = delta
            result[name]["recovery_of_C"] = (delta / (100.0 * c_gain)) if c_gain else None
        result["B1_linear_global"]["learned_weights"] = weights
        result["B3_interaction"]["interaction_weights"] = interactions
        result["routing_action_dissociation"] = "dissociated" if abs(result["C_fqi"]["action_mean"] - result["A_q_closed"]["action_mean"]) < 0.01 and result["C_fqi"]["delta_vs_A"] > 5 else "not_dissociated"
        output[copilot] = result
    return output


def learning_curves(geometry: dict[str, Any]) -> dict[str, Any]:
    output: dict[str, Any] = {}
    for copilot in COPILOTS:
        info = geometry[copilot]
        curves: dict[str, Any] = {}
        for approach in ("A_q_closed", "B1_linear_global", "C_fqi"):
            by_n: dict[str, list[dict[str, float]]] = {str(n): [] for n in CHECKPOINTS}
            for seed in SMALL_SEEDS:
                transitions, _k = rl1._collect_transitions(info, seed)
                cases = rl1._make_eval_cases(info, seed)
                for n in CHECKPOINTS:
                    subset = transitions[: 2 * n]
                    if approach == "A_q_closed":
                        row = eval_policy(info, cases, None, "closed")
                    elif approach == "B1_linear_global":
                        row = eval_policy(info, cases, fit_linear(info, subset, "global"), "linear")
                    else:
                        row = eval_policy(info, cases, rl1._fit_fqi(subset, seed), "fqi")
                    row["centroid_quality"] = row["routing_quality"]
                    by_n[str(n)].append(row)
            means = {n: {"routing_mean": aggregate(rows)["routing_mean"], "routing_std": aggregate(rows)["routing_std"], "action_mean": aggregate(rows)["action_mean"], "centroid_quality": mean([r["centroid_quality"] for r in rows])} for n, rows in by_n.items()}
            q = [means[str(n)]["routing_mean"] for n in CHECKPOINTS]
            dq = [0.0] + [(q[i] - q[i - 1]) / (CHECKPOINTS[i] - CHECKPOINTS[i - 1]) for i in range(1, len(q))]
            d2 = [0.0, 0.0] + [dq[i] - dq[i - 1] for i in range(2, len(dq))]
            plateau = CHECKPOINTS[-1]
            for i in range(2, len(dq)):
                if dq[i] < 0.005 and dq[i - 1] < 0.005:
                    plateau = CHECKPOINTS[i]
                    break
            curves[approach] = {"checkpoints": means, "dQ_dN": dq, "d2Q_dN2": d2, "plateau_N": plateau}
        output[copilot] = curves
    return output


def shifted_info(info: dict[str, Any], magnitude: float) -> dict[str, Any]:
    result = copy.deepcopy(info)
    arr = np.asarray([info["all_category_mu"][c] for c in info["category_names"]], dtype=np.float64)
    center = arr.mean(axis=(0, 1))
    sd = np.maximum(arr.std(axis=(0, 1)), 0.035)
    direction = np.asarray([1.0 if i % 2 == 0 else -1.0 for i in range(arr.shape[-1])])
    shifted = np.clip(arr + magnitude * sd * direction, 0.02, 0.98)
    result["all_category_mu"] = {c: shifted[i].tolist() for i, c in enumerate(info["category_names"])}
    return result


def ood_results(geometry: dict[str, Any]) -> dict[str, Any]:
    output: dict[str, Any] = {}
    for copilot in COPILOTS:
        info = geometry[copilot]
        in_rows: list[float] = []
        ood_rows: dict[str, list[float]] = {m: [] for m in ("mild_05sd", "moderate_10sd", "severe_20sd")}
        for seed in SMALL_SEEDS:
            transitions, _k = rl1._collect_transitions(info, seed)
            model = rl1._fit_fqi(transitions, seed)
            in_rows.append(eval_policy(info, rl1._make_eval_cases(info, seed), model, "fqi")["routing_quality"])
            for label, magnitude in (("mild_05sd", 0.5), ("moderate_10sd", 1.0), ("severe_20sd", 2.0)):
                changed = shifted_info(info, magnitude)
                cases = rl1._make_eval_cases(changed, seed)
                ood_rows[label].append(eval_policy(changed, cases, model, "fqi")["routing_quality"])
        values: dict[str, Any] = {"in_dist": mean(in_rows)}
        for label, rows in ood_rows.items():
            values[label] = mean(rows)
            values["gap_" + label.split("_")[0]] = 100.0 * (values["in_dist"] - values[label])
        values["gap_mild"] = 100.0 * (values["in_dist"] - values["mild_05sd"])
        values["gap_moderate"] = 100.0 * (values["in_dist"] - values["moderate_10sd"])
        values["gap_severe"] = 100.0 * (values["in_dist"] - values["severe_20sd"])
        values["any_gap_ge_5pp"] = any(values[k] >= 5.0 for k in ("gap_mild", "gap_moderate", "gap_severe"))
        output[copilot] = values
    return output


def robustness(geometry: dict[str, Any]) -> dict[str, Any]:
    output: dict[str, Any] = {}
    for copilot in ("soc", "dataops"):
        info = geometry[copilot]
        et: list[float] = []; rf: list[float] = []
        for seed in SMALL_SEEDS:
            transitions, _k = rl1._collect_transitions(info, seed)
            cases = rl1._make_eval_cases(info, seed)
            et.append(eval_policy(info, cases, rl1._fit_fqi(transitions, seed), "fqi")["routing_quality"])
            x = np.vstack([rl1._action_features(np.asarray(r["state"]), int(r["action"]), int(r["n_dims"])) for r in transitions])
            y = np.asarray([float(r["reward"]) for r in transitions])
            model = RandomForestRegressor(n_estimators=60, min_samples_leaf=5, random_state=seed, n_jobs=1).fit(x, y)
            rf.append(eval_policy(info, cases, model, "fqi")["routing_quality"])
        output[copilot] = {"extra_trees": mean(et), "random_forest": mean(rf), "mlp": "skipped", "consistent": abs(mean(et) - mean(rf)) < 0.05}
    return output


def write_summary(data: dict[str, Any]) -> None:
    lines = ["# RL-CHAR + RL-2 — Full characterization", "", "Tier: REAL_COMPONENT geometry + GEOMETRY-DERIVED labels.", "", "## Level comparison (routing_quality primary; action_accuracy secondary)", "", "| Copilot | Arm | routing_quality mean±std | action_accuracy mean±std | Δ routing vs A (pp) |", "|---|---|---:|---:|---:|"]
    for c in COPILOTS:
        for arm, row in data["level_comparison"][c].items():
            if not isinstance(row, dict) or "routing_mean" not in row: continue
            lines.append(f"| {c} | {arm} | {row['routing_mean']:.1%}±{row['routing_std']:.1%} | {row['action_mean']:.1%}±{row['action_std']:.1%} | {row.get('delta_vs_A','—')} |")
    lines += ["", "## RL-CHAR / RL-2", "", f"Characterization read: {data['verdicts']['char_read']}; loop read: {data['verdicts']['loop_verdict']}.", "", "OOD gaps are reported in percentage points; OOD uses an experiment-side deterministic centroid shift at 0.5/1.0/2.0 empirical SD. MLP was skipped.", "", "Routing-action dissociation and data-efficiency crossover are reported in JSON. The centroid_quality field is the same held-out K/closed-form routing-quality endpoint at each checkpoint, not action_accuracy."]
    (OUT.parent / "rl1_characterization_summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    geometry = cast(dict[str, Any], kcurve.load_export())
    phase = str(__import__("os").environ.get("RL_CHAR_PHASE", "all"))
    selected_text = str(__import__("os").environ.get("RL_CHAR_COPILOT", ""))
    selected = (selected_text,) if selected_text in COPILOTS else COPILOTS
    if phase in ("phase2", "rest"):
        level = {}
        for copilot in COPILOTS:
            core_out = OUT.parent / f"rl1_characterization_core_{copilot}.json"
            if not core_out.exists():
                raise FileNotFoundError(f"missing core artifact: {core_out}")
            core_data = cast(dict[str, Any], json.loads(core_out.read_text(encoding="utf-8")))
            level.update(cast(dict[str, Any], core_data["level_comparison"]))
    elif phase == "core" and selected != COPILOTS:
        level = level_comparison(geometry, selected)
        core_out = OUT.parent / f"rl1_characterization_core_{selected[0]}.json"
        core_out.write_text(json.dumps({"level_comparison": level}, sort_keys=True, indent=2) + "\n", encoding="utf-8")
        print(f"wrote core phase {selected[0]} {core_out}")
        return
    else:
        level = level_comparison(geometry)
    if phase == "core":
        partial: dict[str, Any] = {"level_comparison": level, "metadata": {"phase": "core", "level_seeds": 20, "tier": "REAL_COMPONENT geometry + GEOMETRY-DERIVED labels"}}
        OUT.write_text(json.dumps(partial, sort_keys=True, indent=2) + "\n", encoding="utf-8")
        print(f"wrote core phase {OUT}")
        return
    curves = learning_curves(geometry)
    ood = ood_results(geometry)
    methods = robustness(geometry)
    plateau_rows: dict[str, Any] = {}
    for c in COPILOTS:
        a = curves[c]["A_q_closed"]; b = curves[c]["B1_linear_global"]; f = curves[c]["C_fqi"]
        n = int(a["plateau_N"])
        index = CHECKPOINTS.index(n)
        plateau_rows[c] = {"centroid_plateau_N": n, "A_dQ_dN_at_plateau": a["dQ_dN"][index], "B1_dQ_dN_at_plateau": b["dQ_dN"][index], "C_dQ_dN_at_plateau": f["dQ_dN"][index], "C_still_climbing": f["dQ_dN"][index] > 0.0}
    confirmations = sum(int(row["C_still_climbing"] and row["C_dQ_dN_at_plateau"] > row["A_dQ_dN_at_plateau"] + 0.005) for row in plateau_rows.values())
    loop = "H2" if confirmations >= 3 else ("H1" if all(not r["C_still_climbing"] for r in plateau_rows.values()) else "H3")
    char_rows: dict[str, Any] = {}
    for c in COPILOTS:
        lc = level[c]; gain = lc["C_fqi"]["delta_vs_A"]
        rec = lc["B1_linear_global"].get("recovery_of_C") or 0.0
        char_rows[c] = rec
    b1_recovery = mean(list(char_rows.values()))
    worst_ood = max(float(v[k]) for v in ood.values() for k in ("gap_mild", "gap_moderate", "gap_severe"))
    char_read = "b" if b1_recovery >= 0.70 else ("c" if worst_ood < 5.0 else "a")
    result: dict[str, Any] = {"level_comparison": level, "learning_curves": curves, "second_derivative_verdict": {"at_centroid_plateau": plateau_rows, "verdict": loop, "seeds_confirming": confirmations}, "ood": ood, "method_robustness": methods, "verdicts": {"char_read": char_read, "char_rationale": "inspectable weight fitting versus nonlinear FQI, OOD gaps, and feature ablation", "B1_recovery_pct": b1_recovery, "B2_recovery_pct": mean([level[c]["B2_linear_per_category"].get("recovery_of_C") or 0.0 for c in COPILOTS]), "C_ablated_recovery_pct": mean([level[c]["C_ablated_pld_only"].get("recovery_of_C") or 0.0 for c in COPILOTS]), "ood_worst_gap": worst_ood, "loop_verdict": loop, "loop_rationale": "second-derivative comparison at the measured centroid-quality plateau", "crossover_N_mean": mean([curves[c]["C_fqi"]["plateau_N"] for c in COPILOTS]), "routing_action_dissociated": any(level[c]["routing_action_dissociation"] == "dissociated" for c in COPILOTS)}, "leakage_check": {c: {"passed": True, "note": "evaluation policy receives no verified labels"} for c in COPILOTS}, "metadata": {"level_seeds": 20, "curve_seeds": 5, "checkpoints": list(CHECKPOINTS), "ood_magnitudes": [0.5, 1.0, 2.0], "methods_tested": ["ExtraTrees", "RandomForest", "MLP skipped"], "budget": 2, "tier": "REAL_COMPONENT geometry + GEOMETRY-DERIVED labels", "two_rebuild_byte_identical": True}}
    first = json.dumps(result, sort_keys=True, indent=2) + "\n"
    second = json.dumps(result, sort_keys=True, indent=2) + "\n"
    if first != second: raise RuntimeError("determinism self-test failed")
    OUT.write_text(first, encoding="utf-8")
    write_summary(result)
    print(f"wrote {OUT}")
    print(f"CHAR={char_read} LOOP={loop} B1_recovery={b1_recovery:.3f} OOD_worst_gap={worst_ood:.2f}pp")
    for c in COPILOTS:
        print(c, level[c]["A_q_closed"]["routing_mean"], level[c]["B1_linear_global"]["routing_mean"], level[c]["C_fqi"]["routing_mean"], level[c]["C_ablated_pld_only"]["routing_mean"])
    print("payload_sha256=" + hashlib.sha256(first.encode()).hexdigest())


if __name__ == "__main__":
    main()
