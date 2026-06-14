# Session Continuation — Codex Hero Document
**Authority:** MAP v5.154 (supersedes v5.154)
**Repos:** All 5 (SDK, S2P, CI, SOC, GAE)
**Purpose:** Pick up exactly where this session ended.
**Source:** Merged Codex SC + Codex CLI Playbook v4.5 + operational references from main SCs.
**Use as:** Single handoff document for Codex coding sessions.

---

## Read This First

### Platform State After This Session

| Repo | Tag | Tests | Status |
|---|---|---|---|
| CI | **v0.7.4-ci** | 555 passed, 0 failed | ✅ |
| SDK | **v0.7.4** | ~1160 passed, 0 failed | ✅ |
| S2P | **v0.7.2-s2p** | 1043 passed, 0 failed | ✅ |
| SOC | **v5.89** | DIRTY (scratch/temp only) | ✅ |
| GAE | v0.7.25 | 1,237 | ✅ unchanged |

### What Shipped This Session

| Item | Repo | Tag | Evidence |
|---|---|---|---|
| Track A: Route closeout (4 items) | CI + SOC | v0.7.2-ci, v5.89 | AGE timeout, 4-state policy, p95/p99, pool logging |
| P28: S2P financial impact | S2P | v0.7.2-s2p | 13 tests, FinancialSummary + compute_financial_impact |
| P29-A: Migration core + L1-L2 verify + fixer | SDK | v0.7.2 | 23 tests, Class B idempotent, gating logic |
| P29-B: Scratch graph + adversarial JSON + fixer | SDK | v0.7.3 | 41 tests (12+29), domain-scoped, original transforms |
| P29-C: L3 state-vector + fixer | SDK | v0.7.4 | 13 tests, 210-decision DK proof |
| P29-D: Shadow scorer + fixer | SDK | v0.7.4 | 17 tests, 40/40 proven live |
| P30: DI Source Profiler | SDK | v0.7.5 | 16 tests, BaseSourceProfiler |
| AGE agtype normalizer | CI | v0.7.4-ci | 15 tests, systemic read-side fix |
| DDL autocommit fix | SDK | v0.7.4 | scratch graph create/drop live-proven |
| 36→0 test failures fixed | SDK + CI | v0.7.2, v0.7.3-ci | demo test rewrite + mypy fixes |
| Mypy test exclusion | SDK | v0.7.3 | --exclude site-packages |
| MAP v5.154→v5.154 produced | — | — | 525→529 lines, 59→62 rules |
| A1 2000-decision scale analysis | SOC | — | WATCH classification, outlier-distorted avg |

### All Committed and Pushed

No pending commits. Final tags:

| Repo | Tag | Pushed |
|---|---|---|
| CI | v0.7.4-ci | ✅ |
| SDK | v0.7.5 | ✅ |
| S2P | v0.7.2-s2p | ✅ |
| SOC | v5.89 | ✅ |
| GAE | v0.7.25 | ✅ unchanged |

---

## What's Next (In Order)

### 1. Remaining Copilot Migrations (manual runs, same tooling)

Trading is proven. Run the same migration for each copilot:

```powershell
# Purchasing (20 verified)
python -m copilot_sdk.migrate sqlite_to_age --domain=purchasing --age-dsn="host=localhost port=5433 dbname=soc_copilot user=postgres password=postgres" --graph-name=soc_graph --use-scratch-graph

# DataOps (20 verified)
python -m copilot_sdk.migrate sqlite_to_age --domain=dataops --age-dsn="host=localhost port=5433 dbname=soc_copilot user=postgres password=postgres" --graph-name=soc_graph --use-scratch-graph

# S2P (12 verified)
python -m copilot_sdk.migrate sqlite_to_age --domain=s2p --age-dsn="host=localhost port=5433 dbname=soc_copilot user=postgres password=postgres" --graph-name=soc_graph --use-scratch-graph
```

### 2. P30-P35: Remaining Written Prompts

| P# | ID | Repo | Status |
|---|---|---|---|
| P30 | DI-1-SOURCE-PROFILER-P1 | SDK | **✅ DONE** (v0.7.5, 16 tests) |
| P31 | S2P-F10-FINANCIAL-P2 | S2P | WRITTEN (P28 done) |
| P32 | DI-1-SOURCE-PROFILER-P2 | SDK | WRITTEN |
| P33 | G12-SITUATION-P1 | SDK/SOC | WRITTEN |
| P34 | DI-2-INTELLIGENCE-MAP | SDK | WRITTEN |
| P35 | G12-SITUATION-P2 | SDK/SOC | WRITTEN |

### 3. P36+ Feature Queue (50 items)

Per MAP v5.154 §4. S2P first (P36-P41), then DI (P42-P47),
then Trading (P48+).

---

## Codex Workflow (Validated This Session)

**GPT removed from pipeline.** Opus writes 3-stage prompts directly:

```
Stage 1 (5.3, read-only): Discovery + pre-checks
Stage 2 (5.3): Implementation with adaptation instructions
Stage 3 (5.5): Line-by-line review + blast radius + architecture
```

**Key lessons from this session:**

1. **Structured response format is mandatory.** Tell Codex exactly
   what sections to produce. Without it, output is unparseable.

2. **act.ps1 doesn't work in Codex.** Use full venv activation path:
   `& "C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\proj-envs\python_expts_venv\Scripts\Activate.ps1"`

3. **Stage 1 findings feed Stage 2 literally.** Inject actual schema,
   API signatures, and DB paths into Stage 2. Don't let Codex re-scan.

4. **Review must check blast radius + judgment memory.** Stage 3
   catches things tests don't: domain-scoped idempotency (P2),
   scratch retention semantics (P2), AGE readback normalization (P2).

5. **Fixers are small and targeted.** P29-A fixer (gating logic) and
   P29-B fixer (3 P2s) were each one prompt, <30 lines changed.

6. **Server management stays in PowerShell.** Codex never starts/stops
   backends. Manual dry-run validates before commit.

7. **Reference docs in-repo.** Tell Codex to read
   `docs/design/judgment_memory_v2_7.md` and
   `docs/design/dk_runtime_execution_plan_v6_8.md` before implementing.

---

## Architecture Decisions Made This Session

### Route Architecture: CLOSED (v4.2)

```
A1 Scale: WATCH (flat through 1500, outlier at 2000)
Hot-path Packages 2-5: PARKED (trigger: analyze p95 > 500ms sustained)
Route policy: 4 states (CANONICAL_ONLY, SHADOW, PIPELINE_SERVED, DISABLED)
Outlier fix: connect_timeout=10 + statement_timeout=120s
Pool: psycopg_pool installed, pool code wired, logging added
p95/p99: emitted in runner reports
```

### P29 Migration Design (Consolidated, 7 Issues)

```
Issue 1: Direct psycopg (not AGEClient) — async API, sync migration
Issue 2: AGEClient.serialize_for_age() — static method, not _S()
Issue 3: Home DB is source of truth — operational judgment memory
Issue 4: SDK baseline failures — pre-existing, don't block
Issue 5: 3-level verification (count + content + state-vector)
Issue 6: Re-derive strategy — migrate log, not state
Issue 7: Reversibility — keep SQLite, shadow before serving
```

### AGE Capabilities (Tested Live)

```
CREATE GRAPH: ✅ supported
DROP GRAPH:   ✅ supported
RENAME GRAPH: ❌ not supported (syntax error)
MERGE node:   ❌ rejected (ON CREATE SET syntax error)
Pattern:      MATCH-then-CREATE (proven correct)
```

---

## Standing Rules Updates

| Rule | Change |
|---|---|
| #40 | Confirmed: localhost for DSN, 127.0.0.1 for HTTP |
| #58 | Enforced: no raw sqlite3 (migration exempt) |
| #59 | AGE smoke gates at tier boundaries (non-blocking) |
| #60 | NEW: AGE read-side normalization — `normalize_agtype_value()` from `ci_platform.graph.agtype` |
| #61 | NEW: Shadow scorer store isolation — from_preset() rejects `primary_store is shadow_store` |
| #62 | NEW: Migration source of truth — home DB default, repo DBs are dev artifacts |
| — | act.ps1 path: `C:\Users\baner\OneDrive\Documents\Powershell\act.ps1` |
| — | Codex venv: `& "C:\Users\baner\...\Activate.ps1"` (full path) |

---

## Performance Baselines (Updated)

| Metric | Value | Source |
|---|---|---|
| SOC analyze (250, post-campaign-P1) | 193ms | P2E baseline |
| SOC analyze (500) | 236ms | A1 scale |
| SOC analyze (1000) | 307ms | A1 scale |
| SOC analyze (1500) | 255ms | A1 scale |
| SOC analyze (2000, ex-outlier) | ~286ms | A1 scale (13,977s outlier removed) |
| SOC analyze (2000, raw avg) | 7,274ms | Outlier-distorted |
| EntityCache: PARKED | 202ms (no gain over 193ms) | P3H benchmark |
| Hot-path status | DESIGNED + PARKED | Trigger: p95 > 500ms sustained |

---

## Test Counts (Verified End of Session)

```
CI:        555 passed, 14 skipped, 0 failed
SDK:       ~1160 passed, 62 skipped, 0 failed (first clean suite)
S2P:       1043 passed, 10 skipped, 0 failed
SOC:       ~1742 passed (not re-run this session)
GAE:       1237 passed (unchanged)
TOTAL:     ~5,786+
```

### Migration-Specific Tests
```
P29-A migration core:      29
P29-B scratch graph:        12
P29-C state-vector:         13
P29-D shadow scorer:        17
CI agtype normalizer:       15
P30 DI profiler:            16
Total new tests this session: 102
```

---

## Key Files Modified This Session

### CI-Platform
- `ci_platform/graph/age_client.py` — connect_timeout=10, statement_timeout=120s, pool logging
- `ci_platform/graph/agtype.py` — NEW: AGE read-side normalization utility
- `ci_platform/copilot_core/counters.py` — mypy CounterRead casts
- `ci_platform/copilot_core/background.py` — mypy task typing
- `tests/test_agtype.py` — 15 normalization tests

### SDK
- `copilot_sdk/migrate/__init__.py` — NEW package
- `copilot_sdk/migrate/__main__.py` — CLI with --use-scratch-graph
- `copilot_sdk/migrate/sqlite_to_age.py` — migration core (~460 lines)
- `copilot_sdk/migrate/scratch_graph.py` — NEW scratch graph lifecycle
- `copilot_sdk/migrate/verify_state.py` — NEW L3 state-vector verification
- `copilot_sdk/migrate/shadow_scorer.py` — NEW shadow scorer discipline
- `copilot_sdk/di/nl_query.py` — mypy narrowing
- `copilot_sdk/scoring/iks_service.py` — mypy narrowing
- `scripts/shadow_live_test.py` — NEW live shadow validation script
- `tests/test_sqlite_to_age_migration.py` — 29 tests
- `tests/test_scratch_graph.py` — 12 tests
- `tests/test_verify_state.py` — 13 tests
- `tests/test_shadow_scorer.py` — 17 tests
- `tests/test_demo_age_ops.py` — rewritten for current API (19 tests)
- `tests/test_type_checking.py` — exclude site-packages

### SOC
- `backend/app/services/route_policy.py` — 4-state collapse
- `backend/tests/test_route_policy_resolver.py` — 18 tests
- `scripts/diagnostics/run_soc_diag_f.py` — p50/p95/p99

### S2P
- `backend/app/services/financial_impact.py` — FinancialSummary
- `backend/tests/test_financial_impact.py` — 13 tests

---

## Git State

| Repo | Tag | Commits ahead | Clean? |
|---|---|---|---|
| CI | v0.7.4-ci | 0 | ✅ |
| SDK | v0.7.4 | 0 | ✅ |
| S2P | v0.7.2-s2p | 0 | .db DIRTY only |
| SOC | v5.89 | 0 | scratch/temp DIRTY only |
| GAE | v0.7.25 | 0 | ✅ |

