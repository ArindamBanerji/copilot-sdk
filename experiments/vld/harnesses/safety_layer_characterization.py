from __future__ import annotations

"""A1 safety-layer characterization.

The stream labels come from the existing geometry-derived conservation stream.
Threats are deterministic label injections layered on top of that stream. The
gate is an analysis replica with the deployed 100-record relative window and
0.7 multiplier; production source files are not changed or called mutably.
"""

import hashlib
import json
import random
from pathlib import Path
from statistics import mean, pstdev
from typing import Any, cast


ROOT = Path(__file__).resolve().parents[3]
VLD = ROOT / "experiments" / "vld"


OUTPUT = VLD / "results" / "safety_layer_characterization.json"
SEEDS = (42, 123, 7)
COPILOTS = ("soc", "dataops", "s2p", "trading", "purchasing")
CONFIGS = ("G-ABS", "G-REL", "G-BOTH")
REGIMES = ("COLD-START", "STEADY-STATE")
THREATS = ("CLEAN", "SUSTAINED-POISON", "SUDDEN-DROP")
FLOORS = {"soc": 0.764, "s2p": 0.769, "trading": 0.766, "purchasing": 0.655, "dataops": 0.669}
Q_WINDOW = 100
RELATIVE_MULTIPLIER = 0.7
TOTAL = 500


def load_geometry() -> dict[str, Any]:
    payload = json.loads((ROOT / "real_centroids_v1.json").read_text(encoding="utf-8"))
    return cast(dict[str, Any], payload["copilots"])


def base_stream(copilot: str, geometry: dict[str, Any], seed: int) -> list[dict[str, Any]]:
    domain = geometry[copilot]
    rng = random.Random(seed)
    categories = list(domain["category_names"])
    mus = cast(dict[str, list[list[float]]], domain["all_category_mu"])
    rows: list[dict[str, Any]] = []
    for decision in range(1, TOTAL + 1):
        category = rng.choice(categories)
        centroids = mus[category]
        true_action = rng.randrange(len(centroids))
        vector = [max(0.0, min(1.0, float(value) + rng.gauss(0.0, 0.06))) for value in centroids[true_action]]
        distances = [sum((vector[index] - float(value)) ** 2 for index, value in enumerate(center)) for center in centroids]
        oracle_action = min(range(len(distances)), key=distances.__getitem__)
        recommended_action = oracle_action if rng.random() < 0.90 else rng.randrange(len(centroids))
        rows.append({"decision": decision, "category": category, "is_correct": recommended_action == oracle_action, "factor_vector": vector})
    return rows


def threat_stream(copilot: str, geometry: dict[str, Any], seed: int, threat: str) -> list[dict[str, Any]]:
    rows = base_stream(copilot, geometry, seed)
    rng = random.Random(seed + 910_000 + sum(ord(ch) for ch in threat))
    for row in rows:
        decision = int(row["decision"])
        probability = 0.0
        if threat == "SUSTAINED-POISON" and 401 <= decision <= 500:
            probability = 0.20
        elif threat == "SUDDEN-DROP" and 451 <= decision <= 500:
            probability = 0.15
        if probability and rng.random() < probability:
            row["is_correct"] = not bool(row["is_correct"])
    return rows


def abs_pause(records: list[dict[str, Any]], floor: float) -> bool:
    v = len(records)
    if v == 0:
        return True
    q = mean(float(row["is_correct"]) for row in records)
    # Category coverage is not available as a production counter in this
    # isolated stream, so use the documented cold-start coverage ramp.
    alpha = min(1.0, v / 10.0)
    return alpha * q * v < floor


def rel_pause(records: list[dict[str, Any]], multiplier: float = RELATIVE_MULTIPLIER) -> bool:
    if len(records) < 2 * Q_WINDOW:
        return False
    prior = mean(float(row["is_correct"]) for row in records[-2 * Q_WINDOW:-Q_WINDOW])
    current = mean(float(row["is_correct"]) for row in records[-Q_WINDOW:])
    return prior > 0.0 and current < multiplier * prior


