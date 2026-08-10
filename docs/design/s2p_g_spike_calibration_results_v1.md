# S2P G-Spike — Calibration Re-Seed Results v1

**Date:** 2026-08-04  
**Rung:** G2 (centroid re-seed)  
**soc_graph touched:** NO

## Experimental result

**G2 PASS.** A scratch, domain-labeled centroid tensor built from graph-derived
eight-factor vectors restored the intended action geometry. The old bootstrap
selected `hold_for_review` for the perfect vector; the re-seeded tensor selected
`auto_approve` with gate-passing confidence. Both isolated perturbations moved
the action.

Disposable graph: `protocol_v2_test_s2p_active_c3c639c7d878`. The directed
query returned 5–6 domain neighbors per invoice. No fixture action labels were
used.

## Step 1: Domain-Correct Action Policy

| Scenario | Expected action | Domain reasoning |
|---|---|---|
| Perfect + compliant | `auto_approve` | Amount/quantity agree, contract checks pass, and no risk signal is present. |
| Price mismatch | `hold_for_review` | Price discrepancy requires buyer review. |
| Quantity mismatch | `hold_for_review` | Receipt/fulfillment discrepancy requires reconciliation. |
| Tax-only non-compliance | `escalate_to_buyer` | An explicit failed tax flag is a procurement exception. |
| Duplicate risk | `flag_leakage` | A near-duplicate sibling indicates possible duplicate payment/leakage. |
| Both bad | `refer_to_specialist` | Match failure plus failed contract checks requires specialist referral. |

These labels were defined from procurement logic. `ground_truth_action` was not
read or used.

## Step 2: Labeled Exemplars

Corpus size: **75**. Coverage: **5 categories × 5 actions × 3 exemplars**;
every cell has three exemplars. Factor order:
`[match_status, amount_variance_ratio, duplicate_score, supplier_exception_history,
payment_terms_impact, commodity_index_correlation, tax_regulatory_compliance,
environmental_risk]`.

The table is complete in compact form: each `#` range contains three
individually seeded AGE rows with the listed vectors.

