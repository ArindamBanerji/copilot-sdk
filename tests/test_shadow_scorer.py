from __future__ import annotations

from dataclasses import dataclass

import pytest

from copilot_sdk.graph import InMemoryGraphStore
from copilot_sdk.migrate.shadow_scorer import (
    ComparisonResult,
    ShadowScorer,
    _values_match,
)


@dataclass
class FakeScore:
    decision_id: str
    action: str = "strong_execution"
    action_index: int = 0
    confidence: float = 0.8
    probabilities: list[float] | None = None
    category: str = "trend_following"
    factors: dict[str, float] | None = None

    def __post_init__(self) -> None:
        if self.probabilities is None:
            self.probabilities = [0.8, 0.1, 0.05, 0.05]
        if self.factors is None:
            self.factors = {"signal_alignment": 0.7, "market_regime": 0.5}


class FakeScorer:
    def __init__(self, scores: list[FakeScore] | None = None) -> None:
        self._scores = list(scores or [])
        self.learn_calls: list[tuple[tuple, dict]] = []

    def score(self, *args, **kwargs):
        _ = args, kwargs
        return self._scores.pop(0) if self._scores else FakeScore("default")

    def learn(self, *args, **kwargs):
        self.learn_calls.append((args, kwargs))
        return {"decision_id": args[0] if args else kwargs.get("decision_id")}


class CrashingScoreScorer(FakeScorer):
    def score(self, *args, **kwargs):
        _ = args, kwargs
        raise RuntimeError("shadow score failed")


class CrashingLearnScorer(FakeScorer):
    def learn(self, *args, **kwargs):
        _ = args, kwargs
        raise RuntimeError("shadow learn failed")


def _shadow(primary_scores: list[FakeScore], shadow_scores: list[FakeScore], threshold: int = 50) -> ShadowScorer:
    shadow = ShadowScorer(
        primary=FakeScorer(primary_scores),  # type: ignore[arg-type]
        shadow=FakeScorer(shadow_scores),  # type: ignore[arg-type]
        proven_threshold=threshold,
    )
    shadow.compare_state = lambda: ComparisonResult(True, {"state": {"matched": True}})  # type: ignore[method-assign]
    return shadow


def _trading_factors(seed: int) -> dict[str, float]:
    names = [
        "signal_alignment",
        "market_regime",
        "position_sizing",
        "timing_quality",
        "risk_reward_actual",
        "emotional_indicator",
        "signal_confidence",
        "options_delta_exposure",
        "options_iv_percentile",
        "options_gamma_risk",
    ]
    return {
        name: round(((seed + index + 1) % 10) / 10, 4)
        for index, name in enumerate(names)
    }


def test_same_store_rejected():
    store = InMemoryGraphStore(domain="trading")

    with pytest.raises(ValueError, match="independent"):
        ShadowScorer.from_preset("trading", primary_store=store, shadow_store=store)


def test_same_scorer_rejected():
    scorer = FakeScorer()

    with pytest.raises(ValueError, match="independent"):
        ShadowScorer(primary=scorer, shadow=scorer)  # type: ignore[arg-type]


def test_shadow_score_matching():
    scorer = _shadow([FakeScore("p1")], [FakeScore("s1")])

    result = scorer.score({"signal_alignment": 0.7}, "trend_following")

    assert result.decision_id == "p1"
    assert scorer.status.status == "validating"
    assert scorer.status.total_comparisons == 1
    assert scorer.status.consecutive_matches == 1
    assert scorer.status.mismatches == []


def test_shadow_score_mismatch_logged():
    scorer = _shadow(
        [FakeScore("p1", action="strong_execution")],
        [FakeScore("s1", action="skip_recommended")],
    )

    scorer.score({"signal_alignment": 0.7}, "trend_following")

    assert scorer.status.consecutive_matches == 0
    assert len(scorer.status.mismatches) == 1
    mismatch = scorer.status.mismatches[0]
    assert mismatch["operation"] == "score"
    assert mismatch["decision_id"] == "p1"
    assert mismatch["field_results"]["recommended_action"]["primary"] == "strong_execution"
    assert mismatch["field_results"]["recommended_action"]["shadow"] == "skip_recommended"


def test_shadow_score_crash_returns_primary():
    scorer = ShadowScorer(
        primary=FakeScorer([FakeScore("p1")]),  # type: ignore[arg-type]
        shadow=CrashingScoreScorer(),  # type: ignore[arg-type]
    )

    result = scorer.score({"signal_alignment": 0.7}, "trend_following")

    assert result.decision_id == "p1"
    assert scorer.status.total_comparisons == 1
    assert len(scorer.status.mismatches) == 1
    assert "RuntimeError: shadow score failed" in scorer.status.mismatches[0]["field_results"]["shadow_exception"]["shadow"]


def test_shadow_learn_matching():
    scorer = _shadow([FakeScore("p1")], [FakeScore("s1")])
    scorer.score({"signal_alignment": 0.7}, "trend_following")

    result = scorer.learn("p1", "strong_execution")

    assert result == {"decision_id": "p1"}
    assert scorer.status.total_comparisons == 2
    assert scorer.status.consecutive_matches == 2
    shadow_fake = scorer.shadow
    assert shadow_fake.learn_calls[0][0][0] == "s1"


