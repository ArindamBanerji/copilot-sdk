#!/usr/bin/env python3
"""
jm_stress_test.py — JM Architecture Stress Test (v2)

Tests the Judgment Memory shared-graph architecture against a LIVE stack.
Uses HTTP APIs for product operations and AGEClient (ci-platform) for
ground-truth verification. Never imports product/scorer/copilot modules.

Usage:
    python scripts/jm_stress_test.py                  # Full (pause at phase 4 for restart)
    python scripts/jm_stress_test.py --skip-restart    # Skip restart test
    python scripts/jm_stress_test.py --phase 7         # Single phase
    python scripts/jm_stress_test.py --from-phase 4b   # Resume after restart

Requirements:
    - All 5 copilots running (python demo.py --no-browser)
    - AGE/PostgreSQL reachable
    - ci-platform in sys.path (for AGEClient import)
"""

from __future__ import annotations

import argparse
import asyncio
import concurrent.futures
import json
import math
import os
import sys
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, TypedDict
from urllib.parse import urlencode

# ---------------------------------------------------------------------------
# Ensure ci-platform importable
# ---------------------------------------------------------------------------
_WORKSPACE = Path(__file__).resolve().parents[1].parent
_CI_PATH = _WORKSPACE / "ci-platform"
if _CI_PATH.exists() and str(_CI_PATH) not in sys.path:
    sys.path.insert(0, str(_CI_PATH))


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

AGE_DSN = os.environ.get(
    "GRAPH_DSN",
    "host=172.22.74.149 port=5433 dbname=soc_copilot user=postgres password=postgres sslmode=disable",
)
GRAPH_NAME = "soc_graph"

class CopilotConfig(TypedDict):
    port: int
    score_path: str
    learn_path: str


COPILOTS: dict[str, CopilotConfig] = {
    "trading": {
        "port": 8010,
        "score_path": "/api/score",
        "learn_path": "/api/learn",
    },
    "purchasing": {
        "port": 8020,
        "score_path": "/api/score",
        "learn_path": "/api/learn",
    },
    "dataops": {
        "port": 8030,
        "score_path": "/api/score",
        "learn_path": "/api/learn",
    },
    "s2p": {
        "port": 8002,
        "score_path": "/api/s2p/score",
        "learn_path": "/api/learn",
    },
    # SOC excluded from direct scoring — uses triage, not /api/score
}

# Explicit synthetic test inputs matching the public scoring contracts.
# Do not import product/scorer modules into this external verifier.
SCORE_PAYLOADS: dict[str, Callable[[str], dict[str, Any]]] = {
    "trading": lambda tag: {
        "category": "trend_following",
        "metadata": {"entity_id": tag, "origin": "jm_stress_test", "provenance": "synthetic"},
        "factors": {
            "signal_alignment": 0.7, "market_regime": 0.4, "position_sizing": 0.8,
            "timing_quality": 0.3, "risk_reward_actual": 0.6, "emotional_indicator": 0.5,
            "signal_confidence": 0.7, "options_delta_exposure": 0.5,
            "options_iv_percentile": 0.5, "options_gamma_risk": 0.5,
        },
    },
    "purchasing": lambda tag: {
        "category": "protein",
        "metadata": {"entity_id": tag, "origin": "jm_stress_test", "provenance": "synthetic"},
        "factors": {
            "expected_demand": 0.7, "day_of_week": 0.6, "weather_forecast": 0.5,
            "event_flag": 0.4, "historical_waste": 0.3,
            "supplier_lead_time": 0.8, "price_memory_index": 0.7,
        },
    },
    "dataops": lambda tag: {
        "category": "quality_anomaly",
        "metadata": {"entity_id": tag, "origin": "jm_stress_test", "provenance": "synthetic"},
        "factors": {
            "impact_scope": 0.7, "source_reliability": 0.6,
            "recurrence_frequency": 0.5, "downstream_urgency": 0.4,
            "data_freshness": 0.8, "business_criticality": 0.3,
        },
    },
    "s2p": lambda tag: {
        "event_id": tag, "category": "price_variance", "amount": 100.0,
        "supplier_id": "STRESS-SUPPLIER",
        "match_status": 0.9, "amount_variance_ratio": 0.3,
        "duplicate_score": 0.1, "supplier_exception_history": 0.2,
        "payment_terms_impact": 0.5, "commodity_index_correlation": 0.6,
        "tax_regulatory_compliance": 0.9, "environmental_risk": 0.2,
        "context": {"origin": "jm_stress_test", "provenance": "synthetic"},
    },
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

@dataclass
class PhaseResult:
    phase: str
    name: str
    passed: bool
    checks: list[str] = field(default_factory=list)
    failures: list[str] = field(default_factory=list)


def http_get(port: int, path: str, timeout: int = 10) -> tuple[int, Any]:
    import urllib.request
    import urllib.error
    try:
        r = urllib.request.urlopen(f"http://127.0.0.1:{port}{path}", timeout=timeout)
        return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        try:
            return e.code, json.loads(body)
        except Exception:
            return e.code, {"raw": body}
    except Exception as e:
        return 0, {"error": str(e)}


def http_post(port: int, path: str, payload: dict, timeout: int = 15) -> tuple[int, Any]:
    import urllib.request
    import urllib.error
    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        f"http://127.0.0.1:{port}{path}",
        data=data,
        headers={"Content-Type": "application/json"},
    )
    try:
        r = urllib.request.urlopen(req, timeout=timeout)
        return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        try:
            return e.code, json.loads(body)
        except Exception:
            return e.code, {"raw": body}
    except Exception as e:
        return 0, {"error": str(e)}


