"""Exercise the public hero beats with transport responses, not mocked beats."""
from __future__ import annotations

from email.message import Message
from typing import Any
from urllib.error import HTTPError, URLError
from unittest.mock import patch

import pytest

from copilot_sdk.scoring.presets import PRESET_REGISTRY
from scripts import hero_moments as hero


class StubClient(hero.ApiClient):
    def __init__(self, domain: str = "trading") -> None:
        super().__init__("http://test")
        self.calls: list[tuple[str, str, Any]] = []
        self.responses: dict[tuple[str, str], Any] = {
            ("GET", "/health"): {"domain": domain},
            ("GET", "/api/trajectory"): {"current_iks": 1.0},
            ("GET", "/api/conservation/status"): {"status": "GREEN"},
            ("GET", "/api/twin/status"): {"frozen": True, "centroid_drift": 0.1},
            ("GET", "/api/fingerprint"): {"factors": [
                {"name": name, "weight": 1.0} for name in PRESET_REGISTRY[domain]().shape.factor_names
            ]},
            ("POST", "/api/s2p/score" if domain == "s2p" else "/api/score"):
                {"decision_id": "one", "action": PRESET_REGISTRY[domain]().shape.action_names[0]},
            ("POST", "/api/learn"): {"decision_id": "one", "status": "complete", "outcome": "applied"},
            ("POST", "/api/evolution/check-promotion"): {"promoted": False},
        }

    def _request(self, method: str, path: str, payload: dict[str, Any] | None = None) -> Any:
        self.calls.append((method, path, payload))
        value = self.responses.get((method, path), hero.HeroApiError("missing route", status=404))
        if isinstance(value, Exception):
            raise value
        return value


def run_beat(monkeypatch: pytest.MonkeyPatch, client: StubClient, beat: str, domain: str = "trading") -> hero.HeroResult:
    monkeypatch.setattr(hero, "ApiClient", lambda *_args: client)
    return hero.run(domain, hero.COPILOTS[domain], beat)


@pytest.mark.parametrize("domain", ["trading", "purchasing", "dataops", "s2p"])
def test_hero_c2_scores_first_real_preset_category_and_learns(monkeypatch: pytest.MonkeyPatch, domain: str) -> None:
    client = StubClient(domain)
    result = run_beat(monkeypatch, client, "c2", domain)
    assert result.status == "completed"
    posts = [(path, body) for method, path, body in client.calls if method == "POST"]
    score_path = "/api/s2p/score" if domain == "s2p" else "/api/score"
    assert [path for path, _body in posts] == [score_path, "/api/learn"]
    assert posts[0][1]["category"] == PRESET_REGISTRY[domain]().shape.category_names[0]
    assert posts[1][1]["decision_id"] == "one"
    assert posts[1][1]["actual_action"] == PRESET_REGISTRY[domain]().shape.action_names[0]


@pytest.mark.parametrize("method", ["GET", "POST"])
@pytest.mark.parametrize("status", [400, 401, 423, 500, 503, None])
def test_hero_aliases_do_not_hide_backend_failures(method: str, status: int | None) -> None:
    client = StubClient()
    client.responses[(method, "/primary")] = hero.HeroApiError("original failure", status=status)
    client.responses[(method, "/fallback")] = {"ok": True}
    with pytest.raises(hero.HeroApiError, match="original failure") as caught:
        if method == "GET":
            client.first(("/primary", "/fallback"))
        else:
            client.first_post((("/primary", {}), ("/fallback", {})))
    assert caught.value.status == status
    assert [(verb, path) for verb, path, _body in client.calls] == [(method, "/primary")]


@pytest.mark.parametrize("method", ["GET", "POST"])
@pytest.mark.parametrize("status", [404, 405])
def test_hero_aliases_try_missing_routes_only(method: str, status: int) -> None:
    client = StubClient()
    client.responses[(method, "/primary")] = hero.HeroApiError("missing", status=status)
    client.responses[(method, "/fallback")] = {"ok": True}
    result = (client.first(("/primary", "/fallback")) if method == "GET" else
              client.first_post((("/primary", {}), ("/fallback", {}))))
    assert result == ("/fallback", {"ok": True})


