"""Merge corrected Phase 3 results into the JM verification artifacts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


HERE = Path(__file__).resolve().parent
VERIFICATION = HERE / "jm_charts_verification.json"
RESULTS = HERE / "jm_phase3_results.json"
REPORT = HERE / "jm_charts_phase3_report.md"


UPDATES: dict[int, dict[str, str]] = {
    2: {
        "diagnosis": "design_flaw",
        "provenance": "REBUILT",
        "fix": "Paired retained-memory and cold-start arms on identical Person-B labels, observations, and noise, and corrected the final 300-decision window.",
        "actual": "+10.59pp retained-memory advantage; 95% CI [+10.01, +11.17]pp (60 paired trials; seed 42)",
        "status": "PASS",
    },
    6: {
        "diagnosis": "design_flaw",
        "provenance": "REBUILT",
        "fix": "Held the target stream and operator difficulty fixed across cold, partial, and warm arms; varied only centroid initialization.",
        "actual": "Transfer speed increases with similarity (Spearman rho=0.829); warm speedup reaches 1.56-1.78x for similarity 0.6-1.0 (60 paired trials/level; seed 42)",
        "status": "PASS",
    },
    7: {
        "diagnosis": "design_flaw",
        "provenance": "REBUILT",
        "fix": "Used paired target streams and measured decisions to 80% rolling accuracy for initialization-only comparisons.",
        "actual": "Warm-start speedup is 1.77x at similarity 0.6, 1.78x at 0.8, and 1.56x at 1.0 (60 paired trials/level; seed 42)",
        "status": "PASS",
    },
    9: {
        "diagnosis": "design_flaw",
        "provenance": "REBUILT",
        "fix": "Replaced the always-firing toy gate with the SDK recent-window quality rule (100 decisions, q<0.75) and routed paused cases to a fixed human-review control.",
        "actual": "Conservation improves post-change quality by +3.12 to +28.59pp across four degradation streams (100 trials; seed 42)",
        "status": "PASS",
    },
    10: {
        "diagnosis": "design_flaw",
        "provenance": "REBUILT",
        "fix": "Calibrated status transitions against a clean control using the SDK recent-window quality threshold.",
        "actual": "Clean control remains GREEN (0% false positives); degraded streams transition to PAUSED with class-dependent timing (100 trials; seed 42)",
        "status": "PASS",
    },
    11: {
        "diagnosis": "design_flaw",
        "provenance": "REBUILT",
        "fix": "Measured paired post-degradation quality with and without calibrated conservation intervention.",
        "actual": "Constrained degradation is shallower by +28.59, +22.07, +13.30, and +3.12pp; all 95% CIs exclude zero (100 trials; seed 42)",
        "status": "PASS",
    },
    12: {
        "diagnosis": "genuine_negative",
        "provenance": "REBUILT",
        "fix": "Removed clean-stream false positives with the SDK recent-window gate and evaluated four degradation classes without tuning the threshold per class.",
        "actual": "0% clean false positives; detection is 100% for personnel change, 30% corruption, and gradual drift, but 57% for sparse 10% adversarial events (100 trials; seed 42)",
        "status": "FAIL (mismatch)",
    },
    15: {
        "diagnosis": "bug",
        "provenance": "ADAPTED",
        "fix": "Computed Spearman and Kendall directly on true and learned factor values instead of correlating argsort index arrays.",
        "actual": "At 2,000 decisions: Spearman 0.440 +/-0.029, Kendall 0.352 +/-0.025, top-3 overlap 0.636 +/-0.020, cosine 0.825 +/-0.011 (95% CI half-width; 500 runs; seed 42)",
        "status": "PASS",
    },
    17: {
        "diagnosis": "genuine_negative",
        "provenance": "ADAPTED",
        "fix": "Replaced the toy loop with existing five-copilot real K-learning outputs and measured decision utility as routing quality times action accuracy.",
        "actual": "Real K-learning gains +21.96pp over frozen control at 500 decisions, but the raw utility power exponent is c=0.643 (R2=0.955), not super-linear (five deterministic copilot seeds)",
        "status": "FAIL (mismatch)",
    },
    18: {
        "diagnosis": "design_flaw",
        "provenance": "ADAPTED",
        "fix": "Used real K-learning utility and defined approved scope with the SDK recent-quality threshold q>=0.75.",
        "actual": "Eligible deployment scope expands from 3/5 to 5/5 while mean real K-learning utility rises from 0.445 to 0.618 (five deterministic copilot seeds)",
        "status": "PASS",
    },
    19: {
        "diagnosis": "design_flaw",
        "provenance": "ADAPTED",
        "fix": "Replaced the identically-zero toy metric with real mean utility multiplied by conservation-eligible deployment fraction.",
        "actual": "Combined utility-scope metric has c=1.243 with R2=0.795 and non-zero amplitude (five deterministic copilot seeds)",
        "status": "PASS",
    },
    21: {
        "diagnosis": "genuine_negative",
        "provenance": "ADAPTED",
        "fix": "Bootstrapped whole copilot deployments, recomputed utility and eligible scope, and refit the exponent in each of 2,000 resamples.",
        "actual": "Combined point estimate c=1.243; deployment-bootstrap 95% CI [0.355, 1.817] crosses c=1 (bootstrap seed 6042; 2,000 resamples)",
        "status": "FAIL (mismatch)",
    },
    22: {
        "diagnosis": "design_flaw",
        "provenance": "REBUILT",
        "fix": "Allocated independent weight arrays per entity and added a distinct hierarchical arm with a shared global prior; all arms use the same imbalanced stream.",
        "actual": "Hierarchical entity-contextualized accuracy exceeds global by +4.67pp; 95% CI [+3.90, +5.44]pp (50 paired trials; seed 42)",
        "status": "PASS",
    },
    24: {
        "diagnosis": "bug",
        "provenance": "REBUILT",
        "fix": "Sampled action-conditioned observations and updated the matching centroid cell; retained a fixed late-snapshot PCA basis for all panels.",
        "actual": "Silhouette improves from 0.257 at 50 decisions to 0.665 at 500 and 0.701 at 3,000 (seed 42)",
        "status": "PASS",
    },
}


def update_verification() -> dict[str, Any]:
    data: dict[str, Any] = json.loads(VERIFICATION.read_text(encoding="utf-8"))
    for chart in data["charts"]:
        chart_id = int(chart["id"])
        if chart_id not in UPDATES:
            continue
        update = UPDATES[chart_id]
        chart["provenance"] = update["provenance"]
        chart["code_path"] = "experiments/jm_extracted/jm_phase3_corrected.py"
        chart["execution_plan"] = "Phase 3 corrected protocol; deterministic execution followed by verification against the original claim."
        chart["design_changes"] = update["fix"]
        chart["actual_value"] = update["actual"]
        chart["pass_fail"] = update["status"]
        chart["notes"] = "Phase 3 result; no parameter tuning to the expected value."
        chart["phase3_fix"] = update["fix"]
        chart["phase3_diagnosis"] = update["diagnosis"]

    pass_count = sum(chart["pass_fail"] == "PASS" for chart in data["charts"])
    fail_count = sum(chart["pass_fail"].startswith("FAIL") for chart in data["charts"])
    blocked_count = sum(chart["pass_fail"] == "BLOCKED" for chart in data["charts"])
    provenance = {"saved_original": 0, "re_run": 0, "adapted": 0, "rebuilt": 0}
    provenance_keys = {"SAVED-ORIGINAL": "saved_original", "RE-RUN": "re_run", "ADAPTED": "adapted", "REBUILT": "rebuilt"}
    for chart in data["charts"]:
        provenance[provenance_keys[chart["provenance"]]] += 1

    data["summary"].update({
        "total_charts": 24,
        "rendered": 24,
        "pass": pass_count,
        "fail_mismatch": fail_count,
        "blocked": blocked_count,
        "provenance_breakdown": provenance,
        "phase3_summary": {
            "failed_charts_reworked": 14,
            "bugs_fixed": 2,
            "design_flaws_fixed": 9,
            "genuine_negatives": 3,
            "seed": 42,
            "bootstrap_seed": 6042,
        },
    })
    data["summary"]["design_concerns_found"].extend([
        "A calibrated SDK-style recent-window gate detects sparse 10% adversarial events in only 57% of trials.",
        "Real five-copilot K-learning utility grows sub-linearly (c=0.643) despite a +21.96pp final advantage.",
        "The combined utility-scope exponent point estimate exceeds one, but deployment-bootstrap uncertainty crosses one.",
    ])
    data["summary"]["design_changes_made"].extend([
        "Paired personnel-change and transfer arms on identical streams.",
        "Replaced the E-JM-4 toy gate with the SDK recent-window quality rule and a clean specificity control.",
        "Corrected value-based rank statistics for E-JM-5.",
        "Replaced the E-JM-6 toy loop with existing real five-copilot K-learning outputs.",
        "Bootstrapped complete deployments for E-JM-6b.",
        "Implemented independent and hierarchical entity stores for E-JM-7.",
        "Made FIGURE-2 observations action-conditioned and centroid updates cell-specific.",
    ])
    VERIFICATION.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return data


def write_report(data: dict[str, Any]) -> None:
    chart_by_id = {int(chart["id"]): chart for chart in data["charts"]}
    lines = [
        "# JM-CHARTS Phase 3 Verification Report",
        "",
        "Date: Sep 20, 2026",
        "",
        "Phase 3 reworked only the 14 Phase 2 failures. All protocols use deterministic seeds; expected values were verification targets, not tuning objectives.",
        "",
        "## Reworked charts",
        "",
        "| # | File | Diagnosis | Phase 3 correction | New result | Status |",
        "|---:|---|---|---|---|---|",
    ]
    for chart_id in UPDATES:
        chart = chart_by_id[chart_id]
        update = UPDATES[chart_id]
        lines.append(
            f"| {chart_id} | `{chart['file']}` | {update['diagnosis']} | {update['fix']} | {update['actual']} | {update['status']} |"
        )

    lines.extend([
        "",
        "## Diagnosis summary",
        "",
        "- Bugs fixed: 2 charts (#15 rank statistics; #24 action-conditioned centroid generation).",
        "- Design flaws fixed: 9 charts (#2, #6, #7, #9, #10, #11, #18, #19, #22).",
        "- Genuine negatives after correction: 3 charts (#12, #17, #21).",
        "- Final score: 21/24 PASS, 3/24 FAIL, 0 BLOCKED.",
        "",
        "## Genuine findings and paper corrections",
        "",
        "1. E-JM-4 should not claim 97-100% detection across every degradation class. At 0% clean false positives, the calibrated gate detects personnel change, 30% corruption, and gradual drift in 100% of trials, but sparse 10% adversarial events in 57%.",
        "2. E-JM-6 should not describe raw K-learning utility as super-linear. The real five-copilot trajectory is strongly improving (+21.96pp over frozen control) but sub-linear, c=0.643 (R2=0.955).",
        "3. E-JM-6b may report the combined utility-scope point estimate c=1.243, but must not call c>1 robust: the deployment-bootstrap 95% CI is [0.355, 1.817].",
        "",
        "## FIGURE-2",
        "",
        "The Phase 2 stream ignored action when generating observations. With action-conditioned geometry and cell-specific updates, fixed-basis PCA silhouettes rise from 0.257 (50 decisions) to 0.665 (500) and 0.701 (3,000). The centroids visibly differentiate; this is simulated experimental output, not a schematic.",
        "",
        "## Appendix B correction",
        "",
        "Appendix B should state: all 24 figures were rendered and checked; 21 claims pass under corrected paired/calibrated protocols. Three claims require qualification: sparse adversarial detection is 57% at 0% clean false positives; raw K-learning utility is improving but sub-linear (c=0.643); and the combined c=1.243 estimate is not statistically robust because its deployment-bootstrap 95% CI [0.355, 1.817] includes one. Seeds are 42 for rebuilt simulations, 6042 for the deployment bootstrap, and the real K-learning trajectories retain their five recorded seeds.",
        "",
        "## Seeds and confidence intervals",
        "",
        "- Rebuilt paired simulations: seed 42; trial-level 95% t intervals.",
        "- E-JM-5: seed 42; 500 runs; 95% t intervals.",
        "- E-JM-6: recorded copilot seeds 20260912, 20261657, 20261988, 20261237, 20261189.",
        "- E-JM-6b: bootstrap seed 6042; 2,000 whole-deployment resamples; percentile 95% CI.",
    ])
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    results: dict[str, Any] = json.loads(RESULTS.read_text(encoding="utf-8"))
    if set(results) != {"E-JM-1", "E-JM-3", "E-JM-4", "E-JM-5", "E-JM-6", "E-JM-7", "FIGURE-2"}:
        raise ValueError("Phase 3 results are incomplete")
    data = update_verification()
    write_report(data)
    print(json.dumps(data["summary"], indent=2))


if __name__ == "__main__":
    main()
