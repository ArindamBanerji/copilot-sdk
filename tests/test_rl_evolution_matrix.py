"""WP-5 parametrized checks for the SDK copilot evolution contract.

The fixtures load each app's real startup object and use the real SDK
evolver, graph store, scorer, and promotion gate.  The deterministic provider
states are contract inputs, not replacements for production conservation
helpers.
"""

from __future__ import annotations

import ast
import importlib
import sys
from dataclasses import dataclass, replace
from pathlib import Path
from types import ModuleType
from typing import Any, Callable

import pytest

from copilot_sdk.evolution import DefaultPromotionGate, PromptVariantEvolver
from copilot_sdk.graph import InMemoryGraphStore
from copilot_sdk.scoring.scorer import CompoundingScorer


ROOT = Path(__file__).resolve().parents[1]
COPILOTS = ("trading", "purchasing", "dataops")


@dataclass(frozen=True)
class CopilotConfig:
    name: str
    backend: Path
    source_root: Path
    preset: str
    config_module: str
    specs_getter: str


def _config(name: str) -> CopilotConfig:
    backend = ROOT / "apps" / name / "backend"
    return CopilotConfig(
        name=name,
        backend=backend,
        source_root=backend / "app",
        preset=name,
        config_module=f"app.evolution.evolver_config",
        specs_getter=f"get_{name}_variant_specs",
    )


@pytest.fixture(params=COPILOTS, ids=COPILOTS)
def copilot_config(request: pytest.FixtureRequest) -> CopilotConfig:
    return _config(str(request.param))


def _load_app(config: CopilotConfig) -> ModuleType:
    for module_name in list(sys.modules):
        if module_name == "app" or module_name.startswith("app."):
            del sys.modules[module_name]
    sys.path.insert(0, str(config.backend))
    try:
        return importlib.import_module("app.main")
    finally:
        sys.path.remove(str(config.backend))


def _runtime_evolver(config: CopilotConfig) -> Any:
    return _load_app(config).app.state.evolver


def _sdk_evolver(config: CopilotConfig, provider: Callable[[], dict[str, Any]]) -> PromptVariantEvolver:
    _load_app(config)
    config_module = importlib.import_module(config.config_module)
    config_object = replace(getattr(config_module, f"{config.name.upper()}_EVOLVER_CONFIG"), conservation_state_provider=provider)
    evolver = PromptVariantEvolver(config=config_object)
    specs = getattr(config_module, config.specs_getter)()
    evolver.register_variants(specs)
    return evolver


def _variant_ids(evolver: Any) -> set[str]:
    registered = getattr(evolver, "registered_variants", None)
    if registered is not None:
        return {str(item.get("variant_id") or item.get("id")) for item in registered}
    return {str(item.id) for item in evolver.store.get_all_variants()}


def _configured_ids(config: CopilotConfig) -> set[str]:
    module = _load_app(config)
    specs = getattr(importlib.import_module(config.config_module), config.specs_getter)()
    del module
    return {str(spec.id) for spec in specs}


def _families(evolver: PromptVariantEvolver) -> tuple[str, str]:
    variants = evolver.store.get_all_variants()
    active = next(item for item in variants if item.status == "active")
    shadow = next(item for item in variants if item.status == "shadow" and item.family == active.family)
    return active.id, shadow.id


def _record_rates(evolver: PromptVariantEvolver, active_id: str, shadow_id: str, active_success: int, shadow_success: int) -> None:
    for index in range(50):
        evolver.record_outcome(active_id, index < active_success)
        evolver.record_outcome(shadow_id, index < shadow_success)


def _green() -> dict[str, Any]:
    return {"status": "GREEN", "overallSafe": True, "source": "matrix-contract"}


def test_t_startup(copilot_config: CopilotConfig) -> None:
    app_module = _load_app(copilot_config)
    evolver = app_module.app.state.evolver
    assert evolver is not None
    assert _variant_ids(evolver) == _configured_ids(copilot_config)
    assert app_module.app.state.evolver is evolver


