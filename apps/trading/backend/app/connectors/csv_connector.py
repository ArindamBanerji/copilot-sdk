"""CSV import connector for normalized Trading trades."""

from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path
from typing import Iterable

from app.models.trade import NormalizedTrade


BROKER_PRESETS = {
    "thinkorswim": {
        "trade_id": "Exec ID",
        "ticker": "Symbol",
        "direction": "Side",
        "entry_price": "Price",
        "size": "Qty",
        "entry_time": "Exec Time",
        "fees": "Commission",
        "pnl": "P/L",
        "notes": "Description",
    },
    "webull": {
        "trade_id": "Order ID",
        "ticker": "Symbol",
        "direction": "Side",
        "entry_price": "Filled Price",
        "size": "Filled",
        "entry_time": "Filled Time",
        "fees": "Fees",
        "pnl": "Realized P&L",
        "notes": "Notes",
    },
    "robinhood": {
        "trade_id": "Activity ID",
        "ticker": "Instrument",
        "direction": "Trans Code",
        "entry_price": "Price",
        "size": "Quantity",
        "entry_time": "Activity Date",
        "fees": "Fees",
        "pnl": "Amount",
        "notes": "Description",
    },
    "alpaca": {
        "trade_id": "id",
        "ticker": "symbol",
        "direction": "side",
        "entry_price": "avg_entry_price",
        "exit_price": "avg_exit_price",
        "size": "qty",
        "entry_time": "filled_at",
        "fees": "commission",
    },
}


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
        "trader_id": ("trader_id", "trader", "user_id", "account", "account_id"),
        "fees": ("fees", "commission", "fee"),
        "pnl": ("pnl", "profit_loss", "realized_pnl"),
        "notes": ("notes", "note", "comment"),
    }

    def import_from_file(self, filepath: str) -> list[NormalizedTrade]:
        return self.import_from_string(Path(filepath).read_text(encoding="utf-8-sig"))

    def import_flexible(
        self,
        filepath: str,
        column_map: dict[str, str] | None = None,
        broker_preset: str | None = None,
        date_format: str | None = None,
        delimiter: str | None = None,
    ) -> list[NormalizedTrade]:
        content = Path(filepath).read_text(encoding="utf-8-sig")
        if not content.strip():
            return []
        reader = csv.DictReader(content.splitlines(), delimiter=delimiter or self._detect_delimiter(content.splitlines()[0]))
        if not reader.fieldnames:
            return []
        mapping = self._auto_detect_columns(reader.fieldnames)
        if broker_preset:
            mapping.update(BROKER_PRESETS.get(broker_preset.lower(), {}))
        if column_map:
            mapping.update(column_map)
        trades: list[NormalizedTrade] = []
        for index, row in enumerate(reader, start=1):
            trade = self._row_to_trade(row, mapping, index, date_format=date_format)
            if trade is not None:
                trades.append(trade)
        return trades

    def import_from_string(
        self,
        csv_content: str,
        *,
        column_map: dict[str, str] | None = None,
        broker_preset: str | None = None,
        date_format: str | None = None,
        delimiter: str | None = None,
    ) -> list[NormalizedTrade]:
        if not csv_content.strip():
            return []
        reader = csv.DictReader(
            csv_content.splitlines(),
            delimiter=delimiter or self._detect_delimiter(csv_content.splitlines()[0]),
        )
        if not reader.fieldnames:
            return []

        mapping = self._auto_detect_columns(reader.fieldnames)
        if broker_preset:
            mapping.update(BROKER_PRESETS.get(broker_preset.lower(), {}))
        if column_map:
            mapping.update(column_map)
        trades: list[NormalizedTrade] = []
        for index, row in enumerate(reader, start=1):
            trade = self._row_to_trade(row, mapping, len(trades) + 1, date_format=date_format)
            if trade is not None:
                trades.append(trade)
        return trades

    def _detect_delimiter(self, first_line: str) -> str:
        """Detect common CSV delimiters from the header line."""
        counts = {delimiter: first_line.count(delimiter) for delimiter in (",", "\t", "|", ";")}
        delimiter, count = max(counts.items(), key=lambda item: item[1])
        return delimiter if count > 0 else ","

    def _auto_detect_columns(self, headers: Iterable[str]) -> dict[str, str]:
        normalized_headers = {
            header: header.strip().lower().replace(" ", "_")
            for header in headers
            if header is not None
        }
        mapping: dict[str, str] = {}
        for field, aliases in self._ALIASES.items():
            alias_set = set(aliases)
            for original, normalized in normalized_headers.items():
                if normalized in alias_set:
                    mapping[field] = original
                    break
        return mapping

    def _row_to_trade(
        self,
        row: dict[str, str],
        mapping: dict[str, str],
        index: int,
        *,
        date_format: str | None = None,
    ) -> NormalizedTrade | None:
        try:
            ticker = str(_mapped(row, mapping, "ticker") or "").strip()
            if not ticker:
                return None
            return NormalizedTrade(
                trade_id=str(_mapped(row, mapping, "trade_id") or f"csv-{index}"),
                broker="csv",
                ticker=ticker,
                direction=_normalize_direction(_mapped(row, mapping, "direction")),
                entry_price=_parse_float(_mapped(row, mapping, "entry_price")),
                exit_price=_parse_optional_float(_mapped(row, mapping, "exit_price")),
                size=_parse_optional_float(_mapped(row, mapping, "size")) or 0.0,
                entry_time=self._parse_date(_mapped(row, mapping, "entry_time"), date_format=date_format),
                exit_time=_parse_optional_datetime(_mapped(row, mapping, "exit_time"), date_format=date_format),
                strategy_tag=_optional_str(_mapped(row, mapping, "strategy_tag")),
                asset_type=_optional_str(_mapped(row, mapping, "asset_type")) or "equity",
                trader_id=_trader_id(_mapped(row, mapping, "trader_id")),
                fees=_parse_optional_float(_mapped(row, mapping, "fees")) or 0.0,
                pnl=_parse_optional_float(_mapped(row, mapping, "pnl")),
                notes=_optional_str(_mapped(row, mapping, "notes")),
            )
        except (TypeError, ValueError):
            return None

    def _parse_date(self, date_str: object, *, date_format: str | None = None) -> datetime:
        return _parse_datetime(date_str, date_format=date_format)

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
    if normalized in {"sell", "sld", "short", "sold", "s"}:
        return "short"
    if normalized in {"buy", "bot", "long", "b"}:
        return "long"
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


