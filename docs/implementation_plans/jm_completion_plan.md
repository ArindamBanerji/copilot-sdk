# JM v2.7 Completion Plan

Status: fresh code-first diagnostic, 2026-07-28. This plan records current
source behavior, not the claimed state of earlier work.

## 1. Executive summary

The platform has completed most of the shared GraphStore/AGE foundation:

- Protocol-v2 methods exist in the SDK protocol and local/AGE stores.
- GraphConfig/factory wiring is present for the five domains.
- SDK and S2P Rule #72 enforcement is in place.
- Trading, Purchasing, and DataOps seed writers stamp their domains.
- S2P has a domain-bound reader facade.

The fresh recount leaves these actionable gaps:

| Goal | Open | Closed | Current conclusion |
|---|---:|---:|---|
| 1. Governed Decision access | 1 | Listed governed paths | SOC bootstrap still writes directly through `neo4j_client` at `backend/app/services/bootstrap_neo4j.py:193-207` |
| 2. GraphConfig | 1 compatibility path | Active copilot paths | Legacy `Neo4jClient` still reads `NEO4J_*` at `backend/app/db/neo4j.py:56-70`, although startup rejects that backend at `:539-544` |
| 3. No silent substitution | 5 | Most reviewed paths | Convergence defaults and two legacy aggregate fallbacks remain; two AGE count methods intentionally preserve shadow parity |
| 4. Domain-scoped Decision access | 3 | Most reviewed queries | Two legacy aggregate queries are unscoped and AGE context traversal permits NULL-domain nodes |
| 5. Domain-stamped writes | 0 in reviewed seed paths | 3 | Trading, Purchasing, and DataOps seeds stamp their domains |
| 6. One shared `soc_graph` | 0 | Pass | `graph_config.toml` assigns `soc_graph` to all five copilot domains |
| 7. All non-unified paths | Derived | — | Not complete while Goals 1, 3, and 4 remain open; Phase 6 is not started |

Estimated work: 8–13 engineering days, excluding AGE environment wait time.

## 2. Goal-by-goal current state

### Goal 1 — Every Decision read/write through GraphStore/AGE

| Item | Evidence | Status | Fix |
|---|---|---|---|
| SOC bootstrap write | `bootstrap_neo4j.py:193-207` uses `neo4j_client.run_query()` and `CREATE (d:Decision)` directly | OPEN | Route bootstrap through the governed GraphStore/AGE writer, or explicitly make bootstrap a governed migration operation with the same contract and tests |
| SOC bootstrap domain stamp | `bootstrap_neo4j.py:204` stamps `domain: 'soc'` | PASS for stamping, not for governed access | Preserve the stamp during migration |
| S2P scorer store | `s2p-copilot/backend/app/main.py:162-170` constructs the reader from `scorer.graph_store` | PASS | None |
| SDK scorer write | `copilot_sdk/scoring/scorer.py:339` writes through `_graph_store.write_decision()` | PASS | None |

### Goal 2 — Every graph access through GraphConfig

| Item | Evidence | Status | Fix |
|---|---|---|---|
| Trading | `apps/trading/backend/app/main.py:119-127` resolves `GraphConfig.load(DOMAIN)` | PASS | None |
| Purchasing | `apps/purchasing/backend/app/main.py:148-155` resolves `GraphConfig.load(DOMAIN)` | PASS | None |
| DataOps | `apps/dataops/backend/app/main.py:103-112` resolves `GraphConfig.load(DOMAIN)` | PASS | None |
| S2P | `s2p-copilot/backend/app/main.py:115-126` uses `GraphConfig` and `create_graph_store()` | PASS | None |
| SOC legacy client | `gen-ai-roi-demo-v4-v50/backend/app/db/neo4j.py:56-59` reads `NEO4J_URI`, `NEO4J_USER`, and `NEO4J_PASSWORD` | COMPAT OPEN | Remove the unreachable class or make its construction fail before raw environment resolution; startup already rejects non-AGE at `:539-544` |

### Goal 3 — No silent substitution on AGE failure

