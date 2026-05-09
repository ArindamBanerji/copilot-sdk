# Purchasing Backend v2 Implementation Plan

## Executive Summary

Enhance the existing Purchasing backend without rewriting its structure. Preserve all existing endpoints and add richer item catalog data, `purchasing_seed_v2.json`, an analytics cache derived from that seed, a new analytics endpoint, a new similar-orders endpoint, an item profile endpoint, richer order metadata storage, and focused tests for the new behavior.

No SDK, scoring core, generic backend, frontend, Trading, DataOps, GAE, SOC, S2P, or ci-platform files should be changed. The existing `apps/purchasing/backend/app/main.py` already mounts the context router under `/api/context` and the evolution router under `/api`, so new context endpoints should be implemented in the existing Purchasing context router or an app-local helper imported by it.

## Source Contracts from Prompt 0

### Existing Endpoint Shapes

Existing context endpoints are implemented in `apps/purchasing/backend/app/context_router.py`:

- `GET /api/context/today-summary` returns `{date, day_of_week, weather, events}`.
- `GET /api/context/items` returns the raw list from `app/items.json`, with a one-item fallback if that file is missing.
- `GET /api/context/waste-history/{item}` normalizes the item with lowercase underscore keys and returns `{item, waste_pct, count}`.
- `GET /api/context/weather` returns cached weather or offline weather factor data.
- `POST /api/context/order-metadata` requires `decision_id`, currently stores a filtered metadata record keyed by string decision id, and returns `{decision_id, metadata}`.
- `GET /api/context/order-metadata` returns the full metadata object.

Existing non-context endpoints that must continue working:

- `GET /health`
- `POST /api/score`
- `POST /api/learn`
- `GET /api/fingerprint`
- `GET /api/trajectory`
- `GET /api/history`
- `GET /api/evolution/variants`

### Existing Loader and Path Patterns

The Purchasing context router uses:

- `_APP_DIR = Path(__file__).resolve().parent`
- `_DATA_DIR = Path(__file__).resolve().parents[1] / "data"`
- `_load_json(path: Path)` to read UTF-8 JSON.
- `_write_json(path, payload)` to write sorted, indented UTF-8 JSON.
- `_item_key(item)` to normalize item route params by stripping, lowercasing, and replacing spaces with underscores.

Keep these patterns. If a helper is added, it should accept parsed data or explicit paths so tests can keep using patched temp data.

### Existing Test Pattern and Isolation Needs

`apps/purchasing/backend/tests/conftest.py` currently copies these data files into a temporary data directory:

- `waste_history.json`
- `weather_cache.json`
- `evolution_fixtures.json`

It creates an isolated temp `order_metadata.json` as `{}` and monkeypatches:

- `context_router._DATA_DIR`
- `app.main.DATA_DIR`

`app/items.json` is not currently copied or isolated. Tests read it through `_APP_DIR / "items.json"`. If future tests need temp item catalog mutation, add `_APP_DIR` patching and copy `items.json`; otherwise keep item tests read-only.

For v2 tests, update the fixture to copy:

- `purchasing_seed_v2.json`
- `analytics_cache.json`

Metadata tests must continue to mutate only the temp metadata file, not the repo fixture.

### Purchasing Preset Contract

The Purchasing preset contract is:

- Categories: `protein`, `produce`, `dairy`, `dry_goods`, `beverages`
- Actions: `order_as_planned`, `order_more`, `order_less`, `skip`
- Factors: `expected_demand`, `day_of_week`, `weather_forecast`, `event_flag`, `historical_waste`, `supplier_lead_time`

The current compact seed uses `order_id`, `item`, `category`, `day_type`, `action_taken`, `quantity_ordered`, `quantity_remaining`, `stockout`, `is_correct`, and nested `factors`.

### Existing Evolution Fixture Shape

`apps/purchasing/backend/data/evolution_fixtures.json` contains a top-level `variants` list. Current variants include fields such as:

- `id`
- `event_type`
- `variant_id`
- `artifact_type`
- `description`
- `before_state`
- `after_state`
- `graph_context`
- `metadata`
- `impact`
- `magnitude`
- `timestamp`
- `source_copilot`
- `source_rule`
- `warm_start_prior`

Current fixtures do not have explicit `match` fields. Item profile matching must handle both current no-match fixtures and future variants with explicit match metadata.

## Files to Modify

- `apps/purchasing/backend/app/context_router.py`
- `apps/purchasing/backend/app/items.json`
- `apps/purchasing/backend/data/waste_history.json`, only if item profile data needs additional history
- `apps/purchasing/backend/data/evolution_fixtures.json`, if adding explicit match fields
- `apps/purchasing/backend/data/order_metadata.json`, only if a richer default fixture is needed
- `apps/purchasing/backend/tests/test_purchasing_backend.py`
- `apps/purchasing/backend/tests/conftest.py`, to copy v2 data and optionally isolate `items.json`

## Files to Create

- `apps/purchasing/backend/data/purchasing_seed_v2.json`
- `apps/purchasing/backend/data/analytics_cache.json`

Optional, only if it keeps the router small and analytics logic testable:

- an app-local analytics helper module under `apps/purchasing/backend/app/`

Do not create unrelated scripts unless needed and documented.

## Forbidden Files

- `apps/purchasing/backend/app/main.py`, unless router mounting is proven to require a change. Prompt 0 found no such need.
- `copilot_sdk/scoring/**`
- `copilot_sdk/backend/**`
- `copilot_sdk/frontend/**`
- `apps/trading/**`
- `apps/dataops/**`
- `GAE/**`
- `SOC/**`
- `S2P/**`
- `ci-platform/**`
- `graph-attention-engine-v50/**`
- `gen-ai-roi-demo-v4-v50/**`
- `s2p-copilot/**`

Do not use git operations.

## Item Catalog Contract

Enhance every item entry in `apps/purchasing/backend/app/items.json`.

Preserve existing fields:

- `item_id`
- `name`
- `category`
- `unit`
- `par_level`
- `supplier_lead_time`
- `default_quantity_lbs`, if present in a future record

Add fields:

- `display_name`
- `emoji`
- `on_hand_qty`
- `unit_price`
- `supplier`
- `event_sensitivity`
- `usage_range`
- `source`

Recommended category emoji defaults:

- `protein`: meat/plate-style emoji
- `produce`: leafy/produce-style emoji
- `dairy`: dairy-style emoji
- `dry_goods`: grain/package-style emoji
- `beverages`: `☕`

Keep `name` as the normalized key used by routes and waste history. Use `display_name` for human-readable labels.

## purchasing_seed_v2 Contract

Create `apps/purchasing/backend/data/purchasing_seed_v2.json` with exactly 20 orders.

Each order must include:

- `order_id`
- `item`
- `display_name`
- `category`
- `quantity_lbs`
- `day_of_week`
- `date`
- `is_event_day`
- `event_type`
- `expected_demand`
- `day_of_week_factor`
- `weather_forecast`
- `event_flag`
- `historical_waste`
- `supplier_lead_time`
- `action_taken`
- `is_correct`
- `waste_pct`
- `waste_cost_dollars`
- `stockout_occurred`
- `stockout_cost_dollars`
- `total_cost_dollars`

Required data properties:

- 20 total orders.
- Category counts roughly:
  - `protein`: 6
  - `produce`: 6
  - `dairy`: 4
  - `dry_goods`: 2
  - `beverages`: 2
- All preset categories represented.
- Overall accuracy near 71%. With 20 records, prefer 14/20 = 70%.
- Event days lower accuracy than non-event.
- Friday produce weak, especially over-ordering and waste.
- Historical waste meaningful: high waste should correlate with lower accuracy or `order_less` wins.
- Weather weak/noisy: include mixed outcomes at similar weather levels.
- Event days show under-ordering or stockout patterns.
- Similar clusters exist for common protein/event queries.

All factor values must be in `[0, 1]`.

## Analytics Contract

Create `apps/purchasing/backend/data/analytics_cache.json`. It must be computed from `purchasing_seed_v2.json`, not independently invented.

