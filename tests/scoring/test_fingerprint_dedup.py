from __future__ import annotations

from gae.profile_scorer import ProfileScorer

from copilot_sdk.graph import InMemoryGraphStore
from copilot_sdk.scoring.scorer import CompoundingScorer


def _make_scorer(mock_preset) -> tuple[CompoundingScorer, InMemoryGraphStore]:
    store = InMemoryGraphStore(domain="test")
    scorer = CompoundingScorer(
        mock_preset,
        ProfileScorer(
            mu=mock_preset.bootstrap_centroids.copy(),
            actions=list(mock_preset.shape.action_names),
            categories=list(mock_preset.shape.category_names),
        ),
        graph_store=store,
    )
    return scorer, store


def test_learn_writes_exactly_one_fingerprint(mock_preset) -> None:
    scorer, store = _make_scorer(mock_preset)
    category = mock_preset.shape.category_names[0]
    result = scorer.score(
        {name: 0.5 for name in mock_preset.shape.factor_names},
        category,
    )

    scorer.learn(result.decision_id, result.action)

    assert len(store._fingerprints) == 1


def test_compute_iks_does_not_persist_fingerprint(mock_preset) -> None:
    scorer, store = _make_scorer(mock_preset)
    store.write_decision(
        "test",
        category=mock_preset.shape.category_names[0],
        action=mock_preset.shape.action_names[0],
        confidence=0.7,
        factors={name: 0.5 for name in mock_preset.shape.factor_names},
        metadata={"decision_id": "iks-seed"},
    )

    scorer._compute_iks(persist_artifacts=True)

    assert len(store._fingerprints) == 0


def test_explicit_fingerprint_persist_true_still_works(mock_preset) -> None:
    scorer, store = _make_scorer(mock_preset)

    scorer.fingerprint(persist=True)

    assert len(store._fingerprints) == 1
