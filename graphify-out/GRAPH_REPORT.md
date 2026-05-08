# Graph Report - copilot-sdk  (2026-05-03)

## Corpus Check
- 35 files · ~13,583 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 281 nodes · 269 edges · 35 communities detected
- Extraction: 96% EXTRACTED · 4% INFERRED · 0% AMBIGUOUS · INFERRED: 10 edges (avg confidence: 0.74)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_Community 0|Community 0]]
- [[_COMMUNITY_Community 1|Community 1]]
- [[_COMMUNITY_Community 2|Community 2]]
- [[_COMMUNITY_Community 3|Community 3]]
- [[_COMMUNITY_Community 4|Community 4]]
- [[_COMMUNITY_Community 5|Community 5]]
- [[_COMMUNITY_Community 6|Community 6]]
- [[_COMMUNITY_Community 7|Community 7]]
- [[_COMMUNITY_Community 8|Community 8]]
- [[_COMMUNITY_Community 9|Community 9]]
- [[_COMMUNITY_Community 10|Community 10]]
- [[_COMMUNITY_Community 11|Community 11]]
- [[_COMMUNITY_Community 12|Community 12]]
- [[_COMMUNITY_Community 13|Community 13]]
- [[_COMMUNITY_Community 14|Community 14]]
- [[_COMMUNITY_Community 15|Community 15]]
- [[_COMMUNITY_Community 16|Community 16]]
- [[_COMMUNITY_Community 17|Community 17]]
- [[_COMMUNITY_Community 18|Community 18]]
- [[_COMMUNITY_Community 19|Community 19]]
- [[_COMMUNITY_Community 20|Community 20]]
- [[_COMMUNITY_Community 21|Community 21]]
- [[_COMMUNITY_Community 22|Community 22]]
- [[_COMMUNITY_Community 23|Community 23]]
- [[_COMMUNITY_Community 24|Community 24]]
- [[_COMMUNITY_Community 25|Community 25]]
- [[_COMMUNITY_Community 26|Community 26]]
- [[_COMMUNITY_Community 27|Community 27]]
- [[_COMMUNITY_Community 28|Community 28]]
- [[_COMMUNITY_Community 29|Community 29]]
- [[_COMMUNITY_Community 30|Community 30]]
- [[_COMMUNITY_Community 31|Community 31]]
- [[_COMMUNITY_Community 32|Community 32]]
- [[_COMMUNITY_Community 33|Community 33]]
- [[_COMMUNITY_Community 34|Community 34]]

## God Nodes (most connected - your core abstractions)
1. `InterventionControls` - 14 edges
2. `SOCAgent` - 6 edges
3. `compute_iks()` - 6 edges
4. `DomainConfig` - 6 edges
5. `_entry_to_dict()` - 5 edges
6. `EventBus` - 5 edges
7. `SimilarCasesBase` - 5 edges
8. `DecisionResult` - 4 edges
9. `FrozenROICalculator` - 4 edges
10. `build_provenance()` - 4 edges

## Surprising Connections (you probably didn't know these)
- `InterventionControls` --uses--> `CheckpointService`  [INFERRED]
  copilot_sdk\framework\intervention_controls.py → copilot_sdk\framework\checkpoint.py
- `test_hello_world_iks_cold_start()` --calls--> `compute_iks()`  [INFERRED]
  tests\test_hello_world.py → copilot_sdk\framework\iks_base.py
- `test_hello_world_demo_runs()` --calls--> `compute_iks()`  [INFERRED]
  tests\test_hello_world.py → copilot_sdk\framework\iks_base.py
- `CompositeDiscriminant` --uses--> `DecisionHistoryService`  [INFERRED]
  copilot_sdk\framework\composite_gate.py → copilot_sdk\framework\decision_history.py
- `test_iks_cold_start_returns_zero()` --calls--> `compute_iks()`  [INFERRED]
  tests\test_framework_discipline.py → copilot_sdk\framework\iks_base.py

## Communities

### Community 0 - "Community 0"
Cohesion: 0.1
Nodes (13): InterventionControls, InterventionControls — P22 Consolidated Oversight Panel (L-12).  EU AI Act Artic, Restore centroid snapshot.          Parameters         ----------         previe, Force all decisions to human review (disabled=True) or restore., Force specific category to human review., Change auto-approve confidence threshold per category.          Rejects threshol, Return current state of all controls., Return intervention audit log from Neo4j. (+5 more)

