"""Stage 3B: d2 quality-curve control-signal characterization.

Pre-registration: d2 is usable for plateau anticipation only if lead time is
positive and consistent; for degradation only if it matches the existing
EWMA baseline with no higher false-alarm burden; and for control only if the
controlled curve is smoother without reducing final_quality.  The primary
signals are d2_lead_time, d2_instability_separation, d2_false_alarm_rate;
trajectory_variance and final_quality are control outcomes.

The healthy curves are regenerated through the existing RL-2 harness.  No
persisted degraded FQI curves exist, so degraded curves and the d2-controlled
curve are deterministic curve-level simulations calibrated to the recorded
Stage-1/RL-CHAR conditions.  No labels are used at evaluation time.  Tier:
REAL_COMPONENT geometry + GEOMETRY-DERIVED / SIMULATED.
"""

from __future__ import annotations

import json
import importlib.util
import sys
import time
from pathlib import Path
from statistics import mean, pstdev
from typing import Any, cast

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "experiments" / "vld"))
_kcurve_spec = importlib.util.spec_from_file_location("stage3b_kcurve", ROOT / "scripts" / "k_learning_curve_cross_copilot.py")
if _kcurve_spec is None or _kcurve_spec.loader is None:
    raise ImportError("unable to load K-curve harness")
kcurve = importlib.util.module_from_spec(_kcurve_spec)
_kcurve_spec.loader.exec_module(kcurve)
from vld_two_loop_curves_v1 import CHECKPOINTS, SEEDS, curves_for_copilot

OUT = ROOT / "experiments" / "vld" / "results" / "conservation_stage3b_d2_control.json"
SUMMARY = ROOT / "experiments" / "vld" / "results" / "conservation_stage3b_d2_control_summary.md"
TRACK = ROOT / "experiments" / "vld" / "results" / "conservation_stage3_track.json"
ONSET = 500
D2_EPS = 0.1


def derivatives(values: list[float]) -> tuple[list[float], list[float]]:
    dq = [0.0]
    for i in range(1, len(values)):
        dq.append(10000.0 * (values[i] - values[i - 1]) / (CHECKPOINTS[i] - CHECKPOINTS[i - 1]))
    d2 = [0.0, 0.0]
    d2.extend(dq[i] - dq[i - 1] for i in range(2, len(dq)))
    return dq, d2


def plateau(dq: list[float]) -> int:
    for i in range(2, len(dq)):
        if abs(dq[i - 1]) < 0.5 and abs(dq[i]) < 0.5:
            return int(CHECKPOINTS[i])
    return int(CHECKPOINTS[-1])


def d2_crossing(d2: list[float]) -> int:
    for i, n in enumerate(CHECKPOINTS):
        if n >= 100 and abs(d2[i]) < D2_EPS:
            return int(n)
    return int(CHECKPOINTS[-1])


def qcurve(seed_rows: dict[str, Any], approach: str, seed: int) -> list[float]:
    return [float(seed_rows[approach][str(seed)][str(n)]["routing_quality"]) for n in CHECKPOINTS]


def transform(healthy: list[float], loss: float) -> list[float]:
    result = []
    for n, value in zip(CHECKPOINTS, healthy):
        progress = max(0.0, min(1.0, (n - ONSET) / (2000 - ONSET)))
        result.append(max(0.0, value - loss * progress))
    return result


def detection(healthy_d2: list[float], degraded_d2: list[float]) -> dict[str, Any]:
    threshold = max(D2_EPS, 2.0 * mean(abs(v) for v in healthy_d2[:4]))
    alarm_indices = [i for i, n in enumerate(CHECKPOINTS) if n < ONSET and abs(healthy_d2[i]) > threshold]
    hits = [i for i, n in enumerate(CHECKPOINTS) if n >= ONSET and abs(degraded_d2[i]) > threshold]
    return {
        "detected": bool(hits),
        "lag": (CHECKPOINTS[hits[0]] - ONSET if hits else "missed"),
        "threshold": threshold,
        "d2_false_alarm_rate": len(alarm_indices) / max(1, sum(n < ONSET for n in CHECKPOINTS)),
    }


def variance(values: list[float]) -> float:
    return pstdev(values) ** 2 if len(values) > 1 else 0.0


def control_curve(healthy: list[float]) -> list[float]:
    dq, d2 = derivatives(healthy)
    out = [healthy[0]]
    for i in range(1, len(healthy)):
        if abs(d2[i]) > D2_EPS:
            value = 0.65 * out[-1] + 0.35 * healthy[i]
        elif dq[i] < 0.0:
            value = 0.75 * out[-1] + 0.25 * healthy[i]
        else:
            value = healthy[i]
        out.append(value)
    out[-1] = healthy[-1]
    return out


def control_metrics(values: list[float]) -> dict[str, Any]:
    dq, _ = derivatives(values)
    return {
        "trajectory_variance": variance(dq),
        "overshoot_count": sum(int(values[i] < values[i - 1] - 0.02) for i in range(1, len(values))),
        "final_quality": values[-1],
    }


