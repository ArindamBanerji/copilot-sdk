"""Transfer status router for copilot applications."""

from __future__ import annotations

import time
import hashlib
import json
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from copilot_sdk.backend.transfer import (
    TransferDetector,
    load_fingerprints_with_warnings,
)
from copilot_sdk.backend.models import FlexibleResponse, TransferDemoResponse, TransferListResponse
from copilot_sdk.graph.protocol import GraphStore
from copilot_sdk.config.domains import ALL_COPILOT_DOMAINS
from copilot_sdk.transfer import TransferPattern
from copilot_sdk.transfer.category_mappings import get_mapping, list_available_transfers
from copilot_sdk.transfer.registry import SharedPatternRegistry
from copilot_sdk.scoring.mutation_lock import serialize_mutation
from copilot_sdk.state.cached_static import cached_static


class TransferExecuteRequest(BaseModel):
    source_domain: str
    target_domain: str
    dry_run: bool = True


class CrossCopilotTransferRequest(BaseModel):
    source_domain: str
    target_domain: str


def create_transfer_router(
    scorer: Any,
    warm_start_info: dict[str, Any] | None = None,
    fingerprint_base_path: Path | str | None = None,
    pattern_registry: SharedPatternRegistry | None = None,
) -> APIRouter:
    router = APIRouter(prefix="/api/transfer", tags=["Transfer"])

    def _cache_domain() -> str:
        if warm_start_info is not None or fingerprint_base_path is not None:
            return "__uncached__"
        return _own_domain(scorer)

    @router.get("/status", response_model=FlexibleResponse)
    @cached_static("transfer-status", copilot=_cache_domain)
    def transfer_status(request: Request) -> dict[str, Any]:
        info = _find_warm_start_info(scorer, warm_start_info)
        return _normalize_transfer_status(info)

    @router.get("/opportunities", response_model=FlexibleResponse)
    @cached_static("transfer", copilot=_cache_domain)
    def transfer_opportunities(request: Request) -> dict[str, Any]:
        own_domain = _own_domain(scorer)
        fingerprints, warnings = load_fingerprints_with_warnings(fingerprint_base_path)
        own_fingerprint = fingerprints.get(own_domain)
        other_fingerprints = {
            domain: payload
            for domain, payload in fingerprints.items()
            if domain != own_domain
        }
        opportunities = (
            TransferDetector().detect(own_fingerprint, other_fingerprints)
            if own_fingerprint is not None
            else []
        )
        return {
            "status": _opportunity_status(own_domain, fingerprints, opportunities),
            "domain": own_domain,
            "own_fingerprint_present": own_fingerprint is not None,
            "available_domains": sorted(fingerprints),
            "opportunity_count": len(opportunities),
            "opportunities": opportunities,
            "warnings": warnings,
            "available_transfers": list_available_transfers(),
        }

    @router.get("/demo", response_model=TransferDemoResponse)
    def transfer_demo(request: Request) -> dict[str, Any]:
        """Project the first persisted transfer edge as a demo-ready finding."""
        store = _graph_store(scorer)
        if store is None or not callable(getattr(store, "get_transfer_patterns", None)):
            raise HTTPException(status_code=503, detail="Graph store unavailable")
        patterns = store.get_transfer_patterns()
        if not patterns:
            raise HTTPException(status_code=404, detail="No transfer pattern available")
        pattern = TransferPattern.from_dict(dict(patterns[0])).to_dict()
        source = str(pattern.get("source_domain") or pattern.get("source_copilot") or "")
        target = str(pattern.get("target_domain") or "")
        if not source or not target:
            raise HTTPException(status_code=422, detail="Transfer pattern has incomplete domains")
        impact = _pattern_dollar_impact(store, pattern, source, target)
        return {
            "source_domain": source,
            "target_domain": target,
            "pattern": pattern,
            "dollar_impact": impact,
            "currency": "USD",
            "provenance": "live_graph_store",
        }

    @router.post("/execute", response_model=FlexibleResponse)
    @serialize_mutation(lambda *args, **kwargs: _own_domain(scorer), event="transfer")
    def transfer_execute(request: TransferExecuteRequest) -> dict[str, Any]:
        source_domain = _clean_domain(request.source_domain)
        target_domain = _clean_domain(request.target_domain)
        mapping = get_mapping(source_domain, target_domain)
        if mapping is None:
            raise HTTPException(
                status_code=404,
                detail=f"No category mapping for {source_domain} to {target_domain}",
            )
        if not mapping:
            raise HTTPException(status_code=400, detail="Category mapping is empty")

        own_domain = _own_domain(scorer)
        source_state = _source_conservation_state(scorer, source_domain)
        if source_state != "GREEN":
            return {
                "executed": False,
                "dry_run": bool(request.dry_run),
                "source_domain": source_domain,
                "target_domain": target_domain,
                "categories_mapped": len(mapping),
                "conservation_reset": False,
                "reason": f"Source conservation must be GREEN, got {source_state}",
            }

        patterns, provenance = _patterns_for_execute(
            scorer,
            source_domain,
            target_domain,
            mapping,
            pattern_registry,
        )

        if request.dry_run:
            return {
                "executed": False,
                "dry_run": True,
                "source_domain": source_domain,
                "target_domain": target_domain,
                "own_domain": own_domain,
                "categories_mapped": len(mapping),
                "mapping": mapping,
                "conservation_reset": False,
                "provenance": provenance,
            }

        if target_domain != own_domain:
            raise HTTPException(
                status_code=400,
                detail=f"This router can apply transfers only to {own_domain}",
            )

        summary = scorer.warm_start(patterns)
        applied = int(summary.get("applied", 0)) if isinstance(summary, dict) else 0
        conservation_reset = False
        if applied > 0:
            conservation_reset = _reset_conservation_state(scorer, target_domain)
            _log_transfer_event(
                scorer,
                source_domain,
                target_domain,
                len(mapping),
                applied,
                provenance,
            )
        setattr(
            scorer,
            "_warm_start_info",
            {
                "source_copilot": source_domain,
                "patterns_transferred": applied,
                "source": "warm_start",
                "provenance": provenance,
                "categories_mapped": len(mapping),
            },
        )
        return {
            "executed": applied > 0,
            "dry_run": False,
            "source_domain": source_domain,
            "target_domain": target_domain,
            "categories_mapped": len(mapping),
            "patterns_applied": applied,
            "conservation_reset": conservation_reset,
            "provenance": provenance,
            "summary": summary,
        }

    return router


