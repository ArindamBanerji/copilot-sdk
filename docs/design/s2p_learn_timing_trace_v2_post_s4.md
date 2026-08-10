# S2P Learn Timing Trace v2 — Post-S4

Diagnostic-only trace captured after S4. Temporary instrumentation was removed
from `s2p-copilot/backend/app/routers/s2p.py` and
`copilot_sdk/scoring/persistence_outbox.py` before verification.

## 1. Raw trace output

Five valid `price_variance` score→learn pairs were run with supplier
`SUP-001` / `PerfTest`, amount `1000.0`. The trace below retains the timing
markers and omits unrelated `SHAPED_BY` warnings.

```text
HTTP score run=1 status=200 dt=0.9252s
learn 1: decision_read .0607; pre_centroid_read .0001; pre_conservation_snapshot .0001; pre_outcome_evidence .1087; scorer_decision_read .0151; scorer_invoice_link_check .3237; scorer_context_derivation .0001; scorer_graph_link_setup .0001; scorer_learn 2.1612; scorer_graph_link_restore .0000; learn_with_scorer .0001; cache_clear .0000; enqueue_centroid_done .0103; enqueue_conservation_done .7846; enqueue_dk_done .0099; learn_preview_invalidation .2340; after_conservation_snapshot .5678; mutation_lock_released .0001; outcome_receipt .0003; supplier_profile .0001; evolver_outcome .0000; shadow_outcome .0000; response_construction .0000; TOTAL 4.2773s
HTTP learn run=1 status=200 dt=4.2830s

HTTP score run=2 status=200 dt=1.0110s
learn 2: decision_read .0404; pre_centroid_read .0001; pre_conservation_snapshot .0001; pre_outcome_evidence .2236; scorer_decision_read .0219; scorer_invoice_link_check .3919; scorer_context_derivation .0001; scorer_graph_link_setup .0002; scorer_learn 3.0373; scorer_graph_link_restore .0001; learn_with_scorer .0001; cache_clear .0001; enqueue_centroid_done .0120; enqueue_conservation_done 1.0937; enqueue_dk_done .0107; learn_preview_invalidation .3675; after_conservation_snapshot .7029; mutation_lock_released .0002; outcome_receipt .0000; supplier_profile .0001; evolver_outcome .0000; shadow_outcome .0000; response_construction .0000; TOTAL 5.9030s
HTTP learn run=2 status=200 dt=5.9077s

HTTP score run=3 status=200 dt=1.1833s
learn 3: decision_read .0824; pre_centroid_read .0001; pre_conservation_snapshot .0001; pre_outcome_evidence .2236; scorer_decision_read .0194; scorer_invoice_link_check .3679; scorer_context_derivation .0001; scorer_graph_link_setup .0002; scorer_learn 2.5181; scorer_graph_link_restore .0001; learn_with_scorer .0001; cache_clear .0000; enqueue_centroid_done .0101; enqueue_conservation_done .9623; enqueue_dk_done .0097; learn_preview_invalidation .2859; after_conservation_snapshot .6942; mutation_lock_released .0001; outcome_receipt .0000; supplier_profile .0001; evolver_outcome .0000; shadow_outcome .0000; response_construction .0000; TOTAL 5.1746s
HTTP learn run=3 status=200 dt=5.1795s

HTTP score run=4 status=200 dt=1.3490s
learn 4: decision_read .1582; pre_centroid_read .0001; pre_conservation_snapshot .0001; pre_outcome_evidence .1864; scorer_decision_read .1444; scorer_invoice_link_check .4556; scorer_context_derivation .0001; scorer_graph_link_setup .0002; scorer_learn 3.4531; scorer_graph_link_restore .0001; learn_with_scorer .0001; cache_clear .0001; enqueue_centroid_done .0113; enqueue_conservation_done .9912; enqueue_dk_done .0138; learn_preview_invalidation .2942; after_conservation_snapshot .7283; mutation_lock_released .0002; outcome_receipt .0008; supplier_profile .0001; evolver_outcome .0000; shadow_outcome .0000; response_construction .0000; TOTAL 6.4386s
HTTP learn run=4 status=200 dt=6.4449s

HTTP score run=5 status=200 dt=1.1228s
learn 5: decision_read .0261; pre_centroid_read .0002; pre_conservation_snapshot .0001; pre_outcome_evidence .1602; scorer_decision_read .1155; scorer_invoice_link_check .4575; scorer_context_derivation .0001; scorer_graph_link_setup .0002; scorer_learn 3.0441; scorer_graph_link_restore .0001; learn_with_scorer .0001; cache_clear .0001; enqueue_centroid_done .0090; enqueue_conservation_done .8966; enqueue_dk_done .0458; learn_preview_invalidation .3048; after_conservation_snapshot .6132; mutation_lock_released .0002; outcome_receipt .0000; supplier_profile .0001; evolver_outcome .0000; shadow_outcome .0000; response_construction .0000; TOTAL 5.6741s
HTTP learn run=5 status=200 dt=5.6777s

TRACE periodic_drain START pending=781
```

