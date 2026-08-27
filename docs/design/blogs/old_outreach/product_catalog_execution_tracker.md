# CI Product Catalog — Gap-Closure Execution Tracker

**Owner:** Arindam / product · **Opened:** Aug 24, 2026 · **Status:** ACTIVE
**Purpose:** Turn the PM gap review of the product-suite feature catalog into a living, revisitable
plan. Each item has a stable ID and a Status you update in place. This is the master tracker — come
back here, flip Status, and log decisions at the bottom.

## How to use this tracker
- **Status values:** OPEN · WIP · DONE · DROPPED · BLOCKED. Update in place; don't delete rows (mark
  DROPPED with a reason so the history survives).
- **Priority:** P0 (do first / blocks buyer or roadmap use) · P1 (high value) · P2 (polish).
- Log every material change in the **Decision & Change Log** at the bottom, dated.
- When a Codex scan returns, record the outcome against the scan ID and open/close the items it feeds.

## Related artifacts (in /mnt/user-data/outputs unless noted)
- `ci_product_suite_feature_catalog_v7.md` — **CURRENT** catalog (§0–§13). All dollar figures explicitly qualified (per-copilot value lines = modeled; $604K = illustrative demo). (v6 and earlier preserved.)
- `ci_boundaries_note_for_review.md` — “What We Don’t Claim” boundaries, held out of the catalog pending review
- `ci_product_suite_feature_catalog.md` — v1 clean feature/value list (preserved)
- `feature_briefing_v3.md` — reconciled status briefing (metrics/MAP version)
- `codex_prompts_catalog_gap_scans.md` — read-only Codex scans A/B/C (done) + **D** (roadmap verification)
- `ci_engineering_gaps.md` — **engineering gaps register (SCAN-D-verified)** — 16 code-verified gaps with evidence, dependencies, and closure conditions; separate from the product catalog. (Renamed from ci_engineering_roadmap.md; phasing removed.)

## Current source documents (Aug 24, 2026 — use these versions)
cga_arxiv_short **v10_2** · innovation_note **v28** · math_synopsis **v20** · ci_blog **v18** ·
graph_native_reasoning_hero **v23** · jm_paper_draft **v10** · MAP **v5.228 (+v5.229 addendum)** ·
PDs: SOC v5.11 · S2P v1.4 · DataOps v1.9 · Purchasing v1.4 · Trading v1.1-corrected.

## Code roots (from the inventory scan — reuse for all Codex scans)
GAE `…\claude_projects\graph-attention-engine-v50` · copilot-sdk `…\claude_projects\copilot-sdk` ·
SOC `…\claude_projects\gen-ai-roi-demo-v4-v50` · Trading/Purchasing/DataOps `…\copilot-sdk\apps\<name>` ·
S2P `…\claude_projects\s2p-copilot`.

---

## Science grounding (so "boundaries" items stay accurate)

Current claim status per **math_synopsis v20 / innovation_note v28 / cga v10.2**. Do not let any
catalog value line re-violate these.

| Claim | Status | Use in catalog |
|---|---|---|
| Conservation law α·q·V ≥ θ_min, deployed ×5 | VALIDATED | Lead differentiator |
| σ⊥μ two-engine separation | VALIDATED (proved) | Platform differentiator |
| **AE-DECISION** — runtime evolution under 20% adversarial poisoning: non-recovery 57%→14% (−42.5pp, 3/3), drift −60%, recovery 1 decision | **VALIDATED** | **Surface — answers "what stops bad teaching"** |
| **SA-ABSTAIN** — per-decision abstention: 100% OOD detection, <5% FP | **VALIDATED (safety)** | Surface as safety primitive (not an accuracy claim) |
| Self-computation (G,Φ,C): convergence PROVED, calibration VALIDATED, precondition CHARACTERIZED | VALIDATED (scoped) | Surface Level-1 self-computation |
| σ per-factor (noise fingerprint / trust-trap / signal-confidence inversion) | DIAGNOSTIC only | Keep as fingerprint; **never a scoring-weight or lift claim** |
| DiagonalKernel "+13pp over L2" | RETRACTED | Do not cite lift |
| Re-convergence γ>1 "recovery accelerates" (production) | RETRACTED / under re-test | Do not cite as shipped |
| K19 +28pp cross-deployment content transfer | RETRACTED / not reproduced | Transfer = warm-start acceleration only |
| RL-in-scorer (η allocation) | DEFINITIVELY CLOSED-NEGATIVE (4 exp, 6+ strategies) | Frame learning as **governed RL/evolution sidecar**; judgment core is authoritative (G1) |

