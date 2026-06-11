# C9 Theta-Min / DK Read Diagnostic

## Executive verdict

- READY_FOR_FIXER: YES
- ROADMAP_CLARIFICATION_NEEDED: NO

C9 is blocked by two concrete AGE boundary bugs plus one SDK/S2P metric-source bug. The observed `theta_min = inf` is not mathematically legitimate for the live graph data now in AGE. It is caused by conservation metrics counting the wrong domain when the scorer's AGE-backed graph store has no `domain` attribute. Raw AGE and direct store methods show verified/outcome-backed decisions exist for all non-SOC domains.

## Issue A - theta_min root cause

Classification: METRIC_SOURCE_BUG.

Evidence:

- `compute_conservation_metrics()` computes `counts = state_counts(state)` before using its explicit `domain` argument for category coverage. See `copilot_sdk/backend/conservation_utils.py` where counts are computed before `effective_domain` is used for `count_categories_with_data`.
- `state_counts()` calls `store_domain(store, getattr(state, "domain", ""))`; the live AGE adapter/scorer has no `domain` attribute, so count methods are called with an empty domain.
- Raw AGE has outcome-backed data:
  - trading: 280 outcome-backed decisions, 1 category.
  - purchasing: 223 outcome-backed decisions, 1 category.
  - dataops: 211 outcome-backed decisions, 1 category.
  - s2p: 210 outcome-backed decisions, 1 category.
- Direct `AGEGraphStore` methods also return nonzero counts:
  - trading: `count_verified=280`, `count_correct=280`, `count_verified_decisions=280`, `count_categories_with_n=1`.
  - purchasing: `223`, `223`, `223`, `1`.
  - dataops: `211`, `211`, `211`, `1`.
  - s2p: `210`, `210`, `210`, `1`.
- With the plain AGE adapter/scorer, conservation metrics return `alpha=0.0`, `q=0.0`, `V=0`, `theta_min=Infinity` for trading, purchasing, dataops, and s2p.
- With a domain-bearing adapter wrapper, the same SDK metrics become finite:
  - trading: `alpha=1.0`, `q=1.0`, `V=280`, `theta_min=0.084`.
  - purchasing: `alpha=1.0`, `q=1.0`, `V=223`, `theta_min=0.1055`.
  - dataops: `alpha=1.0`, `q=1.0`, `V=211`, `theta_min=0.1115`.

Exact values causing inf: `verified_count=0` and `total_decisions=0` in `state_counts()`, despite raw AGE counts being nonzero. The fallback branch sets `theta_min = float("inf")` when `total_decisions <= 0 or verified_count <= 0`.

## Issue B - ConservationState AGE serialization

Classification: STORAGE_REPRESENTATION_NEEDED as a defensive boundary, but not the primary root cause for current live C9 data.

Current behavior:

- `AGEGraphStore._normalize_float()` and `_normalize_positive_float()` allow non-finite floats such as `inf`.
- `update_conservation_state()` serializes numeric fields directly into Cypher, including `theta_min: {state['theta_min']}`.
- When `theta_min` is `inf`, the Cypher becomes `theta_min: inf`; AGE treats `inf` as an identifier and fails with `could not find rte for inf` / `variable inf does not exist within scope of usage`.
- `get_conservation_state()` expects `theta_min` as a required numeric field.

Recommended representation:

- First fix the metric-source bug so current live data produces finite values.
- Add a narrow AGE serialization guard for non-finite conservation numeric values. If non-finite values remain semantically possible for zero-data domains, the storage representation should be explicit and reversible, for example storing a nullable numeric plus a status/sentinel metadata field, or rejecting/skipping non-finite L5ConservationState writes until Roadmap chooses a public representation.

Formula changes required: NO for the current C9 blocker. Existing formula can produce finite values once counts use the intended domain.

## Issue C - DKWeight weight_json read compatibility

Classification: DK_READ_COMPAT_FIX_NEEDED.

Current behavior:

- `update_dk_weights()` writes `weight_json` and Welford fields as compact JSON strings via `json.dumps(...)` and `self._S(...)`.
- `AGEClient._normalize_value()` parses JSON-encoded list/dict strings into Python objects. Its comment says every consumer gets clean types and no call-site `json.loads()` should be required.
- Raw AGEClient readback returns `weight_json` and all Welford JSON fields as already-decoded Python lists.
- `AGEGraphStore.get_dk_weights()` currently requires `weight_json` to be a `str` and raises `TypeError("L5DKWeight weight_json must be a JSON string")` when AGEClient returns a list.
- The same compatibility issue likely applies to `_decode_dk_welford_state()`, which currently calls `json.loads(raw_value)` for Welford fields.

Impact:

- Runtime writes succeeded: L5DKWeight rows exist for trading, purchasing, dataops, and s2p, and all six Welford fields are present.
- Readback through `get_dk_weights()` fails for all four non-SOC domains.
- This affects C9 proof/readback and likely P26 startup restore over AGE, because startup uses store read methods rather than raw AGE queries.

## Live AGE metric input matrix

| Domain | confirmed/outcome-backed decisions | distinct categories | count_categories_with_n | V direct | alpha via domain wrapper | q via domain wrapper | theta_min via domain wrapper | classification |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| trading | 280 | 1 | 1 | 280 | 1.0 | 1.0 | 0.084 | metric-source bug in scorer/store domain path |
| purchasing | 223 | 1 | 1 | 223 | 1.0 | 1.0 | 0.1055 | metric-source bug in scorer/store domain path |
| dataops | 211 | 1 | 1 | 211 | 1.0 | 1.0 | 0.1115 | metric-source bug in scorer/store domain path |
| s2p | 210 | 1 | 1 | 210 | 1.0 | 1.0 | 0.112 | metric-source bug in scorer/store domain path |

## Fix decision tree

- Metric source bug: fix conservation metric counting so the explicit `domain` argument is used for verified/correct/total counts, not only category coverage.
- Serialization bug: add an AGE boundary guard/representation for non-finite conservation numeric values. This is defensive and may be needed for true zero-data domains, but it is not the primary cause for current non-SOC live data.
- DK read compatibility bug: update AGE DK readback to accept both JSON strings and AGEClient-normalized Python lists for `weight_json` and Welford fields.
- Semantics unclear: no Roadmap clarification needed for the current live C9 blocker, because live data should be finite once counted under the correct domain.

## Roadmap questions

None required for the current C9 unblock. A future Roadmap decision may be useful for how to represent true infinite thresholds in persistent L5 state, but current non-SOC C9 should not require infinite theta values.

## Proposed next prompt

Combined narrow fixer:

1. `copilot-sdk/copilot_sdk/backend/conservation_utils.py`: make conservation count metrics honor the explicit `domain` passed to `compute_conservation_metrics()` for verified/correct/total counts.
2. `ci-platform/ci_platform/graph/age_graph_store.py`: make DK readback accept AGEClient-normalized list values as well as JSON strings for `weight_json` and Welford fields.
3. Optionally add a defensive finite/non-finite guard for AGE `L5ConservationState` serialization, without changing conservation formulas.
