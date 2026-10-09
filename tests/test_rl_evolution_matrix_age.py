"""Real app evolution checks from the parametrized matrix, guarded by AGE."""

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
from copilot_sdk.testing.fixtures import requires_age


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
    return CopilotConfig(name, backend, backend / "app", name,
                         "app.evolution.evolver_config", f"get_{name}_variant_specs")


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
    config_object = replace(
        getattr(config_module, f"{config.name.upper()}_EVOLVER_CONFIG"),
        conservation_state_provider=provider,
    )
    evolver = PromptVariantEvolver(config=config_object)
    evolver.register_variants(getattr(config_module, config.specs_getter)())
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


def _record_rates(evolver: PromptVariantEvolver, active_id: str, shadow_id: str,
                  active_success: int, shadow_success: int) -> None:
    for index in range(50):
        evolver.record_outcome(active_id, index < active_success)
        evolver.record_outcome(shadow_id, index < shadow_success)


def _green() -> dict[str, Any]:
    return {"status": "GREEN", "overallSafe": True, "source": "matrix-contract"}


@pytest.fixture(autouse=True)
def _clear_app_modules():
    yield
    for module_name in list(sys.modules):
        if module_name == "app" or module_name.startswith("app."):
            del sys.modules[module_name]


@requires_age
def test_t_startup(copilot_config: CopilotConfig) -> None:
    app_module = _load_app(copilot_config)
    evolver = app_module.app.state.evolver
    assert evolver is not None
    assert _variant_ids(evolver) == _configured_ids(copilot_config)
    assert app_module.app.state.evolver is evolver


@requires_age
def test_t_amber(copilot_config: CopilotConfig) -> None:
    evolver = _sdk_evolver(copilot_config, lambda: {"status": "AMBER", "overallSafe": False})
    active_id, shadow_id = _families(evolver)
    _record_rates(evolver, active_id, shadow_id, 20, 50)
    result = evolver.check_for_promotion()
    assert result is not None
    assert result["promoted"] is False
    assert "conservation" in str(result["reason"])


@requires_age
def test_t_green(copilot_config: CopilotConfig) -> None:
    evolver = _sdk_evolver(copilot_config, _green)
    active_id, shadow_id = _families(evolver)
    _record_rates(evolver, active_id, shadow_id, 20, 50)
    result = evolver.check_for_promotion()
    assert result is not None
    assert result.get("promoted_id") == shadow_id


@requires_age
def test_t_sup(copilot_config: CopilotConfig) -> None:
    evolver = _sdk_evolver(copilot_config, _green)
    active_id, shadow_id = _families(evolver)
    _record_rates(evolver, active_id, shadow_id, 25, 26)
    assert evolver.check_for_promotion() is None


@requires_age
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
