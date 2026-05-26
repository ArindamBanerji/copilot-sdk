# SCORER-CACHE Plan — Eliminate Fresh-Per-Call Scorer Construction

## Executive Summary

`FreshScorerProxy` is the current hot path: it owns one graph store, but every `score`, `learn`, `fingerprint`, `trajectory`, `get_phase`, and `get_alpha` call constructs a fresh `CompoundingScorer.from_preset(...)` instance (`copilot_sdk/backend/scorer_proxy.py:21-73`). Since `from_preset` now wires RL defaults and constructs `ConservationBoundedThompson`, which loads persisted Thompson posteriors from the graph store at construction time (`copilot_sdk/scoring/scorer.py:160-188`, `copilot_sdk/rl/exploration.py:15-24`, `copilot_sdk/rl/exploration.py:79-97`), this per-call construction is a credible source of avoidable request latency. The recommended implementation is to replace the fresh-per-call behavior with an app/proxy-scoped cached scorer instance, guarded by a per-proxy `RLock` for construction and scorer method calls. This preserves the current app-level `db_path` isolation used by trading, purchasing, and dataops tests, avoids module-global leakage, and mirrors the safer part of the S2P pattern: construct one app-owned scorer and route requests through that state (`../s2p-copilot/backend/app/main.py:54-66`, `../s2p-copilot/backend/app/routers/s2p.py:90-95`). READY_FOR_IMPLEMENTATION: YES, with conservative serialization around shared scorer calls because read/write scorer thread safety is not fully proven.

## Method and Scope

- Repo path: `C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\kaggle_experiments\claude_projects\copilot-sdk`.
- Read-only source/test/config constraint. The only write performed by this diagnostic prompt is `docs/scorer_cache_plan.md`.
- No pytest or test suite was run.
- Evidence comes from live source inspection, not docs alone. The repo `CLAUDE.md` was read first and requires source grounding plus file:line citations (`CLAUDE.md:1-16`).
- Graphify guidance was followed by reading `graphify-out/GRAPH_REPORT.md`, which shows the corpus is large enough for architecture navigation (`graphify-out/GRAPH_REPORT.md:1-9`).
- Caveat: no runtime concurrency stress test was run. Thread-safety conclusions distinguish "source suggests safe enough under lock" from "proven lock-free safe."

## Section 1: Current FreshScorerProxy Hot Path

| App | File | Proxy / Factory | Per-call from_preset? | Methods affected | Evidence |
|---|---|---|---|---|---|
| trading | `apps/trading/backend/app/main.py` | `scorer_proxy = FreshScorerProxy(DOMAIN, scoring_db, _graph_store)` passed as `scorer_factory=lambda: scorer_proxy` | YES, inside proxy methods | `/api/score`, `/api/learn`, `/api/fingerprint`, `/api/trajectory`, `/api/health`, conservation/transfer consumers | `apps/trading/backend/app/main.py:232-244`; proxy `_scorer()` calls `from_preset` at `copilot_sdk/backend/scorer_proxy.py:25-26`; router uses scorer methods at `copilot_sdk/backend/scoring_router.py:61-129` |
| purchasing | `apps/purchasing/backend/app/main.py` | `scorer_proxy = FreshScorerProxy(DOMAIN, scoring_db, _graph_store)` passed as `scorer_factory=lambda: scorer_proxy` | YES, inside proxy methods | same SDK scoring routes plus evidence/conservation consumers | `apps/purchasing/backend/app/main.py:269-300`; proxy calls at `copilot_sdk/backend/scorer_proxy.py:28-73` |
| dataops | `apps/dataops/backend/app/main.py` | `scorer_proxy = FreshScorerProxy(DOMAIN, scoring_db, _graph_store)` passed as `scorer_factory=lambda: scorer_proxy` | YES, inside proxy methods | same SDK scoring routes plus conservation/transfer consumers | `apps/dataops/backend/app/main.py:238-255`; proxy calls at `copilot_sdk/backend/scorer_proxy.py:28-73` |

