# RL SDK Design v1

**Status:** Design proposal; implementation intentionally not included in this change  
**Scope:** `copilot-sdk` RL sidecar and five domain integrations  
**Date:** 2026-08-31

## 1. Problem statement

RL is currently organized around the SOC service rather than the shared SDK.
SOC's `rl_engine.py` contains reward computation, an in-memory reward ledger,
exploration state, and temporal credit helpers in one service module
(`../gen-ai-roi-demo-v4-v50/backend/app/services/rl_engine.py`, lines 28-84,
151-262, and 265-507). This makes SOC the de facto owner of RL even though all
five copilots use the same judgment-memory pattern.

The current unevenness is concrete:

- SOC reward logic imports SOC severity data (`rl_engine.py`, lines 18 and
  86-102), so it is not domain-neutral.
- S2P, Trading, Purchasing, and DataOps can use `CompoundingScorer`, but domain
  feedback is not governed by one final SDK contract.
- Delayed outcomes need temporal credit; the SOC module combines chain credit
  and factor attribution in one helper (`rl_engine.py`, lines 406-528).
- The latest math synopsis says RL-directed scorer learning-rate allocation was
  negative and RL belongs in the operational evolution sidecar, not in scorer
  `eta` allocation (`docs/design/blogs/new_docs/math_synopsis_v20.md`, lines
  2349-2362 and 2436-2440).

The design moves the domain-neutral RL control plane into `copilot_sdk/rl/`.
Each copilot injects only a domain reward function. `CompoundingScorer` remains
authoritative for judgment scoring and centroid learning; RL supplies graded
feedback, temporal attribution, and conservation-governed sidecar exploration.

### Current-state audit and naming drift

An early SDK RL package already exists: `copilot_sdk/rl/reward.py`, `credit.py`,
`exploration.py`, `presets.py`, and `reward_functions.py`. It is prior art, not
the final v1 contract.

| Area | Current implementation | v1 decision |
|---|---|---|
| Reward function | `compute(recommended_action, actual_action, outcome)` (`copilot_sdk/rl/reward.py`, lines 12-24) | Target protocol receives full `decision` and `outcome`; compatibility adapter preserves old calls. |
| Reward computer | Injected function and `[0,1]` clamp (`reward.py`, lines 27-76) | Keep normalization; add range validation, version, and evidence breakdown. |
| Credit | Factor shares and explicit delayed contributors (`credit.py`, lines 10-56) | Generalize to causal decision history with discount, caps, and persistence. |
| Exploration | `select_action()` with fixed epsilon and GREEN-only exploration (`exploration.py`, lines 12-51) | Add `should_explore()` and the conservation-fraction equation; retain zero-exploration fallback. |
| Persistence | `save_ledger()` (`reward.py`, lines 78-101); ledger methods exist in `graph/protocol.py`, lines 122-131 | Use domain-scoped, idempotent reward/credit/policy ledger records. |
| Scorer integration | `CompoundingScorer` accepts RL objects (`scoring/scorer.py`, lines 119-147) | Add one SDK orchestration boundary; RL cannot bypass scorer pause or replace judgment action. |

Two requested paths are absent: `copilot_sdk/scoring/compounding.py` is
represented by `copilot_sdk/scoring/scorer.py`, and the S2P reward precursor is
`../s2p-copilot/backend/app/domains/s2p/reward.py`, not `scorer.py`. This design
uses the files that exist and records that drift explicitly.

## 2. Design goals

| ID | Goal | Acceptance condition |
|---|---|---|
| DG-1 | Any copilot injects a `DomainRewardFunction` and receives the SDK pipeline. | Construction needs no import from another copilot. |
| DG-2 | Binary SOC feedback is graded feedback's special case. | Binary output is exactly `{0,1}` after normalization. |
| DG-3 | Rewards persist through GraphStore/AGE. | Domain-stamped records survive restart and are idempotent. |
| DG-4 | Conservation bounds exploration. | Unsafe snapshots produce zero exploration; epsilon never exceeds `ε_firm★`. |
| DG-5 | Credit is temporal. | Delayed outcomes distribute discounted credit over causal prior decisions. |
| DG-6 | SDK/domain separation is strict. | Framework is in SDK; formulas remain in each copilot. |
| DG-7 | Judgment scoring remains authoritative. | RL cannot replace centroid action, mutate `η` by default, or bypass pause. |
| DG-8 | RL is explainable and governed. | Results contain formula version, evidence, conservation snapshot, provenance, and substantiation. |

## 3. Framework components (`copilot_sdk/rl/`)

### 3.1 Shared boundary types

