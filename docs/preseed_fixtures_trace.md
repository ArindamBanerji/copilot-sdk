# SDK-FIXTURES Conservation Trace

Date: 2026-10-20T09:38:05-07:00
Target: Purchasing backend on localhost:8020

## PROBE 1: Pre-State

health:
```json
{
  "method": "GET",
  "request_body": null,
  "response_body": {
    "alpha": 0.7479,
    "cache_hits": 0,
    "cache_misses": 0,
    "cache_size": 0,
    "cutover_evidence": {},
    "cutover_ready": false,
    "domain": "purchasing",
    "engine": {
      "gae": "gae.profile_scorer.ProfileScorer",
      "scoring": "copilot_sdk.scoring.CompoundingScorer"
    },
    "graph_backend": "age",
    "graph_connected": true,
    "graph_connection": {
      "connect_timeout_seconds": 3,
      "connection_mode": "pooled",
      "pool_available": true,
      "pool_available_connections": 2,
      "pool_max_size": 15,
      "pool_min_size": 2,
      "pool_requested": true,
      "pool_requests_waiting": 0,
      "pool_size": 2,
      "pool_timeout_seconds": 5.0,
      "statement_timeout_ms": 8000
    },
    "graph_name": "soc_graph",
    "graph_source": "graph",
    "graph_status": {
      "checked_at": "2026-10-20T16:38:07.470084+00:00",
      "components": {
        "decisions": "ready",
        "learning_restore": "ready",
        "topology": "ready"
      },
      "connected": true,
      "dsn_source": "env:GRAPH_DSN",
      "graph_name": "soc_graph",
      "storage_identity": "268fc3c2a353ab6b28a2e1be"
    },
    "graph_store_status": "available",
    "node_count": 260,
    "node_count_scope": "domain_decisions",
    "phase": "B",
    "product_claim_allowed": false,
    "production_ready": true,
    "protocol_version": "v2",
    "ready": true,
    "status": "ok"
  },
  "status_code": 200,
  "url": "http://localhost:8020/api/health"
}
```

conservation_status:
```json
{
  "method": "GET",
  "request_body": null,
  "response_body": {
    "V": 238,
    "alpha": 1.0,
    "baseline": 0.75,
    "baseline_q": 0.75,
    "categories_total": 5,
    "categories_with_data": 5,
    "conservation_applicable": true,
    "conservation_mode": "normal",
    "correct_count": 178,
    "domain": "purchasing",
    "engine": {
      "component": "conservation_status",
      "gae": "gae.calibration"
    },
    "evidence_label": "MODELED / PILOT-TARGET \u2014 not measured ROI",
    "g_abs": {
      "active": false,
      "alpha_q_v": 178.0,
      "theta_min": 0.0989
    },
    "g_rate": {
      "active": false,
      "long_baseline": 1.0,
      "m_rate": 0.85,
      "short_accuracy": 1.0,
      "short_window_count": 20,
      "threshold": 0.85,
      "w_short": 20
    },
    "g_rel": {
      "active": false,
      "baseline": 0.75,
      "rolling_accuracy": 0.7478991596638656,
      "threshold": 0.5249999999999999
    },
    "headroom": 177.9011,
    "passed": true,
    "penalty_ratio": 3.0,
    "projected_divergence_week": 5,
    "projected_weekly_net_benefit": 230.0,
    "projection_definition": "First full week cumulative assumed net benefit covers setup cost",
    "projection_inputs": {
      "benefit_per_decision": 2.5,
      "provenance": "SDK-PRESEED planted demo assumptions",
      "required_verified_decisions": 200,
      "setup_cost": 1000.0,
      "weekly_decisions": 100.0,
      "weekly_operating_cost": 20.0
    },
    "projection_status": "break_even_projected",
    "projection_tier": "T-sim",
    "q": 0.7478991596638656,
    "readiness_definition": "Verified coverage vs configured target; not permission to act",
    "readiness_score": 1.0,
    "reason": "Signal 178.00 exceeds theta_min 0.0989 with headroom 177.90. Accuracy 74.8% is above 70% of baseline (75.0%). Status is GREEN with \u03b1=1.00 across 238 verified decisions.",
    "relative_trigger": 0.5249999999999999,
    "relative_trigger_ratio": 0.7,
    "signal": 178.0,
    "status": "GREEN",
    "theta_min": 0.0989,
    "total_categories": 5,
    "total_decisions": 238,
    "verified_count": 238
  },
  "status_code": 200,
  "url": "http://localhost:8020/api/conservation/status"
}
```

decision_count: `238` (source: `conservation_status.total_decisions`)
theta_min: `0.0989`
q: `0.7478991596638656`

## PROBE 2: Degradation Sequence (5 decisions)

### Decision 1 (fixture seed index 30)

conservation_before:
```json
{
  "method": "GET",
  "request_body": null,
  "response_body": {
    "V": 238,
    "alpha": 1.0,
    "baseline": 0.75,
    "baseline_q": 0.75,
    "categories_total": 5,
    "categories_with_data": 5,
    "conservation_applicable": true,
    "conservation_mode": "normal",
    "correct_count": 178,
    "domain": "purchasing",
    "engine": {
      "component": "conservation_status",
      "gae": "gae.calibration"
    },
    "evidence_label": "MODELED / PILOT-TARGET \u2014 not measured ROI",
    "g_abs": {
      "active": false,
      "alpha_q_v": 178.0,
      "theta_min": 0.0989
    },
    "g_rate": {
      "active": false,
      "long_baseline": 1.0,
      "m_rate": 0.85,
      "short_accuracy": 1.0,
      "short_window_count": 20,
      "threshold": 0.85,
      "w_short": 20
    },
    "g_rel": {
      "active": false,
      "baseline": 0.75,
      "rolling_accuracy": 0.7478991596638656,
      "threshold": 0.5249999999999999
    },
    "headroom": 177.9011,
    "passed": true,
    "penalty_ratio": 3.0,
    "projected_divergence_week": 5,
    "projected_weekly_net_benefit": 230.0,
    "projection_definition": "First full week cumulative assumed net benefit covers setup cost",
    "projection_inputs": {
      "benefit_per_decision": 2.5,
      "provenance": "SDK-PRESEED planted demo assumptions",
      "required_verified_decisions": 200,
      "setup_cost": 1000.0,
      "weekly_decisions": 100.0,
      "weekly_operating_cost": 20.0
    },
    "projection_status": "break_even_projected",
    "projection_tier": "T-sim",
    "q": 0.7478991596638656,
    "readiness_definition": "Verified coverage vs configured target; not permission to act",
    "readiness_score": 1.0,
    "reason": "Signal 178.00 exceeds theta_min 0.0989 with headroom 177.90. Accuracy 74.8% is above 70% of baseline (75.0%). Status is GREEN with \u03b1=1.00 across 238 verified decisions.",
    "relative_trigger": 0.5249999999999999,
    "relative_trigger_ratio": 0.7,
    "signal": 178.0,
    "status": "GREEN",
    "theta_min": 0.0989,
    "total_categories": 5,
    "total_decisions": 238,
    "verified_count": 238
  },
  "status_code": 200,
  "url": "http://localhost:8020/api/conservation/status"
}
```

