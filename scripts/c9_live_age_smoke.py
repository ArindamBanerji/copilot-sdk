from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit, urlunsplit


NON_SOC_DOMAINS = ("trading", "purchasing", "dataops", "s2p")
SDK_DOMAINS = {"trading", "purchasing", "dataops"}
DEFAULT_GRAPH_NAME = "soc_graph"
READINESS_READY = "READY_FOR_C9_RERUN"
READINESS_PARTIAL = "PARTIAL_SEE_MISSING"
READINESS_FAIL = "FAIL_NEEDS_FIXER"
READINESS_BLOCKED = "BLOCKED_ENV"


@dataclass(frozen=True)
class DomainPlan:
    domain: str
    loops: int
    method: str


@dataclass
class DomainRunResult:
    domain: str
    method: str
    attempted: int = 0
    succeeded: int = 0
    failed: int = 0
    unsupported_reason: str | None = None
    failures: list[str] = field(default_factory=list)


@dataclass
class SmokeSummary:
    verdict: str
    graph_name: str
    dsn_redacted: str
    domains_requested: list[str]
    domains_exercised: list[str]
    route_results: dict[str, dict[str, Any]]
    before: dict[str, Any] | None
    after: dict[str, Any] | None
    missing_cells: list[dict[str, str]]
    transition_notes: dict[str, str]
    next_action: str


def project_root() -> Path:
    script = Path(__file__).resolve()
    return script.parents[2]


def configure_paths(root: Path | None = None) -> None:
    root = root or project_root()
    for path in (
        root / "copilot-sdk",
        root / "ci-platform",
        root / "s2p-copilot" / "backend",
        root / "graph-attention-engine-v50",
    ):
        text = str(path)
        if path.exists() and text not in sys.path:
            sys.path.insert(0, text)


def parse_domains(value: str | None, single: str | None = None) -> list[str]:
    raw: list[str] = []
    if value:
        raw.extend(part.strip() for part in value.split(","))
    if single:
        raw.append(single.strip())
    domains: list[str] = []
    for domain in raw:
        if not domain:
            continue
        if domain not in NON_SOC_DOMAINS:
            raise ValueError(f"unsupported domain {domain!r}; expected one of {', '.join(NON_SOC_DOMAINS)}")
        if domain not in domains:
            domains.append(domain)
    return domains or list(NON_SOC_DOMAINS)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run C9 live AGE route smoke/seeding and readback checks."
    )
    parser.add_argument("--domain", help="single domain to exercise")
    parser.add_argument("--domains", help="comma-separated domains to exercise")
    parser.add_argument("--loops", type=int, default=1, help="score/learn loops per domain")
    parser.add_argument("--readback", action="store_true", help="query AGE after route loops")
    parser.add_argument("--readback-only", action="store_true", help="query AGE without route loops")
    parser.add_argument("--graph-name", default=os.getenv("AGE_GRAPH_NAME", DEFAULT_GRAPH_NAME))
    parser.add_argument("--database-url", default=os.getenv("DATABASE_URL"))
    parser.add_argument("--json", action="store_true", help="print stable JSON summary as final output")
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument("--dry-run", action="store_true", help="print plan without route loops or AGE queries")
    return parser


def redact_dsn(dsn: str | None) -> str:
    if not dsn:
        return "(unset)"
    if "://" in dsn:
        try:
            parts = urlsplit(dsn)
            if parts.password is None:
                return dsn
            user = parts.username or ""
            host = parts.hostname or ""
            port = f":{parts.port}" if parts.port else ""
            netloc = f"{user}:***@{host}{port}"
            return urlunsplit((parts.scheme, netloc, parts.path, parts.query, parts.fragment))
        except Exception:
            pass
    return re.sub(r"(password=)(\S+)", r"\1***", dsn, flags=re.IGNORECASE)


def graph_dsn_is_passwordless(dsn: str | None) -> bool:
    if not dsn:
        return False
    if "password=" in dsn.lower():
        return False
    if "://" in dsn:
        parts = urlsplit(dsn)
        return bool(parts.username) and parts.password is None
    return "user=" in dsn.lower()


