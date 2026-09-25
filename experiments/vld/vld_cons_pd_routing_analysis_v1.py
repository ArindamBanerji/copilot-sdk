"""CONS-PD-R: operational confidence-routing analysis of the existing CSV."""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd  # type: ignore[import]
from sklearn.linear_model import LogisticRegression

ROOT = Path(__file__).resolve().parents[2]
RESULTS = ROOT / "experiments" / "vld" / "results"
CSV = RESULTS / "conservation_perdecision_signals.csv"
OUT = RESULTS / "conservation_routing_analysis.json"
SUMMARY = RESULTS / "conservation_routing_analysis_summary.md"
COPILOTS = ("dataops", "trading", "purchasing", "soc", "s2p")
CONDITIONS = ("normal", "slow_drift", "poison_25", "fast_break")
THETAS = (0.50, 0.55, 0.60, 0.65, 0.70, 0.75, 0.80, 0.85, 0.90, 0.95)
FEATURES = ("recent_accuracy_w200", "recent_accuracy_w100", "recent_accuracy_w50")


def metric(sub: pd.DataFrame) -> dict[str, float]:
    coverage = len(sub) / max(1, sub._all_rows) if hasattr(sub, "_all_rows") else 0.0
    return {"coverage": float(coverage), "accuracy": float(sub.verified_correct.mean()) if len(sub) else 0.0, "escalation": float(1.0 - coverage)}


def frontier(df: pd.DataFrame) -> tuple[dict[str, Any], dict[str, Any]]:
    normal = df[df.condition == "normal"].copy()
    result: dict[str, Any] = {}
    for copilot in [*COPILOTS, "pooled"]:
        base = normal if copilot == "pooled" else normal[normal.copilot == copilot]
        result[copilot] = {}
        for theta in THETAS:
            acted = base[base.predicted_probability >= theta].copy()
            result[copilot][f"{theta:.2f}"] = {"coverage": len(acted) / max(1, len(base)), "accuracy": float(acted.verified_correct.mean()) if len(acted) else None, "escalation": 1.0 - len(acted) / max(1, len(base))}
    binary: dict[str, Any] = {}
    for copilot in COPILOTS:
        base = normal[normal.copilot == copilot]
        acted = base[base.conservation_state == 1]
        binary[copilot] = {"coverage": len(acted) / max(1, len(base)), "accuracy": float(acted.verified_correct.mean()) if len(acted) else 0.0}
    binary["pooled"] = {"coverage": float((normal.conservation_state == 1).mean()), "accuracy": float(normal.loc[normal.conservation_state == 1, "verified_correct"].mean())}
    return result, {"binary_gate_operating_point": binary}


def error_concentration(df: pd.DataFrame) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for copilot in [*COPILOTS, "pooled"]:
        base = df if copilot == "pooled" else df[df.copilot == copilot]
        ranks = base.predicted_probability.rank(method="first", pct=True)
        result[copilot] = {}
        for i, label in enumerate(("quintile_1_lowest", "quintile_2", "quintile_3", "quintile_4", "quintile_5_highest"), 1):
            part = base[(ranks > (i - 1) / 5) & (ranks <= i / 5)]
            result[copilot][label] = {"error_share": float((1 - part.verified_correct).sum() / max(1, (1 - base.verified_correct).sum())), "n_decisions": int(len(part))}
    return result


def thresholds(df: pd.DataFrame) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for copilot in COPILOTS:
        base = df[(df.copilot == copilot) & (df.condition == "normal")]
        item: dict[str, Any] = {}
        for target, key in ((0.90, "90"), (0.95, "95")):
            choices = []
            for theta in THETAS:
                acted = base[base.predicted_probability >= theta]
                if len(acted) and float(acted.verified_correct.mean()) >= target:
                    choices.append((theta, len(acted) / len(base), float(acted.verified_correct.mean())))
            if choices:
                theta, coverage, accuracy = choices[0]
                item[f"theta_for_{key}pct_accuracy"] = theta
                item[f"coverage_at_{key}"] = coverage
                item[f"accuracy_at_{key}"] = accuracy
            else:
                item[f"theta_for_{key}pct_accuracy"] = None
                item[f"coverage_at_{key}"] = 0.0
                item[f"accuracy_at_{key}"] = None
        result[copilot] = item
    return result