@pytest.mark.parametrize("failure,expected", [
    (HTTPError("http://test", 423, "locked", Message(), None), 423),
    (HTTPError("http://test", 503, "unavailable", Message(), None), 503),
    (URLError("connection refused"), None), (TimeoutError("timeout"), None),
])
def test_hero_transport_preserves_http_status(failure: Exception, expected: int | None) -> None:
    with patch.object(hero.request, "urlopen", side_effect=failure):
        with pytest.raises(hero.HeroApiError) as caught:
            hero.ApiClient("http://test").get("/health")
    assert caught.value.status == expected


@pytest.mark.parametrize("payload", [
    {"status": "paused", "reason": "conservation_red"}, {"paused": True},
    {"status": "blocked"}, {"blocked_by_gate": True},
])
def test_hero_c2_http_200_conservation_veto(monkeypatch: pytest.MonkeyPatch, payload: dict[str, Any]) -> None:
    client = StubClient()
    client.responses[("POST", "/api/learn")] = payload
    result = run_beat(monkeypatch, client, "c2")
    assert result.status == "conservation_blocked"
    assert result.evidence[-1]["payload"] == payload
    assert not any(path == "/api/outcome" for _method, path, _body in client.calls)


@pytest.mark.parametrize("payload", [{}, {"status": "partial"}, {"decision_id": "other", "status": "complete", "outcome": "applied"}])
def test_hero_c2_requires_applied_acknowledgement(monkeypatch: pytest.MonkeyPatch, payload: Any) -> None:
    client = StubClient()
    client.responses[("POST", "/api/learn")] = payload
    assert run_beat(monkeypatch, client, "c2").status == "inconclusive"


@pytest.mark.parametrize("beat", hero.BEATS)
@pytest.mark.parametrize("status,expected", [(503, "unavailable"), (423, "conservation_blocked")])
def test_hero_public_runner_reports_propagated_failure(monkeypatch: pytest.MonkeyPatch, beat: str, status: int, expected: str) -> None:
    client = StubClient()
    client.responses[("GET", "/api/trajectory")] = hero.HeroApiError(f"HTTP {status}", status=status)
    result = run_beat(monkeypatch, client, beat)
    assert result.status == expected
    assert str(status) in result.message
    assert not any(method == "POST" for method, _path, _body in client.calls)


def test_hero_s2p_missing_route_never_uses_generic_score(monkeypatch: pytest.MonkeyPatch) -> None:
    client = StubClient("s2p")
    del client.responses[("POST", "/api/s2p/score")]
    client.responses[("POST", "/api/score")] = {"decision_id": "wrong-service", "action": "approve"}
    assert run_beat(monkeypatch, client, "c2", "s2p").status == "unsupported"
    assert not any(path == "/api/score" for _method, path, _body in client.calls)


@pytest.mark.parametrize("health,warning", [
    ({"service": "purchasing"}, True), ({"copilot": "s2p"}, True),
    ({"domain": "trading", "service": "Trading Copilot"}, False),
    ({"service": "TRADING"}, False), ({"status": "ok"}, False),
])
def test_hero_identity_mismatch_warns_without_blocking(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], health: Any, warning: bool,
) -> None:
    client = StubClient()
    client.responses[("GET", "/health")] = health
    assert run_beat(monkeypatch, client, "c2").status == "completed"
    assert ("WARNING:" in capsys.readouterr().err) == warning


def test_hero_c3_reports_twin_evidence(monkeypatch: pytest.MonkeyPatch) -> None:
    result = run_beat(monkeypatch, StubClient(), "c3")
    assert result.status == "available"
    assert result.evidence[0]["payload"]["frozen"] is True


@pytest.mark.parametrize("promoted,status", [(True, "measured"), (False, "blocked")])
def test_hero_c4_reports_observed_promotion(monkeypatch: pytest.MonkeyPatch, promoted: bool, status: str) -> None:
    client = StubClient()
    client.responses[("POST", "/api/evolution/check-promotion")] = {"promoted": promoted}
    assert run_beat(monkeypatch, client, "c4").status == status


