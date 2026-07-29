"""Five-domain contract coverage for the portable graph stores."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Iterator

import pytest

from copilot_sdk.config.domains import ALL_COPILOT_DOMAINS
from copilot_sdk.graph.memory_store import InMemoryGraphStore
from copilot_sdk.graph.protocol import ProtocolV2GraphStore
from copilot_sdk.graph.sqlite_store import SQLiteGraphStore


CONSERVATION_VALUES: dict[str, tuple[int, float, float]] = {
    "soc": (4862, 0.91, 0.83),
    "s2p": (800, 0.88, 0.75),
    "trading": (150, 0.92, 0.80),
    "purchasing": (120, 0.85, 0.70),
    "dataops": (200, 0.90, 0.78),
}


@pytest.fixture(params=("memory", "sqlite"))
def store(request: pytest.FixtureRequest, tmp_path: Path) -> Iterator[ProtocolV2GraphStore]:
    backend = str(request.param)
    if backend == "memory":
        graph_store: ProtocolV2GraphStore = InMemoryGraphStore(domain="test")
    else:
        graph_store = SQLiteGraphStore(str(tmp_path / "five_domains.db"), "test", "TEST-")
    try:
        yield graph_store
    finally:
        graph_store.close()


def _write_conservation(store: ProtocolV2GraphStore, domain: str, *, suffix: str = "first") -> None:
    V, q, alpha = CONSERVATION_VALUES[domain]
    store.write_conservation_status(
        status_id=f"{domain}-{suffix}",
        domain=domain,
        V=V,
        q=q,
        alpha=alpha,
        theta_min=0.60,
        verified_count=V,
        correct_count=int(V * q),
        status="GREEN",
        policy_version="five-domain-test",
    )


def _write_all_conservation(store: ProtocolV2GraphStore) -> None:
    for domain in ALL_COPILOT_DOMAINS:
        _write_conservation(store, domain)


def _write_trajectory(store: ProtocolV2GraphStore, domain: str) -> None:
    for index, iks in enumerate((0.3, 0.5, 0.7), start=1):
        store.save_centroids(
            domain=domain,
            category="default",
            centroids=[[iks]],
            metadata={"iks": iks},
            decision_id=f"{domain}-decision-{index}",
        )
        time.sleep(0.001)


def _write_transfer(
    store: ProtocolV2GraphStore,
    pattern_id: str,
    source_domain: str,
    target_domain: str,
    confidence: float,
) -> None:
    store.write_transfer_pattern(
        pattern_id=pattern_id,
        source_domain=source_domain,
        target_domain=target_domain,
        pattern_type="factor_quality_transfer",
        factor_mapping={"quality": "quality"},
        confidence=confidence,
        validation_status="validated",
        conservation_status="GREEN",
    )


def _write_cross_domain_patterns(store: ProtocolV2GraphStore) -> None:
    for pattern_id, source, target, confidence in (
        ("soc-trading", "soc", "trading", 0.85),
        ("soc-s2p", "soc", "s2p", 0.78),
        ("trading-dataops", "trading", "dataops", 0.72),
        ("purchasing-dataops", "purchasing", "dataops", 0.68),
        ("s2p-purchasing", "s2p", "purchasing", 0.81),
    ):
        _write_transfer(store, pattern_id, source, target, confidence)


def test_global_conservation_all_five_domains(store: ProtocolV2GraphStore) -> None:
    _write_all_conservation(store)

    latest = store.get_latest_conservation_statuses(domains=None)
    assert len(latest) == len(ALL_COPILOT_DOMAINS)
    assert [row["domain"] for row in latest] == sorted(ALL_COPILOT_DOMAINS)
    for row in latest:
        V, q, alpha = CONSERVATION_VALUES[str(row["domain"])]
        assert (row["V"], row["q"], row["alpha"]) == (V, q, alpha)

    store.write_conservation_status(
        status_id="soc-zz-later",
        domain="soc",
        V=4870,
        q=0.91,
        alpha=0.83,
        theta_min=0.60,
        verified_count=4870,
        correct_count=4431,
        status="GREEN",
        policy_version="five-domain-test",
    )
    refreshed = store.get_latest_conservation_statuses(domains=None)
    assert next(row for row in refreshed if row["domain"] == "soc")["V"] == 4870
    assert {
        str(row["domain"]): int(row["V"])
        for row in refreshed
        if row["domain"] != "soc"
    } == {domain: values[0] for domain, values in CONSERVATION_VALUES.items() if domain != "soc"}


def test_global_conservation_domain_filter(store: ProtocolV2GraphStore) -> None:
    _write_all_conservation(store)
    assert {row["domain"] for row in store.get_latest_conservation_statuses(["soc", "trading"])} == {
        "soc",
        "trading",
    }
    assert [row["domain"] for row in store.get_latest_conservation_statuses(["purchasing"])] == [
        "purchasing"
    ]
    assert store.get_latest_conservation_statuses(["nonexistent"]) == []


def test_global_conservation_empty_domain(store: ProtocolV2GraphStore) -> None:
    _write_conservation(store, "soc")
    _write_conservation(store, "trading")
    assert {row["domain"] for row in store.get_latest_conservation_statuses()} == {"soc", "trading"}
    for domain in set(ALL_COPILOT_DOMAINS) - {"soc", "trading"}:
        assert store.get_latest_conservation_statuses([domain]) == []


def test_iks_trajectory_all_five_domains(store: ProtocolV2GraphStore) -> None:
    for domain in ALL_COPILOT_DOMAINS:
        _write_trajectory(store, domain)

    trajectory = store.get_iks_trajectory(domains=None)
    assert len(trajectory) == 15
    assert [(row["domain"], row["iks"]) for row in trajectory] == [
        (domain, iks) for domain in sorted(ALL_COPILOT_DOMAINS) for iks in (0.3, 0.5, 0.7)
    ]


def test_iks_trajectory_domain_filter(store: ProtocolV2GraphStore) -> None:
    for domain in ALL_COPILOT_DOMAINS:
        _write_trajectory(store, domain)
    trajectory = store.get_iks_trajectory(domains=["purchasing", "dataops"])
    assert {row["domain"] for row in trajectory} == {"purchasing", "dataops"}
    assert len(trajectory) == 6


def test_transfer_patterns_cross_domain_completeness(store: ProtocolV2GraphStore) -> None:
    _write_cross_domain_patterns(store)
    assert len(store.get_transfer_patterns()) == 5
    assert len(store.get_transfer_patterns(source_domain="soc")) == 2
    assert len(store.get_transfer_patterns(target_domain="dataops")) == 2
    assert len(store.get_transfer_patterns(source_domain="purchasing")) == 1
    assert len(store.get_transfer_patterns(source_domain=None, target_domain=None)) == 5


def test_transfer_pattern_every_domain_as_source(store: ProtocolV2GraphStore) -> None:
    for index, source in enumerate(ALL_COPILOT_DOMAINS):
        target = ALL_COPILOT_DOMAINS[(index + 1) % len(ALL_COPILOT_DOMAINS)]
        _write_transfer(store, f"source-{source}", source, target, 0.70)
    assert {row["source_domain"] for row in store.get_transfer_patterns()} == set(ALL_COPILOT_DOMAINS)


def test_transfer_pattern_every_domain_as_target(store: ProtocolV2GraphStore) -> None:
    for index, target in enumerate(ALL_COPILOT_DOMAINS):
        source = ALL_COPILOT_DOMAINS[(index + 1) % len(ALL_COPILOT_DOMAINS)]
        _write_transfer(store, f"target-{target}", source, target, 0.70)
    assert {row["target_domain"] for row in store.get_transfer_patterns()} == set(ALL_COPILOT_DOMAINS)


def test_domain_anchors_created_for_all_five(store: ProtocolV2GraphStore) -> None:
    _write_all_conservation(store)
    for index, source in enumerate(ALL_COPILOT_DOMAINS):
        target = ALL_COPILOT_DOMAINS[(index + 1) % len(ALL_COPILOT_DOMAINS)]
        _write_transfer(store, f"anchor-{source}", source, target, 0.70)

    assert {row["domain"] for row in store.get_latest_conservation_statuses()} == set(ALL_COPILOT_DOMAINS)
    assert {row["source_domain"] for row in store.get_transfer_patterns()} == set(ALL_COPILOT_DOMAINS)


def test_v2_checkpoints_all_five_domains(store: ProtocolV2GraphStore) -> None:
    for domain in ALL_COPILOT_DOMAINS:
        store.save_centroids(
            domain=domain,
            category="default",
            centroids=[[0.3]],
            metadata={"iks": 0.3},
            decision_id=f"{domain}-legacy",
        )
        store.write_centroid_checkpoint(
            checkpoint_id=f"{domain}-v2",
            domain=domain,
            category="default",
            action="approve",
            centroids=[[0.7]],
            decisions_count=3,
            verified_count=2,
            iks=0.7,
            shape=[1, 1],
            factor_names_hash="five-domain",
            metadata={"decision_id": f"{domain}-v2"},
        )
        assert len(store.get_centroid_checkpoints(domain, include_v2=True, limit=None)) == 2
        assert len(store.get_centroid_checkpoints(domain, include_v2=False, limit=None)) == 1


def test_mixed_domain_isolation(store: ProtocolV2GraphStore) -> None:
    _write_all_conservation(store)
    for domain in ALL_COPILOT_DOMAINS:
        _write_trajectory(store, domain)
    _write_cross_domain_patterns(store)

    for domain in ALL_COPILOT_DOMAINS:
        conservation = store.get_latest_conservation_statuses([domain])
        trajectory = store.get_iks_trajectory([domain])
        transfers = store.get_transfer_patterns(source_domain=domain)
        assert len(conservation) == 1
        assert conservation[0]["domain"] == domain
        assert all(row["domain"] == domain for row in trajectory)
        assert all(row["source_domain"] == domain for row in transfers)
