# S2P Learn Timing Trace v1

Diagnostic trace captured from a fresh S2P backend process on 2026-08-02. The
temporary markers were added to the S2P score route (`s2p-copilot/backend/app/routers/s2p.py:1895-2032`),
the learn route (`:2091-2189`), and `_learn_with_scorer` (`:1577-1643`), then
removed before verification. The warm-up score is included in the raw trace
but excluded from the three-run score averages.

## 1. Raw TRACE output

```text
TRACE score step=validation_event dt=0.0001s cumulative=0.0001s
TRACE score step=pre_score_enrichment dt=0.5967s cumulative=0.5968s
TRACE score step=mutation_lock_acquired dt=0.0023s cumulative=0.5991s
TRACE score step=scorer_score dt=0.0992s cumulative=0.6983s
TRACE score step=cache_centroid_invalidation dt=0.1726s cumulative=0.8709s
TRACE score step=mutation_lock_released dt=0.0073s cumulative=0.8781s
TRACE score step=auto_approve dt=0.0019s cumulative=0.8801s
TRACE score step=derived_enrichment dt=0.0012s cumulative=0.8812s
TRACE score step=invoice_link dt=0.2477s cumulative=1.1290s
TRACE score step=side_effect_submit dt=0.0005s cumulative=1.1295s
TRACE score step=response dt=0.0005s cumulative=1.1300s
TRACE score TOTAL=1.1302s
TRACE score step=validation_event dt=0.0000s cumulative=0.0000s
TRACE score step=pre_score_enrichment dt=0.1632s cumulative=0.1633s
TRACE score step=mutation_lock_acquired dt=0.0004s cumulative=0.1637s
TRACE score step=scorer_score dt=0.0862s cumulative=0.2499s
TRACE score step=cache_centroid_invalidation dt=0.1586s cumulative=0.4085s
TRACE score step=mutation_lock_released dt=0.0003s cumulative=0.4088s
TRACE score step=auto_approve dt=0.0001s cumulative=0.4089s
TRACE score step=derived_enrichment dt=0.0002s cumulative=0.4091s
TRACE score step=invoice_link dt=0.1910s cumulative=0.6001s
TRACE score step=side_effect_submit dt=0.0005s cumulative=0.6006s
TRACE score step=response dt=0.0003s cumulative=0.6009s
TRACE score TOTAL=0.6010s
TRACE learn step=validation_context_scorer dt=0.0000s cumulative=0.0000s
TRACE learn step=mutation_lock_acquired dt=0.0003s cumulative=0.0003s
TRACE learn step=decision_read dt=0.0617s cumulative=0.0620s
TRACE learn step=pre_centroid_read dt=0.0018s cumulative=0.0638s
TRACE learn step=pre_conservation_snapshot dt=0.3890s cumulative=0.4528s
TRACE learn step=pre_outcome_evidence dt=0.0918s cumulative=0.5446s
TRACE learn step=scorer_decision_read dt=0.0111s cumulative=0.5557s
TRACE learn step=scorer_invoice_link_check dt=0.2842s cumulative=0.8399s
TRACE learn step=scorer_context_derivation dt=0.0004s cumulative=0.8403s
TRACE learn step=scorer_graph_link_setup dt=0.0004s cumulative=0.8407s
TRACE learn step=scorer_learn dt=2.1515s cumulative=2.9922s
TRACE learn step=scorer_graph_link_restore dt=0.0005s cumulative=2.9927s
TRACE learn step=learn_with_scorer dt=0.0005s cumulative=2.9932s
TRACE learn step=cache_clear dt=0.0004s cumulative=2.9937s
TRACE learn step=l5_centroid dt=0.2115s cumulative=3.2051s
TRACE learn step=l5_conservation dt=0.7617s cumulative=3.9668s
TRACE learn step=l5_dk dt=0.0468s cumulative=4.0136s
TRACE learn step=learn_preview_invalidation dt=0.2212s cumulative=4.2348s
TRACE learn step=after_conservation_snapshot dt=0.5263s cumulative=4.7611s
TRACE learn step=mutation_lock_released dt=0.0004s cumulative=4.7615s
TRACE learn step=outcome_receipt dt=0.0003s cumulative=4.7618s
TRACE learn step=supplier_profile dt=0.0008s cumulative=4.7626s
TRACE learn step=evolver_outcome dt=0.0004s cumulative=4.7631s
TRACE learn step=shadow_outcome dt=0.0003s cumulative=4.7633s
TRACE learn step=response_construction dt=0.0002s cumulative=4.7635s
TRACE learn TOTAL=4.7638s
TRACE score step=validation_event dt=0.0000s cumulative=0.0000s
TRACE score step=pre_score_enrichment dt=0.2957s cumulative=0.2957s
TRACE score step=mutation_lock_acquired dt=0.0004s cumulative=0.2960s
TRACE score step=scorer_score dt=0.1163s cumulative=0.4123s
TRACE score step=cache_centroid_invalidation dt=0.2164s cumulative=0.6287s
TRACE score step=mutation_lock_released dt=0.0017s cumulative=0.6304s
TRACE score step=auto_approve dt=0.0003s cumulative=0.6307s
TRACE score step=derived_enrichment dt=0.0003s cumulative=0.6310s
TRACE score step=invoice_link dt=0.3497s cumulative=0.9807s
TRACE score step=side_effect_submit dt=0.0004s cumulative=0.9811s
TRACE score step=response dt=0.0004s cumulative=0.9814s
TRACE score TOTAL=0.9816s
TRACE learn step=validation_context_scorer dt=0.0000s cumulative=0.0000s
TRACE learn step=mutation_lock_acquired dt=0.0004s cumulative=0.0005s
TRACE learn step=decision_read dt=0.0150s cumulative=0.0155s
TRACE learn step=pre_centroid_read dt=0.0005s cumulative=0.0159s
TRACE learn step=pre_conservation_snapshot dt=0.0003s cumulative=0.0163s
TRACE learn step=pre_outcome_evidence dt=0.1199s cumulative=0.1362s
TRACE learn step=scorer_decision_read dt=0.0183s cumulative=0.1545s
TRACE learn step=scorer_invoice_link_check dt=0.3347s cumulative=0.4892s
TRACE learn step=scorer_context_derivation dt=0.0004s cumulative=0.4895s
TRACE learn step=scorer_graph_link_setup dt=0.0004s cumulative=0.4899s
TRACE learn step=scorer_learn dt=2.0260s cumulative=2.5159s
TRACE learn step=scorer_graph_link_restore dt=0.0008s cumulative=2.5166s
TRACE learn step=learn_with_scorer dt=0.0004s cumulative=2.5170s
TRACE learn step=cache_clear dt=0.0003s cumulative=2.5173s
TRACE learn step=l5_centroid dt=0.1187s cumulative=2.6360s
TRACE learn step=l5_conservation dt=0.7758s cumulative=3.4118s
TRACE learn step=l5_dk dt=0.0337s cumulative=3.4456s
TRACE learn step=learn_preview_invalidation dt=0.2290s cumulative=3.6746s
TRACE learn step=after_conservation_snapshot dt=0.5648s cumulative=4.2394s
TRACE learn step=mutation_lock_released dt=0.0005s cumulative=4.2400s
TRACE learn step=outcome_receipt dt=0.0005s cumulative=4.2405s
TRACE learn step=supplier_profile dt=0.0003s cumulative=4.2407s
TRACE learn step=evolver_outcome dt=0.0002s cumulative=4.2410s
TRACE learn step=shadow_outcome dt=0.0002s cumulative=4.2412s
TRACE learn step=response_construction dt=0.0001s cumulative=4.2413s
TRACE learn TOTAL=4.2414s
TRACE score step=validation_event dt=0.0000s cumulative=0.0000s
TRACE score step=pre_score_enrichment dt=0.2484s cumulative=0.2484s
TRACE score step=mutation_lock_acquired dt=0.0005s cumulative=0.2489s
TRACE score step=scorer_score dt=0.1197s cumulative=0.3686s
TRACE score step=cache_centroid_invalidation dt=0.2223s cumulative=0.5908s
TRACE score step=mutation_lock_released dt=0.0005s cumulative=0.5913s
TRACE score step=auto_approve dt=0.0002s cumulative=0.5915s
TRACE score step=derived_enrichment dt=0.0003s cumulative=0.5919s
TRACE score step=invoice_link dt=0.2716s cumulative=0.8635s
TRACE score step=side_effect_submit dt=0.0004s cumulative=0.8639s
TRACE score step=response dt=0.0003s cumulative=0.8642s
TRACE score TOTAL=0.8645s
TRACE learn step=validation_context_scorer dt=0.0000s cumulative=0.0000s
TRACE learn step=mutation_lock_acquired dt=0.0004s cumulative=0.0004s
TRACE learn step=decision_read dt=0.0157s cumulative=0.0161s
TRACE learn step=pre_centroid_read dt=0.0004s cumulative=0.0165s
TRACE learn step=pre_conservation_snapshot dt=0.0003s cumulative=0.0168s
TRACE learn step=pre_outcome_evidence dt=0.1175s cumulative=0.1343s
TRACE learn step=scorer_decision_read dt=0.0152s cumulative=0.1495s
TRACE learn step=scorer_invoice_link_check dt=0.3155s cumulative=0.4650s
TRACE learn step=scorer_context_derivation dt=0.0017s cumulative=0.4667s
TRACE learn step=scorer_graph_link_setup dt=0.0005s cumulative=0.4672s
TRACE learn step=scorer_learn dt=1.9111s cumulative=2.3783s
TRACE learn step=scorer_graph_link_restore dt=0.0003s cumulative=2.3787s
TRACE learn step=learn_with_scorer dt=0.0002s cumulative=2.3789s
TRACE learn step=cache_clear dt=0.0002s cumulative=2.3791s
TRACE learn step=l5_centroid dt=0.1902s cumulative=2.5693s
TRACE learn step=l5_conservation dt=0.7147s cumulative=3.2839s
TRACE learn step=l5_dk dt=0.0359s cumulative=3.3198s
TRACE learn step=learn_preview_invalidation dt=0.2238s cumulative=3.5436s
TRACE learn step=after_conservation_snapshot dt=0.4831s cumulative=4.0267s
TRACE learn step=mutation_lock_released dt=0.0005s cumulative=4.0272s
TRACE learn step=outcome_receipt dt=0.0006s cumulative=4.0278s
TRACE learn step=supplier_profile dt=0.0004s cumulative=4.0283s
TRACE learn step=evolver_outcome dt=0.0003s cumulative=4.0286s
TRACE learn step=shadow_outcome dt=0.0003s cumulative=4.0289s
TRACE learn step=response_construction dt=0.0002s cumulative=4.0291s
TRACE learn TOTAL=4.0293s
```

