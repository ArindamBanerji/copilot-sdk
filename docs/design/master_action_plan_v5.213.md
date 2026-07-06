# Master Action Plan v5.213 — Consolidated
**Date:** June 27, 2026 · **Supersedes:** v5.212
**Purpose:** Single authoritative MAP. No prior update specs needed.
**Key changes from v5.150:** Rule #40 updated (localhost/127.0.0.1 split).
Rules 58-59 (AGE adoption discipline). §3A active sprint (campaign identity +
hot-path architecture). AGE smoke gates at tier boundaries. AGE adoption matrix.
Prompt template backend compatibility standard.

---

## §1 — Platform State

| Repo | Tests | Tag | Status |
|---|---|---|---|
| GAE | 1,237 | **v0.7.25** | ✅ pip-installable |
| ci-platform | 350 | **v0.7.4-ci** | ✅ pip-installable |
| SDK root | 915 | **v0.7.0** | ✅ |
| Trading BE | **1,138** | v0.7.0 | ✅ |
| Purchasing BE | 168 | v0.7.0 | ✅ |
| DataOps BE | 176 | v0.7.0 | ✅ |
| S2P BE | 926 | **v0.7.2-s2p** | ✅ |
| SOC BE | ~1,742 | **v5.87** | ✅ |
| **Total** | **~6,241** | | **0 failures** |

### Copilot Ports

| Copilot | Backend | Frontend | Graph Backend | Accent |
|---|---|---|---|---|
| SOC | 8001 | 5173 | **AGE** | Blue |
| S2P | 8002 | 5177 | SQLite | Amber |
| Trading | 8010 | 5174 | SQLite | Red |
| Purchasing | 8020 | 5175 | SQLite | Green |
| DataOps | 8030 | 5176 | SQLite | Purple |
| PostgreSQL+AGE | 5433 | — | — | — |

### Tensor Shapes

| Copilot | Current | Target (PD) | Migration item |
|---|---|---|---|
| SOC | (6,4,6)=144 | (6,4,6)=144 | None |
| S2P | (5,5,7)=175 | (5,5,7)=175 pilot / (5,5,8)=200 Phase 4 | d=8 is future |
| Trading | (5,4,10)=200 | **(5,4,10)=200 LIVE** | — |
| Purchasing | (5,4,6)=120 | **(5,4,7)=140** | **#179** |
| DataOps | (6,5,6)=180 | (6,5,6)=180 | None |

---

## §2 — Items DONE (from v5.150 + prior)

| MAP# | ID | Evidence |
|---|---|---|
| #113 | GP-MYPY-FIX | Fixed in BUGFIX-PRELUDE |
| #112 | PUR-AE-VARIANTS | evolver_config.py complete |
| #80 | CONSERVATION-DISPLAY-FIX | ConservationProjection.tsx built + wired |
| #134 | OUTBOX-DESIGN-SPIKE | Downgraded — P14 embeds full schema |
| — | DEMO-PY-FIX | connect_timeout=5, localhost/127.0.0.1 split, AGE_DSN_DATAOPS fixed |
| — | NO-GRAPH-FIXTURE | DataOps conftest.py + 7 tests patched for GRAPH_BACKEND=age isolation |
| — | LOCALHOST-SWEEP | All 5 repos: DSN→localhost, HTTP→127.0.0.1. Standing note produced. |
| — | CAMPAIGN-P1 | Stable identity tuple. 6 campaigns, 25 MEMBER_OF. O(N²)→O(N). |
| — | STEP-0-SPIKE | cache_model_viable. Pooled read 1.1ms. Connection tax 82ms. |
| — | C9B-PRE-HOTPATH | F8 pass: 250/250, all L5 types, avg analyze 1.77s |

---

## §3 — Written Prompts (P0-P35)

### P0-P27: LOCKED (through Codex or complete)

| P# | ID | Status |
|---|---|---|
| P0 | BUGFIX-PRELUDE | ✅ SHIPPED |
| P1-P18 | (see v5.150 §3) | Through Codex (P5, P13 DROP) |
| P20-P27 | L5 nodes + completion | Through Codex / Complete |

### P28-P35: P28-P30 DONE, P31-P35 WRITTEN (convert to 3-stage)

| P# | ID | Status |
|---|---|---|
| P28 | S2P-F10-FINANCIAL-P1 | **✅ DONE** (v0.7.2-s2p, 13 tests) |
| **P29** | **SQLITE-TO-AGE-MIGRATION** | **✅ DONE** (v0.7.4, all 4 sets, 71 tests, Trading 150 migrated, shadow 40/40) |
| P30 | DI-1-SOURCE-PROFILER-P1 | **✅ DONE** (v0.7.5, 16 tests) |
| P31 | S2P-F10-FINANCIAL-P2 | **✅ DONE** (v0.7.2-s2p, 11+24 tests, 3 endpoints, PW 4/4) |
| P32 | DI-1-SOURCE-PROFILER-P2 | **✅ DONE** (SDK+DataOps, 13 tests, 3 endpoints, PW 2/2) |
| P33 | G12-SITUATION-P1 | **✅ DONE** (SDK situation foundation + SOC adapter, 18+9 tests, no endpoints) |
| P34 | DI-2-INTELLIGENCE-MAP | **✅ DONE** (DataOps FE only, IntelligenceMapPanel, PW 5/5) |
| P35 | G12-SITUATION-P2 | **✅ DONE** (S2P traversal + 5 L1 NL templates + SafeTemplateRenderer, PW 5/5) |

**Total written: 34 prompts. 20 DROPs total (+R2, R3, R5): P5, P13, P19, P48 (shipped differently), P49 (regime shipped), P51 (pre-check confirmed), P65, P67. P54 UN-DROPped and shipped.. Rule 65 compliant.. P28-P30 DONE.**

---

## §3A — Active Sprint: C9B + Campaign + Hot-Path

**These items emerged from P26-P27 investigation. They run parallel
to (not blocking) the P36+ feature queue. SOC-focused but the
hot-path architecture is five-copilot by design.**

### C9B Formal Proof (remaining gate)

| Item | Effort | Status |
|---|---|---|
| C9B formal proof on soc_graph_c9b | ~45min | **NEXT** — F8 passed, pre-hotpath baseline proven |
| L5 COMPLETE = C9A (12) + C9B (3) = 15 cells | — | Blocked on C9B |

### Campaign Identity Phase 2 (approved architecture)

