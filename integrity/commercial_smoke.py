"""HTTP smoke checks for a running five-copilot stack.

Scoring POSTs can persist decisions. This CLI neither learns from outcomes nor
starts services. SOC requires an existing alert ID, configurable with --soc-alert-id.
"""

from __future__ import annotations

import argparse
import importlib
import json
import math
from dataclasses import dataclass
from http.client import HTTPException
from types import ModuleType
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener


def _optional_requests() -> ModuleType | None:
    try:
        return importlib.import_module("requests")
    except ImportError:
        return None


_requests = _optional_requests()


@dataclass(frozen=True)
class Check:
    base_url: str
    endpoint: str
    payload: dict[str, Any]
    expected_service: str
    expected_fields: tuple[str, ...] = ()
    identity_endpoint: str = "/health"


_SCORE_FIELDS = (
    "decision_id", "action", "action_index", "confidence", "probabilities",
    "category", "factors", "engine",
)


def _score_payload(category: str, factor_names: tuple[str, ...]) -> dict[str, Any]:
    return {
        "category": category,
        "factors": dict.fromkeys(factor_names, 0.5),
        "metadata": {"source": "commercial_smoke"},
    }


CHECKS: dict[str, Check] = {
    "soc": Check("http://localhost:8001", "/api/alert/analyze",
                 {"alert_id": "SMOKE-TEST-001"}, "soc"),
    "s2p": Check("http://localhost:8002", "/api/s2p/score",
                 {"event_id": "SMOKE-TEST-INV-001", "category": "price_variance",
                  "amount": 100.0, "supplier_id": "SMOKE-TEST-SUPPLIER",
                  "match_status": 0.5, "amount_variance_ratio": 0.5,
                  "duplicate_score": 0.5, "supplier_exception_history": 0.5,
                  "payment_terms_impact": 0.5, "commodity_index_correlation": 0.5,
                  "tax_regulatory_compliance": 0.5, "environmental_risk": 0.5,
                  "context": {"source": "commercial_smoke"}}, "s2p"),
    "trading": Check(
        "http://localhost:8010", "/api/score",
        _score_payload("trend_following", (
            "signal_alignment", "market_regime", "position_sizing", "timing_quality",
            "risk_reward_actual", "emotional_indicator", "signal_confidence",
            "options_delta_exposure", "options_iv_percentile", "options_gamma_risk",
        )), "trading", _SCORE_FIELDS,
    ),
    "purchasing": Check(
        "http://localhost:8020", "/api/score",
        _score_payload("protein", (
            "expected_demand", "day_of_week", "weather_forecast", "event_flag",
            "historical_waste", "supplier_lead_time", "price_memory_index",
        )), "purchasing", _SCORE_FIELDS,
    ),
    "dataops": Check(
        "http://localhost:8030", "/api/score",
        _score_payload("schema_change", (
            "impact_scope", "source_reliability", "recurrence_frequency",
            "downstream_urgency", "data_freshness", "business_criticality",
        )), "dataops", _SCORE_FIELDS,
    ),
}


@dataclass(frozen=True)
class CheckResult:
    copilot: str
    endpoint: str
    passed: bool
    detail: str


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(
        self, req: Request, fp: Any, code: int, msg: str, headers: Any, newurl: str,
    ) -> None:
        return None


def _http_request(
    method: str, url: str, payload: dict[str, Any] | None, timeout: float,
) -> tuple[int, str]:
    """Use bounded connect/read waits; do not retry or redirect scoring POSTs."""
    headers = {"Accept": "application/json"}
    if _requests is not None:
        try:
            with _requests.request(
                method, url, json=payload, headers=headers,
                timeout=(timeout, timeout), allow_redirects=False,
            ) as response:
                return int(response.status_code), str(response.text)
        except _requests.exceptions.Timeout as exc:
            raise TimeoutError(f"connection/read timeout ({timeout:g}s)") from exc
        except _requests.exceptions.RequestException as exc:
            raise OSError(f"HTTP connection/request failed: {exc}") from exc

    data = None if payload is None else json.dumps(payload).encode("utf-8")
    if data is not None:
        headers["Content-Type"] = "application/json"
    request = Request(url, data=data, headers=headers, method=method)
    try:
        with build_opener(_NoRedirect()).open(request, timeout=timeout) as response:
            return int(response.status), response.read().decode("utf-8", errors="replace")
    except HTTPError as exc:
        with exc:
            return exc.code, exc.read().decode("utf-8", errors="replace")
    except URLError as exc:
        if isinstance(exc.reason, TimeoutError):
            raise TimeoutError(f"connection/read timeout ({timeout:g}s)") from exc
        raise OSError(f"HTTP connection/request failed: {exc.reason}") from exc
    except HTTPException as exc:
        raise OSError(f"incomplete HTTP response: {exc}") from exc


