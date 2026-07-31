"""Shared, failure-isolated runtime diagnostics contract."""
from __future__ import annotations

import math
import os
import time
from typing import Any

from pydantic import BaseModel, Field
from copilot_sdk.graph.protocol import ProtocolV2GraphStore
from copilot_sdk.scoring.scorer import CompoundingScorer


class InfrastructureDiag(BaseModel):
    graph_backend: str = "unavailable"
    graph_name: str = "unavailable"
    graph_dsn_reachable: bool = False
    store_class: str = "unavailable"
    protocol_v2: bool = False
    status: str = "fail"
    error: str | None = None


class ScorerDiag(BaseModel):
    centroid_source: str = "unavailable"
    verified_count: int | None = None
    correct_count: int | None = None
    accuracy: float | None = None
    total_categories: int | None = None
    categories_with_decisions: int | None = None
    tensor_shape: list[int] = Field(default_factory=list)
    learned_values: int | None = None
    iks_score: float | None = None
    status: str = "degraded"
    error: str | None = None


class ConservationDiag(BaseModel):
    status: str = "degraded"
    conservation_status: str = "unavailable"
    V: int | None = None
    q: float | None = None
    alpha: float | None = None
    alpha_source: str = "unavailable"
    theta_min: float | None = None
    effective_q: float | None = None
    gate_passes: bool | None = None
    learning_paused: bool | None = None
    pause_reason: str | None = None
    formula: str = "alpha * q * V >= theta_min"
    error: str | None = None


class J6ReadinessDiag(BaseModel):
    store_protocol_v2: bool = False
    domain_anchor_exists: bool | None = None
    outbox_path: str | None = None
    outbox_pending: int | None = None
    outbox_total: int | None = None
    conservation_snapshot_writable: bool = False
    status: str = "blocked"
    error: str | None = None


class ArtifactsDiag(BaseModel):
    decisions: int | None = None
    conservation_snapshots: int | None = None
    centroid_checkpoints: int | None = None
    fingerprints: int | None = None
    evidence_receipts: int | None = None
    transfer_patterns_as_source: int | None = None
    transfer_patterns_as_target: int | None = None
    outcomes: int | None = None
    domain_anchor: bool | None = None
    status: str = "incomplete"
    error: str | None = None


class DiagnosticsResponse(BaseModel):
    domain: str
    timestamp: float
    infrastructure: InfrastructureDiag
    scorer_state: ScorerDiag
    conservation: ConservationDiag
    j6_readiness: J6ReadinessDiag
    graph_artifacts: ArtifactsDiag
    issues: list[str] = Field(default_factory=list)
    copilot_specific: dict[str, Any] = Field(default_factory=dict)
    layers: dict[str, Any] = Field(default_factory=dict)


def _call(obj: Any, name: str, *args: Any, **kwargs: Any) -> Any:
    fn = getattr(obj, name, None)
    if not callable(fn):
        raise AttributeError(f"{type(obj).__name__}.{name} unavailable")
    return fn(*args, **kwargs)


def _count_rows(
    store: Any,
    method: str,
    domain: str,
    issues: list[str] | None = None,
) -> int | None:
    try:
        return int(_call(store, method, domain))
    except Exception as exc:
        if issues is not None:
            issues.append(f"graph_artifacts {method}: {type(exc).__name__}: {exc}")
        return None


def _protocol_store(store: Any) -> ProtocolV2GraphStore | None:
    """Resolve protocol-capable stores hidden behind app adapters."""
    pending = [store]
    seen: set[int] = set()
    while pending:
        candidate = pending.pop(0)
        if candidate is None or id(candidate) in seen:
            continue
        seen.add(id(candidate))
        if isinstance(candidate, ProtocolV2GraphStore):
            return candidate
        for attr in ("_store", "store", "_graph_store"):
            inner = getattr(candidate, attr, None)
            if inner is not None:
                pending.append(inner)
    return None


def _query_runner(store: Any) -> Any:
    """Find the raw AGE query hook through nested store adapters."""
    pending = [store]
    seen: set[int] = set()
    while pending:
        candidate = pending.pop(0)
        if candidate is None or id(candidate) in seen:
            continue
        seen.add(id(candidate))
        runner = getattr(candidate, "_run_query", None)
        if callable(runner):
            return runner
        for attr in ("_store", "store", "_graph_store"):
            inner = getattr(candidate, attr, None)
            if inner is not None:
                pending.append(inner)
    raise AttributeError("AGE query hook unavailable")


