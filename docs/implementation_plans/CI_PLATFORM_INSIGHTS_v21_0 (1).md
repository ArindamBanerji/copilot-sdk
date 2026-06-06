# CI Platform Insights
## Living Architecture & State Document
**Version:** 21.0 · **Date:** June 1, 2026
**Previous version:** 20.0
**Authority:** MAP v5.140 · Protocol v2 v1.8 · JM v2.7 · L5 Design Spec v2

---

## §1 — What Changed in v21.0 (Since v20.0)

### The Headline

The platform crossed an architectural threshold. In the period since v20.0,
the copilot-sdk grew **10×** in file count (35 → 356 .py files). The test
suite grew **2.3×** (~2,764 → ~6,241 tests). The GraphStore protocol went
from ~5 methods to **26**. Protocol v2 shipped with **13 schema tables**
and **88 conformance tests** (84 active). Trading AGE is operational.
L5 is designed, documented, and awaiting L3+L4 completion to activate.

### Architecture Additions (v20.0 → v21.0)

| Layer | What shipped |
|---|---|
| GraphStore Protocol v2 | 26-method protocol, 13 SQLite tables, factory.py, memory_store.py |
| Protocol v2 conformance | 88 tests (120KB), 84 active, 4 OUTBOX_PENDING |
| Trading AGE active | TradingActiveGraphConfig, TradingActiveAGEGraphStore, graph_status.py |
| ci-platform AGE adapters | age_graph_store.py (62 methods, 58KB), age_sdk_adapter.py |
| ci-platform AGE adapter | Full Protocol v2: write_governed_decision, write_observation, append_evidence_receipt, archive, guarded reset |
| L5 Design Spec | Centroid, DKWeight, ConservationState as AGE nodes; 18 new conformance tests planned (59 total) |
| JM v2.7 | Judgment memory architecture authority; V=verified decisions, α=cumulative category coverage |
| 55+ design docs | docs/ directory committed: judgment_memory, protocol_v2, l5_design_spec, age plans, storage_architecture |
| S2P fixes | CI_DATA_DIR fix (Fix 4), status column, count_verified_decisions, O(1) conservation counting |

### Outstanding (Batch 11 — 18 prompts)

Identified, scanned, and sequenced. Execution begins with CONS-V-FIX
(conservation V = verified only) and BUNDLE-REGEN (Trading d=7→d=10).
Full list: §12.

### Known Regression in v21.0

S2P test collection: `test_s2p_suppliers.py` throws `FileNotFoundError`
during collection (926 tests collected, 2 errors). Not a test failure —
a missing fixture file. Track as P2 bug before next test count update.

---

## §2 — Platform Overview

### Repo Metrics (June 1, 2026)

| Repo | .py Files | LOC | Tests | Key Class |
|---|---|---|---|---|
| GAE (gae/ core) | 29 | 8,837 | 1,237 | `ProfileScorer` |
| GAE (total incl. tests) | 88 | 22,404 | — | — |
| SOC backend/app | 164 | 38,607 | 1,742 | `gae_state.py` |
| SOC backend/tests | 184 | 27,262 | — | — |
| SOC backend total | 348 | 65,869 | — | — |
| SOC frontend/src | 24 files (.tsx+.ts+.css) | 13,452 | 36 spec files | `RuntimeEvolutionTab` |
| S2P backend | 75 | 12,980 | 926 (+2 collect errors) | `S2PDomainConfigV2` |
| ci-platform | 30 | 6,484 | 350 | `AGEGraphStoreAdapter` |
| copilot-sdk (copilot_sdk/) | 85 | 12,083 | — | `GraphStore` protocol |
| copilot-sdk (apps/trading) | 106 | 13,940 | 727 | `TradingActiveGraphConfig` |
| copilot-sdk (apps/dataops) | 20 | 5,154 | 176 | `DataOpsGraphClient` |
| copilot-sdk (apps/purchasing) | 23 | 4,457 | 168 | — |
| copilot-sdk (tests/) | 90 | 13,201 | 915 | — |
| copilot-sdk (scripts/) | 7 | 1,584 | — | — |
| **copilot-sdk TOTAL** | **356** | **52,507** | **—** | — |

**Platform total: ~174K LOC across all repos** (was ~85K in v20.0 session starter — platform doubled in size).

### Test Count Summary

