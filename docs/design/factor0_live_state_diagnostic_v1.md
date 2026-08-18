# SOC Factor-0 Live-State Diagnostic v1

**Diagnostic date:** 2026-08-16  
**Mode:** read-only; no production files or live state were modified  
**Backend:** `http://127.0.0.1:8001`  
**Scope:** live centroids, graph decision support, factor-0 distributions, and
identity-context input coverage

## Executive summary

The running SOC process exposes a 6×4×6 centroid tensor through
`GET /api/soc/profile`. Its live factor-0 column is close to the frozen
travel-calibrated sidecar, not to the proposed identity-context prior. The
largest factor-0 movement is only `+0.025000`; mean absolute movement is
`0.006430`.

The graph contains **4,886 active Decision nodes**, of which **4,862** have
`domain_source=backfill` and `origin=zero_day_synthetic`. Those 4,862 records
are the verified population used below. Every one of the 24 category×scorer
action cells has at least 107 verified observations, so no cell is sparse under
the requested `<90` criterion.

However, the empirical factor-0 values in those records are centered almost
exactly on the old prior: overall mean `0.467170`, range `[0.120, 0.830]`, and
cell means track the travel-calibrated action levels. This is not evidence that
the system has learned an identity-context distribution. The current live state
is therefore **not usable as an identity-context bootstrap**.

There is also a runtime observability inconsistency. `/api/soc/profile` exposes
the adapted current tensor and reports drift-based IKS `7.7`, while
`/api/soc/centroid-export` reports `current_mu == bootstrap_mu`, zero drift, and
IKS `94.0` with `decision_count=0`. The export endpoint should not be used as a
source of truth for migration until its bootstrap/current provenance is
reconciled.

## 1. Evidence sources and extraction method

### Live tensor

The current tensor was read from `/api/soc/profile`, whose response contains
`categories`, `actions`, `centroids`, `counts`, and `decision_count`. The
endpoint is implemented at
`gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py:2952-3009`.

### Bootstrap tensor

The comparison baseline was read from
`gen-ai-roi-demo-v4-v50/backend/app/data/iks_bootstrap_soc.json`, the sidecar
loaded by `app/services/iks.py:45-70`. Its factor-0 column is the original
travel-calibrated `[0.75, 0.60, 0.30, 0.20]` for every category.

This sidecar is preferred over the live export's `bootstrap_mu` because the
export currently returns the same values for `current_mu` and `bootstrap_mu`
while the profile endpoint exposes nonzero movement.

### Decision counts and distributions

Counts and factor vectors were queried read-only from the SOC AGE graph using
the same domain filter as `soc_decision_where()`:

```cypher
MATCH (d:Decision)
WHERE d.domain = 'soc' AND (d.archived IS NULL OR d.archived <> true)
  AND d.domain_source = 'backfill'
RETURN d.category, d.action, d.factor_vector
```

The graph query route is explicitly read-only and registry-based at
`app/routers/framework_router.py:633-648`; the direct diagnostic query used
the same graph client without writes. Factor vectors were parsed as six-element
arrays and position 0 was summarized per category/action.

### Factor computer and alert pool

`PrivilegedIdentityContextFactor` was run against `ALERT_POOL` entries and
against representative default, high-risk, and low-risk contexts. The live
implementation and component rules are at
`app/domains/soc/factors.py:64-156`. The alert pool is the 27-entry data set
loaded from `app.data.alert_pool`.

## 2. Live factor-0 centroid column

`live` is from `/api/soc/profile`; `bootstrap` is from the immutable sidecar;
`delta = live - bootstrap`. The per-cell counts are verified backfill Decision
nodes, not the `counts` field in `/api/soc/profile`, because that response
currently reports a zero matrix and `decision_count=0` despite the graph and
learning-state endpoints reporting thousands of decisions.

