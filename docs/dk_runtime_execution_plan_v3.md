# DK Runtime Execution Plan v3 — 5 Prompts to Full Intelligence Loop
**Date:** June 6, 2026
**Priority:** P1 — execute BEFORE all other roadmap items
**Goal:** All SDK copilots compute, persist, and score with learned DK weights
**Timeline:** ~5-6 working days
**Authority:** dk_runtime_fix_architecture_v3.md + p_welford_architecture_decision.md
**Scan status:** Prompt 0 discovery scan COMPLETE. All GAE parameters confirmed.

---

## Why This Runs First

DK runtime is the P1 gap that makes or breaks the product's core claims.
Without it, "compounding intelligence" is aspirational for 5 of 5
copilots. Every other roadmap item (migration, SOC Option C, demo build,
blog publish, arxiv submission) is LESS urgent than making the
intelligence loop actually run. Those items improve a working product;
this item makes the product work.

**Everything else waits until these 5 prompts are done.**

---

## Prerequisites (verify BEFORE Prompt 0)

DK estimation reads verified decisions. If ghost decisions contaminate
the verified pool, DK learns from garbage.

| Prerequisite | MAP# | Status | Verify |
|---|---|---|---|
| **CONS-V-FIX** (V = verified only) | #111 | Must be SHIPPED | `curl http://localhost:8010/api/conservation/status` — total_decisions should match verified count, not inflated by ghosts |
| **OBSERVATION-WIRING** (preview → write_observation) | #115 | Must be SHIPPED | `grep -rn "write_observation" copilot-sdk/` shows preview using observation path |
| **BUNDLE-REGEN** (Trading d=10 bundle) | #102 | Must be SHIPPED | Trading cold-start produces d=10 centroids |
| **GAE editable install** | — | ✅ DONE | `pip install -e ../graph-attention-engine-v50` verified — GAE imports from copilot-sdk |

**If ANY prerequisite is not shipped, fix it BEFORE starting Prompt 0.**
DK estimation on ghost-polluted data produces wrong weights — the
intelligence loop would "learn" from noise, which is worse than static priors.

---

## Exact GAE Parameters (from Prompt 0 scan — CONFIRMED)

```python
from gae.profile_scorer import LearningStrategy, ProfileScorer
from gae.dk_estimator import CoordinateDescentEstimator

# EXACT parameters for_soc_twophase() uses — use these in from_preset():
strategy = LearningStrategy(
    phase_policy=DecisionCountPolicy(n=200),   # 200 decisions before VARIANCE_LEARNING
    dk_estimator=CoordinateDescentEstimator(),  # coordinate descent on buffered decisions
    shrinkage_schedule=FixedAlpha(0.5),         # 50% prior + 50% data = graduation
)
# Additional ProfileScorer params:
# eta_override=0.01           (v14 canonical)
# auto_pause_on_amber=True    (conservation integration)
```

