from __future__ import annotations

import builtins
import math
import os
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

from copilot_sdk.generators.archetype import ArchetypeGenerator
from copilot_sdk.graph import InMemoryGraphStore
from copilot_sdk.scoring.presets import PRESET_REGISTRY
from copilot_sdk.scoring.scorer import CompoundingScorer
from copilot_sdk.scoring.storage import DecisionStore

GAE_PATH = Path(__file__).resolve().parents[2] / "graph-attention-engine-v50"
if str(GAE_PATH) not in sys.path:
    sys.path.insert(0, str(GAE_PATH))

profile_module = pytest.importorskip("gae.profile_scorer")
ProfileScorer = profile_module.ProfileScorer


def test_from_archetype_soc_produces_valid_config():
    preset = ArchetypeGenerator.from_archetype("security_operations")

    assert preset.name == "security_operations"
    assert preset.shape.n_categories == 6
    assert preset.shape.n_actions == 4
    assert preset.shape.n_factors == 6
    assert preset.penalty_ratio == 20.0
    assert preset.bootstrap_centroids.shape == (6, 4, 6)
    assert "credential_access" in preset.shape.category_names


def test_from_archetype_financial_services_shape():
    preset = ArchetypeGenerator.from_archetype("financial_services")

    assert preset.shape.n_categories == 5
    assert preset.shape.n_actions == 4
    assert preset.shape.n_factors == 6
    assert preset.penalty_ratio == 8.0
    assert "transaction_anomaly" in preset.shape.category_names
    assert "flag_review" in preset.shape.action_names
    assert "counterparty_risk" in preset.shape.factor_names


def test_from_archetype_applies_overrides():
    preset = ArchetypeGenerator.from_archetype(
        "financial_services",
        overrides={
            "penalty_ratio": 9.5,
            "categories": ["fraud", "credit"],
            "factors": ["amount", "velocity", "risk"],
        },
    )

    assert preset.penalty_ratio == 9.5
    assert preset.shape.category_names == ("fraud", "credit")
    assert preset.shape.factor_names == ("amount", "velocity", "risk")
    assert preset.bootstrap_centroids.shape == (2, 4, 3)
    assert preset.plateau_config is not None
    assert preset.plateau_config.plateau_window == round(10 * math.sqrt((2 * 4) / 20))


def test_override_categories_reject_non_string_names():
    with pytest.raises(ValueError, match="categories.*strings"):
        ArchetypeGenerator.from_archetype(
            "financial_services",
            overrides={"categories": ["valid", 123]},
        )


def test_override_actions_reject_none_name():
    with pytest.raises(ValueError, match="actions.*strings"):
        ArchetypeGenerator.from_archetype(
            "financial_services",
            overrides={"actions": ["approve", None]},
        )


def test_override_factors_reject_blank_name():
    with pytest.raises(ValueError, match="factors.*non-empty"):
        ArchetypeGenerator.from_archetype(
            "financial_services",
            overrides={"factors": ["risk", "   "]},
        )


def test_override_names_reject_duplicates_after_stripping():
    with pytest.raises(ValueError, match="duplicates"):
        ArchetypeGenerator.from_archetype(
            "financial_services",
            overrides={"categories": ["risk", " risk "]},
        )


def test_override_rejects_unsupported_keys():
    with pytest.raises(ValueError, match="unknown_key"):
        ArchetypeGenerator.from_archetype(
            "financial_services",
            overrides={"unknown_key": "value"},
        )


def test_from_description_matches_nearest():
    security = ArchetypeGenerator.from_description(
        "Investigate credential access, lateral movement, malware command and control, "
        "privilege escalation, endpoint telemetry, and data exfiltration risk."
    )
    procurement = ArchetypeGenerator.from_description(
        "Review invoices, purchase orders, suppliers, duplicate invoice exceptions, "
        "price variance, quantity mismatch, contract gaps, and payment terms."
    )
    dataops = ArchetypeGenerator.from_description(
        "Monitor pipeline failures, schema changes, data quality incidents, access "
        "anomalies, performance degradation, freshness, and configuration drift."
    )

    assert security.name == "security_operations"
    assert procurement.name == "source_to_pay"
    assert dataops.name == "dataops"


