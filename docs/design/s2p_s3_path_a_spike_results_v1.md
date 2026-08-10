# S2P S3 — Path A Solution Spike Results v1

**Date:** 2026-08-04  
**Type:** Experimental; scratch factor code and disposable AGE graph only.  
**soc_graph touched:** NO  
**Solution ladder rung:** S3

## Gate result

**S3 PASS — Path A is viable for the factor/data-contract portion of FIX-B.**

The two replacement factors computed continuous values from numeric graph
properties, both hardcoded math tests passed, and both graph-property
perturbations moved only the intended factor (apart from the expected coupled
`amount_variance_ratio` response to the shared PO amount). The scorer’s
decisions were conservative but procurement-defensible across the directional
sample. The existing scorer centroid calibration did not auto-approve the
perfect vector; that is a calibration/decision-policy follow-up, not evidence
that the graph factors are stubs or unfaithful.

The execution plan read for this spike was
`s2p_fix_b_next_experiments_v3.md`, together with the supplied S3 specification.

## Sandbox and safety

| Item | Result |
|---|---|
| Sandbox | `protocol_v2_test_s2p_active_32e4660bb717` |
| AGE backend | `127.0.0.1:5433`, database `soc_copilot` |
| Production `soc_graph` | never targeted |
| Committed source/test files | not modified |
| Scratch factor file | `copilot-sdk/scripts/_s3_spike.py`; deleted after run |
| Sandbox graph | dropped in `finally` |

## Step 0: Factor designs

### Current Stubs (confirmed source)

Exact committed `MatchStatus.compute()` from
`s2p-copilot/backend/app/domains/s2p/factors.py:141-159`:

```python
def compute(
    self,
    invoice: dict[str, Any] | S2PEvent,
    context: dict[str, Any] | list[dict[str, Any]] | None = None,
) -> float:
    invoice = _as_invoice(invoice)
    nodes = [_node(entry) for entry in _neighbors(context)]
    if nodes:
        has_po = any(_has_label_or_key(node, "PurchaseOrder", "po_id") for node in nodes)
        has_gr = any(_has_label_or_key(node, "GoodsReceipt", "gr_id") for node in nodes)
        if has_po and has_gr:
            return 0.1
        if has_po:
            return 0.6
        return 0.9
    if isinstance(invoice.get("approved_categories"), list) and invoice.get("contract_id"):
        return 0.9 if invoice.get("category") in invoice["approved_categories"] else 0.1
    return _fallback(invoice, self.name, 0.5)
```

Exact committed `TaxRegulatoryCompliance.compute()` from `factors.py:289-302`:

```python
def compute(
    self,
    invoice: dict[str, Any] | S2PEvent,
    context: dict[str, Any] | list[dict[str, Any]] | None = None,
) -> float:
    invoice = _as_invoice(invoice)
    nodes = [_node(entry) for entry in _neighbors(context)]
    if nodes:
        has_contract = any(_has_label_or_key(node, "Contract", "contract_id") for node in nodes)
        return 0.15 if has_contract else 0.8
    metadata = invoice.get("metadata")
    if isinstance(metadata, dict) and metadata.get("tax_code") and metadata.get("withholding_tax") is not None:
        return 0.1
    return _fallback(invoice, self.name, 0.9)
```

### Real MatchStatus

The committed stub at
`s2p-copilot/backend/app/domains/s2p/factors.py:141-159` returns fixed
presence buckets (`0.1`, `0.6`, `0.9`) and ignores all properties. The scratch
replacement instead reads:

- `Invoice.amount` versus `PurchaseOrder.amount`;
- `Invoice.quantity` versus `GoodsReceipt.qty_received`;
- `PurchaseOrder.quantity` versus `GoodsReceipt.qty_received` when present.

For each available numeric pair it computes a normalized discrepancy
`abs(left-right) / max(abs(left), 1)`. The result is

```text
match_status = 1 - min(max(discrepancy), 1)
```

with values clamped to `[0,1]`. No match evidence returns `0.5` with
`provenance=no_match_data`; present but incomplete evidence returns `0.5` with
`provenance=partial_data`; complete evidence returns `provenance=computed` and
the maximum discrepancy.

Exact scratch MatchStatus formula:

```python
po = find_neighbor(context, "PurchaseOrder")
gr = find_neighbor(context, "GoodsReceipt")
if po is None and gr is None:
    return 0.5, {"provenance": "no_match_data"}
discrepancies = []
inv_amount = safe_float(invoice.get("amount"))
if po is not None:
    po_amount = safe_float(po.get("amount"))
    if inv_amount is not None and po_amount is not None:
        discrepancies.append(abs(inv_amount - po_amount) / max(abs(inv_amount), 1.0))
if gr is not None:
    gr_qty = safe_float(gr.get("qty_received"))
    inv_qty = safe_float(invoice.get("quantity"))
    if gr_qty is not None and inv_qty is not None:
        discrepancies.append(abs(inv_qty - gr_qty) / max(abs(inv_qty), 1.0))
    po_qty = safe_float(po.get("quantity")) if po is not None else None
    if po_qty is not None and gr_qty is not None:
        discrepancies.append(abs(po_qty - gr_qty) / max(abs(po_qty), 1.0))
if not discrepancies:
    return 0.5, {"provenance": "partial_data"}
score = 1.0 - min(max(discrepancies), 1.0)
return score, {"provenance": "computed", "max_discrepancy": max(discrepancies)}
```

### Real TaxRegulatoryCompliance

The committed stub at
`s2p-copilot/backend/app/domains/s2p/factors.py:289-302` returns `0.15` or
`0.8` based only on Contract presence. The scratch replacement reads:

- `Invoice.amount <= Contract.max_amount`;
- `Contract.tax_compliant` as a boolean/boolean-like value;
- `Contract.regulatory_status` in `approved`, `active`, or `compliant`.

It returns `checks_passed / checks_total` in `[0,1]`. Missing Contract returns
`0.3` with `provenance=no_contract`; a Contract with no compliance fields
returns `0.5` with `provenance=no_compliance_fields`; otherwise the result is
`provenance=computed` with check counts.

Exact scratch TaxRegulatoryCompliance formula:

```python
contract = find_neighbor(context, "Contract")
if contract is None:
    return 0.3, {"provenance": "no_contract"}
passed = total = 0
max_amount = safe_float(contract.get("max_amount"))
invoice_amount = safe_float(invoice.get("amount"))
if max_amount is not None and invoice_amount is not None:
    total += 1
    passed += int(invoice_amount <= max_amount)
compliant = contract.get("tax_compliant")
if compliant is not None:
    total += 1
    passed += int(compliant is True or str(compliant).lower() in {"true", "1", "yes"})
status = contract.get("regulatory_status")
if status is not None:
    total += 1
    passed += int(str(status).lower() in {"approved", "active", "compliant"})
if total == 0:
    return 0.5, {"provenance": "no_compliance_fields"}
return passed / total, {"provenance": "computed", "checks_passed": passed, "checks_total": total}
```

### Numeric contract

The coercion helper follows DataOps’s `_safe_get_float` pattern at
`apps/dataops/backend/app/graph_queries.py:93-97`: attempt `float(value)`, catch
`TypeError`/`ValueError`, and make the fallback visible through provenance.
Unlike SOC’s numeric `0.8` versus categorical-string enum mismatch, every
numeric S3 property was stored numerically and consumed numerically.

Exact template:

```python
def _safe_get_float(payload: dict[str, Any], key: str, default: float = 0.0) -> float:
    try:
        return float(payload.get(key, default))
    except (TypeError, ValueError):
        return default
```

## Step 1: Disposable graph property completeness

The current committed seed shape in
`s2p-copilot/scripts/seed_s2p_graph.py:165-218` omits the properties required by
the new formulas and by faithful existing readers. The scratch sandbox added:

### Seed gaps identified

Properties that MUST be added to the permanent Track-1 migration:
`PurchaseOrder.amount`, `GoodsReceipt.qty_received`, `Commodity.volatility`,
`Invoice.payment_days`, `Contract.max_amount`, `Contract.tax_compliant`, and
`Contract.regulatory_status`.

| Entity | Required property | Stored value/type in well-matched target |
|---|---|---|
| Invoice | `amount` | `3781.7`, numeric |
| Invoice | `quantity` | `100`, numeric |
| Invoice | `payment_days` | `30`, numeric |
| PurchaseOrder | `amount` | `3781.7`, numeric |
| PurchaseOrder | `quantity` | `100`, numeric |
| GoodsReceipt | `qty_received` | `100`, numeric |
| GoodsReceipt | `amount` | `3781.7`, numeric |
| Supplier | `exception_rate` | `0.033`, numeric |
| Supplier | `payment_terms` | `"Net 30"`, string parsed to 30 days |
| Commodity | `volatility` | `0.35`, numeric |
| Contract | `max_amount` | `5000`, numeric |
| Contract | `tax_compliant` | `true`, boolean |
| Contract | `regulatory_status` | `"approved"`, enum string |

**Well-matched invoice (`S2P-INV-0003`):** Invoice amount `3781.7`, quantity
`100`, payment days `30`; PO amount `3781.7`, quantity `100`; GR received
quantity `100`; compliant Contract max amount `5000`, tax `true`, status
`approved`.

