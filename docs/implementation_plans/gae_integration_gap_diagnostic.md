# GAE Integration Gap Diagnostic

## Executive summary

* Overall verdict: GAE DK learning is inactive in the runtime copilot paths reviewed here. GAE centroid learning is active in memory for SDK/S2P learn paths and conditionally active for SOC, but runtime DK re-estimation and L5 DKWeight persistence are not wired.
* Whether this blocks P-WELFORD-B scoping: YES. P-WELFORD-B cannot be scoped as a storage-only Welford add-on; it first needs a runtime DK learning bridge or explicit Roadmap decision that Welford only covers future DK writes.
* Whether implementation should proceed: NO for P-WELFORD-B implementation until Roadmap selects a DK runtime wiring option. YES for Roadmap review of this diagnostic.
* Top risks:
  * Product/demo claims around trust-trap discovery, DK changes over time, and compounding intelligence are not supported by runtime SDK/S2P evidence unless they refer only to GAE library tests or experimental scripts.
  * P25 L5 DKWeight storage exists, but no runtime path found that calls `update_dk_weights()`.
  * `CompoundingScorer.from_preset()` constructs `ProfileScorer(...)` directly, so it does not enable `ProfileScorer.for_soc_twophase()` defaults that include `CoordinateDescentEstimator`.
  * SOC also constructs `ProfileScorer(...)` directly and has `LEARNING_ENABLED = False` by default, so SOC DK learning is not active by default.

## Evidence summary

### Scan 1 - Construction paths

Command run:

```powershell
Get-ChildItem -Path ".\copilot-sdk\copilot_sdk\scoring",".\copilot-sdk\apps\trading\backend",".\copilot-sdk\apps\purchasing\backend",".\copilot-sdk\apps\dataops\backend",".\s2p-copilot\backend\app",".\gen-ai-roi-demo-v4-v50\backend\app" -Recurse -Include "*.py" | Select-String -Pattern "ProfileScorer|CompoundingScorer|from_preset|for_soc_twophase|reestimate_dk"
```

Key findings:

* `CompoundingScorer.from_preset()` constructs `ProfileScorer(...)` directly at `copilot-sdk/copilot_sdk/scoring/scorer.py:191-195`.
* Trading auto-seed constructs `CompoundingScorer.from_preset(..., consolidation_enabled=True)` at `copilot-sdk/apps/trading/backend/app/main.py:214-219`; the app runtime constructs `FreshScorerProxy` and mounts `create_scoring_router()` at `copilot-sdk/apps/trading/backend/app/main.py:262-272`.
* Purchasing auto-seed constructs `CompoundingScorer.from_preset(..., consolidation_enabled=True)` at `copilot-sdk/apps/purchasing/backend/app/main.py:205-210`; the app runtime constructs `FreshScorerProxy` and mounts `create_scoring_router()` at `copilot-sdk/apps/purchasing/backend/app/main.py:336-346`.
* DataOps auto-seed constructs `CompoundingScorer.from_preset(..., consolidation_enabled=True)` at `copilot-sdk/apps/dataops/backend/app/main.py:229-234`; the app runtime constructs `FreshScorerProxy` and mounts `create_scoring_router()` at `copilot-sdk/apps/dataops/backend/app/main.py:355-378`.
* S2P constructs `CompoundingScorer.from_preset("s2p", graph_store=..., reward_function=...)` at `s2p-copilot/backend/app/main.py:61-72`.
* SOC constructs `ProfileScorer(...)` directly in `SOCDomainConfig.build_profile_scorer()` at `gen-ai-roi-demo-v4-v50/backend/app/domains/soc/config.py:692-708`.

Gaps/unknowns:

* No construction evidence found that Trading, Purchasing, DataOps, S2P, or SOC use `ProfileScorer.for_soc_twophase()` in production runtime.

### Scan 2 - DK estimation calls

Command run:

```powershell
Get-ChildItem -Path ".\copilot-sdk\copilot_sdk\scoring",".\graph-attention-engine-v50\gae" -Recurse -Include "*.py" | Select-String -Pattern "reestimate_dk|CoordinateDescentEstimator|dk_estimator|_dk_weights|estimate("
```

Key findings:

