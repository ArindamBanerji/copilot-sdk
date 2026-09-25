# VLD Post-Regen Geometry Snapshot - 2026-09-11

## 1. Bundle Regeneration Results

Command run from `copilot-sdk`:

```text
python scripts\regenerate_demo_bundles.py
```

Generator output:

```text
trading: wrote demo\trading_demo_bundle.json decisions=200 verified=150 checkpoints=5 events=1
purchasing: wrote demo\purchasing_demo_bundle.json decisions=200 verified=150 checkpoints=5 events=1
dataops: wrote demo\dataops_demo_bundle.json decisions=200 verified=150 checkpoints=5 events=1
```

Generated bundle files:

| File | Size | Tensor shape | Bundle max action spread |
| --- | ---: | --- | ---: |
| `demo/trading_demo_bundle.json` | 406,618 bytes | `(5, 4, 10)` | 0.6400 |
| `demo/purchasing_demo_bundle.json` | 339,183 bytes | `(5, 4, 7)` | 0.6500 |
| `demo/dataops_demo_bundle.json` | 341,804 bytes | `(6, 5, 6)` | 1.0000 |

Trading regenerated bundle per-category spreads:

| Category index | Max action spread |
| ---: | ---: |
| 0 | 0.600000 |
| 1 | 0.355700 |
| 2 | 0.640000 |
| 3 | 0.452500 |
| 4 | 0.601800 |

Purchasing regenerated bundle per-category spreads:

| Category index | Max action spread |
| ---: | ---: |
| 0 | 0.556200 |
| 1 | 0.449500 |
| 2 | 0.504900 |
| 3 | 0.601800 |
| 4 | 0.650000 |

Pre-regen export max diffs from `real_centroids_v1.json` before rerun:

| Copilot | Category | Pre-regen exported max diff |
| --- | --- | ---: |
| trading | all 5 categories | 0.0000 |
| purchasing | all 5 categories | 0.0000 |
| s2p | all 5 categories | 0.6000 |

Post-regen/export finding: the generated Trading/Purchasing bundle files are differentiated, but `tests/extract_real_centroids.py` exports current scorer/checkpoint state. The new bundle files alone did not make Purchasing differentiated in the exported runtime snapshot. Trading changed through L5 restore only for part of the tensor; Purchasing remained collapsed.

## 2. L5 Restore Results

Exporter command run:

```text
python tests\extract_real_centroids.py > real_centroids_v1.json
```

Export artifact:

```text
real_centroids_v1.json sha256=d81e2b17d83b20169a34bf5272886f0e808ba56e6ada86ad4a875054258be1d0
errors={}
```

Per-copilot restore metadata:

| Copilot | `pre_restore_hash` | `post_restore_hash` | `l5_rows_applied` | Changed after L5 |
| --- | --- | --- | ---: | --- |
| trading | `2e5b594bb42e...` | `c672b63e2d0a...` | 6 | yes |
| purchasing | `78acf27a7535...` | `78acf27a7535...` | 0 | no |
| s2p | `683724c09ab9...` | `38c5c5d09819...` | 6 | yes |

Post-export category differentiation:

| Copilot | Category | Shape | Max diff | Status |
| --- | --- | --- | ---: | --- |
| trading | trend_following | `(4, 10)` | 0.526551 | DIFF |
| trading | mean_reversion | `(4, 10)` | 0.030000 | DIFF |
| trading | event_driven | `(4, 10)` | 0.025000 | DIFF |
| trading | income_strategy | `(4, 10)` | 0.000000 | IDENTICAL |
| trading | scalp_intraday | `(4, 10)` | 0.000000 | IDENTICAL |
| purchasing | protein | `(4, 7)` | 0.000000 | IDENTICAL |
| purchasing | produce | `(4, 7)` | 0.000000 | IDENTICAL |
| purchasing | dairy | `(4, 7)` | 0.000000 | IDENTICAL |
| purchasing | dry_goods | `(4, 7)` | 0.000000 | IDENTICAL |
| purchasing | beverages | `(4, 7)` | 0.000000 | IDENTICAL |
| s2p | price_variance | `(5, 8)` | 0.589330 | DIFF |
| s2p | quantity_mismatch | `(5, 8)` | 0.600000 | DIFF |
| s2p | duplicate_risk | `(5, 8)` | 0.600000 | DIFF |
| s2p | contract_gap | `(5, 8)` | 0.600000 | DIFF |
| s2p | format_compliance | `(5, 8)` | 0.600000 | DIFF |

## 3. Per-Copilot Geometry

### Trading

Tensor shape: `(5 categories, 4 actions, 10 factors)`.

Actions:

```text
strong_execution, partial_execution, poor_execution, skip_recommended
```

Factors:

```text
signal_alignment, market_regime, position_sizing, timing_quality,
risk_reward_actual, emotional_indicator, signal_confidence,
options_delta_exposure, options_iv_percentile, options_gamma_risk
```

Pairwise action distances:

| Category | Pair | L2 | Linf |
| --- | --- | ---: | ---: |
| trend_following | strong_execution vs partial_execution | 0.7842 | 0.5266 |
| trend_following | strong_execution vs poor_execution | 0.7391 | 0.4866 |
| trend_following | strong_execution vs skip_recommended | 0.7391 | 0.4866 |
| trend_following | partial_execution vs poor_execution | 0.0934 | 0.0400 |
| trend_following | partial_execution vs skip_recommended | 0.0934 | 0.0400 |
| trend_following | poor_execution vs skip_recommended | 0.0000 | 0.0000 |
| mean_reversion | strong_execution vs each other action | 0.0735 | 0.0300 |
| mean_reversion | partial_execution vs poor_execution/skip_recommended | 0.0000 | 0.0000 |
| mean_reversion | poor_execution vs skip_recommended | 0.0000 | 0.0000 |
| event_driven | strong_execution vs each other action | 0.0659 | 0.0250 |
| event_driven | partial_execution vs poor_execution/skip_recommended | 0.0000 | 0.0000 |
| event_driven | poor_execution vs skip_recommended | 0.0000 | 0.0000 |
| income_strategy | all pairs | 0.0000 | 0.0000 |
| scalp_intraday | all pairs | 0.0000 | 0.0000 |

Trading is only partially differentiated after export. In the showcase category `trend_following`, `poor_execution` and `skip_recommended` are still identical, so `skip_recommended` cannot be a unique VLD target under argmax scoring.

### Purchasing

Tensor shape: `(5 categories, 4 actions, 7 factors)`.

Actions:

```text
order_as_planned, order_more, order_less, skip
```

Factors:

```text
expected_demand, day_of_week, weather_forecast, event_flag,
historical_waste, supplier_lead_time, price_memory_index
```

Pairwise action distances:

| Category | Pairwise action distances |
| --- | --- |
| protein | all six pairs are `L2=0.0000`, `Linf=0.0000` |
| produce | all six pairs are `L2=0.0000`, `Linf=0.0000` |
| dairy | all six pairs are `L2=0.0000`, `Linf=0.0000` |
| dry_goods | all six pairs are `L2=0.0000`, `Linf=0.0000` |
| beverages | all six pairs are `L2=0.0000`, `Linf=0.0000` |

Purchasing has no exported action separation after regeneration/export. Every action has the same distance for every vector in each category, so all margins are zero and no honest positive-margin flip or S1 region exists in the exported geometry.

### S2P

Tensor shape: `(5 categories, 5 actions, 8 factors)`.

Actions:

```text
auto_approve, hold_for_review, escalate_to_buyer, flag_leakage, refer_to_specialist
```

Factors:

```text
match_status, amount_variance_ratio, duplicate_score,
supplier_exception_history, payment_terms_impact,
commodity_index_correlation, tax_regulatory_compliance,
environmental_risk
```

Pairwise action distances for `price_variance`:

| Pair | L2 | Linf |
| --- | ---: | ---: |
| auto_approve vs hold_for_review | 0.5853 | 0.3848 |
| auto_approve vs escalate_to_buyer | 0.9193 | 0.5284 |
| auto_approve vs flag_leakage | 0.9025 | 0.5893 |
| auto_approve vs refer_to_specialist | 1.0167 | 0.5420 |
| hold_for_review vs escalate_to_buyer | 0.4356 | 0.3010 |
| hold_for_review vs flag_leakage | 0.5709 | 0.3010 |
| hold_for_review vs refer_to_specialist | 0.5618 | 0.3814 |
| escalate_to_buyer vs flag_leakage | 0.3775 | 0.3000 |
| escalate_to_buyer vs refer_to_specialist | 0.5025 | 0.3000 |
| flag_leakage vs refer_to_specialist | 0.6557 | 0.4000 |

Pairwise action distances for `quantity_mismatch`, `duplicate_risk`, `contract_gap`, and `format_compliance` are identical in this export:

| Pair | L2 | Linf |
| --- | ---: | ---: |
| auto_approve vs hold_for_review | 0.6279 | 0.3956 |
| auto_approve vs escalate_to_buyer | 0.9578 | 0.5500 |
| auto_approve vs flag_leakage | 0.9438 | 0.6000 |
| auto_approve vs refer_to_specialist | 1.0615 | 0.5500 |
| hold_for_review vs escalate_to_buyer | 0.4336 | 0.3000 |
| hold_for_review vs flag_leakage | 0.5718 | 0.3000 |
| hold_for_review vs refer_to_specialist | 0.5611 | 0.3804 |
| escalate_to_buyer vs flag_leakage | 0.3775 | 0.3000 |
| escalate_to_buyer vs refer_to_specialist | 0.5025 | 0.3000 |
| flag_leakage vs refer_to_specialist | 0.6557 | 0.4000 |