| Item | Effort | Status | Doc |
|---|---|---|---|
| make_campaign_id() → stable identity hash | 0.5d | Ready | soc_campaign_identity_v1.1 |
| derived_entity_key() with type-prefix | 15min | Ready | Review items 3+6 mandatory |
| check_alert() → MERGE-based | 0.5d | Ready | |
| CONTINUES edge for multi-day | 0.5d | Ready | |
| 13 tests | 0.5d | Ready | |
| **Total** | **~3d** | **Prompt not yet written** | |

**Pre-implementation fixes required:** (1) delimiter in hash input (item 6 from review), (2) time_bucket as int64 (item 3 from review).

### Hot-Path Architecture (evidence-backed)

**Authority:** copilot_hot_path_architecture_v2.6
**Step 0 spike result:** cache_model_viable (pooled read 1.1ms, connection tax 82ms = 98.7%)

| Package | Effort | Scope | Status |
|---|---|---|---|
| Pkg 0: Step 0 spike | — | Measured | ✅ DONE |
| Pkg 1: Pooled AGE adapter | 1.5d | ci-platform | ✅ DONE (Track A) |
| Pkg 2: MaterializedCounterStore | 1.5d | ci-platform | After Pkg 1 |
| Pkg 3: EntityCache | 1.5-2d | ci-platform | After Pkg 1 |
| Pkg 4: BackgroundTaskManager | 0.5d | ci-platform | After Pkg 1 |
| Pkg 5: DecisionPipeline + SOC adopt | 1d | ci-platform + SOC | After Pkg 2-4 |
| Pkg 6: SDK copilots adopt | 0.5d each | At AGE migration | Per-copilot |

**Execution rule:** Re-measure after Pkg 1. If pooling alone gets SOC under 1s at 500 decisions, Pkgs 2-5 become quality-of-life and can interleave with feature work.

**Sequencing:** C9B proof FIRST (current code). Then Pkg 1. Then re-measure. Then decide Pkg 2-5 priority.

---

## §4 — Forward Queue: Next 50 Prompts (P36-P85)

**Principle:** All features before Loom. Docker/VPS LAST.
**Numbering:** Sequential from P36. No gaps.
**Backend compatibility:** All prompts follow §17 template standard.

### Tier 1: S2P Immediate Features (P36-P41)

| P# | MAP# | ID | Repo | Effort |
|---|---|---|---|---|
| ~~P36~~ | ~~#41~~ | ~~S2P-LEAD-TIME~~ | ~~s2p~~ | **✅ DONE** (4 endpoints, 37 tests, PW 6/6, fixture enriched) |
| ~~P37~~ | ~~#52~~ | ~~S2P-NL-TRUST~~ | ~~s2p~~ | **✅ DONE** (trust-weighted NL evidence, 19 tests, PW 5/5) |
| ~~P38~~ | — | ~~S2P-GRAPH-TRAVERSAL~~ → **S2P Context Builder** | ~~s2p~~ | **✅ DONE** (read-only context builder, 18 tests, PW 6/6, source-labeled) |
| P39 | — | S2P-GRAPH-ENRICHMENT | s2p | 1d |
| ~~P40~~ | ~~#135~~ | ~~S2P-AUTO-APPROVE~~ → **P40B shadow gate** | ~~s2p~~ | **✅ DONE** (shadow/advisory only, 33 tests, PW 7/7. P40C execution deferred.) |
| ~~P41~~ | ~~#136~~ | ~~S2P-CENTROID-EXPLORER~~ | ~~s2p~~ | **✅ DONE** (read-only explorer + FactorRadar FE, 22 tests, PW 14/14. AGE Smoke Gate next.) |

✅ **AGE SMOKE GATE PASSED:** S2P 1289/10skip/0fail with GRAPH_BACKEND=age (June 14, 2026)

### Tier 2: DI + Cross-Copilot (P42-P47)

| P# | MAP# | ID | Repo | Effort |
|---|---|---|---|---|
| ~~P42~~ | ~~#64~~ | ~~DI-3-NL-QUERY~~ | ~~SDK~~ | **✅ DONE** (5 deterministic NL patterns, 43 tests, no LLM/external API) |
| ~~P43~~ | ~~#65~~ | ~~DI-5-COMBINATION-DISCOVERY~~ | ~~SDK~~ | **✅ DONE** (pure-Python discovery engine, 22 tests, non-causal, no external deps) |
| ~~P44~~ | — | ~~DI-5-GRAPH-ENRICHMENT~~ | ~~SDK~~ | **✅ DONE** (BaseGraphEnricher framework, 29 tests, P39A substrate reuse, provenance-safe) |
| ~~P45~~ | ~~#109~~ | ~~TOAST-POS~~ | ~~SDK~~ | **✅ DONE** (v0.7.8, 27 tests, ToastConnector + MockToast + POS router + profiler wired) |
| ~~P46~~ | ~~#110~~ | ~~PUR-WEEKLY-REPORT~~ | ~~SDK~~ | **✅ DONE** (v0.7.6, 18 tests, domain-agnostic WeeklyReportGenerator, kitchen-language) |
| ~~P47~~ | — | ~~POLARITY-FIX~~ | ~~cross~~ | **✅ DONE** (v0.7.7, 16 tests, display-only, 30 factors across 4 presets, scorer independence proven) |

✅ **AGE SMOKE GATE PASSED:** DataOps 216/216 both modes (June 14, 2026)

### Tier 3: Trading Phase 0 — POC (P48-P53)

| P# | MAP# | ID | Effort | Key detail |
|---|---|---|---|---|
| ~~P48~~ | ~~#150~~ | ~~TRD-DOMAIN-CONFIG~~ | ~~SDK~~ | **✅ DONE** (v0.7.9, 17 tests, SDK domain base classes + TradingDomainConfig, scorer independence proven) |
| ~~P49~~ | ~~#151~~ | ~~TRD-ALPACA-CONNECTOR~~ → **TRD-REGIME-RECOMMENDER** | ~~SDK~~ | **✅ DONE** (v0.7.10, 19 tests, PW 12/12, regime-conditioned edge + sizing + transitions) |
| ~~P50~~ | ~~#152~~ | ~~TRD-YFINANCE~~ | ~~SDK~~ | **✅ CLOSED/PASS** (v0.7.11, 55 BE + 14 PW. MarketDataProvider + cache cascade + F-21 provenance + ProvenanceBadge) |
| ~~P51~~ | ~~#153~~ | ~~TRD-SIGNAL-FACTORS~~ | — | **❌ DROP_CONFIRMED** (Rule 65 pre-check: 10 factors, 83 tests, all bounded [0,1], runtime verified) |
| ~~P52~~ | ~~#154~~ | ~~TRD-CLI-CORE~~ | ~~SDK~~ | **✅ CLOSED/PASS** (v0.7.12, 27 tests. 9 SDK-backed cmds. Self-confirm guard. GPT-5.5 1P1+6P2 fixed.) |
| ~~P53~~ | ~~#155~~ | ~~TRD-TRUST-RADAR~~ | ~~SDK~~ | **✅ CLOSED/PASS** (v0.7.13, F2 HERO. Dual-mode DK radar. TrustAnalyzer. 11 BE + 15 PW. 29/29 full suite.) |