score_response summary:
```json
{
  "action": "order_more",
  "confidence": 0.6105921469292258,
  "decision_id": "dc30b36a2010",
  "score": null
}
```

score_response full:
```json
{
  "method": "POST",
  "request_body": {
    "category": "produce",
    "context": {
      "evidence_tier": "T-sim",
      "fixture": "SDK-PRESEED",
      "planted": true,
      "provenance": "sample",
      "seed_index": 30
    },
    "factors": {
      "day_of_week": 0.4,
      "event_flag": 0.1,
      "expected_demand": 0.45,
      "historical_waste": 0.18,
      "price_memory_index": 0.5,
      "supplier_lead_time": 0.12,
      "weather_forecast": 0.35
    },
    "metadata": {
      "evidence_tier": "T-sim",
      "fixture": "SDK-PRESEED",
      "planted": true,
      "provenance": "sample",
      "seed_index": 30
    }
  },
  "response_body": {
    "action": "order_more",
    "action_index": 1,
    "category": "produce",
    "confidence": 0.6105921469292258,
    "decision_id": "dc30b36a2010",
    "engine": {
      "gae": "gae.profile_scorer.ProfileScorer",
      "scoring": "copilot_sdk.scoring.CompoundingScorer"
    },
    "factors": {
      "day_of_week": 0.4,
      "event_flag": 0.1,
      "expected_demand": 0.45,
      "historical_waste": 0.18,
      "price_memory_index": 0.5,
      "supplier_lead_time": 0.12,
      "weather_forecast": 0.35
    },
    "probabilities": [
      0.29636675106891175,
      0.6105921469292258,
      0.06655286180252667,
      0.026488240199335707
    ]
  },
  "status_code": 200,
  "url": "http://localhost:8020/api/score"
}
```

learn_response summary (including conservation fields):
```json
{
  "conservation_fields": {
    "alpha": 1.0,
    "category_coverage": 1.0,
    "conservation_status": "RED",
    "correct_count": 178,
    "override_rate": 0.25210084033613445,
    "pause_reason": "conservation_red",
    "paused": true,
    "q": 0.7478991596638656,
    "reason": "conservation_red",
    "recent_q": 0.74,
    "recent_window": 100,
    "status": "paused",
    "theta_min": 0.75,
    "verified_count": 238
  },
  "decision_id": "dc30b36a2010",
  "http_status": 200,
  "outcome": "overridden"
}
```

learn_response full:
```json
{
  "method": "POST",
  "request_body": {
    "actual_action": "order_as_planned",
    "context": {
      "evidence_tier": "T-sim",
      "fixture": "SDK-PRESEED",
      "planted": true,
      "provenance": "sample",
      "seed_index": 30
    },
    "decision_id": "dc30b36a2010",
    "outcome": "overridden"
  },
  "response_body": {
    "action": "order_more",
    "alpha": 1.0,
    "bootstrap": null,
    "category_coverage": 1.0,
    "centroid_delta": 0.0,
    "centroid_updated": false,
    "cold_start": null,
    "confidence": 0.6105921469292258,
    "conservation_status": "RED",
    "correct_count": 178,
    "decision_id": "dc30b36a2010",
    "decisions_total": 238,
    "engine": {
      "gae": "gae.profile_scorer.ProfileScorer",
      "scoring": "copilot_sdk.scoring.CompoundingScorer"
    },
    "iks_after": 0.0,
    "iks_before": 0.0,
    "outcome": "overridden",
    "override_rate": 0.25210084033613445,
    "pause_reason": "conservation_red",
    "paused": true,
    "previous_reward": null,
    "q": 0.7478991596638656,
    "reason": "conservation_red",
    "recent_q": 0.74,
    "recent_window": 100,
    "reward": -0.05,
    "reward_multiplier": 1.0,
    "status": "paused",
    "theta_min": 0.75,
    "verified_count": 238
  },
  "status_code": 200,
  "url": "http://localhost:8020/api/learn"
}
```

conservation_after:
```json
{
  "method": "GET",
  "request_body": null,
  "response_body": {
    "V": 238,
    "alpha": 1.0,
    "baseline": 0.75,
    "baseline_q": 0.75,
    "categories_total": 5,
    "categories_with_data": 5,
    "conservation_applicable": true,
    "conservation_mode": "normal",
    "correct_count": 178,
    "domain": "purchasing",
    "engine": {
      "component": "conservation_status",
      "gae": "gae.calibration"
    },
    "evidence_label": "MODELED / PILOT-TARGET \u2014 not measured ROI",
    "g_abs": {
      "active": false,
      "alpha_q_v": 178.0,
      "theta_min": 0.0989
    },
    "g_rate": {
      "active": false,
      "long_baseline": 1.0,
      "m_rate": 0.85,
      "short_accuracy": 1.0,
      "short_window_count": 20,
      "threshold": 0.85,
      "w_short": 20
    },
    "g_rel": {
      "active": false,
      "baseline": 0.75,
      "rolling_accuracy": 0.7478991596638656,
      "threshold": 0.5249999999999999
    },
    "headroom": 177.9011,
    "passed": true,
    "penalty_ratio": 3.0,
    "projected_divergence_week": 5,
    "projected_weekly_net_benefit": 230.0,
    "projection_definition": "First full week cumulative assumed net benefit covers setup cost",
    "projection_inputs": {
      "benefit_per_decision": 2.5,
      "provenance": "SDK-PRESEED planted demo assumptions",
      "required_verified_decisions": 200,
      "setup_cost": 1000.0,
      "weekly_decisions": 100.0,
      "weekly_operating_cost": 20.0
    },
    "projection_status": "break_even_projected",
    "projection_tier": "T-sim",
    "q": 0.7478991596638656,
    "readiness_definition": "Verified coverage vs configured target; not permission to act",
    "readiness_score": 1.0,
    "reason": "Signal 178.00 exceeds theta_min 0.0989 with headroom 177.90. Accuracy 74.8% is above 70% of baseline (75.0%). Status is GREEN with \u03b1=1.00 across 238 verified decisions.",
    "relative_trigger": 0.5249999999999999,
    "relative_trigger_ratio": 0.7,
    "signal": 178.0,
    "status": "GREEN",
    "theta_min": 0.0989,
    "total_categories": 5,
    "total_decisions": 238,
    "verified_count": 238
  },
  "status_code": 200,
  "url": "http://localhost:8020/api/conservation/status"
}
```

### Decision 2 (fixture seed index 31)

