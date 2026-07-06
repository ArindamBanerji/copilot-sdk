# G12 Situation Analyzer Design

## 1. Executive Summary

G12 turns a scored S2P decision into a bounded, replayable situation explanation: load the decision, select the category-specific traversal pattern, gather graph and scorer context up to three hops, return a structured context chain plus an L1 natural-language explanation. This matters for the S14 scenario because the analyst must see why an invoice exception was scored as price variance, quantity mismatch, duplicate risk, contract gap, or format compliance before confirming or overriding the decision. The current codebase already has partial SDK and S2P situation infrastructure, so G12 should harden and specialize it rather than introduce a parallel stack.

```text
POST /api/s2p/situation/{decision_id}
        |
        v
SituationAnalyzer (SDK)
        |
        v
S2PTraversalPatterns by category
        |
        +--> GraphStore traversal/query_context/query_similar
        +--> fixture/context builder fallback
        +--> scorer factors, DK weights, centroid
        |
        v
ContextChain / SituationContext
        |
        v
NLRenderer -> L1 explanation + confidence
```

## 2. Existing Infrastructure Assessment

### SOC Situation Context

SOC already builds alert context before decisioning. The triage route calls `neo4j_client.get_alert(alert_id)`, then `_soc_get_security_context_for_analyze(alert_id)`, then runs `analyze_situation(alert_type, context)` before scoring (`gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py:491`, `gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py:503`, `gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py:510`). `_soc_get_security_context_for_analyze` delegates to `neo4j_client.get_security_context(alert_id)` and optionally caches stable entity context (`gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py:170`, `gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py:174`, `gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py:182`).

SOC uses explicit Cypher path fragments rather than a generic traversal abstraction. Alert queue traversal matches Alert -> User and Alert -> Asset (`gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py:407`, `gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py:409`, `gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py:410`). Graph visualization matches Alert -> Asset, Alert -> User, optional AttackPattern, TravelContext, MATCHES pattern, and Playbook (`gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py:2923`, `gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py:2925`, `gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py:2928`, `gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py:2930`). It then maps returned records into nodes and relationships for visualization (`gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py:2943`, `gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py:3055`).

SOC also has decision-factor context, including a live ThreatIntel lookup via `(ThreatIntel)-[:ASSOCIATED_WITH]->(Alert)` (`gen-ai-roi-demo-v4-v50/backend/app/services/triage.py:163`, `gen-ai-roi-demo-v4-v50/backend/app/services/triage.py:172`). The extractable idea is not the SOC domain schema; it is the pattern of bounded, named context slices that become key facts, graph visualization nodes, and factor evidence.

### S2P Context Builder

S2P already has a read-only context builder. `S2PContextBuilder` is documented as building fixture/scorer/GraphStore-backed context without graph mutation (`s2p-copilot/backend/app/services/s2p_context_builder.py:67`). It builds invoice context by merging fixture invoice data, request context, metadata, supplier context, PO/contract context, similar decisions, and centroid context (`s2p-copilot/backend/app/services/s2p_context_builder.py:81`, `s2p-copilot/backend/app/services/s2p_context_builder.py:108`, `s2p-copilot/backend/app/services/s2p_context_builder.py:110`, `s2p-copilot/backend/app/services/s2p_context_builder.py:111`, `s2p-copilot/backend/app/services/s2p_context_builder.py:114`, `s2p-copilot/backend/app/services/s2p_context_builder.py:132`).

The builder already emits `TraversalNode`, `TraversalEdge`, `evidence_chain`, warnings, and metadata (`s2p-copilot/backend/app/services/s2p_context_builder.py:58`). It creates invoice, supplier, purchase order, contract, category, decision, similar-decision, and centroid nodes when data is available (`s2p-copilot/backend/app/services/s2p_context_builder.py:396`, `s2p-copilot/backend/app/services/s2p_context_builder.py:172`, `s2p-copilot/backend/app/services/s2p_context_builder.py:252`, `s2p-copilot/backend/app/services/s2p_context_builder.py:299`, `s2p-copilot/backend/app/services/s2p_context_builder.py:452`, `s2p-copilot/backend/app/services/s2p_context_builder.py:482`, `s2p-copilot/backend/app/services/s2p_context_builder.py:538`, `s2p-copilot/backend/app/services/s2p_context_builder.py:344`).

The current limitation is that native graph traversal is explicitly deferred (`s2p-copilot/backend/app/services/s2p_context_builder.py:139`) and similar decisions are found by scanning decision rows from existing GraphStore methods (`s2p-copilot/backend/app/services/s2p_context_builder.py:146`, `s2p-copilot/backend/app/services/s2p_context_builder.py:593`). G12 should keep this as fallback but add category-specific traversal patterns that call explicit graph traversal APIs when available.

### Evidence Templates

The five L1 templates already exist in `S2P_TEMPLATES`: price variance, quantity mismatch, duplicate risk, contract gap, and format compliance (`s2p-copilot/backend/app/services/s2p_evidence_templates.py:66`). Each template declares required fields and factors used (`s2p-copilot/backend/app/services/s2p_evidence_templates.py:75`, `s2p-copilot/backend/app/services/s2p_evidence_templates.py:83`, `s2p-copilot/backend/app/services/s2p_evidence_templates.py:91`, `s2p-copilot/backend/app/services/s2p_evidence_templates.py:102`, `s2p-copilot/backend/app/services/s2p_evidence_templates.py:110`, `s2p-copilot/backend/app/services/s2p_evidence_templates.py:121`).

The template engine consumes context produced from records and factors. `evidence_context_from_record` merges metadata, record fields, and a `factors` dict (`s2p-copilot/backend/app/services/s2p_evidence_templates.py:205`, `s2p-copilot/backend/app/services/s2p_evidence_templates.py:210`, `s2p-copilot/backend/app/services/s2p_evidence_templates.py:214`). Factor-derived variables include `amount_variance_ratio`, `commodity_index_correlation`, `duplicate_score`, `match_status`, and `tax_regulatory_compliance` (`s2p-copilot/backend/app/services/s2p_evidence_templates.py:218`, `s2p-copilot/backend/app/services/s2p_evidence_templates.py:222`). Some template variables are currently defaulted or derived heuristically: `po_qty` defaults to `inv_qty * 0.96`, contract threshold defaults to `20.0`, and duplicate match id defaults to `{invoice_id}-PRIOR` (`s2p-copilot/backend/app/services/s2p_evidence_templates.py:224`, `s2p-copilot/backend/app/services/s2p_evidence_templates.py:236`, `s2p-copilot/backend/app/services/s2p_evidence_templates.py:244`). G12 should replace those defaults with graph-derived variables when available and mark defaults as degraded context.