**→ AGE SMOKE GATE: Trading full test suite with GRAPH_BACKEND=age after P53**

### Tier 4: Trading Phase 1 — v1.0 (P54-P63)

| P# | MAP# | ID | Effort | Key detail |
|---|---|---|---|---|
| ~~P54~~ | ~~#156~~ | ~~TRD-REMAINING-FACTORS~~ | ~~SDK~~ | **✅ CLOSED/PASS** (UN-DROPped. 2 context gaps fixed: regime_accuracy dict + signal_confidence keys. 10/10 non-default proof. +4 tests.) |
| ~~P55~~ | ~~#157~~ | ~~TRD-PATTERN-DETECTOR~~ | ~~SDK~~ | **✅ CLOSED/PASS** (v0.7.14, 49 tests. 8 statistical detectors. Fisher+chi2+Spearman. Annual cost. PD F4 satisfied.) |
| ~~P56~~ | ~~#158~~ | ~~TRD-CONSERVATION-STRAT~~ | — | **❌ DROP_CONFIRMED** (already exists: conservation-breakdown + promotion + StrategySafetyBreakdownPanel + 15 tests) |
| ~~P57~~ | ~~#159~~ | ~~TRD-JOURNAL~~ | ~~SDK~~ | **✅ CLOSED/PASS** (v0.7.15, +18 tests. Write-side: manual entry + reflections + tags + search. Concurrent write fix. Corrupt JSON guard.) |
| ~~P58~~ | ~~#160~~ | ~~TRD-IKS-WIRE~~ | — | **❌ DROP_CONFIRMED** (7-area pre-check: IKS full stack wired — IKSService + scorer + iks_base + /api/trajectory + FE display + tests) |
| ~~P59~~ | ~~#161~~ | ~~TRD-IBKR~~ | ~~SDK~~ | **✅ CLOSED/PASS** (v0.7.16, gap closure. +historical OHLCV, broker factory, options fields, ConnectionError. 23 broker tests.) |
| ~~P60~~ | ~~#162~~ | ~~TRD-CSV-IMPORT~~ | ~~SDK~~ | **✅ CLOSED/PASS** (v0.7.16, gap closure. +delimiter auto-detect, Alpaca preset, European dates, preset validation. 25 CSV tests.) |
| ~~P61~~ | ~~#163~~ | ~~TRD-CLI-FULL~~ | — | **❌ DROP_CONFIRMED** (all 5 commands exist in 1206-line cli.py, 102 CLI tests. Ported to cli_sdk.py in P62.) |
| ~~P62~~ | ~~#164~~ | ~~TRD-PYPI~~ | ~~SDK~~ | **✅ CLOSED/PASS** (v0.7.17, 13-cmd product CLI consolidated. pip-installable. GPT-5.5 1P1+3P2 fixed. 41 CLI tests.) |
| ~~P63~~ | ~~#165~~ | ~~TRD-EVIDENCE-NL~~ | ~~SDK~~ | **✅ CLOSED/PASS** (v0.7.18, polarity-aware + DK trust inline + negative evidence. 41 tests (+15). Trading 992.) |

### Tier 5: Purchasing Product (P64-P75)

| P# | MAP# | ID | Effort | Key detail |
|---|---|---|---|---|
| ~~P64~~ | ~~#178~~ | ~~PUR-SYNTH-DATA~~ | — | **❌ DROP_CONFIRMED** (50 suppliers, 500 orders, 12 archetypes, generator exists. 221 PUR tests.) |
| ~~P65~~ | ~~#179~~ | ~~PUR-TENSOR-MIGRATE~~ | — | **❌ DROP_CONFIRMED** (runtime at target shape (5,4,7)=140) |
| ~~P66~~ | ~~#180~~ | ~~PUR-QBO-CONNECTOR~~ | ~~SDK~~ | **✅ CLOSED/PASS** (v0.7.19, full-stack QBO: backend+FE+10 PW. 38 BE + 10 PW. OAuth 2.0, 30 mock vendors, kitchen language.) |
| ~~P67~~ | ~~#181~~ | ~~PUR-FACTORS-7~~ | ~~SDK~~ | **✅ CLOSED/PASS** (UN-DROPped. 7 factors + 4-path wiring. P54 lesson applied. 32 tests.) |
| ~~P68~~ | ~~#182~~ | ~~PUR-SPEND-DASH~~ | ~~SDK~~ | **✅ CLOSED/PASS** (v0.7.20, full-stack. SpendDashboardService + SpendSummaryPanel + 14 PW. 13 BE tests.) |
| ~~P69~~ | ~~#183~~ | ~~PUR-MATCH-ENGINE~~ | ~~SDK~~ | **✅ CLOSED/PASS** (v0.7.21, 3-way match + confidence + kitchen-language + MatchResultPanel + 7 PW. 21 tests.) |
| ~~P70~~ | ~~#184~~ | ~~PUR-ORDER-QUEUE~~ | ~~SDK~~ | **✅ CLOSED/PASS** (v0.7.22, priority formula + score_read_only + top-3 factors + OrderQueuePanel. 10 BE + 9 PW.) |
| ~~P71~~ | ~~#185~~ | ~~PUR-VERIFY~~ | ~~SDK~~ | **✅ CLOSED/PASS** (v0.7.22, confirm/override + 7 kitchen reason codes + scorer.learn() + 409 idempotent. 16 BE + 9 PW.) |
| ~~P72~~ | ~~#186~~ | ~~PUR-CONSERVATION-FULL~~ | ~~SDK~~ | **✅ CLOSED/PASS** (v0.7.22, AutoOrderGate + 5 invariants + per-category conservation + threshold ratchet + AutoOrderPanel. 15 BE + 9 PW.) |
| ~~P73~~ | ~~#187~~ | ~~PUR-PAR-INTELLIGENCE~~ | ~~SDK~~ | **✅ CLOSED/PASS** (v0.7.28, ParLevelOptimizer + ParLevelPanel + FRED commodity. 21 tests + 8 PW.) |
| ~~P74~~ | ~~#188~~ | ~~PUR-IKS-SCORECARD~~ | ~~SDK~~ | **✅ CLOSED/PASS** (v0.7.28, SupplierScorecard + IKS+ScorecardPanels. 15 tests + 8 PW.) |
| ~~P75~~ | ~~#189~~ | ~~PUR-TRUST-ANALYSIS~~ | ~~SDK~~ | **✅ CLOSED/PASS** (v0.7.28, F11 HERO. TrustRadarPanel + trust router. 16 tests + 8 PW.) |

