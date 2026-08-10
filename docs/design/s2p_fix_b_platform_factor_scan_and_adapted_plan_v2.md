# S2P FIX-B — Platform Factor-Architecture Scan & Adapted Plan v2

**Date:** 2026-08-04
**Supersedes:** v1 (adds the deeper-scan confirmation, the reasoned cross-copilot experiment decision, and a clear execution plan).
**Purpose:** answer "why is this S2P-only" deeply, verify it (static scan for four copilots, one runtime experiment for SOC), and adapt the FIX-B path around the answer.

## Claude's finding (Drive scans — the hypothesis to verify)
The shallow answer ("S2P's entities weren't migrated") is wrong. The deep answer, visible in the factor code and now confirmed across all five copilots:

**Exactly two copilots score by traversing a domain-entity subgraph; the other three compute from the event's own fields.**
- **SOC** (factors: privileged_identity_context, asset_criticality, threat_intel_enrichment, pattern_history, time_anomaly, device_trust): reads the alert's **related entities** (User/Asset/ThreatIndicator) via **bespoke typed Cypher** (`neo4j_client`; G12: "explicit Cypher path fragments rather than a generic traversal abstraction"). Entity-context-dependent — and **working.**
- **S2P** (graph-first factors): reads the invoice's related entities (PO/GR/Supplier/Commodity/Contract) via the **generic `query_context`** (label-less VLE). Entity-context-dependent — and **unfinished** (2 of 7 factors are topology-presence stubs; the generic path has the timeout + normalization-reject-to-fixture-fallback bug).
- **Trading / Purchasing / DataOps** compute their factors from the **event's own request fields** (market signals; demand/weather/lead-time; incident severity/blast-radius/sensitivity) — **no entity-subgraph traversal**, so they structurally cannot have the S2P failure mode.

**Why S2P specifically:** it is the only copilot that scores through the *generic* entity-traversal abstraction, and that abstraction plus S2P's graph-first factor rewrite were both left unfinished — masked by fixture fallback. SOC needs entity context too, but built it bespoke and finished. Procurement is inherently relational, so S2P leans hardest on the layer that's least done.

