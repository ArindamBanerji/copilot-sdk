# D1 — Verified-outcome recursion trace

Date: September 14, 2026 · random_state=42

**Tier: REAL_COMPONENT geometry + SIMULATED verification; PLANTED FIXTURE starting state and evidence.**
Executed locally with production VLDInvestigator.compute_Q/investigate, KUtilityStore.update_weights, and S2PEvidenceProvider against exported production geometry and the existing in-memory S2P-SC2 preseed. No operational invoice, signed contract, human verification, application database write, or live AGE claim.

## Outcome and experimental isolation

One actual in-memory verification callback updates K. The next identical-feature invoice at B=2 changes from flag_leakage (frozen counterfactual, reads 0→1) to auto_approve (updated K, reads 0→5). The preceding acquisition episode explicitly uses B=3 to acquire dim 5. Repeating the B=2 cold-start case cannot discover an unread factor by itself.

Initial K5=.62 is a **planted near-boundary warm state**, not a measured learning history. It is reachable from .5 by six +.02 non-flip credits, but those six events were not executed or claimed here. The prepaper's recommended K5=1.0 is a different planted state. This example uses .62→.66; one verification does not produce .5→1.0.

Investigation and the K update leave μ unchanged: **Δμ=0 for every cell (5×8)**; Δσ=0. This records K-only RGI, not centroid learning. No conservation gate is invoked by this local KUtilityStore callback. A1's gate/lifecycle findings remain open; this trace does not establish production safety.

## Source geometry and initial state

Category supplied: price_variance. Category classification is not evaluated.
Factor order: ["match_status", "amount_variance_ratio", "duplicate_score", "supplier_exception_history", "payment_terms_impact", "commodity_index_correlation", "tax_regulatory_compliance", "environmental_risk"].
Action order: ["auto_approve", "hold_for_review", "escalate_to_buyer", "flag_leakage", "refer_to_specialist"].
v0 (factor vector, not action probabilities): [0.9237, 0.101, 0.0568, 0.0, 0.6731, 0.0, 0.3416, 0.2494].
Initial action probabilities: [0.003012061909648834, 0.015785021037539645, 0.04330600732936318, 0.9342007611079798, 0.0036961486154686346].
σ=[1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0]; τ=0.1. Export uses unit-sigma fallback.
K before verification: [0.5, 0.5, 0.5, 0.5, 0.5, 0.62, 0.5, 0.5].

μ rows, in the action/factor order above:
~~~json
[
  [
    0.9419976248269532,
    0.07160378157386231,
    0.02533491678203125,
    0.08,
    0.4946650832179687,
    0.7893301664359375,
    0.9366627080449219,
    0.5
  ],
  [
    0.5572065752806293,
    0.29901926041493887,
    0.05921895209957488,
    0.3150000000000001,
    0.48116979996682585,
    0.5009807395850613,
    0.8813659478838379,
    0.5
  ],
  [
    0.5,
    0.6,
    0.15,
    0.3,
    0.6,
    0.3,
    0.7,
    0.5
  ],
  [
    0.8,
    0.5,
    0.1,
    0.4,
    0.7,
    0.2,
    0.6,
    0.5
  ],
  [
    0.4,
    0.4,
    0.3,
    0.5,
    0.3,
    0.4,
    0.5,
    0.5
  ]
]
~~~

## Contract entitlement and provenance

Contract: CTR-MERIDIAN-BULK; source=contract_db; value=0.93; confidence=0.9.

> Bulk pricing pass-through activates above 2x forecast volume.

Volume: source=demand_forecast; value=0.82; confidence=0.78; volume_multiplier=3.0. Explanation: Rush order exceeds the 2x bulk-pricing threshold.

The fixture's 3× volume exceeds its 2× clause trigger: the simulated approval rationale. **There is no commodity-index entitlement clause in this source fixture.** The commodity_index_correlation factor is populated with contract/volume context, not a computed index correlation. The bulk-volume clause above is verbatim; no index clause has been invented. Neither correlation nor a high normalized factor proves entitlement. The investigator does not parse or enforce the clause: the simulated verifier supplies the contractual interpretation.

Sources: ../s2p-copilot/backend/app/vld_preseed.py and evidence_provider.py. Provider results include fixture clause and source metadata. Reads use ungated coordinate replacement; confidence is recorded, not used as damping.

## 1. Frozen B=2 counterfactual for the subsequent invoice

Decision NEXT-INVOICE-frozen-counterfactual; budget=2; surface=flag_leakage; final=flag_leakage; halt=budget_exhausted.

