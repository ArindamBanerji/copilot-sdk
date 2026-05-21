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
    variant_id: str = "variant-a",
    family: str = "family-a",
    *,
    status: str = "active",
) -> VariantSpec:
    return VariantSpec(id=variant_id, family=family, status=status)


def test_register_and_select_variant():
    evolver = PromptVariantEvolver()

    evolver.register_variants([_variant()])

    assert evolver.get_variant().id == "variant-a"


def test_select_variant_returns_none_when_empty():
    assert PromptVariantEvolver().get_variant() is None


def test_select_variant_uses_default_variant_when_active():
    config = PromptEvolverConfig(default_variant_id="variant-b")
    evolver = PromptVariantEvolver(config=config)
    evolver.register_variants([
        _variant("variant-a"),
        _variant("variant-b"),
    ])

    assert evolver.get_variant().id == "variant-b"


def test_select_variant_skips_retired_default():
    config = PromptEvolverConfig(default_variant_id="variant-b")
    evolver = PromptVariantEvolver(config=config)
    evolver.register_variants([
        _variant("variant-a"),
        _variant("variant-b", status="retired"),
    ])

    assert evolver.get_variant().id == "variant-a"


def test_record_outcome_updates_store():
    evolver = PromptVariantEvolver()
    evolver.register_variants([_variant()])

    evolver.record_outcome("variant-a", True, category="finance")

    assert evolver.store.get_global_stats("variant-a").successes == 1
    assert evolver.store.get_category_stats("finance", "variant-a").successes == 1


def test_get_summary_includes_variant_stats():
    config = PromptEvolverConfig(categories=["finance"])
    evolver = PromptVariantEvolver(config=config)
    evolver.register_variants([_variant()])
    evolver.record_outcome("variant-a", True)

    summary = evolver.get_summary()

    assert summary["variant_count"] == 1
    assert summary["active_count"] == 1
    assert summary["categories"] == ["finance"]
    assert summary["variants"] == [
        {
            "id": "variant-a",
            "family": "family-a",
            "version": 1,
            "status": "active",
            "successes": 1,
            "failures": 0,
            "total": 1,
            "success_rate": 1.0,
        }
    ]


def test_reset_clears_evolver():
    evolver = PromptVariantEvolver()
    evolver.register_variants([_variant()])

    evolver.reset()

    assert evolver.get_summary()["variant_count"] == 0


def test_reset_stats_keeps_variants():
    evolver = PromptVariantEvolver()
    evolver.register_variants([_variant()])
    evolver.record_outcome("variant-a", True)

    evolver.reset_stats()

    assert evolver.get_summary()["variant_count"] == 1
    assert evolver.store.get_global_stats("variant-a").total == 0


def test_instance_isolation():
    first = PromptVariantEvolver()
    second = PromptVariantEvolver()
    first.register_variants([_variant()])

    assert first.get_variant() is not None
    assert second.get_variant() is None


def test_category_resolver_is_called_without_changing_impl1_selection():
    calls = []

    def resolver(context_key: str) -> str:
        calls.append(context_key)
        return "finance"

    evolver = PromptVariantEvolver(config=PromptEvolverConfig(category_resolver=resolver))
    evolver.register_variants([_variant()])

    assert evolver.get_variant(context_key="invoice").id == "variant-a"
    assert calls == ["invoice"]


def test_existing_agent_evolver_unchanged():
    assert evolution.AgentEvolver is AgentEvolver
    assert evolution.PlateauConfig is PlateauConfig
    assert AgentEvolver() is not None
    assert PlateauConfig().enabled is True


def test_no_level1_imports_in_prompt_evolver():
    source = inspect.getsource(prompt_evolver_module)

    assert "ProfileScorer" not in source
    assert "CompoundingScorer" not in source
    assert "centroid" not in source
    assert "copilot_sdk.scoring" not in source


def test_no_soc_imports_in_prompt_evolver():
    source = inspect.getsource(prompt_evolver_module)

    assert "from app." not in source
    assert "import app." not in source
    assert "soc" not in source.lower()
