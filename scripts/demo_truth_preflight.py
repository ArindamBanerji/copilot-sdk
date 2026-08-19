#!/usr/bin/env python
"""Truth checks for the live demo.

This is deliberately a read-only checker.  It never repairs state and never
turns synthetic data into a measured claim; missing proof surfaces are errors.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass
from typing import Any, Iterable
from urllib import error, request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

try:
    from copilot_sdk.evidence.f26 import scan_for_sample
except ImportError:  # pragma: no cover - only useful for a broken checkout
    scan_for_sample = None


@dataclass(frozen=True)
class CopilotSpec:
    name: str
    url: str
    health: tuple[str, ...]
    trajectory: tuple[str, ...]
    claims: tuple[str, ...]
    twins: tuple[str, ...]
    promotions: tuple[str, ...]
    metrics: tuple[str, ...]


def _url(name: str, port: int) -> str:
    return os.environ.get("%s_URL" % name.upper(), "http://127.0.0.1:%s" % port)


SPECS = {
    "soc": CopilotSpec("soc", _url("soc", 8001), ("/health",), ("/api/soc/learning-health",),
                        ("/api/soc/claims", "/api/evidence/summary"), ("/api/soc/frozen-twin", "/api/frozen-twin/status"),
                        ("/api/soc/promotion", "/api/promotion"), ("/api/soc/learning-health",)),
    "trading": CopilotSpec("trading", _url("trading", 8010), ("/health",), ("/api/trajectory",),
                            ("/api/trading/claims", "/api/evidence/summary", "/api/trading/evidence"),
                            ("/api/trading/frozen-twin", "/api/frozen-twin/status", "/api/twin/status"),
                            ("/api/trading/promotion/dashboard", "/api/trading/promotion"),
                            ("/api/trajectory", "/api/trading/learning-health")),
    "purchasing": CopilotSpec("purchasing", _url("purchasing", 8020), ("/health",), ("/api/trajectory",),
                               ("/api/purchasing/claims", "/api/evidence/summary", "/api/purchasing/proof-ledger"),
                               ("/api/purchasing/frozen-twin", "/api/frozen-twin/status"),
                               ("/api/purchasing/promotion",),
                               ("/api/purchasing/proof-ledger", "/api/purchasing/day-0-readiness")),
    "dataops": CopilotSpec("dataops", _url("dataops", 8030), ("/health",), ("/api/trajectory",),
                            ("/api/dataops/claims", "/api/evidence/summary"), ("/api/dataops/frozen-twin/status",),
                            ("/api/dataops/promotion",), ("/api/dataops/claims", "/api/dataops/holdout/status")),
    "s2p": CopilotSpec("s2p", _url("s2p", 8002), ("/health",), ("/api/trajectory", "/api/s2p/trajectory"),
                        ("/api/s2p/claims", "/api/evidence/summary", "/api/s2p/evidence"),
                        ("/api/s2p/frozen-twin", "/api/frozen-twin/status", "/api/twin/status"),
                        ("/api/s2p/promotion", "/api/promotion"), ("/api/s2p/trajectory",)),
}


class PreflightClient:
    def get(self, base_url: str, path: str) -> Any:
        req = request.Request(base_url.rstrip("/") + path, headers={"Accept": "application/json"})
        try:
            with request.urlopen(req, timeout=10) as response:
                raw = response.read().decode("utf-8")
                return json.loads(raw) if raw else {}
        except (error.HTTPError, error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            raise RuntimeError(str(exc)) from exc


def _first_available(client: PreflightClient, spec: CopilotSpec, paths: Iterable[str]) -> tuple[str, Any] | None:
    for path in paths:
        try:
            return path, client.get(spec.url, path)
        except RuntimeError:
            continue
    return None


def _walk(value: Any) -> Iterable[dict[str, Any]]:
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from _walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk(child)


def _has_positive(value: Any, keys: tuple[str, ...]) -> bool:
    for item in _walk(value):
        for key in keys:
            raw = item.get(key)
            try:
                if raw is not None and float(raw) > 0:
                    return True
            except (TypeError, ValueError):
                continue
    return False


def _has_green(value: Any) -> bool:
    for item in _walk(value):
        for key in ("phase", "status", "conservation_status", "conservation_phase"):
            if str(item.get(key, "")).upper() == "GREEN":
                return True
    return False


def _has_verified(value: Any) -> bool:
    return _has_positive(value, ("verified_count", "verified_outcomes", "outcomes_verified", "confirmed_count"))


def _check_no_sample(name: str, path: str, payload: Any, failures: list[str]) -> None:
    if not isinstance(payload, (dict, list)):
        return
    if scan_for_sample is not None and isinstance(payload, dict):
        findings = scan_for_sample(payload)
        if findings:
            failures.append("%s %s: F-26 sample/demo-fixture metric (%s)" % (name, path, findings))
    for item in _walk(payload):
        for key, value in item.items():
            if key in {"evidence_label", "label", "provenance"} and str(value).lower() in {"measured", "observed"}:
                source = str(item.get("source") or item.get("data_source") or item.get("provenance") or "").lower()
                if "synthetic" in source or "sample" in source or "fixture" in source or "demo" in source:
                    failures.append("%s %s: F-27 synthetic value labeled measured" % (name, path))


def check_copilot(spec: CopilotSpec, client: PreflightClient | None = None) -> list[str]:
    client = client or PreflightClient()
    failures: list[str] = []
    health = _first_available(client, spec, spec.health)
    if health is None:
        return ["%s: backend unavailable" % spec.name]
    trajectory = _first_available(client, spec, spec.trajectory)
    if trajectory is None:
        failures.append("%s: verified trajectory endpoint unavailable" % spec.name)
    else:
        _, payload = trajectory
        _check_no_sample(spec.name, spec.trajectory[0], payload, failures)
        if not _has_positive(payload, ("current_iks", "iks", "intelligence_knowledge_score")):
            failures.append("%s: IKS is not positive" % spec.name)
        if not _has_verified(payload):
            failures.append("%s: no verified outcomes reported" % spec.name)
        if not _has_green(payload):
            failures.append("%s: conservation is not GREEN" % spec.name)
    metrics_seen = False
    for path in spec.metrics:
        try:
            payload = client.get(spec.url, path)
        except RuntimeError:
            continue
        metrics_seen = True
        _check_no_sample(spec.name, path, payload, failures)
    if not metrics_seen:
        failures.append("%s: no metric/evidence surface available" % spec.name)
    if _first_available(client, spec, spec.claims) is None:
        failures.append("%s: claim registry unavailable" % spec.name)
    if _first_available(client, spec, spec.twins) is None:
        failures.append("%s: Frozen Twin unavailable" % spec.name)
    if _first_available(client, spec, spec.promotions) is None:
        failures.append("%s: promotion records unavailable" % spec.name)
    return failures


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Read-only demo truth preflight")
    parser.add_argument("--copilots", nargs="+", choices=sorted(SPECS), default=sorted(SPECS))
    parser.add_argument("--dry-run", action="store_true", help="Validate configuration without contacting backends")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv if argv is not None else sys.argv[1:])
    if args.dry_run:
        print("preflight configuration: OK (%s)" % ", ".join(args.copilots))
        return 0
    failures: list[str] = []
    for name in args.copilots:
        failures.extend(check_copilot(SPECS[name]))
    if failures:
        print("DEMO TRUTH PREFLIGHT: FAIL")
        for failure in failures:
            print("  FAIL: %s" % failure)
        return 1
    print("DEMO TRUTH PREFLIGHT: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