---

## Workstream 1 — PLATFORM CAPABILITIES (the moat; currently weakest)
*The reason this is a platform, not five tools. Make cross-domain transfer, the one graph, the one
conservation law, and the provenance backbone first-class.*

| ID | P | Status | Item | Why it matters | Action |
|---|---|---|---|---|---|
| PLAT-1 | P0 | DONE | Add a **"Platform Capabilities"** section | Platform > sum of copilots is the CDO/CISO buying reason | ✅ §0 (section) |
| PLAT-2 | P0 | DONE | Cross-copilot signals + shared-graph discoveries (e.g. $604K cross-domain finding) as a capability | The transfer story is buried in 2 SDK rows | ✅ §0.2 |
| PLAT-3 | P0 | DONE | "**One conservation law governs every loop**" as a platform guarantee | Appears 5× per-copilot; the platform-wide safety proof has no home | ✅ §0.3 |
| PLAT-4 | P0 | DONE | **Provenance/substantiation backbone** as one section (evidence tiers, no-sample-in-headline, claim registry, day-zero honesty, frozen twin) | The product's credibility mechanism, scattered across evidence-gate/claim-gate/governance | ✅ §0.4 |
| PLAT-5 | P1 | DONE | **IKS as switching-cost/moat** (retention + CFO argument) | Listed as a per-copilot metric, never as the asset-you'd-lose | ✅ §0.6 |
| PLAT-6 | P1 | DONE | **Knowledge graph as a product surface** (ontology, queryable cross-domain graph, provenance/retention) | Described as plumbing; the compounding asset is invisible | ✅ §0.1 |
| PLAT-7 | P1 | DONE | **Adversarial robustness + governed sidecar** as a differentiator (AE-DECISION, SA-ABSTAIN, G1 boundary, RL-in-scorer closed) | Validated in v20; answers the #1 buyer fear of learning-from-humans | ✅ §0.5 |

## Workstream 2 — ENTERPRISE & TRUST READINESS (procurement blocks here)
*Table stakes for enterprise AI in 2026. Much of the machinery may already exist (domain-scoping,
pair-authorization, state-persistence, outbox) but is unframed. Scan B confirms real vs absent.*

| ID | P | Status | Item | Why it matters | Action |
|---|---|---|---|---|---|
| ENT-1 | P0 | WIP | Identity & access — **SOC has SAML + JWT + admin-role RBAC** (real); NOT suite-wide. Build gap: uniform caller auth + shared permission model across SDK/Trading/Purchasing/DataOps/S2P | Procurement gate | ✅ Documented in §9; build gap flagged |
| ENT-2 | P0 | WIP | Multi-tenancy & isolation — **data isolation PRESENT** (domain-scoped graph, prefixed IDs, pair auth — strongest capability); **full tenant identity/lifecycle/policy ABSENT** | Transfer/warm-start implies multi-deployment | ✅ Documented in §9; tenancy is the build gap |
| ENT-3 | P0 | WIP | Deployment model — **packaging + setup/migration + backup/restore/rollback PRESENT**; no unified Docker/compose/VPS bundle yet | Buyers ask "how do we run it" | ✅ Documented in §9; bundle is the gap |
| ENT-4 | P0 | OPEN | Security & data governance — **weakest area.** Encryption soft (`sslmode=disable`, no at-rest/field, no app TLS); secrets env-only (no Vault/KMS); PII governance partial (deletion/archival yes, no classification/retention/RTBF) | Security review gate | ✅ Documented in §9; **real build gap — prioritize encryption hardening** |
| ENT-5 | P1 | WIP | Compliance posture — **tamper-evident audit chains (SOC+S2P) + S2P compliance module (UFLPA/CSDDD/Scope-3) PRESENT**; platform-level SOC2/ISO + EU AI Act (Art-50 / Art-12-14) still to frame | Regulated-buyer gate | ✅ Audit surfaced in §9; platform compliance to frame |
| ENT-6 | P1 | WIP | Non-functional — **benchmark + latency helpers + `cached_static` hot-path + health/metrics PRESENT**; no uniform p95/tracing dashboards. **Inbound rate-limiting / quotas ABSENT** (build item) | "How fast/big/reliable" + protection from abuse | ✅ Documented in §9; rate-limiting is a build gap |