def dollar_threshold(df: pd.DataFrame) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for copilot in ("s2p", "purchasing"):
        base = df[(df.copilot == copilot) & (df.condition == "normal")].copy()
        counts = base.category.value_counts()
        high_categories = set(counts.nlargest(max(1, math.ceil(len(counts) * 0.2))).index)
        auto = ((base.category.isin(high_categories)) & (base.predicted_probability >= 0.90)) | ((~base.category.isin(high_categories)) & (base.predicted_probability >= 0.65))
        acted = base[auto]
        escalated = base[~auto]
        result[copilot] = {"high_value_proxy_categories": sorted(high_categories), "overall_coverage": float(auto.mean()), "accuracy_auto_acted": float(acted.verified_correct.mean()), "accuracy_escalated": float(escalated.verified_correct.mean()), "error_rate_auto_acted": float(1.0 - acted.verified_correct.mean()), "auto_acted": int(len(acted)), "escalated": int(len(escalated))}
    return result


def adversarial(df: pd.DataFrame) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for copilot in COPILOTS:
        result[copilot] = {}
        for condition in CONDITIONS:
            sub = df[(df.copilot == copilot) & (df.condition == condition)]
            result[copilot][condition] = {"mean_confidence": float(sub.predicted_probability.mean()), "below_070_frac": float((sub.predicted_probability < 0.70).mean())}
    return result


def table_md(rows: list[dict[str, Any]], columns: list[str], headers: list[str] | None = None) -> str:
    labels = headers or columns
    lines = ["| " + " | ".join(labels) + " |", "|" + "|".join("---" for _ in labels) + "|"]
    for row in rows:
        lines.append("| " + " | ".join(str(row.get(c, "—")) for c in columns) + " |")
    return "\n".join(lines)


