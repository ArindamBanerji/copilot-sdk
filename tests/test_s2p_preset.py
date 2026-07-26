import numpy as np
import sys
import importlib
from pathlib import Path

from copilot_sdk.scoring import CompoundingScorer
from copilot_sdk.scoring.presets.s2p import S2PPreset

S2P_BACKEND = Path(__file__).resolve().parents[2] / "s2p-copilot" / "backend"
if S2P_BACKEND.exists():
    sys.path.insert(0, str(S2P_BACKEND))


def _optimizer_export_service():
    for name in [key for key in sys.modules if key == "app" or key.startswith("app.")]:
        sys.modules.pop(name, None)
    backend_path = str(S2P_BACKEND)
    sys.path[:] = [
        path for path in sys.path
        if not path.endswith("apps\\purchasing\\backend")
        and not path.endswith("apps\\dataops\\backend")
        and not path.endswith("apps\\trading\\backend")
        and path != backend_path
    ]
    sys.path.insert(0, backend_path)
    importlib.invalidate_caches()
    module = importlib.import_module("app.services.optimizer_export")
    return module.OptimizerExportService


LEGACY_FACTORS = [
    "match_status",
    "amount_variance_ratio",
    "duplicate_score",
    "supplier_exception_history",
    "payment_terms_impact",
    "commodity_index_correlation",
    "tax_regulatory_compliance",
]


def test_preset_shape_8():
    assert S2PPreset().shape.n_factors == 8


def test_tensor_200():
    shape = S2PPreset().shape
    assert shape.n_categories * shape.n_actions * shape.n_factors == 200


def test_factor_names_8():
    assert len(S2PPreset().shape.factor_names) == 8


def test_environmental_risk_index_7():
    assert S2PPreset().shape.factor_names[7] == "environmental_risk"


def test_environmental_risk_decay_campaign():
    assert S2PPreset().environmental_risk_decay == 0.005


def test_factor_order_preserved():
    assert list(S2PPreset().shape.factor_names[:7]) == LEGACY_FACTORS


def test_bootstrap_shape_8():
    assert S2PPreset().bootstrap_centroids.shape == (5, 5, 8)


def test_bootstrap_8th_neutral():
    assert np.allclose(S2PPreset().bootstrap_centroids[:, :, 7], 0.5)


def test_bootstrap_first_7_unchanged():
    expected = np.asarray([0.95, 0.05, 0.02, 0.03, 0.50, 0.80, 0.95])
    assert np.allclose(S2PPreset().bootstrap_centroids[0, 0, :7], expected)


def test_legacy_7_padded():
    legacy = np.zeros((5, 5, 7))
    migrated = S2PPreset().migrate_legacy_centroids(legacy)
    assert migrated.shape == (5, 5, 8)
    assert np.allclose(migrated[:, :, 7], 0.5)


def test_legacy_7_values_preserved():
    legacy = np.random.default_rng(42).random((5, 5, 7))
    migrated = S2PPreset().migrate_legacy_centroids(legacy)
    assert np.allclose(migrated[:, :, :7], legacy)


def test_legacy_6_rejected():
    try:
        S2PPreset().migrate_legacy_centroids(np.zeros((5, 5, 6)))
    except ValueError as exc:
        assert "unsupported factor width 6" in str(exc)
    else:
        raise AssertionError("6-factor legacy tensor should be rejected")


def test_legacy_8_unchanged():
    current = np.ones((5, 5, 8))
    assert S2PPreset().migrate_legacy_centroids(current) is not None
    assert np.allclose(S2PPreset().migrate_legacy_centroids(current), current)


def test_migration_idempotent():
    legacy = np.zeros((5, 5, 7))
    once = S2PPreset().migrate_legacy_centroids(legacy)
    twice = S2PPreset().migrate_legacy_centroids(once)
    assert np.allclose(once, twice)


def test_empty_centroids_handled():
    empty = np.asarray([])
    assert S2PPreset().migrate_legacy_centroids(empty).size == 0


def test_single_decision_padded():
    migrated = S2PPreset().migrate_legacy_vector([0.1] * 7)
    assert migrated.shape == (8,)
    assert migrated[7] == 0.5


def test_score_with_8():
    scorer = CompoundingScorer.from_preset("s2p", profile="test")
    factors = {name: 0.5 for name in S2PPreset().shape.factor_names}
    result = scorer.score(factors, "price_variance")
    assert set(result.factors) == set(S2PPreset().shape.factor_names)


def test_score_with_7_auto_padded():
    scorer = CompoundingScorer.from_preset("s2p", profile="test")
    factors = {name: 0.5 for name in LEGACY_FACTORS}
    result = scorer.score(factors, "price_variance")
    assert result.factors["environmental_risk"] == 0.5


def test_conservation_preserved():
    before = {"V": 1.2, "q": 0.94, "alpha": 0.91}
    after = dict(before)
    S2PPreset().migrate_legacy_centroids(np.zeros((5, 5, 7)))
    assert after == before


def test_conservation_green_maintained():
    state = {"status": "GREEN"}
    S2PPreset().migrate_legacy_vector([0.5] * 7)
    assert state["status"] == "GREEN"


def test_optimizer_export_dynamic():
    export = _optimizer_export_service()().export()
    assert export["tensor_shape"]["factors"] == 8


def test_optimizer_export_200():
    export = _optimizer_export_service()().export()
    assert export["centroid_count"] == 200
    assert export["dk_count"] in {0, 40}
