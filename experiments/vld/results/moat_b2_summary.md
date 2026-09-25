# B2 — Routing-level moat experiment

Date: September 14, 2026. random_state=42. K-only; no source modifications.
B2 supersedes B1's moat inference. B1's scripts, results and figures are retained unchanged. No B1 endpoint or conclusion was used as a target.

## 1. Pre-registered streams and realized distances

S_A uses unchanged KE-1 make_case with uniform categories and original exported geometry. The second-firm latent profile shifts means by [+0.75,−0.50,+1.00,−0.75,+0.50,−1.00] empirical geometry SD, scales factors by [1.35,.65,1.20,.80,1.10,.90], and mixes 30% of the preceding cyclic standardized factor. Values clip to [.02,.98]. SD is measured across centroid rows, not unit metric sigma. All same-domain LEARNERS retain the original μ/σ; only K learns. Changing latent profile changes data and verification distribution, not the learning algorithm.
Tier: second-firm perturbations/distances SIMULATED; original geometry REAL_COMPONENT with synthetic verification.

### SOC

Specified S_B category probabilities: {"cloud_infrastructure": 0.1, "credential_access": 0.05, "data_exfiltration": 0.2, "insider_threat": 0.15, "lateral_movement": 0.1, "malware_execution": 0.4}.
Relative action acceptance weights: {"escalate": 1.0, "investigate": 0.8, "monitor": 0.15, "suppress": 0.35}. These are acceptance weights; realized action frequencies are recorded separately in JSON.
Realized category KL(S_A||S_B)=0.201708 nats; KL(S_B||S_A)=0.195306 nats (2,000 training cases each).
Realized S_A priors: {"cloud_infrastructure": 0.1575, "credential_access": 0.161, "data_exfiltration": 0.1665, "insider_threat": 0.173, "lateral_movement": 0.169, "malware_execution": 0.173}.
Realized S_B priors: {"cloud_infrastructure": 0.103, "credential_access": 0.047, "data_exfiltration": 0.1945, "insider_threat": 0.155, "lateral_movement": 0.1, "malware_execution": 0.4005}.

| Factor (surface inputs) | A mean | B mean | B−A mean | A SD | B SD | B−A SD | Mean shift / A SD | Tier |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| privileged_identity_context | 0.59454 | 0.73608 | +0.14154 | 0.18990 | 0.10603 | -0.08387 | +0.745 | SIMULATED |
| asset_criticality | 0.52562 | 0.51543 | -0.01019 | 0.22452 | 0.15020 | -0.07432 | -0.045 | SIMULATED |
| threat_intel_enrichment | 0.42543 | 0.48382 | +0.05839 | 0.27004 | 0.24422 | -0.02581 | +0.216 | SIMULATED |
| pattern_history | 0.40410 | 0.34519 | -0.05890 | 0.21459 | 0.18764 | -0.02696 | -0.274 | SIMULATED |
| time_anomaly | 0.46577 | 0.48649 | +0.02072 | 0.20035 | 0.22735 | +0.02699 | +0.103 | SIMULATED |
| device_trust | 0.56182 | 0.22005 | -0.34177 | 0.31723 | 0.09602 | -0.22121 | -1.077 | SIMULATED |
Full latent-vector mean/SD tables and both correlation matrices are in stream_audit.realized_distribution_distance.factors.full and .surface.

### DATAOPS

Specified S_B category probabilities: {"freshness_violation": 0.1, "pipeline_failure": 0.45, "quality_anomaly": 0.1, "schema_change": 0.05, "transform_drift": 0.2, "volume_anomaly": 0.1}.
Relative action acceptance weights: {"auto_approve": 0.2, "escalate_to_owner": 0.8, "investigate": 1.0, "pause_downstream": 0.6, "refer_to_specialist": 0.4}. These are acceptance weights; realized action frequencies are recorded separately in JSON.
Realized category KL(S_A||S_B)=0.263656 nats; KL(S_B||S_A)=0.274902 nats (2,000 training cases each).
Realized S_A priors: {"freshness_violation": 0.168, "pipeline_failure": 0.1665, "quality_anomaly": 0.153, "schema_change": 0.152, "transform_drift": 0.1795, "volume_anomaly": 0.181}.
Realized S_B priors: {"freshness_violation": 0.0985, "pipeline_failure": 0.45, "quality_anomaly": 0.0875, "schema_change": 0.048, "transform_drift": 0.2205, "volume_anomaly": 0.0955}.

