"""Transfer status router for copilot applications."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter


def create_transfer_router(
    scorer: Any,
    warm_start_info: dict[str, Any] | None = None,
) -> APIRouter:
    router = APIRouter(prefix="/api/transfer", tags=["Transfer"])

    @router.get("/status")
    def transfer_status() -> dict[str, Any]:
        info = _find_warm_start_info(scorer, warm_start_info)
        return _normalize_transfer_status(info)

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
    if patterns_transferred <= 0:
        return {"warm_started": False}

    return {
        "warm_started": True,
        "source_copilot": _source_copilot(info),
        "patterns_transferred": patterns_transferred,
        "transferred_at": _string_or_none(info.get("transferred_at") or info.get("timestamp")),
    }


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


def _string_or_none(value: Any) -> str | None:
    if value is None:
        return None
    return str(value)