---

## Execution Plan Status

| Set | ID | Status | Tests |
|---|---|---|---|
| 1 | P28 + P29-A | ✅ SHIPPED + FIXER | 29 + 13 |
| 2 | P29-B | ✅ SHIPPED + FIXER | 12 |
| 3 | P29-C | ✅ SHIPPED + FIXER | 13 |
| 4 | P29-D | ✅ SHIPPED + FIXER | 17 |
| — | Agtype normalizer | ✅ SHIPPED | 15 (CI) |
| — | Demo test rewrite | ✅ SHIPPED | 19 |
| — | Mypy fixes | ✅ SHIPPED | — |
| — | Shadow live validation | ✅ 40/40 proven | — |
| **TOTAL** | | **ALL P29 COMPLETE** | **86+ new tests** |

---

*Session Continuation · June 11-12, 2026 · MAP v5.154*
*Route Architecture CLOSED (v4.2). P28 + P29 (all 4 sets) shipped.*
*0 SDK failures. 86 migration tests. Trading 150 decisions migrated.*
*Shadow scorer 40/40 proven on live data. SQLite preserved as rollback.*
*62 standing rules. 5,737+ tests across all repos.*
*Next: remaining copilot migrations → P30-P35 → P36+ features.*

---

## P29 Design Rationale (from earlier session snapshot)

### P29-C: Level 3 State-Vector Verification — Design Intent

The real test — proves migration preserves learned judgment, not just decision rows.

**What it does:** Load scorer from SQLite source, load scorer from AGE (after migration), compare full state vector: ALL centroids (C×A×D tensor), DK weights, conservation state (V, q, α). If state vectors match → migration is proven correct. If they diverge → ordering or completeness bug.

**Why it matters:** Decisions are the LOG. The scorer state is the PRODUCT. Verification Levels 1-2 (count + content parity) prove the log copied correctly. Level 3 proves the product re-derives identically. DecisionCountPolicy(200), James-Stein shrinkage, and conservation α·q·V are all path-sensitive — if ordering or count drifted, the state vector diverges even with identical rows.

**Status:** ✅ SHIPPED (P29-C). 13 tests. 210-decision DK proof verified.

### P29-D: Shadow Scorer Discipline — Design Intent

Operational validation. Same canonical→shadow→served discipline from route architecture: run AGE-backed scorer alongside SQLite-backed scorer, compare outputs on real traffic, log discrepancies. After N zero-discrepancy requests → switch GRAPH_BACKEND. SQLite stays intact as rollback.

**Status:** ✅ SHIPPED (P29-D). 17 tests. 40/40 proven on live data.

---

# ══════════════════════════════════════════════════════════
# CODEX CLI PLAYBOOK v4.5 (Operating Procedures)
# ══════════════════════════════════════════════════════════

# Codex CLI Playbook v4.5
**Date:** May 25, 2026 · **Authority:** MAP v5.52 + session learnings through FEATURE-07 / D-04 / D-08 diagnostics + AgentEvolver / CX3 / TAB7-GOV / RL Phase 4 prompt-verification workflows + May 2026 architecture-audit addendum + multi-part response packaging policy  
**Supersedes:** Codex CLI Playbook v4.4 / v4.3 / v4.2 / v4.1 / v4 / v3  
**Purpose:** Operating procedure, prompt patterns, verification workflow, quota-aware model selection, reusable prompt templates, multi-part response packaging, and mandatory **line-by-line + architecture/system-integrity review** standards for Codex CLI across the current multi-repo workspace.

---

## §0 — Executive Defaults

Use these defaults unless the user explicitly overrides them.

1. **Start every non-trivial task with Prompt 0.** Prompt 0 proves paths, reads `CLAUDE.md`, resolves repo-relative paths, confirms scope, and creates a plan. It does not edit.
2. **For code changes, always include a post-implementation line-by-line review.** Tests passing is not completion.
3. **For code changes, always include an architecture/system-integrity review.** A local line-by-line pass is not enough. The review must also verify that the implementation did not duplicate abstractions, create hidden state, bypass reset/GraphStore/DecisionStore/preset patterns, drift from canonical framework files, or create fixture-only paths where live data should be used.
4. **Use GPT-5.3 by default to conserve Codex quota.** Use GPT-5.5 only for mandatory reviews after code has been changed or added, or when the user explicitly requests it.
5. **Prompts must be self-contained by default.** Do not tell Codex to rely on attached files. Restate context, paths, constraints, acceptance criteria, and verification steps directly in the prompt.
6. **Use repo-local documents for durable design, architecture, review, diagnostics, or multi-step planning.** If later Codex prompts must reuse a plan, Codex must create/read it inside the repo, usually under `docs/implementation_plans/` or an explicitly named docs path.
7. **Implementation overrides design docs.** Design docs explain intent and rationale. Live code and tests define current behavior. If they conflict, report the conflict; do not silently force code to match stale docs.
8. **PowerShell-first.** The user is on Windows 11. Use PowerShell-safe commands and fully qualified paths.
9. **No git unless explicitly requested.** Codex should not use git for status/diff/checkout unless the user explicitly authorizes it.
10. **Frontend E2E rule:** Codex must not run Playwright unless the user confirms the full live stack is running. Codex should run `npm run build` for frontend changes.
11. **Design review before implementation for high-risk graph/runtime changes.** For architecture-heavy changes, use GPT-5.3 to produce the plan, GPT-5.5 to review/update the repo-local plan, GPT-5.3 to implement from the approved plan, then GPT-5.5 to review changed code.
12. **`READY: YES` in a no-edit Prompt 0 is not a contradiction.** It means discovery/design is complete and the next implementation prompt may proceed. The `DO NOT EDIT FILES` rule applies only to that read-only prompt.
13. **Verify the prompt before sending it to Codex.** For non-trivial or high-risk work, every final prompt set must include a Prompt Verification Pass: check assumptions, allowed/forbidden scope, old-behavior equivalence, side effects, tests, stop conditions, and the required GPT-5.5 review. Add an explicit “How could this prompt create a fixer?” section for integration/runtime changes.
14. **Split ultra-large prompt sequences into multiple ChatGPT responses.** If a `process_request:` response is likely to become too long or risk truncation, provide Part 1 first, clearly label the total sequence, and continue with later parts only when the user asks. Do not cram Prompt 0, multiple implementation prompts, review prompts, and fixer templates into one response if that risks an incomplete answer.
15. **Proactively correct the request before prompt generation.** Check requests for accuracy, correctness, stale assumptions, wrong paths, brittle shell, missing scope, missing negative tests, missing review, architecture risks, downstream side effects, and oversized prompt shape. Make material fixes before producing the prompt sequence.
---

## §1 — Operating Model

### 1.1 Task Classification

| Task Type | Edits? | Output | Default Model | When to use |
|---|---:|---|---|---|
| **Review-only** | NO | Findings with file:line evidence | GPT-5.3 | Bug hunts, contract checks, security reviews |
| **Coding** | YES | Changed files + tests + self-review | GPT-5.3 | Targeted fixes, features, tests |
| **Mandatory code review** | NO | Line-by-line review + architecture/system-integrity audit of changed/added code | GPT-5.5 | Required after every code-change task |
| **Decision-support** | NO | Recommendation memo | GPT-5.3 | Architecture choices, alternatives |
| **Design-point validation** | NO | FEASIBLE / ISSUES / NOT FEASIBLE | GPT-5.3 | Pre-implementation design checks |
| **Diagnostic report** | DOC ONLY | Markdown report | GPT-5.3 | Read-only investigation + report |
| **Fixer** | YES, limited | Minimal fix + tests | GPT-5.3 | Only after review finds P1/P2 |

### 1.2 Five Things to State Before Writing Prompts

1. **Repo / working directory**: exact path from `claude_projects`.
2. **Task type**: review, coding, diagnostic, decision, design validation.
3. **Allowed edit scope**: exact files and forbidden files.
4. **Required outputs**: format, evidence rules, test logs, changed files.
5. **Stop condition**: e.g., `>=3 P1 findings -> stop and report`.

### 1.3 Standard `process_request:` Behavior

When the user writes `process_request:` with a request or says to use an attached file:

1. Deeply understand the request.
2. Fix obvious workflow issues: wrong paths, stale filenames, brittle shell, missing gate, missing review, missing tests.
3. Convert the request into a sequence of **self-contained Codex prompts**.
4. Include exact PowerShell commands and repo-relative paths.
5. Add Prompt 0 gate/discovery unless task is tiny and safe.
6. Include a mandatory line-by-line review prompt for code changes.
7. Include a mandatory architecture/system-integrity review block for code changes.
8. Include how the user verifies Codex output.
9. Do not ask the user to manually upload/paste files into Codex. Restate the needed context inside prompts.
10. Before finalizing the prompts, run a prompt-level verification pass: identify unverified assumptions, hidden downstream consumers, old-behavior equivalence risks, side-effect ordering risks, reset/state risks, missing negative tests, and scope gaps. Revise the prompts before presenting them.
11. If the generated command/prompt sequence is likely to be too large for one ChatGPT response, split it into multiple labelled parts instead of risking truncation.
12. For architecture/design/review work, prefer repo-local documents that later Codex prompts can read; for normal implementation/fixer work, prefer self-contained prompts.

### 1.4 Multi-Part Response Policy for `process_request:`

Use this policy when the generated sequence would likely exceed a safe single-response size, such as when it includes Prompt 0, multiple implementation prompts, a long GPT-5.5 review prompt, validation commands, and a fixer template.

**Default behavior:**
- Produce **Part 1** with the corrected workflow, assumptions repaired, execution order, and the first one or two prompts.
- Explicitly label what remains: for example, “Part 2 will contain Prompt 2 and validation; Part 3 will contain the GPT-5.5 review and fixer template.”
- Wait for the user to say “continue” before producing the next part.
- Keep each part independently useful and copyable; do not end a prompt mid-code-block.
- Never rely on an unstated future continuation for a prompt already shown. Every prompt included in a part must be complete.

**When to split:**
- More than two long Codex prompts are needed.
- A GPT-5.5 review prompt is broad and detailed enough to be its own response.
- The task spans multiple repos, frontend + backend, graph/runtime state, or fixture/data + API + tests + docs.
- The response includes large command blocks and long validation matrices.
- Prior ChatGPT responses have been truncated or partially generated in the same workflow.

**Recommended part structure:**

```text
Part 1 of 3 — Analysis + Prompt 0 + Prompt 1
- Corrected request interpretation
- Scope and repo path
- Execution order
- Prompt 0 gate/discovery
- First implementation or design prompt, if short enough

Part 2 of 3 — Remaining implementation/design prompts
- Prompt 2 / Prompt 3 as needed
- Validation commands
- Recovery guidance for partial execution

Part 3 of 3 — GPT-5.5 review + targeted fixer template
- Broad line-by-line + architecture review prompt
- Optional targeted fixer skeleton
- Final execution checklist
```

**Recovery rule:** If the user reports that a prompt was partially copied or partially generated, create a recovery/completion prompt that first inspects current repo state, identifies what is already done, and completes only missing work. Do not instruct Codex to repeat the entire implementation blindly.

---

## §2 — Current Workspace & Path Rules

### 2.1 Base Workspace

Use this base path. Note the hyphen in `python-projects`.

```powershell
C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\kaggle_experiments\claude_projects
```

### 2.2 Current Repo Map

| Repo | Local source | Tests | Notes |
|---|---|---|---|
| `gen-ai-roi-demo-v4-v50` | `backend/app/`, `frontend/src/` | `backend/tests/`, `frontend/tests/e2e/` | Current SOC main repo |
| `graph-attention-engine-v50` | `gae/` | `tests/` | Current GAE repo |
| `ci-platform` | `ci_platform/` | `tests/` | Platform/audit/connectors |
| `s2p-copilot` | `backend/app/` | `backend/tests/` | S2P domain repo |
| `copilot-sdk` | `copilot_sdk/` | `tests/` | SDK repo |
| other historical dirs | `gen-ai-roi-demo-v4-*`, `graph-attention-engine-v45` | varies | Use only if explicitly requested |

