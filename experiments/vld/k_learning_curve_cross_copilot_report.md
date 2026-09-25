# Cross-Copilot K Learning Curves

Generated: 2026-09-13T00:16:07.322562+00:00

Evidence tier: REAL_COMPONENT production centroid geometry with synthetic verification scenarios following the existing DataOps K-learning protocol. This is a controlled mechanism test, not live operational value measurement.

## 1. Protocol

The protocol matches the existing DataOps K learning curve experiment: 500 learning decisions, K bounded to [0.1, 3.0], +0.02 / -0.005 updates, checkpoints every 50 decisions, 50 evaluation scenarios per checkpoint, and investigation budget 2. Each copilot uses centroids exported in `real_centroids_v1.json`; DataOps uses the existing baseline file `k_learning_curve_results.json`.

## 2. Per-Copilot Results Table

| Copilot | Tensor | Cells | Final Routing (Learn) | Final Routing (Control) | Delta | Relative Delta | Accuracy (Learn) | Accuracy (Control) | Acc Delta | Hurts | Starvation | Starved Dims |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| dataops | 6×5×6 | 180 | 0.630 | 0.440 | +0.190 | 43.2% | 0.900 | 0.580 | +0.320 | 0 | 8.3% (3/36) | schema_change.data_freshness, freshness_violation.recurrence_frequency, pipeline_failure.downstream_urgency |
| trading | 5×4×10 | 200 | 0.750 | 0.630 | +0.120 | 19.0% | 0.920 | 0.780 | +0.140 | 0 | 48.0% (24/50) | trend_following.signal_confidence, trend_following.options_delta_exposure, trend_following.options_iv_percentile, trend_following.options_gamma_risk, mean_reversion.signal_confidence; +19 more |
| purchasing | 5×4×7 | 140 | 0.720 | 0.510 | +0.210 | 41.2% | 0.820 | 0.520 | +0.300 | 0 | 28.6% (10/35) | protein.supplier_lead_time, protein.price_memory_index, produce.expected_demand, produce.price_memory_index, dairy.supplier_lead_time; +5 more |
| soc | 6×4×6 | 144 | 0.810 | 0.690 | +0.120 | 17.4% | 0.860 | 0.720 | +0.140 | 0 | 36.1% (13/36) | credential_access.time_anomaly, malware_execution.pattern_history, malware_execution.time_anomaly, lateral_movement.asset_criticality, lateral_movement.threat_intel_enrichment; +8 more |
| s2p | 5×5×8 | 200 | 0.650 | 0.620 | +0.030 | 4.8% | 0.840 | 0.780 | +0.060 | 0 | 22.5% (9/40) | price_variance.duplicate_score, price_variance.supplier_exception_history, price_variance.environmental_risk, quantity_mismatch.environmental_risk, duplicate_risk.payment_terms_impact; +4 more |

## 3. Starvation Analysis

### dataops

Starvation rate: **8.3%** (3/36 category-dimension weights stayed at the 0.5 baseline). Starved dimensions: schema_change.data_freshness, freshness_violation.recurrence_frequency, pipeline_failure.downstream_urgency.

### trading

Starvation rate: **48.0%** (24/50 category-dimension weights stayed at the 0.5 baseline). Starved dimensions: trend_following.signal_confidence, trend_following.options_delta_exposure, trend_following.options_iv_percentile, trend_following.options_gamma_risk, mean_reversion.signal_confidence, mean_reversion.options_delta_exposure, mean_reversion.options_iv_percentile, mean_reversion.options_gamma_risk, event_driven.emotional_indicator, event_driven.signal_confidence, event_driven.options_delta_exposure, event_driven.options_iv_percentile; +12 more.

### purchasing

Starvation rate: **28.6%** (10/35 category-dimension weights stayed at the 0.5 baseline). Starved dimensions: protein.supplier_lead_time, protein.price_memory_index, produce.expected_demand, produce.price_memory_index, dairy.supplier_lead_time, dairy.price_memory_index, dry_goods.expected_demand, dry_goods.price_memory_index, beverages.event_flag, beverages.price_memory_index.

### soc