class AGEVerifier:
    """Direct AGE queries via AGEClient for ground-truth verification."""

    def __init__(self, dsn: str, graph_name: str):
        from ci_platform.graph.age_client import AGEClient
        self._client = AGEClient(dsn=dsn, graph_name=graph_name)

    def _run(self, coro):
        """Sync wrapper for async AGEClient methods."""
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(coro)
        # If already in a loop, use a thread
        import threading
        result: dict[str, Any] = {}
        def _target():
            try:
                result["value"] = asyncio.run(coro)
            except Exception as exc:
                result["error"] = exc
        t = threading.Thread(target=_target, daemon=True)
        t.start()
        t.join(timeout=30)
        if "error" in result:
            raise result["error"]
        return result.get("value")

    def count_decisions(self, domain: str) -> int:
        rows = self._run(self._client.run_query(
            f"MATCH (d:Decision {{domain: '{domain}'}}) RETURN count(d) AS cnt"
        ))
        if rows and len(rows) > 0:
            row = rows[0]
            if isinstance(row, dict):
                return int(row.get("cnt", 0))
            if isinstance(row, (list, tuple)):
                return int(row[0])
        return 0

    def decision_counts(self, domain: str) -> dict[str, int]:
        """Separate live inventory, retained archives and conservation evidence."""
        rows = self._run(self._client.run_query(
            "MATCH (d:Decision) WHERE d.domain = $domain "
            "RETURN d.archived AS archived, d.status AS status, "
            "count(d) AS cnt, count(DISTINCT d.decision_id) AS ids",
            {"domain": domain},
        ))
        counts = {"active": 0, "archived": 0, "verified": 0, "total": 0}
        for row in rows:
            count = int(row["cnt"])
            counts["total"] += count
            if row["archived"] is True:
                counts["archived"] += count
            else:
                counts["active"] += count
                if row["status"] in {"confirmed", "overridden"}:
                    counts["verified"] += int(row["ids"])
        return counts

    def transfer_patterns(self) -> list[dict[str, Any]]:
        return list(self._run(self._client.run_query(
            "MATCH (tp:TransferPattern)-[:FROM_DOMAIN]->(src:Domain), "
            "(tp)-[:TO_DOMAIN]->(dst:Domain) "
            "RETURN tp.pattern_id AS pattern_id, src.domain_id AS source_domain, "
            "dst.domain_id AS target_domain"
        )))

    def movement_decision(self, domain: str) -> str | None:
        rows = self._run(self._client.run_query(
            "MATCH (d:Decision)-[:HAS_OUTCOME]->(e:Outcome) WHERE d.domain = $domain "
            "AND (e.domain = $domain OR e.domain IS NULL) "
            "RETURN d.decision_id AS decision_id LIMIT 1", {"domain": domain},
        ))
        return str(rows[0]["decision_id"]) if rows else None

    def find_decision(self, decision_id: str, domain: str) -> dict | None:
        rows = self._run(self._client.run_query(
            "MATCH (d:Decision {decision_id: $decision_id, domain: $domain}) "
            "RETURN d.decision_id AS id, d.domain AS domain, d.category AS cat",
            {"decision_id": decision_id, "domain": domain},
        ))
        if rows and len(rows) > 0:
            row = rows[0]
            if isinstance(row, dict):
                return {"decision_id": row.get("id"), "domain": row.get("domain"), "category": row.get("cat")}
            if isinstance(row, (list, tuple)):
                return {"decision_id": row[0], "domain": row[1], "category": row[2] if len(row) > 2 else None}
        return None

    def count_centroids(self, domain: str) -> int:
        """Count persisted tensors, excluding legacy metadata-only checkpoints."""
        rows = self._run(self._client.run_query(
            "MATCH (c:CentroidCheckpoint) WHERE c.domain = $domain "
            "AND c.centroids IS NOT NULL RETURN count(c) AS cnt", {"domain": domain},
        ))
        if rows and len(rows) > 0:
            row = rows[0]
            if isinstance(row, dict):
                return int(row.get("cnt", 0))
            if isinstance(row, (list, tuple)):
                return int(row[0])
        return 0

    def latest_centroids(self, domain: str) -> Any:
        rows = self._run(self._client.run_query(
            "MATCH (c:CentroidCheckpoint) WHERE c.domain = $domain "
            "RETURN c.centroids AS centroids, c.created_at AS created_at",
            {"domain": domain},
        ))
        # Match GraphStore's numeric timestamp ordering across legacy encodings.
        def timestamp(row: dict[str, Any]) -> float:
            value = row.get("created_at") or 0
            try:
                return float(value)
            except (TypeError, ValueError):
                stamp = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
                return stamp.replace(tzinfo=stamp.tzinfo or timezone.utc).timestamp()

        latest: dict[str, Any] = max(rows, key=timestamp, default={})
        tensor = latest.get("centroids")
        return json.loads(tensor) if isinstance(tensor, str) else tensor

    def count_transfer_patterns(self) -> int:
        rows = self._run(self._client.run_query(
            "MATCH (t:TransferPattern) RETURN count(t) AS cnt"
        ))
        if rows and len(rows) > 0:
            row = rows[0]
            if isinstance(row, dict):
                return int(row.get("cnt", 0))
            if isinstance(row, (list, tuple)):
                return int(row[0])
        return 0

    def all_domain_counts(self) -> dict[str, int]:
        rows = self._run(self._client.run_query(
            "MATCH (d:Decision) RETURN d.domain AS domain, count(d) AS cnt"
        ))
        result: dict[str, int] = {}
        for row in (rows or []):
            if isinstance(row, dict):
                d = str(row.get("domain", ""))
                c = int(row.get("cnt", 0))
            elif isinstance(row, (list, tuple)):
                d, c = str(row[0]), int(row[1])
            else:
                continue
            result[d] = c
        return result


