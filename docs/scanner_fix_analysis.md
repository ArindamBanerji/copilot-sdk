# Integrity Scanner Fix Analysis

## Section A: Why the 11 P1 findings are false positives

The current double-prefix check uses:

```python
r"conservation.*conservation|/api/.*api/"
```

It searches whole source lines rather than route path literals. The first alternative therefore matches any line containing `conservation` twice, while the second matches any line containing two unrelated `/api/` fragments. Examples from the 11 findings that are not doubled routes:

```python
conservation_provider=conservation_provider,
"conservation": lambda s: build_conservation_status(
if path.startswith(("/api/dataops", "/api/context", "/api/ae", "/api/di", "/api/score")):
```

The replacement will inspect only string literals used as route paths and detect adjacent repeated path segments. Its path-level expression is:

```python
r"/(api|[A-Za-z0-9_-]+)/\1(?:/|$)"
```

It is applied only to parsed decorator path strings. It catches `/api/conservation/conservation/` and `/api/api/something`, while ordinary Python identifiers and lists of distinct paths cannot match.

## Section B: Complete `api-path-mismatch` triage

Every baseline finding was resolved against the effective FastAPI path after composing route-decorator paths, `APIRouter(prefix=...)`, `include_router(..., prefix=...)`, shared SDK router factories, and helper-mounted self-computation routes. Query strings were removed for route matching, and dynamic frontend/backend parameters were normalized.

Reason codes: `FACTORY` = route exists inside a mounted router factory; `MODULE` = route exists in a mounted module-level router; `SDK` = route exists in a mounted shared SDK router; `SELF` = route exists through `mount_self_computation_router`; `QUERY` = query text must be removed before path comparison; `EMPTY` = valid empty child path inherits the router prefix; `FSTRING` = backend path is a statically resolvable f-string; `CONCAT` = the old frontend regex captured only the first operand of a concatenated string.

