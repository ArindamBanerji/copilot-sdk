# VLD-Depth Memo v12 — Delta from v11

**Instructions:** Apply these changes to `ci_vld_depth_memo_v11.md` to produce v12.

---

## 1. Header update

Replace the "New in v11" line and add v12:

```
**New in v12:** P1 (graph traversability) **RESOLVED** via Astra repo audit
(Appendix E). The decision graph is **PARTIALLY** topologically traversable — SOC
and S2P have physical non-similarity paths; Trading/Purchasing have zero demonstrated
live coverage; DataOps has system-keyed property-mediated routes. §3C.8 updated from
"open question" to "answered." §3D updated with concrete per-copilot scoping. Response
spec reorganized: P1 is closed; **P7 (Ψ design for SOC/S2P)** is now the highest-
leverage build item. LLM judge prompt for v12 appended (Appendix F).
```

---

## 2. Update §3C step 8 — P1 is now ANSWERED

Replace step 8 in §3C with:

```
8. **Graph traversability — ANSWERED (repo audit, Sep 7 2026).**

   **PARTIALLY.** No intentional Decision→Decision edges exist in any copilot's
   contract or concrete writers. However, indirect topological paths through non-
   decision hub nodes exist and vary by copilot:

   | Copilot | Indirect paths | m_topological | Evidence |
   |---|---|---|---|
   | **SOC** | D→Alert→Campaign→CONTINUES→Campaign→Alert→D (4-5 hops) | **Moderate** | T:898; C:1175-1216, 1715-1728 |
   | **S2P** | D→Invoice→Supplier→Invoice→D; exact supplier/category matcher | **Moderate** | S2C:150-174; migration:384-407 |
   | **DataOps** | System-keyed decision history (property-mediated) | **Low** | context_router.py:913-931 |
   | **Trading** | Shared Instrument/Event in seed output only; no live wiring | **≈0** | seed_graph.py:197-205 |
   | **Purchasing** | Shared Item/Vendor in seed output only; no live wiring | **≈0** | seed_graph.py:197-203 |

   **Key corrections to earlier assumptions:**
   - Decision→Alert→Campaign IS a physical edge path (not just a campaign_id property)
   - Decision retrieval is NOT purely centroid-distance — entity traversal, exact-key
     matching, and cosine retrieval are distinct mechanisms (G:3776-3815; S2C:150-174)
   - L5DKWeight writes currently produce NO SHAPED_BY edge (G:2860-2880)
   - SOC has unused query constants (SHARED_ENTITY_QUERY, TECHNIQUE_SEQUENCE_QUERY) that
     assume edges that no production writer creates — misleading but not evidence of topology

   **Implication for Ψ design:** judgment-trace Ψ is viable and not A0-suspect by
   construction for SOC and S2P (they have non-similarity routes). For Trading/Purchasing,
   Ψ-over-decisions requires building entity attachment first. For all copilots, Ψ-over-
   non-decision-evidence (entities, artifacts, process data) is the more general mechanism.

   **Full report:** Appendix E (`vld_depth_p1_decision_graph_topology_report.md`).
```

---

## 3. Update §3D — concrete scoping

Replace §3D with:

```
## 3D. Planning for the confirmed scoping outcome

P1 + the pilot confirm the bimodal outcome anticipated in v11:

**Tier 1 (build Ψ):** SOC and S2P have physical hub-linked paths. Invest in
state-conditioned admission adapters that traverse Campaign→Alert→Decision (SOC) and
Invoice→Supplier→Decision (S2P). Build the SOC integration first (richest topology,
highest m_world from §3A).

**Tier 2 (wire entities):** DataOps has system-keyed decision history but needs
explicit Decision→Pipeline/Alert entity attachment in production. Trading and
Purchasing need Instrument/Item/Vendor entity attachment via governed Decision
creation. This is prerequisite infrastructure, not VLD-specific.

**Tier 3 (cheaper win):** For Trading/Purchasing (and S2P until OD-1), the pilot
shows the loop earns little over breadth → invest in better single-shot / few-step
adaptive retrieval (Ψ-once). The semantic decision-classification (§3B) is
deliverable in its own right (it flags what needs HITL even where the loop is thin).

**What needs building (from the P1 report):**
1. State-conditioned admission adapter (the Ψ loop itself) — the hard part
2. SOC: expand campaign members into full prior Decision/Outcome records; correct
   the security-context edge-name mismatches (AC:585-592 vs SG:743-796)
3. S2P: enforce as-of cutoff on supplier matcher (S2C:150-174 has no temporal guard)
4. Trading/Purchasing/DataOps: persist entity links in production, not just seeds
5. Coverage measurement: count non-similarity routes per hard-tail case
```

---

## 4. Update response spec — P1 closed, P7 added

Replace the ★ response section with:

```
## ★ What we need you to respond with (to move VLD forward)

**P1 — RESOLVED.** Graph traversability answered (Appendix E). No further repo
audit needed. SOC and S2P have non-similarity paths; Trading/Purchasing ≈0.

**P2 — Estimate `m_topological` per copilot (domain owners).** [unchanged]

**P3 — Ratify the flagged calls.** [unchanged, but add: ratify the θ_min form
`q ≥ 23.53/(α·V)` — the prior `α·q·V` form is **withdrawn** (§6)]

**P4 — React to the reasoning.** [unchanged]

**P5 — [co-highest-leverage] React to the real-mechanism pilot (§3A).** [unchanged]

**P6 — Are the attribution controls the right decisive tests?** [unchanged]

**P7 — [NEW, highest-leverage BUILD item] Design Ψ for SOC.**
The repo audit (Appendix E) establishes the available edges. Design the
state-conditioned admission operator for SOC:
- Entry: Decision→Alert (DECIDED_ON edge, T:898)
- Hub: Alert→Campaign (MEMBER_OF edge, SG:729-796)
- Continuation: Campaign→CONTINUES→Campaign (C:1175-1216)
- Reverse: Campaign→Alert→Decision (prior decisions on same campaign)
- Entity: Alert→User/Asset (SG:729-749) → other Alerts → Decisions
- What to admit on each pass, conditioned on v_t?
- How to avoid the A0 attractor (admit by topology, not by similarity)?
- How to handle missing/sparse edges (not all alerts have campaigns)?
- What is the budget (max nodes admitted per pass)?
This is the Ψ design question — the hard part of the build.
```

