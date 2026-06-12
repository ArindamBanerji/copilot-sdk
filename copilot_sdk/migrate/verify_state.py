"""Level 3 migration verification by replaying verified decision logs."""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from typing import Any, Mapping, cast

import numpy as np
import psycopg

from ci_platform.graph.agtype import normalize_agtype_value
from ci_platform.graph.age_client import AGEClient
from copilot_sdk.graph.protocol import GraphStore

_S = AGEClient.serialize_for_age

_DECISION_COLUMNS = (
    "decision_id",
    "domain",
    "category",
    "category_index",
    "factors_json",
    "factor_vector_json",
    "recommended_action",
    "recommended_index",
    "confidence",
    "probabilities_json",
    "status",
    "created_at",
    "actual_action",
    "actual_index",
    "is_correct",
    "verified_at",
    "context_json",
)


@dataclass
class ScorerState:
    """Snapshot of replay-derived learned state."""

    centroids: dict[tuple[int, int], list[float]]
    dk_weights: list[list[float]] | None
    conservation_V: int
    conservation_q: float
    conservation_alpha: float
    conservation_phase: str
    decision_count: int
    category_phases: dict[int, str] | None = None


@dataclass
class StateComparison:
    """Detailed comparison of two replay-derived scorer states."""

    passed: bool
    centroid_match: bool
    dk_match: bool
    conservation_match: bool
    decision_count_match: bool
    details: dict[str, Any]


