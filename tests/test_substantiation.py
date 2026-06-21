from dataclasses import FrozenInstanceError, fields

import pytest

from copilot_sdk.substantiation import (
    ClaimProvenance,
    ClaimRegistry,
    DayZeroReadiness,
    PromotionEvent,
    TIER_LANGUAGE,
    Tier,
    populate_default_readiness,
    populate_default_registry,
)


def _claim(
    *,
    claim_id: str = "C1",
    tier: Tier = Tier.SCRAPED,
    is_magnitude_claim: bool = False,
) -> ClaimProvenance:
    return ClaimProvenance(
        claim_id=claim_id,
        text="Example claim",
        tier=tier,
        evidence_ref="evidence",
        is_magnitude_claim=is_magnitude_claim,
        copilot="test",
        feature="test-feature",
    )


def test_tier_values():
    assert {tier.value for tier in Tier} == {
        "analytic",
        "scraped_external",
        "oracle_synthetic",
        "real_measured",
    }


def test_tier_str_values():
    assert Tier.ANALYTIC == "analytic"
    assert Tier.SCRAPED == "scraped_external"
    assert Tier.ORACLE == "oracle_synthetic"
    assert Tier.REAL == "real_measured"


def test_claim_provenance_frozen():
    claim = _claim()
    with pytest.raises(FrozenInstanceError):
        claim.tier = Tier.REAL


def test_claim_provenance_all_fields():
    claim = _claim()
    expected = {
        "claim_id",
        "text",
        "tier",
        "evidence_ref",
        "is_magnitude_claim",
        "copilot",
        "feature",
    }
    assert {field.name for field in fields(ClaimProvenance)} == expected
    assert claim.claim_id == "C1"
    assert claim.text == "Example claim"
    assert claim.tier == Tier.SCRAPED
    assert claim.evidence_ref == "evidence"
    assert claim.is_magnitude_claim is False
    assert claim.copilot == "test"
    assert claim.feature == "test-feature"


def test_claim_valid():
    ok, why = _claim(tier=Tier.SCRAPED).is_valid()
    assert ok is True
    assert why == "ok"


def test_claim_magnitude_scraped_invalid():
    ok, why = _claim(tier=Tier.SCRAPED, is_magnitude_claim=True).is_valid()
    assert ok is False
    assert "requires REAL" in why


def test_claim_magnitude_real_valid():
    ok, why = _claim(tier=Tier.REAL, is_magnitude_claim=True).is_valid()
    assert ok is True
    assert why == "ok"


def test_claim_magnitude_oracle_invalid():
    ok, why = _claim(tier=Tier.ORACLE, is_magnitude_claim=True).is_valid()
    assert ok is False
    assert "oracle_synthetic" in why


def test_register_valid_claim():
    registry = ClaimRegistry()
    claim = _claim()
    registry.register(claim)
    assert registry.get(claim.claim_id) == claim


def test_register_magnitude_violation():
    registry = ClaimRegistry()
    with pytest.raises(ValueError, match="F-24"):
        registry.register(_claim(tier=Tier.SCRAPED, is_magnitude_claim=True))


def test_register_duplicate_claim_id():
    registry = ClaimRegistry()
    registry.register(_claim(claim_id="C1", tier=Tier.SCRAPED))
    registry.register(_claim(claim_id="C1", tier=Tier.ANALYTIC))
    assert len(registry.all_claims()) == 1
    assert registry.get("C1").tier == Tier.ANALYTIC


def test_promote_to_real_needs_evidence():
    registry = ClaimRegistry()
    registry.register(_claim())
    with pytest.raises(ValueError, match="requires pilot evidence_ref"):
        registry.promote(
            PromotionEvent(
                claim_id="C1",
                from_tier=Tier.SCRAPED,
                to_tier=Tier.REAL,
                evidence_ref="",
                approved_by="roadmap",
                date="2026-06-20",
            )
        )


def test_promote_to_real_with_evidence():
    registry = ClaimRegistry()
    registry.register(_claim())
    registry.promote(
        PromotionEvent(
            claim_id="C1",
            from_tier=Tier.SCRAPED,
            to_tier=Tier.REAL,
            evidence_ref="pilot metric 42",
            approved_by="roadmap",
            date="2026-06-20",
        )
    )
    assert registry.get("C1").tier == Tier.REAL


