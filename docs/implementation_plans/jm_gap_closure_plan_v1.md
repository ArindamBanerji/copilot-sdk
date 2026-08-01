# JM Gap Closure Implementation Plan v1

Review basis: JM Implementation Reviews Parts 1A, 1B, 2A, and 2B; the age-unification implementation plan; and `copilot-sdk/CLAUDE.md`. This is an implementation plan only. No source or test files were changed while preparing it.

## §1 EXECUTIVE SUMMARY

The reviews establish 33/47 original non-unified paths closed (70.2%), with 4 P1 and 10 P2 paths remaining. The current architecture is partially implemented: 1/7 design goals are CONFORMANT, 4/7 PARTIAL, and 2/7 GAP; 0/9 JM goals are CONFORMANT, 6/9 PARTIAL, and 3/9 GAP (`copilot-sdk/docs/design/jm_implementation_review_part2b_v1.md:7-17`).

This plan has 8 fixes in 7 phases. Fixes 1 and 5 are the initial independent critical-path changes. Fix 2 is the cross-cutting contract hardening. Fix 3 requires an explicit S2P design decision before coding. Fix 4 depends on the backend invariant from Fix 1. Fix 6 is the final startup invariant after the runtime paths are unified. Fix 8 groups the remaining lower-risk cleanup, with its contract sub-items sequenced after Fix 2. Fix 7 is the final validation gate.

| Measure | Plan |
|---|---:|
| Fixes | 8 |
| Phases | 7 |
| Production files affected | 25 unique files; test files are added/updated within the listed suites |
| Estimated effort | 12–18 engineer-days, including 2–3 days of validation and soak testing |
| Expected closure | 47/47 original paths, subject to the S2P shadow decision and passing negative tests |
| Critical path | Fix 1 + Fix 5 → Fix 2 → Fix 3 → Fix 4 → Fix 6 → Fix 8 → Fix 7 |

The governing constraint is fail-closed AGE behavior: GraphConfig owns graph configuration, Decision reads require a domain, Decision writes stamp a domain, and AGE failures must raise rather than silently selecting SQLite or fixtures (`copilot-sdk/docs/design/age_unification_gaps_v1.md:28-43,804-816`).

## §2 DEPENDENCY MAP

```text
                    ┌──────────────┐
                    │ Fix 1         │ Trading/DataOps no AGE→SQLite
                    └──────┬───────┘
                           │
┌──────────────┐           ▼             ┌──────────────┐
│ Fix 5         │     ┌──────────────┐    │ Fix 2         │
│ legacy link   │────▶│ Fix 3         │───▶│ mandatory     │
│ domain stamp  │     │ S2P reconcile │    │ domain API    │
└──────────────┘     └──────┬───────┘    └──────┬───────┘
                             │                   │
                             ▼                   ▼
                       ┌──────────────┐   ┌──────────────┐
                       │ Fix 4         │   │ Fix 8         │
                       │ DataOps close │   │ cleanup batch │
                       └──────┬───────┘   └──────┬───────┘
                              │                   │
                              └────────┬──────────┘
                                       ▼
                                ┌──────────────┐
                                │ Fix 6         │
                                │ soc_graph     │
                                │ startup gate  │
                                └──────┬───────┘
                                       ▼
                                ┌──────────────┐
                                │ Fix 7         │
                                │ full proof   │
                                └──────────────┘
```

Fixes 1 and 5 can run in parallel. Fix 2 can begin in parallel with Fix 1/5 at the design and test-contract level, but its implementation must land before the domain-sensitive Fix 8 sub-items. Fix 3 is sequential after the S2P decision and should precede Fix 6. Fix 4 may begin after the Fix 1 interface behavior is fixed, but its production fixture removal should be tested against the selected shared store. Fix 8A/8B/8D/8E/8F can run in parallel; Fix 8C (LearningState) and Fix 8G (optional `write_outcome`) depend on Fix 2. Fix 7 is last.

## §3 PHASE 1: CRITICAL PATH — FIX 1

### Fix 1 — Remove Trading/DataOps AGE→SQLite rewrites

1. **Problem.** P1-TRD-1 remains GAP because Trading changes `backend == "age"` to `"sqlite"` before the factory (`copilot-sdk/docs/design/jm_implementation_review_part1b_v1.md:19-28`; `copilot-sdk/apps/trading/backend/app/main.py:119-135`). P2-DOPS-1 remains GAP for the same reason in DataOps (`copilot-sdk/docs/design/jm_implementation_review_part1b_v1.md:90-96`; `copilot-sdk/apps/dataops/backend/app/main.py:103-120`). This defeats Goal 3/JM-8 before an AGE outage can be observed.

2. **Design goals addressed.** Design Goals 1, 2, 3, and 7; JM-1, JM-3, JM-6, and JM-8. It makes the common factory the actual AGE decision point and preserves the factory’s existing raise-on-missing-DSN behavior.

3. **Files to change.**
   - `copilot-sdk/apps/trading/backend/app/main.py:119-135,303-340,357-367`.
   - `copilot-sdk/apps/dataops/backend/app/main.py:103-120,534-552,564-573`.