The evidence router already integrates templates, SituationAnalyzer, DK weights, category phase, verified count, and centroid in `/api/s2p/evidence/template` (`s2p-copilot/backend/app/routers/s2p_evidence.py:321`, `s2p-copilot/backend/app/routers/s2p_evidence.py:337`, `s2p-copilot/backend/app/routers/s2p_evidence.py:356`, `s2p-copilot/backend/app/routers/s2p_evidence.py:365`, `s2p-copilot/backend/app/routers/s2p_evidence.py:367`). The trust explanation helper calls `get_dk_weights`, `get_category_phase`, `get_verified_count`, and `get_centroid` from the scorer (`s2p-copilot/backend/app/routers/s2p_evidence.py:63`, `s2p-copilot/backend/app/routers/s2p_evidence.py:65`, `s2p-copilot/backend/app/routers/s2p_evidence.py:67`, `s2p-copilot/backend/app/routers/s2p_evidence.py:68`).

### GraphStore Protocol

The core `GraphStore` protocol currently covers decision writes, outcome writes, decision reads, decision lists, verified counts, centroid checkpoints, archive, close, and entity enrichment reads/writes (`copilot-sdk/copilot_sdk/graph/protocol.py:15`, `copilot-sdk/copilot_sdk/graph/protocol.py:19`, `copilot-sdk/copilot_sdk/graph/protocol.py:30`, `copilot-sdk/copilot_sdk/graph/protocol.py:39`, `copilot-sdk/copilot_sdk/graph/protocol.py:42`, `copilot-sdk/copilot_sdk/graph/protocol.py:53`, `copilot-sdk/copilot_sdk/graph/protocol.py:65`, `copilot-sdk/copilot_sdk/graph/protocol.py:94`). It does not declare `query_context`, `query_similar`, `link_decision_to_entity`, or `get_decision_links` in the protocol (`copilot-sdk/copilot_sdk/graph/protocol.py:15`, `copilot-sdk/copilot_sdk/graph/protocol.py:130`).

SQLite has decision/entity edge tables and enrichment tables (`copilot-sdk/copilot_sdk/graph/sqlite_store.py:562`, `copilot-sdk/copilot_sdk/graph/sqlite_store.py:668`). It implements `link_decision_to_entity` and `get_decision_links` outside the current protocol (`copilot-sdk/copilot_sdk/graph/sqlite_store.py:2420`, `copilot-sdk/copilot_sdk/graph/sqlite_store.py:2440`). In-memory store implements equivalent link and read helpers (`copilot-sdk/copilot_sdk/graph/memory_store.py:1514`, `copilot-sdk/copilot_sdk/graph/memory_store.py:1532`).

AGE is opt-in through the SDK factory and loaded from `ci_platform.graph.age_sdk_adapter` (`copilot-sdk/copilot_sdk/graph/factory.py:76`, `copilot-sdk/copilot_sdk/graph/factory.py:168`). The AGE adapter forwards `link_decision_to_entity` and `get_decision_links` (`ci-platform/ci_platform/graph/age_sdk_adapter.py:439`, `ci-platform/ci_platform/graph/age_sdk_adapter.py:451`). `AGEGraphStore` already exposes `query_context(entity_id, hops)` and `query_similar(decision_id, limit)` (`ci-platform/ci_platform/graph/age_graph_store.py:2365`, `ci-platform/ci_platform/graph/age_graph_store.py:2376`). AGE traversal differs from SQLite because it can run variable-length graph patterns, while SQLite currently models only selected table joins and decision/entity edges (`ci-platform/ci_platform/graph/age_graph_store.py:2369`, `copilot-sdk/copilot_sdk/graph/sqlite_store.py:562`).

## 3. Architecture

### Core Components

1. `SituationAnalyzer` in `copilot_sdk.situation`
   - Already exists and normalizes signals, dispatches typed intents to registered traversal patterns, and bounds max depth (`copilot-sdk/copilot_sdk/situation/analyzer.py:20`, `copilot-sdk/copilot_sdk/situation/analyzer.py:51`, `copilot-sdk/copilot_sdk/situation/analyzer.py:123`, `copilot-sdk/copilot_sdk/situation/analyzer.py:144`).
   - G12 should extend it only where needed for output naming and confidence metadata, not replace it.

2. `TraversalPattern` protocol
   - Already exists with `domain`, `name`, `default_max_depth`, `supports`, and `traverse` (`copilot-sdk/copilot_sdk/situation/patterns.py:10`, `copilot-sdk/copilot_sdk/situation/patterns.py:14`, `copilot-sdk/copilot_sdk/situation/patterns.py:18`, `copilot-sdk/copilot_sdk/situation/patterns.py:21`).
   - G12 should add category-specific implementations in S2P, not domain code inside SDK.

3. `ContextChain` dataclass
   - The SDK currently has `SituationContext`, `TraversalNode`, `TraversalEdge`, and `TraversalResult` (`copilot-sdk/copilot_sdk/situation/models.py:170`, `copilot-sdk/copilot_sdk/situation/models.py:192`, `copilot-sdk/copilot_sdk/situation/models.py:212`, `copilot-sdk/copilot_sdk/situation/models.py:244`).
   - G12 should either alias `ContextChain = SituationContext` for API vocabulary or introduce a thin dataclass with `chain_id`, `nodes`, `edges`, `evidence_chain`, `confidence`, and `metadata`, serialized from `SituationContext`.

4. `NLRenderer`
   - The SDK has `SafeTemplateRenderer`, which renders safely with defaults and missing-variable tracking (`copilot-sdk/copilot_sdk/situation/templates.py:53`, `copilot-sdk/copilot_sdk/situation/templates.py:56`, `copilot-sdk/copilot_sdk/situation/templates.py:94`).
   - G12 should wrap this as an NLRenderer facade that returns `{nl_explanation, missing_variables, audience}`.

5. `S2PTraversalPatterns`
   - S2P currently has a single broad `S2PInvoiceTraversalPattern` (`s2p-copilot/backend/app/services/s2p_situation_pattern.py:21`).
   - G12 should add five category-specific patterns or one router pattern with five named strategies. The current adapter supports S2P invoice/decision/purchase/supplier subject context (`s2p-copilot/backend/app/services/s2p_situation_pattern.py:30`, `s2p-copilot/backend/app/services/s2p_situation_pattern.py:37`, `s2p-copilot/backend/app/services/s2p_situation_pattern.py:48`), calls `S2PContextBuilder`, and returns `SituationContext` (`s2p-copilot/backend/app/services/s2p_situation_pattern.py:88`, `s2p-copilot/backend/app/services/s2p_situation_pattern.py:105`).

