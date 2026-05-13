from __future__ import annotations

from pathlib import Path

import pytest

from copilot_sdk.evolution import (
    EVOLUTION_EVENT_TYPES,
    EvolutionEvent,
    EvolutionLedger,
    EvolutionRule,
    PromotionGate,
    ShadowRunner,
)


class SampleRule:
    name = "sample_rule"

    def generate_variant(self, seed=None):
        return {"variant_id": "variant-1", "action": "accept"}


class SampleLedger:
    def append(self, event):
        return None

    def get_events(self, rule_name=None, limit=100):
        return []

    def get_promoted_rules(self):
        return []

    def reset(self):
        return None


class SampleShadow:
    def run_shadow(self, variant, decisions, baseline=None):
        return {}


class SampleGate:
    def evaluate(self, shadow_results, conservation_state=None):
        return {}


def test_event_types_are_expected():
    assert EVOLUTION_EVENT_TYPES == frozenset(
        {
            "variant_generated",
            "shadow_started",
            "shadow_completed",
            "promoted",
            "rejected",
            "rollback",
        }
    )


def test_evolution_event_validates_type():
    with pytest.raises(ValueError):
        EvolutionEvent("unknown", "rule", "variant")


def test_evolution_event_defaults_metadata_and_timestamp():
    event = EvolutionEvent("variant_generated", "rule", "variant")

    assert event.metadata == {}
    assert event.timestamp


def test_protocols_are_runtime_checkable():
    assert isinstance(SampleRule(), EvolutionRule)
    assert isinstance(SampleLedger(), EvolutionLedger)
    assert isinstance(SampleShadow(), ShadowRunner)
    assert isinstance(SampleGate(), PromotionGate)


def test_no_domain_vocabulary_in_evolution_module():
    root = Path("copilot_sdk/evolution")
    forbidden = [
        "credential_access",
        "lateral_movement",
        "data_exfiltration",
        "invoice",
        "supplier",
        "ticker",
        "portfolio",
        "from app.",
        "gen_ai_roi",
        "soc",
    ]
    text = "\n".join(path.read_text(encoding="utf-8") for path in root.glob("*.py")).lower()

    for word in forbidden:
        assert word not in text
