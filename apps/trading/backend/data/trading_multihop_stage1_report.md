# Trading Stage 1 Multi-Hop Evaluation

PLANTED / POSITIVE CONTROL — not a measurement of real production value.

## 1. Acceptance Test

Verdict: FAIL

Headline comparison for score-keyed cases is VLD vs breadth. content_rule is reported as an oracle upper bound because it reads correct_branches directly.

| ρ | SP | breadth | content_rule | VLD | Δ(VLD−breadth) | Δ(VLD−SP) |
|---:|---:|---:|---:|---:|---:|---:|
| 0.50 | 0.167 | 0.333 | 1.000 | 0.333 | 0.000 | 0.167 |
| 0.70 | 0.300 | 0.000 | 1.000 | 1.000 | 1.000 | 0.700 |
| 0.90 | 0.083 | 0.000 | 1.000 | 1.000 | 1.000 | 0.917 |
| 1.00 | 0.333 | 0.083 | 0.750 | 0.750 | 0.667 | 0.417 |

## 2. Per-Kind Results

| Kind | SP | breadth | content_rule | VLD | N |
|---|---:|---:|---:|---:|---:|
| score_keyed | 0.225 | 0.075 | 0.925 | 0.825 | 40 |

## 3. Controls

- Flat controls: VLD=0.250, single_pass=0.250, pass=True.
- ρ=0.50 controls: VLD=0.333, near chance 0.20±0.20 pass=True.

## 4. Per-ρ Table

Same as §1; score-keyed subset only.

## 5. Cross-Copilot Comparison

| Copilot | VLD at ρ≥0.70 | SP at ρ≥0.70 | Factors | Actions | N |
|---|---:|---:|---:|---:|---:|
| SOC | 100.0% | 25–50% | 6 | 4 | 50 |
| DataOps | 100.0% | 12.5% | 6 | 5 | 50 |
| S2P | 56.2% | 62.5% | 7 | 5 | 50 |
| Trading | 91.2% | 23.5% | 6 | 5 | 40 |

## 6. Centroid Diagnostics

- Action cells with ≥3 instances: 5.
- Action cells defaulted: 0.
- Samples per action: {'execute': 4, 'defer': 11, 'reduce_size': 10, 'hedge': 7, 'reject': 8}.
- Centroid diff ||μ_surface − μ_enriched||: 0.5694.

## Headline

accuracy(VLD) at ρ≥0.70 on score_keyed = 0.912.
accuracy(VLD) - accuracy(breadth) on score_keyed = 0.750.
