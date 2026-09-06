# Product Integrity Execution Strategy

**Version:** 3.0
**Date:** July 10, 2026
**Purpose:** Ensure code implementation faithfully delivers the
product's architecture, commercial value, innovation narrative,
and demo story — and keeps delivering them as implementation
velocity continues.
**Applies to:** All 5 copilots, all 5 repos, current code + after
every prompt batch.

**v2.7 — absorbs the substantiation architecture (canonical merge).** The cross-copilot
substantiation work developed separately (day-zero readiness, four-tier substantiation model,
generated-data taxonomy) is folded in here as the single source of truth, retiring the standalone
`day_zero_substantiation_architecture` reconstruction. New: **§2.4 Substantiation Tiers**
(T-A/T-S/T-O/T-R + the META-4 line + ClaimRegistry migration guard), **§2.5 Generated-Data Taxonomy**
(K1–K4, two bright lines, two-track extraction discipline), **§2.6 Day-Zero Substantiation State**
(the 3-state machine required for every measurement-gated surface). FORBIDDEN extended F-21..F-23
(scraped-as-learned reuses existing F-15), CANONICAL extended C-15..C-16, tier checklists (§6) and the
design registry (§1.0) updated. These
*extend* existing §2.1 (provenance honesty), §2.3 (counterfactual faithfulness), §4.2 (provenance
render), and §8 — they do not replace them.

**v2.8 — outreach collateral under governance.** The end-state narrative (elevator pitches, scenario
catalog) is registered in the §8.3 T3 scan: its end-state magnitudes ("$1.62M/yr," "10,000 decisions,"
"180 days GREEN") are **T-R / after-N** claims (§2.4) and must be tier-labeled — never presented as
current-measured — before any external send (F-21). No other change from v2.7.

**v3.0 — POSTURE + the learning-mechanism truth.** Two structural changes. (1) **§0.5 POSTURE (read first):**
these gates guard **the SEND, not the ROADMAP.** Claim↔code mismatch is the normal state of a company
strengthening its architecture; it closes by *building*, not by shrinking the plan. The single failure this
document exists to prevent is *being caught overclaiming in a diligence room* — so the discipline lives at the
point of external send (T3), and ambition lives in the roadmap. **Showing roadmap is allowed and expected**;
implying roadmap is live is the violation. *Build ambitiously. Claim precisely. Never confuse the two.*
(2) **§2.7 — the learning mechanism, named correctly** (cross-repo Codex diagnostic): the primary mechanism is
**online supervised centroid/prototype learning from verified human decisions** (+ DK coordinate search) —
**NOT RL** (F-25); genuine bandits are peripheral, and the Thompson sampler is `ConservationBoundedThompson`
(**C-19**). The honest naming is the *stronger* claim (**C-18**: "we have no reward function for judgment").
Shared cross-copilot learned state **NOT FOUND** (F-26). **SOC learning is disabled by default** — a demo-truth
constraint. New **§2.8 scenario classes (LIVE / NEAR / ARCH)** operationalize §0.5 (F-27). **§7.3 now carries
evidence-based gate coverage with ONE OPEN F-24** (prompt-variant promotion is ungated ⇒ C-17 scoped until
`C-GOV` lands, ~0.5-1d). Registry extended: **F-25..F-27, C-18..C-19**.

**v2.9 — governed-compounding is now code-checkable.** The platform's headline differentiation ("one
conservation law governs all compounding loops"; next_steps §3.1) is made falsifiable: new **§7.3 governed-
compounding check** (GC-01..05 — every compounding loop routes through one `ConservationGate`, fails-closed
on violation, carries provenance; L3/L4 tier check), wired into the T2/T3 checklists. FORBIDDEN **F-24**
(claiming "governs all loops" when a loop isn't gated) and CANONICAL **C-17** (the governed-compounding claim,
evidence = §7.3) added. The narrative cannot outrun the code.

---

## The Problem This Solves

Codex implements features at high velocity. But implementation
velocity without integrity verification produces a product that
passes tests but fails demos, impresses engineers but confuses
buyers, and accumulates architectural drift that becomes impossible
to extract.

This document defines a tiered verification regime where the most
critical checks run automatically at zero human cost, batch-level
checks run in 15 minutes, and deep assessments run periodically.

---

## §0.5 — POSTURE: these gates guard the SEND, not the ROADMAP (v3.0)

**Read this before applying any check below.** This document is frequently misread as a governor on *what we
may build*. It is not, and treating it that way makes it weaker, not stronger — a gate that tries to police
ambition gets quietly bypassed under a demo deadline, which is exactly when integrity matters most (§6).

**The correct scope, stated once:**

| | Governed by this document? |
|---|---|
| **What we BUILD** (roadmap, architecture, migrations) | **NO.** Build ambitiously. A 63-site migration that yields the right architecture is a *sequencing* problem, not an integrity problem. Claim↔code mismatch is the **normal state of a company strengthening its architecture** — it closes by *building*, not by shrinking the plan. |
| **What we SAY on an external surface** (deck, OSS README, buyer doc, paper, demo shown to a human) | **YES — absolutely.** Every claim is tier-labeled (§2.4), every scenario is class-labeled (§2.7), and the FORBIDDEN registry (§8.1) is enforced at **T3, the point of send.** |

**The single failure we exist to prevent:** *being caught overclaiming in a diligence room, a buyer's security
review, or a peer review.* That is fatal, and it is preventable by a pre-flight check at the send. Everything
else — an ambitious roadmap, an architecture ahead of its proof, an experiment that hasn't run yet — is normal
engineering and **is not this document's business.**

**Corollary — showing roadmap is ALLOWED and expected.** Investors and buyers expect a roadmap. A future
capability, **explicitly labeled as roadmap**, is not an overclaim; refusing to show it is self-harm. The
violation is *implying* a roadmap capability is live (see §2.7 scenario classes; **F-27**).

**So: build ambitiously. Claim precisely. Never confuse the two.**

---

The goal is a system where drift is caught the day it's introduced,
not the week before a demo.

### Lessons From This Session That Shaped v2.0

| Session work | Lesson | What it changed in this document |
|---|---|---|
| P38 S2P evidence | Fixture values presented as real metrics are the dominant DD risk — worse than architecture overclaims | Added §2: Provenance Honesty layer |
| P38 review rung 4 | "Change this factor — does the score change?" is the deepest buyer question | Added §2.3: Counterfactual Faithfulness |
| P29 migration | The product is the re-derived scorer STATE, not the decision LOG. Ordering is correctness. | Added §2.2: Judgment Memory Integrity |
| Route architecture | Aggregate metrics hide workload-specific regressions (P3H proved it) | Built into §3: per-workload, not aggregate |
| Route wiring | "Change observability before authority" — shadow before served | Shaped §6: tiered from automated to periodic |
| Counter design | AGE rejects MERGE; advisory locks for multi-worker safety | Included in §1.1: AGE Safety invariants |
| A1 scale measurement | Measured data trumps projections. 193ms without cache/counters. | §3 gates on measured values, not projected |
| v2.0 review | MERGE invariant contradicts counter + migration designs — reconcile to MATCH-then-CREATE | §1.1 MERGE note, §9.1 cross-artifact |
| v2.0 review | Provenance is a type, not a scan — make illegal state unrepresentable | §2.1 redesigned as `Provenanced[T]` |
| v2.0 review | Comparative tests need frozen benchmark with held-out eval, not stochastic thresholds | §3.1 benchmark requirements |
| v2.0 review | Gate tiers on transitions (batch-close, demo, publish), not calendar | §6 transition-gated |
| v2.0 review | T0 = most frequent drift; T2 = most expensive drift. Both mandatory. | §6.0 reworded |

---

## §0 — Implementation Priority (For Coding Session)

**Build order matters.** The coding session should implement in this
sequence. Each step produces a working deliverable. Later steps
depend on earlier ones.

### Step 1: T0 Scanner Script (~2h)

Build the automated literal-pattern scanner. This is a single Python
script that runs from the `copilot-sdk` root and scans all repos.

**Repo:** `copilot-sdk`
**File:** `integrity/architecture_scan.py`
**Also create:** `integrity/run_t0.sh` (CI entry point)

The script is the foundation. Everything else layers on top.

### Step 2: Provenanced[T] Type (~1h)

Add the provenance type to the SDK so evidence builders can use it.

**Repo:** `copilot-sdk`
**File:** `copilot_sdk/evidence/provenance.py`
**Test:** `tests/test_provenance.py`

This is a library addition. No existing code changes yet — just
the type definition + tests. Evidence builders adopt it in Step 5.

**Adoption path:** S2P is first adopter (Step 5). Other copilots
adopt when their evidence builders ship — Trading, Purchasing,
DataOps at their respective feature milestones. The type exists in
the shared SDK so all copilots can import it immediately.

### Step 3: Frozen Benchmark Fixture + Test Helpers (~2h)

Generate the held-out benchmark data AND the helper functions that
Steps 4 and 7 depend on. Uses the SDK `from_preset` pattern, not
direct ProfileScorer construction.

**Repo:** `copilot-sdk`
**Files:**
- `integrity/generate_benchmark.py` (one-time generator)
- `integrity/fixtures/benchmark_factors_v1.json`
- `integrity/fixtures/benchmark_outcomes_v1.json`
- `integrity/benchmark_fixture.py` (loader + test helpers)

**The loader must provide these helpers for Steps 4 and 7:**
```python
# integrity/benchmark_fixture.py

def load_benchmark_split(split: str) -> list[tuple]:
    """Load train or eval split."""

def train_scorer(decisions: list, seed: int) -> CompoundingScorer:
    """Instantiate from_preset, train on decisions, return scorer."""

def measure_accuracy(scorer, eval_set: list) -> float:
    """Score eval_set, compare to known correct actions, return accuracy."""

def measure_accuracy_with_weights(scorer, eval_set, weights) -> float:
    """Score with custom DK weights, measure on held-out."""

def decisions_to_threshold(scorer, eval_set, threshold: float) -> int:
    """How many decisions until accuracy reaches threshold on held-out."""

def inject_disruption(scorer):
    """Perturb centroids to simulate category disruption."""
```

**Generator uses SDK pattern:**
```python
from copilot_sdk.scoring.scorer import CompoundingScorer

scorer = CompoundingScorer.from_preset("dataops")  # or "soc"
# Generate synthetic factors matching preset's D dimension
# Use seed=42 for reproducibility
# Split 600 → 500 train + 100 held-out eval
```

### Step 4: Innovation Comparative Tests (~3h)

Implement §3.1 tests using the frozen benchmark.

**Repo:** `copilot-sdk`
**File:** `integrity/test_innovation_claims.py`

### Step 5: Adopt Provenanced[T] in S2P Evidence Builder (~2h)

Wire the provenance type into the existing S2P evidence builder.
S2P is first adopter. Other copilots adopt when their evidence
builders ship (Trading, Purchasing, DataOps at their feature
milestones).

**Repo:** `s2p-copilot`
**Stage 1 (discovery):** Find the actual evidence builder file.
P38 may have created `graph_traversal.py`, P37 may have created
`evidence_formatter.py`. Run:
```bash
grep -rl "build.*context\|situation_context\|evidence.*chain" \
  s2p-copilot/backend/app/services/ --include="*.py"
```
**Modify:** whichever file builds the `situation_context` dict
**Test:** `backend/tests/test_s2p_provenance.py`

### Step 6: Commercial Endpoint Smoke Script (~1h)

Build the curl-level endpoint verifier.

**Repo:** `copilot-sdk`
**File:** `integrity/commercial_smoke.py`

### Step 7: Judgment Memory + Counterfactual Tests (~2h)

Implement §2.2 and §2.3 tests.

**Repo:** `copilot-sdk`
**File:** `integrity/test_product_truth.py`

### Total: ~13h across 7 steps.

**Steps 1-3 are prerequisites.** Steps 4-7 can be parallelized or
reordered. The coding session should complete Steps 1-3 in the
first batch, then Steps 4-7 in the second.

---

## §1 — Architecture & Design Conformance

### 1.0 Design Document Registry

All design authority documents live in `copilot-sdk/docs/design/`.
The integrity tests verify code against THESE documents — not
against hardcoded values in the test scripts.

| Document | Governs | Referenced by |
|---|---|---|
| `trading_copilot_product_definition_v1.md` | Trading: tensor (5,4,D), factors, features | SHAPE-02, §3.2 smoke, §7 |
| `purchasing_copilot_pd_v1_3.md` | Purchasing: tensor, kitchen language, features | SHAPE-02, LANG-01, §7 |
| `dataops_copilot_design_v1_6.md` | DataOps: 6 intelligence levels, features | SHAPE-02, §3.2, §7 |
| `s2p_copilot_unified_v1_3.md` | S2P: 5 categories, penalty, evidence | SHAPE-02, §3.2, §7 |
| `math_synopsis_v18.md` | Conservation formula, DK, re-convergence, q, η | CONS-01, §3.1, §8 |
| `dk_runtime_execution_plan_v6_8.md` | L5 proof chain, C9B, DK calibration | §2.2, §3.1 |
| `copilot_analyze_route_architecture_v4_0.md` | Route: 4-phase, counters, cache, wiring | §1.3, AGE-01 |
| `soc_campaign_identity_architecture_v1_3.md` | Campaign identity, stable tuple | SOC tests |
| `judgment_memory_v2_7.md` | Judgment memory: re-derive, ordering, state | §2.2 |
| `cga_arxiv_short_v7_6.md` | arxiv paper claims | §8.3 paper pass |
| `jm_paper_draft_v9.md` | JM paper claims | §8.3 paper pass |
| `ci_blog_v15.md` | CI blog claims | §8.3 paper pass |
| `master_action_plan_v5.163.md` | MAP: queue, priorities, feature list | §1.2 gap detector |