def _parse_datetime(value: object, *, date_format: str | None = None) -> datetime:
    parsed = _parse_optional_datetime(value, date_format=date_format)
    return parsed or datetime.now()


def _parse_optional_datetime(value: object, *, date_format: str | None = None) -> datetime | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = f"{text[:-1]}+00:00"
    for parser in (_from_iso, *_strptime_parsers(date_format=date_format)):
        parsed = parser(text)
        if parsed is not None:
            return parsed
    raise ValueError(f"unsupported datetime: {value}")


def _from_iso(value: str) -> datetime | None:
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def _strptime_parsers(date_format: str | None = None) -> Iterable:
    us_formats = (
        "%Y-%m-%d",
        "%m/%d/%Y",
        "%m/%d/%y",
        "%Y-%m-%d %H:%M:%S",
        "%m/%d/%Y %H:%M",
        "%Y/%m/%d",
    )
    european_formats = (
        "%d-%m-%Y",
        "%d/%m/%Y",
        "%d.%m.%Y",
    )
    formats = european_formats + us_formats if date_format == "european" else us_formats + european_formats
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


def _trader_id(value: object) -> str:
    return _optional_str(value) or "default"


def _mapped(row: dict[str, str], mapping: dict[str, str], field: str) -> str | None:
    column = mapping.get(field)
    return row.get(column) if column else None
