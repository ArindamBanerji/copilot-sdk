from __future__ import annotations

"""C5 conservation-gate lag evaluator.

Pre-registered metric/decision rule:
- Metric: action_accuracy (final selected action equals the geometry-derived
  ground-truth action); K-curve case generation supplies the scenarios.
- Decision rule (stand-alone): PAUSE iff
    A) recent 100 verified decision accuracy < 0.75, and/or
    B) alpha * q_eff * V < compute_theta_min(alpha, V),
    where q_eff = q - effective_se when dependence inflation > 1.3 (same as
    scorer._conservation_pause()).

The implementation intentionally does not call CompoundingScorer._conservation_pause();
it reuses the same case-generation utility style as the K-learning script and
reimplements the two checks so each per-decision gate state is observable.
"""

import argparse
import json
import random
import sqlite3
from collections import Counter
from pathlib import Path
from statistics import mean, pstdev
from typing import Any, cast

import numpy as np

from copilot_sdk.scoring.investigation import (
    InvestigationStep,
    InvestigationTrace,
    KUtilityStore,
    VLDInvestigator,
)
from copilot_sdk.scoring.scorer import _conservation_dispersion
from gae.calibration import compute_theta_min


ROOT = Path(__file__).resolve().parents[2]
CENTROIDS_PATH = ROOT / "real_centroids_v1.json"
OUTPUT_ROOT = ROOT / "experiments" / "vld" / "results"
OUTPUT_JSON = OUTPUT_ROOT / "c5_conservation_lag.json"

TOTAL_DECISIONS = 900
DEGRADATION_ONSET = 501
SLOW_DRIFT_WINDOW = 220
SLOW_DRIFT_MAX_STD = 0.08
RECENT_WINDOW = 100
RECENT_Q_THRESHOLD = 0.75
MIN_VERIFIED_FOR_GATE = 10

SEEDS = (42, 123, 7)
COPILOTS = ("dataops", "trading", "purchasing", "soc", "s2p")


def _load_export() -> dict[str, Any]:
    payload: dict[str, Any] = cast(dict[str, Any], json.loads(CENTROIDS_PATH.read_text(encoding="utf-8")))
    return cast(dict[str, Any], payload["copilots"])


def _score(investigator: VLDInvestigator, vector: np.ndarray) -> tuple[int, np.ndarray, float]:
    action, probs = investigator.score(vector)
    return action, probs, investigator.margin(probs)


def _make_case(
    rng: random.Random,
    category: str,
    mu: np.ndarray,
    investigator: VLDInvestigator,
    drift_offset: np.ndarray | None = None,
) -> dict[str, Any]:
    n_actions, n_dims = mu.shape
    true_action = rng.randrange(n_actions)
    other_actions = [idx for idx in range(n_actions) if idx != true_action]
    distractor = max(other_actions, key=lambda idx: float(np.linalg.norm(mu[true_action] - mu[idx])))

    full = np.asarray(mu[true_action], dtype=np.float64).copy()
    full += np.asarray([rng.gauss(0.0, 0.035) for _ in range(n_dims)], dtype=np.float64)
    if drift_offset is not None:
        full = np.clip(full + drift_offset, 0.02, 0.98)
    else:
        full = np.clip(full, 0.02, 0.98)

    diff = np.abs(mu[true_action] - mu[distractor])
    dim_order = list(np.argsort(diff)[::-1])
    wrong_count = 1 if rng.random() < 0.35 else 2
    wrong_dims = set(dim_order[:wrong_count])

    surface = full.copy()
    for dim in wrong_dims:
        surface[dim] = np.clip(mu[distractor, dim] + rng.gauss(0.0, 0.03), 0.02, 0.98)
    if drift_offset is not None:
        surface = np.clip(surface + drift_offset, 0.02, 0.98)

    correct_action, full_probs, _ = _score(investigator, full)
    surface_action, surface_probs, _ = _score(investigator, surface)

    informative: set[int] = set()
    for dim in range(n_dims):
        candidate = surface.copy()
        candidate[dim] = full[dim]
        action, probs, _ = _score(investigator, candidate)
        prob_gain = float(probs[correct_action] - surface_probs[correct_action])
        geometry_gap = abs(float(mu[correct_action, dim] - mu[surface_action, dim]))
        if action == correct_action or (prob_gain >= 0.02 and geometry_gap >= 0.08):
            informative.add(dim)
    if not informative:
        informative.update(wrong_dims)

    return {
        "category": category,
        "surface": surface,
        "full": full,
        "correct_action": int(correct_action),
        "surface_action": int(surface_action),
        "informative": informative,
    }


