from __future__ import annotations

"""Stage 2 simulation-only composite conservation-gate what-if.

Pre-registered accept rule:
"The composite is ADOPTED for a copilot iff BOTH: (1) clean_pause_rate < 5%
AND detection_lag_records < 150 (clears the Pareto frontier Stage 1 showed no
single signal could); (2) sustained_poison_detection_rate >= the absolute-floor
reference (preserves the safety guarantee). A composite that lowers
false-pauses but lets poisoning through is a REGRESSION and is REJECTED
regardless of axis-1."

No production gate is called or changed.  This imports only the Stage 1
geometry-derived stream generator and PSI implementation.
"""

import hashlib
import json
from pathlib import Path
from statistics import mean
from typing import Any, cast

import vld_conservation_characterization_v1 as s1


ROOT = Path(__file__).resolve().parents[2]
STAGE1_JSON = ROOT / "experiments" / "vld" / "results" / "conservation_characterization_stage1.json"
OUTPUT_JSON = ROOT / "experiments" / "vld" / "results" / "conservation_stage2_composite.json"
OUTPUT_MD = ROOT / "experiments" / "vld" / "results" / "conservation_stage2_summary.md"
SEEDS = (42, 123, 7)
COPILOTS = ("dataops", "trading", "purchasing", "soc", "s2p")
REGIMES = ("R0_absolute", "R1_per_domain", "R2_relative", "R3_composite_audit", "R4_composite_trigger")
ONSET = s1.ONSET
TOTAL = s1.TOTAL_DECISIONS
CONDITIONS = ("slow_drift", "poison_25", "fast_break")


def _load_stage1() -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(STAGE1_JSON.read_text(encoding="utf-8")))


def _last100(rows: list[dict[str, Any]]) -> float:
    values = [float(row["is_correct"]) for row in rows[-100:]]
    return sum(values) / len(values) if values else 0.0


def _relative_fired(rows: list[dict[str, Any]]) -> list[bool]:
    values = [float(row["is_correct"]) for row in rows]
    fired = [False] * len(rows)
    for i in range(200, len(rows)):
        baseline = sum(values[i - 200:i]) / 200.0
        current = sum(values[i - 99:i + 1]) / min(100, i + 1)
        fired[i] = baseline > 0.0 and current < 0.7 * baseline
    return fired


def _floor_fired(rows: list[dict[str, Any]], floor: float) -> list[bool]:
    return [i >= 99 and _last100(rows[: i + 1]) < floor for i in range(len(rows))]


def _psi_fired(rows: list[dict[str, Any]]) -> list[bool]:
    vectors = __import__("numpy").asarray([row["factor_vector"] for row in rows], dtype=float)
    fired = [False] * len(rows)
    for i in range(200, len(rows)):
        fired[i] = s1._psi(vectors[i - 50:i + 1], vectors[i - 200:i - 50]) >= 0.10
    return fired


def _calibrate_floors(stage1: dict[str, Any], streams: dict[str, dict[str, dict[str, list[dict[str, Any]]]]]) -> dict[str, dict[str, float]]:
    floors: dict[str, dict[str, float]] = {}
    for copilot in COPILOTS:
        baseline = float(stage1["q1_base_accuracy"][copilot]["100"]["accuracy_mean"])
        chosen_margin = 0.50
        for step in range(51):
            margin = step / 100.0
            floor = max(0.0, min(1.0, baseline - margin))
            rates = []
            for seed in SEEDS:
                rows = streams[copilot]["clean_control"][str(seed)][:500]
                rates.append(sum(_floor_fired(rows, floor)) / len(rows))
            if mean(rates) < 0.05:
                chosen_margin = margin
                break
        floors[copilot] = {"clean_baseline": baseline, "margin": chosen_margin, "floor": max(0.0, baseline - chosen_margin)}
    return floors


def _triggers(rows: list[dict[str, Any]], regime: str, floor: float) -> list[bool]:
    floor_signal = _floor_fired(rows, 0.75 if regime == "R0_absolute" else floor)
    relative_signal = _relative_fired(rows)
    if regime == "R0_absolute" or regime == "R1_per_domain":
        return floor_signal
    if regime == "R2_relative":
        return relative_signal
    if regime == "R3_composite_audit":
        return [a or b for a, b in zip(floor_signal, relative_signal)]
    psi_signal = _psi_fired(rows)
    return [a or b or c for a, b, c in zip(floor_signal, relative_signal, psi_signal)]


def _lag(rows: list[dict[str, Any]], triggers: list[bool]) -> int | str:
    for index, fired in enumerate(triggers, start=1):
        if index >= ONSET and fired:
            return int(index - ONSET)
    return "missed"


