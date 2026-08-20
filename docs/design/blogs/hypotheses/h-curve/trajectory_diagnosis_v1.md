# H-CURVE trajectory diagnosis v1

This is a descriptive shape diagnosis only. It reads persisted distance trajectories and
centroid snapshots under
graph-attention-engine-v50/experiments/h_curve_parametric_regen/raw/. It does not compute γ,
compare phase rates, evaluate the binary prediction, or import the scorer.

Definitions used here:

- d0 is the first persisted distance; d_min and d_final are the minimum and final values.
- d_inf is the mean of the final 20% of the trajectory.
- Raw increases count positive consecutive increments.
- Smoothed increases count positive increments in trailing rolling means after the window
  is full, for windows 10 and 25.
- The descent-band increment sigma is computed before the decision at which d_min occurs;
  the plateau-band sigma is computed over the final 20%.
- N_settle is the first decision whose distance is within d_inf + one plateau-band sigma.
  It is descriptive only and is never ratioed across phases.

## Per-cell shape table

Each row is one of the 18 persisted phase trajectories. The regime is cold_start for every
trajectory.

| Seed | ε | Phase | d0 | d_min @ decision | d_final | d_inf | d_inf/d0 | Raw increases | Smooth increases w10 / w25 | Noise σ descent / plateau | Observed changed / 144 | Static final-error fraction | N_settle |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 42 | 0.05 | 1 | 0.05051 | 0.04887 @5 | 0.19277 | 0.18376 | 3.638 | 214 | 270 / 274 | 0.000315 / 0.000849 | 24 / 144 | 0.056 | 1 |
| 42 | 0.05 | 2 | 0.40841 | 0.38982 @116 | 0.40138 | 0.40749 | 0.998 | 151 | 146 / 147 | 0.001139 / 0.001017 | 24 / 144 | 0.385 | 1 |
| 42 | 0.20 | 1 | 0.20021 | 0.19090 @46 | 0.22342 | 0.22183 | 1.108 | 173 | 201 / 219 | 0.000443 / 0.000564 | 24 / 144 | 0.668 | 1 |
| 42 | 0.20 | 2 | 0.40901 | 0.38526 @179 | 0.39497 | 0.39982 | 0.978 | 152 | 123 / 123 | 0.000958 / 0.001031 | 24 / 144 | 0.549 | 75 |
| 42 | 0.35 | 1 | 0.35045 | 0.32746 @94 | 0.33574 | 0.33685 | 0.961 | 282 | 286 / 277 | 0.000408 / 0.000357 | 24 / 144 | 0.906 | 54 |
| 42 | 0.35 | 2 | 0.48115 | 0.45608 @528 | 0.46715 | 0.46253 | 0.961 | 279 | 253 / 216 | 0.000791 / 0.000778 | 24 / 144 | 0.673 | 495 |
| 123 | 0.05 | 1 | 0.05087 | 0.05087 @1 | 0.19796 | 0.18801 | 3.696 | 206 | 273 / 274 | 0.000000 / 0.000928 | 24 / 144 | 0.053 | 1 |
| 123 | 0.05 | 2 | 0.40723 | 0.39442 @83 | 0.40600 | 0.40585 | 0.997 | 141 | 133 / 121 | 0.001055 / 0.001076 | 24 / 144 | 0.401 | 41 |
| 123 | 0.20 | 1 | 0.19981 | 0.19385 @44 | 0.23533 | 0.23577 | 1.180 | 170 | 200 / 230 | 0.000549 / 0.000698 | 24 / 144 | 0.602 | 1 |
| 123 | 0.20 | 2 | 0.42252 | 0.41215 @275 | 0.41328 | 0.41464 | 0.981 | 142 | 130 / 119 | 0.000929 / 0.000753 | 24 / 144 | 0.598 | 234 |
| 123 | 0.35 | 1 | 0.34968 | 0.32972 @171 | 0.34231 | 0.34398 | 0.984 | 275 | 283 / 300 | 0.000475 / 0.000441 | 24 / 144 | 0.871 | 15 |
| 123 | 0.35 | 2 | 0.49530 | 0.47951 @427 | 0.48183 | 0.48563 | 0.980 | 288 | 259 / 250 | 0.000692 / 0.000676 | 24 / 144 | 0.757 | 195 |
| 777 | 0.05 | 1 | 0.05006 | 0.04943 @11 | 0.18648 | 0.18646 | 3.724 | 195 | 260 / 271 | 0.000642 / 0.001198 | 24 / 144 | 0.060 | 1 |
| 777 | 0.05 | 2 | 0.39768 | 0.38195 @146 | 0.38504 | 0.38795 | 0.976 | 141 | 127 / 125 | 0.000955 / 0.001077 | 24 / 144 | 0.447 | 97 |
| 777 | 0.20 | 1 | 0.19953 | 0.18806 @62 | 0.22169 | 0.21766 | 1.091 | 154 | 193 / 199 | 0.000492 / 0.000570 | 24 / 144 | 0.678 | 1 |
| 777 | 0.20 | 2 | 0.43834 | 0.40042 @274 | 0.40800 | 0.40512 | 0.924 | 138 | 110 / 80 | 0.000835 / 0.000830 | 24 / 144 | 0.616 | 257 |
| 777 | 0.35 | 1 | 0.34965 | 0.32408 @158 | 0.33520 | 0.33358 | 0.954 | 289 | 310 / 304 | 0.000374 / 0.000350 | 24 / 144 | 0.909 | 54 |
| 777 | 0.35 | 2 | 0.50544 | 0.47518 @557 | 0.47763 | 0.48089 | 0.951 | 284 | 241 / 196 | 0.000710 / 0.000636 | 24 / 144 | 0.772 | 350 |

