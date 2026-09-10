# Purchasing Stage 1 Multi-Hop Evaluation

PLANTED / POSITIVE CONTROL — not a measurement of real production value.

## 1. Acceptance Test

Verdict: PASS

Headline comparison for score-keyed cases is VLD vs breadth. content_rule is reported as an oracle upper bound because it reads correct_branches directly.

| ρ | SP | breadth | content_rule | VLD | Δ(VLD−breadth) | Δ(VLD−SP) |
|---:|---:|---:|---:|---:|---:|---:|
| 0.30 | 0.333 | 0.333 | 1.000 | 0.000 | -0.333 | -0.333 |
| 0.50 | 0.200 | 0.200 | 1.000 | 0.200 | 0.000 | 0.000 |
| 0.70 | 0.333 | 0.167 | 1.000 | 1.000 | 0.833 | 0.667 |
| 0.90 | 1.000 | 0.000 | 1.000 | 1.000 | 1.000 | 0.000 |
| 1.00 | 0.333 | 0.000 | 1.000 | 1.000 | 1.000 | 0.667 |

## 2. Per-Kind Results

| Kind | SP | breadth | content_rule | VLD | N |
|---|---:|---:|---:|---:|---:|
| content_keyed | 0.333 | 0.800 | 0.800 | 0.800 | 15 |
| prerequisite | 0.200 | 0.000 | 1.000 | 1.000 | 5 |
| score_keyed | 0.400 | 0.150 | 1.000 | 0.650 | 20 |

## 3. Controls

- Flat controls: VLD=0.400, single_pass=0.400, pass=True.
- ρ=0.50 controls: VLD=0.200, near chance 0.167±0.20 pass=True.

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

- Action cells with ≥3 non-flat instances: 6.
- Action cells defaulted: 0.
- Samples per action: {'order_standard': 8, 'order_increased': 4, 'order_reduced': 8, 'switch_supplier': 6, 'defer_order': 6, 'emergency_order': 3}.
- Enriched vs surface centroid diff: 0.1355.

## Headline

accuracy(VLD) at ρ≥0.70 on score_keyed = 1.000.
accuracy(VLD) - accuracy(breadth) on score_keyed = 0.500.
Cross-copilot generalization holds: True.
