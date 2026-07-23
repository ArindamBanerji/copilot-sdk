from __future__ import annotations

import asyncio
import ast
import hashlib
import json
import os
import re
import sys
from pathlib import Path
from typing import Any

import pytest

from copilot_sdk.graph.projection import (
    AGEProjection,
    ProjectionRegistry,
    classify_domain_context,
    normalize_projection_node,
    parse_projection_json,
    project_decision,
    project_factor_vector,
    project_outcome,
)


SOC_FACTOR_SCHEMA_VERSION = "soc_factor_schema_v1"
EXPECTED_SOC_FACTORS = [
    "privileged_identity_context",
    "asset_criticality",
    "threat_intel_enrichment",
    "pattern_history",
    "time_anomaly",
    "device_trust",
]
DATAOPS_ALLOWED_DOMAINS = {"dataops"}
DATAOPS_BLOCKED = "blocked_unpartitioned_context"
DATAOPS_CANONICAL = "canonical_domain_context"


class ReadOnlySOCProjectionClient:
    """Tiny test helper that refuses Cypher/SQL mutation verbs."""

    _MUTATION_RE = re.compile(
        r"\b(CREATE|SET|DELETE|DETACH|MERGE|REMOVE|DROP|ALTER|INSERT|UPDATE|TRUNCATE)\b",
        re.IGNORECASE,
    )

    def __init__(self, dsn: str, graph_name: str) -> None:
        repo_root = Path(__file__).resolve().parents[2]
        ci_platform_path = repo_root.parent / "ci-platform"
        if str(ci_platform_path) not in sys.path:
            sys.path.insert(0, str(ci_platform_path))
        from ci_platform.graph.age_client import AGEClient  # noqa: PLC0415

        self.dsn = dsn
        self.graph_name = graph_name
        self._client = AGEClient(dsn=dsn, graph_name=graph_name)

    def query(self, cypher: str) -> list[dict[str, Any]]:
        if self._MUTATION_RE.search(cypher):
            raise AssertionError("SOC projection tests are read-only; mutation query rejected")
        return asyncio.run(self._client.run_query(cypher, None))


@pytest.fixture()
def soc_projection_client() -> ReadOnlySOCProjectionClient:
    if os.getenv("AGE_INTEGRATION") != "1":
        pytest.skip("AGE_INTEGRATION=1 required for read-only SOC AGE projection tests")
    dsn = os.getenv("AGE_TEST_DSN", "").strip()
    graph_name = "soc_graph"
    if not dsn:
        pytest.skip("AGE_TEST_DSN is required for read-only SOC AGE projection tests")

    client = ReadOnlySOCProjectionClient(dsn=dsn, graph_name=graph_name)
    try:
        client.query("MATCH (n) RETURN count(n) AS cnt")
    except Exception as exc:
        pytest.skip(f"SOC AGE graph unavailable for read-only projection tests: {exc}")
    return client


def _node(row: dict[str, Any], key: str) -> dict[str, Any]:
    return normalize_projection_node(row.get(key))


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _load_soc_factors_from_source() -> list[str]:
    config_path = (
        _repo_root().parent
        / "gen-ai-roi-demo-v4-v50"
        / "backend"
        / "app"
        / "domains"
        / "soc"
        / "config.py"
    )
    assert config_path.exists(), f"SOC config file not found: {config_path}"
    module = ast.parse(config_path.read_text(encoding="utf-8"), filename=str(config_path))
    for node in module.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "SOC_FACTORS":
                    value = ast.literal_eval(node.value)
                    assert isinstance(value, list), "SOC_FACTORS must be a list"
                    assert all(isinstance(item, str) for item in value), "SOC_FACTORS must contain strings"
                    return list(value)
    raise AssertionError(f"SOC_FACTORS not found in {config_path}")