conservation_before:
```json
{
  "method": "GET",
  "request_body": null,
  "response_body": {
    "V": 238,
    "alpha": 1.0,
    "baseline": 0.75,
    "baseline_q": 0.75,
    "categories_total": 5,
    "categories_with_data": 5,
    "conservation_applicable": true,
    "conservation_mode": "normal",
    "correct_count": 178,
    "domain": "purchasing",
    "engine": {
      "component": "conservation_status",
      "gae": "gae.calibration"
    },
    "evidence_label": "MODELED / PILOT-TARGET \u2014 not measured ROI",
    "g_abs": {
      "active": false,
      "alpha_q_v": 178.0,
      "theta_min": 0.0989
    },
    "g_rate": {
      "active": false,
      "long_baseline": 1.0,
      "m_rate": 0.85,
      "short_accuracy": 1.0,
      "short_window_count": 20,
      "threshold": 0.85,
      "w_short": 20
    },
    "g_rel": {
      "active": false,
      "baseline": 0.75,
      "rolling_accuracy": 0.7478991596638656,
      "threshold": 0.5249999999999999
    },
    "headroom": 177.9011,
    "passed": true,
    "penalty_ratio": 3.0,
    "projected_divergence_week": 5,
    "projected_weekly_net_benefit": 230.0,
    "projection_definition": "First full week cumulative assumed net benefit covers setup cost",
    "projection_inputs": {
      "benefit_per_decision": 2.5,
      "provenance": "SDK-PRESEED planted demo assumptions",
      "required_verified_decisions": 200,
      "setup_cost": 1000.0,
      "weekly_decisions": 100.0,
      "weekly_operating_cost": 20.0
    },
    "projection_status": "break_even_projected",
    "projection_tier": "T-sim",
    "q": 0.7478991596638656,
    "readiness_definition": "Verified coverage vs configured target; not permission to act",
    "readiness_score": 1.0,
    "reason": "Signal 178.00 exceeds theta_min 0.0989 with headroom 177.90. Accuracy 74.8% is above 70% of baseline (75.0%). Status is GREEN with \u03b1=1.00 across 238 verified decisions.",
    "relative_trigger": 0.5249999999999999,
    "relative_trigger_ratio": 0.7,
    "signal": 178.0,
    "status": "GREEN",
    "theta_min": 0.0989,
    "total_categories": 5,
    "total_decisions": 238,
    "verified_count": 238
  },
  "status_code": 200,
  "url": "http://localhost:8020/api/conservation/status"
}
```

score_response summary:
```json
{
  "action": "order_as_planned",
  "confidence": 0.55591787573574,
  "decision_id": "149b8560bf9d",
  "score": null
}
```

score_response full:
```json
{
  "method": "POST",
  "request_body": {
    "category": "produce",
    "context": {
      "evidence_tier": "T-sim",
      "fixture": "SDK-PRESEED",
      "planted": true,
      "provenance": "sample",
      "seed_index": 31
    },
    "factors": {
      "day_of_week": 0.52,
      "event_flag": 0.2,
      "expected_demand": 0.66,
      "historical_waste": 0.24,
      "price_memory_index": 0.5,
      "supplier_lead_time": 0.2,
      "weather_forecast": 0.75
    },
    "metadata": {
      "evidence_tier": "T-sim",
      "fixture": "SDK-PRESEED",
      "planted": true,
      "provenance": "sample",
      "seed_index": 31
    }
  },
  "response_body": {
    "action": "order_as_planned",
    "action_index": 0,
    "category": "produce",
    "confidence": 0.55591787573574,
    "decision_id": "149b8560bf9d",
    "engine": {
      "gae": "gae.profile_scorer.ProfileScorer",
      "scoring": "copilot_sdk.scoring.CompoundingScorer"
    },
    "factors": {
      "day_of_week": 0.52,
      "event_flag": 0.2,
      "expected_demand": 0.66,
      "historical_waste": 0.24,
      "price_memory_index": 0.5,
      "supplier_lead_time": 0.2,
      "weather_forecast": 0.75
    },
    "probabilities": [
      0.55591787573574,
      0.4238051021708531,
      0.014383828213816759,
      0.005893193879590159
    ]
  },
  "status_code": 200,
  "url": "http://localhost:8020/api/score"
}
```

learn_response summary (including conservation fields):
```json
{
  "conservation_fields": {
    "alpha": 1.0,
    "category_coverage": 1.0,
    "conservation_status": "RED",
    "correct_count": 178,
    "override_rate": 0.25210084033613445,
    "pause_reason": "conservation_red",
    "paused": true,
    "q": 0.7478991596638656,
    "reason": "conservation_red",
    "recent_q": 0.74,
    "recent_window": 100,
    "status": "paused",
    "theta_min": 0.75,
    "verified_count": 238
  },
  "decision_id": "149b8560bf9d",
  "http_status": 200,
  "outcome": "overridden"
}
```

learn_response full:
```json
{
  "method": "POST",
  "request_body": {
    "actual_action": "order_more",
    "context": {
      "evidence_tier": "T-sim",
      "fixture": "SDK-PRESEED",
      "planted": true,
      "provenance": "sample",
      "seed_index": 31
    },
    "decision_id": "149b8560bf9d",
    "outcome": "overridden"
  },
  "response_body": {
    "action": "order_as_planned",
    "alpha": 1.0,
    "bootstrap": null,
    "category_coverage": 1.0,
    "centroid_delta": 0.0,
    "centroid_updated": false,
    "cold_start": null,
    "confidence": 0.55591787573574,
    "conservation_status": "RED",
    "correct_count": 178,
    "decision_id": "149b8560bf9d",
    "decisions_total": 238,
    "engine": {
      "gae": "gae.profile_scorer.ProfileScorer",
      "scoring": "copilot_sdk.scoring.CompoundingScorer"
    },
    "iks_after": 0.0,
    "iks_before": 0.0,
    "outcome": "overridden",
    "override_rate": 0.25210084033613445,
    "pause_reason": "conservation_red",
    "paused": true,
    "previous_reward": null,
    "q": 0.7478991596638656,
    "reason": "conservation_red",
    "recent_q": 0.74,
    "recent_window": 100,
    "reward": -0.05,
    "reward_multiplier": 1.0,
    "status": "paused",
    "theta_min": 0.75,
    "verified_count": 238
  },
  "status_code": 200,
  "url": "http://localhost:8020/api/learn"
}
```

conservation_after:
```json
{
  "method": "GET",
  "request_body": null,
  "response_body": {
    "V": 238,
    "alpha": 1.0,
    "baseline": 0.75,
    "baseline_q": 0.75,
    "categories_total": 5,
    "categories_with_data": 5,
    "conservation_applicable": true,
    "conservation_mode": "normal",
    "correct_count": 178,
    "domain": "purchasing",
    "engine": {
      "component": "conservation_status",
      "gae": "gae.calibration"
    },
    "evidence_label": "MODELED / PILOT-TARGET \u2014 not measured ROI",
    "g_abs": {
      "active": false,
      "alpha_q_v": 178.0,
      "theta_min": 0.0989
    },
    "g_rate": {
      "active": false,
      "long_baseline": 1.0,
      "m_rate": 0.85,
      "short_accuracy": 1.0,
      "short_window_count": 20,
      "threshold": 0.85,
      "w_short": 20
    },
    "g_rel": {
      "active": false,
      "baseline": 0.75,
      "rolling_accuracy": 0.7478991596638656,
      "threshold": 0.5249999999999999
    },
    "headroom": 177.9011,
    "passed": true,
    "penalty_ratio": 3.0,
    "projected_divergence_week": 5,
    "projected_weekly_net_benefit": 230.0,
    "projection_definition": "First full week cumulative assumed net benefit covers setup cost",
    "projection_inputs": {
      "benefit_per_decision": 2.5,
      "provenance": "SDK-PRESEED planted demo assumptions",
      "required_verified_decisions": 200,
      "setup_cost": 1000.0,
      "weekly_decisions": 100.0,
      "weekly_operating_cost": 20.0
    },
    "projection_status": "break_even_projected",
    "projection_tier": "T-sim",
    "q": 0.7478991596638656,
    "readiness_definition": "Verified coverage vs configured target; not permission to act",
    "readiness_score": 1.0,
    "reason": "Signal 178.00 exceeds theta_min 0.0989 with headroom 177.90. Accuracy 74.8% is above 70% of baseline (75.0%). Status is GREEN with \u03b1=1.00 across 238 verified decisions.",
    "relative_trigger": 0.5249999999999999,
    "relative_trigger_ratio": 0.7,
    "signal": 178.0,
    "status": "GREEN",
    "theta_min": 0.0989,
    "total_categories": 5,
    "total_decisions": 238,
    "verified_count": 238
  },
  "status_code": 200,
  "url": "http://localhost:8020/api/conservation/status"
}
```

