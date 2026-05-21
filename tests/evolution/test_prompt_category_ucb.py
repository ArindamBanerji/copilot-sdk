import inspect

from copilot_sdk import evolution
from copilot_sdk.evolution import (
    AgentEvolver,
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


def _evolver(exploration_constant: float = 1.0) -> PromptVariantEvolver:
    evolver = PromptVariantEvolver(
        config=PromptEvolverConfig(exploration_constant=exploration_constant)
    )
    evolver.register_variants([_variant("variant-a"), _variant("variant-b")])
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


def test_no_arg_selection_uses_global_ucb():
    evolver = _evolver()
    _record(evolver, "variant-a", 9, 1)
    _record(evolver, "variant-b", 1, 9)

    assert evolver.get_variant().id == "variant-a"


def test_category_selection_can_differ_from_global():
    evolver = _evolver()
    _record(evolver, "variant-a", 9, 1)
    _record(evolver, "variant-b", 1, 9)
    _record(evolver, "variant-a", 1, 9, category="schema_change")
    _record(evolver, "variant-b", 9, 1, category="schema_change")

    assert evolver.get_variant().id == "variant-a"
    assert evolver.get_variant(category="schema_change").id == "variant-b"


def test_category_ucb_not_raw_success_rate():
    evolver = _evolver()
    # Raw success rate favors A: 80/100 = 0.80 vs B: 3/4 = 0.75.
    # UCB favors B because its lower sample count earns a larger exploration term.
    _record(evolver, "variant-a", 80, 20, category="schema_change")
    _record(evolver, "variant-b", 3, 1, category="schema_change")

    assert evolver.get_variant(category="schema_change").id == "variant-b"


def test_cold_start_category_falls_back_to_global():
    evolver = _evolver()
    _record(evolver, "variant-a", 9, 1)
    _record(evolver, "variant-b", 1, 9)

    assert evolver.get_variant(category="new_category").id == "variant-a"


def test_record_outcome_updates_global_and_category():
    evolver = _evolver()

    evolver.record_outcome("variant-a", True, category="schema_change")

    assert evolver.store.get_global_stats("variant-a").successes == 1
    assert evolver.store.get_category_stats("schema_change", "variant-a").successes == 1


def test_record_outcome_without_category_global_only():
    evolver = _evolver()

    evolver.record_outcome("variant-a", True)

    assert evolver.store.get_global_stats("variant-a").total == 1
    assert evolver.store.get_all_category_stats("schema_change") == {}


def test_reset_clears_global_and_category_stats():
    evolver = _evolver()
    evolver.record_outcome("variant-a", True, category="schema_change")

    evolver.reset()

    assert evolver.get_summary()["variant_count"] == 0
    assert evolver.store.get_global_stats("variant-a").total == 0
    assert evolver.store.get_all_category_stats("schema_change") == {}


def test_reset_stats_preserves_variant_registrations():
    evolver = _evolver()
    evolver.record_outcome("variant-a", True, category="schema_change")

    evolver.reset_stats()

    assert evolver.get_summary()["variant_count"] == 2
    assert evolver.store.get_global_stats("variant-a").total == 0
    assert evolver.store.get_all_category_stats("schema_change") == {}


def test_ucb_exploration_constant_configurable():
    exploit = _evolver(exploration_constant=0.0)
    explore = _evolver(exploration_constant=1.0)
    for evolver in (exploit, explore):
        _record(evolver, "variant-a", 80, 20)
        _record(evolver, "variant-b", 3, 1)

    assert exploit.get_variant().id == "variant-a"
    assert explore.get_variant().id == "variant-b"


def test_ucb_tie_breaking_deterministic():
    evolver = _evolver()
    _record(evolver, "variant-a", 1, 1)
    _record(evolver, "variant-b", 1, 1)

    assert evolver.get_variant().id == "variant-a"


def test_ucb_cold_start_returns_first_active():
    assert _evolver().get_variant().id == "variant-a"


def test_ucb_ignores_retired_variants():
    evolver = PromptVariantEvolver()
    evolver.register_variants([
        _variant("variant-a"),
        _variant("variant-b", status="retired"),
    ])
    _record(evolver, "variant-a", 1, 9)
    _record(evolver, "variant-b", 10, 0)

    assert evolver.get_variant().id == "variant-a"


def test_category_resolver_normalizes_context_key():
    evolver = PromptVariantEvolver(
        config=PromptEvolverConfig(
            category_resolver=lambda context_key: {
                "anomalous_login": "credential_access",
            }[context_key]
        )
    )
    evolver.register_variants([_variant("variant-a"), _variant("variant-b")])
    _record(evolver, "variant-a", 1, 9, category="credential_access")
    _record(evolver, "variant-b", 9, 1, category="credential_access")

    assert evolver.get_variant(context_key="anomalous_login").id == "variant-b"


def test_category_wins_over_context_key():
    calls = []

    def resolver(context_key: str) -> str:
        calls.append(context_key)
        return "credential_access"

    evolver = PromptVariantEvolver(config=PromptEvolverConfig(category_resolver=resolver))
    evolver.register_variants([_variant("variant-a"), _variant("variant-b")])
    _record(evolver, "variant-a", 1, 9, category="schema_change")
    _record(evolver, "variant-b", 9, 1, category="schema_change")

    assert evolver.get_variant(category="schema_change", context_key="anomalous_login").id == "variant-b"
    assert calls == []


def test_context_key_resolved_when_no_category():
    evolver = PromptVariantEvolver(
        config=PromptEvolverConfig(category_resolver=lambda _context_key: "schema_change")
    )
    evolver.register_variants([_variant("variant-a"), _variant("variant-b")])
    _record(evolver, "variant-a", 1, 9, category="schema_change")
    _record(evolver, "variant-b", 9, 1, category="schema_change")

    assert evolver.get_variant(context_key="invoice").id == "variant-b"


def test_context_key_without_resolver_falls_back_global():
    evolver = _evolver()
    _record(evolver, "variant-a", 9, 1)
    _record(evolver, "variant-b", 1, 9)

    assert evolver.get_variant(context_key="invoice").id == "variant-a"


def test_two_evolvers_independent_stats():
    first = _evolver()
    second = _evolver()
    _record(first, "variant-a", 1, 9)
    _record(first, "variant-b", 9, 1)

    assert first.get_variant().id == "variant-b"
    assert second.get_variant().id == "variant-a"


def test_two_evolvers_independent_categories():
    first = _evolver()
    second = _evolver()
    _record(first, "variant-a", 1, 9, category="schema_change")
    _record(first, "variant-b", 9, 1, category="schema_change")

    assert first.get_variant(category="schema_change").id == "variant-b"
    assert second.get_variant(category="schema_change").id == "variant-a"


def test_no_soc_imports_in_prompt_evolver():
    source = inspect.getsource(prompt_evolver_module)

    assert "from app." not in source
    assert "import app." not in source
    assert "soc" not in source.lower()
    assert "credential_access" not in source
    assert "lateral_movement" not in source


def test_no_level1_imports_in_prompt_evolver():
    source = inspect.getsource(prompt_evolver_module)

    assert "ProfileScorer" not in source
    assert "CompoundingScorer" not in source
    assert "centroid" not in source
    assert "_scorer" not in source


def test_existing_agent_evolver_unchanged_importable():
    assert evolution.AgentEvolver is AgentEvolver
    assert evolution.PlateauConfig is PlateauConfig
    assert AgentEvolver() is not None
    assert PlateauConfig().enabled is True
