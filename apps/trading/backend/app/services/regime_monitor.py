"""Trading regime transition monitor."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional


@dataclass(frozen=True)
class RegimeStatus:
    current_regime: str | None
    previous_regime: str | None
    regime_break_active: bool
    decisions_in_new_regime: int
    decisions_to_stabilize: int


class RegimeMonitor:
    def __init__(
        self,
        window: int = 10,
        stabilize_after: int = 20,
        tightening_multiplier: float = 1.3,
        config: Any | None = None,
    ) -> None:
        if config is not None:
            window = int(getattr(config, "regime_break_window", window))
            stabilize_after = int(getattr(config, "regime_stabilize_after", stabilize_after))
            tightening_multiplier = float(
                getattr(config, "regime_tightening_multiplier", tightening_multiplier)
            )
        self._window = max(1, int(window))
        self._stabilize_after = max(1, int(stabilize_after))
        self._tightening_multiplier = max(float(tightening_multiplier), 1.0)
        self._history: list[str] = []
        self._previous_regime: str | None = None
        self._new_regime: str | None = None
        self._decisions_in_new_regime = 0
        self._regime_break_active = False

    def record(self, regime: str) -> Optional[str]:
        observed = str(regime or "").strip().lower()
        if not observed:
            return None

        old_regime = self.current_regime
        self._history.append(observed)
        event: str | None = None

        if self._regime_break_active:
            if observed == self._new_regime:
                self._decisions_in_new_regime += 1
                if self._decisions_in_new_regime >= self._stabilize_after:
                    self._regime_break_active = False
            else:
                self._previous_regime = self._new_regime
                self._new_regime = observed
                self._decisions_in_new_regime = 1
                self._regime_break_active = True
                event = "regime_break"
            return event

        if old_regime is not None and len(self._history) >= self._window:
            prev = self._history[-self._window - 1] if len(self._history) > self._window else self._history[-2]
            if observed != prev:
                self._previous_regime = prev
                self._new_regime = observed
                self._decisions_in_new_regime = 1
                self._regime_break_active = True
                event = "regime_break"
        return event

    @property
    def current_regime(self) -> Optional[str]:
        return self._history[-1] if self._history else None

    @property
    def previous_regime(self) -> Optional[str]:
        return self._previous_regime

    @property
    def is_regime_break(self) -> bool:
        return self._regime_break_active

    @property
    def decisions_in_new_regime(self) -> int:
        return self._decisions_in_new_regime if self._regime_break_active else 0

    @property
    def decisions_to_stabilize(self) -> int:
        return self._stabilize_after

    @property
    def tightening_multiplier(self) -> float:
        return self._tightening_multiplier

    @property
    def tightening_percent(self) -> int:
        return int(round((self._tightening_multiplier - 1.0) * 100))

    def status(self) -> RegimeStatus:
        return RegimeStatus(
            current_regime=self.current_regime,
            previous_regime=self.previous_regime,
            regime_break_active=self.is_regime_break,
            decisions_in_new_regime=self.decisions_in_new_regime,
            decisions_to_stabilize=self.decisions_to_stabilize,
        )
