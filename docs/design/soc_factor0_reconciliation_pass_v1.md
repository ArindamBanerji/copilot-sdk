# SOC Factor-0 Naming Reconciliation — Design / Change Pass v1

**For:** Codex coding session (implementation, not review)
**Repos:** `gen-ai-roi-demo` (SOC, branch `v5.0-dev`) primary; `copilot-sdk` (confirm-only); design doc `soc_copilot_design_v5_8.md` (Drive)
**Authored:** 2026-08-15 · verified against live `v5.0-dev` code
**Status:** Ready to execute. Every claim below cites `file:line` from the current repo.

---

## Summary (read first)

This is **not a migration** — the shipped `v5.0-dev` code has *already* moved factor 0 to `privileged_identity_context` (`PrivilegedIdentityContextFactor`, `factor_index=0`, computing identity/privilege risk from `user_risk_score` + title heuristics + inverted MFA/fingerprint). What remains is an **unfinished-migration cleanup**: `travel_match` still lingers in the eval-scenarios JSON (~12 keys), the provenance explainer key, two router alias-maps, an orphaned `TravelMatchFactor` class, one stale comment — and the entire v5.8 design doc. Change set C1–C6 finishes exactly that, and Codex must prove zero references before deleting anything.

Two things this pass deliberately does **not** paper over, because factor 0's *semantics* changed (travel-match → privileged-identity), not just its name:
- **μ₀[:,:,0] may encode the wrong prior** — if the factor-0 centroid column was hand-set when factor 0 meant "travel match," it now carries a travel prior under an identity label. **V1** requires confirming or re-deriving it.
- **The 71.7% / 78.9% product numbers may be stale** — valid only if measured on the privileged-identity factor 0. If the last validation run predates the semantic change, re-run before any customer-facing use. **V2**.

Neither blocks the naming reconciliation, which is safe to ship as-is.

**Three decisions needed (see §6 for detail) — please respond on each:**
1. `TravelMatchFactor` — delete (if orphaned) or retain as a re-scoped sub-signal?
2. μ₀ re-derivation + accuracy re-validation (V1/V2) — bundle into this pass, or run as a follow-up before the numbers go external?
3. Confirm the product addendum uses `privileged_identity_context` (prose: "privileged identity context / access-pattern") as factor 0.

---

## 0. Decision (canonical naming)

Factor 0 of the SOC `(6,4,6)` tensor is **`privileged_identity_context`**. This is the canonical code, config, tensor, and design-doc name.

- **`travel_match`** is **retired** as the factor-0 name. It survives only as residual drift (listed below) that this pass removes. It may remain, at most, as one *sub-signal contributing to* privileged-identity context — never as the factor-0 identifier.
- **`access_pattern`** (used in the Stryker/Handala blog) is a **prose synonym only** for narrative/marketing. It is **not** a code identifier and must not be introduced into code, config, or the tensor.

**Why this is a reconciliation, not a migration:** the core factor-0 computer has *already* migrated in code. `PrivilegedIdentityContextFactor` is live at `soc/backend/app/domains/soc/factors.py:63` with `factor_index = 0` (`factors.py:73`), and `SOC_FACTORS[0] = "privileged_identity_context"` in `config.py:121`. What remains is (a) residual `travel_match` drift in data/provenance/router-alias/legacy-class, and (b) the v5.8 **design doc**, which still documents `travel_match` at factor 0 throughout. This pass finishes the migration and re-aligns the doc.

---

## 1. Current state (verified in code)

**Already migrated (do NOT touch — confirm only):**
- `domains/soc/factors.py:63` — `class PrivilegedIdentityContextFactor(FactorComputer)`, `name = "privileged_identity_context"`, `factor_index = 0`. Computes identity/privilege risk from pre-resolved security context: `user_risk_score`, title heuristics (admin/root/privileged/svc → 0.9; exec/vp/director → 0.7; else 0.2), inverted `mfa_completed` (missing → 0.85), inverted `device_fingerprint_match` (mismatch → 0.80); no context → 0.5. **This computation is correct and stays as-is.**
- `domains/soc/config.py:121` — `SOC_FACTORS[0] = "privileged_identity_context"`; decay class `config.py:136`; centroid comment `config.py:372`; contract id `config.py:384`.
- `domains/soc/orchestrator.py:69` — dispatches `"privileged_identity_context"`.

