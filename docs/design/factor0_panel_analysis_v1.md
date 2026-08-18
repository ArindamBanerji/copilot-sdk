# SOC Factor-0 Multi-Model Panel Analysis v1

**Status:** analysis/design artifact; no production files modified.

## 1. Executive summary

Six files parsed: **216/216 determinations**. Arm A is aggregated for candidate values; Arm B is mapped through the registered opaque-token map for disposition recovery. All factor values are computed by the formula implemented in this script, with null fields excluded and all-null rows defaulting to 0.5.

The raw credential-access/monitor mean is **0.1875**; geometry guard=False. The final candidate uses 0.1875. The candidate scores **36/36** expected actions. C9B=0.718243; companion=0.542470.

Static candidate drift from the immutable anchor implies IKS 90.3; current static bootstrap/anchor IKS is 0.0. This does not overwrite or recompute live learned-state IKS (operationally reported around 93-94).

## 2. Panel metadata and data quality

| File | Declared model | Arm | Date |
|---|---|---|---|
| gemini_arm_a.txt | Claude 3.7 Sonnet | A | 2026-08-17 |
| gemini_arm_b.txt | Claude 3.7 Sonnet | B | 2026-08-17 |
| gpt_arm_a.txt | GPT-5.6 Sol | A | 2026-08-17 |
| gpt_arm_b.txt | GPT-5.6 Sol | B | 2026-08-17 |
| opus_arm_a.txt | claude-opus-5 | A | 2026-08-17 |
| opus_arm_b.txt | claude-opus-5 | B | 2026-08-17 |

Each file contains 36 determinations; the six-file corpus contains 3 model prefixes x 2 arms. Data-quality note: the `gemini_*` filenames declare `Claude 3.7 Sonnet`; this report preserves both the filename provenance label and the declared model string rather than silently reconciling them.

## 3. Verification checks C1-C10

### C1 - Presence profile
| Arm/group | Risk | Title | MFA | Device |
|---|---|---|---|---|
| ('A', 'category/cloud_infrastructure') | 1.00 | 0.94 | 0.39 | 0.56 |
| ('A', 'category/credential_access') | 1.00 | 1.00 | 1.00 | 1.00 |
| ('A', 'category/data_exfiltration') | 1.00 | 1.00 | 0.72 | 0.83 |
| ('A', 'category/insider_threat') | 1.00 | 1.00 | 1.00 | 1.00 |
| ('A', 'category/lateral_movement') | 0.94 | 0.94 | 0.67 | 0.67 |
| ('A', 'category/malware_execution') | 1.00 | 1.00 | 0.83 | 1.00 |
| ('A', 'disposition/escalate') | 1.00 | 1.00 | 0.86 | 0.86 |
| ('A', 'disposition/investigate') | 1.00 | 0.94 | 0.72 | 0.83 |
| ('A', 'disposition/monitor') | 0.94 | 0.94 | 0.83 | 0.89 |
| ('A', 'disposition/suppress') | 1.00 | 1.00 | 0.67 | 0.81 |
| ('B', 'category/cloud_infrastructure') | 0.72 | 0.56 | 0.22 | 0.39 |
| ('B', 'category/credential_access') | 0.94 | 0.94 | 0.94 | 0.78 |
| ('B', 'category/data_exfiltration') | 0.50 | 0.39 | 0.28 | 0.44 |
| ('B', 'category/insider_threat') | 1.00 | 1.00 | 1.00 | 0.89 |
| ('B', 'category/lateral_movement') | 0.56 | 0.56 | 0.50 | 0.56 |
| ('B', 'category/malware_execution') | 0.56 | 0.56 | 0.50 | 0.50 |
| ('B', 'disposition/escalate') | 0.64 | 0.61 | 0.61 | 0.58 |
| ('B', 'disposition/investigate') | 0.55 | 0.50 | 0.45 | 0.35 |
| ('B', 'disposition/monitor') | 0.64 | 0.64 | 0.64 | 0.57 |
| ('B', 'disposition/suppress') | 0.89 | 0.82 | 0.58 | 0.74 |

