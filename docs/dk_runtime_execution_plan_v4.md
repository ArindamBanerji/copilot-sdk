# DK Runtime Execution Plan v4 — 5 Prompts to Full Intelligence Loop
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

## Architectural Review Synopsis

Three review passes shaped this plan. This synopsis captures the key
decisions and their rationale so the coding session understands WHY,
not just WHAT.

### Review 1 — GPT feedback (6 points, all accepted)

**1. Split Prompt 2 into 2a/2b/2c with behavioral gate.** The original
plan had a 3-4d monolith. If Part A (construction change) is subtly
wrong, Parts B-E build persistence and routing on a broken foundation.
Fix: 2a ships the construction + behavioral gate (G1+G2). Only after
G1+G2 pass does 2b (persistence) and 2c (routing) proceed.

**2. Behavioral acceptance test is THE gate, not item 12 in a list.**
All storage tests can pass and the system still not learn — e.g.,
`reestimate_dk()` runs but returns near-prior weights, or weights
compute but `score()` never consumes them. G1 proves the intelligence
loop WORKS: feed a noisy factor, verify its weight drops, verify
scoring shifts. G2 proves shrinkage: at low N weights stay near prior,
at high N they diverge. These are the "pipeline runs" vs "intelligence
works" distinction.

**3. Ghost-fix prerequisite.** DK estimation reads verified decisions.
If #111 CONS-V-FIX and #115 OBSERVATION-WIRING haven't shipped,
ghost decisions contaminate the verified pool and DK learns from
garbage. These prerequisites must be verified BEFORE Prompt 0.

**4. Low-N shrinkage is built into GAE.** `FixedAlpha(0.5)` = 50%
prior + 50% data. This IS the "graduating from domain prior to
firm-specific" mechanism the blog claims. No James-Stein needed —
GAE already has it. The graduation is continuous, not a threshold.

**5. GAE as editable install, not sys.path.insert.** `pip install -e`
makes GAE a proper importable package. Brittle path hacks break test
suites and don't align with the open-source plan.

**6. C9 gates everything, not just the roadmap.** The blog publish
gate was "Option C only." Wrong — C9 (L5 COMPLETE) is what makes the
288-moat and Mirror TRUE. A buyer who deploys before C9 and inspects
DK weights sees the domain prior. Gate: C9 + #132 for blog/arxiv.
C9 + #132 + demo build for LOOM-V1.

### Review 2 — No-hack architectural audit (3 findings)

**Finding 1 (SIGNIFICANT): Option B (external DK bridge) was a hack.**
The original plan created a `dk_bridge.py` that ran
`CoordinateDescentEstimator` independently, injected `_dk_weights`
via private attribute assignment, and read from GraphStore instead of
the scorer's decision buffer. Three red flags: parallel computation
path, monkey-patching, different data source. Fix: Option A — change
`from_preset()` to construct ProfileScorer with full LearningStrategy.
The scorer calls its own `reestimate_dk()` through its designed API.
Persistence layer READS from the scorer, doesn't compute.

**Finding 2 (resolved): Why not split persist-only (Phase 1.5) and
activate (Phase 2)?** Three reasons the split was wrong:
- "Don't change scoring" is circular — the conservation gate exists
  precisely to catch accuracy degradation from DK activation
- "Observe before trusting" is waste — DK weights in L5 that nobody
  reads have zero commercial value
- "Conservation should be GREEN first" is backwards — conservation
  should monitor DK-weighted accuracy from day one, not switch later
  with no baseline

Combined: compute + persist + activate in one step. Conservation
monitors DK-weighted accuracy as the safety net.

**Finding 3 (resolved): No "minimal" LearningStrategy.** Use the FULL
strategy from `for_soc_twophase()`: `DecisionCountPolicy(n=200)`,
`CoordinateDescentEstimator()`, `FixedAlpha(0.5)`, `eta_override=0.01`,
`auto_pause_on_amber=True`. These are the designed parameters. The
product is a compounding intelligence system — the learning strategy
should be full, not minimal.

### Review 3 — Phase-aware centroid writes (1 significant finding)

**Centroid L5 writes must be conditional on MEAN_CONVERGENCE phase.**
When a category enters VARIANCE_LEARNING (after 200 decisions),
`ProfileScorer.update()` freezes the centroid and buffers decisions
for DK estimation instead. Writing an L5 centroid node with a
SHAPED_BY edge for a frozen centroid is false provenance — it claims
"this decision shaped this centroid" when the centroid didn't move.

Fix: `_persist_centroid_l5()` checks `get_category_phase(category)`.
If VARIANCE_LEARNING: skip centroid write (DK write fires instead).
If MEAN_CONVERGENCE: write centroid with SHAPED_BY edge (truthful).

