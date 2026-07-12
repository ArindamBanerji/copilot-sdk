import inspect

from copilot_sdk.evolution import PromptEvolverConfig, PromptVariantEvolver, VariantSpec
from copilot_sdk.evolution.gate import DefaultPromotionGate
import copilot_sdk.evolution.gate as gate_module
import copilot_sdk.evolution.prompt_evolver as prompt_evolver_module
import copilot_sdk.scoring.scorer as scorer_module


def _variant(variant_id: str, status: str) -> VariantSpec:
    return VariantSpec(id=variant_id, family="family-a", status=status)


def _promotion_ready_evolver(**config_kwargs) -> PromptVariantEvolver:
    evolver = PromptVariantEvolver(config=PromptEvolverConfig(**config_kwargs))
    evolver.register_variants([
        _variant("active-a", "active"),
        _variant("candidate-a", "shadow"),
    ])
    for _ in range(6):
        evolver.record_outcome("active-a", True)
    for _ in range(4):
        evolver.record_outcome("active-a", False)
    for _ in range(9):
        evolver.record_outcome("candidate-a", True)
    evolver.record_outcome("candidate-a", False)
    return evolver


def test_gc01_prompt_promotion_blocked_when_conservation_red() -> None:
    evolver = _promotion_ready_evolver()

    result = evolver.check_for_promotion("family-a", conservation_state={"status": "RED"})

    assert result is not None
    assert result["promoted"] is False
    assert "conservation" in result["reason"]
    assert evolver.store.get_variant("active-a").status == "active"
    assert evolver.store.get_variant("candidate-a").status == "shadow"


def test_gc02_prompt_promotion_allowed_when_conservation_green() -> None:
    evolver = _promotion_ready_evolver()

    result = evolver.check_for_promotion("family-a", conservation_state={"status": "GREEN"})

    assert result is not None
    assert result["promoted_id"] == "candidate-a"
    assert evolver.store.get_variant("active-a").status == "retired"
    assert evolver.store.get_variant("candidate-a").status == "active"


def test_gc03_prompt_promotion_fails_closed_when_conservation_unknown() -> None:
    def broken_provider() -> dict:
        raise RuntimeError("conservation unavailable")

    evolver = _promotion_ready_evolver(conservation_state_provider=broken_provider)

    result = evolver.check_for_promotion("family-a")

    assert result is not None
    assert result["promoted"] is False
    assert "conservation" in result["reason"]
    assert evolver.store.get_variant("active-a").status == "active"
    assert evolver.store.get_variant("candidate-a").status == "shadow"


def test_gc04_conservation_gate_coverage_across_l1_l2_l2b() -> None:
    assert hasattr(DefaultPromotionGate, "_is_conservation_safe")
    assert "_conservation_pause" in inspect.getsource(scorer_module.CompoundingScorer.learn)
    assert "_is_conservation_safe" in inspect.getsource(gate_module.DefaultPromotionGate.evaluate)
    assert "_is_conservation_safe" in inspect.getsource(prompt_evolver_module.PromptVariantEvolver)
