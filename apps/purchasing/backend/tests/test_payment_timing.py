from app.services.payment_timing import PaymentTimingService


def test_analyze_all_suppliers():
    rows = PaymentTimingService().analyze()

    assert isinstance(rows, list)
    assert len(rows) >= 2


def test_analyze_single_supplier():
    row = PaymentTimingService().analyze("sysco")

    assert isinstance(row, dict)
    assert row["supplier"] == "Sysco"


def test_portfolio_summary_shape():
    summary = PaymentTimingService().portfolio_summary()

    assert {"total_suppliers", "avg_dpo", "total_discount_available", "total_captured", "capture_rate_pct", "annual_opportunity", "provenance"} <= set(summary)


def test_discount_capture_rate():
    rows = PaymentTimingService().analyze()

    assert all(0 <= row["discount_capture_rate"] <= 1 for row in rows)


def test_annual_opportunity_positive():
    assert PaymentTimingService().portfolio_summary()["annual_opportunity"] >= 0


def test_dpo_positive():
    assert PaymentTimingService().portfolio_summary()["avg_dpo"] > 0


def test_recommendation_present():
    rows = PaymentTimingService().analyze()

    assert all(row["recommendation"] for row in rows)


def test_provenance_demo():
    service = PaymentTimingService()

    assert service.portfolio_summary()["provenance"] == "demo"
    assert all(row["provenance"] == "demo" for row in service.analyze())