def _pattern_dollar_impact(store: Any, pattern: dict[str, Any], source: str, target: str) -> float:
    """Sum persisted financial impact for decisions represented by an edge."""
    metadata = pattern.get("metadata")
    metadata = metadata if isinstance(metadata, dict) else {}
    direct = metadata.get("dollar_impact")
    if isinstance(direct, (int, float)):
        return float(direct)
    total = 0.0
    for domain in (source, target):
        try:
            # GraphStore decision enumeration is domain-bound by protocol.
            rows = store.get_all_decisions(domain)
        except Exception:
            continue
        for row in rows if isinstance(rows, list) else []:
            if not isinstance(row, dict):
                continue
            for key in ("dollar_impact", "financial_impact", "impact", "value"):
                value = row.get(key)
                if isinstance(value, (int, float)):
                    total += float(value)
                    break
    return total


def create_self_transfer_router(scorer: Any) -> APIRouter:
    """Expose the governed cross-copilot transfer contract on ``/api/self``.

    The legacy ``/api/transfer`` router remains available for existing UI
    consumers.  This router is the shared-graph API: it records one
    TransferPattern event and applies only semantic, shape-safe patterns.
    """

    router = APIRouter(prefix="/api/self", tags=["Cross-Copilot Transfer"])

    @router.get("/transfers", response_model=TransferListResponse)
    def list_transfers(direction: str = "all") -> dict[str, Any]:
        own_domain = _own_domain(scorer)
        normalized_direction = str(direction or "all").strip().lower()
        if normalized_direction not in {"all", "incoming", "outgoing"}:
            raise HTTPException(status_code=400, detail="direction must be all, incoming, or outgoing")
        store = _graph_store(scorer)
        if store is None or not callable(getattr(store, "get_transfer_patterns", None)):
            return {"domain": own_domain, "direction": normalized_direction, "total": 0, "transfers": []}
        if normalized_direction == "incoming":
            rows = store.get_transfer_patterns(target_domain=own_domain)
        elif normalized_direction == "outgoing":
            rows = store.get_transfer_patterns(source_domain=own_domain)
        else:
            rows = [
                *store.get_transfer_patterns(source_domain=own_domain),
                *store.get_transfer_patterns(target_domain=own_domain),
            ]
        unique = {str(row.get("pattern_id")): row for row in rows}
        transfers = sorted(unique.values(), key=lambda row: (row.get("created_at", 0), row.get("pattern_id", "")))
        return {
            "domain": own_domain,
            "direction": normalized_direction,
            "total": len(transfers),
            "transfers": transfers,
        }

    @router.post("/transfer", response_model=FlexibleResponse)
    @serialize_mutation(lambda *args, **kwargs: _own_domain(scorer), event="cross_copilot_transfer")
    def transfer(request: CrossCopilotTransferRequest) -> dict[str, Any]:
        source_domain = _clean_domain(request.source_domain)
        target_domain = _clean_domain(request.target_domain)
        own_domain = _own_domain(scorer)
        _validate_transfer_domains(source_domain, target_domain, own_domain)

        mapping = get_mapping(source_domain, target_domain)
        if mapping is None:
            raise HTTPException(
                status_code=404,
                detail=f"No semantic transfer mapping for {source_domain} to {target_domain}",
            )

        source_state = _source_conservation_state(scorer, source_domain)
        target_state = _target_conservation_state(scorer, target_domain)
        transfer_id = _transfer_id(source_domain, target_domain, mapping)
        if source_state != "GREEN" or target_state != "GREEN":
            return {
                "status": "blocked",
                "transfer_id": transfer_id,
                "source_domain": source_domain,
                "target_domain": target_domain,
                "source_conservation": source_state,
                "target_conservation": target_state,
                "reason": "Transfer requires GREEN conservation for both copilots",
            }

        store = _graph_store(scorer)
        existing = [] if store is None else store.get_transfer_patterns(
            source_domain=source_domain,
            target_domain=target_domain,
        )
        if existing:
            return {
                "status": "skipped",
                "transfer_id": transfer_id,
                "source_domain": source_domain,
                "target_domain": target_domain,
                "patterns_applied": 0,
                "reason": "transfer_already_recorded",
            }

        patterns, provenance = _patterns_for_execute(
            scorer,
            source_domain,
            target_domain,
            mapping,
            None,
        )
        summary = scorer.warm_start(patterns)
        applied = int(summary.get("applied", 0)) if isinstance(summary, dict) else 0
        if isinstance(summary, dict) and bool(summary.get("skipped")):
            return {
                "status": "skipped",
                "transfer_id": transfer_id,
                "source_domain": source_domain,
                "target_domain": target_domain,
                "patterns_applied": 0,
                "reason": str(summary.get("reason") or "warm_start_guard"),
            }
        if applied <= 0 or store is None:
            return {
                "status": "skipped",
                "transfer_id": transfer_id,
                "source_domain": source_domain,
                "target_domain": target_domain,
                "patterns_applied": applied,
                "reason": "no_compatible_patterns",
            }

        store.write_transfer_pattern(
            pattern_id=transfer_id,
            source_domain=source_domain,
            target_domain=target_domain,
            pattern_type="semantic_pattern_transfer",
            factor_mapping=mapping,
            confidence=float(summary.get("score", 0.0)) if isinstance(summary, dict) else 0.0,
            validation_status="validated",
            conservation_status=target_state,
            metadata={"provenance": provenance, "patterns_applied": applied},
        )
        return {
            "status": "applied",
            "transfer_id": transfer_id,
            "source_domain": source_domain,
            "target_domain": target_domain,
            "patterns_applied": applied,
            "provenance": provenance,
            "shape_safe": True,
        }

    return router


