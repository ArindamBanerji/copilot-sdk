# REV-STEP12: F-09 Governed Transfer Source Artifacts — Diagnostic and Fixer Design

REV-STEP11-FIXER is recorded as **PASS**. The SDK baseline remains **4,435 passed, 1 xfailed**. No Step 12 completion entry existed before this diagnostic.

## Deliverable 1 — Diagnostic report

### Transfer router

- **A1 — Synthetic helper:** `_demo_patterns_for_mapping()` is absent.
- **A2 — Governed lookup:** `_patterns_for_execute()` spans `copilot_sdk/backend/transfer_router.py:699-722`. It:
  - Selects an explicit or scorer-attached registry.
  - Otherwise constructs `SharedPatternRegistry(store, source_domain)`.
  - Filters by `source_copilot`.
  - Returns `(registered, "governed")` or `([], "governed")`.
- **A3 — Artifact validation:** `_validate_source_artifacts()`, lines 548–560, calls `store.get_governance(source_domain, artifact_id)`. It is called by:
  - Legacy endpoint: line 135.
  - Self-transfer endpoint: line 294.
  - Checkpoint boundary: line 839.
- **A4 — Conservation validation:** The implemented helper is named `_require_conservation_threshold()`, lines 563–605. It:
  - Requires `ProtocolV2GraphStore`.
  - Calls `get_conservation_state(domain)`.
  - Normalizes `verified_count`, `correct_count`, `q`, `alpha`, `theta_min`, and `status`.
  - Requires `GREEN` and `alpha * q * V >= theta_min`.
  - Fails closed with HTTP 409.
  - Is called for both domains at lines 133–134 and 292–293.
- **A5 — Checkpoint:** `_save_transfer_checkpoint()`, lines 822–868:
  - Revalidates source artifacts.
  - Persists source/target conservation evidence, artifact IDs, mapping, timestamp, and `"governed"` provenance.
  - Calls `save_governance(..., {"kind": "transfer_checkpoint", ...})`.
  - Retains `save_centroids(domain, "transfer_event", ...)`.
- **A6 — Transfer event:** `_log_transfer_event()`, lines 754–800:
  - Accepts artifact IDs, mapping, and conservation evidence.
  - Generates its own timestamp.
  - Hardcodes `"provenance": "governed"`.
  - Delegates checkpoint persistence for the target and optional source store.
  - Does not accept `validation_timestamp` or `transfer_provenance` as explicit parameters.
- **A9:** `TransferExecuteRequest`, lines 34–38:
  - `source_domain: str`
  - `target_domain: str`
  - `source_artifact_ids: list[str]`
  - `dry_run: bool = True`
- **A10:** `CrossCopilotTransferRequest`, lines 41–44:
  - `source_domain: str`
  - `target_domain: str`
  - `source_artifact_ids: list[str]`

Pydantic 2.12.5 is installed, but these models use simple annotation syntax without `Field`, `field_validator`, or `model_validator`. Endpoint helper `_normalize_source_artifact_ids()` rejects empty lists and empty strings.

#### Legacy endpoint order

`transfer_execute()` currently executes:

1. Normalize source and target domains.
2. Resolve and validate category mapping.
3. Resolve own domain and graph store.
4. Normalize artifact IDs.
5. Validate source conservation.
6. Validate target conservation.
7. Validate source artifacts.
8. Load governed patterns.
9. Reject an empty pattern list.
10. Return dry-run projection, if requested.
11. Verify target equals the router’s domain.
12. Call `warm_start()`.
13. Reset conservation projection if applicable.
14. Persist transfer checkpoint/event.
15. Update `_warm_start_info`.
16. Return response.

#### Self-transfer endpoint order

`transfer()` currently executes:

1. Normalize source and target domains.
2. Validate domain identities and target ownership.
3. Resolve mapping.
4. Resolve graph store.
5. Normalize artifact IDs.
6. Validate source conservation.
7. Validate target conservation.
8. Validate source artifacts.
9. Compute transfer ID.
10. Check whether the transfer edge already exists.
11. Load governed patterns.
12. Reject an empty pattern list.
13. Call `warm_start()`.
14. Handle skipped or incompatible results.
15. Persist checkpoint/event.
16. Write the transfer-pattern edge.
17. Return response.

The requested order was patterns → artifacts → source conservation → target conservation.

#### Remaining vocabulary

- `/api/transfer/demo` remains as a persisted-graph display endpoint at lines 92–114; it does not synthesize patterns.
- No `"demo"` or `"synthetic"` provenance remains in execution.
- Line 478 retains `"transfer"` as the default for an observational status projection. It is outside transfer execution.

