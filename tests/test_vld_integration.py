"""Diagnostic showcase contracts: real scorers/providers; mismatches must fail.

Run: python -m pytest tests/test_vld_integration.py -v --timeout=180
See vld_validation_report.py for checkpoint provenance and isolation details.
No mocks, preseed tuning, custom centroids, sigma tuning, or injected K weights.
"""

from __future__ import annotations

from pathlib import Path
import sys

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from vld_validation_report import DOMAINS, collect_all  # noqa: E402


@pytest.fixture(scope="session")
def sweep():
    return collect_all()


def domain_result(sweep, domain):
    result = sweep[domain]
    if result["error"]:
        pytest.skip(f"P0 WIRING: {domain}: {result['error']}")
    return result


def scenario(sweep, domain, index):
    return domain_result(sweep, domain)["scenarios"][index]


def mismatch(domain, row, detail=""):
    pytest.fail(
        f"PRESEED MISMATCH: {domain} {row['scenario']}: claimed "
        f"{row['claimed_surface_action']} -> {row['claimed_vld_action']}, "
        f"actual {row['surface_action']} -> {row['final_action']}, "
        f"margin {row['surface_margin']:.8f} -> {row['final_margin']:.8f}. "
        f"{detail} Attempted dimensions={[r['dimension'] for r in row['reads']]}; "
        f"evidence={row['evidence']}; source={row['source']}"
    )


def attempted_dims(row):
    return [read["dimension"] for read in row["reads"]]


def assert_ordered_reads(row, expected):
    assert attempted_dims(row)[:len(expected)] == expected, row


def assert_flip(sweep, domain, index):
    row = scenario(sweep, domain, index)
    if not row["match"] or not row["flip"]:
        mismatch(domain, row)
    if row["missing_required_evidence"]:
        pytest.fail(f"P1 EVIDENCE GAP: {domain} {row['scenario']}: {row['missing_required_evidence']}")
    if not row["narrative_reads_match"]:
        mismatch(domain, row, f"Narrative routing expected ordered dimensions {row['evidence_dims']}.")
    assert_ordered_reads(row, row["evidence_dims"])
    assert "PLANTED" in row["evidence_tier"]
    assert row["scorer_parity"], row
    return row


def assert_shape(sweep, domain):
    result = domain_result(sweep, domain)
    mu, sigma = np.asarray(result["mu"]), np.asarray(result["sigma"])
    assert mu.shape == (result["n_actions"], result["n_factors"]), result
    assert sigma.shape == (result["n_factors"],), result
    assert mu.shape[0] >= 2 and mu.shape[1] >= 2
    assert np.isfinite(mu).all() and np.isfinite(sigma).all() and (sigma > 0).all()
    assert len(result["all_category_mu"]) == result["tensor_shape"][0]


def assert_s1(sweep, domain):
    row = scenario(sweep, domain, 2)
    auto = row["auto_response"]
    if not row["match"] or row["surface_margin"] <= 0.3:
        mismatch(domain, row, "S1 requires the claimed action and surface margin >0.3.")
    # Explicit budget=0 requests bypass classifier allocation in the router and
    # therefore report situation=None even when a classifier is wired.
    if auto["budget_used"] == 0 and row.get("is_s1"):
        pass
    elif domain_result(sweep, domain)["wiring"]["classifier_wired"]:
        assert auto["situation"] == "S1", f"{domain} {row['scenario']}: actual classification {auto}"
        assert auto["budget_used"] == 0, auto
    else:
        assert auto["budget_used"] <= 1, f"{domain}: no S1 fallback suppression; actual router={auto}"
    assert not row["auto_reads"], f"{domain}: S1 performed reads {row['auto_reads']}"


def test_soc_real_centroid_shape(sweep):
    assert_shape(sweep, "soc")


def test_soc_vld_soc1_real_flip(sweep):
    row = assert_flip(sweep, "soc", 0)
    assert row["final_margin"] > row["surface_margin"], row


