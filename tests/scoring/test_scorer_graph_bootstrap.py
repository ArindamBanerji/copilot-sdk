"""GraphStore bootstrap coverage for verified-decision scorer replay."""
from __future__ import annotations

import hashlib
import json
from itertools import count
from types import SimpleNamespace
from typing import Any, cast

import numpy as np
import pytest

from copilot_sdk.graph.memory_store import InMemoryGraphStore
from copilot_sdk.scoring.presets.trading import TradingPreset
from copilot_sdk.scoring.scorer import CompoundingScorer


DOMAIN = "trading"


def _bootstrap() -> np.ndarray:
    return cast(
        np.ndarray,
        np.asarray(TradingPreset().bootstrap_centroids, dtype=np.float64).copy(),
    )


def _factors(index: int) -> dict[str, float]:
    names = TradingPreset().shape.factor_names
    return {
        name: min(0.95, 0.15 + ((index + offset) % 7) * 0.1)
        for offset, name in enumerate(names)
    }


def _seed_verified(
    store: InMemoryGraphStore,
    *,
    count: int = 10,
    timestamps: list[float] | None = None,
    start: int = 0,
) -> None:
    preset = TradingPreset()
    category = preset.shape.category_names[0]
    predicted = preset.shape.action_names[0]
    alternative = preset.shape.action_names[1]
    for index in range(start, start + count):
        factors = _factors(index)
        timestamp_index = index - start
        created_at = timestamps[timestamp_index] if timestamps is not None else 1_000.0 + index
        decision_id = store.write_decision(
            DOMAIN,
            category=category,
            action=predicted,
            confidence=0.9,
            factors=factors,
            metadata={
                "decision_id": f"bootstrap-{index}",
                "category_index": 0,
                "recommended_index": 0,
                "factor_vector": [factors[name] for name in preset.shape.factor_names],
                "created_at": created_at,
            },
        )
        correct = index % 2 == 0
        store.write_outcome(
            decision_id,
            actual_action=predicted if correct else alternative,
            is_correct=correct,
            metadata={
                "actual_index": 0 if correct else 1,
                "verified_at": created_at + 0.5,
            },
            domain=DOMAIN,
        )


def _scorer(store: InMemoryGraphStore) -> CompoundingScorer:
    return CompoundingScorer.from_preset(
        DOMAIN,
        graph_store=store,
        profile="test",
        enable_rl=False,
    )


def _copy_verified(source: InMemoryGraphStore, target: InMemoryGraphStore) -> None:
    for row in source.get_verified_decisions(DOMAIN):
        target.write_decision(
            DOMAIN,
            category=str(row["category"]),
            action=str(row["recommended_action"]),
            confidence=float(row["confidence"]),
            factors=dict(row["factors"]),
            metadata={
                "decision_id": str(row["decision_id"]),
                "category_index": int(row["category_index"]),
                "recommended_index": int(row["recommended_index"]),
                "factor_vector": list(row["factor_vector"]),
                "created_at": row["created_at"],
            },
        )
        target.write_outcome(
            str(row["decision_id"]),
            actual_action=str(row["actual_action"]),
            is_correct=bool(row["is_correct"]),
            metadata={
                "actual_index": int(row["actual_index"]),
                "verified_at": row["verified_at"],
            },
            domain=DOMAIN,
        )


def test_from_preset_cold_start_empty_graph() -> None:
    scorer = _scorer(InMemoryGraphStore(domain=DOMAIN))

    assert scorer._cold_start is True
    np.testing.assert_allclose(scorer._scorer.centroids, _bootstrap())
    assert scorer._scorer.decision_count == 0


def test_from_preset_centroids_only() -> None:
    store = InMemoryGraphStore(domain=DOMAIN)
    restored = _bootstrap() + 0.01
    store.save_centroids(DOMAIN, "", restored, metadata={"factor_names_hash": ""})

    scorer = _scorer(store)

    assert scorer._cold_start is False
    np.testing.assert_allclose(scorer._scorer.centroids, restored)
    assert scorer._scorer.decision_count == 0


