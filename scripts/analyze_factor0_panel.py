"""Reproducible offline analysis of the SOC factor-0 judge panel."""
from __future__ import annotations

import json
import math
import sys
from collections import Counter, defaultdict
from pathlib import Path
from statistics import median
from typing import Any

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
SDK = ROOT / "copilot-sdk"
BACKEND = ROOT / "gen-ai-roi-demo-v4-v50" / "backend"
PANEL_DIR = SDK / "docs" / "design" / "factor_0_panel_data"
REPORT = SDK / "docs" / "design" / "factor0_panel_analysis_v1.md"
CATEGORIES = ["credential_access", "malware_execution", "lateral_movement", "data_exfiltration", "insider_threat", "cloud_infrastructure"]
ACTIONS = ["escalate", "investigate", "suppress", "monitor"]
FIELDS = ["user_risk_score", "user_title", "mfa_completed", "device_fingerprint_match"]
ARM_B_MAP = {
    "B-01":"SOC-IT-05","B-02":"SOC-IT-02","B-03":"SOC-CI-04","B-04":"SOC-CI-02","B-05":"SOC-IT-06","B-06":"SOC-CI-01",
    "B-07":"SOC-CA-01","B-08":"SOC-TI-05","B-09":"SOC-CI-05","B-10":"SOC-LM-04","B-11":"SOC-TI-06","B-12":"SOC-CA-02",
    "B-13":"SOC-LM-02","B-14":"SOC-TI-02","B-15":"SOC-LM-01","B-16":"SOC-TI-04","B-17":"SOC-CI-03","B-18":"SOC-DE-02",
    "B-19":"SOC-LM-03","B-20":"SOC-DE-01","B-21":"SOC-LM-05","B-22":"SOC-IT-01","B-23":"SOC-CA-06","B-24":"SOC-IT-04",
    "B-25":"SOC-DE-06","B-26":"SOC-IT-03","B-27":"SOC-DE-03","B-28":"SOC-CA-05","B-29":"SOC-DE-05","B-30":"SOC-TI-01",
    "B-31":"SOC-LM-06","B-32":"SOC-TI-03","B-33":"SOC-CI-06","B-34":"SOC-CA-04","B-35":"SOC-DE-04","B-36":"SOC-CA-03",
}