Required top-level sections:

- `contrast_card`
- `counterfactual`
- `category_accuracy`
- `day_of_week`
- `event_impact`
- `waste_cost_analysis`
- `ae_impact`
- `portfolio_summary`

Recommended consistency definitions:

- `total_orders = len(seed)`
- `accuracy = correct orders / total orders`
- `category_accuracy` groups by `category`
- `day_of_week` groups by `day_of_week`
- `event_impact` compares `is_event_day == true` and `false`
- `waste_cost_analysis` sums `waste_cost_dollars`
- `ae_impact` groups by `ae_managed` if included in seed, or uses item/evolution fixture matches if the seed omits it
- `portfolio_summary` includes `total_orders`, `accuracy`, `stockout_rate`, `total_waste_cost_dollars`, `total_stockout_cost_dollars`, `total_cost_dollars`, and category counts

Tests should recompute key summaries from seed and compare to cache:

- total orders
- accuracy
- category counts/accuracy
- event-day versus non-event counts/accuracy
- total waste and stockout costs
- portfolio summary values

## Metadata v2 Contract

Keep existing `POST /api/context/order-metadata` and `GET /api/context/order-metadata` routes and response shape.

Change storage from a fixed allowlist to accepting and storing arbitrary JSON fields keyed by `decision_id`. The only required field should be `decision_id`.

New metadata fields include:

- `display_name`
- `emoji`
- `category`
- `quantity`
- `unit`
- `day`
- `events`
- `cost`
- `stockout_estimate`
- `waste_estimate`
- `risk_ratio`
- `auto_computed_factors`

Backward compatibility requirements:

- Existing v1 fields still round-trip: `item`, `quantity_lbs`, `day`, `events`.
- Missing `decision_id` still returns HTTP 400 with a message containing `decision_id`.
- Return shape remains `{decision_id, metadata}`.

## New Endpoints

### GET /api/context/analytics

Return `analytics_cache.json`.

Preferred behavior:

- If `analytics_cache.json` exists, return it.
- If missing, return a safe object with expected top-level keys and `source: "default"`, or return an HTTP error if the implementation chooses strict cache semantics. Tests should exercise the present-file path.

### GET /api/context/similar

Required query params:

- `category`
- `expected_demand`
- `day_of_week`
- `weather_forecast`
- `event_flag`
- `historical_waste`
- `supplier_lead_time`

Optional query param:

- `n`, default `5`

Implementation requirements:

- Use pure Python cosine similarity. Do not use numpy.
- Read from `purchasing_seed_v2.json`.
- Canonical vector order:
  - `expected_demand`
  - `day_of_week_factor`
  - `weather_forecast`
  - `event_flag`
  - `historical_waste`
  - `supplier_lead_time`
- Treat query param `day_of_week` as the numeric `day_of_week_factor` value.
- Filter to matching category.
- Include results with `similarity > 0.85`.
- Sort descending by similarity.
- Return at most `n` rows in `similar`.
- Return `count` as total matches above threshold before limiting.
- If the seed is missing or malformed, return `{"similar": [], "count": 0}`.

Each result should include:

- `order_id`
- `item`
- `category`
- `day_of_week`
- `is_event_day`
- `quantity_lbs`
- `waste_pct`
- `stockout_occurred`
- `is_correct`
- `similarity`

### GET /api/context/item/{name}/profile

Normalize `{name}` with `_item_key`.

If item is missing:

```json
{"error": "Item not found", "name": "<input name>"}
```

If found, return:

- `item`
- `waste_history`
- `waste_avg`
- `waste_trend`
- `ae_rules`
- `ae_managed`

Recommended behavior:

- `item` is the enhanced catalog record.
- `waste_history` is the list from `waste_history.json`.
- `waste_avg` is the mean of waste history values, or `null` if no values exist.
- `waste_trend` can be `up`, `down`, `flat`, or `unknown`.
- `ae_rules` comes from `evolution_fixtures.json["variants"]`.
- `ae_managed` is `true` when one or more matching approved AE rules apply.

