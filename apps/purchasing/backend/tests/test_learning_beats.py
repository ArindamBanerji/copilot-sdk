from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest
from types import SimpleNamespace
from unittest.mock import MagicMock

from copilot_sdk.graph import InMemoryGraphStore

from app.routers.learning_beats import _stats, _verified


def test_learning_hero_exposes_mirror_and_continuity(client: TestClient) -> None:
    response = client.get("/api/purchasing/learning/hero")
    assert response.status_code == 200
    payload = response.json()
    assert payload["domain"] == "purchasing"
    assert payload["mirror_open"]["title"] == "Mirror open"
    assert payload["continuity_close"]["title"] == "Continuity close"


def test_learning_verified_failure_is_unavailable() -> None:
    class BrokenGraph:
        def get_verified_decisions(self, domain):
            raise RuntimeError("graph unavailable")

    assert _verified(BrokenGraph()) is None


def test_learning_stats_does_not_present_bootstrap_on_conservation_failure() -> None:
    class BrokenGraph:
        def get_verified_decisions(self, domain):
            return []

    class BrokenScorer:
        graph_store = BrokenGraph()

        def get_conservation_status(self):
            raise RuntimeError("conservation unavailable")

    stats = _stats(BrokenScorer())
    assert stats["conservation_status"] == "UNAVAILABLE"
    assert stats["degraded"] is True


def test_learning_stats_marks_healthy_graph_conservation_available() -> None:
    store = InMemoryGraphStore(domain="purchasing")
    store.write_conservation_status(
        "status-1", "purchasing", 12, 0.8, 0.5, 0.4, 10, 8, "GREEN", "v1",
    )
    original = store.get_latest_conservation_statuses
    store.get_latest_conservation_statuses = MagicMock(wraps=original)
    scorer = SimpleNamespace(
        graph_store=store,
        trajectory=lambda: {"current_iks": 1.25},
    )

    stats = _stats(scorer)

    store.get_latest_conservation_statuses.assert_called_once_with(["purchasing"])
    assert stats["conservation_status"] == "GREEN"
    assert stats["conservation_available"] is True
    assert stats["trajectory_available"] is True
    assert stats["iks"] == 1.25
    assert stats["iks_available"] is True
    assert stats["degraded"] is False


@pytest.mark.parametrize(
    "trajectory_result",
    [None, [1.25], "malformed", 42],
)
def test_learning_stats_rejects_silent_malformed_trajectory(trajectory_result) -> None:
    graph = MagicMock()
    graph.get_verified_decisions.return_value = []
    graph.get_latest_conservation_statuses.return_value = []
    scorer = SimpleNamespace(
        graph_store=graph,
        trajectory=lambda: trajectory_result,
    )

    stats = _stats(scorer)

    assert stats["trajectory_available"] is False
    assert stats["iks"] == 0.0
    assert stats["iks_available"] is False
    assert stats["degraded"] is True


def test_learning_stats_accepts_empty_trajectory_as_cold_start() -> None:
    graph = MagicMock()
    graph.get_verified_decisions.return_value = []
    graph.get_latest_conservation_statuses.return_value = []
    scorer = SimpleNamespace(graph_store=graph, trajectory=lambda: {})

    stats = _stats(scorer)

    assert stats["trajectory_available"] is True
    assert stats["iks"] == 0.0
    assert stats["iks_available"] is False
    assert stats["degraded"] is True


def test_learning_stats_propagates_trajectory_type_error() -> None:
    graph = MagicMock()
    graph.get_verified_decisions.return_value = []
    graph.get_latest_conservation_statuses.return_value = []
    scorer = SimpleNamespace(
        graph_store=graph,
        trajectory=MagicMock(side_effect=TypeError("programming bug")),
    )

    with pytest.raises(TypeError, match="programming bug"):
        _stats(scorer)