* `CoordinateDescentEstimator` exists at `graph-attention-engine-v50/gae/dk_estimator.py:34-80`.
* Its `estimate()` returns weights with shape `(n_categories, n_dims)` at `graph-attention-engine-v50/gae/dk_estimator.py:80-198`.
* `ProfileScorer.for_soc_twophase()` wires `CoordinateDescentEstimator()` by default at `graph-attention-engine-v50/gae/profile_scorer.py:373-390`.
* `ProfileScorer.score()` only uses `_dk_weights` when a learning strategy exists, the category is in `VARIANCE_LEARNING`, and `_dk_weights` is not `None` at `graph-attention-engine-v50/gae/profile_scorer.py:457-466`.
* `ProfileScorer.update()` only buffers decisions for DK when `_learning_strategy` exists and the category is in `VARIANCE_LEARNING` at `graph-attention-engine-v50/gae/profile_scorer.py:895-903`.
* `ProfileScorer.reestimate_dk()` exists and calls `dk_estimator.estimate(...)` at `graph-attention-engine-v50/gae/profile_scorer.py:1050-1065`.

Gaps/unknowns:

* No runtime call to `reestimate_dk()` was found in SDK/S2P/SOC app learn/outcome paths.

### Scan 3 - Conservation monitoring

Command run:

```powershell
Get-ChildItem -Path ".\copilot-sdk\copilot_sdk\scoring",".\copilot-sdk\copilot_sdk\backend" -Recurse -Include "*.py" | Select-String -Pattern "ConservationMonitor|OLSMonitor|check_conservation|conservation_check|compute_theta_min|derive_theta_min|conservation_status|count_verified|count_correct"
```

Key findings:

* SDK conservation metrics are centralized in `compute_conservation_metrics()` at `copilot-sdk/copilot_sdk/backend/conservation_utils.py:45-91`.
* The helper uses graph counts and `count_categories_with_n(domain, 1)` at `copilot-sdk/copilot_sdk/backend/conservation_utils.py:53-56` and `copilot-sdk/copilot_sdk/backend/conservation_utils.py:188-195`.
* SDK `/learn` persists conservation state after `scorer.learn(...)` at `copilot-sdk/copilot_sdk/backend/scoring_router.py:105-133`.
* The persistence helper reads old status and writes current state at `copilot-sdk/copilot_sdk/backend/scoring_router.py:300-333`.

Gaps/unknowns:

* Conservation metrics are computed for persistence after learn, but no evidence shows a new conservation state machine or endpoint-only monitoring callback. That is expected for P25b Option 2.

### Scan 4 - What from_preset() actually constructs

Command run:

```powershell
python -c "import inspect; from copilot_sdk.scoring.scorer import CompoundingScorer; print(inspect.getsource(CompoundingScorer.from_preset)); print(inspect.getsource(CompoundingScorer.__init__)); print(inspect.getsource(CompoundingScorer.learn)); print(inspect.getsource(CompoundingScorer.score))"
```

Key findings:

* Source inspection matches file evidence: `from_preset()` creates `ProfileScorer(mu=centroids, actions=..., categories=...)` at `copilot-sdk/copilot_sdk/scoring/scorer.py:191-195`.
* `CompoundingScorer.learn()` calls `self._scorer.update(...)` at `copilot-sdk/copilot_sdk/scoring/scorer.py:343-350`.
* The same method writes an outcome at `copilot-sdk/copilot_sdk/scoring/scorer.py:363-368`.
* The method explicitly says DK weight integration is future work at `copilot-sdk/copilot_sdk/scoring/scorer.py:404-415`.

Gaps/unknowns:

* No DK estimator is passed into the constructed `ProfileScorer`.

### Scan 5 - What for_soc_twophase() does differently

Command run:

```powershell
python -c "import inspect; from gae.profile_scorer import ProfileScorer; print(inspect.getsource(ProfileScorer.for_soc_twophase)); print(inspect.getsource(ProfileScorer.__init__)); print(inspect.getsource(ProfileScorer.reestimate_dk))"
```

Key findings:

* `for_soc_twophase()` builds a `LearningStrategy` and supplies `CoordinateDescentEstimator()` when no estimator is passed at `graph-attention-engine-v50/gae/profile_scorer.py:373-390`.
* `reestimate_dk()` filters buffered correct decisions and writes `_dk_weights` from the estimator at `graph-attention-engine-v50/gae/profile_scorer.py:1050-1065`.