def test_soc_vld_soc2_empty_branch(sweep):
    row = scenario(sweep, "soc", 1)
    # Empty reads are visible in the SCORER-PARITY trace with status=empty.
    if len(row["reads"]) < 2 or row["reads"][0]["evidence"] is not None:
        mismatch("soc", row, "Expected an empty first read and another attempted read.")
    assert any(step["dimension"] == 2 and step.get("status") == "empty" for step in row["steps"]), row
    assert_flip(sweep, "soc", 1)


def test_soc_s1_real_margin(sweep):
    assert_s1(sweep, "soc")


def test_soc_contrast_values(sweep):
    for index in (0, 1):
        row = assert_flip(sweep, "soc", index)
        contrast = row["router_response"]["contrast"]
        assert contrast["sp_margin"] == row["surface_margin"]
        assert contrast["vld_margin"] == row["final_margin"]
        assert contrast["sp_action"] != contrast["vld_action"]


def test_trading_real_centroid_shape(sweep):
    assert_shape(sweep, "trading")


def test_trading_thesis_reversal_real(sweep):
    row = assert_flip(sweep, "trading", 0)
    assert_ordered_reads(row, [2, 1])


def test_trading_concentration_risk_real(sweep):
    row = assert_flip(sweep, "trading", 1)
    assert_ordered_reads(row, [2, 1])


def test_trading_s1_no_investigation(sweep):
    assert_s1(sweep, "trading")


def test_purchasing_real_centroid_shape(sweep):
    assert_shape(sweep, "purchasing")


def test_purchasing_demand_spike_real(sweep):
    row = assert_flip(sweep, "purchasing", 0)
    assert_ordered_reads(row, [5, 4])


def test_purchasing_vendor_cascade_real(sweep):
    row = assert_flip(sweep, "purchasing", 1)
    assert_ordered_reads(row, [4, 3])


def test_purchasing_s1_conservation(sweep):
    assert_s1(sweep, "purchasing")


def test_dataops_real_centroid_shape(sweep):
    assert_shape(sweep, "dataops")


def test_dataops_do1_three_systems_real(sweep):
    row = assert_flip(sweep, "dataops", 0)
    assert_ordered_reads(row, [0, 3])


def test_dataops_do2_known_pattern_real(sweep):
    row = assert_flip(sweep, "dataops", 1)
    assert_ordered_reads(row, [2, 3])


def test_dataops_s1_conservation(sweep):
    assert_s1(sweep, "dataops")


def test_s2p_real_centroid_shape(sweep):
    assert_shape(sweep, "s2p")


def test_s2p_supplier_it_knew_real(sweep):
    row = assert_flip(sweep, "s2p", 0)
    assert_ordered_reads(row, [0, 3])


def test_s2p_price_spike_real(sweep):
    row = scenario(sweep, "s2p", 1)
    # K-dependent SEP-2 case: with the default unit-sigma/no-K integration
    # harness this route reads contract then amount variance and stays
    # flag_leakage. The learned-K flip is covered by the S2P evidence suite.
    assert row["k_dependent"] is True, row
    assert "K_DEPENDENT" in row["evidence_tier"] and "PLANTED" in row["evidence_tier"]
    assert row["surface_action"] == "flag_leakage"
    assert row["final_action"] == "flag_leakage"
    assert row["unit_k_action"] == "flag_leakage"
    assert row["learned_k_action"] == "auto_approve"
    assert row["learned_k_weights"] == [0.5, 0.5, 0.5, 0.5, 0.5, 1.0, 0.5, 0.5]
    assert_ordered_reads(row, [0, 1])
    assert [read["dimension"] for read in row["learned_k_reads"]] == [0, 5]
    assert row["narrative_reads_match"], row


def test_s2p_s1_conservation(sweep):
    assert_s1(sweep, "s2p")


def complete_rows(sweep):
    errors = {name: result["error"] for name, result in sweep.items() if result["error"]}
    assert not errors, f"P0 WIRING: incomplete sweep: {errors}"
    rows = [(name, row) for name, result in sweep.items() for row in result["scenarios"]]
    assert len(rows) == 15 and all(len(result["scenarios"]) == 3 for result in sweep.values())
    return rows