### C2 - Arm-A ordering
| Category | escalate | investigate | suppress | monitor |
|---|---|---|---|---|
| credential_access | 0.690 | 0.402 | 0.138 | 0.187 |
| malware_execution | 0.290 | 0.187 | 0.142 | 0.177 |
| lateral_movement | 0.733 | 0.245 | 0.145 | 0.417 |
| data_exfiltration | 0.417 | 0.209 | 0.402 | 0.173 |
| insider_threat | 0.404 | 0.222 | 0.139 | 0.184 |
| cloud_infrastructure | 0.749 | 0.540 | 0.456 | 0.273 |

Inversions where escalate <= suppress: 0 (none).

### C3 - Information versus ignorance

Escalate rows below the all-absent default 0.5: **19** panel rows.
| Model | Scenario | f0 | Reasoning |
|---|---|---|---|
| gemini | SOC-TI-01 | 0.338 | Critical server malware execution occurs within a clean, MFA-verified admin session on a recognized internal device. |
| gemini | SOC-TI-02 | 0.312 | Executive traveler infected by malware on their known corporate laptop during legitimate, MFA-authenticated travel. |
| gemini | SOC-DE-02 | 0.475 | Recurring exfiltration pattern leveraging valid user access to transfer sensitive files to an unrecognised destination. |
| gemini | SOC-IT-01 | 0.488 | Malicious insider accessing sensitive systems after hours from an unmanaged personal device using valid credentials and MFA. |
| gemini | SOC-IT-02 | 0.325 | High IdP/HR risk score triggered by resignation notice while accessing sensitive financial systems from a known corporate laptop. |
| gpt | SOC-CA-02 | 0.380 | The actor is explicitly privileged, but a frequent traveler can realistically have a normal-risk identity, valid MFA, and a previously bound travel laptop even while an IOC makes the credential event severe. |
| gpt | SOC-TI-01 | 0.155 | A high-confidence malware IOC on a critical asset can originate from a compromised but otherwise clean employee session with valid MFA and a known endpoint because the alert's primary vector is malicious code rather than identity. |
| gpt | SOC-TI-02 | 0.348 | The explicitly privileged frequent traveler can still have a clean IdP profile, valid MFA, and a familiar travel device while the critical malware IOC independently justifies the severe alert. |
| gpt | SOC-LM-02 | 0.363 | High-confidence lateral movement can occur through a legitimate administrator session whose identity signals remain relatively normal, because behavioral traversal evidence need not coincide with an IdP-risk or authentication anomaly. |
| gpt | SOC-DE-01 | 0.207 | Severe exfiltration can originate from a compromised but successfully authenticated data-access user on a familiar endpoint, while the time, volume, repository criticality, and bad destination carry the alert severity outside this identity factor. |
| gpt | SOC-DE-02 | 0.255 | Recurring suspicious data movement can plausibly raise an account's IdP risk over time while still occurring through normal MFA and an established analyst workstation. |
| gpt | SOC-IT-01 | 0.455 | Repeated after-hours behavior with an IOC plausibly corresponds to an elevated-risk employee account that still completed MFA but is operating from a personal fingerprint not previously bound to the identity. |
| gpt | SOC-IT-02 | 0.245 | A departing employee with financial-system access can be moderately elevated in identity risk while still using legitimate MFA and the same corporate device historically associated with the account. |
| opus | SOC-TI-01 | 0.175 | Malware landing on a critical asset says nothing about the account's standing — the realistic actor is a phished employee on their own laptop with a normal MFA-verified session, so the identity profile is clean despite the escalation. |
| opus | SOC-TI-02 | 0.413 | Privilege raises the baseline risk, but a frequent traveler's own laptop stays fingerprint-bound and their sessions still complete MFA, so the critical IOC sits on an otherwise unremarkable identity. |
| opus | SOC-DE-01 | 0.250 | Exfiltration typically runs from an already-compromised endpoint using the victim's live session, so the fingerprint matches and MFA was satisfied hours earlier — the severity is carried by destination and volume, not by identity. |
| opus | SOC-DE-02 | 0.450 | A recurring pattern gives the IdP time to flag the account, and an account with broad data access repeatedly transferring from a fingerprint that never becomes bound is the realistic shape here. |
| opus | SOC-IT-01 | 0.475 | The defining feature of an insider is that authentication succeeds legitimately — MFA passes because it is really them — while the personal device is a fingerprint the account has not been bound to; the binding field restates 'unmanaged personal device'. |
| opus | SOC-IT-02 | 0.438 | A flagged resignation drives the risk score hard, but every other identity signal is pristine — a senior employee on their own corporate laptop passing MFA — which is the whole difficulty of the departing-insider case. |

