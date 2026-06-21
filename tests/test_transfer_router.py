from fastapi import FastAPI
from fastapi.testclient import TestClient

from copilot_sdk.backend.transfer_router import create_transfer_router


class FakeScorer:  # MOCK-OK: transfer router reads centroids only
    def __init__(self, warm_start_info=None, store=None):
        if warm_start_info is not None:
            self._warm_start_info = warm_start_info
        self.graph_store = store
        self._domain = "test"


class FakeStore:  # MOCK-OK: transfer router history fixture
    def __init__(self, checkpoints):
        self._checkpoints = checkpoints

    def get_centroid_checkpoints(self, domain="test", limit=50):
        return self._checkpoints[-limit:]


def _client(scorer=None, warm_start_info=None) -> TestClient:
    app = FastAPI()
    app.include_router(create_transfer_router(scorer or FakeScorer(), warm_start_info=warm_start_info))
    return TestClient(app)


def test_no_warm_start_returns_inactive() -> None:
    response = _client().get("/api/transfer/status")

    assert response.status_code == 200
    assert response.json() == {"warm_started": False}


def test_scorer_warm_start_info_normalizes_source_and_count() -> None:
    client = _client(
        FakeScorer(
            {
                "source_copilots": ["dataops", "purchasing"],
                "applied": 2,
            }
        )
    )

    payload = client.get("/api/transfer/status").json()

    assert payload == {
        "warm_started": True,
        "source_copilot": "dataops, purchasing",
        "patterns_transferred": 2,
        "transferred_at": None,
    }


def test_explicit_warm_start_info_is_used() -> None:
    payload = _client(
        warm_start_info={
            "source_copilot": "dataops",
            "patterns_transferred": 3,
        }
    ).get("/api/transfer/status").json()

    assert payload["warm_started"] is True
    assert payload["source_copilot"] == "dataops"
    assert payload["patterns_transferred"] == 3


def test_timestamp_is_returned() -> None:
    payload = _client(
        warm_start_info={
            "source": "dataops",
            "count": 1,
            "timestamp": "2026-05-15T12:00:00Z",
        }
    ).get("/api/transfer/status").json()

    assert payload["transferred_at"] == "2026-05-15T12:00:00Z"


def test_zero_applied_returns_inactive() -> None:
    payload = _client(
        warm_start_info={
            "source_copilots": ["dataops"],
            "applied": 0,
        }
    ).get("/api/transfer/status").json()

    assert payload == {"warm_started": False}


def test_recent_warm_start_checkpoint_metadata_is_used() -> None:
    store = FakeStore(
        [
            {"metadata": {"source": "manual", "applied": 4}, "created_at": "old"},
            {
                "metadata": {
                    "source": "warm_start",
                    "source_copilots": ["dataops"],
                    "applied": 1,
                },
                "created_at": "2026-05-15T13:00:00Z",
            },
        ]
    )

    payload = _client(FakeScorer(store=store)).get("/api/transfer/status").json()

    assert payload == {
        "warm_started": True,
        "source_copilot": "dataops",
        "patterns_transferred": 1,
        "transferred_at": "2026-05-15T13:00:00Z",
    }
