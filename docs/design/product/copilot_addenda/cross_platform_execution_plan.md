# CI Platform — Cross-Copilot Execution Plan

Date: 2026-08-17  
Source: all five copilot gap analyses and structural diagnoses, product definitions, demo scenarios, final addenda, and MAP v5.228.

## Executive summary

The five copilots have strong scoring, graph, conservation, and UI foundations. The central remaining risk is proof infrastructure: evidence-gated claims, immutable baselines, measured learning, and authority transitions.

This plan contains 21 Codex-sized work items, approximately 105–135 senior engineer-days. With two engineers working in parallel, the critical path is about 8–10 weeks; with one engineer, about 22–27 weeks. All rollout work is additive and feature-flagged.

## Consolidated findings

| Copilot | GAP or P0 PARTIAL | Status | Missing contract | MAP |
|---|---|---|---|---|
| Trading | F16 Claim/Evidence Gate | GAP | No claim gate, endpoint, or measured-versus-synthetic enforcement | MAP-missing |
| Trading | SAFE-2 observation-only | FAIL/GAP | Directive output and broker-order write path remain reachable | MAP-missing |
| Trading | F11 Promotion; F12 AgentEvolver | PARTIAL | Full promotion/measurement/rollback and observation-only contract | P83/P84 adjacent |
| Trading | SAFE-4 legal gate | GAP/NEAR | No enforceable counselor/legal escalation gate | MAP-missing |
| S2P | F23 Decision-Change Proposal | GAP | No canonical persisted proposal, evidence links, proposed action, or audit receipt | MAP-missing |
| S2P | F24 Ledger; F25 Promotion | P0 PARTIAL | No reconciled ledger or seven-stage persisted authority state | MAP-missing |
| S2P | F26 Frozen Twin | GAP | No immutable restart-safe snapshot, replay, or drift report | MAP-missing |
| S2P | F5 Auto-Approve | P0 PARTIAL | Shadow/gate exists; measured conservation expansion unproven | Adjacent |
| SOC | F16 Control Room; F17 Ladder | P0 PARTIAL | No unified learning view or persisted category authority ladder | MAP-missing |
| SOC | F18 Frozen Twin; F19 No-Precedent | GAP | No immutable baseline or explicit novelty surface | MAP-missing |
| SOC | F20/F21/F22 | PARTIAL | Counterfactual, readiness, and transfer measurement incomplete | MAP-missing |
| SOC | C-COUPLE veto | PARTIAL/UNPROVEN | Universal RED referral/auto-approve veto not proven | MAP-missing |
| Purchasing | F23 Proof Ledger; F27 Frozen Twin | PARTIAL | No two-curve attribution ledger or immutable replay baseline | MAP-missing |
| Purchasing | F24/F26/F28/F29 | GAP | Handoff, discovery gate, belief capture, and quote audit absent | MAP-missing |
| Purchasing | F25 competence; §7.3 loop | GAP/PARTIAL | No convergence meter; later comparable improvement unmeasured | MAP-missing |
| DataOps | IKS/forecast/digest; DI-4 | GAP | Productized attribution and prompt integration absent | MAP-missing |
| DataOps | H1/H3/H4/H5/H6 | P0 PARTIAL | Later-score liveness, quality routing, value provenance, gateway incomplete | MAP-missing |
| DataOps | DI abstain/gateway, FDR/holdout, value ledger | GAP/PARTIAL | No enforced safe boundary, holdout gate, or economic evidence chain | MAP-missing |

Cross-cutting: reward/reward_raw remain in production and tests; S2P live code is 5×5×8 while older docs say 5×5×7; SOC has an honest but incomplete travel_match to privileged_identity_context migration; conservation gates evolution but not every decision path; Frozen Twin is absent as shared infrastructure.

## Demo impact

The discovered demo file is demo_scenarios_and_usecases_v2_7.md, although its internal header contains older version drift.

