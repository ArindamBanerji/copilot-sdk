# Generate 50 S2P Multi-Hop Investigation Scenarios

## What you're building

You are generating synthetic test data for an AI copilot that helps accounts payable analysts triage invoice exceptions. Each scenario is a multi-step investigation where the correct action can ONLY be determined by following graph-based evidence — surface-level features alone point to the WRONG action.

## Output

One JSON file with this structure:

```json
{
  "_header": "PLANTED SYNTHETIC — POSITIVE CONTROL — NOT A MEASUREMENT OF VLD VALUE ON REAL DECISIONS.",
  "_spec": "multihop_scenario_spec_v2.md",
  "_stage": "Stage 1: 50 S2P instances (30 strong + 10 moderate + 10 controls)",
  "provenance": "sample",
  "scenarios": [ <50 scenario objects> ]
}
```

## The S2P Domain

**What the copilot does:** An accounts payable analyst receives invoice exceptions flagged by the system (price mismatches, missing receipts, duplicate risks, policy violations). The copilot scores each exception and recommends an action. Some exceptions LOOK like simple approvals but are actually disputes — the investigation checks contract amendments, goods receipt history, and supplier patterns.

**Categories (5):** price_mismatch, receipt_missing, duplicate_suspect, policy_violation, contract_deviation

**Actions (5):** approve, partial_approve, hold_for_review, dispute, escalate_to_procurement

**Factors (7 numeric values, each 0.0 to 1.0):**
- receipt_match — does the invoice match goods receipt? (1.0 = perfect match)
- price_conformance — does the price match the contract/PO? (1.0 = exact match)
- supplier_trust — historical supplier reliability score (1.0 = very trusted)
- duplicate_risk — probability this is a duplicate invoice (1.0 = very likely duplicate)
- policy_conformance — does this follow procurement policy? (1.0 = fully compliant)
- amount_materiality — how large is the amount relative to thresholds? (1.0 = very material)
- contract_coverage — is there a valid contract covering this? (1.0 = fully covered)

## Scenario JSON Schema

Each scenario MUST have ALL of these fields:

```json
{
  "scenario_id": "S2P-001-v1",
  "scenario_type": "hidden_amendment",
  "copilot": "s2p",
  "branching_kind": "score_keyed",
  "rho_planted": 0.90,
  "description": "Invoice price mismatch looks like a dispute but contract was amended last week",

  "alert": {
    "alert_id": "ALERT-S2P-001",
    "category": "price_mismatch",
    "surface_factors": {
      "receipt_match": 0.90,
      "price_conformance": 0.25,
      "supplier_trust": 0.80,
      "duplicate_risk": 0.10,
      "policy_conformance": 0.85,
      "amount_materiality": 0.60,
      "contract_coverage": 0.70
    }
  },

  "available_branches": [
    {
      "branch_id": "check_contract_amendments",
      "evidence_source": "contract_management_system",
      "read_cost": 1,
      "factor_enriched": "price_conformance",
      "factor_new_value": 0.90,
      "evidence_found": "Contract amendment dated last week increased unit price by 12%",
      "narration": "The price mismatch disappears once the amendment is applied"
    },
    {
      "branch_id": "check_gr_history",
      "evidence_source": "goods_receipt_log",
      "read_cost": 1,
      "factor_enriched": "receipt_match",
      "factor_new_value": 0.95,
      "evidence_found": "Goods receipt confirmed for full quantity",
      "narration": "Receipt matches — this is not a short shipment"
    },
    {
      "branch_id": "check_duplicate_invoices",
      "evidence_source": "invoice_registry",
      "read_cost": 1,
      "factor_enriched": "duplicate_risk",
      "factor_new_value": 0.05,
      "evidence_found": "No matching invoice numbers in past 90 days",
      "narration": "Not a duplicate — unique invoice"
    }
  ],

  "correct_branches": ["check_contract_amendments"],
  "misleading_branches": ["check_duplicate_invoices"],
  "read_costs": {"check_contract_amendments": 1, "check_gr_history": 1, "check_duplicate_invoices": 1},
  "budget": 2,
  "surface_only_resolvable": false,

  "decision_tree": {
    "ground_truth_action": "approve",
    "reasoning": "Surface shows low price_conformance (0.25) suggesting dispute. But the contract amendment raised the price — after amendment, price_conformance jumps to 0.90. This invoice should be approved.",
    "hops": [
      {
        "step": 1,
        "branch_id": "check_contract_amendments",
        "evidence_source": "contract_management_system",
        "evidence_found": "Contract amendment dated last week increased unit price by 12%",
        "factor_enriched": "price_conformance",
        "factor_new_value": 0.90,
        "narration": "The price mismatch disappears once the amendment is applied"
      }
    ]
  },

  "alternative_branches": [],
  "graph_nodes": [
    {"id": "invoice_001", "type": "Invoice", "label": "INV-2024-0847"},
    {"id": "contract_amend", "type": "ContractAmendment", "label": "Amendment #3 — price increase"},
    {"id": "po_4521", "type": "PurchaseOrder", "label": "PO-4521"}
  ],
  "graph_edges": [
    {"source": "invoice_001", "target": "po_4521", "type": "REFERENCES_PO"},
    {"source": "po_4521", "target": "contract_amend", "type": "AMENDED_BY"}
  ]
}
```

## THE CRITICAL DESIGN RULE: Boundary Crossing