| Category | Action | Bootstrap μ₀ | Live μ | Delta | Verified n | Residual @ η=.05 | Residual @ η=.01 | Status |
|---|---|---:|---:|---:|---:|---:|---:|---|
| credential_access | escalate | 0.750000 | 0.746783 | -0.003217 | 350 | 1.60e-8 | 0.02967 | washed @ .05; not @ .01 |
| credential_access | investigate | 0.600000 | 0.625000 | +0.025000 | 376 | 4.21e-9 | 0.02285 | washed @ .05; not @ .01 |
| credential_access | suppress | 0.300000 | 0.305000 | +0.005000 | 379 | 3.61e-9 | 0.02217 | washed @ .05; not @ .01 |
| credential_access | monitor | 0.200000 | 0.200000 | +0.000000 | 352 | 1.44e-8 | 0.02908 | washed @ .05; not @ .01 |
| malware_execution | escalate | 0.750000 | 0.732400 | -0.017600 | 135 | 0.000983 | 0.2575 | washed @ .05; not @ .01 |
| malware_execution | investigate | 0.600000 | 0.590000 | -0.010000 | 107 | 0.004135 | 0.3412 | washed @ .05; not @ .01 |
| malware_execution | suppress | 0.300000 | 0.300000 | +0.000000 | 117 | 0.002475 | 0.3085 | washed @ .05; not @ .01 |
| malware_execution | monitor | 0.200000 | 0.197250 | -0.002750 | 116 | 0.002606 | 0.3117 | washed @ .05; not @ .01 |
| lateral_movement | escalate | 0.750000 | 0.750749 | +0.000749 | 248 | 2.99e-6 | 0.08270 | washed @ .05; not @ .01 |
| lateral_movement | investigate | 0.600000 | 0.622802 | +0.022802 | 264 | 1.32e-6 | 0.07042 | washed @ .05; not @ .01 |
| lateral_movement | suppress | 0.300000 | 0.300000 | +0.000000 | 226 | 9.24e-6 | 0.1032 | washed @ .05; not @ .01 |
| lateral_movement | monitor | 0.200000 | 0.200000 | +0.000000 | 245 | 3.49e-6 | 0.08524 | washed @ .05; not @ .01 |
| data_exfiltration | escalate | 0.750000 | 0.753750 | +0.003750 | 201 | 3.33e-5 | 0.1326 | washed @ .05; not @ .01 |
| data_exfiltration | investigate | 0.600000 | 0.625000 | +0.025000 | 178 | 0.000108 | 0.1671 | washed @ .05; not @ .01 |
| data_exfiltration | suppress | 0.300000 | 0.300000 | +0.000000 | 183 | 8.38e-5 | 0.1589 | washed @ .05; not @ .01 |
| data_exfiltration | monitor | 0.200000 | 0.200000 | +0.000000 | 175 | 0.000126 | 0.1722 | washed @ .05; not @ .01 |
| insider_threat | escalate | 0.750000 | 0.765000 | +0.015000 | 191 | 5.56e-5 | 0.1467 | washed @ .05; not @ .01 |
| insider_threat | investigate | 0.600000 | 0.585149 | -0.014851 | 176 | 0.000120 | 0.1705 | washed @ .05; not @ .01 |
| insider_threat | suppress | 0.300000 | 0.300000 | +0.000000 | 171 | 0.000155 | 0.1793 | washed @ .05; not @ .01 |
| insider_threat | monitor | 0.200000 | 0.200000 | +0.000000 | 188 | 6.49e-5 | 0.1512 | washed @ .05; not @ .01 |
| cloud_infrastructure | escalate | 0.750000 | 0.750750 | +0.000750 | 128 | 0.001408 | 0.2763 | washed @ .05; not @ .01 |
| cloud_infrastructure | investigate | 0.600000 | 0.607850 | +0.007850 | 115 | 0.002743 | 0.3148 | washed @ .05; not @ .01 |
| cloud_infrastructure | suppress | 0.300000 | 0.300000 | +0.000000 | 118 | 0.002352 | 0.3055 | washed @ .05; not @ .01 |
| cloud_infrastructure | monitor | 0.200000 | 0.200000 | +0.000000 | 123 | 0.001820 | 0.2905 | washed @ .05; not @ .01 |

### Aggregate centroid findings

- Live factor-0 range: **[0.197250, 0.765000]**.
- Bootstrap factor-0 range: **[0.200000, 0.750000]**.
- Mean absolute factor-0 delta: **0.006430**.
- Maximum absolute delta: **0.025000**, in credential-access/investigate and
  data-exfiltration/investigate.
- No verified scorer cell has fewer than 90 observations.
- Under the requested nominal η=.05 formula, all 24 cells have residual prior
  influence below 1%.
- Under nominal η=.01, **zero** cells are below 1%; the highest residual is
  approximately 34.1% in malware-execution/investigate.

The residual calculation is only a mathematical washout estimate. The live
history exposes effective alpha values of 0.02 in the local checkpoint, and
updates can be frozen, weighted, overridden, or otherwise guarded. Therefore
the table does not prove that any cell is semantically identity-calibrated.

## 3. Per-cell empirical factor-0 distributions

The following uses the 4,862 `domain_source=backfill` records. All 4,862 have
valid six-element factor vectors. In this data set, `outcome IS NOT NULL` is
4,863 because one non-backfill record also has an outcome; the table deliberately
uses the 4,862 verified/backfill records consistent with the running learning
state’s reported verified count.

