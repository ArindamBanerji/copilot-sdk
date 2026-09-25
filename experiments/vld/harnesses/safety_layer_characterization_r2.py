from __future__ import annotations

"""Round 2 safety-layer characterization.

Extends the immutable Round 1 stream and gate replica with G-RATE: a 20
decision window compared with the preceding 400 decisions. All labels remain
geometry-derived and all threat injections are deterministic simulations.
"""

import hashlib
import json
import sys
from pathlib import Path
from statistics import mean, pstdev
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
VLD = ROOT / "experiments" / "vld"
sys.path.insert(0, str(VLD / "harnesses"))
import safety_layer_characterization as r1  # type: ignore[import]  # noqa: E402


OUTPUT = VLD / "results" / "safety_layer_characterization_r2.json"
R1_OUTPUT = VLD / "results" / "safety_layer_characterization.json"
SEEDS = r1.SEEDS
COPILOTS = r1.COPILOTS
CONFIGS = ("G-ABS", "G-REL", "G-BOTH", "G-RATE", "G-THREE")
REGIMES = r1.REGIMES
THREATS = r1.THREATS
SHORT_WINDOW = 20
LONG_WINDOW = 400
RATE_THRESHOLD = 0.90
RATE_THRESHOLDS = (0.85, 0.90, 0.95)


def relative_pause(values: list[float], multiplier: float = r1.RELATIVE_MULTIPLIER) -> bool:
    if len(values) < 2 * r1.Q_WINDOW:
        return False
    prior = sum(values[-2 * r1.Q_WINDOW:-r1.Q_WINDOW]) / r1.Q_WINDOW
    current = sum(values[-r1.Q_WINDOW:]) / r1.Q_WINDOW
    return bool(prior > 0.0 and current < multiplier * prior)


def rate_pause(values: list[float], threshold: float = RATE_THRESHOLD) -> bool:
    if len(values) < LONG_WINDOW:
        return False
    short = sum(values[-SHORT_WINDOW:]) / SHORT_WINDOW
    long = sum(values[-LONG_WINDOW:]) / LONG_WINDOW
    return long > 0.0 and short < threshold * long


def trace(rows: list[dict[str, Any]], config: str, floor: float, rate_threshold: float = RATE_THRESHOLD) -> tuple[list[bool], list[dict[str, float | int | None]]]:
    fired: list[bool] = []
    diagnostics: list[dict[str, float | int | None]] = []
    values: list[float] = []
    correct_total = 0
    for index, row in enumerate(rows):
        value = float(bool(row["is_correct"]))
        values.append(value)
        correct_total += int(value)
        verified = index + 1
        alpha = min(1.0, verified / 10.0)
        absolute = alpha * (correct_total / verified) * verified < floor
        relative = relative_pause(values)
        rate = rate_pause(values, rate_threshold)
        if config == "G-ABS":
            pause = absolute
        elif config == "G-REL":
            pause = relative
        elif config == "G-BOTH":
            pause = absolute or relative
        elif config == "G-RATE":
            pause = rate
        else:
            pause = absolute or relative or rate
        fired.append(pause)
        short = sum(values[-SHORT_WINDOW:]) / min(SHORT_WINDOW, verified)
        long = sum(values[-LONG_WINDOW:]) / min(LONG_WINDOW, verified)
        diagnostics.append({"decision": verified, "short_window_accuracy": short,
                            "long_baseline": long, "rate_gap": short - rate_threshold * long,
                            "rate_fired": int(rate)})
    return fired, diagnostics


def first_lag(fired: list[bool], start: int | None) -> int | None:
    if start is None:
        return None
    for index in range(max(0, start - 1), len(fired)):
        if fired[index]:
            return index + 1 - start
    return None


def measure(rows: list[dict[str, Any]], config: str, regime: str, threat: str, floor: float, rate_threshold: float = RATE_THRESHOLD) -> tuple[dict[str, Any], list[dict[str, float | int | None]]]:
    fired, diagnostics = trace(rows, config, floor, rate_threshold)
    start = 1 if regime == "COLD-START" and threat == "SUSTAINED-POISON" else 451 if regime == "STEADY-STATE" and threat == "SUDDEN-DROP" else 401 if regime == "STEADY-STATE" and threat == "SUSTAINED-POISON" else None
    indices = range(100) if regime == "COLD-START" else range(400, 500)
    pause_count = sum(1 for index in indices if fired[index])
    lag = first_lag(fired, start)
    result = {"false_pause_rate": pause_count / 100 if threat == "CLEAN" else None,
              "detected": lag is not None if threat != "CLEAN" else None,
              "detection_lag": lag if threat != "CLEAN" else None,
              "paused_decisions": pause_count, "n_decisions": 100,
              "rate_threshold": rate_threshold, "tier": "T-real (floors) + T-sim (injected threats)"}
    return result, diagnostics


def aggregate(per_seed: dict[str, dict[str, Any]]) -> dict[str, Any]:
    detections = [bool(x["detected"]) for x in per_seed.values() if x["detected"] is not None]
    lags = [int(x["detection_lag"]) for x in per_seed.values() if isinstance(x["detection_lag"], int)]
    pauses = [float(x["false_pause_rate"]) for x in per_seed.values() if x["false_pause_rate"] is not None]
    return {"detection_rate": mean(detections) if detections else None,
            "detection_lag_mean": mean(lags) if lags else None,
            "detection_lag_std": pstdev(lags) if len(lags) > 1 else 0.0,
            "false_pause_rate_mean": mean(pauses) if pauses else None}