✅ **AGE SMOKE GATE PASSED:** Purchasing 454/1skip/0fail with GRAPH_BACKEND=age (June 20, 2026)

### Tier 6: Quality + Bugs (P76-P77)

| P# | MAP# | ID | Effort |
|---|---|---|---|
| ~~P76~~ | ~~#57~~ | ~~CA-PROTO-4-MYPY~~ | ~~all~~ | **✅ CLOSED/PASS** (195→0 mypy errors across 4 repos. pyproject.toml config. GPT-5.5 1P1+2P2 fixed.) |
| ~~P77~~ | — | ~~SOC-OPTION-C~~ | ~~SOC~~ | **✅ CLOSED/PASS** (CompoundingScorer migration via adapter. SOC v5.98→v6.3. 2122 BE + 21 PW. Parity: 1000 vectors match.) |

### Tier 7: Infrastructure (P78-P80)

| P# | MAP# | ID | Effort |
|---|---|---|---|
| ~~P78~~ | ~~B4.5~~ | ~~OUTBOX-REPLAY-WORKER~~ | ~~SDK~~ | **✅ CLOSED/PASS** (v0.7.38, OutboxStore+Worker+CLI. Idempotent replay + dead-letter. 26 tests.) |
| ~~P79~~ | ~~#133~~ | ~~L5-PLUS-PROOF~~ | ~~SDK~~ | **✅ CLOSED/PASS** (v0.7.42, 5-level validation script. 17 centroids, 4 DK, 5 conservation. 16 tests.) |
| ~~P80~~ | ~~#87~~ | ~~SDK-DOCS~~ | ~~SDK~~ | **✅ CLOSED/PASS** (v0.7.42, 6 developer docs: getting-started, architecture, creating-a-copilot, graphstore, conservation, substantiation.) |

### Tier 8: Trading Phase 1.1 (P81-P85)