def choose_database_url(database_url: str | None, graph_dsn: str | None = None) -> tuple[str | None, str]:
    if database_url:
        reason = "DATABASE_URL"
        if graph_dsn and graph_dsn_is_passwordless(graph_dsn):
            reason += " (ignored passwordless GRAPH_DSN)"
        return database_url, reason
    if graph_dsn and not graph_dsn_is_passwordless(graph_dsn):
        return graph_dsn, "GRAPH_DSN"
    return None, "missing DATABASE_URL; GRAPH_DSN is unset or passwordless"


def domain_plan(domains: list[str], loops: int) -> list[DomainPlan]:
    if loops <= 0:
        raise ValueError("--loops must be positive")
    plans = []
    for domain in domains:
        method = "SDK TestClient /score -> /learn" if domain in SDK_DOMAINS else "S2P TestClient /api/s2p/score -> /api/learn"
        plans.append(DomainPlan(domain=domain, loops=loops, method=method))
    return plans


def factor_payload(factor_names: list[str] | tuple[str, ...], i: int) -> dict[str, float]:
    high = i % 2 == 0
    values = []
    for index, _name in enumerate(factor_names):
        if high:
            values.append(0.9 if index % 2 == 0 else 0.2)
        else:
            values.append(0.1 if index % 2 == 0 else 0.8)
    return dict(zip(factor_names, values))


def make_age_store(database_url: str, graph_name: str) -> Any:
    configure_paths()
    from ci_platform.graph.age_sdk_adapter import AGEGraphStoreAdapter

    return AGEGraphStoreAdapter(dsn=database_url, graph_name=graph_name)


def run_sdk_domain(domain: str, loops: int, database_url: str, graph_name: str) -> DomainRunResult:
    configure_paths()
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    from copilot_sdk.backend.scoring_router import create_scoring_router
    from copilot_sdk.scoring.dk_persistence import DKWelfordTracker
    from copilot_sdk.scoring.scorer import CompoundingScorer

    store = make_age_store(database_url, graph_name)
    scorer = CompoundingScorer.from_preset(domain, graph_store=store, enable_rl=False)
    tracker = DKWelfordTracker()
    app = FastAPI()
    app.include_router(
        create_scoring_router(
            domain,
            scorer_factory=lambda: scorer,
            learning_store=store,
            dk_welford_tracker=tracker,
        )
    )
    client = TestClient(app)
    result = DomainRunResult(domain=domain, method="SDK TestClient /score -> /learn", attempted=loops)
    category = list(scorer._preset.shape.category_names)[0]
    factor_names = list(scorer._preset.shape.factor_names)
    action_names = list(scorer._preset.shape.action_names)
    for i in range(loops):
        try:
            score = client.post(
                "/score",
                json={"category": category, "factors": factor_payload(factor_names, i)},
            )
            if score.status_code != 200:
                raise RuntimeError(f"/score {score.status_code}: {score.text}")
            score_payload = score.json()
            actual_action = score_payload.get("action") or action_names[0]
            if i >= 200 and len(action_names) > 1 and i % 5 == 0:
                actual_action = action_names[(action_names.index(actual_action) + 1) % len(action_names)]
            learn = client.post(
                "/learn",
                json={
                    "decision_id": score_payload["decision_id"],
                    "actual_action": actual_action,
                    "outcome": "confirmed" if actual_action == score_payload.get("action") else "override",
                },
            )
            if learn.status_code != 200:
                raise RuntimeError(f"/learn {learn.status_code}: {learn.text}")
            result.succeeded += 1
        except Exception as exc:
            result.failed += 1
            result.failures.append(f"loop {i}: {exc}")
    return result