This aligns with GAE's designed two-phase architecture:
- Phase 1 (MEAN_CONVERGENCE): centroid learning active, L5 centroid writes active
- Phase 2 (VARIANCE_LEARNING): DK learning active, L5 DK writes active
- Both phases: conservation L5 writes always active

### Discovery scan resolution (Prompt 0 — COMPLETE)

The scan confirmed every GAE parameter with zero unknowns:
- `DecisionCountPolicy(n=200)`: categories transition after 200 decisions
- `FixedAlpha(0.5)`: 50% prior + 50% data = shrinkage/graduation
- `CoordinateDescentEstimator.estimate()`: takes (decisions, centroids, n_categories, n_dims), returns (C, d) ndarray
- `VARIANCE_LEARNING` is a phase string on `CategoryState`, not a category-index set
- `get_verified_decisions()` returns all needed fields (factor_vector, category_index, is_correct)
- GAE editable install works from copilot-sdk
- No custom cadence counter needed — call `reestimate_dk()` every learn, it returns early when not in VARIANCE_LEARNING

### What this plan produces when complete

After C9, every SDK copilot (Trading, Purchasing, DataOps, S2P):
1. **Constructs** ProfileScorer with full LearningStrategy + estimator
2. **Learns centroids** for the first 200 decisions per category (MEAN_CONVERGENCE)
3. **Transitions** to DK estimation after 200 decisions (VARIANCE_LEARNING)
4. **Estimates** DK precision weights via CoordinateDescentEstimator
5. **Shrinks** estimated weights: 50% prior + 50% data (FixedAlpha)
6. **Scores** with learned DK weights (factor precision affects recommendations)
7. **Persists** centroids, DK weights + Welford, and conservation state to L5
8. **Monitors** DK-weighted accuracy via conservation gate (auto-pause on AMBER)
9. **Survives restart** via P26 startup read from L5 store

This is the full compounding intelligence loop. Trust traps are
discovered. The 288-moat is firm-specific. The Mirror shows learned
insight. The product's three core claims become true.

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
Prompt 3b: P-CENTROID-L5-WIRE      (0.5d, L5 centroid runtime write)
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
| ~~P-CENTROID-L5-WIRE~~ | — | **MOVED to Prompt 3b (before P27).** Required for all-three-node gate. |
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
| **3b** | P-CENTROID-L5-WIRE | 0.5d | **L5 centroid writes from learn flow** |
| **4** | P27 full flow test | 0.5d | L5 completion gate (ALL THREE node types) |
| | C9 proof | 1h | **L5 COMPLETE — 288-moat and Mirror become true** |
| | **Total** | **~6d** | **Product claims become true** |

---

*DK Runtime Execution Plan v4 · June 6, 2026*
*5 prompts (Prompt 2 split into 2a/2b/2c with behavioral gate).*
*GAE params: LearningStrategy(DecisionCountPolicy(200), CoordinateDescentEstimator(), FixedAlpha(0.5)).*
*eta_override=0.01. auto_pause_on_amber=True. No custom cadence — use GAE phase transitions.*
*Prerequisites: #111 + #115 + #102 + GAE editable install (done).*
*After C9: 288-moat is real, Mirror shows learned insight, compounding runs.*

---

## Prompt 3b — P-CENTROID-L5-WIRE: L5 Centroid Runtime Write (0.5d)

**Why this moved:** The original plan listed P-CENTROID-L5-WIRE after
C9, reasoning "centroids work via checkpoints." But P27's gate is
"all three L5 node types." Without centroid L5 writes, P27 can only
verify 2 of 3 — and C9's 15-cell proof (5 domains × 3 types) has 5
empty cells. The sequencing conflict is resolved by moving this BEFORE
P27.

**Important distinction:** `save_centroids()` (existing checkpoint
persistence) is NOT equivalent to `update_centroid()` (L5 graph node).
Checkpoints serialize the full centroid tensor for scorer restore.
L5 centroid nodes store per-(category, action) centroid vectors with
SHAPED_BY edges linking them to the causing Decision node. Both serve
different purposes. Both continue to exist.

### Answers to all 8 questions

**Q1:** YES — required before P27. See above.

**Q2: Insertion point — Option B (scoring_router.py)**

Consistent with DK and conservation L5 writes. All three L5 write
types are in the router layer, after learn:

```python
# scoring_router.py learn handler, AFTER learn_result:

# 1. Conservation L5 write (P25b — already wired)
_persist_conservation_state_l5(...)

# 2. DK re-estimation + L5 write (P-DK-RUNTIME-FULL — Prompt 2)
scorer.reestimate_dk_if_due()
persist_dk_after_reestimate(...)

# 3. Centroid L5 write (P-CENTROID-L5-WIRE — THIS PROMPT)
_persist_centroid_l5(
    scorer=scorer,
    learning_store=learning_store,
    domain=domain,
    category=learn_result.category,
    actual_action=learn_result.actual_action,
    caused_by_decision_id=learn_result.decision_id,
)
```