### Registry

`SharedPatternRegistry` in `copilot_sdk/transfer/registry.py:75` supports read-only construction with `(graph_store: GraphStore, domain: str)`.

`register()` at line 91 accepts `graph_store: GraphStore | None = None`. When supplied, it:

- Reads `pattern.metadata["source_artifact_id"]`.
- Uses `pattern.source_domain` or `source_copilot`.
- Calls `graph_store.get_governance()`.
- Raises `ValueError("Source artifact not registered")` when missing.

It persists under `transfer_pattern:{pattern_id}` in the registry domain. Omitting `graph_store` preserves previous behavior.

### Conservation storage

`get_conservation_state` is not part of `GraphStore` or `ProtocolV2GraphStore`. It belongs to `L5LearningStore` in `copilot_sdk/graph/protocol.py:550`, with:

```python
def get_conservation_state(self, domain: str) -> dict | None
```

There is no `save_conservation_state`. Test setup uses:

```python
def update_conservation_state(
    self,
    domain: str,
    status: str,
    alpha: float,
    q: float,
    V: int,
    theta_min: float,
    product: float,
    categories_total: int,
    categories_with_data: int,
    baseline_product: float,
    relative_threshold: float,
    complacency_flag: str,
    caused_by_decision_id: str | None = None,
    old_status: str | None = None,
) -> str
```

The in-memory implementation stores `domain`, `status`, `alpha`, `q`, `V`, `theta_min`, `product`, coverage counts, baseline/relative thresholds, complacency state, IDs, and timestamps.

Graph governance signatures are:

```python
save_governance(domain: str, key: str, state: dict[str, Any]) -> None
get_governance(domain: str, key: str) -> dict[str, Any] | None
list_governance(domain: str) -> list[dict[str, Any]]
```

### Conservation formula

`compute_theta_min` is external to `copilot_sdk`:

- File: `graph-attention-engine-v50/gae/calibration.py`
- Line: 194
- Import: `from gae.calibration import compute_theta_min`
- Signature: `compute_theta_min(alpha: float, V: float) -> float`
- Formula: `23.53 / (alpha * V)`, with infinity returned for nonpositive inputs.

### Tests

`tests/test_transfer_governed_source.py` contains 12 functions and collects **15 cases**:

- Synthetic removal and governed lookup: 4 cases.
- Artifact validation: 3 cases.
- Conservation: 3 cases.
- Persistence: 1 combined case.
- Registry validation: 4 cases because the missing-artifact test is parameterized with missing and empty IDs.

All tests use `InMemoryGraphStore`, a local `_Scorer`, `update_conservation_state()`, `save_governance()`, and `SharedPatternRegistry`.

Asserted provenance is exclusively `"governed"`.

No other test file references the specified request classes or private transfer helpers. The full suite confirms compatibility.

Verification:

- Focused tests: **15 passed**
- SDK_ROOT: **4,435 passed, 1 xfailed**
- Mypy: **clean**
- Synthetic helper scan: clean
- `save_governance`: present
- `save_centroids`: present
- Namespace invariant command: passed

## Deliverable 2 — Findings table

| # | Requirement | Status | Severity | Detail |
|---|---|---|---|---|
| 1 | Synthetic fallback removed | DONE | OK | Helper absent; no synthetic execution provenance. |
| 2 | Governed pattern provenance | DONE | OK | Lines 699–722 return `"governed"` in both branches. |
| 3 | Empty patterns produce 422 | DONE | OK | Both endpoints reject before dry-run or mutation. |
| 4 | Required artifact IDs | DONE | OK | Both models require the field; lines 541–545 reject empty inputs. |
| 5 | Governance artifact validation | DONE | OK | Endpoint and checkpoint-boundary validation are present. |
| 6 | Live conservation revalidation | PARTIAL | P2 | Runtime behavior is correct, but lines 563–570 type/check against `ProtocolV2GraphStore`, which does not define `get_conservation_state`; the capability belongs to `L5LearningStore`. |
| 7 | Endpoint validation order | WRONG | P2 | Both endpoints evaluate conservation and artifacts before discovering that no governed patterns exist. |
| 8 | Governed provenance persistence | PARTIAL | P2 | Persisted data is complete, but timestamp and provenance are generated/hardcoded inside helpers instead of being explicit parameters threaded from the endpoint. |
| 9 | Registry validation | DONE | OK | Optional validation store and backward-compatible path are implemented. |
| 10 | Seventeen focused tests | PARTIAL | P2 | Only 15 cases collect. Four persistence requirements are consolidated into one test, while registry rejection has an extra parameterized case. Boundary/order coverage is incomplete. |
| 11 | Step 12 session record | MISSING | P2 | No Step 12 completion record existed before this diagnostic. |
| 12 | Existing test compatibility | DONE | OK | Full suite passes at baseline; no other tests reference the changed request/helper APIs. |

