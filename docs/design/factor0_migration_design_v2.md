# SOC Factor-0 Migration Design v2

**Decision date:** 2026-08-16  
**Status:** Architecture decision; no implementation authorized by this document  
**Scope:** SOC factor-0 reconciliation from legacy travel semantics to
`privileged_identity_context`

## 1. Problem statement

SOC has a semantic split at factor index 0. The active factor computer is
`PrivilegedIdentityContextFactor`, whose canonical name is
`privileged_identity_context` (`gen-ai-roi-demo-v4-v50/backend/app/domains/soc/factors.py:64-73`).
It computes a bounded average from user risk, title, MFA, and device-fingerprint
signals (`factors.py:95-156`); it does not compute travel-match evidence.

The retained 36-scenario evaluation set is intentionally different. It contains
travel-authored values and the `travel_match` key, with a
`travel_match_v1` semantic marker. The v1 architectural decision explicitly
quarantines those fixtures rather than silently rekeying them
(`copilot-sdk/docs/design/factor0_architectural_decisions_v1.md:24-59`).

The bootstrap centroid tensor is also still travel-derived and marked stale.
The SOC literal is used by `get_profile_centroids()` and
`get_initial_centroids()` (`gen-ai-roi-demo-v4-v50/backend/app/domains/soc/config.py:153-236,663-673`),
and the SDK carries a duplicate preset literal
(`copilot-sdk/copilot_sdk/scoring/presets/soc.py:84-125`).

This is not a harmless identifier rename. Factor 0 is the most influential
dimension in the supplied evaluation: it contributes more than 60% of total
distance in 22/36 scenarios and more than 90% in six. The scorer therefore
couples factor semantics, scenario values, centroid values, confidence
geometry, and learned state.

The current production state is nevertheless operationally functional. The
factor computer has been emitting identity-context values, while the learner
has adapted live centroids through approximately 4,862 verified decisions. The
system is therefore best described as a partially identity-calibrated live
model with a travel-calibrated bootstrap and an honest semantic warning—not as
a completed migration.

## 2. Findings from the failed migration

### Finding 1 — Factor 0 dominates scoring

The 36-scenario analysis found 22 cases where factor 0 exceeds 60% of the
total squared-L2 distance and six above 90%; SOC-IT-03 reaches 100%. Any
factor-0 change is therefore a model-geometry change, not a metadata edit.

### Finding 2 — Scenarios and centroids are atomically coupled

An input interpreted as identity risk cannot be compared meaningfully against a
centroid interpreted as travel-match evidence. The old scenario set must remain
legacy evidence or be re-authored; a blind key replacement is semantic
laundering. This is also the conclusion of the v1 design review and decisions
(`factor0_design_review.md`; `factor0_architectural_decisions_v1.md:35-47`).

### Finding 3 — Centroid changes alter product routing

A 0.003 confidence movement crossed the credential-access referral threshold of
0.62. The threshold is implemented as a category-specific routing policy in
`gen-ai-roi-demo-v4-v50/backend/app/framework/composite_gate.py:30-48,147-154`.
It is not merely a test fixture expectation.

### Finding 4 — Centroid changes alter IKS

The drift IKS is computed as mean L2 distance from an immutable bootstrap
anchor, normalized by `D_MAX = 0.20` (`gen-ai-roi-demo-v4-v50/backend/app/framework/iks_base.py:7-17,34-50,57-96`).
The SOC service loads the anchor from
`backend/app/data/iks_bootstrap_soc.json` (`app/services/iks.py:19-21,45-70`).
Changing live scoring centroids without changing that anchor created artificial
reference-point drift and reduced the observed score from the low 90s to about
51 in the failed attempt.

### Finding 5 — Action-selection verification was insufficient

The proposed values retained the expected action in all 36 bootstrap cases,
with zero action flips (`factor0_scorer_verification_v1.md:44-70`). That test
did not test confidence thresholds, referral routing, IKS, learned-state
compatibility, live endpoint output, or rare category/action cells.

### Finding 6 — Ordinal direction was accidentally useful

The old prior generally ordered escalation above investigation and low-risk
actions below it. That ordering supports action preservation under both travel
and identity interpretations. Preserved order is not evidence that the
magnitudes are calibrated for the new factor.

### Finding 7 — The live learner is already performing an organic transition

Production factor observations are identity-context observations, and the
stochastic update

`mu_new = mu_old + eta * (f_observed - mu_old)`