Gaps/unknowns:

* No production runtime path was found that calls `for_soc_twophase()`.

### Scan 6 - L5 storage hooks in learn/runtime paths

Command run:

```powershell
Get-ChildItem -Path ".\copilot-sdk\copilot_sdk",".\copilot-sdk\apps",".\s2p-copilot\backend\app",".\gen-ai-roi-demo-v4-v50\backend\app" -Recurse -Include "*.py" | Select-String -Pattern "update_centroid|update_dk_weights|update_conservation_state|get_conservation_state|get_centroids|get_dk_weights|learning_store|_learning_store|L5LearningStore"
```

Key findings:

* L5 DK storage methods are implemented in SDK stores, for example `SQLiteGraphStore.update_dk_weights()` at `copilot-sdk/copilot_sdk/graph/sqlite_store.py:1851-1903` and `InMemoryGraphStore.update_dk_weights()` at `copilot-sdk/copilot_sdk/graph/memory_store.py:913-943`.
* Runtime calls to `update_conservation_state()` exist in SDK scoring router at `copilot-sdk/copilot_sdk/backend/scoring_router.py:315-330`, S2P at `s2p-copilot/backend/app/routers/s2p.py:368-383`, and SOC at `gen-ai-roi-demo-v4-v50/backend/app/services/learning_health.py:498-514`.
* No runtime call to `update_dk_weights()` was found outside storage implementations and tests.
* Centroid checkpointing is performed through `save_centroids()`, not `update_centroid()`, at `copilot-sdk/copilot_sdk/scoring/scorer.py:751-759`.

Gaps/unknowns:

* P21/P22 L5 centroid methods exist, but SDK runtime uses checkpoint APIs for centroids. That is storage persistence, not necessarily the `L5Centroid` node/table family introduced by P21/P22.

### Scan 7 - App startup/router/scorer construction per copilot

Command run:

```powershell
Get-ChildItem -Path ".\copilot-sdk\apps\trading\backend",".\copilot-sdk\apps\purchasing\backend",".\copilot-sdk\apps\dataops\backend",".\s2p-copilot\backend\app",".\gen-ai-roi-demo-v4-v50\backend\app" -Recurse -Include "*.py" | Select-String -Pattern "create_app|FastAPI|app.state|scorer|graph_store|CompoundingScorer.from_preset|ProfileScorer|include_router|create_scoring_router|domain_config|preset|PRESET_REGISTRY"
```

Key findings:

* Trading/Purchasing/DataOps route through `FreshScorerProxy`, whose `_scorer()` constructs `CompoundingScorer.from_preset(..., consolidation_enabled=True)` at `copilot-sdk/copilot_sdk/backend/scorer_proxy.py:29-37`.
* `FreshScorerProxy.learn()` serializes `scorer.learn(...)` at `copilot-sdk/copilot_sdk/backend/scorer_proxy.py:53-59`.
* S2P uses `build_s2p_scorer()` and `CompoundingScorer.from_preset()` without `consolidation_enabled=True` at `s2p-copilot/backend/app/main.py:61-72`.
* SOC initializes `SOCDomainConfig().build_profile_scorer()` at `gen-ai-roi-demo-v4-v50/backend/app/services/gae_state.py:183-185` and attaches it at `gen-ai-roi-demo-v4-v50/backend/app/services/gae_state.py:254-258`.

Gaps/unknowns:

* No direct evidence that SDK apps call `flush_centroids()` on normal `/learn`.

### Scan 8 - Tests claiming DK/trust-trap/learning behavior

Command run:

```powershell
Get-ChildItem -Path ".\copilot-sdk\tests",".\copilot-sdk\apps",".\s2p-copilot\backend\tests",".\gen-ai-roi-demo-v4-v50\backend\tests",".\graph-attention-engine-v50\tests" -Recurse -Include "*.py" | Select-String -Pattern "reestimate_dk|CoordinateDescent|dk_weights|update_dk_weights|trust trap|trust_trap|centroid|compounding|learn.*weight|weight.*learn|conservation|update_conservation_state"
```

Key findings:

* GAE library tests exercise `ProfileScorer.reestimate_dk()` and `CoordinateDescentEstimator`, for example `graph-attention-engine-v50/tests/test_val01_conservation_coord_descent.py:150-173`.
* SDK DK tests are storage-focused: `copilot-sdk/tests/test_l5_dk_weight_storage.py:53-63` verifies protocol/store presence, and subsequent tests call `store.update_dk_weights(...)`.
* SDK conservation persistence tests exist in `copilot-sdk/tests/backend/test_scoring_router.py:318-329`, `copilot-sdk/tests/backend/test_scoring_router.py:623-675`.
* S2P conservation persistence tests exist in `s2p-copilot/backend/tests/test_l5_conservation_s2p_hook.py:166-194`.
* S2P explorer/factor-ranking tests read/display `dk_weights`, but those tests do not prove runtime DK re-estimation or L5 DK writes.

Gaps/unknowns:

* No SDK app test found that proves DK weights change over time through `/learn`.
* No test found that proves runtime calls `update_dk_weights()` after learn/outcome.

### Scan 9 - Verified decision / factor vector availability

Command run:

```powershell
Get-ChildItem -Path ".\copilot-sdk\copilot_sdk",".\copilot-sdk\apps",".\s2p-copilot\backend\app",".\gen-ai-roi-demo-v4-v50\backend\app" -Recurse -Include "*.py" | Select-String -Pattern "factor_vector|factor_names|get_verified_decisions|write_decision|write_outcome|is_correct|actual_action|recommended_action|decision_metadata|metadata"
```

Key findings:

* SDK `score()` stores `factor_vector`, category/action indexes, probabilities, and factor names in decision metadata at `copilot-sdk/copilot_sdk/scoring/scorer.py:242-259`.
* SDK `learn()` reads `factor_vector` from the stored decision at `copilot-sdk/copilot_sdk/scoring/scorer.py:312-318`.
* SQLiteGraphStore stores factor vectors from metadata at `copilot-sdk/copilot_sdk/graph/sqlite_store.py:823-852` and returns verified decisions at `copilot-sdk/copilot_sdk/graph/sqlite_store.py:1720-1780`.
* InMemoryGraphStore stores factor vectors at `copilot-sdk/copilot_sdk/graph/memory_store.py:367-383` and returns verified decisions at `copilot-sdk/copilot_sdk/graph/memory_store.py:824-842`.
* SOC writes factor vectors to Decision nodes in triage at `gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py:401-414` and reads them during outcome learning at `gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py:1087-1211`.

Gaps/unknowns:

* Factor vectors and verified decisions are available, but no runtime DK re-estimation uses them today.

### Scan 10 - Baseline tests

Commands run and results:

* `copilot-sdk`: `python -m pytest tests/ -q --timeout=120` -> 1045 passed, 62 skipped.
* `copilot-sdk`: `python -m pytest apps/trading/backend/tests/ -q --timeout=120` -> 765 passed, 1 skipped.
* `copilot-sdk`: `python -m pytest apps/purchasing/backend/tests/ -q --timeout=120` -> 174 passed, 1 skipped.
* `copilot-sdk`: `python -m pytest apps/dataops/backend/tests/ -q --timeout=120` -> 205 passed.
* `s2p-copilot/backend`: `python -m pytest tests/ -q --timeout=120` -> 1012 passed, 10 skipped.
* `graph-attention-engine-v50`: `python -m pytest tests/ -q --timeout=120` -> 1237 passed.

Gaps/unknowns:

* S2P emitted pytest cache permission warnings, but tests passed.

## Per-copilot feature matrix

Legend: YES means direct runtime evidence; NO means searched and not found or opposite evidence exists; PARTIAL means capability exists but does not satisfy the runtime/L5 claim as stated; UNKNOWN means evidence was insufficient.