## Deliverable 3 — Fixer design

### A. Changes required

#### 1. Use the actual conservation capability

File: `copilot_sdk/backend/transfer_router.py:21`

Current:

```python
from copilot_sdk.graph.protocol import GraphStore, ProtocolV2GraphStore
```

Replacement:

```python
from copilot_sdk.graph.protocol import GraphStore, L5LearningStore
```

Current lines 563–570:

```python
def _require_conservation_threshold(store: Any, domain: str) -> dict[str, Any]:
    if not isinstance(store, ProtocolV2GraphStore):
        raise HTTPException(...)
    try:
        state = store.get_conservation_state(domain)
```

Replacement:

```python
def _validate_conservation_threshold(
    store: Any,
    domain: str,
) -> dict[str, Any]:
    if not isinstance(store, L5LearningStore):
        raise HTTPException(
            status_code=409,
            detail=f"Conservation threshold not met for {domain}",
        )
    try:
        state = store.get_conservation_state(domain)
```

Retain the current normalization, canonical formula, fail-closed behavior, and return structure.

Blast radius: two endpoints and focused tests referring to the private helper. No protocol change.

#### 2. Reorder validation

Legacy current lines 132–148:

```python
source_artifact_ids = _normalize_source_artifact_ids(request.source_artifact_ids)
source_conservation = _require_conservation_threshold(store, source_domain)
target_conservation = _require_conservation_threshold(store, target_domain)
_validate_source_artifacts(store, source_domain, source_artifact_ids)

patterns, provenance = _patterns_for_execute(...)
if not patterns:
    raise HTTPException(...)
```

Replacement:

```python
source_artifact_ids = _normalize_source_artifact_ids(request.source_artifact_ids)
patterns, provenance = _patterns_for_execute(
    scorer,
    source_domain,
    target_domain,
    mapping,
    pattern_registry,
)
if not patterns:
    raise HTTPException(
        status_code=422,
        detail="No governed transfer patterns available. Register source artifacts first.",
    )

_validate_source_artifacts(store, source_domain, source_artifact_ids)
source_conservation = _validate_conservation_threshold(store, source_domain)
target_conservation = _validate_conservation_threshold(store, target_domain)
```

Apply the same order to self-transfer before `warm_start()`.

This ensures authoritative absence of governed source material returns 422 without requiring unrelated conservation state.

#### 3. Make persistence evidence explicit

Replace `_log_transfer_event()`’s evidence arguments with keyword-only names:

```python
def _log_transfer_event(
    scorer: Any,
    source_domain: str,
    target_domain: str,
    categories_mapped: int,
    patterns_applied: int,
    *,
    source_conservation_state: dict[str, Any],
    target_conservation_state: dict[str, Any],
    source_artifact_ids: list[str],
    mapping_details: dict[str, str],
    validation_timestamp: str,
    transfer_provenance: str,
) -> None:
```

Construct the event with those values instead of generating or hardcoding them:

```python
event = {
    "source": "transfer_event",
    "source_domain": source_domain,
    "target_domain": target_domain,
    "categories_mapped": categories_mapped,
    "patterns_applied": patterns_applied,
    "source_conservation_state": _checkpoint_conservation(
        source_conservation_state
    ),
    "target_conservation_state": _checkpoint_conservation(
        target_conservation_state
    ),
    "source_artifact_ids": list(source_artifact_ids),
    "mapping_details": dict(mapping_details),
    "validation_timestamp": validation_timestamp,
    "transfer_provenance": transfer_provenance,
    "provenance": transfer_provenance,
    "timestamp": int(time.time()),
}
```

Extend `_save_transfer_checkpoint()` with the same explicit names and use:

```python
"transfer_provenance": transfer_provenance
```

Generate once in each endpoint after successful mutation:

```python
validation_timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
```

Pass `"governed"` explicitly. Preserve `save_governance`, `save_centroids`, source-artifact revalidation, and self-transfer checkpoint persistence.

#### 4. Complete the focused tests and session record

Restructure the focused file to collect 17 cases. After the fixer passes, append the actual Step 12 completion record; do not treat the diagnostic record as completion.

### B. Missing and restructured tests

The four required persistence test names are absent, although one combined test currently contains their assertions. Replace that combined test with four tests using the existing `_Scorer`, `_seed`, and `_client` infrastructure.