The periodic drain marker occurred during learn run 1, after preview
invalidation and before the after-conservation snapshot. No matching DONE
marker appeared before the TestClient process exited. A first capture from the
same environment showed `pending=928`.

Payload sizes and direct enqueue durations:

| Artifact | Payload bytes | Direct enqueue average |
|---|---:|---:|
| `l5_centroid` | 265–322 | 0.0105s |
| `l5_conservation` | 318–319 | 0.0222s |
| `dk_weights` | 1026–1169 | 0.0163s |

## 2. Post-S4 timing table

Intervals are seconds; `TOTAL` uses the cumulative marker.

| Step | Run 1 | Run 2 | Run 3 | Run 4 | Run 5 | Avg |
|---|---:|---:|---:|---:|---:|---:|
| validation_context_scorer | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| mutation_lock_acquired | 0.0000 | 0.0000 | 0.0000 | 0.0001 | 0.0000 | 0.0000 |
| decision_read | 0.0607 | 0.0404 | 0.0824 | 0.1582 | 0.0261 | 0.0736 |
| pre_centroid_read | 0.0001 | 0.0001 | 0.0001 | 0.0001 | 0.0002 | 0.0001 |
| pre_conservation_snapshot | 0.0001 | 0.0001 | 0.0001 | 0.0001 | 0.0001 | 0.0001 |
| pre_outcome_evidence | 0.1087 | 0.2236 | 0.2236 | 0.1864 | 0.1602 | 0.1805 |
| scorer_decision_read | 0.0151 | 0.0219 | 0.0194 | 0.1444 | 0.1155 | 0.0633 |
| scorer_invoice_link_check | 0.3237 | 0.3919 | 0.3679 | 0.4556 | 0.4575 | 0.3993 |
| scorer_context_derivation | 0.0001 | 0.0001 | 0.0001 | 0.0001 | 0.0001 | 0.0001 |
| scorer_graph_link_setup | 0.0001 | 0.0002 | 0.0002 | 0.0002 | 0.0002 | 0.0002 |
| scorer_learn | 2.1612 | 3.0373 | 2.5181 | 3.4531 | 3.0441 | 2.8428 |
| scorer_graph_link_restore | 0.0000 | 0.0001 | 0.0001 | 0.0001 | 0.0001 | 0.0001 |
| cache_clear | 0.0000 | 0.0001 | 0.0000 | 0.0001 | 0.0001 | 0.0001 |
| enqueue_centroid handler window | 0.0103 | 0.0120 | 0.0101 | 0.0113 | 0.0090 | 0.0105 |
| enqueue_conservation handler window | 0.7846 | 1.0937 | 0.9623 | 0.9912 | 0.8966 | 0.9457 |
| enqueue_dk handler window | 0.0099 | 0.0107 | 0.0097 | 0.0138 | 0.0458 | 0.0180 |
| learn_preview_invalidation | 0.2340 | 0.3675 | 0.2859 | 0.2942 | 0.3048 | 0.2973 |
| after_conservation_snapshot | 0.5678 | 0.7029 | 0.6942 | 0.7283 | 0.6132 | 0.6613 |
| mutation_lock_released | 0.0001 | 0.0002 | 0.0001 | 0.0002 | 0.0002 | 0.0002 |
| outcome_receipt | 0.0003 | 0.0000 | 0.0000 | 0.0008 | 0.0000 | 0.0002 |
| supplier_profile | 0.0001 | 0.0001 | 0.0001 | 0.0001 | 0.0001 | 0.0001 |
| evolver_outcome | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| shadow_outcome | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| response_construction | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| TOTAL | 4.2773 | 5.9030 | 5.1746 | 6.4386 | 5.6741 | 5.4935 |

## 3. Side-by-side comparison with pre-S4

Pre-S4 averages come from `s2p_learn_timing_trace_v1.md`.

