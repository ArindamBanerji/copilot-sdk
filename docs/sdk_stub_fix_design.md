## Stub Fix Design — copilot-sdk (5 endpoints)

### Investigation scope and current drift

This investigation started from the current session baseline: DataOps backend 490 passed; SDK root 4,124 passed, 301 skipped, and 1 xfailed without `GRAPH_DSN`. It used read-only source inspection and live GET probes against the existing stack.

The worktree contains an in-progress, uncommitted implementation for the two Trading detail endpoints. The analysis below distinguishes the behavior of the running stack and the original handler path from that newer code. The newer code follows much of the recommended design, but it still needs review and regression coverage before it can be treated as the implementation baseline.

| Endpoint | Route location | Handler |
|---|---|---|
| `GET /api/trading/trades/{trade_id}` | `apps/trading/backend/app/routers/journal.py:84` | `get_trade` via `@router.get("/trades/{trade_id}", response_model=None)` |
| `GET /api/trading/evidence/{trade_id}` | `apps/trading/backend/app/routers/evidence.py:28` | `get_evidence` via `@router.get("/evidence/{trade_id}")` |
| `GET /api/context/analytics` | `apps/trading/backend/app/context_router.py:631` | `analytics` via `@router.get("/analytics")` |
| `GET /api/di/sources` | `copilot_sdk/backend/di_router.py:139` | `sources` via `@router.get("/di/sources", response_model=DIProfilesResponse)` |
| `GET /api/trajectory` | `copilot_sdk/backend/scoring_router.py:302` | `trajectory` via `@router.get("/trajectory", response_model=TrajectoryResponse)` |

Line numbers refer to the inspected worktree and may move as the concurrent Trading work is completed.

### Pattern: How Working Endpoints Access Live Data

The working endpoints consistently receive a scorer or GraphStore provider when their router is assembled. They resolve that provider for each request, scope reads by domain, and return the canonical graph projection rather than maintaining a second cache.

`GET /api/self/decisions` in `copilot_sdk/backend/self_computation_router.py` resolves the injected GraphStore, calls `get_decisions(domain, limit=...)` and `get_verified_decisions(domain)`, and merges verified fields by `decision_id`. That merge supplies the outcome fields stored separately from the original decision.

`GET /api/fingerprint` in `copilot_sdk/backend/scoring_router.py` resolves the injected scorer with `get_scorer()`, invokes `scorer.fingerprint()` through `graph_call`, and computes the fingerprint from the domain's verified decisions and preset factor names. It does not replace absent factor observations with neutral scores.

`GET /api/conservation/status` in `copilot_sdk/backend/conservation_router.py` resolves the injected state provider, reaches the scorer's GraphStore, and reads verified decisions and category counts from the live store. It uses the same graph-backed state as scoring and returns an availability error if that state cannot be read rather than fabricating a healthy default.

The five fixes should use the same pattern:

1. Inject or resolve the application-owned scorer/GraphStore provider.
2. Read the canonical domain-scoped decision and verified-outcome projections.
3. Normalize old and current record representations at one boundary.
4. Return an explicit 404 or availability state when data is absent.
5. Do not turn missing observations into `0.50`, empty objects, or invented business values.

The relevant GraphStore contract already includes:

- `get_decision(decision_id, domain, include_outcome=False) -> dict[str, Any] | None`
- `get_decisions(domain, category=None, limit=400) -> list[dict[str, Any]]`
- `get_all_decisions(domain) -> list[dict[str, Any]]`
- `get_verified_decisions(domain) -> list[dict[str, Any]]`

Canonical decision fields include `decision_id`, `domain`, `entity_id`, `category`, `recommended_action`, `confidence`, `factor_vector`/`factors`, `probabilities`, `status`, `metadata`, and `created_at`. The verified projection can add `actual_action`, `is_correct`, `verified_at`, and `outcome_metadata`. Migrated AGE rows may also carry `factors_json`, have an empty `factor_names` list, or retain legacy correctness on `correct`.

### Endpoint 1: `/api/trading/trades/{trade_id}`

