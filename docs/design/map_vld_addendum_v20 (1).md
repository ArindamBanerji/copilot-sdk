# MAP VLD Addendum v20
**Date:** Sep 13, 2026
**Authority:** MAP v5.92 + VLD Tier 5 implementation + 25 experiments + Fable review + Astra gaps memo
**Purpose:** Complete VLD work plan. Supersedes v19.

---

## Current State

**Platform:** SDK v0.9.59, SOC v5.148, S2P v0.7.50-s2p. ~10,400 tests, 0 failures.
**VLD implementation:** Tier 5A (investigation pipeline) + 5B (SOC/DataOps/S2P domain wiring) complete.
**Experiments:** 25 complete (21 original + Q ablation raw + Q ablation normalized + GAP 1 + GAP 2). 575+ ablation cells. 115,000+ evaluation episodes validated.
**Paper:** ci_rgi_impact_core_v6.md (49KB). Sonnet + Fable + Astra reviews received. v7 pending.
**Core hashes:** investigation.py `3441dcdb`, investigation_router.py `08f4df7a`, scorer.py `24ac9e49`.
**Demo scenarios:** v2.9 (aligned with Astra feedback). 9 VLD beats defined.

---

## Experiment Inventory (25 complete)

| # | ID | Question | Verdict | Key number |
|---|---|---|---|---|
| 1 | KE-1 | Cross-copilot K curves | All 5 positive | +0.03 to +0.21, 0 hurts |
| 2 | KE-2 | Extended to 2000 | Plateau at ~500 | Starvation 19%→14% |
| 3 | KE-3 | Starvation profiles | Geometry-dependent | ρ=0.000 (5 points) |
| 4 | KE-4 | Distribution sensitivity | FRAGILE | Adversarial +0.0pp (ceiling) |
| 5 | KE-5 | Conservation × K | Inert at this scale | 10.2 blocked, no effect |
| 6 | RV-0 | GRU/LSTM ablation | Static wins | 57.8% > 56.3% > 48.8% > 47.0% |
| 7 | RV-1 | Bandit exploration | Starvation cleared, routing hurts | Trading 73.6%→53.0% |
| 8 | RV-4 | Risk-sensitive Q | DO NOT KEEP | B2 invariant; adaptive hurts |
| 9 | RV-5 | Hierarchical C4→RNN | DO NOT KEEP | C4 fallback S1/S3/S6 only |
| 10 | RV-8 | Adaptive-Q headroom | +1.4pp | Separator holds |
| 11 | RV-9 | MCTS lookahead | −31pp at 15× cost | Wrong objective at B=2 |
| 12 | RI-1 | Routing×K interaction | Static+K leads routing | 60.8% vs 56.6% |
| 13 | RI-2 | UCB sweep | Trading has no qualifying c | SOC c=0.5 best |
| 14 | RI-3 | Hybrid exploration | 4/5 pass, Trading −4.6pp | Greedy-then-explore |
| 15 | RI-4 | Cross-copilot transfer | NOT TESTABLE | Zero factor overlap |
| 16 | RI-5 | Rich K state | DO NOT KEEP globally | SOC free; Trading −5.8pp |
| 17 | RI-6 | Temporal K decay | DO NOT KEEP | All λ>0 hurt |
| 18 | RI-7 | Category-conditional | Only policy solving Trading | 74.8% / 0% starvation |
| 19 | RI-8 | Sequence-aware Q | DO NOT KEEP | SOC −14.4pp |
| 20 | RI-9 | Regime-indexed K | Validates production | Trading +9.0pp, SOC +10.4pp |
| 21 | GAP-1 | Adaptive halting | NEGATIVE | C4 can't halt before 2 reads |
| 22 | GAP-2 | Abstention curve | POSITIVE | +9.5 to +15.2pp at 75% coverage |
| 23 | Q-ABL | Q term ablation (raw) | P+L > ALL-THREE | MAGNITUDE ARTIFACT |
| 24 | Q-NORM | Q term ablation (normalized) | Three-term form correct | P+L advantage vanishes under z-norm |
| 25 | BUDGET | Budget-accuracy frontier | 80-92% at B=2 | All 5 copilots |