### 2.3 Path Resolution Rule

If a request assumes a file path, Prompt 0 must prove it exists before deeper work. If the path might have drifted, Prompt 0 resolves the actual file.

PowerShell example:

```powershell
cd "C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\kaggle_experiments\claude_projects"
Test-Path ".\gen-ai-roi-demo-v4-v50\CLAUDE.md"
Test-Path ".\graph-attention-engine-v50\gae\profile_scorer.py"
```

### 2.4 Command Rule

Every Codex shell command is a fresh shell. Always chain path + command.

```powershell
cd "C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\kaggle_experiments\claude_projects\gen-ai-roi-demo-v4-v50\backend"; python -m pytest tests/ -q
```

Avoid Unix-only patterns unless the environment explicitly supports them.

| Avoid | Prefer |
|---|---|
| `head`, `tail`, `grep -v`, fragile pipes | PowerShell `Select-String`, direct file reads, targeted commands |
| vague `cd repo && pytest` | fully qualified `cd "...\repo\backend"; python -m pytest ...` |
| assuming path | `Test-Path` first |

---

## §3 — Prompt Patterns

### 3.1 Review-Only Pattern

Use for bug hunts, audits, and contract checks.

```text
/model gpt-5.3
Echo the current model name in the first line of output.

TASK: <review title>
TASK TYPE: Review-only. NO EDITS.

GLOBAL RULES:
- Do NOT use git.
- Do NOT modify files.
- Read CLAUDE.md first.
- Read full relevant functions/blocks, not just grep hits.
- No evidence, no claim.
- Cite file:line evidence for every finding.
- Classify findings as P1/P2/P3.

OUTPUT FORMAT:
REVIEW VERDICT:
P1 BUGS:
P2 BUGS:
P3 ISSUES:
READING LOG:
FIXER NEEDED:
```

### 3.2 Coding Pattern

Use unless the change is tiny and obviously safe.

```text
Prompt 0 — PLAN/PROOF ONLY, no edits:
  Read CLAUDE.md. Prove paths. Read relevant files. Confirm scope.
  Produce implementation plan, invariant table, and test plan.

Prompt 1 — IMPLEMENT, edits allowed:
  Edit only specified files. Smallest safe patch. Run targeted and required tests.
  Report changed files, test commands, pass/fail, residual risks.

Prompt 2 — POST-IMPLEMENTATION REVIEW, no edits:
  Use GPT-5.5. Re-read changed files line by line.
  Verify correctness, edge cases, tests, scope, downstream drift, and architecture/system-integrity.
```

**Critical:** `Tests passed` is not completion until Prompt 2 review passes.

### 3.3 Diagnostic / Report Pattern

Use when the request says read-only but also asks to produce a report.

Clarify scope:

> No source/test/config behavior changes. The only allowed write is the diagnostic Markdown report.

```text
Prompt 0 — Evidence pass, no edits:
  Read docs/source/tests. Gather file:line evidence.
  Produce conclusions and report plan.

Prompt 1 — Write report only:
  Modify only <REPORT>.md. No fixes. No source/test changes.

Prompt 2 — Review report, no edits:
  Cross-check report claims against source. P1/P2/P3 doc issues only.
```

### 3.4 Decision-Support Pattern

```text
1. Verify the premise live in code.
2. Compare alternatives against actual data flow.
3. Scope blast radius across repos/files/tests.
4. Recommend: option, confidence, blockers, implementation sequence.
```

### 3.5 Design-Point Validation Pattern

For each point:

1. Restate the proposal.
2. Read actual code paths it would touch.
3. Assess feasibility, risks, modifications needed.
4. Verdict: `FEASIBLE`, `ISSUES`, or `NOT FEASIBLE`.
5. Recommendation and test impact.


---

### 3.6 Repo-Local Design Document Pattern

Use this when a task asks for architecture, design, or implementation planning that will be used by later Codex prompts. The plan must live in the repo so Codex can read it in the next step.

**When to use:**
- graph repair / seed repair plans;
- cross-module architecture changes;
- status semantics or API contract changes;
- multi-step runtime features;
- any design that needs a separate GPT-5.5 review before coding.

**Workflow:**

```text
Prompt A — GPT-5.3 design/investigation:
- NO source/test edits.
- Create/update exactly one Markdown plan in the repo, e.g.
  docs/implementation_plans/<topic>.md.
- Include file:line evidence, dependency assessment, implementation plan, commands, tests, blockers.

Prompt B — GPT-5.5 plan review/update:
- NO source/test edits.
- Read the repo-local plan and source files.
- Update the same plan in-place if needed.
- Output READY_FOR_IMPLEMENTATION: YES/NO.

Prompt C — GPT-5.3 implementation:
- Read the approved plan file first.
- Implement exactly from the plan.
- Run targeted/regression tests.

Prompt D — GPT-5.5 code review:
- Mandatory line-by-line review of changed files.
- P1/P2 -> targeted fixer.
```

**Important:** A plan saved to ChatGPT’s sandbox (`/mnt/data`) does not help Codex. Codex must create the plan inside the working repo, usually under `docs/implementation_plans/`.

### 3.7 Scope-Repair Pattern

Use when Prompt 0 disproves the original premise. Do not force the old plan through.

Examples:
- Discovery finds `LearningHealthMonitor.evaluate()` reads in-memory history, not AGE rows; AGE seeding alone cannot fix conservation GREEN/RED inconsistency.
- Discovery finds `app/framework/convergence.py` does not exist; rollback must register on the GAE `ConservationStateMachine` through the live scorer.
- Discovery finds a requested timestamp source uses `now - 90 days`, which would create AE-DRIFT risk.

Prompt response should say:

```text
READY: NO for original plan.
SCOPE REPAIR NEEDED:
- disproven assumption
- safe revised scope
- deferred items
- new implementation prompt
```

### 3.8 Read-Only Investigation that Saves a Document

When the user says “Do NOT implement” but wants a durable architecture document, allow exactly one doc write.

```text
TASK TYPE: Architecture investigation + design document only. DO NOT implement.
ALLOWED WRITE:
- docs/implementation_plans/<topic>.md
FORBIDDEN:
- source files
- tests
- scripts that mutate data
```

The document must be self-contained: a later implementation prompt should need only the plan file plus source code.


### 3.9 Prompt Verification Pass

Use this before presenting the final prompt set for any non-trivial task. This is a prompt-quality gate, not a Codex task.

**Purpose:** reduce avoidable fixer-prompts by catching prompt flaws before Codex acts on them.

**Required checks:**

| Check | Question to answer before final prompt |
|---|---|
| Premise verification | Does Prompt 0 prove the request’s core assumption before editing? |
| Path verification | Are all repo paths and file names proven with `Test-Path` or equivalent? |
| Scope | Are allowed files exact, and are forbidden files broad enough to prevent drift? |
| Old behavior equivalence | With all new flags off or default config, is old behavior explicitly preserved and tested? |
| Side-effect ordering | Could a proposed internal change leak to audit, external write-back, events, metrics, or UI before a safety gate finalizes? |
| State/reset | Are module state, singleton state, caches, buffers, and reset-all paths included? |
| Async/concurrency | Are sync/async boundaries, locks, fire-and-forget tasks, and loop availability handled? |
| Query safety | Are AGE/Cypher rules, `_S()` requirements, and forbidden patterns explicitly tested? |
| Downstream consumers | Are all tabs/endpoints/scripts/tests/PDF/export surfaces mapped for semantic changes? |
| Tests | Are there behavioral tests, not only source-string checks? Are negative/regression tests included? |
| Review | Is the GPT-5.5 line-by-line review prompt included for any code change? |

**Template to add to high-risk prompts:**

```text
PROMPT VERIFICATION PASS:
Before finalizing this plan, verify:
1. All referenced paths exist.
2. The implementation preserves old behavior when new flags/config are off.
3. No safety/referral/conservation gate is bypassed.
4. No side effect is emitted before final decision state is known.
5. All state reset paths are updated.
6. Tests behaviorally prove the new invariant and the old-regression case.
7. The allowed/forbidden file scope prevents broad drift.
8. A GPT-5.5 review prompt is included.
If any item is unresolved, STOP and report instead of implementing.
```

### 3.10 “How Could This Prompt Create a Fixer?” Section

For runtime, graph, triage, reset, AgentEvolver, RL, or multi-consumer status changes, include this section in the prompt itself.

```text
HOW THIS PROMPT COULD CREATE A FIXER:
Before editing, identify likely failure modes:
- Old behavior equivalence risk:
- Side-effect ordering risk:
- Hidden downstream consumer risk:
- Test fixture risk:
- Feature-flag/default risk:
- Reset/state cleanup risk:
- Async/concurrency risk:
- Graph query safety risk:
- UI/API contract risk:

For each risk, either:
- add a discovery check,
- add an implementation constraint,
- add a regression test,
- or STOP and report that the prompt is not safe to execute.
```

**Rule of thumb:** if you can imagine a GPT-5.5 review saying “the implementation fixed A but broke B,” B belongs in this section before implementation.

### 3.11 Old-Behavior Equivalence Pattern

Use when adding a feature flag, moving a safety gate, changing a producer status, or reordering a workflow.

```text
OLD BEHAVIOR EQUIVALENCE:
With all new feature flags disabled / default config unchanged, prove old behavior is unchanged for:
- API response fields
- persisted graph properties
- audit ledger entries
- external write-back / Sentinel calls
- event emissions
- referral/conservation/safety gate inputs
- reset state
- downstream metrics and tab content

Tests required:
- one positive test for the new behavior
- one negative test proving the old path with flags off
- one side-effect test proving no unintended external/persisted change
```

This pattern exists because the RL Phase 4 referral fix correctly fixed side-effect ordering but initially changed referral count semantics. Old-behavior equivalence would have forced a test for R2/R7 count inputs before implementation.

---


### 3.12 Architecture / System-Integrity Review Pattern

Use this for every code-change prompt and every GPT-5.5 post-implementation review. A line-by-line review answers “is this code locally correct?” The architecture review answers “did this change break the system design?”

**Why this exists:** Recent code analysis found issues that a local review might not catch: GraphStore fragmentation, RL state surviving demo resets, `scorer.py` returning infinity on validation errors, display/gate formula mismatch, S2P framework drift, duplicated invoice loading, fixture-only AE data paths, and S2P not yet fully aligned with `PRESET_REGISTRY`.

#### Implementation prompt guardrail

Add this to every non-trivial implementation prompt:

```text
ARCHITECTURE GUARDRAILS:
Before editing, identify the architectural boundary this change touches.

Check:
1. Does this duplicate an existing abstraction/helper/router/store?
2. Does this introduce app-local/private infrastructure where SDK/platform infrastructure already exists?
3. Does this add in-memory state that survives reset or bypasses the state_manager reset pattern?
4. Does this create drift from canonical SOC/SDK/S2P framework files?
5. Does this create a fixture-only path where live data should be used?
6. Does this bypass GraphStore / DecisionStore / EvidenceLedger / state_manager / preset registry?
7. Does this change only visible UI/API while leaving the canonical backend/gate/formula different?
8. Does this preserve reset/demo integrity?
9. Does this preserve factory/preset patterns instead of special-casing one copilot?
10. Does this leave TODO compatibility bridges in place instead of removing them?

If any answer is risky, STOP and report before editing unless the prompt explicitly authorizes the architecture change.
```

#### Post-implementation review audit

Add this to every GPT-5.5 code review prompt:

```text
ARCHITECTURE REVIEW AUDIT:
This is not only a line-by-line review. Perform a system-level architecture review and classify architecture failures as P1/P2/P3 even if the local code is correct.

Review areas:

1. Abstraction consistency
- Did the implementation reuse the canonical abstraction?
- Did it create a duplicate helper/store/router/cache?
- Did it add a private inline subclass or bridge that should live in SDK/platform code?

2. State/reset integrity
- Does all new mutable state reset through the canonical reset/state_manager path?
- Could demo reset leave stale RewardLedger, exploration policy, cache, scorer, baseline, fixture, or graph state?

3. Graph/store integrity
- Are graph links persisted through GraphStore rather than app-state memory?
- Are new GraphStore methods backward-compatible for structural implementations?
- Are SQLite/InMemory/AGE paths handled consistently or explicitly documented?

4. Formula/gate consistency
- Does the displayed formula match the enforced gate?
- Are threshold, conservation, reward, and scoring formulas using the same canonical parameters?
- Are penalty_ratio, learning_rate, and override_rate kept semantically distinct?

5. Framework drift
- Did this diverge S2P/SOC/SDK framework files from canonical versions?
- If divergence is intentional, is it registered in the drift/known-drift test?

6. Fixture vs live data
- Did this add or preserve fixture-backed UI/API where live SDK/backend data is expected?
- If fixture use remains, is it clearly labeled and cached appropriately?

7. Duplication / maintainability
- Did this create duplicate invoice loading, JSON loading, routing, cache, or helper logic?
- Should new logic live in an existing shared helper?

8. Preset/factory alignment
- Does the implementation use PRESET_REGISTRY / from_preset / canonical factory paths?
- Did it hardcode a copilot-specific path that blocks SDK migration?

9. Test architecture
- Do tests prove the architecture path, not just local behavior?
- Are there tests for reset, persistence, compatibility, and canonical-route usage?

10. Risk classification
- Mark architecture issues as P1/P2/P3 separately from line-level code bugs.
- A line-level PASS can still be FAIL_NEEDS_FIXER if architecture is broken.

OUTPUT MUST INCLUDE:
ARCHITECTURE_AUDIT:
- Abstraction consistency:
- State/reset integrity:
- Graph/store integrity:
- Formula/gate consistency:
- Framework drift:
- Fixture/live-data:
- Duplication:
- Preset/factory alignment:
- Test architecture:
- Architecture verdict: PASS / PASS_WITH_P3 / FAIL_NEEDS_FIXER
```

#### Combined review output format

```text
REVIEW_VERDICT:
P1_BUGS:
P2_BUGS:
P3_ISSUES:

LINE_BY_LINE_REVIEW_NOTES:
SCOPE_AUDIT:
TEST_AUDIT:
VALIDATION_AUDIT:

ARCHITECTURE_AUDIT:
- Abstraction consistency:
- State/reset integrity:
- Graph/store integrity:
- Formula/gate consistency:
- Framework drift:
- Fixture/live-data:
- Duplication:
- Preset/factory alignment:
- Test architecture:
- Architecture verdict:

FIXER_NEEDED:
- YES/NO
- If YES, smallest targeted fixer scope.
```

#### Example review prompt

```text
/model gpt-5.5
Echo the current model name in the first line of output.

TASK: Mandatory line-by-line + architecture review of <feature/fix>.
TASK TYPE: Review-only. NO EDITS.

RULES:
- Do NOT use git.
- Do NOT modify files.
- Read changed files fully.
- No evidence, no claim.
- Cite file:line evidence for every finding.
- Classify P1/P2/P3.

FILES TO REVIEW:
- <changed file 1>
- <changed file 2>

REFERENCE FILES:
- canonical store/router/config/framework files
- reset/state_manager files
- response models / frontend consumers
- tests proving the architecture path

REVIEW AREAS:
1. Line-by-line code correctness.
2. Scope and allowed-files compliance.
3. Test quality and validation logs.
4. Architecture/system-integrity:
   - abstraction consistency
   - state/reset integrity
   - graph/store integrity
   - formula/gate consistency
   - framework drift
   - fixture/live-data status
   - duplication/maintainability
   - preset/factory alignment
   - architecture-level test coverage

OUTPUT:
REVIEW_VERDICT:
P1_BUGS:
P2_BUGS:
P3_ISSUES:
LINE_BY_LINE_REVIEW_NOTES:
SCOPE_AUDIT:
TEST_AUDIT:
VALIDATION_AUDIT:
ARCHITECTURE_AUDIT:
FIXER_NEEDED:
```


### 3.13 Multi-Part Prompt Packaging Pattern

Use this when a full `process_request:` answer would be too long for one ChatGPT response. The goal is to avoid incomplete answers and half-generated Codex prompts.

**Packaging rules:**
1. Decide whether the output should be one response or multiple parts before drafting.
2. If multiple parts are needed, say so at the top of Part 1.
3. Each part must contain only complete prompts; never split a single Codex prompt across two ChatGPT responses.
4. Put the GPT-5.5 review prompt in its own part when it is long or architecture-heavy.
5. Keep optional fixer templates short unless the user explicitly asks for the full fixer.
6. For large implementation tasks, prefer a repo-local design or implementation-notes document so later prompts can reference a durable artifact instead of restating everything.
7. If the user asks for “the whole review prompt,” provide that prompt in one response, but do not also include all implementation prompts in the same response.

**Part 1 header template:**

```text
This is Part 1 of 3. I am splitting the workflow to avoid truncation.
Part 1 contains: corrected request analysis, execution order, Prompt 0, and Prompt 1.
Part 2 will contain: remaining implementation prompts and validation commands.
Part 3 will contain: GPT-5.5 line-by-line + architecture review and optional fixer template.
```

**Continuation footer template:**

```text
End of Part 1. Say “continue” for Part 2.
```

**Do not do this:**
- Do not provide a giant response that trails off mid-prompt.
- Do not say “Prompt 3 continues...” inside a code block.
- Do not omit the GPT-5.5 review prompt for code changes just because the response is long; split into another part instead.
- Do not use a multi-part sequence to defer analysis. Part 1 must still include the corrected workflow and the first usable prompt.

**Recovery prompt pattern for partial generation:**

```text
TASK: Recovery / completion for partially executed prompt sequence.
TASK TYPE: Inspection first, then minimal completion.

SITUATION:
A prior prompt may have been partially copied or partially executed. Inspect repo state first.

PHASE 0 — CURRENT STATE, NO EDITS:
- Check target files, endpoints, tests, docs, and validation state.
- Report what is already complete and what remains.

STOP CONDITION:
If everything is already complete, do not edit. Run validation and report.

IMPLEMENTATION:
Only complete missing pieces. Do not duplicate endpoints, tests, docs, or fixtures.
```

---

## §4 — Model Selection & Quota Management

### 4.1 Current Default Policy

To conserve Codex limits:

| Work | Model |
|---|---|
| Discovery, planning, diagnostics, doc reports | GPT-5.3 |
| Implementation prompts | GPT-5.3 |
| Fixer prompts | GPT-5.3 |
| Mandatory post-code review | GPT-5.5 |
| Code-change line-by-line review | GPT-5.5 |
| Exceptionally risky pre-code gate | GPT-5.5 only if explicitly justified |

### 4.2 Quota Strategy

| Quota state | Strategy |
|---|---|
| >50% | Use full workflow, but still avoid broad vague prompts |
| 20–50% | Use GPT-5.3 for all non-review work; split tasks tightly |
| <20% | Stop broad exploration. Use only small diagnostics or final reviews. Avoid new feature implementation. |

### 4.3 Biggest Quota Savers

1. Convert vague tasks into scoped Prompt 0/1/2 flows.
2. Avoid reruns by adding invariant tables before implementation.
3. Read exact files, not whole repos.
4. Use line-by-line review only after code changes.
5. For frontend, run build only; user runs Playwright separately unless live stack is confirmed.

### 4.4 Model Echo Rule

When model identity matters:

```text
/model gpt-5.5
Echo the current model name in the first line of output.
```

---

## §5 — Source of Truth & Design Docs

### 5.1 Authority Rule

Implementation overrides design docs.

| Source | Role |
|---|---|
| Live code | Current implementation truth |
| Live tests | Current verified behavior |
| `CLAUDE.md` | Repo rules and coding constraints |
| Design docs | Intent, terminology, rationale, historical decisions |
| Diagnostic reports | Evidence summary, not executable truth |

If docs and code conflict:

1. Do not silently change code to match docs.
2. Label it as `CODE-DOC CONFLICT` or `DOC INTENT ONLY`.
3. Ask for or encode an explicit implementation decision.
4. Implement only the requested decision, not broad doc reconciliation.

### 5.2 Design Doc Placement

Preferred structure:

```text
graph-attention-engine-v50/docs/design/gae_design_v10_8.md
graph-attention-engine-v50/docs/design/math_synopsis_v15.md
gen-ai-roi-demo-v4-v50/backend/docs/design/soc_copilot_design_v5_8.md
gen-ai-roi-demo-v4-v50/backend/design_issues_v1.md
```

`design_issues_v1.md` should be a short decision index, not a pasted architecture doc.

### 5.3 Diagnostic Classification Labels

Use these when reconciling docs and code:

| Label | Meaning |
|---|---|
| `IMPLEMENTED` | Code implements the behavior |
| `DOC INTENT ONLY` | Docs say it, code does not implement it |
| `CODE-DOC CONFLICT` | Docs and implementation disagree |
| `UNKNOWN` | Evidence insufficient |
| `FUTURE DECISION` | Needs human/product/architecture choice |

---

## §6 — Code-Change Review Requirements

### 6.1 Mandatory Post-Implementation Review

For any code added or changed, final review must use GPT-5.5 and must include **both**:

1. **Line-by-line review** of changed/new code.
2. **Architecture/system-integrity review** of whether the change preserved the intended architecture.

```text
TASK: Mandatory line-by-line + architecture review of <feature/fix>.
TASK TYPE: Review-only. NO EDITS.
MODEL: GPT-5.5.

Review every changed/new function line by line.
Also review whether the implementation broke architecture:
- duplicated abstractions/helpers/stores/routers;
- hidden state or reset leaks;
- GraphStore / DecisionStore / EvidenceLedger bypass;
- formula/gate/display mismatch;
- framework drift;
- fixture-only paths where live data should be used;
- preset/factory bypass;
- frontend/backend contract drift.

Cite file:line evidence for each finding.
Classify P1/P2/P3.
```

### 6.2 Line-by-Line Review Checklist

- Changed files are exactly allowed files.
- No unrelated source/test/config changes.
- Every new function reviewed line by line.
- Edge cases tested.
- Test assertions are meaningful, not weakened.
- Old behavior remnants searched.
- Downstream contracts checked.
- Validation logs reported.
- Residual risks explicit.

### 6.3 Architecture/System-Integrity Checklist

Use this in every post-implementation review.

| Area | Required checks |
|---|---|
| Abstraction consistency | Reuses canonical helper/store/router/factory; no private inline subclass unless explicitly intended |
| State/reset integrity | New mutable state registers with reset/state_manager; demo reset clears caches, ledgers, policies, buffers |
| Graph/store integrity | Persistence uses GraphStore/DecisionStore; optional protocol additions remain backward-compatible; SQLite/InMemory/AGE paths consistent |
| Formula/gate consistency | UI/display formulas match enforced gates; override_rate, learning_rate, penalty_ratio kept distinct |
| Framework drift | S2P/SOC/SDK file drift is intentional and covered by known-drift tests |
| Fixture/live-data | Fixture paths are labeled, cached, and not mistaken for production/live data |
| Duplication | Shared helpers are reused; no duplicate invoice/JSON loading or duplicate router logic |
| Preset/factory alignment | Uses PRESET_REGISTRY/from_preset/canonical factories rather than special-casing one copilot |
| Test architecture | Tests prove architecture path, reset, persistence, compatibility, and canonical routes |

### 6.4 Architecture Findings Classification

Architecture problems can be P1/P2 even when all local tests pass.

