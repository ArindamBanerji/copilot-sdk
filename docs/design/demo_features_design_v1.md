# Demo Feature Design — Path to 56/56
**Date:** Sep 18, 2026
**Purpose:** Bottoms-up design of every product capability needed to bring the 56 demo specs from 30 pass / 26 skip to 56 pass / 0 skip.

---

## Current State

| Category | Count | Specs |
|---|---|---|
| Passing | 30 | SOC-01/03/04/07/08, S2P-04/05/06/08, PUR-01/02/03/04, TRD-01/03/06, DO-01/02/03/06, PLAT-02/04/06/07, MACH-04, PILOT-01/02/03/04, FORK-01 |
| Auto-skip (endpoint down) | 16 | SOC-02/06/09/10, S2P-01/02/03/09, PUR-05, TRD-02, DO-04/05, PLAT-03, MACH-01/02/03 |
| Permanent skip (ROADMAP) | 7 | SOC-05, S2P-07, PUR-06, TRD-04/05, DO-07/08 |
| Permanent skip (CONCEPTUAL) | 3 | PLAT-01, PLAT-05, MACH-05 |

---

## Part 1: Feature Inventory (26 specs → 12 features)

### F-DEMO-01: SOC Alert Analyze Contract (6 specs)
**Specs served:** SOC-02, SOC-06, SOC-09, MACH-01, MACH-02, MACH-03
**Repo:** gen-ai-roi-demo-v4-v50

**What the demos need:**
- SOC-02 (no-precedent): POST analyze with a planted alert → response has action=ESCALATE, similar_cases=[] (empty), factors present
- SOC-06 (policy-wins): POST analyze → response shows policy_override=true when alert matches a referral rule
- SOC-09 (same-alert): POST analyze twice with identical payload → identical action, identical confidence, identical factor contributions
- MACH-01 (through-machine): POST analyze → response includes read_sequence (ordered factor read list) and decision_trace
- MACH-02 (reshape): POST analyze with no-precedent alert (same as SOC-02) → zero similar_cases, ESCALATE
- MACH-03 (parameter-moved): POST analyze twice, second after a verified outcome changes K routing → different factor read order

**What exists:**
- POST /api/alert/analyze exists and returns 200 (SOC-DEMO-READY confirmed)
- PL-SOC-1 (no_precedent_alert.json) fixture exists
- PL-SOC-3 (policy_conflict_alert.json) fixture exists
- PL-MACH-1 (soc_decision_trace.json) fixture exists
- PL-MACH-3 (soc_recursion_k_delta.json) fixture exists

**What's missing (product gaps):**
1. **Response shape gaps.** The /api/alert/analyze response may not include:
   - `similar_cases` array (needed for SOC-02, MACH-02)
   - `policy_override` or `referral_rule` field (needed for SOC-06)
   - `read_sequence` or `decision_trace` (needed for MACH-01, MACH-03)
2. **Fixture injection path.** Planted alerts need to be findable by the analyze endpoint. The preseed script places fixture files on disk, but the backend needs to load and route them.
3. **K-routing delta.** MACH-03 requires two sequential calls where the K routing changes between them. This needs either: (a) a verified outcome between calls that moves the K entry, or (b) a planted state where the K routing is pre-configured to produce different read orders for two alert profiles.

**Design:**
```
POST /api/alert/analyze
Request:  { alert_id: string, ?context: object }
Response: {
  alert_id: string,
  action: string,           // escalate | investigate | suppress | monitor
  confidence: number,
  factors: Array<{ name: string, value: number, weight: number }>,
  similar_cases: Array<{ alert_id: string, similarity: number }>,  // NEW or verify exists
  policy_override: boolean,  // NEW: true if referral rule overrode AI recommendation
  referral_rule: string?,    // NEW: which rule triggered
  decision_trace: {          // NEW
    read_sequence: string[], // ordered factor names as read
    enrichment_reads: number,
    decision_id: string
  }
}
```

**Implementation:**
- Extend the analyze response to include similar_cases, policy_override, decision_trace
- Ensure planted fixtures (PL-SOC-1, PL-SOC-3) are loaded by the preseed script and discoverable by the analyze endpoint
- For MACH-03: create a two-step test that calls analyze → outcome → analyze and asserts read_sequence differs

