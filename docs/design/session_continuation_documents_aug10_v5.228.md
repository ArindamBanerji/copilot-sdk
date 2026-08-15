# CI Platform — Documents Session Continuation
**Date:** August 10-14, 2026 · **MAP:** v5.228 · **Session type:** Document management, versioning, and publication preparation
**Purpose:** Pick up any document session where this one left off. Contains techniques, workflow patterns, document inventory, and the complete state of every deliverable.
**Supersedes:** All prior session continuation documents for document management.

---

## ⚠️ Critical State (Read First)

1. **MAP is at v5.228** — full audit reconciliation. 109 CLOSED + 20 DROP + 6 DEFERRED = 135 resolved items. 10,536 tests. 0 failures. 78 standing rules.
2. **CI Blog v16.1 is FINALIZED** — publish-hold removed. All 5 publication blockers resolved (H-1 SOC-G1, H-2 α=coverage, S-1 copilot counts, S-2 ACCP latency, S-3 Tech-Process Fusion). All 3 verification items closed (V-1 D1-D4 drift, V-2 McKinsey, V-3 Zycus).
3. **Demo Scenarios is at v2.5** — 17 fixer edits propagated. B2 RL naming reconciled. DIFF-1/COMP-1/L-CDK propagated. Internal consistency checklist all-pass.
4. **DataOps Copilot Design is at v1.8** — Addendum A (reification) + §39F (strengthening themes / DI-PROOF).
5. **Bug Hunt is at v5** — 16 dimensions, 5 repos, 5 new dimensions (12-16) for post-AGE-unification surface.
6. **Codex Hero is at v5.226** — includes WinError 64 fix, DI demo status, 5-track forward queue.
7. **Google Drive design directory partially synced** — demo_scenarios v2.5 and bug_hunt v5 are current; MAP, DataOps, CI Blog, and Codex Hero need upload.

---

## Session Workflow Techniques (How This Session Operated)

### 1. MAP Addendum Processing Pattern

The core workflow for this session: receive a MAP addendum (inline text or uploaded file), apply it to the current MAP version, create session continuation documents, and present all three.

**Pattern:**
```
1. cp MAP v5.N → v5.(N+1)
2. sed header (version, date, supersedes)
3. Apply content (items, rules, test counts, forward queue)
4. Update footer
5. cp coding SC → new date/version
6. cp roadmap SC → new date/version
7. Update SC version refs
8. present_files (all three)
```

**Key sed techniques used:**
- Line-number insertion: `sed -i 'Na\...'` for inserting after line N
- Pattern-anchored insertion: `sed -i '/PATTERN/a\...'` for inserting after a matched pattern
- In-place replacement: `sed -i 's|old|new|'` for updating specific text
- **Pipe-delimited sed** (`s|old|new|`) avoids escaping `/` in paths
- **Bottom-up editing** when inserting at multiple points (avoids line number shifts)
- Always verify with grep -c after edits