## 2. Learn timing table

Runs are the three valid score→learn pairs. Categories follow the design
document's AUTH/DERIVED/SIDE/CACHE/LOCK classification. The
`learn_with_scorer` parent marker is a boundary marker and is not added to
the nested `_learn_with_scorer` rows or to the totals below.

| # | Step | Category | Run 1 (s) | Run 2 (s) | Run 3 (s) | Avg (s) |
|---:|---|---|---:|---:|---:|---:|
| 1 | validation_context_scorer | AUTH | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| 2 | mutation_lock_acquired | LOCK | 0.0003 | 0.0004 | 0.0004 | 0.0004 |
| 3 | decision_read | AUTH | 0.0617 | 0.0150 | 0.0157 | 0.0308 |
| 4 | pre_centroid_read | DERIVED | 0.0018 | 0.0005 | 0.0004 | 0.0009 |
| 5 | pre_conservation_snapshot | AUTH/AUDIT | 0.3890 | 0.0003 | 0.0003 | 0.1299 |
| 6 | pre_outcome_evidence | AUTH/AUDIT | 0.0918 | 0.1199 | 0.1175 | 0.1097 |
| 7a | scorer_decision_read | AUTH | 0.0111 | 0.0183 | 0.0152 | 0.0149 |
| 7b | scorer_invoice_link_check | AUTH guard | 0.2842 | 0.3347 | 0.3155 | 0.3115 |
| 7c | scorer_context_derivation | DERIVED | 0.0004 | 0.0004 | 0.0017 | 0.0008 |
| 7d | scorer_graph_link_setup | LOCK | 0.0004 | 0.0004 | 0.0005 | 0.0004 |
| 7e | scorer_learn | AUTH | 2.1515 | 2.0260 | 1.9111 | 2.0295 |
| 7f | scorer_graph_link_restore | LOCK | 0.0005 | 0.0008 | 0.0003 | 0.0005 |
| 7 | learn_with_scorer boundary | — | 0.0005 | 0.0004 | 0.0002 | 0.0004 |
| 8 | cache_clear | CACHE | 0.0004 | 0.0003 | 0.0002 | 0.0003 |
| 9 | l5_centroid | DERIVED | 0.2115 | 0.1187 | 0.1902 | 0.1735 |
| 10 | l5_conservation | DERIVED | 0.7617 | 0.7758 | 0.7147 | 0.7507 |
| 11 | l5_dk | DERIVED | 0.0468 | 0.0337 | 0.0359 | 0.0388 |
| 12 | learn_preview_invalidation | CACHE | 0.2212 | 0.2290 | 0.2238 | 0.2247 |
| 13 | after_conservation_snapshot | AUTH/AUDIT | 0.5263 | 0.5648 | 0.4831 | 0.5247 |
| 14 | mutation_lock_released | LOCK | 0.0004 | 0.0005 | 0.0005 | 0.0005 |
| 15 | outcome_receipt | AUTH/AUDIT | 0.0003 | 0.0005 | 0.0006 | 0.0005 |
| 16 | supplier_profile | SIDE | 0.0008 | 0.0003 | 0.0004 | 0.0005 |
| 17 | evolver_outcome | SIDE | 0.0004 | 0.0002 | 0.0003 | 0.0003 |
| 18 | shadow_outcome | SIDE | 0.0003 | 0.0002 | 0.0003 | 0.0003 |
| 19 | response_construction | AUTH | 0.0002 | 0.0001 | 0.0002 | 0.0002 |
| 20 | TOTAL | — | 4.7638 | 4.2414 | 4.0293 | 4.3448 |

