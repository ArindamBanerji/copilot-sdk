from __future__ import annotations

import inspect

from copilot_sdk.graph import GraphStore, L5LearningStore, ProtocolV2GraphStore


L5_STORAGE_METHODS = [
    "update_centroid",
    "get_centroids",
    "update_dk_weights",
    "get_dk_weights",
    "update_conservation_state",
    "get_conservation_state",
]


def test_l5_learning_store_exists_and_has_required_methods() -> None:
    for method in [*L5_STORAGE_METHODS, "count_categories_with_n"]:
        assert hasattr(L5LearningStore, method)


def test_l5_learning_store_method_signatures() -> None:
    assert list(inspect.signature(L5LearningStore.update_centroid).parameters) == [
        "self",
        "domain",
        "category",
        "action",
        "centroid_vector",
        "delta_norm",
        "caused_by_decision_id",
    ]
    assert list(inspect.signature(L5LearningStore.get_centroids).parameters) == ["self", "domain"]
    assert list(inspect.signature(L5LearningStore.update_dk_weights).parameters) == [
        "self",
        "domain",
        "weight_tensor",
        "n_decisions_used",
        "computed_at",
        "welford_state",
        "n_confirmed",
        "n_overridden",
        "entity_group",
    ]
    dk_params = inspect.signature(L5LearningStore.update_dk_weights).parameters
    assert dk_params["welford_state"].kind is inspect.Parameter.KEYWORD_ONLY
    assert dk_params["n_confirmed"].kind is inspect.Parameter.KEYWORD_ONLY
    assert dk_params["n_overridden"].kind is inspect.Parameter.KEYWORD_ONLY
    assert dk_params["entity_group"].kind is inspect.Parameter.KEYWORD_ONLY
    assert list(inspect.signature(L5LearningStore.get_dk_weights).parameters) == ["self", "domain"]
    assert list(inspect.signature(L5LearningStore.update_conservation_state).parameters) == [
        "self",
        "domain",
        "status",
        "alpha",
        "q",
        "V",
        "theta_min",
        "product",
        "categories_total",
        "categories_with_data",
        "baseline_product",
        "relative_threshold",
        "complacency_flag",
        "caused_by_decision_id",
        "old_status",
    ]
    assert list(inspect.signature(L5LearningStore.get_conservation_state).parameters) == ["self", "domain"]
    assert list(inspect.signature(L5LearningStore.count_categories_with_n).parameters) == [
        "self",
        "domain",
        "n",
    ]
    assert inspect.signature(L5LearningStore.count_categories_with_n).parameters["n"].default == 1


def test_l5_methods_are_not_added_to_graphstore_or_protocol_v2() -> None:
    for method in L5_STORAGE_METHODS:
        assert not hasattr(GraphStore, method)
        assert not hasattr(ProtocolV2GraphStore, method)
    assert not hasattr(GraphStore, "count_categories_with_n")
    assert not hasattr(ProtocolV2GraphStore, "count_categories_with_n")


def test_minimal_graphstore_does_not_need_l5_methods() -> None:
    class MinimalGraphStore:
        def write_decision(self, domain, category, action, confidence, factors, metadata=None):
            return "DEC-1"

        def write_outcome(self, decision_id, actual_action, is_correct, metadata=None):
            return None

        def get_decision(self, decision_id):
            return None

        def get_decisions(self, domain, category=None, limit=400):
            return []

        def get_all_decisions(self, domain):
            return []

        def get_verified_decisions(self, domain):
            return []

        def count_verified(self, domain):
            return 0

        def count_correct(self, domain):
            return 0

        def count_decisions(self, domain):
            return 0

        def save_centroids(self, domain, category, centroids, metadata=None, **kwargs):
            return None

        def load_latest_centroids(self, domain):
            return None

        def get_centroid_checkpoints(self, domain, **kwargs):
            return []

        def archive_old_decisions(self, domain, keep_recent=800):
            return 0

        def count_archived(self, domain):
            return 0

        def close(self):
            return None

        def write_entity_enrichment(self, **kwargs):
            raise NotImplementedError("MinimalGraphStore does not support entity enrichment writes")

        def read_entity_enrichment(self, **kwargs):
            return {}

        def list_entity_enrichments(self, **kwargs):
            return []

    assert isinstance(MinimalGraphStore(), GraphStore)
    assert not isinstance(MinimalGraphStore(), L5LearningStore)


def test_l5_signatures_do_not_include_welford_algorithm_fields() -> None:
    forbidden = {"confirmed_mean", "overridden_mean", "m2", "variance"}
    for method_name in [
        "update_centroid",
        "get_centroids",
        "get_dk_weights",
        "update_conservation_state",
        "get_conservation_state",
        "count_categories_with_n",
    ]:
        signature = inspect.signature(getattr(L5LearningStore, method_name))
        assert forbidden.isdisjoint(signature.parameters)


def test_dk_signature_uses_batch_tensor_and_support_count() -> None:
    signature = inspect.signature(L5LearningStore.update_dk_weights)
    assert "weight_tensor" in signature.parameters
    assert "n_decisions_used" in signature.parameters