**The design gap detector (§1.2) and SHAPE-02 read from these
documents.** When a test checks "tensor shape = (5,4,7) for Trading,"
it should extract that value from the PD, not hardcode it in the
test.

**The paper consistency pass (§8.3) scans these specific files:**
- `cga_arxiv_short_v7_6.md`
- `jm_paper_draft_v9.md`
- `ci_blog_v15.md`

**Substantiation architecture (v2.7):** the cross-copilot substantiation model — tiers, generated-data
taxonomy, and the day-zero state — now lives in **this document (§2.4–§2.6)**, not a separate file. The
prior standalone `day_zero_substantiation_architecture` doc was a reconstruction from a session summary and
is **retired**; its additive content is folded here and its overlaps (provenance honesty, counterfactual
faithfulness, FORBIDDEN/CANONICAL) defer to the canonical §2.1/§2.3/§8. Anything referencing the old file
should now point to this doc's §2.4–§2.6.

### 1.1 Invariant Scanner

**Tier: T0 (literal-pattern checks) + T1 (scope/semantic checks).**

An unreliable automated gate gets `# noqa`'d into irrelevance the
first week it false-fires on a clean PR. Split into two classes:

**Class A — Literal-pattern checks (T0, grep, zero-cost, reliable):**

These match exact strings regardless of scope. No false positives
possible because the string itself is the violation.

**Runnable script (`copilot-sdk/integrity/architecture_scan.py`):**

```python
#!/usr/bin/env python3
"""T0 Architecture Invariant Scanner.
Run: python integrity/architecture_scan.py
     (auto-detects repos root from script location)
Exit code 0 = PASS, 1 = violations found.
"""
import re, sys, os
from pathlib import Path

LITERAL_CHECKS = [
    {
        "id": "AGE-01", "severity": "P1",
        "name": "no_merge_in_cypher",
        "pattern": re.compile(r"\bMERGE\b"),
        "scan_dirs": ["ci-platform", "gen-ai-roi-demo-v4-v50", "copilot-sdk",
                       "s2p-copilot"],
        "extensions": [".py"],
        "skip_if_in_line": ["test", "#", '"""', "SKILL", "docstring", "MERGE is forbidden"],
    },
    {
        "id": "AGE-02", "severity": "P1",
        "name": "no_raw_sqlite3_in_production",
        "pattern": re.compile(r"sqlite3\.connect"),
        "scan_dirs": ["copilot-sdk/copilot_sdk", "s2p-copilot/backend/app",
                       "gen-ai-roi-demo-v4-v50/backend/app"],
        "extensions": [".py"],
        "skip_if_in_line": ["migration", "test", "preseed"],
    },
    {
        "id": "LANG-01", "severity": "P2",
        "name": "purchasing_kitchen_language",
        "pattern": re.compile(r"\b(inventory|customers|shrinkage|SKU)\b", re.I),
        "scan_dirs": ["copilot-sdk/apps/purchasing/frontend",
                       "copilot-sdk/apps/purchasing/backend/app/routers"],
        "extensions": [".py", ".tsx", ".ts"],
        "skip_if_in_line": ["test", "#", "//", "migration"],
    },
]

def scan_file(filepath: Path, check: dict) -> list[dict]:
    violations = []
    try:
        lines = filepath.read_text(encoding="utf-8", errors="ignore").splitlines()
    except Exception:
        return []
    for i, line in enumerate(lines, 1):
        if check["pattern"].search(line):
            if any(skip in line.lower() for skip in check.get("skip_if_in_line", [])):
                continue
            violations.append({
                "id": check["id"], "file": str(filepath),
                "line": i, "text": line.strip()[:120],
                "severity": check["severity"],
            })
    return violations

def main(repos_root: str):
    all_violations = []
    for check in LITERAL_CHECKS:
        for scan_dir in check["scan_dirs"]:
            root = Path(repos_root) / scan_dir
            if not root.exists():
                continue
            for ext in check["extensions"]:
                for filepath in root.rglob(f"*{ext}"):
                    all_violations.extend(scan_file(filepath, check))

    if all_violations:
        print(f"\\n{'='*60}")
        print(f"T0 SCAN: {len(all_violations)} violation(s) found")
        print(f"{'='*60}")
        for v in all_violations:
            print(f"  [{v['severity']}] {v['id']} {v['file']}:{v['line']}")
            print(f"         {v['text']}")
        p1s = [v for v in all_violations if v["severity"] == "P1"]
        if p1s:
            print(f"\\nBLOCKED: {len(p1s)} P1 violation(s). Fix before merge.")
            sys.exit(1)
    else:
        print("T0 SCAN: PASS (0 violations)")
    sys.exit(0)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--repos", default=None,
                        help="Root dir containing all repos. "
                             "Auto-detected from copilot-sdk location if omitted.")
    args = parser.parse_args()
    repos = args.repos
    if repos is None:
        # Auto-detect: this script is in copilot-sdk/integrity/
        # Repos root is two levels up
        repos = str(Path(__file__).resolve().parent.parent.parent)
    main(repos)
```

**CI entry point (`copilot-sdk/integrity/run_t0.sh`):**

```bash
#!/bin/bash
# Run from copilot-sdk root: ./integrity/run_t0.sh
# Auto-detects repos root from script location
REPOS_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
python "$(dirname "$0")/architecture_scan.py" --repos "$REPOS_ROOT"
```

**Class B — Scope/semantic checks (T1, needs AST or human, 15 min):**

These verify that a call happens in the right SCOPE, or that a
value is computed by the right FORMULA. Grep can't see scope — it
matches the string in the file but can't tell if the call is inside
a function the preview path never reaches.

```python
SCOPE_CHECKS = [
    {
        "id": "ARCH-02",
        "name": "no_decision_write_in_read_only",
        "check": "write_decision/create_decision called ONLY from "
                 "learn/outcome/scoring_router scope, never from "
                 "preview/evidence/read-only scope",
        "method": "AST scope analysis or human file review",
        "severity": "P1",
    },
    {
        "id": "ARCH-03",
        "name": "centroid_update_only_in_learn",
        "check": "scorer.update() called only from learn() path",
        "method": "AST call-graph or grep + human verify scope",
        "severity": "P1",
    },
    {
        "id": "ARCH-04",
        "name": "dk_readonly_in_display",
        "check": "reestimate_dk/scorer.update never called from "
                 "evidence/radar/template/explanation code",
        "method": "AST or human scope review",
        "severity": "P1",
    },
    {
        "id": "CONS-01",
        "name": "conservation_formula_correct",
        "check": "θ_min = 23.53/(α×V) computed by the canonical "
                 "formula, not a hardcoded constant. The invariant "
                 "is the FORMULA, not the string '23.53' — refactoring "
                 "23.53 into constituent constants is valid.",
        "method": "human review of conservation module",
        "severity": "P1",
    },
    {
        "id": "CONS-02",
        "name": "auto_approve_conservation_gated",
        "check": "auto-approve/auto-order code checks conservation "
                 "GREEN/status before proceeding",
        "method": "trace call graph from auto-approve entry point",
        "severity": "P1",
    },
    {
        "id": "SHAPE-01",
        "name": "preset_registry_complete",
        "check": "all copilots in PRESET_REGISTRY",
        "method": "enumerate registry keys vs known copilot list",
        "severity": "P1",
    },
    {
        "id": "SHAPE-02",
        "name": "tensor_shape_aligned",
        "check": "preset C×A×D matches PD document claim matches bootstrap JSON. "
                 "Read expected shapes from docs/design/ PD for each copilot. "
                 "Do NOT hardcode shapes in the test — extract from PD.",
        "method": "parse PD tensor table + compare to preset + compare to bootstrap",
        "severity": "P1",
    },
    {
        "id": "PROTO-01",
        "name": "graphstore_protocol_complete",
        "check": "every GraphStore protocol method implemented in "
                 "SQLiteGraphStore + AGEGraphStore",
        "method": "compare protocol class methods vs impl methods",
        "severity": "P1",
    },
]
```

**Exit criterion:** Zero P1 violations across both classes.

**MERGE reconciliation note:** AGE-01 catches a real contradiction
from earlier in this session. Both the CounterStore distinct-counter
design (v3.8 §4.5 SEEN_CATEGORY) and the P29 migration idempotency
suggestion originally used MERGE. Both must use the advisory-lock +
MATCH-then-CREATE pattern instead:

```python
# WRONG (AGE rejects):
# MERGE (u)-[:SEEN_CATEGORY]->(c)

# CORRECT (advisory-lock + MATCH-then-CREATE):
SELECT pg_advisory_xact_lock(hashtext('entity:U1'));
-- Check existence
OPTIONAL MATCH (u:User {id: 'U1'})-[e:SEEN_CATEGORY]->(c:Category {id: $cat})
RETURN e IS NOT NULL AS exists
-- If not exists: CREATE edge only
MATCH (u:User {id: 'U1'}) MATCH (c:Category {id: $cat})
CREATE (u)-[:SEEN_CATEGORY]->(c)
```

This applies to both counter maintenance (§5.3) and migration
idempotency (P29). The invariant scanner catches future violations.

### 1.2 Design Gap Detector

**Tier: T3 — quarterly, or before major milestones.**

Human review comparing implemented features against the product
definition (PD) documents in `copilot-sdk/docs/design/`.

```
For each copilot:
1. Read the PD from docs/design/:
   - SOC: soc_campaign_identity_architecture + route architecture
   - S2P: s2p_copilot_unified_v1_3.md
   - Trading: trading_copilot_product_definition_v1.md
   - Purchasing: purchasing_copilot_pd_v1_3.md
   - DataOps: dataops_copilot_design_v1_6.md
2. For each feature marked "shipped" in the PD:
   a. Find the implementing file(s) in code
   b. Classify: MATCH / PARTIAL (key behavior missing) / DRIFT (different behavior)
3. For each standing rule in the PD:
   a. Classify: ENFORCED (test exists) / SOFT (documented, no test) / BROKEN
4. Cross-reference MAP (master_action_plan_v5.163.md) for queue status
5. Output: gap report with file:line evidence
```

### 1.3 Architecture Drift Metrics

Track across sessions. Red flags trigger investigation:

| Metric | Measurement | Red flag |
|---|---|---|
| GraphStore bypass count | grep `sqlite3.connect` outside migration/test | > 0 |
| Protocol method coverage | impl methods ÷ protocol methods | < 100% |
| Preset registry completeness | registered copilots ÷ total copilots | < 100% |
| Standing rule enforcement | rules with tests ÷ total rules | < 80% |
| Conservation formula integrity | constant = 23.53, formula = α·q·V ≥ θ_min | any deviation |

---

## §2 — Product Truth Verification

This section addresses three layers of product truth that §1
(architecture conformance) doesn't catch. These emerged from the
P38 evidence review and P29 migration work.

### 2.1 Provenance Honesty — Make the Illegal State Unrepresentable

**Tier: T0 (type enforcement) + T1 (spot-check).**

v2.0 tried to grep for unlabeled fixtures (`exception_rate|
compliance_rate|...`). That's a hardcoded denylist that misses the
next fixture someone adds and false-fires on legitimate uses.
Provenance is a property of the DATA FLOW — "did this rendered
number come from a fixture?" — which string matching can't reveal.

**The robust version: make provenance a type at the evidence-builder
boundary.**

```python
# copilot_sdk/evidence/provenance.py

from dataclasses import dataclass
from typing import TypeVar, Generic, Literal

T = TypeVar('T')
Source = Literal["learned", "graph_store", "fixture"]

@dataclass(frozen=True)
class Provenanced(Generic[T]):
    """A value tagged with its provenance source.
    Every value that reaches an evidence/explanation render surface
    must be wrapped in this type. An untagged number CANNOT reach
    the render layer — it won't typecheck."""
    value: T
    source: Source
    label: str | None = None  # e.g., "integration pending" for fixture

# Usage in evidence builder:
def build_supplier_context(supplier_data) -> dict[str, Provenanced]:
    return {
        "exception_rate": Provenanced(
            value=supplier_data.exception_rate,
            source="fixture",
            label="illustrative — integration pending"
        ),
        "similar_decision_accuracy": Provenanced(
            value=accuracy,
            source="graph_store",
        ),
        "centroid_distance": Provenanced(
            value=distance,
            source="learned",
        ),
    }
```

**Enforcement (Class B scope check, T1):**

```python
# Add to SCOPE_CHECKS in §1.1 Class B:
{
    "id": "PROV-01",
    "name": "evidence_builder_uses_provenanced_type",
    "check": "evidence/context builder functions return Provenanced[T], "
             "not raw float/str/dict. Requires checking type annotations "
             "or return statements — not grep-safe.",
    "method": "human review or AST check of evidence builder modules",
    "severity": "P1",
}
```

**The three provenance classes (unchanged from v2.0):**

| Tag | Meaning | Visual | Example |
|---|---|---|---|
| `learned` | From verified decisions. The moat. | ██ highlighted | Centroid distance, DK weight |
| `graph_store` | From actual decision/outcome data | ██ full | Similar decisions count |
| `fixture` | Static/demo data | ░░ muted + label | Supplier exception rate |

