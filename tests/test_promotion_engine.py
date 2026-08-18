"""Contract tests for the shared Promotion & Autonomy state machine."""

from concurrent.futures import ThreadPoolExecutor

from fastapi import FastAPI
from fastapi.testclient import TestClient

from copilot_sdk.promotion import (
    DataOpsPromotionPolicy,
    PromotionEngine,
    PromotionPolicy,
    PromotionStage,
    PromotionStore,
    S2PPromotionPolicy,
    SOCPromotionPolicy,
    create_promotion_router,
)


def _engine(policy: PromotionPolicy | None = None) -> PromotionEngine:
    return PromotionEngine(policy=policy or S2PPromotionPolicy())


def _green(shadow: int = 10) -> dict[str, object]:
    return {"conservation_state": "GREEN", "shadow_decisions": shadow}


def _reach_kept(engine: PromotionEngine, record_id: str) -> None:
    assert engine.advance(record_id).new_stage is PromotionStage.SHADOWING
    assert engine.advance(record_id, _green()).new_stage is PromotionStage.PROMOTED
    assert engine.advance(record_id).new_stage is PromotionStage.MEASURING
    result = engine.advance(
        record_id,
        {
            "measurement_decisions": 10,
            "improvement": 0.10,
        },
    )
    assert result.advanced is True
    assert result.new_stage is PromotionStage.KEPT


def test_pm_01_create_and_advance_through_all_stages() -> None:
    engine = _engine()
    record = engine.create("s2p", "price_variance")

    _reach_kept(engine, record.record_id)
    result = engine.transfer(record.record_id, "s2p", "price_variance", _green())

    assert result.advanced is True
    assert result.new_stage is PromotionStage.TRANSFERRED
    assert result.target_record_id is not None


def test_pm_02_shadow_minimum_blocks_promotion() -> None:
    engine = _engine()
    record = engine.create("s2p", "invoice_match")
    engine.advance(record.record_id)

    result = engine.advance(record.record_id, _green(shadow=9))

    assert result.advanced is False
    assert result.reason == "insufficient_shadow_decisions"
    assert result.new_stage is PromotionStage.SHADOWING


def test_pm_03_red_conservation_blocks_promotion() -> None:
    engine = _engine()
    record = engine.create("soc", "credential_access")
    engine.advance(record.record_id)

    result = engine.advance(
        record.record_id,
        {"conservation_state": "RED", "shadow_decisions": 100},
    )

    assert result.advanced is False
    assert result.reason == "conservation_red"


def test_pm_04_green_conservation_and_gates_allow_promotion() -> None:
    engine = _engine()
    record = engine.create("soc", "malware_execution")
    engine.advance(record.record_id)

    result = engine.advance(record.record_id, _green(100))

    assert result.advanced is True
    assert result.new_stage is PromotionStage.PROMOTED
    assert result.record is not None
    assert result.record.conservation_state_at_transition == "GREEN"


def test_pm_05_rollback_succeeds_from_any_stage() -> None:
    engine = _engine()
    record = engine.create("purchasing", "auto_order")

    result = engine.rollback(record.record_id, "regression detected")

    assert result.advanced is True
    assert result.new_stage is PromotionStage.ROLLED_BACK
    assert result.record is not None
    assert result.record.stage_history[-1]["reason"] == "regression detected"


def test_pm_06_invalid_direct_transition_is_not_in_policy() -> None:
    policy = S2PPromotionPolicy()

    assert PromotionStage.KEPT not in policy.allowed_transitions[PromotionStage.DISCOVERED]
    assert PromotionStage.PROMOTED not in policy.allowed_transitions[PromotionStage.DISCOVERED]


def test_pm_07_history_records_stage_timestamp_reason_and_evidence() -> None:
    engine = _engine()
    record = engine.create("s2p", "late_delivery")

    result = engine.advance(record.record_id, {"reason": "candidate observed"})

    assert result.record is not None
    entry = result.record.stage_history[-1]
    assert entry["stage"] == "shadowing"
    assert entry["reason"] == "candidate observed"
    assert entry["timestamp"]
    assert entry["evidence"]["reason"] == "candidate observed"


def test_pm_08_get_authority_returns_current_stage() -> None:
    engine = _engine()
    record = engine.create("s2p", "supplier_risk")
    engine.advance(record.record_id)

    assert engine.get_authority("s2p", "supplier_risk") is PromotionStage.SHADOWING
    assert engine.get_authority("s2p", "unknown") is PromotionStage.DISCOVERED


def test_pm_09_veto_returns_true_for_red_conservation() -> None:
    class RedProvider:
        def get_state(self) -> dict[str, str]:
            return {"status": "RED"}

    engine = PromotionEngine(S2PPromotionPolicy(), conservation_provider=RedProvider())
    record = engine.create("soc", "insider_threat")

    assert engine.veto(record.record_id) is True


