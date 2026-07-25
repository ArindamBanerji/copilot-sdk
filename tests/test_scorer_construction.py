import pytest

from copilot_sdk.graph.memory_store import InMemoryGraphStore
from copilot_sdk.scoring.scorer import CompoundingScorer


def test_production_scorer_requires_injected_store():
    with pytest.raises(RuntimeError, match="Production scorer requires an injected GraphStore"):
        CompoundingScorer.from_preset("trading", enable_rl=False)


def test_test_profile_uses_in_memory_store():
    scorer = CompoundingScorer.from_preset("trading", profile="test", enable_rl=False)
    assert isinstance(scorer.graph_store, InMemoryGraphStore)


def test_development_profile_uses_sqlite_store(tmp_path):
    scorer = CompoundingScorer.from_preset(
        "trading",
        db_path=str(tmp_path / "trading.db"),
        profile="development",
        enable_rl=False,
    )
    assert scorer.graph_store.__class__.__name__ == "SQLiteGraphStore"


def test_invalid_profile_raises():
    with pytest.raises(ValueError):
        CompoundingScorer.from_preset("trading", profile="bogus")