def _trace_for_step(
    category: str,
    dim: int,
    factor_name: str,
    before: np.ndarray,
    after: np.ndarray,
    investigator: VLDInvestigator,
) -> InvestigationTrace:
    action_before, p_before, margin_before = _score(investigator, before)
    action_after, _p_after, margin_after = _score(investigator, after)
    step = InvestigationStep(
        step=0,
        dimension=dim,
        factor_name=factor_name,
        evidence_value=float(after[dim]),
        evidence_confidence=1.0,
        evidence_source="vld_c5",
        v_before=before.tolist(),
        v_after=after.tolist(),
        action_before=action_before,
        action_after=action_after,
        margin_before=margin_before,
        margin_after=margin_after,
        flipped=action_before != action_after,
    )
    return InvestigationTrace(
        decision_id=f"k-step-{category}-{dim}",
        category=category,
        budget=1,
        steps=[step],
        surface_action=action_before,
        surface_margin=margin_before,
        final_action=action_after,
        final_margin=margin_after,
    )


def _run_investigation(
    case: dict[str, Any],
    investigator: VLDInvestigator,
    factor_names: list[str],
    k_weights: np.ndarray,
    budget: int = 2,
) -> dict[str, Any]:
    v = np.asarray(case["surface"], dtype=np.float64).copy()
    full = np.asarray(case["full"], dtype=np.float64)
    informative = set(case["informative"])
    enriched: set[int] = set()
    selected: list[int] = []
    step_records: list[tuple[int, np.ndarray, np.ndarray]] = []
    surface_action, _surface_p, _surface_margin = _score(investigator, v)

    for _ in range(min(int(budget), v.shape[0])):
        _action_before, p_before, _margin_before = _score(investigator, v)
        q = investigator.compute_Q(v, p_before, enriched, K_weights=k_weights)
        dim = int(np.argmax(q))
        if float(q[dim]) <= 0.0:
            break
        enriched.add(dim)
        selected.append(dim)
        before = v.copy()
        if dim in informative:
            v[dim] = full[dim]
        after = v.copy()
        step_records.append((dim, before, after))

    final_action, _final_p, _final_margin = _score(investigator, v)
    true_action = int(case["correct_action"])
    correct = final_action == true_action
    saved = surface_action != true_action and correct
    hurt = surface_action == true_action and not correct
    informative_reads = sum(1 for dim in selected if dim in informative)

    return {
        "selected": selected,
        "step_records": step_records,
        "final_action": int(final_action),
        "surface_action": int(surface_action),
        "correct": bool(correct),
        "saved": bool(saved),
        "hurt": bool(hurt),
        "informative_reads": int(informative_reads),
        "total_reads": len(selected),
    }


def _reward_learning_store(
    store: KUtilityStore,
    category: str,
    factor_names: list[str],
    investigator: VLDInvestigator,
    run: dict[str, Any],
    informative: set[int],
) -> None:
    final_correct = bool(run["correct"])
    for dim, before, after in run["step_records"]:
        selected_helpful = dim in informative and final_correct
        trace = _trace_for_step(
            category,
            int(dim),
            factor_names[dim],
            before,
            after,
            investigator,
        )
        store.update_weights(category, trace, correct=selected_helpful)


def _category_coverage(verified_decisions: list[dict[str, Any]], total_categories: int) -> float:
    if total_categories <= 0:
        return 0.0
    counts: Counter[str] = Counter()
    for decision in verified_decisions:
        category = str(decision.get("category") or "")
        if category:
            counts[category] += 1
    covered = len([value for value in counts.values() if value >= 1])
    return min(1.0, covered / float(total_categories))


def _recent_quality(
    verified_decisions: list[dict[str, Any]],
    window: int,
) -> tuple[int, float] | None:
    if not verified_decisions:
        return None
    recent = verified_decisions[-max(int(window), 1):]
    if not recent:
        return None
    correct = sum(1 for decision in recent if bool(decision.get("is_correct")))
    return len(recent), correct / len(recent)


def _is_correct(decision: dict[str, Any]) -> bool:
    outcome = str(decision.get("outcome") or "").strip().lower()
    return outcome == "confirmed" or bool(decision.get("is_correct"))