`create_scoring_router` already has an internal `scorer_cache`, but when apps pass `scorer_factory=lambda: scorer_proxy`, the cached object is the proxy, not a `CompoundingScorer` (`copilot_sdk/backend/scoring_router.py:42-59`). Therefore the router cache does not prevent the proxy from building a fresh scorer on each method call.

## Section 2: Thread Safety Assessment

- Q1. Is `CompoundingScorer` thread-safe for concurrent `score()` calls? **UNKNOWN lock-free; safe recommendation is serialize via proxy lock.** `score()` calls GAE `ProfileScorer.score`, then writes a decision through the graph store (`copilot_sdk/scoring/scorer.py:190-247`). The graph store write uses `SQLiteGraphStore._lock` and commits inside `write_decision` (`copilot_sdk/graph/sqlite_store.py:284-308`), but `CompoundingScorer` itself has no method-level lock around `_scorer.score` or decision metadata creation (`copilot_sdk/scoring/scorer.py:190-247`).
- Q2. Is shared scorer safe for concurrent `score()` + `learn()`? **Not proven without serialization.** `learn()` mutates in-memory centroids and scorer learning rates, writes outcomes/checkpoints, updates RL posterior state, and may archive old decisions (`copilot_sdk/scoring/scorer.py:282-385`). These operations are not wrapped in a scorer-level lock. The store protects individual writes with `RLock`, but not the full read-update-write sequence (`copilot_sdk/graph/sqlite_store.py:46-50`, `copilot_sdk/graph/sqlite_store.py:325-343`, `copilot_sdk/graph/sqlite_store.py:446-469`).
- Does `SQLiteGraphStore` handle concurrent access? **Partially.** It opens SQLite with `check_same_thread=False`, uses an `RLock`, and protects major write methods (`copilot_sdk/graph/sqlite_store.py:42-55`, `copilot_sdk/graph/sqlite_store.py:284-308`, `copilot_sdk/graph/sqlite_store.py:325-343`). Many read methods run without the store lock (`copilot_sdk/graph/sqlite_store.py:376-430`, `copilot_sdk/graph/sqlite_store.py:515-542`). SQLite WAL is enabled for file-backed DBs (`copilot_sdk/graph/sqlite_store.py:52-54`), but `:memory:` does not use WAL.
- Locks present/absent: `SQLiteGraphStore` has `threading.RLock` (`copilot_sdk/graph/sqlite_store.py:46`). `FreshScorerProxy` currently has no lock (`copilot_sdk/backend/scorer_proxy.py:14-78`). `CompoundingScorer` has no lock fields in its initializer (`copilot_sdk/scoring/scorer.py:91-120`). `ConservationBoundedThompson` mutates `alpha`/`beta` without a lock (`copilot_sdk/rl/exploration.py:46-53`).
- What remains UNKNOWN: GAE `ProfileScorer.score` internal thread safety was not proven from local SDK source, and no concurrency test was run. The implementation should not depend on lock-free scorer safety.

## Section 3: Mutation Analysis

