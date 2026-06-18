"""Trading journal endpoints."""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from threading import RLock
from typing import Any, Callable
from uuid import uuid4

from fastapi import APIRouter, Body, HTTPException, Query, Request
from fastapi.responses import JSONResponse

from app.routers.data_import import _trade_store_ref
from app.services.subcategory import get_subcategory


GraphStoreFactory = Callable[[], Any]
_JOURNAL_LOCK = RLock()
_MISSING = object()


def create_journal_router(
    graph_store_factory: GraphStoreFactory | None = None,
    *,
    domain: str = "trading",
) -> APIRouter:
    router = APIRouter(prefix="/api/trading", tags=["trading-journal"])

    def _records(request: Request | None = None) -> list[dict[str, Any]]:
        return _journal_records(graph_store_factory, domain, journal_dir=_journal_base_dir(request))

    @router.get("/journal/trades")
    @router.get("/trades")
    def list_trades(
        request: Request,
        ticker: str | None = None,
        category: str | None = None,
        strategy_tag: str | None = None,
        regime: str | None = None,
        outcome: str | None = Query(default=None, pattern="^(win|loss)$"),
        date_from: str | None = None,
        date_to: str | None = None,
        tag: str | None = None,
        search: str | None = None,
        limit: int = Query(default=50, ge=0),
        offset: int = Query(default=0, ge=0),
    ) -> dict[str, Any]:
        filters = _filters(
            ticker=ticker,
            category=category,
            strategy_tag=strategy_tag,
            regime=regime,
            outcome=outcome,
            date_from=date_from,
            date_to=date_to,
            tag=tag,
        )
        filtered = _apply_filters(_records(request), filters)
        if search not in {None, ""}:
            filtered = [trade for trade in filtered if _matches_search(trade, str(search))]
        paged = filtered[offset : offset + limit] if limit else []

        # Preserve the legacy empty shape for existing data endpoint callers that
        # request /api/trading/trades without journal filters.
        if not filtered and not request.url.query:
            return {"trades": [], "count": 0}

        return {
            "trades": paged,
            "count": len(paged),
            "total": len(filtered),
            "filters_applied": filters,
            "aggregate": _aggregate(filtered),
        }

    @router.get("/trades/{trade_id}", response_model=None)
    def get_trade(trade_id: str, request: Request):
        for trade in _records(request):
            if str(trade.get("trade_id")) == str(trade_id):
                return trade
        return JSONResponse(status_code=404, content={"error": "Trade not found"})

    @router.post("/journal/entry")
    def create_manual_entry(
        request: Request,
        payload: dict[str, Any] = Body(...),
    ):
        ticker = str(payload.get("ticker") or "").strip().upper()
        if not ticker:
            raise HTTPException(status_code=400, detail="ticker is required")

        entry_id = str(uuid4())
        entry = {
            "entry_id": entry_id,
            "trade_id": entry_id,
            "ticker": ticker,
            "category": payload.get("category"),
            "direction": payload.get("direction"),
            "entry_price": _number(payload.get("entry_price")),
            "exit_price": _number(payload.get("exit_price")),
            "size": _number(payload.get("position_size") if payload.get("position_size") is not None else payload.get("size")),
            "pnl": _number(payload.get("pnl")),
            "reflection": _string_or_none(payload.get("reflection") if payload.get("reflection") is not None else payload.get("notes")),
            "notes": _string_or_none(payload.get("notes") if payload.get("notes") is not None else payload.get("reflection")),
            "tags": _clean_tags(payload.get("tags")),
            "entry_time": _string_or_none(payload.get("entry_date") if payload.get("entry_date") is not None else payload.get("entry_time")),
            "exit_time": _string_or_none(payload.get("exit_date") if payload.get("exit_date") is not None else payload.get("exit_time")),
            "metadata": {
                "source": "manual_journal",
                "created_at": _now_iso(),
            },
        }
        try:
            _append_manual_entry(_journal_base_dir(request), entry)
        except OSError as exc:
            return _journal_write_error(exc)
        return JSONResponse(status_code=201, content={"entry_id": entry_id, "created": True})

    @router.put("/journal/entry/{entry_id}/reflection", response_model=None)
    def update_reflection(
        entry_id: str,
        request: Request,
        payload: dict[str, Any] = Body(...),
    ) -> dict[str, Any] | JSONResponse:
        if not _entry_exists(entry_id, _records(request)):
            raise HTTPException(status_code=404, detail="Journal entry not found")
        reflection = str(payload.get("reflection") or "")
        try:
            _update_overlay(_journal_base_dir(request), entry_id, reflection=reflection)
        except OSError as exc:
            return _journal_write_error(exc)
        return {"entry_id": entry_id, "updated": True, "reflection": reflection}

    @router.put("/journal/entry/{entry_id}/tags", response_model=None)
    def update_tags(
        entry_id: str,
        request: Request,
        payload: dict[str, Any] = Body(...),
    ) -> dict[str, Any] | JSONResponse:
        if not _entry_exists(entry_id, _records(request)):
            raise HTTPException(status_code=404, detail="Journal entry not found")
        tags = _clean_tags(payload.get("tags"))
        try:
            _update_overlay(_journal_base_dir(request), entry_id, tags=tags)
        except OSError as exc:
            return _journal_write_error(exc)
        return {"entry_id": entry_id, "updated": True, "tags": tags}

    @router.get("/analytics")
    def analytics(
        request: Request,
        ticker: str | None = None,
        category: str | None = None,
        strategy_tag: str | None = None,
        regime: str | None = None,
        outcome: str | None = Query(default=None, pattern="^(win|loss)$"),
        date_from: str | None = None,
        date_to: str | None = None,
        group_by: str = Query(default="category", pattern="^(category|ticker|strategy_tag|regime|month|subcategory)$"),
    ) -> dict[str, Any]:
        filters = _filters(
            ticker=ticker,
            category=category,
            strategy_tag=strategy_tag,
            regime=regime,
            outcome=outcome,
            date_from=date_from,
            date_to=date_to,
        )
        filtered = _apply_filters(_records(request), filters)
        if group_by == "subcategory":
            filtered = [trade for trade in filtered if trade.get("category") == "event_driven"]
        groups: dict[str, list[dict[str, Any]]] = {}
        for trade in filtered:
            key = _group_key(trade, group_by)
            groups.setdefault(key, []).append(trade)
        return {
            "group_by": group_by,
            "groups": [
                {"key": key, "count": len(rows), **_aggregate(rows)}
                for key, rows in sorted(groups.items(), key=lambda item: item[0])
            ],
            "total": len(filtered),
        }

    return router