### Community 1 - "Community 1"
Cohesion: 0.08
Nodes (12): NarrativeProvider, Protocol, DomainConfig, DomainConfig Protocol — register a new copilot domain. Implement this protocol t, FactorComputer, FactorComputer Protocol — compute one factor value from event context. Returns f, Returns factor value in [0.0, 1.0]., ReferralRule Protocol — domain-specific VETO rules. REFER is a hard VETO — canno (+4 more)

### Community 2 - "Community 2"
Cohesion: 0.09
Nodes (11): HelloWorldConfig, Hello World domain — minimal 2-category, 3-action, 2-factor copilot. The simples, compute_factor_vector(), ScoreAFactor, ScoreBFactor, tests/test_hello_world.py — Hello World smoke tests., test_hello_world_demo_runs(), test_hello_world_factor_vector_length() (+3 more)

### Community 3 - "Community 3"
Cohesion: 0.1
Nodes (12): tests/test_discipline.py — SDK boundary discipline tests.  Enforces:  - No domai, FactorComputer defines compute(event) -> float as required by GAE., SourceConnector has fetch/validate; ReferralRule has evaluate., Top-level `import copilot_sdk` completes without error and is versioned., Importing copilot_sdk must not trigger torch, tensorflow,         transformers,, No domains.soc module appears in sys.modules after importing copilot_sdk., No domains.s2p module appears in sys.modules after importing copilot_sdk., AST scan of all .py files under copilot_sdk/ for forbidden import patterns. (+4 more)

### Community 4 - "Community 4"
Cohesion: 0.13
Nodes (17): _entry_to_dict(), get_decisions(), SOC Audit Service — thin adapter over ci_platform Evidence Ledger.  Hash-chain i, Append a sealed LedgerEntry to the ci_platform ledger and return it as a SOC dic, Find the most-recent LedgerEntry for alert_id and update its outcome.      Mutat, Return all decision records, most recent first, excluding RESET sentinels., Back-fill the ledger from existing session state — specifically     FEEDBACK_GIV, Clear all decision records (demo reset). (+9 more)