4. **What changes.** Delete the `if backend == "age": backend = "sqlite"` rewrites. Pass the resolved backend, DSN, graph name, domain, and profile into the active factory. Remove or isolate the generic fallback helper so it cannot be used for a production AGE configuration without an explicit graph name. Ensure the active seed target remains the selected store; if AGE is selected, startup must either seed through the AGE-backed store or fail, never create a SQLite substitute.

5. **What must not change.** Preserve domain names (`trading`, `dataops`), decision ID prefixes, scorer profiles, authorized test-mode SQLite behavior, `DEMO_NO_RESEED`, bundle restore semantics, and the existing explicit demo/test gates. Do not remove valid SQLite use for local/test profiles.

6. **Blast radius.** Trading startup, `FreshScorerProxy`, active graph status, startup restore/seed, execution/journal/context consumers, and CLI-created scorer paths are affected. DataOps startup, scorer creation, bundle/fixture restore, evolution seeding, health reporting, and graph query endpoints are affected. The active wrappers already pass the configured graph and stamp their domains (`copilot-sdk/apps/trading/backend/app/graph_status.py:132-149,342-362`; `copilot-sdk/apps/dataops/backend/app/graph_status.py:127-149,314-334`), so the main risk is changing which store reaches existing consumers.

7. **Tests needed.** Add startup matrix tests for `sqlite`, `age`, and missing/unreachable AGE. Assert `type(app.state.graph_store)` and DSN/graph values. Negative tests must assert that `GRAPH_BACKEND=age` never invokes SQLite construction, missing DSN raises, and an AGE connection failure returns startup failure/503 rather than a usable SQLite scorer. Test fixture seeding into a live AGE store and refusal/explicit handling when AGE is unavailable. Preserve test-profile SQLite startup and demo-mode seeding.

8. **Dependencies.** Factory behavior is already CONFORMANT (`copilot-sdk/docs/design/jm_implementation_review_part1a_v1.md:11-15`; `copilot-sdk/copilot_sdk/graph/factory.py:205-210,257-285`). Fix 6’s universal `soc_graph` invariant follows this change; Fix 4’s DataOps fallback closure depends on the selected store being authoritative. No source dependency blocks implementation.

9. **Verification.** From the repository root:
   - `python -m pytest copilot-sdk/tests copilot-sdk/apps/trading/backend/tests copilot-sdk/apps/dataops/backend/tests -q`.
   - Run Trading and DataOps startup tests with `GRAPH_BACKEND=age`/domain-specific active AGE settings and assert process failure on an unreachable DSN.
   - Run the relevant health/status endpoint tests and inspect that reported backend is AGE, not SQLite.
   - Run the targeted negative test that monkeypatches `create_graph_store` and fails if `backend="sqlite"` is passed after an AGE configuration.

10. **Estimated effort.** 1.5–2.5 engineer-days.

### Fix 5 — Stamp domain on legacy `link_decision_to_entity`

1. **Problem.** The primary Decision node writes are stamped, but the legacy relationship writer’s AGE path accepts an optional domain and its `_link_props` does not include a domain property (`copilot-sdk/docs/design/jm_implementation_review_part2a_v1.md:9-16,§3.2`; `ci-platform/ci_platform/graph/age_graph_store.py:2640-2666,2727-2741`). This is the remaining unstamped write.

2. **Design goals addressed.** Design Goal 5; JM-9. It closes the last write-side domain-stamping gap without changing Decision node identity.

3. **Files to change.** `ci-platform/ci_platform/graph/age_graph_store.py:2640-2666,2727-2741`.

4. **What changes.** Make `domain` required at the public method boundary; validate it with the same domain rules as Decision writes; include `domain: $domain` in the relationship property map or remove the legacy relationship writer if no supported caller remains. Ensure any fallback relationship implementation receives the same domain.

5. **What must not change.** Preserve relationship type, decision/entity identifiers, idempotency, transaction behavior, and existing callers that already provide domain. Do not broaden relationship traversal across domains.

6. **Blast radius.** All AGE relationship-link callers, audit traversal, entity context, and any migration/backfill utility using `link_decision_to_entity` are affected. The protocol and adapter signatures must remain consistent with implementations.

7. **Tests needed.** Write a relationship with `domain="trading"` and assert the edge has that property. Attempt omission and assert `TypeError`/validation failure. Attempt a cross-domain link and assert rejection. Read the relationship through each supported traversal path and assert domain preservation. Run existing AGE store link/idempotency tests.

8. **Dependencies.** Independent of Fix 1; should land before Fix 7. If the method is removed instead, first prove no runtime caller beyond tests with a repository-wide import/call audit.

9. **Verification.** `python -m pytest copilot-sdk/tests -q -k "link_decision or entity"`; run an AGE integration test that creates and reads a linked Decision; run the domain-null census query from §9.

10. **Estimated effort.** 0.5–1 day.

## §4 PHASE 2: PROTOCOL HARDENING — FIX 2

### Fix 2 — Make domain mandatory in protocol reads and domain-sensitive writes

