# S2P score variance trace v1

## 1. Raw trace output

Ten sequential requests were sent to `POST http://127.0.0.1:8002/api/s2p/score`
after restarting the instrumented backend. Request payloads used
`category=price_variance`, `amount=1000`, `supplier_id=SUP-001`, and
`supplier_name=Test`. The HTTP measurements were:

```text
RUN 1 HTTP_TIME: 17.204784s
RUN 2 HTTP_TIME: 43.707851s
RUN 3 HTTP_TIME: 2.601233s
RUN 4 HTTP_TIME: 3.631207s
RUN 5 HTTP_TIME: 23.501061s
RUN 6 HTTP_TIME: 1.360035s
RUN 7 HTTP_TIME: 3.392288s
RUN 8 HTTP_TIME: 4.086368s
RUN 9 HTTP_TIME: 2.764117s
RUN 10 HTTP_TIME: 2.695241s
```

The backend emitted one `TRACE score step=...` line for every instrumented
step and one `TRACE score TOTAL=...` line per request. The resulting raw
step durations, in emission order, are preserved below in the complete
per-run table; the backend capture was saved during the run as
`.codex_tmp/s2p_score_trace_backend.out.log`.

## 2. Per-run timing table

All values are seconds. `mutation_lock_wait` is the interval from scorer
acquisition through entry to the lock body; `mutation_lock_released` is the
interval after leaving the lock.

| Run | Total | validation | fixture | variant | graph_ctx | signal | factors | scorer_acq | lock_wait | scorer | conservation | centroid | invalidation | lock_release | auto_approve | enrichment | link | side | response |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 16.6690 | 0.0001 | 0.0099 | 0.0041 | 11.5784 | 1.6286 | 0.0037 | 0.0034 | 0.0075 | 0.5752 | 0.0027 | 0.0008 | 1.3796 | 0.0047 | 0.0005 | 0.0094 | 1.4548 | 0.0035 | 0.0020 |
| 2 | 43.6688 | 0.0000 | 0.0155 | 0.0040 | 0.3469 | 0.5108 | 0.0005 | 0.0004 | 0.0005 | 0.6499 | 0.0004 | 0.0004 | 11.4499 | 0.0006 | 0.0003 | 0.0005 | 30.6842 | 0.0029 | 0.0007 |
| 3 | 2.5796 | 0.0000 | 0.0016 | 0.0003 | 0.3130 | 0.1232 | 0.0006 | 0.0004 | 0.0003 | 0.1776 | 0.0004 | 0.0003 | 1.4240 | 0.0055 | 0.0008 | 0.0007 | 0.5284 | 0.0007 | 0.0010 |
| 4 | 3.5930 | 0.0000 | 0.0035 | 0.0007 | 0.3827 | 0.2141 | 0.0027 | 0.0038 | 0.0011 | 0.4380 | 0.0007 | 0.0006 | 1.2477 | 0.0140 | 0.0005 | 0.0014 | 1.2748 | 0.0032 | 0.0025 |
| 5 | 23.4424 | 0.0000 | 0.0029 | 0.0031 | 10.4390 | 10.7258 | 0.0005 | 0.0004 | 0.0003 | 0.4518 | 0.0022 | 0.0009 | 0.5495 | 0.0066 | 0.0160 | 0.0114 | 1.2184 | 0.0104 | 0.0025 |
| 6 | 1.3367 | 0.0000 | 0.0026 | 0.0005 | 0.2370 | 0.1525 | 0.0005 | 0.0003 | 0.0003 | 0.2626 | 0.0006 | 0.0004 | 0.2957 | 0.0005 | 0.0002 | 0.0002 | 0.3804 | 0.0009 | 0.0008 |
| 7 | 3.1578 | 0.0000 | 0.0159 | 0.0176 | 0.4242 | 0.2011 | 0.0026 | 0.0011 | 0.0006 | 0.6049 | 0.0174 | 0.0053 | 1.0679 | 0.0163 | 0.0050 | 0.0016 | 0.7745 | 0.0007 | 0.0008 |
| 8 | 3.8813 | 0.0000 | 0.0258 | 0.0117 | 0.4879 | 0.2780 | 0.0009 | 0.0015 | 0.0002 | 0.7420 | 0.0114 | 0.0052 | 1.7595 | 0.0059 | 0.0011 | 0.0017 | 0.5471 | 0.0005 | 0.0005 |
| 9 | 2.7005 | 0.0000 | 0.0295 | 0.0047 | 0.4223 | 0.4434 | 0.0052 | 0.0156 | 0.0007 | 0.6179 | 0.0006 | 0.0005 | 0.6374 | 0.0005 | 0.0002 | 0.0003 | 0.5199 | 0.0007 | 0.0006 |
| 10 | 2.5739 | 0.0000 | 0.0019 | 0.0005 | 0.3554 | 0.3061 | 0.0087 | 0.0004 | 0.0003 | 0.4689 | 0.0007 | 0.0008 | 0.9023 | 0.0102 | 0.0008 | 0.0010 | 0.5147 | 0.0005 | 0.0005 |
| Average | 10.3603 | 0.0000 | 0.0109 | 0.0047 | 2.4987 | 1.4584 | 0.0026 | 0.0027 | 0.0012 | 0.4989 | 0.0037 | 0.0015 | 2.0714 | 0.0065 | 0.0025 | 0.0028 | 3.7897 | 0.0024 | 0.0012 |

