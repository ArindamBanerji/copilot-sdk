# CI Engineering Gaps

**Compiled:** Aug 24, 2026 · **Status:** verified against code (SCAN-D). Separate from the product catalog.

> The product catalog describes what the product *is* and its honest posture (incl. Enterprise & Trust).
> **This document is the gaps** — what is missing in the code, with evidence.

**Sources:** Scan A (connectors / factor lineage / delivery), Scan B (enterprise surface), Scan C
(product-vs-demo + status); **all 16 gaps verified against current code by SCAN-D** — 4 CONFIRMED-OPEN,
12 PARTIAL-EXISTS (pieces exist, capability incomplete), none already-done.

**Legend.** Severity: 🔴 High (blocks an enterprise deal / security review) · 🟠 Med · 🟡 Low.
Status: OPEN (nothing exists) · PARTIAL (pieces exist, incomplete).

---

## 1. Gap summary

| Sev | Count | Gaps |
|---|---|---|
| 🔴 High | 3 | ENG-ENC encryption not hardened · ENG-AUTH no suite-wide auth/RBAC · ENG-TENANT no multi-tenancy |
| 🟠 Med | 7 | ENG-RATE inbound rate-limiting · ENG-DEPLOY deployment bundle · ENG-COMPLY platform compliance · ENG-DELIVER notifications · ENG-COLDSTART cold-start packaging · ENG-HITL review workflow · ENG-WIRE factor provenance/freshness |
| 🟡 Low | 6 | ENG-ASK conversational surface · ENG-REPORT reporting depth · ENG-S2PCLI S2P CLI · DOC-SOC-CAT SOC categories · DOC-TRD-TENSOR Trading tensor · DOC-S2P-TENSOR S2P tensor |

*CONFIRMED-OPEN: ENG-TENANT, ENG-RATE, ENG-S2PCLI, DOC-SOC-CAT, DOC-TRD-TENSOR, DOC-S2P-TENSOR. All others PARTIAL.*

## 2. Enterprise (procurement-gating)

| ID | Gap | Sev | Status | Evidence |
|---|---|---|---|---|
| ENG-ENC | **Encryption not hardened** — no app TLS, no at-rest/field encryption, `sslmode=disable` in shipped configs | 🔴 | PARTIAL | `sslmode=disable` in `demo.py:92`, `posterior_store.py:72`, `migrate_aura_to_age.py:21,447`; no at-rest/TLS impl |
| ENG-AUTH | **No suite-wide caller auth / RBAC** — real auth is SOC-only | 🔴 | PARTIAL | SOC `dependencies.py:require_auth`, `auth.py` (SAML), `jwt_utils.py`; no shared auth module in `copilot_sdk/backend` |
| ENG-TENANT | **No multi-tenancy** — domain isolation is real; no tenant identity, lifecycle, or tenant-scoped policy | 🔴 | OPEN | isolation present (`graph_client.py:20`, prefixed IDs, `graph/factory.py:105,221-242`); no request-scoped tenant |
| ENG-RATE | **No inbound rate-limiting / quotas** — only outbound connector pacing | 🟠 | OPEN | no inbound limiter in any app entrypoint; `sec_client.py:42,50` outbound only |
| ENG-DEPLOY | **No unified deployment bundle** — no Docker/compose; no API versioning or shared error envelope | 🟠 | PARTIAL | migration (`sqlite_to_age.py`, `reconcile_archive.py`), outbox `worker.py`, Trading `cli.py:761,782` backup/restore exist; no Dockerfile/compose |
| ENG-COMPLY | **No platform-level compliance posture** — no SOC2/ISO or EU AI Act mapping | 🟠 | PARTIAL | audit chains SOC `audit.py:114,394` + S2P `audit.py:153,305,407`; S2P `compliance_screener` exists; no platform control mapping |

## 3. Adoption

| ID | Gap | Sev | Status | Evidence |
|---|---|---|---|---|
| ENG-DELIVER | **No push/notification layer** — outbound is exports + Alpaca order-write only | 🟠 | PARTIAL | exports (`soc.py:3507`, audit exports) + Trading broker write `cli.py:833-843` (off by default `settings.py:15`); no notification sender |
| ENG-COLDSTART | **Cold-start not packaged** — pieces exist but scattered | 🟠 | PARTIAL | `gae/bootstrap.py:94`, `convergence.py:180,222`, `archetype_router.py:25`, `qualify_for_pilot.py` — no unified onboarding |
| ENG-HITL | **No human-in-the-loop review workflow** — only referral + override-detection under the hood | 🟠 | PARTIAL | `referral_rules.py:291`, `override_detector.py:27,66-80`, `benchmarking_report.py`; no reviewer queue / bulk-labeling UX |
| ENG-ASK | **No cross-copilot conversational surface** — NL query lives only in DataOps DI | 🟡 | PARTIAL | `di/claude_parser.py`, `di/query_service.py`, `NLQueryPanel.tsx`; no cross-copilot ask endpoint |
| ENG-REPORT | **Thin reporting** — weekly report + ROI exist; no scheduling or BI export | 🟡 | PARTIAL | `report_router.py:56-68`, `roi.py:48,112`; no scheduling/BI export |