def run_s2p_domain(loops: int, database_url: str, graph_name: str) -> DomainRunResult:
    configure_paths()
    try:
        from fastapi.testclient import TestClient

        from app.main import app, build_s2p_scorer
        from app.routers import s2p as s2p_router
        from copilot_sdk.scoring.dk_persistence import DKWelfordTracker
    except Exception as exc:
        return DomainRunResult(
            domain="s2p",
            method="S2P TestClient",
            attempted=0,
            unsupported_reason=f"S2P imports unavailable: {exc}",
        )

    store = make_age_store(database_url, graph_name)
    scorer = build_s2p_scorer(graph_store=store)
    app.state.scorer = scorer
    app.state.graph_store = store
    app.state.learning_store = store
    s2p_router._S2P_DK_WELFORD_TRACKER = DKWelfordTracker()
    client = TestClient(app)
    result = DomainRunResult(domain="s2p", method="S2P TestClient /api/s2p/score -> /api/learn", attempted=loops)
    category = "price_variance"
    action_names = list(scorer._preset.shape.action_names)
    for i in range(loops):
        try:
            score = client.post(
                "/api/s2p/score",
                json={
                    "event_id": f"C9-S2P-{i:04d}",
                    "category": category,
                    "amount": 1000.0 + i,
                    "supplier_id": "SUP-C9",
                    "contract_id": "CON-C9",
                    "supplier_risk_rating": 0.2 if i % 2 == 0 else 0.8,
                    "historical_spend_mean": 900.0,
                    "historical_spend_std": 100.0,
                    "duplicate_score": 0.1 if i % 2 == 0 else 0.9,
                    "commodity_index_delta": 0.05,
                    "payment_terms_days": 30,
                    "tax_compliance_score": 0.9,
                },
            )
            if score.status_code != 200:
                raise RuntimeError(f"/api/s2p/score {score.status_code}: {score.text}")
            score_payload = score.json()
            actual_action = score_payload.get("action") or action_names[0]
            if i >= 200 and len(action_names) > 1 and i % 5 == 0:
                actual_action = action_names[(action_names.index(actual_action) + 1) % len(action_names)]
            learn = client.post(
                "/api/learn",
                json={
                    "decision_id": score_payload["decision_id"],
                    "actual_action": actual_action,
                    "outcome": "confirmed" if actual_action == score_payload.get("action") else "override",
                },
            )
            if learn.status_code != 200:
                raise RuntimeError(f"/api/learn {learn.status_code}: {learn.text}")
            result.succeeded += 1
        except Exception as exc:
            result.failed += 1
            result.failures.append(f"loop {i}: {exc}")
    return result


def run_domain(plan: DomainPlan, database_url: str, graph_name: str) -> DomainRunResult:
    if plan.domain in SDK_DOMAINS:
        return run_sdk_domain(plan.domain, plan.loops, database_url, graph_name)
    if plan.domain == "s2p":
        return run_s2p_domain(plan.loops, database_url, graph_name)
    return DomainRunResult(
        domain=plan.domain,
        method="unsupported",
        unsupported_reason=f"unsupported domain: {plan.domain}",
    )


def _count_rows(rows: list[dict[str, Any]], domain_key: str = "domain", count_key: str = "cnt") -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        domain = str(row.get(domain_key) or "null")
        counts[domain] = int(row.get(count_key) or 0)
    return counts