| Method | Reads | Writes / Mutates | Store Side Effects | RL Side Effects | Safe to share? | Evidence |
|---|---|---|---|---|---|---|
| `score` | preset shape, in-memory centroids through GAE score | no intended centroid mutation seen in wrapper; creates metadata and decision id | writes a decision and commits | none directly | YES only with proxy lock recommended; graph store write is individually locked | `copilot_sdk/scoring/scorer.py:190-247`; `copilot_sdk/graph/sqlite_store.py:284-308` |
| `learn` | decision row, current IKS, centroids | mutates `self._scorer.eta`, `eta_override`, centroids, checkpoint bookkeeping fields, batch fields | writes outcome, centroid checkpoint, optional entity link, maybe archives decisions | computes reward; updates Thompson posterior; assigns credit | YES only with proxy lock; read/write interleaving is otherwise risky | `copilot_sdk/scoring/scorer.py:249-385`; `copilot_sdk/rl/exploration.py:46-53`; `copilot_sdk/graph/sqlite_store.py:325-343`, `copilot_sdk/graph/sqlite_store.py:446-469` |
| `fingerprint` | verified decisions | none in wrapper | read-only store query | none | YES with lock or no lock probably OK, but serialize for consistency | `copilot_sdk/scoring/scorer.py:387-391`; `copilot_sdk/graph/sqlite_store.py:387-404` |
| `trajectory` | checkpoints and verified decisions | none in wrapper | read-only store queries | none | YES with lock or no lock probably OK, but serialize to avoid read during learn checkpoint writes | `copilot_sdk/scoring/scorer.py:418-438`; `copilot_sdk/graph/sqlite_store.py:515-542` |
| `get_phase` | verified/correct counts | none | read-only count queries | none | YES with lock or no lock probably OK | `copilot_sdk/scoring/scorer.py:440-450`; `copilot_sdk/graph/sqlite_store.py:413-430` |
| `get_alpha` | verified/correct counts | none | read-only count queries | none | YES with lock or no lock probably OK | `copilot_sdk/scoring/scorer.py:452-461`; `copilot_sdk/graph/sqlite_store.py:413-430` |

Q3. `score()` mutates persistent graph-store state by writing a decision (`copilot_sdk/scoring/scorer.py:229-237`). Q4. `learn()` mutates both in-memory scorer state and persistent state: centroids and temporary learning-rate fields (`copilot_sdk/scoring/scorer.py:282-306`), outcomes (`copilot_sdk/scoring/scorer.py:314-319`), checkpoint bookkeeping and centroid checkpoints (`copilot_sdk/scoring/scorer.py:326-354`, `copilot_sdk/scoring/scorer.py:690-710`), Thompson posterior state (`copilot_sdk/scoring/scorer.py:355-358`, `copilot_sdk/rl/exploration.py:46-53`), and archive state (`copilot_sdk/scoring/scorer.py:373-385`, `copilot_sdk/scoring/scorer.py:712-726`).

## Section 4: S2P Pattern

S2P constructs a single app-owned scorer with an explicit `SQLiteGraphStore`, reward function, and decision prefix in `build_s2p_scorer`, then assigns it to `app.state.scorer`, `app.state.graph_store`, and `app.state.s2p_reward_function` at startup (`../s2p-copilot/backend/app/main.py:54-66`). S2P routes resolve the scorer from `http_request.app.state.scorer` through `_sdk_scorer` (`../s2p-copilot/backend/app/routers/s2p.py:90-95`), and `/api/s2p/score`, `/api/learn`, and `/api/s2p/iks` all read that app-state scorer (`../s2p-copilot/backend/app/routers/s2p.py:727-733`, `../s2p-copilot/backend/app/routers/s2p.py:840-864`, `../s2p-copilot/backend/app/routers/s2p.py:953-961`).

What S2P proves: app-level scorer sharing is already an accepted pattern in a sibling backend, and it prevents per-request `from_preset` construction on the main score/learn/IKS path. What S2P does **not** prove: lock-free thread safety. The S2P app-scoped scorer code shown here does not add a scorer-level lock around score or learn (`../s2p-copilot/backend/app/routers/s2p.py:727-733`, `../s2p-copilot/backend/app/routers/s2p.py:852-864`).

## Section 5: Reset / Test Isolation