The boundary uses JSON-like mappings so each copilot can retain its own record
shape. The SDK owns result types:

```python
Decision = Mapping[str, Any]
Outcome = Mapping[str, Any]
History = Sequence[Decision]
ConservationStatus = Mapping[str, Any]
```

`RewardResult` contains at least `reward` (normalized `[0,1]`),
`binary_reward` (`0.0` or `1.0`), `domain`, `decision_id`, `breakdown`,
`reward_version`, `provenance`, and `substantiation`.

Negative raw domain values may be accepted by an adapter for penalty-style
formulas, but canonical RL reward is `[0,1]`; raw input remains in the
breakdown. The framework never silently widens the public range.

### 3.2 `DomainRewardFunction`

```python
class DomainRewardFunction(Protocol):
    def compute_reward(
        self,
        decision: Mapping[str, Any],
        outcome: Mapping[str, Any],
    ) -> float:
        """Return a raw reward in the declared range."""

    def reward_range(self) -> tuple[float, float]:
        """Return the inclusive raw range, normally (0.0, 1.0)."""
```

The function is pure, deterministic for identical inputs, and owns only
domain-specific evidence interpretation. It does not write GraphStore, alter
centroids, select actions, or decide whether exploration is safe. The range
must be finite, ordered, and compatible with the SDK normalizer.

The current S2P class compares recommended and actual actions and uses recovery
or at-risk amount (`../s2p-copilot/backend/app/domains/s2p/reward.py`, lines
8-35). A compatibility adapter maps v1 mappings to that signature before S2P
adopts the full protocol.

### 3.3 `RewardComputer`

```python
class RewardComputer(Protocol):
    def compute(
        self,
        decision: Mapping[str, Any],
        outcome: Mapping[str, Any],
        domain_reward_fn: DomainRewardFunction,
    ) -> RewardResult:
        """Compute, validate, normalize, and explain one reward."""
```

Observable contract:

1. Call the injected function once.
2. Validate finiteness and the declared range; out-of-range is an integration
   error, not a signal to widen the range.
3. Normalize to `[0,1]`; for `(0,1)` this is identity after validation.
4. Set `binary_reward=1.0` only for normalized reward `1.0`, else `0.0`.
5. Return raw reward, normalized reward, range, IDs, domain, formula version,
   and evidence breakdown.
6. Keep computation side-effect free; persistence is a separate operation.

Recommended concrete surface:

```python
def compute(...) -> RewardResult: ...
def persist(self, store: GraphStore, result: RewardResult, *, event_id: str) -> str: ...
```

`persist()` is idempotent by `event_id` and writes through GraphStore rather
than directly to AGE or a domain database.

### 3.4 `CreditAssigner`

```python
class CreditAssigner(Protocol):
    def assign(
        self,
        decision_id: str,
        reward: float,
        history: Sequence[Mapping[str, Any]],
    ) -> dict[str, float]:
        """Return decision_id -> discounted credit for causal history."""
```

`history` is ordered causal history. Each item exposes an ID and non-negative
delay or sequence distance. Credit is `reward × γ^delay`, where `0 < γ ≤ 1`,
then subject to a configured budget/cap. Empty history returns `{}`; zero
reward produces zero credits and no write; malformed IDs are skipped and
reported in diagnostics. Results are deterministic and persistable.

The SOC mechanics of half-life 30, lookback 100, and a 0.5 chain-credit budget
(`rl_engine.py`, lines 406-411 and 485-507) become configuration rather than
SOC constants. The current finite-difference factor attribution helper
(`rl_engine.py`, lines 509-528) remains an optional diagnostic, distinct from
temporal decision credit.

Optional compatibility method:

```python
def assign_temporal(
    self,
    reward: float,
    contributors: Sequence[tuple[str, int]],
) -> list[CreditAssignment]: ...
```

### 3.5 `ExplorationPolicy`

```python
class ExplorationPolicy(Protocol):
    def should_explore(
        self,
        conservation_status: Mapping[str, Any],
        category: str,
    ) -> bool: ...

    def select_action(
        self,
        values: Sequence[float],
        *,
        conservation_status: Mapping[str, Any],
        category: str,
    ) -> ExplorationDecision: ...
```

The required equation is:

```text
ε(category, t) = ε_firm★ × (1 − conservation_fraction(category, t))
0 ≤ ε_firm★ ≤ 0.125; 0 ≤ conservation_fraction ≤ 1
```

The policy forces `ε=0` for RED, active pause, invalid/unavailable snapshot,
or insufficient category evidence. AMBER is proposal/shadow-only unless an
explicit promotion gate is enabled. GREEN is eligible but remains bounded by
`ε_firm★`.