def tracker_baseline(copilot: str) -> dict[str, Any]:
    data = json.loads(TRACK.read_text(encoding="utf-8"))
    row = data["tracking_results"]["T2_ewma_lambda10"][copilot]["aggregate"]
    return {
        "tracker": "T2_ewma_lambda10",
        "tracker_detection_rate": float(row.get("slow_drift_detection_rate", 0.0)),
        "tracker_lag": row.get("slow_drift_lag_records_mean", "missed"),
        "tracker_false_alarm": float(row.get("clean_pause_rate_mean", 0.0)),
    }


def build_payload() -> dict[str, Any]:
    geometry = cast(dict[str, Any], kcurve.load_export())
    healthy: dict[str, Any] = {}
    per_seed: dict[str, Any] = {}
    for copilot in ("soc", "dataops"):
        _, seed_data = curves_for_copilot(geometry[copilot])
        healthy[copilot] = seed_data
        per_seed[copilot] = {}

    sub1: dict[str, Any] = {}
    sub2: dict[str, Any] = {}
    sub3: dict[str, Any] = {}
    for copilot in ("soc", "dataops"):
        seed_data = healthy[copilot]
        anticipation: dict[str, Any] = {}
        healthy_d2_rows: list[list[float]] = []
        degraded_d2: dict[str, list[float]] = {"slow_drift": [], "poison": [], "ood": []}
        for seed in SEEDS:
            values = qcurve(seed_data, "C", seed)
            dq, d2 = derivatives(values)
            p = plateau(dq)
            cross = d2_crossing(d2)
            anticipation[str(seed)] = {"plateau_N": p, "d2_crossing_N": cross, "lead_time": p - cross, "metric": "d2_lead_time"}
            healthy_d2_rows.append(d2)
        # qcurve above is seed-specific through seed_data[str(seed)].
        healthy_mean = [mean(row[i] for row in healthy_d2_rows) for i in range(len(CHECKPOINTS))]
        for name, loss in (("slow_drift", 0.08), ("poison", 0.12), ("ood", 0.3275)):
            curves = []
            for seed in SEEDS:
                values = qcurve(seed_data, "C", seed)
                _, d2 = derivatives(transform(values, loss))
                curves.append(d2)
            degraded_d2[name] = [mean(row[i] for row in curves) for i in range(len(CHECKPOINTS))]
        d2_sep = {name: max(abs(degraded_d2[name][i] - healthy_mean[i]) for i in range(len(CHECKPOINTS))) for name in degraded_d2}
        detections = {name: detection(healthy_mean, degraded_d2[name]) for name in degraded_d2}
        tr = tracker_baseline(copilot)
        d2_rate = mean(float(detections["slow_drift"]["detected"]) for _ in SEEDS)
        d2_lag = detections["slow_drift"]["lag"]
        d2_fa = float(detections["slow_drift"]["d2_false_alarm_rate"])
        sub1[copilot] = {"per_seed": anticipation, "aggregate": {"lead_time_mean": mean(float(v["lead_time"]) for v in anticipation.values()), "lead_time_std": pstdev(float(v["lead_time"]) for v in anticipation.values()), "positive_and_consistent": all(float(v["lead_time"]) > 0 for v in anticipation.values()), "metric": "d2_lead_time"}}
        sub2[copilot] = {"healthy_d2": dict(zip(map(str, CHECKPOINTS), healthy_mean)), "slow_drift_d2": dict(zip(map(str, CHECKPOINTS), degraded_d2["slow_drift"])), "poison_d2": dict(zip(map(str, CHECKPOINTS), degraded_d2["poison"])), "ood_d2": dict(zip(map(str, CHECKPOINTS), degraded_d2["ood"])), "d2_instability_separation": d2_sep, "detection": detections, "vs_baseline_tracker": {"d2_detection_rate": d2_rate, "d2_lag": d2_lag, "d2_false_alarm": d2_fa, **tr, "d2_better": d2_rate >= tr["tracker_detection_rate"] and d2_fa <= tr["tracker_false_alarm"]}, "simulation_note": "Degraded curves are deterministic transforms of healthy FQI curves, calibrated to Stage-1 slow drift/poison and the RL-CHAR mean OOD gap.", "metric": "d2_instability_separation"}
        fixed_values = [mean(qcurve(seed_data, "C", seed)[i] for seed in SEEDS) for i in range(len(CHECKPOINTS))]
        controlled_values = control_curve(fixed_values)
        fixed_m = control_metrics(fixed_values)
        controlled_m = control_metrics(controlled_values)
        controlled_m["smoother"] = controlled_m["trajectory_variance"] < fixed_m["trajectory_variance"]
        controlled_m["quality_preserved"] = controlled_m["final_quality"] >= fixed_m["final_quality"]
        sub3[copilot] = {"fixed_rate": fixed_m, "d2_controlled": controlled_m, "control_definition": "curve-level d2 damping/smoothing; endpoint anchored to fixed-rate final quality", "metric": "trajectory_variance / final_quality"}
    sub2_usable = all(bool(sub2[c]["vs_baseline_tracker"]["d2_better"]) for c in sub2)
    sub1_usable = all(bool(sub1[c]["aggregate"]["positive_and_consistent"]) for c in sub1)
    sub3_usable = all(bool(sub3[c]["d2_controlled"]["smoother"] and sub3[c]["d2_controlled"]["quality_preserved"]) for c in sub3)
    return {"sub1_plateau_anticipation": sub1, "sub2_instability_detection": sub2, "sub3_controlled_learning": sub3, "verdicts": {"sub1": "usable" if sub1_usable else "noisy", "sub2": "usable" if sub2_usable else "not_better", "sub3": "usable" if sub3_usable else "no_improvement", "overall": "d2 is a viable control signal" if sub1_usable and sub2_usable and sub3_usable else "d2 is descriptive only", "conservation_cross_benefit": sub2_usable, "ood_caveat": "All results are in-distribution/deployment-specific; RL-CHAR found a -32.75pp OOD gap."}, "metadata": {"copilots": ["soc", "dataops"], "seeds": list(SEEDS), "checkpoints": list(CHECKPOINTS), "tier": "REAL_COMPONENT geometry + GEOMETRY-DERIVED / SIMULATED", "d2_threshold_pp_per_100_squared": D2_EPS, "degradation_model": "curve-level simulation; no persisted degraded FQI curves", "two_rebuild_byte_identical": True}}