| Item | Evidence | Status | Fix |
|---|---|---|---|
| Centroid evolution | `framework_router.py:161-171` raises HTTP 503 on query failure/no result | PASS | None |
| Convergence calendar | `framework_router.py:187-203` initializes synthetic defaults; graph-query failure raises at `:224-237`, but missing state can still return defaults | OPEN / documented cold-start | Return an explicit unavailable response when displayed values are not backed by live state |
| Evolution summary/rejection | `evolution.py:735-751` maps graph failures to 503 | PASS | None |
| SOC IKS | `services/iks.py:211-219`, `:235-237`, and `:244-276` raise on AGE failures | PASS | Preserve valid cold-start handling at `:278-288` |
| S2P outcome lookup | `s2p.py:2195-2203` maps `GraphUnavailableError` to 503 | PASS | None |
| Trading count | `compute_helpers.py:245-252` raises `RuntimeError` on missing/failing graph count | PASS | None |
| Purchasing IKS | `routers/iks.py:49-68` maps missing/unavailable graph to 503 | PASS | None |
| DataOps seed/evolution | `main.py:400-405` emits seed warnings; this is seed telemetry, not a graph-query substitute | REVIEWED | Keep warning semantics, but ensure user-facing metrics do not consume zero seed counts as measured data |
| AGE R2 counts | `age_client.py:620-637` and `:639-662` return zero on exceptions | INTENTIONAL COMPAT | Preserve only while shadow parity requires it; label/document the legacy source and add a removal gate |
| Legacy category aggregate | `age_client.py:747-769` returns `{}` on any exception | OPEN | Add domain filtering and raise/return explicit unavailable status |
| Legacy outcome aggregate | `age_client.py:771-805` returns zero-valued metrics for empty/error results | OPEN | Add domain filtering and distinguish valid empty data from AGE failure |

### Goal 4 — Every Decision query domain-scoped

| Item | Evidence | Status | Fix |
|---|---|---|---|
| SOC campaigns | Current queries use `d.domain = 'soc'`, for example `campaigns.py:411-414`, `:1256-1259`, and `:1698-1701` | PASS | None |
| SOC simulation | Decision update queries use `d.domain = 'soc'` at `services/simulation.py:415-417` and `:545-548` | PASS | None |
| SOC reports/services | Benchmarking, cluster history, cross-graph discovery, and reconvergence queries contain the SOC predicate at `benchmarking_report.py:158-161`, `cluster_history.py:136-140`, `cross_graph_discovery.py:646-650`, and `reconvergence_logger.py:122-125` | PASS | None |
| SDK framework copies | SDK functions accept optional domain and inject it into queries, e.g. `audit.py:238-265`, `decision_history.py:25-50`, `provenance.py:292-318`, and `shadow_mode.py:33-103` | PASS, backward-compatible | Callers must pass domain in production |
| SOC framework copy | Hardcoded SOC predicates are present, e.g. `app/framework/audit.py:235-248` and `shadow_mode.py:36-78` | PASS | Intentional drift from SDK copy |
| S2P framework copy | Hardcoded/parameterized S2P predicates are present, e.g. `decision_history.py:40-49`, `provenance.py:312-318`, and `similar_cases_base.py:66-92` | PASS | Intentional drift from SDK copy |
| Legacy category aggregate | `age_client.py:758-760` queries `Decision` by category without a domain predicate | OPEN | Add `WHERE d.domain = 'soc'` or replace the legacy method with a domain-aware GraphStore method |
| Legacy outcome aggregate | `age_client.py:787-795` aggregates all Decisions without a domain predicate | OPEN | Scope to SOC and remove the zero-valued failure response |
| Context traversal | `age_graph_store.py:2539-2561` accepts domain but emits `n.domain IS NULL OR n.domain = ...` at `:2546-2552` | OPEN compatibility | Remove NULL-domain allowance after migration verification, or explicitly classify NULL nodes as non-Decision compatibility data |

### Goal 5 — Every Decision write stamps domain

All three requested SDK seed paths pass:

- Trading: `apps/trading/backend/app/seed_graph.py:183-195`, domain `trading` at `:190`.
- Purchasing: `apps/purchasing/backend/app/seed_graph.py:167-179`, domain `purchasing` at `:174`.
- DataOps: `apps/dataops/backend/app/seed_graph.py:279-291`, domain `dataops` at `:286`.

The SOC bootstrap also stamps `soc` at `bootstrap_neo4j.py:196-205`, but remains an ungoverned write under Goal 1.

### Gap categories

| Category | Count | Items |
|---|---:|---|
| MUST-FIX-GOAL-N | 6 | Bootstrap governed write; convergence fallback; two legacy aggregates; context NULL compatibility; AGE link-limit mismatch |
| DRIFT | 2 | SOC and S2P framework copies intentionally bind domains differently from the generic SDK copies |
| SEED | 0 | Trading, Purchasing, and DataOps seed writers already stamp domains |
| COMPAT | 4 | Legacy Neo4j environment path; two R2 shadow-parity zero returns; NULL-status/outcome V compatibility |
| PHASE-6 | 5 | TransferPattern persistence; global conservation; fingerprint caller; Observation edges; checkpoint edges |
| NAMING | 2 | `append_evidence_receipt`/`write_evidence_receipt`; `link_entity`/`entity_link` |

### Goal 6 — One shared graph

PASS for configuration. `copilot-sdk/graph_config.toml` assigns `graph = "soc_graph"` for SOC, Trading, Purchasing, DataOps, and S2P. S2P’s reader is explicitly bound to the scorer’s canonical store at `s2p-copilot/backend/app/main.py:162-170`.