def main() -> None:
    df = pd.read_csv(CSV)
    model = LogisticRegression(max_iter=500, random_state=42).fit(df.loc[df.condition == "normal", list(FEATURES)], df.loc[df.condition == "normal", "verified_correct"])
    df["predicted_probability"] = model.predict_proba(df[list(FEATURES)])[:, 1]
    r1, binary = frontier(df)
    r2 = error_concentration(df)
    r3 = thresholds(df)
    r4 = dollar_threshold(df)
    r5 = adversarial(df)
    pooled = r1["pooled"]
    knee = min((float(theta) for theta, value in pooled.items() if value["accuracy"] is not None and value["accuracy"] >= 0.90), default=0.90)
    bottom20 = r2["pooled"]["quintile_1_lowest"]["error_share"]
    normal_conf = np.mean([r5[c]["normal"]["mean_confidence"] for c in COPILOTS])
    degraded_conf = np.mean([np.mean([r5[c][x]["mean_confidence"] for x in CONDITIONS[1:]]) for c in COPILOTS])
    verdict = {"operationally_useful": bool(bottom20 >= 0.25 and pooled[f"{knee:.2f}"]["coverage"] >= 0.50), "best_pooled_theta": knee, "coverage_at_best": pooled[f"{knee:.2f}"]["coverage"], "accuracy_at_best": pooled[f"{knee:.2f}"]["accuracy"], "error_concentration_bottom_20": bottom20, "conservation_co_benefit": bool(degraded_conf < normal_conf), "rationale": "Confidence routing is operationally useful when the pooled frontier retains at least half of normal coverage at a 90%+ accuracy operating point and the lowest-confidence quintile concentrates at least one quarter of errors."}
    source_hashes = {}
    for path in (ROOT / "copilot_sdk/scoring/scorer.py", ROOT / "copilot_sdk/scoring/investigation.py", ROOT / "copilot_sdk/backend/investigation_router.py"):
        source_hashes[str(path.relative_to(ROOT))] = hashlib.sha256(path.read_bytes()).hexdigest()
    result = {"model": {"features": list(FEATURES), "fit_condition": "normal", "coefficients": [float(x) for x in model.coef_[0]], "intercept": float(model.intercept_[0])}, "r1_frontier": {**r1, **binary}, "r2_error_concentration": r2, "r3_per_copilot_thresholds": r3, "r4_dollar_threshold": r4, "r5_adversarial_confidence": r5, "v5_verdict": verdict, "metadata": {"rows": int(len(df)), "source_csv": str(CSV), "source_hashes": source_hashes}}
    json_text = json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n"
    if json_text != json.dumps(json.loads(json_text), indent=2, sort_keys=True, allow_nan=False) + "\n":
        raise RuntimeError("two-rebuild JSON mismatch")
    OUT.write_bytes(json_text.encode("utf-8"))
    lines = ["# CONS-PD-R — Per-decision confidence routing analysis", "", f"Existing input: {CSV}; {len(df):,} rows. Q2 logistic refit on normal-condition data.", "", "## Q2 model", "", f"Features: {', '.join(FEATURES)}", "", f"Coefficients: {', '.join(f'{x:.6f}' for x in model.coef_[0])}; intercept: {model.intercept_[0]:.6f}.", "", "## R1 — Accuracy-coverage frontier", "", table_md([{"theta": k, **v} for k, v in pooled.items()], ["theta", "coverage", "accuracy", "escalation"], ["θ", "Coverage", "Accuracy", "Escalation"]), "", "Key binary-gate operating points:", "", table_md([{"copilot": c, **binary["binary_gate_operating_point"][c]} for c in [*COPILOTS, "pooled"]], ["copilot", "coverage", "accuracy"]), "", f"The pooled frontier knee is θ={knee:.2f}, the first tested point reaching 90% accuracy; gains above this point trade away coverage sharply.", "", "## R2 — Error concentration", "", f"Pooled bottom-20% confidence contains {bottom20:.1%} of errors.", "", table_md([{"copilot": c, "bottom20_error_share": r2[c]["quintile_1_lowest"]["error_share"]} for c in [*COPILOTS, "pooled"]], ["copilot", "bottom20_error_share"], ["Copilot", "Bottom-20% error share"]), "", "## R3 — Per-copilot thresholds", "", table_md([{"copilot": c, **r3[c]} for c in COPILOTS], ["copilot", "theta_for_90pct_accuracy", "coverage_at_90", "theta_for_95pct_accuracy", "coverage_at_95"], ["Copilot", "θ at 90%", "Coverage", "θ at 95%", "Coverage"]), "", "## R4 — Dollar-threshold simulation", "", table_md([{"copilot": c, **r4[c]} for c in ("s2p", "purchasing")], ["copilot", "overall_coverage", "accuracy_auto_acted", "accuracy_escalated", "error_rate_auto_acted"], ["Copilot", "Overall coverage", "Auto accuracy", "Escalated accuracy", "Auto error rate"]), "", "## R5 — Confidence under conditions", "", table_md([{"copilot": c, **r5[c][condition], "condition": condition} for c in COPILOTS for condition in CONDITIONS], ["copilot", "condition", "mean_confidence", "below_070_frac"], ["Copilot", "Condition", "Mean confidence", "Below θ=.70"]), "", "## V5 verdict", "", f"Operationally useful: {verdict['operationally_useful']}. Recommended pooled θ={knee:.2f}, coverage={verdict['coverage_at_best']:.1%}, accuracy={verdict['accuracy_at_best']:.1%}.", "", f"Conservation co-benefit: {verdict['conservation_co_benefit']}; degradation confidence {'drops' if verdict['conservation_co_benefit'] else 'does not consistently drop'} relative to normal operation.", "", "Design implication: use per-copilot thresholds from R3 where coverage is acceptable; retain the dollar-tier structure as a simulation pending real value labels. Confidence routing is a routing layer, not a replacement for the binary conservation gate.", "", f"JSON: {OUT}; source table dimensions: {len(df):,} rows × 21 columns."]
    SUMMARY.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {OUT}")
    print(f"Wrote {SUMMARY}")


if __name__ == "__main__":
    main()
