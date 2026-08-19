# H-TRUST design v1

This is a falsification-first design. The existing centroidal-synthetic results are not a target for replication; they are treated as potentially circular evidence. The primary unit is a labeled real record represented by bounded, interpretable, magnitude-bearing features. A record is a node, and class prototypes are learned only from the training partition.

## Kill experiment (F2 normalize-control)   — what runs first, and the decision rule

Run this before C1 or C2. Use the first three datasets below, with the same fixed train/validation/test splits, feature inclusion, missing-value rules, prototype construction, and seeds used by the main experiment.

1. Fit feature bounds and preprocessing on the training split only. Map each retained numeric/ordinal feature to `[0,1]` using training bounds; retain the resulting vector without row normalization. Exclude IDs and protected/group fields from the primary score, but retain them for subgroup reporting.
2. Fit class prototypes and diagonal reliability weights on training records only. For each factor, estimate outcome-conditioned noise from within-class training residuals around the class prototype; pool class variances with equal class weight and use a pre-registered variance floor. No validation or test labels enter the weights.
3. Evaluate the weighted metric, uniform L2, and tuned cosine on the original magnitude-bearing vectors. Then row-normalize every vector, including prototypes, and re-fit the diagonal weights on normalized training vectors only. Re-run the same retrieval/decision evaluation on normalized vectors. Tuning is nested and identical across methods.
4. The primary endpoint is paired test balanced accuracy; secondary endpoints are top-1 prototype retrieval accuracy, macro-F1, average precision where the class is imbalanced, and calibration error. Report paired per-record differences and 95% bootstrap confidence intervals.

Decision rule, fixed before inspection:

- **F2 falsifies the magnitude-driven claim** if the weighted metric beats tuned cosine on the normalized control by more than 1.0 percentage point in pooled balanced accuracy and its 95% paired interval excludes zero, with the same direction in at least two datasets. This is a kill, even if C1 later looks positive.
- If the normalized weighted metric is within ±1.0pp of cosine, call the control a null/equivalence result and continue. If both collapse to the same ranking, report the mathematical unit-sphere degeneracy rather than claiming a kernel win.
- F1 is evaluated on the unnormalized primary condition: if tuned cosine is within ±1.0pp of the weighted metric, with the interval containing zero in the pooled estimate and no dataset-specific positive replication, cosine is adequate within this regime.

The normalized control is not the main comparison: uniform squared L2 and cosine are monotone-equivalent on unit-normalized vectors. Its sole purpose is to test whether any apparent advantage survives after the magnitude channel is removed.

## Datasets                                  — table: name | source | size | features | sigma source | fit

