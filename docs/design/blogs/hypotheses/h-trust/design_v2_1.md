# H-TRUST design v2.1 — pre-registration addendum + resolved build gates (frozen before build)

Amends `design_v2.md`. Freezes the three pre-registration open questions in the **anti-bias direction**, adds one scope-limit note the design review surfaced, and records the two **access/dependency build-gates** that must be resolved (by you) before Stage 4. Frozen items may not be re-opened during the build; changing one requires a new design version and a fresh Stage-3 review.

In-repo home: `copilot-sdk/docs/design/blogs/hypotheses/h-trust/design_v2.1.md`

The v1.1 freezes still apply in full (numeric/ordinal primary factors, balanced accuracy as the single primary endpoint, 1.0pp margin, ≤2pp width for a decisive cell, required HELOC, train-only fitting, hostile tuned baselines, power as a stopping criterion). v2.1 adds to them.

---

## Frozen pre-registrations (the three open questions)

**PR-3 — post-homogenization admissibility threshold (C2).** A dataset's homogenized baseline is admissible for the heterogeneity test only if `H_base_post ≤ 0.10` **and** its 95% interval width ≤ 0.10, exactly as proposed in design_v2. This threshold is fixed **now**, before any data is seen, and is not tuned after inspecting H_base. A dataset that cannot meet it is marked **C2 UNTESTABLE** — never reported as a flat-null. Rationale: the threshold exists to prevent a confounded C2 curve, not to manufacture a positive one, so it must be set blind.

**PR-4 — grouping key for the duplicate/group split.** Primary rule: if a dataset exposes a valid source-level group key (household / customer / application), use it. Otherwise, a "group" is the exact numeric/ordinal feature-vector hash after the documented quantization. Group-stratified split is deterministic and no group crosses train/validation/test. If a dataset has zero multi-record groups, report that count (zero) and fall back to the pre-registered stratified split. The primary result uses group splits wherever groups exist; full-data and group-split results are reported side by side. This rule is fixed before splitting; the choice of key is not revisited after seeing effects.

**PR-5 — scale-sensitivity seed policy.** The three primary contrasts are run under all three scale conventions (min-max primary; robust-quantile 2/98 with clipping; standardized) at the **full 20 outer seeds each**, not a reduced pilot. The 40-seed extension is triggered per contrast **only** by the existing width>2pp stopping rule, applied independently under each scale convention. Rationale: the magnitude verdict must be scale-robust, so each scale convention gets an equally powered test; under-powering the alternatives would let min-max silently dominate the conclusion.

## Scope-limit note (frozen, for honest write-up)

**SL-1 — the heterogeneity law, if validated, is validated on homogenized-then-graded features, not native data.** The C2 homogenization raises every factor's variance to a common target (`v* = max_j σ_j²`), so the C2 experiment necessarily operates in a **higher-baseline-noise regime than the real data**. This is the price of a genuine homogeneous H=0 anchor and is accepted. Consequence for the paper: a positive C2 result must be stated as "the heterogeneity law holds on features homogenized to a common noise floor and then graded," an explicit scope limit — not as a claim about native-noise data. The C1 mechanism contrasts (magnitude / reliability / primitive) are unaffected; they run on native (non-homogenized) features and carry no such limit.

## Build gates — RESOLVED (frozen)

Both access/dependency blockers are resolved. The design still forbids silent mirror substitution; these decisions replace the STOP conditions with authoritative, hash-verified sources.

**BG-1 — authoritative credit parser: RESOLVED — `xlrd` approved.** Parse the official UCI "Default of Credit Card Clients" `.xls` (UCI id 350) with `xlrd`, one-time, read-only. Record the source URL, retrieval date, byte count, and SHA-256 in the manifest. No public CSV mirror.

**BG-2 — HELOC access: RESOLVED by dataset substitution.** HELOC is REMOVED (its FICO-challenge terms require registration and cannot be auto-fetched or redistributed, which is what forced the v1 mirror and its provenance hole). To keep three required datasets — the design needs ≥2 for replication and forbids a single-benchmark pooled claim, so three is the safe floor — the third required dataset is:

  **Adult / Census Income (UCI id 2).** Openly downloadable, hash-verifiable, bounded interpretable magnitude-bearing numeric/ordinal features (age, hours-per-week, capital-gain, education-num, ...) with a real binary outcome (income >50K).

Rationale for the choice (frozen): Adult is deliberately the LEAST credit-correlated option — the three required sets are now three DIFFERENT domains (Credit = default risk, COIL 2000 = insurance uptake, Adult = income), which is a stronger cross-dataset replication test than three flavors of credit risk. All three are authoritative UCI sources fetched and SHA-256-verified from origin.

**Consequence, stated honestly.** Removing HELOC drops the specific provenance-vs-magnitude probe HELOC carried (it was the one mirror-sourced set where v1 F2 did not fire). This is acceptable because the confound is now closed *by construction*: with three authoritative, hash-verified UCI sources there is no mirror artifact to disentangle. The design_v2 "provenance-vs-magnitude check" is accordingly simplified from a HELOC-specific probe to a QA step: confirm no primary contrast changes sign by source; a contrast that flips with source is a data-integrity failure, not evidence.

## Freeze statement

PR-3, PR-4, PR-5, SL-1, and both build gates (BG-1 `xlrd` approved; BG-2 resolved by the Adult-for-HELOC substitution) are fixed as of this addendum. The three required datasets are UCI Credit (id 350), COIL 2000 (id 125), and Adult/Census Income (id 2), all authoritative and hash-verified. Stage 4 executes `design_v2.md` **as amended here**. Any change to a frozen item is a new design version requiring a fresh Stage-3 review — not a build-time decision.