### Traversal Flow

```text
decision_id
  -> graph_store.get_decision(decision_id)
  -> category = decision.category or decision.metadata.category
  -> intent_type = category-to-intent mapping
  -> select S2P category TraversalPattern
  -> traverse graph max 3 hops
  -> build ContextChain/SituationContext
  -> derive NL variables from context + scorer factors + DK weights
  -> render L1 explanation
```

The score endpoint already returns `decision_id`, `category`, `action`, `confidence`, `probabilities`, `factor_vector`, and `factor_names` (`s2p-copilot/backend/app/routers/s2p.py:1546`, `s2p-copilot/backend/app/routers/s2p.py:1555`). The scorer stores factor values and metadata into the GraphStore decision when scoring (`copilot-sdk/copilot_sdk/scoring/scorer.py:240`, `copilot-sdk/copilot_sdk/scoring/scorer.py:267`, `copilot-sdk/copilot_sdk/scoring/scorer.py:272`). Therefore G12 should insert after `POST /api/s2p/score` and before or beside verification/outcome submission. The score route already links the scored decision to the invoice (`s2p-copilot/backend/app/routers/s2p.py:1644`).

### Integration Point

Add:

```http
POST /api/s2p/situation/{decision_id}
```

Endpoint contract:
- Router placement: add to the existing S2P API surface under `/api/s2p`, matching the current S2P router prefix (`s2p-copilot/backend/app/routers/s2p.py:48`) and the score route mounted at `/api/s2p/score` (`s2p-copilot/backend/app/routers/s2p.py:1562`).
- Query parameters: `max_depth` optional, default `3`, allowed range `0..3` for the public endpoint. The SDK analyzer can allow a larger internal cap, but the endpoint must clamp or reject values above 3 before backend traversal.
- Request body: none for the first implementation; all required lookup state comes from `decision_id` and GraphStore.
- Side effects: read-only. The endpoint must not call `score`, `learn`, `write_decision`, `write_outcome`, `link_decision_to_entity`, or the legacy S2P Neo4j writer.
- Error behavior: `404` if `graph_store.get_decision(decision_id)` returns no decision, `422` if the resolved category is not in `S2PDomainConfig.categories`, and `503` if the scorer or graph store is unavailable.

Response:

```json
{
  "decision_id": "abc123",
  "category": "price_variance",
  "context_chain": [
    {"id": "INV-1", "type": "invoice", "depth": 0},
    {"id": "commodity:steel", "type": "commodity_index", "depth": 1},
    {"id": "contract:MSA-42", "type": "contract_clause", "depth": 2},
    {"id": "threshold:price-pass-through", "type": "threshold", "depth": 3}
  ],
  "nl_explanation": "12.4% price delta on invoice INV-1. Steel moved 9.1% over 30 days. Contract MSA-42 allows pass-through up to 10.0%. exceeds bounds. -> hold_for_review. Confidence: 91%.",
  "confidence": 0.91,
  "missing_variables": [],
  "warnings": [],
  "situation_context": {
    "domain": "s2p",
    "decision_id": "abc123",
    "pattern_name": "s2p_price_variance"
  }
}
```

The endpoint response intentionally separates `context_chain` and `nl_explanation` from raw `SituationContext`: the current SDK `SituationContext` contains nodes, edges, evidence chain, warnings, and metadata but no first-class confidence or rendered text fields (`copilot-sdk/copilot_sdk/situation/models.py:212`, `copilot-sdk/copilot_sdk/situation/models.py:220`, `copilot-sdk/copilot_sdk/situation/models.py:222`, `copilot-sdk/copilot_sdk/situation/models.py:225`, `copilot-sdk/copilot_sdk/situation/models.py:226`). G12 should either wrap `SituationContext` in `ContextChain` or place confidence/rendering metadata in a response DTO rather than overloading SDK node or edge properties.

## 4. Traversal Patterns

S2P categories are `price_variance`, `quantity_mismatch`, `duplicate_risk`, `contract_gap`, and `format_compliance` (`s2p-copilot/backend/app/domains/s2p/config.py:20`). The category-to-intent mapping already maps these to triage intents (`s2p-copilot/backend/app/routers/s2p_control_tower.py:19`).

### price_variance

Pattern: `invoice -> commodity index -> contract clause -> threshold`.

Required nodes:
- `invoice`: from fixture/context or GraphStore decision metadata; invoice fixture lookup exists (`s2p-copilot/backend/app/routers/s2p_data_helpers.py:50`).
- `commodity_index`: from context field `commodity` plus factor `commodity_index_correlation`; evidence context currently uses `commodity_index_correlation` to compute `commodity_delta` (`s2p-copilot/backend/app/services/s2p_evidence_templates.py:219`, `s2p-copilot/backend/app/services/s2p_evidence_templates.py:232`).
- `contract_clause`: from `contract_ref` or `contract_id`; current context builder creates a contract reference node but warns that details are unavailable (`s2p-copilot/backend/app/services/s2p_context_builder.py:299`, `s2p-copilot/backend/app/services/s2p_context_builder.py:326`).
- `threshold`: from graph contract data when available; current evidence defaults `threshold` to 20.0 (`s2p-copilot/backend/app/services/s2p_evidence_templates.py:236`).

### quantity_mismatch

Pattern: `invoice -> PO -> GR -> delta computation`.

Required nodes:
- `invoice`: current builder creates an invoice node from fixture data (`s2p-copilot/backend/app/services/s2p_context_builder.py:396`).
- `purchase_order`: current builder creates a PO node from `po_id`, `po_number`, `purchase_order`, or `po` (`s2p-copilot/backend/app/services/s2p_context_builder.py:259`).
- `goods_receipt`: no first-class GR node exists; current PO properties may include `gr_date` (`s2p-copilot/backend/app/services/s2p_context_builder.py:271`).
- `delta`: current evidence computes `delta` as invoice quantity minus PO quantity (`s2p-copilot/backend/app/services/s2p_evidence_templates.py:241`).

### duplicate_risk

Pattern: `invoice -> similar invoices -> supplier -> amount match`.