def readback_from_store(store: Any, domains: list[str]) -> dict[str, Any]:
    query = getattr(store, "_run_query", None)
    if query is None and hasattr(store, "_store"):
        query = getattr(store._store, "_run_query", None)
    if not callable(query):
        raise RuntimeError("AGE readback requires AGEGraphStore or AGEGraphStoreAdapter")

    def run(cypher: str) -> list[dict[str, Any]]:
        return list(query(cypher) or [])

    centroids = _count_rows(run("MATCH (c:L5Centroid) RETURN c.domain AS domain, count(c) AS cnt ORDER BY domain"))
    dk_weights = _count_rows(run("MATCH (w:L5DKWeight) RETURN w.domain AS domain, count(w) AS cnt ORDER BY domain"))
    shaped = _count_rows(run("MATCH (c:L5Centroid)-[:SHAPED_BY]->(d:Decision) RETURN c.domain AS domain, count(*) AS cnt ORDER BY domain"))
    triggered = _count_rows(run("MATCH (cs:L5ConservationState)-[:TRIGGERED_BY]->(d:Decision) RETURN cs.domain AS domain, count(*) AS cnt ORDER BY domain"))
    decisions = run("MATCH (d:Decision) RETURN d.domain AS domain, d.status AS status, count(d) AS cnt ORDER BY domain, status")
    conservation_rows = run(
        "MATCH (cs:L5ConservationState) RETURN cs.domain AS domain, cs.status AS status, count(cs) AS cnt ORDER BY domain, status"
    )
    welford_rows = run(
        """
        MATCH (w:L5DKWeight)
        RETURN w.domain AS domain,
               count(w) AS cnt,
               count(w.confirmed_mean_json) AS confirmed_mean,
               count(w.confirmed_m2_json) AS confirmed_m2,
               count(w.overridden_mean_json) AS overridden_mean,
               count(w.overridden_m2_json) AS overridden_m2,
               count(w.all_mean_json) AS all_mean,
               count(w.all_m2_json) AS all_m2
        ORDER BY domain
        """
    )
    samples = {
        "centroids": run(
            "MATCH (c:L5Centroid) RETURN c.domain AS domain, c.category AS category, c.action AS action, c.caused_by_decision_id AS caused_by_decision_id, c.delta_norm AS delta_norm ORDER BY domain, category, action LIMIT 25"
        ),
        "dk_weights": run(
            "MATCH (w:L5DKWeight) RETURN w.domain AS domain, w.dk_weight_id AS dk_weight_id, w.n_decisions_used AS n_decisions_used, w.n_confirmed AS n_confirmed, w.n_overridden AS n_overridden, w.entity_group AS entity_group, w.created_at AS created_at ORDER BY domain, created_at DESC LIMIT 25"
        ),
        "conservation": run(
            "MATCH (cs:L5ConservationState) RETURN cs.domain AS domain, cs.status AS status, cs.old_status AS old_status, cs.caused_by_decision_id AS caused_by_decision_id, cs.updated_at AS updated_at ORDER BY domain, updated_at DESC LIMIT 25"
        ),
    }
    conservation: dict[str, dict[str, Any]] = {}
    for row in conservation_rows:
        domain = str(row.get("domain") or "null")
        conservation.setdefault(domain, {"count": 0, "statuses": {}})
        conservation[domain]["count"] += int(row.get("cnt") or 0)
        conservation[domain]["statuses"][str(row.get("status") or "null")] = int(row.get("cnt") or 0)
    welford: dict[str, dict[str, Any]] = {}
    for row in welford_rows:
        domain = str(row.get("domain") or "null")
        count = int(row.get("cnt") or 0)
        fields = {
            key: int(row.get(key) or 0)
            for key in (
                "confirmed_mean",
                "confirmed_m2",
                "overridden_mean",
                "overridden_m2",
                "all_mean",
                "all_m2",
            )
        }
        welford[domain] = {
            "count": count,
            "fields": fields,
            "present": count > 0 and all(value > 0 for value in fields.values()),
        }
    return {
        "decision_status": decisions,
        "L5Centroid": centroids,
        "L5DKWeight": dk_weights,
        "L5ConservationState": conservation,
        "Welford": welford,
        "SHAPED_BY": shaped,
        "TRIGGERED_BY": triggered,
        "samples": samples,
        "domains": domains,
    }


def missing_cells(readback: dict[str, Any], domains: list[str]) -> list[dict[str, str]]:
    missing: list[dict[str, str]] = []
    for domain in domains:
        if int(readback.get("L5Centroid", {}).get(domain, 0)) <= 0:
            missing.append({"domain": domain, "cell": "L5Centroid", "reason": "count is zero"})
        if int(readback.get("L5DKWeight", {}).get(domain, 0)) <= 0:
            missing.append({"domain": domain, "cell": "L5DKWeight", "reason": "count is zero"})
        conservation = readback.get("L5ConservationState", {}).get(domain, {})
        if int(conservation.get("count", 0)) <= 0:
            missing.append({"domain": domain, "cell": "L5ConservationState", "reason": "count is zero"})
        welford = readback.get("Welford", {}).get(domain, {})
        if not bool(welford.get("present")):
            missing.append({"domain": domain, "cell": "DKWeight Welford", "reason": "one or more Welford fields missing"})
        if int(readback.get("SHAPED_BY", {}).get(domain, 0)) <= 0:
            missing.append({"domain": domain, "cell": "SHAPED_BY", "reason": "edge count is zero"})
    return missing


def transition_notes(readback: dict[str, Any], domains: list[str]) -> dict[str, str]:
    notes = {}
    for domain in domains:
        count = int(readback.get("TRIGGERED_BY", {}).get(domain, 0))
        notes[domain] = "present" if count > 0 else "transition not exercised"
    return notes


