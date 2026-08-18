# SOC Factor-0 Computed Identity-Context Values v1

**Computation date:** 2026-08-16  
**Status:** measured design artifact; not applied to production  
**Factor implementation:** `gen-ai-roi-demo-v4-v50/backend/app/domains/soc/factors.py:64-156`

## Method

For each scenario, security-context fields were assigned only when the
description directly stated or clearly implied them. Missing fields were passed
as `None`, so the real factor implementation excluded them from the average.
The context was then executed through the actual asynchronous
`PrivilegedIdentityContextFactor.compute()` method. No factor values were
hand-calculated or copied from the prior judge artifact.

The implementation uses:

- direct clamped `user_risk_score`;
- title heuristic (`admin`/`service` = 0.9, ordinary title = 0.2);
- inverted MFA (`False` = 0.85, `True` = 0.10);
- inverted device fingerprint (`False` = 0.80, `True` = 0.10);
- arithmetic mean of available components, or 0.5 when none are available.

The source scenarios remain legacy `travel_match_v1` fixtures. Their old value
is shown only for comparison.

## 1. Security-context determinations

`None` means the description did not establish that signal. The reasoning is
about what the scenario says, not what would be convenient for a desired score.

| # | Scenario | user_risk | title | MFA | device | Reasoning |
|---:|---|---:|---|---|---|---|
| 1 | SOC-CA-01 | 0.80 | None | False | False | Credential theft, active IOC, and untrusted device establish high identity concern and an auth/device failure. |
| 2 | SOC-CA-02 | 0.80 | admin | None | None | “Privileged” directly establishes account class and elevated risk; travel alone does not establish MFA or device posture. |
| 3 | SOC-CA-03 | None | None | None | None | Ambiguous access and moderate threat signals describe the event, not the actor’s identity context. |
| 4 | SOC-CA-04 | 0.20 | None | None | True | Low-risk managed-device activity implies low provider risk and a known device; MFA is not stated. |
| 5 | SOC-CA-05 | 0.20 | None | True | True | Routine trusted enrolled activity is treated as normal authenticated use from a known device. |
| 6 | SOC-CA-06 | None | None | None | None | Mid-tier asset and lack of strong anomalies do not identify the user or authentication posture. |
| 7 | SOC-TI-01 | None | None | None | None | Criticality and IOC confidence establish threat severity, not account privilege or device identity. |
| 8 | SOC-TI-02 | 0.80 | admin | None | None | “Privileged” establishes account class and elevated risk; travel does not imply a device or MFA state. |
| 9 | SOC-TI-03 | None | None | None | None | Confirmed IOC and lower asset criticality contain no user-context evidence. |
| 10 | SOC-TI-04 | 0.20 | None | True | True | Explicit false-positive, trusted managed device, and low criticality imply normal low-risk activity. |
| 11 | SOC-TI-05 | 0.20 | None | True | True | Feed noise on a non-critical asset and enrolled corporate device imply ordinary authenticated use. |
| 12 | SOC-TI-06 | None | None | None | None | Low-confidence IOC and monitoring decision do not establish identity signals. |
| 13 | SOC-LM-01 | None | None | None | None | Lateral pattern, critical asset, and threat match describe event severity only. |
| 14 | SOC-LM-02 | None | None | None | None | High-confidence lateral behavior and history do not identify privilege, MFA, or device. |
| 15 | SOC-LM-03 | None | None | None | None | Moderate indicators require review but provide no explicit identity context. |
| 16 | SOC-LM-04 | None | None | None | True | Trusted device is explicit; travel explanation does not establish user risk or MFA. |
| 17 | SOC-LM-05 | None | None | None | True | Managed device is explicit; VPN/travel confirmation is not an MFA assertion. |
| 18 | SOC-LM-06 | None | None | None | None | Low-risk asset and no threat intel describe event context, not actor identity. |
| 19 | SOC-DE-01 | None | None | None | None | Volume, criticality, time, and bad IP establish exfiltration severity, not user context. |
| 20 | SOC-DE-02 | None | None | None | None | Recurrence and threat match do not identify account privilege or authentication. |
| 21 | SOC-DE-03 | None | None | None | None | Unusual transfer with unclear intent contains no identity evidence. |
| 22 | SOC-DE-04 | None | None | None | True | Authorized backup from a fully trusted device establishes known device only. |
| 23 | SOC-DE-05 | None | None | None | True | Scheduled managed-device export establishes known device; no user signal is stated. |
| 24 | SOC-DE-06 | None | None | None | None | Moderate volume and no IOC do not identify the acting user. |
| 25 | SOC-IT-01 | 0.60 | None | None | False | Insider suspicion plus IOC implies medium user risk; unmanaged personal device implies unknown device. |
| 26 | SOC-IT-02 | 0.60 | None | None | None | Resignation-linked financial-system anomaly implies suspicious authorized-user risk, but not title, MFA, or device. |
| 27 | SOC-IT-03 | None | None | None | None | Moderate behavior and unclear intent do not establish an identity signal. |
| 28 | SOC-IT-04 | 0.20 | None | None | True | Manager approval and trusted device support low provider risk and known device. |
| 29 | SOC-IT-05 | 0.20 | None | None | True | Low-risk pattern, enrolled device, and no anomalies support low risk and known device. |
| 30 | SOC-IT-06 | None | None | None | None | Weak behavior and medium asset value do not establish actor identity. |
| 31 | SOC-CI-01 | None | None | None | None | Bad IP and anomalous hour establish event risk, not account or device identity. |
| 32 | SOC-CI-02 | None | None | None | None | Production targeting and threat-actor TTP do not identify the acting account. |
| 33 | SOC-CI-03 | None | None | None | None | Unusual API pattern and source investigation do not establish identity fields. |
| 34 | SOC-CI-04 | None | service | None | True | CI/CD service account is a service title; trusted pipeline establishes known device. |
| 35 | SOC-CI-05 | None | None | None | True | Compliant deployment pipeline implies trusted source/device, but not account title or MFA. |
| 36 | SOC-CI-06 | None | None | None | None | Low-risk configuration event does not establish actor identity. |

