# Platform Validation Plan v2.0

Status: Unified validation contract — AGE migration + architectural changes + PI tiers + 7 design goals + JM completion
Supersedes: `age_migration_validation_plan_v1_1.md`
Authority: JM v2.7 + Product Integrity v3.0 + MAP v5.154
Date: 2026-07-29
Review status: Code-first gap review performed 2026-07-29; execution remains gated
by the known gaps and pass criteria in Section 11.
Scope: All 5 copilots, all 5 repos — validates AGE migration AND all
architectural changes made during the AGE unification effort

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

The 13 original validation areas are preserved and extended. 6 new areas
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
  validation result. J6 artifact reachability and Phase-6 proof remain open;
  the current E3 scanner also reports one SDK production finding (Section 11).

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
| WIRE-01 | Frontend wiring | Area 6 (PW) + new Area 14 | Not built |
| AGE-SMOKE | Full AGE suite | Area 7 (AGE suite) | Tests exist, runner needed |
| LANG-01 | Kitchen language | T0 scanner | Script needed |
| PROV-01 | Provenance on surfaces | Area 6 (PW) + new Area 15 | Not built |

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

(Preserved from v1.1 — see canonical_v_soc_note_v1_4.md for full details)

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

## 5. Validation Areas

### Area 1: Domain isolation (Goal 4, Goal 5, Goal 6 | T2)

(Preserved from v1.1 — 10 SOC isolation tests + 5-domain assertions)

**PI integration:** This area implements the cross-domain isolation proof
required by AGE-SMOKE (T2). The 5-domain browser assertion maps to WIRE-01.

### Area 2: V_soc stability and implementation parity (Goal 3, Goal 4 | T2)

(Preserved from v1.1 — census baseline, event ledger, store parity)

**PI integration:** Implements CONS-01 conservation formula verification.
V_soc deliverable 3 (runner NO-GO on unrecorded V change) is built here.

### Area 3: Full platform launch (Goal 1, Goal 2, Goal 6 | T2)

(Preserved from v1.1 — 5 copilots start, health, AGE+soc_graph, stop)

**PI integration:** Commercial endpoint smoke (PI §3.2). Every copilot
health response must include backend=age, graph=soc_graph, domain=<correct>.

### Area 4: Cross-domain write safety and contention (Goal 4, Goal 5 | T2)

(Preserved from v1.1 — phase_cycle_gate, SOC API cycle, contention)

### Area 5: Performance and indexes (T2)

(Preserved from v1.1 — p95 ≤ 193ms, index existence, EXPLAIN plans)

### Area 6: Playwright coverage (Goal 3, Goal 4 | T3)

(Preserved from v1.1 — all 5 PW suites, Trading --workers=1)

**PI integration:** Implements WIRE-01 (backend→frontend wiring), empty-tab
check (PI §4.3), demo timing (PI §5.3), and PROV-01 (provenance on surfaces).

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
```

### Area 10: Recovery, rollback, and flip-back (T2)

(Preserved from v1.1 — CI_ALLOW_SQLITE_FALLBACK, hash preservation)

### Area 11: Data integrity and archive parity (T2)

(Preserved from v1.1 — active+archived=total, orphan/duplicate)

### Area 12: Ungoverned write prevention (Goal 5 | T2)

(Preserved from v1.1 — NULL-domain census, raw-path adversarial)

### Area 13: Behavioral output equivalence (T2)

(Preserved from v1.1 — fixed corpus, SQLite/AGE score comparison)

### Area 14: Frontend wiring verification (NEW — Goal 3 | T2)

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

### Area 15: Innovation claims and substantiation (NEW | T2/T3)

**PI source:** §3.1 comparative tests, §2.3 counterfactual faithfulness,
§2.4 substantiation tiers, §8 FORBIDDEN/CANONICAL

**T2 checks:**
```
□ Innovation comparative tests (8 tests from PI §3.1) — all PASS
□ Counterfactual faithfulness: top factor influences score
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
```

**Prerequisite:** C-0 scaffolding (frozen benchmark, comparative tests,
commercial smoke script) must be built before these checks can run.

### Area 16: FORBIDDEN/CANONICAL Registry Enforcement (NEW | T0/T3)

**PI source:** §8.1 FORBIDDEN, §8.2 CANONICAL, §8.3 Paper consistency

**Architecture-relevant FORBIDDEN entries changed by this session's work:**

| ID | Forbidden | Status after session | Validation check |
|---|---|---|---|
| F-18 | Backend endpoint with no frontend wiring | OPEN — PW not run since B-ADDENDUM | WIRE-01 in Area 14 |
| F-19 | DomainConfig IDs differ from DomainPreset | Need verification | SHAPE-02 in Area 9 |
| F-24 | "Governs all loops" when a loop is ungated | OPEN — L2b prompt-variant ungated | GC-01..GC-05 check |
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

**Governed-compounding checks (GC-01..GC-05, from PI §7.3):**

```
□ GC-01 (T2): Each compounding loop routes through ONE ConservationGate
□ GC-02 (T2): Fail-closed test: gate RED → each loop's promotion BLOCKED
□ GC-03 (T2): Provenance on each loop's I/O (T-A/T-S/T-O/T-R)
□ GC-04 (T3): L3/L4 tier check (situation-analyzer = SOC-only)
□ GC-05 (T3): No claim of L3/L4 in a copilot that hasn't built it
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