### C4 - Service-account floor

Cloud suppress mean=0.4564, range=[0.3667, 0.5050]. Non-cloud suppress mean=0.1931, range=[0.1250, 0.5250]. Difference=+0.2632.

### C5 - Factor-0 x factor-5 collinearity

Pearson r=-0.5264; Spearman rho=-0.4703. `device_field_reused_description_adjective` true/present: 0/108 (0.0%).

### C6 - Arm-A to Arm-B delta

Null-to-non-null fills: 114/432 = **26.4%**. Mean absolute risk delta where both arms provided risk=0.0452.
| Field | Exact same / 108 |
|---|---|
| user_risk_score | 36/108 |
| user_title | 69/108 |
| mfa_completed | 85/108 |
| device_fingerprint_match | 78/108 |

### C7 - Negative controls
| Model | Token | Non-null/4 | Confidence fields | Absent rate |
|---|---|---|---|---|
| gemini | B-10 | 4 | user_risk_score=HIGH, user_title=MEDIUM, mfa_completed=HIGH, device_fingerprint_match=HIGH | 0.00 |
| gemini | B-21 | 4 | user_risk_score=HIGH, user_title=MEDIUM, mfa_completed=HIGH, device_fingerprint_match=HIGH | 0.00 |
| gpt | B-10 | 3 | user_risk_score=MEDIUM, user_title=LOW, mfa_completed=LOW, device_fingerprint_match=LOW | 0.25 |
| gpt | B-21 | 4 | user_risk_score=MEDIUM, user_title=MEDIUM, mfa_completed=MEDIUM, device_fingerprint_match=LOW | 0.00 |
| opus | B-10 | 4 | user_risk_score=MEDIUM, user_title=LOW, mfa_completed=MEDIUM, device_fingerprint_match=MEDIUM | 0.00 |
| opus | B-21 | 4 | user_risk_score=MEDIUM, user_title=LOW, mfa_completed=MEDIUM, device_fingerprint_match=MEDIUM | 0.00 |

Arm-B mean absent rate=0.363.

### C8 - Disposition recovery

Accuracy=104/108 = **96.3%**; prevalence caveat: 12 escalate, 6 investigate, 12 suppress, 6 monitor.
| Category | Correct | Total | Accuracy |
|---|---|---|---|
| credential_access | 17 | 18 | 94.4% |
| malware_execution | 18 | 18 | 100.0% |
| lateral_movement | 18 | 18 | 100.0% |
| data_exfiltration | 17 | 18 | 94.4% |
| insider_threat | 18 | 18 | 100.0% |
| cloud_infrastructure | 16 | 18 | 88.9% |
| True / predicted | escalate | investigate | suppress | monitor |
|---|---|---|---|---|
| escalate | 36 | 0 | 0 | 0 |
| investigate | 0 | 18 | 0 | 0 |
| suppress | 0 | 0 | 36 | 0 |
| monitor | 0 | 2 | 2 | 14 |

