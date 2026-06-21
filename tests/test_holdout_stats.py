from copilot_sdk.substantiation import ConditionalHoldout, UnconditionalHoldout


def _suppression_count(assigner, entity_ids: list[str], **kwargs) -> int:
    return sum(assigner.suppressed(entity_id, **kwargs) for entity_id in entity_ids)


def test_unconditional_suppresses_approximately_15_pct():
    holdout = UnconditionalHoldout(holdout_pct=15, seed=42)
    entity_ids = [f"entity-{idx}" for idx in range(10_000)]

    suppressed = _suppression_count(holdout, entity_ids)

    assert 1_300 <= suppressed <= 1_700


def test_conditional_enriched_suppresses_15_pct():
    holdout = ConditionalHoldout(holdout_pct=15, seed=42)
    entity_ids = [f"entity-{idx}" for idx in range(10_000)]

    suppressed = _suppression_count(holdout, entity_ids, has_enrichment=True)

    assert 1_300 <= suppressed <= 1_700


def test_conditional_unenriched_suppresses_zero():
    holdout = ConditionalHoldout(holdout_pct=15, seed=42)
    entity_ids = [f"entity-{idx}" for idx in range(10_000)]

    suppressed = _suppression_count(holdout, entity_ids, has_enrichment=False)

    assert suppressed == 0


def test_holdout_deterministic_across_calls():
    holdout = UnconditionalHoldout(holdout_pct=15, seed=42)
    first = holdout.suppressed("entity-42")

    assert all(holdout.suppressed("entity-42") == first for _ in range(100))


def test_holdout_different_seeds_different_assignments():
    entity_ids = [f"entity-{idx}" for idx in range(2_000)]
    seed_42 = UnconditionalHoldout(holdout_pct=15, seed=42)
    seed_99 = UnconditionalHoldout(holdout_pct=15, seed=99)

    suppressed_42 = {entity_id for entity_id in entity_ids if seed_42.suppressed(entity_id)}
    suppressed_99 = {entity_id for entity_id in entity_ids if seed_99.suppressed(entity_id)}

    assert suppressed_42 != suppressed_99


def test_unconditional_uniform_distribution():
    holdout = UnconditionalHoldout(holdout_pct=15, seed=42)
    buckets = "0123456789abcdef"

    for bucket in buckets:
        entity_ids = [f"{bucket}-entity-{idx}" for idx in range(1_000)]
        rate = _suppression_count(holdout, entity_ids) / len(entity_ids)
        assert 0.10 <= rate <= 0.20
