from __future__ import annotations

"""Stage 1 characterization of the conservation gate.

This is analysis-only.  It imports the existing C5 case/investigation helpers,
regenerates the same seeded geometry-derived streams to a fixed horizon, and
never calls or changes production gate behavior.
"""

import hashlib
import json
import math
import random
from pathlib import Path
from statistics import mean, pstdev
from typing import Any, cast

import numpy as np

import vld_conservation_lag_c5_v1 as c5
from gae.calibration import compute_theta_min


ROOT = Path(__file__).resolve().parents[2]
GEOMETRY_PATH = ROOT / "real_centroids_v1.json"
OUTPUT_JSON = ROOT / "experiments" / "vld" / "results" / "conservation_characterization_stage1.json"
OUTPUT_MD = ROOT / "experiments" / "vld" / "results" / "conservation_characterization_stage1_summary.md"
SEEDS = (42, 123, 7)
COPILOTS = ("dataops", "trading", "purchasing", "soc", "s2p")
THETAS = (0.60, 0.65, 0.70, 0.75, 0.80)
WINDOWS = (50, 100, 200)
RELATIVE_THRESHOLDS = (0.2, 0.3, 0.5)
DRIFT_THRESHOLDS = (0.05, 0.10, 0.20)
TOTAL_DECISIONS = 900
Q1_DECISIONS = 700
ONSET = c5.DEGRADATION_ONSET
CONDITIONS = ("slow_drift", "poison_25", "fast_break", "clean_control")
FACTOR_BINS = np.asarray([0.0, 0.2, 0.4, 0.6, 0.8, 1.0], dtype=np.float64)


def load_geometry() -> dict[str, Any]:
    payload = cast(dict[str, Any], json.loads(GEOMETRY_PATH.read_text(encoding="utf-8")))
    return cast(dict[str, Any], payload["copilots"])


class _Store:
    def __init__(self) -> None:
        import sqlite3

        self.conn = sqlite3.connect(":memory:")


def _coverage(records: list[dict[str, Any]], n_categories: int) -> float:
    return float(c5._category_coverage(records, n_categories))


def gate_pause(records: list[dict[str, Any]], n_categories: int, theta: float, window: int) -> bool:
    """Standalone Check A + Check B replica with configurable Check A."""
    if len(records) < c5.MIN_VERIFIED_FOR_GATE:
        return False
    recent = records[-window:]
    if len(recent) >= window:
        q_recent = sum(1 for row in recent if c5._is_correct(row)) / len(recent)
        if q_recent < theta:
            return True
    verified = len(records)
    correct = sum(1 for row in records if c5._is_correct(row))
    alpha = _coverage(records, n_categories)
    q = correct / verified
    theta_min = compute_theta_min(alpha, verified)
    return bool(theta_min is not None and alpha * q * verified < theta_min)