### C9 - Cell coverage
| Category | Action | n | Raw mean | IQR | IDs |
|---|---|---|---|---|---|
| credential_access | escalate | 2 | 0.649 | 0.199 | SOC-CA-01, SOC-CA-02 |
| credential_access | investigate | 1 | 0.400 | 0.000 | SOC-CA-03 |
| credential_access | suppress | 2 | 0.140 | 0.005 | SOC-CA-04, SOC-CA-05 |
| credential_access | monitor | 1 | 0.188 | 0.000 | SOC-CA-06 |
| malware_execution | escalate | 2 | 0.263 | 0.100 | SOC-TI-01, SOC-TI-02 |
| malware_execution | investigate | 1 | 0.177 | 0.000 | SOC-TI-03 |
| malware_execution | suppress | 2 | 0.142 | 0.005 | SOC-TI-04, SOC-TI-05 |
| malware_execution | monitor | 1 | 0.168 | 0.000 | SOC-TI-06 |
| lateral_movement | escalate | 2 | 0.812 | 0.012 | SOC-LM-01, SOC-LM-02 |
| lateral_movement | investigate | 1 | 0.212 | 0.000 | SOC-LM-03 |
| lateral_movement | suppress | 2 | 0.150 | 0.000 | SOC-LM-04, SOC-LM-05 |
| lateral_movement | monitor | 1 | 0.155 | 0.000 | SOC-LM-06 |
| data_exfiltration | escalate | 2 | 0.358 | 0.092 | SOC-DE-01, SOC-DE-02 |
| data_exfiltration | investigate | 1 | 0.212 | 0.000 | SOC-DE-03 |
| data_exfiltration | suppress | 2 | 0.337 | 0.037 | SOC-DE-04, SOC-DE-05 |
| data_exfiltration | monitor | 1 | 0.175 | 0.000 | SOC-DE-06 |
| insider_threat | escalate | 2 | 0.413 | 0.062 | SOC-IT-01, SOC-IT-02 |
| insider_threat | investigate | 1 | 0.225 | 0.000 | SOC-IT-03 |
| insider_threat | suppress | 2 | 0.141 | 0.006 | SOC-IT-04, SOC-IT-05 |
| insider_threat | monitor | 1 | 0.188 | 0.000 | SOC-IT-06 |
| cloud_infrastructure | escalate | 2 | 0.825 | 0.012 | SOC-CI-01, SOC-CI-02 |
| cloud_infrastructure | investigate | 1 | 0.483 | 0.000 | SOC-CI-03 |
| cloud_infrastructure | suppress | 2 | 0.367 | 0.000 | SOC-CI-04, SOC-CI-05 |
| cloud_infrastructure | monitor | 1 | 0.333 | 0.000 | SOC-CI-06 |

Single-value cells: **12/24** (credential_access/investigate, credential_access/monitor, malware_execution/investigate, malware_execution/monitor, lateral_movement/investigate, lateral_movement/monitor, data_exfiltration/investigate, data_exfiltration/monitor, insider_threat/investigate, insider_threat/monitor, cloud_infrastructure/investigate, cloud_infrastructure/monitor).

### C10 - Evidence basis audit
| Basis | Count | Share |
|---|---|---|
| category_prior | 28 | 25.9% |
| description | 70 | 64.8% |
| disposition_prior | 10 | 9.3% |

Disposition-prior share=9.3%.

## 4. Pre-registered predictions P1-P5
| Prediction | Result | Interpretation |
|---|---|---|
| P1 variance/weight | YES; Arm-A f0 SD=0.228 | Inter-model variance is nonzero versus a fixed current prior, but the direction/magnitude of a kernel-weight change still requires within-class variance calibration. |
| P2 escalate below 0.5 | 19 | Observed; clean identity does not imply low alert severity. |
| P3 service floor | 0.456 vs 0.193 | Measured, but confounded by authored service-account fields. |
| P4 f0 x f5 | Pearson -0.526; Spearman -0.470 | Descriptive collinearity; shared wording is a possible confounder. |
| P5 A-to-B null fill | 26.4% | Disposition knowledge fills a measurable fraction of fields. |

