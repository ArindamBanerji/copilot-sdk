from __future__ import annotations

"""Stage 3A startup characterization and drift-tracking what-if.

Pre-registered hypotheses:
H-yes: tracked-baseline drift catches slow drift missed by the static floor,
keeps clean_pause_rate <5%, and preserves 100% sustained-poison detection.
H-no: tracking misses slow drift or catches it only at unacceptable
false-pause; slow-drift latency is an honest boundary of accuracy gating.

Simulation only.  Stage 1/2 geometry and stream helpers are imported; no
production gate or existing source file is changed.
"""

import hashlib
import json
import random
from pathlib import Path
from statistics import mean, pstdev
from typing import Any, cast

import numpy as np

import vld_conservation_characterization_v1 as s1
import vld_conservation_stage2_composite_v1 as s2


ROOT = Path(__file__).resolve().parents[2]
STAGE1_JSON = ROOT / "experiments" / "vld" / "results" / "conservation_characterization_stage1.json"
STAGE2_JSON = ROOT / "experiments" / "vld" / "results" / "conservation_stage2_composite.json"
OUTPUT_JSON = ROOT / "experiments" / "vld" / "results" / "conservation_stage3_track.json"
OUTPUT_MD = ROOT / "experiments" / "vld" / "results" / "conservation_stage3_summary.md"
SEEDS = (42, 123, 7)
COPILOTS = ("dataops", "trading", "purchasing", "soc", "s2p")
STARTUP_NS = (100, 250, 500)
RELATIVE_X = (0.10, 0.20, 0.30)
CUSUM_H = (3.0, 5.0, 8.0)
EWMA_LAMBDAS = (0.05, 0.10, 0.20)
STREAM_HORIZON = 1400
EVAL_CLEAN_N = 500
ONSET = s1.ONSET
ROLLING_WINDOW = 100


def _load(path: Path) -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))


def _rolling(values: list[float], window: int = ROLLING_WINDOW) -> list[float]:
    result: list[float] = []
    for i in range(len(values)):
        start = max(0, i + 1 - window)
        result.append(sum(values[start:i + 1]) / (i + 1 - start))
    return result


def _fit(rows: list[dict[str, Any]], n: int, margin: float) -> dict[str, float]:
    values = [float(row["is_correct"]) for row in rows[:n]]
    tracked = _rolling(values)
    steady = tracked[min(ROLLING_WINDOW - 1, len(tracked) - 1):] or tracked
    baseline = mean(steady)
    sigma = pstdev(steady) if len(steady) > 1 else 0.0
    return {"fitted_floor": max(0.0, baseline - margin), "fitted_baseline": baseline, "normal_region_lo": baseline - 2.0 * sigma, "normal_region_hi": baseline + 2.0 * sigma, "tracked_sigma": max(sigma, 0.01), "margin": margin}


def _signals(rows: list[dict[str, Any]], start: int, fit: dict[str, float], regime: str, param: float | None) -> list[bool]:
    values = [float(row["is_correct"]) for row in rows]
    rolling = _rolling(values)
    fired = [False] * len(rows)
    cusum = 0.0
    ewma = fit["fitted_baseline"]
    for i in range(start, len(rows)):
        floor = rolling[i] < fit["fitted_floor"] if i >= ROLLING_WINDOW - 1 else False
        if regime == "T0_static":
            tracked = False
        elif regime.startswith("T1_relative"):
            x = float(param or 0.0)
            tracked = rolling[i] < fit["fitted_baseline"] * (1.0 - x)
        elif regime.startswith("T2_cusum"):
            deviation = max(0.0, (fit["fitted_baseline"] - rolling[i]) / fit["tracked_sigma"])
            cusum = max(0.0, cusum + deviation)
            tracked = cusum >= float(param or 0.0)
        else:
            lam = float(param or 0.0)
            ewma = lam * rolling[i] + (1.0 - lam) * ewma
            tracked = ewma < fit["normal_region_lo"]
        fired[i] = floor or tracked
    return fired


def _lag(rows: list[dict[str, Any]], fired: list[bool]) -> int | str:
    for i in range(ONSET, len(rows)):
        if fired[i]:
            return int(i + 1 - ONSET)
    return "missed"


def _calibration(stage1: dict[str, Any], stage2: dict[str, Any], copilot: str, clean_rows: dict[int, list[dict[str, Any]]]) -> dict[str, dict[str, Any]]:
    margin = float(stage2["R1_per_domain"][copilot]["aggregate"]["floor_calibration"]["margin"])
    result: dict[str, dict[str, Any]] = {}
    for n in STARTUP_NS:
        per_seed: dict[str, Any] = {}
        for seed in SEEDS:
            per_seed[str(seed)] = _fit(clean_rows[seed], n, margin)
        floors = [float(v["fitted_floor"]) for v in per_seed.values()]
        baselines = [float(v["fitted_baseline"]) for v in per_seed.values()]
        target = float(stage2["R1_per_domain"][copilot]["aggregate"]["floor_calibration"]["floor"])
        result[str(n)] = {"per_seed": per_seed, "aggregate": {"fitted_floor_mean": mean(floors), "fitted_baseline_mean": mean(baselines), "matches_r1_floor": abs(mean(floors) - target) < 0.05, "r1_floor": target}}
    return result


