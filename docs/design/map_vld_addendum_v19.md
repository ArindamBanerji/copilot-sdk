# MAP VLD Addendum v19
**Date:** Sep 13, 2026
**Authority:** MAP v5.92 + VLD Tier 5 implementation + 23 experiments + 2 gap experiments + Q ablation (normalized)
**Purpose:** Complete VLD work plan. Supersedes v18.

---

## Current State

**Platform:** SDK v0.9.59, SOC v5.148, S2P v0.7.50-s2p. ~10,400 tests, 0 failures.
**VLD implementation:** Tier 5A (investigation pipeline) + 5B (SOC/DataOps/S2P domain wiring) complete.
**Experiments:** 23 experiments complete (21 original + Q ablation raw + Q ablation normalized). 2 gap experiments complete (adaptive halting, abstention curve). 575+ experimental cells validated.
**Paper:** ci_rgi_impact_core_v5.md (48KB). Sonnet + Fable reviews received. v6 pending.
**Core hashes:** investigation.py `3441dcdb`, investigation_router.py `08f4df7a`, scorer.py `24ac9e49`.

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

## Forward Queue (6 phases, 14 items)

### PHASE 1: Paper Fixes (parallel with Tier 5C)

| # | ID | Effort | Status | Dep |
|---|---|---|---|---|
| 1 | **PAPER-NORM** | 1h | **READY** | Q-NORM done |
| | Apply normalized Q findings to v6. Rewrite §5.1. Remove magnitude-artifact retraction. Fix σ=1.0 framing (→ §4.1 pre-compounding). Remove "honest" (7x). "Fourth engineering memory class." Soften "first system" → composition under governance. State 57:0 generator limitation. | | | |
| 2 | **PAPER-CHARTS** | 3h | READY | All experiments done |
| | Design and generate chart set. 10 candidates: (1) K-learning divergence, (2) cross-copilot K, (3) budget frontier, (4) risk-coverage, (5) RI-1 heatmap, (6) Q ablation normalized heatmap, (7) R0-R5 taxonomy, (8) budget sensitivity saves, (9) Read→Route→Reshape, (10) judgment memory artifacts. | | | |

### PHASE 2: Implementation (main track)

| # | ID | Effort | Status | Dep |
|---|---|---|---|---|
| 3 | **TIER-5C** | 5d | NEXT | Tier 5B done |
| | Trading + Purchasing domain wiring. Evidence providers for remaining factors. Campaign topology, decision attachment. Tests: ~200 per copilot. | | | |
| 4 | **TIER-5D** | 4d | BLOCKED | Tier 5C |
| | 8 missing evidence providers across Trading (6 factors) and Purchasing (3 factors). Provider coverage: Trading 40%→100%, Purchasing 57%→100%. | | | |

### PHASE 3: Paper Review + External Baseline

| # | ID | Effort | Status | Dep |
|---|---|---|---|---|
| 5 | **PAPER-ASTRA** | 1h | BLOCKED | PAPER-NORM (v6) |
| | Chat-Astra (Fable 5.1) review with full CI context. Targets: technical accuracy vs codebase, demo scenario alignment (v2.9), VLD Guard compliance (10 guards), RGI terminology (RGI_v1/v2), missing prepaper v10 results. Produces v7 fix list. | | | |
| 6 | **PAPER-EXTERNAL** | 3-5d | BLOCKED | Tier 5C/5D |
| | External baseline on 543-alert SOC fixture. Three comparators: (1) contextual bandit (same K update, no geometric Q), (2) fine-tuned RF/SVM classifier, (3) sklearn feature importance as routing. Fable's #1 gap: "no number against a non-CI system." Even if external wins on accuracy, comparison legitimizes the mechanism. | | | |

### PHASE 4: Paper Finalization

| # | ID | Effort | Status | Dep |
|---|---|---|---|---|
| 7 | **PAPER-V7** | 2h | BLOCKED | PAPER-ASTRA + PAPER-EXTERNAL |
| | Incorporate Astra fixes + external baseline results + charts. This is the submission-ready version. | | | |
| 8 | **PAPER-ABSTRACT** | 1h | BLOCKED | PAPER-V7 |
| | Write the arxiv abstract from v7. 250 words, measured claims only. | | | |