| Name | Source | Size | Features | Sigma source | Fit to the regime |
|---|---|---:|---|---|---|
| Default of Credit Card Clients | [UCI dataset 350](https://archive.ics.uci.edu/dataset/350/default%2Bof%2Bcredit%2Bcard%2Bclients), DOI `10.24432/C55S3H` | 30,000 records, 23 explanatory variables | Credit limit; age; education/marital indicators; six monthly repayment-status fields; six bill amounts; six payment amounts. Keep numeric/ordinal fields with documented meaning; encode categorical fields as bounded one-hot blocks in a pre-registered sensitivity analysis. | Default-payment label; equal-class-weighted within-default/non-default residual variances around training prototypes, with a train-only floor. | Large real credit-risk sample with genuinely different units and magnitudes. The next-month default label is observed after the features and is not manufactured by the experiment. |
| Insurance Company Benchmark (COIL 2000) | [UCI dataset 125](https://archive.ics.uci.edu/dataset/125), DOI `10.24432/C5630S` | 9,000 customers; 86 variables; the official files separate training descriptions and an evaluation target file | Product-usage counts, socio-demographic attributes, and area-code-derived customer descriptors; retain documented integer/count variables and one-hot categorical blocks, excluding identifiers. | Caravan-policy target in the supplied training target; estimate within-target residual noise on training customers only. The organizer-held evaluation labels are never used for fitting. | Real insurance-company customer data and an insurance-product outcome; it is a hostile test because the positive class is sparse and many fields are weak or categorical. |
| FICO Explainable ML Challenge HELOC | [FICO challenge description](https://community.fico.com/s/explainable-machine-learning-challenge); public task description also available through [IBM AI Explainability 360](https://aix360.factsheets.vpc.res.ibm.com/data) | 10,459 applications; 23 credit-report variables | External risk estimate, trade-history ages, satisfactory-trade counts, delinquency counts, utilization/inquiry measures, and other credit-report quantities. Preserve documented special codes as missing/explicit states; do not silently turn them into evidence. | `RiskPerformance` timely-payment outcome; class-conditional residual variances are fit on training applicants only after a fixed special-code policy. | Real anonymized HELOC applications with interpretable, magnitude-bearing credit-report features. Access/redistribution terms must be checked before release; the experiment may use an authorized local copy. |
| ACSIncome (external validation, optional if license/access permits) | [Folktables repository and task definition](https://github.com/socialfoundations/folktables), [datasheet](https://github.com/socialfoundations/folktables/blob/main/datasheet.md) | 1,664,500 datapoints in the published ACSIncome task; 10 features | Age, class of worker, education, marital status, occupation, birthplace, relationship, hours worked, sex, and race; the target is income above $50,000. Use only the permitted Census/ACS extract and document survey year/state. | Above-threshold-income label; train-only within-label residual variances. Do not use group membership for scoring weights; report subgroup performance separately. | A high-powered bounded public-population validation with interpretable numeric/ordinal features. It is deliberately not a credit/insurance duplicate and can expose a domain-specific artifact. |

Dataset inclusion rules: the first three are required; ACSIncome is a fourth validation set, not a replacement. The experiment must publish exact release/version, download hash, row filtering, feature map, target prevalence, and license/access constraints. No synthetic generator, centroidal resampling, planted near-duplicate, or target-derived feature is permitted.

## Baselines                                  — table: baseline | how it gets a fair shot

| Baseline | How it gets a fair shot |
|---|---|
| Tuned normalized cosine | Row-normalize the same train-fitted bounded feature vectors; tune temperature and classification/retrieval threshold on an inner validation fold. Use the same prototypes, candidate set, class priors, and test records as the proposed metric. Temperature is not fixed at the value that makes cosine look weak. |
| Uniform-weight L2 | Use the same bounded, non-row-normalized vectors and prototypes with `M=I`. Tune only temperature/decision threshold in the same inner folds. This isolates reliability weighting from the distance primitive. |
| Reliability-weighted diagonal metric | Use `M=diag(1/sigma_j^2)` from train-only outcome-conditioned residual estimates. Pre-register the variance floor and any shrinkage; tune only the common temperature and decision threshold. Do not tune weights on test outcomes. |
| Logistic regression | One-hot/ordinal preprocessing, train-only scaling, regularization selected by nested validation, class weighting selected inside the inner loop, and probability calibration fit only on validation data. Report both accuracy and calibration. |
| Gradient-boosted trees | A standard existing-dependency implementation with depth, learning rate, estimators, and class weighting selected by nested validation. It receives the same raw semantic fields, train-only imputation, and the same held-out test set. Feature engineering must be shared or explicitly reported. |
| Optional small GNN / graph baseline | Only if a graph relation is available from the dataset rather than invented from labels. Use the same node split and feature matrix, forbid label-derived edges, tune architecture on validation, and treat this as supplemental—not a required comparator for tabular C1. |

All methods receive the same records, folds, class-prior information available at prediction time, and abstention policy. Hyperparameter budgets are matched by the number of validation configurations and compute budget. No baseline is allowed to see the test labels, test-derived bounds, or metric-derived features.

## C1 protocol

**Question.** On real magnitude-bearing data, does train-only outcome-conditioned diagonal reliability weighting improve decisions over tuned cosine and uniform L2?

**Splits and unit of analysis.** For each dataset, make five repeated stratified outer splits (80/10/10 train/validation/test), with a fixed list of 20 outer seeds shared by all methods; use the first five for the required run and the remaining seeds as a registered extension if the confidence interval is wide. Where the official COIL split is used, preserve it as an external test and create only the training-side validation split. Do not mix customers across repeated longitudinal identities if a source release exposes them.

Within each outer split:

1. Fit imputation, category encoding, bounded scaling, prototypes, `sigma`, temperature, threshold, and calibration using training and inner-validation data only as appropriate.
2. Construct one prototype per outcome class from training records. Score each test record with `softmax(-gamma * (q-k)^T M (q-k))`; the predicted decision is the highest-scoring class, with a pre-registered abstention rule based on the validation margin. The same decision rule is applied to all methods.
3. Report balanced accuracy as primary because COIL and credit outcomes are imbalanced. Report top-1 retrieval, macro-F1, average precision, Brier score/ECE, coverage, and the abstention-risk curve as secondary outcomes.
4. Use paired bootstrap over test records within each outer split, then a random-effects meta-analysis across dataset/split cells. The primary effect is weighted-metric minus tuned-cosine balanced accuracy; a secondary contrast is weighted-metric minus uniform L2.
5. A positive C1 result requires the pooled 95% interval to exclude zero, at least two of three required datasets to have positive point estimates, and no required dataset to show a large negative effect (>2pp). Otherwise report C1 as unresolved or negative, not validated.

The magnitude-bearing condition is the paper's main claim. The row-normalized condition is reported only as the F2 control and is never pooled into the main C1 effect.

## C2 protocol (heterogeneity law)           — measurement, variation, predicted curve

**Measurement.** On every training split, estimate `sigma_j^2` from outcome-conditioned within-class residuals around the training prototypes, using equal class weights so prevalence cannot manufacture heterogeneity. Define the pre-registered heterogeneity index

`H = log(max_j(sigma_j^2 + floor) / min_j(sigma_j^2 + floor))`.

Also report the coefficient of variation of the per-factor variances and the effective reliability concentration (normalized inverse-variance entropy). H is the primary index; the others are robustness summaries. The proposed metric uses the same train-only estimates, with a fixed shrinkage rule selected before seeing test results.

**Variation on real data.** C2 starts from each real training/test split and injects independent, zero-mean, feature-specific measurement noise after the train-fitted `[0,1]` mapping and before fitting prototypes. Use a clipped uniform perturbation (primary) and clipped Gaussian perturbation (robustness), with clipping to the feature's train-fitted bounds. Keep the geometric mean of the injected standard deviations fixed while varying the ratio across factors:

`H_injected ∈ {0, 0.25, 0.50, 1.00, 1.50, 2.00}`,

with `sigma_j = sigma_geo * exp(z_j)` and `z_j` centered to mean zero. Randomly permute which semantic factors receive high noise at each replicate, preserving the same multiset of noise levels. Use at least 20 noise draws per split/level. Labels remain the untouched real outcomes; the perturbation is a measurement-error stress test, not a new synthetic label generator. At `H=0`, every factor receives the same noise scale and the reliability-weighted metric is expected to collapse to uniform L2 up to estimation noise.

**Predicted curve and falsification.** Plot the paired gain in balanced accuracy of weighted metric over uniform L2 and over tuned cosine against measured `H`, with one point per dataset/split/noise draw and a pre-registered mixed-effects slope. The prediction is a gain approximately zero at homogeneous noise, positive and nondecreasing as heterogeneity increases, with possible saturation at high H. Fit a monotone constrained trend only as a descriptive secondary analysis; the primary test is an interaction between method and H with dataset/split random intercepts.

- F3 falsifies the heterogeneity law if the slope is non-positive, the curve is materially non-monotone after uncertainty is included, or the homogeneous gain is as large as the heterogeneous gain.
- A positive result requires the homogeneous estimate to be within ±1pp of zero, the highest-H estimate to exceed it by at least 1pp with a 95% interval excluding zero, and the direction to replicate in at least two required datasets.
- Re-estimate `sigma` from perturbed training data only at every level. Never use the known injected noise scale as the model's weight; it is used only to label the experimental condition and audit estimator recovery.

## Confound register                         — table: confound | design element that rules it out

| Confound | Design element that rules it out |
|---|---|
| Unit-norm degeneracy / the F2 kill is non-experimental | Main C1 uses non-normalized bounded features. F2 separately row-normalizes all vectors and applies the explicit equivalence/kill rule; no claim is based on “L2 versus cosine” on the unit sphere. |
| Dataset artifact or one benchmark carrying the claim | Three required, materially different public datasets plus ACSIncome external validation; paired per-dataset effects, leave-one-dataset-out summary, and no pooled result without dataset-level replication. |
| Sigma-estimation leakage | Bounds, prototypes, imputation, sigma, shrinkage, temperatures, thresholds, and calibration are fit within each training/inner-validation fold. Test labels and test-derived distribution statistics are forbidden. |
| Outcome leakage through feature construction | Exclude IDs, post-outcome fields, target encodings, and future measurements; publish a feature audit and timestamp/ordering rule. Any disputed feature is removed in the primary analysis and restored only in sensitivity analysis. |
| Cosine straw man | Tune cosine temperature/threshold and use identical prototypes, candidate sets, splits, and abstention tuning. Compare against the best validation-selected cosine, not a fixed default. |
| Uniform L2 straw man | Use identical bounded features/prototypes and tune its temperature/threshold. This is the direct no-reliability-weight control. |
| Scale choice manufactures the result | Primary scaling is train-fitted documented-range min-max; repeat with robust quantile bounds and raw-unit standardized sensitivity. The conclusion must not depend on one scale convention. |
| Learned baseline gets less tuning | Nested validation, matched hyperparameter budgets, class weighting, calibration, and the same held-out records for logistic and GBT. |
| Class imbalance makes accuracy misleading | Balanced accuracy is primary; report macro-F1, average precision, per-class recall, calibration, coverage, and prevalence. |
| Noise injection changes label semantics | Labels remain the original public outcomes; perturbations are clipped measurement error on features only, with independent draws, fixed geometric mean, and an unperturbed real-data C1. |
| Heterogeneity is confounded with total noise | Hold geometric mean injected noise fixed while varying only the per-factor spread; report the measured total scale and heterogeneity separately. |
| Sigma estimator simply recovers the known injection schedule | The estimator sees only train records and labels; the injected schedule is not supplied to it. Recovery calibration is reported as a diagnostic, not used in scoring. |
| Multiple testing / favorable dataset selection | Register all datasets, seeds, endpoints, H levels, and decision margins before execution. The primary result is one pooled contrast and one interaction; all other plots are labeled exploratory. |
| Underpowered null | Power plan below requires repeated paired cells and reports the minimum detectable effect; a wide interval is “inconclusive,” never a pass. |
| Contamination from duplicate or related records | Deduplicate using source identifiers before splitting; where household/customer grouping exists, group-split. Publish counts removed. |
| Metric wins by being overconfident | Treat accuracy and calibration as separate channels; report ECE/Brier and reliability diagrams. A sharper but badly calibrated metric cannot be described as uniformly better. |

## Power                                     — seeds/sizes + reasoning

Use 20 pre-registered outer seeds per dataset for the full study, with five required seeds as a smoke run that cannot support a paper conclusion. The first three datasets provide approximately 30,000, 9,000, and 10,459 records respectively; use all eligible records after leakage-safe filtering, with 10% held-out test per outer split. ACSIncome, if used, provides a large external sample but is not allowed to compensate for a negative result on the required datasets.

For each dataset and outer seed, evaluate the same test records under all methods, yielding paired differences rather than independent accuracy estimates. For C2, use six heterogeneity levels, 20 independent perturbation draws, and the same 20 outer seeds: 120 paired condition cells per dataset before the mixed-effects aggregation. The expected effective sample size is the number of independent outer split/dataset cells, not the raw number of noise draws; noise draws improve precision of the stress curve but do not create independent real datasets.

The design target is 80% power at two-sided alpha 0.05 to detect a 1.0pp pooled paired balanced-accuracy difference, assuming a conservative 4.0pp standard deviation of split-level paired effects and moderate cross-dataset correlation; exact power must be recomputed from pilot variance before the run. If the observed split-level variance makes the minimum detectable effect greater than 1.0pp, increase seeds to 40 per dataset or declare the result underpowered before inspecting the method ranking. For F2 and F3, the ±1pp equivalence margin is meaningful only when the 95% interval width is no more than 2pp; otherwise the result is inconclusive.

Power is therefore a stopping criterion, not a license to add favorable datasets or seeds after seeing results. A null with a narrow interval is a real null; a null with a wide interval is explicitly unresolved.

## Self-check                                — the one-line answer

Could this design ONLY produce the answer we want? **No: the first-run F2 normalization control can kill the magnitude story, tuned cosine and learned baselines can win, the homogeneous C2 point is pre-registered to be zero, and dataset-level replication is required.**

## Open questions for reviewer               — anything you were unsure about

- Confirm whether the HELOC challenge agreement permits redistribution of derived splits, summary statistics, and exact feature maps in the paper's artifact; otherwise retain it as a locally reproducible validation set with a documented access path.
- Confirm whether the paper wants one-hot categorical blocks in the primary metric or a numeric/ordinal-only primary with one-hot sensitivity. The choice affects the interpretation of “factor” and therefore sigma heterogeneity.
- Confirm the 1pp equivalence margin against the paper's intended practical decision cost; the design treats it as a provisional pre-registration value, not an observed effect.
- Confirm whether ACSIncome's demographic features may be used for the scientific benchmark under the project's ethics and data-use review. They are excluded from scoring weights if included.
- Confirm whether the primary outcome should remain balanced accuracy or be replaced by a domain-specific cost-weighted decision metric; whichever is chosen must be fixed before the first result.
