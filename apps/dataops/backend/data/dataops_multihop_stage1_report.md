# DataOps Stage 1 Multi-Hop Evaluation

PLANTED / POSITIVE CONTROL — not a measurement of real production value.

## 1. Acceptance Test

Verdict: PASS

Headline comparison for score-keyed cases is VLD vs breadth. content_rule is reported as an oracle upper bound because it reads correct_branches directly.

| ρ | SP | breadth | content_rule | VLD | Δ(VLD−breadth) | Δ(VLD−SP) |
|---:|---:|---:|---:|---:|---:|---:|
| 0.30 | 0.000 | 1.000 | 1.000 | 0.000 | -1.000 | 0.000 |
| 0.50 | 0.200 | 0.100 | 1.000 | 0.100 | 0.000 | -0.100 |
| 0.70 | 0.300 | 0.000 | 1.000 | 1.000 | 1.000 | 0.700 |
| 0.90 | 0.333 | 0.000 | 1.000 | 1.000 | 1.000 | 0.667 |
| 1.00 | 0.231 | 0.000 | 0.615 | 0.615 | 0.615 | 0.385 |

## 2. Per-Kind Results

| Kind | SP | breadth | content_rule | VLD | N |
|---|---:|---:|---:|---:|---:|
| score_keyed | 0.240 | 0.120 | 0.900 | 0.620 | 50 |

## 3. Controls

- Flat controls: VLD=0.000, single_pass=0.000, pass=True.
- ρ=0.50 controls: VLD=0.100, near chance 0.20±0.15 pass=True.

## 4. Per-ρ Table

Same as §1; score-keyed subset only.

## 5. Comparison with SOC

- SOC: VLD=100.0% at ρ≥0.70 on score_keyed conditional scenarios.
- DataOps: VLD=85.7% at ρ≥0.70 on score_keyed conditional scenarios.
- Cross-copilot generalization holds: False.

## Headline

accuracy(VLD) at ρ≥0.70 on score_keyed = 0.857.
accuracy(VLD) - accuracy(breadth) on score_keyed = 0.500.
