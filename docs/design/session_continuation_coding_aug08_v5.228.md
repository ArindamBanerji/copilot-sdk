# SOC Copilot — Session Continuation Document
**Date:** June 11, 2026 · **Authority:** MAP v5.228 (consolidated, all PD audits)
**Purpose:** Pick up coding, roadmap, or document session exactly where it left off.
**Supersedes:** session_continuation_jun8_v5150

---

## ⚠️ Critical State (Read First)

1. **5 copilots in demo.py.** Trading (8010/5174), Purchasing (8020/5175), DataOps (8030/5176), S2P (8002/5177), SOC (8001/5173).
2. **ALL REPOS COMMITTED, TAGGED, PUSHED.** GAE v0.7.25, CI v0.7.0-ci, SDK v0.7.0, S2P v0.7.0-s2p, SOC v5.87. All clean.
3. **GAE pip-installable.** `pip install git+https://github.com/ArindamBanerji/graph-attention-engine.git` works. v5.0-dev merged to main.
4. **P0-P18 through Codex.** P20-P35 WRITTEN + REVIEWED. 33 prompts total (3 DROPs).
5. **MAP v5.228: consolidated, 139 active, 57 rules.** Single source of truth. All 5 copilot PDs audited — zero gaps.
6. **Next 50 execution queue (P36-P85) produced.** Clean sequential numbering. 62 pre-investigation queries generated.
7. **demo.py fixed:** connect_timeout=5 (no more hangs), localhost (mirrored WSL2).
8. **no_graph fixture added:** DataOps test isolation from GRAPH_BACKEND=age env var. 7 tests patched.
9. **Rule #40 UPDATED:** Use `localhost` (mirrored WSL2 mode), not `127.0.0.1`.
10. **Infrastructure is LAST.** All copilot features → quality/bugs → infra → Loom → Docker/VPS.

---

## Platform State (June 11, 2026)

| Repo | Tests | Tag | Branch | Status |
|---|---|---|---|---|
| GAE | **1,237** | **v0.7.25** | main (merged from v5.0-dev) | ✅ pip-installable |
| ci-platform | **350** (+11 skip) | **v0.7.0-ci** | main | ✅ pip-installable |
| SDK root | **915** | **v0.7.0** | main | ✅ |
| Trading BE | **727** | v0.7.0 | main | ✅ |
| Purchasing BE | **168** | v0.7.0 | main | ✅ |
| DataOps BE | **176** | v0.7.0 | main | ✅ |
| S2P BE | **926** | **v0.7.0-s2p** | main | ✅ |
| SOC BE | **~1,742** | **v5.87** | v5.0-dev | ✅ |
| **Total** | **~6,241** | | | **0 failures** |

### pip install (public repos)

```bash
pip install git+https://github.com/ArindamBanerji/graph-attention-engine.git
pip install git+https://github.com/ArindamBanerji/ci-platform.git
```

---

## What Was Done (June 5-8, 2026)

### Prompts Written (P28-P35) — June 5

8 prompts, 3,249 lines, 91 unit tests, 15 PW tests. All reviewed with 5 corrections applied.

### MAP v5.144 → v5.150 — June 5

