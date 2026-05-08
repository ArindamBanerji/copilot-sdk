# CompoundingScorer Block B API Contract

## 1. Executive Summary

The new package is `compounding-scorer`.

Its purpose is to provide a user-facing wrapper around the existing GAE `ProfileScorer`. The wrapper will add preset-based domain configuration, SQLite-backed decision/outcome/centroid storage, factor-noise fingerprinting, trajectory tracking, and a stable `CompoundingScorer` facade.

Loom mode for Block B is local-only:

- Import GAE by inserting the sibling `graph-attention-engine-v50` directory into `sys.path`.
- Do not require `pip install`.
- Do not publish to PyPI.
- Do not modify GAE, SOC, S2P, or ci-platform repositories.

## 2. GAE API Contract

The authoritative dependency is:

```text
../graph-attention-engine-v50/gae/profile_scorer.py
```

Prompt 0 proved that `ProfileScorer` imports successfully when the workspace-local GAE path is added to `sys.path`:

```python
import sys
sys.path.insert(0, "graph-attention-engine-v50")
from gae.profile_scorer import ProfileScorer
```

### Constructor

Exact constructor signature:

```python
ProfileScorer(
    mu: np.ndarray,
    actions: list[str],
    kernel: KernelType = KernelType.L2,
    profile: CalibrationProfile | None = None,
    categories: list[str] | None = None,
    min_confidence: float = 0.0,
    eta_override: float | None = None,
    factor_mask: np.ndarray | None = None,
    scoring_kernel=None,
    auto_pause_on_amber: bool = False,
    *,
    learning_strategy: LearningStrategy | None = None,
) -> None
```

Required constructor call for this package:

```python
ProfileScorer(
    mu=centroids,
    actions=preset.actions,
    categories=preset.categories,
)
```

Optional parameters may be passed only when the package intentionally exposes them:

- `kernel=KernelType.L2`
- `profile=...`
- `min_confidence=...`
- `eta_override=...`
- `factor_mask=...`
- `auto_pause_on_amber=...`
- keyword-only `learning_strategy=...`

Do not call:

```python
ProfileScorer(centroids=..., temperature=...)
```

Prompt 0 proved those constructor names are not supported. GAE expects `mu`, not `centroids`, and temperature is supplied through a calibration `profile` or defaults inside `ProfileScorer`.

### Score

Exact score signature:

```python
ProfileScorer.score(self, f: np.ndarray, category_index: int) -> ScoringResult
```

`f` must be a finite NumPy vector with shape `(n_factors,)`.

Use these `ScoringResult` fields directly:

- `action_index`
- `action_name`
- `probabilities`
- `distances`
- `confidence`
- `entropy`
- `confidence_gap`

Do not recompute `action_index` with `argmax` when `ScoringResult.action_index` is already present.

### Update

Exact update signature:

```python
ProfileScorer.update(
    self,
    f: np.ndarray,
    category_index: int,
    action_index: int,
    correct: bool,
    gt_action_index: int | None = None,
    confidence: float | None = None,
) -> CentroidUpdate
```

Correct outcome call:

```python
scorer.update(
    f=factor_vector,
    category_index=category_index,
    action_index=predicted_action_index,
    correct=True,
    confidence=score_result.confidence,
)
```

Incorrect outcome call when ground truth is known:

```python
scorer.update(
    f=factor_vector,
    category_index=category_index,
    action_index=predicted_action_index,
    correct=False,
    gt_action_index=actual_action_index,
    confidence=score_result.confidence,
)
```

For `correct=False`, pass `gt_action_index` whenever the verified action is known. Omitting it triggers a deprecated push-predicted-only path.

Use these `CentroidUpdate` fields:

- `centroid_delta_norm`
- `category_index`
- `action_index`
- `category_name`
- `action_name`
- `decision_count`
- `gt_delta_norm`
- `outcome`

### Centroids

Use the public `centroids` property:

```python
current = scorer.centroids.copy()
scorer.centroids = restored_centroids
```

`scorer.centroids` is a public alias for `self.mu`. Its setter validates finite values and exact shape. Consumer code should not write `scorer.mu` directly.

## 3. Package Structure

Create the package structure in implementation prompts:

```text
compounding_scorer/__init__.py
compounding_scorer/config.py
compounding_scorer/storage.py
compounding_scorer/fingerprint.py
compounding_scorer/trajectory.py
compounding_scorer/scorer.py
compounding_scorer/presets/__init__.py
tests/conftest.py
tests/test_storage.py
tests/test_fingerprint.py
tests/test_trajectory.py
tests/test_scorer.py
data/.gitkeep
```

Do not create package source or tests in the planning prompt. This document only defines the implementation contract.

## 4. Implementation Contract

### DomainShape

`DomainShape` is a frozen dataclass describing tensor dimensions:

```python
@dataclass(frozen=True)
class DomainShape:
    n_categories: int
    n_actions: int
    n_factors: int
```

It should expose or support validation of:

```python
tensor_shape == (n_categories, n_actions, n_factors)
tensor_size == n_categories * n_actions * n_factors
```

### DomainPreset

`DomainPreset` is a protocol for domain adapters:

```python
class DomainPreset(Protocol):
    name: str
    shape: DomainShape
    categories: list[str]
    actions: list[str]
    factors: list[str]
    centroids: np.ndarray

    def factor_vector(self, item: Mapping[str, Any]) -> np.ndarray: ...
```

`PRESET_REGISTRY` remains empty in Block B. Real preset implementations are separate prompts.

### DecisionStore

`DecisionStore` owns the SQLite connection and persistence behavior.

Responsibilities:

- Create schema if absent.
- Insert decisions.
- Insert verified outcomes.
- Save centroid checkpoints.
- Load latest centroid checkpoint.
- Return decision history for fingerprint and trajectory computation.
- Serialize NumPy arrays and dictionaries as JSON.

### FactorFingerprint / FingerprintResult

`FactorFingerprint` computes factor noise and precision evidence from stored decisions/outcomes.

`FingerprintResult` should include:

- `n_decisions`
- `n_outcomes`
- `status`
- `factor_weights`
- `factor_sigma`
- `per_category_precision`
- `insufficient_data`

### TrajectoryPoint / TrajectoryResult

`TrajectoryPoint` captures one trajectory checkpoint:

- `decisions`
- `timestamp`
- `iks`
- `win_rate`
- `confidence`
- optional `notes`

`TrajectoryResult` captures:

- `points`
- `current_iks`
- `current_win_rate`
- `days_active`
- `source`

### ScoreResult / LearnResult

`ScoreResult` is the package-facing score response:

- `decision_id`
- `category_index`
- `category_name`
- `action_index`
- `action_name`
- `probabilities`
- `confidence`
- `entropy`
- `confidence_gap`
- `factor_vector`
- `timestamp`

`LearnResult` is the package-facing learning response:

- `decision_id`
- `correct`
- `predicted_action_index`
- `actual_action_index`
- `centroid_delta_norm`
- `gt_delta_norm`
- `gae_outcome`
- `decision_count`
- `checkpoint_saved`

### CompoundingScorer

Required methods:

```python
class CompoundingScorer:
    @classmethod
    def from_preset(cls, preset: DomainPreset, db_path: str | Path | None = None) -> "CompoundingScorer": ...

    def score(self, item: Mapping[str, Any], category: str | int) -> ScoreResult: ...

    def learn(
        self,
        decision_id: str,
        actual_action: str | int,
        correct: bool | None = None,
    ) -> LearnResult: ...

    def fingerprint(self) -> FingerprintResult: ...

    def trajectory(self) -> TrajectoryResult: ...

    def export(self, path: str | Path) -> None: ...

    @classmethod
    def load(cls, path: str | Path, preset: DomainPreset, db_path: str | Path | None = None) -> "CompoundingScorer": ...

    def _compute_iks(self) -> float: ...
```

Implementation notes:

- `score()` calls preset factorization, resolves category index, calls `ProfileScorer.score(f, category_index)`, persists the decision, and returns a package `ScoreResult`.
- `learn()` loads the stored decision, resolves the actual action, calls `ProfileScorer.update(...)`, persists outcome, and checkpoints centroids.
- `_compute_iks()` must reflect learned compounding evidence from decisions/outcomes/checkpoints, not merely expert-prior centroid separation.

## 5. Storage Contract

SQLite tables:

### decisions

Required columns:

- `decision_id TEXT PRIMARY KEY`
- `created_at REAL NOT NULL`
- `category_index INTEGER NOT NULL`
- `category_name TEXT NOT NULL`
- `action_index INTEGER NOT NULL`
- `action_name TEXT NOT NULL`
- `confidence REAL NOT NULL`
- `probabilities_json TEXT NOT NULL`
- `factor_vector_json TEXT NOT NULL`
- `item_json TEXT NOT NULL`
- `metadata_json TEXT NOT NULL DEFAULT '{}'`

### outcomes

Required columns:

- `outcome_id INTEGER PRIMARY KEY AUTOINCREMENT`
- `decision_id TEXT NOT NULL`
- `created_at REAL NOT NULL`
- `correct INTEGER NOT NULL`
- `predicted_action_index INTEGER NOT NULL`
- `predicted_action_name TEXT NOT NULL`
- `actual_action_index INTEGER NOT NULL`
- `actual_action_name TEXT NOT NULL`
- `centroid_delta_norm REAL NOT NULL`
- `gt_delta_norm REAL NOT NULL DEFAULT 0.0`
- `gae_outcome TEXT NOT NULL`
- `metadata_json TEXT NOT NULL DEFAULT '{}'`