def _factor_names_hash(factor_names: list[str]) -> str:
    payload = json.dumps(list(factor_names), separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def test_soc_factor_schema_source_of_truth_is_stable():
    """SOC factor schema projection uses the accepted ordered SOC_FACTORS list."""
    factor_names = _load_soc_factors_from_source()

    assert factor_names == EXPECTED_SOC_FACTORS
    assert len(factor_names) == 6
    assert factor_names[2] == "threat_intel_enrichment"
    assert "threat_intel" not in factor_names
    assert _factor_names_hash(factor_names) == _factor_names_hash(list(factor_names))


def test_soc_decision_projection_returns_canonical_decision(soc_projection_client):
    """Current SOC Decision rows can be read as canonical Decision projections."""
    rows = soc_projection_client.query("MATCH (d:Decision) RETURN d LIMIT 1")
    assert rows, "soc_graph has no Decision rows to project"

    projected = project_decision(_node(rows[0], "d"), default_domain="soc")

    assert projected["decision_id"]
    assert projected["domain"] == "soc"
    assert projected["category"]
    assert projected["recommended_action"]
    assert projected["created_at"] is not None


def test_soc_outcome_projection_from_embedded_fields(soc_projection_client):
    """Embedded Decision.outcome/correct fields can project to Outcome semantics."""
    rows = soc_projection_client.query(
        """
        MATCH (d:Decision)
        WHERE d.outcome IS NOT NULL OR d.correct IS NOT NULL
        RETURN d
        LIMIT 1
        """
    )
    if not rows:
        pytest.skip("soc_graph has no embedded Decision outcome/correct fields to project")

    decision = _node(rows[0], "d")
    projected = project_outcome(decision)

    assert decision.get("decision_id") or decision.get("id") or decision.get("alert_id")
    assert projected["actual_action"] is not None or projected["is_correct"] is not None
    assert projected["status"] in {"verified", "confirmed", "overridden"}


def test_soc_factor_vector_projection_from_embedded_decision_property(soc_projection_client):
    """Embedded Decision.factor_vector can project with canonical schema metadata."""
    rows = soc_projection_client.query(
        """
        MATCH (d:Decision)
        WHERE d.factor_vector IS NOT NULL
        RETURN d
        LIMIT 1
        """
    )
    if not rows:
        pytest.skip("soc_graph has no Decision.factor_vector values to project")

    decision = _node(rows[0], "d")
    projected = project_factor_vector(
        decision,
        factor_names=_load_soc_factors_from_source(),
        factor_schema_version=SOC_FACTOR_SCHEMA_VERSION,
        factor_names_hash=_factor_names_hash(EXPECTED_SOC_FACTORS),
    )

    assert projected["factor_names"] == EXPECTED_SOC_FACTORS
    assert projected["factor_schema_version"] == SOC_FACTOR_SCHEMA_VERSION
    assert projected["shape"] == [len(EXPECTED_SOC_FACTORS)]
    assert projected["factor_names_hash"] == _factor_names_hash(EXPECTED_SOC_FACTORS)
    assert projected["factor_names_hash"] == _factor_names_hash(list(EXPECTED_SOC_FACTORS))
    assert len(projected["values"]) == len(EXPECTED_SOC_FACTORS)


def test_soc_partial_outcome_backfill_does_not_double_count_V():
    """Mixed embedded Outcome and canonical Outcome counting remains a future backfill gate."""
    pytest.skip("requires canonical SOC Outcome backfill data; keep skipped until backfill design")


def test_soc_dataops_context_requires_explicit_domain_partition(soc_projection_client):
    """DataOps-like SOC graph nodes require explicit domain/source metadata."""
    rows = soc_projection_client.query(
        """
        MATCH (n:DataQualityAlert)
        RETURN n, 'DataQualityAlert' AS label
        LIMIT 5
        """
    ) + soc_projection_client.query(
        """
        MATCH (n:PipelineSystem)
        RETURN n, 'PipelineSystem' AS label
        LIMIT 5
        """
    )
    if not rows:
        pytest.skip("soc_graph has no DataQualityAlert/PipelineSystem rows to partition")

    classifications = [
        classify_domain_context(
            _node(row, "n"),
            str(row.get("label") or "unknown"),
            allowed_domains=DATAOPS_ALLOWED_DOMAINS,
        )
        for row in rows
    ]

    assert classifications
    for classification in classifications:
        assert classification["status"] in {DATAOPS_CANONICAL, DATAOPS_BLOCKED}
        assert classification["is_soc_alert_context"] is False
        if classification["status"] == DATAOPS_CANONICAL:
            assert classification["domain"] in DATAOPS_ALLOWED_DOMAINS
            assert classification["entity_type"]
            assert classification["natural_key"]
        else:
            assert classification["domain"] != "soc"

    label_only = classify_domain_context({}, "DataQualityAlert", allowed_domains=DATAOPS_ALLOWED_DOMAINS)
    assert label_only["status"] == DATAOPS_BLOCKED
    source_only = classify_domain_context(
        {"source": "pipeline-monitor"}, "PipelineSystem", allowed_domains=DATAOPS_ALLOWED_DOMAINS
    )
    assert source_only["status"] == DATAOPS_BLOCKED
    soc_domain = classify_domain_context(
        {
            "domain": "soc",
            "entity_type": "pipeline_system",
            "system_id": "pipe-1",
            "owner_copilot": "soc",
        },
        "PipelineSystem",
        allowed_domains=DATAOPS_ALLOWED_DOMAINS,
    )
    assert soc_domain["status"] == DATAOPS_BLOCKED


def test_soc_canonical_edge_vocabulary_matches_jm_v2_7():
    """SOC compatibility spec keeps canonical JM v2.7 edge vocabulary locked."""
    repo_root = Path(__file__).resolve().parents[2]
    jm = (repo_root / "docs" / "judgment_memory_v2_7.md").read_text(encoding="utf-8")
    spec = (repo_root / "docs" / "soc_age_schema_compatibility_spec_v1.md").read_text(encoding="utf-8")
    normalized_jm = jm.replace("`", "")
    normalized_spec = spec.replace("`", "")

    jm_edges = (
        "(Decision)-[:TRIGGERED_EVOLUTION]->(EvolutionEvent)",
        "(Rule)-[:APPLIES_TO]->(DomainContext)",
        "(TransferPattern)-[:DERIVED_FROM]->(EvolutionEvent)",
        "(Decision)-[:HAS_OUTCOME]->(Outcome)",
        "(Decision)-[:EMITTED_RECEIPT]->(EvidenceReceipt)",
    )
    spec_edges = (
        "Decision -[:TRIGGERED_EVOLUTION]-> EvolutionEvent",
        "Rule -[:APPLIES_TO]-> DomainContext",
        "TransferPattern -[:DERIVED_FROM]-> EvolutionEvent",
        "Decision -[:HAS_OUTCOME]-> Outcome",
        "Decision -[:EMITTED_RECEIPT]-> EvidenceReceipt",
    )

    for edge in jm_edges:
        assert edge in normalized_jm
    for edge in spec_edges:
        assert edge in normalized_spec
    assert "TransferPattern` from `Rule`" in spec
    assert "apply `Rule` directly to `Domain`" in spec


def test_soc_projection_compatibility_before_route_migration(soc_projection_client):
    """Projection sources exist before any SOC production route migration."""
    counts = {
        "decisions": soc_projection_client.query("MATCH (d:Decision) RETURN count(d) AS cnt")[0]["cnt"],
        "alerts": soc_projection_client.query("MATCH (a:Alert) RETURN count(a) AS cnt")[0]["cnt"],
        "profiles": soc_projection_client.query("MATCH (p:ProfileSnapshot) RETURN count(p) AS cnt")[0]["cnt"],
        "shadow": soc_projection_client.query("MATCH (s:ShadowDecision) RETURN count(s) AS cnt")[0]["cnt"],
    }

    assert int(counts["decisions"]) > 0
    assert int(counts["alerts"]) > 0
    assert all(int(value) >= 0 for value in counts.values())


def test_soc_triggered_evolution_forward_write_required():
    """Forward-write TRIGGERED_EVOLUTION repair remains a later SOC implementation gate."""
    pytest.skip("read-only projection cannot prove forward writes; requires SOC write-path slice")


def test_soc_profile_snapshot_projection_to_centroid_checkpoint(soc_projection_client):
    """ProfileSnapshot can be diagnosed as a CentroidCheckpoint projection source."""
    rows = soc_projection_client.query("MATCH (p:ProfileSnapshot) RETURN p LIMIT 1")
    if not rows:
        pytest.skip("soc_graph has no ProfileSnapshot rows to project")

    snapshot = _node(rows[0], "p")
    assert snapshot.get("mu") is not None or snapshot.get("counts") is not None
    assert snapshot.get("decision_count") is not None or snapshot.get("timestamp") is not None


def test_soc_shadow_decision_not_automatically_observation(soc_projection_client):
    """ShadowDecision remains excluded from canonical Observation until explicitly mapped."""
    rows = soc_projection_client.query("MATCH (s:ShadowDecision) RETURN count(s) AS cnt")
    shadow_count = int(rows[0]["cnt"]) if rows else 0
    assert shadow_count >= 0
    pytest.skip("ShadowDecision-to-Observation mapping intentionally deferred; do not auto-promote")


def test_projection_count_matches_conformance_count(soc_projection_client):
    """The read-only SOC projection uses the same active V semantics as AGEGraphStore."""
    repo_root = Path(__file__).resolve().parents[2]
    ci_platform_path = repo_root.parent / "ci-platform"
    if str(ci_platform_path) not in sys.path:
        sys.path.insert(0, str(ci_platform_path))
    from ci_platform.graph import AGEGraphStoreAdapter  # noqa: PLC0415

    projection = AGEProjection(soc_projection_client.dsn, soc_projection_client.graph_name, "soc")
    store = AGEGraphStoreAdapter(dsn=soc_projection_client.dsn, graph_name=soc_projection_client.graph_name)
    try:
        assert projection.count_verified() == store.count_verified("soc")
    finally:
        store.close()


def test_projection_registry_is_closed():
    """Projection patterns are immutable and every pattern is documented."""
    assert set(ProjectionRegistry.PATTERNS) == {
        "decision_verified",
        "decision_with_outcome",
        "factor_vector",
        "count_verified",
        "count_correct",
        "profile_snapshot",
    }
    assert all(pattern.description and pattern.query_template and pattern.returns for pattern in ProjectionRegistry.PATTERNS.values())
    with pytest.raises(TypeError):
        ProjectionRegistry.PATTERNS["new_pattern"] = ProjectionRegistry.PATTERNS["count_verified"]  # type: ignore[index]
