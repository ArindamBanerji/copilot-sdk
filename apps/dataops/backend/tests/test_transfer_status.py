import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app import ae_router


ENDPOINT = "/api/ae/transfer-status"
REQUIRED_TRANSFER_FIELDS = {
    "transfer_id",
    "source_system",
    "source_pattern",
    "target_system",
    "target_action",
    "transfer_date",
    "status",
    "confidence",
    "decisions_since_transfer",
    "accuracy_at_target",
    "savings_estimate",
    "description",
}


@pytest.fixture(autouse=True)
def transfer_fixture(dataops_data_dir: Path) -> None:
    source = Path(__file__).resolve().parents[1] / "data" / "transfer_status.json"
    target = dataops_data_dir / "transfer_status.json"
    target.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
    ae_router.reset_ae_fixtures()


def _transfer_status(client: TestClient) -> dict:
    response = client.get(ENDPOINT)
    assert response.status_code == 200
    return response.json()


def test_transfer_status_returns_200(client: TestClient) -> None:
    response = client.get(ENDPOINT)

    assert response.status_code == 200


def test_transfer_status_has_transfers_array(client: TestClient) -> None:
    payload = _transfer_status(client)

    assert isinstance(payload["transfers"], list)
    assert payload["transfers"]


def test_transfer_status_has_summary(client: TestClient) -> None:
    payload = _transfer_status(client)

    assert payload["summary"]["total_transfers"] == len(payload["transfers"])
    assert payload["summary"]["active"] == 1
    assert payload["summary"]["monitoring"] == 1
    assert payload["summary"]["pending"] == 1
    assert payload["summary"]["cumulative_savings"] == 62000


def test_billing_api_transfer_is_active(client: TestClient) -> None:
    payload = _transfer_status(client)

    billing_transfer = next(
        transfer
        for transfer in payload["transfers"]
        if transfer["target_system"] == "billing_api"
    )
    assert billing_transfer["transfer_id"] == "TRF-001"
    assert billing_transfer["status"] == "active"
    assert billing_transfer["target_action"] == "auto-resolved"


def test_transfer_has_required_fields(client: TestClient) -> None:
    payload = _transfer_status(client)

    for transfer in payload["transfers"]:
        assert REQUIRED_TRANSFER_FIELDS <= set(transfer)

    pending_transfer = next(
        transfer
        for transfer in payload["transfers"]
        if transfer["status"] == "pending_verification"
    )
    assert pending_transfer["accuracy_at_target"] is None
    assert pending_transfer["savings_estimate"] is None


def test_transfer_confidence_bounded(client: TestClient) -> None:
    payload = _transfer_status(client)

    for transfer in payload["transfers"]:
        assert 0.0 <= transfer["confidence"] <= 1.0


def test_transfer_status_fixture_parses() -> None:
    fixture_path = Path(__file__).resolve().parents[1] / "data" / "transfer_status.json"

    payload = json.loads(fixture_path.read_text(encoding="utf-8"))

    assert "transfers" in payload
    assert "summary" in payload