def _shape(scorer: Any) -> list[int]:
    for owner in (
        scorer,
        getattr(scorer, "_scorer", None),
        getattr(scorer, "gae_scorer", None),
    ):
        centroids = getattr(owner, "centroids", None)
        if centroids is None:
            centroids = getattr(owner, "mu", None)
        if centroids is not None and hasattr(centroids, "shape"):
            return [int(v) for v in centroids.shape]
    preset_shape = getattr(getattr(scorer, "_preset", None), "shape", None)
    dims = getattr(preset_shape, "dims", None)
    if dims is not None:
        return [int(v) for v in dims]
    names = ("n_categories", "n_actions", "n_factors")
    return [int(getattr(preset_shape, name)) for name in names if hasattr(preset_shape, name)]


def _centroid_source(scorer: Any) -> str:
    return _centroid_source_with_status(scorer, None)


def _centroid_source_with_status(scorer: Any, startup_status: Any) -> str:
    for value in (
        getattr(scorer, "_centroid_source", None),
        getattr(scorer, "centroid_source", None),
    ):
        if value:
            return str(value)
    if isinstance(startup_status, dict) and startup_status.get("centroid_source"):
        return str(startup_status["centroid_source"])
    for attr in ("startup_status", "l5_startup_status"):
        value = getattr(scorer, attr, None)
        if isinstance(value, dict) and value.get("centroid_source"):
            return str(value["centroid_source"])
    if _shape(scorer):
        return "cold_start"
    return "unavailable"


def _unwrap_scorer(scorer: Any, _seen: set[int] | None = None) -> CompoundingScorer | None:
    """Unwrap the scorer proxy layers used by the five copilot backends."""
    if scorer is None:
        return None
    if isinstance(scorer, CompoundingScorer):
        return scorer
    seen = _seen or set()
    if id(scorer) in seen:
        return None
    seen.add(id(scorer))
    for attr in ("_compound", "_scorer_proxy", "_scorer_instance", "_scorer", "scorer", "inner"):
        try:
            inner = getattr(scorer, attr, None)
            if callable(inner):
                inner = inner()
        except Exception:
            continue
        result = _unwrap_scorer(inner, seen)
        if result is not None:
            return result
    return None


def _artifact_count(
    store: Any,
    domain: str,
    names: tuple[str, ...],
    *,
    include_v2: bool = False,
) -> int | None:
    for name in names:
        try:
            kwargs = {"include_v2": True} if include_v2 and name == "get_centroid_checkpoints" else {}
            value = _call(store, name, domain, **kwargs)
            if isinstance(value, (list, tuple, set, dict)):
                return len(value)
            return int(value)
        except Exception:
            continue
    return None


def _cypher_count(
    store: Any,
    label: str,
    domain: str,
    *,
    edge_direction: str | None = None,
) -> int:
    """Use the live AGE store query hook when a typed count is unavailable."""
    runner = _query_runner(store)
    escaped = str(domain).replace("\\", "\\\\").replace("'", "\\'")
    if label == "Domain":
        rows = runner(
            f"MATCH (n:Domain) WHERE n.domain_id = '{escaped}' "
            "RETURN count(n) AS cnt"
        )
    elif edge_direction == "source":
        rows = runner(
            f"MATCH (n:TransferPattern)-[:FROM_DOMAIN]->(d:Domain) "
            f"WHERE d.domain_id = '{escaped}' RETURN count(n) AS cnt"
        )
    elif edge_direction == "target":
        rows = runner(
            f"MATCH (n:TransferPattern)-[:TO_DOMAIN]->(d:Domain) "
            f"WHERE d.domain_id = '{escaped}' RETURN count(n) AS cnt"
        )
    else:
        rows = runner(
            f"MATCH (n:{label}) WHERE n.domain = '{escaped}' "
            "RETURN count(n) AS cnt"
        )
    if not rows:
        return 0
    row = rows[0]
    if isinstance(row, dict):
        return int(row.get("cnt", 0))
    return int(row[0])


