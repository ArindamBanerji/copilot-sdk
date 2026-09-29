# C-GOV Design Document (Batch 27)

Generated: 2026-09-28
Model: sol/high
Baseline: 3,812 tests collected

## 1. Codebase State Summary

Current tag: `v0.9.61` on branch `main`, at commit `560447d`. There are no commits after the tag.

The worktree is not clean: 185 paths are changed or untracked (152 tracked modifications and 33 untracked paths), with no staged changes. Three target files already contain unrelated, uncommitted edits:

- `copilot_sdk/evolution/prompt_evolver.py`
- `copilot_sdk/scoring/scorer.py`
- `copilot_sdk/evolution/evolver.py`

`copilot_sdk/evolution/conservation_contract.py`: **EXISTS**. It already defines the conservation state types, state normalization, `ScorerBackedProvider`, and `CachedAsyncProvider`. It must be extended, not replaced.

`tests/evolution/`: **EXISTS**. It contains the current evolution test suite. `test_cross_loop_conservation.py` does not exist, so that name is available.

The integrity baseline repair is complete. The current root collection is 3,812 tests; the recorded post-repair run is 3,812 passed with zero failures.

## 2. Conflict Resolutions

### K1: COLD_START and BOOTSTRAP need operation-aware decisions

The current scorer deliberately allows verified L1 learning during `PRESEED`, `COLD_START`, and `BOOTSTRAP`. In `CompoundingScorer._conservation_pause()`, those states return no pause response, so centroid learning proceeds. `get_conservation_state()` also marks these early phases as passed. This is required to accumulate the evidence that can move the system out of cold start.

Automated L2 and L2b promotion must remain blocked in those states. `DefaultPromotionGate._is_conservation_safe()` currently admits only `GREEN`, `VERIFIED`, or `ACTIVE`, while `PromptVariantEvolver` delegates to that predicate. A context-free `bool` would therefore either block necessary verified learning or permit premature promotion.

The canonical contract will return a frozen, operation-aware decision:

```python
@dataclass(frozen=True)
class ConservationSafety:
    status: str
    available: bool
    learning_allowed: bool
    promotion_allowed: bool
    reason: str


def evaluate_conservation_safety(raw_state: object) -> ConservationSafety:
    ...
```

All loops use this one function. L1 and L1b consult `learning_allowed`; L2 and L2b consult `promotion_allowed`. This is one conservation law with explicit decisions for different mutation classes, rather than several private predicates.

### K2: Snapshot scope follows real transaction boundaries

There is no transaction containing both `CompoundingScorer.learn()` and prompt promotion. The actual call graph is:

```text
POST /learn
  -> scoring_router.learn()
    -> CompoundingScorer.learn()
       -> conservation read
       -> centroid update
       -> _refresh_dk_after_learn()
          -> reestimate_dk_if_due()
       -> optional _run_evolution()
    -> _persist_l5_learning()
       -> currently may call reestimate_dk_if_due() again

POST /check-promotion
  -> evolution_router.check_promotion()
    -> PromptVariantEvolver.check_for_promotion()
       -> provider read
       -> prompt status mutation when admitted
```

Prompt promotion is an independent request and cannot share the scorer's snapshot. GC-08 must test one immutable snapshot per actual mutation transaction:

1. The L1 learning transaction uses one pre-mutation decision for centroid and its internal DK refresh.
2. Direct `reestimate_dk_if_due()` is its own L1b transaction and captures one decision.
3. L2 scorer evolution is a post-learning promotion transaction and captures one post-write state. It must not reuse the pre-learning decision, because the new outcome may have changed conservation health.
4. Each L2b prompt-promotion check captures one provider state.
5. Trading promotion and global transfer each capture one state for their own transaction.

The duplicate DK re-estimation in `scoring_router._persist_l5_learning()` must be removed or changed to persistence-only behavior. `CompoundingScorer.learn()` already owns the learning-triggered DK mutation. Leaving the router call in place would allow two conservation observations and two DK mutations in one HTTP operation.

This revision intentionally does not claim that independent scorer and prompt requests share an object. They share the same public conservation contract.

### K3: Preserve and extend the existing contract module

`conservation_contract.py` already exports:

- `ConservationStatus`
- `ConservationState`
- `ConservationStateProvider`
- `normalize_conservation_state()`
- `ScorerBackedProvider`
- `CachedAsyncProvider`

