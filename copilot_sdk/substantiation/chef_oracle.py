"""Purchasing oracle for par and trust measurement-pipeline validation."""

from __future__ import annotations

from .oracle import (
    BaseOracle,
    ExperimentResult,
    LiftResult,
    compute_accuracy,
    floor_power,
)


ORDER_ACTIONS = {"order_as_planned", "order_more", "order_less"}


class ChefOracle(BaseOracle):
    """Purchasing pipeline validation oracle.

    Treatment: par-intelligence (P73) or trust analysis (P75) shown.
    Measurement: order-change lift (non-skip ordering action vs skip).
    """

    def __init__(
        self,
        *,
        base_order_rate: float = 0.65,
        treatment_lift: float = 0.07,
        base_accuracy: float = 0.60,
        accuracy_lift: float = 0.05,
        seed: int = 42,
    ) -> None:
        self._seed = seed
        super().__init__(
            actions=["order_as_planned", "order_more", "order_less", "skip"],
            base_rate=base_order_rate,
            treatment_lift=treatment_lift,
            base_accuracy=base_accuracy,
            accuracy_lift=accuracy_lift,
            override_rate=0.12,
            seed=seed,
        )

    def _primary_action(self, took_action: bool) -> str:
        if not took_action:
            return "skip"
        roll = self._rng.random()
        if roll < 0.60:
            return "order_as_planned"
        if roll < 0.80:
            return "order_more"
        return "order_less"


class ChefPipelineTest:
    """Run ChefOracle through the shared four-experiment validation pattern."""

    def __init__(self, n_per_arm: int = 500, seed: int = 42) -> None:
        self._n = int(n_per_arm)
        self._seed = seed

    def run_all(self) -> dict[str, ExperimentResult]:
        return {
            "exp1_known_lift": self.exp1_known_lift(),
            "exp2_zero_lift": self.exp2_zero_lift(),
            "exp3_floor_power": self.exp3_floor_power(),
            "exp4_gate_rejects": self.exp4_gate_rejects(),
        }

    def exp1_known_lift(self) -> ExperimentResult:
        expected = 0.07
        treatment, control = _sample_arms(
            ChefOracle(treatment_lift=expected, seed=self._seed),
            self._n,
        )
        lift = _order_lift(treatment, control)
        return ExperimentResult(
            name="known_lift",
            expected_lift=expected,
            measured_lift=lift.escalation_lift,
            passed=abs(lift.escalation_lift - expected) <= 0.04,
            detail=lift,
        )

    def exp2_zero_lift(self) -> ExperimentResult:
        treatment, control = _sample_arms(
            ChefOracle(treatment_lift=0.0, accuracy_lift=0.0, seed=self._seed),
            self._n,
        )
        lift = _order_lift(treatment, control)
        return ExperimentResult(
            name="zero_lift",
            expected_lift=0.0,
            measured_lift=lift.escalation_lift,
            passed=abs(lift.escalation_lift) <= 0.03,
            detail=lift,
        )

    def exp3_floor_power(self) -> ExperimentResult:
        n_floor = floor_power(base_rate=0.65, delta=0.05)
        return ExperimentResult(
            name="floor_power",
            expected_lift=0.05,
            measured_lift=0.0,
            passed=n_floor > 0,
            detail={
                "n_per_arm_floor": n_floor,
                "caveat": "gaussian lower bound; real N higher",
            },
        )

    def exp4_gate_rejects(self) -> ExperimentResult:
        treatment, control = _sample_arms(
            ChefOracle(treatment_lift=0.07, accuracy_lift=-0.08, seed=self._seed),
            self._n,
        )
        lift = _order_lift(treatment, control)
        accuracy = compute_accuracy(treatment, control)
        gate_pass = lift.escalation_lift > 0 and accuracy.treatment >= accuracy.control
        return ExperimentResult(
            name="lift_neg_accuracy",
            expected_lift=0.07,
            measured_lift=lift.escalation_lift,
            passed=not gate_pass,
            detail={
                "lift": lift,
                "accuracy": accuracy,
                "gate_correctly_rejected": not gate_pass,
            },
        )


def _sample_arms(oracle: ChefOracle, n: int) -> tuple[list[dict], list[dict]]:
    treatment = [oracle.synthetic_outcome(shown=True) for _ in range(n)]
    control_oracle = ChefOracle(
        base_order_rate=oracle._base_rate,
        treatment_lift=oracle._lift,
        base_accuracy=oracle._base_accuracy,
        accuracy_lift=oracle._accuracy_lift,
        seed=oracle._seed,
    )
    control = [control_oracle.synthetic_outcome(shown=False) for _ in range(n)]
    return treatment, control


def _order_lift(treatment: list[dict], control: list[dict]) -> LiftResult:
    treatment_rate = sum(row["action"] in ORDER_ACTIONS for row in treatment) / len(
        treatment
    )
    control_rate = sum(row["action"] in ORDER_ACTIONS for row in control) / len(control)
    return LiftResult(
        treatment_rate=treatment_rate,
        control_rate=control_rate,
        escalation_lift=treatment_rate - control_rate,
    )