Example common helper:

```python
def _checkpoint(scorer: _Scorer) -> dict[str, Any]:
    response = _client(scorer).post("/api/transfer/execute", json=_payload())
    assert response.status_code == 200
    records = [
        row
        for row in scorer.graph_store.list_governance(TARGET)
        if row.get("kind") == "transfer_checkpoint"
    ]
    assert len(records) == 1
    return records[0]
```

Tests:

```python
def test_governance_event_includes_source_conservation() -> None:
    scorer = _Scorer()
    _seed(scorer)
    record = _checkpoint(scorer)
    assert record["source_conservation_state"] == {
        "verified_count": 20,
        "correct_count": 18,
        "q": 0.9,
    }


def test_governance_event_includes_target_conservation() -> None:
    scorer = _Scorer()
    _seed(scorer)
    record = _checkpoint(scorer)
    assert record["target_conservation_state"] == {
        "verified_count": 20,
        "correct_count": 18,
        "q": 0.9,
    }


def test_governance_event_includes_artifact_ids_and_mapping() -> None:
    scorer = _Scorer()
    _seed(scorer)
    record = _checkpoint(scorer)
    assert record["source_artifact_ids"] == [ARTIFACT]
    assert record["mapping_details"] == get_mapping(SOURCE, TARGET)


def test_governance_event_has_timestamp_and_provenance() -> None:
    scorer = _Scorer()
    _seed(scorer)
    record = _checkpoint(scorer)
    assert datetime.fromisoformat(
        record["validation_timestamp"].replace("Z", "+00:00")
    ).tzinfo is not None
    assert record["transfer_provenance"] == "governed"
```

To reach 17 rather than 18, replace the two-case registry parameterization with one collected test that loops over both invalid values:

```python
def test_register_with_missing_artifact_raises_valueerror() -> None:
    store = InMemoryGraphStore()
    registry = SharedPatternRegistry(store, SOURCE)
    for artifact_id in ("artifact:missing", ""):
        with pytest.raises(ValueError, match="Source artifact not registered"):
            registry.register(_pattern(artifact_id=artifact_id), graph_store=store)
```

Strengthen existing tests without increasing collection count:

- No-pattern tests should omit conservation/artifact setup, proving pattern lookup runs first.
- The missing-artifact test should also issue requests with `[]` and `[""]`.
- One persistence test should use the self-transfer router and verify its checkpoint.
- A persistence test should directly exercise checkpoint artifact revalidation.
- The conservation test should include missing-state behavior.

### C. Validation-order assessment

The current order is not acceptable for the specified contract. A request with no governed patterns can return 409 for missing conservation or 422 for an artifact before reporting the authoritative problem: no transferable governed source exists.

Recommended order after mapping/domain validation:

1. Normalize artifact IDs.
2. Load governed patterns.
3. Reject empty patterns with 422.
4. Validate source artifacts.
5. Validate source conservation.
6. Validate target conservation.
7. Apply dry-run projection or warm-start mutation.
8. Persist checkpoint/event.
9. Write the self-transfer edge when applicable.
10. Return response.

The self-transfer duplicate-edge check may remain before mutation, but should not replace governed-source validation for a new transfer.

### D. Negative constraints

The fixer must not:

- Modify files outside `transfer_router.py`, `transfer/registry.py`, tests, and the final session-state append.
- Change `GraphStore`, `ProtocolV2GraphStore`, or `L5LearningStore`.
- Change `GraphStoreNamespace`, `scorer.py`, or `engine.py`.
- Change preseed scripts.
- Change conservation or evolution routers.
- Change application `main.py` files.
- Remove `save_centroids`.
- Remove checkpoint-boundary artifact validation.
- Add dependencies.
- Restore synthetic patterns or stale execution provenance.

### E. Fixer prompt outline

1. Read the diagnostic session entry, transfer router, registry, L5 protocol, and focused tests.
2. Capture SDK and focused baselines.
3. Change the conservation helper to use `L5LearningStore`.
4. Reorder both endpoint validation paths.
5. Make timestamp, evidence, mapping, artifacts, and provenance explicit persistence inputs.
6. Preserve additive governance and centroid persistence.
7. Split the combined persistence test, consolidate registry rejection, and strengthen order/boundary assertions.
8. Run focused tests and require 17 passing.
9. Run mypy on both changed source files.
10. Run the full SDK suite and require at least 4,435 passed with no new failures.
11. Run synthetic/provenance/persistence architecture checks.
12. Append the Step 12 completion record.

The diagnostic entry was appended to `docs/session_state.md`.