The implementation must **MODIFY** this module. It must preserve the existing provider and normalization interfaces, add the frozen `ConservationSafety` result, and add `evaluate_conservation_safety()`. The evolution package exports must be extended through `copilot_sdk/evolution/__init__.py`.

### K4: Tag and staging strategy

The MAP target `v0.7.74-sdk` is stale. The current tag is `v0.9.61`; the next repository tag is `v0.9.62`.

`git add -A` is unsafe in the current worktree. The baseline repair and many unrelated edits are still uncommitted, including edits in `prompt_evolver.py`, `scorer.py`, and `evolver.py`. The preferred strategy is:

1. Commit or otherwise isolate the baseline repair and unrelated work first.
2. Apply C-GOV in a clean worktree based on that committed baseline.
3. Stage only the C-GOV files listed in section 10.
4. Run the full suite from a clean checkout of the proposed commit.
5. Create `v0.9.62` only after that clean-checkout validation.

If implementation must occur before cleanup, use hunk-level staging for every pre-edited file and do not tag. A tag created from a partial commit would not reproduce the validated 3,812-test worktree.

## 3. Conservation Contract Function

File: `copilot_sdk/evolution/conservation_contract.py` — modify existing.

Proposed public interface:

```python
@dataclass(frozen=True)
class ConservationSafety:
    status: str
    available: bool
    learning_allowed: bool
    promotion_allowed: bool
    reason: str


def evaluate_conservation_safety(raw_state: object) -> ConservationSafety:
    """Return the canonical C-17 safety decision for a state snapshot."""
```

Return type: frozen dataclass. If `raw_state` is already a `ConservationSafety`, return that same object. This supports identity-based verification that downstream mutations use one immutable decision.

Accepted states and decisions:

| Normalized state | Available | Verified learning | Automated promotion |
|---|---:|---:|---:|
| `GREEN`, `VERIFIED`, `ACTIVE` | True | True | True |
| `PRESEED`, `COLD_START`, `BOOTSTRAP` | True | True | False |
| `AMBER`, `RED`, `CALIBRATING` | True | False | False |
| `UNKNOWN`, `CONSERVATION_UNAVAILABLE` | False | False | False |
| Missing, empty, malformed, unsupported type | False | False | False |

Normalization rules:

- Accept a state string or a mapping with `status`, `state`, or `phase`, in that precedence order.
- Normalize recognized string values with `strip().upper()`.
- A recognized explicit state takes precedence over compatibility booleans. For example, `{"status": "RED", "overallSafe": True}` is unsafe.
- If no explicit state exists, `overallSafe is True` or `overall_safe is True` maps to the compatibility-safe state `GREEN`; false maps to `RED`.
- Unexpected property access, malformed mappings, empty strings, and unsupported values return an unavailable fail-closed result. The function is total for arbitrary input.
- Provider calls remain outside this pure function. Provider exceptions are converted to an `UNKNOWN` or `CONSERVATION_UNAVAILABLE` raw state at the transaction boundary and then evaluated by this function.

COLD_START/BOOTSTRAP handling: verified L1/L1b learning is allowed because it is the mechanism that creates sufficient evidence. Promotion is denied until a promotion-safe state is reached.

Current code to preserve:

- The `ConservationStateProvider` protocol and its callable/getter compatibility.
- `normalize_conservation_state()` keys and output shape.
- `ScorerBackedProvider` and `CachedAsyncProvider` behavior, including their exception-to-`UNKNOWN` conversion.
- Existing public imports from `copilot_sdk.evolution`.

`ConservationStatus` should be expanded, without removing existing members, so normalized providers can preserve `PRESEED`, `COLD_START`, `BOOTSTRAP`, `VERIFIED`, `ACTIVE`, and `CONSERVATION_UNAVAILABLE` rather than erasing them to `UNKNOWN`.

## 4. Gate Changes

File: `copilot_sdk/evolution/gate.py`

Current conservation check, at the end of `DefaultPromotionGate.evaluate()` before the variance check:

```python
if not self._is_conservation_safe(conservation_state):
    reasons.append("conservation_gate")
```

The private predicate currently contains independent parsing logic:

```python
def _is_conservation_safe(self, conservation_state: Any) -> bool:
    if conservation_state is None:
        return False
    if isinstance(conservation_state, str):
        return conservation_state.strip().upper() == "GREEN"
    if not isinstance(conservation_state, dict) or not conservation_state:
        return False
    for key in ("status", "state", "phase"):
        value = conservation_state.get(key)
        if value is None:
            continue
        if not isinstance(value, str):
            return False
        return value.strip().upper() in self._SAFE_PHASES
    if conservation_state.get("overallSafe") is True:
        return True
    if conservation_state.get("overall_safe") is True:
        return True
    return False
```