def test_shadow_learn_crash_returns_primary():
    scorer = ShadowScorer(
        primary=FakeScorer([FakeScore("p1")]),  # type: ignore[arg-type]
        shadow=CrashingLearnScorer([FakeScore("s1")]),  # type: ignore[arg-type]
    )
    scorer.score({"signal_alignment": 0.7}, "trend_following")

    result = scorer.learn("p1", "strong_execution")

    assert result == {"decision_id": "p1"}
    assert scorer.status.total_comparisons == 2
    assert len(scorer.status.mismatches) == 1
    assert "RuntimeError: shadow learn failed" in scorer.status.mismatches[0]["field_results"]["shadow_exception"]["shadow"]


def test_dict_float_tolerance():
    factors_a = {"signal": 0.8800000001, "regime": 0.92}
    factors_b = {"signal": 0.88, "regime": 0.92}

    assert _values_match(factors_a, factors_b, atol=1e-6) is True


def test_dict_key_mismatch_detected():
    factors_a = {"signal": 0.88}
    factors_b = {"signal": 0.88, "extra": 0.1}

    assert _values_match(factors_a, factors_b) is False


def test_learn_without_prior_score():
    scorer = ShadowScorer(
        primary=FakeScorer(),  # type: ignore[arg-type]
        shadow=CrashingLearnScorer(),  # type: ignore[arg-type]
    )

    result = scorer.learn("unknown_id", "strong_execution")

    assert result == {"decision_id": "unknown_id"}
    assert scorer.status.total_comparisons == 1
    assert len(scorer.status.mismatches) == 1


def test_double_score_then_learn_both():
    scorer = _shadow([FakeScore("pA"), FakeScore("pB")], [FakeScore("sA"), FakeScore("sB")])
    scorer.score({"signal_alignment": 0.7}, "trend_following")
    scorer.score({"signal_alignment": 0.8}, "trend_following")

    scorer.learn("pA", "strong_execution")
    scorer.learn("pB", "strong_execution")

    shadow_fake = scorer.shadow
    assert shadow_fake.learn_calls[0][0][0] == "sA"
    assert shadow_fake.learn_calls[1][0][0] == "sB"


def test_proven_after_threshold():
    scorer = _shadow(
        [FakeScore(f"p{i}") for i in range(3)],
        [FakeScore(f"s{i}") for i in range(3)],
        threshold=3,
    )

    for _ in range(3):
        scorer.score({"signal_alignment": 0.7}, "trend_following")

    assert scorer.status.status == "proven"
    assert scorer.status.consecutive_matches == 3


def test_proven_reverts_on_mismatch():
    scorer = _shadow(
        [
            FakeScore("p1"),
            FakeScore("p2"),
            FakeScore("p3", action="strong_execution"),
        ],
        [
            FakeScore("s1"),
            FakeScore("s2"),
            FakeScore("s3", action="skip_recommended"),
        ],
        threshold=2,
    )
    scorer.score({}, "trend_following")
    scorer.score({}, "trend_following")
    assert scorer.status.status == "proven"

    scorer.score({}, "trend_following")

    assert scorer.status.status == "validating"
    assert scorer.status.consecutive_matches == 0
    assert len(scorer.status.mismatches) == 1


def test_mismatch_list_capped():
    scorer = _shadow(
        [FakeScore(f"p{i}", action="strong_execution") for i in range(105)],
        [FakeScore(f"s{i}", action="skip_recommended") for i in range(105)],
    )

    for _ in range(105):
        scorer.score({}, "trend_following")

    assert len(scorer.status.mismatches) == 100
    assert scorer.status.mismatches[0]["decision_id"] == "p5"


def test_report_includes_all_fields():
    scorer = _shadow([FakeScore("p1")], [FakeScore("s1")], threshold=7)
    scorer.score({}, "trend_following")

    report = scorer.report()

    assert report["total_comparisons"] == 1
    assert report["consecutive_matches"] == 1
    assert report["status"] == "validating"
    assert report["proven_threshold"] == 7
    assert report["mismatches"] == []


def test_from_preset_creates_independent_scorers():
    primary_store = InMemoryGraphStore(domain="trading")
    shadow_store = InMemoryGraphStore(domain="trading")

    scorer = ShadowScorer.from_preset(
        "trading",
        primary_store=primary_store,
        shadow_store=shadow_store,
    )

    assert scorer.primary is not scorer.shadow
    assert scorer.primary.graph_store is primary_store
    assert scorer.shadow.graph_store is shadow_store
    assert scorer.primary.graph_store is not scorer.shadow.graph_store


@pytest.mark.timeout(60)
def test_50_cycle_proven_with_real_state_comparison():
    primary_store = InMemoryGraphStore(domain="trading")
    shadow_store = InMemoryGraphStore(domain="trading")
    scorer = ShadowScorer.from_preset(
        "trading",
        primary_store=primary_store,
        shadow_store=shadow_store,
        proven_threshold=50,
    )

    for index in range(50):
        result = scorer.score(_trading_factors(index), "trend_following")
        scorer.learn(result.decision_id, result.action)

    assert scorer.status.status == "proven"
    assert scorer.status.consecutive_matches >= 50
    assert scorer.compare_state().matched is True
