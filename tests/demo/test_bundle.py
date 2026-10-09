import ast
import json
from collections.abc import Iterator
from datetime import datetime, timezone

import pytest

from copilot_sdk.demo.bundle import restore_bundle_if_empty
from copilot_sdk.graph import InMemoryGraphStore
from copilot_sdk.graph.protocol import ProtocolV2GraphStore


DOMAIN = "demo"


def _bundle(**overrides):
    data = {
        "domain": DOMAIN,
        "min_decisions_to_skip": 2,
        "decisions": [
            {
                "decision_id": "d1",
                "category": "alpha",
                "category_index": 1,
                "factors": {"risk": 0.2, "value": 0.8},
                "factor_vector": [0.2, 0.8],
                "factor_names": ["risk", "value"],
                "recommended_action": "approve",
                "recommended_index": 0,
                "confidence": 0.7,
                "probabilities": [0.7, 0.3],
                "created_at": 10.0,
                "verified": True,
                "actual_action": "approve",
                "actual_index": 0,
                "is_correct": True,
                "verified_at": 11.0,
                "context": {"source": "unit"},
            },
            {
                "decision_id": "d2",
                "category": "beta",
                "category_index": 2,
                "factors": {"risk": 0.9},
                "factor_names": ["risk"],
                "recommended_action": "review",
                "recommended_index": 1,
                "confidence": 0.4,
                "created_at": 12.0,
                "verified": False,
            },
        ],
        "centroid_checkpoints": [
            {
                "decision_id": "d1",
                "category": "alpha",
                "centroids": [[0.1, 0.2], [0.3, 0.4]],
                "decisions_count": 2,
                "iks": 0.12,
                "metadata": {"iks": 0.12, "source": "bundle"},
                "created_at": 13.0,
                "decision_time_start": "2026-01-01T00:00:00Z",
                "decision_time_end": "2026-01-01T01:00:00Z",
                "checkpoint_time": "2026-01-01T01:05:00Z",
            }
        ],
        "rl_state": {
            "alpha": {"weights": [1, 2], "updated_at": 14.0},
            "beta": {"weights": [3], "updated_at": 15.0},
        },
        "evolution_events": [
            {
                "event_type": "variant_generated",
                "rule_name": "threshold_rule",
                "variant_id": "v1",
                "metadata": {"seed": 7},
                "timestamp": "2026-01-01 00:00:00",
            }
        ],
    }
    data.update(overrides)
    return data


def _write_bundle(tmp_path, data=None):
    path = tmp_path / "bundle.json"
    path.write_text(json.dumps(data if data is not None else _bundle()), encoding="utf-8")
    return path


def _store(tmp_path):
    return InMemoryGraphStore(domain=DOMAIN)


def test_restores_when_cold(tmp_path):
    store = _store(tmp_path)
    try:
        assert restore_bundle_if_empty(store, _write_bundle(tmp_path), domain=DOMAIN).success is True
        assert store.count_decisions(DOMAIN) == 2
    finally:
        store.close()


def test_skips_when_warm(tmp_path):
    store = _store(tmp_path)
    try:
        path = _write_bundle(tmp_path)
        assert restore_bundle_if_empty(store, path, domain=DOMAIN).success is True
        assert restore_bundle_if_empty(store, path, domain=DOMAIN).success is False
        assert store.count_decisions(DOMAIN) == 2
    finally:
        store.close()


def test_outcomes_written_for_verified_decisions(tmp_path):
    store = _store(tmp_path)
    try:
        restore_bundle_if_empty(store, _write_bundle(tmp_path), domain=DOMAIN)
        verified = store.get_verified_decisions(DOMAIN)
        assert [row["decision_id"] for row in verified] == ["d1"]
        assert verified[0]["actual_action"] == "approve"
    finally:
        store.close()


def test_centroid_checkpoints_written(tmp_path):
    store = _store(tmp_path)
    try:
        restore_bundle_if_empty(store, _write_bundle(tmp_path), domain=DOMAIN)
        checkpoints = store.get_centroid_checkpoints(DOMAIN, limit=None)
        assert len(checkpoints) == 1
        assert checkpoints[0]["checkpoint_time"] == "2026-01-01T01:05:00Z"
        assert checkpoints[0]["metadata"]["source"] == "demo-bundle"
        assert checkpoints[0]["metadata"]["original_source"] == "bundle"
        import numpy as np
        loaded = store.load_latest_centroids(DOMAIN)
        assert isinstance(loaded, np.ndarray)
        np.testing.assert_array_equal(loaded, [[0.1, 0.2], [0.3, 0.4]])
    finally:
        store.close()


