from __future__ import annotations

import importlib.util
import io
import json
import sys
from argparse import Namespace
from dataclasses import replace
from email.message import Message
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit

import pytest


ROOT = Path(__file__).resolve().parents[1]


def _load(name: str, relative: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


preseed = _load("demo_preseed", "scripts/preseed_all_copilots.py")
preflight = _load("demo_truth_preflight", "scripts/demo_truth_preflight.py")


class CompleteClient:
    def __init__(self, spec: Any, bad_metric: bool = False) -> None:
        self.spec = spec
        self.bad_metric = bad_metric

    def get(self, _base_url: str, path: str) -> dict[str, Any]:
        if path in self.spec.health:
            return {"status": "ok"}
        if path in self.spec.trajectory:
            return {"iks": 0.42, "verified_count": 60, "decisions_total": 80, "phase": "GREEN"}
        if path in self.spec.twins:
            return {"status": "frozen", "snapshot_id": "day-0", "comparison": {"changed": False}}
        if path in self.spec.promotions:
            return {"promotions": [{"stage": "shadowing"}, {"stage": "shadowing"}]}
        if path in self.spec.claims:
            return {"claims": [{"claim_id": "demo", "status": "verified", "evidence_tier": "T_O"}]}
        if path in self.spec.metrics:
            if self.bad_metric:
                return {"is_sample_data": True, "provenance": "sample", "accuracy": 0.9}
            return {"evidence_tier": "T_O", "evidence_label": "observed", "verified_count": 60}
        raise RuntimeError("missing path")


def test_s2p_seed_vectors_are_bounded_and_cover_categories() -> None:
    events = [preseed.s2p_event(index) for index in range(200)]
    assert len({event["category"] for event in events}) == 5
    for event in events:
        assert 0.0 <= event["duplicate_score"] <= 1.0
        assert 0.0 <= event["tax_regulatory_compliance"] <= 1.0
        assert event["amount"] > 0


def test_s2p_seed_has_confirm_and_override_schedule(monkeypatch: pytest.MonkeyPatch) -> None:
    sent: list[dict[str, Any]] = []
    scores: dict[str, str] = {}

    def post(_url: str, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        if path == "/api/s2p/score":
            identity = payload["event_id"]
            scores[identity] = "auto_approve"
            return {"decision_id": identity, "action": scores[identity]}
        assert path == "/api/learn"
        sent.append(payload)
        return {"decision_id": payload["decision_id"], "status": "complete", "outcome": "applied"}

    monkeypatch.setattr(preseed, "check_health", lambda _url: (True, {}))
    monkeypatch.setattr(preseed, "check_already_seeded", lambda _url: (False, {"decisions_total": 0}))
    monkeypatch.setattr(preseed, "api_post", post)
    result = preseed.seed_s2p_domain(Namespace(force=False, dry_run=False))
    assert result.successes == len(sent) == preseed.S2P_PRESEED_DECISIONS
    outcomes = [payload["outcome"] for payload in sent]
    assert outcomes.count("confirmed") > outcomes.count("override") > 0
    for payload in sent:
        assert (payload["actual_action"] == scores[payload["decision_id"]]) == (payload["outcome"] == "confirmed")


def test_preflight_passes_complete_copilot() -> None:
    spec = preflight.SPECS["trading"]
    assert preflight.check_copilot(spec, CompleteClient(spec)) == []


def test_preflight_rejects_f26_sample_metric() -> None:
    spec = preflight.SPECS["trading"]
    failures = preflight.check_copilot(spec, CompleteClient(spec, bad_metric=True))
    assert any("F-26" in failure for failure in failures)


def test_preflight_rejects_f27_synthetic_measured_label() -> None:
    spec = preflight.SPECS["trading"]

    class SyntheticMeasured(CompleteClient):
        def get(self, base_url: str, path: str) -> dict[str, Any]:
            payload = super().get(base_url, path)
            if path in self.spec.metrics:
                payload.update({"evidence_label": "measured", "source": "synthetic_preseed"})
            return payload

    failures = preflight.check_copilot(spec, SyntheticMeasured(spec))
    assert any("F-27" in failure for failure in failures)


def test_preflight_rejects_missing_twin_and_promotion() -> None:
    spec = preflight.SPECS["trading"]

    class MissingArtifacts(CompleteClient):
        def get(self, base_url: str, path: str) -> dict[str, Any]:
            if path in self.spec.twins or path in self.spec.promotions:
                raise RuntimeError("not found")
            return super().get(base_url, path)

    failures = preflight.check_copilot(spec, MissingArtifacts(spec))
    assert any("Frozen Twin" in failure for failure in failures)
    assert any("promotion records" in failure for failure in failures)


def test_preflight_dry_run_is_read_only() -> None:
    assert preflight.main(["--dry-run", "--copilots", "trading", "s2p"]) == 0


def test_launcher_exposes_preseed_and_preflight_flags() -> None:
    demo = _load("demo_launcher", "demo.py")
    args = demo.create_parser().parse_args(["--preseed", "--preflight", "--no-browser"])
    assert args.preseed is True
    assert args.preflight is True


def test_preflight_warns_when_f26_unavailable(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.setattr(preflight, "scan_for_sample", None)
    spec = preflight.SPECS["trading"]
    assert preflight.check_copilot(spec, CompleteClient(spec)) == []
    assert "WARNING: F-26 sample scan unavailable" in capsys.readouterr().err


@pytest.mark.parametrize("kind,label", [("claims", "claim registry"), ("twins", "Frozen Twin"), ("promotions", "promotion records")])
@pytest.mark.parametrize("payload", [{}, [], None, "OK", {"status": "ok"}, {"detail": "not configured"}])
def test_preflight_rejects_empty_or_unrelated_artifacts(kind: str, label: str, payload: Any) -> None:
    spec = preflight.SPECS["trading"]

    class InvalidArtifact(CompleteClient):
        def get(self, base_url: str, path: str) -> Any:
            if path in getattr(self.spec, kind):
                return payload
            return super().get(base_url, path)

    failures = preflight.check_copilot(spec, InvalidArtifact(spec))
    assert any(label + " returned empty or unrelated payload" in failure for failure in failures)


@pytest.mark.parametrize("kind,payload,expected", [
    ("claims", {"claims": []}, False), ("promotions", {"promotions": []}, False),
    # Updated: FIX-R1S1C tightened validation; a typed unfrozen status is valid.
    ("twins", {"frozen": False, "snapshot_time": None, "decision_count": 0}, True),
])
def test_preflight_validates_unpopulated_artifact_envelopes(kind: str, payload: Any, expected: bool) -> None:
    assert preflight._has_artifact(payload, kind) is expected


def test_preflight_rejects_unrelated_nested_claim() -> None:
    assert preflight._has_artifact({"claims": [{"claim_id": "x"}]}, "claims") is False


def test_preflight_accepts_valid_claim() -> None:
    assert preflight._has_artifact({"claim_id": "C-001", "status": "verified", "confidence": 0.85}, "claims")


def test_preflight_rejects_wrong_shape_twin() -> None:
    assert preflight._has_artifact({"twin_id": "T1"}, "twins") is False


def test_preflight_accepts_valid_twin() -> None:
    assert preflight._has_artifact({"twin_id": "T1", "current_vs_frozen": {"delta": 0.1}}, "twins")


def test_preflight_rejects_single_unrelated_key() -> None:
    assert preflight._has_artifact({"promoted": "not_a_bool"}, "promotions") is False


def test_preflight_accepts_valid_promotion() -> None:
    assert preflight._has_artifact({"promoted": True, "candidates": [{"id": "p1"}]}, "promotions")


@pytest.mark.parametrize("kind,payload", [
    ("claims", {"claim_id": "C1", "confidence": "not a number"}),
    ("claims", {"claim_id": "C1"}),
    ("claims", {"claim_id": "", "status": "verified"}),
    ("promotions", {"candidates": [None]}),
    ("promotions", {"promotions": ["unrelated"]}),
    ("promotions", {"promoted": "true"}),
    ("promotions", {"promoted": 1}),
    ("twins", {"twin_id": "T1"}),
])
def test_preflight_must_reject_malformed(kind: str, payload: Any) -> None:
    assert preflight._has_artifact(payload, kind) is False


@pytest.mark.parametrize("kind,payload", [
    ("claims", {"claim_id": "C-001", "status": "verified", "confidence": 0.85}),
    ("claims", {"claim_id": "C-001", "factors": [{"name": "f1", "value": 0.9}]}),
    ("claims", {"claim_id": "C-001", "evidence": {"source": "graph"}}),
    ("twins", {"twin_id": "T1", "delta": 0.1}),
    ("twins", {"twin_id": "T1", "delta": 0.0}),
    ("twins", {"twin_id": "T1", "delta": 0, "divergence": 0.05}),
    ("twins", {"twin_id": "T1", "current_vs_frozen": {"accuracy": [0.8, 0.82]}}),
    ("twins", {"snapshot_id": "S1", "comparison": {"drift": 0.02}}),
    ("twins", {"frozen": True, "snapshot_time": "2026-10-01T00:00:00Z", "decision_count": 200}),
    ("twins", {"frozen": False, "decision_count": 0}),
    ("promotions", {"promoted": True, "candidates": [{"id": "C1", "score": 0.9}]}),
    ("promotions", {"promoted": False}),
    ("promotions", {"eligible": True}),
    ("promotions", {"promotions": [{"rule_id": "R1", "status": "promoted"}]}),
])
def test_preflight_must_accept_valid(kind: str, payload: Any) -> None:
    assert preflight._has_artifact(payload, kind) is True


@pytest.mark.parametrize("value", [True, float("nan"), float("inf")])
@pytest.mark.parametrize("kind,identity,field", [
    ("claims", "claim_id", "confidence"), ("twins", "twin_id", "delta"),
])
def test_preflight_numeric_fields_reject_booleans_and_nonfinite(
    kind: str, identity: str, field: str, value: Any,
) -> None:
    assert preflight._has_artifact({identity: "one", field: value}, kind) is False


def _purchasing_promotions() -> dict[str, Any]:
    from copilot_sdk.promotion.core import PromotionRecord, PromotionStage

    record = PromotionRecord("p1", "purchasing", "protein", current_stage=PromotionStage.SHADOWING)
    # create_purchasing_control_router().promotion_state() wire contract.
    return {"records": [record.to_dict()], "observation_only": True}


@pytest.mark.parametrize("key", ["promotions", "candidates", "records"])
@pytest.mark.parametrize("record", [
    {"error": "backend unavailable"}, {"unrelated": "value"}, {}, None,
    {"stage": "unrelated"}, {"stage": []}, {"promoted": "true"},
    {"record_id": "p1", "current_stage": "shadowing"},
    {"id": "c1", "score": True}, {"id": "c1", "score": float("nan")},
])
def test_promotion_unrelated_dict_rejected(key: str, record: Any) -> None:
    assert not preflight._has_artifact({key: [record]}, "promotions")


@pytest.mark.parametrize("key", ["promotions", "candidates", "records"])
def test_promotion_empty_records_rejected(key: str) -> None:
    assert not preflight._has_artifact({key: []}, "promotions")


def test_promotion_valid_trading_accepted() -> None:
    # Trading PromotionEngine._evaluation_payload(), returned as a dashboard list.
    payload = [{"category": "trend_following", "current_stage": "paper", "ready": False,
                "next_stage": "small_live", "blockers": ["Need more decisions"],
                "evidence": {"decisions_in_stage": 10, "conservation_status": "GREEN"}}]
    assert preflight._has_artifact(payload, "promotions")


def test_promotion_valid_purchasing_accepted() -> None:
    assert preflight._has_artifact(_purchasing_promotions(), "promotions")


def test_promotion_mixed_valid_and_malformed_records_rejected() -> None:
    assert not preflight._has_artifact({"promotions": [{"stage": "shadowing"}, {"error": "unavailable"}]}, "promotions")
    assert not preflight._has_artifact({"promotions": [{"promoted": "true", "nested": {"eligible": True}}]}, "promotions")


def test_promotion_candidate_identity_and_score_accepted() -> None:
    assert preflight._has_artifact({"candidates": [{"id": "C1", "score": 0.0}]}, "promotions")


def test_promotion_list_wrapped_envelopes_remain_supported() -> None:
    assert preflight._has_artifact([{"data": {"promotions": [{"stage": "shadowing"}]}}], "promotions")
    assert not preflight._has_artifact([{"data": {"promotions": [{"error": "unavailable"}]}}], "promotions")


class ArtifactClient(CompleteClient):
    def __init__(self, spec: Any, artifacts: dict[str, Any]) -> None:
        super().__init__(spec)
        self.artifacts = artifacts

    def get(self, base_url: str, path: str) -> Any:
        for kind, payload in self.artifacts.items():
            if path in getattr(self.spec, kind):
                return payload
        return super().get(base_url, path)


def _purchasing_twin() -> dict[str, Any]:
    from types import SimpleNamespace

    # Execute the actual service's response construction without opening stores.
    control = _load("preflight_purchasing_control", "apps/purchasing/backend/app/services/purchasing_control.py")
    snapshot = SimpleNamespace(metadata={"timestamp": 1791052800.0}, checksum="a" * 64)
    point = {"decision_id": "d1", "decisions": 1, "timestamp": 1791052801.0, "accuracy": 1.0}
    service = SimpleNamespace(
        twin=SimpleNamespace(is_frozen=lambda: True, get_snapshot=lambda: snapshot),
        _twin_curves=lambda: {"learning_curve": [point], "frozen_curve": [dict(point)],
                             "curve_kind": "retrospective_paired_replay", "metric": "accuracy"},
    )
    return dict(control.PurchasingControlService.frozen_status(service))


def test_purchasing_promotion_records_accepted() -> None:
    spec = preflight.SPECS["purchasing"]
    assert preflight.check_copilot(spec, ArtifactClient(spec, {"promotions": _purchasing_promotions()})) == []


def test_purchasing_frozen_twin_accepted() -> None:
    spec = preflight.SPECS["purchasing"]
    assert preflight.check_copilot(spec, ArtifactClient(spec, {"twins": _purchasing_twin()})) == []


def test_trading_shapes_still_accepted() -> None:
    spec = preflight.SPECS["trading"]
    for twin in ({"twin_id": "T1", "delta": 0.0}, {"frozen": True, "decision_count": 200}):
        assert preflight.check_copilot(spec, ArtifactClient(spec, {
            "twins": twin, "promotions": {"promoted": False},
        })) == []


def test_dataops_shapes_still_accepted() -> None:
    spec = preflight.SPECS["dataops"]
    # Preserve the existing shared SDK status/comparison and gate contracts.
    for twin in ({"snapshot_id": "S1", "comparison": {"drift": 0.02}},
                 {"frozen": False, "decision_count": 0}):
        assert preflight.check_copilot(spec, ArtifactClient(spec, {
            "twins": twin, "promotions": {"eligible": False},
        })) == []


@pytest.mark.parametrize("field,value", [
    ("available", False), ("available", "true"), ("status", "NOT_INITIALIZED"),
    ("snapshot_time", None), ("snapshot_time", True), ("snapshot_time", float("nan")),
    ("checksum", ""), ("checksum", 123), ("learning_curve", None),
    ("learning_curve", ["unrelated"]), ("frozen_curve", [{"error": "unavailable"}]),
    ("frozen_curve", [{"accuracy": True}]), ("frozen_curve", [{"accuracy": float("inf")}]),
    ("frozen_curve", []),
])
def test_purchasing_frozen_twin_malformed_rejected(field: str, value: Any) -> None:
    payload = _purchasing_twin()
    payload[field] = value
    assert not preflight._has_artifact(payload, "twins")


def test_purchasing_frozen_twin_empty_paired_curves_accepted() -> None:
    payload = _purchasing_twin()
    payload.update(learning_curve=[], frozen_curve=[], snapshot_time="2026-10-03T00:00:00Z")
    assert preflight._has_artifact(payload, "twins")


def _http_failure(status: int) -> HTTPError:
    return HTTPError("http://test", status, "test response", Message(), None)


def _mock_http(monkeypatch: pytest.MonkeyPatch, spec: Any, overrides: dict[str, Any]) -> list[str]:
    calls: list[str] = []
    complete = CompleteClient(spec)

    def urlopen(req: Any, timeout: int) -> io.BytesIO:
        path = urlsplit(req.full_url).path
        calls.append(path)
        payload = overrides[path] if path in overrides else complete.get(spec.url, path)
        if isinstance(payload, Exception):
            raise payload
        return io.BytesIO(payload if isinstance(payload, bytes) else json.dumps(payload).encode())

    monkeypatch.setattr(preflight.request, "urlopen", urlopen)
    return calls


@pytest.mark.parametrize("kind", ["health", "trajectory", "claims", "twins", "promotions", "metrics"])
def test_503_not_silently_fallback(monkeypatch: pytest.MonkeyPatch, kind: str) -> None:
    spec = preflight.SPECS["trading"]
    paths = ("/metrics/primary", "/metrics/fallback") if kind == "metrics" else (getattr(spec, kind)[0], "/unused-fallback")
    spec = replace(spec, **{kind: paths})
    calls = _mock_http(monkeypatch, spec, {paths[0]: _http_failure(503)})
    failures = preflight.check_copilot(spec)
    assert any("http_error" in failure and "HTTP 503" in failure and paths[0] in failure for failure in failures)
    assert paths[1] not in calls


@pytest.mark.parametrize("failure", [TimeoutError("timed out"), URLError(TimeoutError("timed out"))])
def test_timeout_reported(monkeypatch: pytest.MonkeyPatch, failure: Exception) -> None:
    spec = preflight.SPECS["trading"]
    calls = _mock_http(monkeypatch, spec, {spec.claims[0]: failure})
    failures = preflight.check_copilot(spec)
    assert any("timeout" in item and spec.claims[0] in item for item in failures)
    assert all(path not in calls for path in spec.claims[1:])


@pytest.mark.parametrize("failure", [URLError("connection refused"), ConnectionResetError("connection reset")])
def test_connection_failure_reported(monkeypatch: pytest.MonkeyPatch, failure: Exception) -> None:
    spec = preflight.SPECS["trading"]
    calls = _mock_http(monkeypatch, spec, {spec.claims[0]: failure})
    assert any("connection_error" in item and spec.claims[0] in item for item in preflight.check_copilot(spec))
    assert all(path not in calls for path in spec.claims[1:])


def _assert_missing_route_falls_back(monkeypatch: pytest.MonkeyPatch, status: int) -> None:
    spec = preflight.SPECS["trading"]
    calls = _mock_http(monkeypatch, spec, {spec.claims[0]: _http_failure(status)})
    assert preflight.check_copilot(spec) == []
    assert spec.claims[0] in calls and spec.claims[1] in calls
    assert spec.claims[2] not in calls


def test_404_fallback_still_works(monkeypatch: pytest.MonkeyPatch) -> None:
    _assert_missing_route_falls_back(monkeypatch, 404)


def test_405_fallback_still_works(monkeypatch: pytest.MonkeyPatch) -> None:
    _assert_missing_route_falls_back(monkeypatch, 405)


@pytest.mark.parametrize("status", [400, 401, 403, 423, 500, 502])
def test_non_route_http_errors_preserve_status(monkeypatch: pytest.MonkeyPatch, status: int) -> None:
    spec = preflight.SPECS["trading"]
    calls = _mock_http(monkeypatch, spec, {spec.claims[0]: _http_failure(status)})
    with pytest.raises(preflight.PreflightApiError) as caught:
        preflight._first_available(preflight.PreflightClient(), spec, spec.claims)
    assert caught.value.status == status
    assert caught.value.classification == "http_error"
    assert calls == [spec.claims[0]]


@pytest.mark.parametrize("payload", [b"not JSON", b"\xff"])
def test_invalid_response_reported_without_fallback(monkeypatch: pytest.MonkeyPatch, payload: bytes) -> None:
    spec = preflight.SPECS["trading"]
    calls = _mock_http(monkeypatch, spec, {spec.claims[0]: payload})
    assert any("invalid_response" in item for item in preflight.check_copilot(spec))
    assert all(path not in calls for path in spec.claims[1:])


def test_unknown_runtime_failure_is_reported(monkeypatch: pytest.MonkeyPatch) -> None:
    spec = preflight.SPECS["trading"]
    calls = _mock_http(monkeypatch, spec, {spec.claims[0]: RuntimeError("original failure")})
    assert any("client_error" in item and "original failure" in item for item in preflight.check_copilot(spec))
    assert all(path not in calls for path in spec.claims[1:])


def test_request_failure_produces_nonzero_cli_exit(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    spec = preflight.SPECS["trading"]
    _mock_http(monkeypatch, spec, {spec.health[0]: _http_failure(503)})
    assert preflight.main(["--copilots", "trading"]) == 1
    output = capsys.readouterr().out
    assert "DEMO TRUTH PREFLIGHT: FAIL" in output and "HTTP 503" in output


def test_f26_list_response_scanned(monkeypatch: pytest.MonkeyPatch) -> None:
    from copilot_sdk.evidence.f26 import scan_for_sample

    payload = [{"provenance": "sample", "metric": 0.9},
               {"source": "demo_fixture", "metrics": [{"accuracy": 0.8}]}]
    scanned: list[dict[str, Any]] = []

    def scan(item: dict[str, Any]) -> list[str]:
        scanned.append(item)
        return list(scan_for_sample(item))

    monkeypatch.setattr(preflight, "scan_for_sample", scan)
    failures: list[str] = []
    preflight._check_no_sample("trading", "/metrics", payload, failures)
    assert scanned == payload
    assert len(failures) == 2
    assert "F-26" in failures[0] and "/metrics[0]" in failures[0]
    assert "F-26" in failures[1] and "/metrics[1]" in failures[1] and "metrics[0].accuracy" in failures[1]


@pytest.mark.parametrize("unexpected", ["not a dict", None, 12, ["nested list"]])
def test_f26_mixed_list_warning(capsys: pytest.CaptureFixture[str], unexpected: Any) -> None:
    failures: list[str] = []
    preflight._check_no_sample("trading", "/metrics", [{"provenance": "sample", "metric": 0.9}, unexpected], failures)
    assert len(failures) == 1 and "/metrics[0]" in failures[0]
    warning = capsys.readouterr().err
    assert "WARNING:" in warning and "/metrics[1]" in warning and "unexpected metric response shape" in warning


@pytest.mark.parametrize("payload", ["OK", None, 42, True])
def test_f26_non_dict_non_list_warning(capsys: pytest.CaptureFixture[str], payload: Any) -> None:
    failures: list[str] = []
    preflight._check_no_sample("trading", "/metrics", payload, failures)
    warning = capsys.readouterr().err
    assert "WARNING:" in warning and "trading /metrics" in warning and type(payload).__name__ in warning
    assert failures == []  # Unexpected shapes warn; this helper does not block.


def test_f26_dict_still_works() -> None:
    failures: list[str] = []
    preflight._check_no_sample("trading", "/metrics", {"provenance": "sample", "nested": {"accuracy": 0.9}}, failures)
    assert len(failures) == 1 and "F-26" in failures[0] and "nested.accuracy" in failures[0]


def test_f26_valid_list_passes_without_warning(capsys: pytest.CaptureFixture[str]) -> None:
    failures: list[str] = []
    preflight._check_no_sample("trading", "/metrics", [{"provenance": "observed", "metric": 0.9},
                                                         {"verified_count": 20}], failures)
    assert failures == []
    assert capsys.readouterr().err == ""


def test_f26_list_finding_blocks_preflight() -> None:
    spec = preflight.SPECS["trading"]

    class ListMetrics(CompleteClient):
        def get(self, base_url: str, path: str) -> Any:
            if path == self.spec.metrics[-1]:
                return [{"provenance": "sample", "metric": 0.9}]
            return super().get(base_url, path)

    failures = preflight.check_copilot(spec, ListMetrics(spec))
    assert any("F-26" in failure and spec.metrics[-1] + "[0]" in failure for failure in failures)


def test_nested_lists_preserve_f26_and_f27_checks(capsys: pytest.CaptureFixture[str]) -> None:
    failures: list[str] = []
    preflight._check_no_sample("trading", "/metrics", [[
        {"provenance": "sample", "accuracy": 0.9},
        {"evidence_label": "measured", "source": "synthetic", "accuracy": 0.8},
    ]], failures)
    assert any("F-26" in failure and "/metrics[0][0]" in failure for failure in failures)
    assert any("F-27" in failure and "/metrics[0][1]" in failure for failure in failures)
    assert "unexpected metric response shape list" in capsys.readouterr().err


@pytest.mark.parametrize("copilot", ["soc", "s2p", "trading", "purchasing", "dataops"])
def test_shared_promotion_records_preserve_all_copilot_identities(copilot: str) -> None:
    from copilot_sdk.promotion.core import PromotionRecord, PromotionStage

    spec = preflight.SPECS[copilot]
    record = PromotionRecord("record-1", copilot, "decision-class", current_stage=PromotionStage.SHADOWING)
    payload = {"records": [record.to_dict()], "observation_only": True}
    assert preflight.check_copilot(spec, ArtifactClient(spec, {"promotions": payload})) == []


def test_http_error_reports_full_url_status_and_body(monkeypatch: pytest.MonkeyPatch) -> None:
    spec = replace(preflight.SPECS["trading"], url="http://backend.test:8010")
    stream = io.BytesIO(b'{"detail":"backend starting"}\n')
    failure = HTTPError(spec.url + spec.claims[0], 503, "Service Unavailable", Message(), stream)
    calls = _mock_http(monkeypatch, spec, {spec.claims[0]: failure})
    failures = preflight.check_copilot(spec)
    diagnostic = next(item for item in failures if "http_error" in item)
    assert "HTTP 503 Service Unavailable" in diagnostic
    assert "GET " + spec.url + spec.claims[0] in diagnostic
    assert '{"detail":"backend starting"}' in diagnostic
    assert "\\n" in diagnostic and "\n" not in diagnostic
    assert all(path not in calls for path in spec.claims[1:])
    assert stream.closed


def test_http_error_body_read_is_bounded(monkeypatch: pytest.MonkeyPatch) -> None:
    spec = preflight.SPECS["trading"]
    failure = _http_failure(503)
    read_sizes: list[int] = []

    def read(size: int) -> bytes:
        read_sizes.append(size)
        return (b"x" * 512 + b"PRIVATE_TAIL")[:size]

    monkeypatch.setattr(failure, "read", read)
    _mock_http(monkeypatch, spec, {spec.claims[0]: failure})
    with pytest.raises(preflight.PreflightApiError) as caught:
        preflight._first_available(preflight.PreflightClient(), spec, spec.claims)
    diagnostic = str(caught.value)
    assert read_sizes == [513]
    assert "x" * 512 + "... [truncated]" in diagnostic
    assert "PRIVATE_TAIL" not in diagnostic
    assert caught.value.status == 503


def test_http_error_empty_body_is_explicit(monkeypatch: pytest.MonkeyPatch) -> None:
    spec = preflight.SPECS["trading"]
    _mock_http(monkeypatch, spec, {spec.claims[0]: _http_failure(503)})
    with pytest.raises(preflight.PreflightApiError) as caught:
        preflight._first_available(preflight.PreflightClient(), spec, spec.claims)
    assert "body=<empty>" in str(caught.value)
    assert caught.value.status == 503


def test_http_error_invalid_utf8_retains_status(monkeypatch: pytest.MonkeyPatch) -> None:
    spec = preflight.SPECS["trading"]
    stream = io.BytesIO(b"backend \xff unavailable")
    failure = HTTPError(spec.url + spec.claims[0], 503, "Service Unavailable", Message(), stream)
    _mock_http(monkeypatch, spec, {spec.claims[0]: failure})
    with pytest.raises(preflight.PreflightApiError) as caught:
        preflight._first_available(preflight.PreflightClient(), spec, spec.claims)
    assert "backend \ufffd unavailable" in str(caught.value)
    assert caught.value.status == 503 and caught.value.classification == "http_error"
    assert caught.value.__cause__ is failure
    assert stream.closed


@pytest.mark.parametrize("body_error", [TimeoutError("body timed out"), OSError("body reset"),
                                        preflight.HTTPException("incomplete body")])
def test_http_body_read_failure_preserves_original_http_error(
    monkeypatch: pytest.MonkeyPatch, body_error: Exception,
) -> None:
    spec = preflight.SPECS["trading"]
    failure = _http_failure(503)

    def read(size: int) -> bytes:
        raise body_error

    monkeypatch.setattr(failure, "read", read)
    calls = _mock_http(monkeypatch, spec, {spec.claims[0]: failure})
    failures = preflight.check_copilot(spec)
    diagnostic = next(item for item in failures if "http_error" in item)
    assert "HTTP 503" in diagnostic and "body=<unavailable:" in diagnostic
    assert str(body_error) in diagnostic and spec.url + spec.claims[0] in diagnostic
    assert all(path not in calls for path in spec.claims[1:])


def test_timeout_diagnostic_includes_full_request_url(monkeypatch: pytest.MonkeyPatch) -> None:
    spec = replace(preflight.SPECS["dataops"], url="http://backend.test:8030")
    calls = _mock_http(monkeypatch, spec, {spec.claims[0]: TimeoutError("timed out")})
    failures = preflight.check_copilot(spec)
    assert any("[timeout]" in item and spec.url + spec.claims[0] in item for item in failures)
    assert all(path not in calls for path in spec.claims[1:])


def test_http_body_close_failure_preserves_original_http_error(monkeypatch: pytest.MonkeyPatch) -> None:
    spec = preflight.SPECS["trading"]
    failure = _http_failure(503)

    def close() -> None:
        raise OSError("close failed")

    monkeypatch.setattr(failure, "close", close)
    calls = _mock_http(monkeypatch, spec, {spec.claims[0]: failure})
    with pytest.raises(preflight.PreflightApiError) as caught:
        preflight._first_available(preflight.PreflightClient(), spec, spec.claims)
    assert caught.value.status == 503 and caught.value.classification == "http_error"
    assert "close failed: OSError" in str(caught.value)
    assert calls == [spec.claims[0]]


def test_f26_empty_list_has_no_warning(capsys: pytest.CaptureFixture[str]) -> None:
    failures: list[str] = []
    preflight._check_no_sample("trading", "/metrics", [], failures)
    assert failures == [] and capsys.readouterr().err == ""


def test_f26_all_non_dict_list_warns_for_each_element(capsys: pytest.CaptureFixture[str]) -> None:
    failures: list[str] = []
    preflight._check_no_sample("trading", "/metrics", [None, 12, "invalid"], failures)
    warnings = capsys.readouterr().err
    assert failures == [] and warnings.count("WARNING:") == 3
    assert all(f"/metrics[{index}]" in warnings for index in range(3))


def test_f26_scans_dict_after_invalid_list_element(capsys: pytest.CaptureFixture[str]) -> None:
    failures: list[str] = []
    preflight._check_no_sample("trading", "/metrics", [None, {"provenance": "sample", "accuracy": 0.9}], failures)
    assert "/metrics[0]" in capsys.readouterr().err
    assert len(failures) == 1 and "F-26" in failures[0] and "/metrics[1]" in failures[0]