# ---------------------------------------------------------------------------
# Phases
# ---------------------------------------------------------------------------

def phase_1(age: AGEVerifier) -> PhaseResult:
    """Multi-domain scoring: score one decision per domain, verify in AGE."""
    result = PhaseResult("1", "Multi-domain scoring", True)
    tag = uuid.uuid4().hex[:8]

    for domain, cfg in COPILOTS.items():
        before = age.count_decisions(domain)
        payload = SCORE_PAYLOADS[domain](f"STRESS-{domain.upper()}-{tag}")
        status, body = http_post(cfg["port"], cfg["score_path"], payload)

        if status in (200, 201):
            decision_id = body.get("decision_id", "unknown")
            after = age.count_decisions(domain)
            if after > before and age.find_decision(decision_id, domain) is not None:
                result.checks.append(f"{domain}: scored {decision_id}, AGE count {before}→{after}")
            else:
                result.failures.append(f"{domain}: score {decision_id} not verified in AGE ({before}→{after})")
                result.passed = False
        else:
            result.failures.append(f"{domain}: scoring not exercised, HTTP {status} — {json.dumps(body)[:300]}")
            result.passed = False

    return result


def phase_2(age: AGEVerifier) -> PhaseResult:
    """Graph persistence: score then query AGE directly for the decision."""
    result = PhaseResult("2", "Graph persistence", True)
    tag = uuid.uuid4().hex[:8]

    status, body = http_post(
        COPILOTS["trading"]["port"],
        COPILOTS["trading"]["score_path"],
        SCORE_PAYLOADS["trading"](f"STRESS-PERSIST-{tag}"),
    )
    if status not in (200, 201):
        result.failures.append(f"Score failed: HTTP {status}")
        result.passed = False
        return result

    decision_id = body.get("decision_id", "")
    if not decision_id:
        result.failures.append("Score returned no decision_id")
        result.passed = False
        return result

    found = age.find_decision(decision_id, "trading")
    if found:
        result.checks.append(
            f"Decision {decision_id} FOUND in AGE: "
            f"domain={found['domain']}, category={found['category']}"
        )
    else:
        result.failures.append(f"Decision {decision_id} NOT FOUND in AGE — not persisted")
        result.passed = False

    return result


