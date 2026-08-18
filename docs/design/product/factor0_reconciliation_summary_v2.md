# Factor-0 Reconciliation — Summary Note

**Date:** August 17, 2026
**Status:** CLOSED — aggregation fix shipped, centroid migration deferred to pilot data
**Authority:** factor0_migration_design_v2.md (CONDITIONAL decision)

---

## 1. What this was about

Factor-0 in the SOC copilot changed from `travel_match` (does the user
have a travel record explaining their location) to `privileged_identity_context`
(user risk score, account title, MFA status, device fingerprint binding).
The factor computer changed but the 36 evaluation scenarios and 24 bootstrap
centroid priors still contained travel-derived values.

Two questions: (1) should we replace the stale scenario/centroid values now,
or defer until real identity data arrives from a pilot? (2) does the factor
computer itself have a correctness defect?

## 2. What we did

### Phase 1: Inventory and architecture (committed)

- 551 references across 132 files inventoried
- Architectural decision B/B/B: defer values, mark STALE, keep aliases with deprecation
- 36 scenarios quarantined with `factor_0_semantic_version: "travel_match_v1"`
- Centroid comments marked STALE
- 2 quarantine tests added

### Phase 2: Failed migration attempt (reverted)

Applied single-model identity values to scenarios and centroids. Caused 4 failures:

| Failure | Root cause |
|---|---|
| IKS 93 → 51 | Centroid change vs frozen anchor creates artificial drift |
| C9B confidence 0.617 < 0.62 | Centroid geometry shifted across routing threshold |
| Low-confidence companion 0.73 > 0.62 | Inverted referral routing |
| IKS sidecar mismatch | 21/144 values changed without anchor update |

**Critical finding:** Factor-0 contributes >60% of L2 scoring distance in
22/36 scenarios, >90% in 6. It is the dominant scoring dimension.
Scenarios and centroids are atomically coupled.

### Phase 3: Multi-model panel (v3 two-arm design)

Designed with iterative review from GPT-5.6, Opus 5, and Gemini/Sonnet:

- **Arm A** (label-visible): 3 models author identity context knowing the disposition.
  Provenance: `label_conditioned: true, evaluative: false`.
- **Arm B** (label-blind): action withheld, IDs shuffled, descriptions sanitized.
  Two negative controls (travel-era descriptions with no identity signal).

Key design improvements over v1/v2:
- Formula stripped from both prompts (prevents back-solving)
- ABSENT as first-class answer (not forced population)
- Ordering checks as findings, not constraints
- JSON output with provenance headers
- No self-grading — all verification in code

### Phase 4: Panel analysis (C1-C10)

| Check | Result |
|---|---|
| C1 presence | Arm A mostly populated; Arm B 36.3% null rate |
| C2 ordering | 0 inversions (escalate > suppress in all categories) |
| C3 info < ignorance | 19/36 escalate panel rows below 0.5 default |
| C4 service floor | Cloud suppress 0.456 vs human suppress 0.193 |
| C5 f0 × f5 correlation | Pearson -0.526 (negative — not double-counting) |
| C6 A→B delta | 26.4% of fields filled from null to non-null |
| C7 negative control | Both controls fully confabulated by all 3 models |
| C8 disposition recovery | 96.3% (104/108) |
| C9 cell coverage | 12/24 cells have n=1 |
| C10 evidence basis | 9.3% disposition_prior |

Scorer verification: 36/36 match, C9B PASS (+0.098 margin), IKS 90.3 > 67.

### Phase 5: Weakness assessment (Opus review)

Five weaknesses identified:

| # | Weakness | Severity |
|---|---|---|
| W1 | Negative control confabulation | Bounds Arm B, not Arm A |
| W2 | 12/24 cells have n=1 | Not a blocker; learning updates in ~14 decisions |
| W3 | Service-account floor (service→0.9) | Root cause: aggregation defect |
| W4 | Credential-access escalate bimodality | Not a blocker; per-cell σ handles it |
| W5 | Separation collapse (DE esc-sup = 0.021) | Root cause: aggregation defect |

**Key architectural finding:** W3, W5, and the insider paradox (IT-02) are
ONE problem — flat mean over non-commensurate signals. `user_risk_score` is
an IdP posterior that already accounts for MFA and device; averaging it with
its own inputs dilutes the signal. Fix lives in the aggregator, not the centroids.

### Phase 6: Debiased test battery

Removed confirmation bias with 6 falsification tests:

| Test | Result | Interpretation |
|---|---|---|
| 1: Current baseline | 36/36, MinConf -0.072 | **Baseline already has negative margins** |
| 1B: Current scenarios + proposed centroids | **34/36, 2 flips** | Atomic coupling confirmed — can't ship centroids alone |
| 2: Proposed (panel) | 36/36, MinConf +0.037 | Strictly better than current on confidence |
| 3: Simple heuristic (0.70/0.45/0.15/0.25) | 35/36, d' 6/6 | Nearly matches panel — category-specific centroids add minimal value over uniform |
| 4: Random centroids (100 trials) | 31.6/36 mean, d' 6.0/6 | **d' ≥ 0.5 gate is trivially easy** (97/100 random pass) |
| 5: Perturbation (refit) | 100/100 at 36/36 | Robust under jitter |
| 5B: Perturbation (fixed centroids) | 100/100 at 36/36 | Robustness is real, not circular |
| 6: Adversarial boundary | Min flip = 0.245 | No fragile scenarios |