def test_t_nolit(copilot_config: CopilotConfig) -> None:
    violations: list[str] = []
    for path in copilot_config.source_root.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            for keyword in node.keywords:
                if keyword.arg != "conservation_state":
                    continue
                if isinstance(keyword.value, ast.Constant) and str(keyword.value.value).upper() in {"GREEN", "AMBER", "RED"}:
                    violations.append(f"{path}:{node.lineno}")
    assert not violations, violations


def test_t_amber(copilot_config: CopilotConfig) -> None:
    evolver = _sdk_evolver(copilot_config, lambda: {"status": "AMBER", "overallSafe": False})
    active_id, shadow_id = _families(evolver)
    _record_rates(evolver, active_id, shadow_id, 20, 50)
    result = evolver.check_for_promotion()
    assert result is not None
    assert result["promoted"] is False
    assert "conservation" in str(result["reason"])


def test_t_green(copilot_config: CopilotConfig) -> None:
    evolver = _sdk_evolver(copilot_config, _green)
    active_id, shadow_id = _families(evolver)
    _record_rates(evolver, active_id, shadow_id, 20, 50)
    result = evolver.check_for_promotion()
    assert result is not None
    assert result.get("promoted_id") == shadow_id


def test_t_sup(copilot_config: CopilotConfig) -> None:
    evolver = _sdk_evolver(copilot_config, _green)
    active_id, shadow_id = _families(evolver)
    _record_rates(evolver, active_id, shadow_id, 25, 26)
    assert evolver.check_for_promotion() is None


def test_t_var(copilot_config: CopilotConfig) -> None:
    gate = DefaultPromotionGate(min_shadow_decisions=10)
    result = gate.evaluate({"sufficient": True, "total": 50, "accuracy": 0.90, "baseline_accuracy": 0.80, "batch_accuracies": [0.50, 0.90, 0.50]}, _green())
    assert result["promoted"] is False
    assert "variance" in result["reason"]


def test_t_samp(copilot_config: CopilotConfig) -> None:
    gate = DefaultPromotionGate(min_shadow_decisions=10)
    result = gate.evaluate({"sufficient": False, "total": 2, "accuracy": 0.95, "baseline_accuracy": 0.80, "batch_accuracies": [0.95, 0.95, 0.95]}, _green())
    assert result["promoted"] is False
    assert "sufficient_data" in result["reason"]


def test_t_outcome(copilot_config: CopilotConfig) -> None:
    evolver = _runtime_evolver(copilot_config)
    if copilot_config.name == "trading":
        variant_id = next(item["variant_id"] for item in evolver.registered_variants)
        before = evolver.evolution_log()[0]["successes"]
        evolver.record_verified_outcome(variant_id, True, category="matrix")
        after = next(item["successes"] for item in evolver.evolution_log() if item["variant_id"] == variant_id)
    else:
        variant_id = evolver.store.get_all_variants()[0].id
        before = evolver.store.get_global_stats(variant_id).total
        evolver.record_outcome(variant_id, True, category="matrix")
        after = evolver.store.get_global_stats(variant_id).total
    assert after == before + 1


def test_t_g1(copilot_config: CopilotConfig) -> None:
    scorer_with_rl = CompoundingScorer.from_preset(copilot_config.preset, graph_store=InMemoryGraphStore(domain=copilot_config.preset), enable_rl=True, profile="test")
    scorer_without_rl = CompoundingScorer.from_preset(copilot_config.preset, graph_store=InMemoryGraphStore(domain=copilot_config.preset), enable_rl=False, profile="test")
    factors = {name: 0.5 for name in scorer_with_rl._preset.shape.factor_names}
    category = scorer_with_rl._preset.shape.category_names[0]
    try:
        first = scorer_with_rl.score(factors, category)
        second = scorer_without_rl.score(factors, category)
        assert first.action == second.action
        assert first.action_index == second.action_index
        assert first.probabilities == pytest.approx(second.probabilities)
    finally:
        scorer_with_rl.graph_store.close()
        scorer_without_rl.graph_store.close()