### Decision 3 (fixture seed index 32)

conservation_before:
```json
{
  "method": "GET",
  "request_body": null,
  "response_body": {
    "V": 238,
    "alpha": 1.0,
    "baseline": 0.75,
    "baseline_q": 0.75,
    "categories_total": 5,
    "categories_with_data": 5,
    "conservation_applicable": true,
    "conservation_mode": "normal",
    "correct_count": 178,
    "domain": "purchasing",
    "engine": {
      "component": "conservation_status",
      "gae": "gae.calibration"
    },
    "evidence_label": "MODELED / PILOT-TARGET \u2014 not measured ROI",
    "g_abs": {
      "active": false,
      "alpha_q_v": 178.0,
      "theta_min": 0.0989
    },
    "g_rate": {
      "active": false,
      "long_baseline": 1.0,
      "m_rate": 0.85,
      "short_accuracy": 1.0,
      "short_window_count": 20,
      "threshold": 0.85,
      "w_short": 20
    },
    "g_rel": {
      "active": false,
      "baseline": 0.75,
      "rolling_accuracy": 0.7478991596638656,
      "threshold": 0.5249999999999999
    },
    "headroom": 177.9011,
    "passed": true,
    "penalty_ratio": 3.0,
    "projected_divergence_week": 5,
    "projected_weekly_net_benefit": 230.0,
    "projection_definition": "First full week cumulative assumed net benefit covers setup cost",
    "projection_inputs": {
      "benefit_per_decision": 2.5,
      "provenance": "SDK-PRESEED planted demo assumptions",
      "required_verified_decisions": 200,
      "setup_cost": 1000.0,
      "weekly_decisions": 100.0,
      "weekly_operating_cost": 20.0
    },
    "projection_status": "break_even_projected",
    "projection_tier": "T-sim",
    "q": 0.7478991596638656,
    "readiness_definition": "Verified coverage vs configured target; not permission to act",
    "readiness_score": 1.0,
    "reason": "Signal 178.00 exceeds theta_min 0.0989 with headroom 177.90. Accuracy 74.8% is above 70% of baseline (75.0%). Status is GREEN with \u03b1=1.00 across 238 verified decisions.",
    "relative_trigger": 0.5249999999999999,
    "relative_trigger_ratio": 0.7,
    "signal": 178.0,
    "status": "GREEN",
    "theta_min": 0.0989,
    "total_categories": 5,
    "total_decisions": 238,
    "verified_count": 238
  },
  "status_code": 200,
  "url": "http://localhost:8020/api/conservation/status"
}
```

score_response summary:
```json
{
  "action": "order_as_planned",
  "confidence": 0.9595857358300718,
  "decision_id": "20f947f540c7",
  "score": null
}
```

score_response full:
```json
{
  "method": "POST",
  "request_body": {
    "category": "dairy",
    "context": {
      "evidence_tier": "T-sim",
      "fixture": "SDK-PRESEED",
      "planted": true,
      "provenance": "sample",
      "seed_index": 32
    },
    "factors": {
      "day_of_week": 0.34,
      "event_flag": 0.1,
      "expected_demand": 0.66,
      "historical_waste": 0.06,
      "price_memory_index": 0.5,
      "supplier_lead_time": 0.3,
      "weather_forecast": 0.6
    },
    "metadata": {
      "evidence_tier": "T-sim",
      "fixture": "SDK-PRESEED",
      "planted": true,
      "provenance": "sample",
      "seed_index": 32
    }
  },
  "response_body": {
    "action": "order_as_planned",
    "action_index": 0,
    "category": "dairy",
    "confidence": 0.9595857358300718,
    "decision_id": "20f947f540c7",
    "engine": {
      "gae": "gae.profile_scorer.ProfileScorer",
      "scoring": "copilot_sdk.scoring.CompoundingScorer"
    },
    "factors": {
      "day_of_week": 0.34,
      "event_flag": 0.1,
      "expected_demand": 0.66,
      "historical_waste": 0.06,
      "price_memory_index": 0.5,
      "supplier_lead_time": 0.3,
      "weather_forecast": 0.6
    },
    "probabilities": [
      0.9595857358300718,
      0.012990223501404968,
      0.014288822755824259,
      0.01313521791269909
    ]
  },
  "status_code": 200,
  "url": "http://localhost:8020/api/score"
}
```

learn_response summary (including conservation fields):
```json
{
  "conservation_fields": {
    "alpha": 1.0,
    "category_coverage": 1.0,
    "conservation_status": "RED",
    "correct_count": 178,
    "override_rate": 0.25210084033613445,
    "pause_reason": "conservation_red",
    "paused": true,
    "q": 0.7478991596638656,
    "reason": "conservation_red",
    "recent_q": 0.74,
    "recent_window": 100,
    "status": "paused",
    "theta_min": 0.75,
    "verified_count": 238
  },
  "decision_id": "20f947f540c7",
  "http_status": 200,
  "outcome": "overridden"
}
```

learn_response full:
```json
{
  "method": "POST",
  "request_body": {
    "actual_action": "order_more",
    "context": {
      "evidence_tier": "T-sim",
      "fixture": "SDK-PRESEED",
      "planted": true,
      "provenance": "sample",
      "seed_index": 32
    },
    "decision_id": "20f947f540c7",
    "outcome": "overridden"
  },
  "response_body": {
    "action": "order_as_planned",
    "alpha": 1.0,
    "bootstrap": null,
    "category_coverage": 1.0,
    "centroid_delta": 0.0,
    "centroid_updated": false,
    "cold_start": null,
    "confidence": 0.9595857358300718,
    "conservation_status": "RED",
    "correct_count": 178,
    "decision_id": "20f947f540c7",
    "decisions_total": 238,
    "engine": {
      "gae": "gae.profile_scorer.ProfileScorer",
      "scoring": "copilot_sdk.scoring.CompoundingScorer"
    },
    "iks_after": 0.0,
    "iks_before": 0.0,
    "outcome": "overridden",
    "override_rate": 0.25210084033613445,
    "pause_reason": "conservation_red",
    "paused": true,
    "previous_reward": null,
    "q": 0.7478991596638656,
    "reason": "conservation_red",
    "recent_q": 0.74,
    "recent_window": 100,
    "reward": -0.05,
    "reward_multiplier": 1.0,
    "status": "paused",
    "theta_min": 0.75,
    "verified_count": 238
  },
  "status_code": 200,
  "url": "http://localhost:8020/api/learn"
}
```