### Phase 7: Measurement methodology corrections

Two circularity defects caught during analysis:

1. **L2 share measurement:** For n=1 cells, scenario f0 = centroid f0 by construction,
   so factor-0 share = 0%. Fixed with between-action discrimination measure.

2. **Margin contribution measurement:** For n=1 cells, distance to correct centroid = 0
   on f0 axis, so margin contribution is positive by construction. Fixed with
   leave-one-out (LOO), which showed only 2/6 categories non-negative.

Both corrections were identified during the analysis, not pre-registered — a
methodological weakness that is documented rather than hidden.

### Phase 8: Aggregation defect fix (SHIPPED)

Fixed the root cause of W3, W5, and the insider paradox in one change.

**The defect:** `PrivilegedIdentityContextFactor.compute()` averaged 4 signals
with equal weight. `user_risk_score` is an IdP posterior (Azure AD, Okta) that
already incorporates MFA and device status. Averaging a conclusion with its
own inputs diluted the signal.

**The fix:** Weighted mean with renormalization over present signals:

| Signal | Weight | Rationale |
|---|---|---|
| user_risk_score | 0.50 | IdP posterior — the conclusion |
| user_title | 0.20 | Static privilege attribute |
| mfa_completed | 0.15 | Auth signal (input to risk_score) |
| device_fingerprint_match | 0.15 | Auth signal (input to risk_score) |

When a signal is absent, its weight is redistributed proportionally among
present signals (standard renormalization).

**Impact on representative inputs:**

| Scenario | Old f0 | New f0 | Delta |
|---|---|---|---|
| Insider paradox (IT-02): risk=0.85, clean auth | 0.3125 | 0.4950 | +0.1825 |
| Admin, no MFA, unknown device | 0.8375 | 0.8775 | +0.0400 |
| Regular user, clean auth | 0.1250 | 0.1700 | +0.0450 |
| Service account, clean auth | 0.3250 | 0.3600 | +0.0350 |
| C9B seed (risk+mfa+device, no title) | 0.8667 | 0.9031 | +0.0364 |
| No context | 0.5000 | 0.5000 | 0.0000 |

**What did NOT change:** eval scenarios, centroid tensor, IKS anchor,
factors 1-5, the factor computer's interface.

**Verification:** 6 checks passed (code structure, 12 exact arithmetic cases,
7 edge cases, weight-sum invariant over 15 subsets, title mapping, file audit).

### Phase 9: Diagnostic flags and cleanup (SHIPPED)

Three flags from post-verification, all resolved:

| Flag | Finding | Action |
|---|---|---|
| `manager` title → 0.20 | Pre-existing mapping, aggregation didn't change it | False alarm — no fix needed |
| `centroid_backup_latest.json` changed | Runtime auto-snapshot artifact from test execution | Restored to tracked version |
| `test_no_incorrect_rl_naming` SDK failure | Pre-existing mixed documentation issue in demo_scenarios_and_usecases_v2_7.md | Reworded active lines, excluded version-history table rows from scanner |

## 3. What we learned

### About factor-0

1. Factor-0 is the dominant scoring dimension (60-100% of L2 in most scenarios).
   Any change to factor-0 is a model geometry change, not a cosmetic update.

2. The current uniform ladder (0.75/0.60/0.30/0.20) actively hurts classification
   in all 6 categories. Factor-0's margin contribution is negative everywhere.
   The system scores 36/36 DESPITE factor-0, not because of it.

3. The proposed panel values improve margin contribution (14 sign flips from
   hurting to helping), but a simple heuristic performs comparably. The panel's
   main contribution is per-scenario characterization, not centroid placement.

4. Scenarios and centroids are atomically coupled. Changing centroids without
   scenarios causes 2 flips (CI-01, CI-02). Changing scenarios without centroids
   was the prior failed migration. Both must change together.

5. The flat-mean aggregation conflated privilege with risk. The fix (weighted
   mean 0.50/0.20/0.15/0.15) is now shipped. Pilot data will flow through the
   correct computation from day one.

### About the methodology

6. Multi-model judge panels work for fixture authoring but not for evaluation.
   Label leakage (conditioning the feature on the disposition) is structural
   in Arm A. Arm B's negative controls showed all 3 models confabulate
   confidently on zero-signal scenarios.

7. Confirmation bias in experiment design is persistent. The naive L2 share
   measurement, the margin contribution measurement, and the d' gate (97%
   random pass rate) all had to be corrected during analysis. Pre-registering
   the measurements and their acceptance criteria before running the panel
   would have saved several iterations.

