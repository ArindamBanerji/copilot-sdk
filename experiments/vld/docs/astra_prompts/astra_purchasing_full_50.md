# Generate 50 PURCHASING Multi-Hop Investigation Scenarios

## What you're building

You are generating synthetic test data for an AI copilot that helps restaurant/retail inventory managers make ordering decisions. Each scenario is a multi-step investigation where the correct action can ONLY be determined by following graph-based evidence — surface-level features alone point to the WRONG action.

## Output

One JSON file with this structure:

```json
{
  "_header": "PLANTED SYNTHETIC — POSITIVE CONTROL — NOT A MEASUREMENT OF VLD VALUE ON REAL DECISIONS.",
  "_spec": "multihop_scenario_spec_v2.md",
  "_stage": "Stage 1: 50 PURCHASING instances (30 strong + 10 moderate + 10 controls)",
  "provenance": "sample",
  "scenarios": [ <50 scenario objects> ]
}
```

## The PURCHASING Domain

**What the copilot does:** An inventory manager receives order signals (demand spikes, supplier issues, waste alerts, stockout risks, quality incidents). The copilot scores each signal and recommends an action. Some signals LOOK like routine reorders but are actually complex — the investigation checks demand calendars, supplier histories, consumption patterns, and quality records.

**Categories (5):** demand_pattern, supplier_comparison, consumption_history, stockout_risk, quality_incident

**Actions (6):** order_standard, order_increased, order_reduced, switch_supplier, defer_order, emergency_order

**Factors (6 numeric values, each 0.0 to 1.0):**
- demand_forecast — predicted demand relative to normal (1.0 = very high demand)
- supplier_reliability — historical supplier on-time/in-full rate (1.0 = very reliable)
- consumption_rate — current consumption vs forecast (1.0 = consuming much faster than expected)
- shelf_life — remaining shelf life relative to order cycle (1.0 = very short shelf life remaining)
- cost_efficiency — cost vs budget/alternatives (1.0 = very expensive/inefficient)
- quality_score — recent quality inspection results (1.0 = perfect quality)

## Scenario JSON Schema

Each scenario MUST have ALL of these fields:

```json
{
  "scenario_id": "PUR-001-v1",
  "scenario_type": "hidden_seasonal_spike",
  "copilot": "purchasing",
  "branching_kind": "score_keyed",
  "rho_planted": 0.90,
  "description": "Low stock looks like standard reorder but demand calendar shows holiday spike in 5 days",

  "alert": {
    "alert_id": "ALERT-PUR-001",
    "category": "stockout_risk",
    "surface_factors": {
      "demand_forecast": 0.30,
      "supplier_reliability": 0.85,
      "consumption_rate": 0.40,
      "shelf_life": 0.70,
      "cost_efficiency": 0.75,
      "quality_score": 0.90
    }
  },

  "available_branches": [
    {
      "branch_id": "check_demand_calendar",
      "evidence_source": "demand_planning_system",
      "read_cost": 1,
      "factor_enriched": "demand_forecast",
      "factor_new_value": 0.95,
      "evidence_found": "Valentine's Day in 5 days — historical demand 4x normal for chocolate items",
      "narration": "Demand calendar shows a major spike that baseline forecast missed"
    },
    {
      "branch_id": "check_consumption_trend",
      "evidence_source": "pos_analytics",
      "read_cost": 1,
      "factor_enriched": "consumption_rate",
      "factor_new_value": 0.85,
      "evidence_found": "POS data shows 3x consumption rate over last 3 days (pre-holiday buying)",
      "narration": "Consumption is already accelerating ahead of the holiday"
    },
    {
      "branch_id": "check_supplier_lead_time",
      "evidence_source": "supplier_portal",
      "read_cost": 1,
      "factor_enriched": "supplier_reliability",
      "factor_new_value": 0.80,
      "evidence_found": "Standard 3-day lead time, supplier has stock available",
      "narration": "Supplier can deliver — but only if ordered today"
    }
  ],

  "correct_branches": ["check_demand_calendar", "check_consumption_trend"],
  "misleading_branches": ["check_supplier_lead_time"],
  "read_costs": {"check_demand_calendar": 1, "check_consumption_trend": 1, "check_supplier_lead_time": 1},
  "budget": 2,
  "surface_only_resolvable": false,

  "decision_tree": {
    "ground_truth_action": "order_increased",
    "reasoning": "Surface shows moderate demand (0.30), steady consumption (0.40) — suggests order_standard. But demand calendar reveals 4x holiday spike and consumption is already accelerating (0.85). Must order_increased immediately to avoid stockout.",
    "hops": [
      {
        "step": 1,
        "branch_id": "check_demand_calendar",
        "evidence_source": "demand_planning_system",
        "evidence_found": "Valentine's Day in 5 days — historical demand 4x normal",
        "factor_enriched": "demand_forecast",
        "factor_new_value": 0.95,
        "narration": "Demand calendar shows a major spike that baseline forecast missed"
      },
      {
        "step": 2,
        "branch_id": "check_consumption_trend",
        "evidence_source": "pos_analytics",
        "evidence_found": "POS data shows 3x consumption rate over last 3 days",
        "factor_enriched": "consumption_rate",
        "factor_new_value": 0.85,
        "narration": "Consumption is already accelerating ahead of the holiday"
      }
    ]
  },

  "alternative_branches": [],
  "graph_nodes": [
    {"id": "item_chocolate", "type": "Item", "label": "Premium Chocolate Box"},
    {"id": "calendar_valentines", "type": "DemandEvent", "label": "Valentine's Day"},
    {"id": "supplier_cocoa", "type": "Supplier", "label": "Cocoa Direct Ltd"}
  ],
  "graph_edges": [
    {"source": "item_chocolate", "target": "calendar_valentines", "type": "DEMAND_SPIKE_ON"},
    {"source": "item_chocolate", "target": "supplier_cocoa", "type": "SUPPLIED_BY"}
  ]
}
```

