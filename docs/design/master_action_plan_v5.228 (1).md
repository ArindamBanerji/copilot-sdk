# Master Action Plan v5.228 — Consolidated
**Date:** August 8, 2026 · **Supersedes:** v5.227. Full MAP audit reconciliation.
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

## §10 — Standing Rules (78)

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
| **68** | **SOC domain scoping.** All SOC Decision queries MUST use `soc_decision_where()` from `app/db/neo4j.py`. No manual domain/archived predicates. |
| **69** | **Shared graph authorization.** Each copilot writing to soc_graph requires exact pair authorization (e.g., `s2p:soc_graph`). |
| **70** | **Domain-prefixed decision IDs.** Non-SOC copilots: TRD-, PUR-, DOPS-, S2P-. SOC retains unprefixed (legacy). |
| **71** | **Preview scorer isolation.** Preview/simulation scorers MUST use InMemoryGraphStore. Production stores never receive synthetic warm-up. |
| **72** | **demo.py hand-edit only.** Added --no-reseed, --preseed-only, --health-timeout. SOC_LEARNING_ENABLED scoped. |
| **73** | **Destructive AGE test guard.** No test may default GRAPH_BACKEND=age or mutate live AGE without TEST_DESTRUCTIVE_AGE=1. |
| **74** | **SOC write/count scoping.** SOC evolution.py and triage.py count/write functions MUST be domain-scoped before shared graph production use. (P1 — referral rule correctness.) |
| **75** | **Framework router reconciliation.** SOC/S2P framework_router.py copies MUST NOT diverge in query structure. Reconcile before SDK extraction. |
| **76** | **DI demo dollar amounts** use preseed fixture data with provenance badge. Never present as measured customer outcomes (F-21/F-22). |
| **77** | **DI trust scores** (0.94, 0.23, etc.) are computed from preseed verified decisions. Real computation on sample data, labeled as such. |
| **78** | **No new neo4j references.** All new code uses "age" or "graph" naming. ~700 existing references cleaned in Program B (store unification). |

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
*~40 active items. 78 rules. 34 prompts written. P28-P30 DONE. ~0 in forward queue.*
*Active sprint: C9B → Campaign Phase 2. Hot-Path Pkg 1 DONE.*
*AGE smoke gates at 4 tier boundaries (non-blocking).*
*Rules 58-62: no raw sqlite3 + AGE smoke + read normalization + shadow isolation + migration source.*
*Rule 40 REVISED June 23: WSL2 NAT IP for DSN (not localhost), 127.0.0.1 for HTTP. ssl=off. PG 17.*
*"All features before Loom. Docker/VPS LAST."*

---


---


## Resolved Diagnostics (do NOT re-run)

| Diagnostic | Result | Consequence |
|---|---|---|
| DIAG-1: AE rejection logged? | PARTIAL — SOC persists + surfaces via `/api/evolution/variant-history`. SDK in-memory only | C-2 is a 1d surfacing task |
| DIAG-2: SOC conservation | live_scorer — `/api/soc/learning-health` returns real α/q/V/θ_min. CALIBRATING < 300 decisions | Demo numbers are real |
| DIAG-3: Integrity gates | Only `Provenanced[T]` exists. Everything else NOT FOUND | C-0 is 4-6d build |
| DIAG-4: Conservation unity | PARTIAL — L1+L2 gated (different functions), L5 ungated, L2b PromptVariantEvolver ungated | C-GOV is 0.5-1d specific fix |
| C-VERIFY-RL | "RL" NOT accurate. Mechanism = online supervised centroid/prototype learning. Blast radius = 63 sites across 5 repos | L1 renamed "decision-trace learning." Read-layer stratification path confirmed. F-25: never name core path `rl_*`/`reward_*`/`policy_*` |
| Situation Analyzer | One shared SDK component (SituationAnalyzer). Role (b) discrimination: PARTIAL. Cross-repo (SOC+S2P) | §3.1 autonomy claim scoped precisely |

## Decisions Confirmed

| ID | Decision | Status |
|---|---|---|
| D1 | OSS boundary: GAE + Trading + SDK scoring primitives = Apache 2.0. Everything else closed | ✅ CONFIRMED |
| D2 | First cut = VC (SOC-led). Trading cut follows | ✅ CONFIRMED |
| D3 | EU AI Act: Omnibus correction accepted. High-risk deferred to Dec 2027. Art-50 at Aug 2026 | ✅ CONFIRMED |
| D4 | Posture: build ambitiously, claim precisely. Gates guard the send, not the roadmap | ✅ CONFIRMED |
| D5 | Cross-copilot judgment transfer: build after C-REGIME (same keyed-centroid-store machinery) | DECIDED — schedule after C-REGIME P3 |

## Four Diagnostic Facts to Build On

