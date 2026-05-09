# copilot-sdk Backend Router Factories Plan

## 1. Executive Summary

Implement shared FastAPI backend router factories under `copilot_sdk/backend`.

Factories:

- `create_scoring_router`
- `create_conservation_router`
- `create_evolution_router`

These factories provide reusable backend surfaces for future copilot applications. GAE must remain visible in responses and imports:

- scoring router wraps `copilot_sdk.scoring`, which wraps GAE `ProfileScorer`;
- conservation router imports `gae.calibration` directly;
- evolution router imports `gae.evolution` directly.

Trading, Purchasing, and DataOps application backends are separate later prompts. This block must not create app-specific backend code.

## 2. Source Contracts from Prompt 0

### `copilot_sdk.scoring`

Public import:

```python
from copilot_sdk.scoring import CompoundingScorer
```

`ScoreResult` fields:

```python
decision_id: str
action: str
action_index: int
confidence: float
probabilities: list[float]
category: str
factors: dict[str, float]
```

`LearnResult` fields:

```python
decision_id: str
iks_before: float
iks_after: float
centroid_delta: float
decisions_total: int
outcome: str
```

`CompoundingScorer.from_preset`:

```python
CompoundingScorer.from_preset(domain: str, db_path: str | None = None)
```

`score`:

```python
score(factors: dict[str, float], category: str) -> ScoreResult
```

`learn`:

```python
learn(decision_id: str, actual_action: str, outcome: str = "confirmed") -> LearnResult
```

Other public methods/properties needed by routers:

```python
fingerprint()
trajectory()
store
gae_scorer
```

Storage accessors available through `scorer.store`:

```python
get_decision(decision_id)
get_verified_decisions()
get_centroid_checkpoints()
get_all_decisions()
count_verified()
count_correct()
```

Current scoring core has no reward fields in `LearnResult`. Reward fields should be added in the scoring router response layer for this build item unless a later implementation proves a scoring-core change is required.

### GAE Calibration API

Direct import source:

```python
from gae.calibration import check_conservation, compute_theta_min, conservation_status
```

Relevant API:

```python
class ConservationCheck(NamedTuple):
    signal: float
    theta_min: float
    headroom: float
    status: str
    passed: bool

compute_theta_min(alpha: float, V: float) -> float
check_conservation(alpha: float, q: float, V: float, theta_min: float) -> ConservationCheck
conservation_status(
    verified_count: int,
    correct_count: int,
    total_decisions: int,
    penalty_ratio: float,
    window: int = 400,
) -> ConservationCheck
```

### GAE Evolution API

Direct import source:

```python
from gae import evolution
```

Relevant constants and APIs:

```python
VALID_EVENT_TYPES
VALID_ARTIFACT_TYPES
get_shadow_summary(variant_id: str) -> dict | None
async get_recent_events(neo4j_client, limit: int = 20) -> list[dict]
async get_evolution_summary(neo4j_client) -> dict
```

Evolution APIs are client-backed and async. Router factory must accept a caller-supplied `neo4j_client` or provider. Without one, endpoints return safe empty responses with engine fields.

### Existing Test Framework

Tests use pytest. Scoring tests use `pytest.importorskip("gae.profile_scorer")`, temporary DB paths, and local `CompoundingScorer` instances. FastAPI is installed in the environment and listed in `pyproject.toml` dev extras with `httpx`.

## 3. Files to Create

```text
copilot_sdk/backend/__init__.py
copilot_sdk/backend/scoring_router.py
copilot_sdk/backend/conservation_router.py
copilot_sdk/backend/evolution_router.py
copilot_sdk/backend/models.py
tests/backend/test_scoring_router.py
tests/backend/test_conservation_router.py
tests/backend/test_evolution_router.py
```

`models.py` is optional but recommended to centralize Pydantic request/response models and avoid duplicated schema definitions.

## 4. Files to Modify

No files outside `copilot_sdk/backend` and `tests/backend` are required for the first implementation pass.

If implementation needs package-level exports, update only:

```text
copilot_sdk/backend/__init__.py
```

Do not modify top-level `copilot_sdk/__init__.py` unless a later prompt explicitly decides router factories should be top-level SDK exports.

## 5. Forbidden Files

Do not modify:

```text
graph-attention-engine-v50/**
gen-ai-roi-demo-v4-v50/**
s2p-copilot/**
ci-platform/**
apps/**
frontend/**
copilot_sdk/scoring/scorer.py
copilot_sdk/scoring/storage.py
copilot_sdk/scoring/fingerprint.py
copilot_sdk/scoring/trajectory.py
package/build/config files
```

