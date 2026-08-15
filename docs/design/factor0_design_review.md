# SOC factor-0 naming reconciliation — design review

Model reviewed: `gpt-5.3`  
Review date: 2026-08-15

## Executive opinion

The canonical live name is correctly `privileged_identity_context`, and the
cross-repo preset agrees with it. The proposed cleanup is not purely a naming
change, however: the evaluation fixtures and centroid comments still encode
travel semantics. I recommend approving the naming decision and the product
addendum wording, but blocking any claim that the existing evaluation quality
or centroid prior is valid for the new semantics until the fixtures and
centroids are re-derived or explicitly reclassified.

## 1. The three decisions in §6

### Decision 1 — `TravelMatchFactor`

Delete it, but only after a broader dependency review than the spec currently
requires. The class is not part of the live factor configuration: the active
configuration imports `PrivilegedIdentityContextFactor` and omits
`TravelMatchFactor` (`gen-ai-roi-demo-v4-v50/backend/app/domains/soc/config.py:27-30`),
and the legacy class is a plain class at `factors.py:159-180`, rather than a
live configured `FactorComputer`. Its query is also based on an absent/legacy
travel graph shape and uses `User.id`, which is inconsistent with the documented
current graph seed; this makes it a poor candidate for retention as-is.

However, “zero references” is too strong as written. A repository-wide search
found eight textual references, including seed/data comments, the simulation
comment, a test comment, the class itself, and its own error log. There are also
tests and documentation that still use the `travel_match` contract. Therefore:

- zero runtime imports/instantiations supports deletion;
- zero textual references does not currently hold;
- delete only after class-specific references, stale tests, seed comments, and
  any historical documentation have been classified as either intentionally
  retained history or updated.

I do not recommend retaining it as a “sub-signal” without a separate design.
That would require a defined input contract, calibration, graph availability,
and an explicit composition rule into the identity factor. The current class
does not provide those, and its implementation is not even the same semantic
family as the live factor.

### Decision 2 — V1/V2 timing

The spec’s split is directionally right but too permissive in one respect. V1
should be a release gate for any claim that the bootstrap centroids represent
privileged-identity semantics; V2 should be a release gate for customer-facing
accuracy/ROI numbers. Neither needs to block a narrowly scoped code cleanup if
that cleanup is clearly labeled as naming/fixture reconciliation and no
semantic quality claim is made.

The proposed “ship C1–C6 now” is safe only if C1 is changed from a blind rekey
to one of these two options:

1. re-derive/relabel the evaluation scenarios so their factor-0 values and
   descriptions are genuinely identity-context scenarios; or
2. keep the old travel fixtures as historical data and create a new, explicitly
   privileged-identity evaluation set.

Blindly changing the key makes the data look semantically validated when it is
not.

### Decision 3 — product addendum naming

Approve. `privileged_identity_context` is the live SOC factor-0 name and is at
index 0 in the configuration (`config.py:116-127`); the live computer declares
the same name and index (`factors.py:64-73`); the SDK preset uses the same name
and six-factor order (`copilot-sdk/copilot_sdk/scoring/presets/soc.py:15-22`
and `:48-55`). “Privileged identity context / access-pattern” is suitable
prose, provided “access-pattern” is not introduced as a second code key.

## 2. Are the R1 scenario values semantically valid after rekeying?

No, not as currently evidenced. They are structurally valid as six bounded
factor values, but the values were authored as travel-match values. The first
three scenarios use `travel_match` values `0.3`, `0.9`, and `0.4`
(`backend/app/data/soc_eval_scenarios.json:7-14`, `:31-38`, `:55-61`). The
second scenario explicitly says “frequent traveler” and lists `travel_match`
as a dominant factor (`soc_eval_scenarios.json:42-46`). Another lateral
movement scenario says VPN-confirmed travel explains the event and gives
`travel_match: 0.8` (`soc_eval_scenarios.json:374-388`).

That does not match the live computer, whose inputs are `user_risk_score`,
title heuristics, inverted MFA completion, and inverted device-fingerprint
match (`backend/app/domains/soc/factors.py:64-73`, `:95-105`, `:133-156`).
The live computer has no travel-record or location input. Rekeying therefore
preserves numbers but changes their meaning and invalidates the scenario
descriptions/dominant-factor assertions unless the fixtures are re-authored.

The expected actions may coincidentally remain reasonable because the other
five factors dominate many scenarios, but that is not evidence that factor 0
is valid. The evaluation data is marked `provenance: "sample"` (for example
`soc_eval_scenarios.json:24`), so it must not be used to support a stronger
semantic or customer-facing claim without a new validation run.

## 3. Is μ₀[:,:,0] likely stale?

Yes—there is meaningful evidence of staleness, and no evidence in the
initialization code that it was re-derived for identity semantics.

The bootstrap tensor is a hand-authored literal beginning at
`config.py:153`. Its category-0 escalate comment still says “travel anomaly”
(`config.py:159-161`), while the factor order now labels axis 2, position 0,
as `privileged_identity_context` (`config.py:116-127`). The remaining category
comments likewise describe action profiles using travel/explainable movement,
not a systematic identity/MFA/title prior (`config.py:182-191`).