| Row | Trading | Purchasing | DataOps | S2P | SOC |
| --- | --- | --- | --- | --- | --- |
| ProfileScorer construction method | `CompoundingScorer.from_preset` via proxy, direct `ProfileScorer(...)` inside SDK (`scorer.py:191-195`, `trading/main.py:262-272`) | Same via proxy (`purchasing/main.py:336-346`) | Same via proxy (`dataops/main.py:355-378`) | `CompoundingScorer.from_preset` (`s2p/main.py:61-72`) | Direct `ProfileScorer(...)` (`soc/config.py:692-708`) |
| Uses CompoundingScorer.from_preset | YES (`trading/main.py:214-219`, proxy `scorer_proxy.py:29-37`) | YES (`purchasing/main.py:205-210`, proxy `scorer_proxy.py:29-37`) | YES (`dataops/main.py:229-234`, proxy `scorer_proxy.py:29-37`) | YES (`s2p/main.py:68-72`) | NO (`soc/config.py:702-708`) |
| Uses ProfileScorer.for_soc_twophase | NO evidence; SDK uses direct constructor (`scorer.py:191-195`) | NO | NO | NO | NO; direct constructor (`soc/config.py:702-708`) |
| DK estimator passed to constructor | NO (`scorer.py:191-195`) | NO | NO | NO | NO |
| CoordinateDescentEstimator reachable | PARTIAL: library reachable, not runtime wired (`profile_scorer.py:373-390`) | PARTIAL | PARTIAL | PARTIAL | PARTIAL |
| Centroids update on learn | YES in memory through `self._scorer.update(...)` (`scorer.py:343-350`) | YES | YES | YES (`s2p.py:1513-1521`, `scorer.py:343-350`) | PARTIAL: only if `LEARNING_ENABLED` true; default false (`soc/config.py:58-61`, `triage.py:1270-1338`) |
| DK weights update on learn | NO; comment says future work (`scorer.py:404-415`) | NO | NO | NO | NO |
| ProfileScorer.reestimate_dk called on learn/outcome | NO runtime call found | NO | NO | NO | NO |
| CoordinateDescentEstimator called on learn/outcome | NO runtime call found | NO | NO | NO | NO |
| Conservation status computed on learn | YES for L5 persistence (`scoring_router.py:127-133`, `conservation_utils.py:45-91`) | YES | YES | YES (`s2p.py:343-386`, `s2p.py:1521`, `s2p.py:1619`) | PARTIAL: computed by health evaluation/triage guard, not every outcome as an L5 DK hook (`triage.py:1255-1264`, `learning_health.py:455-520`) |
| Convergence / conservation tracking active | PARTIAL: persistence and status endpoint, not DK convergence | PARTIAL | PARTIAL | PARTIAL | PARTIAL: conservation guard can block learning, default learning disabled |
| Factor vectors available after score | YES (`scorer.py:242-259`) | YES | YES | YES via SDK scorer | YES (`triage.py:401-414`) |
| Verified decisions available after learn | YES (`sqlite_store.py:1720-1780`) | YES | YES | YES via SDK store | YES in Neo4j outcome path (`triage.py:1087-1211`) |
| Centroid writes to L5 store on learn | PARTIAL/NO for normal app `/learn`: proxy enables consolidation and route does not pass `consolidate`; direct no-consolidation scorer writes checkpoints (`scorer_proxy.py:29-37`, `scorer.py:380-403`) | PARTIAL/NO same | PARTIAL/NO same | YES for checkpoint persistence because S2P from_preset default is non-consolidated (`s2p/main.py:61-72`, `scorer.py:396-403`) | NO L5 centroid write evidence |
| DK weight writes to L5 store on learn | NO; no runtime `update_dk_weights()` call found | NO | NO | NO | NO |
| Conservation writes to L5 store on learn | YES (`scoring_router.py:315-330`) | YES | YES | YES (`s2p.py:368-383`) | PARTIAL: writes on learning health evaluation if category coverage is available (`learning_health.py:455-520`) |
| Conservation old_status read from L5 store | YES (`scoring_router.py:305-313`) | YES | YES | YES (`s2p.py:357-367`) | YES (`learning_health.py:474-489`) |
| TRIGGERED_BY transition semantics available through storage | PARTIAL: available if AGE L5 store is used; SQLite/InMemory have state but no AGE edge | PARTIAL | PARTIAL | PARTIAL | PARTIAL/YES when SOC AGE learning store is configured |
| Tests prove centroid learning | YES for SDK scorer/consolidation (`tests/test_consolidation.py:65-119`) | YES via shared tests | YES via shared tests | YES (`s2p/tests/test_s2p_preview.py:414-425`) | YES when `LEARNING_ENABLED=True` (`backend/tests/test_learning_toggle.py:64-88`) |
| Tests prove DK learning | NO for SDK apps; GAE library tests only (`graph-attention-engine-v50/tests/test_val01_conservation_coord_descent.py:150-173`) | NO | NO | NO | NO |
| Tests prove conservation persistence | YES (`tests/backend/test_scoring_router.py:623-675`) | YES | YES | YES (`s2p/tests/test_l5_conservation_s2p_hook.py:166-194`) | YES (`backend/tests/test_l5_conservation_soc_hook.py:75-221`) |
| Tests prove L5 readback | YES for conservation API smoke/tests; DK storage only | YES | YES | YES conservation/store tests | YES conservation store init/tests |
| Tests prove trust-trap / DK changes over time | NO runtime app proof found | NO | NO | NO | NO |