- **File:** `apps/trading/backend/app/routers/journal.py:84`
- **Current:** The deployed handler searches `_journal_records`, which combines imported trades, manual entries, and `GraphStore.get_all_decisions("trading")`. `_normalize_trade` reads business fields from the row and metadata, but reads factors only from a `factors` mapping. A representative migrated decision has real `factor_vector` and `factors_json` values while `factors` and `factor_names` are empty. The running endpoint therefore returned a real ID, category, action, and confidence, but returned `{}` for factors and metadata and `null` for ticker, entry/exit prices, size, entry/exit times, strategy tag, subcategory, regime, P&L, reflection, and notes.
- **Fix:** Resolve the application GraphStore and call `get_decision(trade_id, "trading", include_outcome=True)` first. Map canonical fields directly: `decision_id` to `trade_id`, `entity_id` or metadata ticker to `ticker`, `created_at` to the trade timestamp, `category`, `recommended_action`, `confidence`, and verified outcome fields. Normalize factors in this order: a nonempty `factors` mapping; parsed `factors_json`; `factor_vector` zipped to a nonempty `factor_names`; or `factor_vector` zipped to the Trading preset's factor names when its length matches the preset. Merge decision metadata and outcome metadata without discarding either. Preserve imported/manual-record fallback only for records that are not in GraphStore. Return 404 when neither source contains the requested ID.
- **Fix, business fields:** Read ticker, prices, size, times, strategy, subcategory, regime, P&L, reflection, and notes only from their explicit decision/outcome metadata keys. Omit unavailable optional fields or expose the existing response's explicit missing state. Do not infer prices, P&L, or narrative text from confidence or correctness. Future score/learn writes should persist these fields in metadata if the product requires full historical trade reconstruction.
- **In-progress code:** The current uncommitted handler already calls `get_decision(..., include_outcome=True)` and uses a shared trade-detail mapper. Its factor helper handles a mapping and vectors, including preset-name fallback. Review it for `factors_json` compatibility and for preservation of both decision and outcome metadata.
- **Complexity:** moderate
- **Risk:** Historical graph rows do not contain all journal-specific business data, so this change can eliminate avoidable nulls but cannot reconstruct values that were never persisted. Factor-name order must come from the preset only when the vector length matches exactly. The imported/manual fallback must not shadow a newer graph record.

### Endpoint 2: `/api/trading/evidence/{trade_id}`

- **File:** `apps/trading/backend/app/routers/evidence.py:28`
- **Current:** The deployed handler locates a normalized journal record and builds factor evidence through `_factors_for`. It tries a factor mapping, selected metadata/context fields, and `compute_factors(context)`, then fills every absent preset factor with `0.50`. On a representative migrated graph row, the normalization step lost its real vector. Eight of the current ten Trading factors were consequently exactly `0.50`; two became `1.0` through recomputation on incomplete context. The prompt's count of eight factors reflects an older preset; the inspected Trading preset and live payload contain ten.
- **Fix:** Make this endpoint depend on the same canonical decision loader and factor normalizer as trade detail. Call `get_decision(trade_id, "trading", include_outcome=True)` and map the stored factor vector without recomputing factors from incomplete context. Build evidence labels and descriptions from the current Trading preset/config while retaining the stored numeric score. Remove the unconditional `setdefault(name, 0.5)` path. If a particular factor is genuinely unavailable, mark it unavailable or omit it according to the response model; do not represent missing evidence as a neutral observation. Source similar-trade and counterfactual evidence from verified graph decisions, using `is_correct`, outcome metadata, and compatible categories/factor vectors.
- **Dependency:** Reuse the Endpoint 1 loader/normalizer so journal and evidence cannot interpret the same decision differently.
- **In-progress code:** The uncommitted handler now performs a direct GraphStore lookup and delegates to the shared trade-detail mapper. This is the correct direction. Confirm that it parses `factors_json`, rejects vector-length mismatches, and never falls back to neutral factor values.
- **Complexity:** moderate
- **Risk:** Removing the default exposes genuinely sparse legacy rows and may require the response model/frontend to render an unavailable factor. Recomputing historical factors would be misleading because the original scoring context and preset version may have changed.