def test_promote_nonexistent_claim():
    registry = ClaimRegistry()
    with pytest.raises(KeyError):
        registry.promote(
            PromotionEvent(
                claim_id="MISSING",
                from_tier=Tier.SCRAPED,
                to_tier=Tier.REAL,
                evidence_ref="pilot",
                approved_by="roadmap",
                date="2026-06-20",
            )
        )


def test_promote_updates_tier():
    registry = ClaimRegistry()
    registry.register(_claim())
    registry.promote(
        PromotionEvent(
            claim_id="C1",
            from_tier=Tier.SCRAPED,
            to_tier=Tier.ANALYTIC,
            evidence_ref="theorem",
            approved_by="reviewer",
            date="2026-06-20",
        )
    )
    assert registry.get("C1").tier == Tier.ANALYTIC


def test_promote_from_analytic_to_scraped():
    registry = ClaimRegistry()
    registry.register(_claim(tier=Tier.ANALYTIC))
    registry.promote(
        PromotionEvent(
            claim_id="C1",
            from_tier=Tier.ANALYTIC,
            to_tier=Tier.SCRAPED,
            evidence_ref="external data source",
            approved_by="reviewer",
            date="2026-06-20",
        )
    )
    claim = registry.get("C1")
    assert claim.tier == Tier.SCRAPED
    assert claim.evidence_ref == "external data source"


def test_promote_to_oracle_without_evidence():
    registry = ClaimRegistry()
    registry.register(_claim(tier=Tier.SCRAPED))
    registry.promote(
        PromotionEvent(
            claim_id="C1",
            from_tier=Tier.SCRAPED,
            to_tier=Tier.ORACLE,
            evidence_ref="",
            approved_by="reviewer",
            date="2026-06-20",
        )
    )
    claim = registry.get("C1")
    assert claim.tier == Tier.ORACLE
    assert claim.evidence_ref == ""


def test_promote_history():
    registry = ClaimRegistry()
    registry.register(_claim())
    event = PromotionEvent(
        claim_id="C1",
        from_tier=Tier.SCRAPED,
        to_tier=Tier.REAL,
        evidence_ref="pilot",
        approved_by="roadmap",
        date="2026-06-20",
    )
    registry.promote(event)
    assert registry.history() == [event]


def test_registry_empty():
    registry = ClaimRegistry()
    assert registry.all_claims() == []
    assert registry.history() == []
    assert registry.get("MISSING") is None


def test_sales_safe():
    registry = ClaimRegistry()
    registry.register(_claim(tier=Tier.ANALYTIC))
    assert "Proven mathematically" in registry.sales_safe("C1")


def test_sales_safe_all_tiers():
    registry = ClaimRegistry()
    for tier in Tier:
        claim_id = f"claim-{tier.value}"
        registry.register(_claim(claim_id=claim_id, tier=tier))
        assert registry.sales_safe(claim_id)
        assert registry.sales_safe(claim_id) == TIER_LANGUAGE[tier]


def test_sales_safe_missing_claim():
    registry = ClaimRegistry()
    with pytest.raises(KeyError):
        registry.sales_safe("MISSING")


def test_get_claim():
    registry = ClaimRegistry()
    claim = _claim(claim_id="CLAIM-X")
    registry.register(claim)
    assert registry.get("CLAIM-X") == claim


def test_all_claims():
    registry = ClaimRegistry()
    registry.register(_claim(claim_id="C1"))
    registry.register(_claim(claim_id="C2"))
    assert {claim.claim_id for claim in registry.all_claims()} == {"C1", "C2"}


def test_readiness_all_true():
    readiness = DayZeroReadiness(
        feature="P1",
        copilot="test",
        populated=True,
        proven=True,
        instrumented=True,
        real_path_committed=True,
        labels_honest=True,
    )
    assert readiness.gate() == (True, [])


def test_readiness_missing_populated():
    readiness = DayZeroReadiness(
        feature="P1",
        copilot="test",
        populated=False,
        proven=True,
        instrumented=True,
        real_path_committed=True,
        labels_honest=True,
    )
    assert readiness.gate() == (False, ["populated"])


