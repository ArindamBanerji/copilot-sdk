#!/usr/bin/env python
"""Seed deterministic demo decisions directly into GraphStore.

This replaces the HTTP score/learn preseed ceremony. The writer uses stable
decision IDs so interrupted runs can resume safely and repeated runs do not
duplicate either decisions or outcomes.

SOC bootstraps from AGE via gae_state.init_learning_state() -- not seeded here.
"""

from __future__ import annotations

import argparse
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass
import json
import math
import os
from pathlib import Path
import sys
import threading
import time
from typing import Any

from copilot_sdk.config import GraphConfig
from copilot_sdk.graph.factory import create_graph_store
from copilot_sdk.graph.protocol import GraphStore, ProtocolV2GraphStore
from copilot_sdk.scoring.presets import PRESET_REGISTRY


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DECISION_COUNT = 200
DEFAULT_OVERRIDE_COUNT = 50
DOMAIN_NAMES = ("trading", "purchasing", "dataops", "s2p")
_BASE_TIMESTAMP = 1_767_225_600.0  # 2026-01-01T00:00:00Z
_SEED_COMPLETION_KEY = "demo_preseed:v1"
_SEED_MARKER_VERSION = 2
_RECEIPT_CONTRACT = "receipts:v1"
_AUTO_SEED_LOCKS = {domain: threading.RLock() for domain in DOMAIN_NAMES}

_SEED_PATHS = {
    "trading": REPO_ROOT / "apps" / "trading" / "backend" / "data" / "trading_seed_v2.json",
    "purchasing": REPO_ROOT / "apps" / "purchasing" / "backend" / "data" / "purchasing_seed_v2.json",
    "dataops": REPO_ROOT / "copilot_sdk" / "scoring" / "presets" / "dataops_seed.json",
}

_FIELD_MAP = {"purchasing": {"day_of_week": "day_of_week_factor"}}


@dataclass(frozen=True)
class SeedResult:
    """Counts from one domain's direct GraphStore seed run."""

    domain: str
    requested: int
    decisions_seeded: int
    outcomes_seeded: int
    decisions_skipped: int
    dry_run: bool = False


