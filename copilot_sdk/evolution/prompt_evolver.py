"""Prompt variant evolution foundation."""

from __future__ import annotations

import math
import logging
from dataclasses import dataclass, field
from typing import Any, Callable, Protocol

from copilot_sdk.evolution.gate import DefaultPromotionGate
from copilot_sdk.evolution.conservation_contract import ConservationStateProvider
from copilot_sdk.evolution.protocol import EvolutionEvent, EvolutionLedger
from copilot_sdk.evolution.variant_store import InMemoryVariantStore, VariantSpec, VariantStats, VariantStore


logger = logging.getLogger(__name__)


class _VariantStatsLike(Protocol):
    @property
    def total(self) -> int: ...

    @property
    def success_rate(self) -> float: ...


@dataclass
class PromptEvolverConfig:
    categories: list[str] = field(default_factory=list)
    exploration_constant: float = 1.414
    promotion_improvement_threshold: float = 0.05
    promotion_min_samples: int = 10
    shadow_delta_min: float = 0.05
    shadow_q_floor: float = 0.80
    shadow_sigma_max: float = 0.10
    shadow_min_samples: int = 50
    shadow_min_batches: int = 3
    category_resolver: Callable[[str], str] | None = None
    default_variant_id: str | None = None
    on_variant_selected: Callable[[dict[str, Any]], None] | None = None
    on_outcome_recorded: Callable[[dict[str, Any]], None] | None = None
    on_promoted: Callable[[dict[str, Any]], None] | None = None
    on_rejected: Callable[[dict[str, Any]], None] | None = None
    conservation_state_provider: Callable[[], Any] | ConservationStateProvider | None = None

    def __post_init__(self) -> None:
        self.categories = [str(category) for category in self.categories]
        self.exploration_constant = float(self.exploration_constant)
        self.promotion_improvement_threshold = float(self.promotion_improvement_threshold)
        self.promotion_min_samples = int(self.promotion_min_samples)
        self.shadow_delta_min = float(self.shadow_delta_min)
        self.shadow_q_floor = float(self.shadow_q_floor)
        self.shadow_sigma_max = float(self.shadow_sigma_max)
        self.shadow_min_samples = int(self.shadow_min_samples)
        self.shadow_min_batches = int(self.shadow_min_batches)


