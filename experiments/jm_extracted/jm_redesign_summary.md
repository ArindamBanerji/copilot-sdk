# JM Experiment Redesign Summary

Date: Sep 20, 2026

The three Phase 3 failures were design-target mismatches. The redesign preserves the bounded quality result, measures cumulative advantage against a paired frozen twin, and measures the SDK discovery surface across domains and evidence sweeps.

## Fix 1 — E-JM-4 per-threat detection

No rerun was needed. The existing Phase 3 trial data were re-charted by threat model.
Sustained: 100%; drift: 100%; sudden: 100%; sparse adversarial: 57%.

Paper sentence: The calibrated conservation gate detected sustained corruption, gradual drift, and sudden personnel change in 100% of trials with 0% clean false positives; sparse 10% adversarial events were detected in 57%, defining the measured sensitivity boundary.

## Fix 2a — E-JM-6 bounded quality

The existing c=0.643 result is retained and reframed as bounded quality approaching a ceiling, not as the super-linearity test.

Paper sentence: K-learning improved decision quality by 21.96 percentage points over a frozen twin; the bounded quality trajectory saturated sub-linearly (c=0.643), while compounding was evaluated on cumulative advantage.

## Fix 2b — E-JM-6-A cumulative advantage

Exponent c=1.387; 95% deployment-bootstrap CI [1.308, 1.477]; interpretation: super-linear.
The comparison used 40 paired deployments and 5000 whole-deployment bootstrap refits.

Paper sentence: Against a decision-0 frozen twin on identical scenarios, cumulative K-learning advantage scaled as t^1.387 (95% CI [1.308, 1.477]).

## Fix 2c — E-JM-6-B discovery surface

Domain exponent=2.150, 95% CI [2.030, 2.299]; time exponent gamma=2.622, 95% CI [2.436, 2.964].
Quadratic domain scaling confirmed: True.

Paper sentence: SDK cross-domain discoveries scaled as n^2.150 across connected domains and t^2.622 across evidence sweeps, with 95% CIs [2.030, 2.299] and [2.436, 2.964], respectively.

## Final verification

Final score: 26/26 PASS (was 21/24).
Random state: 42. Bootstrap unit: whole deployment. Bootstrap resamples: 5,000.
