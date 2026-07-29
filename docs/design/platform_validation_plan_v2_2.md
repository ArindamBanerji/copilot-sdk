# Platform Validation Plan v2.2

Status: Execution-ready — unified validation contract for the AGE unification
  platform changes
Supersedes: `age_migration_validation_plan_v2_0.md`, v1.1, v1.0
Filename: `platform_validation_plan_v2_2.md`
Authority: JM v2.7 + Product Integrity v3.0 + MAP v5.154
PI authority: `copilot-sdk/docs/design/product_integrity_execution_strategy_v3_0.md`
  (copy from project repo; pin to this path before E4 sign-off)
Date: 2026-07-29
Scope: All 5 copilots, all 5 repos — validates AGE migration AND all
architectural changes made during the AGE unification effort

**Version history:**
- v2.2: renamed from `age_migration_validation_plan` to `platform_validation_plan`;
  criteria 1-20 inlined (self-contained); §5.1 interaction tests moved before
  areas for readability; cleanup of resolved items
- v2.1: §11.3 items 3,4,5,7 resolved (copilot×artifact matrix, addendum checks,
  interaction tests, GC-06..08, PI §2.3/2.6/3.3/4.1)
- v2.0: scope expanded to full platform; 22 areas, PI integration, 7 design goals,
  code-first gap review
- v1.1: AGE migration only, 13 areas, 20 criteria

## 0. What changed from v1.1

v1.1 validated AGE migration only. v2.0 validates the **full platform state**
after the AGE unification effort, which changed far more than the database
backend:

### 0.1 Scope expansion

The AGE unification effort produced architectural changes across every repo
that affect scoring behavior, error handling, API responses, frontend behavior,
test contracts, and the system's runtime interface. These changes must be
validated together because they interact:

| Change category | What changed | Impact to validate |
|---|---|---|
| **AGE migration** | All 5 copilots on shared soc_graph | Domain isolation, V stability, data integrity |
| **Silent fallback removal** | 36+ fallbacks → 503/raise across SOC, S2P, SDK | Frontend tabs may break, API contracts changed |
| **Runtime interface cleanup** | 76 getattr/TypeError/hasattr removed (Rule #72) | Error paths changed, Protocol enforced |
| **SDK Protocol completion** | 18 direct domain-aware calls, count_verified_decisions promoted | Scoring, conservation, IKS behavior changed |
| **S2P facade** | 52 call sites → S2PGraphReader (11 methods) | S2P error handling, domain enforcement |
| **Legacy code removal** | Neo4jClient deleted (486 lines), NULL-domain compat removed | Import chains, startup behavior |
| **Persistence wiring** | Conservation, fingerprint, evidence, checkpoint writes added | New graph writes on every learn, latency |
| **Framework parameterization** | 5 SDK framework files accept domain | Query behavior when domain is/isn't passed |
| **Scanner enforcement** | AST taint propagation, Rule #72 enforcement tests | CI gate behavior |
| **Bootstrap conversion** | SOC bootstrap → governed AGE write | Startup, seed, idempotency |

### 0.2 Governance integration

Three previously separate governance layers are integrated:

1. **Product Integrity tiers (T0-T3)** — every validation area maps to a PI
   tier. PI scan IDs are referenced where they apply. C-0 scaffolding is built
   as part of this plan.

2. **7 JM design goals** — every validation area verifies one or more goals.
   The goals are the acceptance criteria.

3. **JM completion status** — J-phase tracking and Phase 6 dependencies.

The 13 original validation areas are preserved and extended. 9 new areas
cover the architectural changes and PI-specific checks.

---

## 1. The 7 Design Goals (acceptance criteria for every area)

| # | Goal | Evidence required |
|---|---|---|
| 1 | Every Decision read/write through GraphStore/AGE | No raw psycopg/Neo4j Decision operations in production |
| 2 | Every graph access through GraphConfig | No raw GRAPH_*/NEO4J_* env reads in production paths |
| 3 | No silent substitution on AGE failure | Every graph failure raises or returns explicit error/503 |
| 4 | Every Decision query domain-scoped | Every MATCH (d:Decision) has d.domain = '<copilot>' |
| 5 | Every Decision write stamps domain | Every CREATE/SET Decision includes domain property |
| 6 | One shared graph (soc_graph) | graph_config.toml assigns soc_graph to all 5 domains |
| 7 | All non-unified paths closed | No getattr/TypeError compat, no legacy fallbacks |

**Goal verification is per-copilot.** A goal PASSes only when ALL 5 copilots
(SOC, S2P, Trading, Purchasing, DataOps) satisfy it. Current status (July 29):
  J1-J5 are substantially implemented, but the 7/7 claim is not yet a
  validation result. J6 artifact reachability and Phase-6 proof remain open.

---

## 2. Product Integrity Tier Mapping

Each validation area maps to one or more PI tiers. The tier determines when
the check runs and what gates it.

| PI Tier | Gates | Triggered by | Areas |
|---|---|---|---|
| T0 | Every commit (automated) | Commit/merge | SHAPE-01, CLAIM-01, LANG-01, E3 scanner, Rule #72 |
| T1 | Batch acknowledgment | scoring/evidence/preset/conservation change | SHAPE-02, CONS-01, PROTO-01, Area 9 config |
| T2 | Batch-close | Batch completion | WIRE-01, AGE-SMOKE, Areas 1-5,7-13, innovation tests |
| T3 | Demo-ready / publish | Demo scheduled or paper submission | Area 6 PW, demo storyboard, empty-tab, timing |

### PI Scan ID to Area mapping

| Scan ID | PI Check | Validation Area | Status |
|---|---|---|---|
| SHAPE-01 | Tensor shape match | Area 9 (config) | Script needed |
| SHAPE-02 | Config↔Preset parity | Area 9 (config) | Script needed |
| CONS-01 | Conservation formula | Area 2 (V_soc) | Partially exists |
| PROTO-01 | Protocol coverage | Area 7 (AGE suite) | Conformance tests exist |
| CLAIM-01 | Forbidden claims | T0 scanner | E3 scanner exists |
| WIRE-01 | Frontend wiring | Area 6 (PW) + Area 14 | Not built |
| AGE-SMOKE | Full AGE suite | Area 7 (AGE suite) | Tests exist, runner needed |
| LANG-01 | Kitchen language | T0 scanner | Script needed |
| PROV-01 | Provenance on surfaces | Area 6 (PW) + Area 15 | Not built |

---

## 3. JM Completion Dependencies

### Phases 0-5: IMPLEMENTED, NOT ALL VALIDATED (J1-J4 + J6)

| Phase | Status | Evidence |
|---|---|---|
| J1: Bootstrap + Neo4j disable | ✅ | Governed write, Neo4jClient removed |
| J2: Fallbacks + aggregates | ✅ | 503/raise, domain scoped, NULL-domain removed |
| J3: Framework caller verification | ✅ | All 5 apps use own copies, SDK callers verified |
| J4: Limit + naming + edges | ✅ | get_decision_links limit, KEEP decisions documented |
| J6: Persistence wiring | ⚠️ Partial / in review | The shared scorer coordinates artifacts for `learn()` callers; the SOC bridge currently reaches the conservation coordinator only, and S2P pre-outcome evidence remains a separate receipt path. Per-copilot artifact evidence is still required. |

### Phase 6: NOT STARTED (post-validation)

| Item | Blocks validation? |
|---|---|
| TransferPattern graph persistence | NO — Phase 6, not Phase E |
| Global conservation queries | NO — Phase 6 |
| Cross-copilot traversal proof | NO — Phase 6 |
| write_conservation_status production caller | PARTIAL — shared scorer plus SOC bridge; reachability must be proven per copilot |
| write_fingerprint production caller | PARTIAL — shared scorer `learn()` path; SOC custom path must be proven separately |

### Remaining JM gaps (tracked, not blocking validation)

| Gap | Category | Blocks |
|---|---|---|
| SOC/S2P framework drift | DRIFT | Phase E quality (fix before PW) |
| composite_gate.py domain=None | COMPAT | Nothing — generic SDK internal |
| V counting NULL-status compat | COMPAT | Nothing — intentional migration compat |
| Observation edges (IN_DOMAIN, ABOUT) | PHASE-6 | Phase 6 only |
| Checkpoint edge naming | NAMING | JM v2.8 doc update only |

---

## 4. Canonical V_soc reconciliation

(See canonical_v_soc_note_v1_4.md for full details)

```text
V_soc_baseline = 4,862 (seed v1, accepted decision but PROVISIONAL until
  canonical note deliverables 1-3 are complete)
V_soc(t) = count_verified("soc") at time t
V_soc(t) >= V_soc_baseline
scorer V == store V == census V at every checkpoint
```

The canonical note records deliverables 1 (seed/hash pin), 2 (baseline_reset
event on reseed), and 3 (runner NO-GO on unrecorded V change) as incomplete.
Area 2 must not be marked PASS until all three are independently evidenced.

---

## 5. Interaction Tests (cross-change validation)

These tests validate interactions between architectural changes that could
produce bugs invisible to area-level testing. Each maps to a pass criterion
(41-46).

**INT-1: 503 conversion × J6 persistence**

If `write_conservation_status` or any J6 artifact write fails, the learn
endpoint must still succeed (log-and-continue). Test all three learn paths:
```
□ Shared scoring_router learn with graph write failure → 200 + warning log
□ SOC triage _guarded_update with persistence failure → completes, no 503
□ S2P scorer.learn() with persistence failure → completes, no 503
□ No fake/empty artifact returned on failure — the artifact simply doesn't persist
□ Warning telemetry emitted (structured log with domain, decision_id, exception)
```

**INT-2: Protocol promotion × S2P facade**

`S2PGraphReader.count_verified_decisions` must delegate to the promoted
GraphStore method with `domain="s2p"`:
```
□ S2PGraphReader.count_verified_decisions() calls store.count_verified_decisions("s2p")
□ Against a mixed-domain store (SOC + S2P decisions), returns S2P count only
□ Method is in GraphStore protocol (protocol.py), not just AGE adapter
```

**INT-3: NULL-domain removal × query_context traversal**

Strict domain filtering must exclude NULL-domain legacy nodes:
```
□ Seed a Decision node with domain=NULL into a disposable graph
□ Run query_context with domain='soc'
□ Assert the NULL-domain node does NOT appear in context results
□ Assert domain='soc' nodes DO appear
```

**INT-4: Framework parameterization × SOC/S2P app copies**

SDK framework files are parameterized (optional domain). SOC and S2P copies
hardcode their domain. This is intentional drift, not a bug. Verify:
```
□ SDK framework with domain='trading' → queries scoped to trading
□ SDK framework with domain=None → queries unscoped (generic SDK internal use)
□ SOC framework copy → queries scoped to 'soc' (hardcoded)
□ S2P framework copy → queries scoped to 's2p' (hardcoded)
□ Framework drift test covers behavioral equivalence for scoped queries
```

**INT-5: Bootstrap governed path × seed idempotency**

Bootstrap checks existing records but uses a direct AGE client write:
```
□ Run bootstrap + seed once → N decisions with domain='soc'
□ Run bootstrap + seed again → same N decisions, same IDs, same domain stamps
□ No duplicate nodes, no missing domain stamps
□ bootstrap_neo4j.py:183-227 uses no MERGE, no $ params
```

**INT-6: E3 scanner × Rule #72 enforcement consistency**

Both enforcement layers must pass on the current codebase:
```
□ E3 scanner: PRODUCTION=0 across SDK, CI, SOC, S2P
□ Rule #72 SDK enforcement: 0 violations
□ Rule #72 S2P enforcement: 0 violations
□ No conflict between scanner allowlist and Rule #72 enforcement
```

---

## 6. Validation Areas

### Area 1: Domain isolation (Goal 4, Goal 5, Goal 6 | T2)

(Preserved from v1.1 — 10 SOC isolation tests + 5-domain assertions)

**PI integration:** This area implements the cross-domain isolation proof
required by AGE-SMOKE (T2). The 5-domain browser assertion maps to WIRE-01.

### Area 2: V_soc stability and implementation parity (Goal 3, Goal 4 | T2)

(Preserved from v1.1 — census baseline, event ledger, store parity)

**PI integration:** Implements CONS-01 conservation formula verification.
V_soc deliverable 3 (runner NO-GO on unrecorded V change) is built here.

**v2.1 addition — V_soc deliverables (from canonical_v_soc_note_v1_4.md):**

All three deliverables must pass before Area 2 is PASS:
```
□ Deliverable 1: Seed script versioned and output hashed; baseline
  identity is (4,862, seed_version_hash), not a bare number
□ Deliverable 2: demo.py --reseed and any graph reset emits
  {event: "baseline_reset", v_before: N, v_after: M, date, seed_version}
□ Deliverable 3: Validation runner NO-GOs a V change with no matching
  baseline_reset event (built into E1 runner)
```

**v2.1 addition — AGE addendum archive/history checks:**

From `age_shared_graph_migration_v3_22_addendum.md:88-212`:
```
□ get_archived_decisions returns domain-scoped archived rows
□ Active + archived = source total for each domain
□ Archived decisions preserve edges, outcomes, and properties
□ No active decision silently becomes archived without a recorded event
```

### Area 3: Full platform launch (Goal 1, Goal 2, Goal 6 | T2)

(Preserved from v1.1 — 5 copilots start, health, AGE+soc_graph, stop)

**PI integration:** Commercial endpoint smoke (PI §3.2). Every copilot
health response must include backend=age, graph=soc_graph, domain=<correct>.

### Area 4: Cross-domain write safety and contention (Goal 4, Goal 5 | T2)

(Preserved from v1.1 — phase_cycle_gate, SOC API cycle, contention)

### Area 5: Performance and indexes (T2)

(Preserved from v1.1 — p95 ≤ 193ms, index existence, EXPLAIN plans)

**v2.1 addition:** Measure J6 synchronous persistence writes
(`scorer.py:672-729`) separately. Establish a p95 budget for the learn
path including persistence. Include concurrent learn contention.

### Area 6: Playwright coverage (Goal 3, Goal 4 | T3)

(Preserved from v1.1 — all 5 PW suites, Trading --workers=1)

**PI integration:** Implements WIRE-01 (backend→frontend wiring), empty-tab
check (PI §4.3), demo timing (PI §5.3), PROV-01 (provenance on surfaces),
and PI §4.1 (frontend narrative — each tab tells its story with provenance
and state transitions).

**Pre-PW checklist (run before PW suites):**
```
□ All 5 backends started and healthy
□ All 5 frontends built and serving
□ curl each /api/health — 200 with AGE
□ curl each /api/fingerprint — valid response
□ curl each /api/conservation/status — valid response
□ No 503 on any primary endpoint
```

**503 risk assessment:** This session converted 36+ silent fallbacks to 503.
Any frontend tab that expected fallback data will now show an error. PW tests
will surface these. Fix the frontend, not the backend.

### Area 7: AGE-gated test suite (Goal 1 | T2)

(Preserved from v1.1 — protocol conformance, projection, migration tests)

**PI integration:** Implements AGE-SMOKE scan. PROTO-01 protocol coverage
verified by conformance tests.

### Area 8: Destructive test safety (T2)

(Preserved from v1.1 — TEST_DESTRUCTIVE_AGE, disposable graph)

**v2.1 addition — domain reset/archive boundary tests:**
```
□ Domain reset clears only the specified domain's data
□ Archive operation moves only specified domain's decisions
□ Legacy NULL-domain records are NOT deleted or traversed accidentally
□ Seed a NULL-domain node, run domain-bound archive, confirm NULL node untouched
```

**v2.1 addition — 40-cycle active/history reconciliation gate:**

From AGE addendum:
```
□ Run 40 score/learn/archive cycles per domain
□ After each cycle: active + archived = expected total
□ Zero discrepancy across all 40 cycles
□ Edge/outcome preservation verified at cycles 1, 10, 20, 40
```

### Area 9: Configuration completeness (Goal 2 | T1)

(Preserved from v1.1 — AGE-positive startup, fail-closed, negative matrix)

**PI integration:** Implements SHAPE-01 tensor shape match and SHAPE-02
config↔preset parity. The configuration matrix tests GraphConfig enforcement.

**Additional T1 checks:**
```
□ SHAPE-01: grep scanner confirms tensor dimensions match PD docs
□ SHAPE-02: validate_against_preset() == [] for all 5 copilots
□ CONS-01: conservation formula matches math_synopsis_v18.md
□ GraphStore bypass: zero sqlite3.connect outside migration/test
□ Production-vs-test factory backend negative matrix: factory.py creates
  AGE store for production profile, permits SQLite/InMemory only for
  explicitly test/tool profiles
```

### Area 10: Recovery, rollback, and flip-back (T2)

(Preserved from v1.1 — CI_ALLOW_SQLITE_FALLBACK, hash preservation)

**v2.1 addition:** Rollback drills must also verify persistence schema:
```
□ After flip-back to SQLite, no partial J6 artifact (receipt, checkpoint)
  is presented as complete
□ After AGE restore, J6 artifacts written pre-rollback are still present
□ S2P facade degrades gracefully under SQLite fallback
```

### Area 11: Data integrity and archive parity (T2)

(Preserved from v1.1 — active+archived=total, orphan/duplicate)

**v2.1 addition — AGE addendum requirements:**

From `age_shared_graph_migration_v3_22_addendum.md:88-212`:
```
□ get_archived_decisions(domain) returns correct archived set
□ Active + archived == source total, per domain and union
□ Archived decisions preserve: DECIDED_ON edge, HAS_OUTCOME edge,
  HAS_CENTROID_CHECKPOINT edge, all node properties
□ Reconciliation runner compares AGE and SQLite at archive boundary
□ 40 zero-discrepancy cycles (see Area 8)
```

### Area 12: Ungoverned write prevention (Goal 5 | T2)

(Preserved from v1.1 — NULL-domain census, raw-path adversarial)

**v2.1 addition — approved exceptions inventory:**
```
Approved direct AGE write exceptions (must be explicitly listed):
  1. bootstrap_neo4j.py:183-227 — SOC bootstrap, domain='soc' stamped,
     idempotent (checks existing), no MERGE/$ violations
  2. Migration module (copilot_sdk/migrate/) — Rule #58 exemption
  3. Seed scripts (copilot_sdk/seed/) — domain-stamped

All other direct AGE Decision writes are FORBIDDEN. E3 scanner must
catch any new ones. Goal 1 is not inferred from E3 alone — the
inventory above is the explicit approval list.
```

### Area 13: Behavioral output equivalence (T2)

(Preserved from v1.1 — fixed corpus, SQLite/AGE score comparison)

**v2.1 addition:** Corpus must cover all 5 domains and account for J6
persistence side effects (new graph writes don't alter score output).

### Area 14: Frontend wiring verification (Goal 3 | T2)

**PI source:** WIRE-01 (PI §4A)

For each copilot, verify:
```
□ Every backend endpoint has a frontend consumer
□ TypeScript interfaces match Pydantic response models
□ No hardcoded fixture data where live backend data should be used
□ 503 responses handled gracefully (error state, not crash)
□ Factor polarity rendered correctly
□ Evidence surfaces carry provenance/source tags
```

Run: manual cross-repo check + Playwright assertions.

Pass: zero unconnected endpoints, zero type mismatches, zero fixture-as-live.

### Area 15: Innovation claims and substantiation (T2/T3)

**PI source:** §3.1 comparative tests, §2.3 counterfactual faithfulness,
§2.4 substantiation tiers, §8 FORBIDDEN/CANONICAL

**T2 checks:**
```
□ Innovation comparative tests (8 tests from PI §3.1) — all PASS
□ Counterfactual faithfulness (PI §2.3): changing the top DK-weighted
  factor changes the score; the displayed factor matches the actual
  DK trust weight, not a stale/hardcoded rank
□ Similar decisions (PI §3.3): similar-decisions endpoint returns
  decisions with explicit similarity inputs and verifiable evidence;
  similarity is by a specifiable function, not cosine-on-raw-factors
□ Provenance rendering: evidence surfaces carry source tags
□ Substantiation tiers: every surfaced value tier-tagged
□ ClaimRegistry migration guard holds
```

**T3 checks:**
```
□ FORBIDDEN scan (PI §8.1): zero violations
□ CANONICAL claims (PI §8.2): all present and evidenced
□ Scenario classes: LIVE/NEAR/ARCH labels on every scenario
□ Demo-truth: learning enabled where shown learning
□ Naming: no "RL" label on centroid learning (F-25)
□ Cross-copilot: no shared learned state claim (F-26)
□ Frontend narrative (PI §4.1): each tab explains provenance and
  state transitions; the story is readable without a presenter
```

**Prerequisite:** C-0 scaffolding (frozen benchmark, comparative tests,
commercial smoke script) must be built before these checks can run.

### Area 16: FORBIDDEN/CANONICAL Registry Enforcement (T0/T3)

**PI source:** §8.1 FORBIDDEN, §8.2 CANONICAL, §8.3 Paper consistency

**Architecture-relevant FORBIDDEN entries changed by this session's work:**

| ID | Forbidden | Status after session | Validation check |
|---|---|---|---|
| F-18 | Backend endpoint with no frontend wiring | OPEN — PW not run since B-ADDENDUM | WIRE-01 in Area 14 |
| F-19 | DomainConfig IDs differ from DomainPreset | Need verification | SHAPE-02 in Area 9 |
| F-24 | "Governs all loops" when a loop is ungated | OPEN — L2b prompt-variant ungated | GC-01..GC-08 check |
| F-25 | Calling learning mechanism "RL" | Check all surfaces | T3 naming scan |
| F-26 | Claiming shared cross-copilot learned state | Check all surfaces | T3 cross-copilot scan |
| F-27 | Scenario without LIVE/NEAR/ARCH label | Check all surfaces | T3 scenario scan |

**CANONICAL claims that must be verifiable after migration:**

| ID | Claim | Evidence in code | Validation |
|---|---|---|---|
| C-01 | "N verified decisions from YOUR team" | GraphStore count, IKS | Area 2 V_soc |
| C-03 | "Conservation PROVES automation is safe" | α·q·V ≥ θ_min | Area 2 CONS-01 |
| C-06 | "Same engine, 5 domains" | 5 presets, CompoundingScorer | Area 3 launch |
| C-07 | "When your expert leaves, 15,000 decisions stay" | Persistence test | J6 persistence wiring |
| C-10 | "Every decision traceable — graph-persisted audit chain" | Audit hash, edges | Area 11 integrity |
| C-17 | "One conservation law governs every compounding loop" | §7.3 GC checks | **SCOPED until C-GOV** |
| C-18 | "No reward function for judgment" | Centroid learning | T3 naming scan |

**Governed-compounding checks (GC-01..GC-08, from PI §7.3):**

```
□ GC-01 (T2): Each compounding loop routes through ONE ConservationGate
□ GC-02 (T2): Fail-closed test: gate RED → each loop's promotion BLOCKED
□ GC-03 (T2): Provenance on each loop's I/O (T-A/T-S/T-O/T-R)
□ GC-04 (T3): L3/L4 tier check (situation-analyzer = SOC-only)
□ GC-05 (T3): No claim of L3/L4 in a copilot that hasn't built it
□ GC-06 (T3): Primary mechanism NOT called "RL" on any surface (F-25);
  bandit components (ConservationBoundedThompson) named accurately
□ GC-07 (T3): No claim of shared cross-copilot learned judgment state
  (F-26); "signals transfer" is approved, "judgment transfers" is not
□ GC-08 (T3): SOC learning is disabled by default (soc/config.py:66);
  a demo beat showing learning must enable it and demonstrably change
  a later score — otherwise the beat is F-27 (implying LIVE when not)
```

**Paper consistency pre-scan (PI §8.3):**
```bash
cd copilot-sdk/docs/design
grep -n "traverses the graph\|graph traversal at inference" \
  cga_arxiv_short_v7_6.md jm_paper_draft_v9.md ci_blog_v15.md
grep -n "always re-converge\|always faster" \
  cga_arxiv_short_v7_6.md math_synopsis_v18.md
grep -n "production-validated" \
  cga_arxiv_short_v7_6.md jm_paper_draft_v9.md
grep -n "reinforcement learning\|RL" \
  cga_arxiv_short_v7_6.md jm_paper_draft_v9.md ci_blog_v15.md
```

### Area 17: Known Architecture Risks (T1/T2)

**PI source:** §9.1 Architecture Risks, §9.2 Commercial Risks, §9.3 Narrative Risks

**Architecture risks changed by this session's migration work:**

| Risk | Symptom | Detection | Current status |
|---|---|---|---|
| GraphStore bypass | raw sqlite3 in production | T0 scan | ✅ Closed — Rule #58, E3 scanner |
| Conservation formula drift | θ_min computed differently | T1 CONS-01 | Need verification |
| Tensor shape drift | MAP says one shape, code another | T1 SHAPE-01/02 | Trading (5,4,10) already diverged from MAP |
| Auto-approve without gate | conservation check missing | T1 scope | Need per-copilot check |
| Cross-artifact contradiction | Design doc says MERGE | T1 cross-doc | ✅ Closed — MERGE forbidden (Rule #50) |
| Stale factor counts in tests | Smoke asserts wrong D | T1 SHAPE-02 | Need verification |
| Backend-only feature | Endpoint works, demo empty | T2 WIRE-01 | OPEN — PW not run |
| Empty tabs | Tab renders, no data | T3 empty-tab | OPEN — PW not run |

**Commercial risks relevant to migration:**

| Risk | Symptom | Detection | Current status |
|---|---|---|---|
| Fixture as measured | Unlabeled hardcoded number | T1 provenance | Need per-copilot check |
| Empty trajectory | IKS = 0 after preseed | T2 smoke | Need live check |
| Conservation always RED | θ_min too high | T2 endpoint | Need live check |
| Explainability theater | Displayed factor doesn't affect score | T2 counterfactual | Need benchmark (C-0) |

**Narrative risks relevant to migration:**

| Risk | Symptom | Detection | Current status |
|---|---|---|---|
| Black box scoring | Score without WHY | T3 narrative | Need per-copilot check |
| Empty tabs | Tab renders, no data | T3 empty-tab | OPEN — 503 changes may cause |
| Wrong language | "inventory" in Purchasing | T0 LANG-01 | Need scanner |
| No compounding story | Trajectory flat | T3 visual | Need live check |
| Stale provenance | "learned" tag on fixture | T2 provenance | Need per-copilot check |

### Area 18: Substantiation and Day-Zero State (T2/T3)

**PI source:** §2.4 Substantiation Tiers, §2.5 Generated-Data Taxonomy,
§2.6 Day-Zero Substantiation State

**The 3-state contract (per measurement-gated surface):**
```
state := INSTRUMENT_VALIDATED (real_t==0 and real_c==0)  # day zero
       | ACCUMULATING          (real_t<K or real_c<K)
       | MEASURED              (both ≥ K)                 # magnitude appears
K = 30 (default until floor-power calibrates)
```

**T2 enforcement tests (identical shape on every copilot):**
```
□ Only `sample` cohorts → magnitude IS null, state != MEASURED (F-22)
□ Magnitude query filters provenance (excludes 'sample' AND 'oracle') (F-22/F-23)
□ real ≥K both arms → MEASURED, magnitude from real only
□ Instrument panel present at EVERY state (T-O)
```

**v2.1 addition — per-copilot day-zero verification (PI §2.6):**
```
□ SOC: conservation status surface shows INSTRUMENT_VALIDATED on fresh tenant
□ S2P: evidence panel shows instrument, no fabricated penalty_ratio magnitude
□ Trading: trust radar shows instrument, no fabricated DK magnitude
□ Purchasing: par dashboard shows instrument, no fabricated par value (F-22)
□ DataOps: insight surface shows instrument, no fabricated pipeline score
```

**Generated-data taxonomy (K1-K4):**
```
K1: Oracle-generated test data (test-only, never surfaced — F-23)
K2: Model-generated operational data (scored, but provenance-tagged)
K3: Archetype demo/fixture data (label 'sample', exclude from metrics — F-22)
K4: Scraped/external real data (legitimate context, provenance-tagged)
```

**This session's impact:** V_soc baseline is synthetic seed data (K3).
The canonical_v_soc_note_v1_4.md documents this and gates the baseline on
deliverable 3 (runner NO-GO on unrecorded V change). All K3 data in the
demo must be labeled, and no K3 value may appear as a measured metric.

### Area 19: Design goal enforcement (Goals 1-7 | T0/T1)

**Static code verification of the 7 design goals.**

**T0 (automated, every commit):**
```
□ E3 scanner: 0 PRODUCTION forbidden pattern violations in all repos
  (✅ SDK allowlist corrected scorer.py:230→234, PRODUCTION=0)
□ Rule #72 enforcement: 0 getattr/TypeError for Decision methods
□ CLAIM-01: no forbidden claims in production code
□ LANG-01: no forbidden terms in Purchasing
```

**T1 (batch acknowledgment):**
```
□ Goal 1: grep for raw Decision CREATE/MATCH outside GraphStore
□ Goal 2: grep for raw GRAPH_*/NEO4J_* env reads
□ Goal 3: grep for except blocks returning empty/zero on graph failure
□ Goal 4: grep for MATCH (d:Decision) without domain predicate
□ Goal 5: grep for Decision CREATE without domain property
□ Goal 7: Rule #72 + E3 scanner clean
```

**Existing tools:**
- E3 scanner (scan_forbidden_patterns.py): covers Goals 4, 5, partial 1
- Rule #72 enforcement (test_rule72_sdk_enforcement.py, test_rule72_enforcement.py): covers Goal 7
- Framework drift test: covers SOC/S2P drift

### Area 20: Silent fallback removal validation (Goal 3 | T2/T3)

**What changed:** 36+ silent fallbacks across SOC, S2P, and SDK converted
to 503/raise. Every endpoint that previously returned synthetic/zero/default
data on graph failure now returns an error.

**Risk:** Frontend tabs that consumed fallback data will show errors or crash.
API consumers that expected 200 with empty data will get 503.

**Validation:**

For each converted endpoint, verify:
```
□ Backend returns 503 on graph failure (not empty/zero)
□ Backend returns valid data on graph success (not broken by the change)
□ Frontend handles 503 gracefully (error state, not crash/blank)
□ No regression in existing test assertions
```

**Inventory of converted endpoints (must validate each):**

SOC (26 conversions):
```
factors.py: travel, asset, campaign, pattern, compute (5 raise)
iks.py: trust, quality, delta (3 raise)
framework_router.py: convergence, OLS, flywheel, Pass1 (4 → 503)
evolution.py: deployments (1 → 503)
soc.py: threat landscape (1 → 503)
metrics.py: evolution, trends, economics, MTTD, MTTR, FPR (6 → 503)
learning_health.py: red-day, conservation, baseline, precision (4 raise)
variant_generator.py: TypeError removal (1)
```

S2P (52 call site migration):
```
All 52 call sites now go through S2PGraphReader facade.
GraphUnavailableError replaces silent None returns.
```

SDK (18 Protocol completion sites):
```
scorer.py: count_verified_decisions, conservation counts, verified reads
conservation_utils.py: domain-scoped counts, no retry
scoring_router.py: direct calls, no getattr fallback
self_computation_router.py: direct calls
iks_service.py: direct call
measurement_state.py: direct call
nl_query.py: no unscoped retry
enrichment.py: direct call, propagate failure
```

**PW tests needed (per copilot):**
```
□ SOC: Alert Triage tab with AGE down → error message, not zeros
□ SOC: Runtime Evolution tab → error message, not empty charts
□ S2P: Evidence tab with AGE down → error, not blank
□ Trading: Analysis tab → error, not stale data
□ Purchasing: Performance tab → error, not fake GREEN
□ DataOps: Insight tab → error, not empty
```

### Area 21: Legacy code removal validation (Goal 2, Goal 7 | T1)

**What changed:** Neo4jClient class deleted (486 lines), NULL-domain
compatibility removed from query_context, 76 runtime interface detection
sites removed.

**Risk:** Import chains broken, test doubles incomplete, query behavior
changed for NULL-domain nodes.

**Validation:**
```
□ No import of Neo4jClient in any production code (grep)
□ No import of Neo4jClient in any test that isn't explicitly testing removal
□ query_context strict domain filtering (no IS NULL branch)
□ All test doubles complete (Rule #63) — no monkeypatch to compensate
□ Rule #72 enforcement tests pass in SDK and S2P (0 violations)
□ No getattr/hasattr for Decision methods in production code
□ No except TypeError around Decision method calls in production
□ NULL-domain traversal exclusion: seed a NULL-domain Decision node,
  run query_context with domain='soc', confirm NULL node excluded
```

**Files removed/changed that need import verification:**
```
SOC: backend/app/db/neo4j.py (Neo4jClient class removed)
CI: ci_platform/graph/age_graph_store.py (NULL-domain removed)
SDK: 10 files (getattr/TypeError replaced with direct calls)
S2P: 18 files (hasattr/getattr/TypeError removed via facade)
Trading: 3 files (TypeError removed)
Purchasing: 5 files (TypeError removed)
```

### Area 22: Persistence wiring validation (Goal 1 | T2)

**What changed:** J6 added a shared scorer persistence coordinator for
`learn()` callers and retained the existing scorer-side fingerprint,
evidence, and checkpoint writes. The shared scoring router no longer owns the
V2 conservation write.

**Risk:** New synchronous graph writes on every learn operation add latency.
SOC and S2P bypass the shared router — need separate bridges. Duplicate
evidence receipts possible. V2+legacy checkpoint duplication.

**v2.1 — Copilot × artifact reachability matrix:**

| Artifact | Trading | Purchasing | DataOps | S2P | SOC |
|---|---|---|---|---|---|
| Conservation snapshot | ✅ scorer.learn() | ✅ scorer.learn() | ✅ scorer.learn() | ✅ scorer.learn() | ⚠️ SOC bridge (conservation only) |
| Fingerprint | ✅ scorer.learn() | ✅ scorer.learn() | ✅ scorer.learn() | ✅ scorer.learn() | ❌ NOT PROVEN — SOC bridge does not call fingerprint |
| Evidence receipt | ✅ scorer.learn() | ✅ scorer.learn() | ✅ scorer.learn() | ⚠️ Custom pre-outcome receipt + scorer post-outcome | ❌ NOT PROVEN — SOC bridge does not call evidence |
| Centroid checkpoint | ✅ scorer.learn() | ✅ scorer.learn() | ✅ scorer.learn() | ✅ scorer.learn() | ❌ NOT PROVEN — SOC uses raw profile scorer |

**SOC gap:** SOC's triage path calls `_guarded_update` on the raw profile
scorer, then the SOC bridge invokes `_persist_learning_artifacts` which
currently reaches the conservation coordinator. Fingerprint, evidence,
and checkpoint writes go through `scorer.learn()` which SOC does NOT call.
Options: (a) extend the SOC bridge to call all four, (b) document SOC as
conservation-only and accept the gap, (c) refactor SOC to call scorer.learn().

**S2P gap:** S2P calls `scorer.learn()` (full artifact path) BUT also has
a custom pre-outcome evidence receipt at `s2p.py:1310-1364` with invoice/
supplier context. The pre-outcome receipt has `metadata.phase` but not
a machine-readable `receipt_type` field. Both receipts are intentional but
must be distinguished by type, not just metadata content.

**Validation (per copilot — must prove each cell in the matrix):**
```
□ Conservation snapshot persists after learn (check graph) — all 5
□ Fingerprint persists on change — Trading/Purchasing/DataOps/S2P
□ SOC fingerprint: explicitly proven OR documented as known gap
□ Evidence receipt linked to triggering Decision — Trading/Purchasing/DataOps
□ S2P: pre-outcome AND post-outcome receipts present, distinct receipt_type
□ SOC evidence: explicitly proven OR documented as known gap
□ Centroid checkpoint created (V2 + legacy) — Trading/Purchasing/DataOps/S2P
□ SOC checkpoint: explicitly proven OR documented as known gap
□ Persistence failure does NOT block the learn response — all 5
□ Domain is correct in every persisted artifact — all 5
□ Cold-start theta_min=inf handled (skipped, not serialized)
□ Latency impact: learn p95 still acceptable with persistence
```

---

## 7. Execution Phases

### Phase E-0: C-0 Scaffolding (PI foundation — builds before validation)

| Step | What | PI ref | Effort |
|---|---|---|---|
| E0-1 | Reconcile and run existing `integrity/architecture_scan.py` | PI §1.1 | 0.25d |
| E0-2 | Build missing `integrity/shape_check.py` (SHAPE-01, SHAPE-02) | PI §6.2 | 0.5d |
| E0-3 | Verify existing frozen benchmark fixture (seed=42, current split); reconcile plan's stale 500/100 claim | PI §11.3 | 0.25d |
| E0-4 | Run and extend existing `integrity/test_innovation_claims.py`; reconcile thresholds with PI §3.1 | PI §3.1 | 0.5d |
| E0-5 | Run existing `integrity/commercial_smoke.py`; add live endpoint coverage | PI §3.2 | 0.5d |
| E0-6 | Wire T0+E3 scanners into validation runner | PI §6.1 | 0.5d |
| E0-7 | Build missing `integrity/path_trigger.sh` or PowerShell equivalent | PI §6 | 0.5d |
| E0-8 | Build missing `integrity/run_all.sh` or PowerShell equivalent | PI §6 | 0.5d |

### Phase E-1: Validation Runner + V_soc (Areas 1-5, 7-12)

| Step | What | Area | Effort |
|---|---|---|---|
| E1-1 | Runner scaffold (cross-platform, 3 levels) | runner design | 1d |
| E1-2 | Census baseline + store parity + V_soc deliverables 1-3 | Area 2 | 0.5d |
| E1-3 | Domain isolation + NULL census + interaction INT-3 | Areas 1, 12 | 0.5d |
| E1-4 | AGE-gated suite orchestration | Area 7 | 0.5d |
| E1-5 | Per-domain cycles + contention + interaction INT-5 | Area 4 | 0.5d |
| E1-6 | Config negative matrix + production/test factory gate | Area 9 | 0.5d |
| E1-7 | Destructive safety + domain boundary + 40-cycle gate | Area 8 | 0.5d |
| E1-8 | Data integrity + archive parity + AGE addendum checks | Area 11 | 0.5d |
| E1-9 | Pass criteria 1-20 + interaction INT-6 | §8 criteria | 0.5d |

### Phase E-2: 5-Domain Proof + Rollback (Areas 3, 10, 13)

| Step | What | Area | Effort |
|---|---|---|---|
| E2-1 | 5-copilot launch/health/stop | Area 3 | 0.5d |
| E2-2 | Score equivalence corpus (5 domains, J6 side-effect neutral) | Area 13 | 1d |
| E2-3 | Rollback flip-back + persistence schema drill | Area 10 | 0.5d |
| E2-4 | Performance benchmark (p95 gate + J6 write budget) | Area 5 | 0.5d |

### Phase E-3: PW + Frontend + Architectural Impact (Areas 6, 14, 15, 20-22)

| Step | What | Area | Effort |
|---|---|---|---|
| E3-1 | SOC/S2P drift reconciliation (prerequisite) | — | 2d |
| E3-2 | Start all 5 backends + frontends | Area 3 | 0.5d |
| E3-3 | 503 impact assessment + interaction INT-1 | Area 20 | 0.5d |
| E3-4 | PW smoke all 5 copilots | Area 6 | 1d |
| E3-5 | Fix 503/wiring issues found | Area 14, 20 | 1-2d |
| E3-6 | WIRE-01 cross-repo check | Area 14 | 0.5d |
| E3-7 | Empty-tab detection + PI §4.1 narrative | Area 6 | 0.5d |
| E3-8 | Legacy removal verification + interaction INT-3 | Area 21 | 0.5d |
| E3-9 | Persistence wiring: copilot × artifact matrix + INT-1/INT-2 | Area 22 | 1d |
| E3-10 | Innovation claims + FORBIDDEN/CANONICAL + GC-01..08 | Areas 15, 16 | 0.5d |
| E3-11 | Day-zero per-copilot verification | Area 18 | 0.5d |

### Phase E-4: Comprehensive Report

| Step | What | Effort |
|---|---|---|
| E4-1 | Run comprehensive validation | 0.5d |
| E4-2 | Collect evidence package | 0.5d |
| E4-3 | Pin PI v3.0 at documented path | 0.25d |
| E4-4 | Operator sign-off | — |

---

## 8. Production-ready pass criteria

All criteria below must pass in one comprehensive report:

**Core criteria (from v1.1):**

1. Five health endpoints return 200 and identify AGE plus `soc_graph`.
2. Census has zero NULL-domain Decisions and no unknown domains.
3. `census_baseline` recorded at run start; every later V satisfies
   `V_census >= census_baseline`, delta equals event ledger.
4. `V_census == store.count_verified("soc")` at every checkpoint.
5. Non-SOC activity produces zero SOC V increase.
6. All 10 SOC isolation tests pass with zero skips.
7. Four non-SOC 40-cycle gates and real SOC API cycle pass.
8. Same-domain contention increments V exactly once per successful
   verification, no lost update, no torn read, no 500.
9. Five-domain concurrency has zero cross-domain Decision, Outcome,
   receipt, category, or count leakage.
10. Every known raw writer rejects or stamps domain; NULL-domain
    count remains zero after adversarial attempts.
11. Active/archive/verified/correct counts, IDs, and topology match SQLite.
12. Fixed score samples match SQLite action, confidence, probabilities,
    factors, and category mapping within stated tolerances.
13. Domain and archived indexes exist; p95 ≤ 193ms for 250 SOC requests;
    error count is zero.
14. All required AGE tests pass with no unexpected skips; pending feature
    tests separately reported.
15. All five post-flip Playwright suites pass; Trading uses `--workers=1`;
    no foreign data renders.
16. Configuration negatives fail closed; AGE-positive processes do not
    open SQLite.
17. Destructive tests cannot target `soc_graph`; disposable cleanup succeeds.
18. With explicit `CI_ALLOW_SQLITE_FALLBACK=1`, one AGE-serving copilot
    can flip reads to SQLite during forced AGE failure, then restore AGE.
19. Source SQLite hashes/counts remain unchanged through migration and rollback.
20. Evidence report retained with redacted credentials and operator sign-off.

**PI additions:**

21. T0 scanner (E3 + architecture_scan.py) reports zero PRODUCTION violations
    across SDK, CI, SOC, and S2P.
22. T1 shape/config checks pass for all 5 copilots (SHAPE-01, SHAPE-02, CONS-01).
23. Innovation comparative tests (8 from PI §3.1) all PASS with reconciled thresholds.
24. FORBIDDEN registry scan (F-01..F-27) shows zero violations on external surfaces.
25. CANONICAL claims (C-01..C-19) are present and correctly evidenced.
26. All 7 design goals PASS for all 5 copilots with file:line evidence.
27. Governed-compounding checks GC-01..GC-03 PASS at T2; GC-04..GC-08 PASS at T3.
28. Day-zero substantiation: no K3 sample value appears as a metric (F-22),
    per-copilot verification (Area 18).
29. Provenance rendering: evidence surfaces carry source tags (PROV-01).
30. Paper consistency: no F-05/F-06/F-08/F-25 phrasings in any paper/blog draft.

**Architectural change criteria (Areas 20-22):**

31. Every converted 503 endpoint: backend returns 503 on failure, valid data on
    success, and frontend handles gracefully (no crash/blank).
32. Zero imports of deleted Neo4jClient in production code.
33. Zero getattr/hasattr/TypeError for Decision methods in production (Rule #72).
34. query_context uses strict domain filtering (no IS NULL branch);
    NULL-domain traversal exclusion test passes (INT-3).
35. Persistence wiring: copilot × artifact matrix (Area 22) shows each claimed
    artifact reachable with correct domain; unclaimed artifacts documented.
36. Persistence failure does not block learn response for any copilot (INT-1).
37. SOC persistence bridge: each artifact either proven reachable or explicitly
    documented as a known gap with remediation plan.
38. S2P pre-outcome and post-outcome receipts carry distinct machine-readable
    `receipt_type` values; both linked to correct lifecycle event.
39. V2 + legacy checkpoint duplication documented and intentional.
40. Cold-start theta_min=inf does not crash AGE serialization.

**Interaction criteria (§5.1):**

41. INT-1: J6 persistence failure does not propagate 503 on any learn path.
42. INT-2: S2P facade delegates count_verified_decisions with domain="s2p".
43. INT-3: NULL-domain node excluded from domain-bound query_context.
44. INT-4: Framework drift test covers SDK parameterized + SOC/S2P hardcoded.
45. INT-5: Bootstrap + seed is idempotent (two cycles, same IDs/counts).
46. INT-6: E3 scanner and Rule #72 both clean across all repos.

**V_soc governance criteria:**

47. V_soc deliverable 1: seed script versioned and output hashed.
48. V_soc deliverable 2: reseed emits baseline_reset ledger event.
49. V_soc deliverable 3: runner NO-GOs unrecorded V change.
50. 40-cycle active/history reconciliation gate: zero discrepancy.

---

## 9. Parallel execution plan

```
PREREQUISITES (before Phase E):
  ✅ J1-J4 complete
  ✅ J6 persistence wiring committed
  ✅ E3 scanner PRODUCTION=0 (allowlist corrected)
  ✅ Mypy clean (ConservationMetrics TypedDict)
  □  SOC/S2P drift reconciliation (before PW)

PARALLEL SESSIONS:

Session A (SDK repo)          Session B (SOC + CI)           Session C (cross-repo)
E0-1..E0-8 C-0 scaffolding   E2-1 5-copilot launch          E3-1 Drift reconciliation
E1-1..E1-9 Runner + V_soc    E2-2 Score equivalence          E3-3..E3-11 PW + frontend
                              E2-3 Rollback drill               + architectural impact
                              E2-4 Performance benchmark

CONVERGENCE:
  E4-1 Comprehensive run (all sessions complete)
  E4-2 Evidence package
  E4-3 Pin PI v3.0
  E4-4 Sign-off

AFTER PHASE E:
  Phase 6: TransferPattern, global conservation, cross-copilot proof
  JM v2.8 document update
```

---

## 10. Pre-validation checklist

Before starting any Phase E work:

```
□ All repos committed and pushed
□ All test suites green (SDK ~2,342, Trading 1,236, Purchasing 687,
  DataOps 265, CI 599, SOC 2,195, S2P 1,651 — total ~8,975)
□ J6 persistence wiring committed and mypy clean
□ SOC/S2P drift scope known (diagnostic complete)
□ AGE running on WSL2 port 5433
□ graph_config.toml assigns soc_graph to all 5 domains
□ E3 scanner reports 0 PRODUCTION violations
  (✅ SDK allowlist corrected scorer.py:230→234)
□ Rule #72 enforcement tests pass in SDK and S2P
```

---

## 11. Review finding disposition

(Preserved from v1.1 — 12 findings resolved, plus session findings)

**Session findings (July 28-29):**

13. J6 review found SOC bypasses shared persistence path — fixed by scorer
    coordinator + SOC bridge.
14. J6 review found S2P duplicate evidence receipts — resolved by receipt
    type tagging.
15. J6 review found V2+legacy checkpoint duplication — documented, V2 to
    add edge creation before legacy removal.
16. J6 review found theta_min=inf on cold start — guarded before AGE write.
17. Neo4jClient class fully removed (486 lines) — no legacy code remains.
18. NULL-domain compatibility removed from query_context.
19. get_decision_links limit enforced globally (not per-query).

---

## 12. Code-first gap review (2026-07-29)

This appendix is the current gate state. The review compared this plan with
the current protocol, factory, scorer, enforcement tests, per-copilot startup
paths, the JM completion plan, the AGE addendum, the canonical V_soc note,
and the PI v3.0 strategy.

### 11.1 Per-area gap register

(Preserved from v2.0 — 22-area gap table)

### 11.2 Cross-cutting answers

(Preserved from v2.0 — A through G)

### 11.3 Required plan changes before execution — RESOLUTION STATUS

| # | Requirement | Status | Resolution |
|---|---|---|---|
| 1 | "7/7 PASS" → target, not claim | ✅ v2.0 | §1 updated |
| 2 | Scanner allowlist scorer.py:230→234 | ✅ Manual fix | PRODUCTION=0, committed |
| 3 | Split Area 22 copilot × artifact | ✅ v2.1 | Reachability matrix + SOC/S2P gaps documented |
| 4 | AGE addendum + V_soc deliverables | ✅ v2.1 | Areas 2, 8, 11 updated; criteria 47-50 added |
| 5 | Interaction tests | ✅ v2.1 | §5.1 INT-1..INT-6; criteria 41-46 added |
| 6 | E0 "build" → "run/reconcile" | ✅ v2.0 | E0 table updated |
| 7 | Pin PI + GC-06..08 + PI §2.3/2.6/3.3/4.1 | ✅ v2.1 | PI pinned in header; GC-06..08 in Area 16; §2.3 in Area 15; §2.6 in Area 18; §3.3 in Area 15; §4.1 in Area 6 |

**All 7 items resolved. Plan is execution-ready for Phase E.**
