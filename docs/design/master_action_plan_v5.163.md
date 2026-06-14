# Master Action Plan v5.163 — Consolidated
**Date:** June 13, 2026 · **Supersedes:** v5.162
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
| Trading BE | 727 | v0.7.0 | ✅ |
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

**Total written: 34 prompts. 7 DROPs (P5, P13, P19, P48, P49, P51, P54). P28-P30 DONE.**

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
| P40 | #135 | S2P-AUTO-APPROVE | s2p | 1-2w |
| P41 | #136 | S2P-CENTROID-EXPLORER | s2p | 1-2w |

**→ AGE SMOKE GATE: S2P full test suite with GRAPH_BACKEND=age after P41**

### Tier 2: DI + Cross-Copilot (P42-P47)

| P# | MAP# | ID | Repo | Effort |
|---|---|---|---|---|
| P42 | #64 | DI-3-NL-QUERY | SDK | 2d |
| P43 | #65 | DI-5-COMBINATION-DISCOVERY | SDK | 1.5d |
| P44 | — | DI-5-GRAPH-ENRICHMENT | SDK | 1.5d |
| P45 | #109 | TOAST-POS | SDK | 1d |
| P46 | #110 | PUR-WEEKLY-REPORT | SDK | 1d |
| P47 | — | POLARITY-FIX | cross | 0.5d |

**→ AGE SMOKE GATE: DataOps full test suite with GRAPH_BACKEND=age after P47**

### Tier 3: Trading Phase 0 — POC (P48-P53)

| P# | MAP# | ID | Effort | Key detail |
|---|---|---|---|---|
| ~~P48~~ | ~~#150~~ | ~~TRD-DOMAIN-CONFIG~~ | — | **❌ DROP** — Trading already (5,4,10)=200 live. |
| P49 | #151 | TRD-ALPACA-CONNECTOR | 2d | alpaca-py. OAuth. Paper+live. |
| P50 | #152 | TRD-YFINANCE | 1d | yfinance. Daily OHLCV. VIX. |
| ~~P51~~ | ~~#153~~ | ~~TRD-SIGNAL-FACTORS~~ | — | **❌ DROP** — All 10 factors already exist. |
| P52 | #154 | TRD-CLI-CORE | 2d | ci-trading init/import/score/trust/conservation. |
| P53 | #155 | TRD-TRUST-RADAR | 3d | F2 HERO. DK weights radar. React+D3. |

**→ AGE SMOKE GATE: Trading full test suite with GRAPH_BACKEND=age after P53**

### Tier 4: Trading Phase 1 — v1.0 (P54-P63)

| P# | MAP# | ID | Effort | Key detail |
|---|---|---|---|---|
| ~~P54~~ | ~~#156~~ | ~~TRD-REMAINING-FACTORS~~ | — | **❌ DROP** — Covered by P51 (all factors built). |
| P55 | #157 | TRD-PATTERN-DETECTOR | 1w | 5 patterns. Extends P8. |
| P56 | #158 | TRD-CONSERVATION-STRAT | 3d | Per-strategy GREEN/AMBER/RED. Paper→small→full. |
| P57 | #159 | TRD-JOURNAL | 3d | Trade log + factor scores + P&L. |
| P58 | #160 | TRD-IKS-WIRE | 0.5d | IKS wired to TradingDomainConfig. |
| P59 | #161 | TRD-IBKR | 3d | ib_insync. Trade import + historical. |
| P60 | #162 | TRD-CSV-IMPORT | 2d | Universal CSV. Flexible column mapping. |
| P61 | #163 | TRD-CLI-FULL | 3d | All commands + export/backup/restore. |
| P62 | #164 | TRD-PYPI | 2d | pip install ci-trading. |
| P63 | #165 | TRD-EVIDENCE-NL | 3d | NL templates × 5 categories. |

### Tier 5: Purchasing Product (P64-P75)

