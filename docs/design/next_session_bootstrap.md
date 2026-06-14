# Next Session Bootstrap Guide
**Purpose:** Force a new Claude session to deeply understand the CI Platform
architecture and implementation before writing any code or prompts.

---

## Part 1: Bootstrap Sequence

### Step 1 — Read These Documents (in order)

```
1. session_continuation_codex_jun11_v5_*.md  ← operational state
2. master_action_plan_v5_*.md                ← queue + rules + tensor shapes
```

### Step 2 — Run Pre-Checks (before any coding)

```powershell
# Verify tensor shapes (MAP may be stale)
cd "$env:CLAUDE_SDK"
python -c "
for mod_name, cls_name in [('trading','TradingPreset'), ('purchasing','PurchasingPreset'), ('dataops','DataOpsPreset'), ('s2p','S2PPreset')]:
    mod = __import__(f'copilot_sdk.scoring.presets.{mod_name}', fromlist=[cls_name])
    p = getattr(mod, cls_name)()
    print(f'{mod_name}: C={p.shape.n_categories} A={p.shape.n_actions} D={p.shape.n_factors} factors={p.shape.factor_names}')
"

# Verify test counts match session continuation
cd "$env:CLAUDE_SDK" && python -m pytest tests/ -q --timeout=120 2>&1 | Select-Object -Last 3
cd "$env:CLAUDE_CI" && python -m pytest tests/ -q --timeout=120 2>&1 | Select-Object -Last 3
cd "$env:CLAUDE_S2P\backend" && python -m pytest tests/ -q --timeout=120 2>&1 | Select-Object -Last 3

# Verify git tags match
foreach ($info in @(
    @{Name="CI"; Path=$env:CLAUDE_CI},
    @{Name="SDK"; Path=$env:CLAUDE_SDK},
    @{Name="S2P"; Path=$env:CLAUDE_S2P},
    @{Name="SOC"; Path=$env:CLAUDE_SOC},
    @{Name="GAE"; Path=$env:CLAUDE_GAE}
)) {
    Push-Location $info.Path
    $tag = git describe --tags --abbrev=0
    Write-Host "  $($info.Name): $tag"
    Pop-Location
}
```

### Step 3 — Understand Tab Content (Demo Contract)

```
Run the live system:
  cd "$env:CLAUDE_SDK" && python demo.py

Verify each copilot by clicking through tabs:
  Trading (5174):    Dashboard, Log Trade, Analysis, Performance
  Purchasing (5175): Dashboard, Order, Analysis, Inventory, Performance
  DataOps (5176):    Dashboard, Triage, Insight, Evidence, Curve
  S2P (5177):        Dashboard, Exception Triage, Insight, Evidence, Suppliers, Performance

Key endpoints per copilot (curl to verify):
  /api/health              — phase, alpha, engine status
  /api/fingerprint         — IKS, profile archetype
  /api/trajectory          — compounding curve data
  /api/conservation/status — verified_count, q, theta_min
  /api/self/accuracy-by-category

SOC (5173) runs separately via gen-ai-roi-demo-v4-v50.

"Tab content is the demo contract."
Frontend changes → click through tabs.
Endpoint changes → curl.
```

### Step 4 — Confirm Codex Workflow

```
GPT removed from pipeline. Opus writes 3-stage prompts directly:
  Stage 1 (gpt-5.3, read-only): Discovery + pre-checks
  Stage 2 (gpt-5.3): Implementation with adaptation instructions
  Stage 3 (gpt-5.5): Line-by-line + blast radius + architecture review

Codex venv activation (MUST use full path):
  & "C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\proj-envs\python_expts_venv\Scripts\Activate.ps1"

Standing rules: 62. Critical: #40, #58, #59, #60, #61, #62.
```

---

## Part 2: Architecture Deep-Dive Questions

**The new session MUST answer these before writing prompts or code.
Search project knowledge for each answer. If unsure, search the
codebase via Codex Stage 1 discovery.**

### Scoring & Learning

**Q1: What is the CompoundingScorer and how does it learn?**
- What does score() do? What does learn() do?
- What is the relationship between score() writing a Decision and learn() writing an Outcome?
- What is score_read_only() and when is it used instead of score()?
- How does the scorer's state change after each learn() call?

**Q2: What is the centroid tensor and why does its shape matter?**
- What do C (categories), A (actions), and D (factors) represent?
- What is the current tensor shape for each of the 5 copilots?
- Why does Trading show (5,4,10)=200 when the MAP says (5,3,6)=90?
- What happens if a decision references a category_index or action_index outside the tensor?

**Q3: What is the conservation law and how does it gate learning?**
- Write the formula: α · q · V ≥ θ_min
- What does each variable mean? (α=category coverage, q=accuracy, V=verified count)
- What is the penalty_ratio and how does it differ per copilot?
- When does conservation transition from GREEN to AMBER to RED?
- Why is conservation path-sensitive (ordering of decisions matters)?