---

## Astra Gaps Analysis (v6→v7)

Seven gaps identified, ranked by leverage. Source: ci_rgi_impact_core_v7_gaps_memo.md.

| # | Gap | Data status | Paper action |
|---|---|---|---|
| 1 | Hero figures (divergence curve) | ✅ All JSONs exist | PAPER-CHARTS (Codex Slot 3) |
| 2 | Worked end-to-end decision | ✅ S2P-SC2 in prepaper v10 | Write from existing data |
| 3 | Competitive dismissal | ⚠️ Confirm cites current | Web search + one paragraph |
| 4 | Moat made numeric | ✅ KE-1 per-checkpoint + TTV analysis | Write from moat analysis |
| 5 | Time-to-value / cold-start | ✅ K-curve divergence + TTV analysis | Write from moat analysis |
| 6 | σ trust-traps | ✅ 63%/0FP (synthetic) | One sidebar paragraph |
| 7 | Economic logic | ✅ Innovation note + moat analysis | Logic without dollar sizing |

### Verified-Outcome Latency Estimates ($7B Industrial Manufacturer)

| Copilot | Decisions/day | Verified/week | Weeks to diverge (250) | Weeks to plateau (500) |
|---|---|---|---|---|
| SOC | 400 triaged | 1,200 | <1 | <1 |
| S2P | 108 exceptions | 486 | <1 | 1 |
| Purchasing | 66 judgment | 231 | 1 | 2-3 |
| DataOps | 25 incidents | 106 | 2-3 | 5-6 |
| Trading | 4/day (hedging) | 19 | 13 | 26 |

**Tier: ILLUSTRATIVE** — industry benchmarks, not measured at a specific firm.

### Moat Arithmetic (per-checkpoint K-curve gaps)

| Copilot | Gap at N=250 | Gap at N=500 | Moat depth |
|---|---|---|---|
| Purchasing | +15.0pp | +21.0pp | Deep (supplier-specific) |
| DataOps | +14.0pp | +19.0pp | Deep (graph complexity) |
| SOC | +12.0pp | +12.0pp | Moderate (fast but saturates) |
| Trading | +9.0pp | +12.0pp | Slow but high per-decision $ |
| S2P | −3.0pp | +3.0pp | Shallow (wedge, not moat) |

**Key insight:** S2P is the GTM wedge (fast verification, dollar-legible, shallow moat). DataOps and Purchasing are the moat domains (deep gap, supplier/graph-specific). The mechanism predicts its own commercial sequencing.

---

## Forward Queue (7 phases, 16 items)

### PHASE 1: Parallel Codex (NOW — 3 slots, zero overlap)

| # | ID | Effort | Codex slot | Repo/dir | Status |
|---|---|---|---|---|---|
| 1 | **TIER-5C** | 5d | Slot 1 | copilot-sdk/apps/{trading,purchasing}/ | SENT |
| | Trading + Purchasing VLD domain wiring. Evidence providers (10+7), investigation configs, router mounts, VLD beat tests (v2.9 alignment). ~38 new tests. | | | | |
| 2 | **D-CEL** | 1.5d | Slot 2 | copilot-sdk/apps/dataops/ (CORRECTED) | SENT |
| | Fix existing DataOps connectors: incomplete Celonis hostname, /process-data→/data endpoint, TLS cert failure. Ensure cached fallback. SAP connector gaps. ~24 new tests. | | | | |
| 3 | **PAPER-CHARTS** | 3h | Slot 3 | copilot-sdk/scripts/ + experiments/vld/paper_charts/ | SENT |
| | 8 publication charts from existing data. Hero: K-divergence curve. Also: cross-copilot K, budget frontier, risk-coverage, RI-1 heatmap, Q ablation normalized, budget sensitivity, R0-R5 taxonomy. PNG 300dpi + SVG. | | | | |