### Read 0: match_status

v_before: [0.9237, 0.101, 0.0568, 0.0, 0.6731, 0.0, 0.3416, 0.2494].
Top actions: flag_leakage, escalate_to_buyer.

| Dim / factor | Precision | Discriminative | Leverage | Base Q | K | Weighted Q |
|---|---:|---:|---:|---:|---:|---:|
| 0 / match_status | 0.01000000 | 0.30000000 | 0.16422000 | 0.47422000 | 0.50000000 | 0.23711000 |
| 1 / amount_variance_ratio | 0.01000000 | 0.10000000 | 0.08980000 | 0.19980000 | 0.50000000 | 0.09990000 |
| 2 / duplicate_score | 0.01000000 | 0.05000000 | 0.00682000 | 0.06682000 | 0.50000000 | 0.03341000 |
| 3 / supplier_exception_history | 0.01000000 | 0.10000000 | 0.07000000 | 0.18000000 | 0.50000000 | 0.09000000 |
| 4 / payment_terms_impact | 0.01000000 | 0.10000000 | 0.00462000 | 0.11462000 | 0.50000000 | 0.05731000 |
| 5 / commodity_index_correlation | 0.01000000 | 0.10000000 | 0.05000000 | 0.16000000 | 0.62000000 | 0.09920000 |
| 6 / tax_regulatory_compliance | 0.01000000 | 0.10000000 | 0.06168000 | 0.17168000 | 0.50000000 | 0.08584000 |
| 7 / environmental_risk | 0.01000000 | 0.00000000 | 0.00000000 | 0.01000000 | 0.50000000 | 0.00500000 |

Evidence payload: {"value": 0.93, "confidence": 0.9, "source": "contract_db", "contract_ref": "CTR-MERIDIAN-BULK", "clause": "Bulk pricing pass-through activates above 2x forecast volume.", "coverage_score": 0.93, "dimension": 0, "factor_name": "match_status", "invoice_id": "VLD-S2P-2"}.
v_after: [0.93, 0.101, 0.0568, 0.0, 0.6731, 0.0, 0.3416, 0.2494].
Action: **flag_leakage → flag_leakage**; flipped=False; status=acquired.

### Read 1: amount_variance_ratio

v_before: [0.93, 0.101, 0.0568, 0.0, 0.6731, 0.0, 0.3416, 0.2494].
Top actions: flag_leakage, escalate_to_buyer.

| Dim / factor | Precision | Discriminative | Leverage | Base Q | K | Weighted Q |
|---|---:|---:|---:|---:|---:|---:|
| 0 / match_status | 0.01000000 | 0.30000000 | 0.16800000 | 0.47800000 | 0.50000000 | excluded |
| 1 / amount_variance_ratio | 0.01000000 | 0.10000000 | 0.08980000 | 0.19980000 | 0.50000000 | 0.09990000 |
| 2 / duplicate_score | 0.01000000 | 0.05000000 | 0.00682000 | 0.06682000 | 0.50000000 | 0.03341000 |
| 3 / supplier_exception_history | 0.01000000 | 0.10000000 | 0.07000000 | 0.18000000 | 0.50000000 | 0.09000000 |
| 4 / payment_terms_impact | 0.01000000 | 0.10000000 | 0.00462000 | 0.11462000 | 0.50000000 | 0.05731000 |
| 5 / commodity_index_correlation | 0.01000000 | 0.10000000 | 0.05000000 | 0.16000000 | 0.62000000 | 0.09920000 |
| 6 / tax_regulatory_compliance | 0.01000000 | 0.10000000 | 0.06168000 | 0.17168000 | 0.50000000 | 0.08584000 |
| 7 / environmental_risk | 0.01000000 | 0.00000000 | 0.00000000 | 0.01000000 | 0.50000000 | 0.00500000 |

Evidence payload: {"value": 0.05, "confidence": 0.82, "source": "pricing_benchmark", "benchmark_delta_pct": 18.0, "sample_size": 41, "dimension": 1, "factor_name": "amount_variance_ratio", "invoice_id": "VLD-S2P-2"}.
v_after: [0.93, 0.05, 0.0568, 0.0, 0.6731, 0.0, 0.3416, 0.2494].
Action: **flag_leakage → flag_leakage**; flipped=False; status=acquired.

## 2. Acquisition episode A before verification (B=3)

Decision VERIFICATION-INVOICE-A; budget=3; surface=flag_leakage; final=auto_approve; halt=budget_exhausted.

### Read 0: match_status

