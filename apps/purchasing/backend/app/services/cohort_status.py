"""Purchasing cohort day-zero state machine.

The cohort status endpoint separates three evidence streams:
- instrument: oracle self-test evidence, labelled oracle
- real: verified operational decisions, labelled real
- structure: sample fixtures, labelled sample

Only real cohorts can move the state machine or produce lift.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from copilot_sdk.substantiation.cohort_day_zero import (
    ACCUMULATING,
    INSTRUMENT_VALIDATED,
    MEASURED,
    STATES,
    BaseCohortDayZeroState,
    compute_state,
    evaluate_v7_gate as _sdk_evaluate_v7_gate,
)

STATE_VALUES = frozenset(STATES)

REAL_PROVENANCE = "real"
SAMPLE_PROVENANCE = "sample"
ORACLE_PROVENANCE = "oracle"

POSITIVE_ACTIONS = frozenset(
    {
        "accept",
        "accepted",
        "approve",
        "approved",
        "confirm",
        "confirmed",
        "order_as_planned",
        "order_more",
        "order_less",
    }
)
NEGATIVE_ACTIONS = frozenset(
    {
        "dismiss",
        "dismissed",
        "override",
        "overridden",
        "reject",
        "rejected",
        "skip",
        "skipped",
    }
)


def evaluate_v7_gate(cohort_status: dict[str, Any]) -> dict[str, Any]:
    """Compatibility wrapper around the SDK v7.0 gate."""

    real = cohort_status.get("real", {})
    threshold_k = int(
        real.get("threshold_k", cohort_status.get("threshold_k", PurchasingCohortStatus.THRESHOLD_K))
    )
    gate_input = dict(real)
    gate_input["provenance"] = REAL_PROVENANCE
    records = cohort_status.get("records") or real.get("records")
    if records is not None:
        gate_input["records"] = records
    return _sdk_evaluate_v7_gate(gate_input, threshold_k)


class PurchasingCohortStatus(BaseCohortDayZeroState):
    """Purchasing par-intelligence cohort day-zero status.

    Real lift is computed from provenance=="real" cohorts only. Sample
    structure and oracle instrument evidence are displayed separately and
    never advance the state machine.
    """

    DOMAIN = "purchasing"
    THRESHOLD_K = 30

    def __init__(
        self,
        graph_store: Any | None = None,
        oracle_artifact_path: str | Path | None = None,
        decision_records: list[dict[str, Any]] | None = None,
    ) -> None:
        self._graph_store = graph_store
        self._decision_records = decision_records
        self._oracle_artifact_path = (
            Path(oracle_artifact_path)
            if oracle_artifact_path is not None
            else Path(__file__).resolve().parents[2] / "chef_oracle_plumb_results.json"
        )

    def _load_instrument(self) -> dict[str, Any]:
        """Load ChefOracle self-test results as oracle provenance."""

        artifact = self._oracle_artifact_path
        result = {
            "validated": False,
            "provenance": ORACLE_PROVENANCE,
            "source_artifact": str(artifact),
            "experiments": [],
        }
        if not artifact.exists():
            return result

        try:
            data = json.loads(artifact.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return result

        experiments = _extract_experiments(data)
        result["experiments"] = experiments
        explicit_validated = data.get("validated") if isinstance(data, dict) else False
        result["validated"] = bool(explicit_validated) or (
            bool(experiments) and all(bool(exp.get("pass")) for exp in experiments)
        )
        return result

    def _count_real_cohorts(self) -> dict[str, Any]:
        """Count treatment/control cohorts where provenance is real."""

        treatment_n, control_n = _count_arms(self._real_records())
        return {
            "treatment_n": treatment_n,
            "control_n": control_n,
        }

    def _count_structure_cohorts(self) -> dict[str, Any]:
        """Count sample cohorts for structure display only."""

        sample_records = [
            record
            for record in self._read_decisions()
            if _record_provenance(record) == SAMPLE_PROVENANCE
        ]
        treatment_n, control_n = _count_arms(sample_records)
        total = treatment_n + control_n
        split_balanced = None
        if total:
            split_balanced = abs(treatment_n - control_n) <= max(1, int(total * 0.1))
        return {
            "present": total > 0,
            "treatment_n": treatment_n,
            "control_n": control_n,
            "split_balanced": split_balanced,
            "join_ok": True if total else None,
            "provenance": SAMPLE_PROVENANCE,
        }

    def _compute_real_lift(self) -> float:
        """Compute lift from provenance=='real' decisions only.

        Any sample or oracle record reaching this method raises under F-26.
        """

        records = self._real_records()
        counts = {"treatment": 0, "control": 0}
        positives = {"treatment": 0, "control": 0}

        for record in records:
            provenance = _record_provenance(record)
            if provenance != REAL_PROVENANCE:
                raise ValueError("sample/oracle cohorts are forbidden in real lift")
            arm = _cohort_arm(record)
            if arm not in counts:
                continue
            counts[arm] += 1
            if _is_positive_outcome(record):
                positives[arm] += 1

        if counts["treatment"] == 0 or counts["control"] == 0:
            return 0.0

        treatment_rate = positives["treatment"] / counts["treatment"]
        control_rate = positives["control"] / counts["control"]
        return round(treatment_rate - control_rate, 6)

    def _real_records(self) -> list[dict[str, Any]]:
        return [
            record
            for record in self._read_decisions()
            if _record_provenance(record) == REAL_PROVENANCE
        ]

    def _read_decisions(self) -> list[dict[str, Any]]:
        if self._decision_records is not None:
            return [dict(record) for record in self._decision_records]
        if self._graph_store is None:
            return []

        for method_name in ("get_verified_decisions", "get_all_decisions", "get_decisions"):
            method = getattr(self._graph_store, method_name, None)
            if method is None:
                continue
            try:
                if method_name == "get_decisions":
                    return list(method("purchasing", limit=10000))
                return list(method("purchasing"))
            except Exception:
                continue
        return []


def _extract_experiments(data: Any) -> list[dict[str, Any]]:
    if isinstance(data, list):
        raw_experiments = data
    elif isinstance(data, dict):
        raw_experiments = (
            data.get("experiments")
            or data.get("results")
            or data.get("experiment_results")
            or []
        )
    else:
        raw_experiments = []

    experiments: list[dict[str, Any]] = []
    for index, raw in enumerate(raw_experiments):
        if not isinstance(raw, dict):
            continue
        experiments.append(
            {
                "name": str(raw.get("name") or raw.get("experiment") or f"experiment_{index + 1}"),
                "injected_lift": _nullable_float(
                    raw.get("injected_lift", raw.get("expected_lift"))
                ),
                "recovered_lift": _nullable_float(
                    raw.get("recovered_lift", raw.get("measured_lift"))
                ),
                "pass": bool(raw.get("pass", raw.get("passed", False))),
            }
        )
    return experiments


def _count_arms(records: list[dict[str, Any]]) -> tuple[int, int]:
    treatment_n = 0
    control_n = 0
    for record in records:
        arm = _cohort_arm(record)
        if arm == "treatment":
            treatment_n += 1
        elif arm == "control":
            control_n += 1
    return treatment_n, control_n


def _record_provenance(record: dict[str, Any]) -> str:
    value = _nested_value(record, "provenance", "provenance_tier")
    return str(value).casefold() if value is not None else ""


def _cohort_arm(record: dict[str, Any]) -> str | None:
    explicit = _nested_value(record, "holdout_group", "cohort", "cohort_group")
    if explicit is not None:
        normalized = str(explicit).casefold()
        if normalized in {"treatment", "shown", "par_shown"}:
            return "treatment"
        if normalized in {"control", "suppressed", "par_suppressed"}:
            return "control"

    par_shown = _nested_value(record, "par_shown", "par_displayed", "treatment")
    if par_shown is None:
        return None
    return "treatment" if _truthy(par_shown) else "control"


def _is_positive_outcome(record: dict[str, Any]) -> bool:
    for key in ("actual_action", "action", "outcome", "chef_action"):
        action = _nested_value(record, key)
        if action is None:
            continue
        normalized = str(action).casefold()
        if normalized in POSITIVE_ACTIONS:
            return True
        if normalized in NEGATIVE_ACTIONS:
            return False
    value = _nested_value(record, "is_correct", "correct")
    return bool(value) if value is not None else False


def _nested_value(record: dict[str, Any], *keys: str) -> Any:
    containers: list[Any] = [record]
    for container_key in ("metadata", "context", "outcome_metadata", "factors"):
        nested = record.get(container_key)
        if isinstance(nested, dict):
            containers.append(nested)
            if isinstance(nested.get("context"), dict):
                containers.append(nested["context"])
            if isinstance(nested.get("metadata"), dict):
                containers.append(nested["metadata"])

    context_json = record.get("context_json")
    if isinstance(context_json, str):
        try:
            parsed = json.loads(context_json)
        except json.JSONDecodeError:
            parsed = None
        if isinstance(parsed, dict):
            containers.append(parsed)

    for container in containers:
        if not isinstance(container, dict):
            continue
        for key in keys:
            if key in container:
                return container[key]
    return None


def _truthy(value: Any) -> bool:
    if isinstance(value, str):
        return value.casefold() in {"1", "true", "yes", "y", "shown", "treatment"}
    return bool(value)


def _nullable_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


CohortStatusService = PurchasingCohortStatus