Proposed change: `evaluate()` calls `evaluate_conservation_safety(conservation_state).promotion_allowed`. Remove the duplicated parser. If `_is_conservation_safe()` must remain temporarily for source compatibility, make it a thin deprecated delegate to the public contract and ensure no production caller uses it. `PromptVariantEvolver` must stop calling the private method.

The `evaluate()` signature does not change. Existing callers may continue passing strings or mappings.

Preserved checks, in their current order and with their current thresholds:

1. Minimum shadow batches when batch metadata is present.
2. Sufficient sample data.
3. One-sided statistical significance.
4. Practical improvement threshold.
5. Accuracy floor.
6. Conservation admission, now delegated.
7. Variance ceiling.

## 5. Prompt Evolver Changes

File: `copilot_sdk/evolution/prompt_evolver.py`

Current logic in `_check_family_for_promotion()`, lines 211–308, resolves conservation before sample-count and improvement checks:

```python
conservation_state = self._resolve_conservation_state()
if not self._promotion_gate._is_conservation_safe(conservation_state):
    reason, code = self._conservation_rejection_reason(conservation_state)
    self._emit_lifecycle_event(...)
    self._notify_event_callback(...)
    return None
```

`_resolve_conservation_state()`, lines 310–324, treats an injected provider as authoritative; absence becomes `UNKNOWN`, and provider exceptions become `UNKNOWN` with a provider-error source.

Proposed change:

- Resolve the provider exactly once per `check_for_promotion()` transaction.
- Immediately pass the raw state to `evaluate_conservation_safety()`.
- Use the returned `promotion_allowed` field before sample-count and improvement logic.
- Pass the same frozen decision through the remaining promotion path; do not reread the provider.
- Keep the current lifecycle event and callback behavior.

RED behavior: emit the existing `conservation_gate_red` rejection and return `None` before prompt status mutation.

Missing/error behavior: emit the existing `conservation_gate_unavailable` rejection and return `None` before prompt status mutation.

GREEN behavior: sample sufficiency, improvement comparison, best-variant selection, lifecycle events, callbacks, return value, and `retired`/`active` status mutation remain unchanged.

## 6. Scorer Changes

File: `copilot_sdk/scoring/scorer.py`

Current `learn()` flow, lines 988–1331, is materially:

```text
load decision and actual action
detect judgment conflict
call _conservation_pause()
return a paused LearningResult when unsafe/unavailable
compute IKS
copy centroids
call self._scorer.update(...)                 # centroid mutation
write outcome and centroid
invalidate verified cache
persist receipt
call _refresh_dk_after_learn()
  -> reestimate_dk_if_due()                   # DK mutation
checkpoint and persist artifacts
optionally run reward/credit updates
every 20 learns, call _run_evolution()
  -> _evolution_conservation_state()          # second conservation read
  -> AgentEvolver.evolve(...)                 # possible L2 mutation
```

`reestimate_dk_if_due()` is public. It is called by `_refresh_dk_after_learn()`, `backend/scorer_proxy.py`, `migrate/verify_state.py`, tests, and dynamically by `backend/scoring_router.py`. It currently has no conservation guard.

Transaction boundaries and snapshot locations:

- **L1 learn transaction:** after the decision is loaded and validated, but before judgment-conflict state or any model/store mutation, call one internal `_capture_conservation_safety()` method. Store the frozen result in `conservation_safety: ConservationSafety`.
- **L1b within learn:** `_refresh_dk_after_learn()` receives that same object and calls an unguarded private implementation only when `learning_allowed` is true.
- **Direct L1b call:** public `reestimate_dk_if_due()` captures its own state once and returns without changing DK weights when `learning_allowed` is false. It delegates to `_reestimate_dk_if_due_unchecked()` when admitted.
- **L2 scorer evolution:** treat this as a distinct post-outcome promotion transaction. `_run_evolution()` captures one post-write safety decision and passes that same object to `AgentEvolver`. It uses `promotion_allowed`, through `DefaultPromotionGate`. It must not reuse the pre-outcome L1 decision or perform another read inside the gate.

Snapshot variable: `conservation_safety: ConservationSafety`.

Guarded mutations:

- Centroid update and its graph persistence: `learning_allowed`.
- DK-weight estimation and persistence: `learning_allowed`.
- Scorer/rule promotion: `promotion_allowed`.
- Ancillary receipt, checkpoint, reward, and credit writes occur only on an admitted learning path, preserving current ordering.