Required nodes:
- `invoice`: as above.
- `similar_decision` or `similar_invoice`: current builder finds similar decisions by same supplier and category (`s2p-copilot/backend/app/services/s2p_context_builder.py:146`, `s2p-copilot/backend/app/services/s2p_context_builder.py:166`).
- `supplier`: current builder builds supplier context from fixture or request data (`s2p-copilot/backend/app/services/s2p_context_builder.py:172`, `s2p-copilot/backend/app/services/s2p_context_builder.py:179`).
- `amount_match`: current evidence defaults `match_amt` from context amount and `similarity` from `duplicate_score` (`s2p-copilot/backend/app/services/s2p_evidence_templates.py:246`, `s2p-copilot/backend/app/services/s2p_evidence_templates.py:247`).

### contract_gap

Pattern: `invoice -> PO -> contract -> coverage analysis`.

Required nodes:
- `invoice`, `purchase_order`, `contract`: current builder already has invoice, PO, and contract reference node support (`s2p-copilot/backend/app/services/s2p_context_builder.py:396`, `s2p-copilot/backend/app/services/s2p_context_builder.py:252`, `s2p-copilot/backend/app/services/s2p_context_builder.py:299`).
- `coverage_analysis`: current evidence computes `covered_pct` from `match_status` and defaults `gap_items` from match score (`s2p-copilot/backend/app/services/s2p_evidence_templates.py:251`, `s2p-copilot/backend/app/services/s2p_evidence_templates.py:252`).
- Graph contract terms are currently unavailable in the builder (`s2p-copilot/backend/app/services/s2p_context_builder.py:326`), so this pattern needs new fixture/live contract data.

### format_compliance

Pattern: `invoice -> rules -> historical compliance rate`.

Required nodes:
- `invoice`: as above.
- `rules`: evidence router exposes fixture rules with factors including `tax_regulatory_compliance` and `match_status` (`s2p-copilot/backend/app/routers/s2p_evidence.py:399`, `s2p-copilot/backend/app/routers/s2p_evidence.py:416`, `s2p-copilot/backend/app/routers/s2p_evidence.py:424`).
- `historical_compliance`: evidence route computes compliance rate from fixtures using `compute_all_factors` and `tax_regulatory_compliance` (`s2p-copilot/backend/app/routers/s2p_evidence.py:439`, `s2p-copilot/backend/app/routers/s2p_evidence.py:445`, `s2p-copilot/backend/app/routers/s2p_evidence.py:463`).

## 5. NL Template Specification

Audience layer L1 is in scope for G12. L2 and L3 should be deferred because existing templates and router naming are L1-focused (`s2p-copilot/backend/app/services/s2p_evidence_templates.py:1`, `s2p-copilot/backend/app/services/s2p_evidence_templates.py:28`).

### price_variance

Template:

```text
{variance_pct:.1f}% price delta on invoice {invoice_id}. {commodity} moved {commodity_delta:.1f}% over {lookback} days. Contract {ref} {allows_blocks} pass-through up to {threshold:.1f}%. {within_exceeds} bounds. -> {action}. Confidence: {confidence_pct}.
```

Graph variables: `invoice_id`, `commodity`, `commodity_delta`, `lookback`, `ref`, `allows_blocks`, `threshold`, `within_exceeds`.

Scorer variables: `amount_variance_ratio`, `commodity_index_correlation`, `payment_terms_impact`, `confidence`, `action`, DK weights for those factors.

Confidence: start from scorer confidence; reduce if required graph variables are defaulted, unavailable, or fixture-only. Current `RenderedEvidence` stores confidence and `confidence_pct` (`s2p-copilot/backend/app/services/s2p_evidence_templates.py:46`, `s2p-copilot/backend/app/services/s2p_evidence_templates.py:59`).

### quantity_mismatch

Template:

```text
Invoice qty {inv_qty} vs PO {po_qty}; GR confirms {gr_qty} received. Delta {delta}. {match_status}. -> {action}. Confidence: {confidence_pct}.
```

Graph variables: `inv_qty`, `po_qty`, `gr_qty`, `delta`, `match_status`.

Scorer variables: `match_status`, `amount_variance_ratio`, `confidence`, `action`, DK weights for those factors.

Confidence: scorer confidence multiplied by graph completeness for PO and GR nodes.

### duplicate_risk

Template:

```text
Invoice {invoice_id} from {supplier}. Similar candidate {match_id} dated {match_date}, amount {match_amt}, similarity {similarity:.1f}%. {verdict}. -> {action}. Confidence: {confidence_pct}.
```

Graph variables: `invoice_id`, `supplier`, `match_id`, `match_date`, `match_amt`, `similarity`, `verdict`.

Scorer variables: `duplicate_score`, `supplier_exception_history`, `confidence`, `action`, DK weights for those factors.

Confidence: scorer confidence multiplied by similar-match evidence strength; no similar invoice should produce a degraded warning rather than a fabricated match id.

### contract_gap

Template:

```text
PO {po_id}. Contract {ref} covers {scope}; coverage {covered_pct:.1f}%. Gap: {gap_items}. -> {action}. Confidence: {confidence_pct}.
```

Graph variables: `po_id`, `ref`, `scope`, `covered_pct`, `gap_items`.

Scorer variables: `match_status`, `payment_terms_impact`, `confidence`, `action`, DK weights for those factors.

Confidence: scorer confidence multiplied by contract-term availability; contract reference without terms is degraded because the current builder only has `contract_ref` and warns details are unavailable (`s2p-copilot/backend/app/services/s2p_context_builder.py:326`).

### format_compliance

Template:

```text
Invoice from {supplier} fails {n_rules:.0f} format rules. Issues: {issues}. Historical compliance: {compliance_pct:.1f}%. -> {action}. Confidence: {confidence_pct}.
```

Graph variables: `supplier`, `n_rules`, `issues`, `compliance_pct`.

Scorer variables: `tax_regulatory_compliance`, `supplier_exception_history`, `confidence`, `action`, DK weights for those factors.

Confidence: scorer confidence multiplied by availability of rule hit and historical compliance evidence.

## 6. Implementation Plan

### Batch 19: SituationAnalyzer Core Hardening

Files:
- Modify `copilot-sdk/copilot_sdk/situation/models.py`
- Modify `copilot-sdk/copilot_sdk/situation/analyzer.py`
- Modify `copilot-sdk/copilot_sdk/situation/templates.py`
- Add/modify SDK tests under `copilot-sdk/tests/` only in implementation phase

Work:
- Add `ContextChain` as alias or thin dataclass around `SituationContext`.
- Add confidence and chain metadata conventions without domain-specific fields.
- Add an `NLRenderer` facade over `SafeTemplateRenderer`.
- Keep `TraversalPattern` domain-agnostic.

