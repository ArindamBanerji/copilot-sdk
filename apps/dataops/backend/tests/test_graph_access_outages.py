from __future__ import annotations

from typing import cast
from unittest.mock import patch
from fastapi import FastAPI

import pytest
from fastapi.testclient import TestClient
from psycopg import OperationalError, ProgrammingError

CASES = [
    ("/api/context/pipelines", "get_all_decisions"),
    ("/api/context/transformations/sap_mm", "get_all_decisions"),
    ("/api/context/schema-impact/sap_mm", "get_all_decisions"),
    ("/api/context/process-timeline", "get_all_decisions"),
    ("/api/context/audit-trail/probe", "get_decision"),
    ("/api/context/decisions", "get_all_decisions"),
    ("/api/context/accuracy-by-category", "get_all_decisions"),
]


@pytest.mark.parametrize("path,method", CASES)
def test_context_store_outage_returns_503(client: TestClient, path: str, method: str) -> None:
    app = cast(FastAPI, client.app)
    app.state.materializer.invalidate()
    with patch.object(app.state.graph_store, method, side_effect=OperationalError("AGE lost connection")):
        response = client.get(path)
    assert response.status_code == 503
    assert response.json() == {"detail": "Graph store unavailable"}


@pytest.mark.parametrize("path,method", CASES[:5])
def test_context_missing_store_returns_503(client: TestClient, path: str, method: str) -> None:
    cast(FastAPI, client.app).state.materializer.invalidate()
    with patch.object(cast(FastAPI, client.app).state, "graph_store", None):
        response = client.get(path)
    assert response.status_code == 503


def test_context_programming_error_is_not_hidden(client: TestClient) -> None:
    cast(FastAPI, client.app).state.materializer.invalidate()
    with patch.object(cast(FastAPI, client.app).state.graph_store, "get_all_decisions", side_effect=ProgrammingError("bad SQL")):
        with pytest.raises(ProgrammingError):
            client.get("/api/context/pipelines")