| Category | Action | n | Mean | SD | Min | Median | Max |
|---|---|---:|---:|---:|---:|---:|---:|
| credential_access | escalate | 350 | 0.753 | 0.046 | 0.671 | 0.753 | 0.830 |
| credential_access | investigate | 376 | 0.601 | 0.047 | 0.521 | 0.602 | 0.679 |
| credential_access | suppress | 379 | 0.303 | 0.046 | 0.221 | 0.303 | 0.380 |
| credential_access | monitor | 352 | 0.202 | 0.046 | 0.121 | 0.202 | 0.280 |
| malware_execution | escalate | 135 | 0.754 | 0.047 | 0.673 | 0.762 | 0.828 |
| malware_execution | investigate | 107 | 0.604 | 0.043 | 0.522 | 0.607 | 0.677 |
| malware_execution | suppress | 117 | 0.299 | 0.045 | 0.221 | 0.295 | 0.379 |
| malware_execution | monitor | 116 | 0.203 | 0.048 | 0.120 | 0.203 | 0.278 |
| lateral_movement | escalate | 248 | 0.750 | 0.049 | 0.670 | 0.750 | 0.830 |
| lateral_movement | investigate | 264 | 0.594 | 0.045 | 0.520 | 0.591 | 0.680 |
| lateral_movement | suppress | 226 | 0.302 | 0.046 | 0.220 | 0.302 | 0.380 |
| lateral_movement | monitor | 245 | 0.201 | 0.045 | 0.121 | 0.207 | 0.280 |
| data_exfiltration | escalate | 201 | 0.753 | 0.044 | 0.670 | 0.752 | 0.830 |
| data_exfiltration | investigate | 178 | 0.596 | 0.047 | 0.520 | 0.593 | 0.680 |
| data_exfiltration | suppress | 183 | 0.299 | 0.044 | 0.222 | 0.294 | 0.379 |
| data_exfiltration | monitor | 175 | 0.198 | 0.049 | 0.122 | 0.198 | 0.279 |
| insider_threat | escalate | 191 | 0.753 | 0.047 | 0.670 | 0.754 | 0.830 |
| insider_threat | investigate | 176 | 0.604 | 0.045 | 0.520 | 0.604 | 0.679 |
| insider_threat | suppress | 171 | 0.293 | 0.043 | 0.221 | 0.289 | 0.380 |
| insider_threat | monitor | 188 | 0.200 | 0.046 | 0.121 | 0.203 | 0.280 |
| cloud_infrastructure | escalate | 128 | 0.754 | 0.050 | 0.671 | 0.752 | 0.828 |
| cloud_infrastructure | investigate | 115 | 0.608 | 0.044 | 0.520 | 0.610 | 0.679 |
| cloud_infrastructure | suppress | 118 | 0.303 | 0.046 | 0.220 | 0.303 | 0.376 |
| cloud_infrastructure | monitor | 123 | 0.197 | 0.045 | 0.121 | 0.198 | 0.279 |

The striking pattern is semantic: action means are approximately
`escalate=.75`, `investigate=.60`, `suppress=.30`, and `monitor=.20` in every
category. That is the legacy prior pattern, not a measured identity-risk
distribution. The graph metadata confirms that all 4,862 records are synthetic
backfill (`domain_source=backfill`, `origin=zero_day_synthetic`).

## 4. Factor-computer output range

The live factor implementation averages available components and defaults to
0.5 when no usable context exists (`factors.py:128-156`). Representative
results:

| Context | Result |
|---|---:|
| No context | 0.5000 |
| High risk: user risk .8, admin, MFA absent, unknown device | 0.8375 |
| Low risk: user risk .2, ordinary analyst, MFA present, known device | 0.1500 |
| Neutral title/risk .5, MFA present, unknown device | 0.4000 |

The computed range for these representative contexts is **[0.1500, 0.8375]**.
This is materially broader and has different causal meaning than the graph
backfill distribution’s observed `[0.120, 0.830]` values; range overlap alone
does not establish semantic equivalence.

## 5. Alert-pool identity-context coverage

The 27-entry `ALERT_POOL` contains:

| Field | Present | Coverage |
|---|---:|---:|
| `user_risk_score` | 0/27 | 0% |
| `user_title` | 0/27 | 0% |
| `mfa_completed` | 27/27 | 100% |
| `device_fingerprint_match` | 27/27 | 100% |
| `security_context` | 0/27 | 0% |

Running the real factor computer over the pool produced:

| Factor-0 result | Count |
|---:|---:|
| 0.100 | 10 |
| 0.450 | 4 |
| 0.475 | 4 |
| 0.825 | 9 |

Pool mean is **0.449074**, sample SD **0.309659**, range **[0.100, 0.825]**.
Because title and user-risk fields are absent, these results are driven only by
inverted MFA and device trust. They are suitable for exercising the factor
computer, not for identity-provider calibration.

## 6. State-source inconsistencies and limitations

### 6.1 Learning-state JSON is not the centroid tensor

`app/data/gae_learning_state.json` contains `W` with shape 4×6, factor names,
decision count 4,863, and update history. The loader documents this as W/history
serialization (`app/services/gae_state.py:136-143` and
`app/framework/learning_state.py:59-79`). It is not a source for the 6×4×6
profile centroids.