| Factor (surface inputs) | A mean | B mean | B−A mean | A SD | B SD | B−A SD | Mean shift / A SD | Tier |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| impact_scope | 0.45232 | 0.54007 | +0.08776 | 0.27442 | 0.24802 | -0.02640 | +0.320 | SIMULATED |
| source_reliability | 0.56566 | 0.39880 | -0.16686 | 0.28385 | 0.14216 | -0.14169 | -0.588 | SIMULATED |
| recurrence_frequency | 0.50720 | 0.73395 | +0.22676 | 0.33863 | 0.24658 | -0.09205 | +0.670 | SIMULATED |
| downstream_urgency | 0.47561 | 0.36114 | -0.11447 | 0.22709 | 0.13837 | -0.08873 | -0.504 | SIMULATED |
| data_freshness | 0.49151 | 0.66745 | +0.17594 | 0.25437 | 0.22920 | -0.02518 | +0.692 | SIMULATED |
| business_criticality | 0.60045 | 0.24600 | -0.35445 | 0.34138 | 0.15148 | -0.18990 | -1.038 | SIMULATED |
Full latent-vector mean/SD tables and both correlation matrices are in stream_audit.realized_distribution_distance.factors.full and .surface.

## 2. Frozen held-out slice and leakage checks

For each copilot, generate 3,000 S_A cases and independently shuffle split indices: 600 fixed test (20%), 400 development, 2,000 training. Both test sets are frozen/hash-checked BEFORE generating any S_B. Category+surface fingerprints and indices have no test/train/development overlap. No arm receives test cases for learning, threshold selection or stopping. Every arm—including migration and the incompatible-domain probe—records both metrics on exactly this same primary S_A test. Arm 2's S_B development evaluation is only a stopping monitor, never the reported moat test.
Arm 4 additionally evaluates a paired drifted-current S_A slice, shared by migrant and current incumbent. This supplemental test does not replace the common original S_A test. Split indices and evaluation hashes are persisted in the JSON. Synthetic verification is the geometry-derived full-vector oracle; the informative-read evidence model is inherited from KE-1 and is not live customer evidence.
Convergence is development max−min ≤0.5pp in both metrics over three consecutive checkpoints, minimum N500, maximum N2000, checkpoints every 50. It is a finite operational criterion, not mathematical asymptotic convergence. The inputs-only arm uses unlabeled action/read-plan stability because verified development labels would violate that condition. Held-out final-window flatness is a diagnostic, not a checkpoint-selection criterion.
Parity uses both metrics against the mean of Arm 1's final three held-out checkpoints at its development-defined convergence. Reported time is the onset of three qualifying checkpoints; confirmation is separately shown. Later losses are disclosed. Not-reached is censored at the actual stopping count.

## 3. Arm 1 convergence

| Copilot | Convergence N | Stop N | Converged routing_quality | Converged action_accuracy | Held-out last 3 flat | Tier |
|---|---:|---:|---:|---:|---|---|
| soc | 500 | 500 | 82.1944% | 94.3333% | True | REAL_COMPONENT |
| dataops | 650 | 650 | 57.6667% | 82.6667% | True | REAL_COMPONENT |

## 4. Arm 2 — pre-registered decision rule

> "The moat is data-specific (strong claim) IFF Arm 2 fails to reach sustained parity on the incumbent’s held-out decisions. If Arm 2 reaches parity, the moat is time-only and the paper weakens the claim—with this evidence."

Every claim below means **routing-level specificity of K under this learner/profile/horizon**. μ-specificity is untested and dependent on TIER-6/7. Joint parity additionally requires action_accuracy.

| Copilot | Parity onset | Confirmation | Stop N | Routing deficit (pp) | Action deficit (pp) | Later loss | Tier |
|---|---|---|---:|---:|---:|---|---|
| soc | not_reached | None | 800 | +29.278 | +37.667 | False | SIMULATED |
| dataops | not_reached | None | 600 | +6.167 | +16.167 | False | SIMULATED |

**soc: DATA-SPECIFIC under the pre-registered routing-level rule, within the observed horizon.** Final routing_quality=52.917%; action_accuracy=56.667%. No S_A training inputs or verified labels were supplied to this learner. Failure to reach parity at a finite stopping horizon does not prove failure for every competitor, algorithm or future stream.

