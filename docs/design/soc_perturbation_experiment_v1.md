# SOC Perturbation Experiment v1
**Date:** 2026-08-04  
**soc_graph modified:** NO (read-only target selection; experiment ran in disposable AGE sandbox)

## Prerequisite

The static platform scan confirms that SOC has active entity-context factors.
In particular, AssetCriticalityFactor issues typed Cypher over
Alert-[:DETECTED_ON]->Asset-[:STORES]->DataClass and reads
Asset.criticality at
gen-ai-roi-demo-v4-v50/backend/app/domains/soc/factors.py:259-283.
The requested scan specification file
copilot-sdk/docs/design/s2p_fix_b_platform_factor_scan_v2.md was absent, but
the static report and source evidence satisfy the prerequisite.

## Step 0: Target Identification

| Item | Result |
|---|---|
| Analyze endpoint | POST /api/alert/analyze |
| Handler | gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py:480-585 |
| Request body | {"alert_id":"C9B-SOC-0209","deployment_version":"v3.1","simulate_failure":false} |
| Target alert | C9B-SOC-0209 |
| Linked User | C9B-SOC-USER-0209, via INVOLVES |
| Linked User risk_score | 0.75, read-only from soc_graph |
| Linked Asset | C9B-SOC-ASSET-0209, via DETECTED_ON |
| Source Asset criticality | 0.8, read-only from soc_graph |
| Property perturbed | Asset.criticality |
| Sandbox | whatif_soc_perturb |
| Sandbox original value | 0.8 |
| Sandbox perturbed value | "critical" |

The target was selected with read-only AGE queries. The source graph returned:
C9B-SOC-0209 -> DETECTED_ON -> C9B-SOC-ASSET-0209 with criticality 0.8,
and C9B-SOC-0209 -> INVOLVES -> C9B-SOC-USER-0209 with risk_score 0.75.

The factor implementation used for the perturbation is:

    MATCH (a:Alert {alert_id: <alert_id>})-[:DETECTED_ON]->(asset:Asset)
    OPTIONAL MATCH (asset)-[:STORES]->(dc:DataClass)
    RETURN asset.criticality AS criticality,
           dc.sensitivity AS sensitivity
    LIMIT 1

This is the query at factors.py:264-271. It maps low=.2, medium=.5,
high=.8, critical=1.0 at factors.py:243-257 and returns the mapped value
with an optional sensitivity boost at :275-283.

## Step 1: Baseline Score

The SOC backend was started on port 8098 with a temporary GraphConfig pointing
to the disposable sandbox. The production port 8001 and production soc_graph
were not used for writes.

| Field | Value |
|---|---|
| HTTP status | 200 |
| Latency | 3615.6 ms |
| Action | refer_to_analyst |
| Confidence | 0.5320197397 |
| Factor vector order | privileged_identity_context, asset_criticality, threat_intel_enrichment, pattern_history, time_anomaly, device_trust |
| Factor vector | [0.475, 0.5, 0.0, 0.4, 0.7, 0.3333333333] |

The baseline response provenance identified asset_criticality as a graph
traversal and returned 0.5. The sandbox retained the source numeric value
0.8; the current factor map treats unknown/non-string criticality as medium
fallback .5. This is a schema/value-shape observation, not a fallback-to-
fixture result.

## Step 2: Perturbation

Only the sandbox Asset property was changed:

    Asset.criticality: 0.8 -> "critical"

The AGE SET completed successfully and a follow-up read returned
"critical". No property in soc_graph was changed.

## Step 3: Perturbed Score

The same request and same Analyze endpoint were used.

| Field | Value |
|---|---|
| HTTP status | 200 |
| Latency | 1511.5 ms |
| Action | investigate |
| Confidence | 0.8515164776 |
| Factor vector | [0.475, 1.0, 0.0, 0.4, 0.7, 0.3333333333] |

The response provenance again identified the factor as a graph traversal and
described the critical asset. The only changed factor input was Asset
criticality.

## Step 4: Revert

The sandbox property was restored from "critical" to numeric 0.8. A
post-revert AGE read returned 0.8.

| Check | Result |
|---|---|
| Sandbox property restored | YES |
| Restored value equals original | YES, 0.8 |
| Production soc_graph changed | NO |

## Step 5: Decisive Check

| Factor | Baseline | Perturbed | Changed? |
|---|---:|---:|---|
| privileged_identity_context | 0.475 | 0.475 | NO |
| asset_criticality | 0.5 | 1.0 | **YES** |
| threat_intel_enrichment | 0.0 | 0.0 | NO |
| pattern_history | 0.4 | 0.4 | NO |
| time_anomaly | 0.7 | 0.7 | NO |
| device_trust | 0.3333333333 | 0.3333333333 | NO |

**Perturbed factor moved: YES.**

## VERDICT

**SOC genuinely graph-backed: YES.**

The decisive evidence is that changing only the disposable graph’s
Asset.criticality property moved asset_criticality from 0.5 to 1.0 and
changed the endpoint recommendation from refer_to_analyst at 0.5320 to
investigate at 0.8515. Unrelated factor values remained unchanged.

This rules out the specific S2P-style fixture coincidence for the active SOC
Analyze route. It does not validate every SOC route: the legacy
compute_soc_factors() compatibility path remains template-backed according to
the static scan.

## Implications for S2P FIX-B

SOC is confirmed as a working reference for S2P Path A at the architectural
pattern level:

1. Resolve a domain entity with bespoke, typed Cypher.
2. Read concrete graph properties in the factor implementation.
3. Preserve factor provenance in the scoring response.
4. Verify graph backing with a property perturbation, not merely a matching
   factor vector.

S2P still requires its own Track-2 normalization fix and Track-1 faithful
property contract. SOC’s result does not repair S2P’s two topology-only
factors or its generic path-row rejection.

The experiment also surfaced a SOC data-contract issue: the source Asset
stored numeric criticality 0.8, while AssetCriticalityFactor’s canonical map
expects categorical strings. The graph-backed path is real, but the migration
or seed contract should standardize this property shape to avoid a semantic
fallback to .5.

## Cleanup

| Item | Result |
|---|---|
| Sandbox property reverted | YES |
| Sandbox graph dropped | YES |
| Remaining whatif_soc_* graphs | NONE |
| Spare backend stopped | YES |
| Temporary config deleted | YES |
| Scratch/log files deleted | YES |
| Production source/test files modified | NO |
| Production soc_graph written | NO |

## Reading and Evidence Log

- Read platform_factor_architecture_scan_v1.md fully.
- Attempted to read s2p_fix_b_platform_factor_scan_v2.md; absent.
- Read s2p_fix_b_whatif_phase_b_results_v1.md fully.
- Read copilot-sdk/CLAUDE.md fully.
- Read SOC Analyze handler, ProcessAlertRequest, SOC factor implementation,
  SOC orchestrator, GraphConfig, and AGE client methods.
- Target selection used read-only queries against soc_graph.
- All graph CREATE/SET/DROP operations were confined to whatif_soc_perturb.