| File | Line | Frontend path | Matched backend? | Verdict | Reason |
|---|---:|---|---|---|---|
| apps/trading/frontend/src/api.ts | 113 | `/api/context/analytics` | Yes | SCANNER_GAP | MODULE |
| apps/trading/frontend/src/api.ts | 169 | `/api/trading/regime` | Yes | SCANNER_GAP | FACTORY/EMPTY |
| apps/trading/frontend/src/api.ts | 173 | `/api/trading/regime/detail` | Yes | SCANNER_GAP | FACTORY |
| apps/trading/frontend/src/api.ts | 228 | `/api/trading/regime/current` | Yes | SCANNER_GAP | FACTORY |
| apps/trading/frontend/src/api.ts | 236 | `/api/trading/regime/performance` | Yes | SCANNER_GAP | FACTORY |
| apps/trading/frontend/src/api.ts | 240 | `/api/trading/regime/recommendation` | Yes | SCANNER_GAP | FACTORY |
| apps/trading/frontend/src/api.ts | 244 | `/api/trading/regime-status` | Yes | SCANNER_GAP | FACTORY |
| apps/trading/frontend/src/api.ts | 279 | `/api/trading/cohort-status` | Yes | SCANNER_GAP | FACTORY |
| apps/trading/frontend/src/api.ts | 283 | `/api/trading/promotion` | Yes | SCANNER_GAP | FACTORY/EMPTY |
| apps/trading/frontend/src/api.ts | 343 | `/api/trading/promotion/dashboard` | Yes | SCANNER_GAP | FACTORY |
| apps/trading/frontend/src/api.ts | 365 | `/api/trading/analytics/vol-sharpe` | Yes | SCANNER_GAP | FACTORY |
| apps/trading/frontend/src/api.ts | 374 | `/api/trading/volatility/vrp` | Yes | SCANNER_GAP | FACTORY |
| apps/trading/frontend/src/api.ts | 383 | `/api/trading/volatility/dispersion` | Yes | SCANNER_GAP | FACTORY |
| apps/trading/frontend/src/api.ts | 387 | `/api/trading/volatility/tail-bets` | Yes | SCANNER_GAP | FACTORY |
| apps/trading/frontend/src/api.ts | 391 | `/api/trading/analytics/vrp-attribution` | Yes | SCANNER_GAP | FACTORY |
| apps/trading/frontend/src/api.ts | 395 | `/api/trading/analytics/regime-vrp` | Yes | SCANNER_GAP | FACTORY |
| apps/trading/frontend/src/api.ts | 399 | `/api/trading/situation/regime` | Yes | SCANNER_GAP | FACTORY |
| apps/trading/frontend/src/api.ts | 403 | `/api/trading/situation` | Yes | SCANNER_GAP | FACTORY/EMPTY |
| apps/trading/frontend/src/api.ts | 407 | `/api/trading/situation/conditioned-stats` | Yes | SCANNER_GAP | FACTORY |
| apps/trading/frontend/src/api.ts | 411 | `/api/trading/situation/sharpe-adjustment` | Yes | SCANNER_GAP | FACTORY |
| apps/trading/frontend/src/api.ts | 415 | `/api/trading/situation/abstention` | Yes | SCANNER_GAP | FACTORY |
| apps/trading/frontend/src/api.ts | 419 | `/api/trading/situation/regime-rejections` | Yes | SCANNER_GAP | FACTORY |
| apps/trading/frontend/src/api.ts | 455 | `/api/trading/claim-gate` | Yes | SCANNER_GAP | FACTORY |
| apps/trading/frontend/src/api.ts | 459 | `/api/trading/analytics/dispersion-follow` | Yes | SCANNER_GAP | FACTORY |
| apps/trading/frontend/src/api.ts | 463 | `/api/trading/vix-timing` | Yes | SCANNER_GAP | FACTORY |
| apps/trading/frontend/src/api.ts | 490 | `/api/trading/execution/summary` | Yes | SCANNER_GAP | FACTORY |
| apps/trading/frontend/src/api.ts | 494 | `/api/trading/execution/analysis` | Yes | SCANNER_GAP | FACTORY |
| apps/trading/frontend/src/api.ts | 525 | `/api/trading/webhook/history` | Yes | SCANNER_GAP | FACTORY |
| apps/trading/frontend/src/api.ts | 559 | `/api/trading/prescore` | Yes | SCANNER_GAP | FACTORY |
| apps/trading/frontend/src/api.ts | 598 | `/api/trading/pre-score` | Yes | SCANNER_GAP | FACTORY |
| apps/trading/frontend/src/api.ts | 602 | `/api/history` | Yes | SCANNER_GAP | SDK |
| apps/trading/frontend/src/api.ts | 717 | `/api/evolution/variants` | Yes | SCANNER_GAP | SDK |
| apps/trading/frontend/src/api.ts | 723 | `/api/evolution/history` | Yes | SCANNER_GAP | SDK |
| apps/trading/frontend/src/api.ts | 727 | `/api/evolution/promoted` | Yes | SCANNER_GAP | SDK |
| apps/trading/frontend/src/api.ts | 732 | `/api/trading/evolution/log?kind=variant` | Yes | SCANNER_GAP | FACTORY/QUERY |
| apps/trading/frontend/src/api.ts | 736 | `/api/trading/evolution/active` | Yes | SCANNER_GAP | FACTORY |
| apps/trading/frontend/src/api.ts | 750 | `/api/trading/evolution/proposals` | Yes | SCANNER_GAP | FACTORY |
| apps/trading/frontend/src/api.ts | 754 | `/api/trading/evolution/active` | Yes | SCANNER_GAP | FACTORY |
| apps/trading/frontend/src/api.ts | 762 | `/api/trading/evolution/log?kind=parameter` | Yes | SCANNER_GAP | FACTORY/QUERY |
| apps/trading/frontend/src/api.ts | 767 | `/api/trading/evolution/apply` | Yes | SCANNER_GAP | FACTORY |
| apps/trading/frontend/src/api.ts | 773 | `/api/trading/evolution/rollback` | Yes | SCANNER_GAP | FACTORY |
| apps/trading/frontend/src/api.ts | 815 | `/api/trading/evolution/rejection-summary` | Yes | SCANNER_GAP | FACTORY |
| apps/trading/frontend/src/api.ts | 819 | `/api/self/evolution/summary` | Yes | SCANNER_GAP | SELF |
| apps/trading/frontend/src/api.ts | 900 | `/api/transfer/opportunities` | Yes | SCANNER_GAP | SDK |
| apps/trading/frontend/src/api.ts | 904 | `/api/transfer/status` | Yes | SCANNER_GAP | SDK |
| apps/trading/frontend/src/api.ts | 912 | `/api/transfer/execute` | Yes | SCANNER_GAP | SDK |
| apps/trading/frontend/src/api.ts | 960 | `/api/archetypes/current` | Yes | SCANNER_GAP | SDK |
| apps/trading/frontend/src/api.ts | 968 | `/api/context/trade-metadata` | Yes | SCANNER_GAP | MODULE |
| apps/trading/frontend/src/api.ts | 972 | `/api/context/market-snapshot` | Yes | SCANNER_GAP | MODULE |
| apps/trading/frontend/src/api.ts | 980 | `/api/trajectory` | Yes | SCANNER_GAP | SDK |
| apps/trading/frontend/src/api.ts | 984 | `/api/conservation/status` | Yes | SCANNER_GAP | SDK |
| apps/trading/frontend/src/api.ts | 988 | `/api/context/conservation-breakdown` | Yes | SCANNER_GAP | MODULE |
| apps/trading/frontend/src/api.ts | 1026 | `/api/fingerprint` | Yes | SCANNER_GAP | SDK |
| apps/trading/frontend/src/api.ts | 1030 | `/api/context/trust-analysis` | Yes | SCANNER_GAP | MODULE |
| apps/trading/frontend/src/api.ts | 1034 | `/api/context/patterns` | Yes | SCANNER_GAP | MODULE |
| apps/trading/frontend/src/api.ts | 1038 | `/api/score` | Yes | SCANNER_GAP | SDK |
| apps/trading/frontend/src/api.ts | 1049 | `/api/learn` | Yes | SCANNER_GAP | SDK |
| apps/trading/frontend/src/api.ts | 1059 | `/api/context/trade-metadata` | Yes | SCANNER_GAP | MODULE |
| apps/purchasing/frontend/src/api.ts | 163 | `/api/context/analytics` | Yes | SCANNER_GAP | MODULE |
| apps/purchasing/frontend/src/api.ts | 167 | `/api/context/items` | Yes | SCANNER_GAP | MODULE |
| apps/purchasing/frontend/src/api.ts | 171 | `/api/inventory/summary` | Yes | SCANNER_GAP | MODULE |
| apps/purchasing/frontend/src/api.ts | 175 | `/api/context/today-summary` | Yes | SCANNER_GAP | MODULE |
| apps/purchasing/frontend/src/api.ts | 179 | `/api/context/weather` | Yes | SCANNER_GAP | MODULE |
| apps/purchasing/frontend/src/api.ts | 321 | `/api/purchasing/menu/analysis` | Yes | SCANNER_GAP | FACTORY |
| apps/purchasing/frontend/src/api.ts | 325 | `/api/purchasing/menu/alerts` | Yes | SCANNER_GAP | FACTORY |
| apps/purchasing/frontend/src/api.ts | 329 | `/api/purchasing/menu/summary` | Yes | SCANNER_GAP | FACTORY |
| apps/purchasing/frontend/src/api.ts | 346 | `/api/purchasing/events/plan` | Yes | SCANNER_GAP | FACTORY |
| apps/purchasing/frontend/src/api.ts | 350 | `/api/purchasing/events/history` | Yes | SCANNER_GAP | FACTORY |
| apps/purchasing/frontend/src/api.ts | 358 | `/api/purchasing/events/record` | Yes | SCANNER_GAP | FACTORY |
| apps/purchasing/frontend/src/api.ts | 370 | `/api/purchasing/chain/validate` | Yes | SCANNER_GAP | FACTORY |
| apps/purchasing/frontend/src/api.ts | 378 | `/api/purchasing/chain/status` | Yes | SCANNER_GAP | FACTORY |
| apps/purchasing/frontend/src/api.ts | 398 | `/api/purchasing/delivery/today` | Yes | SCANNER_GAP | FACTORY |
| apps/purchasing/frontend/src/api.ts | 402 | `/api/purchasing/delivery/week` | Yes | SCANNER_GAP | FACTORY |
| apps/purchasing/frontend/src/api.ts | 406 | `/api/purchasing/delivery/consolidation` | Yes | SCANNER_GAP | FACTORY |
| apps/purchasing/frontend/src/api.ts | 414 | `/api/context/order-metadata` | Yes | SCANNER_GAP | MODULE |
| apps/purchasing/frontend/src/api.ts | 419 | `/api/dashboard/orders` | Yes | SCANNER_GAP | MODULE |
| apps/purchasing/frontend/src/api.ts | 425 | `/api/context/order-metadata` | Yes | SCANNER_GAP | MODULE |
| apps/purchasing/frontend/src/api.ts | 429 | `/api/evolution/variants` | Yes | SCANNER_GAP | SDK |
| apps/purchasing/frontend/src/api.ts | 450 | `/api/evolution/history` | Yes | SCANNER_GAP | SDK |
| apps/purchasing/frontend/src/api.ts | 454 | `/api/evolution/promoted` | Yes | SCANNER_GAP | SDK |
| apps/purchasing/frontend/src/api.ts | 459 | `/api/history` | Yes | SCANNER_GAP | SDK |
| apps/purchasing/frontend/src/api.ts | 464 | `/api/fingerprint` | Yes | SCANNER_GAP | SDK |
| apps/purchasing/frontend/src/api.ts | 468 | `/api/trajectory` | Yes | SCANNER_GAP | SDK |
| apps/purchasing/frontend/src/api.ts | 472 | `/api/conservation/status` | Yes | SCANNER_GAP | SDK |
| apps/purchasing/frontend/src/api.ts | 476 | `/api/purchasing/qbo/vendors` | Yes | SCANNER_GAP | FACTORY |
| apps/purchasing/frontend/src/api.ts | 480 | `/api/purchasing/qbo/bills` | Yes | SCANNER_GAP | FACTORY |
| apps/purchasing/frontend/src/api.ts | 484 | `/api/purchasing/qbo/status` | Yes | SCANNER_GAP | FACTORY |
| apps/purchasing/frontend/src/api.ts | 498 | `/api/purchasing/spend/summary` | Yes | SCANNER_GAP | FACTORY |
| apps/purchasing/frontend/src/api.ts | 502 | `/api/purchasing/spend/by-category` | Yes | SCANNER_GAP | FACTORY |
| apps/purchasing/frontend/src/api.ts | 506 | `/api/purchasing/spend/alerts` | Yes | SCANNER_GAP | FACTORY |
| apps/purchasing/frontend/src/api.ts | 510 | `/api/purchasing/spend/by-supplier` | Yes | SCANNER_GAP | FACTORY |
| apps/purchasing/frontend/src/api.ts | 514 | `/api/purchasing/spend/cost-per-cover` | Yes | SCANNER_GAP | FACTORY |
| apps/purchasing/frontend/src/api.ts | 518 | `/api/purchasing/commodity/indices` | Yes | SCANNER_GAP | FACTORY |
| apps/purchasing/frontend/src/api.ts | 526 | `/api/purchasing/commodity/status` | Yes | SCANNER_GAP | FACTORY |
| apps/purchasing/frontend/src/api.ts | 540 | `/api/purchasing/par/recommendations` | Yes | SCANNER_GAP | FACTORY |
| apps/purchasing/frontend/src/api.ts | 545 | `/api/purchasing/par/status` | Yes | SCANNER_GAP | FACTORY |
| apps/purchasing/frontend/src/api.ts | 580 | `/api/purchasing/cohort-status` | Yes | SCANNER_GAP | FACTORY |
| apps/purchasing/frontend/src/api.ts | 584 | `/api/purchasing/iks/summary` | Yes | SCANNER_GAP | FACTORY |
| apps/purchasing/frontend/src/api.ts | 589 | `/api/purchasing/suppliers/scorecards` | Yes | SCANNER_GAP | FACTORY |
| apps/purchasing/frontend/src/api.ts | 600 | `/api/purchasing/trust-weights` | Yes | SCANNER_GAP | FACTORY/EMPTY |
| apps/purchasing/frontend/src/api.ts | 604 | `/api/purchasing/trust-weights/expected` | Yes | SCANNER_GAP | FACTORY |
| apps/purchasing/frontend/src/api.ts | 608 | `/api/purchasing/trust-weights/insights` | Yes | SCANNER_GAP | FACTORY |
| apps/purchasing/frontend/src/api.ts | 612 | `/api/purchasing/auto-order/status` | Yes | SCANNER_GAP | FACTORY |
| apps/purchasing/frontend/src/api.ts | 616 | `/api/purchasing/auto-order/enable` | Yes | SCANNER_GAP | FACTORY |
| apps/purchasing/frontend/src/api.ts | 620 | `/api/purchasing/auto-order/disable` | Yes | SCANNER_GAP | FACTORY |
| apps/purchasing/frontend/src/api.ts | 624 | `/api/purchasing/auto-order/audit` | Yes | SCANNER_GAP | FACTORY |
| apps/purchasing/frontend/src/api.ts | 634 | `/api/purchasing/auto-order/evaluate` | Yes | SCANNER_GAP | FACTORY |
| apps/purchasing/frontend/src/api.ts | 638 | `/api/purchasing/match/queue` | Yes | SCANNER_GAP | FACTORY |
| apps/purchasing/frontend/src/api.ts | 642 | `/api/purchasing/queue` | Yes | SCANNER_GAP | FACTORY/EMPTY |
| apps/purchasing/frontend/src/api.ts | 650 | `/api/purchasing/match` | Yes | SCANNER_GAP | FACTORY/EMPTY |
| apps/purchasing/frontend/src/api.ts | 657 | `/api/self/` | Yes | SCANNER_GAP | CONCAT (effective `/api/self/centroid-history`) |
| apps/purchasing/frontend/src/api.ts | 665 | `/api/self/accuracy-by-category` | Yes | SCANNER_GAP | SELF |
| apps/purchasing/frontend/src/api.ts | 674 | `/api/self/decisions` | Yes | SCANNER_GAP | SELF |
| apps/purchasing/frontend/src/api.ts | 678 | `/api/self/audit-trail` | Yes | SCANNER_GAP | SELF |
| apps/purchasing/frontend/src/api.ts | 690 | `/api/context/similar` | Yes | SCANNER_GAP | MODULE |
| apps/purchasing/frontend/src/api.ts | 704 | `/api/score` | Yes | SCANNER_GAP | SDK |
| apps/purchasing/frontend/src/api.ts | 713 | `/api/learn` | Yes | SCANNER_GAP | SDK |
| apps/purchasing/frontend/src/api.ts | 717 | `/api/purchasing/verify/reason-codes` | Yes | SCANNER_GAP | FACTORY |
| apps/purchasing/frontend/src/api.ts | 726 | `/api/purchasing/verify` | Yes | SCANNER_GAP | FACTORY/EMPTY |
| apps/purchasing/frontend/src/api.ts | 764 | `/api/purchasing/discovery/insights` | Yes | SCANNER_GAP | FACTORY |
| apps/purchasing/frontend/src/api.ts | 768 | `/api/purchasing/discovery/digest` | Yes | SCANNER_GAP | FACTORY |
| apps/purchasing/frontend/src/api.ts | 780 | `/api/purchasing/alerts` | Yes | SCANNER_GAP | FACTORY/EMPTY |
| apps/purchasing/frontend/src/api.ts | 784 | `/api/purchasing/alerts` | Yes | SCANNER_GAP | FACTORY/EMPTY |
| apps/purchasing/frontend/src/api.ts | 804 | `/api/purchasing/economic/model` | Yes | SCANNER_GAP | FACTORY |
| apps/purchasing/frontend/src/api.ts | 808 | `/api/purchasing/economic/roi-summary` | Yes | SCANNER_GAP | FACTORY |
| apps/purchasing/frontend/src/api.ts | 830 | `/api/purchasing/competence/ramp` | Yes | SCANNER_GAP | FACTORY |
| apps/purchasing/frontend/src/api.ts | 845 | `/api/purchasing/multi-unit/dashboard` | Yes | SCANNER_GAP | FACTORY |
| apps/purchasing/frontend/src/api.ts | 850 | `/api/purchasing/multi-unit/compare` | Yes | SCANNER_GAP | FACTORY |
| apps/purchasing/frontend/src/api.ts | 856 | `/api/purchasing/multi-unit/transfer-opportunities` | Yes | SCANNER_GAP | FACTORY |
| apps/dataops/frontend/src/api.ts | 121 | `/api/dataops/claims?context=demo` | Yes | SCANNER_GAP | FACTORY/QUERY |
| apps/dataops/frontend/src/api.ts | 125 | `/api/dataops/holdout/status` | Yes | SCANNER_GAP | FACTORY |
| apps/dataops/frontend/src/api.ts | 129 | `/api/dataops/abstention-check?source_id=unknown` | Yes | SCANNER_GAP | FACTORY/QUERY |
| apps/dataops/frontend/src/api.ts | 133 | `/api/dataops/promotion` | Yes | SCANNER_GAP | FACTORY |
| apps/dataops/frontend/src/api.ts | 178 | `/api/dataops/frozen-twin/status` | Yes | SCANNER_GAP | FACTORY |
| apps/dataops/frontend/src/api.ts | 182 | `/api/dataops/frozen-twin/freeze` | Yes | SCANNER_GAP | FACTORY |
| apps/dataops/frontend/src/api.ts | 186 | `/api/dataops/holdout/register` | Yes | SCANNER_GAP | FACTORY |
| apps/dataops/frontend/src/api.ts | 190 | `/api/dataops/holdout/verify` | Yes | SCANNER_GAP | FACTORY |
| apps/dataops/frontend/src/api.ts | 317 | `/api/dataops/intelligence/source-trust` | Yes | SCANNER_GAP | FACTORY |
| apps/dataops/frontend/src/api.ts | 380 | `/api/di/products` | Yes | SCANNER_GAP | FACTORY |
| apps/dataops/frontend/src/api.ts | 384 | `/api/di/acquisition-advice` | Yes | SCANNER_GAP | SDK |
| apps/dataops/frontend/src/api.ts | 388 | `/api/di/sources` | Yes | SCANNER_GAP | SDK |
| apps/dataops/frontend/src/api.ts | 392 | `/api/dataops/trust` | Yes | SCANNER_GAP | FSTRING |
| apps/dataops/frontend/src/api.ts | 398 | `/api/di/trust/verify` | Yes | SCANNER_GAP | FACTORY |
| apps/dataops/frontend/src/api.ts | 418 | `/api/di/query` | Yes | SCANNER_GAP | SDK |
| apps/dataops/frontend/src/api.ts | 438 | `/api/context/pipelines` | Yes | SCANNER_GAP | MODULE |
| apps/dataops/frontend/src/api.ts | 443 | `/api/context/alerts` | Yes | SCANNER_GAP | MODULE |
| apps/dataops/frontend/src/api.ts | 448 | `/api/context/alert-groups` | Yes | SCANNER_GAP | MODULE |
| apps/dataops/frontend/src/api.ts | 452 | `/api/ae/impact` | Yes | SCANNER_GAP | FACTORY |
| apps/dataops/frontend/src/api.ts | 456 | `/api/ae/conservation-history` | Yes | SCANNER_GAP | FACTORY |
| apps/dataops/frontend/src/api.ts | 460 | `/api/ae/transfer-status` | Yes | SCANNER_GAP | FACTORY |
| apps/dataops/frontend/src/api.ts | 494 | `/api/dataops/trust` | Yes | SCANNER_GAP | FSTRING |
| apps/dataops/frontend/src/api.ts | 498 | `/api/self/diagnostics` | Yes | SCANNER_GAP | SELF |
| apps/dataops/frontend/src/api.ts | 502 | `/api/di/perturb/status` | Yes | SCANNER_GAP | FACTORY |
| apps/dataops/frontend/src/api.ts | 511 | `/api/di/perturb` | Yes | SCANNER_GAP | FACTORY/EMPTY |
| apps/dataops/frontend/src/api.ts | 515 | `/api/di/perturb/revert` | Yes | SCANNER_GAP | FACTORY |
| apps/dataops/frontend/src/api.ts | 541 | `/api/discovery/cross-system` | Yes | SCANNER_GAP | SDK |
| apps/dataops/frontend/src/api.ts | 576 | `/api/dataops/cohort-status` | Yes | SCANNER_GAP | FACTORY |
| apps/dataops/frontend/src/api.ts | 586 | `/api/conservation/status` | Yes | SCANNER_GAP | SDK |
| apps/dataops/frontend/src/api.ts | 597 | `/api/conservation/what-if` | Yes | SCANNER_GAP | SDK |
| apps/dataops/frontend/src/api.ts | 606 | `/api/trajectory` | Yes | SCANNER_GAP | SDK |
| apps/dataops/frontend/src/api.ts | 610 | `/api/context/accuracy-by-category` | Yes | SCANNER_GAP | MODULE |
| apps/dataops/frontend/src/api.ts | 771 | `/api/context/enterprise-health` | Yes | SCANNER_GAP | MODULE |
| apps/dataops/frontend/src/api.ts | 779 | `/api/context/celonis/process-data` | Yes | SCANNER_GAP | MODULE |
| apps/dataops/frontend/src/api.ts | 864 | `/api/ae/pattern-origin` | Yes | SCANNER_GAP | FACTORY |
| apps/dataops/frontend/src/api.ts | 868 | `/api/ae/incident` | Yes | SCANNER_GAP | FACTORY |
| apps/dataops/frontend/src/api.ts | 872 | `/api/fingerprint` | Yes | SCANNER_GAP | SDK |
| apps/dataops/frontend/src/api.ts | 876 | `/api/evolution/variants` | Yes | SCANNER_GAP | SDK |
| apps/dataops/frontend/src/api.ts | 928 | `/api/evolution/history` | Yes | SCANNER_GAP | SDK |
| apps/dataops/frontend/src/api.ts | 932 | `/api/evolution/promoted` | Yes | SCANNER_GAP | SDK |
| apps/dataops/frontend/src/api.ts | 953 | `/api/ae/operational-rules` | Yes | SCANNER_GAP | FACTORY |
| apps/dataops/frontend/src/api.ts | 957 | `/api/score` | Yes | SCANNER_GAP | SDK |
| apps/dataops/frontend/src/api.ts | 962 | `/api/learn` | Yes | SCANNER_GAP | SDK |
| apps/dataops/frontend/src/api.ts | 966 | `/api/context/alert-metadata` | Yes | SCANNER_GAP | MODULE |
| apps/dataops/frontend/src/api.ts | 970 | `/api/context/apply-fix` | Yes | SCANNER_GAP | MODULE |