def gate_pause(records: list[dict[str, Any]], config: str, floor: float, multiplier: float = RELATIVE_MULTIPLIER) -> bool:
    absolute = abs_pause(records, floor)
    relative = rel_pause(records, multiplier)
    if config == "G-ABS":
        return absolute
    if config == "G-REL":
        return relative
    return absolute or relative


def trace(rows: list[dict[str, Any]], config: str, floor: float, multiplier: float = RELATIVE_MULTIPLIER) -> list[bool]:
    fired: list[bool] = []
    correct_total = 0
    values: list[float] = []
    for index, row in enumerate(rows):
        value = float(bool(row["is_correct"]))
        values.append(value)
        correct_total += int(value)
        verified = index + 1
        alpha = min(1.0, verified / 10.0)
        absolute = alpha * (correct_total / verified) * verified < floor
        relative = False
        if verified >= 2 * Q_WINDOW:
            prior = sum(values[-2 * Q_WINDOW:-Q_WINDOW]) / Q_WINDOW
            current = sum(values[-Q_WINDOW:]) / Q_WINDOW
            relative = prior > 0.0 and current < multiplier * prior
        fired.append(absolute if config == "G-ABS" else relative if config == "G-REL" else absolute or relative)
    return fired


def first_lag(fired: list[bool], start: int | None) -> int | None:
    if start is None:
        return None
    for index in range(max(0, start - 1), len(fired)):
        if fired[index]:
            return index + 1 - start
    return None


def v_clear(rows: list[dict[str, Any]], floor: float) -> int:
    records: list[dict[str, Any]] = []
    streak = 0
    for row in rows:
        records.append(row)
        if not abs_pause(records, floor):
            streak += 1
            if streak >= 3:
                return len(records) - 2
        else:
            streak = 0
    return len(rows)


def cell(rows: list[dict[str, Any]], config: str, regime: str, threat: str, floor: float) -> dict[str, Any]:
    fired = trace(rows, config, floor)
    start = 1 if regime == "COLD-START" and threat == "SUSTAINED-POISON" else 451 if regime == "STEADY-STATE" and threat == "SUDDEN-DROP" else 401 if regime == "STEADY-STATE" and threat == "SUSTAINED-POISON" else None
    window = range(0, 100) if regime == "COLD-START" else range(400, 500)
    pauses = sum(1 for index in window if fired[index])
    lag = first_lag(fired, start)
    return {"false_pause_rate": pauses / 100 if threat == "CLEAN" else None,
            "detected": lag is not None if threat != "CLEAN" else None,
            "detection_lag": lag if threat != "CLEAN" else None,
            "paused_decisions": pauses,
            "n_decisions": 100,
            "floor": floor,
            "relative_multiplier": RELATIVE_MULTIPLIER,
            "tier": "T-real (floors) + T-sim (injected threats)"}


