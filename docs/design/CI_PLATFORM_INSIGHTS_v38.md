# Compounding Intelligence Platform — Deep Analysis Document
**Date:** June 12, 2026 · **Version:** v38.0 (Batch 6-10 pre-classification complete — 11 of 54 prompts are DROPs, TRD-FACTORS market_regime.compute() returns float correctly, RL-STATE-PERSIST already wired needs 2 store methods, prescore fully done, D-06 one-liner confirmed, AE-REAL-DATA is DataOps-only, 12 S2P routers untested)

**v32.0 changes from v31.0:**
- JUDGMENT MEMORY: All three proposed enhancements (bi-temporal checkpoints, conflict detection, consolidation boundaries) are ALREADY SHIPPED in scorer.py. The document was behind the code.
- BLOCK A FAIL: POST /learn returns 422 when conservation fires — LearnResponse required fields missing from pause dict. PW specs using response.ok() will fail. Fix: raise HTTPException(503) on conservation pause.
- broker_router.py EXISTS: 6 routes (status, account, positions, orders, orders/{id}, sync). Previous analysis was wrong.
- evolve=True WORKS: CompoundingScorer.from_preset("trading", evolve=True) triggers evolution every 20 decisions. OSS-EVOLVE is largely already built.
- S2P_KNOWN_DRIFT has stale byte counts: intervention_controls.py says "-114 bytes" but is now +5,513 bytes. audit.py says "-5118 bytes" but is now -1,805 bytes.
- FlexibleResponse with extra="allow" confirmed: extra fields preserved, no frontend breakage.
- Conservation 422 is a latent judgment memory risk: decision verification lost if conservation fires mid-session.
- consolidation_enabled defaults to False: copilots must opt in for clean trajectory charts.
- Part 49 added: complete Blocks A-G analysis + judgment memory architecture validation.

**v31.0 changes from v30.0:**
- A1-PRESEED DONE: skip_recommended present in Trading actions. Preseed has specific handling: if recommended != skip_recommended → return skip_recommended. Shipped in 4f26215.
- C1+C2 DONE: legacy scorer.py deleted (False), s2p_preview.py has zero ProfileScorer imports. Clean.
- S2P 19/19 EFFECTIVELY 200: clustering/payment 404s were wrong test paths. Both routers use prefix="/api/s2p/suppliers" — actual paths are /api/s2p/suppliers/clusters, /api/s2p/suppliers/payment-strategy etc.
- TRD-FACTOR-FALLBACK: confirmed low risk — fallback never fires because TradingPreset() imports cleanly. Technical debt only.
- All transfer routers mounted: Trading L246, Purchasing, DataOps all mount create_transfer_router(scorer_proxy). 404 was wrong test path.
- Zero confirmed blocking gaps as of commit 4f26215.
- Part 48 added: final gap closure + priority recommendations.

**v30.0 changes from v29.0:**
- S2P-PRESET LANDED: s2p now in SCORING PRESET_REGISTRY and RL PRESET_REGISTRY. All 4 domains registered.
- D1 FORMULA FIXED: s2p_performance.py now uses compute_theta_min(projected_override_rate, new_verified). Confirmed via Q5.2.
- 4f26215 COMMITTED: all 50+ previously uncommitted files now in SDK HEAD. SDK working tree clean (1 file).
- S2P 775 tests: up from 361. Major test expansion landed. 21 PW spec files.
- Trading smoke test: 5/15 = 200, but mostly path mismatches not absent endpoints. Broker HTTP API is stub-only (CLI exists).
- DataOps smoke test: 8/9 = 200. Very healthy.
- Purchasing smoke test: 6/8 = 200. evidence/factors path mismatch (route is /evidence/summary).
- S2P smoke test: timed out — startup blocking or fixture load time.
- Transfer router: 404 across Trading, Purchasing, DataOps — not mounted in any of them.
- TRD-FACTOR-FALLBACK: fallback only fires when TradingPreset import fails. Since preset imports fine, scrambled mapping never activates.
- A1-PRESEED: still not done per last ground truth scan.
- C1+C2: status unknown after 4f26215 — needs recheck.
- Part 47 added: comprehensive assessment results.

**v29.0 changes from v28.0:**
- CRITICAL: SDK repo has 50+ uncommitted changes since Batch H+I+J. All ground truth reflects working tree, not HEAD.
- RL-WIRE LANDED: del graph_store GONE, S2P in RL_PRESET_REGISTRY, scorer.py imports get_rl_components. copilot_sdk/rl/presets.py is a new untracked file.
- B1-FIX LANDED: gate.py != RED absent, _is_conservation_safe present, evolver_factory present.
- SCORER-INF FIXED: no float("inf") in scorer.py.
- Bootstrap both correct: trading (5,4,7) and purchasing (5,4,7).
- C3-BROKER LANDED: brokers/ dir, IBKR+Alpaca+CSV connectors, broker CLI functions.
- S2P-GAPS PARTIAL: novelty endpoints landed, financial-impact and supplier analysis (trends/heatmap/correlations) still missing.
- A1-PRESEED NOT DONE: skip_recommended still absent from preseed.
- C1+C2-LEGACY NOT DONE: legacy scorer.py still exists, s2p_preview.py still uses ProfileScorer.
- D1-FORMULA NOT DONE: PENALTY_RATIO formula still in s2p_performance.py.
- TRD-FACTOR-FALLBACK: names now match preset but class implementations are scrambled.
- A2 PW spec updates partially in progress (7 spec files modified in working tree).
- New untracked files include social.py (C2-SOCIAL), webhook.py (C6-WEBHOOK), analytics.py, purchasing CLI, new test files for RL.
- Part 46 added: complete ground truth table.

**v28.0 changes from v27.0:**
- Part 45: Complete fix sequencing with dependency graph, parallel safety analysis, phased plan.
- C1 SAFE: only demo/s2p_demo.py and s2p_preview.py import legacy scorer. Core s2p.py does NOT. C1+C2 can land Phase 1.
- D1 COMPLEXITY: what_if() needs override_rate from get_verified_decisions() — two extra lines vs simple formula swap.
- A1 TRADING-ONLY: Purchasing already has 4 actions. Only Trading preseed needs skip_recommended added.
- B2 RISK: Adding RL state to GraphStore Protocol forces updates to all 4 store implementations. Protocol-free alternative documented.
- Phased sequence: Phase 1 = A1+C1/C2+D1+E1 (parallel), Phase 2 = A2+B1+B3, Phase 3 = B2+F1, Phase 4 = B4.

**v27.0 changes from v26.0:**
- PART 41: PW regression NOT caused by CORS (all apps identical). Caused by Batch H+I+J modifying 12 frontend files simultaneously without PW spec updates. Second cause: preseed only seeds 3 of 4 Trading actions (skip_recommended missing).
- PART 42: SCORER-CACHE VERIFIED — lazy singleton, RLock, shared graph_store, no-op close. RL-PERSIST INCOMPLETE — del graph_store still in presets.py, no save_rl_state/load_rl_state methods. S2P legacy ProfileScorer STILL EXISTS in domains/s2p/scorer.py and s2p_preview.py.
- PART 43: _PreDomainEvolutionStoreAdapter GONE (SDK-CLEANUP complete). Three conservation formula variants persist: SDK canonical, DataOps inline, S2P wrong denominator. S2P test coverage unchanged (11 routers, zero tests).
- PART 44: 24 Trading components have useEffect API hooks — any API failure causes silent empty panel = PW failure without error. Trading has 16+ routers vs Purchasing 8.
- Spec file path corrected: e2e/trading/ not apps/trading/e2e/.
- Parts 41-44 added.

**v26.0 changes from v25.0:**
- Q1 ANSWERED: CreditAssigner.assign() is pure math only. reward × 0.95^age distributed by factor_contributions weights. No graph queries. Adding TRIGGERED_EVOLUTION traversal requires new design.
- Q2 ANSWERED: ConservationBoundedThompson state = alpha[n_actions] + beta[n_actions] + _conservation_status. get_priors() serializes exactly what needs persistence. reset() exists. No history buffer.
- Q3 ANSWERED + AUDIT CORRECTION: DOPS-AGE-FIX is correctly implemented. AGEClient import is lazy inside try/except inside _load_age_client_class(). Every method has fixture fallback. Rule #29 violation was FALSE POSITIVE — reclassified to LEGITIMATE.
- Q4 PARTIAL: FreshScorerProxy not found in scorer.py — located elsewhere. Signature: FreshScorerProxy(domain, db_path, store_factory). Factory pattern confirmed — creates fresh store per request.
- Q5 CONFIRMED: decision_id_prefix on SQLiteGraphStore constructor line 42. Already documented.
- Q6 ANSWERED: 44 routes across 10 active S2P routers need tests. framework_router.py excluded (28 /soc/* routes unmounted by S2P-FW-ROUTER-CLEANUP, file kept but not served).
- Part 40 added: complete Q1-Q6 answers.

**v25.0 changes from v24.0:**
- TASK 9 CLOSED: get_rl_components() does `del graph_store` immediately — store is discarded. All RL components (CreditAssigner, ConservationBoundedThompson) are in-memory only. Rule #35 VIOLATED for RL state.
- Thompson posteriors reset to uniform Beta(1,1) on every restart — eliminates the benefit of Thompson sampling accumulation.
- CreditAssigner() with no graph_store cannot traverse TRIGGERED_EVOLUTION edges — credit assignment is degraded or empty.
- S2P and SOC absent from RL_PRESET_REGISTRY — S2P silently disables RL via try/except.
- exploration_used hardcoded False confirmed — exploration tracking loop never closes.
- Fix: pass graph_store to CreditAssigner and ConservationBoundedThompson constructors.
- Part 39 added: Task 9 complete RL audit. (GraphStore architecture audit — S2P-PERSIST confirmed, DOPS-AGE-FIX incomplete, EvolutionStore separated, RL partial wiring unknown)

**v24.0 changes from v23.0:**
- S2P-PERSIST VERIFIED: SQLiteGraphStore at app/data/s2p.db, domain="s2p", decision_id_prefix="S2P-", test isolation via :memory:. Single instance pattern. ✅
- DOPS-AGE-FIX INCOMPLETE: graph_queries.py:43 still imports AGEClient directly. Conditional import may gate runtime but violation persists at import level.
- Task 7: Zero InMemoryGraphStore in production. ✅
- Task 3: EvolutionStore separated at protocol level. scorer.py casts GraphStore as EvolutionStore via _DomainEvolutionGraphStore adapter. _PreDomainEvolutionStoreAdapter still exists (P3 debt). Protocol has grown from 11→15 methods.
- Task 12: Only S2P uses decision_id_prefix. Trading/Purchasing/DataOps have none — recommend TRD-/PUR-/DOPS-.
- Task 1/5: Trading/Purchasing/DataOps use fresh-instance-per-call factory, not single shared instance. Data consistent via SQLite file, but not same pattern as S2P.
- Task 9 (RL storage): PARTIALLY STALE — user did partial RL wiring unknown to analysis session. Needs fresh read of scorer.py rl section.
- GraphStore protocol has 4 new methods: load_latest_centroids, count_decisions, archive_old_decisions, count_archived.
- Part 38 added: GraphStore architecture audit report.

**v23.0 changes from v22.0:**
- Q2 P1 CONFIRMED: trading_bootstrap.json is (5,3,6) not (5,4,7). Preset validates shape and falls back to uniform 0.5 priors. Trading copilot starts cold on every restart. Fix: regenerate bootstrap JSON.
- Q3 ANSWERED: Purchasing 7th factor = price_memory_index (historical price tracking per supplier×category).
- Q5 ANSWERED: S2P 7 factors confirmed: match_status, amount_variance_ratio, duplicate_score, supplier_exception_history, payment_terms_impact, commodity_index_correlation, tax_regulatory_compliance.
- Q6 DOWNGRADED to P2: float("inf") is in conservation STATUS display helper, not in _conservation_pause() gate. UI display corruption only, not centroid corruption.
- Q7 P1 CONFIRMED: ledger.py save_evolution_event() call omits domain parameter. Cross-domain event queries impossible.
- Q8 P2 CONFIRMED: DefaultPromotionGate passes when conservation_state=None (defaults to GREEN). AMBER should block promotion but doesn't. Fix: change != "RED" to == "GREEN".
- Q10 CONFIRMED CORRECT: _conservation_pause() gate uses gae.calibration.compute_theta_min. Formula is canonical. Display method (lines 390,492) uses penalty_ratio formula — display only, not enforcement.
- Part 37 added: complete Q&A answers and updated action list.

**v22.0 changes from v21.0:**
- Trading actions CORRECTED: strong_execution/partial_execution/poor_execution/skip_recommended — NOT buy/hold/sell. Trading reframed from directional to execution-quality copilot.
- Trading 6th screen RESOLVED: TradeDetailScreen is a drill-down, not a 6th primary tab. CHECK-14.7 expectation should be updated to 6.
- copilot_sdk/rl/ is COMPLETE but UNWIRED: RewardFunction, RewardComputer, 4 domain reward functions, CreditAssigner, ConservationBoundedThompson all implemented. Zero imports anywhere outside rl/__init__.py. Ready but not connected to any scorer or app.
- AGEGraphStoreAdapter EXPLAINED: Docstring says "Transitional SDK GraphStore-compatible wrapper." It's the migration bridge allowing SOC/ci-platform AGEGraphStore to be used through the same Protocol as SQLiteGraphStore. Not a design smell — a deliberate migration tool.
- S2P InMemoryGraphStore CONFIRMED intentional: decision_id_prefix is just namespacing. One-line fix to SQLiteGraphStore would persist all S2P state.
- q_window=400 and temperature=0.1 CONFIRMED everywhere. CHECK-3.6, 3.7 pass.
- Part 36 added: final validation scan closures.

**v21.0 changes from v20.0:**
- TENSOR SHAPES CORRECTED: Trading now (5,4,7) — was (5,3,6). Purchasing now (5,4,7) — was (5,4,6). n_actions AND n_factors both changed for Trading. All previous references to these shapes are stale.
- TRADING PENALTY_RATIO CORRECTED: 3.0 — was 2.0 in insights doc.
- S2P USES InMemoryGraphStore — all S2P learning decisions lost on server restart. Not persisted to disk. Conservation law computed from zero after every restart.
- CHECK-2.3 FAIL: DataOps graph_queries.py:43 imports AGEClient directly (Rule #29 violation).
- CHECK-20.5: 11 S2P routers with zero test coverage — 69 of ~109 routes untested.
- CHECK-14.7: Trading has 6 screens (expected 5) — one extra undocumented screen.
- Trading massively expanded: 26 routes across 10 files, 574 test functions in 29 files.
- copilot_sdk/rl/ package confirmed: exploration.py, reward_functions.py, reward.py, credit.py — RL extracted from SOC into SDK.
- Trading factor registry fallback mismatch: hardcoded fallback names don't match actual preset factor names.
- Part 35 added: complete fitness check results.

**v20.0 changes from v19.0:**
- SCAN 3 CORRECTED: _conservation_pause() gate uses compute_theta_min(override_rate, verified) from gae.calibration — canonical formula. penalty_ratio formula only in display/status reporter. Conservation enforcement is correct; display inconsistency only.
- RL ENGINE NOT REGISTERED WITH STATE_MANAGER (D3): reset_rl_state() not called on demo reset. RewardLedger, ExplorationPolicy priors, RewardComputer rolling history all survive demo resets.
- _S2PGraphStore PRIVATE CLASS IN S2P MAIN.PY (E1): S2P defines its own GraphStore subclass inside main.py instead of using SQLiteGraphStore. Design smell — fifth implementation.
- AGEGraphStoreAdapter UNKNOWN (E1): ci_platform/graph/age_sdk_adapter.py has a sixth GraphStore implementation. Purpose unknown.
- save_evolution_event() IN AGEGraphStore BUT NOT IN PROTOCOL (E4): SQLiteGraphStore lacks this method. AE events cannot be durably stored in SQLite backends. SDK copilots cannot persist AE events.
- scorer.py:48 returns float("inf") on error (B2): Infinity propagates into centroid distance calculations → softmax NaN → undefined probabilities.
- platform.py 6 caches NOT registered with state_manager (D1): Stale pre-reset data returned after demo reset until cache miss.
- DataOps ae_router reads evolution_fixtures.json 3x per request, no caching (C1).
- Part 34 added: full 5-batch architectural scan results.

**v19.0 changes from v18.0:**
- MAP v5.96 sync: F17-DISCOVERY shipped (DiscoveryEngine + 4 patterns, SDK +21 tests), AE-EVOLUTION-ADV shipped (ContextAwareSelector + StepCreditAssigner + AutonomousPromotionGate, SDK 395→446), SOC-BUG-BATCH + SOC-BUG-BATCH-2 shipped, S2P-FW-ROUTER-CLEANUP shipped (28 /soc/* routes unmounted).
- Test counts updated: SDK=446, Trading=36, Purchasing=40, DataOps=129, S2P=361, ci-platform=242+11skip, SOC=1614+3skip, SOC E2E=291, SDK E2E=226. Total ~4,870.
- Conservation formula inconsistency (SCAN 3) now in MAP queue as item #6 (SOC-CONSERVATION-FORMULA, 1d effort).
- New known issues: DataOps fails 6 tests when GRAPH_DSN set (workaround: GRAPH_DSN=""). test_unique_timestamps skipped (SOC seed doesn't write Decision.timestamp to AGE).
- New standing rule #41: S2P AgentEvolver uses SDK evolution infrastructure.
- Tags: v0.6.7-sdk, v0.6.2-s2p, v5.81.
- Part 34 added: expansive architectural scan design and results. (10-scan architectural review — conservation formula inconsistency confirmed, S2P intervention_controls diverged, duplicate helpers in S2P)

**v18.0 changes from v17.0:**
- SCAN 3 MATERIAL: Conservation formula inconsistency. SOC uses 23.53/(alpha×V) where alpha=oversight fraction. SDK uses 23.53/(penalty_ratio×verified) where penalty_ratio=2-20. SDK formula is 3-12× more permissive than SOC for same decision count. penalty_ratio is NOT a substitute for alpha.
- SCAN 5 MATERIAL: S2P intervention_controls.py is now 5,513 bytes LARGER than SOC (was 114 bytes smaller). S2P has diverged into an extension, not a copy. Drift test will fail — KNOWN_DRIFT must be updated.
- SCAN 5: S2P audit.py improved from -5,118 to -1,805 bytes behind SOC. Partial backport landed. Still behind.
- SCAN 7 DEBT: Three separate _find_invoice() implementations across S2P routers (s2p_control_tower, s2p_insight, s2p.py with different signatures). s2p_data_helpers.py exists but underused.
- SCAN 6 INCOMPLETE: Frontend calls /api/s2p/insight/*, /api/s2p/evidence/*, /api/s2p/performance/* — backend routes not confirmed. Need follow-up grep.
- SCAN 4 INCOMPLETE: graph_contract.py files not read (PowerShell syntax error). App code shows no AGE node label usage — contracts appear to be forward-looking specs for future AGE wiring.
- All other scans clean: store bypass (1), evolution isolation (2), module globals (8), test coverage (9), cross-repo imports (10).
- Part 33 added: 10-scan results.

**v17.0 changes from v16.0:**
- Gap 4 (S2P composite_gate wrong categories) CLOSED: S2P composite_gate.py already uses S2P categories (price_variance, quantity_mismatch, duplicate_risk, contract_gap, format_compliance). Drift test entry was misleading — the files SHOULD differ. No backport needed.
- S2P dual-scorer pattern confirmed: CompoundingScorer in app.state (new SDK endpoints) + ProfileScorer singleton in scorer.py (legacy IKS/score_event). Both active simultaneously.
- AE extraction blueprint confirmed: evolver.py is LEGACY UCB (hardcoded variants). Real AE-01→04 is variant_generator.py + promotion_gate.py. Extraction must carry this distinction.
- conservation_router penalty_ratio resolution confirmed: reads store.penalty_ratio set directly on SQLiteGraphStore instance.
- AGEGraphStore has 2 extra methods not in Protocol: query_context() and query_similar() — used by S2P graph context resolution.
- demo.py ports: Trading=8010/5174, Purchasing=8020/5175, DataOps=8030/5176, S2P=8002/5177. SOC NOT in demo.py.
- preseed_all_copilots.py: idempotent (checks /api/trajectory), 3 domains only (Trading/Purchasing/DataOps). S2P not preseeded.
- Parts 31-32 added: Complete Blocks A-G answers for coding session.

**v16.0 changes from v15.0:**
- GAP 1.1 CLOSED: Conservation gate now enforced in CompoundingScorer.learn() via _conservation_pause() reading live GraphStore counts. No more ungated learning.
- GAP 1.2 CLOSED: Conservation state reads from GraphStore.count_verified()/count_correct() — live data, no JSON fallback in learning path.
- GAP 7 CLOSED: _StoreProxy retired in v0.5.7-sdk. _FreshScorerProxy.store is now SQLiteGraphStore (full GraphStore protocol including count methods).
- GAP 3.1 CLOSED: RL-SDK shipped (RL-SDK ✅ per MAP). CompoundingScorer accepts credit_assigner and explorer. SDK copilots now have RL.
- MAJOR ARCHITECTURE UPDATE: GraphStore is now a Protocol (copilot_sdk/graph/protocol.py) with SQLiteGraphStore as primary SDK implementation. Rule #35: ALL platform data through GraphStore. DecisionStore is now internal implementation detail.
- Test counts corrected per MAP v5.92 baseline: SDK=249, DataOps=120, Trading=26, Purchasing=33, S2P=280, ci-platform=224+8skip, GAE=1237, SOC=1572, E2E=280. Total ~4,221.
- STILL OPEN: S2P framework drift (Gaps 4,5,6 — composite_gate, intervention_controls, audit.py). S2P-PRESET Gap 10 (#19 in queue). Evolution ledger Gap 9 (AE-SDK #1 not yet shipped).
- Part 30 added: GraphStore architecture and revised gap status.

**v15.0 changes from v14.0:**
- Source line count verified: 170,227 lines across 6 repos (Python 137,524 · TypeScript/TSX 32,703). Includes all test sources. See §Platform Scale below.
- Issue B (RL exploration vs referral VETO) CONFIRMED NOT A BUG. Code correctly handles this with `_rl_explored_but_referred = True` flag. VETO overrides explored action correctly. Note: referral rules receive `stage1_action = _scoring_result.action_name` (original scorer action, not explored action) — deliberate design, worth documenting for future rule authors.
- Confirmed issue count finalised: 9 confirmed bugs (7 P1, 2 P2). Issue list is complete.
- POSTERIORSTORE RESOLVED: Uses PostgreSQL at localhost:5433/soc_copilot (same WSL2 instance as AGE). NOT file/SQLite. Fail-open — save() and load() silently log warning on failure. WSL2 down = in-memory priors for session only (DB persists when WSL2 returns). More resilient than feared but WSL2 dependency is real.
- TRIAGE EXPLORATION LOCATION: Lines 520-580 show Steps 8a (provenance) and 8 (visualization) — post-decision steps. Exploration decision is earlier in pipeline (before action selection). Issue B (VETO interaction) remains unconfirmed — different line range needed.
- S2P DRIFT FULLY CATALOGUED from drift test: composite_gate.py same size different content (wrong category thresholds — P1), intervention_controls.py -114 bytes (conservation wiring absent — P1), audit.py -5118 bytes (async/OutcomeEntry/epoch missing — P1), 7 more files with minor drift.
- Part 29 added: Final confirmed findings + complete issue priority table.



**v13.0 changes from v12.0:**
- All 5 domain presets fully read. Complete platform tensor shape table documented.
- Key finding: eta_confirm=0.05, eta_override=0.01, temperature=0.1 are IDENTICAL across all 5 domains — GAE mathematical constants, not domain-tunable.
- penalty_ratio varies 10× across domains: Trading=2.0, Purchasing=3.0, S2P=5.0, DataOps=10.0, SOC=20.0 — reflects asymmetric error cost per domain.
- Purchasing uses live weather data: get_weather_factor from copilot_sdk.scoring.verification.weather.
- Bootstrap centroids from JSON files with shape validation + 0.5 fallback — good defensive pattern.
- PRESET_REGISTRY confirmed: {dataops: DataOpsPreset, purchasing: PurchasingPreset, trading: TradingPreset}. S2P not yet in SDK registry.
- Part 28 added: Complete domain preset analysis.



**v12.0 changes from v11.0:**
- Part 25 gaps ALL RESOLVED in implementation: Gap 1 (SHAP→finite differences, correct), Gap 2 (chain credit formula: HALF_LIFE=30, LOOKBACK=100, CHAIN_DISCOUNT=0.5, exponential decay), Gap 3 (exploration formula: rate=epsilon_base×min((headroom-1)/(target-1),1); headroom≤1→rate=0).
- rl_engine.py fully read: RewardComputer (SOC: severity×campaign_multiplier, S2P: financial_impact/reference×cluster_multiplier), ExplorationPolicy (Thompson sampling, PosteriorStore persistence), CreditAssigner (TRIGGERED_EVOLUTION graph query, AGE-compliant), rolling 400-decision reference window.
- Cross-signals confirmed: /api/platform/cross-signals with XC-SOC-S2P-001/002/003 fixture signals. SOC→S2P direction only. R-02 infrastructure exists, fixture-based.
- Platform router discovered: /api/platform/* namespace with rl-reward-demo, rl-exploration-demo, cross-signals, chain-credit-demo, warm-start-evidence, domain-applicability endpoints.
- DomainPreset is a Protocol (duck typing), not base class. temperature field required (not in old DomainConfig).
- evolution_router factory: /evolution/variants and /evolution/patterns. warm_start_prior field designed for cross-copilot transfer.
- presets.py not found at expected path — PRESET_REGISTRY location TBD.
- Part 27 added: RL engine analysis + Part 25 gap closure.



**v11.0 changes from v10.0:**
- MAJOR ARCHITECTURE CORRECTION: SDK copilots (Trading, Purchasing, DataOps) use SQLite via DecisionStore, NOT AGE/PostgreSQL. Framework copy problem resolved for these copilots — they import directly from copilot_sdk. SOC remains on AGE.
- RL CONFIRMED IMPLEMENTED in SOC: ExplorationPolicy (Thompson sampling, alphas[C][A]), CreditAssigner (assign_chain_credit), RewardLedger, 4 feature flags. RL-01→03 design docs are now implementation docs.
- CompoundingScorer is the SDK's core: GAE ProfileScorer + SQLite DecisionStore + DomainPreset. clean factory pattern, no async, no graph client.
- IKS formula corrected: CompoundingScorer uses 4-component 100-point formula (volume 25 + accuracy 25 + fingerprint 25 + coverage 25). Different from SOC's IKS.
- HAVING in DecisionStore is SQLite HAVING (supported) — NOT the AGE HAVING bug. AGE bugs scope is SOC only.
- SDK reward computation lives in scoring_router._signed_reward() — domain-aware graded rewards (trading, purchasing, dataops formulas).
- Test counts updated per MAP v5.86: GAE=1237, SOC=1572, E2E=280, ci-platform=188, S2P=141, copilot-sdk=127, Trading=22, Purchasing=22, DataOps=81, SDK E2E=117, Total=~3787.
- Part 26 added: Full SDK architecture analysis.



**v10.0 changes from v9.0:**
- Part 25 added: RL Design Addendum v1.0 analysis. Library choices confirmed correct (numpy + scipy, zero mandatory new deps). Four design gaps identified: SHAP integration underestimates cost, chain credit mechanism unspecified, conservation-bounded exploration formula missing, S6 cross-domain scenario overstates transfer. Schedule: +0.5 days (not +1) if R6 benchmark replaced with synthetic bandit validation.



**v9.0 changes from v8.0:**
- AE-REVIEW COMPLETE (Top 20 v9 #1 done). Initial verdict FAIL, final verdict PASS WITH P3.
- P1 FIXED: Promotion batch-count gate — fewer than MIN_SHADOW_BATCHES=3 shadow batches could produce promote verdict. Fixed: evaluate_promotion() returns continue when batch_count < 3. 54 promotion gate tests passing.
- P2 FIXED: Stale shadow buffer entries not pruned — verified entries for missing/non-shadow variants triggered repeated flushes indefinitely. Fixed: _flush_shadow_batch() now tracks and removes stale_ids. 39 shadow runner tests passing.
- P2 FIXED: Rollback handler silent drop without event loop — sync handler silently did nothing outside running asyncio loop. Fixed: captures loop at registration, logs warning when no loop. 
- P3 REMAINING: reset_promotion_gate() doesn't unregister GAE ConservationStateMachine handlers — future hardening only.
- Architecture confirmed: all 5 design intent claims verified (graph-context-driven, durable events, P16 separation, four-gate invariant, Evidence Room endpoints). Cross-module coupling clean. AGE query safety all PASS.
- State management table verified: _REGISTRY, _shadow_buffer, _SHADOW_INDEX, _REGISTERED_STATE_MACHINES, PROMPT_STATS all have reset paths. Stale buffer bug now fixed.



**v8.0 changes from v7.0:**
- CA-SOCAGENT CORRECTED: MAP v5.65 explicitly says "dead code, zero imports, P3 delete." Q6 finding (SOCAgent in live triage path) was based on stale code — removed from live path during May 3-5 sprint. Update: NOT in live path.
- Pilot checklist: 9/9 ALL DONE per MAP v5.65. All pilot code items complete.
- datetime() + HAVING fixes: Tier 0C ALL 8 resolved. These are no longer open P1s.
- CA-PROTO-1/2/3 DONE: FactorComputer protocol issues (factor_name/factor_index/polarity) resolved in May 3-5 sprint.
- BACKLOG-074/079/080 DONE: audit.py backport and S2P framework items complete.
- CLAIM-RECONV WITHDRAWN: EXP-G1 v3 — γ_centroid=1.02 (trivial, not >1). DK HURTS convergence 1.9× after disruption. CLAIM-DK-STALE added.
- Test counts corrected: GAE=1203, SOC=1340, E2E=271, SDK=23, Total=~3143.
- AgentEvolver COMPLETE: 256 tests, 7 consecutive zero-fixer Codex results. AE-01→04 + 5 enhancements.
- RL design v1.0 complete: 3 documents. RewardComputer/CreditAssigner/ExplorationPolicy design ready. Next: RL-01→03 implementation.
- Top 20 v9: AE-REVIEW (#1, Codex prompt ready), CLAIMS-UPDATE (#2), RL-01 (#3).
- Narrative: 17/17 contradictions + 7/7 gaps fixed. Complete.
- FEATURE-09 GovernanceTab confirmed shipped (Tab 7).



**v7.0 changes from v6.0:**
- Q2: AgentEvolver structure mapped — evolver.py (UCB selection), evolution_ledger.py (AE-04 in-memory, NOT hash-chained), variant_generator.py (AE-03 graph-driven), admin.py (manual triggers). EvolutionLedger is separate from TRIGGERED_EVOLUTION edges (W2 flywheel).
- Q3: evidence_room.py = 9,797 bytes (40% larger than review). FEATURE-09 shipped as Tab 7 GovernanceTab.
- Q4: FW-10 = LearningStatePanel endpoint (framework_router.py:930). FW-13 = S2P constants (S2P_ENRICHED_PLATEAU, S2P_COLD_PLATEAU). Both backend-only.
- Q6+Q7: Triage pipeline confirmed. analyze_alert: factors → score → referral VETO → AE-02 shadow (fire-and-forget). report_decision_outcome: conservation → LEARNING_ENABLED → acquire_scorer → guarded_update → IKS → TRIGGERED_EVOLUTION.
- Q12 CRITICAL: Tab count is 7, not 5+1. GovernanceTab (governance) is Tab 7 — Evidence Room shipped. Default tab is 'evolution' (RuntimeEvolutionTab). VIS-2 cross-tab navigation via custom events.
- Q13: NO global state store. Zero createContext/useReducer/Redux/Zustand in frontend. Each tab manages its own state independently. Cross-tab updates are eventual (re-fetch on mount/action).
- Q14: Test organization mapped. test_tab_content.py (55KB) is the contract validation test. No shared test graph — uses mocks or live AGE. AgentEvolver has 3 dedicated test files (38KB + 30KB + 14KB + 23KB + 22KB).
- Q15: validate_contracts.py and collect_tab_content.py are in scripts/ — manual only. test_tab_content.py is the CI version.
- Q16: RL reward in feedback_base.py:147 (get_reward_summary). No RewardComputer/CreditAssigner classes yet. RL-01 should land in new app/services/rl_engine.py, wired into triage.py:report_decision_outcome() after guarded_update().



**v6.0 changes from v5.0:**
- Q10 CLOSED: SOCAgent removal from copilot-sdk is zero-risk. No SDK test or import references it outside agent.py itself. Effort: 5 minutes.
- Q11 CLOSED: `.name` blast radius confirmed — 9 call sites across 5 files (evolution.py×2, soc.py×1, triage.py×4, gae_state.py×1, simulation.py×1). Recommended fix: add `.factor_name = name` property alias (zero blast radius, 6 lines) rather than rename (2 hours + 9 call sites).
- Q12 CLOSED: S2P framework copy IS actively imported (scorer.py, ols_status.py, intra-framework imports). BACKLOG-079 confirmed P2 — not dead scaffolding. Three-way drift detection test needed.
- Q13 CRITICAL: datetime() failure produces spike_threshold=5.0 (absolute). ANY deployment with >5 alerts/day triggers permanent category freeze → ALL learning halted from Day 1. **datetime() fix upgraded from P2 (demo) to P1 (pilot blocker).** Must fix before LEARNING_ENABLED=True.

  
**Scope:** 5-repo platform — GAE, SOC, S2P, ci-platform, copilot-sdk  
**Sources:** Design docs (math_synopsis v15, gae_design v10.8, soc_copilot_design v5.8, framework v4, s2p v1.3), REVIEW.md (8-file SOC backend review), graphify graph (9,259 nodes / 15,534 edges), session instructions §1–§9, roadmap session feedback  
**Authority:** Code is authoritative where it conflicts with docs

**v5.0 changes from v4.0:**
- Part 15 added: Protocol definitions review — FactorComputer.factor_name vs SOC's `name` is a breaking API contract break. PyPI not ready. 3 breaking issues + 1 doc gap identified.
- Part 16 added: S2P Preview Tab review — live ProfileScorer scoring confirmed for /queue and /conservation. /compounding is synthetic demo, labeled as such. Demo-ready.
- Part 17 added: Bootstrap pipeline review — fully automated pipeline exists in ci-platform. Gap: no API endpoint to trigger it from customer alert data. "$1.91 onboarding" claim depends on Block 1 API endpoint.
- Part 18 added: audit.py tamper-evidence CONFIRMED — verify_chain() recomputes SHA-256 from payload, checks prev_hash links. EU AI Act Article 12 claim is supportable. BACKLOG-074 backport scope documented.
- Part 19 added: SAML auth review — SSO flow is correct. Gap: JWT cookie not wired into request.state.user in triage path. 1-2 hour middleware fix, not implementation work.
- Part 20 added: RuntimeEvolutionTab review — stable for Loom. All endpoints live. Hardcoded "Learning active" green indicator is a UI bug. Graceful error handling per section.
- Third S2P framework copy confirmed — s2p-copilot/backend/app/framework/ is a third copy of the framework layer alongside SOC's and copilot-sdk's.


- Q2 CLOSED: HAVING confirmed broken on AGE — hard syntax error "syntax error at or near HAVING". compute_analyst_precision() silently broken — threshold filter never executes, all analysts included. Fix: remove HAVING, filter in Python post-query.

**v3.0 changes from v2.0:**
- Q5 CLOSED: D-05 CONFIRMED IMPLEMENTED. acquire_scorer() L43, acquire_scorer_for_reset() L57 both exist in gae_state.py. CA-P1-05 resolved.
- Q3 RESOLVED: audit.py drift is intentional — SOC's app/framework/audit.py is canonical (async, hash-chained OutcomeEntry, epoch archive, rebuild_from_age). SDK version is an earlier simpler iteration. Fix direction: backport SOC→SDK. Drift detection test should compare against SOC as canonical.
- Q6 CRITICAL: SOCAgent is NOT dead code. Import chain: copilot_sdk/framework/agent.py → app/framework/agent.py (copy) → app/services/agent.py (wildcard re-export) → triage.py:12 + evolution.py:13. SOCAgent is in the live triage path.
- Q8 CLOSED: /api/soc/threat-landscape not called by any frontend .tsx. AGE COUNT(CASE WHEN) compatibility question is moot for demo/pilot.
- Q9 CONFIRMED P3: No observed seed_graph partial failures, no test coverage. Theoretical production risk only.
- Q4 CONFIRMED P2: report_decision_outcome() receives decision_id from client — stale ID from post-reset submission is the realistic failure mode.
- Q1 CONFIRMED: datetime() failure is silent — fallback masks it. P2 stands.
- Q7 CONFIRMED: $param edge cases handled correctly by AGEClient for known parameter set.

**v2.0 changes from v1.5:**
- MAJOR CORRECTION: BUG-P1-03 and BUG-P1-SOC-01 through SOC-04 reclassified from P1 to P2. AGEClient._sync_execute() handles $param substitution at Python level. Only datetime() calls and HAVING clause are real AGE violations.
- Part 14 added: Full cross-repo architecture analysis — 6 import wires, framework copy drift confirmed, SOCAgent in live path, AGEClient quality assessment, contract test gaps.
- Three-layer architecture corrected: ci-platform=infrastructure, copilot-sdk=framework+protocols, SOC=domain copilot.

**v1.3 changes from v1.2:**
- Part 12 added: Full factors.py analysis — 6 active factor computers, D-01 polarity mechanics confirmed, AGE compliance clean in active path, TravelMatchFactor latent bug (inactive), TD-014/TD-015 documented.
- D-01 edge case: no-TI alerts return 0.0 (same as max-threat IOC) — reduces discriminative power.
- SOC_FACTOR_TEMPLATES confirmed as demo backward-compat layer.

**v1.2 changes from v1.1:**
- §8 inspections complete — learning_rate/η_confirm separate, LEARNING_ENABLED 2-checkpoint gate, θ_min duplicate flagged, D-02/D-07/stubs all confirmed correct.
- Part 11 added: Full cross_graph_discovery.py analysis — 4 algorithms, no P1 bugs, 1 P2, 2 v6.5 design notes.

**v1.1 changes from v1.0:**
- WeightProvenance constructor labels corrected. W2 flywheel: D-02 fixed READ path only. LEARNING_ENABLED=False is deliberate demo config. BUG-P1-08 reclassified P3. P1 bug priorities reordered per roadmap session feedback.

---

## Part 1 — Mathematical Framework (What the Code Is Doing)

### 1.1 The Core Scoring Equation

```
score(f, c, a) = -Σᵢ w̃ᵢ × (fᵢ - μ_{c,a,i})²
w̃ᵢ = α × w_DK_i + (1 - α)     [shrinkage-interpolated weight]
```

- At α=0 (current default, ContinuousStrategy): pure L2 distance, hyperplane boundaries
- At α>0 (Phase 2, v6.5): DiagonalKernel active, quadric boundaries
- Softmax temperature τ=0.1 sharpens the output probability distribution
- Output: action probabilities P(a|f,c) for A=4 actions

### 1.2 Two-Phase Learning (Framework v4 — designed, not yet deployed)

**Phase 1 (T₀ — Order-0 profile state):** Estimates WHERE centroids cluster  
- μ_{c,a,:} updated on every verified decision via `ProfileScorer.update()`  
- η_confirm=0.05 (confirmations), η_override=0.01 (overrides, 5× attenuation)  
- Saturates ~200 decisions per (c,a) pair  
- Transfers across deployments (+28pp)

**Phase 2 (T₁ — Order-1 profile state):** Estimates WHICH DIMENSIONS MATTER  
- DK weights = "discriminative precision weights" (NOT inverse variances in deployed context)  
- Estimated via coordinate descent on classification accuracy  
- Requires Phase 1 convergence, data-driven via batch pipeline  
- Firm-specific, does NOT transfer (-5.6pp if attempted)  
- James-Stein shrinkage: `w̃ = α × w_DK + (1-α)` — mathematical guardrail

### 1.3 Conservation Law (The Safety Guarantee)

```
α · q · V ≥ θ_min     where θ_min = 23.53 / (α × V)
```

**Critical invariants:**
- θ_min is a FORMULA, not a constant (§3 Rule 2)
- q = rolling verified accuracy over LAST 400 DECISIONS — NOT confidence (v14 change)
- α = fraction verified AMONG VERIFIED DECISIONS — not among all decisions (§3 Rule 10)
- State machine: GREEN → AMBER (learning paused) → RED (scoring degraded)

**Why q is rolling accuracy not confidence:** DK calibration degrades at high noise ratio (ECE 0.42 at NR=5.0 vs 0.04 for L2). Using confidence-based q would make the conservation law unreliable under the exact conditions where it matters most.

### 1.4 Re-convergence Theorem (γ > 1)

```
γ > 1 ⟺ ε_firm > ε_firm★ ≈ 0.125
```
- CONDITIONAL: requires category-sparse disruption + warm-started + ε_firm > 0.125
- ε_firm★ ≈ 0.125 (NOT 0.387 or 0.128 — §3 Rule 1)
- Four proof paths validated (GPT-4.1, Opus 4, Grok 3 ×2)
- Production range 0.15-0.40

### 1.5 DiagonalKernel Weight Types (WeightProvenance — D-08 fix)

Three construction paths, NOT interchangeable:

| Constructor | What it produces | Normalization | Use |
|---|---|---|---|
| `from_sigma()` | Sigma-derived weights | Normalized [0,1] | Scoring display, KernelSelector input |
| `from_learned()` | Discriminative precision weights (DK estimator output) | NOT normalized, can exceed 1.0 | Phase 2 deployed scorer |
| `from_effective()` | Shrinkage-blended: α·w_DK + (1-α) | Blended | Phase 2 active scoring |

**Also:** `raw_weights` is a PROPERTY on any DiagonalKernel returning true 1/σ² (inverse variance). NOT a construction path — available regardless of how the kernel was built. Used for η_eff computation.

**Code rule:** `compute_distance()` uses stored (raw) weights. `compute_gradient()` uses NORMALIZED weights (W/W.max()). This is the GAE-GRADIENT-001 fix (v0.7.7). Any code normalizing all weights at construction is wrong.

### 1.6 KernelSelector Architecture (v6.0 settled)

- Rule-based PRIMARY: noise_ratio > 1.5 → DiagonalKernel, else L2
- Data-driven is MONITORING ONLY (tested, found unreliable — mean_conf would never select DK even at +7.67pp advantage)
- This is a standing rule §3 Rule 6

---

## Part 2 — Architecture Map

### 2.1 Three-Layer Stack

```
Layer 1: GAE (graph-attention-engine-v50)
  Pure math. Apache 2.0. 1,183 tests. numpy-only.
  ProfileScorer, DiagonalKernel, KernelSelector, CalibrationProfile,
  LearningState, EvidenceLedger, ReferralEngine, ConservationStateMachine
  Framework v4: TwoPhaseStrategy, CoordinateDescentEstimator,
  BatchCompositionPolicy, PromotionGate, NoveltyTracker

Layer 2: ci-platform
  Shared infrastructure. Apache 2.0. 174 tests.
  AGEClient (graph), DomainConfig protocol, entity resolution,
  connectors, audit chain (EvidenceLedger/LedgerEntry)
  Framework layer is byte-identical across SOC/S2P/SDK

Layer 3: Copilots (proprietary)
  SOC (gen-ai-roi-demo-v4-v50): 1,003 backend + 254 E2E tests
  S2P (s2p-copilot): 132 tests
  copilot-sdk: 18 tests
```

### 2.2 Five Compounding Pathways (Why the Code Does What It Does)

| Pathway | What Compounds | Key Files | Status |
|---|---|---|---|
| 1. Centroid Learning | ProfileScorer.update() moves μ toward verified decisions | profile_scorer.py, calibration.py | LIVE |
| 2. W2 Flywheel | TRIGGERED_EVOLUTION edges → PatternHistoryFactorComputer score factor | factors.py, graph_schema.py | LIVE (D-02 fixed READ path — WRITE path always worked) |
| 3. Graph Enrichment | External enrichment creates new edges changing scoring context | enrichment/, connectors/ | LIVE |
| 4. Re-Convergence | Recovery faster each time (γ>1) | convergence.py | LIVE (conditional) |
| 5. DK Calibration | Distance metric weights improve as σ estimates sharpen | kernels.py, dk_estimator.py | Phase 2, v6.5 |

### 2.3 SOC Backend Data Flow

```
Alert arrives
  → factors.py: 6 factor computers query AGE graph → float[6] in [0,1]
  → ProfileScorer.score(f, category_index) → action probabilities
  → ReferralEngine R1-R7 VETO check
  → routing zone logic (auto-approve / agent zone / human review)
  → analyst confirms/overrides
  → guarded_update() [checks conservation, spike, freeze, LEARNING_ENABLED]
    → ProfileScorer.update() [η_confirm=0.05 or η_override=0.01]
    → conservation law check
    → TRIGGERED_EVOLUTION edge written (W2 flywheel)
    → centroid snapshot
```

### 2.4 Tensor Shapes

| Repo | Shape | Values | Note |
|---|---|---|---|
| SOC | (6,4,6) = 144 centroids | +144 DK weights = 288 total | A=4: escalate, investigate, suppress, monitor |
| S2P | (5,5,7) = 175 centroids | Different A count is intentional | S2P has A=5 (intentional asymmetry) |

### 2.5 Key Constants

| Constant | Value | Location | Note |
|---|---|---|---|
| η_confirm | 0.05 | CalibrationProfile | Learning rate for confirmations |
| η_override | 0.01 | CalibrationProfile | 5× attenuation from noise |
| τ (temperature) | 0.1 | CalibrationProfile | Softmax sharpness |
| κ* (IKS threshold) | 0.20 | calibration.py | Institutional Knowledge Score |
| θ accuracy target | 0.85 | conservation law | Deployment threshold |
| penalty_ratio (SOC) | 20:1 | SOC CalibrationProfile | Miss vs false positive |
| penalty_ratio (S2P) | 5:1 | S2P CalibrationProfile | More conservative |
| q window | 400 decisions | LearningHealthMonitor | Rolling accuracy window |
| ε_firm★ | ≈0.125 | convergence.py | Re-convergence boundary |
| LEARNING_ENABLED | False | soc/config.py | **Deliberate demo config** — see note below |

**LEARNING_ENABLED = False — why this is deliberate:** The demo runs on a fixed centroid tensor calibrated against the seed scenarios. Enabling learning during the demo would cause centroids to drift from calibrated positions, making the demo narrative unpredictable. This flag exists precisely for the demo→pilot transition: flip to True + re-bootstrap from customer data. It is NOT a bug or oversight.

---

## Part 3 — God Node Analysis (From Graphify)

### 3.1 Production God Nodes

| Node | Edges | Betweenness | What It Is |
|---|---|---|---|
| ProfileScorer | 312 | 0.134 | Core scorer — bridges 13+ communities |
| SOCDomainConfig | ~80 | 0.176 | **Highest betweenness** — bridges 7 communities including graph schema, bootstrap, W2, override |
| DiagonalKernel | 183 | 0.116 | Precision weight engine |
| KernelSelector | 117 | — | Kernel routing |
| L2Kernel | 112 | — | Default kernel |
| AGEClient | ~80 | — | Cross-repo graph client (ci-platform) |

**Key insight:** SOCDomainConfig has HIGHER betweenness centrality than ProfileScorer in the merged platform graph. It's the real architectural chokepoint — config changes cascade to graph schema, bootstrap, W2 factors, override detection, and conservation simultaneously. Changes here are high-risk.

### 3.2 Test/Experiment Infrastructure (NOT architectural concerns)

These appear in god node list but are test fixtures:
- `true_action()` (133 edges) — experiment helper
- `get_base_centroids()` (121 edges) — synthetic data builder
- `make_scorer()` (117 edges) — test factory
- `noise_realistic()` (116 edges) — noise generation fixture
- `build_gt()` (109 edges) — ground truth builder

### 3.3 Community Structure — Architecturally Significant

| Community | Size | What it maps to |
|---|---|---|
| 0 | 615 | Experiment/ablation cluster (cross-graph-experiments) |
| 2 | 470 | SOC backend application layer — startup, DomainConfig, routing |
| 8 | 122 | Conservation law math — compute_theta_min, derive_theta_min |
| 13 | 112 | **Framework v4 batch pipeline — isolated from live SOC path** |
| 17 | 81 | AGEClient — shared graph client (ci-platform) |
| 19 | 97 | graph_schema.py — graph contract, _S(), seed_graph |
| 20 | 105 | Shrinkage layer — FixedAlpha, LinearRampAlpha, TwoPhaseStrategy |
| 25 | 89 | W2 flywheel — PatternHistoryFactorComputer + integration tests |
| 40 | 36 | ConservationStateMachine — correctly isolated (D-04 fix) |
| 59 | 13 | AGE Cypher compatibility tests — standing rules have test coverage |
| 70 | 19 | Cross-repo contract tests — GAE → SOC interface |

**Framework v4 (Community 13) being isolated from Community 2 (live SOC)** confirms the design: PromotionGate, BatchHistory, BatchCompositionPolicy are built but not yet wired into the live decision path. The wire gap is structural, not accidental.

---

## Part 4 — Design Issues (D-01 through D-08)

### Current Status

| ID | Issue | Status | Impact |
|---|---|---|---|
| D-01 | ThreatIntel + DeviceTrust polarity inversions | ⏸ Deferred v1.1 | Returns LOW for HIGH threat. System works because centroids tuned WITH the inversion. Safe but confusing. |
| D-02 | W2 flywheel: factor_snapshot JSON parse fail | ✅ FIXED | Was blocking core product innovation (Pathway 2). Fix: parse JSON string before indexing. |
| D-03 | PromotionGate hardcodes conservation_pass=True | ⏸ Deferred v1.1 | Safe because auto_pause catches at scoring layer. Framework v4 not in production yet. |
| D-04 | OLSMonitor CUSUM never reset after alarm | ✅ FIXED | ConservationStateMachine with transition handlers. 27 tests. |
| D-05 | Stale scorer reference across await in mid-triage reset | ✅ CONFIRMED FIXED | Split accessor implemented: get_profile_scorer() L238, acquire_scorer() L43, acquire_scorer_for_reset() L57 in gae_state.py. CA-P1-05 resolved. |
| D-06 | Unmapped alert types silently route to credential_access | 📋 Queued | v1.0: log + evidence room. v1.1: "unclassified" category. |
| D-07 | seed_graph clean deletes runtime nodes | ✅ FIXED | Origin guard added. Only deletes zero_day_synthetic/zero_day_demo. |
| D-08 | DK weight normalization inconsistency (sigma vs direct path) | ✅ FIXED | WeightProvenance enum + named constructors. 13 tests. |

### D-01 Detail — Polarity Inversion (High Priority for v1.1)
ThreatIntel and DeviceTrust factor computers return values INVERSE to their semantic meaning:
- High threat → LOW score (should be HIGH)
- High device trust → LOW score (should be HIGH)

Centroids were bootstrapped WITH these inversions, so the scoring is internally consistent. However:
1. Any new deployment must replicate the inversions exactly
2. Factor explainability output is semantically wrong ("high threat = low risk")
3. Any partial fix risks breaking the centroid geometry

**v1.1 fix path:** Correct factor computers + regenerate centroids with correct polarity. Cannot be done in-place.

---

## Part 5 — Open Bugs (From REVIEW.md — 8-File SOC Backend Review)

### 5.4 Roadmap-Aligned Priority Table (From Roadmap Session Review)

| Priority | Bug | Effort | Rationale |
|---|---|---|---|
| **Fix first (P0)** | P1-03 (4× $param in learning_health.py) | 1 hour | Conservation monitoring silently returning fallback data on AGE — same pattern as D-02. Infrastructure exists, read path broken. |
| **Fix second (P0)** | P1-07 (audit fail-open → fail-safe) | 5 min | Compliance risk. Wrong default — UNAVAILABLE should not appear as VERIFIED. |
| **Before enabling learning (P1)** | P1-01 + P1-02 ($param in auto-approve + missing decision) | 30 min each | Behind LEARNING_ENABLED gate currently. Fix before flipping for pilot. |
| **Part of D-05 (P1)** | P1-05 (reset re-attach) | — | Resolved by acquire_scorer_for_reset() when D-05 fully ships. |
| **Quick add (P1)** | P1-06 (shape validation) | 5 min | 2-line assertion. |
| **Reclassified P3** | ~~P1-08~~ (noise_ratio) | — | Code is correct; documentation is wrong. Doc fix only. |
| **Defer (production gate)** | P1-09 (seed_graph partial) | 1 hour | Production concern. Not blocking demo or pilot. |

#### BUG-P1-01: AGE $param in composite auto-approve (triage.py:380-383)
```python
# VIOLATES §3 Rule — $param not supported in AGE
MATCH (d:Decision {decision_id: $id}) SET d.auto_approved = true
```
**Impact:** Auto-approved decisions silently fail to set `d.auto_approved = true` on AGE backend. They appear approved in memory but the graph record is wrong. Wrapped in non-blocking try so no error surfaces.  
**Fix:** Replace `$id` with `_S(decision_id)` inline interpolation.  
**File:** `backend/app/routers/triage.py` ~L380

#### BUG-P1-02: report_decision_outcome() returns success for missing Decision (triage.py:912-927)
**Impact:** If decision_id doesn't exist in graph, code prints "node not found" but still emits outcome events, updates in-memory trust/feedback, and calls process_outcome(). In-memory state diverges from graph.  
**Fix:** Check row count from the SET query; return 404 if no rows matched.  
**File:** `backend/app/routers/triage.py` ~L912

#### BUG-P1-03: learning_health.py — multiple $param violations (4 functions) — AGE migration gap
Functions using `$param` instead of `_S()`:
- `compute_volume_baseline()` — `$cutoff_epoch` (L344-350)
- `compute_category_baseline()` — `$cutoff_epoch` (L446-452)
- `compute_analyst_precision()` — `$min_decisions` (L544-554)
- `compute_verification_health()` — `$last_start`, `$now`, `$prior_start` (L628-653)

**Root cause:** These monitoring queries were written when Neo4j Aura was the primary client — `$param` is valid Neo4j syntax. When the platform migrated to AGE for cost/scalability, the core decision path was updated but these 4 monitoring functions were missed.

**Impact:** All conservation monitoring queries fail silently on AGE. Volume spike detection, category freeze detection, analyst precision weighting, and verification health are all potentially returning fallback values rather than real data.

**Fix:** Mechanical — replace each `$param` with an inline `_S()` literal. `_count_red_days()` in the same file already does this correctly and is the reference pattern.  
**File:** `backend/app/services/learning_health.py`

#### BUG-P1-04: compute_volume_baseline() synthetic fallback (learning_health.py:344-375)
**Impact:** Query failure returns zero mean/std, std is then floored to 1.0, producing a spike threshold of 5.0 or 3.0. A broken graph query makes spike detection compare against a synthetic low baseline — could trigger false spikes or miss real ones.  
**Fix:** Distinguish "no data" from "query failed"; return UNKNOWN status on failure.

#### BUG-P1-05: reset_learning_state() missing ProfileScorer re-attach (gae_state.py:277-285)
**Impact:** After hard reset, `_learning_state` is replaced with fresh state but ProfileScorer is NOT attached to it. Subsequent calls to `get_profile_scorer()` return None. Any analyze or profile endpoint called after a hard reset silently gets 503 until the server restarts.  
**Fix:** Call `attach_profile_scorer()` at the end of `reset_learning_state()`, or re-run the init flow.  
**File:** `backend/app/services/gae_state.py` ~L277

#### BUG-P1-06: restore_centroid_from_backup() no shape validation (gae_state.py:603-621)
**Impact:** Valid backup with incompatible tensor shape (e.g., from an old config) is assigned directly to `scorer.centroids` without shape check. Can corrupt live scorer state.  
**Fix:** Validate `mu_array.shape == scorer.centroids.shape` before assigning.  
**File:** `backend/app/services/gae_state.py` ~L603

#### BUG-P1-07: audit failure returns verified=True (evidence_room.py:118-124)
**Impact:** When audit collection fails, `_empty_hash_chain()` returns `verified=True, status="VERIFIED"`. An unavailable audit chain appears verified in the evidence room. This is a compliance/regulatory risk (EU AI Act Article 12 — logging).  
**Fix:** Return `verified=False, status="UNAVAILABLE"` on exception.  
**File:** `backend/app/services/evidence_room.py` ~L118

#### ~~BUG-P1-08~~: DiagonalKernel noise_ratio — RECLASSIFIED TO P3 (documentation fix)
**Original claim:** noise_ratio formula `sqrt(_W_baseline_max / weights_min)` was wrong; docs say `sqrt(1 / weights_min)`.  
**Correction:** In the sigma construction path (the only production path), `_W_baseline_max` is the max of raw inverse-variance weights, and stored weights are normalized by that max. So `weights_min` is already relative to `_W_baseline_max`. The formula `sqrt(_W_baseline_max / weights_min)` correctly computes σ_max/σ_min — the ratio of noisiest to least noisy factor variance. This IS what noise_ratio should be.  
**The documentation is wrong, not the code.** Fix: update docstring to match the formula actually implemented.  
**File:** `gae/kernels.py` — docstring only

#### BUG-P1-09: seed_graph partial failure leaves corrupted graph (graph_schema.py)
**Impact:** With `clean=True`, if edge or Decision creation fails partway through, the function logs/counts the error but continues and returns the verification report. A partially seeded graph remains live. No rollback.  
**Fix:** Collect all seed errors; if any critical failures occur after the clean phase, roll back or halt with explicit error.  
**File:** `backend/app/graph_schema.py`

### 5.2 Key P2 Bugs — Several Upgraded in Priority

#### BUG-P2-01: Analyst identity always "anonymous" — PREREQUISITE FOR R-01
`request.state.user` raises AttributeError on normal FastAPI requests. `analyst_id` always falls back to "anonymous". Per-analyst η weighting path is unreachable.  
**Why this matters more than P2:** Even after R-01 (multi-analyst η) ships, every analyst will get the same learning rate unless this is fixed first. This is a prerequisite, not just a robustness issue.  
**Fix:** Auth middleware (SAML is shipped) must set `request.state.user`. Wire SAML user identity into `OutcomeRequest` processing.

#### BUG-P2-02: UNKNOWN conservation status treated as healthy — SHOULD BE FAIL-SAFE
`compute_verification_health()` defaults conservation to UNKNOWN on failure, and UNKNOWN is treated as passing the conservation check. A broken conservation monitor improves the health rollup.  
**Correct behavior:** UNKNOWN → AMBER (cautious), not GREEN (healthy). Architecturally consistent with the conservation law's purpose: when uncertain, be conservative.  
**Fix:** Change UNKNOWN → AMBER in the health rollup logic.

#### BUG-P2-03: Frozen categories don't clear on spike clear — SILENT LEARNING HALT
`set_volume_spike(False)` does not clear `_frozen_categories`. After a spike clears, previously frozen categories remain blocked indefinitely until manual intervention.  
**Fix:** 2 lines — add `_frozen_categories.clear()` to `set_volume_spike(False)`.

#### BUG-P2-04: factor_vector missing skips save_learning_state
If Decision has no parseable factor_vector, `decision_count` increments but state is not persisted. After restart, count diverges.

#### BUG-P2-05: execute_action() creates empty factor_vector Decisions
Legacy path creates Decisions with empty factor_vector. Both paths are user-facing. Inconsistent records affect W2 flywheel reads and analytics.

#### BUG-P2-06: learning_health.py query aliases (total/verified instead of cnt)
`compute_verification_health()` uses aliases `total` and `verified` — AGE requires `cnt` convention. AGE compatibility uncertain.

#### BUG-P2-07: gae_state.py broadly unlocked mutable state
Multiple module-level collections read/written without explicit locking outside `guarded_update()`. Concurrent requests can produce mixed reads.

#### BUG-P1-SOC-01 through P1-SOC-04: soc.py $param violations — same migration gap as learning_health.py

Four additional `$param` violations in soc.py, all using the same pattern (second `dict` argument to `run_query()`):

- **`get_analyst_benchmarking()`** — 4 queries all use `{"source": SOURCE}`. Entire F9 analyst benchmarking report fails on AGE, returns "accumulating" status or synthetic fallback. **Most impactful.**
- **`explain_decision()`** — 3 queries use `{"decision_id": ...}`, `{"category": ...}`. Explain endpoint may return 500 on AGE.
- **`get_detection_engineering()`** noise map — `{"cat": cat}`. Noise map fp_rate returns None for all categories.
- **`_tab3_content()`** override_rate query — `{"cat": rec_category}`. Tab 3 override rate always shows hardcoded default 15.0%.

**Fix:** Replace all `$param` with inline `_S()` literals. Same pattern as `_count_red_days()` in learning_health.py.  
**File:** `backend/app/routers/soc.py`

- **D-01**: Factor polarity inversions (ThreatIntel, DeviceTrust) — consistent but semantically inverted
- **D-03**: PromotionGate `conservation_pass=True` hardcode — safe at current deployment stage
- **D-06**: Unmapped alert types → credential_access — logged, v1.1 fix planned

---

## Part 6 — Standing Rules Verification

### §3 Rules — Compliance Status

| Rule | Description | Status |
|---|---|---|
| ε_firm★ = 0.125 | Not 0.387 or 0.128 | ✅ Verified in convergence.py |
| θ_min = formula | Not a constant | ⚠️ compute_theta_min() appears in BOTH gae/calibration.py AND soc/config.py — possible duplicate |
| q = 400-decision rolling | Not lifetime average | ✅ LearningHealthMonitor uses 400-window |
| A=4 canonical | No A=5 in scorer | ✅ SCORER_ACTIONS=4, refer_to_analyst is routing only |
| η_override=0.01 | Not arbitrary | ✅ Confirmed in CalibrationProfile |
| KernelSelector rule-based PRIMARY | Data-driven = monitor | ✅ Confirmed in kernel_selector.py |
| Re-convergence conditional | Category-sparse + warm-start + ε_firm>0.125 | ✅ Confirmed in synthetic.py tests |
| b=2.11 sim-only | EXP-G1 for production | ✅ Not in production path |
| Oracle separation only | META-4 retired | ✅ Confirmed |
| α = among verified | Not all decisions | ✅ LearningHealthMonitor._extract_components |
| WeightProvenance 3 types | Named constructors | ✅ D-08 fix implemented |
| Conservation = state machine | Components register handlers | ✅ D-04 fix implemented |

### ⚠️ Unverified: compute_theta_min() duplication

`compute_theta_min()` appears in:
1. `gae/calibration.py` — the canonical GAE location
2. `backend/app/domains/soc/config.py:L782` — unexpected

The graphify path query found no direct edge between the two. **CODE INSPECTION REQUIRED** (see §8).

---

## Part 7 — Architecture Quality Findings

### 7.1 What's Well Designed

**Zero circular dependencies** across 693 files — verified by code_graph_review.py  
**Framework layer byte-identical** across SOC/S2P/SDK (agent.py=374, event_bus.py=119, shadow_mode.py=118)  
**ConservationStateMachine correctly isolated** (Community 40 in graphify) — D-04 fix is clean  
**WeightProvenance correctly isolated** (Community 9 in GAE graph) — D-08 fix is clean  
**W2 flywheel integration tests have their own community** (Community 25) — D-02 fix has test coverage  
**AGE Cypher compatibility rules have dedicated test community** (Community 59) — standing rules enforced  
**Cross-repo contract tests are a proper community** (Community 70) — GAE→SOC interface tested  

### 7.2 Architecture Debt Findings

**1. triage.py is 1,887 lines mixing 12+ concerns**  
`analyze_alert()` alone is 527 lines mixing: scoring, Decision persistence, audit writes, eventing, referral, composite gate, provenance, campaign correlation, Sentinel write-back, graph visualization, narrative assembly. This is the highest-risk file for regressions.

**2. Re-export stub pattern (app/services/ → app/framework/)**  
11 modules in `backend/app/services/` are now re-export stubs pointing to `app/framework/`. The stubs are isolated communities in graphify (no visible callers). Any code still importing from the old paths gets the stub.  
Confirmed stubs: `shadow_mode.py`, `provenance.py`, `ols_status.py` (and 8 others).

**3. SOC backend has a legacy domain config stub**  
`backend/app/domains/supply_chain/config.py` is described as "Smoke-test stub" — the real S2P config is in `s2p-copilot/`. This creates two config paths that could diverge.

**4. Framework v4 is fully built but disconnected from live SOC path**  
Community 13 (PromotionGate/BatchHistory/BatchCompositionPolicy) is structurally isolated from Community 2 (live SOC). The wire from `report_decision_outcome()` to the batch pipeline does not exist yet. This is correct for v6.0 but the connection point must be explicit.

**5. SOC has 291 communities vs GAE's 76**  
High community count relative to size indicates fragmentation — consistent with the mixing of concerns in soc.py (4,001 lines) and triage.py. SOC backend's internal structure is more tangled than GAE's.

**6. ReasoningNarrator uses lazy-import Vertex AI**  
Community 107 reveals a Vertex AI dependency in the SOC backend (`backend/app/` somewhere). Not documented in session instructions. Lazy import means it won't fail at startup but will fail at first use if credentials are absent.

### 7.3 SOC Frontend Hotspot

**RuntimeEvolutionTab.tsx** (3,570 lines, 74 useState calls) — not reviewed yet. The graphify graph shows `fetchJSON()` as a god node (84 edges) in the frontend community (Community 4, 158 nodes). This tab drives Tab 2 of the demo and is the conservation law display.

---

## Part 8 — Code Inspection Requests

These are specific things needed to complete the picture. Priority order per roadmap session:

### 8.3 ✅ CLOSED — CalibrationProfile learning_rate vs η_confirm

**Finding:** `learning_rate` and `eta_confirm` are completely separate parameters serving different roles.
- `CalibrationProfile.learning_rate = 0.02` → consumed in `gae/learning.py` as `alpha_effective` — the α component in the conservation law signal (α·q·V ≥ θ_min). This is the human verification fraction proxy.
- `_ETA_CONFIRM = 0.05` → module constant in `gae/calibration.py`, used directly in bootstrap centroid updates. This is the centroid learning rate η_confirm.

**No discrepancy.** Naming was misleading but values are correct and serve different roles. All convergence timelines (~14 decisions per cell) are unaffected.

### 8.2 ✅ CLOSED — LEARNING_ENABLED gate completeness

**Finding:** `LEARNING_ENABLED` is checked in exactly **two places**:
- `backend/app/routers/triage.py:1056` — live outcome path
- `backend/app/services/simulation.py:418` — simulation path

Both use the identical pattern: `if LEARNING_ENABLED and action_name in SCORER_ACTIONS`.

**Test coverage:** `tests/test_learning_toggle.py` has 4 tests: False→centroids unchanged, True→centroids change, update called when True, score identical regardless of flag.

**Pilot action:** Single line change in `soc/config.py`. No hidden gates. Re-bootstrap from customer data required before flipping.

### 8.1 ✅ CLOSED — θ_min duplication confirmed, action item logged

**Finding:** `backend/app/domains/soc/config.py:L782` has its own `compute_theta_min(alpha, V)` implementing `23.53 / (alpha * V)` directly. The comment at L789 explicitly acknowledges `gae.calibration.derive_theta_min()` exists.

**Current state:** Formula is identical — no correctness risk today. However this is a maintenance liability. If the θ_min derivation ever changes in GAE (it already changed once, v12), the local copy won't update.

**Action item (v1.1):** Remove `soc/config.py:compute_theta_min()`. Replace all callers with `from gae.calibration import derive_theta_min` (or `compute_theta_min`). Single source of truth must be in GAE.

### 8.4 ✅ CLOSED — D-02 fix correctly implemented

**Finding:** Fix is clean and well-structured.
- Dedicated helper `_extract_pattern_history_from_factor_snapshot()` handles `json.loads()` before indexing — root cause of D-02 was indexing raw AGE string directly
- `PatternHistoryFactorComputer` has two explicitly documented paths: Path A (W2 via TRIGGERED_EVOLUTION) and Path B (fallback)
- L516 comment: "Parse full JSON snapshot, then isolate factor_snapshot[3] (pattern_history)"
- Cypher uses inline epoch values, correct AGE compliance throughout

W2 flywheel read path fully operational.

### 8.5 ✅ CLOSED — D-07 fix correctly and thoroughly implemented

**Finding:** Origin guard is comprehensive and correct.
- Backbone labels (User, Asset, Campaign, ThreatIndicator, AttackPattern): deleted only where `origin IS NULL OR origin = zero_day_synthetic OR origin = zero_day_demo`
- Decision/Alert: deleted only for `_DATA_ORIGINS` list — session decisions (`origin=NULL`) explicitly survive, documented in L199 and L472 comments
- Post-clean verification at L504 checks no origin-less backbone nodes survived
- All seed writes use `_S(SYNTHETIC_ORIGIN)` or `_S(DEMO_ORIGIN)` — no raw string interpolation
- REVIEW.md P1 finding about backbone labels being deleted without origin filter was from before the fix. Current code is correct.

### 8.6 ✅ CLOSED — Re-export stubs are active compatibility layer, not dead code

**Finding:** All 6 stub modules (audit, shadow_mode, checkpoint, ols_status, provenance, economics) are actively imported by production code: `framework_router.py`, `triage.py`, `soc.py`, `simulation.py`, and tests. All are lazy imports inside functions. Stubs re-export from `app.framework.*` correctly. No action needed — deliberate backward-compatibility layer from the framework refactoring.

### 8.7 PENDING — Vertex AI dependency location

```powershell
Get-ChildItem -Path "gen-ai-roi-demo-v4-v50\backend" -Filter "*.py" -Recurse | Select-String -Pattern "vertexai|VertexAI|vertex_ai|ReasoningNarrator"
```

### 8.8 PENDING — S2P legacy config in SOC backend

```powershell
Get-Content "gen-ai-roi-demo-v4-v50\backend\app\domains\supply_chain\config.py" | Select-Object -First 50
```

---

## Part 9 — Roadmap Implications

### 9.1 Master Action Table (Roadmap Session Priority)

| Priority | Action | Effort | Notes |
|---|---|---|---|
| **P1 — pilot blocker** | Fix datetime() in compute_volume_baseline() + HAVING in compute_analyst_precision() | 1 hour | **Both confirmed P1 for pilot.** datetime() failure → spike_threshold=5.0 → permanent category freeze → all learning halted from Day 1 with LEARNING_ENABLED=True. HAVING → analyst precision weighting broken. |
| **P0** | Fix BUG-P1-07 (audit fail-open → fail-safe) | 5 min | UNAVAILABLE must not appear as VERIFIED. |
| **P1 structural** | Add drift detection test: app/framework/ vs copilot_sdk/framework/ | 30 min | audit.py 5KB intentional extension (SOC canonical). shadow_mode.py 18 bytes drifted. Fix direction: backport SOC→SDK. |
| **P1** | Fix BUG-P2-02 (UNKNOWN → AMBER not GREEN) | 15 min | Conservation fail-safe, not fail-open. |
| **P1** | Fix BUG-P2-03 (frozen categories clear on spike clear) | 5 min | 2 lines in set_volume_spike(False). |
| **P1** | Fix BUG-P1-06 (shape validation) | 5 min | 2-line assertion in restore_centroid_from_backup(). |
| **Before pilot** | Fix BUG-P1-01 + P1-02 ($param auto-approve + missing decision) | 1 hour | Behind LEARNING_ENABLED gate now. Fix before flipping. |
| **Prerequisite for R-01** | Fix BUG-P2-01 (analyst identity always anonymous) | Medium | SAML wire-up. Without this, per-analyst η never works. |
| **v1.1 target** | SOCDomainConfig → refactor to S2PDomainConfigV2 pattern | Large | Betweenness 0.176 — highest-risk config in platform. |
| **v1.1 target** | triage.py decomposition | Large | 1,887 lines, 12+ concerns. High regression risk. |
| **v1.1 fix** | Remove soc/config.py:compute_theta_min() | Small | Replace with gae.calibration import. Maintenance liability. |
| **v1.1 fix** | D-01 (factor polarity inversions) | Medium | Requires centroid regeneration + coordinated deploy. |
| **v1.1 fix** | D-03 (PromotionGate conservation_pass) | Small | Wire actual conservation check. |
| **v6.5** | Wire BatchPipeline to report_decision_outcome() | Medium | Pathway 5 (DK Calibration) activation. |
| **v6.5** | Phase 1 freeze per (c,a) at PhasePolicy trigger | Medium | Correct two-phase behavior. |
| **v6.5** | Raise discovery Algorithm 4 distance_gap threshold | Small | Current threshold=0.0 is too broad — will be noisy in production. |
| **v6.5** | Update Algorithm 2 confidence filter for DK calibration | Small | >0.70 filter will over-exclude when DK deploys (ECE up to 0.42). |
| **Track** | Reclassify P1-08 as P3 | — | Docstring fix in gae/kernels.py only. |
| **✅ CLOSED** | D-05 status confirmed | — | acquire_scorer() L43, acquire_scorer_for_reset() L57 confirmed in gae_state.py. |

### 9.2 Pilot Checklist (Before Enabling LEARNING_ENABLED=True)

1. Fix datetime() in compute_volume_baseline() + HAVING in compute_analyst_precision() — confirmed broken on AGE
2. Fix BUG-P1-01 ($param in auto-approve) — Decision graph records must be correct
3. Fix BUG-P1-02 (missing decision returns success) — feedback integrity
4. Fix BUG-P2-03 (frozen categories don't clear) — silent learning halt risk
5. ~~Verify §8.3~~ CLOSED — learning_rate=0.02 is α for conservation law, not η_confirm. No issue.
6. Re-bootstrap from customer data (new μ₀ from customer alert distribution)
7. Fix BUG-P2-01 (analyst identity) — if per-analyst η is desired for pilot

### 9.3 Open Analysis Gaps

**cross_graph_discovery.py** ✅ REVIEWED — see Part 11 below.

**Cross-repo contract testing coverage:** Community 70 exists. §8.3 confirmed learning_rate and η_confirm are separate — no contract violation. Still worth verifying whether any test explicitly covers the CalibrationProfile→ProfileScorer η_confirm handoff.

**S2P tensor migration completeness:** S2PDomainConfigV2 (5,5,7) is the current config, but it's not verified that ALL S2P code paths use V2 and not the legacy (6,4,6) stub. Comprehensive queue notes ~70 S2P tests needed migration.

**factors.py (all 6 factor computers, ~900 lines)** ✅ REVIEWED — see Part 12 below.

**RuntimeEvolutionTab.tsx (3,570 lines, 74 useState):** Not reviewed. Frontend god node `fetchJSON()` (84 edges) lives here. Tab 2 drives the conservation law display. High regression risk for any conservation UI changes.

**soc.py (4,001 lines)** ✅ REVIEWED — see Part 13 below.

---

## Part 11 — Cross-Graph Discovery Analysis (FEATURE-07)

**File:** `backend/app/services/cross_graph_discovery.py` — 940 lines  
**Status:** Shipped. Read-only. AGE-compatible.

### Architecture

Four algorithms, one module, one singleton `discovery_service`. Algorithms 1-3 hit the graph; Algorithm 4 runs pure numpy on Algorithm 2's output — no additional queries. Cache TTL=60 seconds. Per-algorithm 3-second timeout. Stale fallback if all 4 fail. Graph clock uses `max(Alert.timestamp_epoch)` — correct for seeded demo where timestamps are synthetic.

Total graph queries per refresh: ≤4 (Algo 1) + 1 (Algo 2) + 4 (Algo 3) = **9 worst case**.

### Algorithm 1 — Shared Entity (≤4 queries)

Finds Users/Assets in alerts spanning ≥2 categories with ≥3 alerts. Two aggregate queries, then two batch TI queries only if qualifying entities exist. Pre-filters in Python before fetching TI — this is the 102→4 query optimization.

**Score formula:** `0.20×(alerts/20) + 0.30×(categories/6) + 0.20×temporal_density + 0.30×TI_present`

**AGE compliance:** Clean. Inline epoch values, `count(a) AS cnt`, `collect()` results handled by `_parse_collected()` which correctly handles AGE JSON string output.

**P2:** `_aligned_alert_rows()` uses `zip(alert_ids, categories, timestamps)` from three separate `collect()` results. If AGE returns differently-sized arrays under partial serialization failure, zip silently truncates. Low risk but worth a length assertion.

### Algorithm 2 — Pattern Convergence (1 query + numpy)

Finds decision pairs from different categories sharing the same recommended action despite divergent factor geometry. Filters on `d.confidence > 0.70`. Only highest-scoring pair per action group emitted.

**Implementation:** Numpy broadcasting for pairwise L2 — `(G,G,6)` diff tensor, then `sqrt(sum(diff²))`. O(G²) numpy not O(G²) Python. CONVERGENCE_LIMIT=200 caps at 19,900 pairs worst case.

**Score:** `min(dist, 1.0) × confidence` — high score means "I'm confident about both assignments but geometrically they look the same." Correct signal.

**Design note for v6.5:** `d.confidence > 0.70` filter is correct under L2 (ECE 0.04-0.06) but will over-exclude when DiagonalKernel deploys (ECE up to 0.42 at high NR). Flag for v6.5 review.

**Returns** `parsed_decisions` as second output — feeds Algorithm 4. Only inter-algorithm dependency.

### Algorithm 3 — Temporal Velocity (4 queries)

Finds Users/Assets with alert volume spike: recent 7 days vs normalized baseline 23 days. MIN_VELOCITY_RATIO=2.5.

**Score:** `ratio / 20.0`. 2.5× spike → 0.125 (LOW). 14× spike needed for HIGH (≥0.70). Very conservative — intentional for demo noise reduction, may under-alert in production.

**AGE compliance:** Clean. Inline epoch values, `count(a) AS cnt`.

### Algorithm 4 — Cross-Factor Anomaly (no queries, pure numpy)

Runs on Algorithm 2's `parsed_decisions`. Uses `SOC_PROFILE_CENTROIDS.mean(axis=1)` to get one (6,6) per-category mean matrix (averages over 4 action centroids).

Two sub-types:
- **MISROUTE:** Assigned category centroid is farther than another — `distance_gap > 0`
- **NOVEL:** All centroids far — `nearest_distance > ANOMALY_THRESHOLD=0.65`

**D-01 interaction — important:** ThreatIntel and DeviceTrust have inverted polarity (D-01). Algorithm 4 compares against action-averaged centroids calibrated WITH the inversions. Both factor vectors and centroids are in the same inverted space — Algorithm 4 behaves correctly despite D-01.

**Design concern:** `distance_gap > 0.0` threshold means ANY decision where another category is mathematically closer gets flagged as MISROUTE. With 200 decisions and 6 categories, this produces many LOW-severity discoveries. In production, raise the minimum `distance_gap` floor (suggest ≥0.10) to reduce noise.

**3-second timeout** checked per-row inside loop — correct for CPU-bound work.

### Summary Findings

| Issue | Severity | Algorithm |
|---|---|---|
| `zip()` silent truncation in `_aligned_alert_rows` | P2 | 1 |
| Confidence filter >0.70 will fail when DK deploys | Design note (v6.5) | 2 |
| Velocity score very conservative (14× for HIGH) | Design note | 3 |
| `distance_gap > 0.0` too broad — noisy in production | P3 (v6.5 floor) | 4 |
| Action-averaged centroids approximate true scoring geometry | Design note | 4 |

**No P1 bugs.** AGE compliance clean throughout. Architecture is sound.

### 9.4 EXP-G1 Dependencies (Need Production Data)

- b=2.11 (re-convergence rate) — simulation only
- ε_firm production range (estimated 0.15-0.40) — needs measurement
- Phase 1 η schedule and freeze point — per-domain calibration
- Optimal shrinkage α — FixedAlpha(0.5) is safe default

---

## Part 10 — Quick Reference for Q&A Sessions

### "Where does X live?"

| X | File | Location |
|---|---|---|
| Scoring equation | gae/profile_scorer.py | score() method |
| Centroid update | gae/profile_scorer.py | update() method |
| Conservation law math | gae/calibration.py | compute_theta_min(), check_conservation() |
| Conservation state machine | gae/convergence.py | ConservationStateMachine |
| Conservation monitoring | backend/app/services/learning_health.py | LearningHealthMonitor.evaluate() |
| DK weight types | gae/kernels.py | WeightProvenance + DiagonalKernel |
| Kernel selection | gae/kernel_selector.py | KernelSelector |
| W2 flywheel read | backend/app/domains/soc/factors.py | PatternHistoryFactorComputer |
| W2 flywheel write | backend/app/routers/triage.py | ~L1234 (TRIGGERED_EVOLUTION edge) |
| Scorer initialization | backend/app/services/gae_state.py | init_learning_state() |
| Scorer mutation gate | backend/app/services/gae_state.py | guarded_update() |
| Learning rate config | backend/app/services/gae_state.py | _soc_profile() [needs inspection] |
| SOC tensor + categories | backend/app/domains/soc/config.py | SOC_PROFILE_CENTROIDS, SOC_CATEGORIES |
| LEARNING_ENABLED flag | backend/app/domains/soc/config.py | L61 |
| Graph safety layer | backend/app/graph_schema.py | _S(), GRAPH_CONTRACT |
| AGE client | ci-platform/graph/age_client.py | AGEClient |
| Phase 2 batch pipeline | gae/batch_pipeline.py | PromotionGate, BatchHistory |
| IKS score | backend/app/services/ | compute_iks() |
| Evidence/audit | ci-platform/ | EvidenceLedger |

### "What's A=4 and why?"

The scorer has exactly 4 actions: escalate, investigate, suppress, monitor. `refer_to_analyst` is a ROUTING decision via ReferralEngine R1-R7, NOT a scorer action. It's a VETO that fires before scoring. Any code using A=5 in ProfileScorer is stale.

### "Why isn't the system learning?"

`LEARNING_ENABLED = False` in `soc/config.py` — deliberate demo configuration. The demo uses a fixed centroid tensor calibrated against seed scenarios; enabling learning would cause centroid drift, making the demo narrative unpredictable. For pilot: flip to True + re-bootstrap from customer data. Additionally `guarded_update()` blocks on: AMBER/RED conservation state, volume spike, frozen categories, and scorer not initialized. All four guards must pass even with LEARNING_ENABLED=True.

### "What is the IKS?"

Institutional Knowledge Score — measures how far current centroids have drifted from the bootstrap baseline μ₀. κ*=0.20 is the threshold above which the system has "substantial institutional knowledge." It's a directional signal, not a quality metric.

### "What's the difference between SOC's Neo4jClient and ci-platform's AGEClient?"

Two graph clients exist, both actively maintained:

- `Neo4jClient` (`backend/app/db/neo4j.py`) — Neo4j Aura cloud client. Original implementation. Kept as a working fallback in case the platform needs to return to Neo4j. Standard Cypher with `$param` named parameters works here.
- `AGEClient` (`ci-platform/graph/age_client.py`) — Apache AGE on PostgreSQL. **Current production client.** Switched to for cost/scalability reasons — Neo4j Aura cloud was not practical at scale. AGE has stricter Cypher compatibility requirements.

`GRAPH_BACKEND` env var controls which client is active. The switch is clean by design.

**Why learning_health.py has $param violations:** Those monitoring queries were written when Neo4j was primary — `$param` is valid Neo4j syntax. When the platform migrated to AGE, the core decision path (triage.py, graph_schema.py) was updated to use `_S()` inline interpolation, but the 4 monitoring functions in learning_health.py were missed. It's a migration gap, not a design oversight. The fix is mechanical: replace `$cutoff_epoch`, `$min_decisions`, `$last_start`, `$now`, `$prior_start` with inline `_S()` calls.

---

*Document version: v4.0 · May 3, 2026 · Living document*  
*Code is authoritative over docs where they conflict*

**Files reviewed:** age_client.py (ci-platform), test_cross_repo_contracts.py (SOC), test_discipline.py (copilot-sdk), domain_config.py, factor_computer.py, source_connector.py (copilot-sdk protocols), sdk __init__.py, sdk framework/agent.py  
**Status:** Fully reviewed. Major correction to P1 bug list. Core structural problem identified.

### CORRECTION: $param Bugs Reclassified from P1 to P2

AGEClient's `_sync_execute()` performs Python-level parameter substitution BEFORE building SQL:
```python
if parameters:
    for name in sorted(parameters, key=len, reverse=True):
        query = query.replace(f"${name}", AGEClient.serialize_for_age(parameters[name]))
```
When `neo4j_client.run_query(query, {"cat": cat})` is called with AGEClient active, the substitution works correctly. `$param` dicts ARE handled.

**BUG-P1-03 and BUG-P1-SOC-01 through SOC-04 reclassified to P2.** The `$param` pattern is not broken on AGE.

**Three real issues remain (P2):**
- `compute_volume_baseline()`: uses `datetime($cutoff_epoch)` — AGE-forbidden function (§3 Rule). Will fail regardless of parameter handling.
- `compute_volume_baseline()`: day-level bucketing in Cypher — needs Python-side computation.
- `compute_analyst_precision()`: uses `HAVING count(d) >= N` — **CONFIRMED BROKEN on AGE**. Hard syntax error: "syntax error at or near HAVING". Every analyst with any decisions gets included regardless of threshold. Fix: remove HAVING clause, filter in Python post-query.

### Actual Import Map — 6 Cross-Repo Wires

```
SOC backend ← ci_platform.graph.AGEClient
  app/graph_schema.py:218, 433 (lazy imports inside functions)
  app/db/neo4j.py:476-477 (conditional on GRAPH_BACKEND=age)

SOC backend ← ci_platform.audit.evidence_ledger
  app/framework/audit.py:24 (EvidenceLedger, LedgerEntry, OutcomeEntry)

SOC backend ← ci_platform.auth.saml
  app/routers/auth.py:11 (lazy import)

SOC backend ← gae (GAE library)
  via pip install, throughout gae_state.py and calibration

SOC backend ← copilot_sdk
  NOT IMPORTED. Migration planned but not done.
  app/framework/__init__.py comment: "Replace 'from app.framework' with 'from copilot_sdk'"

SOC backend ← app/framework/ (internal)
  11 re-export stubs in app/services/ → app/framework/ (confirmed earlier)
```

### The Core Structural Problem: Two Copies of the Framework

SOC backend's `app/framework/` is a **copy** of `copilot_sdk/framework/`, NOT an import from it. Maintained manually. File size comparison:

| File | app/framework/ | copilot_sdk/framework/ | Status |
|---|---|---|---|
| agent.py | 15,088 | 15,089 | 1 byte diff |
| economics.py | 3,932 | 3,932 | Identical |
| event_bus.py | 3,690 | 3,690 | Identical |
| shadow_mode.py | 3,992 | 3,974 | **18 bytes different** |
| audit.py | 15,488 | 10,378 | **5KB different** |

shadow_mode.py has already drifted. audit.py has diverged significantly (5KB). The "byte-identical" design doc claim is already false for at least two files. Any change to copilot-sdk/framework/ must be manually replicated to SOC/app/framework/ or divergence accumulates silently. No automated drift detection exists.

### Three-Layer Architecture (Corrected)

```
Layer 1: GAE (graph-attention-engine-v50) — pure math, pip-installable
  ProfileScorer, DiagonalKernel, KernelSelector, CalibrationProfile, etc.

Layer 2a: ci-platform — infrastructure
  AGEClient (graph), EvidenceLedger (audit), SAMLService (auth),
  connectors (Sentinel, Splunk), enrichment, entity_resolution,
  onboarding (centroid, deployment, pipeline), redaction (PII)

Layer 2b: copilot-sdk — framework + protocols
  PROTOCOLS: DomainConfig, FactorComputer, SourceConnector, ReferralRule
  FRAMEWORK: agent, audit, checkpoint, IKS, provenance, shadow_mode, etc.
  (Framework is a copy of SOC's app/framework/ — migration not yet done)

Layer 3: SOC backend (proprietary)
  app/framework/ — copy of copilot-sdk/framework/ (migration TODO)
  app/services/ — 11 re-export stubs → app/framework/
  app/domains/soc/ — SOC-specific config, factors, campaigns
```

### The SOCAgent — ~~IN THE LIVE TRIAGE PATH~~ DEAD CODE (MAP v5.65 Correction)

**Previous finding was wrong — code changed during May 3-5 sprint.** MAP v5.65 explicitly: "CA-SOCAGENT = dead code — Zero imports found. P3 cleanup, not P1."

The import chain documented below existed at analysis time but was removed during the May 3-5 sprint:
```
[STALE — no longer active after May 3-5 sprint]
copilot_sdk/framework/agent.py  → defines SOCAgent + agent singleton
app/framework/agent.py          → COPY of above
app/services/agent.py:7         → from app.framework.agent import *
app/routers/triage.py:12        → from app.services.agent import agent  ← REMOVED
app/routers/evolution.py:13     → from app.services.agent import agent  ← REMOVED
```

**Current state:** SOCAgent class still exists in both copies but is no longer imported by any production code. Safe to delete (P3 cleanup). No tests or production code will break on deletion.

### The Core Structural Problem: Two Copies of the Framework

SOC backend's `app/framework/` is a **copy** of `copilot_sdk/framework/`, NOT an import. Maintained manually. File size comparison:

| File | app/framework/ | copilot_sdk/framework/ | Status |
|---|---|---|---|
| agent.py | 15,088 | 15,089 | 1 byte diff |
| economics.py | 3,932 | 3,932 | Identical |
| event_bus.py | 3,690 | 3,690 | Identical |
| shadow_mode.py | 3,992 | 3,974 | **18 bytes different** |
| audit.py | 15,488 | 10,378 | **5KB — intentional extension** |

**audit.py: SOC is canonical (Q3 confirmed).** SOC added async safety, hash-chained OutcomeEntry, epoch archive, and restart resilience. SDK version is an earlier iteration that mutates entries directly (breaks hash chain integrity). Fix direction: backport SOC→SDK. SDK's `record_outcome()` is architecturally incorrect vs SOC's version.

### AGEClient Quality Assessment

The AGEClient is well-engineered for what it does:
- Per-query connections inside `asyncio.to_thread()` — correct for sync psycopg + async FastAPI
- `_check_safe_cypher()` enforces `SET n = {}` and MERGE prohibitions at query time
- `_extract_columns()` is bracket-aware for nested `collect({...})` returns
- Parameter substitution handles prefix collisions via sorted-by-length replacement
- MATCH-then-CREATE two-step pattern correctly replaces MERGE throughout
- Python-side datetime computation (timedelta) instead of Cypher `datetime()` — correct
- `count_verified_decisions()` documents the AGE vs Neo4j behavioral difference explicitly

**One gap:** `get_security_context()` and several convenience methods still use `$param` dict — these ARE handled by `_sync_execute()` substitution, but inconsistently with the inline `_S()` pattern used in the SOC backend directly. Two patterns for the same thing.

### Contract Test Coverage — Gaps

9 tests in test_cross_repo_contracts.py cover structural imports and field existence. Critical gaps:

| Missing Test | Risk |
|---|---|
| AGEClient $param substitution correctness | Silent data errors if substitution has edge cases |
| app/framework/ drift from copilot_sdk/framework/ | Already drifted (audit.py 5KB diff) |
| `datetime()` prohibition in AGE callers | compute_volume_baseline() will fail |
| Conservation law α input correctness | learning_rate=0.02 → alpha_effective chain |
| SOCAgent NOT in live triage path | Confuses anyone reading the agent |

### Findings Summary

| Issue | Severity | What to Do |
|---|---|---|
| app/framework/ copy diverging from copilot_sdk/framework/ | **P1 structural** | Add drift detection test comparing file hashes. Commit to migration or explicit fork. |
| datetime() in compute_volume_baseline() | P2 | Replace with Python-side epoch arithmetic |
| HAVING clause in compute_analyst_precision() | P2 | Move to Python filter after query |
| SOCAgent in copilot-sdk encodes SOC domain knowledge | P2 | Move to SOC backend or abstract behind protocol |
| Lazy imports hide ci_platform dependency | P3 | Consider module-level import with GRAPH_BACKEND guard |
| No drift detection test for framework copies | P3 | 5-line test comparing file hashes across repos |
| Two parameter patterns (inline _S() vs dict) | P3 | Standardize on one — AGEClient handles both but consistency matters |
| ~$param violations reclassified~ | Closed | AGEClient handles via Python substitution |

**File:** `backend/app/domains/soc/factors.py` — ~900 lines  
**Status:** Fully reviewed. AGE-compliant active path. Two documented tech debt items.

### Active Factor Pipeline — 6 Computers, Max 4 Graph Queries

| Index | Factor Name | Class | Graph Method | Queries |
|---|---|---|---|---|
| 0 | privileged_identity_context | `PrivilegedIdentityContextFactor` | Context attribute read | 0 |
| 1 | asset_criticality | `AssetCriticalityFactor` | `[:DETECTED_ON]→Asset→[:STORES]→DataClass` | 1 |
| 2 | threat_intel_enrichment | `ThreatIntelEnrichmentFactor` | `[:HAS_INDICATOR]→ThreatIndicator` + `[:MEMBER_OF]→Campaign` | 2 |
| 3 | pattern_history | `PatternHistoryFactorComputer` | `[:TRIGGERED_EVOLUTION]→EvolutionEvent` (W2 path) | 1 |
| 4 | time_anomaly | `TimeAnomalyFactor` | Property read (TD-014) | 0 |
| 5 | device_trust | `DeviceTrustFactor` | Property read (TD-015) | 0 |

Factor index 3 (pattern_history) matches `factor_snapshot[3]` in the D-02 fix — confirmed correct.

### D-01 Polarity Inversions — Mechanics Confirmed

**DeviceTrustFactor (Factor 5):** Computes `untrusted_components / 3`. Result: 0.0 = fully trusted (all MFA+fingerprint+VPN present), 1.0 = fully untrusted. HIGH value = HIGH risk. Factor name says "trust" but HIGH value means LOW trust. Centroids trained with this — suppress centroid sees LOW device_trust, escalate centroid sees HIGH.

**ThreatIntelEnrichmentFactor (Factor 2):** Two-pass with inverted polarity:
- Pass 1 (IOC): HIGH severity → 0.85-1.0. NOT inverted — high value = high risk.
- Pass 3 (campaign): HIGH campaign → 0.05, MEDIUM → 0.20, none → 0.50. INVERTED — low value = high risk.
- Score = `min(pass1, pass3)` — takes lowest value.

**Critical edge case:** When no IOC (pass1=0.0) AND no campaign (pass3=0.50), `min` returns **0.0**. In the inverted convention, 0.0 = maximum threat. This means alerts with NO threat intelligence at all return the same factor value as alerts with the highest-severity IOC. Centroids were calibrated with this behavior so scoring still works, but discriminative power for no-TI vs high-TI alerts is reduced. This is the core of D-01 — consistent but semantically wrong. V1.1 fix requires polarity correction + centroid regeneration.

### Two PatternHistory Classes — Intentional Distinction

`PatternHistoryFactor` — **Legacy/inactive.** Counts decision accuracy by `alert_type` across all history. Lives in the `SOC_FACTOR_TEMPLATES` backward-compat path, feeding `compute_soc_factors()` and the legacy `execute_action()` endpoint. NOT in the live ProfileScorer pipeline.

`PatternHistoryFactorComputer` — **Active W2 path.** Uses TRIGGERED_EVOLUTION edges with exponential recency decay (half-life=30 decisions by decision count, not time). Returns action-specific weighted mean. This IS the live factor computer.

### AGE Compliance — Active Path

All active factor computers are AGE-compliant:
- `AssetCriticalityFactor`: `{{alert_id: {_S(alert_id)}}}` — correct
- `ThreatIntelEnrichmentFactor`: `{{alert_id: {_S(alert_id)}}}` inline — correct, no `$param`
- `PatternHistoryFactor` (legacy): `{_S(situation_type)}` inline — correct. `AS total`, `AS correct` aliases — fine, not reserved words.
- `PatternHistoryFactorComputer`: `{_S(category)}` and `{_S(action_index)}` inline — correct

**Latent bug in inactive code:** `TravelMatchFactor` (NOT in active SOC_FACTORS) uses `MATCH (u:User {{id: {_S(user_id)}}})` — property name `id` is likely wrong (User nodes use `user_id` per GRAPH_CONTRACT). Safe now but must be fixed before activating TravelMatchFactor.

### Tech Debt — Documented and Known

- **TD-014** (TimeAnomalyFactor L4): Reads `alert.business_hours_login` property directly. Future: traverse `(User)-[:ACTIVE_AT]->(TimeSlot)`.
- **TD-015** (DeviceTrustFactor L5): Reads `mfa_completed`, `device_fingerprint_match`, `vpn` properties. Future: traverse `(Alert)-[:USES_DEVICE]->(Device)`.

Both are explicitly documented in code with tech-debt IDs.

### SOC_FACTOR_TEMPLATES — Demo Layer, Not Live Computation

The large `SOC_FACTOR_TEMPLATES` dict (ALERT-7823, ALERT-7824, brute_force, c2_beacon, etc.) contains hardcoded factor values for demo scenarios. These feed `compute_soc_factors()` which is the backward-compat layer for `execute_action()`. This is NOT how `analyze_alert()` computes factors — that path calls the actual FactorComputer classes above.

This confirms BUG-P2-05: `execute_action()` returns static template factors, `analyze_alert()` computes live factors. Both create Decision nodes, but with fundamentally different factor vectors.

### Summary Findings

| Issue | Severity | Factor |
|---|---|---|
| No-TI alerts return 0.0 (same as max-threat) — D-01 edge case | Design (D-01 deferred v1.1) | 2 |
| TravelMatchFactor uses wrong User property `id` vs `user_id` | P2 (inactive — fix before activating) | inactive |
| TimeAnomalyFactor reads property directly | Tech debt TD-014 | 4 |
| DeviceTrustFactor reads property directly | Tech debt TD-015 | 5 |
| execute_action() uses static templates vs live computation | BUG-P2-05 (known) | backward-compat |

**No new P1 bugs.** AGE compliance clean in active path.

---

## Part 13 — soc.py Analysis (4,001 lines, 51 endpoints)

**File:** `backend/app/routers/soc.py`  
**Status:** Fully reviewed. The platform's largest single file — a monolith, not a router.

### Scale and Scope

51 endpoints plus embedded service logic: 10 mock data generators, 5 tab content builder functions (~400 lines combined), 2 campaign formatting helpers, inline utility functions, a category routing translation table, request/response models, and `METRIC_REGISTRY` constant. This explains the 291-community Leiden finding — it's not a router with tangled coupling, it's a collection of complete subsystems crammed into one file.

### New AGE $param Violations — Same Migration Pattern as learning_health.py

| Location | Params Violated | Impact |
|---|---|---|
| `get_detection_engineering()` noise map | `{"cat": cat}` → `$cat` | Noise map returns None fp_rate for all categories |
| `explain_decision()` — 3 queries | `{"decision_id": ...}`, `{"category": ...}` | Explain endpoint may fail on AGE |
| `get_analyst_benchmarking()` — 4 queries | `{"source": SOURCE}` → `$source` | **All F9 ShadowDecision queries fail** → returns synthetic fallback |
| `_tab3_content()` override_rate | `{"cat": rec_category}` → `$cat` | Tab 3 override rate always returns default 15.0% |

`get_analyst_benchmarking()` is the most impactful — all 4 of its ShadowDecision queries use `$source`. The entire F9 analyst benchmarking report returns "accumulating" status or synthetic fallback on AGE.

### Endpoint Map — 51 Endpoints Across 9 Functional Areas

| Area | Count | Key Endpoints |
|---|---|---|
| Analytics / Tab 1 | 8 | /soc/query, /soc/analytics, /soc/threat-landscape, /soc/detection-engineering |
| Learning state / Tab 2 | 12 | /soc/learning-state, /soc/centroid-heatmap, /soc/centroid-export, /soc/analyst-weights |
| Alert triage / Tab 3 | 6 | /soc/explain/{id}, /soc/provenance/{id}, /soc/attack-chains |
| Economics / Tab 4 | 4 | /soc/benchmarking-report, /soc/accuracy-trajectory, /soc/onboarding-calendar |
| Executive / Tab 5 | 5 | /soc/executive-narrative, /soc/executive-narrative/pdf, /soc/epistemic-state |
| Campaigns F6 | 3 | /soc/campaigns, /soc/campaigns/{id}, POST /soc/campaigns/recorrelate |
| Governance | 4 | /soc/compliance, /soc/transparency, /soc/analyst-benchmarking, /soc/f9-report |
| PITR | 3 | /soc/backup-centroid, /soc/restore-centroid, /soc/centroid-backups |
| Sentinel | 2 | /sentinel/alerts, POST /sentinel/writeback-test |

### Cross-Context Metric Query — Display vs Reality

`METRIC_REGISTRY` has 4 "cross-context" metrics (travel risk, device trust, policy conflicts, TI coverage) with rich 5-6 source provenance narratives. However, when any cross-context metric is matched, the actual AGE query run is one hardcoded TI lookup:
```
MATCH (a:Alert)-[:HAS_INDICATOR]->(ti:ThreatIndicator) RETURN a.alert_id, ti.source, ti.indicator_type LIMIT 10
```
The rich 6-source provenance in the API response is display narrative, not live computation. Intentional for demo — must be replaced with real queries for pilot.

### SENTINEL_TO_INTERNAL — Second Category Routing System

soc.py contains a 30-entry `SENTINEL_TO_INTERNAL` dict, a second routing mechanism alongside `resolve_alert_category()` in config.py. It has already been partially updated to fix D-06-adjacent mappings (c2_beacon → malware_execution, phishing → malware_execution). Two separate routing systems that could diverge.

### Well-Engineered Pattern — SOURCE Comments

Multiple endpoints explicitly document data source and restart behavior inline:
```python
decision_count = ls.decision_count  # SOURCE: in-memory LearningState (resets on restart)
verified_decisions = snap.verified_decisions  # SOURCE: GraphSnapshot (graph-backed, survives restart)
```
This is production-quality documentation of a subtle architectural distinction.

### D-01 Incidental Compensation in Tab 3

`_tab3_content()` kernel_note: "device_trust (σ=0.28) contributes 6% of its nominal weight." The highest-noise factor (device_trust, σ=0.28) is also a D-01 inverted polarity factor. Under DiagonalKernel it's automatically down-weighted — partially compensating for the inversion at high noise ratio. Incidental, not designed, but a useful property.

### AGE Compatibility — Two Patterns Need Validation

`count(CASE WHEN t.severity IN ['critical','high'] THEN 1 END)` — both `COUNT(CASE WHEN...)` and `IN [list]` syntax need AGE validation. Not confirmed working.

`NOT exists((a)<-[:DECIDED_ON]-())` — this IS the correct AGE pattern per standing rules (use NOT exists() not NOT (a)<-[:REL]-()). Clean.

### BACKLOG-063 Dead Endpoint

`/soc/benchmarking-level2` comment: "mock data, not called by frontend — remove when L2 benchmarking is implemented." Serves hardcoded mock A/B data. Should be removed or feature-flagged.

### v1.1 Decomposition Targets

Extract from soc.py into dedicated modules:
- `_tab1_content()` through `_tab5_content()` → `services/tab_content.py`
- Mock data generators (MTTR, FP rate, etc.) → `services/demo_data.py`
- `METRIC_REGISTRY` + `match_metric()` → `services/metric_registry.py`
- `SENTINEL_TO_INTERNAL` + `_resolve_category()` → merge into `domains/soc/config.py`
- Campaign formatters → `domains/soc/campaigns.py` (already exists)

### Summary Findings

| Issue | Severity | Location |
|---|---|---|
| $param in analyst benchmarking (4 queries) | **P2** — F9 returns fallback (AGEClient handles substitution, but HAVING still fails in same function) | get_analyst_benchmarking() |
| $param in explain_decision (3 queries) | **P2** — substitution handled by AGEClient | explain_decision() |
| $param in detection-engineering noise map | **P2** — substitution handled by AGEClient | get_detection_engineering() |
| $param in _tab3_content override rate | **P2** — substitution handled by AGEClient | _tab3_content() |
| Cross-context metrics are display fiction | P2 (pilot) | query_soc_metrics() |
| SENTINEL_TO_INTERNAL diverges from config.py | P2 — two routing systems | soc.py global |
| benchmarking-level2 is dead mock endpoint | P3 (BACKLOG-063) | /soc/benchmarking-level2 |
| COUNT(CASE WHEN) + IN list syntax | ⚠️ AGE compatibility uncertain | get_threat_landscape() |

---

*Document version: v4.0 · May 3, 2026 · Living document*  
*Code is authoritative over docs where they conflict*


---

## Part 15 — Protocol Definitions Review (copilot-sdk PyPI Readiness)

**Files:** `copilot_sdk/protocols/domain_config.py`, `factor_computer.py`, `source_connector.py`, `referral_rule.py`
**Verdict:** NOT ready for PyPI. Three breaking issues confirmed.

### Breaking Issues (Must Fix Before PyPI)

**1. FactorComputer.factor_name vs SOC's `name` — CONFIRMED 9 CALL SITES**
Protocol requires `factor_name: str`. SOC uses `name`. Call sites confirmed:
- `evolution.py:236, 363` — `[c.name for c in computers]`
- `soc.py:2756` — `[c.name for c in SOCDomainConfig.get_factor_computers()]`
- `triage.py:274, 400, 572, 601` — `[c.name for c in computers]`
- `gae_state.py:124` — `[c.name for c in SOCDomainConfig.get_factor_computers()]`
- `simulation.py:492` — `[c.name for c in computers]`

**Recommended fix (zero blast radius):** Add `factor_name = name` as a property alias on all 6 FactorComputer classes in factors.py. Callers continue using `.name` unchanged. Protocol is satisfied. Effort: 6 lines. Alternative: rename `.name` → `.factor_name` everywhere — 2 hours + 9 call sites across 5 files.

**2. FactorComputer.factor_index missing from all SOC implementations**
Add `factor_index` to each SOC FactorComputer, or remove from protocol.

**3. Polarity convention unspecified**
D-01 showed ThreatIntel and DeviceTrust return inverted values. No protocol specifies the convention. Add to FactorComputer docstring: "Returns float in [0.0, 1.0]. Convention: 0.0 = maximum risk signal, 1.0 = minimum risk / neutral. Example: high IOC severity → value near 0.0."

### Protocol Compliance Matrix

| Protocol | SOCDomainConfig | S2PDomainConfigV2 | Legacy S2PDomainConfig |
|---|---|---|---|
| DomainConfig | ⚠️ spirit yes, mypy no | ✅ full | ❌ get_initial_centroids returns dict |
| FactorComputer | ❌ name vs factor_name | N/A | N/A |
| SourceConnector | ✅ | N/A | N/A |
| ReferralRule | ✅ | N/A | N/A |

S2PDomainConfigV2 is the reference protocol implementation. SOCDomainConfig satisfies runtime_checkable isinstance() checks but fails mypy on attribute declarations.

---

## Part 16 — S2P Preview Tab Review

**Files:** `s2p-copilot/backend/app/routers/s2p_preview.py`, `services/synthetic_invoices.py`, `domains/s2p/config.py`
**Verdict:** Demo-ready. Live ProfileScorer scoring confirmed for /queue and /conservation.

### Endpoint Status

| Endpoint | Data Source | Live? |
|---|---|---|
| `/api/s2p/preview/queue` | ProfileScorer.score() on synthetic invoices | ✅ Live |
| `/api/s2p/preview/conservation` | Computed from live scored invoices | ✅ Live |
| `/api/s2p/preview/compounding` | Hardcoded linear trajectory 0.72→0.90 | ❌ Synthetic (labeled `source: "synthetic_demo"`) |
| `/api/s2p/preview/suppliers` | s2p_demo_suppliers.json fixture | Static JSON |
| `/api/s2p/preview/config` | S2PDomainConfigV2 class attributes | Config read |

`_get_scorer()` creates a real `ProfileScorer` from `S2PDomainConfigV2.get_profile_centroids()` (shape 5,5,7). Real `scorer.score()` called with numpy factor vectors. **"Same engine, different domain" claim is TRUE** for queue and conservation.

S2PDomainConfigV2 (5,5,7) confirmed as the only config used by preview endpoints. Legacy S2PDomainConfig (6,4,6) only in s2p.py legacy endpoints — no legacy shape bleeds into preview.

**Caching concern:** `_scorer` and `_scored_invoices` are module-level globals. Call `reset_preview_state()` after any demo reset to avoid stale cached invoices.

---

## Part 17 — Bootstrap Pipeline Review

**Files:** `gae_state.py` (init_learning_state), `ci-platform/ci_platform/onboarding/`
**Verdict:** Startup bootstrap fully automated. Customer data onboarding pipeline exists but lacks API endpoint.

### Startup Bootstrap (Automated, Runs at Server Start)

`init_learning_state()` runs at startup via `startup_event()`. Three paths: checkpoint with `bootstrap=True` → load; legacy checkpoint → re-bootstrap; no checkpoint → fresh bootstrap. `bootstrap_calibration()` uses `SOC_BOOTSTRAP_ROUNDS=10`, `samples_per_action=5`, `sigma=0.08`, `seed=42`. Runs in seconds. Non-blocking.

### Customer Data Onboarding Pipeline (Exists, No API Endpoint)

`ci_platform/onboarding/pipeline.py` is a complete 3-stage automated pipeline:
1. **Load**: ingest alert JSON, entity resolution (user/asset de-duplication)
2. **Compute**: `DeploymentQualifier.qualify()` — measures per-factor σ, τ sweep (5 values), kernel recommendation (l2 vs diagonal), enrichment advisor with per-factor noise reduction actions, creates sealed LedgerEntry at qualification time
3. Produces: `tau_initial`, `sigma_per_factor`, `noise_classification`, `learning_recommended`, `category_distribution`, enrichment priorities

This IS the $1.91 onboarding automation foundation. **The gap:** No API endpoint in the SOC backend accepts customer alert data and runs this pipeline. Running it today requires a Python script + manual config update + restart.

**Block 1 work needed:** Add `POST /api/admin/onboard` endpoint. Prerequisite for the "$1.91 onboarding" claim.

### Pilot Step 6 Current Reality

Today's "re-bootstrap from customer data" = Python script → read recommended_config → manually update CalibrationProfile → restart server. Not a click.

---

## Part 18 — audit.py Tamper-Evidence Verification

**File:** `ci_platform/audit/evidence_ledger.py`
**Verdict:** CONFIRMED genuinely tamper-evident. EU AI Act Article 12 claim is supportable.

`compute_hash()` includes in SHA-256 payload: `chain_index`, `decision_id`, `timestamp`, `alert_id`, `factor_breakdown`, `action`, `confidence`, `centroid_state_hash`, `prev_hash`, `kernel_type`, `noise_zone`, `conservation_status` — JSON-serialized with `sort_keys=True`.

`is_valid()` recomputes hash from payload, compares to stored `entry_hash`. `verify_chain()` checks: (1) every entry `is_valid()`, (2) `entry.prev_hash == entries[i-1].entry_hash`. Modifying any included field causes `verify_chain()` to return False.

**Intentionally mutable fields** (not in hash): `outcome`, `analyst_override`. Correct — these are updated via `OutcomeEntry` event sourcing. `append_outcome()` validates `decision_entry_hash` exists in chain before accepting — prevents forged outcomes.

### BACKLOG-074 Backport Scope

SOC's canonical additions vs SDK's earlier version:

| Item | SOC has | SDK has | Action |
|---|---|---|---|
| Lock type | `asyncio.Lock` | `threading.Lock` | Replace |
| Epoch archive | `_ARCHIVED_EPOCHS` | Missing | Add |
| Outcome chain | `OutcomeEntry` + `append_outcome()` | `record_outcome()` mutates entry directly (WRONG) | Replace entirely |
| Merged view | `get_decision_rows()` | `get_decisions()` (decisions only) | Replace |
| Restart resilience | `rebuild_from_age()` | Missing | Add |
| Chain metadata | `chain_index`/`epoch`/`archived_epochs` | Missing | Add to verify_chain() |

SDK's `record_outcome()` is architecturally incorrect — mutates sealed entries directly. Backport requires rewriting it entirely.

---

## Part 19 — SAML Auth Flow Review

**Files:** `ci_platform/auth/saml.py`, `backend/app/routers/auth.py`
**Verdict:** SSO endpoint correct. CA-P2-01 gap is middleware wiring, not SAML implementation.

### What's Implemented (Correct)

Complete SAML SSO flow: `/saml/login` → IdP redirect, `/saml/acs` → validates SAMLResponse, extracts `user_email`, derives role from groups, creates JWT, sets `soc_auth_token` httponly cookie, `/saml/logout` → deletes cookie, `/saml/metadata` → SP XML, `/saml/status` → config check.

Two validation paths: full `python3-saml` signature verification (when IdP cert configured) + fallback XML parse (test use).

### The Gap for CA-P2-01

ACS sets `soc_auth_token` cookie → auth middleware must read cookie → decode JWT → set `request.state.user = decoded["sub"]`. Without this middleware wired, triage.py's `request.state.user` raises AttributeError → falls back to "anonymous". This is the analyst identity bug.

**Fix effort:** 1-2 hours of middleware configuration. SAML is DONE. Work is: ensure auth middleware sets `request.state.user` from validated JWT on every request + ensure `saml_enabled=True` in pilot config.

---

## Part 20 — RuntimeEvolutionTab.tsx Review

**File:** `frontend/src/components/tabs/RuntimeEvolutionTab.tsx` — 3,570 lines, 74 useState
**Verdict:** Stable for Loom. All endpoints live. One hardcoded UI bug.

### useState Breakdown

~18 fetch calls × 3 state each (loading/error/result) = 54 data state + ~20 UI state (expanded sections, selected IDs, input values) = 74 total. All independent — no cascading failures.

### All Endpoints Live

Every endpoint called by this tab returns real data (none are the mock/narrative endpoints from Part 13): deployment-state, learning-state, evolution-events, graph-stats, accuracy-trajectory, what-if conservation simulation, factor-analysis, model-swap-trial, centroid-backups, reward-summary.

### One UI Bug — Hardcoded "Learning active"

Lines ~5090-5093: green dot + "Learning active" is hardcoded HTML. Does NOT read from conservation state. Always shows green regardless of whether conservation is AMBER or RED (learning paused). **Do not demonstrate this indicator during a Loom recording.**

### Error Handling

Each section independently guards against backend errors — shows red-bordered message on failure, loading spinners while fetching. No section failure propagates to others. No white-screen crash risk.

### Loom Recording Guidance

Safe to record. Best demo elements: what-if conservation simulator (live), model swap trial button (proves LLM independence). Avoid: hardcoded "Learning active" green indicator.

---

## Part 21 — Third Framework Copy Confirmed

S2P backend's `app/framework/` directory contains the same ~20 files as SOC's `app/framework/` and copilot-sdk's `copilot_sdk/framework/`. This is now a confirmed **three-way copy**, all actively used:

```
copilot_sdk/copilot_sdk/framework/              ← SDK (earlier version)
gen-ai-roi-demo-v4-v50/backend/app/framework/  ← SOC (richest, audit canonical)
s2p-copilot/backend/app/framework/             ← S2P (confirmed active — scorer.py, ols_status.py)
```

**S2P framework is NOT dead scaffolding (confirmed Q12).** `scorer.py` imports `from app.framework.iks_base import compute_iks` — live scoring path. `ols_status.py` has wildcard re-export from `app.framework.ols_status`. Any framework change must be applied in all three locations until migration to `copilot_sdk` imports is complete. Drift detection test must cover all three.

---

*Document version: v6.0 · May 3, 2026 · Living document*
*Code is authoritative over docs where they conflict*

---

## Part 22 — Coding Session Q&A: 16 Questions Answered

### Q2 — AgentEvolver Architecture

**Files:**
- `app/services/evolver.py` — UCB prompt variant selection, `get_prompt_variant()`, `record_decision_outcome()`, `check_for_promotion()`, `get_evolution_summary()`, `get_weight_history()`
- `app/framework/evolution_ledger.py` — AE-04 in-memory ledger + `_SHADOW_INDEX` projection. **NOT hash-chained** (explicitly stated)
- `app/services/variant_generator.py` — AE-03 graph-context-driven variant generation
- `app/routers/admin.py:421` — `POST /admin/evolver/scan` manual trigger, `POST /admin/evolver/promote` promotion gate

**Integration with triage pipeline:**
- `triage.py:534` — Step 8c: AE-02 per-variant shadow comparison (fire-and-forget, non-blocking)
- `evolution.py:310-317` — Step 9: `get_prompt_variant()` → `record_decision_outcome()` → `check_for_promotion()` → `get_evolution_summary()`

**Critical distinction:** EvolutionLedger tracks prompt variant performance. TRIGGERED_EVOLUTION edges (triage.py:1278) track W2 flywheel centroid learning. These are completely separate systems.

**EvolutionLedger reset** registered with StateManager — resets on demo cycle. TRIGGERED_EVOLUTION edges are graph-persistent.

### Q3 — Evidence Room Growth

evidence_room.py = 9,797 bytes (review described ~243 lines ≈ 7KB). FEATURE-09 added ~40% more code. The audit fail-open bug (BUG-P1-07: `_empty_hash_chain()` returns verified=True on exception) is still open — not fixed as part of FEATURE-09.

GovernanceTab (Tab 7) = the shipped Evidence Room frontend. See Q12.

### Q4 — FW-10 / FW-13 Endpoints

**FW-10 (LearningStatePanel):** `framework_router.py:930` — phase-aware learning state endpoint for Tab 3 LearningStatePanel. Backend-only addition.

**FW-13 (S2P D=7 tensor):** Added `S2P_ENRICHED_PLATEAU = 0.781` and `S2P_COLD_PLATEAU = 0.701` constants to `constants.py`. These are reference values for the 7-factor S2P accuracy trajectory. Config change (S2PDomainConfigV2 already reviewed) + constants. No new frontend tab.

`framework_router.py:1015` — `get_channel_decomposition()` endpoint for ThreeChannelPanel.

### Q6+Q7 — Triage and Outcome Pipeline (Current)

**analyze_alert() call chain:**
1. Guard: ProfileScorer must be attached
2. Factor vector: orchestrator → FactorComputers → Neo4j (6 factors)
3. ProfileScorer.score() — L2 centroid proximity, A=4, τ=0.1
4. Step 8b: Referral VETO (independent of ProfileScorer)
5. Step 8c: AE-02 shadow comparison (fire-and-forget)
6. record_decision() audit write
7. Response with decision_method string

**report_decision_outcome() call chain:**
1. Conservation check → `_conservation_block` (fail-closed: unknown → block)
2. LEARNING_ENABLED gate
3. `acquire_scorer() as _ps_out` — D-05 pattern in live path ✅
4. `set_conservation_status()` on scorer
5. `guarded_update()` — routes through D3/D2/D7 spike guards AND conservation freeze
6. IKS computation update
7. TRIGGERED_EVOLUTION edge write (W2 flywheel — correct decisions only)

The outcome path is well-layered: conservation → LEARNING_ENABLED → acquire_scorer → guarded_update. D-05 fix confirmed active.

### Q12 — 7 Tabs (Not 5+1)

```typescript
type TabId = 'soc' | 'evolution' | 'triage' | 'compounding' | 'executive' | 's2p' | 'governance'
```

| # | Tab | Component | Notes |
|---|---|---|---|
| 1 | soc | SOCAnalyticsTab | Analytics dashboard |
| 2 | evolution | RuntimeEvolutionTab | **Default on load** |
| 3 | triage | AlertTriageTab | Alert queue |
| 4 | compounding | CompoundingTab | Compounding curves |
| 5 | executive | ExecutiveNarrativeTab | Executive summary |
| 6 | s2p | S2PPreviewTab | S2P domain preview |
| 7 | governance | GovernanceTab | **NEW — Evidence Room (FEATURE-09)** |

Description: "Governance evidence, audit chain, conservation health, and evolution trail"

**VIS-2 cross-tab navigation:** App.tsx listens for custom events dispatched by OutcomeFeedback bridge link. `const tab = (e as CustomEvent).detail?.tab as TabId` → `setActiveTab(tab)`. Tab 3 outcome can trigger navigation to Tab 2 this way.

The session continuation doc's "5 SOC tabs + 1 S2P preview" description is stale. Current count is 7.

### Q13 — Frontend State Management: No Global Store

Zero results for createContext, useReducer, createStore, zustand, Redux across all .ts and .tsx files. **Each tab manages its own fetch/loading/error state independently.**

Cross-tab consistency is eventual, not reactive:
- Tab 3 submits outcome → Tab 2 sees it only on next re-fetch (tab switch or manual refresh)
- VIS-2 custom events handle navigation only, not data sync
- No shared state atom between tabs

Implication: UI may show stale IKS or centroid data immediately after an outcome is submitted, until the user navigates back to Tab 2.

### Q14 — Test Organization

**By size (top 10):**

| File | Size | Coverage area |
|---|---|---|
| test_tab_content.py | 55KB | Tab content contract validation |
| test_variant_generator.py | 38KB | AE-03 graph-driven variants |
| test_promotion_gate.py | 30KB | AE promotion gate |
| test_eval_upload.py | 26KB | Eval data upload |
| test_cross_graph_discovery.py | 25KB | FEATURE-07 discovery |
| test_evolution_ledger.py | 23KB | AE-04 ledger |
| test_shadow_runner.py | 22KB | AE-02 shadow comparison |
| test_referral_rules.py | 15KB | R1-R7 referral rules |
| test_audit_chain_wiring_extended.py | 14KB | Audit chain |
| test_ae_integration.py | 14KB | AgentEvolver end-to-end |

AgentEvolver has 5 dedicated test files totalling ~108KB. It is the most heavily tested subsystem.

No shared test graph fixture — tests use mocks or the live AGE instance. test_age_contracts.py validates AGE syntax compatibility.

### Q15 — Contract Validation Tools

`scripts/validate_contracts.py` — manual script, not CI. Used to validate contracts against baseline snapshots.
`scripts/collect_tab_content.py` — manual script that collects tab content for baseline generation.
`tests/test_tab_content.py` (55KB) — the CI version of contract validation. This is what runs in the test suite.

### Q16 — RL Reward Architecture and RL-01 Landing Zone

**What exists today:**
- `app/framework/feedback_base.py:147` — `get_reward_summary()` — in-memory asymmetric reward aggregate using FEEDBACK_GIVEN dict. correct=+0.3, incorrect=-6.0, ratio=20:1.
- `app/services/feedback.py:20` — re-exports from framework
- `triage.py:1696` — `GET /api/soc/rl-reward-summary` endpoint

No `RewardComputer`, `CreditAssigner`, or `ExplorationPolicy` classes exist.

**RL-01 (graded reward shaping) landing zone:**
- New file: `app/services/rl_engine.py` — `RewardComputer` class with graded reward tiers
- Extend: `app/framework/feedback_base.py:get_reward_summary()` — add graded tier breakdown
- Wire: `triage.py:report_decision_outcome()` after `guarded_update()` at ~L1130 — call `RewardComputer.compute(action, outcome, confidence, category)` and feed result into conservation signal
- Keep: existing `get_reward_summary()` endpoint interface stable — extend return shape only


---

*Document version: v18.0 · May 5, 2026 · Living document*
*Code is authoritative over docs where they conflict*

---

## Part 23 — MAP v5.65 Sync (May 5, 2026)

### Platform State (Corrected from MAP v5.65)

| Metric | Previous (v7) | Corrected (v8) |
|---|---|---|
| GAE tests | 1,183 | **1,203** |
| SOC backend tests | 1,003 | **1,340** |
| E2E tests | 254 | **271/272** |
| copilot-sdk tests | 18 | **23** |
| Total tests | ~2,764 | **~3,143** |
| Pilot code | open items | **9/9 ALL DONE** |
| AgentEvolver | in progress | **COMPLETE** (256 tests, 7× zero-fixer Codex) |
| Narrative contradictions | unknown | **17/17 fixed** |
| Narrative gaps | unknown | **7/7 filled** |
| Evidence Room (FEATURE-09) | shipped | **Confirmed Tab 7 GovernanceTab** |
| RL design | not started | **v1.0 COMPLETE** (3 documents) |

### CLAIM-RECONV Withdrawn

EXP-G1 v3 results: 100% convergence all conditions. γ_centroid = **1.02** (trivial — not the >1 acceleration claimed). DK weights HURT convergence **1.9×** after disruption.

**CLAIM-RECONV: WITHDRAWN.** The re-convergence γ>1 claim does not have experimental support.

**CLAIM-DK-STALE: ADDED.** Phase 2 coordinate descent is safety-critical. Stale DK weights degrade post-disruption recovery. Implication: when DK deploys, must validate against disruption scenarios — frozen stale weights are worse than L2.

Standing Rule violation update: §3 Rule 8 said "b=2.11 is sim-only." The stronger statement is now: re-convergence acceleration is not confirmed at all. γ=1.02 is statistically indistinguishable from 1.

### CA-PROTO-1/2/3 — Resolved

FactorComputer protocol issues (factor_name vs name, factor_index missing, polarity convention) were resolved during May 3-5 sprint. The alias approach or rename was implemented. PyPI blockers from Part 15 are now cleared.

### BACKLOG-074/079/080 — Done

- BACKLOG-074: audit.py backport from SOC to SDK — complete
- BACKLOG-079: S2P framework copy alignment — complete  
- BACKLOG-080: (unspecified, complete)

Three-way framework copy drift problem has been addressed. Drift detection test may now exist.

### RL Design v1.0 — Ready for Implementation

Three documents complete:
- `rl_design_v1.md` — 13 sections: RewardComputer, CreditAssigner, ExplorationPolicy, conservation-bounded Thompson sampling
- `rl_design_addendum_v1.md` — Libraries (numpy+scipy only), 6 demo scenarios, data sources
- `rl_design_llm_review.md` — 16 review questions for GPT/Grok external review

**Implementation order:** RL-01 (graded reward shaping, 2 days) → RL-02 (credit assignment, 1.5 days) → RL-03 (exploration policy, 1.5 days). RL-01 is critical for S2P.

**Landing zone (from Part 22, still valid):**
- New `app/services/rl_engine.py` — RewardComputer
- Extend `feedback_base.py:get_reward_summary()` — graded tier breakdown
- Wire into `triage.py:report_decision_outcome()` after `guarded_update()` at ~L1130

### Top 20 v9 — Current Priority Order

1. AE-REVIEW (Codex prompt ready)
2. CLAIMS-UPDATE (v6.2 — RECONV withdrawn, DK-STALE added)
3. **RL-01** (graded reward shaping — critical for S2P)
4. RL-02 (credit assignment)
5. RL-03 (exploration policy)
6. FW-11 (ci-platform consumers)
7. FW-12 (copilot-sdk consumers)
8. P2-SPRINT (remaining CA-P2 safety items)
9. TAB7-OVERRIDE (override analysis alignment)
10. TAB7-GOV (Art 9/15 RED investigation)
11-16. NAR-B1/B6/B2/D4/F3/B5 (narrative polish before Loom)
17. ENT-01 (CI/CD)
18. PB-02 (Docker)
19. ENT-02/03 (CORS + monitoring)
20. F-01 (Loom v1)

### Open Items from Insights Doc — Status Update

| Item | Previous status | MAP v5.65 status |
|---|---|---|
| datetime() fix | P1 pilot blocker (open) | **DONE** (Tier 0C all 8 resolved) |
| HAVING fix | P1 (open) | **DONE** |
| BUG-P1-07 audit fail-open | Open (5 min fix) | **DONE** (Tier 0C) |
| BUG-P2-02 UNKNOWN=GREEN | Open | Likely done (Tier 0C) |
| BUG-P2-03 frozen categories | Open | Likely done (Tier 0C) |
| BUG-P1-06 shape validation | Open | Likely done (Tier 0C) |
| CA-PROTO-1/2/3 | Open | **DONE** |
| BACKLOG-074 audit backport | Open | **DONE** |
| BACKLOG-079 S2P framework | Open | **DONE** |
| CA-SOCAGENT | "Live path" — wrong | **Dead code. P3 delete.** |
| Pilot checklist | Multiple open | **9/9 ALL DONE** |

### What Remains Open (from MAP v5.65)

| Item | Status | When |
|---|---|---|
| CA-P2-01 (analyst identity) | Deferred | v1.1 |
| CA-P2-05 (empty factor_vector) | Deferred | v1.1 |
| CA-PROTO-4 (mypy) | Deferred | v1.1 |
| FW-11 (ci-platform TwoPhaseStrategy) | Pending | Next |
| FW-12 (copilot-sdk health API) | After FW-11 | Next |
| AE-REVIEW (Codex) | Pending | Immediate |
| RL-01→03 | Pending | This week |
| TAB7-OVERRIDE + TAB7-GOV | Pending | Week 2 |
| ENT-01 CI/CD | Pending | Week 3 |
| PB-02 Docker | Pending | Before VPS |


---

*Document version: v18.0 · May 5, 2026 · Living document*
*Code + MAP v5.65 are authoritative over earlier doc versions where they conflict*

---

## Part 24 — AE-REVIEW Results (Top 20 v9 #1 Complete)

**Review tool:** gpt-5.5 (reviewer) + gpt-5.3 (fixer ×2)
**Initial verdict:** FAIL → **Final verdict:** PASS WITH P3

### P1 Bug — Promotion Batch-Count Gate (Fixed)

**Location:** `promotion_gate.py:38-45, 164-182, 229-247`

`MIN_SHADOW_BATCHES = 3` was defined but not enforced. `_compute_batch_std()` returned 0.0 when fewer than 3 batches existed — `evaluate_promotion()` treated that 0.0 as passing the variance gate. A variant could be promoted with sufficient total samples (≥50) but only 1-2 independent shadow batches, violating the four-gate invariant.

**Fix:** `evaluate_promotion()` now calls `_get_shadow_batch_stats()`, returns `continue` when `batch_count < MIN_SHADOW_BATCHES`. Batch count included in promotion evidence. Test at `test_promotion_gate.py:164-189` covers insufficient batch count. 54 promotion gate tests passing.

**Truth table after fix:**

| Condition | Verdict |
|---|---|
| fewer than 3 shadow batches | continue (was: promote possible) |
| all gates pass + ≥3 batches | promote |
| conservation fails | reject |
| win rate < 0.55 | reject |

### P2 Bug — Stale Shadow Buffer (Fixed)

**Location:** `shadow_runner.py:181-194, 229-236`

Verified entries for missing or no-longer-shadow variants were skipped during `_flush_shadow_batch()` but never removed from `_shadow_buffer`. `_maybe_schedule_flush()` kept counting all verified entries, so stale entries repeatedly triggered flushes indefinitely.

**Fix:** `_flush_shadow_batch()` tracks `stale_ids` (verified entries for missing/non-shadow variants) and removes them after processing. Unverified entries preserved. Valid entries removed only after successful `SHADOW_RESULT` ledger write (retry on failure preserved). 39 shadow runner tests passing.

### P2 Bug — Rollback Handler Without Event Loop (Fixed)

**Location:** `promotion_gate.py:373-379`

Rollback handlers registered with `ConservationStateMachine` were synchronous. If fired without a running asyncio loop (e.g., during test teardown or startup sequencing edge cases), they silently did nothing — rollback work dropped.

**Fix:** Handler captures running loop at registration time. Schedules via captured loop or current running loop. Logs warning instead of silently returning when no loop exists. Tests at `test_promotion_gate.py:643-680` (captured-loop scheduling) and `683-704` (no-loop warning) pass.

### P3 Remaining (Not Blocking)

`reset_promotion_gate()` clears `_REGISTERED_STATE_MACHINES` but GAE's `ConservationStateMachine` has no unregister path — handlers remain attached after reset. Old handlers lose their captured loop. Could cause duplicate handlers on re-registration. Future hardening only — not a blocker for current deployment.

### Architecture Verification

All five AE design intent claims confirmed by reviewer:

| Claim | Status |
|---|---|
| Graph-context-driven generation | ACHIEVED — signal evidence stored as `graph_context` at `variant_generator.py:794-803` |
| Durable lifecycle events | ACHIEVED — 6 event types with constants/validation |
| Per-variant shadow testing | PARTIAL → FIXED (stale buffer bug was the gap) |
| Conservation-bounded promotion | PARTIAL → FIXED (batch-count gate was the gap) |
| Rollback on deterioration | PARTIAL → FIXED (no-loop handler was the gap) |
| Domain-portable artifacts | ACHIEVED — SOC-specific rules at rule level only |
| P16 separation | ACHIEVED — promotion gate only reads scorer, never mutates |

**AGE query safety:** All PASS (7 queries reviewed — inline numeric cutoffs, `_S()` serialization, read-only, bounded LIMIT).

**State management:** All 5 state variables have reset paths chained through `evolver.py:461-468`. Stale buffer bug now fixed.

**Cross-module coupling:** Clean. ShadowRunner never auto-promotes. Promotion remains manual through admin flow. Registry transitions enforce status rules at `variant_registry.py:238-252`.

### What This Means for Top 20

AE-REVIEW was #1. It's done. Next: CLAIMS-UPDATE (#2, 1h) → RL-01 (#3, 2 days).

The AE subsystem is now architecture-reviewed with 256 tests + 3 bugs fixed. Safe to build RL on top of this foundation — the conservation-bounded promotion gate is now correct, which matters for RL-03 (Thompson sampling bounded by conservation law).

---

*Document version: v18.0 · May 5, 2026 · Living document*
*Code + MAP v5.65 are authoritative over earlier doc versions where they conflict*

---

## Part 25 — RL Design Addendum v1.0 Review

**Document:** rl_design_addendum_v1.md · May 5, 2026

### What's Correct

**Library choices:** numpy + scipy.stats is the right stack for a contextual bandit. The anti-library list (tf-agents, stable-baselines3, ray, trl, d3rlpy) is accurate — all are wrong abstractions. Zero new mandatory dependencies is the right constraint for MVP.

**Demo scenarios S1 and S3** (campaign amplification, dollar-weighted invoice) are the strongest commercially. S5 (tariff shock auto-pause) is the most differentiated — the only scenario that shows conservation law automatically bounding exploration risk without manual intervention.

**Data sources:** MITRE ATT&CK severity lookup + Hackett S2P financial impact + existing seed data for retroactive grading — all already in the product narrative, grounding reward magnitudes in independently verifiable sources.

### Design Gaps (Need Resolution Before RL-01)

**Gap 1 — SHAP cost underestimated: ✅ RESOLVED IN IMPLEMENTATION**
Implementation chose finite differences (delta=0.01, 12 scorer calls, milliseconds). Correct decision. SHAP deferred to v1.1 as recommended.

**Gap 2 — Chain credit mechanism unspecified: ✅ RESOLVED IN IMPLEMENTATION**
- `HALF_LIFE=30`, `LOOKBACK=100`, `CHAIN_DISCOUNT=0.5`
- `weight[i] = exp(-log(2) × age[i] / 30)`
- `credit_budget = abs(reward) × 0.5`
- `chain_reward[i] = credit_budget × weight[i] / total_weight`
- Queries TRIGGERED_EVOLUTION edges in AGE graph with `_S()` serialization — compliant

**Gap 3 — Conservation-bounded exploration formula: ✅ RESOLVED IN IMPLEMENTATION**
```python
def _compute_rate(self, headroom_ratio: float) -> float:
    headroom = float(headroom_ratio or 0.0)
    if headroom <= 1.0:
        return 0.0
    normalized = min((headroom - 1.0) / (self.target_headroom - 1.0), 1.0)
    return self.epsilon_base * normalized
```
headroom ≤ 1.0 → rate=0 (auto-pause). healthy headroom → rate scales to epsilon_base.

**Gap 4 — S6 cross-domain transfer overstated: Still valid.** Cross-signals are fixture-based. The infrastructure (XC-SOC-S2P-001/002/003, `source_copilot` field in evolution events) is designed in but not live.

### Schedule Revision

Addendum proposes +1 day for: severity lookup (2h) + impact lookup (1h) + retroactive grading (2h) + Yahoo R6 benchmark (4h Colab).

**Yahoo R6 benchmark should be replaced:** R6 is news article recommendation — action space, context space, and reward distribution are incompatible with CI's contextual bandit. "Matching published performance" on R6 doesn't validate CI's Thompson sampling. Better: synthetic bandit with known optimal policy (2h to construct), confirm convergence within expected regret bounds.

**Revised schedule:** severity lookup (2h) + impact lookup (1h) + retroactive grading (2h) + synthetic bandit benchmark (2h) = **7h ≈ +0.5 days** (not +1).

Total RL: RL-01 (2d) + RL-02 (1.5d) + RL-03 (1.5d) + data prep (0.5d) = **5.5 days.**

### What to Resolve Before Starting RL-01

1. Confirm chain credit mechanism in rl_design_v1.md — how is γ=0.7 derived? What's the attribution formula?
2. Confirm conservation-bounded exploration formula — what's the binding equation for exploration_rate vs. conservation_margin?
3. Replace Yahoo R6 with synthetic bandit validation spec
4. Reframe S6 scenario to remove false knowledge transfer claim

### Strong Elements to Preserve

- Binary reward as special case of graded (existing conservation law unchanged)
- MITRE ATT&CK severity → SOC reward weight mapping
- Hackett benchmark → S2P financial impact ranges
- Retroactive grading script (validates graded q ≈ binary q on existing 4860 decisions)
- S5 tariff shock scenario — strongest unique demo element

---

*Document version: v18.0 · May 5, 2026 · Living document*
*Code + MAP v5.65 are authoritative over earlier doc versions where they conflict*

---

## Part 26 — SDK Architecture Analysis (May 11, 2026)

**Source:** MAP v5.86 + copilot_sdk/scoring/scorer.py, storage.py, backend/scoring_router.py, conservation_router.py, apps/dataops/backend/app/main.py, SOC tests/test_rl_full_pipeline.py

### Two-Tier Architecture (Corrected)

The platform now has two fundamentally different copilot architectures:

```
Tier A — SOC (legacy full-stack)
  Persistence: AGE/PostgreSQL (WSL2, port 5433)
  Framework: app/framework/ copy + copilot_sdk/framework/
  RL: app/services/rl_engine.py (SOC-specific)
  Complexity: High — 1,572 tests, 280 E2E, 51 endpoints

Tier B — SDK copilots (Trading, Purchasing, DataOps)
  Persistence: SQLite (DecisionStore — per-domain .db file)
  Framework: copilot_sdk directly (no app/framework/ copies)
  RL: scoring_router._signed_reward() (domain-aware graded rewards)
  Complexity: Low — ~22-81 tests, router factories, clean pattern
```

### CompoundingScorer — SDK Core

**File:** `copilot_sdk/scoring/scorer.py`

Clean wrapper: `GAE ProfileScorer` + `DecisionStore (SQLite)` + `DomainPreset`.

**Factory:** `CompoundingScorer.from_preset(domain, db_path=None)`
- Looks up domain in `PRESET_REGISTRY`
- Creates `DecisionStore` (SQLite at `copilot_sdk/data/{domain}.db`)
- Loads latest centroids from SQLite, or falls back to `preset.bootstrap_centroids`
- Wraps in `ProfileScorer`

**Key methods:**
- `score(factors, category)` → ScoreResult — calls GAE scorer, saves to SQLite
- `learn(decision_id, actual_action)` → LearnResult — calls GAE update, saves outcome + centroid checkpoint
- `fingerprint()` → FingerprintResult — sigma per factor from verified decisions
- `trajectory()` → TrajectoryResult — IKS over time from centroid checkpoints
- `export(path)` / `load(path)` — JSON serialization for portability

**`learn()` eta pattern:** Temporarily overrides `scorer.eta` and `scorer.eta_override`, calls update, restores original values. Clean per-decision rate control without global state mutation.

**IKS formula (100-point, 4 equal components):**
```python
iks = (
    min(verified / 500.0, 1.0) * 25.0   # volume component (max at 500 decisions)
  + accuracy * 25.0                       # accuracy component
  + (1.0 - mean_sigma / 0.5) * 25.0      # fingerprint/DK component
  + coverage * 25.0                       # category coverage (max when all categories ≥10 decisions)
)
```
Different from SOC's IKS which is computed in `app/services/iks.py`.

### DecisionStore — SQLite, Not AGE

**File:** `copilot_sdk/scoring/storage.py`

Pure SQLite. Three tables: `decisions`, `outcomes`, `centroid_checkpoints`.

`HAVING count >= ?` at L206 in `count_categories_with_n()` — **this is SQLite HAVING, fully supported. NOT the AGE HAVING bug.** The AGE HAVING bug scope is SOC only.

Centroid checkpoints stored as JSON — enables IKS trajectory without AGE graph.

Thread safety: SDK copilots use `_FreshScorerProxy` pattern (open new CompoundingScorer per request, close in `finally`). No shared SQLite connection across threads.

### Router Factories — SDK Public API

Three factory functions create domain-parametric FastAPI routers:

**`create_scoring_router(domain, db_path, scorer_factory)`**
Mounts: `POST /score`, `POST /learn`, `GET /fingerprint`, `GET /trajectory`, `GET /history`

Reward computation in `_signed_reward()` — domain-aware graded rewards:
- `trading`: `position_size × research_depth × time_horizon`
- `purchasing`: `stockout_revenue_loss` or `waste_cost` from context
- `dataops`: `business_criticality × impact_scope`

This is RL-01 graded reward shaping at the SDK level — different from SOC's rl_engine approach.

**`create_conservation_router(domain, state_provider)`**
Mounts: `GET /conservation/status`, `POST /conservation/what-if`
Uses `gae.calibration.check_conservation()`, `compute_theta_min()`, `conservation_status()` directly from GAE. Clean.

**`create_evolution_router(domain, ledger_provider)`**
Not fully read — mounts variant/shadow evolution endpoints.

### DataOps Pattern — Reference SDK Copilot

**File:** `copilot_sdk/apps/dataops/backend/app/main.py`

Clean SDK usage:
1. `create_scoring_router("dataops", db_path=..., scorer_factory=lambda: _FreshScorerProxy(...))`
2. `create_conservation_router("dataops", state_provider=_conservation_state)`
3. `create_evolution_router("dataops", ledger_provider=_ledger_provider)`
4. Domain-specific routers: `ae_router` (AE variants), `context_router`

**`_conservation_state()`** reads from `fallback/alerts.json` — NOT from SQLite. Conservation metrics are from a JSON fixture, not live decision history. This means conservation for DataOps is not real-time.

**`_FixtureEvolutionLedger`** reads from `evolution_fixtures.json` — static fixture, not live graph.

**No AGE dependency.** No PostgreSQL. No graph client. Pure SQLite + JSON files.

### RL in SOC — Fully Implemented (Tests Confirm)

**File:** `gen-ai-roi-demo-v4-v50/backend/tests/test_rl_full_pipeline.py` (dated May 7-8)

All four RL feature flags confirmed implemented in `app.services.rl_engine`:

| Flag | Effect |
|---|---|
| `RL_REWARD_LEDGER_ENABLED` | RewardLedger.get_entries() accumulates binary_outcome + graded_reward |
| `RL_EXPLORATION_ENABLED` | ExplorationPolicy selects action via Thompson sampling, sets `d.explored=true` |
| `RL_ETA_MODULATION_ENABLED` | eta/eta_neg/eta_override increased above baseline during update |
| `RL_CHAIN_CREDIT_ENABLED` | CreditAssigner.assign_chain_credit() called after update |

**ExplorationPolicy:** `alphas[n_categories][n_actions]` — Beta distribution parameters. `alphas[c][a] += 1.0` on correct exploration. Thompson sampling via `betavariate(alpha, beta)`.

**Eta modulation confirmed:** `eta_seen[0][0] > 0.05` (eta was increased), restored after (`scorer.eta == 0.05`). RL doesn't permanently change learning rates.

**Chain credit confirmed:** `chain_calls[0]["source_decision_id"] == "D-RL"` — CreditAssigner receives the decision ID.

**TRIGGERED_EVOLUTION edges still written** even with RL: `any("TRIGGERED_EVOLUTION" in query for query in outcome_graph.queries)`. RL and W2 flywheel coexist.

### Framework Copy Problem — Resolution Status

| Repo | Framework source | Copy? |
|---|---|---|
| SOC backend | `app/framework/` (own copy) | ⚠️ Still has copy |
| S2P backend | `app/framework/` (own copy) | ⚠️ Still has copy |
| Trading | `copilot_sdk` directly | ✅ Resolved |
| Purchasing | `copilot_sdk` directly | ✅ Resolved |
| DataOps | `copilot_sdk` directly | ✅ Resolved |

The three-way copy problem documented in Parts 14 and 21 is resolved for new copilots. SOC and S2P still maintain their own framework copies — migration is planned but not done.

### What Still Needs Reading

| Item | Why |
|---|---|
| `copilot_sdk/scoring/presets.py` | PRESET_REGISTRY — what domains are registered? Does S2P preset exist? |
| `copilot_sdk/scoring/config.py` (DomainPreset, DomainShape) | Protocol for adding new domains |
| `copilot_sdk/backend/evolution_router.py` | Third router factory — not yet read |
| `app/services/rl_engine.py` | Full RL implementation in SOC — only seen via tests |
| DataOps context_router + ae_router | Domain-specific AE implementation |
| SOC backend additions (May 5-8, +232 tests) | What features were added in 3 days? |

---
*Document version: v18.0 · May 11, 2026 · Living document*
*Code + MAP v5.86 are authoritative over earlier doc versions where they conflict*

---

## Part 27 — RL Engine Full Analysis + Part 25 Gap Closure

**File:** `gen-ai-roi-demo-v4-v50/backend/app/services/rl_engine.py`

### RewardComputer

Domain-aware graded reward computation without side effects.

**SOC formula:**
```python
reward = ±1 × severity × campaign_multiplier
# severity: from get_severity_weights() — MITRE ATT&CK grounded, per category
# campaign_multiplier: 1.5 if campaign_id in context, else 1.0
# sign: +1 correct, -1 × penalty_ratio (20.0) incorrect
```

**S2P formula:**
```python
impact_weight = min(financial_impact / reference, 1.0)
reward = ±1 × impact_weight × cluster_multiplier
# reference: Hackett benchmark per category (e.g., 45.0 for price_variance)
# cluster_multiplier: 1.3 if exception_cluster in context, else 1.0
```

**Adaptive reference:** `_get_reference_reward()` uses rolling 400-decision sorted median as denominator for `reward_weight`. Same window as conservation q. Consistent design.

**`reward_weight`:** `max(0.1, min(abs(reward)/reference, 3.0))` — bounded multiplier on eta. Higher-impact decisions learn faster.

### ExplorationPolicy — Thompson Sampling

**Conservation-bounded rate formula (Gap 3 resolved):**
```python
rate = epsilon_base × min((headroom - 1.0) / (target_headroom - 1.0), 1.0)
# headroom ≤ 1.0 → rate = 0 (auto-pause)
# headroom = target_headroom → rate = epsilon_base (full exploration)
```

**Posterior:** Beta distribution per (category, action) pair. `alphas[C][A]`, `betas[C][A]`. Initialized at 1.0 (uniform Beta), reset to 2.0 (Jeffrey's prior). PosteriorStore persists across restarts.

**Proposal flow:** `propose(probabilities, category_index, headroom_ratio)` → `ExplorationDecision(explored=bool, explored_action=int|None)`.

### CreditAssigner — Chain Credit (Gap 2 resolved)

```
HALF_LIFE = 30 decisions
LOOKBACK = 100 decisions
CHAIN_DISCOUNT = 0.5
```

**Query:** TRIGGERED_EVOLUTION edges in AGE graph, filtered by category + action_index + decision_number range. AGE-compliant (`_S()` serialization). Falls back to empty list on graph unavailable.

**Credit formula:**
```python
weight[i] = exp(-log(2) × age[i] / HALF_LIFE)    # exponential decay
credit_budget = abs(reward) × CHAIN_DISCOUNT       # 50% of reward
chain_reward[i] = credit_budget × weight[i] / sum(weights)
```

**Factor attribution (Gap 1 resolved):** Finite differences (delta=0.01), NOT SHAP:
```python
p_plus = scorer.score(f_plus, category_index).probabilities[action_index]
p_minus = scorer.score(f_minus, category_index).probabilities[action_index]
attribution[index] = ((p_plus - p_minus) / (2 × delta)) × reward
```
Correct — milliseconds, not seconds.

### Global Singletons + Reset

Five singletons: `_reward_computer`, `_reward_ledger`, `_posterior_store`, `_exploration_policy`, `_credit_assigner`. Lazy initialization. `reset_rl_state()` clears all — registered with StateManager.

### Platform Router — New Discovery

`app/routers/platform.py` contains narrative/demo endpoints in `/api/platform/` namespace:

| Endpoint | Purpose |
|---|---|
| `/api/platform/rl-reward-demo` | Fixture JSON: 3 severity scenarios showing graded reward |
| `/api/platform/rl-exploration-demo` | Fixture JSON: epochs 1-3 showing active→reduced→paused |
| `/api/platform/cross-signals` | Fixture: XC-SOC-S2P-001/002/003 cross-copilot signals |
| `/api/platform/chain-credit-demo` | Fixture: chain credit visualization |
| `/api/platform/warm-start-evidence` | Fixture: warm start evidence |
| `/api/platform/domain-applicability` | Fixture: domain applicability matrix |

All are fixture-based (JSON files), fail-open (empty response if file missing), serve the SOC demo narrative.

### Cross-Signals (R-02 Infrastructure)

Three fixture signals: `XC-SOC-S2P-001/002/003`. Status: 2 active, 1 acknowledged. Source domain: SOC only (not yet bidirectional). Each signal has evidence list with decision_id, category, action, outcome, days_ago, user.

The evolution_router's `_has_pattern()` checks `source_copilot`, `source_rule`, `warm_start_prior` — the cross-domain pattern structure is designed for future live R-02 signals.

### Part 25 Design Gaps — All Resolved

| Gap | Status | How resolved |
|---|---|---|
| Gap 1 (SHAP too slow) | ✅ RESOLVED | finite differences implemented, SHAP deferred |
| Gap 2 (chain credit unspecified) | ✅ RESOLVED | HALF_LIFE=30, CHAIN_DISCOUNT=0.5, exponential decay |
| Gap 3 (exploration formula missing) | ✅ RESOLVED | headroom-ratio formula in ExplorationPolicy._compute_rate() |
| Gap 4 (S6 cross-domain overstated) | Still valid | fixture signals exist, live transfer not implemented |

### What Still Needs Reading

| Item | Why |
|---|---|
| `copilot_sdk/scoring/presets.py` location | PRESET_REGISTRY not found at expected path |
| `gae/evolution.py` | Used by evolution_router but not yet read |
| `app/routers/platform.py` | Full platform router — fixture paths, all 6 endpoints |
| `app/domains/soc/severity.py` | `get_severity_weights()` — MITRE ATT&CK grounding |
| `app/services/posterior_store.py` | PosteriorStore persistence for Thompson sampling |

---
*Document version: v18.0 · May 11, 2026 · Living document*
*Code + MAP v5.86 are authoritative over earlier doc versions where they conflict*

---

## Part 28 — Complete Domain Preset Analysis

**Files:** `copilot_sdk/scoring/presets/__init__.py`, `trading.py`, `purchasing.py`, `dataops.py`

### Complete Platform Tensor Shape Reference

| Copilot | Tensor | C | A | D | Values | penalty_ratio | Architecture |
|---|---|---|---|---|---|---|---|
| SOC | (6,4,6) | 6 | 4 | 6 | 144 | 20.0 | SOC backend + AGE |
| S2P | (5,5,7) | 5 | 5 | 7 | 175 | 5.0 | S2P backend + AGE (planned) |
| DataOps | (6,5,6) | 6 | 5 | 6 | 180 | 10.0 | SDK + SQLite |
| Purchasing | (5,4,6) | 5 | 4 | 6 | 120 | 3.0 | SDK + SQLite |
| Trading | (5,3,6) | 5 | 3 | 6 | 90 | 2.0 | SDK + SQLite |

**Universal constants across all domains:**
- `eta_confirm = 0.05` — GAE mathematical constant, not domain-tunable
- `eta_override = 0.01` — GAE mathematical constant
- `temperature = 0.1` — softmax τ, GAE mathematical constant

### Trading Preset — (5,3,6) = 90 values

**Categories:** equity_long, equity_short, crypto_spot, options, etf  
**Actions:** buy, hold, sell (A=3 — smallest action space on platform)  
**Factors:** conviction, research_depth, technical_signal, position_size, time_horizon, market_regime  
**penalty_ratio=2.0** — symmetric trading errors (missing a buy ≈ cost of a bad buy)

### Purchasing Preset — (5,4,6) = 120 values

**Categories:** protein, produce, dairy, dry_goods, beverages (food service purchasing)  
**Actions:** order_as_planned, order_more, order_less, skip  
**Factors:** expected_demand, day_of_week, **weather_forecast**, event_flag, historical_waste, supplier_lead_time  
**penalty_ratio=3.0** — food waste vs stockout asymmetry is relatively low

**Notable:** `weather_forecast` as a factor means Purchasing integrates live weather data via `get_weather_factor` from `copilot_sdk.scoring.verification.weather`. Only copilot with live external API factor integration in the SDK layer.

### DataOps Preset — (6,5,6) = 180 values

**Categories:** schema_change, volume_anomaly, quality_anomaly, freshness_violation, pipeline_failure, transform_drift  
**Actions:** auto_approve, investigate, escalate_to_owner, pause_downstream, refer_to_specialist (A=5 — largest action space on platform)  
**Factors:** impact_scope, source_reliability, recurrence_frequency, downstream_urgency, data_freshness, business_criticality  
**penalty_ratio=10.0** — missed data quality issues have significant downstream cascade impact

### PRESET_REGISTRY

```python
PRESET_REGISTRY = {
    "dataops": DataOpsPreset,
    "purchasing": PurchasingPreset,
    "trading": TradingPreset,
}
```

**S2P is NOT in PRESET_REGISTRY.** S2P uses the old SOC-adjacent architecture (separate backend repo, AGE graph, S2PDomainConfigV2). S2P will be migrated to the SDK pattern in P8-P9.5 per the MAP.

### Bootstrap Pattern

All presets follow the same defensive pattern:
```python
path = Path(__file__).parent / f"{domain}_bootstrap.json"
centroids = np.asarray(data["centroids"], dtype=np.float64)
if centroids.shape != expected_shape:
    raise ValueError(...)  # shape validation
```
Falls back to `np.full(expected_shape, 0.5)` (uniform neutral prior) if JSON missing or corrupt. Same pattern GAE uses for cold start.

### penalty_ratio Rationale

| Domain | ratio | Why |
|---|---|---|
| Trading | 2.0 | Symmetric — missing a buy ≈ making a bad buy. Exploration is safe. |
| Purchasing | 3.0 | Food waste vs stockout. Roughly 3:1 preference for over-ordering. |
| S2P | 5.0 | Missed leakage (false negative) 5× worse than false positive escalation. |
| DataOps | 10.0 | Missed data quality issue cascades downstream — 10× cost. |
| SOC | 20.0 | Missed threat (false negative) 20× worse than unnecessary escalation. |

This table is the correct reference for any discussion of asymmetric learning or reward shaping across the platform.

---
*Document version: v18.0 · May 11, 2026 · Living document*
*Code + MAP v5.86 are authoritative over earlier doc versions where they conflict*

---

## Part 29 — Final Confirmed Findings (May 11, 2026)

### PosteriorStore — More Resilient Than Feared

**File:** `gen-ai-roi-demo-v4-v50/backend/app/services/posterior_store.py`

Uses PostgreSQL at `localhost:5433/soc_copilot` — the SAME WSL2 instance as AGE. NOT file-based, NOT SQLite. Plain relational table: `rl_posteriors(category, action, alpha, beta, updated_epoch)`.

**Pattern:** Fully fail-open. Every method wraps in try/except and logs a warning on failure — never raises. `_ensure_table()` runs `CREATE TABLE IF NOT EXISTS` on first use.

**WSL2 dependency analysis:**
- WSL2 UP + PostgreSQL running → `load()` reads saved posteriors, `save()` persists updates. Exploration learning accumulates correctly across sessions.
- WSL2 DOWN → `load()` fails silently → in-memory priors (1.0, 1.0) for that session. Session's posterior updates are lost at session end. Data in DB is preserved — next session with WSL2 up reads the last good checkpoint.
- Mid-session WSL2 failure → `save()` fails silently → session's exploration learning lost but prior sessions intact.

**Conclusion:** More resilient than the "silent fallback" characterization suggested. The real risk is specifically mid-session PostgreSQL failure causing loss of that session's posterior updates — not permanent data loss. The WSL2 reboot procedure (port proxy re-creation) is the operational requirement.

**One genuine issue:** `_table_ready` flag is instance-level. Each new `PosteriorStore()` instance re-checks the table on first use via `_ensure_table()`. This is correct but means every server restart hits the DB on first RL operation. Not a bug, just worth knowing.

### Issue A Confirmed — SDK Conservation Gate Absent

Grep of entire `CompoundingScorer` for conservation/guarded/gate/pause/block/amber/red returned only two lines about `predicted_index` — completely unrelated. **Zero conservation enforcement in the SDK learning path.**

In SOC: `guarded_update()` checks D3 spike, D2 category freeze, conservation state before calling `ProfileScorer.update()`.
In SDK: `CompoundingScorer.learn()` calls `self._scorer.update()` directly with no gate.

The conservation router exists as a separate display endpoint and has no feedback loop into the learning path.

**Fix specification:**
```python
# In CompoundingScorer.learn(), before self._scorer.update():
from gae.calibration import conservation_status
counts = {
    "verified_count": self._store.count_verified(),
    "correct_count": self._store.count_correct(),
    "total_decisions": len(self._store.get_all_decisions()),
    "penalty_ratio": self._preset.penalty_ratio,
}
status = conservation_status(**counts)
if status.status in ("AMBER", "RED"):
    return LearnResult(..., outcome="conservation_blocked")
# then proceed with update
```

### S2P Drift — Complete Confirmed Catalogue

From `test_framework_drift.py` S2P_KNOWN_DRIFT table:

| File | Delta | Issue | Severity |
|---|---|---|---|
| composite_gate.py | Same size, different content | Wrong category threshold names — S2P auto-approve thresholds use SOC category names | **P1** |
| intervention_controls.py | -114 bytes | Conservation wiring absent in S2P | **P1** |
| audit.py | -5,118 bytes | Missing async, OutcomeEntry, epoch archive | **P1** |
| checkpoint.py | -747 bytes | PITR backup integration missing | P2 |
| provenance.py | -131 bytes | W2 provenance fields missing | P2 |
| shadow_mode.py | -18 bytes | Minor extension missing | P3 |
| similar_cases_base.py | -13 bytes | Minor | P3 |
| feedback_base.py | -3 bytes | Minor | P3 |
| decision_history.py | -6 bytes | Minor | P3 |
| agent.py | -1 byte | Trivial | P3 |

All listed as "Backport pending." The three P1 items mean S2P has incorrect auto-approve logic, missing conservation enforcement, and an incomplete audit chain.

### Complete Confirmed Issue Priority Table

| # | Issue | Confirmed | Severity | Fix effort |
|---|---|---|---|---|
| 1 | SDK copilots: no conservation gate on learning | ✅ | P1 | 1h per copilot |
| 2 | SDK copilots: conservation state reads JSON not SQLite | ✅ | P1 | 30m per copilot |
| 3 | RL tied to SOC only (not in SDK scoring path) | ✅ | P1 | 2 days |
| 4 | S2P composite_gate.py wrong category threshold names | ✅ | P1 | 1h |
| 5 | S2P intervention_controls.py missing conservation wiring | ✅ | P1 | 1h |
| 6 | S2P audit.py -5KB behind SOC (missing async/OutcomeEntry) | ✅ | P1 | 2h |
| 7 | _StoreProxy missing count_verified/count_correct | ✅ | P2 | 15m |
| 8 | PosteriorStore: WSL2 mid-session failure loses session posteriors | ✅ | P2 | Health check endpoint |
| 9 | Evolution ledger ignores queries (fixture-only for SDK) | ✅ | P2 | Design needed |
| 10 | S2P not in PRESET_REGISTRY | ✅ | P1 | Part of P8 |
| 11 | RL exploration vs referral VETO interaction | Unconfirmed | P1 if real | Read triage.py ~L460-530 |

### What Remains Unconfirmed

**Issue B (RL exploration vs referral VETO):** Lines 520-580 of triage.py showed Steps 8a and 8 — provenance and visualization, after the action is selected. The exploration decision and VETO interaction happen earlier. Need lines ~440-530 to see the VETO+exploration sequence.

```powershell
Get-Content "gen-ai-roi-demo-v4-v50\backend\app\routers\triage.py" | Select-Object -Skip 440 -First 100
```

---
*Document version: v18.0 · May 11, 2026 · Living document*
*Code + MAP v5.86 are authoritative over earlier doc versions where they conflict*

---

## §Platform Scale (May 11, 2026)

### Source Line Count — All Repos

| Repo | Total | Python | TypeScript | TSX |
|---|---|---|---|---|
| GAE (`graph-attention-engine-v50`) | 22,404 | 22,404 | — | — |
| SOC backend (`gen-ai-roi-demo-v4-v50/backend`) | 89,950 | 89,950 | — | — |
| SOC frontend (`gen-ai-roi-demo-v4-v50/frontend`) | 18,843 | — | 5,775 | 13,068 |
| S2P backend (`s2p-copilot/backend`) | 6,962 | 6,962 | — | — |
| ci-platform | 6,176 | 6,176 | — | — |
| copilot-sdk (core + Trading + Purchasing + DataOps) | 25,892 | 12,032 | 3,605 | 10,255 |
| **Grand total** | **170,227** | **137,524** | **9,380** | **23,323** |

Counted with node_modules, __pycache__, .git, and dist excluded. Test sources included (tests/ subdirectories are part of each repo's Python count).

### Context

The SOC backend alone at 90K lines is 53% of the entire Python codebase — which explains its disproportionate complexity, test count (1,572), and confirmed bug density. The copilot-sdk at 26K lines contains three full copilot backends plus the SDK core and their React frontends.

### Tests vs Source Split (estimated)

| Repo | Total tests | Approx test lines | Approx source lines |
|---|---|---|---|
| GAE | 1,237 | ~8,000 | ~14,400 |
| SOC backend | 1,572 + 280 E2E | ~35,000 | ~55,000 |
| SOC frontend | — | — | 18,843 |
| S2P backend | 141 | ~2,000 | ~5,000 |
| ci-platform | 188 | ~3,000 | ~3,200 |
| copilot-sdk | 127 + 117 E2E | ~8,000 | ~17,900 |
| **Total** | **~3,787** | **~56,000** | **~114,000** |

Roughly 33% of the Python codebase is test code — a healthy ratio.

### Issue B — Confirmed NOT a Bug (Final)

The RL exploration vs referral VETO interaction is correctly implemented in `triage.py`. Sequence:

1. Scorer fires → `selected_action = _scoring_result.action_name`
2. RL exploration fires → `selected_action = explored_action` (if LEARNING_ENABLED)
3. Referral VETO evaluates → overrides `selected_action = "refer_to_analyst"` if any rule fires
4. If VETO fires after exploration: `_rl_explored_but_referred = True`, `_rl_exploration_executed = False`

The audit chain correctly records exploration was proposed but not executed. No bypass is possible.

**Design note for future referral rule authors:** The `_alert_context` dict passed to the referral engine contains `'stage1_action': _scoring_result.action_name` — the original scorer recommendation, not the explored action. Rules that branch on `stage1_action` will see the scorer's output, not the explored action. This is intentional (referral rules are designed to be independent of exploration) but should be documented in the referral rules module.

---
*Document version: v18.0 · May 11, 2026 · Living document*
*Code + MAP v5.86 are authoritative over earlier doc versions where they conflict*

---

## Part 30 — MAP v5.92 Sync: GraphStore Architecture + Gap Status (May 13, 2026)

### GraphStore — New Primary Architecture (v0.5.7-sdk)

`GraphStore` is now a Protocol at `copilot_sdk/graph/protocol.py`. Rule #35: ALL platform data flows through GraphStore. DecisionStore is an internal implementation detail.

**Implementations:**
- `SQLiteGraphStore` (`copilot_sdk/graph/sqlite_store.py`) — primary for SDK copilots (Trading, Purchasing, DataOps)
- `InMemoryGraphStore` — for tests
- AGE-backed implementation — for SOC/ci-platform (per MAP "AGE-CENTROID-FIX" in v5.2.2-age)

**Protocol methods include:** `write_decision()`, `get_decision()`, `write_outcome()`, `save_centroids()`, `get_centroid_checkpoints()`, `get_verified_decisions()`, `get_all_decisions()`, `count_verified()`, `count_correct()`, `save_evolution_event()` (planned AE-SDK).

### Conservation Gate — Confirmed Active in CompoundingScorer (Gap 1.1 CLOSED)

```python
# scorer.py lines 199-201
conservation_pause = self._conservation_pause()
if conservation_pause is not None:
    return conservation_pause  # returns {"status": "paused", "reason": "conservation_red"}
```

`_conservation_pause()` at line 357 reads `_conservation_counts(self._graph_store)` — live verified/correct counts from GraphStore. Returns a paused LearnResult dict when conservation status is RED. Gap 1.1 is fully resolved.

### Live Conservation State — Confirmed (Gap 1.2 CLOSED)

Conservation metrics now flow from GraphStore.count_verified() and count_correct() — the same store that records every decision and outcome. No JSON fallback in the conservation path. Gap 1.2 is fully resolved.

### _StoreProxy Retired (Gap 7 CLOSED)

`_FreshScorerProxy.store` is now `SQLiteGraphStore` (a full GraphStore implementation) rather than the old thin proxy. All conservation router count methods are available. Gap 7 is resolved by elimination — the proxy was retired, not patched.

### RL in SDK (Gap 3.1 CLOSED)

CompoundingScorer constructor now accepts:
- `credit_assigner: Any | None` — credit assignment component
- `self._explorer.update(predicted_index, reward_raw)` — Thompson sampling update

RL-SDK is confirmed ✅ in MAP v5.92 as a completed dependency for AE-SDK (#1).

### Updated Platform Test Counts (MAP v5.92 Baseline)

| Repo | Tests | Tag |
|---|---|---|
| SDK root | 249 | v0.5.8-sdk |
| DataOps BE | 120 | v0.5.8-sdk |
| Trading BE | 26 | v0.5.8-sdk |
| Purchasing BE | 33 | v0.5.8-sdk |
| S2P BE | 280 | v0.5.7-s2p |
| ci-platform | 224 + 8 skip | v5.2.2-age |
| GAE | 1,237 | v5.75 |
| SOC BE | 1,572 | v5.75 |
| SOC E2E | 280 | v5.75 |
| **Total** | **~4,221** | **0 failures** |

### Revised Confirmed Issue Status

| # | Issue | Status |
|---|---|---|
| 1 | SDK: no conservation gate on learning | ✅ **CLOSED** v0.5.7-sdk |
| 2 | SDK: conservation state reads JSON not SQLite | ✅ **CLOSED** v0.5.7-sdk |
| 3 | RL tied to SOC only | ✅ **CLOSED** RL-SDK shipped |
| 4 | S2P composite_gate wrong category names | 🔴 **STILL OPEN** |
| 5 | S2P intervention_controls missing conservation wiring | 🔴 **STILL OPEN** |
| 6 | S2P audit.py -5KB behind SOC | 🔴 **STILL OPEN** |
| 7 | _StoreProxy missing count methods | ✅ **CLOSED** _StoreProxy retired |
| 8 | PosteriorStore: mid-session PostgreSQL failure | 🟡 **STILL OPEN** (SOC only) |
| 9 | Evolution ledger ignores queries | 🟡 **STILL OPEN** (AE-SDK #1 in queue) |
| 10 | S2P not in PRESET_REGISTRY | 🔴 **STILL OPEN** (S2P-PRESET #19 in queue) |

**4 closed, 3 open P1 (all S2P), 2 open P2, 1 open P1 queue item.**

The S2P framework drift (Gaps 4, 5, 6) remains the most important unresolved cluster. S2P shipped P10-P13 (factor computers, triage, RL, screen routers) but the framework backports (composite_gate category names, intervention_controls conservation wiring, audit.py async/OutcomeEntry) were not part of those sprints.

### Queue Context (MAP v5.92 Top 5)

The immediate critical path:
1. **AE-SDK (#1, 3-5d)** — closes Gap 9 (evolution ledger)
2. **GRAPH-TPC (#2, 2d)** — AGE wiring for Trading/Purchasing/DataOps
3. **SOC-VERIFY (#3, 0.5d)** — regression gate after SDK changes
4. **S2P-CT+PVG (#4, 4d)** — Control Tower + financial impact
5. **S2P-SUP (#5, 2d)** — Suppliers screen

S2P framework drift backports (Gaps 4-6) are not in the top 5 — they need to be explicitly added to a sprint or attached to S2P-CT+PVG (#4).

---
*Document version: v18.0 · May 13, 2026 · Living document*
*Code + MAP v5.92 are authoritative over earlier doc versions where they conflict*

---

## Part 31 — Block A: GraphStore Protocol & SDK Scorer (Complete Reference)

### A1. GraphStore Protocol — All 11 Methods

```python
@runtime_checkable
class GraphStore(Protocol):
    def write_decision(self, entity_id, category, action, confidence, factors, metadata=None) -> str
    def write_outcome(self, decision_id, actual_action, is_correct, metadata=None) -> None
    def get_decision(self, decision_id) -> dict | None
    def get_decisions(self, category=None, limit=400) -> list[dict]
    def get_verified_decisions(self) -> list[dict]
    def count_verified(self) -> int
    def count_correct(self) -> int
    def get_all_decisions(self) -> list[dict]
    def save_centroids(self, decision_id, category, centroids, metadata=None) -> None
    def get_centroid_checkpoints(self, limit=50) -> list[dict]
    def close(self) -> None
```

`@runtime_checkable` — isinstance() checks work at runtime. Any class with these methods satisfies the protocol without inheritance.

### A2. SQLiteGraphStore — Key Design Points

- **Open-call-close adapter**: Opens a fresh DecisionStore per call, closes in `finally`. Thread-safe by design.
- `write_decision()` serializes `entity_id` into the factors dict under key "entity_id" and "metadata" — this is how entity_id travels through the SQLite schema which has no dedicated column for it.
- `save_centroids(decision_id, category, centroids, metadata)` — NEW signature since v13. `decision_id` and `category` params are ignored by DecisionStore (passed for Protocol compliance and AGEGraphStore parity).
- `penalty_ratio` is NOT part of Protocol — it's set as a plain attribute on SQLiteGraphStore instances: `store.penalty_ratio = 10.0`. The conservation_router reads it via `getattr(store, "penalty_ratio", None)`.
- Extra methods beyond Protocol: NONE. Exactly Protocol-compliant.

### A3. CompoundingScorer — Current Constructor

```python
def __init__(self, preset, store, scorer,
             graph_store=None, reward_function=None,
             credit_assigner=None, exploration_policy=None)
```

All three RL components injectable. All default to None (RL is opt-in).

**`learn()` sequence:**
1. `graph_store.get_decision(decision_id)`
2. `_conservation_pause()` — q < theta_min → return paused dict
3. `scorer.eta = eta_confirm`, `eta_override = None if correct else eta_override * penalty_ratio`
4. `scorer.update()` — GAE centroid update
5. Restore `scorer.eta`, `scorer.eta_override`
6. `graph_store.write_outcome()` — record outcome
7. `graph_store.save_centroids()` — checkpoint
8. `_compute_rl_reward()` — calls `reward_function.compute()` if set
9. `explorer.update(predicted_index, reward_raw)` — Thompson sampling posterior
10. `credit.assign(reward_raw, factor_names)` — credit assignment

**`_conservation_pause()` formula:**
```python
theta_min = 23.53 / (penalty_ratio * verified)
if q < theta_min: return {"status": "paused", ...}
```
Note: uses `penalty_ratio` not `alpha` — a domain-adapted version of the conservation law where penalty_ratio scales the accuracy threshold.

**New in v0.5.8-sdk:**
- `get_phase() -> str` — "A" if verified < 10 or q < 0.5, else "B"
- `get_alpha() -> float` — verified accuracy ratio

### A4. Self-Computation Router — Closure Pattern

```python
def create_self_computation_router(graph_store: GraphStore) -> APIRouter:
    router = APIRouter(prefix="/api/self")
    def _gs() -> GraphStore:
        return graph_store  # closure captures per-app instance

    @router.get("/centroid-history")  # GET /api/self/centroid-history
    @router.get("/accuracy-by-category")  # GET /api/self/accuracy-by-category
    @router.get("/decisions")  # GET /api/self/decisions
    @router.get("/audit-trail")  # GET /api/self/audit-trail
```

No module-global state. Each `create_app()` creates its own `_graph_store(scoring_db)` and passes it to `mount_self_computation_router(app, graph_store)`. Complete isolation between copilot instances.

---

## Part 32 — Blocks B-G: AE Extraction, Routers, S2P, ci-platform, E2E, Demo

### B1. evolver.py — LEGACY UCB (NOT the AE-01→04 system)

`evolver.py` is the original simple UCB tracker — hardcoded variants (TRAVEL_CONTEXT_v1/v2, PHISHING_RESPONSE_v1/v2), in-memory PROMPT_STATS dict, 5% improvement threshold, 10 sample minimum. This is the LEGACY system.

`get_prompt_variant()` now tries the variant_registry first (AE-01 system) before falling back to ACTIVE_PROMPTS. This bridges legacy→new.

**For AE-SDK extraction**, the real implementation is:
- `variant_generator.py` — AE-01 graph-signal variant generation (7 rules, EvolutionRule Protocol)
- `promotion_gate.py` — AE-03 four-gate promotion (after AE-REVIEW P1 fix)
- `app/framework/evolution_ledger.py` — AE-04 durable event storage
- `app/services/shadow_runner.py` — AE-02 shadow comparison

### B4. Promotion Gate — Four-Gate Invariant (Post AE-REVIEW Fix)

After the AE-REVIEW P1 fix, `evaluate_promotion()` returns `continue` when `batch_count < MIN_SHADOW_BATCHES (=3)`. The four gates in order:
1. `total < MIN_SHADOW_SAMPLES (=50)` → continue
2. `win_rate < DELTA_MIN` → reject
3. `projected_q < Q_FLOOR` → reject
4. `conservation fails` → reject
5. `batch_std > SIGMA_MAX` → reject
6. **NEW: `batch_count < 3`** → continue (the fixed gate)
7. All pass → promote

`register_rollback_handler()` attaches to SOC's ConservationStateMachine AMBER/RED transitions. Note: GAE has no unregister path (P3 from AE-REVIEW).

### C1. DataOps Router Stack (Complete)

```python
create_app(db_path):
  scoring_db = str(db_path or DEFAULT_DB_PATH)
  
  # 1. Scoring: POST /api/score, /api/learn, GET /api/fingerprint, /api/trajectory, /api/health, /api/history
  create_scoring_router("dataops", db_path=scoring_db, scorer_factory=lambda: _FreshScorerProxy(scoring_db))
  
  # 2. Conservation: GET /api/conservation/status, POST /api/conservation/what-if
  create_conservation_router("dataops", state_provider=lambda: _graph_store(scoring_db))
  
  # 3. Evolution: GET /api/evolution/variants, /api/evolution/patterns
  create_evolution_router("dataops", ledger_provider=_ledger_provider)
  
  # 4. Self-computation: GET /api/self/centroid-history, /accuracy-by-category, /decisions, /audit-trail
  mount_self_computation_router(app, _graph_store(scoring_db))
  
  # 5. Context: /api/context/* — DataOps-specific context router
  context_router prefix="/api/context"
  
  # 6. AE: /api/ae/* — DataOps-specific AE router (fixture-based)
  ae_router prefix="/api/ae"
  
  # 7. Health: GET /health — simple status check
```

Trading differs: NO evolution router, NO ae_router.
Purchasing has: evolution router (fixture-based), NO ae_router.
All three: conservation state_provider = `lambda: _graph_store(scoring_db)` → SQLiteGraphStore with penalty_ratio set.

### C2. _FreshScorerProxy.get_phase() and get_alpha()

All three copilots (Trading, Purchasing, DataOps) implement `get_phase()` and `get_alpha()` on `_FreshScorerProxy`, delegating to `CompoundingScorer.get_phase()` and `.get_alpha()`. The scoring_router exposes these via `GET /api/health`.

### C3. conservation_router._state_counts() — How penalty_ratio is Resolved

```python
# Priority order for penalty_ratio:
getattr(store, "penalty_ratio", None)     # store = SQLiteGraphStore instance
or getattr(state, "penalty_ratio", None)  # state = the passed-in object
or getattr(preset, "penalty_ratio", None) # preset = _preset on CompoundingScorer
```

In DataOps: `_graph_store(scoring_db)` sets `store.penalty_ratio = 10.0` directly. The conservation router reads it via the first getattr.

### D2. S2P composite_gate.py — Gap 4 CLOSED

S2P's composite_gate.py uses S2P category names:
```python
CATEGORY_CONFIDENCE_THRESHOLDS = {
    "price_variance": 0.85,
    "quantity_mismatch": 0.82,
    "duplicate_risk": 0.90,
    "contract_gap": 0.80,
    "format_compliance": 0.88,
}
```
The drift test's "same size, different content" flag was EXPECTED behavior — composite_gate SHOULD differ between SOC and S2P. Gap 4 was NOT a real bug in the S2P code. The drift test entry should be moved from KNOWN_DRIFT (with "Backport pending") to an explicit note that this difference is intentional.

### D3. S2P Dual-Scorer Architecture (Important for AE-SDK)

S2P has two concurrent scorer patterns:
1. **CompoundingScorer** at `app.state.scorer` — used by `POST /api/s2p/score` and `POST /api/learn` via `_sdk_scorer(http_request)`. This is the SDK path.
2. **ProfileScorer singleton** at `app/domains/s2p/scorer.py` — used by `GET /api/s2p/iks` via `get_s2p_iks()` and `score_event()`. This is the legacy path.

S2P-PRESET (#19) will unify these. Until then, IKS shown in S2P UI comes from the legacy ProfileScorer, not the CompoundingScorer.

### D4. S2P Decision-Invoice Index (Item #20 context)

`_decision_invoice_index(http_request)` stores in `app.state.s2p_decision_invoice_index` — an in-memory dict (not persisted). Comment: "Temporary S2P invoice index until GraphStore supports update/link metadata." Item #20 (S2P-GS-LINK) replaces this.

### E1. AGEClient Key Facts

- `_S(value)` → `serialize_for_age()` handles bool (true/false lowercase), int (str), float (str), string (single-quote escaped)
- `_sync_execute()`: Python-level `$param` substitution (replace with serialized values), extracts column names from query, wraps in `SELECT * FROM cypher('graph', $$ ... $$) AS (col agtype)`, 3 retries on "Entity failed to be updated"
- No MERGE — all writes use MATCH→SET→RETURN or MATCH→CREATE two-step
- `$param` dict substitution happens in Python before SQL generation — not AGE-level params

### E3. AGEGraphStore — Extra Methods Beyond Protocol

`query_context(entity_id, hops=2)` — graph traversal `p = (e)-[*1..hops]-(n)`, returns up to 100 nodes
`query_similar(decision_id, limit=5)` — finds Decisions with same category

These are used by S2P's `_resolve_graph_context()` (s2p.py). The Protocol doesn't require them — they're AGE-specific capabilities.

`save_centroids()` creates `CentroidCheckpoint` nodes in AGE linked to Decision via `[:HAS_CENTROID_CHECKPOINT]`. Falls back to standalone CREATE if Decision not found (AGE-CENTROID-FIX from v5.2.2-age was exactly this fix).

### E4. TwoPhaseStrategy

Lives at `ci_platform/strategy/two_phase_strategy.py`. Simple:
```python
class TwoPhaseStrategy:
    def __init__(self, graph_store: GraphStoreCounts, min_verified=10, q_threshold=0.5)
    def get_phase(self) -> "A" or "B"
    def get_status(self) -> {phase, verified, correct, q, min_verified, q_threshold}
```

CompoundingScorer inlines the same logic in `get_phase()` directly (no TwoPhaseStrategy dependency). TwoPhaseStrategy is used by ci-platform consumers.

### F — E2E Pattern (DataOps flows.spec.ts)

**5 tabs:** Dashboard, Triage, Insight, Evidence, Curve

**Navigation:**
```typescript
await clickTab(page, "Insight")  // tab name string
await expectAnyText(page, [/regex1/i, /regex2/i])  // at least one must match
await openFirstAlert(page)  // returns bool — skip test if false
```

**Score→Learn→Verify pattern:**
```typescript
const scoreResponse = page.waitForResponse(r => r.url().includes("/api/score") && r.request().method() === "POST")
await page.getByRole("button", { name: "Investigate" }).click()
await scoreResponse
const learnResponse = page.waitForResponse(r => r.url().includes("/api/learn") && r.request().method() === "POST" && r.ok())
await page.getByRole("button", { name: "Confirm" }).click()
await learnResponse
await expectAnyText(page, [/system learned/i, /Reward/i, /IKS delta/i])
```

**SC feature mapping:**
| SC | Tab | Content |
|---|---|---|
| SC-11 | Curve | Centroid History |
| SC-12 | Dashboard | Accuracy Alerts |
| SC-13 | Evidence | Rule Genealogy |
| SC-14 | Insight | Decision Explorer |
| SC-15 | Evidence | Rule Lifecycle |
| SC-16 | Evidence | Audit Trail |

### G1. demo.py — Port Map and Startup

| Copilot | Backend | Frontend |
|---|---|---|
| Trading | 8010 | 5174 |
| Purchasing | 8020 | 5175 |
| DataOps | 8030 | 5176 |
| S2P | 8002 | 5177 |

SOC (8001/5173) is **NOT** in demo.py — started separately.

Startup sequence: kill_port → uvicorn start → wait_for_health (30s) → optionally preseed → vite start → wait_for_frontend (15s) → open Edge InPrivate (multi-tab single call).

`--graph` flag: sets GRAPH_DSN, runs `ci-platform/scripts/seed_dataops_graph.py --force`.

### G2. preseed_all_copilots.py — Seeding Pattern

Three domains only: Trading (8010), Purchasing (8020), DataOps (8030). S2P NOT preseeded.

Pattern per entry: `POST /api/score` → get decision_id → `POST /api/learn` → `POST /{metadata_path}`.

Idempotent: checks `GET /api/trajectory` → if `decisions_total > 0` and not `--force`, skips. 

Factor extraction: tries `entry.factors[name]` then `entry[field_map[name]]` — handles both nested and flat factor formats.

### Revised Gap Status After This Session

| Gap | Previous | Now |
|---|---|---|
| 4 (S2P composite_gate wrong categories) | OPEN | ✅ CLOSED — S2P has correct S2P categories. Drift test entry was misleading. |

**Current open gaps (reduced to 2 P1, 2 P2):**
- S2P audit.py -5KB behind SOC (P1)
- S2P intervention_controls.py missing conservation wiring (P1)
- PosteriorStore mid-session failure (P2)
- S2P-PRESET not in registry (P1 — item #19 in queue)

---
*Document version: v18.0 · May 13, 2026 · Living document*
*Code + MAP v5.92 are authoritative over earlier doc versions where they conflict*

---

## Part 33 — 10-Scan Architectural Review (May 13, 2026)

### SCAN 1 — Store Bypass: CLEAN

`scorer.py:19` imports DecisionStore — this is the internal implementation, not a bypass. CompoundingScorer holds `_store: DecisionStore` for `load_latest_centroids()` and the legacy `store` property. Zero `sqlite3.connect` in apps. Zero DecisionStore/sqlite3 in S2P. Rule #35 (all data through GraphStore) is respected at the API boundary.

### SCAN 2 — Evolution Isolation: CLEAN

`copilot_sdk/evolution/` imports zero SOC vocabulary, zero domain-specific terms. All three apps use `create_evolution_router` correctly. No wrong-direction dependencies.

### SCAN 3 — Conservation Formula: MATERIAL INCONSISTENCY

Two incompatible formulas in production:

| Location | Formula | Parameters |
|---|---|---|
| SOC `config.py:812` | `23.53 / (alpha * V)` | alpha=oversight fraction [0-1], V=total decisions |
| SOC `promotion_gate.py:238` | `23.53 / (alpha * volume)` | same |
| SDK `scorer.py:390, 492` | `23.53 / (penalty_ratio * verified)` | penalty_ratio=2-20, verified=count |
| S2P `s2p_performance.py:91` | `23.53 / (PENALTY_RATIO * new_verified)` | same as SDK |

**Impact:** At verified=200, SOC (alpha=0.8): theta_min=0.147. SDK Trading (penalty_ratio=2): theta_min=0.059. SDK DataOps (penalty_ratio=10): theta_min=0.012. SDK formula is 3-12× more permissive than SOC.

**Root cause:** penalty_ratio is an error cost asymmetry parameter (belongs in reward shaping). alpha is a human oversight fraction (belongs in conservation). They are different concepts that happened to live in the denominator of different formulas.

**Also:** `scorer.py:492` has a SECOND theta_min computation — need to confirm what this second location computes (conservation status reporter, or duplicate of the pause gate?).

**Fix:** SDK should use `verified / total_decisions` as its alpha proxy (all verified decisions / total decisions). Or: document explicitly that SDK uses penalty_ratio-scaled conservation as a deliberate domain adaptation. Either way, the formula must be explicitly stated and consistent with the claims documentation.

### SCAN 4 — GraphContract Alignment: INCONCLUSIVE

PowerShell syntax error prevented reading contract files directly. App code shows Trading and DataOps using `pipeline_failure`, `dataset`, `position_size` etc. as data keys and category names — not as AGE graph node labels. No queries to Instrument, Portfolio, TradeSignal, Pipeline, Dataset, QualityRule node types appear in app code.

**Assessment:** GRAPH-TPC contracts are likely forward-looking specs for when AGE wiring lands (per MAP item #2). The copilots currently use SQLiteGraphStore with no AGE dependency. The contracts define the target schema, not the current implementation.

**Follow-up needed:** Read the three graph_contract.py files directly.

### SCAN 5 — S2P Framework Drift: MAJOR DIVERGENCE

New S2P routers (CT, PVG, Suppliers) import zero from `app.framework` — clean.

**Drift size changes (current vs previously documented):**

| File | Previous S2P gap | Current S2P vs SOC | Change |
|---|---|---|---|
| `intervention_controls.py` | S2P -114 bytes | **S2P +5,513 bytes** | S2P grew 5,627 bytes past SOC |
| `audit.py` | S2P -5,118 bytes | S2P -1,805 bytes | Backport partially landed |
| `feedback_base.py` | S2P -3 bytes | S2P -475 bytes | SOC grew, S2P didn't follow |
| `composite_gate.py` | "different content" | diff=-3 bytes | Now essentially identical |
| `checkpoint.py` | S2P -747 bytes | S2P -747 bytes | Unchanged |
| `provenance.py` | S2P -131 bytes | S2P -134 bytes | Unchanged |

**`intervention_controls.py` at +5,513 bytes is the key change.** S2P has added significant new intervention control logic in S2P-CT+PVG+SUP that doesn't exist in SOC. This file has intentionally diverged — it's now a S2P extension, not a copy of SOC's file.

The drift test will fail with this file unless `S2P_KNOWN_DRIFT` is updated with an entry like: "intervention_controls.py: S2P extends SOC with S2P-specific intervention controls. S2P is intentionally larger. Not a backport candidate."

### SCAN 6 — Frontend API Contract: FOLLOW-UP NEEDED

Confirmed from frontend api.ts — calls that need backend route verification:

| Frontend call | Status |
|---|---|
| `/api/s2p/preview/*` | ✅ s2p_preview.py |
| `/api/s2p/score`, `/api/s2p/outcome` | ✅ s2p.py |
| `/api/learn` | ✅ s2p.py learn_router |
| `/api/fingerprint`, `/api/trajectory`, `/api/conservation/status` | ✅ SDK routers |
| `/api/s2p/control-tower/*` | ✅ s2p_control_tower.py |
| `/api/s2p/pvg/*` | ✅ s2p_pvg.py |
| `/api/s2p/suppliers`, `/suppliers/{id}/profile` | ✅ s2p_suppliers.py |
| `/api/s2p/insight/*` (fingerprint, similar, cross-graph, process-signals) | ❓ Need grep |
| `/api/s2p/evidence/*` (audit-trail, rules, compliance) | ❓ Need grep |
| `/api/s2p/performance/*` (trajectory, what-if, summary) | ❓ Need grep |
| `/api/s2p/suppliers/{id}/heatmap`, `/clustering` | ❓ Need grep |

Run to close:
```powershell
Get-ChildItem "$S2P\backend\app\routers" -Filter "*.py" | Select-String -Pattern '"\/api\/s2p\/' | ForEach-Object { "$($_.Path.Split('\')[-1]):$($_.LineNumber): $($_.Line.Trim())" }
```

### SCAN 7 — Duplicate Helpers: CONFIRMED DEBT

Three separate `_find_invoice()` implementations in S2P routers:

| File | Signature |
|---|---|
| `s2p_control_tower.py:63` | `(invoice_id: str) -> dict | None` |
| `s2p_insight.py:39` | `(invoice_id: str) -> dict | None` |
| `s2p.py:37` | `(event_id_or_invoice_id: str) -> dict | None` — different! |

Two separate `_load_json()` implementations (`s2p_insight.py:31`, `s2p_pvg.py:36`). `s2p_data_helpers.py` exists with centralized `load_json()` but the new routers don't use it.

**Risk:** Bug fixes to invoice loading logic must be applied in 3 places. The `s2p.py` signature difference (handles both event_id and invoice_id) means the implementations diverge in behavior.

**Fix:** Consolidate into `s2p_data_helpers.py`. Import from there in all routers. ~30 minutes.

### SCAN 8 — Module-Global Mutable State: CLEAN

Zero mutable module globals in SDK evolution module. Zero in new S2P routers. Clean.

### SCAN 9 — Test Coverage: FULL

| Router | Routes | Test file | Size |
|---|---|---|---|
| s2p_control_tower | 3 | test_s2p_control_tower.py | 138L |
| s2p_pvg | 4 | test_s2p_pvg.py | 142L |
| s2p_suppliers | 5 | test_s2p_suppliers.py | 127L |
| SDK evolution_router | 3 | test_evolution_router.py | 154L |

All endpoints have test coverage.

### SCAN 10 — Cross-Repo Imports: CLEAN

S2P `from copilot_sdk.backend import create_conservation_router` — correct and intentional. Zero cross-app imports between Trading/Purchasing/DataOps.

### Summary — Priority of Findings

| Finding | Severity | Action |
|---|---|---|
| Conservation formula inconsistency (SCAN 3) | P1 | Decide: fix SDK formula to use verified/total as alpha proxy, OR document as intentional domain adaptation |
| S2P intervention_controls.py diverged (SCAN 5) | P2 | Update S2P_KNOWN_DRIFT table — mark as intentional extension |
| S2P audit.py still -1,805 bytes behind SOC (SCAN 5) | P2 | Finish backport |
| SCAN 6 routes unconfirmed (insight/evidence/performance) | P1 gate | Run follow-up grep before SOC-VERIFY |
| Duplicate _find_invoice() across 3 S2P routers (SCAN 7) | P3 | Consolidate into s2p_data_helpers.py |
| graph_contract.py not read (SCAN 4) | Info | Read files directly |

---
*Document version: v18.0 · May 13, 2026 · Living document*
*Code + MAP v5.92 are authoritative over earlier doc versions where they conflict*

---

## Part 34 — 5-Batch Expansive Architectural Scan (May 15, 2026)

### BATCH A — Learning Path Integrity: CONFIRMED SOUND

**A1:** All `.update()` call sites traced. The only production call to `scorer.update()` goes through SOC's `guarded_update()` at `gae_state.py:788`. SDK copilots call `scorer.learn()` which internally gates via `_conservation_pause()`. No raw unguarded `update()` calls exist in production code. Learning path is correctly gated across all five copilots.

**A2 — MAJOR CORRECTION to SCAN 3:**

`_conservation_pause()` (the actual gate that blocks learning) uses:
```python
theta_min = compute_theta_min(override_rate, verified)
```
This calls `gae.calibration.compute_theta_min` — the canonical GAE formula with `override_rate` as alpha. **The learning gate is correct.**

The `23.53 / (penalty_ratio * verified)` formula at scorer.py:390,492 is in a separate `_conservation_status()` display method only. Formula inconsistency exists in display metrics but NOT in enforcement. The SCAN 3 finding is downgraded: P2 cosmetic (display mismatch) not P1 enforcement bug. Item #6 in MAP queue (SOC-CONSERVATION-FORMULA) should fix the display formula to match the gate formula.

**A3:** Only ONE `.learn()` call across all production code: `s2p.py:216`. All other learning goes through `CompoundingScorer.learn()` internally (gated) or SOC's `guarded_update()` (gated). Confirmed sound.

**A4:** AE-EVOLUTION-ADV new classes confirmed in `copilot_sdk/evolution/`:
- `autonomous_promotion.py` — AutonomousPromotionGate
- `context_selector.py` — ContextAwareSelector  
- `credit_attribution.py` — StepCreditAssigner

SDK evolution module is now a proper package under `copilot_sdk/evolution/`.

### BATCH B — Silent Failures

**B2 — scorer.py:48 returns float("inf") on error:**
On TypeError/ValueError in factor vector validation, returns `float("inf")`. Infinity propagating into centroid distance calculations → L2 distances become infinite → softmax receives inf → `exp(inf) = inf` → NaN probabilities. The scorer would return undefined action probabilities silently. This should return a safe bounded value (0.5 or raise) instead.

**B2 — evolution_router.py:100,118 silently return []:**
Graph query failures on AE variant/history endpoints return empty lists — no error surfaced. During demo: AE tab shows "no variants" rather than connection error. Acceptable for demo resilience, hides operational problems.

**B3 — guarded_update correctly blocks:**
`gae_state.py:788` is the sole production path for SOC centroid updates. All guards (D3 spike, D2 freeze, conservation) are applied before reaching line 788. Confirmed sound.

### BATCH C — Fixture vs Live Data Map

**DataOps AE tab — entirely fixture-based:**
`ae_router.py` reads `evolution_fixtures.json` at lines 83, 290, 352 — three separate disk reads per request, no caching. Lines 378, 420, 436 return `"source": "fixture"` explicitly. After AE-SDK ships real evolution infrastructure, ae_router.py must be replaced.

**F17-DISCOVERY — live computation:**
`DiscoveryEngine` computes from registered copilot states passed in. No fixture files. The 4 patterns generate alerts from real centroid data, conservation alignment, transfer opportunities, anomaly co-occurrence. Confirmed live.

**S2P production-facing tabs — partial fixture:**
- Control Tower: `synthetic_invoices.json` (fixture)
- PVG (Process Variant Graph): `synthetic_invoices.json` (fixture, labeled as such)
- Evidence: explicitly `"source": "fixture"` at line 117
- Suppliers: `s2p_demo_suppliers.json` (fixture)
- Scoring/learning path: live (CompoundingScorer + GraphStore)

For Loom demo: score/learn/conservation are live. The enrichment/insight/audit data is fixture-sourced and must be clearly narrated as "demonstration data."

### BATCH D — State Management Findings

**D3 — RL ENGINE NOT REGISTERED WITH STATE_MANAGER (P2 Demo):**

From SOC `main.py`:
```python
from app.services import rl_engine
store = getattr(rl_engine, "_posterior_store", None)  # only reads, doesn't register
```

`reset_rl_state()` is NOT called on demo reset. After "Reset Demo":
- `RewardLedger` entries from previous session persist (cumulative reward misleading)
- `ExplorationPolicy` Beta priors from previous decisions remain (exploration rate incorrect)
- `RewardComputer` rolling 400-decision reference history persists (reward weights incorrect)

Demo shows "learning from nothing" but RL carries prior state. Fix: add `state_manager.register("rl_engine", reset_rl_state)` to main.py startup.

**D1 — platform.py 6 caches NOT registered with state_manager:**

`_SIGNAL_CACHE`, `_DOMAIN_TABLE_CACHE`, `_WARM_START_CACHE`, `_CHAIN_CREDIT_CACHE`, `_RL_REWARD_CACHE`, `_RL_EXPLORATION_CACHE` — all module-level globals written via `global` keyword. After demo reset, platform narrative endpoints return pre-reset cached data until next cache expiry. Fix: register reset functions for each cache with state_manager.

**D1 — soc.py baseline scorer caches NOT registered:**

`_BASELINE_SCORER`, `_BASELINE_SCORER_SOURCE`, `_BOOTSTRAP_CENTROIDS_CACHE` in soc.py — used for model swap trial. Not registered with state_manager. After reset, model swap comparison uses stale pre-reset baseline.

**D4 — All asyncio.Lock instances are module-level:** Correct for single-worker FastAPI async model. Clean.

### BATCH E — Protocol Compliance & GraphStore Ecosystem

**E1 — Six GraphStore implementations:**

| Implementation | Location | Status |
|---|---|---|
| `GraphStore` (Protocol) | `copilot_sdk/graph/protocol.py` | Definition |
| `SQLiteGraphStore` | `copilot_sdk/graph/sqlite_store.py` | Primary SDK ✅ |
| `InMemoryGraphStore` | `copilot_sdk/graph/memory_store.py` | Tests ✅ |
| `AGEGraphStore` | `ci_platform/graph/age_graph_store.py` | SOC/ci-platform ✅ |
| **`AGEGraphStoreAdapter`** | `ci_platform/graph/age_sdk_adapter.py` | **Unknown purpose** |
| **`_S2PGraphStore(InMemoryGraphStore)`** | `s2p-copilot/backend/app/main.py` | **Design smell** |

`_S2PGraphStore` is a private class defined inline in S2P's main.py extending InMemoryGraphStore. This is architecturally wrong — S2P should use `SQLiteGraphStore` directly (or `AGEGraphStore` if it ever gets AGE wiring). Having a private subclass inside main.py makes it untestable and invisible to the framework.

`AGEGraphStoreAdapter` in `ci_platform/graph/age_sdk_adapter.py` — purpose unknown. Likely wraps AGEGraphStore to conform to the SDK Protocol (needed because AGEGraphStore predates the Protocol definition). Needs read.

**E4 — save_evolution_event() gap for SQLite:**

`AGEGraphStore` has `save_evolution_event()`. `SQLiteGraphStore` protocol does NOT include this method. SDK copilots (Trading, Purchasing, DataOps) using SQLiteGraphStore cannot persistently store AE evolution events. For AE-SDK (#1) to work with SQLite backends, either:
1. Add `save_evolution_event()` to the GraphStore Protocol and implement in SQLiteGraphStore
2. Or accept that SDK copilots use an in-memory-only evolution ledger (acceptable for MVP)

This must be resolved before AE-SDK GAP-H1 (#1) prompt is sent.

**E2 — SOC endpoint surface area: ~180 routes across 22 files:**

| File | Routes |
|---|---|
| soc.py | 50 |
| framework_router.py | 34 |
| metrics.py | 13 |
| triage.py | 11 |
| evolution.py | 11 |
| gae.py | 7 |
| admin.py, auth.py | 6, 5 |
| governance_router.py, platform.py | 5, 6 |
| Other (11 files) | ~36 |

SOC-VERIFY (#3) must regression-test against this surface area. The 291 SOC E2E tests cover the primary happy paths but 180 routes likely have uncovered edge cases.

**E5 — Forbidden SET n = {} pattern: CLEAN.** Guard in `age_client.py:54` catches this pattern and rejects it. No violations in production Cypher queries.

### Consolidated New Issue List (Additions to v19.0 gap table)

| # | Finding | Severity | Fix |
|---|---|---|---|
| N1 | RL engine not registered with state_manager — state persists across demo resets | P2 demo | 5 min: add register() call in main.py |
| N2 | platform.py 6 caches not registered with state_manager — stale post-reset | P2 demo | 1h: register reset functions |
| N3 | soc.py baseline scorer caches not registered — stale model swap baseline after reset | P2 demo | 30 min: register reset |
| N4 | scorer.py:48 returns float("inf") — cascades to NaN probabilities | P1 | 5 min: return 0.5 or raise ValueError |
| N5 | _S2PGraphStore private class in s2p main.py — should use SQLiteGraphStore | P2 | Replace with SQLiteGraphStore in S2P-PRESET (#19) |
| N6 | AGEGraphStoreAdapter in ci_platform — unknown purpose, unreviewed | Info | Read age_sdk_adapter.py |
| N7 | save_evolution_event() not in Protocol/SQLiteGraphStore — blocks AE on SQLite | P1 for AE-SDK | Add to Protocol + SQLiteGraphStore before GAP-H1 |
| N8 | DataOps ae_router reads evolution_fixtures.json 3x per request, no cache | P3 | Add module-level cache with reset |
| N9 | SCAN 3 DOWNGRADED: formula mismatch is display-only, not enforcement | — | SOC-CONSERVATION-FORMULA (#6) fixes display |

---
*Document version: v36.0 · May 15, 2026 · Living document*
*Code + MAP v5.96 are authoritative over earlier doc versions where they conflict*

---

## Part 35 — Architecture Fitness Checks v3.0 Results (May 25, 2026)

**Source:** architecture_fitness_checks_v3.md · MAP v5.121

### PASS — Clean Checks (no violations)

| Check | Result |
|---|---|
| 1.1 SOC→SDK boundary | ✅ Clean |
| 1.2 S2P→SOC boundary | ✅ Clean |
| 1.3 SDK→apps boundary | ✅ Clean (comment only, not import) |
| 1.4 ci-platform isolation | ✅ Clean |
| 1.5 GAE isolation | ✅ Clean |
| 1.6 Cross-app SDK imports | ✅ Clean |
| 1.7 SDK apps→private SDK | ✅ Clean |
| 2.1 No raw sqlite3.connect | ✅ Clean |
| 2.5 _StoreProxy gone | ✅ Confirmed eliminated |
| 4.2 AE-03 thresholds | ✅ DELTA_MIN=0.05, Q_FLOOR=0.80, SIGMA_MAX=0.10, MIN_SHADOW_SAMPLES=50, MIN_SHADOW_BATCHES=3 |
| 4.3 P16 separation | ✅ evolver.py has no ProfileScorer/centroid refs |
| 4.5 SDK evolution thresholds | ✅ Match SOC exactly |
| 14.8 CopilotShell in all apps | ✅ All 4 apps import and use CopilotShell |
| 15.9 No local SDK copies | ✅ All apps import from copilot_sdk package |
| 19.1 TODO/FIXME/HACK | ✅ Zero — completely clean |
| 19.5 Bare except | ✅ Zero bare except patterns |

### VIOLATIONS AND FINDINGS

**CHECK-2.3 FAIL — DataOps AGEClient direct import (Rule #29)**
```
apps/dataops/backend/app/graph_queries.py:43:
    from ci_platform.graph.age_client import AGEClient
```
Rule #29: copilot code never imports AGEClient directly. DataOps uses AGEClient in `graph_queries.py` for graph context queries — bypassing the GraphStore abstraction. Fix: route through AGEGraphStore or AGEGraphStoreAdapter.

**CHECK-2.4 — Four GraphStore implementations (expected three)**
Found: InMemoryGraphStore, SQLiteGraphStore, AGEGraphStore, **AGEGraphStoreAdapter**. The fitness check expects exactly 3. AGEGraphStoreAdapter remains undocumented. Read `ci_platform/graph/age_sdk_adapter.py` to understand its purpose before the next Codex round that touches GraphStore.

**CHECK-2.7 — EvolutionStore not yet in protocol.py**
`copilot_sdk/evolution/protocol.py` exists (1,938 bytes) but defines some other protocol, not EvolutionStore. Check marked "skip if not yet implemented." Acceptable gap — add to queue.

**CHECK-2.2 — JSON writes in learning_state.py (both copies)**
Both `copilot_sdk/framework/learning_state.py:155` and `app/framework/learning_state.py:155` write JSON checkpoints. Intentional persistence for learning state — but confirms S2P has its own copy of framework/learning_state.py (drift continues).

**CHECK-3.3 — Penalty ratios (CORRECTED from previous docs)**

| Domain | Canonical | Actual | Status |
|---|---|---|---|
| Trading | 3.0 | 3.0 | ✅ |
| Purchasing | 3.0 | 3.0 | ✅ |
| DataOps | 10.0 | 10.0 | ✅ |
| S2P | 5.0 | 5.0 | ✅ |
| SOC | 20.0 | (not checked) | — |

**Trading was 2.0 in earlier insights doc — now 3.0. Corrected.**

**CHECK-3.5 — TENSOR SHAPES (MAJOR UPDATE)**

| Domain | Previous (v20) | Current (v21) | Changed |
|---|---|---|---|
| Trading | (5, 3, 6) | **(5, 4, 7)** | n_actions +1, n_factors +1 |
| Purchasing | (5, 4, 6) | **(5, 4, 7)** | n_factors +1 |
| DataOps | (6, 5, 6) | (6, 5, 6) | Unchanged |
| S2P | (5, 5, 7) | (5, 5, 7) | Unchanged |
| SOC | (6, 4, 6) | (6, 4, 6) | Unchanged |

Trading gained both a new action (now 4: buy/hold/sell + one new) and a new factor (now 7). Every centroid bootstrap file for Trading and Purchasing must be regenerated.

**CHECK-14.7 — Trading has 6 screens (expected 5)**
Trading has one extra screen beyond the 5 in the design spec. Either the design spec is stale or the extra screen is undocumented. Needs reconciliation before Loom.

**CHECK-15.8 — S2P uses InMemoryGraphStore (P1 persistence)**
```
s2p main.py: from copilot_sdk.graph.memory_store import InMemoryGraphStore
             graph_store=InMemoryGraphStore(decision_id_prefix="S2P-")
```
S2P learning decisions are not persisted to disk. Every server restart wipes all verified decisions, correct/incorrect counts, and centroid checkpoints from S2P. Conservation law starts from zero after every restart. This is a significant gap for any pilot claim about S2P.

**Fix:** Replace with `SQLiteGraphStore` as per Trading/Purchasing/DataOps pattern. Part of S2P-PRESET (#19) work.

**CHECK-20.5 — S2P has 11 routers with zero test coverage**

| Router | Routes | Tests |
|---|---|---|
| framework_router.py | 28 | ❌ NO TESTS |
| s2p.py | 6 | ❌ NO TESTS |
| s2p_evolution.py | 6 | ❌ NO TESTS |
| s2p_explorer.py | 6 | ❌ NO TESTS |
| s2p_governance.py | 6 | ❌ NO TESTS |
| s2p_discovery.py | 5 | ❌ NO TESTS |
| s2p_simulation.py | 4 | ❌ NO TESTS |
| s2p_clustering.py | 2 | ❌ NO TESTS |
| s2p_early_warning.py | 2 | ❌ NO TESTS |
| s2p_novelty.py | 2 | ❌ NO TESTS |
| s2p_payment.py | 2 | ❌ NO TESTS |

69 of ~109 S2P routes have zero test coverage. The 8 routers with tests (preview, suppliers, insight, evidence, pvg, control_tower, performance, data_helpers) cover ~40 routes.

### New Structural Discoveries

**copilot_sdk/rl/ package now exists:**
```
exploration.py    (3,058B) — Thompson sampling / exploration policy
reward_functions.py (2,068B) — domain reward functions
reward.py         (1,583B) — reward computation
credit.py         (1,246B) — credit assignment
```
RL extracted from SOC-only into SDK. Closes earlier gap N/A from v20.

**copilot_sdk/evolution/ is now 12 files:**
`variant_store.py` (6,212B) added — durable evolution event storage at SDK level. Likely resolves the `save_evolution_event()` SQLite gap identified in v20 (item N7).

**Trading massively expanded (MAP v5.121 level):**
- 26 routes across 10 router files (was ~4 routes previously)
- 574 test functions in 29 test files
- New routers: correlation, data_import, evidence, journal, prescore, promotion, regime, vix_timing
- Established as the most tested SDK copilot

**Trading factor registry fallback mismatch:**
`registry.py` tries `TradingPreset().shape.factor_names` first, then falls back to hardcoded names:
`signal_alignment, market_regime, position_sizing, timing_quality, risk_reward_actual, emotional_indicator, signal_confidence`
These names DO NOT match the actual preset factor names. If the TradingPreset import fails at runtime, factor names will be silently wrong. The try/except around the preset import is too broad.

### Updated Platform Tensor Shape Reference (v21 canonical)

| Copilot | Tensor | C | A | D | Values | penalty_ratio |
|---|---|---|---|---|---|---|
| SOC | (6,4,6) | 6 | 4 | 6 | 144 | 20.0 |
| S2P | (5,5,7) | 5 | 5 | 7 | 175 | 5.0 |
| Trading | **(5,4,7)** | 5 | **4** | **7** | **140** | 3.0 |
| Purchasing | **(5,4,7)** | 5 | 4 | **7** | **140** | 3.0 |
| DataOps | (6,5,6) | 6 | 5 | 6 | 180 | 10.0 |

### Fitness Check Summary

| Category | Pass | Fail | Gap |
|---|---|---|---|
| Cross-repo boundaries (1.x) | 7/7 | 0 | 0 |
| GraphStore hygiene (2.x) | 3/6 | 1 (2.3) | 2 (2.4, 2.7) |
| Conservation constants (3.x) | 4/5 | 0 | 1 (SOC penalty_ratio unverified) |
| Promotion gate (4.x) | 3/4 | 0 | 1 (2.7 not shipped) |
| Frontend (14.x) | 1/2 | 1 (Trading 6≠5) | 0 |
| Cross-copilot consistency (15.x) | 2/3 | 1 (15.8 S2P InMemory) | 0 |
| Code quality (19.x) | 3/3 | 0 | 0 |
| S2P test coverage (20.5) | 0/1 | 1 (69 routes) | 0 |

**Actionable fixes in priority order:**
1. S2P InMemoryGraphStore → SQLiteGraphStore (P1 persistence, part of S2P-PRESET #19)
2. DataOps AGEClient direct import → route through GraphStore (Rule #29, 30 min)
3. Trading 6th screen → document or remove (before Loom)
4. S2P 69 untested routes → add test files for critical routers (s2p.py, evolution, governance)
5. Trading factor registry fallback → fix hardcoded names to match preset

---
*Document version: v36.0 · May 25, 2026 · Living document*
*Code + MAP v5.121 + fitness_checks_v3.0 are authoritative*

---

## Part 36 — Final Validation Scans: All Open Questions Closed

### Trading Domain Reframe (Major Conceptual Update)

Trading is NOT a directional copilot (buy/hold/sell). It is an **execution quality copilot**.

**Actions (A=4):** `strong_execution, partial_execution, poor_execution, skip_recommended`
These evaluate HOW WELL a trade was executed, not which direction to trade.

This changes the commercial framing entirely. Trading's "decision" is: given a trade you've already decided to make, what execution quality did you achieve? This is a post-decision evaluation domain, not a pre-decision recommendation domain. The 6 screens (Dashboard, Analysis, Journal, LogTrade, Performance, TradeDetail) all make sense in this context — TradeDetail is a drill-down screen accessed from Journal/LogTrade, not a primary nav tab.

**CHECK-14.7 updated:** 6 screens is correct for Trading. The fitness check spec (expected 5) is stale.

### copilot_sdk/rl/ — Complete Package, Zero Wiring

Full package exports:
```python
RewardFunction           # protocol
RewardComputer           # implementation
BinaryRewardFunction     # binary correct/incorrect
GradedFinancialRewardFunction  # dollar-weighted
PnLRewardFunction        # P&L-based (Trading)
WasteReductionRewardFunction   # waste reduction (Purchasing)
CreditAssigner           # chain credit
ConservationBoundedThompson    # exploration policy
```

**Zero imports of `copilot_sdk.rl` found anywhere outside the package itself.** The RL package is complete and ready — but no scorer, no app, no router currently uses it. SDK apps still use scoring_router's inline `_signed_reward()` function. To activate: inject via `CompoundingScorer.from_preset(..., reward_function=GradedFinancialRewardFunction(...))`.

### AGEGraphStoreAdapter — Transitional Bridge (Closed)

Docstring: *"Transitional SDK GraphStore-compatible wrapper around AGEGraphStore."*

It's a thin delegation layer allowing SOC/ci-platform to use AGEGraphStore through the same Protocol interface as SQLiteGraphStore. Exists to support migration without breaking existing SOC code. Not a design problem — it's the mechanism that makes the AGE→SDK migration possible without a flag day. The "undocumented 4th implementation" concern from v20 is resolved.

### S2P InMemoryGraphStore — One-Line Fix

```python
# Current (loses all state on restart):
graph_store=InMemoryGraphStore(decision_id_prefix="S2P-")

# Fix (persists to SQLite):
graph_store=SQLiteGraphStore(str(DATA_DIR / "s2p.db"), domain="s2p")
```

The `decision_id_prefix="S2P-"` is only used for in-memory ID generation — it adds no persistence semantics. Switching to SQLiteGraphStore requires one line in `main.py` plus the `copilot_sdk.graph import SQLiteGraphStore` import. All downstream services (`app.state.graph_store`, `app.state.scorer`, `app.state.s2p_evolution`) chain off the same reference and would automatically persist.

### Conservation Constants — Confirmed (CHECK-3.6, 3.7)

| Constant | Value | Status |
|---|---|---|
| q_window | 400 | ✅ S2P config.py:118, Trading preset:67 |
| temperature (τ) | 0.1 | ✅ All 4 presets, archetype generator |

Note: `generators/archetype.py:29` uses `temperature: float = 0.1` as a softmax parameter — same value as scorer τ but independent context. Not a conflict.

### Complete Updated Platform Reference (v22 canonical)

| Copilot | Tensor | Actions | Domain framing | penalty_ratio | Persistence |
|---|---|---|---|---|---|
| SOC | (6,4,6) | escalate/investigate/suppress/monitor | Threat triage | 20.0 | AGE (PostgreSQL) |
| S2P | (5,5,7) | approve/flag/hold/escalate/reject | Invoice exception | 5.0 | **InMemory** ⚠️ |
| Trading | (5,4,7) | strong/partial/poor_exec/skip | **Execution quality** | 3.0 | SQLite |
| Purchasing | (5,4,7) | order_as_planned/more/less/skip | Food procurement | 3.0 | SQLite |
| DataOps | (6,5,6) | auto_approve/investigate/escalate_owner/pause_downstream/refer | Data quality | 10.0 | SQLite |

### What Remains Genuinely Open

After all scans, the genuine open items are:

| Item | Priority | Effort |
|---|---|---|
| S2P InMemoryGraphStore → SQLiteGraphStore | P1 | 5 min + restart |
| DataOps AGEClient direct import in graph_queries.py | P1 | 30 min |
| copilot_sdk/rl/ wiring to SDK scorers | P2 | Design decision needed |
| 69 untested S2P routes | P2 | 1-2 sprints |
| EvolutionStore protocol (CHECK-2.7) | P3 | Design needed |
| Trading factor registry fallback names mismatch | P3 | 15 min |

Everything else is confirmed clean or explained.

---
*Document version: v36.0 · May 25, 2026 · Living document — final fitness scan*
*Code + MAP v5.121 + fitness_checks_v3.0 are authoritative*

---

## Part 37 — Complete Q&A: All 10 Questions Answered (May 25, 2026)

### Q2 — Trading Bootstrap JSON: SHAPE MISMATCH (P1)

```
trading_bootstrap.json: (5, 3, 6) = 90 values
TradingPreset.shape:    (5, 4, 7) = 140 values
```

`_load_bootstrap()` validates shape and raises `ValueError` on mismatch, then catches and falls back to `np.full((5,4,7), 0.5)` — uniform neutral priors. Every Trading restart starts from zero knowledge instead of calibrated bootstrap. This is TRD-DB-FIX. Fix: run the bootstrap regeneration script for the new (5,4,7) shape.

### Q3 — Purchasing 7th Factor

`price_memory_index` — historical price tracking per supplier × category. High = price within learned norms. Low = anomalous price spike or hidden discount opportunity. Previous 6 factors unchanged. Now stored in `purchasing_bootstrap.json` (which also needs shape verification — previously (5,4,6), now (5,4,7)).

### Q5 — S2P Factor Names (Confirmed)

```
match_status                  (0) — PO/invoice field alignment
amount_variance_ratio         (1) — dollar amount delta vs PO
duplicate_score               (2) — similarity to prior invoices
supplier_exception_history    (3) — supplier's past exception rate
payment_terms_impact          (4) — DPO/cash flow effect
commodity_index_correlation   (5) — price vs market commodity index
tax_regulatory_compliance     (6) — tax/regulatory flag score
```

The 8-factor design doc included `environmental_risk` as factor 8. Shipped as Option C (7 factors) without it.

### Q6 — float("inf") Severity: Downgraded to P2

The `return float("inf")` at scorer.py:48 is in a helper function taking `alpha` and `verified` parameters — called from the **conservation status display method**, not from `_conservation_pause()` or `learn()`. If `penalty_ratio` or `verified` is non-numeric, the status API response contains `inf` which JSON-serializes as null or raises in some parsers. UI display corruption only — centroids are unaffected. Fix: return `None` or `99.0`.

### Q7 — Evolution Ledger Missing Domain (P1)

Current call in `ledger.py`:
```python
self._graph_store.save_evolution_event(
    event.event_type,
    event.rule_name,
    event.variant_id,
    metadata={**event.metadata, "timestamp": event.timestamp},
)
```

`domain` is absent. If `AGEGraphStore.save_evolution_event()` requires domain (likely — every other AGE write is domain-scoped), this call will:
- Either fail silently (if AGEGraphStore has a default domain), storing all events under wrong domain
- Or raise an exception caught by the broad `except Exception` and logged as warning — events silently dropped

**Cross-domain event queries would return empty results for SDK copilots even when events were written.** Fix: add `domain=` parameter to the call, sourced from the evolver's preset name.

### Q8 — DefaultPromotionGate AMBER Pass (P2)

```python
conservation_status = str((conservation_state or {}).get("status", "GREEN")).upper()
checks["conservation"] = conservation_status != "RED"
```

When `conservation_state` is `None` or `{}`: defaults to `"GREEN"`, conservation check passes. When conservation is `"AMBER"`: `"AMBER" != "RED"` is True — conservation check passes. Only `"RED"` blocks promotion.

The SOC promotion gate (promotion_gate.py) explicitly checks conservation before promotion. The SDK `DefaultPromotionGate` is more permissive — AMBER allows promotion. For a variant that degrades performance during a conservation AMBER period, this means it can be promoted despite the system being in an oversight-constrained state.

**Fix:** `conservation_status == "GREEN"` — one character change.

### Q10 — Conservation Gate Formula: Confirmed Correct

`_conservation_pause()` (the actual learning gate) uses:
```python
verified, correct, override_rate = _conservation_stats(self._graph_store)
theta_min = compute_theta_min(override_rate, verified)  # from gae.calibration
```
`verified = count_verified()` from GraphStore. `override_rate` = fraction of decisions that were overrides (this IS alpha — human override rate). The formula is canonical. Lines 390/492 using `penalty_ratio` are in `_conservation_status()` for display only.

### Updated Action List (All Findings Consolidated)

**P1 — Fix immediately:**

| # | Finding | Fix | Time |
|---|---|---|---|
| 1 | trading_bootstrap.json shape (5,3,6) not (5,4,7) | Regenerate bootstrap JSON | 15 min |
| 2 | S2P InMemoryGraphStore — no persistence | `SQLiteGraphStore(str(DATA_DIR / "s2p.db"), domain="s2p")` | 5 min |
| 3 | Evolution ledger missing domain parameter | Add `domain=preset.name` to `save_evolution_event()` call | 15 min |
| 4 | DataOps AGEClient direct import | Route through GraphStore or AGEGraphStoreAdapter | 30 min |

**P2 — Fix before Loom:**

| # | Finding | Fix | Time |
|---|---|---|---|
| 5 | DefaultPromotionGate passes AMBER | Change `!= "RED"` to `== "GREEN"` | 2 min |
| 6 | float("inf") in conservation status display | Return `None` instead | 5 min |
| 7 | RL package unwired to any scorer | Design decision: which apps, which reward functions | Design session |
| 8 | 69 untested S2P routes | Add test files for s2p.py, evolution, governance | 2 sprints |

**P3 — Track:**

| # | Finding | Fix |
|---|---|---|
| 9 | Trading factor registry fallback names mismatch | Fix 7 hardcoded names to match preset |
| 10 | purchasing_bootstrap.json may also need shape check | Verify (5,4,7) |

---
*Document version: v36.0 · May 25, 2026 · Living document — fitness scan complete*
*Code + MAP v5.121 + fitness_checks_v3.0 are authoritative*

---

## Part 38 — GraphStore Architecture Audit v1.0 (May 25, 2026)

### Task 1/5/10 — Store Instantiation Map

| Copilot | Store Class | DB Path | Domain | Prefix | Instance Pattern |
|---|---|---|---|---|---|
| Trading | SQLiteGraphStore | `apps/trading/backend/data/trading.db` | trading | ❌ none | Fresh per call (factory) |
| Purchasing | SQLiteGraphStore | `apps/purchasing/backend/data/purchasing.db` | purchasing | ❌ none | Fresh per call (factory) |
| DataOps | SQLiteGraphStore | `apps/dataops/backend/data/dataops.db` | dataops | ❌ none | Fresh per call (factory) |
| S2P | SQLiteGraphStore | `app/data/s2p.db` | s2p | ✅ S2P- | Single shared via app.state |
| SOC | AGEGraphStore | PostgreSQL:5433 | soc | N/A | AGEClient singleton |

**Trading/Purchasing/DataOps fresh-instance pattern:** Each router mounts `lambda: _graph_store(scoring_db)`. Every request creates a new SQLiteGraphStore pointing to the same file. Data consistency is maintained via SQLite file-level locking, but this is NOT the single-instance pattern. S2P's `app.state.scorer.graph_store` shared by reference is the cleaner architecture. Recommend standardizing Trading/Purchasing/DataOps to S2P pattern.

### Task 2 — Direct DB Bypass Status

| Check | Result |
|---|---|
| AGEClient direct import (Rule #29) | ❌ **PERSISTS**: `apps/dataops/backend/app/graph_queries.py:43`. DOPS-AGE-FIX was "conditional import" — violation still present at module level |
| sqlite3.connect | ✅ ZERO violations |
| psycopg outside ci-platform | ✅ ZERO violations |

### Task 3 — EvolutionStore Separation (B1-FIX)

**Protocol separation: ✅ PASS.** GraphStore has 15 methods, zero evolution methods. `copilot_sdk/evolution/protocol.py` defines EvolutionStore (save_evolution_event + get_evolution_events with domain parameter), VariantSelector, ShadowRunner, PromotionGate, EvolutionLedger, EvolutionRule.

**GraphStore protocol grew from 11→15 methods:**
New: `load_latest_centroids`, `count_decisions`, `archive_old_decisions`, `count_archived`

**Domain parameter: ✅ FIXED.** `InMemoryEvolutionLedger(domain="unknown")` passes `domain=self.domain` to `save_evolution_event`. Q7 P1 bug from v23 is resolved.

**`_PreDomainEvolutionStoreAdapter` still exists** (ledger.py:82) — P3 debt. Handles legacy stores that don't accept domain.

**scorer.py EvolutionStore wiring:**
```python
cast(EvolutionStore, self._graph_store)  # GraphStore cast as EvolutionStore
```
Works because SQLiteGraphStore satisfies both protocols. Separation is at protocol contract level, not implementation level. Acceptable but should be documented explicitly.

### Task 6 — S2P-PERSIST: ✅ VERIFIED LANDED

```python
SQLiteGraphStore(effective, domain="s2p", decision_id_prefix="S2P-")
# effective = str(DATA_DIR / "s2p.db") in production
# effective = ":memory:" in test mode (db_path=None)
```
Single instance at `app.state.scorer.graph_store`, shared to conservation router via `lambda: app.state.scorer.graph_store`. Clean.

### Task 7 — InMemoryGraphStore Residuals: ✅ ZERO

No production InMemoryGraphStore. Clean.

### Task 9 — RL Storage Path: PARTIALLY STALE

At last full read (v22): `copilot_sdk/rl/` complete, entirely unwired. User has since done partial RL wiring. Fresh read needed — see targeted question below.

### Task 11 — SOC Architecture (from insights doc)

AGEClient singleton via `neo4j.py`. All SOC graph operations route through this client. PosteriorStore (`rl_posteriors` table, same PostgreSQL DB) bypasses GraphStore — acceptable for SOC (same DB instance) but documented fragmentation. AGEGraphStoreAdapter is the transitional bridge for SDK integration.

### Task 12 — decision_id_prefix Consistency

| Copilot | Prefix |
|---|---|
| S2P | `"S2P-"` ✅ |
| Trading | none ⚠️ recommend `"TRD-"` |
| Purchasing | none ⚠️ recommend `"PUR-"` |
| DataOps | none ⚠️ recommend `"DOPS-"` |

Prefixes are optional in both SQLiteGraphStore and InMemoryGraphStore (default ""). Adding them enables unambiguous cross-copilot decision identification in discovery patterns.

### Recommended Fixes (Ordered by Severity)

| # | Finding | Fix | Effort |
|---|---|---|---|
| 1 | DOPS-AGE-FIX incomplete — AGEClient still imported | Route through AGEGraphStoreAdapter | 30 min |
| 2 | Trading/Purchasing/DataOps fresh-instance pattern | Move to single-instance via app.state | 1h per app |
| 3 | No decision_id_prefix on Trading/Purchasing/DataOps | Add TRD-/PUR-/DOPS- to _graph_store() | 5 min each |
| 4 | _PreDomainEvolutionStoreAdapter | Remove when all stores support domain | 30 min |

---
*Document version: v36.0 · May 25, 2026 · Living document*
*Code + MAP v5.121 + graphstore_architecture_audit_v1.0 are authoritative*

---

## Part 39 — Task 9: RL Storage Path Audit (Complete)

**File:** `copilot_sdk/rl/presets.py`

### Critical Finding: graph_store Discarded

```python
def get_rl_components(domain, preset, graph_store=None):
    del graph_store  # ← DISCARDED IMMEDIATELY
    config = RL_PRESET_REGISTRY.get(domain)
    ...
    return {
        "reward_function": _construct(reward_factory),
        "credit_assigner": CreditAssigner(),                           # no store
        "exploration_policy": ConservationBoundedThompson(n_actions),  # no store
    }
```

The `graph_store` parameter is accepted by signature but deleted before use. **Rule #35 is violated for RL state.**

### RL_PRESET_REGISTRY Coverage

| Domain | Registered | Reward Function | Notes |
|---|---|---|---|
| trading | ✅ | PnLRewardFunction | penalty_ratio=3.0 |
| purchasing | ✅ | WasteReductionRewardFunction | penalty_ratio=3.0 |
| dataops | ✅ | GradedFinancialRewardFunction | penalty_ratio=10.0 |
| s2p | ❌ | None | RL silently disabled via try/except |
| soc | ❌ | N/A | Uses separate rl_engine.py |

### Storage Path for Each RL Component

| Component | Where state lives | Persists? | Rule #35 |
|---|---|---|---|
| RewardFunction | Stateless (compute only) | N/A | ✅ N/A |
| CreditAssigner() | In-memory | ❌ Lost on restart | ❌ Violated |
| ConservationBoundedThompson | In-memory Beta posteriors | ❌ Lost on restart | ❌ Violated |
| exploration_used flag | Hardcoded False | N/A | ❌ Never meaningful |

### Downstream Consequences

**Thompson sampling:** Posterior accumulation is the entire value of Thompson sampling — it remembers which actions worked. Starting from uniform Beta(1,1) on every restart means the exploration policy never becomes informed. The copilot re-explores the same actions indefinitely instead of converging.

**Credit assignment:** `CreditAssigner()` without graph_store cannot query TRIGGERED_EVOLUTION edges. Either returns zero credits for every decision, or fails silently and the credit path is dead.

**S2P RL:** `get_rl_components("s2p", ...)` returns `None` → `from_preset()` catches via try/except → RL silently disabled. S2P never gets exploration or credit — even the degraded in-memory version.

### Fix Specification

```python
# In presets.py:
return {
    "reward_function": _construct(reward_factory),
    "credit_assigner": CreditAssigner(graph_store=graph_store),
    "exploration_policy": ConservationBoundedThompson(
        n_actions=n_actions, graph_store=graph_store
    ),
}
# Remove: del graph_store
```

Then in ConservationBoundedThompson and CreditAssigner:
- Accept optional `graph_store` parameter
- Persist posterior updates via GraphStore method (new `save_rl_state()` or embed in `write_outcome()` metadata)
- Add "s2p" to RL_PRESET_REGISTRY with appropriate reward function

### Recommendation Priority

| Fix | Effort | Impact |
|---|---|---|
| Remove `del graph_store`, pass to components | 5 min | Unblocks persistence |
| Add graph_store param to CreditAssigner | 30 min | Credit traversal works |
| Add graph_store param to ConservationBoundedThompson | 1h | Posteriors persist |
| Add "s2p" to RL_PRESET_REGISTRY | 30 min | S2P gets RL |
| Fix exploration_used tracking | 1h | Exploration loop closes |

---
*Document version: v36.0 · May 25, 2026 · Living document*
*Code + MAP v5.121 + graphstore_architecture_audit_v1.0 are authoritative*

---

## Part 40 — Pre-Codex Q1-Q6 Answers (May 25, 2026)

### Q1 — CreditAssigner.assign(): Pure Math, No Graph

```python
def assign(reward, factors, factor_contributions=None, decision_age=0) -> dict[str, float]
```

Pure temporal discount math: `base = reward × (temporal_discount=0.95 ^ decision_age)`. Distributes base proportionally by `factor_contributions` magnitudes if provided, uniformly if not. Zero graph calls. Zero external state.

**For RL-PERSIST:** TRIGGERED_EVOLUTION edge traversal requires new design from scratch. Suggested: add `graph_store: GraphStore | None = None` param; when provided, query `get_verified_decisions()` filtered by category for chain credit weighting; fall back to current math-only behavior when None.

### Q2 — ConservationBoundedThompson: State Surface

**Three state fields — everything that needs persistence:**
```python
alpha: list[float]  # length=n_actions, init=1.0 each — success counts
beta:  list[float]  # length=n_actions, init=1.0 each — failure counts  
_conservation_status: str  # "GREEN"|"AMBER"|"RED"
```

**Key behaviors:**
- `update(action, reward)`: alpha[action] += reward if >0; beta[action] += |reward| if <0
- `select_action(probabilities)`: greedy when AMBER/RED; Thompson sample when GREEN
- `get_priors()`: returns `{"alpha": [...], "beta": [...], "conservation_status": str}` — serialization-ready
- `reset()`: wipes to uniform Beta(1,1), status GREEN
- No history buffer. No rolling window.

**For RL-PERSIST:** On each `update()`, call `get_priors()` and persist to GraphStore. On construction with existing store, load latest and restore. `get_priors()` is already designed for this.

### Q3 — DataOps graph_queries.py: AUDIT CORRECTION

**DOPS-AGE-FIX is CORRECTLY implemented. Rule #29 violation was a FALSE POSITIVE.**

The AGEClient import is inside a guarded lazy-loader function:
```python
def _load_age_client_class() -> type[Any] | None:
    try:
        from ci_platform.graph.age_client import AGEClient  # lazy, guarded
    except Exception:
        return None
    return AGEClient
```

All 10 public methods have deterministic fixture fallback when AGE unavailable. `_run_graph()` returns None on failure and sets `_graph_connected = False`. `DataOpsGraphClient` is a correct dual-mode client.

**Cannot be replaced by GraphStore Protocol** — these are domain graph queries for pipeline topology (PipelineSystem nodes, FEEDS edges, DataQualityAlert nodes). GraphStore handles judgment memory; this handles semantic memory. The architecture is correct by design.

**Reclassify:** DOPS-AGE-FIX finding → LEGITIMATE PATTERN, not a violation.

### Q4 — FreshScorerProxy: Location Unknown

`class FreshScorerProxy` not found in `copilot_sdk/scoring/scorer.py`. Must be in a separate file. From main.py usage: `FreshScorerProxy(DOMAIN, scoring_db, _graph_store)` where `_graph_store` is a **factory function** `lambda db_path: SQLiteGraphStore(...)`. The proxy calls the factory to create a fresh store per request.

**For APP-STORE-HYGIENE:** Switching to single-instance pattern requires finding the proxy class and either (a) changing it to receive an existing store instance instead of a factory, or (b) bypassing the proxy entirely by passing a long-lived scorer to the routers.

**Follow-up command needed:**
```powershell
Get-ChildItem "copilot_sdk" -Filter "*.py" -Recurse | Select-String -Pattern "class FreshScorerProxy" | ForEach-Object { "$($_.Path): $($_.LineNumber): $($_.Line.Trim())" }
```

### Q5 — SQLiteGraphStore decision_id_prefix: Confirmed

Constructor line 42: `def __init__(self, db_path, domain="graph", decision_id_prefix="")`. Used in `write_decision()` at lines 253-254 to prefix generated IDs. On `SQLiteGraphStore` itself, not a subclass. APP-STORE-HYGIENE can pass `decision_id_prefix="TRD-"` (etc.) directly.

### Q6 — S2P Untested Endpoint Inventory (44 routes, 10 routers)

framework_router.py excluded — 28 /soc/* routes unmounted by S2P-FW-ROUTER-CLEANUP. File kept, not served.

| Router | Routes | Endpoints |
|---|---|---|
| s2p.py | 6 | POST /score, GET /auto-approve/stats, GET /auto-approve/expansion-proof, POST /outcome, GET /iks, GET /learning-gate |
| s2p_evolution.py | 6 | GET /rules, GET /variants, GET /promotion-check, POST /reset, GET /shadow-results, GET /promoted |
| s2p_governance.py | 6 | GET /compliance-screening, GET /compliance-gaps, GET /conservation-proof, GET /rationalization, GET /rationalization/overlap, GET /rationalization/supplier/{id} |
| s2p_explorer.py | 6 | GET /export/centroids, GET /export/csv, GET /centroid/{cat}/{act}, GET /drift/{cat}, GET /dk-weights, GET /contribution |
| s2p_discovery.py | 5 | GET /alerts, GET /disruptions, GET /extended, GET /supplier/{id}, GET /propagation/{id} |
| s2p_simulation.py | 4 | GET /scenarios, GET /scenarios/{id}, GET /what-if/{id}, GET /impact-summary |
| s2p_novelty.py | 4 | GET /status, GET /history, GET /rate, GET /auto-pause |
| s2p_clustering.py | 2 | GET /clusters, GET /similarity |
| s2p_early_warning.py | 3 | GET /early-warnings, GET /trends, GET /trend-signals |
| s2p_payment.py | 2 | GET /payment-strategy, GET /payment-behavior |

**Priority for S2P-TEST-COVERAGE:** s2p.py (core scoring/learning), s2p_evolution.py (AE), s2p_governance.py (conservation proof) — these three have the most production risk. The rest (simulation, clustering, novelty, payment) are analytical endpoints that can follow.

---
*Document version: v36.0 · May 25, 2026 · Living document*
*Code + MAP v5.121 + graphstore_architecture_audit_v1.0 are authoritative*

---

## Part 41 — PW Regression Root Cause (May 26, 2026)

### What Was Wrong With the Investigation Premise

"Despite zero intentional frontend changes" was incorrect. Batch H+I+J (commit `29931dc`) modified 12 frontend files: `api.ts`, `RegimePanel.tsx`, `CorrelationPanel.tsx`, `OptionsFactorPanel.tsx`, `PreScorePanel.tsx`, `PromotionPanel.tsx`, `VIXTimingPanel.tsx`, `AnalysisScreen.tsx`, `JournalScreen.tsx`, `LogTradeScreen.tsx`, `PerformanceScreen.tsx`, `types.ts`. The PW failures are a direct consequence of adding 6 new components/features without updating all existing PW specs.

### Root Cause 1: PW Specs Not Updated After Component Changes

Batch H+I+J added: promotion panel, regime-recommend, correlation, earnings-subcat, vix-timing, options-factors. Each adds new components that changed screen structure. The existing PW specs were written against the pre-H+I+J layout and now reference elements that have moved or been restructured.

### Root Cause 2: Preseed Missing 4th Trading Action

```python
# preseed_all_copilots.py Trading config:
actions=["strong_execution", "partial_execution", "poor_execution"]
# Missing: "skip_recommended"
```

Tensor is (5,4,7) — 4 actions. Preseed only seeds 3. `skip_recommended` (action index 3) has zero historical data. Per-action panels render empty for that action slot. Panels that require all 4 action slots may conditionally hide themselves (empty state).

### CORS: NOT the Root Cause

All four apps use identical pattern:
```python
DEFAULT_CORS_ORIGINS = (
    "http://localhost:5173,"
    "http://localhost:5174,"
    "http://localhost:5175,"
    "http://localhost:5176,"
    "http://localhost:5177"
)
```
CORS allows 5 Vite ports. Trading/Purchasing/DataOps all identical. CORS does not differentiate Trading failures from Purchasing/DataOps passes.

### trade-metadata endpoint: EXISTS

`context_router.py:409` — `POST /api/context/trade-metadata`. Mounted at `apps/trading/backend/app/main.py:264` as `prefix="/api/context"`. The endpoint is present and returns data from `trade_metadata.json`. CORS cluster A is likely a cascade from a different failure, not a missing endpoint.

### Spec File Location (Corrected)

Specs are at `e2e/trading/` (top-level), NOT `apps/trading/e2e/`. 21 spec files confirmed. Previous scans with wrong path returned false "NOT FOUND" results.

### Cluster Attribution

| Cluster | Specs | Expected text | Likely cause |
|---|---|---|---|
| C — Dashboard text | flows.spec.ts | /Portfolio Summary/, /Decision History/, /Accuracy Alerts/ | DashboardScreen restructured in H+I+J |
| B — Regime missing | regime.spec.ts | RegimePanel visible | RegimePanel.tsx modified — API call or render changed |
| A — CORS/trade-metadata | flows.spec.ts | waitForResponse /api/context/trade-metadata | Cascade from Cluster B or preseed empty state |
| D — Score timeout | flows.spec.ts | waitForResponse /api/score, 15s | Cold scorer + empty preseed data = slow first call |

### Fix Sequence

1. Fix preseed to include `skip_recommended` — restores 4th action data for all panels
2. Update PW specs to match new screen structure from H+I+J
3. Re-run to see which failures remain (likely reduces from 21 to <5)

---

## Part 42 — Post-Implementation Verification

### SCORER-CACHE: ✅ CORRECTLY LANDED

`copilot_sdk/backend/scorer_proxy.py`:
- `self._lock = threading.RLock()` — reentrant lock for thread safety ✅
- `self._scorer_instance: CompoundingScorer | None = None` — lazy singleton ✅
- `_scorer()` uses double-check pattern with lock ✅
- `CompoundingScorer.from_preset(..., graph_store=self.graph_store)` — uses shared store ✅
- `_close_scorer_store` → `return None` (no-op) — store lifecycle controlled by proxy ✅

Every method (score, learn, fingerprint, trajectory, get_phase, get_alpha) acquires `_lock` before calling `_scorer()`. RLock allows reentrant acquisition. Correct.

### RL-PERSIST: ❌ INCOMPLETE

No `save_rl_state()` or `load_rl_state()` methods exist in scorer.py. Centroid checkpoints are saved (`_save_centroids_checkpoint` at multiple points in `learn()`), but Thompson posterior arrays (`alpha[]`, `beta[]` in `ConservationBoundedThompson`) are still in-memory only. `del graph_store` in `presets.py` is still present. Thompson posteriors reset to uniform Beta(1,1) on every restart.

### S2P Legacy ProfileScorer: ❌ STILL EXISTS

`domains/s2p/scorer.py` still contains:
```python
_scorer: ProfileScorer | None = None
def get_scorer() -> ProfileScorer: ...
def _build_scorer() -> ProfileScorer: return ProfileScorer(...)
```
`routers/s2p_preview.py:185` still imports and constructs `ProfileScorer` directly. S2P-PRESET unified the CompoundingScorer path in `main.py` but the legacy files were NOT removed. Dual-scorer problem persists for the preview tab.

### SDK-CLEANUP (_PreDomainEvolutionStoreAdapter): ✅ COMPLETE

Zero results for `_PreDomainEvolutionStoreAdapter` scan. Removed.

---

## Part 43 — Architecture Health

### Conservation Formula: Three Variants Persist

| Location | Formula | Status |
|---|---|---|
| `copilot_sdk/scoring/scorer.py:604,818` | `compute_theta_min(override_rate, verified)` | ✅ Canonical |
| `apps/dataops/backend/app/context_router.py:220` | `23.53 / (effective_alpha * v_cat)` | ⚠️ Inline, per-category variant |
| `s2p-copilot/backend/app/routers/s2p_performance.py:101` | `23.53 / (PENALTY_RATIO * new_verified)` | ❌ Wrong denominator |

### S2P Test Coverage: Unchanged (11 routers, zero tests)

Same as previous scan. No new test files added for untested routers.

### Backend Test Counts (May 26)

| Copilot | Tests |
|---|---|
| Trading | 641 |
| Purchasing | 141 |
| DataOps | 152 |

---

## Part 44 — New Questions

### Component Conditional Rendering (The Silent Failure Pattern)

24 Trading components have `useEffect` API hooks. When any API call fails (CORS, 404, timeout, empty response), the component state stays at its default (null/empty), the conditional render fires the empty branch, and the panel shows nothing. PW `expect(element).toBeVisible()` fails with no console error in the backend. This is the mechanism behind ALL "panel not found" failures.

### Trading vs Purchasing Structural Gap

Trading mounts 16+ routers: scoring, transfer, conservation, evolution, self-computation, context, evidence, journal, analytics, correlation, prescore, promotion, regime, social, vix-timing, webhook, data-import. Purchasing mounts ~8. Every router beyond the base set is a surface area for silent API failures → empty panels → PW failures.

### Prioritized Fix List (Derived from Analysis)

**Immediate (before next PW run):**
1. Fix preseed to include `skip_recommended` as 4th Trading action — restores data for all per-action panels
2. Update PW specs for Batch H+I+J new structure — regime, correlation, vix-timing, promotion panels

**Near-term:**
3. Remove legacy `domains/s2p/scorer.py` and `s2p_preview.py` ProfileScorer — complete S2P-PRESET
4. Fix RL-PERSIST — remove `del graph_store`, wire Thompson posteriors to GraphStore
5. Fix S2P `s2p_performance.py:101` conservation formula — use `compute_theta_min()`

**Tracked (no immediate action):**
6. DataOps `context_router.py:220` conservation formula — per-category variant, intentional
7. S2P test coverage — 11 routers still untested

---
*Document version: v36.0 · May 26, 2026 · Living document*
*Code + MAP v5.121 are authoritative*

---

## Part 45 — Fix Sequencing with Dependency Analysis (May 26, 2026)

### Q1 — Dependency Graph

```
A1 ──soft──→ A2      Run PW after A1; fix remaining failing specs in A2.
                      A2 before A1 = writing against moving target.

B1+B3 ──hard──→ B2   B1 removes del graph_store. B2 uses graph_store in
                      component constructors. Same commit (presets.py).

B2 ──soft──→ B4      exploration_used tracking requires graph_store in
                      ConservationBoundedThompson. Stub before B2 is noise.

C2 ──soft──→ C1      Switch s2p_preview.py to app.state.scorer (C2), then
                      delete domains/s2p/scorer.py (C1). Same commit is fine.

D1 independent       s2p_performance.py only. No other fix touches it.
E1 independent       gate.py only. One character.
F1 bundles with B2   Both touch scorer.py. One PR.

C1/C2 independent of B   Different repos entirely.
D1 independent of C       Different files in same repo.
```

### Q2 — Parallel Safety (File Overlap Matrix)

| File | Fixes that touch it | Parallel safe? |
|---|---|---|
| `copilot_sdk/rl/presets.py` | B1, B3 | Must be ONE commit |
| `copilot_sdk/scoring/scorer.py` | B2, F1 | Bundle into one PR |
| `copilot_sdk/rl/exploration.py` | B2, B4 | B2 adds param; B4 uses it — serial |
| `copilot_sdk/rl/credit.py` | B2 only | No conflict |
| `copilot_sdk/graph/protocol.py` | B2 (new methods) | Blocks all 4 store impls |
| `s2p-copilot/backend/app/routers/s2p_preview.py` | C2 only | No conflict |
| `s2p-copilot/backend/app/domains/s2p/scorer.py` | C1 only | No conflict |
| `s2p-copilot/backend/app/routers/s2p_performance.py` | D1 only | No conflict |
| `copilot_sdk/evolution/gate.py` | E1 only | No conflict |
| `e2e/trading/*.spec.ts` | A2 only | No conflict |
| `scripts/preseed_all_copilots.py` | A1 only | No conflict |

**B2 is the highest-risk fix.** Adding RL state persistence to GraphStore Protocol requires all 4 implementations to update simultaneously (SQLiteGraphStore, InMemoryGraphStore, AGEGraphStore, AGEGraphStoreAdapter). Alternative: persist Thompson state as JSON via existing `save_centroids()` with a reserved key like `_rl_state_{domain}`. Avoids Protocol changes entirely.

### Q3 — Per-Fix Effort Estimates

| Fix | File(s) | Lines changed | New tests | Risk | Notes |
|---|---|---|---|---|---|
| A1 | `scripts/preseed_all_copilots.py` | ~5 | 0 | Low | Add "skip_recommended" to Trading actions list. Purchasing already has 4 actions — no change needed. 7th factor handled by extract_factors() default 0.50 — no change needed. |
| A2 | `e2e/trading/*.spec.ts` (up to 21 files) | ~50–100 | 0 | Medium | Run PW after A1 first; fix only specs that still fail. Most use `expectAnyText([...])` — flexible pattern; only strict `.toBeVisible()` locators need changing. |
| B1+B3 | `copilot_sdk/rl/presets.py` | ~15 | 5 | Medium | Remove `del graph_store`. Pass to CreditAssigner() and ConservationBoundedThompson(). Add "s2p" to RL_PRESET_REGISTRY. ONE commit. |
| B2+F1 | `scorer.py`, `exploration.py`, `credit.py`, `protocol.py` (or use save_centroids alternative) | ~80–120 | 20 | HIGH | New Protocol methods = 4 store impls must update. ALTERNATIVE: JSON blob via `save_centroids("_rl_state_domain")` — no Protocol change, ~40 lines total. |
| C1+C2 | `s2p/scorer.py` (delete), `s2p_preview.py` (switch to app.state.scorer), `demo/s2p_demo.py` (update import) | ~45 | 10 | Low-Medium | s2p.py (core router) does NOT import legacy scorer — confirmed. Only 3 files affected: scorer.py, s2p_preview.py, s2p_demo.py. |
| D1 | `s2p_performance.py` | ~12 | 3 | Low | Import `compute_theta_min`. Compute `override_rate` from `get_verified_decisions()`. Use `compute_theta_min(override_rate, new_verified)` in what_if(). Access to graph_store already present via `_graph_store(request)`. |
| E1 | `copilot_sdk/evolution/gate.py` | 1 | 1 | Very Low | `conservation_status != "RED"` → `conservation_status == "GREEN"`. One line. |
| B4 | `scorer.py`, `exploration.py` | ~15 | 5 | Low | Close exploration_used tracking loop. After B2 only. |

### Q4 — Optimal Fix Sequence

```
Phase 1 — Parallel, no dependencies (same day, different Codex sessions):
  A1: preseed Trading 4th action    (scripts/, ~5 lines, low risk)
  E1: gate AMBER fix                (gate.py, 1 line, very low risk)
  D1: S2P conservation formula      (s2p_performance.py, ~12 lines, low risk)
  C1+C2: S2P legacy scorer removal  (s2p-copilot/, ~45 lines, medium risk)

Phase 2 — After Phase 1 verified (run PW first after A1):
  A2: PW spec updates               (e2e/trading/, ~100 lines, medium risk)
      [Run PW after A1. Fix only remaining failures. Expected: 21 → ~8-10]
  B1+B3: presets.py RL wiring       (copilot-sdk, ~15 lines, medium risk)
      [Parallel with A2 — different files, different repo concern]

Phase 3 — After B1+B3 landed:
  B2+F1: RL persistence + inf fix   (copilot-sdk, ~80 lines, HIGH risk)
      [Consider Protocol-free alternative via save_centroids JSON blob]

Phase 4 — After B2 verified:
  B4: exploration_used tracking     (copilot-sdk, ~15 lines, low risk)
```

### Q5 — What Else Is Broken

**C1 legacy scorer callers (confirmed):**
- `demo/s2p_demo.py:14` — imports from legacy scorer (demo script, not production)
- `s2p_preview.py:185,194` — constructs ProfileScorer directly
- `s2p.py` (core router) — does NOT import legacy scorer ✅

C1+C2 fix scope: delete `domains/s2p/scorer.py`, update `s2p_preview.py` to use `request.app.state.scorer`, update `demo/s2p_demo.py` import.

**A1 preseed scope (confirmed Trading-only):**
- Trading: `actions=["strong_execution", "partial_execution", "poor_execution"]` → add `"skip_recommended"`. ONE change.
- Purchasing: `actions=["order_as_planned", "order_more", "order_less", "skip"]` — already 4 actions. No change.
- Both: 7th factor handled by `extract_factors()` defaulting to 0.50. No factor change needed.

**Purchasing/DataOps/S2P PW specs:** No frontend changes in recent batch (only Trading). Their specs don't need updating.

**Expected PW count after A1+A2:** 21 failures → ~8-10 after A1 (preseed restores 4th-action data for all per-action panels) → ~2-4 after A2 (spec updates match new component structure) → ~0-2 genuine integration bugs remaining.

**D1 implementation detail:** `what_if()` is a projection endpoint. Current formula: `23.53 / (PENALTY_RATIO * new_verified)`. Fix requires:
```python
from copilot_sdk.scoring.scorer import compute_theta_min

# In what_if():
verified_decisions = _safe_call(graph_store, "get_verified_decisions", [], domain)
overrides = sum(1 for d in verified_decisions if d.get("outcome") == "override")
override_rate = overrides / len(verified_decisions) if verified_decisions else 0.0
theta_min = compute_theta_min(override_rate, new_verified)
theta_min = round(theta_min, 4) if theta_min is not None else 1.0
```

**B2 Protocol-free alternative:** Instead of adding `save_rl_state(domain, alpha, beta)` to GraphStore Protocol, call existing `save_centroids()` with a reserved metadata field:
```python
# In ConservationBoundedThompson.update():
self._graph_store.save_centroids(
    domain=f"_rl_state_{self._domain}",
    centroids={"alpha": self.alpha, "beta": self.beta},
    decision_count=0
)
```
Then `load_latest_centroids("_rl_state_{domain}")` on construction restores state. Zero Protocol changes. Zero new store implementations. ~40 lines total.

---
*Document version: v36.0 · May 26, 2026 · Living document*
*Code + MAP v5.121 are authoritative*

---

## Part 46 — Ground Truth Baseline (May 26, 2026)

### Critical Context: Large Uncommitted SDK Working Tree

The SDK repo has 50+ changed/new files not committed since `29931dc Batch H+I+J`. All Q2-Q16 results reflect the **working tree**, not HEAD. S2P and CI repos are clean.

**Untracked new files of note:**
- `copilot_sdk/rl/presets.py` — RL wiring (B1+B3 landed via this file)
- `apps/trading/backend/app/routers/social.py` — C2-SOCIAL
- `apps/trading/backend/app/routers/webhook.py` — C6-WEBHOOK
- `apps/trading/backend/app/routers/analytics.py` — new analytics router
- `apps/trading/backend/app/brokers/` — C3-BROKER
- `apps/purchasing/backend/app/routers/` — new routers for Purchasing
- `apps/purchasing/backend/cli.py` — new Purchasing CLI
- `tests/rl/test_rl_persistence.py`, `test_rl_wiring.py`, `test_rl_presets.py` — RL tests
- `tests/evolution/test_gate_fail_closed.py` — gate fix test

**Modified spec files in working tree:**
`e2e/trading/analysis.spec.ts`, `dashboard.spec.ts`, `flows.spec.ts`, `promotion.spec.ts`, `regime-recommend.spec.ts`, `conservation-breakdown.spec.ts`, `correlation.spec.ts` — A2 spec updates partially in progress.

### Ground Truth Status Table

| Item | Status | Evidence |
|---|---|---|
| B1-FIX (gate) | ✅ LANDED | `!= "RED"` absent, `_is_conservation_safe` present, `evolver_factory` present |
| RL-WIRE (B1+B3) | ✅ LANDED | `del graph_store` gone, S2P in registry, scorer imports `get_rl_components` |
| _PreDomain adapter | ✅ GONE | No match in ledger.py — SDK-CLEANUP complete |
| SCORER-INF | ✅ FIXED | No `float("inf")` in scorer.py |
| TRD bootstrap | ✅ (5,4,7) | Both trading AND purchasing bootstrap JSONs correct |
| S2P-PERSIST | ✅ LANDED | `SQLiteGraphStore(effective, domain="s2p", decision_id_prefix="S2P-")` |
| C3-BROKER | ✅ LANDED | `brokers/` dir, IBKR+Alpaca+CSV connectors, broker CLI functions |
| S2P-GAPS | ⚠️ PARTIAL | novelty/rate ✅, novelty/auto-pause ✅, novelty_score ✅ — financial-impact ❌, suppliers/trends ❌, heatmap ❌, correlations ❌ |
| TRD-FACTOR-FALLBACK | ⚠️ NAMES OK, IMPL WRONG | Names match preset, class implementations scrambled (see below) |
| A1-PRESEED | ❌ NOT DONE | `skip_recommended` absent — only 3 Trading actions in preseed |
| C1+C2 (legacy scorer) | ❌ NOT DONE | `scorer.py` exists, `s2p_preview.py` has `from gae import ProfileScorer` |
| D1-FORMULA | ❌ NOT DONE | `23.53 / (PENALTY_RATIO * new_verified)` still at line 101 |

### TRD-FACTOR-FALLBACK Detail

Registry fallback names now match preset — but class implementations are scrambled:

```python
# Current (fallback names correct, implementations WRONG):
"signal_alignment":   ConvictionFactor()       # possibly correct
"market_regime":      ResearchDepthFactor()    # WRONG — should be MarketRegimeFactor
"position_sizing":    TechnicalSignalFactor()  # WRONG — should be PositionSizeFactor
"timing_quality":     PositionSizeFactor()     # WRONG — should be TimeHorizonFactor
"risk_reward_actual": TimeHorizonFactor()      # WRONG
"emotional_indicator":MarketRegimeFactor()     # WRONG
"signal_confidence":  SignalConfidenceFactor() # correct
```

Only fires if TradingPreset import fails — low risk, but silently computes wrong factor values.

### Q2g — Purchasing Evolution Pattern

Purchasing uses fixture-backed evolution via `variant_provider=_evolution_variants` loading from `evolution_fixtures.json`. Not using live evolver. Consistent with documented design.

### Frontend Screen Inventory (Q15)

| Copilot | Screens |
|---|---|
| Trading | Dashboard, LogTrade, Analysis, Performance, Journal, TradeDetail (6) |
| Purchasing | Dashboard, Analysis, Inventory, Order, Performance (5) |
| DataOps | Dashboard, Triage, Evidence, Insight, Curve (5) |
| S2P | Dashboard, Triage, Evidence, Insight, Performance, Suppliers (6) |

### S2P Route Counts (Q16, current)

Total: ~96 routes across 20 router files. 11 routers still have zero test files. s2p_pvg.py grew from 4→5 routes, s2p_suppliers.py from 7→9 routes since last scan.

### Remaining Open Work (Priority Order)

| Fix | Status | Next action |
|---|---|---|
| A1: preseed skip_recommended | ❌ | Add to preseed_all_copilots.py Trading actions list |
| C1+C2: S2P legacy scorer | ❌ | Delete scorer.py, switch s2p_preview.py to app.state.scorer |
| D1: S2P conservation formula | ❌ | Import compute_theta_min, add override_rate computation |
| S2P-GAPS missing 4 endpoints | ⚠️ | Add financial-impact, suppliers/trends/heatmap/correlations |
| TRD-FACTOR-FALLBACK impl fix | ⚠️ | Correct class mapping in registry.py |
| A2: PW spec updates | 🔄 In progress | 7 specs modified in working tree — needs testing |
| Commit working tree | 🔴 | 50+ changes need commit before next Codex session |

---
*Document version: v36.0 · May 26, 2026 · Living document*
*Code + MAP v5.121 are authoritative*

---

## Part 47 — Comprehensive Assessment (May 26, 2026)

### Commit 4f26215 Summary

All previously uncommitted work is now in HEAD: B1-FIX, C3-BROKER, RL-WIRE, SCORER-INF, bootstrap fixes, PW specs (partial), social/webhook/analytics stubs, Purchasing CLI+evidence. SDK working tree: 1 file. S2P and CI: clean.

### Updated Status Table (v30 canonical)

| Item | Status | Evidence |
|---|---|---|
| B1-FIX (gate) | ✅ DONE | committed 4f26215 |
| RL-WIRE | ✅ DONE | all 4 domains in RL_PRESET_REGISTRY |
| S2P-PRESET | ✅ DONE | s2p in SCORING PRESET_REGISTRY |
| D1-FORMULA | ✅ DONE | compute_theta_min(override_rate, new_verified) in s2p_performance.py |
| SCORER-INF | ✅ DONE | committed 4f26215 |
| Bootstrap shapes | ✅ DONE | trading (5,4,7), purchasing (5,4,7) |
| _PreDomain adapter | ✅ GONE | SDK-CLEANUP complete |
| S2P-PERSIST | ✅ DONE | SQLiteGraphStore at s2p.db |
| C3-BROKER (CLI) | ✅ DONE | CLI + connectors; HTTP API = stub only |
| A1-PRESEED | ❌ NOT DONE | skip_recommended absent from Trading actions |
| C1+C2 legacy scorer | ❓ UNKNOWN | needs recheck after 4f26215 |
| Transfer router | ❌ NOT MOUNTED | 404 across Trading, Purchasing, DataOps |
| Docker | ❌ ABSENT | no Dockerfile in any repo |
| DI-1 SOURCE-PROFILER | ❌ ABSENT | no profiler code |
| TRD-FACTOR-FALLBACK | ⚠️ SCRAMBLED | only fires if TradingPreset import fails — low risk |

### Smoke Test Results (Assessment B)

**DataOps: 8/9 returning 200 (HEALTHY)**
200: health, conservation, evolution, pipelines, ae/impact, dataops/health, dataops/celonis/status, self/decisions
404: transfer/patterns (not mounted)

**Purchasing: 6/8 returning 200 (HEALTHY)**
200: health, conservation, evolution, context/analytics, context/items, purchasing/health
404: /evidence/factors (path mismatch — route is /evidence/summary), transfer/patterns

**Trading: 5/15 returning 200 — path mismatches, not absent code**
200: health, conservation, evolution, self/decisions, context/analytics
405: /api/score (needs POST — not a failure)
404 (path mismatches): regime/current, correlation/matrix, analytics/execution-summary, social/profiles
404 (not mounted): broker/orders, broker/positions (CLI only, no HTTP API), transfer/patterns
404 (likely prefix wrong): vix-timing/analysis

**Trading 404 root causes:**
- `regime/current` → route exists but not at `/current` suffix
- `analytics/execution-summary` → analytics.py has `/execution-analysis` and `/cross-insights`, not `/execution-summary`
- `social/profiles` → router prefix mismatch (router defines `/social/*` internally, suggesting it mounts at `/api` not `/api/social`)
- `broker/*` → C3-BROKER shipped CLI+connectors only; no FastAPI HTTP routes yet
- `transfer/patterns` → transfer router not mounted in Trading main.py

**S2P: TIMED OUT** — startup blocking call or fixture load time. Need shorter timeout.

### Test Counts (v30)

| Repo | Tests | PW specs | PW tests |
|---|---|---|---|
| Trading BE | 641 | 21 spec files | ~123 tests |
| Purchasing BE | 141 | 8 spec files | ~47 tests |
| DataOps BE | 167 | 8 spec files | ~99 tests |
| S2P BE | 775 | 21 spec files | ~135 tests |

### New File Inventory (all confirmed present)

| File | Lines | Routes | Notes |
|---|---|---|---|
| trading/routers/social.py | 94 | 9 | Stub — /traders, /social, /profiles etc |
| trading/routers/webhook.py | 291 | 4 | /tradingview, /history, /config, /test |
| trading/routers/analytics.py | 300 | 2 | /execution-analysis, /cross-insights |
| trading/app/brokers/ | 4 files | — | CLI only — alpaca, ibkr, csv, yfinance |
| trading/app/evolution/ | 3 files | — | dimensions.py (58L), variant_provider.py (11L) |
| purchasing/cli.py | 431 | — | Full CLI |
| purchasing/routers/evidence.py | 280 | 6 | /evidence/summary, /decisions, /audit-trail, /conservation-proof, /health, /status |
| dataops/routers/dataops_status.py | 126 | 4 | /health, /celonis/status, /sap/status, /enterprise-health |
| copilot_sdk/rl/presets.py | 63 | — | RL wiring for all 4 domains |

### Trading Service Layer (New)

10 service files in trading/services/:
- correlation.py (179L), pattern_detector.py (219L), promotion.py (200L)
- regime_recommender.py (153L), regime.py (170L), subcategory.py (75L)
- trader_profiles.py (231L), vix_timing.py (191L)

### Open Work (Priority Order for Next Batch)

| Fix | Status | Next action |
|---|---|---|
| A1: preseed skip_recommended | ❌ | Add to preseed_all_copilots.py Trading actions list (~5 min) |
| C1+C2: S2P legacy scorer | ❓ | Recheck: `Test-Path "$S2P\backend\app\domains\s2p\scorer.py"` |
| Transfer router mounting | ❌ | Mount create_transfer_router in Trading, Purchasing, DataOps main.py |
| Trading route path audit | ❌ | Verify regime, analytics, social, vix_timing mount paths vs smoke test |
| Broker HTTP API | ❌ | C3-BROKER CLI done; HTTP routes (order/positions/account) still needed |
| TRD-FACTOR-FALLBACK | ⚠️ | Fix class mapping in registry.py fallback (low risk, low priority) |
| DataOps conservation formula | ⚠️ | context_router.py:220 inline formula — display only, low priority |

---
*Document version: v36.0 · May 26, 2026 · Living document*
*Code + MAP v5.121 are authoritative*

---

## Part 48 — All Gaps Closed + Priority Recommendations (May 26, 2026)

### Final Gap Closure

**A1-PRESEED: DONE (was wrongly marked NOT DONE)**
```python
actions=["strong_execution", "partial_execution", "poor_execution", "skip_recommended"]
```
Also has dedicated handling:
```python
if config.name == "trading" and recommended_action != "skip_recommended":
    return "skip_recommended", True
```
The previous ground truth scan caught a stale reading before commit `4f26215`.

**C1+C2-LEGACY: DONE**
- `domains/s2p/scorer.py`: `False` — deleted
- `s2p_preview.py`: zero ProfileScorer imports — clean
- Both shipped in commit `4f26215`

**S2P 19/19 EFFECTIVELY 200**
Clustering and payment routers use `prefix="/api/s2p/suppliers"` — not their own prefix. Actual paths:
- `/api/s2p/suppliers/clusters` ✅
- `/api/s2p/suppliers/similarity` ✅
- `/api/s2p/suppliers/payment-strategy` ✅
- `/api/s2p/suppliers/payment-behavior` ✅

The smoke test tested wrong paths. All S2P endpoints are working.

**Transfer router: MOUNTED EVERYWHERE**
Trading L246, Purchasing, DataOps all mount `create_transfer_router(scorer_proxy)`. The 404 for `/api/transfer/patterns` was a wrong path — the route is at a different URL inside the transfer router.

**TRD-FACTOR-FALLBACK: TECHNICAL DEBT ONLY**
Fallback mapping is scrambled but never fires — `TradingPreset()` imports cleanly so the primary path always runs. No runtime impact.

### Definitive Platform Status (v31 canonical — as of 4f26215)

| Item | Status |
|---|---|
| B1-FIX (gate) | ✅ DONE |
| RL-WIRE | ✅ DONE — all 4 domains |
| S2P-PRESET | ✅ DONE — scoring + RL registries |
| D1-FORMULA | ✅ DONE — compute_theta_min in s2p_performance.py |
| SCORER-INF | ✅ DONE |
| Bootstrap shapes | ✅ DONE — both (5,4,7) |
| _PreDomain adapter | ✅ GONE |
| S2P-PERSIST | ✅ DONE |
| A1-PRESEED | ✅ DONE — skip_recommended present |
| C1+C2 legacy scorer | ✅ DONE — deleted |
| C3-BROKER CLI | ✅ DONE |
| S2P endpoints | ✅ 19/19 returning 200 |
| DataOps endpoints | ✅ 8/9 returning 200 |
| Purchasing endpoints | ✅ 6/8 returning 200 |
| Trading endpoints | ✅ mounted; path audit needed |
| TRD-FACTOR-FALLBACK | ⚠️ TECHNICAL DEBT — low risk |
| Docker | ❌ ABSENT |
| DI-1 SOURCE-PROFILER | ❌ ABSENT |
| ENT-01 CI/CD | ✅ .github/workflows EXISTS |
| Broker HTTP API | ❌ CLI only; no FastAPI routes |

### Test Suite State (v31)

| Repo | BE Tests | PW Specs | PW Tests |
|---|---|---|---|
| Trading | 641 | 21 files | ~123 |
| Purchasing | 141 | 8 files | ~47 |
| DataOps | 167 | 8 files | ~99 |
| S2P | 775 | 21 files | ~135 |
| **Total backend** | **~1,724** | | |

### Priority Recommendations for Next Batch

#### Priority 1 — PW Green (fixes remaining test failures)

The 21 PW failures from Batch H+I+J are the top priority. Now that A1-PRESEED is confirmed done and C1+C2 are clean, the remaining failures are spec-to-code mismatches from the new components. The path audit for Trading (regime, analytics, social, vix-timing actual URLs) needs to happen before writing spec fixes.

**Recommended prompt:** `TRD-PW-FIX` — read the actual mounted paths from main.py, reconcile with existing spec assertions, fix the ~8-10 still-failing tests. Expected outcome: 21 → 0 failures.

#### Priority 2 — Trading Broker HTTP API (C3-BROKER-API)

The CLI exists (Alpaca, IBKR, CSV connectors). The missing piece is FastAPI routes for `/api/broker/orders`, `/api/broker/positions`, `/api/broker/account`. These are needed for the T18-T20 execution scenarios and for the Loom demo's live-trading narrative. Without HTTP routes, the broker capability is invisible to the frontend.

**Recommended prompt:** `TRD-BROKER-HTTP` — add FastAPI router wrapping the existing connector classes. Mount at `/api/broker`. ~3 hours effort.

#### Priority 3 — S2P Test Coverage (S2P-TEST-COVERAGE)

S2P has 775 backend tests but 11 routers with zero test files. The untested surface includes `s2p.py` (core scoring/learning — 6 routes), `s2p_evolution.py` (6 routes), `s2p_governance.py` (6 routes), `s2p_explorer.py` (6 routes). These are production-critical paths with no test coverage.

**Recommended prompt:** `S2P-TEST-COVERAGE` — add test files for the 4 highest-risk routers (s2p.py, s2p_evolution.py, s2p_governance.py, s2p_explorer.py). ~20 new tests each.

#### Priority 4 — TRD-FACTOR-FALLBACK Fix

Fix the scrambled class mapping in `registry.py`. Correct mapping:
```python
"signal_alignment":   ConvictionFactor()
"market_regime":      MarketRegimeFactor()      # not ResearchDepthFactor
"position_sizing":    PositionSizeFactor()      # not TechnicalSignalFactor
"timing_quality":     TimeHorizonFactor()       # not PositionSizeFactor
"risk_reward_actual": SignalConfidenceFactor()  # needs verification
"emotional_indicator":MarketRegimeFactor()      # needs verification
"signal_confidence":  SignalConfidenceFactor()
```
15-minute fix. Low risk but worth cleaning before Loom.

#### Priority 5 — DataOps Conservation Formula (D2)

`context_router.py:220` has `23.53 / (effective_alpha * v_cat)` — an inline per-category variant. Mathematically close to canonical but not using `compute_theta_min`. Display-only, not gate-critical. Low priority but creates confusing inconsistency in the transparency panel.

#### Priority 6 — Docker / PB-02

No Dockerfile exists in any repo. Blocking for VPS deployment and the Loom demo if a cloud instance is needed. This is a full sprint item (~2 days, MAP item #15).

#### What NOT to prioritize next

- S2P-GAPS is complete — no action needed
- Transfer router paths — already mounted, just need path documentation not code changes
- RL persistence (B2/B4) — del graph_store is gone (B1 done), Thompson posteriors are wired. The remaining B2 (save/load to GraphStore) is P3 — system works correctly with in-session learning, persistence across restarts is an enhancement not a bug

### Recommended Send Order for Codex

```
Round 1 (parallel, different repos):
  TRD-PW-FIX          — fix remaining 21 PW failures (Trading e2e/)
  S2P-TEST-COVERAGE   — add tests for 4 untested S2P routers

Round 2 (after Round 1 verified):
  TRD-BROKER-HTTP     — add FastAPI broker routes (/api/broker/*)
  TRD-FACTOR-FALLBACK — fix registry.py class mapping (15 min)

Round 3 (after Round 2):
  PB-02 DOCKER        — Dockerfiles + docker-compose
```

---
*Document version: v36.0 · May 26, 2026 · Living document*
*Code + MAP v5.121 + commit 4f26215 are authoritative*

---

## Part 49 — Blocks A-G Analysis + Judgment Memory Audit (May 27, 2026)

### Block A — response_model= Regression Risk

**PASS: ScoreResponse** — all error paths raise HTTPException. Single return path has complete payload. FlexibleResponse(extra="allow") preserves extra fields.

**FAIL: LearnResponse — conservation pause returns 422**
When `_conservation_pause()` fires inside `scorer.learn()`, it returns `{"status": "paused", "reason": "conservation_red", ...}` missing all required LearnResponse fields (`decision_id, iks_before, iks_after, centroid_delta, decisions_total, outcome`). FastAPI returns 422. PW specs using `response.ok()` on `/api/learn` will fail silently.
**Fix:** Raise `HTTPException(status_code=503, detail=conservation_pause)` when paused.

**PASS: ConservationStatusResponse** — default counts (state=None) returns all required fields. ValueError → HTTPException(400).

**PASS: audit-trail** — L107 confirmed no response_model=. All other self-computation endpoints have response_model.

**PASS: Discovery, Evolution, Transfer** — all return paths produce complete dicts.

**G3: FlexibleResponse confirmed correct** — `ConfigDict(extra="allow")` preserves extra fields in ScoreResponse, LearnResponse, FingerprintResponse, TrajectoryResponse. Frontend destructuring is safe.

### Block B — PW Specs

Most specs use `clickTab + expectAnyText` — content checks, not response shape validation. `waitForResponse` calls are on `/api/score` (POST, PASS), `/api/learn` (POST + response.ok() — **RISK**), `/api/transfer/status` (GET, PASS), `/api/evolution/variants` (GET, PASS).

The learn endpoint conservation pause is the ONLY live regression risk. In normal test conditions (40 preseed decisions, GREEN conservation) this won't fire — but it's a correctness gap.

### Block C — Broker Router

**broker_router.py EXISTS** at `apps/trading/backend/app/routers/broker_router.py`:
- 6 routes: GET /status, GET /account, GET /positions, GET /orders, GET /orders/{id}, POST /sync
- All credential failures handled gracefully — `EnvironmentError` caught → `{"connected": false, "status": "disconnected"}`
- `place_order` NOT exposed via HTTP (CLI only — correct)
- MockBroker non-deterministic timestamps — PW specs should check connectivity, not timestamp text
- No import-time side effects — credentials checked only on instantiation, inside request handlers

### Block D — Transfer Detection

**D1:** `_own_domain()` reads `scorer.graph_store.domain` — all three SDK apps set this correctly.
**D2:** Fingerprint shape compatible — `factors[].name` and `factors[].sigma` correctly parsed by TransferDetector.
**D3:** `save_fingerprint()` exists in transfer.py — whether preseed calls it needs one more read.

### Block E — Drift Test

SDK KNOWN_DRIFT is current and correct (4 entries, all legitimate).

S2P_KNOWN_DRIFT has stale byte counts — test still PASSES but comments are misleading:

| File | Comment says | Actual delta |
|---|---|---|
| agent.py | "Minor diff. 1 byte" | 47 bytes (S2P larger) |
| audit.py | "-5118 bytes in S2P" | -1,805 bytes (partial backport) |
| intervention_controls.py | "-114 bytes in S2P" | **+5,513 bytes** (S2P intentionally grew) |
| feedback_base.py | "Minor diff. 3 bytes" | -475 bytes |

S2P_KNOWN_DRIFT should be updated with correct byte deltas and `intervention_controls.py` marked as intentional extension (not backport pending).

### Block F — Batch 5 Readiness

**evolve=True ALREADY WORKS:**
```python
CompoundingScorer.from_preset("trading", evolve=True)
# Evolution auto-triggers every 20 decisions
# AgentEvolver wired with ThresholdRule, FactorWeightRule, ActionBiasRule
```
OSS-EVOLVE "60 seconds to magic" is already possible. The only remaining work is UI exposure and documentation.

**D-06:** `DEFAULT_CATEGORY = "unclassified"` exists at config.py:92. The fix surface is where `ALERT_TYPE_CATEGORY_MAP` lookup falls through — needs to return `DEFAULT_CATEGORY` instead of the legacy `"credential_access"` fallback.

### Block G — Architecture Health

**G1:** No route collisions detected. Each router factory defines its own prefix.
**G2:** No module-level mutable state in broker_router.py or transfer.py. Clean.
**G3:** FlexibleResponse preserves extra fields. Plain BaseModel endpoints return exact shapes.

### Judgment Memory Architecture Validation

**All four requirements from judgment_memory_analysis.md §6 are met:**

| Requirement | Implementation | Status |
|---|---|---|
| Verified outcomes stored | `write_outcome(is_correct=bool)` → `is_correct INTEGER NOT NULL` in SQLite | ✅ |
| Per-factor quality measurement | `scorer.fingerprint()` → `FingerprintResponse.factors[].sigma` | ✅ |
| Conservation law | `count_verified()`, `count_correct()` → `compute_theta_min(override_rate, verified)` | ✅ |
| Interpretable domain-specific factors | 6-7 named factors per domain | ✅ |

**All three proposed enhancements from §7 are ALREADY SHIPPED:**

| Enhancement | Proposed | Actual Status | Evidence |
|---|---|---|---|
| Bi-temporal centroid checkpoints | "~2d effort" | ✅ SHIPPED | `_batch_decision_time_start/end` tracked + passed to `_save_centroids_checkpoint()` |
| Judgment conflict detection | "~1d effort" | ✅ SHIPPED | `from copilot_sdk.scoring.conflict import JudgmentConflict, detect_conflict`; `_detect_judgment_conflict()` in every `learn()` |
| Consolidation boundaries | "~1d effort" | ✅ SHIPPED | `consolidation_enabled: bool = False`; `flush_centroids()`; `consolidate: bool = False` on `learn()` |

The judgment_memory_analysis.md was written before reading the current code. The document describes features that are already implemented.

**Design flaws that could corrupt judgment memory — none active:**

| Potential Flaw | Status | Evidence |
|---|---|---|
| Fresh scorer per request (racing centroid updates) | ✅ FIXED | SCORER-CACHE: single `_scorer_instance` per proxy |
| S2P ephemeral storage | ✅ FIXED | SQLiteGraphStore at s2p.db |
| Wrong factor computers (fallback scramble) | ⚠️ LATENT | TRD-FACTOR-FALLBACK — only if TradingPreset import fails |
| Conservation 422 loses decision verification | ⚠️ LATENT | Conservation pause returns 422 — write_outcome never called. Centroid correctly not updated but verification lost. |
| RL posteriors reset on restart | ℹ️ ACCEPTED | RL exploration is additive, not core judgment memory. Core (centroids, verification) is durable. |

**One architectural recommendation:**
`consolidation_enabled` defaults to `False`. For the "judgment memory compounds" Loom narrative — specifically the trajectory chart showing clean per-shift centroid updates rather than noise — copilots should be initialized with `consolidation_enabled=True`. The feature exists but is opt-in. The blog/Loom story requires opting in to show the clean "morning shift: +0.034 on schema_change (12 decisions)" visualization.

---
*Document version: v36.0 · May 27, 2026 · Living document*
*Code + MAP v5.121 + commit 4f26215 are authoritative*

---

## Part 50 — Storage Architecture Analysis Through the Judgment Memory Lens

### The Framework

Judgment memory requires four things to compound correctly:
1. **Decision record** — what was scored, what was recommended
2. **Verification record** — what actually happened, is_correct
3. **Centroid geometry** — accumulated quality encoded as tensor μ(C,A,D)
4. **Conservation proof** — α·q·V ≥ θ_min, computed from 1+2

The compounding narrative from the analysis document (Month 1 → Month 3 → Month 6) requires ALL layers to persist across restarts and accumulate correctly. The storage architecture problems found throughout this session map directly onto failures at specific layers.

### The Two-Tier Storage Problem

| Layer | Storage Backend | Durability | Compounds? |
|---|---|---|---|
| Decision record | SQLite `decisions` table | ✅ Durable | ✅ |
| Verification record | SQLite `outcomes` table (`is_correct INTEGER NOT NULL`) | ✅ Durable | ✅ |
| Centroid geometry | SQLite `centroids` table + `load_latest_centroids()` | ✅ Durable | ✅ |
| Conservation gate counts | Reads from SQLite on each call | ✅ Durable | ✅ |
| Conservation dynamic monitoring (CUSUM, EWMA) | **In-memory only** | ❌ Resets | Partial |
| Thompson posteriors (RL exploration) | **In-memory only** | ❌ Resets | ❌ |
| Evolution events (rule provenance) | **In-memory only (SDK)** | ❌ Resets | ❌ |
| Promoted rule history | **In-memory only** | ❌ Resets | ❌ |
| Conflict detection history | **In-memory only** | ❌ Resets | ❌ |
| Fingerprint export (cross-domain transfer) | JSON files via `save_fingerprint()` | ✅ Durable | ✅ |

**Tier 1 (SOLID):** Decision, Verification, Centroid, Conservation gate — the foundational judgment memory. Durable and correctly implemented across all copilots post-S2P-PERSIST.

**Tier 2 (EPHEMERAL):** Conservation monitoring depth, RL exploration, Evolution events — the compounding infrastructure. All reset on restart. The Month 3 and Month 6 stories from the analysis document require Tier 2 durability.

### How Prior Storage Problems Mapped to Judgment Memory Failures

Each storage fragmentation issue found in this session had a specific judgment memory consequence:

**1. S2P InMemoryGraphStore (fixed)**
All four judgment memory layers were ephemeral for S2P. Every server restart wiped the centroid tensor — "the tensor μ(C,A,D) IS the institutional knowledge." S2P had no institutional knowledge between sessions. The platform's core claim — irreversible accumulation — was false for S2P.

**2. Trading bootstrap shape mismatch (5,3,6) vs (5,4,7) (fixed)**
Warm start from expert priors was silently disabled. On every restart, the scorer fell back to uniform 0.5 priors. The "14 decisions per cell" convergence time was never achieved — every session started from scratch. This is a judgment memory initialization failure: the pre-encoded domain knowledge was never loaded.

**3. S2P dual-scorer (fixed)**
Decisions scored by the legacy ProfileScorer couldn't be verified through CompoundingScorer, and vice versa. Verified outcomes were written to a store that a different scorer was reading centroids from. This created **verification-centroid decoherence** — the centroid geometry drifted away from what the verification record showed. The fingerprint would be computing sigma from a different population than what drove the centroid positions.

**4. del graph_store in RL presets (fixed)**
CreditAssigner and ConservationBoundedThompson received no graph_store. Thompson posteriors reset to uniform Beta(1,1) on every restart. The RL layer re-explored all actions from scratch every session — the exact opposite of compounding. Worse: CreditAssigner couldn't traverse TRIGGERED_EVOLUTION edges, so credit for correct decisions couldn't be traced back through the graph to contributing factors. The W2 flywheel (TRIGGERED_EVOLUTION edges → PatternHistoryFactorComputer) was disconnected from the credit signal.

**5. Fresh-instance-per-call before SCORER-CACHE (fixed)**
The conservation dynamic monitoring (CUSUM, EWMA λ=0.1, OLSMonitor) was reset to zero on every request. The CUSUM warmup period (50 decisions) was never completed — it restarted with each call. This meant the AMBER early warning system was permanently blind. The conservation LAW was enforced (static counts), but the MONITORING layer never accumulated. The platform was enforcing conservation without being able to detect it was approaching violation.

**6. Six GraphStore implementations — the fragmentation problem**
The multiple store pattern created capability inconsistencies. Most critically: `save_evolution_event()` exists in AGEGraphStore (SOC) but NOT in SQLiteGraphStore (Trading/Purchasing/DataOps/S2P). This means:

- SOC: evolution events persist → promoted rules survive restarts → procedural memory compounds from judgment memory ✅
- SDK copilots: evolution events are in-memory → promoted rules reset on restart → the AgentEvolver "writes the rule" story only works within a session ❌

The judgment_memory_analysis.md Month 3 story — "AgentEvolver proposes a rule: auto-escalate first-time failures from sources with reliability > 0.85 when impact > 0.7. Shadow-tested 15 decisions. 73% win rate. Promoted." — is NOT reproducible for Trading, Purchasing, DataOps, or S2P. The promoted rule exists until restart. Then gone.

### The Remaining Structural Gap

After all fixes, the storage architecture has one remaining structural gap that breaks the full judgment memory narrative:

```
Judgment Memory → Discovers pattern (centroids + fingerprint)
                → AgentEvolver proposes rule (in memory)
                → Shadow testing (in memory)
                → Promotion (in memory ← THIS IS LOST ON RESTART)
                → Procedural memory updated (in memory ← THIS TOO)
```

The first arrow (discovery) is durable. The remaining arrows are ephemeral for all SDK copilots. For the "6 months, $1.62M/year saved" story, the promoted rules must survive restarts.

**The fix is add `save_evolution_event()` to SQLiteGraphStore** — the N7 item from Part 37. This is the bridge between judgment memory (durable) and procedural memory (currently ephemeral for SDK). Without it, judgment memory discovers patterns that procedural memory immediately forgets.

### Priority Recommendations

**Priority 1 — Correctness (blocking PW):**
POST `/api/learn` returns 422 when conservation fires. Fix: raise `HTTPException(503)` on conservation pause. 5 minutes.

**Priority 2 — Judgment Memory Completeness:**
Add `save_evolution_event()` to `SQLiteGraphStore`. This is item N7 from Part 37. Enables evolution history to compound across restarts for all SDK copilots. Without this, the Month 3 and Month 6 compounding stories are impossible for Trading/Purchasing/DataOps/S2P. ~2 hours (new SQLite table + method).

**Priority 3 — RL Compounding:**
Persist Thompson posteriors via `save_centroids("_rl_state_{domain}")` or new GraphStore method. Currently all RL exploration resets on restart. The recommended Protocol-free approach (Part 45) stores posteriors as a JSON blob in the centroids table under a reserved key. ~2 hours.

**Priority 4 — Conservation Monitoring Depth:**
The CUSUM/EWMA conservation monitoring state resets on restart. The warmup period (50 decisions) restarts from zero. The AMBER early warning never fires against historical context. This is lower priority than 1-3 because the conservation GATE still works — only the early warning quality is degraded. Persisting the CUSUM state requires either: adding it to centroids JSON (trivial), or a new GraphStore method (more structured). ~1 hour.

**Priority 5 — Demo Narrative:**
Enable `consolidation_enabled=True` in preseed/demo scenarios. The trajectory chart shows noise (one data point per decision) instead of the clean "morning shift: +0.034 on schema_change (12 decisions)" narrative from the analysis document. This is opt-in and requires no code changes — just pass `consolidation_enabled=True` to `from_preset()`.

**Priority 6 — Maintenance:**
Update S2P_KNOWN_DRIFT byte counts (stale comments, test still passes). Fix DataOps context_router conservation formula. Fix Trading factor registry class mapping.

### The Clean Architecture Statement

After all fixes in Priorities 1-4, the storage architecture would have:

- **Tier 1 (Decision + Verification + Centroid):** Fully durable. All copilots. This IS the judgment memory foundation.
- **Tier 2 (Evolution + RL + Conservation monitoring):** Fully durable. Closes the month-over-month compounding gap.
- **Tier 3 (Cross-domain transfer):** Durable via fingerprint JSON files. Already working.

The platform would then correctly support the full judgment memory narrative — not just the within-session story, but the Month 1 → Month 3 → Month 6 institutional accumulation that makes the $1.62M/year case.


---

## Part 51 — Consolidated Summary: Suggestions & Priorities

### Platform State (May 27, 2026)

The platform is architecturally sound at the foundation level. All critical gaps from the past several sessions have been closed. The remaining work is about completeness, not correctness.

### What's Solid

The Tier 1 judgment memory foundation works correctly across all five copilots:
- Every decision is recorded durably (SQLite, or AGE for SOC)
- Every verified outcome is stored with `is_correct`
- Centroid geometry accumulates and persists across restarts
- Conservation gate enforces quality bounds using correct data
- Cross-domain transfer works via fingerprint JSON files
- All three judgment memory enhancements (bi-temporal checkpoints, conflict detection, consolidation) are already shipped

### Priority Fixes (Ordered)

**P1 — learn() 422 on conservation pause (5 min)**
`POST /api/learn` returns 422 when conservation fires. PW specs using `response.ok()` on `/api/learn` will fail. Fix: `raise HTTPException(status_code=503, detail=conservation_pause)` instead of returning the pause dict.

**P2 — Evolution event durability for SDK copilots (2h)**
Add `save_evolution_event()` and `get_evolution_events()` to `SQLiteGraphStore`. Without this, promoted rules and the full evolution history reset on every restart for Trading, Purchasing, DataOps, and S2P. This is the structural gap that prevents the Month 3 / Month 6 compounding story from working.

**P3 — RL posterior persistence (2h)**
Persist Thompson alpha/beta arrays via `save_centroids("_rl_state_{domain}")`. Use the Protocol-free approach (reserves a key in the existing centroids table — no schema change). Without this, RL exploration resets on every restart and never converges.

**P4 — PW spec updates for Batch H+I+J (1 session)**
21 PW failures remain from the new component additions. P1 fix reduces this number. Run PW after P1, then update remaining failing specs to match new component paths and text.

**P5 — Enable consolidation_enabled=True for demo (config change)**
Pass `consolidation_enabled=True` to `from_preset()` in preseed/demo scenarios. Transforms the trajectory chart from noise (one point per decision) to signal (one point per shift boundary). This is the visual difference between "this thing works" and "this is the compounding intelligence story."

**P6 — S2P test coverage: 11 untested routers (1-2 sprints)**
`s2p.py` (core scoring/learning), `s2p_evolution.py`, `s2p_governance.py`, `s2p_explorer.py` are the highest-risk untested routers. 69 routes with zero test coverage.

**P7 — Update S2P_KNOWN_DRIFT table (15 min)**
Stale byte counts. `intervention_controls.py` says "-114 bytes" but is now +5,513 bytes (intentional extension). Update comments to reflect actual state.

**P8 — Fix Trading factor registry fallback (15 min)**
Class implementations are scrambled (market_regime → ResearchDepthFactor). Only fires if TradingPreset import fails — low risk but wrong.

### What to Send to Codex Next

```
Round 1 (immediate, parallel):
  TRD-LEARN-FIX    — fix 422 on conservation pause (P1)
  S2P-TEST-COVERAGE — add tests for 4 critical S2P routers (P6)

Round 2 (after Round 1 verified):
  EVOLVE-PERSIST   — add save_evolution_event to SQLiteGraphStore (P2)
  RL-STATE-PERSIST — add Thompson posterior persistence via save_centroids (P3)
  TRD-PW-FIX       — update PW specs after P1 lands (P4)

Round 3 (before Loom):
  DEMO-CONSOLIDATION — enable consolidation_enabled=True in preseed (P5)
  TRD-FACTOR-FIX    — fix registry.py class mapping (P8)
  DRIFT-TABLE-UPDATE — update S2P_KNOWN_DRIFT byte counts (P7)
```

---
*Document version: v36.0 · May 27, 2026 · Living document*
*Code + MAP v5.121 + commit 4f26215 are authoritative*

---

## Part 52 — 24-Prompt Pre-classification (May 27, 2026)

### Net result: 24 planned → 16 actual prompts

7 prompts DROP (already done): D-CEL-FE (#4), TRD-YFINANCE (#14), TRD-TRUST-RADAR (#18), TRD-IBKR (#20), TRD-CSV-IMPORT (#21), TRD-JOURNAL (#22), TRD-EVIDENCE-NL (#23).

### Batch 1 Classifications

| # | ID | Classification | Key Finding |
|---|---|---|---|
| 1 | B1-FIX | PARTIAL → verify ledger args | Gate fully done (_is_conservation_safe handles all shapes). Ledger L35 call visible but args unknown. |
| 2 | S2P-GAPS | PARTIAL → fixture fields only | All 6 endpoints 200 ✅. Fixture fields unknown (PowerShell JSON parse failed). |
| 3 | LEARN-422 | **BROKEN** | Conservation pause → 422 confirmed. DataOps 23.53 already fixed (0 occurrences). |
| 4 | D-CEL-FE | **DROP** | All 5 components exist. enterprise-health exists. Both connectors have health(). |
| 5 | SC-DATA-BACKED | DONE + NEEDS FIX | SC-13/15 FOUND in all 3 apps. AE router STILL reads evolution_fixtures.json — global dict loaded from JSON, NOT from EvolutionStore. |
| 6 | SOC-TAB7 | PARTIAL | GovernanceTab fetches 6 endpoints. override_analysis lives in CompoundingTab, not GovernanceTab — potential misalignment location. |

### Batch 2 Classifications

| # | ID | Classification | Key Finding |
|---|---|---|---|
| 7 | SP-2 S2P-PYDANTIC | **NOT DONE** | 103 raw dict returns, ZERO typed responses across all 17 S2P routers. |
| 8 | SP-CLEANUP | PARTIAL | find_invoice consolidated in s2p_data_helpers ✅. audit.py has most patterns but no tamper detection. No /process-context endpoint. |
| 9 | SP-3 S2P-GS-LINK | PARTIAL | No in-memory invoice_index. link_decision_to_entity() EXISTS in both stores. Whether it's called on score/learn path unknown. |
| 10 | PUR-ENHANCE | PARTIAL | Weather reads from weather_cache.json (not live). evolve=False (not set in purchasing main.py). Only 1 router. |
| 11 | SDK-SMALL-FIXES | PARTIAL | DataOps 23.53 = 0 (ALREADY FIXED). consolidation_enabled and evolve not in preseed. Two flag enables needed. |
| 12 | STORY-PW | PARTIAL | story-flow.spec.ts EXISTS for DataOps ✅. Trading 5-act storyboard NOT DONE. |

### Batch 3 Classifications

| # | ID | Classification | Key Finding |
|---|---|---|---|
| 13 | TRD-DOMAIN-CONFIG | DONE + TINY FIX | (5,4,7) correct, categories correct, actions correct. 1 test still asserts old (5,3,6). |
| 14 | TRD-YFINANCE | **DROP** | YFinanceProvider comprehensive: regime, correlation, options, VIX. YFINANCE_AVAILABLE guard. |
| 15 | TRD-FACTORS | DONE + NEEDS FIX | **CRITICAL: market_regime.py first return is `return "volatile"` — STRING not float.** Registry mapping scrambled. |
| 16 | TRD-VERIFICATION-MODEL | PARTIAL | NormalizedTrade exists. verification_score field present. Multi-signal formula (r_multiple, execution_quality) not confirmed. |
| 17 | TRD-SYNTHETIC-DATA | **NOT DONE** | 40 trades vs 2,000 target. No generator. |
| 18 | TRD-TRUST-RADAR | **DROP** | TrustRadarPanel.tsx exists, mounted in AnalysisScreen. |

### Batch 4 Classifications

| # | ID | Classification | Key Finding |
|---|---|---|---|
| 19 | TRD-ALPACA | DONE + TINY FIX | import_trades(), normalize_orders(), NormalizedTrade ✅. alpaca-py NOT in requirements.txt. |
| 20 | TRD-IBKR | **DROP** | IBKRConnector with IB_AVAILABLE graceful fallback. |
| 21 | TRD-CSV-IMPORT | **DROP** | CSVConnector: import_flexible(), auto-detect, NormalizedTrade. |
| 22 | TRD-JOURNAL | **DROP** | /trades, /trades/{id}, /analytics. JournalScreen with filters. Full stack. |
| 23 | TRD-EVIDENCE-NL | **DROP** | TradingTemplateEngine with trend_following/mean_reversion. GET /evidence/{id}. |
| 24 | S2P-M4 INTENT | PARTIAL | ~5-8 intents (L16-L54 = 38 lines). Dict-based, no IntentType enum. Target: 15-18 + enum. |

### Critical Finding: market_regime.py returns a STRING

`market_regime.py` first return statement: `return "volatile"` — not a float in [0,1].
Any code calling MarketRegimeFactor.compute() directly gets a string. numpy operations on this string will throw TypeError. This is a silent data corruption risk when the factor computer is called outside the registry fallback path.

### Critical Finding: AE Router Still Using Fixture JSON

Five separate fixture reads in ae_router.py:
```python
_evolution_fixtures = {}  # global module-level dict
_evolution_fixtures = json.loads(path.read_text())  # loaded from file
payload = _get_fixtures()["evolution_fixtures.json"]  # served to frontend
```
SC-13 (RuleGenealogyTree) and SC-15 (RuleLifecycle) show data from fixture files, not from AgentEvolver. The 12 evolution API refs in trading's api.ts call endpoints that return fixture data. This means the Month 3 "promoted rule" story shows synthetic data, not real evolution history.

### Recommended Codex Send Order

```
Immediate:
  LEARN-422     — raise HTTPException(503) on conservation pause (5 min)

Round 1 (parallel):
  TRD-FACTOR-FIX  — fix market_regime string return + fix registry mapping
  SDK-SMALL-FIXES — consolidation_enabled=True + evolve=True in preseed (15 min)
  SP-PYDANTIC     — add Pydantic response models to all 17 S2P routers

Round 2:
  AE-REAL-DATA    — wire AE router to evolver.get_evolution_history()
  TRD-SYNTHETIC   — generate 2,000 trades with 6 behavioral patterns
  STORY-PW-TRD    — Trading 5-act storyboard spec (copy DataOps pattern)
  SP-PROCESS-CTX  — add /process-context endpoint to S2P

Round 3:
  S2P-M4-INTENT   — expand to 15-18 intents + IntentType enum
  PUR-ENHANCE     — evolve=True + live weather verification
  BUNDLE-TINY     — 1 stale test + requirements.txt gaps

Verify first before writing prompts:
  B1-FIX          — grep ledger L35 full call → likely DROP
  SP-GS-LINK      — grep link_decision_to_entity usage in s2p.py → scope or DROP
  SOC-TAB7        — read Tab 1 endpoint list → scope fix precisely
  TRD-VERIFY      — grep r_multiple/execution_quality → scope multi-signal formula
  S2P-GAPS        — Python fixture field check → scope or DROP
```

---
*Document version: v36.0 · May 27, 2026 · Living document*
*Code + MAP v5.121 + commit 4f26215 are authoritative*

---

## Part 53 — Five Grep Verdicts + P6 Architecture (May 27, 2026)

### Five Grep Final Verdicts

| Check | Result | Action |
|---|---|---|
| B1-FIX ledger keyword args | ✅ Already keyword: `domain=self.domain, event_type=..., rule_name=..., variant_id=..., metadata=...` | **DROP** — B1-FIX fully done |
| SP-GS-LINK `link_decision_to_entity` in s2p.py | ❌ Zero occurrences | **ADD to Round 2** — method exists in stores, never called on score/learn path |
| SOC-TAB7 Tab 1 endpoints | Tab 1 fetches ONE endpoint: `/api/soc/detection-engineering` | **SCOPE DOWN** — Tab 7/Tab 1 mismatch is not the issue; override_analysis lives in CompoundingTab (Tab 4), not Tab 1 |
| TRD-VERIFY r_multiple formula | ❌ Zero occurrences of r_multiple, 0.3×outcome, 0.4×execution_quality | **ADD to Round 3** — multi-signal formula from PD v1.0 Appendix C.1 not implemented |
| S2P-GAPS fixture path | FileNotFoundError — file is at `$CLAUDE_S2P\data\` not `\backend\data\` | Re-run with correct path before closing |

### P6 — save_evolution_event: The Architecture Fix

**Root cause:** SQLiteGraphStore doesn't implement `save_evolution_event()`. The ledger wraps its call in `try/except` — so every evolution event for every SDK copilot silently fails today. Nothing is written. Nothing compounds.

**The fix:** One new SQLite table, two methods on SQLiteGraphStore, two stub methods on InMemoryGraphStore.

```sql
CREATE TABLE IF NOT EXISTS evolution_events (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    domain        TEXT    NOT NULL,
    event_type    TEXT    NOT NULL,
    rule_name     TEXT    NOT NULL,
    variant_id    TEXT,
    metadata_json TEXT    NOT NULL DEFAULT '{}',
    created_at    REAL    NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_evolution_events_domain_rule
    ON evolution_events (domain, rule_name, created_at DESC);
```

```python
# SQLiteGraphStore — two new methods:
def save_evolution_event(self, domain, event_type, rule_name,
                          variant_id=None, metadata=None) -> None:
    with self._connect() as conn:
        conn.execute(
            "INSERT INTO evolution_events (domain, event_type, rule_name, "
            "variant_id, metadata_json, created_at) VALUES (?,?,?,?,?,?)",
            (domain, event_type, rule_name, variant_id,
             json.dumps(metadata or {}), time.time()),
        )

def get_evolution_events(self, domain, rule_name=None, limit=50) -> list[dict]:
    sql = ("SELECT domain, event_type, rule_name, variant_id, "
           "metadata_json, created_at FROM evolution_events "
           "WHERE domain=?" + (" AND rule_name=?" if rule_name else "") +
           " ORDER BY created_at DESC LIMIT ?")
    args = (domain, rule_name, limit) if rule_name else (domain, limit)
    with self._connect() as conn:
        rows = conn.execute(sql, args).fetchall()
    return [{"domain": r["domain"], "event_type": r["event_type"],
             "rule_name": r["rule_name"], "variant_id": r["variant_id"],
             "metadata": json.loads(r["metadata_json"]),
             "created_at": r["created_at"]} for r in rows]

# InMemoryGraphStore — two stub methods + __init__ list:
# self._evolution_events: list[dict] = []
def save_evolution_event(self, domain, event_type, rule_name,
                          variant_id=None, metadata=None) -> None:
    self._evolution_events.append({"domain": domain, "event_type": event_type,
        "rule_name": rule_name, "variant_id": variant_id,
        "metadata": metadata or {}, "created_at": time.time()})

def get_evolution_events(self, domain, rule_name=None, limit=50) -> list[dict]:
    events = [e for e in self._evolution_events if e["domain"] == domain]
    if rule_name:
        events = [e for e in events if e["rule_name"] == rule_name]
    return events[-limit:]
```

**Tests needed (6 minimum):** save_and_retrieve_by_domain, retrieve_by_rule_name, limit_respected, domain_isolation, empty_domain_returns_empty, metadata_roundtrip.

**Risk: near zero.** Ledger already has try/except — adding the method makes it succeed; not adding it silently fails (current state). No existing tables touched. Append-only new table.

**What this unlocks in sequence:**
1. Evolution events stop being silently dropped — immediate on deploy
2. `evolver.get_evolution_history()` returns real data — AE-REAL-DATA (P5) unblocked
3. Promoted rules survive restarts — Month 3/Month 6 story is now real for all SDK copilots
4. RuleGenealogyTree (SC-13) shows actual promotion history, not synthetic fixtures
5. Judgment memory → procedural memory handoff closes for Trading/Purchasing/DataOps/S2P

**Effort: ~2 hours. Codex files:** `copilot_sdk/graph/sqlite_store.py`, `copilot_sdk/graph/memory_store.py`, new `tests/graph/test_evolution_events.py`.

---

## Part 54 — Consolidated Suggestions & Priorities (v36.0 · May 29, 2026) [SEE PART 75 FOR CURRENT STATE]

### ⚡ Four Things The Next Developer Session Needs To Know

> **1. Fix Trading demo bundle first (#102, 15 min).** The demo is broken for first-start. Trading bundle has d=7 factor vectors; Trading preset is (5,4,10). Centroids silently fall back to flat 0.5. Fix: update `regenerate_demo_bundles.py` to include 3 options factors, re-run, commit. **Do this before anything else.**

> **2. Three AE variant configs (#104, #105, #107) in 1.5d — fixes a platform-wide gap across all copilots simultaneously.** Every copilot has AgentEvolver mounted but zero domain-specific VariantSpec dimensions. S2P: add escalation_criteria + triage_weights (0.5d). Trading: add alert_threshold + pattern_sensitivity + regime_boundary (0.5d). DataOps: add alert_routing_threshold + escalation_criteria + pattern_sensitivity (0.5d). Same pattern, three files, one Codex session.

> **3. DI-1 SOURCE-PROFILER is unblocked — start immediately.** D-CEL confirmed DONE (ApplyFixModal renders sapResponse). DI-1 (2wk) is the highest-leverage item in the MAP: closes 4 DataOps scenario gaps (D-I1, D-I2, D-I14, D-I15) simultaneously and unblocks every other DI item. No prerequisites remain. Write the Codex prompt now.

> **4. G12 Situation Analyzer is the strategic investment.** Without it, S2P is a better AP automation story. With it (S14 "Not a Script — A Decision"), the demo shows procurement AI reasoning from context — "Copper rose 4.8%. Contract §7.3 allows pass-through. Within bounds. Accept." No competitor can show this. 3-4wk, next major build after Sprint 1 quick wins.

---

### Platform State

**~48 of ~70 tracked prompts are confirmed DROPs** (MAP v5.139 — includes S2P review session). PW: 260/2/5flaky/1skip baseline (pre-B10 FE). Trading rerun needed after B10 FE components (#89). Test baselines: SDK 788, TRD 704, PUR 147, DOPS 175, S2P 854. 

**Methodology rule (Part 63):** Parts 1-38 (architecture) reliable. Parts 41-62 PW hypotheses ~17% accurate — codebase moves faster. **Pre-check-driven prompts only. Grep confirms broken state before any fix is written.** Pre-checks prevented 4 wrong fixes in R2 (T1 analytics mapping wrong — normalizer handles it; D2 variantId likely wrong — normalizer handles it; D1/D3 already done before analysis).

---

### The Three Things That Matter Most

**1. Two remaining PW hard failures — 20 min, both spec issues**
Backend is clean. The 2 failures are assertion problems in test specs:
- **#97 Trading flows:41** (5 min): `waitForFunction` checks `!textContent.includes("Loading")` on `<main>` — too broad. Scope to loading spinner element. Add to P2 SDK-TRADING-FE.
- **#98 DataOps flows:332** (15 min): Pattern Origin panel expects `/SOC|S2P/i` but startup events have no `source_copilot` field. Add `source_copilot: "SOC"` to one startup seed event.

**2. DEMO-BUNDLE — 1.5h across 3 Codex prompts (copilot-sdk repo, MAP #NEW)**
Eliminates `preseed_all_copilots.py` as runtime dependency. Replaces 1,200 HTTP calls per session with ~50ms SQLite restore at startup. Fully unblocked. DataOps `main.py` has the reference pattern (`_auto_seed_if_needed` + `_seed_demo_evolution_events_if_needed`). See duration breakdown below.

**3. Batch 10 Round 0 — SOC + S2P PW gates**
Trading gate passed. SOC (#15) and S2P (#17) still pending. Run before any Codex work.

---

### PW Round 2 — What Actually Happened

**T1 hypothesis was wrong.** Both Trading and DataOps have recursive snake→camelCase normalizers in api.ts — manual mapping was already handled. The actual cascade source was **T-CORS**: `trade_metadata.json` existed (431.6KB) but contained malformed JSON. `_load_json_optional` only caught `FileNotFoundError`, not `JSONDecodeError` → 500 → Promise.all → all panels hidden → 22 failures. One endpoint fix cleared 22 in one shot.

**D2 hypothesis was likely also wrong.** Not mentioned in R2 results — recursive normalizer converts `variant_id` → `variantId` automatically.

**R2 actual fixes:** T-CORS (JSONDecodeError catch) + D-SCHED (confirmed done at startup, pre-check) + D-TRANSFER (confirmed done, pre-check).

**Standing rule #42:** Both Trading/DataOps api.ts have recursive snake→camelCase normalizers. No manual mapping needed.
**Standing rule #43:** `_load_json_optional` must catch BOTH `FileNotFoundError` AND `JSONDecodeError`.

---

### Demo Bundle — Duration Breakdown

| Prompt | What | Duration |
|---|---|---|
| Prompt 1 | `copilot_sdk/demo/__init__.py` + `bundle.py` — `restore_bundle_if_empty()` with exact SQLite column names | 30 min |
| Prompt 2 | `scripts/regenerate_demo_bundles.py` — reads seed JSONs, builds centroid tensor, outputs 3 bundle files | 30 min |
| Prompt 3 | Lifespan wiring: Trading/Purchasing/DataOps `main.py` + skip-when-warm/restore-when-cold tests | 30 min |
| **Total** | **3 prompts, 1 Codex session** | **~1.5h** |

`centroids_json` format: `json.dumps(tensor.tolist())` — confirmed from `load_latest_centroids()`. Reference implementation: DataOps `main.py` `_auto_seed_if_needed()` + `_seed_demo_evolution_events_if_needed()`.

---

### Full Priority Stack (v36.0 — post R2)

```
Immediate:
  #97 PW-TRADING-FLOWS41   5 min   flows:41 scope waitForFunction to spinner (add to P2)
  #98 PW-DATAOPS-FLOWS332  15 min  add source_copilot:"SOC" to one startup seed event
  DEMO-BUNDLE             1.5h     3 prompts: bundle.py → regenerate → lifespan wiring

Batch 10 Round 0 (gate):
  P1 PW-GATES              0.5d    SOC #15 + S2P #17 PW runs (Trading #16 PASSED)

Batch 10 Round 1 (parallel):
  P2 SDK-TRADING-FE        1.5d    #89 TRD-SC-DATA + #19 STORY-PW Trading + #97 flows:41
  P3 S2P-QUICK-COMPLETE    3d      #42 S2P-G10 + #51 S2P-F22

Batch 10 Round 2 (parallel):
  P4 TRD-DATA-FOUNDATION   3d      #21 TRD-VERIFICATION-MODEL + #22 TRD-SYNTHETIC-DATA
  P5 S2P-M4 INTENT         1wk     #46 IntentType enum + 5→15-18 intents

Batch 10 Round 3 (parallel):
  P7 TRD-OPTIONS-FACTORS   1wk     #30 d=7→d=10 options greeks
  P6 S2P-AE-VARIANTS       1wk     #44 wire evolver to SDK AgentEvolver

Batch 10 Round 4:
  P8 S2P-AUDIT-EXPORT      1wk     #40 SOX-ready combined export endpoint

After Batch 10:
  SDK-SMALL-FIXES          15 min  consolidation_enabled=True + evolve=True in preseed
  SP-PYDANTIC              2-3h    103 raw dicts → typed responses, 17 S2P routers
  SP-GS-LINK               1h      link_decision_to_entity on S2P score/learn path
  TRD-SYNTHETIC-DATA       0.5d    40 → 2,000 trades (part of P4)
  TRD-BROKER-ORDER         1h      POST /orders to broker_router
  S2P-TEST-COVERAGE-2      1 sess  12 routers, 53 untested routes
  BUNDLE-TINY              30 min  1 stale test + KNOWN_DRIFT byte counts

Lower priority:
  SP-11 PROCESS-CTX        1h      SP-4 AUDIT-BACKPORT        1h
  S2P-F11 AUDIT-EXPORT     1h      S2P-F8 FACTOR-PROPOSER     2h
  SOC-TAB7                 1h      TRD-MULTI-TRADER           1wk (rescoped)
```

---

### MAP Changes (v5.136 → v5.137)

**NEW items:**

| MAP# | ID | Effort | What |
|---|---|---|---|
| #89 | TRD-SC-DATA | 2h | Wire SC-11/12/14/16 to Trading frontend |
| #97 | PW-TRADING-FLOWS41 | 5 min | flows:41 waitForFunction scope too broad |
| #98 | PW-DATAOPS-FLOWS332 | 15 min | flows:332 add source_copilot to seed event |

**DONE this session (MAP v5.137 confirmed):**

| MAP# | ID | Evidence |
|---|---|---|
| #12 | SC-DATAOPS-LIVE | All 4 SC components live, /api/self/* wired |
| #14 | CLAIMS-UPDATE | Manual, May 28 |
| #18 | STORY-PW DataOps | story-flow.spec.ts 8 tests |
| #20 | TRD-FACTORS | Both dicts correct |
| #25 | TRD-CLI | 23 commands, pip-installable |
| #26 | TRD-PYPI | pyproject.toml entry_points |
| #28 | TRD-CROSS-INSIGHTS | analytics.py cross_insights() |
| #29 | TRD-EXECUTION-ANALYSIS | analytics.py execution_analysis() |
| #31 | TRD-TRADINGVIEW-HOOK | webhook.py 291L |
| #35 | SP-10 INVOICE-HELPERS | s2p_data_helpers.py |
| #45 | S2P-G14 RL-CALIBRATION | S2PRewardFunction wired |
| #53 | PU-3 WEATHER-VERIFY | use_live=True → open-meteo.com |
| #54 | PU-5 EVOLVE-DEMO-PUR | evolve=True at L201 |
| #90 | SDK-PW-FIX | 8 fixes R1+R2, 31→2 failures |
| — | LEARN-422 | 200+paused (no 422) |
| — | D-06-UNMAPPED | DEFAULT_CATEGORY |
| — | EVOLVE-PERSIST | sqlite+memory+ledger+tests |
| — | D3-TRANSFER-STATUS | fixture wired |
| — | D1-SCHEDULING | startup seed hook |

**RESCOPED (v5.136):** #27 3wk→1wk, #30 2wk→1wk, #42 1wk→2d, #44 2-3wk→1wk, #48 1wk→3d, #50 1wk→3d, #51 3d→1d. Total saved: ~6 weeks.

**TRD-PW-FULL-RUN #16:** ✅ GATE PASSED (106/1/4flaky).

---

### PW Status

| Suite | Baseline | Post R2 | Remaining |
|---|---|---|---|
| Purchasing | 46/1/0 | **47/0/0 ✅** | 0 |
| S2P Preview | 10/1/0 | **11/0/0 ✅** | 0 |
| DataOps | 92/6/1 | **96/1/1flaky ✅** | #98 spec fix (15 min) |
| Trading | 87/23/0 | **106/1/4flaky ✅** | #97 spec fix (5 min) |

---

### What's Already Done — Don't Rebuild

PW R1+R2 shipped (8 fixes). EVOLVE-PERSIST shipped. LEARN-422 shipped. D-06 shipped. D1-SCHED shipped. D3-TRANSFER shipped. Recursive normalizers in both api.ts files handle snake→camelCase — don't add manual mapping.

---

### Storage Architecture — FULLY CLOSED

Both Tier 2 gaps confirmed closed: RL posteriors (save_rl_state/load_rl_state) + evolution events (save_evolution_event in both stores + ledger). Platform supports full Month 1→3→6 compounding narrative today.

---

### DROP Totals (MAP v5.137 authoritative)

| Batch | DROPs | MAP Items |
|---|---|---|
| Original list | 7 | TrustRadar, yfinance, IBKR, CSV, Journal, Evidence NL, D-CEL-FE |
| Batch 6-10 (Parts 55-56) | 5 | RL-STATE-PERSIST, TRD-SERVICE-VERIFY, TRD-REALTIME-SCORE, TRD-REGIME-RECOMMEND, TRD-EARNINGS-SUBCAT |
| Deep Analysis (Part 56) | 13 | #12,14,18,20,25,26,28,29,31,35,45,53,54 |
| Parts 57-59 | 1 | DO-7 |
| Parts 61-62 | 5 | LEARN-422, D-06, EVOLVE-PERSIST, D3-TRANSFER, D1-SCHED |
| PW R1+R2 (#90) | 1 | SDK-PW-FIX (8 fixes shipped) |
| **Total** | **32** | **of ~54 queued prompts (MAP v5.137)** |

---

## Part 55 — Batch 6-10 Pre-classification (May 27, 2026)

### Critical Corrections From Scan

**TRD-FACTORS: market_regime.compute() returns float correctly.** Prior finding wrong — we were reading `classify_regime()` helper function whose first return is `"volatile"`. `MarketRegimeFactor.compute()` returns `clamp(accuracy.get(str(regime), 0.5))` — float. Registry scramble is still real (5 of 7 names map to wrong class). Scope: registry.py only.

**RL-STATE-PERSIST: Already wired, just needs store methods.** `ConservationBoundedThompson` already calls `save_rl_state(key, data)` after every update() and `load_rl_state(key)` in __init__. `get_priors()` returns `{alpha, beta, conservation_status}`. Work is implementing those 2 methods on SQLiteGraphStore + InMemoryGraphStore. NOT Protocol-free — save_centroids requires domain+category, can't double as key-value store.

**TRD-REALTIME-SCORE is fully done.** `prescore.py` is a complete implementation: POST /api/trading/prescore with regime detection, subcategory classification, compute_factors, options analytics, NL evidence, warnings. DROP.

**AE-REAL-DATA is DataOps-only.** Trading and Purchasing have no ae_router. Only DataOps has one (18 fixture reads). evolver.get_evolution_history() EXISTS at L106.

**Financial impact reads fixtures.** s2p_pvg.py `/financial-impact` returns `_financial_impact_from_fixtures()` — hardcoded, not real per-decision economics.

**12 S2P routers missing tests** (not 4 as previously tracked). 53 routes with zero test coverage.

**D-06 exact location confirmed.** soc.py L1129: `category = row.get("category") or "credential_access"`. Fix: `or DEFAULT_CATEGORY`. One line.

### Classification Table

| # | ID | Classification | Action |
|---|---|---|---|
| 1 | LEARN-422 | BROKEN | FIX — raise HTTPException(503) on conservation pause |
| 2 | EVOLVE-PERSIST | NOT DONE | FULL — 2 methods × 2 stores + table |
| 3 | RL-STATE-PERSIST | **DONE** | **DROP** — SQLiteGraphStore.save_rl_state() at :484, load_rl_state() at :503, rl_state table at :115. InMemory _rl_state dict + methods at :186. Tests in test_rl_persistence.py. Confirmed by Codex audit. |
| 4 | TRD-FACTORS-FIX | DONE + NEEDS FIX | FIX — registry.py class mapping only (compute() returns float) |
| 5 | S2P-TEST-COVERAGE-2 | NOT DONE | FULL — 12 routers, 53 routes |
| 6 | D-06-UNMAPPED | BROKEN | FIX — soc.py L1129 one-line fix |
| 7 | SC-DATA-BACKED DataOps | DONE + NEEDS FIX | FIX — wire ae_router to evolver |
| 8 | AE-REAL-DATA | PARTIAL (DataOps only) | SCOPE DOWN — DataOps ae_router only |
| 9 | SDK-SMALL-FIXES | PARTIAL | SCOPE DOWN — 2 flag enables in preseed |
| 10 | SOC-TAB7 | PARTIAL | SCOPE DOWN — CompoundingTab/GovernanceTab alignment |
| 11 | STORY-PW | PARTIAL | SCOPE DOWN — Trading storyboard only |
| 12 | SP-PYDANTIC | NOT DONE | FULL — 103 raw dicts → typed |
| 13 | SP-4 AUDIT-BACKPORT | PARTIAL | SCOPE DOWN — tamper detection text only (verify_chain exists) |
| 14 | SP-11 PROCESS-CTX | PARTIAL | SCOPE DOWN — standalone GET /process-context/{id} endpoint |
| 15 | SP-3 GS-LINK | NOT DONE | FIX — call link_decision_to_entity in s2p.py |
| 16 | PUR-ENHANCE | PARTIAL | SCOPE DOWN — evolve=True + weather |
| 17 | BUNDLE-TINY | NOT DONE | FIX — stale test + requirements + KNOWN_DRIFT |
| 18 | TRD-SERVICE-VERIFY | DONE + WELL-DESIGNED | **DROP** |
| 19 | TRD-FACTORS verify | DONE + NEEDS FIX | FIX — registry only (after #4) |
| 20 | TRD-VERIFICATION-MODEL | NOT DONE | FULL — r_multiple + execution_quality formula |
| 21 | TRD-SYNTHETIC-DATA | NOT DONE | FULL — 40 → 2,000 trades + generator |
| 22 | TRD-BROKER-ORDER | DONE + NEEDS FIX | FIX — add POST /orders to broker_router |
| 23 | TRD-REALTIME-SCORE | DONE | **DROP** |
| 24 | S2P-F8 FACTOR-PROPOSER | NOT DONE | FULL — DK weights → swap recommendations |
| 25 | TRD-AGENT-EVOLVER | PARTIAL | SCOPE DOWN — wire evolve=True to scorer |
| 26 | TRD-REGIME-RECOMMEND | DONE | **DROP** |
| 27 | TRD-EARNINGS-SUBCAT | DONE | **DROP** |
| 28 | S2P-F10 FINANCIAL-IMPACT | DONE + NEEDS REDESIGN | REDESIGN — real per-decision computation |
| 29 | S2P-F11 AUDIT-EXPORT | PARTIAL | SCOPE DOWN — combined SOX export endpoint |
| 30 | S2P-M4 INTENT-TAXONOMY | PARTIAL | SCOPE DOWN — 5 → 15-18 intents + IntentType enum |

### Saves: 5 DROPs from Batch 6-10

Total DROPs from 30-prompt batch: #3 RL-STATE-PERSIST (confirmed done by Codex), #18, #23, #26, #27 = **5 saved**. Combined with prior document: **12 of 54 total prompts across both sets are DROPs.**

### Codex Baseline Test Counts (Confirmed May 27, 2026)

| Suite | Count | vs Prior Scan |
|---|---|---|
| SDK root | 765 passed, 1 skipped | +124 vs prior 641 |
| Trading | 655 passed | +14 vs 641 |
| Purchasing | 143 passed | +2 vs 141 |
| DataOps | 170 passed | +3 vs 167 |

New tests have landed since the last manual count. These are the authoritative baselines for the next implementation batch.

### Revised Send Order (18 actual prompts — RL-STATE-PERSIST is a DROP)

```
Immediate (unblock PW + fix silent bug):
  LEARN-422              — 5 min
  D-06-UNMAPPED          — 2 min (soc.py L1129 one-line)

Round 1 (parallel):
  EVOLVE-PERSIST         — 2h  ← architecture gate for AE-REAL-DATA
  TRD-FACTORS-FIX        — 30 min (registry.py only)
  SDK-SMALL-FIXES        — 15 min (2 flags in preseed)
  SP-PYDANTIC            — 3h  (103 raw dicts)

Round 2 (after Round 1):
  AE-REAL-DATA           — 2h  (DataOps ae_router → evolver; needs EVOLVE-PERSIST)
  SP-GS-LINK             — 1h
  TRD-BROKER-ORDER       — 1h
  S2P-TEST-COVERAGE-2    — 1 session (12 routers)
  TRD-SYNTHETIC-DATA     — half day

Round 3 (before Loom):
  TRD-VERIFICATION-MODEL — 2h
  TRD-AGENT-EVOLVER      — 2h
  S2P-M4 INTENT          — 2h
  S2P-F10 FINANCIAL      — 2h (redesign from fixtures to real)
  BUNDLE-TINY            — 30 min
  STORY-PW Trading       — 2h
  SP-11/SP-4/S2P-F11/S2P-F8/PUR-ENHANCE/SOC-TAB7 — lower priority
```

---
*Document version: v36.0 · May 28, 2026 · Synopsis updated — Parts 48-55*
*Code + MAP v5.131 + commit 4f26215 are authoritative*

---

## Part 56 — Deep Analysis v36.0: 35-Item Classification (May 27-28, 2026)

### Critical Finding: 12 More DROPs — Codebase Is Far Ahead of Queue

Running total: **24 of ~54 queued prompts are confirmed DROPs.** The codebase has been advancing faster than the analysis documents. Previous scans are stale on several items.

### Corrections to Prior Findings

**DO-7 (DataOps conservation formula): NEEDS RE-VERIFICATION**
Part 14 options scan surfaced `context_router.py: theta_min_proxy = 23.53 / (effective_alpha * v_cat)` via accidental "theta" match in a grep for options greeks. The earlier "0 occurrences" for DataOps 23.53 was likely wrong. Re-run: `Select-String "$env:CLAUDE_SDK\apps\dataops\backend\app\context_router.py" -Pattern "23\.53"` before sending DO-7 to Codex.

**TRD-FACTORS: Already fixed, not by our prompt.**
Both `_PRESET_FACTOR_COMPUTERS` and `_FALLBACK_FACTOR_COMPUTERS` are identical and correctly mapped. No prompt needed.

**DataOps SC-11/12/14/16: All live, not a gap.**
CentroidTimelineChart, AccuracyAlertPanel, AuditTrailViewer, DecisionExplorer all fetch from real `/api/self/*` endpoints. `mount_self_computation_router` wired in main.py.

### New Untracked Gap: TRD-SC-DATA

Trading frontend has ZERO SC-11/12/14/16 components. No centroid timeline, accuracy alerts, decision explorer, or audit trail in Trading frontend. DataOps has all four; Trading has none. This is not in the current queue.

### S2P Is More Complete Than Tracked

Previously undocumented: `OutcomeReceipt` model, `receipt_store` service, `s2p_evolver` service with `record_triage_outcome`/`check_promotion`/`get_evolution_summary`, `S2PRewardFunction()` wired in main.py. S2P has custom reward function AND receipt infrastructure.

### 35-Item Classification Table

| # | MAP# | ID | Classification | Action |
|---|---|---|---|---|
| 1 | 12 | SC-DATAOPS-LIVE | **DROP** | SC-11/12/14/16 all live with real endpoint calls |
| 2 | 14 | CLAIMS-UPDATE | DOCS ONLY | No Codex — manual update |
| 3 | 15 | SOC-PW-RERUN | READY | After D-06+TAB7 land |
| 4 | 16 | TRD-PW-FULL-RUN | READY | factors+registry fixed, broker GET routes exist |
| 5 | 17 | S2P-PW-RUN | READY | Port 5177 configured |
| 6 | 18 | STORY-PW DataOps | **DROP** | story-flow.spec.ts exists (8 tests) |
| 7 | 19 | STORY-PW Trading | NOT DONE | No storyboard spec |
| 8 | 20 | TRD-FACTORS | **DROP** | Registry fully corrected — both dicts identical and correct |
| 9 | 21 | TRD-VERIFICATION-MODEL | NOT DONE | r_multiple zero occurrences confirmed |
| 10 | 22 | TRD-SYNTHETIC-DATA | NOT DONE | 40 trades, no generator |
| 11 | 25 | TRD-CLI | **DROP** | 23 commands, ci-trading entry point, Apache-2.0, 64 tests |
| 12 | 35 | SP-10 INVOICE-HELPERS | **DROP** | Consolidated in s2p_data_helpers.py |
| 13 | 38 | S2P-F8 FACTOR-PROPOSER | NOT DONE | DK weights readable, no swap logic |
| 14 | 39 | S2P-F10 FINANCIAL-IMPACT | REDESIGN | _financial_impact_from_fixtures() confirmed |
| 15 | 26 | TRD-PYPI | **DROP** | pyproject.toml, ci-trading entry point, Apache-2.0 |
| 16 | 29 | TRD-EXECUTION-ANALYSIS | **DROP** | analytics.py has execution_analysis + cross_insights |
| 17 | 30 | TRD-OPTIONS-FACTORS | PARTIAL | options.py (185L) + greeks in evidence. d=7 tensor unchanged. |
| 18 | 31 | TRD-TRADINGVIEW-HOOK | **DROP** | webhook.py (291L): POST/tradingview + factor mapping + history |
| 19 | 40 | S2P-F11 AUDIT-EXPORT | PARTIAL | hash chain + verify_chain + SOX flags. No combined export endpoint. |
| 20 | 41 | S2P-F14 LEAD-TIME | PARTIAL | lead_time_weeks + cycle_time_hours exist. Per-supplier GR/PO missing. |
| 21 | 42 | S2P-G10 OUTCOME-RECEIPT | PARTIAL | OutcomeReceipt + receipt_store + record_triage_outcome exist |
| 22 | 27 | TRD-MULTI-TRADER | PARTIAL | social.py (9 routes), TraderProfileService, Portfolio node. NormalizedTrade has no trader_id. |
| 23 | 28 | TRD-CROSS-INSIGHTS | **DROP** | analytics.py cross_insights() IS the feature |
| 24 | 43 | S2P-G12 SITUATION-ANALYZER | NOT SCANNED | 47-node graph traversal — needs separate scan |
| 25 | 44 | S2P-G13 AE-VARIANTS | PARTIAL | evolver_config.py + s2p_evolver service exist. Dimension coverage unknown. |
| 26 | 45 | S2P-G14 RL-CALIBRATION | **DROP** | S2PRewardFunction wired in main.py and app.state |
| 27 | 46 | S2P-M4 INTENT-TAXONOMY | PARTIAL | 5 intents, dict-based, no enum. Target 15-18. |
| 28 | 53 | PU-3 WEATHER-VERIFY | **DROP** | use_live=True calls open-meteo.com. Cache + live both work. |
| 29 | 47 | S2P-F18 PROCESS-TECH | PARTIAL | Process context in score. WHERE/WHY/WHAT/LEARN needs Celonis. |
| 30 | 48 | S2P-F19 Payment timing | PARTIAL | Routes exist (payment-strategy, payment-behavior). Fixture-based. |
| 31 | 49 | S2P-F20 OPTIMIZER-API | NOT SCANNED | No code found |
| 32 | 50 | S2P-F21 Disruption sim | PARTIAL | 4 routes: scenarios, what-if, impact-summary |
| 33 | 51 | S2P-F22 Compliance | PARTIAL | governance router has compliance + sox_readiness score |
| 34 | 52 | SP-12 S2P-NL-TRUST | NOT DONE | Zero NL infrastructure in S2P |
| 35 | 54 | PU-5 EVOLVE-DEMO | **DROP** | evolve=True at L201 in purchasing main.py |

### DROPs Summary

New DROPs this scan: #1, #6, #8, #11, #12, #15, #16, #18, #23, #26, #28, #35 = **12 DROPs**
Running total: **24 of ~54 prompts are DROPs**

### PW Status

| Suite | Specs | Tests | Status |
|---|---|---|---|
| Trading | 21 spec files | ~123 tests | READY after TRD-PW-FULL-RUN |
| Purchasing | 8 spec files | ~47 tests | READY |
| DataOps | 8 spec files | ~99 tests | READY (7 data-dependent skips normal) |
| S2P | 21 spec files | ~135 tests | READY — port 5177 configured |

### Coverage Numbers (authoritative from Codex baseline)

| Copilot | Routes | Tests | Untested routers |
|---|---|---|---|
| Trading | 38 | 661 | data_import.py (5 routes) |
| Purchasing | 6 | 143 | None |
| DataOps | 4 (routers/) + more in app/ root | 171 | None in routers/ |
| S2P | 76 | 775 | 9 routers, 44 routes |

### What To Verify Before Next Batch

```powershell
# Re-verify DO-7 (DataOps 23.53 formula — prior result may be wrong)
Select-String "$env:CLAUDE_SDK\apps\dataops\backend\app\context_router.py" -Pattern "23\.53|theta_min_proxy"

# Verify Trading SC-DATA gap (untracked)
Get-ChildItem "$env:CLAUDE_SDK\apps\trading\frontend\src" -Filter "*.tsx" -Recurse | `
    Select-String -Pattern "centroid.history|accuracy-by-category|self/decisions|audit.trail" | `
    Select-Object -First 5
```

---
*Document version: v36.0 · May 28, 2026 · Parts 48-56*
*Code + MAP v5.135 + Codex baseline (SDK 765, Trading 655, Purchasing 143, DataOps 171) are authoritative*

---

## Part 57 — PW Failure Root Cause Analysis (May 28, 2026)

### Trading 23 Failures — One Root Cause (RC1=RC2=RC3)

**The CORS error is a symptom, not the cause.** CORS config at L65-67 correctly includes `http://localhost:5174`. The issue is `_load_json` (non-optional) in `market-snapshot` endpoint throwing `FileNotFoundError` if the file is absent in the test environment.

**Cascade chain:**
1. `getMarketSnapshot()` → GET `/api/context/market-snapshot` → `_load_json("market_snapshot.json")` → FileNotFoundError → 500
2. Dashboard `Promise.all([getAnalytics(), getHistory(), getTradeMetadata(), getMarketSnapshot()])` fails
3. `catch` block fires → `error` state → renders `<h2>Dashboard unavailable</h2>` instead of all panels
4. `RegimePanel`, `PortfolioSummary`, `ThesisBreakdown`, `CalendarHeatmap`, `AccuracyAlertPanel`, `DecisionHistory` all replaced → all 23 tests fail

**Fix — one line:**
```python
# context_router.py - change _load_json to _load_json_optional
@router.get("/market-snapshot")
def market_snapshot() -> dict[str, Any]:
    return _load_json_optional("market_snapshot.json") or {
        "regime": "ranging", "vix": 20.0, "source": "default"
    }
```
Also audit all other `_load_json` (non-optional) calls in context_router.py — any that reference files that may be absent in a fresh test environment should use `_load_json_optional`.

**Note on POST /trade-metadata 500:** Separate issue. Preseed sends V2 seed entries with `trade_id` not `decision_id` → endpoint raises HTTPException(400) → preseed catches as metadata_warning. Not a true 500 and not the CORS root cause.

### DataOps 6 Failures — 3 Distinct Root Causes

**RC4 — Fingerprint strict mode (insight.spec.ts:22, flows.spec.ts:94)**
`FingerprintPanel` renders `<h2>Fingerprint</h2>`. `IncidentReplayCard` renders `"No fingerprint insight recorded."` (contains "fingerprint" lowercase). Playwright's `getByText("Fingerprint")` is case-insensitive → matches BOTH elements → strict mode violation.
**Fix:** `page.getByRole('heading', { name: 'Fingerprint' })` — scoped to headings only.

**RC5 — Operational Rules "scheduling" (evidence.spec.ts:112, flows.spec.ts:314)**
`evolution_fixtures.json` was updated with new variant types: `routing_rule`, `context_policy`, `scoring_threshold`. Test expects `/scheduling/i` and `/quality|resource|memory|off-peak/i`. Neither appears anywhere in current fixtures.
**Fix options:**
1. Add scheduling variant to fixtures (preferred — preserves demo narrative):
   ```json
   {"id":"V-DO-SCHED-001","artifact_type":"scheduling_rule","description":"Shift resource-intensive quality checks to off-peak windows..."}
   ```
   `humanize("scheduling_rule")` = "Scheduling Rule" → matches test.
2. Update test assertions to match new types: `/routing_rule|routing rule|context_policy|context policy/i`

**RC6 — Transfer status labels (story-flow.spec.ts:87)**
Test looks for `TRF-001/002/003` sections with exact badge text `^Active$`, `^Monitoring$`, `^Pending Verification$`. `TransferStatusPanel` renders `humanize(transfer.status)` — "Active", "Monitoring", "Pending Verification" are all defined in STATUS_STYLES. Issue is in `transfer_status.json` fixture data.
**Verify:** `Get-Content "$env:CLAUDE_SDK\apps\dataops\backend\data\transfer_status.json" | Select-Object -First 40` — confirm TRF-001 has `"status": "active"`, TRF-002 `"status": "monitoring"`, TRF-003 `"status": "pending_verification"`. If statuses differ or IDs are different, update fixture.

### Purchasing 1 Failure — RC7

`waitForResponse` IS correctly set up before click in `scoreCurrentOrder`. The race is elsewhere: the failing test calls `itemSelect.selectOption(secondValue)` BEFORE `scoreCurrentOrder()`. Item selection may trigger a state change or auto-prescore POST to `/api/score` that fires BEFORE the listener in `scoreCurrentOrder` is attached.
**Fix:** Add stabilization after item select:
```ts
await itemSelect.selectOption(secondValue);
await expect(page.getByText("Six scorer inputs")).toBeVisible();  // wait for form to re-stabilize
await scoreCurrentOrder(page);
```

### S2P 1 Failure — RC8

Preview scoring is deterministic — actions come from real scorer output. Bootstrap centroids not sufficiently diverged → all invoices score to `auto_approve` → only 1 unique action → test expects ≥2.
**Fix:** Add 2-3 preview invoices with high `amount_variance_ratio` and low confidence factors to force `hold_for_review`/`escalate_to_buyer` assignments. Or relax test to accept bootstrap state: `expectAnyText(page, [/Auto Approve|Hold For Review|Escalate/i, /Bootstrap|calibrating/i])`.

### Fix Priority

```
Immediate (unblocks 23 Trading failures):
  context_router.py: _load_json("market_snapshot.json") → _load_json_optional with fallback

One-liners (test fixes):
  insight.spec.ts L22: getByText("Fingerprint") → getByRole('heading', {name:'Fingerprint'})
  flows.spec.ts (DataOps): same fix

Fixture:
  evolution_fixtures.json: add scheduling_rule variant
  transfer_status.json: verify TRF-001/002/003 statuses

Test:
  Purchasing flows.spec.ts: add stabilization after itemSelect.selectOption
  S2P preview: diversify invoice factors or relax unique-action assertion
```

---
*Document version: v36.0 · May 28, 2026 · Parts 48-57*
*Code + MAP v5.135 are authoritative*

---

## Part 58 — RC6 + DO-7 Final Verdicts (May 28, 2026)

### RC6: Transfer status fixture is correct — root cause is camelCase mapping

`transfer_status.json` has:
- TRF-001: `"status": "active"` ✅
- TRF-002: `"status": "monitoring"` ✅
- TRF-003: `"status": "pending_verification"` ✅

The fixture is correct. `TransferStatusPanel` renders `humanize(transfer.status)` → "Active", "Monitoring", "Pending Verification".

The test failure is in the filter: `transfer.locator("section").filter({ hasText: /TRF-001/i })`. This filter depends on `transfer.transferId` being rendered inside the `<section>` element. The component renders `{transfer.transferId}` (camelCase) but the fixture uses `transfer_id` (snake_case). If the API client does not map `transfer_id → transferId`, the prop is undefined and TRF-001/002/003 never appear in the DOM → filter finds zero sections → `getByText(/^Active$/i)` times out.

**Fix — verify in api.ts then choose:**
```powershell
Select-String "$env:CLAUDE_SDK\apps\dataops\frontend\src\api.ts" -Pattern "transferId|transfer_id" | Select-Object -First 5 | ForEach-Object { "L$($_.LineNumber): $($_.Line.Trim())" }
```
If mapping is absent: add it to the API client. If mapping exists but field name differs: update either the fixture or the component prop access.

### DO-7: FIXED — DROP

```
L13:   from copilot_sdk.scoring.scorer import compute_theta_min
L1314: compute_theta_min(APPLY_FIX_OVERRIDE_RATE, APPLY_FIX_VERIFIED_COUNT) or 0.0
```

No `23.53` inline formula anywhere in DataOps `context_router.py`. The earlier "0 occurrences" result was correct. The `theta_min_proxy` seen in Part 14 was a false positive from the greeks grep matching "theta". **DO-7 is fully fixed — DROP from the queue.**

### Updated Drop Count

DO-7 confirmed DROP. Total: **25 of ~54 queued prompts are DROPs.**

### Complete PW Fix Summary (for Codex)

| RC | Copilot | Failures | Fix | File |
|---|---|---|---|---|
| 1/2/3 | Trading | 23 | `_load_json("market_snapshot.json")` → `_load_json_optional` with fallback | context_router.py |
| 4 | DataOps | 2 | `getByText("Fingerprint")` → `getByRole('heading', {name:'Fingerprint'})` | e2e/dataops/insight.spec.ts, flows.spec.ts |
| 5 | DataOps | 2 | Add scheduling_rule variant to evolution_fixtures.json | apps/dataops/backend/data/evolution_fixtures.json |
| 6 | DataOps | 2 | Fix snake_case→camelCase mapping for transferId in api.ts | apps/dataops/frontend/src/api.ts |
| 7 | Purchasing | 1 | Add stabilization wait after itemSelect.selectOption | e2e/purchasing/flows.spec.ts |
| 8 | S2P | 1 | Diversify preview invoice factors for action variety | s2p-copilot/backend/app/routers/s2p_preview.py or data |

---
*Document version: v36.0 · May 28, 2026 · Parts 48-58*

---

## Part 59 — RC6 Confirmed: Full Snake→Camel Fix Needed (May 28, 2026)

**`transferId` and `transfer_id` — zero occurrences in api.ts.** The mapping was never written.

**Full impact:** Every field in `TransferStatusPanel` renders undefined:
- `transfer.transferId` → undefined → `filter({ hasText: /TRF-001/i })` finds nothing → RC6 test fails
- `transfer.sourceSystem` → undefined → heading shows "to" (no system names)
- `transfer.confidence` → undefined → `formatPercent(undefined)` = "0%"
- `transfer.savingsEstimate` → undefined → "$0"
- `transfer.accuracyAtTarget` → undefined → "Pending" (only correct by accident)

The panel is visually broken in ALL DataOps E2E tests that check it, not just story-flow.

**Fix — in `apps/dataops/frontend/src/api.ts`, inside `getTransferStatus()`:**
```typescript
transfers: (data.transfers || []).map((t: any) => ({
    transferId:              t.transfer_id,
    sourceSystem:            t.source_system,
    sourcePattern:           t.source_pattern,
    targetSystem:            t.target_system,
    targetAction:            t.target_action,
    transferDate:            t.transfer_date,
    status:                  t.status,
    confidence:              t.confidence,
    decisionsSinceTransfer:  t.decisions_since_transfer,
    accuracyAtTarget:        t.accuracy_at_target,
    savingsEstimate:         t.savings_estimate,
    description:             t.description,
})),
```

Single fix, no backend changes, no fixture changes needed. Unblocks both RC6 DataOps failures and makes the transfer panel visually correct for Loom.


---

## Part 60 — PW Round 2 Root Cause Analysis (May 28, 2026)

### Context
After SDK-PW-FIX + SOC-PW-FIX (Round 1), 27 failures remain: Trading 23, DataOps 4.

### Trading 23 Failures — 3 Root Causes

**T1 — Analytics snake_case mismatch (15 failures: Group B + Group C)**
`analytics_cache.json` uses snake_case (`portfolio_summary`, `thesis_breakdown`, `calendar_heatmap`).
`getAnalytics()` in api.ts returns raw JSON without mapping.
DashboardScreen reads camelCase (`portfolioSummary`, `thesisBreakdown`, `calendarHeatmap`) → all undefined → components return null → no headings → panels invisible.
Fix: add mapping in `apps/trading/frontend/src/api.ts` getAnalytics():
`portfolioSummary: data.portfolio_summary, thesisBreakdown: data.thesis_breakdown, calendarHeatmap: data.calendar_heatmap, categoryCounts: data.category_counts, ...`

**T2 — Group A CORS "no console errors" (6 failures)**
Likely clears after T1 (broken renders generate React console errors). Re-run before additional fixes.

**T3 — evidence:26 "Recommended action is" (1 failure)**
EvidencePanel renders `evidence.evidenceText` — no element contains "Recommended action is".
Phrase is stale from old wording. Fix: update test assertion to match actual evidenceText format.

### DataOps 4 Failures — 3 Root Causes

**D1 — Scheduling in Operational Rules (evidence:112, flows:314)**
`store_variants()` → `_variants(evolution_store_factory, domain)` — reads from LIVE evolver state, NOT from evolution_fixtures.json. Adding V-DO-SCHED-001 to fixtures had zero effect.
Fix: add scheduling variant to DataOps evolver config VariantSpec list (evolver_config.py).

**D2 — Variant names in Rule Lifecycle (evidence:47)**
`_normalize_rule_lifecycle()` returns `variant_id` (snake_case). `RuleLifecycle.tsx` reads `rule.variantId` (camelCase) → undefined → falls back to description text or "V-DO-RECUR-001" → neither matches `/dataops-recurring-impact/i`.
Fix: change `_normalize_rule_lifecycle()` to output `variantId` (one character change).

**D3 — Transfer status hardcoded empty (story-flow:87)**
`/api/ae/transfer-status` endpoint body: `return {"transfers": [], ...}` — hardcoded empty stub.
`transfer_status.json` fixture exists and is correct. RC6 camelCase mapping in api.ts is correct.
The endpoint simply never reads the fixture.
Fix: wire endpoint to load from `transfer_status.json`.

### Fix Priority (send as one Codex prompt)

| # | Failures | Fix | File |
|---|---|---|---|
| T1 | 15 Trading | getAnalytics() snake→camelCase mapping | `apps/trading/frontend/src/api.ts` |
| T2 | 6 Trading | Re-run after T1 — likely auto-clears | — |
| T3 | 1 Trading | Update evidenceText test assertion | `e2e/trading/evidence.spec.ts` |
| D1 | 2 DataOps | Add scheduling VariantSpec to evolver config | `apps/dataops/backend/app/evolver_config.py` |
| D2 | 1 DataOps | `variant_id` → `variantId` in normalize function | `apps/dataops/backend/app/ae_router.py` |
| D3 | 1 DataOps | Wire /transfer-status to read transfer_status.json | `apps/dataops/backend/app/ae_router.py` |

T1 + D1 + D2 + D3 as one prompt. Re-run PW. T2 and T3 only if residual failures remain.


---

## Part 61 — MAP v5.136 Verification Scan (May 29, 2026)

### Critical Finding: EVOLVE-PERSIST is DONE — DROP

The single most impactful finding from this scan. EVOLVE-PERSIST was listed as Round 1 priority in the synopsis. It shipped before this session:
- `sqlite_store.py L544`: `def save_evolution_event()` — full INSERT INTO evolution_events
- `memory_store.py L219`: `def save_evolution_event()` — list append + domain filter
- `ledger.py L35`: `self._evolution_store.save_evolution_event(` — called directly
- `test_graphstore_consolidation.py L224-228`: integration test with assertions

Both stores implement the method. The ledger calls it without try/except. Tests pass. The Month 3/Month 6 compounding story persists across restarts. **DROP from queue. Total DROPs: 28.**

### LEARN-422 — DONE (MAP was correct)
`scoring_router.py` returns 200 with `paused=True` + `pause_reason` in LearnResponse body (L251-265). No 422 fires. PW tests using `response.ok()` get true. The synopsis was wrong to list this as pending. DROP.

### D-06-UNMAPPED — DONE (MAP was correct)
`soc.py L1130`: `category = row.get("category") or DEFAULT_CATEGORY`. DEFAULT_CATEGORY imported at L25. Hardcoded "credential_access" string gone. DROP.

### D3 (transfer-status stub) — DONE
Endpoint now reads from fixture with optional fallback:
```python
payload = _load_json("transfer_status.json", None)
if isinstance(payload, dict) and isinstance(payload.get("transfers"), list):
    return payload
```
story-flow:87 should now pass. DROP from PW Round 2 batch.

### PW Round 2 Fixes — Updated (3 remaining, not 5)

| Fix | Status | Notes |
|---|---|---|
| T1 analytics snake→camel | STILL NEEDED | getAnalytics() returns raw JSON, no mapping |
| T2 console errors | Re-run after T1 | Likely auto-clears |
| T3 evidence text | Re-run after T1 | May clear if cascade |
| D1 scheduling VariantSpec | INCONCLUSIVE | main.py L237 has scheduling_rule — need context scan |
| D2 variantId (ae_router L207) | STILL NEEDED | "variant_id" snake_case, component reads variantId |
| D3 transfer-status | **DONE ✅** | _load_json("transfer_status.json", None) wired |

One scan before sending D1: `Get-Content "$env:CLAUDE_SDK\apps\dataops\backend\app\main.py" | Select-Object -Skip 225 -First 30`

### Demo Bundle — UNBLOCKED

`centroids_json` format confirmed: `np.asarray(_from_json(row["centroids_json"]), dtype=np.float64)`
Bundle needs: `"centroids_json": json.dumps(tensor.tolist())` in each checkpoint entry.
`copilot_sdk/demo/` does not yet exist. Three Codex prompts ready to send.
With EVOLVE-PERSIST done, evolution_events in the bundle will now persist correctly.
**Move to Immediate queue.**

### Storage Architecture — FULLY CLOSED

Both Tier 2 gaps are now closed:
- RL posteriors: durable via save_rl_state/load_rl_state (confirmed Batch 9)
- Evolution events: durable via save_evolution_event (confirmed this scan)

The platform correctly supports the full Month 1 → Month 3 → Month 6 compounding narrative today. No storage gaps remain.

### Updated DROP Count

| Added this scan | Item |
|---|---|
| DONE | LEARN-422 |
| DONE | D-06-UNMAPPED |
| DONE | EVOLVE-PERSIST |
| DONE | D3 transfer-status fix |
| **Total DROPs: 28** | of ~54 queued prompts |


---

## Part 62 — DataOps main.py Full Review (May 29, 2026)

### D1 DONE ✅ — Scheduling seeded at startup via save_evolution_event

`_seed_demo_evolution_events_if_needed()` runs in `_run_startup_seed_once()` (called from both `@app.on_event("startup")` and the TestClient middleware):

```python
graph_store.save_evolution_event(
    domain=DOMAIN,
    event_type="shadow_started",
    rule_name="resource_quality_scheduling_signal",
    variant_id="dataops-off-peak-scheduling-v1",
    metadata={"artifact_type": "scheduling_rule", ...}
)
```

`store_variants()` in ae_router reads `get_evolution_events()` → `_variant_from_event()` extracts `artifact_type` from metadata → `_normalize_rule()` sets `"type": "scheduling_rule"` → `humanize("scheduling_rule")` = "Scheduling Rule" → matches `/scheduling/i`. PW test evidence:112 failed because this function was added after the last PW run. **D1: DROP.**

### D2 STILL NEEDED — variantId one-liner

`_variant_from_event()` correctly sets `variant["id"] = "dataops-recurring-impact-v1"`. But `_normalize_rule_lifecycle()` L207 outputs `"variant_id"` (snake_case). `RuleLifecycle.tsx` renders `rule.variantId || rule.name || rule.id` — `variantId` is undefined, `name` (description text) is truthy and shown first, `id` never reached. Fix: L207 `"variantId": _variant_id(variant)`.

### Auto-Seeding Pattern Already in DataOps

`_auto_seed_if_needed()` already implements the demo bundle pattern for DataOps:
- Checks `count_decisions(DOMAIN)` — skips if warm
- Creates `CompoundingScorer.from_preset()` directly — no HTTP
- Seeds from `dataops_seed.json` fixture
- Hooked to `@app.on_event("startup")`

Demo bundle GENERALIZES this across Trading + Purchasing and adds centroid checkpoints for the trajectory chart. DataOps already has the foundation.

### PW Round 2 — Final: T1 + D2 Only

| Fix | Status |
|---|---|
| T1 getAnalytics() snake→camelCase | STILL NEEDED — 15 Trading failures |
| T2 console errors | Re-run after T1 |
| T3 evidence text | Re-run after T1 |
| D1 scheduling | **DONE ✅** — startup seeds via save_evolution_event |
| D2 ae_router L207 variantId | STILL NEEDED — 1 DataOps failure |
| D3 transfer stub | **DONE ✅** |

PW Round 2 Codex prompt = T1 + D2. Two changes. Total DROPs: **30**.


---

## Part 63 — Methodology Retrospective (May 29, 2026)

### Accuracy Assessment: Parts 41-62 PW Analysis

**Net assessment from session review:** Parts 1-38 (architecture, math, bugs, protocols) remain accurate. Parts 41-62 (PW analysis, fix hypotheses) had approximately 17% accuracy on specific fixes — 1 of 6 correct in Part 60.

**Part 60 fix accuracy breakdown:**

| Fix | Prediction | Reality | Correct |
|---|---|---|---|
| T1 analytics mapping | Not done — needs fix | Still needed ✓ | ✓ |
| D1 scheduling | Missing from evolver config | Already in startup via save_evolution_event | ✗ |
| D2 variantId | L207 snake_case mismatch | Still present (pending) | ✓ (likely) |
| D3 transfer stub | Hardcoded empty | Already wired to fixture | ✗ |
| LEARN-422 | Needs HTTPException(503) | Already returns 200+paused | ✗ |
| EVOLVE-PERSIST | Not shipped | Already in both stores + ledger + tests | ✗ |

**Root cause of low accuracy:** Static code analysis against stale snapshots. The codebase was moving faster than the analysis. By the time fixes were proposed, several were already resolved.

### The Correct Methodology Going Forward

**Pre-check-driven Codex prompts, not analysis-driven ones.**

```
Old pattern (17% accuracy):
  Scan code → form hypothesis → write fix → send to Codex
  Problem: hypothesis formed against stale snapshot

Correct pattern:
  Form hypothesis → verify current state with targeted scan
  → confirm broken/fixed → write minimal Codex prompt
  → send only what the scan confirms is needed
```

**Operationally, for any PW fix prompt:**
1. Grep for the exact line/pattern before writing the fix
2. If the grep shows it's already fixed → DROP, do not send
3. If the grep confirms broken → write prompt with the exact line reference
4. Never write a fix prompt from memory or prior analysis alone

**What this means for T1 and D2 (the remaining PW items):**
Both were confirmed by fresh scans in Parts 60-62, not prior analysis:
- T1: `getAnalytics()` body confirmed as 3 lines with no mapping (Part 60 scan, check #5)
- D2: `L207: "variant_id"` confirmed in ae_router scan (Parts 60, 62)

These two are safe to send. Everything else has been verified as done.

### Document Reliability Map

| Content | Parts | Reliability | Use for |
|---|---|---|---|
| Architecture, math, conservation law, GAE | 1-38 | High ✓ | Reference, design decisions |
| Bug catalogue, protocol rules | 1-38 | High ✓ | Regression prevention |
| PW root cause analysis (pre-scan) | 41-62 | Low (~17%) | Hypothesis only — verify before acting |
| PW root cause analysis (post-scan confirmed) | 57-62 | High ✓ | Safe to act on |
| DROP confirmations (scan-verified) | 55-62 | High ✓ | Safe to remove from queue |
| Priority stack | Part 54 | Medium | Cross-check against MAP before sending |


---

## Part 64 — MAP v5.137 Results: PW Fix R1+R2 Complete (May 29, 2026)

### PW Final Results (post R1+R2)

| Suite | Pre-Fix | Post R2 | Status |
|---|---|---|---|
| Trading | 87/23/0 | **106/1/4flaky** | ✅ Gate PASSED |
| DataOps | 92/6/1 | **96/1/1flaky/1skip** | ✅ Gate PASSED |
| Purchasing | 46/1/0 | **47/0/0** | ✅ Clean |
| S2P Preview | 10/1/0 | **11/0/0** | ✅ Clean |
| **Total** | **235/31** | **260/2/5flaky/1skip** | **99.2%** |

### 2 Hard Failures Remaining (both spec issues, not backend bugs)

**#97 Trading flows:41** — `waitForFunction` checks `!textContent.includes("Loading")` on entire `<main>`. Rendered content incidentally contains "Loading" text elsewhere. Performance screen renders correctly (line 65 passes). Fix: scope selector to loading spinner element only. 5 min. Added to P2 SDK-TRADING-FE.

**#98 DataOps flows:332** — Pattern Origin panel expects `/SOC|S2P/i`. Seeded evolution events are DataOps-local with no `source_copilot` field set. Fix: add `source_copilot: "SOC"` to one startup seed event. 15 min.

### R2 Actual Fixes (3, not 5)

| Fix | What | Impact |
|---|---|---|
| **T-CORS** | `_load_json_optional` caught FileNotFoundError but NOT JSONDecodeError. `trade_metadata.json` existed (431.6KB) but had malformed JSON → 500 → Promise.all cascade → 22 Trading failures in one shot. Fix: catch JSONDecodeError too. | +22 Trading tests |
| **D-SCHED** | Operational Rules reads EvolutionStore (SQLite), not fixtures. Startup hook `_seed_demo_evolution_events_if_needed()` already seeded the scheduling event at startup. Pre-check confirmed. | DataOps scheduling test pass |
| **D-TRANSFER** | `/api/ae/transfer-status` was hardcoded empty stub → wired to fixture. Pre-check confirmed. | DataOps transfer test pass |

### Critical Corrections to Part 54 Hypotheses

**T1 (getAnalytics() mapping) was WRONG.** Both Trading and DataOps frontends have recursive snake→camelCase normalizers in api.ts (L38-54 Trading, L110-135 DataOps). The analytics mapping was already handled. Manual mapping was unnecessary.

**D2 (variantId L207) was likely also wrong.** The recursive normalizer in DataOps api.ts converts `variant_id` → `variantId` automatically. Not mentioned in R2 results because the normalizer resolved it.

**Actual cascade source:** `trade_metadata.json` malformed JSON → `_load_json_optional` JSONDecodeError not caught → 500 → Promise.all in DashboardScreen caught → error state → all panels replaced → 22 tests. One endpoint fix cleared 22 failures.

### New Standing Rules (#42, #43)

**Rule 42:** Both Trading and DataOps frontends have recursive snake→camelCase normalizers in api.ts. Manual field mapping is unnecessary for these copilots — the normalizer handles it.

**Rule 43:** `_load_json_optional` must handle BOTH `FileNotFoundError` AND `JSONDecodeError`. Malformed JSON in optional cache files is a real failure mode. A file existing is not the same as a file being valid.

### Updated DROP Count: 32 of ~54

SDK-PW-FIX (#90) confirmed DONE with 8 total fixes. MAP v5.137 DROP count = 32.

### Test Baselines (authoritative from MAP v5.137)

| Repo | Tests |
|---|---|
| SDK root | 770 |
| Trading BE | **663** (+2 from R2) |
| Purchasing BE | 143 |
| DataOps BE | 171 |
| S2P BE | **817** (+1 from R1) |
| SOC BE | ~1,583 |
| ci-platform | 339+11skip |


---

## Part 65 — Batch 11-14 Pre-Scan Results (May 29, 2026)

### DROP Summary from Scans 1-3

| Item | MAP# | Evidence |
|---|---|---|
| S2P-F21 Disruption | #50 | 4 fully computed scenarios, `_apply_mitigation()` math, no fixtures |
| CONSERVATION-PERSIST | #58 | `_evolution_conservation_state()` derives from SQLite decisions — pure computation, no in-memory state |
| GRAPH-TPC | #60 | All 3 contracts defined with NodeTypes — MAP goal was definition |
| S2P-F18-P1 D-CEL | #47 | `CelonisConnector` in S2P + DataOps, `/celonis/status` + `/sap/status` routes live |
| BLOCK-1.2 Archetype | #61 | `ArchetypeGenerator` fully implemented and exported from `copilot_sdk.generators` |
| S2P-F18-P2 | #47-P2 | Cascades from P1 DROP |
| S2P-F19 Payment | #48 | 10-supplier `DEMO_PAYMENT_BEHAVIOR`, OTIF correlation math, integrates `supplier_profile_accumulator` |
| GAP-H2-DEMO | #59 | `demo.py COPILOTS` includes Trading/Purchasing/DataOps. Transfer infrastructure complete. |

**Running total: ~42 of ~70 tracked prompts are DROPs.**

### Major Scope Reductions

| Item | MAP# | Old Scope | New Scope | Evidence |
|---|---|---|---|---|
| TRD-MULTI-TRADER | #27 | 1wk | **30 min** | `TraderProfileService` fully built (20 methods). Missing only: `trader_id` field in `NormalizedTrade` + write path. `_decision_trader()` already reads `metadata.trader_id`. |
| TRD-VERIFICATION-MODEL | #21 | 2d | **2h** | `r_multiple`, `execution_quality`, `verification_score` in `NormalizedTrade`. All inputs (`stop_loss`, `expected_entry_price`, `fill_rate`) present. Only computation functions missing. |
| S2P-F8 Factor Proposer | #38 | 1-2wk | **1d** | `/dk-weights` + `/contribution` endpoints built. Missing: recommendation logic only. |
| S2P-F20 Optimizer API | #49 | 2wk | **1d** | `/export/centroids` + `/export/csv` exist. Missing: import endpoint + conservation check. |
| Factor Contribution UI | #56 | 2d | **1d frontend** | `/contribution` backend complete. Work is purely frontend bar chart. |
| SDK-DOCS | #87 | fresh write | **0.5d** | README + `examples/hello_world/` exist. API reference + protocol docs needed. |

### Key Design Shifts

**TRD-MULTI-TRADER precise fix:**
1. Add `trader_id: Optional[str] = None` to `NormalizedTrade` dataclass
2. Pass `trader_id` in `write_decision()` metadata
3. Update `CSVConnector` to extract trader_id column if present
`TraderProfileService._decision_trader()` already reads `metadata.trader_id` and groups correctly.

**TRD-VERIFICATION-MODEL computation formulas:**
```python
r_multiple = (exit_price - entry_price) / (entry_price - stop_loss)  # long trades
execution_quality = fill_rate * (1 - abs(entry_price - expected_entry_price) / entry_price)
```
All inputs already in `NormalizedTrade`. Add functions in `context_router.py` or `CSVConnector`, call after trade import.

**S2P-F10 Financial Impact:** Still a genuine redesign. `ANNUAL_TARGET_USD = 680000.0` + `BREAKDOWN` percentages are hardcoded constants. Real per-decision economics needed.

**S2P-F8 Factor Proposer:** Foundation built — `/dk-weights` returns DK weights, `/contribution` returns per-invoice factor contributions. Only missing: ranking logic ("given these weights, which factor should you consider replacing?").

**SDK-DOCS:** README has pip install + quick start + `examples/hello_world/`. Not blank slate. Fill API reference + protocol docs + demo bundle section.


---

## Part 66 — S2P Implementation vs PD v1.3: Factor Space & Infrastructure (May 29, 2026)

### Source: s2p_pd_scan.txt (Scan 1) · Authority: s2p_copilot_unified_v1_3.md

### Factor Space — Confirmed Correct (PD Part II, Invoice Exception Pilot)

The S2P PD v1.3 defines two distinct factor architectures:
- **Part I (Engineering Design §3):** d=8 domain-level risk scores (supplier_risk, logistics_risk, demand_risk, inventory_risk, regulatory_risk, geopolitical_risk, financial_risk, environmental_risk). Shape (5,5,8). Future full S2P architecture.
- **Part II (Product Definition §PD6):** d=7 operational invoice factors (match_status, amount_variance_ratio, duplicate_score, supplier_exception_history, payment_terms_impact, commodity_index_correlation, tax_regulatory_compliance). Shape (5,5,7). The pilot.

**Implementation uses Part II — confirmed correct.** All 7 factor computers implemented. Categories (price_variance, quantity_mismatch, duplicate_risk, contract_gap, format_compliance) and actions (auto_approve, hold_for_review, escalate_to_buyer, flag_leakage, refer_to_specialist) both match §PD6 exactly. No drift. `S2PDomainConfigV2 = S2PDomainConfig` alias maintains backward compatibility.

Evidence templates confirmed for all 5 categories — the "REQUIRES WORK ⚠️" flag in PD §17.4 referred to Part I (d=8 domain language). For the Part II pilot: ✅ complete.

### Infrastructure — Far More Complete Than MAP Suggested

21 routers, ~115 routes, 75+ test files, 854 tests. Key confirmed:

| Router | Routes | Tests | PD Feature |
|---|---|---|---|
| framework_router.py | 28 | — | Core scoring pipeline |
| s2p.py | 6 | 34 score endpoint | F1/F3/F5 basics |
| s2p_suppliers.py | 9 | 19 supplier + 18 accumulator | F13 supplier intelligence |
| s2p_evidence.py | 9 | 16 evidence | F2 evidence panel |
| s2p_governance.py | 7 | 25 governance + 20 auto-approve | F4/F5/F22 |
| s2p_evolution.py | 8 | 14+13+10+8+4 evolution | F12/G13 AE |
| s2p_discovery.py | 5 | 34 discovery | F17/S5 |
| s2p_novelty.py | 4 | 27 novelty | F6/S9 |
| s2p_insight.py | 5 | 15 insight | F16/S16 |
| s2p_simulation.py | 4 | 25 simulation | F21/S3 |
| s2p_payment.py | 2 | 20 payment | F19/S12 |
| s2p_clustering.py | 2 | 16 clustering | S7 |
| s2p_early_warning.py | 3 | 15 early warning | F15/S11 |
| s2p_control_tower.py | 4 | 16 control tower | G6 |
| s2p_explorer.py | 6 | 11 explorer | F7/F8 foundation |
| s2p_audit_export.py | 2 | 8 audit | F11 |
| s2p_pvg.py | 5 | 12 pvg | F10 |

### Financial Impact — Better Foundation Than Expected

`_financial_impact_from_fixtures()` reads `load_invoices()` per-invoice — not hardcoded constants. Iterates fixture invoices computing `amount_recovered` and `amount_at_risk` per record, aggregates by category. `source: "fixture"` label confirmed. **Redesign needed (#39) is fixture → OutcomeReceipt source**, not constants → computation. This is a smaller jump than assumed. Effort: 1-2wk (was 2wk).

### IntentType Enum — 17 Intents Confirmed ✅

Full taxonomy (PD G6 target: 15-18):

| Category | Intents |
|---|---|
| triage (5) | triage_price, triage_quantity, triage_duplicate, triage_contract, triage_format |
| action (5) | auto_approve, hold_review, escalate_buyer, escalate_manager, refer_specialist |
| query (4) | query_invoice, query_supplier, query_compliance, query_conservation |
| operational (3) | report_financial, report_audit, batch_process |

MAP #46 S2P-M4 INTENT: **fully confirmed ✅.**

### OutcomeReceipt — Hash Chain Implemented, Near-PD-Complete

Full `OutcomeReceipt` implementation:
- `receipt_hash`: SHA-256 over all fields (`hashlib.sha256(json.dumps(stable_payload)).hexdigest()[:16]`) ✅
- `previous_receipt_hash`: audit chain link ✅ — IS `audit_status.prev_hash`
- `centroid_updated: bool` ✅ — IS `learning_update.centroid_moved`
- `conservation_state_before` + `conservation_state_after` ✅
- `verified_count_before` + `verified_count_after` ✅
- `amount_at_risk: float` ✅
- `override_reason` ✅ — IS reason_code
- `factor_vector: list[float]` + `factors: dict` ✅

Missing vs PD spec (small additions): `amount_recovered`, `cycle_time_saved`, `weight_updated` flag, `evidence_chain`, `exportable` flag. MAP #42 confirmed ✅ DONE at shipped scope. New item #103 (0.5d) for the remaining fields.

---

## Part 67 — S2P Design Concerns & Scenario Coverage (May 29, 2026)

### Source: s2p_pd_scan.txt + s2p_pd_scan2.txt + evolver_config.py analysis

### Design Concern 1 — G12 Situation Analyzer NOT BUILT (Critical)

**The most important finding from the entire S2P review.**

PD scenario S14 ("Not a Script — A Decision"):
> "5.2% variance. Copper rose 4.8%. Contract §7.3 allows pass-through ≤110% of index. Within bounds. Accept. Confidence: 0.91."

Zero S2P situation analyzer code found. `s2p_evidence.py`'s 9 routes are evidence panel display routes — not the 47-node graph traversal that reasons from procurement context. Graph traversal references in the codebase are SOC's `provenance.py`.

**Competitive impact:** Every competitor (Zycus Merlin, Celonis) shows auto-approve rate improvement. Only S14 shows *reasoning from context*. Without S14, the demo proves learning but not reasoning. The demo becomes a very good AP automation story rather than a procurement AI that reasons from context. MAP #43 should be elevated to next-batch priority.

**Effort unchanged: 3-4 weeks.** No shortcut path — the 47-node traversal requires building the graph schema (invoice × contract × commodity × supplier × compliance rules), the traversal query engine, and the NL rendering pipeline. This is the most complex remaining S2P item.

### Design Concern 2 — AE Dimension Families Incomplete

`evolver_config.py` (`$S2P/backend/app/domains/s2p/evolver_config.py`) implements 2 of 4 PD G13 dimension families:

**Implemented:**
- `evidence_ordering`: v1 (active, order: factor_fingerprint→similar_invoices→audit_trail) + v2 (shadow, order: supplier_history→contract_terms→factor_fingerprint) ✅
- `routing_threshold`: v1 (active, auto_approve=0.86, escalate=0.68) + v2 (shadow, 0.91/0.72) ✅

**Missing:**
- `escalation_criteria`: routing conditions for escalate_to_buyer vs escalate_to_manager vs refer_to_specialist. Without this, the system cannot learn optimal escalation thresholds.
- `triage_weights`: F1 priority queue weighting formula. Without this, the system cannot learn which exception ordering maximizes resolution speed.

MAP #44 S2P-G13 AE-VARIANTS: **change from ✅ DONE to ⚠️ PARTIAL.** New item #104 (0.5d) to add the 2 missing families.

**Architectural note:** `PromptEvolverConfig(exploration_constant=1.414)` = UCB1 with √2 exploration — mathematically optimal. `promotion_improvement_threshold=0.05` = 5% improvement bar — reasonable.

### Design Concern 3 — promotion_min_samples=10 Too Low

`promotion_min_samples=10` in `PromptEvolverConfig`. For `routing_threshold` variants — where the confidence delta between v1 (0.86) and v2 (0.91) is only 5 percentage points — 10 samples is statistically inadequate to detect meaningful improvement. The decisions that fall in the 0.86-0.91 confidence band may number fewer than 10 in many sessions.

**Risk:** A routing_threshold variant could promote on noise in low-volume sessions. If SDK conservation law governs promotion (likely — `copilot_sdk.evolution` owns the promotion gate), this risk is partially mitigated. But `promotion_min_samples` should be raised to 50+ for `routing_threshold` specifically.

**Recommendation:** Either raise globally to 50, or make `promotion_min_samples` per-family configurable and set 50 for routing_threshold, 20 for evidence_ordering.

### Design Concern 4 — S8 Lead Time (F14) Not Implemented

`supplier_history()` returns `accumulator.get_supplier_history(supplier_id, limit)` — accumulated invoice decision events. No GR/PO lead time computation, no per-quarter trending (Q1-Q3: 14.2d, Q4: 21.4d), no commodity correlation ("Copper > $4.50 predicts Q4 delays 6 weeks early").

S8 scenario requires: (a) lead_time_weeks field aggregated from supplier history, (b) per-quarter breakdown, (c) correlation index computation. These are absent. MAP #41 S2P-F14 LEAD-TIME: genuine 1-2wk work.

### Design Concern 5 — Financial Impact Source (F10)

`_financial_impact_from_fixtures()` reads fixture invoice data (`load_invoices()`). For the compounding narrative, leakage prevented must grow from zero as OutcomeReceipt records accumulate — not read from a static file with pre-populated `amount_recovered` fields. The `source: "fixture"` label in the response directly contradicts the demo story ("the system learned $680K in leakage from 10,000 decisions").

Redesign path (#39): replace `load_invoices()` as the data source with `receipt_store.get_all_receipts()`, aggregate `amount_at_risk` and `amount_recovered` from live verified decisions.

### S16 Confirmed via s2p_insight.py

`/cross-graph`: `impact_score = exception_rate × (1 + bottleneck_duration/60)` per supplier, sorted by impact — **connects Celonis bottleneck duration to supplier exception rates.** Reads `celonis_process_data.json` with DataOps backend fallback. `/process-context/{invoice_id}`: 6 SAP activities with duration breakdown + category-specific bottleneck reason. `/process-signals`: Celonis recommendations.

**S16 is demo-ready.** MAP #47 S2P-F18 PROCESS-TECH: **complete DROP** — both connector layer (CelonisConnector, Scan 1) and endpoint layer (insight router, Scan 2).

### 16-Scenario Coverage Final State

| # | Scenario | Status | Key Gap / Feature |
|---|---|---|---|
| S1 | Exception Rate Drops | ✅ | Scoring + triage |
| S2 | Autopilot Expansion Proof | ✅ | Auto-approve + conservation |
| S3 | Strategic Sourcing | ✅ | F21 disruption confirmed |
| S4 | Factor Proposer | ⚠️ 1d | Ranking logic missing |
| S5 | Pattern Nobody Queried | ✅ | Discovery router |
| S6 | Expertise Walks Out | ✅ | Supplier accumulator |
| S7 | 47 Supplier Duplicates | ✅ | Clustering router |
| S8 | ERP Lead Time Wrong | ⚠️ 1-2wk | F14 aggregation missing |
| S9 | Automation Broke Silently | ✅ | Novelty detection |
| S10 | Consultant Findings Evaporate | ✅ | Centroid persistence |
| S11 | Supplier Fine Until Wasn't | ✅ | Early warning + /declining |
| S12 | Working Capital Trap | ✅ | Payment strategy confirmed |
| S13 | System Tunes Itself | ⚠️ 0.5d | AE 2/4 families; #104 adds rest |
| **S14** | **Not a Script — a Decision** | **❌ CRITICAL GAP** | **G12 not built** |
| S15 | System Values Caution | ✅ | penalty_ratio=5.0 |
| S16 | Where Celonis Stops | ✅ | insight router confirmed |

**13✅ · 3⚠️ · 1❌**

**Path to full demo coverage:**
- 2 days of Codex work (#103 + #104 + S4 ranking): → 15/16 ✅
- 3-4 weeks for G12 Situation Analyzer: → 16/16 ✅

### New MAP Items from S2P Review

| MAP# | ID | Effort | What |
|---|---|---|---|
| #103 | S2P-G10-SUPPLEMENT | 0.5d | OutcomeReceipt: add amount_recovered, cycle_time_saved, weight_updated, exportable |
| #104 | S2P-G13-SUPPLEMENT | 0.5d | AE evolver_config: add escalation_criteria + triage_weights dimension families |

### Confirmed DROPs from S2P Review

| MAP# | ID | Evidence |
|---|---|---|
| #47 P1 | S2P-F18 connector | CelonisConnector + SAPConnector in both backends (Scan 1) |
| #47 P2 | S2P-F18 endpoints | insight router: /cross-graph + /process-context + /process-signals (Scan 2) |
| #48 | S2P-F19 PAYMENT | DEMO_PAYMENT_BEHAVIOR 10 suppliers, OTIF math, accumulator integration |
| #50 | S2P-F21 DISRUPTION | 4 computed scenarios, _apply_mitigation() math |


---

## Part 68 — Trading Copilot: PD v1.0 vs Implementation (May 29, 2026)

### Source: trading_pd_scan1.txt + trading_pd_scan2.txt · Authority: trading_copilot_product_definition_v1.md

### Architecture Overview

Trading has a rich, complete backend across 12 routers and 9 dedicated services:

| Router | Routes | Tests | PD Feature |
|---|---|---|---|
| context_router.py | 10 | — | F2/F4/F5 hub |
| social.py | 9 | 11 | F13/T8/T12 multi-trader |
| broker_router.py | 7 | 18+14 | Broker integration |
| data_import.py | 5 | 10+16 | F1 import |
| webhook.py | 4 | 10 | T25 TradingView |
| journal.py | 3 | 20 | F7 journal |
| promotion.py | 2 | 32 | F11/T10 paper→live |
| regime.py | 2 | 27+25 | F10/T4/T16 |
| analytics.py | 2 | 7 | F14/F15 |
| evidence.py | 1 | 26 | F3 NL |
| prescore.py | 1 | 23 | F9 (v1.1, AHEAD OF SCHEDULE) |
| correlation.py | 1 | 26 | T18 |
| vix_timing.py | 1 | 28 | T20 |

**Total: 704 tests across 39 test files.**

### Key Confirmed Implementations

**F2 Signal Trust Radar (T1) — ✅**
`context_router.py L295: GET /trust-analysis`. The hero feature — radar chart showing expected vs actual DK weights — is implemented. `test_trust_analysis.py: 9 tests`.

**F4 Pattern Detector (T2/T7) — ✅ 5 detectors**
`services/pattern_detector.py` (8.1KB): `_detect_revenge` (30 min post-loss), `_detect_overconfidence` (size after 3 wins), `_detect_fomo` (day extreme entries), `_detect_tilt` (3+ trades/hour), `_detect_drawdown_chase` (size increase in drawdown). 23 tests. Exposed at `context_router.py L310: GET /patterns`.

**F5 Conservation Dashboard (T5/T9) — ✅**
`context_router.py L330: GET /conservation-breakdown`. Per-strategy GREEN/AMBER/RED. 15 tests.

**F9 Pre-trade Decision Support — ✅ AHEAD OF SCHEDULE**
PD schedules F9 as v1.1. `prescore.py` already implemented with POST `/prescore`. 23 tests. Confirms TRD-REALTIME-SCORE as DROP.

**F11 Strategy Promotion (T10) — ✅ COMPREHENSIVE**
`services/promotion.py` (8.8KB). `PromotionService.evaluate()` with `gae.calibration.conservation_status()` gating. Tracks per-strategy-tag performance (more granular than PD spec). GET `/promotion` + POST `/promotion/evaluate`. 32 tests.

**F10 RegimeRecommender (T4/T14/T16) — ✅ EXACTLY PD SPEC**
`regime.py` imports `RegimeService` + `RegimeRecommender`. `/regime/detail` calls `RegimeRecommender().recommend()` with conservation_status. Logic precisely matches PD §3.5: `if delta > 0.05 → increase; if delta < -0.10 → reduce; else → hold`. 25 recommender + 27 regime tests.

**CorrelationMonitor (T18) — ✅**
`services/correlation.py` (7.2KB). `CorrelationService(window_days=window).compute(trades)`. Configurable 2-252 day window. 26 tests.

**VIXTimingService (T20) — ✅**
`services/vix_timing.py` (7.1KB). `VIXTimingService().analyze(trades, vix_data)` with historical VIX from `RegimeService`. 28 tests.

**TradingTemplateEngine (F3) — ✅ PARTIAL**
`evidence.py L91: class TradingTemplateEngine`. Trend_following + mean_reversion templates confirmed. Event_driven, income, scalp templates need verification scan if required. 26 evidence tests.

### Design Concern 1 — T3 Time-of-Day Pattern NOT Detected

`pattern_detector.py` has 5 detectors. None of them detect time-of-day accuracy degradation (PD T3: "Friday 2-4pm accuracy: 39% vs 54% baseline"). `_detect_tilt` catches 3+ trades/hour (quantity) but not accuracy-by-period (quality). The `journal.py /analytics` endpoint may partially cover this, but the behavioral pattern surfacing ("Friday afternoon is costing you $1,200/month") is absent.

**T3 status: ⚠️ PARTIAL.** New item #106 (1d) adds `_detect_time_of_day` to `pattern_detector.py`.

### Design Concern 2 — F12 AgentEvolver Has No Trading-Specific Variants

`test_evolution_mount.py: 3` + `test_evolution_trading.py: 13` confirm the SDK AgentEvolver is mounted for Trading. But no Trading-specific `evolver_config.py` exists — no `VariantSpec` dimensions. S2P has `evidence_ordering` + `routing_threshold` families. Trading needs domain-specific variants:
- `alert_threshold`: revenge detection window — v1 (30 min active) vs v2 (45 min shadow)
- `pattern_sensitivity`: overconfidence trigger — v1 (3 wins) vs v2 (4 wins, less sensitive)
- `regime_boundary`: VIX thresholds — v1 (20/30 current) vs v2 (22/28 tighter)

PD §7.4 F12 explicitly requires "auto-calibrates alert thresholds, pattern sensitivity, regime boundaries." Without Trading-specific variants, F12 is generic-only.

**New item #105 (0.5d)** — same pattern as S2P #104.

### 20-Scenario Coverage Final State

| # | Scenario | Cluster | Status |
|---|---|---|---|
| T1 | Signal Trust Radar | A | ✅ |
| T2 | Post-win overtrading | A | ✅ |
| T3 | Friday afternoon degradation | A | ⚠️ 1d (#106) |
| T4 | Market regime analysis | A | ✅ |
| T5 | Can I scale this strategy? | B | ✅ |
| T6 | Execution gap quantified | B | ✅ |
| T7 | Revenge trade real-time | C | ✅ |
| T8 | Per-trader edge profile | D | ✅ |
| T9 | Strategy stopped working | D | ✅ |
| T10 | Prove it before real money | D | ✅ |
| T11 | Trade history unified | E | ✅ |
| T12 | Playbook transferred | E | ✅ |
| T13 | Tariff shock survivor | F | ✅ |
| T14 | Regime shift detected | F | ✅ |
| T15 | Revenge trade at VIX 32 | F | ✅ |
| T16 | Volatile-market edge rotation | G | ✅ |
| T17 | Premium selling IV/RV timing | G | ⚠️ v1.1 |
| T18 | Correlation breakdown alert | G | ✅ |
| T19 | Earnings subcategory split | G | ✅ |
| T20 | VIX mean-reversion timing | G | ✅ |

**17✅ · 2⚠️ · 0❌ — No critical gaps.**

After #105 (0.5d) + #106 (1d): **18/20 ✅**. T17 requires options data (v1.1, correct scheduling).

### Comparison: Trading vs S2P

| Metric | Trading | S2P |
|---|---|---|
| Scenarios confirmed ✅ | 17/20 | 13/16 |
| Critical gaps (❌) | **0** | 1 (G12) |
| Services implemented | 9 | 21 routers |
| Tests | 704 | 854 |
| AE variants | 0 (generic only) | 2/4 families |
| Ahead of schedule | F9 (prescore) | F19/F21 (payments, simulation) |

Trading is the more mature copilot: 0 critical gaps vs S2P's 1 (G12 Situation Analyzer). Demo-ready for all 7 scenario clusters today.

### New MAP Items from Trading PD Review

| MAP# | ID | Effort | What |
|---|---|---|---|
| #105 | TRD-F12-VARIANTS | 0.5d | Trading-specific VariantSpec: alert_threshold (revenge 30→45 min), pattern_sensitivity (overconfidence 3→4 wins), regime_boundary (VIX 20/30 vs 22/28) |
| #106 | TRD-T3-TOD | 1d | `_detect_time_of_day` in pattern_detector.py: segment accuracy by hour + day-of-week, surface worst windows with annual cost estimate |

### Additional Confirmed DROPs from Trading Scans

| Feature | Evidence |
|---|---|
| TRD-REALTIME-SCORE (F9) | prescore.py implemented, 23 tests — v1.1 feature done in v1.0 |
| TRD-REGIME-CLASSIFIER (F10) | regime.py + RegimeService (7.3KB) + 27 tests |
| TRD-REGIME-RECOMMEND (T26) | regime_recommender.py (5.9KB) + 25 tests |
| TRD-CORRELATION-MONITOR (T27) | correlation.py + CorrelationService (7.2KB) + 26 tests |
| TRD-VIX-TIMING (T29) | vix_timing.py + VIXTimingService (7.1KB) + 28 tests |
| TRD-PATTERN-DETECTOR (T8/T7) | pattern_detector.py (8.1KB) + 5 detectors + 23 tests |
| TRD-PROMOTION-ENGINE (F11) | promotion.py + PromotionService (8.8KB) + 32 tests |
| TRD-EVIDENCE-NL (F3) | TradingTemplateEngine in evidence.py + 26 tests |
| F2 TRUST-RADAR | /trust-analysis in context_router.py + 9 tests |
| F5 CONSERVATION-BREAKDOWN | /conservation-breakdown in context_router.py + 15 tests |


---

## Part 69 — Trading NL Template Engine: Complete Verification (May 29, 2026)

### Source: apps/trading/backend/app/evidence.py · Final Trading review

### All 5 Category Templates Confirmed ✅

`TradingTemplateEngine` in `app/evidence.py` has all 5 category renderers plus `_generic` fallback:

| Category | Template method | Focus factors | Quality |
|---|---|---|---|
| trend_following | `_trend_following` | signal_alignment + market_regime | ✅ |
| mean_reversion | `_mean_reversion` | timing_quality + position_sizing | ✅ |
| event_driven | `_event_driven` | subcategory + signal_confidence + risk_reward | ✅ |
| income_strategy | `_income_strategy` | risk_reward + position_sizing + options analytics | ✅ |
| scalp_intraday | `_scalp_intraday` | timing_quality + emotional_indicator | ✅ |

**F3 NL Evidence: fully complete.** Each template highlights the 1-2 factors most diagnostic for that trade category — architecturally clean, no LLM calls (docstring: "Render stable Trading evidence text without external model calls").

### T17 Income/IV-RV — More Complete Than Initially Assessed

`_income_strategy()` calls `_options_analytics_text()` which renders:
`"Options analytics-only: IV/RV {iv_rv_ratio:.2f}, Greeks {greeks:.2f}, Theta {theta:.2f}."`

IV/RV is already in the evidence text for income_strategy trades when options factors are detected. The full T17 recommendation ("IV/RV > 1.5 → increase allocation") still requires RegimeRecommender integration with IV/RV as input signal — but the evidence panel for options trades is already working. T17 status: ⚠️ v1.1 for the recommendation layer; ✅ for evidence display.

### `_emotional_detail()` Matches PD §10.2 Precisely

Three emotional patterns implemented with exact PD thresholds:
```python
minutes_since_last_trade < 30 AND last_trade_was_loss  → "quick re-entry after loss"  (T7)
consecutive_wins >= 3 AND size_vs_rolling_avg > 1.3    → "elevated sizing after streak" (T2)
entry_at_day_extreme                                    → "entry at daily extreme" (FOMO)
```
Factor computer (`EmotionalIndicatorFactor.compute()`) and evidence template are in sync. No drift.

### T3 Time-of-Day Confirmed Absent from Evidence Layer

`_emotional_detail()` has no time-of-day check. `timing_quality` factor renders quality label ("strong"/"moderate"/"weak"/"poor") but not period-specific accuracy. "Friday 2-4pm: accuracy 39% vs 54% baseline" is NOT surfaced in any evidence template. The fix is in `pattern_detector.py` (add `_detect_time_of_day`), not in `evidence.py`. **Confirms MAP #106 is the correct intervention.**

### Critical Design Discipline: "Decision Context" Not "Emotional"

`FACTOR_DISPLAY = {"emotional_indicator": "Decision context", ...}`

The UI renders "Decision context: quick re-entry after loss" — never the word "emotional." PD §10.2 explicitly specifies: *"Displayed as 'Decision Context' in UI (never 'emotional')."* Code follows the spec exactly. Good design.

### `render_trust_analysis()` is Implemented ✅

```python
def render_trust_analysis(self, factor_weights) -> str:
    rows = sorted(((name, weight) for name, weight in factor_weights.items()),
                  key=lambda item: (-item[1], item[0]))
    rendered = [f"{FACTOR_DISPLAY.get(name)} {weight:.2f}" for name, weight in rows]
    return "Trust weighting: " + "; ".join(rendered) + "."
```
Produces: `"Trust weighting: Signal alignment 0.94; Timing 0.67; Regime fit 0.52; ..."` The `/trust-analysis` endpoint in context_router.py feeds directly into this. F2 hero feature is end-to-end complete.

### Trading PD Review — Complete Final State

**F3 NL Evidence: ✅ FULLY COMPLETE** — all 5 templates, factor breakdown, trust analysis.
**No additional scans required for Trading.**

**Final Trading scenario coverage:**

| Count | Status |
|---|---|
| 17 | ✅ Demo-ready today |
| 2 | ⚠️ Partial (T3 needs #106; T17 v1.1 recommendation layer) |
| 0 | ❌ Critical gaps |

**Path to 20/20:** #105 (0.5d AE variants) + #106 (1d time-of-day detector) → 19/20. T17 full recommendation → 20/20 (requires options RegimeRecommender integration, v1.1).


---

## Part 70 — DataOps Copilot: PD v1.6 vs Implementation (May 29, 2026)

### Source: dataops_pd_scan1-3.txt · Authority: dataops_copilot_design_v1_6.md

### Architecture: 37 Routes, 8 SC Components, Full Process-Tech Fusion

**Route inventory (corrected — DataOps uses app/*.py, not app/routers/):**
- `context_router.py` (57.7KB): 26 routes — main intelligence hub
- `ae_router.py` (20.7KB): 8 routes — OE-1→OE-5 AE pipeline
- SDK-mounted via main.py: scoring + conservation + evolution + transfer routers
- `dataops_status.py`: 4 routes — connector health
- **Total: 37+ routes, exceeds PD §4's "26 endpoints" specification**

**DomainConfig (6,5,6) — ✅ CONFIRMED exactly to PD spec:**
- Categories (6): schema_change, volume_anomaly, quality_anomaly, freshness_violation, pipeline_failure, transform_drift
- Actions (5): auto_approve, investigate, escalate_to_owner, pause_downstream, refer_to_specialist
- Factors (6): impact_scope, source_reliability, recurrence_frequency, downstream_urgency, data_freshness, business_criticality
- penalty_ratio=10.0, eta_confirm=0.05, eta_override=0.01, temperature=0.1

**All 8 SC Components Confirmed ✅:**

| SC | Component | Route |
|---|---|---|
| SC-9 | ReasoningPanel.tsx | /alert/{id}/factors (props-driven) |
| SC-10 | ConservationProjection.tsx (SDK shared) | conservation_router |
| SC-11 | CentroidTimeline.tsx + CentroidTimelineChart.tsx | /centroid-history |
| SC-12 | AccuracyAlertPanel.tsx + AccuracyAlerts.tsx | /accuracy-by-category |
| SC-13 | RuleGenealogy.tsx + RuleGenealogyTree.tsx | /pattern-origin |
| SC-14 | DecisionExplorer.tsx + DecisionExplorerPanel.tsx | /decisions |
| SC-15 | RuleLifecycle.tsx + RuleLifecyclePanel.tsx | /rule-lifecycle |
| SC-16 | AuditTrailViewer.tsx | /audit-trail/{alert_id} |

**Process-Tech Fusion WHERE→WHY→WHAT→LEARN→TRANSFER — all 5 stages ✅:**

| Stage | Route | Frontend |
|---|---|---|
| WHERE | /process-timeline | ProcessTimelinePanel.tsx |
| WHY | /bottleneck/{system}, /cross-graph-insight/{alert_id} | BottleneckPanel.tsx, CrossGraphInsightCard.tsx |
| WHAT | /transformations/{system}, /apply-fix | SchemaImpactPanel.tsx, ApplyFixModal.tsx |
| LEARN | /impact, /pattern-origin | AEImpactPanel.tsx, PatternOriginCard.tsx |
| TRANSFER | /transfer-status | TransferStatusPanel.tsx |

**Frontend richness: 45+ components** — exceeds PD design. Notable extensions: WhatIfReordering.tsx, DisruptionAnnotation.tsx, FactorAutoFill.tsx, IncidentReplayCard.tsx, ProfileArchetype.tsx.

### Design Concern 1 — cross-graph-insight is Fixture-Based

`/cross-graph-insight/{alert_id}` reads `_fallback_alerts_by_id()` — fixture alerts with pre-populated `cross_graph_refs` dicts (process_signal, erp_impact, root_cause). `graph_queries.py` (21.1KB) is `DataOpsGraphClient` — a fixture-loading wrapper, not live AGE traversal. The `slowdown_factor` computation is real math on fixture data.

**Demo impact:** The cross-graph story (WHY the bottleneck happened, $12K SAP impact, root cause in schema change) is compelling and credible for demo. For production: DI-5 Combination Discovery replaces pre-curated refs with live graph sweeps.

**D-I3 ("Combinations nobody queried") is ❌** — requires live DI-5. **D-I4 ("Cross-pipeline dependency") is ⚠️** — works in demo via fixtures.

### Design Concern 2 — apply-fix Returns Mock SAP Response

`_apply_fix_sap_response()` returns `"source": "fixture_demo"`. The WHAT stage is demo-functional but the SAP write is simulated. SAP connector reads (5.1KB) but the write path is mocked. Fine for Continental Tire demo. For production pilot: real SAP write needed (not a current MAP item).

### Design Concern 3 — No DataOps-Specific AE VariantSpec

ae_router.py has the full OE-1→OE-5 pipeline (`match_ae_rule()`, `_pattern_genealogy()`, `_generate_lifecycle_events()`) but zero VariantSpec dimensions. Same gap as Trading (#105) and S2P (#104).

**Needed variants for DataOps:**
- `alert_routing_threshold`: auto_approve confidence 0.86→0.91
- `escalation_criteria`: escalate_to_owner vs pause_downstream triggers
- `pattern_sensitivity`: recurrence detection 3→5 occurrences before "recurring" classification

**New item #107 DOPS-AE-VARIANTS (0.5d).**

### Extensibility Architecture — CONFIRMED CORRECT

`create_X_router()` factory pattern throughout main.py enables zero-surgery addition:
- New scenarios → route in context_router.py or new factory file
- New connectors → drop alongside celonis_connector.py / sap_connector.py
- New AE variants → add VariantSpec (#107 creates the initial config)
- DI Phase A-C → 11 new files, zero changes to existing 37 routes

The factory pattern (create_scoring_router, create_conservation_router, create_evolution_router, create_ae_router) is the right extensibility design. Adding Intelligence Map (DI-2) = one new React component + one new router factory. No surgery to existing code.

### 22-Scenario Coverage — Final State

**Critical reframing: The 7 DataOps ❌ are ALL Level 5-6 (DI Phase A-C roadmap). Level 1-4 (built scope) is 10/11 ✅.**

| Scenario | Level | Status | Key Feature |
|---|---|---|---|
| D-M1 Alert fatigue | 1-3 | ✅ | /alerts + conservation auto-expand |
| D-M2 Quality metrics improving | 3 | ✅ | /centroid-history + IKS |
| D-M3 Engineer who quit | 3-4 | ✅ | SC-11/12 + DK fingerprint |
| D-M4 Quarterly close | 3 | ✅ | /recommendation + conservation |
| D-M5 Can't hire engineers | 3 | ✅ | Conservation expansion |
| **D-M6 Business users locked out** | **5** | **❌** | **DI-3 NL engine (7wk roadmap)** |
| D-M7 $400K project stale | 3 | ✅ | Centroid persistence |
| D-I1 Self-aware data per-source | 5 | ❌ | DI-1 Source Profiler (roadmap) |
| D-I2 Metadata trust | 5 | ❌ | DI-1 (roadmap) |
| D-I3 Combinations nobody queried | 6 | ❌ | DI-5 live discovery (roadmap) |
| D-I4 Cross-pipeline dependency | 4 | ⚠️ | fixture-based; live = DI-5 |
| D-I5 Auto-approval expansion | 3 | ✅ | Conservation law |
| D-I6 Per-consumer quality routing | 4 | ⚠️ | Conservation works; per-consumer = DI-4 |
| D-I7 Acquisition advisor | 6 | ❌ | DI-8 (roadmap) |
| D-I8 Data monetization | 6 | ❌ | DI-8 (roadmap) |
| D-I9 Connect my data NL | 5 | ❌ | DI-4 (roadmap) |
| D-I10 Quality-aware NL | 5 | ❌ | DI-3 (roadmap) |
| D-I11 Fix transferred 6 pipelines | 4 | ✅ | /transfer-status + PatternOriginCard |
| D-I12 Three-channel improvement | 3-4 | ✅ | centroid + graph + DK in one click |
| D-I13 Shadow-tested rejected | 4 | ✅ | /operational-rules + /impact AE shadow |
| D-I14 Agent trust infrastructure | 5 | ⚠️ | DK weights exist; Trust API = DI-1 |
| D-I15 Data product IKS | 5 | ⚠️ | IKS exists; per-product = DI-1 |

**10✅ · 5⚠️ (all fixture/partial) · 7❌ (all DI roadmap)**

### Copilot Comparison — Built Scope

| Copilot | Built scope ✅ | Critical gap IN built scope | Expansion roadmap |
|---|---|---|---|
| Trading | 17/20 | 0 | T17 options (v1.1), #105, #106 |
| S2P | 13/16 | **1 — G12 Situation Analyzer** | DI-equivalent TBD |
| DataOps Level 1-4 | 10/11 | 0 | DI-1→DI-11 (14wk Level 5-6) |

DataOps Level 1-4 is MORE complete than S2P. The 7 DataOps ❌ are deliberate roadmap, not missing foundational features.

### New MAP Items from DataOps PD Review

| MAP# | ID | Effort | What |
|---|---|---|---|
| **#107** | DOPS-AE-VARIANTS | 0.5d | DataOps-specific VariantSpec: alert_routing_threshold (0.86→0.91), escalation_criteria (owner vs downstream triggers), pattern_sensitivity (3→5 recurrences). Same pattern as Trading #105 and S2P #104. |

DI-1→DI-11 are already in MAP (items #62-#72, Tiers 7-10). No new DI items needed — they're all correctly mapped.


---

## Part 71 — DataOps Gap Closure Plan (May 29, 2026)

### Position Correction

The "deliberate roadmap" framing in Part 70 was wrong. DataOps is a high-value copilot. The 8 ❌ scenario gaps are **active deficits** that need a concrete closure plan — not a rationalization. The fact that DI Phase A-C wasn't built yet is a sequencing problem, not an architectural decision to accept missing scenarios.

**Correct statement:** DataOps has 8 unbuilt scenarios (D-M6, D-I1, D-I2, D-I3, D-I7, D-I8, D-I9, D-I10) that are demo-blocking and outreach-blocking for the Data Intelligence product story. They require DI Phase A-C (DI-1→DI-8). No exceptions.

### DI-1 SOURCE-PROFILER: Highest-Leverage Item in the Platform

DI-1 (2wk) is the single item with the most scenario unlock power across the entire MAP:
- Directly closes: D-I1 (self-aware data), D-I2 (metadata trust), D-I14 (agent trust), D-I15 (per-product IKS) — **4 scenarios in 2 weeks**
- Unblocks: DI-2, DI-3, DI-4, DI-5 — every other DI item
- Cross-copilot benefit: per-source trust is domain-agnostic — SOC gets per-SIEM trust, Purchasing gets per-QuickBooks trust

No other item in the MAP closes 4 scenarios simultaneously.

### Scenario Gap Closure Critical Path

| Step | Item | Effort | Scenarios Closed | Cumulative ✅ |
|---|---|---|---|---|
| Start | Built (v1.5) | — | D-M1-5, D-M7, D-I5, D-I11, D-I12, D-I13 | 10/22 |
| + D-CEL confirm | D-CEL frontend | confirm status | prerequisite gate | 10/22 |
| + 2wk | **DI-1 SOURCE-PROFILER** | 2wk | D-I1, D-I2, D-I14, D-I15 | **14/22** |
| + 1wk | DI-4 PROMPT-INTEGRATOR | 1wk | D-I6, D-I9 | **16/22** |
| + 3wk | DI-3 NL-QUERY-ENGINE | 3wk | D-M6, D-I10 | **18/22** |
| + 3wk | DI-5 COMBINATION-DISCOVERY | 3wk | D-I3, D-I4 | **20/22** |
| + 2wk | DI-8 ACQUISITION-ADVISOR | 2wk | D-I7, D-I8 | **22/22** |

**Total: ~11 weeks to full 22/22 scenario coverage.**
DI-2 (Intelligence Map v1, 2wk), DI-6 (Data Valuation, 2wk), DI-7 (Map v2, 1wk), DI-9-11 (connectors, 3wk) run alongside this path without adding to critical path duration.

### Priority Elevation Required in MAP

Current MAP placement: DI items in Tiers 7-10 (distant future, after many other copilots).
Required MAP placement for DataOps high-value status:

| New Tier | Items | Timing |
|---|---|---|
| Tier 4.5 (IMMEDIATE after Loom) | DI-1, DI-2 | Start as soon as D-CEL confirmed |
| Tier 5 (parallel with S2P G12) | DI-3, DI-4 | 4wk after DI-1 starts |
| Tier 5.5 | DI-5, DI-6 | 7wk after DI-1 starts |
| Tier 6 | DI-7, DI-8 | 10wk after DI-1 starts |
| Parallel anytime | DI-9, DI-10, DI-11 | No dependencies — start with DI-1 |

### Prerequisite: D-CEL Status Confirmation

MAP v5.138 lists D-CEL (1.5d — SAP + Celonis real connectors + frontend) as QUEUED. Scans confirmed backend connectors built (`celonis_connector.py` 5.6KB, `sap_connector.py` 5.1KB). Frontend integration status unknown.

**Required scan before DI-1 starts:**
```powershell
Get-ChildItem "$env:CLAUDE_SDK\apps\dataops\frontend\src" -Filter "*.tsx" -Recurse |
    Select-String "celonis|Celonis|SAP|sap" | Select-Object -First 10
```
If frontend Celonis/SAP components exist → D-CEL is DONE → DI-1 starts immediately.
If not → D-CEL 1.5d Codex prompt is the first action.

### The 5 ⚠️ Scenarios — Upgrade Path

| Scenario | Current | Closes When | Effort |
|---|---|---|---|
| D-I4 Cross-pipeline dependency | ⚠️ fixture | DI-5 live traversal | +3wk from DI-1 |
| D-I6 Per-consumer quality routing | ⚠️ conservation only | DI-4 Prompt Integrator | +1wk from DI-1 |
| D-I14 Agent trust infrastructure | ⚠️ DK weights only | DI-1 Trust API endpoint | 2wk |
| D-I15 Data product IKS | ⚠️ IKS exists, no per-product | DI-1 per-product breakdown | 2wk |

All 4 ⚠️ scenarios are closed by DI-1 or DI-4 — both in the first 3 weeks of Phase A.

### Revised DataOps Scenario Status

After this correction, the document record shows:

**Today (pre-DI):** 10✅ · 4⚠️ · 8❌ = 10/22 demo-ready. **This is a gap, not a feature.**

**After DI Phase A (4wk):** 16✅ · 0⚠️ · 6❌

**After DI Phase B (7wk):** 18✅ · 0⚠️ · 4❌

**After DI Phase C (11wk):** 22✅ · 0⚠️ · 0❌

**Full DataOps demo: 11 weeks from DI-1 start.**


---

## Part 72 — D-CEL Confirmed DONE: DI-1 Unblocked (May 29, 2026)

### D-CEL Frontend Status: ✅ CONFIRMED DONE

`ApplyFixModal.tsx` is fully wired to SAP:
- "SAP Write-back" / "Apply Fix to SAP S/4HANA" / "Applied to SAP S/4HANA" labels
- Renders `response.sapResponse?.d?.PurchaseOrder` (PO number)
- Renders `response.sapResponse?.d?.Status` (SAP status)

The WHAT stage of Process-Tech Fusion is complete: frontend calls backend, backend calls SAP connector, SAP response (PO + status) is rendered in the modal with production-quality S/4HANA branding. Backend returns `fixture_demo` source — real SAP writes are a production upgrade, not a demo requirement.

**D-CEL: DROP from QUEUED.** Both backend connectors (`celonis_connector.py` 5.6KB, `sap_connector.py` 5.1KB) and frontend (`ApplyFixModal.tsx`, `CelonisBadge.tsx`, `SAPDataBadge.tsx`, `EnterpriseHealthBar.tsx`) are confirmed built and wired.

### Consequence: DI-1 SOURCE-PROFILER Starts Immediately

No prerequisite work remains. DI-1 Codex prompt can be written now.

DI-1 (2wk) closes 4 scenarios immediately upon delivery:
- D-I1: Every data asset knows its own reliability ✅
- D-I2: Metadata trust — catalog that knows it's wrong ✅
- D-I14: Agent trust infrastructure ✅
- D-I15: Every data product gets an IQ score ✅

**Gap count after DI-1: 8❌ → 4❌. DataOps: 14/22 scenarios ✅.**


---

## Part 73 — Purchasing Copilot: Domain Reconciliation (May 29, 2026)

### Finding: Domain Mismatch Between PD v1.1 and Implementation

PD v1.1 targets $10-50M manufacturers (Dave's Ohio machining shop, Maria's food distributor). Implementation uses food service domain:
- **Categories:** protein, produce, dairy, dry_goods, beverages
- **Actions:** order_as_planned, order_more, order_less, skip
- **Factors:** expected_demand, day_of_week, weather_forecast, event_flag, historical_waste, supplier_lead_time, price_memory_index
- **Routes:** `/waste-history/{item}`, `/weather`, `/today-summary`

Legacy migration code (`_migrate_legacy_centroids`) shows evolution from (5,4,6) → (5,4,7) within the food service domain.

### Assessment: Food Service Is the Stronger Fit

The food service domain is actually superior to the manufacturing domain for the purchasing copilot position, for five reasons:

**1. Unique action space — no S2P overlap.** Manufacturing purchasing actions (approve/hold/flag/escalate) are isomorphic to S2P invoice exception routing. Food service actions (order_more/less/skip/as-planned) are genuinely novel: quantity optimization under perishable demand uncertainty. No competitor addresses this.

**2. Faster compounding.** Restaurant orders 3×/week = 1,000 verified decisions in 3 months. Manufacturing: same milestone in 9-12 months. Food service reaches IKS convergence 3-4× faster.

**3. Factor space coherence — no infrastructure dependencies.** Manufacturing factors need LME feeds, contract databases, and clean QBO data. Food service factors compute from Day 1: weather API (free), timestamps (inherent), calendar (simple), delivery history (from first order). DiagonalKernel works with what restaurants already have.

**4. Trust trap is more visceral.** Manufacturing: "quoted price is noisier than delivery history." Requires explaining supplier evaluation methodology. Food service: "Your intuition about Friday night (σ=0.34) predicts worse than Tuesday afternoon weather (σ=0.07, weight 94%)." Every F&B operator immediately recognizes this. Gap between gut feel and actual signal IS their daily pain.

**5. Distinct buyer — zero S2P overlap.** Restaurant owner / F&B director is not a CPO. Not a procurement coordinator. They have zero purchasing intelligence tools today. S2P can't shrink to them. Manufacturing purchasing overlaps too much with S2P's lower end.

### Scenario Translation: 17/19 Survive the Domain Shift

| PD Scenario | Food Service Version | Status |
|---|---|---|
| P1 Overpaying | Food cost drift — protein prices creeping | ✅ translates |
| P2 Par levels | Reorder quantities from consumption patterns | ✅ (implemented) |
| P3 Auto-approve expansion | System proves weekly produce order is safe | ✅ |
| P4 Same overcharge Q4 | Seasonal seafood/produce pricing premium | ✅ |
| P5 Best purchaser left | New chef lacks 8 years of waste pattern data | ✅ |
| I1 Trust trap | Gut event demand vs weather signal | ✅ stronger |
| I2 Price memory | "Last negotiated salmon rate: $12.40 (Oct 2025)" | ✅ |
| P6 12 suppliers same job | 3 produce suppliers behaviorally identical | ✅ |
| P7 Supplier declining | Produce supplier OTIF dropping → find backup | ✅ |
| M8 Market vs supplier | "Fish +15% — Atlantic cod LME: +8%. Supplier adding 7%" | ✅ |
| I4 Invisible correlation | Packaging price tracks shipping not paper index | ✅ |
| P8 Pattern nobody queried | Weekend demand correlates with local sports calendar | ✅ |
| P9 Data quality excuse | Works from POS + invoice history Day 1 | ✅ |
| I3 Warns about itself | New chef's decisions diverge from learned pattern | ✅ |
| I5 Format costs $4K/month | Supplier invoice format change → manual corrections | ✅ |
| I7 Proof bank needs | Conservation GREEN 180 days → credit line proof | ✅ |
| P10 Tariff/supply shock | Avian flu → egg prices, supply disruption response | ✅ |
| I8 One plant taught six | Chain: one location's learning → all others Day 1 | ✅ |
| M1/M2 Table stakes | Food cost % dashboard / POS receipt vs invoice match | ✅ rewrite |

### What Changes

**PD v1.2 needed (strategic reframe, 0.5d):**
- Buyer: Restaurant owner ($2-10M), café chain (3-5 locations), hotel F&B — not Ohio machining shop
- Personas: Marco (Italian restaurant), Lisa (café chain), Rafael (hotel F&B)
- Connector priority: Toast POS / Lightspeed first, QBO second (restaurants use QBO for accounting, POS for orders)
- 3 new food-service-specific scenarios: weather model, event demand, day-of-week optimization

**MAP items — impact:**
- P1 PUR-DOMAIN-CONFIG: ✅ DONE (food service preset exists)
- P2 PUR-SYNTH-DATA: Needs food service archetypes (30 restaurants, not 50 manufacturers)
- P6 PUR-QBO-CONNECTOR: Survives (restaurants use QBO) — but Toast connector is higher priority
- P7 PUR-FACTORS: 6-7 factor computers likely exist — needs scan to confirm
- P6 connector priority: Add PUR-TOAST-CONNECTOR as new P6a (ahead of QBO)

**New MAP item:**
- PUR-DOMAIN-REFRAME: 0.5d — PD v1.2 rewrite (food service buyers, personas, scenario translations, connector priority update)

### Scanning Note

Scan commands hung during execution. Route inventory and factor computer confirmation pending. Once reframing is confirmed, single targeted scan: route inventory + factor computers + test count.

### Standing Principle

The implementation is not wrong — the PD is misaligned with it. The code evolved to the better domain. PD v1.2 should catch up to the code, not the other way around.


---

## Part 74 — Purchasing Copilot: PD v1.2 Written (May 29, 2026)

### PD v1.2 Document

`purchasing_copilot_pd_v1_2.md` — 835 lines. Supersedes v1.1.

Full reframe from manufacturing SMB to food service / restaurant domain.
6 clusters (A-F), 22 scenarios, 4 buyer personas, Toast-first connector priority.

### Domain Confirmed: Food Service

| Spec | PD v1.2 | Implementation |
|---|---|---|
| Categories | protein, produce, dairy, dry_goods, beverages | ✅ Confirmed |
| Actions | order_as_planned, order_more, order_less, skip | ✅ Confirmed |
| Factors | expected_demand, day_of_week, weather_forecast, event_flag, historical_waste, supplier_lead_time, price_memory_index | ✅ Confirmed |
| Tensor | (5,4,7) | ✅ Confirmed |
| Migration | (5,4,6) → (5,4,7) via _migrate_legacy_centroids() | ✅ Confirmed |

### New in v1.2: Cluster F (Food Service Intelligence)

Three scenarios native to food service — no manufacturing or S2P equivalent:

- **F1 "The Weather Nobody Checked":** weather_forecast factor (DK weight 94%) adjusts protein/produce orders 3 days before demand drop. "Rain Saturday: reduce protein 30%."
- **F2 "The Event We Forgot":** event_flag factor (DK weight 81%) learns which events move demand. Marathon Sunday: covers +65%, protein +80%.
- **F3 "Tuesday Is Not Friday":** day_of_week factor (DK weight 88%) learns two-tier par. Tuesday = 62% of Friday demand. Waste reduction: $180/week.

These 3 scenarios are UNIQUELY competitive — no food service purchasing tool (BlueCart, MarketMan, Upserve) uses weather, event, or day-of-week signals in ordering recommendations.

### Manufacturing Vertical: Sequenced, Not Abandoned

PD v1.1's manufacturing scenarios (Midwest Steel Q4 premiums, Chen-Lin lead times, tariff shock recovery) are valid future work documented in PD v1.2 §12 Q7 as a v2.x vertical using the same DomainConfig architecture. DomainShape (5,4,7) maps cleanly — only the category/factor names change, all platform machinery is domain-agnostic.

### Current Status and Next Actions

| Item | Status |
|---|---|
| P1 PUR-DOMAIN-CONFIG | ✅ DONE |
| P3 PUR-CENTROIDS | ✅ DONE (with migration) |
| P2 PUR-SYNTH-DATA | **Next action — 2d** |
| P6a PUR-TOAST-CONNECTOR | **New P0 priority — 2w** |
| Scan to confirm Phase 0/1 | Short targeted scan (run each line separately) |


---

## Part 75 — Full Platform State & Priority Stack (v36.0 · May 29, 2026)

### Supersedes Part 54. Authoritative platform state after all PD reviews and scans.

---

### Platform State — Post PD Review Session

| Metric | Value | Source |
|---|---|---|
| Total tests | SDK 788, TRD 704, PUR 147, DOPS 175, S2P 854 = **2,868** | MAP v5.138 baselines |
| Total tracked prompts | ~70 | MAP v5.138 |
| Confirmed DROPs | **~48 of ~70** | MAP §FINAL |
| Active items | **~36** | MAP §FINAL |
| Cumulative DONE | **~45** | MAP §FINAL |
| New items this session | **6 active** (#103-#107, #109) | MAP §FINAL |
| Standing Rules | **47** | Rule #47: pre-check-driven prompts only |
| P0 blocker | **#102 Trading bundle stale** | d=7 bundle vs d=10 preset |

---

### B11-14 Pre-Scan Queries — Formally Closed

All pending queries from the B11-14 pre-scan (Part 65) are answered:

| Query | Answer | Part |
|---|---|---|
| Is S2P-F19 (payment) built? | ✅ DROP — DEMO_PAYMENT_BEHAVIOR fully computed | 65 |
| Is S2P-F21 (disruption) built? | ✅ DROP — 4 scenarios with _apply_mitigation() math | 65 |
| Is CONSERVATION-PERSIST needed? | ✅ DROP — pure SQLite derivation, no state to persist | 65 |
| Is GAP-H2-DEMO built? | ✅ DROP — demo.py includes all 3 SDK copilots, TransferDetector complete | 65 |
| Is GRAPH-TPC built? | ✅ DROP — all 3 graph contracts defined | 65 |
| Is BLOCK-1.2 built? | ✅ DROP — ArchetypeGenerator fully implemented | 65 |
| Is S2P-F18 P1+P2 built? | ✅ DROP — connectors + insight router both confirmed | 65, 67 |
| TRD-MULTI-TRADER scope? | 30 min — TraderProfileService 20 methods built, add trader_id field | 65 |
| TRD-VERIFICATION-MODEL scope? | 2h — r_multiple/execution_quality formulas, all inputs present | 65 |
| S2P-F10 Financial Impact status? | Still redesign needed — fixture→OutcomeReceipt source switch | 65, 67 |
| S2P-F8 Factor Proposer scope? | 1d — /dk-weights + /contribution built, only ranking logic missing | 65, 67 |
| SDK-DOCS scope? | 0.5d — README exists, not blank slate | 65 |
| Is D-CEL done? | ✅ DROP — ApplyFixModal renders sapResponse, full SAP wiring confirmed | 72 |
| Is DI-1 unblocked? | ✅ YES — start immediately | 72 |
| Is demo bundle still broken? | ✅ P0 BLOCKER — d=7 vs d=10, fix in 15-30 min (#102) | MAP §6 |
| Which Trading items are DROPs? | TRD-REALTIME-SCORE, REGIME, CORRELATION, VIX, PATTERNS, PROMOTION, NL, TRUST, CONSERVATION all built | 68 |
| Is S2P G12 built? | ❌ NOT BUILT — zero code found | 67 |
| What's the S2P AE variant status? | 2/4 families — #104 adds escalation_criteria + triage_weights | 67, Part 67 |
| OutcomeReceipt — what's missing? | Hash chain IMPLEMENTED. Missing: amount_recovered, cycle_time_saved, weight_updated, exportable | 67 |

---

### Copilot Scenario Coverage — Complete State

**Trading: 17/20 ✅ — Zero critical gaps**

| Status | Scenarios |
|---|---|
| ✅ (17) | T1 trust radar, T2 overconfidence, T4 regime, T5 scaling, T6 execution gap, T7 revenge, T8 per-trader, T9 strategy stopped, T10 paper→live, T11 import, T12 playbook, T13 tariff, T14 regime shift, T15 revenge VIX32, T16 volatile edge, T18 correlation, T19 earnings, T20 VIX timing |
| ⚠️ (2) | T3 Friday afternoon (no time-of-day detector), T17 IV/RV (v1.1 recommendation layer) |
| ❌ (0) | None |

**After #105 (0.5d) + #106 (1d): 19/20 ✅. T17 full = options RegimeRecommender v1.1.**

---

**S2P: 13/16 ✅ — One critical gap (G12)**

| Status | Scenarios |
|---|---|
| ✅ (13) | S1 exception rate, S2 autopilot, S3 sourcing, S5 pattern, S6 expertise, S7 duplicates, S9 novelty, S10 persistence, S11 early warning, S12 payment, S15 caution, S16 Celonis |
| ⚠️ (3) | S4 factor proposer (ranking logic 1d), S8 lead time (F14 aggregation 1-2wk), S13 AE tunes (2/4 families, #104 0.5d) |
| ❌ (1) | **S14 "Not a Script — A Decision" — G12 Situation Analyzer not built (3-4wk)** |

**After #103 + #104 + S4 (2d): 15/16 ✅. After G12: 16/16 ✅.**

**G12 is the reasoning pillar.** Every competitor shows auto-approve rate improvement. S14 is the only scenario that shows procurement AI reasoning from context ("Copper rose 4.8%. Contract §7.3 allows pass-through. Within bounds. Accept."). Without S14, S2P is a better AP automation story. With S14, it's category-defining.

---

**DataOps: 10/11 ✅ Level 1-4 — 0/11 Level 5-6 (active gap, not roadmap)**

| Status | Scenarios |
|---|---|
| ✅ (10) | D-M1-M5, D-M7, D-I5, D-I11, D-I12, D-I13 |
| ⚠️ (5) | D-I4 (fixture), D-I6 (conservation only), D-I14 (DK weights, no Trust API), D-I15 (IKS exists, no per-product) |
| ❌ (8) | D-M6, D-I1, D-I2, D-I3, D-I7, D-I8, D-I9, D-I10 — all Level 5-6, all active deficits |

**Gap closure path:** DI-1 (2wk) → 14/22. DI-4 (1wk) → 16/22. DI-3 (3wk) → 18/22. DI-5 (3wk) → 20/22. DI-8 (2wk) → **22/22 in 11 weeks from DI-1 start.**

**DI-1 is unblocked. Start immediately.** Closes D-I1, D-I2, D-I14, D-I15 simultaneously. Unblocks DI-2, DI-3, DI-4, DI-5. Highest leverage item in the MAP.

---

**Purchasing: 3/22 — Food service domain confirmed (PD v1.2 written)**

Domain mismatch resolved: implementation is food service (protein/produce/dairy/dry_goods/beverages), PD v1.1 was manufacturing. Food service is the superior domain — unique action space (order_more/less/skip), faster compounding (3× decision velocity), cleaner factors (weather_forecast/day_of_week from Day 1). PD v1.2 written (835 lines, 22 scenarios, Cluster F new food service intelligence).

P1 PUR-DOMAIN-CONFIG ✅ DONE. P3 PUR-CENTROIDS ✅ DONE. First active action: **P2 PUR-SYNTH-DATA (2d)** — food service archetypes.

---

### Platform-Wide AE Variant Gap — 3d Fix Across All Copilots

**Every copilot has the AgentEvolver pipeline but zero (or incomplete) domain-specific VariantSpec configs.** Discovered this session as a cross-copilot pattern.

| Copilot | Pipeline | Variants | Gap | Fix |
|---|---|---|---|---|
| S2P | ✅ | 2/4 families | escalation_criteria + triage_weights | #104, 0.5d |
| Trading | ✅ | 0 families | alert_threshold, pattern_sensitivity, regime_boundary | #105, 0.5d |
| DataOps | ✅ | 0 families | alert_routing_threshold, escalation_criteria, pattern_sensitivity | #107, 0.5d |
| Purchasing | ✅ (SDK) | 0 (planned in PD v1.2) | order_quantity_threshold, weather_sensitivity, event_lead_time, price_memory_alert | P22, Phase 1.1 |

All three immediate fixes use identical VariantSpec patterns. One Codex session, three copilots.

---

### Design Concerns — Consolidated Registry (All Copilots)

| # | Copilot | Concern | Severity | Fix |
|---|---|---|---|---|
| DC-1 | S2P | G12 Situation Analyzer not built | 🔴 Critical | #43, 3-4wk |
| DC-2 | S2P | AE promotion_min_samples=10 (too low for routing_threshold variants) | 🟡 Medium | Raise to 50 in #104 |
| DC-3 | S2P | S8 lead time: supplier_history returns events not aggregations | 🟡 Medium | #41, 1-2wk |
| DC-4 | S2P | S4 factor proposer: /contribution built, ranking logic missing | 🟡 Medium | 1d standalone |
| DC-5 | Trading | T3 time-of-day: no _detect_time_of_day in pattern_detector | 🟡 Medium | #106, 1d |
| DC-6 | Trading | TRD-MULTI-TRADER: trader_id field missing from NormalizedTrade | 🟢 Low | #27, 30 min |
| DC-7 | DataOps | cross-graph-insight fixture-based (not live AGE traversal) | 🟡 Medium | DI-5, 3wk |
| DC-8 | DataOps | apply-fix returns mock SAP response (fixture_demo) | 🟡 Medium | Production upgrade, not MAP item |
| DC-9 | All | AE VariantSpec configs missing across all copilots | 🟡 Medium | #103-#107, 3d |
| DC-10 | Purchasing | Domain was misaligned with implementation | 🟢 Resolved | PD v1.2 written |
| DC-11 | S2P | OutcomeReceipt missing: amount_recovered, cycle_time_saved, weight_updated, exportable | 🟢 Low | #103, 0.5d |
| DC-12 | DataOps | DI Phase A-C (Level 5-6) = 8 active scenario gaps | 🔴 High | DI-1→DI-8, 11wk |

---

### Priority Action Stack — v36.0 Final

```
P0 — Before next Codex session:
  #102 DEMO-BUNDLE-REGEN-D10   15-30 min   Trading demo broken (d=7 vs d=10)
  #92 INVENTORY-SCRIPTS check  5 min       One-line confirm or write prompt

Sprint 1 — Quick wins (4d total, all can run in parallel):
  #103 S2P-G10-SUPPLEMENT      0.5d        4 missing OutcomeReceipt fields
  #104 S2P-G13-SUPPLEMENT      0.5d        S2P AE: escalation_criteria + triage_weights
  #105 TRD-F12-VARIANTS        0.5d        Trading AE: 3 variant dimensions
  #106 TRD-T3-TOD              1d          _detect_time_of_day in pattern_detector.py
  #107 DOPS-AE-VARIANTS        0.5d        DataOps AE: 3 variant dimensions
  #27 TRD-MULTI-TRADER         30 min      Add trader_id field (2 lines)
  #38 S2P-F8 ranking logic     1d          Factor proposer recommendation

Sprint 2 — Platform expansion (parallel tracks):
  DI-1 SOURCE-PROFILER         2wk         UNBLOCKED — closes 4 DataOps gaps
  P2 PUR-SYNTH-DATA            2d          Food service supplier archetypes
  P6a PUR-TOAST-CONNECTOR      2wk         Restaurant POS connector
  DI-2 INTELLIGENCE-MAP-V1    2wk         Parallel with DI-1

Sprint 3 — Critical gap (after Sprint 2):
  #43 S2P-G12 SITUATION-ANALYZER  3-4wk   THE critical gap — reasoning pillar
  DI-3 NL-QUERY-ENGINE            3wk     After DI-1

After Sprint 3:
  DI-4/5/6/7/8               8wk          Complete DataOps 22/22
  P9-P15 Purchasing Phase 1   10wk         Full purchasing copilot v1.0
  S2P Phase 1.1               6-8wk        Discovery + self-tuning
```

---

### DROP Totals — Authoritative

| Epoch | DROPs | Running Total |
|---|---|---|
| Original list (before B6-10) | 7 | 7 |
| Batch 6-10 deep analysis (Parts 55-56) | 18 | 25 |
| Parts 57-62 PW fixes + DataOps | 7 | 32 |
| B11-14 pre-scan (Part 65) | 8 (#47×2, #48, #50, #58, #59, #60, #61) | 40 |
| PD reviews — Trading scans | ~5 (realtime, regime, correlation, vix, patterns) | ~45 |
| PD reviews — S2P scan 2 (#47 full) | 1 | ~46 |
| D-CEL + PUR P1/P3 + #108 (Parts 72-74) | 4 | **~48** |
| **Total** | **~48** | **of ~70 tracked prompts** |

---

### What the Next Developer Session Sees

**Clean state:**
- 0 open P1 bugs
- 0 PW hard failures (2 flaky edge cases, #97 + #98, both spec issues not code)
- Storage fully closed (RL + evolution persistence shipped)
- All 5 copilot PD reviews complete

**What to build next (in order):**
1. Fix Trading demo bundle (#102, 15 min)
2. Three AE variant configs (#104, #105, #107, 1.5d total)
3. Time-of-day pattern detector (#106, 1d)
4. Start DI-1 Source Profiler (2wk, unblocked)
5. Start G12 Situation Analyzer (3-4wk, in parallel or sequential)

**The compounding story for all copilots is demo-ready except:**
- S14 reasoning scenario (S2P) — G12 is the blocker
- 8 Level 5-6 DataOps scenarios — DI Phase A-C is the path
- Full Purchasing story — PD v1.2 written, P2 is the next build step


---

## Part 76 — Final Pre-Handoff Scan Results (May 29, 2026)

### Purchasing Factor Computers — factors.py Does NOT Exist

`apps/purchasing/backend/app/factors.py` — file not found. Factor computation logic for
the food service domain is embedded in route handlers:
- `/weather` → weather_forecast factor data
- `/waste-history/{item}` → historical_waste factor data
- `/today-summary` → expected_demand factor data
- `/item/{name}/profile` → supplier_lead_time factor data

No formal `FactorComputer` classes exist. **P7 PUR-FACTORS scope confirmed: 1wk** —
extract + formalize as proper FactorComputer classes (expected_demand, day_of_week,
weather_forecast, event_flag, historical_waste, supplier_lead_time, price_memory_index).
This is refactoring embedded logic into the standard protocol, not ground-zero.

### #92 INVENTORY-SCRIPTS — ✅ CONFIRMED DROP

`tab_inventory.py` exists in `/scripts/`. This IS the inventory script. DROP confirmed.

**Scripts directory full list:**
- `demo_warm_start.py` — warm start demo
- `discovery_demo.py` — discovery demo
- `evolve_demo.py` — evolution demo
- `preseed_all_copilots.py` — 1,200 HTTP calls per session (replaced by DEMO-BUNDLE)
- `regenerate_demo_bundles.py` — **#102 fix target** (add 3 options factors, re-run)
- `tab_inventory.py` — inventory script (#92 DROP)
- `transfer_demo.py` — transfer demo

**#102 fix is confirmed:** `regenerate_demo_bundles.py` exists. Update DOMAINS[0]
to include `options_delta_exposure`, `options_iv_percentile`, `options_gamma_risk`.
Re-run. Commit. 15-30 min.

### Final Active Count

| Step | Count |
|---|---|
| v5.138 active | 49 |
| Session DROPs (§FINAL list) | −12 |
| #92 INVENTORY-SCRIPTS | −1 |
| New items added (#103-#109) | +6 (one immediately DONE) |
| **v5.139 final active** | **~35** |
| **Total DROPs all time** | **~49 of ~70** |

### Handoff Status: READY

All Sprint 1 prompts are fully scoped. No remaining unknowns block any
immediate Codex work. PW gates (Trading rerun, SOC #15, S2P #17) go to
the coding session as Round 0.


---

## Part 77 — Gemini Evaluation: Purchasing Copilot Pitch Materials (May 29, 2026)

### Source: External evaluation of PD v1.2 pitch scenarios and positioning

### Confirmed Strong — Do Not Change

| Element | Rating | Why It Works |
|---|---|---|
| P2 Departure (Rosa left) | ✅ Best overall | Emotional hook + hard metric ($28K). Universal fear. Personalizes data retention. |
| P3 Price Memory | ✅ Top 3 | Concrete, universal. Supplier sneaking price hikes because new chef doesn't know negotiated rate. |
| P8 Competitor positioning | ✅ Top 3 | Validates incumbents while exposing the learning gap. BlueCart/MarketMan/Upserve are known. |
| Weather intelligence (F1) | ✅ Extremely compelling | Specific, realistic, operators pay to automate this blind spot. |
| Events intelligence (F2) | ✅ Highly compelling | $1,200 lost to marathon 86's. Learning which events actually drive demand vs noise. |
| Trust trap concept (I1) | ✅ Concept excellent | "The factor you trust most predicts least" — novel category. |
| Chain learning for Lisa | ✅ Extremely compelling | $200-300/location/month is easy yes for ops director. |

### What Was Changed and Why

**P6 (Day of Week) — reframed around dynamic par intelligence**

Old framing "Tuesday is not Friday" rated 5/10 — too obvious, sounds like an observation not a solution. New framing leads with the waste number ($180/week) and dynamic par tiers. Day-of-week structure is the mechanism, not the hook.

**P9 (Day 1) — removed vaporware claim**

"Trust trap visible in 20 minutes before lunch" was called out as vaporware. Restaurant operators are skeptical of SaaS platforms promising instant magic. Rewritten to: connect Toast + QBO → ingest historical orders → generate first supplier fingerprint → catch one tangible mistake in 30 days. One catch pays for the year. More credible.

**Hero one-liner added: "BlueCart stores the order. We store the leverage."**

Rated 10/10. Now prominently placed in the positioning section. Use in all demo scripts, slide decks, and pitch conversations.

**Revenue framing: "$45-75K/year" → "3 points off food cost"**

"Points" is the native language of restaurant operators. "3 points off food cost" translates immediately for every buyer regardless of their revenue. For Marco ($3.2M): 3 points ≈ $29K. For Rafael ($28M hotel F&B): 3 points ≈ $280K. The dollar amount requires math; the points frame is instant.

**Terminology fix applied:**

| Old | New |
|---|---|
| "Price Position" | "Lowest Quoted Price" |
| "Delivery Reliability" | "Showing Up On Time" |
| "centroid geometry" | "everything the system learned from your orders" |
| "DK weight 94%" | "your most reliable signal" |
| "N=23 rainy Saturdays" | "23 rainy Saturdays" |
| "σ=0.07" | "very reliable" or "consistent" |

**Trust trap I1 vocabulary — needs kitchen language, not procurement language.** The concept is excellent (rated: fantastic). The execution in evidence text must not say "σ=0.29, DK weight 8%." Must say: "Their lowest quoted price — the thing you check first — is your least reliable signal."

### Key Insights for Demo Script

1. **Marco's 30-day ask:** He doesn't need a paradigm shift. He needs the system to catch ONE tangible mistake that pays for the whole year. Lead with the first catch, not the platform capabilities.

2. **The radar chart closes the sale for Marco.** Seeing inverted expectations vs actual factor weights — "you've been trusting the wrong signal for 7 years" — produces immediate ROI clarity at $299-499/month (less than one botched weekend delivery).

3. **Lisa's chain learning is the enterprise upsell.** The siloed knowledge problem for multi-location operators is the holy grail. "Chicago's produce supplier warning → Miami gets it Day 1" = easy yes at $200-300/location.

4. **Day of week is mechanism, not hook.** Don't lead with it. Lead with weather ($480 waste from rain weekend), events ($1,200 lost from marathon), or departure ($28K in 6 months). Day-of-week emerges as "also, here's what else it learned."

5. **Jargon rule is absolute.** Any customer-facing text (demo script, UI labels, email, pitch deck) must pass the "chef test" — would a chef understand this without a glossary? If no, rewrite. The jargon-to-kitchen mapping in PD v1.2 §11.1 is the authoritative guide.

### Changes Applied to PD v1.2

All five changes have been made to `purchasing_copilot_pd_v1_2.md` (now 882 lines):
1. Hero one-liner "BlueCart stores the order. We store the leverage." in §5
2. P6 rewritten around dynamic par + waste reduction
3. P9 rewritten with credible 30-day story (no "20 min" claim)
4. Revenue framing updated to "3 points off food cost" in §6
5. Jargon-to-kitchen mapping table added to §11.1 NL Evidence Templates


---

## Part 78 — Purchasing Copilot PD v1.3: Roadmap Session Changes (May 29, 2026)

### Source: purchasing_copilot_pd_v1_3.md · Supersedes v1.2

### What Changed v1.2 → v1.3

**1. Revenue framing softened (credibility fix)**
- v1.2: "$45-75K/year" or "3 points off food cost"
- v1.3: "$15-45K (1-3 points of recoverable leakage)" — tighter, more defensible
- CFO pitch: "1-3 points" (range) not "3 points" (false precision)

**2. Marco's $28K departure cost now itemized**
- v1.2: Single "$28K in the first 6 months"
- v1.3: $8K price creep nobody challenged + $7K over-ordering + $5K missed credits + $4K poor substitutions + $4K stockout losses = $28K
- Impact: Far more believable. Each line item resonates with a different operator.

**3. Factor display names now official (§7.1)**

| Factor (code) | Display Name (UI/narrative) |
|---|---|
| expected_demand | Expected Demand |
| day_of_week | Day of Week |
| weather_forecast | Weather Forecast |
| event_flag | Local Events |
| historical_waste | Waste History |
| supplier_lead_time | **Whether They Show Up** |
| price_memory_index | **What They Charge** |

Factor code→display name mapping from v1.1 also documented (6 v1.1 factor names consolidated into the current 7). Engineering implication: P7 PUR-FACTORS, P10 PUR-ORDER-QUEUE, P15 PUR-TRUST-ANALYSIS must all use Display Names in NL output and UI labels.

**4. New §8.1 Day 1 Experience — time-to-value narrative**
Progressive story that addresses the "vaporware" criticism (Gemini Q9):
- **Hour 1**: Connect Toast POS, import 500 orders → first supplier fingerprint visible (pricing volatility, delivery reliability, trust trap indicator)
- **Week 1**: Radar chart sharpens for top 5 suppliers. Price memory surfaces first unchallenged increase.
- **Month 1**: Weather factor activates. Day-of-week profile learned. Food cost drops 1.2 points without menu changes.
- **24 weeks**: Full compounding trajectory.

The "trust trap visible before lunch" claim is retained but properly scoped to the fingerprint view from 500 historical orders — not from live data ingestion.

**5. New §8.2 Weekly Recovered-Dollar Report — NEW PRODUCT REQUIREMENT**
This is the retention mechanism. Without it, Marco cancels. The system must produce a Monday digest showing:
- "We found $412 this week."
- "We prevented $180 in waste."
- "We flagged $230 in price variance."
- "Net recovered this month: $1,820."

Pulls from verified decisions + conservation log + price memory alerts. No AI narration — facts and dollars only. **New MAP item #110 PUR-WEEKLY-REPORT (3d).**

**6. New §8.3 Chain Learning as Top Sales Angle**
All three LLM evaluators (Grok: "strongest angle in the entire deck", Gemini: "holy grail", GPT: "one location's scar tissue becomes every location's warning system") confirmed chain learning is the top multi-location hook. Lisa's pitch should lead with chain learning, not with general features. I8 remains v2.0 in the build sequence but is now the primary value proposition for Lisa's demo.

**7. Scenario count: 22 → 23** (M8 commodity decomposition now an explicit scenario)

**8. Jargon fixes applied in scenarios**
- "N=23 rainy Saturdays" → "from your last 2 years of rainy Saturdays"
- Event scenario: "from past events" replaces specific N= counts
- Consistent with jargon scrub rule in §11.1

**9. Hero one-liner validated across 3 LLMs**
"BlueCart stores the order. We store the leverage." — rated 9-10/10 by Grok, Gemini, GPT. Now explicitly labeled as such in §5.

### Artifact: §5 Has Duplicate Positioning Paragraph
The positioning section has "BlueCart, MarketMan, and Upserve manage purchasing PROCESS..." appearing twice — once in the new version and once from v1.2. Author should clean this before finalizing v1.3 for distribution.

### Updated Purchasing Scenario Coverage (v1.3)

| Phase | Scenarios | Count |
|---|---|---|
| v0.1 (now) | P1, P3, I1 partial | 3/23 |
| v1.0 (8-12wk) | +M1/M2, P2/P4-P7, I2/I3 | 13/23 |
| v1.1 (14-18wk) | +P8/P9/M8/I4/I5/F1/F2/F3 | 21/23 |
| v2.0 (20-28wk) | +P10/I7/I8 | 23/23 |

### New MAP Item from v1.3

| MAP# | ID | Effort | What |
|---|---|---|---|
| **#110** | PUR-WEEKLY-REPORT | 3d | Weekly recovered-dollar digest (Monday email/in-app). Pulls from verified decisions + conservation log + price memory alerts. Shows dollars found, waste prevented, supplier flags. The retention mechanism — without it, operators cancel. |

### Engineering Notes for Codex Session

**Factor display names are now spec (not optional):**
All three UI-facing Codex prompts must use Display Names, not code names:
- P7 PUR-FACTORS: `compute()` output labels use "Whether They Show Up", "What They Charge"
- P10 PUR-ORDER-QUEUE: Evidence panel uses Display Names throughout
- P15 PUR-TRUST-ANALYSIS: Radar chart axes and legend use Display Names

**§8.1 time-to-value narrative is product spec:**
The "1 hour → 1 week → 1 month" progression is now the official onboarding story. The evidence panel and fingerprint view must be functional from the first 500-order import.

**Chain learning demo (§8.3) shapes Lisa's demo script:**
Lead with "your best location's purchasing discipline becomes the baseline for all four." Don't lead with technical architecture. The cross-location benchmarking dashboard (same item, different price; same supplier, different OTIF by location) should be prioritized in the UI design.



---

## Part 79 — P36-P85 Forward Queue: Full Classification (June 7, 2026)

**Session type:** Code analysis against MAP v5.150 + design docs
**Method:** Ground truth PowerShell scans (3 signals per prompt) + semantic LLM comparison of PD spec vs implementation. No pytest in classification — tests prove nothing about spec coverage.
**Design docs location:** `$env:CLAUDE_SDK\docs\design\` (all 7 files)

### Methodology corrections established this session

1. **Scans deliver content only — no verdicts.** PowerShell pattern matching cannot verify semantic correctness. A grep finding `emotional_indicator` in registry.py says nothing about whether it maps to the correct factor computer class.

2. **PD is the spec, MAP is the action plan.** MAP v5.150 one-liners ("NL templates × 5 categories") are insufficient for verification. Every DROP/SUPPLEMENT decision requires reading the actual PD section and comparing to implementation at the level of meaning.

3. **T1 transcript data can be stale.** The P48 Codex audit confirmed that registry.py wrong mappings (emotional_indicator→ResearchDepthFactor, risk_reward_actual→TimeHorizonFactor) previously recorded as T1 findings had been fixed in a prior Codex session. Any finding from a prior session transcript must be re-verified against current files before acting on it.

4. **Passing tests ≠ spec coverage.** Test suites written alongside incomplete implementations pass against those incomplete implementations. The classification gate is PD requirements PRESENT in implementation, not test pass rate.

5. **Code analysis session scope.** This session classifies prompts and produces findings. It does not write implementation prompts — that is the coding session's job.

### Confirmed DROPs (4 total)

| Prompt | Evidence |
|---|---|
| P41 S2P-CENTROID-EXPLORER | s2p_explorer.py registered in main.py; /drift/{category} reads live scorer; getDKWeights confirmed live |
| P48 TRD-DOMAIN-CONFIG | Codex audit all A-J present; 173 tests passed; registry mappings corrected in prior session |
| P65 PUR-TENSOR-MIGRATE | (5,4,7) confirmed; price_memory_index at index 6; migration code correct; 92 tests passed |
| P81 TRD-REGIME-CLASSIFIER | Codex audit all A-J present; exact PD §10.4 thresholds confirmed; live yfinance + ADX |

**MAP correction required:** Trading tensor table in MAP §1 and §11 shows current=(5,3,6), target=(5,4,7). Correct values: current=(5,4,10), target=(5,4,10). Options factors 7-9 are intentional MAP #176 extension.

### P41 — reclassified from DROP to SUPPLEMENT

P41 was assumed DROP based on frontend calls confirmed live. PD F7 read-through revealed two absent requirements:
- **B ABSENT:** Invoice-specific centroid overlay (where THIS invoice sits vs learned centroid). `/contribution` endpoint exists but frontend never calls it. No invoice selection in CentroidExplorerPanel.tsx.
- **C ABSENT:** Historical centroid drift (30/90/180 days). `/drift/{category}` returns current centroid only — no time series, no checkpoint retrieval.

Items PRESENT: DK weights endpoint (live), current centroid display per action (live).

### Complete Classification Table — All 50 Prompts

| Prompt | Classification | Primary gap / evidence basis |
|---|---|---|
| P36 | SUPPLEMENT | Lead-time helper exists; F14 conditional distributions absent |
| P37 | FULL | Nothing found |
| P38 | SUPPLEMENT | AGE factory exists; traversal queries absent |
| P39 | FULL | No AGE write path |
| P40 | SUPPLEMENT | Threshold lowering never applied; no ledger write on auto-approve |
| P41 | SUPPLEMENT | Invoice overlay absent; historical drift absent |
| P42 | FULL | copilot_sdk/di/ absent |
| P43 | SUPPLEMENT | 9 stubs, 14 mocks |
| P44 | FULL | No enrichment write calls in DataOps |
| P45 | FULL | Nothing found |
| P46 | FULL | Nothing found |
| P47 | SUPPLEMENT | ThreatIntel + DeviceTrust + S2P L228 polarity inverted |
| P48 | **DROP** | Codex audit confirmed all PD §10.1 requirements |
| P49 | SUPPLEMENT | Paper/live account distinction absent |
| P50 | SUPPLEMENT | 1 stub, 1 mock |
| P51 | UNSURE | T1 registry mapping errors stale — re-verify against current registry.py |
| P52 | SUPPLEMENT | connect absent; import Alpaca unsupported; score/trust/conservation offline proxies |
| P53 | SUPPLEMENT | Frontend TrustRadarPanel exists; backend /trust endpoint absent |
| P54 | UNSURE | T1 registry mapping errors stale — re-verify against current registry.py |
| P55 | SUPPLEMENT | 2 stubs; no /patterns router |
| P56 | SUPPLEMENT | Simplified proxy only; per-strategy conservation absent |
| P57 | SUPPLEMENT | 1 stub |
| P58 | FULL | Zero IKS symbols in Trading backend |
| P59 | SUPPLEMENT | 3 stubs |
| P60 | SUPPLEMENT | 4 stubs |
| P61 | SUPPLEMENT | patterns absent; dashboard absent; backup/restore partial (no centroids+weights) |
| P62 | SUPPLEMENT | pyproject.toml ready; pip: "No matching distribution found" |
| P63 | SUPPLEMENT | 5 templates present but missing named fields: regime_acc, rsi_value, event_acc, hold_min, premium/dte/delta |
| P64 | SUPPLEMENT | Wrong archetypes; no behavioral patterns |
| P65 | **DROP** | Codex audit confirmed all PD §7.1 requirements |
| P66 | FULL | Nothing found |
| P67 | SUPPLEMENT | 7 factors named in context_router; no factor computers |
| P68 | FULL | Nothing found |
| P69 | FULL | Nothing found |
| P70 | FULL | Nothing found |
| P71 | FULL | Nothing found |
| P72 | SUPPLEMENT | /conservation-proof exists; no implementation |
| P73 | FULL | Nothing found |
| P74 | FULL | Nothing found |
| P75 | FULL | Nothing found |
| P76 | UNSURE | copilot_sdk.backend.* and copilot_sdk.framework.* suppress ignore_errors; ci_platform.onboarding.* same |
| P77 | UNSURE | SOC α canonicalization (α ~0.08→~1.0, 12× θ_min drop) — scope requires SOC conservation code read |
| P78 | FULL | demo.py:390 explicitly says "not available yet" |
| P79 | UNSURE | L5-Plus-Proof #133 — no code symbols; MAP says Day 25 item |
| P80 | SUPPLEMENT | README 0.9KB only |
| P81 | **DROP** | Codex audit confirmed all PD §10.4 requirements; exact thresholds match |
| P82 | SUPPLEMENT | entry_at_day_extreme hardcoded False; tagged_signals absent from request schema |
| P83 | SUPPLEMENT | Sigma not computed in promotion metrics (paper→small→full otherwise correct) |
| P84 | SUPPLEMENT | Regime boundary variant family absent (only EXECUTION_THRESHOLD + REVENGE_COOLDOWN) |
| P85 | SUPPLEMENT | Impl clean; /regime-recommend endpoint absent |

**Summary:** 4 DROPs · 16 FULLs · 26 SUPPLEMENTs · 4 UNSUREs

### Key semantic findings from PD comparisons

**P40 S2P-AUTO-APPROVE:** `build_expansion_proof()` computes proposed lower threshold but never applies it. `_stats` is in-memory demo telemetry (`"source": "in_memory_demo_stats"`) — no graph store write on any auto-approve decision. PD F5 requires ledger write per decision and conservation-gated threshold lowering.

**P52 CLI:** `connect` command absent from parser entirely. `import` supports csv/ibkr only — `--broker alpaca` fails. `score`, `trust`, `conservation` are all offline proxies that print "Full conservation requires the scoring server." PD F8 expects live API-connected behaviour.

**P61 CLI:** `backup` backs up config+trades JSON only. PD requires "backup centroids + weights." `patterns` and `dashboard` commands absent from parser.

**P63 TRD-EVIDENCE-NL:** `TradingTemplateEngine` exists with all 5 renderers and live factor values. Missing named fields per PD §10.6: `{regime_acc}` in TREND_FOLLOWING, `{rsi_value}` in MEAN_REVERSION, `{event_acc}` in EVENT_DRIVEN, `{hold_min}` in SCALP, `{premium}/{dte}/{delta}` in INCOME.

**P82 TRD-REALTIME-SCORE:** `entry_at_day_extreme` hardcoded `False` in `_context_for()` — PD requires computation from day high/low. `tagged_signals` not in `PreScoreRequest` schema — signal_alignment factor defaults to 0.5.

**P83 TRD-PROMOTION-ENGINE:** Three stages (paper/small_live/full_live) present, conservation gating correct, persistence to JSON file correct. Only gap: sigma not in `_metrics()`. PD example shows "accuracy 62%, σ=0.12" at promotion decision.

**P84 TRD-AGENT-EVOLVER-FULL:** EXECUTION_THRESHOLD and REVENGE_COOLDOWN variant families present. PD F12 requires regime boundary auto-calibration as third dimension. Absent from evolver_config.py and dimensions.py.

### P51 + P54 — require re-verification before any action

Prior T1 finding: registry.py had three wrong mappings. P48 Codex audit showed those mappings are now correct in current files. P51 and P54 were classified SUPPLEMENT solely on that T1 finding. Classification is now UNSURE until a current-state audit of registry.py confirms or denies the prior finding.

### Standing rules added this session

**Rule for code analysis sessions:** Scans deliver content. LLM makes semantic comparisons. Never use pattern match results as DROP/SUPPLEMENT evidence.

**Rule for Codex prompts (when the coding session writes them):** Every file inside a Codex prompt is an instruction for Codex to execute. Human-facing notes (e.g. "run in separate windows") must not appear inside prompt files.

**Rule for prerequisite handling in Codex prompts:** Every prompt that imports from copilot_sdk needs a PRE-CHECK that verifies the dependency exists. If missing, the FIX section specifies exactly what to create and what not to create. "Stop if missing" is wrong — Codex will improvise. "Here is exactly what to create" is correct.



---

## Part 80 — P69/P70 Purchasing Match + Queue: Implementation State (June 7, 2026)

### P69 PUR-MATCH-ENGINE — COMPLETE with known durability gap

Three-way match router at `apps/purchasing/backend/app/routers/match.py` (207 lines).

**Exception queue — router memory:**
```python
PENDING_EXCEPTIONS: list[dict[str, Any]] = []  # module-level list
```
`_upsert_exception()` deduplicates by order_id using slice assignment — idempotent
within a server session. A server restart loses all pending exceptions.
PD F2 describes an analyst workflow that requires persistence across sessions.
This is a known limitation labelled in the response as `"source": "router_memory"`.

**Register as follow-up: P69-PERSIST** — migrate exception queue from router memory
to graph store. 0.5d. Dependency: P71 (verify endpoint for DecisionEntry writes).

**Price tolerance formula — flag for review:**
```python
price_tolerance = 0.10 + ((1.0 - price_memory_index) * 0.15)
```
Low price_memory_index (anomalous price history) → wider tolerance (up to 0.25).
High price_memory_index (price within learned norms) → tighter tolerance (0.115).

Interpretation: when price_memory_index is low, we have little historical data
to confidently flag exceptions, so we tolerate more variance. This may be
intentional. However it could also be read as "anomalous prices get more lenient
matching," which is the opposite of what a fraud-prevention system would want.

The PD F2 does not specify the tolerance formula. Flag for product review before
any price-variance exception accuracy measurement is done.

**Graph write path:**
`_write_match_decision()` correctly calls `graph_store_factory().write_decision()`
with domain="purchasing", action="order_as_planned" or "skip", and full metadata.
Reports `decision_write.status` as "written" / "not_configured" / "failed" — never
claims success without confirming the store write. DecisionEntry auditing is live.

### P70 PUR-ORDER-QUEUE — COMPLETE

Order queue router at `apps/purchasing/backend/app/routers/queue.py` (102 lines).

**Priority formula confirmed:**
```python
priority_score = historical_waste * expected_demand * (1.0 - supplier_lead_time)
```
Matches PD F3: "prioritized by waste risk × demand signal × supplier risk."
`supplier_lead_time` is inverted (higher lead time = higher supplier risk = lower priority).

**Data source:** `load_purchasing_orders()` from fixture context. Response labels
this as `"source": "purchasing_fixture_context"`. Will automatically use live data
when P66 (QBO) and P45 (Toast POS) connectors ship and populate the orders store.

**Conservation status:** computed from graph store with fallback chain:
BOOTSTRAP (no verified decisions) → AMBER (accuracy < 50%) → GREEN (accuracy ≥ 50%).
Included in queue response for downstream auto-approve gating.

---

## Part 81 — P74/P75 Purchasing IKS + Trust: Implementation State (June 7, 2026)

### IKSService — architectural design (SDK-level, affects all copilots)

Created at `copilot_sdk/scoring/iks_service.py` (75 lines), exported from
`copilot_sdk/__init__.py` at L16. Confirmed thin wrapper — does not reimplement
IKS maths.

**Constructor signature:**
```python
IKSService(graph_store, *, domain: str, shape: Any, categories: Iterable[str])
```
Requires explicit shape and categories — not self-configuring. Callers must
pass the domain preset's shape and category list. This is correct: IKSService
is domain-agnostic; the caller provides domain context.

**Delegation chain:**
```
IKSService.summary()
  → _verified_decisions() reads graph_store.get_verified_decisions(domain)
  → compute_trajectory([], decisions, shape) from copilot_sdk.scoring.trajectory
  → returns {iks, per_category, trajectory, verified_count, available, source}
```

**Dependency:** `graph_store.get_verified_decisions(domain)` must exist.
If absent, `_verified_decisions()` returns `[]` gracefully — IKS = 0.0, available = False.

**Per-category breakdown:** calls `compute_trajectory` once per category with
scoped decisions. For a 5-category domain with 100 verified decisions, this
is 6 compute_trajectory calls (1 overall + 5 per category). Acceptable.

**Import path (confirmed):** `from copilot_sdk import IKSService`
P58 TRD-IKS-WIRE must use this path. Do not create a new IKSService.

### P74 PUR-IKS-SCORECARD — COMPLETE

IKS + supplier scorecard router at `apps/purchasing/backend/app/routers/iks.py` (182 lines).

**IKS endpoint:** `GET /api/purchasing/iks` calls `IKSService.summary()` correctly.
Passes `PurchasingPreset().shape` and `CATEGORIES` to constructor. ✓

**Supplier scorecard:** `GET /api/purchasing/suppliers/{supplier_id}/scorecard`
uses graph-first, fixture-fallback pattern:
1. Try `graph_store.get_verified_decisions(domain)` filtered by supplier_id
2. If rows found → compute OTIF + exception rate from actual outcomes
3. If absent → fall back to `get_supplier_by_id()` fixture data

Fallback response labelled `"source": "fixture_context"` — not `"source": "graphstore"`.
Will improve automatically as P71 (verify) writes OutcomeEntry records with supplier_id.

**Unknown supplier:** returns 404. ✓

### P75 PUR-TRUST-ANALYSIS — COMPLETE

Trust analysis router at `apps/purchasing/backend/app/routers/trust.py` (99 lines).

**Display names enforced — code names never in response:**
```python
DISPLAY_NAMES = {
    "expected_demand":    "Expected Demand",
    "day_of_week":        "Day of Week",
    "weather_forecast":   "Weather Forecast",
    "event_flag":         "Local Events",
    "historical_waste":   "Waste History",
    "supplier_lead_time": "Whether They Show Up",
    "price_memory_index": "What They Charge",
}
```
Response is a list of dicts with key `display_name` — factor code names never exposed. ✓

**Trust trap rule:** `actual_weight < EXPECTED_WEIGHT * 0.5` (actual < half of uniform prior). ✓

**Hero narrative:** `"The factor you trust most is the one that lies to you."` ✓

**DK unavailable path:** when `get_dk_weights()` returns empty, `actual_weight` and
`trust_trap` are omitted from each factor row. Response has `"available": False`.
No fake weights injected. ✓

**DK weight normalization:** averages weights across all category rows, then
normalizes to sum=1.0 before returning. This produces comparable weights
regardless of how many centroid cells exist.

---

## Part 82 — P51/P54 Registry Mappings: RESOLVED (June 7, 2026)

### Prior finding was stale

Prior session (T1) recorded three wrong mappings in registry.py:
- `emotional_indicator → ResearchDepthFactor` (wrong)
- `risk_reward_actual → TimeHorizonFactor` (wrong)
- `MarketRegimeFactor.factor_name = "emotional_indicator"` (wrong)

Current state of `apps/trading/backend/app/factors/registry.py` (85 lines):
```python
_PRESET_FACTOR_COMPUTERS = {
    "signal_alignment":       SignalAlignmentFactor(),
    "market_regime":          MarketRegimeFactor(),
    "position_sizing":        PositionSizeFactor(),
    "timing_quality":         TimingQualityFactor(),
    "risk_reward_actual":     RiskRewardActualFactor(),   # ← now correct
    "emotional_indicator":    EmotionalIndicatorFactor(), # ← now correct
    "signal_confidence":      SignalConfidenceFactor(),
    "options_delta_exposure": OptionsDeltaExposureFactor(),
    "options_iv_percentile":  OptionsIVPercentileFactor(),
    "options_gamma_risk":     OptionsGammaRiskFactor(),
}
```

All 10 factor names map to semantically correct classes. A prior Codex session
corrected the mappings. The T1 reading was from a snapshot that preceded that fix.

**P51 TRD-SIGNAL-FACTORS: reclassified UNSURE → DROP CANDIDATE.**
**P54 TRD-REMAINING-FACTORS: reclassified UNSURE → DROP CANDIDATE.**

Both require a Codex audit against the PD §10.1 factor computer specs to confirm
DROP — the registry mappings are correct but the `compute()` method semantics
still need verification. Use the P48 audit prompt as the template.

### Registry design note

The registry maintains two identical dicts (`_PRESET_FACTOR_COMPUTERS` and
`_FALLBACK_FACTOR_COMPUTERS`) that diverge only in how `ALL_FACTOR_NAMES` is
sourced — from `TradingPreset().shape.factor_names` when the import succeeds,
or from a hardcoded fallback tuple when it fails. Both dicts have identical
class assignments. `TRADING_FACTOR_COMPUTERS` selects between them at module load.

This means a TradingPreset import failure degrades gracefully — factor computers
still work, names still match, only the canonical source of truth is bypassed.

---

## Part 83 — P42/P44 DataOps DI: Implementation State (June 7, 2026)

### P42 DI-3-NL-QUERY — COMPLETE

SDK package at `copilot_sdk/di/` (2 files). HTTP endpoint at
`apps/dataops/backend/app/routers/query.py` (31 lines).

**Intent taxonomy (canonical — 5 intents + fallback):**
| Intent | Trigger keywords |
|---|---|
| source_reliability | confidence, trust, reliable, reliability |
| freshness | fresh, freshness, stale, late |
| recurrence | recurring, recurrence, repeat, again |
| impact | impact, blast, downstream, affected |
| metric | metric, revenue, answer, how much, what was |
| unknown | anything else |

Pattern-based classification — no LLM calls. ✓
Evidence: last 5 verified decisions from `get_verified_decisions("dataops")`.

**Query templates are Cypher (informational only):**
Each intent returns a Cypher template string in the response. These are
documentation artifacts — the actual query execution uses `get_verified_decisions()`
which is SQLite-compatible. The Cypher templates are not executed by NLQueryRouter.

**Graceful handling:**
- Empty question → 400 error at HTTP layer
- Empty string after strip → returns "Ask a DataOps question" with intent=unknown
- Graph store without `get_verified_decisions` → tries `get_all_decisions` → falls back to []
- Unknown intent → returns "could not map" message, no crash

### P44 DI-6-GRAPH-ENRICHMENT — COMPLETE with naming question unresolved

Enrichment service at `apps/dataops/backend/app/services/graph_enrichment.py` (122 lines).

**Idempotent write design:**
```python
enrichment_id = sha256({source_ids: sorted_list, enrichment_type: str})[:16]
```
Same source_ids + enrichment_type always produces the same enrichment_id.
Update path: find existing node → update payload + timestamp.
Create path: create new EnrichmentNode.

**Three write paths (in priority order):**
1. `graph_store.write_enrichment(record)` — preferred, uses store abstraction
2. `graph_store.upsert_enrichment_node(**record)` — upsert method if available
3. `graph_store.run_query(cypher, params)` — AGE direct; handles async via asyncio.run

Handles async graph queries correctly: detects awaitable result, uses asyncio.run
when no event loop is running, raises RuntimeError when event loop IS running
(caller must await). This is the correct pattern for the AGE client.

**Source linking:** calls `graph_store.link_enrichment_source(enrichment_id, source_id)`
for each source — creates edges between EnrichmentNode and source nodes in graph.

**P44 naming mismatch — RESOLVED:**

DataOps PD §39 defines DI-6 DATA-VALUATION as:
> "Economic value estimation per discovered combination.
> improvement_pp × decisions/year × avg_decision_value.
> Dollar amounts on Intelligence Map gold lines.
> Effort: 2w. Dependency: DI-5 (COMBINATION-DISCOVERY)."

`DataOpsGraphEnricher` writes quality annotation nodes to the graph.
DATA-VALUATION computes dollar amounts per data combination found by DI-5.
These are **different features**. The P44 implementation built graph enrichment
infrastructure — not DATA-VALUATION.

**Classification correction: P44 is NOT COMPLETE for DI-6.**

What was built: `DataOpsGraphEnricher` (graph annotation infrastructure).
What DI-6 requires: economic value estimation formula, dependency on DI-5 results.
DI-5 (COMBINATION-DISCOVERY) is also not yet built.

**Correct state:**
- `DataOpsGraphEnricher` is correctly implemented and useful infrastructure.
  It will eventually store DATA-VALUATION results as enrichment records.
  But the computation itself is absent.
- DI-6 DATA-VALUATION: FULL (nothing built for the feature itself).
  Dependency: DI-5 must ship first.
- Rename `DataOpsGraphEnricher` as "graph enrichment infrastructure" in MAP.
  Register DI-6 as a separate pending item.

**P44 reclassification: COMPLETE → INFRASTRUCTURE PARTIAL**
The graph enrichment infrastructure is solid and should be kept.
The DI-6 DATA-VALUATION feature is unbuilt and cannot be built until DI-5 ships.

### P42/P44 pipeline wiring — incomplete

`DataOpsGraphEnricher` was created but never called from the DataOps processing
pipeline. No automatic enrichment writes on DataOps insights. This is documented
in the P42/P44 Codex report as "pending because the DataOps insight pipeline
integration point was not clear within allowed scope."

The coding session must identify where DataOps produces significant findings
and insert a `DataOpsGraphEnricher().write_enrichment(...)` call at that point.
Until this is done, the enricher exists but produces no data.



---

## Part 84 — MAP v5.154 State Delta (June 12, 2026)

**Authority:** MAP v5.154 supersedes v5.150. All numbers in this Part are canonical.

### Test counts (v5.154)

| Repo | Tests | Tag |
|---|---|---|
| GAE | 1,237 | v0.7.25 |
| ci-platform | 350 | v0.7.4-ci |
| SDK root | 915 | v0.7.0 |
| Trading BE | 727 | v0.7.0 |
| Purchasing BE | 168 | v0.7.0 |
| DataOps BE | 176 | v0.7.0 |
| S2P BE | 926 | v0.7.2-s2p |
| SOC BE | ~1,742 | v5.87 |
| **Total** | **~6,241** | 0 failures |

### New DONE items (v5.150 → v5.154)

| Item | Evidence | Impact |
|---|---|---|
| P28 S2P-F10-FINANCIAL-P1 | v0.7.2-s2p, 13 tests | S2P financial impact analysis |
| P29 SQLITE-TO-AGE-MIGRATION | v0.7.4, 71 tests, Trading 150 migrated, shadow 40/40 | Migration tooling for all 4 SQLite copilots |
| P30 DI-1-SOURCE-PROFILER-P1 | v0.7.5, 16 tests | DataOps source profiling phase 1 |
| C9B-PRE-HOTPATH | F8 pass: 250/250, all L5 types, avg analyze 1.77s | Pre-hotpath baseline proven |
| Pkg 1: Pooled AGE adapter | ci-platform Track A — psycopg_pool opt-in built into age_client.py | 82ms connection tax eliminated when psycopg_pool installed |
| CAMPAIGN-P1 | Stable identity tuple, 6 campaigns, 25 MEMBER_OF, O(N²)→O(N) | 14× analyze speedup (25.6s → 1.77s) |
| STEP-0-SPIKE | cache_model_viable. Pooled read 1.1ms. Fresh read 83.2ms. Tax 82ms (98.7%) | Architecture decision for hot-path validated |
| LOCALHOST-SWEEP | All 5 repos: DSN→localhost, HTTP→127.0.0.1 | Rule 40 compliance across platform |
| GP-MYPY-FIX (#113) | Fixed in BUGFIX-PRELUDE | — |
| PUR-AE-VARIANTS (#112) | evolver_config.py complete | Purchasing AgentEvolver wired |
| CONSERVATION-DISPLAY-FIX (#80) | ConservationProjection.tsx built + wired | SOC frontend |
| DEMO-PY-FIX | connect_timeout=5, localhost/127.0.0.1 split, AGE_DSN_DATAOPS fixed | demo.py reliability |
| NO-GRAPH-FIXTURE | DataOps conftest.py + 7 tests patched for GRAPH_BACKEND=age isolation | Test isolation |
| OUTBOX-DESIGN-SPIKE | Downgraded — P14 embeds full schema | — |

### DROPs confirmed (P36-P85 queue)

| Prompt | Reason |
|---|---|
| P48 TRD-DOMAIN-CONFIG | Trading already (5,4,10)=200 live |
| P51 TRD-SIGNAL-FACTORS | All 10 factors already exist |
| P54 TRD-REMAINING-FACTORS | Covered by P51 (all factors built) |

These three were in the session_continuation_jun7 as confirmed DROPs. MAP v5.154 makes them official.

### New MAP item

**#209 CI-MYPY-COPILOT-CORE** — 2h effort, P3 priority.
Pre-existing mypy failures in:
- `ci_platform/copilot_core/counters.py`: 4 `no-any-return` errors in `AGECounterStore.increment_cumulative()` and `AGECounterStore.increment_distinct()`. Both methods call `self._graph.run_transaction(operation)` which returns `Any`, then return `cast(CounterRead, await result)`. Mypy flags this as "Returning Any from function declared to return CounterRead" because `cast()` does not narrow `Any`.
- `ci_platform/copilot_core/background.py`: 2 type annotation errors in `BackgroundTaskManager`. Likely `cast(Coroutine[Any,Any,Any], awaitable)` from `Awaitable[Any]` in `submit()`.

Not blocking tests or runtime. Fix before next ci-platform pip release.

### New standing rules (v5.151-v5.154)

| Rule | Text |
|---|---|
| **40 (updated)** | Mirrored WSL2 split: Database DSNs (AGE/PostgreSQL) MUST use `localhost`. HTTP calls to local uvicorn MUST use `127.0.0.1`. localhost HTTP adds 2s IPv6 penalty; 127.0.0.1 DSN can't reach WSL2. |
| **58** | No raw sqlite3 in feature code. All persistence through GraphStore protocol only. No `import sqlite3` or `sqlite3.connect()` in production code. Violation = P1 fix before tag. Tests/migration scripts exempt. |
| **59** | AGE smoke gate at tier boundaries. Each copilot's full test suite must pass with `GRAPH_BACKEND=age` at the tier boundary noted in MAP §4. Non-blocking for features, blocking for "AGE-ready" status. |
| **60** | AGE read-side normalization. All direct-psycopg AGE reads MUST use `normalize_agtype_value()`. Write: `serialize_for_age()`. One canonical function per direction. |
| **61** | Shadow scorer store isolation. ShadowScorer.from_preset() MUST reject `primary_store is shadow_store`. Shared stores corrupt shadow discipline. |
| **62** | Migration source of truth. Home DB (`~/.ci-platform/<domain>/<domain>.db`) is default migration source. Repo DBs are development artifacts. CLI accepts `--source` for override. |

### AGE adoption sequence (§16A)

| Copilot | Graph backend today | AGE migration point | Order |
|---|---|---|---|
| **SOC** | **AGE ✅** | Done — C9A + F8 proof | **1st (done)** |
| DataOps | SQLite | After Tier 2 (post-P47) | 2nd |
| S2P | SQLite | After Tier 1 (post-P41) | 3rd |
| Trading | SQLite | After Tier 3 + tensor (post-P53) | 4th |
| Purchasing | SQLite | After Tier 5 + tensor (post-P75) | 5th |

AGE smoke gates at tier boundaries (Rule 59, non-blocking for features):
- After P41: S2P full test suite with `GRAPH_BACKEND=age`
- After P47: DataOps full test suite
- After P53: Trading full test suite
- After P75: Purchasing full test suite

### Performance baselines (measured June 9, 2026)

| Metric | Value | Source |
|---|---|---|
| SOC analyze (250 decisions, post-Campaign-P1) | **1,767ms avg** | C9B pre-hotpath baseline |
| SOC analyze (250 decisions, pre-Campaign-P1) | 25,602ms avg | F8 proof (before Campaign-P1 fix) |
| Speedup from Campaign-P1 | **14×** | O(N²) → O(N) campaign identity |
| Pooled AGE point read | **1.1ms** | Step-0-spike |
| Fresh AGE point read (no pool) | 83.2ms | Step-0-spike |
| Connection tax (fresh − pooled) | **82.1ms (98.7%)** | Step-0-spike |
| ProfileScorer.score() | 0.25ms | Phase-C trace |
| Committed Phase-3 write | 8.8ms avg | Phase-3 diagnostic |
| Hot-path target (cache architecture) | ~47ms projected | Derived from spike |

### MAP §11 tensor table inconsistency (carry-forward)

MAP §11 still shows Trading current=(5,3,6) / target=(5,4,7). MAP §1 shows Trading (5,4,10)=200 LIVE. These contradict each other. §1 is authoritative — Trading is (5,4,10) live. §11 has not been updated. Flag for MAP author to correct §11 in next version.

---

## Part 85 — Campaign P1 Fix: Architecture and Performance Impact (June 12, 2026)

**Source:** `gen-ai-roi-demo-v4-v50/backend/app/domains/soc/campaigns.py` (1,256 lines, scanned June 12)

### The O(N²) problem (pre-Campaign-P1)

Before Campaign-P1, `CampaignMatcher.check_alert()` would attempt to match each new alert against all prior campaign candidates using floating-point timestamps and string-concatenated identity keys without delimiters. Two specific bugs caused combinatorial explosion:

1. **Hash collision from undelimited concatenation**: `"user" + "X" + "category"` and `"use" + "rXcategory"` produced identical hash inputs, creating phantom campaign merges that caused O(N²) queries.
2. **Float bucket drift**: `campaign_time_bucket()` returned a float, causing the same event to hash to different buckets across runs due to floating-point rounding, defeating identity-based deduplication.

At 250 decisions these produced avg analyze time of 25,602ms.

### The Campaign-P1 fix

Three changes, all in `campaigns.py`:

**Fix 1 — Null-byte delimiter in `make_campaign_identity_key()`:**
```python
material = (
    "L1:"
    + str(rule_type)
    + "\x00"              # ← null byte — cannot appear in field values
    + str(derived_entity_key)
    + "\x00"
    + str(category)
    + "\x00"
    + str(int(time_bucket))   # ← int() enforces integer bucket
)
return "L1-" + hashlib.sha256(material.encode("utf-8")).hexdigest()[:32]
```
Null byte as delimiter eliminates all hash collisions. `int(time_bucket)` fixes float drift.

**Fix 2 — Type-prefixed entity keys in `derived_entity_key()`:**
```python
for field_name, prefix in (
    ("source_entity_id", "entity"),
    ("user_id",          "user"),
    ("asset_id",         "asset"),
    ("source_location",  "loc"),
):
    value = event.get(field_name)
    if _present(value):
        return f"{prefix}:{str(value).strip()}"
```
Type prefix prevents `user_id=X` from matching `asset_id=X` as the same entity.

**Fix 3 — `_identity_groups()` groups by `(entity_key, category, bucket)` tuple:**
Each event maps to exactly one group. No cross-product. The correlation loop runs over groups, not over all alert pairs. This is the O(N) path.

### Performance result

| Phase | Pre-Campaign-P1 | Post-Campaign-P1 | Improvement |
|---|---|---|---|
| SOC analyze avg (250 decisions) | 25,602ms | 1,767ms | **14.5×** |
| Campaign identity stability | Non-deterministic | Deterministic (SHA-256 truncated) | — |
| Collision risk | Present | Eliminated | — |

### Campaign-P1 NL summary (notable: deterministic, no LLM)

`build_nl_summary()` generates campaign summaries from templates only:
```python
f"{n} alerts: {cat_str} over {dur_hours}h. Kill chain pattern detected."
```
No LLM call. Fast. Consistent. Proof-safe.

### Campaign graph schema (6 campaigns, 25 MEMBER_OF edges as of F8)

```
Campaign node:
  campaign_id, first_seen, last_seen, alert_count,
  category_sequence, shared_entities, technique_sequence,
  confidence, trigger_rule, rule_type, derived_entity_key,
  category, time_bucket, severity, nl_summary

Alert-[:MEMBER_OF]->Campaign
Decision-[:DECIDED_ON]->Alert-[:MEMBER_OF]->Campaign
```

---

## Part 86 — Hot-Path Architecture: Pkg 1 Pooled AGE Adapter (June 12, 2026)

**Source:** Scan C grep results on `ci-platform/ci_platform/graph/age_client.py`  
**Status:** Pooling built INTO `age_client.py` — not a separate file.

### Architecture (from grep evidence)

Pkg 1 extends the existing `AGEClient` with opt-in connection pooling via `psycopg_pool`:

```python
# L51: availability check at module load
_PSYCOPG_POOL_AVAILABLE = importlib.util.find_spec("psycopg_pool") is not None

# L128: stored on instance
self._pool_available = _PSYCOPG_POOL_AVAILABLE

# L136: mode set at construction
self._connection_mode = "pooled"

# L144-151: pool init/close lifecycle methods

# L158-163: connection_mode property
# returns "pooled" when psycopg_pool available, "warm_fallback" otherwise

# L180: lazy import inside pool init
from psycopg_pool import ConnectionPool
```

### Three connection modes

| Mode | Condition | Cost per query |
|---|---|---|
| `pooled` | `psycopg_pool` installed | **1.1ms** (from Step-0-spike) |
| `warm_fallback` | psycopg_pool absent, same-connection reuse | ~5-15ms est |
| `fresh` (pre-Pkg 1) | New connection every query | **83.2ms** (from Step-0-spike) |

The 82ms connection tax (98.7% of pre-Pkg-1 read cost) is eliminated when `psycopg_pool` is installed. This is the single largest performance lever available without changing the query structure.

### Per-copilot adoption (Pkg 6, per-copilot)

SDK copilots (Trading, Purchasing, DataOps, S2P) adopt the pooled adapter when they migrate to AGE (per AGE adoption sequence in Part 84). The pool is already in ci-platform — copilots just need to install `psycopg_pool` and use the standard `AGEClient` construction. No code changes to copilot routers.

**Full `age_client.py` read pending** — a second scan will confirm pool size, connection lifecycle, and whether warm_fallback uses persistent connection or reconnects per query.

---

## Part 87 — narrator.generate_reasoning(): Confirmed LLM Call (June 12, 2026)

**Source:** `gen-ai-roi-demo-v4-v50/backend/app/services/reasoning.py` (109 lines, scanned June 12)

### What narrator is

```python
class ReasoningNarrator:
    def __init__(self):
        self._initialized: bool = False
        self.model = None    # GenerativeModel("gemini-1.5-pro-002") — Vertex AI

    def _ensure_init(self) -> None:
        # Deferred: import vertexai takes ~8s at module level
        import vertexai
        from vertexai.generative_models import GenerativeModel
        project_id = os.getenv("PROJECT_ID")
        region     = os.getenv("VERTEX_AI_LOCATION", "us-central1")
        vertexai.init(project=project_id, location=region)
        self.model = GenerativeModel("gemini-1.5-pro-002")
        self._initialized = True
```

`narrator.generate_reasoning()` calls **Vertex AI Gemini-1.5-pro-002** with a ~20-line prompt containing full alert context (user, asset, risk scores, travel, MFA, device match, campaign). This is the function called at L607 of `triage.py` between `scorer_decision` and `decision_node_and_edge_write` with no `_soc_perf_phase` wrapper.

### Two execution paths

**Path A — Vertex AI live (PROJECT_ID set, GCP credentials present):**
```python
response = await self.model.generate_content_async(prompt)
return response.text.strip()
```
Round-trip to Google Cloud. ~1–3s per analyze call depending on model latency.

**Path B — Fallback (any exception including missing credentials):**
```python
except Exception as e:
    return self._fallback_reasoning(action, context)
```
`_fallback_reasoning()` is a deterministic template — ~0ms.
Only handles 3 actions: `false_positive_close`, `auto_remediate`, `escalate_incident`.
All other actions (including the 4 canonical scorer actions: escalate, investigate, suppress, monitor) fall through to the generic else branch — also deterministic, also fast.

### Impact on proof runs vs production

| Environment | Path | Latency contribution |
|---|---|---|
| Proof runner (no GCP creds) | Fallback | ~0ms |
| Phase-C-25 trace (3,688ms analyze avg) | Likely **Path A (live)** | ~2,800ms (the 82% gap) |
| Post-Campaign-P1 (1,767ms avg) | **Unknown** — either env changed or Campaign-P1 alone explains it | — |

**Key open question:** Was `PROJECT_ID` set during the Phase-C-25 run? If yes, the 82% gap (3,028ms) is entirely narrator. If no, the 82% gap must come from something else (campaign correlation pre-Campaign-P1 is the more likely explanation).

**Campaign-P1 alone explains the 25,602ms → 1,767ms speedup** without narrator being on the critical path. Campaign P1 ran the `fetch_all_events()` query (scan all Decisions) on EVERY analyze call, then correlated everything O(N²). This query alone at 250 decisions would be 20+ seconds.

### Recommended instrumentation

```python
# triage.py L607 — add immediately:
with _soc_perf_phase("narrator_reasoning", route=_perf_route, alert_id=alert_id):
    reasoning = await narrator.generate_reasoning(alert_type, selected_action, context)
```

One trace cycle will determine definitively whether narrator is on the post-campaign-P1 critical path. If it shows <50ms, the fallback is firing (PROJECT_ID unset). If it shows >500ms, Vertex AI is live.

### Production recommendation

If narrator is confirmed live in production: move it off the critical path. The `reasoning` field in the analyze response is narrative only — it does not affect the decision, confidence, referral, or any downstream gate. It can be:
1. Fire-and-forget (return response, write reasoning async)
2. Cached per `(alert_type, action)` tuple with short TTL
3. Replaced entirely with `_fallback_reasoning()` for proof/demo runs



---

## Part 86 — Pkg 1: AGEClient Pooling Architecture (June 12, 2026)

**Source:** `ci-platform/ci_platform/graph/age_client.py` (1,103 lines, scanned June 12)

### Architecture decision

Pooling is built into the existing `AGEClient` class — not a separate file.
The module-level check `_PSYCOPG_POOL_AVAILABLE = importlib.util.find_spec("psycopg_pool") is not None`
happens at import time. `psycopg_pool` is an optional install; the client
degrades gracefully when absent.

### Three connection modes

Set at construction time via `AGE_USE_POOL` env var or `use_pool` argument:

| Mode | Condition | Cost per query | Behavior |
|---|---|---|---|
| `fresh` | `AGE_USE_POOL` unset / False | **83.2ms** | New `psycopg.connect()` per query via `asyncio.to_thread()` |
| `pooled` | `AGE_USE_POOL=true` + psycopg_pool installed | **1.1ms** | `ConnectionPool.connection()` context manager |
| `warm_fallback` | `AGE_USE_POOL=true` + psycopg_pool absent | ~5-15ms est. | Single persistent connection behind `threading.RLock()` |

### Pool configuration

```python
# Defaults — override with env vars
AGE_USE_POOL      = false        # must opt in
AGE_POOL_MIN_SIZE = 1
AGE_POOL_MAX_SIZE = 5

# Constructor signature
AGEClient(
    dsn=None,           # defaults to DATABASE_URL env
    graph_name=None,    # defaults to AGE_GRAPH_NAME env
    use_pool=None,      # overrides AGE_USE_POOL
    pool_min_size=None, # overrides AGE_POOL_MIN_SIZE
    pool_max_size=None, # overrides AGE_POOL_MAX_SIZE
)
```

Pool is created lazily on first `_ensure_pool()` call with:
```python
ConnectionPool(
    conninfo=self._dsn,
    min_size=self._pool_min_size,   # default 1
    max_size=self._pool_max_size,   # default 5
    kwargs={"autocommit": True, "connect_timeout": 10},
    configure=self._configure_age_session,  # LOAD 'age' + SET search_path
    open=True,   # eager open at init time
)
```

If pool init fails (e.g. psycopg_pool import error), client falls back to
`warm_fallback` and logs a warning — no hard failure.

### Session configuration

Every new connection (fresh or warm) calls `_configure_age_session()`:
```python
conn.execute("LOAD 'age'")
conn.execute("SET search_path = ag_catalog, '$user', public; SET statement_timeout = '120s'")
```

This loads the AGE extension and sets the 120-second statement timeout.
Pool's `configure=` parameter ensures pooled connections also receive this.

### Safety guards built in

`_check_safe_cypher()` rejects two AGE anti-patterns at call time:
- `SET n = {}` (deletes all properties — AGE interprets as empty map assignment)
- `MERGE (` — unsupported in AGE; MATCH-then-CREATE must be used instead

All parameter interpolation uses `serialize_for_age()` (inlined literals,
not `$1` positional params — AGE does not support those inside `$$` blocks).

### Retry logic

`_sync_execute()` retries up to 3 times on `"Entity failed to be updated"` errors
with jittered backoff (0.1s × attempt + random 0-50ms). All other errors propagate
immediately. On warm_fallback, a failed query discards the warm connection
so the next attempt reconnects.

### warm_fallback persistence model

`_ensure_warm_connection()` returns the existing `_warm_conn` if it is open,
creates a new one otherwise. All warm-fallback queries acquire `_warm_lock`
(threading.RLock) before using the connection — serialized but persistent.
`_discard_warm_connection()` closes and nulls the connection; called on any
query failure so the next call reconnects cleanly.

### Referral count queries (get_sequence_count / get_cross_category_count)

Both referral engine queries use Python `datetime.now() - timedelta(minutes=N)`
for the cutoff timestamp rather than Cypher `duration()` (not supported in AGE).
The timestamp is passed as an ISO string parameter. This is the correct pattern
and is enforced as a code pattern across all AGEClient time-window queries.

### Per-copilot adoption (Pkg 6)

SDK copilots (Trading, Purchasing, DataOps, S2P) currently use SQLite.
When they migrate to AGE (per the adoption sequence in Part 84), they:
1. Install `psycopg_pool` (already in ci-platform requirements)
2. Set `AGE_USE_POOL=true` in their environment
3. Use the standard `get_graph_client()` factory — no code changes to routers

The pool is already built. Adoption is a configuration change, not a code change.

---

## Part 88 — P28/P29/P30 Implementation State (June 12, 2026)

### P28 S2P-F10-FINANCIAL-P1 — COMPLETE

**Location:** `s2p-copilot/backend/app/services/financial_impact.py` (117 lines)
**Test file:** `s2p-copilot/backend/tests/test_financial_impact.py` (210 lines, 13 tests)
**Endpoint:** `GET /api/s2p/financial-impact`

**What was built:**

`compute_financial_impact(decisions, receipts=None) -> FinancialSummary`

Pure function. No graph calls. Receipt-based aggregation: for each verified
decision, looks up its receipt by `decision_id`/`invoice_id` key. Falls back
to decision-level fields when no receipt is present (tracked as `missing_receipts`).

```python
@dataclass
class FinancialSummary:
    total_decisions: int        # all decisions passed in
    verified_decisions: int     # status in {confirmed, overridden, verified} OR verified=True
    total_amount: float         # sum of receipt.amount (or decision.amount)
    total_at_risk: float        # sum of amount_at_risk
    total_recovered: float      # sum of amount_recovered
    net_savings: float          # = total_recovered
    recovery_rate: float        # total_recovered / total_at_risk
    missing_receipts: int       # decisions with no matching receipt
    by_supplier: dict           # {supplier_name: {count, amount, at_risk, recovered}}
    by_category: dict           # {category: {count, amount, at_risk, recovered}}
```

**Endpoint response shape** (from test contract):
```json
{
  "total_recovered": float,
  "total_at_risk": float,
  "total_leakage_prevented": float,
  "by_category": {category: {...}},
  "auto_approve_savings_hours": float,   // count of auto_approve × 0.25h
  "source": "fixture"
}
```

**Key design decisions:**
- `auto_approve_savings_hours` = count of verified `ground_truth_action == "auto_approve"` × 0.25h — a concrete ROI metric for demo
- `source: "fixture"` in demo mode — honest labelling, will become `"graph"` when live decisions are wired
- Null amounts coerced to 0.0 — no crashes on sparse data
- `net_savings == total_recovered` — no deductions; recovered amount is the saving

### P29 SQLITE-TO-AGE-MIGRATION — COMPLETE (module found, content pending)

**Location:** `copilot_sdk/migrate/sqlite_to_age.py`
**CLI:** `python -m copilot_sdk.migrate sqlite_to_age`
**Tests:** `tests/test_sqlite_to_age_migration.py` (71 tests)

**CLI interface** (from `__main__.py`):
```
python -m copilot_sdk.migrate sqlite_to_age
  --domain      required   e.g. "trading", "purchasing"
  --source      optional   override default source path (~/.ci-platform/<domain>/<domain>.db)
  --age-dsn     required   PostgreSQL DSN for AGE target
  --graph-name  optional   AGE graph name (default: soc_graph)
  --dry-run                read source, report counts, write nothing
  --batch-size  int=50     decisions per AGE write batch
  --no-verify              skip post-migration shadow verification
```

Source of truth: Home DB (`~/.ci-platform/<domain>/<domain>.db`) per Rule 62.
`--source` overrides for dev/test scenarios.

MAP evidence: "Trading 150 migrated, shadow 40/40" — 150 Trading decisions
migrated from SQLite to AGE, shadow verification passed 40 of 40 sampled.

**Full module content pending** — Scan K will read `sqlite_to_age.py` to confirm
the migration logic: batch writes, shadow comparison, rollback path, and
what constitutes a "verified" migrated decision.

### P30 DI-1-SOURCE-PROFILER-P1 — COMPLETE (structure confirmed, content pending)

**Location:** `copilot_sdk/di/` package (extends P42's NLQueryRouter package)

**Package structure after P30:**
```
copilot_sdk/di/
├── __init__.py      # exports: NLQueryRouter, ProfileConfig, SourceProfile, BaseSourceProfiler
├── nl_query.py      # P42: NLQueryRouter (6 intents, pattern-based)
├── models.py        # P30: SourceProfile dataclass + ProfileConfig
└── profiler.py      # P30: BaseSourceProfiler with profile() method
```

**Export confirmation** (`__init__.py`):
```python
from copilot_sdk.di.models import ProfileConfig, SourceProfile
from copilot_sdk.di.profiler import BaseSourceProfiler
__all__ = ["NLQueryRouter", "ProfileConfig", "SourceProfile", "BaseSourceProfiler"]
```

`BaseSourceProfiler.profile(entity_ids: Iterable[str]) -> SourceProfile`

**Full content pending** — Scan L will read `models.py` and `profiler.py` to
document `SourceProfile` fields and what `BaseSourceProfiler.profile()` computes
(reliability score, freshness, recurrence — the DI-1 source profiling dimensions).



---

## Part 89 — P29 SQLite-to-AGE Migration: Architecture (June 12, 2026)

**Source:** `copilot_sdk/migrate/sqlite_to_age.py` (495 lines) + `__main__.py` (64 lines)  
**Tests:** `tests/test_sqlite_to_age_migration.py` (71 tests, 632 lines)

### What is migrated (and what is not)

**Migrated:** Verified decision log only — SQLite rows with `status IN ('confirmed', 'overridden')`.
Outcome columns (actual_action, actual_index, is_correct, verified_at) are merged into the same
AGE Decision node when an outcomes table entry exists.

**Intentionally NOT migrated:** Learned state — L5 centroids, DK weights, Welford accumulators,
conservation signal. The design rationale (from the module docstring): *"Learned state is
re-derived by replaying the ordered verified log."* The migration preserves the inputs to learning
(the verified decisions), not the outputs. This means a freshly migrated copilot starts with
the decision history but zero IKS — IKS is rebuilt as the replay pipeline runs.

### Decision node schema (AGE)

```
Decision {
    # from decisions table
    decision_id, domain, category, category_index,
    factors_json, factor_vector_json,
    recommended_action, recommended_index,
    confidence, probabilities_json, status, created_at,

    # merged from outcomes table (when present)
    actual_action, actual_index, is_correct,
    verified_at, context_json
}
```

### Three verification levels

**Level 1 (always runs unless `--no-verify`):**
Count parity + first/last `created_at` equality between SQLite and AGE.
Fast. Catches truncation, off-by-one, duplicate writes.

**Level 2 (always runs unless `--no-verify`):**
Content parity on a random sample (default 10, `random.Random(0)` for reproducibility).
Checks per sampled decision: `category`, `recommended_action`, `confidence` (abs_tol=1e-9),
`factors_json` (semantic JSON comparison with float tolerance).

**Level 3 (optional — `verify_l3=True` + `preset_config` required):**
Full state-vector replay — re-runs the learning algorithm against migrated decisions and
compares the resulting L5/DK state against the source SQLite state.
Imports `copilot_sdk.migrate.verify_state.verify_level3` at call time.

### Scratch graph pattern

```
--use-scratch-graph:
  1. create_scratch_graph()  → temp AGE graph
  2. verify_scratch_clean()  → confirm empty
  3. _write_batch() × N      → write to scratch
  4. _verify_level1/2()      → verify scratch
  5. copy_to_live()           → copy to target graph
  6. drop_scratch_graph()     → cleanup on success

  On any failure: scratch RETAINED, migration returns FAIL with
  scratch_retained and scratch_retained_reason in result dict.
  Operator can inspect scratch before discarding manually.
```

### Batch semantics

- Default batch size: 50 decisions
- Per-decision: `MATCH (d:Decision {decision_id: X, domain: Y}) RETURN d`
  - Existing → `skipped` count
  - Missing → `CREATE (d:Decision {...}) RETURN d`
- Per-decision exception → `conn.rollback()`, `errors` count incremented
- Any `errors > 0` after all batches → migration FAIL (no partial-success)
- MATCH-then-CREATE throughout — never MERGE (Rule 62 compliance)

### CLI

```powershell
python -m copilot_sdk.migrate sqlite_to_age `
    --domain trading `
    --source ~/.ci-platform/trading/trading.db `   # Rule 62 default
    --age-dsn "host=localhost port=5433 ..." `
    --graph-name soc_graph_c9b `
    --batch-size 50 `
    --use-scratch-graph                            # recommended for production
```

`--dry-run`: reads SQLite, reports counts and a 3-decision sample, writes nothing.
`--no-verify`: skips L1 and L2 (L3 is always opt-in).

### "Trading 150 migrated, shadow 40/40" — what this means

150 verified Trading decisions migrated from `~/.ci-platform/trading/trading.db` to AGE.
3 batches of 50. "Shadow 40/40" = Level 2 content verification ran on 40 sampled decisions
(expanded from the default 10 for the Trading pilot), all 40 passed category/action/
confidence/factors_json parity checks.

### Per-copilot adoption order

Migration tooling is complete. Adoption follows the AGE adoption sequence (Part 84):
DataOps (2nd) → S2P (3rd) → Trading (4th) → Purchasing (5th).
Each run: `--domain <domain> --age-dsn <dsn> --use-scratch-graph`.
Source defaults to `~/.ci-platform/<domain>/<domain>.db` (Rule 62).

---

## Part 90 — P30 DI-1 Source Profiler: Architecture (June 12, 2026)

**Source:** `copilot_sdk/di/models.py` (41 lines) + `copilot_sdk/di/profiler.py` (134 lines)  
**Package:** `copilot_sdk/di/` — extends the P42 NLQueryRouter package

### Package state after P30

```python
from copilot_sdk.di import (
    NLQueryRouter,      # P42: 6-intent pattern-based NL routing
    ProfileConfig,      # P30: quality scoring configuration
    SourceProfile,      # P30: quality profile for one source connector
    BaseSourceProfiler, # P30: profiles a connector over a set of entity IDs
)
```

### ProfileConfig (frozen dataclass)

```python
@dataclass(frozen=True)
class ProfileConfig:
    freshness_weight:    float = 0.3
    completeness_weight: float = 0.3
    consistency_weight:  float = 0.2
    validation_weight:   float = 0.2
    freshness_window_hours: float = 24.0
    required_fields:     list[str] = []   # empty = completeness always 1.0
```

Four quality dimensions, weights summing to 1.0. Window defaults to 24 hours.

### SourceProfile (frozen dataclass)

```python
@dataclass(frozen=True)
class SourceProfile:
    source_name:          str        # from connector.source_name attribute
    entity_type:          str        # from connector.entity_type attribute
    trust_tier:           int        # from connector.trust_tier (default 3)
    freshness_score:      float      # [0,1] — avg freshness across records
    completeness_score:   float      # [0,1] — required_fields coverage
    consistency_score:    float      # [0,1] — HARDCODED 0.5 in P1
    validation_pass_rate: float      # [0,1] — fraction passing connector.validate()
    record_count:         int        # total records fetched
    last_profiled:        datetime   # UTC timestamp of profile run
    overall_quality:      float      # weighted sum, clamped [0,1]
    errors:               list[str]  # non-fatal fetch/validate exceptions
```

### BaseSourceProfiler.profile() algorithm

```python
def profile(self, entity_ids: Iterable[str]) -> SourceProfile:
    # 1. Fetch: connector.fetch(entity_id) -> list[dict]
    # 2. Validate: connector.validate(record) -> bool

    # 3. Freshness: per-record score = 1 - (age_seconds / window_seconds)
    #    avg over records with a parseable timestamp field
    #    (checks: timestamp, updated_at, created_at — first present wins)

    # 4. Completeness: fraction of required_fields present and non-empty
    #    if required_fields=[] → completeness = 1.0

    # 5. Consistency: 0.5 (placeholder — P2 deferred)

    # 6. validation_pass_rate: sum(validate(r) for r in records) / len(records)

    # 7. overall_quality = clamp(
    #        0.3 * freshness + 0.3 * completeness +
    #        0.2 * consistency + 0.2 * validation_pass_rate
    #    )
```

**Connector interface** (duck-typed, no ABC):
- `connector.fetch(entity_id: str) -> list[dict]`
- `connector.validate(record: dict) -> bool`
- `connector.source_name: str`
- `connector.entity_type: str`
- `connector.trust_tier: int`

### P1 vs P2 boundary

**P1 (done):** Freshness, completeness, validation scoring. Infrastructure: ProfileConfig,
SourceProfile, BaseSourceProfiler. 16 tests.

**P2 (P32 DI-1-SOURCE-PROFILER-P2, written):** Consistency scoring — currently `0.5`
placeholder. Will compare records across time windows or across entity instances to detect
schema drift, value distribution shifts, or cross-source disagreement.

### Design decision: no graph calls in profiler

`BaseSourceProfiler` is pure Python — no graph queries, no AGE dependency. It profiles
the connector's data quality directly. The graph is not involved. This is correct for
Phase 1 where the profiler runs against freshly fetched records from the source connector.
Future phases may write `SourceProfile` results to the graph as enrichment nodes
(consistent with the DataOpsGraphEnricher infrastructure from P44).