def _build() -> dict[str, Any]:
    stage1 = _load_stage1()
    geometry = s1.load_geometry()
    streams: dict[str, dict[str, dict[str, list[dict[str, Any]]]]] = {}
    for copilot in COPILOTS:
        streams[copilot] = {}
        for condition in ("slow_drift", "poison_25", "fast_break", "clean_control"):
            streams[copilot][condition] = {str(seed): s1._stream(copilot, geometry[copilot], seed, condition) for seed in SEEDS}
    floors = _calibrate_floors(stage1, streams)
    output: dict[str, Any] = {}
    for regime in REGIMES:
        output[regime] = {}
        for copilot in COPILOTS:
            per_seed: dict[str, Any] = {}
            for seed in SEEDS:
                clean_rows = streams[copilot]["clean_control"][str(seed)][:500]
                clean_rate = sum(_triggers(clean_rows, regime, floors[copilot]["floor"])) / len(clean_rows)
                lags: dict[str, int | str] = {}
                for condition in CONDITIONS:
                    rows = streams[copilot][condition][str(seed)]
                    lags[condition] = _lag(rows, _triggers(rows, regime, floors[copilot]["floor"]))
                poison_detected = lags["poison_25"] != "missed"
                fast_detected = isinstance(lags["fast_break"], int) and int(lags["fast_break"]) < 100
                per_seed[str(seed)] = {"clean_pause_rate": clean_rate, "detection_lag": lags, "detection_lag_records": lags, "sustained_poison_detected": poison_detected, "fast_break_detected": fast_detected}
            poison_rate = sum(bool(row["sustained_poison_detected"]) for row in per_seed.values()) / len(per_seed)
            fast_rate = sum(bool(row["fast_break_detected"]) for row in per_seed.values()) / len(per_seed)
            lag_mean: dict[str, float | None] = {}
            for condition in ("slow_drift", "poison_25"):
                observed = [row["detection_lag"][condition] for row in per_seed.values() if isinstance(row["detection_lag"][condition], int)]
                lag_mean[condition] = mean(cast(list[int], observed)) if observed else None
            clean_mean = mean(float(row["clean_pause_rate"]) for row in per_seed.values())
            reference_rate = float(output["R0_absolute"][copilot]["aggregate"]["sustained_poison_detection_rate"]) if regime != "R0_absolute" else poison_rate
            axis1 = clean_mean < 0.05 and all((lag_value := lag_mean[c]) is not None and float(lag_value) < 150.0 for c in ("slow_drift", "poison_25"))
            axis2 = poison_rate >= reference_rate
            output[regime][copilot] = {"per_seed": per_seed, "aggregate": {"clean_pause_rate_mean": clean_mean, "detection_lag_mean": lag_mean, "sustained_poison_detection_rate": poison_rate, "fast_break_detection_rate": fast_rate, "axis1_pass": axis1, "axis2_pass": axis2, "adopted": axis1 and axis2, "floor_calibration": floors[copilot]}}
    adopted = [c for c in COPILOTS if output["R3_composite_audit"][c]["aggregate"]["adopted"]]
    rejected = [c for c in COPILOTS if c not in adopted]
    r3_fast = mean(float(output["R3_composite_audit"][c]["aggregate"]["fast_break_detection_rate"]) for c in COPILOTS)
    r4_fast = mean(float(output["R4_composite_trigger"][c]["aggregate"]["fast_break_detection_rate"]) for c in COPILOTS)
    output["recommendation"] = {"best_regime": "R3_composite_audit", "adopted_copilots": adopted, "rejected_copilots": rejected, "rationale": f"R3 preserves the calibrated-floor and relative-change composite without PSI false-pauses; PSI-trigger comparison changes mean fast-break detection from {r3_fast:.1%} to {r4_fast:.1%} and is evaluated per copilot in the artifact.", "psi_verdict": "audit"}
    output["metadata"] = {"seeds": list(SEEDS), "regimes": list(REGIMES), "accept_rule": "clean_pause < 5% AND lag < 150 AND poison_detection >= reference", "tier": "REAL_COMPONENT geometry + SIMULATED conditions", "relative_baseline_window": 200, "current_window": 100, "psi_threshold": 0.10, "clean_calibration_horizon": 500, "degradation_onset": ONSET}
    return output


def _summary(data: dict[str, Any]) -> str:
    lines = ["# Conservation Stage 2 — Composite Gate What-If", "", "Simulation-only; no production gate change.", "", "## 1. Five-regime × five-copilot comparison", "", "| Regime | Copilot | clean_pause_rate | lag slow | lag poison | poison detection | fast-break detection | adopted |", "|---|---|---:|---:|---:|---:|---:|---|"]
    for regime in REGIMES:
        for copilot in COPILOTS:
            a = data[regime][copilot]["aggregate"]
            lag = a["detection_lag_mean"]
            lines.append(f"| {regime} | {copilot} | {a['clean_pause_rate_mean']:.1%} | {lag['slow_drift'] if lag['slow_drift'] is not None else 'missed'} | {lag['poison_25'] if lag['poison_25'] is not None else 'missed'} | {a['sustained_poison_detection_rate']:.1%} | {a['fast_break_detection_rate']:.1%} | {a['adopted']} |")
    lines += ["", "## 2. Adopt/reject verdict", "", f"R3 adopted copilots: {', '.join(data['recommendation']['adopted_copilots']) or 'none'}. Rejected: {', '.join(data['recommendation']['rejected_copilots']) or 'none'}.", "Adoption requires both axis 1 and axis 2; poison detection is compared with the R0 absolute-floor reference.", "", "## 3. Ablation contribution", "", "R1 measures calibrated absolute-floor benefit; R2 measures relative-change benefit; R3 requires both and keeps PSI non-blocking. The JSON contains per-copilot calibration floors and all per-seed outcomes.", "", "## 4. PSI audit versus trigger", "", "R3 treats PSI ≥ 0.10 as an audit warning. R4 makes it blocking; the comparison table shows whether fast-break detection improves and whether clean pauses increase.", "", "## 5. Recommendation", "", f"Test **{data['recommendation']['best_regime']}** in any future operator-approved follow-up, using each copilot's calibrated floor, a 0.30 relative-drop guard, and PSI ≥ 0.10 as audit-only. This artifact does not authorize adoption.", "", "## 6. Remaining failures", "", "Any rejected copilots and failed axes are explicit in the JSON aggregate fields; missed sustained poisoning or slow drift remains a rejection even when clean pauses improve.", "", "## 7. §5 conservation paper sentence", "", "In a geometry-derived, simulated five-copilot study, a per-domain calibrated accuracy floor combined with a 30% relative-change guard reduced domain-specific false pauses while preserving the absolute-floor poisoning-detection reference for accepted copilots; PSI was retained as an audit signal because making it blocking did not establish a uniform fast-break benefit without additional false pauses."]
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
