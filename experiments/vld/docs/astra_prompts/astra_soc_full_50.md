# Generate 50 SOC Multi-Hop Investigation Scenarios

## What you're building

You are generating synthetic test data for an AI copilot that helps SOC (Security Operations Center) analysts triage security alerts. Each scenario is a multi-step investigation where the correct action can ONLY be determined by following graph-based evidence — surface-level features alone point to the WRONG action.

## Output

One JSON file with this structure:

```json
{
  "_header": "PLANTED SYNTHETIC — POSITIVE CONTROL — NOT A MEASUREMENT OF VLD VALUE ON REAL DECISIONS.",
  "_spec": "multihop_scenario_spec_v2.md",
  "_stage": "Stage 1: 50 SOC instances (30 strong + 10 moderate + 10 controls)",
  "provenance": "sample",
  "scenarios": [ <50 scenario objects> ]
}
```

## The SOC Domain

**What the copilot does:** A SOC analyst receives security alerts (credential access, lateral movement, data exfiltration, insider threats, cloud misconfigurations, malware detections). The copilot scores each alert and recommends an action. Some alerts LOOK benign on the surface but are actually serious — the investigation checks identity context, timing patterns, threat intel, and campaign history.

**Categories (6):** credential_access, lateral_movement, data_exfiltration, insider_threat, cloud_misconfiguration, malware

**Actions (4):** escalate, investigate, monitor, suppress

**Factors (6 numeric values, each 0.0 to 1.0):**
- privileged_identity_context — is this a privileged/admin account? (1.0 = highly privileged)
- asset_criticality — how critical is the affected asset? (1.0 = crown jewel)
- threat_intel_enrichment — does threat intel match known campaigns? (1.0 = strong match)
- time_anomaly — is the timing unusual? (1.0 = very anomalous, e.g., 3am Saturday)
- pattern_history — has this pattern been seen before? (1.0 = very familiar pattern)
- device_trust — is the source device trusted? (1.0 = fully trusted/managed)

## Scenario JSON Schema

Each scenario MUST have ALL of these fields:

```json
{
  "scenario_id": "SOC-001-v1",
  "scenario_type": "privilege_chain",
  "copilot": "soc",
  "branching_kind": "score_keyed",
  "rho_planted": 0.90,
  "description": "Alert looks like routine admin login but identity check reveals compromised service account",

  "alert": {
    "alert_id": "ALERT-SOC-001",
    "category": "credential_access",
    "surface_factors": {
      "privileged_identity_context": 0.30,
      "asset_criticality": 0.25,
      "threat_intel_enrichment": 0.15,
      "time_anomaly": 0.20,
      "pattern_history": 0.85,
      "device_trust": 0.80
    }
  },

  "available_branches": [
    {
      "branch_id": "check_identity_chain",
      "evidence_source": "identity_graph",
      "read_cost": 1,
      "factor_enriched": "privileged_identity_context",
      "factor_new_value": 0.95,
      "evidence_found": "Service account SVC-BACKUP linked to domain admin via delegation chain",
      "narration": "What looked like a routine service account is actually a domain admin equivalent"
    },
    {
      "branch_id": "check_timing_context",
      "evidence_source": "behavioral_analytics",
      "read_cost": 1,
      "factor_enriched": "time_anomaly",
      "factor_new_value": 0.90,
      "evidence_found": "This account has never authenticated on weekends — current time is Saturday 3:17am",
      "narration": "Behavioral baseline shows this is highly anomalous timing"
    },
    {
      "branch_id": "check_pattern_db",
      "evidence_source": "pattern_database",
      "read_cost": 1,
      "factor_enriched": "pattern_history",
      "factor_new_value": 0.80,
      "evidence_found": "Similar login pattern seen 47 times from this account",
      "narration": "Pattern looks familiar on the surface — misleading"
    }
  ],

  "correct_branches": ["check_identity_chain", "check_timing_context"],
  "misleading_branches": ["check_pattern_db"],
  "read_costs": {"check_identity_chain": 1, "check_timing_context": 1, "check_pattern_db": 1},
  "budget": 2,
  "surface_only_resolvable": false,

  "decision_tree": {
    "ground_truth_action": "escalate",
    "reasoning": "Surface shows low privilege (0.30), low criticality (0.25), familiar pattern (0.85), trusted device (0.80) — suggests suppress or monitor. But identity chain reveals domain admin delegation (0.95) and timing is highly anomalous (0.90). This is a compromised service account accessing production at 3am — must escalate immediately.",
    "hops": [
      {
        "step": 1,
        "branch_id": "check_identity_chain",
        "evidence_source": "identity_graph",
        "evidence_found": "Service account SVC-BACKUP linked to domain admin via delegation chain",
        "factor_enriched": "privileged_identity_context",
        "factor_new_value": 0.95,
        "narration": "What looked like a routine service account is actually a domain admin equivalent"
      },
      {
        "step": 2,
        "branch_id": "check_timing_context",
        "evidence_source": "behavioral_analytics",
        "evidence_found": "This account has never authenticated on weekends — current time is Saturday 3:17am",
        "factor_enriched": "time_anomaly",
        "factor_new_value": 0.90,
        "narration": "Behavioral baseline shows this is highly anomalous timing"
      }
    ]
  },

  "alternative_branches": [],
  "graph_nodes": [
    {"id": "svc_backup", "type": "Identity", "label": "SVC-BACKUP service account"},
    {"id": "admin_delegation", "type": "DelegationChain", "label": "Domain Admin delegation"},
    {"id": "prod_server", "type": "Asset", "label": "PROD-DB-01"}
  ],
  "graph_edges": [
    {"source": "svc_backup", "target": "admin_delegation", "type": "DELEGATED_TO"},
    {"source": "svc_backup", "target": "prod_server", "type": "ACCESSED"}
  ]
}
```