**Tests:** +6 BE (response shape tests) + verify existing planted fixtures load
**Effort:** 1.5d

---

### F-DEMO-02: SOC Checkpoint/Rollback (1 spec)
**Specs served:** SOC-10
**Repo:** gen-ai-roi-demo-v4-v50

**What the demo needs:**
- Create a named checkpoint (save current scorer state)
- Make a decision that changes the state
- Rollback to the checkpoint → state matches the saved checkpoint

**What exists:**
- PL-SOC-5 (checkpoint_rollback.json) fixture exists
- The simulate-failure endpoint exists and works (SOC-GATE-FIX shipped)

**What's missing:**
- POST /api/learning/checkpoint (create checkpoint)
- POST /api/learning/rollback (restore checkpoint)
- GET /api/learning/checkpoints (list checkpoints)

**Design:**
```
POST /api/learning/checkpoint
Request:  { name: string }
Response: { checkpoint_id: string, name: string, created_at: string,
            state_hash: string, decision_count: number }

POST /api/learning/rollback
Request:  { checkpoint_id: string }
Response: { restored: true, checkpoint_id: string, name: string,
            state_hash: string, decisions_rolled_back: number }

GET /api/learning/checkpoints
Response: { checkpoints: Array<{ checkpoint_id, name, created_at, state_hash }> }
```

**Implementation:**
- Serialize scorer state (centroids, conservation, decision count) to a named snapshot
- Store snapshots in-memory (dict keyed by checkpoint_id) — demo only, not production persistence
- Rollback replaces current scorer state with snapshot
- Add to SOC's main.py router

**Tests:** +4 BE (create, list, rollback, verify state)
**Effort:** 1d

---

### F-DEMO-03: S2P Score with Stable Fixtures (3 specs)
**Specs served:** S2P-01, S2P-02, S2P-03
**Repo:** s2p-copilot

**What the demos need:**
- S2P-01 (rule-said-no): POST /api/s2p/score with a copper invoice → action ACCEPT despite rule rejection, contract clause in reasoning
- S2P-02 (day-zero): POST /api/s2p/score on a fresh system → returns score with confidence > 0 and factors
- S2P-03 (paying-more): POST /api/s2p/score with container-context → action HOLD with working-capital reasoning

**What exists:**
- POST /api/s2p/score endpoint exists
- S2P preseed with 200 invoice decisions exists
- PL-S2P-1 (demo_container_context.json) fixture exists

**What's missing:**
- Stable fixture payloads (event_id + category) that the PW spec can POST and get deterministic responses
- The spec was skipped because Codex didn't know the exact payload shape

**Design:**
The PW specs need to know the exact POST body format for /api/s2p/score.
```
POST /api/s2p/score
Request: {
  event_id: string,       // e.g., "S2P-INV-0001" from preseed
  category: string,       // e.g., "price_variance"
  factors?: object        // optional override
}
Response: {
  action: string,
  confidence: number,
  factors: Array<{ name: string, value: number }>,
  reasoning?: string
}
```

**Implementation:**
- Document the exact POST payload in s2p-copilot docs
- Create 3 stable fixture payloads (one per spec) in data/demo_fixtures/
- Verify each fixture returns the expected action with current preseed state
- The product code already exists — this is a fixture + documentation task

**Tests:** +3 BE (one per fixture payload verifies expected action)
**Effort:** 0.5d

---

### F-DEMO-04: Frozen Twin API (2 specs)
**Specs served:** S2P-09, PUR-05
**Repo:** copilot-sdk (shared) + mount in S2P and Purchasing

**What the demos need:**
- S2P-09: GET twin endpoint → returns live accuracy series + frozen accuracy series with positive gap
- PUR-05: GET twin endpoint → returns two divergent waste/accuracy curves

**What exists:**
- FrozenTwinComparisonPanel (B8, shipped — frontend component)
- PL-S2P-4 (frozen twin fixture) — fixture file exists
- PL-PUR-2 (purchasing_twin_init.json) — fixture file exists

**What's missing:**
- No backend endpoint serves frozen twin data on SDK copilots or S2P
- SOC has some twin infrastructure (SOC-08 passes) but S2P and Purchasing don't