has been moving live centroids toward the observed identity-context
distribution. This is expected adaptation, but it does not repair the
bootstrap provenance, the frozen IKS reference, sparse-cell behavior, or
evaluation evidence. With a constant step size, the residual influence of an
initial value after `n` same-rate observations is `(1-eta)^n`; at eta=0.05 it
falls below 1% after roughly 90 observations, while at eta=0.01 it takes roughly
459. The actual washout is cell-specific and cannot be inferred from the total
decision count alone.

## 3. Answers to the design questions

### Q1 — Is the live semantic split a problem or the system working as designed?

**Answer: both, at different layers.** The learning loop is working as
designed: it uses actual factor observations and can converge from a bounded
initial prior when coverage and feedback are sufficient. The semantic split is
still a governance and cold-start problem. It affects early decisions,
confidence, and audit interpretation; it remains material in cells with low
effective update counts; and it leaves the IKS anchor and historical records
with a different semantic provenance.

The bootstrap does not need to be perfect for eventual convergence, but “the
learner will fix it” is not an acceptable release criterion. Before convergence,
the prior influences behavior. A migration is justified only when its transient
behavior and its effect on the reference metrics are explicitly verified.

### Q2 — What are the evaluation scenarios for?

**Answer: primarily regression and historical evidence, not current
identity-quality validation.** They can validate scorer mechanics and protect
the behavior of the legacy fixture set. They must not be used to claim that the
live identity-context factor is accurate. A new identity-context suite is needed
for real-world triage-quality evaluation, with values tied to identity-provider,
MFA, title, and device evidence.

The correct long-term arrangement is two versioned suites:

1. `travel_match_v1`: retained, quarantined, historical/regression-only.
2. `privileged_identity_context_v1`: separately authored and reviewed for
   identity semantics.

### Q3 — What should happen to the IKS anchor?

**Answer: leave the existing anchor immutable.** The implementation loads a
separate sidecar anchor and computes drift from it; this is the intended
two-artifact model. Overwriting it would erase the historical meaning of the
existing IKS series and manufacture a lower score by moving the reference point.

The factor transition should be disclosed as one component of the observed
historical drift. If a future major model version needs an identity-native
baseline, create a versioned `mu_zero_v2` and a new IKS series with an explicit
re-baselining label. Do not mutate `iks_bootstrap_soc.json` in place and do not
compare v1 and v2 scores as if they were continuous.

### Q4 — How should confidence thresholds be managed?

**Answer: explicit product-policy thresholds, recalibrated when geometry
changes.** They are not disposable constants: the 0.62 credential-access value
controls referral behavior. They also cannot be auto-derived from centroids
without policy review, because safety and analyst workload determine the cost of
false referrals and missed referrals.

For a controlled migration, preserve thresholds only if replay proves that the
existing operating points remain valid. Otherwise ship a versioned threshold
set atomically with the new scorer prior and record the calibration dataset,
operating point, and approval. Never change a threshold merely to make a test
pass.

### Q5 — Is explicit migration necessary now?

**Answer: no numeric migration is necessary now; it is conditionally required
later.** The current system is working, its canonical runtime name is clear,
its legacy fixtures are labeled, aliases are monitored, and the live learner is
already adapting. Replacing the prior now would create avoidable product and
metric discontinuities without sufficient evidence; the v1 centroid review
itself labels ten of 24 entries uncertain and says the proposed prior is not
production-ready (`factor0_centroid_review_v1.md:123-160`).

Organic convergence is sufficient as an interim operating strategy only with
the guardrails in Section 5. It is not sufficient for a claim that the model
has been identity-calibrated. Migration should be triggered by measured
identity-context data and a controlled replay/release gate, not by the passage
of time or the existence of a plausible hand-authored table.

### Q6 — If migration is needed, what is the atomic unit?

**Answer: a versioned model-and-evidence release, not an individual file edit.**
The atomic release must include:

1. A semantic contract naming factor 0, its input signals, polarity, version,
   missing-data behavior, and provenance/substantiation tier.
2. A new identity-context evaluation suite and expected actions, while retaining
   the legacy suite as a separate version.
3. One approved scoring prior, applied identically to SOC config and SDK preset;
   factor order, tensor shape, and factors 1–5 must be checked byte-for-byte or
   numerically.
4. A new immutable IKS anchor artifact and a new versioned IKS series. The old
   anchor and historical series remain read-only.
5. A frozen live-state snapshot, including current centroids, learning ledger,
   verified decisions, effective cell counts, and semantic/model version.
6. An explicit cutover policy: preserve live learned centroids, initialize a
   new model, or run a dual scorer before promotion. A silent reset or
   retroactive rescoring is forbidden.
