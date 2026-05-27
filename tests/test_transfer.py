import json
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from copilot_sdk.backend.transfer import (
    TransferDetector,
    detect_transfer_opportunities,
    load_fingerprints,
    load_fingerprints_with_warnings,
    save_fingerprint,
)
from copilot_sdk.backend.transfer_router import create_transfer_router


def _fingerprint(domain: str, factors: dict[str, float]) -> dict:
    return {
        "domain": domain,
        "fingerprint": {
            "factors": [
                {"name": name, "sigma": sigma, "weight": 1.0, "interpretation": "test"}
                for name, sigma in factors.items()
            ],
            "overall_win_rate": 0.5,
            "per_category_precision": {},
            "decisions_analyzed": 10,
        },
    }


def test_detector_finds_source_low_target_high_shared_factor() -> None:
    opportunities = detect_transfer_opportunities(
        {
            "trading": _fingerprint("trading", {"market_regime": 0.12}),
            "dataops": _fingerprint("dataops", {"market_regime": 0.45}),
        }
    )

    assert opportunities == [
        {
            "source_domain": "trading",
            "target_domain": "dataops",
            "factor": "market_regime",
            "source_sigma": 0.12,
            "target_sigma": 0.45,
            "direction": "trading->dataops",
            "recommendation": "warm_start_factor",
            "reason": "trading has learned market_regime while dataops remains noisy",
        }
    ]


def test_detector_detects_reverse_direction_from_other_to_own() -> None:
    opportunities = TransferDetector().detect(
        _fingerprint("trading", {"market_regime": 0.45}),
        {"dataops": _fingerprint("dataops", {"market_regime": 0.12})},
    )

    assert opportunities[0]["direction"] == "dataops->trading"


def test_no_overlap_returns_no_opportunities() -> None:
    assert (
        detect_transfer_opportunities(
            {
                "trading": _fingerprint("trading", {"market_regime": 0.12}),
                "dataops": _fingerprint("dataops", {"impact_scope": 0.45}),
            }
        )
        == []
    )


def test_both_learned_returns_no_transfer_needed() -> None:
    assert (
        detect_transfer_opportunities(
            {
                "trading": _fingerprint("trading", {"shared": 0.12}),
                "dataops": _fingerprint("dataops", {"shared": 0.10}),
            }
        )
        == []
    )


def test_both_unlearned_returns_no_transfer_source() -> None:
    assert (
        detect_transfer_opportunities(
            {
                "trading": _fingerprint("trading", {"shared": 0.50}),
                "dataops": _fingerprint("dataops", {"shared": 0.45}),
            }
        )
        == []
    )


def test_threshold_boundaries_are_strict() -> None:
    assert (
        detect_transfer_opportunities(
            {
                "source": _fingerprint("source", {"shared": 0.15}),
                "target": _fingerprint("target", {"shared": 0.45}),
            }
        )
        == []
    )
    assert (
        detect_transfer_opportunities(
            {
                "source": _fingerprint("source", {"shared": 0.14}),
                "target": _fingerprint("target", {"shared": 0.30}),
            }
        )
        == []
    )


def test_multiple_domains_aggregate_opportunities() -> None:
    opportunities = detect_transfer_opportunities(
        {
            "a": _fingerprint("a", {"shared": 0.10}),
            "b": _fingerprint("b", {"shared": 0.40}),
            "c": _fingerprint("c", {"shared": 0.50}),
        }
    )

    assert [item["direction"] for item in opportunities] == ["a->b", "a->c"]


def test_malformed_or_missing_factors_are_ignored_safely() -> None:
    opportunities = detect_transfer_opportunities(
        {
            "a": {"domain": "a", "fingerprint": {"factors": [{"name": "shared", "sigma": "bad"}]}},
            "b": {"domain": "b", "fingerprint": {"factors": None}},
        }
    )

    assert opportunities == []


def test_save_and_load_fingerprint_roundtrip(tmp_path: Path) -> None:
    path = save_fingerprint("Trading", {"factors": [{"name": "x", "sigma": 0.1}]}, tmp_path)

    assert path == tmp_path / "trading.json"
    loaded = load_fingerprints(tmp_path)
    assert loaded["trading"]["domain"] == "trading"
    assert loaded["trading"]["fingerprint"]["factors"][0]["name"] == "x"


def test_load_fingerprints_skips_malformed_json(tmp_path: Path) -> None:
    (tmp_path / "bad.json").write_text("{", encoding="utf-8")
    save_fingerprint("dataops", {"factors": []}, tmp_path)

    loaded, warnings = load_fingerprints_with_warnings(tmp_path)

    assert sorted(loaded) == ["dataops"]
    assert warnings[0]["file"] == "bad.json"


class FakeScorer:
    _domain = "trading"


def _client(tmp_path: Path) -> TestClient:
    app = FastAPI()
    app.include_router(create_transfer_router(FakeScorer(), fingerprint_base_path=tmp_path))
    return TestClient(app)


def test_transfer_router_opportunities_returns_200_with_no_fingerprint_files(tmp_path: Path) -> None:
    response = _client(tmp_path).get("/api/transfer/opportunities")

    assert response.status_code == 200
    assert response.json()["status"] == "missing_fingerprints"
    assert response.json()["opportunities"] == []


def test_transfer_router_status_returns_200_with_no_fingerprint_files(tmp_path: Path) -> None:
    response = _client(tmp_path).get("/api/transfer/status")

    assert response.status_code == 200
    assert response.json() == {"warm_started": False}


def test_transfer_router_returns_opportunities_from_temp_fingerprints(tmp_path: Path) -> None:
    save_fingerprint("trading", {"factors": [{"name": "shared", "sigma": 0.5}]}, tmp_path)
    save_fingerprint("dataops", {"factors": [{"name": "shared", "sigma": 0.1}]}, tmp_path)

    payload = _client(tmp_path).get("/api/transfer/opportunities").json()

    assert payload["status"] == "opportunities_available"
    assert payload["own_fingerprint_present"] is True
    assert payload["opportunities"][0]["direction"] == "dataops->trading"


def test_transfer_router_hides_other_domain_opportunities_when_own_fingerprint_missing(
    tmp_path: Path,
) -> None:
    save_fingerprint("dataops", {"factors": [{"name": "shared", "sigma": 0.1}]}, tmp_path)
    save_fingerprint("purchasing", {"factors": [{"name": "shared", "sigma": 0.5}]}, tmp_path)

    response = _client(tmp_path).get("/api/transfer/opportunities")
    payload = response.json()

    assert response.status_code == 200
    assert payload["status"] == "missing_own_fingerprint"
    assert payload["own_fingerprint_present"] is False
    assert payload["opportunity_count"] == 0
    assert payload["opportunities"] == []


def test_endpoint_response_is_json_safe_with_malformed_file(tmp_path: Path) -> None:
    (tmp_path / "bad.json").write_text("{", encoding="utf-8")

    response = _client(tmp_path).get("/api/transfer/opportunities")

    assert response.status_code == 200
    json.dumps(response.json())
    assert response.json()["warnings"][0]["file"] == "bad.json"