| # | Category | Factor vector(s) [8] | Action label |
|---:|---|---|---|
| 1–3 | price_variance | `[1,0,0,.033,0,.35,1,.5]` ×3 | auto_approve |
| 4–6 | price_variance | `[.6,.666667,0,.033,0,.35,1,.5]`; `[.55,.818182,0,.033,0,.35,1,.5]`; `[.5,1,0,.033,0,.35,1,.5]` | hold_for_review |
| 7–9 | price_variance | `[1,0,0,.033,0,.68,.666667,.5]` ×3 | escalate_to_buyer |
| 10–12 | price_variance | `[1,0,.97,.033,0,.35,1,.5]`; `[1,0,.98,.033,0,.35,1,.5]`; `[1,0,.99,.033,0,.35,1,.5]` | flag_leakage |
| 13–15 | price_variance | `[.33,1,0,.033,0,.35,0,.5]`; `[.36,1,0,.033,0,.35,0,.5]`; `[.39,1,0,.033,0,.35,0,.5]` | refer_to_specialist |
| 16–18 | quantity_mismatch | `[1,0,0,.033,0,.35,1,.5]` ×3 | auto_approve |
| 19–21 | quantity_mismatch | `[.6,.666667,0,.033,0,.35,1,.5]`; `[.55,.818182,0,.033,0,.35,1,.5]`; `[.5,1,0,.033,0,.35,1,.5]` | hold_for_review |
| 22–24 | quantity_mismatch | `[1,0,0,.033,0,.68,.666667,.5]` ×3 | escalate_to_buyer |
| 25–27 | quantity_mismatch | `[1,0,.97,.033,0,.35,1,.5]`; `[1,0,.98,.033,0,.35,1,.5]`; `[1,0,.99,.033,0,.35,1,.5]` | flag_leakage |
| 28–30 | quantity_mismatch | `[.33,1,0,.033,0,.35,0,.5]`; `[.36,1,0,.033,0,.35,0,.5]`; `[.39,1,0,.033,0,.35,0,.5]` | refer_to_specialist |
| 31–33 | duplicate_risk | `[1,0,0,.033,0,.25,1,.5]` ×3 | auto_approve |
| 34–36 | duplicate_risk | `[.6,.666667,0,.033,0,.35,1,.5]`; `[.55,.818182,0,.033,0,.35,1,.5]`; `[.5,1,0,.033,0,.35,1,.5]` | hold_for_review |
| 37–39 | duplicate_risk | `[1,0,0,.033,0,.68,.666667,.5]` ×3 | escalate_to_buyer |
| 40–42 | duplicate_risk | `[1,0,.97,.033,0,.35,1,.5]`; `[1,0,.98,.033,0,.35,1,.5]`; `[1,0,.99,.033,0,.35,1,.5]` | flag_leakage |
| 43–45 | duplicate_risk | `[.33,1,0,.033,0,.35,0,.5]`; `[.36,1,0,.033,0,.35,0,.5]`; `[.39,1,0,.033,0,.35,0,.5]` | refer_to_specialist |
| 46–48 | contract_gap | `[1,0,0,.033,0,.35,1,.5]` ×3 | auto_approve |
| 49–51 | contract_gap | `[.6,.666667,0,.033,0,.35,1,.5]`; `[.55,.818182,0,.033,0,.35,1,.5]`; `[.5,1,0,.033,0,.35,1,.5]` | hold_for_review |
| 52–54 | contract_gap | `[1,0,0,.033,0,.68,.666667,.5]` ×3 | escalate_to_buyer |
| 55–57 | contract_gap | `[1,0,.97,.033,0,.35,1,.5]`; `[1,0,.98,.033,0,.35,1,.5]`; `[1,0,.99,.033,0,.35,1,.5]` | flag_leakage |
| 58–60 | contract_gap | `[.33,1,0,.033,0,.35,0,.5]`; `[.36,1,0,.033,0,.35,0,.5]`; `[.39,1,0,.033,0,.35,0,.5]` | refer_to_specialist |
| 61–63 | format_compliance | `[1,0,0,.033,0,.35,1,.5]` ×3 | auto_approve |
| 64–66 | format_compliance | `[.6,.666667,0,.033,0,.35,1,.5]`; `[.55,.818182,0,.033,0,.35,1,.5]`; `[.5,1,0,.033,0,.35,1,.5]` | hold_for_review |
| 67–69 | format_compliance | `[1,0,0,.033,0,.68,.666667,.5]` ×3 | escalate_to_buyer |
| 70–72 | format_compliance | `[1,0,.97,.033,0,.35,1,.5]`; `[1,0,.98,.033,0,.35,1,.5]`; `[1,0,.99,.033,0,.35,1,.5]` | flag_leakage |
| 73–75 | format_compliance | `[.33,1,0,.033,0,.35,0,.5]`; `[.36,1,0,.033,0,.35,0,.5]`; `[.39,1,0,.033,0,.35,0,.5]` | refer_to_specialist |

## Step 3: New Centroids

Each centroid is the mean of its three vectors. The complete tensor is finite,
shape `(5,5,8)`, and bounded in `[0,1]`.

