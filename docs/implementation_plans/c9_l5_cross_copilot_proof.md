# C9 L5 Cross-Copilot Proof

## Executive verdict

- C9 verdict: PASS
- Scope: 4 non-SOC domains
- SOC: #132 gap
- Proof source: `docs/implementation_plans/c9_live_age_readback_final.json`
- AGE graph: `soc_graph`
- DSN: `postgresql://postgres:***@localhost:5433/soc_copilot`
- Readback verdict from source JSON: `READY_FOR_C9_RERUN`
- Missing cells from source JSON: `[]`

## C9 pass criteria

C9 v5.4 requires 4 non-SOC domains x 3 L5 node types = 12 cells:

- Required domains: `trading`, `purchasing`, `dataops`, `s2p`
- Required node type: `L5Centroid`
- Required node type: `L5DKWeight` with Welford state
- Required node type: `L5ConservationState`
- Required edge proof: `SHAPED_BY`
- Transition-dependent edge proof: `TRIGGERED_BY`
- SOC is excluded from this pass and remains tracked as #132.

`TRIGGERED_BY` is not required unless a conservation status transition is exercised. In this readback, all current conservation states are `GREEN`, and the transition classification is `transition not exercised`.

## 12-cell matrix

| Domain | L5Centroid | L5DKWeight | L5ConservationState | Welford | SHAPED_BY | TRIGGERED_BY | Verdict |
| --- | ---: | ---: | --- | --- | ---: | --- | --- |
| trading | 4 | 1 | 1, `GREEN` | present, six fields | 4 | transition not exercised | PASS |
| purchasing | 4 | 1 | 1, `GREEN` | present, six fields | 4 | transition not exercised | PASS |
| dataops | 4 | 1 | 1, `GREEN` | present, six fields | 4 | transition not exercised | PASS |
| s2p | 2 | 1 | 1, `GREEN` | present, six fields | 2 | transition not exercised | PASS |

## L5Centroid proof

Counts by domain:

| Domain | L5Centroid count |
| --- | ---: |
| trading | 4 |
| purchasing | 4 |
| dataops | 4 |
| s2p | 2 |

Sample rows from live AGE readback:

| Domain | Category | Action | Caused by decision | Delta norm |
| --- | --- | --- | --- | ---: |
| dataops | pipeline_failure | auto_approve | DEC-240a3832 | 0.010215567860863481 |
| dataops | pipeline_failure | investigate | DEC-277ca601 | 0.010651636085898936 |
| dataops | schema_change | investigate | DEC-b16ee667 | 0.010997018164898982 |
| dataops | schema_change | refer_to_specialist | DEC-9a5d95b3 | 0.012247448713915901 |
| purchasing | protein | order_as_planned | DEC-ac0cc8c7 | 0.013228756555322966 |
| purchasing | protein | order_less | DEC-1c8c34d2 | 0.013228756555322966 |
| purchasing | protein | order_more | DEC-7c22b77d | 0.009978709681863679 |
| purchasing | protein | skip | DEC-dd2f5037 | 0.009549171538719826 |
| s2p | price_variance | flag_leakage | DEC-942a8cc7 | 0.013228756555322964 |
| s2p | price_variance | refer_to_specialist | DEC-5946ab80 | 0.008674267847339545 |
| trading | trend_following | partial_execution | DEC-19c80205 | 0.009298828335305223 |
| trading | trend_following | poor_execution | DEC-1b816e1c | 0.01581138830084191 |
| trading | trend_following | skip_recommended | DEC-6730d55b | 0.010000000000000009 |
| trading | trend_following | strong_execution | DEC-99730a3f | 0.01581138830084191 |

## L5DKWeight + Welford proof

Counts by domain:

| Domain | L5DKWeight count | DK weight id | n_decisions_used | n_confirmed | n_overridden |
| --- | ---: | --- | ---: | ---: | ---: |
| trading | 1 | trading:dkw:a25a79d42cfc | 280 | 280 | 0 |
| purchasing | 1 | purchasing:dkw:266fdfe9bc29 | 210 | 210 | 0 |
| dataops | 1 | dataops:dkw:d4d5f5cc93a3 | 210 | 210 | 0 |
| s2p | 1 | s2p:dkw:6f5e5c6010ad | 210 | 210 | 0 |