---

## 5. Add Appendix E — P1 report reference

```
## Appendix E — P1 Graph Traversability Report (reference)

Full report: `vld_depth_p1_decision_graph_topology_report.md` (30KB, Sep 7 2026).
Source: Astra (`gpt-6-astra /xhigh`) repo audit across all 6 repositories.

**Headline:** PARTIALLY — CI is not similarity-only by construction. SOC has
physical decision–alert–campaign paths; S2P has decision–invoice links and
supplier-keyed prior-decision retrieval; DataOps has system-keyed decision history.
Trading/Purchasing have zero demonstrated live native coverage.

**Key file references (abbreviated):**
- G: ci-platform/ci_platform/graph/age_graph_store.py
- T: gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py
- C: gen-ai-roi-demo-v4-v50/backend/app/domains/soc/campaigns.py
- S2C: s2p-copilot/backend/app/services/s2p_context_builder.py
- SG: gen-ai-roi-demo-v4-v50/backend/app/graph_schema.py

See the full report for per-section evidence with file:line citations.
```

---

## 6. Add Appendix F — LLM Judge Prompt for v12

```
## Appendix F — LLM Judge Prompt (v12)

### Purpose
You are an independent expert reviewer. This memo (v12) incorporates a resolved P1
(graph traversability), a real-mechanism pilot (§3A/Appendix D), and five prior judge
reviews (Appendix A). Your job is to react to the **new material** and the program's
**next decisions**.

### What to respond to (in order of leverage)

**J1 — Does the P1 resolution (Appendix E) change the program's viability?**
The repo audit found partial topological traversability (SOC/S2P moderate, Trading/
Purchasing ≈0). Given this + the pilot's Δ_trajectory=0 finding:
(a) Is "adaptive retrieval, not the loop" still the right framing?
(b) Should the program pivot to Ψ-once for all copilots, or is multi-step Ψ
    worth pursuing for SOC/S2P?
(c) Is the bimodal scoping (§3D) the right response, or should it be sharper?

**J2 — Is the P7 (Ψ design for SOC) specification sufficient?**
The Ψ design question (P7) lists the available edges and poses 4 sub-questions.
(a) Are there missing edges or mechanisms that P1 didn't find?
(b) Is the budget question (max nodes per pass) the right framing, or should
    budget be evidence-bytes / information-gain?
(c) What is the right admission criterion conditioned on v_t?

**J3 — React to the θ_min resolution (§6).**
The prior `α·q·V ≥ θ_min` form is withdrawn; `q ≥ 23.53/(α·V)` is adopted.
(a) Is this the correct interpretation of the conservation constraint?
(b) What happens at zero denominator (α=0 or V=0)?
(c) Is the constant 23.53 derived or conventional?

**J4 — What is the minimum viable characterization?**
Given P1 + pilot + scoping, what is the smallest experiment set that produces
a publishable result (positive or negative)?
(a) Can E0+E1+E3 on SOC alone suffice?
(b) Is cross-domain replication required for a finding, or is SOC-only a valid
    scoped result?

**J5 — Open challenge.** Anything mis-tiered, missing, or wrong.

### Format
Answer by ID (J1–J5). Keep facts separate from opinions. One-paragraph J1 is
more valuable than a five-page J5.

### Context
Read the full v12 memo. The embedded P1 report (Appendix E), the pilot data
(§3A/Appendix D), and the five-judge review (Appendix A) are the key inputs.
The 38-decision parameterization and decision register are external but
summarized in §3B/§10/Appendix A.
```

---

## 7. Execution Next Steps

```
## Next Steps (v12 execution plan)

### Immediate (this week)
1. ✅ P1 resolved — Appendix E produced
2. Send v12 memo to 2-3 LLM judges (Appendix F prompt)
3. Domain owner elicitation: SOC m_topological estimate from real cases (P2)
4. Begin P7: Ψ design for SOC (the highest-leverage build item)

### Build prerequisites (before E0)
- [ ] B1: Non-circular synthetic generator (exists: vld_mechanism_sim.py)
- [ ] B2: A operator via score_read_only (exists: scorer.py)
- [ ] B3: Ψ operator — the hard part. SOC first.
       - Expand campaign members into Decision/Outcome records
       - Correct security-context edge-name mismatches
       - Enforce monotone bounded admission
- [ ] B4: 5-arm + attribution control harness
- [ ] B5: Metrics (truth, baseline-relative ΔU, normalized residual)
- [ ] B6: Bitemporal replay (BLOCKED until AGE as-of reconstruction confirmed)

### Experiment sequence
E0 (instrument gate) → E1 (A0 test) → E2 (contraction map) → **E3 (depth gate/STOP)**
→ E4-E7 if E3 passes.

SOC first. Synthetic defaults for E0-E5; production bitemporal for E6-E7.

### Decision gates
- E0 fails → fix Ψ/harness, do not proceed
- E3 shows Δ_depth ≤ 0 across ≥3 domains → STOP (publishable negative)
- E3 shows Δ_depth > 0 for SOC but not others → SOC-only finding (valid, scoped)
- E3 shows Δ_trajectory > 0 → the loop adds value (update the pilot's finding)
```