class _ReplayGraphStore:
    """Minimal GraphStore surface needed by CompoundingScorer.learn()."""

    def __init__(self, domain: str) -> None:
        self.domain = domain
        self._decisions: dict[str, dict[str, Any]] = {}
        self._outcomes: dict[str, dict[str, Any]] = {}

    def load_latest_centroids(self, domain: str) -> None:
        _ = domain
        return None

    def add_decision(self, decision: dict[str, Any]) -> None:
        self._decisions[str(decision["decision_id"])] = dict(decision)

    def get_decision(self, decision_id: str) -> dict[str, Any] | None:
        decision = self._decisions.get(str(decision_id))
        return None if decision is None else dict(decision)

    def write_outcome(
        self,
        decision_id: str,
        actual_action: str,
        is_correct: bool,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        meta = dict(metadata or {})
        decision = self._decisions[str(decision_id)]
        self._outcomes[str(decision_id)] = {
            "decision_id": str(decision_id),
            "domain": self.domain,
            "actual_action": actual_action,
            "actual_index": int(meta.get("actual_index", 0)),
            "is_correct": bool(is_correct),
            "verified_at": float(meta.get("verified_at", 0.0)),
            "context": dict(meta.get("context") or {}),
        }
        decision["status"] = "confirmed" if is_correct else "overridden"

    def get_verified_decisions(self, domain: str) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for decision_id, outcome in self._outcomes.items():
            decision = dict(self._decisions[decision_id])
            decision.update(outcome)
            rows.append(decision)
        return sorted(
            [row for row in rows if str(row.get("domain")) == str(domain)],
            key=lambda row: (float(row.get("created_at") or 0.0), str(row.get("decision_id") or "")),
        )

    def count_verified(self, domain: str) -> int:
        return len(self.get_verified_decisions(domain))

    def count_verified_decisions(self, domain: str) -> int:
        return self.count_verified(domain)

    def count_decisions(self, domain: str) -> int:
        return sum(
            1
            for decision in self._decisions.values()
            if str(decision.get("domain")) == str(domain)
        )

    def archive_old_decisions(self, domain: str, keep_recent: int = 800) -> int:
        _ = domain, keep_recent
        return 0

    def count_correct(self, domain: str) -> int:
        return sum(
            1
            for row in self.get_verified_decisions(domain)
            if bool(row.get("is_correct"))
        )

    def save_centroids(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs

    def update_centroid(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs

    def record_judgment_conflict(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs


def _age_sql(graph_name: str, cypher: str, columns: str) -> str:
    return f"SELECT * FROM cypher({_S(graph_name)}, $$ {cypher} $$) AS ({columns})"


def _row_value(row: Any, key: str, index: int = 0) -> Any:
    if row is None:
        return None
    if isinstance(row, Mapping):
        return row.get(key)
    try:
        return row[key]
    except (TypeError, KeyError):
        return row[index]


def _json_value(value: Any, default: Any) -> Any:
    if value is None:
        return default
    if isinstance(value, str):
        return json.loads(value)
    return value


def _domain_from_preset_config(domain: str, preset_config: Any) -> str:
    if preset_config is None:
        return domain
    if isinstance(preset_config, str):
        return preset_config
    if isinstance(preset_config, Mapping):
        return str(preset_config.get("domain") or preset_config.get("name") or domain)
    return str(getattr(preset_config, "name", domain) or domain)


def _normalise_decision(
    decision: Mapping[str, Any],
    outcome: Mapping[str, Any] | None,
) -> tuple[dict[str, Any], str, dict[str, Any]]:
    factors = _json_value(decision.get("factors_json"), {})
    factor_vector = _json_value(decision.get("factor_vector_json"), [])
    probabilities = _json_value(decision.get("probabilities_json"), [])
    actual_action = (
        (outcome or {}).get("actual_action")
        or decision.get("actual_action")
    )
    if actual_action is None:
        raise ValueError(f"missing actual_action for decision {decision.get('decision_id')}")
    context = _json_value(
        (outcome or {}).get("context_json", decision.get("context_json")),
        {},
    )
    normalised = {
        "decision_id": str(decision["decision_id"]),
        "domain": str(decision.get("domain") or ""),
        "category": str(decision.get("category") or ""),
        "category_index": int(decision.get("category_index") or 0),
        "factors": factors,
        "factor_vector": [float(value) for value in factor_vector],
        "recommended_action": str(decision.get("recommended_action") or ""),
        "recommended_index": int(decision.get("recommended_index") or 0),
        "confidence": float(decision.get("confidence") or 0.0),
        "probabilities": [float(value) for value in probabilities],
        "status": str(decision.get("status") or "confirmed"),
        "created_at": float(decision.get("created_at") or 0.0),
    }
    return normalised, str(actual_action), dict(context or {})


def _empty_state(domain: str, preset_config: Any) -> ScorerState:
    from copilot_sdk.scoring.scorer import PRESET_REGISTRY

    resolved_domain = _domain_from_preset_config(domain, preset_config)
    preset = PRESET_REGISTRY[resolved_domain]()
    centroids = {
        (category_index, action_index): [0.0] * preset.shape.n_factors
        for category_index in range(preset.shape.n_categories)
        for action_index in range(preset.shape.n_actions)
    }
    return ScorerState(
        centroids=centroids,
        dk_weights=None,
        conservation_V=0,
        conservation_q=0.0,
        conservation_alpha=0.0,
        conservation_phase="EMPTY",
        decision_count=0,
        category_phases={
            category_index: "MEAN_CONVERGENCE"
            for category_index in range(preset.shape.n_categories)
        },
    )


def replay_decisions(
    decisions: list[dict[str, Any]],
    outcomes: dict[str, dict[str, Any]],
    domain: str,
    preset_config: Any = None,
) -> ScorerState:
    """Replay ordered decisions through a fresh CompoundingScorer."""
    if not decisions:
        return _empty_state(domain, preset_config)

    from copilot_sdk.scoring.scorer import PRESET_REGISTRY, CompoundingScorer

    resolved_domain = _domain_from_preset_config(domain, preset_config)
    preset = PRESET_REGISTRY[resolved_domain]()
    store = _ReplayGraphStore(resolved_domain)
    scorer = CompoundingScorer.from_preset(
        resolved_domain,
        graph_store=cast(GraphStore, store),
        enable_rl=False,
    )
    baseline = np.asarray(scorer.gae_scorer.centroids, dtype=np.float64).copy()

    ordered = sorted(
        decisions,
        key=lambda row: (float(row.get("created_at") or 0.0), str(row.get("decision_id") or "")),
    )
    for decision in ordered:
        decision_id = str(decision["decision_id"])
        normalised, actual_action, context = _normalise_decision(
            decision,
            outcomes.get(decision_id),
        )
        store.add_decision(normalised)
        scorer.learn(decision_id, actual_action, context=context)

    scorer.reestimate_dk_if_due()
    current = np.asarray(scorer.gae_scorer.centroids, dtype=np.float64)
    learned_delta = current - baseline
    centroids = {
        (category_index, action_index): learned_delta[category_index, action_index, :].copy().tolist()
        for category_index in range(learned_delta.shape[0])
        for action_index in range(learned_delta.shape[1])
    }
    verified_rows = store.get_verified_decisions(resolved_domain)
    verified = len(verified_rows)
    correct = sum(1 for row in verified_rows if bool(row.get("is_correct")))
    category_count = len({int(row.get("category_index") or 0) for row in verified_rows})
    total_categories = max(int(learned_delta.shape[0]), 1)
    q = correct / verified if verified else 0.0
    alpha = category_count / total_categories if verified else 0.0
    dk_weights = scorer.get_dk_weights()
    category_phases = {
        category_index: scorer.get_category_phase(category_name)
        for category_index, category_name in enumerate(preset.shape.category_names)
    }
    return ScorerState(
        centroids=centroids,
        dk_weights=dk_weights,
        conservation_V=verified,
        conservation_q=q,
        conservation_alpha=alpha,
        conservation_phase="ACTIVE" if verified else "EMPTY",
        decision_count=len(ordered),
        category_phases=category_phases,
    )


def _compare_centroids(
    left: dict[tuple[int, int], list[float]],
    right: dict[tuple[int, int], list[float]],
    atol: float,
) -> tuple[bool, list[dict[str, Any]]]:
    mismatches: list[dict[str, Any]] = []
    for key in sorted(set(left) | set(right)):
        left_vec = np.asarray(left.get(key, []), dtype=np.float64)
        right_vec = np.asarray(right.get(key, []), dtype=np.float64)
        if left_vec.shape != right_vec.shape or not np.allclose(left_vec, right_vec, atol=atol, rtol=0.0):
            max_abs_delta = None
            if left_vec.shape == right_vec.shape and left_vec.size:
                max_abs_delta = float(np.max(np.abs(left_vec - right_vec)))
            mismatches.append(
                {
                    "category_index": key[0],
                    "action_index": key[1],
                    "left_shape": tuple(left_vec.shape),
                    "right_shape": tuple(right_vec.shape),
                    "max_abs_delta": max_abs_delta,
                }
            )
    return not mismatches, mismatches


def _compare_dk(
    left: list[list[float]] | None,
    right: list[list[float]] | None,
    atol: float,
) -> tuple[bool, dict[str, Any]]:
    if left is None or right is None:
        return left is right, {"left_present": left is not None, "right_present": right is not None}
    left_arr = np.asarray(left, dtype=np.float64)
    right_arr = np.asarray(right, dtype=np.float64)
    if left_arr.shape != right_arr.shape:
        return False, {"left_shape": tuple(left_arr.shape), "right_shape": tuple(right_arr.shape)}
    if np.allclose(left_arr, right_arr, atol=atol, rtol=0.0):
        return True, {"shape": tuple(left_arr.shape)}
    return False, {
        "shape": tuple(left_arr.shape),
        "max_abs_delta": float(np.max(np.abs(left_arr - right_arr))),
    }


def compare_states(
    state_a: ScorerState,
    state_b: ScorerState,
    label_a: str = "sqlite",
    label_b: str = "age",
    centroid_atol: float = 1e-6,
    dk_atol: float = 1e-6,
    conservation_atol: float = 0.01,
) -> StateComparison:
    """Compare two replay-derived scorer states."""
    centroid_match, centroid_mismatches = _compare_centroids(
        state_a.centroids,
        state_b.centroids,
        centroid_atol,
    )
    dk_match, dk_details = _compare_dk(state_a.dk_weights, state_b.dk_weights, dk_atol)
    decision_count_match = state_a.decision_count == state_b.decision_count
    conservation_checks = {
        "V": state_a.conservation_V == state_b.conservation_V,
        "q": math.isclose(state_a.conservation_q, state_b.conservation_q, abs_tol=conservation_atol),
        "alpha": math.isclose(
            state_a.conservation_alpha,
            state_b.conservation_alpha,
            abs_tol=conservation_atol,
        ),
        "phase": state_a.conservation_phase == state_b.conservation_phase,
    }
    conservation_match = all(conservation_checks.values())
    product_a = state_a.conservation_alpha * state_a.conservation_q * state_a.conservation_V
    product_b = state_b.conservation_alpha * state_b.conservation_q * state_b.conservation_V
    details = {
        "labels": {"left": label_a, "right": label_b},
        "centroid_mismatches": centroid_mismatches,
        "dk": dk_details,
        "decision_count": {
            label_a: state_a.decision_count,
            label_b: state_b.decision_count,
            "match": decision_count_match,
        },
        "conservation": {
            "checks": conservation_checks,
            label_a: {
                "V": state_a.conservation_V,
                "q": state_a.conservation_q,
                "alpha": state_a.conservation_alpha,
                "product": product_a,
                "phase": state_a.conservation_phase,
            },
            label_b: {
                "V": state_b.conservation_V,
                "q": state_b.conservation_q,
                "alpha": state_b.conservation_alpha,
                "product": product_b,
                "phase": state_b.conservation_phase,
            },
            "conservation_product_a": product_a,
            "conservation_product_b": product_b,
        },
    }
    passed = centroid_match and dk_match and conservation_match and decision_count_match
    return StateComparison(
        passed=passed,
        centroid_match=centroid_match,
        dk_match=dk_match,
        conservation_match=conservation_match,
        decision_count_match=decision_count_match,
        details=details,
    )


def read_decisions_from_age(
    conn: psycopg.Connection,
    graph_name: str,
    domain: str,
) -> list[dict[str, Any]]:
    """Read migrated Decision nodes from AGE in path-sensitive order."""
    returns = ", ".join(f"d.{column} AS {column}" for column in _DECISION_COLUMNS)
    columns = ", ".join(f"{column} agtype" for column in _DECISION_COLUMNS)
    cypher = (
        f"MATCH (d:Decision {{domain: {_S(domain)}}}) "
        f"RETURN {returns} ORDER BY d.created_at ASC, d.decision_id ASC"
    )
    rows = conn.execute(_age_sql(graph_name, cypher, columns)).fetchall()
    decisions: list[dict[str, Any]] = []
    for row in rows:
        item = {
            column: normalize_agtype_value(_row_value(row, column, index))
            for index, column in enumerate(_DECISION_COLUMNS)
        }
        decisions.append({key: value for key, value in item.items() if value is not None})
    return decisions


def _outcomes_from_age_decisions(decisions: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    outcomes: dict[str, dict[str, Any]] = {}
    for decision in decisions:
        decision_id = str(decision.get("decision_id") or "")
        if not decision_id or "actual_action" not in decision:
            continue
        outcomes[decision_id] = {
            "decision_id": decision_id,
            "domain": decision.get("domain"),
            "actual_action": decision.get("actual_action"),
            "actual_index": decision.get("actual_index"),
            "is_correct": decision.get("is_correct"),
            "verified_at": decision.get("verified_at"),
            "context_json": decision.get("context_json", "{}"),
        }
    return outcomes


def verify_level3(
    source_db: str,
    conn: psycopg.Connection,
    graph_name: str,
    domain: str,
    preset_config: Any,
) -> dict[str, Any]:
    """Run Level 3 state-vector verification for SQLite vs AGE logs."""
    from copilot_sdk.migrate.sqlite_to_age import _read_outcomes, _read_verified_decisions

    sqlite_decisions = _read_verified_decisions(source_db)
    age_decisions = read_decisions_from_age(conn, graph_name, domain)
    if len(sqlite_decisions) != len(age_decisions):
        return {
            "passed": False,
            "comparison": {
                "reason": "decision_count_mismatch",
                "sqlite_count": len(sqlite_decisions),
                "age_count": len(age_decisions),
            },
        }

    sqlite_state = replay_decisions(
        sqlite_decisions,
        _read_outcomes(source_db),
        domain,
        preset_config,
    )
    age_state = replay_decisions(
        age_decisions,
        _outcomes_from_age_decisions(age_decisions),
        domain,
        preset_config,
    )
    comparison = compare_states(sqlite_state, age_state)
    return {
        "passed": comparison.passed,
        "comparison": {
            "centroid_match": comparison.centroid_match,
            "dk_match": comparison.dk_match,
            "conservation_match": comparison.conservation_match,
            "decision_count_match": comparison.decision_count_match,
            "details": comparison.details,
        },
    }