Examples:
- P1: safety/score path can emit NaN/inf or bypasses final gate.
- P2: new app-state memory replaces GraphStore/DecisionStore and breaks reset/demo integrity.
- P2: displayed conservation formula differs from enforced conservation gate.
- P2: adding a required member to a runtime Protocol breaks structural third-party implementations.
- P3: fixture-backed path remains but is labeled and acceptable short-term.

### 6.5 Fixer Rule

Use a fixer only for concrete P1/P2 findings.

```text
/model gpt-5.3
TASK: Targeted fixer for <finding>.
BUG TO FIX: <paste exact P1/P2 with file:line evidence>

Rules:
- minimal edits only
- implicated files only
- do not weaken tests
- preserve architecture invariants
- run targeted tests and required suite/build
- report scope and residual risks
```

---

## §7 — Frontend / Playwright Rules

### 7.1 Default Frontend Verification

For frontend code changes Codex must run:

```powershell
cd "C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\kaggle_experiments\claude_projects\gen-ai-roi-demo-v4-v50\frontend"; npm run build
```

Codex must **not** run Playwright unless the user confirms the full live stack is running.

### 7.2 Live Stack Required for Playwright

Codex may create and run Playwright only if the user confirms:

- AGE/PostgreSQL+AGE on WSL2, port `5433`
- SOC backend `uvicorn`, port `8001`
- SOC frontend Vite, port `5173`

If not confirmed:

- Codex may create `.spec.ts` files.
- Codex must run `npm run build`.
- Codex reports the user-run Playwright command.

### 7.3 Existing E2E Patterns

- File location: `frontend/tests/e2e/<name>.spec.ts`
- Import: `import { test, expect } from '@playwright/test';`
- Tabs are plain buttons; use text click patterns such as `page.getByText('Alert Triage').click()` unless existing specs use another selector.
- API tests may use `page.request.get('/api/...')` or existing `BACKEND` constant pattern.
- Use `Array.isArray()` before `.length` on API responses.
- Use `safeKey(id, index)` style in React lists; avoid bare `key={item.id}` if IDs may be missing/duplicated.
- Do not call forbidden demo reset/seed endpoints unless the specific test already owns that behavior.

### 7.4 Frontend API Safety

Before implementing UI against backend:

1. Read actual Pydantic response models.
2. Read backend `to_dict()` methods.
3. Match TypeScript interfaces to actual JSON.
4. Use existing API URL pattern; do not invent new `BACKEND`/absolute/relative style.
5. Apply `ensureArray()` before `.map()` or rendering API list fields.
6. Expected failures should use `console.debug`, not `console.error`, when existing app pattern treats them as non-blocking.

---

## §8 — Backend / AGE / API Rules

### 8.1 Pydantic Response Models

Frontend-consumed FastAPI endpoints must declare `response_model`.

- List fields must be `list[X]`, not optional lists.
- Response shape must match frontend TypeScript.
- Unsupported domain or invalid request should return explicit 4xx, not silent 200 unless the contract says otherwise.

### 8.2 AGE Query Safety

For AGE/PostgreSQL Cypher, do not blindly use Neo4j syntax.

Avoid:

- named `$params`
- `datetime()`
- `duration()`
- `CASE WHEN`
- `MERGE`
- `ON CREATE` / `ON MATCH`
- `toFloat()`
- `labels(...)`
- array properties unless encoded as JSON strings

Prefer:

- inline sanitized literals via `_S()` for strings
- integer epoch timestamps
- separate queries + Python merge instead of unsupported Cypher constructs
- tests that inspect generated Cypher for forbidden patterns

### 8.3 Production Clock Rule

For graph-driven windows, use graph timestamps, not host wall-clock.

Example from FEATURE-07:

- derive `as_of_epoch_ms` from max graph `timestamp_epoch`
- compute 7-day/30-day windows from graph clock
- do not use `datetime.utcnow()` or `time.time()` for discovery windows
- use wall-clock only for cache TTL and generated timestamps

Add tests that fail if host wall-clock is used.

### 8.4 Cache / Stale Fallback Rule

If a service has a useful stale cache:

- refresh failure should return stale cache with `stale=true` where the design requires graceful degradation
- graph-clock failure should not overwrite useful stale data with empty envelopes
- cache expiry tests should control time via `time_fn` or direct cache time manipulation; do not sleep

---

## §9 — Bug Hunt Operating Procedure

### 9.1 Structure

1. Prompt 0: gate + repo/file proof + sentinel searches.
2. Section prompts by topic to prevent capacity/context failures.
3. Each prompt reads full relevant blocks/functions.
4. Findings use exact format: P1 / P2 / P3 / race / missing guard / coverage gap.
5. Final consistency check verifies all sections addressed.

### 9.2 Bug Hunt Skeleton

```text
/model gpt-5.3
ADVERSARIAL BUG HUNT — <title> (REVIEW ONLY)

GUARDRAILS:
- Review only. No edits. No patches. No git.
- Read full relevant blocks/functions, not just grep hits.
- No evidence, no claim.
- Every finding cites file:line.
- Do NOT propose fixes unless asked.

STOP CONDITION:
- If >=3 P1 findings confirmed, finish current subsection, then stop.

OUTPUT FORMAT:
P1 BUGS:
P2 BUGS:
P3 ISSUES:
RACE CONDITIONS:
MISSING GUARDS:
COVERAGE GAPS:
READING LOG:
```

### 9.3 Proven Hunt Sections

| Section | Catches |
|---|---|
| Import/dependency contracts | Missing or stale cross-repo imports |
| Serialization/data integrity | Shape mismatches, NaN propagation, pickle/checkpoint compat |
| Security surface | Auth bypass, path traversal, injection |
| Dead code/stale refs | Retired imports, unreachable functions |
| Cross-repo consistency | GAE/SOC/ci-platform contract drift |
| Frontend/backend API drift | URL composition, response shape, Pydantic/TS mismatch |
| Race/concurrency | Lock ordering, async/thread interaction |
| Startup/config order | Cold start, initialization sequence |
| Defaults/spec drift | Configurable defaults not asserted by tests |

### 9.4 Depth Ledger

Require:

```text
READING LOG:
- file path: line ranges read
```

Downgrade any claim without evidence to `unverified`.

---

## §10 — Invariant Tables Before Difficult Code

For hard changes, Prompt 0 should include semantic invariant tables and the Prompt Verification Pass from §3.9.

Use especially for:

- lifecycle/state machines
- cache/stale behavior
- concurrency/locking
- graph query pipelines
- frontend/backend contract changes
- normalization/math changes
- audit ledger/evidence chain changes

Example invariant table request:

```text
Before coding, produce invariant tables for:
1. State lifecycle: states, transitions, forbidden transitions.
2. Error/fallback behavior: no cache, fresh cache, stale cache, refresh success/failure.
3. Boundary values: exact thresholds and inclusive/exclusive semantics.
4. Query safety: forbidden patterns and required relationship directions.
5. Tests: which test fails for each invariant violation.
```

Lessons from recent work:

- A full passing suite can still miss a spec-default bug.
- A tactical fixer can overfit unless the invariant is explicit.
- For state lifecycle bugs, distinguish “current update reinforced” from “ever reinforced.”
- For cache systems, stale fallback must be tested for every failure mode that can occur before refresh.

---

## §11 — Verification Commands

### 11.1 SOC Backend

```powershell
cd "C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\kaggle_experiments\claude_projects\gen-ai-roi-demo-v4-v50\backend"; python -m pytest tests/ -q
```

### 11.2 GAE

```powershell
cd "C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\kaggle_experiments\claude_projects\graph-attention-engine-v50"; python -m pytest tests/ -q
```

### 11.3 Frontend Build

```powershell
cd "C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\kaggle_experiments\claude_projects\gen-ai-roi-demo-v4-v50\frontend"; npm run build
```

### 11.4 User-Run Playwright

Only after live stack is up:

```powershell
cd "C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\kaggle_experiments\claude_projects\gen-ai-roi-demo-v4-v50\frontend"
npx playwright test --reporter=list
```

Targeted feature spec example:

```powershell
cd "C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\kaggle_experiments\claude_projects\gen-ai-roi-demo-v4-v50\frontend"
npx playwright test tests/e2e/feature_discovery.spec.ts --reporter=list
```

### 11.5 Multi-Repo Verification

Run only when the task spans repos or contracts:

```powershell
cd "C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\kaggle_experiments\claude_projects\graph-attention-engine-v50"; python -m pytest tests/ -q
cd "C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\kaggle_experiments\claude_projects\ci-platform"; python -m pytest tests/ -q
cd "C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\kaggle_experiments\claude_projects\gen-ai-roi-demo-v4-v50\backend"; python -m pytest tests/ -q
cd "C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\kaggle_experiments\claude_projects\s2p-copilot\backend"; python -m pytest tests/ -q
cd "C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\kaggle_experiments\claude_projects\copilot-sdk"; python -m pytest tests/ -q
```

Do not hardcode old pass-count gates unless refreshed from the current repo. Report actual pass counts.

---

## §12 — Quick Templates

### A. Prompt 0 Gate

```text
/model gpt-5.3
Echo the current model name in the first line of output.

TASK: Gate and plan for <task>.
TASK TYPE: No edits.

WORKING DIRECTORY:
C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\kaggle_experiments\claude_projects

RULES:
- Do NOT use git.
- Do NOT modify files.
- Read CLAUDE.md first.
- Prove target paths exist.
- Resolve uncertain paths.
- Output READY / NOT READY.

OUTPUT:
READY:
FILES VERIFIED:
PLAN:
RISKS:
```

### B. Implementation Prompt

```text
/model gpt-5.3
Echo the current model name in the first line of output.

TASK: Implement <feature/fix>.
TASK TYPE: Coding. Minimal edits only.

ALLOWED FILES:
- <file1>
- <file2>

FORBIDDEN:
- git
- unrelated files
- test weakening

VALIDATION:
<exact commands>

OUTPUT:
READY:
FILES CHANGED:
TESTS RUN:
SELF-REVIEW:
RESIDUAL RISKS:
```

### C. Mandatory Code Review

```text
/model gpt-5.5
Echo the current model name in the first line of output.

TASK: Mandatory line-by-line review of <changed code>.
TASK TYPE: Review-only. NO EDITS.

Read changed files fully. Cite file:line evidence.
Classify P1/P2/P3.

OUTPUT:
REVIEW VERDICT:
P1 BUGS:
P2 BUGS:
P3 ISSUES:
SCOPE AUDIT:
TEST AUDIT:
FIXER NEEDED:
```

### D. Diagnostic Report

```text
/model gpt-5.3
TASK: Diagnostic evidence pass for <topic>.
TASK TYPE: Read-only. NO EDITS.

Then:
/model gpt-5.3
TASK: Write <REPORT>.md only.
ONLY allowed write: <REPORT>.md.
```

### E. Targeted Fixer

```text
/model gpt-5.3
TASK: Targeted fixer for <P1/P2>.
BUG TO FIX:
<paste exact finding with file:line>

Rules:
- minimal edits only
- implicated files only
- add/update focused test
- run validation
```

### F. Mandatory Review with Architecture Audit

```text
/model gpt-5.5
Echo the current model name in the first line of output.

TASK: Mandatory line-by-line + architecture review of <changed code>.
TASK TYPE: Review-only. NO EDITS.

RULES:
- Do NOT use git.
- Do NOT modify files.
- Read changed files fully.
- No evidence, no claim.
- Cite file:line evidence.
- Classify P1/P2/P3.

REVIEW AREAS:
1. Line-by-line correctness.
2. Scope and test quality.
3. Validation logs.
4. Architecture/system-integrity:
   - abstraction consistency
   - state/reset integrity
   - graph/store integrity
   - formula/gate consistency
   - framework drift
   - fixture/live-data
   - duplication
   - preset/factory alignment
   - test architecture

OUTPUT:
REVIEW_VERDICT:
P1_BUGS:
P2_BUGS:
P3_ISSUES:
LINE_BY_LINE_REVIEW_NOTES:
SCOPE_AUDIT:
TEST_AUDIT:
VALIDATION_AUDIT:
ARCHITECTURE_AUDIT:
FIXER_NEEDED:
```



