"""Domain configuration base classes.

Shared by all copilots. Each copilot creates its own DomainConfig
subclass with domain-specific actions, factors, situations, and
category metadata.

These are METADATA classes for UI, evidence, and reporting - separate
from DomainPreset (scorer configuration). The scorer does not read from
DomainConfig. DomainConfig does not affect scoring math.

SOC currently has its own copy in its application repository. SOC will
migrate to this SDK version when it next touches its DomainConfig.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class DomainAction:
    """A domain-specific action the copilot can recommend.

    Used for UI labels, cost models, and reporting.
    """

    id: str
    label: str
    time_saved_min: float = 0.0
    cost_dollars: float = 0.0
    risk_level: str = "low"


@dataclass(frozen=True)
class DomainFactor:
    """A domain-specific factor used in scoring.

    Used for evidence panels, NL templates, and trust explanations.
    """

    id: str
    label: str
    description: str = ""


@dataclass(frozen=True)
class DomainSituationType:
    """A domain-specific situation pattern.

    Used by the situation analyzer and situation display.
    """

    id: str
    label: str
    description: str = ""
    color: str = "#6B7280"


@dataclass(frozen=True)
class DomainCategory:
    """A domain-specific category.

    Used for UI labels and category-level reporting.
    """

    id: str
    label: str
    description: str = ""


class BaseDomainConfig:
    """Base class for domain configurations.

    Subclasses define actions, factors, situations, categories.
    Provides lookup helpers: get_action(id), get_factor(id),
    get_categories(), get_category_index(id).
    """

    actions: list[DomainAction] = []
    factors: list[DomainFactor] = []
    situation_types: list[DomainSituationType] = []
    categories: list[DomainCategory] = []

    def get_action(self, action_id: str) -> DomainAction | None:
        return next((action for action in self.actions if action.id == action_id), None)

    def get_factor(self, factor_id: str) -> DomainFactor | None:
        return next((factor for factor in self.factors if factor.id == factor_id), None)

    def get_situation_type(self, type_id: str) -> DomainSituationType | None:
        return next(
            (situation for situation in self.situation_types if situation.id == type_id),
            None,
        )

    def get_categories(self) -> list[str]:
        return [category.id for category in self.categories]

    def get_category_index(self, category_id: str) -> int | None:
        ids = self.get_categories()
        return ids.index(category_id) if category_id in ids else None

    def get_action_ids(self) -> list[str]:
        return [action.id for action in self.actions]

    def get_factor_ids(self) -> list[str]:
        return [factor.id for factor in self.factors]

    def validate_against_preset(self, preset: Any) -> list[str]:
        """Verify domain config agrees with scorer preset shape.

        Checks count AND ordered ID parity for actions, factors, categories.
        Returns list of mismatches (empty = clean).

        This is the programmatic SHAPE-02 integrity check.

        Args:
            preset: A DomainPreset with a .shape attribute (DomainShape with
                n_actions, n_factors, n_categories, action_names, factor_names,
                category_names).

        Returns:
            List of mismatch descriptions. Empty = config and preset agree
            completely.

        Future: DD-1 entity_field check can be added here when entity_field
        ships on DomainPreset.
        """
        shape = getattr(preset, "shape", None)
        if shape is None:
            return []

        errors: list[str] = []
        def check(
            label: str,
            ids: list[str],
            configured_count: int,
            expected_count: int,
            expected_ids: list[str],
        ) -> None:
            if configured_count != expected_count:
                errors.append(
                    f"{label} count mismatch: config={configured_count} "
                    f"preset={expected_count}"
                )
            id_label = label[:-1] if label.endswith("s") else label
            if ids != expected_ids:
                errors.append(
                    f"{id_label} IDs mismatch: config={ids} preset={expected_ids}"
                )

        check(
            "actions",
            self.get_action_ids(),
            len(self.actions),
            shape.n_actions,
            list(shape.action_names),
        )
        check(
            "factors",
            self.get_factor_ids(),
            len(self.factors),
            shape.n_factors,
            list(shape.factor_names),
        )
        check(
            "categories",
            self.get_categories(),
            len(self.categories),
            shape.n_categories,
            list(shape.category_names),
        )

        return errors