def test_learning_stats_propagates_scorer_conservation_type_error() -> None:
    graph = MagicMock()
    graph.get_verified_decisions.return_value = []
    scorer = SimpleNamespace(
        graph_store=graph,
        trajectory=MagicMock(return_value={"current_iks": 0.42}),
        get_conservation_status=MagicMock(side_effect=TypeError("programming bug")),
    )

    with pytest.raises(TypeError, match="programming bug"):
        _stats(scorer)


def test_learning_stats_propagates_graph_conservation_type_error() -> None:
    graph = MagicMock()
    graph.get_verified_decisions.return_value = []
    graph.get_latest_conservation_statuses.side_effect = TypeError("programming bug")
    scorer = SimpleNamespace(
        graph_store=graph,
        trajectory=MagicMock(return_value={"current_iks": 0.42}),
    )

    with pytest.raises(TypeError, match="programming bug"):
        _stats(scorer)


def test_learning_stats_rejects_silent_none_scorer_conservation() -> None:
    graph = MagicMock()
    graph.get_verified_decisions.return_value = []
    scorer = SimpleNamespace(
        graph_store=graph,
        trajectory=lambda: {"current_iks": 1.25},
        get_conservation_status=lambda: None,
    )

    stats = _stats(scorer)

    assert stats["conservation_available"] is False
    assert stats["conservation_status"] == "UNAVAILABLE"
    assert stats["degraded"] is True


@pytest.mark.parametrize("statuses", [None, {"status": "GREEN"}, [{"status": None}]])
def test_learning_stats_rejects_silent_malformed_graph_conservation(statuses) -> None:
    graph = MagicMock()
    graph.get_verified_decisions.return_value = []
    graph.get_latest_conservation_statuses.return_value = statuses
    scorer = SimpleNamespace(
        graph_store=graph,
        trajectory=lambda: {"current_iks": 1.25},
    )

    stats = _stats(scorer)

    assert stats["conservation_available"] is False
    assert stats["conservation_status"] == "UNAVAILABLE"
    assert stats["degraded"] is True


def test_learning_stats_accepts_empty_graph_conservation_as_bootstrap() -> None:
    graph = MagicMock()
    graph.get_verified_decisions.return_value = []
    graph.get_latest_conservation_statuses.return_value = []
    scorer = SimpleNamespace(
        graph_store=graph,
        trajectory=lambda: {"current_iks": 1.25},
    )

    stats = _stats(scorer)

    assert stats["conservation_available"] is True
    assert stats["conservation_status"] == "BOOTSTRAP"
    assert stats["degraded"] is False


@pytest.mark.parametrize("state", ["GREEN", "AMBER", "RED"])
def test_learning_stats_accepts_recognized_graph_conservation_states(state: str) -> None:
    graph = MagicMock()
    graph.get_verified_decisions.return_value = []
    graph.get_latest_conservation_statuses.return_value = [{"status": state}]
    scorer = SimpleNamespace(
        graph_store=graph,
        trajectory=lambda: {"current_iks": 1.25},
    )

    stats = _stats(scorer)

    assert stats["conservation_available"] is True
    assert stats["conservation_status"] == state
    assert stats["degraded"] is False


def test_learning_http_outage_preserves_numeric_iks() -> None:
    class BrokenGraph:
        def get_verified_decisions(self, domain):
            raise RuntimeError("offline")

        def get_latest_conservation_statuses(self, domains):
            raise RuntimeError("offline")

    app = FastAPI()
    from app.routers.learning_beats import create_learning_beats_router
    scorer = SimpleNamespace(
        graph_store=BrokenGraph(),
        trajectory=lambda: (_ for _ in ()).throw(RuntimeError("offline")),
    )
    app.include_router(create_learning_beats_router(scorer))
    client = TestClient(app)
    for path in ("/api/purchasing/learning/hero", "/api/purchasing/diagnostics/ramp"):
        payload = client.get(path).json()
        assert payload["iks"] == 0.0
        assert payload["trajectory_available"] is False
        assert payload["iks_available"] is False
        assert payload["degraded"] is True
        assert all(value is not None for value in payload.values())


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
