"""Regression coverage for live prompt-variant evolution wiring."""

from __future__ import annotations

from pathlib import Path

from copilot_sdk.evolution import PromptVariantEvolver
from tests.evolution_contract_helpers import make_contract_app


ROOT = Path(__file__).resolve().parents[1]


def _evolver(copilot: str) -> PromptVariantEvolver:
    app = make_contract_app(copilot)
    evolver = app.state.evolver
    assert isinstance(evolver, PromptVariantEvolver)
    return evolver


def test_purchasing_evolver_instantiated() -> None:
    assert isinstance(_evolver("purchasing"), PromptVariantEvolver)


def test_purchasing_variants_registered() -> None:
    evolver = _evolver("purchasing")
    variants = evolver.store.get_all_variants()
    assert sum(variant.status == "active" for variant in variants) == 1
    assert sum(variant.status == "shadow" for variant in variants) == 1


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
    assert sum(variant.status == "active" for variant in variants) == 1
    assert sum(variant.status == "shadow" for variant in variants) == 1


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
