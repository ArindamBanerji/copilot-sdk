"""Seed observable demo states through existing scoring APIs (synthetic data).

No gate bypass, timestamp spoofing, or production-model replacement. Existing
history and immutable twins are preserved. Run after the ordinary preseed.
"""
from __future__ import annotations

import argparse
import json
import shutil
import time
import sys
from typing import Any
from pathlib import Path
from datetime import datetime, timezone

# Support both `python scripts/preseed_demo_fixtures.py` and module invocation.
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from copilot_sdk.backend.modeled_projection import ProjectionInputs
from copilot_sdk.graph.factory import create_graph_store
from copilot_sdk.backend.historical_checkpoint import HISTORY_IMPORT_KEY, HistoricalCheckpointImport

from scripts.preseed_all_copilots import (
    DOMAINS, ApiError, api_get, api_post, domain_url, extract_factors, load_seed,
)


def regime_metadata(volatile: bool) -> dict[str, float]:
    return {"vix": 35.0 if volatile else 14.0, "adx": 35.0}


def trading_seed_sequence() -> list[tuple[int, bool, bool]]:
    # Keep a stable trending regime long enough to establish the ten-decision
    # comparison window, then hold volatile continuously.  The monitor fires
    # on the regime transition and remains active while fewer than twenty
    # decisions have stabilized in the new regime.
    return ([(index, index % 20 < 17, False) for index in range(40)]
            + [(40 + index, index % 2 == 0, True) for index in range(15)])


def score_outcome(domain: str, index: int, correct: bool, *, volatile: bool = False) -> dict[str, Any]:
    config = next(item for item in DOMAINS if item.name == domain)
    url = domain_url(config)
    seeds = load_seed(config.seed_path)
    row = seeds[index % len(seeds)]
    provenance = {"planted": True, "provenance": "sample", "evidence_tier": "T-sim",
                  "fixture": "SDK-PRESEED", "seed_index": index}
    metadata: dict[str, Any] = dict(provenance)
    if domain == "trading":
        # The monitor consumes market inputs, not requested regime labels.
        metadata.update(regime_metadata(volatile))
    score = api_post(url, "/api/score", {"category": row["category"],
        "factors": extract_factors(row, config), "metadata": metadata, "context": provenance})
    action = score.get("action") or score.get("recommended_action")
    if not action or not score.get("decision_id"):
        raise RuntimeError(f"{domain}: incomplete score response")
    actual = action if correct else next(value for value in config.actions if value != action)
    try:
        result = api_post(url, "/api/learn", {"decision_id": score["decision_id"],
            "actual_action": actual, "outcome": "confirmed" if correct else "overridden",
            "context": provenance})
    except ApiError as exc:
        # Keep scored decisions and let the remaining sequence establish the
        # regime transition. Never bypass or mutate the conservation gate.
        if domain != "trading" or "HTTP 423" not in str(exc):
            raise
        result = {"blocked_by_gate": True, "gate_error": str(exc)}
    print(json.dumps({"domain": domain, "index": index, "decision_id": score["decision_id"],
                      "learn": result}), flush=True)
    return dict(result)


def seed_trading() -> dict[str, Any]:
    url = domain_url(DOMAINS[0])
    status = api_get(url, "/api/trading/regime-status")
    if status.get("regime_break_active"):
        return dict(status)
    # Market metadata drives RegimeMonitor, not labels or requested accuracy.
    # Stop at 15 observations, before its 20-observation stabilization point.
    for index, correct, volatile in trading_seed_sequence():
        score_outcome("trading", index, correct, volatile=volatile)
    status = api_get(url, "/api/trading/regime-status")
    if not status.get("regime_break_active"):
        raise RuntimeError(f"Trading regime break not observed: {status}")
    return dict(status)