class PromptVariantEvolver:
    """Deterministic prompt variant foundation."""

    def __init__(
        self,
        config: PromptEvolverConfig | None = None,
        store: VariantStore | None = None,
        ledger: EvolutionLedger | None = None,
    ) -> None:
        self._config = config or PromptEvolverConfig()
        self._store = store or InMemoryVariantStore()
        self._ledger = ledger
        self._promotion_gate = DefaultPromotionGate()

    @property
    def store(self) -> VariantStore:
        return self._store

    @property
    def config(self) -> PromptEvolverConfig:
        """Return the live configuration used by this evolver."""

        return self._config

    def register_variants(self, specs: list[VariantSpec]) -> None:
        for spec in specs:
            self._store.register_variant(spec)

    def get_variant(
        self,
        *,
        category: str | None = None,
        context_key: str | None = None,
    ) -> VariantSpec | None:
        active_variants = self._store.get_active_variants()
        if not active_variants:
            return None

        active_ids = [variant.id for variant in active_variants]
        resolved_category = self._resolve_category(category=category, context_key=context_key)
        if resolved_category is not None and self._category_has_stats(resolved_category, active_ids):
            selected_id = self._select_ucb(
                {
                    variant_id: self._store.get_category_stats(resolved_category, variant_id)
                    for variant_id in active_ids
                },
                active_ids,
            )
            variant = self._store.get_variant(selected_id) if selected_id is not None else None
            self._emit_selected_hook(variant, category=resolved_category, source="category_ucb")
            return variant

        if self._global_is_cold(active_ids):
            default_variant = self._active_default_variant()
            if default_variant is not None:
                self._emit_selected_hook(default_variant, category=resolved_category, source="default")
                return default_variant

        selected_id = self._select_ucb(
            {variant_id: self._store.get_global_stats(variant_id) for variant_id in active_ids},
            active_ids,
        )
        variant = self._store.get_variant(selected_id) if selected_id is not None else None
        self._emit_selected_hook(variant, category=resolved_category, source="global_ucb")
        return variant

    def record_outcome(
        self,
        variant_id: str,
        success: bool,
        category: str | None = None,
    ) -> None:
        self._store.record_outcome(variant_id, success, category=category)
        self._emit_outcome_hook(
            {
                "variant_id": variant_id,
                "success": bool(success),
                "category": category,
                "source": "outcome",
            }
        )

    def record_shadow_result(
        self,
        variant_id: str,
        success: bool,
        batch_id: str | None = None,
    ) -> None:
        spec = self._require_variant(variant_id)
        self._store.record_outcome(variant_id, success, category=None)
        payload = {
            "variant_id": variant_id,
            "family": spec.family,
            "success": bool(success),
            "batch_id": batch_id,
            "source": "shadow_result",
        }
        self._emit_lifecycle_event("shadow_completed", variant_id, payload)
        self._emit_outcome_hook(payload)

    def check_for_promotion(
        self,
        family: str | None = None,
        conservation_state: Any = None,
    ) -> dict | None:
        families = [family] if family is not None else self._families_in_order()
        for family_name in families:
            result = self._check_family_for_promotion(family_name, conservation_state)
            if result is not None:
                return result
        return None

    def get_summary(self) -> dict:
        variants = []
        for spec in self._store.get_all_variants():
            stats = self._store.get_global_stats(spec.id)
            variants.append(
                {
                    "id": spec.id,
                    "family": spec.family,
                    "version": spec.version,
                    "status": spec.status,
                    "successes": stats.successes,
                    "failures": stats.failures,
                    "total": stats.total,
                    "success_rate": stats.success_rate,
                }
            )
        return {
            "variant_count": len(variants),
            "active_count": sum(1 for variant in variants if variant["status"] == "active"),
            "variants": variants,
            "categories": list(self._config.categories),
        }

    def reset(self) -> None:
        self._store.reset()

    def reset_stats(self) -> None:
        self._store.reset_stats_only()

    def _check_family_for_promotion(self, family: str, conservation_state: Any = None) -> dict | None:
        variants = self._store.get_variants_by_family(family)
        active_variants = [variant for variant in variants if variant.status == "active"]
        if not active_variants:
            return None

        active_variant = active_variants[0]
        shadow_variants = [variant for variant in variants if variant.status == "shadow"]
        if not shadow_variants:
            return None

        # Prompt evolution is a compounding loop: conservation must be safe
        # before sample or improvement evidence can authorize promotion.
        conservation_state = self._resolve_conservation_state(conservation_state)
        if not self._promotion_gate._is_conservation_safe(conservation_state):
            blocked = shadow_variants[0]
            blocked_stats = self._store.get_global_stats(blocked.id)
            reason = self._conservation_rejection_reason(conservation_state)
            logger.warning(
                "Prompt variant promotion blocked: reason=%s, conservation=%s, variant=%s",
                reason,
                conservation_state,
                blocked.id,
            )
            result = {
                "family": family,
                "promoted": False,
                "reason": reason,
                "message": (
                    "Prompt variant promotion blocked: conservation RED"
                    if reason == "conservation_gate_red"
                    else "Prompt variant promotion blocked: conservation unavailable"
                ),
                "candidate_id": blocked.id,
                "previous_id": active_variant.id,
                "candidate_total": blocked_stats.total,
            }
            self._emit_lifecycle_event(
                "rejected",
                blocked.id,
                {
                    **result,
                    "variant_id": blocked.id,
                    "previous_active": active_variant.id,
                },
            )
            if self._config.on_rejected is not None:
                self._config.on_rejected(dict(result))
            return result

        active_stats = self._store.get_global_stats(active_variant.id)
        active_rate = active_stats.success_rate
        candidates: list[tuple[int, VariantSpec, VariantStats, float, float]] = []
        for variant in shadow_variants:
            candidate_stats = self._store.get_global_stats(variant.id)
            if candidate_stats.total < self._config.promotion_min_samples:
                continue
            candidate_rate = candidate_stats.success_rate
            improvement = candidate_rate - active_rate
            if improvement <= self._config.promotion_improvement_threshold:
                continue
            candidates.append((len(candidates), variant, candidate_stats, candidate_rate, improvement))

        if not candidates:
            return None

        _, promoted, promoted_stats, candidate_rate, improvement = max(
            candidates,
            key=lambda candidate: (
                candidate[4],
                candidate[3],
                -candidate[0],
            ),
        )
        self._store.update_variant_status(active_variant.id, "retired")
        self._store.update_variant_status(promoted.id, "active")

        result = {
            "family": family,
            "promoted_id": promoted.id,
            "previous_id": active_variant.id,
            "improvement": improvement,
            "candidate_rate": candidate_rate,
            "active_rate": active_rate,
            "candidate_total": promoted_stats.total,
        }
        self._emit_lifecycle_event(
            "promoted",
            promoted.id,
            {
                **result,
                "variant_id": promoted.id,
                "previous_active": active_variant.id,
            },
        )
        if self._config.on_promoted is not None:
            self._config.on_promoted(dict(result))
        return result

    def _resolve_conservation_state(self, conservation_state: Any = None) -> Any:
        provider = self._config.conservation_state_provider
        if conservation_state is not None:
            logger.warning(
                "Explicit conservation_state is deprecated; configured provider is authoritative"
            )
        if provider is None:
            return conservation_state if conservation_state is not None else {"status": "UNKNOWN"}
        try:
            if callable(provider):
                return provider()
            return provider.get_state()
        except Exception as exc:
            logger.warning("Conservation provider failed; promotion is blocked: %s", exc)
            return {"status": "UNKNOWN", "reason": "provider_error"}

    @staticmethod
    def _conservation_rejection_reason(conservation_state: Any) -> str:
        values: list[Any] = []
        if isinstance(conservation_state, str):
            values.append(conservation_state)
        elif isinstance(conservation_state, dict):
            values.extend(
                conservation_state.get(key)
                for key in ("status", "state", "phase")
            )
        if any(isinstance(value, str) and value.strip().upper() == "RED" for value in values):
            return "conservation_gate_red"
        return "conservation_gate_unavailable"

    def _families_in_order(self) -> list[str]:
        families: list[str] = []
        seen: set[str] = set()
        for variant in self._store.get_all_variants():
            if variant.family in seen:
                continue
            seen.add(variant.family)
            families.append(variant.family)
        return families

    def _resolve_category(
        self,
        *,
        category: str | None,
        context_key: str | None,
    ) -> str | None:
        if category is not None:
            return _clean_category(category)
        if context_key is None or self._config.category_resolver is None:
            return None
        return _clean_category(self._config.category_resolver(context_key))

    def _category_has_stats(self, category: str, active_ids: list[str]) -> bool:
        return any(
            self._store.get_category_stats(category, variant_id).total > 0
            for variant_id in active_ids
        )

    def _global_is_cold(self, active_ids: list[str]) -> bool:
        return all(
            self._store.get_global_stats(variant_id).total <= 0
            for variant_id in active_ids
        )

    def _active_default_variant(self) -> VariantSpec | None:
        default_variant_id = self._config.default_variant_id
        if not default_variant_id:
            return None
        default_variant = self._store.get_variant(default_variant_id)
        if default_variant is None or default_variant.status != "active":
            return None
        return default_variant

    def _select_ucb(
        self,
        stats_by_variant: dict[str, _VariantStatsLike],
        active_ids: list[str],
    ) -> str | None:
        if not active_ids:
            return None
        total_all = 0
        for variant_id in active_ids:
            stats = stats_by_variant.get(variant_id)
            if stats is not None:
                total_all += max(int(stats.total), 0)
        if total_all <= 0:
            return active_ids[0]

        best_variant_id: str | None = None
        best_score = float("-inf")
        log_total = math.log(max(total_all, 2))
        for variant_id in active_ids:
            stats = stats_by_variant[variant_id]
            total = int(stats.total)
            if total <= 0:
                return variant_id
            mean = float(stats.success_rate)
            exploration = self._config.exploration_constant * math.sqrt(log_total / total)
            score = mean + exploration
            if score > best_score:
                best_variant_id = variant_id
                best_score = score
        return best_variant_id

    def _require_variant(self, variant_id: str) -> VariantSpec:
        spec = self._store.get_variant(variant_id)
        if spec is None:
            raise ValueError(f"Unknown variant: {variant_id}")
        return spec

    def _emit_lifecycle_event(
        self,
        event_type: str,
        variant_id: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        if self._ledger is None:
            return
        spec = self._store.get_variant(variant_id)
        event_metadata = dict(metadata or {})
        event_metadata.setdefault("variant_id", variant_id)
        if spec is not None:
            event_metadata.setdefault("family", spec.family)
        rule_name = str(event_metadata.get("family") or (spec.family if spec is not None else variant_id))
        self._ledger.append(
            EvolutionEvent(
                event_type=event_type,
                rule_name=rule_name,
                variant_id=variant_id,
                metadata=event_metadata,
            )
        )

    def _emit_selected_hook(
        self,
        variant: VariantSpec | None,
        *,
        category: str | None,
        source: str,
    ) -> None:
        if variant is None or self._config.on_variant_selected is None:
            return
        self._config.on_variant_selected(
            {
                "variant_id": variant.id,
                "family": variant.family,
                "category": category,
                "source": source,
            }
        )

    def _emit_outcome_hook(self, payload: dict[str, Any]) -> None:
        if self._config.on_outcome_recorded is not None:
            self._config.on_outcome_recorded(dict(payload))


def _clean_category(category: str | None) -> str | None:
    if category is None:
        return None
    value = str(category).strip()
    return value or None