def test_readiness_single_missing():
    fields_to_check = [
        "populated",
        "proven",
        "instrumented",
        "real_path_committed",
        "labels_honest",
    ]
    for missing_field in fields_to_check:
        values = {field: True for field in fields_to_check}
        values[missing_field] = False
        readiness = DayZeroReadiness(feature="P1", copilot="test", **values)
        assert readiness.gate() == (False, [missing_field])


def test_readiness_na_fields():
    readiness = DayZeroReadiness(
        feature="no-analytic-claim-feature",
        copilot="test",
        populated=True,
        proven=True,
        instrumented=True,
        real_path_committed=True,
        labels_honest=True,
    )
    assert readiness.gate() == (True, [])


def test_readiness_missing_multiple():
    readiness = DayZeroReadiness(
        feature="P1",
        copilot="test",
        populated=True,
        proven=False,
        instrumented=True,
        real_path_committed=False,
        labels_honest=True,
    )
    assert readiness.gate() == (False, ["proven", "real_path_committed"])


def test_readiness_all_false():
    readiness = DayZeroReadiness(
        feature="P1",
        copilot="test",
        populated=False,
        proven=False,
        instrumented=False,
        real_path_committed=False,
        labels_honest=False,
    )
    assert readiness.gate() == (
        False,
        [
            "populated",
            "proven",
            "instrumented",
            "real_path_committed",
            "labels_honest",
        ],
    )


def test_populate_default():
    registry = populate_default_registry()
    assert len(registry.all_claims()) == 32


def test_populate_count():
    registry = populate_default_registry()
    assert len(registry.all_claims()) == 32


def test_populate_no_magnitude_violations():
    registry = populate_default_registry()
    assert all(claim.is_valid()[0] for claim in registry.all_claims())


def test_populate_claim_ids_unique():
    registry = populate_default_registry()
    claim_ids = [claim.claim_id for claim in registry.all_claims()]
    assert len(claim_ids) == len(set(claim_ids))


def test_populate_evidence_refs_nonempty():
    registry = populate_default_registry()
    assert all(claim.evidence_ref.strip() for claim in registry.all_claims())


def test_populate_features_nonempty():
    registry = populate_default_registry()
    assert all(claim.feature.strip() for claim in registry.all_claims())


def test_populate_magnitude_safety():
    registry = populate_default_registry()
    assert all(
        claim.tier == Tier.REAL
        for claim in registry.all_claims()
        if claim.is_magnitude_claim
    )


def test_populate_has_soc_gamma():
    registry = populate_default_registry()
    assert registry.get("SOC-gamma").tier == Tier.ANALYTIC


def test_populate_has_purchasing_qbo():
    registry = populate_default_registry()
    assert registry.get("P66-qbo").tier == Tier.SCRAPED


def test_populate_has_verify_real():
    registry = populate_default_registry()
    assert registry.get("P71-verify").tier == Tier.REAL


def test_populate_all_copilots():
    registry = populate_default_registry()
    assert {claim.copilot for claim in registry.all_claims()} == {
        "soc",
        "s2p",
        "trading",
        "purchasing",
        "dataops",
        "cross_copilot",
    }


def test_f24_enforcement_end_to_end():
    registry = ClaimRegistry()
    with pytest.raises(ValueError, match="F-24"):
        registry.register(
            _claim(
                claim_id="oracle-magnitude",
                tier=Tier.ORACLE,
                is_magnitude_claim=True,
            )
        )

    registry.register(
        _claim(claim_id="real-magnitude", tier=Tier.REAL, is_magnitude_claim=True)
    )
    assert registry.get("real-magnitude").tier == Tier.REAL

    registry.register(_claim(claim_id="promote-with-evidence", tier=Tier.SCRAPED))
    registry.promote(
        PromotionEvent(
            claim_id="promote-with-evidence",
            from_tier=Tier.SCRAPED,
            to_tier=Tier.REAL,
            evidence_ref="pilot metric",
            approved_by="roadmap",
            date="2026-06-20",
        )
    )
    assert registry.get("promote-with-evidence").tier == Tier.REAL

    registry.register(_claim(claim_id="promote-without-evidence", tier=Tier.SCRAPED))
    with pytest.raises(ValueError, match="requires pilot evidence_ref"):
        registry.promote(
            PromotionEvent(
                claim_id="promote-without-evidence",
                from_tier=Tier.SCRAPED,
                to_tier=Tier.REAL,
                evidence_ref="",
                approved_by="roadmap",
                date="2026-06-20",
            )
        )