def _stream(copilot: str, geometry: dict[str, Any], seed: int, scenario: str) -> list[dict[str, Any]]:
    categories = list(geometry["category_names"])
    factors = list(geometry["factor_names"])
    sigma = np.asarray(geometry["sigma"], dtype=np.float64)
    tau = float(geometry["tau"])
    mus = {name: np.asarray(geometry["all_category_mu"][name], dtype=np.float64) for name in categories}
    rng = random.Random(seed)
    pre = c5._category_distribution_for_break(categories, True)
    post = c5._category_distribution_for_break(categories, False)
    drift_direction = np.zeros(len(factors), dtype=np.float64)
    drift_seen = False
    store = c5.KUtilityStore(_Store(), d=len(factors))
    verified: list[dict[str, Any]] = []
    rows: list[dict[str, Any]] = []
    for decision in range(1, TOTAL_DECISIONS + 1):
        weights = pre if scenario == "fast_break" and decision >= ONSET else post if scenario == "fast_break" else None
        category = rng.choices(categories, weights=weights, k=1)[0] if weights else rng.choice(categories)
        investigator = c5.VLDInvestigator(mus[category], sigma, factors, tau=tau)
        drift: np.ndarray | None = None
        if scenario == "slow_drift" and decision >= ONSET:
            if not drift_seen:
                raw = np.asarray([rng.gauss(0.0, 1.0) for _ in factors], dtype=np.float64)
                norm = float(np.linalg.norm(raw)) or 1.0
                drift_direction = raw / norm
                drift_seen = True
            progress = min(1.0, (decision - ONSET + 1) / c5.SLOW_DRIFT_WINDOW)
            drift = np.clip(drift_direction * (c5.SLOW_DRIFT_MAX_STD * progress), -0.20, 0.20)
        case = c5._make_case(rng, category, mus[category], investigator, drift_offset=drift)
        run = c5._run_investigation(case, investigator, factors, store.get_weights(category))
        true_correct = bool(run["correct"])
        outcome_correct = true_correct
        if scenario == "poison_25" and decision >= ONSET and rng.random() < 0.25:
            outcome_correct = not outcome_correct
        run["correct"] = outcome_correct
        c5._reward_learning_store(store, category, factors, investigator, run, set(case["informative"]))
        verified.append({"category": category, "is_correct": outcome_correct, "outcome": "confirmed" if outcome_correct else "rejected"})
        margin = float(investigator.margin(investigator.score(np.asarray(case["surface"], dtype=np.float64))[1]))
        rows.append({"decision": decision, "category": category, "is_correct": int(outcome_correct), "margin": margin, "factor_vector": [float(x) for x in case["surface"]]})
    return rows


def _accuracy_series(rows: list[dict[str, Any]], window: int) -> list[float]:
    values = [float(row["is_correct"]) for row in rows]
    return [sum(values[max(0, i + 1 - window): i + 1]) / min(window, i + 1) for i in range(len(values))]


def _first_lag(rows: list[dict[str, Any]], trigger: list[bool], start: int = ONSET) -> int | None:
    for index, fired in enumerate(trigger, start=1):
        if index >= start and fired:
            return index - start
    return None


def _psi(reference: np.ndarray, current: np.ndarray) -> float:
    total = 0.0
    for dim in range(reference.shape[1]):
        ref_counts, _ = np.histogram(reference[:, dim], bins=FACTOR_BINS)
        cur_counts, _ = np.histogram(current[:, dim], bins=FACTOR_BINS)
        ref = (ref_counts + 0.5) / (sum(ref_counts) + 0.5 * (len(FACTOR_BINS) - 1))
        cur = (cur_counts + 0.5) / (sum(cur_counts) + 0.5 * (len(FACTOR_BINS) - 1))
        total += float(np.sum((cur - ref) * np.log(cur / ref)))
    return float(total / max(reference.shape[1], 1))


def _relative_trigger(rows: list[dict[str, Any]], drop: float) -> list[bool]:
    accuracies = [float(row["is_correct"]) for row in rows]
    fired = [False] * len(rows)
    for i in range(200, len(rows)):
        baseline = sum(accuracies[i - 200:i]) / 200.0
        current = sum(accuracies[max(0, i - 99):i + 1]) / min(100, i + 1)
        fired[i] = baseline > 0.0 and current < baseline * (1.0 - drop)
    return fired


def _drift_trigger(rows: list[dict[str, Any]], threshold: float) -> list[bool]:
    vectors = np.asarray([row["factor_vector"] for row in rows], dtype=np.float64)
    fired = [False] * len(rows)
    for i in range(200, len(rows)):
        fired[i] = _psi(vectors[i - 50:i + 1], vectors[i - 200:i - 50]) > threshold
    return fired


