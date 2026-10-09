# DESIGN PRINCIPLES: Judgment Memory Architecture

**Source:** Banerji (2026), “Judgment Memory: A Conservation-Bounded Fourth Cognitive Type for Multi-Domain AI Decision Systems”  
**Extracted:** 2026-10-05  
**Status:** CANONICAL — all copilot-sdk code and architecture decisions must comply.

## Overview

This document extracts the architectural rules established by the Judgment Memory paper so engineers can apply them without reconstructing the paper’s argument. The core design is one governed graph substrate containing episodic, semantic, procedural, and judgment memory, with verified outcomes and conservation bounds governing learning and autonomous scope. In copilot-sdk, AGE is the durable shared-graph backend for production and integrated reasoning experiments; InMemoryGraphStore is a test/development implementation, not a concurrent or alternate source of memory.

## Principle 1: One governed graph is the fundamental memory substrate

**Rule:** Use one logical governed graph as the authoritative memory substrate for all four memory types; do not create a separate authoritative store or graph per component, service, experiment arm, or memory type.

**Rationale:** The graph is valuable not only as a place to persist records, but as the common substrate through which different forms of memory interact. A shared substrate makes cross-type relationships available to one traversal and avoids building a separate synchronization and reconciliation architecture for every interaction.

**Source:** Sections 1, 3.4, 6.4.

**Violation:** The scoring engine writes judgment state to a private in-memory store, the entity service writes semantic links to another store, and event history lives in a third store with no common graph identity.

**Correct:** Compose one active GraphStore for the integrated runtime and persist decisions, verified outcomes, entity relationships, learned procedures, centroid state, and conservation state in its shared graph; isolate domain and experiment records with graph/domain scope, not separate per-component or per-arm stores. InMemoryGraphStore may implement the GraphStore contract for unit tests or local development, but it is not a second runtime authority or a substitute in a reasoning-quality experiment.

## Principle 2: Cross-type interactions are the capability source

**Rule:** Design graph operations so episodic, semantic, procedural, and judgment records can be traversed together where the decision capability requires it.

**Rationale:** The paper identifies the interactions—not merely the presence of each memory type—as the source of emergent capabilities. Trust-trap detection, conservation-gated transfer, and personnel-change analysis depend on traversing between memory types; separate stores add joins and orchestration that often prevent those capabilities from being built. In E-JM-7, per-entity factor weighting detected 2.7x more entity-specific trust traps, while separate stores performed like global-only analysis, demonstrating that the interaction itself matters.

**Source:** Sections 3.4, 6.4; E-JM-7 in Section 6.4.

**Violation:** Compute entity-specific trust from a global centroid table and then look up semantic entity relationships in an unrelated database as an optional second step.

**Correct:** Traverse from the entity to its decisions and associated factor-quality structure in the same graph query, so entity context affects the judgment analysis.

## Principle 3: Decisions and observations are different graph facts

**Rule:** Only a decision with a verified human outcome may enter verified decision count `V`; a preview or GET observation must never become a decision or count toward `V`.

**Rationale:** Pending decisions become confirmed or overridden only through the decision lifecycle. Observations are created by preview/read endpoints, are excluded from conservation and AgentEvolver, and must remain a separate fact type. Mixing them would inflate `V` with unverified evidence and invalidate the conservation guarantee.

**Source:** Section 4.2.

**Violation:** A score-preview GET writes a normal Decision vertex, and the verified-count query includes it before a human has acted.

**Correct:** A preview writes an Observation (or remains non-persistent); only the later verified confirmation or override changes the verified decision record and conservation count.

## Principle 4: Conservation is a non-negotiable quality reserve

**Rule:** Bound autonomous scope with the conservation condition `alpha * q * V >= theta_min`, where `alpha` is category coverage, `q` is accuracy over the rolling 400-decision verified window, and `V` counts confirmed and overridden decisions only.

