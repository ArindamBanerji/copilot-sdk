"""HTTP smoke CLI tests with no live service dependency."""

from __future__ import annotations

import json
from io import BytesIO
from http.client import IncompleteRead
from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock, Mock
from urllib.error import HTTPError, URLError
from email.message import Message

import pytest

from integrity import commercial_smoke as smoke


def _valid_score(copilot: str = "trading") -> dict[str, Any]:
    check = smoke.CHECKS[copilot]
    if not check.expected_fields:
        return {"action": "review"}
    return {
        "decision_id": "smoke-decision", "action": "review", "action_index": 0,
        "confidence": 0.7, "probabilities": [0.7, 0.3],
        "category": check.payload["category"], "factors": check.payload["factors"],
        "engine": {"scoring": "CompoundingScorer"},
    }


def _responses(monkeypatch: pytest.MonkeyPatch, body: object, status: int = 200) -> Mock:
    transport = Mock(side_effect=[(200, '{"domain":"trading"}'), (status, json.dumps(body))])
    monkeypatch.setattr(smoke, "_http_request", transport)
    return transport


def test_argparse_help(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    transport = Mock(side_effect=AssertionError("help must not contact a service"))
    monkeypatch.setattr(smoke, "_http_request", transport)
    with pytest.raises(SystemExit) as stopped:
        smoke.main(["--help"])
    assert stopped.value.code == 0
    assert "--copilot" in capsys.readouterr().out
    transport.assert_not_called()


def test_argparse_single_copilot(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    transport = _responses(monkeypatch, _valid_score())
    assert smoke.main(["--copilot", "trading", "--base-url", "http://example.test:9000/", "--timeout", "2.5"]) == 0
    assert transport.call_args_list[0].args == ("GET", "http://example.test:9000/health", None, 2.5)
    assert transport.call_args_list[1].args == (
        "POST", "http://example.test:9000/api/score", smoke.CHECKS["trading"].payload, 2.5,
    )
    assert "1/1 passed" in capsys.readouterr().out


def test_argparse_all(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    replies = []
    for name in smoke.CHECKS:
        replies.extend([(200, json.dumps({"domain": name})), (200, json.dumps(_valid_score(name)))])
    transport = Mock(side_effect=replies)
    monkeypatch.setattr(smoke, "_http_request", transport)
    assert smoke.main(["--all"]) == 0
    assert transport.call_count == 10
    for call, check in zip(transport.call_args_list[1::2], smoke.CHECKS.values(), strict=True):
        assert call.args[0:3] == ("POST", check.base_url + check.endpoint, check.payload)
    assert "5/5 passed" in capsys.readouterr().out


@pytest.mark.parametrize("args", [
    [], ["--all", "--copilot", "soc"], ["--all", "--base-url", "http://example.test"],
    ["--all", "--timeout", "0"], ["--all", "--timeout", "nan"],
    ["--copilot", "trading", "--soc-alert-id", "ALERT-1"],
    ["--all", "--soc-alert-id", " "],
])
def test_invalid_arguments(args: list[str], monkeypatch: pytest.MonkeyPatch) -> None:
    transport = Mock()
    monkeypatch.setattr(smoke, "_http_request", transport)
    with pytest.raises(SystemExit) as stopped:
        smoke.main(args)
    assert stopped.value.code == 2
    transport.assert_not_called()


def test_connection_refused_handling(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(smoke, "_requests", None)
    opener = Mock()
    opener.open.side_effect = URLError(ConnectionRefusedError("refused"))
    monkeypatch.setattr(smoke, "build_opener", Mock(return_value=opener))
    result = smoke.run_check("trading")
    assert not result.passed
    assert "connection error" in result.detail and "refused" in result.detail


def test_timeout_handling(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(smoke, "_requests", None)
    opener = Mock()
    opener.open.side_effect = URLError(TimeoutError("read timed out"))
    monkeypatch.setattr(smoke, "build_opener", Mock(return_value=opener))
    result = smoke.run_check("trading", timeout=0.25)
    assert not result.passed
    assert "timeout" in result.detail and "0.25s" in result.detail


def test_non_json_response(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(smoke, "_http_request", Mock(side_effect=[
        (200, '{"domain":"trading"}'), (200, "<html>" + "x" * 220 + "TAIL"),
    ]))
    result = smoke.run_check("trading")
    assert not result.passed
    assert "non-JSON" in result.detail and "<html>" in result.detail
    assert "TAIL" not in result.detail


@pytest.mark.parametrize("status", [302, 404, 500])
def test_non_2xx_response(status: int, monkeypatch: pytest.MonkeyPatch) -> None:
    _responses(monkeypatch, {"error": "not available"}, status)
    result = smoke.run_check("trading")
    assert not result.passed
    assert f"HTTP {status}" in result.detail


@pytest.mark.parametrize("identity", [{"domain": "soc"}, {"service": "s2p"}, {}])
def test_wrong_service_identity(identity: dict[str, str], monkeypatch: pytest.MonkeyPatch) -> None:
    transport = Mock(return_value=(200, json.dumps(identity)))
    monkeypatch.setattr(smoke, "_http_request", transport)
    result = smoke.run_check("trading")
    assert not result.passed
    assert "identity" in result.detail and "trading" in result.detail
    assert transport.call_count == 1  # No scoring mutation on the wrong service.


@pytest.mark.parametrize(("copilot", "display_name"), [
    ("soc", "SOC Copilot Demo"), ("s2p", "s2p-copilot"),
])
def test_canonical_domain_allows_service_display_name(
    copilot: str, display_name: str, monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(smoke, "_http_request", Mock(side_effect=[
        (200, json.dumps({"domain": copilot, "service": display_name})),
        (200, json.dumps(_valid_score(copilot))),
    ]))
    assert smoke.run_check(copilot).passed


@pytest.mark.parametrize("domain", ["s2p", None, ""])
def test_service_name_cannot_override_wrong_domain(
    domain: str | None, monkeypatch: pytest.MonkeyPatch,
) -> None:
    transport = Mock(return_value=(200, json.dumps({"domain": domain, "service": "soc"})))
    monkeypatch.setattr(smoke, "_http_request", transport)
    assert not smoke.run_check("soc").passed
    assert transport.call_count == 1


@pytest.mark.parametrize("selection", [["--copilot", "soc"], ["--all"]])
def test_soc_alert_override_does_not_mutate_defaults(
    selection: list[str], monkeypatch: pytest.MonkeyPatch,
) -> None:
    replies = []
    names = list(smoke.CHECKS) if selection == ["--all"] else ["soc"]
    for name in names:
        replies.extend([(200, json.dumps({"domain": name})), (200, json.dumps(_valid_score(name)))])
    transport = Mock(side_effect=replies)
    monkeypatch.setattr(smoke, "_http_request", transport)
    assert smoke.main([*selection, "--soc-alert-id", "ALERT-LM-101"]) == 0
    assert transport.call_args_list[1].args[2] == {"alert_id": "ALERT-LM-101"}
    assert smoke.CHECKS["soc"].payload == {"alert_id": "SMOKE-TEST-001"}


def test_s2p_payload_contains_current_required_event_fields() -> None:
    payload = smoke.CHECKS["s2p"].payload
    assert payload["event_id"] == "SMOKE-TEST-INV-001"
    assert payload["category"] == "price_variance"
    assert isinstance(payload["amount"], float)
    assert payload["supplier_id"]
    assert "invoice_id" not in payload
    for factor in (
        "match_status", "amount_variance_ratio", "duplicate_score",
        "supplier_exception_history", "payment_terms_impact",
        "commodity_index_correlation", "tax_regulatory_compliance", "environmental_risk",
    ):
        assert 0 <= payload[factor] <= 1


def test_missing_fields(monkeypatch: pytest.MonkeyPatch) -> None:
    _responses(monkeypatch, {"action": "review"})
    result = smoke.run_check("trading")
    assert not result.passed
    assert "missing expected fields" in result.detail
    assert "confidence" in result.detail and "decision_id" in result.detail


@pytest.mark.parametrize("copilot", list(smoke.CHECKS))
def test_valid_response_passes(copilot: str, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(smoke, "_http_request", Mock(side_effect=[
        (200, json.dumps({"domain": copilot})), (201, json.dumps(_valid_score(copilot))),
    ]))
    assert smoke.run_check(copilot).passed


@pytest.mark.parametrize("body", [[], None, "scalar"])
def test_non_object_json_rejected(body: object, monkeypatch: pytest.MonkeyPatch) -> None:
    _responses(monkeypatch, body)
    result = smoke.run_check("trading")
    assert not result.passed
    assert "expected JSON object" in result.detail


def test_response_identity_cannot_contradict_health(monkeypatch: pytest.MonkeyPatch) -> None:
    _responses(monkeypatch, {**_valid_score(), "domain": "purchasing"})
    result = smoke.run_check("trading")
    assert not result.passed
    assert "wrong service identity" in result.detail


def test_all_continues_after_connection_failure(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    replies: list[Any] = [ConnectionRefusedError("refused")]
    for name in list(smoke.CHECKS)[1:]:
        replies.extend([(200, json.dumps({"domain": name})), (200, json.dumps(_valid_score(name)))])
    transport = Mock(side_effect=replies)
    monkeypatch.setattr(smoke, "_http_request", transport)
    assert smoke.main(["--all"]) == 1
    output = capsys.readouterr().out
    assert "FAIL soc" in output and "PASS dataops" in output and "4/5 passed" in output
    assert transport.call_count == 9


def test_requests_transport_passes_timeout_and_disables_redirects(monkeypatch: pytest.MonkeyPatch) -> None:
    response = MagicMock(status_code=200, text='{"ok":true}')
    response.__enter__.return_value = response
    request = Mock(return_value=response)
    monkeypatch.setattr(smoke, "_requests", SimpleNamespace(request=request))
    assert smoke._http_request("POST", "http://example.test/api/score", {"factor": 0.5}, 2.0) == (200, '{"ok":true}')
    assert request.call_args.kwargs["timeout"] == (2.0, 2.0)
    assert request.call_args.kwargs["allow_redirects"] is False
    assert request.call_args.kwargs["json"] == {"factor": 0.5}
    response.__exit__.assert_called_once()


@pytest.mark.parametrize("timeout", [False, True])
def test_requests_transport_errors(timeout: bool, monkeypatch: pytest.MonkeyPatch) -> None:
    class RequestFailure(Exception):
        pass

    class RequestTimeout(RequestFailure):
        pass

    failure = RequestTimeout("slow") if timeout else RequestFailure("refused")
    request = Mock(side_effect=failure)
    monkeypatch.setattr(smoke, "_requests", SimpleNamespace(
        request=request, exceptions=SimpleNamespace(Timeout=RequestTimeout, RequestException=RequestFailure),
    ))
    result = smoke.run_check("trading")
    assert not result.passed
    assert ("timeout" if timeout else "connection error") in result.detail


def test_urllib_fallback_encodes_json_and_handles_http_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(smoke, "_requests", None)
    opener = Mock()
    opener.open.side_effect = HTTPError("http://example.test", 500, "failed", Message(), BytesIO(b"failed"))
    monkeypatch.setattr(smoke, "build_opener", Mock(return_value=opener))
    assert smoke._http_request("POST", "http://example.test", {"a": 1}, 3.0) == (500, "failed")
    request = opener.open.call_args.args[0]
    assert request.method == "POST"
    assert json.loads(request.data) == {"a": 1}
    assert opener.open.call_args.kwargs == {"timeout": 3.0}


def test_optional_requests_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(smoke.importlib, "import_module", Mock(side_effect=ImportError("not installed")))
    assert smoke._optional_requests() is None


def test_urllib_fallback_reads_successful_response(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(smoke, "_requests", None)
    response = MagicMock(status=200)
    response.read.return_value = b'{"domain":"trading"}'
    response.__enter__.return_value = response
    opener = Mock()
    opener.open.return_value = response
    monkeypatch.setattr(smoke, "build_opener", Mock(return_value=opener))
    assert smoke._http_request("GET", "http://example.test/health", None, 2.0) == (200, '{"domain":"trading"}')
    assert opener.open.call_args.args[0].data is None
    response.__exit__.assert_called_once()


def test_urllib_truncated_response_fails_cleanly(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(smoke, "_requests", None)
    response = MagicMock(status=200)
    response.read.side_effect = IncompleteRead(b"partial", 100)
    response.__enter__.return_value = response
    opener = Mock()
    opener.open.return_value = response
    monkeypatch.setattr(smoke, "build_opener", Mock(return_value=opener))
    result = smoke.run_check("trading")
    assert not result.passed
    assert "incomplete HTTP response" in result.detail


def test_invalid_base_url_fails_without_network(monkeypatch: pytest.MonkeyPatch) -> None:
    transport = Mock()
    monkeypatch.setattr(smoke, "_http_request", transport)
    assert not smoke.run_check("trading", base_url="file:///tmp/example").passed
    transport.assert_not_called()


@pytest.mark.parametrize("copilot", ["trading", "purchasing", "dataops"])
def test_payload_matches_current_sdk_contract(copilot: str) -> None:
    from copilot_sdk.backend.scoring_router import ScoreRequest
    from copilot_sdk.scoring.presets import PRESET_REGISTRY

    payload = smoke.CHECKS[copilot].payload
    assert ScoreRequest(**payload).category == payload["category"]
    shape = PRESET_REGISTRY[copilot]().shape
    assert payload["category"] in shape.category_names
    assert set(payload["factors"]) == set(shape.factor_names)
    assert all(0.0 <= value <= 1.0 for value in payload["factors"].values())