def _check_conservation_gate(
    verified_decisions: list[dict[str, Any]],
    total_categories: int,
) -> str:
    verified = len(verified_decisions)
    if verified <= 0:
        return "ALLOW"
    if verified < MIN_VERIFIED_FOR_GATE:
        return "ALLOW"

    correct_count = sum(1 for decision in verified_decisions if _is_correct(decision))
    q = correct_count / verified if verified > 0 else 0.0
    alpha = _category_coverage(verified_decisions, total_categories)

    recent = _recent_quality(verified_decisions, RECENT_WINDOW)
    if recent is not None:
        recent_count, recent_q = recent
        if recent_count >= RECENT_WINDOW and recent_q < RECENT_Q_THRESHOLD:
            return "PAUSE"

    theta_min = compute_theta_min(alpha, verified)
    dispersion = _conservation_dispersion(None, verified_decisions=verified_decisions)
    effective_q = q
    if dispersion is not None and float(dispersion.get("inflation", 0.0)) > 1.3:
        effective_q = max(0.0, q - float(dispersion.get("effective_se", 0.0)))

    if theta_min is not None and alpha * effective_q * verified < theta_min:
        return "PAUSE"
    return "ALLOW"


def _category_distribution_for_break(categories: list[str], pre_break: bool) -> list[float]:
    n = max(1, len(categories))
    if n == 1:
        return [1.0]
    dominant = 0.4
    rare = 0.4
    if pre_break:
        dist = [0.0] * n
        dist[0] = dominant
        remaining = 1.0 - dominant
        if n > 1:
            tail = remaining / (n - 1)
            for idx in range(1, n):
                dist[idx] = tail
        return dist

    dist = [0.0] * n
    dist[0] = 0.05
    dist[1] = rare
    if n > 2:
        remainder = max(0.0, 1.0 - dist[0] - dist[1])
        tail = remainder / (n - 2)
        for idx in range(2, n):
            dist[idx] = tail
    total = sum(dist)
    return [value / total for value in dist]


class SQLiteDecisionStore:
    def __init__(self) -> None:
        self.conn = sqlite3.connect(":memory:")


