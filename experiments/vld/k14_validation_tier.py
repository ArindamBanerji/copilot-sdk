"""K14 input gate and validation-tier study.

Pre-registered decision:
    K14 is established only when K2 diverges from ANCHOR in a competence-
    correlated way, its compounding gain differs materially from ANCHOR's,
    and K3 tracks ANCHOR closely.  Missing K2 labels block the experiment;
    anchor or canonical-execution fields are never substituted for K2.

Tier: REAL_COMPONENT geometry + GEOMETRY-DERIVED + SIMULATED.
"""

from __future__ import annotations

import argparse
import json
import math
import random
from pathlib import Path
from typing import Any, cast


ROOT = Path(__file__).resolve().parents[2]
SAMPLES = Path(r"G:\My Drive\public-files\gen-ai-roi\claude_projects\design\blogs\ci_core\vld_samples")
AUTHORITY = Path(r"G:\My Drive\public-files\gen-ai-roi\claude_projects\design\blogs\ci_core\vld_k14_validation_tier_experiment.md")
DEFAULT_OUTPUT = ROOT / "experiments" / "vld" / "results" / "k14_validation_tier.json"
LABELS = ROOT / "experiments" / "vld" / "data" / "k14_k2_labels.json"
COPILOTS = ("soc", "dataops", "s2p", "trading", "purchasing")
SCENARIO_FILES = {
    "soc": "astra_soc_50_scenarios.json",
    "dataops": "astra_dataops_full_50.json",
    "s2p": "astra_s2p_50_scenarios.json",
    "trading": "astra_trading_50_scenarios.json",
    "purchasing": "astra_purchasing_full_50.json",
}
K2_KEYS = ("correct_action", "llm_judged_action", "llm_label", "judge_label", "expected_action")
COMPETENCE_KEYS = ("llm_confidence", "judge_confidence", "competence", "judge_score", "model_confidence")


