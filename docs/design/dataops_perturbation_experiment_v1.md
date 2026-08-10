# DataOps Perturbation Experiment v1

**Date:** 2026-08-04  
**Production data modified:** NO

This report used a disposable AGE graph cloned read-only from the DataOps
subgraph in `soc_graph`. The disposable graph was dropped after the run.

## Step 0: Target

| Item | Result |
|---|---|
| Graph/fixture mode | **GRAPH mode**: AGE active, test mode, disposable graph `protocol_v2_test_dataops_aedd9b079b0d` |
| Graph status | `active_backend=age`, `active_test_mode=true`, `graph_kind=test`, `operational_graph_client_status=separate_dataops_graph_client` |
| Graph selection env | `DATAOPS_ACTIVE_GRAPH_BACKEND=age`, `DATAOPS_ACTIVE_AGE_DSN`, `DATAOPS_ACTIVE_AGE_GRAPH`, `DATAOPS_ACTIVE_AGE_DOMAIN=dataops`; `DATAOPS_ACTIVE_AGE_TEST_MODE=1` for the disposable graph |
| Endpoint | `GET /api/context/alert/{id}/factors` for graph-backed factor assembly; `POST /api/score` for action/confidence |
| Target alert | `DQ-001`, category `pipeline_failure` |
| Relationship | `DataQualityAlert-[:AFFECTS]->PipelineSystem` |
| Linked PipelineSystem | `warehouse_etl` (the stored graph has no `pipeline_id` property) |
| `business_criticality` stored | `0.92`, numeric (`agtype` numeric) |
| `sla_minutes` stored | `30`, numeric |
| `source_reliability` stored | `0.82`, numeric |

The active code does not have a standalone `business_criticality.compute()`
method. The complete consuming logic is the factor assembly in
`apps/dataops/backend/app/graph_queries.py:313-378`, specifically:

```python
"business_criticality": {
    "value": _safe_get_float(
        system,
        "business_criticality",
        self._alert_factor(alert, "business_criticality"),
    ),
    "source": source,
    "detail": "system business criticality",
},
```

The conversion helper at `graph_queries.py:93-97` is:

```python
def _safe_get_float(payload, key, default=0.0):
    try:
        return float(payload.get(key, default))
    except (TypeError, ValueError):
        return default
```

Thus the expected property shape is numeric/coercible-to-float. A missing or
wrong-type system property silently falls back to the alert-level value via
`self._alert_factor(...)`; if that is also absent or non-numeric, the helper
returns its default `0.0`.

## Step 1: Baseline Score

The graph endpoint returned `source: graph` and `all_auto_computed: true`.
The score request used those graph-derived factor values.

| Field | Value |
|---|---|
| HTTP status | 200 |
| Action | `auto_approve` |
| Confidence | `0.9148835372` |
| Latency | 93.5 ms |

| Factor | Value | Provenance |
|---|---:|---|
| impact_scope | 0.1250 | graph |
| source_reliability | 0.8200 | graph |
| recurrence_frequency | 0.1667 | graph |
| downstream_urgency | 0.7500 | graph |
| data_freshness | 0.8800 | graph response; alert property |
| business_criticality | 0.9200 | graph |

## Step 2: Baseline Faithfulness

| Factor | Stored graph input | Stored type | Expected type | Baseline value | Faithful? |
|---|---|---|---|---:|---|
| impact_scope | one downstream `FEEDS` system (`downstream_count=1`) | topology/count | integer count, normalized by 8 | 0.1250 | YES |
| source_reliability | PipelineSystem `source_reliability=0.82` | numeric | numeric/coercible float | 0.8200 | YES |
| recurrence_frequency | two matching prior `AFFECTS` alerts, `prior_count=2` | topology/count | integer count, normalized by 12 | 0.1667 | YES |
| downstream_urgency | minimum FEEDS-path SLA `30` minutes | numeric | numeric minutes, normalized by `(120-sla)/120` | 0.7500 | YES |
| business_criticality | PipelineSystem `business_criticality=0.92` | numeric | numeric/coercible float | 0.9200 | YES |
| data_freshness | alert `data_freshness=0.88` | numeric alert property | numeric/coercible float | 0.8800 | YES |

Silent defaults found: **NONE on the target**.  
Shape mismatches: **NONE on the target**.

There is nevertheless a silent-fallback contract risk in the implementation:
`source_reliability` and `business_criticality` use `_safe_get_float`, and a
bad/missing system value can be replaced by an alert value or `0.0` without an
error. This run did not trigger that fallback; the stored numeric shapes were
the shapes consumed by the active factors.

## Steps 3-5: Perturbation + Revert

Only the disposable graph property was changed:

```text
PipelineSystem(name=warehouse_etl).business_criticality: 0.92 -> 0.11
```

The post-`SET` read returned `0.11`. The same alert was then scored again.

| Field | Value |
|---|---|
| HTTP status | 200 |
| Action | `auto_approve` |
| Confidence | `0.9985834353` |
| Latency | 81.3 ms |
| Reverted | YES; post-revert read returned numeric `0.92` |

All graph factor provenance values remained `source: graph` after the
perturbation.

## Step 6: Decisive Check

| Factor | Baseline | Perturbed | Changed? |
|---|---:|---:|---|
| impact_scope | 0.1250 | 0.1250 | NO |
| source_reliability | 0.8200 | 0.8200 | NO |
| recurrence_frequency | 0.1667 | 0.1667 | NO |
| downstream_urgency | 0.7500 | 0.7500 | NO |
| data_freshness | 0.8800 | 0.8800 | NO |
| business_criticality | 0.9200 | 0.1100 | **YES** |

Perturbed factor moved: **YES**. The isolated graph property perturbation
changed the corresponding factor and no unrelated factor.

## VERDICT

**DataOps genuinely graph-backed: YES.**

The active graph-mode endpoint reported graph provenance for every factor, and
changing only the disposable PipelineSystem property changed only
`business_criticality`. This is runtime evidence, not just static source
evidence.

**Silent-default factors:** 0 observed on this target; fallback risk exists in
`source_reliability` and `business_criticality` if their system properties are
missing or non-numeric.  
**Shape mismatches:** 0 observed; the DataOps contract is numeric and the
stored values were numeric.  
**Platform pattern (SOC + DataOps):** both bespoke consumers are genuinely
graph-backed. SOC demonstrated a numeric-to-categorical shape mismatch; this
DataOps target did not. DataOps does have a separate silent fallback path that
should be guarded by explicit provenance or contract validation.

## Cleanup

| Item | Result |
|---|---|
| Disposable graph dropped | YES |
| Disposable property reverted | YES |
| Production `soc_graph` written | NO |
| Production `warehouse_etl.business_criticality` verified | unchanged at `0.92` |
| Temporary backend stopped | YES |
| Scratch script and isolated run data deleted | YES |
| Production source/test files modified | NO |