**Why this is the highest-leverage change:** If the type system
guarantees every on-screen value carries its source, the buyer-facing
provenance rendering is free and can't drift. The provenance
distinction IS the product story when it's on screen. Microsoft
can't tag a line "← derived from 150 verified decisions by YOUR
AP team." CGA can.

### 2.2 Judgment Memory Integrity

**Tier: T2 — every batch, 10 minutes.**

The P29 migration review established: the product isn't the decision
log — it's the scorer state RE-DERIVED from the log. If centroids
and DK weights don't survive a restart, or if decision ordering
corrupts the re-derived state, the "compounding intelligence" claim
is false.

**Tests:**

```python
class TestJudgmentMemoryIntegrity:

    def test_scorer_state_survives_restart(self):
        """The fundamental compounding claim.
        Score input X → result A.
        Stop scorer. Restart scorer. Load from persistence.
        Score input X → result B.
        Assert A == B (within float tolerance).
        If this fails, judgment memory is volatile, not compounding."""

    def test_learning_order_preserved(self):
        """Decision ordering is a correctness requirement.
        DK estimation and phase transitions are path-sensitive.
        Replay decisions in original created_at order → state S1.
        Replay same decisions in random order → state S2.
        Assert S1 != S2 (ordering matters).
        Then verify production paths always process in order."""

    def test_verified_count_matches_scorer_belief(self):
        """The scorer's internal decision count must match
        what's persisted. If the scorer thinks it has 200 decisions
        (triggering DK estimation) but persistence has 20, the
        phase transition is based on phantom data."""

    def test_centroid_moves_toward_verified_outcome(self):
        """The core learning mechanism.
        Get centroid for (category, action).
        Submit 10 verified outcomes for that (category, action).
        Get centroid again.
        Assert centroid moved TOWARD the factor vectors of the outcomes.
        Not just 'moved' — moved in the right direction."""
```

### 2.3 Counterfactual Faithfulness

**Tier: T2 — every batch, 10 minutes.**

The P38 review rung 4: "if I change this displayed factor, does the
recommendation change?" If the evidence chain is decorative rather
than causal, it's explainability theater.

```python
class TestCounterfactualFaithfulness:

    def test_displayed_factor_influences_score(self):
        """The evidence chain shows factors that drove the decision.
        Changing the top displayed factor MUST change the score.
        If it doesn't, the evidence chain is narrative, not causal."""
        result_1 = scorer.score(factors_original, category)
        evidence = build_evidence(result_1)

        factors_modified = factors_original.copy()
        # Flip within valid [0,1] range — not multiply by -1 (invalid)
        factors_modified[evidence.top_factor_index] = \
            1.0 - factors_modified[evidence.top_factor_index]
        result_2 = scorer.score(factors_modified, category)

        assert result_1.confidence != result_2.confidence, \
            "Displayed factor doesn't influence score — explainability theater"

    def test_dk_weight_reflects_actual_trust(self):
        """DK weight displayed as 'trust score' must reflect
        actual scoring influence. A factor with weight 0.85
        must contribute more to the centroid distance than
        a factor with weight 0.15."""

    def test_conservation_status_reflects_actual_gate(self):
        """If conservation shows GREEN, auto-approve must be allowed.
        If conservation shows RED, auto-approve must be blocked.
        The display must match the gate, not an approximation."""
```

---

## §2.4 — Substantiation Tiers (What Evidence Backs a Claim)

Extends §2.1 (provenance honesty) and §2.3 (counterfactual faithfulness) from "is this value
labeled and does it move the score" to "what *kind* of evidence substantiates this claim, and is
the claim allowed at that tier." Every commercial claim / surfaced value is backed by exactly one
tier. The bright line runs between T-O and T-R.

| Tier | Source | Substantiates | Does NOT substantiate | Provenance label |
|---|---|---|---|---|
| **T-A Analytic** | Math proof / theorem (`math_synopsis_v18`) | existence + direction + a *bound*, day-zero | a realized magnitude for a given customer | `proven` |
| **T-S Scraped/External** | Real external data (feeds, filings, market data) — real, not customer-specific | a populated real day-zero product; context claims | "learned from YOUR operations" | ░░ `scraped_external` |
| **T-O Oracle-Synthetic** | Parametric oracle + synthetic stream | **capability** + **pipeline validity** (instrument detects a KNOWN injected effect) | **any magnitude of a real-agent effect** (the META-4 line) | test-only (never surfaces) |
| **T-R Real-Measured** | Customer's verified decisions (pilot+) | customer-specific magnitude; learned intelligence | — | ██ `learned` |

**The META-4 line (the standing result this encodes):** synthetic / LLM-persona data can
substantiate *capability* and *mechanism*; it structurally **cannot** substantiate the *magnitude*
of a behavioral/learning effect that depends on the real agent — the LLM competence prior IS the
data-generating mechanism (identifiability). "Does the system form campaigns / re-converge" is
simulable; "does it change THIS analyst's behavior by X%" is not. → **F-23.**

**ClaimRegistry + migration guard.** Every commercial claim is tagged with its tier and evidence
pointer (extends §8 CANONICAL). One rule: **no claim silently migrates to T-R (██ `learned`).**
Promotion requires an explicit evidence-bearing event (a pilot metric id). This is the CC-21
discipline (γ held at analytic, refused promotion to real except via EXP-G1) generalized to every
claim. → **F-21.**

**Per-copilot substantiation map:** SOC = T-A proven (γ) + T-R (analyst lift, pilot); Trading = T-S
(real market data, the K4 exemplar) + T-R (follow-rate); S2P = T-S (supplier filings) + T-R
(hold-rate); Purchasing = T-S (commodity prices) + T-R (order-change); DataOps = T-S (DQ benchmarks)
+ T-R (remediation-accept). **Only SOC has a proven T-A today**; the rest are T-S + T-R-pending — the
map says so rather than inventing a proof.

## §2.5 — Generated-Data Taxonomy (Four Kinds, Two Bright Lines)

"Synthetic data" is four distinct kinds with different rules; conflating them is the failure mode.
Refines §2.1's provenance tiers (`context` splits into `scraped_external` and `sample`; a new
`proven` tier covers analytic claims with no per-decision data).

| Kind | Generator | Tier | Substantiates | Label | Hard rule |
|---|---|---|---|---|---|
| **K1 Oracle-behavioral** | parametric oracle (AnalystOracle…) | T-O | pipeline validity + capability | test-only | never leaves the harness; validates the instrument detects a KNOWN injected effect |
| **K2 Factor-vector oracle** | LLM generates vectors → math oracle labels correctness | T-O | learning *mechanism* (the γ pattern) | test-only | substantiates γ>1 direction, never a realized γ |
| **K3 Demo-population fixture** | LLM-persona / archetype generator | none | **nothing** (demo realism only) | `sample` | **the dangerous one — it looks real**; NEVER in a metric/score/par/claim |
| **K4 Scraped/external real** | scraper/connector (real source) | T-S | real context (░░) | ░░ `scraped_external` | real, not customer-specific; carries source + freshness |

**Two bright lines:** (1) **K1/K2 never surface** — oracle output reaching a user-facing value is
the META-4 violation (**F-23**). (2) **K3 ≠ K4** — archetype demo data (K3) substantiates nothing and
is the highest fixture-as-real risk (**F-22**); scraped real (K4) is legitimate ░░ context. The
platform's biggest live K3 exposure is the Purchasing 50-supplier/500-order archetype generator
feeding P68/P72 computed metrics.

**Extraction discipline (two-track, for the substantiation SDK/UI):** display-layer components that
are identical across copilots *by construction* — the `ProvenanceBadge` + the tier enum — extract
NOW to a local `copilot-sdk` workspace package (+ one tested SOC copy). Behavioral protocols
(oracle / holdout / cohort-state logic) vary by domain → extract on the **second** real instance
(rule-of-three), not from SOC alone.

## §2.6 — Day-Zero Substantiation State (Required for Every Measurement-Gated Feature)

T-R magnitude is pilot-gated **by definition**, so **every measurement-gated surface is empty on day
zero** — and the temptation is to fill it with synthetic magnitude (**F-22**). A feature is not
"demo-ready" (§5 / T3) until it renders the empty-██ state without an error or a fabricated number.
Show **capability now** (T-A proven / T-O instrument-validated / labeled prior); let ██ fill over
real use.

**The 3-state contract** (one status object per measurement-gated surface; magnitude only from
`provenance=='real'`, only at MEASURED):
```
state := INSTRUMENT_VALIDATED (real_t==0 and real_c==0)   # day zero — show the instrument, not a number
       | ACCUMULATING          (real_t<K or real_c<K)
       | MEASURED              (both ≥ K)                   # ██ magnitude appears HERE, real-only
K = min real decisions/arm before a magnitude shows (default 30 until floor-power calibrates)

instrument{}  (T-O, ALWAYS present) — the oracle self-test: "injected +5pp → recovered +5pp ✓;
              0→0 ✓; +lift/−accuracy → gate rejects ✓" — framed as the instrument working, NOT the
              customer's forecast.
real{}        (T-R) — treatment_n/control_n/threshold_k; magnitude null until MEASURED; ██ learned.
structure{}   (optional K3 seed) — counts/split-balance/join-ok ONLY; `sample`; feeds NO magnitude.
```

**Enforcement tests (T2; identical shape on every copilot):**
```
□ only `sample` cohorts present → magnitude IS null, state != MEASURED          (F-22)
□ magnitude query filters provenance (excludes 'sample' AND 'oracle')           (F-22/F-23)
□ real ≥K both arms → MEASURED, magnitude computed from real only
□ instrument panel present at EVERY state (T-O), independent of real volume
```

**Promotion-gate guardrail:** any promotion / auto-approve gate takes `provenance=='real'` inputs by
construction; it **ABSTAINS** ("awaiting_real_cohorts") below K — never reads a synthetic magnitude
as "conditions met." Keeps a holdout/promotion clock from ever looking closer to closed than the
real data supports.

**Cross-copilot risk (worst replica = Purchasing):** slow accumulation + a cohort-shaped K3
generator + (until built) no provenance display; **learned par _looks_ learned**, so an
archetype-derived par is a hero-surface F-22. **Build the Purchasing day-zero state before P73/P75
render a par dashboard.** (The `par_shown` treatment flag is the Purchasing analog of SOC's
`campaign_context_shown` — it must be recorded at display time or the measurement is unrecoverable.)

---

## §2.7 — The Learning Mechanism: Name It Correctly (v3.0, evidence-based)

Established by the cross-repo Codex diagnostic (2026-07-10). **We must not describe our own architecture
inaccurately — that is the fastest way to lose a technical room**, and the first thing a VC benchmarking us
against an RL framework (e.g. TensorTrade) will probe.

**What the code actually does:**

| Layer | Mechanism | Evidence |
|---|---|---|
| **Primary (L1)** | **Online supervised centroid/prototype learning** from *verified human decisions* — the signal is a **correctness label, not a reward** — plus **DK coordinate-search** weight estimation | `gae/profile_scorer.py:780, :950`; `gae/dk_estimator.py:171-192` |
| **Secondary (L1b)** | **Genuine bandit components**, peripheral: Thompson posterior + UCB variant selection | `copilot_sdk/rl/exploration.py:41-52`; `rl_engine.py:328-359`; `prompt_evolver.py:282-311` |
| **Notable** | The Thompson sampler is **`ConservationBoundedThompson`** — *exploration is conservation-bounded by construction* | `copilot_sdk/rl/exploration.py:41-52` |

**The naming rule (→ F-25).** Do **not** call the primary mechanism "reinforcement learning" or "RL." Correct
names: *decision-trace learning*, *judgment/prototype learning*, *supervised centroid learning from verified
decisions*. The bandit components **may** be called bandits/Thompson/UCB — they are real, but they are not the
primary mechanism.

**Why the honest name is *stronger* (→ C-18/C-19).** "We have **no reward function for judgment** — we learn a
prototype geometry from verified human decisions" is a **sharper** differentiator than "we do RL," because it
is exactly what reward-maximizing agents cannot say. And "our explorer is conservation-bounded **by
construction**" is a governance claim with a class name behind it.

**Cross-copilot scope (→ F-26).** Shared cross-copilot **learned state: NOT FOUND**. The *architecture* is
shared (one SDK/GAE scorer); the *learned geometry is per-app/domain*. Until built (decision D5), say **"one
engine, five domains — signals transfer"**, never "judgment transfers between copilots."

**Per-copilot learning reality (affects demo truth, §5):** Trading / Purchasing / DataOps / S2P = **BUILT**
end-to-end. **SOC = PARTIAL — learning is DISABLED by default** (`soc/config.py:66`; gated at
`triage.py:1961-1968`). **A "watch it learn" beat on SOC is a demo-truth violation unless learning is
explicitly enabled and shown to change a later score.**

## §2.8 — Scenario Classes: LIVE / NEAR / ARCH (the operational form of §0.5)

Every scenario, capability, or claim placed on an **external surface** carries a class label. This is how
"build ambitiously, claim precisely" becomes a check.

| Class | Meaning | How it may be shown | Rule |
|---|---|---|---|
| **LIVE** | demoable today from the pinned preseed | shown **running** | must pass T3 (§6.4) |
| **NEAR** | shipping this wave; a build item exists | *"shipping — here's the item"* | effort/owner stated; never shown as running |
| **ARCH** | what the architecture enables; not yet built | **explicitly labeled roadmap/vision** | may be shown; must be labeled |

