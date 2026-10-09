"""Promotion payload compatibility across SDK and application adapters."""
from __future__ import annotations

from pathlib import Path
import subprocess
import sys

import pytest

from copilot_sdk.graph import InMemoryGraphStore
from copilot_sdk.promotion import PromotionRecord, PromotionStage, PromotionStore


@pytest.mark.parametrize("wrapped", [False, True], ids=["flat", "legacy-envelope"])
def test_sdk_reads_both_promotion_record_formats(wrapped: bool) -> None:
    graph = InMemoryGraphStore()
    record = PromotionRecord(
        "existing", "s2p", "supplier_risk", PromotionStage.SHADOWING,
        stage_history=[{"stage": "shadowing", "reason": "observed"}],
        shadow_decisions=12, measurement_decisions=4, improvement_delta=0.25,
        conservation_state_at_transition="GREEN",
    )
    payload = record.to_dict()
    graph.save_promotion("s2p", record.record_id, {"record": payload} if wrapped else payload)
    reader = PromotionStore(graph, "s2p")
    assert reader.load(record.record_id) == record
    assert reader.list_all("s2p") == [record]
    assert reader.load_by_class("s2p", "supplier_risk") == record


def test_promotion_listing_keeps_mixed_formats_separate_from_other_state() -> None:
    graph = InMemoryGraphStore()
    legacy = PromotionRecord("a", "trading", "trend")
    flat = PromotionRecord("b", "trading", "mean_reversion")
    graph.save_promotion("trading", "a", {"record": legacy.to_dict()})
    graph.save_promotion("trading", "b", flat.to_dict())
    graph.save_promotion("trading", "frozen_twin:trading", {"snapshot": {"weights": []}})
    graph.save_promotion("trading", "rule", {"promoted": False, "reason": "conservation"})
    reader = PromotionStore(graph, "trading")
    assert reader.list_all("trading") == [legacy, flat]
    assert reader.load("frozen_twin:trading") is None
    assert reader.load("rule") is None


def test_transfer_is_readable_through_the_actual_s2p_application_adapter() -> None:
    root = Path(__file__).resolve().parents[1]
    backend = root.parent / "s2p-copilot" / "backend"
    # A separate interpreter prevents the sibling application's "app" package
    # from replacing another copilot's imports in the SDK test process.
    script = """
import sys
sys.path.insert(0, sys.argv[1])
from app.services.s2p_autonomy import GraphPromotionStore
from copilot_sdk.graph import InMemoryGraphStore
from copilot_sdk.promotion import (
    PromotionEngine, PromotionStore, PromotionStage, PurchasingPromotionPolicy,
)

graph = InMemoryGraphStore()
source = PromotionStore(graph, "purchasing")
engine = PromotionEngine(PurchasingPromotionPolicy(), source)
original = engine.create("purchasing", "supplier_risk")
for evidence in (
    {}, {"conservation_state": "GREEN", "shadow_decisions": 10},
    {}, {"measurement_decisions": 10, "improvement": 0.1},
):
    assert engine.advance(original.record_id, evidence).advanced
result = engine.transfer(original.record_id, "s2p", evidence={"conservation_state": "GREEN"})
assert result.advanced and result.target_record_id is not None
destination = GraphPromotionStore(graph, "s2p")
record = destination.load(result.target_record_id)
assert record is not None
assert record.record_id == result.target_record_id
assert record.record_id != original.record_id
assert record.copilot == "s2p"
assert record.decision_class == original.decision_class
assert record.current_stage is PromotionStage.DISCOVERED
assert record.shadow_decisions == record.measurement_decisions == 0
assert record.stage_history[0]["stage"] == "discovered"
assert destination.list_all("s2p") == [record]
assert destination.load_by_class("s2p", original.decision_class) == record
assert PromotionStore(graph, "s2p").load(record.record_id) == record
assert source.load(record.record_id) is None
assert source.load(original.record_id).current_stage is PromotionStage.TRANSFERRED
# Application writes must remain readable by the SDK as well.
destination.save(record)
assert PromotionStore(graph, "s2p").load(record.record_id) == record
print("S2P_TRANSFER_READABLE")
"""
    completed = subprocess.run(
        [sys.executable, "-B", "-c", script, str(backend)],
        cwd=root, capture_output=True, text=True, timeout=60,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert "S2P_TRANSFER_READABLE" in completed.stdout

