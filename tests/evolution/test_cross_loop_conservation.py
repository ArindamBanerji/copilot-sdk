from __future__ import annotations

import inspect
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import numpy as np

from apps.trading.backend.app.services.trading_evolver import TradingAgentEvolver
from copilot_sdk.ae.gate import PromotionGate as AEPromotionGate
from copilot_sdk.conservation.global_gate import GlobalConservationGate
from copilot_sdk.evolution import (
    ConservationSafety,
    DefaultPromotionGate,
    PromptEvolverConfig,
    PromptVariantEvolver,
    VariantSpec,
    evaluate_conservation_safety,
)
from copilot_sdk.graph.memory_store import InMemoryGraphStore
from copilot_sdk.scoring.scorer import CompoundingScorer


def _scorer() -> tuple[CompoundingScorer, InMemoryGraphStore]:
    store = InMemoryGraphStore(domain="trading")
    scorer = CompoundingScorer.from_preset(
        "trading",
        graph_store=store,
        profile="test",
        enable_rl=False,
    )
    return scorer, store


def _decision(scorer: CompoundingScorer) -> Any:
    factors = {name: 0.5 for name in scorer._preset.shape.factor_names}
    category = scorer._preset.shape.category_names[0]
    return scorer.score(factors, category)


def _pause(status: str = "RED", reason: str = "conservation_red") -> dict[str, Any]:
    return {
        "status": "paused",
        "reason": reason,
        "q": 0.0,
        "theta_min": 1.0,
        "verified_count": 10,
        "correct_count": 0,
        "alpha": 0.0,
        "category_coverage": 0.0,
        "override_rate": 1.0,
        "conservation_status": status,
        "conservation_mode": "normal",
        "conservation_read_failures": 0,
    }


def _prompt_evolver(provider: Any = None) -> PromptVariantEvolver:
    evolver = PromptVariantEvolver(
        config=PromptEvolverConfig(conservation_state_provider=provider)
    )
    evolver.register_variants(
        [
            VariantSpec(id="active", family="family", status="active"),
            VariantSpec(id="candidate", family="family", status="shadow"),
        ]
    )
    for _ in range(6):
        evolver.record_outcome("active", True)
    for _ in range(4):
        evolver.record_outcome("active", False)
    for _ in range(9):
        evolver.record_outcome("candidate", True)
    evolver.record_outcome("candidate", False)
    return evolver


def _promotable_shadow() -> dict[str, Any]:
    return {
        "sufficient": True,
        "total": 2_000,
        "correct": 1_640,
        "accuracy": 0.82,
        "baseline_total": 2_000,
        "baseline_correct": 1_400,
        "baseline_accuracy": 0.70,
        "batch_accuracies": [0.81, 0.82, 0.83],
    }


def test_red_blocks_centroid_mutation() -> None:
    scorer, store = _scorer()
    decision = _decision(scorer)
    before = np.asarray(scorer._scorer.centroids).copy()
    before_verified = store.count_verified_decisions("trading")
    red = evaluate_conservation_safety("RED")
    scorer._capture_conservation_safety = lambda: (red, _pause())

    result = scorer.learn(
        decision.decision_id,
        decision.action,
        persist_artifacts=False,
    )

    assert result["status"] == "paused"
    assert np.array_equal(before, scorer._scorer.centroids)
    assert store.count_verified_decisions("trading") == before_verified
    assert store.get_decision(decision.decision_id, domain="trading").get("outcome") is None


def test_red_preserves_dk_weights() -> None:
    scorer, _store = _scorer()
    decision = _decision(scorer)
    original = np.ones(
        (scorer._preset.shape.n_categories, scorer._preset.shape.n_factors),
        dtype=np.float64,
    )
    scorer._scorer._dk_weights = original.copy()
    red = evaluate_conservation_safety("RED")
    scorer._capture_conservation_safety = lambda: (red, _pause())
    reestimate = MagicMock()
    scorer._scorer.reestimate_dk = reestimate

    scorer.learn(decision.decision_id, decision.action, persist_artifacts=False)
    changed = scorer.reestimate_dk_if_due()

    assert changed is False
    assert np.array_equal(original, scorer._scorer._dk_weights)
    reestimate.assert_not_called()


def test_promotion_gate_blocks_red() -> None:
    result = DefaultPromotionGate().evaluate(
        _promotable_shadow(),
        conservation_state="RED",
    )

    assert result["promoted"] is False
    assert result["checks"]["conservation"] is False
    assert result["reason"] == "conservation"


def test_prompt_promotion_all_paths() -> None:
    red = _prompt_evolver(lambda: {"status": "RED"})
    red_result = red.check_for_promotion("family")
    assert red_result["reason"] == "conservation_gate_red"
    assert red.store.get_variant("candidate").status == "shadow"

    green = _prompt_evolver(lambda: {"status": "GREEN"})
    green_result = green.check_for_promotion("family")
    assert green_result["promoted_id"] == "candidate"
    assert green.store.get_variant("candidate").status == "active"

    missing = _prompt_evolver()
    missing_result = missing.check_for_promotion("family")
    assert missing_result["reason"] == "conservation_gate_unavailable"
    assert missing.store.get_variant("candidate").status == "shadow"

    def failed_provider() -> dict[str, str]:
        raise ConnectionError("conservation unavailable")

    failed = _prompt_evolver(failed_provider)
    failed_result = failed.check_for_promotion("family")
    assert failed_result["reason"] == "conservation_gate_unavailable"
    assert failed.store.get_variant("candidate").status == "shadow"