Tests:
- Unit tests for `ContextChain.to_dict`, missing-variable rendering, and max-depth behavior.

Dependencies:
- Existing SDK situation package.

Risks:
- Public SDK compatibility; do not rename existing `SituationContext` fields.

### Batch 20: S2P Traversal Patterns and Graph Queries

Files:
- Modify `s2p-copilot/backend/app/services/s2p_situation_pattern.py`
- Modify `s2p-copilot/backend/app/services/s2p_context_builder.py`
- Add `s2p-copilot/backend/app/services/s2p_traversal_patterns.py`
- Modify or extend S2P fixtures under implementation phase only if fixture data is approved

Work:
- Add five named traversal strategies: `price_variance`, `quantity_mismatch`, `duplicate_risk`, `contract_gap`, `format_compliance`.
- Use `query_context` and `query_similar` when present; fallback to current builder.
- Add forwarding methods for `query_context` and `query_similar` to `AGEGraphStoreAdapter`, because `AGEGraphStore` implements them but the SDK adapter currently only forwards `link_decision_to_entity` and `get_decision_links` (`ci-platform/ci_platform/graph/age_graph_store.py:2365`, `ci-platform/ci_platform/graph/age_graph_store.py:2376`, `ci-platform/ci_platform/graph/age_sdk_adapter.py:439`, `ci-platform/ci_platform/graph/age_sdk_adapter.py:451`).
- Implement SQLite traversal with explicit bounded joins and limits over `decision_entity_edges`, `observations`, and `entity_enrichments`; SQLite has these tables but no native variable-length traversal (`copilot-sdk/copilot_sdk/graph/sqlite_store.py:562`, `copilot-sdk/copilot_sdk/graph/sqlite_store.py:585`, `copilot-sdk/copilot_sdk/graph/sqlite_store.py:668`).
- Preserve provenance fields for fixture, GraphStore, scorer, and unavailable context.
- Add explicit degraded warnings when values are defaulted.

Tests:
- Unit tests for each category pattern using real in-memory/SQLite stores.
- Integration tests for decision id -> category -> traversal.

Dependencies:
- Current `S2PContextBuilder`, `S2PInvoiceTraversalPattern`, GraphStore link helpers.

Risks:
- S2P graph data may lack commodity, goods receipt, contract clause, threshold, and rule nodes.

### Batch 21: NLRenderer and DK Weight Integration

Files:
- Modify `s2p-copilot/backend/app/services/s2p_evidence_templates.py`
- Modify `s2p-copilot/backend/app/routers/s2p_evidence.py`
- Add `s2p-copilot/backend/app/routers/s2p_situation.py`

Work:
- Render the exact five L1 templates from the existing `S2P_TEMPLATES`.
- Merge traversal variables, decision factors, scorer confidence, DK weights, centroid, and category phase.
- Use scorer decision confidence from the persisted decision for `/api/s2p/situation/{decision_id}`. The existing evidence-template endpoint derives confidence from `variables["score"]` (`s2p-copilot/backend/app/routers/s2p_evidence.py:364`), and `evidence_context_from_record` sets that score to the max factor value (`s2p-copilot/backend/app/services/s2p_evidence_templates.py:238`); that behavior is acceptable for the current template preview but is not the right confidence source for a scored decision situation.
- Add confidence computation that reflects scorer confidence and context completeness.
- Return `context_chain`, `nl_explanation`, `confidence`, `missing_variables`, `warnings`, and `trust_weighted_factors`.

Tests:
- Integration tests for all five categories producing non-empty NL and structured chains.
- Tests that missing graph variables are reported, not silently fabricated.

Dependencies:
- Scorer exposes `get_dk_weights`, `get_category_phase`, `get_verified_count`, and `get_centroid` (`copilot-sdk/copilot_sdk/scoring/scorer.py:327`, `copilot-sdk/copilot_sdk/scoring/scorer.py:334`, `copilot-sdk/copilot_sdk/scoring/scorer.py:423`).

Risks:
- DK weights may be `None` until variance learning is active (`copilot-sdk/copilot_sdk/scoring/scorer.py:329`).

### Batch 22: Frontend SituationPanel and PW Specs

Files:
- Modify S2P frontend route/panel files in the implementation phase after locating the active frontend.
- Add Playwright specs under the active e2e suite.

Work:
- Add a SituationPanel beside evidence/verification.
- Fetch `POST /api/s2p/situation/{decision_id}` after score and before verify.
- Display chain nodes, L1 explanation, confidence, warnings, missing variables, and trust-weighted factor rows.

Tests:
- Playwright spec for score -> situation panel -> evidence -> verify.
- Tests must use stable `data-testid` selectors per SDK CLAUDE guidance (`copilot-sdk/CLAUDE.md:72`, `copilot-sdk/CLAUDE.md:78`).

Dependencies:
- Backend endpoint from Batch 21.

Risks:
- Need to identify the active frontend before implementation; this investigation did not modify or inspect frontend files.

## 7. GraphStore Extension Plan

### New Methods

Add a separate optional protocol, not new required methods on `GraphStore`, to preserve structural compatibility:

```python
class GraphTraversalStore(Protocol):
    def query_context(self, entity_id: str, hops: int = 2) -> list[dict[str, Any]]: ...
    def query_similar(self, decision_id: str, limit: int = 5) -> list[dict[str, Any]]: ...
    def get_decision_links(self, decision_id: str | None = None) -> list[dict[str, Any]]: ...
```

Reason: the base `GraphStore` is a public structural protocol (`copilot-sdk/copilot_sdk/graph/protocol.py:15`), and `ProtocolV2GraphStore` was deliberately kept separate so legacy stores can still satisfy the narrow contract (`copilot-sdk/copilot_sdk/graph/protocol.py:131`, `copilot-sdk/copilot_sdk/graph/protocol.py:135`).

### SQLite Implementation

SQLite should implement `query_context` by joining:
- `decisions`
- `decision_entity_edges`
- optionally `entity_enrichments`

Evidence: SQLite already has `decision_entity_edges` (`copilot-sdk/copilot_sdk/graph/sqlite_store.py:562`), `entity_enrichments` (`copilot-sdk/copilot_sdk/graph/sqlite_store.py:668`), `link_decision_to_entity` (`copilot-sdk/copilot_sdk/graph/sqlite_store.py:2420`), and `get_decision_links` (`copilot-sdk/copilot_sdk/graph/sqlite_store.py:2440`). SQLite cannot do native arbitrary graph traversal, so `hops` should be bounded and implemented as explicit joins/expansions over known edge tables.

### AGE Implementation

