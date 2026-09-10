# Trading Stage 1 Multi-Hop Evaluation

PLANTED / POSITIVE CONTROL — not a measurement of real production value.

## 1. Acceptance Test

Verdict: PASS

Headline comparison for score-keyed cases is VLD vs breadth. content_rule is reported as an oracle upper bound because it reads correct_branches directly.

| ρ | SP | breadth | content_rule | VLD | Δ(VLD−breadth) | Δ(VLD−SP) |
|---:|---:|---:|---:|---:|---:|---:|
| 0.30 | 0.333 | 0.333 | 1.000 | 0.000 | -0.333 | -0.333 |
| 0.50 | 0.600 | 0.400 | 1.000 | 0.400 | 0.000 | -0.200 |
| 0.70 | 0.500 | 0.000 | 1.000 | 1.000 | 1.000 | 0.500 |
| 0.90 | 0.667 | 0.000 | 1.000 | 1.000 | 1.000 | 0.333 |
| 1.00 | 0.000 | 0.000 | 1.000 | 1.000 | 1.000 | 1.000 |

## 2. Per-Kind Results

| Kind | SP | breadth | content_rule | VLD | N |
|---|---:|---:|---:|---:|---:|
| content_keyed | 0.400 | 0.333 | 0.800 | 0.800 | 15 |
| prerequisite | 0.400 | 0.800 | 1.000 | 1.000 | 5 |
| score_keyed | 0.450 | 0.150 | 1.000 | 0.700 | 20 |

## 3. Controls

- Flat controls: VLD=0.400, single_pass=0.400, pass=True.
- ρ=0.50 controls: VLD=0.400, near chance 0.20±0.20 pass=True.

## 4. Per-ρ Table

Same as §1; score-keyed subset only.

## 5. Cross-Copilot Comparison

| Copilot | VLD at ρ≥0.70 | SP at ρ≥0.70 | Factors | Actions | N |
|---|---:|---:|---:|---:|---:|
| SOC | 100.0% | 25–50% | 6 | 4 | 50 |
| DataOps | 100.0% | 12.5% | 6 | 5 | 50 |
| S2P | 56.2% | 62.5% | 7 | 5 | 50 |
| Trading | 100.0% | 41.7% | 6 | 5 | 40 |

## 6. Centroid Diagnostics

- Action cells with ≥3 instances: 5.
- Action cells defaulted: 0.
- Samples per action: {'execute': 6, 'defer': 9, 'reduce_size': 8, 'hedge': 6, 'reject': 6}.
- Centroid diff ||μ_surface − μ_enriched||: 0.1045.

## Headline

accuracy(VLD) at ρ≥0.70 on score_keyed = 1.000.
accuracy(VLD) - accuracy(breadth) on score_keyed = 0.550.