**Reframe of the "decorative graph" worry:** the compounding/**learning** graph (Decisions/centroids/RL/outcomes) is real and used by all five copilots. The **entity-context-for-scoring** layer exists in only two — bespoke-and-working in SOC, generic-and-unfinished in S2P. The graph core is not decorative; only S2P's entity-context path is unfinished. **SOC is the working reference for how to do it right — provided SOC genuinely consumes the graph (verified below, not assumed).**

## Cross-copilot experiments — the decision (thought through)
- **SOC: YES — run one perturbation experiment.** SOC is the *other* entity-context copilot and the pattern we'd model S2P's fix on, so whether SOC's live scoring genuinely reads the graph is **load-bearing**. If SOC also silently falls back (as S2P did — and J6 shows SOC's stored corpus has empty `factor_vector` rows, so this is a live risk), the "working reference" collapses and the platform's entity-context scoring is broken wherever it's used. A static read can't settle this — only perturbation can, exactly as it did for S2P.
- **Trading / Purchasing / DataOps: NO runtime experiment.** They compute from event fields and never traverse an entity subgraph, so they can't have the reject-to-fallback bug. The static scan confirms their factor source; that's sufficient.

This is the same lesson Phase B taught: a copilot can *look* graph-backed and be fixture-fallback; only perturbation distinguishes them — so spend the one experiment where entity-context is actually used (SOC).

---

## Execution plan (ordered — scans, experiments, then the S2P path)
1. **Codex static platform scan (all 5 copilots)** — confirm the factor-source map and stub inventory below.
2. **SOC perturbation experiment (Codex)** — verify SOC's live analyze scoring genuinely reads the graph.
3. **Synthesize** both → is the stub/fallback pattern S2P-only, and is SOC a valid working reference?
4. **Decide the fork (A vs B)** for S2P with that in hand — recommendation: **A, modeled on SOC.**
5. **If A:** study SOC's real factor computation (e.g. `asset_criticality`, `privileged_identity_context`) as the template; design real graph-native `MatchStatus` + `TaxRegulatoryCompliance` for S2P (3-way-match quality from PO/GR amount+qty; compliance from contract clause/threshold fields). **Spike them** in a disposable graph before any migration.
6. **Then** resume Track 1 migration + Phases B2/F/C/D — now with real factors, so the faithfulness gate becomes "decisions are domain-correct," not "match a fixture vector."
Gate: steps 1–2 run first; a "SOC also falls back" result at step 2 changes the whole program (platform-level), so do it before committing S2P effort.

### PROMPT — Codex static platform scan (read-only)
```
TASK: Platform factor-architecture scan. Read-only; no source/test edits; no graph writes.
FOR EACH copilot (SOC/gen-ai-roi-demo-v4-v50, Trading, Purchasing, DataOps, S2P), per factor report:
1. SOURCE: computes from (a) the scoring event's own request/metadata fields, (b) a graph entity-subgraph traversal, or (c) a stored/fixture vector?
2. IF graph-sourced: bespoke typed Cypher (SOC-style neo4j_client) or the generic query_context label-less VLE (S2P-style)? Cite the call site.
3. STUB CHECK: any factor returning fixed constants/buckets on node PRESENCE while ignoring properties (like S2P MatchStatus {0.1,0.6,0.9}, Tax {0.15,0.8})? List them.
4. NORMALIZATION/FALLBACK: does the copilot's context resolution accept its query's row shape or reject→fallback (the S2P bug)? Does scoring silently fall back to stored/fixture factors when context is absent/rejected?
5. ENTITY PRESENCE: are the copilot's scoring entities actually present in live soc_graph, or absent (like S2P)?
6. VERDICT: REAL (computes from live graph properties) / BESPOKE-REAL (SOC typed) / EVENT-FIELD (no graph) / STUB-or-FALLBACK (looks graph-backed, isn't).
SUMMARY: is the stub/fallback pattern S2P-only or shared? Per-copilot table + summary. Change nothing.
```

### PROMPT — SOC perturbation experiment (Codex, disposable/scoped)
```
TASK: Verify SOC scoring is genuinely graph-backed (not fixture fallback), the way Phase B did for S2P. Report-only on committed source; no writes to production soc_graph — use a disposable/scoped SOC graph or a clone; drop after.
1. Stand up SOC on its live analyze path (the path that COMPUTES a factor vector, not the execute/seed path that writes empty vectors — J6). Pick a target alert whose factors read graph context (privileged_identity_context reads User risk/title/MFA; asset_criticality reads Asset; threat_intel_enrichment reads ThreatIndicator).
2. Score it; record the factor vector + action + confidence.
3. PERTURB a graph property the factors read — e.g. change the target alert's User risk_score (or Asset criticality) to a distinctly different value in the disposable graph.
4. Re-score; confirm the corresponding factor (privileged_identity_context / asset_criticality) MOVES, and unrelated factors don't.
REPORT: both scores, which factor moved, latency. VERDICT: SOC genuinely graph-backed = YES/NO. If NO, SOC silently falls back like S2P and the platform's entity-context scoring is broken wherever used — flag as platform-level. Revert; drop the disposable graph.
```

## Do NOT
- Treat this as S2P-only until step 1 confirms it, or model S2P's fix on SOC until step 2 confirms SOC actually reads the graph.
- Run runtime experiments on Trading/Purchasing/DataOps — the static scan is the right tool for event-field factors.
- Model S2P's fix on the generic `query_context` abstraction when SOC's bespoke pattern works.

## Provenance
Factor-source map from Claude's Drive reads of `soc factors.py`, `test_options_scored_factors.py` (Trading), `test_purchasing_factors.py`, `CANONICAL_FACTOR_NAMES.md`, `s2p test_factors.py`; SOC's bespoke-Cypher pattern from `g12_situation_analyzer.md`; SOC's compute-vs-empty-vector paths and the empty-corpus risk from `j6_factor_vector_diagnostic.md`. The stub finding is from `s2p_fix_b_whatif_phase_e_results_v1.md`. Codex confirms live and covers DataOps.