1. **Mechanism is NOT RL** — online supervised centroid/prototype learning from verified decisions + DK coordinate-search weight estimation. Genuine bandit components exist but are peripheral.
2. **Regime dimension = 63 consumer sites across 5 repos** — a sequencing input, not a veto. Read-layer stratification ships as precursor; full migration is C-REGIME (staged, each phase shippable).
3. **`PromptVariantEvolver` promotion is UNGATED** — gates only on sample count + improvement, not conservation. C-GOV fixes this.
4. **SOC learning is DISABLED by default** — `soc/config.py:66`, gated at `triage.py:1961-1968`. SOC is the flagship VC cut. C-1 must enable + verify.

---

## Critical Path: Four Tracks

```
Track ①  DO-FIRST:    C-GOV (0.5-1d)
Track ②  DEMO:        C-0 (4-6d) → C-1 (2-3d) → {C-2, C-3, C-4, C-5, S14-C} (5.5-6.5d) → C-6 (3d) → {C-7, C-8, C-9}
Track ③  TRADING:     C-OSS-1Q (3-5d) → C-TRD-SIT Steps 1-2 (2.5d) → C-TRD-VOL V1+V2 (2d) → C-TRD-SIT 3a (1-2d) → C-REGIME (2-3 weeks)
Track ④  ARCHITECTURE: C-REGIME P0-P3 → P4 + EXP-REGIME → P5 → D5 cross-copilot transfer
```

Track ① is a prerequisite for everything. Track ③ runs parallel with Track ② from day 2. Track ④ starts after Track ③ delivers C-TRD-SIT 3a.

---

## Wave 0: Governance Scaffolding (DO-FIRST)

### Batch 27: C-GOV — Conservation Gate Unification (0.5-1 day)

**Purpose:** Make C-17 ("one conservation law governs every compounding loop") code-true. The cheapest, highest-value item in the plan.

**What:** Gate `PromptVariantEvolver` promotion through `ConservationGate`. Currently `prompt_evolver.py:195-215` gates only on sample count + improvement — no conservation check.

| Step | Work | Evidence |
|---|---|---|
| 1 | Read `copilot_sdk/evolution/prompt_evolver.py:195-215` | The ungated promotion path |
| 2 | Read `copilot_sdk/evolution/gate.py:27-41` | The existing `ConservationGate` that gates L2 scorer promotion |
| 3 | Route prompt-variant promotion through the same gate | One function call + fail-closed test |
| 4 | Write test: promotion BLOCKED when conservation gate is RED | GC-01 |
| 5 | Grep: ONE gate across L1/L1b/L2/L2b | GC-02 |

**DoD:** Test asserts `prompt_evolver` promotion blocked when conservation RED. Grep shows one gate. All SDK tests pass.
**Test target:** SDK root (~1,980). 0 failures.
**Tag:** SDK v0.7.74
**Consequence:** Until this lands, every external surface must scope to "governs our scoring, exploration and scorer-evolution loops."

---

## Wave 0.5: Diagnostics + Quant Wiring (parallel)

### Batch 28: C-OSS-1Q — Trading Quant Wiring (3-5 days, parallel with Batch 27)

**Status at v2:**
- Step 0 (placement): ✅ DONE. 19/19 + 1,980/0
- Steps 1+2 (drop-ins + B4): ✅ DONE. Review PASS after fixer. 3,141/0
- Steps 3d+3e (real-fixture + ClaimRegistry): ⏳ Running

| Step | Work | Status |
|---|---|---|
| 0 | Folder move → `ci_trading/quant/` in SDK | ✅ DONE |
| 1a | `classify_regime()` drop-in at F10 | ✅ DONE (string wrapper at `market_regime.py:22`) |
| 1b | `CorrelationMonitor` drop-in at T18 | ✅ DONE (wired at `correlation.py:169`) |
| 1c | `IVRVFactor` drop-in at T17 | ✅ DONE (protocol wrapper at `options.py:123`) |
| 2 | B4 dispersion → θ_min gate | ✅ DONE (effective_q at `scorer.py:792`, capped at n_boot=200) |
| 3a-c | GPT-5.5 review | ✅ PASS (re-review after fixer) |
| 3d | Real-fixture reproduction (3 tests) | ⏳ Running |
| 3e | ClaimRegistry migration (T-O → T-R) | ⏳ Running |

**CRITICAL SEQUENCING:** Wire → green → real-fixture → migrate. Oracle numbers never surfaced before 3d/3e (META-4/F-21).
**Tag after 3d/3e:** SDK v0.7.75

---

## Wave 1: Foundation

### Batch 29: C-0 — Integrity Gate Scaffolding (4-6 days)

**Purpose:** Build the governance infrastructure everything else passes through.
**Dependency:** None (can start parallel with B28 3d/3e)
**Source:** product_integrity_v2.9 §0 Steps 1-7

| Step | Item | Effort | DoD |
|---|---|---|---|
| 1 | T0 scanner (`integrity/architecture_scan.py`) | 2h | `python integrity/architecture_scan.py` → PASS |
| 2 | `Provenanced[T]` type — verify exists | 0.5h | Already at `evidence/provenance.py:12` |
| 3 | Frozen benchmark fixture (500 train + 100 held-out) | 2h | `benchmark_factors_v1.json` + `benchmark_outcomes_v1.json` |
| 4 | Innovation comparative tests (9 tests from §3.1) | 3h | `test_innovation_claims.py` → all pass |
| 5 | Commercial smoke script | 1h | `python integrity/commercial_smoke.py --copilot soc` → PASS |
| 6 | Judgment memory + counterfactual tests | 2h | `test_product_truth.py` → all pass |

