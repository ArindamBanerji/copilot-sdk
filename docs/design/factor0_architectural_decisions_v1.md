# SOC Factor-0 Architectural Decisions v1

**Decision date:** 2026-08-15  
**Scope:** SOC factor-0 reconciliation  
**Status:** Architecture gate; implementation is intentionally not included in
this document.

## Ground truth

The live factor-0 identifier is `privileged_identity_context` at tensor index
0. The SOC configuration declares that order at
`gen-ai-roi-demo-v4-v50/backend/app/domains/soc/config.py:116-127`; the live
computer declares `PrivilegedIdentityContextFactor`, `name =
"privileged_identity_context"`, and `factor_index = 0` at
`.../domains/soc/factors.py:64-73`; and the SDK preset uses the same six-factor
order at `copilot-sdk/copilot_sdk/scoring/presets/soc.py:15-55`.

This is not a key-only rename. The live computer uses `user_risk_score`, title
heuristics, missing-MFA risk, and device-fingerprint mismatch
(`factors.py:95-156`), while the existing evaluation scenarios describe travel
and location semantics, including a “frequent traveler” scenario and
`travel_match` values (`backend/app/data/soc_eval_scenarios.json:7-48`).

## Decision 1 — Evaluation scenarios

### Choice: B — retain as explicitly versioned legacy travel fixtures; create a new identity-context set later

The existing 36 scenarios will not be blindly rekeyed. They remain historical
or legacy evaluation data whose factor-0 semantics are `travel_match_v1`.
They must be visibly marked with semantic provenance before being used by
tools, reports, or demos that might imply identity-context validation. A new
identity-context fixture set will be authored separately from the old travel
set.

### Rationale

Option C is rejected: changing only the key would make travel-derived values
appear to validate a different computation, violating H7 and the two-regime
honesty rule. The design review confirms that the values are structurally
bounded but semantically unsupported for the live computer
(`factor0_design_review.md:75-97`).

Option A is the correct eventual quality path, but it requires domain work and
evidence that is not available in the current repository. Option B preserves
the historical evidence without laundering it into a current claim. The
existing `provenance: "sample"` marker is not sufficiently specific because it
does not identify the retired factor semantics.

### Required consequences

* Do not rename the existing factor keys until the data is either re-authored
  or explicitly consumed through a legacy adapter.
* Add a semantic marker such as `semantic_version: "travel_match_v1"` and a
  clear historical status to the retained fixture set.
* Create a separate identity-context fixture set whose values are justified by
  user risk, title, MFA, and device-context evidence.
* Keep evaluation outputs from the legacy set out of customer-facing accuracy
  or ROI claims.

## Decision 2 — μ₀ factor-0 prior

### Choice: B — mark the current prior explicitly stale and defer re-derivation

The numeric factor-0 column remains unchanged for the moment, but it is not
to be described as an identity-context-calibrated prior. Its documentation
must identify it as a travel-derived or semantically unverified prior pending
V1 re-derivation.

### Rationale

Option A is required before claiming that the bootstrap represents the live
identity-context semantics, but the repository contains no provenance-tagged
re-derivation or evidence for the current numbers. The tensor is a hand-authored
literal at `config.py:153`; category comments still include “travel anomaly” at
`config.py:160` and “travel explains movement” at `config.py:188-189`.
`get_profile_centroids()` returns that literal rather than a validated artifact
(`config.py:663-673`), and the SDK contains a duplicate literal
(`scoring/presets/soc.py:84-125`). Numeric agreement across repositories is not
semantic validation.

Option C is rejected because changing comments to the new name would imply
identity-context validation without changing or evidencing the values. That is
the exact failure mode this reconciliation is intended to prevent.

### Required consequences

* Add an explicit stale/unverified marker to the prior’s provenance or release
  documentation; do not change values merely to make labels agree.
* Run V1 category/action analysis for all 24 factor-0 centroid entries.
* Re-derive the prior from identity-context rationale, or replace it with a
  documented identity-context artifact.
* Keep the SOC and SDK tensors numerically synchronized only after the new
  rationale is approved.