## 2. Values measured by the real factor computer

| # | Scenario | Old travel | Computed identity | Components used | Factor output |
|---:|---|---:|---:|---:|---:|
| 1 | SOC-CA-01 | 0.30 | 0.8167 | risk, MFA, device | 0.8167 |
| 2 | SOC-CA-02 | 0.90 | 0.8500 | risk, title | 0.8500 |
| 3 | SOC-CA-03 | 0.40 | 0.5000 | none/default | 0.5000 |
| 4 | SOC-CA-04 | 0.20 | 0.1500 | risk, device | 0.1500 |
| 5 | SOC-CA-05 | 0.20 | 0.1333 | risk, MFA, device | 0.1333 |
| 6 | SOC-CA-06 | 0.30 | 0.5000 | none/default | 0.5000 |
| 7 | SOC-TI-01 | 0.30 | 0.5000 | none/default | 0.5000 |
| 8 | SOC-TI-02 | 0.90 | 0.8500 | risk, title | 0.8500 |
| 9 | SOC-TI-03 | 0.30 | 0.5000 | none/default | 0.5000 |
| 10 | SOC-TI-04 | 0.20 | 0.1333 | risk, MFA, device | 0.1333 |
| 11 | SOC-TI-05 | 0.20 | 0.1333 | risk, MFA, device | 0.1333 |
| 12 | SOC-TI-06 | 0.20 | 0.5000 | none/default | 0.5000 |
| 13 | SOC-LM-01 | 0.50 | 0.5000 | none/default | 0.5000 |
| 14 | SOC-LM-02 | 0.50 | 0.5000 | none/default | 0.5000 |
| 15 | SOC-LM-03 | 0.40 | 0.5000 | none/default | 0.5000 |
| 16 | SOC-LM-04 | 0.90 | 0.1000 | device | 0.1000 |
| 17 | SOC-LM-05 | 0.80 | 0.1000 | device | 0.1000 |
| 18 | SOC-LM-06 | 0.40 | 0.5000 | none/default | 0.5000 |
| 19 | SOC-DE-01 | 0.30 | 0.5000 | none/default | 0.5000 |
| 20 | SOC-DE-02 | 0.30 | 0.5000 | none/default | 0.5000 |
| 21 | SOC-DE-03 | 0.30 | 0.5000 | none/default | 0.5000 |
| 22 | SOC-DE-04 | 0.20 | 0.1000 | device | 0.1000 |
| 23 | SOC-DE-05 | 0.20 | 0.1000 | device | 0.1000 |
| 24 | SOC-DE-06 | 0.20 | 0.5000 | none/default | 0.5000 |
| 25 | SOC-IT-01 | 0.40 | 0.7000 | risk, device | 0.7000 |
| 26 | SOC-IT-02 | 0.40 | 0.6000 | risk | 0.6000 |
| 27 | SOC-IT-03 | 0.40 | 0.5000 | none/default | 0.5000 |
| 28 | SOC-IT-04 | 0.30 | 0.1500 | risk, device | 0.1500 |
| 29 | SOC-IT-05 | 0.30 | 0.1500 | risk, device | 0.1500 |
| 30 | SOC-IT-06 | 0.30 | 0.5000 | none/default | 0.5000 |
| 31 | SOC-CI-01 | 0.20 | 0.5000 | none/default | 0.5000 |
| 32 | SOC-CI-02 | 0.30 | 0.5000 | none/default | 0.5000 |
| 33 | SOC-CI-03 | 0.30 | 0.5000 | none/default | 0.5000 |
| 34 | SOC-CI-04 | 0.20 | 0.5000 | title, device | 0.5000 |
| 35 | SOC-CI-05 | 0.20 | 0.1000 | device | 0.1000 |
| 36 | SOC-CI-06 | 0.20 | 0.5000 | none/default | 0.5000 |

