# Purchasing Stage 1 Multi-Hop Evaluation

PLANTED / POSITIVE CONTROL — not a measurement of real production value.

## 1. Acceptance Test

Verdict: PASS

Headline comparison for score-keyed cases is VLD vs breadth. content_rule is reported as an oracle upper bound because it reads correct_branches directly.

| ρ | SP | breadth | content_rule | VLD | Δ(VLD−breadth) | Δ(VLD−SP) |
|---:|---:|---:|---:|---:|---:|---:|
| 0.30 | 0.400 | 1.000 | 1.000 | 0.000 | -1.000 | -0.400 |
| 0.50 | 1.000 | 0.000 | 1.000 | 0.000 | 0.000 | -1.000 |
| 0.70 | 0.300 | 0.000 | 1.000 | 1.000 | 1.000 | 0.700 |
| 0.90 | 0.333 | 0.000 | 1.000 | 1.000 | 1.000 | 0.667 |
| 1.00 | 0.375 | 0.000 | 1.000 | 1.000 | 1.000 | 0.625 |

## 2. Per-Kind Results

| Kind | SP | breadth | content_rule | VLD | N |
|---|---:|---:|---:|---:|---:|
| score_keyed | 0.425 | 0.125 | 1.000 | 0.750 | 40 |

## 3. Controls

- Flat controls: VLD=0.000, single_pass=0.000, pass=True.
- ρ=0.50 controls: VLD=0.000, near chance 0.167±0.20 pass=True.

## 4. Per-ρ Table

Same as §1; score-keyed subset only.

## 5. Cross-Copilot Comparison

| Copilot | VLD at ρ≥0.70 | Actions | Factors | N |
|---|---:|---:|---:|---:|
| SOC | 100.0% | 4 | 6 | 50 |
| DataOps | 100.0% | 5 | 6 | 50 |
| S2P | 56.2% | 5 | 7 | 50 |
| Trading | 100.0% | 5 | 6 | 40 |
| Purchasing | 100.0% | 6 | 6 | 40 |

## 6. Centroid Diagnostics

- Action cells with ≥3 non-flat instances: 4.
- Action cells defaulted: 2.
- Samples per action: {'order_standard': 0, 'order_increased': 8, 'order_reduced': 10, 'switch_supplier': 15, 'defer_order': 7, 'emergency_order': 0}.
- Enriched vs surface centroid diff: 0.4210.

## Headline

accuracy(VLD) at ρ≥0.70 on score_keyed = 1.000.
accuracy(VLD) - accuracy(breadth) on score_keyed = 0.625.
Cross-copilot generalization holds: True.