def phase_3(age: AGEVerifier) -> PhaseResult:
    """Verify persisted CentroidCheckpoint tensors for every scored domain."""
    result = PhaseResult("3", "Centroid durability", True)
    shapes = {"trading": (5, 4, 10), "purchasing": (5, 4, 7),
              "dataops": (6, 5, 6), "s2p": (5, 5, 8)}
    for domain, (categories, actions, factors) in shapes.items():
        count = age.count_centroids(domain)
        tensor = age.latest_centroids(domain)
        valid = isinstance(tensor, list) and len(tensor) == categories and all(
            isinstance(category, list) and len(category) == actions and all(
                isinstance(action, list) and len(action) == factors and all(
                    isinstance(value, (int, float)) and math.isfinite(value) for value in action
                ) for action in category
            ) for category in tensor
        )
        if count > 0 and valid:
            result.checks.append(f"{domain}: {count} tensor checkpoints; latest shape {categories}×{actions}×{factors}, finite")
        else:
            result.failures.append(f"{domain}: {count} tensor checkpoints; latest tensor missing/invalid")
    result.passed = not result.failures
    return result


def phase_4a(age: AGEVerifier) -> PhaseResult:
    """Pre-restart snapshot: record counts for restart survival test."""
    result = PhaseResult("4a", "Pre-restart snapshot", True)
    counts = age.all_domain_counts()
    inventories = {domain: age.decision_counts(domain) for domain in counts}
    conservation: dict[str, int] = {}

    for domain, cfg in COPILOTS.items():
        status, body = http_get(cfg["port"], "/api/conservation/status")
        if status == 200 and isinstance(body, dict):
            conservation[domain] = body.get("verified_count", 0)

    state = {
        "counts": counts,
        "inventories": inventories,
        "conservation": conservation,
        "timestamp": time.time(),
    }
    state_file = Path(__file__).parent / "_jm_stress_state.json"
    state_file.write_text(json.dumps(state, indent=2))

    for domain, count in sorted(counts.items()):
        cons = conservation.get(domain, "?")
        inventory = inventories[domain]
        result.checks.append(
            f"{domain}: {count} decisions "
            f"(active={inventory['active']}, archived={inventory['archived']}), "
            f"verified={cons}"
        )

    result.checks.append(f"State saved to {state_file}")
    result.checks.append("")
    result.checks.append(">>> RESTART NOW <<<")
    result.checks.append("  python demo.py --stop")
    result.checks.append("  python demo.py --no-browser")
    result.checks.append("  python scripts/jm_stress_test.py --from-phase 4b")
    return result


def phase_4b(age: AGEVerifier) -> PhaseResult:
    """Post-restart verification: confirm counts survived restart."""
    result = PhaseResult("4b", "Post-restart survival", True)

    state_file = Path(__file__).parent / "_jm_stress_state.json"
    if not state_file.exists():
        result.failures.append("No state file — run phase 4a first")
        result.passed = False
        return result

    pre = json.loads(state_file.read_text())
    pre_counts = pre["counts"]
    pre_inventories = pre.get("inventories", {})
    pre_conservation = pre.get("conservation", {})
    post_counts = age.all_domain_counts()

    for domain in sorted(set(list(pre_counts.keys()) + list(post_counts.keys()))):
        before = pre_counts.get(domain, 0)
        after = post_counts.get(domain, 0)
        if after >= before:
            result.checks.append(f"{domain}: {before}→{after} decisions (survived)")
        else:
            result.failures.append(f"{domain}: {before}→{after} (LOST {before - after})")
            result.passed = False

        before_inventory = pre_inventories.get(domain)
        if isinstance(before_inventory, dict):
            after_inventory = age.decision_counts(domain)
            active_before = int(before_inventory.get("active", 0))
            active_after = int(after_inventory["active"])
            if active_after >= active_before:
                result.checks.append(
                    f"{domain}: active {active_before}→{active_after} (visible history survived)"
                )
            else:
                result.failures.append(
                    f"{domain}: active {active_before}→{active_after} "
                    f"(ARCHIVED/HIDDEN {active_before - active_after})"
                )
                result.passed = False

    # Verify conservation counts survived
    for domain, cfg in COPILOTS.items():
        status, body = http_get(cfg["port"], "/api/conservation/status")
        if status == 200 and isinstance(body, dict):
            post_verified = body.get("verified_count", 0)
            pre_verified = pre_conservation.get(domain, 0)
            if post_verified >= pre_verified:
                result.checks.append(f"{domain}: conservation {pre_verified}→{post_verified} (survived)")
            else:
                result.failures.append(f"{domain}: conservation {pre_verified}→{post_verified} (LOST)")
                result.passed = False

    try:
        state_file.unlink()
    except OSError:
        pass

    return result


