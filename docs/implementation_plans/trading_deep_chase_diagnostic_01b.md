# Trading Deep Chase Diagnostic 01b

Date: 2026-06-05
Model: gpt-5.3
Task Type: Diagnostic document creation only; no source code changes.
Repo: copilot-sdk
Diagnostic Scope: Deep read of Trading CLI, SDK backend conservation/IKS surfaces, `context_router.py`, `services/pattern_detector.py`, and IBKR/CSV connector stub context.
Prerequisite Diagnostic: `docs/implementation_plans/trading_backend_filetree_diagnostic.md` found and read.

## Executive Summary

* Overall verdict: several unresolved MAP items can move from path guessing to targeted supplement/review prompts, but this diagnostic does not prove runtime behavior.
* Which MAP items can be dropped: none should be dropped solely from this inspection.
* Which MAP items need supplement prompts: P53, P55, P56, P58, P59, P60, P61, P62, P85.
* Which MAP items need full implementation: P58 appears to need full implementation if `/iks` or IKS score wiring is required; no SDK backend IKS evidence was found.
* Biggest remaining ambiguity: packaging/install validation and runtime API behavior were not tested by instruction, so P62 and CLI service behavior remain code-inspection verdicts only.
* Recommended next prompt: a focused implementation supplement for P58 IKS wiring, plus a no-edit GPT-5.5 review of P52/P61/P62 packaging and CLI behavior if PyPI readiness matters.

## Path Resolution

* CLAUDE_SDK value: `C:\Users\baner\CopyFolder\IOT_thoughts\python-projects\kaggle_experiments\claude_projects\copilot-sdk`
* Repo path used: `C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\kaggle_experiments\claude_projects\copilot-sdk`
* Trading backend app path used: `C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\kaggle_experiments\claude_projects\copilot-sdk\apps\trading\backend\app`
* CLI path: `apps/trading/backend/cli.py`
* SDK backend path: `copilot_sdk/backend`
* context_router.py path: `apps/trading/backend/app/context_router.py`
* pattern_detector.py path: `apps/trading/backend/app/services/pattern_detector.py`
* IBKR connector path: `apps/trading/backend/app/connectors/ibkr_connector.py`
* CSV connector path: `apps/trading/backend/app/connectors/csv_connector.py`
* Prior Diag 01 report found: YES

## CLAUDE.md Relevant Notes

* Do not use git directly.
* Docs are aspirational until proven in code; inspect actual source files.
* Cite file and line for behavioral claims.
* Code and tests beat docs; report drift when source and docs disagree.
* Make surgical changes only.
* The repo guidance says to verify after changes, but this diagnostic was explicitly constrained to no tests and one Markdown write only.

## Part 1 - CLI Deep Read

### Files inspected

* `apps/trading/backend/cli.py`
* `apps/trading/pyproject.toml`
* `apps/trading/ci_trading/cli.py`

### CLI commands found