def seed_purchasing() -> dict[str, Any]:
    url = domain_url(DOMAINS[1])
    status = api_get(url, "/api/conservation/status")
    if status.get("status") != "GREEN" and status.get("passed") is not False:
        raise RuntimeError("Purchasing reports non-GREEN but passed=true; restart updated backend before adding outcomes")
    twin = api_get(url, "/api/purchasing/frozen-twin")
    if not twin.get("available"):
        if status.get("status") == "GREEN":
            for index in range(30):
                score_outcome("purchasing", index, index % 5 != 4)
        try:
            twin = api_post(url, "/api/purchasing/frozen-twin/freeze", {})
        except ApiError as exc:
            # Degradation is independently demonstrable; report the unready
            # twin contract instead of pretending a snapshot was created.
            twin = {"available": False, "error": str(exc)}
            print(json.dumps({"scenario": "purchasing-twin", **twin}), flush=True)
    for index in range(20):
        status = api_get(url, "/api/conservation/status")
        if status.get("status") != "GREEN" and status.get("passed") is False:
            return {"twin": twin, "conservation": status}
        score_outcome("purchasing", 30 + index, index % 2 == 0)
    status = api_get(url, "/api/conservation/status")
    if status.get("status") == "GREEN" or status.get("passed") is not False:
        raise RuntimeError(f"Purchasing degradation not observed: {status}")
    return {"twin": twin, "conservation": status}


def seed_projection() -> dict[str, Any]:
    # Explicit illustrative assumptions, not pilot observations or earned ROI.
    inputs = ProjectionInputs(setup_cost=1000, weekly_decisions=100,
        benefit_per_decision=2.5, weekly_operating_cost=20,
        required_verified_decisions=200, provenance="SDK-PRESEED planted demo assumptions")
    root = Path(__file__).resolve().parents[1]
    store = create_graph_store(domain="purchasing",
                               db_path=root / "apps/purchasing/backend/data/purchasing.db")
    try:
        store.save_governance("purchasing", "demo:roi_projection", inputs.model_dump())
        return {"seeded": True, "inputs": inputs.model_dump(),
                "note": "Conservation projection requires the updated Purchasing backend"}
    finally:
        store.close()


def seed_evolution() -> dict[str, Any]:
    root = Path(__file__).resolve().parents[1]
    store = create_graph_store(domain="dataops", db_path=root / "apps/dataops/backend/data/dataops.db")
    try:
        existing = {row.get("event_id") for row in store.get_evolution_events("dataops", limit=10000)}
        for index, event in enumerate(("proposed", "promoted", "demoted")):
            identity = f"SDK-PRESEED-DO04-{index}"
            if identity in existing:
                continue
            store.write_evolution_event(event_id=identity, domain="dataops", event_type=event,
                rule_name="Demo rule lifecycle", variant_id="SDK-PRESEED-DO04", metadata={
                    "planted": True, "provenance": "sample", "evidence_tier": "T-sim",
                    "sequence": index, "reason": "Synthetic lifecycle demonstration; not an active production rule",
                })
        return {"seeded": True, "variant_id": "SDK-PRESEED-DO04",
                "note": "Persisted synthetic transitions; restart updated DataOps lifecycle builder"}
    finally:
        store.close()


def _epoch(value: Any) -> float:
    if isinstance(value, (int, float)):
        return float(value)
    parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    return parsed.replace(tzinfo=timezone.utc).timestamp() if parsed.tzinfo is None else parsed.timestamp()


def plan_historical_gap(checkpoints: list[dict[str, Any]], decisions: list[dict[str, Any]]) -> dict[str, Any]:
    """Carry forward a pre-gap snapshot; never backdate today's verified count."""
    ordinary = sorted((row for row in checkpoints if not (row.get("metadata") or {}).get("historical_import")),
                      key=lambda row: _epoch(row["created_at"]))
    activity = [_epoch(row[key]) for row in decisions for key in ("created_at", "verified_at")
                if row.get(key) is not None]
    # Prefer the most recent idle interval, matching the current demo cohort.
    for before, after in reversed(list(zip(ordinary, ordinary[1:]))):
        start = _epoch(before["created_at"]) + 1
        end = start + 8 * 86400
        if end >= _epoch(after["created_at"]):
            continue
        if any(_epoch(before["created_at"]) < stamp <= end for stamp in activity):
            continue
        if before.get("verified_count") is None or not before.get("shape"):
            continue
        return {"source": before, "start": start, "end": end}
    raise RuntimeError("No observed eight-day inactive interval with a usable pre-gap checkpoint; use an isolated demo history")


