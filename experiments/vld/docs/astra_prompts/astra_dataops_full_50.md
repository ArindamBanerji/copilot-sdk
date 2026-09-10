# Generate 50 DATAOPS Multi-Hop Investigation Scenarios

## What you're building

You are generating synthetic test data for an AI copilot that helps DataOps engineers triage pipeline alerts. Each scenario is a multi-step investigation where the correct action can ONLY be determined by following graph-based evidence — surface-level features alone point to the WRONG action.

## Output

One JSON file with this structure:

```json
{
  "_header": "PLANTED SYNTHETIC — POSITIVE CONTROL — NOT A MEASUREMENT OF VLD VALUE ON REAL DECISIONS.",
  "_spec": "multihop_scenario_spec_v2.md",
  "_stage": "Stage 1: 50 DATAOPS instances (30 strong + 10 moderate + 10 controls)",
  "provenance": "sample",
  "scenarios": [ <50 scenario objects> ]
}
```

## The DATAOPS Domain

**What the copilot does:** A DataOps engineer receives pipeline alerts (data drift, schema changes, pipeline failures, latency spikes). The copilot scores each alert and recommends an action. Some alerts LOOK routine on the surface but are actually serious — the investigation loop checks graph evidence to find the true root cause.

**Categories (6):** pipeline_failure, data_drift, schema_change, latency_spike, dependency_cascade, quality_degradation

**Actions (5):** auto_fix, manual_fix, rollback, escalate_to_owner, monitor

**Factors (6 numeric values, each 0.0 to 1.0):**
- source_reliability — how trustworthy is the data source? (1.0 = very reliable)
- schema_stability — has the schema changed recently? (1.0 = very stable)
- data_quality — current data quality score (1.0 = perfect)
- impact_scope — how many downstream systems affected? (1.0 = many systems)
- pattern_familiarity — have we seen this pattern before? (1.0 = very familiar)
- transformation_health — are ETL transformations healthy? (1.0 = all healthy)

## Scenario JSON Schema

Each scenario MUST have ALL of these fields:

```json
{
  "scenario_id": "DO-001-v1",
  "scenario_type": "hidden_cascade",
  "copilot": "dataops",
  "branching_kind": "score_keyed",
  "rho_planted": 0.90,
  "description": "Pipeline alert looks like isolated failure but schema change propagated to 5 systems",

  "alert": {
    "alert_id": "ALERT-DO-001",
    "category": "pipeline_failure",
    "surface_factors": {
      "source_reliability": 0.85,
      "schema_stability": 0.80,
      "data_quality": 0.75,
      "impact_scope": 0.20,
      "pattern_familiarity": 0.90,
      "transformation_health": 0.70
    }
  },

  "available_branches": [
    {
      "branch_id": "check_schema_history",
      "evidence_source": "schema_registry",
      "read_cost": 1,
      "factor_enriched": "schema_stability",
      "factor_new_value": 0.15,
      "evidence_found": "MATKL_V2 migration: 340K new material codes pushed 3 days ago",
      "narration": "Schema registry shows a major migration that surface metrics missed"
    },
    {
      "branch_id": "check_downstream_impact",
      "evidence_source": "dependency_graph",
      "read_cost": 1,
      "factor_enriched": "impact_scope",
      "factor_new_value": 0.95,
      "evidence_found": "5 downstream systems affected including billing pipeline",
      "narration": "Dependency graph reveals cascade to billing — not isolated"
    },
    {
      "branch_id": "check_similar_patterns",
      "evidence_source": "pattern_database",
      "read_cost": 1,
      "factor_enriched": "pattern_familiarity",
      "factor_new_value": 0.85,
      "evidence_found": "Similar pattern resolved by auto-fix 12 times before",
      "narration": "Pattern database confirms this looks familiar on the surface"
    }
  ],

  "correct_branches": ["check_schema_history", "check_downstream_impact"],
  "misleading_branches": ["check_similar_patterns"],
  "read_costs": {"check_schema_history": 1, "check_downstream_impact": 1, "check_similar_patterns": 1},
  "budget": 2,
  "surface_only_resolvable": false,

  "decision_tree": {
    "ground_truth_action": "escalate_to_owner",
    "reasoning": "Surface factors suggest auto_fix (high pattern_familiarity, low impact_scope). But schema_stability drops to 0.15 (major migration) and impact_scope jumps to 0.95 (billing pipeline affected). This is not a routine fix.",
    "hops": [
      {
        "step": 1,
        "branch_id": "check_schema_history",
        "evidence_source": "schema_registry",
        "evidence_found": "MATKL_V2 migration: 340K new material codes pushed 3 days ago",
        "factor_enriched": "schema_stability",
        "factor_new_value": 0.15,
        "narration": "Schema registry shows a major migration that surface metrics missed"
      },
      {
        "step": 2,
        "branch_id": "check_downstream_impact",
        "evidence_source": "dependency_graph",
        "evidence_found": "5 downstream systems affected including billing pipeline",
        "factor_enriched": "impact_scope",
        "factor_new_value": 0.95,
        "narration": "Dependency graph reveals cascade to billing — not isolated"
      }
    ]
  },

  "alternative_branches": [],
  "graph_nodes": [
    {"id": "pipeline_erp_ingest", "type": "PipelineSystem", "label": "ERP Ingest Pipeline"},
    {"id": "schema_matkl_v2", "type": "SchemaChange", "label": "MATKL_V2 Migration"},
    {"id": "billing_pipeline", "type": "PipelineSystem", "label": "Billing Pipeline"}
  ],
  "graph_edges": [
    {"source": "pipeline_erp_ingest", "target": "schema_matkl_v2", "type": "SCHEMA_CHANGED_BY"},
    {"source": "schema_matkl_v2", "target": "billing_pipeline", "type": "IMPACTS"}
  ]
}
```