| Command | Framework Click/Typer/Other | Calls Real Service/API? | Mock/Hardcoded? | Evidence |
| ------- | --------------------------- | ----------------------: | --------------: | -------- |
| init | argparse | No | No | `cmd_init` at `apps/trading/backend/cli.py` L206; parser at L951. Creates local config/trade storage. |
| import | argparse | Yes | No | `cmd_import` at L231; imports CSV via `CSVConnector` or IBKR via `IBKRConnector`; parser at L954-L960. |
| score | argparse | Yes | No | `cmd_score` at L271 calls `compute_factors`; prints "Offline factor scoring only; no decision recorded" at L285/L306. |
| trust | argparse | Yes | No | `cmd_trust` at L310 uses `TRADING_FACTOR_COMPUTERS`, `ALL_FACTOR_NAMES`, and `compute_factors`; sample capped at L326. |
| conservation | argparse | No backend API | Partial offline proxy | `cmd_conservation` at L336 prints "Offline conservation proxy" at L347 and "Full conservation requires the scoring server" at L352. |
| journal | argparse | Local store only | No | `cmd_journal` at L356; parser at L974-L982. |
| regime | argparse | Yes | No | `cmd_regime` at L426 imports `RegimeService`; detailed mode imports `RegimeRecommender`. |
| correlation | argparse | Yes | No | `cmd_correlation` at L492 imports `CorrelationService`; parser at L987-L989. |
| vix-timing | argparse | Yes | No | `cmd_vix_timing` at L530 imports `RegimeService` and `VIXTimingService`; parser at L991-L992. |
| promote | argparse | Yes | CLI conservation unknown | `cmd_promote` at L580 imports `PromotionService`; L588 says CLI conservation status is unknown and GREEN conservation is required. |
| export | argparse | Local store only | No | `cmd_export` at L698; parser at L998-L1001. |
| backup | argparse | Local store only | No | `cmd_backup` at L721; parser at L1003-L1004. |
| restore | argparse | Local store only | No | `cmd_restore` at L742; parser at L1006-L1008. |
| retag | argparse | Local store only | No | `cmd_retag` at L762; parser at L1010-L1013. |
| order | argparse | Yes | Optional mock broker | `cmd_order` at L775 calls broker `place_order`; parser at L1015-L1022 includes `--broker` choices `alpaca`, `mock`. |
| orders | argparse | Yes | Optional mock broker | `cmd_orders` at L806 calls broker `get_orders`; parser at L1024-L1028 includes `--broker` choices `alpaca`, `mock`. |
| positions | argparse | Yes | Optional mock broker | `cmd_positions` at L821 calls broker `get_positions`; parser at L1030-L1032 includes `--broker` choices `alpaca`, `mock`. |
| account | argparse | Yes | Optional mock broker | `cmd_account` at L842 calls broker `get_account`; parser at L1034-L1036 includes `--broker` choices `alpaca`, `mock`. |
| sync | argparse | Yes | Optional mock broker | `cmd_sync` at L854 calls broker `get_orders(status="filled")`; parser at L1038-L1042 includes `--broker` choices `alpaca`, `mock`. |
| evolution variants | argparse | Yes | No | `cmd_evolution_variants` at L892; parser at L1047-L1048. |
| evolution status | argparse | Yes | Partial hardcoded unavailable status | `cmd_evolution_status` at L912; L924 prints "last promotion: unavailable". |
| evolution promote | argparse | Yes | Backend promotion unavailable in CLI | `cmd_evolution_promote` at L929; L938-L939 blocks because offline CLI cannot verify GREEN conservation and no backend promotion endpoint is available. |

### pyproject / Entry Point

* pyproject path: `apps/trading/pyproject.toml`
* ci-trading entry point present: YES
* evidence:
  * `apps/trading/pyproject.toml` has `[project.scripts]` with `ci-trading = "ci_trading.cli:main"`.
  * `apps/trading/ci_trading/cli.py` exists and its `main` loads `backend/cli.py` through `_load_backend_cli()`.

### CLI Verdicts

* P52 TRD-CLI-CORE: SUPPLEMENT. Core CLI exists with many commands, but scoring/conservation paths are explicitly offline/proxy in places.
* P61 TRD-CLI-FULL: SUPPLEMENT. Broad command coverage exists, including broker, journal, regime, correlation, VIX timing, promotion, export/backup/restore, and evolution; runtime behavior was not tested.
* P62 TRD-PYPI: SUPPLEMENT. `pyproject.toml` and console script exist, but packaging/install/build behavior was not validated by instruction.

## Part 2 - SDK Backend Conservation and IKS

### Conservation router endpoints

| Method | Path | Function | Evidence |
| ------ | ---- | -------- | -------- |
| GET | `/conservation/status` | `status` | `copilot_sdk/backend/conservation_router.py`, inside `create_conservation_router`, observed as `@router.get("/conservation/status", response_model=ConservationStatusResponse)`. |
| POST | `/conservation/what-if` | `what_if` | `copilot_sdk/backend/conservation_router.py`, inside `create_conservation_router`, observed as `@router.post("/conservation/what-if", response_model=ConservationWhatIfResponse)`. |

### IKS / Scoring endpoint evidence