### G. Multi-Part `process_request:` Response Header

Use when the answer would be too long for one ChatGPT response.

```text
This is Part <N> of <TOTAL>. I am splitting the Codex workflow to avoid truncation.

This part contains:
- <items included>

Remaining parts:
- Part <N+1>: <items>
- Part <N+2>: <items>

Execution note:
Do not run later prompts until the previous prompt returns READY: YES, unless the previous prompt explicitly says READY: NO and provides a scope-repair path.
```

### H. Recovery Prompt for Partial / Truncated Prompt Execution

Use when the user copied a partial prompt or a previous ChatGPT response was truncated.

```text
/model gpt-5.3
Echo the current model name in the first line of output.

TASK: Recovery and completion for partially executed <feature/task> prompt.
TASK TYPE: Inspect first. Then minimal completion only if needed.

RULES:
- Do NOT use git.
- Do NOT assume the repo is clean.
- Do NOT duplicate work already completed.
- First inspect target files, tests, docs, endpoints, and validation state.
- If everything is complete, run validation and report READY: YES.
- If work remains, complete only missing pieces inside the allowed scope.

PHASE 0 — CURRENT STATE, NO EDITS:
- List target files and whether each expected change is present.
- List tests/docs already created.
- List validations already passing/failing if logs are available.
- Identify missing work.

STOP CONDITION:
If no missing work remains, do not edit.

OUTPUT:
READY:
CURRENT_STATE:
MISSING_WORK:
FILES_CHANGED:
TESTS_RUN:
RESIDUAL_RISKS:
```

---

## §13 — Standing Rules

1. Restate repo + task type + scope before prompts.
2. Read `CLAUDE.md` first.
3. No git unless explicitly authorized.
4. No evidence, no claim.
5. Read full functions/blocks, not just grep hits.
6. Use exact file paths and line evidence.
7. Use GPT-5.3 for most work; GPT-5.5 for post-code reviews.
8. Model echo when audit trail matters.
9. Prompt 0 before implementation unless task is tiny and safe.
10. Mandatory line-by-line review after code changes.
11. For frontend: build yes, Playwright no unless live stack confirmed.
12. For docs vs code: implementation overrides docs; conflicts must be labelled.
13. For API endpoints consumed by frontend: Pydantic response model required.
14. For API arrays in frontend: `ensureArray()` before `.map()` or rendering.
15. For graph clock/window logic: use graph timestamps, not host wall-clock.
16. For cache: stale fallback must not overwrite useful stale data.
17. For AGE queries: inspect generated Cypher for forbidden patterns.
18. For difficult state/math changes: require invariant table before coding.
19. For diagnostics: only allowed doc write, no fixes.
20. If Codex output is confusing or finds a major bug, create a targeted fixer prompt rather than broad rerun.
21. Before sending prompts for non-trivial tasks, run a prompt verification pass and revise the prompts for missing assumptions, side effects, old-behavior equivalence, and tests.
22. For high-risk integration prompts, include “How could this prompt create a fixer?” and convert each identified risk into a discovery check, constraint, or regression test.
23. Every code-change GPT-5.5 review must include both line-by-line code review and architecture/system-integrity review.
24. A code-level PASS is not enough if the architecture audit fails. Architecture failures can require a targeted fixer even when tests pass.
25. For very large `process_request:` outputs, split the response into labelled parts rather than risking truncation. Each part must contain complete prompts only.
26. Prefer self-contained prompts for implementation/fixers; use repo-local documents for architecture, design, review, diagnostics, or multi-step planning that later prompts must reuse.
27. If a prompt sequence was partially generated or partially executed, create a recovery prompt that inspects current repo state first and completes only missing work.

---

## §14 — Session Startup Checklist

Every new session:

1. ☐ Restate task in one sentence.
2. ☐ Classify task type.
3. ☐ Confirm repo(s) and exact base path.
4. ☐ Choose model by quota policy.
5. ☐ Run Prompt 0 gate/discovery.
6. ☐ For coding, implement smallest safe patch.
7. ☐ Run required tests/build.
8. ☐ Run GPT-5.5 line-by-line review for code changes.
9. ☐ Use targeted fixer only for P1/P2.
10. ☐ Report user-run commands for any Playwright/manual step.
11. ☐ If the prompt sequence is large, split ChatGPT output into labelled parts and keep every prompt complete.
12. ☐ If recovering from a partial prompt, inspect repo state first before continuing.


---

## §15 — Recent Case Studies / Starting Points

Use these as concrete anchors when a new session starts. They capture what worked, what failed, and which prompt pattern to reuse.

### 15.1 FEATURE-07 Backend — Cross-Graph Discovery

**Scenario:** Implemented backend service + router + tests for `/api/discoveries?domain=soc`, with four algorithms: Shared Entity, Pattern Convergence, Temporal Velocity, and Cross-Factor Anomaly.

**What went right:**
- Prompt 0/0B/0C forced source evidence before implementation.
- The graph-clock issue was caught before coding: seeded March 2025 data would have disappeared if the service used host wall-clock from 2026.
- Invariant tables prevented ambiguous cache/router/severity behavior.

**Critical lessons:**
- Use **Production Graph Clock** for graph-window logic: derive `as_of_epoch_ms` from max graph `timestamp_epoch`, not `datetime.utcnow()` or `time.time()`.
- Exact severity thresholds must be pinned before coding: `>=0.7 high`, `>=0.4 medium`, otherwise low.
- Shared Entity window must be enforced after parsing aligned alert/category/timestamp lists.
- AGE queries need explicit safety checks: no `$param`, `datetime()`, `duration()`, `CASE WHEN`, `MERGE`, `toFloat()`, `labels()`, or `AS count` alias.
- Frontend-facing FastAPI routes require Pydantic `response_model` declarations.
- Stale cache fallback must not be overwritten by an empty envelope when graph-clock lookup fails.

**Reusable prompt pattern:**
1. Prompt 0 — source/relationship/AGE/query evidence.
2. Prompt 0B — adversarial plan review.
3. Prompt 0C — plan repair if review finds blockers.
4. Prompt 1 — implementation with deltas embedded.
5. Prompt 2 — GPT-5.5 line-by-line review.
6. Prompt 3 — targeted fixer only for P1/P2.

**Minimum tests to demand:**
- Graph-clock/no-wall-clock test.
- Exact severity boundary tests.
- Query safety tests inspecting generated Cypher.
- Stale-cache-on-graph-clock-failure test.
- Unsupported domain returns 400.
- Pydantic response models present for frontend-consumed endpoints.

### 15.2 FEATURE-07 Frontend — Discovery Banner in Tab 3

**Scenario:** Wire shipped discovery backend into Alert Triage / Tab 3 with a full-width banner above the main grid, plus E2E spec creation.

**What went right:**
- Prompt required reading actual backend Pydantic models and `Discovery.to_dict()` before TypeScript interfaces.
- Codex was told not to guess URL style; it had to follow existing Vite/API patterns.
- Playwright was explicitly not run because the live stack had not been confirmed.

**Critical lessons:**
- Read `AlertTriageTab.tsx` fully before inserting anything. Large React files often have subtle layout/state assumptions.
- Banner must be placed **between header and grid**, not inside the grid.
- Do not add parent tab state unless the existing pattern demands it; prefer a self-fetching, non-blocking child component.
- Use `ensureArray()` before `.map()` or rendering any API-derived array.
- Use `console.debug` for expected non-blocking failures, not `console.error`, if existing app convention treats missing optional services as normal.
- Codex creates E2E specs and runs `npm run build`; user runs Playwright manually unless full live stack is confirmed.

**Reusable prompt pattern:**
1. Prompt 0 — read backend models, parent tab, App lifecycle, Vite proxy, API helpers, E2E patterns.
2. Prompt 1 — implement component + integration + spec; run build only.
3. Prompt 2 — GPT-5.5 review if code was changed.
4. Prompt 3 — targeted fixer only for P1/P2.

**User-run Playwright example:**

```powershell
cd "C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\kaggle_experiments\claude_projects\gen-ai-roi-demo-v4-v50\frontend"
npx playwright test tests/e2e/feature_discovery.spec.ts --reporter=list
```

### 15.3 Diagnostic Reports — 404 Source + Discovery Performance

**Scenario:** Investigate two unknowns before fixing: browser-level 404 during `deep_flows.spec.ts`, and 30-second timeout for discovery E2E.

**Key rule:** When a request says “read-only” but asks to produce a report, interpret as:
- no source/test/config behavior changes;
- the only allowed write is the named diagnostic Markdown file.

**Critical lessons:**
- Separate evidence pass from report writing.
- For 404s, enumerate every possible source: Vite proxy, static resources, App-level requests, Tab mount requests, backend router behavior, and external service ports.
- For performance, analyze each algorithm’s query count, loops, JSON parsing, vectorization, and first-request startup/cache behavior.
- Do not implement timing logs or fixes inside the diagnostic prompt.

**Reusable prompt pattern:**
1. Prompt 0 — evidence pass, no edits.
2. Prompt 1 — write only `DIAGNOSTIC_REPORT.md`.
3. Prompt 2 — review diagnostic report, no edits.

### 15.4 D-04 / D-08 Multi-Repo Diagnostics

**Scenario:** Diagnose D-04 “OLS CUSUM reset on GREEN” and D-08 “always normalize DK weights” across SOC and GAE repos.

**What changed midstream:**
The missing `design_issues_v1.md` was later added as a decision index, and broader design docs were placed under repo `docs/design/` directories. Those docs help, but may lag implementation.

**Critical authority rule:**
- Implementation and live tests are current truth.
- Design docs provide intent, terminology, and rationale.
- If code and docs conflict, label as `CODE-DOC CONFLICT` or `DOC INTENT ONLY`; do not silently rewrite code to match docs.

**Concrete findings from this session:**
- D-04: Current implementation did not show GREEN-triggered OLS/CUSUM reset. Reset semantics remained a future decision: accumulator only, alarm state, red-day counter, replay/dashboard epoch, or combination.
- D-08: DK normalization issue was more concrete: some sigma paths normalized, while direct weights / learned weights / accessor paths could expose or use unnormalized weights.
- Recommended implementation sequence: implement D-08 first if normalization formula/accessor semantics are clear; implement D-04 second after reset semantics are explicitly chosen.

**Reusable prompt pattern:**
1. Prompt 0 — multi-repo evidence pass.
2. Prompt 1 — write diagnostic report only.
3. Prompt 2 — review diagnostic report.
4. If design docs are added later, run Prompt 0R/1R/2R refresh with implementation-overrides rule.

### 15.5 State Lifecycle Fixer Trap — Reinforced vs Ever-Reinforced

**Scenario:** A GAE fixer solved one test failure by protecting dimensions with `reinforcement_count > 0`, but review found a P2: “reinforced in current update” and “ever reinforced” were conflated.

**Critical lesson:**
For lifecycle/state bugs, require a semantic invariant table before implementation. The table must distinguish:
- current transition event;
- persistent state;
- provisional vs established state;
- prune eligibility now vs later;
- tests that fail for naive overfit fixes.

**Prompt requirement to reuse:**

```text
Before coding, produce a lifecycle invariant table:
- state names
- transition triggers
- forbidden transitions
- current-update-only protections
- persistent protections
- prune/delete eligibility
- test proving a naive fix fails
```

### 15.6 Evidence Ledger / Concurrency Reviews

**Scenario:** Concurrent EvidenceLedger appends needed review for `chain_index` / `prev_hash` safety across library and SOC audit layers.

