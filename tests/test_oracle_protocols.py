from __future__ import annotations

from copilot_sdk.substantiation import (
    AnalyticClaim,
    BaseOracle,
    ChefOracle,
    ChefPipelineTest,
    ConditionalHoldout,
    DataOpsOracle,
    DataOpsPipelineTest,
    HoldoutAssigner,
    Oracle,
    RealInstrument,
    ScrapedContextProvider,
    TraderOracle,
    TraderPipelineTest,
    UnconditionalHoldout,
    compute_accuracy,
    compute_lift,
    floor_power,
)


def _sample(oracle: BaseOracle, *, shown: bool, n: int = 5000) -> list[dict]:
    return [oracle.synthetic_outcome(shown=shown) for _ in range(n)]


def test_base_oracle_deterministic():
    first = BaseOracle(
        actions=["escalate", "dismiss"],
        base_rate=0.30,
        treatment_lift=0.10,
        base_accuracy=0.70,
        accuracy_lift=0.05,
        seed=123,
    )
    second = BaseOracle(
        actions=["escalate", "dismiss"],
        base_rate=0.30,
        treatment_lift=0.10,
        base_accuracy=0.70,
        accuracy_lift=0.05,
        seed=123,
    )
    assert [first.synthetic_outcome(shown=True) for _ in range(20)] == [
        second.synthetic_outcome(shown=True) for _ in range(20)
    ]


def test_base_oracle_treatment_lift():
    treatment = _sample(
        BaseOracle(
            actions=["escalate", "dismiss"],
            base_rate=0.30,
            treatment_lift=0.10,
            base_accuracy=0.70,
            accuracy_lift=0.05,
            seed=101,
        ),
        shown=True,
    )
    control = _sample(
        BaseOracle(
            actions=["escalate", "dismiss"],
            base_rate=0.30,
            treatment_lift=0.10,
            base_accuracy=0.70,
            accuracy_lift=0.05,
            seed=101,
        ),
        shown=False,
    )
    assert compute_lift(treatment, control).escalation_lift > 0.07


def test_base_oracle_correct_modeled():
    outcomes = _sample(
        BaseOracle(
            actions=["escalate", "dismiss"],
            base_rate=0.30,
            treatment_lift=0.10,
            base_accuracy=0.70,
            accuracy_lift=0.05,
            seed=202,
        ),
        shown=True,
        n=200,
    )
    assert any(row["correct"] for row in outcomes)
    assert any(not row["correct"] for row in outcomes)


def test_base_oracle_zero_lift():
    treatment = _sample(
        BaseOracle(
            actions=["escalate", "dismiss"],
            base_rate=0.40,
            treatment_lift=0.0,
            base_accuracy=0.65,
            accuracy_lift=0.0,
            seed=303,
        ),
        shown=True,
    )
    control = _sample(
        BaseOracle(
            actions=["escalate", "dismiss"],
            base_rate=0.40,
            treatment_lift=0.0,
            base_accuracy=0.65,
            accuracy_lift=0.0,
            seed=303,
        ),
        shown=False,
    )
    assert abs(compute_lift(treatment, control).escalation_lift) < 0.001


def test_base_oracle_negative_accuracy():
    treatment = _sample(
        BaseOracle(
            actions=["escalate", "dismiss"],
            base_rate=0.30,
            treatment_lift=0.10,
            base_accuracy=0.70,
            accuracy_lift=-0.20,
            seed=404,
        ),
        shown=True,
    )
    control = _sample(
        BaseOracle(
            actions=["escalate", "dismiss"],
            base_rate=0.30,
            treatment_lift=0.10,
            base_accuracy=0.70,
            accuracy_lift=-0.20,
            seed=404,
        ),
        shown=False,
    )
    accuracy = compute_accuracy(treatment, control)
    assert accuracy.treatment < accuracy.control


def test_compute_lift_basic():
    treatment = [{"action": "escalate"}, {"action": "dismiss"}]
    control = [{"action": "dismiss"}, {"action": "dismiss"}]
    result = compute_lift(treatment, control)
    assert result.treatment_rate == 0.5
    assert result.control_rate == 0.0
    assert result.escalation_lift == 0.5


def test_compute_accuracy_basic():
    treatment = [{"correct": True}, {"correct": False}]
    control = [{"correct": False}, {"correct": False}]
    result = compute_accuracy(treatment, control)
    assert result.treatment == 0.5
    assert result.control == 0.0