| Repo | v20.0 (baseline) | v21.0 | Δ |
|---|---|---|---|
| GAE | 1,183 | 1,237 | +54 |
| SOC backend | 1,003 | 1,742 | +739 |
| S2P backend | 132 | 926 | +794 |
| ci-platform | 174 | 350 | +176 |
| copilot-sdk root | 18 | 915 | +897 |
| Trading | ~704 | 727 | +23 |
| DataOps | ~175 | 176 | +1 |
| Purchasing | ~147 | 168 | +21 |
| **Total** | **~2,764** | **~6,241** | **+3,477 (+126%)** |

Protocol v2 conformance (in copilot-sdk root): 88 tests total,
84 active, 4 `@OUTBOX_PENDING` (unblock when outbox table ships — Batch 11 P14).

### Ports & Services

| Component | Port | Backend | Auth |
|---|---|---|---|
| SOC FastAPI | 8001 | AGE (PostgreSQL 17, WSL2:5433) | — |
| S2P FastAPI | 8002 | SQLite (~/.ci-platform/s2p/s2p.db) | — |
| Trading FastAPI | 8010 | SQLite (~/.ci-platform/trading/trading.db) | — |
| Purchasing FastAPI | 8020 | SQLite (~/.ci-platform/purchasing/purchasing.db) | — |
| DataOps FastAPI | 8030 | SQLite (~/.ci-platform/dataops/dataops.db) | — |
| Vite frontend | 5173 | — | — |
| PostgreSQL+AGE | 5433 | WSL2 Ubuntu-24.04, pg cluster 17 main | postgres/postgres |

---

## §3 — Three-Layer Architecture

```
Layer 1: GAE (graph-attention-engine-v50/)
  Pure math. Apache 2.0. PyPI v0.7.23. 1,237 tests. numpy-only.
  ProfileScorer, DiagonalKernel, KernelSelector, CalibrationProfile,
  LearningState, EvidenceLedger, ReferralEngine.
  Framework v4: TwoPhaseStrategy, CoordinateDescentEstimator,
  PromotionGate, NoveltyTracker, BatchCompositionPolicy.
  Domain-agnostic. d = len(factors), configurable.

Layer 2: ci-platform (ci-platform/)
  Shared infrastructure. Apache 2.0. 350 tests.
  AGEClient — graph client. _S() serialization. All Cypher.
  AGEGraphStoreAdapter — 62 methods, 58KB. Full Protocol v2.
  AGESDKAdapter — bridge between SDK GraphStore protocol and AGEGraphStoreAdapter.
  DomainConfig, entity resolution, connectors, data onboarding.
  Audit chain: DecisionEntry/OutcomeEntry in EvidenceLedger.
  S2PDomainConfig lives here.

Layer 3: Copilots + SDK (proprietary)
  SOC (gen-ai-roi-demo-v4-v50/): 1,742 backend tests, 36 E2E spec files.
  S2P (s2p-copilot/): 926 tests (+2 collection errors).
  copilot-sdk (356 .py files, 915 tests):
    ├── copilot_sdk/      — SDK core (85 .py files, 12,083 LOC)
    │   └── graph/        — Protocol v2 (6 files: protocol, factory, sqlite_store, memory_store, contract, __init__)
    ├── apps/trading/     — 55 .py files, 727 tests
    ├── apps/dataops/     — 10 .py files, 176 tests
    ├── apps/purchasing/  — 8 .py files, 168 tests
    └── apps/s2p/         — (preview only, main S2P is separate repo)
```

### Two-Graph Architecture (DataOps pattern — all SDK copilots)

Each SDK copilot has TWO separate graph paths that must not be conflated:

```
Path A: SQLiteGraphStore (via factory.py)
  Purpose: scorer Decisions, Outcomes, conservation V
  Writes: write_governed_decision, write_outcome, count_verified_decisions
  Factory: create_graph_store(backend="sqlite", domain="trading", ...)
  Location: ~/.ci-platform/{domain}/{domain}.db

Path B: DataOpsGraphClient / AGEClient (ci-platform)
  Purpose: operational graph — pipelines, alerts, entities
  Writes: direct AGE queries via AGEClient
  Location: SOC AGE graph (PostgreSQL 17, WSL2)
  Status: LEGITIMATE dual-path by design (confirmed in analysis)
```

Never merge these paths. Path A is the Protocol v2 governed decision store.
Path B is the domain-specific operational graph.

---

## §4 — Five Compounding Pathways

Every module serves one or more of these pathways:

1. **Centroid Learning** — `ProfileScorer.update()` moves centroid positions
   toward verified decisions. μ(C,A,D) IS the institutional knowledge.
   Files: `profile_scorer.py`, `calibration.py`.

2. **W2 Flywheel** — `TRIGGERED_EVOLUTION` graph edges connect verified
   decisions to future similar contexts. `PatternHistoryFactorComputer`
   reads these as a scoring factor (+10.13pp, p=0.0002).
   Files: `factors.py`, `graph_schema.py`.

3. **Graph Enrichment** — External enrichment (CISA KEV, NVD, Pulsedive)
   creates new edges that change scoring context. Files: `enrichment/`.

4. **Re-Convergence** — Recovery after disruption is mathematically faster
   each time (γ>1 theorem). Files: `convergence.py`.

5. **DiagonalKernel Calibration** — The distance metric improves as σ
   estimates sharpen. DK weights per-factor by 1/σ². Files: `kernels.py`,
   `dk_estimator.py`.

---

## §5 — GraphStore Protocol v2

### Architecture Decision

Protocol v2 is ADDITIVE — `write_decision()` (v1) preserved for
`CompoundingScorer` backward compat. `write_governed_decision()` (v2)
is the new path with explicit decision_id, status lifecycle, and probabilities.

### 26-Method Protocol Surface

```python
class GraphStore(Protocol):
    # V1 (preserved for CompoundingScorer backward compat)
    def write_decision(...) -> str: ...              # returns generated decision_id

    # V2 governed lifecycle
    def write_governed_decision(...) -> None: ...    # caller supplies decision_id
    def write_outcome(...) -> None: ...              # status → confirmed/overridden
    def write_observation(...) -> None: ...          # preview/read only, excluded from V
    def append_evidence_receipt(...) -> tuple[int, str]: ...  # (chain_index, payload_hash)
    def write_conservation_status(...) -> None: ...
    def write_fingerprint(...) -> None: ...
    def write_centroid_checkpoint(...) -> None: ...
    def write_evolution_event(...) -> None: ...
    def link_entity(...) -> None: ...

    # Lifecycle management
    def archive_decisions(...) -> int: ...
    def domain_scoped_reset(domain: str) -> None: ...

    # Reads
    def get_decision(decision_id: str) -> dict | None: ...
    def get_decisions(...) -> list[dict]: ...
    def get_all_decisions(domain: str) -> list[dict]: ...
    def get_verified_decisions(domain: str) -> list[dict]: ...

    # Conservation counts (Standing Rule #37: V = verified only)
    def count_verified(domain: str) -> int: ...          # JOIN with outcomes
    def count_verified_decisions(domain: str) -> int: ... # status IN ('confirmed','overridden')
    def count_correct(domain: str) -> int: ...
    def count_decisions(domain: str) -> int: ...          # ALL statuses — display only

    # Centroid storage
    def save_centroids(...) -> None: ...
    def load_latest_centroids(domain: str) -> Any | None: ...
    def get_centroid_checkpoints(...) -> list[dict]: ...

    # Archive
    def archive_old_decisions(domain: str, keep_recent: int = 800) -> int: ...
    def count_archived(domain: str) -> int: ...
    def close() -> None: ...
```

### 13-Table SQLite Schema

```
decisions               — pending/confirmed/overridden lifecycle
outcomes                — write_outcome, is_correct, verified_at
centroid_checkpoints    — μ snapshots with IKS
evolution_events        — AE evolver history
rl_state                — Thompson sampling posteriors
decision_entity_edges   — link_entity pairs
observations            — preview/read scores (excluded from V)
observation_entity_edges — ABOUT edges from observations
observation_factor_vectors — factor vectors for observations
evidence_receipts       — hash-chained audit trail
conservation_snapshots  — transition snapshots (GREEN/AMBER/RED)
fingerprints            — DK weight estimation snapshots
decisions_archive       — archived pending rows
```

**Missing (batch 11 P14):** `outbox` and `outbox_quarantine` tables.
4 conformance tests remain `@OUTBOX_PENDING` until these ship.

### Idempotency Classes

| Class | Operations | Conflict policy |
|---|---|---|
| A — Must-survive | write_governed_decision, write_outcome, append_evidence_receipt, write_centroid_checkpoint, write_evolution_event | Skip on identical payload_hash. Quarantine on conflict. |
| B — Recomputable | write_fingerprint, write_conservation_status | Upsert — newer replaces older |
| C — Disposable | write_observation, link_entity | INSERT OR IGNORE |