## Construction-path analysis

Trading, Purchasing, and DataOps use `FreshScorerProxy` in their FastAPI app setup. The proxy lazily creates `CompoundingScorer.from_preset(..., evolve=True, consolidation_enabled=True)` at `copilot-sdk/copilot_sdk/backend/scorer_proxy.py:29-37`, and the app routers are mounted with that proxy and graph store as the optional learning store (`trading/main.py:262-272`, `purchasing/main.py:336-346`, `dataops/main.py:355-378`).

S2P builds a `CompoundingScorer` directly in `build_s2p_scorer()` at `s2p-copilot/backend/app/main.py:61-72`. This is still the SDK construction path and not `for_soc_twophase()`.

SOC does not use `CompoundingScorer`; `SOCDomainConfig.build_profile_scorer()` returns `ProfileScorer(...)` directly at `gen-ai-roi-demo-v4-v50/backend/app/domains/soc/config.py:692-708`, and `gae_state.init_learning_state()` attaches that scorer at `gen-ai-roi-demo-v4-v50/backend/app/services/gae_state.py:183-185` and `gen-ai-roi-demo-v4-v50/backend/app/services/gae_state.py:254-258`.

No app construction path found in these repos uses `ProfileScorer.for_soc_twophase()`.

## DK estimation path analysis

`CoordinateDescentEstimator` exists and is tested in GAE. It estimates a `(n_categories, n_dims)` weight matrix from `(factor_vector, category_index, correct_action_index)` decisions at `graph-attention-engine-v50/gae/dk_estimator.py:80-198`.

`ProfileScorer.for_soc_twophase()` is the construction path that wires `CoordinateDescentEstimator()` by default through `LearningStrategy` at `graph-attention-engine-v50/gae/profile_scorer.py:373-390`.

`ProfileScorer.reestimate_dk()` exists at `graph-attention-engine-v50/gae/profile_scorer.py:1050-1065`, but it only works if `_learning_strategy` and `_decision_buffer` are present, and it only uses buffered correct decisions. The regular SDK `CompoundingScorer.from_preset()` path does not create the scorer with a learning strategy because it calls `ProfileScorer(...)` directly at `copilot-sdk/copilot_sdk/scoring/scorer.py:191-195`.

SDK `CompoundingScorer.learn()` updates centroids and writes outcomes at `copilot-sdk/copilot_sdk/scoring/scorer.py:343-368`. It has an explicit comment that DK weight integration is future work at `copilot-sdk/copilot_sdk/scoring/scorer.py:404-415`. No `reestimate_dk()` call was found in SDK/S2P/SOC runtime code. No `update_dk_weights()` runtime call was found outside storage implementations and tests.

Data shape:

* GAE DK estimator expects 1D factor vectors per verified decision and produces a 2D `(C, D)` weight matrix.
* Current P23/P24 L5 DK storage accepts a 2D `weight_tensor`, so it can store `(C, D)` weights if runtime wiring is added.
* The per-decision factor vector source is present in SDK/S2P/SOC, but it is not currently connected to DK re-estimation.

## Conservation monitoring analysis

SDK conservation status computation was extracted to `compute_conservation_metrics()` at `copilot-sdk/copilot_sdk/backend/conservation_utils.py:45-91`. The `/learn` route calls `_persist_conservation_state_l5()` after learning at `copilot-sdk/copilot_sdk/backend/scoring_router.py:117-133`; the persistence helper computes metrics, reads old state, and writes L5 state at `copilot-sdk/copilot_sdk/backend/scoring_router.py:300-333`.

S2P has equivalent persistence after `/api/learn` at `s2p-copilot/backend/app/routers/s2p.py:1513-1522` and after `/api/s2p/outcome` at `s2p-copilot/backend/app/routers/s2p.py:1610-1619`.