`get_profile_centroids()` and `get_initial_centroids()` merely return copies of
that same literal (`config.py:663-673`); they do not load a provenance-tagged
artifact, perform a re-derivation, or record the semantic version of factor 0.
The SDK has a duplicate hard-coded bootstrap tensor with the same values
(`copilot-sdk/copilot_sdk/scoring/presets/soc.py:84-125`), which confirms
cross-repo numeric convergence but not semantic correctness. The strongest
current conclusion is: shape and ordering are stable; the factor-0 prior is
unproven and probably stale.

Required V1 output should compare every category/action factor-0 centroid to
an identity-context rationale, or replace it with a documented re-derived
prior. Do not infer correctness from the `(6,4,6)` shape test.

## 4. Risks missed by the spec

- **Tests will drift or fail.** Existing tests still name `travel_match`,
  including the factor-order assertion in `tests/test_eval1_soc.py:69-74` and
  judgment input in `tests/test_judg1_soc.py:63-69`. C1–C5 must include the
  test contract update or intentionally preserve a test-only legacy fixture.

- **The alias is an external compatibility contract, not just an internal
  shim.** Both routers actively fall back from the canonical key to the old
  key (`routers/evaluation.py:20-23`, `:43-49`; `routers/judgment.py:28-31`,
  `:173-180`). Removing it can break clients sending persisted or older JSON.
  The spec needs a compatibility policy: hard cutover, versioned endpoint, or
  a bounded deprecation window.

- **Persisted data and learning state may retain old names or old semantics.**
  Decisions, provenance payloads, exported evaluations, and serialized scorer
  state can outlive this source edit. A source grep cannot establish that old
  records are migrated or safely interpreted.

- **Provenance becomes misleading even after the key rename.** The current
  provenance table maps both names to the identity explainer
  (`backend/app/framework/provenance.py:216-223`), but that only fixes lookup;
  it does not make travel-derived values identity-derived. Historical records
  need a semantic/version marker or an explicit legacy explanation.

- **The spec’s residual inventory is incomplete.** `travel_match` remains in
  alert-pool/seed comments, active framework-agent prose, tests, support
  notebooks, and the v5.8 backend design document. The requested C5 path also
  names `services/simulation.py`, while the same stale comment appears in
  `app/data/alert_pool.py`; both locations need classification.

- **The design-doc path is ambiguous.** The spec says to update
  `soc_copilot_design_v5_8.md`, but the live copy found by this review is under
  `gen-ai-roi-demo-v4-v50/backend/docs/design/`, not under the requested
  `copilot-sdk/docs/design/`. C6 needs an explicit authoritative path and
  ownership boundary.

- **Factor-name ordering is duplicated.** Config, SDK preset, evaluation
  fixtures, tests, docs, and possibly serialized vectors all encode axis-2
  position 0 independently. A rename-only change can leave the name aligned
  while the semantic contract remains split. Add a single contract test that
  checks names, factor computer dispatch, fixture meaning/version, and SDK
  order together.

- **The code’s “safe to ship” wording is too broad.** The naming cleanup can
  be safe operationally while still invalidating evaluation interpretation.
  Release notes and product claims must distinguish those two statements.

## 5. Is C1–C6 ordering safe?

Partly. C1 and C2 must be coordinated, as the spec says, because the loader
currently supports both canonical and legacy keys (`evaluation.py:36-65`).
But the safest sequence is:

1. inventory runtime, test, persisted-data, and documentation consumers;
2. decide the compatibility policy and semantic disposition of R1;
3. update tests/fixtures or create a new identity-semantic fixture set;
4. update the two router consumers and verify canonical loading;
5. update provenance dispatch and its tests;
6. only then remove the orphan class after runtime and textual references are
   classified; update comments/docs in the same bounded change;
7. run focused contract/evaluation/provenance tests, then the configured full
   suite and cross-repo checks.

Thus, the relative C1→C2 dependency is correct, but the published C1–C6 list
is incomplete: tests and compatibility/persistence checks must precede alias
removal, and semantic fixture/centroid decisions must precede declaring the
evaluation valid.

## 6. Recommended implementation order and estimate

Recommended staged order:

1. **Contract/inventory pass:** 0.5–1 day. Enumerate all runtime and textual
   references, persisted schemas, test fixtures, and authoritative docs.
2. **Naming cleanup:** 0.5–1 day. Update canonical fixture keys, tests,
   provenance key, aliases per the chosen compatibility policy, comments, and
   remove the orphan class only after evidence is recorded.
3. **Semantic evaluation remediation:** 1–2 days. Re-author or replace the
   36 scenarios with identity/MFA/title/device-context values and update
   dominant-factor explanations; then run the evaluation and record the
   experiment provenance.
4. **V1 centroid review/re-derivation:** 1–3 days depending on whether the
   existing validation source can be recovered. Update both repo presets only
   if the evidence supports a numeric change.
5. **V2 validation and release evidence:** 1–3 days for the two regimes,
   seed/repeatability checks, and product-number signoff.
6. **C6 documentation convergence:** 0.5–1 day once the semantic decisions
   are settled.

The naming-only portion is roughly 1–2 engineering days. A responsible change
that preserves semantic honesty and validates the numbers is roughly 4–8 days,
with V1/V2 being the uncertainty. No implementation is recommended until the
R1 semantic disposition and external alias policy are explicitly decided.

## Bottom line

Approve the canonical name and product prose. Delete the orphan class after a
complete dependency classification. Do not call the current R1 data valid
under privileged-identity semantics, and treat μ₀[:,:,0] as likely stale until
re-derived or evidenced. The proposed ordering has the right C1/C2 coupling
but needs test, compatibility, persistence, and semantic-validation gates.
