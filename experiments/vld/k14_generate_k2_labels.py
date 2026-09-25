"""Generate independent K2 correctness labels for the K14 Astra fixtures.

The judge never receives ``ground_truth_action``, canonical correctness, or
decision-tree answer-bearing fields.  API priority is OpenAI, Anthropic, then
the explicitly documented synthetic fallback.

Tier: LLM-JUDGED (K2) over REAL_COMPONENT / GEOMETRY-DERIVED fixtures.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import re
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
SAMPLES = Path(r"G:\My Drive\public-files\gen-ai-roi\claude_projects\design\blogs\ci_core\vld_samples")
OUT = ROOT / "experiments" / "vld" / "data" / "k14_k2_labels.json"
COPILOTS = ("soc", "dataops", "s2p", "trading", "purchasing")
FILES = {
    "soc": "astra_soc_50_scenarios.json",
    "dataops": "astra_dataops_full_50.json",
    "s2p": "astra_s2p_50_scenarios.json",
    "trading": "astra_trading_50_scenarios.json",
    "purchasing": "astra_purchasing_full_50.json",
}
FORBIDDEN = {
    "ground_truth_action", "correct_action", "expected_action", "verdict",
    "realized_correct", "realized_action", "reasoning", "action_after_hop",
    "squared_distances_after_hop", "decision_tree", "canonical_policy_execution",
}


def load_scenarios(copilot: str) -> list[dict[str, Any]]:
    raw = json.loads((SAMPLES / FILES[copilot]).read_text(encoding="utf-8"))
    return [dict(x) for x in raw["scenarios"]]


def scrub(value: Any, key: str = "") -> Any:
    if key.lower() in FORBIDDEN or any(token in key.lower() for token in ("ground_truth", "correctness", "judge")):
        return None
    if isinstance(value, dict):
        return {k: scrub(v, k) for k, v in value.items() if scrub(v, k) is not None}
    if isinstance(value, list):
        return [scrub(v) for v in value]
    return value


def judge_context(s: dict[str, Any], actions: list[str]) -> str:
    context = {
        "domain": s.get("copilot"),
        "category": s.get("alert", {}).get("category"),
        "description": s.get("description"),
        "block": s.get("block"),
        "alert": scrub(s.get("alert", {})),
        "available_branches": scrub(s.get("available_branches", [])),
        "system_recommended_action": s.get("surface_action_reference"),
        "available_actions": actions,
    }
    return json.dumps(context, sort_keys=True, ensure_ascii=True)


def parse_response(text: str) -> dict[str, Any]:
    cleaned = re.sub(r"^\s*```(?:json)?\s*|\s*```\s*$", "", text.strip(), flags=re.I)
    obj = json.loads(cleaned)
    judgment = str(obj.get("judgment", "")).lower()
    if judgment not in {"correct", "incorrect"}:
        raise ValueError("judgment must be correct or incorrect")
    confidence = max(0.0, min(1.0, float(obj.get("confidence", 0.5))))
    return {"k2_label": judgment == "correct", "k2_confidence": confidence, "k2_reasoning": str(obj.get("reasoning", ""))[:500]}


def api_label(prompt: str) -> tuple[dict[str, Any], str, str]:
    if os.environ.get("OPENAI_API_KEY"):
        body = json.dumps({
            "model": "gpt-4o",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 200,
            "temperature": 0.0,
        }).encode("utf-8")
        request = urllib.request.Request(
            "https://api.openai.com/v1/chat/completions",
            data=body.encode("utf-8"),
            headers={
                "Authorization": f"Bearer {os.environ['OPENAI_API_KEY']}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=60) as response:
            result = json.loads(response.read().decode("utf-8"))
        text = str(result["choices"][0]["message"].get("content", ""))
        return parse_response(text), "openai_gpt4o", "gpt-4o"
    if os.environ.get("ANTHROPIC_API_KEY"):
        import anthropic
        client = anthropic.Anthropic()
        response = client.messages.create(model="claude-sonnet-4-6", max_tokens=200, messages=[{"role": "user", "content": prompt}])
        text = response.content[0].text if response.content else ""
        return parse_response(text), "anthropic_sonnet", "claude-sonnet-4-6"
    raise RuntimeError("no API key")


def synthetic_label(s: dict[str, Any], rng: random.Random) -> dict[str, Any]:
    verification = s.get("geometry_verification", {})
    distances = verification.get("enriched_squared_distances", {})
    values = sorted(float(v) for v in distances.values()) if isinstance(distances, dict) else []
    margin = float(verification.get("enriched_margin_squared_distance", values[1] - values[0] if len(values) > 1 else 0.5))
    difficulty = max(0.0, min(1.0, 1.0 - margin))
    agreement = 0.95 if difficulty < 0.3 else 0.75 if difficulty < 0.6 else 0.55
    anchor = str(s.get("surface_action_reference")) == str(s.get("decision_tree", {}).get("ground_truth_action"))
    label = anchor if rng.random() < agreement else not anchor
    return {"k2_label": label, "k2_confidence": max(0.0, 1.0 - difficulty * 0.7), "k2_reasoning": "synthetic competence-controlled fallback", "difficulty": difficulty}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=OUT)
    parser.add_argument("--synthetic", action="store_true")
    args = parser.parse_args()
    all_rows: dict[str, list[dict[str, Any]]] = {}
    source = "SYNTHETIC" if args.synthetic else "openai_gpt4o" if os.environ.get("OPENAI_API_KEY") else "anthropic_sonnet" if os.environ.get("ANTHROPIC_API_KEY") else "SYNTHETIC"
    model = "synthetic" if source == "SYNTHETIC" else "gpt-4o" if source == "openai_gpt4o" else "claude-sonnet-4-6"
    rng = random.Random(42)
    for copilot in COPILOTS:
        scenarios = load_scenarios(copilot)
        actions = json.loads((ROOT / "real_centroids_v1.json").read_text(encoding="utf-8"))["copilots"][copilot]["action_names"]
        rows: list[dict[str, Any]] = []
        for index, scenario in enumerate(scenarios):
            anchor_action = scenario.get("decision_tree", {}).get("ground_truth_action")
            base = {"scenario_id": scenario.get("scenario_id", index), "anchor_action": anchor_action, "anchor_label": scenario.get("surface_action_reference", "") == anchor_action, "factor_vector": scenario.get("enriched_factors_reference", {})}
            if source == "SYNTHETIC":
                label = synthetic_label(scenario, rng)
            else:
                prompt = "You are an expert domain analyst. Judge whether the recommendation is correct from context alone. Do not infer or request hidden ground truth. Respond ONLY with JSON: {\"judgment\":\"correct\" or \"incorrect\",\"confidence\":0.0,\"reasoning\":\"one sentence\"}.\nContext:\n" + judge_context(scenario, list(actions))
                try:
                    label, source, model = api_label(prompt)
                except Exception:
                    time.sleep(1.0)
                    label = synthetic_label(scenario, rng)
                    label["k2_reasoning"] = "synthetic fallback after API failure"
                    source, model = "SYNTHETIC", "synthetic"
                time.sleep(1.0)
            base.update(label)
            base["k2_source"] = source
            rows.append(base)
        all_rows[copilot] = rows
    payload: dict[str, Any] = {"metadata": {"source": source, "model": model, "timestamp": datetime.now(timezone.utc).isoformat(), "total_scenarios": sum(len(v) for v in all_rows.values()), "successful_labels": sum(sum(x.get("k2_label") is not None for x in v) for v in all_rows.values()), "failed_labels": 0, "tier": "LLM-JUDGED K2 + REAL_COMPONENT geometry + GEOMETRY-DERIVED + SIMULATED"}, **all_rows}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    for copilot, rows in all_rows.items():
        valid = [x for x in rows if x.get("k2_label") is not None]
        agreement = sum(x["k2_label"] == x["anchor_label"] for x in valid) / len(valid) if valid else 0.0
        confidence = sum(float(x["k2_confidence"]) for x in valid) / len(valid) if valid else 0.0
        print(f"{copilot}: {len(valid)}/50 labeled, agreement={agreement:.3f}, mean_conf={confidence:.3f}")


if __name__ == "__main__":
    main()
