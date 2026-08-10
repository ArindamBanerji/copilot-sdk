"""Regression coverage for live prompt-variant evolution wiring."""

from __future__ import annotations

import importlib
import sys
from pathlib import Path
from types import ModuleType

from copilot_sdk.evolution import PromptVariantEvolver


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


def _evolver(copilot: str) -> PromptVariantEvolver:
    app_module = _load_app(copilot)
    evolver = app_module.app.state.evolver
    assert isinstance(evolver, PromptVariantEvolver)
    return evolver


def test_purchasing_evolver_instantiated() -> None:
    assert isinstance(_evolver("purchasing"), PromptVariantEvolver)


def test_purchasing_variants_registered() -> None:
    evolver = _evolver("purchasing")
    variants = evolver.store.get_all_variants()
    assert sum(variant.status == "active" for variant in variants) == 6
    assert sum(variant.status == "shadow" for variant in variants) == 6


def test_purchasing_conservation_provider_live() -> None:
    provider = _evolver("purchasing").config.conservation_state_provider
    assert provider is not None
    state = provider()
    assert isinstance(state, dict)
    assert "status" in state


def test_dataops_evolver_instantiated() -> None:
    assert isinstance(_evolver("dataops"), PromptVariantEvolver)


def test_dataops_variants_registered() -> None:
    evolver = _evolver("dataops")
    variants = evolver.store.get_all_variants()
    assert sum(variant.status == "active" for variant in variants) == 2
    assert sum(variant.status == "shadow" for variant in variants) == 2


def test_dataops_conservation_provider_live() -> None:
    provider = _evolver("dataops").config.conservation_state_provider
    assert provider is not None
    state = provider()
    assert isinstance(state, dict)
    assert "status" in state


def test_no_literal_green_in_purchasing() -> None:
    source_files = (ROOT / "apps" / "purchasing").rglob("*.py")
    source = "\n".join(path.read_text(encoding="utf-8") for path in source_files)
    assert 'conservation_state="GREEN"' not in source


def test_no_literal_green_in_dataops() -> None:
    source_files = (ROOT / "apps" / "dataops").rglob("*.py")
    source = "\n".join(path.read_text(encoding="utf-8") for path in source_files)
    assert 'conservation_state="GREEN"' not in source