**dataops: DATA-SPECIFIC under the pre-registered routing-level rule, within the observed horizon.** Final routing_quality=51.500%; action_accuracy=66.500%. No S_A training inputs or verified labels were supplied to this learner. Failure to reach parity at a finite stopping horizon does not prove failure for every competitor, algorithm or future stream.

## 5. Arm 3 — access versus catch-up

Deficit is incumbent converged level minus final entrant; a negative deficit means outperformance. Labels received are counted; a fraction is not treated as free access. Original training evidence remains the KE-1 synthetic oracle-coupled provider. Inputs-only gets neither latent full vectors nor clean informative tags. Noisy arms queue captured investigations for 50 decisions and credit only the received label plus acquired evidence.

| Copilot | Access | Parity onset | Confirmation | Stop N | A labels received | Routing deficit pp | Action deficit pp | Tier |
|---|---|---|---|---:|---:|---:|---:|---|
| soc | arm3a_inputs_no_labels | not_reached | None | 2000 | 0 | +21.611 | +26.833 | SIMULATED |
| soc | arm3b_10pct | not_reached | None | 500 | 50 | +18.861 | +18.167 | SIMULATED |
| soc | arm3b_50pct | not_reached | None | 1000 | 500 | +6.028 | +7.167 | SIMULATED |
| soc | arm3c_eps10 | not_reached | None | 850 | 800 | +0.694 | +3.333 | SIMULATED |
| soc | arm3c_eps25 | not_reached | None | 1000 | 950 | +0.778 | +3.000 | SIMULATED |
| dataops | arm3a_inputs_no_labels | not_reached | None | 2000 | 0 | +7.000 | +12.500 | SIMULATED |
| dataops | arm3b_10pct | not_reached | None | 700 | 70 | +4.500 | +12.833 | SIMULATED |
| dataops | arm3b_50pct | not_reached | None | 650 | 325 | -1.500 | +1.833 | SIMULATED |
| dataops | arm3c_eps10 | not_reached | None | 500 | 450 | +2.917 | +4.667 | SIMULATED |
| dataops | arm3c_eps25 | not_reached | None | 550 | 500 | +2.667 | +3.167 | SIMULATED |

A failure of 3a supports the value of verified labels relative to this particular self-label baseline; it does **not** show that labels are unobtainable or that all unlabeled methods must fail. See JSON for actual corruption fractions, pending verifications, later parity losses and paid evidence reads.

## 6. Arm 4 — measured switching-cost decomposition

Predeclared drift: ±.25 empirical geometry SD, factor scales [1.10,.90,1.10,.90,1.05,.95], rho=.10 cyclic mixing, clipped [.02,.98], category/action sampling unchanged. Drift is not tuned after execution. Staleness dip compares the SAME migrated state before versus after the paired drift; it may be zero or negative. Re-parity compares to a continuing incumbent independently adapted on the drifted training stream. No μ updates occur; copied μ retains its values. Cost is measured adaptation/re-verification volume, plus a qualitative integration burden; no invented dollar or engineering-hour estimate.

| Copilot | Routing staleness dip pp | Action staleness dip pp | Gap to current routing pp | Gap to current action pp | Re-parity onset | Confirmation | Current reference convergence N | Tier |
|---|---:|---:|---:|---:|---|---|---|---|
| soc | +21.750 | +23.500 | +3.889 | +1.167 | 250 | 350 | 500 | SIMULATED |
| dataops | -7.750 | +1.833 | +2.889 | +0.833 | 300 | 400 | 500 | SIMULATED |

soc: Measured re-parity onset=250, confirmation=350 processed/verified drift decisions. Engineering burden not monetized: schema/factor mapping, state export/import, provenance validation, scorer parity checks and current-outcome re-verification. Final pending verifications=0; total adaptation decisions actually run=500. Illustrative weeks to re-parity=0.20833333333333334 at 1200 verified/week.

dataops: Measured re-parity onset=300, confirmation=400 processed/verified drift decisions. Engineering burden not monetized: schema/factor mapping, state export/import, provenance validation, scorer parity checks and current-outcome re-verification. Final pending verifications=0; total adaptation decisions actually run=500. Illustrative weeks to re-parity=2.830188679245283 at 106 verified/week.

The stability confirmation window is an observation requirement, not a claim that all those labels are technically necessary for recovery. Copying K/μ is explicitly customer-authorized full-state access; this arm does not independently test the competitor-without-data moat.