def seed_historical_gap() -> dict[str, Any]:
    """Import an explicitly synthetic carry-forward inside an observed idle interval."""
    root = Path(__file__).resolve().parents[1]
    store = create_graph_store(domain="purchasing", db_path=root / "apps/purchasing/backend/data/purchasing.db")
    try:
        return persist_historical_gap(store)
    finally:
        store.close()


def persist_historical_gap(store: Any) -> dict[str, Any]:
    """Publish a display-only, verification-free eight-day interval.

    Anchor the fixture immediately after the latest real checkpoint so the
    first visible gap is the planted interval, rather than an unrelated old
    gap whose verified count changed.
    """
    checkpoints = store.get_centroid_checkpoints("purchasing", limit=None, include_v2=True)
    ordinary = [row for row in checkpoints
                if not (row.get("metadata") or {}).get("historical_import")
                and row.get("verified_count") is not None
                and row.get("shape")]
    if not ordinary:
        raise RuntimeError("No usable real checkpoint for the verification-gap fixture")
    source = max(ordinary, key=lambda row: _epoch(row["created_at"]))
    start = _epoch(source["created_at"]) + 1
    end = start + 8 * 86400
    ingested_at = time.time()
    revision = f"demo_reseed_{int(ingested_at * 1000000)}"
    imports = []
    for index, observed_at in enumerate((start, end)):
        event = HistoricalCheckpointImport(observed_at=observed_at, planted=True,
            provenance="synthetic", evidence_tier="T-sim",
            description="Synthetic carry-forward of the actual pre-gap geometry/count; no scoring or verification during the eight-day interval")
        imports.append({**source, "checkpoint_id": f"{revision}_{index}", "created_at": ingested_at,
            "metadata": {"historical_import": event.model_dump(), "source_checkpoint_id": source["checkpoint_id"],
                         "display_only": True, "origin": "demo_reseed"}})
    existing = store.get_governance("purchasing", HISTORY_IMPORT_KEY) or {}
    supersessions = {row["checkpoint_id"]: {"superseded": True, "superseded_by": revision}
        for row in existing.get("checkpoints", [])
        if isinstance(row, dict) and row.get("checkpoint_id")}
    # One publication contains replacement points and annotations for retained
    # immutable imports. Neither scoring history nor restore selection changes.
    store.save_governance("purchasing", HISTORY_IMPORT_KEY,
        {"revision": revision, "checkpoints": imports, "supersessions": supersessions})
    return {"seeded": True, "gap_days": 8, "verified_count": source["verified_count"],
            "revision": revision, "superseded_imports": len(supersessions), "provenance": "synthetic"}


def seed_investigation_evidence() -> dict[str, Any]:
    root = Path(__file__).resolve().parents[1]
    source = root / "data/demo_fixtures/dataops_investigation_evidence.json"
    target = root / "apps/dataops/backend/data/demo_fixtures/investigation_evidence.json"
    if target.exists() and target.read_bytes() != source.read_bytes():
        raise RuntimeError(f"Refusing to overwrite different existing demo evidence: {target}")
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, target)
    return {"seeded": True, "fixture": "PL-DO-5", "provenance": "synthetic",
            "note": "Restart DataOps to load the evidence; action flip remains geometry-dependent"}


def run_scenarios(scenario: str = "all") -> int:
    failures = 0
    for name, seed in (("trading", seed_trading), ("purchasing", seed_purchasing),
                       ("projection", seed_projection), ("evolution", seed_evolution),
                       ("gap", seed_historical_gap), ("investigation", seed_investigation_evidence)):
        if scenario not in (name, "all"):
            continue
        try:
            print(json.dumps({"scenario": name, "result": seed()}), flush=True)
        except Exception as exc:
            failures += 1
            print(json.dumps({"scenario": name, "error": str(exc)}), flush=True)
    return int(failures > 0)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scenario", choices=("trading", "purchasing", "projection", "evolution", "gap", "investigation", "all"), default="all")
    args = parser.parse_args()
    return run_scenarios(args.scenario)


if __name__ == "__main__":
    raise SystemExit(main())