**Design:**
```
GET /api/learning/frozen-twin
Response: {
  initialized: boolean,
  frozen_at: string?,        // timestamp when twin was pinned
  frozen_accuracy: number?,  // accuracy at freeze point
  live_accuracy: number?,    // current live accuracy
  gap: number?,              // live - frozen (the compounding proof)
  series: {
    frozen: Array<{ decision_n: number, accuracy: number }>,
    live: Array<{ decision_n: number, accuracy: number }>
  }
}

POST /api/learning/frozen-twin/freeze
Response: { initialized: true, frozen_at: string, frozen_accuracy: number }
```

**Implementation:**
- Add to copilot-sdk shared backend: create_frozen_twin_router(scorer)
- On freeze: snapshot current accuracy and centroid state
- On GET: return frozen state vs current live state
- Mount in S2P (main.py) and Purchasing (main.py)
- The gap IS the compounding proof: "the live system kept learning, the frozen one didn't"

**Tests:** +6 BE (freeze, get, gap calculation, mount verification)
**Effort:** 1d

---

### F-DEMO-05: Trading Regime Analytics (1 spec)
**Specs served:** TRD-02
**Repo:** copilot-sdk (apps/trading/)

**What the demo needs:**
- GET regime analytics → returns regime data with break markers, local-Hurst, tail-dependence shift

**What exists:**
- PL-TRD-1 (trading_regime_break.json) fixture exists
- Trading has fingerprint/trajectory/conservation — but no regime endpoint

**What's missing:**
- GET /api/self/regime-analytics endpoint

**Design:**
```
GET /api/self/regime-analytics
Response: {
  current_regime: string,        // "normal" | "volatile" | "trending"
  regime_history: Array<{
    regime: string,
    start_decision: number,
    end_decision: number?,
    break_detected: boolean,
    break_confidence: number?,
    local_hurst: number?,        // persistence measure
    tail_dependence: number?     // extreme co-movement
  }>,
  autonomy_band: {
    current_width: number,       // narrower during volatile regime
    normal_width: number
  }
}
```

**Implementation:**
- Compute regime from decision sequence (rolling volatility of accuracy)
- Detect break points (CUSUM or simple threshold on rolling window)
- Narrow the autonomy band during volatile regime (the "throttle" behavior)
- Serve from Trading's context router or new regime_router.py

**Tests:** +5 BE (regime detection, break detection, autonomy narrowing, endpoint shape)
**Effort:** 1.5d

---

### F-DEMO-06: DataOps Rule Lifecycle (1 spec)
**Specs served:** DO-04
**Repo:** copilot-sdk (apps/dataops/)

**What the demo needs:**
- GET rule lifecycle → at least one rule with transition history (promoted → active → demoted with reason)

**What exists:**
- AE (AgentEvolver) infrastructure exists in SDK
- Evolution events endpoint exists on SOC (SOC-03 passes)
- DataOps has ae_router but no rule-lifecycle endpoint

**What's missing:**
- GET /api/self/rule-lifecycle on DataOps

**Design:**
```
GET /api/self/rule-lifecycle
Response: {
  rules: Array<{
    rule_id: string,
    description: string,
    current_status: string,      // "active" | "shadow" | "promoted" | "demoted" | "retired"
    transitions: Array<{
      from_status: string,
      to_status: string,
      reason: string,
      decision_n: number,
      timestamp: string
    }>,
    accuracy_at_promotion: number?,
    accuracy_at_demotion: number?,
    decisions_under_rule: number
  }>
}
```

**Implementation:**
- DataOps needs the rule-lifecycle endpoint wired from the existing AE infrastructure
- This is SC-PORT for DataOps — port the self-computation rule-lifecycle surface from SOC
- Query the variant/evolution ledger and format as lifecycle transitions

**Tests:** +4 BE (lifecycle shape, transitions, status values)
**Effort:** 1d

---

### F-DEMO-07: DataOps K14 Divergence (1 spec)
**Specs served:** DO-05
**Repo:** copilot-sdk (apps/dataops/)

**What the demo needs:**
- Score shows investigation action differs from surface assessment
- The K14 story: "the LLM says approve, investigation says reject"

**What exists:**
- K14 experiment established the blind-spot phenomenon (12% agreement on investigation-dependent decisions)
- PL-DO-5 (dataops_k14_divergence.json) fixture exists
- Investigation infrastructure exists in SDK (investigation.py, investigation_router.py)

