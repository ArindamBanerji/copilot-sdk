# VLD Branch Shape Diagnosis - 2026-09-11

## 1. Root Cause

`copilot_sdk/scoring/investigation.py` does not produce a `branch` or `branches` field at all. The VLD core trace shape is a stable `steps` list:

```python
# copilot_sdk/scoring/investigation.py
12: class InvestigationStep:
13:     step: int
14:     dimension: int
15:     factor_name: str
...
29: class InvestigationTrace:
30:     decision_id: str
31:     category: str
32:     budget: int
33:     steps: list[InvestigationStep]
```

The investigation loop always appends `InvestigationStep` objects when evidence exists and skips appending when the evidence provider returns `None`:

```python
130: steps: list[InvestigationStep] = []
131: for step_index in range(budget):
...
138: evidence = evidence_provider.read_evidence(...)
139: enriched.add(k_star)
140: if evidence is None:
141:     continue
...
153: steps.append(InvestigationStep(...))
171: return InvestigationTrace(..., steps=steps, ...)
```

`copilot_sdk/backend/investigation_router.py` also preserves this shape:

```python
24: class InvestigationResponse(BaseModel):
35:     steps: list[dict[str, Any]]
...
105: "steps": [asdict(step) for step in trace.steps],
```

So the branch-shape inconsistency is not a VLD core trace bug. The root cause is Stage 1 multihop scenario schema drift:

- Current raw Stage 1 JSON in Trading, Purchasing, DataOps, SOC, and S2P stores `available_branches`, `correct_branches`, and `misleading_branches` as lists.
- Older evaluator/test/validator code expected `available_branches` and `correct_branches` as dicts keyed by hop/step, for example `scenario["correct_branches"]["1"][0]` or `scenario["available_branches"].values()`.
- The evaluator scripts now contain normalizers that convert both shapes into the older internal dict-by-step shape before evaluation. Focused multihop tests pass in the current checkout because test fixtures call `load_scenarios()` or `load_stage1()`, which normalize.

Raw data shape confirmed:

| Domain | Raw `available_branches` | Raw `correct_branches` | Raw `misleading_branches` |
| --- | --- | --- | --- |
| Trading | list in 50/50 scenarios | list in 50/50 scenarios | list in 50/50 scenarios |
| Purchasing | list in 50/50 scenarios | list in 50/50 scenarios | list in 50/50 scenarios |
| DataOps | list in 50/50 scenarios | list in 50/50 scenarios | list in 50/50 scenarios |
| SOC | list in 50/50 scenarios | list in 50/50 scenarios | list in 50/50 scenarios |
| S2P | list in 50/50 scenarios | list in 50/50 scenarios | list in 50/50 scenarios |

## 2. Consumption Inventory

Total files found reading branch fields or branch trace rows: 18.

### Core VLD

`copilot_sdk/scoring/investigation.py`

- Lines 12-25: `InvestigationStep`, no branch field.
- Lines 29-37: `InvestigationTrace`, `steps` only.
- Lines 130-175: produces `steps: list[InvestigationStep]`.
- Shape: list of dataclasses.
- Status: pass; not the bug source.

`copilot_sdk/backend/investigation_router.py`

- Lines 24-36: response model has `steps: list[dict[str, Any]]`.
- Line 105: returns `[asdict(step) for step in trace.steps]`.
- Shape: list of dicts from VLD steps.
- Status: pass; no branch post-processing.

### Stage 1 evaluator scripts

`apps/trading/backend/scripts/evaluate_multihop_stage1.py`

- Lines 66-146: `_branch_id`, `_branch_prerequisites`, `_branch_record_steps`, `_group_branch_ids_by_step`, `_normalize_scenario_branches`.
- Lines 190-197: `ScenarioGraphStore` normalizes then stores `correct_by_step`, `available_by_step`, `misleading`.
- Lines 245-248: `load_scenarios()` normalizes selected scenarios.
- Lines 405-423: `breadth()` and `content_rule()` iterate normalized dict keys.
- Shape accepted at boundary: list or dict. Internal canonical shape: dict[str step, list[str branch_id]].
- Status: focused test passed, `12 passed`.

`apps/purchasing/backend/scripts/evaluate_multihop_stage1.py`

