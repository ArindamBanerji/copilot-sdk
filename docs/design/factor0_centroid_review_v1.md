# Factor-0 Centroid Prior Review v1

## Method

This review treats μ₀ as a Day-1 prior for **privileged identity context**,
not as a label attached to the old travel prior. Each entry was evaluated using
the category, action, existing factors, and the live computation's four signals:
privilege/title, MFA state, device familiarity, and identity-provider risk.

The proposed values are deliberately conservative priors. They are not claims
about a particular customer population and must be validated against the real
scorer and SOC analyst review before being written into production. The
scenario-level draft in `factor0_identity_values_v1.md` was used as an
alignment check, not as independent ground truth.

## Review table

| Category | Action | Current μ₀ | Proposed μ₀ | Status | Rationale |
|---|---|---:|---:|---|---|
| credential_access | escalate | 0.75 | **0.75** | KEEP | Stolen credentials commonly target privileged identities; untrusted endpoints and MFA bypass are high-concern combinations. |
| credential_access | investigate | 0.60 | **0.55** | REVISE | Investigation is uncertain, but credential compromise still gives identity context a moderately high prior. |
| credential_access | suppress | 0.30 | **0.15** | REVISE | Suppression should describe routine, MFA-protected activity from a known device and ordinary user. |
| credential_access | monitor | 0.20 | **0.35** | REVISE | Monitoring can still involve an unresolved identity signal; 0.20 is too certain that the actor is benign. |
| malware_execution | escalate | 0.75 | **0.70** | REVISE | Malware severity does not prove privilege, but escalation cases often involve compromised or high-risk identities. |
| malware_execution | investigate | 0.60 | **0.50** | UNCERTAIN | IOC evidence is present, but the scenario descriptions rarely identify the account, MFA, or device. |
| malware_execution | suppress | 0.30 | **0.15** | REVISE | False-positive malware events explicitly use trusted managed devices and should have low identity concern. |
| malware_execution | monitor | 0.20 | **0.35** | UNCERTAIN | Low-confidence IOC activity may be ordinary-user noise, but the description does not establish that identity context. |
| lateral_movement | escalate | 0.75 | **0.70** | REVISE | Escalated lateral movement frequently involves privileged paths, stolen sessions, or unknown endpoints. |
| lateral_movement | investigate | 0.60 | **0.50** | UNCERTAIN | Moderate lateral signals do not identify the actor's privilege or authentication posture. |
| lateral_movement | suppress | 0.30 | **0.15** | REVISE | A suppressed case should be supported by ordinary identity, verified MFA, and a known managed device. |
| lateral_movement | monitor | 0.20 | **0.35** | UNCERTAIN | A single hop may be benign, but the source description does not prove a low-risk identity. |
| data_exfiltration | escalate | 0.75 | **0.70** | REVISE | Large or recurring exfiltration with suspicious timing/destination warrants a moderately high actor-risk prior. |
| data_exfiltration | investigate | 0.60 | **0.50** | UNCERTAIN | High asset criticality is not identity evidence; the actor's role and authentication state are unspecified. |
| data_exfiltration | suppress | 0.30 | **0.15** | REVISE | Authorized scheduled transfers from trusted devices are the clearest low-identity-risk baseline. |
| data_exfiltration | monitor | 0.20 | **0.35** | UNCERTAIN | Moderate transfer volume without IOC is not enough to establish either benign or privileged identity context. |
| insider_threat | escalate | 0.75 | **0.75** | KEEP | The category is explicitly about an authorized actor behaving maliciously; escalation should start with high identity concern. |
| insider_threat | investigate | 0.60 | **0.55** | UNCERTAIN | Insider indicators imply concern, but the description does not establish privilege, MFA, or device posture. |
| insider_threat | suppress | 0.30 | **0.15** | REVISE | Manager approval, known device, and no history support a low identity-risk prior despite the category. |
| insider_threat | monitor | 0.20 | **0.35** | UNCERTAIN | Weak insider signals should not be treated as benign identity context without corroborating identity evidence. |
| cloud_infrastructure | escalate | 0.75 | **0.60** | REVISE | Cloud escalation may involve a privileged workload or service account, but infrastructure severity alone does not establish the actor. |
| cloud_infrastructure | investigate | 0.60 | **0.45** | UNCERTAIN | Developers, SREs, and service accounts are all plausible; the descriptions do not distinguish them. |
| cloud_infrastructure | suppress | 0.30 | **0.30** | KEEP | Scheduled maintenance from a trusted source is compatible with a known, authorized service identity, though not zero risk. |
| cloud_infrastructure | monitor | 0.20 | **0.30** | UNCERTAIN | Low-risk configuration activity suggests lower concern, but the acting identity is not described. |

## Pattern analysis

### Monotonicity check

Using action order `escalate, investigate, suppress, monitor`, the intended
ordering check is `escalate ≥ investigate ≥ monitor ≥ suppress`:

| Category | Proposed sequence | Result |
|---|---|---|
| credential_access | 0.75, 0.55, 0.15, 0.35 | Pass after reading as escalate ≥ investigate ≥ monitor ≥ suppress: **0.75 ≥ 0.55 ≥ 0.35 ≥ 0.15** |
| malware_execution | 0.70, 0.50, 0.15, 0.35 | Pass after action-order normalization: **0.70 ≥ 0.50 ≥ 0.35 ≥ 0.15** |
| lateral_movement | 0.70, 0.50, 0.15, 0.35 | Pass after action-order normalization. |
| data_exfiltration | 0.70, 0.50, 0.15, 0.35 | Pass after action-order normalization. |
| insider_threat | 0.75, 0.55, 0.15, 0.35 | Pass after action-order normalization. |
| cloud_infrastructure | 0.60, 0.45, 0.30, 0.30 | Pass, with monitor and suppress intentionally tied. |

The tensor's physical axis order is `[escalate, investigate, suppress,
monitor]`; the comparisons above reorder the last two for the stated semantic
check. The equality/tie in cloud activity avoids inventing a distinction the
scenario descriptions do not support.

### Category pattern check

| Rank | Category | Proposed average |
|---:|---|---:|
| 1 | credential_access | 0.45 |
| 1 | insider_threat | 0.45 |
| 3 | lateral_movement | 0.425 |
| 3 | data_exfiltration | 0.425 |
| 5 | malware_execution | 0.425 |
| 6 | cloud_infrastructure | 0.4125 |

Credential access and insider threat are highest, as expected because identity
is central to those categories. Cloud infrastructure is lowest because the
actor can be a regular developer, SRE, or service account; the category alone
does not establish identity risk. Malware and lateral movement remain close to
cloud because their technical evidence is not automatically identity evidence.

### Range assessment

The proposed range is **0.15–0.75**. This is broad enough to distinguish
known-benign managed activity from suspicious privileged activity, but it does
not use extreme 0.0/1.0 values without direct evidence. The values are not a
uniform 0.5 prior, and the repeated values are intentional category/action
priors rather than claims of per-alert precision.

### Alignment with scenario values (Step 1)

The alignment is directionally sound:

* Credential-access scenario values cluster around 0.71/0.76 for escalation,
  0.50 for investigation, 0.15 for suppression, and 0.36 for monitoring;
  these support the proposed 0.75/0.55/0.15/0.35.
* Malware, lateral-movement, and data-exfiltration scenario values support
  high escalation, neutral investigation, low suppression, and moderate
  monitoring priors.
* Insider-threat scenarios support a high escalation prior even though the
  single draft escalation scenario has incomplete identity details.
* Cloud scenarios justify a lower overall prior, except that service-account
  maintenance must not be mistaken for an ordinary human user.

The largest residual uncertainty is not arithmetic; it is the missing identity
provider, MFA, and device evidence in many scenario descriptions.

### Cross-factor coherence

The proposed factor-0 values agree with the other factors without duplicating
them. High asset criticality, threat-intel severity, or time anomaly can justify
escalation while factor 0 remains neutral when the actor is unknown. Conversely,
an unknown device or compromised identity can raise factor 0 even when asset
criticality is modest. This separation is preferable to using factor 0 as a
second threat-intel or asset-criticality signal.

The proposed 0.15 suppression priors align with the existing trusted-device
values near 0.80–0.90 in the other factors. The cloud suppression prior stays
at 0.30 because a trusted CI/CD service account is still a privileged identity,
even when the action is authorized.

## Summary

* Total entries: **24**
* KEEP: **3**
* REVISE: **11**
* UNCERTAIN: **10**

## Largest deltas from current values

The largest absolute delta is **0.15**, occurring in multiple entries:

* `cloud_infrastructure / escalate`: **0.75 → 0.60**. Infrastructure
  severity is not sufficient to assume a privileged actor.
* `cloud_infrastructure / investigate`: **0.60 → 0.45**. Actor type is
  unspecified.
* All `monitor` priors except cloud: **0.20 → 0.35**. Monitoring does not
  prove a benign identity; it reflects unresolved identity context.
* Most `suppress` priors: **0.30 → 0.15**. Suppression is reserved for
  explicitly trusted, ordinary, managed activity.

These changes are not intended to preserve the travel-derived ordering. They
replace it with an identity-risk ordering while keeping values conservative.

## Recommendation

The proposed prior is **not yet ready for production implementation**. It is
ready for a structured SOC analyst review, followed by a real scorer comparison
with the other five factors unchanged.

Before implementation:

1. Obtain analyst confirmation for the nine UNCERTAIN entries.
2. Verify that the scorer's polarity and action-selection behavior interpret
   factor 0 as intended; in particular, test cloud service-account cases.
3. Run the existing 36-scenario evaluation with the proposed values and record
   any expected-action changes.
4. Preserve the legacy fixture set and provenance until the new identity-context
   fixture set is approved.

Using the current travel-derived values risks encoding location-explanation
semantics as identity risk. Using uniform `0.5` would be safer semantically but
would discard useful Day-1 distinctions. The proposed values are a better
interim hypothesis, but only analyst review and scorer evidence can promote
them to a production prior.