* Search under `copilot_sdk/backend` for `@router.*iks`, `/iks`, `iks_score`, `IKSService`, and `institutional_knowledge` returned no matches.
* Diag 01 showed Trading `main.py` registers SDK scoring, transfer, evolution, and conservation routers, but this deep chase found no SDK backend IKS endpoint evidence.
* The conservation router exposes domain-level status and what-if endpoints; no per-strategy Trading conservation endpoint was observed inside `create_conservation_router`.

### SDK Verdicts

* P56 TRD-CONSERVATION-STRAT: SUPPLEMENT. SDK conservation exists, but no per-strategy Trading-specific conservation endpoint was observed.
* P58 TRD-IKS-WIRE: FULL. No `/iks` or IKS score endpoint evidence was found in SDK backend.

## Part 3 - context_router.py

### Endpoint inventory

| Method | Path | Function | Purpose inferred from code | Evidence |
| ------ | ---- | -------- | -------------------------- | -------- |
| GET | `/market-snapshot` | `market_snapshot` | Return cached market snapshot or default snapshot. | `context_router.py` L258-L262. |
| GET | `/ticker/{ticker}` | `ticker_detail` | Return cached ticker details or unknown source payload. | `context_router.py` L264-L276. |
| GET | `/portfolio-summary` | `portfolio_summary` | Return portfolio summary from analytics cache or data file. | `context_router.py` L279-L284. |
| GET | `/analytics` | `analytics` | Return cached analytics or empty analytics payload. | `context_router.py` L287-L292. |
| GET | `/trust-analysis` | `trust_analysis` | Return factor trust scores from imported trades. | `context_router.py` L295-L305. |
| GET | `/patterns` | `behavioral_patterns` | Return detected behavioral patterns from imported trades. | `context_router.py` L309-L327. |
| GET | `/conservation-breakdown` | `conservation_breakdown` | Return simplified proxy breakdown; authoritative endpoint remains `/api/conservation/status`. | `context_router.py` L330-L343. |
| GET | `/similar` | `similar_trades` | Return nearest seeded trades by factor-vector similarity. | `context_router.py` L368-L417. |
| POST | `/trade-metadata` | `save_trade_metadata` | Persist trade metadata keyed by `decision_id`. | `context_router.py` L420-L430. |
| GET | `/trade-metadata` | `get_trade_metadata` | Return saved trade metadata. | `context_router.py` L433-L434. |

### Trust / DK / Signal Confidence Coverage

* Endpoint path if present: `/trust-analysis`.
* Signal-confidence inversion coverage: UNCLEAR. `signal_confidence` appears as a factor name at L28 and as a `/similar` query argument at L377/L391, but no explicit inversion logic was observed in the searched context.
* DK weight / radar coverage: UNCLEAR. No `dk_weight` or `radar` references were found by the targeted search.
* Evidence:
  * `_trust_label` at L108 and `_trust_scores` at L124 compute trust labels/scores.
  * `/trust-analysis` at L295-L305 returns factors, implemented computers, trust scores, total trades, and hero insight.

### Pattern Coverage

* Endpoint path if present: `/patterns`.
* Pattern detector exposure: YES.
* Evidence:
  * `context_router.py` imports `detect_patterns` at L14.
  * `/patterns` is declared at L309-L310.
  * The endpoint calls `patterns = detect_patterns(trades)` at L320 and returns `patterns`, `total_patterns_detected`, `total_trades_analyzed`, and `most_severe_pattern` at L323-L326.

### Regime Recommendation Coverage

* Endpoint path if present: not in `context_router.py`.
* RegimeRecommender service present: YES, elsewhere.
* Evidence:
  * Repo search found `app/routers/regime.py` importing `RegimeRecommender` at L11 and calling `RegimeRecommender().recommend(...)` at L46.
  * `app/services/regime_recommender.py` defines `class RegimeRecommender` at L12 and `def recommend` at L13.

### Mock / Demo / Hardcoded Signal Review