**Critical lessons:**
- Lock must be acquired before reading previous entry.
- Lock must be held through seal and append.
- Async and thread locks must not create false confidence if separate paths mutate the same state.
- Tests should force interleavings, not merely call append twice.

**Reusable review checklist:**
- read/compute/append atomicity;
- lock scope;
- sync vs async interaction;
- duplicate index prevention;
- hash-chain continuity;
- exception path lock release;
- persistence/reload consistency.

### 15.7 Session Restart Minimum Context

When starting a new Codex session, include this minimum context if relevant:

```text
Workspace:
C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\kaggle_experiments\claude_projects

Current repos:
- gen-ai-roi-demo-v4-v50
- graph-attention-engine-v50
- ci-platform
- s2p-copilot
- copilot-sdk

Default model policy:
- GPT-5.3 for discovery, planning, diagnostics, implementation, and fixers.
- GPT-5.5 only for mandatory line-by-line reviews after code changes/additions.

Standing constraints:
- No git unless explicitly authorized.
- Read CLAUDE.md first.
- Prompt 0 before implementation.
- Self-contained prompts; do not rely on attachments.
- Implementation overrides design docs.
- Frontend: run npm build; do not run Playwright unless live stack is confirmed.
```


---

## §16 — Recent Session Addendum: AgentEvolver, CX3, TAB7-GOV

These case studies came from the May 2026 AgentEvolver and governance sessions. They refine the base workflow above.

### 16.1 AgentEvolver Runtime Loop — Holistic Review Before Declaring Done

**Scenario:** AE-01 through AE-04 plus follow-on fixes shipped across multiple prompts: VariantGenerator/Registry, EvolutionLedger, ShadowRunner, PromotionGate, domain-agnostic shadow actions, summary endpoint, drift rule, warm-start, and coverage-gap rule.

**What worked:** individual feature reviews caught local issues.  
**What was missing:** a holistic cross-module review was needed to catch lifecycle bugs that no single module review found.

**Holistic review must inspect:**
- event lifecycle: `VARIANT_CREATED -> SHADOW_STARTED -> SHADOW_RESULT -> PROMOTION_APPROVED/REJECTED -> ROLLBACK`;
- graph-context evidence propagation;
- registry state transitions;
- shadow buffer lifecycle;
- promotion gate invariants;
- rollback handler reachability;
- reset state across every AE module;
- P16 separation: AE must not mutate ProfileScorer/centroids/DK/Level 1 state.

**Concrete findings that justified holistic review:**
- Promotion gate had `MIN_SHADOW_BATCHES = 3`, but variance could pass with fewer than three batches because std returned `0.0`. The correct fix is a separate batch-count gate that returns `continue` until enough independent batches exist.
- Shadow buffer skipped stale verified entries for missing/non-shadow variants without pruning them, so flush could repeatedly trigger on stale entries.
- Rollback sync handler could silently drop work if fired without a running asyncio loop; handler registration needs a loop-aware dispatcher or explicit logged failure.

**Reusable holistic review prompt requirements:**
- file-by-file read of all core modules and tests;
- cross-module interaction map;
- mutable state/reset table;
- event type consistency matrix;
- AGE query safety table;
- promotion truth table;
- test coverage matrix;
- design intent alignment table.

### 16.2 CX3 Decision Timestamp Spread — Repo-Local Design Plan + 5.5 Review + Implementation

**Scenario:** Evidence Room audit trail showed 4,860 zero-day Decisions with identical `timestamp_epoch`. The audit rebuild preserved timestamps correctly; the source graph data was wrong.

**Correct workflow:**
1. GPT-5.3 investigates and writes `docs/implementation_plans/cx3_decision_timestamp_spread_architecture.md` inside the repo.
2. GPT-5.5 reviews and updates that plan in the repo.
3. GPT-5.3 implements only from the approved plan.
4. GPT-5.5 performs mandatory line-by-line review.

**Key lessons:**
- Do not rely on ChatGPT sandbox files for Codex. Codex needs repo-local docs.
- Design should explicitly decide source-seed fix vs existing-graph repair.
- For graph repair, default to dry-run and require explicit `--apply`.
- Preserve nodes and edges; property-only repair is safer than destructive reseed.
- Historical synthetic timestamps are safer than `now - 90 days` because AE-DRIFT uses wall-clock windows.
- Every apply query must include `origin='zero_day_synthetic'` guard.

**Implementation plan requirements for repair scripts:**
- default dry-run;
- explicit apply;
- idempotency guard (`unique_ts` and span days);
- no `MERGE`, no `$params`, no deletes;
- deterministic timestamp generation;
- `verified_at_epoch` remains historical and after `timestamp_epoch`;
- tests for deterministic spread, query safety, idempotency, and AE-DRIFT non-false-fire.

### 16.3 TAB7-GOV Conservation Status — Complete Downstream Impact Analysis

**Scenario:** Evidence Room conservation showed GREEN via an IKS fallback while governance report sections showed RED because they called `LearningHealthMonitor.evaluate()` directly. Same tab, same state, conflicting health story.

**Important pattern:** When fixing a producer’s status semantics, map every downstream consumer before implementation.

**Required design expansion:**
- complete consumer map for `LearningHealthMonitor.evaluate()`;
- scripts such as `scripts/collect_tab_content.py`;
- CI contract tests such as `test_tab_content.py`;
- backend services such as `balance_sheet.py`, `executive_narrative.py`, `simulation.py`, `triage.py`;
- Pydantic response models;
- frontend helpers and E2E tests;
- PDF/export surfaces.

**Decision pattern:** Choose a single source of truth for status semantics. Avoid consumer-specific fallbacks unless explicitly defense-in-depth.

**Questions every status-semantics design must answer:**
- Should the producer return `CALIBRATING`, `PRE_ACTIVATION`, or `GREEN + metadata`?
- Does the frontend already handle the proposed value?
- Does the governance report need governance-specific mapping/copy?
- Should executive narrative display operational knowledge status separately from conservation/learning status?
- Which tests and sanity scripts must change?

### 16.4 SEED-FIX v2 — Scope Repair After Discovery Disproves the Premise

**Scenario:** The first seed-fix assumption was “seed AGE Decision rows to make conservation GREEN.” Prompt 0 proved that `LearningHealthMonitor.evaluate()` derived alpha/q/V from in-memory learning history, not AGE rows. AGE seeding fixes counts/audit/category/timestamp realism, but not conservation product directly.

**Correct response:** create a scope-repair implementation prompt, not a normal fixer.

**Repaired scope:**
- fix AGE verified Decision seed data;
- add tightly gated Evidence Room conservation fallback;
- add cross-tab sanity checks;
- defer evolution event seeding because `record_evolution_event()` stamped current time.

**Lesson:** Discovery may split a single “root cause” into separate fixes. Codex prompts must reflect the revised architecture rather than repeating an invalid premise.

### 16.5 Frontend Status Indicators — Data-Driven UI with Lazy Health Data

**Scenario:** RuntimeEvolutionTab had hardcoded green “Learning active” status in two places while the backend status could be GREEN/AMBER/RED/CALIBRATING.

**Fix pattern:**
- read status source and loading behavior first;
- preserve lazy loading;
- no new API call;
- no new state;
- null-safe fallback for locations outside the loaded-data guard;
- frontend build required;
- Playwright only if live stack is confirmed.

**Reusable status mapping checklist:**
- `GREEN -> green / Learning active`;
- `AMBER -> amber / Learning paused`;
- `RED -> red / Learning paused`;
- `CALIBRATING -> blue / Calibrating`;
- null fallback depends on context and must be explicit.

### 16.6 Discovery Output Semantics: `READY: YES` + `DO NOT EDIT FILES`

This is not contradictory. It means the read-only discovery/design prompt completed successfully and the next prompt can implement. The `DO NOT EDIT FILES` instruction applies to the discovery prompt itself.

When Codex returns `READY: YES` from Prompt 0:
- read the findings;
- incorporate any concrete file/line discoveries into Prompt 1;
- do not rerun Prompt 0 unless findings are incomplete.

When Codex returns `READY: NO`:
- inspect whether the original premise was disproven;
- generate a scope-repair prompt;
- do not force implementation.

### 16.7 Pattern: Plan Review Before Implementation

For high-risk graph/runtime changes, use this four-prompt chain:

```text
1. GPT-5.3 creates/updates repo-local design plan.
2. GPT-5.5 reviews and updates the plan.
3. GPT-5.3 implements from the approved plan.
4. GPT-5.5 line-by-line reviews code changes.
```

This pattern is especially appropriate when the implementation can mutate graph data, change semantic status values, affect runtime state machines, or cross multiple tabs/endpoints.


### 16.8 RL Phase 4 — Prompt Verification Prevents Fixer Churn

**Scenario:** RL Phase 4 introduced reward, exploration, eta modulation, posterior update, and chain credit behind feature flags in `triage.py`.

**What happened:** A first fixer correctly moved referral finalization before side effects so exploration could not leak to audit/Sentinel/DecisionMade before referral veto. But the prompt did not explicitly require old referral-count equivalence. Because referral now ran before the Decision node was created, `sequence_count` and `cross_category_count` excluded the current alert. R2/R7 referral behavior changed even with RL flags off.

**Root cause:** The implementation prompt protected the new safety invariant but under-specified the old behavior invariant.

**Prompt lesson:** High-risk integration prompts must include both:
- new safety invariant tests; and
- old behavior equivalence tests.

**Required pattern for similar prompts:**

```text
OLD BEHAVIOR EQUIVALENCE:
With all new feature flags false, prove the old behavior is unchanged for:
- referral rule inputs and thresholds;
- persisted Decision node properties;
- audit/external/event side effects;
- LearningState/binary q;
- reset behavior.

SIDE-EFFECT ORDERING:
No audit/external/event side effect may be emitted before the final action is known.

HOW COULD THIS PROMPT CREATE A FIXER?
List old-behavior risks and turn each into a test before implementation.
```

**Concrete test examples to demand:**
- threshold-minus-one count plus current alert should still trigger the same referral rule;
- referral-vetoed exploration must store final action as `refer_to_analyst` in the primary Decision creation query;
- with exploration flag false, no exploration metadata is written behaviorally, not merely by source-string inspection;
- successful eta modulation changes update magnitude and restores all eta fields.

**Rule:** For any prompt that reorders runtime steps, require an explicit “old inputs vs adjusted inputs” table:
`old source -> new source -> equivalence adjustment -> test`.



### 16.9 Architecture Audit Addendum — Line-by-Line Review Is Not Enough

**Scenario:** A later architecture review found problems that a local code review would not reliably catch:
- GraphStore fragmentation and private inline graph-store subclasses;
- reset/demo integrity gaps where RL state or caches survive reset;
- scoring validation returning `inf` and risking NaN softmax;
- conservation display formula diverging from the enforced gate formula;
- S2P framework drift and duplicate invoice loaders;
- DataOps AE tab backed by fixture reads instead of live AE infrastructure;
- S2P missing PRESET_REGISTRY alignment.

**Key lesson:** Every post-code review must answer two different questions:
1. Is the local implementation correct line by line?
2. Does the implementation preserve the architecture and system invariants?

**Required prompt change:** All GPT-5.5 code reviews must include an `ARCHITECTURE_AUDIT` block covering abstraction consistency, state/reset integrity, GraphStore/DecisionStore usage, formula/gate consistency, framework drift, fixture/live-data status, duplication, preset/factory alignment, and architecture-level test coverage.

**Reusable review conclusion pattern:**
```text
Line-by-line verdict: PASS.
Architecture verdict: FAIL_NEEDS_FIXER.
Reason: implementation works locally but introduced duplicated state / bypassed GraphStore / mismatched displayed formula / broke reset integrity.
```

**Rule:** Do not close a feature merely because the targeted tests pass. Close it only when both the line-by-line review and the architecture audit pass.




### 16.10 Large Prompt Sequences — Multi-Part Responses and Recovery Prompts