def phase_5(age: AGEVerifier) -> PhaseResult:
    """Conservation gate: score then learn, verify gate evaluates."""
    result = PhaseResult("5", "Conservation gate", True)
    tag = uuid.uuid4().hex[:8]

    # Score
    status, body = http_post(
        COPILOTS["trading"]["port"],
        COPILOTS["trading"]["score_path"],
        SCORE_PAYLOADS["trading"](f"STRESS-GATE-{tag}"),
    )
    if status not in (200, 201):
        result.failures.append(f"Score failed: HTTP {status}")
        result.passed = False
        return result

    decision_id = body.get("decision_id", "")

    # Learn (was /api/confirm — actually /api/learn)
    learn_status, learn_body = http_post(
        COPILOTS["trading"]["port"],
        "/api/learn",
        {"decision_id": decision_id, "actual_action": body["action"], "outcome": "confirmed"},
    )

    if learn_status in (200, 201):
        result.checks.append(f"Learn accepted for {decision_id}")
    elif learn_status == 423:
        result.checks.append(f"Gate blocked learn for {decision_id} (conservation active — correct)")
    else:
        result.failures.append(f"Unexpected learn status {learn_status}: {json.dumps(learn_body)[:100]}")
        result.passed = False

    # Conservation status should have real counts
    cons_status, cons_body = http_get(COPILOTS["trading"]["port"], "/api/conservation/status")
    if cons_status == 200 and isinstance(cons_body, dict):
        verified = cons_body.get("verified_count", -1)
        if verified > 0:
            result.checks.append(f"Conservation verified_count={verified} (graph-backed)")
        elif verified == 0:
            result.checks.append(f"Conservation verified_count=0 (no confirmations yet)")
        else:
            result.failures.append(f"Conservation verified_count={verified} (unexpected)")
            result.passed = False
    else:
        result.failures.append(f"Conservation status HTTP {cons_status}")
        result.passed = False

    return result


def phase_6(age: AGEVerifier) -> PhaseResult:
    """Cross-domain transfer evidence: verify transfer patterns in AGE."""
    result = PhaseResult("6", "Cross-domain transfer evidence", True)

    count = age.count_transfer_patterns()
    if count > 0:
        result.checks.append(f"{count} TransferPattern nodes in AGE")
    else:
        result.failures.append("NO TransferPattern nodes in AGE")
        result.passed = False

    # Also check via API
    status, body = http_get(COPILOTS["trading"]["port"], "/api/transfer/opportunities")
    if status == 200 and isinstance(body, dict):
        source = body.get("source", "unknown")
        result.checks.append(f"Transfer API source={source}")
    elif status == 200:
        result.checks.append(f"Transfer API returned data (size={len(body) if isinstance(body, list) else '?'})")
    else:
        result.failures.append(f"Transfer API HTTP {status}")
        result.passed = False

    return result


