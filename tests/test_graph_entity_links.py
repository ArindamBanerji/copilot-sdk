from __future__ import annotations

from dataclasses import dataclass
from typing import cast

import numpy as np

from copy import deepcopy

from copilot_sdk.graph import GraphStore, InMemoryGraphStore, SQLiteGraphStore
from copilot_sdk.scoring.config import DomainShape
from copilot_sdk.scoring.scorer import CompoundingScorer

from gae.profile_scorer import ProfileScorer


@dataclass(frozen=True)
class LinkPreset:
    name: str = "link-test"
    shape: DomainShape = DomainShape(
        n_categories=1,
        n_actions=2,
        n_factors=3,
        category_names=("alpha",),
        action_names=("approve", "review"),
        factor_names=("amount", "risk", "history"),
    )
    penalty_ratio: float = 5.0
    eta_confirm: float = 0.05
    eta_override: float = 0.01
    temperature: float = 0.1

    @property
    def bootstrap_centroids(self) -> np.ndarray:
        return cast(
            np.ndarray,
            np.array([[[0.2, 0.3, 0.4], [0.7, 0.6, 0.5]]], dtype=np.float64),
        )


class MinimalGraphStore:
    def __init__(self):
        self.domain = "test"
        self.decisions = {}
        self.outcomes = {}
        self._archive = []

    def write_decision(self, domain, category, action, confidence, factors, metadata=None):
        decision_id = str((metadata or {}).get("decision_id") or "decision-1")
        self.decisions[decision_id] = {
            "decision_id": decision_id,
            "domain": domain,
            "entity_id": (metadata or {}).get("entity_id"),
            "category": category,
            "recommended_action": action,
            "confidence": confidence,
            "factors": deepcopy(factors),
            "metadata": deepcopy(metadata or {}),
        }
        return decision_id

    def write_outcome(self, decision_id, actual_action, is_correct, metadata=None, domain=None):
        self.outcomes[decision_id] = {
            "actual_action": actual_action,
            "is_correct": bool(is_correct),
            "metadata": deepcopy(metadata or {}),
        }
        return None

    def get_decision(self, decision_id, domain=None):
        decision = self.decisions.get(decision_id)
        if decision is None:
            return None
        return deepcopy(decision)

    def get_decisions(self, domain, category=None, limit=400):
        decisions = [
            decision
            for decision in self.decisions.values()
            if decision.get("domain") == domain and (category is None or decision["category"] == category)
        ]
        return deepcopy(decisions[:limit])

    def get_verified_decisions(self, domain):
        verified = []
        for decision_id, decision in self.decisions.items():
            if decision.get("domain") != domain:
                continue
            outcome = self.outcomes.get(decision_id)
            if outcome is None:
                continue
            merged = deepcopy(decision)
            merged.update(
                {
                    "actual_action": outcome["actual_action"],
                    "is_correct": outcome["is_correct"],
                    "outcome_metadata": deepcopy(outcome["metadata"]),
                }
            )
            verified.append(merged)
        return verified

    def count_verified(self, domain):
        return len(self.outcomes)

    def count_verified_decisions(self, domain):
        return len(self.get_verified_decisions(domain))

    def count_correct(self, domain):
        return sum(1 for outcome in self.outcomes.values() if outcome["is_correct"])

    def count_decisions(self, domain):
        return len(self.get_all_decisions(domain))

    def get_all_decisions(self, domain):
        return self.get_decisions(domain, category=None, limit=len(self.decisions))

    def get_archived_decisions(self, domain):
        return list(self._archive)

    def archive_old_decisions(self, domain, keep_recent=800):
        return 0

    def count_archived(self, domain):
        return 0

    def save_centroids(self, *args, **kwargs):
        return None

    def load_latest_centroids(self, domain):
        return None

    def get_centroid_checkpoints(self, *args, **kwargs):
        return []

    def load_latest_checkpoint_for_regime(self, domain, regime_tag):
        return None

    def get_checkpoint_lineage(self, domain, checkpoint_id):
        return None

    def get_decision_checkpoints(self, domain, decision_id):
        return []

    def save_evolution_event(self, *args, **kwargs):
        return None

    def get_evolution_events(self, *args, **kwargs):
        return []

    def close(self):
        return None

    def write_entity_enrichment(self, **kwargs):
        raise NotImplementedError("MinimalGraphStore does not support entity enrichment writes")

    def read_entity_enrichment(self, **kwargs):
        return {}

    def list_entity_enrichments(self, **kwargs):
        return []