Scoring core files remain forbidden unless a later implementation proves reward fields cannot be safely produced in the router layer.

## 6. Scoring Router Contract

Factory:

```python
create_scoring_router(
    domain: str,
    db_path: str | None = None,
    scorer_factory: callable | None = None,
)
```

`scorer_factory`, when provided, should return a `CompoundingScorer`-compatible object. This keeps tests isolated and allows apps to supply scoped storage.

Endpoints:

```text
POST /score
POST /learn
GET  /fingerprint
GET  /trajectory
GET  /history
```

Request models:

```python
class ScoreRequest:
    category: str
    factors: dict[str, float]
    context: dict[str, Any] | None = None

class LearnRequest:
    decision_id: str
    actual_action: str
    outcome: str = "confirmed"
    context: dict[str, Any] | None = None
```

Response requirements:

- Every response includes an `engine` field.
- Scoring engine value should credit both layers, for example:

```text
copilot_sdk.scoring.CompoundingScorer + gae.profile_scorer.ProfileScorer
```

`POST /score` response wraps `ScoreResult`:

```python
{
    "engine": "...",
    "decision_id": "...",
    "action": "...",
    "action_index": 0,
    "confidence": 0.0,
    "probabilities": [...],
    "category": "...",
    "factors": {...},
}
```

`POST /learn` response wraps `LearnResult` and adds graded reward fields:

```python
{
    "engine": "...",
    "decision_id": "...",
    "iks_before": 0.0,
    "iks_after": 0.0,
    "centroid_delta": 0.0,
    "decisions_total": 1,
    "outcome": "applied",
    "reward": 0.0,
    "previous_reward": None,
    "reward_multiplier": 1.0,
}
```

`GET /fingerprint` response:

- Convert dataclasses to JSON-compatible dicts.
- Include `engine`.
- Include `decisions_analyzed`, `overall_win_rate`, `per_category_precision`, and `factors`.

`GET /trajectory` response:

- Convert dataclasses to JSON-compatible dicts.
- Include `engine`.
- Include `points`, `current_iks`, `current_win_rate`, `decisions_total`, and `days_active`.

`GET /history` response:

- Return `{"engine": ..., "decisions": [...]}` from `scorer.store.get_all_decisions()`.
- Empty history returns an empty list.

Unknown domain behavior:

- If `CompoundingScorer.from_preset()` raises `ValueError`, factory creation or endpoint invocation should surface a clear 4xx error.
- Prefer endpoint-time `HTTPException(status_code=404, detail=...)` when the factory lazily builds scorers.

## 7. Graded Reward Strategy

Do not edit scoring core for the first router implementation.

Reward computation order:

1. If the preset or scorer exposes `compute_reward(decision, outcome, context)`, call it.
2. Otherwise use SDK-level safe defaults based on decision factors and request context.
3. If no domain-specific inputs exist, return a conservative default reward of `0.0`.

Domain defaults:

```python
trading:
    reward = position_size * research_depth * time_horizon

purchasing:
    reward = context["waste_cost"] if present
    else context["stockout_revenue_loss"] if present
    else 0.05

dataops:
    reward = business_criticality * impact_scope

unknown:
    reward = 0.0
```

Reward sign:

- If the learned decision is incorrect, use negative reward.
- If correct, use positive reward.
- Correctness can be computed by comparing `actual_action` to the stored decision's `recommended_action` before or after `learn()`.

Previous reward convention:

- `previous_reward = None` when no previous verified reward is available.
- `reward_multiplier = 1.0` when `previous_reward` is `None` or `0`.
- If prior reward storage is not implemented, keep `previous_reward = None` consistently and document that durable reward history is a later extension.

The router can inspect the stored decision through `scorer.store.get_decision(decision_id)` before calling `learn()`. That row includes `factors`, `recommended_action`, and `confidence`.

## 8. Conservation Router Contract

Factory:

```python
create_conservation_router(
    domain: str,
    db_path: str | None = None,
    scorer_factory: callable | None = None,
)
```

Endpoints:

```text
GET  /conservation/status
POST /conservation/what-if
```

Response requirements:

- Every response includes `engine: "gae.calibration"`.
- No SOC backend imports.
- Domain-parametric.
- Safe fallback if no scoring state exists.

Status behavior:

- Build or receive a `CompoundingScorer`.
- Get:
  - `verified_count = scorer.store.count_verified()`
  - `correct_count = scorer.store.count_correct()`
  - `total_decisions = len(scorer.store.get_all_decisions())`
  - `penalty_ratio = scorer._preset.penalty_ratio` if available; otherwise default to `1.0`
