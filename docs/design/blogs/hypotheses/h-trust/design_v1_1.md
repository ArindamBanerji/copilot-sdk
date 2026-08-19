# H-TRUST design v1.1 — pre-registration addendum (frozen before build)

Amends `design_v1.md`. Resolves the two design-review conditions and the five reviewer open questions, each in the **anti-bias direction**. These decisions are **frozen before any code runs (Stage 4)** and may not be re-opened during the build; changing any of them requires a new design version and a fresh Stage-3 review.

In-repo home: `copilot-sdk/docs/design/blogs/hypotheses/h-trust/design_v1.1.md`

---

## Design-review conditions (the two APPROVED-conditional items)

**PR-1 — Primary "factor" set = numeric / ordinal only.** The per-factor reliability estimate σ_j and the heterogeneity index H are computed over genuinely magnitude-bearing numeric/ordinal features only. One-hot categorical blocks are **excluded from the primary factor set** — they manufacture low-variance indicator dimensions that would inflate H and flatter the C2 law. One-hot encodings enter as a **sensitivity analysis only**, reported separately, never in the primary C1/C2 result. Rationale: keeps "factor reliability" meaning the reliability of a real quantity, which is what H-TRUST claims — not the reliability of an indicator column.

**PR-2 — Single primary endpoint = balanced accuracy.** Balanced accuracy is the **one** primary endpoint for both C1 and C2. Every other metric (top-1 retrieval, macro-F1, average precision, Brier/ECE, coverage, abstention-risk) is **exploratory** and cannot — individually or in combination — be promoted to "the result" after the fact. Rationale: closes the garden-of-forking-paths across the ~6 endpoints.

## Reviewer open questions — frozen answers

**Q1 (HELOC redistribution).** HELOC remains a **required** dataset. If its agreement forbids redistributing derived splits/data, run it on an authorized local copy and publish the numbers, feature map, and access path — **do not drop it**. Dropping a required dataset for access convenience reintroduces dataset-selection bias; leave-one-dataset-out is reported regardless.

**Q2 (categorical encoding).** Resolved by PR-1 — numeric/ordinal-only primary, one-hot sensitivity-only.

**Q3 (1pp equivalence margin).** Fixed at **1.0 percentage point**, pre-registered now, for all three falsification rules (F1/F2/F3). Not revisited after seeing interval widths. The margin is meaningful only when the 95% interval width ≤ 2pp; otherwise the cell is **INCONCLUSIVE**, never a pass or a kill.

**Q4 (ACSIncome ethics/use).** ACSIncome stays **optional external validation only** (it was never a required dataset). Demographic/group features are excluded from scoring weights and used only for subgroup reporting. If the project's ethics/data-use review does not clear it before the run, ACSIncome is omitted — this does not weaken the required three-dataset result.

**Q5 (primary outcome).** Resolved by PR-2 — balanced accuracy, fixed now.

## Unchanged from design_v1

Everything else in `design_v1.md` stands: the F2 normalize-control runs first with its kill rule; hostile tuned baselines (cosine temperature/threshold tuned, matched hyperparameter budgets); train-only σ / prototype / threshold / calibration fitting; the fixed-geometric-mean heterogeneity variation (spread varied, total noise held constant); the 16-item confound register; and power as a **stopping criterion** — a wide interval is inconclusive, never a pass.

## Freeze statement

These pre-registrations are fixed as of this addendum. The build (Stage 4) executes `design_v1.md` **as amended here** and reports against F1/F2/F3 exactly as written. Any change to a frozen item is a new design version requiring a fresh Stage-3 review — not a build-time decision.