SOC health evaluation persists L5 conservation state only after it resolves a GREEN/AMBER/RED status and a category coverage value, then reads old state and writes state at `gen-ai-roi-demo-v4-v50/backend/app/services/learning_health.py:455-520`. SOC triage calls `LearningHealthMonitor.evaluate()` before optional centroid learning and blocks learning on failures at `gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py:1255-1264`.

## L5 storage hook analysis

### Store methods implemented

* Centroid storage methods exist in SDK L5 store protocols and stores (`copilot-sdk/copilot_sdk/graph/protocol.py:238-250`, `copilot-sdk/copilot_sdk/graph/sqlite_store.py:1786-1849`, `copilot-sdk/copilot_sdk/graph/memory_store.py:868-911`).
* DKWeight storage methods exist (`copilot-sdk/copilot_sdk/graph/protocol.py:252-262`, `copilot-sdk/copilot_sdk/graph/sqlite_store.py:1851-1924`, `copilot-sdk/copilot_sdk/graph/memory_store.py:913-958`).
* ConservationState storage methods exist and are runtime-called after P25b/P25c (`copilot-sdk/copilot_sdk/graph/protocol.py:265-285`, `scoring_router.py:315-330`, `s2p.py:368-383`, `learning_health.py:498-514`).

### Runtime hooks calling store methods

* Centroid runtime persistence: SDK `CompoundingScorer.learn()` calls `_save_centroids_checkpoint()` and that calls `save_centroids()` at `copilot-sdk/copilot_sdk/scoring/scorer.py:396-403` and `copilot-sdk/copilot_sdk/scoring/scorer.py:751-759`. That is checkpoint persistence. It is not a direct call to the L5 `update_centroid()` method.
* DKWeight runtime persistence: no runtime call to `update_dk_weights()` found.
* ConservationState runtime persistence: YES for SDK/S2P/SOC as described above.

### Tests proving runtime hooks

* SDK consolidation tests prove centroid checkpoints are saved or buffered (`copilot-sdk/tests/test_consolidation.py:65-119`).
* SDK and S2P tests prove conservation persistence (`copilot-sdk/tests/backend/test_scoring_router.py:623-675`, `s2p-copilot/backend/tests/test_l5_conservation_s2p_hook.py:166-194`).
* DKWeight tests prove storage only (`copilot-sdk/tests/test_l5_dk_weight_storage.py:53-63` and later direct store calls).

## Blast-radius analysis

If DK re-estimation is inactive in SDK copilots, the impact is high:

* P-WELFORD-B scope: Welford accumulators cannot be only appended to DK storage. The runtime path that generates DK weights is absent for SDK/S2P/SOC. P-WELFORD-B must include or depend on DK runtime wiring.
* P26/P27 readiness: P27 cannot truthfully validate complete L5 schema runtime coverage while DKWeight is storage-only and no runtime L5 DK writes occur.
* #120-#127 demo claims: any demo claim that live Trading/Purchasing/DataOps/S2P learns DK weights over time is unsupported by this evidence.
* Trust-trap discovery claims: no runtime proof found that DK weights change over time in product apps, so trust-trap discovery claims should be limited to experimental/GAE-library evidence until DK runtime wiring is implemented.
* Compounding intelligence claims: centroid learning and conservation persistence are active/partial, but DK compounding is not active in runtime paths.
* 288-moat / firm-specific-values claim: firm-specific factors and verified decisions are stored, but the DK-specific moat is not runtime-persisted.
* JM paper claims: paper claims should distinguish algorithm capability in `graph-attention-engine-v50` from product runtime integration.
* L5 cross-copilot proof C9: ConservationState has runtime hooks, DKWeight does not. C9 should not pass as complete L5 proof until DK runtime writes and Welford audit state are implemented and tested.

## Fix scoping

### Option A - wire ProfileScorer.reestimate_dk into CompoundingScorer.learn

Required code changes:

* Construct SDK `ProfileScorer` through a two-phase/learning-strategy path or pass an equivalent `LearningStrategy` into direct construction.
* Decide when categories enter `VARIANCE_LEARNING`.
* Call `reestimate_dk()` after verified learn/outcome when enough buffered decisions exist.
* Persist resulting `(C, D)` weights through `update_dk_weights()`.

Expected effort: medium-high. This touches construction, runtime learn, DK persistence, and tests.