**F-25 naming rule (enforced from this batch):** Never name new symbols `rl_*`, `reward_*`, `policy_*` for the core learning path. The mechanism is supervised prototype learning from verified decisions.

**Test target:** SDK root + integrity tests. 0 failures.
**Tag:** SDK v0.7.76

---

### Batch 30: C-1 — Deterministic Demo Preseed (2-3 days)

**Purpose:** The foundation everything records and demos on. Non-negotiable.
**Dependency:** C-0 (Batch 29)

| Item | DoD |
|---|---|
| `demo.py --preseed` | Non-flat IKS ×5, pending alert + order queue, rejected AE variants in logs, cross-copilot signal, `sample` value present but never in headline |
| `demo.py --record-mode` | Pins seed + freezes connectors (FRED/OpenMeteo serve cached values) |
| F-26 audit | No `sample` value in any headline metric across all 5 copilots |
| Byte-identical | Two preseed runs produce identical demo numbers |
| **⚠️ SOC learning ON** | SOC learning enabled in demo profile. Verified: a confirmed decision changes a later SOC score. If not possible, re-cut the VC beat |

**Why SOC learning matters:** SOC is the flagship VC cut. Learning is DISABLED by default (`soc/config.py:66`, gated at `triage.py:1961-1968`). Any "watch it learn / compounding" beat will not fire unless learning is explicitly enabled.

**Test target:** All 6 BE suites (7,830+). All 5 FE builds. All PW suites (~1,485). 0 failures. Two preseed runs identical.
**Tag:** SDK v0.7.77, SOC v5.103

---

### Batch 30.5: DPW — Demo Storyboard Playwright (2-3 days)

**Dependency:** C-1 (Batch 30). Specs skip gracefully without preseed.
**Purpose:** Convert demo storyboards (§2.1-§2.3) into executable PW specs. Catches preseed gaps, CORS regressions, empty rejection tables, missing ProvenanceBadges.

| ID | Item | Effort | DoD |
|---|---|---|---|
| DPW-1 | VC cut spec (7 beats: V1-V7) | 1d | Content assertions across 4 copilots (ports 5173-5176) |
| DPW-2 | Trader cut spec (3 beats: TR1-TR3) | 0.5d | Trading port 5174 only |
| DPW-3 | Enterprise cut spec (8 beats: E1-E8) | 1d | SOC + S2P + DataOps cross-copilot |
| DPW-4 | Shared demo fixture | 0.5d | Port map, health checks, preseed gate |

**Architecture:** Cross-copilot navigation (one browser, multiple ports). Preseed gate (skip if IKS=0). Health-first. Content assertions, not timing. Serial beats. Idempotent.
**Files:** `copilot-sdk/e2e/demo-cuts/{demo-fixture.ts, vc-cut.spec.ts, trader-cut.spec.ts, enterprise-cut.spec.ts}`
**Tag:** SDK v0.7.78 (combined with C-1)


## Wave 2: Hero Moments

### Batch 31: C-2/C-3/C-4/C-5/S14-C — Three Heroes + Trust Beats + Contrast (5.5-6.5 days)

**Dependency:** C-1 (Batch 30), DIAG-1 (resolved: PARTIAL — SOC surfaces rejection reasons)

| ID | Moment | Surface | Effort | DoD |
|---|---|---|---|---|
| C-2 | **Rejection Moment** | Trading Perf + SOC Runtime Evolution | 1d | "47 tested / 12 promoted / 35 rejected — 18 correctness, 11 conservation, 6 variance" table from existing logs |
| C-3 | **Counterfactual** | ≥2 copilots scoring surface | 1d | Perturb factor → real score delta. Feed `sample` → F-26 refused. Live |
| C-4 | **Day-Zero** | ≥1 copilot fresh-tenant view | 1-2d | INSTRUMENT_VALIDATED → ACCUMULATING → MEASURED renders. K=30/arm. Magnitude only from real provenance |
| C-5 | **Staged Trust Beats** (ST-1..4) | SOC + Trading/Purchasing | 2d (0.5 each) | Refusal, red-team simulate_failure, cold-mirror overlay, acts-in-stack |
| S14-C | **Rule-vs-Reasoning Contrast** (NEW) | S2P Exception Triage | 0.5d | Two-column: threshold REJECTS vs SituationPanel ACCEPTS. Computed, not hardcoded. $ impact visible. |

**Test target:** BE suites + hero-moment tests. 0 failures.
**Tag:** SDK v0.7.78, SOC v5.104

---

## Wave 3: Loom + OSS + Trading Intelligence

### Batch 32: Loom Harness (5 days)

**Dependency:** C-1 + hero moments (Batches 30-31)