def load_object(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def find_scenarios(value: Any) -> list[dict[str, Any]]:
    if isinstance(value, dict) and isinstance(value.get("scenarios"), list):
        return [cast(dict[str, Any], row) for row in value["scenarios"] if isinstance(row, dict)]
    return []


def nested_key_present(value: Any, keys: tuple[str, ...]) -> bool:
    if isinstance(value, dict):
        if any(key in value for key in keys):
            return True
        return any(nested_key_present(child, keys) for child in value.values())
    if isinstance(value, list):
        return any(nested_key_present(child, keys) for child in value)
    return False


def inspect_inputs() -> dict[str, Any]:
    audit: dict[str, Any] = {}
    for copilot in COPILOTS:
        path = SAMPLES / SCENARIO_FILES[copilot]
        entry: dict[str, Any] = {
            "path": str(path),
            "accessible": False,
            "scenario_count": 0,
            "anchor_field_count": 0,
            "k2_label_field_present": False,
            "competence_proxy_present": False,
        }
        try:
            raw = load_object(path)
            scenarios = find_scenarios(raw)
            entry.update(
                {
                    "accessible": True,
                    "scenario_count": len(scenarios),
                    "anchor_field_count": sum("ground_truth_action" in row.get("decision_tree", {}) for row in scenarios),
                    "k2_label_field_present": nested_key_present(scenarios, K2_KEYS),
                    "competence_proxy_present": nested_key_present(scenarios, COMPETENCE_KEYS),
                    "anchor_field": "decision_tree.ground_truth_action",
                }
            )
        except (OSError, json.JSONDecodeError) as exc:
            entry["error"] = f"{type(exc).__name__}: {exc}"
        audit[copilot] = entry
    return audit


def load_labels() -> dict[str, Any]:
    return cast(dict[str, Any], load_object(LABELS))


def load_geometry() -> dict[str, Any]:
    raw = cast(dict[str, Any], load_object(ROOT / "real_centroids_v1.json"))
    return cast(dict[str, Any], raw["copilots"])


def vec_for(scenario: dict[str, Any], factor_names: list[str]) -> list[float]:
    values = scenario.get("enriched_factors_reference", {})
    if not isinstance(values, dict):
        values = scenario.get("alert", {}).get("surface_factors", {})
    return [float(values.get(name, 0.0)) for name in factor_names]


def nearest_action(vector: list[float], info: dict[str, Any]) -> str:
    names = [str(x) for x in info["action_names"]]
    mu = info["mu"]
    distances = [sum((float(a) - float(b)) ** 2 for a, b in zip(vector, row)) for row in mu]
    best_index = min(range(len(distances)), key=lambda index: distances[index])
    return names[best_index]


def label_rows(copilot: str, labels: dict[str, Any], scenarios: list[dict[str, Any]], info: dict[str, Any]) -> list[dict[str, Any]]:
    labels_list = labels[copilot]
    output: list[dict[str, Any]] = []
    names = [str(x) for x in info["factor_names"]]
    for i, scenario in enumerate(scenarios):
        row = labels_list[i] if i < len(labels_list) else None
        vector = vec_for(scenario, names)
        recommended = str(scenario.get("surface_action_reference"))
        gt_action = scenario.get("decision_tree", {}).get("ground_truth_action", recommended)
        k3 = nearest_action(vector, info) == gt_action
        anchor = (recommended == scenario.get("decision_tree", {}).get("ground_truth_action", ""))
        output.append({"scenario": scenario, "row": row, "vector": vector, "recommended": recommended, "anchor": anchor, "k3": k3})
    return output


def informative_dims(scenario: dict[str, Any], factor_names: list[str]) -> set[int]:
    dims: set[int] = set()
    for branch in scenario.get("decision_tree", {}).get("hops", []):
        name = branch.get("factor_enriched")
        if name in factor_names:
            dims.add(factor_names.index(str(name)))
    if not dims:
        dims = set(range(min(2, len(factor_names))))
    return dims


def run_arm(rows: list[dict[str, Any]], info: dict[str, Any], seed: int, regime: str) -> dict[str, Any]:
    rng = random.Random(seed)
    stream = list(rows) * 10
    rng.shuffle(stream)
    names = [str(x) for x in info["factor_names"]]
    action_names = [str(x) for x in info["action_names"]]
    spreads = [max(float(mu[d]) for mu in info["mu"]) - min(float(mu[d]) for mu in info["mu"]) for d in range(len(names))]
    k = [[0.5 for _ in names] for _ in action_names]
    curve: dict[str, float] = {}
    action_curve: dict[str, float] = {}
    snapshots: dict[str, list[list[float]]] = {}
    for position, item in enumerate(stream, 1):
        action_index = action_names.index(item["recommended"]) if item["recommended"] in action_names else 0
        scores = [(k[action_index][d] * spreads[d], d) for d in range(len(names))]
        selected = {d for _, d in sorted(scores, reverse=True)[:2]}
        useful = informative_dims(item["scenario"], names)
        signal = item["row"].get("k2_label") if regime == "k2" else item["k3"] if regime == "k3" else item["anchor"]
        for dim in selected:
            target = 1.0 if bool(signal) else 0.0
            k[action_index][dim] = max(0.1, min(3.0, k[action_index][dim] + (0.02 if target else -0.005)))
        if position % 50 == 0:
            eval_rows = rows
            routed = 0
            correct = 0
            for ev in eval_rows:
                ev_action = action_names.index(ev["recommended"]) if ev["recommended"] in action_names else 0
                ev_scores = [(k[ev_action][d] * spreads[d], d) for d in range(len(names))]
                ev_selected = {d for _, d in sorted(ev_scores, reverse=True)[:2]}
                routed += int(bool(ev_selected & informative_dims(ev["scenario"], names)))
                predicted = nearest_action([ev["vector"][d] if d in ev_selected else 0.0 for d in range(len(names))], info)
                correct += int(predicted == ev["scenario"].get("decision_tree", {}).get("ground_truth_action"))
            curve[str(position)] = routed / len(eval_rows)
            action_curve[str(position)] = correct / len(eval_rows)
            snapshots[str(position)] = [list(row) for row in k]
    values = list(curve.values())
    gain = values[-1] - values[0] if values else 0.0
    return {"routing_curve": curve, "action_accuracy_curve": action_curve, "gain": gain, "k_snapshot_500": snapshots.get("500", []), "k_snapshot_final": snapshots.get("500", [])}


def correlation(xs: list[float], ys: list[float]) -> float | None:
    if len(xs) < 2:
        return None
    mx, my = sum(xs) / len(xs), sum(ys) / len(ys)
    den = math.sqrt(sum((x - mx) ** 2 for x in xs) * sum((y - my) ** 2 for y in ys))
    return sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / den if den else 0.0


def build_payload() -> dict[str, Any]:
    audit = inspect_inputs()
    accessible = all(bool(audit[c]["accessible"]) for c in COPILOTS)
    all_have_anchor = all(int(audit[c].get("anchor_field_count", 0)) == 50 for c in COPILOTS)
    if not accessible or not all_have_anchor or not LABELS.exists():
        return {"status": "blocked", "reason": "K14 inputs or generated K2 labels are missing.", "input_audit": audit, "k14_established": False, "seeds": [42, 123, 7]}
    labels = load_labels()
    geometry = load_geometry()
    per: dict[str, Any] = {}
    for copilot in COPILOTS:
        scenarios = find_scenarios(load_object(SAMPLES / SCENARIO_FILES[copilot]))
        prepared = label_rows(copilot, labels, scenarios, geometry[copilot])
        k2_agreement = sum(int(bool(x["row"].get("k2_label")) == x["anchor"]) for x in prepared) / len(prepared)
        k3_agreement = sum(int(x["k3"] == x["anchor"]) for x in prepared) / len(prepared)
        difficulties = [float(x["row"].get("difficulty", 0.5)) for x in prepared]
        correctness = [float(bool(x["row"].get("k2_label")) == x["anchor"]) for x in prepared]
        confidence = [float(x["row"].get("k2_confidence", 0.5)) for x in prepared]
        bins = {"easy": [i for i, d in enumerate(difficulties) if d < 0.3], "medium": [i for i, d in enumerate(difficulties) if 0.3 <= d < 0.6], "hard": [i for i, d in enumerate(difficulties) if d >= 0.6]}
        by_diff = {name: sum(correctness[i] for i in ids) / len(ids) if ids else None for name, ids in bins.items()}
        gains: dict[str, list[float]] = {"k2": [], "k3": [], "anchor": []}
        curves: dict[str, Any] = {}
        for seed in [42, 123, 7]:
            for regime in gains:
                result = run_arm(prepared, geometry[copilot], seed, regime)
                gains[regime].append(result["gain"])
                curves[f"{regime}_{seed}"] = result
        k2_mean, k3_mean, anchor_mean = (sum(gains[x]) / 3 for x in ("k2", "k3", "anchor"))
        per[copilot] = {"k2_anchor_agreement": k2_agreement, "k3_anchor_agreement": k3_agreement, "k2_anchor_agreement_by_difficulty": by_diff, "k2_compounding_gain": {"mean": k2_mean, "seeds": gains["k2"]}, "k3_compounding_gain": {"mean": k3_mean, "seeds": gains["k3"]}, "anchor_compounding_gain": {"mean": anchor_mean, "seeds": gains["anchor"]}, "k2_competence_correlation": {"pearson": correlation(confidence, correctness)}, "k2_difficulty_correlation": {"pearson": correlation(difficulties, correctness)}, "q1_diverges": k2_agreement < k3_agreement, "q2_gain_differs": abs(k2_mean - anchor_mean) > 0.03, "q3_k3_tracks": k3_agreement > 0.85, "q4_competence_correlated": (correlation(confidence, correctness) or 0.0) > 0.3, "curves": curves}
    established = all(row["q1_diverges"] and row["q2_gain_differs"] and row["q3_k3_tracks"] and row["q4_competence_correlated"] for row in per.values())
    mean = lambda key: sum(float(row[key]) for row in per.values()) / len(per)
    return {"status": "measured", "input_audit": audit, "per_copilot": per, "aggregate": {"mean_k2_anchor_agreement": mean("k2_anchor_agreement"), "mean_k3_anchor_agreement": mean("k3_anchor_agreement"), "mean_k2_gain": sum(float(row["k2_compounding_gain"]["mean"]) for row in per.values()) / len(per), "mean_anchor_gain": sum(float(row["anchor_compounding_gain"]["mean"]) for row in per.values()) / len(per), "mean_competence_correlation": sum(float(row["k2_competence_correlation"]["pearson"] or 0.0) for row in per.values()) / len(per)}, "k14_established": established, "verdict_sentence": "K14 is established only if all four preregistered Q conditions hold; the measured result and K2 source provenance are reported without substituting ANCHOR for K2.", "seeds": [42, 123, 7], "metadata": {"k2_source": labels.get("metadata", {}).get("source"), "tier": "LLM-JUDGED K2 + REAL_COMPONENT geometry + GEOMETRY-DERIVED + SIMULATED", "same_stream_requirement": True, "anchor_source": "decision_tree.ground_truth_action", "authority_path": str(AUTHORITY), "geometry_path": str(ROOT / "real_centroids_v1.json"), "decisions_per_arm": 500}}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    payload = build_payload()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    summary = args.output.with_name("k14_validation_tier_summary.md")
    if payload.get("status") == "measured":
        lines = ["# K14 — Validation-Tier Study", "", "Status: **MEASURED**.", "", f"K14 established: **{payload['k14_established']}**.", "", "| Copilot | K2↔ANCHOR | K3↔ANCHOR | K2 gain | K3 gain | ANCHOR gain |", "|---|---:|---:|---:|---:|---:|"]
        for copilot in COPILOTS:
            row = payload["per_copilot"][copilot]
            lines.append(f"| {copilot} | {row['k2_anchor_agreement']:.3f} | {row['k3_anchor_agreement']:.3f} | {row['k2_compounding_gain']['mean']:.3f} | {row['k3_compounding_gain']['mean']:.3f} | {row['anchor_compounding_gain']['mean']:.3f} |")
        lines += ["", "K2 source: " + str(payload["metadata"].get("k2_source")), "", "Tier: LLM-JUDGED K2 + REAL_COMPONENT geometry + GEOMETRY-DERIVED + SIMULATED.", ""]
        summary.write_text("\n".join(lines), encoding="utf-8")
        return
    lines = [
        "# K14 — Validation-Tier Study",
        "",
        "Status: **BLOCKED — NOT MEASURED**.",
        "",
        payload["reason"],
        "",
        "| Copilot | Astra scenarios | ANCHOR fields | K2 label present | competence field present |",
        "|---|---:|---:|---|---|",
    ]
    for copilot in COPILOTS:
        row = payload["input_audit"][copilot]
        lines.append(f"| {copilot} | {row.get('scenario_count', 0)} | {row.get('anchor_field_count', 0)} | {row.get('k2_label_field_present', False)} | {row.get('competence_proxy_present', False)} |")
    lines += [
        "",
        "The fixtures expose `decision_tree.ground_truth_action`, which is suitable as the planted ANCHOR. They do not expose an independent LLM-judged action or LLM confidence/competence proxy. `canonical_policy_execution.realized_action` (where present) is not substituted for K2 because doing so would make K2 and ANCHOR non-independent.",
        "",
        "No compounding curves, label agreements, correlations, or K14 verdict were computed. A valid rerun requires K2 labels and a competence/confidence field for the same 50 scenarios per copilot.",
        "",
        "Tier: REAL_COMPONENT geometry + GEOMETRY-DERIVED + SIMULATED.",
        "",
    ]
    summary.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
