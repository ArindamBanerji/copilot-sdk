# Platform Faithfulness Audit v1

**Date:** 2026-08-04  
**Type:** Read-only. No data modified.

## Scope and method

This audit covers the requested 18-factor denominator: SOC (6), DataOps (5),
and S2P (7). DataOps `data_freshness` and S2P `environmental_risk` are active
additional factors but are outside that requested denominator; they are noted
below.

Classification is runtime-oriented:

- **FAITHFUL**: a stored property/topology/history value reaches the factor,
  or the factor returns an explicit semantic absence value such as SOC threat
  intel `0.0` when no indicator/campaign exists.
- **SILENT-DEFAULT**: the expected evidence is absent or malformed and the
  factor returns a neutral/conservative fallback rather than reporting the
  missing contract. This includes the known SOC numeric/string mismatch.
- **STUB**: the factor ignores the value-bearing properties and returns a
  fixed bucket based only on node presence.

No graph was written. Read-only AGE queries inspected `soc_graph` and existing
empty/test S2P graph names. No populated S2P AGE entity graph or checked-in
`s2p.db` was present, so S2P rows use the committed seed contract and the
prior disposable read-only Phase E evidence where identified.

## Per-Copilot × Per-Factor Table

### SOC

Active factor order is defined in
`gen-ai-roi-demo-v4-v50/backend/app/domains/soc/config.py:743-751`.
The active SOC target is `C9B-SOC-0209`; its graph properties were read from
`soc_graph`.

| Factor | Property/evidence read | Expected type | Stored type/value | Factor value | Classification |
|---|---|---|---|---:|---|
| privileged_identity_context | User `risk_score`; alert/context `mfa_completed`, `device_fingerprint_match`, title | numeric, categorical title, booleans | User `risk_score=0.75` numeric; alert MFA=`false`, fingerprint=`true`; title absent | 0.475 | **FAITHFUL** |
| asset_criticality | Asset.criticality; optional DataClass.sensitivity | categorical string enum (`low/medium/high/critical`) | numeric `0.8`; sensitivity absent | 0.500 | **SILENT-DEFAULT** |
| threat_intel_enrichment | Alert→ThreatIndicator severity/source; Alert→Campaign severity/confidence | categorical severity strings plus numeric confidence | no matching ThreatIndicator or Campaign rows | 0.000 | **FAITHFUL**: explicit no-match zero |
| pattern_history | Decision→EvolutionEvent `factor_snapshot` / verified history | numeric factor snapshot/history, enough rows for aggregation | active `TRIGGERED_EVOLUTION` count `0` for `insider_threat` | 0.400 | **SILENT-DEFAULT**: documented neutral fallback |
| time_anomaly | alert `weekend_login`, `business_hours_login` | booleans | both properties absent | 0.700 | **SILENT-DEFAULT**: conservative absent-field fallback |
| device_trust | alert `mfa_completed`, `device_fingerprint_match`, `vpn`/`vpn_provider` | booleans or provider presence | `false`, `true`, `vpn_provider="c9b_seed"` | 0.3333 | **FAITHFUL** |

The asset factor’s complete relevant path is
`gen-ai-roi-demo-v4-v50/backend/app/domains/soc/factors.py:259-283`: it reads
`asset.criticality`, converts it to a string, maps only the categorical enum,
and uses `0.5` for an unknown value. The live `0.8` therefore does not reach
the numeric output semantically. The prior perturbation proved this diagnosis:
changing only the disposable value to string `"critical"` moved the factor
from `0.5` to `1.0`.

Other SOC fallback behavior is visible in code: pattern history falls back to
`0.40` at `factors.py:549-571`; time anomaly falls back to `0.70` at
`factors.py:599-610`; device trust consumes the alert booleans/provider at
`factors.py:640-650`. The SOC orchestrator’s provenance sidecar also labels
the pattern/time defaults as fallback at
`app/domains/soc/orchestrator.py:95-120`.

### DataOps

The target is `DQ-001` → `PipelineSystem(name=warehouse_etl)`, from the
disposable GRAPH-mode run documented in
`dataops_perturbation_experiment_v1.md`. DataOps factor assembly is in
`apps/dataops/backend/app/graph_queries.py:313-378`; graph formulas are at
`:505-566`.

