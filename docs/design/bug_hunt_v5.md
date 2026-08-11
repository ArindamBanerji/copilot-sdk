# ADVERSARIAL BUG HUNT v5: Standard Multi-Repo Prompt
# ================================================
#
# USAGE: Set the REPO variables below, then send entire prompt to Codex CLI.
# This prompt is repo-agnostic. The probes apply to any Python+React codebase.
#
# REPO CONFIG (v5 — run each dimension against ALL repos):
#   SOC      = gen-ai-roi-demo-v4-v50    (backend + frontend)
#   SDK      = copilot-sdk               (SDK core + 4 app backends + 4 frontends)
#   S2P      = s2p-copilot               (backend only)
#   GAE      = graph-attention-engine-v50 (engine)
#   CI       = ci-platform               (graph store + AGE client)

ADVERSARIAL BUG HUNT v5: Line-by-Line Deep Analysis
====================================================

PURPOSE: Find bugs that grep cannot find. Every check requires
READING the FULL function body and REASONING about behavior under
edge conditions. Pattern-matching (grep for bad strings) is
insufficient — you must trace data flow and identify logic errors.

v4 changes from v3:
  - 6 new probe dimensions (async safety, memory, type coercion,
    error state corruption, input validation, graph injection)
  - Stronger evidence standard: every finding requires BEFORE/AFTER
    state trace, not just "this line looks wrong"
  - Framework v4 probes (FW-01→FW-07 integration)
  - Parameterized for multi-repo use
  - "Show your work" requirement on every probe

Do NOT implement — review only.
Stop if ≥5 P1 findings — report immediately.

Start from claude_projects directory.
Read CLAUDE.md first.