def classify_readiness(
    readback: dict[str, Any] | None,
    domains: list[str],
    route_results: dict[str, DomainRunResult] | None = None,
) -> tuple[str, list[dict[str, str]], dict[str, str]]:
    if readback is None:
        return READINESS_BLOCKED, [{"domain": "*", "cell": "readback", "reason": "AGE readback unavailable"}], {}
    missing = missing_cells(readback, domains)
    notes = transition_notes(readback, domains)
    route_unsupported = False
    route_failed = False
    for result in (route_results or {}).values():
        if result.unsupported_reason:
            route_unsupported = True
            missing.append(
                {
                    "domain": result.domain,
                    "cell": "route",
                    "reason": result.unsupported_reason,
                }
            )
        if result.failed:
            route_failed = True
            missing.append(
                {
                    "domain": result.domain,
                    "cell": "route",
                    "reason": f"{result.failed} route loop(s) failed",
                }
            )
    if missing:
        if route_failed:
            return READINESS_FAIL, missing, notes
        return READINESS_PARTIAL, missing, notes
    if route_unsupported:
        return READINESS_PARTIAL, missing, notes
    if route_failed:
        return READINESS_FAIL, missing, notes
    return READINESS_READY, missing, notes


def print_human_summary(summary: SmokeSummary, *, verbose: bool = False) -> None:
    print("C9 live AGE smoke")
    print(f"graph: {summary.graph_name}")
    print(f"dsn: {summary.dsn_redacted}")
    print(f"domains requested: {', '.join(summary.domains_requested)}")
    print(f"domains exercised: {', '.join(summary.domains_exercised) or '(none)'}")
    if summary.before is not None:
        print("before counts:")
        print(json.dumps({k: summary.before.get(k) for k in ("L5Centroid", "L5DKWeight", "L5ConservationState", "Welford", "SHAPED_BY", "TRIGGERED_BY")}, indent=2, sort_keys=True))
    if summary.route_results:
        print("route results:")
        for domain, result in summary.route_results.items():
            print(f"- {domain}: {result.get('succeeded', 0)}/{result.get('attempted', 0)} succeeded via {result.get('method')}")
            if result.get("unsupported_reason"):
                print(f"  unsupported: {result['unsupported_reason']}")
            if verbose:
                for failure in result.get("failures", []):
                    print(f"  failure: {failure}")
    if summary.after is not None:
        print("after counts:")
        print(json.dumps({k: summary.after.get(k) for k in ("L5Centroid", "L5DKWeight", "L5ConservationState", "Welford", "SHAPED_BY", "TRIGGERED_BY")}, indent=2, sort_keys=True))
    print("missing cells:")
    if summary.missing_cells:
        for item in summary.missing_cells:
            print(f"- {item['domain']} {item['cell']}: {item['reason']}")
    else:
        print("- NONE")
    if summary.transition_notes:
        print("TRIGGERED_BY:")
        for domain, note in summary.transition_notes.items():
            print(f"- {domain}: {note}")
    print(f"C9 readiness verdict: {summary.verdict}")
    print(f"next action: {summary.next_action}")