**Mismatched invoice (`S2P-INV-MISMATCH`):** represented by the run profile
`S2P-INV-BOTH-BAD`: Invoice amount `5000`, quantity `100`; PO amount `3000`,
quantity `100`; GR received quantity `80`; non-compliant Contract max amount
`4000`, tax `false`, status `suspended`.

All nodes carried `domain='s2p'` and `entity_id`. Each Invoice had five
outgoing edges: `MATCHED_TO`, `RECEIVED_AS`, `SUPPLIED_BY`,
`HAS_COMMODITY_INDEX`, and `GOVERNED_BY`.

The current committed seed creates only Contract identity/linkage fields
(`contract_id`, supplier linkage, and commodity linkage); S3 therefore adds
`max_amount`, `tax_compliant`, and `regulatory_status` to the Track-1 contract.

## Step 2: Scratch implementation and math checks

The scratch file contained `safe_float`, `find_neighbor`,
`RealMatchStatus`, `RealTaxRegulatoryCompliance`, the directed-query harness,
and a read-only scorer call. It imported the five existing factor readers from
committed source; only the two stub replacements were scratch implementations.

| Hardcoded case | Result | Provenance |
|---|---:|---|
| Perfect MatchStatus | `1.0000` | computed; max discrepancy `0.0` |
| Big MatchStatus mismatch | `0.2000` | computed; max discrepancy `0.8` |
| MatchStatus no data | `0.5000` | `no_match_data` |
| Perfect TaxRegulatoryCompliance | `1.0000` | computed; `3/3` checks |

## Step 3: Graph-backed factor computation

The Track-2 query was the proven directed shape from Phase B:

```cypher
MATCH (e:Invoice {invoice_id: '<id>'})-[]->(n)
WHERE n.domain = 's2p'
RETURN n
LIMIT 100
```

AGE vertex values were normalized to flat property dictionaries for the
factor context. Each target returned five neighbors. `CompoundingScorer` was
called with `score_read_only` using its test-profile in-memory store, so no
Decision was persisted.

| Invoice | RealMatch | RealTax | Amount variance | Duplicate | Supplier exception | Payment terms | Commodity | Environmental | Scorer action |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| S2P-INV-0003 (perfect) | 1.000 | 1.000 | 0.000 | 0.000 | 0.033 | 0.000 | 0.350 | 0.500 | hold_for_review |
| S2P-INV-PRICE-OFF | 0.793 | 1.000 | 0.261 | 0.000 | 0.033 | 0.000 | 0.350 | 0.500 | hold_for_review |
| S2P-INV-QTY-OFF | 0.700 | 1.000 | 0.000 | 0.000 | 0.033 | 0.000 | 0.350 | 0.500 | hold_for_review |
| S2P-INV-NON-COMPL | 1.000 | 0.000 | 0.000 | 0.000 | 0.033 | 0.000 | 0.350 | 0.500 | hold_for_review |
| S2P-INV-BOTH-BAD | 0.600 | 0.000 | 0.667 | 0.000 | 0.033 | 0.000 | 0.350 | 0.500 | refer_to_specialist |

The scorer confidences were `0.5839`, `0.9246`, `0.8585`, `0.7482`, and
`0.7828`, respectively. These are live scorer projections from graph-derived
factor vectors, not fixture-vector replay.

## Step 4: Perturbation

### A — MatchStatus input

Disposable `PurchaseOrder.amount` changed from `3781.7` to `2000.0`.

| Factor | Original | After A | Result |
|---|---:|---:|---|
| RealMatchStatus | 1.0000 | 0.5289 | **moved** |
| AmountVarianceRatio | 0.0000 | 0.89085 | moved as the expected direct consumer of the same PO amount |
| RealTaxRegulatoryCompliance | 1.0000 | 1.0000 | stable |
| SupplierExceptionHistory | 0.0330 | 0.0330 | stable |
| PaymentTermsImpact | 0.0000 | 0.0000 | stable |
| CommodityIndexCorrelation | 0.3500 | 0.3500 | stable |
| EnvironmentalRisk | 0.5000 | 0.5000 | stable |

RealMatchStatus moved continuously and all unrelated factors stayed stable.
The coupled AmountVarianceRatio movement is expected, not contamination.

### B — TaxRegulatoryCompliance input

Disposable `Contract.tax_compliant` changed from `true` to `false`.

| Factor | Original | After B | Result |
|---|---:|---:|---|
| RealTaxRegulatoryCompliance | 1.0000 | 0.6667 | **moved** |
| RealMatchStatus | 1.0000 | 1.0000 | stable |
| AmountVarianceRatio | 0.0000 | 0.0000 | stable |
| DuplicateScore | 0.0000 | 0.0000 | stable |
| SupplierExceptionHistory | 0.0330 | 0.0330 | stable |
| PaymentTermsImpact | 0.0000 | 0.0000 | stable |
| CommodityIndexCorrelation | 0.3500 | 0.3500 | stable |
| EnvironmentalRisk | 0.5000 | 0.5000 | stable |

