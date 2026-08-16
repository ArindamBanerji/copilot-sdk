"""Guard the semantic boundary around legacy SOC factor-0 fixtures."""

import json
from pathlib import Path

from copilot_sdk.scoring.presets.soc import SOCPreset


SCENARIOS_PATH = (
    Path(__file__).parents[2]
    / "gen-ai-roi-demo-v4-v50"
    / "backend"
    / "app"
    / "data"
    / "soc_eval_scenarios.json"
)


def test_soc_legacy_scenarios_are_semantically_quarantined():
    data = json.loads(SCENARIOS_PATH.read_text(encoding="utf-8"))

    assert isinstance(data, list)
    assert len(data) == 36
    assert all(
        scenario.get("factor_0_semantic_version") == "travel_match_v1"
        for scenario in data
    )
    assert all(
        scenario["factor_0_semantic_version"] != "privileged_identity_context_v1"
        for scenario in data
    )


def test_sdk_soc_preset_uses_canonical_factor_zero():
    preset = SOCPreset()

    assert preset.shape.factor_names[0] == "privileged_identity_context"
    assert "travel_match" not in preset.shape.factor_names