### Factory Pattern

```python
from copilot_sdk.graph.factory import create_graph_store

# SQLite (default — all SDK copilots)
store = create_graph_store(backend="sqlite", domain="trading")
# → ~/.ci-platform/trading/trading.db

# AGE (Trading active, guarded)
store = create_graph_store(
    backend="age", domain="trading",
    dsn=os.environ["TRADING_ACTIVE_AGE_DSN"],
    graph_name="protocol_v2_test",
    test_mode=True,
)
```

Safety guards in factory: soc_graph forbidden, protocol_v2_test* requires
test_mode=True, product graphs require allow-list membership.

---

## §6 — AGE Migration State

### Three Adapters (ci-platform/ci_platform/graph/)

| File | Size | Methods | Purpose |
|---|---|---|---|
| `age_client.py` | 35.8KB | ~40 | Raw AGE Cypher execution, _S() serialization, connection pool |
| `age_graph_store.py` | 58.4KB | 62 | Full Protocol v2 implementation for AGE |
| `age_sdk_adapter.py` | 10.9KB | ~15 | Bridge: SDK GraphStore protocol → AGEGraphStoreAdapter |

### Current AGE Status per Copilot

| Copilot | GraphStore backend | AGE Decision writes | Note |
|---|---|---|---|
| SOC | AGE (direct AGEClient) | ✅ Yes | Existing AGEClient path, not via factory |
| Trading | SQLite (default) or AGE (TRADING_ACTIVE_*) | ✅ Test mode available | graph_status.py, TradingActiveAGEGraphStore |
| S2P | SQLite | ❌ | Phase 3 per Protocol v2 roadmap |
| DataOps | SQLite | ❌ | **P17 DATAOPS-AGE is L5 prerequisite** |
| Purchasing | SQLite | ❌ | After DataOps |

### AGE Cypher Standing Rules (§3 invariants)

- **No `$param`** — use `_S()` for string serialization
- **No `MERGE`** — use MATCH→CREATE two-step
- **No `datetime()`** — use epoch integers
- **No `ON CREATE SET` / `ON MATCH SET`** — two-step pattern
- **`count` alias → `cnt`** (reserved word in AGE)
- **No `labels[0]`** → use `head(labels(n))`
- **No `toString()`** — cast differently or avoid
- **`SET n = {}` FORBIDDEN** — AGE interprets as "delete all properties"
- **Decision nodes atomic with DECIDED_ON edge** — single Cypher statement

### L5 Design (Planned — L3+L4 prerequisite)

Three new AGE node types (L5 Design Spec v2, June 1, 2026):

```
Centroid(domain, category, action, vector_json, d, count, eta_last, created_at, updated_at)
  Edge: -[:SHAPED_BY {eta, delta_norm}]->(Decision)

DKWeight(domain, entity_group, weight_json, d, n_confirmed, n_overridden,
         confirmed_mean_json, confirmed_m2_json, ...)  ← Welford required
  Edge: -[:SUPERSEDES]->(DKWeight)

ConservationState(domain, status, alpha, q, V, theta_min, product,
                  categories_total, categories_with_data, complacency_flag, ...)
  Edge: -[:TRIGGERED_BY {old_status, new_status}]->(Decision) on transition
```

6 new GraphStore methods (update_centroid, get_centroids, update_dk_weights,
get_dk_weights, update_conservation_state, get_conservation_state).
18 new conformance tests (42-59). Total: 59 conformance tests post-L5.

**L5 prerequisite chain:** L3 complete (all 5 copilots write Decisions/Outcomes to AGE)
→ L4 complete (EvidenceReceipt wired, Observation wired, Outbox table) → L5.
Current blocker: P17 DATAOPS-AGE (last copilot without AGE Decision writes).

---

## §7 — Key Architecture Files

### The Six Core Files (Understanding the System)

```
1. SOC: backend/app/routers/triage.py           ← THE decision pipeline (score→referral→write-back)
2. SOC: backend/app/services/gae_state.py       ← Singleton scorer state, _learning_state global
3. GAE: gae/profile_scorer.py                   ← THE scorer: score(), update(), centroids
4. ci-platform: ci_platform/graph/age_client.py ← AGE graph client, _S() serialization
5. SDK: copilot_sdk/graph/sqlite_store.py       ← SQLite adapter (67 methods, 73KB)
6. SDK: copilot_sdk/graph/protocol.py           ← GraphStore protocol (26 methods, 5.1KB)
```

