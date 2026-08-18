# MAP v5.229 Addendum — Cross-Platform Gap Reconciliation

**Date:** August 18, 2026
**Authority:** MAP v5.228 + cross_platform_gap_analysis_memo_v1.md
**Status:** DRAFT — for Codex cleanup and reconciliation

---

## What this addendum does

The cross-platform gap analysis (August 16-17) scanned all 5 copilots' codebases
against their authoritative product definitions. It found 21 Codex-sized work items
not in MAP v5.228. This addendum merges those items into the MAP's track structure,
resolves overlaps, and produces a unified forward queue.

## Current state update (August 18, 2026)

| Repo | Tests | Tag | Status |
|---|---|---|---|
| SDK root | 3,007 | **v0.9.25** | ✅ |
| SOC BE | 2,274 | **v5.122** | ✅ |
| S2P BE | 1,701 | v0.7.34-s2p | ✅ |
| Trading BE | 1,243 | v0.9.25 | ✅ |
| Purchasing BE | 693 (+1 skip) | v0.9.25 | ✅ |
| DataOps BE | 289 | v0.9.25 | ✅ |
| ci-platform | 619 | v0.7.13-ci | ✅ |
| **Total** | **9,826** | | **0 failures** |

**New since v5.228:**
- Factor-0 aggregation fix shipped (v5.122 SOC): weighted mean 0.50/0.20/0.15/0.15
- RL naming fix shipped (v0.9.25 SDK)
- Factor-0 reconciliation closed (quarantine + design docs + panel data + scripts)
- Cross-platform gap analysis complete (5 copilots, 96 features, 21 work items)

---

## Overlap analysis: MAP v5.228 items vs memo items

| MAP item | Memo item | Relationship |
|---|---|---|
| C-GOV (B27) | — | **MAP-only.** Still do-first |
| C-0 (B29) | SH-01 Evidence/Claim Gate | **PARTIAL OVERLAP.** C-0 is broader (integrity scaffolding). SH-01 is the specific evidence gate service. Merge: C-0 includes SH-01 deliverable |
| C-1 (B30) | — | **MAP-only.** Demo preseed |
| C-2/3/4/5 (B31) | — | **MAP-only.** Hero moments |
| C-TRD-SIT (B34) | P0-01 SAFE-2 | **PARTIAL OVERLAP.** B34 adds situation features; P0-01 quarantines safety violations. P0-01 must precede B34 |
| C-REGIME (B37-39) | — | **MAP-only.** Architecture |
| C-ENT-1 (B41) | — | **MAP-only.** Enterprise |
| — | SH-02 Frozen Twin | **MEMO-ONLY.** Not in MAP. Highest-leverage shared build. Add as new batch |
| — | SH-03 Promotion state machine | **MEMO-ONLY.** P83 (TRD-PROMOTION-ENGINE) is Trading-only. SH-03 is cross-copilot. Supersedes P83 |
| — | SH-04 Counterfactual inspector | **MEMO-ONLY.** Extends existing SDK counterfactual |
| — | SH-05 Day-0 readiness | **MEMO-ONLY.** Extends existing SDK readiness primitives |
| — | SH-06 Verified-outcome protocol | **MEMO-ONLY.** reward_raw migration |
| — | S2P-01/02/03 (F23-F26) | **MEMO-ONLY.** v1.4 moat features not in MAP |
| — | SOC-01/02/03 (F16-F22) | **MEMO-ONLY.** v5.9 proof features not in MAP |
| — | PUR-01 (F23-F29) | **MEMO-ONLY.** v1.4 evidence features |
| — | DI-01 (evidence gates) | **MEMO-ONLY.** DataOps evidence/abstention |
| — | DEMO-01/02 | **PARTIAL OVERLAP with B31-32.** Memo demo includes hero-beat harness |
| — | PILOT-01/02 | **MEMO-ONLY.** Day-0 qualification + measured transfer |
| AGE unification (§21) | — | **MAP-only.** Memo doesn't address graph backend |
| Demo polish (§21) | — | **MAP-only.** DI-GOLD-FE, DI-PRODUCT-FE, etc. |

---

## Merged track structure (5 tracks)

### Track 0: Safety + Governance (DO-FIRST, ~3 days)

| Seq | ID | Source | Days | Dependency |
|---|---|---|---|---|
| 0.1 | C-GOV: Conservation gate unification | MAP B27 | 0.5-1 | None |
| 0.2 | P0-01: Trading SAFE-2 quarantine | Memo | 4-6 | None |
| 0.3 | P0-02: Evidence-tier inventory | Memo | 1-2 | None |

### Track 1: Shared Infrastructure (highest leverage, ~5 weeks)

| Seq | ID | Source | Days | Dependency |
|---|---|---|---|---|
| 1.1 | SH-01 + C-0: Evidence/Claim Gate + Integrity scaffolding | Merged | 6-8 | Track 0 |
| 1.2 | SH-02: Frozen Twin | Memo | 8-12 | SH-01 |
| 1.3 | SH-03: Promotion/autonomy state machine | Memo (supersedes P83) | 7-10 | SH-01 |
| 1.4 | SH-04: Counterfactual inspector | Memo | 5-7 | SH-01 |
| 1.5 | SH-05: Day-0 readiness assessment | Memo | 6-9 | SH-01 |
| 1.6 | SH-06: Verified-outcome protocol (reward migration) | Memo | 4-6 | SH-01 |

SH-02 through SH-06 can parallelize after SH-01 ships.

### Track 2: Demo + Loom (parallel with Track 1, ~4-5 weeks)