## 5. Aggregated Arm-A values
| Scenario | Category/action | Risk median | Risk IQR | Title | MFA | Device | Computed f0 |
|---|---|---|---|---|---|---|---|
| SOC-CA-01 | credential_access/escalate | 0.840 | 0.025 | admin | False | False | 0.847 |
| SOC-CA-02 | credential_access/escalate | 0.700 | 0.165 | admin | True | True | 0.450 |
| SOC-CA-03 | credential_access/investigate | 0.500 | 0.010 | user | True | False | 0.400 |
| SOC-CA-04 | credential_access/suppress | 0.180 | 0.025 | user | True | True | 0.145 |
| SOC-CA-05 | credential_access/suppress | 0.140 | 0.025 | user | True | True | 0.135 |
| SOC-CA-06 | credential_access/monitor | 0.350 | 0.005 | user | True | True | 0.188 |
| SOC-TI-01 | malware_execution/escalate | 0.250 | 0.040 | user | True | True | 0.163 |
| SOC-TI-02 | malware_execution/escalate | 0.350 | 0.130 | admin | True | True | 0.363 |
| SOC-TI-03 | malware_execution/investigate | 0.310 | 0.100 | user | True | True | 0.177 |
| SOC-TI-04 | malware_execution/suppress | 0.150 | 0.005 | user | True | True | 0.137 |
| SOC-TI-05 | malware_execution/suppress | 0.190 | 0.050 | user | True | True | 0.147 |
| SOC-TI-06 | malware_execution/monitor | 0.270 | 0.025 | user | True | True | 0.168 |
| SOC-LM-01 | lateral_movement/escalate | 0.750 | 0.150 | admin | False | False | 0.825 |
| SOC-LM-02 | lateral_movement/escalate | 0.700 | 0.225 | admin | None | None | 0.800 |
| SOC-LM-03 | lateral_movement/investigate | 0.450 | 0.030 | user | True | True | 0.212 |
| SOC-LM-04 | lateral_movement/suppress | 0.200 | 0.025 | user | True | True | 0.150 |
| SOC-LM-05 | lateral_movement/suppress | 0.200 | 0.060 | user | True | True | 0.150 |
| SOC-LM-06 | lateral_movement/monitor | 0.265 | 0.015 | None | True | True | 0.155 |
| SOC-DE-01 | data_exfiltration/escalate | 0.600 | 0.235 | None | True | True | 0.267 |
| SOC-DE-02 | data_exfiltration/escalate | 0.700 | 0.090 | analyst | True | False | 0.450 |
| SOC-DE-03 | data_exfiltration/investigate | 0.450 | 0.070 | analyst | True | True | 0.212 |
| SOC-DE-04 | data_exfiltration/suppress | 0.120 | 0.025 | service | None | True | 0.373 |
| SOC-DE-05 | data_exfiltration/suppress | 0.100 | 0.025 | service | True | True | 0.300 |
| SOC-DE-06 | data_exfiltration/monitor | 0.300 | 0.015 | user | True | True | 0.175 |
| SOC-IT-01 | insider_threat/escalate | 0.800 | 0.065 | user | True | False | 0.475 |
| SOC-IT-02 | insider_threat/escalate | 0.850 | 0.160 | None | True | True | 0.350 |
| SOC-IT-03 | insider_threat/investigate | 0.500 | 0.020 | user | True | True | 0.225 |
| SOC-IT-04 | insider_threat/suppress | 0.190 | 0.025 | user | True | True | 0.147 |
| SOC-IT-05 | insider_threat/suppress | 0.140 | 0.025 | user | True | True | 0.135 |
| SOC-IT-06 | insider_threat/monitor | 0.350 | 0.020 | user | True | True | 0.188 |
| SOC-CI-01 | cloud_infrastructure/escalate | 0.800 | 0.170 | admin | False | False | 0.838 |
| SOC-CI-02 | cloud_infrastructure/escalate | 0.700 | 0.260 | service | False | False | 0.812 |
| SOC-CI-03 | cloud_infrastructure/investigate | 0.450 | 0.030 | service | None | True | 0.483 |
| SOC-CI-04 | cloud_infrastructure/suppress | 0.100 | 0.005 | service | None | True | 0.367 |
| SOC-CI-05 | cloud_infrastructure/suppress | 0.100 | 0.000 | service | None | True | 0.367 |
| SOC-CI-06 | cloud_infrastructure/monitor | 0.230 | 0.025 | admin | True | True | 0.333 |

