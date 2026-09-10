# ═══════════════════════════════════════════════════════════════
# CODEX E-5: Purchasing Stage 1 Multi-Hop Evaluation
# Repo: copilot-sdk
# Model: gpt-5.6-terra (measurement script, no app changes)
# PARALLEL-SAFE: scripts/ and data/ only, no app/ changes
# ═══════════════════════════════════════════════════════════════

```
/model gpt-5.6-terra
/reasoning high

# ═══ REQUIRED READING ═══
#
# 1. Purchasing Stage 1 data (YOUR INPUT — 40 instances):
#    copilot-sdk/apps/purchasing/backend/data/purchasing_multihop_stage1.json
#
# 2. Purchasing schema extensions:
#    copilot-sdk/apps/purchasing/backend/data/purchasing_multihop_schema_extensions.json
#
# 3. Purchasing domain:
#    - Categories (5): demand_pattern, supplier_comparison, consumption_history,
#      stockout_risk, quality_incident
#    - Actions (6): order_standard, order_increased, order_reduced,
#      switch_supplier, defer_order, emergency_order
#    - Factors (6): demand_forecast, supplier_reliability, consumption_rate,
#      shelf_life, cost_efficiency, quality_score
#
# 4. DataOps evaluator (REFERENCE — follow this pattern):
#    copilot-sdk/apps/dataops/backend/scripts/evaluate_multihop_stage1.py

# ═══ CONTEXT ═══
#
# SOC and DataOps: VLD=100% at ρ≥0.70. S2P: 56.2% (centroid sparsity).
# Trading: pending (E-4).
#
# Purchasing has 6 ACTIONS (most of any copilot). Chance = 1/6 = 0.167.
# 40 instances with 35 non-flat / 6 actions = ~5.8 per action cell.
#
# LESSONS: enriched centroids mandatory (REQ-1). Headline is VLD vs
# breadth on score_keyed (content_rule is oracle). ρ=0.50 band ±0.20
# for small n.
#
# SCRIPTS-ONLY. No app/ changes.

# ═══ PRE-CHECKS (ALL MANDATORY) ═══

echo "=== PRE-CHECK 1: Purchasing backend baseline ==="
cd $CLAUDE_SDK
python -m pytest apps/purchasing/backend/tests/ -q --timeout=120 2>&1 | Select-Object -Last 5
# Record exact count. If failures → HALT.

echo "=== PRE-CHECK 2: SDK root baseline ==="
python -m pytest tests/ -q --timeout=120 2>&1 | Select-Object -Last 5

echo "=== PRE-CHECK 3: Stage 1 validator ==="
python apps/purchasing/backend/scripts/validate_stage1.py
# Must pass ALL 10 QUALITY CHECKS.

echo "=== PRE-CHECK 4: Data integrity ==="
python -c "
import json, collections
d = json.load(open('apps/purchasing/backend/data/purchasing_multihop_stage1.json'))
S = d['scenarios']
print(f'Instances: {len(S)}')
assert len(S) == 40, f'Expected 40, got {len(S)}'
assert 'provenance' in d, 'MISSING provenance'
print(f'Provenance: {d[\"provenance\"]}')
kinds = collections.Counter(x['branching_kind'] for x in S)
print(f'Kinds: {dict(kinds)}')
rhos = collections.Counter(x['rho_planted'] for x in S if x['branching_kind'] == 'score_keyed')
print(f'Score-keyed ρ: {dict(sorted(rhos.items()))}')
actions = collections.Counter(x['decision_tree']['ground_truth_action'] for x in S)
print(f'Actions: {dict(actions)}')
n_actions = len(actions)
print(f'Action count: {n_actions} (chance = {1/n_actions:.3f})')
flat = sum(1 for x in S if x.get('surface_only_resolvable'))
print(f'Flat controls: {flat}')
sample = S[0]['alert']['surface_factors']
expected = {'demand_forecast','supplier_reliability','consumption_rate',
            'shelf_life','cost_efficiency','quality_score'}
actual = set(sample.keys())
if actual != expected:
    print(f'WARNING: factor mismatch. Expected: {sorted(expected)}, Got: {sorted(actual)}')
else:
    print(f'Factor names: OK ({len(actual)} factors)')
ids = [x['scenario_id'] for x in S]
assert len(ids) == len(set(ids)), 'Duplicate scenario_ids!'
print(f'Scenario IDs: all unique')
cells = collections.Counter(
    x['decision_tree'].get('ground_truth_action','?')
    for x in S if not x.get('surface_only_resolvable'))
print(f'Instances per action: {dict(cells)}')
print(f'Min per action: {min(cells.values())}')
"

echo "=== PRE-CHECK 5: Reference evaluator exists ==="
python -c "
import os
ref = 'apps/dataops/backend/scripts/evaluate_multihop_stage1.py'
print(f'Reference: {ref} ({os.path.getsize(ref)} bytes)' if os.path.exists(ref) else 'WARNING: not found')
"

# ═══ TASK 1: ScenarioGraphStore + 4 Arms ═══
#
# File: apps/purchasing/backend/scripts/evaluate_multihop_stage1.py (NEW)
#
# Follow DataOps evaluator. Adapt for Purchasing:
# - 6 actions, 6 factors. Chance = 1/6 = 0.167.
# - Centroids: (n_actions × n_factors) = (6 × 6).
# - ENRICHED centroids (apply all hops before computing mean).
# - Cells with < 3 instances → rng.uniform(0.2, 0.8, 6) seed=42.
# - HEADLINE: VLD vs BREADTH on score_keyed.

# ═══ TASK 2: Run + Report ═══
#
# 40 × 4 = 160 result rows.
# Save: apps/purchasing/backend/data/purchasing_multihop_stage1_results.json
# Generate: apps/purchasing/backend/data/purchasing_multihop_stage1_report.md
#
# REPORT:
# 1. ACCEPTANCE TEST: VLD vs breadth on score_keyed per ρ
# 2. PER-KIND: | Kind | SP | breadth | content_rule | VLD | N |
# 3. CONTROLS: flat (VLD ≤ SP), ρ=0.50 (VLD near 0.167 ± 0.20)
# 4. PER-ρ TABLE
# 5. CROSS-COPILOT:
#    | Copilot     | VLD ρ≥0.70 | Actions | Factors | N  |
#    | SOC         | 100%       | 4       | 6       | 50 |
#    | DataOps     | 100%       | 5       | 6       | 50 |
#    | S2P         | 56.2%      | 5       | 7       | 50 |
#    | Trading     | TBD        | 5       | 6       | 40 |
#    | Purchasing  | ___%       | 6       | 6       | 40 |
# 6. CENTROID DIAGNOSTICS: cells covered, enriched vs surface diff

# ═══ TASK 3: Tests ═══
#
# File: apps/purchasing/backend/tests/test_multihop_evaluation.py (NEW)
#
# 1. ScenarioGraphStore loads scenario
# 2. Different evidence for correct vs misleading
# 3. Single-pass uses only surface_factors (6 dims)
# 4. Breadth reads all branches up to budget
# 5. Content-rule uses correct_branches
# 6. VLD produces trace with ≥1 step
# 7. Flat control: VLD ≤ SP
# 8. ρ=0.50: VLD near chance (0.167 ± 0.20)
# 9. All 40 instances evaluated
# 10. Results JSON has 160 rows
# 11. Enriched centroids used (diff > 0)
# 12. Report generated and non-empty

# ═══ POST-CHECKS (ALL MANDATORY) ═══

# POST-1: BLAST RADIUS
#   git diff --name-only apps/purchasing/backend/app/ → EMPTY

# POST-2: Results completeness
#   python -c "
#   import json
#   r = json.load(open('apps/purchasing/backend/data/purchasing_multihop_stage1_results.json'))
#   assert len(r) == 160, f'Expected 160, got {len(r)}'
#   arms = set(x['arm'] for x in r)
#   assert arms == {'single_pass','breadth','content_rule','vld'}
#   print(f'Results: {len(r)} rows, arms: {sorted(arms)}')
#   "

# POST-3: Report exists and non-trivial
#   python -c "
#   import os
#   rpt = 'apps/purchasing/backend/data/purchasing_multihop_stage1_report.md'
#   assert os.path.exists(rpt) and os.path.getsize(rpt) > 500
#   print(f'Report: {os.path.getsize(rpt)} bytes')
#   "

# POST-4: Controls
#   python -c "
#   import json
#   r = json.load(open('apps/purchasing/backend/data/purchasing_multihop_stage1_results.json'))
#   d = json.load(open('apps/purchasing/backend/data/purchasing_multihop_stage1.json'))
#   flat_ids = [s['scenario_id'] for s in d['scenarios'] if s.get('surface_only_resolvable')]
#   for fid in flat_ids:
#       sp = [x for x in r if x['scenario_id']==fid and x['arm']=='single_pass'][0]['correct']
#       vld = [x for x in r if x['scenario_id']==fid and x['arm']=='vld'][0]['correct']
#       if vld and not sp: print(f'FLAT CONTROL FAIL: {fid}')
#   print(f'Flat controls: {len(flat_ids)} checked')
#   rho50 = [s['scenario_id'] for s in d['scenarios']
#            if s['branching_kind']=='score_keyed' and s['rho_planted']==0.50]
#   vc = sum(1 for rid in rho50
#            for x in r if x['scenario_id']==rid and x['arm']=='vld' and x['correct'])
#   va = vc/len(rho50) if rho50 else 0
#   print(f'ρ=0.50 VLD: {va:.3f} (chance=0.167, band ±0.20)')
#   assert abs(va - 0.167) <= 0.25, f'ρ=0.50 FAIL: {va:.3f}'
#   "

# POST-5: Tests pass
#   python -m pytest apps/purchasing/backend/tests/test_multihop_evaluation.py -q
#   Expected: 12 passed

# POST-6: Existing suites unchanged
#   python -m pytest apps/purchasing/backend/tests/ -q --timeout=120
#   Expected: PRE-CHECK 1 count + 12
#   python -m pytest tests/ -q --timeout=120
#   Expected: 3372+

# POST-7: Provenance
#   python -m pytest apps/purchasing/backend/tests/ -k provenance -q

# ═══ EXIT ═══
# Report: PASS/FAIL, per-ρ table, cross-copilot comparison.
# "0 new regressions introduced."
```
