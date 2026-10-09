from __future__ import annotations

import logging
from types import SimpleNamespace
from typing import Any, cast

from copilot_sdk.demo.bundle import _restore
from copilot_sdk.evolution import EvolutionEvent, InMemoryEvolutionLedger
from copilot_sdk.reporting.weekly import WeeklyReportGenerator
from copilot_sdk.scoring.measurement_state import MeasurementState, compute_measurement_state
from copilot_sdk.scoring.scorer import CompoundingScorer


def test_fingerprint_reports_persistence_failure() -> None:
    scorer = object.__new__(CompoundingScorer)
    scorer_any = cast(Any, scorer)
    scorer_any._preset = SimpleNamespace(shape=SimpleNamespace(factor_names=[]))
    scorer_any._verified_decisions = lambda: []
    scorer_any._persist_fingerprint = lambda result, decision_id=None: False

    result = scorer.fingerprint(persist=True)

    assert result.persistence_failed is True


def test_evolution_failure_is_observable() -> None:
    scorer = object.__new__(CompoundingScorer)
    scorer._evolver = object()
    scorer._graph_store = SimpleNamespace(
        get_verified_decisions=lambda _domain: (_ for _ in ()).throw(ConnectionError("offline"))
    )
    scorer._domain = "trading"

    assert scorer._run_evolution() is False


def test_ledger_append_reports_persistence_failure(caplog) -> None:
    store = SimpleNamespace(write_evolution_event=lambda **kwargs: (_ for _ in ()).throw(RuntimeError("offline")))
    ledger = InMemoryEvolutionLedger(evolution_store=store, domain="trading")

    with caplog.at_level(logging.WARNING):
        persisted = ledger.append(EvolutionEvent("shadow_started", "rule", "variant"))

    assert persisted is False
    assert ledger.event_count == 1
    assert "Failed to persist evolution event" in caplog.text


def test_bundle_restore_reports_skipped_records(caplog) -> None:
    from copilot_sdk.graph.memory_store import InMemoryGraphStore
    from typing import Any

    class FailingStore(InMemoryGraphStore):
        def count_decisions(self, domain: str) -> int:
            return 0

        def write_governed_decision(self, **kwargs: Any) -> None:
            if kwargs["decision_id"] == "bad":
                raise RuntimeError("write failed")
            super().write_governed_decision(**kwargs)

    bundle = {
        "domain": "trading",
        "factor_names": [],
        "decisions": [
            {"decision_id": "good", "category": "alpha"},
            {"decision_id": "bad", "category": "alpha"},
        ],
    }
    with caplog.at_level(logging.WARNING):
        result = _restore(FailingStore(), bundle, "trading")

    assert result.restored_count == 1
    assert result.skipped_count == 1
    assert result.failed_stores == ["decisions"]
    assert not result.fully_restored
    assert "decision_id=bad" in caplog.text


def test_weekly_iks_failure_is_unavailable() -> None:
    class Scorer:
        def trajectory(self) -> object:
            raise ConnectionError("history offline")

    generator = WeeklyReportGenerator(SimpleNamespace(), Scorer(), "purchasing")

    assert generator._compute_iks(0.0, 1.0) == (None, None)


def test_measurement_iks_failure_is_degraded() -> None:
    class Shape:
        category_names = ("alpha",)
        action_names = ("act",)

    class Store:
        domain = "trading"

        def get_verified_decisions(self, _domain: str) -> list[dict[str, object]]:
            return [{"category": "alpha", "actual_action": "act", "is_correct": True}]

    class Scorer:
        _preset = SimpleNamespace(shape=Shape(), measurement_k_min=1)
        graph_store = Store()

        def trajectory(self) -> object:
            raise ConnectionError("history offline")

    status = compute_measurement_state(Scorer())

    assert status.state is MeasurementState.DEGRADED
    assert status.iks_available is False
    assert status.degraded is True
