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
            return []
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
        return (
            NormalizedTrade(
                trade_id=f"ibkr-{exec_id}",
                broker="ibkr",
                ticker=str(symbol).upper(),
                direction="long" if side == "BOT" else "short",
                entry_price=float(price),
                size=_parse_float(shares, 0.0) or 0.0,
                entry_time=executed_at.replace(tzinfo=None),
                asset_type=str(_get(contract, "secType") or "equity").lower(),
                fees=commission or 0.0,
                pnl=pnl,
            ),
            executed_at,
        )


def _get(source: Any, name: str) -> Any:
    if source is None:
        return None
    if isinstance(source, dict):
        return source.get(name)
    return getattr(source, name, None)


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