conservation_after:
```json
{
  "method": "GET",
  "request_body": null,
  "response_body": {
    "V": 238,
    "alpha": 1.0,
    "baseline": 0.75,
    "baseline_q": 0.75,
    "categories_total": 5,
    "categories_with_data": 5,
    "conservation_applicable": true,
    "conservation_mode": "normal",
    "correct_count": 178,
    "domain": "purchasing",
    "engine": {
      "component": "conservation_status",
      "gae": "gae.calibration"
    },
    "evidence_label": "MODELED / PILOT-TARGET \u2014 not measured ROI",
    "g_abs": {
      "active": false,
      "alpha_q_v": 178.0,
      "theta_min": 0.0989
    },
    "g_rate": {
      "active": false,
      "long_baseline": 1.0,
      "m_rate": 0.85,
      "short_accuracy": 1.0,
      "short_window_count": 20,
      "threshold": 0.85,
      "w_short": 20
    },
    "g_rel": {
      "active": false,
      "baseline": 0.75,
      "rolling_accuracy": 0.7478991596638656,
      "threshold": 0.5249999999999999
    },
    "headroom": 177.9011,
    "passed": true,
    "penalty_ratio": 3.0,
    "projected_divergence_week": 5,
    "projected_weekly_net_benefit": 230.0,
    "projection_definition": "First full week cumulative assumed net benefit covers setup cost",
    "projection_inputs": {
      "benefit_per_decision": 2.5,
      "provenance": "SDK-PRESEED planted demo assumptions",
      "required_verified_decisions": 200,
      "setup_cost": 1000.0,
      "weekly_decisions": 100.0,
      "weekly_operating_cost": 20.0
    },
    "projection_status": "break_even_projected",
    "projection_tier": "T-sim",
    "q": 0.7478991596638656,
    "readiness_definition": "Verified coverage vs configured target; not permission to act",
    "readiness_score": 1.0,
    "reason": "Signal 178.00 exceeds theta_min 0.0989 with headroom 177.90. Accuracy 74.8% is above 70% of baseline (75.0%). Status is GREEN with \u03b1=1.00 across 238 verified decisions.",
    "relative_trigger": 0.5249999999999999,
    "relative_trigger_ratio": 0.7,
    "signal": 178.0,
    "status": "GREEN",
    "theta_min": 0.0989,
    "total_categories": 5,
    "total_decisions": 238,
    "verified_count": 238
  },
  "status_code": 200,
  "url": "http://localhost:8020/api/conservation/status"
}
```

### Decision 4 (fixture seed index 33)

conservation_before:
```json
{
  "method": "GET",
  "request_body": null,
  "response_body": {
    "V": 238,
    "alpha": 1.0,
    "baseline": 0.75,
    "baseline_q": 0.75,
    "categories_total": 5,
    "categories_with_data": 5,
    "conservation_applicable": true,
    "conservation_mode": "normal",
    "correct_count": 178,
    "domain": "purchasing",
    "engine": {
      "component": "conservation_status",
      "gae": "gae.calibration"
    },
    "evidence_label": "MODELED / PILOT-TARGET \u2014 not measured ROI",
    "g_abs": {
      "active": false,
      "alpha_q_v": 178.0,
      "theta_min": 0.0989
    },
    "g_rate": {
      "active": false,
      "long_baseline": 1.0,
      "m_rate": 0.85,
      "short_accuracy": 1.0,
      "short_window_count": 20,
      "threshold": 0.85,
      "w_short": 20
    },
    "g_rel": {
      "active": false,
      "baseline": 0.75,
      "rolling_accuracy": 0.7478991596638656,
      "threshold": 0.5249999999999999
    },
    "headroom": 177.9011,
    "passed": true,
    "penalty_ratio": 3.0,
    "projected_divergence_week": 5,
    "projected_weekly_net_benefit": 230.0,
    "projection_definition": "First full week cumulative assumed net benefit covers setup cost",
    "projection_inputs": {
      "benefit_per_decision": 2.5,
      "provenance": "SDK-PRESEED planted demo assumptions",
      "required_verified_decisions": 200,
      "setup_cost": 1000.0,
      "weekly_decisions": 100.0,
      "weekly_operating_cost": 20.0
    },
    "projection_status": "break_even_projected",
    "projection_tier": "T-sim",
    "q": 0.7478991596638656,
    "readiness_definition": "Verified coverage vs configured target; not permission to act",
    "readiness_score": 1.0,
    "reason": "Signal 178.00 exceeds theta_min 0.0989 with headroom 177.90. Accuracy 74.8% is above 70% of baseline (75.0%). Status is GREEN with \u03b1=1.00 across 238 verified decisions.",
    "relative_trigger": 0.5249999999999999,
    "relative_trigger_ratio": 0.7,
    "signal": 178.0,
    "status": "GREEN",
    "theta_min": 0.0989,
    "total_categories": 5,
    "total_decisions": 238,
    "verified_count": 238
  },
  "status_code": 200,
  "url": "http://localhost:8020/api/conservation/status"
}
```

score_response summary:
```json
{
  "action": "order_as_planned",
  "confidence": 0.950146755550136,
  "decision_id": "6338e872cff3",
  "score": null
}
```

score_response full:
```json
{
  "method": "POST",
  "request_body": {
    "category": "dairy",
    "context": {
      "evidence_tier": "T-sim",
      "fixture": "SDK-PRESEED",
      "planted": true,
      "provenance": "sample",
      "seed_index": 33
    },
    "factors": {
      "day_of_week": 0.4,
      "event_flag": 0.08,
      "expected_demand": 0.6,
      "historical_waste": 0.08,
      "price_memory_index": 0.5,
      "supplier_lead_time": 0.32,
      "weather_forecast": 0.28
    },
    "metadata": {
      "evidence_tier": "T-sim",
      "fixture": "SDK-PRESEED",
      "planted": true,
      "provenance": "sample",
      "seed_index": 33
    }
  },
  "response_body": {
    "action": "order_as_planned",
    "action_index": 0,
    "category": "dairy",
    "confidence": 0.950146755550136,
    "decision_id": "6338e872cff3",
    "engine": {
      "gae": "gae.profile_scorer.ProfileScorer",
      "scoring": "copilot_sdk.scoring.CompoundingScorer"
    },
    "factors": {
      "day_of_week": 0.4,
      "event_flag": 0.08,
      "expected_demand": 0.6,
      "historical_waste": 0.08,
      "price_memory_index": 0.5,
      "supplier_lead_time": 0.32,
      "weather_forecast": 0.28
    },
    "probabilities": [
      0.950146755550136,
      0.01764881199738599,
      0.024622599336840502,
      0.00758183311563756
    ]
  },
  "status_code": 200,
  "url": "http://localhost:8020/api/score"
}
```

learn_response summary (including conservation fields):
```json
{
  "conservation_fields": {
    "alpha": 1.0,
    "category_coverage": 1.0,
    "conservation_status": "RED",
    "correct_count": 178,
    "override_rate": 0.25210084033613445,
    "pause_reason": "conservation_red",
    "paused": true,
    "q": 0.7478991596638656,
    "reason": "conservation_red",
    "recent_q": 0.74,
    "recent_window": 100,
    "status": "paused",
    "theta_min": 0.75,
    "verified_count": 238
  },
  "decision_id": "6338e872cff3",
  "http_status": 200,
  "outcome": "overridden"
}
```