Triage totals: **0 REAL, 0 FALSE_POS, 174 SCANNER_GAP**. All 174 emitted findings are operational false positives; `SCANNER_GAP` identifies the concrete scanner limitation responsible for each one.

## Section C: Scanner improvements needed

1. Parse Python route decorators with `ast` so multiline decorators, empty child paths, and simple f-strings are represented correctly.
2. Recursively scan every Python module below each app backend. The current file walk is recursive already, but its line regex loses router context.
3. Record `APIRouter(prefix=...)` and compose it with each decorator path.
4. Resolve `include_router` mounts to router factories and imported module-level routers, then prepend mount prefixes.
5. Resolve shared SDK router factories and helper mounts such as `mount_self_computation_router` for each app rather than adding bare SDK child paths globally.
6. Extract complete frontend quoted strings and template literals, normalize `${...}` and FastAPI `{name}` parameters to `{param}`, and ignore query/fragment text during route comparison.
7. Fold simple frontend string concatenation so `/api/self/` is not treated as a complete request path.
8. Compare normalized full paths exactly. Prefix matching can hide a missing child route.
9. Restrict double-prefix detection to parsed route path literals with adjacent repeated segments.

## Fix Plan

1. `scripts/scan_integrity.py`, router parsing helpers: add AST-based string, decorator, router-prefix, import, and mount extraction.
2. `scripts/scan_integrity.py`, `check_routers`: replace whole-line grep with repeated-segment validation over actual route decorator strings.
3. `scripts/scan_integrity.py`, `check_parity`: build per-app effective endpoint sets by recursively collecting app routes and resolving mounts to app and SDK router definitions.
4. `scripts/scan_integrity.py`, frontend extraction/normalization: collect full quoted/template expressions, fold simple concatenated literals, remove query/fragment text, and normalize `${...}`/`{...}` parameters.
5. `tests/test_integrity_scanner.py`: add focused regression coverage for double-prefix false positives, composed router prefixes, SDK/shared mounts, parameter normalization, and true missing routes.
6. `docs/scanner_fix_analysis.md`: record post-fix counts and verification results.