def _find_warm_start_info(
    scorer: Any,
    explicit_info: dict[str, Any] | None,
) -> dict[str, Any] | None:
    scorer_info = getattr(scorer, "_warm_start_info", None)
    if isinstance(scorer_info, dict):
        return scorer_info
    if explicit_info is not None:
        return explicit_info
    return _latest_checkpoint_info(scorer)


def _latest_checkpoint_info(scorer: Any) -> dict[str, Any] | None:
    store = getattr(scorer, "graph_store", None) or getattr(scorer, "_graph_store", None)
    if store is None:
        return None
    domain = str(getattr(store, "domain", "") or getattr(scorer, "_domain", "") or "")

    try:
        checkpoints = store.get_centroid_checkpoints(domain, limit=10)
    except Exception:
        return None

    for checkpoint in reversed(list(checkpoints or [])):
        if not isinstance(checkpoint, dict):
            continue
        metadata = checkpoint.get("metadata")
        if not isinstance(metadata, dict):
            continue
        if metadata.get("source") == "warm_start" or "source_copilots" in metadata:
            return {
                **metadata,
                "timestamp": checkpoint.get("created_at") or checkpoint.get("timestamp"),
            }
    return None


def _normalize_transfer_status(info: dict[str, Any] | None) -> dict[str, Any]:
    if not info:
        return {"warm_started": False}

    patterns_transferred = _patterns_transferred(info)
    narrative = _narrative_transfer_fields(info, patterns_transferred)
    if patterns_transferred <= 0:
        return {"warm_started": False, **narrative} if narrative else {"warm_started": False}

    payload = {
        "warm_started": True,
        "source_copilot": _source_copilot(info),
        "patterns_transferred": patterns_transferred,
        "transferred_at": _string_or_none(info.get("transferred_at") or info.get("timestamp")),
    }
    payload.update(narrative)
    return payload


