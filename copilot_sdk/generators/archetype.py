"""Industry archetype generator for ephemeral domain presets."""

from __future__ import annotations

import hashlib
import json
import math
import re
import sys
from dataclasses import dataclass
from typing import Any

import numpy as np

from copilot_sdk.evolution import PlateauConfig
from copilot_sdk.scoring.config import DomainShape


@dataclass(frozen=True)
class GeneratedDomainPreset:
    """DomainPreset-compatible config generated from an industry archetype."""

    name: str
    shape: DomainShape
    penalty_ratio: float
    bootstrap_centroids: np.ndarray
    eta_confirm: float = 0.05
    eta_override: float = 0.01
    temperature: float = 0.1
    expected_initial_accuracy: float = 0.65
    plateau_config: PlateauConfig | None = None


@dataclass(frozen=True)
class _ArchetypeSpec:
    name: str
    canonical_description: str
    categories: tuple[str, ...]
    actions: tuple[str, ...]
    factors: tuple[str, ...]
    penalty_ratio: float


_ARCHETYPES: tuple[_ArchetypeSpec, ...] = (
    _ArchetypeSpec(
        name="security_operations",
        canonical_description=(
            "Security operations teams investigate credential misuse, lateral movement, "
            "malware execution, command-and-control activity, privilege escalation, and "
            "data exfiltration. The copilot recommends response actions under high "
            "asymmetric error cost where false reassurance is expensive. Signals include "
            "identity risk, endpoint telemetry, network movement, data movement, "
            "privilege context, and threat confidence."
        ),
        categories=(
            "credential_access",
            "lateral_movement",
            "data_exfiltration",
            "privilege_escalation",
            "malware_execution",
            "command_and_control",
        ),
        actions=("monitor", "investigate", "escalate", "contain"),
        factors=(
            "identity_risk",
            "asset_criticality",
            "threat_confidence",
            "blast_radius",
            "control_coverage",
            "analyst_context",
        ),
        penalty_ratio=20.0,
    ),
    _ArchetypeSpec(
        name="source_to_pay",
        canonical_description=(
            "Source-to-pay teams evaluate invoices, purchase orders, supplier exceptions, "
            "contract coverage, and payment terms. The copilot detects duplicate invoices, "
            "price variance, quantity mismatch, contract gaps, and format compliance issues. "
            "Recommended actions balance automation with buyer review, leakage investigation, "
            "and specialist referral."
        ),
        categories=(
            "price_variance",
            "duplicate_invoice",
            "quantity_mismatch",
            "contract_gap",
            "format_compliance",
        ),
        actions=(
            "auto_approve",
            "hold_for_review",
            "escalate_to_buyer",
            "flag_leakage",
            "refer_to_specialist",
        ),
        factors=(
            "match_status",
            "amount_variance_ratio",
            "duplicate_score",
            "supplier_exception_history",
            "payment_terms_impact",
            "commodity_index_correlation",
            "tax_regulatory_compliance",
        ),
        penalty_ratio=5.0,
    ),
    _ArchetypeSpec(
        name="dataops",
        canonical_description=(
            "Data operations teams monitor schema changes, pipeline failures, data quality "
            "incidents, access anomalies, performance degradation, and configuration drift. "
            "The copilot recommends approval, investigation, owner escalation, downstream "
            "pause, or specialist referral based on operational impact. Signals include "
            "impact scope, source reliability, recurrence, urgency, freshness, and business "
            "criticality."
        ),
        categories=(
            "schema_change",
            "pipeline_failure",
            "data_quality",
            "access_anomaly",
            "performance_degradation",
            "configuration_drift",
        ),
        actions=(
            "auto_approve",
            "investigate",
            "escalate_to_owner",
            "pause_downstream",
            "refer_to_specialist",
        ),
        factors=(
            "impact_scope",
            "source_reliability",
            "recurrence_frequency",
            "downstream_urgency",
            "data_freshness",
            "business_criticality",
        ),
        penalty_ratio=10.0,
    ),
    _ArchetypeSpec(
        name="financial_services",
        canonical_description=(
            "Financial services teams review transaction anomalies, fraud signals, credit "
            "risk, compliance breaches, and regulatory reporting exceptions. The copilot "
            "recommends approval, review, escalation, or rejection under material but "
            "bounded financial and regulatory risk. Signals include transaction amount, "
            "counterparty risk, deviation from historical patterns, regulatory exposure, "
            "frequency, and velocity."
        ),
        categories=(
            "transaction_anomaly",
            "compliance_breach",
            "credit_risk",
            "fraud_detection",
            "regulatory_reporting",
        ),
        actions=("approve", "flag_review", "escalate", "reject"),
        factors=(
            "transaction_amount",
            "counterparty_risk",
            "pattern_deviation",
            "regulatory_exposure",
            "historical_frequency",
            "velocity",
        ),
        penalty_ratio=8.0,
    ),
)