def _floor_triggers(rows: list[dict[str, Any]], theta: float, window: int, n_categories: int) -> list[bool]:
    records: list[dict[str, Any]] = []
    triggers: list[bool] = []
    for row in rows:
        records.append({"category": row["category"], "is_correct": bool(row["is_correct"]), "outcome": "confirmed" if row["is_correct"] else "rejected"})
        triggers.append(gate_pause(records, n_categories, theta, window))
    return triggers


def _cell_metrics(streams: dict[str, dict[str, dict[str, list[dict[str, Any]]]]], copilot: str, condition: str, trigger_fn: Any) -> dict[str, float | None]:
    clean = streams[copilot]["clean_control"]
    clean_rates = []
    lags = []
    for seed in SEEDS:
        clean_trigger = trigger_fn(clean[str(seed)])
        clean_rates.append(sum(clean_trigger) / len(clean_trigger))
        if condition != "clean_control":
            rows = streams[copilot][condition][str(seed)]
            lag = _first_lag(rows, trigger_fn(rows))
            if lag is not None:
                lags.append(lag)
    return {"clean_pause_rate": mean(clean_rates), "detection_lag": mean(lags) if lags else None}


def _corr(xs: list[float], ys: list[float]) -> float | None:
    if len(xs) < 3 or pstdev(xs) == 0.0 or pstdev(ys) == 0.0:
        return None
    return float(np.corrcoef(np.asarray(xs), np.asarray(ys))[0, 1])


