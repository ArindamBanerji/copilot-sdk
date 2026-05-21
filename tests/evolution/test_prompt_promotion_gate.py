import inspect

from copilot_sdk import evolution
from copilot_sdk.evolution import (
    AgentEvolver,
    InMemoryEvolutionLedger,
    PlateauConfig,
    PromptEvolverConfig,
    PromptVariantEvolver,
    VariantSpec,
)
import copilot_sdk.evolution.prompt_evolver as prompt_evolver_module


def _variant(
    variant_id: str,
    *,
    family: str = "family-a",
    status: str = "active",
) -> VariantSpec:
    return VariantSpec(id=variant_id, family=family, status=status)


def _evolver(
    *,
    config: PromptEvolverConfig | None = None,
    ledger: InMemoryEvolutionLedger | None = None,
) -> PromptVariantEvolver:
    evolver = PromptVariantEvolver(config=config, ledger=ledger)
    evolver.register_variants([
        _variant("active-a"),
        _variant("candidate-a", status="shadow"),
    ])
    return evolver


def _record(
    evolver: PromptVariantEvolver,
    variant_id: str,
    successes: int,
    failures: int,
    *,
    category: str | None = None,
) -> None:
    for _ in range(successes):
        evolver.record_outcome(variant_id, True, category=category)
    for _ in range(failures):
        evolver.record_outcome(variant_id, False, category=category)


def test_promotion_when_candidate_exceeds_threshold():
    evolver = _evolver()
    _record(evolver, "active-a", 6, 4)
    _record(evolver, "candidate-a", 9, 1)

    result = evolver.check_for_promotion("family-a")

    assert result["promoted_id"] == "candidate-a"
    assert result["previous_id"] == "active-a"


def test_no_promotion_below_threshold():
    evolver = _evolver()
    _record(evolver, "active-a", 8, 2)
    _record(evolver, "candidate-a", 8, 2)

    assert evolver.check_for_promotion("family-a") is None


def test_no_promotion_at_equal_threshold():
    evolver = _evolver(config=PromptEvolverConfig(promotion_improvement_threshold=0.05))
    _record(evolver, "active-a", 8, 2)
    _record(evolver, "candidate-a", 17, 3)

    assert evolver.check_for_promotion("family-a") is None


def test_no_promotion_insufficient_samples():
    evolver = _evolver()
    _record(evolver, "active-a", 6, 4)
    _record(evolver, "candidate-a", 4, 0)

    assert evolver.check_for_promotion("family-a") is None


def test_promotion_updates_variant_statuses():
    evolver = _evolver()
    _record(evolver, "active-a", 6, 4)
    _record(evolver, "candidate-a", 9, 1)

    evolver.check_for_promotion("family-a")

    assert evolver.store.get_variant("active-a").status == "retired"
    assert evolver.store.get_variant("candidate-a").status == "active"


def test_promotion_returns_result_dict():
    evolver = _evolver()
    _record(evolver, "active-a", 6, 4)
    _record(evolver, "candidate-a", 9, 1)

    result = evolver.check_for_promotion("family-a")

    assert result == {
        "family": "family-a",
        "promoted_id": "candidate-a",
        "previous_id": "active-a",
        "improvement": 0.30000000000000004,
        "candidate_rate": 0.9,
        "active_rate": 0.6,
        "candidate_total": 10,
    }


def test_no_promotion_returns_none():
    evolver = _evolver()

    assert evolver.check_for_promotion("family-a") is None


def test_promotion_per_family():
    evolver = _evolver()
    evolver.register_variants([
        _variant("active-b", family="family-b"),
        _variant("candidate-b", family="family-b", status="shadow"),
    ])
    _record(evolver, "active-a", 6, 4)
    _record(evolver, "candidate-a", 9, 1)
    _record(evolver, "active-b", 9, 1)
    _record(evolver, "candidate-b", 1, 9)

    result = evolver.check_for_promotion("family-b")

    assert result is None
    assert evolver.store.get_variant("candidate-a").status == "shadow"


def test_promotion_family_none_checks_all():
    evolver = _evolver()
    evolver.register_variants([
        _variant("active-b", family="family-b"),
        _variant("candidate-b", family="family-b", status="shadow"),
    ])
    _record(evolver, "active-a", 9, 1)
    _record(evolver, "candidate-a", 1, 9)
    _record(evolver, "active-b", 6, 4)
    _record(evolver, "candidate-b", 9, 1)

    result = evolver.check_for_promotion()

    assert result["family"] == "family-b"
    assert result["promoted_id"] == "candidate-b"


