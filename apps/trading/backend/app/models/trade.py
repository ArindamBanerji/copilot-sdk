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
    fees: float = 0.0
    pnl: Optional[float] = None
    notes: Optional[str] = None

    def __post_init__(self) -> None:
        self.trade_id = str(self.trade_id)
        self.broker = str(self.broker)
        self.ticker = str(self.ticker).upper()
        self.direction = str(self.direction).lower()
        self.entry_price = float(self.entry_price)
        self.exit_price = float(self.exit_price) if self.exit_price is not None else None
        self.size = float(self.size)
        self.fees = float(self.fees)
        self.pnl = float(self.pnl) if self.pnl is not None else None

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
            "fees": self.fees,
            "pnl": self.pnl if self.pnl is not None else self.computed_pnl,
            "notes": self.notes,
            "is_closed": self.is_closed,
            "hold_minutes": self.hold_minutes,
        }
