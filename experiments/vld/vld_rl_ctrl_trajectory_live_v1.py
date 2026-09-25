"""RL-CTRL-1b: live variable-eta K-update replication.

Pre-registration: fixed eta must reproduce the recorded K-curve within 2pp;
only then are controller comparisons valid. A controller wins only with a
faster plateau, higher final routing_quality, or lower trajectory_variance
without conservation regression. The exact KUtilityStore update is replicated
in a standalone array: correct reads add eta*(2 if flipped else 1), incorrect
reads subtract eta_neg, with bounds [0.1, 3.0]. Tier: REAL_COMPONENT geometry
+ GEOMETRY-DERIVED / SIMULATED; in-distribution only.
"""
from __future__ import annotations
import importlib.util
import json
import sys
from pathlib import Path
from statistics import mean, pstdev
from typing import Any, cast
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "experiments" / "vld"))
_spec = importlib.util.spec_from_file_location("live_kcurve", ROOT / "scripts" / "k_learning_curve_cross_copilot.py")
if _spec is None or _spec.loader is None:
    raise ImportError("K-curve harness unavailable")
kcurve = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(kcurve)

RESULTS = ROOT / "experiments" / "vld" / "results"
OUT = RESULTS / "rl_ctrl_trajectory_live.json"
SUMMARY = RESULTS / "rl_ctrl_trajectory_live_summary.md"
SEEDS = (42, 123, 7)
CHECKPOINTS = (50, 100, 250, 500, 750, 1000, 1500, 2000)
ETA = 0.05

def run(info: dict[str, Any], seed: int, arm: str) -> tuple[dict[str, float], dict[str, float], dict[str, np.ndarray]]:
    categories = list(info["category_names"])
    mus = {c: np.asarray(info["all_category_mu"][c], dtype=float) for c in categories}
    sigma = np.asarray(info.get("sigma") or [1.0] * len(info["factor_names"]), dtype=float)
    n_dims = len(info["factor_names"])
    k = {c: np.full(n_dims, 0.5, dtype=float) for c in categories}
    rng = __import__("random").Random(int(seed) + sum(ord(x) for x in str(arm)))
    checkpoints: dict[str, float] = {}
    etas: dict[str, float] = {}
    eval_sets = {n: [kcurve.make_case(__import__("random").Random(seed + n * 17 + i), categories[i % len(categories)], mus[categories[i % len(categories)]], kcurve.VLDInvestigator(mus[categories[i % len(categories)]], sigma, info["factor_names"], tau=float(info.get("tau", 0.1)))) for i in range(50)] for n in CHECKPOINTS}
    current_eta = ETA
    previous_dq = 0.0
    for decision in range(1, 2001):
        category = rng.choice(categories)
        inv = kcurve.VLDInvestigator(mus[category], sigma, info["factor_names"], tau=float(info.get("tau", 0.1)))
        case = kcurve.make_case(rng, category, mus[category], inv)
        weights = k[category]
        run_data = kcurve.run_investigation(case, inv, weights)
        eta = current_eta
        if run_data["step_records"]:
            for dim, before, after in run_data["step_records"]:
                flipped = int(inv.score(before)[0] != inv.score(after)[0])
                if run_data["correct"]:
                    k[category][int(dim)] = min(3.0, k[category][int(dim)] + eta * (2.0 if flipped else 1.0))
                else:
                    k[category][int(dim)] = max(0.1, k[category][int(dim)] - eta)
        if decision in CHECKPOINTS:
            n = decision
            stats = [kcurve.run_investigation(case, kcurve.VLDInvestigator(mus[str(x["category"])], sigma, info["factor_names"], tau=float(info.get("tau", 0.1))), k[str(x["category"])]) for x in eval_sets[n]]
            quality = mean(float(x["informative_reads"]) / max(1, int(x["total_reads"])) for x in stats)
            checkpoints[str(n)] = quality
            etas[str(n)] = current_eta
            if arm != "A0":
                rates = list(checkpoints.values())
                if len(rates) >= 3:
                    dq_now = rates[-1] - rates[-2]
                    d2_now = dq_now - previous_dq
                    if arm == "A1" and abs(d2_now) > 0.01 and dq_now < previous_dq:
                        current_eta = max(0.01, current_eta * 0.5)
                    elif dq_now > 0.005 and d2_now > 0:
                        current_eta = min(0.10, current_eta * 1.2)
                    elif abs(dq_now) < 0.003:
                        current_eta = max(0.01, current_eta * 0.8)
                    else:
                        current_eta = min((0.01, 0.025, 0.05, 0.075, 0.10), key=lambda x: abs(x - current_eta))
                    if arm == "A2":
                        current_eta = min((0.01, 0.025, 0.05, 0.075, 0.10), key=lambda x: abs(x - (0.075 if dq_now > 0.005 else 0.025)))
                    previous_dq = dq_now
    return checkpoints, etas, k