## 3. Variance analysis

The two cold-start candidates are not both dominated by the same one-time
initialization. Run 1 is dominated by graph context resolution (11.5784s),
while run 2 is dominated by score invalidation (11.4499s) and invoice-link
work (30.6842s). This is operational/backend variance rather than a single
lazy scorer construction cost.

Runs 3–10 are nominally warm, but their totals still range from 1.3367s to
23.4424s. The warm spike in run 5 is caused by graph context resolution
(10.4390s) plus cross-copilot signal retrieval (10.7258s). The remaining
warm runs range from 1.3367s to 3.8813s.

The largest contributors to the observed spread are:

1. `invoice_link_check_or_create`: 30.6842s in run 2, versus 0.3804–1.4548s
   in the other runs. This is the single largest spike.
2. `graph_context_resolution`: 11.5784s in run 1 and 10.4390s in run 5,
   versus 0.2370–0.4879s in the other runs.
3. `score_invalidation_event`: 11.4499s in run 2, and 0.2957–1.7595s in
   the other runs. `cross_copilot_signal` also spikes to 10.7258s in run 5.

The scorer itself is comparatively stable at 0.1776–0.7420s in this run.
Lock wait is negligible (0.0002–0.0075s), so mutation-lock contention is not
the source of these sequential-request spikes.

## 4. Comparison to previous trace

The pre-S4 score trace reported `pre_score_enrichment` at 0.163–0.296s,
`invoice_link` at 0.191–0.350s, and
`cache_centroid_invalidation` at 0.159–0.222s.

Those ranges do not hold for this trace:

- The broken-out pre-score components are usually small, but
  `graph_context_resolution` reaches 11.5784s and `cross_copilot_signal`
  reaches 10.7258s.
- `invoice_link_check_or_create` reaches 30.6842s, far outside the former
  0.191–0.350s range.
- `score_invalidation_event` reaches 11.4499s, far outside the former
  0.159–0.222s cache range.

The previous warm trace therefore measured normal runs but did not expose the
backend stalls visible here.

## 5. Recommendation

The first stabilization target should be the graph-backed invoice link path,
because it produced the largest individual stall. Graph context resolution
and cross-copilot signal retrieval should be measured at their underlying
query/connection boundaries next; their spikes co-occur in run 5. Cache
invalidation should likewise be split into its individual cache operations,
because the aggregate invalidation marker reached 11.4499s.

A warm-up can reduce ordinary first-request setup, but it will not eliminate
this variance: the largest stalls occurred on different runs and different
steps, including warm run 5. The data supports stabilizing or bounding these
graph/cache reads and writes before changing scorer logic. No optimization was
made as part of this diagnostic.