learn_response full:
```json
{
  "method": "POST",
  "request_body": {
    "actual_action": "order_more",
    "context": {
      "evidence_tier": "T-sim",
      "fixture": "SDK-PRESEED",
      "planted": true,
      "provenance": "sample",
      "seed_index": 33
    },
    "decision_id": "6338e872cff3",
    "outcome": "overridden"
  },
  "response_body": {
    "action": "order_as_planned",
    "alpha": 1.0,
    "bootstrap": null,
    "category_coverage": 1.0,
    "centroid_delta": 0.0,
    "centroid_updated": false,
    "cold_start": null,
    "confidence": 0.950146755550136,
    "conservation_status": "RED",
    "correct_count": 178,
    "decision_id": "6338e872cff3",
    "decisions_total": 238,
    "engine": {
      "gae": "gae.profile_scorer.ProfileScorer",
      "scoring": "copilot_sdk.scoring.CompoundingScorer"
    },
    "iks_after": 0.0,
    "iks_before": 0.0,
    "outcome": "overridden",
    "override_rate": 0.25210084033613445,
    "pause_reason": "conservation_red",
    "paused": true,
    "previous_reward": null,
    "q": 0.7478991596638656,
    "reason": "conservation_red",
    "recent_q": 0.74,
    "recent_window": 100,
    "reward": -0.05,
    "reward_multiplier": 1.0,
    "status": "paused",
    "theta_min": 0.75,
    "verified_count": 238
  },
  "status_code": 200,
  "url": "http://localhost:8020/api/learn"
}
```

conservation_after:
```json
{
  "method": "GET",
  "request_body": null,
  "response_body": {
    "V": 238,
    "alpha": 1.0,
    "baseline": 0.75,
    "baseline_q": 0.75,
    "categories_total": 5,
    "categories_with_data": 5,
    "conservation_applicable": true,
    "conservation_mode": "normal",
    "correct_count": 178,
    "domain": "purchasing",
    "engine": {
      "component": "conservation_status",
      "gae": "gae.calibration"
    },
    "evidence_label": "MODELED / PILOT-TARGET \u2014 not measured ROI",
    "g_abs": {
      "active": false,
      "alpha_q_v": 178.0,
      "theta_min": 0.0989
    },
    "g_rate": {
      "active": false,
      "long_baseline": 1.0,
      "m_rate": 0.85,
      "short_accuracy": 1.0,
      "short_window_count": 20,
      "threshold": 0.85,
      "w_short": 20
    },
    "g_rel": {
      "active": false,
      "baseline": 0.75,
      "rolling_accuracy": 0.7478991596638656,
      "threshold": 0.5249999999999999
    },
    "headroom": 177.9011,
    "passed": true,
    "penalty_ratio": 3.0,
    "projected_divergence_week": 5,
    "projected_weekly_net_benefit": 230.0,
    "projection_definition": "First full week cumulative assumed net benefit covers setup cost",
    "projection_inputs": {
      "benefit_per_decision": 2.5,
      "provenance": "SDK-PRESEED planted demo assumptions",
      "required_verified_decisions": 200,
      "setup_cost": 1000.0,
      "weekly_decisions": 100.0,
      "weekly_operating_cost": 20.0
    },
    "projection_status": "break_even_projected",
    "projection_tier": "T-sim",
    "q": 0.7478991596638656,
    "readiness_definition": "Verified coverage vs configured target; not permission to act",
    "readiness_score": 1.0,
    "reason": "Signal 178.00 exceeds theta_min 0.0989 with headroom 177.90. Accuracy 74.8% is above 70% of baseline (75.0%). Status is GREEN with \u03b1=1.00 across 238 verified decisions.",
    "relative_trigger": 0.5249999999999999,
    "relative_trigger_ratio": 0.7,
    "signal": 178.0,
    "status": "GREEN",
    "theta_min": 0.0989,
    "total_categories": 5,
    "total_decisions": 238,
    "verified_count": 238
  },
  "status_code": 200,
  "url": "http://localhost:8020/api/conservation/status"
}
```

### Decision 5 (fixture seed index 34)

conservation_before:
```json
{
  "method": "GET",
  "request_body": null,
  "response_body": {
    "V": 238,
    "alpha": 1.0,
    "baseline": 0.75,
    "baseline_q": 0.75,
    "categories_total": 5,
    "categories_with_data": 5,
    "conservation_applicable": true,
    "conservation_mode": "normal",
    "correct_count": 178,
    "domain": "purchasing",
    "engine": {
      "component": "conservation_status",
      "gae": "gae.calibration"
    },
    "evidence_label": "MODELED / PILOT-TARGET \u2014 not measured ROI",
    "g_abs": {
      "active": false,
      "alpha_q_v": 178.0,
      "theta_min": 0.0989
    },
    "g_rate": {
      "active": false,
      "long_baseline": 1.0,
      "m_rate": 0.85,
      "short_accuracy": 1.0,
      "short_window_count": 20,
      "threshold": 0.85,
      "w_short": 20
    },
    "g_rel": {
      "active": false,
      "baseline": 0.75,
      "rolling_accuracy": 0.7478991596638656,
      "threshold": 0.5249999999999999
    },
    "headroom": 177.9011,
    "passed": true,
    "penalty_ratio": 3.0,
    "projected_divergence_week": 5,
    "projected_weekly_net_benefit": 230.0,
    "projection_definition": "First full week cumulative assumed net benefit covers setup cost",
    "projection_inputs": {
      "benefit_per_decision": 2.5,
      "provenance": "SDK-PRESEED planted demo assumptions",
      "required_verified_decisions": 200,
      "setup_cost": 1000.0,
      "weekly_decisions": 100.0,
      "weekly_operating_cost": 20.0
    },
    "projection_status": "break_even_projected",
    "projection_tier": "T-sim",
    "q": 0.7478991596638656,
    "readiness_definition": "Verified coverage vs configured target; not permission to act",
    "readiness_score": 1.0,
    "reason": "Signal 178.00 exceeds theta_min 0.0989 with headroom 177.90. Accuracy 74.8% is above 70% of baseline (75.0%). Status is GREEN with \u03b1=1.00 across 238 verified decisions.",
    "relative_trigger": 0.5249999999999999,
    "relative_trigger_ratio": 0.7,
    "signal": 178.0,
    "status": "GREEN",
    "theta_min": 0.0989,
    "total_categories": 5,
    "total_decisions": 238,
    "verified_count": 238
  },
  "status_code": 200,
  "url": "http://localhost:8020/api/conservation/status"
}
```

score_response summary:
```json
{
  "action": "order_as_planned",
  "confidence": 0.9005843515018455,
  "decision_id": "94b44a8957ea",
  "score": null
}
```

