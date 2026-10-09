"""Exercise timestamp boundaries with real stored decisions and live consumers."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pytest

from copilot_sdk.connectors.airflow_connector import AirflowConnector
from copilot_sdk.demo.bundle import restore_bundle_if_empty
from copilot_sdk.enterprise.process_ingest import ProcessExportIngester
from copilot_sdk.graph.legacy_signal_filter import LegacySignalFilteringGraphStore
from copilot_sdk.graph.memory_store import InMemoryGraphStore
from copilot_sdk.migrate.verify_state import replay_decisions
from copilot_sdk.reporting.weekly import WeeklyReportGenerator
from copilot_sdk.scoring.presets.trading import TradingPreset
from copilot_sdk.scoring.scorer import CompoundingScorer
from copilot_sdk.transfer.registry import TransferPattern

EPOCH = 1705314600.0
ISO = "2024-01-15T10:30:00Z"


class ISOReadbackMemoryStore(InMemoryGraphStore):
    """Real memory persistence with historical ISO serialization on decision reads.

    Writes, verification, counts, and every other capability are inherited. Only
    the presentation of actual stored timestamps changes; no rows are invented.
    """

    @staticmethod
    def _serialize(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [{**row, "created_at": datetime.fromtimestamp(row["created_at"], timezone.utc).isoformat()}
                for row in rows]

    def get_all_decisions(self, domain: str) -> list[dict[str, Any]]:
        return self._serialize(super().get_all_decisions(domain))

    def get_verified_decisions(self, domain: str) -> list[dict[str, Any]]:
        return self._serialize(super().get_verified_decisions(domain))


def _write(store: InMemoryGraphStore, decision_id: str, timestamp: float | str,
           *, legacy: bool = False) -> str:
    metadata: dict[str, Any] = {"decision_id": decision_id, "created_at": timestamp}
    if legacy:
        metadata.update(signal_detail="legacy", signal_timestamp=ISO)
    result: str = store.write_decision("trading", "trend_following", "strong_execution", 0.9,
                                      {"signal_alignment": 0.8}, metadata)
    return result


def test_memory_decision_and_outcome_accept_iso_metadata() -> None:
    store = InMemoryGraphStore(domain="trading")
    identifier = _write(store, "iso", ISO)
    store.write_outcome(identifier, "strong_execution", True,
                        {"verified_at": "2024-01-15T16:00:01+05:30"}, domain="trading")
    row = store.get_verified_decisions("trading")[0]
    assert row["created_at"] == EPOCH
    assert row["verified_at"] == EPOCH + 1
    assert isinstance(row["created_at"], float)
    assert isinstance(row["verified_at"], float)


def test_memory_observation_accepts_iso_metadata() -> None:
    store = InMemoryGraphStore(domain="trading")
    store.write_observation("obs", "trading", "trend_following", "strong_execution", 0.9,
                            "preview", "v1", "v1", metadata={"created_at": ISO})
    # The protocol has no observation read method; inspect the persisted record.
    row = store._observations["obs"]
    assert row["created_at"] == EPOCH


def test_memory_checkpoint_accepts_iso_created_at() -> None:
    store = InMemoryGraphStore(domain="trading")
    store.save_centroids("trading", "trend_following", [[0.5]], created_at=ISO)
    row = store.get_centroid_checkpoints("trading")[0]
    assert row["created_at"] == EPOCH


def test_legacy_filter_orders_iso_readback_before_pagination() -> None:
    store = ISOReadbackMemoryStore(domain="trading")
    _write(store, "last", EPOCH + 1)
    _write(store, "b", EPOCH)
    _write(store, "a", EPOCH)
    _write(store, "hidden", EPOCH - 1, legacy=True)
    assert all(isinstance(row["created_at"], str) for row in store.get_all_decisions("trading"))
    filtered = LegacySignalFilteringGraphStore(store)
    assert [row["decision_id"] for row in filtered.get_decisions("trading")] == ["a", "b", "last"]
    assert [row["decision_id"] for row in filtered.get_decisions("trading", offset=1, limit=1)] == ["b"]
    assert filtered.get_decisions("trading", limit=0) == []


def test_weekly_report_windows_iso_readback_with_real_scorer() -> None:
    store = ISOReadbackMemoryStore(domain="trading")
    for identifier, timestamp in [("old", EPOCH - 8 * 86400), ("new", EPOCH)]:
        _write(store, identifier, timestamp)
        store.write_outcome(identifier, "strong_execution", True, domain="trading")
    scorer = CompoundingScorer.from_preset("trading", graph_store=store, profile="test", enable_rl=False)
    report = WeeklyReportGenerator(store, scorer, "trading").generate(period_days=7)
    assert report.period_end == EPOCH
    assert report.total_decisions == report.total_verified == 1
    assert report.overall_accuracy == 1.0


def test_bundle_normalizes_decision_outcome_and_checkpoint_timestamps(tmp_path: Path) -> None:
    path = tmp_path / "bundle.json"
    path.write_text(json.dumps({
        "domain": "demo",
        "decisions": [{"decision_id": "d1", "category": "risk", "recommended_action": "approve",
                       "factors": {"risk": 0.5}, "factor_names": ["risk"], "created_at": ISO,
                       "verified": True, "actual_action": "approve", "is_correct": True,
                       "verified_at": "2024-01-15T10:30:01Z"}],
        "centroid_checkpoints": [{"category": "risk", "centroids": [[0.5]], "created_at": ISO}],
    }), encoding="utf-8")
    store = InMemoryGraphStore(domain="demo")
    report = restore_bundle_if_empty(store, path, domain="demo")
    assert report.fully_restored
    row = store.get_verified_decisions("demo")[0]
    assert row["created_at"] == EPOCH
    assert row["verified_at"] == EPOCH + 1
    assert store.get_centroid_checkpoints("demo")[0]["created_at"] == EPOCH


def test_migration_replay_iso_and_numeric_rows_produce_same_state() -> None:
    shape = TradingPreset().shape
    numeric = [{
        "decision_id": f"d{index}", "domain": "trading", "category": shape.category_names[0],
        "category_index": 0, "recommended_action": shape.action_names[0], "recommended_index": 0,
        "actual_action": shape.action_names[0], "confidence": 0.8,
        "factor_vector_json": json.dumps([0.3 + index * 0.2] * shape.n_factors),
        "probabilities_json": json.dumps([1.0] + [0.0] * (shape.n_actions - 1)),
        "created_at": EPOCH + index,
    } for index in range(2)]
    historical = [{**row, "created_at": datetime.fromtimestamp(row["created_at"], timezone.utc).isoformat()}
                  for row in reversed(numeric)]
    assert replay_decisions(historical, {}, "trading") == replay_decisions(numeric, {}, "trading")


def test_transfer_pattern_deserialization_accepts_iso() -> None:
    pattern = TransferPattern.from_dict({"pattern_id": "p1", "created_at": ISO})
    assert pattern.created_at == EPOCH
    assert pattern.to_dict()["created_at"] == EPOCH


def test_process_ingestion_orders_mixed_timestamps_by_instant() -> None:
    result = ProcessExportIngester().ingest([
        {"case_id": "c1", "activity": "last", "timestamp": "2024-01-15T02:30:01-08:00"},
        {"case_id": "c1", "activity": "first", "timestamp": "2024-01-15T16:00:00+05:30"},
        {"case_id": "c1", "activity": "middle", "timestamp": EPOCH + 0.5},
    ])
    assert [edge["to"] for edge in result["context_graph"]["relationships"]] == [
        "activity:first", "activity:middle", "activity:last",
    ]


def test_airflow_cutoff_compares_instants_not_iso_text(monkeypatch: pytest.MonkeyPatch) -> None:
    cutoff = datetime.now(timezone.utc) - timedelta(days=7)
    old = (cutoff - timedelta(hours=1)).astimezone(timezone(timedelta(hours=14))).isoformat()
    recent = (cutoff + timedelta(hours=1)).astimezone(timezone(timedelta(hours=-12))).isoformat()
    connector = AirflowConnector(token="test")
    # Only the external HTTP response is replaced; filtering/statistics are live.
    monkeypatch.setattr(connector, "_request_json", lambda _path: {"dag_runs": [
        {"dag_id": "d1", "execution_date": old, "state": "failed"},
        {"dag_id": "d1", "execution_date": recent, "state": "success"},
    ]})
    result = connector.fetch_dag_stats("d1", days=7)
    assert result["run_count"] == 1
    assert result["success_rate"] == 1.0
