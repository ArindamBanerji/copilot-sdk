"""Trigger an auditable factor-quality warm-start between copilot domains."""

from __future__ import annotations

import argparse
import json
import math
import sys
from typing import Any

from copilot_sdk.scoring.presets import PRESET_REGISTRY
from copilot_sdk.scoring.scorer import CompoundingScorer
from copilot_sdk.transfer import SharedPatternRegistry, TransferPattern


def _latest_source_fingerprint(store: Any, source: str) -> dict[str, Any] | None:
    rows = store._run_query(
        f"""
        MATCH (fp:Fingerprint)
        WHERE fp.domain = {store._S(source)}
        RETURN fp
        ORDER BY fp.created_at DESC
        LIMIT 1
        """,
    )
    if not rows:
        return None
    raw = rows[0].get("fp", rows[0])
    return dict(raw) if isinstance(raw, dict) else None


def _decode_json(value: Any, default: Any) -> Any:
    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return default
    return value


def build_registry(store: Any, source: str, target: str) -> SharedPatternRegistry:
    """Build a compatibility registry from the latest graph fingerprint."""
    fingerprint = _latest_source_fingerprint(store, source)
    registry = SharedPatternRegistry()
    if fingerprint is None or not fingerprint.get("fingerprint_id"):
        print(f"NOT_PROVEN: no fingerprint found for source domain '{source}'")
        print("Run score/learn cycles for the source domain first (P6.3a)")
        sys.exit(1)
    preset = PRESET_REGISTRY[target]()
    source_names: list[str] = []
    raw_names = fingerprint.get("factor_names")
    if isinstance(raw_names, str):
        try:
            decoded_names = json.loads(raw_names)
        except json.JSONDecodeError:
            decoded_names = []
        if isinstance(decoded_names, list):
            source_names = [str(name) for name in decoded_names]
    elif isinstance(raw_names, list):
        source_names = [str(name) for name in raw_names]
    factor_stats = _decode_json(fingerprint.get("factor_stats"), {})
    if not isinstance(factor_stats, dict):
        factor_stats = {}
    factor_rows = factor_stats.get("factors", [])
    if not isinstance(factor_rows, list):
        factor_rows = []
    stats_by_name = {
        str(item.get("name")): item
        for item in factor_rows
        if isinstance(item, dict) and item.get("name")
    }
    factor_mapping = {
        (source_names[index] if index < len(source_names) else f"{source}:{index}"): name
        for index, name in enumerate(preset.shape.factor_names)
        if (source_names[index] if index < len(source_names) else f"{source}:{index}")
        in stats_by_name
    }
    centroid_delta: list[float] = []
    mapped_factor_count = 0
    for target_name in preset.shape.factor_names:
        source_name = next(
            (name for name, mapped_name in factor_mapping.items() if mapped_name == target_name),
            None,
        )
        stats = stats_by_name.get(source_name or "", {})
        value = stats.get("weight")
        if value is None:
            value = stats.get("mean")
        if value is None:
            value = stats.get("sigma")
        try:
            numeric = 0.0 if value is None else float(value)
        except (TypeError, ValueError):
            numeric = 0.0
        if math.isfinite(numeric) and value is not None:
            mapped_factor_count += 1
            centroid_delta.append(numeric)
        else:
            centroid_delta.append(0.0)
    validation_status = (
        "validated"
        if mapped_factor_count == len(preset.shape.factor_names)
        else "partial"
    )
    registry.register(
        TransferPattern(
            pattern_id=f"script-{source}-{target}",
            source_copilot=source,
            pattern_type="factor_quality_transfer",
            category=preset.shape.category_names[0],
            action=preset.shape.action_names[0],
            win_rate=1.0,
            centroid_delta=centroid_delta,
            confidence=1.0,
            metadata={
                "source_domain": source,
                "source_fingerprint_id": str(fingerprint["fingerprint_id"]),
                "factor_mapping": factor_mapping,
                "factor_stats": factor_stats,
                "validation_status": validation_status,
            },
        )
    )
    return registry


def _load_age_store(age_dsn: str, graph_name: str) -> Any:
    from scripts.phase6_claim_proof import _load_age_store as load_store

    return load_store(age_dsn, graph_name)


def run_warm_start(
    *,
    source: str,
    target: str,
    age_dsn: str,
    graph_name: str,
) -> dict[str, Any]:
    if source not in PRESET_REGISTRY or target not in PRESET_REGISTRY:
        raise ValueError("source and target must be configured copilot domains")
    raw_store = _load_age_store(age_dsn, graph_name)
    from ci_platform.graph.age_sdk_adapter import AGEGraphStoreAdapter

    store = AGEGraphStoreAdapter(store=raw_store)
    try:
        registry = build_registry(raw_store, source, target)
        scorer = CompoundingScorer.from_preset(
            target,
            graph_store=store,
            profile="production",
        )
        summary: dict[str, Any] = dict(scorer.warm_start(registry))
        summary["transfer_patterns"] = store.get_transfer_patterns(
            source_domain=source,
            target_domain=target,
        )
        return summary
    finally:
        store.close()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Trigger a Phase 6 warm-start")
    parser.add_argument("--dry-run", action="store_true", help="print the plan without connecting")
    parser.add_argument("--apply", action="store_true", help="apply the warm-start")
    parser.add_argument("--verify", action="store_true", help="verify TransferPatterns in AGE")
    parser.add_argument("--source")
    parser.add_argument("--target")
    parser.add_argument("--age-dsn")
    parser.add_argument("--graph-name", default="soc_graph")
    args = parser.parse_args(argv)

    if not args.apply and not args.verify:
        print("Dry-run: no graph writes")
        print("Plan: resolve source fingerprint, apply target warm-start, verify TransferPattern")
        return 0
    if args.apply and (not args.source or not args.target):
        parser.error("--source and --target are required with --apply")
    if args.apply and (args.source not in PRESET_REGISTRY or args.target not in PRESET_REGISTRY):
        parser.error("--source and --target must be configured copilot domains")
    if not args.age_dsn:
        parser.error("--age-dsn is required with --apply or --verify")

    if args.apply:
        print(json.dumps(run_warm_start(
            source=args.source,
            target=args.target,
            age_dsn=args.age_dsn,
            graph_name=args.graph_name,
        ), sort_keys=True, default=str))
    if args.verify:
        store = _load_age_store(args.age_dsn, args.graph_name)
        try:
            rows = store.get_transfer_patterns(
                source_domain=args.source if args.source else None,
                target_domain=args.target if args.target else None,
            )
            print(json.dumps(rows, sort_keys=True, default=str))
        finally:
            store.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