v_before: [0.9237, 0.101, 0.0568, 0.0, 0.6731, 0.0, 0.3416, 0.2494].
Top actions: flag_leakage, escalate_to_buyer.

| Dim / factor | Precision | Discriminative | Leverage | Base Q | K | Weighted Q |
|---|---:|---:|---:|---:|---:|---:|
| 0 / match_status | 0.01000000 | 0.30000000 | 0.16422000 | 0.47422000 | 0.50000000 | 0.23711000 |
| 1 / amount_variance_ratio | 0.01000000 | 0.10000000 | 0.08980000 | 0.19980000 | 0.50000000 | 0.09990000 |
| 2 / duplicate_score | 0.01000000 | 0.05000000 | 0.00682000 | 0.06682000 | 0.50000000 | 0.03341000 |
| 3 / supplier_exception_history | 0.01000000 | 0.10000000 | 0.07000000 | 0.18000000 | 0.50000000 | 0.09000000 |
| 4 / payment_terms_impact | 0.01000000 | 0.10000000 | 0.00462000 | 0.11462000 | 0.50000000 | 0.05731000 |
| 5 / commodity_index_correlation | 0.01000000 | 0.10000000 | 0.05000000 | 0.16000000 | 0.62000000 | 0.09920000 |
| 6 / tax_regulatory_compliance | 0.01000000 | 0.10000000 | 0.06168000 | 0.17168000 | 0.50000000 | 0.08584000 |
| 7 / environmental_risk | 0.01000000 | 0.00000000 | 0.00000000 | 0.01000000 | 0.50000000 | 0.00500000 |

Evidence payload: {"value": 0.93, "confidence": 0.9, "source": "contract_db", "contract_ref": "CTR-MERIDIAN-BULK", "clause": "Bulk pricing pass-through activates above 2x forecast volume.", "coverage_score": 0.93, "dimension": 0, "factor_name": "match_status", "invoice_id": "VLD-S2P-2"}.
v_after: [0.93, 0.101, 0.0568, 0.0, 0.6731, 0.0, 0.3416, 0.2494].
Action: **flag_leakage → flag_leakage**; flipped=False; status=acquired.

### Read 1: amount_variance_ratio

v_before: [0.93, 0.101, 0.0568, 0.0, 0.6731, 0.0, 0.3416, 0.2494].
Top actions: flag_leakage, escalate_to_buyer.

| Dim / factor | Precision | Discriminative | Leverage | Base Q | K | Weighted Q |
|---|---:|---:|---:|---:|---:|---:|
| 0 / match_status | 0.01000000 | 0.30000000 | 0.16800000 | 0.47800000 | 0.50000000 | excluded |
| 1 / amount_variance_ratio | 0.01000000 | 0.10000000 | 0.08980000 | 0.19980000 | 0.50000000 | 0.09990000 |
| 2 / duplicate_score | 0.01000000 | 0.05000000 | 0.00682000 | 0.06682000 | 0.50000000 | 0.03341000 |
| 3 / supplier_exception_history | 0.01000000 | 0.10000000 | 0.07000000 | 0.18000000 | 0.50000000 | 0.09000000 |
| 4 / payment_terms_impact | 0.01000000 | 0.10000000 | 0.00462000 | 0.11462000 | 0.50000000 | 0.05731000 |
| 5 / commodity_index_correlation | 0.01000000 | 0.10000000 | 0.05000000 | 0.16000000 | 0.62000000 | 0.09920000 |
| 6 / tax_regulatory_compliance | 0.01000000 | 0.10000000 | 0.06168000 | 0.17168000 | 0.50000000 | 0.08584000 |
| 7 / environmental_risk | 0.01000000 | 0.00000000 | 0.00000000 | 0.01000000 | 0.50000000 | 0.00500000 |

Evidence payload: {"value": 0.05, "confidence": 0.82, "source": "pricing_benchmark", "benchmark_delta_pct": 18.0, "sample_size": 41, "dimension": 1, "factor_name": "amount_variance_ratio", "invoice_id": "VLD-S2P-2"}.
v_after: [0.93, 0.05, 0.0568, 0.0, 0.6731, 0.0, 0.3416, 0.2494].
Action: **flag_leakage → flag_leakage**; flipped=False; status=acquired.

### Read 2: commodity_index_correlation

v_before: [0.93, 0.05, 0.0568, 0.0, 0.6731, 0.0, 0.3416, 0.2494].
Top actions: flag_leakage, escalate_to_buyer.