@pytest.mark.parametrize("state,promotion,expected", [
    ("RED", None, "unavailable"), ("UNKNOWN", None, "unavailable"),
    ("RED", {"promoted": False}, "inconclusive"),
    ("RED", {"promoted": False, "reason": "conservation_gate_red"}, "measured"),
    ("RED", {}, "inconclusive"),
    ("RED", {"promoted": True}, "inconclusive"), ("GREEN", {"promoted": False}, "unavailable"),
])
def test_hero_c5_needs_observed_negative_promotion(
    monkeypatch: pytest.MonkeyPatch, state: str, promotion: Any, expected: str,
) -> None:
    client = StubClient()
    client.responses[("GET", "/api/conservation/status")] = {"status": state}
    if promotion is None:
        del client.responses[("POST", "/api/evolution/check-promotion")]
    else:
        client.responses[("POST", "/api/evolution/check-promotion")] = promotion
    assert run_beat(monkeypatch, client, "c5").status == expected


def test_c5_conservation_gate_reason_required(monkeypatch: pytest.MonkeyPatch) -> None:
    client = StubClient()
    client.responses[("GET", "/api/conservation/status")] = {"status": "RED"}
    client.responses[("POST", "/api/evolution/check-promotion")] = {"promoted": False}
    result = run_beat(monkeypatch, client, "c5")
    assert result.status == "inconclusive"
    assert "cannot be verified" not in result.message


def test_c5_conservation_gate_present(monkeypatch: pytest.MonkeyPatch) -> None:
    client = StubClient()
    client.responses[("GET", "/api/conservation/status")] = {"status": "RED"}
    client.responses[("POST", "/api/evolution/check-promotion")] = {
        "promoted": False, "reason": "conservation_gate_red",
    }
    assert run_beat(monkeypatch, client, "c5").status == "measured"


def test_c5_promotion_denied_other_reason(monkeypatch: pytest.MonkeyPatch) -> None:
    client = StubClient()
    client.responses[("GET", "/api/conservation/status")] = {"status": "RED"}
    client.responses[("POST", "/api/evolution/check-promotion")] = {
        "promoted": False, "reason": "insufficient_history",
    }
    assert run_beat(monkeypatch, client, "c5").status == "inconclusive"


def test_c5_missing_promotion_endpoint(monkeypatch: pytest.MonkeyPatch) -> None:
    client = StubClient()
    client.responses[("GET", "/api/conservation/status")] = {"status": "RED"}
    del client.responses[("POST", "/api/evolution/check-promotion")]
    result = run_beat(monkeypatch, client, "c5")
    assert result.status == "unavailable"


@pytest.mark.parametrize("payload,expected", [
    ({"promoted": False, "reason": "insufficient_history; conservation gate passed"}, "inconclusive"),
    ({"promoted": False, "reason": "insufficient_history", "gate": "conservation", "conservation_status": "GREEN"}, "inconclusive"),
    ({"promoted": False, "reason": "insufficient_history"}, "inconclusive"),
    ({"promoted": False}, "inconclusive"),
    ({"promoted": False, "reason": "missing_data"}, "inconclusive"),
    ({"promoted": False, "conservation_status": "PASSED"}, "inconclusive"),
    ({"promoted": False, "reason": "conservation_gate_red"}, "measured"),
    ({"promoted": False, "conservation_status": "RED"}, "measured"),
    ({"promoted": False, "conservation_status": "BLOCKED"}, "measured"),
    ({"promoted": False, "reason": "conservation_gate_red", "conservation_status": "RED"}, "measured"),
    ({"promoted": False, "blocked_by": "conservation", "conservation_status": "RED"}, "measured"),
])
def test_c5_conservation_gate_exact_cases(
    monkeypatch: pytest.MonkeyPatch, payload: dict[str, Any], expected: str,
) -> None:
    client = StubClient()
    client.responses[("GET", "/api/conservation/status")] = {"status": "RED"}
    client.responses[("POST", "/api/evolution/check-promotion")] = payload
    assert run_beat(monkeypatch, client, "c5").status == expected


@pytest.mark.parametrize("status", ["GREEN", "PASSED"])
def test_c5_contradictory_promotion_status_is_inconclusive(
    monkeypatch: pytest.MonkeyPatch, status: str,
) -> None:
    client = StubClient()
    client.responses[("GET", "/api/conservation/status")] = {"status": "RED"}
    client.responses[("POST", "/api/evolution/check-promotion")] = {
        "promoted": False, "reason": "conservation_gate_red", "conservation_status": status,
    }
    assert run_beat(monkeypatch, client, "c5").status == "inconclusive"