| Line / Context | Signal | Classification | P-Issue? | Notes |
| -------------- | ------ | -------------- | -------: | ----- |
| L19-L20 `_DEFAULT_DATA_DIR` / `_DATA_DIR` | default | unclear | No | Default data directory, not inherently a production stub. |
| L45 fallback to `_DEFAULT_DATA_DIR` | fallback/default | demo-mode conditional acceptable | No | Reads packaged/default data if configured data path lacks file. |
| L62 `_empty_analytics()` returns `"source": "default"` and empty objects | default | production fallback | UNCLEAR | Produces empty analytics when cache absent; acceptable fallback or product gap depends on expected runtime. |
| L76-L77 `_default_market_snapshot()` returns ranging/VIX/ADX defaults | hardcoded/default | production stub / P-issue | YES | Market snapshot can fall back to hardcoded `ranging`, `20.0`, `25.0` values. |
| L108-L137 trust labels and default factor value `0.5` | default | algorithmic fallback | UNCLEAR | Default factor value may be neutral fallback for missing data. |
| L261 market snapshot fallback | default | production stub / P-issue | YES | Endpoint returns hardcoded default market snapshot when cache missing. |

### context_router Verdicts

* P53 TRD-TRUST-RADAR: SUPPLEMENT. Trust endpoint exists; DK weight/radar and signal-confidence inversion were not clearly present.
* P55 TRD-PATTERN-DETECTOR: SUPPLEMENT. Pattern endpoint wires to detector; deeper detector implementation exists, but runtime behavior was not tested.
* P85 TRD-REGIME-RECOMMEND: SUPPLEMENT. Regime recommender exists in `routers/regime.py`/service, not in `context_router.py`; endpoint integration should be reviewed directly.

## Part 4 - pattern_detector.py

### Function inventory

| Function | Purpose | Evidence |
| -------- | ------- | -------- |
| `detect_patterns` | Normalize/sort trades and run detector functions. | `services/pattern_detector.py` L10. |
| `_as_trade_dict` | Convert dict-like trade objects to dicts. | L33. |
| `_parse_time` | Parse datetimes/ISO strings. | L42. |
| `_minutes_between` | Compute minutes between previous exit and current entry. | L55. |
| `_clamp` | Clamp numeric severity to 0-1. | L63. |
| `_trade_id` | Extract trade ID. | L71. |
| `_number` | Parse numeric values. | L75. |
| `_pnl` | Extract P&L/computed P&L. | L83. |
| `_accuracy` | Compute verified-trade accuracy. | L90. |
| `_is_loss` | Detect negative P&L. | L97. |
| `_is_win` | Detect positive P&L. | L102. |
| `_size` | Parse trade size. | L107. |
| `_pattern` | Build normalized pattern response payload. | L111. |
| `_detect_revenge` | Detect quick re-entry after a loss. | L134. |
| `_detect_overconfidence` | Detect size increases after winning streaks. | L159. |
| `_is_oversized_after_streak` | Determine oversizing after streak. | L190. |
| `_detect_fomo` | Detect entries at day extremes. | L201. |
| `_detect_tilt` | Detect rapid-fire clusters in an hour. | L216. |
| `_detect_drawdown_chase` | Detect increased size while in drawdown. | L248. |
| `_detect_tod_degradation` | Detect time-of-day accuracy degradation. | L277. |

### Pattern inventory

* `revenge_trading`
* `overconfidence`
* `fomo`
* `tilt`
* `drawdown_chase`
* `tod_degradation`

### Return format

* JSON-serializable: YES
* Evidence:
  * `_pattern` returns a dict with string, float, int, and list-of-string fields: `name`, `display_name`, `description`, `frequency`, `severity`, `affected_trade_count`, `affected_trades`, and `recommendation`.
  * `detect_patterns` returns `list[dict]` and sorts by numeric `severity`.

### Stub / TODO review

* TODOs: none found by targeted scan.
* pass statements: none found by targeted scan.
* NotImplementedError: none found by targeted scan.
* stub signals: none found by targeted scan.

### P55 Verdict

* Verdict: SUPPLEMENT
* Remaining effort: likely router/API review and runtime validation rather than full algorithm implementation, because multiple concrete detector functions exist and `/patterns` exposes them.