AGE already has `query_context(entity_id, hops)` and `query_similar(decision_id, limit)` (`ci-platform/ci_platform/graph/age_graph_store.py:2365`, `ci-platform/ci_platform/graph/age_graph_store.py:2376`). `query_context` clamps hops through `_safe_hops`, which returns a value in `1..5` (`ci-platform/ci_platform/graph/age_graph_store.py:195`, `ci-platform/ci_platform/graph/age_graph_store.py:200`), and `query_similar` clamps limits through `_safe_limit`, which returns a value in `1..1000` (`ci-platform/ci_platform/graph/age_graph_store.py:187`, `ci-platform/ci_platform/graph/age_graph_store.py:192`). The SDK adapter must forward those methods like it already forwards `get_decision_links` (`ci-platform/ci_platform/graph/age_sdk_adapter.py:451`).

AGE queries must avoid unsupported `MERGE`; the AGE client rejects `MERGE` (`ci-platform/ci_platform/graph/age_client.py:111`). G12 should call store methods or use AGE literal helpers, not introduce raw `$params` in new S2P router code. The current AGE client inlines `$name` parameter values before execution (`ci-platform/ci_platform/graph/age_client.py:451`), and documents that AGE does not support `$1` positional params inside dollar-quoted blocks (`ci-platform/ci_platform/graph/age_client.py:422`). Keeping G12 traversal read-only and store-mediated avoids dialect drift.

### Backward Compatibility

Do not add traversal methods to `GraphStore` directly in Batch 19. Use `getattr` capability checks in S2P patterns first, matching current S2P score behavior where `_resolve_graph_context` calls `query_context` only if present (`s2p-copilot/backend/app/routers/s2p.py:76`). After SQLite and AGE both implement the optional protocol, a later cleanup can promote it to a documented extension.

## 8. Test Plan

Unit tests:
- SDK `SituationAnalyzer`: no pattern, pattern selected, max depth, context metadata.
- SDK `NLRenderer`: exact template rendering, missing variables, numeric formatting.
- S2P patterns: one test per category with real in-memory or SQLite store.
- Evidence templates: no hardcoded fallback appears when graph values are supplied.

Integration tests:
- Score an invoice, capture `decision_id`, call situation endpoint, assert category-specific chain and explanation.
- Verify `context_chain` includes no nodes beyond depth 3.
- Assert warning when contract details or GR data are unavailable.
- Assert DK weights are included when `get_dk_weights` returns data and marked unavailable when `None`.
- Assert the situation endpoint is read-only by comparing decision count and decision links before and after the call.
- Assert `max_depth > 3` is rejected or clamped at the public endpoint, even though the SDK analyzer may have a higher internal `max_allowed_depth`.
- Assert AGE adapter traversal is exercised through `AGEGraphStoreAdapter.query_context`/`query_similar` once those forwarding methods are added.

Fixture requirements:
- Price variance: invoice, commodity, commodity_delta, contract_ref, threshold.
- Quantity mismatch: invoice quantity, PO quantity, GR quantity.
- Duplicate risk: at least one prior same-supplier/same-category invoice or decision.
- Contract gap: PO, contract reference, covered scope, gap items.
- Format compliance: failed rules and historical compliance rate.

Playwright plan:
- Score flow displays situation panel.
- Evidence panel and situation panel agree on category/action/confidence.
- Missing graph data produces visible warning state.
- Use stable `data-testid` selectors, not layout-position selectors (`copilot-sdk/CLAUDE.md:74`, `copilot-sdk/CLAUDE.md:78`).

## 9. Risk Register

1. GraphStore Protocol backward compatibility
   - Risk: adding required methods to `GraphStore` breaks structural implementations.
   - Mitigation: add optional `GraphTraversalStore` and use capability checks.

2. AGE query safety
   - Risk: AGE rejects `MERGE` and needs literal interpolation.
   - Evidence: AGE client forbids `MERGE` (`ci-platform/ci_platform/graph/age_client.py:111`) and serializes parameters into Cypher literals (`ci-platform/ci_platform/graph/age_client.py:451`).
   - Mitigation: reuse AGE helper serialization and avoid write traversal in G12.

3. Performance
   - Risk: unbounded graph expansion.
   - Evidence: `SituationAnalyzer` already bounds max depth (`copilot-sdk/copilot_sdk/situation/analyzer.py:144`); AGE `query_context` accepts bounded hops (`ci-platform/ci_platform/graph/age_graph_store.py:2365`).
   - Mitigation: max depth 3 for endpoint; hard cap 5 in analyzer.

4. Fixture vs live data paths
   - Risk: current S2P context often uses fixture/context data.
   - Evidence: builder provenance marks fixture context as integration pending (`s2p-copilot/backend/app/services/s2p_context_builder.py:18`, `s2p-copilot/backend/app/services/s2p_context_builder.py:20`) and metadata marks native traversal deferred (`s2p-copilot/backend/app/services/s2p_context_builder.py:139`).
   - Mitigation: preserve provenance and expose degraded warnings.

5. S2P graph data availability
   - Risk: commodity index, GR, contract clauses, thresholds, and historical rules may not exist as graph nodes.
   - Evidence: current builder warns contract details are unavailable (`s2p-copilot/backend/app/services/s2p_context_builder.py:326`) and current evidence defaults missing values (`s2p-copilot/backend/app/services/s2p_evidence_templates.py:236`, `s2p-copilot/backend/app/services/s2p_evidence_templates.py:244`).
   - Mitigation: Batch 20 fixture/live data work must define minimal node schemas before endpoint is considered production complete.

6. AGE adapter traversal gap
   - Risk: S2P code that checks `hasattr(graph_store, "query_context")` will not see AGE traversal when the graph store is an `AGEGraphStoreAdapter`, because the adapter currently forwards decision link helpers but not `query_context` or `query_similar`.
   - Evidence: `AGEGraphStore` implements `query_context` and `query_similar` (`ci-platform/ci_platform/graph/age_graph_store.py:2365`, `ci-platform/ci_platform/graph/age_graph_store.py:2376`), while the adapter excerpt forwards `link_decision_to_entity` and `get_decision_links` only (`ci-platform/ci_platform/graph/age_sdk_adapter.py:439`, `ci-platform/ci_platform/graph/age_sdk_adapter.py:451`).
   - Mitigation: Batch 20 must add adapter forwarding methods before AGE-backed situation traversal is considered implemented.