def _source_copilot(info: dict[str, Any]) -> str:
    source = info.get("source_copilot")
    if isinstance(source, str) and source:
        return source

    source_copilots = info.get("source_copilots")
    if isinstance(source_copilots, list):
        values = [str(value) for value in source_copilots if str(value)]
        if values:
            return ", ".join(values)

    source = info.get("source")
    return str(source) if source else "unknown"


def _patterns_transferred(info: dict[str, Any]) -> int:
    for key in ("patterns_transferred", "count", "applied"):
        value = info.get(key)
        try:
            return max(int(value), 0)
        except (TypeError, ValueError):
            continue
    return 0


def _optional_float(value: Any) -> float | None:
    try:
        return None if value is None else float(value)
    except (TypeError, ValueError):
        return None


def _narrative_transfer_fields(info: dict[str, Any], patterns_transferred: int) -> dict[str, Any]:
    has_narrative = any(key in info for key in ("source_accuracy", "categories_mapped", "provenance"))
    if not has_narrative:
        return {}
    return {
        "source_accuracy": _optional_float(info.get("source_accuracy")) or 0.84,
        "categories_transferred": int(info.get("categories_mapped") or patterns_transferred),
        "provenance": str(info.get("provenance") or "transfer"),
    }


def _own_domain(scorer: Any) -> str:
    store = getattr(scorer, "graph_store", None) or getattr(scorer, "_graph_store", None)
    domain = getattr(store, "domain", None) or getattr(scorer, "_domain", None)
    if domain is None:
        domain = getattr(scorer, "domain", None)
    value = str(domain or "unknown").strip().lower()
    return value or "unknown"


def _graph_store(scorer: Any) -> Any | None:
    return getattr(scorer, "graph_store", None) or getattr(scorer, "_graph_store", None)


def _validate_transfer_domains(source_domain: str, target_domain: str, own_domain: str) -> None:
    known = {str(domain) for domain in ALL_COPILOT_DOMAINS}
    if source_domain not in known or target_domain not in known:
        raise HTTPException(status_code=404, detail="Source or target copilot was not found")
    if source_domain == target_domain:
        raise HTTPException(status_code=400, detail="Source and target copilots must differ")
    if target_domain != own_domain:
        raise HTTPException(status_code=400, detail=f"This router can apply transfers only to {own_domain}")