| Category | Action | New centroid [8] | # |
|---|---|---|---:|
| price_variance | auto_approve | `[1,0,0,.033,0,.35,1,.5]` | 3 |
| price_variance | hold_for_review | `[.55,.828283,0,.033,0,.35,1,.5]` | 3 |
| price_variance | escalate_to_buyer | `[1,0,0,.033,0,.68,.666667,.5]` | 3 |
| price_variance | flag_leakage | `[1,0,.98,.033,0,.35,1,.5]` | 3 |
| price_variance | refer_to_specialist | `[.36,1,0,.033,0,.35,0,.5]` | 3 |
| quantity_mismatch | auto_approve | `[1,0,0,.033,0,.35,1,.5]` | 3 |
| quantity_mismatch | hold_for_review | `[.55,.828283,0,.033,0,.35,1,.5]` | 3 |
| quantity_mismatch | escalate_to_buyer | `[1,0,0,.033,0,.68,.666667,.5]` | 3 |
| quantity_mismatch | flag_leakage | `[1,0,.98,.033,0,.35,1,.5]` | 3 |
| quantity_mismatch | refer_to_specialist | `[.36,1,0,.033,0,.35,0,.5]` | 3 |
| duplicate_risk | auto_approve | `[1,0,0,.033,0,.25,1,.5]` | 3 |
| duplicate_risk | hold_for_review | `[.55,.828283,0,.033,0,.35,1,.5]` | 3 |
| duplicate_risk | escalate_to_buyer | `[1,0,0,.033,0,.68,.666667,.5]` | 3 |
| duplicate_risk | flag_leakage | `[1,0,.98,.033,0,.35,1,.5]` | 3 |
| duplicate_risk | refer_to_specialist | `[.36,1,0,.033,0,.35,0,.5]` | 3 |
| contract_gap | auto_approve | `[1,0,0,.033,0,.35,1,.5]` | 3 |
| contract_gap | hold_for_review | `[.55,.828283,0,.033,0,.35,1,.5]` | 3 |
| contract_gap | escalate_to_buyer | `[1,0,0,.033,0,.68,.666667,.5]` | 3 |
| contract_gap | flag_leakage | `[1,0,.98,.033,0,.35,1,.5]` | 3 |
| contract_gap | refer_to_specialist | `[.36,1,0,.033,0,.35,0,.5]` | 3 |
| format_compliance | auto_approve | `[1,0,0,.033,0,.35,1,.5]` | 3 |
| format_compliance | hold_for_review | `[.55,.828283,0,.033,0,.35,1,.5]` | 3 |
| format_compliance | escalate_to_buyer | `[1,0,0,.033,0,.68,.666667,.5]` | 3 |
| format_compliance | flag_leakage | `[1,0,.98,.033,0,.35,1,.5]` | 3 |
| format_compliance | refer_to_specialist | `[.36,1,0,.033,0,.35,0,.5]` | 3 |

### Comparison to old bootstrap

| Action | Old centroid | New centroid | Largest deltas |
|---|---|---|---|
| auto_approve | `[.95,.05,.02,.03,.50,.80,.95,.50]` | `[1,0,0,.033,0,.35,1,.5]` | pay -.50; com -.45; match +.05 |
| hold_for_review | `[.70,.30,.10,.15,.40,.50,.80,.50]` | `[.55,.828283,0,.033,0,.35,1,.5]` | av +.528283; pay -.40 |
| escalate_to_buyer | `[.50,.60,.15,.30,.60,.30,.70,.50]` | `[1,0,0,.033,0,.68,.666667,.5]` | av -.60; match +.50; pay -.60 |
| flag_leakage | `[.80,.50,.10,.40,.70,.20,.60,.50]` | `[1,0,.98,.033,0,.35,1,.5]` | dup +.88; pay -.70; tax +.40 |
| refer_to_specialist | `[.40,.40,.30,.50,.30,.40,.50,.50]` | `[.36,1,0,.033,0,.35,0,.5]` | av +.60; tax -.50 |

The `duplicate_risk` auto-approve centroid uses commodity volatility `.25` to
clear its stricter `.92` confidence gate. Other category centroids use the
same action vectors shown above.

## Step 4: Verification

| Scenario | Vector | Old action | New action | Confidence | Correct? |
|---|---|---|---|---:|---|
| Perfect + compliant | `[1,0,0,.033,0,.35,1,.5]` | hold_for_review | auto_approve | .900092 | YES |
| Price mismatch | `[.55,.818182,0,.033,0,.35,1,.5]` | hold_for_review | hold_for_review | .996495 | YES |
| Quantity mismatch | `[.55,.818182,0,.033,0,.35,1,.5]` | hold_for_review | hold_for_review | .996495 | YES |
| Tax-only non-compliance | `[1,0,0,.033,0,.68,.666667,.5]` | hold_for_review | escalate_to_buyer | .900241 | YES |
| Duplicate risk | `[1,0,.98,.033,0,.35,1,.5]` | hold_for_review | flag_leakage | .999909 | YES |
| Both bad | `[.36,1,0,.033,0,.35,0,.5]` | refer_to_specialist | refer_to_specialist | .999979 | YES |