def build() -> dict[str, Any]:
    geometry = load_geometry()
    output: dict[str, Any] = {"cells": {}, "v_clear": {}, "multiplier_sensitivity": {}}
    streams: dict[str, dict[str, dict[str, list[dict[str, Any]]]]] = {
        copilot: {
            threat: {str(seed): threat_stream(copilot, geometry, seed, threat) for seed in SEEDS}
            for threat in THREATS
        }
        for copilot in COPILOTS
    }
    for copilot in COPILOTS:
        output["cells"][copilot] = {}
        output["v_clear"][copilot] = {str(seed): v_clear(streams[copilot]["CLEAN"][str(seed)], FLOORS[copilot]) for seed in SEEDS}
        for config in CONFIGS:
            output["cells"][copilot][config] = {}
            for regime in REGIMES:
                output["cells"][copilot][config][regime] = {}
                for threat in THREATS:
                    per_seed = {str(seed): cell(streams[copilot][threat][str(seed)], config, regime, threat, FLOORS[copilot]) for seed in SEEDS}
                    detected = [bool(item["detected"]) for item in per_seed.values() if item["detected"] is not None]
                    lags = [int(item["detection_lag"]) for item in per_seed.values() if isinstance(item["detection_lag"], int)]
                    pauses = [float(item["false_pause_rate"]) for item in per_seed.values() if item["false_pause_rate"] is not None]
                    output["cells"][copilot][config][regime][threat] = {"per_seed": per_seed,
                        "aggregate": {"detection_rate": mean(detected) if detected else None,
                                      "detection_lag_mean": mean(lags) if lags else None,
                                      "detection_lag_std": pstdev(lags) if len(lags) > 1 else 0.0,
                                      "false_pause_rate_mean": mean(pauses) if pauses else None}}
        output["multiplier_sensitivity"][copilot] = {}
        for multiplier in (0.6, 0.7, 0.8):
            entries: dict[str, Any] = {}
            for threat in ("CLEAN", "SUDDEN-DROP"):
                sensitivity_seed: list[dict[str, Any]] = []
                for seed in SEEDS:
                    rows = streams[copilot][threat][str(seed)]
                    fired = trace(rows, "G-REL", FLOORS[copilot], multiplier)
                    pause_rate = sum(fired[400:500]) / 100
                    lag = first_lag(fired, 451) if threat == "SUDDEN-DROP" else None
                    sensitivity_seed.append({"false_pause_rate": pause_rate, "detection_lag": lag})
                entries[threat] = {"false_pause_rate_mean": mean(float(x["false_pause_rate"]) for x in sensitivity_seed),
                                   "detection_lag_mean": mean([int(x["detection_lag"]) for x in sensitivity_seed if x["detection_lag"] is not None]) if any(x["detection_lag"] is not None for x in sensitivity_seed) else None,
                                   "per_seed": sensitivity_seed}
            output["multiplier_sensitivity"][copilot][str(multiplier)] = entries
    output["metadata"] = {"seeds": list(SEEDS), "copilots": list(COPILOTS), "configs": list(CONFIGS), "regimes": list(REGIMES), "threats": list(THREATS), "factorial_cells": 90, "q_window": Q_WINDOW, "relative_multiplier": RELATIVE_MULTIPLIER, "floors": FLOORS, "tier": "T-real (floors) + T-sim (injected threats)", "oracle": "geometry-derived nearest-centroid labels from real_centroids_v1.json; deterministic stream generator", "gate_replica": "absolute alpha*q*V floor plus prior/current 100-record relative trigger", "two_layer_rule": "G-BOTH covers all cells and each single layer fails at least one cell covered by G-BOTH"}
    output["verdict"] = verdict(output)
    return output


def verdict(data: dict[str, Any]) -> dict[str, Any]:
    both = data["cells"]
    both_coverage = True
    abs_fail = False
    rel_fail = False
    matches = 0
    total_predictions = 15
    for copilot in COPILOTS:
        for regime in REGIMES:
            for threat in THREATS:
                b = both[copilot]["G-BOTH"][regime][threat]["aggregate"]
                a = both[copilot]["G-ABS"][regime][threat]["aggregate"]
                r = both[copilot]["G-REL"][regime][threat]["aggregate"]
                both_coverage &= threat == "CLEAN" or (b["detection_rate"] or 0.0) > 0.0
                abs_fail |= threat != "CLEAN" and (a["detection_rate"] or 0.0) < 1.0
                rel_fail |= threat != "CLEAN" and (r["detection_rate"] or 0.0) < 1.0
    established = both_coverage and abs_fail and rel_fail
    return {"two_layer_necessity": "ESTABLISHED" if established else "NOT ESTABLISHED", "g_both_covers_all_cells": both_coverage, "g_abs_fails_cell_both_covers": abs_fail, "g_rel_fails_cell_both_covers": rel_fail, "prediction_accuracy_cells": matches, "prediction_cells": total_predictions, "interpretation": "Both layers are necessary under the preregistered criterion." if established else "The preregistered two-layer criterion was not fully met; report the observed failures rather than upgrading the claim."}


def main() -> None:
    data = build()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(data, indent=2, sort_keys=True, allow_nan=False) + "\n"
    OUTPUT.write_text(text, encoding="utf-8")
    print(f"wrote {OUTPUT} sha256={hashlib.sha256(text.encode()).hexdigest()[:16]}")


if __name__ == "__main__":
    main()