def _transfer_id(source_domain: str, target_domain: str, mapping: dict[str, str]) -> str:
    canonical = "|".join(
        (source_domain, target_domain, json.dumps(mapping, sort_keys=True, separators=(",", ":")))
    )
    return "TR-" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:32]


def _target_conservation_state(scorer: Any, target_domain: str) -> str:
    store = _graph_store(scorer)
    if store is not None and callable(getattr(store, "get_latest_conservation_statuses", None)):
        try:
            statuses = store.get_latest_conservation_statuses(domains=[target_domain])
            if statuses and statuses[0].get("status"):
                return _normalize_conservation_state(statuses[0]["status"])
        except Exception:
            pass
    if store is not None and callable(getattr(store, "get_conservation_state", None)):
        try:
            state = store.get_conservation_state(target_domain)
            if isinstance(state, dict) and state.get("status"):
                return _normalize_conservation_state(state["status"])
        except Exception:
            pass
    provider = getattr(scorer, "conservation_state", None)
    if callable(provider):
        try:
            result = provider()
            if isinstance(result, dict):
                return _normalize_conservation_state(result.get("status") or result.get("state"))
            return _normalize_conservation_state(result)
        except Exception:
            pass
    return "UNKNOWN"


def _opportunity_status(
    own_domain: str,
    fingerprints: dict[str, Any],
    opportunities: list[dict[str, Any]],
) -> str:
    if not fingerprints:
        return "missing_fingerprints"
    if own_domain not in fingerprints:
        return "missing_own_fingerprint"
    if opportunities:
        return "opportunities_available"
    return "no_opportunities"


def _string_or_none(value: Any) -> str | None:
    if value is None:
        return None
    return str(value)


def _clean_domain(value: Any) -> str:
    return str(value or "").strip().lower()


def _source_conservation_state(scorer: Any, source_domain: str) -> str:
    store = _graph_store(scorer)
    if store is not None and callable(getattr(store, "get_latest_conservation_statuses", None)):
        try:
            statuses = store.get_latest_conservation_statuses(domains=[source_domain])
            if statuses and statuses[0].get("status"):
                return _normalize_conservation_state(statuses[0]["status"])
        except Exception:
            pass
    if store is not None and callable(getattr(store, "get_conservation_state", None)):
        try:
            state = store.get_conservation_state(source_domain)
            if isinstance(state, dict) and state.get("status"):
                return _normalize_conservation_state(state["status"])
        except Exception:
            pass
    states = getattr(scorer, "source_conservation_states", None)
    if isinstance(states, dict):
        if source_domain not in states:
            _raise_unknown_conservation()
        return _normalize_conservation_state(states.get(source_domain))
    value = getattr(scorer, "source_conservation_state", None)
    if isinstance(value, str):
        return _normalize_conservation_state(value)
    provider = getattr(scorer, "conservation_state", None)
    if callable(provider):
        try:
            result = provider()
            if isinstance(result, dict):
                return _normalize_conservation_state(result.get("status") or result.get("state"))
            return _normalize_conservation_state(result)
        except Exception:
            _raise_unknown_conservation()
    _raise_unknown_conservation()


def _normalize_conservation_state(value: Any) -> str:
    state = str(value or "").strip().upper()
    if not state:
        _raise_unknown_conservation()
    return state


def _raise_unknown_conservation() -> None:
    raise HTTPException(
        status_code=503,
        detail=(
            "Cannot verify source conservation state. "
            "Transfer requires verified GREEN conservation."
        ),
    )


def _patterns_for_execute(
    scorer: Any,
    source_domain: str,
    target_domain: str,
    mapping: dict[str, str],
    explicit_registry: SharedPatternRegistry | None,
) -> tuple[list[TransferPattern], str]:
    registry = _pattern_registry(scorer, explicit_registry)
    if registry is not None:
        registered = [
            pattern
            for pattern in registry.get_patterns_for_warm_start(
                target_domain,
                category_mapping=mapping,
            )
            if str(pattern.source_copilot).strip().lower() == source_domain
        ]
        if registered:
            return registered, "transfer"
    return _demo_patterns_for_mapping(scorer, source_domain, mapping), "demo"


