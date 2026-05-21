"""In-memory prompt variant registry and outcome statistics."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field, replace
from typing import Any


VARIANT_STATUSES = frozenset({"active", "shadow", "promoted", "retired"})


@dataclass
class VariantSpec:
    id: str
    family: str
    version: int = 1
    template: str = ""
    status: str = "active"
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.id, str) or not self.id.strip():
            raise ValueError("VariantSpec.id must be a non-empty string")
        if not isinstance(self.family, str) or not self.family.strip():
            raise ValueError("VariantSpec.family must be a non-empty string")
        if not isinstance(self.version, int) or self.version <= 0:
            raise ValueError("VariantSpec.version must be a positive int")
        if self.status not in VARIANT_STATUSES:
            raise ValueError(f"Unsupported variant status: {self.status}")
        self.metadata = dict(self.metadata or {})


@dataclass
class VariantStats:
    successes: int = 0
    total: int = 0
    failures: int = 0

    @property
    def success_rate(self) -> float:
        return self.successes / self.total if self.total > 0 else 0.0


@dataclass
class CategoryVariantStats:
    category: str
    variant_id: str
    successes: int = 0
    total: int = 0
    failures: int = 0

    @property
    def success_rate(self) -> float:
        return self.successes / self.total if self.total > 0 else 0.0


class InMemoryVariantStore:
    """Instance-local prompt variant store."""

    def __init__(self) -> None:
        self._variants: dict[str, VariantSpec] = {}
        self._global_stats: dict[str, VariantStats] = {}
        self._category_stats: dict[str, dict[str, CategoryVariantStats]] = {}

    def register_variant(self, spec: VariantSpec) -> None:
        if not isinstance(spec, VariantSpec):
            raise TypeError("spec must be a VariantSpec")
        if spec.id in self._variants:
            raise ValueError(f"Variant already registered: {spec.id}")
        self._variants[spec.id] = _copy_spec(spec)
        self._global_stats[spec.id] = VariantStats()

    def get_variant(self, variant_id: str) -> VariantSpec | None:
        spec = self._variants.get(variant_id)
        return _copy_spec(spec) if spec is not None else None

    def get_variants_by_family(self, family: str) -> list[VariantSpec]:
        return [
            _copy_spec(spec)
            for spec in self._variants.values()
            if spec.family == family
        ]

    def get_all_variants(self) -> list[VariantSpec]:
        return [_copy_spec(spec) for spec in self._variants.values()]

    def get_active_variants(self) -> list[VariantSpec]:
        return [
            _copy_spec(spec)
            for spec in self._variants.values()
            if spec.status == "active"
        ]

    def get_global_stats(self, variant_id: str) -> VariantStats:
        stats = self._global_stats.get(variant_id)
        return _copy_global_stats(stats) if stats is not None else VariantStats()

    def get_category_stats(self, category: str, variant_id: str) -> CategoryVariantStats:
        stats = self._category_stats.get(category, {}).get(variant_id)
        if stats is None:
            return CategoryVariantStats(category=category, variant_id=variant_id)
        return _copy_category_stats(stats)

    def get_all_category_stats(self, category: str) -> dict[str, CategoryVariantStats]:
        return {
            variant_id: _copy_category_stats(stats)
            for variant_id, stats in self._category_stats.get(category, {}).items()
        }

    def record_outcome(
        self,
        variant_id: str,
        success: bool,
        category: str | None = None,
    ) -> None:
        if variant_id not in self._variants:
            raise ValueError(f"Unknown variant: {variant_id}")
        self._apply_global_outcome(variant_id, success)
        if category is not None:
            self._apply_category_outcome(str(category), variant_id, success)

    def update_variant_status(self, variant_id: str, new_status: str) -> None:
        if new_status not in VARIANT_STATUSES:
            raise ValueError(f"Unsupported variant status: {new_status}")
        spec = self._variants.get(variant_id)
        if spec is None:
            raise ValueError(f"Unknown variant: {variant_id}")
        self._variants[variant_id] = replace(spec, status=new_status)

    def reset(self) -> None:
        self._variants.clear()
        self._global_stats.clear()
        self._category_stats.clear()

    def reset_stats_only(self) -> None:
        self._global_stats.clear()
        self._category_stats.clear()
        for variant_id in self._variants:
            self._global_stats[variant_id] = VariantStats()

    def _apply_global_outcome(self, variant_id: str, success: bool) -> None:
        stats = self._global_stats.setdefault(variant_id, VariantStats())
        stats.total += 1
        if success:
            stats.successes += 1
        else:
            stats.failures += 1

    def _apply_category_outcome(self, category: str, variant_id: str, success: bool) -> None:
        category_stats = self._category_stats.setdefault(category, {})
        stats = category_stats.setdefault(
            variant_id,
            CategoryVariantStats(category=category, variant_id=variant_id),
        )
        stats.total += 1
        if success:
            stats.successes += 1
        else:
            stats.failures += 1


def _copy_spec(spec: VariantSpec) -> VariantSpec:
    return replace(spec, metadata=deepcopy(spec.metadata))


def _copy_global_stats(stats: VariantStats) -> VariantStats:
    return VariantStats(
        successes=stats.successes,
        total=stats.total,
        failures=stats.failures,
    )


def _copy_category_stats(stats: CategoryVariantStats) -> CategoryVariantStats:
    return CategoryVariantStats(
        category=stats.category,
        variant_id=stats.variant_id,
        successes=stats.successes,
        total=stats.total,
        failures=stats.failures,
    )
