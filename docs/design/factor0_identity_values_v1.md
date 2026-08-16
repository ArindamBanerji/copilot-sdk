# Factor-0 Identity-Context Values v1

## Method

These are domain judgments for the live `PrivilegedIdentityContextFactor`,
not a rename of the existing travel values. Each value is the arithmetic mean
of four components, rounded to two decimals:

* **Title:** `0.9` for admin/root/service/system/svc, `0.7` for executive or
  director-level roles, `0.2` for an ordinary user, and `0.5` when unclear.
* **MFA:** `0.85` when compromised credentials, stolen sessions, or an auth
  bypass is implied; `0.10` for a normal verified action; `0.50` when unclear.
* **Device:** `0.80` for an unmanaged, unfamiliar, or suspicious endpoint;
  `0.10` for a known managed device; `0.45` when unclear.
* **User risk:** an identity-provider estimate based on the scenario: low
  regular-user risk is `0.2-0.3`, suspicious/changed/privileged identities are
  `0.6-0.8`, and unknown is `0.5`.

The old value is shown only for audit comparison. It is not used as evidence
for the new value. The source scenarios remain legacy fixtures marked
`factor_0_semantic_version: "travel_match_v1"`.

## Values table

| # | Scenario | Category | Expected action | Old travel_match | New identity_context | Component breakdown (title / MFA / device / risk) | Confidence | Description change needed? |
|---:|---|---|---|---:|---:|---|---|---|
| 1 | SOC-CA-01 | credential_access | escalate | 0.30 | **0.71** | 0.50 / 0.85 / 0.80 / 0.70 = 0.71 | MEDIUM | No |
| 2 | SOC-CA-02 | credential_access | escalate | 0.90 | **0.76** | 0.90 / 0.85 / 0.50 / 0.80 = 0.76 | HIGH | Yes |
| 3 | SOC-CA-03 | credential_access | investigate | 0.40 | **0.50** | 0.50 / 0.50 / 0.45 / 0.55 = 0.50 | LOW | No |
| 4 | SOC-CA-04 | credential_access | suppress | 0.20 | **0.15** | 0.20 / 0.10 / 0.10 / 0.20 = 0.15 | HIGH | No |
| 5 | SOC-CA-05 | credential_access | suppress | 0.20 | **0.15** | 0.20 / 0.10 / 0.10 / 0.20 = 0.15 | HIGH | No |
| 6 | SOC-CA-06 | credential_access | monitor | 0.30 | **0.36** | 0.20 / 0.50 / 0.45 / 0.30 = 0.36 | MEDIUM | No |
| 7 | SOC-TI-01 | malware_execution | escalate | 0.30 | **0.50** | 0.50 / 0.50 / 0.45 / 0.55 = 0.50 | LOW | No |
| 8 | SOC-TI-02 | malware_execution | escalate | 0.90 | **0.76** | 0.90 / 0.85 / 0.50 / 0.80 = 0.76 | HIGH | Yes |
| 9 | SOC-TI-03 | malware_execution | investigate | 0.30 | **0.50** | 0.50 / 0.50 / 0.45 / 0.55 = 0.50 | LOW | No |
| 10 | SOC-TI-04 | malware_execution | suppress | 0.20 | **0.15** | 0.20 / 0.10 / 0.10 / 0.20 = 0.15 | HIGH | No |
| 11 | SOC-TI-05 | malware_execution | suppress | 0.20 | **0.15** | 0.20 / 0.10 / 0.10 / 0.20 = 0.15 | HIGH | No |
| 12 | SOC-TI-06 | malware_execution | monitor | 0.20 | **0.50** | 0.50 / 0.50 / 0.45 / 0.55 = 0.50 | LOW | No |
| 13 | SOC-LM-01 | lateral_movement | escalate | 0.50 | **0.51** | 0.50 / 0.50 / 0.45 / 0.60 = 0.51 | MEDIUM | No |
| 14 | SOC-LM-02 | lateral_movement | escalate | 0.50 | **0.71** | 0.50 / 0.85 / 0.80 / 0.70 = 0.71 | MEDIUM | No |
| 15 | SOC-LM-03 | lateral_movement | investigate | 0.40 | **0.50** | 0.50 / 0.50 / 0.45 / 0.55 = 0.50 | LOW | No |
| 16 | SOC-LM-04 | lateral_movement | suppress | 0.90 | **0.15** | 0.20 / 0.10 / 0.10 / 0.20 = 0.15 | MEDIUM | Yes |
| 17 | SOC-LM-05 | lateral_movement | suppress | 0.80 | **0.15** | 0.20 / 0.10 / 0.10 / 0.20 = 0.15 | MEDIUM | Yes |
| 18 | SOC-LM-06 | lateral_movement | monitor | 0.40 | **0.36** | 0.20 / 0.50 / 0.45 / 0.30 = 0.36 | LOW | No |
| 19 | SOC-DE-01 | data_exfiltration | escalate | 0.30 | **0.69** | 0.50 / 0.85 / 0.80 / 0.60 = 0.69 | MEDIUM | No |
| 20 | SOC-DE-02 | data_exfiltration | escalate | 0.30 | **0.71** | 0.50 / 0.85 / 0.80 / 0.70 = 0.71 | MEDIUM | No |
| 21 | SOC-DE-03 | data_exfiltration | investigate | 0.30 | **0.49** | 0.50 / 0.50 / 0.45 / 0.50 = 0.49 | LOW | No |
| 22 | SOC-DE-04 | data_exfiltration | suppress | 0.20 | **0.15** | 0.20 / 0.10 / 0.10 / 0.20 = 0.15 | HIGH | No |
| 23 | SOC-DE-05 | data_exfiltration | suppress | 0.20 | **0.15** | 0.20 / 0.10 / 0.10 / 0.20 = 0.15 | HIGH | No |
| 24 | SOC-DE-06 | data_exfiltration | monitor | 0.20 | **0.39** | 0.20 / 0.50 / 0.45 / 0.40 = 0.39 | MEDIUM | No |
| 25 | SOC-IT-01 | insider_threat | escalate | 0.40 | **0.61** | 0.20 / 0.85 / 0.80 / 0.60 = 0.61 | HIGH | No |
| 26 | SOC-IT-02 | insider_threat | escalate | 0.40 | **0.49** | 0.20 / 0.50 / 0.45 / 0.80 = 0.49 | MEDIUM | No |
| 27 | SOC-IT-03 | insider_threat | investigate | 0.40 | **0.50** | 0.50 / 0.50 / 0.45 / 0.55 = 0.50 | LOW | No |
| 28 | SOC-IT-04 | insider_threat | suppress | 0.30 | **0.15** | 0.20 / 0.10 / 0.10 / 0.20 = 0.15 | HIGH | No |
| 29 | SOC-IT-05 | insider_threat | suppress | 0.30 | **0.15** | 0.20 / 0.10 / 0.10 / 0.20 = 0.15 | HIGH | No |
| 30 | SOC-IT-06 | insider_threat | monitor | 0.30 | **0.36** | 0.20 / 0.50 / 0.45 / 0.30 = 0.36 | LOW | No |
| 31 | SOC-CI-01 | cloud_infrastructure | escalate | 0.20 | **0.60** | 0.50 / 0.50 / 0.80 / 0.60 = 0.60 | MEDIUM | No |
| 32 | SOC-CI-02 | cloud_infrastructure | escalate | 0.30 | **0.79** | 0.70 / 0.85 / 0.80 / 0.80 = 0.79 | MEDIUM | No |
| 33 | SOC-CI-03 | cloud_infrastructure | investigate | 0.30 | **0.49** | 0.50 / 0.50 / 0.45 / 0.50 = 0.49 | LOW | No |
| 34 | SOC-CI-04 | cloud_infrastructure | suppress | 0.20 | **0.55** | 0.90 / 0.50 / 0.10 / 0.70 = 0.55 | MEDIUM | No |
| 35 | SOC-CI-05 | cloud_infrastructure | suppress | 0.20 | **0.50** | 0.90 / 0.50 / 0.10 / 0.50 = 0.50 | MEDIUM | No |
| 36 | SOC-CI-06 | cloud_infrastructure | monitor | 0.20 | **0.34** | 0.20 / 0.50 / 0.45 / 0.20 = 0.34 | LOW | No |