| Beat | Current blocker | Required work |
|---|---|---|
| SOC cold mirror/control room | Learning disabled by default; F16 partial; F18 absent | SH-02, SOC-01, truth-controlled enablement |
| SOC promotion/rejection | Authority ladder and RED veto unproven | SH-03, SOC-02 |
| SOC no-precedent | No explicit surface | SOC-03 |
| S2P S14 Not a Script | Graph/situation exists; canonical evidence object absent | S2P-01, S2P-02 |
| S2P autopilot expands with proof | Ledger and seven-stage promotion absent | S2P-02, S2P-03 |
| Purchasing handoff | Ledger, handoff pack, competence meter absent | PUR-01 |
| Trading observation-only claim | SAFE-2 fails; F16 gap | P0-01, SH-01, TRD-01 |
| DataOps earned trust | Abstain, holdout, and value provenance absent | DI-01 |

The demo document’s high demo-ready count is an inventory claim, not acceptance evidence, until endpoint, test, and honesty-gate proof exists.

## Shared build decisions

| Capability | Owner | Shared interface | Domain work |
|---|---|---|---|
| Evidence/Claim Gate | SDK | claim, evidence, provenance, tier, allow/deny/refer receipt | thresholds, legal text, UI |
| Frozen Twin | SDK | immutable manifest, hash, restart-safe storage, replay, diff | scorer adapter and baseline panel |
| Promotion/autonomy | SDK mechanics | seven stages, conservation gate, audit, rollback | labels, authority policy, category keys |
| Counterfactual | SDK | deterministic per-factor perturbation and flip explanation | factor metadata, endpoint, card |
| Day-0 readiness | SDK protocol + ci-platform | coverage, freshness, identity, graph, connector, safe-mode report | domain mappings |
| Ledger events | SDK schema | verified decision, outcome, learning, drift, provenance | KPI/economic attribution |
| reward migration | SDK policy | canonical outcome receipt plus bounded dual-read | per-router migration |
| Tensor changes | Per domain | no universal numeric defaults | atomic geometry/threshold review |

## Dependency DAG

P0-01 → SH-01 → TRD-01  
SH-06 → all domain outcome adapters  
SH-02 → S2P-03, SOC-01, PUR-01, DI-01  
SH-03 → S2P-03, SOC-02, Trading promotion, DataOps promotion  
SH-04 → S2P counterfactual, SOC-03, Purchasing counterfactual  
SH-05 → S2P readiness, SOC readiness, DataOps onboarding  
S2P-01 → S2P-02 → S2P-03  
SOC-01 → SOC-02 → SOC demo wiring  
All domain wiring → DEMO-01 → PILOT-01 → PILOT-02

## Implementation phases and work-item cards

### Phase 0 — Safety and cleanup (1–2 weeks)

#### P0-01 Trading SAFE-2 quarantine
- Repo: copilot-sdk/apps/trading/backend, frontend, E2E. Dependencies: none. Effort: 4–6 days.
- Acceptance: negative scan/tests prove no directive output or broker write; broker endpoint is disabled or explicitly non-production; full Trading E2E proves no action submission.
- Reference: Trading SAFE-2, F9/F15. Notes: read corrected Trading gap analysis, PD safety sections, broker routers, templates, and E2E first.

#### P0-02 Evidence-tier and canonical-number inventory
- Repo: copilot-sdk/docs/design plus app repos. Dependencies: none. Effort: 2–3 days.
- Acceptance: every claim has provenance/honesty tier; SOC 71.7/78.9/IKS/frozen-ROI and other claims are labeled; synthetic results cannot be called measured.
- Reference: all gap analyses and SOC canonical-number audit. Notes: inventory only; no production value edits.

#### P0-03 Stale-contract cleanup
- Repo: copilot-sdk, s2p-copilot, SOC repo. Dependencies: none. Effort: 3–5 days.
- Acceptance: 5×5×7 references are historical or corrected; SOC legacy fixtures remain quarantined; compatibility tests protect keys and geometry.
- Reference: S2P tensor and SOC factor-0 findings. Notes: no fixture re-authoring or centroid change.

#### P0-04 Demo truth controls
- Repo: demo configs and E2E fixtures. Dependencies: P0-02. Effort: 2–4 days.
- Acceptance: explicit SOC learning/S2P shadow/Trading observation flags; synthetic labels; preflight checks for ports, queues, graph, connectors, and seed state.
- Reference: demo v2.7 preconditions. Notes: guards only.