The extra nested rows are the six requested `_learn_with_scorer` substeps;
the handler-level table has 18 logical stages when the parent boundary and
the response boundary are counted as the design document does.

## 3. Learn analysis

Using the observed average intervals and excluding the non-additive parent
boundary marker:

| Category | Average time |
|---|---:|
| AUTH/AUDIT and AUTH guards | 3.1517s |
| DERIVED | 0.9647s |
| SIDE | 0.0011s |
| CACHE | 0.2250s |
| LOCK | 0.0018s |
| Sum of measured categories | 4.3442s |

The small difference from the 4.3448s average total is rounding in the
printed four-decimal intervals. The AUTH-only theoretical minimum is about
3.15s under the current audit and duplicate-link requirements. This is a
floor for this trace, not a target guarantee: it assumes the required
authoritative reads/writes remain inline and excludes lock overhead and all
deferrable work.

Top three slowest learn steps:

1. `scorer_learn` — 2.0295s average — AUTH. This is the SDK authoritative
   learning operation at the S2P wrapper's call site (`s2p.py:1625-1630`).
2. `l5_conservation` — 0.7507s average — DERIVED. This is L5 conservation
   persistence (`s2p.py:595-638`, called by the learn route at `:2144`).
3. `after_conservation_snapshot` — 0.5247s average — AUTH/AUDIT. This is
   the post-outcome snapshot used by the receipt path (`s2p.py:2153-2155`).