v1 defines `conservation_fraction` centrally as consumed exploration budget
divided by allowed budget, clamped to `[0,1]`. It is not `q` and does not
replace the conservation invariant `α(t)·q(t)·V(t) ≥ θ_min`; q remains rolling
verified accuracy over the last 400 decisions (`math_synopsis_v20.md`, lines
1165-1181).

The current SDK policy uses fixed epsilon and disables every non-GREEN status
(`copilot_sdk/rl/exploration.py`, lines 12-51). That safe behavior is retained
as fallback while the fractional equation is introduced.

### 3.6 SDK orchestration boundary

An internal `RLCoordinator` coordinates the components; it is not a new domain
API:

```text
CompoundingScorer.score -> GraphStore decision
verified outcome -> RewardComputer.compute
                -> persist reward ledger row
                -> CreditAssigner.assign over causal history
                -> persist credit rows
                -> update exploration state only if gate permits
                -> CompoundingScorer.learn for judgment-memory update
```

`CompoundingScorer.learn()` already writes outcomes and then invokes RL hooks
(`copilot_sdk/scoring/scorer.py`, lines 1054-1060 and 1124-1135). v1 preserves
that boundary: RL does not route reward into scorer `eta` by default, replace
centroid-selected action, or bypass conservation pause.

## 4. Domain reward functions

Every function returns a raw value in `(0,1)` unless its declared range says
otherwise. The SDK normalizes and records the formula version.

| Copilot | Function | Reward definition | Evidence |
|---|---|---|---|
| SOC | `SOCBinaryRewardFunction` | `1.0` when actual triage action equals the verified correct action; `0.0` otherwise. | Verified analyst outcome, recommended/actual action, category, severity. |
| S2P | `S2PGradedRewardFunction` | `clip(exception_accuracy × savings_ratio, 0, 1)`, with savings ratio based on recovered value divided by amount at risk. | Invoice/decision ID, recovery, amount at risk, verification evidence. |
| Trading | `TradingPnLRewardFunction` | `clip(risk_adjusted_PnL / max_expected, 0, 1)`, accounting for costs, tail exposure, and incomplete mark-to-market windows. | Trade ID, realized/marked P&L, risk budget, holding period, costs, regime. |
| Purchasing | `PurchasingCostImpactRewardFunction` | `clip(cost_impact / max_cost, 0, 1)`, adjusted for realized savings, quality, and delivery penalty. | Order ID, baseline/realized cost, quality/service verification. |
| DataOps | `DataOpsResolutionRewardFunction` | `clip(resolution_time_improvement × blast_radius_reduction, 0, 1)`; no improvement is zero. | Incident/job ID, time baseline/current, affected entities, recovery validation. |

Formula ownership is deliberately domain-local. The SDK owns range checking,
normalization, binary projection, persistence, and governance. Insufficient
evidence produces zero/unknown according to the domain contract; it must never
be converted into a success reward.

### Binary compatibility

SOC wraps its existing correctness outcome as:

```text
correct -> 1.0
incorrect -> 0.0
```

The existing SOC module can produce negative raw penalty-style values
(`rl_engine.py`, lines 86-136). The adapter preserves old binary learning
semantics at the compatibility boundary while canonical v1 reward remains
`[0,1]`; asymmetric penalties belong in outcome/learning policy, not an
undocumented range change.

## 5. GraphStore persistence

Judgment Memory v2.9 defines Decision and Outcome data as shared GraphStore
state and includes reward in the outcome model (`docs/design/judgment_memory_v2_9.md`,
lines 346-367 and 710-717). GraphStore already exposes domain-scoped ledger
methods `save_ledger`, `get_ledger`, `list_ledgers`, and `delete_ledger`
(`copilot_sdk/graph/protocol.py`, lines 122-131).

v1 ledger records contain:

```text
entry_id, event_id, domain, decision_id
reward_raw, reward_normalized, binary_reward, reward_range
reward_formula_version, credit_assignments
exploration_used, exploration_epsilon, conservation_snapshot
metadata, provenance, substantiation, created_at, schema_version
```

Rules:

1. Every read/write carries `domain`; cross-domain ledger access is rejected.
2. Records are append-only from the product perspective. Delete is limited to
   domain reset and audit-approved cleanup.
3. Replaying `event_id` returns the original entry and never duplicates credit.
4. SQLite and AGE adapters provide equivalent semantics.
5. Persistence failure prevents posterior advancement and returns a retryable
   result; reward must not appear successfully learned if it was not durable.
