from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from copilot_sdk.backend.discovery_router import create_discovery_router
from copilot_sdk.discovery.cross_system import CrossSystemCorrelator


class _Engine:
    def __init__(self) -> None:
        self._alerts = []
        self.domain_decisions = {
            "soc": [{"entity_id": "supplier-a", "category": "credential_access", "score": 0.8}],
            "s2p": [{"entity_id": "supplier-a", "category": "otif_drop", "score": 0.75}],
        }

    def sweep(self):
        return []

    def get_digest(self, min_confidence: float = 0.5):
        return []


class _DemoEngine(_Engine):
    def __init__(self) -> None:
        super().__init__()
        self.domain_decisions = {
            "soc": [
                {
                    "entity_id": "supplier-a",
                    "category": "credential_access",
                    "score": 0.8,
                    "provenance": "sample",
                }
            ],
            "s2p": [
                {
                    "entity_id": "supplier-a",
                    "category": "otif_drop",
                    "score": 0.75,
                    "provenance": "sample",
                }
            ],
        }


def _client() -> TestClient:
    app = FastAPI()
    app.include_router(create_discovery_router(_Engine()))
    return TestClient(app)


def test_scan_finds_shared_entity() -> None:
    alerts = CrossSystemCorrelator().scan(
        {
            "soc": [{"entity_id": "supplier-a", "category": "credential_access", "score": 0.8}],
            "s2p": [{"entity_id": "supplier-a", "category": "otif_drop", "score": 0.76}],
        }
    )

    assert len(alerts) == 1
    assert alerts[0]["entity_id"] == "supplier-a"


def test_scan_no_overlap() -> None:
    alerts = CrossSystemCorrelator().scan(
        {
            "soc": [{"entity_id": "supplier-a", "score": 0.8}],
            "s2p": [{"entity_id": "supplier-b", "score": 0.8}],
        }
    )

    assert alerts == []


def test_scan_correlation_threshold() -> None:
    alerts = CrossSystemCorrelator().scan(
        {
            "soc": [{"entity_id": "supplier-a", "score": 0.95}],
            "s2p": [{"entity_id": "supplier-a", "score": 0.10}],
        },
        min_correlation=0.5,
    )

    assert alerts == []


def test_generate_alert_fields() -> None:
    alert = CrossSystemCorrelator().generate_alert(
        "supplier-a",
        "soc",
        "s2p",
        "credential_access",
        "otif_drop",
        0.73,
    )

    assert {"alert_id", "entity_id", "domains", "correlation", "timeline"}.issubset(alert)


def test_alert_is_advisory() -> None:
    alert = CrossSystemCorrelator().generate_alert("e", "soc", "s2p", "a", "b", 0.7)

    assert alert["advisory"] is True
    assert "action" not in alert


def test_empty_domains() -> None:
    assert CrossSystemCorrelator().scan({}) == []


def test_router_cross_system() -> None:
    payload = _client().get("/api/discovery/cross-system").json()

    assert isinstance(payload["alerts"], list)
    assert payload["provenance"] == "real"


def test_provenance_real_when_real_decisions() -> None:
    payload = _client().get("/api/discovery/cross-system").json()

    assert payload["provenance"] == "real"


def test_provenance_demo_when_sample_decisions() -> None:
    app = FastAPI()
    app.include_router(create_discovery_router(_DemoEngine()))
    payload = TestClient(app).get("/api/discovery/cross-system").json()

    assert payload["provenance"] == "demo"


def test_digest_includes_cross_system() -> None:
    payload = _client().get("/api/discovery/digest").json()

    assert "alerts" in payload
    assert "cross_system" in payload
    assert isinstance(payload["cross_system"], list)