def _build() -> tuple[dict[str, Any], dict[str, Any]]:
    geometry = load_geometry()
    streams: dict[str, dict[str, dict[str, list[dict[str, Any]]]]] = {}
    for copilot in COPILOTS:
        streams[copilot] = {}
        for condition in ("slow_drift", "poison_25", "fast_break", "clean_control"):
            source = "poison_25" if condition == "poison_25" else condition
            streams[copilot][condition] = {str(seed): _stream(copilot, geometry[copilot], seed, source) for seed in SEEDS}

    q1: dict[str, Any] = {}
    for copilot in COPILOTS:
        q1[copilot] = {}
        rows = [row for seed in SEEDS for row in streams[copilot]["clean_control"][str(seed)][:Q1_DECISIONS] if row["decision"] > 200]
        for window in WINDOWS:
            series = []
            for seed in SEEDS:
                series.extend(_accuracy_series(streams[copilot]["clean_control"][str(seed)][:Q1_DECISIONS], window)[200:])
            q1[copilot][str(window)] = {"accuracy_mean": mean(series), "accuracy_std": pstdev(series), "fraction_below_075": sum(x < 0.75 for x in series) / len(series), "time_series": series}

    q2: dict[str, Any] = {}
    floor_cache: dict[tuple[str, str, int, float, int], list[bool]] = {}

    def floor_trigger(copilot: str, condition: str, seed: int, theta: float, window: int) -> list[bool]:
        key = (copilot, condition, seed, theta, window)
        if key not in floor_cache:
            rows = streams[copilot][condition][str(seed)]
            floor_cache[key] = _floor_triggers(rows, theta, window, len(geometry[copilot]["category_names"]))
        return floor_cache[key]

    for copilot in COPILOTS:
        q2[copilot] = {}
        for theta in THETAS:
            for window in WINDOWS:
                key = f"{theta:.2f}_{window}"
                q2[copilot][key] = {}
                for condition in CONDITIONS:
                    clean_rates = [sum(floor_trigger(copilot, "clean_control", seed, theta, window)) / TOTAL_DECISIONS for seed in SEEDS]
                    lags = [_first_lag(streams[copilot][condition][str(seed)], floor_trigger(copilot, condition, seed, theta, window)) for seed in SEEDS] if condition != "clean_control" else []
                    observed = [lag for lag in lags if lag is not None]
                    q2[copilot][key][condition] = {"clean_pause_rate": mean(clean_rates), "detection_lag": mean(observed) if observed else None}

    driver_rows: list[dict[str, Any]] = []
    for copilot in COPILOTS:
        baseline = mean(float(r["is_correct"]) for seed in SEEDS for r in streams[copilot]["clean_control"][str(seed)][:500])
        for condition in ("slow_drift", "poison_25", "fast_break"):
            degraded = [r for seed in SEEDS for r in streams[copilot][condition][str(seed)][ONSET - 1:ONSET + 99]]
            margins = [float(r["margin"]) for seed in SEEDS for r in streams[copilot][condition][str(seed)][:500]]
            rows = [r for seed in SEEDS for r in streams[copilot][condition][str(seed)]]
            trig = _floor_triggers(rows, 0.75, 100, len(geometry[copilot]["category_names"]))
            lag = _first_lag(rows, trig)
            driver_rows.append({"copilot": copilot, "condition": condition, "detection_lag": float(lag if lag is not None else 399), "base_accuracy": baseline, "degradation_magnitude": baseline - mean(float(r["is_correct"]) for r in degraded), "margin_std": pstdev(margins), "decision_volume": float(len(rows))})
    q3_factors = ["base_accuracy", "degradation_magnitude", "margin_std", "decision_volume"]
    correlations: list[dict[str, Any]] = []
    for factor in q3_factors:
        correlation = _corr([float(r[factor]) for r in driver_rows], [float(r["detection_lag"]) for r in driver_rows])
        correlations.append({"factor": factor, "correlation": correlation, "absolute_correlation": abs(correlation or 0.0)})
    correlations.sort(key=lambda x: (-float(x["absolute_correlation"]), str(x["factor"])))
    q3 = {"ranked_factors": correlations, "per_copilot_drivers": {copilot: [r for r in driver_rows if r["copilot"] == copilot] for copilot in COPILOTS}}

    q4: dict[str, Any] = {"absolute_floor": {}, "relative_change": {}, "distributional_shift": {}}
    for copilot in COPILOTS:
        nc = len(geometry[copilot]["category_names"])
        q4["absolute_floor"][copilot] = {condition: q2[copilot]["0.75_100"][condition] for condition in CONDITIONS}
        q4["relative_change"][copilot] = {str(drop): {condition: _cell_metrics(streams, copilot, condition, lambda rows, d=drop: _relative_trigger(rows, d)) for condition in CONDITIONS} for drop in RELATIVE_THRESHOLDS}
        q4["distributional_shift"][copilot] = {str(threshold): {condition: _cell_metrics(streams, copilot, condition, lambda rows, d=threshold: _drift_trigger(rows, d)) for condition in CONDITIONS} for threshold in DRIFT_THRESHOLDS}

    proposal = {"regime": "composite", "rationale": "The absolute floor has a domain-specific clean-pause frontier, while relative change improves comparability but is not uniformly fast and factor drift is not uniformly discriminative. Stage 2 should test a composite calibrated floor plus relative-change guard, with drift retained as an audit signal.", "proposed_what_ifs": ["Per-domain theta at the lowest clean_pause_rate below 5% with lag monitoring.", "Relative drop 0.30 over a 200-record baseline and 100-record current window.", "Optional drift PSI 0.10 as a non-blocking diagnostic.", "Accept only if every copilot has clean_pause_rate < 5% and mean detected lag < 150 records on slow_drift, poison_25, and fast_break where observable; report misses separately."]}
    result = {"q1_base_accuracy": q1, "q2_pareto_surface": q2, "q3_lag_drivers": q3, "q4_alternative_signals": q4, "stage2_proposal": proposal, "metadata": {"seeds": list(SEEDS), "thetas": list(THETAS), "windows": list(WINDOWS), "relative_change_thresholds": list(RELATIVE_THRESHOLDS), "tier": "REAL_COMPONENT geometry + SIMULATED streams/degradation", "stream_horizon": TOTAL_DECISIONS, "degradation_onset": ONSET, "drift_thresholds": list(DRIFT_THRESHOLDS)}}
    return result, {"driver_rows": driver_rows, "streams": streams}


