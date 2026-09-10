# Generate 50 TRADING Multi-Hop Investigation Scenarios

## What you're building

You are generating synthetic test data for an AI copilot that helps portfolio managers evaluate trade decisions. Each scenario is a multi-step investigation where the correct action can ONLY be determined by following graph-based evidence — surface-level features alone point to the WRONG action.

## Output

One JSON file with this structure:

```json
{
  "_header": "PLANTED SYNTHETIC — POSITIVE CONTROL — NOT A MEASUREMENT OF VLD VALUE ON REAL DECISIONS.",
  "_spec": "multihop_scenario_spec_v2.md",
  "_stage": "Stage 1: 50 TRADING instances (30 strong + 10 moderate + 10 controls)",
  "provenance": "sample",
  "scenarios": [ <50 scenario objects> ]
}
```

## The TRADING Domain

**What the copilot does:** A portfolio manager receives trade signals (thesis contradictions, concentration risks, timing anomalies, fundamental changes, correlation patterns). The copilot scores each signal and recommends an action. Some trades LOOK safe on the surface but are actually risky — the investigation checks portfolio context, thesis validity, market correlations, and earnings calendars.

**Categories (5):** thesis_check, portfolio_exposure, time_pattern, fundamental_change, correlation_risk

**Actions (5):** execute, defer, reduce_size, hedge, reject

**Factors (6 numeric values, each 0.0 to 1.0):**
- thesis_alignment — does this trade align with stated investment thesis? (1.0 = perfect alignment)
- portfolio_concentration — how concentrated is the portfolio in this sector? (1.0 = very concentrated)
- timing_signal — is the timing favorable? (1.0 = strong favorable timing)
- fundamental_strength — how strong are the fundamentals? (1.0 = very strong)
- correlation_risk — how correlated is this with existing positions? (1.0 = highly correlated)
- liquidity_risk — how liquid is this position? (1.0 = very illiquid/risky)

## Scenario JSON Schema

Each scenario MUST have ALL of these fields:

```json
{
  "scenario_id": "TRD-001-v1",
  "scenario_type": "hidden_thesis_shift",
  "copilot": "trading",
  "branching_kind": "score_keyed",
  "rho_planted": 0.90,
  "description": "Trade looks thesis-aligned but the sector thesis was revised last week",

  "alert": {
    "alert_id": "ALERT-TRD-001",
    "category": "thesis_check",
    "surface_factors": {
      "thesis_alignment": 0.85,
      "portfolio_concentration": 0.20,
      "timing_signal": 0.75,
      "fundamental_strength": 0.80,
      "correlation_risk": 0.15,
      "liquidity_risk": 0.10
    }
  },

  "available_branches": [
    {
      "branch_id": "check_thesis_history",
      "evidence_source": "thesis_registry",
      "read_cost": 1,
      "factor_enriched": "thesis_alignment",
      "factor_new_value": 0.15,
      "evidence_found": "Sector thesis revised from 'overweight' to 'underweight' 5 days ago",
      "narration": "The thesis this trade was based on has been reversed"
    },
    {
      "branch_id": "check_concentration",
      "evidence_source": "portfolio_analytics",
      "read_cost": 1,
      "factor_enriched": "portfolio_concentration",
      "factor_new_value": 0.80,
      "evidence_found": "Adding this position would put sector at 35% of portfolio (limit: 25%)",
      "narration": "Concentration breach — this trade would exceed sector limits"
    },
    {
      "branch_id": "check_momentum",
      "evidence_source": "technical_analytics",
      "read_cost": 1,
      "factor_enriched": "timing_signal",
      "factor_new_value": 0.70,
      "evidence_found": "RSI at 55, neutral zone — no strong timing signal",
      "narration": "Timing is neutral, not a concern but not a catalyst"
    }
  ],

  "correct_branches": ["check_thesis_history", "check_concentration"],
  "misleading_branches": ["check_momentum"],
  "read_costs": {"check_thesis_history": 1, "check_concentration": 1, "check_momentum": 1},
  "budget": 2,
  "surface_only_resolvable": false,

  "decision_tree": {
    "ground_truth_action": "reject",
    "reasoning": "Surface shows strong thesis alignment (0.85), low concentration (0.20), good timing (0.75), strong fundamentals (0.80) — suggests execute. But the thesis was reversed last week (alignment drops to 0.15) and this trade would breach concentration limits (0.80). Must reject.",
    "hops": [
      {
        "step": 1,
        "branch_id": "check_thesis_history",
        "evidence_source": "thesis_registry",
        "evidence_found": "Sector thesis revised from 'overweight' to 'underweight' 5 days ago",
        "factor_enriched": "thesis_alignment",
        "factor_new_value": 0.15,
        "narration": "The thesis this trade was based on has been reversed"
      },
      {
        "step": 2,
        "branch_id": "check_concentration",
        "evidence_source": "portfolio_analytics",
        "evidence_found": "Adding this position would put sector at 35% of portfolio (limit: 25%)",
        "factor_enriched": "portfolio_concentration",
        "factor_new_value": 0.80,
        "narration": "Concentration breach — this trade would exceed sector limits"
      }
    ]
  },

  "alternative_branches": [],
  "graph_nodes": [
    {"id": "trade_signal_001", "type": "TradeSignal", "label": "Buy 500 ACME Corp"},
    {"id": "thesis_revision", "type": "ThesisRevision", "label": "Tech sector: OW -> UW"},
    {"id": "portfolio_state", "type": "PortfolioState", "label": "Tech at 28% (limit 25%)"}
  ],
  "graph_edges": [
    {"source": "trade_signal_001", "target": "thesis_revision", "type": "GOVERNED_BY"},
    {"source": "trade_signal_001", "target": "portfolio_state", "type": "IMPACTS_CONCENTRATION"}
  ]
}
```

