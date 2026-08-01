"""Permanent JM v2.7 cross-copilot validation contracts."""

from __future__ import annotations

import os
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

import pytest

from copilot_sdk.config import GraphConfig, GraphConfigError, require_shared_graph
from copilot_sdk.graph.factory import create_graph_store
from copilot_sdk.graph.memory_store import InMemoryGraphStore
from copilot_sdk.graph.sqlite_store import SQLiteGraphStore
from scripts.jm_v27_live_validation import (
    STARTUP_ENDPOINTS,
    _audit_counts_pass,
    _correctness_rows_pass,
)


DOMAINS = ("soc", "trading", "purchasing", "dataops", "s2p")


@contextmanager
def _shared_graph_environment() -> Iterator[None]:
    keys = (
        "GRAPH_BACKEND",
        "GRAPH_DSN",
        "GRAPH_NAME",
        "AGE_GRAPH_NAME",
        "GRAPH_DOMAIN",
    )
    previous = {key: os.environ.get(key) for key in keys}
    try:
        os.environ["GRAPH_BACKEND"] = "age"
        os.environ["GRAPH_DSN"] = "host=validation"
        os.environ["GRAPH_NAME"] = "soc_graph"
        os.environ.pop("AGE_GRAPH_NAME", None)
        os.environ.pop("GRAPH_DOMAIN", None)
        yield
    finally:
        for key, value in previous.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


def _write_decision(store: Any, domain: str, decision_id: str) -> str:
    return str(
        store.write_decision(
            domain,
            "shared",
            "review",
            0.8,
            {"signal": 0.8},
            metadata={"decision_id": decision_id},
        )
    )


def test_all_five_graphconfigs_resolve_soc_graph() -> None:
    with _shared_graph_environment():
        configs = [GraphConfig.load(domain, profile="production") for domain in DOMAINS]

    assert {config.graph for config in configs} == {"soc_graph"}
    assert len({config.dsn for config in configs}) == 1


def test_domain_isolation_no_cross_contamination() -> None:
    stores = {domain: InMemoryGraphStore(domain=domain) for domain in DOMAINS}
    try:
        ids = {
            domain: _write_decision(stores[domain], domain, f"{domain}-decision")
            for domain in DOMAINS
        }
        for domain, store in stores.items():
            decisions = store.get_decisions(domain=domain)
            assert {row["decision_id"] for row in decisions} == {ids[domain]}
    finally:
        for store in stores.values():
            store.close()


def test_correctness_scanner_clean() -> None:
    from integrity import correctness_scanner

    root = Path(__file__).resolve().parents[2]
    assert correctness_scanner.main(["--check", "--root", str(root)]) == 0


@pytest.mark.parametrize("store_kind", ["memory", "sqlite"])
def test_count_correct_property_based_all_stores(
    store_kind: str, tmp_path: Path
) -> None:
    store: Any = (
        InMemoryGraphStore(domain="validation")
        if store_kind == "memory"
        else SQLiteGraphStore(tmp_path / "count.sqlite", domain="validation")
    )
    try:
        decision_id = _write_decision(store, "validation", f"count-{store_kind}")
        store.write_outcome(decision_id, "review", True, domain="validation")
        assert store.count_correct("validation") == 1
    finally:
        store.close()


@pytest.mark.parametrize("store_kind", ["memory", "sqlite"])
def test_write_outcome_sets_d_correct_all_stores(
    store_kind: str, tmp_path: Path
) -> None:
    store: Any = (
        InMemoryGraphStore(domain="validation")
        if store_kind == "memory"
        else SQLiteGraphStore(tmp_path / "outcome.sqlite", domain="validation")
    )
    try:
        decision_id = _write_decision(store, "validation", f"outcome-{store_kind}")
        store.write_outcome(decision_id, "review", True, domain="validation")
        decision = store.get_decision(decision_id, domain="validation")
        assert decision is not None
        assert decision["correct"] is True
        assert decision["status"] in {"confirmed", "overridden"}
    finally:
        store.close()


def test_soc_graph_invariant_rejects_production_non_soc() -> None:
    with pytest.raises(GraphConfigError, match="soc_graph"):
        require_shared_graph(
            backend="age",
            graph="other_graph",
            domain="trading",
            profile="production",
        )


@pytest.mark.parametrize("store_kind", ["memory", "sqlite"])
def test_link_decision_domain_required_all_stores(
    store_kind: str, tmp_path: Path
) -> None:
    store: Any = (
        InMemoryGraphStore(domain="validation")
        if store_kind == "memory"
        else SQLiteGraphStore(tmp_path / "link.sqlite", domain="validation")
    )
    try:
        decision_id = _write_decision(store, "validation", f"link-{store_kind}")
        with pytest.raises(TypeError):
            store.link_decision_to_entity(decision_id, "entity")
    finally:
        store.close()


def test_no_silent_sqlite_substitution() -> None:
    try:
        store = create_graph_store(
            backend="age",
            domain="validation",
            dsn="host=127.0.0.1 port=1 dbname=unreachable",
            graph_name="unreachable_graph",
        )
    except (ConnectionError, OSError, RuntimeError, ValueError, GraphConfigError):
        return
    try:
        assert not isinstance(store, SQLiteGraphStore)
    finally:
        store.close()


def test_d_correct_coverage_aligned_with_outcomes() -> None:
    """Unverified SDK decisions may remain NULL; outcome decisions may not."""
    rows = [
        {"domain": "s2p", "total": 5, "with_outcome": 3, "with_correct": 3},
        {"domain": "trading", "total": 0, "with_outcome": 0, "with_correct": 0},
        {"domain": "purchasing", "total": 0, "with_outcome": 0, "with_correct": 0},
        {"domain": "dataops", "total": 0, "with_outcome": 0, "with_correct": 0},
        {"domain": "soc", "total": 5, "with_outcome": 0, "with_correct": 5},
    ]
    assert _correctness_rows_pass(rows)


def test_soc_audit_is_hash_chain_not_outcome_nodes() -> None:
    """SOC's audit contract is the Decision hash chain, not Outcome edges."""
    counts = {
        "s2p": {"outcomes": 1, "receipts": 1, "checkpoints": 1, "conservation": 1},
        "trading": {"outcomes": 1, "receipts": 1, "checkpoints": 1, "conservation": 1},
        "purchasing": {"outcomes": 1, "receipts": 1, "checkpoints": 1, "conservation": 1},
        "dataops": {"outcomes": 1, "receipts": 1, "checkpoints": 1, "conservation": 1},
        "soc": {"hash_chain": 1},
        "transfers": 6,
    }
    assert _audit_counts_pass(counts)
    assert STARTUP_ENDPOINTS["s2p"]["health"] == "/health"
    assert STARTUP_ENDPOINTS["soc"]["fingerprint"] is None