score_response full:
```json
{
  "method": "POST",
  "request_body": {
    "category": "dairy",
    "context": {
      "evidence_tier": "T-sim",
      "fixture": "SDK-PRESEED",
      "planted": true,
      "provenance": "sample",
      "seed_index": 34
    },
    "factors": {
      "day_of_week": 0.88,
      "event_flag": 0.12,
      "expected_demand": 0.42,
      "historical_waste": 0.07,
      "price_memory_index": 0.5,
      "supplier_lead_time": 0.34,
      "weather_forecast": 0.2
    },
    "metadata": {
      "evidence_tier": "T-sim",
      "fixture": "SDK-PRESEED",
      "planted": true,
      "provenance": "sample",
      "seed_index": 34
    }
  },
  "response_body": {
    "action": "order_as_planned",
    "action_index": 0,
    "category": "dairy",
    "confidence": 0.9005843515018455,
    "decision_id": "94b44a8957ea",
    "engine": {
      "gae": "gae.profile_scorer.ProfileScorer",
      "scoring": "copilot_sdk.scoring.CompoundingScorer"
    },
    "factors": {
      "day_of_week": 0.88,
      "event_flag": 0.12,
      "expected_demand": 0.42,
      "historical_waste": 0.07,
      "price_memory_index": 0.5,
      "supplier_lead_time": 0.34,
      "weather_forecast": 0.2
    },
    "probabilities": [
      0.9005843515018455,
      0.010828169626805818,
      0.04446084294478049,
      0.04412663592656822
    ]
  },
  "status_code": 200,
  "url": "http://localhost:8020/api/score"
}
```

learn_response summary (including conservation fields):
```json
{
  "conservation_fields": {
    "alpha": 1.0,
    "category_coverage": 1.0,
    "conservation_status": "RED",
    "correct_count": 178,
    "override_rate": 0.25210084033613445,
    "pause_reason": "conservation_red",
    "paused": true,
    "q": 0.7478991596638656,
    "reason": "conservation_red",
    "recent_q": 0.74,
    "recent_window": 100,
    "status": "paused",
    "theta_min": 0.75,
    "verified_count": 238
  },
  "decision_id": "94b44a8957ea",
  "http_status": 200,
  "outcome": "overridden"
}
```

learn_response full:
```json
{
  "method": "POST",
  "request_body": {
    "actual_action": "order_more",
    "context": {
      "evidence_tier": "T-sim",
      "fixture": "SDK-PRESEED",
      "planted": true,
      "provenance": "sample",
      "seed_index": 34
    },
    "decision_id": "94b44a8957ea",
    "outcome": "overridden"
  },
  "response_body": {
    "action": "order_as_planned",
    "alpha": 1.0,
    "bootstrap": null,
    "category_coverage": 1.0,
    "centroid_delta": 0.0,
    "centroid_updated": false,
    "cold_start": null,
    "confidence": 0.9005843515018455,
    "conservation_status": "RED",
    "correct_count": 178,
    "decision_id": "94b44a8957ea",
    "decisions_total": 238,
    "engine": {
      "gae": "gae.profile_scorer.ProfileScorer",
      "scoring": "copilot_sdk.scoring.CompoundingScorer"
    },
    "iks_after": 0.0,
    "iks_before": 0.0,
    "outcome": "overridden",
    "override_rate": 0.25210084033613445,
    "pause_reason": "conservation_red",
    "paused": true,
    "previous_reward": null,
    "q": 0.7478991596638656,
    "reason": "conservation_red",
    "recent_q": 0.74,
    "recent_window": 100,
    "reward": -0.05,
    "reward_multiplier": 1.0,
    "status": "paused",
    "theta_min": 0.75,
    "verified_count": 238
  },
  "status_code": 200,
  "url": "http://localhost:8020/api/learn"
}
```

conservation_after:
```json
{
  "method": "GET",
  "request_body": null,
  "response_body": {
    "V": 238,
    "alpha": 1.0,
    "baseline": 0.75,
    "baseline_q": 0.75,
    "categories_total": 5,
    "categories_with_data": 5,
    "conservation_applicable": true,
    "conservation_mode": "normal",
    "correct_count": 178,
    "domain": "purchasing",
    "engine": {
      "component": "conservation_status",
      "gae": "gae.calibration"
    },
    "evidence_label": "MODELED / PILOT-TARGET \u2014 not measured ROI",
    "g_abs": {
      "active": false,
      "alpha_q_v": 178.0,
      "theta_min": 0.0989
    },
    "g_rate": {
      "active": false,
      "long_baseline": 1.0,
      "m_rate": 0.85,
      "short_accuracy": 1.0,
      "short_window_count": 20,
      "threshold": 0.85,
      "w_short": 20
    },
    "g_rel": {
      "active": false,
      "baseline": 0.75,
      "rolling_accuracy": 0.7478991596638656,
      "threshold": 0.5249999999999999
    },
    "headroom": 177.9011,
    "passed": true,
    "penalty_ratio": 3.0,
    "projected_divergence_week": 5,
    "projected_weekly_net_benefit": 230.0,
    "projection_definition": "First full week cumulative assumed net benefit covers setup cost",
    "projection_inputs": {
      "benefit_per_decision": 2.5,
      "provenance": "SDK-PRESEED planted demo assumptions",
      "required_verified_decisions": 200,
      "setup_cost": 1000.0,
      "weekly_decisions": 100.0,
      "weekly_operating_cost": 20.0
    },
    "projection_status": "break_even_projected",
    "projection_tier": "T-sim",
    "q": 0.7478991596638656,
    "readiness_definition": "Verified coverage vs configured target; not permission to act",
    "readiness_score": 1.0,
    "reason": "Signal 178.00 exceeds theta_min 0.0989 with headroom 177.90. Accuracy 74.8% is above 70% of baseline (75.0%). Status is GREEN with \u03b1=1.00 across 238 verified decisions.",
    "relative_trigger": 0.5249999999999999,
    "relative_trigger_ratio": 0.7,
    "signal": 178.0,
    "status": "GREEN",
    "theta_min": 0.0989,
    "total_categories": 5,
    "total_decisions": 238,
    "verified_count": 238
  },
  "status_code": 200,
  "url": "http://localhost:8020/api/conservation/status"
}
```

Post-degradation conservation_status:
```json
{
  "method": "GET",
  "request_body": null,
  "response_body": {
    "V": 238,
    "alpha": 1.0,
    "baseline": 0.75,
    "baseline_q": 0.75,
    "categories_total": 5,
    "categories_with_data": 5,
    "conservation_applicable": true,
    "conservation_mode": "normal",
    "correct_count": 178,
    "domain": "purchasing",
    "engine": {
      "component": "conservation_status",
      "gae": "gae.calibration"
    },
    "evidence_label": "MODELED / PILOT-TARGET \u2014 not measured ROI",
    "g_abs": {
      "active": false,
      "alpha_q_v": 178.0,
      "theta_min": 0.0989
    },
    "g_rate": {
      "active": false,
      "long_baseline": 1.0,
      "m_rate": 0.85,
      "short_accuracy": 1.0,
      "short_window_count": 20,
      "threshold": 0.85,
      "w_short": 20
    },
    "g_rel": {
      "active": false,
      "baseline": 0.75,
      "rolling_accuracy": 0.7478991596638656,
      "threshold": 0.5249999999999999
    },
    "headroom": 177.9011,
    "passed": true,
    "penalty_ratio": 3.0,
    "projected_divergence_week": 5,
    "projected_weekly_net_benefit": 230.0,
    "projection_definition": "First full week cumulative assumed net benefit covers setup cost",
    "projection_inputs": {
      "benefit_per_decision": 2.5,
      "provenance": "SDK-PRESEED planted demo assumptions",
      "required_verified_decisions": 200,
      "setup_cost": 1000.0,
      "weekly_decisions": 100.0,
      "weekly_operating_cost": 20.0
    },
    "projection_status": "break_even_projected",
    "projection_tier": "T-sim",
    "q": 0.7478991596638656,
    "readiness_definition": "Verified coverage vs configured target; not permission to act",
    "readiness_score": 1.0,
    "reason": "Signal 178.00 exceeds theta_min 0.0989 with headroom 177.90. Accuracy 74.8% is above 70% of baseline (75.0%). Status is GREEN with \u03b1=1.00 across 238 verified decisions.",
    "relative_trigger": 0.5249999999999999,
    "relative_trigger_ratio": 0.7,
    "signal": 178.0,
    "status": "GREEN",
    "theta_min": 0.0989,
    "total_categories": 5,
    "total_decisions": 238,
    "verified_count": 238
  },
  "status_code": 200,
  "url": "http://localhost:8020/api/conservation/status"
}
```