**What's missing:**
- An endpoint that returns both surface assessment and investigation assessment for comparison
- Or: score response that includes both assessments

**Design:**
```
GET /api/self/k14-comparison?decision_id={id}
Response: {
  decision_id: string,
  surface_assessment: {
    action: string,
    confidence: number,
    label: "surface"
  },
  investigation_assessment: {
    action: string,
    confidence: number,
    label: "investigation",
    reads_performed: number,
    evidence_found: string[]
  },
  divergent: boolean,           // true when actions differ
  k14_note: string              // "Surface and investigation assessments diverge on this decision"
}
```

**Implementation:**
- Add endpoint to DataOps context_router or new k14_router.py
- For demo: use planted fixture (PL-DO-5) as the comparison data
- The divergence IS the K14 story — show it explicitly

**Tests:** +3 BE (comparison shape, divergence flag, non-divergent case)
**Effort:** 0.5d

---

### F-DEMO-08: S2P Fingerprint (1 spec)
**Specs served:** PLAT-03
**Repo:** s2p-copilot

**What the demo needs:**
- GET /api/fingerprint on S2P (port 8002) returns factor data
- PLAT-03 iterates all 5 ports — 4 work, S2P doesn't

**What exists:**
- SDK copilots all have /api/fingerprint via the shared scoring_router
- S2P mounts the SDK conservation_router but may not mount scoring_router
- S2P has /api/s2p/insight/fingerprint but not /api/fingerprint

**What's missing:**
- Alias route: GET /api/fingerprint on S2P → delegates to /api/s2p/insight/fingerprint

**Design:**
```python
# s2p-copilot/backend/app/routers/compat_router.py (or add to existing)
@router.get("/api/fingerprint")
async def fingerprint_alias():
    return await s2p_fingerprint_handler()  # delegate to existing
```

**Implementation:**
- Add a 3-line alias route in S2P's compat_router or main.py
- Verify response shape matches what PLAT-03 asserts (factors array)

**Tests:** +1 BE (alias returns same data as /api/s2p/insight/fingerprint)
**Effort:** 0.25d

---

### F-DEMO-09: Investigation Trace Surface (2 specs)
**Specs served:** TRD-04, PUR-06
**Repo:** copilot-sdk

**What the demos need:**
- TRD-04 (position-alone): Investigation found the real risk (position exposure) that the surface didn't see
- PUR-06 (demand-limit): Investigation found that demand wasn't the limit, the real bottleneck was something else

**What exists:**
- Investigation infrastructure (investigation.py, investigation_router.py) — FROZEN, working
- K14 experiment characterized the investigation mechanism

**What's missing:**
- A user-facing surface that shows the investigation trace for a given decision
- GET /api/self/investigation-trace?decision_id={id}

**Design:**
```
GET /api/self/investigation-trace?decision_id={id}
Response: {
  decision_id: string,
  investigation_budget: number,   // reads allocated
  reads_performed: Array<{
    source: string,               // which graph node/edge was read
    value: number | string,
    contribution: number,         // how much this read changed the score
    order: number                 // 1st, 2nd, 3rd read
  }>,
  surface_action: string,        // what the LLM/surface would have said
  investigation_action: string,  // what investigation concluded
  divergent: boolean,
  key_finding: string            // "Position exposure (read #3) changed action from APPROVE to HOLD"
}
```

**Implementation:**
- Add to copilot-sdk shared backend: create_investigation_trace_router(scorer)
- Queries the investigation log for the given decision
- Mount in Trading and Purchasing
- For demo: planted decisions (from preseed) should have investigation traces

**Tests:** +5 BE (trace shape, reads array, divergence, key finding)
**Effort:** 1.5d

---

### F-DEMO-10: Entrant vs Incumbent (1 spec)
**Specs served:** TRD-05
**Repo:** copilot-sdk (apps/trading/)

**What the demo needs:**
- Cold-start (entrant) vs warm geometry (incumbent) — show that the incumbent has an advantage from accumulated decisions

**What exists:**
- Fingerprint endpoint shows earned weights (TRD-06 passes)
- Conservation status shows verified_count

**What's missing:**
- GET /api/self/entrant-comparison endpoint

