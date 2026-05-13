from __future__ import annotations

from copilot_sdk.evolution import AgentEvolver, InMemoryEvolutionLedger


class Rule:
    name = "rule-a"

    def predict(self, decision):
        return "review"

    def generate_variant(self, seed=None):
        return Variant(seed or "variant-a", "accept")


class Variant:
    def __init__(self, variant_id, action):
        self.variant_id = variant_id
        self.action = action

    def predict(self, decision):
        return self.action


class FailingRule:
    name = "failing-rule"

    def generate_variant(self, seed=None):
        raise RuntimeError("boom")


def _decisions(count=10):
    return [
        {
            "actual_action": "accept",
            "recommended_action": "review",
            "metadata": {},
        }
        for _ in range(count)
    ]


def test_register_rule_adds_active_rule():
    evolver = AgentEvolver()
    rule = Rule()

    evolver.register_rule(rule)

    assert evolver.get_active_rules()["rule-a"] is rule


def test_get_active_rules_returns_copy():
    evolver = AgentEvolver()
    evolver.register_rule(Rule())

    active = evolver.get_active_rules()
    active.clear()

    assert "rule-a" in evolver.get_active_rules()


def test_evolve_missing_rule_rejected():
    result = AgentEvolver().evolve("missing", _decisions())

    assert result["promoted"] is False
    assert result["reason"] == "not_registered"


def test_evolve_promotes_variant_and_replaces_active_rule():
    evolver = AgentEvolver()
    evolver.register_rule(Rule())

    result = evolver.evolve("rule-a", _decisions(), conservation_state={"status": "GREEN"})

    assert result["promoted"] is True
    assert evolver.get_active_rules()["rule-a"].variant_id == "variant-a"


def test_evolve_rejects_when_shadow_insufficient():
    evolver = AgentEvolver()
    rule = Rule()
    evolver.register_rule(rule)

    result = evolver.evolve("rule-a", _decisions(count=2))

    assert result["promoted"] is False
    assert result["reason"] == "sufficient_data"
    assert evolver.get_active_rules()["rule-a"] is rule


def test_evolve_generation_failure_records_rejection_and_keeps_rule():
    evolver = AgentEvolver()
    rule = FailingRule()
    evolver.register_rule(rule)

    result = evolver.evolve("failing-rule", _decisions(), seed={"try": 1})

    assert result["promoted"] is False
    assert "generation_failed" in result["reason"]
    assert evolver.get_active_rules()["failing-rule"] is rule
    history = evolver.get_evolution_history("failing-rule")
    assert [event["event_type"] for event in history] == ["rejected"]
    assert history[0]["metadata"]["reason"] == "generation_failed"
    assert history[0]["metadata"]["error"] == "boom"
    assert history[0]["metadata"]["seed"] == {"try": 1}


def test_evolve_records_event_sequence_on_promotion():
    ledger = InMemoryEvolutionLedger()
    evolver = AgentEvolver(ledger=ledger)
    evolver.register_rule(Rule())

    evolver.evolve("rule-a", _decisions())

    assert [event["event_type"] for event in ledger.get_events()] == [
        "variant_generated",
        "shadow_started",
        "shadow_completed",
        "promoted",
    ]


def test_evolve_records_rejection_event():
    ledger = InMemoryEvolutionLedger()
    evolver = AgentEvolver(ledger=ledger)
    evolver.register_rule(Rule())

    evolver.evolve("rule-a", _decisions(count=2))

    assert ledger.get_events()[-1]["event_type"] == "rejected"


def test_evolution_history_filters_by_rule():
    evolver = AgentEvolver()
    evolver.register_rule(Rule())
    evolver.evolve("rule-a", _decisions())

    assert all(event["rule_name"] == "rule-a" for event in evolver.get_evolution_history("rule-a"))


def test_get_promoted_rules_delegates_to_ledger():
    evolver = AgentEvolver()
    evolver.register_rule(Rule())
    evolver.evolve("rule-a", _decisions())

    assert evolver.get_promoted_rules() == ["rule-a"]


def test_reset_clears_ledger_but_keeps_active_rules():
    evolver = AgentEvolver()
    evolver.register_rule(Rule())
    evolver.evolve("rule-a", _decisions())

    evolver.reset()

    assert evolver.get_evolution_history() == []
    assert "rule-a" in evolver.get_active_rules()


def test_evolve_uses_seed_as_variant_id():
    evolver = AgentEvolver()
    evolver.register_rule(Rule())

    result = evolver.evolve("rule-a", _decisions(), seed="variant-seeded")

    assert result["variant_id"] == "variant-seeded"


def test_evolve_returns_shadow_and_gate_results():
    evolver = AgentEvolver()
    evolver.register_rule(Rule())

    result = evolver.evolve("rule-a", _decisions())

    assert result["shadow_results"]["accuracy"] == 1.0
    assert result["gate_result"]["promoted"] is True