Risks:

* Could change score behavior if phase-two DK weights affect `ProfileScorer.score()`.
* Needs clear category phase policy for non-SOC domains.
* Needs concurrency discipline around read/update/write.

Tests required:

* Construction test proving estimator is present.
* Learn/outcome test proving `reestimate_dk()` is called when conditions are met.
* L5 `update_dk_weights()` call/readback tests.
* Tests proving response shape and conservation status unchanged.
* Cross-domain Trading/Purchasing/DataOps/S2P tests.

Blockers:

* Roadmap must decide whether runtime scoring may enter phase-two DK scoring now or whether DK estimation should be computed/persisted without affecting scoring until a later gate.

### Option B - minimal SDK DK bridge

Required code changes:

* Leave scorer construction and scoring behavior unchanged.
* Add a post-learn DK estimator bridge that reads verified decisions from graph store, builds `(factor_vector, category_index, correct_action_index)` tuples, runs `CoordinateDescentEstimator`, and writes `update_dk_weights()`.
* Keep the bridge non-fatal and isolated from `ProfileScorer.score()`.
* P-WELFORD-B can then attach Welford accumulators to the same bridge.

Expected effort: medium.

Risks:

* Creates a second DK computation path outside `ProfileScorer.reestimate_dk()`.
* Must avoid formula drift from GAE estimator semantics.
* Must define cadence/min sample size and avoid expensive recalculation per learn without bounds.

Tests required:

* Verified-decision extraction shape tests.
* Estimator invocation tests with real `CoordinateDescentEstimator` or controlled fake.
* L5 `update_dk_weights()` readback.
* Welford audit-state correctness.
* Non-fatal failure tests.

Blockers:

* Roadmap must approve a router/scorer-side bridge instead of using `ProfileScorer.reestimate_dk()`.

### Option C - Roadmap split

An alternative is to split into:

* P-WELFORD-A: storage/protocol Welford fields only, backward-compatible and nullable.
* P-DK-RUNTIME: DK runtime bridge/re-estimation and L5 DK writes.
* P-WELFORD-B: Welford accumulators attached to the runtime bridge and audit recomputation tests.

This reduces risk if Roadmap wants schema completion before runtime scoring changes, but it does not solve the product/demo DK gap by itself.

## Recommendation to Roadmap

Recommended path: Option B unless Roadmap explicitly wants phase-two DK scoring behavior enabled now. The safest near-term move is a minimal SDK/S2P DK bridge that computes and persists DK weights after verified learn/outcome without changing score behavior. That gives P-WELFORD-B a concrete runtime path to audit while avoiding accidental changes to production recommendations.

Questions Roadmap must answer:

* Should DK re-estimation affect runtime scoring immediately, or only persist L5 DK state for audit/startup read first?
* What cadence/minimum sample threshold should trigger DK re-estimation?
* Should Trading/Purchasing/DataOps with consolidation enabled flush L5 centroid state on normal `/learn`, or is checkpoint batching acceptable?
* Should SOC `LEARNING_ENABLED=False` remain the default while P-WELFORD-B is implemented?
* Should P-WELFORD-B update the SDK `CompoundingScorer` path only, or also SOC's direct `ProfileScorer` path?

Stop conditions before implementation:

* No Roadmap decision on whether DK affects score behavior.
* No approved cadence/min sample policy.
* No safe category-index/action-index extraction from verified decisions.
* Any proposed implementation requires GraphStore broadening instead of using existing verified-decision and L5 store APIs.

## Baseline validation

* `copilot-sdk`: `python -m pytest tests/ -q --timeout=120` -> 1045 passed, 62 skipped.
* `copilot-sdk`: `python -m pytest apps/trading/backend/tests/ -q --timeout=120` -> 765 passed, 1 skipped.
* `copilot-sdk`: `python -m pytest apps/purchasing/backend/tests/ -q --timeout=120` -> 174 passed, 1 skipped.
* `copilot-sdk`: `python -m pytest apps/dataops/backend/tests/ -q --timeout=120` -> 205 passed.
* `s2p-copilot/backend`: `python -m pytest tests/ -q --timeout=120` -> 1012 passed, 10 skipped.
* `graph-attention-engine-v50`: `python -m pytest tests/ -q --timeout=120` -> 1237 passed.