1. **Problem.** Goal 4 and Goal 5 are PARTIAL because the public protocol permits domain omission. `get_decision`, traversal reads, and `query_similar` have optional domains (`copilot-sdk/docs/design/jm_implementation_review_part2a_v1.md:9-16,20-46`; `copilot-sdk/copilot_sdk/graph/protocol.py:40-48,144-161`). AGE and InMemory mirror this optionality (`ci-platform/ci_platform/graph/age_graph_store.py:2015-2027,2668-2718,3074-3109`; `copilot-sdk/copilot_sdk/graph/memory_store.py:1043-1047,1748-1803,1864-1889`).

2. **Design goals addressed.** Design Goals 4 and 5; JM-7 and JM-9, with secondary benefit to JM-2/JM-6.

3. **Files to change.**
   - `copilot-sdk/copilot_sdk/graph/protocol.py:30-48,144-161`.
   - `copilot-sdk/copilot_sdk/graph/memory_store.py:1043-1047,1748-1803,1864-1889`.
   - `ci-platform/ci_platform/graph/age_graph_store.py:2015-2027,2668-2718,3074-3109`.
   - `copilot-sdk/copilot_sdk/graph/age_sdk_adapter.py:84-100,268-269,530-556`.

4. **What changes.** Make `domain: str` required for every Decision-sensitive read: `get_decision`, `get_verified_decisions`, `count_decisions`, `count_verified_decisions`, context/traversal, similar-case queries, links, and any equivalent method discovered in the protocol. Make `write_outcome` domain-required at the same contract boundary. Remove `None` branches that intentionally omit predicates. In each store, validate non-empty domain and add a domain filter to every relevant in-memory and Cypher read. Update the adapter to pass the required value and preserve it through all delegated calls.

5. **What must not change.** Preserve legitimate cross-domain transfer queries as explicitly named, reviewed operations; do not make cross-domain TransferPattern traversal impossible. Preserve return shapes, pagination, ordering, and read-only restrictions. Preserve test-only compatibility only behind an explicit test adapter, not a production default.

6. **Blast radius.** This is cross-cutting: all GraphStore implementations, adapter methods, scorer reads/writes, all five copilots’ routers/services, similar-case and framework reads, and test fixtures/call sites are affected. Compile/type failures are expected and desirable until every caller supplies its domain. The age-unification plan already identifies domain-scoping of all S2P framework reads as a contract dependency (`copilot-sdk/docs/design/age_unification_gaps_v1.md:464-472`).

7. **Tests needed.** Add contract tests parameterized over AGE, SQLite, and InMemory: omission fails; a domain returns only its own records; a foreign-domain record cannot be returned by any Decision read; traversal, links, similar-case, count, outcome, and verified reads all enforce the same rule. Add adapter pass-through spies. Add an explicit cross-domain transfer-pattern test proving only reviewed transfer APIs can traverse domains. Add static checks for Cypher reads lacking a domain parameter/predicate.

8. **Dependencies.** Fix 1 is not technically required, but this contract should land before Fix 8C/8G and before final S2P/DataOps query cleanup. Fix 5 is a parallel write-side fix. Update all callers before merging.

9. **Verification.** `python -m pytest copilot-sdk/tests -q -k "graph_store or domain or scorer"`; run each copilot backend test suite; run a deliberate call with omitted domain and assert a failure; run a cross-domain corpus test and compare returned ID sets.

10. **Estimated effort.** 2.5–4 engineer-days.

## §5 PHASE 3: S2P RECONCILIATION — FIX 3

### Fix 3 — Resolve S2P shadow and enrichment split

1. **Problem.** Blocker B remains OPEN. S2P points enrichment at the SQLite primary and can replace `app.state.graph_store` with it (`copilot-sdk/docs/design/jm_implementation_review_part1a_v1.md:11-15,157-158`; `s2p-copilot/backend/app/main.py:172-183`). The optional shadow path rejects `soc_graph` and constructs a separate AGE graph (`s2p-copilot/backend/app/s2p_shadow.py:117-129,223-250`; `copilot-sdk/docs/design/jm_implementation_review_part2b_v1.md:33-35`).

2. **Design goals addressed.** Design Goals 1, 4, 6, and 7; JM-1, JM-2, JM-4, JM-6, and JM-7.

3. **Files to change.**
   - `s2p-copilot/backend/app/main.py:160-183`.
   - `s2p-copilot/backend/app/s2p_shadow.py:82-129,223-250`.

4. **What changes.** Preferred option: retire the separate production shadow graph and make shadow state a phase/label/metadata view within the same `GraphStore` and `soc_graph`. Point enrichment at the same selected store as the scorer; never replace it with `DualWriteStore.primary` SQLite in production. If shadow behavior is needed for experiments, keep it behind an explicit disposable test profile that cannot advertise production JM compliance and cannot use Decision data from another graph. Remove the `soc_graph` rejection only if the resulting path demonstrably targets the same shared graph; otherwise remove the path.

5. **What must not change.** Preserve S2P domain isolation, scorer behavior, restore/L5 state semantics, enrichment response contracts, shadow opt-in behavior in disposable tests, and the ability to compare phases. Preserve SQLite local/test support outside production AGE profiles.

6. **Blast radius.** S2P startup, scorer construction, enrichment routers/services, situation traversal, shadow controls, health/status reporting, and any consumers of `app.state.graph_store` are affected. A key regression risk is that enrichment currently intentionally points at SQLite (`main.py:172-183`); callers may implicitly rely on SQLite-specific methods.