**Design:**
```
GET /api/self/entrant-comparison
Response: {
  incumbent: {
    verified_decisions: number,
    accuracy: number,
    iks: number,
    centroid_stability: number,   // low drift = mature geometry
    warm_start_advantage_pp: number  // accuracy - baseline (the gap)
  },
  entrant: {
    verified_decisions: 0,
    accuracy: number,            // baseline accuracy (Day 0)
    iks: 0,
    centroid_stability: 0,
    warm_start_advantage_pp: 0
  },
  gap: {
    accuracy_pp: number,         // incumbent.accuracy - entrant.accuracy
    decisions_to_parity: number, // estimated decisions for entrant to catch up
    note: string                 // "Incumbent has +X.Xpp from Y verified decisions"
  }
}
```

**Implementation:**
- Compute from scorer state: current accuracy vs baseline (Day 0)
- The "entrant" is always the Day 0 baseline — no second scorer needed
- decisions_to_parity estimated from the learning curve shape

**Tests:** +3 BE (comparison shape, gap calculation, Day 0 baseline)
**Effort:** 0.5d

---

### F-DEMO-11: Cross-Graph Kill Chain Discovery (1 spec)
**Specs served:** SOC-05
**Repo:** gen-ai-roi-demo-v4-v50

**What the demo needs:**
- Two individually-benign alerts that together constitute a kill chain
- The system discovers the relationship via cross-graph attention

**What exists:**
- Alert analysis infrastructure
- Graph store with alert/entity relationships
- Cross-system correlation patterns (from DataOps OE features)

**What's missing:**
- POST /api/alert/cross-correlate endpoint
- Kill chain detection logic

**Design:**
```
POST /api/alert/cross-correlate
Request: { alert_ids: [string, string] }
Response: {
  correlation: {
    alert_1: { alert_id, action_alone: string, severity_alone: string },
    alert_2: { alert_id, action_alone: string, severity_alone: string },
    combined_severity: string,     // "critical" (elevated from "low" + "low")
    kill_chain_pattern: string,    // "credential_access → lateral_movement"
    shared_entities: string[],     // entities linking the two alerts
    recommendation: string,        // "Escalate as coordinated attack"
    confidence: number
  },
  discovery_note: string           // "Individually benign. Together: kill chain."
}
```

**Implementation:**
- Query graph for shared entities between two alerts
- Pattern matching: known kill chain sequences (credential_access → lateral_movement, etc.)
- Severity elevation when pattern matches
- Plant two fixture alerts that match a known kill chain

**Tests:** +5 BE (correlation, severity elevation, pattern match, no-match case)
**Effort:** 2d

---

### F-DEMO-12: RL-CTRL Production Scoring (1 spec)
**Specs served:** S2P-07
**Repo:** copilot-sdk + s2p-copilot

**What the demo needs:**
- Investigation budget strip: system spends 1 read on easy decisions, 3 on hard ones
- The RL controller is in production, not just experimental

**What exists:**
- RL-CTRL-2C experiment: +6.8pp S2P, +6.5pp SOC at fewer reads, safe at λ=0
- Adaptive budget controller code in experiments
- Investigation infrastructure

**What's missing:**
- Production wiring: the adaptive budget controller needs to be in the scoring path, not just experiments
- GET /api/self/investigation-budget endpoint showing the allocation

**Design:**
```
GET /api/self/investigation-budget
Response: {
  controller: "adaptive",        // "adaptive" | "uniform"
  stats: {
    mean_reads_easy: number,     // e.g., 1.2
    mean_reads_hard: number,     // e.g., 2.8
    total_reads_saved: number,   // vs uniform 2.0
    quality_delta_pp: number     // +6.8pp over uniform
  },
  recent_decisions: Array<{
    decision_id: string,
    difficulty: string,          // "easy" | "medium" | "hard"
    reads_allocated: number,
    reads_used: number
  }>
}
```