## Revised descriptions

These replace travel-based causal language; they do not assert facts absent
from the original scenario.

* **SOC-CA-02:** “Privileged account credential access with an active IOC match; elevated identity risk requires escalation despite the absence of confirmed device context.”
* **SOC-TI-02:** “Privileged account associated with a critical IOC match; elevated identity risk and threat evidence require immediate escalation.”
* **SOC-LM-04:** “Lateral movement from a regular user on a known managed device toward a non-critical asset, with no independent identity-risk indicators.”
* **SOC-LM-05:** “Lateral access from a regular user on a known managed device toward a non-critical target; identity context is low, but the event remains subject to monitoring.”

## Distribution analysis

Using the table as written:

* High confidence: **11**
* Medium confidence: **14**
* Low confidence: **11**
* Description changes needed: **4**

The qualitative distribution is defensible: credential theft, suspicious
sessions, unmanaged endpoints, insider indicators, and privileged service
activity receive more identity concern; routine managed-device activity receives
low concern; and descriptions with no identity evidence remain near the neutral
default. Cloud service accounts are not automatically low-risk: a service
identity can be highly privileged even when the operation is authorized.

The other five factors should continue to dominate many outcomes. The largest
semantic shifts are the travel-derived lateral-movement suppress cases
(SOC-LM-04/05), privileged travel descriptions (SOC-CA-02 and SOC-TI-02), and
suspicious exfiltration/identity cases. These shifts are directionally
consistent with the expected actions, but an action-level claim requires an
actual scorer run after the values are integrated.

## Flagged scenarios

1. **SOC-CA-03, SOC-TI-01, SOC-TI-03, SOC-TI-06, SOC-LM-03, SOC-LM-06,
   SOC-DE-03, SOC-DE-06, SOC-IT-03, SOC-IT-06, SOC-CI-01, SOC-CI-03, and
   SOC-CI-06:** identity details are insufficient for high-confidence
   calibration. These should be checked against representative identity-provider
   telemetry or explicitly retained as neutral/uncertain fixtures.
2. **Potential action-flip review:** SOC-LM-04/05 move sharply downward and
   should preserve suppression; SOC-CI-04/05 move upward because service
   accounts are inherently privileged and should be scorer-checked to ensure
   legitimate maintenance still suppresses. No flip can be asserted without
   running the real scorer with the other five factors unchanged.

## Recommendation

These values are a useful **domain-review draft**, not implementation-ready
data. Resolve SOC-IT-01 first, then have a SOC analyst confirm the medium/low
confidence scenarios and run the real evaluation scorer with the proposed
identity-context values. Only after that review should the legacy fixture set
be replaced or a new identity-context fixture set be promoted. Do not alter
the production JSON or customer-facing metrics from this document alone.