### GraphStore Module (copilot_sdk/graph/)

| File | Size | Purpose |
|---|---|---|
| `protocol.py` | 5.1KB | Runtime-checkable Protocol, 26 method signatures |
| `factory.py` | 5.3KB | create_graph_store() with AGE guards |
| `sqlite_store.py` | 73KB | 67 methods, 13 tables, _ensure_migrations() |
| `memory_store.py` | 34.3KB | In-memory adapter for tests, matches SQLite API |
| `contract.py` | 2.1KB | Structural protocol contracts |

### Protocol v2 Test Suite (tests/graph/)

| File | Size | Tests | Purpose |
|---|---|---|---|
| `test_protocol_v2_conformance.py` | 120.2KB | 88 | Primary conformance suite, parametrized SQLite+AGE |
| `test_soc_age_projection_contract.py` | 16.6KB | ~40 | SOC AGE projection contracts |
| `test_sqlite_store.py` | 15.1KB | — | SQLite-specific tests |
| `test_graphstore_factory.py` | 8KB | — | Factory guard tests |
| `test_memory_store.py` | 8.8KB | — | In-memory adapter tests |
| `test_contract_cross.py` | 6.6KB | — | Cross-adapter contracts |

### Trading AGE Active Files (apps/trading/)

| File | Size | Tests |
|---|---|---|
| `backend/app/graph_status.py` | 12.7KB | — |
| `backend/tests/test_trading_graph_status.py` | 18.5KB | 11 |
| `backend/tests/test_trading_active_age_live.py` | 4.2KB | guarded (TRADING_ACTIVE_LIVE_AGE_TEST=1) |

### Design Documents (docs/ — 55 committed)

Key authorities for implementation:

| Document | Purpose |
|---|---|
| `judgment_memory_v2_7.md` (56.4KB) | **ARCHITECTURE AUTHORITY** — V definition, α definition, Decision lifecycle |
| `protocol_v2_design_v1_8.md` (50KB) | **IMPL AUTHORITY** — 26 methods, idempotency, outbox, conformance tests |
| `l5_design_spec_v5.md` (27.2KB) | L5 node design — Centroid, DKWeight, ConservationState |
| `storage_architecture.md` (67KB) | Full storage design |
| `opus_review_handoff_governed_graph_migration.md` (66KB) | Migration architecture review |
| `s2p_pw_failures_v2_4.md` (42.6KB) | S2P Playwright root cause + fixes |
| `soc_age_schema_compatibility_spec_v1.md` (31.7KB) | SOC↔canonical vocabulary |

---

## §8 — Conservation Law & Standing Rules

### Conservation Formula (Invariants)

```
α·q·V ≥ θ_min

α     = cumulative category coverage = categories_with_verified / C (monotone, JM v2.7)
q     = rolling verified accuracy over 400 decisions (NOT lifetime average)
V     = count_verified_decisions() — decisions with status IN ('confirmed','overridden')
θ_min = 23.53/(α×V)  — formula, NOT a constant
```

**Standing Rule #37 (JM v2.7):** V = verified decisions only. Pending decisions
are excluded from V. `count_decisions()` counts all statuses — used for display
only, never for conservation computation.

**Standing Rule #38:** α = cumulative category coverage, NOT penalty ratio.
`α = len(categories_with_any_verified_decision) / C`. Computed from AGE:
```cypher
MATCH (d:Decision {domain: $domain}) WHERE d.status IN ['confirmed','overridden']
RETURN COUNT(DISTINCT d.category) AS c_d
```

### Conservation Status Machine

```
GREEN → AMBER: learning paused, scoring continues
GREEN → RED:   learning paused, scoring degraded
AMBER → GREEN: sufficient oversight restored
```

Components register for GREEN/AMBER/RED transitions via `ConservationStateMachine`.
**Never** direct point-to-point wiring.

### Key Invariants (§3 of session doc)