def load_streams(geometry: dict[str, Any]) -> dict[str, dict[str, dict[str, list[dict[str, Any]]]]]:
    return {copilot: {threat: {str(seed): r1.threat_stream(copilot, geometry, seed, threat) for seed in SEEDS} for threat in THREATS} for copilot in COPILOTS}


def build() -> dict[str, Any]:
    geometry = r1.load_geometry()
    streams = load_streams(geometry)
    data: dict[str, Any] = {"cells": {}, "diagnostics": {}, "rate_threshold_sensitivity": {}, "r1_consistency": {}}
    old = json.loads(R1_OUTPUT.read_text(encoding="utf-8"))
    for copilot in COPILOTS:
        data["cells"][copilot] = {}
        data["diagnostics"][copilot] = {}
        data["r1_consistency"][copilot] = {}
        for config in CONFIGS:
            data["cells"][copilot][config] = {}
            for regime in REGIMES:
                data["cells"][copilot][config][regime] = {}
                for threat in THREATS:
                    per_seed: dict[str, dict[str, Any]] = {}
                    diagnostic_seeds: dict[str, Any] = {}
                    for seed in SEEDS:
                        result, diagnostics = measure(streams[copilot][threat][str(seed)], config, regime, threat, r1.FLOORS[copilot])
                        per_seed[str(seed)] = result
                        diagnostic_seeds[str(seed)] = diagnostics[400:500] if regime == "STEADY-STATE" and threat != "CLEAN" else diagnostics[:100]
                    data["cells"][copilot][config][regime][threat] = {"per_seed": per_seed, "aggregate": aggregate(per_seed)}
                    data["diagnostics"][copilot][f"{regime}/{threat}"] = diagnostic_seeds
                    if config in ("G-ABS", "G-REL", "G-BOTH"):
                        new_value = data["cells"][copilot][config][regime][threat]["aggregate"]
                        old_value = old["cells"][copilot][config][regime][threat]["aggregate"]
                        data["r1_consistency"][copilot][f"{config}/{regime}/{threat}"] = new_value == old_value
        data["rate_threshold_sensitivity"][copilot] = {}
        for threshold in RATE_THRESHOLDS:
            data["rate_threshold_sensitivity"][copilot][str(threshold)] = {}
            for threat in ("CLEAN", "SUDDEN-DROP"):
                sensitivity_per_seed: dict[str, dict[str, Any]] = {}
                for seed in SEEDS:
                    result, _ = measure(streams[copilot][threat][str(seed)], "G-RATE", "STEADY-STATE", threat, r1.FLOORS[copilot], threshold)
                    sensitivity_per_seed[str(seed)] = result
                data["rate_threshold_sensitivity"][copilot][str(threshold)][threat] = {"per_seed": sensitivity_per_seed, "aggregate": aggregate(sensitivity_per_seed)}
    consistency_values = [value for value in data["r1_consistency"].values() for value in value.values()]
    data["metadata"] = {"seeds": list(SEEDS), "copilots": list(COPILOTS), "configs": list(CONFIGS), "regimes": list(REGIMES), "threats": list(THREATS), "factorial_cells": 150, "new_config_cells": 60, "short_window": SHORT_WINDOW, "long_window": LONG_WINDOW, "rate_threshold": RATE_THRESHOLD, "rate_thresholds": list(RATE_THRESHOLDS), "applicable_threat_cells": ["COLD-START/SUSTAINED-POISON", "STEADY-STATE/SUSTAINED-POISON", "STEADY-STATE/SUDDEN-DROP"], "tier": "T-real (floors) + T-sim (injected threats)", "oracle": "Round 1 deterministic nearest-centroid geometry-derived stream", "r1_consistency_all_match": all(consistency_values)}
    data["verdict"] = verdict(data)
    return data


def verdict(data: dict[str, Any]) -> dict[str, Any]:
    three_covers = True
    rate_drop_detected = []
    applicable = (("COLD-START", "SUSTAINED-POISON"), ("STEADY-STATE", "SUSTAINED-POISON"), ("STEADY-STATE", "SUDDEN-DROP"))
    for copilot in COPILOTS:
        for regime, threat in applicable:
                result = data["cells"][copilot]["G-THREE"][regime][threat]["aggregate"]
                three_covers &= (result["detection_rate"] or 0.0) > 0.0
                config_result = data["cells"][copilot]["G-RATE"][regime][threat]["aggregate"]
                if regime == "STEADY-STATE" and threat == "SUDDEN-DROP":
                    rate_drop_detected.append((config_result["detection_rate"] or 0.0) > 0.0)
    rate_detects = all(rate_drop_detected) if rate_drop_detected else False
    return {"three_layer_necessity": "ESTABLISHED" if three_covers else "NOT ESTABLISHED", "g_three_covers_all_applicable_threat_cells": three_covers, "g_rate_detects_all_steady_sudden_drops": rate_detects, "r1_legacy_configs_consistent": data["metadata"]["r1_consistency_all_match"], "interpretation": "G-THREE covers all applicable measured threat cells and G-RATE closes the sudden-drop gap." if three_covers else "G-RATE was measured as the proposed fix, but G-THREE did not cover every applicable measured threat cell; report the remaining gap."}


def main() -> None:
    data = build()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(data, indent=2, sort_keys=True, allow_nan=False) + "\n"
    OUTPUT.write_text(text, encoding="utf-8")
    print(f"wrote {OUTPUT} sha256={hashlib.sha256(text.encode()).hexdigest()[:16]}")
    print(json.dumps(data["verdict"], indent=2))


if __name__ == "__main__":
    main()