7. **Tests needed.** Startup tests for AGE and dual-write assert scorer, enrichment, and `app.state.graph_store` resolve to the same authoritative store/graph. Assert shadow opt-in either uses the same graph or is rejected in production. Simulate AGE outage and assert scorer/enrichment fail closed. Cross-domain S2P reads must not change. Add a test that compares DSN and graph name object identity/config values across scorer, enrichment, and shadow.

8. **Dependencies.** Requires an architecture decision before implementation. Fix 2 should land before changing traversal callers; Fix 1 should land before S2P is used as the one-graph startup model. Fix 6 depends on the chosen outcome.

9. **Verification.** `python -m pytest s2p-copilot/backend/tests -q`; launch S2P with production AGE settings and inspect startup state; run enrichment and situation endpoints; force AGE failure; assert no SQLite primary is selected and no second graph name/DSN is accepted.

10. **Estimated effort.** 2–4 engineer-days after decision. Add 0.5 day if shadow retirement requires migration of existing shadow tests.

### S2P design decision gate

The implementation owner must record one of these decisions before coding: **A (recommended):** retire the separate production shadow graph and use one shared GraphStore; **B:** retain shadow only as an explicitly isolated disposable test graph and remove it from production JM claims. Option B cannot close JM-1/Goal 6 and therefore leaves the final verdict PARTIAL.

## §6 PHASE 4: DATAOPS CLOSURE — FIX 4

### Fix 4 — Close DataOps fixture/offline substitution

1. **Problem.** P1-DOPS-1 and P1-DOPS-2 remain PARTIAL because Decision-shaped JSON and fixture/offline branches remain (`copilot-sdk/docs/design/jm_implementation_review_part1b_v1.md:90-96`; `copilot-sdk/apps/dataops/backend/app/context_router.py:381-403,431-437`; `copilot-sdk/apps/dataops/backend/app/graph_queries.py:46-63,509-527,550-564`). P2-DOPS-2 and P2-DOPS-4 also remain because startup seeds from local bundles and local JSON remains a metadata authority (`.../main.py:564-573`; `.../context_router.py:1603-1615`).

2. **Design goals addressed.** Design Goals 1, 3, 5, 6, and 7; JM-3 and JM-6, with secondary JM-8 benefit.

3. **Files to change.**
   - `copilot-sdk/apps/dataops/backend/app/graph_queries.py:46-63,509-564`.
   - `copilot-sdk/apps/dataops/backend/app/context_router.py:381-403,431-437,902-987,1579-1615`.
   - `copilot-sdk/apps/dataops/backend/app/main.py:342-424,564-573`.

4. **What changes.** Separate graph-required Decision/context paths from explicitly demo-only sample endpoints. In production, AGE query/client failure raises a typed 503 and never returns fixture rows. Remove production startup fixture restoration/seeding of Decision-shaped records; permit it only under an explicit disposable test/demo profile. Require domain on normalized Decision-shaped records and reject local JSON records without `domain="dataops"`. Keep local non-Decision metadata only when its provenance is explicit and it cannot enter the Decision graph response as authoritative evidence.

5. **What must not change.** Preserve legitimate demo mode, read-only sample endpoints, response schemas, DataOps domain IDs, enrichment facts, and explicit test fixtures. Preserve non-Decision operational metadata when clearly labeled and not used as a Decision substitute.

6. **Blast radius.** DataOps health, graph queries, context router endpoints, scorer startup, bundle restore, evolution-event seeding, and frontend consumers that expect demo content are affected. Existing graph enrichment is domain-scoped and should remain unchanged (`copilot-sdk/apps/dataops/backend/app/services/graph_enrichment.py:50-130`).

7. **Tests needed.** Production AGE failure tests for each graph query assert 503/exception and zero fixture rows. Demo-mode tests assert fixtures remain available only with the explicit demo flag. Startup tests assert no local Decision seed occurs in production, while disposable test mode still seeds and stamps `dataops`. JSON records without domain are rejected; valid non-Decision metadata remains labeled. Health tests must report the actual selected graph/source rather than `ok` with fixture provenance.

8. **Dependencies.** Depends on Fix 1 so AGE remains selected; should use Fix 2’s required domain contract. Fix 6 should follow to enforce the shared graph name after DataOps no longer has a substitute path.

9. **Verification.** `python -m pytest copilot-sdk/apps/dataops/backend/tests -q`; run DataOps with unreachable AGE and call graph/context/health endpoints; run with explicit demo/test profile and assert fixture behavior; inspect startup logs and `app.state.dataops_active_graph_config`.

10. **Estimated effort.** 2–3 engineer-days.

## §7 PHASE 5: STARTUP INVARIANT — FIX 6

### Fix 6 — Make `soc_graph` a startup invariant

1. **Problem.** Goal 6 is PARTIAL because all five startup paths still resolve configurable graph names, generic fallbacks can omit `graph_name`, and S2P shadow explicitly targets a second graph (`copilot-sdk/docs/design/jm_implementation_review_part2b_v1.md:21-35`). The active wrappers authorize `soc_graph` conditionally, but that is not a universal startup invariant (`.../trading/backend/app/graph_status.py:330-357`; purchasing `:365-386`; dataops `:314-334`).

