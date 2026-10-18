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
        profile="test",
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


def test_prepare_score_is_read_only_until_persist(mock_preset) -> None:
    scorer, store = _make_scorer(mock_preset)
    category = mock_preset.shape.category_names[0]
    before_count = scorer._scorer.decision_count
    before_centroids = scorer._scorer.centroids.copy()

    prepared = scorer.prepare_score(
        {name: 0.5 for name in mock_preset.shape.factor_names}, category
    )

    assert scorer._scorer.decision_count == before_count
    assert (scorer._scorer.centroids == before_centroids).all()
    assert store.get_all_decisions("test") == []
    scorer.persist_prepared_score(prepared)
    assert len(store.get_all_decisions("test")) == 1


def test_fingerprint_reads_external_outcome_on_next_call(mock_preset) -> None:
    scorer, store = _make_scorer(mock_preset)
    category = mock_preset.shape.category_names[0]

    before = scorer.fingerprint(persist=False)
    result = scorer.score(
        {name: 0.5 for name in mock_preset.shape.factor_names},
        category,
    )
    store.write_outcome(result.decision_id, result.action, True, domain="test")

    after = scorer.fingerprint(persist=False)
    assert after.decisions_analyzed == 1
    assert before.decisions_analyzed == 0


def test_verified_decisions_reads_external_outcome_on_next_call(mock_preset) -> None:
    scorer, store = _make_scorer(mock_preset)
    category = mock_preset.shape.category_names[0]

    before = scorer._verified_decisions()
    result = scorer.score(
        {name: 0.5 for name in mock_preset.shape.factor_names},
        category,
    )
    store.write_outcome(result.decision_id, result.action, True, domain="test")

    after = scorer._verified_decisions()
    assert before == []
    assert len(after) == 1
