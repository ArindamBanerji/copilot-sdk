"""Preset registry for future domain-specific adapters."""

from copilot_sdk.scoring.presets.trading import TradingPreset
from copilot_sdk.scoring.presets.purchasing import PurchasingPreset
from copilot_sdk.scoring.presets.dataops import DataOpsPreset

PRESET_REGISTRY: dict[str, type] = {
    "dataops": DataOpsPreset,
    "purchasing": PurchasingPreset,
    "trading": TradingPreset,
}

# Additional production presets are implemented in separate prompts.