**Residual `travel_match` drift (this pass removes):**

| # | Location | Current | Problem |
|---|---|---|---|
| R1 | `data/soc_eval_scenarios.json` (~12 keys: lines 8, 32, 44, 56, 79, 101, 123, 146, 169, 183, 193, 215) | factor-0 keyed as `"travel_match"` | Eval data name ≠ live factor name; only works via the R3 alias shim |
| R2 | `framework/provenance.py:218` | `"travel_match": _explain_privileged_identity_context` | Explainer keyed under the retired name but points to the new explainer |
| R3 | `routers/evaluation.py:22` **and** `routers/judgment.py:30` | `"privileged_identity_context": "travel_match"` | Alias shim that only exists to bridge the un-migrated R1 data |
| R4 | `domains/soc/factors.py:159` | `class TravelMatchFactor` (`name = "travel_match"`) | Appears orphaned (no `TravelMatchFactor()` instantiation found); confirm then remove |
| R5 | `services/simulation.py:118` | comment `# TravelMatchFactor → user_id, source_location` | Stale comment |

---

## 2. Change set

Execute in this order. R1+R3 are coupled — do them together or the eval path breaks.

**C1 — Rekey eval scenarios (R1).** In `data/soc_eval_scenarios.json`, rename every factor-0 key `"travel_match"` → `"privileged_identity_context"` (both the value entries and any factor-name lists, e.g. lines 44, 183). **Values unchanged** — only the key name. Count the occurrences before and after; they must match.

