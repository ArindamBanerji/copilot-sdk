"""Purchasing curve contract exercised with real stored outcomes and geometry."""
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from typing import Any

import pytest

from copilot_sdk.graph.memory_store import InMemoryGraphStore
from copilot_sdk.scoring import CompoundingScorer
from copilot_sdk.scoring.presets.purchasing import PurchasingPreset


def control_service(store: InMemoryGraphStore, scorer: Any, data_dir: Path) -> Any:
    source = Path(__file__).resolve().parents[1] / "apps/purchasing/backend/app/services/purchasing_control.py"
    spec = spec_from_file_location("purchasing_twin_curve_contract", source)
    assert spec is not None and spec.loader is not None
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.PurchasingControlService(lambda: store, lambda: scorer, data_dir)


@pytest.mark.parametrize("field", ["learning_curve", "frozen_curve"])
def test_twin_has_curve_with_real_points(tmp_path: Path, field: str) -> None:
    store = InMemoryGraphStore(domain="purchasing")
    scorer = CompoundingScorer.from_preset("purchasing", graph_store=store, profile="test", enable_rl=False)
    try:
        service = control_service(store, scorer, tmp_path)
        assert service.frozen_status()[field] == []
        factors = dict.fromkeys(PurchasingPreset().shape.factor_names, 0.5)
        for _ in range(2):
            result = scorer.score(factors, "produce")
            scorer.learn(result.decision_id, result.action, "confirmed")
        created = service.freeze()
        assert created["available"] is True
        assert len(created[field]) == 2
        assert all(0 <= point["accuracy"] <= 1 for point in created[field])
        assert all(point["decision_id"] for point in created[field])
        before_count = store.count_decisions("purchasing")
        reloaded = control_service(store, scorer, tmp_path).frozen_status()
        assert reloaded["checksum"] == created["checksum"]
        assert reloaded[field] == created[field]
        assert store.count_decisions("purchasing") == before_count
        assert service.twin.get_snapshot().verify_integrity()
    finally:
        store.close()