### centroid_checkpoints

Required columns:

- `checkpoint_id INTEGER PRIMARY KEY AUTOINCREMENT`
- `created_at REAL NOT NULL`
- `decision_count INTEGER NOT NULL`
- `centroids_json TEXT NOT NULL`
- `shape_json TEXT NOT NULL`
- `metadata_json TEXT NOT NULL DEFAULT '{}'`

JSON serialization behavior:

- Convert NumPy arrays to plain Python lists before `json.dumps`.
- Convert NumPy scalar values to Python `float` or `int`.
- Use stable key ordering where useful for test determinism.
- On load, convert centroid JSON back to `np.ndarray(dtype=np.float64)`.
- Validate restored centroid shape before assigning `scorer.centroids`.

## 6. Fingerprint Contract

If fewer than 5 decisions exist:

- Return `insufficient_data=True`.
- Return status such as `"insufficient_data"`.
- Return default weights normalized across factors, for example uniform `1.0`.
- Return empty or default sigma evidence.
- Do not claim learned factor precision.

For sufficient data:

- Use stored decision factor vectors and verified outcomes.
- Compute pooled sigma across correct and incorrect decisions per factor.
- Convert lower-noise factors to higher precision weights.
- Normalize weights to `[0, 1]`.
- Preserve factor order from the preset.
- Compute per-category precision only for categories with at least 3 decisions.
- Categories with fewer than 3 decisions should be omitted or marked insufficient.

## 7. Trajectory Contract

If no decisions exist:

- Return exactly one point.
- `decisions=0`
- `iks=0.0`
- `win_rate=0.50`
- `current_iks=0.0`
- `current_win_rate=0.50`
- `days_active=0`
- source should indicate cold start or empty history.

For non-empty history:

- Add a trajectory point every 10 decisions.
- Always add a final point if the latest decision is not already represented by the last 10-decision checkpoint.
- `current_iks` and `current_win_rate` come from the last point.
- `days_active` is computed from first decision timestamp to last decision timestamp.
- Points must be ordered by decision count ascending.
- Win rate uses verified outcomes; if no outcomes exist, use neutral `0.50`.

## 8. Test Plan

### Storage tests, at least 7

- Initializes SQLite schema.
- Inserts and retrieves a decision.
- Stores probabilities and factor vectors as JSON.
- Inserts and retrieves an outcome.
- Saves centroid checkpoint.
- Loads latest centroid checkpoint.
- Handles missing checkpoint cleanly.
- Persists across store reopen.

### Fingerprint tests, at least 5

- Fewer than 5 decisions returns insufficient data defaults.
- Computes pooled sigma from mixed correct/incorrect outcomes.
- Normalizes weights to `[0, 1]`.
- Preserves preset factor order.
- Computes per-category precision only for categories with at least 3 decisions.

### Trajectory tests, at least 4

- Empty decisions returns one cold-start point with `iks=0.0` and `win_rate=0.50`.
- Produces checkpoints every 10 decisions.
- Includes final non-multiple-of-10 point.
- Computes `current_iks`, `current_win_rate`, and `days_active` from last/first history.

### Scorer tests, at least 9

- Use `pytest.importorskip` or test `sys.path` setup for GAE.
- Construct `CompoundingScorer` directly with `MockPreset`.
- Keep `PRESET_REGISTRY` empty.
- Builds `ProfileScorer` using `mu=...`, not `centroids=...`.
- `score()` returns GAE `action_index` directly.
- `score()` persists a decision.
- `learn(correct=True)` calls `ProfileScorer.update()` with correct arguments.
- `learn(correct=False)` passes `gt_action_index`.
- `learn()` saves outcome and centroid checkpoint.
- `export()` writes centroids and metadata.
- `load()` restores via `scorer.centroids`.
- Unknown category/action validation errors are clear.

## 9. Validation Commands

Run from the target repo:

```powershell
python -m pytest tests\test_storage.py tests\test_fingerprint.py tests\test_trajectory.py -v --timeout=120
python -m pytest tests\test_scorer.py -v --timeout=120
python -m pytest tests\ -v --timeout=120
python -c "from compounding_scorer import CompoundingScorer; print('import OK')"
```

## 10. Scope Guardrails

- Do not edit `graph-attention-engine-v50`.
- Do not edit `gen-ai-roi-demo-v4-v50`.
- Do not edit `s2p-copilot`.
- Do not edit `ci-platform`.
- Do not add pip packaging yet.
- Do not add package/build/config files unless a later prompt explicitly authorizes them.
- Preset implementations are separate prompts.
- `PRESET_REGISTRY` remains empty for now.
- Positive scorer tests should use a local `MockPreset`.
- Block B implementation should be repo-local to `compounding-scorer`.