`reestimate_dk_if_due()` guard approach: **Option B**, a guarded public method plus `_reestimate_dk_if_due_unchecked(conservation_safety)` used only by an already-admitted learn transaction. This keeps external callers safe while avoiding a second provider/store read inside `learn()`.

The current cold-start special case in `_evolution_conservation_state()` returns `GREEN` when no verified decisions exist. That is fail-open for L2 promotion and must be removed. The method should return or derive the real early phase, which the public contract marks learning-allowed and promotion-denied.

`copilot_sdk/backend/scoring_router.py` also needs a surgical change: `_persist_l5_learning()` must not invoke a second DK re-estimation after `learn()`. It may persist/read the current weights, but mutation belongs to the scorer transaction.

## 7. AE Gate Changes

File: `copilot_sdk/ae/gate.py`

Current fail-open defaults are:

```python
def evaluate(..., conservation_state: str = "GREEN") -> PromotionDecision:
def check(..., conservation_state: str = "GREEN") -> PromotionDecision:
def should_promote(..., conservation_state: str = "GREEN") -> bool:
```

Active consumers: the class is exported from `copilot_sdk.ae`, and tests import it, but no active production caller was found.

Proposed fix: preserve the compatibility class, change each default to `None`, accept the existing raw state forms, and delegate promotion admission to `evaluate_conservation_safety(...).promotion_allowed`. An omitted or malformed state then blocks. Do not delete the class because it is a public package export.

## 8. Other Paths

### `copilot_sdk/evolution/evolver.py`

No provider read occurs here. `AgentEvolver.evolve()` receives `conservation_state`, generates/shadows a variant, and calls the promotion gate before changing rule status. It should accept a `ConservationSafety` object as an additional supported state form and pass it through unchanged. No other behavioral change is needed. The file already has unrelated uncommitted changes, so avoid editing it unless typing or pass-through support truly requires a hunk.

### `copilot_sdk/conservation/global_gate.py`

`check_transfer()` currently calls `snapshot()` and then calls `transfer_allowed()`, which takes another snapshot. This violates the one-snapshot rule for a transfer transaction. Add a pure helper that evaluates the supplied snapshot, make `check_transfer()` read once, and delegate aggregate admission to the public contract. Store-read failures already occur before the transfer write and must remain fail-closed.

### Custom evolvers in `apps/`

`apps/trading/backend/app/services/trading_evolver.py` is an active custom L2 path. It duplicates conservation parsing in `_conservation_green()`. `promote()` first calls `check_promotion()` and then rereads the provider before status mutation. Replace the parser with the public contract and allow `check_promotion()` to receive an already-captured decision so `promote()` reads once.

`apps/trading/backend/app/services/promotion.py` also contains a duplicate `_is_conservation_green()` helper, but it is a separate business-tier promotion service rather than one of the four compounding loops named by Batch 27. Catalog it for a follow-up consolidation unless call-chain review during implementation proves it mutates a scorer, DK, rule, or prompt asset covered by C-17.

No other app-local evolver found in the first-pass inventory should be changed without demonstrating that it performs one of those governed mutations.

## 9. GC Test Design (Revised)

All tests belong in `tests/evolution/test_cross_loop_conservation.py`, unless an existing behavior test is the clearer location for a compatibility assertion. Each test constructs fresh state and uses `profile="test"` for `InMemoryGraphStore`.

### GC-01: `test_red_blocks_centroid_mutation`

- Tests: RED blocks L1 before centroid or outcome mutation.
- Setup: fresh scorer and decision; force its conservation snapshot source to RED.
- Assertions: `LearningResult` is paused, centroid tensor is byte/value identical, verified/outcome counts do not change.
- CHANGED from original: no; it now also asserts the persistent outcome is unchanged.

### GC-02: `test_red_preserves_dk_weights`

- Tests: RED blocks both internal and directly invoked L1b mutation.
- Setup: fresh scorer with known DK weights and a due re-estimation condition.
- Assertions: weights and persisted DK state are identical after blocked learn and blocked direct refresh.
- CHANGED from original: yes; direct public `reestimate_dk_if_due()` is covered because it has external callers.

### GC-03: `test_promotion_gate_blocks_red`

- Tests: `DefaultPromotionGate.evaluate()` rejects otherwise promotable shadow results under RED.
- Setup: use results satisfying all non-conservation thresholds.
- Assertions: `promote` is false and `conservation_gate` is the rejection reason.
- CHANGED from original: use the actual `evaluate()` API; there is no `check()` method on this gate.

