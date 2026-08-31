# AGE Unification Complete — Design Document v1
# Date: August 30, 2026
# Status: VERIFIED AND UPDATED — source audit completed August 30, 2026

---

## 1. Problem Statement

The platform claims "all 5 copilots on AGE" but this is only partially true.
Core scorer Decisions and centroids use AGE (INV-4, INV-5 PASS). However,
35 categorized non-unified paths remain where reachable production state bypasses
the shared AGE graph or bypasses the GraphStore/GraphConfig contracts:

- 10 evolution/learning/observation paths outside AGE
- 10 promotion/authority/twin paths outside AGE
- 3 direct AGEClient/psycopg bypasses outside GraphStore
- 4 silent fallbacks that swallow or erase AGE errors
- 3 P1 decision-data paths that can reach SQLite or process memory
- 3 raw graph configuration reads bypassing GraphConfig

Every demo run creates SQLite WAL files in the source tree, dirtying git.
SOC PW is unstable (0F→3F) because Tab 2 IKS reads from SQLite evolution
state that degrades under extended testing.

The counts below are categorized findings, not unique files. One component may
appear in more than one category when it owns more than one kind of state.
The core scorer Decision and centroid path is currently AGE-backed when the
production profile is loaded; the findings are the remaining reachable paths.

---

## 2. Design Goals (7 Invariants)

These are the architectural contracts. Every line of production code must
satisfy ALL 7. No exceptions. No "temporary" bypasses.

### INV-1: GraphStore Protocol for All Decision Data
Every Decision read/write across all 5 copilots goes through GraphStore
protocol backed by AGE — no direct neo4j, no direct psycopg, no direct
SQLite for production Decision data.

### INV-2: GraphConfig for All Graph Access
Every graph access path uses GraphConfig for DSN/graph resolution — no
raw env var reads, no localhost fallbacks, no hardcoded defaults.

### INV-3: No Silent Substitution
When AGE is the declared backend, failure raises, never returns
fixtures/SQLite/in-memory data. Rule #10 (No Silent Failure).

### INV-4: Domain-Scoped Queries
Every query is domain-scoped — no unscoped Decision read can return
another copilot's data. Already PASS — preserve.

### INV-5: Domain-Stamped Writes
Every write stamps domain — no Decision enters the graph without an
explicit domain property. Already PASS — preserve.

### INV-6: One Shared Graph
One shared graph (soc_graph) — all 5 copilots read from and write to
the same graph, enabling cross-copilot traversal.

### INV-7: Close All Non-Unified Paths
Close all 35 categorized non-unified paths with an implementation plan
that prioritizes the P1s, addresses the P2-P7s, and sequences by dependency.

---

## 3. Audit Findings (from age_unification_audit.txt)

### 3.1 P1 — Decision Data Outside AGE (3 paths)
1. SDK SQLite GraphStore backend reachable: `copilot_sdk/graph/factory.py:177-188`
2. SDK dual-write mode uses SQLite as primary: `copilot_sdk/graph/factory.py:194-201`
3. S2P legacy audit decisions in process memory: `s2p-copilot/backend/app/framework/audit.py:24-27, :122-150, :176-194`

### 3.2 P2 — Centroid Persistence Outside AGE (2 paths)
1. SQLite GraphStore centroid checkpoints and L5 centroid rows:
   `copilot_sdk/graph/sqlite_store.py:455-491, :2414-2454, :2726-2780`
2. SOC serializes the mutable learning/scorer checkpoint to JSON:
   `gen-ai-roi-demo-v4-v50/backend/app/services/gae_state.py:86-92, :537-546`

### 3.3 P3 — Evolution/Learning/Observation State Outside AGE (10 paths)
1. Trading variant/evolution: `apps/trading/backend/app/main.py:410-415`
2. Purchasing variant/evolution: `apps/purchasing/backend/app/main.py:513-514`
3. DataOps variant/evolution: `apps/dataops/backend/app/main.py:654-663`
4. S2P variant/evolution: `s2p-copilot/backend/app/services/s2p_evolver.py:29-38`
5. SOC variant/evolution: `gen-ai-roi-demo-v4-v50/backend/app/services/evolver.py:260-270`
6. S2P compounding ledger: `s2p-copilot/backend/app/services/compounding_ledger.py:42-97`
7. DataOps holdout/verified-outcome: `apps/dataops/backend/app/dataops_governance.py:19-44`
8. Purchasing proof/verified-outcome: `apps/purchasing/backend/app/services/purchasing_control.py:119-148`
9. S2P proposal and canonical outcome store: `s2p-copilot/backend/app/services/proposal_service.py:40-64`, instantiated at `s2p-copilot/backend/app/main.py:204-205`
10. SOC DK-history telemetry remains process-local: `gen-ai-roi-demo-v4-v50/backend/app/services/soc_learning_control.py:51-57`