7. Legacy S2P Neo4j writer is not AGE-safe
   - Risk: the score route calls a legacy S2P graph write path that uses `MERGE`; copying that pattern into G12 would violate AGE safety.
   - Evidence: `write_s2p_decision` uses `MERGE` (`s2p-copilot/backend/app/domains/s2p/graph.py:31`), while AGE rejects `MERGE` (`ci-platform/ci_platform/graph/age_client.py:111`).
   - Mitigation: G12 situation endpoint must remain read-only and must use GraphStore traversal APIs, not the legacy S2P Neo4j writer.

8. Confidence source mismatch
   - Risk: current evidence template preview confidence can differ from scorer decision confidence because it derives confidence from the max factor score.
   - Evidence: `/api/s2p/evidence/template` sets `confidence = float(variables.get("score") or 0.0)` (`s2p-copilot/backend/app/routers/s2p_evidence.py:364`), while `evidence_context_from_record` computes `score` as the max factor value (`s2p-copilot/backend/app/services/s2p_evidence_templates.py:238`); the scorer returns persisted decision confidence separately (`copilot-sdk/copilot_sdk/scoring/scorer.py:277`, `copilot-sdk/copilot_sdk/scoring/scorer.py:281`).
   - Mitigation: G12 must use persisted decision/scorer confidence as the base and apply context-completeness adjustments only after that.

9. S2P factor-count documentation drift
   - Risk: hardcoding factor count from docs can break G12 factor/DK alignment.
   - Evidence: `s2p-copilot/CLAUDE.md` says S2P tensor is `(5, 5, 7)` (`s2p-copilot/CLAUDE.md:32`), while current `S2PDomainConfig` defines eight factors and `N_FACTORS = 8` (`s2p-copilot/backend/app/domains/s2p/config.py:38`, `s2p-copilot/backend/app/domains/s2p/config.py:84`).
   - Mitigation: implementation must read `S2PDomainConfig.factors` at runtime and never hardcode the factor count.

## 10. Reading Log

