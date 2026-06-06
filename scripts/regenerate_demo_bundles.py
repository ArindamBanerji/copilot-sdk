"""Build-time generator for demo restore bundles.

This script is intentionally not imported by application startup code. It reads
versioned seed examples and writes deterministic JSON bundles under demo/.
"""

from __future__ import annotations

import json
import math
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "demo"
DECISIONS_PER_DOMAIN = 200
VERIFIED_RATIO = 0.75
OVERRIDE_RATIO = 0.20
RANDOM_SEED = 42
BASE_EPOCH = 1_700_000_000


@dataclass(frozen=True)
class DomainConfig:
    name: str
    seed_path: Path
    categories: tuple[str, ...]
    actions: tuple[str, ...]
    factors: tuple[str, ...]
    prefix: str
    events: tuple[dict[str, Any], ...]


CONFIGS = (
    DomainConfig(
        name="trading",
        seed_path=REPO / "apps/trading/backend/data/trading_seed_v2.json",
        categories=(
            "trend_following",
            "mean_reversion",
            "event_driven",
            "income_strategy",
            "scalp_intraday",
        ),
        actions=(
            "strong_execution",
            "partial_execution",
            "poor_execution",
            "skip_recommended",
        ),
          factors=(
              "signal_alignment",
              "market_regime",
              "position_sizing",
              "timing_quality",
              "risk_reward_actual",
              "emotional_indicator",
              "signal_confidence",
              "options_delta_exposure",
              "options_iv_percentile",
              "options_gamma_risk",
          ),
        prefix="TRD",
        events=(
            {
                "event_type": "variant_generated",
                "rule_name": "execution_quality_rule",
                "variant_id": "trading-demo-v1",
                "metadata": {"label": "Trading demo execution rule"},
            },
        ),
    ),
    DomainConfig(
        name="purchasing",
        seed_path=REPO / "apps/purchasing/backend/data/purchasing_seed_v2.json",
        categories=("protein", "produce", "dairy", "dry_goods", "beverages"),
        actions=("order_as_planned", "order_more", "order_less", "skip"),
        factors=(
            "expected_demand",
            "day_of_week",
            "weather_forecast",
            "event_flag",
            "historical_waste",
            "supplier_lead_time",
            "price_memory_index",
        ),
        prefix="PUR",
        events=(
            {
                "event_type": "variant_generated",
                "rule_name": "waste_reduction_rule",
                "variant_id": "purchasing-demo-v1",
                "metadata": {"label": "Purchasing demo waste reduction rule"},
            },
        ),
    ),
    DomainConfig(
        name="dataops",
        seed_path=REPO / "copilot_sdk/scoring/presets/dataops_seed.json",
        categories=(
            "schema_change",
            "volume_anomaly",
            "quality_anomaly",
            "freshness_violation",
            "pipeline_failure",
            "transform_drift",
        ),
        actions=(
            "auto_approve",
            "investigate",
            "escalate_to_owner",
            "pause_downstream",
            "refer_to_specialist",
        ),
        factors=(
            "impact_scope",
            "source_reliability",
            "recurrence_frequency",
            "downstream_urgency",
            "data_freshness",
            "business_criticality",
        ),
        prefix="DOP",
        events=(
            {
                "event_type": "variant_generated",
                "rule_name": "scheduling_rule",
                "variant_id": "dataops-scheduling-demo-v1",
                "metadata": {
                    "label": "DataOps scheduling visibility rule",
                    "scheduling_rule": "surface stale pipeline windows",
                },
            },
        ),
    ),
)


