from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from psycopg import OperationalError, ProgrammingError

from copilot_sdk.backend.scoring_router import ENGINE, create_scoring_router
from copilot_sdk.graph import InMemoryGraphStore


def client_for(scorer: SimpleNamespace, domain: str) -> TestClient:
    app = FastAPI()
    app.include_router(create_scoring_router(domain, scorer_factory=lambda: scorer))
    return TestClient(app)


@pytest.mark.parametrize("domain", ["trading", "purchasing", "dataops", "s2p"])
def test_history_outage_and_unchanged_recovery(domain: str) -> None:
    store = InMemoryGraphStore(domain=domain)
    store.write_decision(domain, "category", "action", 0.6, {"signal": 0.4})
    scorer = SimpleNamespace(graph_store=store)
    with client_for(scorer, domain) as client:
        before = client.get("/history")
        assert before.status_code == 200
        assert before.json() == {"engine": ENGINE, "decisions": store.get_decisions(domain, limit=10**12)}
        with patch.object(store, "get_decisions", side_effect=OperationalError("lost connection")):
            response = client.get("/history")
            assert response.status_code == 503
            assert response.json() == {"detail": "Graph store unavailable"}
        assert client.get("/history").json() == before.json()


@pytest.mark.parametrize("path,method", [
    ("/fingerprint", "fingerprint"), ("/trajectory", "trajectory"),
    ("/health", "get_phase"), ("/health", "get_alpha"),
])
def test_derived_scoring_reads_translate_outages(path: str, method: str) -> None:
    scorer = SimpleNamespace(graph_store=InMemoryGraphStore(domain="dataops"),
                             fingerprint=Mock(), trajectory=Mock(),
                             get_phase=Mock(return_value="A"), get_alpha=Mock(return_value=0.5))
    setattr(scorer, method, Mock(side_effect=OperationalError("connection lost")))
    with client_for(scorer, "dataops") as client:
        assert client.get(path).status_code == 503


@pytest.mark.parametrize("path", ["/measurement-state", "/dataops/measurement-state"])
def test_measurement_store_outage(path: str) -> None:
    store = InMemoryGraphStore(domain="dataops")
    with patch.object(store, "get_verified_decisions", side_effect=OperationalError("offline")):
        with client_for(SimpleNamespace(graph_store=store), "dataops") as client:
            assert client.get(path).status_code == 503


def test_history_does_not_translate_programming_errors() -> None:
    store = InMemoryGraphStore(domain="dataops")
    with patch.object(store, "get_decisions", side_effect=ProgrammingError("invalid SQL")):
        with client_for(SimpleNamespace(graph_store=store), "dataops") as client:
            with pytest.raises(ProgrammingError):
                client.get("/history")