AE matching must be safe when match fields are absent:

- If `rule.match.categories` is missing, treat the rule as broadly applicable only if the implementation intentionally chooses that policy, or ignore it safely.
- If categories are present, match the item category.
- If `event_required` is present, only match event-sensitive profile contexts or return the rule with that requirement visible.
- Malformed JSON in string fields such as `metadata`, `graph_context`, or `warm_start_prior` should not break the endpoint.

If adding explicit match fields to `evolution_fixtures.json`, use:

- `V-PUR-FRIDAY-001`: `categories: ["produce"]`, `day: "friday"`
- `V-PUR-EVENT-001`: `categories: ["protein"]`, `event_required: true`
- `V-PUR-DAIRY-001`: `categories: ["dairy"]`

## Tests

Add these tests to `apps/purchasing/backend/tests/test_purchasing_backend.py` while keeping all existing tests passing:

- `test_items_enhanced_fields`
- `test_analytics`
- `test_analytics_consistent_with_seed_v2`
- `test_similar_orders`
- `test_item_profile`
- `test_item_profile_unknown`
- `test_order_metadata_v2_fields`
- `test_seed_v2_exists`
- `test_item_profile_ae_rule_matching`, if match fields are added

Test expectations:

- `test_items_enhanced_fields`: known item includes all enhanced fields and preserves existing fields.
- `test_seed_v2_exists`: seed has 20 records, required fields, valid categories/actions, factor values in range, and all categories represented.
- `test_analytics`: endpoint returns all required top-level sections.
- `test_analytics_consistent_with_seed_v2`: recompute counts, accuracy, category accuracy, event impact, waste/stockout totals, and selected portfolio fields from seed and compare to cache.
- `test_similar_orders`: query a known protein/event cluster and assert descending similarities, threshold `> 0.85`, limited row count, and expected response fields.
- `test_item_profile`: known item returns catalog item, waste stats, and AE fields.
- `test_item_profile_unknown`: unknown item returns `{"error": "Item not found", "name": name}`.
- `test_order_metadata_v2_fields`: POST richer metadata and assert every v2 field round-trips.
- `test_item_profile_ae_rule_matching`: only add if explicit match fields are added to evolution fixtures.

Fixture update:

- Copy `purchasing_seed_v2.json` and `analytics_cache.json` into temp data.
- Continue creating isolated `order_metadata.json`.
- Keep temp SQLite db behavior unchanged.
- If item tests need temp-only item mutations, copy `items.json` into temp app data and monkeypatch `_APP_DIR`; otherwise keep read-only item tests against source `app/items.json`.

## Validation Commands

Run from repo root:

```powershell
python -m pytest apps/purchasing/backend/tests/ -v --timeout=120
python -m pytest tests/ -q --timeout=120
```

If `pytest-timeout` is not installed and `--timeout` is rejected, rerun without the timeout flag and record that the plugin is unavailable:

```powershell
python -m pytest apps/purchasing/backend/tests/ -v
python -m pytest tests/ -q
```

## Prompt Verification Pass

- Existing endpoints are preserved; new endpoints are added under the existing context router.
- Analytics/seed drift is avoided by deriving `analytics_cache.json` from `purchasing_seed_v2.json` and testing consistency.
- No SDK/core edits are required.
- New tests cover new endpoints, richer metadata, seed existence, and analytics consistency.
- Item profile handles both current no-match evolution fixtures and future explicit match fields safely.
- The plan is self-contained and constrained to Purchasing backend files plus this plan document.

## Residual Risks

- The prompt names a v2 seed but forbids `copilot_sdk/scoring/**`; therefore the seed must live in `apps/purchasing/backend/data/`.
- `items.json` is under `app/`, not `data/`, and current fixture does not isolate it. Avoid mutating it in tests unless `_APP_DIR` isolation is added.
- Exact analytics sub-shapes are not already defined by existing code. The implementation must define stable shapes and then test them.
- Evolution fixtures currently have no match fields, so item profile logic must be defensive and tests should cover no-match behavior unless match fields are added.
