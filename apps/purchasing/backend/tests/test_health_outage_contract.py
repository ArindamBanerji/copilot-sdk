from __future__ import annotations

from typing import cast
from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient
from psycopg import OperationalError


def test_health_aliases_report_actual_store_and_node_count(client: TestClient) -> None:
    for path in ("/health", "/api/health"):
        payload = client.get(path).json()
        assert payload["graph_backend"] == "sqlite"
        assert payload["graph_connected"] is True
        assert isinstance(payload["node_count"], int)
        assert payload["ready"] is False


def test_health_aliases_survive_graph_outage(client: TestClient) -> None:
    app = cast(FastAPI, client.app)
    with patch.object(app.state.graph_store, "count_decisions", side_effect=OperationalError("lost")):
        for path in ("/health", "/api/health"):
            response = client.get(path)
            assert response.status_code == 503
            assert response.json()["graph_connected"] is False
            assert response.json()["node_count"] is None
