from __future__ import annotations

import numpy as np
from fastapi.testclient import TestClient
import sys
from pathlib import Path

from copilot_sdk.transfer.chain_transfer import ChainTransfer, LocationStore
from copilot_sdk.scoring.presets.purchasing import PurchasingPreset

PURCHASING_BACKEND = Path(__file__).resolve().parents[1] / "apps" / "purchasing" / "backend"


CATEGORIES = ["protein", "produce"]
ACTIONS = ["order_as_planned", "order_more"]


def _store(**overrides):
    data = {
        "location_id": "Chicago",
        "decisions": 250,
        "accuracy": 0.85,
        "conservation": "GREEN",
        "categories": CATEGORIES,
        "actions": ACTIONS,
        "pattern_grid": np.ones((2, 2, 3), dtype=float),
        "dk_weights": {"supplier": 0.3},
    }
    data.update(overrides)
    return LocationStore(**data)


def test_validate_source_green():
    assert ChainTransfer().validate(_store(), _store(location_id="Miami", decisions=0))["valid"] is True


def test_validate_source_red():
    assert ChainTransfer().validate(_store(conservation="RED"), _store(location_id="Miami"))["valid"] is False


def test_validate_insufficient():
    assert ChainTransfer().validate(_store(decisions=50), _store(location_id="Miami"))["valid"] is False


def test_validate_different_presets():
    target = _store(location_id="Miami", categories=["produce"], pattern_grid=np.ones((1, 2, 3)))
    assert ChainTransfer().validate(_store(), target)["valid"] is False


def test_validate_target_has_data():
    result = ChainTransfer().validate(_store(), _store(location_id="Miami", decisions=75))
    assert result["valid"] is True
    assert result["warnings"]


def test_transfer_copies_centroids():
    source = _store(pattern_grid=np.ones((2, 2, 3)) * 0.8)
    target = _store(location_id="Miami", decisions=0, pattern_grid=np.zeros((2, 2, 3)))
    ChainTransfer().transfer(source, target)
    assert np.allclose(target.pattern_grid, source.pattern_grid)


def test_transfer_sets_not_adds():
    source = _store(pattern_grid=np.ones((2, 2, 3)) * 0.72)
    target = _store(location_id="Miami", decisions=0, pattern_grid=np.ones((2, 2, 3)) * 0.50)
    ChainTransfer().transfer(source, target)
    assert np.allclose(target.pattern_grid, 0.72)
    assert not np.allclose(target.pattern_grid, 1.22)


def test_transfer_target_centroids_equal_source():
    source = _store(pattern_grid=np.ones((2, 2, 3)) * 0.77)
    target = _store(location_id="Miami", decisions=0, pattern_grid=np.ones((2, 2, 3)) * 0.33)
    ChainTransfer().transfer(source, target)
    assert np.allclose(target.pattern_grid, source.pattern_grid)


def test_transfer_preserves_source():
    source = _store(pattern_grid=np.ones((2, 2, 3)) * 0.81)
    before = np.array(source.pattern_grid, copy=True)
    target = _store(location_id="Miami", decisions=0, pattern_grid=np.ones((2, 2, 3)) * 0.20)
    ChainTransfer().transfer(source, target)
    assert np.allclose(source.pattern_grid, before)


def test_transfer_non_zero_target_overwritten():
    source = _store(pattern_grid=np.ones((2, 2, 3)) * 0.8)
    target = _store(location_id="Miami", decisions=0, pattern_grid=np.ones((2, 2, 3)) * 0.6)
    ChainTransfer().transfer(source, target)
    assert np.allclose(target.pattern_grid, 0.8)


def test_transfer_resets_conservation():
    target = _store(location_id="Miami", decisions=0)
    ChainTransfer().transfer(_store(), target)
    assert target.conservation_v == 0


def test_dk_never_transferred():
    source = _store(dk_weights={"supplier": 0.9})
    target = _store(location_id="Miami", decisions=0, dk_weights={"supplier": 0.1})
    ChainTransfer().transfer(source, target)
    assert target.dk_weights["supplier"] == 0.1


def test_dry_run_no_changes():
    target = _store(location_id="Miami", decisions=0, pattern_grid=np.zeros((2, 2, 3)))
    ChainTransfer().transfer(_store(), target, dry_run=True)
    assert np.allclose(target.pattern_grid, 0)


def test_estimate_accuracy():
    assert ChainTransfer().estimate_accuracy(0.85) == 0.722


def test_estimate_floor():
    assert ChainTransfer().estimate_accuracy(0.40) == 0.50


def test_transfer_logged():
    source = _store()
    target = _store(location_id="Miami", decisions=0)
    ChainTransfer().transfer(source, target)
    assert source.log
    assert target.log


def test_uses_warm_start(monkeypatch):
    called = []

    def fake_warm_start(current, patterns, category_names, action_names, blend_weight=1.0):
        called.append({
            "patterns": patterns,
            "categories": category_names,
            "actions": action_names,
            "blend_weight": blend_weight,
        })
        return np.asarray(current), 1.0

    monkeypatch.setattr("copilot_sdk.transfer.chain_transfer.warm_start_func", fake_warm_start)
    result = ChainTransfer().transfer(_store(), _store(location_id="Miami", decisions=0), dry_run=True)
    assert result["transferred"] is True
    assert called


def test_provenance_demo():
    result = ChainTransfer().transfer(_store(), _store(location_id="Miami", decisions=0), dry_run=True)
    assert result["provenance"] == "demo"


