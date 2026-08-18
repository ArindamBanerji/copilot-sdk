"""Trading runtime settings used by safety-sensitive application boundaries."""

from __future__ import annotations

import os


_TRUE_VALUES = frozenset({"1", "true", "yes", "on"})


class TradingSettings:
    """Environment-backed settings with safe observation-only defaults."""

    @property
    def TRADING_EXECUTION_ENABLED(self) -> bool:
        """Return whether a deployment explicitly enables broker writes."""
        return os.getenv("TRADING_EXECUTION_ENABLED", "false").strip().lower() in _TRUE_VALUES


settings = TradingSettings()

