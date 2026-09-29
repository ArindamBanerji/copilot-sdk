from __future__ import annotations

from typing import cast
from unittest.mock import patch
from fastapi import FastAPI

from fastapi.testclient import TestClient
from psycopg import OperationalError


def test_health_aliases_have_one_handler_and_matching_graph_fields(client: TestClient) -> None:
    for path in ("/health", "/api/health"):
        routes = [r for r in cast(FastAPI, client.app).routes if getattr(r, "path", None) == path
                  and "GET" in (getattr(r, "methods", None) or set())]
        assert len(routes) == 1
    root = client.get("/health").json()
    api = client.get("/api/health").json()
    for key in ("ready", "graph_backend", "graph_connected", "node_count", "node_count_scope"):
        assert root[key] == api[key]
    assert root["graph_backend"] == "sqlite"
    assert root["graph_connected"] is True
    assert root["ready"] is False


def test_health_aliases_survive_store_outage(client: TestClient) -> None:
    with patch.object(cast(FastAPI, client.app).state.graph_store, "count_decisions", side_effect=OperationalError("offline")):
        for path in ("/health", "/api/health"):
            response = client.get(path)
            assert response.status_code == 503
            assert response.json()["graph_connected"] is False
            assert response.json()["node_count"] is None