| ID | Item | Effort | DoD |
|---|---|---|---|
| C-6 | Spotlight+caption overlay (reads beats-config JSON) | 3d | Overlay renders on SDK ×4 + SOC |
| C-7 | Auto-advance runner | 1d | Cut plays unattended |
| C-8 | Reset/replay (`--record-reset --beat V4`) | 1d | Resets to pinned state < 30s |

**Tag:** SDK v0.7.79

---

### Batch 33: C-9 + C-OSS-1 — Beats Config + Trading OSS Extraction (7-8 days)

**Dependency:** D1 ✅, C-OSS-1Q (Batch 28), Loom (Batch 32)

| ID | Item | Effort | DoD |
|---|---|---|---|
| C-9 | Beats-config authoring (3 cut JSONs) | 1d | 3 cuts load in C-6 |
| C-OSS-1 | Trading OSS: standalone, no closed imports, sample trader, BYOD CSV, Rejection Moment, ProvenanceBadge | 6-7d | Stranger → one command → mirror + CSV + evolver |
| OSS-4 | **Launch gate:** clean machine, GAE gate < 5 min, Trading mirror + Rejection < 5 min, §8 FORBIDDEN/CANONICAL passes | 0.5d | Pass/fail |

**Tag:** SDK v0.7.80

---

### Batch 34: C-TRD-SIT — Situation-Conditioned Judgment (4 days)

**Purpose:** Wire situation awareness into Trading scoring. Makes the OSS copilot the proof of C-COUPLE (situation → conservation gate).
**Dependency:** C-OSS-1Q (Batch 28)
**Source:** next_steps §9.3

| Step | Work | Effort | DoD | Blocked? |
|---|---|---|---|---|
| 1 | Situational tagging: tag each scored decision with regime + vol_state + hurst from `classify_regime()` | 0.5d | Every new decision carries regime metadata | NO |
| 2 | **Autonomy throttle (= C-COUPLE in OSS):** on regime break, conservation gate tightens (lower theta_min headroom), AE proposals auto-deferred, sizing paused | 2d | Replayed regime break → conservation AMBER + visible autonomy reduction | NO |
| 3a | Read-layer stratification: per-regime accuracy/IKS/conservation stats computed at read time from tagged decisions. Zero writes to `mu` | 1-2d | Per-regime stats render on Trading Performance. Supplies data C-REGIME P3 needs | NO |

**Scenarios unlocked:** TRD-S1 (regime-conditioned mirror), TRD-S3 (autonomy throttle), TRD-S4 (regime-scoped rejection). All NEAR → LIVE.
**Test target:** SDK root + Trading. 0 failures.
**Tag:** SDK v0.7.81

---

### Batch 35: C-TRD-VOL — Volatility Scenarios (3-4 days)

**Purpose:** Vol is the conservation law's natural home. Read-side analytics, no scorer change.
**Dependency:** C-OSS-1Q (Batch 28), C-TRD-SIT Step 1 (Batch 34)
**Source:** next_steps §9.4

| ID | Scenario | Effort | DoD |
|---|---|---|---|
| V1 | Clustering-adjusted Sharpe: "your measured Sharpe is a clustering artifact" | 1d | B4 inflation ratio on trader's own decision series. Day-zero when n < K |
| V2 | VRP edge-or-insurance: "is your premium capture edge or insurance?" | 1d | B7 model-free IV + B1 realized vol on trader's data. Provenance + tier tags |
| V5 | Regime-conditioned rich/cheap (upgrades T17) | 0.5d | Per-regime VRP percentile |
| V6 | Dispersion follow-rate | 0.5d | B8 implied correlation on trader's basket |
| V7 | Effective-bets-in-a-tail (upgrades T18) | 0.5d | B6 tail dependence on trader's positions |

**F-21 guard:** All illustrative magnitudes are formats, not measured results. Day-zero state when n < K.
**Test target:** SDK root + Trading. 0 failures.
**Tag:** SDK v0.7.82

---

### Batch 36: C-OSS-2 — GAE OSS Extraction (3-4 days)

**Dependency:** D1 ✅

| Item | DoD |
|---|---|
| GAE standalone: license, README, CI | Fresh-venv install works |
| Quickstart notebook | Shows centroid learning + conservation gate firing in < 5 min |
| 2-3 sample datasets | Included in repo |
| YAML DomainConfig example | User can configure their own domain |
| "Read the gate" path | Conservation gate fires visibly |

**Tag:** GAE v0.7.26

---

## Wave 4: Architecture — Regime-Indexed Judgment Memory

### Batch 37-39: C-REGIME — The 63-Site Migration (2-3 weeks, staged)

**Purpose:** Convert situation-conditioned *reporting* into situation-conditioned **judgment**. The scorer conditions on regime. Architectural answer to non-stationarity.
**Dependency:** C-TRD-SIT 3a (Batch 34)
**Source:** next_steps §9.5