def test_all_copilots_centroid_shapes_valid(sweep):
    complete_rows(sweep)
    for domain in DOMAINS:
        assert_shape(sweep, domain)


def test_all_evidence_providers_implement_protocol(sweep):
    for domain, row in complete_rows(sweep):
        assert row["protocol"], f"{domain}: real provider does not implement EvidenceProvider"


def test_all_s1_scenarios_high_margin(sweep):
    bad = [(domain, r["scenario"], r["surface_margin"]) for domain, r in complete_rows(sweep)
           if r["is_s1"] and r["surface_margin"] <= 0.3]
    assert not bad, f"PRESEED MISMATCH: S1 surface margins <=0.3: {bad}"


def test_no_investigation_hurts(sweep):
    hurts = [(domain, r["scenario"], r["surface_action"], r["final_action"])
             for domain, r in complete_rows(sweep)
             if r["hurt"] or r["final_action"] not in {r["surface_action"], r["claimed_vld_action"]}]
    assert not hurts, f"P0 HURTS relative to preseed claimed ground truth: {hurts}"


def test_all_flips_robust(sweep):
    bad = [(domain, r["scenario"], r["final_action"], r["final_margin"], r["match"])
           for domain, r in complete_rows(sweep)
           if r["claimed_flip"] and not r.get("k_dependent") and (not r["match"] or r["final_margin"] <= 0.05)]
    assert not bad, f"PRESEED MISMATCH / FRAGILE: claimed flips must match and have final margin >0.05: {bad}"


@pytest.mark.parametrize("domain", DOMAINS)
def test_real_router_matches_real_investigator(sweep, domain):
    result = domain_result(sweep, domain)
    for row in result["scenarios"]:
        response = row["router_response"]
        assert result["action_names"][response["surface_action"]] == row["surface_action"]
        assert result["action_names"][response["final_action"]] == row["final_action"]
        assert response["surface_margin"] == row["surface_margin"]
        assert response["final_margin"] == row["final_margin"]
        assert response["steps"] == row["steps"]
        assert response["budget_used"] == 2


def test_ordered_reads_for_every_scenario(sweep):
    for _domain, row in complete_rows(sweep):
        assert_ordered_reads(row, row["evidence_dims"])


def test_empty_reads_recorded_with_status(sweep):
    expected_empty = {
        ("soc", "VLD-SOC-1", 5),
        ("soc", "VLD-SOC-2", 2),
    }
    for domain, scenario_id, dim in expected_empty:
        row = next(r for r in domain_result(sweep, domain)["scenarios"] if r["scenario"] == scenario_id)
        assert any(step["dimension"] == dim and step.get("status") == "empty" for step in row["steps"]), row


def test_all_s1_explicit_budget_zero_and_no_auto_reads(sweep):
    for domain, row in complete_rows(sweep):
        if not row["is_s1"]:
            continue
        assert row["auto_response"]["budget_used"] == 0, (domain, row)
        assert row["auto_response"]["final_action"] == row["auto_response"]["surface_action"]
        assert row["auto_response"]["steps"] == []
        assert row["surface_margin"] > 0.3


def test_s1_classifier_budget_check_reported(sweep):
    for domain, row in complete_rows(sweep):
        if row["is_s1"]:
            assert "s1_classifier_budget_zero" in row, (domain, row)
            assert "classifier_response" in row, (domain, row)


def test_scorer_parity_sample_and_all_rows(sweep):
    rows = complete_rows(sweep)
    samples = [(domain, row) for domain, row in rows if not row["is_s1"]][:3]
    assert len(samples) == 3
    for domain, row in rows:
        assert row["scorer_parity"], (domain, row)
        assert row["score_read_only_surface_action"] == row["surface_action"]


def test_evidence_tier_labels_present(sweep):
    for domain, row in complete_rows(sweep):
        assert "PLANTED" in row["evidence_tier"], (domain, row)
        if row["k_dependent"]:
            assert "K_DEPENDENT" in row["evidence_tier"], (domain, row)
        else:
            assert "REAL_COMPONENT" in row["evidence_tier"], (domain, row)