**Scenario:** Some `process_request:` outputs became so long that ChatGPT responses were truncated or a later prompt was only partially produced. The user copied the partial prompt before realizing it was incomplete.

**Correct workflow:** Split long prompt sequences proactively.

**Recommended sequence for large tasks:**
1. Part 1 — corrected request analysis, execution order, Prompt 0, and first implementation/design prompt.
2. Part 2 — remaining implementation/design prompts and validation commands.
3. Part 3 — GPT-5.5 line-by-line + architecture review prompt and optional targeted fixer template.

**Critical lessons:**
- A partially generated Codex prompt is dangerous because Codex may act on incomplete scope, incomplete validation, or missing forbidden-file rules.
- The solution is not to make every prompt shorter at the cost of missing safeguards. The solution is to split ChatGPT responses while keeping each Codex prompt complete.
- The GPT-5.5 review prompt is often long and should usually be its own part.
- If the user already ran a partial prompt, the next prompt must be a recovery/completion prompt, not a blind rerun.

**Recovery prompt must:**
- inspect current repo state first;
- identify which endpoints/files/tests/docs are already complete;
- avoid duplicating work;
- complete only missing pieces;
- run validation;
- honestly report residual risks.

**Reusable decision rule:**
If the answer would include more than two long code blocks or more than one full implementation prompt plus a full review prompt, split it.

---

## §17 — Updated Quick Prompts from Recent Sessions

### 17.1 Repo-Local Architecture Plan Prompt Skeleton

```text
/model gpt-5.3
TASK: <topic> — investigate and write architecture plan.
TASK TYPE: Architecture investigation + design document only. DO NOT implement.

ALLOWED WRITE:
- docs/implementation_plans/<topic>.md

RULES:
- Do NOT modify source or tests.
- Read CLAUDE.md first.
- No evidence, no claim.
- Every factual finding cites file:line evidence.
- The plan must be self-contained for later implementation.

OUTPUT DOCUMENT SECTIONS:
1. Executive Summary
2. Source / Current Behavior
3. Dependency Assessment
4. Design Options
5. Recommended Architecture
6. Detailed Implementation Plan
7. Manual Commands
8. Test Plan
9. Open Questions / Blockers
10. Reading Log

OUTPUT AFTER WRITING:
READY_FOR_IMPLEMENTATION: YES/NO
PLAN_FILE:
BLOCKERS:
```

### 17.2 GPT-5.5 Plan Review Prompt Skeleton

```text
/model gpt-5.5
TASK: Review and update <topic> architecture plan before implementation.
TASK TYPE: Architecture review + documentation update only. NO SOURCE/TEST EDITS.

ALLOWED WRITE:
- docs/implementation_plans/<topic>.md

RULES:
- Read source files cited by the plan.
- No evidence, no claim.
- Update the plan in-place if corrections are needed.
- Output IMPLEMENTATION_GO: YES/NO.
```

### 17.3 Implement-from-Plan Prompt Skeleton

```text
/model gpt-5.3
TASK: Implement <topic> from approved plan.
TASK TYPE: Coding. Minimal scoped implementation.

READ FIRST:
- docs/implementation_plans/<topic>.md
- CLAUDE.md

RULES:
- Implement exactly from the approved plan.
- Do not broaden scope.
- Use allowed files only.
- Run targeted and regression tests.
- Report manual commands separately.
```


### 17.4 Multi-Part Response Skeleton

```text
PART 1 OF 3 — Analysis + Prompt 0 + Prompt 1

I am splitting this workflow to avoid response truncation.
This part includes:
- corrected request interpretation;
- repo/path/scope assumptions;
- execution order;
- Prompt 0;
- Prompt 1.

Remaining:
- Part 2: Prompt 2 / Prompt 3 and validation commands.
- Part 3: GPT-5.5 review prompt and optional fixer template.
```

### 17.5 Partial-Prompt Recovery Skeleton

```text
/model gpt-5.3
Echo the current model name in the first line of output.

TASK: Recovery / completion for partially generated or partially executed <task> prompt.
TASK TYPE: Inspect first; minimal completion if needed.

RULES:
- Do NOT use git.
- Do NOT duplicate already completed work.
- Do NOT assume the prior partial prompt completed cleanly.
- Inspect target files, tests, docs, and validation state first.
- Complete only missing items inside the original allowed scope.

PHASE 0 — NO EDITS:
- Verify expected files.
- Verify expected endpoints/functions/classes.
- Verify expected tests/docs.
- Verify validation state if possible.

STOP CONDITION:
If all expected work exists and validation passes, do not edit.

OUTPUT:
READY:
CURRENT_STATE:
MISSING_WORK:
FILES_CHANGED:
TESTS_RUN:
RESIDUAL_RISKS:
```

---

*Codex CLI Playbook v4.5 · May 25, 2026*  
*Task classify → Prompt verification → split response if needed → Prompt 0 gate or repo-local design plan → implement/document → verify → GPT-5.5 review → targeted fixer only when needed.*

---

# ══════════════════════════════════════════════════════════
# OPERATIONAL REFERENCES (from main Session Continuation docs)
# ══════════════════════════════════════════════════════════

## Platform State (June 12, 2026)

| Repo | Tag | Tests | Status |
|---|---|---|---|
| CI | **v0.7.4-ci** | 555 passed, 0 failed | ✅ |
| SDK | **v0.7.5** | ~1,209 passed, 0 failed | ✅ |
| S2P | **v0.7.2-s2p** | 1,043 passed, 0 failed | ✅ |
| SOC | **v5.89** | ~1,742 passed | ✅ |
| GAE | v0.7.25 | 1,237 passed | ✅ unchanged |
| **Total** | | **~5,786+** | **0 failures** |

## Copilot Ports & Tensors

| Copilot | Backend | Frontend | Tensor (current) | Tensor (target) |
|---|---|---|---|---|
| SOC | 8001 | 5173 | (6,4,6)=144 | — |
| S2P | 8002 | 5177 | (5,5,7)=175 | (5,5,8)=200 Phase 4 |
| Trading | 8010 | 5174 | **(5,4,10)=200** | — (LIVE) |
| Purchasing | 8020 | 5175 | (5,4,6)=120 | **(5,4,7)=140** |
| DataOps | 8030 | 5176 | (6,5,6)=180 | — |
| PostgreSQL+AGE | 5433 | — | | |

**Trading tensor drift:** Codex built (5,4,10) with all 10 factors during P20-P27 batch. MAP still said (5,3,6). See map_v5154_correction_delta.md for 3 DROPs (P48, P51, P54) + pre-checks for Purchasing/DataOps/S2P tensors.

## Tab Content Reference (Demo Contract)

| Copilot | Port | Tabs |
|---|---|---|
| Trading | 5174 | Dashboard, Log Trade, Analysis, Performance |
| Purchasing | 5175 | Dashboard, Order, Analysis, Inventory, Performance |
| DataOps | 5176 | Dashboard, Triage, Insight, Evidence, Curve |
| S2P | 5177 | Dashboard, Exception Triage, Insight, Evidence, Suppliers, Performance |
| SOC | 5173 | SOC Analytics, Runtime Evolution, Alert Triage, Compounding, Executive Narrative, S2P Preview, Evidence Room |

**Key endpoints (curl to verify):** `/api/health`, `/api/fingerprint`, `/api/trajectory`, `/api/conservation/status`, `/api/self/accuracy-by-category`

**Verification rule:** Frontend changes → click through tabs. Endpoint changes → curl. "Tab content is the demo contract."

## Test Verification Commands

```powershell
cd "$env:CLAUDE_SDK"
python -m pytest tests/ -q --timeout=120                          # SDK root: ~1,209
python -m pytest apps/trading/backend/tests/ -q --timeout=120     # Trading: 727
python -m pytest apps/purchasing/backend/tests/ -q --timeout=120  # Purchasing: 168
python -m pytest apps/dataops/backend/tests/ -q --timeout=120     # DataOps: 176

cd "$env:CLAUDE_S2P\backend"
python -m pytest tests/ -q --timeout=120                          # S2P: 1,043

cd "$env:CLAUDE_CI"
python -m pytest tests/ -q --timeout=120                          # ci-platform: 555

cd "$env:CLAUDE_GAE"
python -m pytest tests/ -q --timeout=120                          # GAE: 1,237
```

## §WSL2-AGE — Quick Reference

**After every reboot (admin PowerShell):** `Start-AGE`
**Verify:** `python demo.py --status` → AGE/PostgreSQL UP ✓
**Key:** Mirrored WSL2. `localhost` for DSN, `127.0.0.1` for HTTP (Rule #40).

**Env vars:**
```
GRAPH_BACKEND  = age
GRAPH_DSN      = host=localhost port=5433 dbname=postgres user=postgres password=postgres
DATABASE_URL   = postgresql://postgres:postgres@localhost:5433/soc_copilot
AGE_GRAPH_NAME = soc_graph
```

## Standing Rules (Key Subset for Codex Sessions)

| # | Rule |
|---|---|
| 38 | WSL2 interactive session open before AGE work. |
| 40 | `localhost` for DSN, `127.0.0.1` for HTTP. Mirrored WSL2. |
| 48 | Persist-before-cache for L5 writes. |
| 50 | All Cypher uses AGE two-step pattern. MERGE forbidden. |
| 58 | No raw sqlite3 outside migration module. |
| 59 | AGE smoke gates at tier boundaries (non-blocking). |
| 60 | AGE read-side: `normalize_agtype_value()`. Write-side: `serialize_for_age()`. |
| 61 | Shadow scorer: `from_preset()` rejects `primary_store is shadow_store`. |
| 62 | Migration source of truth: home DB (`~/.ci-platform/<domain>/`). |

## Document Versions

| Document | Version |
|---|---|
| MAP | **v5.154** |
| MAP correction delta | **v5.154** (applied) |
| CI blog | **v14** |
| Claims registry | **v7** |
| Math synopsis | **v17** |
| GAE design | **v10.10** |
| DataOps design | **v1.6** |
| cga_arxiv | **v7.5** — **STILL NOT SUBMITTED** |

## Blog Posts (Dakshineshwari.net)

| # | Blog | URL |
|---|---|---|
| 1 | After ten thousand decisions | https://www.dakshineshwari.net/post/after-ten-thousand-decisions-show-me-how-your-system-got-smarter-v3-1 |
| 2 | Stryker/Handala Attack | https://www.dakshineshwari.net/post/compounding-intelligence-and-the-stryker-handala-attack |
| 3 | CI 4.0 Self-Improving Judgment | https://www.dakshineshwari.net/post/compounding-intelligence-4-0-how-enterprise-ai-develops-self-improving-judgment |
| 4 | CGA Math Foundation | https://www.dakshineshwari.net/post/cross-graph-attention-mathematical-foundation-with-experimental-validation |
| 5 | CISO Demo | https://www.dakshineshwari.net/post/operationalizing-context-graphs-ciso-cybersecurity-ops-agent-demo |
| 6 | Gen-AI ROI in a Box | https://www.dakshineshwari.net/post/gen-ai-roi-in-a-box |

## Forward Queue (Next Actions)

```
1. P28-P30: ✅ DONE (v0.7.2-s2p, v0.7.4, v0.7.5)
2. Remaining copilot migrations (Purchasing, DataOps, S2P — same tooling)
3. P31-P35 (written, convert to 3-stage)

4. P36+ feature queue (S2P first). 3 Trading DROPs: P48, P51, P54.
5. Trading tensor (5,4,10)=200 already LIVE. All 10 factors built.
```

---

*Codex Hero Document · June 12, 2026 · MAP v5.154*
*Session state + CLI Playbook v4.5 + operational references.*
*P28-P30 DONE. 86 migration tests. Trading (5,4,10)=200 live. 7 DROPs. SDK v0.7.5.*
*62 standing rules. ~5,786+ tests. 0 failures.*
*Next: remaining migrations → P31-P35 (3-stage) → P36+ features (3 Trading DROPs applied).*
