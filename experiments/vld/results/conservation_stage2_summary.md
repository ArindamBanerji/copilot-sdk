# Conservation Stage 2 — Composite Gate What-If

Simulation-only; no production gate change.

## 1. Five-regime × five-copilot comparison

| Regime | Copilot | clean_pause_rate | lag slow | lag poison | poison detection | fast-break detection | adopted |
|---|---|---:|---:|---:|---:|---:|---|
| R0_absolute | dataops | 24.7% | 217.5 | 50.666666666666664 | 100.0% | 66.7% | False |
| R0_absolute | trading | 1.3% | missed | 90.66666666666667 | 100.0% | 0.0% | False |
| R0_absolute | purchasing | 45.9% | 0 | 11.333333333333334 | 100.0% | 100.0% | False |
| R0_absolute | soc | 0.7% | missed | 90.33333333333333 | 100.0% | 0.0% | False |
| R0_absolute | s2p | 1.6% | 328 | 40 | 100.0% | 33.3% | False |
| R1_per_domain | dataops | 4.3% | missed | 93 | 100.0% | 0.0% | False |
| R1_per_domain | trading | 4.1% | missed | 79 | 100.0% | 0.0% | False |
| R1_per_domain | purchasing | 2.9% | missed | 49.333333333333336 | 100.0% | 33.3% | False |
| R1_per_domain | soc | 3.5% | missed | 79 | 100.0% | 0.0% | False |
| R1_per_domain | s2p | 4.5% | 169 | 34 | 100.0% | 33.3% | False |
| R2_relative | dataops | 0.0% | missed | missed | 0.0% | 0.0% | False |
| R2_relative | trading | 0.0% | missed | missed | 0.0% | 0.0% | False |
| R2_relative | purchasing | 0.0% | missed | missed | 0.0% | 0.0% | False |
| R2_relative | soc | 0.0% | missed | missed | 0.0% | 0.0% | False |
| R2_relative | s2p | 0.0% | missed | missed | 0.0% | 0.0% | False |
| R3_composite_audit | dataops | 4.3% | missed | 93 | 100.0% | 0.0% | False |
| R3_composite_audit | trading | 4.1% | missed | 79 | 100.0% | 0.0% | False |
| R3_composite_audit | purchasing | 2.9% | missed | 49.333333333333336 | 100.0% | 33.3% | False |
| R3_composite_audit | soc | 3.5% | missed | 79 | 100.0% | 0.0% | False |
| R3_composite_audit | s2p | 4.5% | 169 | 34 | 100.0% | 33.3% | False |
| R4_composite_trigger | dataops | 29.3% | 12.666666666666666 | 4.333333333333333 | 100.0% | 100.0% | False |
| R4_composite_trigger | trading | 6.3% | 33.666666666666664 | 38.666666666666664 | 100.0% | 100.0% | False |
| R4_composite_trigger | purchasing | 11.3% | 10.333333333333334 | 20 | 100.0% | 100.0% | False |
| R4_composite_trigger | soc | 32.3% | 3.3333333333333335 | 42 | 100.0% | 100.0% | False |
| R4_composite_trigger | s2p | 6.5% | 37.666666666666664 | 26.666666666666668 | 100.0% | 33.3% | False |

## 2. Adopt/reject verdict

R3 adopted copilots: none. Rejected: dataops, trading, purchasing, soc, s2p.
Adoption requires both axis 1 and axis 2; poison detection is compared with the R0 absolute-floor reference.

## 3. Ablation contribution

R1 measures calibrated absolute-floor benefit; R2 measures relative-change benefit; R3 requires both and keeps PSI non-blocking. The JSON contains per-copilot calibration floors and all per-seed outcomes.

## 4. PSI audit versus trigger

R3 treats PSI ≥ 0.10 as an audit warning. R4 makes it blocking; the comparison table shows whether fast-break detection improves and whether clean pauses increase.

## 5. Recommendation

Test **R3_composite_audit** in any future operator-approved follow-up, using each copilot's calibrated floor, a 0.30 relative-drop guard, and PSI ≥ 0.10 as audit-only. This artifact does not authorize adoption.

## 6. Remaining failures

Any rejected copilots and failed axes are explicit in the JSON aggregate fields; missed sustained poisoning or slow drift remains a rejection even when clean pauses improve.

## 7. §5 conservation paper sentence

In a geometry-derived, simulated five-copilot study, a per-domain calibrated accuracy floor combined with a 30% relative-change guard reduced domain-specific false pauses while preserving the absolute-floor poisoning-detection reference for accepted copilots; PSI was retained as an audit signal because making it blocking did not establish a uniform fast-break benefit without additional false pauses.