def test_rl_state_explicitly_skipped_without_protocol(tmp_path, caplog):
    store = _store(tmp_path)
    try:
        report = restore_bundle_if_empty(store, _write_bundle(tmp_path), domain=DOMAIN)
        assert store.load_rl_state("alpha") is None
        assert store.load_rl_state("beta") is None
        assert report.skipped_stores == ["rl_state"]
        assert report.skipped_count == 2
        assert report.skipped_reasons == {"rl_state": "no protocol method for RL state (REV-P4a)"}
        assert not report.fully_restored
        assert "no protocol method for RL state" in caplog.text
    finally:
        store.close()


def test_evolution_events_written(tmp_path):
    store = _store(tmp_path)
    try:
        restore_bundle_if_empty(store, _write_bundle(tmp_path), domain=DOMAIN)
        events = store.get_evolution_events(DOMAIN)
        assert len(events) == 1
        assert events[0]["metadata"] == {"seed": 7, "timestamp": "2026-01-01 00:00:00",
                                         "source": "demo-bundle", "synthetic": True,
                                         "provenance": "synthetic"}
        assert events[0]["timestamp"] == "2026-01-01 00:00:00"
    finally:
        store.close()


def test_domain_mismatch_returns_false(tmp_path):
    store = _store(tmp_path)
    try:
        assert restore_bundle_if_empty(
            store,
            _write_bundle(tmp_path, _bundle(domain="other")),
            domain=DOMAIN,
        ).success is False
        assert store.count_decisions(DOMAIN) == 0
    finally:
        store.close()


def test_missing_file_returns_false(tmp_path):
    store = _store(tmp_path)
    try:
        assert restore_bundle_if_empty(store, tmp_path / "missing.json", domain=DOMAIN).success is False
    finally:
        store.close()


def test_malformed_json_returns_false(tmp_path):
    store = _store(tmp_path)
    path = tmp_path / "bad.json"
    path.write_text("{bad", encoding="utf-8")
    try:
        assert restore_bundle_if_empty(store, path, domain=DOMAIN).success is False
    finally:
        store.close()


def test_idempotent_decisions(tmp_path):
    store = InMemoryGraphStore(domain=DOMAIN)
    try:
        path = _write_bundle(tmp_path, _bundle(min_decisions_to_skip=999))
        assert restore_bundle_if_empty(store, path, domain=DOMAIN).success is True
        assert restore_bundle_if_empty(store, path, domain=DOMAIN).success is True
        assert store.count_decisions(DOMAIN) == 2
    finally:
        store.close()


def test_second_restore_same_bundle_returns_false_when_all_writes_noop(tmp_path):
    store = _store(tmp_path)
    data = {
        "schema_version": "1.0",
        "domain": DOMAIN,
        "min_decisions_to_skip": 999,
        "decisions": [
            {
                "decision_id": "d-stable",
                "category": "alpha",
                "category_index": 0,
                "factors": {"risk": 0.2},
                "factor_vector": [0.2],
                "factor_names": ["risk"],
                "recommended_action": "approve",
                "recommended_index": 0,
                "confidence": 0.7,
                "created_at": 10.0,
                "verified": False,
            }
        ],
        "centroid_checkpoints": [],
        "rl_state": None,
        "evolution_events": [],
    }
    try:
        path = _write_bundle(tmp_path, data)
        assert restore_bundle_if_empty(store, path, domain=DOMAIN).success is True
        assert restore_bundle_if_empty(store, path, domain=DOMAIN).success is False
        assert store.count_decisions(DOMAIN) == 1
    finally:
        store.close()


def test_rl_state_null_safe(tmp_path):
    store = _store(tmp_path)
    try:
        path = _write_bundle(tmp_path, _bundle(rl_state={"alpha": None}))
        report = restore_bundle_if_empty(store, path, domain=DOMAIN)
        assert report.success is True
        assert store.load_rl_state("alpha") is None
        assert report.skipped_count == 1
        assert report.skipped_stores == ["rl_state"]
    finally:
        store.close()


def test_probabilities_json_fallback_from_confidence(tmp_path):
    store = _store(tmp_path)
    data = _bundle(decisions=[{**_bundle()["decisions"][0], "probabilities": None}])
    try:
        restore_bundle_if_empty(store, _write_bundle(tmp_path, data), domain=DOMAIN)
        decision = store.get_all_decisions(DOMAIN)[0]
        assert decision["probabilities"] == [0.7]
    finally:
        store.close()