def phase_7(age: AGEVerifier) -> PhaseResult:
    """Compare directional transfer evidence with persisted AGE patterns."""
    result = PhaseResult("7", "Cross-domain traversal", True)
    patterns = age.transfer_patterns()
    pairs: dict[tuple[str, str], set[str]] = {}
    for pattern in patterns:
        pair = (pattern["source_domain"], pattern["target_domain"])
        pairs.setdefault(pair, set()).add(pattern["pattern_id"])
    if not pairs:
        result.failures.append("No persisted cross-domain transfer evidence to exercise")
    # Include a pair without evidence: unrelated witnesses must not leak into it.
    pairs.setdefault(("trading", "s2p"), set())
    for (src, tgt), expected in sorted(pairs.items()):
        query = urlencode({"source_domain": src, "target_domain": tgt, "pattern_id": "any"})
        status, body = http_get(8010, "/api/traversal/transfer_witness?" + query)
        if status != 200 or not isinstance(body, list):
            result.failures.append(f"{src}→{tgt}: HTTP {status}, expected a witness list")
            continue
        actual = set()
        for witness in body:
            pattern = witness.get("transfer_pattern", {})
            if (pattern.get("source_domain"), pattern.get("target_domain")) != (src, tgt):
                result.failures.append(f"{src}→{tgt}: leaked witness from a different domain pair")
            actual.add(pattern.get("pattern_id"))
        if actual != expected:
            result.failures.append(f"{src}→{tgt}: API patterns={actual}, AGE patterns={expected}")
        else:
            result.checks.append(f"{src}→{tgt}: {len(actual)} witnesses match AGE")
        for pattern_id in sorted(expected):
            query = urlencode({"source_domain": src, "target_domain": tgt, "pattern_id": pattern_id})
            status, body = http_get(8010, "/api/traversal/transfer_witness?" + query)
            if status != 200 or not isinstance(body, list) or {
                w.get("transfer_pattern", {}).get("pattern_id") for w in body
            } != {pattern_id}:
                result.failures.append(f"Specific pattern lookup failed: {pattern_id} (HTTP {status})")

    decision_id = age.movement_decision("trading")
    if decision_id is None:
        result.failures.append("No linked Trading decision exists to exercise decision_movement")
    else:
        status, body = http_get(8010, "/api/traversal/decision_movement?" + urlencode({"decision_id": decision_id}))
        if status == 200 and isinstance(body, list) and body:
            result.checks.append(f"decision_movement: {decision_id}, {len(body)} evidence paths")
        else:
            result.failures.append(f"decision_movement: HTTP {status}, empty/malformed evidence for {decision_id}")
    result.passed = not result.failures
    return result


def phase_8(age: AGEVerifier) -> PhaseResult:
    """Concurrent load: 40 valid scores; verify every returned ID in its domain."""
    result = PhaseResult("8", "Concurrent load", True)
    tag = uuid.uuid4().hex[:6]
    scored_ids: list[tuple[str, str]] = []
    errors: list[str] = []

    def score_one(domain: str, index: int) -> tuple[str, str | None, str | None]:
        cfg = COPILOTS[domain]
        payload = SCORE_PAYLOADS[domain](f"STRESS-CONC-{domain[:3].upper()}-{tag}-{index:03d}")
        status, body = http_post(cfg["port"], cfg["score_path"], payload, timeout=30)
        if status in (200, 201) and isinstance(body, dict) and body.get("decision_id"):
            return domain, str(body["decision_id"]), None
        # Gates remain enforced, but rejected work is not a successful load test.
        return domain, None, f"HTTP {status}: {json.dumps(body)[:300]}"

    tasks = [(domain, i) for domain in COPILOTS for i in range(10)]
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        futures = [pool.submit(score_one, domain, index) for domain, index in tasks]
        for future in concurrent.futures.as_completed(futures):
            domain, decision_id, error = future.result()
            if decision_id:
                scored_ids.append((domain, decision_id))
            if error:
                errors.append(f"{domain}: {error}")

    result.checks.append(f"Scored {len(scored_ids)}/{len(tasks)} decisions")
    result.failures.extend(errors[:5])
    if len(errors) > 5:
        result.failures.append(f"...and {len(errors) - 5} more errors")
    if len(set(scored_ids)) != len(scored_ids):
        result.failures.append("Concurrent score requests returned duplicate decision IDs")
    for domain in COPILOTS:
        ids = [did for owner, did in scored_ids if owner == domain]
        persisted = sum(age.find_decision(did, domain) is not None for did in ids)
        result.checks.append(f"{domain}: {persisted}/10 exact decision IDs persisted in AGE")
        if len(ids) != 10 or persisted != 10:
            result.failures.append(f"{domain}: expected 10 persisted scores, received {len(ids)}, found {persisted}")
    result.passed = not result.failures
    return result


