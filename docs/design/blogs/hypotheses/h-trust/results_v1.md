# H-TRUST results v1

This report is the run of the corrected factorial instrument in `design_v2.md`, as amended by
`design_v2_1.md`. The experiment code is fresh and de-circularized: it is under
`experiments/htrust/` and does not import a product scorer. The primary endpoint is balanced
accuracy. Effects below are percentage-point differences (first cell minus second cell); the
95% intervals are bootstrap intervals over the 20 preregistered seeds unless otherwise noted.
The 1.0pp margin and 2pp interval-width rule are applied exactly as frozen.

## Kill experiment (F2) — fired? + number + reading

The run-first F2' contrast was `(raw, uniform, distance) - (normalized, uniform, distance)`.
The legacy v1 weighted-normalized comparison was not run because v2.1 replaces it and forbids
the multi-factor comparison as a primary endpoint.

| Dataset | Min-max | Robust-quantile | Standardized | Scale-robust F2' result |
|---|---:|---:|---:|---|
| Credit | +1.960pp [1.777, 2.144] | +0.452pp [0.240, 0.644] | +4.497pp [4.325, 4.669] | **Fails**: robust is below 1pp |
| COIL 2000 | +0.504pp [0.200, 0.836] | +0.669pp [0.157, 1.188] | −0.187pp [−1.007, 0.639] | **Fails**: none clears 1pp across scales |
| Adult | +11.058pp [10.688, 11.437] | +11.129pp [10.793, 11.477] | +0.457pp [0.276, 0.625] | **Fails**: standardized is below 1pp |

**F2' fires as a scale-robust magnitude test.** Only Adult has a large raw-versus-normalized
effect under two conventions; no required dataset clears the 1pp margin under all three scale
conventions. This does not mean every raw cell equals its normalized control: it means the
preregistered magnitude claim is not robust to the frozen scale sensitivity analysis. The raw
and normalized uniform-distance cells were fitted and evaluated on the same seed splits.

## C1 — table (metric vs baselines, per dataset, significance) + verdict

The three rows per contrast are the preregistered single-factor contrasts. A cell is decisive
only when its interval width is at most 2pp; `INC` means the frozen width rule prevents a
decision. Values are balanced-accuracy differences in pp.

| Contrast | Dataset | Min-max | Robust-quantile | Standardized |
|---|---|---:|---:|---:|
| Magnitude: raw uniform L2 − normalized uniform L2 | Credit | +1.960 [1.777,2.144] | +0.452 [0.240,0.644] | +4.497 [4.325,4.669] |
|  | COIL 2000 | +0.504 [0.200,0.836] | +0.669 [0.157,1.188] | −0.187 [−1.007,0.639] |
|  | Adult | +11.058 [10.688,11.437] | +11.129 [10.793,11.477] | +0.457 [0.276,0.625] |
| Reliability: raw weighted L2 − raw uniform L2 | Credit | +0.886 [0.617,1.165] | −0.708 [−0.841,−0.559] | −0.243 [−0.322,−0.157] |
|  | COIL 2000 | +1.005 [0.345,1.695] | −0.627 [−1.385,0.167] | +0.319 [−0.074,0.725] |
|  | Adult | +1.075 [0.944,1.191] | +0.305 [0.177,0.426] | −0.132 [−0.274,0.015] |
| Primitive: raw uniform L2 − raw uniform dot | Credit | +8.795 [8.431,9.177] | +12.346 [12.123,12.570] | +4.497 [4.325,4.669] |
|  | COIL 2000 | **INC** +4.722 [3.603,5.909] | +8.469 [7.540,9.385] | −0.187 [−1.007,0.639] |
|  | Adult | +22.391 [22.108,22.677] | +24.243 [23.996,24.488] | +0.457 [0.276,0.625] |

The normalized uniform-distance versus normalized uniform-dot QA anchor had zero mismatch in
all factorial rows (`qa_normalized_distance_dot_mismatch = 0`); a nonzero value would have been
a coding failure, not an effect.

**C1 verdict: INVALIDATED for the preregistered broad claim.** The isolated effects are not
scale-robust: the magnitude contrast fails the margin under at least one convention in every
dataset, reliability reverses sign or falls below 1pp across conventions, and the primitive
contrast is near zero under standardization. Some cells are strongly positive, especially Adult
under min-max/robust scaling, but those cells cannot be promoted to the scale-robust claim.

## C2 — heterogeneity curve (incl. homogeneous point) + verdict

The runner first measured native heterogeneity, then added per-factor noise to homogenize the
baseline and re-measured it. The frozen admissibility rule is `H_base_post <= 0.10` with interval
width `<= 0.10`. Credit and Adult passed every seed; COIL failed every seed (post values
0.183–0.275), so COIL is **C2 UNTESTABLE**, not a flat null.

| Dataset | H_base native (mean) | H_base post (mean; range) | Admissible? |
|---|---:|---:|---|
| Credit | 7.259 | 0.0437 (0.0277–0.0578) | Yes |
| COIL 2000 | 6.188 | 0.2187 (0.1828–0.2748) | No — C2 untestable |
| Adult | 1.685 | 0.0249 (0.0123–0.0461) | Yes |

For the admissible datasets, the table reports seed-level means (20 independent seeds), rather
than treating the 20 repeated draw cells per seed as independent observations. Effects are
reliability-weighted L2 minus uniform L2, in pp.