### GC-04: `test_prompt_promotion_all_paths`

- Tests: four independent subcases: RED blocks, GREEN promotes, missing blocks, provider exception blocks.
- Setup: a fresh evolver/family per subcase with sample and improvement thresholds met.
- Assertions: returned variant and status changes only on GREEN; RED emits `conservation_gate_red`; missing/exception emit `conservation_gate_unavailable`.
- CHANGED from original: acknowledges that prompt promotion is already gated and verifies delegation to the public contract.

### GC-05: `test_all_governed_loops_use_conservation_contract`

- Tests: common contract usage, not class uniqueness.
- Setup: AST/source inventory limited to the governed entry points: scorer L1/L1b, `DefaultPromotionGate`, prompt evolver, AE compatibility gate, global transfer, and Trading custom L2.
- Assertions: each imports/calls `evaluate_conservation_safety`; former private parser names are absent from production call sites.
- CHANGED from original: explicitly avoids asserting one gate class, because unrelated evidence and qualification gates remain valid.

### GC-06: `test_missing_state_fails_closed_all_levels`

- Tests: missing state across L1, direct L1b, L2, and L2b.
- Setup: expose `None` through each real boundary; for scorer, use the internal snapshot seam rather than inventing a public provider parameter.
- Assertions: no centroid, DK, rule, or prompt status mutation.
- CHANGED from original: bootstrap is not modeled as missing. A recognized `COLD_START` is learning-allowed but promotion-denied.

### GC-07: `test_provider_exception_fails_closed_all_levels`

- Tests: graph/provider/check failures at each boundary.
- Setup: graph conservation read raises for L1/L1b; prompt provider raises for L2b; malformed/raising mapping exercises the total contract and L2 gate.
- Assertions: typed blocked result or rejection, no governed mutation, and unavailable reason where exposed.
- CHANGED from original: pure contract evaluation is total; provider exceptions are handled at transaction boundaries.

### GC-08: `test_single_snapshot_per_transaction`

- Tests: immutable decisions and exactly one source read in each real transaction.
- Setup: counting providers/stores return alternating GREEN/RED values; instrument L1 learn, direct L1b, L2 scorer evolution, L2b prompt promotion, Trading promotion, and global transfer independently.
- Assertions: each transaction reads once; all mutations in that transaction use the same `ConservationSafety` identity; independent transactions may observe different states. Verify the router does not perform a second DK mutation.
- CHANGED from original: it does not require scorer learning and prompt promotion to share a snapshot because they have separate call stacks and requests. L2 scorer promotion uses a post-outcome snapshot, avoiding promotion from stale pre-outcome health.

The file should contain eight named test functions. GC-04 may use local subcases rather than pytest parameterization if the acceptance criterion requires exactly eight collected GC tests.

## 10. Git Strategy

Files intended for the C-GOV implementation, staged explicitly:

```text
copilot_sdk/evolution/conservation_contract.py
copilot_sdk/evolution/__init__.py
copilot_sdk/evolution/gate.py
copilot_sdk/evolution/prompt_evolver.py
copilot_sdk/scoring/scorer.py
copilot_sdk/backend/scoring_router.py
copilot_sdk/ae/gate.py
copilot_sdk/conservation/global_gate.py
apps/trading/backend/app/services/trading_evolver.py
tests/evolution/test_cross_loop_conservation.py
tests/test_conservation_contract.py
tests/test_conservation_gate_coverage.py
```

Only include a listed file if implementation actually changes it. Add focused regression tests to an existing file only when they verify that file's established public behavior.

Files with pre-existing uncommitted changes to avoid overwriting or whole-file staging:

```text
copilot_sdk/evolution/prompt_evolver.py
copilot_sdk/scoring/scorer.py
copilot_sdk/evolution/evolver.py
copilot_sdk/backend/scoring_router.py
```

Use a clean worktree after prerequisite changes are committed. If that is not possible, stage the dirty targets interactively by hunk and inspect `git diff --cached` before committing. Do not use `git add -A`.

Correct prospective tag: `v0.9.62`.

Proposed commit message:

```text
C-GOV (B27): unify cross-loop conservation decisions

- add an operation-aware immutable conservation decision
- route learning, DK refresh, and promotions through the contract
- use one conservation snapshot per mutation transaction
- add GC-01 through GC-08 regression coverage
```