### 6.2 Local centroid backups are not current live state

The backup directory contains valid 6×4×6 artifacts, but the latest file is a
test-shaped snapshot at decision count 50, not a snapshot at the live graph
count. It must not be substituted for `/api/soc/profile` without a timestamp and
state-identity check. Backup serialization itself is implemented at
`app/services/gae_state.py:587-639`.

### 6.3 `/api/soc/profile` and `/api/soc/centroid-export` disagree

Observed responses:

| Endpoint | Current tensor | Bootstrap | Decision count | IKS |
|---|---|---|---:|---:|
| `/api/soc/profile` | adapted values above | not returned | 0 in response | 7.7 |
| `/api/soc/centroid-export` | adapted values above | identical to current | 0 | 94.0 |
| `/api/soc/learning-state` | not returned | not returned | 4,863 / 4,862 verified | 94.0 v2 |
| `/api/soc/graph-stats` | not returned | not returned | 4,886 historical | n/a |

The export route is built around `build_centroid_export()` at
`app/routers/soc.py:3981-4075`; startup writes bootstrap state at
`app/main.py:337-341`. The export’s zero drift must therefore be treated as an
observability/provenance defect until the DeploymentState bootstrap artifact is
shown to be immutable and distinct from current state. The profile endpoint’s
drift calculation against the sidecar is the more useful measured comparison for
this diagnostic, but its zero decision count is also a response-layer defect.

## 7. Assessment for migration

### Are the live centroids usable as the new identity-context bootstrap?

**No.** The tensor is a valid live scorer snapshot, but it is not an approved
identity-context bootstrap for four reasons:

1. The current values remain very close to the travel-calibrated sidecar.
2. The 4,862 supporting records are synthetic backfill, not customer identity
   telemetry.
3. Their factor-0 means reproduce the old action-conditioned pattern across all
   categories.
4. Current data coverage contains MFA/device fields in the demo pool but no
   user-risk, title, or security-context fields.

The live tensor can be retained as a **versioned operational snapshot** for
replay and audit. It must not be relabeled as identity-calibrated or promoted to
`mu_zero_v2`.

### What is usable now?

- The factor computer’s implementation and its high/low/default behavior are
  measurable.
- The graph supplies complete category/action coverage for the synthetic
  backfill population.
- The live centroid API supplies a current 6×4×6 tensor.
- The existing sidecar supplies a stable comparison baseline.

### What is missing before atomic migration?

1. A provenance-correct current/live/bootstrap export with immutable anchor
   identity and consistent decision count.
2. Per-cell learning counts from the actual scorer state, not a zero-filled API
   response or graph action counts assumed to equal update counts.
3. Identity-native records with user-risk, title, MFA, and device evidence, or a
   documented missing-field policy for each signal.
4. An identity-context evaluation suite with analyst-approved labels and
   semantic versioning.
5. Replay evidence for confidence, referral thresholds, action margins, and IKS
   continuity.
6. A decision on how the 4,862 synthetic backfill records participate in a
   migration: exclude, retain as legacy, or explicitly reclassify with evidence.
7. A versioned migration/rollback plan that does not overwrite the v1 IKS
   anchor or silently rescoring historical decisions.

## 8. Recommended next diagnostic/implementation gate

Before any centroid or anchor change, repair observability in an isolated,
versioned change and verify it against the current state:

1. Make `/api/soc/centroid-export` return a truly immutable bootstrap artifact,
   current tensor, state version, and authoritative decision count.
2. Expose per-cell scorer update counts and distinguish scorer updates from
   graph Decision counts.
3. Add semantic provenance to every factor vector and learned centroid state.
4. Re-run this extraction on identity-native pilot data, not synthetic backfill.
5. Only then evaluate a candidate identity bootstrap through the full migration
   checklist: action selection, confidence/routing, IKS anchor/version,
   learned-state continuity, APIs, PW, and rollback.

## Final status

| Data | Available? | Source | Quality |
|---|---|---|---|
| Live centroids | Yes | `/api/soc/profile` | Current tensor, but response count is inconsistent |
| Per-cell decision counts | Yes | AGE graph, 4,862 verified backfill records | Decision counts, not proven scorer-update counts |
| Factor-0 distribution | Yes | AGE `factor_vector`, plus live factor on alert pool | Synthetic/backfill distribution; not identity-native |
| Alert-pool context | Partial | `ALERT_POOL` | MFA/device complete; title/risk/security context absent |

**Assessment:** The live snapshot is operationally usable for replay and
diagnosis, but not as an identity-context bootstrap. The dominant blocker is not
cell sparsity; it is semantic provenance and the absence of identity-native
telemetry, compounded by inconsistent live export metadata.
