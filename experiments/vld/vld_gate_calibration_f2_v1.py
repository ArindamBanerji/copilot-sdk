from __future__ import annotations

"""F-2 preregistration: action_accuracy on geometry-derived labels.

Decision rule: a margin is acceptable only if every copilot's mean clean
PAUSE-decision rate is <5% and Purchasing plus SOC retain slow-drift and
25%-poison detection with lag <=1.5x their global-0.75 lag. A calibrated
floor is each domain's pooled steady-state clean action_accuracy minus m.
The run reuses C5's deterministic scenario generator and K-learning helpers;
both conservation checks are replicated here, with Check A's floor variable.
Each seed's scenario stream is rebuilt twice and canonical bytes compared.
Tier: REAL_COMPONENT geometry + SIMULATED streams/degradation.
"""

import hashlib
import json
import random
import sys
from pathlib import Path
from statistics import mean, pstdev
from typing import Any

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
GAE_ROOT = ROOT.parent / "graph-attention-engine-v50"
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(GAE_ROOT))

from experiments.vld import vld_conservation_lag_c5_v1 as c5
from copilot_sdk.scoring.scorer import _conservation_dispersion
from gae.calibration import compute_theta_min

SEEDS = (42, 123, 7)
COPILOTS = ("dataops", "trading", "purchasing", "soc", "s2p")
MARGINS = (0.05, 0.10, 0.15)
DIAG_N = 500
BASELINE_START = 200
ONSET = 501
RUN_N = 900
WINDOW = 100
GLOBAL_FLOOR = 0.75
TIER = "REAL_COMPONENT geometry + SIMULATED streams/degradation"
RESULT_PATH = ROOT / "experiments/vld/results/gate_calibration_f2.json"
SUMMARY_PATH = ROOT / "experiments/vld/results/gate_calibration_f2_summary.md"
R = dict[str, Any]