Starvation rate: **36.1%** (13/36 category-dimension weights stayed at the 0.5 baseline). Starved dimensions: credential_access.time_anomaly, malware_execution.pattern_history, malware_execution.time_anomaly, lateral_movement.asset_criticality, lateral_movement.threat_intel_enrichment, lateral_movement.time_anomaly, data_exfiltration.pattern_history, data_exfiltration.time_anomaly, insider_threat.asset_criticality, insider_threat.threat_intel_enrichment, cloud_infrastructure.asset_criticality, cloud_infrastructure.pattern_history; +1 more.

### s2p

Starvation rate: **22.5%** (9/40 category-dimension weights stayed at the 0.5 baseline). Starved dimensions: price_variance.duplicate_score, price_variance.supplier_exception_history, price_variance.environmental_risk, quantity_mismatch.environmental_risk, duplicate_risk.payment_terms_impact, duplicate_risk.environmental_risk, contract_gap.environmental_risk, format_compliance.duplicate_score, format_compliance.environmental_risk.

No factor name was starved across multiple copilots under the exact exported factor names; starvation is geometry and category specific.

Tensor size vs starvation correlation: **+0.000**. In this run, starvation does not scale linearly with tensor cells. Tensor size vs routing-quality gain correlation: **-0.589**, driven by the smaller gains in the two 200-cell copilots (Trading and S2P).

## 4. Cross-Copilot Comparison

K learning improves final routing quality in all five copilots: range **+0.030 to +0.210**. The largest absolute gain is **purchasing** (+0.210); the smallest is **s2p** (+0.030).

The DataOps baseline gain is +0.190, which is 43.2% relative to its final control routing quality. That relative +43% style result does not replicate uniformly: relative gains are dataops 43.2%, trading 19.0%, purchasing 41.2%, soc 17.4%, s2p 4.8%.

The control arm varies across copilots from **0.440** to **0.690**, so the fixed-K baseline is not perfectly stable across geometries. Accuracy gains remain non-negative for every copilot, and learning-arm hurts are zero in the final checkpoint for every copilot.

Charts generated:

- `experiments/vld/charts/pub_cross_copilot_routing.png`
- `experiments/vld/charts/pub_cross_copilot_starvation.png`
- `experiments/vld/charts/pub_cross_copilot_accuracy.png`
- `experiments/vld/charts/pub_tensor_vs_starvation.png`

## 5. Implications for RGI Claims

The supported claim is that RGI/K learning works as a mechanism across five copilots under production centroid geometry: every copilot shows a positive routing-quality delta and non-negative accuracy delta with zero final-checkpoint hurts. The stronger claim that a +43% routing gain generalizes is not supported; gains vary by geometry, from +0.030 in S2P to +0.210 in Purchasing.

Starvation does not scale cleanly with tensor size in this run. Trading and S2P both have 200-cell tensors, but their starvation rates differ (48.0% vs 22.5%) and both have lower routing gains than the smaller Purchasing tensor. This supports the RV-1 bandit extension as a targeted exploration mechanism: starvation is category-dimension specific and should be managed by exploration pressure rather than by tensor-size heuristics alone.

## Appendix A. Per-Checkpoint Final Curves

### dataops

| Decisions | Routing Learn | Routing Control | Accuracy Learn | Accuracy Control | Saves | Hurts |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 50 | 0.420 | 0.400 | 0.560 | 0.520 | 23 | 0 |
| 100 | 0.500 | 0.440 | 0.800 | 0.660 | 38 | 0 |
| 150 | 0.490 | 0.430 | 0.760 | 0.640 | 31 | 0 |
| 200 | 0.520 | 0.420 | 0.720 | 0.560 | 32 | 0 |
| 250 | 0.560 | 0.420 | 0.720 | 0.580 | 30 | 0 |
| 300 | 0.580 | 0.410 | 0.880 | 0.600 | 37 | 0 |
| 350 | 0.570 | 0.510 | 0.800 | 0.700 | 35 | 0 |
| 400 | 0.530 | 0.400 | 0.840 | 0.640 | 38 | 0 |
| 450 | 0.550 | 0.490 | 0.860 | 0.720 | 39 | 0 |
| 500 | 0.630 | 0.440 | 0.900 | 0.580 | 38 | 0 |

### trading