### 3.4 P4 — Promotion/Authority/Twin State Outside AGE (10 paths)
1. Trading promotion: `apps/trading/backend/app/services/claim_gate.py:120-125`
2. Purchasing promotion: `apps/purchasing/backend/app/services/purchasing_control.py:143-155`
3. DataOps promotion: `apps/dataops/backend/app/dataops_governance.py:41-44`
4. S2P promotion: `s2p-copilot/backend/app/services/s2p_autonomy.py:18-34`
5. SOC promotion: `gen-ai-roi-demo-v4-v50/backend/app/services/authority_ladder.py:65-87`
6. SOC authority-veto: `gen-ai-roi-demo-v4-v50/backend/app/services/authority_ladder.py:87-100`
7. S2P Frozen Twin snapshot is filesystem JSON, with an in-memory graph store:
   `s2p-copilot/backend/app/services/s2p_autonomy.py:27-31`, `copilot_sdk/twin/service.py:21-24`
8. Purchasing Frozen Twin snapshot is filesystem JSON:
   `apps/purchasing/backend/app/services/purchasing_control.py:150-155`
9. DataOps Frozen Twin uses the default filesystem-backed SDK store:
   `apps/dataops/backend/app/dataops_governance.py:43-45`, `copilot_sdk/twin/store.py:12-29`
10. SOC Learning Control uses the default filesystem-backed SDK store:
    `gen-ai-roi-demo-v4-v50/backend/app/services/soc_learning_control.py:51-57`

### 3.5 P5 — Direct Graph Clients Outside GraphStore (3 paths)
1. SOC direct AGEClient: `gen-ai-roi-demo-v4-v50/backend/app/db/graph_client.py:52-65`
2. S2P framework router direct AGEClient: `s2p-copilot/backend/app/routers/framework_router.py:20-32`
3. SOC posterior store direct psycopg: `gen-ai-roi-demo-v4-v50/backend/app/services/posterior_store.py:28-63`

### 3.6 P6 — Raw Graph Configuration Reads (3 paths)
1. SOC campaigns AGE_GRAPH_NAME: `gen-ai-roi-demo-v4-v50/backend/app/domains/soc/campaigns.py:122, :148`
2. SOC triage AGE_GRAPH_NAME: `gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py:285`
3. SOC graph-client error branch reads raw GRAPH_BACKEND after GraphConfig failure:
   `gen-ai-roi-demo-v4-v50/backend/app/db/graph_client.py:38-44`

### 3.7 P7 — Silent Substitution (4 paths)
1. SOC learning-store → None: `gen-ai-roi-demo-v4-v50/backend/app/services/gae_state.py:150-174`
2. SOC centroid → False: `gen-ai-roi-demo-v4-v50/backend/app/services/gae_state.py:427-441`
3. Purchasing graph-read → empty list: `apps/purchasing/backend/app/services/purchasing_control.py:160-170`
4. S2P duplicate-context → empty: `s2p-copilot/backend/app/graph/s2p_graph_reader.py:241-245`

---

## 4. Verification Results and Corrected Scope

The prior 26-path headline was directionally correct for the original
non-P2 bullets, but the original section itself totalled 27 when its P2 row
was included. It also omitted eight reachable state/configuration paths listed
above. No
original finding was removed. The following distinctions are required:

1. `SQLiteGraphStore` is a deliberate test/development implementation, but
   `create_graph_store()` also exposes it through the SQLite and dual-write
   branches. Production scorer guards reject it; production configuration can
   still select dual-write for non-SOC callers, whose primary is SQLite.
2. `s2p.db` is passed as a compatibility path to the S2P scorer, but the
   injected active graph store is authoritative at
   `s2p-copilot/backend/app/main.py:185-191`; it is not counted as an active
   Decision SQLite path.
3. The SOC and S2P direct AGE clients use domain predicates in the inspected
   Decision queries, so INV-4 remains PASS. They are still INV-1/P5 violations
   because the calls bypass the GraphStore protocol.
4. Frozen Twin snapshots are immutable comparison artifacts, not live
   Decisions. They are nevertheless non-unified authority state and remain in
   INV-7/P4 until the architecture explicitly exempts them.

## 5. Proposed Architecture

### 5.1 GraphStore Protocol Extension
The existing GraphStore protocol handles Decision + Centroid operations.
Extend it to handle:
- Evolution/variant state (currently SQLite)
- Promotion/authority state (currently SQLite)
- Compounding ledger (currently SQLite)
- Governance/holdout state (currently SQLite)

