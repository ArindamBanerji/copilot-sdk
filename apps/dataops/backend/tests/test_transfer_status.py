from fastapi.testclient import TestClient


ENDPOINT = "/api/ae/transfer-status"


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
    assert len(payload["transfers"]) >= 3
    assert {transfer["transfer_id"] for transfer in payload["transfers"]} >= {"TRF-001", "TRF-002", "TRF-003"}


def test_transfer_status_has_summary(client: TestClient) -> None:
    payload = _transfer_status(client)

    assert payload["summary"]["total_transfers"] == len(payload["transfers"])
    assert payload["summary"]["active"] == 1
    assert payload["summary"]["monitoring"] == 1
    assert payload["summary"]["pending"] == 1
    assert payload["summary"]["cumulative_savings"] == 62000


def test_fixture_transfer_is_rendered(client: TestClient) -> None:
    payload = _transfer_status(client)

    assert any(
        transfer.get("target_system") == "billing_api"
        for transfer in payload["transfers"]
    )


def test_transfer_has_required_fields(client: TestClient) -> None:
    payload = _transfer_status(client)

    for transfer in payload["transfers"]:
        assert {
            "transfer_id",
            "source_system",
            "source_pattern",
            "target_system",
            "target_action",
            "status",
            "confidence",
            "description",
        }.issubset(transfer)


def test_transfer_confidence_bounded(client: TestClient) -> None:
    payload = _transfer_status(client)

    for transfer in payload["transfers"]:
        assert 0.0 <= transfer["confidence"] <= 1.0


def test_transfer_status_exposes_empty_store_shape(client: TestClient) -> None:
    payload = _transfer_status(client)

    assert set(payload) == {"transfers", "summary", "provenance"}
    assert payload["summary"]["total_transfers"] == len(payload["transfers"])