6. Reward summaries are not automatically product claims; they require
   provenance and substantiation labels.

## 6. Migration: SOC `rl_engine.py` to SDK

### 6.1 What moves, stays, and is removed

| Component | Destination | Migration rule |
|---|---|---|
| `RewardComputer` | SDK | Replace SOC domain branching with injection. |
| `CreditAssigner` | SDK | Generalize chain credit; keep factor attribution optional. |
| `ExplorationPolicy` | SDK | Preserve safe status fallback, then add conservation-fraction epsilon. |
| Reward persistence | SDK + GraphStore | Replace SOC-only/in-memory ownership with domain-scoped ledger records. |
| Learning integration | SDK around `CompoundingScorer` | Keep scorer centroid update and conservation pause authoritative. |
| SOC reward formula | SOC | Small `SOCBinaryRewardFunction`; SDK has no SOC imports. |
| S2P reward formula | S2P | Current reward class becomes an adapter, then adopts v1 mapping signature. |
| `_ContextualRewardFunction` bridge | Removed after S2P migration | One-release adapter may remain only for rollback. |
| SOC `rl_engine.py` | Reduced, then deleted | First become compatibility facade importing SDK components. |

### 6.2 Compatibility sequence

1. Freeze SOC action, binary outcome, posterior, credit, exploration, and
   conservation trajectories as replay fixtures.
2. Add SDK adapters for current SOC signatures with no domain behavior change.
3. Route SOC imports through the facade; move severity lookup into the SOC
   domain function.
4. Persist reward, credit, and exploration state through GraphStore; compare
   SQLite/AGE replay results.
5. Migrate S2P from `_ContextualRewardFunction` to its injected function.
6. Enable Trading, Purchasing, and DataOps with domain evidence adapters.
7. Remove compatibility code only after all route, replay, and conformance
   tests pass.

### 6.3 Safety constraints

- RL remains disabled by default until a domain has reward-quality fixtures and
  conservation tests.
- Preserve SOC G1: exploration is proposal/shadow-only until strict production
  enablement (`judgment_memory_v2_9.md`, lines 1449-1452).
- Do not route reward into centroid `eta` by default; the latest math synopsis
  reports that line definitively negative (`math_synopsis_v20.md`, lines
  2349-2362).
- Domain reward functions do not write GraphStore, set conservation state, or
  select actions.
- Conservation RED/pause wins over reward magnitude.

## 7. Phased execution plan

### RL-0 — Contract freeze and replay fixtures

**Depends on:** none. **Owner:** SDK plus domain owners.  
Freeze v1 types, formula-version registry, SOC replay corpus, and the five
domain outcome schemas. Exit when SOC trajectory is reproducible and evidence
requirements are documented.

### RL-1 — SDK framework

**Depends on:** RL-0.  
Implement canonical interfaces, normalization, temporal credit,
conservation-bounded exploration, GraphStore ledger adapter, idempotency, and
coordinator. Add 20+ focused tests for reward compute, binary/graded behavior,
range validation, credit, persistence, exploration, and conservation bounds.
Exit requires SDK-only imports and tests with no domain dependencies.

### RL-2 — SOC extraction

**Depends on:** RL-1; parallel with RL-3/RL-4.  
Replace internal implementations with SDK imports, retain
`SOCBinaryRewardFunction`, and preserve G1 proposal/shadow behavior. Exit when
SOC routes and replay tests prove the same action/reward/posterior trajectory.

### RL-3 — S2P graded integration

**Depends on:** RL-1; parallel with RL-2/RL-4.  
Replace `_ContextualRewardFunction`, define recovery/savings evidence, and
persist graded rewards plus temporal credit. Exit when S2P tests prove graded
rewards, delayed credit, and unchanged `θ_min` behavior.

### RL-4 — Trading, Purchasing, and DataOps

**Depends on:** RL-1; parallel with RL-2/RL-3.  
Implement the three domain functions and evidence adapters in shadow mode.
Exit when all five copilots compute, persist, replay, and audit through the
same coordinator.

### RL-5 — Promotion and production enablement

**Depends on:** RL-2, RL-3, RL-4.  
Compare shadow versus baseline, verify headroom and rollback, and verify
SQLite/AGE parity. Enable execution only after domain evidence review; no
unsubstantiated improvement claim is permitted.

Dependency ordering:

```text
RL-0 -> RL-1 -> {RL-2, RL-3, RL-4} -> RL-5
```

## 8. Test contract

### 8.1 Reward

- Binary functions return only `0.0` or `1.0`.
- Graded functions preserve distinct values such as `.25`, `.60`, and `1.0`.
- Raw value, normalized value, range, formula version, and evidence breakdown
  are retained.