## THE CRITICAL DESIGN RULE: Boundary Crossing

1. Set surface factors so they are closest to the WRONG action's centroid.
2. Set hop evidence so that at least 2 factors shift by >= 0.30 each.
3. Each hop MUST enrich a DIFFERENT factor.
4. ground_truth_action must be DIFFERENT from what surface factors suggest.

## Action Profiles

| Action | demand | supplier | consumption | shelf_life | cost_eff | quality |
|---|---|---|---|---|---|---|
| order_standard | 0.3-0.5 | 0.7-1.0 | 0.3-0.5 | 0.5-0.7 | 0.6-0.8 | 0.7-1.0 |
| order_increased | 0.7-1.0 | 0.6-0.9 | 0.7-1.0 | 0.3-0.6 | 0.3-0.6 | 0.6-0.9 |
| order_reduced | 0.1-0.3 | 0.5-0.8 | 0.1-0.3 | 0.7-1.0 | 0.7-1.0 | 0.5-0.8 |
| switch_supplier | 0.3-0.6 | 0.0-0.3 | 0.3-0.6 | 0.3-0.6 | 0.6-1.0 | 0.0-0.4 |
| defer_order | 0.0-0.3 | 0.4-0.7 | 0.0-0.3 | 0.7-1.0 | 0.7-1.0 | 0.6-0.9 |
| emergency_order | 0.8-1.0 | 0.2-0.5 | 0.8-1.0 | 0.0-0.3 | 0.0-0.4 | 0.4-0.7 |

## Instance Distribution (50 total)

### Block A: 30 Strong-Conditional (rho >= 0.70)

6 templates x 5 variations. Every hop shifts >= 0.30.

rho: 0.70=10, 0.90=12, 1.00=8

**Template 1: Hidden seasonal spike** (PUR-001 to PUR-005)
Surface: order_standard (moderate demand). Evidence: holiday spike coming. GT: order_increased or emergency_order.
Shifts: demand_forecast LOW->HIGH (>=0.50), consumption_rate LOW->HIGH (>=0.30).

**Template 2: Reliable supplier, bad batch** (PUR-006 to PUR-010)
Surface: order_standard (high supplier reliability). Evidence: quality hold on recent batch. GT: switch_supplier.
Shifts: supplier_reliability HIGH->LOW (>=0.50), quality_score HIGH->LOW (>=0.40).

**Template 3: Looks fresh, actually expiring** (PUR-011 to PUR-015)
Surface: order_standard (normal shelf life). Evidence: batch received was near-expiry. GT: order_reduced or defer_order.
Shifts: shelf_life LOW->HIGH (>=0.50), cost_efficiency LOW->HIGH (>=0.30).

**Template 4: Cheap supplier, hidden costs** (PUR-016 to PUR-020)
Surface: order_standard (good cost efficiency). Evidence: return rate 3x normal, net cost higher. GT: switch_supplier.
Shifts: cost_efficiency HIGH->LOW (>=0.40), quality_score HIGH->LOW (>=0.40).

**Template 5: Steady consumption, upcoming closure** (PUR-021 to PUR-025)
Surface: order_standard (steady consumption). Evidence: store closure for renovation next week. GT: order_reduced or defer_order.
Shifts: consumption_rate MED->LOW (>=0.30), demand_forecast MED->LOW (>=0.30).

**Template 6: Good quality, wrong item substituted** (PUR-026 to PUR-030)
Surface: order_standard (high quality). Evidence: supplier shipped substitute item. GT: switch_supplier or emergency_order.
Shifts: quality_score HIGH->LOW (>=0.40), supplier_reliability HIGH->LOW (>=0.30).

### Block B: 10 Moderate (rho = 0.30 and 0.50)

**Template 7: Ambiguous demand signal** (PUR-031 to PUR-035) rho=0.30
**Template 8: Borderline shelf life** (PUR-036 to PUR-040) rho=0.50

### Block C: 5 Flat Controls (PUR-FLAT-001 to PUR-FLAT-005)

surface_only_resolvable=true, hops=[], budget=0, rho=1.00.

### Block D: 5 rho=0.50 Checks (PUR-RHO50-001 to PUR-RHO50-005)

rho=0.50, has hops. VLD should equal chance (1/6=0.167).

## Graph Entities

**Node types:** Item, Supplier, DemandEvent, InventoryLevel, ConsumptionRecord, ShelfLifeSpec, QualityReport, Batch, AlternativeSupplier, StoreSchedule

**Edge types:** SUPPLIED_BY, DEMAND_SPIKE_ON, CURRENT_LEVEL, CONSUMED_AT, EXPIRES_PER, FROM_BATCH, ALTERNATIVE_FOR, SUBSTITUTE_OF, QUALITY_HOLD_ON

## Checklist

- [ ] scenario_id starts with "PUR-"
- [ ] copilot = "purchasing"
- [ ] surface_factors has 6 keys: demand_forecast, supplier_reliability, consumption_rate, shelf_life, cost_efficiency, quality_score
- [ ] ground_truth_action: order_standard, order_increased, order_reduced, switch_supplier, defer_order, emergency_order
- [ ] Block A: GT differs from surface, each hop shifts >= 0.30
- [ ] Each hop enriches a DIFFERENT factor
- [ ] Block C: surface_only_resolvable=true, hops=[]
- [ ] Block D: rho=0.50, has hops
- [ ] provenance = "sample"
- [ ] No duplicate IDs
- [ ] All 6 actions appear at least 3 times
