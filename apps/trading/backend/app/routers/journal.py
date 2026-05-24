"""Read-only Trading journal endpoints."""

from __future__ import annotations

from datetime import datetime
from statistics import mean
from typing import Any, Callable

from fastapi import APIRouter, Query, Request
from fastapi.responses import JSONResponse

from app.routers.data_import import _trade_store_ref


GraphStoreFactory = Callable[[], Any]


def create_journal_router(
    graph_store_factory: GraphStoreFactory | None = None,
    *,
    domain: str = "trading",
) -> APIRouter:
    router = APIRouter(prefix="/api/trading", tags=["trading-journal"])

    def _records() -> list[dict[str, Any]]:
        return _journal_records(graph_store_factory, domain)

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
        )
        filtered = _apply_filters(_records(), filters)
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
    def get_trade(trade_id: str):
        for trade in _records():
            if str(trade.get("trade_id")) == str(trade_id):
                return trade
        return JSONResponse(status_code=404, content={"error": "Trade not found"})

    @router.get("/analytics")
    def analytics(
        ticker: str | None = None,
        category: str | None = None,
        strategy_tag: str | None = None,
        regime: str | None = None,
        outcome: str | None = Query(default=None, pattern="^(win|loss)$"),
        date_from: str | None = None,
        date_to: str | None = None,
        group_by: str = Query(default="category", pattern="^(category|ticker|strategy_tag|regime|month)$"),
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
        filtered = _apply_filters(_records(), filters)
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
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    seen: set[str] = set()

    for trade in list(_trade_store_ref):
        normalized = _normalize_trade(trade)
        trade_id = str(normalized.get("trade_id") or "")
        if trade_id:
            seen.add(trade_id)
        records.append(normalized)

    if graph_store_factory is not None:
        store = None
        try:
            store = graph_store_factory()
            for decision in store.get_all_decisions(domain):
                normalized = _normalize_trade(decision)
                trade_id = str(normalized.get("trade_id") or "")
                if trade_id and trade_id in seen:
                    continue
                if trade_id:
                    seen.add(trade_id)
                records.append(normalized)
        except Exception:
            pass
        finally:
            close = getattr(store, "close", None)
            if callable(close):
                close()

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

    trade_id = (
        raw.get("trade_id")
        or metadata.get("trade_id")
        or raw.get("decision_id")
        or metadata.get("decision_id")
    )
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

    return {
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
        "regime": regime,
        "pnl": pnl,
        "factors": factors,
        "action": action,
        "confidence": _number(raw.get("confidence") if raw.get("confidence") is not None else metadata.get("confidence")),
        "metadata": metadata,
    }


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
    value = trade.get(group_by)
    return str(value) if value not in {None, ""} else "unknown"


def _as_dict(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


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
        return datetime.fromisoformat(text)
    except ValueError:
        return None


def _entry_date(trade: dict[str, Any]) -> datetime | None:
    value = trade.get("entry_time")
    return _parse_date(str(value)) if value else None
