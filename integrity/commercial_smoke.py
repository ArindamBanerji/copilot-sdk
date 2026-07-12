"""Commercial smoke check for core copilot score-confirm loop."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from copilot_sdk.graph.memory_store import InMemoryGraphStore  # noqa: E402
from copilot_sdk.scoring.scorer import CompoundingScorer  # noqa: E402


SUPPORTED = ("soc", "trading", "purchasing", "dataops", "s2p")


def _status(scorer: CompoundingScorer) -> str:
    pause = scorer._conservation_pause()
    if pause is None:
        return "GREEN"
    return "RED" if pause.get("reason") == "conservation_red" else "AMBER"


def run(copilot: str) -> dict[str, Any]:
    scorer = CompoundingScorer.from_preset(
        copilot,
        graph_store=InMemoryGraphStore(domain=copilot),
        enable_rl=False,
    )
    shape = scorer._preset.shape
    factors = {name: 0.6 for name in shape.factor_names}
    category = shape.category_names[0]
    score = scorer.score(factors, category, metadata={"source": "commercial_smoke"})
    learned = scorer.learn(score.decision_id, score.action, context={"source": "commercial_smoke"})
    score_after = scorer.score_read_only(factors, category)
    score_changed = (
        score_after.action != score.action
        or abs(float(score_after.confidence) - float(score.confidence)) > 1e-12
        or any(
            abs(float(after) - float(before)) > 1e-12
            for before, after in zip(score.probabilities, score_after.probabilities, strict=False)
        )
    )
    status = _status(scorer)
    passed = (
        bool(score.decision_id)
        and score.action in shape.action_names
        and learned.decisions_total >= 1
        and learned.centroid_delta > 0
        and score_changed
        and status in {"GREEN", "AMBER", "RED"}
    )
    return {
        "copilot": copilot,
        "status": "PASS" if passed else "FAIL",
        "action": score.action,
        "confidence": round(score.confidence, 6),
        "confidence_after": round(score_after.confidence, 6),
        "score_changed": score_changed,
        "decisions_total": learned.decisions_total,
        "centroid_delta": round(learned.centroid_delta, 8),
        "conservation": status,
        "iks": round(learned.iks_after, 6),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run commercial smoke loop.")
    parser.add_argument("--copilot", choices=SUPPORTED, required=True)
    args = parser.parse_args(argv)
    result = run(args.copilot)
    for key, value in result.items():
        print(f"{key}: {value}")
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
