"""Deterministic EXP-AE-GATE rerun for DefaultPromotionGate.

Pre-registered acceptance target: power > 80% at a true +5pp improvement
and false-positive rate < 10% under a true 0pp improvement.  The simulated
production arm has accuracy 0.70; the candidate arm has 0.75 for power and
0.70 for FPR.  Each arm is an independent binomial shadow window, evaluated
by the production gate with GREEN conservation and zero batch variance so the
experiment isolates the gate's sample-size/statistical decision.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np

from copilot_sdk.evolution.gate import DefaultPromotionGate


ALPHA = 0.05
PRACTICAL_SIGNIFICANCE = 0.03
BASELINE_ACCURACY = 0.70
ALTERNATIVE_ACCURACY = 0.75
TRIALS = 20_000
SEED = 20260915
N_MINS = (10, 25, 50, 100, 250, 500, 750, 1_000, 1_250, 1_500, 2_000)


def _promotion_rate(n_min: int, candidate_accuracy: float, seed: int) -> float:
    """Evaluate the production gate over a deterministic binomial trial set."""
    rng = np.random.default_rng(seed)
    candidate_correct = rng.binomial(n_min, candidate_accuracy, size=TRIALS)
    baseline_correct = rng.binomial(n_min, BASELINE_ACCURACY, size=TRIALS)
    gate = DefaultPromotionGate(
        superiority_threshold_pp=PRACTICAL_SIGNIFICANCE * 100.0,
        min_shadow_decisions=n_min,
        alpha=ALPHA,
    )
    promoted = 0
    for candidate, baseline in zip(candidate_correct, baseline_correct):
        shadow_accuracy = int(candidate) / n_min
        baseline_rate = int(baseline) / n_min
        result = gate.evaluate(
            {
                "sufficient": True,
                "total": n_min,
                "correct": int(candidate),
                "baseline_correct": int(baseline),
                "accuracy": shadow_accuracy,
                "baseline_accuracy": baseline_rate,
                "batch_accuracies": [shadow_accuracy, shadow_accuracy, shadow_accuracy],
            },
            conservation_state={"status": "GREEN"},
        )
        promoted += int(result["promoted"])
    return promoted / TRIALS


def build_results() -> dict[str, Any]:
    """Build the complete result without time- or environment-dependent values."""
    results: dict[str, Any] = {}
    for n_min in N_MINS:
        results[str(n_min)] = {
            "power": _promotion_rate(n_min, ALTERNATIVE_ACCURACY, SEED + n_min),
            "fpr": _promotion_rate(n_min, BASELINE_ACCURACY, SEED + 10_000 + n_min),
            "null_trials": TRIALS,
            "alt_trials": TRIALS,
            "delta_threshold": PRACTICAL_SIGNIFICANCE,
            "alpha": ALPHA,
        }

    qualifying = [
        (int(n_min), result)
        for n_min, result in results.items()
        if result["power"] > 0.80 and result["fpr"] < 0.10
    ]
    recommendation_n_min, recommendation = qualifying[0] if qualifying else (None, None)
    payload = {
        **results,
        "baseline": {
            "gate_type": "strict_inequality",
            "power": 0.59,
            "fpr": 0.44,
            "n_min": 10,
        },
        "recommendation": {
            "n_min": recommendation_n_min,
            "power": None if recommendation is None else recommendation["power"],
            "fpr": None if recommendation is None else recommendation["fpr"],
            "meets_target": recommendation is not None,
        },
        "metadata": {
            "gate_type": "two_proportion_z_test",
            "practical_significance": PRACTICAL_SIGNIFICANCE,
            "alpha": ALPHA,
            "one_sided": True,
            "trials_per_condition": TRIALS,
            "seed": SEED,
            "protocol": "independent_binomial_shadow_windows",
            "target": "power > 0.80 and fpr < 0.10",
        },
    }
    return payload


def _canonical_bytes(payload: dict[str, Any]) -> bytes:
    return json.dumps(payload, indent=2, sort_keys=True).encode("utf-8") + b"\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("experiments/vld/results/exp_ae_gate_rerun.json"),
    )
    args = parser.parse_args()

    first = build_results()
    second = build_results()
    first_bytes = _canonical_bytes(first)
    second_bytes = _canonical_bytes(second)
    if first_bytes != second_bytes:
        raise RuntimeError("EXP-AE-GATE two-rebuild determinism check failed")
    first["metadata"]["two_rebuild_byte_identical"] = True
    first["metadata"]["payload_sha256"] = hashlib.sha256(_canonical_bytes(first)).hexdigest()

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(_canonical_bytes(first))
    print(
        "recommended n_min={n_min}, power={power}, fpr={fpr}, meets_target={meets}".format(
            n_min=first["recommendation"]["n_min"],
            power=first["recommendation"]["power"],
            fpr=first["recommendation"]["fpr"],
            meets=first["recommendation"]["meets_target"],
        )
    )


if __name__ == "__main__":
    main()