2. **Design goals addressed.** Design Goals 1, 2, 6, and 7; JM-1, JM-2, JM-4, and JM-6.

3. **Files to change.**
   - `copilot-sdk/apps/trading/backend/app/main.py:303-313`; `.../trading/backend/app/graph_status.py:132-149,330-362`.
   - `copilot-sdk/apps/purchasing/backend/app/main.py:414-425`; `.../purchasing/backend/app/graph_status.py:134-145,365-386`.
   - `copilot-sdk/apps/dataops/backend/app/main.py:534-541`; `.../dataops/backend/app/graph_status.py:136-149,314-334`.
   - `s2p-copilot/backend/app/main.py:115-126`.
   - `gen-ai-roi-demo-v4-v50/backend/app/main.py:176-202`; `.../backend/app/db/neo4j.py:29-54`.

4. **What changes.** Add one shared production invariant: non-test AGE startup requires `graph_name == "soc_graph"` and the domain/graph authorization pair. Pass `graph_name` explicitly through every factory call, including generic helpers. Reject alternate production graph names before store construction. Keep test profiles explicitly named and isolated. Make SOC’s resolver expose the same invariant rather than hiding graph resolution in a legacy client-shaped module.

5. **What must not change.** Preserve test graph support, domain-specific authorization, GraphConfig ownership, backend selection, and the existing shared graph census/claim tooling. Do not hard-code `soc_graph` into tests that intentionally use isolated graphs.

6. **Blast radius.** All five application startup paths, active graph status, health endpoints, factory calls, deployment environment variables, and test profiles are affected. Any deployment currently using a non-`soc_graph` production graph will fail fast and must be migrated.

7. **Tests needed.** Parameterized five-copilot startup tests assert `soc_graph` and reject alternate production graph. Test omitted graph name in generic helpers. Test authorized `soc_graph` succeeds and unauthorized/mismatched domain fails. Verify test profiles retain their configured disposable graph. Assert all scorer/enrichment/shadow stores share DSN and graph.

8. **Dependencies.** Depends on Fixes 1, 3, and 4; otherwise a copilot could pass the invariant and still silently use SQLite or a second S2P graph. Fix 2 is required for final domain proof but not for the graph-name guard itself.

9. **Verification.** `python -m pytest copilot-sdk/apps/trading/backend/tests copilot-sdk/apps/purchasing/backend/tests copilot-sdk/apps/dataops/backend/tests s2p-copilot/backend/tests -q`; run SOC startup tests; run each service with a non-`soc_graph` production setting and assert fail-fast; run the five-config assertion in `phase6_claim_proof.py:176-188`.

10. **Estimated effort.** 1.5–2.5 engineer-days.

## §8 PHASE 6: CLEANUP BATCH — FIX 8

Fix 8 is intentionally grouped, but each sub-item has its own test and rollback boundary. The remaining Part 1A/2A items are documented at `copilot-sdk/docs/design/jm_implementation_review_part1a_v1.md:139-185`, `copilot-sdk/docs/design/jm_implementation_review_part1b_v1.md:84-115`, and `copilot-sdk/docs/design/jm_implementation_review_part2a_v1.md:9-16,§2.5,§3.2,§4`.

### 8A — Route projection through the common AGE lifecycle

- **Problem/evidence:** P2-INFRA-3 is PARTIAL because `AGEProjection` directly constructs `AGEClient` after loading GraphConfig (`copilot-sdk/docs/design/jm_implementation_review_part1a_v1.md:139-141`; `copilot-sdk/copilot_sdk/graph/projection.py:224-244`).
- **Goals:** Design Goals 1/2/6/7; JM-1/JM-6/JM-8.
- **Change:** Inject or obtain a read-only GraphStore/factory-owned client; retain read-only Cypher rejection and domain predicates. Do not allow projection callers to supply an unauthorized graph.
- **Preserve/blast radius:** Preserve projection output and mutation rejection. Affects projection consumers and AGE client lifecycle only.
- **Tests/dependencies:** Projection read, mutation rejection, DSN/graph authorization, and unreachable AGE tests. Depends on Fix 6; 0.5–1 day.
- **Verification:** `python -m pytest copilot-sdk/tests -q -k projection`; inspect that no projection test constructs a raw client.

### 8B — Route SOC seed construction through approved infrastructure

- **Problem/evidence:** P2-SOC-4 is PARTIAL; the original path is gone, but active `gen-ai-roi-demo-v4-v50/backend/app/graph_schema.py` still calls `get_graph_client` directly after config validation (`copilot-sdk/docs/design/jm_implementation_review_part1a_v1.md:149-150,181`; `gen-ai-roi-demo-v4-v50/backend/app/graph_schema.py:210-224,456-492`).
- **Goals:** Design Goals 1/2/6; JM-1/JM-6/JM-8.
- **Change:** Use the approved GraphStore/factory boundary for seed writes, or make the seed tool accept only an explicitly injected authorized client from the common lifecycle. Refuse production seed substitution and preserve disposable test seeding.
- **Preserve/blast radius:** Preserve schema/index creation and seed idempotency. Affects SOC startup/seed tooling and operational migrations.
- **Tests/dependencies:** Seed with AGE, missing DSN, alternate graph, and test graph; assert no direct ungoverned client. Depends on Fix 6; 0.5–1 day.
- **Verification:** `python -m pytest gen-ai-roi-demo-v4-v50/backend/tests -q -k "graph_schema or seed"`.

