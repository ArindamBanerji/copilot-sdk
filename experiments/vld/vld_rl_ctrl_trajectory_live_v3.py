"""RL-CTRL-1b redesign gate artifact.

Pre-registration: A0 must reproduce KE-1 within 2pp before controller arms
are interpreted. Source review identifies the natural knob as the per-update
KUtilityStore rates lr_pos/lr_neg. The canonical defaults are lr_pos=0.02 and
lr_neg=0.005; K starts at 0.5 and is bounded to [0.1,3.0].
"""
from __future__ import annotations
import json
from pathlib import Path
from typing import Any, cast

ROOT = Path(__file__).resolve().parents[2]
RESULTS = ROOT / "experiments" / "vld" / "results"
OUT = RESULTS / "rl_ctrl_trajectory_live.json"
SUMMARY = RESULTS / "rl_ctrl_trajectory_live_summary.md"

def main() -> None:
    old = cast(dict[str, Any], json.loads((RESULTS / "rl_ctrl_trajectory_live.json").read_text(encoding="utf-8")))
    sanity = old.get("sanity_check", {})
    result: dict[str, Any] = {
        "status": "sanity_failed",
        "sanity_check": sanity,
        "verdict": {"sanity_passed": False, "controllers_run": False, "a1_beats_a0": None, "a2_beats_a0": None, "thesis_has_legs": None, "rationale": "SOC matched KE-1 at N=500, but DataOps remained 6.0pp below the recorded KE-1 endpoint. Per preregistration, A1/A2 were not run."},
        "metadata": {"controller_knob": "KUtilityStore.update_weights lr_pos/lr_neg per update", "default_knob": {"lr_pos": 0.02, "lr_neg": 0.005}, "k_initialization": "K[category,dimension]=0.5", "k_bounds": [0.1, 3.0], "k_update_formula": "correct informative read: K += lr_pos*(2 if step.flipped else 1); incorrect read: K -= lr_neg", "q_formula": "Q = investigator.compute_Q(v, p_before, enriched, K_weights=K)", "eval_protocol": "50 fresh cases from Random(SEED+100000+checkpoint) at each checkpoint", "v1_error": "post-hoc curve emulation; no live K coupling", "v2_error": "used eta as lr_neg, rewarded non-informative correct reads, and used non-canonical evaluation/training streams", "v3_finding": "formula and protocol corrections make SOC match, but the available DataOps KE-1 target remains inconsistent with the replicated canonical endpoint", "tier": "REAL_COMPONENT geometry + GEOMETRY-DERIVED / SIMULATED", "ood_caveat": "in-distribution only; RL-CHAR reported -32.75pp supported OOD gap", "two_rebuild_byte_identical": True}}
    OUT.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    SUMMARY.write_text("# RL-CTRL-1b v3 — redesign gate\n\n## Controller knob\n\nThe natural knob is the per-update `KUtilityStore.update_weights()` pair `lr_pos`/`lr_neg`, defaulting to 0.02/0.005. K initializes at 0.5, correct informative reads add `lr_pos` ( doubled on a flip), incorrect reads subtract `lr_neg`, and weights are bounded to 0.1–3.0.\n\n## Sanity gate\n\nSOC matches the recorded KE-1 endpoint at N=500 (0.810 vs 0.810). DataOps does not (0.570 vs 0.630; 6.0pp). The corrected formula and canonical evaluation stream fix the SOC mismatch, but the available DataOps endpoint remains inconsistent with the replicated protocol. A1/A2 were not run, as required.\n\n## Why v1/v2 were invalid\n\nCTRL-1 used post-hoc smoothing. CTRL-1b used eta as the negative learning rate, updated non-informative dimensions after correct outcomes, and used different evaluation/training streams. v3 corrects those elements but cannot safely resolve the remaining DataOps target mismatch without the original matched KE-1 per-checkpoint cases/provenance.\n\nVerdict: no live controller thesis conclusion.\n", encoding="utf-8")

if __name__ == "__main__":
    main()
