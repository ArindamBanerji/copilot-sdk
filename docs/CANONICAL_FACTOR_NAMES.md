# Canonical Factor Names (Runtime-Verified)

**Last verified:** June 14, 2026 (Scan A runtime introspection)
**Source:** CompoundingScorer.from_preset() for each domain

## SOC (6 categories x 4 actions x 6 factors = 144)

Categories: credential_access, malware_execution, lateral_movement, data_exfiltration, insider_threat, cloud_infrastructure

Actions: escalate, investigate, suppress, monitor

Factors: privileged_identity_context, asset_criticality, threat_intel_enrichment, pattern_history, time_anomaly, device_trust

## S2P (5 x 5 x 7 = 175)

Categories: quantity_mismatch, duplicate_risk, price_variance, compliance_flag, timing_anomaly

Actions: auto_approve, hold_for_review, flag_leakage, escalate_compliance, reject

Factors: match_status, amount_variance_ratio, supplier_risk_score, po_coverage, historical_exception_rate, contract_compliance_flag, urgency_score

## Trading (5 x 4 x 10 = 200)

Categories: momentum_breakout, mean_reversion, trend_following, volatility_event, sector_rotation

Actions: strong_execution, partial_execution, poor_execution, skip_recommended

Factors: signal_alignment, market_regime, volume_confirmation, risk_reward_ratio, portfolio_heat, sector_momentum, correlation_risk, options_delta_exposure, options_iv_percentile, options_gamma_risk

## Purchasing (5 x 4 x 7 = 140)

Categories: proteins, produce, dairy, dry_goods, beverages

Actions: order_as_planned, order_more, order_less, skip

Factors: expected_demand, day_of_week, weather_forecast, event_flag, historical_waste, supplier_lead_time, price_memory_index

## DataOps (6 x 5 x 6 = 180)

Categories: schema_change, volume_anomaly, freshness_violation, pipeline_failure, quality_degradation, access_pattern

Actions: auto_resolve, investigate, escalate, defer, remediate

Factors: severity_score, blast_radius, recurrence_probability, data_sensitivity, business_impact, resolution_complexity