### Area 17: Known Architecture Risks (NEW | T1/T2)

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

### Area 18: Substantiation and Day-Zero State (NEW | T2/T3)

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
□ E3 scanner: 0 PRODUCTION forbidden pattern violations
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

### Area 20: Silent fallback removal validation (NEW — Goal 3 | T2/T3)

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

### Area 21: Legacy code removal validation (NEW — Goal 2, Goal 7 | T1)

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

### Area 22: Persistence wiring validation (NEW — Goal 1 | T2)

**What changed:** J6 added a shared scorer persistence coordinator for
`learn()` callers and retained the existing scorer-side fingerprint,
evidence, and checkpoint writes. The shared scoring router no longer owns the
V2 conservation write. This is not yet proof that all four artifacts are
reachable for all five copilots: SOC's bridge currently invokes the
coordinator's conservation path, while SOC's raw profile update does not
execute the generic scorer `learn()` artifact sequence.

**Risk:** New synchronous graph writes on every learn operation add latency.
SOC and S2P bypass the shared router — need separate bridges. Duplicate
evidence receipts possible. V2+legacy checkpoint duplication.

**Validation (per copilot):**

```
□ Conservation snapshot persists after learn (check graph)
□ Fingerprint persists on change, deduplicates on no-change
□ Post-outcome evidence receipt linked to triggering Decision; separately
  verify any copilot-specific pre-outcome receipt
□ Centroid checkpoint created (V2 + legacy documented)
□ Persistence failure does NOT block the learn response
□ Domain is correct in every persisted artifact
□ Cold-start theta_min=inf handled (skipped, not serialized)
□ SOC bridge reaches persistence coordinator
□ S2P receipt cardinality and provenance: pre-outcome and post-outcome
  receipts are intentionally distinct and have distinct machine-readable
  types (not merely different metadata)
□ Latency impact: learn p95 still acceptable
```

**Per-copilot reachability:**
```
□ SOC: triage → _guarded_update → conservation coordinator; separately
  prove whether fingerprint, evidence, and checkpoint writes are reachable
□ S2P: s2p.py → scorer.learn() → persistence coordinator
□ Trading: scoring_router → scorer.learn() → persistence coordinator
□ Purchasing: scoring_router → scorer.learn() → persistence coordinator
□ DataOps: scoring_router → scorer.learn() → persistence coordinator
```

**Static code verification of the 7 design goals.**