**Phase behavior (GAE's designed architecture, NOT custom code):**
- Category starts in `MEAN_CONVERGENCE`: `update()` does centroid learning only
- After 200 verified decisions: `CategoryState.freeze()` → `VARIANCE_LEARNING`
- In `VARIANCE_LEARNING`: `update()` buffers decisions for DK estimation
- `reestimate_dk()` runs `CoordinateDescentEstimator.estimate()` on buffered decisions
- `FixedAlpha(0.5)` shrinks results: `applied = 0.5 * prior + 0.5 * estimated`
- `score()` uses `_dk_weights` when category is in `VARIANCE_LEARNING`

**No custom cadence counter needed.** Call `reestimate_dk()` after every
learn. It returns early when no category is in VARIANCE_LEARNING
(negligible cost). `DecisionCountPolicy(n=200)` controls the phase
transition — not our code.

**CoordinateDescentEstimator.estimate() API (from scan):**
```python
estimate(
    decisions,     # sequence of (factor_vector, category_index, correct_action_index)
    centroids,     # (C, A, D) or (A, D) numpy array
    n_categories,  # int
    n_dims,        # int
) -> np.ndarray   # shape (n_categories, n_dims)
```

---

## Prompt Sequence

```
Prompt 0: DISCOVERY SCAN           (30 min, no code changes) ✅ COMPLETE
Prompt 1: P-WELFORD-A              (0.5d, storage/protocol)
Prompt 2: P-DK-RUNTIME-FULL        (3-4d, split into 3 sub-prompts)
  Prompt 2a: CONSTRUCTION CHANGE   (1d, construction + behavioral gate)
  ──── GATE: behavioral test proves DK weights change with data ────
  Prompt 2b: PERSISTENCE + WELFORD (1d, dk_persistence.py + L5 writes)
  Prompt 2c: ROUTER + STARTUP      (1d, scoring_router wiring + app init)
Prompt 3: P26 STARTUP-READ         (0.5d, warm-start from L5)
Prompt 4: P27 FULL-FLOW-TEST       (0.5d, L5 completion gate)
          C9: L5 PROOF             (manual, 1h)
```

---
## Prompt 0 — Discovery Scan (30 min, no code changes)

**Purpose:** Determine exact constructor parameters for ProfileScorer
with full LearningStrategy. This is information gathering — Codex
reads code and reports, does not modify anything.

**Prompt:**

```
/model gpt-5.3
Echo the current model name in the first line of output.

TASK: Discovery scan only. Read code and report findings. NO code changes.
TASK TYPE: Code analysis.

WORKING DIRECTORY:
C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\kaggle_experiments\claude_projects

RUN THESE SCANS AND REPORT OUTPUT:

SCAN 1 — ProfileScorer constructor and for_soc_twophase:

Set-Location "$env:CLAUDE_PROJECTS\graph-attention-engine-v50"
python -c @"
import inspect
from gae.profile_scorer import ProfileScorer

print('=== for_soc_twophase FULL SOURCE ===')
print(inspect.getsource(ProfileScorer.for_soc_twophase))

print('=== __init__ FULL SOURCE ===')
print(inspect.getsource(ProfileScorer.__init__))

print('=== reestimate_dk FULL SOURCE ===')
print(inspect.getsource(ProfileScorer.reestimate_dk))

print('=== score DK-RELEVANT LINES ===')
src = inspect.getsource(ProfileScorer.score)
for i, line in enumerate(src.split(chr(10))):
    if any(k in line for k in ['_dk_weights', 'VARIANCE', '_learning_strategy', 'learning']):
        print(f'  L{i}: {line.strip()}')
"@

SCAN 2 — LearningStrategy class:

python -c @"
import inspect, sys
sys.path.insert(0, '.')
# Find LearningStrategy - may be in profile_scorer or separate module:
try:
    from gae.profile_scorer import LearningStrategy
    print('=== LearningStrategy SOURCE ===')
    print(inspect.getsource(LearningStrategy))
except ImportError:
    print('LearningStrategy not in profile_scorer')
    # Search other modules:
    import os
    for f in os.listdir('gae'):
        if f.endswith('.py'):
            src = open(f'gae/{f}').read()
            if 'class LearningStrategy' in src or 'VARIANCE_LEARNING' in src:
                print(f'FOUND in gae/{f}')
                for i, line in enumerate(src.split(chr(10))):
                    if 'LearningStrategy' in line or 'VARIANCE' in line:
                        print(f'  L{i}: {line}')
"@

SCAN 3 — CoordinateDescentEstimator.estimate() signature:

python -c @"
import inspect
from gae.dk_estimator import CoordinateDescentEstimator
print('=== estimate FULL SOURCE ===')
print(inspect.getsource(CoordinateDescentEstimator.estimate))
print('=== __init__ ===')
print(inspect.getsource(CoordinateDescentEstimator.__init__))
"@

SCAN 4 — Can GAE be imported from copilot-sdk?

Set-Location "$env:CLAUDE_PROJECTS\copilot-sdk"

# First: install GAE as an editable package (correct dependency management):
pip install -e ../graph-attention-engine-v50 --break-system-packages 2>&1 | Select-Object -Last 3

# Then verify import:
python -c @"
try:
    from gae.dk_estimator import CoordinateDescentEstimator
    from gae.profile_scorer import ProfileScorer
    print('GAE IMPORT: OK')
    print(f'ProfileScorer methods: {[m for m in dir(ProfileScorer) if not m.startswith("_")]}')
except ImportError as e:
    print(f'GAE IMPORT FAILED: {e}')
    print('RESOLUTION: GAE may need a setup.py/pyproject.toml for editable install')
    print('Create a minimal pyproject.toml in graph-attention-engine-v50/ if missing')
"@

SCAN 5 — Current from_preset() and CompoundingScorer.learn():

python -c @"
import inspect
from copilot_sdk.scoring.scorer import CompoundingScorer
print('=== from_preset FULL SOURCE ===')
print(inspect.getsource(CompoundingScorer.from_preset))
print('=== learn FULL SOURCE ===')
print(inspect.getsource(CompoundingScorer.learn))
print('=== __init__ ===')
print(inspect.getsource(CompoundingScorer.__init__))
"@

SCAN 6 — What get_verified_decisions returns:

python -c @"
import inspect
from copilot_sdk.graph.sqlite_store import SQLiteGraphStore
print('=== get_verified_decisions ===')
print(inspect.getsource(SQLiteGraphStore.get_verified_decisions))
"@

OUTPUT REQUIRED:
Report ALL scan output. Then answer these 5 questions:

Q1: What parameters does for_soc_twophase() pass to ProfileScorer.__init__
    that from_preset() does NOT? List each with its default value.

Q2: What is the LearningStrategy constructor signature? What does
    VARIANCE_LEARNING contain (set of category indices)?

Q3: What does CoordinateDescentEstimator.estimate() expect as input?
    (exact parameter names + types)

Q4: Does GAE import from copilot-sdk? If not, what path fix is needed?

Q5: What fields does get_verified_decisions() return per decision?
    (exact dict keys)

DO NOT MODIFY ANY CODE. Report only.
```

**Gate:** If Scan 4 fails (GAE import), resolve before proceeding:
1. Check if `graph-attention-engine-v50/` has a `setup.py` or `pyproject.toml`
2. If not, create a minimal `pyproject.toml` with `[project] name="gae"`
3. Run `pip install -e ../graph-attention-engine-v50`
4. Verify `from gae.dk_estimator import CoordinateDescentEstimator` works

Do NOT use `sys.path.insert` — that's brittle, CWD-dependent, and
breaks test suites. GAE must be a proper importable package, which
also aligns with the open-source (Track A) plan.


---

## Prompt 1 — P-WELFORD-A: Storage Extension (0.5d)

**Full spec:** p_welford_architecture_decision.md §P-WELFORD-A

**Summary:** Extend L5LearningStore.update_dk_weights() with optional
keyword-only `welford_state`, `n_confirmed`, `n_overridden`,
`entity_group`. Add nullable columns to SQLite, InMemory, AGE stores.
6 tests. Backward-compatible (old rows return welford_state=None).

**Prerequisite:** Prompt 0 scan complete. ✅

**Acceptance:** All existing tests pass + 6 new Welford storage tests.

---

## Prompt 2 — P-DK-RUNTIME-FULL (3-4d, split into 3 sub-prompts)

**Full spec:** dk_runtime_fix_architecture_v3.md
**This is the prompt sequence that makes the product's claims true.**

### Prompt 2a — Construction Change + Behavioral Gate (1d)

**The crux.** If this is wrong, everything built on it is wrong.

**Scope:**
1. Modify `CompoundingScorer.from_preset()` to construct `ProfileScorer`
   with full `LearningStrategy` + `CoordinateDescentEstimator`.
   Categories start in `MEAN_CONVERGENCE` and transition to
   `VARIANCE_LEARNING` via `DecisionCountPolicy(n=200)` — this is
   GAE's designed phase gate, not custom code.
2. Add `reestimate_dk_if_due()` method that calls
   `self._scorer.reestimate_dk()` after every learn. Returns early
   if no category is in `VARIANCE_LEARNING` yet (negligible cost).
   No custom cadence counter — GAE's phase policy controls timing.
3. Add accessors: `get_dk_weights()`, `get_verified_count()`.

**Exact construction change in `from_preset()`:**
```python
# BEFORE (current — no DK learning):
self._scorer = ProfileScorer(mu=centroids, actions=actions, categories=categories)

# AFTER (full intelligence loop):
from gae.dk_estimator import CoordinateDescentEstimator
strategy = LearningStrategy(
    phase_policy=DecisionCountPolicy(n=200),
    dk_estimator=CoordinateDescentEstimator(),
    shrinkage_schedule=FixedAlpha(0.5),
)
self._scorer = ProfileScorer(
    mu=centroids, actions=actions, categories=categories,
    learning_strategy=strategy,
    eta_override=0.01,
    auto_pause_on_amber=True,
)
# If for_soc_twophase() hardcodes SOC-specific constants, use direct
# constructor with these params instead. Either way: full strategy.
```

**File:** `copilot_sdk/scoring/scorer.py` ONLY.

**CoordinateDescentEstimator.estimate() API (from scan):**
```python
estimate(
    decisions,     # sequence of (factor_vector, category_index, correct_action_index)
    centroids,     # (C, A, D) or (A, D) numpy array
    n_categories,  # int
    n_dims,        # int
) -> np.ndarray   # shape (n_categories, n_dims)
```

**Verified-decision data (from scan — `get_verified_decisions()` keys):**
```
decision_id, domain, entity_id, category, category_index,
factors, factor_vector, recommended_action, recommended_index,
confidence, probabilities, status, metadata, created_at,
actual_action, actual_index, is_correct, verified_at,
context, outcome_metadata
```

**THE BEHAVIORAL GATE (must pass before Prompt 2b):**

```python
def test_dk_learning_actually_works():
    """THE gate test. Proves the intelligence loop works, not just the pipeline.

    Feed a dataset where factor 0 is pure noise (random uniform)
    and factor 1 is highly predictive (correlates with correct action).
    Must run 200+ decisions to pass DecisionCountPolicy phase gate,
    then verify DK weights change.

    (a) factor 0's DK weight drops measurably below the prior
    (b) factor 1's DK weight rises measurably above the prior
    (c) scoring output shifts with the updated weights
    """
    scorer = CompoundingScorer.from_preset("trading", graph_store=store)

    # Phase 1: 200 decisions in MEAN_CONVERGENCE (centroid-only learning)
    for i in range(200):
        correct = (i % 2 == 0)
        factors = {
            "signal_alignment": random.random(),              # NOISE — random
            "market_regime": 0.8 if correct else 0.2,         # SIGNAL — predictive
            # ... other factors with moderate signal
        }
        result = scorer.score(category="momentum", factors=factors)
        scorer.learn(decision_id=result.decision_id,
                     actual_action="buy" if correct else "hold",
                     outcome="correct" if correct else "incorrect")

    # Category should now be in VARIANCE_LEARNING
    scorer.reestimate_dk_if_due()

    # Phase 2: 50 more decisions in VARIANCE_LEARNING (DK estimation active)
    for i in range(50):
        # ... same pattern
        result = scorer.score(category="momentum", factors=factors)
        scorer.learn(...)

    scorer.reestimate_dk_if_due()
    learned_weights = scorer.get_dk_weights()
    assert learned_weights is not None, "DK weights should exist after VARIANCE_LEARNING"

    # (a) Noisy factor weight should be lower
    # (b) Signal factor weight should be higher
    # (c) Scoring output should differ from prior-only scoring
    # Exact assertions depend on weight matrix structure — see (C, d) shape
```

**Additional test: FixedAlpha(0.5) shrinkage verification:**

```python
def test_dk_shrinkage_via_fixed_alpha():
    """FixedAlpha(0.5) means DK weights = 50% prior + 50% data-driven.
    This IS the 'graduating from domain prior to firm-specific' mechanism.

    At N=210 (just entered VARIANCE_LEARNING + 10 decisions): weights
    are 50% prior + 50% of a small dataset (close to prior).
    At N=410 (200 more decisions in VARIANCE_LEARNING): weights are
    50% prior + 50% of a larger dataset (more data-driven, but still
    bounded by alpha=0.5).

    The FixedAlpha(0.5) blend ensures DK never fully abandons the prior.
    """
    scorer = CompoundingScorer.from_preset("trading", graph_store=store)

    # Phase 1: 200 decisions → MEAN_CONVERGENCE → VARIANCE_LEARNING
    for i in range(200):
        # ... score + learn
        pass

    # 10 decisions in VARIANCE_LEARNING
    for i in range(10):
        # ... score + learn with noisy factor 0, signal factor 1
        pass
    scorer.reestimate_dk_if_due()
    weights_210 = scorer.get_dk_weights()

    # 200 more decisions in VARIANCE_LEARNING
    for i in range(200):
        # ... score + learn with same pattern
        pass
    scorer.reestimate_dk_if_due()
    weights_410 = scorer.get_dk_weights()

    # More data = more divergence from prior (within 50% alpha constraint)
    # Both should exist and differ
    assert weights_210 is not None
    assert weights_410 is not None
    # weights_410 should show more separation between noisy/signal factors
```

**Gate: If G1 + G2 do not pass, DO NOT proceed to Prompt 2b.**
The GAE machinery (DecisionCountPolicy + FixedAlpha + CoordinateDescentEstimator)
must produce the expected behavior. If it does not, investigate the GAE
estimator — do not work around it.

**Prompt 2a tests (4):**

| # | Test | What it proves |
|---|---|---|
| G1 | `test_dk_learning_actually_works` | **THE gate.** Noisy factor down-weighted, signal factor up-weighted, scoring shifts. |
| G2 | `test_dk_shrinkage_via_fixed_alpha` | FixedAlpha(0.5) graduation: 50% prior + 50% data. More data = more divergence. |
| 3 | `test_dk_phase_transition` | After 200 decisions, category enters VARIANCE_LEARNING. Before 200: centroid-only. |
| 4 | `test_dk_reestimate_early_return` | `reestimate_dk_if_due()` returns early when no category in VARIANCE_LEARNING (fast, no-op). |

### ──── GATE: Prompt 2a behavioral tests G1+G2 must pass ────

### Prompt 2b — Persistence + Welford (1d)

**Scope:**
1. Create `copilot_sdk/scoring/dk_persistence.py`:
   - `WelfordAccumulator` class (online mean + M2)
   - `DKWelfordTracker` class (confirmed + overridden + all)
   - `persist_dk_after_reestimate()`: reads weights FROM scorer,
     writes to L5 with Welford state. Non-fatal.
2. Follows **persist-before-cache ordering** (Standing Rule #48):
   persist to L5 store FIRST, then update cache/state. If both fail,
   raise. If L5 fails but scorer has weights, log error and continue
   (scorer is authoritative for scoring; L5 is for audit/restart).

**File:** `copilot_sdk/scoring/dk_persistence.py` (NEW)

**Prompt 2b tests (5):**

| # | Test | What it proves |
|---|---|---|
| 5 | `test_welford_accumulator_math` | Mean + M2 match batch numpy |
| 6 | `test_welford_confirmed_overridden_split` | is_correct routes correctly |
| 7 | `test_welford_roundtrip_via_state` | Serialize/deserialize matches |
| 8 | `test_persist_dk_reads_from_scorer` | Persistence reads scorer's weights, doesn't compute independently |
| 9 | `test_persist_dk_nonfatal` | L5 failure → scoring continues |

### Prompt 2c — Router Wiring + App Startup (1d)

**Scope:**
1. Wire inline DK persistence in `scoring_router.py` after conservation
   L5 write. After every learn: call `scorer.reestimate_dk_if_due()`,
   then if weights updated, call `persist_dk_after_reestimate()`.
   Same non-fatal pattern as P25b.
2. Wire same in S2P `s2p.py`.
3. App startup: Welford tracker initialization + warm-start from L5.

**Files:** `scoring_router.py`, `s2p.py`, Trading/Purchasing/DataOps/S2P `main.py`

**Prompt 2c tests (5):**

| # | Test | What it proves |
|---|---|---|
| 10 | `test_learn_persists_dk_weights_to_l5` | After 200+ learns (phase transition), L5 has DK weights |
| 11 | `test_learn_dk_includes_welford_state` | L5 DK entry has Welford (6 vectors) |
| 12 | `test_learn_dk_no_store_silent` | learning_store=None → no error |
| 13 | `test_dk_welford_warm_start` | Tracker restored from L5 on startup |
| 14 | `test_dk_weights_activated_in_scorer` | Scorer's own `_dk_weights` updated by `reestimate_dk()`, not external injection |

### Full suite runs

```powershell
Set-Location "$env:CLAUDE_PROJECTS\copilot-sdk"
python -m pytest tests/ -q --timeout=120
python -m pytest apps/trading/backend/tests/ -q --timeout=120
python -m pytest apps/purchasing/backend/tests/ -q --timeout=120
python -m pytest apps/dataops/backend/tests/ -q --timeout=120

Set-Location "$env:CLAUDE_PROJECTS\s2p-copilot\backend"
python -m pytest tests/ -q --timeout=120
```

### Stop conditions

- Do NOT modify GAE library code
- Do NOT create a parallel DK computation path (no external bridge estimator)
- Do NOT inject _dk_weights via private attribute assignment
- Do NOT broaden GraphStore
- Do NOT change conservation formulas
- If GAE import fails → STOP, resolve path, report

---

## Prompt 3 — P26: Startup Read (0.5d)

**Scope:** On copilot startup, read from L5 store:
- Centroids → populate scorer centroids (if available)
- DK weights + Welford → populate scorer DK weights + tracker
- Conservation state → populate conservation monitor

If AGE/L5 unavailable → fall back to SQLite checkpoint or cold-start
defaults. Status must indicate source (AGE vs SQLite vs cold-start).

**Tests:**
- `test_startup_loads_dk_from_l5` — DK weights survive restart
- `test_startup_loads_welford_from_l5` — Welford state survives restart
- `test_startup_loads_conservation_from_l5` — conservation survives restart
- `test_startup_fallback_on_l5_failure` — cold-start if L5 unavailable
- `test_startup_status_indicates_source` — status reports AGE/SQLite/cold

---

## Prompt 4 — P27: Full Flow Integration Test (0.5d)

**Scope:** End-to-end test that verifies the COMPLETE L5 schema:

```
score() → learn() → centroid updated (MEAN_CONVERGENCE phase)
                   → after 200 decisions: phase transition to VARIANCE_LEARNING
                   → DK re-estimated via reestimate_dk()
                   → conservation state persisted
                   → Welford accumulators updated
                   → ALL nodes readable from L5 store
                   → SHAPED_BY edge (centroid → decision)
                   → TRIGGERED_BY edge (conservation → decision, on transition)
```

**Key tests:**
- Test 58: `test_dk_welford_storage_roundtrip` — write + read Welford
- Test 59: `test_full_learn_flow_writes_all_three` — 200+ learn calls
  produce Centroid + DKWeight + ConservationState in L5, with edge
  assertions

**After P27 passes → C9 manual gate.**

---

## C9 — L5 Cross-Copilot Proof (manual, 1h)

Query the AGE graph:

```powershell
# All 5 domains present with L5 nodes:
# (run via psql or AGEClient)

MATCH (c:L5Centroid) RETURN c.domain, count(c) ORDER BY c.domain
MATCH (w:L5DKWeight) RETURN w.domain, count(w) ORDER BY w.domain
MATCH (cs:L5ConservationState) RETURN cs.domain, cs.status ORDER BY cs.domain
```

**Pass criteria:** 5 domains × 3 node types = 15 cells populated.
DKWeight nodes have welford_state (not null). ConservationState has
valid status. Centroids have count > 0.

**Deliverable:** L5 proof report. L5 COMPLETE.

---

## What Runs AFTER These 5 Prompts

| Item | Effort | Why it can wait |
|---|---|---|
| P-DK-RUNTIME-SOC | 1-2d | SOC has different construction path. SDK first. |
| P-CENTROID-L5-WIRE | 1d | Centroids work via checkpoints. L5 adds auditability. |
| #131 SQLITE-TO-AGE-MIGRATION | 2-3d | Historical data → AGE. Requires L5 complete. |
| #132 SOC-OPTION-C | 2-3d | SOC α = coverage. Requires L5 complete. |
| #133 L5+ PROOF | 0.5d | Full common data platform proof. |
| Demo build (#120-#127) | 11-16d | Requires L5+ complete. |
| Blog/arxiv publish | Founder action | Gated on **C9 + #132** (see below). |

**None of these run until Prompts 0-4 are done and C9 passes.**

### Updated gate language — C9 is upstream of EVERYTHING

The blog's publish gate was previously "Option C (#132) only." This
is wrong. C9 is what makes the 288-moat and the Mirror TRUE:

| Gate | What it unblocks | Why |
|---|---|---|
| **C9 (L5 COMPLETE)** | 288-moat claim, Mirror demo beat, trust-trap discovery claim, "compounding intelligence" across SDK copilots | Until C9, DK weights are static priors. The 288 is actually 144. The Mirror shows domain design, not learned insight. |
| **C9 + #132** | Blog publish, arxiv submission | Blog claims 288 + SOC conservation. Both must be true. |
| **C9 + #132 + demo build** | LOOM-V1 (#88) | Demo shows learned trust traps + correct SOC conservation numbers. |

A buyer who deploys today and inspects DK weights sees the domain
prior — exactly the over-claim we hedged against in the 288-guardrails.
C9 is what makes the hedge unnecessary.

---

## Discovery Scan Results — Decision Summary (11 questions)

| Q | Question | Answer | Source |
|---|---|---|---|
| 1 | DK affect live scoring? | **YES** | Architecture v3 decision |
| 2 | Which option? | **A — for_soc_twophase() params** | Architecture v3 + scan confirms |
| 3 | Change from_preset()? | **YES** | Architecture v3 decision |
| 4 | S2P same path? | **YES — same from_preset()** | Scan: S2P uses CompoundingScorer.from_preset("s2p") |
| 5 | Cadence? | **GAE DecisionCountPolicy(n=200) + reestimate_dk() every learn** | Scan: for_soc_twophase uses n=200 |
| 6 | Use n=200 as-is? | **YES** | 200 decisions in MEAN_CONVERGENCE before VARIANCE_LEARNING |
| 7 | Use FixedAlpha(0.5)? | **YES — this IS the shrinkage/graduation** | 50% prior + 50% data. The blog's "graduating" mechanism. |
| 8 | eta_override=0.01 + auto_pause? | **YES — canonical values** | eta_override=0.01 = v14 math synopsis. auto_pause = conservation. |
| 9 | P-WELFORD-A now? | **YES** | Already approved, storage only |
| 10 | Test 58? | **Storage roundtrip (P-WELFORD-A). Behavioral gate (2a).** | Welford can't recompute coordinate descent alone |
| 11 | P27 blocked on DK scoring? | **YES** | C9 requires DK weights USED in scoring, not just stored |

---

## Summary

| Prompt | What | Effort | Outcome |
|---|---|---|---|
| **0** | Discovery scan (6 scans, no code) | 30 min | ✅ COMPLETE — all params confirmed |
| **1** | P-WELFORD-A storage | 0.5d | L5 accepts Welford state |
| **2a** | Construction change (for_soc_twophase params) + behavioral gate | 1d | **Scorer learns DK weights (PROVEN by G1+G2)** |
| **2b** | Persistence + Welford tracking | 1d | DK weights + Welford in L5 store |
| **2c** | Router wiring + app startup | 1d | Learn flow writes DK to L5 per copilot |
| **3** | P26 startup read | 0.5d | Judgment memory survives restart |
| **4** | P27 full flow test | 0.5d | L5 completion gate passes |
| | C9 proof | 1h | **L5 COMPLETE — 288-moat and Mirror become true** |
| | **Total** | **~5-6d** | **Product claims become true** |

---

*DK Runtime Execution Plan v3 · June 6, 2026*
*5 prompts (Prompt 2 split into 2a/2b/2c with behavioral gate).*
*GAE params: LearningStrategy(DecisionCountPolicy(200), CoordinateDescentEstimator(), FixedAlpha(0.5)).*
*eta_override=0.01. auto_pause_on_amber=True. No custom cadence — use GAE phase transitions.*
*Prerequisites: #111 + #115 + #102 + GAE editable install (done).*
*After C9: 288-moat is real, Mirror shows learned insight, compounding runs.*