def test_from_description_uses_token_fallback_when_sklearn_unavailable(monkeypatch):
    real_import = builtins.__import__

    def blocked_sklearn_import(name, *args, **kwargs):
        if name == "sklearn" or name.startswith("sklearn."):
            raise ImportError("blocked sklearn for fallback test")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", blocked_sklearn_import)

    preset = ArchetypeGenerator.from_description(
        "Investigate credential access, lateral movement, malware command and control, "
        "privilege escalation, endpoint telemetry, and data exfiltration risk."
    )

    assert preset.name == "security_operations"


def test_from_description_empty_raises():
    with pytest.raises(ValueError, match="non-empty"):
        ArchetypeGenerator.from_description("  ")


def test_from_archetype_unknown_raises():
    with pytest.raises(ValueError, match="not_real"):
        ArchetypeGenerator.from_archetype("not_real")


def test_generated_config_constructs_scorer(tmp_path):
    preset = ArchetypeGenerator.from_archetype("dataops")
    store = DecisionStore(tmp_path / "generated.sqlite")
    graph_store = InMemoryGraphStore()
    scorer = ProfileScorer(
        mu=preset.bootstrap_centroids.copy(),
        actions=list(preset.shape.action_names),
        categories=list(preset.shape.category_names),
    )
    try:
        wrapper = CompoundingScorer(
            preset,
            store,
            scorer,
            graph_store=graph_store,
        )
        assert wrapper._preset is preset
        assert wrapper._graph_store is graph_store
    finally:
        store.close()


def test_plateau_follows_cells_formula():
    for name in ArchetypeGenerator.list_archetypes():
        preset = ArchetypeGenerator.from_archetype(name)
        config = preset.plateau_config
        assert config is not None
        cells = preset.shape.n_categories * preset.shape.n_actions
        expected_window = round(10 * math.sqrt(cells / 20))
        assert config.plateau_window == expected_window
        assert config.plateau_cooldown == expected_window * 5
        assert config.min_improvement_rate == 0.20


def test_centroid_shape_matches_dimensions():
    for name in ArchetypeGenerator.list_archetypes():
        preset = ArchetypeGenerator.from_archetype(name)
        assert preset.bootstrap_centroids.shape == (
            len(preset.shape.category_names),
            len(preset.shape.action_names),
            len(preset.shape.factor_names),
        )


def test_no_preset_registry_mutation():
    before = set(PRESET_REGISTRY)

    ArchetypeGenerator.from_archetype("security_operations")
    ArchetypeGenerator.from_description("Invoice supplier duplicate payment price variance review.")

    assert set(PRESET_REGISTRY) == before


def test_centroids_are_deterministic_across_calls():
    first = ArchetypeGenerator.from_archetype(
        "source_to_pay",
        overrides={"penalty_ratio": 6.0},
    ).bootstrap_centroids
    second = ArchetypeGenerator.from_archetype(
        "source_to_pay",
        overrides={"penalty_ratio": 6.0},
    ).bootstrap_centroids

    assert np.array_equal(first, second)


def test_sklearn_lazy_import_not_on_module_import():
    code = (
        "import sys; "
        "sys.path.insert(0, '.'); "
        "import copilot_sdk.generators.archetype; "
        "assert 'sklearn' not in sys.modules, 'sklearn loaded on module import'; "
        "print('lazy import ok')"
    )
    result = subprocess.run(
        [sys.executable, "-c", code],
        cwd=Path(__file__).resolve().parents[1],
        env={**os.environ, "PYTHONPATH": "."},
        capture_output=True,
        text=True,
        timeout=30,
    )

    assert result.returncode == 0, result.stdout + result.stderr