**T0 (automated, every commit):**
```
□ E3 scanner: 0 PRODUCTION forbidden pattern violations in all four repos;
  current SDK state fails this until the stale `scorer.py` line allowlist is
  reconciled with the actual construction at `scorer.py:234`
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

---

## 6. Execution Phases

### Phase E-0: C-0 Scaffolding (PI foundation — builds before validation)

| Step | What | PI ref | Effort |
|---|---|---|---|
| E0-1 | Reconcile and run existing `integrity/architecture_scan.py` (T0 invariants) | PI §1.1 | 0.25d |
| E0-2 | Build missing `integrity/shape_check.py` (SHAPE-01, SHAPE-02) | PI §6.2 | 0.5d |
| E0-3 | Use and verify the existing frozen benchmark fixture (seed=42, 400/100 current split); reconcile the plan's stale 500/100 claim | PI §11.3 | 0.25d |
| E0-4 | Run and extend existing `integrity/test_innovation_claims.py`; reconcile its actual thresholds and test names with the eight PI claims | PI §3.1 | 0.5d |
| E0-5 | Run existing `integrity/commercial_smoke.py` against all 5 copilot presets and separately add live endpoint coverage | PI §3.2 | 0.5d |
| E0-6 | Wire T0 scanner + E3 scanner into a validation runner; fail on the current SDK allowlist mismatch | PI §6.1 | 0.5d |
| E0-7 | Build missing `integrity/path_trigger.sh` (T1/T2 path-filter) | PI §6 | 0.5d |
| E0-8 | Build missing `integrity/run_all.sh` (full tier suite), or document the supported PowerShell equivalent | PI §6 | 0.5d |

**E0-4 innovation comparative tests (from PI §3.1):**
```
test_accuracy_improves:       acc at 500 > acc at 50 + 0.03
test_dk_weights_improve:      learned DK > uniform on held-out
test_reconvergence_faster:    N2 < N1 after disruption
test_conservation_blocks:     RED status blocks auto-approve
test_iks_monotonic:           IKS at 100 < 300 < 500
test_five_presets:            all 5 copilot presets load and score
test_counterfactual:          top factor change → score change
test_provenance_attached:     evidence surface carries source tag
```

**E0-5 commercial smoke ports (from PI §3.2):**
```
SOC:        8001 — /api/health, /api/alert/analyze, /api/conservation/status
S2P:        8002 — /api/health, /api/score, /api/conservation/status
Trading:    8010 — /api/health, /api/score, /api/conservation/status
Purchasing: 8020 — /api/health, /api/score, /api/conservation/status
DataOps:    8030 — /api/health, /api/score, /api/conservation/status
```

### Phase E-1: Validation Runner + V_soc (Areas 1-5, 7-12)

| Step | What | Area | Effort |
|---|---|---|---|
| E1-1 | Runner scaffold (cross-platform, 3 levels) | §3 runner | 1d |
| E1-2 | Census baseline + store parity + V_soc deliv 3 | Area 2 | 0.5d |
| E1-3 | Domain isolation + NULL census | Areas 1, 12 | 0.5d |
| E1-4 | AGE-gated suite orchestration | Area 7 | 0.5d |
| E1-5 | Per-domain cycles + contention | Area 4 | 0.5d |
| E1-6 | Config negative matrix | Area 9 | 0.5d |
| E1-7 | Destructive safety gates | Area 8 | 0.5d |
| E1-8 | Data integrity + parity | Area 11 | 0.5d |
| E1-9 | 20 pass criteria as assertions | §7 criteria | 0.5d |

### Phase E-2: 5-Domain Proof + Rollback (Areas 3, 10, 13)

| Step | What | Area | Effort |
|---|---|---|---|
| E2-1 | 5-copilot launch/health/stop | Area 3 | 0.5d |
| E2-2 | Score equivalence corpus | Area 13 | 1d |
| E2-3 | Rollback flip-back drill | Area 10 | 0.5d |
| E2-4 | Performance benchmark (p95 gate) | Area 5 | 0.5d |

### Phase E-3: Playwright + Frontend + Architectural Impact (Areas 6, 14, 15, 20-22)

| Step | What | Area | Effort |
|---|---|---|---|
| E3-1 | SOC/S2P drift reconciliation and SDK scanner cleanup (prerequisites; includes stale `scorer.py:230` → `:234` allowlist entry) | — | 2d |
| E3-2 | Start all 5 backends + frontends | Area 3 | 0.5d |
| E3-3 | 503 impact assessment — curl every converted endpoint | Area 20 | 0.5d |
| E3-4 | PW smoke all 5 copilots | Area 6 | 1d |
| E3-5 | Fix 503/wiring issues found | Area 14, 20 | 1-2d |
| E3-6 | WIRE-01 cross-repo check | Area 14 | 0.5d |
| E3-7 | Empty-tab detection | Area 6 (PI §4.3) | 0.5d |
| E3-8 | Legacy removal import verification | Area 21 | 0.5d |
| E3-9 | Persistence wiring live check: artifact-by-artifact, per-copilot, including custom SOC/S2P paths and failure semantics | Area 22 | 1d |
| E3-10 | Innovation claims + FORBIDDEN scan | Area 15, 16 | 0.5d |

### Phase E-4: Comprehensive Report

| Step | What | Effort |
|---|---|---|
| E4-1 | Run comprehensive validation | 0.5d |
| E4-2 | Collect evidence package | 0.5d |
| E4-3 | Operator sign-off | — |

---

## 7. Production-ready pass criteria

(Preserved from v1.1 — all 20 criteria, plus 5 new PI criteria)

1-20: (as in v1.1)

**PI additions:**

21. T0 scanner (E3 + architecture_scan.py) reports zero PRODUCTION violations.
22. T1 shape/config checks pass for all 5 copilots (SHAPE-01, SHAPE-02, CONS-01).
23. Innovation comparative tests (8 from PI §3.1) all PASS.
24. FORBIDDEN registry scan (F-01..F-27) shows zero violations on external surfaces.
25. CANONICAL claims (C-01..C-19) are present and correctly evidenced.
26. All 7 design goals PASS for all 5 copilots with file:line evidence.
27. Governed-compounding checks GC-01..GC-03 PASS (GC-04/05 at T3 only).
28. Day-zero substantiation: no K3 sample value appears as a metric (F-22).
29. Provenance rendering: evidence surfaces carry source tags (PROV-01).
30. Paper consistency: no F-05/F-06/F-08/F-25 phrasings in any paper/blog draft.

**Architectural change criteria (Areas 20-22):**

31. Every converted 503 endpoint: backend returns 503 on failure, valid data on
    success, and frontend handles gracefully (no crash/blank).
32. Zero imports of deleted Neo4jClient in production code.
33. Zero getattr/hasattr/TypeError for Decision methods in production (Rule #72).
34. query_context uses strict domain filtering (no IS NULL branch).
35. Persistence wiring: conservation, fingerprint, evidence, and checkpoint
    each have a passing production reachability test for every copilot that
    claims the artifact, with the correct domain; SOC's custom update path
    must explicitly account for artifacts not reached by generic `learn()`.
36. Persistence failure does not block learn response for any copilot.
37. SOC persistence bridge reaches every artifact it claims to persist, or
    reports the artifact as an explicit known gap; conservation reachability
    alone is not evidence of fingerprint/evidence/checkpoint reachability.
38. S2P pre-outcome and post-outcome receipts are both intentional, linked to
    the correct lifecycle event, and carry distinct machine-readable receipt
    types; do not call this "no duplicate" solely from different metadata.
39. V2 + legacy checkpoint duplication documented and intentional.
40. Cold-start theta_min=inf does not crash AGE serialization.

---

## 8. Parallel execution plan

```
PREREQUISITES (before Phase E):
  ✅ J1-J4 complete (7/7 goals × 5 copilots)
  ⚠️  J6 fixer in review (persistence wiring)
  □  SOC/S2P drift reconciliation (before PW)
  □  Batch commit all repos

