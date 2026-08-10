# S2P FIX-B What-If — Phase E Results v1
**Date:** 2026-08-04  
**soc_graph touched:** NO

Phase E used disposable AGE graphs only. The requested
`s2p_fix_b_two_track_implementation_v2.md` was not present at the requested
path, nor under another workspace path; this is recorded as a documentation
gap. The experiment proceeded from v5, A′, B, the live factor source, and the
locked-in query shape.

## E1: Per-Factor Divergence Diagnosis

### Factor Property Map

Common helpers in `s2p-copilot/backend/app/domains/s2p/factors.py`:

- `_neighbors` (`:83-92`) reads either a list or `context["neighbors"]`.
- `_node` (`:95-99`) unwraps `entry["node"]`.
- `_has_label_or_key` (`:112-114`) treats either a label or the factor’s key
  as evidence that a node has the expected type.
- `_fallback` (`:74-80`) prefers an invoice field, then
  `invoice["factors"]`, then the factor default.

| Factor | Neighbor | Properties read | Fallback | Formula summary |
|---|---|---|---:|---|
| `match_status` | PurchaseOrder, GoodsReceipt | `po_id`, `gr_id` | 0.5 | With graph nodes: PO+GR → 0.1; PO only → 0.6; otherwise → 0.9 |
| `amount_variance_ratio` | PurchaseOrder | `po_id`, `amount`/`total_amount`/`po_amount`/`net_amount`; invoice `amount` | 0.3 | `abs(invoice_amount - po_amount) / max(abs(po_amount), 1)` |
| `duplicate_score` | sibling Invoice | `invoice_id`, `amount` | 0.05 | Highest `1 - abs(current - sibling)/max(current,sibling,1)` |
| `supplier_exception_history` | Supplier | `supplier_id`, `exception_rate` | 0.5 | Returns Supplier `exception_rate` if present |
| `payment_terms_impact` | Supplier | `supplier_id`, `payment_terms`; invoice `payment_days` or metadata `payment_days` | 0.5 | `abs(actual_days - standard_days)/max(standard_days,1)` |
| `commodity_index_correlation` | Commodity | `commodity_id`, `volatility` | 0.5 | Returns Commodity `volatility` |
| `tax_regulatory_compliance` | Contract, Supplier | `contract_id` | 0.9 | Any graph context with Contract → 0.15; graph context without Contract → 0.8 |

The decisive exact branches are:

```python
# MatchStatus.compute(), factors.py:144-160
nodes = [_node(entry) for entry in _neighbors(context)]
if nodes:
    has_po = any(_has_label_or_key(node, "PurchaseOrder", "po_id") for node in nodes)
    has_gr = any(_has_label_or_key(node, "GoodsReceipt", "gr_id") for node in nodes)
    if has_po and has_gr:
        return 0.1
    if has_po:
        return 0.6
    return 0.9
```

```python
# AmountVarianceRatio.compute(), factors.py:168-190
inv_amount = _amount(invoice.get("amount"))
for entry in _neighbors(context):
    node = _node(entry)
    if not _has_label_or_key(node, "PurchaseOrder", "po_id"):
        continue
    po_amount = _amount(
        node.get("amount")
        or node.get("total_amount")
        or node.get("po_amount")
        or node.get("net_amount")
    )
    if inv_amount is not None and po_amount is not None:
        return _clamp(abs(inv_amount - po_amount) / max(abs(po_amount), 1.0))
```

```python
# DuplicateScore.compute(), factors.py:199-224
if _graph_has_context(context):
    current_id = invoice.get("invoice_id") or invoice.get("event_id")
    current_amount = _amount(invoice.get("amount"))
    best = 0.0
    for entry in _neighbors(context):
        node = _node(entry)
        if not _has_label_or_key(node, "Invoice", "invoice_id"):
            continue
        if node.get("invoice_id") == current_id:
            continue
        other_amount = _amount(node.get("amount"))
        if current_amount is None or other_amount is None:
            continue
        denominator = max(abs(current_amount), abs(other_amount), 1.0)
        best = max(best, 1.0 - abs(current_amount - other_amount) / denominator)
    return _clamp(best, 0.0)
```