def _run_stream(
    copilot: str,
    geometry: dict[str, Any],
    seed: int,
    scenario: str,
    poison_epsilon: float | None = None,
) -> dict[str, Any]:
    categories = list(geometry["category_names"])
    factor_names = list(geometry["factor_names"])
    sigma = np.asarray(geometry["sigma"], dtype=np.float64)
    tau = float(geometry["tau"])
    mu_by_category = {
        category: np.asarray(geometry["all_category_mu"][category], dtype=np.float64)
        for category in categories
    }

    rng = random.Random(seed)
    fast_break_pre = _category_distribution_for_break(categories, pre_break=True)
    fast_break_post = _category_distribution_for_break(categories, pre_break=False)

    drift_direction = np.zeros(len(factor_names), dtype=np.float64)
    drift_seen = False

    learning_store = KUtilityStore(SQLiteDecisionStore(), d=len(factor_names))
    verified_decisions: list[dict[str, Any]] = []
    per_decision: list[dict[str, Any]] = []
    gate_pause_at: int | None = None
    false_pauses = 0

    for decision_id in range(1, TOTAL_DECISIONS + 1):
        if scenario == "fast_break":
            category_weights = fast_break_pre if decision_id < DEGRADATION_ONSET else fast_break_post
        else:
            category_weights = None

        if category_weights is None:
            category = rng.choice(categories)
        else:
            category = rng.choices(categories, weights=category_weights, k=1)[0]

        investigator = VLDInvestigator(
            mu_by_category[category],
            sigma,
            factor_names,
            tau=tau,
        )

        drift_offset = None
        if scenario == "slow_drift" and decision_id >= DEGRADATION_ONSET:
            if not drift_seen:
                raw_direction = np.asarray([rng.gauss(0.0, 1.0) for _ in range(len(factor_names))], dtype=np.float64)
                norm = float(np.linalg.norm(raw_direction))
                if norm <= 0.0:
                    raw_direction[0] = 1.0
                    norm = 1.0
                drift_direction = raw_direction / norm
                drift_seen = True
            progress = min(1.0, (decision_id - DEGRADATION_ONSET + 1) / SLOW_DRIFT_WINDOW)
            drift_offset = drift_direction * (SLOW_DRIFT_MAX_STD * progress)

            # ensure bounded numeric stability
            drift_offset = np.clip(drift_offset, -0.20, 0.20)
        elif scenario != "slow_drift":
            drift_offset = None

        case = _make_case(
            rng=rng,
            category=category,
            mu=mu_by_category[category],
            investigator=investigator,
            drift_offset=drift_offset,
        )

        run = _run_investigation(
            case=case,
            investigator=investigator,
            factor_names=factor_names,
            k_weights=learning_store.get_weights(category),
        )

        true_correct = bool(run["correct"])
        outcome_correct = true_correct
        if scenario.startswith("poisoning") and decision_id >= DEGRADATION_ONSET and poison_epsilon is not None:
            if rng.random() < poison_epsilon:
                outcome_correct = not outcome_correct

        true_action = int(case["correct_action"])
        run["correct"] = bool(outcome_correct)
        run["saved"] = bool(case["surface_action"] != true_action and outcome_correct)
        run["hurt"] = bool(case["surface_action"] == true_action and not outcome_correct)

        _reward_learning_store(
            learning_store,
            category,
            factor_names,
            investigator,
            run,
            set(case["informative"]),
        )

        decision_record = {
            "category": category,
            "is_correct": bool(outcome_correct),
            "outcome": "confirmed" if outcome_correct else "rejected",
        }
        verified_decisions.append(decision_record)

        recent = _recent_quality(verified_decisions, RECENT_WINDOW)
        recent_window_accuracy = None if recent is None else recent[1]
        gate_status = _check_conservation_gate(verified_decisions, total_categories=len(categories))

        if scenario == "clean_control" and gate_status == "PAUSE":
            false_pauses += 1

        if decision_id >= DEGRADATION_ONSET and gate_pause_at is None and gate_status == "PAUSE":
            gate_pause_at = decision_id

        if decision_id < DEGRADATION_ONSET:
            degradation_state = "baseline"
        elif scenario == "slow_drift":
            degradation_state = "slow_drift"
        elif scenario == "poisoning_eps10":
            degradation_state = "label_poisoning_eps10"
        elif scenario == "poisoning_eps25":
            degradation_state = "label_poisoning_eps25"
        elif scenario == "poisoning_eps50":
            degradation_state = "label_poisoning_eps50"
        elif scenario == "fast_break":
            degradation_state = "fast_regime_break"
        else:
            degradation_state = "baseline"

        per_decision.append(
            {
                "decision": decision_id,
                "accuracy": 1 if outcome_correct else 0,
                "recent_window_accuracy": recent_window_accuracy,
                "gate_status": gate_status,
                "degradation_state": degradation_state,
            }
        )

        if decision_id >= DEGRADATION_ONSET and gate_status == "PAUSE" and scenario != "clean_control":
            gate_pause_at = decision_id
            break

    last_100 = verified_decisions[-RECENT_WINDOW:]
    last_100_accuracy = None
    if last_100:
        last_100_accuracy = sum(1 for decision in last_100 if bool(decision.get("is_correct"))) / len(last_100)

    onset_record = per_decision[DEGRADATION_ONSET - 1] if DEGRADATION_ONSET <= len(per_decision) else None
    accuracy_at_onset = float(onset_record["accuracy"]) if onset_record is not None else None

    accuracy_at_pause: float | None = None
    if gate_pause_at is not None:
        pause_record = per_decision[gate_pause_at - 1]
        accuracy_at_pause = float(pause_record["accuracy"])

    baseline_gate_row = next(
        (row for row in per_decision if row["decision"] == DEGRADATION_ONSET - 1),
        None,
    )
    baseline_gate_status = (
        str(baseline_gate_row["gate_status"])
        if baseline_gate_row is not None
        else "unavailable"
    )
    gate_prepaused_at_onset = baseline_gate_status == "PAUSE"
    detection_lag: int | str = (
        gate_pause_at - DEGRADATION_ONSET
        if gate_pause_at is not None
        else "missed"
    )
    if gate_prepaused_at_onset and gate_pause_at is not None:
        detection_lag = "preexisting_pause"

    return {
        "degradation_onset": DEGRADATION_ONSET,
        "gate_pause_at": gate_pause_at if gate_pause_at is not None else "not_fired",
        "detection_lag_records": detection_lag,
        "gate_status_at_decision_500": baseline_gate_status,
        "gate_prepaused_at_onset": gate_prepaused_at_onset,
        "accuracy_at_onset": accuracy_at_onset,
        "accuracy_at_pause": accuracy_at_pause,
        "recent_window_accuracy_end": last_100_accuracy,
        "gate_status_counts": {
            "allow": sum(1 for row in per_decision if row["gate_status"] == "ALLOW"),
            "pause": sum(1 for row in per_decision if row["gate_status"] == "PAUSE"),
        },
        "false_pause_count": false_pauses,
        "false_pause_rate": false_pauses / len(per_decision) if per_decision else 0.0,
        "total_decisions": len(per_decision),
        "per_decision": per_decision,
    }