### Endpoint 3: `/api/context/analytics` (Trading)

- **File:** `apps/trading/backend/app/context_router.py:631`
- **Current:** The route uses the context router's response materializer when available, otherwise reads `request.app.state.graph_store`. The materializer already supplies both all decisions and verified decisions. The Trading analytics builder currently consumes only the all-decisions list. The inspected 133 KB response contained 12 nulls: `counterfactual.dollars_saved`, `regime_analysis.regime`, and `rolling_10[0..9].correct`. The ten rolling entries were recent pending decisions, so their correctness was unknown. `dollars_saved` and `regime` are explicitly emitted as `None`. Other aggregates, including the portfolio win rate, are computed from real graph data.
- **Fix:** In the materializer callback, pass both `shared["decisions"]` and `shared["verified"]` to the analytics builder. Merge verified fields into decisions by `decision_id`, following `/api/self/decisions`. Compute rolling correctness only from the most recent verified decisions, ordered by `verified_at` with `created_at` as a compatibility fallback. Derive the regime from the newest applicable decision metadata (`regime_tag` or `regime_metadata.regime`) or from the app's `RegimeMonitor`; label it unavailable when neither exists. Compute monetary impact only from persisted outcome/decision metadata with an explicit currency and definition. If no monetary observations exist, return an explicit unavailable state supported by the response contract rather than an invented amount.
- **Store requirements:** Existing `get_all_decisions("trading")` and `get_verified_decisions("trading")` methods are sufficient. No new store method is needed. A small shared `merge_verified_fields`/metadata-normalization helper would avoid duplicating the self-computation router's logic.
- **Complexity:** moderate
- **Risk:** Changing rolling calculations from all decisions to verified decisions changes the series denominator and ordering, which is correct but visible. Regime metadata has legacy key variants. A real `dollars_saved` figure remains blocked for historical rows that lack monetary outcome metadata; response-schema changes must be coordinated if the current field cannot express unavailable data without `null`.

### Endpoint 4: `/api/di/sources` (DataOps)

- **File:** `copilot_sdk/backend/di_router.py:139`
- **Current:** `create_di_router` owns a private in-memory profile cache populated only by the shared router's refresh endpoint. `sources()` simply returns `profiles()`. DataOps independently profiles its `airflow`, `dbt`, and `snowflake` connectors at startup and exposes those real summaries through its custom `/api/di/profiles` routes. Because the two routes do not share state, `/api/di/sources` reported all three sources as unprofiled; each source had `age_seconds: null` and `latest_profile: null`, producing the six observed nulls. Live probes of DataOps' custom profile endpoints returned populated quality, freshness, completeness, consistency, validation, record-count, timestamp, and overall-quality data for the same sources.
- **Fix:** Give `create_di_router` an injected profile-state provider, or an initial/cache provider that returns the application-owned profile summaries. Have both `/di/profiles` and `/di/sources` render from that provider. For the narrow DataOps assembly, an acceptable minimal change is to register a DataOps-owned `/api/di/sources` alias backed by `_dataops_profile_summaries` and remove the duplicate shared route before mounting, matching the existing duplicate handling for `/api/di/profiles` and `/api/di/intelligence-map`. The provider-based shared-router change is preferable if other copilots need the same contract.
- **Data source:** This endpoint describes connector profiler state, so the authoritative source is the app's live profiler registry/profile cache rather than DecisionStore. GraphStore should be used only if profiler snapshots are deliberately persisted there under a defined schema.
- **Complexity:** moderate for provider injection; trivial for a DataOps-specific route alias
- **Risk:** FastAPI resolves duplicate paths in registration order, so adding another handler without removing the existing shared route can leave the stale handler active. Consolidating caches may change refresh visibility and needs a test proving `/di/profile/{source}/refresh`, `/di/profiles`, and `/di/sources` all observe the same state.