PARALLEL SESSIONS:

Session A (SDK repo)          Session B (SOC + CI)           Session C (cross-repo)
E0-1..E0-6 C-0 scaffolding   E2-1 5-copilot launch          E3-1 Drift reconciliation
E1-1..E1-9 Runner + V_soc    E2-2 Score equivalence          E3-3..E3-7 PW + frontend
                              E2-3 Rollback drill
                              E2-4 Performance benchmark

CONVERGENCE:
  E4-1 Comprehensive run (all sessions complete)
  E4-2 Evidence package
  E4-3 Sign-off

AFTER PHASE E:
  Phase 6: TransferPattern, global conservation, cross-copilot proof
  JM v2.8 document update
```

---

## 9. Pre-validation checklist

Before starting any Phase E work:

```
□ All repos committed and pushed
□ All test suites green (SDK 2,341+, Trading 1,236, Purchasing 687,
  DataOps 265, CI 599, SOC 2,196, S2P 1,651 — total ~8,975)
□ J6 fixer reviewed and clean
□ SOC/S2P drift scope known (diagnostic complete)
□ AGE running on WSL2 port 5433
□ graph_config.toml assigns soc_graph to all 5 domains
□ E3 scanner reports 0 PRODUCTION violations (SDK currently has one at
  `copilot_sdk/scoring/scorer.py:234` until its TOML line entry is updated)
