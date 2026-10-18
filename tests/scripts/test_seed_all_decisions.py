"""Direct GraphStore seed-writer coverage."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import threading
from typing import Any, cast

import pytest

from copilot_sdk.graph.memory_store import InMemoryGraphStore
from scripts.seed_all_decisions import (
    DOMAIN_NAMES,
    auto_seed_domain_if_empty,
    seed_all_domains,
    seed_domain,
)


_SEED_COMPLETION_KEY = "demo_preseed:v1"


def _assert_seeded(domain: str) -> None:
    store = InMemoryGraphStore(domain=domain)
    result = seed_domain(domain, store)

    assert result.decisions_seeded == 200
    assert result.outcomes_seeded == 200
    assert store.count_decisions(domain) == 200
    assert store.count_verified_decisions(domain) == 200
    rows = store.get_verified_decisions(domain)
    by_id = {row["decision_id"]: row for row in rows}
    first = by_id[f"seed-{domain}-0001"]
    assert first["metadata"]["seed_domain"] == domain
    assert first["metadata"]["seed_index"] == 1
    assert sum(
        row["actual_action"] != row["recommended_action"] for row in rows
    ) == 50


def test_seed_trading_decisions() -> None:
    _assert_seeded("trading")


def test_seed_purchasing_decisions() -> None:
    _assert_seeded("purchasing")


def test_seed_dataops_decisions() -> None:
    _assert_seeded("dataops")


def test_seed_s2p_decisions() -> None:
    _assert_seeded("s2p")


def test_seed_idempotent() -> None:
    store = InMemoryGraphStore(domain="trading")
    first = seed_domain("trading", store)
    second = seed_domain("trading", store)

    assert (first.decisions_seeded, first.outcomes_seeded) == (200, 200)
    assert (second.decisions_seeded, second.outcomes_seeded) == (0, 0)
    assert second.decisions_skipped == 200
    assert store.count_decisions("trading") == 200
    assert store.count_verified_decisions("trading") == 200


def test_seed_dry_run() -> None:
    store = InMemoryGraphStore(domain="dataops")
    result = seed_domain("dataops", store, dry_run=True)

    assert result.dry_run is True
    assert result.requested == 200
    assert store.count_decisions("dataops") == 0


def test_seed_all_domains() -> None:
    stores = {domain: InMemoryGraphStore(domain=domain) for domain in DOMAIN_NAMES}
    results = seed_all_domains(stores.__getitem__)

    assert [result.domain for result in results] == list(DOMAIN_NAMES)
    assert all(result.decisions_seeded == 200 for result in results)
    assert all(
        stores[domain].count_verified_decisions(domain) == 200
        for domain in DOMAIN_NAMES
    )


@pytest.mark.parametrize("domain", ("trading", "purchasing", "dataops"))
def test_age_startup_seed_fires_once_for_empty_domain(domain: str) -> None:
    store = InMemoryGraphStore(domain=domain)

    assert auto_seed_domain_if_empty(domain, store) == 200
    first_count = store.count_decisions(domain)
    assert first_count == 200

    assert auto_seed_domain_if_empty(domain, store) == 0
    assert store.count_decisions(domain) == first_count


def test_age_startup_seed_respects_demo_no_reseed(monkeypatch: pytest.MonkeyPatch) -> None:
    class NoSeedReadStore(InMemoryGraphStore):
        def get_governance(self, domain: str, key: str) -> dict[str, Any] | None:
            raise AssertionError("DEMO_NO_RESEED must suppress marker reads")

        def count_decisions(self, domain: str) -> int:
            raise AssertionError("DEMO_NO_RESEED must suppress decision reads")

    store = NoSeedReadStore(domain="trading")
    monkeypatch.setenv("DEMO_NO_RESEED", "1")

    assert auto_seed_domain_if_empty("trading", store) == 0
    assert InMemoryGraphStore.count_decisions(store, "trading") == 0


def test_age_startup_seed_resumes_partial_seed_and_marks_completion() -> None:
    domain = "trading"
    store = InMemoryGraphStore(domain=domain)
    partial = seed_domain(domain, store, count=50)

    assert partial.decisions_seeded == 50
    assert store.get_governance(domain, _SEED_COMPLETION_KEY) is None

    assert auto_seed_domain_if_empty(domain, store) == 150
    assert store.count_decisions(domain) == 200
    assert store.count_verified_decisions(domain) == 200
    marker = store.get_governance(domain, _SEED_COMPLETION_KEY)
    assert marker is not None
    assert marker["status"] == "complete"
    assert marker["decision_count"] == 200

    assert auto_seed_domain_if_empty(domain, store) == 0
    assert store.count_decisions(domain) == 200


def test_age_startup_seed_concurrent_initializers_write_once() -> None:
    domain = "purchasing"

    class MarkerCountingStore(InMemoryGraphStore):
        def __init__(self) -> None:
            super().__init__(domain=domain)
            self.marker_writes = 0

        def save_governance(
            self,
            marker_domain: str,
            key: str,
            state: dict[str, Any],
        ) -> None:
            if key == _SEED_COMPLETION_KEY:
                self.marker_writes += 1
            super().save_governance(marker_domain, key, state)

    store = MarkerCountingStore()
    start = threading.Barrier(2)

    def initialize() -> int:
        start.wait(timeout=5)
        return int(auto_seed_domain_if_empty(domain, store))

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(lambda _index: initialize(), range(2)))

    assert sorted(results) == [0, 200]
    assert store.count_decisions(domain) == 200
    assert store.count_verified_decisions(domain) == 200
    assert store.marker_writes == 1
    assert store.get_governance(domain, _SEED_COMPLETION_KEY) is not None


def test_seed_domain_uses_atomic_governed_write_when_available() -> None:
    domain = "trading"

    class GovernedWriteStore(InMemoryGraphStore):
        def __init__(self) -> None:
            super().__init__(domain=domain)
            self.basic_writes = 0
            self.governed_writes = 0

        def write_decision(
            self,
            decision_domain: str,
            category: str,
            action: str,
            confidence: float,
            factors: dict[str, Any],
            metadata: dict[str, Any] | None = None,
        ) -> str:
            self.basic_writes += 1
            return cast(
                str,
                super().write_decision(
                    decision_domain, category, action, confidence, factors, metadata
                ),
            )

        def write_governed_decision(self, *args: Any, **kwargs: Any) -> None:
            self.governed_writes += 1
            super().write_governed_decision(*args, **kwargs)

    store = GovernedWriteStore()

    result = seed_domain(domain, store, count=5)

    assert result.decisions_seeded == 5
    assert store.governed_writes == 5
    assert store.basic_writes == 0


def test_age_startup_seed_does_not_resume_non_seed_data() -> None:
    domain = "dataops"
    store = InMemoryGraphStore(domain=domain)
    seed_domain(domain, store, count=50)
    store.write_decision(
        domain,
        "pipeline_health",
        "monitor",
        0.8,
        {"data_quality": 0.8},
        metadata={"decision_id": "real-user-decision"},
    )

    assert auto_seed_domain_if_empty(domain, store) == 0
    assert store.count_decisions(domain) == 51
    assert store.get_governance(domain, _SEED_COMPLETION_KEY) is None
