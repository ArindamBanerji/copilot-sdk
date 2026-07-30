from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.routers.execution_router import create_execution_router
from app.services.execution_analysis import ExecutionAnalyzer


def test_single_broker():
    comparison = ExecutionAnalyzer().analyze([
        {"broker": "alpaca", "fill_price": 100.10, "mid_price": 100.00, "quantity": 10},
    ])

    assert comparison.best_broker == "alpaca"
    assert comparison.brokers[0].trade_count == 1
    assert round(comparison.brokers[0].avg_slippage, 2) == 0.10


def test_two_brokers_compared():
    comparison = ExecutionAnalyzer().analyze([
        {"broker": "alpaca", "fill_price": 100.10, "mid_price": 100.00, "quantity": 1},
        {"broker": "ibkr", "fill_price": 100.02, "mid_price": 100.00, "quantity": 1},
    ])

    assert comparison.best_broker == "ibkr"


def test_slippage_from_mid():
    comparison = ExecutionAnalyzer().analyze([
        {"broker": "alpaca", "fill_price": 10.25, "mid_price": 10.00, "limit_price": 9.00},
    ])

    assert comparison.brokers[0].avg_slippage == 0.25


def test_slippage_from_limit():
    comparison = ExecutionAnalyzer().analyze([
        {"broker": "alpaca", "fill_price": 10.25, "limit_price": 10.05},
    ])

    assert round(comparison.brokers[0].avg_slippage, 2) == 0.20


def test_slippage_no_reference():
    comparison = ExecutionAnalyzer().analyze([
        {"broker": "alpaca", "fill_price": 10.25},
    ])

    assert comparison.brokers[0].avg_slippage == 0.0


def test_annual_savings():
    comparison = ExecutionAnalyzer().analyze([
        {"broker": "slow", "fill_price": 101.00, "mid_price": 100.00, "quantity": 10},
        {"broker": "fast", "fill_price": 100.50, "mid_price": 100.00, "quantity": 10},
    ])

    assert comparison.best_broker == "fast"
    assert comparison.annual_savings_estimate == 120.0


def test_recommendation_text():
    comparison = ExecutionAnalyzer().analyze([
        {"broker": "slow", "fill_price": 101.00, "mid_price": 100.00, "quantity": 10},
        {"broker": "fast", "fill_price": 100.50, "mid_price": 100.00, "quantity": 10},
    ])

    assert "fast" in comparison.recommendation
    assert "$120" in comparison.recommendation
    assert "estimated from 2 trades over sample period" in comparison.recommendation


def test_empty_trades():
    comparison = ExecutionAnalyzer().analyze([])

    assert comparison.brokers == []
    assert comparison.best_broker == ""


def test_fill_rate():
    rows = [{"broker": "alpaca", "fill_price": 10, "mid_price": 10, "status": "filled"} for _ in range(8)]
    rows.extend({"broker": "alpaca", "status": "canceled"} for _ in range(2))

    comparison = ExecutionAnalyzer().analyze(rows)

    assert comparison.brokers[0].fill_rate == 0.8


def test_median_slippage():
    odd = ExecutionAnalyzer().analyze([
        {"broker": "alpaca", "fill_price": 10.10, "mid_price": 10.00},
        {"broker": "alpaca", "fill_price": 10.20, "mid_price": 10.00},
        {"broker": "alpaca", "fill_price": 10.30, "mid_price": 10.00},
    ])
    even = ExecutionAnalyzer().analyze([
        {"broker": "alpaca", "fill_price": 10.10, "mid_price": 10.00},
        {"broker": "alpaca", "fill_price": 10.30, "mid_price": 10.00},
    ])

    assert round(odd.brokers[0].median_slippage, 2) == 0.20
    assert round(even.brokers[0].median_slippage, 2) == 0.20


def test_execution_with_journal_normalized_records():
    comparison = ExecutionAnalyzer().analyze([
        {
            "entry_price": 100.10,
            "metadata": {
                "broker": "alpaca",
                "mid_price": 100.00,
                "filled_avg_price": 100.10,
            },
        },
        {
            "entry_price": 100.02,
            "metadata": {
                "broker": "ibkr",
                "mid_price": 100.00,
                "filled_avg_price": 100.02,
            },
        },
    ])

    assert comparison.best_broker == "ibkr"
    assert {broker.broker for broker in comparison.brokers} == {"alpaca", "ibkr"}
    assert max(broker.avg_slippage for broker in comparison.brokers) > 0


class _Store:
    def get_all_decisions(self, domain: str):
        assert domain == "trading"
        return [
            {"metadata": {"broker": "alpaca", "fill_price": 100.10, "mid_price": 100.00}},
            {"metadata": {"broker": "ibkr", "fill_price": 100.01, "mid_price": 100.00}},
        ]

    def close(self) -> None:
        return None


def _client() -> TestClient:
    app = FastAPI()
    app.include_router(create_execution_router(lambda: _Store(), domain="trading"))
    return TestClient(app)


def test_router_analysis():
    response = _client().get("/api/trading/execution/analysis")

    assert response.status_code == 200
    assert response.json()["best_broker"] == "ibkr"


def test_router_summary():
    response = _client().get("/api/trading/execution/summary")

    assert response.status_code == 200
    payload = response.json()
    assert payload["best_broker"] == "ibkr"
    assert len(payload["brokers"]) == 2