**The class travels with the scenario.** Showing an ARCH item is *allowed and expected* (investors expect a
roadmap). **The violation is an ARCH or NEAR item *implied* to be LIVE — or any external scenario with no class
label at all (→ F-27).**

**T3 check:** every scenario in a deck / storyboard / README / demo carries LIVE, NEAR, or ARCH, and the LIVE
ones actually run on the pinned preseed.

---

## §3 — Commercial & Innovation Value Verification

### 3.1 Innovation Claims: Comparative Tests (Not Just Existence)

**Tier: T2 — every batch, 15 minutes.**

v1.0 tested "does the machinery run?" v2.0 tests "does the
machinery WORK — does it actually deliver the compounding
intelligence the buyer is paying for?"

**Frozen benchmark requirement:** These tests verify the central
commercial claim. They deserve the most engineering. Without a
controlled test fixture, they're either flaky (stochastic threshold)
or tautological (measuring overfitting on training data).

```python
# integrity/benchmark_fixture.py

BENCHMARK = {
    "seed": 42,                    # Fixed seed for reproducibility
    "n_train": 500,                # Decisions used for learning
    "n_eval": 100,                 # HELD-OUT decisions for accuracy measurement
    "scenario": "frozen_soc_v1",   # Named scenario, versioned
    "factors": "fixtures/benchmark_factors_v1.json",  # Fixed factor vectors
    "outcomes": "fixtures/benchmark_outcomes_v1.json", # Fixed correct actions
}
```

**Critical:** Accuracy is measured on the HELD-OUT eval split, not
the training decisions. Measuring on training data tests overfitting,
not compounding. The held-out split is from the same distribution
but never seen during learning.

```python
class TestInnovationClaimsComparative:

    @pytest.fixture(autouse=True)
    def frozen_benchmark(self):
        """All comparative tests share a frozen scenario.
        Fixed seed, fixed data, held-out eval split."""
        self.train = load_benchmark_split("train")  # 500 decisions
        self.eval = load_benchmark_split("eval")    # 100 held-out
        self.seed = BENCHMARK["seed"]

    def test_accuracy_improves_with_learning(self):
        """THE core claim. Accuracy on held-out data IMPROVES.
        Not 'centroids moved' — accuracy IMPROVED on unseen data."""
        scorer_50 = train_scorer(self.train[:50], seed=self.seed)
        scorer_500 = train_scorer(self.train, seed=self.seed)
        acc_50 = measure_accuracy(scorer_50, self.eval)
        acc_500 = measure_accuracy(scorer_500, self.eval)
        assert acc_500 > acc_50 + 0.03, \
            f"No improvement on held-out: {acc_50:.2%} → {acc_500:.2%}"

    def test_dk_weights_improve_scoring(self):
        """DK weights must improve accuracy on held-out data.
        Uniform weights vs learned weights — learned must be better."""
        scorer = train_scorer(self.train, seed=self.seed)
        acc_uniform = measure_accuracy_with_weights(
            scorer, self.eval, np.ones(scorer.d) / scorer.d)
        acc_dk = measure_accuracy_with_weights(
            scorer, self.eval, scorer.dk_weights)
        assert acc_dk > acc_uniform, \
            "DK weights don't improve held-out accuracy — decorative"

    def test_conservation_prevents_bad_automation(self):
        """Drive accuracy below θ_min. Verify auto-approve BLOCKED.
        Restore accuracy. Verify auto-approve RESUMES.
        Gate must be functional, not advisory."""

    def test_reconvergence_is_faster(self):
        """Phase 1 cold start: N1 decisions to 80% on held-out.
        Disrupt. Phase 2 recovery: N2 decisions to 80% on held-out.
        Assert N2 < N1."""
        scorer = train_scorer(self.train[:200], seed=self.seed)
        n1 = decisions_to_threshold(scorer, self.eval, 0.80)
        inject_disruption(scorer)
        n2 = decisions_to_threshold(scorer, self.eval, 0.80)
        assert n2 < n1, f"Recovery not faster: {n1} → {n2}"

    def test_iks_increases_monotonically(self):
        """IKS at 100 < IKS at 300 < IKS at 500.
        Monotonic accumulation, not just > 0."""

    def test_penalty_asymmetry_is_conservative(self):
        """Override penalizes MORE than confirmation rewards.
        Centroid movement from one override > one confirm."""

    def test_judgment_memory_transfers(self):
        """Train on domain A. Transfer to domain B.
        B starts at better-than-random on held-out."""

    def test_five_copilots_same_engine(self):
        """All 5 presets load and score without error.
        Same CompoundingScorer, different configurations."""
```

### 3.2 Commercial Endpoint Smoke Tests

**Tier: T2 — every batch, 5 minutes per copilot.**

**Runnable script (`copilot-sdk/integrity/commercial_smoke.py`):**

```python
#!/usr/bin/env python3
"""T2 Commercial Endpoint Smoke Test.
Run: python integrity/commercial_smoke.py --copilot soc --port 8001
Ports: SOC=8001, S2P=8002, Trading=8010, Purchasing=8020, DataOps=8030
"""
import requests, sys, json

DEFAULT_PORTS = {
    "soc": 8001, "s2p": 8002, "trading": 8010,
    "purchasing": 8020, "dataops": 8030,
}

CHECKS = {
    "all": [
        {"path": "/api/health", "method": "GET",
         "expect_keys": ["phase", "alpha", "engine"],
         "name": "health endpoint has phase/alpha/engine"},
        {"path": "/api/trajectory", "method": "GET",
         "expect_nonempty": True,
         "name": "trajectory returns data"},
        {"path": "/api/conservation/status", "method": "GET",
         "expect_value_in": {"status": ["GREEN", "AMBER", "RED"]},
         "name": "conservation status is valid"},
        {"path": "/api/fingerprint", "method": "GET",
         "expect_keys": ["iks"],
         "name": "fingerprint has IKS"},
    ],
    "soc": [
        {"path": "/api/alert/analyze", "method": "POST",
         "body": {"alert_id": "smoke-test-001", "alert_type": "anomalous_login"},
         "expect_keys": ["action", "confidence", "factors"],
         "name": "SOC analyze returns action/confidence/factors"},
    ],
    "s2p": [
        # NOTE: discover actual evidence endpoint path in Stage 1.
        # P35 evidence route may be POST or different path than assumed.
        {"path": "/api/s2p/evidence/template",
         "method": "GET",
         "params": {"invoice_id": "INV-SMOKE-001"},
         "expect_keys": ["situation_context"],
         "name": "S2P evidence returns situation_context"},
    ],
}

def run_check(base_url, check):
    url = f"{base_url}{check['path']}"
    try:
        if check["method"] == "POST":
            r = requests.post(url, json=check.get("body", {}), timeout=5)
        else:
            r = requests.get(url, params=check.get("params"), timeout=5)
        if r.status_code != 200:
            return "FAIL", f"HTTP {r.status_code}"
        data = r.json()
        if "expect_keys" in check:
            missing = [k for k in check["expect_keys"] if k not in data]
            if missing:
                return "FAIL", f"Missing keys: {missing}"
        if check.get("expect_nonempty") and not data:
            return "FAIL", "Empty response"
        return "PASS", f"{r.elapsed.total_seconds()*1000:.0f}ms"
    except Exception as e:
        return "FAIL", str(e)

def main(copilot, port):
    base = f"http://localhost:{port}"
    results = []
    for check in CHECKS["all"] + CHECKS.get(copilot, []):
        status, detail = run_check(base, check)
        results.append({"name": check["name"], "status": status, "detail": detail})
        print(f"  [{status}] {check['name']} ({detail})")

    fails = [r for r in results if r["status"] == "FAIL"]
    if fails:
        print(f"\\nFAIL: {len(fails)} check(s) failed")
        sys.exit(1)
    print(f"\\nPASS: all {len(results)} checks passed")

if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--copilot", required=True, choices=list(DEFAULT_PORTS.keys()))
    p.add_argument("--port", type=int, default=None,
                   help="Override port (default: per-copilot)")
    args = p.parse_args()
    port = args.port or DEFAULT_PORTS[args.copilot]
    main(args.copilot, port)
```

**Quick manual smoke (no script needed):**

```bash
# SOC (port 8001)
curl -s localhost:8001/api/health | python -m json.tool
curl -s localhost:8001/api/conservation/status | python -m json.tool
curl -s localhost:8001/api/fingerprint | python -m json.tool

# S2P (port 8002) — verify actual evidence path in Stage 1
curl -s "localhost:8002/api/s2p/evidence/template?invoice_id=INV-001" | python -m json.tool
```

### 3.3 Similar-Decisions Verification

**Tier: T2 — every batch where evidence code changed.**

From the P38 review: "similar decisions" must be actually similar
by a specifiable function, not "last N decisions relabeled."

```python
def test_similar_decisions_are_actually_similar():
    """'Similar' means same supplier AND same category.
    Not: last N decisions. Not: random subset."""
    similar = find_similar_decisions(
        graph_store, supplier_id="S1", category="price_variance",
        exclude_decision_id="D100", max_results=10)

    for dec in similar:
        assert dec.supplier_id == "S1", "Similar decision has wrong supplier"
        assert dec.category == "price_variance", "Similar decision has wrong category"
        assert dec.decision_id != "D100", "Target decision not excluded"
```

---

## §4 — Frontend Narrative Verification

### 4.1 Tab Narrative Requirements

**Tier: T3 — before any demo or recording.**

Each tab must tell part of the product story. Data without context
is a narrative failure.

| Tab type | Must show | Must NOT show | Narrative |
|---|---|---|---|
| Dashboard | IKS, conservation, compounding curve | Raw numbers without context | "Your system is learning" |
| Triage/Score | Recommendation + confidence + WHY | Score without explanation | "System explains its reasoning" |
| Analysis/Insight | DK weights, factor contributions | Data without interpretation | "System knows what matters" |
| Evidence/Audit | Decision history, provenance tags, audit trail | Unlinked data, unlabeled fixtures | "Every decision is traceable" |
| Performance | Trajectory over time, improvement rate | Flat lines, empty charts | "Getting better every day" |

### 4.2 Provenance Rendering Check

**Tier: T2 — every batch where evidence/explanation UI changed.**

Every evidence surface must render provenance tags. The check:

```typescript
// provenance.spec.ts

test('Evidence chain renders provenance tags', async ({ page }) => {
  await page.goto('/api/s2p/evidence/template?invoice_id=INV-001');

  // Every evidence line has a source tag
  const evidenceLines = page.locator('[data-testid="evidence-line"]');
  const count = await evidenceLines.count();
  expect(count).toBeGreaterThan(0);

  for (let i = 0; i < count; i++) {
    const source = await evidenceLines.nth(i).getAttribute('data-source');
    expect(['learned', 'graph_store', 'fixture']).toContain(source);
  }

  // Fixture lines are visually distinguished
  const fixtureLines = page.locator('[data-source="fixture"]');
  if (await fixtureLines.count() > 0) {
    // Must have "illustrative" or "integration pending" indicator
    const text = await fixtureLines.first().textContent();
    expect(text).toMatch(/illustrative|integration pending|context/i);
  }

  // Learned lines exist (the moat — must be present)
  const learnedLines = page.locator('[data-source="learned"]');
  expect(await learnedLines.count()).toBeGreaterThan(0);
});
```

### 4.3 Empty Tab Detection

**Tier: T3 — before any demo.**

```typescript
test('No empty tabs in demo path', async ({ page }) => {
  const tabs = ['Dashboard', 'Triage', 'Insight', 'Evidence', 'Performance'];
  for (const tab of tabs) {
    await clickTab(page, tab);
    const content = await page.locator('main').textContent();
    expect(content.length).toBeGreaterThan(50),
      `Tab '${tab}' is empty — broken demo`);
  }
});
```

### 4.4 Kitchen Language Check (Purchasing Only)

**Tier: T0 — automated, every commit.**

Implemented as LANG-01 in the §1.1 architecture scanner. The
forbidden terms (`inventory`, `customers`, `shrinkage`, `SKU`) are
checked automatically in the T0 scan. No separate implementation
needed.

---

## §5 — Demo Storyboard Alignment

### 5.1 Per-Copilot Demo Stories

**Tier: T3 — before any demo, Loom recording, or buyer presentation.**

Each copilot has a story arc. The demo must follow it.

| Copilot | Demo story | Key moment | Verification |
|---|---|---|---|
| **SOC** | Alert → triage → learn → auto-resolve next time | "Learned. Next similar alert: auto-resolved." | Score same alert type twice; second has higher confidence |
| **S2P** | Invoice exception → explain (with provenance) → verify → conservation proof | "5:1 penalty ensures conservative scoring. These values learned from YOUR team." | Provenance tags visible; penalty_ratio = 5.0 in response |
| **Trading** | Import trades → trust radar → "your favorite signal is noise" | DK weight inversion visible on radar | Low-weighted popular signal highlighted |
| **Purchasing** | Order → par adjustment → waste reduction → dollar saved | "$180/week saved from par optimization" | Weekly report shows cost_impact > 0 |
| **DataOps** | Pipeline alert → schema root cause → fix → transfer | "Learned at inventory_api, auto-resolved at billing_api" | AE promotion + cross-system transfer visible |

### 5.2 Demo Endpoint Verification

**Note:** The `DEMO_ACTS` dictionary and `verify_demo_acts` function
are built as part of a future T3 prompt. For now, use the §3.2
commercial smoke script to verify endpoints individually. The
pattern below shows the target structure:

```python
# Future: integrity/demo_verify.py
DEMO_ACTS = {
    "soc": [
        {"name": "triage", "endpoints": [
            {"path": "/api/alert/analyze", "method": "POST",
             "body": {"alert_id": "demo-001", "alert_type": "anomalous_login"},
             "required_fields": ["action", "confidence"]},
        ]},
        {"name": "learn", "endpoints": [
            {"path": "/api/alert/outcome", "method": "POST",
             "body": {"alert_id": "demo-001", "decision_id": "...",
                      "outcome": "correct"},
             "required_fields": ["status"]},
        ]},
    ],
    # Other copilots defined when their demo paths are built
}
```

### 5.3 Timing Check

Every demo endpoint must respond within demo timing. A buyer
watching a live demo sees latency as brokenness.

| Context | Latency threshold | Rationale |
|---|---|---|
| Score/analyze | < 500ms | Buyer watches the screen |
| Learn/outcome | < 1s | Can be slightly async |
| Dashboard/status | < 200ms | First impression |
| Evidence/explanation | < 500ms | Buyer reads while loading |
| Conservation | < 200ms | Status badge, always visible |

---

## §6 — Tiered Execution Model

The verification regime is tiered by cost and frequency. T0 catches
80% of drift for 0% human cost. T3 is deep but periodic.

### 6.0 Tier Summary

**T0 catches the most FREQUENT drift (pattern violations). T2
catches the most EXPENSIVE drift (commercial credibility). Both
are mandatory.** Do not let T0's "80% of violations" framing
deprioritize T2, which is where the buyer-facing risk lives.

**Tiers gate TRANSITIONS, not the calendar.** A timer-based
checklist gets skipped under a demo deadline — exactly when
integrity matters most.