## Workstream 3 — ADOPTION PATH (where enterprise AI dies)
| ID | P | Status | Item | Why it matters | Action |
|---|---|---|---|---|---|
| ADOPT-1 | P0 | OPEN | **Cold-start / time-to-value** as a coherent capability (archetypes + bootstrap + day-zero + predict-weeks-to-competence) | #1 adoption blocker; genuine under-sold differentiator | New section |
| ADOPT-2 | P1 | OPEN | Human-in-the-loop workflow surface (review queue, feedback UX, bulk labeling, disagreement capture) | The learning loop depends on it; only referral/override exist under the hood | Frame HITL |
| ADOPT-3 | P1 | OPEN | Notification/delivery layer (email/Slack/Teams/PagerDuty) — **CONFIRMED gap (Scan A):** outbound is only exports (audit/centroid/optimizer JSON-CSV) + Trading Alpaca order-write; no push layer | Copilots detect but don't push; enterprise expects delivery | Needs build — scope a delivery/notification service |
| ADOPT-4 | P1 | OPEN | Conversational / "ask the copilot" NL surface | For a product called "copilot," no unified ask-surface (only NL-evidence fragments) | Decide build vs frame existing |
| ADOPT-5 | P2 | OPEN | Customer reporting/analytics (exec dashboards, scheduled reports, BI export) | The ongoing value narrative the buyer shows their boss | Extend weekly-report/ROI |

## Workstream 4 — BUYER-FACING FRAMING (make it usable in a sales/roadmap conversation)
| ID | P | Status | Item | Why it matters | Action |
|---|---|---|---|---|---|
| BUYER-1 | P0 | DONE | **Personas** — map features to SOC analyst vs CISO, trader vs risk lead, kitchen mgr vs owner, data engineer vs CDO | Every value line is generic today | ✅ §11.1 |
| BUYER-2 | P0 | DONE | **Jobs-to-be-done / one workflow per copilot** (day-in-the-life chain) | Buyers buy workflows, not atomic features | ✅ §11.2 |
| BUYER-3 | P1 | DONE | Table-stakes vs differentiator marking | "Import CSV" and "conservation law" sit at equal weight | ✅ §12.1/12.2 |
| BUYER-4 | P1 | WIP | Maturity signal — **demo axis done** (§10 product/demo/dev). GA/beta/production tagging per feature still to add | "Shipped in code" ≠ battle-tested | Add GA/beta tags |
| BUYER-5 | P0 | DONE | **Split product vs demo** — Scan C: PRODUCT ~753 / DEMO 29 / DEV ~268. 29 demo items isolated (the `*_beats` routers + beat/proof panels + demo scripts) | Inflated surface eroded technical trust | ✅ Added catalog §10; demo layer named & separated |

## Workstream 5 — COMPLETENESS / CODE GAPS (your bar was "complete")
| ID | P | Status | Item | Why it matters | Action |
|---|---|---|---|---|---|
| COMP-1 | P1 | DONE | Connector catalog — Scan A found **31** connectors (catalog showed ~7). Recovered: SOC threat-intel suite (Sentinel/NVD/MITRE/GreyNoise/Pulsedive), S2P SEC/FDA supplier intel, shared Snowflake/dbt/Airflow, FRED, Toast | Completeness + technical-buyer question | ✅ Added §8 Connectors to catalog |
| COMP-2 | P1 | DONE | Granularity — Scan C enumerated all **28 Purchasing routers** (with endpoints) + the **DI feature set** (data-valuation, acquisition-advisor, combination-discovery, intelligence-map, source-profiler, query-service, enrichment, trust-gateway all BUILT; prompt-integrator/perturbation PARTIAL) | Named shipped features were hidden | ✅ Enumerated **and folded into catalog §5/§6 (v5)** |
| COMP-3 | P1 | DONE | **Factor lineage** captured — 37 factors mapped (graph/connector/decision-history). Key finding: computations real but mostly **fixture-backed** pending per-deployment live wiring | First question a technical buyer asks | ✅ Added factor-source note to §8 |
| COMP-4 | P1 | OPEN | Unified API / CLI / extensibility story (GAE CLI, Trading 13-cmd CLI, S2P CLI, scaffold generator "build your own copilot", factor-proposer) | A developer-platform play, entirely unframed | New "extensibility" entry |
| COMP-5 | P2 | DONE | Status drift resolved — SOC campaign detection, SOC-TWIN, SOC-FRONTIER, framework-router, shared-frontend-TSX all **BUILT** (not partial/spec); S2P CLI confirmed **ABSENT**; Trading execution gate **enforced** (default off) | Accuracy | ✅ Catalog tags corrected |
| COMP-6 | P2 | OPEN | Robustness-to-bad-teaching absent from catalog (now VALIDATED — see PLAT-7) | Differentiator + buyer fear | Covered by PLAT-7 |