7. Confidence thresholds and referral-policy calibration, including C9B seed
   contracts and boundary cases.
8. Alias/provenance behavior, persisted-record compatibility, and rollback
   metadata.
9. Product endpoint and PW evidence proving that IKS, confidence, routing,
   narrative, and displayed factor labels remain coherent.

### Q7 — What is the complete verification protocol?

Action-selection parity is only one gate. Every future factor-0 change must
pass the checklist in Section 6, including geometry, metrics, state, contracts,
and product behavior.

## 4. Decision

### CONDITIONAL — defer numeric migration; prepare an evidence-gated release

Do not migrate the production bootstrap centroid, frozen v1 IKS anchor, or
legacy scenario file now. Keep the current canonical runtime factor and the
honestly labeled legacy data. Treat the live learned centroids as a mixed-state
model whose semantic version must be visible in diagnostics and release
artifacts.

The decision becomes **MIGRATE** only after all of the following are true:

* a SOC analyst approves the identity-context contract and the uncertain
  scenario/prior cases;
* identity-context observations and verified outcomes provide coverage for all
  category/action cells, with sparse cells explicitly handled;
* offline replay and shadow scoring cover action selection, confidence,
  referrals, margins, and analyst workload—not only top-1 action;
* the new prior is tied to evidence and substantiation, not only a hand-authored
  rationale;
* a new immutable IKS anchor and versioned metric continuity plan exist;
* the live-state cutover, rollback, and historical-record policy are approved;
* full backend, SDK, and PW suites pass with no new skips and no product-facing
  metric discontinuity that has not been labeled and accepted.

## 5. Interim guardrails while migration is deferred

1. Keep `privileged_identity_context` canonical in runtime config, factor
   dispatch, and SDK presets. Do not reintroduce travel semantics into the live
   factor computer.
2. Keep `travel_match_v1` fixtures quarantined and excluded from current
   identity-quality, accuracy, ROI, or customer-learned claims.
3. Keep the two input aliases during the bounded compatibility window, with
   deprecation telemetry and semantic provenance. New writes and responses use
   the canonical key.
4. Do not change the current prior or IKS anchor independently. Any experiment
   must use an isolated, versioned artifact and must not mutate production
   learning state.
5. Surface semantic version, bootstrap version, anchor version, and learned
   state version in diagnostics. A single numeric IKS without its anchor version
   is not comparable across releases.
6. Track effective update counts and factor-0 distributions per category/action.
   Do not declare a cell migrated merely because the global total is large.
7. Separate semantic migration from model-quality claims. The current IKS may
   include travel-to-identity adaptation; describe that as historical
   recalibration, not as a pure measure of customer-specific domain learning.
8. Add release checks that reject a scenario or report when its semantic
   version does not match the claim being made.

## 6. Future migration specification

When the evidence gates pass, use this sequence as one controlled release:

### A. Freeze and snapshot

Stop learning writes, record the live centroid tensor and its per-cell update
counts, snapshot decision/outcome ledgers, and record the current IKS and
anchor-version metadata. No historical record may be silently rewritten.

### B. Build parallel artifacts

Create the identity-context scenario set and its provenance. Create the new
identity bootstrap prior and SDK copy from one canonical source. Create a new
immutable IKS anchor with a new version identifier. Retain v1 artifacts for
historical replay.

### C. Replay and shadow

Replay representative historical data twice: current v1 semantics and proposed
identity semantics. Compare top-1 action, referral routing, confidence,
top-two margin, per-category error, and analyst workload. Include boundary
cases, low-confidence cases, service accounts, missing context, and sparse
cells. Run the new scorer in shadow before it can affect selected actions.

### D. Decide learned-state continuity

Prefer an explicit policy backed by replay:

* retain live centroids if they already represent the new factor and annotate
  them with the new semantic version;
* otherwise initialize a new version from the approved identity prior; or
* run a dual model until the new model meets the release gate.

The choice must account for the 4,862 existing decisions and their historical
factor semantics. Existing learned values must not be treated as if they had
been trained from an identity-native bootstrap unless the evidence supports
that claim.

### E. Calibrate and cut over

Approve confidence/referral thresholds from identity-context replay. Apply the
scoring prior, threshold set, anchor version, fixture version, and diagnostics
version together. Verify aliases, provenance, API payloads, and rollback before
resuming learning.

### F. Post-cutover observation

Monitor action mix, referral rate, confidence distribution, margin distribution,
per-cell update counts, IKS v2 trend, and v1/v2 metric labels. Define a rollback
trigger in advance; do not use a passing unit suite as the only production
health signal.

