# Accessing Design Files via Google Drive — Session Guide

---

## Location

All design documents are at:
```
G:\My Drive\public-files\gen-ai-roi\claude_projects\design\
```

They are also mirrored to Google Drive and accessible via the
`Google Drive:search_files`, `Google Drive:read_file_content`,
and `Google Drive:download_file_content` tools.

---

## Key Files

| File | What it is | When to use |
|---|---|---|
| `dataops_copilot_design_v1_7.md` (88KB) | DataOps design spec. §1-§28 engineering, §29-§41 Data Intelligence layer. | Any DataOps feature work. §18 = self-computation, §25 = enterprise connectors, §40 = DI engineering specs. |
| `master_action_plan_v5.225.md` (65KB) | Queue of all work items across all copilots. Priority order. Standing rules. Test counts. | Check what's done, what's next, what the priorities are. |
| `session_continuation_codex_hero_jul31_v5.225.md` (96KB) | Session bootstrap document. Platform state, repo structure, test commands, verification ladders. | Starting a new session. Contains git status, test baselines, port allocations, standing rules. |
| `s2p_copilot_unified_v1_3.md` (136KB) | S2P product definition. 16 scenarios. Feature specs F1-F19. | Any S2P feature work. |
| `trading_copilot_product_definition_v1.md` (96KB) | Trading product definition. Factors, CLI, integrations. | Any Trading feature work. |
| `purchasing_copilot_pd_v1_3.md` (51KB) | Purchasing product definition. Toast POS, commodity, weather. | Any Purchasing feature work. |
| `demo_scenarios_and_usecases_v2_1.md` (61KB) | Demo storyboard. 94 scenarios. Presenter scripts. Silence beats. Kill-shot map. | Demo prep, Loom recording, outreach. |
| `math_synopsis_v18.md` (151KB) | Mathematical foundations. Conservation law, DK, centroids, IKS. | Math/theory questions. Proofs. |
| `platform_validation_plan_v2_3.md` (54KB) | 10-scan validation suite. Pre-tag checks. Architectural invariants. | Before git tags. Quality gates. |
| `next_steps_strategy_v1_23.md` (169KB) | Strategy document. Competitive rooms. Build waves. Outreach plan. | Strategic planning, positioning. |
| `ci_blog_v15.md` (76KB) | CI blog post. Re-convergence. IKS. Economics. | Publication prep. |
| `gae_design_v10_10.md` (168KB) | Graph Attention Engine design. Cross-graph attention. | GAE math/architecture. |
| `judgment_memory_v2_7.md` (58KB) | Judgment Memory design. Shadow testing. Variant promotion. | JM feature work. |

---

## How to Search

```
Google Drive:search_files with query parameter:
  title = 'dataops_copilot_design_v1_7.md'
  OR
  fullText contains 'SC-TRUST' and title contains 'design'
  OR
  title contains 'master_action_plan'
```

**Combined filters work best:**
```
title = 'dataops_copilot_design_v1_7.md' and fullText contains 'Source Profiler'
```

---

## How to Read File Content

**Step 1:** Search to get the file ID:
```
Google Drive:search_files
  query: "title = 'dataops_copilot_design_v1_7.md'"
  pageSize: 1
```

**Step 2:** Download content using the file ID:
```
Google Drive:download_file_content
  fileId: "<id from search result>"
```

The content comes as base64. Decode in bash:
```bash
echo "<base64>" | base64 -d
```

**Shortcut for code files:** Search with `fullText contains` to
find specific functions/classes without downloading the whole file.
The `contentSnippet` in search results often has enough context.

---

## How to Read Source Code

All 5 repos are mirrored to:
```
G:\My Drive\public-files\gen-ai-roi\claude_projects\
```

**Search for code files:**
```
Google Drive:search_files
  query: "title = 'TriageScreen.tsx' and fullText contains 'handleScore'"
```

**Search across files:**
```
Google Drive:search_files
  query: "fullText contains 'CompoundingScorer' and title contains '.py'"
```

**Pattern for finding implementations:**
```
title = 'api.ts' and fullText contains 'getPreviewQueue' and fullText contains 'export'
```

---

## Common Patterns

**Find a design section:**
```
Google Drive:search_files
  query: "title = 'dataops_copilot_design_v1_7.md' and fullText contains 'SC-12'"
```

**Find implementation of a feature:**
```
Google Drive:search_files
  query: "fullText contains 'AccuracyAlertsPanel' and title contains '.tsx'"
```

**Find test files:**
```
Google Drive:search_files
  query: "title contains '.spec.ts' and fullText contains 'trust-card'"
```

**Find a connector:**
```
Google Drive:search_files
  query: "title = 'celonis.py' and fullText contains 'CelonisConfig'"
```

**Check if something exists in any repo:**
```
Google Drive:search_files
  query: "fullText contains 'AcquisitionAdvisor' and title contains '.py'"
  pageSize: 5
```

---

## Important Notes

1. **Google Drive sync is not instant.** Files modified in the last
   few minutes may not be searchable yet. If a file was just changed
   by Codex, ask the user to run a local scan instead.

2. **contentSnippet in search results** often contains enough to
   answer the question without downloading the full file. Check it
   first before calling download_file_content.

3. **fullText search is case-insensitive** for content but
   **title search is case-sensitive** for exact matches.

4. **Binary files** (images, .db) appear in search but can't be
   read via download_file_content.

5. **The design directory has the LATEST versions.** The project
   knowledge files (mounted at /mnt/project/) may be older versions.
   Always prefer Google Drive for current state.

6. **Codex prompts should reference design docs** with a READ FIRST
   block telling Codex where to find the spec:
   ```
   READ FIRST:
     docs/design/dataops_copilot_design_v1_7.md (§18 Self-Computation)
   ```
   This gives Codex the design context before implementation.