## 6. Derived centroid priors
| Category | Action | n | Raw mean | Final candidate | Source IDs |
|---|---|---|---|---|---|
| credential_access | escalate | 2 | 0.649 | 0.649 | SOC-CA-01, SOC-CA-02 |
| credential_access | investigate | 1 | 0.400 | 0.400 | SOC-CA-03 |
| credential_access | suppress | 2 | 0.140 | 0.140 | SOC-CA-04, SOC-CA-05 |
| credential_access | monitor | 1 | 0.188 | 0.188 | SOC-CA-06 |
| malware_execution | escalate | 2 | 0.263 | 0.263 | SOC-TI-01, SOC-TI-02 |
| malware_execution | investigate | 1 | 0.177 | 0.177 | SOC-TI-03 |
| malware_execution | suppress | 2 | 0.142 | 0.142 | SOC-TI-04, SOC-TI-05 |
| malware_execution | monitor | 1 | 0.168 | 0.168 | SOC-TI-06 |
| lateral_movement | escalate | 2 | 0.812 | 0.812 | SOC-LM-01, SOC-LM-02 |
| lateral_movement | investigate | 1 | 0.212 | 0.212 | SOC-LM-03 |
| lateral_movement | suppress | 2 | 0.150 | 0.150 | SOC-LM-04, SOC-LM-05 |
| lateral_movement | monitor | 1 | 0.155 | 0.155 | SOC-LM-06 |
| data_exfiltration | escalate | 2 | 0.358 | 0.358 | SOC-DE-01, SOC-DE-02 |
| data_exfiltration | investigate | 1 | 0.212 | 0.212 | SOC-DE-03 |
| data_exfiltration | suppress | 2 | 0.337 | 0.337 | SOC-DE-04, SOC-DE-05 |
| data_exfiltration | monitor | 1 | 0.175 | 0.175 | SOC-DE-06 |
| insider_threat | escalate | 2 | 0.413 | 0.413 | SOC-IT-01, SOC-IT-02 |
| insider_threat | investigate | 1 | 0.225 | 0.225 | SOC-IT-03 |
| insider_threat | suppress | 2 | 0.141 | 0.141 | SOC-IT-04, SOC-IT-05 |
| insider_threat | monitor | 1 | 0.188 | 0.188 | SOC-IT-06 |
| cloud_infrastructure | escalate | 2 | 0.825 | 0.825 | SOC-CI-01, SOC-CI-02 |
| cloud_infrastructure | investigate | 1 | 0.483 | 0.483 | SOC-CI-03 |
| cloud_infrastructure | suppress | 2 | 0.367 | 0.367 | SOC-CI-04, SOC-CI-05 |
| cloud_infrastructure | monitor | 1 | 0.333 | 0.333 | SOC-CI-06 |

Geometry guard: raw credential_access/monitor=0.1875; final=0.1875. Not required because raw mean < 0.40.

## 7. Full Section-7 scorer verification