def _load_seed_file(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError(f"Seed file must contain a list: {path}")
    return [dict(row) for row in payload if isinstance(row, dict)]


def _s2p_event(index: int) -> dict[str, Any]:
    """Return the same deterministic invoice inputs as the retired HTTP seed."""
    categories = PRESET_REGISTRY["s2p"]().shape.category_names
    return {
        "event_id": f"demo-s2p-{index + 1:04d}",
        "category": categories[index % len(categories)],
        "amount": round(1000.0 + (index % 17) * 137.5, 2),
        "supplier_id": f"supplier-{index % 12:02d}",
        "supplier_name": f"Demo Supplier {index % 12:02d}",
        "contract_id": f"contract-{index % 8:02d}",
        "match_status": 1.0 if index % 5 else 0.0,
        "amount_variance_ratio": round(0.01 + (index % 13) * 0.012, 4),
        "duplicate_score": round(0.04 + (index % 10) * 0.07, 4),
        "supplier_exception_history": round((index % 6) * 0.09, 4),
        "payment_terms_impact": round(0.1 + (index % 8) * 0.05, 4),
        "commodity_index_correlation": round(0.2 + (index % 9) * 0.06, 4),
        "tax_regulatory_compliance": round(0.7 + (index % 5) * 0.05, 4),
        "environmental_risk": round(0.1 + (index % 6) * 0.07, 4),
    }


def _source_rows(domain: str) -> list[dict[str, Any]]:
    if domain == "s2p":
        return [_s2p_event(index) for index in range(DEFAULT_DECISION_COUNT)]
    try:
        path = _SEED_PATHS[domain]
    except KeyError as exc:
        raise ValueError(f"Unsupported seed domain: {domain}") from exc
    return _load_seed_file(path)


def _expanded_rows(domain: str, count: int) -> list[dict[str, Any]]:
    if count < 0:
        raise ValueError("count must be non-negative")
    rows = _source_rows(domain)
    if not rows and count:
        raise ValueError(f"No seed rows available for {domain}")
    return [dict(rows[index % len(rows)]) for index in range(count)] if rows else []


def _coerce_factor(value: Any) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return 0.5
    if not math.isfinite(number):
        return 0.5
    return max(0.0, min(1.0, number))


def _factors(
    domain: str,
    row: Mapping[str, Any],
    factor_names: Sequence[str],
) -> dict[str, float]:
    nested_value = row.get("factors")
    nested = nested_value if isinstance(nested_value, Mapping) else {}
    aliases = _FIELD_MAP.get(domain, {})
    return {
        name: _coerce_factor(
            nested[name] if name in nested else row.get(aliases.get(name, name))
        )
        for name in factor_names
    }


def _fixture_action(row: Mapping[str, Any], actions: Sequence[str], sequence: int) -> str:
    candidate = str(row.get("action_taken") or row.get("direction") or "")
    if candidate in actions:
        return candidate
    return actions[(sequence - 1) % len(actions)]


def _is_override(sequence: int, *, override_count: int) -> bool:
    return sequence % 4 == 0 and sequence <= override_count * 4


def _alternate_action(actions: Sequence[str], recommended: str) -> str:
    return next(action for action in actions if action != recommended)


def _seed_identity(domain: str, sequence: int) -> str:
    return f"seed-{domain}-{sequence:04d}"


def _seed_marker_complete(domain: str, graph_store: GraphStore) -> bool:
    marker = graph_store.get_governance(domain, _SEED_COMPLETION_KEY)
    return bool(
        marker
        and marker.get("status") == "complete"
        and marker.get("marker_version") == _SEED_MARKER_VERSION
        and marker.get("decision_count") == DEFAULT_DECISION_COUNT
        and marker.get("domain") == domain
        and marker.get("receipt_contract") == _RECEIPT_CONTRACT
    )


def _is_seed_decision(
    decision: Mapping[str, Any], domain: str, decision_id: str, sequence: int,
) -> bool:
    metadata = decision.get("metadata")
    source = decision.get("source")
    return bool(
        decision.get("decision_id") == decision_id
        and isinstance(metadata, Mapping)
        and metadata.get("planted") is True
        and metadata.get("seed_domain") == domain
        and metadata.get("seed_index") == sequence
        and (source == "demo_preseed" or metadata.get("source") == "demo_preseed")
    )


def _receipt_factors(decision: Mapping[str, Any]) -> dict[str, float]:
    factors = decision.get("factors")
    if isinstance(factors, Mapping):
        return {
            str(name): float(value)
            for name, value in sorted(factors.items(), key=lambda item: str(item[0]))
        }
    names = decision.get("factor_names")
    vector = decision.get("factor_vector")
    if (
        isinstance(names, Sequence)
        and not isinstance(names, (str, bytes))
        and isinstance(vector, Sequence)
        and not isinstance(vector, (str, bytes))
        and len(names) == len(vector)
    ):
        return {
            str(name): float(value)
            for name, value in sorted(zip(names, vector), key=lambda item: str(item[0]))
        }
    raise ValueError(
        f"Seed decision {decision.get('decision_id')!r} has no deterministic factors"
    )


def _append_seed_receipt(
    graph_store: GraphStore,
    domain: str,
    decision: Mapping[str, Any],
) -> None:
    append_receipt = getattr(graph_store, "append_evidence_receipt", None)
    if not callable(append_receipt):
        raise TypeError(
            "GraphStore does not support required append_evidence_receipt "
            "artifact persistence"
        )
    decision_id = str(decision["decision_id"])
    actual_action = str(decision["actual_action"])
    recommended_action = str(decision["recommended_action"])
    is_correct = decision.get("is_correct")
    if not isinstance(is_correct, bool):
        raise ValueError(
            f"Seed outcome is not verified for evidence receipt: {decision_id}"
        )
    canonical_payload = {
        "receipt_type": "demo_preseed_outcome_ingestion",
        "receipt_version": "v1",
        "domain": domain,
        "decision_id": decision_id,
        "category": str(decision["category"]),
        "factors": _receipt_factors(decision),
        "recommended_action": recommended_action,
        "actual_action": actual_action,
        "is_correct": is_correct,
        "outcome": "confirmed" if is_correct else "overridden",
        "provenance": {"source": "demo_preseed", "sample_type": "T-sim"},
    }
    receipt_intent_id = f"demo_preseed:v1:{domain}:{decision_id}:outcome"
    try:
        append_receipt(
            receipt_intent_id=receipt_intent_id,
            domain=domain,
            decision_id=decision_id,
            canonical_payload=canonical_payload,
            actor="demo_preseed",
            source_route="scripts.seed_all_decisions",
            metadata={
                "source": "demo_preseed",
                "sample_type": "T-sim",
                "receipt_contract": _RECEIPT_CONTRACT,
            },
        )
    except ValueError as exc:
        raise ValueError(
            f"Conflicting seed evidence receipt for {domain}/{decision_id}: {exc}"
        ) from exc


def _seed_population_matches(
    domain: str,
    graph_store: GraphStore,
    existing_count: int,
) -> bool:
    """Return whether every active row belongs to this deterministic seed set."""
    if existing_count < 0 or existing_count > DEFAULT_DECISION_COUNT:
        return False
    rows = graph_store.get_decisions(
        domain,
        limit=DEFAULT_DECISION_COUNT + 1,
        chronological=True,
    )
    if len(rows) != existing_count:
        return False
    expected = {
        _seed_identity(domain, sequence): sequence
        for sequence in range(1, DEFAULT_DECISION_COUNT + 1)
    }
    seen: set[str] = set()
    for row in rows:
        decision_id = str(row.get("decision_id") or "")
        sequence = expected.get(decision_id)
        metadata = row.get("metadata")
        if (
            sequence is None
            or decision_id in seen
            or not isinstance(metadata, Mapping)
            or metadata.get("planted") is not True
            or metadata.get("seed_domain") != domain
            or metadata.get("seed_index") != sequence
        ):
            return False
        seen.add(decision_id)
    return True


def _write_seed_completion_marker(
    domain: str, graph_store: GraphStore, *, receipts_complete: bool,
) -> None:
    """Publish completion only after the full deterministic population exists."""
    if not receipts_complete:
        return
    existing_count = int(graph_store.count_decisions(domain))
    if existing_count != DEFAULT_DECISION_COUNT:
        return
    if not _seed_population_matches(domain, graph_store, existing_count):
        return
    if _seed_marker_complete(domain, graph_store):
        return
    graph_store.save_governance(
        domain,
        _SEED_COMPLETION_KEY,
        {
            "status": "complete",
            "marker_version": _SEED_MARKER_VERSION,
            "domain": domain,
            "decision_count": DEFAULT_DECISION_COUNT,
            "receipt_contract": _RECEIPT_CONTRACT,
            "completed_at_epoch": time.time(),
        },
    )


def seed_domain(
    domain: str,
    graph_store: GraphStore | None,
    *,
    dry_run: bool = False,
    count: int = DEFAULT_DECISION_COUNT,
    override_count: int = DEFAULT_OVERRIDE_COUNT,
) -> SeedResult:
    """Write one domain's deterministic decisions and outcomes directly."""
    normalized = domain.strip().lower()
    if normalized not in DOMAIN_NAMES:
        raise ValueError(f"Unsupported seed domain: {domain}")
    preset = PRESET_REGISTRY[normalized]()
    categories = tuple(preset.shape.category_names)
    actions = tuple(preset.shape.action_names)
    factor_names = tuple(preset.shape.factor_names)
    source_count = len(_source_rows(normalized))
    rows = _expanded_rows(normalized, count)
    if dry_run:
        return SeedResult(normalized, len(rows), 0, 0, 0, dry_run=True)
    if graph_store is None:
        raise ValueError("graph_store is required unless dry_run=True")
    if not callable(getattr(graph_store, "append_evidence_receipt", None)):
        raise TypeError(
            "GraphStore does not support required append_evidence_receipt "
            "artifact persistence"
        )
    governed_store = (
        graph_store if isinstance(graph_store, ProtocolV2GraphStore) else None
    )

    decisions_seeded = 0
    outcomes_seeded = 0
    decisions_skipped = 0
    receipts_complete = True
    for sequence, row in enumerate(rows, start=1):
        decision_id = _seed_identity(normalized, sequence)
        factors = _factors(normalized, row, factor_names)
        category = str(row.get("category") or categories[(sequence - 1) % len(categories)])
        if category not in categories:
            raise ValueError(f"Unknown {normalized} category in seed row: {category}")
        recommended = _fixture_action(row, actions, sequence)
        category_index = categories.index(category)
        recommended_index = actions.index(recommended)
        created_at = _BASE_TIMESTAMP + float(sequence)
        confidence = round(0.70 + (sequence % 20) * 0.01, 6)
        probabilities = [0.0] * len(actions)
        probabilities[recommended_index] = confidence
        vector = [factors[name] for name in factor_names]
        decision_metadata = {
            "decision_id": decision_id,
            "entity_id": str(
                row.get("event_id")
                or row.get("trade_id")
                or row.get("order_id")
                or decision_id
            ),
            "category_index": category_index,
            "recommended_index": recommended_index,
            "factor_vector": vector,
            "factor_names": list(factor_names),
            "probabilities": probabilities,
            "created_at": created_at,
            "planted": True,
            "provenance": "sample",
            "evidence_tier": "T-sim",
            "source": "demo_preseed",
            "sample_type": "T-sim",
            "seed_domain": normalized,
            "seed_index": sequence,
            "source_seed_index": ((sequence - 1) % max(source_count, 1)) + 1,
        }

        existing = graph_store.get_decision(decision_id, normalized, include_outcome=True)
        if existing is None:
            if governed_store is not None:
                governed_store.write_governed_decision(
                    decision_id=decision_id,
                    domain=normalized,
                    category=category,
                    category_index=category_index,
                    recommended_action=recommended,
                    recommended_index=recommended_index,
                    confidence=confidence,
                    probabilities=probabilities,
                    factor_vector=vector,
                    factor_names=list(factor_names),
                    source="demo_preseed",
                    scorer_version="demo_preseed_v1",
                    preset_version="demo_preseed_v1",
                    factor_schema_version="demo_preseed_v1",
                    metadata=decision_metadata,
                )
                written_id = decision_id
            else:
                written_id = graph_store.write_decision(
                    normalized,
                    category,
                    recommended,
                    confidence,
                    factors,
                    metadata=decision_metadata,
                )
            if written_id != decision_id:
                raise RuntimeError(
                    f"GraphStore changed governed seed ID {decision_id!r} to {written_id!r}"
                )
            decisions_seeded += 1
        else:
            if not _is_seed_decision(existing, normalized, decision_id, sequence):
                raise ValueError(
                    f"Refusing to repair non-seed decision collision: {decision_id}"
                )
            decisions_skipped += 1

        current = graph_store.get_decision(decision_id, normalized, include_outcome=True)
        if current is not None and current.get("actual_action") is not None:
            if not _is_seed_decision(current, normalized, decision_id, sequence):
                raise ValueError(
                    f"Refusing to attest non-seed decision: {decision_id}"
                )
            if not isinstance(current.get("is_correct"), bool):
                receipts_complete = False
                continue
            _append_seed_receipt(graph_store, normalized, current)
            continue
        is_override = _is_override(sequence, override_count=override_count)
        actual = _alternate_action(actions, recommended) if is_override else recommended
        actual_index = actions.index(actual)
        graph_store.write_outcome(
            decision_id,
            actual,
            not is_override,
            {
                "actual_index": actual_index,
                "verified_at": created_at + 0.5,
                "context": {
                    "planted": True,
                    "provenance": "sample",
                    "evidence_tier": "T-sim",
                    "seed_domain": normalized,
                    "seed_index": sequence,
                    "is_preseed_override": is_override,
                },
            },
            domain=normalized,
            outcome="overridden" if is_override else "confirmed",
            verified_at_epoch=created_at + 0.5,
            analyst_action=actual,
            final_action=actual,
            recommended_action=recommended,
            was_override=is_override,
        )
        outcomes_seeded += 1
        persisted = graph_store.get_decision(
            decision_id, normalized, include_outcome=True
        )
        if persisted is None or not isinstance(persisted.get("is_correct"), bool):
            receipts_complete = False
            continue
        _append_seed_receipt(graph_store, normalized, persisted)

    result = SeedResult(
        normalized,
        len(rows),
        decisions_seeded,
        outcomes_seeded,
        decisions_skipped,
    )
    if count == DEFAULT_DECISION_COUNT:
        _write_seed_completion_marker(
            normalized, graph_store, receipts_complete=receipts_complete
        )
    return result


def auto_seed_domain_if_empty(domain: str, graph_store: GraphStore) -> int:
    """Seed or resume a deterministic startup population without touching real data."""
    normalized = domain.strip().lower()
    if normalized not in DOMAIN_NAMES:
        raise ValueError(f"Unsupported seed domain: {domain}")
    with _AUTO_SEED_LOCKS[normalized]:
        if os.environ.get("DEMO_NO_RESEED") == "1":
            print(f"[{normalized}] auto-seed skipped: DEMO_NO_RESEED=1")
            return 0
        if _seed_marker_complete(normalized, graph_store):
            print(f"[{normalized}] auto-seed skipped: completion marker present")
            return 0
        existing = int(graph_store.count_decisions(normalized))
        if existing and not _seed_population_matches(normalized, graph_store, existing):
            print(f"[{normalized}] auto-seed skipped: {existing} non-seed decisions exist")
            return 0
        result = seed_domain(normalized, graph_store)
        action = "resumed" if existing else "into AGE"
        print(
            f"[{normalized}] auto-seed {action}: "
            f"{result.decisions_seeded} decisions"
        )
        return result.decisions_seeded


def seed_all_domains(
    graph_store_factory: Callable[[str], GraphStore],
    *,
    domains: Iterable[str] = DOMAIN_NAMES,
    dry_run: bool = False,
    count: int = DEFAULT_DECISION_COUNT,
) -> list[SeedResult]:
    """Seed each requested domain through a caller-supplied GraphStore factory."""
    return [
        seed_domain(domain, graph_store_factory(domain), dry_run=dry_run, count=count)
        for domain in domains
    ]


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Seed deterministic decisions directly into AGE GraphStore."
    )
    parser.add_argument(
        "--domain",
        choices=("all", *DOMAIN_NAMES),
        action="append",
        help="Domain to seed; repeat for a subset (default: all four SDK domains).",
    )
    parser.add_argument(
        "--graph-dsn",
        default=os.environ.get("GRAPH_DSN"),
        help="AGE connection DSN (default: GRAPH_DSN or domain GraphConfig).",
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Validate seed inputs without graph writes."
    )
    return parser


def _configured_store(domain: str, graph_dsn: str | None) -> GraphStore:
    overrides: dict[str, Any] = {"backend": "age"}
    if graph_dsn:
        overrides["dsn"] = graph_dsn
    config = GraphConfig.load(domain, overrides=overrides)
    return create_graph_store(config=config)


def main(argv: Sequence[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    selected = list(args.domain or ["all"])
    if "all" in selected and len(selected) > 1:
        parser.error("--domain all cannot be combined with another --domain")
    domains = DOMAIN_NAMES if selected == ["all"] else tuple(dict.fromkeys(selected))
    stores: list[GraphStore] = []
    try:
        for domain in domains:
            if args.dry_run:
                result = seed_domain(domain, None, dry_run=True)
            else:
                store = _configured_store(domain, args.graph_dsn)
                stores.append(store)
                result = seed_domain(domain, store)
            print(
                f"Seeded {result.decisions_seeded} decisions + "
                f"{result.outcomes_seeded} outcomes for {domain}"
            )
            if result.decisions_skipped:
                print(f"Skipped {result.decisions_skipped} existing decisions for {domain}")
            if result.dry_run:
                print(f"Dry run validated {result.requested} decisions for {domain}")
    finally:
        for store in stores:
            store.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