## 7. Complete verification checklist for any centroid change

### Contract and semantics

- [ ] Factor name, index, polarity, input signals, defaults, and semantic
      version agree across factor computer, SOC config, SDK preset, schemas,
      persisted records, and diagnostics.
- [ ] Scenario fixtures are either re-authored with evidence or explicitly
      marked as legacy; no blind key rename is present.
- [ ] Provenance and substantiation tiers are attached to every reportable
      value; legacy/demo data cannot become a customer claim.

### Numeric and scorer geometry

- [ ] Both tensor copies have shape `(6,4,6)` and identical factor order.
- [ ] All factor-0 entries have a documented rationale and evidence status;
      uncertain entries are explicitly gated.
- [ ] Factors 1–5 are unchanged unless the release declares them changed.
- [ ] Run bootstrap squared-L2 action selection for every scenario and report
      expected-action matches, flips, top-two margins, and near ties.
- [ ] Run learned-state replay with real scorer code, not an action-only script.
- [ ] Test missing context, extreme values, service accounts, normal users,
      unknown devices, MFA absent/present, and sparse cells.

### Confidence and routing

- [ ] Recompute confidence distributions and margins per category/action.
- [ ] Verify every category threshold and the global fallback.
- [ ] Exercise referral boundaries immediately below, at, and above each
      threshold, including the credential-access 0.62 boundary.
- [ ] Verify C9B seed contracts, low-confidence analyst routing, and referral
      workload; do not relax expectations to hide geometry changes.

### IKS and state continuity

- [ ] Confirm which anchor version is used and that an immutable anchor is not
      overwritten.
- [ ] Compare mean L2 drift and IKS before/after using the same anchor; explain
      every discontinuity.
- [ ] If re-baselining, publish a new metric series and prohibit direct numeric
      comparison with the old series.
- [ ] Snapshot and validate live centroids, learning ledger, update counts,
      verified decisions, and semantic/model versions.
- [ ] Prove that no historical decision is silently rescored or double-counted.

### Product and compatibility

- [ ] Check diagnostics, profile, learning-state, Tab 2 IKS, narratives,
      confidence labels, and factor explanations.
- [ ] Run PW tests for displayed labels, routing, IKS, and scenario history.
- [ ] Test both canonical and legacy input aliases and verify deprecation
      telemetry.
- [ ] Verify persisted readers, exports, provenance registry, SDK consumers,
      and cross-repository tensor copies.

### Release quality

- [ ] Run SOC backend, SDK, per-copilot, and relevant frontend suites.
- [ ] Require zero new failures and zero unreviewed skips.
- [ ] Run static checks for stale names, tensor mismatch, semantic-marker
      mismatch, and unverified customer-facing claims.
- [ ] Record artifacts, counts, thresholds, anchor version, rollback trigger,
      and reviewer approval in the release record.

## 8. Lessons learned

1. A factor rename with changed meaning is a model migration, not a string
   migration.
2. Preserving all top-1 actions does not prove confidence, routing, IKS, or
   learned-state safety.
3. A frozen baseline is a measurement contract. Never overwrite it to make a
   new model appear continuous.
4. Organic learning can reduce the practical effect of a bad prior, but it
   cannot repair provenance or justify a customer-facing semantic claim.
5. The unit of change is the semantic contract plus scorer geometry, thresholds,
   anchor, state policy, fixtures, and verification evidence.
6. Honest quarantine is safer than semantic laundering. The current state can
   ship operationally only while its mixed semantics remain visible and its
   claims remain bounded.

## Final decision summary

| Question | Decision |
|---|---|
| Q1 live system | Learner is working, but the semantic split remains a cold-start, sparse-cell, and provenance risk. |
| Q2 eval scenarios | Retain the 36 as versioned regression/historical fixtures; author a separate identity-quality suite. |
| Q3 IKS anchor | Keep the existing anchor immutable; use a versioned new anchor only for a future major baseline. |
| Q4 confidence | Treat thresholds as explicit product policy; recalibrate and version them whenever geometry changes. |
| Q5 migration necessity | Defer numeric migration now; trigger it only on measured identity evidence and controlled replay. |
| Q6 atomic unit | A versioned model-and-evidence release covering prior, anchor, thresholds, state, fixtures, provenance, and rollback. |
| Q7 verification | Full contract, geometry, confidence, IKS, state, product, compatibility, and suite checklist in Section 7. |

**Decision: CONDITIONAL.** Keep the current production behavior and honest
quarantine. Prepare, but do not execute, the evidence-gated versioned
identity-context migration.