### Phase 1 — Shared infrastructure (2–3 weeks)

#### SH-01 Evidence/Claim Gate
- Repo: copilot-sdk/copilot_sdk/substantiation and adapters. Dependencies: P0-01, P0-02. Effort: 6–8 days.
- Acceptance: typed allow/deny/refer gate with audit receipt; synthetic/modelled values cannot receive measured label; Trading endpoint and denial tests.
- Reference: Trading F16, DataOps gates, Purchasing legal/proof. Notes: generic mechanics only; domain thresholds in adapters.

#### SH-02 Frozen Twin
- Repo: copilot-sdk/copilot_sdk plus domain persistence. Dependencies: P0-02, SH-06. Effort: 8–12 days.
- Acceptance: snapshot contains centroids, DK weights, conservation, IKS reference, schema, hash; immutable/restart-safe; replay/drift tests.
- Reference: S2P F26, SOC F18, Purchasing F27, DataOps DI-TWIN. Notes: never rewrite the IKS anchor.

#### SH-03 Promotion/autonomy state machine
- Repo: copilot-sdk evolution/conservation/audit. Dependencies: SH-01, SH-06. Effort: 7–10 days.
- Acceptance: persisted Discover, Shadow, Promote, Measure, Keep/Rollback, Transfer; RED blocks authority increase; rollback and domain-independent tests.
- Reference: S2P F25, SOC F17/C-COUPLE, Trading F11/F12, DataOps. Notes: existing evolvers are adapters, not proof.

#### SH-04 Counterfactual inspector
- Repo: copilot-sdk scoring/self-computation. Dependencies: SH-01. Effort: 5–7 days.
- Acceptance: deterministic per-factor smallest tested flip or explicit no-flip; original/target/direction/action/margin/decision ID; no state mutation.
- Reference: S2P F27, SOC F20, Purchasing. Notes: advisory output only.

#### SH-05 Day-0 readiness
- Repo: SDK readiness plus ci-platform qualification. Dependencies: SH-01. Effort: 6–9 days.
- Acceptance: coverage/freshness/identity/graph/connector/safe-mode report; truthful unavailable AGE state; S2P/SOC endpoints and degraded tests.
- Reference: S2P F29, SOC F21, DataOps onboarding. Notes: distinguish AGE-required from SQLite-degraded behavior.

#### SH-06 Verified-outcome protocol
- Repo: SDK and all domain routers/models. Dependencies: none. Effort: 4–6 days.
- Acceptance: canonical receipt with decision, actor, evidence, verification, learning effect; reward/reward_raw bounded dual-read telemetry; exactly-once learning/ledger tests.
- Reference: cross-copilot reward findings and §7.3. Notes: schema/provenance only, not RL behavior.

### Phase 2 — Per-copilot moat features (3–5 weeks)

#### S2P-01 Decision-Change Proposal F23
- Repo: s2p-copilot/backend and SDK S2P frontend. Dependencies: SH-01, SH-06. Effort: 6–8 days.
- Acceptance: persisted proposal links decision, evidence, reason, proposed action, confidence, actor/state; endpoint/UI receipt; create/retrieve/reject tests.
- Reference: S2P F23 GAP. Notes: factor proposals are not this canonical object.

#### S2P-02 Compounding Ledger F24
- Repo: S2P backend/frontend. Dependencies: S2P-01, SH-06. Effort: 7–10 days.
- Acceptance: one reconciled view for decisions, outcomes, IKS, conservation, finance, provenance; unavailable data is not fabricated; totals reconcile.
- Reference: S2P F24 partial. Notes: use stable event IDs.

#### S2P-03 Promotion F25 and Frozen Twin F26
- Repo: S2P backend/frontend/E2E. Dependencies: SH-02, SH-03, S2P-01, S2P-02. Effort: 9–12 days.
- Acceptance: persisted seven-stage transitions; immutable restart-safe drift report; S2/S9/S14/S16 E2E remains shadow-safe.
- Reference: S2P F25/F26. Notes: auto-approve remains shadow-only pending measured gates.