## Why the half-distance metric censored

All 18 phase trajectories have d_inf > 0.5*d0. Therefore the final-20%-plateau
diagnostic says a half-distance crossing is impossible for every persisted trajectory under
this fixed-fraction definition.

By cell, the counts are:

| ε | Cells with d_inf > 0.5*d0 | Phase trajectories with d_inf > 0.5*d0 |
|---:|---:|---:|
| 0.05 | 3 / 3 | 6 / 6 |
| 0.20 | 3 / 3 | 6 / 6 |
| 0.35 | 3 / 3 | 6 / 6 |
| **Total** | **9 / 9 cells** | **18 / 18 phases** |

The ε=0.05 Phase-1 trajectories rise from approximately 0.05 to approximately 0.19,
so their plateau is several times d0. The other trajectories begin with a short descent
but settle at roughly 0.92–1.00 of their initial distance in Phase 2 and roughly 0.95–1.18
in the ε=0.20/0.35 Phase-1 arms.

## Is the raw non-monotonicity just per-step noise around a decreasing smoothed trend?

**No for every cell under the pre-registered descriptive test.** None of the 18 trajectories
has a monotone-decreasing trailing rolling mean at either window 10 or window 25. Smoothing
does reduce raw increases in several Phase-2 trajectories, especially at ε=0.35, but it
does not turn the series into a monotone decreasing curve.

| Seed | ε | Phase | Raw increases | Smoothed increases w10 | Smoothed increases w25 | Smoothed decreasing at either window? |
|---:|---:|---:|---:|---:|---:|---|
| 42 | 0.05 | 1 | 214 | 270 | 274 | No |
| 42 | 0.05 | 2 | 151 | 146 | 147 | No |
| 42 | 0.20 | 1 | 173 | 201 | 219 | No |
| 42 | 0.20 | 2 | 152 | 123 | 123 | No |
| 42 | 0.35 | 1 | 282 | 286 | 277 | No |
| 42 | 0.35 | 2 | 279 | 253 | 216 | No |
| 123 | 0.05 | 1 | 206 | 273 | 274 | No |
| 123 | 0.05 | 2 | 141 | 133 | 121 | No |
| 123 | 0.20 | 1 | 170 | 200 | 230 | No |
| 123 | 0.20 | 2 | 142 | 130 | 119 | No |
| 123 | 0.35 | 1 | 275 | 283 | 300 | No |
| 123 | 0.35 | 2 | 288 | 259 | 250 | No |
| 777 | 0.05 | 1 | 195 | 260 | 271 | No |
| 777 | 0.05 | 2 | 141 | 127 | 125 | No |
| 777 | 0.20 | 1 | 154 | 193 | 199 | No |
| 777 | 0.20 | 2 | 138 | 110 | 80 | No |
| 777 | 0.35 | 1 | 289 | 310 | 304 | No |
| 777 | 0.35 | 2 | 284 | 241 | 196 | No |

The increment noise bands are small in absolute distance units, generally about
0.0003–0.0012, but the trajectory shape is not explained by a decreasing smoothed trend.

## Coverage finding — does partial tensor-cell updating inflate the Frobenius distance floor?

The persisted phase-start and phase-final centroid snapshots show 24 changed scalar entries
out of 144 in every phase, with 120 scalar entries observationally unchanged. For Phase 1,
the start is μ0; for Phase 2, the correct phase-local start is μ_phase1_final. The final-error
squared-distance fraction attributable to observationally unchanged entries ranges from:

- Phase 1: 0.053–0.909.
- Phase 2: 0.385–0.772.

Thus partial tensor updating materially inflates the observed Frobenius distance floor in most
trajectories, especially ε=0.20 and ε=0.35 Phase 1. It is not the sole explanation for
the ε=0.05 Phase-1 rise, where the unchanged-entry contribution is only about 5–6%.

Important limitation: the persisted artifacts do not contain per-decision centroid snapshots,
category/action assignments, or update masks. Therefore exact “ever received an update” counts
are NOT DETERMINED. The 24/144 figure is the reproducible count of scalar entries that changed
between the phase-start and phase-final snapshots, not a claim that exactly 24 entries were
ever touched. The static-error fractions are computed from the persisted final snapshot and
target only.

## One-paragraph shape summary

The persisted trajectories have a shallow, noisy shape rather than a clean exponential decay
to a low plateau. Several Phase-1 paths show a brief initial dip followed by a rise to a
higher plateau; Phase-2 paths generally show a modest descent followed by a broad plateau
near 0.92–1.00 of their starting distance. Rolling means reduce some step noise but remain
non-monotone at both windows across all 18 trajectories. The full-tensor Frobenius distance
also retains a substantial static component because only 24 of 144 scalar entries are
observably changed between phase snapshots. This diagnosis describes trajectory geometry
only and makes no claim about γ or theorem support.