**C2 — Remove the alias shim (R3).** After C1, delete the `"privileged_identity_context": "travel_match"` entry in both `routers/evaluation.py:22` and `routers/judgment.py:30`. Verify no other code path depends on that alias (`grep` for the alias dict's usage). If a downstream reader still expects `"travel_match"`, cite it — do not silently leave the alias.

**C3 — Fix provenance key (R2).** In `framework/provenance.py:218`, change the key `"travel_match"` → `"privileged_identity_context"` (the value `_explain_privileged_identity_context` is already correct). Confirm no other dispatch still looks up `"travel_match"` in that table.

**C4 — Remove legacy class (R4).** Confirm `TravelMatchFactor` (`factors.py:159`) is never instantiated or imported anywhere in `gen-ai-roi-demo` (`grep -rn "TravelMatchFactor"`). **If and only if** there is zero instantiation, delete the class and the now-dead `travel_match` `PropertySpec`/`name` lines inside it. If any live reference exists, do **not** delete — instead cite it and stop for a decision (see §6).

**C5 — Stale comment (R5).** Update `services/simulation.py:118` to reference `privileged_identity_context`.

**C6 — Design doc (`soc_copilot_design_v5_8.md`).** This is a docs edit (separate docs/Codex session or manual). Replace `travel_match` → `privileged_identity_context` at factor 0 in: §5.1 factor summary table, §5.2/§5.x factor implementations, §14 `SOCDomainConfig` (`get_factor_computers()` index 0, `get_factor_decay_classes()`, `get_profile_centroids()` axis-2 factor-0 label + inline comments), and §4.4 canonical-numbers factor order. Add a changelog line: *"Factor 0 renamed travel_match → privileged_identity_context to match shipped v5.0-dev code (PrivilegedIdentityContextFactor). Semantics: identity/privilege/access-behavior risk, not travel matching."* Leave factors 1–5 untouched.

---

## 3. Validation obligations (do not skip — honesty gates)

These are the reason this is a *design* pass and not a blind find/replace. Factor 0's **semantics changed** (travel-match → privileged-identity risk), so name-alignment alone is not sufficient.

- **V1 — Bootstrap centroids μ₀[:,:,0].** Confirm the factor-0 column of `get_profile_centroids()` was re-derived for privileged-identity semantics, not carried over from travel-match priors. If the μ₀ values at index 0 were set when factor 0 meant "travel match," they now encode the wrong prior under a new label. Required output: a one-line-per-category statement of what μ₀[c, :, 0] represents under privileged-identity semantics, or a re-derivation. **No evidence → flag, do not assert it's fine.**
- **V2 — Two-regime accuracy numbers.** The realistic 50-seed product numbers (71.7% static / 78.9% @1000) and the centroidal-synthetic mechanism numbers (97.89%) must be confirmed to have been measured on the **privileged-identity** factor 0, not the legacy travel_match factor 0. If the last validation run predates the factor-0 semantic change, these numbers are stale and must be re-run before they appear in any customer-facing material. State which experiment run produced the current numbers and whether it used `PrivilegedIdentityContextFactor`.
- **V3 — Cross-repo convergence.** `copilot-sdk/copilot_sdk/scoring/presets/soc.py` already lists `privileged_identity_context` at factor 0. Confirm the two repos agree on factor-0 name **and** intended semantics; cite any divergence.

---

## 4. Guardrails (must NOT change)

- Tensor shape stays `(6, 4, 6)`. Factor 0 stays at **index 0** (permanent axis-2 binding).
- Factors 1–5 unchanged: `asset_criticality`, `threat_intel_enrichment`, `pattern_history`, `time_anomaly`, `device_trust`.
- Do **not** introduce `access_pattern` as a code identifier anywhere.
- Do **not** alter the `PrivilegedIdentityContextFactor.compute()` logic — this pass is naming/data/doc reconciliation, not a factor redesign.
- Actions unchanged: `escalate, investigate, suppress, monitor` (A=4); `refer_to_analyst` stays a referral VETO (R1–R7), not a tensor action.

---

## 5. Codex prompt (ready to paste — CLI mode)

> Scope: `gen-ai-roi-demo` repo, branch `v5.0-dev`, files: `backend/app/data/soc_eval_scenarios.json`, `backend/app/routers/evaluation.py`, `backend/app/routers/judgment.py`, `backend/app/framework/provenance.py`, `backend/app/domains/soc/factors.py`, `backend/app/services/simulation.py`.
> Task: reconcile factor-0 naming from the retired `travel_match` to the canonical `privileged_identity_context`, per the change set C1–C5 in this spec. Do the changes; do not redesign the factor.
> Rules: No evidence, no claim — cite `file:line` for every edit and for every wiring check. Before deleting `TravelMatchFactor`, prove zero instantiations/imports by citing the grep result; if any live reference exists, STOP and report it instead of deleting. R1 (JSON rekey) and C2 (alias removal) must land in the same change or the eval path breaks — verify the eval path resolves factor 0 by name after both. Run the repo-configured test runner (not a literal test command) and report factor/eval/provenance test results. Output: a per-file change list with before/after and the test summary.
> Do NOT touch `PrivilegedIdentityContextFactor.compute()`, the `(6,4,6)` shape, or factors 1–5.

The design-doc edit (C6) and the V1–V3 validations are **separate follow-ups**, not part of the Codex code prompt above.

---

## 6. Open decisions for you

1. **`TravelMatchFactor` — delete or retain as documented legacy?** Recommendation: delete if orphaned (cleanest). Retain only if you want travel-anomaly kept as an explicit sub-signal feeding privileged-identity context later — in which case it should be renamed and re-scoped, not left as a stray `travel_match` class.
2. **V1/V2 in-scope now or follow-up?** The naming reconciliation (C1–C6) is safe to ship immediately. The μ₀ re-derivation and accuracy re-validation (V1/V2) are heavier and gate only the *customer-facing numbers*. Recommendation: ship C1–C6 now; run V1/V2 before the product doc's ROI/accuracy figures go external. Flag if you want them bundled.
3. **Design-doc factor-0 in the product addendum:** the forthcoming SOC product addendum will use `privileged_identity_context` (prose: "privileged identity context / access-pattern") as factor 0, consistent with this pass. Confirm.
