"""Shadow scorer discipline for SQLite-to-AGE backend validation.

This utility is intentionally not wired into app routers. It compares a
canonical primary scorer with a shadow scorer and always returns the primary
result.
"""

from __future__ import annotations

import logging
import math
from dataclasses import asdict, dataclass, field
from typing import Any

import numpy as np

from copilot_sdk.migrate.verify_state import ScorerState, compare_states
from copilot_sdk.scoring.scorer import PRESET_REGISTRY, CompoundingScorer

logger = logging.getLogger(__name__)

_MAX_MISMATCHES = 100


@dataclass
class ComparisonResult:
    """Field-by-field comparison result for a shadow operation."""

    matched: bool
    field_results: dict[str, dict[str, Any]]
    decision_id: str | None = None


@dataclass
class ShadowStatus:
    """Current shadow validation status."""

    total_comparisons: int = 0
    consecutive_matches: int = 0
    mismatches: list[dict[str, Any]] = field(default_factory=list)
    status: str = "validating"
    proven_threshold: int = 50


class ShadowScorer:
    """Compare primary and shadow scorers while serving primary results only."""

    def __init__(
        self,
        primary: CompoundingScorer,
        shadow: CompoundingScorer,
        proven_threshold: int = 50,
        *,
        domain: str | None = None,
        preset: Any | None = None,
    ) -> None:
        if primary is shadow:
            raise ValueError("primary and shadow scorers must be independent instances")
        self.primary = primary
        self.shadow = shadow
        self._status = ShadowStatus(proven_threshold=int(proven_threshold))
        self._decision_id_map: dict[str, str] = {}
        self._domain = domain
        self._preset = preset

    @classmethod
    def from_preset(
        cls,
        domain: str,
        primary_store: Any,
        shadow_store: Any,
        proven_threshold: int = 50,
    ) -> "ShadowScorer":
        """Create independent primary and shadow scorers from the same preset."""
        if primary_store is shadow_store:
            raise ValueError(
                "primary_store and shadow_store must be independent instances - shared store corrupts shadow discipline"
            )
        preset = PRESET_REGISTRY[domain]()
        primary = CompoundingScorer.from_preset(
            domain,
            graph_store=primary_store,
            enable_rl=False,
        )
        shadow = CompoundingScorer.from_preset(
            domain,
            graph_store=shadow_store,
            enable_rl=False,
        )
        return cls(
            primary=primary,
            shadow=shadow,
            proven_threshold=proven_threshold,
            domain=domain,
            preset=preset,
        )

    def score(self, *args: Any, **kwargs: Any) -> Any:
        """Score on both scorers, compare, and return the primary result."""
        primary_result = self.primary.score(*args, **kwargs)
        try:
            shadow_result = self.shadow.score(*args, **kwargs)
            primary_id = _get_field(primary_result, "decision_id")
            shadow_id = _get_field(shadow_result, "decision_id")
            if primary_id and shadow_id:
                self._decision_id_map[str(primary_id)] = str(shadow_id)
            comparison = self.compare_score_results(
                primary_result,
                shadow_result,
                decision_id=primary_id,
            )
        except Exception as exc:
            comparison = ComparisonResult(
                matched=False,
                decision_id=_get_field(primary_result, "decision_id"),
                field_results={
                    "shadow_exception": {
                        "matched": False,
                        "primary": None,
                        "shadow": f"{exc.__class__.__name__}: {exc}",
                    }
                },
            )
        self._record_comparison("score", comparison)
        return primary_result

    def learn(self, *args: Any, **kwargs: Any) -> Any:
        """Learn on both scorers, compare state, and return the primary result."""
        primary_result = self.primary.learn(*args, **kwargs)
        try:
            shadow_args = self._shadow_learn_args(args)
            shadow_kwargs = self._shadow_learn_kwargs(args, kwargs)
            self.shadow.learn(*shadow_args, **shadow_kwargs)
            comparison = self.compare_state()
            comparison.decision_id = str(args[0]) if args else kwargs.get("decision_id")
        except Exception as exc:
            comparison = ComparisonResult(
                matched=False,
                decision_id=str(args[0]) if args else kwargs.get("decision_id"),
                field_results={
                    "shadow_exception": {
                        "matched": False,
                        "primary": None,
                        "shadow": f"{exc.__class__.__name__}: {exc}",
                    }
                },
            )
        self._record_comparison("learn", comparison)
        return primary_result

    def compare_score_results(
        self,
        primary_result: Any,
        shadow_result: Any,
        decision_id: str = "",
    ) -> ComparisonResult:
        """Compare decision-critical score outputs field by field."""
        fields = {
            "recommended_action": ("action", "recommended_action"),
            "confidence": ("confidence",),
            "factor_vector": ("factor_vector", "factors"),
            "probabilities": ("probabilities",),
            "routing_zone": ("routing_zone",),
        }
        results: dict[str, dict[str, Any]] = {}
        for field, aliases in fields.items():
            primary_present, primary_value = _first_present(primary_result, aliases)
            shadow_present, shadow_value = _first_present(shadow_result, aliases)
            if not primary_present and not shadow_present and field == "routing_zone":
                continue
            matched = _values_match(primary_value, shadow_value)
            results[field] = {
                "matched": matched,
                "primary": primary_value,
                "shadow": shadow_value,
            }
        return ComparisonResult(
            matched=all(item["matched"] for item in results.values()),
            field_results=results,
            decision_id=decision_id or _get_field(primary_result, "decision_id"),
        )

    def compare_state(self) -> ComparisonResult:
        """Compare current centroid, DK, and conservation state."""
        if self._domain is None or self._preset is None:
            raise ValueError("domain and preset are required for state comparison")
        primary_state = _snapshot_scorer_state(self.primary, self._domain, self._preset)
        shadow_state = _snapshot_scorer_state(self.shadow, self._domain, self._preset)
        state_comparison = compare_states(
            primary_state,
            shadow_state,
            label_a="primary",
            label_b="shadow",
        )
        fields = {
            "centroids": {
                "matched": state_comparison.centroid_match,
                "primary": "snapshot",
                "shadow": "snapshot",
                "details": state_comparison.details.get("centroid_mismatches", []),
            },
            "dk_weights": {
                "matched": state_comparison.dk_match,
                "primary": primary_state.dk_weights,
                "shadow": shadow_state.dk_weights,
                "details": state_comparison.details.get("dk", {}),
            },
            "conservation": {
                "matched": state_comparison.conservation_match,
                "primary": state_comparison.details["conservation"]["primary"],
                "shadow": state_comparison.details["conservation"]["shadow"],
                "details": state_comparison.details["conservation"]["checks"],
            },
            "decision_count": {
                "matched": state_comparison.decision_count_match,
                "primary": primary_state.decision_count,
                "shadow": shadow_state.decision_count,
            },
        }
        return ComparisonResult(
            matched=state_comparison.passed,
            field_results=fields,
        )

    @property
    def status(self) -> ShadowStatus:
        """Current validation status."""
        return self._status

    def report(self) -> dict[str, Any]:
        """Return a structured report suitable for validation scripts."""
        return asdict(self._status)

    def _record_comparison(self, operation: str, comparison: ComparisonResult) -> None:
        self._status.total_comparisons += 1
        if comparison.matched:
            self._status.consecutive_matches += 1
            if self._status.consecutive_matches >= self._status.proven_threshold:
                self._status.status = "proven"
            logger.info(
                "shadow scorer %s comparison matched decision_id=%s consecutive=%s",
                operation,
                comparison.decision_id,
                self._status.consecutive_matches,
            )
            return

        self._status.consecutive_matches = 0
        self._status.status = "validating"
        mismatch = {
            "operation": operation,
            "decision_id": comparison.decision_id,
            "field_results": comparison.field_results,
        }
        self._status.mismatches.append(mismatch)
        if len(self._status.mismatches) > _MAX_MISMATCHES:
            self._status.mismatches = self._status.mismatches[-_MAX_MISMATCHES:]
        logger.warning(
            "shadow scorer %s comparison mismatch decision_id=%s fields=%s",
            operation,
            comparison.decision_id,
            sorted(comparison.field_results),
        )

    def _shadow_learn_args(self, args: tuple[Any, ...]) -> tuple[Any, ...]:
        if not args:
            return args
        primary_id = str(args[0])
        shadow_id = self._decision_id_map.get(primary_id, primary_id)
        return (shadow_id, *args[1:])

    def _shadow_learn_kwargs(self, args: tuple[Any, ...], kwargs: dict[str, Any]) -> dict[str, Any]:
        if args or "decision_id" not in kwargs:
            return dict(kwargs)
        shadow_kwargs = dict(kwargs)
        primary_id = str(shadow_kwargs["decision_id"])
        shadow_kwargs["decision_id"] = self._decision_id_map.get(primary_id, primary_id)
        return shadow_kwargs