_ARCHETYPE_BY_NAME = {spec.name: spec for spec in _ARCHETYPES}
_SUPPORTED_OVERRIDES = {"penalty_ratio", "categories", "actions", "factors"}


class ArchetypeGenerator:
    """Build ephemeral DomainPreset-compatible configs from archetypes."""

    @staticmethod
    def list_archetypes() -> list[str]:
        return [spec.name for spec in _ARCHETYPES]

    @staticmethod
    def from_archetype(name: str, overrides: dict[str, Any] | None = None) -> GeneratedDomainPreset:
        try:
            spec = _ARCHETYPE_BY_NAME[name]
        except KeyError as exc:
            available = ", ".join(ArchetypeGenerator.list_archetypes())
            raise ValueError(f"Unknown archetype {name!r}. Available archetypes: {available}") from exc
        return _build_preset(spec, overrides)

    @staticmethod
    def from_description(text: str, overrides: dict[str, Any] | None = None) -> GeneratedDomainPreset:
        scores = ArchetypeGenerator.score_archetypes(text)
        return ArchetypeGenerator.from_archetype(scores[0][0], overrides=overrides)

    @staticmethod
    def score_archetypes(text: str) -> list[tuple[str, float]]:
        query = _require_description(text)
        scores = _score_with_sklearn(query)
        if scores is None:
            scores = _score_with_token_overlap(query)
        order = {spec.name: index for index, spec in enumerate(_ARCHETYPES)}
        return sorted(scores, key=lambda item: (-item[1], order[item[0]]))


def _build_preset(
    spec: _ArchetypeSpec,
    overrides: dict[str, Any] | None = None,
) -> GeneratedDomainPreset:
    values = _apply_overrides(spec, overrides)
    categories = values["categories"]
    actions = values["actions"]
    factors = values["factors"]
    shape = DomainShape(
        n_categories=len(categories),
        n_actions=len(actions),
        n_factors=len(factors),
        category_names=categories,
        action_names=actions,
        factor_names=factors,
    )
    centroids = _generate_centroids(spec.name, shape, values)
    expected_initial_accuracy = _expected_initial_accuracy(centroids)
    return GeneratedDomainPreset(
        name=spec.name,
        shape=shape,
        penalty_ratio=values["penalty_ratio"],
        bootstrap_centroids=centroids,
        expected_initial_accuracy=expected_initial_accuracy,
        plateau_config=_plateau_config_for_shape(shape),
    )


def _apply_overrides(spec: _ArchetypeSpec, overrides: dict[str, Any] | None) -> dict[str, Any]:
    raw = dict(overrides or {})
    unsupported = sorted(set(raw) - _SUPPORTED_OVERRIDES)
    if unsupported:
        raise ValueError(f"Unsupported override key(s): {', '.join(unsupported)}")

    values: dict[str, Any] = {
        "categories": spec.categories,
        "actions": spec.actions,
        "factors": spec.factors,
        "penalty_ratio": spec.penalty_ratio,
    }
    if "categories" in raw:
        values["categories"] = _validate_names(raw["categories"], "categories")
    if "actions" in raw:
        values["actions"] = _validate_names(raw["actions"], "actions")
    if "factors" in raw:
        values["factors"] = _validate_names(raw["factors"], "factors")
    if "penalty_ratio" in raw:
        values["penalty_ratio"] = _validate_penalty_ratio(raw["penalty_ratio"])
    return values