def _safe_cypher_count(
    store: Any,
    label: str,
    domain: str,
    issues: list[str],
    *,
    edge_direction: str | None = None,
) -> int | None:
    try:
        return _cypher_count(store, label, domain, edge_direction=edge_direction)
    except Exception as exc:
        issues.append(f"graph_artifacts {label}: {type(exc).__name__}: {exc}")
        return None


def _decision_count(store: Any, domain: str, issues: list[str]) -> int | None:
    active = _count_rows(store, "count_decisions", domain, issues)
    if active is None:
        issues.append("graph_artifacts Decision: count_decisions unavailable")
        return None
    archived = _count_rows(store, "count_archived", domain, issues)
    return active + archived if archived is not None else active


def build_diagnostics(
    domain: str,
    scorer: Any,
    graph_store: Any | None = None,
    *,
    extras: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Read diagnostics from the live scorer and its injected store only."""
    issues: list[str] = []
    live_scorer = _unwrap_scorer(scorer) or scorer
    if graph_store is not None:
        store = graph_store
    elif live_scorer is not None:
        store = getattr(live_scorer, "graph_store", None) or getattr(live_scorer, "_graph_store", None)
    else:
        store = None
    infra = InfrastructureDiag()
    if store is None:
        infra.error = "live graph store unavailable"
        issues.append("infrastructure: live graph store unavailable")
    else:
        infra.store_class = type(store).__name__
        try:
            config = getattr(store, "graph_config", None)
            backend = getattr(config, "backend", None) or getattr(store, "backend", None)
            infra.graph_backend = str(backend or os.environ.get("GRAPH_BACKEND") or "unavailable")
            graph = getattr(config, "graph", None) or getattr(store, "graph_name", None) or getattr(store, "_graph_name", None)
            infra.graph_name = str(graph or os.environ.get("AGE_GRAPH_NAME") or "unavailable")
            infra.protocol_v2 = _protocol_store(store) is not None
            _call(store, "get_decisions", domain, limit=1)
            infra.graph_dsn_reachable = True
            infra.status = "ok"
        except Exception as exc:
            infra.error = str(exc)
            issues.append(f"infrastructure: {exc}")

    response_extras = extras or {}
    startup_status = response_extras.get("l5_startup_status") or response_extras.get("startup_status")
    scorer_diag = ScorerDiag(
        centroid_source=(
            _centroid_source_with_status(live_scorer, startup_status)
            if live_scorer is not None
            else "unavailable"
        )
    )
    if live_scorer is not None:
        try:
            verified = int(_call(live_scorer, "get_verified_count"))
            correct = _count_rows(store, "count_correct", domain, issues) if store is not None else None
            shape = _shape(live_scorer)
            scorer_diag.tensor_shape = shape
            scorer_diag.learned_values = math.prod(shape) + shape[-1] if shape else None
            scorer_diag.verified_count = verified
            scorer_diag.correct_count = correct
            scorer_diag.accuracy = (correct / verified) if correct is not None and verified else 0.0
            preset_shape = getattr(getattr(live_scorer, "_preset", None), "shape", None)
            scorer_diag.total_categories = getattr(preset_shape, "n_categories", None)
            if scorer_diag.total_categories is None and shape:
                scorer_diag.total_categories = shape[0]
            if store is not None:
                try:
                    scorer_diag.categories_with_decisions = int(_call(store, "count_categories_with_n", domain, n=1))
                except Exception as exc:
                    scorer_diag.categories_with_decisions = None
                    issues.append(f"scorer_state categories_with_decisions: {type(exc).__name__}: {exc}")
            try:
                scorer_diag.iks_score = float(_call(live_scorer, "_compute_iks", persist_artifacts=False))
            except Exception as exc:
                scorer_diag.iks_score = None
                issues.append(f"scorer_state iks_score: {type(exc).__name__}: {exc}")
            scorer_diag.status = "ok" if scorer_diag.verified_count is not None else "degraded"
        except Exception as exc:
            scorer_diag.error = str(exc)
            issues.append(f"scorer_state: {exc}")

    conservation = ConservationDiag()
    if live_scorer is not None:
        try:
            state = None
            try:
                state = _call(live_scorer, "_evolution_conservation_state")
            except Exception:
                pass
            if state is None:
                state = _call(store, "get_conservation_state", domain) if store is not None else None
            if state is None:
                raise RuntimeError("conservation state unavailable")
            if scorer_diag.verified_count is None:
                raise RuntimeError("verified count unavailable")
            conservation.V = scorer_diag.verified_count
            conservation.q = float(state.get("q"))
            conservation.alpha = float(state.get("alpha", state.get("category_coverage")))
            conservation.alpha_source = "category_coverage"
            conservation.theta_min = float(state.get("theta_min"))
            conservation.effective_q = conservation.alpha * conservation.q * conservation.V
            conservation.gate_passes = conservation.effective_q >= conservation.theta_min
            conservation.conservation_status = str(state.get("status", state.get("conservation_status", "unavailable"))).upper()
            pause = _call(live_scorer, "_conservation_pause")
            conservation.learning_paused = pause is not None
            conservation.pause_reason = pause.get("reason") if isinstance(pause, dict) else None
            conservation.status = "ok"
        except Exception as exc:
            conservation.error = str(exc)
            issues.append(f"conservation: {exc}")

    anchor: bool | None = None
    if store is not None:
        try:
            anchor = bool(_call(store, "has_domain_anchor", domain))
        except Exception:
            try:
                anchor = bool(_cypher_count(store, "Domain", domain))
            except Exception:
                anchor = None
                issues.append("graph_artifacts Domain: domain anchor query unavailable")
    artifacts = ArtifactsDiag(
        decisions=_decision_count(store, domain, issues) if store is not None else None,
        outcomes=(
            _safe_cypher_count(store, "Outcome", domain, issues)
            if store is not None else None
        ),
        conservation_snapshots=(
            _safe_cypher_count(store, "ConservationStatus", domain, issues)
            if store is not None else None
        ),
        centroid_checkpoints=(
            _artifact_count(store, domain, ("get_centroid_checkpoints",), include_v2=True)
            if store is not None else None
        ),
        fingerprints=(
            _safe_cypher_count(store, "Fingerprint", domain, issues)
            if store is not None else None
        ),
        evidence_receipts=(
            _safe_cypher_count(store, "EvidenceReceipt", domain, issues)
            if store is not None else None
        ),
        transfer_patterns_as_source=(
            _safe_cypher_count(store, "TransferPattern", domain, issues, edge_direction="source")
            if store is not None else None
        ),
        transfer_patterns_as_target=(
            _safe_cypher_count(store, "TransferPattern", domain, issues, edge_direction="target")
            if store is not None else None
        ),
        domain_anchor=anchor,
    )
    artifact_issues = [issue for issue in issues if issue.startswith("graph_artifacts ")]
    if artifact_issues:
        artifacts.error = "; ".join(artifact_issues)
    artifacts.status = "complete" if artifacts.decisions is not None and anchor is True else "incomplete"
    if artifacts.status != "complete":
        issues.append("graph_artifacts incomplete")

    outbox = getattr(live_scorer, "_outbox", None) if live_scorer is not None else None
    pending = total = None
    if outbox is not None:
        try:
            pending = int(_call(outbox, "pending_count"))
            total = pending
        except Exception:
            pass
    outbox_ready = pending == 0
    readiness = J6ReadinessDiag(
        store_protocol_v2=infra.protocol_v2,
        domain_anchor_exists=anchor,
        outbox_path=str(getattr(outbox, "db_path")) if outbox is not None and getattr(outbox, "db_path", None) is not None else None,
        outbox_pending=pending,
        outbox_total=total,
        conservation_snapshot_writable=_protocol_store(store) is not None,
        status=(
            "ready"
            if infra.protocol_v2 and outbox_ready
            else "blocked"
        ),
    )
    if readiness.status != "ready":
        issues.append("j6_readiness blocked")
    diagnostic_error = response_extras.get("error")
    if diagnostic_error:
        message = f"diagnostics_error: {diagnostic_error}"
        issues.append(message)
        infra.error = str(diagnostic_error)
        if scorer_diag.error is None:
            scorer_diag.error = str(diagnostic_error)
    return DiagnosticsResponse(
        domain=domain,
        timestamp=time.time(),
        infrastructure=infra,
        scorer_state=scorer_diag,
        conservation=conservation,
        j6_readiness=readiness,
        graph_artifacts=artifacts,
        issues=issues,
        copilot_specific=response_extras,
        layers={"infrastructure": infra, "scorer_state": scorer_diag, "conservation": conservation, "j6_readiness": readiness, "graph_artifacts": artifacts},
    ).model_dump()