def test_promotion_uses_global_stats_not_category_stats():
    evolver = _evolver()
    _record(evolver, "active-a", 9, 1)
    _record(evolver, "candidate-a", 1, 9)
    _record(evolver, "candidate-a", 20, 0, category="schema_change")

    assert evolver.check_for_promotion("family-a") is None


def test_shadow_result_updates_stats():
    evolver = _evolver()

    evolver.record_shadow_result("candidate-a", True, batch_id="batch-1")

    assert evolver.store.get_global_stats("candidate-a").successes == 1
    assert evolver.store.get_all_category_stats("schema_change") == {}


def test_shadow_result_unknown_variant_rejected():
    evolver = _evolver()

    try:
        evolver.record_shadow_result("missing", True)
    except ValueError as exc:
        assert "Unknown variant" in str(exc)
    else:
        raise AssertionError("expected ValueError")


def test_shadow_result_emits_ledger_event():
    ledger = InMemoryEvolutionLedger()
    evolver = _evolver(ledger=ledger)

    evolver.record_shadow_result("candidate-a", True, batch_id="batch-1")

    events = ledger.get_events()
    assert len(events) == 1
    assert events[0]["event_type"] == "shadow_completed"
    assert events[0]["variant_id"] == "candidate-a"
    assert events[0]["metadata"]["batch_id"] == "batch-1"
    assert events[0]["metadata"]["success"] is True


def test_shadow_thresholds_in_config_not_used_by_simple_promotion():
    config = PromptEvolverConfig(
        shadow_delta_min=99.0,
        shadow_q_floor=99.0,
        shadow_sigma_max=-1.0,
        shadow_min_samples=9999,
        shadow_min_batches=9999,
    )
    evolver = _evolver(config=config)
    _record(evolver, "active-a", 6, 4)
    _record(evolver, "candidate-a", 9, 1)

    assert evolver.check_for_promotion("family-a")["promoted_id"] == "candidate-a"


def test_on_promoted_hook_called():
    calls = []
    evolver = _evolver(config=PromptEvolverConfig(on_promoted=calls.append))
    _record(evolver, "active-a", 6, 4)
    _record(evolver, "candidate-a", 9, 1)

    evolver.check_for_promotion("family-a")

    assert calls[0]["promoted_id"] == "candidate-a"
    assert calls[0]["previous_id"] == "active-a"


def test_on_variant_selected_hook_called_if_implemented():
    calls = []
    evolver = PromptVariantEvolver(config=PromptEvolverConfig(on_variant_selected=calls.append))
    evolver.register_variants([_variant("active-a")])

    selected = evolver.get_variant()

    assert selected.id == "active-a"
    assert calls == [
        {
            "variant_id": "active-a",
            "family": "family-a",
            "category": None,
            "source": "global_ucb",
        }
    ]


def test_on_outcome_recorded_hook_called_for_shadow_result():
    calls = []
    evolver = _evolver(config=PromptEvolverConfig(on_outcome_recorded=calls.append))

    evolver.record_shadow_result("candidate-a", False, batch_id="batch-1")

    assert calls == [
        {
            "variant_id": "candidate-a",
            "family": "family-a",
            "success": False,
            "batch_id": "batch-1",
            "source": "shadow_result",
        }
    ]


def test_lifecycle_event_emitted_to_ledger():
    ledger = InMemoryEvolutionLedger()
    evolver = _evolver(ledger=ledger)
    _record(evolver, "active-a", 6, 4)
    _record(evolver, "candidate-a", 9, 1)

    evolver.check_for_promotion("family-a")

    events = ledger.get_events()
    assert events[0]["event_type"] == "promoted"
    assert events[0]["rule_name"] == "family-a"
    assert events[0]["variant_id"] == "candidate-a"
    assert events[0]["metadata"]["previous_active"] == "active-a"


def test_promotion_does_not_import_scorer():
    source = inspect.getsource(prompt_evolver_module)

    assert "ProfileScorer" not in source
    assert "CompoundingScorer" not in source
    assert "centroid" not in source
    assert "_scorer" not in source


def test_no_soc_imports():
    source = inspect.getsource(prompt_evolver_module)

    assert "from app." not in source
    assert "import app." not in source
    assert "soc" not in source.lower()
    assert "credential_access" not in source
    assert "lateral_movement" not in source


def test_existing_agent_evolver_unchanged_importable():
    assert evolution.AgentEvolver is AgentEvolver
    assert evolution.PlateauConfig is PlateauConfig
    assert AgentEvolver() is not None
    assert PlateauConfig().enabled is True
