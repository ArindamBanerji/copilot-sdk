# S2P FIX-B — What-If Solution Experiments — Executable Plan & Prompts v3

**Date:** 2026-08-04
**Supersedes:** v2 (adds the Context & Approach section); v1 (added shared setup, ordered execution steps, and near-ready Codex prompt blocks).
**Type:** Experimental spikes in throwaway sandboxes. **Report-only** on source; **never write the live `soc_graph`.** Scratch scripts allowed, deleted after.
**Purpose:** validate candidate FIX-B fixes empirically before writing a production migration. Spike first, spec second. The coding session takes the prompt blocks below, fills the few `[Codex: resolve]` gaps against the tree, and runs them in order A → B → C → D.

---

## Context & Approach — why "what-if" experiments, and why now

This S2P investigation has run as a waterfall: design a fix on paper → have it statically verified → discover a flaw → redesign. Every loop was reasoning followed by a static read of the code. And nearly every confident paper claim in it was wrong until empirical signal arrived — the "hub fan-out" mechanism, the "self-healing" link write, the "fail-open" conservation gate, the AGE-syntax assumptions were each corrected only by data (a live diagnostic, a live-graph probe, the demo launcher output). When theory keeps missing and evidence keeps deciding, the rational move is to stop refining theory and start generating evidence.

A what-if solution experiment doesn't try to prove a fix correct in advance; it runs a candidate fix against real infrastructure in a throwaway sandbox and reports what actually happens. Most candidates are expected to fail — and that is the point: the failures map the boundary of what could work far faster than argument does. Instead of committing to one carefully-reasoned production migration and hoping it survives contact with reality, we try several approaches cheaply, watch which survive, and write the real spec around the winner rather than around what we reasoned into.