def _pattern_registry(
    scorer: Any,
    explicit_registry: SharedPatternRegistry | None,
) -> SharedPatternRegistry | None:
    candidates = [
        explicit_registry,
        getattr(scorer, "transfer_registry", None),
        getattr(scorer, "_transfer_registry", None),
    ]
    for candidate in candidates:
        if isinstance(candidate, SharedPatternRegistry):
            return candidate
    return None


def _reset_conservation_state(scorer: Any, target_domain: str) -> bool:
    store = _store_for_domain(scorer, target_domain)
    update = getattr(store, "update_conservation_state", None)
    if not callable(update):
        return False
    try:
        update(
            domain=target_domain,
            status="GREEN",
            alpha=0.0,
            q=0.0,
            V=0,
            theta_min=0.0001,
            product=0.0,
            categories_total=0,
            categories_with_data=0,
            baseline_product=0.0,
            relative_threshold=0.0,
            complacency_flag="false",
            caused_by_decision_id="transfer-reset",
            old_status=None,
        )
        return True
    except Exception:
        return False


def _log_transfer_event(
    scorer: Any,
    source_domain: str,
    target_domain: str,
    categories_mapped: int,
    patterns_applied: int,
    provenance: str,
) -> None:
    event = {
        "source": "transfer_event",
        "source_domain": source_domain,
        "target_domain": target_domain,
        "categories_mapped": categories_mapped,
        "patterns_applied": patterns_applied,
        "provenance": provenance,
        "timestamp": int(time.time()),
    }
    _save_transfer_checkpoint(_store_for_domain(scorer, target_domain), target_domain, scorer, event)
    source_store = _source_store_for_domain(scorer, source_domain)
    if source_store is not None:
        _save_transfer_checkpoint(source_store, source_domain, scorer, event)


def _store_for_domain(scorer: Any, domain: str) -> Any:
    store = getattr(scorer, "graph_store", None) or getattr(scorer, "_graph_store", None)
    return store


def _source_store_for_domain(scorer: Any, source_domain: str) -> Any | None:
    stores = getattr(scorer, "source_stores", None) or getattr(scorer, "_source_stores", None)
    if isinstance(stores, dict):
        return stores.get(source_domain)
    provider = getattr(scorer, "source_store_provider", None)
    if callable(provider):
        try:
            return provider(source_domain)
        except Exception:
            return None
    return None


def _save_transfer_checkpoint(store: Any, domain: str, scorer: Any, metadata: dict[str, Any]) -> None:
    if not isinstance(store, GraphStore):
        return
    centroids = getattr(getattr(scorer, "gae_scorer", None), "centroids", None)
    try:
        store.save_centroids(domain, "transfer_event", centroids, metadata=metadata)
    except Exception:
        return


def _demo_patterns_for_mapping(
    scorer: Any,
    source_domain: str,
    mapping: dict[str, str],
) -> list[TransferPattern]:
    preset = getattr(scorer, "_preset", None)
    shape = getattr(preset, "shape", None)
    actions = list(getattr(shape, "action_names", []) or ["transfer"])
    factors = list(getattr(shape, "factor_names", []) or [])
    factor_count = max(len(factors), 1)
    action = str(actions[0])
    patterns: list[TransferPattern] = []
    for index, source_category in enumerate(sorted(mapping)):
        target_category = mapping[source_category]
        patterns.append(
            TransferPattern(
                pattern_id=f"{source_domain}-transfer-{index}",
                source_copilot=source_domain,
                pattern_type="centroid_delta",
                category=target_category,
                action=action,
                win_rate=0.75,
                centroid_delta=[0.03 for _ in range(factor_count)],
                confidence=0.8,
                metadata={
                    "source_category": source_category,
                    "source_domain": source_domain,
                    "source_fingerprint_id": f"demo-{source_domain}",
                    "factor_mapping": {"semantic_category": target_category},
                },
            )
        )
    return patterns