| App | Test app pattern | DB isolation | Cache risk | Required reset/change | Evidence |
|---|---|---|---|---|---|
| trading | pytest fixture creates `create_app(db_path=tmp_path / "trading_test.db")` and returns `TestClient(app)` | per-test tmp DB path | module-global cache would leak scorer/db across tests; app/proxy-scoped cache is safe | keep cache attached to the per-app `FreshScorerProxy` instance; do not use module globals | `apps/trading/backend/tests/conftest.py:22-46`; `apps/trading/backend/app/main.py:222-244` |
| purchasing | pytest fixture creates `create_app(db_path=tmp_path / "purchasing_test.db")`; CLI tests also pass `--db-path` to tmp files | per-test tmp DB path and CLI tmp paths | module-global cache would break tmp-path isolation; proxy-scoped cache respects `create_app` db path | cache only in backend proxy; leave CLI out of initial scope unless separately benchmarked | `apps/purchasing/backend/tests/conftest.py:50-53`; `apps/purchasing/backend/tests/test_cli.py:36-43`; `apps/purchasing/backend/app/main.py:259-281` |
| dataops | pytest fixture monkeypatches data dirs/default DB, then creates `create_app(db_path=dataops_data_dir / "test_dataops.db")` | per-test tmp data dir and tmp DB path | module-global cache would be especially risky because tests monkeypatch app module paths | cache only on the app-created proxy; do not reuse across `create_app` calls | `apps/dataops/backend/tests/conftest.py:21-74`; `apps/dataops/backend/app/main.py:228-250` |

Q6. All three backend test suites create fresh app instances with tmp DB paths. Therefore a module-global scorer cache is unsafe. A proxy-level cache is safe if each app keeps constructing a new proxy inside `create_app`, which is true today for trading, purchasing, and dataops (`apps/trading/backend/app/main.py:235`, `apps/purchasing/backend/app/main.py:272`, `apps/dataops/backend/app/main.py:241`).

## Section 6: Cache Strategy Options

### Option A — App-level startup scorer

- Build one `CompoundingScorer` in each app `create_app` and put it on `app.state`.
- Pros: closest to S2P (`../s2p-copilot/backend/app/main.py:62-66`); explicit app ownership.
- Cons: requires changing each app and possibly adjusting routers that currently receive a scorer-like proxy. `create_conservation_router` and `create_transfer_router` can work with scorer/store-like objects (`copilot_sdk/backend/conservation_router.py:94-143`, `copilot_sdk/backend/transfer_router.py:24-44`), but app-specific changes are broader.
- Verdict: safe but broader than necessary.

### Option B — Proxy-level lazy cache

- Keep app files mostly as-is. Change `FreshScorerProxy` so `_scorer()` lazily constructs one `CompoundingScorer` and returns it for later calls.
- Add `threading.RLock` on the proxy. Use it around lazy construction and around methods that call the shared scorer.
- Pros: one SDK change covers all three apps because they already instantiate `FreshScorerProxy` inside `create_app` (`apps/trading/backend/app/main.py:235`, `apps/purchasing/backend/app/main.py:272`, `apps/dataops/backend/app/main.py:241`); preserves per-app tmp DB isolation; minimal API churn.
- Cons: class name becomes misleading unless renamed or documented. Serialized method calls may reduce parallelism but should still remove the expensive repeated construction.
- Verdict: **recommended**.

### Option C — Per-method fresh scorer with optimized RL load

- Keep fresh construction but optimize `from_preset`/RL loading.
- Pros: lower concurrency risk.
- Cons: touches more SDK internals and does not address all construction overhead. The hot path is explicit in `FreshScorerProxy` (`copilot_sdk/backend/scorer_proxy.py:25-73`).
- Verdict: reject for this prompt.

### Option D — Global module cache

- Cache scorers in a module-level dictionary by domain/db path.
- Pros: simple in one file.
- Cons: unsafe for test isolation and tmp-path lifecycle. All three test suites rely on fresh `create_app(...tmp...)` patterns (`apps/trading/backend/tests/conftest.py:22-46`, `apps/purchasing/backend/tests/conftest.py:50-53`, `apps/dataops/backend/tests/conftest.py:69-74`).
- Verdict: reject.