def run(args: argparse.Namespace) -> SmokeSummary:
    domains = parse_domains(args.domains, args.domain)
    plans = domain_plan(domains, args.loops)
    dsn, dsn_source = choose_database_url(args.database_url, os.getenv("GRAPH_DSN"))
    route_results: dict[str, DomainRunResult] = {}
    before = None
    after = None
    if args.dry_run:
        dry_run_missing = [{"domain": "*", "cell": "dry-run", "reason": "route loops and AGE readback not executed"}]
        return SmokeSummary(
            verdict=READINESS_PARTIAL,
            graph_name=args.graph_name,
            dsn_redacted=redact_dsn(dsn),
            domains_requested=domains,
            domains_exercised=[],
            route_results={plan.domain: asdict(DomainRunResult(plan.domain, plan.method, attempted=plan.loops)) for plan in plans},
            before=None,
            after=None,
            missing_cells=dry_run_missing,
            transition_notes={},
            next_action=f"dry run only; DSN source would be {dsn_source}",
        )
    if dsn is None:
        return SmokeSummary(
            verdict=READINESS_BLOCKED,
            graph_name=args.graph_name,
            dsn_redacted="(unset)",
            domains_requested=domains,
            domains_exercised=[],
            route_results={},
            before=None,
            after=None,
            missing_cells=[{"domain": "*", "cell": "environment", "reason": dsn_source}],
            transition_notes={},
            next_action="set DATABASE_URL to a live AGE/Postgres DSN",
        )
    try:
        store = make_age_store(dsn, args.graph_name)
    except Exception as exc:
        return SmokeSummary(
            verdict=READINESS_BLOCKED,
            graph_name=args.graph_name,
            dsn_redacted=redact_dsn(dsn),
            domains_requested=domains,
            domains_exercised=[],
            route_results={},
            before=None,
            after=None,
            missing_cells=[{"domain": "*", "cell": "environment", "reason": f"AGE store unavailable: {exc}"}],
            transition_notes={},
            next_action="fix live AGE imports, DSN, or graph connectivity",
        )
    if args.readback or args.readback_only:
        try:
            before = readback_from_store(store, domains)
        except Exception as exc:
            return SmokeSummary(
                verdict=READINESS_BLOCKED,
                graph_name=args.graph_name,
                dsn_redacted=redact_dsn(dsn),
                domains_requested=domains,
                domains_exercised=[],
                route_results={},
                before=None,
                after=None,
                missing_cells=[{"domain": "*", "cell": "readback", "reason": str(exc)}],
                transition_notes={},
                next_action="fix live AGE readback access or query compatibility",
            )
    if not args.readback_only:
        for plan in plans:
            route_results[plan.domain] = run_domain(plan, dsn, args.graph_name)
    if args.readback or args.readback_only:
        try:
            after = readback_from_store(store, domains)
        except Exception as exc:
            return SmokeSummary(
                verdict=READINESS_BLOCKED,
                graph_name=args.graph_name,
                dsn_redacted=redact_dsn(dsn),
                domains_requested=domains,
                domains_exercised=[domain for domain, result in route_results.items() if result.succeeded],
                route_results={domain: asdict(result) for domain, result in route_results.items()},
                before=before,
                after=None,
                missing_cells=[{"domain": "*", "cell": "readback", "reason": str(exc)}],
                transition_notes={},
                next_action="fix live AGE readback access or query compatibility",
            )
    readback = after or before
    verdict, missing, notes = classify_readiness(readback, domains, route_results)
    next_action = (
        "rerun C9 manual L5 proof"
        if verdict == READINESS_READY
        else "targeted route/runtime fixer"
        if verdict == READINESS_FAIL
        else "rerun smoke with more loops or inspect missing cells"
        if verdict == READINESS_PARTIAL
        else "fix live AGE environment"
    )
    return SmokeSummary(
        verdict=verdict,
        graph_name=args.graph_name,
        dsn_redacted=redact_dsn(dsn),
        domains_requested=domains,
        domains_exercised=[domain for domain, result in route_results.items() if result.succeeded],
        route_results={domain: asdict(result) for domain, result in route_results.items()},
        before=before,
        after=after,
        missing_cells=missing,
        transition_notes=notes,
        next_action=next_action,
    )


def main(argv: list[str] | None = None) -> int:
    configure_paths()
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        summary = run(args)
    except Exception as exc:
        summary = SmokeSummary(
            verdict=READINESS_FAIL,
            graph_name=getattr(args, "graph_name", DEFAULT_GRAPH_NAME),
            dsn_redacted=redact_dsn(getattr(args, "database_url", None)),
            domains_requested=[],
            domains_exercised=[],
            route_results={},
            before=None,
            after=None,
            missing_cells=[{"domain": "*", "cell": "runner", "reason": str(exc)}],
            transition_notes={},
            next_action="targeted runner/environment fixer",
        )
    if not args.json:
        print_human_summary(summary, verbose=args.verbose)
    if args.json:
        print(json.dumps(asdict(summary), sort_keys=True))
    return 0 if summary.verdict in {READINESS_READY, READINESS_PARTIAL, READINESS_BLOCKED} else 1


if __name__ == "__main__":
    raise SystemExit(main())