This is a configuration/static-code result; a live five-domain AGE read proof is a separate Phase-6 gate.

### Goal 7 — All non-unified paths

FAIL by derivation. The remaining bootstrap write, legacy aggregate methods, context NULL compatibility, and missing Phase-6 graph topology are still non-unified paths.

## 3. Execution steps

### Phase J1 — Goal 2 and Goal 5 quick fixes

| What | Repo | Depends | Effort | Tests |
|---|---|---|---:|---|
| Retire or hard-disable the raw `Neo4jClient` environment path | SOC | Confirm all callers use AGE switcher | 0.5–1 day | SOC backend unit suite; import/startup checks |
| Reconfirm all seed writers and bootstrap writers include domain | SDK/SOC | None | 0.5 day | Seed contract and domain-isolation tests |

The three SDK seed files already pass; only bootstrap needs governed-path treatment.

### Phase J2 — Remaining silent fallbacks

| What | Repo | Depends | Effort | Tests |
|---|---|---|---:|---|
| Replace convergence defaults with explicit unavailable state when live graph/state is absent | SOC | Decide cold-start API contract | 1 day | Framework-router contract tests and frontend response tests |
| Scope and harden `count_decisions_by_category()` | CI/SOC | J1 backend selection | 0.5 day | Graph snapshot and domain-isolation tests |
| Scope and harden `compute_outcome_stats()` | CI/SOC | J1 backend selection | 0.5 day | Snapshot/metrics tests, failure-path tests |
| Retain R2 shadow-parity zero behavior only behind documented legacy mode | CI | Shadow comparison policy | 0.5 day | R2 shadow tests and mismatch telemetry tests |

### Phase J3 — Framework and query reconciliation

| What | Repo | Depends | Effort | Tests |
|---|---|---|---:|---|
| Verify every SDK framework caller passes its copilot domain | SDK/apps | None | 1 day | SDK, Trading, Purchasing, DataOps framework tests |
| Keep SOC/S2P copies hardcoded or reconcile them with the SDK domain-parameter contract | SOC/S2P | Caller inventory | 1 day | Framework drift tests |
| Add an AST/contract check for legacy AGE Decision aggregates | CI/SOC | J2 method changes | 0.5 day | Scanner and domain-isolation tests |

### Phase J4 — JM semantic cleanup

| What | Repo | Depends | Effort | Tests |
|---|---|---|---:|---|
| Make AGE `get_decision_links()` accept and enforce `limit` | CI | Protocol already defines limit | 0.5 day | Adapter/store signature and traversal tests |
| Remove `n.domain IS NULL` from `query_context()` after NULL census verification | CI | Verify no active NULL-domain Decisions | 0.5–1 day | Cross-domain traversal tests |
| Decide whether to rename `append_evidence_receipt`→`write_evidence_receipt` and `link_entity`→`entity_link`, or formally ratify aliases | SDK/CI/S2P | Consumer inventory | 1 day | Protocol conformance and compatibility tests |
| Align checkpoint/observation edges with JM vocabulary or document canonical aliases | CI | Phase-6 graph model decision | 1–2 days | Graph topology contract tests |

### Phase J5 — Phase-6 cross-copilot proof

| What | Repo | Depends | Effort | Tests |
|---|---|---|---:|---|
| Persist `TransferPattern` nodes and domain/evolution edges | SDK/CI | J4 vocabulary decision | 2–3 days | AGE topology and idempotency tests |
| Implement graph-native transfer traversal | SDK/CI/S2P/SOC | TransferPattern persistence | 1–2 days | Cross-domain AGE integration tests |
| Implement global conservation and global IKS queries | CI/SOC/SDK | Domain-scoped counts and persisted snapshots | 1–2 days | Five-domain live AGE proof |
| Run pure graph discovery proof with no API stitching or fixtures | All | All preceding J5 items | 1 day | Phase-6 integration/PW suite |

### Phase J6 — Production persistence callers

| What | Repo | Depends | Effort | Tests |
|---|---|---|---:|---|
| Wire `write_conservation_status()` into the authoritative conservation completion path | SDK/SOC/S2P | J2 failure contract | 1 day | Conservation persistence and restart tests |
| Wire `write_fingerprint()` into the factor-quality/fingerprint producer | SDK/SOC/S2P | Protocol naming decision | 1 day | Fingerprint write/read and duplicate tests |
| Verify checkpoint and evidence writes are linked to the triggering Decision | CI/SOC/S2P | J4 topology decision | 1 day | Evidence-chain and checkpoint-edge tests |

## 4. Dependency map

```text
J1 ───────┬──> J2 ───────┬──> J6
          │              │
          └──> J3 ───────┴──> J4 ───> J5
```