def _evaluate(regime: str, param: float | None, copilot: str, seed: int, n: int, streams: dict[str, dict[str, dict[str, list[dict[str, Any]]]]], fit: dict[str, float]) -> dict[str, Any]:
    clean = streams[copilot]["clean_control"][str(seed)]
    clean_eval = clean[n:n + EVAL_CLEAN_N]
    clean_fired = _signals(clean, n, fit, regime, param)
    clean_rate = sum(clean_fired[n:n + len(clean_eval)]) / len(clean_eval)
    lags: dict[str, int | str] = {}
    for condition in ("slow_drift", "poison_25", "fast_break"):
        rows = streams[copilot][condition][str(seed)]
        fired = _signals(rows, n, fit, regime, param)
        lags[condition] = _lag(rows, fired)
    slow = lags["slow_drift"]
    poison = lags["poison_25"] != "missed"
    fast = isinstance(lags["fast_break"], int) and int(lags["fast_break"]) < 100
    return {"clean_pause_rate": clean_rate, "slow_drift_detected": slow != "missed", "slow_drift_lag_records": slow, "slow_drift_lag": slow, "sustained_poison_detected": poison, "fast_break_detection": fast, "fast_break_detected": fast, "detection_lag_records": lags}


def _regimes() -> list[tuple[str, float | None]]:
    regimes: list[tuple[str, float | None]] = [("T0_static", None)]
    regimes.extend((f"T1_relative_{int(x * 100)}", x) for x in RELATIVE_X)
    regimes.extend((f"T2_cusum_h{int(h)}", h) for h in CUSUM_H)
    regimes.extend((f"T2_ewma_lambda{int(lam * 100)}", lam) for lam in EWMA_LAMBDAS)
    return regimes


def _build() -> dict[str, Any]:
    stage1 = _load(STAGE1_JSON)
    stage2 = _load(STAGE2_JSON)
    geometry = s1.load_geometry()
    s1.TOTAL_DECISIONS = STREAM_HORIZON
    streams: dict[str, dict[str, dict[str, list[dict[str, Any]]]]] = {}
    for copilot in COPILOTS:
        streams[copilot] = {}
        for condition in ("slow_drift", "poison_25", "fast_break", "clean_control"):
            streams[copilot][condition] = {str(seed): s1._stream(copilot, geometry[copilot], seed, condition) for seed in SEEDS}
    startup: dict[str, Any] = {}
    for copilot in COPILOTS:
        clean_rows = {seed: streams[copilot]["clean_control"][str(seed)] for seed in SEEDS}
        startup[copilot] = _calibration(stage1, stage2, copilot, clean_rows)
    tracking: dict[str, Any] = {}
    for regime, param in _regimes():
        tracking[regime] = {}
        for copilot in COPILOTS:
            n = 100
            per_seed: dict[str, Any] = {}
            for seed in SEEDS:
                fit = startup[copilot][str(n)]["per_seed"][str(seed)]
                per_seed[str(seed)] = _evaluate(regime, param, copilot, seed, n, streams, fit)
            clean_mean = mean(float(v["clean_pause_rate"]) for v in per_seed.values())
            slow_detect = mean(float(v["slow_drift_detected"]) for v in per_seed.values())
            slow_lags = [v["slow_drift_lag_records"] for v in per_seed.values() if isinstance(v["slow_drift_lag_records"], int)]
            poison_rate = mean(float(v["sustained_poison_detected"]) for v in per_seed.values())
            fast_rate = mean(float(v["fast_break_detection"]) for v in per_seed.values())
            slow_mean: float | str = mean(cast(list[int], slow_lags)) if slow_lags else "missed"
            h1 = clean_mean < 0.05
            h2 = slow_detect >= 1.0 and slow_mean != "missed" and float(slow_mean) < 150.0
            h3 = poison_rate >= 1.0
            tracking[regime][copilot] = {"per_seed": per_seed, "aggregate": {"clean_pause_rate_mean": clean_mean, "slow_drift_detection_rate": slow_detect, "slow_drift_lag_records_mean": slow_mean, "slow_drift_lag_mean": slow_mean, "sustained_poison_detection_rate": poison_rate, "fast_break_detection": fast_rate, "fast_break_detection_rate": fast_rate, "h_yes_axis1": h1, "h_yes_axis2": h2, "h_yes_axis3": h3, "validated": h1 and h2 and h3, "startup_N": n, "parameter": param}}
    candidates = [(regime, sum(bool(tracking[regime][c]["aggregate"]["validated"]) for c in COPILOTS), mean(float(tracking[regime][c]["aggregate"]["clean_pause_rate_mean"]) for c in COPILOTS)) for regime, _ in _regimes() if regime != "T0_static"]
    candidates.sort(key=lambda x: (-x[1], x[2], x[0]))
    best_regime = candidates[0][0]
    best_param = dict(_regimes())[best_regime]
    validated = [c for c in COPILOTS if tracking[best_regime][c]["aggregate"]["validated"]]
    failed = [c for c in COPILOTS if c not in validated]
    verdict = "H-yes" if len(validated) == len(COPILOTS) else "H-no"
    return {"startup_characterization": startup, "tracking_results": tracking, "best_tracker": {"regime": best_regime, "params": {"X_pct": best_param} if best_regime.startswith("T1") else {"cusum_h": best_param} if best_regime.startswith("T2_cusum") else {"ewma_lambda": best_param}, "validated_copilots": validated, "failed_copilots": failed, "rationale": "Selected by maximum validated copilots, then lowest mean clean-pause rate. H-no remains if any copilot fails an acceptance axis."}, "verdict": verdict, "metadata": {"seeds": list(SEEDS), "startup_N_sweep": list(STARTUP_NS), "relative_movement_X": list(RELATIVE_X), "cusum_h": list(CUSUM_H), "ewma_lambda": list(EWMA_LAMBDAS), "tier": "REAL_COMPONENT geometry + SIMULATED conditions", "startup_eval_disjoint": True, "eval_clean_decisions": EVAL_CLEAN_N, "slow_drift_onset": ONSET}}