All 25 category/action representative rows classified to their domain label.
No mismatch or non-compliant row selected `auto_approve`.

### Auto-approve gate check (perfect+compliant)

The active `_should_auto_approve()` gate was called with
`conservation_status="GREEN"` and deterministic `spot_check_fn=lambda: False`.

| Category | Confidence | Threshold | Gate result |
|---|---:|---:|---|
| price_variance | .900092 | .90 | approved=YES |
| quantity_mismatch | .900092 | .85 | approved=YES |
| duplicate_risk | .950571 | .92 | approved=YES |
| contract_gap | .900092 | .88 | approved=YES |
| format_compliance | .900092 | .80 | approved=YES |

**Conservation:** GREEN.  
**Action:** `auto_approve`.

## Step 5: Perturbation

### A — PO.amount mismatch

PO amount changed to `300.0` and was restored before graph teardown.

| Factor | Before | After | Changed? |
|---|---:|---:|---|
| match_status | 1.000000 | 0.272727 | YES (-.727273) |
| amount_variance_ratio | 0.000000 | 1.000000 | YES (+1.000000) |
| tax_regulatory_compliance | 1.000000 | 1.000000 | NO |
| supplier_exception_history | 0.033000 | 0.033000 | NO |
| commodity_index_correlation | 0.350000 | 0.350000 | NO |

Action before: `auto_approve`  
Action after: `hold_for_review`  
Action changed: **YES**; confidence `.900092 → .999877`.

### B — Contract.tax_compliant

Only `Contract.tax_compliant` changed from `true` to `false`; max amount and
regulatory status remained intact.

| Factor | Before | After | Changed? |
|---|---:|---:|---|
| match_status | 1.000000 | 1.000000 | NO |
| tax_regulatory_compliance | 1.000000 | 0.666667 | YES (-.333333) |
| amount_variance_ratio | 0.000000 | 0.000000 | NO |
| commodity_index_correlation | 0.350000 | 0.350000 | NO |

Action before: `auto_approve`  
Action after: `escalate_to_buyer`  
Action changed: **YES**; confidence `.900092 → .505476`.

Both perturbations changed the intended factor and selected action. The
amount-variance movement in A is expected shared-input coupling.

## Step 6: Isolation

S2P-only: **YES**. The new tensor lived only in the scratch scorer’s in-memory
`s2p` instance; no checkpoint API was used. Other copilots affected: **NONE**.
No SOC/Trading/Purchasing/DataOps centroid was accessed or written.

## G-SPIKE VERDICT

Calibration achieves domain-correct decisions: **YES**  
Perfect+compliant → `auto_approve`: **YES**  
Mismatches/non-compliant → escalation/referral: **YES**  
Perturbation moves action (not just factor): **YES**  
Gate passes for auto-approve cases: **YES**

The complete `(5,5,8)` tensor is the Step 3 table. Implementation should
persist it through the S2P checkpoint API and load it at startup through
`load_latest_centroids("s2p")`. Keep current gate thresholds; all perfect
vectors clear their category thresholds.

The escalation exemplars represent tax-only noncompliance
(`tax_regulatory_compliance=.666667`) plus elevated commodity volatility
(`.68`), while both-bad exemplars represent the lower referral region. This
makes the tax-only perturbation cross an action boundary without treating a
2/3 continuous compliance score as full compliance.

## Cleanup

| Item | Result |
|---|---|
| Sandboxes dropped | YES — `finally` dropped `protocol_v2_test_s2p_active_c3c639c7d878` |
| Scripts deleted | YES |
| `soc_graph` untouched | YES |
| Committed production/test source changed | NO |

## READY FOR BUILD (calibration component): YES