### PHASE 5: Remaining VLD Implementation

| # | ID | Effort | Status | Dep |
|---|---|---|---|---|
| 9 | **TIER-6** | 10d | BLOCKED | Tier 5D |
| | Episode lifecycle. Trajectory store. R3 cross-episode patterns. Episode snapshots in production. | | | |
| 10 | **TIER-7** | 8d | BLOCKED | Tier 6 |
| | K lifecycle. Production verified-feedback→K update path. σ learning from verified outcomes (heterogeneous σ). Conservation under aggressive learning. | | | |
| 11 | **TIER-8** | 16d | BLOCKED | Tier 7 |
| | Demo surface. 9 VLD beats + 6 Loom recordings. Investigation traces in UI. Abstention UX. | | | |

### PHASE 6: Non-VLD (parallel)

| # | ID | Effort | Status | Dep |
|---|---|---|---|---|
| 12 | **D-CEL** | 1.5d | Prompt ready | — |
| | Real SAP + Celonis. $1.62M headline. Process-Tech Fusion demo. | | | |
| 13 | **GR-01 + RL-SDK** | 5d | Processing | — |
| | GraphStore protocol + RL extraction to SDK. | | | |
| 14 | **LINKEDIN + BLOGS** | Ongoing | Active | — |
| | Content series, dakshineshwari.net posts. | | | |

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

## Key Findings (for paper and sessions)

**What works:**
- K learning compounds across all 5 copilots (+3-21%, 0 hurts)
- Static+K leads routing (60.8% vs RNN 56.6%)
- Category-conditional routing solves starvation (Trading 48%→0%)
- Three-term Q is correct (magnitude artifact resolved by normalization)
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

---

## Data Inventory (ci_core)

**Experiment JSONs:** 25 files (ri1-ri9, rv0-rv1-rv4-rv5-rv8-rv9, ke4-ke5, k_learning_curve × 2, budget_frontier, gap1, gap2, q_ablation, q_ablation_normalized)
**CSVs:** 4 files (budget_frontier, gap1, gap2, q_ablation, q_ablation_normalized)
**Reports:** 7 files (group_a_d, group_b_c, cross-copilot K, rv01, data search, gap results memo, 8-datasets memo)
**Paper versions:** v1-v5 (impact core) + v9-v10 (prepaper)
**Charts:** ~55 pub_*.png files
**Reviews:** vld_sonnet_review_1.txt, vld_v5_feedback_v1.txt

---

## Copy Script (run after each session)

```powershell
$src = "$env:CLAUDE_SDK"
$dst = "G:\My Drive\public-files\gen-ai-roi\claude_projects\design\blogs\ci_core"
$chartDst = "$dst\charts"
if (-not (Test-Path $chartDst)) { New-Item -ItemType Directory -Path $chartDst | Out-Null }

# All experiment JSONs
Copy-Item "$src\experiments\vld\*.json" "$dst\" -Force
# All CSVs
Copy-Item "$src\experiments\vld\*.csv" "$dst\" -Force
# All reports
Copy-Item "$src\experiments\vld\*report*.md" "$dst\" -Force
# All charts
Copy-Item "$src\experiments\vld\charts\pub_*.png" "$chartDst\" -Force
# Design docs
Copy-Item "$src\docs\design\vld_*.md" "$dst\" -Force
Copy-Item "$src\docs\design\ci_vld_*.md" "$dst\" -Force

# Verify
Get-ChildItem "$dst" -Filter "*.json" | Measure-Object | ForEach-Object { Write-Host "JSONs: $($_.Count)" }
Get-ChildItem "$dst" -Filter "*.csv" | Measure-Object | ForEach-Object { Write-Host "CSVs: $($_.Count)" }
Get-ChildItem "$chartDst" -Filter "pub_*" | Measure-Object | ForEach-Object { Write-Host "Charts: $($_.Count)" }
```

---

*MAP VLD Addendum v19 · Sep 13, 2026*
*25 experiments complete. 575+ cells validated. Paper v5 reviewed by Sonnet + Fable.*
*Three-term Q confirmed correct (magnitude artifact resolved).*
*Next: PAPER-NORM (v6) → TIER-5C → PAPER-EXTERNAL → arxiv.*
