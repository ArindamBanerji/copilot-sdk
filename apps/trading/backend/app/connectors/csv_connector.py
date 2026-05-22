"""CSV import connector for normalized Trading trades."""

from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path
from typing import Iterable

from app.models.trade import NormalizedTrade


class CSVConnector:
    _ALIASES = {
        "trade_id": ("trade_id", "id", "order_id"),
        "ticker": ("ticker", "symbol", "asset", "instrument"),
        "direction": ("direction", "side", "action"),
        "entry_price": ("entry_price", "price", "fill_price", "avg_price"),
        "exit_price": ("exit_price", "close_price"),
        "size": ("size", "qty", "quantity", "shares"),
        "entry_time": ("entry_time", "filled_at", "date", "time", "timestamp"),
        "exit_time": ("exit_time", "closed_at"),
        "strategy_tag": ("strategy_tag", "strategy", "tag"),
        "asset_type": ("asset_type", "asset_class"),
        "fees": ("fees", "commission", "fee"),
        "pnl": ("pnl", "profit_loss", "realized_pnl"),
        "notes": ("notes", "note", "comment"),
    }

    def import_from_file(self, filepath: str) -> list[NormalizedTrade]:
        return self.import_from_string(Path(filepath).read_text(encoding="utf-8-sig"))

    def import_from_string(self, csv_content: str) -> list[NormalizedTrade]:
        if not csv_content.strip():
            return []
        reader = csv.DictReader(csv_content.splitlines())
        if not reader.fieldnames:
            return []

        normalized_headers = {
            header: header.strip().lower().replace(" ", "_")
            for header in reader.fieldnames
            if header is not None
        }
        trades: list[NormalizedTrade] = []
        for row in reader:
            try:
                ticker = str(self._value(row, normalized_headers, "ticker") or "").strip()
                if not ticker:
                    continue
                direction = _normalize_direction(self._value(row, normalized_headers, "direction"))
                entry_price = _parse_float(self._value(row, normalized_headers, "entry_price"))
                trade = NormalizedTrade(
                    trade_id=str(
                        self._value(row, normalized_headers, "trade_id")
                        or f"csv-{len(trades) + 1}"
                    ),
                    broker="csv",
                    ticker=ticker,
                    direction=direction,
                    entry_price=entry_price,
                    exit_price=_parse_optional_float(self._value(row, normalized_headers, "exit_price")),
                    size=_parse_optional_float(self._value(row, normalized_headers, "size")) or 0.0,
                    entry_time=_parse_datetime(self._value(row, normalized_headers, "entry_time")),
                    exit_time=_parse_optional_datetime(self._value(row, normalized_headers, "exit_time")),
                    strategy_tag=_optional_str(self._value(row, normalized_headers, "strategy_tag")),
                    asset_type=_optional_str(self._value(row, normalized_headers, "asset_type")) or "equity",
                    fees=_parse_optional_float(self._value(row, normalized_headers, "fees")) or 0.0,
                    pnl=_parse_optional_float(self._value(row, normalized_headers, "pnl")),
                    notes=_optional_str(self._value(row, normalized_headers, "notes")),
                )
                trades.append(trade)
            except (TypeError, ValueError):
                continue
        return trades

    def _value(
        self,
        row: dict[str, str],
        normalized_headers: dict[str, str],
        field: str,
    ) -> str | None:
        aliases = set(self._ALIASES[field])
        for original, normalized in normalized_headers.items():
            if normalized in aliases:
                return row.get(original)
        return None


def _normalize_direction(value: object) -> str:
    normalized = str(value or "long").strip().lower()
    if normalized in {"sell", "short", "sold"}:
        return "short"
    return "long"


def _parse_float(value: object) -> float:
    parsed = _parse_optional_float(value)
    if parsed is None:
        raise ValueError("missing numeric value")
    return parsed


def _parse_optional_float(value: object) -> float | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    return float(text.replace("$", "").replace(",", ""))


def _parse_datetime(value: object) -> datetime:
    parsed = _parse_optional_datetime(value)
    return parsed or datetime.now()


def _parse_optional_datetime(value: object) -> datetime | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = f"{text[:-1]}+00:00"
    for parser in (_from_iso, *_strptime_parsers()):
        parsed = parser(text)
        if parsed is not None:
            return parsed
    raise ValueError(f"unsupported datetime: {value}")


def _from_iso(value: str) -> datetime | None:
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def _strptime_parsers() -> Iterable:
    formats = (
        "%Y-%m-%d",
        "%m/%d/%Y",
        "%m/%d/%y",
        "%Y-%m-%d %H:%M:%S",
        "%m/%d/%Y %H:%M",
        "%Y/%m/%d",
    )
    for date_format in formats:
        yield lambda value, fmt=date_format: _strptime(value, fmt)


def _strptime(value: str, date_format: str) -> datetime | None:
    try:
        return datetime.strptime(value, date_format)
    except ValueError:
        return None


def _optional_str(value: object) -> str | None:
    text = str(value).strip() if value is not None else ""
    return text or None