Both properties were restored before graph teardown.

## Step 5: Soft sanity

Fixtures were used only to construct varied disposable inputs; their stored
`ground_truth_action` values were treated as directional guidance, not an
oracle.

| Invoice | Domain condition | Scorer action | Defensible? |
|---|---|---|---|
| S2P-INV-0003 | exact amount/quantity match; all compliance checks pass | hold_for_review | YES; conservative approval gate |
| S2P-INV-PRICE-OFF | 20.7% price discrepancy; compliant contract | hold_for_review | YES; escalates rather than approving |
| S2P-INV-QTY-OFF | 30% receipt shortfall; compliant contract | hold_for_review | YES; escalates quantity mismatch |
| S2P-INV-NON-COMPL | exact match; over-limit, false tax, suspended status | hold_for_review | YES; blocks auto-approval and requires review |
| S2P-INV-BOTH-BAD | price/quantity mismatch; all compliance checks fail | refer_to_specialist | YES; escalation is appropriate |

The existing preset did not select `auto_approve` for the perfect vector. That
is conservative and defensible, but Path A implementation should separately
recalibrate the S2P action centroids/auto-approve gate against the new factor
semantics. This spike does not treat the old fixture vector as a target for
that calibration.

## S3 VERDICT

**Faithful graph-native S2P factors achievable: YES.**  
**Path A viable: YES.**

The graph contains the required numeric properties, the directed query reaches
all factor entities, both replacement factors use concrete values rather than
presence buckets, and isolated perturbations prove that graph inputs drive
continuous factor changes. The sample scorer behavior is directionally
defensible and never auto-approves a mismatched or non-compliant invoice.

Proceed to the permanent two-track FIX-B work: Track 2’s proven directed read
and normalization, Track 1’s property-completeness migration contract, and
the two real factors with explicit provenance. Then run the planned F/B2/C/D
validation phases. Do not treat the old fixture vector as an oracle.

### Canonical factor formulas for implementation

The production implementations should use the exact formulas shown in Step 0:
numeric pairwise discrepancy for `RealMatchStatus`, and passed compliance
checks divided by available checks for `RealTaxRegulatoryCompliance`.

### Property-shape contract for Track 1 migration

| Label | Property | Type | Required by |
|---|---|---|---|
| Invoice | `amount` | numeric | MatchStatus, AmountVarianceRatio |
| Invoice | `quantity` | numeric | MatchStatus |
| Invoice | `payment_days` | numeric | PaymentTermsImpact |
| PurchaseOrder | `amount` | numeric | MatchStatus, AmountVarianceRatio |
| PurchaseOrder | `quantity` | numeric | MatchStatus |
| GoodsReceipt | `qty_received` | numeric | MatchStatus |
| GoodsReceipt | `amount` | numeric | MatchStatus data completeness |
| Supplier | `exception_rate` | numeric `[0,1]` | SupplierExceptionHistory |
| Supplier | `payment_terms` | parseable string | PaymentTermsImpact |
| Commodity | `volatility` | numeric `[0,1]` | CommodityIndexCorrelation |
| Contract | `max_amount` | numeric | TaxRegulatoryCompliance |
| Contract | `tax_compliant` | boolean/boolean-like | TaxRegulatoryCompliance |
| Contract | `regulatory_status` | enum string | TaxRegulatoryCompliance |

### Provenance contract

Every fallback returns `provenance != 'computed'`: `no_match_data`,
`partial_data`, `no_contract`, and `no_compliance_fields` are explicit. The
perturbation proof is continuous and isolated, with the documented shared-input
coupling between MatchStatus and AmountVarianceRatio.

## What Surprised Us

1. The first disposable harness attempt returned zero neighbors because AGE
   vertex wrappers were not normalized; after switching the shaping read to
   `properties(n)`, the required directed query returned all five neighbors.
2. `amount_variance_ratio` necessarily moves with a PO amount perturbation;
   isolation must exclude factors that intentionally consume the same input.
3. The old scorer centroids conservatively hold a perfect graph-derived vector
   instead of auto-approving it. This is calibration work, not a graph-factor
   failure, and the old fixture vector is not an oracle.

## READY FOR IMPLEMENTATION (Track 2 + Track 1 + real factors): YES

## Cleanup

| Item | Result |
|---|---|
| Scratch factor code deleted | YES |
| Scratch output deleted | YES |
| All perturbations reverted | YES |
| Disposable AGE graph dropped | YES |
| `soc_graph` written | NO |
| Production/test source modified | NO |