| Phase | Work | Effort | DoD | Behavior change? |
|---|---|---|---|---|
| P0 | Accessor contract: `scorer.centroids(regime=...)` / `scorer.update(..., regime=...)` | 1d | Accessor defined, not yet enforced | NO |
| P1 | Indirection across 63 sites: replace all direct `mu[...]` with accessor | 3-4d | All 63 sites use accessor. Existing tests green with ZERO edits. T0 scanner enforces ARCH-20 | NO — mechanical, behavior-identical |
| P2 | Regime axis behind accessor: `mu: (K,D) → (R,K,D)` with default `GLOBAL` | 2-3d | Default GLOBAL ⇒ zero behavior change. Reversible state migration | NO — GLOBAL fallback |
| P3 | Populate in Trading only: regime-tagged decisions fill per-regime centroids | 2-3d | Trading scores differ by regime. Other copilots byte-identical (GLOBAL fallback) | YES — Trading only |
| P4 | γ>1 re-convergence under regime shift: re-init from nearest prior regime instead of cold-start | 3-5d | `math_synopsis` extension. Needs EXP-REGIME to verify | YES — Trading only |
| P5 | Roll out to remaining copilots | 2-3d | All 5 copilots regime-aware (GLOBAL default preserved for non-Trading) | Per-copilot opt-in |

**ARCH-20 rule (T0 scanner, enforced from P1):**
```
FORBIDDEN:  scorer.mu[...]  /  state["mu"][...]  /  raw centroid indexing
REQUIRED:   scorer.centroids(regime=...)  /  scorer.update(..., regime=...)
```

**Tag per phase:** SDK v0.7.83 (P1), v0.7.84 (P2), v0.7.85 (P3), v0.7.86 (P4)

---

### Batch 40: EXP-REGIME — Re-Convergence Experiment (3-5 days, after C-REGIME P4)