## Verification and before/after counts

| Measure | Before | After |
|---|---:|---:|
| Double-prefix P1 findings | 11 | 0 |
| `api-path-mismatch` P2 findings | 174 | 0 |
| Stale-path P2 findings | 35 | 35 (unchanged by design) |
| Real API mismatches | unknown | 0 |

The static scan finishes with 35 findings: P1=0, P2=35, P3=0, all in the untouched `stale-path` check. `python scripts/scan_integrity.py --repo sdk --check parity,routers --format json` returns valid JSON, a CLEAN verdict, and exit code 0. `--repo all --check parity --format json` scans SDK, S2P, and CI Platform, returns valid JSON, and exits 0.

The required full `--repo sdk --check all` run produced 40 findings: the same 35 stale paths plus five live-service observations from processes already running locally. The two P1s are real health/conservation alpha mismatches for Trading and Purchasing, rather than router scanner false positives. The three live P2s are two `AMBER` conservation-status vocabulary warnings and DataOps health missing `phase`. These runtime findings do not change the targeted static before/after counts.

Validation:

- `python -m mypy scripts/scan_integrity.py --config-file pyproject.toml`: PASS
- `python -m pytest tests/test_integrity_scanner.py -q --timeout=60`: 16 passed
- Static integrity scan: P1=0, `api-path-mismatch`=0, stale-path=35
