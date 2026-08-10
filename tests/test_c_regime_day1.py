from __future__ import annotations

import pytest

pytest.importorskip("gae.profile_scorer")

from copilot_sdk.graph import InMemoryGraphStore
from copilot_sdk.scoring.scorer import CompoundingScorer
from scripts.preseed_all_copilots import annotate_trading_regime


CANONICAL_REGIMES = {"trending", "ranging", "volatile"}


def _scorer() -> tuple[CompoundingScorer, InMemoryGraphStore]:
    store = InMemoryGraphStore(domain="trading")
    scorer = CompoundingScorer.from_preset(
        "trading", graph_store=store, profile="test", enable_rl=False
    )
    return scorer, store


def _factors(scorer: CompoundingScorer) -> dict[str, float]:
    return {name: 0.5 for name in scorer._preset.shape.factor_names}


def _category(scorer: CompoundingScorer) -> str:
    return str(scorer._preset.shape.category_names[0])


def test_checkpoint_has_regime_tag() -> None:
    scorer, store = _scorer()
    result = scorer.score(_factors(scorer), _category(scorer), metadata={"regime_tag": "trending"})
    scorer.learn(result.decision_id, result.action)

    checkpoints = store.get_centroid_checkpoints("trading", include_v2=True)
    assert checkpoints
    assert checkpoints[-1]["metadata"]["regime_tag"] == "trending"


def test_decision_has_regime_tag() -> None:
    scorer, store = _scorer()
    result = scorer.score(_factors(scorer), _category(scorer), metadata={"regime_tag": "volatile"})

    decision = store.get_decision(result.decision_id, domain="trading")
    assert decision is not None
    assert decision["metadata"]["regime_tag"] == "volatile"


def test_preseed_creates_regime_tagged_decisions() -> None:
    seed = [{"category": "equities"} for _ in range(15)]
    annotated = annotate_trading_regime(seed)
    tags = {row["regime"] for row in annotated}

    assert tags == CANONICAL_REGIMES
    assert all(sum(row["regime"] == tag for row in annotated) >= 5 for tag in CANONICAL_REGIMES)
    assert all(row["regime_context"]["regime"] in CANONICAL_REGIMES for row in annotated)


def test_preseed_creates_per_regime_checkpoints() -> None:
    scorer, store = _scorer()
    seed = annotate_trading_regime([{} for _ in range(15)])
    category = _category(scorer)
    for row in seed:
        result = scorer.score(_factors(scorer), category, metadata={"regime_tag": row["regime"]})
        scorer.learn(
            result.decision_id,
            result.action,
            consolidate=True,
            context={"preseed": True, "consolidate": True},
        )

    checkpoints = store.get_centroid_checkpoints("trading", include_v2=True)
    checkpoint_tags = [checkpoint["metadata"].get("regime_tag") for checkpoint in checkpoints]
    assert all(tag in checkpoint_tags for tag in CANONICAL_REGIMES)


def test_three_canonical_labels_only() -> None:
    scorer, store = _scorer()
    for tag in ("trending", "ranging", "volatile"):
        result = scorer.score(_factors(scorer), _category(scorer), metadata={"regime_tag": tag})
        scorer.learn(result.decision_id, result.action)

    decisions = [store.get_decision(decision_id, domain="trading") for decision_id in store._decisions]
    decision_tags = {decision["metadata"].get("regime_tag") for decision in decisions if decision}
    checkpoints = store.get_centroid_checkpoints("trading", include_v2=True)
    checkpoint_tags = {checkpoint["metadata"].get("regime_tag") for checkpoint in checkpoints}
    assert decision_tags <= CANONICAL_REGIMES
    assert checkpoint_tags <= CANONICAL_REGIMES


def test_legacy_checkpoint_has_null_regime() -> None:
    store = InMemoryGraphStore(domain="trading")
    store.write_centroid_checkpoint(
        checkpoint_id="legacy-checkpoint",
        domain="trading",
        category="general",
        action="hold",
        centroids=[[[0.5] * 7] * 3],
        decisions_count=1,
        verified_count=0,
        iks=0.0,
        shape=[1, 3, 7],
        factor_names_hash="legacy",
        metadata={"decision_id": "legacy-decision"},
    )

    checkpoint = store.get_centroid_checkpoints("trading", include_v2=True)[0]
    assert checkpoint["metadata"].get("regime_tag") is None