Production L2 geometry and tau=0.1 were used. Expected-action result: **36/36**.
| Scenario | Expected | Winner | Status | Distance margin | Confidence |
|---|---|---|---|---|---|
| SOC-CA-01 | escalate | escalate | MATCH | 0.438 | 0.988 |
| SOC-CA-02 | escalate | escalate | MATCH | 0.240 | 0.917 |
| SOC-CA-03 | investigate | investigate | MATCH | 0.233 | 0.872 |
| SOC-CA-04 | suppress | suppress | MATCH | 0.184 | 0.863 |
| SOC-CA-05 | suppress | suppress | MATCH | 0.065 | 0.656 |
| SOC-CA-06 | monitor | monitor | MATCH | 0.140 | 0.756 |
| SOC-TI-01 | escalate | escalate | MATCH | 0.123 | 0.773 |
| SOC-TI-02 | escalate | escalate | MATCH | 0.277 | 0.941 |
| SOC-TI-03 | investigate | investigate | MATCH | 0.185 | 0.788 |
| SOC-TI-04 | suppress | suppress | MATCH | 0.203 | 0.884 |
| SOC-TI-05 | suppress | suppress | MATCH | 0.223 | 0.903 |
| SOC-TI-06 | monitor | monitor | MATCH | 0.198 | 0.819 |
| SOC-LM-01 | escalate | escalate | MATCH | 0.577 | 0.997 |
| SOC-LM-02 | escalate | escalate | MATCH | 0.548 | 0.996 |
| SOC-LM-03 | investigate | investigate | MATCH | 0.203 | 0.880 |
| SOC-LM-04 | suppress | suppress | MATCH | 0.158 | 0.828 |
| SOC-LM-05 | suppress | suppress | MATCH | 0.078 | 0.684 |
| SOC-LM-06 | monitor | monitor | MATCH | 0.093 | 0.690 |
| SOC-DE-01 | escalate | escalate | MATCH | 0.287 | 0.946 |
| SOC-DE-02 | escalate | escalate | MATCH | 0.221 | 0.901 |
| SOC-DE-03 | investigate | investigate | MATCH | 0.289 | 0.911 |
| SOC-DE-04 | suppress | suppress | MATCH | 0.170 | 0.846 |
| SOC-DE-05 | suppress | suppress | MATCH | 0.077 | 0.683 |
| SOC-DE-06 | monitor | monitor | MATCH | 0.144 | 0.793 |
| SOC-IT-01 | escalate | escalate | MATCH | 0.239 | 0.916 |
| SOC-IT-02 | escalate | escalate | MATCH | 0.172 | 0.848 |
| SOC-IT-03 | investigate | investigate | MATCH | 0.205 | 0.836 |
| SOC-IT-04 | suppress | suppress | MATCH | 0.222 | 0.902 |
| SOC-IT-05 | suppress | suppress | MATCH | 0.153 | 0.821 |
| SOC-IT-06 | monitor | monitor | MATCH | 0.202 | 0.820 |
| SOC-CI-01 | escalate | escalate | MATCH | 0.380 | 0.978 |
| SOC-CI-02 | escalate | escalate | MATCH | 0.283 | 0.944 |
| SOC-CI-03 | investigate | investigate | MATCH | 0.218 | 0.880 |
| SOC-CI-04 | suppress | suppress | MATCH | 0.201 | 0.882 |
| SOC-CI-05 | suppress | suppress | MATCH | 0.131 | 0.787 |
| SOC-CI-06 | monitor | monitor | MATCH | 0.131 | 0.760 |

Confidence range: min=0.6564, mean=0.8525, max=0.9969.

## 8. C9B and low-confidence companion
| Check | Winner | Confidence | Threshold | Result | Margin |
|---|---|---|---|---|---|
| C9B | investigate | 0.718243 | 0.620 | PASS | 0.098243 |
| Low-confidence companion | monitor | 0.542470 | 0.620 | PASS | -0.077530 |

Both checks are required; top-1 action preservation alone is insufficient.

## 9. IKS impact assessment

The immutable anchor was read but not changed. Current static bootstrap/anchor drift=0.000000, IKS=0.0; proposed candidate drift=0.180590, IKS=90.3. The latter is a candidate reference-point impact, not a live learned-state measurement. A proposed IKS below 67 is a migration problem under the design gate.

## 10. Recommendation

The panel is useful evidence for semantic reconciliation, but is not sufficient to trigger production migration. It is a synthetic judgment corpus, disposition-prior reasoning is not independent evidence, and single-value cells lack variance estimates. Use the candidate only for isolated replay/shadow analysis. Require SOC analyst review, identity-native pilot evidence, sparse-cell treatment, threshold replay, immutable-anchor/versioning, rollback, and product endpoint checks before migration.

## 11. Provenance and reproducibility

Arm-A values are model-aggregated panel judgments from the six source files, computed by `factor0()` in `scripts/analyze_factor0_panel.py`. The script reads the real SOC tensor, scenario fixture, and frozen IKS anchor without modifying them. The repository directory is `factor_0_panel_data` (underscore).

## Final results
| Check | Result |
|---|---|
| C1-C10 | computed |
| Scorer | 36/36 |
| C9B | PASS |
| Low-confidence companion | PASS |
| IKS | 0.0 -> 90.3 |
| Decision | CONDITIONAL / shadow-only |