1. **ε_firm★ = 0.125.** Not 0.387 or 0.128. Re-convergence boundary.
2. **θ_min = 23.53/(α×V).** Formula, not constant.
3. **q = rolling over 400 decisions.** Not lifetime average.
4. **A=4 canonical.** Four actions. `refer_to_analyst` via R1-R7 referral rules, NOT 5th action.
5. **η_override=0.01.** 5× attenuation from noise, not arbitrary.
6. **KernelSelector: rule-based PRIMARY.** Data-driven monitoring only.
7. **Re-Convergence is conditional.** Category-sparse + warm-started + ε_firm > 0.125.
8. **b=2.11 is sim-only.** EXP-G1 needed for production validation.
9. **Oracle separation only.** META-4 retired.
10. **α = among verified decisions.** Not among all decisions.
11. **DiagonalKernel weights: three types** (WeightProvenance). Code normalizing
    all weights is wrong.
12. **Conservation is a state machine.** ConservationStateMachine.

---

## §9 — Platform State (June 1, 2026)

### Live Conservation Status

| Copilot | Status | V (verified) | total_decisions | Note |
|---|---|---|---|---|
| SOC | — | 5,053 | — | IKS=93.3, 645 alerts processed |
| S2P | **GREEN** | 27 | 39 | New DB clean post Fix4 |
| Trading | **RED** | 40 | 642 | 602 ghost pending — bundle d=7 mismatch |
| DataOps | **RED** | 20 | 575 | 555 ghost pending — cold start |
| Purchasing | **RED** | 20 | 520 | 500 ghost pending — cold start |

**Root cause for Trading/DataOps/Purchasing RED:** Trading bundle fails to
restore (d=7 vs preset d=10 → falls back to np.full 0.5). Copilots start cold.
Live demo scores hundreds of alerts that never get verified → ghost pending
decisions inflate `total_decisions` dramatically. Fix: Batch 11 P1 (CONS-V-FIX)
changes `total_decisions` display to verified-only. P2 (BUNDLE-REGEN) fixes
the bundle shape so copilots start warm.

### Database States

| DB | Path | Size | Rows | Status |
|---|---|---|---|---|
| S2P (new) | ~/.ci-platform/s2p/s2p.db | 4KB | 1 decision, 1 outcome | ✅ Clean post Fix4 |
| S2P (old) | backend/app/data/s2p.db | 34.4MB | 24,027 decisions | ⚠️ Old path, not used |
| Trading | ~/.ci-platform/trading/trading.db | 612KB | — | Active |
| DataOps | ~/.ci-platform/dataops/dataops.db | 584KB | — | Active |
| Purchasing | ~/.ci-platform/purchasing/purchasing.db | 596KB | — | Active |
| SOC | PostgreSQL/AGE WSL2:5433 | — | ~12,177 nodes | Active |

### Design Decisions (Locked — Do Not Reopen)

| Decision | What was decided | Authority |
|---|---|---|
| D-01 | Factor polarity inversions (ThreatIntel, DeviceTrust) — deferred v1.1 | Session v20 |
| D-03 | PromotionGate hardcodes conservation_pass=True — deferred v1.1 | Session v20 |
| D-08 | WeightProvenance enum + named constructors — DONE | Session v20 |
| D-05 | Split accessor get_scorer()/acquire_scorer() — DONE | Session v20 |
| D-07 | seed_graph clean origin guard — DONE | Session v20 |
| D-02 | W2 flywheel AGE read path factor_snapshot — DONE | Session v20 |
| D-04 | OLSMonitor CUSUM reset — DONE | Session v20 |
| JM-V | V = verified decisions only (count_verified_decisions) | JM v2.7 |
| JM-α | α = cumulative category coverage (not penalty ratio) | JM v2.7 |
| JM-OBS | Observations excluded from V, not in AgentEvolver flywheel | JM v2.7 |
| P2-OUT | write_outcome duplicate → RAISE (one outcome per decision hard invariant) | Protocol v2 v1.8 |
| P2-ADT | archive_decisions with verified requires confirm_verified=True guard | Protocol v2 v1.8 |
| P2-SVC | GraphStore methods are synchronous canonical writes; outbox in service layer | Protocol v2 v1.8 |
| P2-RET | append_evidence_receipt returns (chain_index, payload_hash) only | Protocol v2 v1.6 M1 fix |
| AGE-MRG | No MERGE in AGE Cypher — two-step read-then-CREATE-or-SET | AGE standing rules |
| L5-α | ConservationState.alpha = cumulative coverage computed from Decision nodes | L5 Spec v2 |
| L5-WFD | DKWeight Welford state (mean, M2) required for audit chain | L5 Spec v2 |

---

## §10 — Known Issues Tracker