- Lines 82-162: same normalizer pattern.
- Lines 190-199: `ScenarioGraphStore` normalizes before dict access.
- Lines 231-235: `load_scenarios()` normalizes primary 40 records.
- Lines 413-428: arms read via `ScenarioGraphStore` and normalized helpers.
- Shape accepted at boundary: list or dict. Internal canonical shape: dict-by-step.
- Status: focused test passed, `12 passed`.

`apps/dataops/backend/scripts/evaluate_multihop_stage1.py`

- Lines 65-145: same normalizer pattern.
- Lines 173-180: `ScenarioGraphStore` normalizes before dict access.
- Lines 212-213: `load_scenarios()` normalizes.
- Lines 340-358: arms iterate normalized dict keys.
- Shape accepted at boundary: list or dict. Internal canonical shape: dict-by-step.
- Status: focused test passed, `10 passed`.

`../gen-ai-roi-demo-v4-v50/backend/scripts/evaluate_multihop_stage1.py`

- Lines 77-157: same normalizer pattern.
- Lines 177-187: `ScenarioGraphStore` normalizes before dict access.
- Lines 250-251: `load_scenarios()` normalizes.
- Lines 282-325: selection helpers assume normalized dict-by-step scenarios.
- Shape accepted at boundary: list or dict. Internal canonical shape: dict-by-step.
- Status: focused test passed, `11 passed`.

`../s2p-copilot/backend/scripts/evaluate_multihop_stage1.py`

- Lines 52-55: `load_stage1()` normalizes all scenarios.
- Lines 58-138: same normalizer pattern.
- Lines 183-201: `ScenarioGraphStore` normalizes before building evidence map.
- Lines 301-320: arms use `ScenarioGraphStore`.
- Shape accepted at boundary: list or dict. Internal canonical shape: dict-by-step.
- Status: focused test passed, `10 passed`.

### Stage 1 tests

`apps/trading/backend/tests/test_multihop_evaluation.py`

- Lines 18-27: `_scenario()` reads through `mh.load_scenarios()`, so data is normalized.
- Lines 41-42: expects `correct_branches` dict and `misleading_branches` list.
- Lines 63, 72-73: expects trace rows with `branch_name` and normalized `correct_branches.values()`.
- Status: pass now.

`apps/purchasing/backend/tests/test_multihop_evaluation.py`

- Lines 23-28: reads through normalized `mh.load_scenarios()`.
- Lines 42-43: expects `correct_branches` dict and `misleading_branches` list.
- Lines 65, 74-76: expects trace rows with `branch_name` and normalized `correct_branches.values()`.
- Status: pass now.

`apps/dataops/backend/tests/test_multihop_evaluation.py`

- Lines 19-28: `_scenario()` reads through normalized `mh.load_scenarios()`.
- Lines 42-43: expects `correct_branches` dict and `misleading_branches` list.
- Lines 63, 72-73: expects trace rows with `branch_name` and normalized `correct_branches.values()`.
- Status: pass now.

`../gen-ai-roi-demo-v4-v50/backend/tests/test_multihop_evaluation.py`

- Lines 24-26: fixture reads through normalized `load_scenarios(DATA_PATH)`.
- Lines 31, 60, 67, 110: expects dict-by-step branches.
- Lines 32-42: verifies evidence by branch name.
- Lines 74-76: verifies VLD read branches.
- Status: pass now.

`../s2p-copilot/backend/tests/test_multihop_evaluation.py`

- Lines 25-26: reads through normalized `load_stage1()`.
- Lines 47, 53-54, 79: uses `ScenarioGraphStore` accessors and raw `misleading_branches` list.
- Status: pass now.

`../gen-ai-roi-demo-v4-v50/backend/tests/test_multihop_wiring.py`

- Line 21 imports `evaluate_all`.
- Lines 59-69 verify scenario branch behavior through service/evaluator outputs, not raw branch-shape access.
- Status: not a direct shape consumer; include in post-fix smoke tests.

### Validators and runtime services

The five `scripts/validate_stage1.py` files still assume raw dict-by-step branch data:

- `apps/trading/backend/scripts/validate_stage1.py` lines 64-70, 111.
- `apps/purchasing/backend/scripts/validate_stage1.py` lines 66-72, 113.
- `apps/dataops/backend/scripts/validate_stage1.py` lines 65-71, 111.
- `../gen-ai-roi-demo-v4-v50/backend/scripts/validate_stage1.py` lines 66-72, 112.
- `../s2p-copilot/backend/scripts/validate_stage1.py` lines 64-70, 110.