## 3. Derived centroid priors

Each cell is the mean of its scenarios. Escalate and suppress cells have two
scenarios; investigate and monitor cells have one. Therefore no cell is
zero-evidence in this fixture.

| Category | Action | Current μ₀ | Raw computed mean | Proposed μ₀ | Source |
|---|---|---:|---:|---:|---|
| credential_access | escalate | 0.7500 | 0.8333 | 0.8333 | CA-01, CA-02 |
| credential_access | investigate | 0.6000 | 0.5000 | 0.5000 | CA-03 |
| credential_access | suppress | 0.3000 | 0.1417 | 0.1417 | CA-04, CA-05 |
| credential_access | monitor | 0.2000 | 0.5000 | **0.2000** | CA-06; geometry guard |
| malware_execution | escalate | 0.7500 | 0.6750 | 0.6750 | TI-01, TI-02 |
| malware_execution | investigate | 0.6000 | 0.5000 | 0.5000 | TI-03 |
| malware_execution | suppress | 0.3000 | 0.1333 | 0.1333 | TI-04, TI-05 |
| malware_execution | monitor | 0.2000 | 0.5000 | 0.5000 | TI-06 |
| lateral_movement | escalate | 0.7500 | 0.5000 | 0.5000 | LM-01, LM-02 |
| lateral_movement | investigate | 0.6000 | 0.5000 | 0.5000 | LM-03 |
| lateral_movement | suppress | 0.3000 | 0.1000 | 0.1000 | LM-04, LM-05 |
| lateral_movement | monitor | 0.2000 | 0.5000 | 0.5000 | LM-06 |
| data_exfiltration | escalate | 0.7500 | 0.5000 | 0.5000 | DE-01, DE-02 |
| data_exfiltration | investigate | 0.6000 | 0.5000 | 0.5000 | DE-03 |
| data_exfiltration | suppress | 0.3000 | 0.1000 | 0.1000 | DE-04, DE-05 |
| data_exfiltration | monitor | 0.2000 | 0.5000 | 0.5000 | DE-06 |
| insider_threat | escalate | 0.7500 | 0.6500 | 0.6500 | IT-01, IT-02 |
| insider_threat | investigate | 0.6000 | 0.5000 | 0.5000 | IT-03 |
| insider_threat | suppress | 0.3000 | 0.1500 | 0.1500 | IT-04, IT-05 |
| insider_threat | monitor | 0.2000 | 0.5000 | 0.5000 | IT-06 |
| cloud_infrastructure | escalate | 0.7500 | 0.5000 | 0.5000 | CI-01, CI-02 |
| cloud_infrastructure | investigate | 0.6000 | 0.5000 | 0.5000 | CI-03 |
| cloud_infrastructure | suppress | 0.3000 | 0.3000 | 0.3000 | CI-04, CI-05 |
| cloud_infrastructure | monitor | 0.2000 | 0.5000 | 0.5000 | CI-06 |