def test_unverified_decisions_have_no_outcomes(tmp_path):
    store = _store(tmp_path)
    data = _bundle(decisions=[{**_bundle()["decisions"][1], "verified": False}])
    try:
        restore_bundle_if_empty(store, _write_bundle(tmp_path, data), domain=DOMAIN)
        assert store.get_verified_decisions(DOMAIN) == []
    finally:
        store.close()


def test_bundle_restore_none_correctness_stays_pending(tmp_path):
    store = _store(tmp_path)
    decision = {**_bundle()["decisions"][0], "verified": True, "is_correct": None}
    data = _bundle(decisions=[decision])
    try:
        assert restore_bundle_if_empty(store, _write_bundle(tmp_path, data), domain=DOMAIN).success is True
        restored = store.get_all_decisions(DOMAIN)[0]
        assert restored["status"] == "pending"
        assert restored.get("correct") is None
    finally:
        store.close()


def test_empty_noop_bundle_returns_false(tmp_path):
    store = _store(tmp_path)
    data = {
        "schema_version": 1,
        "domain": DOMAIN,
        "min_decisions_to_skip": 2,
        "decisions": [],
        "centroid_checkpoints": [],
        "rl_state": None,
        "evolution_events": [],
    }
    try:
        assert restore_bundle_if_empty(store, _write_bundle(tmp_path, data), domain=DOMAIN).success is False
        assert store.count_decisions(DOMAIN) == 0
        assert store.get_centroid_checkpoints(DOMAIN, limit=None) == []
        assert store.load_rl_state("alpha") is None
        assert store.get_evolution_events(DOMAIN) == []
    finally:
        store.close()


def test_in_memory_graph_store_restores_supported_sections(tmp_path):
    store = InMemoryGraphStore(domain=DOMAIN)
    report = restore_bundle_if_empty(store, _write_bundle(tmp_path), domain=DOMAIN)
    assert not report.fully_restored
    assert report.skipped_stores == ["rl_state"]
    assert report.restored_count == 5
    assert report.stores_failed == 0
    assert store.count_decisions(DOMAIN) == 2


def test_bundle_module_importable():
    from copilot_sdk.demo.bundle import restore_bundle_if_empty as imported

    assert imported is restore_bundle_if_empty


