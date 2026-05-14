from __future__ import annotations

import argparse
import tempfile
import time
from pathlib import Path

import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from copilot_sdk.scoring.presets import PRESET_REGISTRY
from copilot_sdk.graph.memory_store import InMemoryGraphStore
from copilot_sdk.scoring.scorer import CompoundingScorer


class DemoGraphStore(InMemoryGraphStore):
    def write_decision(self, *args, **kwargs) -> str:
        decision_id = super().write_decision(*args, **kwargs)
        metadata = kwargs.get("metadata") or {}
        decision = self._decisions[decision_id]
        decision["factor_vector"] = list(metadata.get("factor_vector") or [])
        decision["recommended_index"] = int(metadata.get("recommended_index", 0))
        decision["category_index"] = int(metadata.get("category_index", 0))
        return decision_id

    def count_verified(self) -> int:
        return super().count_verified() + 50

    def count_correct(self) -> int:
        return super().count_correct() + 50


def _factors(names: tuple[str, ...], step: int, seed: int) -> dict[str, float]:
    return {
        name: ((step + seed + index) % 10) / 10.0
        for index, name in enumerate(names)
    }


def run(domain: str, decisions: int, seed: int) -> None:
    preset = PRESET_REGISTRY[domain]()
    start = time.perf_counter()
    with tempfile.TemporaryDirectory(prefix="copilot-sdk-evolve-") as tmp:
        db_path = str(Path(tmp) / f"{domain}.db")
        scorer = CompoundingScorer.from_preset(
            domain,
            db_path=db_path,
            graph_store=DemoGraphStore(),
            evolve=True,
        )
        categories = tuple(preset.shape.category_names)
        factors = tuple(preset.shape.factor_names)
        for step in range(max(int(decisions), 0)):
            category = categories[step % len(categories)]
            result = scorer.score(_factors(factors, step, seed), category)
            scorer.learn(result.decision_id, result.action)

        evolver = getattr(scorer, "_evolver", None)
        active_rules = sorted(evolver.get_active_rules()) if evolver is not None else []
        history = evolver.get_evolution_history(limit=1000) if evolver is not None else []
        promoted = evolver.get_promoted_rules() if evolver is not None else []
        elapsed = time.perf_counter() - start
        print(f"domain: {domain}")
        print(f"decisions: {decisions}")
        print(f"active_rules: {active_rules}")
        print(f"event_count: {len(history)}")
        print(f"promoted_rules: {promoted}")
        print(f"elapsed_seconds: {elapsed:.3f}")
        scorer.store.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a local CompoundingScorer evolution demo.")
    parser.add_argument("--domain", choices=sorted(PRESET_REGISTRY), default="trading")
    parser.add_argument("--decisions", type=int, default=25)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    run(args.domain, args.decisions, args.seed)


if __name__ == "__main__":
    main()