def _get_field(value: Any, field_name: str, default: Any = None) -> Any:
    if isinstance(value, dict):
        return value.get(field_name, default)
    return getattr(value, field_name, default)


def _first_present(value: Any, aliases: tuple[str, ...]) -> tuple[bool, Any]:
    for alias in aliases:
        if isinstance(value, dict) and alias in value:
            return True, value[alias]
        if not isinstance(value, dict) and hasattr(value, alias):
            return True, getattr(value, alias)
    return False, None


def _values_match(primary: Any, shadow: Any, atol: float = 1e-6) -> bool:
    if isinstance(primary, dict) and isinstance(shadow, dict):
        if set(primary) != set(shadow):
            return False
        return all(_values_match(primary[key], shadow[key], atol=atol) for key in primary)
    if _is_number(primary) and _is_number(shadow):
        return math.isclose(float(primary), float(shadow), abs_tol=atol, rel_tol=0.0)
    if _is_numeric_sequence(primary) and _is_numeric_sequence(shadow):
        left = np.asarray(primary, dtype=np.float64)
        right = np.asarray(shadow, dtype=np.float64)
        return bool(left.shape == right.shape and np.allclose(left, right, atol=atol, rtol=0.0))
    return bool(primary == shadow)


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _is_numeric_sequence(value: Any) -> bool:
    if not isinstance(value, (list, tuple)):
        return False
    return all(_is_number(item) for item in value)