def _validate_names(value: Any, field_name: str) -> tuple[str, ...]:
    if isinstance(value, str) or not isinstance(value, (list, tuple)):
        raise ValueError(f"{field_name} override must be a non-empty list or tuple of names")

    names: list[str] = []
    for index, item in enumerate(value):
        if not isinstance(item, str):
            raise ValueError(
                f"{field_name} override values must be strings; "
                f"item {index} has type {type(item).__name__}"
            )
        names.append(item.strip())

    names_tuple = tuple(names)
    if not names_tuple or any(not item for item in names_tuple):
        raise ValueError(f"{field_name} override must contain only non-empty names")
    if len(set(names_tuple)) != len(names_tuple):
        raise ValueError(f"{field_name} override must not contain duplicates")
    return names_tuple


def _validate_penalty_ratio(value: Any) -> float:
    try:
        penalty_ratio = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError("penalty_ratio override must be a finite positive number") from exc
    if not math.isfinite(penalty_ratio) or penalty_ratio <= 0:
        raise ValueError("penalty_ratio override must be a finite positive number")
    return penalty_ratio


def _plateau_config_for_shape(shape: DomainShape) -> PlateauConfig:
    cells = shape.n_categories * shape.n_actions
    window = round(10 * math.sqrt(cells / 20))
    return PlateauConfig(
        plateau_window=window,
        min_improvement_rate=0.20,
        plateau_cooldown=window * 5,
    )


def _generate_centroids(
    archetype_name: str,
    shape: DomainShape,
    values: dict[str, Any],
) -> np.ndarray:
    payload = {
        "name": archetype_name,
        "categories": values["categories"],
        "actions": values["actions"],
        "factors": values["factors"],
        "penalty_ratio": values["penalty_ratio"],
    }
    seed_bytes = hashlib.sha256(
        json.dumps(payload, sort_keys=True).encode("utf-8")
    ).digest()[:8]
    seed = int.from_bytes(seed_bytes, "big", signed=False)
    rng = np.random.default_rng(seed)
    base = np.full(shape.tensor_shape, 0.5, dtype=np.float64)
    noise = rng.uniform(-0.1, 0.1, size=shape.tensor_shape)
    return np.clip(base + noise, 0.0, 1.0).astype(np.float64)


def _expected_initial_accuracy(centroids: np.ndarray) -> float:
    """Heuristic initial accuracy from archetype centroid confidence."""
    confidence = float(np.mean(np.max(np.asarray(centroids, dtype=np.float64), axis=1)))
    return round(max(0.5, min(0.9, confidence + 0.08)), 2)


def _score_with_sklearn(text: str) -> list[tuple[str, float]] | None:
    previous_modules = {name for name in sys.modules if name == "sklearn" or name.startswith("sklearn.")}
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity
    except ImportError:
        return None
    try:
        documents = [spec.canonical_description for spec in _ARCHETYPES]
        matrix = TfidfVectorizer().fit_transform([text, *documents])
        similarities = cosine_similarity(matrix[0:1], matrix[1:]).ravel()
        return [
            (spec.name, float(score))
            for spec, score in zip(_ARCHETYPES, similarities)
        ]
    finally:
        for module_name in list(sys.modules):
            if (
                (module_name == "sklearn" or module_name.startswith("sklearn."))
                and module_name not in previous_modules
            ):
                sys.modules.pop(module_name, None)


def _score_with_token_overlap(text: str) -> list[tuple[str, float]]:
    query_tokens = _tokens(text)
    return [
        (spec.name, _jaccard(query_tokens, _tokens(spec.canonical_description)))
        for spec in _ARCHETYPES
    ]


def _jaccard(left: set[str], right: set[str]) -> float:
    if not left and not right:
        return 0.0
    return len(left & right) / len(left | right)


def _tokens(text: str) -> set[str]:
    return {token for token in re.split(r"[^a-z0-9_]+", text.lower()) if token}


def _require_description(text: str) -> str:
    if not isinstance(text, str) or not text.strip():
        raise ValueError("Description text must be a non-empty string")
    return text.strip()