def _journal_records(
    graph_store_factory: GraphStoreFactory | None,
    domain: str,
    *,
    journal_dir: Path | None = None,
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    seen: set[str] = set()
    base_dir = journal_dir or _journal_base_dir(None)
    overlays = _load_overlay(base_dir)

    def add_record(record: Any) -> None:
        normalized = _apply_overlay(_normalize_trade(record), overlays)
        trade_id = str(normalized.get("trade_id") or "")
        if trade_id and trade_id in seen:
            return
        if trade_id:
            seen.add(trade_id)
        records.append(normalized)

    for trade in list(_trade_store_ref):
        add_record(trade)

    for entry in _load_manual_entries(base_dir):
        add_record(entry)

    if graph_store_factory is not None:
        store = None
        try:
            store = graph_store_factory()
            for decision in store.get_all_decisions(domain):
                add_record(decision)
        except Exception:
            pass
        finally:
            close = getattr(store, "close", None)
            if callable(close):
                close()

    records.sort(key=lambda trade: _entry_date(trade) or datetime.min, reverse=True)
    return records


def _normalize_trade(record: Any) -> dict[str, Any]:
    if hasattr(record, "to_dict"):
        raw = record.to_dict()
    elif isinstance(record, dict):
        raw = dict(record)
    else:
        raw = {}

    metadata = _as_dict(raw.get("metadata"))
    factors = _as_dict(raw.get("factors"))
    if isinstance(factors.get("metadata"), dict):
        metadata = {**factors["metadata"], **metadata}
    options_factors = _options_factors(raw, metadata, factors)

    trade_id = (
        raw.get("trade_id")
        or metadata.get("trade_id")
        or raw.get("decision_id")
        or metadata.get("decision_id")
    )
    entry_id = raw.get("entry_id") or metadata.get("entry_id") or trade_id
    ticker = raw.get("ticker") or metadata.get("ticker")
    action = raw.get("action") or raw.get("recommended_action") or metadata.get("action")
    direction = raw.get("direction") or metadata.get("direction") or action
    entry_time = raw.get("entry_time") or metadata.get("entry_time") or metadata.get("date")
    exit_time = raw.get("exit_time") or metadata.get("exit_time")
    pnl = _number(raw.get("pnl"))
    if pnl is None:
        pnl = _number(metadata.get("pnl"))
    if pnl is None:
        pnl = _number(metadata.get("pnl_dollars"))
    regime = raw.get("regime") or metadata.get("regime") or raw.get("market_regime") or metadata.get("market_regime")
    reflection = (
        raw.get("reflection")
        or raw.get("notes")
        or metadata.get("reflection")
        or metadata.get("notes")
    )
    notes = raw.get("notes") or metadata.get("notes") or reflection

    normalized = {
        "entry_id": str(entry_id) if entry_id is not None else None,
        "trade_id": str(trade_id) if trade_id is not None else None,
        "ticker": str(ticker).upper() if ticker else None,
        "direction": direction,
        "entry_price": _number(raw.get("entry_price") if raw.get("entry_price") is not None else metadata.get("entry_price")),
        "exit_price": _number(raw.get("exit_price") if raw.get("exit_price") is not None else metadata.get("exit_price")),
        "size": _number(raw.get("size") if raw.get("size") is not None else metadata.get("size") or metadata.get("shares")),
        "entry_time": _string_or_none(entry_time),
        "exit_time": _string_or_none(exit_time),
        "strategy_tag": raw.get("strategy_tag") or metadata.get("strategy_tag") or metadata.get("thesis_type"),
        "category": raw.get("category") or metadata.get("category"),
        "subcategory": None,
        "regime": regime,
        "pnl": pnl,
        "factors": factors,
        "action": action,
        "confidence": _number(raw.get("confidence") if raw.get("confidence") is not None else metadata.get("confidence")),
        "reflection": _string_or_none(reflection),
        "notes": _string_or_none(notes),
        "tags": _clean_tags(raw.get("tags") if raw.get("tags") is not None else metadata.get("tags")),
        "metadata": metadata,
    }
    if options_factors:
        normalized["options_factors"] = options_factors
        normalized["options_analytics_only"] = True
    normalized["subcategory"] = get_subcategory(normalized)
    return normalized


def _filters(**kwargs: str | None) -> dict[str, str]:
    return {key: str(value) for key, value in kwargs.items() if value not in {None, ""}}


def _apply_filters(
    trades: list[dict[str, Any]],
    filters: dict[str, str],
) -> list[dict[str, Any]]:
    output = list(trades)
    if "ticker" in filters:
        ticker = filters["ticker"].upper()
        output = [trade for trade in output if str(trade.get("ticker") or "").upper() == ticker]
    if "category" in filters:
        output = [trade for trade in output if str(trade.get("category") or "") == filters["category"]]
    if "strategy_tag" in filters:
        output = [trade for trade in output if str(trade.get("strategy_tag") or "") == filters["strategy_tag"]]
    if "regime" in filters:
        output = [trade for trade in output if str(trade.get("regime") or "") == filters["regime"]]
    if "outcome" in filters:
        want_win = filters["outcome"] == "win"
        output = [
            trade for trade in output
            if trade.get("pnl") is not None and (float(trade["pnl"]) > 0) == want_win
        ]
    if "tag" in filters:
        tag = filters["tag"].lower()
        output = [
            trade for trade in output
            if any(str(value).lower() == tag for value in trade.get("tags", []))
        ]
    if "date_from" in filters:
        start = _parse_date(filters["date_from"])
        if start is not None:
            output = [trade for trade in output if _entry_date(trade) is not None and _entry_date(trade) >= start]
    if "date_to" in filters:
        end = _parse_date(filters["date_to"])
        if end is not None:
            output = [trade for trade in output if _entry_date(trade) is not None and _entry_date(trade) <= end]
    return output


def _aggregate(trades: list[dict[str, Any]]) -> dict[str, Any]:
    total = len(trades)
    pnls = [float(trade["pnl"]) for trade in trades if trade.get("pnl") is not None]
    confidences = [
        float(trade["confidence"])
        for trade in trades
        if trade.get("confidence") is not None
    ]
    wins = sum(1 for trade in trades if trade.get("pnl") is not None and float(trade["pnl"]) > 0)
    return {
        "total_trades": total,
        "win_rate": wins / total if total else 0.0,
        "avg_pnl": mean(pnls) if pnls else 0.0,
        "total_pnl": sum(pnls) if pnls else 0.0,
        "avg_confidence": mean(confidences) if confidences else 0.0,
    }


def _group_key(trade: dict[str, Any], group_by: str) -> str:
    if group_by == "month":
        parsed = _entry_date(trade)
        return parsed.strftime("%Y-%m") if parsed is not None else "unknown"
    if group_by == "subcategory":
        return get_subcategory(trade) or "other"
    value = trade.get(group_by)
    return str(value) if value not in {None, ""} else "unknown"


def _as_dict(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def _options_factors(
    raw: dict[str, Any],
    metadata: dict[str, Any],
    factors: dict[str, Any],
) -> dict[str, Any] | None:
    for source in (
        raw.get("options_factors"),
        metadata.get("options_factors"),
        factors.get("options_factors"),
    ):
        if isinstance(source, dict):
            return dict(source)
    return None


def _number(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _string_or_none(value: Any) -> str | None:
    return str(value) if value is not None else None


def _parse_date(value: str) -> datetime | None:
    text = value.strip()
    if text.endswith("Z"):
        text = f"{text[:-1]}+00:00"
    try:
        parsed = datetime.fromisoformat(text)
        if parsed.tzinfo is not None:
            parsed = parsed.astimezone(timezone.utc).replace(tzinfo=None)
        return parsed
    except ValueError:
        return None


def _entry_date(trade: dict[str, Any]) -> datetime | None:
    value = trade.get("entry_time")
    return _parse_date(str(value)) if value else None


def _journal_base_dir(request: Request | None) -> Path:
    if request is not None:
        state_dir = getattr(request.app.state, "trading_journal_dir", None)
        if state_dir:
            return Path(state_dir).expanduser()
        data_dir = getattr(request.app.state, "trading_data_dir", None)
        if data_dir:
            return Path(data_dir).expanduser()

    env_dir = os.getenv("TRADING_JOURNAL_DIR") or os.getenv("TRADING_JOURNAL_PATH")
    if env_dir:
        return Path(env_dir).expanduser()
    return Path.home() / ".ci-platform" / "trading"


def _entries_path(base_dir: Path) -> Path:
    return base_dir / "journal_entries.json"


def _overlay_path(base_dir: Path) -> Path:
    return base_dir / "journal_reflections.json"


def _load_manual_entries(base_dir: Path) -> list[dict[str, Any]]:
    payload = _read_json(_entries_path(base_dir), list)
    return [dict(item) for item in payload] if isinstance(payload, list) else []


def _load_overlay(base_dir: Path) -> dict[str, dict[str, Any]]:
    payload = _read_json(_overlay_path(base_dir), dict)
    if not isinstance(payload, dict):
        return {}
    return {
        str(key): dict(value)
        for key, value in payload.items()
        if isinstance(value, dict)
    }


def _read_json(path: Path, default_factory) -> Any:
    with _JOURNAL_LOCK:
        return _read_json_unlocked(path, default_factory)


def _write_json_atomic(path: Path, payload: Any) -> None:
    with _JOURNAL_LOCK:
        _write_json_atomic_unlocked(path, payload)


def _append_manual_entry(base_dir: Path, entry: dict[str, Any]) -> None:
    _locked_append(_entries_path(base_dir), entry, list)


def _update_overlay(
    base_dir: Path,
    entry_id: str,
    *,
    reflection: Any = _MISSING,
    tags: Any = _MISSING,
) -> None:
    def update_value(current: dict[str, Any]) -> dict[str, Any]:
        history = current.get("history")
        history_rows = list(history) if isinstance(history, list) else []
        update: dict[str, Any] = {"updated_at": _now_iso()}

        if reflection is not _MISSING:
            current["reflection"] = str(reflection)
            current["notes"] = str(reflection)
            update["reflection"] = str(reflection)
        if tags is not _MISSING:
            current["tags"] = _clean_tags(tags)
            update["tags"] = current["tags"]

        history_rows.append(update)
        current["history"] = history_rows
        current["updated_at"] = update["updated_at"]
        return current

    _locked_update(_overlay_path(base_dir), str(entry_id), update_value, dict)


def _apply_overlay(trade: dict[str, Any], overlays: dict[str, dict[str, Any]]) -> dict[str, Any]:
    entry_id = str(trade.get("trade_id") or trade.get("entry_id") or "")
    overlay = overlays.get(entry_id)
    if not overlay:
        return trade
    merged = dict(trade)
    if "reflection" in overlay:
        merged["reflection"] = _string_or_none(overlay.get("reflection"))
        merged["notes"] = _string_or_none(overlay.get("notes") or overlay.get("reflection"))
    if "tags" in overlay:
        merged["tags"] = _clean_tags(overlay.get("tags"))
    return merged


def _entry_exists(entry_id: str, records: list[dict[str, Any]]) -> bool:
    return any(str(record.get("trade_id") or record.get("entry_id")) == str(entry_id) for record in records)


def _clean_tags(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    tags: list[str] = []
    seen: set[str] = set()
    for item in value:
        text = str(item).strip()
        if not text or text in seen:
            continue
        seen.add(text)
        tags.append(text)
    return tags


def _matches_search(entry: dict[str, Any], query: str) -> bool:
    q = query.lower()
    searchable = " ".join(
        str(value)
        for value in (
            entry.get("ticker"),
            entry.get("category"),
            entry.get("strategy_tag"),
            entry.get("reflection"),
            entry.get("notes"),
            " ".join(entry.get("tags", []) or []),
        )
        if value
    ).lower()
    return q in searchable


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _read_json_unlocked(path: Path, default_factory) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return default_factory()
    except json.JSONDecodeError:
        corrupt_path = _corrupt_path(path)
        try:
            path.rename(corrupt_path)
        except OSError:
            corrupt_path = path
        logging.warning("Corrupt journal file %s renamed to %s", path, corrupt_path)
        return default_factory()
    except OSError:
        return default_factory()


def _write_json_atomic_unlocked(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_name(f".{path.name}.{uuid4().hex}.tmp")
    temp_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    temp_path.replace(path)


def _locked_append(path: Path, entry: dict[str, Any], default_factory=list) -> None:
    with _JOURNAL_LOCK:
        data = _read_json_unlocked(path, default_factory)
        if not isinstance(data, list):
            data = default_factory()
        data.append(entry)
        _write_json_atomic_unlocked(path, data)


def _locked_update(path: Path, key: str, value_factory, default_factory=dict) -> None:
    with _JOURNAL_LOCK:
        data = _read_json_unlocked(path, default_factory)
        if not isinstance(data, dict):
            data = default_factory()
        current = dict(data.get(str(key), {})) if isinstance(data.get(str(key)), dict) else {}
        data[str(key)] = value_factory(current)
        _write_json_atomic_unlocked(path, data)


def _corrupt_path(path: Path) -> Path:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S%f")
    return path.with_name(f"{path.name}.corrupt.{stamp}")


def _journal_write_error(exc: OSError) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content={"error": "Failed to write journal", "detail": str(exc)},
    )