## THE CRITICAL DESIGN RULE: Boundary Crossing

Every non-control scenario MUST satisfy this: **the surface factors point to the WRONG action, and the investigation evidence redirects to the CORRECT action.**

1. Set surface factors so they are closest to the WRONG action's centroid (see Action Profiles).
2. Set hop evidence so that at least 2 factors shift by >= 0.30 each.
3. Each hop MUST enrich a DIFFERENT factor.
4. ground_truth_action must be DIFFERENT from what surface factors suggest.

## Action Profiles

| Action | source_rel | schema_stab | data_qual | impact_scope | pattern_fam | transform_health |
|---|---|---|---|---|---|---|
| auto_fix | 0.7-0.9 | 0.7-0.9 | 0.5-0.7 | 0.1-0.3 | 0.8-1.0 | 0.6-0.8 |
| manual_fix | 0.5-0.7 | 0.5-0.7 | 0.3-0.5 | 0.3-0.5 | 0.4-0.6 | 0.4-0.6 |
| rollback | 0.3-0.5 | 0.2-0.4 | 0.2-0.4 | 0.5-0.7 | 0.3-0.5 | 0.2-0.4 |
| escalate_to_owner | 0.2-0.5 | 0.1-0.3 | 0.2-0.5 | 0.7-1.0 | 0.1-0.4 | 0.1-0.3 |
| monitor | 0.8-1.0 | 0.8-1.0 | 0.7-0.9 | 0.0-0.2 | 0.7-0.9 | 0.8-1.0 |

## Instance Distribution (50 total)

### Block A: 30 Strong-Conditional (score_keyed, rho >= 0.70)

6 templates x 5 variations. Every hop shifts its factor by >= 0.30.

rho distribution: rho=0.70: 10, rho=0.90: 12, rho=1.00: 8

**Template 1: Hidden cascade** (DO-001 to DO-005)
Surface: auto_fix. Evidence: schema change cascaded to critical systems. GT: escalate_to_owner.
Shifts: impact_scope LOW->HIGH (>=0.50), schema_stability HIGH->LOW (>=0.40).

**Template 2: Familiar pattern, unfamiliar cause** (DO-006 to DO-010)
Surface: auto_fix. Evidence: root cause is new despite similar symptoms. GT: manual_fix.
Shifts: pattern_familiarity HIGH->LOW (>=0.40), source_reliability HIGH->LOW (>=0.30).