def canonical(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n").encode()


def check_b_status(records: list[R], categories: int) -> str:
    verified = len(records)
    if verified == 0 or verified < c5.MIN_VERIFIED_FOR_GATE:
        return "ALLOW"
    correct = sum(c5._is_correct(row) for row in records)
    q = correct / verified
    alpha = c5._category_coverage(records, categories)
    theta_min = compute_theta_min(alpha, verified)
    dispersion = _conservation_dispersion(None, verified_decisions=records)
    effective_q = q
    if dispersion is not None and float(dispersion.get("inflation", 0.0)) > 1.3:
        effective_q = max(0.0, q - float(dispersion.get("effective_se", 0.0)))
    if theta_min is not None and alpha * effective_q * verified < theta_min:
        return "PAUSE"
    return "ALLOW"


def check_b_sequence(records: list[R], categories: int) -> list[str]:
    seen: list[R] = []
    result: list[str] = []
    for record in records:
        seen.append(record)
        result.append(check_b_status(seen, categories))
    return result


def make_stream(cop: str, geometry: R, seed: int, scenario: str,
                poison: float | None = None, n: int = RUN_N) -> list[R]:
    categories = list(geometry["category_names"])
    names = list(geometry["factor_names"])
    sigma = np.asarray(geometry["sigma"], dtype=np.float64)
    mus = {k: np.asarray(v, dtype=np.float64) for k, v in geometry["all_category_mu"].items()}
    rng = random.Random(seed)
    store = c5.KUtilityStore(c5.SQLiteDecisionStore(), d=len(names))
    pre = c5._category_distribution_for_break(categories, True)
    post = c5._category_distribution_for_break(categories, False)
    direction = np.zeros(len(names), dtype=np.float64)
    drift_ready = False
    records: list[R] = []
    for decision in range(1, n + 1):
        weights = (pre if decision < ONSET else post) if scenario == "fast_break" else None
        category = rng.choice(categories) if weights is None else rng.choices(categories, weights=weights, k=1)[0]
        inv = c5.VLDInvestigator(mus[category], sigma, names, tau=float(geometry["tau"]))
        offset = None
        if scenario == "slow_drift" and decision >= ONSET:
            if not drift_ready:
                raw = np.asarray([rng.gauss(0, 1) for _ in names], dtype=np.float64)
                norm = float(np.linalg.norm(raw))
                if norm <= 0:
                    raw[0] = 1.0
                    norm = 1.0
                direction = raw / norm
                drift_ready = True
            progress = min(1.0, (decision - ONSET + 1) / c5.SLOW_DRIFT_WINDOW)
            offset = np.clip(direction * (c5.SLOW_DRIFT_MAX_STD * progress), -0.20, 0.20)
        case = c5._make_case(rng, category, mus[category], inv, offset)
        run = c5._run_investigation(case, inv, names, store.get_weights(category))
        true_correct = bool(run["correct"])
        observed = true_correct
        if scenario == "poisoning_eps25" and decision >= ONSET and poison is not None and rng.random() < poison:
            observed = not observed
        run["correct"] = observed
        c5._reward_learning_store(store, category, names, inv, run, set(case["informative"]))
        records.append({"decision": decision, "category": category,
                        "is_correct": observed, "outcome": "confirmed" if observed else "rejected",
                        "true_correct": true_correct, "degradation": scenario if decision >= ONSET else "baseline"})
    store.conn.close()
    return records


def evaluate(records: list[R], categories: int, floor: float, start: int,
             stop_early: bool, check_b: list[str] | None = None) -> R:
    seen: list[R] = []
    rows: list[R] = []
    pause_at: int | None = None
    for record in records:
        seen.append(record)
        recent = c5._recent_quality(seen, WINDOW)
        check_a = recent is not None and recent[0] >= WINDOW and recent[1] < floor
        if check_a:
            status, reason = "PAUSE", "recent_accuracy_floor"
        else:
            b_status = check_b[len(rows)] if check_b is not None else check_b_status(seen, categories)
            status, reason = ("PAUSE", "gae_theta") if b_status == "PAUSE" else ("ALLOW", "none")
        rows.append({"decision": record["decision"],
                     "action_accuracy": float(record["is_correct"]),
                     "recent_window_accuracy": None if recent is None else recent[1],
                     "gate_status": status, "gate_reason": reason,
                     "degradation_state": record["degradation"]})
        if int(record["decision"]) >= start and status == "PAUSE" and pause_at is None:
            pause_at = int(record["decision"])
            if stop_early:
                break
    return {"rows": rows, "gate_pause_at": pause_at,
            "false_pauses": sum(r["gate_status"] == "PAUSE" for r in rows),
            "total_decisions": len(rows),
            "false_pause_rate": (sum(r["gate_status"] == "PAUSE" for r in rows) / len(rows)) if rows else 0.0}


def mean_sd(values: list[float]) -> tuple[float, float]:
    return mean(values), pstdev(values)


def main() -> None:
    geometry = c5._load_export()
    streams: dict[str, dict[str, list[R]]] = {cop: {} for cop in COPILOTS}
    for cop in COPILOTS:
        for seed in SEEDS:
            first = make_stream(cop, geometry[cop], seed, "clean_control", n=DIAG_N)
            second = make_stream(cop, geometry[cop], seed, "clean_control", n=DIAG_N)
            assert canonical(first) == canonical(second), f"clean rebuild mismatch: {cop}/{seed}"
            streams[cop][str(seed)] = first

    clean_check_b = {cop: {str(seed): check_b_sequence(streams[cop][str(seed)], len(geometry[cop]["category_names"]))
                           for seed in SEEDS} for cop in COPILOTS}

    diagnosis: R = {}
    baseline: dict[str, float] = {}
    calibration: R = {}
    for cop in COPILOTS:
        per_seed: R = {}
        stable_values: list[float] = []
        for seed in SEEDS:
            records = streams[cop][str(seed)]
            trace = evaluate(records, len(geometry[cop]["category_names"]), GLOBAL_FLOOR, 1, False,
                             clean_check_b[cop][str(seed)])
            steady = [r["recent_window_accuracy"] for r in trace["rows"]
                      if r["decision"] >= BASELINE_START and r["recent_window_accuracy"] is not None]
            stable_values.extend(float(v) for v in steady)
            base_mean, base_sd = mean_sd([float(v) for v in steady])
            per_seed[str(seed)] = {"clean_base_accuracy_mean": base_mean,
                "clean_base_accuracy_std": base_sd, "vs_075_floor": base_mean-GLOBAL_FLOOR,
                "false_pause_rate": trace["false_pause_rate"], "total_decisions": trace["total_decisions"],
                "false_pauses": trace["false_pauses"], "tier": TIER,
                "metric": "action_accuracy", "per_decision": trace["rows"]}
        pooled, pooled_sd = mean_sd(stable_values)
        baseline[cop] = max(0.0, pooled)
        rates = [float(per_seed[str(seed)]["false_pause_rate"]) for seed in SEEDS]
        diagnosis[cop] = {"per_seed": per_seed,
            "aggregate": {"base_accuracy_mean": pooled, "base_accuracy_std": pooled_sd,
                          "false_pause_rate_mean": mean(rates), "tier": TIER,
                          "metric": "action_accuracy"}}
        calibration[cop] = {}
        for margin in MARGINS:
            floor = max(0.0, baseline[cop]-margin)
            rows: R = {}
            for seed in SEEDS:
                row = evaluate(streams[cop][str(seed)], len(geometry[cop]["category_names"]), floor, 1, False,
                               clean_check_b[cop][str(seed)])
                rows[str(seed)] = {"false_pause_rate": row["false_pause_rate"],
                                   "false_pauses": row["false_pauses"], "total_decisions": row["total_decisions"]}
            calibration[cop][f"{margin:.2f}"] = {"per_domain_floor": floor, "per_seed": rows,
                "aggregate": {"false_pause_rate_mean": mean([float(x["false_pause_rate"]) for x in rows.values()]),
                              "tier": TIER, "metric": "action_accuracy"}}

    # The degradation streams are generated twice and compared before scoring each threshold.
    preservation: R = {"purchasing": {}, "soc": {}}
    candidates = [m for m in MARGINS if calibration["purchasing"][f"{m:.2f}"]["aggregate"]["false_pause_rate_mean"] < .05]
    for cop in ("purchasing", "soc"):
        for margin in candidates:
            floor = max(0.0, baseline[cop]-margin)
            cell: R = {}
            for scenario, poison, name in (("slow_drift", None, "slow_drift"),
                                            ("poisoning_eps25", .25, "poison_25")):
                details: R = {}
                for seed in SEEDS:
                    first = make_stream(cop, geometry[cop], seed, scenario, poison, RUN_N)
                    second = make_stream(cop, geometry[cop], seed, scenario, poison, RUN_N)
                    assert canonical(first) == canonical(second), f"degradation rebuild mismatch: {cop}/{scenario}/{seed}"
                    check_b = check_b_sequence(first, len(geometry[cop]["category_names"]))
                    global_result = evaluate(first, len(geometry[cop]["category_names"]), GLOBAL_FLOOR, ONSET, True, check_b)
                    calibrated = evaluate(first, len(geometry[cop]["category_names"]), floor, ONSET, True, check_b)
                    glag = None if global_result["gate_pause_at"] is None else global_result["gate_pause_at"]-ONSET
                    plag = None if calibrated["gate_pause_at"] is None else calibrated["gate_pause_at"]-ONSET
                    ratio = None if glag is None or glag <= 0 or plag is None else plag/glag
                    details[str(seed)] = {"lag_global": glag if glag is not None else "missed",
                        "lag_per_domain": plag if plag is not None else "missed", "ratio": ratio,
                        "preserved": bool(plag is not None and glag is not None and ratio is not None and ratio <= 1.5),
                        "tier": TIER, "metric": "action_accuracy"}
                cell[name] = {"per_seed": details}
            cell["floor"] = floor
            preservation[cop][f"{margin:.2f}"] = cell

    acceptable: list[float] = []
    for margin in MARGINS:
        all_low = all(float(calibration[c][f"{margin:.2f}"]["aggregate"]["false_pause_rate_mean"]) < .05 for c in COPILOTS)
        preserve = True
        if margin in candidates:
            for cop in ("purchasing", "soc"):
                for scenario in ("slow_drift", "poison_25"):
                    preserve = preserve and all(bool(r["preserved"]) for r in preservation[cop][f"{margin:.2f}"][scenario]["per_seed"].values())
        else:
            preserve = False
        if all_low and preserve:
            acceptable.append(margin)
    best = min(acceptable) if acceptable else None
    result = {"diagnosis": diagnosis, "calibration": calibration,
        "detection_preservation": preservation,
        "recommendation": {"best_margin": best,
            "rationale": ("Smallest swept margin meets <5% mean clean PAUSE rate for every copilot and preserves all tested Purchase/SOC detection lags within 1.5x." if best is not None else "No swept margin satisfies both the all-copilot <5% clean PAUSE-rate requirement and the pre-registered detection-preservation rule."),
            "all_copilots_below_5pct": best is not None,
            "detection_preserved": best is not None},
        "metadata": {"seeds": list(SEEDS), "pre_registered_rule": "All copilot mean clean PAUSE-decision rates <5%; Purchasing and SOC slow-drift and poison-25 lag <=1.5x global-floor lag.",
            "gate_source": "scorer.py:2198, _conservation_pause()", "global_threshold": GLOBAL_FLOOR,
            "global_window": WINDOW, "clean_decisions": DIAG_N, "tier": TIER,
            "metric": "action_accuracy", "determinism_per_seed": "two fresh scenario rebuilds byte-identical"}}
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_bytes(canonical(result))
    write_summary(result)
    print(json.dumps(result["recommendation"], sort_keys=True))


def write_summary(result: R) -> None:
    lines = ["# F-2: Purchasing conservation-gate calibration", "",
        f"Tier: {TIER}. Gate metric: action_accuracy (geometry-derived outcome correctness).",
        "Pre-registered acceptance: every copilot clean PAUSE-decision rate <5%, while Purchasing and SOC retain slow-drift and 25%-poison detection within 1.5x global-floor lag.", "",
        "## Diagnosis", "", "| Copilot | Clean base action_accuracy | Δ from 0.75 | Clean PAUSE rate |", "|---|---:|---:|---:|"]
    for cop in COPILOTS:
        a = result["diagnosis"][cop]["aggregate"]
        lines.append(f"| {cop} | {a['base_accuracy_mean']:.3f} ± {a['base_accuracy_std']:.3f} | {a['base_accuracy_mean']-.75:+.3f} | {a['false_pause_rate_mean']:.1%} |")
    lines += ["", "## Clean PAUSE rate by margin", "", "| Copilot | m=.05 | m=.10 | m=.15 |", "|---|---:|---:|---:|"]
    for cop in COPILOTS:
        vals = [result["calibration"][cop][f"{m:.2f}"]["aggregate"]["false_pause_rate_mean"] for m in MARGINS]
        lines.append(f"| {cop} | " + " | ".join(f"{v:.1%}" for v in vals) + " |")
    lines += ["", "## Detection preservation", "", "| Copilot | Margin | Scenario | Global lag mean | Calibrated lag mean | Seeds preserved |", "|---|---:|---|---:|---:|---:|"]
    for cop in ("purchasing", "soc"):
        for margin, cell in result["detection_preservation"][cop].items():
            for scenario in ("slow_drift", "poison_25"):
                vals = list(cell[scenario]["per_seed"].values())
                gl = [float(r["lag_global"]) for r in vals if isinstance(r["lag_global"], (int, float))]
                pl = [float(r["lag_per_domain"]) for r in vals if isinstance(r["lag_per_domain"], (int, float))]
                count = sum(bool(r["preserved"]) for r in vals)
                global_text = f"{mean(gl):.1f}" if gl else "missed"
                calibrated_text = f"{mean(pl):.1f}" if pl else "missed"
                lines.append(f"| {cop} | {margin} | {scenario} | {global_text} | {calibrated_text} | {count}/3 |")
    rec = result["recommendation"]
    lines += ["", "## Recommendation and paper sentence", "", rec["rationale"], "",
        (f'"The gate requires per-domain calibration; a per-domain floor at margin {rec["best_margin"]} yields below-5% mean clean PAUSE-decision rates across the tested copilots while preserving measured detection within the preregistered 1.5× lag bound."' if rec["best_margin"] is not None else '"A per-domain floor may reduce clean-stream pauses, but none of the tested margins simultaneously met the all-copilot <5% false-pause and detection-preservation criteria; calibration remains unresolved."'),
        "", "The reported PAUSE rate counts PAUSE decisions, not unique streams. F-2 uses a 500-decision clean diagnostic; C5's cited Purchasing 34.78% PAUSE-decision rate used 900 decisions, so these rates are not directly interchangeable. A lag of 0 means the first recorded PAUSE was at onset (decision 501); it does not by itself establish degradation-specific detection. Any Check B pauses remain active under calibration and are reported in per-decision JSON as `gae_theta`.", ""]
    SUMMARY_PATH.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