The next largest step is `scorer_invoice_link_check` at 0.3115s average.
It is an AUTH guard because it controls duplicate invoice-link behavior,
even though it is a read-only graph operation.

Steps with more than 100ms run-to-run variance:

- `pre_conservation_snapshot`: 0.0003–0.3890s (0.3887s range).
- `after_conservation_snapshot`: 0.4831–0.5648s (0.0817s range; below the
  requested 100ms threshold and listed only as a notable near-threshold read).
- The score comparison's `pre_score_enrichment` varies 0.1632–0.2957s and
  `invoice_link` varies 0.1910–0.3497s; these are not learn steps but explain
  score variance.

DERIVED steps over 100ms and therefore primary deferral candidates:

- `l5_centroid`: 0.1735s average.
- `l5_conservation`: 0.7507s average.

The trace does not show post-lock side effects as a material contributor;
supplier, evolver, and shadow recording together average about 1ms.

## 4. Score trace

Score Run 1/2/3 below are the three scores paired with Learn Run 1/2/3.
The preceding warm-up score was 1.1302s and is retained only in the raw
trace.

| # | Step | Category | Run 1 (s) | Run 2 (s) | Run 3 (s) | Avg (s) |
|---:|---|---|---:|---:|---:|---:|
| 1 | validation_event | AUTH | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| 2 | pre_score_enrichment | DERIVED | 0.1632 | 0.2957 | 0.2484 | 0.2358 |
| 3 | mutation_lock_acquired | LOCK | 0.0004 | 0.0004 | 0.0005 | 0.0004 |
| 4 | scorer_score | AUTH | 0.0862 | 0.1163 | 0.1197 | 0.1074 |
| 5 | cache_centroid_invalidation | CACHE | 0.1586 | 0.2164 | 0.2223 | 0.1991 |
| 6 | mutation_lock_released | LOCK | 0.0003 | 0.0017 | 0.0005 | 0.0008 |
| 7 | auto_approve | DERIVED | 0.0001 | 0.0003 | 0.0002 | 0.0002 |
| 8 | derived_enrichment | DERIVED | 0.0002 | 0.0003 | 0.0003 | 0.0003 |
| 9 | invoice_link | AUTH/SIDE persistence | 0.1910 | 0.3497 | 0.2716 | 0.2708 |
| 10 | side_effect_submit | SIDE | 0.0005 | 0.0004 | 0.0004 | 0.0004 |
| 11 | response | AUTH | 0.0003 | 0.0004 | 0.0003 | 0.0003 |
| 12 | TOTAL | — | 0.6010 | 0.9816 | 0.8645 | 0.8157 |

