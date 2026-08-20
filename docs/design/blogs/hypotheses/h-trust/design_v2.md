# H-TRUST design v2 (corrected instrument)

The hypothesis is unchanged: on bounded, interpretable, magnitude-bearing features, a reliability-weighted metric beats normalized cosine and uniform L2, the advantage is magnitude-driven, and the gain grows with per-factor noise heterogeneity. This version changes only the instrument so each mechanism can lose independently. The v1.1 freezes remain in force: numeric/ordinal primary factors only, balanced accuracy as the single primary endpoint, 1.0pp margin, 95% interval width ≤2pp for a decisive cell, required HELOC, train-only fitting, hostile tuned baselines, and power as a stopping criterion.

## Why v2 (the three v1 defects, one line each)

1. **Factor conflation:** v1 compared normalized weighted distance with cosine, changing both magnitude and weighting at once, so its F2 result could not identify either mechanism.
2. **Uncontrolled C2 baseline:** v1 called injected H=0 “homogeneous” without measuring or removing intrinsic per-factor heterogeneity, so the flat curve could be an artifact of a nonzero baseline.
3. **Unclosed validity controls:** v1 used a credit CSV mirror, an unapproved HELOC mirror, one scale convention, and no duplicate/group audit, so provenance and scale could not be separated from the observed effect.

## Factorial + the degeneracy note

Run the full crossed design over three axes:

| Axis | Levels |
|---|---|
| Magnitude | raw bounded vectors; row-normalized vectors |
| Weighting | uniform `M=I`; train-only reliability-weighted `M=diag(1/sigma^2)` |
| Primitive | squared distance `-(q-k)^T M(q-k)`; dot/cosine similarity |

The primary factor set is numeric/ordinal only. Categorical one-hot blocks remain sensitivity-only and can never enter the primary C1/C2 result or H.

The cell `(normalized, uniform, distance)` is mathematically the same ranking as `(normalized, uniform, dot/cosine)`: on the unit sphere, squared L2 is `2 - 2 cosine`. They are one direction-only/no-reweighting reference cell, not two independent observations. Any difference between those two implementations is a numerical or coding defect and is reported as a QA failure, not as an effect.

The proposed metric is the raw weighted-distance cell. Cosine is the normalized uniform dot/cosine cell. Uniform L2 is the raw uniform-distance cell. All cells use the same train/validation/test records, class prototypes, decision rule, and primary balanced-accuracy endpoint.

## Primary contrasts (table: contrast | cells | the single factor it isolates | falsification rule)

| Contrast | Cells | Single factor isolated | Falsification rule |
|---|---|---|---|
| MAGNITUDE / F2' | `(raw, uniform, distance)` vs `(normalized, uniform, distance)` | Magnitude representation only; weighting and primitive are fixed | F2' fires if raw does not exceed normalized by **more than 1.0pp**. A 95% interval width >2pp is INCONCLUSIVE, never a kill or pass. |
| RELIABILITY | `(raw, weighted, distance)` vs `(raw, uniform, distance)` | Reliability weighting only; magnitude and distance are fixed | The reliability claim fails if the weighted-minus-uniform contrast is ≤1.0pp, or if its interval is >2pp wide. |
| PRIMITIVE | `(raw, uniform, distance)` vs `(raw, uniform, dot)` | Distance vs dot primitive only; magnitude and weighting are fixed | The distance-primitive claim fails if distance does not exceed raw dot by >1.0pp, or if its interval is >2pp wide. |

The three contrasts are the only primary C1 tests. The v1-style weighted-raw versus normalized-cosine comparison is retained as an exploratory factorial corner contrast and is forbidden as a primary endpoint. A primary contrast is decisive only when its paired 95% interval width is ≤2pp; otherwise report INCONCLUSIVE-UNDERPOWERED.

## Magnitude / reliability / primitive isolation protocol

For each required dataset, use 20 pre-registered stratified outer seeds with an 80/10/10 train/validation/test split. Deduplicate before splitting. Fit imputation, bounds, prototypes, sigma, shrinkage/floor, temperature/threshold, and calibration only on the applicable training/validation data. The test split is touched only for final balanced accuracy.

For every outer split:

1. Fit one prototype per class from the training records. Estimate each numeric/ordinal `sigma_j^2` from equal-class-weighted within-class residuals around those prototypes, with a fixed train-only variance floor. The uniform cell uses the same prototypes and `M=I`.
2. Evaluate all factorial cells on the same test records. For distance use negative squared distance; for dot use raw dot on raw vectors and cosine on row-normalized vectors. Do not infer a benefit from a different temperature: tune the common temperature and any binary threshold inside validation, but compare the primary argmax/decision rule identically.
3. Report balanced accuracy as the only primary metric. Top-1 retrieval, macro-F1, average precision, Brier/ECE, coverage, and abstention risk are exploratory and cannot upgrade a primary result.
4. Compute paired per-record differences within each test split, then bootstrap split-level effects. Report dataset-specific effects, pooled effects, and leave-one-dataset-out effects. A positive mechanism claim requires replication in at least two required datasets and no required dataset with a negative effect beyond 2pp.
5. Include a tuned logistic regression and a tuned gradient-boosted-tree baseline as hostile learned references, with matched nested-validation budgets. These are exploratory comparators: they do not replace any of the three isolated primary contrasts.

The magnitude verdict is not allowed to depend on reliability weighting or on replacing distance with dot. The reliability verdict is not allowed to depend on normalization. The primitive verdict is not allowed to depend on reweighting.

## C2 baseline-heterogeneity control (H_base measurement + homogenize-or-place, per dataset)

**Choice: homogenize the baseline, then place graded H above it.** Before any injection, measure `H_base = log(max(sigma_j^2 + floor) / min(sigma_j^2 + floor))` separately for Credit, COIL 2000, and authorized HELOC, using train-only outcome-conditioned residual variances. Publish the per-factor variance vector, H_base, confidence interval, and factor names.

For each split, add independent zero-mean bounded measurement noise to each factor until all factors have the same target variance `v* = max_j(sigma_j^2)` (or the smallest common target that makes the required perturbation feasible). Refit sigma from the homogenized training records, without giving the target variances to the scorer. The post-homogenization baseline is admissible only if `H_base_post ≤ 0.10` and its 95% interval width is ≤0.10. If a dataset cannot meet that condition without clipping-dominated distortion, mark its C2 heterogeneity law **UNTESTABLE** and do not report a confounded curve as evidence.

From that admissible homogeneous baseline, inject independent clipped Gaussian noise with fixed geometric-mean standard deviation and factor-spread levels `H_target ∈ {0, 0.5, 1.0, 1.5, 2.0}`. Randomly permute which semantic factors receive each spread at every draw. Re-measure H from the perturbed training data; the target schedule is not supplied to weighting. Use 20 seeds × 20 independent draws per dataset/level. The H=0 condition is the post-homogenization condition, not the uncorrected real-data condition.

The C2 primary quantity is the isolated RELIABILITY contrast (raw weighted distance minus raw uniform distance) at each measured H. The prediction is zero at genuine H=0 and a positive, nondecreasing gain as H increases. F3 fires if the homogeneous gain is as large as the high-H gain, the slope is non-positive, or the curve is materially non-monotone. Any dataset failing the post-homogenization admissibility test is C2 UNTESTABLE, not a flat-null result.

## Provenance plan (sources, hashes, dependency flags, provenance-vs-magnitude check)

| Dataset | Required source and access rule | Recorded provenance |
|---|---|---|
| Default of Credit Card Clients | Download the original UCI `.xls` from UCI dataset 350; do not use a GitHub/Kaggle mirror. | URL, retrieval date, byte count, SHA-256, UCI citation/DOI, and exact parser version. `xlrd` is an optional dependency and must be explicitly approved before installation; if not approved, STOP rather than silently substituting a CSV. |
| COIL 2000 | Download the official UCI dataset 125 archive and use the documented training target. | URL, retrieval date, byte count, SHA-256, archive member hashes, UCI citation/DOI, and the 5,822-row training count. |
| HELOC | Use an authorized local copy obtained under the FICO Explainable ML Challenge terms. Do not use a public mirror unless a reviewer explicitly approves its provenance. | Local access authorization record, source/access path, retrieval or receipt date, byte count, SHA-256, feature-map hash, and exact special-code policy. If no authorized copy is available, STOP the build; do not drop HELOC. |

No ACSIncome is required. If it is later cleared, it is external validation only and demographic/group features never enter scoring weights. Every dataset receives a `manifest.json` with source, license/access status, content hash, row/column counts, target prevalence, excluded columns, and parser/dependency versions.

To test provenance versus magnitude, report the three isolated contrasts separately by source class (official UCI Credit, official UCI COIL, authorized FICO HELOC), include a dataset × provenance interaction descriptively, and compare the v1 pattern without using provenance as a post-hoc explanation. A contrast that changes sign only with source/mirror status is a provenance failure, not evidence for H-TRUST. No pooled claim is accepted without the authorized-HELOC result.

## Scale-convention sensitivity + duplicate/group audit