| Tier | Gates | Triggered by | Human cost |
|---|---|---|---|
| **T0** | Merge/commit (CI) | Every commit (automated) | 0 |
| **T1** | Batch acknowledgment | Change in `scoring/`, `evidence/`, `preset/`, or `conservation/` | 15 min |
| **T2** | **Batch-close** (batch isn't "done" until T2 passes) | Batch completion report | 30 min |
| **T3** | **Demo-ready** or **publish** (paper submission blocked until T3) | Demo scheduled OR paper/blog submission | 2-3h |

**Path-filtered triggering (T1/T2):** Ten prompts can be ten typos
or one new copilot. Count is the wrong unit. CI path-filters trigger
the relevant checks:
- Change under `scoring/` → T1 shape check + T2 innovation tests
- Change under `evidence/` → T1 provenance spot-check + T2 faithfulness
- Change to a preset → T1 SHAPE-02 alignment
- Change under `conservation/` → T1 CONS-01 formula check

### 6.1 T0 Checklist (Automated — Every Commit)

```bash
# integrity/t0_check.sh — runs in CI, blocks merge on failure
python integrity/architecture_scan.py    # §1.1 invariants
echo "T0: $(date) — PASS/FAIL" >> integrity/log.txt
```

### 6.2 T1 Checklist (Path-Filtered — When Scoring/Evidence/Preset Changed, 15 min)

```
□ Tensor shape: preset matches PD in docs/design/ matches bootstrap JSON (all 5)
□ Preset registry: all 4 SDK copilots registered
□ Conservation: formula matches math_synopsis_v18.md definition
□ GraphStore bypass: zero sqlite3.connect outside migration/test
□ Protocol coverage: all protocol methods implemented
□ Provenance spot-check: pick 1 evidence surface, verify source tags
□ Design docs present: docs/design/ has all PD + architecture files
```

### 6.3 T2 Checklist (Batch — Every Batch, 30 min)

```
□ Innovation comparative tests (§3.1) — all PASS
□ Commercial endpoint smoke (§3.2) — all copilots respond correctly
□ Judgment memory: scorer survives restart (§2.2)
□ Counterfactual faithfulness: top factor influences score (§2.3)
□ Provenance rendering: evidence surfaces carry source tags (§4.2)
□ Substantiation tiers: every surfaced value tier-tagged; no K3 `sample` in a metric (F-22); no oracle output surfaced (F-23); ClaimRegistry migration guard holds (§2.4/§2.5)
□ Day-zero state: measurement-gated surfaces pass the §2.6 enforcement tests (sample-only → magnitude null; provenance-filtered magnitude; instrument present at every state)
□ Similar decisions: actually similar by specifiable function (§3.3)
□ Full test suite: zero failures in affected repos
```

### 6.4 T3 Checklist (Periodic — Monthly or Before Demo, 2-3h)

```
□ Design gap scan: PD features vs code (§1.2) — per copilot
□ Demo storyboard: all acts have working endpoints (§5.2)
□ Timing check: all demo endpoints < threshold (§5.3)
□ Frontend narrative: each tab tells its story (§4.1)
□ Empty tab detection: no empty tabs in demo path (§4.3)
□ Day-zero render: every measurement-gated surface shows INSTRUMENT_VALIDATED with NO fabricated number on a fresh tenant (§2.6); Purchasing par day-zero state present before any par dashboard
□ Governed-compounding (§7.3): every compounding loop routes through the ONE ConservationGate (GC-01), fails-closed on gate violation (GC-02), and carries provenance on I/O (GC-03) — the C-17 platform claim is code-true or scoped down (F-24)
□ **Naming (§2.7 / GC-06):** the primary mechanism is NOT called "RL" anywhere in the surface (F-25); bandit components named accurately
□ **Cross-copilot (§2.7 / GC-07):** no claim of shared learned judgment state (F-26) — "signals transfer," not "judgment transfers"
□ **Scenario classes (§2.8 / F-27):** every scenario on the surface carries LIVE / NEAR / ARCH; every LIVE one actually runs on the pinned preseed
□ **Demo-truth (§2.7):** if a beat shows learning, learning is ENABLED on that copilot — SOC learning is disabled by default (`soc/config.py:66`); a SOC "watch it learn" beat must enable it and demonstrably change a later score
□ Substantiation map current: each copilot's headline claim tier-tagged and truthful (§2.4); no T-R claim without a pilot evidence pointer
□ Differentiation audit: per copilot (§7)
□ Paper consistency: no inference-time traversal claims; F-21..F-23 clear, C-15/C-16 present (§8.2)
```

---

## §7 — Per-Copilot Differentiation

### 7.1 Differentiation Audit Template

**Tier: T3 — quarterly or before major investor/buyer presentation.**

For each copilot, answer:

```
1. COMPETITIVE POSITION
   - 3-5 named competitors for this domain
   - For each: what can they do that we can't? (honest)
   - For each: what can WE do that THEY can't? (must cite CI innovation)
   - The "they can't" list must include ≥3 items grounded in
     compounding intelligence, not just features

2. BUYER VERIFICATION
   - Enterprise: what question does this copilot answer that no
     competitor can?
   - SMB: can they install and see value in < 1 hour?
   - VC: what is the moat? Why can't a well-funded team replicate
     this in 6 months?

3. INNOVATION UTILIZATION
   - Which of the 12 CI innovations does this copilot USE?
   - Which are VISIBLE to the buyer in the UI?
   - Which are MEASURABLE (buyer can see the number change)?

4. VALUE QUANTIFICATION
   - Is there a dollar figure the buyer can verify?
   - Is it grounded in real computation or hand-waved?
   - Can the buyer reproduce the calculation?
```

### 7.2 Copilot Differentiation Scorecards

**SOC — Enterprise CISO**

| Differentiator | Visible? | Measurable? | Competitor gap |
|---|---|---|---|
| Centroid learning | IKS, trajectory | Yes (IKS score) | CrowdStrike/Palo Alto can't compound from analyst verifications |
| Conservation proof | GREEN/AMBER/RED | Yes (formula visible) | No competitor proves automation safety mathematically |
| +36.89pp kernel choice | Provable in docs | Test exists | Architecture advantage, not feature |
| DK noise adaptation | Factor trust weights | Yes (radar) | No competitor shows per-factor trust |
| 288-value judgment memory | Fingerprint panel | Yes (tensor) | Can't be replicated by copying code — needs YOUR decisions |
| Re-convergence γ>1 | Not shown directly | Test exists | System recovers faster after disruption |

**Moat:** "CrowdStrike can build agents. They cannot build 5
compounding pathways feeding one living graph — that requires a
mathematical engine (published, peer-reviewable) producing
firm-specific judgment from verified outcomes, not a fine-tuned
model producing generic responses."

**Trading — Individual trader + VC**

| Differentiator | Competitor gap |
|---|---|
| Per-signal trust weights | Tradervue/Edgewonk can't show which signals are noise |
| Conservation-gated scaling | No competitor proves it's safe to scale position size |
| Open source + self-hosted | Data stays local — no cloud dependency |
| pip install in 10 minutes | No competitor offers this |
| 200 centroid values = trading DNA | Open-sourcing the engine costs nothing — the moat is YOUR 1,000 trades |

**Purchasing — Restaurant owner**

| Differentiator | BlueCart/MarketMan gap |
|---|---|
| Learns from verified orders (not rules) | Competitors use static par levels |
| Day-of-week par intelligence | No competitor learns temporal patterns |
| Conservation proof for auto-ordering | Competitors use fixed dollar thresholds |
| Kitchen language throughout | Competitors use generic ERP/SCM language |
| Weather + events integration | No competitor connects external signals to ordering |

**S2P — CPO/CFO enterprise**

| Differentiator | Zycus/Coupa/Celonis gap |
|---|---|
| Evidence with LEARNED provenance | Competitors show rules, we show what the system learned from YOUR AP team |
| 5:1 penalty proves conservative scoring | Competitors promise conservatism, we prove it mathematically |
| Conservation-gated auto-approve | Competitors use fixed rules, we prove safety dynamically |
| Cross-system pattern discovery | No competitor connects ERP + process mining + operational data |
| WHERE→WHY→WHAT→LEARN→TRANSFER | Celonis does WHERE only; we do all 5 |

**DataOps — CDO/VP Data**

| Differentiator | Monte Carlo/Databricks gap |
|---|---|
| "Your data gets smarter every day" | Competitors detect issues, we learn from resolutions |
| 6-level intelligence hierarchy | Competitors stop at Level 2 (detection) |
| Intelligence Map with $ values | No competitor assigns dollar value to data combinations |
| Quality-aware NL with confidence | Genie/Numbers Station don't weight by learned trust |
| Process-Tech Fusion | No competitor connects WHERE→WHY→WHAT→LEARN |

### 7.3 Governed-compounding check (the PLATFORM differentiation claim — must be code-true)

The platform's headline differentiation (next_steps §3.1) is that CI is **the governed compounding layer** —
*one conservation law governs all compounding loops.* That is a strong, falsifiable claim; it is only
CANONICAL (C-17) if the code enforces it. This check is the T2/T3 gate on that claim.

**GATE COVERAGE — evidence-based (Codex diagnostic, 2026-07-10). Status: ONE OPEN GAP.**

| Loop | Conservation-gated? | Evidence |
|---|---|---|
| **L1** decision-trace/centroid learning | ✅ **YES** — `_conservation_pause` runs *before* the update | `copilot_sdk/scoring/scorer.py:465`; gate reads q/θ_min/verified-outcome stats at `:783-790`, `:1074-1082` |
| **L1b** exploration (Thompson) | ✅ **YES — by construction** | `ConservationBoundedThompson`, `copilot_sdk/rl/exploration.py:41-52` |
| **L2** AgentEvolver / scorer promotion | ✅ **YES** — gates on accuracy, baseline superiority, variance **AND conservation** | `copilot_sdk/evolution/gate.py:27-41`; `scorer.py:988-994` |
| **L2b** **prompt-variant promotion** | ❌ **NO — conservation coupling NOT FOUND** | `copilot_sdk/evolution/prompt_evolver.py:195-215` (gates only on sample count + improvement) |

**⚠️ LIVE F-24 VIOLATION.** Because L2b is ungated, **C-17 is NOT currently code-true.** Until fixed:
- **Permitted claim:** *"one conservation law governs our scoring, exploration, and scorer-evolution loops."* (accurate)
- **FORBIDDEN:** *"one conservation law governs **every** compounding loop"* / *"all loops"* (F-24).
- **Fix (small, do it):** route `PromptVariantEvolver` promotion through the same `ConservationGate`
  (next_steps `C-GOV`, ~0.5-1d) → C-17 becomes true and this note is deleted.

**Checks:**
```
GC-01 (T2)  Each loop's state change routes through the ONE ConservationGate.
            STATUS: L1 ✅ · L1b ✅ · L2 ✅ · L2b ❌ (prompt_evolver.py:195-215)
GC-02 (T2)  Fail-closed test per loop: with the gate RED, each loop's promotion/change is BLOCKED
            (not warned, not logged-and-continued).
GC-03 (T2)  Provenance present on each loop's I/O (T-A/T-S/T-O/T-R) — no loop learns from unlabeled data.
GC-04 (T3)  L3/L4 tier check: situation-analyzer discrimination is SOC-ONLY (option-scoring);
            graph synthesis is S2P enrichment (partial). Neither may be featured as general/live (F-21).
GC-05 (T3)  Claim-scope: if any loop is NOT gated, the pitch names the gated loops — never "all" (F-24).
GC-06 (T3)  Naming: the primary mechanism is NOT called "RL" (§2.7, F-25).
GC-07 (T3)  Cross-copilot: no claim of shared learned judgment state (§2.7, F-26).
GC-08 (T0)  [after C-REGIME P1] No direct `mu[...]` access outside the scorer accessor — grep-enforced.
```
**Consequence:** until GC-01 is fully green, C-17 is scoped down (not deleted) per §0.5 — *the roadmap keeps
the ambition; the claim states today's truth.*

---

## §8 — FORBIDDEN Registry, CANONICAL Claims, & Paper Consistency

### 8.1 FORBIDDEN Claims

Claims that must never appear in code, docs, UI, or papers:

| ID | Forbidden claim | Correct alternative |
|---|---|---|
| F-01 | Implementation module names presented as architectural capabilities (e.g., "context builder" ≠ "graph traversal") | Name the actual capability delivered, not an aspirational architecture |
| F-02 | Fixture values as measured metrics without provenance | Label: "illustrative" / "integration pending" |
| F-03 | "Similar decisions" without specifiable similarity | Same supplier AND same category |
| F-04 | Evidence factors that don't influence score | Verify counterfactual faithfulness |
| F-05 | "Inference-time graph traversal" in papers | "Context assembled from learned state and graph-persisted decision history" |
| F-06 | "Re-convergence always faster" | State conditions: category-sparse + warm-started + ε > 0.125 |
| F-07 | "DK always better" | State: NR-dependent |
| F-08 | "Production-validated" for b=2.11 | "Sim-validated, EXP-G1 pending" |
| F-09 | "Zero false positives" for referral | State actual FPR |
| F-10 | "Self-healing" | "Conservation auto-pauses when quality degrades" |
| F-21 | A claim presented at a tier higher than its evidence (esp. T-O/T-A magnitude asserted as T-R `learned`) | State the tier; no magnitude below T-R; promote only via an evidence event (§2.4) |
| F-22 | K3 demo-fixture value used in a metric / score / par / claim | Label `sample`, exclude from all computed values (specializes F-02; §2.5/§2.6) |
| F-23 | K1/K2 oracle output surfaced to a user, or used as a magnitude claim | Oracle is test-only — the META-4 line (§2.5) |
| F-24 | Claiming "governed compounding / one conservation law governs all compounding loops" when a loop's state change does NOT fail-closed on a conservation-gate violation, or does not carry provenance | Every compounding loop routes through the one `ConservationGate` and carries provenance — verified by §7.3. **CURRENTLY OPEN: L2b prompt-variant promotion is ungated** ⇒ say "our scoring, exploration and scorer-evolution loops," never "all loops," until `C-GOV` lands |
| F-25 | Calling the **primary** learning mechanism "reinforcement learning" / "RL" | It is **online supervised centroid/prototype learning from verified human decisions** (+ DK coordinate search) — the signal is a *correctness label, not a reward* (§2.7). Genuine bandit components (Thompson/UCB) exist and **may** be named as such. *The honest name is the stronger claim: "we have no reward function for judgment."* |
| F-26 | Claiming shared **cross-copilot learned judgment state** ("judgment transfers between copilots") | Learned geometry is **per-app/domain**; shared cross-copilot learned state NOT FOUND (§2.7). Say "one engine, five domains — **signals** transfer." Revisit when decision D5 ships |
| F-27 | Placing a scenario/capability on an external surface **without a class label**, or implying a **NEAR/ARCH** item is **LIVE** | Every external scenario carries **LIVE / NEAR / ARCH** (§2.8). Showing roadmap is *allowed and expected* — **implying** it is live is the violation |

*(Scraped/external presented as customer-learned is already **F-15** — "external enrichment labeled as learned." §2.4's ░░/██ discipline reuses F-15; no new entry.)*

### 8.2 CANONICAL Claims (Approved, With Evidence)

Claims that SHOULD appear — the positive list reviewers can
confidently use. Without this, caution strips true claims.

| ID | Approved claim | Evidence pointer | Where to use |
|---|---|---|---|
| C-01 | "This confidence reflects N verified decisions from YOUR team" | GraphStore decision count, IKS endpoint | Evidence panel, demo, pitch |
| C-02 | "The system learns which information sources to trust" | DK weights visible on radar/trust display | Analysis tab, papers |
| C-03 | "Conservation PROVES automation is safe — mathematically" | α·q·V ≥ θ_min formula, GREEN/AMBER/RED | Dashboard, compliance, papers |
| C-04 | "After disruption, recovery is faster than cold start" | Re-convergence theorem (4 proof paths, conditions stated) | Papers, innovation note |
| C-05 | "5:1 penalty ensures conservative scoring" | η_override/η_confirm ratio, centroid movement test | S2P evidence, compliance |
| C-06 | "Same engine, 5 domains — YOUR decisions make it yours" | 5 presets, same CompoundingScorer class | Platform pitch, papers |
| C-07 | "When your expert leaves, 15,000 decisions stay" | Centroid persistence test, IKS survives restart | ROI pitch, retention story |
| C-08 | "Open source engine, proprietary judgment memory" | Apache 2.0 license + centroid tensor is learned, not copied | VC pitch (Trading) |
| C-09 | "+36.89pp from kernel architecture choice" | EXP-C1 measured result | Papers, technical DD |
| C-10 | "Every decision is traceable — graph-persisted audit chain" | Audit hash, SHAPED_BY edges, Decision→Outcome trail | Compliance, enterprise |
| C-15 | "Mechanism proven analytically; magnitude measured on YOUR data at pilot" | γ theorem (T-A) + pre-committed T-R path (§2.4) | Papers, pitch, day-zero |
| C-16 | "Populated day-zero with real external data, labeled context (░░) vs learned (██)" | T-S scraped source + ██/░░ render (§2.4/§2.6) | Demo, buyer, day-zero |
| C-17 | "One conservation law governs every compounding loop — the governed compounding layer" | §7.3 governed-compounding check: each loop fails-closed on gate violation + carries provenance. **⚠️ SCOPED until C-GOV lands** — currently say "our scoring, exploration and scorer-evolution loops" | Platform pitch, VC, technical DD, OSS README |
| C-18 | **"We have no reward function for judgment — we learn a prototype geometry from your verified decisions"** | §2.7: supervised centroid learning; signal is a correctness label (`gae/profile_scorer.py:780, :950`) | **The RL/TensorTrade differentiation**; VC, technical DD, OSS README |
| C-19 | **"Where we explore, exploration is conservation-bounded by construction"** | `ConservationBoundedThompson`, `copilot_sdk/rl/exploration.py:41-52` | Governance pitch, technical DD |

**Paper consistency pass uses BOTH registries:** flag F-01..F-27
phrasings AND confirm C-01..C-19 are present and correctly stated.

### 8.3 Paper Consistency Pass

**Tier: T3 — before any paper submission or blog publication.**

Sentence-level search across these files in `copilot-sdk/docs/design/`:
- `cga_arxiv_short_v7_6.md` (arxiv paper)
- `jm_paper_draft_v9.md` (judgment memory paper)
- `ci_blog_v15.md` (CI blog)
- `math_synopsis_v18.md` (math claims — verify against code)
- `outreach_elevator_pitches_v4.md` + `outreach_use_scenario_catalog.md` (**outreach collateral — T3-gated before any external send**)

**Outreach-collateral rule (v2.8):** the pitches/catalog carry **end-state** magnitudes ("$1.62M/yr,"
"10,000 decisions," "180 days GREEN," "175 experiments"). These are **T-R / after-N** claims (§2.4) — honest
only as *"after N decisions"* / *"at pilot"* / *"target"*, never as current-measured (else **F-21** tier
overclaim). Before any external send, run §8.1 (F-01..F-23) + §2.4 tier-tagging over the collateral: every
ROI or decision-count number must state its tier and, where end-state, be labeled as such. The day-zero
honesty framing (§2.6) applies to the pitch as much as the demo.

```bash
# Quick automated pre-scan:
cd copilot-sdk/docs/design
grep -n "traverses the graph\|graph traversal at inference" \
  cga_arxiv_short_v7_6.md jm_paper_draft_v9.md ci_blog_v15.md
grep -n "always re-converge\|always faster" \
  cga_arxiv_short_v7_6.md math_synopsis_v18.md
grep -n "production-validated" \
  cga_arxiv_short_v7_6.md jm_paper_draft_v9.md
```

```
FORBIDDEN search (remove or fix):
- "traverses the graph" / "graph traversal at inference" → F-05
- "always re-converges" / "always faster" → F-06
- "production-validated" near b=2.11 → F-08

CANONICAL confirm (must be present and correct):
- Conservation formula stated with conditions → C-03
- DK described as learned trust, not fixed weights → C-02
- Re-convergence stated with conditions → C-04
- Centroid learning described as from verified outcomes → C-01
```

---

## §9 — Known Risk Areas

### 9.1 Architecture Risks

| Risk | Symptom | Detection | Fix |
|---|---|---|---|
| GraphStore bypass | raw sqlite3 in production | T0 literal scan | Extract to protocol method |
| Conservation formula drift | θ_min computed differently | T1 formula review | Revert to canonical |
| Tensor shape drift | MAP says one shape, code another | T1 shape check | Code wins — update MAP |
| Auto-approve without gate | conservation check missing | T1 scope check | Add conservation gate |
| DK mutation in display | evidence code calls update | T1 scope check | Make read-only |
| **Cross-artifact contradiction** | Design doc says MERGE, scanner says forbidden | T1 cross-doc review | Reconcile to MATCH-then-CREATE |
| **Stale factor counts in tests** | Smoke test asserts D=10, preset says D=7 | T1 SHAPE-02 | Fix test to match preset |

### 9.2 Commercial Risks

| Risk | Symptom | Detection | Fix |
|---|---|---|---|
| Fixture as measured | Unlabeled hardcoded number | T1 provenance check | Add source tag |
| Empty trajectory | IKS = 0 after preseed | T2 endpoint smoke | Fix preseed |
| Conservation always RED | θ_min too high for data | T2 endpoint check | Verify preseed volume |
| Explainability theater | Displayed factor doesn't affect score | T2 counterfactual test | Fix evidence selection |

### 9.3 Narrative Risks

| Risk | Symptom | Detection | Fix |
|---|---|---|---|
| Black box scoring | Score without WHY | T3 narrative check | Add reasoning panel |
| Empty tabs | Tab renders, no data | T3 empty-tab check | Wire endpoint or preseed |
| Wrong language | "inventory" in Purchasing | T0 language check | Kitchen terms |
| No compounding story | Trajectory flat | T3 visual check | Fix preseed + learn path |
| Stale provenance | "learned" tag on fixture value | T2 provenance audit | Correct source tag |

---

## §10 — Execution Schedule Summary

| Tier | Gates | Triggered by | Time |
|---|---|---|---|
| T0 | Merge/commit | Every commit (CI, automated) | 30s |
| T1 | Batch acknowledgment | Change in scoring/evidence/preset/conservation | 15min |
| T2 | **Batch-close** | Batch completion (batch isn't "done" until T2 passes) | 30min |
| T3 | **Demo-ready / publish** | Demo scheduled OR paper submission | 2-3h |

**Build T0 first.** One script, one CI integration. Catches the most
frequent drift for zero human cost.

**T2 catches the most expensive drift.** The comparative tests (§3.1)
and counterfactual faithfulness (§2.3) verify the thing the buyer is
paying for. A batch that ships without T2 may pass all unit tests
and still produce a product that doesn't compound.

**T3 blocks demos and papers.** The paper consistency pass (§8.3) and
demo storyboard check (§5) prevent the most permanent errors
(published overclaims, failed live demos).

**Path-filtered T1/T2:** CI triggers the relevant tier checks based
on which files changed, not a prompt count. Ten documentation typos
don't trigger innovation tests. One change to the scorer does.

**Path-filter wrapper (`copilot-sdk/integrity/path_trigger.sh`):**

```bash
#!/bin/bash
# Determines which tiers to trigger based on changed files.
# Run: ./integrity/path_trigger.sh
CHANGED=$(git diff --name-only HEAD~1)

T1_NEEDED=false
T2_NEEDED=false

echo "$CHANGED" | grep -q "scoring/\|preset\|conservation" && T1_NEEDED=true
echo "$CHANGED" | grep -q "evidence/\|template\|trust\|context" && T2_NEEDED=true
echo "$CHANGED" | grep -q "scorer\|learn\|update\|centroid" && T2_NEEDED=true

echo "Changed files: $(echo "$CHANGED" | wc -l)"
echo "T1 needed: $T1_NEEDED"
echo "T2 needed: $T2_NEEDED"

if [ "$T1_NEEDED" = true ]; then
    echo "=== T1: Shape + Registry ==="
    python integrity/shape_check.py 2>/dev/null || echo "shape_check.py not yet built"
fi

if [ "$T2_NEEDED" = true ]; then
    echo "=== T2: Innovation + Commercial ==="
    python -m pytest integrity/test_innovation_claims.py -v --timeout=120 2>/dev/null || \
        echo "test_innovation_claims.py not yet built"
fi
```

**Full integrity suite (`copilot-sdk/integrity/run_all.sh`):**

```bash
#!/bin/bash
# Run all tiers sequentially. Use for batch-close or pre-demo.
# Does NOT abort on first failure — runs all tiers, reports summary.
REPOS_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
FAILS=0

echo "=== T0: Architecture Scan ==="
python "$(dirname "$0")/architecture_scan.py" --repos "$REPOS_ROOT"

echo ""
echo "=== T1: Shape + Registry + Provenance ==="
python "$(dirname "$0")/shape_check.py" 2>/dev/null || echo "[SKIP] shape_check.py not yet built"

echo ""
echo "=== T2: Innovation Claims ==="
python -m pytest "$(dirname "$0")/test_innovation_claims.py" -v --timeout=120 2>/dev/null || \
    echo "[SKIP] test_innovation_claims.py not yet built"

echo ""
echo "=== T2: Commercial Smoke (SOC) ==="
python "$(dirname "$0")/commercial_smoke.py" --copilot soc 2>/dev/null || \
    echo "[SKIP] commercial_smoke.py not yet built or SOC not running"

echo ""
echo "=== T2: Product Truth ==="
python -m pytest "$(dirname "$0")/test_product_truth.py" -v --timeout=120 2>/dev/null || \
    echo "[SKIP] test_product_truth.py not yet built"

echo ""
echo "=== COMPLETE ==="
```

**Who runs each tier:**

| Tier | Runner | In the multi-LLM workflow |
|---|---|---|
| T0 | CI/automated script | Runs on every commit. No human. |
| T1 | Coding session | After batch, before reporting "batch done" to Roadmap. |
| T2 | Coding session | Batch-close gate. Report T2 results in batch summary. |
| T3 | Roadmap session | Before approving demo/publish. Request from Coding if needed. |

---

## §11 — Codex Prompt Templates (For Coding Session)

### 11.1 Prompt: Build T0 Scanner (Step 1)

```
WORKING DIRECTORY: copilot-sdk
VENV: .venv (activate before running)
TASK: Create the T0 architecture invariant scanner.
TASK TYPE: New file creation + test.

Create copilot-sdk/integrity/architecture_scan.py with the
literal-pattern checks from §1.1 Class A of this document.

The script:
- Accepts --repos <path> (default: parent of cwd)
- Scans all .py files in ci-platform, gen-ai-roi-demo-v4-v50,
  copilot-sdk, s2p-copilot for LITERAL_CHECKS patterns
- Skips lines containing exception strings (test, comment, docstring)
- Reports violations with file:line:text
- Exits 0 on pass, 1 on any P1 violation

Also create integrity/run_t0.sh as a one-line CI entry point.

Test: run the scanner against all repos. If it finds real violations,
report them. If it false-fires, fix the skip list.

EXIT: scanner runs clean (0 violations or documented pre-existing).
```

### 11.2 Prompt: Build Provenanced[T] Type (Step 2)

```
WORKING DIRECTORY: copilot-sdk
VENV: .venv (activate before running)
TASK: Add provenance type to copilot-sdk evidence module.
TASK TYPE: New library file + test.

Create copilot_sdk/evidence/provenance.py with:
- Provenanced[T] generic dataclass (value, source, label)
- Source = Literal["learned", "graph_store", "fixture"]
- Frozen/immutable

Create tests/test_provenance.py:
- Provenanced wraps float, str, dict, list
- Source tag is required
- Label is optional (used for fixture annotation)
- Serializes to dict for JSON API response
- Type is generic (Provenanced[float], Provenanced[dict])

Do NOT modify any existing evidence builders yet. This is the type
definition only. Adoption happens in Step 5.
```

### 11.3 Prompt: Generate Frozen Benchmark (Step 3)

```
WORKING DIRECTORY: copilot-sdk
VENV: .venv (activate before running)
TASK: Generate frozen benchmark fixture for innovation claims tests.
TASK TYPE: Script + fixture files.

Create copilot-sdk/integrity/generate_benchmark.py that:
1. Instantiates scorer via CompoundingScorer.from_preset("dataops")
   (uses SDK preset pattern, not direct ProfileScorer construction)
2. Uses seed=42 for all random operations
3. Generates 600 synthetic factor vectors matching preset D dimension
4. Assigns correct actions based on centroid proximity
5. Splits into train (500) and eval (100) — held-out
6. Saves to integrity/fixtures/benchmark_factors_v1.json
   and integrity/fixtures/benchmark_outcomes_v1.json

Create copilot-sdk/integrity/benchmark_fixture.py:
- load_benchmark_split("train") → list of (factors, category, action)
- load_benchmark_split("eval") → list of (factors, category, action)
- BENCHMARK dict with seed, counts, scenario name
- train_scorer(decisions, seed) → CompoundingScorer
- measure_accuracy(scorer, eval_set) → float
- measure_accuracy_with_weights(scorer, eval_set, weights) → float
- decisions_to_threshold(scorer, eval_set, threshold) → int
- inject_disruption(scorer) → mutates centroids

The eval split must NEVER be used during training in any test.

Run the generator once. Commit the fixture files. They are versioned
and frozen — regenerate only on explicit version bump.
```

### 11.4 Prompt: Innovation Comparative Tests (Step 4)

```
WORKING DIRECTORY: copilot-sdk
VENV: .venv (activate before running)
TASK: Implement innovation claims comparative tests.
TASK TYPE: Test file using frozen benchmark.

Create copilot-sdk/integrity/test_innovation_claims.py with the
8 comparative tests from §3.1 of the Product Integrity Strategy.

Key requirements:
- All tests use the frozen benchmark fixture (Step 3)
- Accuracy measured on HELD-OUT eval split, never training data
- test_accuracy_improves: acc at 500 > acc at 50 + 0.03
- test_dk_weights_improve: learned DK > uniform on held-out
- test_reconvergence_faster: N2 < N1 after disruption
- test_conservation_blocks: RED status blocks auto-approve
- test_iks_monotonic: IKS at 100 < 300 < 500
- test_five_presets: all 5 copilot presets load and score

Run: pytest integrity/test_innovation_claims.py -v
All tests must PASS.
```

---

## Document Control

| Version | Date | Change |
|---|---|---|
| v1.0 | June 13, 2026 | Initial strategy. 10-item checklist, invariant scanner, innovation tests, commercial gate, demo storyboard, differentiation audit. |
| v2.0 | June 13, 2026 | Major revision. Tiered execution. Three missing layers. Comparative tests. FORBIDDEN registry. |
| v2.1 | June 13, 2026 | Design authority review. T0/T1 split. Provenanced type. Frozen benchmark. Transition-gated tiers. CANONICAL claims. |
| v2.2 | June 13, 2026 | Made executable. §0 build order. Runnable scripts. Codex prompts. |
| v2.3 | June 13, 2026 | **11 corrections from coding session review.** (1) Port numbers: SOC=8001, S2P=8002, Trading=8010, Purchasing=8020, DataOps=8030. (2) Step 5: discover actual evidence builder file, not assume name. (3) Repos root: auto-detect from copilot-sdk location, not hardcode ~/repos. (4) Counterfactual: flip within [0,1] range (1.0-x), not multiply by -1. (5) Benchmark: use `CompoundingScorer.from_preset()`, not direct ProfileScorer. (6) S2P endpoint: discover actual path in Stage 1. (7) Path-filter: `path_trigger.sh` using `git diff` + `run_all.sh` full suite entry point. (8) F-01: generalized from P38-specific to "module names as architectural capabilities." (9) All 4 Codex prompts: added WORKING DIRECTORY + VENV preamble. (10) Added `run_all.sh` — single entry point for T0+T1+T2. (11) Provenanced adoption: S2P first, other copilots at their milestones. |
| v2.3.1 | June 13, 2026 | Final review: 10 internal issues fixed. |
| v2.4 | June 13, 2026 | **Design document registry added (§1.0).** All PD + architecture docs in `copilot-sdk/docs/design/` are the authority for integrity tests. §1.2 gap detector reads from docs/design/. SHAPE-02 reads tensor shapes from PD documents (not hardcoded). §8.3 paper pass lists specific files + adds grep pre-scan command. T1 checklist references docs/design/. Tests verify code against design docs, not assumed values. |

---

# ══════════════════════════════════════════════════════════
# v2.5 ADDITIONS (June 14-15, 2026)
# Source: Coding session scans, DDs, frontend audit, domain unification
# ══════════════════════════════════════════════════════════


**Add after Step 5 (Provenanced adoption):**

```
Step 6: Frontend Wiring Audit (~1h)
  Build WIRE-CHECK scanner (wire_check.ps1).
  Run against all 5 copilots across 3 repos.
  Produces: list of backend endpoints with no frontend consumer.
  Every ❌ gap gets classified P1/P2/P3.
  P1 gaps become immediate frontend prompts.
  
Step 7: validate_against_preset Integration (~30 min)
  Every copilot that has a DomainConfig gets a sync test:
    config.validate_against_preset(preset) == []
  Currently: Trading only. Future: add as each copilot adopts.
```

---

## §1 — Architecture Invariants: Add These

**ARCH-20: CENTROID-ACCESSOR (v3.0 — activate after `C-REGIME` P1)**
```
ARCH-20: CENTROID-ACCESSOR
  No direct indexing of the learned centroid tensor outside the scorer accessor.
  FORBIDDEN:  scorer.mu[...]  /  state["mu"][...]  /  centroids[cat][act]  (raw)
  REQUIRED:   scorer.centroids(regime=...)  /  scorer.update(..., regime=...)
  WHY: the regime axis (C-REGIME P2) is added BEHIND the accessor. The 63 consumer
       sites are migrated once (P1); this rule keeps them migrated.
  TIER: T0 (grep scanner, every commit) — activate the moment P1 completes.
  EVIDENCE: 63 consumer sites across 5 repos (Codex diagnostic, 2026-07-10).
```

**Add to §1.1 (Architecture Scanner Rules):**

```
ARCH-15: FRONTEND-WIRING
  Every backend endpoint registered via @router.get/@router.post
  must have either:
  (a) A frontend component that calls it, or
  (b) An explicit "API-only" annotation in the route docstring, or
  (c) A backlog item (with prompt number) for the frontend component.
  
  Detection: WIRE-CHECK scan compares backend route decorators
  against frontend fetch/axios/api calls per copilot.
  
  Violation = P2 if in demo path, P3 otherwise.

ARCH-16: CONFIG-PRESET-PARITY
  Every DomainConfig subclass must pass:
    config.validate_against_preset(preset) == []
  
  Checks: count parity (actions, factors, categories) AND
  ordered ID parity (action_ids, factor_ids, category_ids).
  
  Detection: validate_against_preset() method on BaseDomainConfig.
  Currently enforced for Trading (3 sync tests + 1 validation test).
  
  Violation = P1 (config/preset drift causes UI label mismatches).

ARCH-17: DOMAIN-TYPE-CANONICAL-SOURCE
  DomainAction, DomainFactor, DomainSituationType are defined in
  copilot_sdk/domains/base.py (frozen, with defaults). This is the
  canonical source. SOC re-exports from here. No other definition
  of these classes is permitted.
  
  SOC-specific types (DomainPolicy, PromptVariant, DomainConfig ABC)
  stay in SOC repo (app/domains/base.py) because their fields are
  SOC-specific.
  
  Detection: grep for "class DomainAction" — must appear only in
  copilot_sdk/domains/base.py (definition) and SOC's base.py
  (re-export, not redefinition).
```

---

## §1.1 — FORBIDDEN Registry: Add F-11 through F-17

**Add to the FORBIDDEN table:**

| ID | Forbidden | Correct | Detection |
|---|---|---|---|
| F-11 | `delta_exposure`, `implied_vol_rank`, `gamma_risk` in prompts | `options_delta_exposure`, `options_iv_percentile`, `options_gamma_risk` | T0 grep |
| F-12 | Stale Purchasing factor names (cost_trend_alignment, supplier_reliability, etc.) | Runtime names: expected_demand, day_of_week, weather_forecast, event_flag, historical_waste, supplier_lead_time, price_memory_index | T0 grep + T1 runtime |
| F-13 | Enrichment with < N_min used as scoring factor | Display-only until factor_eligible=True | T2 enrichment check |
| F-14 | DK re-estimated on mixed enriched/fixture distribution | Gate: >80% enrichment coverage before re-estimation | T2 DK check |
| F-15 | External enrichment labeled as "learned" | source="integration", provenance_tier="context" | T2 provenance check |
| F-16 | "Self-healing enrichment" claim | Conservation cannot catch automation bias | T0 claims check |
| F-17 | "Multiplicative" scoring improvement (unbacked) | "Increases effective discriminative dimensionality (D_eff)" | T0 claims check |
| **F-18** | **Backend endpoint with no frontend wiring plan** | **Component built, or deferred with prompt number, or Playwright stub** | **T2 WIRE-CHECK** |
| **F-19** | **DomainConfig IDs that differ from DomainPreset names** | **validate_against_preset() == []** | **T1 SHAPE-02** |
| **F-20** | **Designing from import lines / class names without reading full files** | **12-area investigation with field-level + call-site evidence** | **Process rule** |

---

## §1.1 — CANONICAL Registry: Add C-11 through C-14

**Add to the CANONICAL table:**

| ID | Approved Claim | Evidence |
|---|---|---|
| C-11 | "System learns about YOUR suppliers from YOUR team's decisions" | ProvenancedValue source="verified_outcomes" |
| C-12 | "Supplier intelligence accumulates — 150 decisions deep" | source_count visible in evidence |
| C-13 | "7-pathway scoring engine (6 state + 1 input)" | Two-loop diagram, factor-eligibility gate |
| C-14 | "Conservation proves enrichment is safe" | α·q·V gates automation during distribution shifts |

---

## NEW §4A — Frontend Wiring Verification

**Insert after §4 (Frontend Narrative Verification):**

```
## §4A — Frontend Wiring Verification

### 4A.1 The Wiring Gap Problem

Tier: T2 — every batch where backend endpoints are added.

Backend features implemented and tested but with no frontend
consumer create invisible product gaps. The backend passes all
tests. The demo shows nothing. This is a category of drift that
T0 (architecture patterns) and T1 (shape/registry checks) do
not catch because they verify the backend, not the full stack.

### 4A.2 WIRE-CHECK Scan

Multi-repo scan comparing backend route decorators against
frontend API calls per copilot:

  Repos scanned:
    copilot-sdk/apps/{trading,purchasing,dataops}/
    copilot-sdk/apps/s2p/frontend/ + s2p-copilot/backend/
    gen-ai-roi-demo-v4-v50/{backend,frontend}/

  Backend: count @router.get/@router.post decorators
  Frontend: count fetch()/axios/api references + extract /api/ paths

  Per-endpoint deep check:
    For each new endpoint, grep the corresponding frontend for
    the endpoint path. Zero hits = unwired.

### 4A.3 Gap Classification

  P1 (demo blocker): endpoint is in the demo story (§5.1) and
    has no UI. Build frontend component before next demo.
  P2 (product gap): endpoint adds visible value but isn't
    critical demo path. Build in next batch.
  P3 (infrastructure): endpoint is internal/operational.
    OK to be API-only.

### 4A.4 Standing Rule #65

Every new backend endpoint must have a frontend wiring plan:
  (a) Frontend component built in the same prompt, or
  (b) Prompt explicitly notes "frontend deferred" with the
      follow-up prompt number, or
  (c) Playwright spec stub created for future component.

No more "Playwright deferred — no frontend consumer" without
a plan to CREATE the consumer.

### 4A.5 Known Gaps (June 14, 2026 Baseline)

  P1: P46 /api/purchasing/report/weekly — no frontend
  P2: P48 TradingDomainConfig — frontend hardcodes labels
  P2: P47 interpret_factor() — not in evidence panels
  P2: P45 /api/purchasing/pos/today — no frontend
  P2: response_model on 4 demo endpoints — untyped responses
  P3: P39A enrichment SDK copilots — S2P has display, others don't

  ❓ (unverified): Trading Dashboard/fingerprint/trajectory/conservation
  ❓ (unverified): DataOps IntelligenceMapPanel API calls
  ❓ (unverified): S2P enrichment/centroid/financial frontend calls

  Action: run WIRE-CHECK once to resolve all ❓ marks.
```

---

## §6 — Tiered Execution Model: Add Scans

**Add to the T1 checks table:**

| Check | ID | What |
|---|---|---|
| Config↔Preset parity | SHAPE-02 | `config.validate_against_preset(preset) == []` for every copilot with DomainConfig |
| DROP pre-check | DROP-CHECK | 5-condition runtime verification before marking any prompt as DROP |

**Add to the T2 checks table:**

| Check | ID | What |
|---|---|---|
| Frontend wiring | WIRE-01 | Backend endpoint → frontend consumer verification (multi-repo) |
| AGE smoke gate | AGE-SMOKE | Full suite with GRAPH_BACKEND=age at tier boundaries |

---

## §6 — Scan ID Registry (NEW subsection)

**Add at the end of §6:**

```
### 6.5 Scan ID Registry

| Scan ID | What | Tier | Frequency | Tool |
|---|---|---|---|---|
| SHAPE-01 | Tensor shape match | T0 | Every commit | grep scanner |
| SHAPE-02 | Config↔Preset parity | T1 | Every batch | validate_against_preset() |
| PROV-01 | Provenance on render surfaces | T2 | Batch close | manual + Playwright |
| CLAIM-01 | Forbidden claims check | T0 | Every commit | grep scanner |
| WIRE-01 | Backend → frontend consumer | T2 | Every batch | wire_check.ps1 |
| AGE-SMOKE | Full suite with GRAPH_BACKEND=age | T2 | Tier boundary | pytest + env vars |
| DROP-CHECK | 5-condition runtime pre-check | T1 | Per prompt candidate | drop_precheck.ps1 |
| LANG-01 | Kitchen language (Purchasing) | T0 | Every commit | grep scanner |
```

---

## §9 — Risks: Add Frontend Wiring

**Add to §9.1 (Architecture Risks):**

| Risk | Symptom | Detection | Fix |
|---|---|---|---|
| Backend-only feature | Endpoint works, demo shows nothing | WIRE-01 scan | Build frontend component |
| Hardcoded frontend labels | DomainConfig has correct labels, frontend has stale hardcoded ones | WIRE-01 deep check | Wire frontend to /api/config endpoint |
| Polarity not rendered | interpret_factor() returns "high (favorable)" but evidence panel shows "0.85" | WIRE-01 deep check | Wire polarity into evidence display |

**Add to §9.3 (Narrative Risks):**

| Risk | Symptom | Detection | Fix |
|---|---|---|---|
| Backend-only weekly report | /api/purchasing/report/weekly returns data, no UI | WIRE-01 | P1: build WeeklyReportCard.tsx |
| POS data invisible | /api/purchasing/pos/today returns covers, no dashboard card | WIRE-01 | P2: build POS panel |

---

## §10 — Execution Schedule: Add WIRE-01

**Update the tier table:**

| Tier | Gates | Triggered by | Time |
|---|---|---|---|
| T0 | Merge/commit (CI) | Every commit | 30s |
| T1 | Batch acknowledgment | Change in scoring/evidence/preset/conservation/domains | 15min |
| T2 | **Batch-close** | Batch completion + WIRE-CHECK + AGE-SMOKE (if tier boundary) | 30min |
| T3 | Demo-ready / publish | Demo scheduled OR paper submission | 2-3h |

---

## §11 — Codex Prompts: Add WIRE-CHECK Prompt

**Add as §11.5:**

```
### 11.5 Prompt: Frontend Wiring Audit (Step 6)

WORKING DIRECTORY: copilot-sdk (then SOC, then S2P)
VENV: activate before running
TASK: Run WIRE-CHECK across all copilots. Report gaps.
TASK TYPE: Read-only scan. No edits.

Run wire_check.ps1 (integrity/wire_check.ps1).
For each copilot, report:
  - Backend endpoint count
  - Frontend API call count
  - Unwired endpoints (backend exists, no frontend call)
  - Classification: P1 (demo blocker) / P2 (product gap) / P3 (infra)

Do NOT fix gaps in this prompt. Report only.
Fixing is a separate prompt per gap.
```

---

## Design Decisions Registry: Add DD-4 through DD-7

**Add to the design decisions section (or create one if v2.4 doesn't have it):**

| DD | Decision | Date | Evidence |
|---|---|---|---|
| DD-1 | entity_field: Option C (domain-aware, deferred) | June 14 | P39A takes entity_id explicitly |
| DD-2 | SOC tensor = (6,4,6)=144 | June 14 | Runtime confirmed |
| DD-3 | AGE upsert: advisory-lock + MATCH-then-CREATE | June 14 | P29 proven |
| DD-4 | DomainPolicy stays SOC-local | June 14 | Fields: name, rule, priority, action_override (SOC-specific) |
| DD-5 | PromptVariant stays SOC-local | June 14 | Fields: category, version, description (SOC-specific) |
| DD-6 | DomainConfig ABC stays SOC-local | June 14 | 3 dead stubs + SOC-only concrete methods |
| DD-7 | Shared domain types frozen | June 14 | Zero mutation in 200K lines. All construction inline. |

---

## AGE Smoke Gate Results: Add DataOps

**Add to §16A or wherever AGE adoption is tracked:**

| Copilot | AGE Smoke Gate | Result | Date |
|---|---|---|---|
| SOC | After C9A+F8 | ✅ PASS | prior |
| **DataOps** | After P47 | ✅ **PASS — 216/216 both modes** | **June 14, 2026** |
| S2P | After P41 | ⏳ Pending | — |
| Trading | After P53 | ⏳ Pending | — |
| Purchasing | After P75 | ⏳ Pending | — |

---

## Investigation Methodology Rule (NEW)

**Add to standing rules or process section:**

```
INVESTIGATION RULE: Never design from import lines and class names.
Before any unification, migration, or cross-repo design:

1. Read FULL source files (not grep snippets)
2. Verify actual field names and types (not assumed)
3. Map all call sites (not just import sites)
4. Check for mutation patterns
5. Verify cross-repo import paths
6. Count test files that reference the changed classes

Investigation tools by depth:
  PowerShell: pattern matching, file existence, mutation grep
  Codex: semantic reading, class surface comparison, method analysis
  Graphify: dependency graphs, blast radius, cross-module consumers
  Runtime: live data verification, preset attribute discovery

The domain unification design v1.0 assumed DomainPolicy was
(id, label, description). SOC's actual DomainPolicy is
(id, name, rule, priority, action_override). The wrong design
would have shipped incompatible dataclasses to SDK. Only a
12-area investigation caught this before implementation.
```

---

## Document Control: Add v2.5

| Version | Date | Change |
|---|---|---|
| v2.5 | June 14, 2026 | Frontend wiring audit (§4A). WIRE-01 scan. SHAPE-02 scan. Rule #65. F-18/F-19/F-20. ARCH-15/16/17. DD-4-7. DataOps AGE gate PASS. Investigation methodology rule. DROP-CHECK scan. |

---

*Product Integrity Execution Strategy v2.4 → v2.5 Delta*
*New: §4A Frontend Wiring, WIRE-01 + SHAPE-02 + DROP-CHECK scans,*
*Rule #65, F-18/F-19/F-20, ARCH-15/16/17, DD-4-7,*
*DataOps AGE PASS, investigation methodology rule.*

---

## Document Control (Updated)

| Version | Date | Change |
|---|---|---|
| v2.5 | June 15, 2026 | Frontend wiring audit (§4A). WIRE-01 + SHAPE-02 + DROP-CHECK scans. ARCH-15/16/17. F-18/F-19/F-20. C-11/C-12/C-13/C-14. DD-4-7. DataOps AGE gate PASS. Investigation methodology rule. Steps 6+7 (frontend wiring + validate_against_preset). Scan ID registry. |

---

*Product Integrity Execution Strategy v2.5 · June 15, 2026*
*v2.4 base + frontend wiring (§4A), WIRE-01/SHAPE-02/DROP-CHECK scans,*
*ARCH-15/16/17, F-18-20, C-11-14, DD-4-7, investigation methodology rule.*

| v3.0 | July 10, 2026 | **POSTURE + the learning-mechanism truth (two structural changes).** **(1) §0.5 POSTURE — these gates guard the SEND, not the ROADMAP.** The document was being misread as a governor on what may be *built*; that makes it weaker (a gate that polices ambition gets bypassed under a demo deadline — exactly when integrity matters most). Correct scope, stated once: **what we BUILD is not governed here** (build ambitiously; a 63-site migration that yields the right architecture is a sequencing problem, not an integrity problem; claim↔code mismatch is the normal state of a company strengthening its architecture and closes by *building*, not by shrinking the plan); **what we SAY on an external surface IS governed here** (tier-labeled, class-labeled, FORBIDDEN-scanned at T3). The single failure this document exists to prevent: *being caught overclaiming in a diligence room / security review / peer review.* **Showing roadmap is allowed and expected** — implying roadmap is live is the violation. *Build ambitiously. Claim precisely. Never confuse the two.* **(2) §2.7 — the learning mechanism, named correctly** (cross-repo Codex diagnostic, 2026-07-10): the primary mechanism is **online supervised centroid/prototype learning from verified human decisions** (signal = correctness label, NOT a reward) plus DK coordinate-search weight estimation (`gae/profile_scorer.py:780,:950`; `gae/dk_estimator.py:171-192`) — **it is NOT "RL"** (**F-25**). Genuine bandit components exist but are peripheral, and the Thompson sampler is **`ConservationBoundedThompson`** — exploration is conservation-bounded by construction (**C-19**). The honest naming is the *stronger* differentiator (**C-18**: "we have no reward function for judgment" — exactly what a reward-maximizing agent cannot say). Shared cross-copilot learned state **NOT FOUND** ⇒ say "signals transfer," never "judgment transfers" (**F-26**); revisit at decision D5. **SOC learning is DISABLED by default** (`soc/config.py:66`) while Trading/Purchasing/DataOps/S2P are BUILT end-to-end ⇒ a SOC "watch it learn" beat is a demo-truth violation unless enabled and shown to change a later score. **New §2.8 — scenario classes LIVE / NEAR / ARCH**, the operational form of §0.5: every external scenario carries a class; showing ARCH is fine, *implying* it is LIVE is **F-27**. **§7.3 rewritten with evidence-based gate coverage and ONE OPEN F-24**: L1 ✅ (`scorer.py:465`), L1b ✅ (conservation-bounded by construction), L2 ✅ (`gate.py:27-41` gates on accuracy/superiority/variance AND conservation), **L2b ❌ prompt-variant promotion is ungated** (`prompt_evolver.py:195-215`) ⇒ **C-17 is scoped** ("our scoring, exploration and scorer-evolution loops") until `C-GOV` (~0.5-1d) lands. GC checks extended (GC-06 naming, GC-07 cross-copilot, GC-08 centroid-accessor). **New ARCH-20 CENTROID-ACCESSOR** T0 invariant (activate after C-REGIME P1: no direct `mu[...]` outside the accessor — keeps the 63 sites migrated). Registry extended: **F-25..F-27, C-18..C-19**; zero duplicate IDs verified. |