## Part 5 - IBKR and CSV Connector Stub Context

### IBKR connector

* TODO/stub count: 2 `pass` matches from the configured TODO/stub scan context.
* Blocking primary import flow: UNCLEAR
* Optional feature only: NO
* Evidence:
  * `IBKRConnector` imports `IB` from `ib_insync` and raises if missing at `connectors/ibkr_connector.py` L11 and L27.
  * `import_trades` exists at L65 and returns `[]` when `connect()` fails at L67.
  * The primary import path reads `self._ib.fills()` at L70, converts fills to `NormalizedTrade`, and warns if no fills at L80.
  * `pass` at L51 is inside disconnect exception handling; `pass` at L140 is inside datetime parse fallback handling.
* P59 verdict: SUPPLEMENT
* P59 effort estimate: medium. Connector exists, but connection failure returns empty imports and runtime behavior with real IBKR/TWS was not validated.

### CSV connector

* TODO/stub count: 0 for TODO/pass/NotImplementedError/stub terms; `return []` appears for empty file/input/no headers.
* Blocking core parse/import: NO
* Edge-case only: YES
* Evidence:
  * `CSVConnector` exists at `connectors/csv_connector.py` L50.
  * `import_from_file` and `import_flexible` exist at L68-L76.
  * Empty content/no headers return `[]` at L79/L82.
  * `import_from_string` exists at L95 and similarly returns `[]` for empty content/no headers at L97/L100.
  * Rows are converted to `NormalizedTrade` at L115 and L165.
* P60 verdict: SUPPLEMENT
* P60 effort estimate: low. Core parser/import paths exist; likely needs edge-case/runtime validation, not full implementation from scratch.

## Final MAP Summary Table

| Prompt                     | Verdict | Remaining Effort | Key Evidence |
| -------------------------- | ------- | ---------------- | ------------ |
| P52 TRD-CLI-CORE           | SUPPLEMENT | Low-medium | `apps/trading/backend/cli.py` has argparse commands and core local flows; score/conservation are explicitly offline/proxy. |
| P53 TRD-TRUST-RADAR        | SUPPLEMENT | Medium | `/trust-analysis` exists; no `dk_weight`/`radar` references found. |
| P55 TRD-PATTERN-DETECTOR   | SUPPLEMENT | Low | `detect_patterns` implements six detectors and `/patterns` exposes it. |
| P56 TRD-CONSERVATION-STRAT | SUPPLEMENT | Medium | SDK conservation has status/what-if only; no per-strategy Trading endpoint observed. |
| P58 TRD-IKS-WIRE           | FULL | Medium-high | SDK backend search found no `/iks` or IKS score evidence. |
| P59 TRD-IBKR               | SUPPLEMENT | Medium | IBKR connector exists but returns `[]` on connection failure; real broker runtime unvalidated. |
| P60 TRD-CSV-IMPORT         | SUPPLEMENT | Low | CSV connector parses files/strings to `NormalizedTrade`; empty inputs return `[]`. |
| P61 TRD-CLI-FULL           | SUPPLEMENT | Medium | Broad CLI commands exist; several advanced flows are offline/proxy or blocked without backend state. |
| P62 TRD-PYPI               | SUPPLEMENT | Medium | `pyproject.toml` has `ci-trading` script and package wrapper; install/build not validated. |
| P85 TRD-REGIME-RECOMMEND   | SUPPLEMENT | Low-medium | `RegimeRecommender` exists and is used by `routers/regime.py`; context router does not expose it. |

## Diagnostic Limitations

* This diagnostic does not validate runtime behavior.
* This diagnostic does not run tests.
* This diagnostic does not prove feature completeness unless full implementation code was read.
* Verdicts are path/code-inspection verdicts only.
* Packaging, installability, broker connectivity, and API response behavior were not executed by instruction.

## Recommended Next Step

Use a focused MAP queue update that marks P58 as needing full IKS implementation and routes P52/P53/P55/P56/P59/P60/P61/P62/P85 to supplement/review prompts. The smallest immediate implementation prompt should target P58 IKS endpoint/service wiring because no SDK backend evidence was found.