def test_bundle_has_no_forbidden_runtime_imports():
    source = (
        __import__("pathlib")
        .Path("copilot_sdk/demo/bundle.py")
        .read_text(encoding="utf-8")
    )
    tree = ast.parse(source)
    forbidden = ("copilot_sdk.scoring", "copilot_sdk.backend", "copilot_sdk.rl")
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            assert not any(alias.name.startswith(forbidden) for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module:
            assert not node.module.startswith(forbidden)



def test_bundle_restore_protocol_based(tmp_path):
    from copilot_sdk.graph.factory import create_graph_store
    from copilot_sdk.graph.protocol import ProtocolV2GraphStore

    store = create_graph_store(backend="memory", domain=DOMAIN, profile="test", env={},
                               decision_id_prefix="NEW-")
    assert isinstance(store, ProtocolV2GraphStore)
    report = restore_bundle_if_empty(store, _write_bundle(tmp_path), domain=DOMAIN)
    assert not report.fully_restored
    assert report.skipped_stores == ["rl_state"]
    assert report.skipped_count == 2
    assert report.section_counts == {
        "decisions": 2, "outcomes": 1, "centroid_checkpoints": 1,
        "rl_state": 0, "evolution_events": 1,
    }
    assert report.restored_count == 5
    assert [row["decision_id"] for row in store.get_all_decisions(DOMAIN)] == ["d2", "d1"]
    assert store.get_centroid_checkpoints(DOMAIN)[0]["decisions_count"] == 2


def test_bundle_restore_provenance_metadata(tmp_path):
    store = _store(tmp_path)
    restore_bundle_if_empty(store, _write_bundle(tmp_path), domain=DOMAIN)
    for row in store.get_all_decisions(DOMAIN):
        assert row["metadata"]["provenance"] == "synthetic"
        assert row["metadata"]["source"] == "demo-bundle"
        assert row["metadata"]["synthetic"] is True
    assert store.get_decision("d1", DOMAIN)["factors"] == {"risk": 0.2, "value": 0.8}
    assert store.get_decision("d1", DOMAIN)["created_at"] == 10.0


def test_bundle_idempotent_on_warm_store(tmp_path):
    store = _store(tmp_path)
    path = _write_bundle(tmp_path)
    first = restore_bundle_if_empty(store, path, domain=DOMAIN)
    assert first.restored_count == 5
    assert first.skipped_stores == ["rl_state"]
    before = (store.get_all_decisions(DOMAIN), store.get_verified_decisions(DOMAIN),
              store.get_centroid_checkpoints(DOMAIN), store.get_evolution_events(DOMAIN))
    report = restore_bundle_if_empty(store, path, domain=DOMAIN)
    assert not report.success
    assert report.restored_count == 0
    assert before == (store.get_all_decisions(DOMAIN), store.get_verified_decisions(DOMAIN),
                      store.get_centroid_checkpoints(DOMAIN), store.get_evolution_events(DOMAIN))


def test_bundle_missing_factor_names_raises_before_writing(tmp_path):
    import pytest

    store = _store(tmp_path)
    data = _bundle()
    data["decisions"][1].pop("factor_names")
    with pytest.raises(ValueError, match="explicit factor_names"):
        restore_bundle_if_empty(store, _write_bundle(tmp_path, data), domain=DOMAIN)
    assert store.count_decisions(DOMAIN) == 0
    assert store.get_centroid_checkpoints(DOMAIN) == []


def test_bundle_misaligned_factor_schema_raises_before_writing(tmp_path):
    import pytest

    store = _store(tmp_path)
    data = _bundle()
    data["decisions"][0]["factor_names"] = ["value", "risk"]
    with pytest.raises(ValueError, match="do not match"):
        restore_bundle_if_empty(store, _write_bundle(tmp_path, data), domain=DOMAIN)
    assert store.count_decisions(DOMAIN) == 0


def test_bundle_count_failure_never_starts_restore(tmp_path):
    class UnavailableStore(InMemoryGraphStore):
        def count_decisions(self, domain: str) -> int:
            raise ConnectionError("count unavailable")

    store = UnavailableStore(domain=DOMAIN)
    report = restore_bundle_if_empty(store, _write_bundle(tmp_path), domain=DOMAIN)
    assert not report.success
    assert report.failed_stores == ["count_decisions"]
    assert store.get_all_decisions(DOMAIN) == []


def test_bundle_partial_section_failure_is_not_complete(tmp_path):
    class CheckpointFailure(InMemoryGraphStore):
        def save_centroids(self, *args, **kwargs) -> None:
            raise ConnectionError("checkpoint unavailable")

    store = CheckpointFailure(domain=DOMAIN)
    report = restore_bundle_if_empty(store, _write_bundle(tmp_path), domain=DOMAIN)
    assert report.success and not report.fully_restored
    assert report.failed_stores == ["centroid_checkpoints"]
    assert report.section_counts["centroid_checkpoints"] == 0
    assert report.section_counts["outcomes"] == 1
    assert report.skipped_count == 3
    assert report.skipped_stores == ["rl_state"]


def test_bundle_rl_envelope_is_one_skipped_state_record(tmp_path):
    store = _store(tmp_path)
    data = _bundle(rl_state={"key": "thompson_posteriors", "alpha": [2], "beta": [3],
                             "thompson_posteriors": {"alpha": [2], "beta": [3]}, "updated_at": 14})
    report = restore_bundle_if_empty(store, _write_bundle(tmp_path, data), domain=DOMAIN)
    assert report.section_counts["rl_state"] == 0
    assert report.skipped_count == 1
    assert report.skipped_stores == ["rl_state"]
    assert store.load_rl_state("thompson_posteriors") is None
    assert store.load_rl_state("key") is None


def test_bundle_explicit_outcome_section(tmp_path):
    store = _store(tmp_path)
    data = _bundle(rl_state=None)
    data["decisions"][0]["verified"] = False
    data["outcomes"] = [{"decision_id": "d1", "actual_action": "approve", "is_correct": True,
                         "actual_index": 0, "verified_at": 11}]
    report = restore_bundle_if_empty(store, _write_bundle(tmp_path, data), domain=DOMAIN)
    assert report.fully_restored
    rows = store.get_verified_decisions(DOMAIN)
    assert [row["decision_id"] for row in rows] == ["d1"]
    assert rows[0]["verified_at"] == 11


def test_bundle_historical_checkpoint_fields_through_factory(tmp_path):
    from copilot_sdk.graph.factory import create_graph_store

    store = create_graph_store(backend="memory", domain=DOMAIN, profile="test", env={})
    data = _bundle(rl_state=None)
    data["centroid_checkpoints"][0]["decisions_count"] = 1
    assert restore_bundle_if_empty(store, _write_bundle(tmp_path, data), domain=DOMAIN).fully_restored
    row = store.get_centroid_checkpoints(DOMAIN)[0]
    assert row["decisions_count"] == 1
    assert row["created_at"] == 13.0
    assert row["decision_time_start"] == "2026-01-01T00:00:00Z"
    assert row["decision_time_end"] == "2026-01-01T01:00:00Z"
    assert row["checkpoint_time"] == "2026-01-01T01:05:00Z"
    assert all(isinstance(row[field], str) for field in ("decision_time_start", "decision_time_end", "checkpoint_time"))


def test_bundle_age_reopen_all_supported_sections(tmp_path, disposable_age, caplog):
    store = disposable_age.store(DOMAIN)
    path = _write_bundle(tmp_path)
    report = restore_bundle_if_empty(store, path, domain=DOMAIN)
    assert report.success and not report.fully_restored
    assert report.skipped_stores == ["rl_state"]
    assert report.skipped_count == 2
    assert report.section_counts == {
        "decisions": 2, "outcomes": 1, "centroid_checkpoints": 1,
        "rl_state": 0, "evolution_events": 1,
    }
    assert "no protocol method for RL state" in caplog.text
    reopened = disposable_age.store(DOMAIN)
    assert [row["decision_id"] for row in reopened.get_all_decisions(DOMAIN)] == ["d1", "d2"]
    outcome = reopened.get_verified_decisions(DOMAIN)[0]
    assert outcome["decision_id"] == "d1"
    assert outcome["verified_at"] == 11.0
    assert outcome["outcome_metadata"]["context"] == {"source": "unit"}
    checkpoint = reopened.get_centroid_checkpoints(DOMAIN)[0]
    assert checkpoint["centroids"] == [[0.1, 0.2], [0.3, 0.4]]
    assert checkpoint["created_at"] == 13.0
    assert checkpoint["decisions_count"] == 2
    assert checkpoint["checkpoint_time"] == "2026-01-01T01:05:00Z"
    assert checkpoint["decision_time_start"] == "2026-01-01T00:00:00Z"
    assert checkpoint["decision_time_end"] == "2026-01-01T01:00:00Z"
    assert checkpoint["iks"] == 0.12
    event = reopened.get_evolution_events(DOMAIN)[0]
    assert event["metadata"]["seed"] == 7
    assert event["timestamp"] == "2026-01-01 00:00:00"
    assert not restore_bundle_if_empty(reopened, path, domain=DOMAIN).success


def test_shipped_bundle_factor_schema_matches_generator():
    from pathlib import Path
    import random
    from scripts.regenerate_demo_bundles import CONFIGS, RANDOM_SEED, build_bundle, load_seed_entries

    state = random.getstate()
    try:
        random.seed(RANDOM_SEED)
        for config in CONFIGS:
            data = json.loads((Path("demo") / f"{config.name}_demo_bundle.json").read_text())
            assert data["factor_names"] == list(config.factors)
            generated = build_bundle(config, load_seed_entries(config.seed_path))
            assert generated["factor_names"] == list(config.factors)
            for row in data["decisions"]:
                assert row["factor_vector"] == [row["factors"][name] for name in data["factor_names"]]
    finally:
        random.setstate(state)


@pytest.fixture(params=["memory", "age"])
def portable_store(request: pytest.FixtureRequest) -> Iterator[ProtocolV2GraphStore]:
    store: ProtocolV2GraphStore
    if request.param == "memory":
        store = InMemoryGraphStore(domain=DOMAIN)
    else:
        store = request.getfixturevalue("disposable_age").store(DOMAIN)
    assert isinstance(store, ProtocolV2GraphStore)
    try:
        yield store
    finally:
        store.close()


@pytest.mark.parametrize("names", [["c", "b", "a"], ["a", "b", "different"]])
def test_replay_rejects_changed_factor_schema(tmp_path, portable_store, names):
    row = {**_bundle()["decisions"][0], "factor_names": ["a", "b", "c"],
           "factor_vector": [0.1, 0.2, 0.3], "factors": {}, "verified": False}
    data = _bundle(decisions=[row], centroid_checkpoints=[], rl_state=None,
                   evolution_events=[], min_decisions_to_skip=999)
    path = _write_bundle(tmp_path, data)
    assert restore_bundle_if_empty(portable_store, path, domain=DOMAIN).restored_count == 1
    before = portable_store.get_decision("d1", DOMAIN)
    row["factor_names"] = names
    report = restore_bundle_if_empty(portable_store, _write_bundle(tmp_path, data), domain=DOMAIN)
    assert report.failed_stores == ["decisions"]
    assert report.restored_count == 0
    assert not report.fully_restored
    assert portable_store.get_decision("d1", DOMAIN) == before


def test_replay_accepts_identical_factor_schema(tmp_path, portable_store):
    row = {**_bundle()["decisions"][0], "factor_names": ["a", "b", "c"],
           "factor_vector": [0.1, 0.2, 0.3], "factors": {}, "verified": False}
    path = _write_bundle(tmp_path, _bundle(decisions=[row], centroid_checkpoints=[],
                         rl_state=None, evolution_events=[], min_decisions_to_skip=999))
    assert restore_bundle_if_empty(portable_store, path, domain=DOMAIN).restored_count == 1
    before = portable_store.get_decision("d1", DOMAIN)
    report = restore_bundle_if_empty(portable_store, path, domain=DOMAIN)
    assert report.fully_restored
    assert report.failed_stores == []
    assert report.restored_count == 0
    assert not report.success
    assert portable_store.get_decision("d1", DOMAIN) == before


@pytest.mark.parametrize(("field", "value"), [
    ("context", {"source": "different"}), ("actual_index", 1), ("verified_at", 99.0),
])
def test_replay_rejects_changed_outcome_facts(tmp_path, portable_store, field, value):
    data = _bundle(centroid_checkpoints=[], rl_state=None, evolution_events=[],
                   min_decisions_to_skip=999)
    assert restore_bundle_if_empty(portable_store, _write_bundle(tmp_path, data),
                                   domain=DOMAIN).restored_count == 3
    before = portable_store.get_decision("d1", DOMAIN, include_outcome=True)
    data["decisions"][0][field] = value
    report = restore_bundle_if_empty(portable_store, _write_bundle(tmp_path, data), domain=DOMAIN)
    assert report.failed_stores == ["outcomes"]
    assert report.section_counts["outcomes"] == 0
    assert report.restored_count == 0
    assert not report.fully_restored
    assert portable_store.get_decision("d1", DOMAIN, include_outcome=True) == before


def test_replay_accepts_identical_outcome_facts(tmp_path, portable_store):
    path = _write_bundle(tmp_path, _bundle(centroid_checkpoints=[], rl_state=None,
                         evolution_events=[], min_decisions_to_skip=999))
    assert restore_bundle_if_empty(portable_store, path, domain=DOMAIN).restored_count == 3
    before = portable_store.get_decision("d1", DOMAIN, include_outcome=True)
    report = restore_bundle_if_empty(portable_store, path, domain=DOMAIN)
    assert report.fully_restored and not report.success
    assert report.restored_count == 0
    assert portable_store.get_decision("d1", DOMAIN, include_outcome=True) == before


def test_every_supported_artifact_has_synthetic_provenance(tmp_path, portable_store):
    report = restore_bundle_if_empty(portable_store, _write_bundle(tmp_path, _bundle(rl_state=None)),
                                     domain=DOMAIN)
    assert report.fully_restored
    assert report.section_counts == {"decisions": 2, "outcomes": 1,
                                     "centroid_checkpoints": 1, "evolution_events": 1}
    decisions = portable_store.get_all_decisions(DOMAIN)
    outcome = portable_store.get_decision("d1", DOMAIN, include_outcome=True)
    assert outcome is not None
    checkpoints = portable_store.get_centroid_checkpoints(DOMAIN)
    events = portable_store.get_evolution_events(DOMAIN)
    assert len(decisions) == 2
    assert len(checkpoints) == len(events) == 1
    metadata = [row["metadata"] for row in decisions]
    metadata += [outcome["outcome_metadata"], checkpoints[0]["metadata"], events[0]["metadata"]]
    for item in metadata:
        assert item["source"] == "demo-bundle"
        assert item["synthetic"] is True
        assert item["provenance"] == "synthetic"
    assert checkpoints[0]["metadata"]["original_source"] == "bundle"
    assert outcome["outcome_metadata"]["context"] == {"source": "unit"}
    assert events[0]["metadata"]["seed"] == 7


def _event_bundle(events):
    return _bundle(decisions=[], outcomes=[], centroid_checkpoints=[], rl_state=None,
                   evolution_events=events, min_decisions_to_skip=999)


def test_event_replay_counts_only_new_records(tmp_path, portable_store):
    events = [
        {"event_id": f"event-{index}", "event_type": "promoted", "rule_name": "rule",
         "variant_id": "variant", "timestamp": f"2026-01-{index + 1:02d}T00:00:00Z"}
        for index in range(3)
    ]
    path = _write_bundle(tmp_path, _event_bundle(events))
    first = restore_bundle_if_empty(portable_store, path, domain=DOMAIN)
    assert first.restored_count == 3
    assert first.replayed_count == 0
    before = portable_store.get_evolution_events(DOMAIN, limit=1000)
    replay = restore_bundle_if_empty(portable_store, path, domain=DOMAIN)
    assert replay.fully_restored
    assert replay.restored_count == 0
    assert replay.replayed_count == 3
    assert replay.section_replay_counts == {"evolution_events": 3}
    assert not replay.success
    assert portable_store.get_evolution_events(DOMAIN, limit=1000) == before
    events.append({"event_id": "one-new-event", "event_type": "promoted",
                   "rule_name": "rule", "variant_id": "variant"})
    added = restore_bundle_if_empty(portable_store, _write_bundle(tmp_path, _event_bundle(events)),
                                    domain=DOMAIN)
    assert added.fully_restored and added.success
    assert added.restored_count == 1
    assert added.replayed_count == 3
    assert len(portable_store.get_evolution_events(DOMAIN, limit=1000)) == 4


def test_event_counts_include_inventory_beyond_default_page(tmp_path, portable_store):
    for index in range(105):
        portable_store.write_evolution_event(f"existing-{index}", DOMAIN, "promoted", "rule", "variant")
    data = _event_bundle([{"event_id": "new", "event_type": "promoted", "rule_name": "rule",
                           "variant_id": "variant", "timestamp": "2000-01-01T00:00:00Z"}])
    path = _write_bundle(tmp_path, data)
    assert restore_bundle_if_empty(portable_store, path, domain=DOMAIN).restored_count == 1
    replay = restore_bundle_if_empty(portable_store, path, domain=DOMAIN)
    assert replay.restored_count == 0
    assert replay.replayed_count == 1
    assert replay.fully_restored
    assert len(portable_store.get_evolution_events(DOMAIN, limit=1000)) == 106


def test_event_inventory_cap_fails_before_unmeasurable_write(tmp_path, portable_store):
    for index in range(999):
        portable_store.write_evolution_event(f"existing-{index}", DOMAIN, "promoted", "rule", "variant")
    events = [{"event_id": identifier, "event_type": "promoted", "rule_name": "rule",
               "variant_id": "variant"} for identifier in ("last-slot", "must-not-write")]
    path = _write_bundle(tmp_path, _event_bundle(events))
    report = restore_bundle_if_empty(portable_store, path, domain=DOMAIN)
    assert report.restored_count == 1
    assert report.section_counts == {"evolution_events": 1}
    assert report.failed_stores == ["evolution_events"]
    assert report.skipped_count == 1
    assert not report.fully_restored
    assert "1000" in report.failed_reasons["evolution_events"]
    assert "AGE-SDK #11" in report.failed_reasons["evolution_events"]
    before = portable_store.get_evolution_events(DOMAIN, limit=1000)
    assert len(before) == 1000
    assert "last-slot" in {row["event_id"] for row in before}
    assert "must-not-write" not in {row["event_id"] for row in before}
    retry = restore_bundle_if_empty(portable_store, path, domain=DOMAIN)
    assert retry.restored_count == 0
    assert retry.skipped_count == 2
    assert not retry.success and not retry.fully_restored
    assert portable_store.get_evolution_events(DOMAIN, limit=1000) == before


def test_scoring_only_protocol_skips_all_bundle_sections(tmp_path):
    from unittest.mock import Mock
    from copilot_sdk.graph.protocol import GraphStore, ScoringPersistenceStore

    store = Mock(spec_set=ScoringPersistenceStore)
    assert isinstance(store, ScoringPersistenceStore)
    assert not isinstance(store, GraphStore)
    report = restore_bundle_if_empty(store, _write_bundle(tmp_path), domain=DOMAIN)
    assert report.restored_count == report.replayed_count == 0
    assert report.stores_failed == 0
    assert not report.success and not report.fully_restored
    assert report.skipped_stores == ["decisions", "outcomes", "centroid_checkpoints",
                                     "rl_state", "evolution_events"]
    assert report.skipped_count == 7
    assert report.skipped_reasons == {
        "decisions": "ProtocolV2GraphStore required", "outcomes": "GraphStore required",
        "centroid_checkpoints": "GraphStore required",
        "rl_state": "no protocol method for RL state (REV-P4a)",
        "evolution_events": "ProtocolV2GraphStore required",
    }
    assert store.mock_calls == []


def test_base_protocol_restores_outcomes_checkpoints_only(tmp_path):
    from unittest.mock import Mock
    from copilot_sdk.graph.protocol import GraphStore

    backing = InMemoryGraphStore(domain=DOMAIN)
    identifier = backing.write_decision(DOMAIN, "alpha", "approve", 0.7, {"risk": 0.2})
    store = Mock(spec_set=GraphStore, wraps=backing)
    assert isinstance(store, GraphStore)
    assert not isinstance(store, ProtocolV2GraphStore)
    data = _bundle(rl_state=None, min_decisions_to_skip=999)
    for row in data["decisions"]:
        row["verified"] = False
    data["outcomes"] = [{"decision_id": identifier, "actual_action": "approve",
                         "is_correct": True, "actual_index": 0, "verified_at": 11.0,
                         "context": {"source": "base"}}]
    report = restore_bundle_if_empty(store, _write_bundle(tmp_path, data), domain=DOMAIN)
    assert report.restored_count == 2
    assert report.section_counts == {"decisions": 0, "outcomes": 1,
                                     "centroid_checkpoints": 1, "evolution_events": 0}
    assert report.skipped_stores == ["decisions", "evolution_events"]
    assert report.skipped_count == 3
    assert report.skipped_reasons == {"decisions": "ProtocolV2GraphStore required",
                                      "evolution_events": "ProtocolV2GraphStore required"}
    assert report.failed_stores == []
    assert not report.fully_restored
    assert store.count_decisions(DOMAIN) == 1
    outcome = store.get_decision(identifier, DOMAIN, include_outcome=True)
    assert outcome["actual_action"] == "approve"
    assert outcome["verified_at"] == 11.0
    assert outcome["outcome_metadata"]["context"] == {"source": "base"}
    assert len(store.get_centroid_checkpoints(DOMAIN)) == 1
    assert backing.get_evolution_events(DOMAIN) == []


def test_v2_protocol_stub_restores_governed_decisions_and_events(tmp_path):
    from unittest.mock import Mock

    backing = InMemoryGraphStore(domain=DOMAIN)
    store = Mock(spec_set=ProtocolV2GraphStore, wraps=backing)
    data = _bundle(rl_state=None)
    report = restore_bundle_if_empty(store, _write_bundle(tmp_path, data), domain=DOMAIN)
    assert report.fully_restored
    assert report.restored_count == 5
    assert report.section_counts == {"decisions": 2, "outcomes": 1,
                                     "centroid_checkpoints": 1, "evolution_events": 1}
    assert store.count_decisions(DOMAIN) == 2
    assert len(store.get_evolution_events(DOMAIN)) == 1


def test_bundle_dispatch_only_uses_declared_protocols():
    from pathlib import Path

    source = Path("copilot_sdk/demo/bundle.py").read_text(encoding="utf-8")
    assert "from copilot_sdk.graph.protocol import" in source
    assert "store: Any" not in source
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            assert node.module not in {
                "copilot_sdk.graph.memory_store",
                "ci_platform.graph.age_sdk_adapter", "ci_platform.graph.age_graph_store",
            }
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in {"getattr", "hasattr", "callable"}
            if node.func.id == "isinstance":
                assert ast.unparse(node.args[1]) not in {
                    "InMemoryGraphStore", "AGEGraphStore", "AGEGraphStoreAdapter",
                }


@pytest.mark.parametrize(("field", "value"), [
    ("scorer_version", "changed-scorer"), ("preset_version", "changed-preset"),
    ("factor_schema_version", "changed-schema"), ("created_at", 50.0),
])
def test_replay_rejects_changed_decision_identity_fields(tmp_path, portable_store, field, value):
    data = _bundle(centroid_checkpoints=[], rl_state=None, evolution_events=[], min_decisions_to_skip=999)
    data["decisions"][0]["verified"] = False
    assert restore_bundle_if_empty(portable_store, _write_bundle(tmp_path, data),
                                   domain=DOMAIN).restored_count == 2
    before = portable_store.get_decision("d1", DOMAIN)
    data["decisions"][0][field] = value
    report = restore_bundle_if_empty(portable_store, _write_bundle(tmp_path, data), domain=DOMAIN)
    assert report.failed_stores == ["decisions"]
    assert field in report.failed_reasons["decisions"]
    assert report.restored_count == 0
    assert not report.fully_restored
    assert portable_store.get_decision("d1", DOMAIN) == before


def test_outcome_replay_without_explicit_time_is_equivalent(tmp_path, portable_store):
    identifier = portable_store.write_decision(DOMAIN, "alpha", "approve", 0.7, {})
    data = _event_bundle([])
    data["outcomes"] = [{"decision_id": identifier, "actual_action": "approve", "is_correct": True}]
    path = _write_bundle(tmp_path, data)
    assert restore_bundle_if_empty(portable_store, path, domain=DOMAIN).restored_count == 1
    before = portable_store.get_decision(identifier, DOMAIN, include_outcome=True)
    report = restore_bundle_if_empty(portable_store, path, domain=DOMAIN)
    assert report.fully_restored and not report.success
    assert report.restored_count == 0
    assert report.replayed_count == 1
    assert portable_store.get_decision(identifier, DOMAIN, include_outcome=True) == before