**Rationale:** Conservation is a circuit breaker and quality reserve, not an optimizer that chooses actions. It restricts adaptation so human-oversight quality remains above a provable floor; the paper gives `theta_min = 23.53 / (alpha * V)` and states that the threshold tightens with verified volume.

**Source:** Sections 4.1 and 4.3.

**Violation:** A system enables autonomous processing because it has accumulated many preview requests, or relaxes the threshold when verified accuracy falls.

**Correct:** Compute coverage and rolling quality from verified decisions, evaluate the conservation condition, and keep autonomous processing gated when the quality reserve is insufficient.

## Principle 5: Judgment memory is a distinct fourth cognitive type

**Rule:** Persist judgment memory as inspectable factor-quality structure conditioned on verified decisions, distinct from event history, entity relationships, and action rules.

**Rationale:** Episodic memory records what happened; semantic memory represents entities and relationships; procedural memory stores policies and rules. Judgment memory represents which factors predict which outcomes in a category/action context, with centroid geometry, a per-factor noise fingerprint, and conservation state.

**Source:** Sections 1, 3.1, 3.2, and 7.

**Violation:** Treat a decision log as judgment memory, infer quality only from hidden model weights, or store one unconditioned factor average for all categories and actions.

**Correct:** Store category/action-conditioned centroids, inspectable per-factor noise diagnostics, and the associated conservation state, updated only from verified outcomes.

## Principle 6: Compounding requires geometric refinement and scope expansion

**Rule:** Preserve both interacting compounding mechanisms: verified decisions refine judgment geometry, and improved quality permits more categories to pass conservation gates.

**Rationale:** Each verified decision incrementally refines centroids and the noise fingerprint; by itself this is sub-linear. Quality gains also make additional categories eligible for autonomous processing. The paper attributes compounding to their multiplicative interaction, not to either mechanism alone.

**Source:** Section 3.2.

**Violation:** Claim compounding because model accuracy improves inside the same fixed category set, while conservation never changes eligible scope—or expand automation without geometric quality improvement.

**Correct:** Measure geometric refinement and eligible-scope expansion separately, and verify that the combined system exhibits their interaction under conservation gates.

## Principle 7: Centroid geometry is a quality reference, not a classifier

**Rule:** Use centroid geometry to evaluate similarity to established quality patterns; leave the decision to the human or the explicitly governed scoring policy.

**Rationale:** The paper explicitly says centroid geometry does not make decisions. It is a reference consulted by the scoring engine to assess how an observation resembles a verified pattern, while the human remains the decision-maker.

**Source:** Section 3.3.

**Violation:** Select and execute an action directly from the nearest centroid, presenting the result as a judgment-memory decision.

**Correct:** Let the scoring engine consult centroid distances as quality evidence, return a recommendation with inspectable evidence, and preserve the human decision and override lifecycle.

## Principle 8: No alternate graph/cache memory substrate; outbox is write-only

**Rule:** Do not add an alternate GraphStore, persistent cache, or query-serving cache to the integrated runtime; the only persistence carve-out is the bounded `PersistenceOutbox` for pending writes during graph outages, and it must never serve reads or cross-type reasoning.

**Rationale:** The paper’s shared-graph argument depends on common graph traversals between memory types. A private cache or per-component store cannot provide those interactions merely by reproducing selected scorer calculations, and even a nominally non-authoritative cache invites backend-specific reads, fallback behavior, and reconciliation. A bounded outage buffer is different: it holds only pending graph writes, drains them to the graph, and is not a queryable memory store. Pure request-local computation memoization is not another memory backend, but it may not replace graph reads or change observable graph semantics. Any persistent or query-serving cache violates the shared-graph requirement and must not be introduced.

**Source:** Sections 3.4 and 6.4; the buffer distinction is an implementation constraint that preserves those shared-graph properties.