- Call GAE `conservation_status(...)`.
- Return `signal`, `theta_min`, `headroom`, `status`, and `passed`.

Insufficient state:

- `conservation_status()` returns RED for zero decisions/verified count.
- Endpoint must not crash on an empty DB.

What-if request:

```python
class ConservationWhatIfRequest:
    alpha: float
    q: float
    V: float
    theta_min: float | None = None
```

What-if behavior:

- If `theta_min` is absent, compute it with `compute_theta_min(alpha, V)`.
- Then call `check_conservation(alpha, q, V, theta_min)`.
- Return the same response shape plus input echo.

## 9. Evolution Router Contract

Factory:

```python
create_evolution_router(
    domain: str,
    neo4j_client_provider: callable | None = None,
)
```

Endpoints:

```text
GET /evolution/variants
GET /evolution/patterns
```

Response requirements:

- Every response includes `engine: "gae.evolution"`.
- Directly import GAE evolution module.
- Domain-parametric.
- No SOC backend imports.
- Safe empty response if no ledger/client exists.

Variants behavior:

- If no `neo4j_client_provider` is supplied, return:

```python
{"engine": "gae.evolution", "domain": domain, "variants": []}
```

- If a client is supplied, call `await evolution.get_recent_events(client, limit=...)`.
- Filter or group events into variant-shaped dicts without inventing app-specific fields.

Patterns behavior:

- If no client is supplied, return:

```python
{"engine": "gae.evolution", "domain": domain, "patterns": []}
```

- If a client is supplied, use `await evolution.get_evolution_summary(client)` and/or recent events to expose transfer-pattern-friendly rows.
- Keep shape generic: `pattern_id`, `source_copilot`, `source_rule`, `warm_start_prior`, `artifact_type`, `metadata` when available.

## 10. Test Plan

### Scoring Router Tests

Create `tests/backend/test_scoring_router.py`.

Required tests:

- factory returns a FastAPI `APIRouter`.
- `POST /score` returns action, confidence, probabilities, category, factors, and engine.
- `POST /learn` returns `reward`, `previous_reward`, `reward_multiplier`, and engine.
- `GET /fingerprint` returns factor data and engine.
- `GET /trajectory` returns points/current IKS and engine.
- `GET /history` returns a list, empty before scoring and populated after scoring.
- unknown domain returns a clear 4xx response or factory error.
- no SOC/S2P/gen-ai imports are introduced.

Use `fastapi.FastAPI` plus `fastapi.testclient.TestClient`.

### Conservation Router Tests

Create `tests/backend/test_conservation_router.py`.

Required tests:

- factory returns `APIRouter`.
- `GET /conservation/status` returns engine and conservation fields.
- empty/insufficient state does not crash.
- `POST /conservation/what-if` returns safe GAE result.
- response references direct GAE calibration engine.
- no SOC imports.

### Evolution Router Tests

Create `tests/backend/test_evolution_router.py`.

Required tests:

- factory returns `APIRouter`.
- `GET /evolution/variants` returns engine and list shape.
- `GET /evolution/patterns` returns engine and list shape.
- empty/no-client state returns empty lists without crashing.
- mocked client path exercises GAE evolution call shape if practical.
- no SOC imports.

## 11. Validation Commands

Run from the repo root:

```powershell
python -m pytest tests/backend -v --timeout=120
python -m pytest tests -v --timeout=120
python -c "from copilot_sdk.backend import create_scoring_router, create_conservation_router, create_evolution_router; print('backend routers OK')"
```

If code files under `copilot_sdk` are changed, also follow `CLAUDE.md` and run:

```powershell
python -m pytest tests/ -v
```

Do not run graphify update in a documentation-only prompt. Implementation prompts that modify code should run graphify update if available and safe.

## 12. Open Risks / Decisions

- FastAPI is currently a dev extra, not a required runtime dependency. If router factories become public runtime API, dependency policy may need a packaging decision.
- `LearnResult` has no reward fields. First implementation should augment in router responses; durable reward history can be a later scoring-core/storage extension.
- `previous_reward` convention is explicitly `None` unless durable reward history exists; multiplier defaults to `1.0` when previous is absent or zero.
- Evolution GAE APIs require an async graph client. Router must be dependency-injected and fail open with empty lists when no client is supplied.
- Existing repo rules say SDK has no domain-specific code, but scoring presets already exist. Backend router implementation must remain generic and not add app-specific backend modules.