def parse_panel(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    start, end = text.find("{"), text.rfind("}")
    data = json.loads(text[start:end + 1])
    if len(data.get("determinations", [])) != 36:
        raise ValueError(f"{path.name}: expected 36 determinations")
    return data


def factor0(row: dict[str, Any]) -> float:
    values: list[float] = []
    if row.get("user_risk_score") is not None:
        values.append(max(0.0, min(float(row["user_risk_score"]), 1.0)))
    title = row.get("user_title")
    if title is not None:
        title = str(title).strip().lower()
        if title in {"admin", "root", "privileged", "service", "system", "svc"}:
            values.append(0.9)
        elif title in {"chief", "ciso", "cio", "cto", "ceo", "vp", "vice president", "director", "executive", "exec"}:
            values.append(0.7)
        else:
            values.append(0.2)
    if row.get("mfa_completed") is not None:
        values.append(0.85 if not bool(row["mfa_completed"]) else 0.10)
    if row.get("device_fingerprint_match") is not None:
        values.append(0.80 if not bool(row["device_fingerprint_match"]) else 0.10)
    return float(np.mean(values)) if values else 0.5


def iqr(values: list[float]) -> float:
    return float(np.percentile(values, 75) - np.percentile(values, 25)) if len(values) > 1 else 0.0


def majority(values: list[Any]) -> Any:
    values = [v for v in values if v is not None]
    if not values:
        return None
    counts = Counter(map(str, values)).most_common()
    if len(counts) > 1 and counts[0][1] == counts[1][1]:
        return None
    return next(v for v in values if str(v) == counts[0][0])


def ranks(values: list[float]) -> np.ndarray:
    order = np.argsort(values, kind="stable")
    out = np.empty(len(values), dtype=float)
    out[order] = np.arange(len(values), dtype=float)
    return out


def f(value: Any, digits: int = 3) -> str:
    return "-" if value is None else (f"{value:.{digits}f}" if isinstance(value, float) else str(value))


def table(headers: list[str], rows: list[list[Any]]) -> str:
    result = ["| " + " | ".join(headers) + " |", "|" + "|".join("---" for _ in headers) + "|"]
    result += ["| " + " | ".join(str(x).replace("|", "\\|") for x in row) + " |" for row in rows]
    return "\n".join(result)


def score(vector: np.ndarray, centroids: np.ndarray, category: int, tau: float = 0.1) -> tuple[int, float, float]:
    distances = np.sum((centroids[category] - vector) ** 2, axis=1)
    winner = int(np.argmin(distances))
    logits = -distances / tau
    logits -= max(logits)
    probs = np.exp(logits)
    probs /= np.sum(probs)
    sorted_distances = np.sort(distances)
    return winner, float(sorted_distances[1] - sorted_distances[0]), float(probs[winner])


def main() -> None:
    files = sorted(PANEL_DIR.glob("*.txt"))
    if len(files) != 6:
        raise ValueError(f"Expected six panel files in {PANEL_DIR}; found {len(files)}")
    rows: list[dict[str, Any]] = []
    metadata: list[dict[str, Any]] = []
    for path in files:
        data = parse_panel(path)
        prefix = path.stem.split("_arm_")[0]
        for item in data["determinations"]:
            row = dict(item)
            row.update(panel_model=prefix, declared_model=data.get("model", "?"), arm=data["arm"], source_file=path.name)
            row["scenario_id"] = ARM_B_MAP[row["id"]] if data["arm"] == "B" else row["id"]
            row["factor_0"] = factor0(row)
            rows.append(row)
        metadata.append({"file": path.name, "model": data.get("model", "?"), "arm": data["arm"], "date": data.get("run_date", "?")})
    if len(rows) != 216:
        raise ValueError(f"Expected 216 rows, found {len(rows)}")

    sys.path.insert(0, str(BACKEND))
    from app.domains.soc.config import SOC_PROFILE_CENTROIDS  # type: ignore[import-not-found]
    current = np.asarray(SOC_PROFILE_CENTROIDS, dtype=float)
    anchor = np.asarray(json.loads((BACKEND / "app/data/iks_bootstrap_soc.json").read_text(encoding="utf-8"))["mu_zero"], dtype=float)
    data = json.loads((BACKEND / "app/data/soc_eval_scenarios.json").read_text(encoding="utf-8"))
    scenarios = data if isinstance(data, list) else data["scenarios"]
    if len(scenarios) != 36:
        raise ValueError("Scenario fixture is not 36 rows")
    by_id = {s["scenario_id"]: s for s in scenarios}
    true_action = {s["scenario_id"]: s["expected_action"] for s in scenarios}
    models = sorted({r["panel_model"] for r in rows})
    arm_a = [r for r in rows if r["arm"] == "A"]
    arm_b = [r for r in rows if r["arm"] == "B"]
    a_by = defaultdict(list)
    for r in arm_a:
        a_by[r["scenario_id"]].append(r)

    # C1 presence profiles.
    presence: dict[tuple[str, str], dict[str, float]] = {}
    for arm, source in (("A", arm_a), ("B", arm_b)):
        groups = defaultdict(list)
        for r in source:
            group = true_action[r["scenario_id"]] if arm == "A" else r.get("predicted_disposition", "missing")
            groups[("disposition", group)].append(r)
            groups[("category", by_id[r["scenario_id"]]["category"])].append(r)
        for key, group in groups.items():
            presence[(arm, "/".join(map(str, key)))] = {field: sum(r.get(field) is not None for r in group) / len(group) for field in FIELDS}

    # C2-C4.
    cell_panel = defaultdict(list)
    for r in arm_a:
        cell_panel[(by_id[r["scenario_id"]]["category"], true_action[r["scenario_id"]])].append(r["factor_0"])
    c2 = {cat: {act: float(np.mean(cell_panel[(cat, act)])) for act in ACTIONS} for cat in CATEGORIES}
    inversions = [cat for cat in CATEGORIES if c2[cat]["escalate"] <= c2[cat]["suppress"]]
    c3 = [r for r in arm_a if true_action[r["scenario_id"]] == "escalate" and r["factor_0"] < 0.5]
    cloud = [r["factor_0"] for r in arm_a if r["scenario_id"] in {"SOC-CI-04", "SOC-CI-05"}]
    human = [r["factor_0"] for r in arm_a if true_action[r["scenario_id"]] == "suppress" and by_id[r["scenario_id"]]["category"] != "cloud_infrastructure"]

    # C5.
    medians = [float(median([r["factor_0"] for r in a_by[s["scenario_id"]]])) for s in scenarios]
    devices = [float(s["factors"]["device_trust"]) for s in scenarios]
    pearson = float(np.corrcoef(medians, devices)[0, 1])
    spearman = float(np.corrcoef(ranks(medians), ranks(devices))[0, 1])
    reused = [r.get("device_field_reused_description_adjective") is True for r in arm_a]
    panel_f0_std = float(np.std([r["factor_0"] for r in arm_a]))

    # C6.
    a_lookup = {(r["panel_model"], r["scenario_id"]): r for r in arm_a}
    b_lookup = {(r["panel_model"], r["scenario_id"]): r for r in arm_b}
    null_fills = 0
    total_slots = len(arm_a) * len(FIELDS)
    agreement = Counter()
    risk_delta: list[float] = []
    for model in models:
        for s in scenarios:
            a, b = a_lookup[(model, s["scenario_id"])], b_lookup[(model, s["scenario_id"])]
            if a.get("user_risk_score") is not None and b.get("user_risk_score") is not None:
                risk_delta.append(abs(float(a["user_risk_score"]) - float(b["user_risk_score"])))
            for field in FIELDS:
                if b.get(field) is None and a.get(field) is not None:
                    null_fills += 1
                if a.get(field) == b.get(field):
                    agreement[field] += 1
    fill_pct = 100 * null_fills / total_slots

    # C7-C8.
    negative = [r for r in arm_b if r["id"] in {"B-10", "B-21"}]
    b_absent = [sum(r.get(field) is None for field in FIELDS) / 4 for r in arm_b]
    confusion = Counter()
    correct = 0
    cat_hits, cat_total = Counter(), Counter()
    for r in arm_b:
        actual, predicted = true_action[r["scenario_id"]], r.get("predicted_disposition", "missing")
        confusion[(actual, predicted)] += 1
        cat = by_id[r["scenario_id"]]["category"]
        cat_total[cat] += 1
        if actual == predicted:
            correct += 1
            cat_hits[cat] += 1

    # Arm-A aggregation and C9.
    aggregated: dict[str, dict[str, Any]] = {}
    for s in scenarios:
        group = a_by[s["scenario_id"]]
        risks = [float(r["user_risk_score"]) for r in group if r.get("user_risk_score") is not None]
        fields = {field: majority([r.get(field) for r in group]) for field in FIELDS}
        fields["user_risk_score"] = float(median(risks)) if risks else None
        aggregated[s["scenario_id"]] = {"fields": fields, "factor_0": factor0(fields), "risk_iqr": iqr(risks)}
    cell_values = defaultdict(list)
    cell_ids = defaultdict(list)
    for s in scenarios:
        key = (s["category"], s["expected_action"])
        cell_values[key].append(aggregated[s["scenario_id"]]["factor_0"])
        cell_ids[key].append(s["scenario_id"])
    raw_priors = {(cat, act): float(np.mean(cell_values[(cat, act)])) for cat in CATEGORIES for act in ACTIONS}
    proposed_f0 = dict(raw_priors)
    guard = raw_priors[("credential_access", "monitor")] >= 0.40
    if guard:
        proposed_f0[("credential_access", "monitor")] = float(current[0, 3, 0])
    proposed = current.copy()
    for ci, cat in enumerate(CATEGORIES):
        for ai, act in enumerate(ACTIONS):
            proposed[ci, ai, 0] = proposed_f0[(cat, act)]
    raw_monitor = raw_priors[("credential_access", "monitor")]
    final_monitor = proposed_f0[("credential_access", "monitor")]

    # C10.
    evidence = Counter()
    for r in arm_a:
        basis = str(r.get("evidence_basis", "other")).lower()
        evidence["mixed" if "|" in basis or "," in basis else basis] += 1

    # Section 7 scorer verification.
    verification = []
    matches = 0
    confidences = []
    for s in scenarios:
        sid = s["scenario_id"]
        fv = np.asarray([aggregated[sid]["factor_0"]] + [s["factors"][name] for name in ["asset_criticality", "threat_intel_enrichment", "pattern_history", "time_anomaly", "device_trust"]], dtype=float)
        winner, margin, confidence = score(fv, proposed, int(s["category_index"]))
        matches += winner == int(s["expected_action_index"])
        confidences.append(confidence)
        verification.append([sid, s["expected_action"], ACTIONS[winner], "MATCH" if winner == int(s["expected_action_index"]) else "FLIP", f(margin), f(confidence)])
    c9b_winner, c9b_margin, c9b_conf = score(np.asarray([0.85, 1, 0, .4, .7, 2/3]), proposed, 0)
    low_winner, low_margin, low_conf = score(np.asarray([.825, .5, 0, .4, .7, 2/3]), proposed, 0)
    current_drift = float(np.mean(np.linalg.norm(current - anchor, axis=2)))
    proposed_drift = float(np.mean(np.linalg.norm(proposed - anchor, axis=2)))
    current_iks = 100 * min(current_drift / .2, 1)
    proposed_iks = 100 * min(proposed_drift / .2, 1)

    # Report construction is intentionally plain so the script remains easy to audit.
    out: list[str] = []
    def add(text: str = "") -> None:
        out.append(text)
    add("# SOC Factor-0 Multi-Model Panel Analysis v1")
    add("\n**Status:** analysis/design artifact; no production files modified.")
    add("\n## 1. Executive summary")
    add(f"\nSix files parsed: **{len(rows)}/216 determinations**. Arm A is aggregated for candidate values; Arm B is mapped through the registered opaque-token map for disposition recovery. All factor values are computed by the formula implemented in this script, with null fields excluded and all-null rows defaulting to 0.5.")
    add(f"\nThe raw credential-access/monitor mean is **{raw_monitor:.4f}**; geometry guard={guard}. The final candidate uses {final_monitor:.4f}. The candidate scores **{matches}/36** expected actions. C9B={c9b_conf:.6f}; companion={low_conf:.6f}.")
    add(f"\nStatic candidate drift from the immutable anchor implies IKS {proposed_iks:.1f}; current static bootstrap/anchor IKS is {current_iks:.1f}. This does not overwrite or recompute live learned-state IKS (operationally reported around 93-94).")
    add("\n## 2. Panel metadata and data quality")
    add("\n" + table(["File", "Declared model", "Arm", "Date"], [[m["file"], m["model"], m["arm"], m["date"]] for m in metadata]))
    add("\nEach file contains 36 determinations; the six-file corpus contains 3 model prefixes x 2 arms. Data-quality note: the `gemini_*` filenames declare `Claude 3.7 Sonnet`; this report preserves both the filename provenance label and the declared model string rather than silently reconciling them.")
    add("\n## 3. Verification checks C1-C10")
    add("\n### C1 - Presence profile")
    c1_rows = [[key, f(values["user_risk_score"], 2), f(values["user_title"], 2), f(values["mfa_completed"], 2), f(values["device_fingerprint_match"], 2)] for key, values in sorted(presence.items())]
    add(table(["Arm/group", "Risk", "Title", "MFA", "Device"], c1_rows))
    add("\n### C2 - Arm-A ordering")
    add(table(["Category"] + ACTIONS, [[cat] + [f(c2[cat][act]) for act in ACTIONS] for cat in CATEGORIES]))
    add(f"\nInversions where escalate <= suppress: {len(inversions)} ({', '.join(inversions) if inversions else 'none'}).")
    add("\n### C3 - Information versus ignorance")
    add(f"\nEscalate rows below the all-absent default 0.5: **{len(c3)}** panel rows.")
    add(table(["Model", "Scenario", "f0", "Reasoning"], [[r["panel_model"], r["scenario_id"], f(r["factor_0"]), r.get("reasoning", "")] for r in c3]) if c3 else "None.")
    add("\n### C4 - Service-account floor")
    add(f"\nCloud suppress mean={np.mean(cloud):.4f}, range=[{min(cloud):.4f}, {max(cloud):.4f}]. Non-cloud suppress mean={np.mean(human):.4f}, range=[{min(human):.4f}, {max(human):.4f}]. Difference={np.mean(cloud)-np.mean(human):+.4f}.")
    add("\n### C5 - Factor-0 x factor-5 collinearity")
    add(f"\nPearson r={pearson:.4f}; Spearman rho={spearman:.4f}. `device_field_reused_description_adjective` true/present: {sum(reused)}/{len(reused)} ({100*np.mean(reused):.1f}%).")
    add("\n### C6 - Arm-A to Arm-B delta")
    add(f"\nNull-to-non-null fills: {null_fills}/{total_slots} = **{fill_pct:.1f}%**. Mean absolute risk delta where both arms provided risk={np.mean(risk_delta):.4f}.")
    add(table(["Field", "Exact same / 108"], [[field, f"{agreement[field]}/{len(arm_a)}"] for field in FIELDS]))
    add("\n### C7 - Negative controls")
    add(table(["Model", "Token", "Non-null/4", "Confidence fields", "Absent rate"], [[r["panel_model"], r["id"], sum(r.get(x) is not None for x in FIELDS), ", ".join(f'{x}={r.get("confidence", {}).get(x, "-")}' for x in FIELDS), f(sum(r.get(x) is None for x in FIELDS)/4, 2)] for r in negative]))
    add(f"\nArm-B mean absent rate={np.mean(b_absent):.3f}.")
    add("\n### C8 - Disposition recovery")
    add(f"\nAccuracy={correct}/{len(arm_b)} = **{100*correct/len(arm_b):.1f}%**; prevalence caveat: 12 escalate, 6 investigate, 12 suppress, 6 monitor.")
    add(table(["Category", "Correct", "Total", "Accuracy"], [[cat, cat_hits[cat], cat_total[cat], f(100*cat_hits[cat]/cat_total[cat], 1)+"%"] for cat in CATEGORIES]))
    add(table(["True / predicted"] + ACTIONS, [[actual] + [confusion[(actual, predicted)] for predicted in ACTIONS] for actual in ACTIONS]))
    add("\n### C9 - Cell coverage")
    add(table(["Category", "Action", "n", "Raw mean", "IQR", "IDs"], [[cat, act, len(cell_values[(cat, act)]), f(raw_priors[(cat, act)]), f(iqr(cell_values[(cat, act)])), ", ".join(cell_ids[(cat, act)])] for cat in CATEGORIES for act in ACTIONS]))
    singles = [f"{cat}/{act}" for cat in CATEGORIES for act in ACTIONS if len(cell_values[(cat, act)]) == 1]
    add(f"\nSingle-value cells: **{len(singles)}/24** ({', '.join(singles)}).")
    add("\n### C10 - Evidence basis audit")
    add(table(["Basis", "Count", "Share"], [[key, value, f(100*value/len(arm_a), 1)+"%"] for key, value in sorted(evidence.items())]))
    add(f"\nDisposition-prior share={100*evidence['disposition_prior']/len(arm_a):.1f}%.")
    add("\n## 4. Pre-registered predictions P1-P5")
    add(table(["Prediction", "Result", "Interpretation"], [
        ["P1 variance/weight", f"YES; Arm-A f0 SD={panel_f0_std:.3f}", "Inter-model variance is nonzero versus a fixed current prior, but the direction/magnitude of a kernel-weight change still requires within-class variance calibration."],
        ["P2 escalate below 0.5", str(len(c3)), "Observed; clean identity does not imply low alert severity."],
        ["P3 service floor", f"{np.mean(cloud):.3f} vs {np.mean(human):.3f}", "Measured, but confounded by authored service-account fields."],
        ["P4 f0 x f5", f"Pearson {pearson:.3f}; Spearman {spearman:.3f}", "Descriptive collinearity; shared wording is a possible confounder."],
        ["P5 A-to-B null fill", f"{fill_pct:.1f}%", "Disposition knowledge fills a measurable fraction of fields."],
    ]))
    add("\n## 5. Aggregated Arm-A values")
    add(table(["Scenario", "Category/action", "Risk median", "Risk IQR", "Title", "MFA", "Device", "Computed f0"], [[s["scenario_id"], f'{s["category"]}/{s["expected_action"]}', f(aggregated[s["scenario_id"]]["fields"]["user_risk_score"]), f(aggregated[s["scenario_id"]]["risk_iqr"]), aggregated[s["scenario_id"]]["fields"]["user_title"], aggregated[s["scenario_id"]]["fields"]["mfa_completed"], aggregated[s["scenario_id"]]["fields"]["device_fingerprint_match"], f(aggregated[s["scenario_id"]]["factor_0"])] for s in scenarios]))
    add("\n## 6. Derived centroid priors")
    add(table(["Category", "Action", "n", "Raw mean", "Final candidate", "Source IDs"], [[cat, act, len(cell_values[(cat, act)]), f(raw_priors[(cat, act)]), f(proposed_f0[(cat, act)]), ", ".join(cell_ids[(cat, act)])] for cat in CATEGORIES for act in ACTIONS]))
    add(f"\nGeometry guard: raw credential_access/monitor={raw_monitor:.4f}; final={final_monitor:.4f}. {'Required because raw mean >= 0.40.' if guard else 'Not required because raw mean < 0.40.'}")
    add("\n## 7. Full Section-7 scorer verification")
    add(f"\nProduction L2 geometry and tau=0.1 were used. Expected-action result: **{matches}/36**.")
    add(table(["Scenario", "Expected", "Winner", "Status", "Distance margin", "Confidence"], verification))
    add(f"\nConfidence range: min={min(confidences):.4f}, mean={np.mean(confidences):.4f}, max={max(confidences):.4f}.")
    add("\n## 8. C9B and low-confidence companion")
    add(table(["Check", "Winner", "Confidence", "Threshold", "Result", "Margin"], [["C9B", ACTIONS[c9b_winner], f(c9b_conf, 6), "0.620", "PASS" if c9b_conf >= .62 else "FAIL", f(c9b_conf-.62, 6)], ["Low-confidence companion", ACTIONS[low_winner], f(low_conf, 6), "0.620", "PASS" if low_conf < .62 else "FAIL", f(low_conf-.62, 6)]]))
    add("\nBoth checks are required; top-1 action preservation alone is insufficient.")
    add("\n## 9. IKS impact assessment")
    add(f"\nThe immutable anchor was read but not changed. Current static bootstrap/anchor drift={current_drift:.6f}, IKS={current_iks:.1f}; proposed candidate drift={proposed_drift:.6f}, IKS={proposed_iks:.1f}. The latter is a candidate reference-point impact, not a live learned-state measurement. A proposed IKS below 67 is a migration problem under the design gate.")
    add("\n## 10. Recommendation")
    add("\nThe panel is useful evidence for semantic reconciliation, but is not sufficient to trigger production migration. It is a synthetic judgment corpus, disposition-prior reasoning is not independent evidence, and single-value cells lack variance estimates. Use the candidate only for isolated replay/shadow analysis. Require SOC analyst review, identity-native pilot evidence, sparse-cell treatment, threshold replay, immutable-anchor/versioning, rollback, and product endpoint checks before migration.")
    add("\n## 11. Provenance and reproducibility")
    add("\nArm-A values are model-aggregated panel judgments from the six source files, computed by `factor0()` in `scripts/analyze_factor0_panel.py`. The script reads the real SOC tensor, scenario fixture, and frozen IKS anchor without modifying them. The repository directory is `factor_0_panel_data` (underscore).")
    add("\n## Final results")
    add(table(["Check", "Result"], [["C1-C10", "computed"], ["Scorer", f"{matches}/36"], ["C9B", "PASS" if c9b_conf >= .62 else "FAIL"], ["Low-confidence companion", "PASS" if low_conf < .62 else "FAIL"], ["IKS", f"{current_iks:.1f} -> {proposed_iks:.1f}"], ["Decision", "CONDITIONAL / shadow-only"]]))
    REPORT.write_text("\n".join(out) + "\n", encoding="utf-8")
    print("\n".join(out))


if __name__ == "__main__":
    main()
