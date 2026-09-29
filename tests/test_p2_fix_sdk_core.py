from __future__ import annotations

import json
from pathlib import Path
from types import ModuleType
from unittest.mock import MagicMock

import numpy as np
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from copilot_sdk.backend.platform_router import create_platform_router
from copilot_sdk.demo.bundle import restore_bundle_if_empty
from copilot_sdk.evolution.evolver import AgentEvolver
from copilot_sdk.evolution.prompt_evolver import PromptVariantEvolver
from copilot_sdk.scoring.presets import dataops, purchasing, trading
from copilot_sdk.scoring.verification import price


@pytest.mark.parametrize("failure", [ConnectionError("down"), None])
def test_platform_metrics_mark_failed_or_malformed_reads_unavailable(failure: Exception | None) -> None:
    scorer = MagicMock()
    if failure is None:
        scorer.get_verified_count.return_value = None
        scorer.trajectory.return_value = None
    else:
        scorer.get_verified_count.side_effect = failure
        scorer.trajectory.side_effect = failure
    app = FastAPI()
    app.include_router(create_platform_router(scorer, current_domain="trading"), prefix="/api")

    payload = TestClient(app).get("/api/platform/domain-applicability").json()

    assert payload["platform_summary"]["total_decisions"] == 0
    assert payload["platform_summary"]["mean_compounding_gain_pp"] == 0.0
    assert payload["data_available"] is False


@pytest.mark.parametrize("fallback", [(168.0, False), (0.0, False)])
def test_live_price_fallback_is_not_labelled_live(monkeypatch: pytest.MonkeyPatch, fallback: tuple[float, bool]) -> None:
    monkeypatch.setattr(price, "_fetch_live_price", lambda _ticker: fallback)
    result = price.verify_trade("NVDA", 100.0, "buy", use_live=True)
    assert result.source in {"cached_seed", "unknown_ticker"}
    assert result.price_source_available is False


@pytest.mark.parametrize(
    ("module", "preset_type"),
    [(trading, trading.TradingPreset), (purchasing, purchasing.PurchasingPreset), (dataops, dataops.DataOpsPreset)],
)
@pytest.mark.parametrize("mode", ["exception", "malformed"])
def test_bootstrap_failures_mark_preset_degraded(
    monkeypatch: pytest.MonkeyPatch,
    module: ModuleType,
    preset_type: type,
    mode: str,
) -> None:
    if mode == "exception":
        monkeypatch.setattr(module.Path, "read_text", lambda *_args, **_kwargs: (_ for _ in ()).throw(OSError("down")))
    else:
        monkeypatch.setattr(module.Path, "read_text", lambda *_args, **_kwargs: json.dumps({"centroids": [0.5]}))
    preset = preset_type()
    centroids = preset.bootstrap_centroids
    assert isinstance(centroids, np.ndarray)
    assert preset.bootstrap_degraded is True


@pytest.mark.parametrize("evolver_kind", ["agent", "prompt"])
def test_evolution_ledger_failure_is_exposed(evolver_kind: str) -> None:
    ledger = MagicMock()
    ledger.append.return_value = False
    if evolver_kind == "agent":
        agent_evolver = AgentEvolver(ledger=ledger)
        agent_evolver._record("promoted", "rule", "variant")
        warnings = agent_evolver.warnings
    else:
        prompt_evolver = PromptVariantEvolver(ledger=ledger, profile="test")
        prompt_evolver._emit_lifecycle_event("promoted", "variant")
        warnings = prompt_evolver.warnings
    assert warnings == ["evolution_ledger_write_failed"]


@pytest.mark.parametrize("payload", ["not-json", json.dumps([])])
def test_restore_report_exposes_bundle_read_failure(tmp_path: Path, payload: str) -> None:
    path = tmp_path / "bundle.json"
    path.write_text(payload, encoding="utf-8")
    report = restore_bundle_if_empty(MagicMock(), path, domain="trading")
    assert report.success is False
    assert report.fully_restored is False
    assert report.stores_failed == 1
    assert report.failed_stores == ["bundle"]


def test_restore_report_exposes_partial_age_write(tmp_path: Path) -> None:
    path = tmp_path / "bundle.json"
    path.write_text(json.dumps({
        "domain": "trading",
        "decisions": [
            {"decision_id": "ok", "category": "c", "recommended_action": "a"},
            {"decision_id": "bad", "category": "c", "recommended_action": "a"},
        ],
    }), encoding="utf-8")
    store = MagicMock()
    store.graph_config.backend = "age"
    store.count_decisions.return_value = 0
    store.write_governed_decision.side_effect = [None, ConnectionError("down")]

    report = restore_bundle_if_empty(store, path, domain="trading")

    assert report.success is True
    assert report.fully_restored is False
    assert report.stores_restored == 1
    assert report.stores_failed == 1
    assert report.failed_stores == ["decisions"]