def _json_object(method: str, url: str, payload: dict[str, Any] | None, timeout: float) -> dict[str, Any]:
    try:
        status, body = _http_request(method, url, payload, timeout)
    except TimeoutError as exc:
        raise ValueError(f"{method} {url}: timeout ({timeout:g}s): {exc}") from exc
    except OSError as exc:
        raise ValueError(f"{method} {url}: connection error: {exc}") from exc
    if not 200 <= status < 300:
        raise ValueError(f"{method} {url}: HTTP {status}: {body[:200]!r}")
    try:
        result = json.loads(body)
    except ValueError as exc:
        raise ValueError(f"{method} {url}: non-JSON response: {body[:200]!r}") from exc
    if not isinstance(result, dict):
        raise ValueError(f"{method} {url}: expected JSON object, got {type(result).__name__}")
    return dict(result)


def _identity_error(response: dict[str, Any], expected: str, *, required: bool) -> str | None:
    # Health exposes a canonical domain alongside a human-facing service name.
    # A present domain is authoritative, including when it is invalid or empty.
    for key in ("domain", "service"):
        if key not in response:
            continue
        actual = response[key]
        if actual != expected:
            return f"wrong service identity: expected {expected!r}, got {actual!r} ({key})"
        return None
    if required:
        return f"missing service identity: expected {expected!r} in domain or service"
    return None


def run_check(
    copilot: str, *, base_url: str | None = None, timeout: float = 10.0,
    soc_alert_id: str | None = None,
) -> CheckResult:
    """Verify identity and score response, returning a failure instead of crashing."""
    check = CHECKS[copilot]
    payload = dict(check.payload)
    if copilot == "soc" and soc_alert_id is not None:
        payload["alert_id"] = soc_alert_id
    base = (base_url if base_url is not None else check.base_url).rstrip("/")
    try:
        parsed = urlsplit(base)
        if parsed.scheme not in ("http", "https") or not parsed.hostname or parsed.query or parsed.fragment:
            raise ValueError("base URL must be an HTTP(S) URL without query or fragment")
        _ = parsed.port  # Validate malformed ports before either transport runs.
        if not math.isfinite(timeout) or timeout <= 0:
            raise ValueError("timeout must be finite and positive")
        identity = _json_object("GET", base + check.identity_endpoint, None, timeout)
        identity_error = _identity_error(identity, check.expected_service, required=True)
        if identity_error:
            raise ValueError(identity_error)
        result = _json_object("POST", base + check.endpoint, payload, timeout)
        identity_error = _identity_error(result, check.expected_service, required=False)
        if identity_error:
            raise ValueError(identity_error)
        missing = [name for name in check.expected_fields if name not in result]
        if missing:
            raise ValueError("missing expected fields: " + ", ".join(missing))
        if check.expected_fields:
            if not isinstance(result["action"], str) or not result["action"]:
                raise ValueError("invalid action: expected nonempty string")
            confidence = result["confidence"]
            if type(confidence) not in (int, float) or not math.isfinite(confidence) or not 0 <= confidence <= 1:
                raise ValueError("invalid confidence: expected a finite number in [0, 1]")
            if not isinstance(result["probabilities"], list) or not result["probabilities"]:
                raise ValueError("invalid probabilities: expected nonempty list")
            if result["category"] != check.payload["category"]:
                raise ValueError(f"wrong category: expected {check.payload['category']!r}, got {result['category']!r}")
        return CheckResult(copilot, check.endpoint, True, "identity and score response verified")
    except ValueError as exc:
        return CheckResult(copilot, check.endpoint, False, str(exc))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Check live copilot identity and scoring over HTTP.",
        epilog="Scoring POSTs may persist decisions. Use --soc-alert-id for an existing SOC alert.",
    )
    selection = parser.add_mutually_exclusive_group(required=True)
    selection.add_argument("--copilot", choices=tuple(CHECKS))
    selection.add_argument("--all", action="store_true", help="check all five copilots")
    parser.add_argument("--base-url", help="override base URL for --copilot (not --all)")
    parser.add_argument("--soc-alert-id", help="existing SOC alert ID for --all or --copilot soc")
    parser.add_argument("--timeout", type=float, default=10.0, help="connect/read timeout in seconds (default: 10)")
    args = parser.parse_args(argv)
    if args.all and args.base_url is not None:
        parser.error("--base-url requires --copilot")
    if args.soc_alert_id is not None:
        if not args.all and args.copilot != "soc":
            parser.error("--soc-alert-id requires --all or --copilot soc")
        if not args.soc_alert_id.strip():
            parser.error("--soc-alert-id must be nonempty")
    if not math.isfinite(args.timeout) or args.timeout <= 0:
        parser.error("--timeout must be finite and positive")
    selected = list(CHECKS) if args.all else [args.copilot]
    passed = 0
    for copilot in selected:
        result = run_check(
            copilot, base_url=args.base_url, timeout=args.timeout,
            soc_alert_id=args.soc_alert_id,
        )
        passed += int(result.passed)
        print(f"{'PASS' if result.passed else 'FAIL'} {copilot} POST {result.endpoint}: {result.detail}")
    print(f"{passed}/{len(selected)} passed")
    return 0 if passed == len(selected) else 1


if __name__ == "__main__":
    raise SystemExit(main())