Current status: they fail before branch validation on edge schema drift (`KeyError: 'from'` at line 44-46 depending on domain), but if edge schema were fixed first they would still need branch normalization because current raw JSON branch fields are lists.

SOC runtime services:

- `../gen-ai-roi-demo-v4-v50/backend/app/services/multihop_scenarios.py` lines 37-115 define the same normalizer and lines 124, 227 apply it.
- `../gen-ai-roi-demo-v4-v50/backend/app/services/investigation_patterns.py` lines 322-328 assume the incoming scenario is already normalized.

## 3. Shared Infrastructure

There is no shared cross-repo evaluator module. Each copilot owns a near-copy of `scripts/evaluate_multihop_stage1.py`.

Current importer pattern:

- Trading, Purchasing, and DataOps tests dynamically import their local evaluator script with `importlib.util.spec_from_file_location`.
- SOC and S2P tests import from local `scripts.evaluate_multihop_stage1`.
- SOC runtime has a separate `app/services/multihop_scenarios.py` implementation with the same normalization logic.

The copied normalizer is the effective fix point today, but it is duplicated. There should be one shared helper for:

- extracting a branch id from either a string or dict record,
- deriving step from prerequisites,
- normalizing `available_branches` and `correct_branches` to dict-by-step,
- copying `read_cost` from list records into `read_costs`.

Because the repos are separate and this task is diagnosis-only, the design recommendation is to introduce a small shared normalizer per repo boundary first, then consolidate into SDK test/evaluation utilities if all copilot repos can depend on it.

## 4. DataOps Tolerance Analysis

In the current checkout, DataOps tolerance exists in `apps/dataops/backend/scripts/evaluate_multihop_stage1.py`, not inline in `apps/dataops/backend/tests/test_multihop_evaluation.py`.

What was added:

- `_branch_id()` accepts dict records or plain string ids.
- `_branch_prerequisites()` understands `requires_branches`, `prerequisite_branches`, `requires_branch_ids`, and `access.requires_completed_branches`.
- `_branch_record_steps()` computes hop depth from prerequisites.
- `_group_branch_ids_by_step()` accepts either dict-by-step input or list input.
- `_normalize_scenario_branches()` produces dict-by-step `available_branches` and `correct_branches`, and fills `read_costs` from list records.
- `load_scenarios()` and `ScenarioGraphStore.__init__()` call the normalizer.

This is a proper boundary adapter, not merely a test workaround, because it normalizes once at the loader/store boundary and lets evaluator logic remain deterministic. The remaining weakness is duplication: the same adapter exists independently in Trading, Purchasing, DataOps, SOC, and S2P evaluator code.

The DataOps test file itself still expects the normalized dict shape (`scenario["correct_branches"]["1"][0]` and `.values()`), so removing the normalizer would reintroduce the failure.

## 5. Recommended Fix

Recommended classification: **B) `investigation.py` is consistent; the Stage 1 evaluators/tests/validators were wrong or stale for the current JSON schema.**

Canonical external data shape should be the current list-based Stage 1 JSON:

```python
available_branches: list[dict]
correct_branches: list[str]
misleading_branches: list[str]
```

Canonical internal evaluator shape should remain dict-by-step because the arms are step/budget driven:

```python
available_branches: dict[str, list[str]]
correct_branches: dict[str, list[str]]
misleading_branches: list[str]
read_costs: dict[str, int]
```

Fix plan for an implementation prompt:

1. Keep `copilot_sdk/scoring/investigation.py` unchanged.
2. Keep `copilot_sdk/backend/investigation_router.py` unchanged.
3. Preserve the evaluator normalizers already present in Trading, Purchasing, DataOps, SOC, and S2P.
4. Update any remaining raw-data consumers, especially `validate_stage1.py`, to normalize before branch assertions.
5. Make tests explicit that `load_scenarios()`/`load_stage1()` returns normalized scenarios. Avoid direct raw JSON branch indexing in tests unless the test is specifically checking raw schema.
6. Optionally move duplicated normalization into a shared local helper where repository boundaries allow it.

Do not remove DataOps tolerance. It should be kept and preferably moved to shared evaluation infrastructure with the other copied normalizers.

## 6. Blast Radius

