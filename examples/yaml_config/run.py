"""Level-2: Run a copilot from YAML config. No Python domain code."""

from __future__ import annotations

import argparse
import random
from pathlib import Path
from typing import Any

from .loader import ConfiguredScorer, load_scorer

_FACTORS = (
    "signal_alignment", "market_regime", "position_sizing", "timing_quality",
    "risk_reward_actual", "emotional_indicator", "signal_confidence",
    "options_delta_exposure", "options_iv_percentile", "options_gamma_risk",
)
_CATEGORIES = ("trend_following", "mean_reversion", "event_driven", "income_strategy")


def run_loop(scorer: ConfiguredScorer, seed: int = 5, steps: int = 12) -> list[str]:
    """Run the same score -> outcome -> learn loop used by Python callers."""
    rng = random.Random(seed)
    decisions: list[str] = []
    for step in range(steps):
        factors = {name: rng.random() for name in _FACTORS}
        result = scorer.score(factors, _CATEGORIES[step % len(_CATEGORIES)])
        scorer.learn(result.decision_id, result.action, context={"preseed": True})
        decisions.append(result.action)
        print(f"{step + 1:02d}  {result.category:<16} {result.action:<18} {result.confidence:.3f}")
    return decisions


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("config", type=Path)
    args = parser.parse_args(argv)
    config = load_scorer(args.config)
    print(f"Preset: {config.config['from']}  penalty_ratio: {config.config['penalty_ratio']}")
    print("step category          decision             confidence")
    run_loop(config)
    print("Surfaces: decisions, confidence, and learned outcomes emitted above.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