### PHASE 2: Paper v7 (after PAPER-CHARTS complete)

| # | ID | Effort | Status | Dep |
|---|---|---|---|---|
| 4 | **PAPER-V7** | 3-4h | BLOCKED | PAPER-CHARTS + Astra gaps memo |
| | **Astra gap #1:** Replace chart placeholders with figure references | | | |
| | **Astra gap #2:** S2P-SC2 worked walkthrough sidebar (from prepaper v10 K-range analysis). Factor names, v₀ values, Q ranking, evidence reads, μ-shift. Tier: PLANTED FIXTURE. | | | |
| | **Astra gap #3:** Competitive dismissal paragraph. Confirm cites: RLT 2026, 2607.07380, SIGIR'26, L2M 2510.12624. Four differentiators: no-LLM, enterprise decisions, scorer-parameter-reuse, compounding-under-conservation. | | | |
| | **Astra gap #4:** Moat arithmetic. Per-checkpoint learn-vs-frozen gaps from KE-1 (REAL_COMPONENT). Calendar conversion for $7B manufacturer (ILLUSTRATIVE). "The follower inherits the frozen line and must earn their own 500 verified decisions." | | | |
| | **Astra gap #5:** Time-to-value. 90-day deployment sequence: S2P week 1 (wedge) → SOC week 2 → DataOps week 4 → Trading month 3. The mechanism picks the GTM order. Divergence ~250, plateau ~500 (from K-curves). Calendar estimates ILLUSTRATIVE. | | | |
| | **Astra gap #6:** σ trust-trap sidebar. "63% of signal-confidence inversions surfaced, 0 FP, synthetic." One concrete example. | | | |
| | **Astra gap #7:** Economic logic. Compounding + non-transferable + first-mover = winner-take-most per firm×domain. Open-source engine = default substrate. Customer buys: factor-space design + verification-loop engineering + first 500 decisions. No dollar sizing. | | | |
| | **Astra caution carried:** S2P moat is shallow (+3pp). S2P is wedge, not moat. Say this — mechanism predicts own sequencing. All calendar conversions ILLUSTRATIVE. All K-curve gaps REAL_COMPONENT. Don't let concreteness read as production-proven. | | | |

### PHASE 3: Paper Review Round 2

| # | ID | Effort | Status | Dep |
|---|---|---|---|---|
| 5 | **PAPER-ASTRA-R2** | 1h | BLOCKED | PAPER-V7 |
| | Send v7 to Fable 5.1 (Chat-Astra) with full CI context. Review targets: technical accuracy vs codebase, demo scenario alignment (v2.9), VLD Guard compliance (10 guards), moat arithmetic plausibility, competitive dismissal accuracy. Produces v8 fix list. | | | |

### PHASE 4: Implementation continued

| # | ID | Effort | Status | Dep |
|---|---|---|---|---|
| 6 | **TIER-5D** | 4d | BLOCKED | TIER-5C |
| | 8 missing evidence providers: Trading (6 placeholder→real), Purchasing (3 placeholder→real). Provider coverage: Trading 40%→100%, Purchasing 57%→100%. After this, all 5 copilots have full provider coverage. | | | |
| 7 | **PAPER-EXTERNAL** | 3-5d | BLOCKED | TIER-5D |
| | External baseline on 543-alert SOC fixture. Three comparators: (1) contextual bandit (same K update, no geometric Q), (2) fine-tuned RF/SVM classifier, (3) sklearn feature importance as routing. Fable's #1 gap: "no number against a non-CI system." Even if an external baseline wins on accuracy, the comparison legitimizes the mechanism. | | | |

### PHASE 5: Paper Finalization

| # | ID | Effort | Status | Dep |
|---|---|---|---|---|
| 8 | **PAPER-V8** | 2h | BLOCKED | PAPER-ASTRA-R2 + PAPER-EXTERNAL |
| | Incorporate Astra R2 fixes + external baseline results. Submission-ready version. | | | |
| 9 | **PAPER-ABSTRACT** | 1h | BLOCKED | PAPER-V8 |
| | arxiv abstract. 250 words, measured claims only. | | | |