def test_from_preset_replay_verified(monkeypatch: pytest.MonkeyPatch) -> None:
    normal_store = InMemoryGraphStore(domain=DOMAIN)
    normal = _scorer(normal_store)
    category = TradingPreset().shape.category_names[0]
    actions = TradingPreset().shape.action_names
    identifiers = count()
    monkeypatch.setattr(
        "copilot_sdk.scoring.scorer.uuid.uuid4",
        lambda: SimpleNamespace(hex=f"{0xABC000000000 + next(identifiers):012x}" + "f" * 20),
    )
    for index in range(10):
        result = normal.score(_factors(index), category)
        actual_action = result.action if index % 2 == 0 else next(
            action for action in actions if action != result.action
        )
        normal.learn(result.decision_id, actual_action)

    replay_store = InMemoryGraphStore(domain=DOMAIN)
    _copy_verified(normal_store, replay_store)
    replayed = _scorer(replay_store)

    assert replayed._cold_start is False
    assert replayed._scorer.decision_count == 10
    assert np.allclose(replayed._scorer.centroids, normal._scorer.centroids, atol=1e-10)


def test_from_preset_replay_idempotent() -> None:
    store = InMemoryGraphStore(domain=DOMAIN)
    _seed_verified(store)

    first = _scorer(store)
    second = _scorer(store)

    assert first._scorer.decision_count == second._scorer.decision_count == 10
    assert np.allclose(first._scorer.centroids, second._scorer.centroids, atol=1e-10)


def test_from_preset_incompatible_checkpoint_replays() -> None:
    store = InMemoryGraphStore(domain=DOMAIN)
    _seed_verified(store)
    store.save_centroids(
        DOMAIN,
        "",
        np.zeros_like(_bootstrap()),
        metadata={"factor_names_hash": "incompatible"},
    )

    replayed = _scorer(store)
    expected_store = InMemoryGraphStore(domain=DOMAIN)
    _seed_verified(expected_store)
    expected = _scorer(expected_store)

    assert replayed._cold_start is False
    assert np.allclose(replayed._scorer.centroids, expected._scorer.centroids, atol=1e-10)


def test_from_preset_empty_verified_with_centroids() -> None:
    store = InMemoryGraphStore(domain=DOMAIN)
    restored = _bootstrap() * 0.9
    store.save_centroids(DOMAIN, "", restored)

    scorer = _scorer(store)

    assert scorer._cold_start is False
    assert scorer._scorer.decision_count == 0
    np.testing.assert_allclose(scorer._scorer.centroids, restored)


def test_from_preset_replay_preserves_decision_count() -> None:
    store = InMemoryGraphStore(domain=DOMAIN)
    _seed_verified(store, count=7)

    scorer = _scorer(store)

    assert scorer._scorer.decision_count == len(store.get_verified_decisions(DOMAIN))


def test_from_preset_replay_chronological() -> None:
    class ReverseVerifiedStore(InMemoryGraphStore):
        def get_verified_decisions(
            self,
            domain: str,
            *,
            offset: int = 0,
            limit: int | None = None,
            chronological: bool = False,
            verified_after: tuple[float, str] | None = None,
        ) -> list[dict[str, Any]]:
            return list(reversed(super().get_verified_decisions(
                domain, offset=offset, limit=limit, chronological=chronological,
                verified_after=verified_after,
            )))

    timestamps = [3_000.0, 1_000.0, 2_000.0]
    reversed_store = ReverseVerifiedStore(domain=DOMAIN)
    _seed_verified(reversed_store, count=3, timestamps=timestamps)
    chronological_store = InMemoryGraphStore(domain=DOMAIN)
    _seed_verified(chronological_store, count=3, timestamps=timestamps)

    replayed = _scorer(reversed_store)
    expected = _scorer(chronological_store)

    assert np.allclose(replayed._scorer.centroids, expected._scorer.centroids, atol=1e-10)