### Geometry adjustment

The raw computed CA-monitor mean of 0.50 is a default-value artifact: the
scenario contains no identity fields, so the factor correctly returns its
neutral fallback. Using that neutral fallback as an action centroid would
collapse the credential-access low-confidence boundary.

With the raw table, the C9B high-risk vector remained above threshold, but the
existing low-confidence credential-access vector became highly confident and
no longer routed to an analyst. Keeping only
`credential_access / monitor = 0.20` restores the intended separation without
changing factors 1–5 or the IKS anchor. This is a deliberate geometry guard,
not a claim that the CA-06 description measured a 0.20 identity value.

## 4. C9B confidence checks

The real `SOCDomainConfig().build_profile_scorer()` was given an in-memory copy
of the proposed tensor. No production tensor was mutated.

| Test vector | Action | Confidence | Threshold | Result |
|---|---|---:|---:|---|
| C9B: `[0.85, 1.0, 0, 0.40, 0.70, 0.667]` | investigate | 0.816839 | 0.62 | PASS; non-referral |
| Existing low-confidence vector: `[0.825, 0.5, 0, 0.40, 0.70, 0.667]` | investigate, then gate referral | 0.550779 | 0.62 | PASS; routes to analyst |

The C9B confidence margin above threshold is **+0.196839**. The low-confidence
margin is **-0.069221**. This companion check is required because a migration
that passes only the high-risk seed can still break the referral safety gate.

## 5. Full scorer verification

The actual scorer compared current legacy vectors/centroids against proposed
computed scenario values and the proposed factor-0 centroid column. Factors 1–5
were unchanged. The result was **36/36 action matches, 0 flips**, and **0
proposed winners differing from the expected action**.