Welford field presence:

| Domain | all_mean | all_m2 | confirmed_mean | confirmed_m2 | overridden_mean | overridden_m2 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| trading | 1 | 1 | 1 | 1 | 1 | 1 |
| purchasing | 1 | 1 | 1 | 1 | 1 | 1 |
| dataops | 1 | 1 | 1 | 1 | 1 | 1 |
| s2p | 1 | 1 | 1 | 1 | 1 | 1 |

The DK runtime claim is proven for the four non-SOC domains by current-state `L5DKWeight` nodes with Welford state populated.

## L5ConservationState proof

Counts and current state by domain:

| Domain | Count | Status | Old status | Caused by decision | Updated at |
| --- | ---: | --- | --- | --- | --- |
| trading | 1 | GREEN | GREEN | DEC-55824c0b | 2026-06-07T15:39:04.765419Z |
| purchasing | 1 | GREEN | GREEN | DEC-1c8c34d2 | 2026-06-07T16:49:42.146736Z |
| dataops | 1 | GREEN | GREEN | DEC-b16ee667 | 2026-06-07T16:39:53.968693Z |
| s2p | 1 | GREEN | GREEN | DEC-5946ab80 | 2026-06-07T16:50:02.676066Z |

All four non-SOC domains have `L5ConservationState` readback in live AGE.

## Edge proof

`SHAPED_BY` counts by domain:

| Domain | SHAPED_BY count |
| --- | ---: |
| trading | 4 |
| purchasing | 4 |
| dataops | 4 |
| s2p | 2 |

`TRIGGERED_BY` counts by domain:

| Domain | TRIGGERED_BY count | Classification |
| --- | ---: | --- |
| trading | 0 | transition not exercised |
| purchasing | 0 | transition not exercised |
| dataops | 0 | transition not exercised |
| s2p | 0 | transition not exercised |

The `TRIGGERED_BY` edge is transition-dependent under v5.4. The live proof does not fail on zero `TRIGGERED_BY` edges because current conservation states stayed `GREEN`; no status transition was exercised.

## Decision status context

Live AGE decision status counts from the readback:

| Domain | Status | Count |
| --- | --- | ---: |
| dataops | confirmed | 221 |
| dataops | null | 1 |
| purchasing | confirmed | 228 |
| purchasing | pending | 1 |
| purchasing | null | 1 |
| s2p | confirmed | 215 |
| s2p | null | 1 |
| trading | confirmed | 351 |
| trading | null | 1 |
| null | null | 4862 |

The null-status decision rows are historical residuals from earlier live graph state and are not part of the new-write C9 proof. One purchasing pending decision remains from an earlier timed-out run and is not part of the completed C9 proof cells.

## Product-claim status

- 288-moat claim: PROVEN for 4 non-SOC SDK/S2P domains; SOC pending #132.
- Mirror learned-insight claim: PROVEN for 4 non-SOC domains through live `L5Centroid` and `SHAPED_BY` readback.
- Trust-trap discovery / DK runtime claim: PROVEN for 4 non-SOC domains through live `L5DKWeight` and Welford readback.
- Compounding intelligence: PROVEN for 4 non-SOC domains through live centroid, DK, conservation, and edge readback.
- SOC conservation claim: NOT PART OF THIS C9 PASS; #132 gap.

## Residuals

- SOC remains #132 gap.
- `TRIGGERED_BY` needs transition-specific proof if a future milestone requires transition edge evidence.
- Old status-null `Decision` nodes remain a historical cleanup/migration item.
- One purchasing pending decision remains from an earlier timed-out run.
- Multi-process tracker coordination remains future hardening.

## Final next step

C9 PASS for the non-SOC SDK/S2P scope. The next roadmap item can proceed according to v5.4, with SOC/#132 tracked separately.