### PHASE 6: Remaining VLD Implementation

| # | ID | Effort | Status | Dep |
|---|---|---|---|---|
| 10 | **TIER-6** | 10d | BLOCKED | TIER-5D |
| | Episode lifecycle. Trajectory store. R3 cross-episode patterns. Episode snapshots in production. | | | |
| 11 | **TIER-7** | 8d | BLOCKED | TIER-6 |
| | K lifecycle. Production verified-feedback→K update path. σ learning from verified outcomes (heterogeneous σ). Conservation under aggressive learning. | | | |
| 12 | **TIER-8** | 16d | BLOCKED | TIER-7 |
| | Demo surface. 9 VLD beats (v2.9) + 6 Loom recordings. Investigation traces in UI. Abstention UX. | | | |

### PHASE 7: Non-VLD (parallel throughout)

| # | ID | Effort | Status | Dep |
|---|---|---|---|---|
| 13 | **D-CEL** | 1.5d | Codex running (corrected scope) | — |
| | Real SAP + Celonis connectors. Fix existing DataOps implementation. | | | |
| 14 | **GR-01 + RL-SDK** | 5d | Processing | — |
| | GraphStore protocol + RL extraction to SDK. | | | |
| 15 | **LINKEDIN + BLOGS** | Ongoing | Active | — |
| | Content series, dakshineshwari.net posts. | | | |
| 16 | **TIER-5C verification** | 0.5d | BLOCKED | TIER-5C Codex results |
| | Run full test suite after Codex delivers. Frontend typechecks. VLD beat alignment against v2.9 scenarios. | | | |

---

## Deferred Experiments (8)

| ID | Reason |
|---|---|
| KE-6 | Multi-copilot joint K (needs shared factors) |
| KE-7 | K under concept drift (needs Tier 7) |
| RV-2 | Attention-weighted routing (needs trained model) |
| RV-3 | RL-trained router (needs Tier 6 episodes) |
| RV-6 | Cross-episode pattern routing (needs Tier 6) |
| RV-7 | Multi-agent debate routing (needs agent infrastructure) |
| RI-10 | Operational verification quality (needs design partner) |
| RI-11 | σ learning validation (needs Tier 7) |

---

## Key Findings

**What works:**
- K learning compounds across all 5 copilots (+3-21%, 0 hurts)
- Static+K leads routing (60.8% vs RNN 56.6%)
- Category-conditional routing solves starvation (Trading 48%→0%)
- Three-term Q correct (magnitude artifact resolved by 575-cell normalization)
- Post-investigation abstention: +9.5 to +15.2pp at 75% coverage
- Budget efficiency: 80-92% of exhaustive at B=2
- 57:0 saves on constructed scenarios (+22.8pp)

