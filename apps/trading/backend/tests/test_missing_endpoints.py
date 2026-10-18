from __future__ import annotations

from collections.abc import Iterator

import pytest

from app.routers.data_import import _trade_store_ref


@pytest.fixture(autouse=True)
def seeded_trade() -> Iterator[None]:
    _trade_store_ref.clear()
    _trade_store_ref.append(
        {
            "trade_id": "TRADE-001",
            "ticker": "MSFT",
            "direction": "long",
            "category": "trend_following",
            "strategy_tag": "momentum",
            "action": "strong_execution",
            "confidence": 0.82,
            "factors": {"signal_alignment": 0.9},
            "metadata": {
                "probabilities": {
                    "strong_execution": 0.7,
                    "partial_execution": 0.2,
                    "poor_execution": 0.08,
                    "skip_recommended": 0.02,
                },
            },
        }
    )
    yield
    _trade_store_ref.clear()


def test_trade_detail_contract_and_unknown_default(client) -> None:
    response = client.get("/api/trading/trades/TRADE-001")
    unknown = client.get("/api/trading/trades/UNKNOWN")

    assert response.status_code == unknown.status_code == 200
    assert response.json()["trade_id"] == "TRADE-001"
    assert response.json()["ticker"] == "MSFT"
    assert unknown.json() == {
        "trade_id": "UNKNOWN",
        "ticker": None,
        "direction": None,
        "entry_price": None,
        "exit_price": None,
        "size": None,
        "entry_time": None,
        "exit_time": None,
        "strategy_tag": None,
        "category": None,
        "regime": None,
        "pnl": None,
        "factors": {},
        "options_factors": {},
        "options_analytics_only": False,
        "action": None,
        "confidence": None,
        "metadata": {},
    }


def test_evidence_contract_and_unknown_default(client) -> None:
    response = client.get("/api/trading/evidence/TRADE-001")
    unknown = client.get("/api/trading/evidence/UNKNOWN")

    assert response.status_code == unknown.status_code == 200
    assert {
        "trade_id",
        "evidence_text",
        "factor_breakdown",
        "factors",
        "factor_scores",
        "similar_trades",
        "counterfactual",
        "action",
        "confidence",
    } <= response.json().keys()
    assert response.json()["counterfactual"] == {
        "alternate_action": "partial_execution",
        "projected_score": 0.2,
        "delta": -0.5,
    }
    assert unknown.json()["trade_id"] == "UNKNOWN"
    assert unknown.json()["factors"] == []
    assert unknown.json()["similar_trades"] == []


def test_promotion_detail_contract_and_unknown_default(client) -> None:
    response = client.get("/api/trading/promotion/trend_following")
    unknown = client.get("/api/trading/promotion/unknown")

    assert response.status_code == unknown.status_code == 200
    expected = {
        "category",
        "current_stage",
        "current_stage_label",
        "next_stage",
        "next_stage_label",
        "ready",
        "evidence",
        "recommendation",
        "blockers",
        "max_sizing_pct",
        "state",
    }
    assert expected <= response.json().keys()
    assert response.json()["category"] == "trend_following"
    assert expected <= unknown.json().keys()
    assert unknown.json()["category"] == "unknown"


def test_archetype_detail_contract_and_unknown_default(client) -> None:
    response = client.get("/api/archetypes/financial_services")
    unknown = client.get("/api/archetypes/researcher")

    assert response.status_code == unknown.status_code == 200
    expected = {
        "name",
        "domain",
        "description",
        "expected_initial_accuracy",
        "categories",
        "actions",
        "factors",
        "shape",
        "centroids",
        "penalty_ratio",
        "calibration_note",
        "calibration_notes",
    }
    assert expected <= response.json().keys()
    assert expected <= unknown.json().keys()
    assert unknown.json()["name"] == "researcher"