74 new items (#135-#208) from 5 copilot PD audits. Consolidated into single document.

### Forward Queue P36-P85 — June 5

50 items across 8 tiers. 62 pre-investigation queries across 8 groups with 5 context summaries.

### Git Update — June 6

All 5 repos committed, tagged, pushed. .gitignore updated (SDK: 20 lines added, filtering ~150 scan artifacts).

### Infrastructure Fixes — June 8

| Fix | What | Impact |
|---|---|---|
| demo.py connect_timeout | `psycopg.connect(dsn, connect_timeout=5)` | `--status` no longer hangs |
| demo.py localhost | All connections use `localhost` not `127.0.0.1` | Mirrored WSL2 works |
| no_graph fixture | conftest.py + 7 test patches in DataOps | Tests isolated from profile env vars |
| PowerShell profile | `GRAPH_DSN` → `host=localhost` | Consistent with mirrored WSL2 |
| Rule #40 updated | `localhost` for mirrored WSL2 | Standing rule corrected |

---

## Copilot Ports & Tensors

| Copilot | Backend | Frontend | Tensor (current) | Tensor (target) | Accent |
|---|---|---|---|---|---|
| SOC | 8001 | 5173 | (6,4,6)=144 | — | Blue |
| S2P | 8002 | 5177 | (5,5,7)=175 | (5,5,8)=200 Phase 4 | Amber |
| Trading | 8010 | 5174 | (5,3,6)=90 | **(5,4,7)=140** #150 | Red |
| Purchasing | 8020 | 5175 | (5,4,6)=120 | **(5,4,7)=140** #179 | Green |
| DataOps | 8030 | 5176 | (6,5,6)=180 | — | Purple |
| PostgreSQL+AGE | 5433 | — | | | |

---

## MAP v5.228 Summary

### Copilot Completeness — All Zero Gaps

| Copilot | PD | Tracked | Gaps |
|---|---|---|---|
| SOC | v5.8 | ~49 | **0** |
| S2P | v1.3 unified | 26 | **0** |
| DataOps | v1.6 | 13 | **0** |
| Trading | v1.0 | 27 | **0** |
| Purchasing | v1.3 | 23 | **0** |

### Forward Queue (P36-P85)

```
Tier 1: S2P features        P36-P41   6 items
Tier 2: DI + cross-copilot  P42-P47   6 items
Tier 3: Trading Phase 0     P48-P53   6 items
Tier 4: Trading Phase 1     P54-P63  10 items
Tier 5: Purchasing Product   P64-P75  12 items
Tier 6: Quality/Bugs        P76-P77   2 items
Tier 7: Infrastructure      P78-P80   3 items
Tier 8: Trading Phase 1.1   P81-P85   5 items
```

### Post-P85: 39 long-term + 9 demo tier + 2 Docker/VPS LAST

---

## Prompt Status

| Range | Status | Count |
|---|---|---|
| P0 | ✅ SHIPPED | 1 |
| P1-P18 | Through Codex (P5+P13 dropped) | 16 |
| P20-P27 | WRITTEN (L5 nodes) | 8 |
| P28-P35 | WRITTEN + REVIEWED | 8 |
| **Total written** | | **33 (30 active + 3 DROPs)** |
| P36-P85 | TO WRITE (queries generated) | 50 |

---

## Standing Rules (57)

Rules 1-39 from prior sessions. Key updates:

| # | Rule |
|---|---|
| 40 | **Use `localhost` for DSN (AGE/PostgreSQL), `127.0.0.1` for HTTP (backend APIs). Mirrored WSL2.|
| 45 | Plan before implementation for enhancement prompts. |
| 46 | Trading DB: delete trading.db on preset shape change. |
| 47 | Domain-prefixed aliases are convention, not requirement. |
| 48 | Trading is execution-quality domain, NOT directional. |
| 49 | copilot_sdk/rl/ is complete but unwired. Wire via from_preset() injection. |
| 50-55 | (From v5.144: outbox replay, managed by AGE, etc.) |
| 56 | **Trading penalty_ratio = 3.0** (PD v1.0 authoritative). |
| 57 | **Kitchen language mandatory for Purchasing UI.** |

---

## Canonical Values

| What | Value |
|---|---|
| Trading tensor (current → target) | (5,3,6)=90 → **(5,4,7)=140** |
| Purchasing tensor (current → target) | (5,4,6)=120 → **(5,4,7)=140** |
| DataOps tensor | (6,5,6)=180 |
| S2P tensor | (5,5,7)=175 |
| SOC tensor | (6,4,6)=144 |
| Trading penalty_ratio | **3.0** |
| Purchasing penalty_ratio | 3.0 |
| DataOps penalty_ratio | 10.0 |
| S2P penalty_ratio | 5.0 |
| SOC penalty_ratio | 20.0 |
| η_confirm / η_override | 0.05 / 0.01 |
| τ | 0.1 |
| q window | 400 |
| θ_min | 23.53/(α×V) |

---

## SOC Tab Names (7 tabs)

| # | Display Label | Component |
|---|---|---|
| 1 | SOC Analytics | AnalyticsTab |
| 2 | Runtime Evolution | RuntimeEvolutionTab |
| 3 | Alert Triage | AlertTriageTab |
| 4 | Compounding | CompoundingTab |
| 5 | Executive Narrative | NarrativeTab |
| 6 | S2P Preview | S2PPreviewTab |
| 7 | Evidence Room | GovernanceTab |

---

## Test Verification Guide

### Per-Repo Commands

```powershell
cd "$env:CLAUDE_SDK"
python -m pytest tests/ -q --timeout=120                          # 915
python -m pytest apps/trading/backend/tests/ -q --timeout=120     # 727
python -m pytest apps/purchasing/backend/tests/ -q --timeout=120  # 168
python -m pytest apps/dataops/backend/tests/ -q --timeout=120     # 176

cd "$env:CLAUDE_S2P\backend"
python -m pytest tests/ -q --timeout=120                          # 926

cd "$env:CLAUDE_CI"
python -m pytest tests/ -q --timeout=120                          # 350

cd "$env:CLAUDE_GAE"
python -m pytest tests/ -q --timeout=120                          # 1,237
```

### Architectural Checks

```powershell
cd "$env:CLAUDE_SDK"
Select-String -Path apps\*\backend\app\main.py -Pattern "_StoreProxy" -Recurse
Select-String -Path copilot_sdk\backend\conservation_router.py -Pattern "DecisionStore"
Select-String -Path apps\*\backend\app\main.py -Pattern "self_computation" -Recurse
```

---

## Session Startup Checklist

```
1. Read this session continuation document
2. Read MAP v5.228 (map_v5150.md) — 139 active, 57 rules
3. Read next 50 queue (next_50_coding_queue.md) — P36-P85
4. Start AGE from admin PowerShell: Start-AGE
5. Verify: python demo.py --status (AGE UP ✓)
6. Check git status (all should be clean):
   cd "$env:CLAUDE_SDK"; git status; git log --oneline -1
   cd "$env:CLAUDE_S2P"; git status; git log --oneline -1
   cd "$env:CLAUDE_CI"; git status; git log --oneline -1
7. Run baseline tests if counts look wrong
8. Check P20-P35 Codex submission status
9. Resume from next unshipped prompt
```

---

## Pending Actions

| # | Action | Status |
|---|---|---|
| 1 | Send P20-P35 to Codex | PENDING |
| 2 | Run p36_p85 pre-investigation queries | PENDING |
| 3 | Write prompts P36-P85 from query results | PENDING |
| 4 | Resolve Welford conflict (Decision 3 vs C2) | PENDING |
| 5 | Manual fix BUG-006 + BUG-010 | PENDING |
| 6 | Commit demo.py fix + no_graph fixture | **READY** |

---

## §WSL2-AGE — Quick Reference

**After every reboot (admin PowerShell):** `Start-AGE`

**Verify:** `python demo.py --status` → AGE/PostgreSQL UP ✓

**Manual start (if Start-AGE fails):**
```
wsl -d Ubuntu-24.04 -u root
service postgresql start
# Keep terminal open (Rule #38)
```

**Key:** This machine uses **mirrored WSL2 networking**. `localhost` works. `127.0.0.1` does NOT reach WSL2. Rule #40 updated.

**Env vars (set in PowerShell profile):**
```
GRAPH_BACKEND  = age
GRAPH_DSN      = host=localhost port=5433 dbname=postgres user=postgres password=postgres
DATABASE_URL   = postgresql://postgres:postgres@localhost:5433/soc_copilot
AGE_GRAPH_NAME = soc_graph
```

---

## One-Paragraph Status — Fresh Sessions

**Coding:** ~6,241 tests, 0 failures. All 5 repos committed, tagged, pushed (GAE v0.7.25, CI v0.7.0-ci, SDK v0.7.0, S2P v0.7.0-s2p, SOC v5.87). GAE pip-installable from GitHub. P0-P18 through Codex. P20-P35 written and reviewed. 33 prompts total. MAP v5.228 consolidated: 139 active items, 57 rules, all 5 copilots zero PD gaps. Forward queue P36-P85 (50 items) with 62 pre-investigation queries. demo.py fixed (connect_timeout, localhost for mirrored WSL2). DataOps no_graph test fixture applied (7 tests). Rule #40 updated: localhost, not 127.0.0.1. **Next: send P20-P35 to Codex → run P36-P85 queries → write P36-P85 prompts.**

---

## Document Versions

| Document | Version |
|---|---|
| Master Action Plan | **v5.150** (139 active, consolidated) |
| Session Continuation | **June 8 (v5.150)** — this document |
| CI blog | **v14** |
| Claims registry | **v7** |
| Math synopsis | **v17** |
| GAE design | **v10.10** |
| DataOps design | **v1.6** |
| S2P design | **v1.3 (unified)** |
| Trading PD | **v1.0** |
| Purchasing PD | **v1.3** |
| cga_arxiv | **v7.5** — **STILL NOT SUBMITTED** |

## Blog Posts (Dakshineshwari.net)

| Priority | Blog |
|---|---|
| 1 | [After ten thousand decisions](https://www.dakshineshwari.net/post/after-ten-thousand-decisions-show-me-how-your-system-got-smarter-v3-1) |
| 2 | [Stryker/Handala Attack](https://www.dakshineshwari.net/post/compounding-intelligence-and-the-stryker-handala-attack) |
| 3 | [CI 4.0 Self-Improving Judgment](https://www.dakshineshwari.net/post/compounding-intelligence-4-0-how-enterprise-ai-develops-self-improving-judgment) |
| 4 | [CGA Math Foundation](https://www.dakshineshwari.net/post/cross-graph-attention-mathematical-foundation-with-experimental-validation) |
| 5 | [CISO Demo](https://www.dakshineshwari.net/post/operationalizing-context-graphs-ciso-cybersecurity-ops-agent-demo) |
| 6 | [Gen-AI ROI in a Box](https://www.dakshineshwari.net/post/gen-ai-roi-in-a-box) |

---

*Session Continuation · June 11, 2026 · MAP v5.228*
*~6,241 tests. 0 failures. All repos pushed.*
*GAE v0.7.25 pip-installable. 33 prompts written. 50 to write.*
*139 active items. 57 rules. All 5 copilots: zero PD gaps.*
*demo.py fixed. Rule #40: localhost (mirrored WSL2).*
*Next: P20-P35 to Codex → P36-P85 queries → write prompts.*

---

## Tab Content Reference (Demo Contract)

Before making UI/frontend/endpoint changes, verify what each tab shows:

| Copilot | Port | Tabs |
|---|---|---|
| Trading | 5174 | Dashboard, Log Trade, Analysis, Performance |
| Purchasing | 5175 | Dashboard, Order, Analysis, Inventory, Performance |
| DataOps | 5176 | Dashboard, Triage, Insight, Evidence, Curve |
| S2P | 5177 | Dashboard, Exception Triage, Insight, Evidence, Suppliers, Performance |
| SOC | 5173 | SOC Analytics, Runtime Evolution, Alert Triage, Compounding, Executive Narrative, S2P Preview, Evidence Room |

**Key endpoints (curl to verify per copilot):**
- `/api/health` — phase, alpha, engine status
- `/api/fingerprint` — IKS, profile archetype
- `/api/trajectory` — compounding curve
- `/api/conservation/status` — verified_count, q, theta_min
- `/api/self/accuracy-by-category` — per-category accuracy

**SOC is separate** (gen-ai-roi-demo-v4-v50): `cd "$env:CLAUDE_SOC" && cd backend && uvicorn app.main:app --port 8001`

**Verification rule:** Frontend changes → click through tabs in browser. Endpoint changes → curl. "Tab content is the demo contract."

---

## ⚠️ CRITICAL: WSL2/AGE Fix (June 23, 2026)

**Rule #40 REVISED.** Windows OS update broke psycopg3 SSL over WSL2 NAT.

**Before (broken):** `host=localhost` in DSN
**After (working):** `host=<WSL2 NAT IP>` + `sslmode=disable` + `ssl=off` in postgresql.conf

```powershell
# Post-reboot (admin):
wsl -u root pg_ctlcluster 17 main start

# Every session:
$wslIp = (wsl -u root hostname -I).Trim().Split()[0]
$env:GRAPH_DSN = "host=$wslIp port=5433 dbname=soc_copilot user=postgres password=postgres sslmode=disable"
```

**Pending:** Verify all 5 repos read GRAPH_DSN from env (not hardcoded localhost).
**Reference:** standing_note_wsl2_age_fix_june23.md

---

## Standing Note: Rule #40 DSN Fix — Cross-Session (June 23, 2026)

**Root cause:** Windows OS update broke psycopg3 SSL over WSL2 NAT. PG 17.

**3-layer fix applied:**
1. `ssl = off` in postgresql.conf
2. demo.py: `_resolve_wsl2_ip()` + `_build_age_dsn()` + `pg_ctlcluster 17 main start`
3. All hardcoded DSNs patched across 3 repos (8 files total)

**Files changed:**
- SOC: posterior_store.py, check_age.py, migrate_aura_to_age.py, test_posterior_store.py
- CI: age_client.py
- SDK: graph_queries.py, sqlite_to_age.py, scratch_graph.py, c9_live_age_smoke.py, verify_l5_completion.py

**Verification:** SOC 21 tests, CI 555 passed, SDK 1,859 passed. Zero bare DSNs remaining.

**For new Codex prompts:** Read `GRAPH_DSN` from env, append `sslmode=disable`, use `connect_timeout=5`.

```python
dsn = os.getenv("GRAPH_DSN", "host=localhost port=5433 dbname=soc_copilot "
                "user=postgres password=postgres sslmode=disable")
if "sslmode" not in dsn:
    dsn += " sslmode=disable"
```

**Post-reboot:** `wsl -u root pg_ctlcluster 17 main start` (admin), then set `$env:GRAPH_DSN` with WSL IP.

---

## Standing Note: WinError 64 — Python asyncio IOCP Accept Crash (August 2026)

**Root cause:** Python 3.11 on Windows defaults to `ProactorEventLoop` (IOCP). When Playwright workers rapidly open/close browser pages, the IOCP accept loop crashes with `OSError: [WinError 64] The specified network name is no longer available`. Server stays alive, port stays bound, but stops accepting connections — all subsequent browser fetches hang indefinitely.

**Why curl worked but Playwright failed:** curl = single stable connection. Playwright = rapid connection churn across workers.

**Fix:** `--loop asyncio` on all uvicorn commands forces `SelectorEventLoop` (uses `select()` instead of IOCP). Applied to ALL copilot backends in `demo.py` on Windows:

```python
if platform.system() == "Windows":
    cmd.extend(["--loop", "asyncio"])
```

**Impact:** Eliminated all WinError 64 crashes. Resolved "Loading invoice queue..." S2P Playwright failures entirely.

**For new Codex prompts:** Any prompt that starts a uvicorn server on Windows MUST include `--loop asyncio`. Pattern: `uvicorn app.main:app --port XXXX --loop asyncio`
