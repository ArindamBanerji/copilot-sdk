# Step 12 Design: Governed Transfer Source Artifacts

Date: 2026-10-07
Status: REVIEWED DESIGN
Finding: F-09

## Section 1: Current State

### Synthetic fallback and callers

`copilot_sdk/backend/transfer_router.py` defines `_demo_patterns_for_mapping()` at lines 722-755. It manufactures `TransferPattern` values from the category mapping, chooses the first target action, creates constant centroid deltas, and labels metadata provenance as `demo` with a synthetic `source_fingerprint_id`.

The only caller is `_patterns_for_execute()` at line 639 in the same module. Repository-wide search found no direct caller in tests, apps, scripts, or `copilot_sdk/demo/preseed.py`. Step 13 therefore has no direct private-helper dependency to update.

`_patterns_for_execute()` first checks an explicit or scorer-attached `SharedPatternRegistry`. When matching registered patterns exist it returns them with provenance `transfer`; otherwise it calls the synthetic helper and returns provenance `demo`. A graph store containing governed transfer patterns is not consulted unless a registry was separately attached.

### Transfer requests and execution

`TransferExecuteRequest` and `CrossCopilotTransferRequest` currently contain only source/target domains (plus `dry_run` on the legacy request). Neither carries source artifact IDs. The legacy endpoint checks only the source conservation label and returns a normal response rather than an HTTP conflict. The self-transfer endpoint checks source and target labels, but it can use scorer attributes as fallback rather than requiring live graph evidence. Neither path evaluates `alpha * q * V` against `theta_min`.

Both endpoints call `_patterns_for_execute()` and therefore silently receive synthetic patterns when governed patterns are absent.

### Transfer checkpoint persistence

`_save_transfer_checkpoint(store, domain, scorer, metadata)` verifies `isinstance(store, GraphStore)`, validates a nonempty domain, and calls `save_centroids(domain, "transfer_event", centroids, metadata=metadata)`. It does not validate source artifacts and does not write a governance event. `_log_transfer_event()` invokes it for the target store and, when available, a separate source store.

The existing centroid checkpoint is read by transfer status projection, so the governed change must be additive: save the governance event and retain the centroid checkpoint for compatibility.

### Registry

`SharedPatternRegistry` is already graph-backed. `register(pattern)` writes `{"kind": "transfer_pattern", "pattern": ...}` under `transfer_pattern:{pattern_id}` in the registry domain, but it does not validate the artifact from which the pattern was derived.

### Exact GraphStore governance signatures

```python
def save_governance(self, domain: str, key: str, state: dict[str, Any]) -> None: ...
def get_governance(self, domain: str, key: str) -> dict[str, Any] | None: ...
def list_governance(self, domain: str) -> list[dict[str, Any]]: ...
```

The actual positional order is `(domain, key)`, so source validation must call `store.get_governance(source_domain, artifact_id)`.

## Section 2: Proposed Changes

### Change 1: remove synthetic fallback

Delete `_demo_patterns_for_mapping()` entirely. `_patterns_for_execute()` will use an explicit/scorer registry when present, or construct a read-only `SharedPatternRegistry` over the scorer's `GraphStore` and `source_domain`. It returns matching governed patterns with provenance `governed`, or `([], "governed")` when none exist.

Both transfer endpoints will reject an empty pattern list with HTTP 422 and the exact detail `No governed transfer patterns available. Register source artifacts first.` before dry-run projection or warm-start mutation.

### Change 2: explicit source artifact validation

Add required `source_artifact_ids: list[str]` fields to both transfer request models. Normalize and reject empty IDs. Before warm-start mutation, validate each ID against the shared graph with `get_governance(source_domain, artifact_id)`. Missing artifacts produce HTTP 422 with `Source artifact {id} not found in governance store`.

`_save_transfer_checkpoint()` will independently repeat this validation immediately before persistence. Early endpoint validation prevents mutating scorer state and only then discovering invalid provenance; checkpoint validation enforces the persistence boundary for direct/internal callers.

### Change 3: live conservation threshold revalidation

Add a graph-only helper that reads `get_conservation_state(domain)` immediately before execution. It extracts `verified_count` (falling back to `V`), `correct_count`, `q`, and `alpha`, then computes the threshold with the canonical `compute_theta_min(alpha, V)` helper. Recomputing the threshold prevents stale persisted projections from weakening the gate. The gate passes only when the status is `GREEN` and `alpha * q * V >= theta_min`.

