from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import create_app
from app.services.economic_model import PurchasingEconomicModel, demo_cost_impacts, unlock_range_totals


def test_compute_basic():
    result = PurchasingEconomicModel().compute(100)
    assert result.projected_savings == 960.0


def test_benchmark_tiers():
    assert PurchasingEconomicModel("food_service_small")._benchmark == 8.0
    assert PurchasingEconomicModel("food_service_medium")._benchmark == 12.0
    assert PurchasingEconomicModel("food_service_large")._benchmark == 15.0


def test_conservative_factor():
    result = PurchasingEconomicModel("food_service_small").compute(10, [])
    assert result.projected_savings == 64.0


def test_actual_vs_projected():
    result = PurchasingEconomicModel().compute(10, [{"dollars_found": 120.0}])
    assert result.actual_savings == 120.0
    assert result.attainment_pct == 125.0


def test_sources_breakdown():
    result = PurchasingEconomicModel().compute(10, [{"dollars_found": 100.0}])
    assert result.sources["waste_reduction"] == 35.0
    assert result.sources["supplier_consolidation"] == 15.0


def test_project_forward_12():
    projection = PurchasingEconomicModel().project_forward(1000, months=12)
    assert len(projection) == 12
    assert projection[-1]["projected_savings"] == 9600.0


def test_roi_summary_kitchen():
    service = PurchasingEconomicModel()
    summary = service.roi_summary(service.compute(1000, demo_cost_impacts()))
    assert "Year 1" in summary
    assert "centroid" not in summary.lower()
    assert "sigma" not in summary.lower()


def test_empty_decisions():
    result = PurchasingEconomicModel().compute(0, [])
    assert result.projected_savings == 0
    assert result.actual_savings == 0


def test_cost_impacts_merged():
    result = PurchasingEconomicModel().compute(10, [{"dollars_found": 10, "stockout_prevention": 20, "supplier_consolidation": 30}])
    assert result.actual_savings == 60


def test_pd_small_tier_alignment():
    assert PurchasingEconomicModel("food_service_small").annual_benchmark() == 34000


def test_pd_medium_tier_alignment():
    assert PurchasingEconomicModel("food_service_medium").annual_benchmark() == 144000


def test_pd_large_tier_alignment():
    assert PurchasingEconomicModel("food_service_large").annual_benchmark() == 229000


def test_unlock_categories():
    result = PurchasingEconomicModel().compute(10, [{"dollars_found": 100.0}])
    assert len(result.unlocks) == 13


def test_weekly_report_format():
    result = PurchasingEconomicModel().compute(10, demo_cost_impacts())
    assert "found $" in str(result.weekly_report["summary"])
    assert "Prevented $" in str(result.weekly_report["summary"])
    assert "Flagged $" in str(result.weekly_report["summary"])


def test_router_model():
    client = TestClient(create_app(db_path=":memory:", demo_bundle_path=False))
    response = client.get("/api/purchasing/economic/model")
    assert response.status_code == 200
    data = response.json()
    assert data["tier"] == "food_service_medium"
    assert data["annual_benchmark"] == 144000


def test_consumes_waste_tracker():
    class Waste:
        def weekly_waste_cost(self):
            return {"prevented_this_week": 100}

    result = PurchasingEconomicModel(waste_tracker=Waste()).compute(10, [])
    assert result.actual_savings >= 100
    assert result.provenance == "live"


def test_consumes_par_optimizer():
    class Rec:
        weekly_savings_estimate = 25

    class Par:
        def recommend_all(self, items, orders):
            return [Rec()]

    result = PurchasingEconomicModel(par_optimizer=Par()).compute(10, [])
    assert result.actual_savings >= 1300
    assert result.provenance == "live"


def test_demo_fallback_labeled():
    result = PurchasingEconomicModel().compute(10, [])
    assert result.provenance == "demo"


def test_live_provenance():
    result = PurchasingEconomicModel(cost_impact_source={"dollars_found": 10}).compute(10, [])
    assert result.provenance == "live"


def test_roi_small_tier():
    result = PurchasingEconomicModel("food_service_small").compute(1000, [])
    assert 21.0 <= result.roi_multiple <= 22.0


def test_roi_medium_tier():
    result = PurchasingEconomicModel("food_service_medium").compute(1000, [])
    assert 29.0 <= result.roi_multiple <= 31.0


def test_roi_large_tier():
    result = PurchasingEconomicModel("food_service_large").compute(1000, [])
    assert 46.0 <= result.roi_multiple <= 47.0


def test_roi_math_matches_pd():
    service = PurchasingEconomicModel()
    assert round(service.compute_roi(129000), 1) == 21.5
    assert round(service.compute_roi(277000), 1) == 46.3


def test_unlock_ranges_match_pd():
    assert unlock_range_totals() == (129000.0, 277000.0)
