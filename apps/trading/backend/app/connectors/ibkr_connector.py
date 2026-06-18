"""Optional Interactive Brokers connector using ib_insync."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from app.models.trade import NormalizedTrade

try:
    from ib_insync import IB

    IB_AVAILABLE = True
except ImportError:
    IB = None  # type: ignore[assignment]
    IB_AVAILABLE = False


class IBKRConnector:
    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 7497,
        client_id: int = 10,
    ):
        if not IB_AVAILABLE:
            raise RuntimeError("ib_insync not installed. Run: pip install ib_insync")
        self.host = host
        self.port = int(port)
        self.client_id = int(client_id)
        self._ib = IB()

    @staticmethod
    def is_available() -> bool:
        return IB_AVAILABLE

    def connect(self) -> bool:
        try:
            if self._ib.isConnected():
                return True
            self._ib.connect(self.host, self.port, clientId=self.client_id)
            return bool(self._ib.isConnected())
        except Exception:
            return False

    def disconnect(self) -> None:
        try:
            if self._ib.isConnected():
                self._ib.disconnect()
        except Exception:
            pass

    def test_connection(self) -> dict[str, Any]:
        connected = self.connect()
        if not connected:
            return {"connected": False, "error": "Unable to connect to IBKR Gateway or TWS"}
        try:
            accounts = list(self._ib.managedAccounts() or [])
            return {"connected": True, "accounts": accounts}
        except Exception as exc:
            return {"connected": False, "error": str(exc)}
        finally:
            self.disconnect()

    def import_trades(self, days: int = 365) -> list[NormalizedTrade]:
        if not self.connect():
            raise ConnectionError("Failed to connect to IBKR TWS/Gateway")
        try:
            since = datetime.now(timezone.utc) - timedelta(days=int(days))
            fills = list(self._ib.fills() or [])
            trades: list[NormalizedTrade] = []
            for index, fill in enumerate(fills):
                trade, executed_at = self._fill_to_trade(fill, index)
                if trade is None or executed_at is None:
                    print("Warning: skipped IBKR fill with invalid execution time.")
                    continue
                if executed_at >= since:
                    trades.append(trade)
            if not trades:
                print("Warning: no IBKR fills found.")
            return trades
        finally:
            self.disconnect()

    def fetch_historical(
        self,
        ticker: str,
        duration: str = "1 Y",
        bar_size: str = "1 day",
    ) -> list[dict]:
        """Fetch historical OHLCV bars from IBKR."""
        if not self.connect():
            return []
        try:
            contract = _stock_contract(ticker)
            bars = self._ib.reqHistoricalData(
                contract,
                endDateTime="",
                durationStr=duration,
                barSizeSetting=bar_size,
                whatToShow="TRADES",
                useRTH=True,
                formatDate=1,
            )
            return [_bar_to_ohlcv(bar) for bar in list(bars or [])]
        except Exception:
            return []
        finally:
            self.disconnect()

    @staticmethod
    def mock_historical(ticker: str, days: int = 60) -> list[dict]:
        """Deterministic OHLCV fixture data for tests and demos."""
        base = 100.0 + (sum(ord(ch) for ch in str(ticker).upper()) % 50)
        start = datetime(2026, 1, 1)
        rows: list[dict] = []
        for i in range(days):
            close = base + i * 0.25
            rows.append(
                {
                    "date": (start + timedelta(days=i)).strftime("%Y-%m-%d"),
                    "open": round(close - 0.5, 2),
                    "high": round(close + 1.0, 2),
                    "low": round(close - 1.0, 2),
                    "close": round(close, 2),
                    "volume": 1_000_000 + i * 1_000,
                }
            )
        return rows

    @staticmethod
    def _fill_to_trade(fill: Any, index: int) -> tuple[NormalizedTrade | None, datetime | None]:
        execution = _get(fill, "execution")
        contract = _get(fill, "contract")
        report = _get(fill, "commissionReport")
        exec_id = _get(execution, "execId") or f"{index + 1}"
        symbol = _get(contract, "symbol") or _get(execution, "symbol")
        price = _get(execution, "price")
        shares = _get(execution, "shares") or _get(execution, "qty")
        if not symbol or price in {None, ""}:
            return None, None
        side = str(_get(execution, "side") or "").upper()
        executed_at = _parse_execution_time(_get(execution, "time"))
        if executed_at is None:
            return None, None
        commission = _parse_float(_get(report, "commission"), 0.0)
        pnl = _parse_float(_get(report, "realizedPNL"), None)
        trade = NormalizedTrade(
            trade_id=f"ibkr-{exec_id}",
            broker="ibkr",
            ticker=str(symbol).upper(),
            direction="long" if side == "BOT" else "short",
            entry_price=float(price),
            size=_parse_float(shares, 0.0) or 0.0,
            entry_time=executed_at.replace(tzinfo=None),
            asset_type=_asset_type(_get(contract, "secType")),
            fees=commission or 0.0,
            pnl=pnl,
        )
        for name, value in _contract_metadata(contract).items():
            setattr(trade, name, value)
        return (trade, executed_at)


def _get(source: Any, name: str) -> Any:
    if source is None:
        return None
    if isinstance(source, dict):
        return source.get(name)
    return getattr(source, name, None)


def _asset_type(sec_type: Any) -> str:
    normalized = str(sec_type or "equity").strip().lower()
    if normalized in {"opt", "option"}:
        return "option"
    if normalized in {"fut", "future"}:
        return "future"
    if normalized in {"stk", "stock"}:
        return "equity"
    return normalized or "equity"


def _contract_metadata(contract: Any) -> dict[str, Any]:
    asset_type = _asset_type(_get(contract, "secType"))
    metadata: dict[str, Any] = {}
    if asset_type == "option":
        strike = _parse_float(_get(contract, "strike"), None)
        expiry = _optional_str(_get(contract, "lastTradeDateOrContractMonth"))
        option_type = _option_type(_get(contract, "right"))
        if strike is not None:
            metadata["strike"] = strike
        if expiry:
            metadata["expiry"] = expiry
        if option_type:
            metadata["option_type"] = option_type
    elif asset_type == "future":
        expiry = _optional_str(_get(contract, "lastTradeDateOrContractMonth"))
        multiplier = _parse_float(_get(contract, "multiplier"), None)
        if expiry:
            metadata["expiry"] = expiry
        if multiplier is not None:
            metadata["multiplier"] = multiplier
    return metadata


def _option_type(value: Any) -> str | None:
    normalized = str(value or "").strip().upper()
    if normalized in {"C", "CALL"}:
        return "call"
    if normalized in {"P", "PUT"}:
        return "put"
    return None


def _stock_contract(ticker: str) -> Any:
    try:
        from ib_insync import Stock

        return Stock(str(ticker).upper(), "SMART", "USD")
    except Exception:
        return {"symbol": str(ticker).upper(), "secType": "STK", "exchange": "SMART", "currency": "USD"}


def _bar_to_ohlcv(bar: Any) -> dict:
    date_value = _get(bar, "date")
    if isinstance(date_value, datetime):
        date = date_value.strftime("%Y-%m-%d")
    else:
        date = str(date_value or "")
    return {
        "date": date,
        "open": round(float(_get(bar, "open") or 0.0), 2),
        "high": round(float(_get(bar, "high") or 0.0), 2),
        "low": round(float(_get(bar, "low") or 0.0), 2),
        "close": round(float(_get(bar, "close") or 0.0), 2),
        "volume": int(_parse_float(_get(bar, "volume"), 0.0) or 0.0),
    }


def _parse_execution_time(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        return _to_utc(value)
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = f"{text[:-1]}+00:00"
    try:
        return _to_utc(datetime.fromisoformat(text))
    except ValueError:
        pass
    try:
        return _to_utc(datetime.strptime(text, "%Y%m%d  %H:%M:%S"))
    except ValueError:
        return None


def _to_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _parse_float(value: Any, default: float | None) -> float | None:
    if value in {None, ""}:
        return default
    try:
        return float(str(value).replace("$", "").replace(",", ""))
    except (TypeError, ValueError):
        return default


def _optional_str(value: Any) -> str | None:
    text = str(value or "").strip()
    return text or None
