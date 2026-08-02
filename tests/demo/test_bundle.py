import ast
import json

from copilot_sdk.demo.bundle import restore_bundle_if_empty
from copilot_sdk.graph import InMemoryGraphStore, SQLiteGraphStore


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
    return SQLiteGraphStore(tmp_path / "graph.sqlite", domain=DOMAIN)


def test_restores_when_cold(tmp_path):
    store = _store(tmp_path)
    try:
        assert restore_bundle_if_empty(store, _write_bundle(tmp_path), domain=DOMAIN) is True
        assert store.count_decisions(DOMAIN) == 2
    finally:
        store.close()


def test_skips_when_warm(tmp_path):
    store = _store(tmp_path)
    try:
        path = _write_bundle(tmp_path)
        assert restore_bundle_if_empty(store, path, domain=DOMAIN) is True
        assert restore_bundle_if_empty(store, path, domain=DOMAIN) is False
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
        assert checkpoints[0]["metadata"]["source"] == "bundle"
    finally:
        store.close()


def test_rl_state_written(tmp_path):
    store = _store(tmp_path)
    try:
        restore_bundle_if_empty(store, _write_bundle(tmp_path), domain=DOMAIN)
        assert store.load_rl_state("alpha")["weights"] == [1, 2]
        assert store.load_rl_state("beta")["weights"] == [3]
    finally:
        store.close()


def test_evolution_events_written(tmp_path):
    store = _store(tmp_path)
    try:
        restore_bundle_if_empty(store, _write_bundle(tmp_path), domain=DOMAIN)
        events = store.get_evolution_events(DOMAIN)
        assert len(events) == 1
        assert events[0]["metadata"] == {"seed": 7}
    finally:
        store.close()


def test_domain_mismatch_returns_false(tmp_path):
    store = _store(tmp_path)
    try:
        assert restore_bundle_if_empty(
            store,
            _write_bundle(tmp_path, _bundle(domain="other")),
            domain=DOMAIN,
        ) is False
        assert store.count_decisions(DOMAIN) == 0
    finally:
        store.close()


def test_missing_file_returns_false(tmp_path):
    store = _store(tmp_path)
    try:
        assert restore_bundle_if_empty(store, tmp_path / "missing.json", domain=DOMAIN) is False
    finally:
        store.close()


def test_malformed_json_returns_false(tmp_path):
    store = _store(tmp_path)
    path = tmp_path / "bad.json"
    path.write_text("{bad", encoding="utf-8")
    try:
        assert restore_bundle_if_empty(store, path, domain=DOMAIN) is False
    finally:
        store.close()


def test_idempotent_decisions(tmp_path):
    store = SQLiteGraphStore(tmp_path / "graph.sqlite", domain=DOMAIN)
    try:
        path = _write_bundle(tmp_path, _bundle(min_decisions_to_skip=999))
        assert restore_bundle_if_empty(store, path, domain=DOMAIN) is True
        assert restore_bundle_if_empty(store, path, domain=DOMAIN) is True
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
        assert restore_bundle_if_empty(store, path, domain=DOMAIN) is True
        assert restore_bundle_if_empty(store, path, domain=DOMAIN) is False
        assert store.count_decisions(DOMAIN) == 1
    finally:
        store.close()


def test_rl_state_null_safe(tmp_path):
    store = _store(tmp_path)
    try:
        path = _write_bundle(tmp_path, _bundle(rl_state={"alpha": None}))
        assert restore_bundle_if_empty(store, path, domain=DOMAIN) is True
        assert store.load_rl_state("alpha") == {}
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
        assert restore_bundle_if_empty(store, _write_bundle(tmp_path, data), domain=DOMAIN) is True
        restored = store.get_all_decisions(DOMAIN)[0]
        assert restored["status"] == "pending"
        assert restored["correct"] is None
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
        assert restore_bundle_if_empty(store, _write_bundle(tmp_path, data), domain=DOMAIN) is False
        assert store.count_decisions(DOMAIN) == 0
        assert store.get_centroid_checkpoints(DOMAIN, limit=None) == []
        assert store.load_rl_state("alpha") is None
        assert store.get_evolution_events(DOMAIN) == []
    finally:
        store.close()


def test_in_memory_graph_store_returns_false_and_does_not_crash(tmp_path):
    store = InMemoryGraphStore(domain=DOMAIN)
    assert restore_bundle_if_empty(store, _write_bundle(tmp_path), domain=DOMAIN) is False
    assert store.count_decisions(DOMAIN) == 0


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