**Implementation:**
- Extract the adaptive budget controller from experiments to SDK production code
- Wire into the scoring path (before investigation.py's read loop)
- Add endpoint to serve allocation stats
- This is GAP-D from the MAP

**Tests:** +8 BE (controller selection, easy/hard allocation, stats, endpoint shape)
**Effort:** 3d

---

### F-DEMO-13: Concepts Endpoint (3 specs)
**Specs served:** PLAT-01, PLAT-05, MACH-05
**Repo:** copilot-sdk

**What the demos need:**
- PLAT-01 (Four Clocks): Retrieve the "Four Clocks" positioning frame content
- PLAT-05 (Two Questions): Retrieve the K14 "two questions" caption
- MACH-05 (Retraction List): Retrieve the list of withdrawn claims

**What exists:** Nothing — these are narrative/positioning content, not computed data

**Design:**
```
GET /api/platform/concepts/{concept_id}
Response: {
  concept_id: string,
  title: string,
  version: string,
  content: object              // concept-specific structured content
}

Concepts:
  "four-clocks" → { clocks: [
    { name: "State Clock", measures: "What exists now", worth: "Operating cost" },
    { name: "Event Clock", measures: "What just happened", worth: "Operating cost" },
    { name: "Decision Clock", measures: "What was learned", worth: "Capital investment" },
    { name: "Insight Clock", measures: "What was discovered", worth: "Capital investment" }
  ], divider: "THE COMPOUNDING DIVIDE" }

  "two-questions" → { questions: [
    { question: "Does the surface tell you?", label: "Surface", k14_agreement: "~86%" },
    { question: "Does investigation change the answer?", label: "Investigation", k14_agreement: "~12% (surface) vs ~76% (geometry)" }
  ], note: "K14: The questions that separate surface from investigation." }

  "retraction-list" → { retractions: [
    { claim: "+28pp with RL in scorer", status: "WITHDRAWN", reason: "EXP-RL-SCORER: 3 strategies, none beat uniform η", date: "2026-04" },
    { claim: "AE accelerates d²/dt²", status: "HYPOTHESIS", reason: "EXP-AE-SECONDDERIV not yet run", date: "2026-05" },
    ...
  ] }
```

**Implementation:**
- Simple key-value store with structured content
- Loaded from a JSON fixture file (data/concepts.json)
- One router, one endpoint, one fixture file
- Content is version-controlled and API-accessible (useful for Loom scripts too)

**Tests:** +3 BE (each concept returns correct shape)
**Effort:** 0.5d

---

### F-DEMO-14: DI Features (2 specs)
**Specs served:** DO-07, DO-08
**Repo:** copilot-sdk (apps/dataops/)

**What the demos need:**
- DO-07 (what-to-buy): Self-computation recommends the next data source to acquire, ranked by ROI
- DO-08 (ask-person): Natural language query with quality-aware response

**What exists:**
- DI-8 (Acquisition Advisor) shipped: real catalog, ROI-ranked, free-first (MAP: CLOSED/PASS, v0.7.62)
- DI-3 (NL Query Engine / Prompt Integrator) shipped: Jaccard+Levenshtein join (MAP: DI-PROMPT-INTEGRATOR CLOSED/PASS, v0.7.62)

**Wait — these are already built.** The MAP shows:
- R27 DI-PROMPT-INTEGRATOR: ✅ CLOSED/PASS (v0.7.62)
- R30 DI-ACQUISITION-ADVISOR: ✅ CLOSED/PASS (v0.7.62)

**What's missing:**
The endpoints exist but may not be mounted in the DataOps app, or the spec is probing the wrong path.

**Action:**
- Verify the DI endpoints are mounted in DataOps main.py
- If not mounted: mount them
- If mounted but different path: fix the spec's probe URL

**Tests:** 0 new (already have tests from R27/R30)
**Effort:** 0.25d (mount verification + spec URL fix)

---

## Part 2: Build Sequence

### Priority order (by specs unlocked per day of effort)

| Priority | Feature | Specs | Effort | Specs/day |
|---|---|---|---|---|
| 1 | F-DEMO-14 (DI mount check) | DO-07, DO-08 | 0.25d | 8.0 |
| 2 | F-DEMO-08 (S2P fingerprint alias) | PLAT-03 | 0.25d | 4.0 |
| 3 | F-DEMO-03 (S2P score fixtures) | S2P-01/02/03 | 0.5d | 6.0 |
| 4 | F-DEMO-13 (concepts endpoint) | PLAT-01/05, MACH-05 | 0.5d | 6.0 |
| 5 | F-DEMO-07 (K14 divergence) | DO-05 | 0.5d | 2.0 |
| 6 | F-DEMO-10 (entrant comparison) | TRD-05 | 0.5d | 2.0 |
| 7 | F-DEMO-06 (rule lifecycle) | DO-04 | 1d | 1.0 |
| 8 | F-DEMO-04 (frozen twin) | S2P-09, PUR-05 | 1d | 2.0 |
| 9 | F-DEMO-02 (checkpoint/rollback) | SOC-10 | 1d | 1.0 |
| 10 | F-DEMO-01 (SOC analyze contract) | SOC-02/06/09, MACH-01/02/03 | 1.5d | 4.0 |
| 11 | F-DEMO-05 (regime analytics) | TRD-02 | 1.5d | 0.7 |
| 12 | F-DEMO-09 (investigation trace) | TRD-04, PUR-06 | 1.5d | 1.3 |
| 13 | F-DEMO-11 (kill chain) | SOC-05 | 2d | 0.5 |
| 14 | F-DEMO-12 (RL-CTRL production) | S2P-07 | 3d | 0.3 |

### Parallel execution plan (3-4 repos, no file overlap)

**Batch 1 (Day 1): Quick wins — 9 specs in 1 day**

| Prompt | Repo | Features | Specs | Effort |
|---|---|---|---|---|
| DI-MOUNT | SDK (DataOps app) | F-DEMO-14 | DO-07, DO-08 | 0.25d |
| S2P-COMPAT | S2P | F-DEMO-03 + F-DEMO-08 | S2P-01/02/03, PLAT-03 | 0.5d |
| CONCEPTS | SDK (platform router) | F-DEMO-13 | PLAT-01/05, MACH-05 | 0.5d |

**After Batch 1: 30 + 9 = 39 pass**

**Batch 2 (Day 2-3): Medium features — 8 specs in 2 days**

| Prompt | Repo | Features | Specs | Effort |
|---|---|---|---|---|
| SOC-ANALYZE | SOC | F-DEMO-01 | SOC-02/06/09, MACH-01/02/03 | 1.5d |
| SDK-SURFACES | SDK | F-DEMO-04 + F-DEMO-06 + F-DEMO-07 + F-DEMO-10 | S2P-09, PUR-05, DO-04, DO-05, TRD-05 | 2d |

**After Batch 2: 39 + 11 = 50 pass (+ SOC-10 pending)**

**Batch 3 (Day 4-5): SOC + Trading — 3 specs in 2.5 days**

| Prompt | Repo | Features | Specs | Effort |
|---|---|---|---|---|
| SOC-CHECKPOINT | SOC | F-DEMO-02 | SOC-10 | 1d |
| TRD-REGIME | SDK (Trading app) | F-DEMO-05 | TRD-02 | 1.5d |

**After Batch 3: 50 + 3 = 53 pass**

**Batch 4 (Day 6-9): Big features — 3 specs in ~5 days**

| Prompt | Repo | Features | Specs | Effort |
|---|---|---|---|---|
| SOC-KILLCHAIN | SOC | F-DEMO-11 | SOC-05 | 2d |
| INVESTIGATION | SDK | F-DEMO-09 | TRD-04, PUR-06 | 1.5d |

**After Batch 4: 53 + 3 = 56 pass (all ROADMAP except S2P-07)**

**Batch 5 (Day 10-12): RL-CTRL production — final spec**

| Prompt | Repo | Features | Specs | Effort |
|---|---|---|---|---|
| RL-CTRL-PROD | SDK + S2P | F-DEMO-12 | S2P-07 | 3d |

**After Batch 5: 56 pass / 0 skip / 0 fail**

---

## Part 3: Summary

| Batch | Day | Specs pass | Cumulative | Key milestone |
|---|---|---|---|---|
| 1 | 1 | +9 | 39/56 | Quick wins: DI mount, S2P compat, concepts |
| 2 | 2-3 | +11 | 50/56 | SOC analyze contract, SDK surfaces |
| 3 | 4-5 | +3 | 53/56 | Checkpoint/rollback, regime analytics |
| 4 | 6-9 | +3 | 56/56* | Kill chain, investigation trace |
| 5 | 10-12 | — | 56/56 | RL-CTRL production (if S2P-07 counted) |

*56/56 achievable by Day 9 if S2P-07 is excluded (RL-CTRL is the biggest feature).
Including S2P-07: Day 12.

**Total effort: ~12 working days for all 14 features, ~55 new backend tests.**
**Critical discovery: DO-07 and DO-08 may already be built (DI features shipped in v0.7.62) — verify mount first.**
