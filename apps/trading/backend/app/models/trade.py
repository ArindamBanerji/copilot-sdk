"""Normalized trade model used by Trading data connectors."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class NormalizedTrade:
    trade_id: str
    broker: str
    ticker: str
    direction: str
    entry_price: float
    exit_price: Optional[float] = None
    size: float = 0.0
    entry_time: datetime = field(default_factory=datetime.now)
    exit_time: Optional[datetime] = None
    strategy_tag: Optional[str] = None
    asset_type: str = "equity"
    trader_id: str = "default"
    fees: float = 0.0
    pnl: Optional[float] = None
    notes: Optional[str] = None
    stop_loss: Optional[float] = None
    expected_entry_price: Optional[float] = None
    expected_exit_price: Optional[float] = None
    fill_rate: float = 1.0
    r_multiple: Optional[float] = None
    execution_quality: Optional[float] = None
    verification_score: Optional[float] = None

    def __post_init__(self) -> None:
        self.trade_id = str(self.trade_id)
        self.broker = str(self.broker)
        self.ticker = str(self.ticker).upper()
        self.direction = str(self.direction).lower()
        self.entry_price = float(self.entry_price)
        self.exit_price = float(self.exit_price) if self.exit_price is not None else None
        self.size = float(self.size)
        self.trader_id = _normalize_trader_id(self.trader_id)
        self.fees = float(self.fees)
        self.pnl = float(self.pnl) if self.pnl is not None else None
        self.stop_loss = float(self.stop_loss) if self.stop_loss is not None else None
        self.expected_entry_price = (
            float(self.expected_entry_price)
            if self.expected_entry_price is not None
            else None
        )
        self.expected_exit_price = (
            float(self.expected_exit_price)
            if self.expected_exit_price is not None
            else None
        )
        self.fill_rate = float(self.fill_rate)
        self.r_multiple = float(self.r_multiple) if self.r_multiple is not None else None
        self.execution_quality = (
            float(self.execution_quality)
            if self.execution_quality is not None
            else None
        )
        self.verification_score = (
            float(self.verification_score)
            if self.verification_score is not None
            else None
        )

    @property
    def is_closed(self) -> bool:
        return self.exit_price is not None or self.exit_time is not None

    @property
    def hold_minutes(self) -> Optional[float]:
        if self.exit_time is None:
            return None
        return (self.exit_time - self.entry_time).total_seconds() / 60.0

    @property
    def computed_pnl(self) -> Optional[float]:
        if self.exit_price is None:
            return None
        if self.direction == "short":
            return (self.entry_price - self.exit_price) * self.size - self.fees
        return (self.exit_price - self.entry_price) * self.size - self.fees

    def to_dict(self) -> dict:
        return {
            "trade_id": self.trade_id,
            "broker": self.broker,
            "ticker": self.ticker,
            "direction": self.direction,
            "entry_price": self.entry_price,
            "exit_price": self.exit_price,
            "size": self.size,
            "entry_time": self.entry_time.isoformat(),
            "exit_time": self.exit_time.isoformat() if self.exit_time else None,
            "strategy_tag": self.strategy_tag,
            "asset_type": self.asset_type,
            "trader_id": self.trader_id,
            "fees": self.fees,
            "pnl": self.pnl if self.pnl is not None else self.computed_pnl,
            "notes": self.notes,
            "stop_loss": self.stop_loss,
            "expected_entry_price": self.expected_entry_price,
            "expected_exit_price": self.expected_exit_price,
            "fill_rate": self.fill_rate,
            "r_multiple": self.r_multiple,
            "execution_quality": self.execution_quality,
            "verification_score": self.verification_score,
            "is_closed": self.is_closed,
            "hold_minutes": self.hold_minutes,
        }


def _normalize_trader_id(value: object) -> str:
    text = str(value or "").strip()
    return text or "default"