## 4. Data-wiring

| ID | Gap | Sev | Status | Evidence |
|---|---|---|---|---|
| ENG-WIRE | **No shared factor provenance/freshness enforcement** — most factor paths fixture/cache-backed until wired per deployment; no per-request live/fixture provenance contract | 🟠 | PARTIAL | SAP/Celonis live+cache fallback (`sap_connector.py`, `celonis_connector.py:44-99`); OpenMeteo **is** wired (`scoring/verification/weather.py:31-42,62-84`; purchasing `context_router.py:195-204`) |

## 5. Doc/code-truth

| ID | Gap | Sev | Status | Evidence |
|---|---|---|---|---|
| ENG-S2PCLI | **S2P has no CLI** — HTTP routes only | 🟡 | OPEN | `s2p_registry.py:28-30` maps HTTP score/learn/outcome; no `cli.py` |
| DOC-SOC-CAT | **SOC PD categories ≠ code** | 🟡 | OPEN | code `soc/config.py:92-99` = credential_access, malware_execution, lateral_movement, data_exfiltration, insider_threat, cloud_infrastructure |
| DOC-TRD-TENSOR | **Trading tensor doc drift** | 🟡 | OPEN | code `presets/trading.py:38-49,116-123` = **(5,4,10)**; PD says (5,4,7) |
| DOC-S2P-TENSOR | **S2P tensor doc drift** | 🟡 | OPEN | code `s2p/config.py:38-48` + `presets/s2p.py:29-33` = **(5,5,8)**; stale `CLAUDE.md:30-49` says (5,5,7) |

---

## 6. Dependencies & closure condition (per gap)

| ID | Depends on | Closed when |
|---|---|---|
| ENG-ENC | — | every production DSN enforces encrypted transport; `sslmode=disable` absent from production paths; at-rest/field-encryption tests pass |
| ENG-AUTH | — | every protected endpoint invokes one shared auth dependency; role/permission tests cover caller + admin paths |
| ENG-TENANT | ENG-AUTH | every request carries an authenticated tenant; reads/writes enforce tenant+domain; cross-tenant tests fail closed |
| ENG-RATE | ENG-AUTH | inbound throttled by tenant+route with a stable 429 contract |
| ENG-DEPLOY | ENG-ENC, ENG-AUTH | each component has a reproducible container + restore/rollback path + versioned API + shared error envelope |
| ENG-COMPLY | ENG-AUTH | every component emits a verified audit chain into a common evidence model; controls mapped to SOC2/ISO/EU-AI-Act |
| ENG-DELIVER | ENG-AUTH, ENG-RATE | all sends authenticated, audited, retryable, per-channel; broker writes stay disabled unless prod flag set |
| ENG-COLDSTART | ENG-AUTH, ENG-WIRE | one onboarding path creates tenant config, runs bootstrap, predicts convergence, selects archetype, records pilot status |
| ENG-HITL | ENG-AUTH | reviewer can claim/resolve/bulk-label queued cases, capture disagreement, persist with audit identity |
| ENG-ASK | ENG-AUTH, ENG-TENANT | one authenticated ask endpoint routes across domains with tenant-scoped context + explicit unsupported-query response |
| ENG-REPORT | ENG-DELIVER | reports schedulable per tenant, delivered via authenticated channel, BI-compatible export |
| ENG-WIRE | ENG-TENANT | every factor reports live/fixture provenance + freshness; fallback explicit per request |
| ENG-S2PCLI | ENG-AUTH | documented `s2p` command: invoice-gen, scoring, learning, reporting, stable exit codes |
| DOC-SOC-CAT | — | PD + catalogs reproduce the six code categories; examples validate against `config.py` |
| DOC-TRD-TENSOR | — | all Trading docs/schema checks state + validate (5,4,10) |
| DOC-S2P-TENSOR | — | all S2P docs/schemas state + validate (5,5,8); stale (5,5,7) removed |

*Dependency note: nearly everything depends on **ENG-AUTH** (identity is the keystone); **ENG-ENC** is
independent. The DOC-* fixes are independent doc edits.*

---

*Verified against code by SCAN-D (read-only); full per-gap evidence at
`copilot-sdk/docs/catalog_scans/scan_d_eng_roadmap_verification.md`.*