□ Rule #72 enforcement tests pass in SDK and S2P
```

---

## 10. Review finding disposition

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

## 11. Code-first gap review (2026-07-29)

This appendix is the current gate state. It supersedes any statement above
that says a validation tool is already built or that all seven goals have
already passed. The review compared this plan with the current protocol,
factory, scorer, enforcement tests, per-copilot startup paths, the JM
completion plan, the AGE addendum, the canonical V_soc note, and the PI v3.0
strategy. The PI v3.0 file is not present at the documented
`copilot-sdk/docs/design/` path; the available copy is under the repository
source snapshot `gen_ai_roi_demo_temp/.../product_integrity_execution_strategy_v3_0.md`.
Execution must pin the authoritative PI document before sign-off.

### 11.1 Per-area gap register

| Area | Current code-first result | Gap / required gate | PI tier |
|---|---|---|---|
| 1. Domain isolation | Partial | Add mixed-domain AGE tests for CRUD, links, and `query_context`; prove NULL-domain traversal artifacts are excluded by `age_graph_store.py:2548-2570`. | T2 |
| 2. V stability | Blocked | `V_soc=4,862` is provisional. Complete canonical-note deliverables 1-3 (seed/hash pin, `baseline_reset`, and NO-GO runner) before treating the baseline as final; see canonical note `:453-477`. | T1/T2 |
| 3. Launch | Partial | Startup checks exist, but launch acceptance must cover the custom SOC and S2P paths in addition to the three shared-router apps, with graph-reader/scorer state assertions. | T2 |
| 4. Write safety | Partial | `bootstrap_neo4j.py:183-227` still writes Decision nodes through a direct AGE client path. Validate the approved bootstrap exception, domain stamp, no `$`/MERGE violations, and idempotency when bootstrap and seed are both invoked. | T0/T1 |
| 5. Performance | Incomplete | Measure the synchronous J6 writes in `scorer.py:672-729` and establish a p95 budget; include failure logging and concurrent learn contention. | T2 |
| 6. Playwright | Incomplete | Exercise every converted 503 route and its unavailable UI state, not just health/score. Include SOC/S2P custom routes and persistence-failure responses. | T3 |
| 7. AGE-gated suite | Partial | Existing conformance tests cover store methods, but the plan lacks a named live AGE runner for all five domains plus archive/history and J6 artifact assertions. | T2 |
| 8. Destructive safety | Partial | Add explicit tests for strict domain reset/archive boundaries and for legacy NULL-domain records not being deleted or traversed accidentally. | T1/T2 |
| 9. Config | Partial | `graph_config.toml` maps all five production profiles to AGE/soc_graph, while `factory.py:171-192` intentionally permits explicit test/tool backends. Add a negative test distinguishing production from test/migration exceptions; implement missing SHAPE-01/02 runner. | T0/T1 |
| 10. Rollback | Incomplete | Add rollback drills for persistence schema/API changes and for facade/scorer wiring, not only backend flip-back. Verify no partial receipt/checkpoint state is presented as complete. | T2 |
| 11. Integrity/archive | Incomplete | Incorporate AGE addendum retention/history requirements: `get_archived_decisions`, active/history parity, preserved edges/outcomes, reconciliation runner, and 40 zero-discrepancy cycles (`age_shared_graph_migration_v3_22_addendum.md:88-212`). | T1/T2 |
| 12. Ungoverned write | Partial | Static checks must explicitly inventory the bootstrap direct AGE write and every migration/tool exception; Goal 1 cannot be inferred from E3's Decision-MATCH rule alone. | T0/T1 |
| 13. Score equivalence | Partial | Compare current AGE production paths against a fixed corpus for all five domains and account for J6 persistence side effects; the existing integrity tests use in-memory stores (`integrity/test_innovation_claims.py:16-45`). | T2 |
| 14. Frontend wiring | Incomplete | WIRE-01 is listed but not built. Add an endpoint-to-surface inventory, generated/client schema check, and explicit 503/empty/cold-start rendering checks for all five frontends. | T2/T3 |
| 15. Innovation | Partial | Innovation tests exist, but current names/thresholds differ from the plan: the code tests 50→200 and 200→400 (`integrity/test_innovation_claims.py:76-150`), not the stated 50→500 +.03. Reconcile claims and add PI §2.3 counterfactual faithfulness assertions. | T2/T3 |
| 16. Forbidden/canonical | Incomplete | The E3 scanner and architecture scanner cover different subsets. Add executable F/C registry coverage and scan IDs for all required external surfaces; do not claim zero until the SDK scanner is clean. | T0/T3 |
| 17. Architecture/commercial | Incomplete | Most risks are checklist prose. Convert graph bypass, auto-approve, stale factor counts, empty tabs, IKS, conservation RED, and provenance into executable pass/fail checks. | T2/T3 |
| 18. Substantiation/day-zero | Partial | Sample rejection and restart/counterfactual tests exist (`integrity/test_product_truth.py:28-104`), but the PI §2.6 three-state contract is not proven on all five API/frontend surfaces. | T2/T3 |
| 19. Static goals | Failing | Rule #72 tests exist, but E3 currently reports SDK PRODUCTION=1 at `copilot_sdk/scoring/scorer.py:234`; TOML still allowlists `scorer.py:230` (`age_unification_forbidden_patterns_allowlist.toml:16-23`). Fix/revalidate before E0 passes. | T0/T1 |
| 20. Fallback validation | Partial | The plan inventories the historical conversions, but lacks a machine-readable endpoint matrix proving each failure path returns 503/raise, valid empty stays 200, and each frontend handles it. | T0/T2/T3 |
| 21. Legacy removal | Partial | Neo4jClient class removal and strict `query_context` are present (`gen-ai.../db/neo4j.py:1-56`, `ci-platform/.../age_graph_store.py:2548-2570`), but add explicit import, adapter-signature, and NULL-artifact traversal tests. | T0/T2 |
| 22. Persistence wiring | Failing as a universal claim | Shared scorer persistence is present (`scorer.py:672-729`), but SOC's bridge only proves conservation reachability (`triage.py:2115-2129`); S2P's pre-outcome receipt has `metadata.phase` but not the required machine-readable `receipt_type` (`s2p.py:1333-1337`). The three-test J6 file (`tests/scoring/test_j6_persistence.py:52-136`) does not prove all requested per-copilot behaviors. | T1/T2/T3 |

### 11.2 Cross-cutting answers

**A — Missing areas:** archive/history reconciliation and the 40-cycle
zero-discrepancy gate from the AGE addendum; authoritative V_soc seed/hash and
baseline-reset governance; explicit SOC/S2P custom-path artifact reachability;
PI authority-path pinning; and an executable endpoint/empty-state matrix for
the 503 conversions.

**B — Missing pass criteria:** (1) E3 clean in each repository, including the
stale SDK allowlist correction; (2) strict `query_context` excludes a
NULL-domain neighbor; (3) bootstrap plus seed is idempotent; (4) every J6
artifact has a per-copilot reachability assertion; (5) persistence failure is
observable and does not fabricate success; (6) active/history parity and
archived-edge preservation; (7) S2P pre/post receipt types and lifecycle
links; (8) production-vs-test factory backend negative matrix; and (9) PI
§2.3, §2.6, and §3.3 assertions.

**C — PI gaps:** PI §2.3 requires counterfactual faithfulness tied to the
displayed factor and actual DK trust, not only a score delta; PI §2.6 requires
the three-state day-zero contract on measured surfaces; PI §3.3 requires a
similar-decisions demonstration with explicit similarity inputs and evidence;
PI §4.1 requires the frontend narrative to explain provenance and state
transitions; PI §7.3 requires GC-01 through GC-08, while this plan names only
GC-01 through GC-05. Add those checks and their scan IDs to the runner.

**D — Interaction risks:**

| Interaction | Current verdict | Required validation |
|---|---|---|
| 503 conversion + J6 persistence | Code intentionally logs and continues on artifact-write failure; `scorer.py:696-729` does not turn the primary learn into 503. | Test shared-router, SOC, and S2P learn failures separately; verify no fake artifact is returned and warning telemetry is emitted. |
| Protocol promotion + S2P facade | Pass at the implementation level: `S2PGraphReader.count_verified_decisions` delegates with `domain="s2p"` (`s2p_graph_reader.py:73-77`), and the method is in `GraphStore` (`protocol.py:61-65`). | Add a facade integration assertion against a mixed-domain store. |
| NULL removal + traversal | Strict filtering is implemented in `query_context` (`age_graph_store.py:2558-2560`). | Seed a NULL-domain legacy node and prove it cannot enter a domain-bound context result. |
| Framework params + app copies | SDK methods are optional-domain parameterized; SOC/S2P copies hardcode their domain. This is intentional drift, not identical implementation. | Run framework drift plus a behavior test for all three SDK app domains and both copied frameworks. |
| Bootstrap governed path + seed | Bootstrap checks existing records but uses a direct AGE client write (`bootstrap_neo4j.py:183-227`); no plan gate proves combined bootstrap/seed idempotency. | Run two bootstrap/seed cycles and assert stable Decision IDs/counts and domain stamps. |
| E3 scanner + Rule #72 | Not clean: Rule #72 enforcement exists, but E3 reports one SDK production violation caused by the stale line allowlist. | Correct the allowlist and run both enforcement layers across all four repository scans. |

**E — Ordering risks:** E0 currently describes several already-existing
artifacts as build steps while omitting the missing `shape_check.py`,
`path_trigger.sh`, and `run_all.sh`. First inventory and reconcile tools, then
make E0 a hard gate. Canonical V_soc deliverables must precede E1 baseline
acceptance. J6 reachability and scanner cleanup must precede E3 Playwright and
the final report. Archive/history reconciliation may run in parallel with
frontend work after the protocol/store contract is fixed, but its result must
be included before E4.

**F — Missing scripts:** `integrity/shape_check.py` (0.5 day),
`integrity/path_trigger.sh` (0.5 day), and `integrity/run_all.sh` (0.5 day)
are referenced by E0 but absent. The E1 “runner scaffold” also has no named
implementation (1 day). PI v3.0 references `wire_check.ps1`; no such file was
found in the active SDK repository, so either add it (0.5 day) or explicitly
replace it with a checked-in cross-platform runner. `integrity/architecture_scan.py`,
`integrity/commercial_smoke.py`, `integrity/test_innovation_claims.py`,
`integrity/benchmark_fixture.py`, and `scripts/validate_age_migration.py`
already exist and should be run/reconciled rather than rebuilt.

**G — Behaviors with no demonstrated test:** the current test inventory has no
per-copilot production reachability test for all four J6 artifacts, no test of
the SOC bridge beyond its conservation invocation, no bootstrap-plus-seed
idempotency test, no NULL-domain exclusion assertion for `query_context`, no
40-cycle active/history reconciliation gate, and no complete 503 endpoint to
frontend empty/unavailable-state matrix. `tests/scoring/test_j6_persistence.py:52-136`
covers only shared in-memory artifact behavior and router conservation; it
does not establish those production-path claims. These are test gaps, not
proof that the underlying features are absent.

### 11.3 Required plan changes before execution

1. Treat “all 7 goals PASS” as a target, not current status, until the gates
   in this appendix pass.
2. Correct the SDK SQLite allowlist entry from line 230 to the actual
   construction at `copilot_sdk/scoring/scorer.py:234`, then require all four
   E3 repository scans to report zero PRODUCTION findings.
3. Split Area 22 into artifact × copilot reachability, explicitly accounting
   for SOC's custom raw-profile update and S2P's custom learn/receipt path.
4. Add the AGE addendum archive/history checks and the canonical V_soc
   deliverables to Areas 2, 8, and 11 and to the E1 runner.
5. Add explicit interaction tests for protocol/facade, strict traversal,
   bootstrap/seed idempotency, framework drift, 503 behavior, and J6 failure
   semantics.
6. Replace the E0 “build” wording for existing tools with run/reconcile
   wording, and list the missing scripts and their owners/effort.
7. Pin the authoritative PI v3.0 document location before sign-off and add
   PI §2.3, §2.6, §3.3, §4.1, and all GC-01..GC-08 checks.

Until items 1-7 are complete, the plan is **NEEDS_FURTHER_UPDATES** and is
not an execution-ready Phase-E gate.