8. The hardest things to get right in LLM judge design are the context and
   the questions. v1 asked "what does the description say?" (wrong question).
   v2 asked "what is typical for this action?" (label leakage). v3's two-arm
   design was correct but required three rounds of review to reach.

### About the product

9. The current system works. 36/36 accuracy with the stale factor-0 values.
   The other 5 factors compensate. The migration is a correctness improvement,
   not a functional fix.

10. Real identity data from a pilot customer replaces the entire panel exercise.
    Live alerts with actual user_risk_score, MFA status, and device fingerprint
    provide ground truth that no LLM panel can match.

## 4. Decision

**SHIP the aggregation fix. DEFER the centroid/scenario migration to pilot data.**

Rationale for aggregation fix (shipped):
- One code defect caused three symptoms (W3, W5, insider paradox)
- Fix is self-contained (one function, same interface)
- Pilot data will flow through the correct computation from day one
- No centroid, scenario, or IKS changes required

Rationale for deferring centroid migration:
- The product works now (36/36, IKS 93)
- The panel values are label-conditioned (Arm A) and cannot carry evaluative claims
- A simple heuristic nearly matches the panel — the exercise was over-specified
- Real pilot data provides ground truth

**What shipped:**
- Quarantined scenarios with `travel_match_v1` provenance
- STALE centroid comments
- Alias deprecation instrumentation
- Aggregation fix: flat mean → weighted mean (0.50/0.20/0.15/0.15)
- RL naming fix in demo_scenarios_and_usecases_v2_7.md
- Design documents and analysis scripts
- This summary note

**What is filed for future work (triggered by pilot data):**

| Item | Trigger | Effort |
|---|---|---|
| Centroid migration (atomic: scenarios + centroids + IKS anchor) | Pilot identity data | 1-2d |
| Per-(action,factor) σ in DiagonalKernel | After centroid migration | 1d |
| Weight floor (≥10% per factor) | With centroid migration | 0.5d |
| Kernel refresh cadence (≥40 decisions) | With centroid migration | 0.5d |

## 5. Artifacts produced

| Artifact | Location | Purpose |
|---|---|---|
| factor0_inventory_v1.md | copilot-sdk/docs/design/ | 551-reference inventory |
| factor0_architectural_decisions_v1.md | copilot-sdk/docs/design/ | B/B/B decisions |
| factor0_identity_values_v1.md | copilot-sdk/docs/design/ | Single-model judge values |
| factor0_centroid_review_v1.md | copilot-sdk/docs/design/ | Single-model centroid review |
| factor0_scorer_verification_v1.md | copilot-sdk/docs/design/ | 36/36 scorer verification |
| factor0_migration_design_v2.md | copilot-sdk/docs/design/ | CONDITIONAL migration design |
| factor0_live_state_diagnostic_v1.md | copilot-sdk/docs/design/ | 4,862 decisions = synthetic backfill |
| factor0_panel_analysis_v1.md | copilot-sdk/docs/design/ | C1-C10 verification results |
| factor0_panel_data/*.txt | copilot-sdk/docs/design/ | 6 raw panel outputs (3 models × 2 arms) |
| factor0_reconciliation_summary_v1.md | copilot-sdk/docs/design/ | This summary note |
| analyze_factor0_panel.py | copilot-sdk/scripts/ | Reproducible panel analysis |
| factor0_margin_contribution_v2.py | copilot-sdk/scripts/ | Margin contribution analysis |
| factor0_loo_margin_v3.py | copilot-sdk/scripts/ | LOO margin + d' + kernel checks |
| factor0_debiased_battery_v4.py | copilot-sdk/scripts/ | 6-test falsification battery |
| factor0_agg_verify_v1.py | copilot-sdk/scripts/ | Aggregation fix verification |
| test_factor0_legacy_fixture_quarantine.py | copilot-sdk/tests/ | Quarantine guard tests |

## 6. Final test state

| Repo | Tests | Failures | Status |
|---|---|---|---|
| SDK root | 3,007 | 0 | ✅ |
| SOC BE | 2,274 | 0 | ✅ |
| S2P BE | 1,701 | 0 | ✅ |
| Trading BE | 1,243 | 0 | ✅ |
| Purchasing BE | 693 (+1 skip) | 0 | ✅ |
| DataOps BE | 289 | 0 | ✅ |
| ci-platform | 619 | 0 | ✅ |
| **Total** | **9,826** | **0** | ✅ |

## 7. Impact on roadmap

Factor-0 reconciliation is CLOSED and OFF the critical path. The forward
queue resumes at:

1. **Track 1 (engineering):** SOC monkeypatch removal, PW re-runs
2. **Track 3 (AGE unification):** Phase B remaining → C → D → E → Phase 6
3. **Track 4 (demo polish):** 4/8 beats to all 8 (~2 weeks)
4. **Track 5 (architecture):** C-REGIME P0-P4 + EXP-REGIME

Factor-0 re-enters the queue only when a pilot customer provides
identity-enriched alert data. Until then, the system operates correctly
with stale-but-honest factor-0 values, a correct aggregator, and
quarantine infrastructure that prevents stale values from being treated
as identity-validated.