| P# | MAP# | ID | Effort | Key detail |
|---|---|---|---|---|
| ~~P81~~ | ~~#166~~ | ~~TRD-REGIME-CLASSIFIER~~ | ~~SDK~~ | **✅ CLOSED/PASS** (v0.7.42, F10. RegimeClassifier+History+Router+Panel. Per-category×regime accuracy. 35 BE + 12 PW.) |
| ~~P82~~ | ~~#167~~ | ~~TRD-REALTIME-SCORE~~ | ~~SDK~~ | **✅ CLOSED/PASS** (v0.7.42, F9. PreScorer+Router+Panel. score_read_only ONLY. Cosine similarity. 29 BE + 10 PW.) |
| P83 | #168 | TRD-PROMOTION-ENGINE | 1w | Paper→small→full. Conservation-gated. |
| ~~P84~~ | ~~#169~~ | ~~TRD-AGENT-EVOLVER-FULL~~ | ~~SDK~~ | **✅ CLOSED/PASS** (v0.7.53, variant shadow-test + 4-gate promotion. TradingVariantGenerator + EvolutionPanel. 17 BE + 4 PW.) |
| P85 | #170 | TRD-REGIME-RECOMMEND | — | **⚠️ PRE-CHECK_REQUIRED / POSSIBLY_SUPERSEDED_BY_P49.** P49 shipped regime recommender. Verify remaining scope. |
| ~~P86~~ | — | ~~OSS-EVOLVE~~ | ~~SDK~~ | **✅ CLOSED/PASS** (v0.7.53, domain-agnostic ScorerEvolution + hard bounds + conservation gate + rollback. 16 SDK + 5 PW.) |
| ~~P87~~ | — | ~~GAP-H2-DEMO~~ (transfer) | ~~SDK~~ | **✅ CLOSED/PASS** (v0.7.54, supplement. Category mappings + /execute + TransferPanel + TransferComparisonCard. 17 BE + 7 PW.) |
| ~~P88~~ | — | ~~BLOCK-1.2~~ (archetypes) | ~~SDK~~ | **✅ CLOSED/PASS** (v0.7.54, supplement. Archetype router + Selector + ComparisonCard + first-run. 15 BE + 7 PW.) |
| ~~P89~~ | — | ~~SOC-EXECUTIVE-NARRATIVE~~ | — | **❌ DROP_CONFIRMED** (fully implemented: 807-line tab, 656-line service, PDF export, tests.) |
| ~~P90~~ | — | ~~F17-CROSS-SYSTEM~~ | ~~SDK~~ | **✅ CLOSED/PASS** (v0.7.55, supplement. CrossSystemCorrelator + CrossSystemPanel on DataOps. 10 BE + 5 PW.) |
| ~~#137~~ | — | ~~S2P-NOVELTY-DETECTION~~ | ~~S2P~~ | **✅ CLOSED/PASS** (v0.7.17-s2p, supplement. Conservation link + auto-approve gate + NoveltyAlertBanner. 5 BE + 6 PW.) |
| ~~#138~~ | — | ~~S2P-FACTOR-PROPOSER~~ | ~~S2P~~ | **✅ CLOSED/PASS** (v0.7.17-s2p, full build. FactorProposer + FactorInsightPanel. 12 BE + 6 PW.) |
| ~~R1~~ | — | ~~TRD-EARNINGS-SUBCAT~~ | ~~SDK~~ | **✅ CLOSED/PASS** (v0.7.56, supplement. EarningsInsightCard. 24 existing + 3 PW.) |
| ~~R2~~ | — | ~~TRD-VIX-TIMING~~ | — | **❌ DROP_CONFIRMED** (221 lines, 28 tests, VIXTimingPanel, PW spec — fully implemented.) |
| ~~R3~~ | — | ~~TRD-CORRELATION-MONITOR~~ | — | **❌ DROP_CONFIRMED** (239 lines, 26 tests, CorrelationPanel, PW spec — fully implemented.) |
| ~~R4~~ | — | ~~TRD-EXECUTION-ANALYSIS~~ | ~~SDK~~ | **✅ CLOSED/PASS** (v0.7.56, full build. ExecutionQualityCard. 13 BE + 5 PW.) |
| ~~R5~~ | — | ~~TRD-OPTIONS-FACTORS~~ | — | **❌ DROP_CONFIRMED** (222 lines, 51 tests, OptionsFactorPanel, PW spec — fully implemented.) |
| ~~R6~~ | — | ~~TRD-TRADINGVIEW-HOOK~~ | ~~SDK~~ | **✅ CLOSED/PASS** (v0.7.56, supplement. WebhookStatusCard. 10 existing + 5 PW.) |
| ~~R7~~ | — | ~~PUR-WEATHER~~ | ~~SDK~~ | **✅ CLOSED/PASS** (v0.7.57, supplement. WeatherImpactCard + category-specific risk. PD F12. 10 BE + 6 PW.) |
| ~~R8~~ | — | ~~PUR-PREP-WASTE~~ | ~~SDK~~ | **✅ CLOSED/PASS** (v0.7.57, supplement. WasteTracker + WasteAlertCard + benchmarks. PD F12. 10 BE + 6 PW.) |
| ~~R9~~ | — | ~~PUR-MENU-ENGINEERING~~ | ~~SDK~~ | **✅ CLOSED/PASS** (v0.7.57, full build. MenuEngineer + MenuMatrixCard 2×2 quadrant. PD F15. 13 BE + 7 PW.) |
| ~~R10~~ | — | ~~PUR-EVENT-CATERING~~ | ~~SDK~~ | **✅ CLOSED/PASS** (v0.7.58, supplement. EventPlanner + Bayesian adjustment + EventPlannerCard. PD F13. 13 BE + 6 PW.) |
| ~~R11~~ | — | ~~PUR-CHAIN-TRANSFER~~ | ~~SDK~~ | **✅ CLOSED/PASS** (v0.7.58, full build. ChainTransfer "Holy Grail" — warm_start_centroids + shape validation + DK never transferred. PD I8. 31 BE + 7 PW.) |
| ~~R12~~ | — | ~~PUR-DELIVERY~~ | ~~SDK~~ | **✅ CLOSED/PASS** (v0.7.58, full build. DeliveryCoordinator + time windows + order merging + DeliveryScheduleCard. PD M2. 21 BE + 6 PW.) |
| ~~R13~~ | — | ~~PUR-PREDICTIVE-PAR~~ | ~~SDK~~ | **✅ CLOSED/PASS** (v0.7.59, supplement. Day/weather/event multipliers + conservation GREEN gate + safety bounds. PD F3+F14. 18 BE + 6 PW.) |
| ~~R14~~ | — | ~~PUR-CROSS-DISCOVERY~~ | ~~SDK~~ | **✅ CLOSED/PASS** (v0.7.59, full build. Wraps P43 CombinationDiscoveryEngine for Purchasing. Kitchen language. PD F16. 12 BE + 6 PW.) |
| ~~R15~~ | — | ~~PUR-ALERTS~~ | ~~SDK~~ | **✅ CLOSED/PASS** (v0.7.59, full build. 7 alert types from PD scenarios. No AMBER fabrication. Dedup enforced. PD P3/P7/I2. 24 BE + 7 PW.) |
| ~~R16~~ | — | ~~PUR-ECON~~ | ~~SDK~~ | **✅ CLOSED/PASS** (v0.7.60, full build. ROI model per PD §6/§9. Hackett benchmarks. Weekly report. 22-46x ROI verified. 24 BE + 6 PW.) |
| ~~R17~~ | — | ~~PUR-MULTI-UNITS~~ | ~~SDK~~ | **✅ CLOSED/PASS** (v0.7.60, supplement. GroupDashboard + cross-location benchmarks + R11 transfer. PD F20/I8. 17 BE + 6 PW.) |
| ~~R18b~~ | — | ~~S2P-SUPPLIER-PROFILES~~ | ~~S2P~~ | **✅ CLOSED/PASS** (v0.7.17-s2p, supplement. SupplierBehavioralProfile + payment/quality/lead_time. Foundation for F14/F16/F19. 30 BE.) |
| ~~R19~~ | — | ~~S2P-TREND-CORRELATION~~ | ~~S2P~~ | **✅ CLOSED/PASS** (v0.7.17-s2p, supplement. Distress archetypes + combined severity + days-to-impact. PD F15. 28 tests.) |
| ~~R20~~ | — | ~~S2P-WORKING-CAPITAL~~ | ~~S2P~~ | **✅ CLOSED/PASS** (v0.7.17-s2p, supplement. Payment-OTIF correlation + DPO optimization + early-pay return. PD F19. 33 tests.) |
| ~~R21~~ | — | ~~S2P-OPTIMIZER-API~~ | ~~S2P~~ | **✅ CLOSED/PASS** (v0.7.17-s2p, supplement. Structured parameter export. (5,5,7)=175 centroids + 35 DK. Gurobi/OR-Tools compatible. PD F20. 16 tests.) |
| ~~R22~~ | — | ~~S2P-DISRUPTION-SIM~~ | ~~S2P~~ | **✅ CLOSED/PASS** (v0.7.17-s2p, supplement. 4 scenario types + alternatives + batch stress test. PD F21. 38 tests.) |
| ~~R23~~ | — | ~~S2P-COMPLIANCE~~ | ~~S2P~~ | **✅ CLOSED/PASS** (v0.7.17-s2p, full build. UFLPA+CSDDD+Scope 3 + SHA256 audit. PD F22. 17 tests.) |
| ~~R24~~ | — | ~~S2P-CLUSTERING~~ | ~~S2P~~ | **✅ CLOSED/PASS** (v0.7.17-s2p, supplement. Behavioral clustering + silhouette + consolidation. PD F16. 37 tests.) |
| ~~R25~~ | — | ~~S2P-PROCESS-TECH~~ | ~~S2P~~ | **✅ CLOSED/PASS** (v0.7.17-s2p, supplement. ProcessFusionCycle 5 stages. PD F18. 27 tests.) |
| ~~R26~~ | — | ~~S2P-TENSOR-D8~~ | ~~SDK+S2P~~ | **✅ CLOSED/PASS** (v0.7.62, full build. 8th factor environmental_risk. (5,5,8)=200. 22 tests.) |
| ~~R27~~ | — | ~~DI-PROMPT-INTEGRATOR~~ | ~~SDK~~ | **✅ CLOSED/PASS** (v0.7.62, full build. First DataOps DI. Jaccard+Levenshtein join. 23 tests.) |
| ~~R28~~ | — | ~~DI-DATA-VALUATION~~ | ~~SDK~~ | **✅ CLOSED/PASS** (v0.7.62, full build. Dollar value per combination. Conservative 70%. DI-6. 16 tests.) |
| ~~R29~~ | — | ~~DI-INTELLIGENCE-MAP-V2~~ | ~~SDK~~ | **✅ CLOSED/PASS** (v0.7.62, full build. Gold lines from R28. IKS badges. DI-7. 13 BE + 5 PW.) |
| ~~R30~~ | — | ~~DI-ACQUISITION-ADVISOR~~ | ~~SDK~~ | **✅ CLOSED/PASS** (v0.7.62, full build. Real catalog. ROI-ranked, free-first. DI-8. 16 tests.) |

