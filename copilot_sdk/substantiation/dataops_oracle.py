"""DataOps oracle for intelligence-map measurement-pipeline validation."""

from __future__ import annotations

from .oracle import (
    BaseOracle,
    ExperimentResult,
    compute_accuracy,
    compute_lift,
    floor_power,
)


class DataOpsOracle(BaseOracle):
    """DataOps pipeline validation oracle.

    Treatment: intelligence-map (P34) or recommendation shown.
    Measurement: remediation-acceptance lift (auto_approve vs investigate).
    """

    def __init__(
        self,
        *,
        base_accept_rate: float = 0.50,
        treatment_lift: float = 0.09,
        base_accuracy: float = 0.65,
        accuracy_lift: float = 0.04,
        seed: int = 42,
    ) -> None:
        self._seed = seed
        super().__init__(
            actions=["auto_approve", "investigate"],
            base_rate=base_accept_rate,
            treatment_lift=treatment_lift,
            base_accuracy=base_accuracy,
            accuracy_lift=accuracy_lift,
            override_rate=0.08,
            seed=seed,
        )

    def _primary_action(self, took_action: bool) -> str:
        return "auto_approve" if took_action else "investigate"


class DataOpsPipelineTest:
    """Run DataOpsOracle through the shared four-experiment pattern."""

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
        expected = 0.09
        treatment, control = _sample_arms(
            DataOpsOracle(treatment_lift=expected, seed=self._seed),
            self._n,
        )
        lift = compute_lift(
            treatment,
            control,
            positive_action="auto_approve",
        )
        return ExperimentResult(
            name="known_lift",
            expected_lift=expected,
            measured_lift=lift.escalation_lift,
            passed=abs(lift.escalation_lift - expected) <= 0.04,
            detail=lift,
        )

    def exp2_zero_lift(self) -> ExperimentResult:
        treatment, control = _sample_arms(
            DataOpsOracle(treatment_lift=0.0, accuracy_lift=0.0, seed=self._seed),
            self._n,
        )
        lift = compute_lift(
            treatment,
            control,
            positive_action="auto_approve",
        )
        return ExperimentResult(
            name="zero_lift",
            expected_lift=0.0,
            measured_lift=lift.escalation_lift,
            passed=abs(lift.escalation_lift) <= 0.03,
            detail=lift,
        )

    def exp3_floor_power(self) -> ExperimentResult:
        n_floor = floor_power(base_rate=0.50, delta=0.05)
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
            DataOpsOracle(treatment_lift=0.09, accuracy_lift=-0.08, seed=self._seed),
            self._n,
        )
        lift = compute_lift(
            treatment,
            control,
            positive_action="auto_approve",
        )
        accuracy = compute_accuracy(treatment, control)
        gate_pass = lift.escalation_lift > 0 and accuracy.treatment >= accuracy.control
        return ExperimentResult(
            name="lift_neg_accuracy",
            expected_lift=0.09,
            measured_lift=lift.escalation_lift,
            passed=not gate_pass,
            detail={
                "lift": lift,
                "accuracy": accuracy,
                "gate_correctly_rejected": not gate_pass,
            },
        )


def _sample_arms(oracle: DataOpsOracle, n: int) -> tuple[list[dict], list[dict]]:
    treatment = [oracle.synthetic_outcome(shown=True) for _ in range(n)]
    control_oracle = DataOpsOracle(
        base_accept_rate=oracle._base_rate,
        treatment_lift=oracle._lift,
        base_accuracy=oracle._base_accuracy,
        accuracy_lift=oracle._accuracy_lift,
        seed=oracle._seed,
    )
    control = [control_oracle.synthetic_outcome(shown=False) for _ in range(n)]
    return treatment, control
