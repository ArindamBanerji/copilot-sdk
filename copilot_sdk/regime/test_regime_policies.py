"""Focused tests for the shared per-copilot regime policies."""

from __future__ import annotations

import json

from copilot_sdk.regime import (
    DataOpsRegimePolicy,
    PurchasingRegimePolicy,
    RegimeConditioner,
    RegimeDetector,
    S2PRegimePolicy,
)


def test_s2p_normal_and_disrupted() -> None:
    detector = RegimeDetector(S2PRegimePolicy())
    assert detector.detect({"otif": 0.98, "lead_time": 5, "exception_rate": 0.02}).regime == "normal"
    assert detector.detect({"otif": 0.60, "lead_time": 20, "exception_rate": 0.40}).regime == "disrupted"


def test_s2p_seasonal_and_unknown() -> None:
    detector = RegimeDetector(S2PRegimePolicy())
    assert detector.detect({"seasonality": 0.9}).regime == "seasonal"
    assert detector.detect({}).regime == "unknown"


def test_dataops_stable_degraded_disrupted() -> None:
    detector = RegimeDetector(DataOpsRegimePolicy())
    assert detector.detect({"pipeline_success_rate": 0.99, "alert_volume": 1}).regime == "stable"
    assert detector.detect({"pipeline_success_rate": 0.85, "alert_volume": 25}).regime == "degraded"
    assert detector.detect({"pipeline_success_rate": 0.50, "alert_volume": 60}).regime == "disrupted"


def test_purchasing_regimes() -> None:
    detector = RegimeDetector(PurchasingRegimePolicy())
    assert detector.detect({"stock_days": 14, "supply_fill_rate": 0.95}).regime == "balanced"
    assert detector.detect({"stock_days": 3, "supply_fill_rate": 0.70}).regime == "shortage"
    assert detector.detect({"stock_days": 45, "supply_fill_rate": 0.95}).regime == "surplus"
    assert detector.detect({"seasonality": 0.9, "stock_days": 14}).regime == "seasonal"


def test_policies_are_configurable_and_conditioned() -> None:
    policy = PurchasingRegimePolicy(
        thresholds={"shortage_stock_days": 10}, abstention_minimum=2
    )
    state = RegimeDetector(policy).detect({"stock_days": 8})
    assert state.regime == "shortage"
    conditioned = RegimeConditioner(policy).condition(
        {"verified_decisions": [
            {"regime": "shortage", "verified": True, "outcome_correct": True},
            {"regime": "shortage", "verified": True, "outcome_correct": False},
        ]},
        state,
    )
    assert conditioned.regime_scoped_accuracy == 0.5
    assert conditioned.abstention is False
    json.dumps(conditioned.to_dict(), allow_nan=False)
