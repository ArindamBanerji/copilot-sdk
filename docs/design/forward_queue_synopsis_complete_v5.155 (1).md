# Forward Queue Synopsis — Complete (P31-P85+)
**Date:** June 12, 2026 · **Authority:** MAP v5.155
**Coverage:** 55 items (P31-P85) + 39 post-P85 detailed synopses + §3A active sprint
**DROPs:** 4 in range (P48, P49 VERIFY, P51, P54). 7 total including P5/P13/P19.
**AGE smoke gates:** 4 (after P41, P47, P53, P75)

---


---

# Forward Queue Synopsis — Part 1 of 5
## P31-P41: Remaining Written Prompts + S2P Immediate Features

---

### P31 — S2P-F10-FINANCIAL-P2 (endpoints)
**Repo:** s2p-copilot · **Effort:** 1d · **Dep:** P28 (DONE)

**What:** Add REST endpoints exposing P28's `compute_financial_impact()` to the S2P backend. Three endpoints: `/api/s2p/financial-impact` (GET, summary), `/api/s2p/financial-impact/{category}` (GET, per-category breakdown), and `/api/s2p/financial-impact/trend` (GET, time-series for dashboard charts).

**Architecture:** Endpoints go in `s2p-copilot/backend/app/routers/` as a new `financial_router.py`. Mount in `main.py`. Use Pydantic response models (Rule: frontend-consumed endpoints need `response_model`). The `FinancialSummary` dataclass from P28 becomes the response shape. Category breakdown needs the S2P 5-category taxonomy from `S2PDomainConfig`.

**Caveats:** Don't duplicate the computation — endpoints call the service. Time-series trend needs a decision window (last 30/90/180 days). The endpoint must handle zero-decision edge case (new copilot with no history). Wire into S2P frontend's Dashboard and Performance tabs.

---

### P32 — DI-1-SOURCE-PROFILER-P2 (endpoints)
**Repo:** copilot-sdk · **Effort:** 1d · **Dep:** P30 (DONE)

**What:** Add REST endpoints for the DI Source Profiler from P30. Endpoints: `/api/di/profile/{source_name}` (GET, cached profile), `/api/di/profile/{source_name}/refresh` (POST, re-run profiling), `/api/di/profiles` (GET, all source profiles summary).

**Architecture:** Create `copilot_sdk/backend/di_router.py` using `create_di_router()` factory pattern (same as `create_scoring_router()`). The router accepts a registry of `SourceConnector` instances. Each app mounts the router and registers its connectors. Profile results cached with configurable TTL.

**Caveats:** The profiler is domain-agnostic — the router should work for any copilot. Don't create per-copilot DI routers. Consistency score is still 0.5 stub (P30 documented this). Frontend integration is separate — this is API only.

---

### P33 — G12-SITUATION-P1 (foundation)
**Repo:** copilot-sdk + gen-ai-roi-demo-v4-v50 · **Effort:** 2d

**What:** Build the Situation Analyzer foundation — the component that builds bounded evidence context for NL explanations of WHY the scorer recommended an action. Phase 1: SOC domain (alert → campaign → entity → schema-change context). The S2P PD describes traversal-style procurement context for future native graph work.

**Architecture:** `SituationAnalyzer` lives in copilot-sdk (domain-agnostic traversal engine). Domain-specific traversal patterns (SOC alert chains, S2P invoice→supplier→contract) are registered via a `TraversalPattern` protocol. The analyzer takes a `decision_id`, reads the decision's graph neighborhood, and produces a structured context chain.

**Caveats:** This is the "WHY" engine — it explains scorer decisions in natural language. Must work with both SQLite and AGE backends (GraphStore protocol). SOC already has partial situation context in `triage.py` — don't duplicate, extract and generalize. The traversal depth must be bounded (max 3 hops default) to prevent runaway queries.

---

### P34 — DI-2-INTELLIGENCE-MAP (visualization)
**Repo:** copilot-sdk · **Effort:** 1.5d

**What:** Build the Intelligence Map — a visual representation of connected data sources, their quality profiles (from P30/P32), and cross-source relationships. React component showing sources as nodes, data flows as edges, quality scores as color/size.

**Architecture:** Frontend component in `copilot_sdk/frontend/`. Consumes `/api/di/profiles` endpoint from P32. Uses Recharts or D3 for the graph visualization. Each node shows source_name, trust_tier, overall_quality with color coding (green >0.8, amber >0.5, red ≤0.5). Edges show which sources feed which copilot decisions.

**Caveats:** This is a visualization component, not a backend service. Keep it lightweight — no new backend endpoints beyond P32. The consistency_score (0.5 stub) means edges won't show real cross-source agreement yet. Document this limitation in the component.

---

### P35 — G12-SITUATION-P2 (S2P + NL templates)
**Repo:** copilot-sdk + s2p-copilot · **Effort:** 2d · **Dep:** P33

**What:** Extend the Situation Analyzer with S2P-specific traversal patterns and NL evidence templates. S2P PD §M8 defines 5 evidence templates: price_variance, quantity_mismatch, duplicate_risk, contract_gap, format_compliance.

**Architecture:** Register S2P traversal patterns: invoice → supplier → contract → commodity chain. Each pattern produces a structured context that feeds into the NL template engine. Templates live in s2p-copilot (domain-specific), template engine lives in copilot-sdk (reusable).

**Caveats:** Templates must use actual scorer factors, not hardcoded values. The template should show which factors contributed most to the score (DK weights × factor values). S2P PD specifies 3 audience layers (L1 analyst, L2 manager, L3 executive) — implement L1 first, L2/L3 are v1.1.

---

### P36 — S2P-LEAD-TIME (supplier lead time learning)
**Repo:** s2p-copilot · **Effort:** 0.5d

**What:** Add lead time tracking to S2P supplier profiles. From S2P PD F14: learn actual vs stated lead times from GR/PO timestamp deltas. Per-supplier, per-category lead time distributions. Alert when actual consistently exceeds stated.

**Architecture:** Add `lead_time_days` computation to S2P's outcome processing. When a PO is received (GR), compute `actual_lead_time = gr_date - po_date`. Store as a property on the Supplier→Invoice edge or as a time-series in the supplier profile. Use rolling statistics (mean, p95) not just latest.

**Caveats:** Requires PO and GR timestamps in the decision/outcome data. If S2P synthetic data doesn't include these, extend `synthetic_invoices.json` first. The 0.5d estimate assumes data is available — if not, this becomes 1-1.5d including data generation.

---

### P37 — S2P-NL-TRUST (trust-weighted NL explanations)
**Repo:** s2p-copilot · **Effort:** 1d · **Dep:** P35 (templates)

**What:** Enhance S2P NL evidence with DK trust weights. Instead of "match_status = 0.73", show "match_status = 0.73 (trusted factor, weight 0.89)" vs "environmental_risk = 0.45 (noisy factor, weight 0.15)". The system explains WHY it trusts some factors more than others.

**Architecture:** Read DK weights from the scorer via `get_dk_weights()`. Merge with factor values in the NL template. Sort factors by contribution (weight × |value - centroid_mean|) to show most important first. S2P PD §11.1 L1 template shows the pattern.

**Caveats:** DK weights only exist after phase transition (200+ decisions per category). Before that, all factors are equally weighted — template must handle this gracefully ("System is still learning factor reliability. All factors weighted equally."). Don't crash on None DK weights.

---

### P38 — S2P-GRAPH-TRAVERSAL (graph query patterns)
**Repo:** s2p-copilot · **Effort:** 1d

**What:** Roadmap target: implement S2P-specific graph query patterns for the Situation Analyzer (P33). Current buyer-demo implementation is a read-only S2P context builder over available fixture, scorer, and GraphStore read APIs; it must not be described as native graph traversal until AGE/G12 traversal ships. Traversal-style patterns: invoice→supplier (supplier history), invoice→PO→contract (contract coverage), supplier→category→centroid (behavioral context).

**Architecture:** Define `S2PTraversalPattern` implementations that register with the Situation Analyzer. Each pattern is a parameterized Cypher query template. Use `_S()` for string serialization (AGE safety). Queries must work with both SQLite GraphStore (SQL) and AGE GraphStore (Cypher).