def main() -> None:
    random.seed(RANDOM_SEED)
    OUT.mkdir(exist_ok=True)
    for config in CONFIGS:
        seed_entries = load_seed_entries(config.seed_path)
        bundle = build_bundle(config, seed_entries)
        out_path = OUT / f"{config.name}_demo_bundle.json"
        out_path.write_text(json.dumps(bundle, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        verified = sum(1 for decision in bundle["decisions"] if decision["verified"])
        print(
            f"{config.name}: wrote {out_path.relative_to(REPO)} "
            f"decisions={len(bundle['decisions'])} verified={verified} "
            f"checkpoints={len(bundle['centroid_checkpoints'])} events={len(bundle['evolution_events'])}"
        )


def load_seed_entries(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        print(f"WARNING: missing seed file {path}")
        return []
    raw = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(raw, list):
        return [entry for entry in raw if isinstance(entry, dict)]
    if isinstance(raw, dict):
        for key in ("items", "examples", "data"):
            entries = raw.get(key)
            if isinstance(entries, list):
                return [entry for entry in entries if isinstance(entry, dict)]
    raise ValueError(f"Unsupported seed shape: {path}")


def build_bundle(config: DomainConfig, seed_entries: list[dict[str, Any]]) -> dict[str, Any]:
    decisions = build_decisions(config, seed_entries)
    centroids = build_centroids(config, decisions)
    rl_alpha, rl_beta = build_rl_state(config, decisions)
    return {
        "schema_version": "1.0",
        "domain": config.name,
        "generated_by": "scripts/regenerate_demo_bundles.py",
        "deterministic_seed": RANDOM_SEED,
        "min_decisions_to_skip": 180,
        "decisions": decisions,
        "centroid_checkpoints": build_checkpoints(config, centroids),
        "rl_state": {
            "key": "thompson_posteriors",
            "alpha": rl_alpha,
            "beta": rl_beta,
            "thompson_posteriors": {"alpha": rl_alpha, "beta": rl_beta},
            "updated_at": float(BASE_EPOCH + DECISIONS_PER_DOMAIN),
        },
        "evolution_events": build_events(config),
    }


def build_decisions(config: DomainConfig, seed_entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    verified_count = int(DECISIONS_PER_DOMAIN * VERIFIED_RATIO)
    override_count = int(verified_count * OVERRIDE_RATIO)
    decisions: list[dict[str, Any]] = []
    for idx in range(DECISIONS_PER_DOMAIN):
        seed = seed_entries[idx % len(seed_entries)] if seed_entries else {}
        category = coerce_member(seed.get("category"), config.categories, idx)
        recommended_action = coerce_member(
            seed.get("action_taken") or seed.get("recommended_action") or seed.get("action"),
            config.actions,
            idx,
        )
        category_index = config.categories.index(category)
        recommended_index = config.actions.index(recommended_action)
        factor_values = factors_for_seed(seed, config, idx)
        confidence = confidence_for(factor_values, recommended_index)
        probabilities = probabilities_for(config.actions, recommended_index, confidence)
        verified = idx < verified_count
        is_override = verified and idx < override_count
        actual_index = (recommended_index + 1) % len(config.actions) if is_override else recommended_index
        actual_action = config.actions[actual_index]
        is_correct = verified and actual_index == recommended_index and bool(seed.get("is_correct", True))
        timestamp = BASE_EPOCH + idx * 3_600
        metadata = {
            "source": "demo_bundle_generator",
            "seed_index": idx % len(seed_entries) if seed_entries else None,
            "override": is_override,
        }
        decision = {
            "decision_id": f"{config.prefix}-DEMO-{idx + 1:04d}",
            "domain": config.name,
            "category": category,
            "category_index": category_index,
            "recommended_action": recommended_action,
            "recommended_index": recommended_index,
            "confidence": confidence,
            "probabilities": probabilities,
            "probabilities_json": json.dumps(probabilities, sort_keys=True),
            "factors": factor_values,
            "factors_json": json.dumps(factor_values, sort_keys=True),
            "factor_vector": [factor_values[name] for name in config.factors],
            "factor_vector_json": json.dumps([factor_values[name] for name in config.factors]),
            "timestamp_epoch": timestamp,
            "created_at": float(timestamp),
            "verified": verified,
            "is_correct": is_correct,
            "actual_action": actual_action,
            "actual_index": actual_index,
            "verified_at": float(timestamp + 1_800),
            "context": {
                "actual_source": "seed" if seed else "synthetic",
                "override": is_override,
            },
            "metadata": metadata,
        }
        decisions.append(decision)
    return decisions


def factors_for_seed(seed: dict[str, Any], config: DomainConfig, idx: int) -> dict[str, float]:
    nested = seed.get("factors")
    factors = nested if isinstance(nested, dict) else seed
    result: dict[str, float] = {}
    for offset, name in enumerate(config.factors):
          if name in factors:
              result[name] = normalize_value(factors[name], name)
          elif name == "signal_confidence":
              result[name] = normalize_value(seed.get("signal_alignment", 0.5), name)
          elif name == "options_delta_exposure":
              result[name] = round(0.35 + 0.04 * ((idx + offset) % 9), 4)
          elif name == "options_iv_percentile":
              result[name] = round(0.30 + 0.05 * ((idx + offset) % 8), 4)
          elif name == "options_gamma_risk":
              result[name] = round(0.25 + 0.06 * ((idx + offset) % 7), 4)
          elif name == "price_memory_index":
              result[name] = round(0.35 + 0.05 * ((idx + offset) % 7), 4)
          else:
              result[name] = round(0.45 + 0.1 * random.random(), 4)
    return result


def normalize_value(value: Any, name: str) -> float:
    if isinstance(value, bool):
        return 1.0 if value else 0.0
    if isinstance(value, (int, float)):
        number = float(value)
        if 0.0 <= number <= 1.0:
            return round(number, 4)
        if name in {"day_of_week", "supplier_lead_time"}:
            return round(max(0.0, min(number / 7.0, 1.0)), 4)
        if name == "expected_demand":
            return round(max(0.0, min(number / 250.0, 1.0)), 4)
        return round(1.0 / (1.0 + math.exp(-number / 10.0)), 4)
    if isinstance(value, str):
        days = {
            "monday": 0.0,
            "tuesday": 1.0 / 6.0,
            "wednesday": 2.0 / 6.0,
            "thursday": 3.0 / 6.0,
            "friday": 4.0 / 6.0,
            "saturday": 5.0 / 6.0,
            "sunday": 1.0,
        }
        key = value.strip().lower()
        if key in days:
            return round(days[key], 4)
        return round((sum(ord(ch) for ch in key) % 100) / 100.0, 4)
    return 0.5


def confidence_for(factors: dict[str, float], recommended_index: int) -> float:
    avg = sum(factors.values()) / max(len(factors), 1)
    confidence = 0.55 + (avg * 0.35) - (recommended_index * 0.015)
    return round(max(0.35, min(confidence, 0.94)), 4)


def probabilities_for(actions: tuple[str, ...], recommended_index: int, confidence: float) -> list[float]:
    remainder = max(0.0, 1.0 - confidence)
    other = round(remainder / max(len(actions) - 1, 1), 6)
    probabilities = [other for _ in actions]
    probabilities[recommended_index] = confidence
    drift = round(1.0 - sum(probabilities), 6)
    probabilities[-1] = round(probabilities[-1] + drift, 6)
    return probabilities


def build_centroids(config: DomainConfig, decisions: list[dict[str, Any]]) -> list[list[list[float]]]:
    by_category = {category: [] for category in config.categories}
    for decision in decisions:
        by_category[decision["category"]].append(decision["factor_vector"])
    centroids: list[list[list[float]]] = []
    for category in config.categories:
        vectors = by_category[category]
        if vectors:
            base = [
                round(sum(vector[pos] for vector in vectors) / len(vectors), 4)
                for pos in range(len(config.factors))
            ]
        else:
            base = [0.5 for _ in config.factors]
        centroids.append([list(base) for _ in config.actions])
    return centroids


def build_checkpoints(config: DomainConfig, centroids: list[list[list[float]]]) -> list[dict[str, Any]]:
    checkpoints = []
    counts = (20, 60, 100, 150, 200)
    for idx, count in enumerate(counts):
        timestamp = BASE_EPOCH + count * 3_600
        metadata = {
            "label": f"{config.name} demo checkpoint {idx + 1}",
            "iks": round(0.04 + idx * 0.035, 4),
        }
        checkpoints.append(
            {
                "domain": config.name,
                "decision_id": None,
                "category": None,
                "centroids": centroids,
                "centroids_json": json.dumps(centroids, sort_keys=True),
                "decisions_count": count,
                "iks": metadata["iks"],
                "metadata": metadata,
                "metadata_json": json.dumps(metadata, sort_keys=True),
                "created_at": float(timestamp),
                "timestamp_epoch": timestamp,
                "decision_time_start": iso_time(BASE_EPOCH),
                "decision_time_end": iso_time(timestamp),
                "checkpoint_time": iso_time(timestamp + 900),
            }
        )
    return checkpoints


def build_rl_state(config: DomainConfig, decisions: list[dict[str, Any]]) -> tuple[list[float], list[float]]:
    alpha = [1.0 for _ in config.actions]
    beta = [1.0 for _ in config.actions]
    for decision in decisions:
        if not decision["verified"]:
            continue
        idx = int(decision["actual_index"])
        if decision["is_correct"]:
            alpha[idx] += 1.0
        else:
            beta[idx] += 1.0
    return [round(value, 4) for value in alpha], [round(value, 4) for value in beta]


def build_events(config: DomainConfig) -> list[dict[str, Any]]:
    events = []
    for idx, event in enumerate(config.events):
        row = dict(event)
        row.setdefault("event_type", "variant_generated")
        row.setdefault("rule_name", f"{config.name}_demo_rule")
        row.setdefault("variant_id", f"{config.name}-demo-{idx + 1}")
        row.setdefault("metadata", {})
        row["timestamp"] = iso_time(BASE_EPOCH + idx * 86_400)
        events.append(row)
    return events


def coerce_member(value: Any, allowed: tuple[str, ...], idx: int) -> str:
    text = str(value) if value is not None else ""
    if text in allowed:
        return text
    return allowed[idx % len(allowed)]


def iso_time(epoch: int) -> str:
    from datetime import datetime, timezone

    return datetime.fromtimestamp(epoch, timezone.utc).isoformat().replace("+00:00", "Z")


if __name__ == "__main__":
    main()
