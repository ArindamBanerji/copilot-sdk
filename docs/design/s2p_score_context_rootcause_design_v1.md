# S2P Score Context — Root-Cause Design & Experiment Plan v1

**Date:** 2026-08-04
**Status:** root cause identified from the factor code; design proposed; experiments + scans defined to confirm before building.
**Frame:** this is a graph-modeling problem, not a query-tuning problem. Timeout/F1/depth-cap are guardrails or band-aids — the real fix is to stop fetching context the way we do.

---

## 1. Root cause (evidence-based — a hub/supernode fan-out)

The score fetches **one** undirected 2-hop blob — `MATCH p = (e {entity_id:$id})-[*1..2]-(n) WHERE n.domain='s2p' RETURN p LIMIT 100` — via `_resolve_graph_context → reader.query_context(invoice_id, max_depth=2)`, and passes `{"neighbors": rows}` to `compute_all_factors`. What the factors actually consume (confirmed in `factors.py` / `test_factors.py`):

| Factor | Needs | Hops |
|---|---|---|
| MatchStatus | invoice's PurchaseOrder + GoodsReceipt | 1 |
| AmountVarianceRatio | invoice's PurchaseOrder(amount) | 1 |
| SupplierExceptionHistory | invoice's Supplier(exception_rate) | 1 |
| PaymentTermsImpact | invoice's Supplier(payment_terms) | 1 |
| CommodityIndexCorrelation | invoice's Commodity(volatility) | 1 |
| TaxRegulatoryCompliance | invoice's Contract / Supplier | 1 |
| **DuplicateScore** | **other Invoice siblings with similar amount** | **2** |

**6 of 7 factors need only the invoice's direct 1-hop neighbors.** The 2-hop depth exists solely to reach sibling invoices for DuplicateScore — and siblings are reachable only *through a shared node*: `invoice → Commodity (HAS_COMMODITY_INDEX) → other invoices`, or `invoice → Supplier → other invoices`. Those shared nodes are **hubs** (a commodity index is shared by many invoices), so from a dense entity (S2P-INV-0003) the undirected 2-hop fans back out to every co-sharing invoice — hundreds/thousands of paths — and AGE's VLE explodes (community data: exponential in depth). This is why one specific entity is *deterministically* pathological: it points at a popular hub.

**Why every patch so far is wrong:**
- **Timeout-only** → masks a 30–120s hang as a fast empty context; the score then silently computes on fixture fallbacks for all 6 direct factors. Fast but *wrong answers*.
- **F1 degrade-to-None on error** → correct as a floor (no 503) but same problem: empty context = wrong factors for the dense entities.
- **Blind depth-cap to 1** → fixes the explosion but *silently kills DuplicateScore's* graph signal (it falls back to the fixture `duplicate_score`), losing real duplicate detection.
- **Typed/directed Cypher (my F3)** → doesn't even parse in AGE (no pipe-typed/directed var-length, no `labels()`/`length()`).

The correct fix must be **fast AND preserve all 7 factors' signals** — which means splitting the read by what each factor needs.

---

## 2. The design — split the context read

Replace the single explosive 2-hop blob with two bounded, purpose-built reads.

### 2a. Direct context (feeds 6/7 factors) — 1-hop, bounded, always cheap
The invoice's own entities (PO, GR, Supplier, Commodity, Contract) are all 1 hop away. Fetch them with a **1-hop** read, bounded by edge count (~5–10), not hub degree. AGE-compatible shape (no var-length, no typed multi-edge, no `RETURN p`):
```
-- AGE: whole query is wrapped by AGEClient as
-- SELECT * FROM cypher('<graph>', $$ ... $$) AS (n agtype);
MATCH (e {entity_id: '<interpolated, escaped invoice_id>'})-[]-(n)
WHERE n.domain = 's2p'
RETURN n
LIMIT 100
```
Three AGE specifics that make this correct (see §7):
- **Parameters:** do NOT write inline `$entity_id` unless the call is a PREPARE'd statement (AGE `$param` requires prepared statements + an agtype map as the 3rd `cypher()` arg). The current code string-interpolates, so keep that (with proper escaping) — matching the existing pattern — OR migrate the context reads to prepared statements (safer against injection). Pick one deliberately; don't half-use `$`.
- **Return shape:** `RETURN n` returns the whole vertex as a single agtype value (label + id + properties) — exactly what the factor code reads (`node._label`, `node.po_id`, `node.amount`, …). But it changes the column-definition list from the old `RETURN p` (`AS (p agtype)`) to `AS (n agtype)` — the AGEClient's result-column mapping must change with it.
- **Relationship form:** `-[]-` (untyped, undirected, single hop) is the documented AGE pattern; if a bare `-[]-` misbehaves on this version, `-[*1..1]-` is the drop-in fallback (same VLE machinery the current query already uses, just depth 1).