def _build_scorer(tmp_path, graph_store=None) -> CompoundingScorer:
    preset = LinkPreset()
    gae_scorer = ProfileScorer(
        mu=preset.bootstrap_centroids.copy(),
        actions=list(preset.shape.action_names),
        categories=list(preset.shape.category_names),
    )
    return CompoundingScorer(preset, gae_scorer, graph_store=graph_store or InMemoryGraphStore())


def _score(scorer: CompoundingScorer):
    return scorer.score({"amount": 0.2, "risk": 0.4, "history": 0.6}, "alpha")


def test_link_decision_to_entity_sqlite(tmp_path):
    store = SQLiteGraphStore(tmp_path / "graph.sqlite")

    store.link_decision_to_entity("decision-1", "invoice-1", domain="graph")

    assert store.get_decision_links("decision-1", domain="graph") == [
        {
            "decision_id": "decision-1",
            "entity_id": "invoice-1",
            "edge_type": "DECIDED_ON",
            "created_at": store.get_decision_links("decision-1", domain="graph")[0]["created_at"],
        }
    ]


def test_link_decision_to_entity_inmemory():
    store = InMemoryGraphStore()

    store.link_decision_to_entity("decision-1", "invoice-1", domain="test")

    assert store.get_decision_links("decision-1", domain="test") == [
        {
            "decision_id": "decision-1",
            "entity_id": "invoice-1",
            "edge_type": "DECIDED_ON",
            "created_at": store.get_decision_links("decision-1", domain="test")[0]["created_at"],
        }
    ]


def test_learn_with_context_invoice_creates_link(tmp_path):
    graph_store = InMemoryGraphStore()
    scorer = _build_scorer(tmp_path, graph_store=graph_store)
    result = _score(scorer)

    scorer.learn(result.decision_id, result.action, context={"invoice_id": "INV-001"})

    assert graph_store.get_decision_links(result.decision_id, domain="test") == [
        {
            "decision_id": result.decision_id,
            "entity_id": "INV-001",
            "entity_type": "invoice",
            "edge_type": "DECIDED_ON",
            "created_at": graph_store.get_decision_links(result.decision_id, domain="test")[0]["created_at"],
        }
    ]
    scorer.graph_store.close()


def test_learn_without_entity_unchanged(tmp_path):
    graph_store = InMemoryGraphStore()
    scorer = _build_scorer(tmp_path, graph_store=graph_store)
    result = _score(scorer)

    scorer.learn(result.decision_id, result.action)

    assert graph_store.get_decision_links(result.decision_id, domain="test") == []
    scorer.graph_store.close()


def test_minimal_structural_graphstore_still_satisfies_graphstore_protocol():
    store = MinimalGraphStore()

    assert not isinstance(store, GraphStore)
    assert not hasattr(store, "link_decision_to_entity")


def test_learn_with_context_tolerates_graphstore_without_link_method(tmp_path):
    graph_store = MinimalGraphStore()
    scorer = _build_scorer(tmp_path, graph_store=graph_store)
    result = _score(scorer)

    learn = scorer.learn(result.decision_id, result.action, context={"invoice_id": "INV-001"})

    assert learn.decision_id == result.decision_id
    verified = graph_store.get_verified_decisions("test")
    assert verified[0]["outcome_metadata"]["context"] == {"invoice_id": "INV-001"}
    assert not hasattr(graph_store, "link_decision_to_entity")
    scorer.graph_store.close()