**What doesn't work:**
- Adaptive halting (C4 can't halt before 2 reads)
- Temporal decay (all λ>0 hurt)
- Sequence bias (destroys SOC −14.4pp)
- MCTS lookahead (−31pp at 15× cost)
- Cross-copilot transfer (zero factor overlap)
- Risk-sensitive adaptive budget (more reads ≠ better routing)
- Naive abstention (86% abstained, worse on retained)

**What was corrected:**
- P+L > ALL-THREE was magnitude artifact (z-norm: −0.77pp)
- $0.9M/$1.62M are illustrative, not grounded
- Conservation is inert at 500-decision scale

**GTM sequencing (from mechanism, not sales):**
- S2P: wedge (fast verification, dollar-legible, shallow moat)
- SOC: expansion (fast compounding, moderate moat, highest stakes)
- DataOps: moat domain (deep gap +19pp, graph complexity)
- Purchasing: moat domain (deep gap +21pp, supplier-specific)
- Trading: long-cycle (slow but highest per-decision value)

---

## Data Inventory (ci_core)

**Experiment JSONs:** ~25 files
**CSVs:** ~5 files
**Reports:** 7 files (group_a_d, group_b_c, cross-copilot K, rv01, data search, gap results, 8-datasets)
**Paper versions:** v1-v6 (impact core) + v9-v10 (prepaper)
**Charts:** ~55 pub_*.png + paper_charts/ (after PAPER-CHARTS completes)
**Reviews:** vld_sonnet_review_1.txt, vld_v5_feedback_v1.txt, ci_rgi_impact_core_v7_gaps_memo.md
**Analysis:** moat_ttv_economics_analysis_v1.md
**Demo scenarios:** demo_scenarios_and_usecases_v2_9.md

---

## Copy Script

```powershell
$src = "$env:CLAUDE_SDK"
$dst = "G:\My Drive\public-files\gen-ai-roi\claude_projects\design\blogs\ci_core"
$chartDst = "$dst\charts"
if (-not (Test-Path $chartDst)) { New-Item -ItemType Directory -Path $chartDst | Out-Null }

# All experiment data
Copy-Item "$src\experiments\vld\*.json" "$dst\" -Force
Copy-Item "$src\experiments\vld\*.csv" "$dst\" -Force
Copy-Item "$src\experiments\vld\*report*.md" "$dst\" -Force

# All charts (existing + paper charts when ready)
Copy-Item "$src\experiments\vld\charts\pub_*.png" "$chartDst\" -Force
if (Test-Path "$src\experiments\vld\paper_charts") {
    Copy-Item "$src\experiments\vld\paper_charts\*" "$chartDst\" -Force
}

# Design docs
Copy-Item "$src\docs\design\vld_*.md" "$dst\" -Force
Copy-Item "$src\docs\design\ci_vld_*.md" "$dst\" -Force
Copy-Item "$src\docs\design\demo_scenarios_and_usecases_v2_9.md" "$dst\" -Force

# Verify
Get-ChildItem "$dst" -Filter "*.json" | Measure-Object | ForEach-Object { Write-Host "JSONs: $($_.Count)" }
Get-ChildItem "$dst" -Filter "*.csv" | Measure-Object | ForEach-Object { Write-Host "CSVs: $($_.Count)" }
Get-ChildItem "$chartDst" -Filter "*" | Measure-Object | ForEach-Object { Write-Host "Charts: $($_.Count)" }
Get-ChildItem "$dst" -Filter "*impact_core*" | Select-Object Name, Length | Format-Table
Write-Host "Done." -ForegroundColor Green
```

---

## Parallel Execution Map

```
NOW (3 Codex slots):
  Slot 1: TIER-5C ──────► copilot-sdk/apps/{trading,purchasing}/
  Slot 2: D-CEL ────────► copilot-sdk/apps/dataops/ (corrected)
  Slot 3: PAPER-CHARTS ─► copilot-sdk/scripts/ + experiments/vld/paper_charts/

CHAT (while Codex runs):
  PAPER-ASTRA-R2 prep: confirm competitive cites via web search

AFTER Codex returns:
  Verify TIER-5C ──► TIER-5D ──► PAPER-EXTERNAL
  PAPER-CHARTS ────► PAPER-V7 (incorporate Astra gaps + moat + TTV)
  PAPER-V7 ────────► PAPER-ASTRA-R2 ──► PAPER-V8 ──► ABSTRACT
```

---

*MAP VLD Addendum v20 · Sep 13, 2026*
*25 experiments complete. 575+ cells validated. Fable + Astra reviews received.*
*Three-term Q confirmed correct. Moat arithmetic grounded on $7B manufacturer.*
*S2P = wedge. DataOps/Purchasing = moat domains. Mechanism predicts GTM sequencing.*
*3 Codex prompts running parallel: TIER-5C + D-CEL + PAPER-CHARTS.*
*Next: verify Codex → PAPER-V7 (Astra gaps) → PAPER-ASTRA-R2 → PAPER-EXTERNAL → arxiv.*