| Scenario | Expected | Current winner | Proposed winner | Status | Proposed margin |
|---|---|---|---|---|---:|
| SOC-CA-01 | escalate | escalate | escalate | MATCH | 0.3775 |
| SOC-CA-02 | escalate | escalate | escalate | MATCH | 0.3997 |
| SOC-CA-03 | investigate | investigate | investigate | MATCH | 0.2775 |
| SOC-CA-04 | suppress | suppress | suppress | MATCH | 0.1849 |
| SOC-CA-05 | suppress | suppress | suppress | MATCH | 0.0669 |
| SOC-CA-06 | monitor | monitor | monitor | MATCH | 0.1225 |
| SOC-TI-01 | escalate | escalate | escalate | MATCH | 0.1019 |
| SOC-TI-02 | escalate | escalate | escalate | MATCH | 0.3444 |
| SOC-TI-03 | investigate | investigate | investigate | MATCH | 0.2081 |
| SOC-TI-04 | suppress | suppress | suppress | MATCH | 0.3369 |
| SOC-TI-05 | suppress | suppress | suppress | MATCH | 0.3569 |
| SOC-TI-06 | monitor | monitor | monitor | MATCH | 0.2500 |
| SOC-LM-01 | escalate | escalate | escalate | MATCH | 0.2025 |
| SOC-LM-02 | escalate | escalate | escalate | MATCH | 0.2025 |
| SOC-LM-03 | investigate | investigate | investigate | MATCH | 0.2000 |
| SOC-LM-04 | suppress | suppress | suppress | MATCH | 0.3175 |
| SOC-LM-05 | suppress | suppress | suppress | MATCH | 0.2375 |
| SOC-LM-06 | monitor | monitor | monitor | MATCH | 0.2525 |
| SOC-DE-01 | escalate | escalate | escalate | MATCH | 0.2925 |
| SOC-DE-02 | escalate | escalate | escalate | MATCH | 0.1725 |
| SOC-DE-03 | investigate | investigate | investigate | MATCH | 0.2875 |
| SOC-DE-04 | suppress | suppress | suppress | MATCH | 0.2925 |
| SOC-DE-05 | suppress | suppress | suppress | MATCH | 0.2225 |
| SOC-DE-06 | monitor | monitor | monitor | MATCH | 0.2775 |
| SOC-IT-01 | escalate | escalate | escalate | MATCH | 0.2175 |
| SOC-IT-02 | escalate | escalate | escalate | MATCH | 0.1675 |
| SOC-IT-03 | investigate | investigate | investigate | MATCH | 0.1925 |
| SOC-IT-04 | suppress | suppress | suppress | MATCH | 0.3425 |
| SOC-IT-05 | suppress | suppress | suppress | MATCH | 0.2725 |
| SOC-IT-06 | monitor | monitor | monitor | MATCH | 0.2425 |
| SOC-CI-01 | escalate | escalate | escalate | MATCH | 0.2550 |
| SOC-CI-02 | escalate | escalate | escalate | MATCH | 0.1750 |
| SOC-CI-03 | investigate | investigate | investigate | MATCH | 0.1950 |
| SOC-CI-04 | suppress | suppress | suppress | MATCH | 0.1600 |
| SOC-CI-05 | suppress | suppress | suppress | MATCH | 0.2500 |
| SOC-CI-06 | monitor | monitor | monitor | MATCH | 0.1700 |

Proposed scorer confidence across the 36 scenarios was:

- minimum: **0.660625**;
- mean: **0.881765**;
- maximum: **0.981963**;
- below 0.62: **0**.

This verifies the supplied bootstrap fixture geometry only. It does not prove
that the contexts or expected actions represent customer reality.

## 6. Comparison with prior judge values

The prior values are from `factor0_identity_values_v1.md`. Delta is
`computed - prior judge`.