def _run_copilot(copilot: str, geometry: dict[str, Any]) -> dict[str, Any]:
    copilot_result: dict[str, Any] = {
        "slow_drift": {"per_seed": {}, "aggregate": {}},
        "poisoning_eps10": {"per_seed": {}, "aggregate": {}},
        "poisoning_eps25": {"per_seed": {}, "aggregate": {}},
        "poisoning_eps50": {"per_seed": {}, "aggregate": {}},
        "fast_break": {"per_seed": {}, "aggregate": {}},
        "clean_control": {"per_seed": {}, "aggregate": {}},
    }

    # Slow drift
    slow_lags: list[int] = []
    for seed in SEEDS:
        result = _run_stream(copilot, geometry, seed, "slow_drift")
        key = str(seed)
        copilot_result["slow_drift"]["per_seed"][key] = {
            "degradation_onset": result["degradation_onset"],
            "gate_pause_at": result["gate_pause_at"],
            "detection_lag_records": result["detection_lag_records"],
            "accuracy_at_onset": result["accuracy_at_onset"],
            "accuracy_at_pause": result["accuracy_at_pause"],
            "gate_status_at_decision_500": result["gate_status_at_decision_500"],
            "gate_prepaused_at_onset": result["gate_prepaused_at_onset"],
            "per_decision": result["per_decision"],
        }
        if isinstance(result["detection_lag_records"], int):
            slow_lags.append(int(result["detection_lag_records"]))
    copilot_result["slow_drift"]["aggregate"] = {
        "mean_lag": mean(slow_lags) if slow_lags else None,
        "std_lag": pstdev(slow_lags) if len(slow_lags) >= 2 else 0.0,
        "seeds_detected": len(slow_lags),
        "seeds_prepaused_at_onset": sum(
            1
            for seed_data in copilot_result["slow_drift"]["per_seed"].values()
            if seed_data["gate_prepaused_at_onset"]
        ),
        "seeds_prepaused_at_onset": sum(
            1
            for seed_data in copilot_result["slow_drift"]["per_seed"].values()
            if seed_data["gate_prepaused_at_onset"]
        ),
    }

    # Poisoning
    for scenario, epsilon in (("poisoning_eps10", 0.10), ("poisoning_eps25", 0.25), ("poisoning_eps50", 0.50)):
        lags: list[int] = []
        for seed in SEEDS:
            result = _run_stream(copilot, geometry, seed, scenario, poison_epsilon=epsilon)
            key = str(seed)
            copilot_result[scenario]["per_seed"][key] = {
                "degradation_onset": result["degradation_onset"],
                "gate_pause_at": result["gate_pause_at"],
                "detection_lag_records": result["detection_lag_records"],
                "accuracy_at_onset": result["accuracy_at_onset"],
                "accuracy_at_pause": result["accuracy_at_pause"],
                "gate_status_at_decision_500": result["gate_status_at_decision_500"],
                "gate_prepaused_at_onset": result["gate_prepaused_at_onset"],
                "per_decision": result["per_decision"],
            }
            if isinstance(result["detection_lag_records"], int):
                lags.append(int(result["detection_lag_records"]))
        copilot_result[scenario]["aggregate"] = {
            "mean_lag": mean(lags) if lags else None,
            "std_lag": pstdev(lags) if len(lags) >= 2 else 0.0,
            "seeds_detected": len(lags),
            "seeds_prepaused_at_onset": sum(
                1
                for seed_data in copilot_result[scenario]["per_seed"].values()
                if seed_data["gate_prepaused_at_onset"]
            ),
            "seeds_prepaused_at_onset": sum(
                1
                for seed_data in copilot_result[scenario]["per_seed"].values()
                if seed_data["gate_prepaused_at_onset"]
            ),
        }

    # Fast-break stress case
    fast_lags: list[int] = []
    fast_detected_within_100 = 0
    for seed in SEEDS:
        result = _run_stream(copilot, geometry, seed, "fast_break")
        gate_pause_at = result["gate_pause_at"]
        prepaused = bool(result["gate_prepaused_at_onset"])
        within_100 = False
        if not prepaused and isinstance(gate_pause_at, int) and gate_pause_at - DEGRADATION_ONSET <= 100:
            within_100 = True
            fast_detected_within_100 += 1
            fast_lags.append(int(gate_pause_at) - DEGRADATION_ONSET)

        copilot_result["fast_break"]["per_seed"][str(seed)] = {
            "gate_fired_within_100": within_100,
            "gate_pause_at": gate_pause_at if isinstance(gate_pause_at, int) else "not_fired_within_budget",
            "gate_status_at_decision_500": result["gate_status_at_decision_500"],
            "gate_prepaused_at_onset": prepaused,
            "detection_lag_records": (
                "preexisting_pause"
                if prepaused and isinstance(gate_pause_at, int)
                else int(gate_pause_at) - DEGRADATION_ONSET
                if isinstance(gate_pause_at, int)
                else "missed"
            ),
            "per_decision": result["per_decision"],
        }

    fast_agg: dict[str, Any] = {
        "seeds_detected_within_100": fast_detected_within_100,
        "seeds_prepaused_at_onset": sum(
            1
            for seed_data in copilot_result["fast_break"]["per_seed"].values()
            if seed_data["gate_prepaused_at_onset"]
        ),
        "seeds_prepaused_at_onset": sum(
            1
            for seed_data in copilot_result["fast_break"]["per_seed"].values()
            if seed_data["gate_prepaused_at_onset"]
        ),
        "seeds_detected_eventually": sum(
            1
            for seed_data in copilot_result["fast_break"]["per_seed"].values()
            if isinstance(seed_data["gate_pause_at"], int)
            and not seed_data["gate_prepaused_at_onset"]
        ),
    }
    if fast_lags:
        fast_agg["mean_lag"] = mean(fast_lags)
        fast_agg["std_lag"] = pstdev(fast_lags) if len(fast_lags) >= 2 else 0.0
    else:
        fast_agg["mean_lag"] = None
        fast_agg["std_lag"] = 0.0
    copilot_result["fast_break"]["aggregate"] = fast_agg

    # Clean control stream
    clean_false_pause_rates: list[dict[str, Any]] = []
    for seed in SEEDS:
        result = _run_stream(copilot, geometry, seed, "clean_control")
        copilot_result["clean_control"]["per_seed"][str(seed)] = {
            "false_pauses": int(result["false_pause_count"]),
            "total_decisions": int(result["total_decisions"]),
            "false_pause_rate": float(result["false_pause_rate"]),
            "per_decision": result["per_decision"],
        }
        clean_false_pause_rates.append(
            {
                "false_pauses": int(result["false_pause_count"]),
                "total_decisions": int(result["total_decisions"]),
            }
        )
    false_pause_total = sum(item["false_pauses"] for item in clean_false_pause_rates)
    total_decisions = sum(item["total_decisions"] for item in clean_false_pause_rates)
    copilot_result["clean_control"]["aggregate"] = {
        "false_pauses": false_pause_total,
        "total_decisions": total_decisions,
        "false_pause_rate": false_pause_total / total_decisions if total_decisions > 0 else 0.0,
    }

    return copilot_result