---

## §5 — Post-P85 Queue (Long-Term Features)

*(Unchanged from v5.150 — Trading 1.2/2.0, Purchasing 1.1/2.0, S2P 1.1/v2.0/Phase 4, DI A-D, Session Starters)*

### Trading Phase 1.2 + 2.0

| MAP# | ID | Effort | Phase |
|---|---|---|---|
| #171 | TRD-CORRELATION-MONITOR | 1w | 1.2 |
| #172 | TRD-EARNINGS-SUBCAT | 3d | 1.2 |
| #173 | TRD-VIX-TIMING | 3d | 1.2 |
| #174 | TRD-CROSS-INSIGHTS | 4w | 2.0 |
| #175 | TRD-EXECUTION-ANALYSIS | 1w | 2.0 |
| #176 | TRD-OPTIONS-FACTORS | 2w | 2.0 |
| #177 | TRD-TRADINGVIEW-HOOK | 1w | 2.0 |

### Purchasing Phase 1.1 + 2.0

| MAP# | ID | Effort | Phase |
|---|---|---|---|
| #190-#200 | (see v5.150) | | |

### S2P Phase 1.1 + v2.0 + Phase 4

| MAP# | ID | Effort | Phase |
|---|---|---|---|
| #137-#140, #201-#208 | (see v5.150) | | |

### DI Phase A-D

| MAP# | ID | Effort | Phase |
|---|---|---|---|
| #141-#149 | (see v5.150) | | |
| **#209** | **CI-MYPY-COPILOT-CORE** | **2h** | **P3. Pre-existing mypy failures in ci_platform/copilot_core/counters.py (4 no-any-return) and background.py (2 type annotation). Not blocking tests or runtime. Fix before next ci-platform pip install release.** |

### Session Starter Items

| MAP# | ID | Effort |
|---|---|---|
| #26-#30 | (see v5.150) | |

---

## §6 — Demo Tier (#120-#127)

*(Unchanged from v5.150)*

| MAP# | ID | Effort |
|---|---|---|
| #120-#127 | (see v5.150) | |
| #88 | LOOM-V1 | 2d |

---

## §7 — Docker/VPS (LAST)

| ID | Effort |
|---|---|
| DOCKER-COMPOSE | 1.5d |
| VPS-DEPLOY | 1w |

---

## §8 — Level Definitions

*(Unchanged from v5.150)*

---

## §9 — Demo Gating Rules

*(Unchanged from v5.150)*

---

## §10 — Standing Rules (67)

Rules 1-39 from v5.142 (see prior versions for full text).

**Rule #40 (UPDATED June 9, 2026):**

| # | Rule |
|---|---|
| 40 | **WSL2 networking (REVISED June 23, 2026).** Database DSNs: MUST use WSL2 NAT IP (`wsl -u root hostname -I`) + `sslmode=disable`. IP changes per boot — resolve dynamically, never hardcode. `ssl = off` in postgresql.conf. PostgreSQL 17 (`pg_ctlcluster 17 main start`). HTTP calls to uvicorn: `127.0.0.1` (unchanged). See standing_note_wsl2_age_fix_june23.md. |

Rules 41-53 from v5.142 (unchanged).

Rules 54-57 from v5.150:

| # | Rule |
|---|---|
| 54 | Historical migration uses outbox replay. SQLite NOT deleted. Twice = no dupes. |
| 55 | "Managed by AGE" requires migration. demo.py --status shows state per copilot. |
| 56 | Trading penalty_ratio = 3.0 (PD v1.0 authoritative). |
| 57 | Kitchen language mandatory for Purchasing UI. |

**New rules (v5.151):**

| # | Rule |
|---|---|
| 58 | **No raw sqlite3 in feature code.** All persistence through GraphStore protocol methods only. No `import sqlite3` or `sqlite3.connect()` in production code (tests/migration scripts exempt). Violation = P1 fix before tag. |
| 59 | **AGE smoke gate at tier boundaries.** Each copilot's full test suite must pass with `GRAPH_BACKEND=age` at the tier boundary noted in §4. Failures generate migration-fix prompts immediately — they do NOT block feature shipping. Gate is non-blocking for features, blocking for "AGE-ready" status. |

---

## §11 — Canonical Tensor Values

*(Unchanged from v5.150)*

| Copilot | Current Tensor | Target Tensor | Centroid values | +DK weights | Total |
|---|---|---|---|---|---|
| SOC | (6,4,6) | — | 144 | 144 | 288 |
| S2P | (5,5,7) | (5,5,8) Phase 4 | 175 | 175 | 350 |
| Trading | (5,3,6) | **(5,4,7)** | **140** | **140** | **280** |
| Purchasing | (5,4,6) | **(5,4,7)** | **140** | **140** | **280** |
| DataOps | (6,5,6) | — | 180 | 180 | 360 |
| **Total (target)** | | | **779** | **779** | **1,558** |

---

## §12 — SOC Tab Names

*(Unchanged from v5.150)*

---

## §13 — Copilot Completeness Matrix

*(Unchanged from v5.150 — all zero gaps)*

---

## §14 — Item Count Summary