Source or target failure raises HTTP 409 with exact detail `Conservation threshold not met for {domain}`. Missing/unreadable state fails closed through the same response. Both legacy and self-transfer endpoints use the same helper, eliminating scorer/static conservation fallbacks from the execution decision while leaving observational helper functions intact for backward-compatible status displays.

The normalized evidence returned by the helper is:

```python
{
    "verified_count": int,
    "correct_count": int,
    "q": float,
    "alpha": float,
    "theta_min": float,
    "status": str,
}
```

### Change 4: governed provenance persistence

Extend `_log_transfer_event()` and `_save_transfer_checkpoint()` to carry:

- `source_conservation_state`: `verified_count`, `correct_count`, `q`
- `target_conservation_state`: the same shape
- `source_artifact_ids`: normalized IDs
- `mapping_details`: a detached mapping dictionary
- `validation_timestamp`: UTC ISO-8601 text
- `transfer_provenance`: `governed`

`_save_transfer_checkpoint()` writes a governance record with `kind="transfer_checkpoint"` under a transfer-specific key, and retains the existing centroid checkpoint with the same enriched metadata. The legacy `provenance` response becomes `governed`; no `demo` or `synthetic` marker is produced.

The self-transfer endpoint will persist the same checkpoint after a successful warm start in addition to its existing `write_transfer_pattern()` edge.

### Change 5: registry validation

Extend the backward-compatible signature to:

```python
def register(
    self,
    pattern: TransferPattern,
    graph_store: GraphStore | None = None,
) -> TransferPattern:
```

When `graph_store` is supplied, derive the source artifact ID from `pattern.metadata["source_artifact_id"]` and source domain from `pattern.source_domain`/`source_copilot`. Missing metadata or a missing `get_governance(source_domain, source_artifact_id)` record raises `ValueError("Source artifact not registered")`. When omitted, registration retains current behavior for compatibility.

## Section 3: Test Plan

New file: `tests/test_transfer_governed_source.py`.

### Group A: removal of synthetic fallback

1. Legacy execute with no governed patterns returns HTTP 422.
2. Self transfer with no governed patterns returns HTTP 422.
3. `_demo_patterns_for_mapping` is absent.
4. `_patterns_for_execute()` returns an empty list when source governance has no transfer patterns.

### Group B: source artifact validation

5. Missing source artifact returns HTTP 422 with the exact ID.
6. All source artifacts present permits execution.
7. Two of three present still refuses the missing third.

### Group C: conservation revalidation

8. Source signal below threshold returns HTTP 409.
9. Target signal below threshold returns HTTP 409.
10. Both states above threshold permit execution.

### Group D: provenance persistence

11. Governance event includes source conservation evidence.
12. Governance event includes target conservation evidence.
13. Governance event includes source artifact IDs and mapping details.
14. Governance event has an ISO validation timestamp and `transfer_provenance="governed"`.

### Group E: registry

15. `register(..., graph_store=store)` accepts an existing source artifact.
16. It rejects a missing/unidentified artifact with the exact `ValueError`.
17. `register()` without the optional argument remains backward compatible.

Existing transfer-router and cross-copilot tests that exercised the synthetic fallback will be updated to register a real source artifact and graph-backed transfer pattern, supply its artifact ID, and persist live GREEN conservation evidence for both domains.

## Design Review Findings

- Removing `_demo_patterns_for_mapping()` has no direct external caller impact; only endpoint behavior and tests that implicitly relied on its fallback change.
- No Step 13 file imports or calls the helper. `copilot_sdk/demo/preseed.py` and `scripts/preseed_all_copilots.py` remain untouched.
- The exact governance method order is `(domain, key)`, contrary to the illustrative keyword order in the prompt; implementation will use the protocol signature.
- HTTP 422 is appropriate for missing patterns/artifacts because the request cannot be applied without registered source evidence. HTTP 409 is appropriate for a valid transfer whose current governed conservation reserve conflicts with execution.
- Existing label-only conservation helpers are insufficient for F-09. Execution must use graph state containing numeric `alpha`, `q`, `V`, and `theta_min`, while observational routes may retain their current projections.
- A required request field is intentional: accepting an empty artifact list would preserve untraceable transfers. Existing tests and callers must migrate to explicit governed IDs.
- Checkpoint persistence must remain additive. Removing `save_centroids()` would break transfer status lookup; the new governance event is added alongside it.
- Registry validation cannot infer a trustworthy source artifact from the new pattern's own ID. The optional validation path therefore requires `metadata.source_artifact_id` and fails closed if absent.