### Endpoint 5: `/api/trajectory` (Purchasing)

- **File:** `copilot_sdk/backend/scoring_router.py:302`
- **Current:** Trading and Purchasing mount the same `create_scoring_router` factory at `/api`, pass a `FreshScorerProxy` wrapped by `GateEnforcedScorer`, and resolve the scorer through the same closure. The route calls `scorer.trajectory()` through `graph_call`. `CompoundingScorer.trajectory()` reads `GraphStore.get_verified_decisions(domain)` and `compute_trajectory` computes cumulative correctness. Its initial baseline point is intentionally `0.50`; it emits a flat `0.50` trajectory only when it sees no usable outcomes. The current live Purchasing endpoint no longer reproduces the reported nine defaults: it returned 147 points, only the initial point was `0.50`, the last point represented 1,456 decisions with win rate `0.819`, and current IKS was `70.5`. Trading followed the same live path and also returned real values.
- **Fix:** Do not make an endpoint-specific change without a reproducing fixture. Add a regression test that seeds Purchasing verified decisions through the same GraphStore path and asserts that points after the baseline reflect `is_correct`. If the old failure is reproduced with migrated data, normalize legacy outcome projection in the GraphStore boundary: prefer outcome `is_correct`, then decision `is_correct`, then legacy decision `correct`. Preserve the intentional initial `0.50` baseline. Verify startup bundle restore and auto-seed complete before the first trajectory request; do not add a Purchasing-only in-memory trajectory cache.
- **Why Trading differed in the earlier probe:** The router setup is equivalent. The plausible difference is runtime/store state: Purchasing was probed before restore/seed completed, had no verified rows visible to its scorer, or used legacy rows whose correctness was not projected into `is_correct`. Trading's additional regime/materializer wiring does not serve this direct route.
- **Complexity:** trivial regression coverage if the current behavior holds; moderate only if legacy projection normalization is required
- **Risk:** A shared GraphStore projection change affects all domains and must preserve current outcome precedence. Treating the baseline `0.50` point as a defect would break the designed trajectory contract. The original finding is stale on the current stack, so speculative production changes carry more risk than value.

### Implementation Order

1. **Unify `/api/di/sources` profile state.** It is a contained split-cache defect with live data already available and no dependency on the Trading changes.
2. **Add the Purchasing trajectory regression fixture.** Establish whether any implementation change remains necessary. Apply legacy projection normalization only if the fixture reproduces the flat-default behavior.
3. **Finish the canonical Trading decision loader and factor normalizer.** Review the in-progress Endpoint 1 work, add `factors_json` compatibility, and test current plus migrated records.
4. **Wire Trading evidence to that loader.** Remove neutral defaults only after the shared factor contract and unavailable behavior are covered.
5. **Correct Trading analytics.** Reuse the verified merge helper, then address regime and monetary availability with explicit response semantics.

Endpoints 1 and 2 should land together or in that order because evidence depends on the trade-detail normalization contract. Endpoint 3 can reuse their compatibility helper but otherwise has no runtime dependency. Endpoints 4 and 5 are independent.

### Blockers

- Historical Trading decisions do not consistently persist ticker, entry/exit prices, size, timestamps, strategy tag, regime, P&L, reflection, or notes. No store method can reconstruct fields that were never written. A metadata backfill or forward persistence change is required for complete historical trade detail.
- `counterfactual.dollars_saved` cannot be computed honestly unless decisions/outcomes persist a defined monetary impact and currency. The current graph data supports an unavailable result, not a fabricated number.
- The Purchasing flat-`0.50` trajectory is not reproducible on the current live stack. A captured failing payload or legacy-row fixture is required before changing shared production logic.
- The Trading trade-detail and evidence handlers are already being modified in the shared worktree. Their final diff and tests must be reviewed against this specification to avoid duplicate or conflicting edits.
- DataOps `/api/di/sources` is profiler data, not decision data. Wiring it directly to DecisionStore would preserve the wrong abstraction; it needs the same application-owned profiler state used by the working DataOps profile endpoints.