This is O(edge-count), predictable milliseconds, and gives 6/7 factors exactly what they read today. Perf tip (verify): anchoring the start node with its label — `(e:<InvoiceLabel> {entity_id: '…'})` — plus an index lets AGE scan one label table instead of all of them; the current label-less `(e {entity_id: …})` works (it's what runs today) but is slower.

### 2b. Duplicate context (feeds DuplicateScore only) — targeted + bounded, never a fan-out
DuplicateScore needs "is there another invoice from the same supplier with a near-identical amount?" — a *bounded* question, not "all invoices 2 hops away." Options, best first:
1. **Targeted indexed lookup:** same-supplier, amount within ±X%, `LIMIT k` (k≈5–20), backed by an index on `(supplier_id, amount)`. Bounds the *work*, not just the result. Never fans through the hub.
2. **Precomputed duplicate-candidate set** maintained on write (invoice bucketed by `(supplier_id, amount-band)`), read O(1) at score time.
3. **Deferred/cached** duplicate score (compute async, read last value at score time) — acceptable because duplicate risk changes slowly.

Whichever we pick, DuplicateScore keeps a *real* signal instead of degrading to the fixture fallback — which the naive depth-cap loses.

### 2c. Guardrail (defense-in-depth, not the fix)
Keep F1 (degrade on failure) + a short (~2s) `statement_timeout` on the context reads. With 2a/2b bounded, this should essentially never fire — but it caps any unforeseen pathology. The difference from "timeout-only": here the *common path returns correct context fast*, so the timeout is a safety net, not the mechanism.

### 2d. Graph-modeling principle (the durable lesson)
On a hot path, **never traverse *through* a hub.** Read direct neighbors (1-hop) or do a targeted, indexed, bounded lookup. Undirected variable-length from an entity whose neighbors include shared nodes is unbounded by construction. This principle should guard the situation endpoint (depth-3) too.

---

## 3. Experiments to confirm (run against the live AGE graph — for Codex)

Do these BEFORE building; they confirm the hub model and validate the AGE-compatible shapes. Each is a `cypher(...)` snippet with a pass/fail read.

- **E1 — Confirm the hub.** For S2P-INV-0003, get 1-hop neighbors and each neighbor's degree:
  `MATCH (e {entity_id:'S2P-INV-0003'})-[]-(n) RETURN n LIMIT 100` (inspect labels), then for each neighbor `MATCH (h {<id>})-[]-(x) RETURN count(*)`. **Expect:** a Commodity/Supplier neighbor with very high degree (the hub).
- **E2 — 1-hop is fast + sufficient.** Time `MATCH (e {entity_id:'S2P-INV-0003'})-[]-(n) RETURN n LIMIT 100`. **Expect:** <50ms, and the result contains PO/GR/Supplier/Commodity/Contract.
- **E3 — 2-hop explodes via the hub.** `MATCH (e {entity_id:'S2P-INV-0003'})-[]-(mid)-[]-(n) RETURN count(*)` and group by `mid`. **Expect:** the count is dominated by one hub `mid`.
- **E4 — AGE syntax probes** (docs already settle some — see §7; confirm the rest empirically on THIS version): confirmed-by-docs → `RETURN n` returns the vertex agtype, `DISTINCT` is supported, params require prepared statements, `-[]->` is documented. Still verify on this instance → bare undirected `-[]-` (vs `-[*1..1]-`) executes cleanly; `RETURN DISTINCT n` dedupes vertices as expected; whether label-anchoring `(e:<label> {…})` uses an index (needs the invoice's vertex label from S2); single-type `-[:HAS_COMMODITY_INDEX]-` at 1 hop parses (typed FIXED-length may work even though typed VAR-length doesn't). Do NOT probe pipe-typed/directed var-length, `labels()`, `length()` — already confirmed absent.
- **E5 — Targeted duplicate query is bounded.** Time a same-supplier, amount-range, `LIMIT 20` lookup on S2P-INV-0003's supplier. **Expect:** fast and bounded even though the supplier is a hub → validates 2b(1). Also check whether an index on `(supplier_id, amount)` exists / helps.

---

## 4. Code scans to map the tree (for Codex — I couldn't read these remotely; the store file is 129KB and snippets return only the head)

- **S1 — `store.query_context`** (`ci_platform/graph/age_graph_store.py`): exact Cypher, how `hop_count`/`max_depth` is chosen, and whether a **1-hop context helper already exists** (if so, 2a is a re-wire, not new code).
- **S2 — the write path:** which edges connect invoice → PO/GR/Supplier/Commodity/Contract, and confirm Commodity/Supplier are shared across invoices (the hubs). Grep `link_decision_to_entity`, `write_entity_enrichment`, the graph seeding, and the edge labels (DECIDED_ON, HAS_COMMODITY_INDEX, GOVERNED_BY, RECEIVED_AS, COMPLIANCE_RECORD).
- **S3 — DuplicateScore's exact requirement** (`factors.py` `DuplicateScore.compute`): does it need all siblings or just same-supplier near-amount? (Determines 2b's query.) Confirm the fixture fallback path so we know the degraded behavior.
- **S4 — indexes:** existing indexes on vertex `entity_id`, `supplier_id`, `amount` (for E5 / 2b).