The score trace's three dominant intervals are invoice linking (0.2708s),
pre-score enrichment (0.2358s), and cache/centroid invalidation (0.1991s).
The scorer's own score call is comparatively stable at 0.0862–0.1197s.

## 5. Recommendation

The data supports Option A in the design document, but with ordering:

1. Profile and reduce or defer `l5_conservation` persistence first; it is the
   largest clearly DERIVED interval at 0.75s average.
2. Profile the 0.52s post-outcome conservation snapshot separately. It is
   classified AUTH/AUDIT in the current contract, so it should not be deferred
   without an explicit receipt-generation contract change.
3. Investigate `scorer_invoice_link_check` (0.31s) before removing its guard;
   it is a duplicate-prevention correctness check, not merely presentation.
4. Defer only the L5 centroid persistence (0.17s) and other derived durable
   projections behind a durable, observable queue. The trace does not justify
   moving authoritative scoring, outcome writes, pre-outcome evidence, or
   receipt work off the response path.

The learn average is 4.3448s, with the scorer itself averaging 2.0295s. The
trace therefore confirms material S2P handler overhead, especially L5
conservation and the post-outcome snapshot. The score average for the paired
runs is 0.8157s, while the warm-up score is 1.1302s; the score trace does not
support a claim that `scorer_score` is the source of the learn latency.

Instrumentation cleanup verification found zero `TRACE` or `_trace_mark`
tokens in the target source (the remaining `_traceback` occurrence is an
existing exception attribute). The targeted cleanup test run produced 127
passed and 1 failed test; the failure was
`tests/test_s2p_shadow_live_age.py::test_live_age_shadow_learn_non_strict_success`,
which asserted that a duplicate learn must not return 200. No instrumentation
was present during that test run, and no product optimization was applied in
this diagnostic task.

