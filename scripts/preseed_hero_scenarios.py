"""Opt-in synthetic seed phase for the existing hero_moments walkthrough.

Run after normal-mode base preseed. A failed verification is not demo-ready.
DataOps production bottleneck input is an external prerequisite, not something
score/learn writes can manufacture. S2P's final triage cohort stays pending.
"""
from __future__ import annotations

import argparse
from collections.abc import Callable, Iterator
from contextlib import contextmanager
import hashlib
import json
import math
import os
from pathlib import Path
import random
import sys
from typing import Any

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from copilot_sdk.evolution.conservation_contract import evaluate_conservation_safety
from copilot_sdk.scoring.presets import PRESET_REGISTRY
from scripts.preseed_all_copilots import ApiError, api_get, api_post

DOMAINS = ("trading", "purchasing", "dataops", "s2p")
PORTS = (8010, 8020, 8030, 8002)
SEED = 20260711
JOURNAL_DIR = Path(__file__).resolve().parents[1] / ".tmp" / "c1_heroes"
Check = tuple[str, str, Callable[[Any], bool]]


def hero_decisions(domain: str, seed: int = SEED) -> list[dict[str, Any]]:
    """Generate bounded, reproducible inputs; never assign scorer weights.

    Narrow, uninformative factor noise can earn high fingerprint precision.
    Broad but outcome-separated values on the useful factor expose why that
    precision is not predictive accuracy. Early/recent category mixes also
    exercise the existing category-divergence detector on the planted cohort.
    """
    if domain not in DOMAINS:
        raise ValueError(f"Unknown hero domain: {domain}")
    preset = PRESET_REGISTRY[domain]()
    shape = preset.shape
    rng = random.Random(seed)
    rows: list[dict[str, Any]] = []
    count = {"trading": 40, "purchasing": 30, "dataops": 20, "s2p": 30}[domain]
    for index in range(count):
        factors = {name: round(rng.uniform(0.05, 0.95), 6) for name in shape.factor_names}
        category = shape.category_names[index % shape.n_categories]
        correct = True
        action: str | None = None
        metadata: dict[str, Any] = {
            "planted": True, "provenance": "sample", "evidence_tier": "T-sim",
            "hero_id": f"C1-v1-{domain}-{seed}-{index:02d}",
        }
        if domain in {"trading", "purchasing"}:
            half = count // 2
            offset = index % half
            recent_errors = (3, 8, 13, 18) if domain == "trading" else (3, 7, 11, 14)
            early_stable = (0, 1, 2, 4) if domain == "trading" else (0, 1, 2, 4, 5)
            degrading = offset not in early_stable if index < half else offset in recent_errors
            category = shape.category_names[0 if degrading else 1 + offset % (shape.n_categories - 1)]
            # Confirmations precede corrections so the append does not create
            # an artificial error burst at the 75% conservation boundary.
            early_correct = offset % 4 != 3
            recent_correct = domain == "purchasing" and offset in (7, 14)
            correct = (early_correct if index < half else recent_correct) if degrading else True
            trusted, useful = (("signal_alignment", "timing_quality") if domain == "trading"
                               else ("supplier_lead_time", "historical_waste"))
            factors[trusted] = round((0.5 if domain == "trading" else 0.85) + rng.uniform(-0.001, 0.001), 6)
            factors[useful] = round(rng.uniform(0.55, 0.95) if correct else rng.uniform(0.05, 0.45), 6)
        elif domain == "dataops":
            category = ("schema_change", "pipeline_failure")[index % 2]
            metadata.update(system="warehouse_etl", alert_id=metadata["hero_id"])
        else:
            category = ("price_variance", "duplicate_risk", "contract_gap")[index // 10]
            approve = index % 10 < {"price_variance": 8, "duplicate_risk": 3, "contract_gap": 5}[category]
            action = "auto_approve" if approve else "hold_for_review"
            category_index = shape.category_names.index(category)
            action_index = shape.action_names.index(action)
            factors = dict(zip(shape.factor_names, map(float, preset.bootstrap_centroids[category_index, action_index])))
            supplier = (1 + index % 3) if approve else (8 + index % 3)
            metadata.update(supplier_id=f"supplier-{supplier:02d}", intended_action=action)
        rows.append({"category": category, "factors": factors, "correct": correct,
                     "actual_action": action, "metadata": metadata})
    return rows


def _positive_iks(data: Any) -> bool:
    value = data.get("current_iks") if isinstance(data, dict) else None
    return isinstance(value, (int, float)) and math.isfinite(value) and value > 0


def _status(data: Any) -> bool:
    return bool(evaluate_conservation_safety(data).available)


def _green(data: Any) -> bool:
    return bool(isinstance(data, dict) and data.get("status") == "GREEN" and data.get("passed") is True)


def _category_divergence(data: Any) -> bool:
    return isinstance(data, dict) and any(
        isinstance(row, dict) and row.get("trap_type") == "CATEGORY_DIVERGENCE"
        for row in data.get("traps", [])
    )


def _weight_order(data: Any, trusted: str, useful: str) -> bool:
    if not isinstance(data, dict):
        return False
    weights = {row["name"]: row.get("weight") for row in data.get("factors", []) if isinstance(row, dict) and "name" in row}
    first, second = weights.get(trusted), weights.get(useful)
    return (isinstance(first, (int, float)) and isinstance(second, (int, float))
            and math.isfinite(first) and math.isfinite(second) and first > second)


def _trading_weights(data: Any) -> bool:
    if not _weight_order(data, "signal_alignment", "timing_quality"):
        return False
    factors = data["factors"]
    trusted = next(row["weight"] for row in factors if row["name"] == "signal_alignment")
    return all(isinstance(row.get("weight"), (int, float)) and row["weight"] <= trusted for row in factors)


def _purchasing_weights(data: Any) -> bool:
    return _weight_order(data, "supplier_lead_time", "historical_waste")


def _rows(data: Any, key: str) -> bool:
    return isinstance(data, dict) and isinstance(data.get(key), list) and bool(data[key])


def _checkpoints(data: Any) -> bool:
    return _rows(data, "checkpoints")


def _rules(data: Any) -> bool:
    return _rows(data, "rules")


def _schema(data: Any) -> bool:
    return _rows(data, "schema_changes")


def _bottleneck(data: Any) -> bool:
    return isinstance(data, dict) and isinstance(data.get("bottleneck"), dict) and _rows(data, "all_steps_ranked")


def _queue(data: Any) -> bool:
    if not isinstance(data, dict):
        return False
    # Verify our own cohort, not unrelated pre-existing mixed actions.
    expected = {row["metadata"]["hero_id"]: row for row in hero_decisions("s2p")}
    actual = {row.get("invoice_id"): row for row in data.get("exceptions", []) if isinstance(row, dict)}
    return all(identity in actual and actual[identity].get("recommended_action") == row["actual_action"]
               and actual[identity].get("supplier_id") == row["metadata"]["supplier_id"]
               for identity, row in expected.items())


def _suppliers(data: Any) -> bool:
    if not isinstance(data, dict):
        return False
    found = {row.get("supplier_id") for row in data.get("suppliers", []) if isinstance(row, dict)}
    return {f"supplier-{index:02d}" for index in (1, 2, 3, 8, 9, 10)} <= found


def hero_checks(domain: str) -> list[Check]:
    if domain in {"trading", "purchasing"}:
        return [("fingerprint_weight_order", "/api/fingerprint", _trading_weights if domain == "trading" else _purchasing_weights),
                ("category_divergence", "/api/self/trust-traps", _category_divergence),
                ("positive_iks", "/api/trajectory", _positive_iks),
                ("conservation_available", "/api/conservation/status", _status)]
    if domain == "dataops":
        return [("bottleneck_prerequisite", "/api/context/bottleneck/warehouse_etl", _bottleneck),
                ("schema_impact", "/api/context/schema-impact/warehouse_etl", _schema),
                ("checkpoints", "/api/self/centroid-history", _checkpoints),
                ("operational_rules", "/api/ae/operational-rules", _rules),
                ("lifecycle", "/api/ae/rule-lifecycle", _rules)]
    if domain == "s2p":
        return [("triage_cohort", "/api/s2p/preview/queue?limit=50", _queue),
                ("supplier_profiles", "/api/s2p/preview/suppliers", _suppliers),
                ("conservation_green", "/api/conservation/status", _green)]
    raise ValueError(f"Unknown hero domain: {domain}")


def verify_hero_state(domain: str, base_url: str, checks: list[Check] | None = None) -> dict[str, Any]:
    """Read existing endpoints; emit bounded, serializable evidence per check."""
    results: dict[str, Any] = {}
    for name, path, validator in hero_checks(domain) if checks is None else checks:
        try:
            data = api_get(base_url, path)
            results[name] = {"passed": bool(validator(data)), "path": path,
                             "data_summary": json.dumps(data, sort_keys=True, default=str)[:1200]}
        except (ApiError, ValueError, TypeError, KeyError) as exc:
            results[name] = {"passed": False, "path": path, "error": str(exc)}
    return results


def _passed(checks: dict[str, Any]) -> bool:
    return bool(checks) and all(row.get("passed") is True for row in checks.values())


@contextmanager
def _journal(path: Path, target: str) -> Iterator[dict[str, Any]]:
    path.parent.mkdir(parents=True, exist_ok=True)
    lock = path.with_suffix(".lock")
    try:
        descriptor = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError as exc:
        raise ApiError(f"Hero journal locked; inspect interrupted/concurrent run: {lock}") from exc
    os.close(descriptor)
    try:
        state = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {"target": target, "rows": {}}
        if not isinstance(state, dict) or state.get("target") != target or not isinstance(state.get("rows"), dict):
            raise ApiError("Hero journal target/schema mismatch; refusing to replay writes")
        yield state
    finally:
        lock.unlink()


def _save(path: Path, state: dict[str, Any]) -> None:
    temporary = path.with_suffix(".new")
    temporary.write_text(json.dumps(state, sort_keys=True), encoding="utf-8")
    temporary.replace(path)


def seed_hero(domain: str, base_url: str, *, journal_dir: Path = JOURNAL_DIR) -> dict[str, Any]:
    """Append a bounded cohort once; never retry an uncertain score/learn write."""
    rows = hero_decisions(domain)
    report: dict[str, Any] = {
        "domain": domain, "seeded": 0, "skipped": 0, "errors": [], "warnings": [], "prerequisites": [],
    }
    target = f"C1-v1:{domain}:{base_url.rstrip('/')}"
    path = journal_dir / (hashlib.sha256(target.encode()).hexdigest()[:24] + ".json")
    try:
        before = verify_hero_state(domain, base_url)
        if domain == "dataops" and before.get("bottleneck_prerequisite", {}).get("passed") is not True:
            report["prerequisites"].append("DataOps bottleneck prerequisite is not met; no seed writes sent")
            report.update(status="prerequisite_not_met", checks=before)
            return report
        if _passed(before):
            report.update(status="already_ready", checks=before)
            return report
        conservation = api_get(base_url, "/api/conservation/status")
        # S2P has no generic /api/trajectory; its live conservation response
        # exposes the verified history count without a sibling-repo import.
        trajectory = conservation if domain == "s2p" else api_get(base_url, "/api/trajectory")
        if int(trajectory.get("decisions_total", trajectory.get("verified_count", 0))) < 150:
            report["warnings"].append("Base preseed appears incomplete; continuing with normal conservation admission")
        safety = evaluate_conservation_safety(conservation)
        if not safety.learning_allowed or safety.status == "PRESEED":
            raise ApiError(f"Hero phase requires normal learning admission; status={safety.status}")
        with _journal(path, target) as state:
            for row in rows:
                identity = row["metadata"]["hero_id"]
                previous = state["rows"].get(identity)
                if previous:
                    if previous.get("phase") != "complete":
                        raise ApiError(f"Unfinished write for {identity}; inspect decision {previous.get('decision_id')} before retrying")
                    report["skipped"] += 1
                    continue
                record: dict[str, Any] = {"phase": "score_pending"}
                state["rows"][identity] = record
                _save(path, state)
                payload = {"category": row["category"], "factors": row["factors"],
                           "metadata": row["metadata"], "context": row["metadata"]}
                if domain == "s2p":
                    payload = {"event_id": identity, "category": row["category"], "amount": 1000,
                               "supplier_id": row["metadata"]["supplier_id"],
                               "supplier_risk_rating": 1 - row["factors"]["supplier_exception_history"],
                               **row["factors"], "context": row["metadata"]}
                score = api_post(base_url, "/api/s2p/score" if domain == "s2p" else "/api/score", payload)
                if not isinstance(score, dict) or not score.get("decision_id") or not score.get("action"):
                    raise ApiError("Incomplete score acknowledgement; refusing automatic retry")
                record.update(decision_id=score["decision_id"], phase="learn_pending")
                _save(path, state)
                if domain != "s2p":
                    actions = PRESET_REGISTRY[domain]().shape.action_names
                    actual = score["action"] if row["correct"] else next(action for action in actions if action != score["action"])
                    learned = api_post(base_url, "/api/learn", {"decision_id": score["decision_id"],
                        "actual_action": actual, "outcome": "confirmed" if row["correct"] else "overridden",
                        "context": row["metadata"]})
                    if (not isinstance(learned, dict) or learned.get("decision_id") != score["decision_id"]
                            or learned.get("status") != "complete" or learned.get("outcome") != "applied"
                            or learned.get("paused") is True or learned.get("centroid_updated") is False
                            or learned.get("status") in {"paused", "blocked"} or learned.get("blocked_by_gate")
                            or learned.get("learning_applied") is False or learned.get("persistence_failures")):
                        raise ApiError(f"Learning not admitted: {learned}")
                record["phase"] = "complete"
                _save(path, state)
                report["seeded"] += 1
    except (ApiError, OSError, ValueError, TypeError) as exc:
        report["errors"].append(str(exc))
    report["checks"] = verify_hero_state(domain, base_url)
    report["status"] = "ready" if not report["errors"] and _passed(report["checks"]) else "not_ready"
    return report


def run_heroes(selected_names: set[str] | None = None, *, verify_only: bool = False) -> int:
    selected = set(DOMAINS) if selected_names is None else selected_names
    unknown = selected - set(DOMAINS)
    if unknown:
        raise ValueError(f"No C-1 seed requested for domains: {sorted(unknown)}")
    reports = []
    for domain, port in zip(DOMAINS, PORTS):
        if domain not in selected:
            continue
        url = os.environ.get(f"{domain.upper()}_URL", f"http://127.0.0.1:{port}")
        if verify_only:
            checks = verify_hero_state(domain, url)
            report = {"domain": domain, "status": "ready" if _passed(checks) else "not_ready", "checks": checks}
        else:
            report = seed_hero(domain, url)
        reports.append(report)
    print(json.dumps(reports, indent=2, sort_keys=True))
    return int(any(report["status"] not in {"ready", "already_ready"} for report in reports))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--domains", nargs="+", choices=DOMAINS, default=list(DOMAINS))
    parser.add_argument("--verify-only", action="store_true")
    args = parser.parse_args(argv)
    return run_heroes(set(args.domains), verify_only=args.verify_only)


if __name__ == "__main__":
    raise SystemExit(main())