def phase_9(age: AGEVerifier) -> PhaseResult:
    """Health consistency: all copilots report same graph identity."""
    result = PhaseResult("9", "Health consistency", True)
    identities: set[str] = set()

    # Include SOC here (health works even without /api/score)
    all_copilots: dict[str, Any] = {**COPILOTS, "soc": {"port": 8001}}

    for domain, cfg in all_copilots.items():
        status, body = http_get(cfg["port"], "/health")
        if status != 200:
            result.failures.append(f"{domain}: health HTTP {status}")
            result.passed = False
            continue

        ready = body.get("ready")
        backend = body.get("graph_backend")
        connected = body.get("graph_connected")
        graph_name = body.get("graph_name", (body.get("graph_status") or {}).get("graph_name"))
        identity = (body.get("graph_status") or {}).get("storage_identity", "MISSING")

        checks_pass = all([
            ready is True,
            backend == "age",
            connected is True,
            graph_name == GRAPH_NAME,
            isinstance(identity, str) and identity not in {"", "MISSING", "unavailable"},
        ])

        if checks_pass:
            result.checks.append(f"{domain}: ready={ready} backend={backend} graph={graph_name}")
            identities.add(str(identity))
        else:
            result.failures.append(
                f"{domain}: ready={ready} backend={backend} connected={connected} graph={graph_name} identity={identity}"
            )
            result.passed = False

    if len(identities) == 1:
        result.checks.append(f"Reported graph identity: {next(iter(identities))}")
    elif len(identities) > 1:
        result.failures.append(f"INCONSISTENT identities: {identities}")
        result.passed = False
    elif len(identities) == 0:
        result.failures.append("No identities collected")
        result.passed = False

    return result


def phase_10(age: AGEVerifier) -> PhaseResult:
    """Compare active inventory and verified counts with the same AGE scopes."""
    result = PhaseResult("10", "Endpoint-vs-AGE data consistency", True)
    before = age.decision_counts("trading")
    status, body = http_get(8010, "/api/context/analytics")
    after = age.decision_counts("trading")
    if status == 200 and isinstance(body, dict):
        api_trades = body.get("total_trades", -1)
        # Bracket the read to allow actual concurrent writes, not arbitrary drift.
        if min(before["active"], after["active"]) <= api_trades <= max(before["active"], after["active"]):
            result.checks.append(
                f"Trading active inventory: API={api_trades}, AGE={after['active']}; "
                f"archives={after['archived']}, retained total={after['total']}"
            )
        else:
            result.failures.append(f"Trading: API={api_trades}, active AGE={before['active']}→{after['active']} — DIVERGED")
    else:
        result.failures.append(f"Trading analytics HTTP {status}")

    for domain, cfg in COPILOTS.items():
        before = age.decision_counts(domain)
        status, body = http_get(cfg["port"], "/api/conservation/status")
        after = age.decision_counts(domain)
        if status == 200 and isinstance(body, dict):
            verified = body.get("verified_count", -1)
            if min(before["verified"], after["verified"]) <= verified <= max(before["verified"], after["verified"]):
                result.checks.append(
                    f"{domain}: verified API={verified}, AGE={after['verified']}; "
                    f"active={after['active']}, archived={after['archived']}"
                )
            else:
                result.failures.append(f"{domain}: verified API={verified}, AGE={before['verified']}→{after['verified']}")
        else:
            result.failures.append(f"{domain}: conservation HTTP {status}")

    status, body = http_get(8002, "/api/s2p/preview/queue")
    # Count actual rows, not top-level response keys.
    if status == 200 and isinstance(body, dict) and body.get("source") == "graph":
        rows = body.get("invoices")
        if isinstance(rows, list) and rows:
            missing = [row.get("decision_id") for row in rows
                       if not age.find_decision(str(row.get("decision_id", "")), "s2p")]
            if missing:
                result.failures.append(f"S2P queue contains decisions absent from AGE: {missing}")
            else:
                result.checks.append(f"S2P queue: {len(rows)} displayed decisions verified in AGE")
        else:
            result.failures.append("S2P preview queue has no decision rows to verify")
    else:
        result.failures.append(
            f"S2P queue HTTP {status}: missing graph source/response contract; {json.dumps(body)[:300]}"
        )
    result.passed = not result.failures
    return result


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

PHASES: dict[str, Any] = {
    "1": phase_1, "2": phase_2, "3": phase_3,
    "4a": phase_4a, "4b": phase_4b,
    "5": phase_5, "6": phase_6, "7": phase_7,
    "8": phase_8, "9": phase_9, "10": phase_10,
}

ALL_PHASES = ["1", "2", "3", "4a", "4b", "5", "6", "7", "8", "9", "10"]


