# Factor-0 scorer verification output

Bootstrap squared-L2 scoring; no application state is mutated.

| # | Scenario | Category | Expected | Current winner | Proposed winner | Status | Margin (curr) | Margin (prop) |
|---:|---|---|---|---|---|---|---:|---:|
| 1 | SOC-CA-01 | credential_access | escalate | escalate | escalate | SAME | 0.288000 | 0.301500 |
| 2 | SOC-CA-02 | credential_access | escalate | escalate | escalate | SAME | 0.303000 | 0.321500 |
| 3 | SOC-CA-03 | credential_access | investigate | investigate | investigate | SAME | 0.267500 | 0.207500 |
| 4 | SOC-CA-04 | credential_access | suppress | suppress | suppress | SAME | 0.162500 | 0.222500 |
| 5 | SOC-CA-05 | credential_access | suppress | suppress | suppress | SAME | 0.042500 | 0.102500 |
| 6 | SOC-CA-06 | credential_access | monitor | monitor | monitor | SAME | 0.115500 | 0.181500 |
| 7 | SOC-TI-01 | malware_execution | escalate | escalate | escalate | SAME | 0.080000 | 0.092500 |
| 8 | SOC-TI-02 | malware_execution | escalate | escalate | escalate | SAME | 0.278000 | 0.316500 |
| 9 | SOC-TI-03 | malware_execution | investigate | investigate | investigate | SAME | 0.230000 | 0.217500 |
| 10 | SOC-TI-04 | malware_execution | suppress | suppress | suppress | SAME | 0.182500 | 0.242500 |
| 11 | SOC-TI-05 | malware_execution | suppress | suppress | suppress | SAME | 0.202500 | 0.262500 |
| 12 | SOC-TI-06 | malware_execution | monitor | monitor | monitor | SAME | 0.147500 | 0.227500 |
| 13 | SOC-LM-01 | lateral_movement | escalate | escalate | escalate | SAME | 0.153000 | 0.166500 |
| 14 | SOC-LM-02 | lateral_movement | escalate | escalate | escalate | SAME | 0.213000 | 0.246500 |
| 15 | SOC-LM-03 | lateral_movement | investigate | investigate | investigate | SAME | 0.270000 | 0.222500 |
| 16 | SOC-LM-04 | lateral_movement | suppress | suppress | suppress | SAME | 0.137500 | 0.197500 |
| 17 | SOC-LM-05 | lateral_movement | suppress | suppress | suppress | SAME | 0.057500 | 0.117500 |
| 18 | SOC-LM-06 | lateral_movement | monitor | monitor | monitor | SAME | 0.070500 | 0.136500 |
| 19 | SOC-DE-01 | data_exfiltration | escalate | escalate | escalate | SAME | 0.297000 | 0.328500 |
| 20 | SOC-DE-02 | data_exfiltration | escalate | escalate | escalate | SAME | 0.183000 | 0.216500 |
| 21 | SOC-DE-03 | data_exfiltration | investigate | investigate | investigate | SAME | 0.353000 | 0.307000 |
| 22 | SOC-DE-04 | data_exfiltration | suppress | suppress | suppress | SAME | 0.112500 | 0.172500 |
| 23 | SOC-DE-05 | data_exfiltration | suppress | suppress | suppress | SAME | 0.042500 | 0.102500 |
| 24 | SOC-DE-06 | data_exfiltration | monitor | monitor | monitor | SAME | 0.089500 | 0.173500 |
| 25 | SOC-IT-01 | insider_threat | escalate | escalate | escalate | SAME | 0.160500 | 0.164000 |
| 26 | SOC-IT-02 | insider_threat | escalate | escalate | escalate | SAME | 0.104500 | 0.096000 |
| 27 | SOC-IT-03 | insider_threat | investigate | investigate | investigate | SAME | 0.222500 | 0.230000 |
| 28 | SOC-IT-04 | insider_threat | suppress | suppress | suppress | SAME | 0.200000 | 0.260000 |
| 29 | SOC-IT-05 | insider_threat | suppress | suppress | suppress | SAME | 0.130000 | 0.190000 |
| 30 | SOC-IT-06 | insider_threat | monitor | monitor | monitor | SAME | 0.178000 | 0.244000 |
| 31 | SOC-CI-01 | cloud_infrastructure | escalate | escalate | escalate | SAME | 0.232500 | 0.277500 |
| 32 | SOC-CI-02 | cloud_infrastructure | escalate | escalate | escalate | SAME | 0.209500 | 0.254500 |
| 33 | SOC-CI-03 | cloud_infrastructure | investigate | investigate | investigate | SAME | 0.267000 | 0.229500 |
| 34 | SOC-CI-04 | cloud_infrastructure | suppress | suppress | suppress | SAME | 0.260000 | 0.200000 |
| 35 | SOC-CI-05 | cloud_infrastructure | suppress | suppress | suppress | SAME | 0.180000 | 0.130000 |
| 36 | SOC-CI-06 | cloud_infrastructure | monitor | monitor | monitor | SAME | 0.112000 | 0.130000 |

## Summary

Total: 36
MATCH: 36
FLIP: 0
Flips TO expected: 0
Flips FROM expected: 0
Flips between non-expected: 0
## Flip analysis

There are no flips to analyze. All 36 current winners equal the proposed
winners, and every winner remains equal to the scenario's expected action.
The proposed changes therefore do not alter bootstrap action selection under
the supplied squared-L2 scoring model.

The smallest current margin is `0.020000` for `SOC-TI-01` (malware execution,
escalate). Its proposed margin increases to `0.092500`, so the closest case
does not become less separated. Other near-boundary cases also remain stable;
`SOC-CA-05`, `SOC-DE-05`, and `SOC-IT-02` retain their expected winners.

## Recommendation

**Proceed to domain review, not direct production replacement.** The proposed
values are behaviorally safe in this bootstrap comparison: they preserve all
36 expected actions and do not introduce an action flip. This verifies only
the supplied Day-1 L2 model; it does not validate the semantic judgments or
future learned-centroid behavior.

Before implementation, retain the legacy fixture provenance, obtain SOC
analyst approval for the uncertain priors, and run the normal evaluation and
regression suites with the real scorer after any controlled fixture migration.

## Risk assessment

The worst observed case is not an action flip but the small current margin of
`SOC-TI-01`. It remains an escalation and gains separation under the proposed
values. The principal remaining risk is distributional: customer data could
move a learned centroid differently from this bootstrap snapshot, especially
for uncertain malware, lateral-movement, and cloud scenarios. The verification
script changes no production tensor or fixture data and should not be treated
as customer validation.





