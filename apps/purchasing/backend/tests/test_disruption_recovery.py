from app.services.disruption_recovery import DisruptionRecoveryService


def test_recovery_status_shape():
    status = DisruptionRecoveryService().recovery_status()

    assert {"status", "days_since_disruption", "categories_affected", "gamma", "re_calibration_progress_pct", "estimated_days_to_green", "provenance"} <= set(status)


def test_gamma_above_one():
    assert DisruptionRecoveryService().recovery_status()["gamma"] > 1.0


def test_normal_gamma_one():
    assert DisruptionRecoveryService(active=False).recovery_status()["gamma"] == 1.0


def test_trigger_sets_category():
    status = DisruptionRecoveryService(active=False).trigger_disruption("dairy")

    assert "dairy" in status["categories_affected"]


def test_recovery_progress():
    progress = DisruptionRecoveryService().recovery_status()["re_calibration_progress_pct"]

    assert 0 <= progress <= 100


def test_estimated_days():
    assert isinstance(DisruptionRecoveryService().recovery_status()["estimated_days_to_green"], int)
    assert DisruptionRecoveryService().recovery_status()["estimated_days_to_green"] >= 0


def test_recovery_history():
    history = DisruptionRecoveryService().recovery_history()

    assert isinstance(history, list)
    assert history


def test_provenance_demo():
    service = DisruptionRecoveryService()

    assert service.recovery_status()["provenance"] == "demo"
    assert all(row["provenance"] == "demo" for row in service.recovery_history())