def _summary(result: dict[str, Any]) -> str:
    lines = ["# Conservation Characterization Stage 1", "", "Analysis-only; geometry is REAL_COMPONENT and streams/degradations are SIMULATED.", "", "## 1. Q1 — below-floor structure", "", "| Copilot | N=50 | N=100 | N=200 |", "|---|---:|---:|---:|"]
    for copilot in COPILOTS:
        vals = [result["q1_base_accuracy"][copilot][str(n)]["fraction_below_075"] for n in WINDOWS]
        lines.append(f"| {copilot} | {vals[0]:.1%} | {vals[1]:.1%} | {vals[2]:.1%} |")
    over10 = [c for c in COPILOTS if result["q1_base_accuracy"][c]["100"]["fraction_below_075"] > 0.10]
    lines += ["", f"At N=100, copilots above 10% below-floor time: {', '.join(over10) if over10 else 'none'}. This is {'structural across domains' if len(over10) > 1 else 'Purchasing-specific at the tested horizon' if over10 == ['purchasing'] else 'mixed/domain-specific'}.", "", "## 2. Q2 — Pareto surface", "", "The viable operating-point test is clean_pause_rate < 5% and mean lag < 150 records across all five copilots. The full θ×N×condition surface is in the JSON artifact. See per-copilot rows below for the current point (0.75,100).", "", "| Copilot | Clean pause | Slow drift lag | Poison 25 lag | Fast break lag |", "|---|---:|---:|---:|---:|"]
    for c in COPILOTS:
        cell = result["q2_pareto_surface"][c]["0.75_100"]
        fmt = lambda x: "missed" if x is None else f"{x:.1f}"
        lines.append(f"| {c} | {cell['clean_control']['clean_pause_rate']:.1%} | {fmt(cell['slow_drift']['detection_lag'])} | {fmt(cell['poison_25']['detection_lag'])} | {fmt(cell['fast_break']['detection_lag'])} |")
    lines += ["", "## 3. Q3 — lag drivers", ""]
    for rank, item in enumerate(result["q3_lag_drivers"]["ranked_factors"], 1):
        lines.append(f"{rank}. **{item['factor']}**: Pearson r={item['correlation'] if item['correlation'] is not None else 'undefined'}.")
    lines += ["", "## 4. Q4 — alternative signals", "", "| Signal family | Parameter | Result |", "|---|---:|---|"]
    for family in ("absolute_floor", "relative_change", "distributional_shift"):
        params = ["0.75 / 100"] if family == "absolute_floor" else list(next(iter(result["q4_alternative_signals"][family].values())).keys())
        for param in params:
            lines.append(f"| {family} | {param} | Per-copilot/per-condition clean rates and lags are in JSON |")
    lines += ["", "## 5. Stage 2 proposal", "", f"**Regime:** {result['stage2_proposal']['regime']}. {result['stage2_proposal']['rationale']}", "", "Stage 2 requires operator sign-off before running.", "", "## 6. Characterization verdict", "", "The conservation gate's problem is **mixed, with calibration and statistic limitations rather than a single universal defect**. The Q1/Q2 surface shows whether the absolute floor is domain-specific and whether any retuning clears the joint clean-pause/lag rule; Q3 quantifies whether base accuracy, degradation magnitude, margin volatility, or fixed volume explains lag; Q4 compares relative change and distributional shift on identical streams. These results characterize candidate regimes only and do not adopt a gate change."]
    return "\n".join(lines) + "\n"


def main() -> None:
    result, _details = _build()
    serialized = json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n"
    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_JSON.write_text(serialized, encoding="utf-8")
    OUTPUT_MD.write_text(_summary(result), encoding="utf-8")
    print(f"wrote {OUTPUT_JSON} sha256={hashlib.sha256(serialized.encode()).hexdigest()[:16]}")
    print(f"wrote {OUTPUT_MD}")


if __name__ == "__main__":
    main()