**Q3: Field mapping for update_centroid()**

| Field | Source | Notes |
|---|---|---|
| `domain` | `domain_config.domain` | Same as conservation/DK writes |
| `category` | `learn_result.category` | The decision's category |
| `action` | `learn_result.actual_action` | The action whose centroid was updated by `ProfileScorer.update()`. This is the ACTUAL action (the analyst's choice), because `update()` moves the centroid toward the observed factor vector for the action that was taken. |
| `centroid_vector` | Read from scorer AFTER learn | `scorer.get_centroid(category, action)` or equivalent accessor. This is the POST-update centroid. |
| `count` | From scorer | Number of decisions that have shaped this centroid |
| `eta_last` | From scorer if available | Last learning rate used. None if not exposed. |
| `caused_by_decision_id` | `learn_result.decision_id` | The decision that triggered this centroid update |

**On delta_norm:** If the P21/P22 `update_centroid()` signature includes
`delta_norm`, compute as `norm(post_centroid - pre_centroid)`. This
requires capturing the centroid BEFORE `scorer.learn()`:

```python
# BEFORE learn:
pre_centroid = scorer.get_centroid(category, action)

# learn() updates centroid in-memory
learn_result = scorer.learn(...)

# AFTER learn:
post_centroid = scorer.get_centroid(category, action)
delta_norm = sum((a - b)**2 for a, b in zip(post_centroid, pre_centroid)) ** 0.5
```

If capturing pre-centroid is impractical (requires an extra read), set
`delta_norm=None`. The centroid vector itself is the critical field.
Delta is monitoring metadata, not structural.

**Discovery required:** Read the actual `update_centroid()` signature
from `copilot_sdk/graph/protocol.py` (P21 implementation) to confirm
exact parameter names and which are required vs optional.

**Q4: Non-fatal?** YES. Same try/except/log/continue pattern:

```python
def _persist_centroid_l5(scorer, learning_store, domain, category,
                          actual_action, caused_by_decision_id):
    if learning_store is None:
        return

    # CRITICAL: Only write L5 centroid when the category is in
    # MEAN_CONVERGENCE (centroid actually updated by update()).
    # In VARIANCE_LEARNING, centroids are FROZEN — update() buffers
    # decisions for DK estimation instead. Writing an L5 centroid node
    # with SHAPED_BY edge for a frozen centroid is false provenance.
    category_phase = scorer.get_category_phase(category)
    if category_phase == "VARIANCE_LEARNING":
        return  # Centroid frozen — DK estimation active, not centroid learning

    try:
        centroid_vector = scorer.get_centroid(category, actual_action)
        if centroid_vector is None:
            return  # No centroid for this (category, action) yet
        learning_store.update_centroid(
            domain=domain,
            category=category,
            action=actual_action,
            centroid_vector=centroid_vector,
            # count, eta_last, delta_norm: discover from P21 signature
            caused_by_decision_id=caused_by_decision_id,
        )
    except Exception as e:
        logger.error(f"L5 centroid write failed for {domain}: {e}")
```

**Why the phase check matters:** Without it, a category that has been
in VARIANCE_LEARNING for 1,000 decisions would have 1,000 L5 centroid
nodes all pointing to the SAME frozen centroid vector, each falsely
claiming to be "shaped by" a different decision. This is incorrect
provenance that would mislead an auditor. The centroid stopped changing
at decision 200 — only the first 200 L5 centroid nodes are real.

**Q5: save_centroids() unchanged?** YES. L5 centroid write is ADDITIVE.
The existing checkpoint mechanism continues to work exactly as before.
Both coexist:
- `save_centroids()`: full tensor checkpoint for scorer restore
- `update_centroid()`: per-(category, action) L5 node for audit + graph

**Q6: S2P in scope?** YES. S2P uses `CompoundingScorer.from_preset("s2p")`
which shares the SDK learn path. The wiring in `scoring_router.py`
covers Trading/Purchasing/DataOps. S2P's `/api/s2p/outcome` handler
needs the same inline write (same pattern as P25b and P-DK-RUNTIME).

**Q7: SHAPED_BY edge — P27 or C9?**

- **P27 (automated):** Assert L5 centroid ROW/STATE exists after learn.
  Verify `learning_store.get_centroid(domain, category, action)` returns
  a populated dict with the expected centroid_vector.
- **C9 (manual):** Assert SHAPED_BY edge exists in AGE. Requires live
  AGE graph. `MATCH (c:L5Centroid)-[:SHAPED_BY]->(d:Decision) RETURN count(*)`

P27 tests storage correctness. C9 tests graph topology. Both are needed;
they test different things.

**Q8: Updated sequencing — P-CENTROID-L5-WIRE is now Prompt 3b.**

### Prompt 3b scope

**Files to modify:**
- `copilot_sdk/backend/scoring_router.py` — add `_persist_centroid_l5()` after DK write
- `s2p-copilot/backend/app/routers/s2p.py` — same pattern for S2P outcome
- `copilot_sdk/scoring/scorer.py` — add `get_centroid(category, action)` accessor if not already exposed

**Files NOT to modify:**
- `save_centroids()` checkpoint path — untouched
- `update_centroid()` store implementations — already exist from P21/P22
- Conservation or DK paths — already wired

### Prompt 3b tests (5)

| # | Test | What it proves |
|---|---|---|
| 1 | `test_learn_persists_centroid_to_l5` | After learn (MEAN_CONVERGENCE), L5 store has centroid for (domain, category, action) |
| 2 | `test_centroid_l5_has_caused_by_decision_id` | SHAPED_BY provenance: which decision caused this centroid update |
| 3 | `test_centroid_l5_nonfatal` | L5 failure → learn continues, checkpoint still works |
| 4 | `test_centroid_l5_coexists_with_checkpoint` | Both save_centroids() and update_centroid() fire on same learn — no interference |
| 5 | `test_centroid_l5_skipped_in_variance_learning` | After 200 decisions (VARIANCE_LEARNING), centroid L5 write is SKIPPED — no false provenance. DK L5 write fires instead. |

### Required accessor additions

```python
# In CompoundingScorer (scorer.py):

def get_centroid(self, category: str, action: str) -> list[float] | None:
    """Read post-update centroid for (category, action). Read-only."""
    # Thin wrapper over ProfileScorer centroid access
    ...

def get_category_phase(self, category: str) -> str:
    """Return 'MEAN_CONVERGENCE' or 'VARIANCE_LEARNING' for a category.
    Used by centroid L5 write to determine if centroid is frozen."""
    # Read from ProfileScorer._category_states[category_index].phase
    ...
```

**Discovery required:** Verify how `CategoryState.phase` is accessed
in ProfileScorer. The phase field may be a string or an enum.

### L5 write ordering note

The L5 write order in the router is conservation (P25b) → DK (Prompt 2c)
→ centroid (Prompt 3b). The spec's intended order is centroid → DK →
conservation (matching the data flow: centroid update first, DK estimation
second, conservation check last). The writes are independent — all
reference a Decision node that already exists — so order doesn't affect
correctness. However, if the team wants semantic clarity, the three
inline calls can be reordered in `scoring_router.py` during Prompt 3b
to match the spec.

### P27 test runtime note

P27's full-flow test requires 200+ decisions to trigger the VARIANCE_LEARNING
phase transition. Running 200 score+learn cycles takes 1-3 minutes in
automated tests. This is acceptable for an integration test that runs
once per suite. If faster testing is needed, the test fixture can
construct a scorer with a reduced phase threshold (e.g., `DecisionCountPolicy(n=10)`
for test-only) — but this should be clearly marked as test-only and not
affect production construction.

### Stop conditions

- Do NOT modify save_centroids() checkpoint behavior
- Do NOT change centroid computation (that's ProfileScorer.update())
- Do NOT change DK or conservation paths
- Do NOT broaden GraphStore
- Do NOT write L5 centroid nodes when category is in VARIANCE_LEARNING
  (centroid is frozen — false SHAPED_BY provenance)
- If `get_centroid(category, action)` accessor doesn't exist, add it
  as a thin wrapper (read-only, no computation) — do NOT restructure scorer
- If `get_category_phase(category)` accessor doesn't exist, add it
  as a thin wrapper reading CategoryState.phase — do NOT restructure scorer

---

## Updated Prompt Sequence (v4)

```
Prompt 0: DISCOVERY SCAN           (30 min) ✅ COMPLETE
Prompt 1: P-WELFORD-A              (0.5d)   storage/protocol
Prompt 2a: CONSTRUCTION CHANGE     (1d)     construction + behavioral gate
──── GATE: G1+G2 must pass ────
Prompt 2b: PERSISTENCE + WELFORD   (1d)     dk_persistence.py + L5 writes
Prompt 2c: ROUTER + STARTUP        (1d)     DK wiring + app init
Prompt 3: P26 STARTUP-READ          (0.5d)   warm-start from L5
Prompt 3b: P-CENTROID-L5-WIRE       (0.5d)   L5 centroid runtime write ← NEW
Prompt 4: P27 FULL-FLOW-TEST        (0.5d)   ALL THREE node types + Welford
          C9: L5 PROOF              (manual)  5 domains × 3 types = 15 cells
```

**Total: ~6d** (was ~5-6d; +0.5d for Prompt 3b).