### 8C — Scope S2P LearningState and private artifact idempotency reads

- **Problem/evidence:** `LearningState` is queried without a domain (`s2p-copilot/backend/app/routers/framework_router.py:276-285`). AGE private artifact/idempotency lookups omit domain (`ci-platform/ci_platform/graph/age_graph_store.py:1214-1221,1293-1299,1387-1393,1725-1731,1897-1903`), listed in Part 2A §4.
- **Goals:** Design Goals 4/7; JM-2/JM-7/JM-9.
- **Change:** Stamp LearningState with domain at write time and add `WHERE ls.domain=$domain`; add domain to all artifact lookup predicates and parameters. If an artifact is deliberately global, rename/document it as global and provide a reviewed cross-domain API rather than relying on an omitted predicate.
- **Preserve/blast radius:** Preserve warm-start status and idempotent writes. Affects S2P framework status, scorer artifact persistence, and AGE migration data.
- **Tests/dependencies:** Foreign-domain LearningState/artifact cannot satisfy S2P; same-domain idempotency remains stable. Depends on Fix 2; 0.5–1 day.
- **Verification:** `python -m pytest copilot-sdk/tests s2p-copilot/backend/tests -q -k "learning or artifact or idempot"` plus cross-domain AGE query tests.

### 8D — Remove or quarantine the dormant S2P legacy reader

- **Problem/evidence:** P1-S2P-5 remains as a dormant callable reader accepting a legacy Neo4j driver, although no runtime caller was traced (`copilot-sdk/docs/design/jm_implementation_review_part1a_v1.md:14,175`; `s2p-copilot/backend/app/domains/s2p/graph.py:50-71`).
- **Goals:** Design Goals 1/6/7; JM-1/JM-6.
- **Change:** Prefer delete/deprecate the module and migrate its tests to `GraphStore`; if compatibility is required, make it an explicit test-only adapter and prohibit production imports.
- **Preserve/blast radius:** Preserve test coverage of equivalent domain-scoped reads, not the legacy driver API. Affects only dormant tests/imports if the call audit confirms review evidence.
- **Tests/dependencies:** Import-time production guard; equivalent GraphStore read tests. Depends on Fix 3; 0.5 day.
- **Verification:** `python -m pytest s2p-copilot/backend/tests -q -k "s2p_graph"`; repository-wide import scan and application startup smoke test.

### 8E — Close mixed S2P situation context

- **Problem/evidence:** The route combines local Decision metadata with graph traversal input even while asserting S2P and rejecting foreign graph Decision domains (`copilot-sdk/docs/design/jm_implementation_review_part1a_v1.md:161,183`; `s2p-copilot/backend/app/routers/s2p_situation.py:49-72,120-145`).
- **Goals:** Design Goals 4/6/7; JM-2/JM-6/JM-7.
- **Change:** Make the graph Decision authoritative for graph-derived fields; treat local metadata as explicitly non-Decision request metadata or reject it in production. Add a provenance assertion before rendering context.
- **Preserve/blast radius:** Preserve situation response shape and S2P templates. Affects situation endpoint inputs, provenance, and error behavior.
- **Tests/dependencies:** Foreign/local metadata conflict tests; graph outage returns 503; provenance marks only graph-backed values authoritative. Depends on Fix 2/3; 0.5–1 day.
- **Verification:** `python -m pytest s2p-copilot/backend/tests -q -k "situation or context"`.

### 8F — Quarantine S2P JSON Decision-shaped seed input

- **Problem/evidence:** JSON/local fallback input remains, although target validation and `domain="s2p"` stamping exist (`copilot-sdk/docs/design/jm_implementation_review_part1a_v1.md:162,185`; `s2p-copilot/backend/app/seed_graph.py:43-65,116-135,206-220`).
- **Goals:** Design Goals 3/5/6/7; JM-3/JM-6/JM-9.
- **Change:** Permit JSON seeds only for disposable test graphs; reject production `soc_graph` unless an explicit migration/seed command is authorized. Keep domain stamping and add provenance/source type to distinguish seed data from learned Decisions.
- **Preserve/blast radius:** Preserve repeatable test topology and seed IDs. Affects seed tooling and operational deployment scripts.
- **Tests/dependencies:** Production graph refusal; disposable graph success; domain/source assertions; idempotent rerun. Depends on Fix 6; 0.5–1 day.
- **Verification:** `python -m pytest s2p-copilot/backend/tests -q -k "seed_graph"`; run the seed command against a disposable graph and assert refusal against `soc_graph`.

### 8G — Route Purchasing `CI_DATA_DIR` through typed configuration

