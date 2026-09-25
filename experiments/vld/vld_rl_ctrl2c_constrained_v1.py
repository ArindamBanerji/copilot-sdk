"""Gate report for RL-CTRL-2C.

Pre-registration:
    DEPLOYABLE iff a constrained controller satisfies clean-pause <= 5%,
    poison detection >= B0, and retains at least half of B2-soft's quality
    gain in at least two of three seeds for both copilots.  Otherwise report
    TRADEOFF or INFEASIBLE only after a valid lambda sweep.

This deliverable intentionally does not run a fabricated sweep.  The CTRL-2
harness has no reward/constraint injection point and its K store is recreated
inside the decision loop.  Under the instruction to reuse that harness and
not rebuild or modify source, a valid RL-CTRL-2C comparison is unavailable.
Tier: REAL_COMPONENT geometry + GEOMETRY-DERIVED / SIMULATED.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
RESULTS = ROOT / "experiments" / "vld" / "results"
SOURCE = ROOT / "experiments" / "vld" / "vld_rl_ctrl_enrichment_v1.py"
REFERENCE = RESULTS / "rl_ctrl_enrichment.json"
OUTPUT = RESULTS / "rl_ctrl2c_constrained_enrichment.json"
SUMMARY = RESULTS / "rl_ctrl2c_constrained_enrichment_summary.md"

LAMBDAS = [0, 0.5, 1, 2, 5, 10, 20, 50]
SEEDS = [42, 123, 7]
FLOORS = {"s2p": 0.769, "soc": 0.764}


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise TypeError(f"Expected object in {path}")
    return value


def source_facts() -> dict[str, str]:
    text = SOURCE.read_text(encoding="utf-8")
    return {
        "reward": "train_policy hard-codes informative_reads/total_reads - .035*b; no lambda or violation input",
        "constraint": "pause(history) is len(history) >= 20 and last-20 accuracy < .60; it is not the R1 per-domain floor",
        "poison": "run_arm counts synthetic windows where n%400 is in 1..20; this is not the Stage 2 poison protocol",
        "persistence": "run_arm constructs h.KUtilityStore(h.SQLiteDecisionStore(), ...) inside each decision before reward_learning_store",
        "source_bytes": str(len(text.encode("utf-8"))),
    }


def main() -> None:
    reference = load_json(REFERENCE)
    facts = source_facts()
    soft: dict[str, Any] = {}
    for copilot in ("s2p", "soc"):
        copilot_data = reference.get(copilot, {})
        if isinstance(copilot_data, dict):
            soft[copilot] = {
                arm: copilot_data.get(arm, {}).get("aggregate", {})
                for arm in ("B0_fixed", "B2_learned")
            }

    payload: dict[str, Any] = {
        "status": "blocked",
        "reason": (
            "A valid lambda sweep cannot be performed under the reuse-only/no-source-change constraint: "
            "CTRL-2 train_policy hard-codes its reward, exposes no constraint-violation input, "
            "does not use the calibrated R1 floors, and run_arm recreates the KUtilityStore per decision."
        ),
        "gate_report": {
            "reward_lambda_injection": False,
            "constraint_violation_injection": False,
            "r1_floors_used_by_harness": False,
            "poison_protocol_available_in_same_loop": False,
            "source_facts": facts,
        },
        "b2_soft_reference": soft,
        "frontier": {"s2p": [], "soc": []},
        "verdict": {
            "deployable": False,
            "tradeoff": False,
            "infeasible": False,
            "rationale": "Not measured; no best lambda exists. A safety verdict would be invalid without a parameterized and persistent loop.",
            "best_lambda_s2p": None,
            "best_lambda_soc": None,
            "retained_quality_s2p": None,
            "retained_quality_soc": None,
            "conservation_both_satisfied": False,
        },
        "metadata": {
            "lambda_grid": LAMBDAS,
            "seeds": SEEDS,
            "floors": FLOORS,
            "constraint": "clean_pause <= 5% AND poison_detection >= B0",
            "pre_registered_rule": ">= half of B2-soft gain retained under constraint",
            "tier": "REAL_COMPONENT geometry + GEOMETRY-DERIVED + SIMULATED",
            "ood_caveat": "in-distribution only",
            "harness": "experiments/vld/vld_rl_ctrl_enrichment_v1.py",
            "action_mask_tested": False,
            "note": "No lambda values were evaluated; empty frontier is intentional.",
        },
    }
    RESULTS.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")

    lines = [
        "# RL-CTRL-2C — Conservation-Constrained Enrichment Controller",
        "",
        "Status: **BLOCKED / NOT MEASURED**.",
        "",
        "## Gate result",
        "",
        "The requested lambda sweep was not run because the existing CTRL-2 harness is not parameterized for it, and the task forbids rebuilding the loop or modifying source.",
        "",
        "- `train_policy()` hard-codes `informative_reads / total_reads - .035*b`; it accepts no lambda or constraint-violation term.",
        "- `pause()` uses a 20-record rolling accuracy threshold of `< 0.60`, not the calibrated R1 floors (S2P 0.769, SOC 0.764).",
        "- The poison counter is a synthetic periodic window, not the Stage 2 poison-detection protocol.",
        "- `run_arm()` constructs a new `KUtilityStore` for each decision, so updates are not persistent across the stream.",
        "",
        "## Existing B2-soft reference",
        "",
        "The prior in-distribution reference remains descriptive only:",
        "",
        "| Copilot | B0 quality | B0 clean-pause | B0 poison | B2-soft quality | B2-soft clean-pause | B2-soft poison |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for copilot in ("s2p", "soc"):
        b0 = soft.get(copilot, {}).get("B0_fixed", {})
        b2 = soft.get(copilot, {}).get("B2_learned", {})
        lines.append(
            f"| {copilot} | {b0.get('final_quality', 'n/a')} | {b0.get('clean_pause_rate', 'n/a')} | {b0.get('sustained_poison_detection', 'n/a')} | "
            f"{b2.get('final_quality', 'n/a')} | {b2.get('clean_pause_rate', 'n/a')} | {b2.get('sustained_poison_detection', 'n/a')} |"
        )
    lines.extend(
        [
            "",
            "## Frontier and decision",
            "",
            "No lambda frontier, smallest satisfying lambda, retained-quality fraction, or action-mask comparison exists because no valid constrained controller was evaluated. The result is neither DEPLOYABLE, TRADEOFF, nor INFEASIBLE; it is a blocked measurement.",
            "",
            "A source-level follow-up must first parameterize the reward/violation signal, use persistent K state, and implement the calibrated per-domain conservation and Stage 2 poison protocols. Only then can the preregistered decision rule be applied.",
            "",
            "Tier: REAL_COMPONENT geometry + GEOMETRY-DERIVED / SIMULATED. OOD caveat: any future controller result remains in-distribution unless separately validated.",
            "",
        ]
    )
    SUMMARY.write_text("\n".join(lines), encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
