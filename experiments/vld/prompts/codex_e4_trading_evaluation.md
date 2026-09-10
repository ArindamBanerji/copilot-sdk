# ═══════════════════════════════════════════════════════════════
# CODEX E-4: Trading Stage 1 Multi-Hop Evaluation
# Repo: copilot-sdk
# Model: gpt-5.6-terra (measurement script, no app changes)
# PARALLEL-SAFE: scripts/ and data/ only, no app/ changes
# ═══════════════════════════════════════════════════════════════

```
/model gpt-5.6-terra
/reasoning high

# ═══ REQUIRED READING ═══
#
# 1. Trading Stage 1 data (YOUR INPUT — 40 instances):
#    copilot-sdk/apps/trading/backend/data/trading_multihop_stage1.json
#    Read _header, provenance, and at least 5 scenarios across all
#    3 branching kinds.
#
# 2. Trading schema extensions:
#    copilot-sdk/apps/trading/backend/data/trading_multihop_schema_extensions.json
#
# 3. Trading domain config:
#    copilot-sdk/apps/trading/backend/app/ — search for categories,
#    actions, factors, presets. You need:
#    - Categories (5): thesis_check, portfolio_exposure, time_pattern,
#      fundamental_change, correlation_risk
#    - Actions (5): execute, defer, reduce_size, hedge, reject
#    - Factors (6): thesis_alignment, portfolio_concentration,
#      timing_signal, fundamental_strength, correlation_risk, liquidity_risk
#
# 4. DataOps evaluator (REFERENCE — follow this pattern):
#    copilot-sdk/apps/dataops/backend/scripts/evaluate_multihop_stage1.py
#    This is the working reference. Match its ScenarioGraphStore,
#    4-arm structure, and report format.

# ═══ CONTEXT ═══
#
# SOC and DataOps Stage 1 evaluations confirmed: VLD=100% at ρ≥0.70
# on score_keyed conditional scenarios. This evaluation tests whether
# Trading produces the same result.
#
# IMPORTANT LESSONS FROM PRIOR EVALUATIONS:
#
# 1. Content_rule on score_keyed uses correct_branches directly — it's
#    an ORACLE, not a fair comparator. THE HONEST COMPARISON for
#    score_keyed is VLD vs BREADTH. Report both but headline VLD vs breadth.
#
# 2. S2P evaluation FAILED (VLD=0.562 at ρ≥0.70). Root cause: centroid
#    sparsity. Trading has 40 instances with 35 non-flat. Centroids are
#    built PER-ACTION (not per category×action), so 35/5 = 7 instances
#    per action cell — adequate for centroid means.
#    CENTROID INIT IS CRITICAL. Use enriched centroids (REQ-1 from
#    recurrence addendum). If a cell has < 3 instances, use
#    domain-reasonable defaults spread across [0.2, 0.8] with seed=42.
#
# 3. Chance for 5 actions = 1/5 = 0.20. ρ=0.50 controls must be near
#    0.20 ± 0.15.
#
# POSITIVE CONTROL: planted scenarios.
# SCRIPTS-ONLY task. No app/ code changes.

# ═══ PRE-CHECKS (ALL MANDATORY — halt if any fail) ═══

echo "=== PRE-CHECK 1: Trading backend baseline ==="
cd $CLAUDE_SDK
python -m pytest apps/trading/backend/tests/ -q --timeout=120 2>&1 | Select-Object -Last 5
# Record the EXACT count. If any failures → HALT.

echo "=== PRE-CHECK 2: SDK root baseline ==="
python -m pytest tests/ -q --timeout=120 2>&1 | Select-Object -Last 5
# Expected: 3372+ passed.

echo "=== PRE-CHECK 3: Stage 1 validator ==="
python apps/trading/backend/scripts/validate_stage1.py
# Must output: "ALL 10 QUALITY CHECKS + SPEC CONSTRAINTS PASSED"
# If FAIL → HALT. Do not proceed with invalid data.

echo "=== PRE-CHECK 4: Data integrity ==="
python -c "
import json, collections

# Load and inspect
d = json.load(open('apps/trading/backend/data/trading_multihop_stage1.json'))
S = d['scenarios']
print(f'Instances: {len(S)}')
assert len(S) == 40, f'Expected 40, got {len(S)}'

# Provenance check (DataOps blocker)
assert 'provenance' in d, 'MISSING provenance field — will fail provenance tests'
print(f'Provenance: {d[\"provenance\"]}')

# Branching kind distribution
kinds = collections.Counter(x['branching_kind'] for x in S)
print(f'Kinds: {dict(kinds)}')

# ρ distribution on score_keyed
rhos = collections.Counter(x['rho_planted'] for x in S if x['branching_kind'] == 'score_keyed')
print(f'Score-keyed ρ: {dict(sorted(rhos.items()))}')

# Action distribution
actions = collections.Counter(x['decision_tree']['ground_truth_action'] for x in S)
print(f'Actions: {dict(actions)}')
n_actions = len(actions)
print(f'Action count: {n_actions} (chance = {1/n_actions:.3f})')

# Flat controls
flat = sum(1 for x in S if x.get('surface_only_resolvable'))
print(f'Flat controls: {flat}')

# Factor name verification
sample = S[0]['alert']['surface_factors']
expected = {'thesis_alignment','portfolio_concentration','timing_signal',
            'fundamental_strength','correlation_risk','liquidity_risk'}
actual = set(sample.keys())
if actual != expected:
    print(f'WARNING: factor mismatch. Expected: {sorted(expected)}, Got: {sorted(actual)}')
    # Don't halt — factors may have different names in the generated data
    # but the evaluator builds centroids from whatever factors exist
else:
    print(f'Factor names: OK ({len(actual)} factors)')

# Scenario ID uniqueness
ids = [x['scenario_id'] for x in S]
assert len(ids) == len(set(ids)), 'Duplicate scenario_ids found!'
print(f'Scenario IDs: all unique')

# Cell coverage estimate
cells = collections.Counter(
    (x['decision_tree'].get('ground_truth_action', 'unknown'))
    for x in S if not x.get('surface_only_resolvable')
)
min_cell = min(cells.values())
print(f'Min instances per action: {min_cell} (risk if < 3)')
"

echo "=== PRE-CHECK 5: DataOps evaluator exists (reference) ==="
python -c "
import os
ref = 'apps/dataops/backend/scripts/evaluate_multihop_stage1.py'
if os.path.exists(ref):
    print(f'Reference evaluator: {ref} ({os.path.getsize(ref)} bytes)')
else:
    print('WARNING: DataOps evaluator not found — build from scratch')
"

# ═══ TASK 1: Build ScenarioGraphStore + 4 Arms ═══
#
# File: apps/trading/backend/scripts/evaluate_multihop_stage1.py (NEW)
#
# Follow the DataOps evaluator pattern exactly. Adapt for Trading domain:
# - 5 categories, 5 actions, 6 factors
# - Centroid tensor: (5 × 5 × 6) — but build as (n_actions × n_factors)
#   since we score per-action, not per-category-action.
#
# CENTROID INITIALIZATION (REQ-1 — enriched, not surface):
#   For each action, collect all scenarios with that ground_truth_action.
#   For each, apply all hops to get enriched vector.
#   μ[action] = mean(enriched vectors for that action).
#   If cell has < 3 instances → use rng.uniform(0.2, 0.8, n_factors)
#   with seed=42.
#
# FOUR ARMS:
#   ARM 1: single_pass — score v_0 against centroids
#   ARM 2: breadth — read ALL branches up to budget, re-extract, score
#   ARM 3: content_rule — use correct_branches, upper bound
#   ARM 4: vld — score-conditioned routing, selective replacement, re-score
#
# HEADLINE: VLD vs BREADTH on score_keyed (not VLD vs content_rule)

# ═══ TASK 2: Run + Report ═══
#
# Run all 4 arms on all 40 instances.
# Expected: 40 × 4 = 160 result rows.
#
# Save: apps/trading/backend/data/trading_multihop_stage1_results.json
# Generate: apps/trading/backend/data/trading_multihop_stage1_report.md
#
# REPORT SECTIONS:
#
# 1. ACCEPTANCE TEST:
#    HEADLINE: VLD vs BREADTH on score_keyed
#    | ρ | SP | breadth | content_rule | VLD | Δ(VLD−breadth) | Δ(VLD−SP) |
#    PASS if: Δ(VLD−breadth) negative at ρ=0.30, ~0 at ρ=0.50,
#    positive at ρ≥0.70
#
# 2. PER-KIND RESULTS:
#    | Kind | SP | breadth | content_rule | VLD | N |
#
# 3. CONTROLS:
#    Flat: VLD ≤ SP? (must pass)
#    ρ=0.50: VLD near chance 1/5=0.20 ± 0.20? (must pass — generous band for n=5)
#
# 4. PER-ρ TABLE (score_keyed only)
#
# 5. CROSS-COPILOT COMPARISON:
#    | Copilot | VLD at ρ≥0.70 | SP at ρ≥0.70 | Factors | Actions | N |
#    | SOC     | 100%          | 25-50%       | 6       | 4       | 50 |
#    | DataOps | 100%          | 12.5%        | 6       | 5       | 50 |
#    | S2P     | 56.2%         | 62.5%        | 7       | 5       | 50 |
#    | Trading | ___%          | ___%         | 6       | 5       | 40 |
#
# 6. CENTROID DIAGNOSTICS:
#    How many cells had ≥ 3 instances? (vs defaulted)
#    Centroid diff ‖μ_surface − μ_enriched‖
#    If VLD fails: is cell sparsity the cause? (S2P lesson)

# ═══ TASK 3: Tests ═══
#
# File: apps/trading/backend/tests/test_multihop_evaluation.py (NEW)
#
# 1. ScenarioGraphStore loads a trading scenario without error
# 2. ScenarioGraphStore returns different evidence for correct vs misleading
# 3. Single-pass arm uses only surface_factors (6 dims)
# 4. Breadth arm reads all branches up to budget
# 5. Content-rule arm uses correct_branches
# 6. VLD arm produces a trace with ≥1 step
# 7. Flat control: VLD ≤ SP
# 8. ρ=0.50: VLD near chance (0.20 ± 0.20 — generous band for n=5)
# 9. All 40 instances evaluated without crash
# 10. Results JSON has 160 rows (40 × 4 arms)
# 11. Enriched centroids used (centroid diff > 0)
# 12. Report file generated and non-empty

# ═══ POST-CHECKS (MANDATORY — all must pass before EXIT) ═══

# POST-CHECK 1: BLAST RADIUS
#   git diff --name-only apps/trading/backend/app/ → EMPTY
#   No production code modified.

# POST-CHECK 2: Results completeness
#   python -c "
#   import json
#   r = json.load(open('apps/trading/backend/data/trading_multihop_stage1_results.json'))
#   assert len(r) == 160, f'Expected 160 rows, got {len(r)}'
#   arms = set(x['arm'] for x in r)
#   assert arms == {'single_pass','breadth','content_rule','vld'}, f'Missing arms: {arms}'
#   print(f'Results: {len(r)} rows, arms: {sorted(arms)}')
#   "

# POST-CHECK 3: Report generated
#   python -c "
#   import os
#   rpt = 'apps/trading/backend/data/trading_multihop_stage1_report.md'
#   assert os.path.exists(rpt), 'Report not generated'
#   sz = os.path.getsize(rpt)
#   assert sz > 500, f'Report too small ({sz} bytes)'
#   print(f'Report: {rpt} ({sz} bytes)')
#   "

# POST-CHECK 4: Controls pass
#   python -c "
#   import json
#   r = json.load(open('apps/trading/backend/data/trading_multihop_stage1_results.json'))
#   d = json.load(open('apps/trading/backend/data/trading_multihop_stage1.json'))
#   S = {s['scenario_id']: s for s in d['scenarios']}
#
#   # Flat controls: VLD ≤ SP
#   flat_ids = [s['scenario_id'] for s in d['scenarios'] if s.get('surface_only_resolvable')]
#   for fid in flat_ids:
#       sp = [x for x in r if x['scenario_id']==fid and x['arm']=='single_pass'][0]['correct']
#       vld = [x for x in r if x['scenario_id']==fid and x['arm']=='vld'][0]['correct']
#       if vld and not sp:
#           print(f'CONTROL FAIL: flat {fid} VLD correct but SP wrong')
#   print(f'Flat controls checked: {len(flat_ids)}')
#
#   # ρ=0.50: VLD near chance
#   rho50_ids = [s['scenario_id'] for s in d['scenarios']
#                if s['branching_kind']=='score_keyed' and s['rho_planted']==0.50]
#   vld_correct = sum(1 for rid in rho50_ids
#                     for x in r if x['scenario_id']==rid and x['arm']=='vld' and x['correct'])
#   vld_acc = vld_correct / len(rho50_ids) if rho50_ids else 0
#   chance = 0.20
#   print(f'ρ=0.50 VLD accuracy: {vld_acc:.3f} (chance={chance:.3f}, band ±0.15)')
#   assert abs(vld_acc - chance) <= 0.20, f'ρ=0.50 control FAIL: {vld_acc:.3f} outside band'
#   "

# POST-CHECK 5: Tests pass
#   python -m pytest apps/trading/backend/tests/test_multihop_evaluation.py -q
#   Expected: 12 passed

# POST-CHECK 6: Existing suites unchanged
#   python -m pytest apps/trading/backend/tests/ -q --timeout=120
#   Expected: same count as PRE-CHECK 1 + 12 new = ___
#   python -m pytest tests/ -q --timeout=120
#   Expected: 3372+ passed (same as PRE-CHECK 2)

# POST-CHECK 7: No provenance regression
#   python -m pytest apps/trading/backend/tests/ -k provenance -q
#   If provenance test exists, must pass.

# ═══ EXIT ═══
# Include in session state or report:
# - Acceptance test: PASS or FAIL
# - Per-kind accuracy table
# - Per-ρ accuracy table (score_keyed)
# - Headline: accuracy(VLD) at ρ≥0.70 on score_keyed
# - Cross-copilot comparison (SOC=100%, DataOps=100%, S2P=56.2%, Trading=___)
# - Centroid diagnostics (cells covered, enriched vs surface diff)
# - If FAIL: is it centroid sparsity (S2P pattern) or data quality?
# "0 new regressions introduced."
```