**Caveats:** AGE query safety rules apply (Rule #50): no MERGE, no $params, no datetime(), no CASE WHEN. For SQLite mode, traversal degrades to JOIN queries. The dual-backend requirement means each traversal pattern needs two implementations or a query abstraction layer. Consider whether GraphStore.traverse() should be a protocol method.

---

### P39 — S2P-GRAPH-ENRICHMENT (graph node enrichment)
**Repo:** s2p-copilot · **Effort:** 1d

**What:** Enrich S2P graph with computed properties from decision history. After N decisions for a supplier, compute and store: exception_rate, average_lead_time, OTIF_score, category_distribution. These become graph node properties queryable by traversal patterns.

**Architecture:** Background enrichment job (not real-time). Reads decision history from GraphStore, computes aggregates, writes enriched properties back to Supplier nodes. Idempotent — re-running produces same result. Uses GraphStore.update_node_properties() or equivalent.

**Caveats:** This is a write-back to the graph — must respect Rule #58 (GraphStore protocol only, no raw sqlite3). Enrichment must not corrupt existing node properties. Include a dry-run mode. The enrichment is periodic (e.g., after every 50 decisions), not per-decision (performance).

---

### P40 — S2P-AUTO-APPROVE (conservation-gated automation)
**Repo:** s2p-copilot · **Effort:** 1-2w

**What:** S2P PD F5: Auto-approve engine. Invoices that meet conservation-approved confidence thresholds are auto-resolved. Per-category thresholds (not global). Threshold can only lower (expand auto-approve scope) when conservation proof passes. Auto-approved decisions still write to the audit ledger. Spot-check sampling: 2% random presented for human verification.

**Architecture:** This is the biggest S2P feature. Components: (1) `AutoApproveGate` that checks confidence ≥ threshold per category, (2) conservation proof checker that validates threshold lowering, (3) spot-check sampler that randomly selects 2% for human review, (4) audit trail that marks auto-approved decisions with `source=auto_approve`. All through the existing score→learn pipeline, not a bypass.

**Caveats:** Auto-approve must NOT bypass conservation law. The penalty_ratio (5:1) means auto-approve errors are 5x more costly than manual review time. The conservation gate (α·q·V ≥ θ_min) must be GREEN before auto-approve activates for any category. This is the feature most likely to need a fixer — require old-behavior equivalence tests (auto-approve disabled = identical behavior).

---

### P41 — S2P-CENTROID-EXPLORER (visual explanation)
**Repo:** s2p-copilot + copilot-sdk · **Effort:** 1-2w

**What:** S2P PD F7: Visual explanation of WHY the system scored this way. Radar chart showing each factor's contribution. Centroid position overlay. Historical centroid drift. Factor trust weights (DK). "This invoice is closest to 'hold_for_review' because match_status is 0.73 (below centroid mean of 0.89 for auto_approve)."

**Architecture:** React component consuming scorer state via API. Endpoints: `/api/s2p/centroid/{category}/{action}` (centroid vector), `/api/s2p/dk-weights` (DK weights per category). Frontend uses Recharts radar chart. Component is reusable across copilots (parameterized by factor names).

**Caveats:** Centroid data changes with every learn() call — the visualizer must handle live updates or accept staleness. DK weights may be None before phase transition. The "why" explanation must match the actual scorer computation — don't invent a separate explanation model. Historical centroid drift requires storing centroid snapshots (L5 nodes handle this).

**→ AGE SMOKE GATE after P41: S2P full test suite with GRAPH_BACKEND=age**

---

# Forward Queue Synopsis — Part 2 of 5
## P42-P53: DI + Cross-Copilot + Trading Phase 0

---

### P42 — DI-3-NL-QUERY (natural language graph queries)
**Repo:** copilot-sdk · **Effort:** 2d

**What:** Extend the existing `NLQueryRouter` in `copilot_sdk/di/nl_query.py` with richer query patterns. Currently handles basic intent classification and query routing. P42 adds: multi-entity queries ("show me all suppliers with exception rate > 10%"), time-windowed queries ("alerts in the last 7 days"), and aggregation queries ("average lead time by category").

**Architecture:** `NLQueryRouter` already exists — extend, don't replace. Add new intent types to the classifier. Each intent maps to a parameterized GraphStore query. Results are formatted as structured responses (tables, lists, summaries). The router must work with both SQLite and AGE backends.

**Caveats:** NL parsing is pattern-based, not LLM-based (no external API calls). Keep the intent taxonomy small and explicit — 10-15 patterns max. Each pattern must have test coverage. Don't add fuzzy matching that would make behavior unpredictable. The query results must respect GraphStore protocol (Rule #58).

---

### P43 — DI-5-COMBINATION-DISCOVERY (cross-factor patterns)
**Repo:** copilot-sdk · **Effort:** 1.5d

**What:** Discover interesting factor combinations from decision history. "When signal_alignment > 0.8 AND market_regime > 0.7, the system is 94% accurate. When both are low, accuracy drops to 61%." This is data mining on the decision log, not real-time scoring.

**Architecture:** Batch analysis function that reads verified decisions from GraphStore, partitions by factor value ranges (quartiles), computes accuracy per partition, and identifies statistically significant combinations. Output is a list of `CombinationInsight` objects. No new endpoints — this feeds into the Insight tab.

**Caveats:** Must handle sparse partitions (few decisions in a combination) gracefully — require minimum sample size (e.g., 10 decisions) before reporting. Don't use floating-point equality for factor ranges — use quartile bins. The analysis is read-only and deterministic.

---

### P44 — DI-5-GRAPH-ENRICHMENT (SDK-level graph enrichment)
**Repo:** copilot-sdk · **Effort:** 1.5d

**What:** SDK-level graph enrichment framework. Counterpart to P39 (S2P-specific enrichment). Creates the base `GraphEnricher` class that copilots extend with domain-specific enrichment logic. Computes and writes derived properties back to graph nodes.

**Architecture:** `GraphEnricher` base class in `copilot_sdk/di/enrichment.py`. Protocol: `enrich(graph_store, domain) → EnrichmentReport`. Subclasses define which nodes to enrich and what properties to compute. Runs as a batch job, not per-request. Idempotent. Dry-run mode.

**Caveats:** Same as P39 — writes back to graph via GraphStore protocol only. Must not corrupt existing properties. Must work with SQLite and AGE. The enrichment schedule (when to run) is left to the caller — this is the engine, not the scheduler.

---

### P45 — TOAST-POS (Toast POS connector)
**Repo:** copilot-sdk · **Effort:** 1d

**What:** SourceConnector implementation for Toast POS system. Purchasing PD P6a: order history, covers, item velocity, webhooks. Fetches restaurant transaction data for the Purchasing copilot's factor computation.

**Architecture:** Implements the `SourceConnector` protocol (source_name, entity_type, trust_tier, fetch, validate). Lives in `copilot_sdk/connectors/toast.py`. Uses Toast API (REST). Auth via API key. Fetches: daily order summaries, item-level sales, cover counts. Validates: required fields present, amounts non-negative, dates parseable.

**Caveats:** External API dependency — must work in offline/test mode with fixture data. Create `MockToastConnector` for tests. Real API calls only in integration tests (marked with `@pytest.mark.integration`). Rate limiting must be respected. The connector produces records that Purchasing factor computers consume.

---

### P46 — PUR-WEEKLY-REPORT (automated purchasing report)
**Repo:** copilot-sdk · **Effort:** 1d

**What:** Weekly summary report for the Purchasing copilot. Covers: decisions made this week, accuracy by category, conservation status, cost impact, top supplier performance changes. Output as structured data (JSON) that the frontend renders.

**Architecture:** Report generator in `copilot_sdk/reporting/weekly.py`. Reads from GraphStore (decisions, outcomes) and scorer state (centroids, DK, conservation). Produces a `WeeklyReport` dataclass. No PDF generation — structured data only. Frontend rendering is separate.

**Caveats:** The "week" must use graph timestamps, not wall clock (Rule: production clock). Report must handle edge cases: zero decisions this week, copilot in CALIBRATING phase, conservation RED. The report is read-only — it doesn't modify state.

---

### P47 — POLARITY-FIX (cross-copilot factor polarity)
**Repo:** cross-repo · **Effort:** 0.5d

**What:** Fix factor polarity inconsistencies across copilots. Some factors have "higher is better" polarity (e.g., signal_alignment), others have "lower is better" (e.g., timing_quality where 0 = perfect timing). The scorer treats all factors as "higher distance from centroid = worse", which is correct, but the UI displays and NL templates must match the factor's natural polarity.

**Architecture:** Add `polarity` attribute to factor definitions in each preset (1 = higher is better, -1 = lower is better). NL templates and UI charts respect polarity when displaying factor values. The scorer math is unchanged — polarity only affects display/explanation.

**Caveats:** This is a display-only fix with zero impact on scoring or learning. But it affects every copilot's UI and NL templates. Requires careful audit of all 5 copilots' factor definitions. Don't change the scorer — only the interpretation layer.

**→ AGE SMOKE GATE after P47: DataOps full test suite with GRAPH_BACKEND=age**

---

### P48 — TRD-DOMAIN-CONFIG: **DROP**
**Reason:** Trading preset is already (5,4,10) with all categories, actions, and factors live. Codex built this during P20-P27. See map_v5154_correction_delta.md.

---

### P49 — TRD-ALPACA-CONNECTOR (broker API)
**Repo:** copilot-sdk · **Effort:** 2d · **Status: VERIFY — may also be done**

**What:** SourceConnector implementation for Alpaca Markets API. Paper trading + live trading. Import trade history, positions, account data. OAuth authentication. Trading PD Phase 0 POC requirement.

**Architecture:** `AlpacaConnector` in `copilot_sdk/connectors/alpaca.py`. Uses `alpaca-py` SDK. Supports paper mode (api.alpaca.markets) and live mode (api.alpaca.markets with different keys). Fetches: order history, positions, account equity. Validates: filled orders have prices, quantities match.

**Caveats:** **Pre-check required:** `dir apps\trading\backend\app\connectors\` — if alpaca connector exists, DROP. External API — needs MockAlpacaConnector for tests. Paper vs live mode via config, not code change. Must handle API rate limits (200 req/min). OAuth token refresh logic needed.

---

### P50 — TRD-YFINANCE (market data connector)
**Repo:** copilot-sdk · **Effort:** 1d

**What:** SourceConnector for Yahoo Finance data via `yfinance`. Daily OHLCV, VIX, sector indices. Feeds Trading copilot's market_regime and timing_quality factors.

**Architecture:** `YFinanceConnector` in `copilot_sdk/connectors/yfinance.py`. Fetches: daily bars (30/90/180 day windows), VIX current + historical, sector ETF performance. Caches responses (yfinance is slow and rate-limited). trust_tier=2 (market data, not authoritative for positions).

**Caveats:** yfinance is unofficial and breaks periodically. Build with graceful degradation — if yfinance fails, factor computers should use stale cache or default values, not crash. Cache TTL: 15 minutes for intraday, 24h for daily. Weekend/holiday handling: last trading day's data.

---

### P51 — TRD-SIGNAL-FACTORS: **DROP**
**Reason:** All 10 factors already exist in TradingPreset including signal_alignment, market_regime, emotional_indicator. See tensor shape verification.

---

### P52 — TRD-CLI-CORE (command-line trading tool)
**Repo:** copilot-sdk · **Effort:** 2d

**What:** CLI tool for the Trading copilot. Commands: `ci-trading init` (create home DB), `ci-trading import` (import trades from CSV/broker), `ci-trading score` (score a prospective trade), `ci-trading trust` (show DK trust weights), `ci-trading conservation` (show conservation status).

**Architecture:** Uses `click` or `argparse`. Entry point registered in `pyproject.toml`. Each command creates a scorer from the Trading preset, operates on the home DB (`~/.ci-platform/trading/trading.db`). The `score` command accepts factors as CLI args or reads from stdin (piping from data sources).

**Caveats:** The CLI must work without a running backend — it's a standalone tool. Uses SQLiteGraphStore directly (not HTTP). The `init` command must be idempotent. `import` must handle duplicate detection (same trade_id = skip, not error). Factor names must match the preset exactly.

---

### P53 — TRD-TRUST-RADAR (DK weights visualization)
**Repo:** copilot-sdk · **Effort:** 3d

**What:** Trading PD F2 HERO feature. Radar chart showing DK trust weights — which factors the system trusts most. Expected vs actual: "You think timing matters most, but the system learned that market_regime is 3x more predictive for your trading style." Interactive: click a factor to see its contribution history.

**Architecture:** React component in `copilot_sdk/frontend/` (shared, parameterized by factor names). Backend endpoint: `/api/trust-weights` returning DK weights per category. D3 or Recharts radar chart. Overlay: user-provided expected weights vs learned weights.

**Caveats:** DK weights are None before phase transition (200+ decisions). Component must show "Learning in progress — {n}/200 decisions" during Phase 1. The radar chart must handle 10 factors (Trading has 10) — visual clarity at that dimensionality needs testing. Options factors (delta, IV, gamma) may cluster — consider grouping.

**→ AGE SMOKE GATE after P53: Trading full test suite with GRAPH_BACKEND=age**

---

# Forward Queue Synopsis — Part 3 of 5
## P54-P63: Trading Phase 1 (v1.0)

---

### P54 — TRD-REMAINING-FACTORS: **DROP**
**Reason:** All 10 factors already built. position_sizing, timing_quality, risk_reward_actual, signal_confidence plus 3 options factors are all live in TradingPreset.

---

### P55 — TRD-PATTERN-DETECTOR (trade pattern recognition)
**Repo:** copilot-sdk · **Effort:** 1w

**What:** Detect 5 recurring trading patterns from decision history: (1) revenge trading (rapid re-entry after loss), (2) position sizing drift (gradually increasing size after wins), (3) FOMO entries (entries at extreme momentum), (4) averaging down (adding to losing positions), (5) style drift (category distribution shift over time).

**Architecture:** `PatternDetector` in `copilot_sdk/discovery/patterns/trading.py`. Reads verified decisions from GraphStore. Each pattern is a `DetectionRule` with a `detect(decisions) → list[PatternHit]` method. Pattern hits include: pattern_name, severity (0-1), evidence (which decisions triggered), and NL explanation.

**Caveats:** Patterns are behavioral, not market-based — they detect trader behavior, not market conditions. False positive rate matters: a pattern flagged too often gets ignored. Use minimum evidence thresholds (e.g., 3+ instances in 30 days). The detection is read-only analytics, not a gate on scoring. Extends P8's framework (DataOps pattern detection) — reuse the base class.

---

### P56 — TRD-CONSERVATION-STRAT (per-strategy conservation)
**Repo:** copilot-sdk · **Effort:** 3d

**What:** Per-category (strategy) conservation status. Instead of one global GREEN/AMBER/RED, show: "trend_following: GREEN (127 verified, q=0.82). mean_reversion: AMBER (43 verified, q=0.67). event_driven: RED (8 verified, q=0.50)." Paper→small→full promotion path per strategy.

**Architecture:** Conservation already computes per-category α (category coverage). This extends it with per-category q and V. The frontend shows a table/cards per category with status. Backend endpoint: `/api/conservation/status/by-category` returning per-category breakdown.

**Caveats:** The conservation law formula (α·q·V ≥ θ_min) uses GLOBAL α (fraction of categories with data). Per-category status is a display/operational concept, not a formula change. Don't modify the conservation math — this is a reporting layer on top. The "promotion path" (paper→small→full) is a position sizing recommendation, not a scorer gate.

---

### P57 — TRD-JOURNAL (trade journal)
**Repo:** copilot-sdk · **Effort:** 3d

**What:** Structured trade journal. Each entry: trade details (ticker, size, entry/exit), factor scores at time of trade, scorer recommendation vs actual decision, P&L outcome, post-trade reflection (free text). Historical view with search/filter.

**Architecture:** New model: `JournalEntry` stored in GraphStore (Decision node extended with journal_notes, pnl_amount, reflection). Frontend: JournalScreen with entry form + list view. Backend endpoints: POST/GET/PUT for journal entries. Connects to existing Decision nodes — not a separate data model.

**Caveats:** P&L must be optional (user may not track it initially). The journal is append-only for audit integrity — edits create new versions, not overwrites. Search must handle the free-text reflection field (simple substring, not full-text search). The journal is Trading-specific — don't generalize to SDK level yet.

---

### P58 — TRD-IKS-WIRE (IKS wiring)
**Repo:** copilot-sdk · **Effort:** 0.5d

**What:** Wire IKS (Institutional Knowledge Score) to TradingDomainConfig. IKS measures how far centroids have drifted from bootstrap — "how much has the system learned about YOUR trading?" The IKSService is domain-agnostic and already exists. This just connects it.

**Architecture:** Add IKS computation to Trading's health/status endpoint. The `IKSService` reads current centroids and bootstrap centroids, computes L2 drift normalized by D_MAX. Wire into `/api/health` response and Trading Dashboard.

**Caveats:** Tiny task — just wiring. D_MAX = 0.30 (same across copilots). Bootstrap centroids must exist in the Trading preset. If they don't, compute them from the first N decisions (deferred bootstrap). IKS = 0 at start, grows toward 100 as centroids drift.

---

### P59 — TRD-IBKR (Interactive Brokers connector)
**Repo:** copilot-sdk · **Effort:** 3d

**What:** SourceConnector for Interactive Brokers via `ib_insync`. Import trade history (executions, filled orders), current positions, historical bars. Supports paper and live accounts.

**Architecture:** `IBKRConnector` in `copilot_sdk/connectors/ibkr.py`. Uses `ib_insync` async API. TWS/Gateway must be running locally. Fetches: executions (last 7 days by default), positions, historical daily bars. Validates: execution prices > 0, quantities integer, timestamps valid.

**Caveats:** IBKR API requires TWS or IB Gateway running — connector must detect unavailability gracefully. `ib_insync` uses asyncio — may conflict with sync scorer pipeline. Use `asyncio.run()` or thread pool for fetch operations. Rate limits are strict (50 messages/sec). Include connection timeout handling. MockIBKRConnector for all tests.

---

### P60 — TRD-CSV-IMPORT (universal CSV importer)
**Repo:** copilot-sdk · **Effort:** 2d

**What:** Import trades from any CSV format. Flexible column mapping: user specifies which columns map to ticker, date, action, size, price, etc. Supports: brokerage export CSVs, custom spreadsheets, TradingView export.

**Architecture:** `CSVImporter` in `copilot_sdk/connectors/csv_import.py`. Column mapping via a `ColumnMap` config (dict of logical_name → csv_column_name). Auto-detection of common formats (Alpaca, IBKR, TradingView) via header fingerprinting. Parsed trades are converted to Decision-compatible dicts for import into GraphStore.

**Caveats:** Date parsing is the hardest part — support ISO, US (MM/DD/YYYY), European (DD/MM/YYYY), and epoch formats. Amount parsing must handle currency symbols ($, €) and thousands separators. Duplicate detection via (ticker + date + amount) hash. The importer produces decisions but does NOT call learn() — imported trades are historical, not live scoring events.

---

### P61 — TRD-CLI-FULL (complete CLI)
**Repo:** copilot-sdk · **Effort:** 3d · **Dep:** P52

**What:** Complete the Trading CLI started in P52. Add: `ci-trading export` (decisions to CSV/JSON), `ci-trading backup` (SQLite DB copy), `ci-trading restore` (from backup), `ci-trading status` (full system status), `ci-trading import-csv` (uses P60), `ci-trading import-broker` (uses P49/P59).

**Architecture:** Extends P52's click/argparse CLI. Each command is a self-contained function. Export supports multiple formats (CSV, JSON, markdown table). Backup is a file copy with timestamp. Restore validates the backup before overwriting.

**Caveats:** `restore` is destructive — require `--confirm` flag. Backup path defaults to `~/.ci-platform/trading/backups/`. Export must handle large decision counts (1000+) without memory issues — use streaming/pagination. Import commands must show progress (tqdm or simple counter).

---

### P62 — TRD-PYPI (pip-installable package)
**Repo:** copilot-sdk · **Effort:** 2d

**What:** Make the Trading copilot installable via `pip install ci-trading`. Package includes: CLI, scorer, presets, connectors, factor computers. User installs and runs `ci-trading init` to start.

**Architecture:** `pyproject.toml` with `[project.scripts]` entry point. Dependencies: copilot-sdk, ci-platform (as pip packages), yfinance, alpaca-py (optional). Namespace: `ci_trading` or `copilot_trading`. Build with `hatch` or `flit`. Publish to PyPI (or private index initially).

**Caveats:** Dependency management is the main risk. copilot-sdk and ci-platform must be pip-installable first (they already are). Optional dependencies (yfinance, alpaca-py) must not prevent installation if missing — use extras: `pip install ci-trading[alpaca]`. Test the install in a clean venv. README must include quickstart.

---

### P63 — TRD-EVIDENCE-NL (NL evidence templates for Trading)
**Repo:** copilot-sdk · **Effort:** 3d · **Dep:** P33/P35

**What:** NL evidence templates × 5 Trading categories: trend_following, mean_reversion, event_driven, income_strategy, scalp_intraday. Each template explains WHY the scorer recommended an action using the Situation Analyzer (P33) and DK trust weights.

**Architecture:** Templates in `apps/trading/backend/templates/` (or `copilot_sdk/templates/trading/`). Each template is parameterized: factor values, DK weights, centroid distances, recommended action, confidence. L1 (trader) format: "STRONG_EXECUTION recommended (87%). signal_alignment is high (0.91, weight 0.85). market_regime confirms trend (0.88). Timing is poor (0.07) but low-weighted (0.12)."

**Caveats:** Templates must be accurate — they must reflect actual scorer computation, not a simplified approximation. Factor polarity matters (P47 fixes this). Options factors (delta, IV, gamma) need trading-specific language, not generic "factor X is high." Include negative evidence: "Despite high signal, timing_quality is 0.07 — wait for better entry."

---

# Forward Queue Synopsis — Part 4 of 5
## P64-P77: Purchasing Product + Quality/Bugs

---

### P64 — PUR-SYNTH-DATA (synthetic purchasing data)
**Repo:** copilot-sdk · **Effort:** 2d

**What:** Generate 30 food-service supplier profiles and 500 demo orders. Purchasing PD P2. Suppliers represent archetypes: reliable broadliner (Sysco-like), specialty produce, local bakery, seasonal seafood, etc. Orders span 6 months with realistic patterns: seasonal variation, supplier-specific lead times, occasional stockouts.

**Architecture:** Generator script in `apps/purchasing/backend/scripts/generate_synth.py`. Output: `suppliers.json` (30 profiles with name, categories, reliability, lead_time_mean/std) and `orders.json` (500 orders with supplier_id, items, amounts, dates, delivery status). Deterministic (seeded RNG) for reproducibility.

**Caveats:** Kitchen language mandatory (Rule #57). Use food-service terms: "covers" not "customers", "par levels" not "inventory targets", "prep waste" not "shrinkage". Supplier names should be realistic but fictional. Orders must span all 5 Purchasing categories. Include edge cases: split deliveries, partial fills, credit memos.

---

### P65 — PUR-TENSOR-MIGRATE (tensor shape expansion)
**Repo:** copilot-sdk · **Effort:** 1d

**What:** Migrate Purchasing from (5,4,6) to (5,4,7). Add 7th factor: `price_memory_index` — how well the system remembers historical pricing for this item/supplier combination.

**Architecture:** Update PurchasingPreset: add factor name, update n_factors, update bootstrap centroids. Migration: existing decisions have 6-factor vectors — pad with 0.0 for the 7th factor. New decisions include all 7. The scorer handles variable-length factor vectors during transition.

**Caveats:** **Pre-check required:** verify current Purchasing tensor shape — it may have already been expanded (like Trading was). Run `PurchasingPreset().shape` before implementing. If already at (5,4,7), DROP. Existing centroid checkpoints need migration or re-bootstrap. Conservation state must be preserved across tensor change.

---

### P66 — PUR-QBO-CONNECTOR (QuickBooks Online API)
**Repo:** copilot-sdk · **Effort:** 2w

**What:** SourceConnector for QuickBooks Online. OAuth 2.0 authentication. Fetches: invoices (vendor bills), vendors (suppliers), payment history, chart of accounts. Purchasing PD P6.

**Architecture:** `QBOConnector` in `copilot_sdk/connectors/qbo.py`. Uses `python-quickbooks` or direct REST API. OAuth flow: initial authorization → access token → refresh token rotation. Fetches mapped to SourceConnector protocol: fetch(vendor_id) returns bills for that vendor. Validates: amounts match, dates valid, vendor active.

**Caveats:** OAuth is the hardest part — QBO tokens expire every 60 minutes, refresh tokens every 100 days. Need secure token storage (not in GraphStore — use keyring or encrypted config). Rate limit: 500 req/min. Sandbox mode for testing (QuickBooks Developer sandbox). This is the longest single connector — 2 weeks reflects OAuth complexity.

---

### P67 — PUR-FACTORS-7 (7 factor computers)
**Repo:** copilot-sdk · **Effort:** 1w

**What:** Implement all 7 Purchasing factor computers per PD §11.2: (1) cost_trend_alignment, (2) supplier_reliability, (3) coverage_depth, (4) par_compliance, (5) waste_risk, (6) seasonal_alignment, (7) price_memory_index.

**Architecture:** Factor computers in `apps/purchasing/backend/app/factors/`. Each implements the `FactorComputer` protocol: `compute(context) → float`. Context includes: order details, supplier history, seasonal data, inventory state. Registered in the factor registry.

**Caveats:** **Pre-check required:** some factors may already exist (like Trading's were). Check `apps/purchasing/backend/app/factors/` before implementing. Kitchen language in factor names and descriptions. par_compliance needs par level data (from P64 synth data or real Toast/QBO data). waste_risk needs prep/waste tracking (may need mock data initially).

---

### P68 — PUR-SPEND-DASH (food cost dashboard)
**Repo:** copilot-sdk · **Effort:** 3d

**What:** Purchasing PD F1: Food cost dashboard. Shows: total food cost by category (produce, protein, dairy, dry goods, beverages), cost per cover trend, supplier spend distribution, price variance alerts. Time periods: daily, weekly, monthly.

**Architecture:** Backend: `/api/purchasing/spend/summary` and `/api/purchasing/spend/by-category` endpoints. Reads from decision history + order data. Frontend: Dashboard tab in Purchasing copilot (already has a Dashboard shell). Charts: Recharts bar/line charts. Cards: total spend, cost per cover, top suppliers.

**Caveats:** "Cost per cover" requires cover count data (from Toast connector, P45). If Toast not connected, show spend only with "Connect Toast for per-cover metrics." All amounts in USD. Handle currency formatting consistently. Use the Purchasing green accent color.

---

### P69 — PUR-MATCH-ENGINE (three-way match)
**Repo:** copilot-sdk · **Effort:** 1w

**What:** Purchasing PD F2: Three-way match engine. Matches: (1) purchase order → (2) delivery receipt → (3) vendor invoice. Flags discrepancies: quantity mismatch, price variance, missing receipt, duplicate invoice. Match confidence score feeds into scoring.

**Architecture:** `MatchEngine` in `apps/purchasing/backend/app/services/match.py`. Takes order_id, finds related delivery and invoice records. Computes match_status: FULL_MATCH, PARTIAL_MATCH, MISMATCH, MISSING_COMPONENT. Match result becomes a factor input for the scorer (contributes to coverage_depth factor).

**Caveats:** Three-way match is the core AP function — errors here directly affect financial accuracy. Tolerances must be configurable: quantity ±2%, price ±1%, date ±3 days. Partial matches (2 of 3 documents) should proceed with warnings, not block. The match result is stored on the Decision node for audit.

---

### P70 — PUR-ORDER-QUEUE (smart order queue + NL evidence)
**Repo:** copilot-sdk · **Effort:** 1.5w

**What:** Purchasing PD F3+F4: Smart ordering queue with NL evidence. Prioritized list of purchasing decisions. Each shows: scorer recommendation, confidence, top 3 contributing factors, NL explanation. Queue ordered by: urgency (stockout risk), confidence (low confidence = needs human), financial impact.

**Architecture:** Backend: `/api/purchasing/queue` endpoint. Reads pending orders, scores each, sorts by priority. Frontend: Order tab (already has shell). Each queue item expandable to show full factor breakdown, similar past decisions, and NL evidence template. Uses Situation Analyzer (P33) for context.

**Caveats:** Queue must update when orders are confirmed/overridden. Don't re-score on every page load — cache with 60s TTL. NL templates must use kitchen language (Rule #57). Priority algorithm: (stockout_risk × 0.4) + (1 - confidence × 0.3) + (financial_impact × 0.3). Configurable weights.

---

### P71 — PUR-VERIFY (confirm/override + audit)
**Repo:** copilot-sdk · **Effort:** 1w

**What:** Purchasing PD F5: Confirm/override interface. User accepts or overrides scorer recommendation with a reason code. Override triggers learn() with actual_action ≠ recommended_action. Hash-chain audit trail (EvidenceLedger).

**Architecture:** Backend: POST `/api/purchasing/verify` accepting {decision_id, action, reason_code}. Calls scorer.learn(). Writes to EvidenceLedger. Frontend: Verify button on each queue item. Reason code dropdown (standard reasons: supplier preference, price override, seasonal adjustment, manager directive, other).

**Caveats:** This is the learn() trigger — it updates centroids and conservation state. Must validate that the decision_id exists and hasn't already been verified (idempotency). Reason codes must be stored on the outcome for audit. The hash-chain write must be atomic with the learn() call. Use the existing EvidenceLedger from SDK.

---

### P72 — PUR-CONSERVATION-FULL (conservation + auto-approve)
**Repo:** copilot-sdk · **Effort:** 3d

**What:** Purchasing PD F6+F7: Full conservation dashboard + auto-approve engine for Purchasing. Same pattern as P40 (S2P auto-approve) but with Purchasing-specific thresholds. penalty_ratio = 3.0 (PD-specified).

**Architecture:** Reuse S2P auto-approve architecture (P40) with Purchasing parameters. Per-category thresholds. Conservation dashboard in Performance tab. Auto-approve gate checks conservation GREEN before activating. Spot-check sampling at 2%.

**Caveats:** Purchasing penalty_ratio (3:1) is lower than S2P (5:1) and much lower than SOC (20:1). This means auto-approve can expand faster but errors are still penalized. Don't copy S2P penalty ratio — use 3.0 from PurchasingPreset. Kitchen language: "auto-ordered" not "auto-approved."

---

### P73 — PUR-PAR-INTELLIGENCE (par level learning)
**Repo:** copilot-sdk · **Effort:** 1w

**What:** Purchasing PD F8: Par level intelligence. Learn optimal par levels from consumption patterns + seasonality + waste data. "Your salmon par is set at 40 lbs but actual usage averages 32 lbs. Recommended: 35 lbs (saves $180/week, maintains 95% service level)."

**Architecture:** `ParLevelOptimizer` in `apps/purchasing/backend/app/services/par.py`. Reads: daily consumption (from Toast/POS), current par levels, waste logs, delivery schedule. Computes: recommended par by item, service level trade-off curve, seasonal adjustments. Output feeds the par_compliance factor.

**Caveats:** Seasonal adjustment requires 3+ months of data — initial recommendations should be conservative with wide confidence intervals. Service level (in-stock rate) must be explicit — "95% means 1 stockout per 20 days." Don't optimize par levels until conservation is GREEN for that category.

---

### P74 — PUR-IKS-SCORECARD (IKS + supplier scorecard)
**Repo:** copilot-sdk · **Effort:** 1.5w

**What:** Purchasing PD F9+F10: IKS display + supplier scorecard. IKS: "Your system knows 47% of your purchasing patterns." Supplier scorecard: per-supplier card showing reliability, price trend, delivery performance, exception history. "Sysco: A-tier. 94% on-time. Price trending +2.1% (above market +1.3%)."

**Architecture:** IKS: wire IKSService (same as P58 for Trading). Supplier scorecard: new endpoint `/api/purchasing/supplier/{id}/scorecard`. Reads accumulated decisions for that supplier. Frontend: Suppliers tab (or section within Inventory tab).

**Caveats:** Supplier scorecard is computed from decision history, not real-time. Cache with 5-minute TTL. Handle suppliers with few decisions gracefully ("Not enough data for reliable scoring — 3 verified decisions, need 10+"). Price trend needs historical price data (from QBO or CSV imports).

---

### P75 — PUR-TRUST-ANALYSIS (trust radar — HERO)
**Repo:** copilot-sdk · **Effort:** 1w

**What:** Purchasing PD F11 HERO feature. Same as P53 (TRD-TRUST-RADAR) but for Purchasing. Radar chart showing DK trust weights for 7 Purchasing factors. "You think cost_trend_alignment drives decisions, but the system learned that supplier_reliability is 2x more predictive."

**Architecture:** Reuse the React component from P53 (parameterized by factor names). Backend: `/api/purchasing/trust-weights`. Frontend: Analysis tab.

**Caveats:** Same as P53: DK weights may be None before phase transition. 7 factors (vs Trading's 10) makes the radar chart cleaner visually. Kitchen language in factor labels: "Freshness timing" not "seasonal_alignment."

**→ AGE SMOKE GATE after P75: Purchasing full test suite with GRAPH_BACKEND=age**

---

### P76 — CA-PROTO-4-MYPY (mypy cleanup)
**Repo:** cross-repo · **Effort:** 3-4h

**What:** Fix remaining mypy errors across platform. Focus on: ci-platform copilot_core (already fixed this session), any remaining SDK mypy targets, type stubs for external dependencies.

**Architecture:** Run `python -m mypy <target>` across all repos. Fix type annotations, add casts where needed. No `type: ignore` unless truly external (like psycopg stubs).

**Caveats:** Most copilot_core mypy issues were fixed this session (v0.7.3-ci). This is cleanup of remaining targets. The psycopg stub issue is handled by `--exclude site-packages` in test_type_checking.py. Don't break working code to satisfy mypy — prefer targeted casts.

---

### P77 — SOC-OPTION-C (SOC architectural option)
**Repo:** gen-ai-roi-demo-v4-v50 · **Effort:** 1.5d

**What:** Implement SOC "Option C" — the specific architectural choice for SOC copilot evolution. Details depend on the current design decision state. Likely involves: consolidating SOC-specific code paths into SDK-standard patterns, or implementing a specific SOC feature that was deferred.

**Architecture:** Requires Stage 1 discovery to determine current Option C scope. Read SOC design docs and MAP for context. This was likely a specific decision that was parked.

**Caveats:** SOC is the most mature copilot — changes here affect the largest test suite (1,742 tests). Any structural change needs broad regression testing. The SOC E2E suite (280 tests) must pass after this change. Don't break the demo.

---

# Forward Queue Synopsis — Part 5 of 5
## P78-P85: Infrastructure + Trading 1.1 + §3A Sprint + Post-P85

---

## P78-P80: Infrastructure

### P78 — OUTBOX-REPLAY-WORKER (event replay)
**Repo:** copilot-sdk · **Effort:** 1d · **Dep:** P14 (outbox table)

**What:** Background worker that replays outbox events. The outbox pattern stores events (decision created, outcome recorded, centroid updated) in a durable table, then a worker reads and dispatches them. This enables: reliable event delivery, replay after crashes, audit trail reconstruction.

**Architecture:** `OutboxWorker` in `copilot_sdk/outbox/worker.py`. Reads from outbox table (created in P14). Dispatches events to registered handlers. Marks events as processed. Supports: replay from offset, dead-letter for failed events, idempotent handlers.

**Caveats:** The outbox table must exist (P14 dependency). Worker must be stoppable (graceful shutdown). Event ordering must be preserved (process in outbox_id order). Idempotency: replaying the same event twice must produce same result. This is infrastructure — no copilot-specific logic.

---

### P79 — L5-PLUS-PROOF (L5 completion proof)
**Repo:** copilot-sdk · **Effort:** 0.5d

**What:** Formal proof that L5 nodes are complete: all 15 cells (C9A: 12 cells + C9B: 3 cells) verified. This is the gate for declaring the L5 schema fully operational.

**Architecture:** Verification script that queries AGE for all L5 node types (L5Centroid, L5DKWeight, L5ConservationState) and confirms: (1) all expected cells exist, (2) values are within valid ranges, (3) timestamps are sequential. Produces a proof report.

**Caveats:** C9B formal proof is in §3A (active sprint) and may ship before this prompt. If C9B is done, P79 becomes a documentation/verification wrapper. Requires AGE running with the SOC graph.

---

### P80 — SDK-DOCS (documentation)
**Repo:** copilot-sdk · **Effort:** 0.5d

**What:** SDK developer documentation. Covers: how to create a new copilot (step-by-step), GraphStore protocol, factor computers, presets, conservation law, DK weights, IKS, CLI, connectors.

**Architecture:** Markdown docs in `copilot-sdk/docs/`. Structure: getting-started.md, architecture.md, creating-a-copilot.md, graphstore.md, conservation.md, faq.md. Reference existing design docs but translate to developer-facing language.

**Caveats:** Docs must match current implementation, not design docs (implementation overrides docs rule). Include code examples that actually run. Test all code examples in a clean environment. Don't document features that aren't built yet.

---

## P81-P85: Trading Phase 1.1

### P81 — TRD-REGIME-CLASSIFIER (market regime detection)
**Repo:** copilot-sdk · **Effort:** 1w

**What:** Classify current market regime: trending, ranging, or volatile. Uses VIX level, ADX (Average Directional Index), and price momentum. The regime feeds the `market_regime` factor and affects scoring context.

**Architecture:** `RegimeClassifier` in `apps/trading/backend/app/services/regime.py`. Inputs: VIX current (from yfinance), ADX (computed from daily bars), 20-day momentum. Output: regime label + confidence. Rules: VIX > 25 → volatile, ADX > 25 → trending, else → ranging. Confidence from distance to thresholds.

**Caveats:** Regime classification is a simplification — real markets don't have clean regime boundaries. Use confidence scores, not hard labels. The classifier must handle missing data (yfinance down → use last known regime with stale=True). Update frequency: once per trading day, not per-trade.

---

### P82 — TRD-REALTIME-SCORE (pre-trade scoring)
**Repo:** copilot-sdk · **Effort:** 2w

**What:** Score a prospective trade BEFORE execution. "If I buy AAPL now, what does the system recommend?" Uses `score_read_only()` (no Decision persisted until trade is executed). Shows: recommended action, confidence, factor breakdown, similar historical trades.

**Architecture:** Backend: `/api/trading/pre-score` endpoint accepting {ticker, category, factors}. Calls `scorer.score_read_only()`. Frontend: "Score Before Trading" panel in Log Trade tab. Shows ScoreResult with factor radar overlay. Similar trades from decision history (cosine similarity on factor vectors).

**Caveats:** Pre-score is read-only — it must NOT create a Decision node. Use `score_read_only()` exclusively. Similar trade lookup needs efficient vector search (for 150-500 decisions, brute-force cosine similarity is fine). Factor values come from live market data (yfinance) + user input (position size, emotional state).

---

### P83 — TRD-PROMOTION-ENGINE (paper → live promotion)
**Repo:** copilot-sdk · **Effort:** 1w

**What:** Conservation-gated promotion path for trading strategies. A strategy starts in "paper" mode (tracked but not real money). After conservation GREEN + minimum decisions, it can be "promoted" to small size. After sustained GREEN, promoted to full size. Demotion on conservation AMBER/RED.

**Architecture:** `PromotionManager` in `apps/trading/backend/app/services/promotion.py`. States: PAPER → SMALL → FULL. Transitions gated by: conservation status (must be GREEN), minimum verified decisions (50 for SMALL, 200 for FULL), minimum accuracy (q > 0.65). Demotion: any category going RED → demote to PAPER.

**Caveats:** Promotion is advisory, not enforced — the system can't prevent the user from trading. It's a "traffic light" system. The promotion state is per-category (a trader can be FULL for trend_following but PAPER for event_driven). State persisted in GraphStore. This interacts with conservation law — don't create a parallel gate system.

---

### P84 — TRD-AGENT-EVOLVER-FULL (full AgentEvolver for Trading)
**Repo:** copilot-sdk · **Effort:** 2w

**What:** Wire the full AgentEvolver (already built for SOC) into the Trading copilot. AE generates variant scoring strategies, shadow-tests them, and promotes winners. Trading-specific variant dimensions: factor weighting adjustments, category-specific threshold tuning, regime-conditional scoring.

**Architecture:** Reuse SOC AgentEvolver infrastructure (VariantGenerator, Registry, ShadowRunner, PromotionGate). Add Trading-specific variant dimensions in `apps/trading/backend/app/ae_config.py`. AE runs in background, doesn't affect live scoring until promotion gate passes.

**Caveats:** AE must NOT mutate ProfileScorer/centroids/DK/Level 1 state (P16 separation rule). Shadow testing uses isolated scorer instances. PromotionGate requires MIN_SHADOW_BATCHES = 3 with separate batch-count gate. This is 2 weeks because Trading has 10 factors (more variant dimensions than SOC's 6).

---

### P85 — TRD-REGIME-RECOMMEND (regime-based recommendations)
**Repo:** copilot-sdk · **Effort:** 1w · **Dep:** P81

**What:** Regime-conditional trading recommendations. "In volatile regime: reduce position sizes, favor income strategies, avoid scalp_intraday." Uses the RegimeClassifier (P81) output to adjust scoring context and surface regime-appropriate strategies.

**Architecture:** `RegimeRecommender` in `apps/trading/backend/app/services/regime_recommend.py`. Maps regime → strategy preferences (weights on categories). In volatile regime: income_strategy weight ↑, scalp_intraday weight ↓. Recommendation surfaces in Dashboard and Log Trade tabs. Does NOT change the scorer — it's a UI overlay showing regime context.

**Caveats:** Regime recommendations are advisory — the scorer still computes independently. Don't modify scorer internals based on regime (that's what the trader's decisions + conservation law handle organically). The recommender must be clearly labeled as "suggestion" not "system requirement."

---

## §3A Active Sprint Items

### C9B — Formal Proof (~45min)
**Repo:** gen-ai-roi-demo-v4-v50 · **Status:** NEXT

**What:** Run the formal C9B proof on `soc_graph_c9b`. Verify all 3 C9B cells (L5DKWeight nodes for 3 specific categories). Combined with C9A's 12 cells = 15 total L5 cells complete.

**Caveats:** Requires AGE running. Read the C9B pre-hotpath baseline (F8 pass: 250/250). This is a manual verification task, not a coding prompt.

---

### Campaign Identity Phase 2 (~3d)
**Repo:** gen-ai-roi-demo-v4-v50 · **Status:** Prompt not yet written

**What:** From soc_campaign_identity_v1.3: (1) make_campaign_id() → stable identity hash with delimiter fix, (2) derived_entity_key() with type-prefix, (3) check_alert() → MERGE-based (but AGE rejects MERGE — need MATCH-then-CREATE), (4) CONTINUES edge for multi-day campaigns, (5) 13 tests.

**Architecture:** Campaign identity determines how alerts are grouped into campaigns in the graph. Current: campaign_id may drift across restarts. Fix: hash-based deterministic ID from (alert_type, entity, time_bucket_int64).

**Caveats:** Two pre-implementation fixes required from the review: (1) delimiter in hash input (item 6), (2) time_bucket as int64 (item 3). AGE rejects MERGE — the design says MERGE-based check_alert() but implementation must use MATCH-then-CREATE (proven correct by P29). This is the same pattern the migration uses.

---

## Post-P85 Long-Term Queue (Summary)

### Trading Phase 1.2 + 2.0 (MAP #171-#177)
7 items: correlation monitor, earnings subcategory, VIX timing, cross-insights, execution analysis, options factors expansion, TradingView webhook. These build on the Phase 1.1 foundation. Options factors (delta, IV, gamma) are already in the tensor at (5,4,10) — P176 may be partially done.

### Purchasing Phase 1.1 + 2.0 (MAP #190-#200)
~11 items: weather integration (OpenMetro), prep waste learning, menu engineering, event/catering, chain transfer learning, delivery coordination, predictive par, cross-category discovery, alerts, economic model, multi-unit.

### S2P Phase 1.1 + v2.0 + Phase 4 (MAP #137-#140, #201-#208)
~12 items: novelty detection, factor proposer, supplier profiles, lead time advanced, trend correlation, cross-system discovery, working capital copilot, optimizer API, disruption simulation, compliance screening, d=8 tensor expansion.

### DI Phase A-D (MAP #141-#149)
~9 items: source health monitoring, cross-source consistency, anomaly detection, automated enrichment, intelligence dashboard, pattern library, compliance checking, data lineage, quality SLA.

### Session Starters (MAP #26-#30)
5 items from early roadmap: OSS-EVOLVE, GAP-H2-DEMO, BLOCK-1.2, SOC-TAB5, F17-DISCOVERY.

### Demo Tier (#120-#127 + #88)
9 items: demo polishing, Loom recording, presentation materials.

### Docker/VPS (LAST)
2 items: DOCKER-COMPOSE + VPS-DEPLOY. Always last. All features ship before containerization.

---


---

# Part 6 (Supplementary): Post-P85 Detailed Synopses

---

## Trading Phase 1.2: Volatility Trading (~3 weeks)

### #171 — TRD-CORRELATION-MONITOR (1w)
**What:** 20-day rolling cross-position correlation matrix. Alerts when average pairwise correlation > 0.6 (diversification collapsed). Shows effective exposure multiplier: "Your 5 positions are now 1 bet. Effective exposure: 3×." Includes concentrated-position accuracy lookup from decision history.

**Architecture:** `CorrelationMonitor` service. Inputs: daily returns for open positions (from yfinance). Computes Pearson correlation matrix. Stores rolling state. Alert triggers configurable threshold. Output: `CorrelationAlert` with avg_correlation, baseline, effective_multiplier, recommendations.

**Caveat:** Requires position tracking (from Alpaca/IBKR connectors). If no positions loaded, service returns "no data." Rolling window size (20 days) must be configurable. Weekend/holiday gaps in return series must be handled.

### #172 — TRD-EARNINGS-SUBCAT (3d)
**What:** Split `event_driven` category into `event_directional` (single-leg calls/puts around earnings) vs `event_volatility` (straddles, strangles, iron condors). Per-subcategory accuracy reveals: "You're a volatility trader, not a direction trader. Straddles: 68%. Directional: 39%."

**Architecture:** Classifier function that reads trade metadata (asset_type, strategy_tag). If option + spread structure → event_volatility. If option single-leg or equity → event_directional. Subcategory stored as property on Decision node. Per-subcategory accuracy computed from decision history.

**Caveat:** Does NOT change the tensor shape — subcategories are a reporting overlay on the existing `event_driven` category. The scorer still uses 5 categories. The subcategory is metadata for display/analysis only. Requires strategy_tag in trade imports (from broker or user-tagged).

### #173 — TRD-VIX-TIMING (3d)
**What:** Per-hold-period accuracy analysis for VIX-related trades. "Your 3-day VIX hold: 71%. 1-day: 39%. Wait for confirmation." Entry timing analysis: "You enter VIX shorts too early — 44% peak accuracy."

**Architecture:** Filter decisions by VIX-related trades (category or ticker). Group by hold period (computed from entry→exit timestamps). Compute accuracy per group. Surface in Analysis tab as a hold-period chart.

**Caveat:** Requires exit timestamps on trades (not just entry). If trades don't have exits, this computes entry accuracy only. VIX-related filtering needs a clear definition (VIX ETFs? Any trade with VIX > threshold at entry?).

---

## Trading Phase 2.0: Multi-Trader + Network + Options (~10 weeks)

### #174 — TRD-CROSS-INSIGHTS (4w)
**What:** Anonymized cross-trader signal insights. Opt-in network. "RSI works for 23% of swing traders in trending markets." Proprietary tier feature. Aggregates DK weights across participating traders without revealing individual positions.

**Architecture:** Server-side aggregation service (requires cloud component — first non-self-hosted feature). Each participant uploads: anonymized DK weights, category distributions, regime accuracy. Server computes: aggregate signal effectiveness, strategy prevalence, regime-conditional patterns. Returns: community insights without individual attribution.

**Caveat:** This is the first feature requiring a server component — all prior features are self-hosted. Privacy design is critical: no position data, no P&L, no timing. Only aggregated factor weights. Opt-in only. Legal review needed for data contribution terms. Likely a v2.0+ feature.

### #175 — TRD-EXECUTION-ANALYSIS (1w)
**What:** Broker fill quality comparison. "Alpaca: avg slippage $0.12. IBKR: avg slippage $0.04. On your frequency, switching saves $1,200/year." Compares execution prices vs reference prices (mid-quote at time of order).

**Architecture:** Read executions from broker connectors (P49/P59). For each fill: compute slippage = |fill_price - mid_price|. Aggregate per broker. Compare across brokers if multiple connected. Surface in Performance tab.

**Caveat:** Requires mid-price at order time — most broker APIs don't provide this. May need to approximate from yfinance daily data (less accurate for intraday). Meaningful only with 50+ trades per broker.

### #176 — TRD-OPTIONS-FACTORS (2w)
**What:** Extended factor space for options trading. Greeks (delta, gamma, theta, vega), IV/RV ratio, spread structure, theta decay rate. Trading PD T24.

**Architecture:** Note: **The tensor is already (5,4,10) with options_delta_exposure, options_iv_percentile, and options_gamma_risk.** This prompt extends those 3 basic options factors with richer computation: true Greeks from options chain data (not just proxy values), IV/RV ratio (requires `py_vollib`), and spread-level analysis.

**Caveat:** **Pre-check:** The 3 options factors exist but may use proxy values (VIX-based) not true Greeks. This prompt upgrades proxies to real values. Requires options chain data from broker API. `py_vollib` for Black-Scholes computation. If broker doesn't provide options data, proxy values remain (graceful degradation).

### #177 — TRD-TRADINGVIEW-HOOK (1w)
**What:** TradingView webhook receiver. Captures TV alert notifications as signal events. Correlates alerts with subsequent trade execution quality. "Your RSI oversold alert → actual entry within 5 min: 72% accuracy. Entry after 30 min: 48%."

**Architecture:** FastAPI webhook endpoint: POST `/api/trading/tv-alert`. Accepts TradingView JSON payload. Stores as SignalEvent in GraphStore. Correlation engine matches signal events to subsequent decisions by (ticker, timestamp proximity). Surface in Analysis tab.

**Caveat:** TradingView sends webhooks to a URL — requires the Trading backend to be network-reachable (ngrok for local dev, or deployed). Webhook payload format varies by user configuration — need flexible parser. Rate limit webhook processing to prevent flood.

---

## Purchasing Phase 1.1: Intelligence Layer (~8 weeks)

### #190 — PUR-WEATHER (1w)
**What:** Weather API integration (OpenMetro, free). `weather_forecast` factor wired to Purchasing. Seafood/produce purchasing correlates with weather: storms delay fishing boats, heat wilts produce.

**Architecture:** `WeatherConnector` in `copilot_sdk/connectors/weather.py`. Fetches 7-day forecast for configured location(s). Factor computer: `weather_impact = f(forecast, category)`. High for seafood + storm forecast, low for dry goods + any weather.

**Caveat:** Weather is a weak signal for most categories — only meaningful for fresh produce, seafood, and dairy. Don't overweight. Factor trust (DK) should naturally learn this — weather will get high DK weight for seafood, low for dry goods.

### #191 — PUR-PREP-WASTE (1w)
**What:** Prep waste tracking and learning. "Your salmon prep waste is 18% — industry average is 12%. Recommended: switch to pre-portioned ($0.40/lb premium saves $2.10/lb in waste)."

**Architecture:** Waste data from POS (Toast) or manual entry. `WasteTracker` service computes waste rate per item per period. Feeds `waste_risk` factor. Learning: track waste rate trend over time, correlate with supplier, prep method, day of week.

**Caveat:** Waste tracking requires data input — if no POS integration and no manual entry, this feature is dormant. Provide a simple manual entry UI (item, date, waste_lbs) as fallback.

### #192 — PUR-MENU-ENGINEERING (1.5w)
**What:** Menu engineering intelligence. Correlates menu item profitability with purchasing decisions. "Your salmon entree margins dropped 8% because salmon cost rose 15%. Recommended: seasonal menu adjustment or supplier switch."

**Architecture:** Connects menu items (from Toast POS) to ingredient costs (from purchasing decisions). Computes: food cost %, margin per item, contribution margin. Identifies: stars (high popularity + high margin), puzzles (high popularity + low margin), dogs (low both).

**Caveat:** Requires both POS data (menu sales) and purchasing data (ingredient costs). Recipe-to-ingredient mapping is needed — this is complex (one menu item = multiple ingredients from multiple suppliers). Start with a simplified mapping (ingredient categories, not exact recipes).

### #193 — PUR-EVENT-CATERING (1w)
**What:** Event and catering purchase planning. "Friday catering for 80 people: suggested order: 10 lbs chicken, 15 lbs salmon, 20 lbs vegetables. Based on similar events: expected waste 8%, confidence 76%."

**Architecture:** Event template system with learned adjustments. Templates: per-person quantities by cuisine type. Learning: after each event, compare ordered vs consumed. Adjust templates over time. Surface in Order tab as "Event Mode."

**Caveat:** Catering is episodic — few events per month. Learning requires many events to be statistically meaningful. Use strong priors (industry standards) with slow Bayesian updates.

### #194 — PUR-CHAIN-TRANSFER (2w)
**What:** Chain learning transfer. Multi-unit restaurant group: "Location A learned salmon ordering patterns from 500 decisions. Transfer to Location B (new opening) for immediate 73% accuracy."

**Architecture:** This is the cross-copilot transfer mechanism applied to Purchasing. Transfer centroid state from source location to target. Conservation law gates the transfer — source must be GREEN. Target starts with transferred centroids as bootstrap, then learns its own adjustments.

**Caveat:** Transfer assumes similar menus and suppliers — may not hold across different cuisine types. Transfer is one-directional (source → target). The target's conservation resets after transfer (it hasn't verified these centroids locally yet). This is a v2.0 feature requiring multi-tenant architecture.

### #195-#200 — PUR-DELIVERY, PUR-PREDICTIVE, PUR-DISCOVERY, PUR-ALERTS, PUR-ECON, PUR-MULTI
6 additional items covering: delivery coordination with suppliers, predictive par levels, cross-category discovery, automated alerts, economic model validation, and multi-unit management. These build on Phase 1.1 foundation and are well-specified in Purchasing PD v1.3 Appendix A.

---

## S2P Phase 1.1 + v2.0 + Phase 4 (~20 weeks total)

### #137 — S2P-NOVELTY-DETECTION (1-2w)
**What:** S2P PD F6: Monitor incoming decision patterns against learned distributions. When novelty rate > 20% of recent decisions → alert AP director + conservation review + auto AMBER on affected categories. "Last novelty spike was March 2026 (tariff shock). System paused electronics for 3 days."

**Architecture:** `NoveltyTracker` from framework v4. Per-category novelty rate = fraction of recent decisions where factor vector distance from nearest centroid > threshold. Rolling window (100 decisions). Alert pipeline.

**Caveat:** Novelty threshold must be calibrated per-category (some categories are naturally more variable). Too sensitive = alert fatigue. Too loose = misses real distribution shifts. Start conservative (threshold = 2σ from centroid).

### #138 — S2P-FACTOR-PROPOSER (1-2w)
**What:** S2P PD F8: Periodic analysis evaluating each factor's contribution. "Your environmental_risk factor contributes 3% of signal. Replace with tariff_exposure for estimated +4pp accuracy."

**Architecture:** Analyze DK weights × factor value variance × outcome correlation. Factors with consistently low DK weight AND low outcome correlation are candidates for replacement. Produce recommendations. Accept/reject interface.

**Caveat:** Factor replacement changes the tensor shape — requires careful migration (new centroid dimension, old data padded). Don't auto-replace — always human decision. This is analytics/recommendation only.

### #139-#140, #201-#208 — S2P Extended Features
~10 items covering: supplier behavioral profiles (F13), lead time advanced (F14), trend correlation (F15), clustering (F16), cross-system discovery (F17), process-tech fusion (F18), working capital copilot (F19), centroid-to-optimizer API (F20), disruption simulation (F21), compliance screening (F22). All well-specified in S2P PD v1.3 §PD5 with engineering estimates.

**Key architectural note for F19-F22:** These create NEW copilot personalities (Working Capital, Compliance Sentinel) that are separate from the Invoice Exception copilot. They share the conservation law and CompoundingScorer infrastructure but have their own tensor shapes, factor sets, and penalty ratios.

---

## DI Phase A-D: Data Intelligence (~15 weeks)

### DI-1 — SOURCE-PROFILER (2w) — P30 DONE (foundation only)
**What:** Per-source, per-column reliability profiles from DK weights. P30 built the foundation (BaseSourceProfiler, SourceProfile, ProfileConfig). DI-1 extends with: ColumnProfile (per-column trust from factor decomposition), ConsumerProfile (per-consumer data quality), 6 new API endpoints, Trust API for external agents.

**Architecture:** Extends P30's models with `ColumnProfile` (column_name, null_rate, distinct_count, dk_weight_contribution). Maps factors to source columns via `factor_to_source_map`. DK weight propagates to input columns. DataOps design v1.6 §40.1 has full spec.

### DI-2 — INTELLIGENCE-MAP-V1 (2w)
**What:** Force-directed graph visualization. Nodes = data sources (brightness = DK trust weight). Lines = discovered correlations. React + D3. WebSocket for real-time pulsing when centroids update. "Day 1 → Month 12" animation showing trust evolution.

**Architecture:** DataOps design v1.6 §40.4. Node brightness from DiagonalKernel weights. Node size from data volume. Line thickness from cross-graph attention scores. Gold dotted lines = suggested new connections (from DI-5). Pulsing from learn() WebSocket events.

### DI-3 — NL-QUERY-ENGINE (3w)
**What:** Quality-aware NL answers. "$4.2M (confidence 94%). SAP: 99% reliable. Salesforce: 87%. Data as of 2 hours ago." Pipeline: classify intent → generate SQL (Claude API or local LLM) → execute → enrich (source attribution + reliability + confidence + freshness + anomaly context) → respond.

**Architecture:** DataOps design v1.6 §40.2. Confidence = weighted average of source trust scores. Adjustments: -5% if AMBER alert, -10% if stale > 24h. Flag if sources disagree > 5%.

**Caveat:** SQL generation from NL is the hardest part. Start with template-based (not LLM-generated) for safety. LLM-generated SQL must be sandboxed (read-only, timeout, row limit).

### DI-4 — PROMPT-INTEGRATOR (1w)
**What:** "Connect my QuickBooks to my spreadsheet." Auto-discover join keys (fuzzy match). Per-source trust weights on combined view. Quality annotations per field. Suggest improvements after 100 verified uses.

### DI-5 — COMBINATION-DISCOVERY (3w)
**What:** Cross-graph sweeps for value-creating data combinations. Internal pairs: Pearson/Spearman correlation between factors from source A and outcomes involving source B. If |r| > 0.3, p < 0.05 → candidate. External: residual analysis reveals what additional data would help. Rank by ROI.

**Architecture:** DataOps design v1.6 §40.3. `CombinationCandidate` dataclass: sources, correlation, p_value, estimated_improvement_pp, estimated_annual_value. External catalog: weather, commodity, industry benchmarks.

### DI-6 — DATA-VALUATION (2w)
**What:** Dollar values on discovered combinations. improvement_pp × decisions/year × avg_decision_value. Gold lines on Intelligence Map with $ labels.

### DI-7 — INTELLIGENCE-MAP-V2 (1w)
**What:** Extends DI-2 with: gold dotted lines (suggestions with $ labels), per-product IKS badges, cluster grouping by domain.

### DI-8 — ACQUISITION-ADVISOR (2w)
**What:** "What external data should I buy?" Ranked by ROI. External data catalog integration. Also: data monetization discovery — "Your learned supplier profiles outperform D&B — licensing opportunity."

### DI-9 — SNOWFLAKE-META (1w)
**What:** Snowflake metadata connector. Table stats, column profiles, query history. Feeds Source Profiler node size + NL engine SQL generation.

### DI-10 — DBT-CONNECTOR (1w)
**What:** dbt model run history + test results → intelligence graph. Each dbt model becomes a node in Intelligence Map.

### DI-11 — AIRFLOW-CONNECTOR (1w)
**What:** DAG execution history → pipeline intelligence. Run durations, failure rates, scheduling patterns.

---

## Session Starters (#26-#30)

### #26 — OSS-EVOLVE (2-3d)
**What:** CompoundingScorer with `evolve=True`. The scorer can propose its own parameter adjustments (learning rate, penalty ratio) based on accumulated evidence. Conservation law gates all changes.

**Caveat:** This is an advanced self-tuning feature. Must be conservation-bounded — the scorer cannot evolve past its safety constraints. Requires extensive testing with adversarial scenarios (what if it evolves toward always-approve?).

### #27 — GAP-H2-DEMO (3-5d)
**What:** Cross-copilot transfer demo. "SOC learned a pattern from 2,000 alerts. Transfer to DataOps. DataOps immediately recognizes similar schema change patterns." Uses graph attention to find transferable learned patterns.

**Caveat:** Transfer must respect domain boundaries — not all SOC patterns apply to DataOps. Conservation law on the target copilot resets after transfer. This is a demo/proof-of-concept, not production transfer.

### #28 — BLOCK-1.2 (1w)
**What:** Industry archetype generator. Pre-built centroid configurations for specific industries: "Healthcare SOC," "Financial Services SOC," "Retail DataOps." Enables faster onboarding — start from industry-specific bootstrap instead of generic.

### #29 — SOC-TAB5 (2d)
**What:** Executive learning narrative tab for SOC. Summary for CISOs: "Your SOC has processed 12,847 alerts. System accuracy: 84%. Auto-resolved: 2,341 (saved 487 analyst hours). Top learning: credential_access accuracy improved 23% in 90 days."

### #30 — F17-DISCOVERY (3d)
**What:** Cross-system shadow alerts for S2P. "Invoice from Supplier X flagged. Shadow alert: same supplier's OTIF declined 15% in DataOps. Cross-system correlation: 0.73." Discovers patterns that span copilot boundaries.

---

## Demo Tier (#120-#127 + #88)

### #88 — LOOM-V1 (2d)
**What:** Record the 5-act Process-Tech Fusion demo. "Three enterprise systems, one graph." ~8 minutes. Uses all built components: D-CEL connectors, BottleneckPanel, SchemaImpactPanel, WhatIfReordering, Score→Learn→Conservation flow.

### #120-#127 — Demo Polish (varies)
8 items covering: demo script refinement, tab content verification, screenshot capture, presentation materials, competitive positioning slides, customer-facing documentation, landing page content, video production.

**Caveat:** Loom is LAST in the feature queue (before Docker/VPS only). All features ship first. Every session that promoted Loom had to revert.

---

## Docker/VPS (ALWAYS LAST)

### DOCKER-COMPOSE (1.5d)
**What:** Docker Compose configuration for the full platform. All 5 copilots + AGE/PostgreSQL + frontend builds. Single `docker compose up` starts everything.

**Architecture:** Multi-service compose: postgres-age (with AGE extension), soc-backend, s2p-backend, trading-backend, purchasing-backend, dataops-backend, frontend (multi-app Vite build). Volumes for persistent data. Network for inter-service communication.

### VPS-DEPLOY (1w)
**What:** Deploy to a VPS (DigitalOcean/Hetzner). Includes: SSL, domain, reverse proxy (nginx/caddy), systemd services, backup cron, monitoring.

**Caveat:** First external deployment. Security review needed: CORS, auth, rate limiting, data encryption at rest. Currently everything runs on localhost — external deployment requires authentication layer.

---

## Cross-Reference: AGE Smoke Gates

| Gate | After | Copilot | Rule |
|---|---|---|---|
| 1 | P41 | S2P | Full test suite with GRAPH_BACKEND=age |
| 2 | P47 | DataOps | Full test suite with GRAPH_BACKEND=age |
| 3 | P53 | Trading | Full test suite with GRAPH_BACKEND=age |
| 4 | P75 | Purchasing | Full test suite with GRAPH_BACKEND=age |

Gates are **non-blocking** for features (Rule #59). Failures generate migration-fix prompts but don't stop feature shipping.

---

## Cross-Reference: DROPs (7 total)

| P# | Reason |
|---|---|
| P5 | Dropped in original batch |
| P13 | Dropped in original batch |
| P19 | Dropped in original batch |
| P48 | Trading tensor already (5,4,10) |
| P49 | VERIFY — may be done |
| P51 | All 10 Trading factors built |
| P54 | Covered by P51 (same factors) |
