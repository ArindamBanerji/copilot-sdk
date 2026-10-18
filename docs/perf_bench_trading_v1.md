# Trading Frozen Benchmark Results (v1)

Date: 2026-10-13

## 1. Benchmark Configuration

- Fixture version: `v1`
- Deterministic seed: `20260711`
- Split: 400 training decisions and 100 held-out evaluation decisions
- Preset: current Trading tensor `(5, 4, 10)`, or 200 cells
- Categories: `trend_following`, `mean_reversion`, `event_driven`, `income_strategy`, `scalp_intraday`
- Actions: 4
- Factors: 10
- Scorer: `CompoundingScorer.from_preset("trading", profile="test", enable_rl=False)`
- Learning: the benchmark calls `score()` and `learn()` with `persist_artifacts=False`; held-out evaluation uses `score_read_only()`.
- Disruption seeds: global disruption uses the fixture seed internally; category disruption uses the same seed explicitly.

The `(5, 3, 6)=90` shape named in the benchmark request is the legacy Trading bootstrap shape. The current preset migrates that bootstrap to `(5, 4, 10)=200` at load time, so this run reports the active runtime shape.

## 2. Results

| Metric | Value |
|---|---:|
| Baseline accuracy after 400 decisions | 48.0% |
| Decisions from the 400-decision baseline to 0.50 accuracy | 77 |
| Accuracy after global disruption, magnitude 0.3 | 30.0% |
| Accuracy before category disruption | 48.0% |
| Accuracy after category disruption, magnitude 0.5 | 40.0% |
| Selected-category accuracy (`trend_following`, `mean_reversion`) | 42.5% → 22.5% |
| Unaffected-category accuracy | 51.7% → 51.7% |
| Decisions from the 400-decision baseline to 0.45 accuracy | 0 |
| Decisions from the 400-decision baseline to 0.55 accuracy | 352 |

`decisions_to_threshold()` was run from a fresh scorer trained on all 400 frozen training rows for each reported threshold. It then consumed additional rows through the normal score-and-learn benchmark path until the complete 100-row held-out set met the threshold.

## 3. DK Results

The DK functions are present and were run with their source-defined defaults.

| Metric | Value |
|---|---:|
| DK split | 1,000 train / 100 eval |
| DK held-out accuracy | 61.0% |
| Categories in `VARIANCE_LEARNING` | 5 of 5 |
| Evaluation examples in `VARIANCE_LEARNING` | 100 |
| Learned-weight mean top-action margin | 0.216414 |
| Uniform-weight mean top-action margin | 0.115907 |
| Learned-minus-uniform margin | +0.100507 |
| Learned weight max/min ratio | 20.000000 |

The positive margin delta shows that active learned DK weights separate the top action from the runner-up more clearly than uniform factor weights.

## 4. Cross-Copilot Comparison

Not run. The frozen v1 fixture is explicitly a Trading fixture: its header fixes `domain` and `preset` to `trading`, its categories and factors come from `TradingPreset`, and its outcome generator maps Trading actions. Reusing those rows for Purchasing or DataOps would test invalid category and factor contracts rather than provide a comparable benchmark.

## 5. Interpretation

The scorer math is stable and useful at 400 decisions. The 48.0% held-out result is deterministic and materially above the 25% random baseline for four actions. The independent fresh scorer used for the category experiment reproduced the same 48.0% baseline.

Disruption detection behaves as expected. Global centroid noise reduced held-out accuracy by 18 percentage points. Category-localized noise reduced accuracy in the two selected categories by 20 percentage points while leaving the other three categories unchanged at 51.7%. This confirms that category disruption is isolated to the selected centroid slices.

The 0.50 and 0.55 thresholds require 77 and 352 additional verified learning updates, respectively, while the 0.45 threshold is already satisfied. The frozen fixture therefore shows continued learning beyond 400 decisions rather than an immediate plateau.

The standard benchmark exercises the conservation check on every `learn()` call; it does not set the internal conservation-bypass flag. Its rows are tagged `benchmark=True`, however, and the scorer intentionally excludes such synthetic decisions from live conservation metrics. Consequently this run does **not** establish the live preseed-count conservation threshold. That behavior needs a separate conservation benchmark using non-benchmark decisions; claiming that the live gate engaged from these fixture rows would be misleading.

## 6. Relevance to DIAG-SEQ-D-TRADING-2

The frozen scorer benchmark completes with deterministic learning, a baseline above random, a clear disruption response, exact category isolation, and a positive DK weight effect. These results support the diagnosis that the 16 Trading E2E timeout failures are caused by backend read-path latency over the large AGE dataset, rather than a regression in scorer mathematics.