**Template 3: Quality looks fine, transformation broke** (DO-011 to DO-015)
Surface: monitor. Evidence: upstream transformation silently corrupted output. GT: rollback.
Shifts: transformation_health HIGH->LOW (>=0.50), data_quality HIGH->LOW (>=0.30).

**Template 4: Small blast radius, critical system** (DO-016 to DO-020)
Surface: auto_fix. Evidence: affected system is billing/payment pipeline. GT: escalate_to_owner.
Shifts: impact_scope LOW->HIGH (>=0.60).

**Template 5: Stable source, unstable schema** (DO-021 to DO-025)
Surface: monitor. Evidence: source pushed silent schema change. GT: manual_fix or rollback.
Shifts: schema_stability HIGH->LOW (>=0.50), transformation_health HIGH->LOW (>=0.30).

**Template 6: Drift looks cosmetic, actually structural** (DO-026 to DO-030)
Surface: monitor (small data drift). Evidence: drift is from a broken join producing duplicates. GT: rollback or manual_fix.
Shifts: data_quality HIGH->LOW (>=0.40), source_reliability HIGH->LOW (>=0.30).

Variations per template: v1-v3 different ground_truth_actions, v4 different rho, v5 rho=0.70.

### Block B: 10 Moderate (score_keyed, rho = 0.30 and 0.50)

2 templates x 5 variations. Factor shifts can be smaller (>= 0.15).

rho=0.30: 5, rho=0.50: 5

**Template 7: Ambiguous source issue** (DO-031 to DO-035)
Could be auto_fix or monitor. Evidence is ambiguous — shifts are small.

**Template 8: Noisy quality signal** (DO-036 to DO-040)
Quality fluctuates. Evidence doesn't clearly point one way.

### Block C: 5 Flat Controls (DO-FLAT-001 to DO-FLAT-005)

surface_only_resolvable = true, hops = [], budget = 0.
Surface factors alone determine action. No graph evidence.
branching_kind = "score_keyed", rho_planted = 1.00.
available_branches = [], correct_branches = [], misleading_branches = [].

### Block D: 5 rho=0.50 Instrument Checks (DO-RHO50-001 to DO-RHO50-005)

score_keyed, rho=0.50. Must have hops (not flat).
VLD accuracy should equal chance (1/5 = 0.200).

## Graph Entities

**Node types:** PipelineSystem, SchemaChange, DataSource, TransformationJob, DependencyLink, QualityCheck, PatternRecord, AlertGroup, DownstreamConsumer

**Edge types:** SCHEMA_CHANGED_BY, IMPACTS, FEEDS_INTO, TRIGGERED_BY, MATCHES_PATTERN, DEPENDS_ON, PRODUCES, CONSUMES

## Checklist Before Submitting

For EACH of the 50 scenarios, verify:
- [ ] scenario_id starts with "DO-"
- [ ] copilot = "dataops"
- [ ] branching_kind = "score_keyed"
- [ ] rho_planted matches block (A: >=0.70, B: 0.30/0.50, C: 1.00, D: 0.50)
- [ ] surface_factors has exactly 6 keys: source_reliability, schema_stability, data_quality, impact_scope, pattern_familiarity, transformation_health
- [ ] All factor values between 0.0 and 1.0
- [ ] ground_truth_action is one of: auto_fix, manual_fix, rollback, escalate_to_owner, monitor
- [ ] Block A: ground_truth_action DIFFERS from surface suggestion, each hop shifts >= 0.30
- [ ] Each hop enriches a DIFFERENT factor
- [ ] correct_branches are from available_branches
- [ ] misleading_branches NOT in correct_branches
- [ ] budget < total available_branches (non-flat)
- [ ] graph_nodes and graph_edges non-empty (non-flat)
- [ ] Block C: surface_only_resolvable=true, hops=[]
- [ ] Block D: rho=0.50, has hops
- [ ] provenance = "sample"
- [ ] No duplicate scenario_ids
- [ ] All 5 actions appear at least 3 times across all 50 scenarios
