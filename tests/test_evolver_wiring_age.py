"""Real Purchasing/DataOps evolver wiring checks requiring AGE."""

from __future__ import annotations

import importlib
import sys
from pathlib import Path
from types import ModuleType

import pytest

from copilot_sdk.evolution import PromptVariantEvolver
from copilot_sdk.testing.fixtures import requires_age


ROOT = Path(__file__).resolve().parents[1]


def _load_app(copilot: str) -> ModuleType:
    """Load an app package in isolation; Purchasing and DataOps both use ``app``."""
    for name in list(sys.modules):
        if name == "app" or name.startswith("app."):
            del sys.modules[name]
    backend = ROOT / "apps" / copilot / "backend"
    sys.path.insert(0, str(backend))
    try:
        return importlib.import_module("app.main")
    finally:
        sys.path.remove(str(backend))


@pytest.fixture(autouse=True)
def _clear_app_modules():
    yield
    for name in list(sys.modules):
        if name == "app" or name.startswith("app."):
            del sys.modules[name]


@requires_age
def test_purchasing_evolver_instantiated() -> None:
    evolver = _load_app("purchasing").app.state.evolver
    assert isinstance(evolver, PromptVariantEvolver)


@requires_age
def test_purchasing_variants_registered() -> None:
    evolver = _load_app("purchasing").app.state.evolver
    variants = evolver.store.get_all_variants()
    assert sum(variant.status == "active" for variant in variants) == 6
    assert sum(variant.status == "shadow" for variant in variants) == 6


@requires_age
def test_purchasing_conservation_provider_live() -> None:
    provider = _load_app("purchasing").app.state.evolver.config.conservation_state_provider
    assert provider is not None
    state = provider()
    assert isinstance(state, dict)
    assert "status" in state


@requires_age
def test_dataops_evolver_instantiated() -> None:
    evolver = _load_app("dataops").app.state.evolver
    assert isinstance(evolver, PromptVariantEvolver)


@requires_age
def test_dataops_variants_registered() -> None:
    evolver = _load_app("dataops").app.state.evolver
    variants = evolver.store.get_all_variants()
    assert sum(variant.status == "active" for variant in variants) == 2
    assert sum(variant.status == "shadow" for variant in variants) == 2


@requires_age
def test_dataops_conservation_provider_live() -> None:
    provider = _load_app("dataops").app.state.evolver.config.conservation_state_provider
    assert provider is not None
    state = provider()
    assert isinstance(state, dict)
    assert "status" in state