```python
# SupplierExceptionHistory.compute(), factors.py:227-242
for entry in _neighbors(context):
    node = _node(entry)
    if _has_label_or_key(node, "Supplier", "supplier_id") and node.get("exception_rate") is not None:
        return _clamp(node.get("exception_rate"))
```

```python
# PaymentTermsImpact.compute(), factors.py:247-267
actual_days = _payment_days(invoice.get("payment_days"))
if actual_days is None:
    metadata = invoice.get("metadata")
    if isinstance(metadata, dict):
        actual_days = _payment_days(metadata.get("payment_days"))
if actual_days is None:
    return _fallback(invoice, self.name, 0.5)
for entry in _neighbors(context):
    node = _node(entry)
    if not _has_label_or_key(node, "Supplier", "supplier_id"):
        continue
    standard_days = _payment_days(node.get("payment_terms")) or 30
    return _clamp(abs(actual_days - standard_days) / max(standard_days, 1))
```

```python
# CommodityIndexCorrelation.compute(), factors.py:273-283
for entry in _neighbors(context):
    node = _node(entry)
    if _has_label_or_key(node, "Commodity", "commodity_id") and node.get("volatility") is not None:
        return _clamp(node.get("volatility"))
```

```python
# TaxRegulatoryCompliance.compute(), factors.py:289-302
nodes = [_node(entry) for entry in _neighbors(context)]
if nodes:
    has_contract = any(_has_label_or_key(node, "Contract", "contract_id") for node in nodes)
    return 0.15 if has_contract else 0.8
metadata = invoice.get("metadata")
if isinstance(metadata, dict) and metadata.get("tax_code") and metadata.get("withholding_tax") is not None:
    return 0.1
return _fallback(invoice, self.name, 0.9)
```

### Seeded Property Table

Sandbox: `protocol_v2_test_s2p_active_c3c4ce854256`. This was the target slice
of the A′ wrapper, with the locked-in `domain='s2p'`, `provenance='seed'`, and
`entity_id` additions.

| Neighbor label | entity_id | Properties present and values |
|---|---|---|
| Supplier | `SUP-003` | `supplier_id=SUP-003`, `name=Northstar Packaging`, `category=packaging`, `exception_rate=0.04`, `payment_terms=Net 30`, `otif_score=0.96`, `domain=s2p`, `provenance=seed` |
| PurchaseOrder | `PO-20260003` | `po_id=PO-20260003`, `po_number=PO-20260003`, `supplier_id=SUP-003`, `currency=USD`, `amount=3781.7`, `domain=s2p`, `provenance=seed` |
| GoodsReceipt | `GR-PO-20260003` | `gr_id=GR-PO-20260003`, `qty_received=0`, `date=fixture`, `domain=s2p`, `provenance=seed` |
| Commodity | `resin` | `commodity_id=resin`, `volatility=0.822`, `domain=s2p`, `provenance=seed` |
| Contract | `CTR-003-PRI` | `contract_id=CTR-003-PRI`, `domain=s2p`, `provenance=seed` |

The AGE `RETURN n` query returned exactly these five directed outgoing
neighbors. All expected factor-readable keys were present for the factors that
look for them. No sibling Invoice was included in this one-hop direct result.

### SQLite Source Values

The fixture entry `data/synthetic_invoices.json` contains:

```json
{
  "invoice_id": "S2P-INV-0003",
  "supplier_id": "SUP-003",
  "po_number": "PO-20260003",
  "amount": 3781.7,
  "category": "price_variance",
  "ground_truth_action": "auto_approve",
  "factors": {
    "match_status": 0.953,
    "amount_variance_ratio": 0.04,
    "duplicate_score": 0.007,
    "supplier_exception_history": 0.033,
    "payment_terms_impact": 0.515,
    "commodity_index_correlation": 0.822,
    "tax_regulatory_compliance": 0.938
  }
}
```

The SQLite `decisions` row stores the same seven values in `factors_json` and
`factor_vector_json`; it is not recomputing them from entity vertices. Its
`decision_entity_edges` row for a representative decision contains only:
`DECIDED_ON → S2P-INV-0003`. The SQLite schema has no entity-vertex property
table corresponding to the AGE Supplier/PO/GR/Commodity/Contract nodes.

Therefore the claimed SQLite baseline is a stored fixture-derived decision
vector, not an independently computed graph-entity ground truth. Direct
`compute_all_factors(fixture_invoice, context=None)` reproduces the stored
fixture vector because `_fallback` reads `invoice["factors"]`.

### Divergence Cause Table

| Factor | Graph | SQLite target | Cause | Fix implication |
|---|---:|---:|---|---|
| `match_status` | 0.100 | 0.953 | FORMULA: PO and GR presence takes a hard-coded graph branch of 0.1; properties are not consulted | Change the factor semantics or introduce a graph-native match-status property/derived metric; data-only seeding cannot fix it |
| `amount_variance_ratio` | 0.000 | 0.040 | WRONG VALUE / FIXTURE COINCIDENCE: wrapper PO amount equals invoice amount, while SQLite stores fixture factor 0.04 | Seed the authoritative PO amount if a real amount variance exists, or preserve explicit source factor; current JSON PO amount is insufficient |
| `duplicate_score` | 0.000 | 0.007 | MISSING NEIGHBOR / FIXTURE COINCIDENCE: direct context has no sibling Invoice; SQLite stores fixture value | Add bounded sibling entities and their amounts, or establish a graph-independent source for this factor |
| `supplier_exception_history` | 0.040 | 0.033 | WRONG VALUE: seeded Supplier `exception_rate=0.04`; stored fixture target is 0.033; s2p.db has no Supplier property source | Resolve source-of-truth conflict; JSON supplier data and invoice factor disagree |
| `payment_terms_impact` | 0.515 | 0.515 | FIXTURE COINCIDENCE in the standalone E1 input; Supplier has `Net 30`, but the factor needs invoice `payment_days` to enter the graph branch | Seed/request `payment_days` explicitly if this is to be graph-derived |
| `commodity_index_correlation` | 0.822 | 0.822 | REAL graph match: Commodity `volatility=0.822` is read directly | No correction required for this factor |
| `tax_regulatory_compliance` | 0.150 | 0.938 | FORMULA: any non-empty graph context containing Contract takes hard-coded 0.15; Contract properties are ignored | Change formula/contract semantics; adding `tax_regulatory_compliance=0.938` does not help |

### Authoritative Source Decision

JSON fixtures are sufficient to reproduce the current SQLite target vector, but
they are not sufficient as a faithful entity source: the fixture’s invoice
factors disagree with its Supplier and PO source values. `s2p.db` is not a
solution for entity properties; it stores the already-materialized factor
vector and only a Decision→Invoice edge for the representative row.

**VERDICT: HYBRID is required for a faithful design**, but no source choice can
solve the two formula blockers without changing factor semantics. The current
SQLite baseline is a fixture-derived target, not a graph-computed oracle.

## E2: Iterate to Faithful (S2P-INV-0003)

### Corrections Applied

| Label | Property added/changed | Value | Source |
|---|---|---:|---|
| PurchaseOrder | `match_status`, `amount_variance_ratio` | 0.953, 0.04 | Target-vector diagnostic only |
| GoodsReceipt | `match_status`, `received` | 0.953, `true` | Target-vector diagnostic only |
| Contract | `tax_regulatory_compliance`, `compliant` | 0.938, `true` | Target-vector diagnostic only |