- NaN, infinity, reversed range, and out-of-range values fail closed.
- Compute calls the domain function once and performs no persistence.

### 8.2 Credit

- Credit follows `reward × γ^delay` and respects budget/cap.
- Empty history and zero reward produce no credit writes.
- Invalid IDs/delays are deterministic and diagnosed.
- History is causal and domain-scoped; unrelated decisions receive no credit.
- Replaying an outcome never duplicates credit.
- Factor attribution is distinguishable from temporal decision credit.

### 8.3 Exploration and conservation

- `ε ≤ ε_firm★` for every category and snapshot.
- `ε=0` for RED, active pause, invalid snapshot, and insufficient evidence.
- The equation is tested at conservation fractions `0`, `.25`, `.5`, and `1`.
- AMBER produces proposal/shadow output unless explicitly promoted.
- Seeded policy replay is deterministic when deterministic mode is requested.
- Exploration cannot mutate `θ_min`, `α`, `q`, or `V`.

### 8.4 Persistence and integration

- SQLite and AGE round-trip equivalent reward/credit records.
- Ledger rows are domain-stamped and idempotent by event ID.
- Restart/replay reconstructs reward history and exploration state.
- Persistence failure prevents posterior advancement.
- `CompoundingScorer.learn()` still updates centroids and honors pause.
- SOC binary reward produces the pre-migration IKS/action trajectory.
- S2P graded reward removes the contextual bridge and preserves recovery/risk
  semantics.
- Trading, Purchasing, and DataOps reject insufficient evidence and honor
  their declared ranges.
- `θ_min` is unchanged before/after reward, credit, and exploration operations.

### 8.5 Quality and governance

- SDK import graph has no copilot application imports.
- Domain functions have no GraphStore writes or conservation bypass.
- Required tests use real scorer/store/conservation fixtures, not forbidden
  fakes or mocks.
- User-facing summaries include provenance and substantiation.
- Shadow, promotion, and rollback records are auditable and do not elevate
  synthetic evidence into a production claim.

## 9. Dependency map

| Work item | Depends on | Parallelism | External dependency |
|---|---|---|---|
| RL-0 | None | Immediate | Domain agreement on evidence |
| RL-1 | RL-0 | Foundation | Existing GraphStore/scorer boundary |
| RL-2 | RL-1 | Parallel with RL-3/RL-4 | SOC routes and replay fixtures |
| RL-3 | RL-1 | Parallel with RL-2/RL-4 | S2P recovery/savings evidence |
| RL-4 | RL-1 | Parallel with RL-2/RL-3 | Three domain outcome adapters |
| RL-5 | RL-2, RL-3, RL-4 | Final gate | Governance, pilot substantiation, AGE parity |

No new third-party dependency is required. The framework uses existing SDK
protocols and GraphStore adapters; domain packages own their formulas.

## 10. Open decisions and non-goals

1. v1 canonical reward is `[0,1]`; raw negative penalties are adapter policy.
2. Credit may be separate rows or embedded list if domain-scoped and idempotent.
3. The consumed exploration-budget source must be calibrated against live
   conservation snapshots before production enablement.
4. RL-directed scorer `eta` remains out of scope until a new gated experiment
   reverses the existing negative result.
5. RL may propose an operational variant, but never replaces the centroid
   judgment action.
6. Existing SOC and S2P implementations are migration inputs, not SDK
   dependencies.

## Appendix A — audited sources

- SOC RL: `../gen-ai-roi-demo-v4-v50/backend/app/services/rl_engine.py`, lines 28-84, 151-262, 265-507.
- SDK scorer: `copilot_sdk/scoring/scorer.py`, lines 119-147, 241-364, 912-1135.
- SDK RL package: `copilot_sdk/rl/reward.py`, `credit.py`, `exploration.py`, `presets.py`, and `reward_functions.py`.
- GraphStore ledger: `copilot_sdk/graph/protocol.py`, lines 122-131.
- S2P reward: `../s2p-copilot/backend/app/domains/s2p/reward.py`, lines 8-35.
- Judgment Memory: `docs/design/judgment_memory_v2_9.md`, lines 346-367, 565-639, and 710-717.
- Math synopsis: `docs/design/blogs/new_docs/math_synopsis_v20.md`, lines 1155-1181 and 2349-2362.
- Innovation note: `docs/design/blogs/new_docs/innovation_note_v28.md`, lines 34-36, 90-103, and 199-206.
- AGE unification: `docs/design/age_unification_complete_design_v1.md`, lines 151-185 and 220-249.