def test_readiness_plus_registry():
    registry = ClaimRegistry()
    registry.register(
        ClaimProvenance(
            claim_id="feature-populated",
            text="Feature populated from external data",
            tier=Tier.SCRAPED,
            evidence_ref="external source",
            is_magnitude_claim=False,
            copilot="test",
            feature="P1",
        )
    )
    registry.register(
        ClaimProvenance(
            claim_id="feature-mechanism",
            text="Feature mechanism has analytic proof",
            tier=Tier.ANALYTIC,
            evidence_ref="theorem",
            is_magnitude_claim=False,
            copilot="test",
            feature="P1",
        )
    )
    readiness = DayZeroReadiness(
        feature="P1",
        copilot="test",
        populated=registry.get("feature-populated") is not None,
        proven=registry.get("feature-mechanism") is not None,
        instrumented=True,
        real_path_committed=True,
        labels_honest=True,
    )
    assert readiness.gate() == (True, [])


def test_c21_canonical_exists():
    registry = populate_default_registry()
    claim = registry.get("C-21")
    assert claim is not None
    assert claim.tier == Tier.ANALYTIC
    assert claim.is_magnitude_claim is False
    assert claim.copilot == "cross_copilot"
    assert claim.feature == "canonical"


def test_c22_canonical_exists():
    registry = populate_default_registry()
    claim = registry.get("C-22")
    assert claim is not None
    assert claim.tier == Tier.SCRAPED
    assert claim.is_magnitude_claim is False
    assert claim.copilot == "cross_copilot"
    assert claim.feature == "canonical"


def test_readiness_entries_exist():
    assert len(populate_default_readiness()) == 7


def test_soc_campaign_gate_passes():
    entry = next(
        r
        for r in populate_default_readiness()
        if r.feature == "SOC-campaign-intelligence"
    )
    assert entry.gate() == (True, [])


def test_purchasing_p73_gate_fails():
    entry = next(
        r for r in populate_default_readiness() if r.feature == "P73-par-intelligence"
    )
    ok, missing = entry.gate()
    assert ok is False
    assert missing == ["proven"]


def test_all_entries_have_copilot():
    assert all(entry.copilot.strip() for entry in populate_default_readiness())


def test_readiness_gate_logic():
    passing = DayZeroReadiness(
        feature="feature",
        copilot="test",
        populated=True,
        proven=True,
        instrumented=True,
        real_path_committed=True,
        labels_honest=True,
    )
    assert passing.gate() == (True, [])

    failing = DayZeroReadiness(
        feature="feature",
        copilot="test",
        populated=True,
        proven=True,
        instrumented=False,
        real_path_committed=True,
        labels_honest=True,
    )
    assert failing.gate() == (False, ["instrumented"])


def test_total_claims_with_canonicals():
    registry = populate_default_registry()
    assert len(registry.all_claims()) == 32


def test_promote_analytic_to_real_requires_evidence():
    registry = ClaimRegistry()
    registry.register(_claim(claim_id="analytic-claim", tier=Tier.ANALYTIC))

    with pytest.raises(ValueError, match="requires pilot evidence_ref"):
        registry.promote(
            PromotionEvent(
                claim_id="analytic-claim",
                from_tier=Tier.ANALYTIC,
                to_tier=Tier.REAL,
                evidence_ref="",
                approved_by="roadmap",
                date="2026-06-20",
            )
        )


def test_promote_with_evidence_succeeds():
    registry = ClaimRegistry()
    registry.register(_claim(claim_id="pilot-claim", tier=Tier.SCRAPED))

    registry.promote(
        PromotionEvent(
            claim_id="pilot-claim",
            from_tier=Tier.SCRAPED,
            to_tier=Tier.REAL,
            evidence_ref="EXP-G1",
            approved_by="roadmap",
            date="2026-06-20",
        )
    )

    claim = registry.get("pilot-claim")
    assert claim.tier == Tier.REAL
    assert claim.evidence_ref == "EXP-G1"