**Gotchas discovered:**
- sed `a\` with special characters (single quotes, pipes) requires careful escaping via `'\''` for single quotes
- Pattern-anchored sed insertions can silently fail if the anchor text has special regex characters — verify with grep after every insertion
- When sed anchor text includes `*` or `(`, use fixed-string grep first to confirm the pattern exists, then construct the sed

### 2. Document Merge Pattern (Base + Addendum → New Version)

Used for DataOps v1.7→v1.8, Demo Scenarios v2.1→v2.5, Bug Hunt v4→v5, CI Blog v15→v16.1.

**Pattern:**
```
1. Read base structure (grep section headers, find insertion points)
2. Read addendum structure (identify which sections it adds/modifies)
3. Determine insertion strategy:
   - Addendum adds new sections → find boundary, insert between existing sections
   - Addendum modifies existing sections → find exact text, str_replace
   - Addendum replaces sections → truncate + rebuild
4. Build merged document
5. Update version in header + document control table
6. Verify with section count + key term grep
```

**Critical rule:** Always find insertion points BEFORE making changes. Line numbers shift with every insertion, so either work bottom-up or re-grep between edits.

### 3. Fixer Addendum Pattern (v2.4 → v2.5 demo scenarios)

A fixer addendum declares corrections in one section but those corrections need to be propagated to every place they affect. The fixer lists exact in-place edits.

**Pattern:**
```
1. Read the fixer to understand ALL affected locations
2. Apply most-urgent fixes first (on-stage-truth > structural > cosmetic)
3. For each fix: grep to find exact text → sed/str_replace → verify
4. Run the self-consistency checklist the fixer provides
5. Update document control
```

**Demo Scenarios v2.5 example:** 17 edits across 7 groups (A-G), with a self-verification checklist of 7 items. Key learning: the fixer's checklist IS the test suite — run every check.

### 4. Publication Blocker Audit Pattern (CI Blog)

Used for the CI Blog v16.1 finalization. Systematic scan for claims that are ahead of code.

**Pattern:**
```
1. Grep for every "shipped" / "proven" / "validated" / "LIVE" claim
2. Cross-reference against known code state (what's actually shipped vs designed)
3. Grep for specific numbers (counts, latencies, dollar amounts)
4. Check named competitors for factual accuracy
5. Check for contradictory registers (absolutist vs honest in same doc)
6. Classify: Hard blocker (fatal if published) / Should-fix / Already clean
7. Fix each, verify, downgrade/close
```

**V-1 D1-D4 canonical decision drift pattern:** When a document makes a definitional change (e.g., "α = category coverage not override rate"), grep EVERY occurrence of that concept throughout the document. Definitions appear in:
- Section body text
- Figure captions (often stale — different update cadence than body)
- Concrete examples (often use old numbers)
- Changelog entries (historical — leave as-is)
- Architecture reference appendix

### 5. Google Drive Sync Pattern

**Tools:** `Google Drive:search_files`, `Google Drive:create_file`, `Google Drive:read_file_content`

**Limitations discovered:**
- `textContent` parameter works for files up to ~5KB
- Larger files (60-100KB) cannot be uploaded inline through the API tool — manual sync required
- `base64Content` parameter exists but the tool truncates large payloads
- **Recommendation:** For large files, download from chat output attachments and drop into the Drive folder manually

**Search patterns that work:**
```
title = 'filename.md'                              # exact file
fullText contains 'SC-TRUST' and title contains 'design'  # content search
title contains '.py' and fullText contains 'CompoundingScorer'  # code search
```

### 6. Standing Note Pattern

Operational fixes that affect every session get appended to BOTH session continuation documents AND saved as standalone files.

**Standing notes created this session:**
- WSL2/AGE Fix (Rule #40 DSN) — `standing_note_rule40_dsn_fix_jun23.md`
- WinError 64 — Python asyncio IOCP crash fix

**Standing note content must include:**
- Root cause
- Fix applied (with code pattern to copy)
- Files changed (by repo)
- Verification results
- Pattern for new Codex prompts going forward

---

## Documents Produced / Updated This Session

### Version Progression Table

| Document | Start Version | End Version | Lines | Key Changes |
|---|---|---|---|---|
| **MAP** | v5.204 | **v5.228** | 1,175 | 24 versions. R10-R33 shipped. AGE migration. JM phases. Rules 68-78. Full audit. |
| **CI Blog** | v14 (v12 internal) | **v16.1** | 737 | 4 new sections (Left Turn, Governor, Second Derivative, Field Honestly). V-1/V-2/V-3 verified. 5 publication blockers resolved. Finalized — no DRAFT. |
| **Demo Scenarios** | v2.1 | **v2.5** | 928 | v2.2 (8 DI beats), v2.3 (DI-PROOF + arc), v2.4 (DIFF-1/COMP-1/L-CDK + B1-B4), v2.5 (17 fixer edits propagated). |
| **DataOps Design** | v1.6 | **v1.8** | 2,205 | v1.7 (Addendum A reification, §39A-E), v1.8 (§39F strengthening themes, DI-PROOF). |
| **Bug Hunt** | v4 | **v5** | 781 | 5 new dimensions (12-16). Multi-repo config. 11→16 dimensions. |
| **Codex Hero** | v5.198 | **v5.226** | 2,441 | Rebuilt from scratch at v5.224, then updated to v5.226. WinError 64. DI demo. Track ⑤. |
| **Coding SC** | v5.204 | **v5.228** | 407 | 24 versions tracked. Standing notes appended. |
| **Roadmap SC** | v5.204 | **v5.228** | 407 | 24 versions tracked. Standing notes appended. |

### New Standalone Documents Created

| File | Lines | Purpose |
|---|---|---|
| `dataops_forward_prompt_plan_v1.md` | 290 | DataOps execution plan: 8 batches, 20 prompts, ~17 weeks |
| `standing_note_rule40_dsn_fix_jun23.md` | 42 | Cross-session DSN fix reference |
| `ci_blog_v16_addendum.md` | 37 | v15→v16 addendum reference |
| `ci_blog_v16_1.md` | 737 | Finalized CI blog |

### MAP Version Progression (24 versions this session)

| Version | Date | Key Change |
|---|---|---|
| v5.205 | Jun 24 | R10-R12 (chain transfer "holy grail") |
| v5.206 | Jun 24 | R13-R15 (Purchasing v2.0) |
| v5.207 | Jun 24 | R16-R18b (ROI + multi-unit + S2P profiles) |
| v5.208 | Jun 25 | R19-R21 (S2P Layer 2-3) |
| v5.209 | Jun 25 | R22-R24 (S2P feature-complete F1-F22) |
| v5.210 | Jun 25 | R25-R27 (S2P tensor d=8, first DataOps DI) |
| v5.211 | Jun 25 | R28-R30 (DataOps DI-6/7/8) + R22-R30 recovery |
| v5.212 | Jun 27 | Full PW verification pass (826+ specs, 0 failures) |
| v5.213 | Jun 27 | R31-R33 (DataOps DI-1→DI-11 COMPLETE) |
| v5.214 | Jul 10 | Batches 27-35 forward plan v1 |
| v5.215 | Jul 11 | Batch plan v2 (27-42), 4 tracks |
| v5.216 | Jul 11 | +S14-CONTRAST in B31 |
| v5.217 | Jul 11 | +B30.5 Demo Storyboard PW |
| v5.218 | Jul 11 | +BKL-1 Purchasing PW timeout |
| v5.219 | Jul 23 | Rule #63/#64 retroactive cleanup |
| v5.220 | Jul 25 | AGE shared-graph ALL 5 COPILOTS. 33,048 nodes. Rules 68-72. |
| v5.221 | Jul 25 | JM Phases 0-5 DONE. Phase 6 pending. Rule 73. |
| v5.222 | Jul 25 | Corrections: SOC-ADAPTER-V RESOLVED. CONFIG-CONSOL 1-7. |
| v5.223 | Jul 25 | §21 AGE unification forward queue (~55d). |
| v5.224 | Jul 26 | B-ADDENDUM (P1 SOC unscoped writes) + C6-FUTURE. Rules 74-75. |
| v5.225 | Jul 31 | DataOps PD v1.7 (Addendum A reification). |
| v5.226 | Aug 2 | DataOps DI: 7 shipped, 4 in flight, 6 demo polish. Rules 76-77. |
| v5.227 | Aug 6 | JM P0 SHIPPED. NEO4J-RENAME tracked. Rule 78. |
| v5.228 | Aug 8 | FULL AUDIT. 109 CLOSED + 20 DROP + 6 DEFERRED = 135 resolved. |

---

## Platform State (August 10, 2026)

| Repo | Tag | Tests | Status |
|---|---|---|---|
| SDK root+apps | v0.7.64 | ~1,918 | ✅ |
| Trading BE | — | 1,138 | ✅ |
| Purchasing BE | — | 642 | ✅ |
| DataOps BE | — | 261 | ✅ |
| S2P BE | v0.7.17-s2p | 1,627 | ✅ |
| SOC BE | v6.3+ | 2,174 | ✅ |
| CI | v0.7.4-ci | 582 | ✅ |
| GAE | v0.7.25 | 1,237 | ✅ |
| **Backend total** | | **9,579** | **0 failures** |
| Playwright (all) | | **957** | ✅ |
| **Grand total** | | **10,536** | **0 failures** |

### Feature Completion

| Copilot | Status |
|---|---|
| SOC | ✅ Campaign v6.0 + domain scoping |
| Trading | ✅ Phase 0+1+1.1 + AgentEvolver |
| Purchasing | ✅ v1.0 + v1.1 + v2.0 |
| S2P | ✅ F1-F22 + tensor d=8 |
| DataOps | ✅ DI-1→DI-11 + 3 connectors |
| **Total** | **122 features, 27 tabs** |

### AGE Shared Graph

All 5 copilots on AGE. 33,048 Decision nodes. Domain-prefixed IDs (TRD-/PUR-/DOPS-/S2P-).

### Tensors (Runtime-Verified)

| Copilot | Tensor | Values |
|---|---|---|
| SOC | (6,4,6)=144 | 288 |
| S2P | (5,5,8)=200 | 400 |
| Trading | (5,4,10)=200 | 400 |
| Purchasing | (5,4,7)=140 | 280 |
| DataOps | (6,5,6)=180 | 360 |
| **Total** | | **1,728** |

---

## Standing Rules Summary (78 total)

Key rules from this session:
- **68:** SOC domain scoping (soc_decision_where)
- **69:** Shared graph authorization (exact pair)
- **70:** Domain-prefixed IDs
- **71:** Preview scorer isolation (InMemoryGraphStore)
- **72:** demo.py hand-edit only
- **73:** Destructive AGE test guard (TEST_DESTRUCTIVE_AGE=1)
- **74:** SOC write/count scoping (P1)
- **75:** Framework router reconciliation
- **76:** DI demo dollar amounts provenance (F-21/F-22)
- **77:** DI trust scores labeled
- **78:** No new neo4j references

---

## Standing Notes (Critical for All Sessions)

### WSL2/AGE Fix (June 23, 2026)
```powershell
# Post-reboot (admin):
wsl -u root pg_ctlcluster 17 main start

# Every session:
$wslIp = (wsl -u root hostname -I).Trim().Split()[0]
$env:GRAPH_DSN = "host=$wslIp port=5433 dbname=soc_copilot user=postgres password=postgres sslmode=disable"
```
DSN uses WSL2 NAT IP (dynamic per boot). ssl=off. PG 17. 8 files changed across 3 repos.

### WinError 64 — Python asyncio IOCP Crash
```python
if platform.system() == "Windows":
    cmd.extend(["--loop", "asyncio"])
```
Forces SelectorEventLoop. Eliminates IOCP accept crash under Playwright connection churn. Applied to ALL copilot backends in demo.py.

### For New Codex Prompts — DSN Pattern
```python
dsn = os.getenv("GRAPH_DSN", "host=localhost port=5433 dbname=soc_copilot "
                "user=postgres password=postgres sslmode=disable")
if "sslmode" not in dsn:
    dsn += " sslmode=disable"
```

---

## Forward Queue

### Demo Track (Batches 27-42)
```
Track ① GOVERNANCE:  C-GOV (DO-FIRST, 0.5-1d)
Track ② DEMO:        C-0 → C-1 → DPW → heroes → Loom → OSS
Track ③ TRADING:     C-OSS-1Q → C-TRD-SIT → C-TRD-VOL
Track ④ ARCHITECTURE: C-REGIME 63-site → EXP-REGIME
Track ⑤ DATAOPS:      SC-TRUST→SC-13 ✅. Demo polish (~5.5d). Level 5: DI-3 (~4w).
```

### AGE Unification (~55d remaining)
Phase B remaining (2d) → B-ADDENDUM P1 (2d) → Phase C S2P (10d) → Phase D (6.5d) → Phase E (5d) → C6-FUTURE (2d) → Phase 6 (10.5d)

### JM Store Program
P0 ✅ → P-1 (1d) → P1 (4-5d) → P2 (1-1.5w) → STOP

---

## Google Drive Sync Status

| File | On Drive | Current | Action |
|---|---|---|---|
| master_action_plan | v5.227 | **v5.228** | Upload |
| dataops_copilot_design | v1.7 | **v1.8** | Upload |
| ci_blog | v15 | **v16.1** | Upload |
| codex_hero SC | v5.225 | **v5.226** | Upload |
| demo_scenarios | ✅ v2.5 | v2.5 | Current |
| bug_hunt | ✅ v5 | v5 | Current |
| dataops_forward_prompt_plan | — | v1 | New — upload |
| substantiation_sprint_plan | — | v1.1 | New — upload |

---

## CI Blog v16.1 — Publication Status

**FINALIZED.** No DRAFT stamps. No publish-hold. All blockers resolved.

| Blocker | Resolution |
|---|---|
| H-1 SOC-G1 | ✅ Confirmed shipped |
| H-2 α=coverage | ✅ Confirmed in code |
| S-1 Copilot counts | ✅ Five running + seven S2P workflow-personas |
| S-2 ACCP <150ms | ✅ Relabeled P95 design target |
| S-3 Tech-Process Fusion | ✅ Moved to roadmap framing |
| V-1 D1-D4 drift | ✅ 5 instances found and fixed |
| V-2 McKinsey | ✅ SQL injection verified, contradiction removed |
| V-3 Zycus | ✅ Unverified numbers dropped, honest reframing |

---

## Key Insights and Decisions Made This Session

### 1. Document Classification
When a new document arrives (like the DataOps Forward Prompt Plan), determine its type:
- **Design doc** (what + why) → merge into parent design doc
- **Execution plan** (when + how + order) → standalone, reference from MAP
- **Session continuation** (current state) → kept current with every MAP bump
- **Standing note** (cross-session operational fix) → standalone + appended to SCs

### 2. Fixer Pattern > Feature-Tour Pattern
The demo scenarios v2.5 fixer revealed that addendum sections (§4.10, §4.11) that declare corrections but don't propagate them into primary sections create internal inconsistency. The fix: after adding new sections, explicitly propagate every change into every location it affects, then run the self-consistency checklist.

### 3. Publication Blocker Taxonomy
- **Hard blockers:** Code claims that are ahead of production (fatal)
- **Should-fix:** Countable facts a reader checks (copilot counts, latency numbers)
- **Already clean:** Properly conditioned claims (γ conditioning, simulation labels)

The priority order is often the inverse of the list order — V-3 (named competitor facts) was highest risk even though it was listed third.

### 4. Honest Competitive Register
Two competitive teardowns in contradictory registers (absolutist + honest) is worse than either alone. The fix: one honest register throughout — concede real strengths, distinguish on the specific mechanism (compounding), never strawman.

### 5. sed Insertion Failures Are Silent
When sed pattern-anchored insertions (`/PATTERN/a\...`) fail because the pattern doesn't match, there's no error — the file is simply unchanged. Always verify with grep -c after every insertion. This caught the R22-R30 gap where 9 items were missing from the MAP because earlier sed insertions silently failed.

---

## Document Versions Reference (All Documents)

| Document | Version | File |
|---|---|---|
| MAP | **v5.228** | `master_action_plan_v5.228.md` |
| CI Blog | **v16.1** | `ci_blog_v16_1.md` |
| Demo Scenarios | **v2.5** | `demo_scenarios_and_usecases_v2_5.md` |
| DataOps Design | **v1.8** | `dataops_copilot_design_v1_8.md` |
| Bug Hunt | **v5** | `bug_hunt_v5.md` |
| Codex Hero | **v5.226** | `session_continuation_codex_hero_aug02_v5.226.md` |
| DataOps Forward Plan | **v1** | `dataops_forward_prompt_plan_v1.md` |
| Substantiation Sprint | **v1.1** | `substantiation_sprint_execution_plan_v1_1.md` |
| Product Integrity | **v3.0** (on Drive) | — |
| Math Synopsis | **v18** | — |
| GAE Design | **v10.10** | — |
| JM Design | **v2.9** | — |
| S2P PD | **v1.3** | — |
| Trading PD | **v1** | — |
| Purchasing PD | **v1.3** | — |
| Validation Plan | **v2.3** | — |
| Strategy | **v1.23** | — |
| cga_arxiv | **v7.5** — **STILL NOT SUBMITTED** | — |

---

## Google Drive — Access Guide

### Location

All design documents: `G:\My Drive\public-files\gen-ai-roi\claude_projects\design\`
All 5 repos mirrored to: `G:\My Drive\public-files\gen-ai-roi\claude_projects\`

**Tools:** `Google Drive:search_files`, `Google Drive:read_file_content`, `Google Drive:download_file_content`
**Design folder parentId:** `1kMmSt0XrxPiHM-3rTm5dq5BlHWDNFc9r`

### Key Files on Drive (update versions after sync)

| File | What | When to use |
|---|---|---|
| `master_action_plan_v5.228.md` | Work queue, rules, test counts | What's done, what's next |
| `dataops_copilot_design_v1_8.md` | DataOps spec (§1-§41) | Any DataOps feature work |
| `ci_blog_v16_1.md` | CI blog post (FINALIZED) | Publication |
| `demo_scenarios_and_usecases_v2_5.md` | Demo storyboard, 94 scenarios | Demo prep, Loom |
| `session_continuation_codex_hero_aug02_v5.226.md` | Session bootstrap | Starting a new session |
| `bug_hunt_v5.md` | 16-dimension adversarial probe | Quality sweeps |
| `s2p_copilot_unified_v1_3.md` (136KB) | S2P product definition | S2P feature work |
| `trading_copilot_product_definition_v1.md` (96KB) | Trading product definition | Trading feature work |
| `purchasing_copilot_pd_v1_3.md` (51KB) | Purchasing product definition | Purchasing feature work |
| `math_synopsis_v18.md` (151KB) | Mathematical foundations | Math/theory, proofs |
| `gae_design_v10_10.md` (168KB) | Graph Attention Engine | GAE math/architecture |
| `judgment_memory_v2_9.md` (58KB) | Judgment Memory design | JM feature work |
| `platform_validation_plan_v2_3.md` (54KB) | 10-scan validation suite | Before git tags |
| `next_steps_strategy_v1_23.md` (169KB) | Strategy document | Positioning, outreach |

### Search Patterns

```
# Exact file
Google Drive:search_files  query: "title = 'dataops_copilot_design_v1_8.md'"

# Content search
Google Drive:search_files  query: "fullText contains 'SC-TRUST' and title contains 'design'"

# Combined (best results)
Google Drive:search_files  query: "title = 'dataops_copilot_design_v1_8.md' and fullText contains 'Source Profiler'"

# Code search
Google Drive:search_files  query: "fullText contains 'CompoundingScorer' and title contains '.py'"

# Find implementations
Google Drive:search_files  query: "fullText contains 'AccuracyAlertsPanel' and title contains '.tsx'"

# Find tests
Google Drive:search_files  query: "title contains '.spec.ts' and fullText contains 'trust-card'"
```

### Reading File Content

```
Step 1: Search for file ID
  Google Drive:search_files  query: "title = 'filename.md'"  pageSize: 1

Step 2: Download content
  Google Drive:download_file_content  fileId: "<id from search>"

Step 3: Content arrives as base64. Decode:
  echo "<base64>" | base64 -d
```

**Shortcut:** `contentSnippet` in search results often has enough context without downloading the full file. Check it first.

### Upload Limitations

- `textContent` parameter works for files up to ~5KB
- Files >5KB cannot be reliably uploaded inline via the API tool
- **For large files (60-100KB):** user must download from chat outputs and drop into Drive folder manually
- `create_file` with `parentId` creates files in the design directory

### Important Rules

1. **Drive sync is not instant** — recently Codex-modified files may not be searchable yet
2. **fullText search is case-insensitive** for content; **title search is case-sensitive** for exact matches
3. **Design directory has LATEST versions** — project knowledge files (mounted at /mnt/project/) may be older
4. **Binary files** appear in search but can't be read via download_file_content
5. **Codex prompts should reference design docs** with a READ FIRST block:
   ```
   READ FIRST:
     docs/design/dataops_copilot_design_v1_8.md (§18 Self-Computation)
   ```

---

*Session Continuation — Documents Session · August 10-14, 2026 · MAP v5.228*
*24 MAP versions (v5.205→v5.228). CI Blog finalized (v16.1). Demo Scenarios v2.5. DataOps v1.8. Bug Hunt v5.*
*10,536 tests. 0 failures. 78 rules. 122 features. 27 tabs. 33,048 AGE nodes.*
*All 5 publication blockers resolved. All 3 verification items closed.*