## Workstream 6 — HONEST BOUNDARIES & GTM (companions)
| ID | P | Status | Item | Why it matters | Action |
|---|---|---|---|---|---|
| BND-1 | P0 | DONE | **"What we don't claim" / known-limitations** companion (γ>1, DK+13pp, +28pp transfer, RL-in-scorer) | Technical evaluators will ask; honesty is a maturity signal | ✅ §13 (v4) |
| BND-2 | P1 | OPEN | Packaging / editions / OSS boundary (GAE+Trading+SDK primitives = Apache-2.0; rest closed — MAP D1) | Core product-line decision, absent | Add editions/licensing frame |
| BND-3 | P1 | OPEN | Trust/quality evidence surface (10,536 tests, 0 failures, adversarially tested) as a **buyer trust asset** | Correctly stripped as metadata — but belongs on a buyer-facing trust page | Add trust page |
| BND-4 | P2 | OPEN | Roadmap view ("what's coming") | Half of what a roadmap session needs | Derive from MAP forward plan |

---

## Top 5 — do these before the catalog goes anywhere
1. **PLAT-1..4 + PLAT-7** — Platform Capabilities section (transfer, one graph, one conservation law, provenance backbone, adversarial robustness). *The moat, currently weakest.*
2. **ENT-1..4** — Enterprise & Trust section. *Clears procurement; machinery partly exists.*
3. **BUYER-5 + BUYER-4** — Split product vs demo instrumentation; add maturity tags. *Protects credibility.*
4. **BUYER-1 + BUYER-2** — Personas + one JTBD workflow per copilot. *Makes it usable in a buyer conversation.*
5. **COMP-1..3 (+COMP-2)** — Fix Purchasing/DI granularity; add missing connectors; factor lineage.

---

## Codex scan backlog (read-only; prompts in `codex_prompts_catalog_gap_scans.md`)

| Scan | Status | Closes | Scope |
|---|---|---|---|
| **SCAN-A** | ✅ DONE | COMP-1 ✅, COMP-3 ✅, ADOPT-3 (confirmed gap) | Connectors + external data sources + per-factor lineage + notification/delivery surfaces |
| **SCAN-B** | ✅ DONE | ENT-1..6 documented | Enterprise-readiness surface: authn, RBAC, tenancy/isolation, secrets/encryption, deployment/backup, health/observability, rate-limit, API/OpenAPI, perf instrumentation |
| **SCAN-C** | ✅ DONE | BUYER-5 ✅, COMP-2 ✅, COMP-5 ✅, BUYER-4 (partial) | Product-vs-demo-vs-devtool classification + Purchasing/DI granularity + status-drift reconciliation |
| **SCAN-D** | ✅ DONE | roadmap verified & COMMITTED | Verified 16 gaps vs code: 4 CONFIRMED-OPEN, 12 PARTIAL, 0 already-done; corrected ENG-WIRE (OpenMeteo IS wired) → `ci_engineering_gaps.md`

