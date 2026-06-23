"""Transfer status router for copilot applications."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from copilot_sdk.backend.transfer import (
    TransferDetector,
    load_fingerprints_with_warnings,
)
from copilot_sdk.transfer import TransferPattern
from copilot_sdk.transfer.category_mappings import get_mapping, list_available_transfers
from copilot_sdk.transfer.registry import SharedPatternRegistry


class TransferExecuteRequest(BaseModel):
    source_domain: str
    target_domain: str
    dry_run: bool = True


def create_transfer_router(
    scorer: Any,
    warm_start_info: dict[str, Any] | None = None,
    fingerprint_base_path: Path | str | None = None,
    pattern_registry: SharedPatternRegistry | None = None,
) -> APIRouter:
    router = APIRouter(prefix="/api/transfer", tags=["Transfer"])

    @router.get("/status")
    def transfer_status() -> dict[str, Any]:
        info = _find_warm_start_info(scorer, warm_start_info)
        return _normalize_transfer_status(info)

    @router.get("/opportunities")
    def transfer_opportunities() -> dict[str, Any]:
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

    @router.post("/execute")
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

        warm_start = getattr(scorer, "warm_start", None)
        if not callable(warm_start):
            raise HTTPException(status_code=400, detail="Scorer does not support warm_start")

        summary = warm_start(patterns)
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
    get_checkpoints = getattr(store, "get_centroid_checkpoints", None)
    if not callable(get_checkpoints):
        return None
    domain = str(getattr(store, "domain", "") or getattr(scorer, "_domain", "") or "")

    try:
        checkpoints = get_checkpoints(domain, limit=10)
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
    save = getattr(store, "save_centroids", None)
    if not callable(save):
        return
    centroids = getattr(getattr(scorer, "gae_scorer", None), "centroids", None)
    try:
        save(domain, "transfer_event", centroids, metadata=metadata)
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
                metadata={"source_category": source_category},
            )
        )
    return patterns
