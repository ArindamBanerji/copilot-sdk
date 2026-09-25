"""Trading runtime settings used by safety-sensitive application boundaries."""

from __future__ import annotations

class TradingSettings:
    """Runtime settings for an observation-only Trading copilot."""

    @property
    def TRADING_EXECUTION_ENABLED(self) -> bool:
        """Keep broker writes unavailable in every deployment profile.

        The retained property is a compatibility surface for callers and makes
        the safety invariant inspectable. Environment configuration cannot
        re-enable execution through this application.
        """
        return False


settings = TradingSettings()