| P# | MAP# | ID | Effort | Key detail |
|---|---|---|---|---|
| P64 | #178 | PUR-SYNTH-DATA | 2d | 30 suppliers + 500 orders. |
| P65 | #179 | PUR-TENSOR-MIGRATE | 1d | (5,4,6)→(5,4,7). +price_memory_index. |
| P66 | #180 | PUR-QBO-CONNECTOR | 2w | QuickBooks Online API. OAuth 2.0. |
| P67 | #181 | PUR-FACTORS-7 | 1w | 7th factor: price_memory_index. |
| P68 | #182 | PUR-SPEND-DASH | 3d | Food cost dashboard. |
| P69 | #183 | PUR-MATCH-ENGINE | 1w | Three-way match. |
| P70 | #184 | PUR-ORDER-QUEUE | 1.5w | Smart queue + NL evidence. |
| P71 | #185 | PUR-VERIFY | 1w | Confirm/override + hash-chain. |
| P72 | #186 | PUR-CONSERVATION-FULL | 3d | Full conservation + auto-approve. |
| P73 | #187 | PUR-PAR-INTELLIGENCE | 1w | Learned par + seasonal. |
| P74 | #188 | PUR-IKS-SCORECARD | 1.5w | IKS + supplier scorecard. |
| P75 | #189 | PUR-TRUST-ANALYSIS | 1w | F11 HERO. Trust radar. |

**→ AGE SMOKE GATE: Purchasing full test suite with GRAPH_BACKEND=age after P75**

### Tier 6: Quality + Bugs (P76-P77)

| P# | MAP# | ID | Effort |
|---|---|---|---|
| P76 | #57 | CA-PROTO-4-MYPY | 3-4h |
| P77 | — | SOC-OPTION-C | 1.5d |

### Tier 7: Infrastructure (P78-P80)

| P# | MAP# | ID | Effort |
|---|---|---|---|
| P78 | B4.5 | OUTBOX-REPLAY-WORKER | 1d |
| P79 | #133 | L5-PLUS-PROOF | 0.5d |
| P80 | #87 | SDK-DOCS | 0.5d |

### Tier 8: Trading Phase 1.1 (P81-P85)

| P# | MAP# | ID | Effort | Key detail |
|---|---|---|---|---|
| P81 | #166 | TRD-REGIME-CLASSIFIER | 1w | trending/ranging/volatile. VIX + ADX. |
| P82 | #167 | TRD-REALTIME-SCORE | 2w | Pre-trade scoring. |
| P83 | #168 | TRD-PROMOTION-ENGINE | 1w | Paper→small→full. Conservation-gated. |
| P84 | #169 | TRD-AGENT-EVOLVER-FULL | 2w | Full AgentEvolver trading. |
| P85 | #170 | TRD-REGIME-RECOMMEND | 1w | RegimeRecommender. |

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

## §10 — Standing Rules (64)

Rules 1-39 from v5.142 (see prior versions for full text).

**Rule #40 (UPDATED June 9, 2026):**

| # | Rule |
|---|---|
| 40 | **Mirrored WSL2 networking split.** Database DSNs (AGE/PostgreSQL) MUST use `localhost`. HTTP calls to local uvicorn MUST use `127.0.0.1`. Never mix: localhost HTTP adds 2s IPv6 penalty, 127.0.0.1 DSN can't reach WSL2. See standing_note_localhost_vs_127001.md. |

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
| DONE | ~79 (+13 from v5.153: P28-P30, Track A, CI-MYPY, SDK 36→0, agtype normalizer) |
| Written prompts (P0-P35) | 34 (4 DROPs) |
| Active sprint (§3A) | ~10 items (C9B + campaign + hot-path) |
| Forward queue (P36-P85) | ~47 (3 DROPs: P48, P51, P54) |
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

P48: ❌ DROP (already built). P49-P53 unblocked directly.
P49-P53: No longer blocked (P48 DROP — preset live)
  → AGE SMOKE: Trading (Rule 59)

P54-P63: Depend on P49-P53 (Phase 0). P54 DROP (factors built).

P64-P65: Independent (Purchasing synth + tensor)
P66-P75: Depend on P65 (tensor migration)
  → AGE SMOKE: Purchasing (Rule 59)

P76: Independent (mypy)
P77: After L5 complete
P78-P79: After P14 (outbox table)
P80: Independent
P81-P85: Depend on P55-P63 (Trading Phase 1, P54 DROP)
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

**Connection addresses (Rule 40):**
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

*MAP v5.163 · June 13, 2026 · P36-P38 + evidence hardening DONE. S2P 1,189. Rules 63-64. Next: P39.*
*~130 active items. 64 rules. 34 prompts written. P28-P30 DONE. ~44 in forward queue.*
*Active sprint: C9B → Campaign Phase 2. Hot-Path Pkg 1 DONE.*
*AGE smoke gates at 4 tier boundaries (non-blocking).*
*Rules 58-62: no raw sqlite3 + AGE smoke + read normalization + shadow isolation + migration source.*
*Rule 40 updated: localhost for DSN, 127.0.0.1 for HTTP.*
*"All features before Loom. Docker/VPS LAST."*