| Step | Pre-S4 avg | Post-S4 avg | Delta |
|---|---:|---:|---:|
| decision_read | 0.0308 | 0.0736 | +0.0428 |
| pre_centroid_read | 0.0009 | 0.0001 | -0.0008 |
| pre_conservation_snapshot | 0.1299 | 0.0001 | -0.1298* |
| pre_outcome_evidence | 0.1097 | 0.1805 | +0.0708 |
| scorer_decision_read | 0.0149 | 0.0633 | +0.0484 |
| scorer_invoice_link_check | 0.3115 | 0.3993 | +0.0878 |
| scorer_context_derivation | 0.0008 | 0.0001 | -0.0007 |
| scorer_graph_link_setup | 0.0004 | 0.0002 | -0.0002 |
| scorer_learn | 2.0295 | 2.8428 | +0.8133 |
| cache_clear | 0.0003 | 0.0001 | -0.0002 |
| L5 centroid / enqueue | 0.1735 | 0.0105 | -0.1630 |
| L5 conservation / enqueue | 0.7507 | 0.0222 direct; 0.9457 handler window | -0.7285 direct; +0.1950 window |
| L5 DK / enqueue | 0.0388 | 0.0163 | -0.0225 |
| learn_preview_invalidation | 0.2247 | 0.2973 | +0.0726 |
| after_conservation_snapshot | 0.5247 | 0.6613 | +0.1366 |
| TOTAL | 4.3448 | 5.4935 | +1.1487 |

\* The pre-S4 first-run cache miss made this comparison nonstationary; the
post-S4 trace had a warm cache for this step.

## 4. Regression analysis

The expected 0.96s saving was not realized because S4 deferred only the final
durable writes. The conservation path still performs
`compute_conservation_metrics()` and `get_conservation_state()` synchronously
before constructing the payload. That handler window averaged 0.9457s, even
though the direct SQLite enqueue calls were generally only 9–22ms.

The larger unexpected regression is contention. `scorer_learn` increased by
0.8133s on average and varied from 2.1612s to 3.4531s. A periodic drain began
inside run 1 with 781 pending rows and had not completed when the process
ended. The drain replays rows serially through graph-store writes and updates
the same SQLite outbox, so it can compete with active learning and graph
operations. The previous capture also observed 928 pending rows.

Other slower steps were `after_conservation_snapshot` (+0.1366s), invoice-link
checking (+0.0878s), preview invalidation (+0.0726s), and evidence (+0.0708s).
These are consistent with shared graph/SQLite contention, but the trace does
not prove a single causal lock for each one.

## 5. Hypothesis verdicts

- H1 — rejected. Direct enqueue was approximately 9–22ms, with one 80.4ms
  contended conservation outlier; DK averaged approximately 16ms. The three
  calls are not a multi-second cost.
- H2 — partially confirmed, not primary. The after-conservation snapshot
  increased from 0.5247s to 0.6613s, but did not exceed 1s and explains only
  about 0.14s.
- H3 — confirmed as an active risk and likely major contributor. A periodic
  drain ran during learn with 781 pending rows and did not finish in the
  capture window. `scorer_learn` was the largest positive delta.
- H4 — rejected as stated. `cache_clear` remained effectively unchanged at
  approximately 0.1–0.3ms. The trace instead shows the conservation payload
  preparation still running inline.
- H5 — rejected. Payloads were small: centroid 265–322 bytes, conservation
  318–319 bytes, DK 1026–1169 bytes. Serialization is not the cause.

## 6. Recommendation

Diagnostic recommendation only: first prevent a large backlog drain from
running concurrently with request-critical scorer/graph work, and establish a
bounded drain/backpressure policy. Then profile the conservation payload
preparation separately from the enqueue. To obtain the planned latency saving,
the expensive derived conservation computation/read must not remain on the
request path; it needs a worker-safe snapshot/event design or equivalent
background derivation. The actual SQLite enqueue path does not need
optimization based on this trace.

## Verification

- Temporary instrumentation removed: YES.
- Source scan for `TRACE learn`, `TRACE outbox enqueue`, `TRACE periodic_drain`,
  and `trace_mark`: no matches.
- Outbox mypy: PASS.
- Router mypy: only the two pre-existing endpoint `no-any-return` errors.
- Requested `pytest -k "score_endpoint or learn"`: did not complete; it timed
  out after about 92s with four failures visible and a stuck TestClient/thread
  stack. No timing markers were present during this verification run.