1. Set surface factors so they are closest to the WRONG action's centroid.
2. Set hop evidence so that at least 2 factors shift by >= 0.30 each.
3. Each hop MUST enrich a DIFFERENT factor.
4. ground_truth_action must be DIFFERENT from what surface factors suggest.

## Action Profiles

| Action | receipt | price | supplier | duplicate | policy | amount | contract |
|---|---|---|---|---|---|---|---|
| approve | 0.8-1.0 | 0.8-1.0 | 0.7-1.0 | 0.0-0.2 | 0.8-1.0 | 0.0-0.4 | 0.8-1.0 |
| partial_approve | 0.5-0.7 | 0.5-0.7 | 0.6-0.8 | 0.0-0.2 | 0.6-0.8 | 0.3-0.6 | 0.5-0.8 |
| hold_for_review | 0.4-0.6 | 0.4-0.6 | 0.4-0.6 | 0.2-0.5 | 0.4-0.6 | 0.4-0.7 | 0.4-0.6 |
| dispute | 0.1-0.4 | 0.1-0.3 | 0.2-0.5 | 0.3-0.7 | 0.2-0.4 | 0.5-0.9 | 0.1-0.4 |
| escalate_to_procurement | 0.2-0.5 | 0.1-0.4 | 0.1-0.3 | 0.4-0.8 | 0.1-0.3 | 0.6-1.0 | 0.0-0.3 |

## Instance Distribution (50 total)

### Block A: 30 Strong-Conditional (rho >= 0.70)

6 templates x 5 variations. Every hop shifts >= 0.30.

rho: 0.70=10, 0.90=12, 1.00=8

**Template 1: Hidden amendment** (S2P-001 to S2P-005)
Surface: dispute (low price_conformance). Evidence: contract amended. GT: approve.
Shifts: price_conformance LOW->HIGH (>=0.50).

**Template 2: Partial delivery looks like short** (S2P-006 to S2P-010)
Surface: dispute (low receipt_match). Evidence: planned partial delivery per PO terms. GT: partial_approve.
Shifts: receipt_match LOW->HIGH (>=0.40).

**Template 3: Trusted supplier, bad batch** (S2P-011 to S2P-015)
Surface: approve (high supplier_trust). Evidence: quality hold on recent batch. GT: hold_for_review.
Shifts: supplier_trust HIGH->LOW (>=0.40), policy_conformance HIGH->LOW (>=0.30).

**Template 4: Small amount, no contract** (S2P-016 to S2P-020)
Surface: approve (low amount_materiality). Evidence: no contract coverage, policy requires one above threshold. GT: escalate_to_procurement.
Shifts: contract_coverage HIGH->LOW (>=0.50), policy_conformance HIGH->LOW (>=0.40).

**Template 5: Duplicate looks unique** (S2P-021 to S2P-025)
Surface: approve (low duplicate_risk). Evidence: same supplier, same amount, 3 days apart. GT: dispute or hold_for_review.
Shifts: duplicate_risk LOW->HIGH (>=0.50).

**Template 6: Policy compliant but strategically wrong** (S2P-026 to S2P-030)
Surface: approve (high policy_conformance). Evidence: spend exceeds category budget, needs procurement review. GT: escalate_to_procurement.
Shifts: amount_materiality LOW->HIGH (>=0.40), contract_coverage HIGH->LOW (>=0.30).

### Block B: 10 Moderate (rho = 0.30 and 0.50)

2 templates x 5 variations. Shifts >= 0.15.

**Template 7: Ambiguous price variance** (S2P-031 to S2P-035)
Could be approve or partial_approve. Evidence is mixed.

**Template 8: Borderline materiality** (S2P-036 to S2P-040)
Amount near threshold. Could go either way.

### Block C: 5 Flat Controls (S2P-FLAT-001 to S2P-FLAT-005)

surface_only_resolvable=true, hops=[], budget=0, rho=1.00.

### Block D: 5 rho=0.50 Checks (S2P-RHO50-001 to S2P-RHO50-005)

rho=0.50, has hops. VLD should equal chance (1/5=0.200).

## Graph Entities

**Node types:** Invoice, PurchaseOrder, ContractAmendment, GoodsReceipt, Supplier, QualityHold, DeliverySchedule, SpendCategory, PolicyRule, DuplicateCandidate

**Edge types:** REFERENCES_PO, AMENDED_BY, RECEIVED_AS, SUPPLIED_BY, QUALITY_HOLD_ON, DELIVERED_PER, IN_CATEGORY, GOVERNED_BY, DUPLICATE_OF

## Checklist

- [ ] scenario_id starts with "S2P-"
- [ ] copilot = "s2p"
- [ ] branching_kind = "score_keyed"
- [ ] surface_factors has 7 keys: receipt_match, price_conformance, supplier_trust, duplicate_risk, policy_conformance, amount_materiality, contract_coverage
- [ ] All factor values 0.0-1.0
- [ ] ground_truth_action: approve, partial_approve, hold_for_review, dispute, escalate_to_procurement
- [ ] Block A: GT differs from surface, each hop shifts >= 0.30
- [ ] Each hop enriches a DIFFERENT factor
- [ ] Block C: surface_only_resolvable=true, hops=[]
- [ ] Block D: rho=0.50, has hops
- [ ] provenance = "sample"
- [ ] No duplicate IDs
- [ ] All 5 actions appear at least 3 times