These properties were added only in the disposable sandbox. No production or
test source was edited.

### Iteration Log

| Attempt | Context/data | Action/confidence | Divergent factors |
|---|---|---|---|
| 1 | A′ properties: PO + GR + Supplier + Commodity + Contract | Factor vector `[0.1, 0.0, 0.0, 0.04, 0.515, 0.822, 0.15, 0.5]`; endpoint-equivalent action `refer_to_specialist` | Match, amount, duplicate, supplier, tax |
| 2 | Added target-valued match/tax properties to PO, GR, Contract | Exactly unchanged: `[0.1, 0.0, 0.0, 0.04, 0.515, 0.822, 0.15, 0.5]` | Same five |
| Diagnostic | Removed GR | `match_status=0.6` | Still cannot reach 0.953 |
| Diagnostic | Removed Contract | `tax_regulatory_compliance=0.8` | Still cannot reach 0.938 |
| Diagnostic | Removed PO | `match_status=0.9`, amount falls back to 0.04 | Still cannot reach 0.953 and loses graph PO amount computation |

The possible graph-context `match_status` outputs are discrete `{0.1, 0.6,
0.9}`. The possible non-empty-context tax outputs are `{0.15, 0.8}`. Neither
target (`0.953` or `0.938`) is reachable by adding or changing node properties.

### Final Property Set

No property set can achieve all seven targets under the current formulas. The
minimum set that produces the observed graph-derived values is:

| Label | Property | Value source | Required by factor |
|---|---|---|---|
| PurchaseOrder | `po_id`, `amount` | wrapper/authoritative PO source | AmountVarianceRatio |
| GoodsReceipt | `gr_id` | wrapper/authoritative GR source | MatchStatus branch |
| Supplier | `supplier_id`, `exception_rate`, `payment_terms` | supplier source | SupplierExceptionHistory, PaymentTermsImpact |
| Commodity | `commodity_id`, `volatility` | authoritative commodity source | CommodityIndexCorrelation |
| Contract | `contract_id` | contract source | TaxRegulatoryCompliance branch |
| Invoice siblings | `invoice_id`, `amount` | authoritative invoice source | DuplicateScore |

### Final Factor Vector

| Factor | Target | E2 attempt 2 | Match? |
|---|---:|---:|---|
| `match_status` | 0.953 | 0.100 | NO |
| `amount_variance_ratio` | 0.040 | 0.000 | NO |
| `duplicate_score` | 0.007 | 0.000 | NO |
| `supplier_exception_history` | 0.033 | 0.040 | NO |
| `payment_terms_impact` | 0.515 | 0.515 | YES, but not independently graph-proven in E1 input |
| `commodity_index_correlation` | 0.822 | 0.822 | YES |
| `tax_regulatory_compliance` | 0.938 | 0.150 | NO |

### E2 VERDICT: FAIL

Iterations: 2 plus formula-boundary diagnostics.  
Faithfulness achieved: NO.

E1 and E2 do **not** show that the data is merely incomplete. The two hard
divergences are unreachable from the current graph-context formulas. Per the
experiment gate, E3 population validation was skipped.

## E3: Population Faithfulness

**SKIPPED.** E2 failed, so the population gate was not run. A population rate
would not be meaningful while the single-invoice factor vector is mathematically
unable to match its target.

## Phase E Synthesis

### Faithfulness Achievable: NO, under current factor formulas

The FIX-B premise “seed entities, then preserve the SQLite decision vector” is
not achievable by seeding properties alone. The current SQLite “ground truth”
is a stored fixture vector, while the graph factor code computes a different
semantics from graph topology.

### Canonical Property Set for Migration

The entity migration should still seed these factor-readable properties for a
future corrected factor implementation:

| Label | Required properties | Source status |
|---|---|---|
| Invoice | `invoice_id`, `supplier_id`, `po_number`, `amount`, `category`, metadata needed for request context | JSON fixture, but reconcile factor fields |
| Supplier | `supplier_id`, `exception_rate`, `payment_terms`, `otif_score` | JSON supplier fixture currently conflicts with invoice factor target |
| PurchaseOrder | `po_id`, `po_number`, `supplier_id`, `amount`, `currency` | JSON fixture plus authoritative PO amount required |
| GoodsReceipt | `gr_id`, received quantity/status/date | A′ wrapper currently uses `qty_received=0`; authoritative receipt data required |
| Commodity | `commodity_id`, `volatility` | JSON/derived source; commodity perturbation proved this path |
| Contract | `contract_id` plus compliance/terms properties | Contract source required; current formula ignores them |
| Invoice siblings | `invoice_id`, `amount`, supplier linkage | Required for bounded DuplicateScore |

### Authoritative Source

**HYBRID, with unresolved conflicts.** The current `s2p.db` tables and columns
needed for the stored target are:

- `decisions.factors_json`
- `decisions.factor_vector_json`
- `decisions.recommended_action`
- `decision_entity_edges.decision_id`, `entity_id`, `edge_type`

Those tables do not provide the entity properties required by graph factor
computation. A real migration needs governed source tables or fixture fields for
PO amounts, receipt status/quantities, supplier exception history, contract
compliance, and sibling invoices.

### Migration Data Contract

Track 1 must not treat the stored SQLite factor vector as proof that the entity
subgraph is semantically faithful. It must either:

1. change the factor formulas to consume explicit graph-native evidence and
   define target-compatible formulas for match status and compliance; or
2. persist the existing factor values as decision-level authoritative
   properties and make the score path explicitly use those values, with clear
   provenance that they are fixture/materialized rather than recomputed.

The migration must retain domain/provenance/entity identity, seed all five
outgoing factor entities, add bounded sibling data for DuplicateScore, and
define a source-of-truth policy for the JSON-vs-stored-factor conflicts.

### What Surprised Us

1. The SQLite database contains no entity-property store that could serve as a
   direct graph migration source; its representative edge is only
   Decision→Invoice.
2. Adding explicit target-valued `match_status` and compliance properties to
   graph nodes had no effect because the current factor code never reads them.
3. The graph and SQLite values that agree (`payment_terms_impact` and
   `commodity_index_correlation`) do not have the same evidentiary status:
   commodity was genuinely graph-derived, while payment terms requires an
   invoice `payment_days` input to be graph-derived.
4. The “SQLite ground truth” is partly fixture coincidence: `_fallback` returns
   the invoice’s stored factor fields when graph context is absent.

### Blocking Issues for B2/F/C/D

1. **BLOCKER:** `MatchStatus` must be redesigned or supplied a graph-native
   formula capable of producing the intended continuous/graded value.
2. **BLOCKER:** `TaxRegulatoryCompliance` must use compliance properties rather
   than topology-only `Contract present` branching.
3. **BLOCKER:** define authoritative source values for PO amount, sibling
   invoices, supplier exception rate, and payment-day context.
4. **BLOCKER:** replace the absent two-track implementation document or provide
   its canonical path before implementation proceeds.
5. E3 population faithfulness cannot start until E2 passes.

## Cleanup

- Sandboxes dropped: YES. Two protocol-prefixed graphs from this run were
  dropped; zero `protocol_v2_test_s2p_active_*` graphs remain.
- Scripts deleted: YES. `_phase_e.py` was deleted.
- Production files edited: NO.
- Test files edited: NO.
- `soc_graph` untouched: YES; it remained present and was never a target.

## READY FOR B2/F/C/D: NO

Phase E blocks the FIX-B migration until the two factor formulas and the
authoritative source contract are resolved. Making the current endpoint
graph-backed without those changes would convert the previously visible timeout
into a silently wrong decision.