Recommendation for Q7: implement Option B first. Use app/proxy-scoped caching, not a module-global cache. Keep the graph store owned by the proxy. Add a conservative proxy lock around all shared scorer calls because scorer-level thread safety is not proven.

## Section 7: Implementation Recommendation

Files to change in a later implementation prompt:

1. `copilot_sdk/backend/scorer_proxy.py`
   - Add `threading.RLock`.
   - Add `self._scorer_instance: CompoundingScorer | None = None`.
   - Change `_scorer()` to lazily construct once with `CompoundingScorer.from_preset(self._preset_name, graph_store=self.graph_store)`.
   - Wrap construction in the lock.
   - Wrap `score`, `learn`, `fingerprint`, `trajectory`, `get_phase`, and `get_alpha` calls in the same lock. This is conservative but appropriate because `learn()` mutates centroids and RL state (`copilot_sdk/scoring/scorer.py:282-385`).
   - Keep `_close_scorer_store` a no-op because the scorer borrows the proxy-owned store (`copilot_sdk/backend/scorer_proxy.py:75-78`).
   - Either keep the class name for compatibility and update docstring from "Fresh" to "cached scorer proxy", or add a compatibility alias if renaming.
2. Tests to add or update:
   - likely `tests/` or `copilot_sdk/backend` tests if a backend test module exists; otherwise app backend tests for trading/purchasing/dataops.
   - app-specific tests in `apps/trading/backend/tests/test_trading_backend.py`, `apps/purchasing/backend/tests/test_purchasing_backend.py`, and `apps/dataops/backend/tests/test_dataops_backend.py` may be needed to prove end-to-end app isolation.

Exact design shape:

```python
class FreshScorerProxy:
    def __init__(...):
        ...
        self._lock = threading.RLock()
        self._scorer_instance: CompoundingScorer | None = None

    def _scorer(self) -> CompoundingScorer:
        with self._lock:
            if self._scorer_instance is None:
                self._scorer_instance = CompoundingScorer.from_preset(
                    self._preset_name,
                    graph_store=self.graph_store,
                )
            return self._scorer_instance

    def score(...):
        with self._lock:
            return self._scorer().score(...)
```

Reset strategy:

- No app reset endpoint is present in the inspected main files. Test isolation comes from fresh `create_app` with fresh tmp `db_path`, so the cache must remain proxy-instance scoped.
- If future reset endpoints are added, they should call a proxy method such as `reset_cache()` that closes/rebuilds the scorer while preserving or replacing the graph store intentionally. Do not add reset surface unless tests require it.

Expected performance benefit:

- Removes six categories of repeated `from_preset` construction from proxy methods (`copilot_sdk/backend/scorer_proxy.py:28-73`).
- Avoids repeated RL component construction and Thompson posterior load from SQLite (`copilot_sdk/scoring/scorer.py:160-188`, `copilot_sdk/rl/exploration.py:79-97`).
- Measure: count `CompoundingScorer.from_preset` calls during repeated `/api/score`; compare latency under Playwright parallel workers before/after.

Q8. Exact files for later implementation: start with `copilot_sdk/backend/scorer_proxy.py` and focused tests. App source files should not need changes for Option B because all three apps already use `FreshScorerProxy` in `create_app`.

## Section 8: Test Plan for Later Implementation

Add/update tests that prove:

1. `FreshScorerProxy` reuses the same scorer across multiple `score()` calls and `CompoundingScorer.from_preset` is called once per proxy.
2. `score()` followed by `learn()` still updates the same shared scorer and graph store.
3. `fingerprint()`, `trajectory()`, `get_phase()`, and `get_alpha()` do not trigger additional scorer construction after the first call.
4. Two proxy instances with different tmp `db_path`s do not share scorer or data.
5. Trading `create_app(db_path=tmp_path / "one.db")` and `create_app(db_path=tmp_path / "two.db")` remain isolated.
6. Purchasing and dataops app tests preserve current tmp DB isolation.
7. Concurrent repeated `score()` calls do not raise and produce valid unique decision ids. Use a modest thread pool test around the proxy if feasible.
8. Interleaved `score()` + `learn()` under the proxy lock does not corrupt state and results in verified counts/trajectory changing as expected.
9. No module-global cache leakage: constructing a new proxy starts with no cached scorer.
10. If the implementation keeps the `FreshScorerProxy` class name, add a test or doc assertion only if useful; behavior matters more than naming.