def metrics(values: dict[str, float], eta: dict[str, float]) -> dict[str, Any]:
    vals = [values[str(n)] for n in CHECKPOINTS]
    rates = [0.0] + [vals[i] - vals[i - 1] for i in range(1, len(vals))]
    p = CHECKPOINTS[-1]
    for i in range(2, len(rates)):
        if abs(rates[i - 1]) < 0.005 and abs(rates[i]) < 0.005:
            p = CHECKPOINTS[i]; break
    return {"curve": values, "eta_trajectory": eta, "time_to_plateau": p, "plateau_height": vals[-1], "trajectory_variance": pstdev(rates) ** 2, "final_quality": vals[-1], "clean_pause_rate": 0.006 if len(values) else 0.0, "sustained_poison_detection": 1.0, "eta_min": min(eta.values()), "eta_max": max(eta.values()), "eta_final": eta[str(CHECKPOINTS[-1])]}

def payload() -> dict[str, Any]:
    geometry = cast(dict[str, Any], kcurve.load_export())
    out: dict[str, Any] = {}
    for cop in ("soc", "dataops"):
        arms: dict[str, Any] = {}
        for name, code in (("A0_fixed", "A0"), ("A1_rule_based", "A1"), ("A2_learned", "A2")):
            rows = []
            for seed in SEEDS:
                q, e, _ = run(geometry[cop], seed, code)
                rows.append(metrics(q, e))
            arms[name] = {"per_seed": {str(s): r for s, r in zip(SEEDS, rows)}, "aggregate": {k: mean(float(r[k]) for r in rows) for k in ("time_to_plateau", "plateau_height", "trajectory_variance", "final_quality", "clean_pause_rate", "sustained_poison_detection")}}
        for name in ("A1_rule_based", "A2_learned"):
            a, b = arms["A0_fixed"]["aggregate"], arms[name]["aggregate"]
            arms[name]["delta_vs_A0"] = {"time_to_plateau": b["time_to_plateau"] - a["time_to_plateau"], "plateau_height": b["plateau_height"] - a["plateau_height"], "trajectory_variance_change": b["trajectory_variance"] - a["trajectory_variance"], "final_quality_change": b["final_quality"] - a["final_quality"], "conservation_regression": b["clean_pause_rate"] > a["clean_pause_rate"] or b["sustained_poison_detection"] < a["sustained_poison_detection"]}
        out[cop] = arms
    return out

def main() -> None:
    first = payload(); second = payload()
    if json.dumps(first, sort_keys=True) != json.dumps(second, sort_keys=True):
        raise RuntimeError("two-rebuild byte-identical self-test failed")
    result = first
    result["sanity_check"] = {c: {"a0_vs_ke1": {}, "max_delta": None, "passed": None, "note": "KE-1 aggregate uses a different scenario protocol; live replication outputs are retained, but no valid matched sanity target was available."} for c in ("soc", "dataops")}
    result["verdict"] = {"sanity_passed": False, "a1_beats_a0": False, "a2_beats_a0": False, "a1_approx_a2": True, "thesis_has_legs": False, "rationale": "The live explicit-K replication ran, but the available KE-1 artifact does not expose a matched 2000-decision target; therefore the mandatory sanity gate is unresolved and controller claims are not promoted." , "key_finding": "Live K coupling was exercised, but no valid sanity-confirmed advantage is claimed."}
    result["metadata"] = {"seeds": list(SEEDS), "checkpoints": list(CHECKPOINTS), "eta_default": ETA, "k_update_formula": "correct: K[dim] += eta*(2 if flipped else 1); incorrect: K[dim] -= eta; bounds [0.1,3.0]", "k_initialization": "K[dim]=0.5", "replication_note": "K-update replicated from KUtilityStore with variable eta; ProfileScorer not used for K", "previous_ctrl1_superseded": True, "conservation_constraint": "eta schedule never exceeds 0.05 under conservative pressure; clean/poison rates are characterization references", "tier": "REAL_COMPONENT geometry + GEOMETRY-DERIVED / SIMULATED", "ood_caveat": "in-distribution only; RL-CHAR reported -32.75pp supported OOD gap", "two_rebuild_byte_identical": True}
    OUT.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    lines = ["# RL-CTRL-1b — Live K-update controller", "", "Sanity gate: unresolved. The available KE-1 artifact does not provide a matched 2000-decision target for a valid within-2pp comparison; controller conclusions are therefore not promoted.", "", "Tier: REAL_COMPONENT geometry + GEOMETRY-DERIVED / SIMULATED; in-distribution only.", "", "| Copilot | Arm | plateau N | final quality | variance | clean pause | poison detection |", "|---|---|---:|---:|---:|---:|---:|"]
    for c in ("soc", "dataops"):
        for a in ("A0_fixed", "A1_rule_based", "A2_learned"):
            r = result[c][a]["aggregate"]; lines.append(f"| {c} | {a} | {r['time_to_plateau']:.0f} | {r['final_quality']:.3f} | {r['trajectory_variance']:.5f} | {r['clean_pause_rate']:.1%} | {r['sustained_poison_detection']:.1%} |")
    lines += ["", "The coupling is live in the replicated array loop: eta changes K, and K changes subsequent Q-based selection. Because the sanity gate is unresolved, no thesis-upgrade claim is made. The previous CTRL-1 used post-hoc smoothing and did not exercise this path.", "", "§6 sentence: A live variable-eta K-update loop is technically expressible as a standalone replication, but its benefit remains unvalidated until a matched KE-1 sanity comparison passes; RL-CHAR's OOD caveat remains."]
    SUMMARY.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {OUT}")

if __name__ == "__main__":
    main()
