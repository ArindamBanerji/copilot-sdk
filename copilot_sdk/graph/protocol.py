"""Public graph persistence protocol for copilot decisions."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class GraphStore(Protocol):
    """Domain-scoped decision/outcome persistence contract."""

    def write_decision(
        self,
        domain: str,
        category: str,
        action: str,
        confidence: float,
        factors: dict[str, Any],
        metadata: dict[str, Any] | None = None,
    ) -> str:
        ...

    def write_outcome(
        self,
        decision_id: str,
        actual_action: str,
        is_correct: bool,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        ...

    def get_decision(self, decision_id: str) -> dict[str, Any] | None:
        ...

    def get_decisions(
        self,
        domain: str,
        category: str | None = None,
        limit: int = 400,
    ) -> list[dict[str, Any]]:
        ...

    def get_all_decisions(self, domain: str) -> list[dict[str, Any]]:
        ...

    def get_verified_decisions(self, domain: str) -> list[dict[str, Any]]:
        ...

    def count_verified(self, domain: str) -> int:
        ...

    def count_correct(self, domain: str) -> int:
        ...

    def count_decisions(self, domain: str) -> int:
        ...

    def save_centroids(
        self,
        domain: str,
        category: str,
        centroids: Any,
        metadata: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> None:
        ...

    def load_latest_centroids(self, domain: str) -> Any | None:
        ...

    def get_centroid_checkpoints(
        self,
        domain: str,
        **kwargs: Any,
    ) -> list[dict[str, Any]]:
        ...

    def archive_old_decisions(self, domain: str, keep_recent: int = 800) -> int:
        ...

    def count_archived(self, domain: str) -> int:
        ...

    def close(self) -> None:
        ...


@runtime_checkable
class ProtocolV2GraphStore(GraphStore, Protocol):
    """Governed-memory GraphStore extension.

    Keep this separate from ``GraphStore`` so legacy scorer/entity-link helpers
    can still satisfy the narrow runtime persistence contract structurally.
    """

    def write_governed_decision(
        self,
        decision_id: str,
        domain: str,
        category: str,
        category_index: int,
        recommended_action: str,
        recommended_index: int,
        confidence: float,
        probabilities: list[float],
        factor_vector: list[float],
        factor_names: list[str],
        source: str = "score",
        scorer_version: str = "",
        preset_version: str = "",
        factor_schema_version: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> None:
        ...

    def write_observation(
        self,
        observation_id: str,
        domain: str,
        category: str,
        recommended_action: str,
        confidence: float,
        source_route: str,
        scorer_version: str,
        factor_schema_version: str,
        entity_id: str | None = None,
        factor_vector: list[float] | None = None,
        factor_names: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        ...

    def append_evidence_receipt(
        self,
        receipt_intent_id: str,
        domain: str,
        decision_id: str,
        canonical_payload: dict[str, Any],
        actor: str,
        source_route: str,
        metadata: dict[str, Any] | None = None,
    ) -> tuple[int, str]:
        ...

    def write_conservation_status(
        self,
        status_id: str,
        domain: str,
        V: int,
        q: float,
        alpha: float,
        theta_min: float,
        verified_count: int,
        correct_count: int,
        status: str,
        policy_version: str,
    ) -> None:
        ...

    def write_fingerprint(
        self,
        fingerprint_id: str,
        domain: str,
        factor_names: list[str],
        factor_stats: dict[str, Any],
        skipped_incompatible: int,
        window: int,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        ...

    def write_centroid_checkpoint(
        self,
        checkpoint_id: str,
        domain: str,
        category: str,
        action: str,
        centroids: Any,
        decisions_count: int,
        verified_count: int,
        iks: float,
        shape: list[int],
        factor_names_hash: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        ...

    def write_evolution_event(
        self,
        event_id: str,
        domain: str,
        event_type: str,
        rule_name: str,
        variant_id: str,
        source_copilot: str | None = None,
        source_rule: str | None = None,
        metric: float | None = None,
        shadow_batch_size: int | None = None,
        min_shadow_batches: int | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        ...

    def link_entity(
        self,
        decision_id: str,
        entity_id: str,
        entity_type: str,
        domain: str,
    ) -> None:
        ...

    def archive_decisions(
        self,
        domain: str,
        before: float,
        status_filter: str = "pending",
        confirm_verified: bool = False,
    ) -> int:
        ...

    def domain_scoped_reset(self, domain: str) -> None:
        ...

    def count_verified_decisions(self, domain: str) -> int:
        ...


@runtime_checkable
class L5LearningStore(Protocol):
    """L5 Design Spec v5.0 learning-state persistence contract.

    This protocol is intentionally separate from ``GraphStore`` and
    ``ProtocolV2GraphStore``. Minimal decision stores are not required to
    implement L5 learning state.
    """

    def update_centroid(
        self,
        domain: str,
        category: str,
        action: str,
        centroid_vector: list[float],
        delta_norm: float,
        caused_by_decision_id: str | None = None,
    ) -> None:
        ...

    def get_centroids(self, domain: str) -> list[dict[str, object]]:
        ...

    def update_dk_weights(
        self,
        domain: str,
        weight_tensor: list[list[float]],
        n_decisions_used: int,
        computed_at: float,
        *,
        welford_state: dict[str, object] | None = None,
        n_confirmed: int | None = None,
        n_overridden: int | None = None,
        entity_group: str | None = None,
    ) -> None:
        """Persist a batch DKWeight tensor and its decision support count."""
        ...

    def get_dk_weights(self, domain: str) -> dict[str, object] | None:
        ...

    def update_conservation_state(
        self,
        domain: str,
        status: str,
        alpha: float,
        q: float,
        V: int,
        theta_min: float,
        product: float,
        categories_total: int,
        categories_with_data: int,
        baseline_product: float,
        relative_threshold: float,
        complacency_flag: str,
        caused_by_decision_id: str | None = None,
        old_status: str | None = None,
    ) -> str:
        """Persist L5 conservation state; complacency_flag is TEXT advisory."""
        ...

    def get_conservation_state(
        self,
        domain: str,
    ) -> dict | None:
        ...

    def count_categories_with_n(self, domain: str, n: int = 1) -> int:
        ...