The asymmetry is what makes this worth doing. The fix mutates production data — the shared `soc_graph` with ~26K decisions the whole platform depends on — so a wrong migration is expensive and awkward to unwind. A spike costs a disposable graph that gets dropped in seconds, and the infrastructure already exists: the test suite spins up and tears down isolated AGE graphs routinely (`conftest.py`'s per-test disposable graphs), and `soc_graph` can be cloned for the trials that need production scale and density. Nothing here writes production; everything runs in a `whatif_*` sandbox or a clone and is discarded afterward.

So the workflow flips to spike-first, spec-second. The experiments below are ordered cheap-to-expensive, and each is built to kill one specific open question with data — does seeding entities even fix the score (A1), which label mapping makes the factors fire (A2), which query shape is fast *and* correct at production density (B1), is the migration non-destructive and reversible (C1), does the full suite go green in AGE mode (D1). Because an early failure invalidates the later phases, they run in order and stop on a premise-breaking result. What comes out is not a validated plan but a validated *shape* — and only then does the FIX-B migration spec get written, grounded in what survived contact with the graph instead of what read well on paper.

---

## 0. Shared setup (all phases)

**AGE DSN.** Use the S2P active AGE DSN: `host=172.22.74.149 port=5433 sslmode=disable`. If that host is unreachable from the shell, use `host=localhost port=5433 sslmode=disable` (the entity-model scan confirmed localhost works under WSL). Verify: `psycopg.connect(dsn)`, then `conn.execute("LOAD 'age'")`.

**Create / drop a disposable sandbox graph** (the `conftest.py` `s2p_age_test_env` pattern):
```python
import psycopg, uuid
name = f"whatif_s2p_{uuid.uuid4().hex[:12]}"
with psycopg.connect(dsn, autocommit=True) as c:
    c.execute("LOAD 'age'"); c.execute("SET search_path = ag_catalog, \"$user\", public")
    c.execute(f"SELECT create_graph('{name}')")
# ... run trial ...
    c.execute(f"SELECT drop_graph('{name}', true)")   # always drop after
```

**Seed the entity subgraph into a sandbox:**
`python s2p-copilot/scripts/seed_s2p_graph.py --graph <sandbox_name>`
`[Codex: confirm exact CLI flags from main(); a non-soc_graph target should NOT require ALLOW_PRODUCTION_SEED (the guard only blocks 'soc_graph'). Confirm it stamps or not — for these trials stamping is optional.]`

**Point the S2P backend at a sandbox** (for score/PW trials): set `S2P_ACTIVE_GRAPH_BACKEND=age`, `S2P_ACTIVE_AGE_DSN=<dsn>`, `S2P_ACTIVE_AGE_GRAPH=<sandbox_name>`, `S2P_ACTIVE_AGE_DOMAIN=s2p`.

**Reference: `S2P-INV-0003`** (the canonical failing entity) — supplier `SUP-003` (Northstar Packaging), commodity `resin`, contract `CTR-003-PRI`, PO `PO-20260003`, category `price_variance`, amount `3781.7`. **SQLite baseline to match** (from `s2p_diag`): action `auto_approve`, confidence `0.947`, factors `match_status 0.953, amount_variance_ratio 0.04, duplicate_score 0.007, supplier_exception_history 0.033, payment_terms_impact 0.515, commodity_index_correlation 0.822, tax_regulatory_compliance 0.938`.

**Cloning `soc_graph`** (Phases B/C) — `[Codex: resolve the mechanism.]` Options: (a) pg-level — `create_graph('<clone>')`, then `INSERT INTO <clone>.<label> SELECT … FROM soc_graph.<label>` for the S2P Decision + DecisionEntityLink label tables; (b) Cypher-level — MATCH S2P Decisions/orphans in soc_graph and CREATE in the clone. **For C (safety) a representative subset (a few thousand S2P Decisions + all 84 orphans) suffices** to prove non-destructiveness/idempotency/rollback. **For B (performance) match production density** (see below) — all ~25,892 or a density-matched synthetic.

**Density to reproduce (B):** ~25,892 S2P Decisions over ~50 fixture invoices ≈ **518 Decisions/invoice**; after linking, each Invoice is a `DECIDED_ON` hub. B must run at this density or the crowding/fan-out won't appear.

**Hard safety rules (every phase):** never `create_graph`/`drop_graph`/write `soc_graph`; all work in a `whatif_*` sandbox or a `<clone>`; delete scratch scripts after; edit no production/test source.

---

## 1. Execution plan (ordered)
1. **Phase A** (cheap disposable) — validate the premise + resolve label mapping. **If A1 fails, STOP and report** — everything downstream is moot.
2. **Phase B** (soc_graph clone at density) — pick the query shape + confirm the index is used.
3. **Phase C** (soc_graph clone) — prove the migration is non-destructive, idempotent, reversible; set orphan policy.
4. **Phase D** (seeded disposable + backend) — run the sharded PW suite in AGE mode with A/B's winners applied.
Each phase is a standalone Codex prompt (below). Run in order; a failure short-circuits the rest.

---

## 2. Codex prompt blocks (near-ready — coding session finalizes the `[Codex: resolve]` gaps)

### PROMPT A — Correctness spike
```
TASK: S2P FIX-B what-if — Phase A (correctness spike). Report-only; no source edits; never write soc_graph; drop all sandboxes after.
CONTEXT: S2P PW fails because the demo runs S2P against soc_graph, which has S2P Decisions but no entity subgraph, so the score's context read scans and times out. Hypothesis: seeding the entity subgraph into the queried graph makes the score work. Use the Shared Setup (DSN, create/drop graph, seed tool, S2P-INV-0003 reference + SQLite baseline).

A1 — seed-fixes-score:
1. Create sandbox SB_A1. Seed the entity subgraph: python s2p-copilot/scripts/seed_s2p_graph.py --graph SB_A1.
2. Verify labels created: count Invoice/Supplier/PurchaseOrder/GoodsReceipt/Commodity/Contract nodes and DECIDED_ON/SUPPLIED_BY/MATCHED_TO/HAS_COMMODITY_INDEX/GOVERNED_BY/RECEIVED_AS edges. Confirm S2P-INV-0003 exists with a linked Decision (the seed builds Decisions; if not, create one minimal Decision + DECIDED_ON).
3. Score S2P-INV-0003 two ways: (a) direct — call query_context('S2P-INV-0003', 2, domain='s2p') then compute_all_factors(invoice, {"neighbors": rows}); (b) endpoint — start the S2P backend pointed at SB_A1 (env in Shared Setup), POST /api/s2p/score with the S2P-INV-0003 payload.
4. MEASURE: the 7 factor values (real vs fixture-fallback), action, confidence, latency, any timeout. Compare to the SQLite baseline.
5. REPORT PASS if factors are real, no timeout, and match (or explainably differ from) the baseline. If FAIL: which factor fell back, which neighbor was absent/mis-keyed, any anchor mismatch (entity_id vs invoice_id).

A2 — label mapping (resolves D1):
1. Sandbox SB_A2_SEED seeded with seed labels (Commodity/Contract/GoodsReceipt). Sandbox SB_A2_CONTRACT with the active-contract labels (CommodityIndex/ContractClause/ComplianceHistory) + their property keys [Codex: adapt the seed to emit contract labels/schema, or hand-CREATE the commodity/contract/compliance nodes with the contract keys].
2. Run CommodityIndexCorrelation, TaxRegulatoryCompliance, MatchStatus against each.
3. MEASURE + REPORT which label set makes each factor return a real value vs fallback → the canonical label/property set the migration must write.

Drop SB_A1/SB_A2_*. Return the Report Format below.
```

### PROMPT B — Query shape & index (after A passes)
```
TASK: S2P FIX-B what-if — Phase B (query shape + index) at production density. Report-only; sandbox = a CLONE of soc_graph; never write soc_graph; drop after.
SETUP: Clone soc_graph into SB_B [Codex: resolve clone mechanism; match ~518 Decisions/invoice density]. Seed the entity subgraph into SB_B and create the DECIDED_ON links so invoices are real hubs. Create an index on Invoice.invoice_id [Codex: resolve AGE index DDL + verify it exists].

B1 — which query wins + is the index used:
Time (cold + warm, ≥3 reps) for S2P-INV-0003, each variant:
  (1) label-less  MATCH p=(e {entity_id:'S2P-INV-0003'})-[*1..2]-(n) WHERE n.domain='s2p' RETURN p LIMIT 100
  (2) 1-hop undirected  MATCH (e:Invoice {invoice_id:'S2P-INV-0003'})-[]-(n) RETURN n LIMIT 100
  (3) 1-hop label-filtered/directed to entities only  [e.g. (e:Invoice {...})-[]->(n) or WHERE n:Supplier OR n:PurchaseOrder OR n:GoodsReceipt OR n:Commodity OR n:Contract]
  (4) variants (2)+(3) WITH vs WITHOUT the Invoice.invoice_id index
For EACH: latency; whether the result actually contains the PO/GR/Supplier/Commodity/Contract the factors need OR gets crowded by the ~518 Decisions out of LIMIT 100; and via EXPLAIN, whether the index is used.
REPORT the query shape that is fast AND returns the factor-required neighbors.

B2 — targeted duplicate lookup:
Run a same-supplier, amount ±X%, LIMIT k lookup for S2P-INV-0003's supplier; time it; confirm it returns sibling invoices bounded, no fan-out. REPORT viability.

Drop SB_B. Return the Report Format.
```

### PROMPT C — Migration safety (soc_graph clone)
```
TASK: S2P FIX-B what-if — Phase C (migration safety). Report-only; sandbox = a CLONE of soc_graph; never write soc_graph; drop after.
SETUP: Clone soc_graph into SB_C including its S2P Decisions (a representative few-thousand subset is fine) + all 84 DecisionEntityLink orphans. Record pre-counts: S2P Decision count, orphan count, per-label counts.

C1 — hardened migration is safe + reversible:
Run the migration against SB_C with: stamping every node/edge (domain='s2p', provenance='migration', domain_source='migration'), NON-force only (natural-key CREATE-if-absent), and the force delete `MATCH (n) WHERE n.domain='s2p' DETACH DELETE n` explicitly DISABLED (assert off). [Codex: use a hardened wrapper over scripts/seed_s2p_graph.py write_seed_plan; do not run the tool's force path.]
ASSERT + REPORT: S2P Decision count before == after (zero deleted); every new node/edge carries the three stamps; idempotent (2nd run creates 0 new); rollback `MATCH (n {domain_source:'migration'}) WHERE n.domain='s2p' DETACH DELETE n` returns SB_C to exact pre-counts.

C2 — orphan reconciliation:
On migrated SB_C, reconcile the 84 orphan DecisionEntityLink into real edges where the Decision and entity both now exist; count reconciled vs residual; assert no Decision touched, no force-delete used. REPORT the retain/reconcile/delete policy with counts.

Drop SB_C. Return the Report Format.
```

### PROMPT D — End-to-end (seeded disposable + backend)
```
TASK: S2P FIX-B what-if — Phase D (end-to-end PW in AGE mode). Report-only on source; sandbox = disposable graph; never write soc_graph; drop after.
SETUP: Create SB_D, seed the entity subgraph + the Invoice.invoice_id index. Apply the WINNING query shape from B1 and the off-path _link_decision_to_invoice change (→ _SIDE_EFFECT_EXECUTOR) in a scratch/branch build only [Codex: minimal local patch, not a committed source edit]. Point the S2P PW backend at SB_D (env in Shared Setup).

D1 — full suite green:
Run the sharded S2P suite in AGE mode: cd copilot-sdk/e2e; npx playwright test --config=s2p/playwright.config.ts s2p/ --reporter=line, workers=1 for backend-heavy shards, per-test 90/180s, --global-timeout 600/900s. REPORT pass/fail per shard, any residual timeouts or empty-context failures.

D2 — off-path link behavior:
Confirm score latency drops vs inline, real DECIDED_ON edges are created (entities present), and NO new orphan DecisionEntityLink nodes appear. REPORT counts.

Drop SB_D. Return the Report Format.
```

---

## 3. Report Format (every prompt returns this)
Per trial: sandbox used · exact commands/Cypher run · measured numbers (latency, counts, factor values, EXPLAIN) · PASS/FAIL · one line "what surprised us / what failed and why."
Then a **synthesis**: what worked · what didn't · what could work — and a recommended fix shape (canonical label set, winning query shape, index set, migration parameters, orphan policy). Explicitly flag anything that failed in a way that changes the FIX-B plan.

## 4. After the spikes
Claude writes the FIX-B migration + query spec around the shape that **survived** — the label set A2 confirmed, the query B1 proved fast-and-correct, the migration parameters C1 proved safe, validated end-to-end by D1 — instead of the shape reasoned into. Place that spec in `copilot-sdk/docs/design/` so the design-verify step can read it.

## Provenance
Setup mechanics (disposable graph, env, DSN, localhost fallback), the writer, live counts, and the target are from `s2p_entity_model_scan_v1.md`. The S2P-INV-0003 baseline is from `s2p_diag`. The factor→label mapping and query shapes are from Claude's reads of `test_factors.py`/`factors.py` and `s2p_score_context_rootcause_design_v2.md`. The ~518/invoice density is computed from the scan counts and is itself tested by B1.