Each scan writes its report in-repo to `copilot-sdk\docs\catalog_scans\` (read-only otherwise):
SCAN-A → `scan_a_connectors_factors_delivery.md` · SCAN-B → `scan_b_enterprise_readiness.md` · SCAN-C → `scan_c_product_vs_demo.md`. Pull those files back here when they're generated and I'll execute the Top-5 against them.

---

## Decision & Change Log
- **2026-08-24** — Tracker opened from PM gap review of `ci_product_suite_feature_catalog_v2_complete.md`. 6 workstreams, 33 items. Grounded science section in math_synopsis v20 / innovation_note v28 / cga v10.2. Reframed COMP-6→PLAT-7 (adversarial robustness is VALIDATED, not missing — surface it). RL framing set to "governed sidecar; RL-in-scorer closed." 3 Codex scans (A/B/C) authored and marked PROMPT-READY.
- **2026-08-24** — SCAN-A returned. Folded into catalog as new **§8 Connectors, Data Sources & Delivery**. Findings: (1) 31 connectors vs ~7 shown — recovered SOC threat-intel suite (Sentinel/NVD/MITRE/GreyNoise/Pulsedive), S2P SEC/openFDA supplier intel, shared Snowflake/dbt/Airflow; (2) factors mostly fixture-backed pending live wiring (honest-state note added); (3) delivery gap confirmed — exports + Alpaca order-write only, no push layer (ADOPT-3 stays OPEN as build). COMP-1, COMP-3 → DONE. Two items handed to SCAN-C: weather=MockWeather (OpenMeteo not wired), and Trading Alpaca live order-write vs "observation-only" claim.
- **2026-08-24** — SCAN-B returned (PRESENT=3, PARTIAL=11, ABSENT=1). Wrote catalog **§9 Enterprise & Trust Posture** (honest: foundations / identity / hardening). Present: data isolation (strongest), tamper-evident audit (SOC+S2P), backup-migration-rollback, health/observability. Partial: auth/RBAC/SSO (SOC-only), secrets (env-only), encryption (`sslmode=disable`), PII gov, deployment bundle, API governance, perf. Absent: inbound rate-limiting. ENT-1/2/3/5/6 → WIP (documented, build gaps flagged); ENT-4 → OPEN (encryption hardening prioritized). Real build gaps for eng roadmap: suite-wide auth + tenant policy, inbound rate-limiting, encryption at-rest/TLS.
- **2026-08-24** — SCAN-C returned (PRODUCT=753, DEMO=29, DEV=268). Added catalog **§10 Product vs Demo Instrumentation**; corrected 5 inline tags now proven BUILT (campaign detection, frozen-twin, no-precedent, framework-router, shared-frontend-TSX). **Resolved flags:** Trading execution gate IS enforced (`TRADING_EXECUTION_ENABLED=false` default) — Trading safety gap DROPPED; S2P CLI confirmed ABSENT. BUYER-5, COMP-2, COMP-5 → DONE; BUYER-4 → WIP (demo axis done, GA/beta pending). **All three scans (A/B/C) now complete.** Remaining Top-5: PLAT-1..7 (platform section), ENT build gaps, BUYER-1/2/3 (personas, JTBD, differentiator marking).
- **2026-08-24** — Wrote catalog **§0 Platform Capabilities** (moat, placed first): 0.1 one shared graph (PLAT-6), 0.2 cross-domain transfer as warm-start acceleration — not +28pp (PLAT-2), 0.3 one conservation law across every loop + as transfer mechanism (PLAT-3), 0.4 provenance/substantiation backbone + σ⊥μ diagnostic (PLAT-4), 0.5 robust-to-bad-teaching governed sidecar with AE-DECISION 57→14 + SA-ABSTAIN + RL-in-scorer-closed (PLAT-7), 0.6 IKS/switching-cost moat (PLAT-5). PLAT-1..7 → DONE. Next: BUYER-1/2 (personas + JTBD), then BUYER-3 (differentiator marking).
- **2026-08-24** — Wrote catalog **§11 Personas & Jobs-to-be-Done**: 11.1 personas (operator vs economic buyer per copilot + CFO/CIO platform buyer + technical-evaluator role), 11.2 one end-to-end JTBD workflow per copilot, each step mapped to a shipped feature from §0–§10. BUYER-1, BUYER-2 → DONE. Remaining Top-5: BUYER-3 (differentiator vs table-stakes marking) — final response.
- **2026-08-24** — Wrote catalog **§12 Differentiators vs Table-Stakes**: legend (◆/●), 12.1 the 17 defensible moats (each with why-hard-to-copy + location; retracted claims explicitly excluded), 12.2 grouped table-stakes with "parity, not persuasion" notes, 12.3 rule-of-thumb for the room. BUYER-3 → DONE. **TOP-5 COMPLETE:** (1) Platform Capabilities §0 ✅ (2) Enterprise & Trust §9 ✅ documented (3) product/demo split §10 ✅ (4) personas + JTBD §11 ✅ (5) connectors/granularity/lineage ✅. Catalog now spans §0–§12. Remaining tracker items are engineering build-gaps (ENT-1..6, ADOPT), catalog polish (BUYER-4 GA/beta tags), and GTM companions (BND-1..4) — not blockers for using the catalog.
- **2026-08-24** — Catalog snapshotted to **v3** (`ci_product_suite_feature_catalog_v3.md`) at the Top-5-complete milestone (§0–§12). Versioning convention set: future catalog edits produce v4, v5, … (filename bump per update). v3 is now the working file.
- **2026-08-24** — Per direction, engineering build gaps are kept OUT of the product catalog and pulled into a dedicated **`ci_engineering_roadmap.md`** (the roadmap track): ENT/ADOPT/doc-hygiene/data-wiring as roadmap items (severity, effort, implementation site, dependencies, acceptance criteria) in a proposed 4-phase sequence. Catalog keeps §9 as *posture* only. Authored **SCAN-D** (read-only) to verify the roadmap against code before it's committed (DRAFT → COMMITTED). Note: an LLM-judge pass can calibrate priority after SCAN-D, but code verification comes first.
- **2026-08-24** — SCAN-D returned; folded into `ci_engineering_gaps.md` (then named roadmap) and verified. All 16 gaps confirmed real (4 CONFIRMED-OPEN, 12 PARTIAL, none already-done). **Correction:** ENG-WIRE reframed — live OpenMeteo path IS wired (`scoring/verification/weather.py`); real gap is shared factor provenance/freshness, not a missing connector. Dependency finding: nearly all items depend on ENG-AUTH (keystone) and ENG-ENC is independent → both lead P1. Exact file:line evidence + per-gap acceptance criteria now in the roadmap. Optional next: LLM-judge severity/priority calibration.
- **2026-08-24** — Lane A decided & started. Order: v4 §13 boundaries (BND-1) → v5 COMP-2 granularity fold-in → v6 §14 trust+OSS-boundary (BND-3/BND-2 factual) → v7 §15 extensibility (COMP-4). Deferred: BUYER-4 maturity tags (no clean GA/beta evidence), BND-4 roadmap view (catalog will POINT to the separate eng roadmap, not duplicate it). **v4 shipped:** catalog §13 “What We Don’t Claim” — 6 withdrawn claims (DK-lift, γ>1 production, +28pp, RL-in-scorer, zero-falsification, ε_firm) + 4 honest current-state boundaries. BND-1 → DONE. Versioning: catalog now v4; next catalog edit → v5.
- **2026-08-24** — Per direction: (1) v4 §13 “What We Don’t Claim” **pulled from the catalog** into `ci_boundaries_note_for_review.md` for cross-session review (v5 built from v3 so it’s not in the catalog line). (2) **v5 shipped** — folded COMP-2 granularity into the catalog: §5 Purchasing expanded to 13 feature-router clusters (from the 28 Scan-C routers), §6 DataOps gained the DI capability cluster (valuation/acquisition-advisor/combination-discovery/intelligence-map/source-profiler/query-service BUILT; prompt-integrator/perturbation PARTIAL). (3) Added **§13 Competitive Landscape** from ci_blog_v18 — three generations, where-each-stops (Palantir/SAP Joule/Zycus Merlin/Celonis/Monte Carlo/LangChain/Snowflake-Databricks/agent-memory), four questions, read/route/reshape, four memory types + signal-confidence inversion. Honesty held: no 36.89pp, no DK-lift, no γ>1, no simulated trajectory; used only the validated 42.5pp adversarial + σ-diagnostic. BND-1 → in review-note (not catalog). Versioning: catalog now v5; next catalog edit → v6.
- **2026-08-24** — **v6: comprehensive review pass.** (1) Verified features/functionality for every component (§1–§7) against code ground truth; corrected 6 stale status tags: Trading **execution gate = ENFORCED** (was “in progress”), Trading broker router (cred-gated), Purchasing **QBO = built** (live OAuth + mock fallback), DataOps SAP/Celonis = **live+cache fallback** (was “in progress”), S2P **CLI = not built** (HTTP routes only, per Scan C). (2) Per direction, converted the §0 moat prose (0.1–0.6) from paragraphs to bullets — each now lead bullets + a **Moat:** bullet + evidence line. §8–§11 prose left as honest-state description (not moat filler). Versioning: catalog now v6; next edit → v7.
- **2026-08-24** — **v7:** ensured every dollar figure is honestly qualified. Per-copilot value lines (§5/§6/§7) already carried **modeled**; tagged the one remaining figure — the §0.2 **$604K** cross-domain finding — as an **illustrative demo figure** (it’s a scenario result, not a modeled projection). SOC’s ~30 min/alert left untagged because it’s **measured** (SANS). Catalog now v7.
- **2026-08-24** — Renamed the engineering doc **roadmap → `ci_engineering_gaps.md`** and tightened it to a precise gaps register: removed the phased-plan sequencing (roadmap), kept the code-verified gaps (evidence/file:line), the dependency graph, and per-gap closure conditions. No frivolous framing or effort guesses. Old `ci_engineering_roadmap.md` deleted.
- _(add next entry here)_