## 4. Q Ordering Analysis

Unit sigma and `tau=0.1` were used from the export. Trading gates `correlation_engine` and `portfolio_engine`; Purchasing gates `vendor_tracker` and `lead_time_tracker`; S2P has no gated sources in `main.py`.

### Trading

Registered evidence:

- `VLD-TRD-1`: dim 1 `market_regime` = 0.88, confidence 0.90, source `correlation_engine`; dim 3 `timing_quality` = 0.25, confidence 0.85, source `momentum_tracker`.
- `VLD-TRD-2`: dim 2 `position_sizing` = 0.85, confidence 0.92, source `portfolio_engine`; dim 1 `market_regime` = 0.78, confidence 0.88, source `correlation_engine`.

Claimed target flips:

- `strong_execution -> poor_execution`: no positive-margin candidate found in the bounded search with current evidence.
- `strong_execution -> skip_recommended`: infeasible as a unique target in `trend_following` because `poor_execution` and `skip_recommended` are identical; argmax selects `poor_execution` before `skip_recommended` on ties.

Feasible flip pairs with existing evidence:

| Scenario | Feasible pair | Surface margin | Final margin | Q/read order |
| --- | --- | ---: | ---: | --- |
| VLD-TRD-1 | strong_execution -> partial_execution | 0.847312 | 0.490948 | dim 2 none, then dim 1 evidence |
| VLD-TRD-2 | strong_execution -> partial_execution | 0.982158 | 0.575971 | dim 2 evidence, then dim 1 evidence |

Trading S1 region:

- `strong_execution` centroid is a robust S1 candidate: margin 0.985286.
- `partial_execution` centroid is weak: margin 0.029453.
- `poor_execution`/`skip_recommended` centroids are tied: margin 0.

### Purchasing

Registered evidence exists for all seven dimensions on showcase orders, but no flip is geometrically meaningful because all action rows are identical in the exported tensor.

Results:

- `VLD-PUR-DEMAND-SPIKE`: no claimed or alternate positive-margin flip.
- `VLD-PUR-VENDOR-CASCADE`: no claimed or alternate positive-margin flip.
- `VLD-PUR-S1-STANDARD`: every action centroid scores as `order_as_planned` with margin 0.

Blocker: the regenerated bundle is differentiated, but this did not propagate into `real_centroids_v1.json`. VLD-REGEN-2 should not tune Purchasing preseed vectors until the exported scorer geometry is actually differentiated.

### S2P

Registered evidence:

- `VLD-S2P-1`: dim 0 contract coverage = 0.95, dim 3 supplier history exception value = 0.03, plus additional provider evidence on dims 1, 2, 4, 6, 7.
- `VLD-S2P-2`: dim 0 contract coverage = 0.93, dim 1 pricing variance = 0.05, dim 5 demand/volume context = 0.82, plus additional provider evidence on dims 2, 3, 4, 6, 7.

Claimed target flips are feasible:

| Scenario | Feasible pair | Surface margin | Final margin | Q/read order |
| --- | --- | ---: | ---: | --- |
| VLD-S2P-1 | hold_for_review -> auto_approve | 0.882886 | 0.909827 | dim 0 contract, then dim 3 supplier history |
| VLD-S2P-2 | flag_leakage -> auto_approve | 0.890912 | 0.893497 | dim 0 contract, then dim 5 volume context |

S1 regions:

| Action centroid | Scores as | Margin |
| --- | --- | ---: |
| auto_approve | auto_approve | 0.936492 |
| hold_for_review | hold_for_review | 0.672738 |
| escalate_to_buyer | escalate_to_buyer | 0.516399 |
| flag_leakage | flag_leakage | 0.587476 |
| refer_to_specialist | refer_to_specialist | 0.809617 |

The best S1 candidate for the current demo contract is the `auto_approve` centroid.

## 5. Feasible Preseed Vectors

These are design outputs only. No preseed file was modified.

### Trading feasible alternates

`VLD-TRD-1` feasible alternate:

```text
surface vector = [0.3691, 0.1681, 0.9979, 0.7543, 0.0423, 0.9649, 0.0445, 0.8666, 0.5830, 0.9457]
surface action = strong_execution
surface margin = 0.847312
Q/read order = dim 2 (no evidence), then dim 1 market_regime
evidence = dim 1 value 0.88, confidence 0.90, source correlation_engine
effective gated dim 1 value = 0.80881
predicted VLD action = partial_execution
final margin = 0.490948
```

Narrative: the first top-Q read lacks registered evidence; the second read uses correlation/regime evidence to move the trade away from a strong execution recommendation. This is not the existing `poor_execution` narrative.