Do not create the commit or tag until the current cumulative worktree is separated and a clean checkout of the exact staged commit passes all gates.

## 11. Implementation Prompt Corrections

The referenced file `cgov_prompt1_impl_v3.md` is not present in the repository. The corrections below apply to the implementation prompt supplied in the task.

1. **Assumption:** create `conservation_contract.py`.
   **Reality:** it exists and is imported by production code and tests.
   **Correction:** modify it, preserve providers and normalization, and export the new result/function.

2. **Assumption:** one boolean predicate can govern all loops.
   **Reality:** verified learning is allowed in cold start/bootstrap while automated promotion is denied.
   **Correction:** return an immutable operation-aware decision with `learning_allowed` and `promotion_allowed`.

3. **Assumption:** one transaction spans L1, L1b, L2, and L2b.
   **Reality:** prompt promotion is a separate endpoint; scorer evolution occurs post-outcome; direct DK refresh also has external callers.
   **Correction:** enforce one snapshot per actual mutation transaction and one contract across transactions.

4. **Assumption:** provider failure can be handled inside a side-effect-free state predicate.
   **Reality:** a pure predicate receives state and cannot invoke providers.
   **Correction:** boundary code converts provider/read failures to unavailable input; the total pure function evaluates it.

5. **Assumption:** the scorer snapshot can be taken at the first line of `learn()`.
   **Reality:** the decision must first be loaded and validated, while no governed or diagnostic state should mutate before admission.
   **Correction:** capture after input/decision validation and before conflict-state, centroid, outcome, DK, receipt, or artifact mutation.

6. **Assumption:** DK refresh occurs only inside `learn()`.
   **Reality:** it is public and called by the scorer proxy, migration verification, scoring router, and tests.
   **Correction:** guard the public method and create an admitted private implementation for `learn()`.

7. **Assumption:** scorer evolution should share the pre-learning snapshot.
   **Reality:** the newly written outcome may change conservation health.
   **Correction:** treat L2 as a post-outcome transaction with one fresh post-write snapshot.

8. **Assumption:** PromptVariantEvolver lacks conservation gating.
   **Reality:** it already resolves a provider and calls a private gate predicate before sample checks.
   **Correction:** replace only the private predicate call with the public contract; preserve events and success behavior.

9. **Assumption:** `DefaultPromotionGate` exposes `check()`.
   **Reality:** its API is `evaluate(shadow_results, conservation_state=None)`.
   **Correction:** write GC-03 against `evaluate()` and preserve its signature.

10. **Assumption:** AE gate's GREEN default can simply be removed from an active internal caller chain.
    **Reality:** it is a public export with tests but no production caller found.
    **Correction:** preserve the class and methods, default to `None`, and delegate fail-closed.

11. **Assumption:** only the initially listed SDK files need review.
    **Reality:** scoring router repeats DK mutation, global transfer rereads state, and Trading has an active custom L2 path with duplicate parsing and reads.
    **Correction:** include the surgical changes listed in sections 6 and 8.

12. **Assumption:** `evolver.py` needs a new provider read.
    **Reality:** it receives state from its caller and gates before rule mutation.
    **Correction:** keep it provider-free and change it only if required to pass through `ConservationSafety`.

13. **Assumption:** GC-05 should prove one gate class.
    **Reality:** evidence and qualification gates serve different purposes.
    **Correction:** prove one conservation contract across governed loops, without merging unrelated gates.

14. **Assumption:** GC-08 can assert one read across scorer and prompt loops.
    **Reality:** they are independent transactions.
    **Correction:** assert one read and one immutable decision within each transaction boundary.

15. **Assumption:** existing source-inspection tests will remain valid.
    **Reality:** `tests/test_conservation_gate_coverage.py` refers to private conservation implementation details.
    **Correction:** update it to assert public-contract delegation.

16. **Assumption:** exactly eight scenarios necessarily means eight collected pytest cases.
    **Reality:** parametrizing GC-04 creates additional collected cases.
    **Correction:** use eight named test functions and local independent subcases for GC-04 if an exact eight-test gate is required.

17. **Assumption:** the baseline tag is `v0.7.74-sdk`.
    **Reality:** the repository is at `v0.9.61`.
    **Correction:** target `v0.9.62` after clean-checkout validation.

18. **Assumption:** `git add -A` is safe.
    **Reality:** 185 worktree paths are changed or untracked, including target files.
    **Correction:** isolate prerequisite work, stage only explicit files/hunks, inspect the index, and avoid tagging a partial commit.