def test_compute_lift_with_positive_action():
    treatment = [{"buyer_action": "hold"}, {"buyer_action": "auto"}]
    control = [{"buyer_action": "auto"}, {"buyer_action": "auto"}]
    result = compute_lift(
        treatment,
        control,
        action_key="buyer_action",
        positive_action="hold",
    )
    assert result.escalation_lift == 0.5


def test_floor_power_positive():
    assert floor_power(base_rate=0.30, delta=0.05) > 0


def test_floor_power_smaller_delta_needs_more_N():
    assert floor_power(base_rate=0.30, delta=0.03) > floor_power(
        base_rate=0.30,
        delta=0.05,
    )


def test_unconditional_deterministic():
    holdout = UnconditionalHoldout(holdout_pct=15, seed=42)
    assert holdout.suppressed("entity-1") == holdout.suppressed("entity-1")


def test_unconditional_rate():
    holdout = UnconditionalHoldout(holdout_pct=15, seed=42)
    rate = sum(holdout.suppressed(f"entity-{i}") for i in range(1000)) / 1000
    assert 0.10 <= rate <= 0.20


def test_conditional_no_enrichment():
    holdout = ConditionalHoldout(holdout_pct=15, seed=42)
    assert not any(
        holdout.suppressed(f"entity-{i}", has_enrichment=False) for i in range(100)
    )


def test_conditional_with_enrichment():
    holdout = ConditionalHoldout(holdout_pct=15, seed=42)
    assert any(
        holdout.suppressed(f"entity-{i}", has_enrichment=True) for i in range(100)
    )


def test_conditional_rate_approximately_correct():
    holdout = ConditionalHoldout(holdout_pct=15, seed=42)
    rate = (
        sum(holdout.suppressed(f"entity-{i}", has_enrichment=True) for i in range(1000))
        / 1000
    )
    assert 0.10 <= rate <= 0.20


def test_real_instrument_protocol():
    class Instrument:
        decision_node_fields = ["treatment_flag", "outcome", "correct"]

        def measure(self, cohort: list[dict]) -> dict:
            return {"n": len(cohort)}

    assert isinstance(Instrument(), RealInstrument)


def test_scraped_context_protocol():
    class Provider:
        def populate(self, entity_id: str) -> dict:
            return {"entity_id": entity_id}

    assert isinstance(Provider(), ScrapedContextProvider)


def test_analytic_claim_protocol():
    class Claim:
        theorem_ref = "gamma theorem"
        conditions = ["epsilon_firm > 0"]
        bound = None

    assert isinstance(Claim(), AnalyticClaim)


def test_base_oracle_satisfies_protocol():
    oracle = BaseOracle(
        actions=["escalate", "dismiss"],
        base_rate=0.30,
        treatment_lift=0.10,
        base_accuracy=0.70,
        accuracy_lift=0.05,
    )
    assert isinstance(oracle, Oracle)


def test_unconditional_satisfies_protocol():
    assert isinstance(UnconditionalHoldout(), HoldoutAssigner)


def test_conditional_satisfies_protocol():
    assert isinstance(ConditionalHoldout(), HoldoutAssigner)


def test_trader_pipeline_run_all():
    results = TraderPipelineTest(n_per_arm=200).run_all()

    assert len(results) == 4
    assert all(result.passed for result in results.values())


def test_chef_pipeline_run_all():
    results = ChefPipelineTest(n_per_arm=200).run_all()

    assert len(results) == 4
    assert all(result.passed for result in results.values())


def test_dataops_pipeline_run_all():
    results = DataOpsPipelineTest(n_per_arm=200).run_all()

    assert len(results) == 4
    assert all(result.passed for result in results.values())


def test_all_oracles_satisfy_protocol():
    for oracle in (TraderOracle(), ChefOracle(), DataOpsOracle()):
        assert isinstance(oracle.known_effect, float)
        assert isinstance(oracle.known_accuracy_effect, float)
        assert callable(oracle.synthetic_outcome)
        assert isinstance(oracle, Oracle)


def test_oracle_outcomes_have_required_fields():
    required = {"action", "was_override", "quality_signal", "correct"}

    for oracle in (TraderOracle(), ChefOracle(), DataOpsOracle()):
        outcome = oracle.synthetic_outcome(shown=True)
        assert required.issubset(outcome)