### Open P1 Issues: 0

All v20.0 P1 issues resolved. No open P1.

### Active Bugs (June 1, 2026) — Full detail in CI_BUG_SYNOPSIS_v21_0.md

**Tier 1 — Demo-breaking (fix immediately):**

| ID | Bug | File | Fix |
|---|---|---|---|
| BUG-001 | Conservation V counts all decisions, not verified only (Trading total=642 vs V=40) | conservation_router.py · s2p.py | Batch 11 P1 — 2 lines |
| BUG-002 | Trading bundle shape mismatch d=7 vs preset d=10 (cold-starts every demo) | regenerate_demo_bundles.py | Batch 11 P2 — add 3 factors + re-run |

**Tier 2 — CI-breaking (4 failing tests + 1 collection error):**

| ID | Bug | File | Fix |
|---|---|---|---|
| BUG-003 | `append_evidence_receipt` returns `tuple[Any,...]` not `tuple[int,str]` | sqlite_store.py:904 | Add `-> tuple[int, str]` annotation — 5 min manual |
| BUG-004 | factory.py returns `Any` not `GraphStore` | factory.py:175 | Add `cast(GraphStore, ...)` — 5 min manual |
| BUG-005 | GraphStore protocol structural invariant tests failing (2 tests) | test_graph_entity_links.py · test_graphstore_consolidation.py | Batch 11 P13 |
| BUG-006 | S2P `test_s2p_suppliers.py` FileNotFoundError — module-level relative path `Path("../data/s2p_demo_suppliers.json")` fails when pytest runs from repo root | test_s2p_suppliers.py:16 | Replace with `Path(__file__).parent.parent / "app" / "data" / "s2p_demo_suppliers.json"` — 10 min manual |

**Note on BUG-003, BUG-004, BUG-006:** All three are under 15 minutes total. Fix directly in coding session, no Codex prompt needed.

**Test health: 98.9%** — 6,241 tests total, 4 failing, 2 collection errors. 4 `@OUTBOX_PENDING` conformance tests are expected skips (not failures).

---

## §11 — GraphStore Implementations (3 Adapters)

All three implement the 26-method GraphStore protocol:

| Adapter | Location | Size | Notes |
|---|---|---|---|
| `SQLiteGraphStore` | copilot_sdk/graph/sqlite_store.py | 73KB, 67 methods | Primary for all SDK copilots. 13 tables. |
| `InMemoryGraphStore` | copilot_sdk/graph/memory_store.py | 34.3KB | Used in tests. Matches SQLite API. |
| `AGEGraphStoreAdapter` | ci_platform/graph/age_graph_store.py | 58.4KB, 62 methods | Full Protocol v2 on AGE. |
| `AGESDKAdapter` | ci_platform/graph/age_sdk_adapter.py | 10.9KB | Thin bridge: SDK protocol → AGEGraphStoreAdapter |
| `TradingActiveAGEGraphStore` | apps/trading/backend/app/graph_status.py | 12.7KB | Wraps AGESDKAdapter, adds Trading-specific guards |
| `S2PActiveAGEGraphStore` | s2p-copilot/backend/app/s2p_graph_status.py | — | S2P equivalent of Trading pattern |
| `PurchasingActiveAGEGraphStore` | apps/purchasing/backend/app/graph_status.py | — | Purchasing equivalent of Trading pattern |
| `DemoGraphStore` | copilot_sdk/demo/evolve_demo.py | — | Thin InMemoryGraphStore subclass for demo scenarios |
| `GraphStoreCounts` | copilot_sdk/scoring/two_phase_strategy.py | — | Narrow sub-protocol (count operations only) for TwoPhaseStrategy. Separate from main GraphStore protocol — implementations must satisfy both. |

**Factory:** `copilot_sdk.graph.factory.create_graph_store()` selects SQLite
or AGE based on `GRAPH_BACKEND` env var. AGE requires explicit DSN + graph name.
soc_graph is forbidden in factory context. protocol_v2_test* requires test_mode=True.

---

## §12 — Outstanding Work (Batch 11 — 18 Prompts)

### Execution Order