Source files that should not be modified for this fix:

- `copilot_sdk/scoring/investigation.py`
- `copilot_sdk/backend/investigation_router.py`

Evaluator/source files that already contain the correct normalization pattern and should be kept aligned:

- `apps/trading/backend/scripts/evaluate_multihop_stage1.py`
- `apps/purchasing/backend/scripts/evaluate_multihop_stage1.py`
- `apps/dataops/backend/scripts/evaluate_multihop_stage1.py`
- `../gen-ai-roi-demo-v4-v50/backend/scripts/evaluate_multihop_stage1.py`
- `../s2p-copilot/backend/scripts/evaluate_multihop_stage1.py`
- `../gen-ai-roi-demo-v4-v50/backend/app/services/multihop_scenarios.py`

Files that still need schema-boundary cleanup:

- `apps/trading/backend/scripts/validate_stage1.py`
- `apps/purchasing/backend/scripts/validate_stage1.py`
- `apps/dataops/backend/scripts/validate_stage1.py`
- `../gen-ai-roi-demo-v4-v50/backend/scripts/validate_stage1.py`
- `../s2p-copilot/backend/scripts/validate_stage1.py`

Tests that should remain in the verification set:

- `apps/trading/backend/tests/test_multihop_evaluation.py`
- `apps/purchasing/backend/tests/test_multihop_evaluation.py`
- `apps/dataops/backend/tests/test_multihop_evaluation.py`
- `../gen-ai-roi-demo-v4-v50/backend/tests/test_multihop_evaluation.py`
- `../gen-ai-roi-demo-v4-v50/backend/tests/test_multihop_wiring.py`
- `../s2p-copilot/backend/tests/test_multihop_evaluation.py`

Total likely implementation file count: 5 validator files if the evaluator normalizers are accepted as already fixed. If consolidation is requested, add 1 shared helper plus 5 evaluator imports/callers, but that is a larger cleanup and not required to resolve current failures.

## 7. Verification

Focused tests run during this diagnosis:

```text
python -m pytest apps\trading\backend\tests\test_multihop_evaluation.py -v --timeout=120
12 passed

python -m pytest apps\purchasing\backend\tests\test_multihop_evaluation.py -v --timeout=120
12 passed

python -m pytest apps\dataops\backend\tests\test_multihop_evaluation.py -q --timeout=120
10 passed

python -m pytest ..\gen-ai-roi-demo-v4-v50\backend\tests\test_multihop_evaluation.py -q --timeout=120
11 passed

python -m pytest ..\s2p-copilot\backend\tests\test_multihop_evaluation.py -q --timeout=120
10 passed
```

Validator status during diagnosis:

```text
apps/trading/backend/scripts/validate_stage1.py
KeyError: 'from'

apps/purchasing/backend/scripts/validate_stage1.py
KeyError: 'from'

apps/dataops/backend/scripts/validate_stage1.py
KeyError: 'from'

../gen-ai-roi-demo-v4-v50/backend/scripts/validate_stage1.py
KeyError: 'from'

../s2p-copilot/backend/scripts/validate_stage1.py
KeyError: 'from'
```

Post-fix verification should run:

```powershell
python -m pytest apps\trading\backend\tests\test_multihop_evaluation.py -q --timeout=120
python -m pytest apps\purchasing\backend\tests\test_multihop_evaluation.py -q --timeout=120
python -m pytest apps\dataops\backend\tests\test_multihop_evaluation.py -q --timeout=120

Set-Location ..\gen-ai-roi-demo-v4-v50\backend
python -m pytest tests\test_multihop_evaluation.py tests\test_multihop_wiring.py -q --timeout=120

Set-Location ..\..\s2p-copilot\backend
python -m pytest tests\test_multihop_evaluation.py -q --timeout=120
```

Validator checks should also be re-run from each backend root after edge schema handling is fixed:

```powershell
python scripts\validate_stage1.py
```

Expected branch-shape grep after a complete fix:

- Evaluators and services may contain `_normalize_scenario_branches`.
- Validators should either import/use the same normalizer or explicitly support list-shaped raw JSON.
- Tests should not perform raw JSON branch-shape assertions unless the test name says it is checking raw Stage 1 schema.
- `copilot_sdk/scoring/investigation.py` and `copilot_sdk/backend/investigation_router.py` should still have no `branch`/`branches` output fields.