The primary scale is train-fitted min-max to `[0,1]`. Repeat the entire three-contrast C1 analysis under two pre-registered train-only alternatives: robust quantile scaling using the 2nd/98th percentiles with clipping, and standardization using train mean/standard deviation. Row normalization occurs after each convention. Numeric/ordinal factor membership is unchanged.

The magnitude mechanism is scale-robust only if F2' passes with raw-minus-normalized >1pp and interval width ≤2pp under all three scale conventions in at least two required datasets. If it passes under one convention but not another, report MAGNITUDE SCALE-DEPENDENT and do not validate the magnitude claim. Reliability and primitive contrasts are reported by scale but cannot be redefined as the magnitude result.

Before splitting, perform exact-duplicate and near-duplicate audits on the primary numeric/ordinal matrix after a documented quantization. Publish counts removed and hashes of duplicate groups. Define a group as the exact feature-vector hash after quantization; where a source exposes a valid household/customer/application group, use that source group instead. Use a deterministic group-stratified split so no group crosses train/validation/test. If a dataset has no multi-record groups, report zero grouped records and retain the ordinary stratified split as the pre-registered fallback. Report the full-data and group-split results side by side; the primary result uses group splits whenever groups exist.

## Power (per contrast; stopping criterion)

Use 20 outer seeds per dataset for each of the three primary contrasts, with paired test records and identical splits across cells. The target is 80% power at two-sided alpha 0.05 for a 1.0pp paired balanced-accuracy effect using a conservative 4pp split-level standard deviation. Compute the realized minimum detectable effect from the pilot variance before interpreting the ranking.

For C2, use 20 seeds × 20 draws × five post-homogenization H levels per required dataset. Draws improve precision but are not counted as independent real datasets; the effective replication unit is the dataset/seed split. If any primary contrast has a 95% interval wider than 2pp, add the pre-registered extension to 40 seeds before conclusion. If it remains wider than 2pp, classify that contrast INCONCLUSIVE-UNDERPOWERED. No added datasets, favorable seeds, metrics, or H levels may be introduced after seeing effects.

## Confound register (delta from v1: what is newly closed)

All v1.1 confounds remain: unit-norm degeneracy, dataset artifact, sigma leakage, outcome leakage, cosine/uniform straw-man risk, scale choice, learned-baseline tuning, imbalance, injection-label contamination, total-noise confounding, schedule leakage, multiple testing, duplicate records, calibration, and underpowered nulls.

| New or strengthened confound | v2 closure |
|---|---|
| Magnitude and weighting changed together | Three-factorial design and primary raw-uniform-distance vs normalized-uniform-distance contrast isolate magnitude with reweighting off. |
| Magnitude and primitive changed together | Raw uniform distance vs raw uniform dot isolates primitive. |
| Reliability and magnitude changed together | Raw weighted distance vs raw uniform distance isolates reliability. |
| Unit-sphere L2/cosine duplicate cell | Normalized-uniform distance and dot are one reference cell; no double counting. |
| Intrinsic H made H=0 non-homogeneous | Measure H_base, homogenize, re-measure, and mark failure UNTESTABLE rather than interpreting a confounded curve. |
| Official/mirror provenance | Authoritative UCI sources and authorized HELOC are required; hashes and source interactions are recorded. |
| Scale convention manufactures magnitude | Min-max, robust-quantile, and standardized sensitivity are pre-registered; magnitude must be consistent. |
| Duplicate or group contamination | Exact/near-duplicate hashes and deterministic group splits are performed before evaluation, with counts published. |
| Learned reweighting disguised as reliability test | Sigma is the only weighting change in the primary reliability contrast; no learned model or product scorer supplies weights. |

## Self-check (one line: could this ONLY produce the answer we want?)

**No: each mechanism has a one-factor control, the direction-only anchor is explicit, homogeneous H is verified before C2, authoritative provenance and group/scale failures can invalidate the run, and every contrast can return INCONCLUSIVE.**

## Open questions for reviewer

- Approve `xlrd` for parsing the authoritative UCI `.xls`, or specify an approved stdlib-compatible parser; the build must stop if neither is approved.
- Confirm the authorized HELOC access path and whether hashes/derived split metadata may be published without redistributing the data.
- Confirm whether exact feature-vector grouping is sufficient for each dataset or whether a source-specific group key is available.
- Confirm the post-homogenization admissibility thresholds (`H_base_post ≤0.10`, interval width ≤0.10) before Stage 3; these thresholds are intended to prevent a confounded C2 result, not to guarantee a positive one.
- Confirm whether the robust-quantile and standardized sensitivity runs should be full 20-seed runs or the same pre-registered 40-seed stopping extension when intervals are wide.
