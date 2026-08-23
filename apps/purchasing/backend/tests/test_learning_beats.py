from fastapi.testclient import TestClient


def test_learning_hero_exposes_mirror_and_continuity(client: TestClient) -> None:
    response = client.get("/api/purchasing/learning/hero")
    assert response.status_code == 200
    payload = response.json()
    assert payload["domain"] == "purchasing"
    assert payload["mirror_open"]["title"] == "Mirror open"
    assert payload["continuity_close"]["title"] == "Continuity close"


def test_diagnostics_beats_expose_live_contracts(client: TestClient) -> None:
    gate = client.get("/api/purchasing/diagnostics/signal-gate")
    ramp = client.get("/api/purchasing/diagnostics/ramp")
    assert gate.status_code == 200
    assert ramp.status_code == 200
    assert gate.json()["domain"] == "purchasing"
    assert ramp.json()["remaining_verified"] >= 0


def test_evidence_beats_expose_ledger_and_self_pause(client: TestClient) -> None:
    ledger = client.get("/api/purchasing/evidence/proof-ledger")
    pause = client.get("/api/purchasing/learning/self-pause")
    assert ledger.status_code == 200
    assert pause.status_code == 200
    assert isinstance(ledger.json()["entries"], list)
    assert isinstance(pause.json()["paused"], bool)