## THE CRITICAL DESIGN RULE: Boundary Crossing

1. Set surface factors so they are closest to the WRONG action's centroid.
2. Set hop evidence so that at least 2 factors shift by >= 0.30 each.
3. Each hop MUST enrich a DIFFERENT factor.
4. ground_truth_action must be DIFFERENT from what surface factors suggest.

## Action Profiles

| Action | priv_identity | asset_crit | threat_intel | time_anomaly | pattern_hist | device_trust |
|---|---|---|---|---|---|---|
| escalate | 0.7-1.0 | 0.7-1.0 | 0.6-1.0 | 0.6-1.0 | 0.1-0.4 | 0.1-0.4 |
| investigate | 0.4-0.7 | 0.4-0.7 | 0.3-0.6 | 0.3-0.6 | 0.3-0.6 | 0.3-0.6 |
| monitor | 0.2-0.5 | 0.2-0.5 | 0.1-0.4 | 0.1-0.3 | 0.6-0.9 | 0.6-0.9 |
| suppress | 0.0-0.3 | 0.0-0.3 | 0.0-0.2 | 0.0-0.2 | 0.8-1.0 | 0.8-1.0 |

## Instance Distribution (50 total)

### Block A: 30 Strong-Conditional (rho >= 0.70)

6 templates x 5 variations. Every hop shifts >= 0.30.

rho: 0.70=10, 0.90=12, 1.00=8

**Template 1: Hidden privilege chain** (SOC-001 to SOC-005)
Surface: suppress (low privilege, familiar pattern). Evidence: delegation chain reveals admin equivalent. GT: escalate.
Shifts: privileged_identity_context LOW->HIGH (>=0.50), time_anomaly LOW->HIGH (>=0.40).

**Template 2: Benign device, malicious campaign** (SOC-006 to SOC-010)
Surface: monitor (trusted device, familiar pattern). Evidence: threat intel matches active APT campaign. GT: escalate.
Shifts: threat_intel_enrichment LOW->HIGH (>=0.50), device_trust HIGH->LOW (>=0.40).

**Template 3: Normal hours, wrong geography** (SOC-011 to SOC-015)
Surface: suppress (normal business hours, low anomaly). Evidence: login from impossible geography for this user. GT: escalate or investigate.
Shifts: time_anomaly LOW->HIGH (>=0.50), pattern_history HIGH->LOW (>=0.30).

**Template 4: Low criticality asset, data staging** (SOC-016 to SOC-020)
Surface: monitor (low asset criticality). Evidence: asset is being used to stage data exfiltration. GT: escalate.
Shifts: asset_criticality LOW->HIGH (>=0.50), threat_intel_enrichment LOW->HIGH (>=0.30).

**Template 5: Familiar malware, new variant** (SOC-021 to SOC-025)
Surface: suppress (pattern matches known benign tool). Evidence: variant is weaponized version. GT: investigate or escalate.
Shifts: pattern_history HIGH->LOW (>=0.40), threat_intel_enrichment LOW->HIGH (>=0.40).

**Template 6: Trusted insider, policy violation** (SOC-026 to SOC-030)
Surface: suppress (trusted device, known user). Evidence: accessing resources outside their role. GT: investigate.
Shifts: device_trust HIGH->LOW (>=0.30), privileged_identity_context LOW->HIGH (>=0.30).

### Block B: 10 Moderate (rho = 0.30 and 0.50)

2 templates x 5 variations. Shifts >= 0.15.

**Template 7: Ambiguous login pattern** (SOC-031 to SOC-035) rho=0.30
**Template 8: Borderline alert severity** (SOC-036 to SOC-040) rho=0.50

### Block C: 5 Flat Controls (SOC-FLAT-001 to SOC-FLAT-005)

surface_only_resolvable=true, hops=[], budget=0, rho=1.00.

### Block D: 5 rho=0.50 Checks (SOC-RHO50-001 to SOC-RHO50-005)

rho=0.50, has hops. VLD should equal chance (1/4=0.250).

## Graph Entities

**Node types:** Identity, Asset, Campaign, ThreatIntel, DelegationChain, GeoLocation, BehavioralBaseline, MalwareVariant, DataStaging, PolicyRule

**Edge types:** DELEGATED_TO, ACCESSED, MATCHES_CAMPAIGN, ORIGINATES_FROM, BASELINE_FOR, VARIANT_OF, STAGES_TO, VIOLATES

## Checklist

- [ ] scenario_id starts with "SOC-"
- [ ] copilot = "soc"
- [ ] branching_kind = "score_keyed"
- [ ] surface_factors has 6 keys: privileged_identity_context, asset_criticality, threat_intel_enrichment, time_anomaly, pattern_history, device_trust
- [ ] All factor values 0.0-1.0
- [ ] ground_truth_action: escalate, investigate, monitor, suppress
- [ ] Block A: GT differs from surface, each hop shifts >= 0.30
- [ ] Each hop enriches a DIFFERENT factor
- [ ] Block C: surface_only_resolvable=true, hops=[]
- [ ] Block D: rho=0.50, has hops
- [ ] provenance = "sample"
- [ ] No duplicate IDs
- [ ] All 4 actions appear at least 3 times