**Q4: What is DecisionCountPolicy(200) and why does it create phase transitions?**
- What are MEAN_CONVERGENCE and VARIANCE_LEARNING phases?
- What happens at 200 decisions per category?
- Why do DK weights only appear after phase transition?
- How did P29-C's 210-decision test prove this?

### Storage & Migration

**Q5: What is the GraphStore protocol and what are its three implementations?**
- SQLiteGraphStore, InMemoryGraphStore, AGEGraphStore — when is each used?
- What does GRAPH_BACKEND env var control?
- Why does Rule #58 forbid raw sqlite3 in production code?
- How does the factory pattern select the backend?

**Q6: How does the SQLite→AGE migration work?**
- What are the 3 verification levels? (L1=count, L2=content, L3=state-vector)
- What is the scratch graph pattern and why does it exist?
- Why does the migration use direct psycopg instead of AGEClient?
- What is MATCH-then-CREATE and why not MERGE? (AGE rejects MERGE)
- What does "migrate the LOG, not the STATE" mean?
- What is normalize_agtype_value() and why is it needed on reads?

**Q7: What is the shadow scorer and what does "proven" mean?**
- How does it compare primary (SQLite) vs shadow (AGE) results?
- Why must primary_store and shadow_store be different instances?
- What is the proven_threshold and when does status revert?
- Trading showed 40/40 proven — what exactly was compared?

### Architecture & Copilots

**Q8: How are the 5 copilots structured across 5 repositories?**
- Which repos hold which copilot backends? Which hold frontends?
- How does demo.py start all 4 SDK copilots?
- Why is S2P backend in s2p-copilot but S2P frontend in copilot-sdk?
- What is FreshScorerProxy and why do apps use it?

**Q9: What is the DomainPreset and how does it configure each copilot?**
- What does TradingPreset contain? (categories, actions, factors, penalty_ratio, etc.)
- How does from_preset() create a scorer from a preset?
- What is PRESET_REGISTRY and why must every copilot register?

**Q10: What are the standing rules and which are most critical for daily work?**
- Rule #40: localhost vs 127.0.0.1 — why does mixing them cause 2s penalties?
- Rule #58: no raw sqlite3 — what's the exemption for migration?
- Rule #59: AGE smoke gates — blocking or non-blocking? For what?
- Rule #60: agtype normalization — what problem does it solve?
- Rule #62: home DB vs repo DB — which is source of truth for migration?

### Route Architecture & Performance

**Q11: What is the route architecture and why is it CLOSED?**
- What are the 4 route policy states? (CANONICAL_ONLY, SHADOW, PIPELINE_SERVED, DISABLED)
- What did A1 2000-decision scale test show? (flat through 1500, outlier at 2000)
- Why are hot-path Packages 2-5 PARKED?
- What triggers re-evaluation? (p95 > 500ms sustained at 1000+ decisions)

**Q12: What are the AGE capabilities and limitations?**
- CREATE GRAPH: supported
- DROP GRAPH: supported
- RENAME GRAPH: not supported
- MERGE: not supported (ON CREATE SET syntax error)
- What is the AGE two-step pattern for Cypher queries?
- What does serialize_for_age() do on writes?
- What does normalize_agtype_value() do on reads?

### Process & Workflow

**Q13: How does the 3-stage Codex workflow operate?**
- What does Stage 1 discover that Stage 2 needs?
- Why is Stage 2 told "adapt based on Stage 1 findings"?
- What specific things does Stage 3 review that tests don't catch?
- Give an example of a P2 bug Stage 3 found (domain-scoped idempotency, scratch retention, agtype readback)

**Q14: What is the relationship between the MAP, session continuation, and project knowledge?**
- MAP = queue + rules + tensor shapes + forward prompts
- Session continuation = operational state + what shipped + git tags
- Project knowledge = product definitions + design docs + architecture
- Which is authoritative when they conflict? (implementation > docs)

**Q15: What is the demo contract and how is it verified?**
- What does "tab content is the demo contract" mean?
- How do you verify each copilot's tabs work?
- What endpoints must return data for each tab?
- What is preseed_all_copilots.py and when must it run?
- What breaks if conservation shows 0 verified decisions?

---

## Part 3: Red Flags to Watch For

If the new session encounters any of these, STOP and investigate:

1. **Test count mismatch** — session continuation says X, actual says Y. Something shipped or broke between sessions.
2. **Tag mismatch** — expected v0.7.5, actual v0.7.4. Commit didn't land.
3. **Tensor shape mismatch** — MAP says one shape, preset says another. Codex built something the MAP didn't track.
4. **DIRTY repo** — unexpected modified files beyond .db artifacts.
5. **P30 Stage 2 results pending** — may have Codex output to review.
6. **AGE not running** — `Test-NetConnection localhost -Port 5433` fails. Run `wsl -u root service postgresql start`.
7. **import errors** — `pip install -e .` may need re-running after cross-repo changes.
