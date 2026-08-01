from __future__ import annotations

import re

from copilot_sdk.graph.dual_write_store import DualWriteStore
from copilot_sdk.graph.memory_store import InMemoryGraphStore
from copilot_sdk.graph.sqlite_store import SQLiteGraphStore


_HEX_ID = re.compile(r"^[0-9a-f]{12}$")


def test_sqlite_generate_decision_id_uses_trading_prefix(tmp_path):
    store = SQLiteGraphStore(tmp_path / "trading.db", domain="trading", decision_id_prefix="TRD-")
    try:
        decision_id = store.generate_decision_id("trading")
        assert decision_id.startswith("TRD-")
        assert _HEX_ID.fullmatch(decision_id.removeprefix("TRD-"))
    finally:
        store.close()


def test_sqlite_generate_decision_id_uses_purchasing_prefix(tmp_path):
    store = SQLiteGraphStore(tmp_path / "purchasing.db", domain="purchasing", decision_id_prefix="PUR-")
    try:
        decision_id = store.generate_decision_id("purchasing")
        assert decision_id.startswith("PUR-")
        assert _HEX_ID.fullmatch(decision_id.removeprefix("PUR-"))
    finally:
        store.close()


def test_sqlite_generate_decision_id_without_prefix_is_bare_hex(tmp_path):
    store = SQLiteGraphStore(tmp_path / "plain.db", domain="test")
    try:
        assert _HEX_ID.fullmatch(store.generate_decision_id("test"))
    finally:
        store.close()


def test_memory_generate_decision_id_is_bare_hex():
    assert _HEX_ID.fullmatch(InMemoryGraphStore().generate_decision_id("test"))


def test_dual_write_delegates_id_generation_to_prefixed_primary(tmp_path):
    primary = SQLiteGraphStore(tmp_path / "trading.db", domain="trading", decision_id_prefix="TRD-")
    secondary = InMemoryGraphStore(domain="trading")
    dual = DualWriteStore(primary, secondary)
    try:
        decision_id = dual.generate_decision_id("trading")
        assert decision_id.startswith("TRD-")
        assert _HEX_ID.fullmatch(decision_id.removeprefix("TRD-"))
    finally:
        dual.close()


def test_generated_ids_are_unique(tmp_path):
    store = SQLiteGraphStore(tmp_path / "unique.db", domain="trading", decision_id_prefix="TRD-")
    try:
        assert store.generate_decision_id("trading") != store.generate_decision_id("trading")
    finally:
        store.close()


def test_generated_id_is_valid_for_governed_write(tmp_path):
    store = SQLiteGraphStore(tmp_path / "governed.db", domain="trading", decision_id_prefix="TRD-")
    try:
        decision_id = store.generate_decision_id("trading")
        store.write_governed_decision(
            decision_id=decision_id,
            domain="trading",
            category="equity",
            category_index=0,
            recommended_action="buy",
            recommended_index=0,
            confidence=0.9,
            probabilities=[0.9, 0.1],
            factor_vector=[0.1, 0.2],
            factor_names=["signal", "risk"],
        )
        assert store.get_decision(decision_id, domain="trading")["decision_id"] == decision_id
    finally:
        store.close()


def test_domain_parameter_is_accepted_for_future_domain_schemes(tmp_path):
    store = SQLiteGraphStore(tmp_path / "domain.db", domain="trading", decision_id_prefix="TRD-")
    try:
        assert store.generate_decision_id("future_domain").startswith("TRD-")
    finally:
        store.close()