* Do not use the current prior to support customer-facing claims.

## Decision 3 — Alias removal timing

### Choice: B — retain aliases with deprecation warnings and remove them after a bounded persisted-data audit

The aliases at `backend/app/routers/evaluation.py:22` and
`backend/app/routers/judgment.py:30` remain temporarily as input compatibility
paths. New writes and canonical responses use `privileged_identity_context`.
Legacy reads should emit structured deprecation telemetry and preserve the
legacy semantic marker.

The aliases are removed in a bounded follow-up once persisted records and
known clients have been audited. If the client population cannot be
inventoried, use a versioned endpoint or equivalent explicit compatibility
boundary rather than silently breaking old payloads.

### Rationale

Option A is unsafe because the inventory found serialized scenario data and an
API contract example using `travel_match`, and the design review identifies
persisted decisions, provenance, exports, and scorer state as possible
long-lived consumers (`factor0_design_review.md:131-147`). Option C is rejected
because it would preserve a retired factor identifier indefinitely and make
semantic cleanup unverifiable. A bounded window balances compatibility with a
real removal condition.

### Required consequences

* Canonicalize new input/output to `privileged_identity_context`.
* Accept the old key only at explicit compatibility boundaries.
* Log/count legacy reads, including source and semantic version where safe.
* Audit persisted data and downstream clients before removal.
* Remove the aliases only when the audit’s exit criteria are met and both
  canonical and legacy-path tests have passed.

## Implementation order

1. Add the legacy semantic marker and quarantine rules for the existing travel
   fixtures. Add tests proving they cannot be reported as identity-context
   validation.
2. Define and implement the identity-context fixture schema and author the new
   evaluation set. Validate its factor-0 values against the live computer.
3. Add the alias deprecation instrumentation and canonical-write behavior;
   retain legacy input during the audit window.
4. Run V1: inspect or re-derive every μ₀ factor-0 category/action entry and
   record evidence. Update the SOC and SDK bootstrap artifacts only from the
   approved result.
5. Update runtime tests, provenance dispatch, and active documentation. Verify
   factor order, tensor shape `(6,4,6)`, and factors 1–5 remain unchanged.
6. Audit persisted data and clients, then remove aliases if the bounded exit
   criteria are satisfied.
7. Reassess the orphan `TravelMatchFactor` only after zero runtime imports and
   instantiations are proven. Do not retain it as a sub-signal without a new
   contract, calibration, and composition design.

## What can ship now vs. what is deferred

### Safe to ship now

* The canonical name remains `privileged_identity_context` in live config,
  factor dispatch, and the SDK preset.
* Existing travel scenarios can remain available as explicitly labeled
  historical/legacy fixtures, provided they are excluded from current
  semantic-quality and customer-facing claims.
* Existing aliases can remain as monitored compatibility input paths.
* Product prose may use “privileged identity context” (with “access-pattern”
  only as prose, never as a code identifier).

### Deferred behind evidence gates

* Re-authoring or rekeying the 36 scenarios as identity-context data.
* Re-deriving or validating μ₀ factor-0 values (V1).
* Customer-facing accuracy/ROI claims based on this factor (V2).
* Alias removal.
* Deleting or re-scoping `TravelMatchFactor`.
* Broad historical-document cleanup and generated graph regeneration.

## Risk assessment

| Decision | If wrong | Detection/mitigation |
|---|---|---|
| D1 = B | Legacy fixtures may be overlooked and later used as current evidence; identity fixture work may be delayed. | Explicit semantic version, quarantine tests, fixture provenance review, and separate identity set. |
| D2 = B | A stale prior may influence runtime scoring while its quality is unknown. | Visible stale marker, V1 release gate, no customer claim, and re-derivation before semantic signoff. |
| D3 = B | Legacy clients may continue relying on the old key; deprecation may last too long. | Structured read telemetry, persisted-data audit, bounded removal deadline, and versioned boundary if clients are unknown. |

The principal forbidden outcome is a silent rename that makes old travel
semantics appear to be validated privileged-identity semantics. These decisions
keep that outcome structurally blocked while preserving a controlled path to
complete the reconciliation.
