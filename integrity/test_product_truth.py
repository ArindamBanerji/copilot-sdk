from __future__ import annotations

import json
import math
import subprocess
import sys
from pathlib import Path

import pytest

from copilot_sdk.evidence.provenance import Provenanced
from copilot_sdk.graph.memory_store import InMemoryGraphStore
from copilot_sdk.scoring.scorer import CompoundingScorer


def _scorer() -> CompoundingScorer:
    return CompoundingScorer.from_preset(
        "trading",
        graph_store=InMemoryGraphStore(domain="trading"),
        enable_rl=False,
    )


def _base_factors(scorer: CompoundingScorer, value: float = 0.5) -> dict[str, float]:
    return {name: value for name in scorer._preset.shape.factor_names}


def test_scorer_state_survives_process_restart(tmp_path: Path) -> None:
    scorer = _scorer()
    shape = scorer._preset.shape
    factors = _base_factors(scorer, 0.6)
    for _ in range(25):
        result = scorer.score(factors, shape.category_names[0])
        scorer.learn(result.decision_id, result.action, context={"restart_test": True})
    export_path = tmp_path / "state.json"
    scorer.export(export_path)
    before = scorer.score(factors, shape.category_names[0])
    script = (
        "import json; "
        "from copilot_sdk.scoring.scorer import CompoundingScorer; "
        f"s=CompoundingScorer.load({str(export_path)!r}); "
        f"r=s.score(json.loads({json.dumps(factors)!r}), {shape.category_names[0]!r}); "
        "print(json.dumps({'action': r.action, 'confidence': r.confidence}))"
    )
    output = subprocess.check_output([sys.executable, "-c", script], text=True)
    after = json.loads(output)
    print(f"restart before={before.action}/{before.confidence:.6f} after={after}")
    assert after["action"] == before.action
    assert math.isclose(float(after["confidence"]), before.confidence, abs_tol=1e-12)


def test_counterfactual_faithfulness() -> None:
    scorer = _scorer()
    shape = scorer._preset.shape
    low = _base_factors(scorer, 0.5)
    high = _base_factors(scorer, 0.5)
    for name in ("signal_alignment", "position_sizing", "risk_reward_actual", "signal_confidence"):
        low[name] = 0.1
        high[name] = 0.9
    low_score = scorer.score(low, shape.category_names[0])
    high_score = scorer.score(high, shape.category_names[0])
    delta = abs(high_score.confidence - low_score.confidence)
    print(f"counterfactual low={low_score.action}/{low_score.confidence:.4f} high={high_score.action}/{high_score.confidence:.4f} delta={delta:.4f}")
    assert high_score.action != low_score.action
    assert delta > 0.05


def test_counterfactual_direction() -> None:
    scorer = _scorer()
    shape = scorer._preset.shape
    weak = _base_factors(scorer, 0.5)
    strong = _base_factors(scorer, 0.5)
    for name in ("signal_alignment", "position_sizing", "risk_reward_actual", "signal_confidence"):
        weak[name] = 0.1
        strong[name] = 0.9
    weak_score = scorer.score(weak, shape.category_names[0])
    strong_score = scorer.score(strong, shape.category_names[0])
    strong_index = shape.action_names.index("strong_execution")
    print(f"direction weak_strong_prob={weak_score.probabilities[strong_index]:.4f} strong_strong_prob={strong_score.probabilities[strong_index]:.4f}")
    assert strong_score.probabilities[strong_index] > weak_score.probabilities[strong_index]


def test_displayed_factor_matches_computed() -> None:
    scorer = _scorer()
    shape = scorer._preset.shape
    computed = _base_factors(scorer, 0.42)
    result = scorer.score(computed, shape.category_names[0])
    print(f"displayed_factor_count={len(result.factors)}")
    assert result.factors == computed


def test_sample_value_rejected_from_metric() -> None:
    scorer = _scorer()
    shape = scorer._preset.shape
    factors: dict[str, object] = _base_factors(scorer, 0.5)
    factors[shape.factor_names[0]] = Provenanced(0.5, "sample")
    try:
        scorer.score(factors, shape.category_names[0])  # type: ignore[arg-type]
    except (TypeError, ValueError) as exc:
        message = str(exc).lower()
        if "provenance" in message and "provenanced" not in message:
            return
        pytest.fail(f"sample-provenance rejection used the wrong error: {exc}")
    pytest.fail("sample-provenance factor was accepted into scoring")
