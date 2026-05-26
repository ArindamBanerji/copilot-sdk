from __future__ import annotations

from copilot_sdk.evolution import AgentEvolver, EvolutionEvent, InMemoryEvolutionLedger, PlateauConfig


class CountingRule:
    name = "plateau-rule"

    def __init__(self) -> None:
        self.generated = 0

    def predict(self, decision):
        return "review"

    def generate_variant(self, seed=None):
        self.generated += 1
        return Variant(f"variant-{self.generated}", "accept")


class Variant:
    def __init__(self, variant_id: str, action: str) -> None:
        self.variant_id = variant_id
        self.action = action

    def predict(self, decision):
        return self.action


def _decisions(count: int = 10) -> list[dict[str, str]]:
    return [
        {
            "recommended_action": "review",
            "actual_action": "accept",
        }
        for _ in range(count)
    ]


def _evolver(
    ledger: InMemoryEvolutionLedger,
    *,
    cooldown: int = 2,
    min_improvement_rate: float = 0.2,
) -> tuple[AgentEvolver, CountingRule]:
    rule = CountingRule()
    evolver = AgentEvolver(
        ledger=ledger,
        plateau_config=PlateauConfig(
            plateau_window=10,
            min_improvement_rate=min_improvement_rate,
            plateau_cooldown=cooldown,
        ),
    )
    evolver.register_rule(rule)
    return evolver, rule


def _record_gain_events(
    ledger: InMemoryEvolutionLedger,
    positives: int,
    total: int = 10,
) -> None:
    for index in range(total):
        accuracy = 0.7 if index < positives else 0.5
        baseline = 0.5
        ledger.append(
            EvolutionEvent(
                "shadow_completed",
                "plateau-rule",
                f"variant-{index}",
                metadata={
                    "accuracy": accuracy,
                    "baseline_accuracy": baseline,
                },
            )
        )


def test_plateau_detected_when_no_recent_gains():
    ledger = InMemoryEvolutionLedger()
    _record_gain_events(ledger, positives=0)
    evolver, rule = _evolver(ledger)

    result = evolver.evolve("plateau-rule", _decisions(), conservation_state={"status": "GREEN"})

    assert result["promoted"] is False
    assert result["reason"] == "plateau_cooldown"
    assert result["plateau_detected"] is True
    assert result["metadata"]["improvement_rate"] == 0.0
    assert rule.generated == 0


def test_plateau_not_detected_with_recent_gains():
    ledger = InMemoryEvolutionLedger()
    _record_gain_events(ledger, positives=5)
    evolver, rule = _evolver(ledger)

    result = evolver.evolve("plateau-rule", _decisions(), conservation_state={"status": "GREEN"})

    assert result["promoted"] is True
    assert result["reason"] == "promoted"
    assert rule.generated == 1


def test_plateau_cooldown_skips_evolution():
    ledger = InMemoryEvolutionLedger()
    _record_gain_events(ledger, positives=0)
    evolver, rule = _evolver(ledger, cooldown=2)

    first = evolver.evolve("plateau-rule", _decisions())
    second = evolver.evolve("plateau-rule", _decisions())

    assert first["plateau_detected"] is True
    assert second["plateau_detected"] is False
    assert second["reason"] == "plateau_cooldown"
    assert second["cooldown_remaining"] == 1
    assert rule.generated == 0


def test_plateau_resumes_after_cooldown():
    ledger = InMemoryEvolutionLedger()
    _record_gain_events(ledger, positives=0)
    evolver, rule = _evolver(ledger, cooldown=1)

    evolver.evolve("plateau-rule", _decisions(), conservation_state={"status": "GREEN"})
    skipped = evolver.evolve("plateau-rule", _decisions(), conservation_state={"status": "GREEN"})
    resumed = evolver.evolve("plateau-rule", _decisions(), conservation_state={"status": "GREEN"})

    assert skipped["reason"] == "plateau_cooldown"
    assert resumed["promoted"] is True
    assert resumed["reason"] == "promoted"
    assert rule.generated == 1


def test_plateau_config_from_preset():
    config = PlateauConfig()
    evolver = AgentEvolver(plateau_config=config)

    assert config.plateau_window == 10
    assert config.min_improvement_rate == 0.2
    assert config.plateau_cooldown == 50
    assert evolver.plateau_config is config


def test_plateau_logged_as_evolution_event():
    ledger = InMemoryEvolutionLedger()
    _record_gain_events(ledger, positives=0)
    evolver, _ = _evolver(ledger)

    evolver.evolve("plateau-rule", _decisions())

    event = ledger.get_events("plateau-rule")[-1]
    assert event["event_type"] == "plateau_detected"
    assert event["variant_id"] == "plateau"
    assert event["metadata"]["plateau_window"] == 10
    assert event["metadata"]["min_improvement_rate"] == 0.2
    assert event["metadata"]["cooldown"] == 2