def test_validate_shape_mismatch():
    target = _store(location_id="Miami", pattern_grid=np.ones((2, 2, 2)))
    assert ChainTransfer().validate(_store(), target)["valid"] is False


def test_validate_factor_count_mismatch():
    target = _store(location_id="Miami", pattern_grid=np.ones((2, 2, 4)))
    assert ChainTransfer().validate(_store(), target)["valid"] is False


def test_validate_shape_match_passes():
    assert ChainTransfer().validate(_store(), _store(location_id="Miami", decisions=0))["valid"] is True


def test_demo_grids_match_purchasing_preset():
    create_app = _purchasing_create_app()
    try:
        from app.routers.chain_router import create_demo_chain_stores

        preset = PurchasingPreset()
        expected = (preset.shape.n_categories, preset.shape.n_actions, preset.shape.n_factors)
        stores = create_demo_chain_stores()
        assert stores["chicago"].shape == expected
        assert stores["miami"].shape == expected
    finally:
        _clear_app_modules()


def test_router_validate():
    create_app = _purchasing_create_app()
    try:
        client = TestClient(create_app(db_path=":memory:", demo_bundle_path=False))
        response = client.post("/api/purchasing/chain/validate", json={"source": "chicago", "target": "miami"})
        assert response.status_code == 200
        assert "valid" in response.json()
    finally:
        _clear_app_modules()


def test_router_uses_request_payload():
    create_app = _purchasing_create_app()
    try:
        client = TestClient(create_app(db_path=":memory:", demo_bundle_path=False))
        response = client.post("/api/purchasing/chain/validate", json={"source": "miami", "target": "chicago"})
        assert response.status_code == 200
        data = response.json()
        assert data["source_location"] == "Miami"
        assert data["target_location"] == "Chicago"
        assert data["valid"] is False
    finally:
        _clear_app_modules()


def test_router_rejects_unknown_location():
    create_app = _purchasing_create_app()
    try:
        client = TestClient(create_app(db_path=":memory:", demo_bundle_path=False))
        response = client.post("/api/purchasing/chain/validate", json={"source": "nonexistent", "target": "miami"})
        assert response.status_code == 404
    finally:
        _clear_app_modules()


def test_router_validate_returns_location_names():
    create_app = _purchasing_create_app()
    try:
        client = TestClient(create_app(db_path=":memory:", demo_bundle_path=False))
        response = client.post("/api/purchasing/chain/validate", json={"source": "chicago", "target": "miami"})
        data = response.json()
        assert data["source_location"] == "Chicago"
        assert data["target_location"] == "Miami"
    finally:
        _clear_app_modules()


def test_router_transfer_dry_run():
    create_app = _purchasing_create_app()
    try:
        client = TestClient(create_app(db_path=":memory:", demo_bundle_path=False))
        response = client.post("/api/purchasing/chain/transfer", json={"source": "chicago", "target": "miami", "dry_run": True})
        assert response.status_code == 200
        assert response.json()["dry_run"] is True
    finally:
        _clear_app_modules()


def test_chain_state_resets():
    create_app = _purchasing_create_app()
    try:
        with TestClient(create_app(db_path=":memory:", demo_bundle_path=False)) as client:
            response = client.post("/api/purchasing/chain/transfer", json={"source": "chicago", "target": "miami", "dry_run": False})
            assert response.status_code == 200
            assert client.app.state.purchasing_chain_stores["miami"].log
            reset = client.post("/api/purchasing/demo/reset")
            assert reset.status_code == 200
            assert client.app.state.purchasing_chain_stores["miami"].log == []
    finally:
        _clear_app_modules()


def test_chain_status_empty_after_reset():
    create_app = _purchasing_create_app()
    try:
        with TestClient(create_app(db_path=":memory:", demo_bundle_path=False)) as client:
            client.post("/api/purchasing/chain/transfer", json={"source": "chicago", "target": "miami", "dry_run": False})
            client.post("/api/purchasing/demo/reset")
            status = client.get("/api/purchasing/chain/status").json()
            assert status["target"]["decisions"] == 0
            assert status["target"]["accuracy"] == 0.5
    finally:
        _clear_app_modules()


def test_double_transfer_idempotent():
    source = _store(pattern_grid=np.ones((2, 2, 3)) * 0.72)
    target = _store(location_id="Miami", decisions=0, pattern_grid=np.ones((2, 2, 3)) * 0.50)
    ChainTransfer().transfer(source, target)
    first = np.array(target.pattern_grid, copy=True)
    ChainTransfer().transfer(source, target)
    assert np.allclose(target.pattern_grid, first)


def test_transfer_history_cleared_on_reset():
    create_app = _purchasing_create_app()
    try:
        with TestClient(create_app(db_path=":memory:", demo_bundle_path=False)) as client:
            client.post("/api/purchasing/chain/transfer", json={"source": "chicago", "target": "miami", "dry_run": False})
            assert client.app.state.purchasing_chain_stores["chicago"].log
            client.post("/api/purchasing/demo/reset")
            assert client.app.state.purchasing_chain_stores["chicago"].log == []
    finally:
        _clear_app_modules()


def _purchasing_create_app():
    _clear_app_modules()
    if str(PURCHASING_BACKEND) not in sys.path:
        sys.path.insert(0, str(PURCHASING_BACKEND))
    from app.main import create_app

    return create_app


def _clear_app_modules() -> None:
    for name in list(sys.modules):
        if name == "app" or name.startswith("app."):
            sys.modules.pop(name, None)