- J1 must precede J2 because fallback behavior and raw backend selection cannot be assessed reliably until the active backend is unambiguous.
- J3 can run in parallel with late J2 work.
- J4 depends on the final domain and protocol contracts.
- J5 is strictly downstream of J4.
- J6 can begin after J2 for conservation persistence, but checkpoint/evidence caller work depends on J4.

## 5. Playwright integration

| Risk | Affected behavior | Required verification |
|---|---|---|
| 503 conversion | SOC convergence, evolution, IKS, S2P outcome, Trading state, Purchasing IKS | Assert unavailable/error UI rather than fabricated zero/default values |
| Domain scoping | Framework dashboards, S2P explorer/evidence, performance tabs | Seed at least two domains and assert each tab sees only its domain |
| Bootstrap migration | SOC startup and dashboard counts | Startup contract plus SOC dashboard smoke test |
| Global graph proof | Transfer/global conservation/IKS views | New Phase-6 Playwright tests against live AGE; no fixture/API stitching |
| Edge vocabulary | Evidence and centroid detail panels | Verify linked Decision→Outcome/Receipt/Checkpoint records render correctly |

Before changing any response shape, run the existing backend contract suite and the relevant Playwright groups. The S2P repo specifically requires its Playwright S2P group after backend changes.

## 6. Product integrity gates

| Phase | PI tier | Gate |
|---|---|---|
| J1 | T0 | No raw production backend path; all Decision writes carry domain |
| J2 | T1 | AGE failure is visible; no displayed metric silently becomes zero/default |
| J3 | T1 | AST/domain scanner has no production misses; framework drift is registered |
| J4 | T1/T2 | Protocol/store signatures and graph edge vocabulary are conformance-tested |
| J5 | T2/T3 | Five-domain live AGE traversal, global conservation, and TransferPattern proof |
| J6 | T2 | Persisted conservation/fingerprint/checkpoint evidence survives restart and is attributable |

Required gates for every phase: targeted tests, full affected-repo suite, scanner run, and cross-domain isolation test. Live AGE claims require AGE integration tests rather than SQLite-only evidence.

## 7. JM v2.8 document delta

JM v2.8 should replace the static “current implementation” map with:

1. Protocol-v2 implementation status and exact names (`append_evidence_receipt`, `link_entity`).
2. The GraphConfig/factory and S2P facade architecture.
3. A separate compatibility section for NULL-status/outcome counting and R2 shadow parity.
4. The actual edge vocabulary, including any approved aliases for `HAS_CENTROID_CHECKPOINT` and missing Observation edges.
5. Phase-6 status explicitly marked not started until TransferPattern persistence and live traversal proof ship.
6. A fresh V_soc baseline reference and its synthetic-data qualification from `canonical_v_soc_note_v1_4.md:198-273`.
7. The AGE `get_decision_links(limit)` contract and context-traversal NULL-domain decision.
8. Production caller requirements for conservation and fingerprint persistence.

## Summary

The critical path is `J1 → J2 → J4 → J5`, with J3 parallelizable after the initial backend inventory. The three seed files requested by the diagnostic already pass. The highest-priority newly confirmed code gaps are the SOC bootstrap Decision write, two unscoped legacy AGE aggregates, and NULL-domain traversal compatibility.

### JM §12b Compliance Status

| Artifact | §12b policy | Implementation | Status |
|---|---|---|---|
| Outcome | Fail-closed | `learn()` propagates failure | ✅ Compliant |
| Evidence | Queue/retry | Outbox records + startup drain | ✅ Compliant |
| Conservation | Queue/retry | Outbox records + startup drain | ✅ Compliant |
| Fingerprint | Not specified | Outbox records (recomputable) | ✅ Documented |
| Checkpoint | Not specified | Outbox records (best-effort replay) | ✅ Documented |

### JM §4.2 Edge Topology Status

| Edge | Status | Implementation |
|---|---|---|
| IN_DOMAIN | ✅ | `write_decision` creates edge |
| HAS_FACTOR_VECTOR | ✅ | `write_decision` creates FactorVector node + edge |
| EMITTED_RECEIPT | ✅ | Pre-existing |
| SNAPSHOT_AFTER | ✅ | J6 fixer |
| DERIVED_FROM | ✅ | J6 fixer |
| SUMMARIZES_DOMAIN | ✅ | J6 fixer |
| HAS_OUTCOME | ✅ | Pre-existing |
| ABOUT | ✅ | Pre-existing |

Remaining for Phase 6: Observation edges (`IN_DOMAIN`, `ABOUT`,
`HAS_FACTOR_VECTOR`), TransferPattern edges (`FROM_DOMAIN`, `TO_DOMAIN`,
`DERIVED_FROM`), and cross-copilot traversal proof.
