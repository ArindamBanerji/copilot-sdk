#!/usr/bin/env python
"""Pre-seed Trading, Purchasing, and DataOps copilots from repo seed files.

The script talks to the running backend APIs and intentionally uses only the
Python standard library.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, Iterable, List, NamedTuple, Optional, Tuple
from urllib import error, request

from copilot_sdk.backend.transfer import save_fingerprint


TIMEOUT_SECONDS = 10
REPO_ROOT = Path(__file__).resolve().parents[1]
PRESEED_DECISIONS_PER_COPILOT = 200
PRESEED_OVERRIDE_COUNT = 50

TRADING_FACTORS = [
    "signal_alignment",
    "market_regime",
    "position_sizing",
    "timing_quality",
    "risk_reward_actual",
    "emotional_indicator",
    # Existing Trading seeds omit this seventh factor; extract_factors defaults it to neutral 0.50.
    "signal_confidence",
]

PURCHASING_FACTORS = [
    "expected_demand",
    "day_of_week",
    "weather_forecast",
    "event_flag",
    "historical_waste",
    "supplier_lead_time",
    # Existing Purchasing seeds omit this seventh factor; extract_factors defaults it to neutral 0.50.
    "price_memory_index",
]

PURCHASING_FIELD_MAP = {
    "day_of_week": "day_of_week_factor",
}

DATAOPS_FACTORS = [
    "impact_scope",
    "source_reliability",
    "recurrence_frequency",
    "downstream_urgency",
    "data_freshness",
    "business_criticality",
]


class ApiError(RuntimeError):
    pass


class DomainConfig(NamedTuple):
    name: str
    env_var: str
    default_url: str
    seed_path: Path
    factors: List[str]
    actions: List[str]
    metadata_path: str
    field_map: Dict[str, str]


class DomainResult(NamedTuple):
    name: str
    total: int
    successes: int
    failures: int
    metadata_failures: int
    skipped: bool
    unreachable: bool
    total_reward: float


DOMAINS = [
    DomainConfig(
        name="trading",
        env_var="TRADING_URL",
        default_url="http://127.0.0.1:8010",
        seed_path=REPO_ROOT / "apps" / "trading" / "backend" / "data" / "trading_seed_v2.json",
        factors=TRADING_FACTORS,
        actions=["strong_execution", "partial_execution", "poor_execution", "skip_recommended"],
        metadata_path="/api/context/trade-metadata",
        field_map={},
    ),
    DomainConfig(
        name="purchasing",
        env_var="PURCHASING_URL",
        default_url="http://127.0.0.1:8020",
        seed_path=REPO_ROOT / "apps" / "purchasing" / "backend" / "data" / "purchasing_seed_v2.json",
        factors=PURCHASING_FACTORS,
        actions=["order_as_planned", "order_more", "order_less", "skip"],
        metadata_path="/api/context/order-metadata",
        field_map=PURCHASING_FIELD_MAP,
    ),
    DomainConfig(
        name="dataops",
        env_var="DATAOPS_URL",
        default_url="http://127.0.0.1:8030",
        seed_path=REPO_ROOT / "copilot_sdk" / "scoring" / "presets" / "dataops_seed.json",
        factors=DATAOPS_FACTORS,
        actions=[
            "auto_approve",
            "investigate",
            "escalate_to_owner",
            "pause_downstream",
            "refer_to_specialist",
        ],
        metadata_path="/api/context/alert-metadata",
        field_map={},
    ),
]


def api_get(base_url: str, path: str) -> Any:
    return _api_json("GET", base_url, path, None)


def api_post(base_url: str, path: str, body: Dict[str, Any]) -> Any:
    return _api_json("POST", base_url, path, body)


def _api_json(method: str, base_url: str, path: str, body: Optional[Dict[str, Any]]) -> Any:
    url = base_url.rstrip("/") + path
    data = None
    headers = {"Accept": "application/json"}
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"

    req = request.Request(url, data=data, headers=headers, method=method)
    try:
        with request.urlopen(req, timeout=TIMEOUT_SECONDS) as response:
            text = response.read().decode("utf-8")
            return json.loads(text) if text else {}
    except error.HTTPError as exc:
        text = _read_error_text(exc)
        raise ApiError("%s %s failed: HTTP %s %s" % (method, path, exc.code, text)) from exc
    except error.URLError as exc:
        raise ApiError("%s %s failed: %s" % (method, path, exc.reason)) from exc
    except TimeoutError as exc:
        raise ApiError("%s %s failed: timed out after %ss" % (method, path, TIMEOUT_SECONDS)) from exc
    except json.JSONDecodeError as exc:
        raise ApiError("%s %s failed: invalid JSON response" % (method, path)) from exc


def _read_error_text(exc: error.HTTPError) -> str:
    try:
        return exc.read().decode("utf-8", errors="replace")
    except Exception:
        return ""


def check_health(base_url: str) -> Tuple[bool, Any]:
    try:
        return True, api_get(base_url, "/health")
    except ApiError as exc:
        return False, str(exc)


def check_already_seeded(base_url: str) -> Tuple[bool, Dict[str, Any]]:
    trajectory = api_get(base_url, "/api/trajectory")
    return int(trajectory.get("decisions_total") or 0) >= PRESEED_DECISIONS_PER_COPILOT, trajectory


def load_trading_seed() -> List[Dict[str, Any]]:
    return load_seed(DOMAINS[0].seed_path)


def load_purchasing_seed() -> List[Dict[str, Any]]:
    return load_seed(DOMAINS[1].seed_path)


def load_dataops_seed() -> List[Dict[str, Any]]:
    return load_seed(DOMAINS[2].seed_path)


def load_seed(path: Path) -> List[Dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError("Seed file must contain a list: %s" % path)
    return [entry for entry in payload if isinstance(entry, dict)]


def expanded_seed(
    seed: List[Dict[str, Any]],
    target_count: int = PRESEED_DECISIONS_PER_COPILOT,
    start_index: int = 0,
) -> List[Dict[str, Any]]:
    if not seed:
        return []
    expanded = []
    for index in range(start_index, start_index + target_count):
        source_index = index % len(seed)
        entry = dict(seed[source_index])
        entry["_preseed_source_index"] = source_index + 1
        entry["_preseed_sequence"] = index + 1
        expanded.append(entry)
    return expanded


def selected_domains(args: argparse.Namespace) -> List[DomainConfig]:
    selected = []
    if args.trading_only:
        selected.append(DOMAINS[0])
    if args.purchasing_only:
        selected.append(DOMAINS[1])
    if args.dataops_only:
        selected.append(DOMAINS[2])
    return selected or list(DOMAINS)


def domain_url(config: DomainConfig) -> str:
    return os.environ.get(config.env_var, config.default_url)


def extract_factors(entry: Dict[str, Any], config: DomainConfig) -> Dict[str, float]:
    nested = entry.get("factors")
    nested_factors = nested if isinstance(nested, dict) else {}
    factors = {}
    for factor in config.factors:
        if factor in nested_factors:
            raw = nested_factors.get(factor)
        else:
            raw = entry.get(config.field_map.get(factor, factor))
        factors[factor] = coerce_factor(raw)
    return factors


def coerce_factor(value: Any) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return 0.5
    if number != number or number in (float("inf"), float("-inf")):
        return 0.5
    return max(0.0, min(1.0, number))


def actual_action(entry: Dict[str, Any], score: Dict[str, Any]) -> str:
    return str(entry.get("action_taken") or entry.get("direction") or score.get("action") or "")


def is_override_sequence(index: int) -> bool:
    return index % 4 == 0 and index <= PRESEED_OVERRIDE_COUNT * 4


def alternate_action(config: DomainConfig, recommended_action: str) -> str:
    for action in config.actions:
        if action != recommended_action:
            return action
    raise ValueError("no alternate action available for %s" % config.name)


def learn_action(entry: Dict[str, Any], score: Dict[str, Any], config: DomainConfig, index: int) -> Tuple[str, bool]:
    recommended_action = str(score.get("action") or actual_action(entry, score) or "")
    if not recommended_action:
        raise ValueError("missing recommended action")
    if is_override_sequence(index):
        if config.name == "trading" and recommended_action != "skip_recommended":
            return "skip_recommended", True
        return alternate_action(config, recommended_action), True
    return recommended_action, False


def outcome_for(entry: Dict[str, Any]) -> str:
    return "confirmed" if bool(entry.get("is_correct", True)) else "overridden"


def entry_label(entry: Dict[str, Any]) -> str:
    for key in ("trade_id", "order_id", "alert_id", "event_id", "ticker", "item", "dataset"):
        value = entry.get(key)
        if value:
            return "%s=%s" % (key, value)
    return "unknown-entry"


def metadata_payload(entry: Dict[str, Any], factors: Dict[str, float], score: Dict[str, Any]) -> Dict[str, Any]:
    payload = {
        key: value
        for key, value in entry.items()
        if key != "factors"
    }
    payload["decision_id"] = score.get("decision_id")
    if isinstance(entry.get("factors"), dict):
        payload["seed_factors"] = entry["factors"]
    payload["scored_factors"] = factors
    payload["score_action"] = score.get("action")
    payload["score_confidence"] = score.get("confidence")
    return payload


def seed_domain(config: DomainConfig, args: argparse.Namespace) -> DomainResult:
    base_url = domain_url(config)
    source_seed = load_seed(config.seed_path)
    seed = expanded_seed(source_seed)
    print("")
    print("== %s ==" % config.name)
    print(
        "seed: %s decisions from %s source entries in %s"
        % (len(seed), len(source_seed), config.seed_path.relative_to(REPO_ROOT))
    )
    print("url: %s" % base_url)

    healthy, health_payload = check_health(base_url)
    if not healthy:
        print("health: unreachable (%s)" % health_payload)
        return DomainResult(config.name, len(seed), 0, 1, 0, False, True, 0.0)
    print("health: ok")

    if args.dry_run:
        try:
            _already, trajectory = check_already_seeded(base_url)
            print("trajectory decisions_total: %s" % trajectory.get("decisions_total", "unknown"))
        except ApiError as exc:
            print("trajectory: unavailable (%s)" % exc)
            return DomainResult(config.name, len(seed), 0, 1, 0, False, True, 0.0)
        print("dry-run: no score/learn/metadata calls made")
        return DomainResult(config.name, len(seed), len(seed), 0, 0, False, False, 0.0)

    try:
        already_seeded, trajectory = check_already_seeded(base_url)
    except ApiError as exc:
        print("trajectory: unavailable (%s)" % exc)
        return DomainResult(config.name, len(seed), 0, 1, 0, False, True, 0.0)

    existing_decisions = int(trajectory.get("decisions_total") or 0)
    if already_seeded and not args.force:
        print(
            "already seeded: decisions_total=%s target=%s; skipping (use --force to append again)"
            % (trajectory.get("decisions_total"), PRESEED_DECISIONS_PER_COPILOT)
        )
        verify_domain(config, base_url, 0, 0, 0.0)
        return DomainResult(config.name, len(seed), 0, 0, 0, True, False, 0.0)

    if not args.force:
        remaining = max(PRESEED_DECISIONS_PER_COPILOT - existing_decisions, 0)
        seed = expanded_seed(source_seed, remaining, start_index=max(existing_decisions, 0))
        if existing_decisions > 0:
            print(
                "top-up: decisions_total=%s target=%s remaining=%s"
                % (existing_decisions, PRESEED_DECISIONS_PER_COPILOT, len(seed))
            )

    successes = 0
    failures = 0
    metadata_failures = 0
    total_reward = 0.0
    start = time.time()

    for index, entry in enumerate(seed, start=1):
        label = entry_label(entry)
        seed_sequence = int(entry.get("_preseed_sequence") or index)
        try:
            category = entry.get("category")
            if not category:
                raise ValueError("missing category")
            factors = extract_factors(entry, config)
            score_body = {
                "category": category,
                "factors": factors,
                "context": {
                    "seed_domain": config.name,
                    "seed_index": seed_sequence,
                    "seed_id": label,
                },
            }
            score = api_post(base_url, "/api/score", score_body)
            decision_id = score.get("decision_id")
            if not decision_id:
                raise ValueError("score response missing decision_id")
            action, is_override = learn_action(entry, score, config, seed_sequence)
            if not action:
                raise ValueError("missing actual_action")
            learn = api_post(
                base_url,
                "/api/learn",
                {
                    "decision_id": decision_id,
                    "actual_action": action,
                    "outcome": "overridden" if is_override else "confirmed",
                    "context": {
                        "seed_domain": config.name,
                        "seed_index": seed_sequence,
                        "seed_id": label,
                        "source_seed_index": entry.get("_preseed_source_index"),
                        "is_preseed_override": is_override,
                        "previous_reward": None,
                    },
                },
            )
            total_reward += float(learn.get("reward") or 0.0)
            try:
                api_post(base_url, config.metadata_path, metadata_payload(entry, factors, score))
            except Exception as exc:
                metadata_failures += 1
                print("  warning: metadata failed for %s #%s %s: %s" % (config.name, index, label, exc))
            successes += 1
            outcome_label = "override" if is_override else "confirm"
            print("  ok #%s %s -> %s %s reward=%s" % (index, label, action, outcome_label, learn.get("reward")))
        except Exception as exc:
            failures += 1
            print("  failed #%s %s: %s" % (index, label, exc))

    elapsed = time.time() - start
    print("seeded %s/%s in %.1fs" % (successes, len(seed), elapsed))
    verify_domain(config, base_url, successes, failures, total_reward)
    return DomainResult(config.name, len(seed), successes, failures, metadata_failures, False, False, total_reward)


def verify_domain(
    config: DomainConfig,
    base_url: str,
    successes: int,
    failures: int,
    total_reward: float,
) -> None:
    try:
        trajectory = api_get(base_url, "/api/trajectory")
    except ApiError as exc:
        print("verify trajectory failed: %s" % exc)
        trajectory = {}
    try:
        fingerprint = api_get(base_url, "/api/fingerprint")
    except ApiError as exc:
        print("verify fingerprint failed: %s" % exc)
        fingerprint = {}
    if fingerprint:
        try:
            path = save_fingerprint(config.name, fingerprint, source_url=base_url.rstrip("/") + "/api/fingerprint")
            print("fingerprint exported: %s" % path.relative_to(REPO_ROOT))
        except Exception as exc:
            print("warning: fingerprint export failed: %s" % exc)

    factors = fingerprint.get("factors") or []
    active = any(float(factor.get("weight") or 0.0) > 0.0 for factor in factors if isinstance(factor, dict))
    print(
        "verify: successes=%s failures=%s iks=%s decisions_total=%s fingerprint=%s total_reward=%.6f"
        % (
            successes,
            failures,
            trajectory.get("current_iks", "unknown"),
            trajectory.get("decisions_total", "unknown"),
            "active" if active else "cold",
            total_reward,
        )
    )


def print_summary(results: Iterable[DomainResult]) -> int:
    print("")
    print("== summary ==")
    exit_code = 0
    for result in results:
        status = "skipped" if result.skipped else "failed" if result.failures or result.unreachable else "ok"
        print(
            "%s: %s successes=%s/%s failures=%s metadata_warnings=%s total_reward=%.6f"
            % (
                result.name,
                status,
                result.successes,
                result.total,
                result.failures,
                result.metadata_failures,
                result.total_reward,
            )
        )
        if result.failures or result.unreachable:
            exit_code = 1
    return exit_code


def parse_args(argv: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Pre-seed Trading, Purchasing, and DataOps copilots.")
    parser.add_argument("--trading-only", action="store_true", help="Seed Trading only, or include Trading in selected subset.")
    parser.add_argument("--purchasing-only", action="store_true", help="Seed Purchasing only, or include Purchasing in selected subset.")
    parser.add_argument("--dataops-only", action="store_true", help="Seed DataOps only, or include DataOps in selected subset.")
    parser.add_argument("--dry-run", action="store_true", help="Load seeds and check backend health without mutating.")
    parser.add_argument("--force", action="store_true", help="Append seed decisions even if trajectory already has decisions.")
    return parser.parse_args(argv)


def main(argv: List[str]) -> int:
    args = parse_args(argv)
    results = []
    for config in selected_domains(args):
        try:
            results.append(seed_domain(config, args))
        except Exception as exc:
            print("%s: failed before seeding: %s" % (config.name, exc))
            try:
                total = len(load_seed(config.seed_path))
            except Exception:
                total = 0
            results.append(DomainResult(config.name, total, 0, 1, 0, False, False, 0.0))
    return print_summary(results)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
