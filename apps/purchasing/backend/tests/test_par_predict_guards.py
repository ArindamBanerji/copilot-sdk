"""Failure-boundary coverage for Purchasing predictive PAR endpoints."""

from __future__ import annotations

from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.main import create_app


def _app_client(*, raise_server_exceptions: bool = True) -> tuple[FastAPI, TestClient]:
    app = create_app(db_path=":memory:", demo_bundle_path=False, profile="test")
    return app, TestClient(app, raise_server_exceptions=raise_server_exceptions)


def test_par_predict_invalid_date_returns_422() -> None:
    _app, client = _app_client()

    response = client.get("/api/purchasing/par/predict?date=not-a-date")

    assert response.status_code == 422
    assert "Invalid date format" in response.json()["detail"]


def test_par_predict_graph_failure_returns_503() -> None:
    app, client = _app_client()
    with patch.object(
        app.state.graph_store,
        "get_all_decisions",
        side_effect=ConnectionError("offline"),
    ):
        response = client.get("/api/purchasing/par/predict")

    assert response.status_code == 503
    assert "graph unavailable" in response.json()["detail"].lower()


def test_par_predict_week_graph_failure_returns_503() -> None:
    app, client = _app_client()
    with patch.object(
        app.state.graph_store,
        "get_all_decisions",
        side_effect=ConnectionError("offline"),
    ):
        response = client.get("/api/purchasing/par/predict-week")

    assert response.status_code == 503
    assert "graph unavailable" in response.json()["detail"].lower()


def test_par_predict_programming_error_propagates() -> None:
    app, client = _app_client(raise_server_exceptions=False)
    with patch.object(
        app.state.graph_store,
        "get_all_decisions",
        side_effect=AttributeError("broken"),
    ):
        response = client.get("/api/purchasing/par/predict")

    assert response.status_code == 500

