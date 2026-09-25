"""Frozen twin uses real immutable geometry and verified cohort replay."""
from importlib import import_module
from pathlib import Path

from copilot_sdk.graph.memory_store import InMemoryGraphStore
from copilot_sdk.scoring import CompoundingScorer
from copilot_sdk.scoring.presets.purchasing import PurchasingPreset
from copilot_sdk.backend.scorer_proxy import FreshScorerProxy
from copilot_sdk.scoring.gate_enforced_scorer import GateEnforcedScorer
from copilot_sdk.scoring.composite_gate import CompositeGate


def test_twin_replays_real_cohort_without_mutation(tmp_path: Path) -> None:
    service_type = import_module("app.services.purchasing_control").PurchasingControlService
    store = InMemoryGraphStore(domain="purchasing")
    scorer = CompoundingScorer.from_preset("purchasing", graph_store=store, profile="test", enable_rl=False)
    proxy = GateEnforcedScorer(FreshScorerProxy("purchasing", ":memory:", lambda _: store, profile="test"), CompositeGate())
    service = service_type(lambda: store, lambda: proxy, tmp_path)
    try:
        assert service.frozen_status()["learning_curve"] == []
        frozen = service.freeze()
        checksum = frozen["checksum"]
        factors = dict.fromkeys(PurchasingPreset().shape.factor_names, 0.5)
        for index in range(5):
            result = scorer.score(factors, "produce")
            scorer.learn(result.decision_id, result.action, "confirmed")
        before = store.count_decisions("purchasing")
        body = service.frozen_status()
        assert len(body["learning_curve"]) == len(body["frozen_curve"]) == 5
        assert body["curve_kind"] == "retrospective_paired_replay"
        assert body["checksum"] == checksum == service.freeze()["checksum"]
        assert store.count_decisions("purchasing") == before
        assert service.twin.get_snapshot().verify_integrity()
    finally:
        store.close()