def _snapshot_scorer_state(scorer: CompoundingScorer, domain: str, preset: Any) -> ScorerState:
    gae_scorer = scorer.gae_scorer
    centroids_array = np.asarray(gae_scorer.centroids, dtype=np.float64)
    centroids = {
        (category_index, action_index): centroids_array[category_index, action_index, :].copy().tolist()
        for category_index in range(centroids_array.shape[0])
        for action_index in range(centroids_array.shape[1])
    }
    store = scorer.graph_store
    verified = _call_count(store, "count_verified", domain)
    correct = _call_count(store, "count_correct", domain)
    q = correct / verified if verified else 0.0
    alpha = _category_coverage_alpha(store, domain, preset)
    category_phases = {
        category_index: scorer.get_category_phase(category_name)
        for category_index, category_name in enumerate(preset.shape.category_names)
    }
    return ScorerState(
        centroids=centroids,
        dk_weights=scorer.get_dk_weights(),
        conservation_V=verified,
        conservation_q=q,
        conservation_alpha=alpha,
        conservation_phase=scorer.get_phase(),
        decision_count=_call_count(store, "count_decisions", domain),
        category_phases=category_phases,
    )


def _category_coverage_alpha(store: Any, domain: str, preset: Any) -> float:
    total_categories = max(int(preset.shape.n_categories), 1)
    get_verified = getattr(store, "get_verified_decisions", None)
    if callable(get_verified):
        try:
            categories: set[int] = set()
            category_names = list(preset.shape.category_names)
            for row in get_verified(domain):
                if "category_index" in row and row.get("category_index") is not None:
                    categories.add(int(row["category_index"]))
                    continue
                category = row.get("category")
                if category in category_names:
                    categories.add(category_names.index(category))
            return len(categories) / total_categories
        except Exception:
            return 0.0
    count_categories_with_n = getattr(store, "count_categories_with_n", None)
    if callable(count_categories_with_n):
        try:
            return min(max(int(count_categories_with_n(domain, n=1)), 0), total_categories) / total_categories
        except Exception:
            return 0.0
    return 0.0


def _call_count(store: Any, method_name: str, domain: str) -> int:
    method = getattr(store, method_name, None)
    if not callable(method):
        return 0
    try:
        return max(int(method(domain)), 0)
    except Exception:
        return 0