| # | Prompt | Repos | Effort | Tier |
|---|---|---|---|---|
| 1 | **CONS-V-FIX** — conservation_router V = count_verified_decisions | sdk + s2p | 0.5d | Foundation |
| 2 | **BUNDLE-REGEN-D10** — Trading bundle d=7→d=10 | sdk | 0.5d | Foundation |
| 3 | **TRD-AE-VARIANTS** — Trading evolver_config | sdk | 0.5d | AE variants |
| 4 | **DOPS-AE-VARIANTS** — DataOps evolver_config | sdk | 0.5d | AE variants |
| 5 | **PUR-AE-VARIANTS** — Purchasing evolver_config | sdk | 0.5d | AE variants |
| 6 | **S2P-AE-SUPPLEMENT** — 2 more families + min_samples 10→50 | s2p | 0.5d | AE variants |
| 7 | **TRD-MULTI-TRADER** — trader_id in NormalizedTrade + connectors | sdk | 0.5d | Trading |
| 8 | **TRD-T3-TOD** — time-of-day pattern detector (analytics.py) | sdk | 1d | Trading |
| 9 | **S2P-F8-RANKING** — factor ranking endpoint | s2p | 1d | S2P |
| 10 | **S2P-F20-OPTIMIZER** — centroid import + conservation gate | s2p | 1d | S2P |
| 11 | **S2P-RECEIPT-FIELDS** — 4 missing fields on OutcomeReceipt | s2p | 0.5d | S2P |
| 12 | **CONTRIBUTION-FE** — FactorContributionChart component | sdk | 1d | Platform |
| 13 | **GP-MYPY** — 2 mypy errors (sqlite_store:904 + factory:175) | sdk | 0.5d | Platform |
| 14 | **OUTBOX-QUARANTINE** — outbox+quarantine tables + enqueue (unblocks 4 conformance tests) | sdk | 1d | Protocol v2 |
| 15 | **OBSERVATION-WIRING** — S2P preview → write_observation | s2p | 0.5d | Protocol v2 |
| 16 | **EVIDENCE-RECEIPT-WIRING** — learn path → append_evidence_receipt | s2p | 1d | Protocol v2 |
| 17 | **DATAOPS-AGE** — DataOps graph_status.py (L5 prerequisite — only copilot without active AGE store; Trading, S2P, Purchasing all have equivalent implementations) | sdk | 1.5d | AGE migration |
| 18 | **DEMO-AGE-OPS** — per-copilot AGE flags in demo.py | sdk | 1d | AGE migration |

**Estimated total:** ~14 working days.

### L5 Prerequisites

L5 (Centroid/DKWeight/ConservationState AGE nodes) requires:
- ✅ Protocol v2 tables (done)
- ✅ write_governed_decision on all stores (done)
- ❌ P14: Outbox table
- ❌ P15: Observation wiring
- ❌ P16: EvidenceReceipt wiring
- ❌ P17: DataOps AGE (last copilot without AGE Decision writes)
- After P14-P17 ship → L5 implementation can begin

### After Batch 11 (Next Horizon)

- **L5 implementation:** 6 new GraphStore methods + 18 conformance tests
- **S2P→AGE migration** (Phase 3 per Protocol v2 roadmap)
- **Purchasing→AGE migration** (Phase 4)
- **SOC canonical vocabulary** (Phase 5 — SOC inventory needed first)
- **Cross-copilot proof** (Phase 6 — SOC→DataOps→S2P traversal in one Cypher)
- **DI-1 Source Profiler** (greenfield — per-source trust scores)

---

## §13 — Document History

| Version | Date | Key Changes |
|---|---|---|
| v1.0–v10.0 | Feb–Mar 2026 | Initial platform build, GAE, SOC, S2P |
| v11.0–v15.0 | Mar–Apr 2026 | Framework v4, Two-Phase learning, DK calibration |
| v16.0–v19.0 | Apr–May 2026 | ci-platform, copilot-sdk, SDK copilots (Trading, DataOps, Purchasing) |
| v20.0 | May 2026 | Batch analysis, 8 design issues, 101 bugs catalogued, MAP v5.57 |
| **v21.0** | **June 1, 2026** | **Protocol v2 (26 methods, 13 tables, 88 conformance tests), Trading AGE active, L5 design spec, test suite 2.3× growth (2,764→6,241), copilot-sdk 10× growth (35→356 .py files), 55+ docs committed, Batch 11 (18 prompts) identified and sequenced** |

---

*CI Platform Insights v21.0 · June 1, 2026*
*6 repos · ~174K LOC total · 356 files in copilot-sdk alone · 6,241 tests · 26-method GraphStore Protocol v2*
*"Each verified decision permanently improves the system's judgment."*
