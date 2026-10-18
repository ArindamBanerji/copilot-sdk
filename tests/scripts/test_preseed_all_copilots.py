from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest

import scripts.preseed_all_copilots as preseed


def test_api_json_sets_socket_read_timeout_after_request(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    events: list[object] = []

    class FakeSocket:
        def settimeout(self, timeout: float) -> None:
            events.append(("socket_timeout", timeout))

    class FakeResponse:
        status = 200

        def read(self) -> bytes:
            return b'{"ok": true}'

    class FakeConnection:
        def __init__(self, host: str, port: int | None, timeout: float) -> None:
            events.append(("connect", host, port, timeout))
            self.sock = FakeSocket()

        def request(
            self,
            method: str,
            target: str,
            body: bytes | None,
            headers: dict[str, str],
        ) -> None:
            del body, headers
            events.append(("request", method, target))

        def getresponse(self) -> FakeResponse:
            assert events[-1] == ("socket_timeout", preseed.READ_TIMEOUT_SECONDS)
            events.append("getresponse")
            return FakeResponse()

        def close(self) -> None:
            events.append("close")

    monkeypatch.setattr(preseed.http.client, "HTTPConnection", FakeConnection)

    assert preseed.api_get("http://example.test", "/health") == {"ok": True}
    assert ("request", "GET", "/health") in events
    assert ("socket_timeout", preseed.READ_TIMEOUT_SECONDS) in events


def test_s2p_missing_trajectory_total_uses_health_node_count(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        preseed,
        "check_health",
        lambda _url: (True, {"node_count": 29_517}),
    )

    def unavailable(_url: str) -> tuple[bool, dict[str, Any]]:
        raise preseed.ApiError("GET /api/trajectory failed: HTTP 404")

    monkeypatch.setattr(preseed, "check_already_seeded", unavailable)
    monkeypatch.setattr(
        preseed,
        "api_get",
        lambda _url, path: {"invoices": [{"event_id": "existing"}]}
        if path == "/api/s2p/performance/trajectory"
        else pytest.fail(path),
    )
    monkeypatch.setattr(
        preseed,
        "api_post",
        lambda *_args, **_kwargs: pytest.fail("already-seeded S2P must not score"),
    )

    result = preseed.seed_s2p_domain(SimpleNamespace(force=False, dry_run=False))

    assert result.skipped is True
    assert result.successes == 0
    assert result.failures == 0


def test_s2p_low_health_node_count_enters_scoring_loop(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(preseed, "S2P_PRESEED_DECISIONS", 2)
    monkeypatch.setattr(preseed, "check_health", lambda _url: (True, {"node_count": 1}))

    def unavailable(_url: str) -> tuple[bool, dict[str, Any]]:
        raise preseed.ApiError("GET /api/trajectory failed: HTTP 404")

    monkeypatch.setattr(preseed, "check_already_seeded", unavailable)
    monkeypatch.setattr(
        preseed,
        "api_get",
        lambda _url, path: {"invoices": []}
        if path == "/api/s2p/performance/trajectory"
        else pytest.fail(path),
    )
    calls: list[str] = []

    def post(_url: str, path: str, body: dict[str, Any]) -> dict[str, Any]:
        calls.append(path)
        if path == "/api/s2p/score":
            return {"decision_id": body["event_id"], "action": "auto_approve"}
        if path == "/api/learn":
            return {"decision_id": body["decision_id"], "reward": 1.0}
        raise AssertionError(path)

    monkeypatch.setattr(preseed, "api_post", post)

    result = preseed.seed_s2p_domain(SimpleNamespace(force=False, dry_run=False))

    assert result.skipped is False
    assert result.successes == 2
    assert result.failures == 0
    assert calls.count("/api/s2p/score") == 2
    assert calls.count("/api/learn") == 2


def test_preseed_learn_payload_does_not_send_privileged_preseed_flag(monkeypatch):
    seen: list[dict[str, Any]] = []

    class FakeTransport:
        def check_health(self, base_url: str):
            return True, {"ok": True}

        def check_already_seeded(self, base_url: str):
            return False, {"decisions_total": 0}

        def has_regime_checkpoint(self, base_url: str) -> bool:
            return True

        def api_post(self, base_url: str, path: str, body: dict[str, Any]):
            if path == "/api/score":
                return {"decision_id": "seed-decision", "action": "order_as_planned"}
            if path == "/api/learn":
                seen.append(body)
                return {"outcome_id": "learned", "reward": 1.0}
            if path == "/api/context/order-metadata":
                return {"ok": True}
            raise AssertionError(path)

        def verify_domain(self, config, base_url: str, successes: int, failures: int, total_reward: float) -> None:
            return None

    seed = {
        "item": "chicken_breast",
        "expected_demand": 0.7,
        "day_of_week_factor": 0.5,
        "weather_forecast": 0.4,
        "event_flag": 0.2,
        "historical_waste": 0.3,
        "supplier_lead_time": 0.6,
        "category": "produce",
        "actual_action": "order_as_planned",
    }
    monkeypatch.setattr(preseed, "load_seed", lambda path: [seed])
    monkeypatch.setattr(preseed, "expanded_seed", lambda source, *args, **kwargs: list(source))
    config = next(c for c in preseed.DOMAINS if c.name == "purchasing")
    args = SimpleNamespace(dry_run=False, force=True)

    result = preseed.seed_domain(config, args, FakeTransport())

    assert result.successes == 1
    assert seen
    assert seen[0]["context"]["seed_domain"] == "purchasing"
    assert "preseed" not in seen[0]["context"]