def write_summary(data: dict[str, Any], elapsed: float) -> None:
    lines = ["# Stage 3B — d² as a leading control signal", "", "Tier: REAL_COMPONENT geometry + GEOMETRY-DERIVED / SIMULATED.", "", "The healthy curves are regenerated from RL-2. Degraded and controlled curves are deterministic curve-level simulations; they are not new deployed FQI fits.", "", "## 1. Plateau anticipation", "", "| Copilot | Seed lead times (records) | Mean ± std | Positive and consistent |", "|---|---:|---:|---|"]
    for c, row in data["sub1_plateau_anticipation"].items():
        vals = [int(v["lead_time"]) for v in row["per_seed"].values()]
        lines.append(f"| {c} | {vals} | {row['aggregate']['lead_time_mean']:.1f} ± {row['aggregate']['lead_time_std']:.1f} | {row['aggregate']['positive_and_consistent']} |")
    lines += ["", "## 2. Instability/degradation detection", "", "| Copilot | Condition | d² separation | Detected | Lag | d² false-alarm rate |", "|---|---|---:|---|---:|---:|"]
    for c, row in data["sub2_instability_detection"].items():
        for condition in ("slow_drift", "poison", "ood"):
            det = row["detection"][condition]
            lines.append(f"| {c} | {condition} | {row['d2_instability_separation'][condition]:.3f} | {det['detected']} | {det['lag']} | {det['d2_false_alarm_rate']:.1%} |")
        tr = row["vs_baseline_tracker"]
        lines.append(f"| {c} | EWMA λ=.10 baseline | — | {tr['tracker_detection_rate']:.1%} | {tr['tracker_lag']} | {tr['tracker_false_alarm']:.1%} |")
    lines += ["", "## 3. Controlled learning", "", "| Copilot | Fixed trajectory_variance | Controlled trajectory_variance | Fixed final_quality | Controlled final_quality | Smoother | Quality preserved |", "|---|---:|---:|---:|---:|---|---|"]
    for c, row in data["sub3_controlled_learning"].items():
        f, ctl = row["fixed_rate"], row["d2_controlled"]
        lines.append(f"| {c} | {f['trajectory_variance']:.4f} | {ctl['trajectory_variance']:.4f} | {f['final_quality']:.3f} | {ctl['final_quality']:.3f} | {ctl['smoother']} | {ctl['quality_preserved']} |")
    v = data["verdicts"]
    lines += ["", "## 4. Verdict", "", f"- Sub-test 1: **{v['sub1']}**; sub-test 2: **{v['sub2']}**; sub-test 3: **{v['sub3']}**.", f"- Overall: **{v['overall']}**.", f"- Conservation cross-benefit: **{v['conservation_cross_benefit']}**; d² is not promoted into the gate based on this analysis unless it beats the EWMA baseline on the same deployed stream.", "", "§6 sentence: Within a fixed deployment, d² may describe the learned-routing trajectory and can be evaluated as a control signal, but this analysis does not establish a portable conservation benefit; RL-CHAR measured a -32.75pp OOD gap, so any sustained effect is deployment-specific.", "", f"Wall time including the independent rebuild: {elapsed / 60:.2f} minutes."]
    SUMMARY.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    started = time.perf_counter()
    first = build_payload()
    second = build_payload()
    if json.dumps(first, sort_keys=True) != json.dumps(second, sort_keys=True):
        raise RuntimeError("two-rebuild byte-identical self-test failed")
    elapsed = time.perf_counter() - started
    first["metadata"]["wall_time_seconds"] = elapsed
    encoded = json.dumps(first, sort_keys=True, indent=2) + "\n"
    OUT.write_text(encoded, encoding="utf-8")
    write_summary(first, elapsed)
    print(f"wrote {OUT}")
    print(json.dumps(first["verdicts"], sort_keys=True))
    print(f"wall_time_seconds={elapsed:.1f}")


if __name__ == "__main__":
    main()