- `copilot-sdk/CLAUDE.md:5` says docs are aspirational until proven in code.
- `copilot-sdk/CLAUDE.md:6` requires file and line citations for behavioral claims.
- `copilot-sdk/CLAUDE.md:24` says the SDK is a public package for domain copilots.
- `copilot-sdk/CLAUDE.md:41` says SDK protocols must not leak domain internals.
- `copilot-sdk/CLAUDE.md:53` says not to use git directly.
- `s2p-copilot/CLAUDE.md:25` says S2P is a procurement domain copilot.
- `s2p-copilot/CLAUDE.md:41` says S2P is an independent domain.
- `s2p-copilot/CLAUDE.md:55` says not to use git directly.
- `gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py:170` defines `_soc_get_security_context_for_analyze`.
- `gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py:174` calls `neo4j_client.get_security_context`.
- `gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py:407` starts alert queue Cypher.
- `gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py:453` defines `/alert/analyze`.
- `gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py:503` fetches security context in analysis.
- `gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py:514` calls `analyze_situation`.
- `gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py:1097` fetches graph visualization data.
- `gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py:2917` defines graph data builder.
- `gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py:2923` uses a bounded explicit graph query.
- `gen-ai-roi-demo-v4-v50/backend/app/services/triage.py:163` defines threat-intel factor builder.
- `gen-ai-roi-demo-v4-v50/backend/app/services/triage.py:172` queries ThreatIntel associated with Alert.
- `s2p-copilot/backend/app/domains/s2p/config.py:20` defines S2P categories.
- `s2p-copilot/backend/app/domains/s2p/config.py:29` defines S2P actions.
- `s2p-copilot/backend/app/domains/s2p/config.py:38` defines S2P factors.
- `s2p-copilot/backend/app/domains/s2p/config.py:58` contains evidence template strings.
- `s2p-copilot/backend/app/domains/s2p/graph.py:12` defines S2P decision graph write.
- `s2p-copilot/backend/app/domains/s2p/graph.py:31` uses `MERGE` for Neo4j-style S2PDecision write.
- `s2p-copilot/backend/app/models/intents.py:11` defines `IntentType`.
- `s2p-copilot/backend/app/models/intents.py:38` defines `INTENT_METADATA`.
- `s2p-copilot/backend/app/routers/s2p_control_tower.py:19` maps categories to triage intents.
- `s2p-copilot/backend/app/routers/s2p_control_tower.py:27` maps intents to categories.
- `s2p-copilot/backend/app/routers/s2p_control_tower.py:54` maps intents to evidence panels.
- `s2p-copilot/backend/app/routers/s2p_control_tower.py:92` infers intent from category/factors.
- `s2p-copilot/backend/app/routers/s2p.py:70` defines `_resolve_graph_context`.
- `s2p-copilot/backend/app/routers/s2p.py:76` checks for `query_context`.
- `s2p-copilot/backend/app/routers/s2p.py:1524` defines score request fields.
- `s2p-copilot/backend/app/routers/s2p.py:1546` defines score response fields.
- `s2p-copilot/backend/app/routers/s2p.py:1562` defines `/api/s2p/score`.
- `s2p-copilot/backend/app/routers/s2p.py:1600` resolves graph context during scoring.
- `s2p-copilot/backend/app/routers/s2p.py:1601` computes factors.
- `s2p-copilot/backend/app/routers/s2p.py:1605` calls scorer.score.
- `s2p-copilot/backend/app/routers/s2p.py:1644` links decision to invoice.
- `s2p-copilot/backend/app/routers/s2p.py:1693` defines outcome request fields.
- `s2p-copilot/backend/app/routers/s2p.py:1725` defines the SDK-shaped learn endpoint.
- `s2p-copilot/backend/app/routers/s2p_data_helpers.py:19` loads invoice fixtures.
- `s2p-copilot/backend/app/routers/s2p_data_helpers.py:24` loads supplier fixtures.
- `s2p-copilot/backend/app/routers/s2p_data_helpers.py:50` finds invoice by event or invoice id.
- `s2p-copilot/backend/app/services/s2p_context_builder.py:58` defines context build result fields.
- `s2p-copilot/backend/app/services/s2p_context_builder.py:67` defines context builder.
- `s2p-copilot/backend/app/services/s2p_context_builder.py:81` builds invoice context.
- `s2p-copilot/backend/app/services/s2p_context_builder.py:146` finds similar decisions.
- `s2p-copilot/backend/app/services/s2p_context_builder.py:252` builds PO/contract context.
- `s2p-copilot/backend/app/services/s2p_context_builder.py:344` builds centroid context.
- `s2p-copilot/backend/app/services/s2p_context_builder.py:593` reads decisions via GraphStore methods.
- `s2p-copilot/backend/app/services/s2p_evidence_templates.py:66` defines the five S2P templates.
- `s2p-copilot/backend/app/services/s2p_evidence_templates.py:126` defines `S2PEvidenceEngine`.
- `s2p-copilot/backend/app/services/s2p_evidence_templates.py:137` renders evidence.
- `s2p-copilot/backend/app/services/s2p_evidence_templates.py:205` builds evidence context from a record.
- `s2p-copilot/backend/app/services/s2p_situation_pattern.py:21` defines current S2P traversal pattern.
- `s2p-copilot/backend/app/services/s2p_situation_pattern.py:63` traverses an intent.
- `s2p-copilot/backend/app/services/s2p_situation_pattern.py:88` calls `S2PContextBuilder`.
- `s2p-copilot/backend/app/services/s2p_situation_pattern.py:105` returns `SituationContext`.
- `s2p-copilot/backend/app/routers/s2p_evidence.py:17` imports current S2P traversal pattern.
- `s2p-copilot/backend/app/routers/s2p_evidence.py:19` imports SDK SituationAnalyzer.
- `s2p-copilot/backend/app/routers/s2p_evidence.py:321` defines template endpoint.
- `s2p-copilot/backend/app/routers/s2p_evidence.py:337` creates SituationAnalyzer with S2P pattern.
- `s2p-copilot/backend/app/routers/s2p_evidence.py:356` analyzes intent.
- `copilot-sdk/copilot_sdk/situation/analyzer.py:20` defines `SituationAnalyzer`.
- `copilot-sdk/copilot_sdk/situation/analyzer.py:100` defines `analyze_decision`.
- `copilot-sdk/copilot_sdk/situation/analyzer.py:123` defines `analyze_intent`.
- `copilot-sdk/copilot_sdk/situation/models.py:100` defines `TypedIntent`.
- `copilot-sdk/copilot_sdk/situation/models.py:170` defines `TraversalNode`.
- `copilot-sdk/copilot_sdk/situation/models.py:192` defines `TraversalEdge`.
- `copilot-sdk/copilot_sdk/situation/models.py:212` defines `SituationContext`.
- `copilot-sdk/copilot_sdk/situation/patterns.py:10` defines `TraversalPattern`.
- `copilot-sdk/copilot_sdk/situation/templates.py:53` defines `SafeTemplateRenderer`.
- `copilot-sdk/copilot_sdk/graph/protocol.py:15` defines `GraphStore`.
- `copilot-sdk/copilot_sdk/graph/protocol.py:131` defines separate `ProtocolV2GraphStore`.
- `copilot-sdk/copilot_sdk/graph/factory.py:16` recognizes sqlite and age backends.
- `copilot-sdk/copilot_sdk/graph/factory.py:76` loads AGE adapter.
- `copilot-sdk/copilot_sdk/graph/factory.py:133` creates SQLite GraphStore by default.
- `copilot-sdk/copilot_sdk/graph/factory.py:168` constructs AGE adapter.
- `copilot-sdk/copilot_sdk/graph/sqlite_store.py:562` defines decision entity edges.
- `copilot-sdk/copilot_sdk/graph/sqlite_store.py:668` defines entity enrichments.
- `copilot-sdk/copilot_sdk/graph/sqlite_store.py:2420` links decisions to entities.
- `copilot-sdk/copilot_sdk/graph/sqlite_store.py:2440` reads decision links.
- `copilot-sdk/copilot_sdk/scoring/scorer.py:71` defines score result fields.
- `copilot-sdk/copilot_sdk/scoring/scorer.py:129` predicts factors/category/action/probabilities.
- `copilot-sdk/copilot_sdk/scoring/scorer.py:240` scores and persists a decision.
- `copilot-sdk/copilot_sdk/scoring/scorer.py:327` exposes DK weights.
- `copilot-sdk/copilot_sdk/scoring/scorer.py:334` exposes centroid vectors.
- `copilot-sdk/copilot_sdk/scoring/scorer.py:434` learns from verified outcome.
- `copilot-sdk/copilot_sdk/scoring/scorer.py:1014` exposes GraphStore as single source of truth.
- `ci-platform/ci_platform/graph/age_sdk_adapter.py:10` defines AGE SDK adapter.
- `ci-platform/ci_platform/graph/age_sdk_adapter.py:439` forwards `link_decision_to_entity`.
- `ci-platform/ci_platform/graph/age_sdk_adapter.py:451` forwards decision links.
- `ci-platform/ci_platform/graph/age_graph_store.py:187` defines AGE safe limit clamping.
- `ci-platform/ci_platform/graph/age_graph_store.py:195` defines AGE safe hop clamping.
- `ci-platform/ci_platform/graph/age_graph_store.py:2365` defines AGE `query_context`.
- `ci-platform/ci_platform/graph/age_graph_store.py:2376` defines AGE `query_similar`.
- `ci-platform/ci_platform/graph/age_client.py:8` documents AGE dialect differences.
- `ci-platform/ci_platform/graph/age_client.py:111` rejects MERGE.
- `ci-platform/ci_platform/graph/age_client.py:422` documents literal interpolation.

## Output Summary

READY_FOR_IMPLEMENTATION: YES, after applying the explicit Batch 20 AGE adapter forwarding requirement and endpoint read-only/max-depth constraints above.

PLAN_FILE: `copilot-sdk/docs/implementation_plans/g12_situation_analyzer.md`

EXISTING_INFRASTRUCTURE: SDK already has `SituationAnalyzer`, `TraversalPattern`, `SituationContext`, and `SafeTemplateRenderer`; S2P already has `S2PInvoiceTraversalPattern`, `S2PContextBuilder`, five L1 evidence templates, DK/trust explanation integration, score-time GraphStore persistence, and evidence endpoint wiring. The missing G12 work is category-specific traversal chains, explicit read-only situation endpoint, graph traversal protocol hardening, AGE adapter traversal forwarding, replacement of heuristic template defaults with graph-derived variables, scorer-confidence-based NL output, and frontend SituationPanel integration.

BLOCKERS: No design blocker. Implementation risk remains around graph data availability for commodity index, goods receipt, contract clauses, thresholds, rules, and historical compliance nodes. Required pre-implementation corrections are now captured for AGE adapter traversal forwarding, read-only endpoint behavior, max-depth enforcement, confidence source selection, and factor-count drift. Also note `copilot-sdk/copilot_sdk/scoring/profile_scorer.py` was requested but does not exist; scorer evidence was taken from `copilot-sdk/copilot_sdk/scoring/scorer.py`, which imports `gae.profile_scorer`.