### Community 5 - "Community 5"
Cohesion: 0.12
Nodes (16): compute_iks(), interpret(), interpret_iks_v2(), _mean_centroid_drift(), IKS (Institutional Knowledge Score) algorithm for CopilotFramework. compute_iks(, Return a human-readable interpretation of the IKS (v1) score., Return a human-readable interpretation of the IKS v2 composite score., Compute mean ‖μ(t)[c,a,:] − μ₀[c,a,:]‖₂ over all (c, a) pairs.      Parameters (+8 more)

### Community 6 - "Community 6"
Cohesion: 0.15
Nodes (9): DecisionResult, SOC Copilot Agent - Simple Rule-Based Decision Engine ~150 lines total. The demo, Agent decision output, Calculate faithfulness score: Does reasoning match decision and context?, Evaluate 4 deterministic eval gates.         All are deterministic checks - no L, Simple rule-based SOC decision engine.     No LLM orchestration - just determini, Determine if this decision should trigger an evolution event.          Returns:, Main decision function. Rule-based logic.          Args:             alert_type: (+1 more)

### Community 7 - "Community 7"
Cohesion: 0.13
Nodes (11): DecisionMade, EventBus, GraphMutated, OutcomeVerified, Lightweight event bus for SOC Copilot (v4.1 — replaced by ci-platform at v4.5)., Emitted after a Decision node is written to the graph.     Channel A: Decision n, Emitted after a Decision node is marked correct/incorrect.     Channel B: Outcom, Emitted for every graph write (decision or outcome).     Provides a single audit (+3 more)

### Community 8 - "Community 8"
Cohesion: 0.18
Nodes (7): build_provenance(), DecisionProvenance, FactorProvenance, get_provenance_from_graph(), ProvenanceService, ProvenanceService — factor provenance and decision audit trail (Phase 6).  Provi, Builds factor provenance records for a decision.

### Community 9 - "Community 9"
Cohesion: 0.21
Nodes (8): cosine_similarity(), get_theta(), SimilarCaseFinder ABC for CopilotFramework. Domain implementations supply SOC/S2, Return up to k similar past Decision nodes for *category*.          Category fil, Return fraction of *similar_cases* whose action matches *current_action*., Case-based reasoning retrieval — domain subclass supplies get_theta()., Fetch up to *limit* verified Decision nodes for *category* from Neo4j,         m, SimilarCasesBase

### Community 10 - "Community 10"
Cohesion: 0.2
Nodes (6): CompositeDiscriminant, CompositeDiscriminant — multi-signal auto-approve gate (Phase 5).  Uses 13 featu, Multi-signal auto-approve gate.      Uses scorer output features + graph context, DecisionHistoryService, DecisionHistoryService — per-category decision counts and rolling accuracy.  Pro, Tracks per-category decision counts and rolling accuracy.

### Community 11 - "Community 11"
Cohesion: 0.2
Nodes (9): get_all_trust_scores(), get_reward_summary(), get_trust_status(), Feedback trust/reward mechanics for CopilotFramework. Domain-agnostic — no SOC r, Return all current trust scores and the full update history.      Returns     --, Aggregate current in-memory feedback state into an RL reward summary.      Rewar, Update trust score for a situation type after a decision outcome.      Asymmetri, Get trust status for a single situation type.      Returns     -------     { (+1 more)

### Community 12 - "Community 12"
Cohesion: 0.2
Nodes (9): load_from_file(), make_state(), LearningState singleton for CopilotFramework. Domain layer (SOC/S2P) builds the, Read the metadata field from the checkpoint. Returns {} if absent., Atomically persist W matrix + WeightUpdate history to a JSON checkpoint.      Us, Create a fresh LearningState from raw parameters., Deserialize W matrix and WeightUpdate history from a JSON checkpoint.      Param, read_checkpoint_metadata() (+1 more)

### Community 13 - "Community 13"
Cohesion: 0.22
Nodes (8): create_narrative_provider(), get_narrative_provider(), NarrativeProvider ABC for CopilotFramework. Domain implementations (e.g. Templat, Set the module-level singleton. Called once at app startup., Register a NarrativeProvider class under a name.      Called by the domain servi, Create a NarrativeProvider instance by name.      Args:         provider_type: n, register_narrative_provider(), set_narrative_provider()

### Community 14 - "Community 14"
Cohesion: 0.29
Nodes (3): CheckpointService, CheckpointService — centroid checkpoint and rollback (TD-033, Phase 4 §17.5).  C, Centroid checkpoint and rollback (TD-033).

### Community 15 - "Community 15"
Cohesion: 0.29
Nodes (3): ShadowModeService — Phase 4 shadow mode (§21).  Shadow mode: system makes decisi, Shadow mode: system makes decisions but does not act on them.     Analyst action, ShadowModeService

### Community 16 - "Community 16"
Cohesion: 0.33
Nodes (5): decisions_to_days(), predict_n_half(), Domain-agnostic convergence math for CopilotFramework.  CLAIM-CONV-01 (V-MV-CONV, Predict N_half (decisions to 50% convergence) from deployment params.     CLAIM-, Convert decision count to calendar days.     V IS used here — volume determines

### Community 17 - "Community 17"
Cohesion: 0.33
Nodes (3): FrozenROICalculator, Compute frozen-mode annual ROI.          Returns dict with:           time_saved, ROI for frozen scorer mode (LEARNING_ENABLED=False).      Three value drivers, a

### Community 18 - "Community 18"
Cohesion: 0.5
Nodes (3): get_ols_status(), ols_status.py — OLS (Override Lift Score) Dashboard service (L-09).  Uses GAE 0., Compute OLS dashboard status for the frontend.      Parameters     ----------

### Community 19 - "Community 19"
Cohesion: 1.0
Nodes (1): copilot-sdk — Build compounding intelligence copilots.  The engine is open. The

### Community 20 - "Community 20"
Cohesion: 1.0
Nodes (1): Domain-agnostic feedback state store for CopilotFramework.  FEEDBACK_GIVEN is ex

### Community 21 - "Community 21"
Cohesion: 1.0
Nodes (1): CopilotFramework — domain-agnostic copilot infrastructure.  This package is desi

### Community 22 - "Community 22"
Cohesion: 1.0
Nodes (1): Hello World demo — score + IKS in 30 lines. Run: python examples/hello_world/dem

### Community 23 - "Community 23"
Cohesion: 1.0
Nodes (1): Snapshot current centroids to a Checkpoint node in Neo4j.          Parameters

### Community 24 - "Community 24"
Cohesion: 1.0
Nodes (1): Return all Checkpoint nodes ordered by timestamp DESC.

### Community 25 - "Community 25"
Cohesion: 1.0
Nodes (1): Restore centroids from a Checkpoint node and freeze the scorer.          Paramet

### Community 26 - "Community 26"
Cohesion: 1.0
Nodes (1): Evaluate whether a decision should be auto-approved.          Parameters

### Community 27 - "Community 27"
Cohesion: 1.0
Nodes (1): Get decision count and rolling accuracy for a category.          Uses the last 1

### Community 28 - "Community 28"
Cohesion: 1.0
Nodes (1): Build provenance for a decision.          Parameters         ----------

### Community 29 - "Community 29"
Cohesion: 1.0
Nodes (1): Retrieve a stored decision's factor vector from Neo4j and rebuild provenance.

### Community 30 - "Community 30"
Cohesion: 1.0
Nodes (1): Mark a Decision node as shadow_mode=True.

### Community 31 - "Community 31"
Cohesion: 1.0
Nodes (1): Record what the analyst actually did (the ground truth).         Also sets d.agr

### Community 32 - "Community 32"
Cohesion: 1.0
Nodes (1): Generate shadow mode report: agreement rates by category.          Returns

### Community 33 - "Community 33"
Cohesion: 1.0
Nodes (1): Return cosine similarity in [0, 1].  Returns 0.0 for zero vectors.

### Community 34 - "Community 34"
Cohesion: 1.0
Nodes (1): Return per-category cosine similarity threshold for retrieval.

## Knowledge Gaps
- **114 isolated node(s):** `copilot-sdk — Build compounding intelligence copilots.  The engine is open. The`, `SOC Copilot Agent - Simple Rule-Based Decision Engine ~150 lines total. The demo`, `Agent decision output`, `Simple rule-based SOC decision engine.     No LLM orchestration - just determini`, `Main decision function. Rule-based logic.          Args:             alert_type:` (+109 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **Thin community `Community 19`** (2 nodes): `__init__.py`, `copilot-sdk — Build compounding intelligence copilots.  The engine is open. The`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 20`** (2 nodes): `feedback_store.py`, `Domain-agnostic feedback state store for CopilotFramework.  FEEDBACK_GIVEN is ex`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 21`** (2 nodes): `__init__.py`, `CopilotFramework — domain-agnostic copilot infrastructure.  This package is desi`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 22`** (2 nodes): `demo.py`, `Hello World demo — score + IKS in 30 lines. Run: python examples/hello_world/dem`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 23`** (1 nodes): `Snapshot current centroids to a Checkpoint node in Neo4j.          Parameters`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 24`** (1 nodes): `Return all Checkpoint nodes ordered by timestamp DESC.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 25`** (1 nodes): `Restore centroids from a Checkpoint node and freeze the scorer.          Paramet`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 26`** (1 nodes): `Evaluate whether a decision should be auto-approved.          Parameters`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 27`** (1 nodes): `Get decision count and rolling accuracy for a category.          Uses the last 1`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 28`** (1 nodes): `Build provenance for a decision.          Parameters         ----------`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 29`** (1 nodes): `Retrieve a stored decision's factor vector from Neo4j and rebuild provenance.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 30`** (1 nodes): `Mark a Decision node as shadow_mode=True.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 31`** (1 nodes): `Record what the analyst actually did (the ground truth).         Also sets d.agr`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 32`** (1 nodes): `Generate shadow mode report: agreement rates by category.          Returns`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 33`** (1 nodes): `Return cosine similarity in [0, 1].  Returns 0.0 for zero vectors.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 34`** (1 nodes): `Return per-category cosine similarity threshold for retrieval.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `compute_iks()` connect `Community 5` to `Community 2`?**
  _High betweenness centrality (0.013) - this node is a cross-community bridge._
- **Why does `test_hello_world_demo_runs()` connect `Community 2` to `Community 5`?**
  _High betweenness centrality (0.009) - this node is a cross-community bridge._
- **Are the 3 inferred relationships involving `compute_iks()` (e.g. with `test_iks_cold_start_returns_zero()` and `test_hello_world_iks_cold_start()`) actually correct?**
  _`compute_iks()` has 3 INFERRED edges - model-reasoned connections that need verification._
- **What connects `copilot-sdk — Build compounding intelligence copilots.  The engine is open. The`, `SOC Copilot Agent - Simple Rule-Based Decision Engine ~150 lines total. The demo`, `Agent decision output` to the rest of the system?**
  _114 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Community 0` be split into smaller, more focused modules?**
  _Cohesion score 0.1 - nodes in this community are weakly interconnected._
- **Should `Community 1` be split into smaller, more focused modules?**
  _Cohesion score 0.08 - nodes in this community are weakly interconnected._
- **Should `Community 2` be split into smaller, more focused modules?**
  _Cohesion score 0.09 - nodes in this community are weakly interconnected._