- **Problem/evidence:** P2-PUR-5 remains GAP because `_resolve_scoring_db` reads `CI_DATA_DIR` directly (`copilot-sdk/docs/design/jm_implementation_review_part1b_v1.md:100-104`; `copilot-sdk/apps/purchasing/backend/app/main.py:180-189`).
- **Goals:** Design Goal 2; JM-1/JM-8.
- **Change:** Put local DB path resolution in the typed Purchasing configuration/path helper; keep it explicitly local/test-only and prevent it from selecting a graph backend or becoming an AGE fallback.
- **Preserve/blast radius:** Preserve local DB filename, parent creation, and `:memory:` behavior. Affects Purchasing startup and CLI/test environment setup.
- **Tests/dependencies:** Env/path precedence tests and assertion that CI_DATA_DIR cannot alter active graph config. Depends on Fix 6; 0.5 day.
- **Verification:** `python -m pytest copilot-sdk/apps/purchasing/backend/tests -q -k "scoring_db or config"`.

## §9 PHASE 7: VALIDATION — FIX 7

### Fix 7 — Re-run full validation and operational proof

1. **Problem.** Code review alone cannot prove the live one-graph claims. Part 2B records the census/claim evidence as useful but insufficient to close code-level topology risks (`copilot-sdk/docs/design/jm_implementation_review_part2b_v1.md:7-17,51-80`).

2. **Design goals addressed.** All 7 design goals and all 9 JM goals. This fix changes no product behavior; it is the release gate proving the preceding changes.

3. **Files/tools to change or execute.** No production source changes are planned. Execute/update only validation artifacts if the existing tooling requires a report fixture: `copilot-sdk/scripts/phase6_claim_proof.py:76-125,154-165,176-188,210-228`, `copilot-sdk/scripts/graph_census_v2.py:15-64`, and `copilot-sdk/scripts/validate_age_migration.py:31-34,126-145,221-275`.

4. **What changes.** Add missing negative assertions to validation if needed: five production GraphConfigs must resolve the same DSN/`soc_graph`; no SQLite store may be authoritative in production AGE mode; no NULL-domain Decision; cross-domain TransferPatterns are explicit; Decision→Outcome→Receipt→Checkpoint chains are complete; AGE outage fails closed.

5. **What must not change.** Do not weaken claim thresholds, omit failed domains, or treat fixture/demo data as live evidence. Keep test graph separation and preserve raw evidence/report artifacts.

6. **Blast radius.** Release/deployment acceptance, live graph census, all five startup configurations, claim proof, migration validation, and operational runbooks.

7. **Tests needed.** Full unit/integration suites; five-copilot startup matrix; AGE outage matrix; domain-negative matrix; graph census; phase-6 claim proof; migration validator. Confirm all 8/8 claims only after the command output itself records PASS.

8. **Dependencies.** All fixes 1–6 and applicable Fix 8 sub-items must be merged and deployed to the validation environment.

9. **Verification commands.** From `copilot-sdk`:
   - `python -m pytest tests -q`.
   - `python scripts/phase6_claim_proof.py --execute --age-dsn $env:AGE_DSN --graph-name soc_graph`.
   - `python scripts/graph_census_v2.py --dsn $env:AGE_DSN --graph soc_graph`.
   - `python scripts/validate_age_migration.py --level comprehensive --age-dsn $env:AGE_DSN --test-graph protocol_v2_test_jm`.
   - Run each backend suite and capture startup/health responses for Trading, Purchasing, DataOps, S2P, and SOC.
   - Repeat the outage tests with an unreachable DSN and assert explicit startup/503 failure, not a successful SQLite/fixture response.

10. **Estimated effort.** 2–3 engineer-days, including deployment, evidence capture, and one repeat run after remediation.

## §10 RISK ASSESSMENT

| Fix/gap | What could go wrong if incorrect | Likelihood | Impact |
|---|---|---:|---:|
| Fix 1 — Trading/DataOps rewrite removal | Startup becomes unavailable where AGE configuration is incomplete; callers may have depended on hidden SQLite state. | Medium | High |
| Fix 2 — mandatory domain | Missed caller causes runtime failures; an incorrectly permissive compatibility default reopens cross-domain leakage. | High | Critical |
| Fix 3 — S2P split | Enrichment or shadow silently reads stale/empty state, or a test graph is accidentally used in production. | High | Critical |
| Fix 4 — DataOps fixtures | Demo/frontend paths break, or a fixture still enters an authoritative response under a new code path. | Medium | High |
| Fix 5 — legacy link | Existing relationship backfills fail or create edges with inconsistent properties. | Low | High |
| Fix 6 — `soc_graph` invariant | Deployments using alternate production graphs fail fast; a weak guard leaves a second graph possible. | Medium | Critical |
| Fix 8 — direct clients/cleanup | Seed/projection tools diverge from factory lifecycle; dormant compatibility code is removed while an untraced caller remains. | Low–Medium | Medium–High |
| Fix 7 — validation | False PASS from incomplete census, omitted domains, or fixture-backed claims masks all prior defects. | Medium | Critical |

Rollback strategy: each phase must be separately deployable behind configuration only for test environments; production rollback must not restore silent AGE→SQLite substitution. If a new failure is found, fail closed and correct the configuration/caller rather than reintroducing a fallback.

## §11 SUCCESS CRITERIA

