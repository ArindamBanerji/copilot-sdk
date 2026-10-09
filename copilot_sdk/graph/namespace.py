"""Domain isolation for consumers borrowing one protocol graph store."""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from dataclasses import replace
from typing import Any, cast

from copilot_sdk.graph.enrichment import (
    EnrichmentSourceSet, EntityEnrichmentReceipt, EntityEnrichmentRecord,
    ProvenancedValue,
)
from copilot_sdk.graph.protocol import ProtocolV2GraphStore

_DOMAIN_FIELDS = frozenset({"domain", "source_domain", "target_domain"})
_PAYLOAD_FIELDS = frozenset({
    "metadata", "outcome_metadata", "context", "factors", "factor_stats",
    "fingerprint", "factor_mapping", "canonical_payload", "payload", "state",
    "metrics", "computed_from", "centroids",
})


class GraphStoreNamespace(ProtocolV2GraphStore):
    """Stateless domain-namespace view over one shared governed graph.

    Rewrites every domain argument as ``f"{namespace}::{domain}"`` on writes
    and strips the prefix on reads. The adapter does not own the store lifecycle.
    """

    def __init__(self, store: ProtocolV2GraphStore, namespace: str) -> None:
        normalized = namespace.strip()
        if not normalized or "::" in normalized:
            raise ValueError("namespace must be a non-empty single segment")
        if not isinstance(store, ProtocolV2GraphStore):
            raise RuntimeError("GraphStoreNamespace requires ProtocolV2GraphStore")
        self._store = store
        self._prefix = f"{normalized}::"

    def _domain(self, domain: str) -> str:
        if not domain.strip():
            raise ValueError("domain must be non-empty")
        if domain.startswith(":"):
            raise ValueError("domain must not begin with a colon")
        return f"{self._prefix}{domain}"

    def _logical_domain(self, domain: str) -> str:
        if not self._owns_domain(domain):
            raise ValueError("graph result escaped its namespace")
        return domain[len(self._prefix):]

    def _owns_domain(self, domain: object) -> bool:
        return (
            isinstance(domain, str)
            and domain.startswith(self._prefix)
            and bool(domain[len(self._prefix):].strip())
            and not domain[len(self._prefix):].startswith(":")
        )

    @staticmethod
    def _transfer_row(value: Mapping[str, Any]) -> bool:
        return all(
            key in value for key in ("pattern_id", "source_domain", "target_domain")
        )

    def _domain_values(self, value: object) -> list[object]:
        domains: list[object] = []
        if isinstance(value, Mapping):
            for key, item in value.items():
                if key == "domain" and self._transfer_row(value):
                    continue
                if key in _DOMAIN_FIELDS:
                    domains.append(item)
                elif key not in _PAYLOAD_FIELDS:
                    domains.extend(self._domain_values(item))
        elif isinstance(value, list):
            for item in value:
                domains.extend(self._domain_values(item))
        return domains

    def _rewrite(self, value: Any) -> Any:
        if isinstance(value, Mapping):
            return {
                key: (
                    deepcopy(item)
                    if key == "domain" and self._transfer_row(value)
                    else self._logical_domain(item)
                    if key in _DOMAIN_FIELDS
                    else deepcopy(item)
                    if key in _PAYLOAD_FIELDS
                    else self._rewrite(item)
                )
                for key, item in value.items()
            }
        if isinstance(value, list):
            return [self._rewrite(item) for item in value]
        return deepcopy(value)

    def _row(self, row: Mapping[str, Any]) -> dict[str, Any]:
        if not self._belongs(row):
            raise RuntimeError("result row is not bounded to this namespace")
        return cast(dict[str, Any], self._rewrite(row))

    def _rows(self, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [self._row(row) for row in rows if self._belongs(row)]

    def _belongs(self, row: Mapping[str, Any]) -> bool:
        domains = self._domain_values(row)
        return bool(domains) and all(self._owns_domain(domain) for domain in domains)

    def write_decision(self, domain: str, category: str, action: str, confidence: float, factors: dict[str, Any], metadata: dict[str, Any] | None=None) -> str:
        result: str = self._store.write_decision(
            domain=self._domain(domain),
            category=category,
            action=action,
            confidence=confidence,
            factors=factors,
            metadata=metadata,
        )
        return result

    def write_outcome(self, decision_id: str, actual_action: str, is_correct: bool, metadata: dict[str, Any] | None=None, *, domain: str, outcome: str | None=None, verified_at_epoch: float | None=None, quality_signal: float | None=None, override_comment: str | None=None, verified_by: str | None=None, analyst_action: str | None=None, final_action: str | None=None, recommended_action: str | None=None, was_override: bool | None=None) -> None:
        self._store.write_outcome(
            decision_id=decision_id,
            actual_action=actual_action,
            is_correct=is_correct,
            metadata=metadata,
            domain=self._domain(domain),
            outcome=outcome,
            verified_at_epoch=verified_at_epoch,
            quality_signal=quality_signal,
            override_comment=override_comment,
            verified_by=verified_by,
            analyst_action=analyst_action,
            final_action=final_action,
            recommended_action=recommended_action,
            was_override=was_override,
        )

    def get_decision(self, decision_id: str, domain: str, *, include_outcome: bool=False) -> dict[str, Any] | None:
        result = self._store.get_decision(
            decision_id=decision_id,
            domain=self._domain(domain),
            include_outcome=include_outcome,
        )
        return self._row(result) if result is not None else None

    def get_decisions(self, domain: str, category: str | None=None, limit: int=400) -> list[dict[str, Any]]:
        result = self._store.get_decisions(
            domain=self._domain(domain),
            category=category,
            limit=limit,
        )
        return self._rows(result)

    def get_all_decisions(self, domain: str) -> list[dict[str, Any]]:
        result = self._store.get_all_decisions(
            domain=self._domain(domain),
        )
        return self._rows(result)

    def get_archived_decisions(self, domain: str) -> list[dict[str, Any]]:
        result = self._store.get_archived_decisions(
            domain=self._domain(domain),
        )
        return self._rows(result)

    def get_verified_decisions(self, domain: str) -> list[dict[str, Any]]:
        result = self._store.get_verified_decisions(
            domain=self._domain(domain),
        )
        return self._rows(result)

    def count_verified(self, domain: str) -> int:
        result: int = self._store.count_verified(
            domain=self._domain(domain),
        )
        return result

    def count_verified_decisions(self, domain: str) -> int:
        result: int = self._store.count_verified_decisions(
            domain=self._domain(domain),
        )
        return result

    def save_evolution(self, domain: str, variant_id: str, state: dict[str, Any]) -> None:
        self._store.save_evolution(
            domain=self._domain(domain),
            variant_id=variant_id,
            state=state,
        )

    def get_evolution(self, domain: str, variant_id: str) -> dict[str, Any] | None:
        result: dict[str, Any] | None = self._store.get_evolution(
            domain=self._domain(domain),
            variant_id=variant_id,
        )
        return result

    def list_evolutions(self, domain: str) -> list[dict[str, Any]]:
        result: list[dict[str, Any]] = self._store.list_evolutions(
            domain=self._domain(domain),
        )
        return result

    def delete_evolution(self, domain: str, variant_id: str) -> None:
        self._store.delete_evolution(
            domain=self._domain(domain),
            variant_id=variant_id,
        )

    def save_evolution_state(self, domain: str, variant_id: str, state: dict[str, Any]) -> None:
        self._store.save_evolution_state(
            domain=self._domain(domain),
            variant_id=variant_id,
            state=state,
        )

    def get_evolution_state(self, domain: str, variant_id: str) -> dict[str, Any] | None:
        result: dict[str, Any] | None = self._store.get_evolution_state(
            domain=self._domain(domain),
            variant_id=variant_id,
        )
        return result

    def save_posterior(self, domain: str, key: str, state: dict[str, Any]) -> None:
        self._store.save_posterior(
            domain=self._domain(domain),
            key=key,
            state=state,
        )

    def get_posterior(self, domain: str, key: str) -> dict[str, Any] | None:
        result: dict[str, Any] | None = self._store.get_posterior(
            domain=self._domain(domain),
            key=key,
        )
        return result

    def list_posteriors(self, domain: str) -> list[dict[str, Any]]:
        result: list[dict[str, Any]] = self._store.list_posteriors(
            domain=self._domain(domain),
        )
        return result

    def delete_posterior(self, domain: str, key: str) -> None:
        self._store.delete_posterior(
            domain=self._domain(domain),
            key=key,
        )

    def save_promotion(self, domain: str, rule_id: str, state: dict[str, Any]) -> None:
        self._store.save_promotion(
            domain=self._domain(domain),
            rule_id=rule_id,
            state=state,
        )

    def get_promotion(self, domain: str, rule_id: str) -> dict[str, Any] | None:
        result: dict[str, Any] | None = self._store.get_promotion(
            domain=self._domain(domain),
            rule_id=rule_id,
        )
        return result

    def list_promotions(self, domain: str) -> list[dict[str, Any]]:
        result: list[dict[str, Any]] = self._store.list_promotions(
            domain=self._domain(domain),
        )
        return result

    def delete_promotion(self, domain: str, rule_id: str) -> None:
        self._store.delete_promotion(
            domain=self._domain(domain),
            rule_id=rule_id,
        )

    def save_ledger(self, domain: str, entry_id: str, state: dict[str, Any]) -> None:
        self._store.save_ledger(
            domain=self._domain(domain),
            entry_id=entry_id,
            state=state,
        )

    def get_ledger(self, domain: str, entry_id: str) -> dict[str, Any] | None:
        result: dict[str, Any] | None = self._store.get_ledger(
            domain=self._domain(domain),
            entry_id=entry_id,
        )
        return result

    def list_ledgers(self, domain: str) -> list[dict[str, Any]]:
        result: list[dict[str, Any]] = self._store.list_ledgers(
            domain=self._domain(domain),
        )
        return result

    def delete_ledger(self, domain: str, entry_id: str) -> None:
        self._store.delete_ledger(
            domain=self._domain(domain),
            entry_id=entry_id,
        )

    def save_governance(self, domain: str, key: str, state: dict[str, Any]) -> None:
        self._store.save_governance(
            domain=self._domain(domain),
            key=key,
            state=state,
        )

    def get_governance(self, domain: str, key: str) -> dict[str, Any] | None:
        result: dict[str, Any] | None = self._store.get_governance(
            domain=self._domain(domain),
            key=key,
        )
        return result

    def list_governance(self, domain: str) -> list[dict[str, Any]]:
        result: list[dict[str, Any]] = self._store.list_governance(
            domain=self._domain(domain),
        )
        return result

    def delete_governance(self, domain: str, key: str) -> None:
        self._store.delete_governance(
            domain=self._domain(domain),
            key=key,
        )

    def count_correct(self, domain: str) -> int:
        result: int = self._store.count_correct(
            domain=self._domain(domain),
        )
        return result

    def count_decisions(self, domain: str) -> int:
        result: int = self._store.count_decisions(
            domain=self._domain(domain),
        )
        return result

    def save_centroids(self, domain: str, category: str, centroids: Any, metadata: dict[str, Any] | None=None, **kwargs: Any) -> None:
        self._store.save_centroids(
            domain=self._domain(domain),
            category=category,
            centroids=centroids,
            metadata=metadata,
            **kwargs,
        )

    def load_latest_centroids(self, domain: str) -> Any | None:
        result: Any | None = self._store.load_latest_centroids(
            domain=self._domain(domain),
        )
        return result

    def get_centroid_checkpoints(self, domain: str, include_v2: bool=False, **kwargs: Any) -> list[dict[str, Any]]:
        result = self._store.get_centroid_checkpoints(
            domain=self._domain(domain),
            include_v2=include_v2,
            **kwargs,
        )
        return self._rows(result)

    def load_latest_checkpoint_for_regime(self, domain: str, regime_tag: str) -> dict[str, Any] | None:
        result = self._store.load_latest_checkpoint_for_regime(
            domain=self._domain(domain),
            regime_tag=regime_tag,
        )
        return self._row(result) if result is not None else None

    def get_checkpoint_lineage(self, domain: str, checkpoint_id: str) -> dict[str, Any] | None:
        result = self._store.get_checkpoint_lineage(
            domain=self._domain(domain),
            checkpoint_id=checkpoint_id,
        )
        return self._row(result) if result is not None else None

    def get_decision_checkpoints(self, domain: str, decision_id: str) -> list[dict[str, Any]]:
        result = self._store.get_decision_checkpoints(
            domain=self._domain(domain),
            decision_id=decision_id,
        )
        return self._rows(result)

    def archive_old_decisions(self, domain: str, keep_recent: int=800) -> int:
        result: int = self._store.archive_old_decisions(
            domain=self._domain(domain),
            keep_recent=keep_recent,
        )
        return result

    def count_archived(self, domain: str) -> int:
        result: int = self._store.count_archived(
            domain=self._domain(domain),
        )
        return result

    def close(self) -> None:
        # Caller owns the borrowed graph lifecycle.
        return None

    def write_entity_enrichment(self, *, domain: str, entity_type: str, entity_id: str, namespace: str, metrics: dict[str, ProvenancedValue], computed_from: EnrichmentSourceSet, dry_run: bool=False, idempotency_key: str | None=None) -> EntityEnrichmentReceipt:
        receipt = self._store.write_entity_enrichment(
            domain=self._domain(domain),
            entity_type=entity_type,
            entity_id=entity_id,
            namespace=namespace,
            metrics=metrics,
            computed_from=computed_from,
            dry_run=dry_run,
            idempotency_key=idempotency_key,
        )
        return replace(receipt, domain=self._logical_domain(receipt.domain))

    def read_entity_enrichment(self, *, domain: str, entity_type: str, entity_id: str, namespace: str | None=None) -> dict[str, ProvenancedValue]:
        result: dict[str, ProvenancedValue] = self._store.read_entity_enrichment(
            domain=self._domain(domain),
            entity_type=entity_type,
            entity_id=entity_id,
            namespace=namespace,
        )
        return result

    def list_entity_enrichments(self, *, domain: str, entity_type: str | None=None, namespace: str | None=None, limit: int=500) -> list[EntityEnrichmentRecord]:
        records = self._store.list_entity_enrichments(
            domain=self._domain(domain),
            entity_type=entity_type,
            namespace=namespace,
            limit=limit,
        )
        return [
            replace(record, domain=self._logical_domain(record.domain))
            for record in records
            if record.domain.startswith(self._prefix)
        ]

    def generate_decision_id(self, domain: str) -> str:
        result: str = self._store.generate_decision_id(
            domain=self._domain(domain),
        )
        return result

    def write_governed_decision(self, decision_id: str, domain: str, category: str, category_index: int, recommended_action: str, recommended_index: int, confidence: float, probabilities: list[float], factor_vector: list[float], factor_names: list[str], source: str='score', scorer_version: str='', preset_version: str='', factor_schema_version: str='', metadata: dict[str, Any] | None=None) -> None:
        self._store.write_governed_decision(
            decision_id=decision_id,
            domain=self._domain(domain),
            category=category,
            category_index=category_index,
            recommended_action=recommended_action,
            recommended_index=recommended_index,
            confidence=confidence,
            probabilities=probabilities,
            factor_vector=factor_vector,
            factor_names=factor_names,
            source=source,
            scorer_version=scorer_version,
            preset_version=preset_version,
            factor_schema_version=factor_schema_version,
            metadata=metadata,
        )

    def write_observation(self, observation_id: str, domain: str, category: str, recommended_action: str, confidence: float, source_route: str, scorer_version: str, factor_schema_version: str, entity_id: str | None=None, factor_vector: list[float] | None=None, factor_names: list[str] | None=None, metadata: dict[str, Any] | None=None) -> None:
        self._store.write_observation(
            observation_id=observation_id,
            domain=self._domain(domain),
            category=category,
            recommended_action=recommended_action,
            confidence=confidence,
            source_route=source_route,
            scorer_version=scorer_version,
            factor_schema_version=factor_schema_version,
            entity_id=entity_id,
            factor_vector=factor_vector,
            factor_names=factor_names,
            metadata=metadata,
        )

    def append_evidence_receipt(self, receipt_intent_id: str, domain: str, decision_id: str, canonical_payload: dict[str, Any], actor: str, source_route: str, metadata: dict[str, Any] | None=None) -> tuple[int, str]:
        result: tuple[int, str] = self._store.append_evidence_receipt(
            receipt_intent_id=receipt_intent_id,
            domain=self._domain(domain),
            decision_id=decision_id,
            canonical_payload=canonical_payload,
            actor=actor,
            source_route=source_route,
            metadata=metadata,
        )
        return result

    def write_conservation_status(self, status_id: str, domain: str, V: int, q: float, alpha: float, theta_min: float, verified_count: int, correct_count: int, status: str, policy_version: str) -> None:
        self._store.write_conservation_status(
            status_id=status_id,
            domain=self._domain(domain),
            V=V,
            q=q,
            alpha=alpha,
            theta_min=theta_min,
            verified_count=verified_count,
            correct_count=correct_count,
            status=status,
            policy_version=policy_version,
        )

    def write_fingerprint(self, fingerprint_id: str, domain: str, factor_names: list[str], factor_stats: dict[str, Any], skipped_incompatible: int, window: int, metadata: dict[str, Any] | None=None) -> None:
        self._store.write_fingerprint(
            fingerprint_id=fingerprint_id,
            domain=self._domain(domain),
            factor_names=factor_names,
            factor_stats=factor_stats,
            skipped_incompatible=skipped_incompatible,
            window=window,
            metadata=metadata,
        )

    def write_centroid_checkpoint(self, checkpoint_id: str, domain: str, category: str, action: str, centroids: Any, decisions_count: int, verified_count: int, iks: float, shape: list[int], factor_names_hash: str, quality_window_size: int | None=None, quality_verified_count: int | None=None, quality_correct_count: int | None=None, rolling_accuracy: float | None=None, quality_window_end: str | None=None, quality_policy_version: str | None=None, metadata: dict[str, Any] | None=None, decision_id: str | None=None) -> None:
        self._store.write_centroid_checkpoint(
            checkpoint_id=checkpoint_id,
            domain=self._domain(domain),
            category=category,
            action=action,
            centroids=centroids,
            decisions_count=decisions_count,
            verified_count=verified_count,
            iks=iks,
            shape=shape,
            factor_names_hash=factor_names_hash,
            quality_window_size=quality_window_size,
            quality_verified_count=quality_verified_count,
            quality_correct_count=quality_correct_count,
            rolling_accuracy=rolling_accuracy,
            quality_window_end=quality_window_end,
            quality_policy_version=quality_policy_version,
            metadata=metadata,
            decision_id=decision_id,
        )

    def write_evolution_event(self, event_id: str, domain: str, event_type: str, rule_name: str, variant_id: str, source_copilot: str | None=None, source_rule: str | None=None, metric: float | None=None, shadow_batch_size: int | None=None, min_shadow_batches: int | None=None, metadata: dict[str, Any] | None=None, decision_id: str | None=None) -> None:
        self._store.write_evolution_event(
            event_id=event_id,
            domain=self._domain(domain),
            event_type=event_type,
            rule_name=rule_name,
            variant_id=variant_id,
            source_copilot=source_copilot,
            source_rule=source_rule,
            metric=metric,
            shadow_batch_size=shadow_batch_size,
            min_shadow_batches=min_shadow_batches,
            metadata=metadata,
            decision_id=decision_id,
        )

    def get_evolution_events(self, domain: str, **kwargs: Any) -> list[dict[str, Any]]:
        result = self._store.get_evolution_events(
            domain=self._domain(domain),
            **kwargs,
        )
        return self._rows(result)

    def write_transfer_pattern(self, pattern_id: str, source_domain: str, target_domain: str, pattern_type: str, factor_mapping: dict[str, Any], confidence: float, validation_status: str, conservation_status: str, source_rule: str | None=None, target_rule: str | None=None, source_fingerprint_id: str | None=None, evolution_event_id: str | None=None, metadata: dict[str, Any] | None=None) -> None:
        self._store.write_transfer_pattern(
            pattern_id=pattern_id,
            source_domain=self._domain(source_domain),
            target_domain=self._domain(target_domain),
            pattern_type=pattern_type,
            factor_mapping=factor_mapping,
            confidence=confidence,
            validation_status=validation_status,
            conservation_status=conservation_status,
            source_rule=source_rule,
            target_rule=target_rule,
            source_fingerprint_id=source_fingerprint_id,
            evolution_event_id=evolution_event_id,
            metadata=metadata,
        )

    def get_transfer_patterns(self, source_domain: str | None=None, target_domain: str | None=None) -> list[dict[str, Any]]:
        result = self._store.get_transfer_patterns(
            source_domain=(self._domain(source_domain) if source_domain is not None else None),
            target_domain=(self._domain(target_domain) if target_domain is not None else None),
        )
        if source_domain is None and target_domain is None:
            result = [
                row for row in result
                if isinstance(row.get("source_domain"), str)
                and row["source_domain"].startswith(self._prefix)
                and isinstance(row.get("target_domain"), str)
                and row["target_domain"].startswith(self._prefix)
            ]
        return self._rows(result)

    def decision_movement(self, domain: str, decision_id: str) -> list[dict[str, Any]]:
        result = self._store.decision_movement(
            domain=self._domain(domain),
            decision_id=decision_id,
        )
        return self._rows(result)

    def contextual_judgment(self, domain: str, entity_group: str, category: str) -> list[dict[str, Any]]:
        result = self._store.contextual_judgment(
            domain=self._domain(domain),
            entity_group=entity_group,
            category=category,
        )
        return self._rows(result)

    def promotion_basis(self, domain: str, rule_id: str) -> list[dict[str, Any]]:
        result = self._store.promotion_basis(
            domain=self._domain(domain),
            rule_id=rule_id,
        )
        return self._rows(result)

    def transfer_witness(self, source_domain: str, target_domain: str, pattern_id: str) -> list[dict[str, Any]]:
        result = self._store.transfer_witness(
            source_domain=self._domain(source_domain),
            target_domain=self._domain(target_domain),
            pattern_id=pattern_id,
        )
        return self._rows(result)

    def list_fingerprints(self, domain: str | None=None) -> list[dict[str, Any]]:
        result = self._store.list_fingerprints(
            domain=self._domain(domain) if domain is not None else None,
        )
        return self._rows(result)

    def get_latest_conservation_statuses(self, domains: list[str] | None=None) -> list[dict[str, Any]]:
        result = self._store.get_latest_conservation_statuses(
            domains=(
                [self._domain(domain) for domain in domains]
                if domains is not None else None
            ),
        )
        return self._rows(result)

    def get_iks_trajectory(self, domains: list[str] | None=None, start: float | None=None, end: float | None=None) -> list[dict[str, Any]]:
        result = self._store.get_iks_trajectory(
            domains=(
                [self._domain(domain) for domain in domains]
                if domains is not None else None
            ),
            start=start,
            end=end,
        )
        return self._rows(result)

    def link_entity(self, decision_id: str, entity_id: str, entity_type: str, domain: str) -> None:
        self._store.link_entity(
            decision_id=decision_id,
            entity_id=entity_id,
            entity_type=entity_type,
            domain=self._domain(domain),
        )

    def archive_decisions(self, domain: str, before: float, status_filter: str='pending', confirm_verified: bool=False) -> int:
        result: int = self._store.archive_decisions(
            domain=self._domain(domain),
            before=before,
            status_filter=status_filter,
            confirm_verified=confirm_verified,
        )
        return result

    def domain_scoped_reset(self, domain: str) -> None:
        self._store.domain_scoped_reset(self._domain(domain))


__all__ = ["GraphStoreNamespace"]