**Violation:** Give each experiment arm a fresh InMemoryGraphStore and report its scorer math as evidence about the production system’s reasoning; maintain a second GraphStore or persistent/query-serving cache; or fall back to cached memory when graph reads fail.

**Correct:** Keep the governed graph as the sole memory substrate for reads and cross-type reasoning. During an outage, enqueue pending writes in the bounded `PersistenceOutbox`, report graph-backed reads unavailable, and drain the queued writes after recovery; do not answer queries from the outbox.

## Principle 9: Reasoning-quality experiments must exercise the real shared graph

**Rule:** An experiment that measures system reasoning or cross-memory capability must use an AGE-backed shared graph and the same traversal paths as the evaluated deployment; per-arm InMemoryGraphStore instances are not valid evidence of integrated reasoning quality.

**Rationale:** The paper locates reasoning capability in interactions across memory types and states that separate stores lose those interactions in practice. A fresh InMemoryGraphStore per arm can execute centroid and scorer arithmetic, but it cannot demonstrate that the deployed graph supplies entity context, episodic history, procedures, and conservation together.

**Source:** Sections 3.3, 3.4, and 6.4.

**Violation:** Replace persistent S2P experiment stores with a new per-run InMemoryGraphStore and continue describing the run as an evaluation of the governed reasoning architecture.

**Correct:** Run integrated reasoning experiments against a shared AGE graph configured for the experiment, with experiment-specific domain/ID namespaces and controlled cleanup; all arms must use that common graph substrate. Reserve InMemoryGraphStore for unit tests, development, or isolated algorithm experiments whose claims are explicitly limited to local algorithm behavior.

## Principle 10: Transfer moves governed memory artifacts, not detached rules

**Rule:** Transfer judgment across domains as a governed memory artifact whose factor mapping, validation, and source/target conservation context remain inspectable in the shared graph.

**Rationale:** The paper defines transferable memory artifacts as a discriminator of judgment memory and describes cross-domain judgment transfer as a source of convergence improvement. Transfer gated by conservation requires judgment and conservation state to be jointly visible, rather than copying a detached policy into another store.

**Source:** Sections 3.2, 3.4, 6.4, and 7.

**Violation:** Copy a source domain’s action rule into the target domain without preserving factor mapping, evidence, validation status, or conservation eligibility.

**Correct:** Persist the transfer pattern and its evidence, factor mapping, validation status, and conservation linkage in the graph, then make it eligible only under the target domain’s governance.

## Applying the principles

- Every Codex prompt that makes an architectural decision should read this document first.
- Every code review should check whether changes preserve the shared graph, verified-decision boundary, conservation law, and cross-type traversals.
- When implementation choices are ambiguous, trace the decision back to the cited paper section; do not weaken the shared-graph requirement to accommodate a convenient cache or isolated fixture.

## Cross-reference to copilot-sdk

These are implementation landmarks for applying the principles, not a claim that every current path is already compliant:

| Concern | Code reference |
|---|---|
| Graph persistence contract and traversal capabilities | `copilot_sdk/graph/protocol.py` (`GraphStore`, `GraphTraversalStore`, `ProtocolV2GraphStore`) |
| Backend construction and domain wiring | `copilot_sdk/graph/factory.py` |
| Verified scoring, learning, and outcome lifecycle | `copilot_sdk/scoring/scorer.py`; `copilot_sdk/graph/outcome_service.py` |
| Decision/observation graph contract | `copilot_sdk/graph/protocol.py` (`write_observation`, governed decision methods); `copilot_sdk/scoring/scorer.py` |
| Conservation status and verified-count projection | `copilot_sdk/backend/conservation_utils.py`; `copilot_sdk/backend/conservation_router.py` |
| Entity-context filtering and graph traversal consumers | `copilot_sdk/graph/legacy_signal_filter.py`; `copilot_sdk/backend/transfer_router.py` |
| S2P reasoning experiment harness requiring a shared graph | `apps/s2p_differentiation/engine.py` |
