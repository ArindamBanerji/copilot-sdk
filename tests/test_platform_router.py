from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from copilot_sdk.backend.scorer_proxy import FreshScorerProxy
from copilot_sdk.backend.platform_router import create_platform_router
from copilot_sdk.graph import SQLiteGraphStore
from copilot_sdk.scoring.presets.trading import TradingPreset


class _Scorer:
    """Complete read-only contract fixture for the applicability router."""

    def get_verified_count(self) -> int:
        return 80

    def trajectory(self) -> dict[str, object]:
        return {
            "current_win_rate": 0.572,
            "points": [{"decisions": 0, "win_rate": 0.50}],
        }


def _client() -> TestClient:
    app = FastAPI()
    app.include_router(create_platform_router(_Scorer(), current_domain="trading"), prefix="/api")
    return TestClient(app)


def _graph_store(db_path: str | Path) -> SQLiteGraphStore:
    store = SQLiteGraphStore(str(db_path), domain="trading")
    setattr(store, "penalty_ratio", 2.0)
    return store


def test_domain_applicability_200() -> None:
    assert _client().get("/api/platform/domain-applicability").status_code == 200


def test_domain_applicability_shape() -> None:
    payload = _client().get("/api/platform/domain-applicability").json()
    assert len(payload["domains"]) == 5
    assert payload["platform_summary"]["total_domains"] == 5


def test_domain_applicability_tensor_sizes() -> None:
    domains = _client().get("/api/platform/domain-applicability").json()["domains"]
    assert all(item["tensor_size"] == item["tensor_shape"][0] * item["tensor_shape"][1] * item["tensor_shape"][2] for item in domains)
    trading = next(item for item in domains if item["name"] == "trading")
    assert trading["tensor_shape"] == [5, 4, 10]
    assert trading["tensor_size"] == 200


def test_domain_applicability_exploratory_label() -> None:
    payload = _client().get("/api/platform/domain-applicability").json()
    assert payload["metric_tier"] == "EXPLORATORY"
    assert all(item["metric_tier"] == "EXPLORATORY" for item in payload["domains"])


def test_domain_applicability_summary() -> None:
    payload = _client().get("/api/platform/domain-applicability").json()
    assert payload["platform_summary"]["total_decisions"] == 80
    assert payload["platform_summary"]["mean_compounding_gain_pp"] == 1.44


def test_verified_count_nonzero_from_real_proxy(tmp_path: Path) -> None:
    proxy = FreshScorerProxy(
        "trading",
        tmp_path / "applicability.db",
        _graph_store,
        profile="test",
    )
    preset = TradingPreset()
    factors = {name: 0.5 for name in preset.shape.factor_names}
    result = proxy.score(factors, preset.shape.category_names[0])
    proxy.learn(result.decision_id, result.action)
    app = FastAPI()
    app.include_router(create_platform_router(proxy, current_domain="trading"), prefix="/api")
    payload = TestClient(app).get("/api/platform/domain-applicability").json()
    trading = next(item for item in payload["domains"] if item["name"] == "trading")
    assert trading["verified_decisions"] == 1
    assert payload["platform_summary"]["total_decisions"] == 1


def test_tensor_shapes_per_domain() -> None:
    domains = _client().get("/api/platform/domain-applicability").json()["domains"]
    actual = {item["name"]: (item["tensor_shape"], item["tensor_size"]) for item in domains}
    assert actual == {
        "soc": ([6, 4, 6], 144),
        "dataops": ([6, 5, 6], 180),
        "s2p": ([5, 5, 8], 200),
        "trading": ([5, 4, 10], 200),
        "purchasing": ([5, 4, 7], 140),
    }


def test_dataops_tensor_180() -> None:
    domains = _client().get("/api/platform/domain-applicability").json()["domains"]
    dataops = next(item for item in domains if item["name"] == "dataops")
    assert dataops["tensor_shape"] == [6, 5, 6]
    assert dataops["tensor_size"] == 180


def test_purchasing_tensor_140() -> None:
    domains = _client().get("/api/platform/domain-applicability").json()["domains"]
    purchasing = next(item for item in domains if item["name"] == "purchasing")
    assert purchasing["tensor_shape"] == [5, 4, 7]
    assert purchasing["tensor_size"] == 140