New AGE node types:
```
(:EvolutionState {domain, variant_id, generation, fitness, created_at})
(:PromotionState {domain, rule_id, status, min_n, fpr, promoted_at})
(:CompoundingLedger {domain, iks, conservation_status, entry_count})
(:GovernanceState {domain, holdout_pct, verified_count, abstention_rate})
```

### 5.2 Migration Strategy
For each SQLite store:
1. Add AGE write path (parallel with existing SQLite)
2. Add AGE read path with SQLite fallback (temporary)
3. Verify AGE data matches SQLite
4. Remove SQLite path
5. Remove fallback

### 5.3 Silent Substitution Elimination
Every catch block that swallows AGE errors must be replaced with:
- Raise on AGE unavailable (Rule #10)
- Health endpoint reflects failure
- No empty-list fallback for graph reads

---

## 6. Reference Documents (in-repo)

Architecture:
- `docs/design/judgment_memory_v2_9.md` — latest JM spec
- `docs/design/jm_frozen_contracts_v1.md` — frozen API contracts
- `docs/design/jm_implementation_review_part1_v1.md` through `part2b_v1.md` — implementation review
- `docs/design/jm_reference_and_value_upgrades_executable_v6.md` — upgrade execution plan
- `docs/design/blogs/new_docs/graph_native_reasoning_hero_v23.md` — why graph-native
- `docs/design/blogs/new_docs/math_synopsis_v20.md` — centroid persistence contracts
- `docs/design/blogs/new_docs/innovation_note_v28.md` — platform architecture

---

## 7. Execution Plan

The dependency order is:

1. Extend the GraphStore/AGE schema for variant, promotion, evidence,
   observation, twin metadata, and learning-state records. Preserve the
   existing required domain arguments and shared `soc_graph` authorization.
2. Migrate the ten P3 paths, beginning with the five `SQLiteVariantStore`
   instances, then S2P proposals/ledger, DataOps/Purchasing evidence ledgers,
   and SOC DK history. Reads must be AGE-first with verification before the
   SQLite implementation is removed.
3. Migrate the ten P4 paths: promotion/authority state, then Frozen Twin
   metadata/snapshots. Keep immutable baseline semantics and explicit
   corruption/missing-state errors.
4. Remove the four P7 swallowed-error paths. AGE unavailability must surface
   as an error and a degraded health result, never an empty or absent state.
5. Route the three P5 direct-client surfaces through GraphStore adapters and
   make the three P6 configuration surfaces consume GraphConfig only.
6. Close the three P1 branches last, after AGE parity is proven, then remove
   SQLite/dual-write production selection while retaining isolated test and
   migration tooling where explicitly documented.

### 7.1 Execution phases

| Phase | Scope | Primary files/components | Dependency | Effort |
|---|---|---|---|---|
| 1 | AGE node/schema + protocol extension | `copilot_sdk/graph/protocol.py`, `ci-platform/ci_platform/graph/age_graph_store.py`, adapter | none | 5–8 days |
| 2 | P3 evolution/learning state | five app evolvers, S2P proposal/ledger, DataOps/Purchasing ledgers, SOC DK history | 1 | 7–10 days |
| 3 | P4 promotion/twin state | five promotion stores, authority audit, four Frozen Twin paths | 1 | 7–10 days |
| 4 | P7 fail-closed behavior | SOC learning/centroid persistence, Purchasing reads, S2P context reads | 1–3 | 2–4 days |
| 5 | P5 GraphStore routing | SOC graph client, S2P framework router, SOC posterior store | 1 | 4–6 days |
| 6 | P6 GraphConfig routing | SOC campaigns, SOC triage, SOC graph-client branch | 1, 5 | 1–2 days |
| 7 | P1 production-path closure | factory SQLite/dual-write selection, S2P audit ledger | 2–6 | 3–5 days |

The highest-blast-radius phase is Phase 2 because evolution and outcome
telemetry feed several UI and promotion surfaces. Phase 7 has the highest
data-compatibility risk because it removes existing SQLite authority paths.

## 8. Success Criteria

1. `git status --porcelain` returns clean after demo run (no SQLite WAL)
2. SOC PW stable at 0F across 3 consecutive runs
3. All 7 invariants PASS (verified by bespoke test suite)
4. No `.sqlite3` files in production data directories
5. `demo.py --dump` shows all 5 copilots on `[AGE]` with zero SQLite fallback
6. Cross-copilot traversal works (e.g., Trading can read SOC patterns)
7. No categorized P1–P7 path remains outside the documented test or
   migration exception set.

## 9. Bespoke invariant tests

`tests/test_age_unification_invariants.py` is the executable audit gate. It
loads production configuration and imports production GraphStore/scorer code;
it intentionally remains red while the P1–P7 paths above exist. INV-4 and
INV-5 tests are regression tests for the already verified protocol contract.