| Dim / factor | Precision | Discriminative | Leverage | Base Q | K | Weighted Q |
|---|---:|---:|---:|---:|---:|---:|
| 0 / match_status | 0.01000000 | 0.30000000 | 0.16800000 | 0.47800000 | 0.50000000 | excluded |
| 1 / amount_variance_ratio | 0.01000000 | 0.10000000 | 0.10000000 | 0.21000000 | 0.50000000 | excluded |
| 2 / duplicate_score | 0.01000000 | 0.05000000 | 0.00682000 | 0.06682000 | 0.50000000 | 0.03341000 |
| 3 / supplier_exception_history | 0.01000000 | 0.10000000 | 0.07000000 | 0.18000000 | 0.50000000 | 0.09000000 |
| 4 / payment_terms_impact | 0.01000000 | 0.10000000 | 0.00462000 | 0.11462000 | 0.50000000 | 0.05731000 |
| 5 / commodity_index_correlation | 0.01000000 | 0.10000000 | 0.05000000 | 0.16000000 | 0.62000000 | 0.09920000 |
| 6 / tax_regulatory_compliance | 0.01000000 | 0.10000000 | 0.06168000 | 0.17168000 | 0.50000000 | 0.08584000 |
| 7 / environmental_risk | 0.01000000 | 0.00000000 | 0.00000000 | 0.01000000 | 0.50000000 | 0.00500000 |

Evidence payload: {"value": 0.82, "confidence": 0.78, "source": "demand_forecast", "volume_multiplier": 3.0, "explanation": "Rush order exceeds the 2x bulk-pricing threshold.", "dimension": 5, "factor_name": "commodity_index_correlation", "invoice_id": "VLD-S2P-2"}.
v_after: [0.93, 0.05, 0.0568, 0.0, 0.6731, 0.82, 0.3416, 0.2494].
Action: **flag_leakage → auto_approve**; flipped=True; status=acquired.

## 3. Verification event and actual update

Event ID: SIM-VERIFY-A-42. Source: deterministic simulated invoice reviewer using CTR-MERIDIAN-BULK and its preseed's 3× volume evidence. Verified action=auto_approve; the acquisition's final action matches, so correct=True.

Actual call: KUtilityStore.update_weights(category, acquired_trace, correct=True) (copilot_sdk/scoring/investigation.py:441–477). It credits each acquired dimension +.02, doubled to +.04 when that step flipped the action, capped at 3.0. This differs from GAP-2's flat +.02 informative-read credit.

K before: [0.5, 0.5, 0.5, 0.5, 0.5, 0.62, 0.5, 0.5].
K after: [0.52, 0.52, 0.5, 0.5, 0.5, 0.66, 0.5, 0.5].
ΔK: [0.02, 0.02, 0.0, 0.0, 0.0, 0.04, 0.0, 0.0].
Δμ and Δσ: all zeros. Only the in-memory K table was written.
Stored (dimension, weight, n_updates): [[0, 0.52, 1], [1, 0.52, 1], [5, 0.66, 1]].

## 4. Subsequent similar invoice B with updated K (B=2)

Decision NEXT-INVOICE-B-updated; budget=2; surface=flag_leakage; final=auto_approve; halt=budget_exhausted.

### Read 0: match_status

v_before: [0.9237, 0.101, 0.0568, 0.0, 0.6731, 0.0, 0.3416, 0.2494].
Top actions: flag_leakage, escalate_to_buyer.

| Dim / factor | Precision | Discriminative | Leverage | Base Q | K | Weighted Q |
|---|---:|---:|---:|---:|---:|---:|
| 0 / match_status | 0.01000000 | 0.30000000 | 0.16422000 | 0.47422000 | 0.52000000 | 0.24659440 |
| 1 / amount_variance_ratio | 0.01000000 | 0.10000000 | 0.08980000 | 0.19980000 | 0.52000000 | 0.10389600 |
| 2 / duplicate_score | 0.01000000 | 0.05000000 | 0.00682000 | 0.06682000 | 0.50000000 | 0.03341000 |
| 3 / supplier_exception_history | 0.01000000 | 0.10000000 | 0.07000000 | 0.18000000 | 0.50000000 | 0.09000000 |
| 4 / payment_terms_impact | 0.01000000 | 0.10000000 | 0.00462000 | 0.11462000 | 0.50000000 | 0.05731000 |
| 5 / commodity_index_correlation | 0.01000000 | 0.10000000 | 0.05000000 | 0.16000000 | 0.66000000 | 0.10560000 |
| 6 / tax_regulatory_compliance | 0.01000000 | 0.10000000 | 0.06168000 | 0.17168000 | 0.50000000 | 0.08584000 |
| 7 / environmental_risk | 0.01000000 | 0.00000000 | 0.00000000 | 0.01000000 | 0.50000000 | 0.00500000 |

