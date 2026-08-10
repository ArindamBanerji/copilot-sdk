# C9B SOC L5 Formal Proof Report

**Status: PASSED**  
**Graph:** `soc_graph_c9b`  
**Execution:** one uninterrupted route-run process, 250 valid SOC
score/outcome loops  
**Evidence source:** AGE readback after the proof process completed

## Scope

C9B closes the three SOC L5 cells left after C9A:

1. `L5Centroid`
2. `L5DKWeight`
3. `L5ConservationState`

The execution plan defines these as the SOC x 3 cells at
`copilot-sdk/docs/dk_runtime_execution_plan_v6_8.md:2751-2759`. The live
runner reads all three labels and their required edges at
`gen-ai-roi-demo-v4-v50/scripts/soc_c9b_live_age_smoke.py:130-220`.

## Proof execution

The fresh graph was dropped and recreated, then seeded with 300 deterministic
`C9B-DK-*` alerts. DK-proof mode forces all seed alerts into
`credential_access`; the seed mode is implemented at
`gen-ai-roi-demo-v4-v50/scripts/soc_c9b_seed_alerts.py:69-81` and
`gen-ai-roi-demo-v4-v50/scripts/soc_c9b_seed_alerts.py:118-143`.

The proof process was run with SOC learning enabled, AGE backend, graph
`soc_graph_c9b`, and 250 loops. The runner completed with exit code 0. The
runner's route path is `POST /api/alert/analyze` followed by
`POST /api/alert/outcome`, as implemented at
`gen-ai-roi-demo-v4-v50/scripts/soc_c9b_live_age_smoke.py:270-327`.

## AGE readback

| Cell / invariant | Observed value | Expected value | Result |
|---|---:|---:|---|
| `L5Centroid` nodes for `soc` | 1 | > 0 | PASS |
| `L5DKWeight` nodes for `soc` | 1 | > 0 | PASS |
| `L5ConservationState` nodes for `soc` | 1, status `GREEN` | > 0 with valid status | PASS |
| `SHAPED_BY` edges for `soc` | 1 | > 0 | PASS |
| Welford fields on `L5DKWeight` | all six present | all six present | PASS |
| SOC decisions | 250 | >= 250 | PASS |
| DK decisions used | 250 | >= 250 | PASS |
| Confirmed outcomes | 250 | 250 | PASS |
| Overridden outcomes | 0 | recorded | PASS |

The final AGE readback returned:

```json
{
  "L5Centroid": {"soc": 1},
  "L5DKWeight": {"soc": 1},
  "L5ConservationState": {"soc": {"count": 1, "status": "GREEN"}},
  "SHAPED_BY": {"soc": 1},
  "Welford": {
    "soc": {
      "present": true,
      "fields": {
        "confirmed_mean": true,
        "confirmed_m2": true,
        "overridden_mean": true,
        "overridden_m2": true,
        "all_mean": true,
        "all_m2": true
      }
    }
  },
  "decisions": {"soc": 250},
  "dk_weight": {"n_decisions_used": 250, "n_confirmed": 250, "n_overridden": 0}
}
```

## Computed-value checks

The conservation readback was:

```text
V = 249
alpha = 0.1667
q = 1.0
categories_total = 6
categories_with_data = 1
theta_min = 0.566988
status = GREEN
```

The expected signal is `alpha * q * V`:

```text
0.1667 * 1.0 * 249 = 41.5083
```

The observed state is therefore populated and internally coherent: one
category has data, all 249 verified outcomes are correct, and the state is
`GREEN`. The runner explicitly rejects missing/non-finite conservation inputs
at `gen-ai-roi-demo-v4-v50/scripts/soc_c9b_live_age_smoke.py:196-231`.

The DK expectation is a learned weight with at least 200 decisions in one
category. The final `L5DKWeight` reports `n_decisions_used=250`, with all six
Welford mean/M2 fields present, satisfying the requirement described at
`copilot-sdk/docs/dk_runtime_execution_plan_v6_8.md:833-921`.

## C9B closure

**C9B: PASSED.** The three SOC cells are present on the fresh
`soc_graph_c9b`, populated by the live route path, and the DK/Welford and
conservation readbacks satisfy their formal predicates. Combined with C9A's
12 cells, the repository now has evidence for all 15 L5 cells.

## Caveat

The production SOC startup guard still requires the shared production graph
`soc_graph`; this proof used the repository's test-mode configuration to run
the same route path against the disposable proof graph. The guard is defined
at `copilot-sdk/copilot_sdk/config/graph_config.py:26-49` and was not changed.
