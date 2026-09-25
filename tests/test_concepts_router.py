from fastapi import FastAPI
from fastapi.testclient import TestClient

from copilot_sdk.backend.concepts_router import create_concepts_router


def _client() -> TestClient:
    app = FastAPI()
    app.include_router(create_concepts_router())
    return TestClient(app)


def test_four_clocks_200() -> None:
    response = _client().get("/api/platform/concepts/four-clocks")
    assert response.status_code == 200
    assert len(response.json()["content"]["clocks"]) == 4


def test_two_questions_200() -> None:
    response = _client().get("/api/platform/concepts/two-questions")
    assert response.status_code == 200
    assert len(response.json()["content"]["questions"]) == 2


def test_retraction_list_200() -> None:
    response = _client().get("/api/platform/concepts/retraction-list")
    assert response.status_code == 200
    assert response.json()["content"]["retractions"]


def test_unknown_concept_404() -> None:
    assert _client().get("/api/platform/concepts/unknown").status_code == 404