---

## 5. Implementation plan (after E1–E5 + S1–S4 confirm)

1. Add **`query_direct_context(entity_id, domain)`** — the 1-hop bounded read (2a), returning `neighbors` in the same shape `compute_all_factors` reads today (so 6 factors are unchanged).
2. Add **`query_duplicate_candidates(supplier_id, amount, k)`** — the targeted bounded lookup (2b), and wire DuplicateScore to it (or merge its results into `neighbors` as Invoice nodes so the factor code is unchanged).
3. Point `_resolve_graph_context` at the two bounded reads instead of `query_context(max_depth=2)`. Keep F1 + a short `statement_timeout` as the guardrail.
4. **VERIFY:** score returns full correct factors (not fixture fallbacks) for S2P-INV-0003 in <500ms; DuplicateScore still fires on a seeded duplicate; the failing PW suite (flows/rule-vs-reasoning/situation-analyzer) greens *with real context*, not empty; no `RETURN p`/untyped `-[*1..2]-` on the score path.
5. Apply the same direct-read/no-hub-traversal shape to the situation endpoint (depth-3) separately.

---

## 6. Sequencing

- **Now (unblocks progress, low risk):** F1 + short `statement_timeout` as the guardrail — but labeled as the *floor*, and explicitly NOT the fix (it returns empty context for dense entities → wrong factors).
- **Next (the real fix):** run E1–E5 + S1–S4 (Codex), then implement §5. This is a ~1–2 day change, not a patch, and it fixes correctness (right factors) and latency (bounded reads) together.

## 7. AGE Cypher — syntax ground truth (for whoever writes the queries)

Apache AGE implements a *subset* of openCypher over PostgreSQL; several Neo4j idioms don't parse. This is the ground truth to write against (confirmed from Apache AGE docs + the user's empirical tests on this instance). Two of my earlier query drafts were Neo4j-idiom and wrong — don't repeat them.

**Confirmed NOT supported (do not use):**
- Pipe-typed variable-length: `-[:A|B*1..2]-` — no.
- Directed variable-length: `-[*1..2]->` — no (undirected `-[*1..2]-` is what runs today).
- `labels(n)`, `length(r)` — no (`size()` is present; use it if a count is needed).
- Inline `$param` in a plain (non-prepared) query — errors.

**Confirmed supported (safe to use):**
- Untyped undirected variable-length `-[*1..N]-` (this is the current query; the problem is depth/fan-out, not syntax).
- `RETURN n` / `RETURN e` returning a whole vertex as one agtype value (label + id + properties). `RETURN DISTINCT` is supported.
- `WHERE`, `LIMIT`, numeric functions, `size()`.
- Documented fixed-length patterns incl. untyped `-[]->` and typed single-type `-[:TYPE]->`.
- Label-less property match `(e {entity_id: '…'})` (runs today) — works but scans all label tables; label-anchoring is the perf win.

**Parameters — the correctness trap:**
- AGE runs every query as `SELECT * FROM cypher('<graph>', $$ <cypher> $$ [, <params>]) AS (<cols> agtype);`.
- Cypher `$name` params work ONLY inside a `PREPARE`d statement, with a Postgres `$1` placeholder as the 3rd `cypher()` arg and an agtype map supplied at `EXECUTE`. Not in ad-hoc queries.
- The current code therefore **string-interpolates** the entity_id. Keep interpolation (escape properly) for the new reads, OR convert the context reads to prepared statements — but don't write bare `$entity_id` expecting Neo4j behavior.

**Column-definition coupling:** the `AS (… agtype)` list must match the RETURN signature. Switching `RETURN p` → `RETURN n` requires the AGEClient's result-column definition to change from one path column to one vertex column. Whoever changes RETURN must change the column def in the same place.

**Net for §2a:** `MATCH (e {entity_id: '<escaped>'})-[]-(n) WHERE n.domain = 's2p' RETURN n LIMIT 100`, wrapped by AGEClient with `AS (n agtype)`, interpolated (or prepared). Every token in that is confirmed-supported. E4 only needs to confirm the bare `-[]-` form and label-anchoring on this instance.

## Provenance
- Factor→context mapping is confirmed from `factors.py` + `test_factors.py` (each factor's `compute` + its graph tests). The single-2-hop-blob path is confirmed from Codex's read of `_resolve_graph_context`. AGE syntax limits are from the user's empirical tests + Apache AGE docs. The hub *mechanism* is a high-confidence hypothesis pending E1/E3. Store internals (S1–S4) need Codex's on-tree read — the mirror's 129KB file returns only its head via search.