| Phase | Required verdict change |
|---|---|
| Phase 1 | P1-TRD-1 and P2-DOPS-1 become CONFORMANT; no production AGE path rewrites to SQLite; legacy link is domain-stamped. |
| Phase 2 | Goal 4 and Goal 5 protocol/store enforcement become CONFORMANT; omitted domain cannot return Decision data. |
| Phase 3 | Blocker B becomes CLOSED; S2P scorer, enrichment, and permitted shadow state use one authoritative graph. |
| Phase 4 | P1-DOPS-1/P1-DOPS-2, P2-DOPS-2/P2-DOPS-4 become CONFORMANT or explicitly demo-only and non-authoritative. |
| Phase 5 | Goal 6/JM-1 one-graph startup invariant becomes CONFORMANT; all five production paths reject alternate graph names. |
| Phase 6 | Residual P2 direct-client, mixed-context, seed, LearningState, Purchasing path, and dormant-reader gaps are closed or explicitly quarantined. |
| Phase 7 | Census and claims provide reproducible evidence: one DSN/graph, five domains, domain-complete writes/reads, no NULL-domain Decisions, and fail-closed outage behavior. |

## §12 POST-PLAN: JM GOALS EXPECTED STATE

“After” means after the phase’s acceptance tests pass; a goal cannot be promoted solely because code was merged.

| JM Goal | Current | After Phase 1 | After Phase 2 | After Phase 3 | After Phase 4 | After Phase 5 | After Phase 6 | After Phase 7 |
|---|---|---|---|---|---|---|---|---|
| JM-1 One engine, one graph | PARTIAL/GAP | PARTIAL | PARTIAL | PARTIAL → one S2P authority | PARTIAL | CONFORMANT if invariant passes | CONFORMANT | CONFORMANT + proven |
| JM-2 Cross-graph attention | PARTIAL | PARTIAL | PARTIAL → fail-closed domain API | CONFORMANT path | CONFORMANT path | CONFORMANT | CONFORMANT | CONFORMANT + proven |
| JM-3 $604K finding | PARTIAL | PARTIAL | PARTIAL | PARTIAL | CONFORMANT data path | CONFORMANT | CONFORMANT | CONFORMANT + reproduced |
| JM-4 Pattern transfer | PARTIAL | PARTIAL | PARTIAL | CONFORMANT one-graph transfer | CONFORMANT | CONFORMANT | CONFORMANT | CONFORMANT + reproduced |
| JM-5 Conservation | PARTIAL | PARTIAL | PARTIAL | CONFORMANT if same S2P authority | CONFORMANT | CONFORMANT | CONFORMANT | CONFORMANT + chain proof |
| JM-6 One traversal, one answer | GAP/PARTIAL | PARTIAL | PARTIAL | PARTIAL → no S2P split | CONFORMANT path | CONFORMANT | CONFORMANT | CONFORMANT + outage proof |
| JM-7 Domain partitioning | PARTIAL | PARTIAL | CONFORMANT contract | CONFORMANT | CONFORMANT | CONFORMANT | CONFORMANT | CONFORMANT + negative proof |
| JM-8 SQLite local/test only | GAP/PARTIAL | PARTIAL → no Trading/DataOps rewrite | PARTIAL | CONFORMANT production S2P path | CONFORMANT | CONFORMANT | CONFORMANT | CONFORMANT + startup matrix |
| JM-9 Audit chain graph traversal | PARTIAL | CONFORMANT write paths | CONFORMANT | CONFORMANT | CONFORMANT | CONFORMANT | CONFORMANT | CONFORMANT + census |

## §13 READING LOG

The following required artifacts were read fully before writing this plan:

| File | Range |
|---|---:|
| `copilot-sdk/docs/design/jm_implementation_review_part1a_v1.md` | 1–218 |
| `copilot-sdk/docs/design/jm_implementation_review_part1b_v1.md` | 1–144 |
| `copilot-sdk/docs/design/jm_implementation_review_part2a_v1.md` | 1–256 |
| `copilot-sdk/docs/design/jm_implementation_review_part2b_v1.md` | 1–192 |
| `copilot-sdk/docs/design/age_unification_gaps_v1.md` | 1–817; §6 implementation plan reviewed |
| `copilot-sdk/CLAUDE.md` | 1–139 |

Source files re-checked for current line references include all paths named in §§3–9: the five copilot `main.py` startup paths; Trading, Purchasing, and DataOps graph-status modules; S2P shadow, situation, seed, framework, and legacy graph modules; DataOps graph queries/context; common protocol, InMemory, AGE store, adapter, projection, scorer/factory; SOC graph schema and resolver; and validation/census scripts. The active SOC seed file is `gen-ai-roi-demo-v4-v50/backend/app/graph_schema.py`; the originally named `.../domains/soc/graph_schema.py` is absent, as recorded by Part 1A (`copilot-sdk/docs/design/jm_implementation_review_part1a_v1.md:149-150,201-202`).

DOCUMENT_PATH: `copilot-sdk/docs/implementation_plans/jm_gap_closure_plan_v1.md`
FIX_COUNT: 8
PHASE_COUNT: 7
TOTAL_FILES: 25 unique production files; test files are affected within the listed suites
ESTIMATED_EFFORT: 12–18 engineer-days
DEPENDENCY_CRITICAL_PATH: Fix 1 + Fix 5 → Fix 2 → Fix 3 → Fix 4 → Fix 6 → Fix 8 → Fix 7
READY: YES
