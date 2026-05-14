"""Preset registry for future domain-specific adapters."""

from copilot_sdk.scoring.presets.trading import TradingPreset
from copilot_sdk.scoring.presets.purchasing import PurchasingPreset
from copilot_sdk.scoring.presets.dataops import DataOpsPreset
from copilot_sdk.scoring.presets.s2p import S2PPreset

PRESET_REGISTRY: dict[str, type] = {
    "dataops": DataOpsPreset,
    "purchasing": PurchasingPreset,
    "s2p": S2PPreset,
    "trading": TradingPreset,
}

# Additional production presets are implemented in separate prompts.
