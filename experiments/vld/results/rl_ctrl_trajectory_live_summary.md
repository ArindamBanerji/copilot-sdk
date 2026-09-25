# RL-CTRL-1b v3 — redesign gate

## Controller knob

The natural knob is the per-update `KUtilityStore.update_weights()` pair `lr_pos`/`lr_neg`, defaulting to 0.02/0.005. K initializes at 0.5, correct informative reads add `lr_pos` ( doubled on a flip), incorrect reads subtract `lr_neg`, and weights are bounded to 0.1–3.0.

## Sanity gate

SOC matches the recorded KE-1 endpoint at N=500 (0.810 vs 0.810). DataOps does not (0.570 vs 0.630; 6.0pp). The corrected formula and canonical evaluation stream fix the SOC mismatch, but the available DataOps endpoint remains inconsistent with the replicated protocol. A1/A2 were not run, as required.

## Why v1/v2 were invalid

CTRL-1 used post-hoc smoothing. CTRL-1b used eta as the negative learning rate, updated non-informative dimensions after correct outcomes, and used different evaluation/training streams. v3 corrects those elements but cannot safely resolve the remaining DataOps target mismatch without the original matched KE-1 per-checkpoint cases/provenance.

Verdict: no live controller thesis conclusion.