| Decisions | Routing Learn | Routing Control | Accuracy Learn | Accuracy Control | Saves | Hurts |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 50 | 0.670 | 0.650 | 0.840 | 0.820 | 31 | 0 |
| 100 | 0.660 | 0.630 | 0.920 | 0.900 | 33 | 0 |
| 150 | 0.740 | 0.620 | 0.900 | 0.760 | 34 | 0 |
| 200 | 0.730 | 0.640 | 0.880 | 0.700 | 33 | 0 |
| 250 | 0.670 | 0.580 | 0.940 | 0.740 | 36 | 0 |
| 300 | 0.660 | 0.590 | 0.880 | 0.780 | 37 | 0 |
| 350 | 0.720 | 0.580 | 0.900 | 0.760 | 33 | 0 |
| 400 | 0.670 | 0.650 | 0.820 | 0.780 | 29 | 0 |
| 450 | 0.740 | 0.580 | 0.880 | 0.740 | 36 | 0 |
| 500 | 0.750 | 0.630 | 0.920 | 0.780 | 38 | 0 |

### purchasing

| Decisions | Routing Learn | Routing Control | Accuracy Learn | Accuracy Control | Saves | Hurts |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 50 | 0.630 | 0.600 | 0.700 | 0.660 | 26 | 0 |
| 100 | 0.540 | 0.450 | 0.660 | 0.520 | 27 | 0 |
| 150 | 0.550 | 0.530 | 0.560 | 0.480 | 24 | 0 |
| 200 | 0.620 | 0.510 | 0.700 | 0.560 | 31 | 0 |
| 250 | 0.680 | 0.530 | 0.720 | 0.560 | 31 | 0 |
| 300 | 0.700 | 0.540 | 0.780 | 0.600 | 35 | 0 |
| 350 | 0.650 | 0.580 | 0.720 | 0.620 | 34 | 0 |
| 400 | 0.760 | 0.500 | 0.860 | 0.500 | 37 | 0 |
| 450 | 0.660 | 0.510 | 0.800 | 0.620 | 30 | 0 |
| 500 | 0.720 | 0.510 | 0.820 | 0.520 | 38 | 0 |

### soc

| Decisions | Routing Learn | Routing Control | Accuracy Learn | Accuracy Control | Saves | Hurts |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 50 | 0.690 | 0.590 | 0.800 | 0.740 | 37 | 0 |
| 100 | 0.780 | 0.710 | 0.880 | 0.820 | 36 | 0 |
| 150 | 0.760 | 0.600 | 0.840 | 0.700 | 34 | 0 |
| 200 | 0.790 | 0.680 | 0.840 | 0.700 | 32 | 0 |
| 250 | 0.720 | 0.600 | 0.880 | 0.740 | 36 | 0 |
| 300 | 0.760 | 0.620 | 0.920 | 0.780 | 39 | 0 |
| 350 | 0.750 | 0.620 | 0.860 | 0.720 | 34 | 0 |
| 400 | 0.830 | 0.670 | 0.960 | 0.740 | 37 | 0 |
| 450 | 0.810 | 0.650 | 0.940 | 0.660 | 41 | 0 |
| 500 | 0.810 | 0.690 | 0.860 | 0.720 | 33 | 0 |

### s2p

| Decisions | Routing Learn | Routing Control | Accuracy Learn | Accuracy Control | Saves | Hurts |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 50 | 0.570 | 0.560 | 0.760 | 0.740 | 32 | 0 |
| 100 | 0.550 | 0.570 | 0.740 | 0.740 | 29 | 0 |
| 150 | 0.630 | 0.610 | 0.780 | 0.720 | 32 | 0 |
| 200 | 0.610 | 0.590 | 0.780 | 0.760 | 33 | 0 |
| 250 | 0.590 | 0.620 | 0.800 | 0.760 | 34 | 0 |
| 300 | 0.680 | 0.560 | 0.800 | 0.720 | 36 | 0 |
| 350 | 0.720 | 0.610 | 0.820 | 0.760 | 35 | 0 |
| 400 | 0.690 | 0.610 | 0.860 | 0.760 | 37 | 0 |
| 450 | 0.700 | 0.630 | 0.820 | 0.760 | 33 | 0 |
| 500 | 0.650 | 0.620 | 0.840 | 0.780 | 39 | 0 |