| Factor | Property/evidence read | Expected type | Stored type/value | Factor value | Classification |
|---|---|---|---|---:|---|
| impact_scope | PipelineSystem FEEDS descendants | integer topology count, normalized by 8 | one downstream FEEDS node; count `1` | 0.1250 | **FAITHFUL** |
| downstream_urgency | PipelineSystem.sla_minutes across FEEDS path | numeric minutes | root minimum SLA `30` | 0.7500 | **FAITHFUL** |
| business_criticality | PipelineSystem.business_criticality | numeric/coercible float | `0.92` numeric | 0.9200 | **FAITHFUL** |
| source_reliability | PipelineSystem.source_reliability | numeric/coercible float | `0.82` numeric | 0.8200 | **FAITHFUL** |
| recurrence_frequency | DataQualityAlert AFFECTS history | integer matching-alert count, normalized by 12 | two matching prior `pipeline_failure` alerts | 0.1667 | **FAITHFUL** |

The disposable perturbation changed only
`warehouse_etl.business_criticality` from `0.92` to `0.11`; only the matching
factor moved. DataOps has fallback risk: `_safe_get_float` at
`graph_queries.py:93-97` silently uses the alert factor or `0.0` for missing or
non-numeric system properties. That risk was not triggered by this target and
is therefore not counted as an observed silent default.

### S2P

The active S2P registry contains eight factors at
`s2p-copilot/backend/app/domains/s2p/factors.py:331-339`. The requested
seven-factor denominator excludes the additional `environmental_risk` factor.
Representative target: `S2P-INV-0003` / `PO-20260003` / `SUP-003`.

Because no populated S2P AGE graph or checked-in `s2p.db` was available for a
read-only query, the “stored” column below distinguishes the migration-plan
shape from the prior disposable Phase E read. The Phase E vector is not treated
as an oracle.

| Factor | Property/evidence read | Expected type | Stored type/value | Factor value | Classification |
|---|---|---|---|---:|---|
| match_status | PurchaseOrder and GoodsReceipt presence | presence of labeled nodes/IDs | PO + GR present in Phase E disposable context | 0.100 | **STUB** |
| amount_variance_ratio | PurchaseOrder.amount vs Invoice.amount | numeric currency amounts | Invoice `3781.7` numeric; PO amount in disposable probe also `3781.7` | 0.000 | **FAITHFUL** to stored amounts; target `0.04` is a fixture/source conflict |
| duplicate_score | sibling Invoice.invoice_id and Invoice.amount | bounded sibling set with numeric amounts | no sibling invoices in direct context | 0.000 | **SILENT-DEFAULT**: graph-context neutral `0.0` |
| supplier_exception_history | Supplier.exception_rate | numeric range `[0,1]` | `0.04` numeric for SUP-003 | 0.040 | **FAITHFUL**; differs from materialized target `0.033` |
| payment_terms_impact | Supplier.payment_terms plus Invoice.payment_days | terms string parseable to days plus numeric actual days | `"Net 30"` string; `payment_days` absent from seeded Invoice shape | 0.515 | **SILENT-DEFAULT**: falls back to materialized invoice value |
| commodity_index_correlation | Commodity.volatility | numeric range `[0,1]` | `0.822` numeric in Phase E disposable read | 0.822 | **FAITHFUL** |
| tax_regulatory_compliance | Contract presence only | presence of Contract/contract_id | Contract present | 0.150 | **STUB** |

The two stubs are explicit in code. `MatchStatus.compute()` returns `0.1`,
`0.6`, or `0.9` from PO/GR presence at
`s2p-copilot/backend/app/domains/s2p/factors.py:141-159`; it never reads
amount, receipt quantity, or match properties. `TaxRegulatoryCompliance.compute()`
returns `0.15` or `0.8` from Contract presence at `factors.py:289-302`; it
does not read Contract compliance properties.

For the five non-stubs, the property readers themselves are shape-compatible
when the required entities and fields exist:

- amount reads numeric PO amount at `factors.py:165-190`;
- supplier history reads numeric `exception_rate` at `:224-241`;
- payment terms parses a terms string but requires invoice `payment_days` at
  `:247-267`;