| Category | Count |
|---|---|
| DONE | ~159 (+13 from v5.153: P28-P30, Track A, CI-MYPY, SDK 36→0, agtype normalizer) |
| Written prompts (P0-P35) | 34 (4 DROPs) |
| Active sprint (§3A) | ~10 items (C9B + campaign + hot-path) |
| Forward queue (P36-P85) | ~47 (2 DROPs: P51, P54). P48 shipped. |
| Post-P85 long-term | 40 |
| Demo tier (#120-#127 + #88) | 9 |
| Docker/VPS | 2 |
| Session starter (#26-#30) | 5 |
| **Total tracked** | **~207** |
| **Active (not DONE)** | **~149** |
| Standing rules | **59** |
| **60** | **AGE read-side normalization.** All direct-psycopg AGE reads MUST use `normalize_agtype_value()`. Write: `serialize_for_age()`. Read: `normalize_agtype_value()`. One canonical function per direction. |
| **61** | **Shadow scorer store isolation.** ShadowScorer.from_preset() MUST reject `primary_store is shadow_store`. Shared stores corrupt shadow discipline. |
| **62** | **Migration source of truth.** Home DB (`~/.ci-platform/<domain>/<domain>.db`) is default migration source. Repo DBs are development artifacts. CLI accepts `--source` for override. |
| **63** | **Evidence provenance required.** Every evidence/context node carries source label (fixture/graph_store/scorer) + provenance tier (context/learned/unavailable). Fixture values never presented as measured customer facts without provenance. GraphStore read ≠ verified outcome. |
| **64** | **Counterfactual faithfulness.** Displayed evidence factors must be actual scorer inputs. Modifying the top displayed factor must change score/action/confidence. No explainability theater. |
| **65** | **DROP requires explicit pre-check.** No MAP item may be marked DROP solely by roadmap inspection. Suspected duplicates or already-live items must become PRE-CHECK_REQUIRED first. Read-only Codex pre-check must return DROP_CONFIRMED, SUPERSEDED, KEEP, PARTIAL, or NEEDS_RENUMBERING before status changes. |
| **66** | **Substantiation tier required.** Every new feature prompt must declare its substantiation tier (T-A/T-S/T-O/T-R) and evidence basis. ClaimRegistry entry required. |
| **67** | **F-26 gate.** No provenance="sample" in any computed metric. is_sample_data() + assert_no_sample_in_metric() gate infrastructure enforced. |

---

## §15 — Dependency Map (P36-P85) + AGE Smoke Gates

```
P28-P35: Ship P29 first (migration tooling), then P28, P30-P35

§3A sprint (parallel to P36+):
  C9B → Campaign Phase 2 → Hot-Path Pkg 1
  Hot-Path Pkg 1 → re-measure → decide Pkg 2-5 priority

P36-P37: Independent
P38-P39: Need graph_contract content
P40-P41: After L5 (P20-P27) — conservation GREEN
  → AGE SMOKE: S2P (Rule 59)

P42-P44: Independent (DI greenfield)
P45-P46: Independent
P47: Independent
  → AGE SMOKE: DataOps (Rule 59)

P48: ✅ DONE (v0.7.9). P49-P53 unblocked.
P49: ✅ DONE (regime recommender). P50-P53 unblocked.
  → AGE SMOKE: Trading (Rule 59)

P54-P63: Depend on P49-P53 Phase 0. P54 CLOSED/PASS (UN-DROPped).

P64: Independent. P65: DROP_CONFIRMED (runtime at target shape).
P66-P75: Unblocked (P65 DROP_CONFIRMED — Purchasing at (5,4,7)).
  → AGE SMOKE: Purchasing (Rule 59)

P76: Independent (mypy)
P77: After L5 complete
P78-P79: After P14 (outbox table)
P80: Independent
P81-P85: Depend on P55-P63. P54 DROP_CONFIRMED. P85 PRE-CHECK_REQUIRED (possibly superseded by P49).
| ~~P86~~ | — | ~~OSS-EVOLVE~~ | ~~SDK~~ | **✅ CLOSED/PASS** (v0.7.53, domain-agnostic ScorerEvolution + hard bounds + conservation gate + rollback. 16 SDK + 5 PW.) |
| ~~P87~~ | — | ~~GAP-H2-DEMO~~ (transfer) | ~~SDK~~ | **✅ CLOSED/PASS** (v0.7.54, supplement. Category mappings + /execute + TransferPanel + TransferComparisonCard. 17 BE + 7 PW.) |
| ~~P88~~ | — | ~~BLOCK-1.2~~ (archetypes) | ~~SDK~~ | **✅ CLOSED/PASS** (v0.7.54, supplement. Archetype router + Selector + ComparisonCard + first-run. 15 BE + 7 PW.) |
| ~~P89~~ | — | ~~SOC-EXECUTIVE-NARRATIVE~~ | — | **❌ DROP_CONFIRMED** (fully implemented: 807-line tab, 656-line service, PDF export, tests.) |
| ~~P90~~ | — | ~~F17-CROSS-SYSTEM~~ | ~~SDK~~ | **✅ CLOSED/PASS** (v0.7.55, supplement. CrossSystemCorrelator + CrossSystemPanel on DataOps. 10 BE + 5 PW.) |
| ~~#137~~ | — | ~~S2P-NOVELTY-DETECTION~~ | ~~S2P~~ | **✅ CLOSED/PASS** (v0.7.17-s2p, supplement. Conservation link + auto-approve gate + NoveltyAlertBanner. 5 BE + 6 PW.) |
| ~~#138~~ | — | ~~S2P-FACTOR-PROPOSER~~ | ~~S2P~~ | **✅ CLOSED/PASS** (v0.7.17-s2p, full build. FactorProposer + FactorInsightPanel. 12 BE + 6 PW.) |
| ~~R1~~ | — | ~~TRD-EARNINGS-SUBCAT~~ | ~~SDK~~ | **✅ CLOSED/PASS** (v0.7.56, supplement. EarningsInsightCard. 24 existing + 3 PW.) |
| ~~R2~~ | — | ~~TRD-VIX-TIMING~~ | — | **❌ DROP_CONFIRMED** (221 lines, 28 tests, VIXTimingPanel, PW spec — fully implemented.) |
| ~~R3~~ | — | ~~TRD-CORRELATION-MONITOR~~ | — | **❌ DROP_CONFIRMED** (239 lines, 26 tests, CorrelationPanel, PW spec — fully implemented.) |
| ~~R4~~ | — | ~~TRD-EXECUTION-ANALYSIS~~ | ~~SDK~~ | **✅ CLOSED/PASS** (v0.7.56, full build. ExecutionQualityCard. 13 BE + 5 PW.) |
| ~~R5~~ | — | ~~TRD-OPTIONS-FACTORS~~ | — | **❌ DROP_CONFIRMED** (222 lines, 51 tests, OptionsFactorPanel, PW spec — fully implemented.) |
| ~~R6~~ | — | ~~TRD-TRADINGVIEW-HOOK~~ | ~~SDK~~ | **✅ CLOSED/PASS** (v0.7.56, supplement. WebhookStatusCard. 10 existing + 5 PW.) |
| ~~R7~~ | — | ~~PUR-WEATHER~~ | ~~SDK~~ | **✅ CLOSED/PASS** (v0.7.57, supplement. WeatherImpactCard + category-specific risk. PD F12. 10 BE + 6 PW.) |
| ~~R8~~ | — | ~~PUR-PREP-WASTE~~ | ~~SDK~~ | **✅ CLOSED/PASS** (v0.7.57, supplement. WasteTracker + WasteAlertCard + benchmarks. PD F12. 10 BE + 6 PW.) |
| ~~R9~~ | — | ~~PUR-MENU-ENGINEERING~~ | ~~SDK~~ | **✅ CLOSED/PASS** (v0.7.57, full build. MenuEngineer + MenuMatrixCard 2×2 quadrant. PD F15. 13 BE + 7 PW.) |
| ~~R18b~~ | — | ~~S2P-SUPPLIER-PROFILES~~ | ~~S2P~~ | **✅ CLOSED/PASS** (v0.7.17-s2p, supplement. SupplierBehavioralProfile + payment/quality/lead_time. Foundation for F14/F16/F19. 30 BE.) |
| ~~R19~~ | — | ~~S2P-TREND-CORRELATION~~ | ~~S2P~~ | **✅ CLOSED/PASS** (v0.7.17-s2p, supplement. Distress archetypes + combined severity + days-to-impact. PD F15. 28 tests.) |
| ~~R20~~ | — | ~~S2P-WORKING-CAPITAL~~ | ~~S2P~~ | **✅ CLOSED/PASS** (v0.7.17-s2p, supplement. Payment-OTIF correlation + DPO optimization + early-pay return. PD F19. 33 tests.) |
| ~~R21~~ | — | ~~S2P-OPTIMIZER-API~~ | ~~S2P~~ | **✅ CLOSED/PASS** (v0.7.17-s2p, supplement. Structured parameter export. (5,5,7)=175 centroids + 35 DK. Gurobi/OR-Tools compatible. PD F20. 16 tests.) |
```

**AGE smoke gate protocol (Rule 59):**
```powershell
# Run at each tier boundary. Non-blocking for features.
$env:GRAPH_BACKEND = "age"
$env:GRAPH_DSN = "host=localhost port=5433 dbname=soc_copilot user=postgres password=postgres"
cd "$env:CLAUDE_SDK"
python -m pytest apps/<copilot>/backend/tests/ -q --timeout=120
# Result: PASS → copilot is AGE-ready
# Result: FAIL → generate migration-fix prompt, feature ships anyway
```

---

## §16 — Existing Prompt Overlaps

*(Unchanged from v5.150)*

---

## §16A — AGE Adoption Tracking Matrix

| Copilot | Backend today | GraphStore? | Raw sqlite3? | L5 proof | AGE smoke | Migration point | Adoption order |
|---|---|---|---|---|---|---|---|
| **SOC** | **AGE ✅** | AGEGraphStore | No | ✅ C9A+F8 | ✅ | **Done** | **1st (done)** |
| DataOps | SQLite | Yes (P17) | **Audit** | — | After P47 | After Tier 2 | **2nd** |
| S2P | SQLite | Yes | **Audit** | — | After P41 | After Tier 1 | **3rd** |
| Trading | SQLite | Yes | **Audit** | — | After P53 | After Tier 3 + tensor | **4th** |
| Purchasing | SQLite | Yes | **Audit** | — | After P75 | After Tier 5 + tensor | **5th** |

**"Audit" columns:** Run the following to baseline raw sqlite3 usage:
```powershell
foreach ($repo in @($env:CLAUDE_SDK, $env:CLAUDE_S2P)) {
    Get-ChildItem $repo -Recurse -Include *.py |
        Where-Object { $_.FullName -notmatch "node_modules|__pycache__|\.git|tests|migration" } |
        Select-String "import sqlite3|sqlite3\.connect" |
        ForEach-Object { "  $($_.Path.Replace($env:CLAUDE_PROJ,''))`:$($_.LineNumber)" }
}
```

**Per-copilot AGE-ready criteria (Rule 58 + Rule 59):**
1. No raw sqlite3 in production code
2. Full test suite passes with GRAPH_BACKEND=age
3. demo.py --status shows graph backend per copilot
4. Migration tooling from P29 applied
5. Rollback path: GRAPH_BACKEND unset → SQLite (existing default)
6. No regression in SQLite default mode

---

## §17 — Prompt Template Standards

**All Codex prompts (P36+) include this backend compatibility block:**

```
BACKEND COMPATIBILITY (Rule 58):
- All persistence through GraphStore protocol. No raw sqlite3.
- Tests must pass with GRAPH_BACKEND unset (SQLite default).
- If test needs AGE: use pytest.mark.skipif(not AGE_AVAILABLE).
- New GraphStore methods: add to protocol + SQLite + AGE implementations.
- New test fixtures: include no_graph monkeypatch where needed.
```

**Connection addresses (Rule 40 — REVISED June 23, 2026):
```
DATABASE DSN: host=localhost    (mirrored WSL2)
HTTP calls:   127.0.0.1        (avoid IPv6 fallback)
```

---

## §18 — Performance Baselines (Measured June 9, 2026)

| Metric | Value | Source |
|---|---|---|
| ProfileScorer.score() | 0.25ms | Phase-C trace |
| SOC analyze (250 decisions, post-campaign-P1) | 1,767ms avg | C9B pre-hotpath baseline |
| SOC analyze (250 decisions, pre-campaign-P1) | 25,602ms avg | F8 proof |
| Pooled AGE point read | 1.1ms | Step 0 spike |
| Fresh AGE point read (unpooled) | 83.2ms | Step 0 spike |
| Connection tax (fresh - pooled) | 82.1ms (98.7%) | Step 0 spike |
| Committed Phase-3 write | 8.8ms avg | Phase-3 diagnostic |
| Hot-path target (cache architecture) | ~47ms projected | Derived from spike |

---

*MAP v5.195 · June 20, 2026 · SUBSTANTIATION SPRINT COMPLETE. 5 oracles. 6 K4 connectors. 32 claims. F-26=0. SDK v0.7.34. SOC v5.95. S2P v0.7.17-s2p. ~115 DONE.*
*~40 active items. 67 rules. 34 prompts written. P28-P30 DONE. ~0 in forward queue.*
*Active sprint: C9B → Campaign Phase 2. Hot-Path Pkg 1 DONE.*
*AGE smoke gates at 4 tier boundaries (non-blocking).*
*Rules 58-62: no raw sqlite3 + AGE smoke + read normalization + shadow isolation + migration source.*
*Rule 40 REVISED June 23: WSL2 NAT IP for DSN (not localhost), 127.0.0.1 for HTTP. ssl=off. PG 17.*
*"All features before Loom. Docker/VPS LAST."*