def _summary(data: dict[str, Any]) -> str:
    best = data["best_tracker"]["regime"]
    lines = ["# Conservation Stage 3A — Startup Characterization and Drift Tracking", "", "Simulation-only; no production gate change.", "", "## 1. Startup characterization", "", "| Copilot | N=100 floor | N=250 floor | N=500 floor | R1 floor |", "|---|---:|---:|---:|---:|"]
    for copilot in COPILOTS:
        vals = data["startup_characterization"][copilot]
        lines.append(f"| {copilot} | {vals['100']['aggregate']['fitted_floor_mean']:.3f} | {vals['250']['aggregate']['fitted_floor_mean']:.3f} | {vals['500']['aggregate']['fitted_floor_mean']:.3f} | {vals['100']['aggregate']['r1_floor']:.3f} |")
    lines += ["", "The startup fit uses the first N records and evaluates on a disjoint held-out stream segment. N=100 is treated as sufficient when its fitted floor is within 0.05 of the Stage 2 R1 floor.", "", "## 2. Tracking comparison", "", "| Regime | Copilot | clean_pause_rate | slow drift detection | slow drift lag | poison detection | fast-break detection | validated |", "|---|---|---:|---:|---:|---:|---:|---|"]
    for regime in data["tracking_results"]:
        for copilot in COPILOTS:
            a = data["tracking_results"][regime][copilot]["aggregate"]
            lines.append(f"| {regime} | {copilot} | {a['clean_pause_rate_mean']:.1%} | {a['slow_drift_detection_rate']:.1%} | {a['slow_drift_lag_records_mean']} | {a['sustained_poison_detection_rate']:.1%} | {a['fast_break_detection']:.1%} | {a['validated']} |")
    lines += ["", "## 3. Did tracking close the slow-drift gap?", "", f"T0 is the static per-domain floor. The selected tracker is **{best}**; previously missed copilots and their axis results are in the JSON per-copilot aggregates.", "", "## 4. False-pause cost", "", "Acceptance requires clean_pause_rate <5%. Compare each tracker against T0 in the table; any tracker above 5% fails axis 1 even if its lag improves.", "", "## 5. Tracker comparison", "", "Relative movement, standardized CUSUM, and EWMA are all evaluated. The best tracker is selected by validated-copilot count, then lowest mean clean-pause rate.", "", "## 6. H-yes/H-no verdict", "", f"**{data['verdict']}**. Validated copilots: {', '.join(data['best_tracker']['validated_copilots']) or 'none'}. Failed copilots: {', '.join(data['best_tracker']['failed_copilots']) or 'none'}.", "", "## 7. Best tracker", "", f"{best} with parameters {data['best_tracker']['params']}.", "", "## 8. §5 conservation sentence", "", "slow-drift latency is a genuine boundary of accuracy-based gating even with tracking; the static per-domain floor remains the false-pause fix, with slow-drift as an honest limitation." if data["verdict"] == "H-no" else "conservation parameters are characterized per deployment at startup and tracked for drift; baseline-tracking catches slow drift the static floor missed, at <5% false-pause, with 100% sustained-poisoning detection.", "", "## 9. Stage 3B", "", "Stage 3B (d² control signal) is **priority** because H-no indicates that accuracy/geometry tracking did not close the slow-drift boundary." if data["verdict"] == "H-no" else "Stage 3B is optional because H-yes was supported."]
    return "\n".join(lines) + "\n"


def main() -> None:
    data = _build()
    text = json.dumps(data, indent=2, sort_keys=True, allow_nan=False) + "\n"
    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_JSON.write_text(text, encoding="utf-8")
    OUTPUT_MD.write_text(_summary(data), encoding="utf-8")
    print(f"wrote {OUTPUT_JSON} sha256={hashlib.sha256(text.encode()).hexdigest()[:16]}")
    print(f"wrote {OUTPUT_MD}")


if __name__ == "__main__":
    main()