def run_phases(phase_ids: list[str], age: AGEVerifier) -> list[PhaseResult]:
    results = []
    for pid in phase_ids:
        fn = PHASES.get(pid)
        if fn is None:
            print(f"Unknown phase: {pid}")
            continue
        print(f"\n{'=' * 60}")
        doc = (fn.__doc__ or "").strip().split("\n")[0]
        print(f"PHASE {pid}: {doc}")
        print(f"{'=' * 60}")

        try:
            r = fn(age)
        except Exception as e:
            r = PhaseResult(pid, doc, False)
            r.failures.append(f"EXCEPTION: {type(e).__name__}: {e}")

        r.passed = r.passed and not r.failures
        results.append(r)
        for c in r.checks:
            print(f"  ✓ {c}")
        for f in r.failures:
            print(f"  ✗ {f}")
        status_str = "PASS" if r.passed else "FAIL"
        print(f"  → {status_str}")

        if pid == "4a":
            print("\n  *** RESTART REQUIRED — see instructions above ***")
            break

    return results


def print_summary(results: list[PhaseResult]) -> bool:
    print(f"\n{'=' * 60}")
    print("JM ARCHITECTURE STRESS TEST — SUMMARY")
    print(f"{'=' * 60}")
    all_pass = True
    for r in results:
        status_str = "PASS" if r.passed else "FAIL"
        marker = "✓" if r.passed else "✗"
        print(f"  {marker} Phase {r.phase:4s}  {r.name:40s}  {status_str}")
        if not r.passed:
            all_pass = False
            for f in r.failures[:3]:
                print(f"           ✗ {f}")

    print(f"\n{'=' * 60}")
    passed = sum(1 for r in results if r.passed)
    total = len(results)
    if all_pass:
        print(f"ALL {total} PHASES PASSED — selected live checks verified (not an architectural proof).")
    else:
        failed = total - passed
        print(f"{passed}/{total} passed, {failed} FAILED — see details above.")
    print(f"{'=' * 60}")
    return all_pass


def main():
    # Windows redirects stdout through the active ANSI code page. The report
    # uses Unicode status glyphs and arrows, so set its encoding explicitly.
    reconfigure = getattr(sys.stdout, "reconfigure", None)
    if callable(reconfigure):
        reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(description="JM Architecture Stress Test")
    parser.add_argument("--skip-restart", action="store_true",
                        help="Skip phases 4a/4b (no restart needed)")
    parser.add_argument("--phase", type=str,
                        help="Run a single phase (e.g., --phase 7)")
    parser.add_argument("--from-phase", type=str,
                        help="Resume from phase (e.g., --from-phase 4b)")
    parser.add_argument("--dsn", type=str, default=AGE_DSN, help="AGE DSN")
    parser.add_argument("--graph", type=str, default=GRAPH_NAME, help="Graph name")
    args = parser.parse_args()

    print("JM Architecture Stress Test v2")
    print("DSN: configured (credentials redacted)")
    print(f"Graph: {args.graph}")
    print()

    # Initialize AGE verifier
    print("Initializing AGE verifier...")
    try:
        age = AGEVerifier(args.dsn, args.graph)
        counts = age.all_domain_counts()
        total = sum(counts.values())
        print(f"  AGE: {total} decisions across {len(counts)} domains")
        for d, c in sorted(counts.items()):
            print(f"    {d}: {c}")
    except Exception as e:
        print(f"  AGE UNREACHABLE: {type(e).__name__}: {e}")
        print("  Ensure AGE is running and DSN is correct.")
        sys.exit(1)

    # Check copilots
    print("\nChecking copilots...")
    all_copilots: dict[str, Any] = {**COPILOTS, "soc": {"port": 8001}}
    for domain, cfg in all_copilots.items():
        status, _ = http_get(cfg["port"], "/health", timeout=5)
        marker = "✓" if status == 200 else "✗"
        print(f"  {marker} {domain} (:{cfg['port']}): HTTP {status}")
        if status != 200:
            print(f"  Start all copilots first: python demo.py --no-browser")
            sys.exit(1)

    # Select phases
    if args.phase:
        phase_ids = [args.phase]
    elif args.from_phase:
        idx = ALL_PHASES.index(args.from_phase)
        phase_ids = ALL_PHASES[idx:]
    elif args.skip_restart:
        phase_ids = [p for p in ALL_PHASES if p not in ("4a", "4b")]
    else:
        phase_ids = ALL_PHASES

    results = run_phases(phase_ids, age)
    all_pass = print_summary(results)
    sys.exit(0 if all_pass else 1)


if __name__ == "__main__":
    main()
