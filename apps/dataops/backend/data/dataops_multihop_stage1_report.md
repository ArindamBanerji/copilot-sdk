# DataOps Stage 1 Multi-Hop Evaluation

PLANTED / POSITIVE CONTROL — not a measurement of real production value.

## 1. Acceptance Test

Verdict: PASS

Headline comparison for score-keyed cases is VLD vs breadth. content_rule is reported as an oracle upper bound because it reads correct_branches directly.

| ρ | SP | breadth | content_rule | VLD | Δ(VLD−breadth) | Δ(VLD−SP) |
|---:|---:|---:|---:|---:|---:|---:|
| 0.30 | 0.500 | 1.000 | 1.000 | 0.000 | -1.000 | -0.500 |
| 0.50 | 0.000 | 0.200 | 1.000 | 0.200 | 0.000 | 0.200 |
| 0.70 | 0.125 | 0.250 | 1.000 | 1.000 | 0.750 | 0.875 |
| 0.90 | 0.500 | 0.250 | 1.000 | 1.000 | 0.750 | 0.500 |
| 1.00 | 0.750 | 0.500 | 1.000 | 1.000 | 0.500 | 0.250 |

## 2. Per-Kind Results

| Kind | SP | breadth | content_rule | VLD | N |
|---|---:|---:|---:|---:|---:|
| content_keyed | 0.267 | 0.533 | 0.800 | 0.800 | 15 |
| prerequisite | 0.700 | 0.500 | 1.000 | 1.000 | 10 |
| score_keyed | 0.320 | 0.400 | 1.000 | 0.680 | 25 |

## 3. Controls

- Flat controls: VLD=0.400, single_pass=0.400, pass=True.
- ρ=0.50 controls: VLD=0.200, near chance 0.20±0.15 pass=True.

## 4. Per-ρ Table

Same as §1; score-keyed subset only.

## 5. Comparison with SOC

- SOC: VLD=100.0% at ρ≥0.70 on score_keyed conditional scenarios.
- DataOps: VLD=100.0% at ρ≥0.70 on score_keyed conditional scenarios.
- Cross-copilot generalization holds: True.

## Headline

accuracy(VLD) at ρ≥0.70 on score_keyed = 1.000.
accuracy(VLD) - accuracy(breadth) on score_keyed = 0.280.