IMPORTANT: Chain cd && command (cd doesn't persist).

═══════════════════════════════════════════════════════
METHOD — MANDATORY FOR EVERY PROBE
═══════════════════════════════════════════════════════

For EACH numbered check, you MUST follow this exact sequence.
Skipping any step invalidates the finding.

STEP A — LOCATE: Find the exact function/method. Quote its 
  signature with file:line.

STEP B — READ: Read the FULL function body, not a summary. 
  If the function is >100 lines, read it in chunks and note 
  the line ranges you read.

STEP C — TRACE: For the specific edge condition described, 
  trace execution line by line. State the value of each 
  relevant variable at each branch point. Write this out:
    Line N: variable = value (because ...)
    Line N+1: branch taken / not taken (because variable is ...)
    Line N+2: ...

STEP D — VERDICT: State what happens at the END of the trace.
  Quote the EXACT line (≤80 chars) that handles OR fails to 
  handle the condition.

STEP E — CLASSIFY: P1 / P2 / P3 / OK with file:line citation.

EVIDENCE STANDARD:
  "The function handles it" without a line-by-line trace is 
  NOT acceptable. "OK — triage.py:987 handles null" without 
  showing the trace that REACHES line 987 is NOT acceptable.
  You must show: entry point → branch decisions → outcome.

SEVERITY CALIBRATION:
  P1 = uncaught exception on production endpoint, silent data
    corruption, shared state mutation without isolation, security
    bypass, unbounded memory growth in production
  P2 = edge case failure that degrades gracefully, UX bug,
    operational surprise, missing validation, test gap on
    critical path
  P3 = code quality, stale data, cosmetic, missing test for
    non-critical path

If a bug CAN cause an uncaught exception on a production 
endpoint, classify as P1 regardless of how unlikely the 
trigger is. Probability doesn't matter — blast radius does.

═══════════════════════════════════════════════════════
DIMENSION 1: NULL / MISSING DATA PATHS
═══════════════════════════════════════════════════════
Goal: Every function that reads from external state (graph, 
cache, file, request) must handle the case where that state 
is absent, empty, or malformed.

1a. OUTCOME PATH — missing decision node
    Read backend/app/routers/triage.py report_decision_outcome().
    Trace: request.decision_id matches NO Decision node in graph.
    Does the graph query return empty? Does code check before 
    accessing row[0]? Does code proceed with None values?
    Show the trace from query → result check → first use of result.

1b. OUTCOME PATH — orphaned decision (no DECIDED_ON edge)
    Same function. The MATCH pattern is Decision-[DECIDED_ON]->Alert.
    Trace: Decision exists but edge is missing. Does OPTIONAL MATCH
    return null for alert? Does code check alert is not None before
    using alert properties?

1c. OUTCOME PATH — null factor_vector
    Same function. Trace: gae_result exists but factor_vector is None.
    Where does code check? What counter increments are skipped?
    What counter increments still happen? Is decision_count handled?
    (v5.52 note: defensive fix added — verify it's correct)

1d. SCORING — null scorer
    Read backend/app/services/gae_state.py get_profile_scorer().
    Can it return None? Then search for EVERY caller of 
    get_profile_scorer() across the backend. For each caller:
    does it check for None before calling scorer.score()?
    List each caller with file:line and whether it checks.

1e. IKS — null bootstrap
    Read backend/app/services/iks.py compute_visible_iks().
    Trace: get_mu_zero() returns None (bootstrap file missing).
    Does compute_visible_iks crash? What does it return?

1f. GRAPH — empty result set
    Search backend/ for every graph query that accesses result[0]
    or result["key"]. For each: is there a len(result) > 0 check
    before the access? List the top 5 unguarded accesses.

═══════════════════════════════════════════════════════
DIMENSION 2: CONCURRENCY / ASYNC SAFETY
═══════════════════════════════════════════════════════
Goal: In an async web server, any mutable singleton can be 
corrupted by concurrent requests. Every shared mutable state 
must be identified and evaluated.

2a. MUTABLE SINGLETONS — inventory
    Search backend/ for module-level variables and singleton 
    patterns. List EVERY mutable object that is:
      - Defined at module level (not inside a function)
      - Modified by request handlers
    For each: state whether concurrent modification is safe.
    Common patterns: _scorer = None, _learning_state = None,
    _snapshot = None, counters, caches, lists.

2b. SCORER STATE — concurrent update()
    Read gae/profile_scorer.py update(). It modifies self.mu 
    (centroids). If two concurrent requests both call update()
    on the same scorer instance:
      Request A reads self.mu[c,a,:] = [0.5, 0.5, 0.5]
      Request B reads self.mu[c,a,:] = [0.5, 0.5, 0.5]  
      Request A writes self.mu[c,a,:] += delta_A
      Request B writes self.mu[c,a,:] += delta_A  (should be += delta_B on UPDATED value)
    Is there a lock? Quote the lock acquisition or state "no lock."
    Is numpy's GIL sufficient? (No — GIL protects interpreter, 
    not application logic. Two awaits can interleave.)

2c. SIMULATION ISOLATION
    Read backend/app/services/simulation.py run().
    Trace: where is the scorer obtained? Is it the production 
    singleton or a copy? Quote the exact line.
    Then find EVERY scorer.update() call. Is it on the copy?
    If ANY update touches production: P1.
    Also check: does simulation write to production graph?
    Does it increment production decision_count?

2d. SNAPSHOT COUNTER RACE
    Read backend/app/services/gae_state.py 
    maybe_write_centroid_snapshot().
    Quote the counter increment line. Is there a lock?
    Trace: two async handlers both at count=9.

2e. AUDIT CHAIN — concurrent record
    Read backend/app/framework/audit.py record_decision().
    Is the hash computed INSIDE or OUTSIDE the lock?
    If outside: two calls compute same prev_hash → fork.
    Is chain_index derived from len(entries) inside the lock?


2f. AGE CONNECTION POOL UNDER CONCURRENT COPILOT WRITES
     5 copilots share one AGE database. Check: are connections
     pooled or per-request? If pooled, what is max_connections?
     Under 5 concurrent copilot backends each writing decisions,
     can the pool exhaust? Check connect_timeout behavior on
     pool exhaustion. If no timeout → indefinite hang: P1.
═══════════════════════════════════════════════════════
DIMENSION 3: ERROR STATE CORRUPTION
═══════════════════════════════════════════════════════
Goal: When a function fails mid-execution, is shared state 
left in a consistent state? Every try/except and every 
multi-step mutation must be checked.

3a. ETA_OVERRIDE save/restore
    Read triage.py report_decision_outcome(). Find the 
    eta_override save/restore pattern. Is it:
      saved = scorer.eta_override
      scorer.eta_override = computed_value
      try: await guarded_update(...)
      finally: scorer.eta_override = saved
    Or is the finally block MISSING? If guarded_update throws,
    is eta_override left corrupted for ALL subsequent requests?
    Quote the exact try/finally block (or its absence).

3b. CENTROID MUTATION — partial update
    Read gae/profile_scorer.py update(). There are 4 mutation 
    sites + 1 clip. If the function raises after mutation site 2
    but before site 4:
      - Are mutations 1-2 applied but 3-4 not?
      - Is the clip (np.clip) skipped?
      - Is centroids left in an inconsistent state?
    Can any of the intermediate lines raise? (numpy ops can 
    raise on NaN, inf, shape mismatch)

3c. GRAPH WRITE — partial commit
    Read backend/app/routers/triage.py the outcome handler.
    It does multiple graph writes (UPDATE decision, CREATE edges).
    If write 1 succeeds but write 2 fails:
      - Is write 1 rolled back?
      - Or is the graph left with a partial update?
    Does the AGE client use transactions? Quote the transaction 
    boundary or state "no transaction wrapper."

3c-ext. K4 CONNECTOR NETWORK FAILURES
     All K4 connectors (MarketDataProvider, CommodityDataProvider,
     QBOConnector, ThreatIntelProvider, SupplierIntelProvider,
     DQBenchmarkProvider) make external API calls.
     Check: does each connector catch network errors and fall back
     to cached/fixture? Does any connector leak credentials in
     error messages? If credentials appear in any exception: P1.

3d. CHECKPOINT RESTORE — incomplete state
    Read backend/app/framework/checkpoint.py rollback().
    List EVERY field restored. Then list EVERY field NOT restored.
    Specifically check: centroids, W matrix, decision_count,
    conservation status, kernel weights, covariance estimator.
    If centroids restored but decision_count not: the system 
    thinks it has N decisions but centroids reflect M < N.

3e. STARTUP — initialization order
    Read backend/app/main.py the startup event handler.
    List the initialization order. If component B depends on 
    component A, but A is initialized AFTER B:
      - Does B get None for A's value?
      - Does B crash on startup?
    Specifically: does scorer initialization happen before 
    learning_state? Before conservation? Before audit chain?

═══════════════════════════════════════════════════════
DIMENSION 4: NUMERICAL / TYPE EDGE CASES
═══════════════════════════════════════════════════════
Goal: Numpy operations can silently produce wrong results 
through broadcasting, type coercion, or special values.

4a. DIVISION BY ZERO — conservation law
    Read backend/app/services/learning_health.py evaluate().
    Trace: V=0 (zero verified decisions). Does q = correct/total 
    produce ZeroDivisionError? What value does q take?
    Trace: V=1. Does θ_min = 23.53/(α×V) produce inf when α=0?
    Quote the exact division lines.

4b. NUMPY BROADCASTING — shape mismatches
    Read gae/profile_scorer.py score(). Find every numpy 
    operation involving self.centroids. What shapes are expected?
    What happens if f has shape (D,) vs (1,D) vs (D,1)?
    Is there a shape assertion or reshape at the top of score()?

4c. NaN PROPAGATION
    Read gae/profile_scorer.py score() and update().
    Can centroids contain NaN? (e.g., 0/0 in an update delta)
    If centroids[c,a,d] = NaN, does score() return NaN scores?
    Does the NaN propagate to the frontend? Is there a NaN guard?
    Search for np.isnan, np.nanmean, or NaN checks.

4d. INTEGER OVERFLOW / PRECISION
    Read backend/app/services/learning_health.py.
    decision_count is a Python int (arbitrary precision).
    But: are there any numpy int32/int64 casts? At 10M decisions,
    int32 overflows. Search for np.int32, astype(int).

4e. FLOAT COMPARISON — equality checks
    Search backend/ for "== 0.0", "== 1.0", "== 0", "!= 0" on 
    float variables. Float equality is unreliable.
    List the top 5 most dangerous float equality checks.

4f. IKS SHAPE MISMATCH
    Read backend/app/services/iks.py. If scorer.centroids is 
    (6,4,6) but mu_zero is (6,4,5) — does numpy subtraction 
    broadcast silently or error?

═══════════════════════════════════════════════════════
DIMENSION 5: MEMORY / RESOURCE LEAKS
═══════════════════════════════════════════════════════
Goal: In a long-running server, any unbounded collection 
is a memory leak. Any unclosed resource is a leak.

5a. UNBOUNDED COLLECTIONS — inventory
    Search backend/ for lists, dicts, or sets that:
      - Are defined at module/instance level
      - Are appended to in request handlers
      - Have NO trim/eviction logic
    For each: state the growth rate (per request? per decision?
    per category?) and estimated memory at 100K decisions.
    Known bounded: BatchHistory (max_records), _novelty_scores 
    (max_look). Check everything else.

5b. DECISION BUFFER — growth
    Read gae/profile_scorer.py. The _decision_buffer is a list 
    appended in Phase 2. Is it EVER trimmed? Is there a max size?
    At 1000 decisions/day for 30 days = 30,000 entries ×
    (6 floats + 3 ints) × 8 bytes = ~2MB. Acceptable? But what 
    about 1 year?

5c. GRAPH CONNECTIONS — pool management
    Read ci-platform/ci_platform/graph/age_client.py.
    How are database connections managed? Connection pool?
    Is there a max pool size? Can a slow query exhaust the pool?
    Does the pool auto-recover from connection drops?

5d. FILE HANDLES — snapshot writes
    Read backend/app/services/gae_state.py write_centroid_backup().
    Are file handles always closed? (with statement? try/finally?)
    What about the read path: list_centroid_backups()?
    At 1000 snapshots, does it load ALL file contents?

5e. LOGGING — unbounded log growth
    Search for logger calls in hot paths (score(), update(), 
    request handlers). Are any set to DEBUG level by default?
    At 1000 requests/minute, DEBUG logging produces ~100MB/hour.
    Is log rotation configured?


5f. CENTROID HISTORY UNBOUNDED GROWTH
     centroid_history_handler appends history on every learn() call.
     Check: is there a max_entries cap or rotation? If history grows
     without bound: P2 (memory at 100K decisions). If capped,
     verify the eviction policy (oldest-first, not random).
═══════════════════════════════════════════════════════
DIMENSION 6: INPUT VALIDATION / INJECTION
═══════════════════════════════════════════════════════
Goal: Every API endpoint must validate inputs. Every graph 
query must prevent injection.

6a. API BOUNDARY — request validation
    List every POST endpoint in backend/app/routers/.
    For each: does it use a Pydantic model for the request body?
    If yes: does the model have field validators (ge=0, le=1, etc.)?
    If no: the endpoint accepts arbitrary JSON — classify by risk.

6b. GRAPH QUERY INJECTION — _S() safety
    Read ci-platform/ci_platform/graph/age_client.py _S().
    What does _S() do to its input? Does it escape single quotes?
    Does it handle None, lists, dicts, or only scalars?
    Then search backend/ for any graph query that does NOT use _S()
    — raw string interpolation into Cypher. List each.

6c. FILE UPLOAD — size + type validation
    Read backend/app/routers/eval_router.py the upload endpoint.
    Is there a max file size check? Max row count? File type check?
    What happens if someone POSTs a 500MB CSV? A .exe renamed .csv?
    Quote the line that reads the file body.

6d. GRAPH EXPLORER — mutation prevention
    Read backend/app/services/graph_explorer.py.
    Does validate_query() reject CREATE, SET, DELETE, DETACH, DROP?
    What about MERGE (which can create)? What about CALL (which can
    invoke procedures)? Is the check case-insensitive?
    Quote the exact regex or string check.

6e. ANALYST ACTION VALIDATION
    Read triage.py report_decision_outcome().
    If request.analyst_action is "DROP TABLE" or "'); DROP TABLE;--"
    — does it get validated before being used? Does it get passed 
    to a graph query? Could it produce injection?

═══════════════════════════════════════════════════════
DIMENSION 7: CONSERVATION LAW CORRECTNESS
═══════════════════════════════════════════════════════
Goal: The conservation law is the safety guarantee. If it's 
wrong, the system can silently degrade.

7a. CONSERVATION FORMULA — boundary values
    Read backend/app/services/learning_health.py evaluate().
    Trace these specific scenarios:
      - V=0, q=undefined → what status?
      - V=1, q=1.0, α=0.05 → signal = 0.05. θ_min = 23.53/(0.15×1) = 156.9. Status?
      - V=400, q=0.5, α=0.5 → signal = 100. θ_min = 23.53/(0.15×400) = 0.39. Status?
      - V=400, q=0.99, α=0.5 → signal = 198. Status?

7b. CONSERVATION — auto_pause lifecycle
    Where is auto_pause_active SET? Where is it CLEARED?
    Can it get stuck in paused state if the system recovers?
    Trace the full: healthy → degraded → paused → recovered → unpaused path.
    Is each transition tested?

7c. CONSERVATION — decision_count vs history disagreement
    decision_count includes refer_to_analyst (routing actions).
    history (q_window) excludes them (only scorer actions).
    At what ratio of routing:scorer actions does this divergence 
    become observable? (e.g., if 50% of decisions are routing,
    decision_count = 2× len(history). Does anything break?)

7d. CONSERVATION — Phase 2 interaction
    In Phase 2 (VARIANCE_LEARNING), centroids are frozen.
    update() returns CentroidUpdate(outcome='phase2_buffered').
    Does this buffered outcome get recorded in history?
    Does it affect q? If Phase 2 outcomes DON'T enter history,
    and a category stays in Phase 2 for 1000 decisions, the
    q_window goes stale. Is this handled?


7e. CROSS-DOMAIN CONSERVATION POLLUTION
     On shared AGE graph, conservation counts must be domain-scoped.
     Check: count_verified, count_decisions in conservation paths
     filter by domain. If any conservation query counts ALL domains: P1.
     SOC referral rules (triage.py:721-722) known risk.

7f. AUTO-ORDER THRESHOLD RATCHET DIRECTION
     AutoOrderGate threshold contracts on error, expands on accuracy.
     Check: threshold_ratchet logic — does error DECREASE the
     threshold (correct) or INCREASE it (backwards)? If threshold
     moves in wrong direction on error: P1.
═══════════════════════════════════════════════════════
DIMENSION 8: FRAMEWORK v5 INTEGRATION
═══════════════════════════════════════════════════════
Goal: FW-01→FW-07 added 5 new modules. Verify they integrate
correctly with the existing scorer and don't introduce regressions.

8a. TWO-PHASE — category index bounds
    Read gae/profile_scorer.py. _category_states is a list of 
    length C. What happens if score(f, category_index=C) is called?
    (index == length → IndexError). Is there a bounds check?
    What about category_index=-1? (Python allows negative indexing.)

8b. DK ESTIMATOR — empty category
    Read gae/dk_estimator.py estimate(). If a category has 0 or 1
    decisions, the function should return uniform weights for that
    category. Verify: does it check len(cat_decisions) < 2?
    What if ALL categories have 0 decisions?

8c. SHRINKAGE — alpha boundary
    Read gae/shrinkage.py compute_effective_weights().
    Verify: alpha=0.0 → exactly 1.0 (not 1.0 + epsilon).
    Verify: alpha=1.0 → exactly w_dk (not w_dk + epsilon).
    These must be EXACT, not approximate, because tests assert 
    equality (not allclose).

8d. PROFILE SCORER — learning_strategy + existing features
    Does learning_strategy interact with:
      - factor_mask? (If factor_mask zeros out dimension d, 
        does Phase 2 DK weight for dimension d still get computed?)
      - min_confidence? (Does the confidence gate fire before 
        or after the Phase 2 branch in update()?)
      - auto_pause_on_amber? (Does conservation pause override 
        Phase 2 buffering?)
    Trace each interaction by reading update() top to bottom.

8e. BATCH PIPELINE — promotion gate threshold
    Read gae/batch_pipeline.py DefaultPromotionGate.evaluate().
    The superiority margin is 0.05 (5pp). But what is "old_accuracy"?
    Is it accuracy with current DK weights? Or accuracy with uniform
    weights (baseline)? If the first estimation goes from uniform 
    (say 0.50) to estimated (0.82), delta = 0.32 > 0.05. Passes.
    But if re-estimation goes from 0.82 to 0.83, delta = 0.01 < 0.05.
    Fails. Is this the intended behavior? (Marginal improvements 
    are rejected — could prevent convergence.)

8f. NOVELTY — interaction with reestimate_dk()
    After reestimate_dk(), should the novelty accumulator be reset?
    Read profile_scorer.py reestimate_dk(). Does it call 
    novelty_tracker.reset_accumulator()? If not, the accumulator 
    keeps growing and the next batch triggers immediately.
    But: the novelty tracker is NOT inside ProfileScorer — it's 
    external. So this is a coupling question: who owns the reset?


8g. CENTROID_HISTORY_HANDLER DUPLICATION
     copilot_sdk ships a shared centroid_history_handler.
     Check: no copilot app has a local copy that diverges.
     If Trading/Purchasing/DataOps/S2P have their own handler,
     verify signatures match SDK version. Drift = P2.

8h. DK WEIGHT TRANSFER LEAK
     warm_start_centroids should NEVER transfer DK weights.
     Only centroids. Check: TransferPattern and warm_start_centroids
     confirm DK weights are excluded from transfer payload.
     If DK weights appear in any transfer response: P1.
═══════════════════════════════════════════════════════
DIMENSION 9: FRONTEND CONSISTENCY
═══════════════════════════════════════════════════════
Goal: Frontend state management can show inconsistent data.

9a. RACE CONDITION — rapid alert selection
    Read frontend AlertTriageTab. What happens if user clicks 
    alert A, then alert B before A's response arrives?
    Is there request cancellation (AbortController)? Or does 
    A's response overwrite B's display?

9b. CROSS-TAB CONSISTENCY
    After a new outcome is submitted:
      - Tab 1 shows total_decisions from graph
      - Tab 2 shows decision_count from LearningState
      - Tab 4 shows IKS from compute_visible_iks
    Which updates first? Is there a window where they disagree?
    How long?

9c. ERROR BOUNDARY — backend 500
    Is there ANY E2E test that verifies the app doesn't crash 
    when a backend endpoint returns 500? Search frontend/tests/.

9d. CONSOLE ERRORS — production noise
    Run: cd frontend && npm run build
    Are there any build warnings that indicate runtime issues?
    (unused imports are fine; missing module resolution is P2)

═══════════════════════════════════════════════════════
DIMENSION 10: TEST COVERAGE — CRITICAL PATH GAPS
═══════════════════════════════════════════════════════
Goal: Identify untested critical paths. A test that MOCKS 
the function away does NOT count as coverage.

For each function below:
  1. Search tests/ for calls to the function or its endpoint
  2. READ each test — classify what scenario it covers
  3. List COVERED scenarios and GAP scenarios

10a. report_decision_outcome() — triage.py
     GAPS to check: invalid decision_id, invalid analyst_action,
     concurrent outcomes for same decision, outcome when paused

10b. SimulationOrchestrator.run() — simulation.py
     GAPS to check: scorer not modified after sim, graph not 
     polluted, crash mid-run cleanup, concurrent sims

10c. LearningHealthMonitor.evaluate() — learning_health.py
     GAPS to check: V=0, V=1, α=0, RED→GREEN transition,
     auto_pause survives restart

10d. CheckpointService.rollback() — checkpoint.py
     GAPS to check: post-rollback scoring matches checkpoint,
     LearningState consistent, non-existent checkpoint_id

10e. ProfileScorer Phase 2 flow — profile_scorer.py
     GAPS to check: Phase 2 with factor_mask, Phase 2 with 
     min_confidence gate, Phase 2 pickle round-trip with 
     dk_weights, reestimate_dk with only incorrect decisions

FORMAT:
  [function] COVERED: scenario1, scenario2
  [function] GAPS: scenario3 (P2), scenario4 (P3)


10f. DEMO.PY PRESEED DATA FRESHNESS
     demo.py generates preseed data on startup. If the preseed
     format changes but demo.py is not updated, the demo shows
     stale or incompatible fixture data.
     Check: preseed generation calls match current service signatures.
     Check: no hardcoded dates older than 30 days in preseed data.

10g. PROVENANCEBADGE MISSING ON NEW SURFACES
     Every surface that displays computed metrics MUST show a
     ProvenanceBadge. New panels added after the badge system
     may be missing it.
     Check: grep all *Panel.tsx / *Card.tsx for ProvenanceBadge import.
     Any panel that renders numeric metrics without a badge: P2.
═══════════════════════════════════════════════════════
DIMENSION 11: SECURITY / COMPLIANCE
═══════════════════════════════════════════════════════

11a. PII IN LOGS
     Search backend/ for logger.info, logger.debug, logger.warning 
     that log request bodies, alert data, or user identifiers.
     List the top 5 most concerning log statements.

11b. CERTIFICATION LANGUAGE
     Search governance_report.py and governance_router.py for:
     "compliant", "compliance", "certified", "certification",
     "meets requirements", "satisfies", "in accordance with"
     Legal constraint: ONLY "evidence supporting human oversight."
     Any certification-adjacent language in API responses: P1.

11c. CORS CONFIGURATION
     Read backend/app/main.py. What origins are allowed?
     Is it "*" (allow all)? If so: P2 for production but 
     acceptable for demo.

11d. SAML BYPASS
     Read backend/app/middleware/saml_auth.py (if exists).
     When SAML is disabled, are ALL routes open? Including 
     admin routes? Is there a whitelist?

═══════════════════════════════════════════════════════
EXECUTION
═══════════════════════════════════════════════════════

RUN TESTS (all repos):
  cd gen-ai-roi-demo-v4-v50/backend && python -m pytest tests/ -x --timeout=120 -q
  cd ../../graph-attention-engine-v50 && python -m pytest tests/ --timeout=120 -q  
  cd ../ci-platform && python -m pytest tests/ --timeout=60 -q
  cd ../s2p-copilot/backend && python -m pytest tests/ --timeout=60 -q
  cd ../copilot-sdk && python -m pytest tests/ --timeout=60 -q

FRONTEND BUILD CHECK:
  cd gen-ai-roi-demo-v4-v50/frontend && npm run build 2>&1 | tail -20

═══════════════════════════════════════════════════════
═══════════════════════════════════════════════════════
DIMENSION 12: CROSS-COPILOT TRANSFER SAFETY
═══════════════════════════════════════════════════════

12a. TRANSFER CENTROIDS SHAPE MISMATCH
     warm_start_centroids transfers from source to target copilot.
     If source has (5,4,10) and target has (5,4,7), what happens?
     Check: shape validation before write. Missing validation: P1.

12b. TRANSFER DK WEIGHT LEAK
     DK weights must NEVER transfer. Check: TransferPattern and
     warm_start_centroids exclude DK. If DK in payload: P1.

12c. TRANSFER CONSERVATION RESET
     After transfer, target conservation must reset (new learning
     epoch). Check: does transfer reset V/q/alpha? If old
     conservation state persists post-transfer: P2.

12d. CROSS-DOMAIN GRAPH QUERY ISOLATION
     After 5-copilot AGE migration, graph queries must scope by
     domain. Check: any Cypher query that reads Decision nodes
     without domain= predicate. Missing scope: P1.

═══════════════════════════════════════════════════════
DIMENSION 13: EVOLUTION / PROMOTION GATE CORRECTNESS
═══════════════════════════════════════════════════════

13a. PROMOTION GATE — INSUFFICIENT BATCHES
     4-gate check: 3 batches, 5pp improvement, GREEN conservation,
     stable variance. Check: can a variant with only 1 batch pass?
     If batch count not enforced: P2.

13b. SHADOW SCORER ISOLATION (Rule #61)
     Shadow scorer must use separate store from primary.
     Check: from_preset() rejects primary_store is shadow_store.
     If shadow writes to primary store: P1.

13c. AGENTEVOLVER VARIANT CLEANUP
     Rejected variants should not accumulate indefinitely.
     Check: is there a max_variants cap or cleanup? Unbounded: P3.

13d. SCORER EVOLUTION HARD BOUNDS
     ScorerEvolution proposes eta/penalty/temperature changes.
     Check: can any proposal exceed EvolutionBounds? If bypass
     path exists (e.g., direct attribute set): P1.

═══════════════════════════════════════════════════════
DIMENSION 14: MEASUREMENT SPINE CONSISTENCY
═══════════════════════════════════════════════════════

14a. COHORT STATE MACHINE — INVALID TRANSITIONS
     3 states: INSTRUMENT_VALIDATED → ACCUMULATING → MEASURED.
     Check: can state go backwards? Can it skip ACCUMULATING?
     Invalid transition: P2.

14b. ORACLE EXPERIMENT — SYNTHETIC IN PRODUCTION
     Oracle experiments use synthetic cohorts. Check: can oracle
     data leak into production graphs? F-27 gate must block.
     If oracle data written to AGE: P1.

14c. HOLDOUT ASSIGNMENT DETERMINISM
     SHA-256 holdout must be deterministic: same decision_id →
     same assignment. Check: any randomness in holdout? If
     non-deterministic: P2 (measurement invalid).

14d. CLAIM REGISTRY — PROMOTE WITHOUT EVIDENCE
     promote() requires evidence_ref. Check: can a claim be
     promoted to REAL tier without evidence? If yes: P2.

14e. PROVENANCE BADGE — STALE AFTER K4 FLIP
     When a metric flips from K3→K4, does the ProvenanceBadge
     update? If badge still shows "sample" after live data: P2.

═══════════════════════════════════════════════════════
DIMENSION 15: AGE TRANSACTION ATOMICITY
═══════════════════════════════════════════════════════

15a. SCORE+LEARN ATOMICITY
     score() creates Decision node; learn() updates it.
     Check: if learn() fails mid-write, is the Decision node
     left in inconsistent state? Transaction boundary?

15b. CONCURRENT DOMAIN WRITES
     5 copilots writing simultaneously. Check: can two copilots
     create Decision nodes with colliding IDs? Domain prefix
     (TRD-/PUR-/DOPS-/S2P-) should prevent. If not enforced: P1.

15c. ADVISORY-LOCK PATTERN
     AGE uses advisory-lock + MATCH-then-CREATE (not MERGE).
     Check: any AGE write that uses MERGE. If MERGE found: P2
     (Rule #50 violation).

═══════════════════════════════════════════════════════
DIMENSION 16: MULTI-COPILOT ENDPOINT PARITY
═══════════════════════════════════════════════════════

16a. HEALTH ENDPOINT CONSISTENCY
     All 5 copilots should return consistent /health schema.
     Check: do all backends return the same fields? Missing
     fields in any copilot: P3.

16b. CENTROID HISTORY ENDPOINT PARITY
     JM P0 shipped shared centroid_history_handler.
     Check: all 5 copilots mount /api/{domain}/centroid-history.
     Any copilot missing the endpoint: P2.

16c. COHORT STATUS ENDPOINT PARITY
     All 5 copilots should have /api/{domain}/cohort-status.
     Check: response schema matches across all 5. Missing or
     divergent schema: P2.

16d. CONSERVATION ENDPOINT PARITY
     All 5 copilots expose conservation status.
     Check: field names and state values match across copilots.
     If one copilot uses "green" while others use "GREEN": P3.

═══════════════════════════════════════════════════════
EXECUTION NOTES FOR v5
═══════════════════════════════════════════════════════

Run priority: Dimensions 12, 15, 7 first (shared-graph safety).
Then 13, 14 (evolution + measurement). Then remaining.

Per-repo focus:
  SOC: Dims 12d, 7e (domain scoping), 15 (transaction safety)
  SDK: Dims 13 (evolution), 16 (endpoint parity), 8g-8h
  S2P: Dims 12d (query isolation), 14 (measurement spine)
  CI:  Dims 15 (AGE atomicity), 2f (connection pool)
  GAE: Dims 4 (numerical), 5f (history growth)

OUTPUT FORMAT
═══════════════════════════════════════════════════════

For EACH numbered probe (1a through 11d):
  LOCATE: function signature with file:line
  TRACE: line-by-line variable state under the edge condition
  VERDICT: what happens (quote the exact line, ≤80 chars)
  CLASSIFY: P1 / P2 / P3 / OK with file:line citation

SUMMARY — sorted by severity:

P1 BUGS (fix before any demo/pilot):
  [file:line] description + trace summary

P2 BUGS (fix before pilot):
  [file:line] description

P3 ISSUES (backlog):
  [file:line] description

RACE CONDITIONS:
  [file:line] description + concurrent scenario

MEMORY/RESOURCE LEAKS:
  [object] growth rate + estimated size at 100K decisions

FRAMEWORK v4 INTEGRATION:
  [8a-8f] finding + severity

COVERAGE GAPS (from Dimension 10):
  [function] GAPS: scenario (severity)

TEST COUNTS:
  GAE: ~1,237 passed
  SOC backend: ~2,174 passed  
  SOC PW: ~391 passed
  ci-platform: ~582 passed
  S2P: ~1,627 passed
  SDK+apps: ~1,918 passed
  Trading PW: ~191 passed
  Purchasing PW: ~222 passed
  DataOps PW: ~127 passed
  S2P PW: ~86 passed

Rule: No evidence, no claim. No trace, no verdict.
Every P1 must have a reproducible trigger scenario.
Every OK must cite the specific guard line.