def test_all_governed_loops_use_conservation_contract() -> None:
    root = Path(__file__).resolve().parents[2]
    governed = [
        root / "copilot_sdk/evolution/gate.py",
        root / "copilot_sdk/evolution/prompt_evolver.py",
        root / "copilot_sdk/scoring/scorer.py",
        root / "copilot_sdk/ae/gate.py",
        root / "copilot_sdk/conservation/global_gate.py",
        root / "apps/trading/backend/app/services/trading_evolver.py",
    ]
    sources = {path: path.read_text(encoding="utf-8") for path in governed}

    for path, source in sources.items():
        assert "evaluate_conservation_safety" in source, path
    assert "_is_conservation_safe" not in sources[
        root / "copilot_sdk/evolution/prompt_evolver.py"
    ]
    assert "_conservation_green" not in sources[
        root / "apps/trading/backend/app/services/trading_evolver.py"
    ]


def test_missing_state_fails_closed_all_levels() -> None:
    missing = evaluate_conservation_safety(None)
    assert missing == ConservationSafety(
        status="UNKNOWN",
        available=False,
        learning_allowed=False,
        promotion_allowed=False,
        reason="conservation_state_unavailable",
    )
    assert evaluate_conservation_safety("COLD_START").learning_allowed is True
    assert evaluate_conservation_safety("COLD_START").promotion_allowed is False
    assert DefaultPromotionGate().evaluate(
        _promotable_shadow(), conservation_state=None
    )["promoted"] is False
    assert AEPromotionGate(min_n=1).should_promote([1.0], [0.0]) is False

    scorer, _store = _scorer()
    before = np.asarray(scorer._scorer._dk_weights).copy() if scorer._scorer._dk_weights is not None else None
    scorer._capture_conservation_safety = lambda: (missing, _pause("UNKNOWN", "conservation_unavailable"))
    assert scorer.reestimate_dk_if_due() is False
    assert scorer.get_dk_weights() is None if before is None else np.array_equal(before, scorer._scorer._dk_weights)

    prompt = _prompt_evolver()
    result = prompt.check_for_promotion("family")
    assert result["reason"] == "conservation_gate_unavailable"
    assert prompt.store.get_variant("candidate").status == "shadow"


def test_provider_exception_fails_closed_all_levels() -> None:
    scorer, _store = _scorer()

    def failed_read() -> Any:
        raise ConnectionError("graph unavailable")

    scorer._read_conservation_inputs_with_retry = failed_read
    safety, pause = scorer._capture_conservation_safety()
    assert safety.available is False
    assert safety.learning_allowed is False
    assert pause is not None and pause["reason"] == "conservation_unavailable"
    assert scorer.reestimate_dk_if_due() is False

    class RaisingMapping(dict[str, object]):
        def get(self, key: str, default: object = None) -> object:
            raise RuntimeError("malformed state")

    malformed = evaluate_conservation_safety(RaisingMapping())
    assert malformed.available is False
    assert DefaultPromotionGate().evaluate(
        _promotable_shadow(), conservation_state=RaisingMapping()
    )["promoted"] is False

    prompt = _prompt_evolver(lambda: (_ for _ in ()).throw(ConnectionError("down")))
    result = prompt.check_for_promotion("family")
    assert result["reason"] == "conservation_gate_unavailable"


def test_single_snapshot_per_transaction() -> None:
    green = evaluate_conservation_safety("GREEN")
    assert evaluate_conservation_safety(green) is green

    prompt_reads = 0

    def prompt_provider() -> dict[str, str]:
        nonlocal prompt_reads
        prompt_reads += 1
        return {"status": "GREEN" if prompt_reads == 1 else "RED"}

    prompt = _prompt_evolver(prompt_provider)
    assert prompt.check_for_promotion("family")["promoted_id"] == "candidate"
    assert prompt_reads == 1

    global_store = MagicMock()
    global_store.get_latest_conservation_statuses.return_value = [
        {"domain": "soc", "status": "GREEN", "verified_count": 10},
        {"domain": "s2p", "status": "GREEN", "verified_count": 10},
    ]
    transfer = GlobalConservationGate(global_store, domains=("soc", "s2p"))
    assert transfer.check_transfer("soc", "s2p")["allowed"] is True
    global_store.get_latest_conservation_statuses.assert_called_once()

    trading_reads = 0

    def trading_provider() -> dict[str, str]:
        nonlocal trading_reads
        trading_reads += 1
        return {"status": "GREEN" if trading_reads == 1 else "RED"}

    trading = TradingAgentEvolver(
        baseline_scorer=MagicMock(),
        store_factory=MagicMock(return_value=object()),
        conservation_provider=trading_provider,
    )
    trading._variants["candidate"] = {"variant_id": "candidate", "adjustments": {}}
    trading._results["candidate"] = [
        {
            "improvement_pp": 12.0,
            "decisions_tested": 1_000,
            "variant_accuracy": 0.82,
            "baseline_accuracy": 0.70,
        }
        for _ in range(3)
    ]
    assert trading.promote("candidate")["promoted"] is True
    assert trading_reads == 1

    router_source = inspect.getsource(
        __import__(
            "copilot_sdk.backend.scoring_router",
            fromlist=["_persist_dk_state_l5"],
        )._persist_dk_state_l5
    )
    assert 'if "dk_refresh" not in payload' in router_source
