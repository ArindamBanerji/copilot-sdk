from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import create_app
from app.services.chain_demo_seed import ChainLearningDemo


def test_chain_seed_creates_4_locations_with_decision_counts():
    state = ChainLearningDemo().seed()

    assert len(state["locations"]) == 4
    assert len(state["decisions"]) == 415
    assert state["locations"]["downtown"]["decisions"] == 200
    assert state["locations"]["new"]["decisions"] == 15


def test_chain_seed_uses_provenance_demo():
    state = ChainLearningDemo().seed()

    assert state["provenance"] == "demo"
    assert all(location["provenance"] == "demo" for location in state["locations"].values())
    assert all(decision["provenance"] == "demo" for decision in state["decisions"])


def test_transfer_copies_dk_weights_from_source_to_targets():
    service = ChainLearningDemo()
    state = service.seed()

    service.transfer(state, "downtown", ["airport"])

    assert state["locations"]["airport"]["dk_weights"] == state["locations"]["downtown"]["dk_weights"]


def test_transfer_respects_conservation_gate():
    service = ChainLearningDemo()
    state = service.seed()

    result = service.transfer(state, "airport", ["downtown"])

    assert result["skipped"] == [{"location": "downtown", "reason": "target_not_amber_or_red"}]
    assert "baseline_from" not in state["locations"]["downtown"]


def test_transfer_response_includes_before_after_iks():
    service = ChainLearningDemo()
    state = service.seed()

    result = service.transfer(state, "downtown", ["airport", "suburb", "new"])

    assert result["before"]["airport"]["iks"] == 31
    assert result["after"]["airport"]["iks"] == 47
    assert result["before"]["new"]["iks"] == 3
    assert result["after"]["new"]["iks"] == 28


def test_transfer_narrative_uses_kitchen_language():
    service = ChainLearningDemo()
    result = service.transfer(service.seed(), "downtown", ["airport", "suburb", "new"])

    assert "purchasing discipline transferred" in result["narrative"]
    assert "Airport: IKS 31->47" in result["narrative"]


def test_chain_seed_endpoint_and_transfer_endpoint():
    client = TestClient(create_app(db_path=":memory:", demo_bundle_path=False))

    seeded = client.post("/api/purchasing/demo/chain-seed")
    transferred = client.post(
        "/api/purchasing/chain/transfer",
        json={"source_location": "downtown", "target_locations": ["airport", "suburb", "new"]},
    )

    assert seeded.status_code == 200
    assert seeded.json() == {"locations_seeded": 4, "total_decisions": 415, "provenance": "demo"}
    assert transferred.status_code == 200
    assert "centroids" not in transferred.json()["transferred"]
    assert transferred.json()["transferred"]["dk_weights"] == 21


def test_chain_seed_populates_multi_unit_dashboard():
    client = TestClient(create_app(db_path=":memory:", demo_bundle_path=False))

    client.post("/api/purchasing/demo/chain-seed")
    dashboard = client.get("/api/purchasing/multi-unit/dashboard")

    assert dashboard.status_code == 200
    names = [row["name"] for row in dashboard.json()["locations"]]
    assert names == ["Downtown", "Airport", "Suburb", "New"]