#### SOC-01 Control Room and measured ledger
- Repo: SOC backend/frontend. Dependencies: SH-01, SH-02, SH-06. Effort: 8–12 days.
- Acceptance: mounted panel for centroid/DK/conservation/evolution/counts/frozen comparison; measured/synthetic labels; empty/disabled/active tests.
- Reference: SOC F16/F18/F22. Notes: no centroid edits or global learning enablement.

#### SOC-02 Earned Autonomy Ladder and veto
- Repo: SOC backend/frontend. Dependencies: SH-03, SOC-01. Effort: 6–9 days.
- Acceptance: persisted five-rung category state; RED forces referral/hold; transition, rollback, and UI tests.
- Reference: SOC F17/C-COUPLE. Notes: read triage, situation, referral, conservation, §22.6–§22.7.

#### SOC-03 No-Precedent and What-If
- Repo: SOC self-computation/frontend. Dependencies: SH-04, SOC-01. Effort: 6–9 days.
- Acceptance: novelty surface with knowns/unknowns/pause; real factor flip thresholds; no-flip and actual-flip tests.
- Reference: SOC F19/F20. Notes: novelty evidence, advisory output.

#### PUR-01 Purchasing proof/discovery/legal/handoff
- Repo: Purchasing backend/frontend/E2E. Dependencies: SH-01, SH-02, SH-05, SH-06. Effort: 10–15 days.
- Acceptance: F23 ledger, F24 handoff, F26 gate, F27 Twin, F28 belief capture schemas/endpoints/UI; F29 source-derived quote audit; §7.3/legal/evidence tests.
- Reference: Purchasing F23–F29. Notes: no fabricated savings.

#### TRD-01 Trading Claim Gate and promotion safety
- Repo: Trading backend/frontend/E2E. Dependencies: P0-01, SH-01, SH-03, SH-06. Effort: 7–10 days.
- Acceptance: claim response has tier/provenance/measured status; promotion stays observation-only; SAFE-2 and claim negatives pass.
- Reference: Trading F16, SAFE-2, F11/F12. Notes: gate claims, not trading directives.

#### DI-01 DataOps evidence/abstain/holdout/value provenance
- Repo: DataOps backend/frontend/E2E and ci-platform. Dependencies: SH-01, SH-05, SH-06. Effort: 10–15 days.
- Acceptance: abstain/read-only gateway; FDR/30-day holdout; Value Provenance Ledger linking source, transformation, decision, economics.
- Reference: DataOps DI-4, DI-ABSTAIN, DI-GATEWAY, holdout, value ledger, H5/H6. Notes: trust metadata is not authorization.

### Phase 3 — Demo readiness (1–2 weeks)

#### DEMO-01 Hero-beat harness
- Repo: copilot-sdk/e2e and app fixtures. Dependencies: P0-04, S2P-03, SOC-02, SOC-03, TRD-01, PUR-01, DI-01. Effort: 6–9 days.
- Acceptance: preflight ports/queues/graph/seed/flags/evidence; E2E S2P S14, SOC promotion/no-precedent, Purchasing handoff, Trading claim gate, DataOps abstain; failed preconditions stop visibly.
- Reference: demo v2.7. Notes: scenarios are acceptance stories, not proof.

#### DEMO-02 Loop closure and C-COUPLE
- Repo: shared and domain tests. Dependencies: SH-03, SH-06, S2P-02, SOC-02, PUR-01, DI-01. Effort: 5–8 days.
- Acceptance: one outcome receipt, one learning event, and later score or explicit not-measurable result; RED blocks authority increase; restart reconciliation.
- Reference: Purchasing §7.3, DataOps H1/H3, SOC C-COUPLE, S2P ledger. Notes: do not reuse original score as later score.

### Phase 4 — Pilot readiness (2–4 weeks)

#### PILOT-01 Day-0, frozen baseline, AGE qualification
- Repo: ci-platform, domain backends, SDK. Dependencies: SH-02, SH-05, DEMO-01. Effort: 7–10 days.
- Acceptance: signed readiness and immutable baseline before learning; AGE-required versus SQLite-degraded explicit; restart/hash/backup/connector/PII/identity checks.
- Reference: Day-0, ci-platform, Frozen Twin findings. Notes: Preview proxy remains separate.