def test_pm_10_s2p_policy_validates_seven_stage_lifecycle() -> None:
    policy = S2PPromotionPolicy()

    assert len(policy.stages) == 7
    assert policy.stage_names == (
        "discover",
        "shadow",
        "promote",
        "measure",
        "keep",
        "rollback",
        "transfer",
    )


def test_pm_11_soc_policy_validates_five_rung_ladder() -> None:
    policy = SOCPromotionPolicy()

    assert len(policy.stages) == 5
    assert policy.rungs == (
        "observed",
        "assisted",
        "shadow-qualified",
        "auto-approved",
        "circuit-broken",
    )


def test_pm_12_sqlite_save_load_round_trip_preserves_fields(tmp_path) -> None:
    store = PromotionStore(str(tmp_path / "promotion.sqlite3"))
    engine = PromotionEngine(S2PPromotionPolicy(), store=store)
    record = engine.create("s2p", "approval")
    engine.advance(record.record_id, {"reason": "candidate"})

    loaded = store.load(record.record_id)

    assert loaded is not None
    assert loaded.record_id == record.record_id
    assert loaded.copilot == record.copilot
    assert loaded.decision_class == record.decision_class
    assert loaded.stage_history[-1]["stage"] == "shadowing"


def test_pm_13_list_all_scopes_records_by_copilot() -> None:
    engine = _engine()
    engine.create("s2p", "a")
    engine.create("s2p", "b")
    engine.create("soc", "a")

    assert len(engine.get_all("s2p")) == 2
    assert len(engine.get_all("soc")) == 1


def test_pm_14_router_status_returns_current_state() -> None:
    engine = _engine()
    record = engine.create("s2p", "invoice_match")
    app = FastAPI()
    app.include_router(create_promotion_router(engine))

    with TestClient(app) as client:
        response = client.get("/api/promotion/status", params={"copilot": "s2p"})

    assert response.status_code == 200
    assert response.json()["records"][0]["record_id"] == record.record_id


def test_pm_15_router_advance_works_end_to_end() -> None:
    engine = _engine()
    record = engine.create("s2p", "invoice_match")
    app = FastAPI()
    app.include_router(create_promotion_router(engine))

    with TestClient(app) as client:
        first = client.post(f"/api/promotion/{record.record_id}/advance", json={})
        second = client.post(
            f"/api/promotion/{record.record_id}/advance",
            json={"conservation_state": "GREEN", "shadow_decisions": 10},
        )

    assert first.status_code == 200
    assert first.json()["new_stage"] == "shadowing"
    assert second.status_code == 200
    assert second.json()["new_stage"] == "promoted"


def test_pm_16_concurrent_advance_attempts_only_one_succeeds() -> None:
    engine = _engine()
    record = engine.create("s2p", "concurrent")

    def advance() -> bool:
        return engine.advance(record.record_id).advanced

    with ThreadPoolExecutor(max_workers=8) as executor:
        results = list(executor.map(lambda _: advance(), range(8)))

    assert sum(results) == 1
    assert engine.get_authority("s2p", "concurrent") is PromotionStage.SHADOWING


def test_pm_17_keep_requires_improvement_threshold() -> None:
    policy = S2PPromotionPolicy(improvement_threshold=0.05)
    engine = _engine(policy)
    record = engine.create("s2p", "quality")
    _reach_to_measuring(engine, record.record_id)

    result = engine.advance(
        record.record_id,
        {"measurement_decisions": 10, "improvement": 0.05},
    )

    assert result.advanced is False
    assert result.reason == "improvement_below_threshold"


def test_pm_18_transfer_creates_record_in_target_context() -> None:
    engine = _engine()
    record = engine.create("s2p", "supplier_risk")
    _reach_kept(engine, record.record_id)

    result = engine.transfer(record.record_id, "purchasing", "vendor_risk", _green())

    assert result.advanced is True
    assert result.target_record_id is not None
    target = engine.store.load(result.target_record_id)
    assert target is not None
    assert target.copilot == "purchasing"
    assert target.decision_class == "vendor_risk"
    assert target.current_stage is PromotionStage.DISCOVERED


def _reach_to_measuring(engine: PromotionEngine, record_id: str) -> None:
    engine.advance(record_id)
    engine.advance(record_id, _green())
    result = engine.advance(record_id)
    assert result.new_stage is PromotionStage.MEASURING


def test_pm_19_dataops_policy_is_conservative_five_rung_projection() -> None:
    policy = DataOpsPromotionPolicy()

    assert policy.stage_names == SOCPromotionPolicy().stage_names
    assert policy.conservation_required is True