| Dataset | Injected H | Gain pp [95% seed CI] |
|---|---:|---:|
| Credit | 0.0 | −0.0156 [−0.0294,−0.0023] |
| Credit | 0.5 | −0.0215 [−0.0365,−0.0071] |
| Credit | 1.0 | −0.0194 [−0.0346,−0.0060] |
| Credit | 1.5 | −0.0132 [−0.0257,−0.0021] |
| Credit | 2.0 | −0.0113 [−0.0218,−0.0023] |
| Adult | 0.0 | −0.0003 [−0.0051,0.0048] |
| Adult | 0.5 | −0.0043 [−0.0083,−0.0003] |
| Adult | 1.0 | +0.0007 [−0.0081,0.0095] |
| Adult | 1.5 | −0.0053 [−0.0153,0.0051] |
| Adult | 2.0 | −0.0002 [−0.0111,0.0106] |

The fitted seed-level slope was +0.0034pp per H for Credit [−0.0017, +0.0083] and
−0.0002pp per H for Adult [−0.0056, +0.0057]. Neither is a positive, monotone law of the
preregistered size; both are far below the 1pp effect margin, and the homogeneous point is not
smaller in a meaningful increasing pattern.

**C2 verdict: INVALIDATED for the admissible datasets; COIL is untestable.** F3 fires because
the gain is flat/non-monotone and not larger at graded heterogeneity than at H=0. This verdict
is scoped to the homogenized-then-graded SL-1 protocol, as required; it is not a claim about
native COIL heterogeneity.

## Confound check — table: confound | held? | evidence

| Confound | Held? | Evidence |
|---|---|---|
| Unit-norm degeneracy | Yes | Primary raw cells were magnitude-bearing; the normalized uniform L2/dot anchor matched exactly (zero QA mismatch). Normalization was a control, not the main comparison. |
| Factor conflation | Yes | Primary contrasts changed exactly one factorial axis: magnitude, weighting, or primitive. The forbidden v1-style multi-factor comparison was not used as a primary endpoint. |
| Dataset artifact | No for the broad claim | Direction and size vary sharply by dataset and scale; Adult is large under two scales but near zero under standardization, while COIL is near zero/negative under standardization. |
| Sigma-estimation leakage | Yes | Prototypes, sigma/M, thresholds, and calibration were estimated from training splits; test balanced accuracy was held out. |
| Scale convention | Yes | All three contrasts were run under min-max, robust-quantile, and standardized scaling with 20 seeds each; the claim failed this hostile sensitivity requirement. |
| Native heterogeneity confounding C2 | Yes for Credit/Adult; no for COIL | Homogenization was followed by remeasurement. Credit and Adult met H_base_post <= 0.10; COIL did not and was marked untestable. |
| Duplicate/group contamination | Yes | Deterministic group splitting used quantized feature-vector groups where present; manifest records removed duplicate rows: Credit 56, COIL 651, Adult 227. |
| Provenance | Yes | All three archives were fetched from authoritative UCI origins and SHA-256 checked; no public mirrors or HELOC were used. The v1 provenance pattern cannot be tested because the frozen v2.1 dataset set excludes the v1 sources. |
| Underpowered null | Partly | C1 used 20 seeds per dataset × scale and all decisive C1 intervals were <=2pp; COIL primitive/min-max is explicitly inconclusive by width. C2 uses 20 seed-level units and remains a low-effect/flat result, while COIL is untestable by the preregistered H gate. |
| Outcome/feature circularity | Yes | No product scorer or centroidal-synthetic generator was reused; features and labels came from UCI archives and only train-split estimates were used. |

## Verdict — one line per claim with its tier and deciding number

- **F1 (cosine/dot adequacy): FIRED under the scale sensitivity control** — the raw primitive contrast is near zero under standardized scaling for all three datasets (Credit +4.497pp, COIL −0.187pp, Adult +0.457pp; only the first clears 1pp), so cosine adequacy cannot be rejected scale-robustly.
- **F2' (magnitude-driven advantage): FIRED** — no required dataset clears +1.0pp under all three scale conventions; the decisive failures are Credit robust +0.452pp, COIL standardized −0.187pp, and Adult standardized +0.457pp.
- **F3 (heterogeneity law): FIRED for the admissible SL-1 datasets** — Credit slope +0.0034pp/H and Adult slope −0.0002pp/H, with gains remaining approximately zero/negative across H; COIL is C2 UNTESTABLE because H_base_post mean was 0.2187.
- **C1: INVALIDATED** — the isolated metric effects are not robust across magnitude scale, reliability weighting, and primitive conventions under the 1pp rule.
- **C2: INVALIDATED on Credit and Adult; COIL UNTESTABLE** — no positive increasing gain-vs-H law survived baseline homogenization.

## Ledger + paper-map update

Raw outputs are saved in `experiments/htrust/v2_raw/`, with downloaded authoritative archives in
`experiments/htrust/v2_data/`. The run manifest records source URLs, byte counts, feature hashes,
archive SHA-256 hashes, row counts, and parser metadata. The approved `xlrd` dependency was
used only to parse the authoritative Credit `.xls` archive.

The H-TRUST ledger is marked **re-defining** rather than accepted: the preregistered C1/C2
claims did not survive the corrected instrument. The paper-map result tier remains **TBD** because
the acceptance condition was not met; the negative result is recorded here and in the ledger.