## 7. Transfer-across-incompatible-domains probe

**Not a robustness replication. No replication weight.** The source domain learns on its own exported geometry and S_A training data. At evaluation only, K is mapped by category/factor position into target native geometry. This positional bridge is SIMULATED; source and target geometries are REAL_COMPONENT. No action indices or μ are transferred. Different factor meanings make transfer failure ambiguous; even agreement with Arm 2 is not independent replication evidence.

| Target | Trained on | Parity onset | Final routing_quality | Final action_accuracy | Same reach/fail as Arm 2 | Tier |
|---|---|---|---:|---:|---|---|
| soc | dataops | not_reached | 63.000% | 64.667% | True | REAL_COMPONENT geometry / SIMULATED mapping |
| dataops | soc | not_reached | 48.750% | 71.500% | True | REAL_COMPONENT geometry / SIMULATED mapping |

dataops → soc factor mapping:

| Index | Source factor | Target factor |
|---:|---|---|
| 0 | impact_scope | privileged_identity_context |
| 1 | source_reliability | asset_criticality |
| 2 | recurrence_frequency | threat_intel_enrichment |
| 3 | downstream_urgency | pattern_history |
| 4 | data_freshness | time_anomaly |
| 5 | business_criticality | device_trust |
Category mapping by corresponding export index: [{"index": 0, "source": "schema_change", "target": "credential_access"}, {"index": 1, "source": "volume_anomaly", "target": "malware_execution"}, {"index": 2, "source": "quality_anomaly", "target": "lateral_movement"}, {"index": 3, "source": "freshness_violation", "target": "data_exfiltration"}, {"index": 4, "source": "pipeline_failure", "target": "insider_threat"}, {"index": 5, "source": "transform_drift", "target": "cloud_infrastructure"}].

soc → dataops factor mapping:

| Index | Source factor | Target factor |
|---:|---|---|
| 0 | privileged_identity_context | impact_scope |
| 1 | asset_criticality | source_reliability |
| 2 | threat_intel_enrichment | recurrence_frequency |
| 3 | pattern_history | downstream_urgency |
| 4 | time_anomaly | data_freshness |
| 5 | device_trust | business_criticality |
Category mapping by corresponding export index: [{"index": 0, "source": "credential_access", "target": "schema_change"}, {"index": 1, "source": "malware_execution", "target": "volume_anomaly"}, {"index": 2, "source": "lateral_movement", "target": "quality_anomaly"}, {"index": 3, "source": "data_exfiltration", "target": "freshness_violation"}, {"index": 4, "source": "insider_threat", "target": "pipeline_failure"}, {"index": 5, "source": "cloud_infrastructure", "target": "transform_drift"}].

## 8. Paper conclusion

Under the pre-registered rule, soc: DATA-SPECIFIC under the pre-registered routing-level rule, within the observed horizon (joint parity=not_reached, observed N=800); dataops: DATA-SPECIFIC under the pre-registered routing-level rule, within the observed horizon (joint parity=not_reached, observed N=600). These are finite, single-seed tests of routing-level specificity in learned K, using exported geometry and synthetic verified outcomes. They neither establish μ-specificity nor prove labels unobtainable. Partial-access and migration outcomes quantify this learner's information/re-verification tradeoffs; the incompatible-domain probe has no replication weight. The stronger interpretation is conditional on the stated convergence criterion and cannot be generalized beyond the tested profiles.

## 9. Revised Fig-2 data and reproducibility

Use each copilot's fig2_data.incumbent and fig2_data.independent for both routing_quality and action_accuracy curves; use fig2_data.access for the partial-access panel. Raw checkpoints retain K, labels received, stopping metrics, exact counts and evaluation-set hashes. These replace B1's moat figure DATA; no existing figure file is overwritten.
Wall-clock assumptions: SOC=1,200 and DataOps=106 verified outcomes/week from MAP v20 ($7B manufacturer); tier ILLUSTRATIVE. The JSON stores weeks per arm.
Run mypy on experiments/vld/vld_moat_b2_v1.py before python -B experiments/vld/vld_moat_b2_v1.py. The script performs two independent full computations and compares canonical JSON bytes. The recorded determinism hash excludes only metadata.determinism_hash.
Mypy passed before execution. Full determinism self-test passed; source/geometry hashes are retained. Only this new script, result JSON and summary were authored; no git commands or source modifications.