def test_promote_preserves_history():
    registry = ClaimRegistry()
    registry.register(_claim(claim_id="history-claim", tier=Tier.SCRAPED))
    event = PromotionEvent(
        claim_id="history-claim",
        from_tier=Tier.SCRAPED,
        to_tier=Tier.REAL,
        evidence_ref="pilot outcome",
        approved_by="roadmap",
        date="2026-06-20",
    )

    registry.promote(event)

    assert registry.history() == [event]


def test_promote_updates_claim_tier():
    registry = ClaimRegistry()
    registry.register(_claim(claim_id="tier-claim", tier=Tier.ORACLE))

    registry.promote(
        PromotionEvent(
            claim_id="tier-claim",
            from_tier=Tier.ORACLE,
            to_tier=Tier.SCRAPED,
            evidence_ref="external data",
            approved_by="reviewer",
            date="2026-06-20",
        )
    )

    assert registry.get("tier-claim").tier == Tier.SCRAPED


def test_sales_safe_returns_tier_language():
    registry = ClaimRegistry()
    registry.register(_claim(claim_id="analytic-safe", tier=Tier.ANALYTIC))
    registry.register(_claim(claim_id="scraped-safe", tier=Tier.SCRAPED))
    registry.register(_claim(claim_id="oracle-safe", tier=Tier.ORACLE))

    assert "Proven mathematically" in registry.sales_safe("analytic-safe")
    assert "Populated day-zero" in registry.sales_safe("scraped-safe")
    assert "capability runs" in registry.sales_safe("oracle-safe")


def test_c21_canonical_sales_safe():
    registry = populate_default_registry()
    assert "Proven mathematically" in registry.sales_safe("C-21")


def test_c22_canonical_sales_safe():
    registry = populate_default_registry()
    assert "Populated day-zero" in registry.sales_safe("C-22")


def test_f24_blocks_magnitude_at_oracle():
    registry = ClaimRegistry()

    with pytest.raises(ValueError, match="F-24"):
        registry.register(
            _claim(
                claim_id="oracle-magnitude-blocked",
                tier=Tier.ORACLE,
                is_magnitude_claim=True,
            )
        )


def test_f24_allows_magnitude_at_real():
    registry = ClaimRegistry()
    registry.register(
        _claim(
            claim_id="real-magnitude-allowed",
            tier=Tier.REAL,
            is_magnitude_claim=True,
        )
    )

    assert registry.get("real-magnitude-allowed").tier == Tier.REAL


def test_readiness_all_true_passes():
    readiness = DayZeroReadiness(
        feature="ready-feature",
        copilot="test",
        populated=True,
        proven=True,
        instrumented=True,
        real_path_committed=True,
        labels_honest=True,
    )

    assert readiness.gate() == (True, [])


def test_readiness_each_false_fails():
    gate_fields = [
        "populated",
        "proven",
        "instrumented",
        "real_path_committed",
        "labels_honest",
    ]

    for field_name in gate_fields:
        values = {field: True for field in gate_fields}
        values[field_name] = False
        readiness = DayZeroReadiness(
            feature=f"missing-{field_name}",
            copilot="test",
            **values,
        )
        assert readiness.gate() == (False, [field_name])


def test_readiness_multiple_false():
    readiness = DayZeroReadiness(
        feature="multi-missing",
        copilot="test",
        populated=False,
        proven=True,
        instrumented=False,
        real_path_committed=True,
        labels_honest=False,
    )

    assert readiness.gate() == (
        False,
        ["populated", "instrumented", "labels_honest"],
    )


def test_readiness_soc_is_only_pass():
    passing = [
        entry.feature
        for entry in populate_default_readiness()
        if entry.gate()[0]
    ]

    assert passing == ["SOC-campaign-intelligence"]


def test_readiness_purchasing_fails_on_proven():
    entry = next(
        readiness
        for readiness in populate_default_readiness()
        if readiness.feature == "P73-par-intelligence"
    )

    assert entry.gate() == (False, ["proven"])


def test_readiness_trading_fails_on_proven():
    entry = next(
        readiness
        for readiness in populate_default_readiness()
        if readiness.feature == "P53-trust-radar"
    )

    assert entry.gate() == (False, ["proven"])