#### PILOT-02 Measured transfer and competence
- Repo: SDK and domain measurement adapters. Dependencies: PILOT-01, DEMO-02, SH-02. Effort: 8–12 days.
- Acceptance: frozen/live curves with observations, outcomes, denominators, intervals; SOC F22 and Purchasing/DataOps competence metrics measured; Claim Gate promotes synthetic only after holdout criteria.
- Reference: SOC F22, Purchasing F25, DataOps acceleration/holdout, Trading F16. Notes: retain synthetic history as synthetic.

## Critical path and risk

Longest chain: P0-01 → SH-01 → SH-03 → S2P-01 → S2P-02 → S2P-03 → DEMO-01 → PILOT-01 → PILOT-02. High estimate is 64–78 engineer-days. SH-02, SH-04, SH-05, and SH-06 can run in parallel.

Risks and mitigations:

- Frozen Twin incompatibility: versioned manifests, shape/hash validation, restart tests.
- IKS anchor rewrite: immutable path and write-denial test.
- Generic policy overreach: shared mechanics only; domain policy injected.
- UI-only claims gate: enforce at service boundary with negative tests.
- Reward migration loss: additive field and bounded dual-read window.
- AGE unavailability: readiness blocks affected graph claims.
- Demo overstatement: preflight requires endpoint/E2E receipts.
- SOC geometry regression: atomic tensor migration plus confidence/IKS/action checks.
- Sparse cells: mark low evidence and require pilot evidence.

## MAP reconciliation

Add these items to MAP v5.228:

| MAP item | Closes | Work |
|---|---|---|
| XPLAT-01 Evidence/Claim Gate | Trading F16 and honesty | SH-01, TRD-01 |
| XPLAT-02 Frozen Twin | S2P F26, SOC F18, Purchasing F27, DataOps DI-TWIN | SH-02 |
| XPLAT-03 Promotion/Autonomy | S2P F25, SOC F17, Trading F11/F12, DataOps | SH-03, S2P-03, SOC-02 |
| XPLAT-04 Counterfactual | S2P F27, SOC F20, Purchasing | SH-04, SOC-03 |
| XPLAT-05 Day-0 | S2P F29, SOC F21, DataOps | SH-05, PILOT-01 |
| XPLAT-06 Verified Outcome | §7.3 and reward compatibility | SH-06, DEMO-02 |
| XPLAT-07 Proof Ledger | S2P F24, Purchasing F23, DataOps value, SOC F16 | S2P-02, SOC-01, PUR-01, DI-01 |
| TRD-01/02 | SAFE-2 and SAFE-4 | P0-01, TRD-01 |
| S2P-V14-00..07 | F23–F29 | S2P-01, S2P-02, S2P-03, SH-02, SH-04, SH-05, PILOT-02 |
| SOC-V59-00/01 | F16–F22 and C-COUPLE | SOC-01, SOC-02, SOC-03, DEMO-02, PILOT-02 |
| PUR-V14-00 | F23–F29 and legal | PUR-01 |
| DI-V19-00 | DI gates, holdout, value ledger | DI-01 |

## Priority queue

Demo-blocking: P0-01, P0-04, SH-01, SH-02, SH-03, S2P-01, SOC-01, SOC-02, TRD-01, DEMO-01.

Pilot-blocking: SH-05, SH-06, S2P-02, S2P-03, PUR-01, DI-01, DEMO-02, PILOT-01.

Near-term hardening: SH-04, SOC-03, Trading SAFE-4, S2P confidence panel, Purchasing competence/belief capture, DataOps trust/connectors.

Roadmap: PILOT-02, SOC transfer measurement, Purchasing quote audit, DataOps acquisition/valuation extensions.

## Execution rule

No work item closes because a class, route, or static panel exists. Closure requires the endpoint or state transition, backend coverage, and UI/E2E evidence where user-facing. Synthetic, modeled, unavailable, and fallback-graph results remain visibly labeled.