Validation commands for a later implementation prompt:

```powershell
python -m pytest tests/ -q --timeout=120
python -m pytest apps/trading/backend/tests/ -q --timeout=120
python -m pytest apps/purchasing/backend/tests/ -q --timeout=120
python -m pytest apps/dataops/backend/tests/ -q --timeout=120
```

Do not run these for this diagnostic prompt.

## Section 9: Risks / Open Questions

- Lock-free `CompoundingScorer.score()` thread safety is UNKNOWN because it calls GAE `ProfileScorer.score` and writes decisions, with no scorer-level lock (`copilot_sdk/scoring/scorer.py:190-247`).
- Shared `learn()` absolutely needs serialization unless deeper proof is added, because it mutates centroids, learning-rate fields, checkpoint fields, and RL posterior state (`copilot_sdk/scoring/scorer.py:282-385`).
- `SQLiteGraphStore` uses a shared connection with `check_same_thread=False` and locks writes, but read methods are not generally locked (`copilot_sdk/graph/sqlite_store.py:42-55`, `copilot_sdk/graph/sqlite_store.py:376-430`). The proxy lock avoids most same-process read/write interleaving through the shared scorer, but other routers can still instantiate separate stores against the same DB.
- Trading, purchasing, and dataops also mount routers that create fresh graph stores for analytics/context/self-computation paths (`apps/trading/backend/app/main.py:261-276`, `apps/purchasing/backend/app/main.py:298-300`, `apps/dataops/backend/app/main.py:258-268`). This plan only addresses scorer construction overhead, not every DB access pattern.
- `FreshScorerProxy` class naming will become inaccurate after caching. Renaming would be cleaner but broader; compatibility favors keeping the name and updating docstring first.
- GPT-5.5 review should confirm whether serializing all proxy methods is acceptable for expected throughput before implementation.

## Section 10: Prompt Inputs for Implementation

Approved files:

- `copilot_sdk/backend/scorer_proxy.py`
- Focused tests, preferably a new or existing SDK/backend proxy test file if present; otherwise app-level tests under:
  - `apps/trading/backend/tests/`
  - `apps/purchasing/backend/tests/`
  - `apps/dataops/backend/tests/`

Preferred strategy:

- Proxy-level lazy cached scorer, scoped to each `FreshScorerProxy` instance created inside each app `create_app`.
- Add per-proxy `threading.RLock`.
- Serialize proxy method calls conservatively.
- Do not use module-global cache.
- Do not change app `create_app` files unless tests prove a missing integration hook.

Invariants:

- `CompoundingScorer.from_preset` is called once per proxy instance, not once per method.
- `score` and `learn` operate on the same cached scorer and graph store.
- Separate app/proxy instances with separate `db_path`s remain isolated.
- No stale `db_path` survives across `create_app` calls.
- No test writes to default app DB when it should use `tmp_path`.

Required tests:

- construction-count test;
- score/learn same scorer test;
- repeated fingerprint/trajectory/health no extra construction test;
- two tmp DB isolation test;
- modest concurrent score test;
- interleaved score/learn test under lock;
- app regression tests for trading, purchasing, and dataops.

Blockers:

- None for a conservative proxy-level cache.
- Do not attempt lock-free shared scorer until GAE `ProfileScorer` and SDK scorer internals have dedicated concurrency tests.

READY_FOR_IMPLEMENTATION: YES