`VLD-TRD-2` feasible alternate:

```text
surface vector = [0.9799, 0.2885, 0.0066, 0.8448, 0.6336, 0.9348, 0.1601, 0.0338, 0.4228, 0.7856]
surface action = strong_execution
surface margin = 0.982158
Q/read order = dim 2 position_sizing, then dim 1 market_regime
evidence dim 2 = value 0.85, confidence 0.92, source portfolio_engine
effective gated dim 2 value = 0.782528
evidence dim 1 = value 0.78, confidence 0.88, source correlation_engine
effective gated dim 1 value = 0.721020
predicted VLD action = partial_execution
final margin = 0.575971
```

Narrative: portfolio concentration and market regime reads reduce confidence in full execution. This supports a strong-to-partial story, not the current `skip_recommended` story.

Trading S1:

```text
vector = [0.6000, 0.2197, 0.2417, 0.0245, 0.4000, 0.6566, 0.5000, 0.5000, 0.5000, 0.5000]
action = strong_execution
surface margin = 0.985286
budget recommendation = 0
```

### Purchasing

No feasible flip vectors and no S1 vectors exist against the exported Purchasing geometry. All action centroids are identical; every action probability tie has margin 0. This remains blocked until the differentiated bundle is loaded into the scorer/export path.

### S2P

`VLD-S2P-1` feasible claimed flip:

```text
surface vector = [0.3906, 0.1186, 0.0000, 0.4267, 0.3338, 0.7039, 1.0000, 0.1912]
surface action = hold_for_review
surface margin = 0.882886
Q/read order = dim 0 match_status, then dim 3 supplier_exception_history
evidence dim 0 = value 0.95, confidence 0.90, source contract_db
evidence dim 3 = value 0.03, confidence 0.8214, source supplier_history
predicted VLD action = auto_approve
final margin = 0.909827
```

Narrative: contract coverage establishes that partial delivery is covered, then supplier history verifies low exception risk.

`VLD-S2P-2` feasible claimed flip:

```text
surface vector = [0.9237, 0.1010, 0.0568, 0.0000, 0.6731, 0.0000, 0.3416, 0.2494]
surface action = flag_leakage
surface margin = 0.890912
Q/read order = dim 0 match_status, then dim 5 commodity_index_correlation
evidence dim 0 = value 0.93, confidence 0.90, source contract_db
evidence dim 5 = value 0.82, confidence 0.78, source demand_forecast
predicted VLD action = auto_approve
final margin = 0.893497
```

Narrative: contract coverage validates the bulk pricing clause, then volume context explains the apparent price spike.

S2P S1:

```text
vector = [0.9420, 0.0716, 0.0253, 0.0800, 0.4947, 0.7893, 0.9367, 0.5000]
action = auto_approve
surface margin = 0.936492
budget recommendation = 0
```

## 6. Summary

Feasibility count against the actual post-export geometry:

| Copilot | Claimed flips feasible | Alternate flips feasible | S1 feasible |
| --- | ---: | ---: | ---: |
| Trading | 0 / 2 | 2 / 2, but both are strong_execution -> partial_execution | 1 / 1 with revised strong_execution S1 |
| Purchasing | 0 / 2 | 0 / 2 | 0 / 1 |
| S2P | 2 / 2 | 2 / 2 | 1 / 1 |

Overall:

- Claimed flip scenarios feasible: 2 of 6.
- Any flip scenario feasible with existing evidence: 4 of 6.
- S1 scenarios feasible: 2 of 3.

What VLD-REGEN-2 needs to apply:

1. Do not edit Purchasing preseed yet. First make the exported Purchasing scorer geometry consume the differentiated regenerated bundle or an equivalent differentiated checkpoint.
2. For Trading, either revise the demo claims to strong_execution -> partial_execution or repair the exported tensor so `poor_execution` and `skip_recommended` are separately learnable winners.
3. For S2P, update the two flip vectors to the exact post-L5 vectors above if the current post-export hash remains `38c5c5d09819...`.
4. Use the strong `strong_execution` Trading centroid and the S2P `auto_approve` centroid as S1 candidates; leave Purchasing S1 blocked until geometry is repaired.

Open blockers:

- Regenerated bundle differentiation is real, but it is not sufficient if `real_centroids_v1.json` still exports stale/collapsed checkpoint state.
- Purchasing has no positive-margin VLD behavior in the exported snapshot.
- Trading `skip_recommended` remains impossible as a unique target while it is identical to `poor_execution` in `trend_following`.

Core hashes observed after the run:

```text
copilot_sdk/scoring/investigation.py: a1531aea56125475f29cebec64b197a500a7a82bdf56fa1caa1c567ca9c8672a
copilot_sdk/backend/investigation_router.py: f30767bc7080196a358569a16b34ac8159c6250aca3d3fc6244368067bfc8e90
```