Evidence payload: {"value": 0.93, "confidence": 0.9, "source": "contract_db", "contract_ref": "CTR-MERIDIAN-BULK", "clause": "Bulk pricing pass-through activates above 2x forecast volume.", "coverage_score": 0.93, "dimension": 0, "factor_name": "match_status", "invoice_id": "VLD-S2P-2"}.
v_after: [0.93, 0.101, 0.0568, 0.0, 0.6731, 0.0, 0.3416, 0.2494].
Action: **flag_leakage → flag_leakage**; flipped=False; status=acquired.

### Read 1: commodity_index_correlation

v_before: [0.93, 0.101, 0.0568, 0.0, 0.6731, 0.0, 0.3416, 0.2494].
Top actions: flag_leakage, escalate_to_buyer.

| Dim / factor | Precision | Discriminative | Leverage | Base Q | K | Weighted Q |
|---|---:|---:|---:|---:|---:|---:|
| 0 / match_status | 0.01000000 | 0.30000000 | 0.16800000 | 0.47800000 | 0.52000000 | excluded |
| 1 / amount_variance_ratio | 0.01000000 | 0.10000000 | 0.08980000 | 0.19980000 | 0.52000000 | 0.10389600 |
| 2 / duplicate_score | 0.01000000 | 0.05000000 | 0.00682000 | 0.06682000 | 0.50000000 | 0.03341000 |
| 3 / supplier_exception_history | 0.01000000 | 0.10000000 | 0.07000000 | 0.18000000 | 0.50000000 | 0.09000000 |
| 4 / payment_terms_impact | 0.01000000 | 0.10000000 | 0.00462000 | 0.11462000 | 0.50000000 | 0.05731000 |
| 5 / commodity_index_correlation | 0.01000000 | 0.10000000 | 0.05000000 | 0.16000000 | 0.66000000 | 0.10560000 |
| 6 / tax_regulatory_compliance | 0.01000000 | 0.10000000 | 0.06168000 | 0.17168000 | 0.50000000 | 0.08584000 |
| 7 / environmental_risk | 0.01000000 | 0.00000000 | 0.00000000 | 0.01000000 | 0.50000000 | 0.00500000 |

Evidence payload: {"value": 0.82, "confidence": 0.78, "source": "demand_forecast", "volume_multiplier": 3.0, "explanation": "Rush order exceeds the 2x bulk-pricing threshold.", "dimension": 5, "factor_name": "commodity_index_correlation", "invoice_id": "VLD-S2P-2"}.
v_after: [0.93, 0.101, 0.0568, 0.0, 0.6731, 0.82, 0.3416, 0.2494].
Action: **flag_leakage → auto_approve**; flipped=True; status=acquired.

## Arithmetic reconciliation and causal comparison

For amount_variance_ratio (dim 1), initial unweighted Q=.1998, rounded to .200. At K1=.5 its weighted score is .1998×.5=.0999, rounded to .100. After the contract read, the top-two actions and dim-1 input are unchanged, so its base Q remains .1998. This is **base versus K-weighted Q**, not a first-read recomputation that halves the score.

Before verification, dim 5 has .16×.62=.0992 < dim 1's .1998×.5=.0999. After verification, dim 5 has .16×.66=.1056 > dim 1's .1998×.52=.103896. The next B=2 episode reads 0→5 and changes the action. The counterfactual and next episode share exactly v0, μ, σ, τ, providers and B=2; only K differs.

No population routing_quality, category_accuracy or action_accuracy is inferred from this single trace.

## Reproduction and source hashes

Run python -B scripts/d1_recursion_trace_v1.py. random_state=42; deterministic trace.
- copilot-sdk/real_centroids_v1.json: 1d782457bfbf8349d7cedfa531a30b3007c1e9e08b378068a9e826d437215863
- copilot-sdk/copilot_sdk/scoring/investigation.py: 3441dcbdb67a93e231ceda9827db36b46413e5d2fd29e750e3310caf1a2df6b4
- s2p-copilot/backend/app/vld_preseed.py: 2a3d69353992ff0e0814e57223638541eeb2fc5cbdeede19d4960ebf2efba0fb
- s2p-copilot/backend/app/evidence_provider.py: 7c3db1d38591bb89ad24bff3d9ee3282eea25bce7df7425aaab1a5ebef547ba9