def test_checkpoint_watermark_replays_only_later_verified_decisions() -> None:
    store = InMemoryGraphStore(domain=DOMAIN)
    _seed_verified(store, count=5)
    at_checkpoint = _scorer(store)
    preset = TradingPreset()
    factor_hash = hashlib.sha256(
        json.dumps(
            list(preset.shape.factor_names), separators=(",", ":")
        ).encode("utf-8")
    ).hexdigest()
    store.write_centroid_checkpoint(
        checkpoint_id="trading:checkpoint:watermark",
        domain=DOMAIN,
        category=preset.shape.category_names[0],
        action=preset.shape.action_names[0],
        centroids=at_checkpoint._scorer.centroids,
        decisions_count=5,
        verified_count=5,
        iks=0.0,
        shape=list(at_checkpoint._scorer.centroids.shape),
        factor_names_hash=factor_hash,
        metadata={
            "decision_count": 5,
            "replay_watermark_verified_count": 5,
            "replay_watermark_decision_id": "bootstrap-4",
        },
        decision_id="bootstrap-4",
    )
    _seed_verified(store, count=3, start=5)

    restored = _scorer(store)
    expected_store = InMemoryGraphStore(domain=DOMAIN)
    _seed_verified(expected_store, count=8)
    expected = _scorer(expected_store)

    assert restored._scorer.decision_count == 8
    np.testing.assert_allclose(
        restored._scorer.centroids,
        expected._scorer.centroids,
        atol=1e-10,
    )


def test_checkpoint_restore_reads_post_watermark_in_bounded_batches() -> None:
    class TrackingStore(InMemoryGraphStore):
        verified_reads: list[tuple[int, int | None, tuple[float, str] | None]]

        def __init__(self) -> None:
            super().__init__(domain=DOMAIN)
            self.verified_reads = []

        def get_verified_decisions(
            self,
            domain: str,
            *,
            offset: int = 0,
            limit: int | None = None,
            chronological: bool = False,
            verified_after: tuple[float, str] | None = None,
        ) -> list[dict[str, Any]]:
            self.verified_reads.append((offset, limit, verified_after))
            return super().get_verified_decisions(
                domain, offset=offset, limit=limit, chronological=chronological,
                verified_after=verified_after,
            )

    store = TrackingStore()
    _seed_verified(store, count=1_000)
    at_checkpoint = _scorer(store)
    assert at_checkpoint._save_centroids_checkpoint(
        decision_id="bootstrap-999",
        category=TradingPreset().shape.category_names[0],
        action=TradingPreset().shape.action_names[0],
        iks=0.0,
        replay_verified_at=1_999.5,
    ) is True
    _seed_verified(store, count=1_000, start=1_000)
    store.verified_reads.clear()

    restored = _scorer(store)

    assert restored._scorer.decision_count == 2_000
    cursor = (1_999.5, "bootstrap-999")
    assert store.verified_reads == [(0, 1_000, cursor), (1_000, 1_000, cursor)]


def test_checkpoint_cursor_replays_late_verified_decision() -> None:
    class TrackingStore(InMemoryGraphStore):
        replayed_pages: list[list[str]]

        def __init__(self) -> None:
            super().__init__(domain=DOMAIN)
            self.replayed_pages = []

        def get_verified_decisions(
            self,
            domain: str,
            *,
            offset: int = 0,
            limit: int | None = None,
            chronological: bool = False,
            verified_after: tuple[float, str] | None = None,
        ) -> list[dict[str, Any]]:
            rows = super().get_verified_decisions(
                domain,
                offset=offset,
                limit=limit,
                chronological=chronological,
                verified_after=verified_after,
            )
            if verified_after is not None:
                self.replayed_pages.append([str(row["decision_id"]) for row in rows])
            return rows

    store = TrackingStore()
    preset = TradingPreset()
    category = preset.shape.category_names[0]
    predicted = preset.shape.action_names[0]
    decision_ids: list[str] = []
    for index in range(5):
        factors = _factors(index)
        decision_ids.append(store.write_decision(
            DOMAIN,
            category,
            predicted,
            0.9,
            factors,
            metadata={
                "decision_id": f"late-{index + 1}",
                "category_index": 0,
                "recommended_index": 0,
                "factor_vector": [factors[name] for name in preset.shape.factor_names],
                "created_at": 1_000.0 + index,
            },
        ))
    for index in (0, 1, 2, 4):
        store.write_outcome(
            decision_ids[index],
            predicted,
            True,
            metadata={"actual_index": 0, "verified_at": 2_000.0 + index},
            domain=DOMAIN,
        )
    checkpoint_scorer = _scorer(store)
    assert checkpoint_scorer._save_centroids_checkpoint(
        decision_id=decision_ids[4],
        category=category,
        action=predicted,
        iks=0.0,
        replay_verified_at=2_004.0,
    ) is True

    store.write_outcome(
        decision_ids[3],
        predicted,
        True,
        metadata={"actual_index": 0, "verified_at": 2_005.0},
        domain=DOMAIN,
    )
    store.replayed_pages.clear()

    restored = _scorer(store)

    assert restored._scorer.decision_count == 5
    assert store.replayed_pages == [[decision_ids[3]]]