## THE CRITICAL DESIGN RULE: Boundary Crossing

1. Set surface factors so they are closest to the WRONG action's centroid.
2. Set hop evidence so that at least 2 factors shift by >= 0.30 each.
3. Each hop MUST enrich a DIFFERENT factor.
4. ground_truth_action must be DIFFERENT from what surface factors suggest.

## Action Profiles

| Action | thesis | concentration | timing | fundamental | correlation | liquidity |
|---|---|---|---|---|---|---|
| execute | 0.7-1.0 | 0.0-0.3 | 0.6-1.0 | 0.7-1.0 | 0.0-0.3 | 0.0-0.3 |
| defer | 0.5-0.7 | 0.2-0.5 | 0.2-0.5 | 0.4-0.6 | 0.2-0.5 | 0.2-0.5 |
| reduce_size | 0.4-0.7 | 0.5-0.8 | 0.3-0.6 | 0.5-0.7 | 0.4-0.7 | 0.3-0.6 |
| hedge | 0.3-0.6 | 0.4-0.7 | 0.3-0.5 | 0.4-0.6 | 0.6-0.9 | 0.4-0.7 |
| reject | 0.0-0.3 | 0.6-1.0 | 0.0-0.4 | 0.0-0.4 | 0.6-1.0 | 0.6-1.0 |

## Instance Distribution (50 total)

### Block A: 30 Strong-Conditional (rho >= 0.70)

6 templates x 5 variations. Every hop shifts >= 0.30.

rho: 0.70=10, 0.90=12, 1.00=8

**Template 1: Hidden thesis reversal** (TRD-001 to TRD-005)
Surface: execute. Evidence: thesis reversed + concentration breach. GT: reject.
Shifts: thesis_alignment HIGH->LOW (>=0.50), portfolio_concentration LOW->HIGH (>=0.40).

**Template 2: Correlated positions masked** (TRD-006 to TRD-010)
Surface: execute (low correlation). Evidence: 3 existing positions are correlated through sector. GT: hedge or reduce_size.
Shifts: correlation_risk LOW->HIGH (>=0.50), liquidity_risk LOW->HIGH (>=0.30).

**Template 3: Strong fundamentals, earnings trap** (TRD-011 to TRD-015)
Surface: execute (strong fundamentals). Evidence: earnings in 3 days, implied vol spike. GT: defer.
Shifts: timing_signal HIGH->LOW (>=0.40), fundamental_strength HIGH->LOW (>=0.30).

**Template 4: Safe size, illiquid exit** (TRD-016 to TRD-020)
Surface: execute (small position). Evidence: daily volume can't support exit in < 5 days. GT: reduce_size.
Shifts: liquidity_risk LOW->HIGH (>=0.50).

**Template 5: Momentum looks good, mean reversion due** (TRD-021 to TRD-025)
Surface: execute (strong timing). Evidence: RSI > 80, historically reverts within 5 days. GT: defer or hedge.
Shifts: timing_signal HIGH->LOW (>=0.40), correlation_risk LOW->HIGH (>=0.30).

**Template 6: Thesis aligned but sector rotating** (TRD-026 to TRD-030)
Surface: execute. Evidence: macro rotation out of sector, fund flows negative. GT: defer or reject.
Shifts: thesis_alignment HIGH->LOW (>=0.40), fundamental_strength HIGH->LOW (>=0.30).

### Block B: 10 Moderate (rho = 0.30 and 0.50)

**Template 7: Ambiguous momentum** (TRD-031 to TRD-035) rho=0.30
**Template 8: Borderline concentration** (TRD-036 to TRD-040) rho=0.50

### Block C: 5 Flat Controls (TRD-FLAT-001 to TRD-FLAT-005)

surface_only_resolvable=true, hops=[], budget=0, rho=1.00.

### Block D: 5 rho=0.50 Checks (TRD-RHO50-001 to TRD-RHO50-005)

rho=0.50, has hops. VLD should equal chance (1/5=0.200).

## Graph Entities

**Node types:** TradeSignal, Position, Portfolio, Sector, ThesisRevision, EarningsEvent, CorrelationCluster, LiquidityProfile, MacroIndicator, TechnicalSignal

**Edge types:** GOVERNED_BY, IN_SECTOR, CORRELATED_WITH, IMPACTS_CONCENTRATION, EARNINGS_ON, HEDGED_BY, SECTOR_ROTATION, LIQUIDITY_CONSTRAINT

## Checklist

- [ ] scenario_id starts with "TRD-"
- [ ] copilot = "trading"
- [ ] surface_factors has 6 keys: thesis_alignment, portfolio_concentration, timing_signal, fundamental_strength, correlation_risk, liquidity_risk
- [ ] ground_truth_action: execute, defer, reduce_size, hedge, reject
- [ ] Block A: GT differs from surface, each hop shifts >= 0.30
- [ ] Each hop enriches a DIFFERENT factor
- [ ] Block C: surface_only_resolvable=true, hops=[]
- [ ] Block D: rho=0.50, has hops
- [ ] provenance = "sample"
- [ ] No duplicate IDs
- [ ] All 5 actions appear at least 3 times