**Purpose:** Unlock TRD-S7 / UC-13 (the platform's strongest technical scenario). Currently ARCH → LIVE only after this experiment passes.

| Item | DoD |
|---|---|
| Pre-register success criterion | Written before running. Avoid post-hoc fitting |
| Replay real regime break (2020-03, 2022) | (a) cold-start learner vs (b) regime-indexed re-initialization |
| Measure | Post-break recovery strictly faster than cold-start on ≥2 real breaks |
| Write result into `math_synopsis` as T-A | Only then may TRD-S7 be reclassified ARCH → LIVE |

**Tag:** SDK v0.7.87

---

## Wave 5: Enterprise + Horizon

### Batch 41: C-ENT-1 — Sunk-Investment Multiplier (2-3 days)

**Purpose:** The Celonis/process-intelligence room. Our strongest enterprise wedge with previously weakest scenario support.

| Item | DoD |
|---|---|
| Real Celonis-style process export ingest | Process-mining export + EDW metadata → context graph |
| Fusion beat renders | "where → what → why → which decision" |
| **Scope guard** | Surface the decision, do NOT claim ERP write-back (roadmap, F-21) |

**Tag:** CI v0.7.7-ci, S2P v0.7.24-s2p

---

### Batch 42: Horizon (do NOT pull forward)

| ID | Item | Trigger | Effort |
|---|---|---|---|
| C-10 | Toast POS OAuth2 | Toast sandbox approved | 2-3d |
| C-11 | Second cross-copilot signal (DataOps→SOC/Trading) | After Wave 2 | 2d |
| C-12 | EU AI Act Art-12/14 governance PDF | High-risk buyer (Dec 2027) | 1-2d |
| C-13 | QBO + live Snowflake/dbt/Airflow | Per design-partner | 2-3d each |
| D5 | Cross-copilot judgment transfer | After C-REGIME P3 | ~1 week |

---


### AGE Shared-Graph Migration (July 20-25, 2026) — ALL 5 COPILOTS ON AGE

| Copilot | Graph Backend | Prefix | Active | Archived | Status |
|---|---|---|---|---|---|
| SOC | AGE (original tenant) | (none) | 4,882 | 0 | ✅ V_soc=4,862 |
| Trading | AGE (shared) | TRD- | 800 | 499 | ✅ 40/40 cycles |
| Purchasing | AGE (shared) | PUR- | 800 | 242 | ✅ 40/40 cycles |
| DataOps | AGE (shared) | DOPS- | 721 | 0 | ✅ 40/40 cycles |
| S2P | AGE (shared) | S2P- | 800 | 24,304 | ✅ 40/40 cycles |
| **Total** | | | **8,003** | **25,045** | **33,048 nodes** |

**SOC domain-scoping:** ✅ DONE (86 queries scoped, soc_decision_where(), 10 isolation tests).
**Design docs:** age_shared_graph_migration_v3_22, s2p_age_migration_v1_2, soc_domain_scoping_v1_2.


### JM v2.7 Migration Phases

| Phase | Description | Status |
|---|---|---|
| 0 | Foundation | ✅ DONE |
| 1 | Protocol v2 + SOC Inventory | ✅ DONE |
| 2 | Conformance + Factory | ✅ DONE |
| 3 | S2P AGE Migration | ✅ DONE (24K decisions) |
| 4 | SDK Copilots AGE | ✅ DONE (Trading+Purchasing+DataOps flipped) |
| 5 | SOC Domain Scoping | ✅ DONE (86 queries, 10 isolation tests) |
| **6** | **Cross-Copilot Proof** | **❌ NOT STARTED** |

**Phase 6 requires:** CONFIG-CONSOL (63 env vars → TOML), SOC-ADAPTER-V (count_verified=0 bug), OD-1 entity edges.

### Operational Gaps (Phase 6 blockers)

| ID | Item | Priority | Blocks |
|---|---|---|---|
| CONFIG-CONSOL | Graph config consolidation | P2 | **Steps 1-7 DONE. Step 8 (harden) after validation.** |
| ~~SOC-ADAPTER-V~~ | ~~SOC adapter count_verified returns 0~~ | — | **✅ RESOLVED. V=0→4,862. P1-SOC-1 closed.** |
| OD-1 | S2P entity edges (353+ deferred) | P3 | Phase 6 cross-graph discovery |
| SDK-80-SKIPS | 80 skipped SDK tests | P2 | **AUDITED: 73 AGE-gated (pass w/ AGE up), 7 feature-gated.** |
| TEST-RESTORE | 11 in-memory equivalents for guarded destructive tests | P2 | Test coverage |
| PW-SOC-DOMAIN | PW: SOC tabs show only SOC data | P2 | Demo confidence |
| PW-S2P-FLIP | PW: S2P tabs work post-AGE-flip | P2 | Demo confidence |
| AGE-INDEX-PERF | Benchmark SOC latency with Decision.domain index | P3 | Performance sign-off |

### AGE Unification — Remaining Phases

| Phase | Items | Status |
|---|---|---|
| A (Infrastructure) | A1-A4 | ✅ DONE (factory fail-closed, scorer requires store, AGE client explicit DSN) |
| B (SOC Scorer) | B0-B3 | ✅ DONE (V=0→4,862 fixed, InMemoryGraphStore default removed) |
| B (remaining) | B6-B7 | Pending |
| B' | B'1-B'2 (RL state) | Pending (P2) |
| C | C1-C12 (S2P, 15 non-unified) | Not started |
| D | D1-D14 (Trading/Purchasing/DataOps) | Not started |
| E | E1-E4 (validation + release) | Not started |

### §21 — AGE Unification Forward Queue (~55d total remaining)

**Critical path:** Fix 140 test failures → Commit A+B → B6-B7 (1d) → C1-C12 S2P (10d) → D remaining (6.5d) → E validation (5d) → 20-gate PASS → Phase 6 (10.5d)

**Immediate (in progress):**
D1+D7+D11 Trading/Purchasing/DataOps profile-aware startup (140 test failures in Codex)

**Phase B remaining (SOC cleanup, 2d):**
B6 retire legacy neo4j branch · B7 seed uses disposable graphs · B'1 PosteriorStore GraphConfig · B'2 RL engine fail-loud


**B-ADDENDUM — SOC unscoped writes/counts (P1, 2d, parallel with C7-C12):**
5 functions in SOC neo4j.py with active callers but no domain scope: create_decision_trace, create_evolution_event, get_sequence_count, get_cross_category_count, get_recent_evolution. triage.py:721-722 counts ALL domains for referral — inflates counts on shared graph. Must scope before production.
**Phase C — S2P Decision Path (largest block, ~10d):**
C1 retire direct Aura (2d) · C2 stamp domain (0.5d) · C3 govern score/outcome (1d) · C4 govern graph writes (1d) · C5 scope counts (0.5d) · C6 scope framework reads (1d) · C7 restrict Cypher explorer (0.5d) · C8 main GraphConfig (1d) · C9 shadow config (0.5d) · C10 remove empty substitution (1d) · C11 seed disposable (0.5d) · C12 supplier profile isolated (0.5d)

**Phase D remaining (~6.5d):**
D2 Trading dual_write status · D3 Trading CLI GraphConfig · D4 regime unscoped retry · D5 fail-closed routers · D8 Purchasing status · D12 DataOps context from AGE · D13 DataOps GraphConfig · D14 DataOps enrichment predicates

**Phase E — Validation + Release (5d):**
E1 comprehensive runner (13 areas + 73 AGE tests, 2d) · E2 5-domain read proof (1d) · E3 forbidden-pattern scan (1d) · E4 migration/rollback evidence (1d)

**20 production-ready gates** must pass in one comprehensive report (zero NULL-domain, V_soc stable, isolation proven, score equivalence within 1e-9, p95 ≤ 193ms, PW all 5 copilots, config negatives fail-closed, rollback works).


**C6-FUTURE — SDK framework router extraction (~2d, after E, before Phase 6):**
SOC/S2P framework_router.py copies have drifted (parameterized Cypher vs f-string, different field names). Reconcile and extract to SDK with domain constructor arg.

**DataOps DI — Shipped Aug 2 (+57 tests):**
SC-TRUST ✅ · DI-1-REMAINING ✅ · DI-5-WIRE ✅ · SC-11 ✅ · SC-12 ✅ · SC-13 ✅ · DI-TEST-ISOLATION ✅

**In flight:** SC-14+15+16 (⏳ Codex sent) · D-CEL-WIRE (📋 ready)

**Demo polish queue (~5.5d):**
DI-GOLD-FE (1w, P1 Level 6 hero) · DI-PRODUCT-FE (0.5d, P1 CDO kill-shot) · DI-SOURCE-FE (1d, P2)
DI-DIRTY-DATA-FE (0.5d fixture, P1 cold-start) · DI-CROSS-COPILOT (2d, P2) · DEMO-V22-BEATS (0.5d, P3)

**Demo-readiness: 4/8 beats PASS today.** 4 need frontend panels or fixture. ~2 weeks to all 8 PASS.
**Phase 6 — Cross-Copilot Proof (~10.5d, after E):**
TransferPattern edges (2d) · cross-domain traversal (1d) · $604K finding from live traversal (1d) · global conservation (1d) · OD-1 entity edges (2d) · PW post-flip all 5 (3d) · perf benchmark (0.5d)

**Validation coverage gaps (13 areas, ~18d):**
Domain isolation 70% · V_soc stability 35% · Full platform launch 25% · Cross-domain write safety 50% · Performance 35% · PW post-flip 0% · AGE-gated suite 65% · Destructive test safety 55% · Config completeness 55% · Recovery/rollback 20% · Data integrity 60% · Ungoverned write prevention 20% · Output equivalence 0%

### §22 — MAP Full Audit Reconciliation (August 8, 2026)

**Scope:** Every MAP item (P28-P89 + R1-R33 + supplements + infrastructure) audited against code.

**Platform state (verified August 8):**

| Repo | Tag | Tests | Skips | Failures |
|---|---|---|---|---|
| SDK root | v0.7.64 | 1,918 | 0 | 0 |
| Trading BE | — | 1,138 | 0 | 0 |
| Purchasing BE | — | 642 | 0 | 0 |
| DataOps BE | — | 261 | 0 | 0 |
| S2P BE | v0.7.17-s2p | 1,627 | 0 | 0 |
| SOC BE | v6.3+ | 2,174 | 0 | 0 |
| CI | v0.7.4-ci | 582 | 9 | 0 |
| GAE | v0.7.25 | 1,237 | 0 | 0 |
| **Total backend** | | **9,579** | **9** | **0** |
| Playwright (all) | | **957** | 1 | 0 |
| **Grand total** | | **10,536** | 10 | **0** |

**Audit totals:**

| Category | CLOSED | DROP | DEFERRED | Total |
|---|---|---|---|---|
| P-series (P28-P89) | 42 | 17 | 3 | 62 |
| R-series (R1-R33) | 30 | 3 | 0 | 33 |
| Supplements (#137-R24 etc.) | 16 | 0 | 0 | 16 |
| JM store program | 1 (P0) | 0 | 3 (P-1,P1,P2) | 4 |
| Substantiation sprint | 13 | 0 | 0 | 13 |
| Infrastructure (mypy, PW, mock, WSL2, WinError) | 7 | 0 | 0 | 7 |
| **Total** | **109** | **20** | **6** | **135** |

**DROP registry (20):** P5,P13,P19 (early) · P48,P49 (shipped differently) · P51,P56,P58,P61 (pre-check confirmed) · P64,P65 (purchasing) · P67 (UN-DROPped→shipped) · P85 (superseded by P49) · P89 (fully implemented) · R2,R3,R5 (Trading already built)

**DEFERRED (6):** P40C (execution auto-approve, safety prereqs) · P83 (promotion engine) · P39 (graph enrichment, absorbed into P44) · JM P-1,P1,P2 (store program, after P0)

**Standing rules:** 78 (verified). **Forbidden registry:** F-1 through F-27. **Canonical claims:** C-1 through C-22.
**Design decisions:** DD-1 through DD-7 (all resolved).
### Backlog: Known Issues

| ID | Priority | Description | Fix Options |
|---|---|---|---|
| BKL-1 | P3 | Purchasing score flow timeout under 4-worker contention. `flows.spec.ts:34` takes 21.8s in isolation, times out at 30s under 4 workers. Full UI flow slow (navigate→select→score→confirm→navigate→assert IKS), not the score endpoint (0.02s). Passes consistently with retry. | `@cached_static` on 15 Purchasing endpoints, or `--workers=2` for Purchasing suite |

### JM Judgment History Store Program (August 6, 2026)

| Phase | What | Effort | Status |
|---|---|---|---|
| **P0** | Fix all broken centroid history surfaces | 1-2d | **✅ SHIPPED** (all 5 copilots 200, ~2046 tests verified) |
| P-1 | Verify + freeze contracts | 1d | Next |
| P1 | Store foundation (loader, Memory, hash, warm-start, pool, txn) | 4-5d | After P-1 |
| P2 | Quality axis + centroid ablation + lineage + UI | 1-1.5w | After P1 |

### Technical Debt: NEO4J-RENAME

~700 references to "neo4j" across 150+ files in all 4 repos. Code works correctly (talks to AGE),
but naming is misleading. ~55 production code refs = HIGH risk for confusion. Fix in Program B
(store unification) when every file is touched anyway. ~2 days + full regression. Rule #78 prevents new refs.

### Pre-existing Issues

| Issue | Severity |
|---|---|
| Rule72 enforcement failure (SDK, 1 isolated test) | P2 |
| DataOps mypy 27 errors (4 files) | P2 |
| SOC AGE failures still 503 (framework_router.py) | By design |

### Retroactive Cleanup: Rule #63 + #64 (July 23, 2026)

**Priority:** After Phase 3 blockers, before Phase 4 copilot flips.
**Estimated effort:** 2-3 sessions diagnostics + 3-5 sessions fixes.

**Rule #63 — Test Double Completeness Audit:**
Mock/monkeypatch acceptable ONLY for network calls, hardware, paid services.
Everything else: test doubles must track state internally. Fix the double, not the caller.
Known issues: FakeConn (SDK), TopologyConn (SDK), FakeAGEStore (SDK), ci-platform doubles, SOC/S2P/GAE TBD.

**Rule #64 — Frontend Wiring Verification Audit:**
Every backend endpoint needs: PW spec (real backend), TS interface matching Pydantic model,
no hardcoded fixtures where live data should be, ensureArray() before .map(), null-safe rendering,
no error+data state coexistence.
Known issues: GovernanceTab dual-state, ExecutiveNarrative null crash.

**Execution order:**
1. Phase 3 blockers (#1-#3) first
2. Rule #63 scan (all repos) → fix SDK → fix CI/SOC/S2P/GAE
3. Rule #64 scan (SOC first) → fix SOC → fix Trading/Purchasing/DataOps/S2P

## Execution Timeline

```
Week 1:   B27 C-GOV (0.5-1d) + B28 3d/3e finish + B29 C-0 start
Week 2:   B29 C-0 finish + B30 C-1 preseed
Week 3:   B30.5 DPW storyboard specs + B31 heroes (C-2/C-3/C-4/C-5/S14-C)
Week 3-4: B32 Loom harness ‖ B34 C-TRD-SIT Steps 1-2 (parallel)
Week 4:   B33 OSS extraction starts ‖ B35 C-TRD-VOL V1+V2
Week 5:   B33 OSS finish + B34 C-TRD-SIT 3a + B36 GAE OSS
Week 6-8: B37-39 C-REGIME (P0→P3, staged)
Week 9:   B40 EXP-REGIME + B41 C-ENT-1
```

**Track ① (do-first):** C-GOV → done in 1 day
**Track ② (demo):** C-0 → C-1 → heroes → Loom → OSS — ~4-5 weeks
**Track ③ (trading):** C-OSS-1Q → C-TRD-SIT → C-TRD-VOL — ~2 weeks (parallel with Track ②)
**Track ④ (architecture):** C-REGIME → EXP-REGIME — ~3-4 weeks (starts after Track ③)

**Total to raise-ready (Tracks ①-③):** ~5-6 weeks
**Total including architecture (Track ④):** ~9-10 weeks

---

## Validation Gates (non-negotiable, every batch)

1. `grep "failed"` returns empty across ALL test outputs — check BEFORE `grep "passed"`
2. All affected BE suites pass (report exact counts)
3. All affected FE builds pass
4. All affected PW suites pass (report exact counts)
5. No `sample` value in headline metrics (F-26)
6. GPT-5.5 review PASS for code changes (line-by-line + architecture audit)
7. Integrity tier checks pass (T0 always, T1/T2 per path)
8. No symbols named `rl_*`/`reward_*`/`policy_*` for core learning path (F-25)
9. Legacy functions renamed with `_legacy` suffix, not deleted

---

## Document Dependency Map (per §9.0.1)

| Build item | This doc only? | Also needs |
|---|---|---|
| C-GOV, C-OSS-1Q, C-TRD-SIT, C-TRD-VOL, C-REGIME, EXP-REGIME | ✅ Yes | `ci_trading_quant.zip` for C-OSS-1Q |
| C-0 | ❌ | `product_integrity_v2.9.md` (C-0's spec IS that document) |
| C-2, C-3, C-4, C-5, C-6..C-9, C-ENT-1 | ❌ | `demo_scenarios_v2.0.md` (surface/API/caption specs) |
| C-OSS-1, C-OSS-2 | ❌ | OSS README templates |

---

*MAP v5.155 Batch Additions v2 · July 11, 2026*
*Aligned with next_steps_strategy v1.23 (four-track critical path).*
*C-VERIFY-RL resolved. C-GOV is DO-FIRST. SOC learning check in C-1.*
*Read-layer stratification confirmed. 63-site migration staged.*
*122/122 features. 9,315 tests. 0 failures. 4 tracks. ~9-10 weeks total.*

---

*MAP v5.215 · July 11, 2026 · Batch plan v2 (27-42). 4 tracks. ~9-10 weeks.*
*122 features. 27 tabs. 9,315 tests. Diagnostics resolved. C-GOV DO-FIRST.*