def test_checkpoint_replay_uses_verification_order(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    store = InMemoryGraphStore(domain=DOMAIN)
    preset = TradingPreset()
    category = preset.shape.category_names[0]
    predicted, alternative = preset.shape.action_names[:2]
    live = _scorer(store)

    baseline = live.score(_factors(0), category)
    live.learn(baseline.decision_id, baseline.action, persist_artifacts=False)
    baseline_centroids = live._scorer.centroids.copy()
    cursor_time = live._last_checkpoint_verified_at
    assert cursor_time is not None
    assert live._save_centroids_checkpoint(
        decision_id=baseline.decision_id,
        category=category,
        action=baseline.action,
        iks=0.0,
        replay_verified_at=cursor_time,
    ) is True

    decision_ids: list[str] = []
    for suffix, factor_index, created_at in (
        ("a", 1, cursor_time + 1.0),
        ("b", 2, cursor_time + 2.0),
    ):
        factors = _factors(factor_index)
        decision_ids.append(store.write_decision(
            DOMAIN,
            category,
            predicted,
            0.9,
            factors,
            metadata={
                "decision_id": f"verification-order-{suffix}",
                "category_index": 0,
                "recommended_index": 0,
                "factor_vector": [factors[name] for name in preset.shape.factor_names],
                "created_at": created_at,
            },
        ))

    reference = _scorer(store)
    monkeypatch.setattr(
        "copilot_sdk.scoring.scorer.time.time",
        lambda: cursor_time + 10.0,
    )  # MOCK-OK: deterministic verification timestamp; scorer and store are real.
    reference.learn(decision_ids[1], predicted, persist_artifacts=False)
    monkeypatch.setattr(
        "copilot_sdk.scoring.scorer.time.time",
        lambda: cursor_time + 20.0,
    )  # MOCK-OK: deterministic verification timestamp; scorer and store are real.
    reference.learn(decision_ids[0], alternative, persist_artifacts=False)
    expected_centroids = reference._scorer.centroids.copy()

    rows = {str(row["decision_id"]): row for row in store.get_verified_decisions(DOMAIN)}
    assert rows[decision_ids[0]]["created_at"] < rows[decision_ids[1]]["created_at"]
    assert rows[decision_ids[1]]["verified_at"] < rows[decision_ids[0]]["verified_at"]

    store.save_centroids(DOMAIN, "", baseline_centroids)
    replayed = _scorer(store)

    np.testing.assert_allclose(replayed._scorer.centroids, expected_centroids, atol=1e-10)


def test_old_checkpoint_without_cursor_rebuilds_full_history() -> None:
    store = InMemoryGraphStore(domain=DOMAIN)
    _seed_verified(store, count=5)
    preset = TradingPreset()
    factor_hash = hashlib.sha256(
        json.dumps(list(preset.shape.factor_names), separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    store.write_centroid_checkpoint(
        checkpoint_id="trading:checkpoint:legacy",
        domain=DOMAIN,
        category=preset.shape.category_names[0],
        action=preset.shape.action_names[0],
        centroids=np.zeros_like(_bootstrap()),
        decisions_count=5,
        verified_count=5,
        iks=0.0,
        shape=list(_bootstrap().shape),
        factor_names_hash=factor_hash,
        metadata={"replay_watermark_verified_count": 5},
        decision_id="bootstrap-4",
    )

    restored = _scorer(store)
    expected_store = InMemoryGraphStore(domain=DOMAIN)
    _seed_verified(expected_store, count=5)
    expected = _scorer(expected_store)

    assert restored._scorer.decision_count == 5
    np.testing.assert_allclose(restored._scorer.centroids, expected._scorer.centroids)
