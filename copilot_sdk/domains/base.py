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
