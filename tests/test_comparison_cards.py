from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from copilot_sdk.backend.archetype_router import create_archetype_router
from copilot_sdk.backend.transfer_router import create_transfer_router


class _Scorer:
    _domain = "trading"


def _archetype_client() -> TestClient:
    app = FastAPI()
    app.include_router(create_archetype_router())
    return TestClient(app)


def _transfer_client() -> TestClient:
    app = FastAPI()
    app.include_router(
        create_transfer_router(
            _Scorer(),
            warm_start_info={
                "source_copilot": "soc",
                "patterns_transferred": 3,
                "categories_mapped": 3,
                "source_accuracy": 0.84,
                "provenance": "transfer",
            },
        )
    )
    return TestClient(app)


def test_archetype_response_has_initial_accuracy() -> None:
    payload = _archetype_client().get("/api/archetypes/financial_services").json()

    assert "expected_initial_accuracy" in payload


def test_initial_accuracy_range() -> None:
    payload = _archetype_client().get("/api/archetypes/financial_services").json()

    assert 0.5 <= payload["expected_initial_accuracy"] <= 0.9


def test_transfer_status_has_source_accuracy() -> None:
    payload = _transfer_client().get("/api/transfer/status").json()

    assert payload["source_accuracy"] == 0.84


def test_transfer_status_has_categories_count() -> None:
    payload = _transfer_client().get("/api/transfer/status").json()

    assert payload["categories_transferred"] == 3