## PROBE 3: Conservation Math

```json
{
  "V": 238.0,
  "aggregate_signal_alpha_q_V": 178.0,
  "alpha": 1.0,
  "formula_note": "The aggregate endpoint compares alpha*q*V with theta_min. q alone is also shown because the per-decision recent-quality gate can compare q with a fixed threshold.",
  "q": 0.7478991596638656,
  "q_vs_theta_min": {
    "q": 0.7478991596638656,
    "relation": "at_or_above",
    "theta_min": 0.0989
  },
  "theta_min_computed": 0.0988655462184874,
  "theta_min_from_endpoint": 0.0989,
  "would_be_RED": false
}
```

## PROBE 4: Per-Decision vs Aggregate

```json
{
  "aggregate_conservation_status": "GREEN",
  "learn_response_has_conservation": true,
  "mismatch": true,
  "per_decision_conservation_fields": [
    {
      "alpha": 1.0,
      "category_coverage": 1.0,
      "conservation_status": "RED",
      "correct_count": 178,
      "override_rate": 0.25210084033613445,
      "pause_reason": "conservation_red",
      "paused": true,
      "q": 0.7478991596638656,
      "reason": "conservation_red",
      "recent_q": 0.74,
      "recent_window": 100,
      "status": "paused",
      "theta_min": 0.75,
      "verified_count": 238
    },
    {
      "alpha": 1.0,
      "category_coverage": 1.0,
      "conservation_status": "RED",
      "correct_count": 178,
      "override_rate": 0.25210084033613445,
      "pause_reason": "conservation_red",
      "paused": true,
      "q": 0.7478991596638656,
      "reason": "conservation_red",
      "recent_q": 0.74,
      "recent_window": 100,
      "status": "paused",
      "theta_min": 0.75,
      "verified_count": 238
    },
    {
      "alpha": 1.0,
      "category_coverage": 1.0,
      "conservation_status": "RED",
      "correct_count": 178,
      "override_rate": 0.25210084033613445,
      "pause_reason": "conservation_red",
      "paused": true,
      "q": 0.7478991596638656,
      "reason": "conservation_red",
      "recent_q": 0.74,
      "recent_window": 100,
      "status": "paused",
      "theta_min": 0.75,
      "verified_count": 238
    },
    {
      "alpha": 1.0,
      "category_coverage": 1.0,
      "conservation_status": "RED",
      "correct_count": 178,
      "override_rate": 0.25210084033613445,
      "pause_reason": "conservation_red",
      "paused": true,
      "q": 0.7478991596638656,
      "reason": "conservation_red",
      "recent_q": 0.74,
      "recent_window": 100,
      "status": "paused",
      "theta_min": 0.75,
      "verified_count": 238
    },
    {
      "alpha": 1.0,
      "category_coverage": 1.0,
      "conservation_status": "RED",
      "correct_count": 178,
      "override_rate": 0.25210084033613445,
      "pause_reason": "conservation_red",
      "paused": true,
      "q": 0.7478991596638656,
      "reason": "conservation_red",
      "recent_q": 0.74,
      "recent_window": 100,
      "status": "paused",
      "theta_min": 0.75,
      "verified_count": 238
    }
  ],
  "per_decision_conservation_status": [
    "RED",
    "RED",
    "RED",
    "RED",
    "RED"
  ]
}
```

## PROBE 5: seed_purchasing() Failure Condition

endpoint_checked: `POST /api/learn response["conservation_status"] (primary); GET /api/conservation/status (returned as secondary context)`

condition_expected: At least one learn response must contain the explicit top-level field conservation_status with value "RED".

actual_value: `{'per_decision_conservation_status': ['RED', 'RED', 'RED', 'RED', 'RED'], 'per_decision_red_observed': True, 'aggregate_status': 'GREEN', 'aggregate_passed': True}`

Source inspection:
```json
{
  "actual_value": {
    "aggregate_passed": true,
    "aggregate_status": "GREEN",
    "per_decision_conservation_status": [
      "RED",
      "RED",
      "RED",
      "RED",
      "RED"
    ],
    "per_decision_red_observed": true
  },
  "condition_expected": "At least one learn response must contain the explicit top-level field conservation_status with value \"RED\".",
  "endpoint_checked": "POST /api/learn response[\"conservation_status\"] (primary); GET /api/conservation/status (returned as secondary context)",
  "function_source": "def seed_purchasing() -> dict[str, Any]:\n    url = domain_url(DOMAINS[1])\n    status = api_get(url, \"/api/conservation/status\")\n    if status.get(\"status\") != \"GREEN\" and status.get(\"passed\") is not False:\n        raise RuntimeError(\"Purchasing reports non-GREEN but passed=true; restart updated backend before adding outcomes\")\n    twin = api_get(url, \"/api/purchasing/frozen-twin\")\n    if not twin.get(\"available\"):\n        if status.get(\"status\") == \"GREEN\":\n            for index in range(30):\n                score_outcome(\"purchasing\", index, index % 5 != 4)\n        try:\n            twin = api_post(url, \"/api/purchasing/frozen-twin/freeze\", {})\n        except ApiError as exc:\n            # Degradation is independently demonstrable; report the unready\n            # twin contract instead of pretending a snapshot was created.\n            twin = {\"available\": False, \"error\": str(exc)}\n            print(json.dumps({\"scenario\": \"purchasing-twin\", **twin}), flush=True)\n    learn_results = [\n        score_outcome(\"purchasing\", 30 + index, index % 2 == 0)\n        for index in range(20)\n    ]\n    conservation_results = [\n        result for result in learn_results if \"conservation_status\" in result\n    ]\n    if not conservation_results:\n        raise KeyError(\"Purchasing learn responses missing required 'conservation_status' field\")\n    if not any(result[\"conservation_status\"] == \"RED\" for result in conservation_results):\n        raise RuntimeError(f\"Purchasing per-decision conservation degradation not observed: {conservation_results}\")\n    status = api_get(url, \"/api/conservation/status\")\n    return {\"twin\": twin, \"conservation\": status}",
  "source_file": "scripts\\preseed_demo_fixtures.py",
  "uses_per_decision_evidence": true
}
```

## DIAGNOSIS

The live endpoint mismatch remains reproducible: /api/learn reports per-decision conservation RED while /api/conservation/status remains GREEN. The updated seed_purchasing() now validates the explicit top-level learn-response conservation_status field, so this trace provides the evidence the fixture expects.
