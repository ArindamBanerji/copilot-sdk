from __future__ import annotations

from types import SimpleNamespace

from fastapi import FastAPI
from fastapi.testclient import TestClient

from copilot_sdk.backend.transfer_router import (
    _latest_checkpoint_info,
    _source_conservation_state,
    _source_store_for_domain,
    _target_conservation_state,
    create_transfer_router,
)


class _UnavailableStore:
    domain = "trading"

    def get_centroid_checkpoints(self, _domain: str, limit: int) -> list[dict[str, object]]:
        raise ConnectionError("graph offline")

    def get_latest_conservation_statuses(self, *, domains: list[str]) -> list[dict[str, str]]:
        raise ConnectionError("graph offline")

    def get_conservation_state(self, _domain: str) -> dict[str, str]:
        raise ConnectionError("graph offline")


def test_checkpoint_failure_is_distinguishable_from_no_checkpoint() -> None:
    failed = _latest_checkpoint_info(SimpleNamespace(graph_store=_UnavailableStore()))
    empty = _latest_checkpoint_info(SimpleNamespace(graph_store=None))

    assert failed == {"checkpoint_lookup_failed": True}
    assert empty is None


def test_target_fallback_is_marked_after_graph_failure() -> None:
    scorer = SimpleNamespace(
        graph_store=_UnavailableStore(),
        conservation_state=lambda: {"status": "GREEN"},
    )

    state = _target_conservation_state(scorer, "trading")

    assert state.startswith("GREEN")
    assert "fallback" in state


def test_source_fallback_cannot_execute_as_verified_green() -> None:
    scorer = SimpleNamespace(
        graph_store=_UnavailableStore(),
        source_conservation_states={"dataops": "GREEN"},
    )
    app = FastAPI()
    app.include_router(create_transfer_router(scorer))

    response = TestClient(app).post(
        "/api/transfer/execute",
        json={"source_domain": "dataops", "target_domain": "trading", "dry_run": False},
    )

    assert response.status_code == 200
    assert response.json()["executed"] is False
    assert "fallback" in response.json()["reason"]


def test_source_store_failure_is_logged(caplog) -> None:
    def unavailable(_domain: str) -> object:
        raise ConnectionError("source graph offline")

    scorer = SimpleNamespace(source_store_provider=unavailable)
    with caplog.at_level("WARNING"):
        result = _source_store_for_domain(scorer, "dataops")

    assert result is None
    assert "dataops" in caplog.text
    assert "Source store lookup failed" in caplog.text