- commodity reads numeric `volatility` at `:273-283`;
- duplicate reads sibling invoice IDs and numeric amounts at `:196-218`.

The migration seed plan at `s2p-copilot/scripts/seed_s2p_graph.py:165-218`
does not populate PO amount, receipt quantity, commodity volatility, or
invoice payment days in its canonical node shapes. Phase E’s disposable probe
supplied some of those values and demonstrated which readers respond. This is
an additional migration-contract gap even where the factor formula is not a
stub.

The additional, uncounted `environmental_risk` factor reads neighbor
`environmental_risk`/`carbon_footprint` or invoice metadata at
`factors.py:305-328`; no live stored value was available in this read-only
workspace.

## Summary

### Classification Counts

| Copilot | Total graph-factors | FAITHFUL | SILENT-DEFAULT | STUB |
|---|---:|---:|---:|---:|
| SOC | 6 | 3 | 3 | 0 |
| DataOps | 5 | 5 | 0 | 0 |
| S2P | 7 | 3 | 2 | 2 |
| **TOTAL** | **18** | **11** | **5** | **2** |

The SOC count treats missing time fields and missing active pattern history as
observed default paths because the factor outputs are exactly their coded
fallbacks. Threat-intel no-match is not counted as a default: `0.0` is the
factor’s explicit semantic result for no matching indicator/campaign.

### Platform-Wide Pattern

**Hypothesis validated: YES.** There are five observed silent-default paths
plus two topology-only stubs across the 18-factor audit. The issue is not
S2P-only: SOC has the proven numeric/string data-contract mismatch, DataOps
has silent numeric fallback branches (not triggered on its target), and S2P
has both fallback gaps and two formula stubs.

### Per Silent-Default: Data-Contract Fix

| Copilot | Factor | Stored type → expected type | Fix |
|---|---|---|---|
| SOC | asset_criticality | numeric `0.8` → categorical enum string | Standardize Asset.criticality to `low/medium/high/critical`, or change the factor contract to numeric ranges; reject unknown shapes loudly. |
| SOC | pattern_history | zero active history rows → verified Decision/EvolutionEvent history | Distinguish “no history” from a neutral materialized value and expose provenance; seed/migrate the active history edge contract. |
| SOC | time_anomaly | absent boolean flags → booleans | Require `weekend_login`/`business_hours_login`, or emit explicit missing-data provenance instead of silently using `0.7`. |
| S2P | duplicate_score | no sibling Invoice set → bounded Invoice IDs + numeric amounts | Seed/query sibling invoices or make the neutral result explicitly `missing_evidence`, not an indistinguishable score. |
| S2P | payment_terms_impact | missing numeric Invoice.payment_days plus string Supplier terms → numeric actual days + parseable terms | Add authoritative payment-days input to the graph/event contract and validate both operands before scoring. |

DataOps should receive the same explicit-missing-data guard for
`business_criticality` and `source_reliability`, even though this target was
faithful: `_safe_get_float` currently allows a system property to silently
fall through to an alert/default value.

## Implications

**S2P-only problem:** NO.  
**Platform program needed:** YES, for property-shape validation and fallback
provenance across bespoke consumers.  
**Recommended:** both property-shape standardization and per-factor fixes.
The platform should add fail-visible contracts/provenance for missing or
wrong-type graph inputs; each copilot must then correct its domain-specific
formula or migration shape. S2P additionally requires redesign of the two
presence-only stubs.

## Evidence and limitations

- SOC live values were read from `soc_graph`; no writes occurred.
- DataOps values and graph provenance come from the completed disposable AGE
  run in `dataops_perturbation_experiment_v1.md`; its graph was dropped.
- Existing S2P shadow/test graph names were read and contained no Invoice,
  Supplier, PO, or Contract nodes. No S2P graph was created because this audit
  was read-only.
- The S2P committed SQLite runtime file was absent, so current SQLite row
  values could not be independently re-read in this workspace. Phase E
  disposable read evidence and committed seed shapes are cited explicitly.

## Cleanup

| Item | Result |
|---|---|
| Scripts deleted | YES; no scratch script was required |
| Data modified | NO |
| Production graph modified | NO |
| Disposable graph created | NO |