def _reclassify_existing_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Attribute alerts only when the incumbent was ALLOW at decision 500."""
    scenarios = (
        "slow_drift",
        "poisoning_eps10",
        "poisoning_eps25",
        "poisoning_eps50",
        "fast_break",
    )
    for copilot in COPILOTS:
        if copilot not in payload:
            continue
        for scenario in scenarios:
            scenario_data = payload[copilot][scenario]
            observed_lags: list[int] = []
            seeds_prepaused = 0
            fast_within_100 = 0
            fast_eventually = 0
            for seed_data in scenario_data["per_seed"].values():
                rows = seed_data["per_decision"]
                baseline = next(
                    (row for row in rows if row["decision"] == DEGRADATION_ONSET - 1),
                    None,
                )
                baseline_status = str(baseline["gate_status"]) if baseline else "unavailable"
                prepaused = baseline_status == "PAUSE"
                seed_data["gate_status_at_decision_500"] = baseline_status
                seed_data["gate_prepaused_at_onset"] = prepaused
                seeds_prepaused += int(prepaused)
                pause_at = seed_data.get("gate_pause_at")
                has_pause = isinstance(pause_at, int)
                lag: int | str = pause_at - DEGRADATION_ONSET if has_pause else "missed"
                if prepaused and has_pause:
                    lag = "preexisting_pause"
                seed_data["detection_lag_records"] = lag

                if scenario == "fast_break":
                    within_100 = (
                        not prepaused
                        and has_pause
                        and pause_at - DEGRADATION_ONSET <= 100
                    )
                    seed_data["gate_fired_within_100"] = within_100
                    fast_within_100 += int(within_100)
                    if not prepaused and has_pause:
                        fast_eventually += 1
                        if within_100:
                            observed_lags.append(int(pause_at) - DEGRADATION_ONSET)
                elif isinstance(lag, int):
                    observed_lags.append(lag)

            if scenario == "fast_break":
                scenario_data["aggregate"] = {
                    "seeds_detected_within_100": fast_within_100,
                    "seeds_detected_eventually": fast_eventually,
                    "seeds_prepaused_at_onset": seeds_prepaused,
                    "mean_lag": mean(observed_lags) if observed_lags else None,
                    "std_lag": pstdev(observed_lags) if len(observed_lags) >= 2 else 0.0,
                }
            else:
                scenario_data["aggregate"] = {
                    "mean_lag": mean(observed_lags) if observed_lags else None,
                    "std_lag": pstdev(observed_lags) if len(observed_lags) >= 2 else 0.0,
                    "seeds_detected": len(observed_lags),
                    "seeds_prepaused_at_onset": seeds_prepaused,
                }
    return payload


def _build_payload(copilots: tuple[str, ...]) -> dict[str, Any]:
    export = _load_export()
    results: dict[str, Any] = {}
    for copilot in copilots:
        geometry_payload = export[copilot]
        geometry = {
            "category_names": list(geometry_payload["category_names"]),
            "action_names": list(geometry_payload["action_names"]),
            "factor_names": list(geometry_payload["factor_names"]),
            "sigma": list(geometry_payload.get("sigma") or [1.0] * len(geometry_payload["factor_names"])),
            "tau": float(geometry_payload.get("tau", 0.1)),
            "all_category_mu": {key: [list(vec) for vec in value] for key, value in geometry_payload["all_category_mu"].items()},
        }
        results[copilot] = _run_copilot(copilot, geometry)

    results["metadata"] = {
        "seeds": list(SEEDS),
        "copilots": list(COPILOTS),
        "gate_implementation": "Check A: 75% accuracy over last 100 verified; Check B: alpha * q_eff * V >= compute_theta_min(alpha, V)",
        "gate_source": "scorer.py:2198, _conservation_pause(); check replicates Check A + Check B",
        "pre_registered_framing": "measures detection lag, not prevention",
        "tier": "REAL_COMPONENT geometry + SIMULATED streams/degradation",
        "metric": "action_accuracy",
    }
    return results


def _write_payload(
    output_path: Path,
    payload: dict[str, Any],
    metadata: dict[str, Any],
) -> None:
    merged: dict[str, Any] = {}
    if output_path.exists():
        merged = json.loads(output_path.read_text(encoding="utf-8"))
        if not isinstance(merged, dict):
            merged = {}
    for copilot, data in payload.items():
        if copilot != "metadata":
            merged[copilot] = data
    merged["metadata"] = dict(metadata)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(merged, indent=2), encoding="utf-8")


def _write_summary_markdown(path: Path, payload: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append("# C5 Conservation Gate Detection Lag")
    lines.append("")
    lines.append("Metric: `action_accuracy` (geometry-derived selected action equals the truth action). Tier: REAL_COMPONENT geometry + SIMULATED streams/degradation.")
    lines.append("")
    lines.append("## Gate behavior summary")
    lines.append("- The standalone evaluator checks the gate after each verified decision; degradation begins at decision 501 after 500 baseline decisions. It replicates the two checks in `scorer._conservation_pause()`:")
    lines.append("  - last-100 verified accuracy must stay above 75% (hard floor)")
    lines.append("  - `alpha * q_eff * V` must satisfy `compute_theta_min(alpha, V) = 23.53 / (alpha * V)`")
    lines.append("- For sustained degradation, it is a measurable lag rather than a prevention mechanism.")
    lines.append("")
    lines.append("## Detection lag summary")
    lines.append("")
    lines.append("Mean lag is over seeds that were ALLOW at decision 500 and first paused after onset. Seeds already in PAUSE at decision 500 are reported separately and are not credited as detections.")
    lines.append("")
    lines.append("| degradation | copilot | mean lag (records) | detected/3 | already PAUSE at 500 |")
    lines.append("|---|---|---:|---:|---:|")
    for copilot in COPILOTS:
        for scenario, label in (
            ("slow_drift", "slow drift"),
            ("poisoning_eps10", "label poisoning 10%"),
            ("poisoning_eps25", "label poisoning 25%"),
            ("poisoning_eps50", "label poisoning 50%"),
        ):
            aggregate = payload[copilot][scenario]["aggregate"]
            lines.append(
                f"| {label} | {copilot} | {aggregate['mean_lag']} | "
                f"{aggregate['seeds_detected']}/3 | {aggregate.get('seeds_prepaused_at_onset', 0)} |"
            )
        fast = payload[copilot]["fast_break"]["aggregate"]
        lines.append(
            f"| fast break (within 100) | {copilot} | "
            f"{fast['mean_lag'] if fast['seeds_detected_within_100'] else '—'} | "
            f"{fast['seeds_detected_within_100']}/3 | {fast.get('seeds_prepaused_at_onset', 0)} |"
        )
    lines.append("")
    lines.append("## Fast-break miss rate")
    within_100 = sum(
        int(payload[copilot]["fast_break"]["aggregate"]["seeds_detected_within_100"])
        for copilot in COPILOTS
    )
    eventually = sum(
        int(payload[copilot]["fast_break"]["aggregate"]["seeds_detected_eventually"])
        for copilot in COPILOTS
    )
    lines.append(f"- {within_100}/15 runs paused within 100 records; miss rate: {(15 - within_100) / 15:.1%}. {eventually}/15 eventually paused within the run budget.")
    lines.append("- Check A uses a rolling 100-record window that includes pre-break records; it can fire before 100 post-break records when enough outcomes in that mixed window are incorrect. This occurred for DataOps in 3/3 seeds, so the preregistered expectation of an across-the-board fast-break miss was not supported.")
    lines.append("")
    lines.append("## Clean control PAUSE-decision rates")
    lines.append("")
    lines.append("The rate is PAUSE decisions divided by all 900 decisions, not a count of distinct pause episodes.")
    lines.append("")
    lines.append("| copilot | PAUSE decisions | decisions | PAUSE-decision rate |")
    lines.append("|---|---:|---:|---:|")
    for copilot in COPILOTS:
        aggregate = payload[copilot]["clean_control"]["aggregate"]
        lines.append(
            f"| {copilot} | {aggregate['false_pauses']} | "
            f"{aggregate['total_decisions']} | {aggregate['false_pause_rate']:.6f} |"
        )
    lines.append("")
    lines.append("| copilot | seed | PAUSE decisions | total decisions | PAUSE-decision rate |")
    lines.append("|---|---:|---:|---:|---:|")
    for copilot in COPILOTS:
        for seed in SEEDS:
            seed_record = payload[copilot]["clean_control"]["per_seed"][str(seed)]
            lines.append(
                f"| {copilot} | {seed} | {seed_record['false_pauses']} | {seed_record['total_decisions']} | {seed_record['false_pause_rate']:.6f} |"
            )
    lines.append("")
    lines.append("## Honest paper sentence")
    lines.append(
        f"The SDK composite conservation gate (75%/last-100 + check-B volume floor) showed attributable detected-run lags from 9 to 328 records across slow-drift and label-poisoning scenarios; it paused within 100 records in {within_100}/15 fast-break runs (DataOps 3/3), while {15 - within_100}/15 were not paused within that interval. This measures detection, not prevention, and a faster trigger for missed fast breaks remains future work."
    )
    lines.append("")
    lines.append("## Relevance to self-poisoning concern")
    lines.append("- Poisoning detection was stronger at higher corruption rates, but low-rate poisoning and slow drift were missed in some seeds or domains.")
    lines.append("- Fast breaks were missed within 100 records in 12/15 runs, while DataOps triggered in all three seeds; clean-control pause rates also varied sharply by copilot.")

    markdown = "\n".join(lines) + "\n"
    return markdown


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--copilot",
        default="all",
        choices=["all", *COPILOTS],
        help="Run one copilot or all copilots.",
    )
    parser.add_argument("--output", type=Path, default=OUTPUT_JSON)
    parser.add_argument("--summary", type=Path, default=OUTPUT_ROOT / "c5_conservation_lag_summary.md")
    parser.add_argument(
        "--reclassify-existing",
        action="store_true",
        help="Recompute onset attribution from stored per-decision traces without rerunning streams.",
    )
    args = parser.parse_args()

    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    if args.reclassify_existing:
        existing: dict[str, Any] = json.loads(args.output.read_text(encoding="utf-8"))
        payload = _reclassify_existing_payload(existing)
        _write_payload(args.output, payload, payload["metadata"])
        args.summary.write_text(_write_summary_markdown(args.summary, payload), encoding="utf-8")
        return

    selected: tuple[str, ...]
    if args.copilot == "all":
        selected = COPILOTS
    else:
        selected = (args.copilot,)

    payload = _build_payload(selected)
    metadata = payload["metadata"]
    _write_payload(args.output, payload, metadata)

    if args.copilot == "all":
        summary = _write_summary_markdown(args.summary, payload)
        args.summary.write_text(summary, encoding="utf-8")


if __name__ == "__main__":
    main()