| Seq | ID | Source | Days | Dependency |
|---|---|---|---|---|
| 2.1 | C-1: Demo preseed | MAP B30 | 2-3 | SH-01 |
| 2.2 | DPW: Demo storyboard PW | MAP B30.5 | 2-3 | C-1 |
| 2.3 | Demo polish (4 remaining beats) | MAP §21 | ~10 | C-1 |
| 2.4 | C-2/3/4/5: Hero moments | MAP B31 | 5.5-6.5 | C-1 |
| 2.5 | C-6/7/8: Loom harness | MAP B32 | 5 | Heroes |
| 2.6 | DEMO-01: Hero-beat harness | Memo | 2-3 | SH-01 + C-1 |

### Track 3: Per-Copilot Moat Features (after shared infra, ~6-8 weeks)

| Seq | ID | Source | Days | Dependency |
|---|---|---|---|---|
| 3.1 | S2P-01: F23 Decision-Change Proposal | Memo | 6-8 | SH-01 |
| 3.2 | S2P-02: F24 Compounding Ledger | Memo | 7-10 | S2P-01 |
| 3.3 | S2P-03: F25 Promotion + F26 Frozen Twin wiring | Memo | 9-12 | S2P-02, SH-02, SH-03 |
| 3.4 | SOC-01: F16 Control Room + F18 Frozen Twin wiring | Memo | 8-12 | SH-02 |
| 3.5 | SOC-02: F17 Earned Autonomy + C-COUPLE veto | Memo | 6-9 | SH-03 |
| 3.6 | SOC-03: F19 No-Precedent + F20 Counterfactual | Memo | 6-9 | SH-04 |
| 3.7 | TRD-01: F16 Claim Gate + promotion safety | Memo | 7-10 | SH-01, P0-01 |
| 3.8 | PUR-01: F23-F29 proof/discovery/legal | Memo | 10-15 | SH-01, SH-02, SH-05 |
| 3.9 | DI-01: Evidence/abstain/holdout/value | Memo | 10-15 | SH-01, SH-05 |

### Track 4: Architecture + AGE (parallel, ~9-10 weeks)

| Seq | ID | Source | Days | Dependency |
|---|---|---|---|---|
| 4.1 | C-OSS-1Q: Trading quant wiring | MAP B28 | 3-5 | None |
| 4.2 | C-TRD-SIT: Situation-conditioned judgment | MAP B34 | 4 | P0-01, C-OSS-1Q |
| 4.3 | C-TRD-VOL: Volatility scenarios | MAP B35 | 3-4 | C-TRD-SIT |
| 4.4 | C-REGIME P0-P4: Regime-indexed memory | MAP B37-39 | 2-3 wks | C-TRD-SIT 3a |
| 4.5 | EXP-REGIME: Re-convergence experiment | MAP B40 | 3-5 | C-REGIME P4 |
| 4.6 | AGE unification B→C→D→E→Phase 6 | MAP §21 | ~33 | Parallel |

### Track 5: Pilot Readiness (after Track 1 + 3, ~2-4 weeks)

| Seq | ID | Source | Days | Dependency |
|---|---|---|---|---|
| 5.1 | PILOT-01: Day-0 qualification + frozen baseline | Memo | 5-8 | SH-02, SH-05, ≥1 copilot moat |
| 5.2 | PILOT-02: Measured transfer + competence | Memo | 5-8 | PILOT-01 |
| 5.3 | C-ENT-1: Sunk-investment multiplier | MAP B41 | 2-3 | Track 2 |

---

## Critical path (merged)

```
Track 0: P0-01 (SAFE-2, 4-6d) + C-GOV (1d) ────────────────────────────────────┐
Track 1: SH-01 (6-8d) → SH-02 (8-12d) ‖ SH-03 (7-10d) ‖ SH-05 (6-9d) ───────┤
Track 3: S2P-01 (6-8d) → S2P-02 (7-10d) → S2P-03 (9-12d) ────────────────────┤
Track 5: PILOT-01 (5-8d) → PILOT-02 (5-8d) ────────────────────────────────────┘

Total critical path: ~66-84 engineer-days (aligned with memo's 64-78 estimate)

Parallel:
  Track 2 (demo) runs alongside Track 1 from day 7
  Track 4 (architecture + AGE) runs independently
```

## Items retired or superseded

| Old item | Disposition | Reason |
|---|---|---|
| P83 TRD-PROMOTION-ENGINE | Superseded by SH-03 | Cross-copilot promotion replaces Trading-only |
| P85 TRD-REGIME-RECOMMEND | PRE-CHECK confirmed: superseded by P49 | Already shipped |
| MAP demo items (DI-GOLD-FE etc.) | Absorbed into Track 2 demo polish | Same work, merged sequence |

---

## CODEX CLEANUP TASK

The above is a draft. Send to Codex with this prompt to produce the final MAP addendum:

```
Read the following documents:
1. MAP v5.228 (copilot-sdk/docs/design/master_action_plan_v5.228.md)
2. cross_platform_gap_analysis_memo_v1.md (copilot-sdk/docs/design/copilot_addenda/)
3. cross_platform_execution_plan.md (copilot-sdk/docs/design/copilot_addenda/)
4. This draft addendum

Produce MAP v5.229 addendum that:
A. Updates §1 platform state to current test counts
B. Adds new MAP items for all memo work items not already in MAP
C. Resolves overlaps (C-0/SH-01, P83/SH-03, B34/P0-01)
D. Adds the 5-track merged structure to the execution timeline
E. Updates the critical path
F. Updates item count summary
G. Adds factor-0 aggregation fix to §2 DONE items
H. Does NOT change any existing DONE/CLOSED items
I. Preserves all standing rules
J. Produces a clean diff that can be applied to MAP v5.228
```