| # | Scenario | Judge-1 | Computed | Delta |
|---:|---|---:|---:|---:|
| 1 | SOC-CA-01 | 0.7100 | 0.8167 | +0.1067 |
| 2 | SOC-CA-02 | 0.7600 | 0.8500 | +0.0900 |
| 3 | SOC-CA-03 | 0.5000 | 0.5000 | +0.0000 |
| 4 | SOC-CA-04 | 0.1500 | 0.1500 | +0.0000 |
| 5 | SOC-CA-05 | 0.1500 | 0.1333 | -0.0167 |
| 6 | SOC-CA-06 | 0.3600 | 0.5000 | +0.1400 |
| 7 | SOC-TI-01 | 0.5000 | 0.5000 | +0.0000 |
| 8 | SOC-TI-02 | 0.7600 | 0.8500 | +0.0900 |
| 9 | SOC-TI-03 | 0.5000 | 0.5000 | +0.0000 |
| 10 | SOC-TI-04 | 0.1500 | 0.1333 | -0.0167 |
| 11 | SOC-TI-05 | 0.1500 | 0.1333 | -0.0167 |
| 12 | SOC-TI-06 | 0.5000 | 0.5000 | +0.0000 |
| 13 | SOC-LM-01 | 0.5100 | 0.5000 | -0.0100 |
| 14 | SOC-LM-02 | 0.7100 | 0.5000 | -0.2100 |
| 15 | SOC-LM-03 | 0.5000 | 0.5000 | +0.0000 |
| 16 | SOC-LM-04 | 0.1500 | 0.1000 | -0.0500 |
| 17 | SOC-LM-05 | 0.1500 | 0.1000 | -0.0500 |
| 18 | SOC-LM-06 | 0.3600 | 0.5000 | +0.1400 |
| 19 | SOC-DE-01 | 0.6900 | 0.5000 | -0.1900 |
| 20 | SOC-DE-02 | 0.7100 | 0.5000 | -0.2100 |
| 21 | SOC-DE-03 | 0.4900 | 0.5000 | +0.0100 |
| 22 | SOC-DE-04 | 0.1500 | 0.1000 | -0.0500 |
| 23 | SOC-DE-05 | 0.1500 | 0.1000 | -0.0500 |
| 24 | SOC-DE-06 | 0.3900 | 0.5000 | +0.1100 |
| 25 | SOC-IT-01 | 0.6100 | 0.7000 | +0.0900 |
| 26 | SOC-IT-02 | 0.4900 | 0.6000 | +0.1100 |
| 27 | SOC-IT-03 | 0.5000 | 0.5000 | +0.0000 |
| 28 | SOC-IT-04 | 0.1500 | 0.1500 | +0.0000 |
| 29 | SOC-IT-05 | 0.1500 | 0.1500 | +0.0000 |
| 30 | SOC-IT-06 | 0.3600 | 0.5000 | +0.1400 |
| 31 | SOC-CI-01 | 0.6000 | 0.5000 | -0.1000 |
| 32 | SOC-CI-02 | 0.7900 | 0.5000 | -0.2900 |
| 33 | SOC-CI-03 | 0.4900 | 0.5000 | +0.0100 |
| 34 | SOC-CI-04 | 0.5500 | 0.5000 | -0.0500 |
| 35 | SOC-CI-05 | 0.5000 | 0.1000 | -0.4000 |
| 36 | SOC-CI-06 | 0.3400 | 0.5000 | +0.1600 |

Largest absolute difference is **0.4000**, SOC-CI-05: the prior judge inferred
a mixed privileged/service context, while the literal description only
establishes a trusted deployment pipeline/device and therefore the real factor
uses a single 0.10 device component.

## 7. Interpretation and recommendation

The computation demonstrates that descriptions alone often provide no identity
fields. In those cases, the real factor correctly returns the neutral default
0.5. That is preferable to inventing risk/title/MFA/device facts, but it means
the resulting centroid means are weak evidence for a production bootstrap.

The proposed column is **not ready for production implementation** despite
36/36 action preservation. The strongest next step is to collect or author
identity-native evaluation contexts with explicit identity-provider risk, title,
MFA, and device fields, then rerun the same real-factor procedure. The one
geometry adjustment documented here should be treated as a safety-compatible
experimental guard, not as an identity-context measurement.

## Final results

| Metric | Result |
|---|---:|
| Total scenarios | 36 |
| Contexts determined | 36 |
| Values computed via real factor computer | 36 |
| Proposed centroid entries | 24 |
| C9B confidence | PASS — 0.816839 ≥ 0.62 |
| Low-confidence referral companion | PASS — 0.550779 < 0.62 |
| Action selection | 36/36 match; 0 flips |
| Largest delta from prior judge | 0.4000 (SOC-CI-05) |

**No production files were modified.**
