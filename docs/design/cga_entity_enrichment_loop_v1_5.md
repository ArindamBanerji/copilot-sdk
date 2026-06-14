# CGA Entity Enrichment Loop Architecture

****Version:** 1.4
**Date:** June 13, 2026
**Status:** Design — for review + math framework integration
**Authority:** math_synopsis v18, Product Integrity Strategy v2.4
**Triggered by:** P39 design gap discovery + P38 provenance review

---

## §1 — What We Found

### 1.1 The Discovery

The CGA scoring engine has multiple pathways that make individual
decisions better: centroids learn judgment, DK estimates factor
trust, conservation gates safety. But all of these improve what the
SCORER does with the factors. The factors themselves never improve.

Every time an invoice from Supplier X arrives, the factor vector is
computed from the same sources — invoice fields + fixture context.
The scorer may be wiser about what those factors mean, but the
factors are unchanged.

Entity enrichment adds a second feedback loop to the SCORING ENGINE:

```
LOOP 1 (existing): Decision → Outcome → Centroid Update → Better Scoring
LOOP 2 (new):      Decisions → Outcomes → Entity Enrichment → Richer Factors
```

Loop 1 changes how the scorer INTERPRETS factors.
Loop 2 changes what the factors ARE.

**This is a scoring pathway, not a compounding pathway.**

The distinction matters:

| Category | What it does | Examples |
|---|---|---|
| **Scoring pathways** | Make individual decisions better within a fixed decision function | Centroids, DK, conservation, referral, enrichment, kernel, η asymmetry |
| **Compounding pathways** | Create EMERGENT capabilities that didn't exist at decision 0 | AgentEvolver, SituationAnalysis, ProcessTechFusion, cross-copilot transfer, RL |

Entity enrichment doesn't create emergent capabilities. After 10,000
decisions, the system has better supplier exception rates, but it's
still making the same KIND of decision with richer inputs. AgentEvolver
creates rules that didn't exist. Process-Tech Fusion transfers
intelligence across systems. Those are qualitatively different.

**Why enrichment matters despite being "only" a scoring pathway:**

It's the only scoring pathway that changes the FACTOR SPACE rather
than the scorer STATE. All other scoring pathways (centroids, DK,
conservation) modify the scorer's internal state while receiving the
same factors. Enrichment modifies the factors while the scorer
adapts. This is unique, architecturally significant, and increases
the effective discriminative dimensionality of the scoring space:
richer factors give the scorer more structure to learn from.

### 1.2 The Two-Loop Scoring Engine

```
SCORING ENGINE (7 pathways):

  STATE pathways (modify scorer internals):
    1. Centroid learning       → μ moves toward correct patterns
    2. DK weight estimation    → w learns which factors to trust
    3. Conservation            → α·q·V gates automation safety
    4. Referral calibration    → thresholds adapt to analyst patterns
    5. L2 kernel choice        → +36.89pp from distance metric
    6. η asymmetry             → conservative penalization (5:1)

  INPUT pathway (modifies factor space):
    7. Entity enrichment       → entity knowledge from verified decisions
       ↑ the only pathway that changes what the FACTORS are

COMPOUNDING INTELLIGENCE (separate, emergent):
    - AgentEvolver             → rules evolve from patterns
    - SituationAnalysis        → contextual WHY explanations
    - ProcessTechFusion        → WHERE→WHY→WHAT→LEARN→TRANSFER
    - Cross-copilot transfer   → domain portability
    - RL exploration           → strategy discovery
    - Context Connectors       → external knowledge integration
```

### 1.3 Why This Matters Commercially

Entity enrichment is the scoring pathway that makes the "smarter
with every decision" claim literally true for the DATA, not just
the scorer. After 150 verified invoices from Chen-Lin, the system
knows their exception rate, accuracy pattern, and trend — compiled
from YOUR AP team's decisions.

No competitor has this. Coupa builds rules. Zycus fine-tunes models.
Neither derives entity-level knowledge from verified decisions and
feeds it back as scoring input.

### 1.4 The Rowboat Labs Connection

Rowboat Labs (https://www.rowboatlabs.com/) demonstrated automated
knowledge graph construction through NLP extraction and document
analysis. Their approach enriches graphs from EXTERNAL sources.

CGA's enrichment loop enriches graphs from INTERNAL sources —
verified decisions. The two are complementary:

| Source | Provenance | Factor eligible? |
|---|---|---|
| Rowboat-style extraction | `integration` / `context` | No (until validated against decisions) |
| CGA enrichment loop | `verified_outcomes` / `learned` | Yes (after N_min threshold) |

Future integration: CGA consumes Rowboat-enriched graphs as context
inputs and COMPOUNDS on them through verified decisions. External
enrichment starts as context; CGA makes it learned.

**Promotion path (integration → learned):**

External enrichment can be promoted to `factor_eligible=True` when:
1. The external value has been present on ≥ N_min decisions
2. The value correlates with verified outcomes (the system's
   decisions involving entities with that external attribute have
   measurable accuracy ≥ θ for the attribute's categories)
3. The correlation is computed by the CGA enrichment service, not
   asserted by the external source

Until promoted, external enrichment is display-only with
`provenance_tier="context"`. Promotion is a CGA-internal decision
based on verified-outcome evidence, not an external claim.

---

## §2 — Mathematical Implications

### 2.0 What Changes and What Doesn't

**The formalism doesn't change.** The centroid update rule, the DK
estimator, the conservation formula, the re-convergence theorem —
none need modification. The existing proofs hold in the post-
enrichment steady state.

**What changes is the CONDITIONS under which the proofs apply.**
Enrichment breaks the stationarity assumption during the transition
period (fixture → measured factors). The math section specifies
what this means and what gates protect against it.

**Why enrichment is mathematically distinct from other scoring
pathways:**

All other scoring pathways modify the scorer's internal STATE
(μ, w, α, q) while receiving the SAME factor vector x ∈ ℝ^D.
The factor space is fixed — every decision sees the same D
dimensions computed the same way.

Enrichment modifies the FACTOR SPACE. The nominal dimension D
stays the same, but the INFORMATION CONTENT of the factor vector
changes. Factors that were constants (fixture = 0.5 for all
entities) become variables (enriched = 0.15 to 0.85 depending on
entity history).

Formally: before enrichment, if factor j is fixture for all
entities, then x_j = c (constant). Factor j has zero
DISCRIMINATIVE power — the centroid value μ_j = c for every
(category, action) pair, so it contributes nothing to the distance
computation that distinguishes categories. The effective
discriminative dimensionality is D_eff = D - k, where k factors
are degenerate (fixture). Enrichment removes k' ≤ k degeneracies,
increasing D_eff to D - (k - k').

Note: degenerate factors are not absent from the computation — the
scorer still processes all D dimensions. But the centroid structure
in those dimensions is flat (all same value), so the scorer learns
nothing from them. Enrichment gives those dimensions structure.

The centroids μ were learned in a space where k dimensions had no
structure. After enrichment activates, centroids need to learn
the category-specific means in the newly-variable dimensions.
This is the precise characterization of the "distribution shift."

### 2.1 Factor Distribution Shift at Enrichment Activation

When enrichment replaces fixture with measured values, the factor
distribution P(x | category, action) shifts.

**Characterization of the shift:**

Let x_j^(before) = c (fixture, constant for all entities in
category/action pair). After enrichment:

x_j^(after) ~ F_j(entity_history)

where F_j is the enrichment-derived distribution for factor j.

The centroid for (category, action) was:
μ_ca^(before) = E[x | cat=c, act=a] with x_j = constant

After enrichment:
μ_ca^(after) = E[x | cat=c, act=a] with x_j ~ F_j

The centroid shift in factor j is:
Δμ_ca,j = E[F_j | cat=c, act=a] - c

**Re-convergence applies.** The same centroid-distance proof path
holds: centroids move toward the new means with each verified
decision. The convergence rate depends on |Δμ|, which is the
magnitude of the enrichment-induced shift.

**Quantitative bound on convergence time:**

If k' factors are enriched and the enrichment shift per factor is
δ, the centroid recovery time per affected (category, action) pair
is approximately:

N_recovery ≈ log₂(δ / τ) × N_half

where δ is the absolute centroid shift in the enriched dimension
(e.g., fixture c=0.5 → enriched mean E[F_j]=0.2 gives δ=0.3),
τ is the convergence tolerance (use τ=0.01 for production), and
N_half ≈ 14 decisions (the centroid EMA half-life at q̄≥0.70 from
DK calibration work, UNI-DK-01 v5.3).

**Worked examples:**

| Scenario | δ | τ | log₂(δ/τ) | N_half | N_recovery |
|---|---|---|---|---|---|
| Small shift (0.5→0.4) | 0.1 | 0.01 | 3.3 | 14 | ~47 decisions |
| Medium shift (0.5→0.2) | 0.3 | 0.01 | 4.9 | 14 | ~69 decisions |
| Large shift (0.5→0.1) | 0.4 | 0.01 | 5.3 | 14 | ~74 decisions |
| Negligible shift (0.5→0.45) | 0.05 | 0.01 | 2.3 | 14 | ~32 decisions |

Note: these are per (category, action) centroid. Calendar time
depends on the arrival rate for that pair. Concrete values for the
math synopsis update, not this document.

**What if enrichment doesn't improve the factor?** Example: fixture
exception_rate = 0.5, measured exception_rate = 0.50. The enrichment
adds measurement noise without signal. The centroid shift δ ≈ 0, so
N_recovery ≈ 0 (no shift to recover from). The DK estimator handles
this correctly: if the enriched factor has low between-category
variance (same value across categories), DK assigns low weight.
The system neither benefits nor is harmed — enrichment is neutral
for that metric. This is safe but the evidence panel should still
show it honestly (measured=True, but the value happens to match the
fixture default).

**Why the v1.0 formula was wrong:** The earlier bound k'×(δ/η)²
had three errors: (1) centroid updates use geometric EMA decay, so
convergence is LOGARITHMIC in δ, not quadratic; (2) the rate is
~1/η not 1/η²; (3) k' factors don't multiply because centroid
updates are vector-valued — all D dimensions update simultaneously
on each verified decision, so k' enriched dimensions recover IN
PARALLEL, not sequentially. The corrected bound is per-centroid,
not per-factor-dimension.

**Caveat:** This bound is per (category, action) centroid. The
CALENDAR TIME depends on the arrival rate of decisions for that
(category, action) pair. A category that sees 10 decisions/day
recovers in ~2 days. A category that sees 1 decision/week takes
~2 months.

**The gradual-vs-batch recommendation now rests on different
arguments** (since recovery time is logarithmic, not quadratic,
the time difference is smaller than v1.0 implied):

```
BATCH:    conservation may dip temporarily (all centroids shift at once)
          DK variance is artificial during transition (the real argument)
GRADUAL:  conservation dip is imperceptible per-entity
          DK mixed-distribution problem is avoided
```

The DK coverage gate (§2.3) and conservation dip are the primary
arguments for gradual enrichment, not recovery time.

**Recommendation: gradual enrichment.**

The worked examples above show recovery takes 32-74 decisions per
centroid regardless of batch or gradual. The arguments for gradual
are about DK and conservation, not recovery speed:

- **Gradual:** DK coverage grows smoothly (no bimodal spike);
  conservation dip is imperceptible per-entity
- **Batch:** DK sees artificial variance from mixed distribution
  (the §2.3 gate catches this); conservation may dip temporarily
  as all centroids shift simultaneously

### 2.2 Conservation With Endogenous Factors

Conservation computes α·q·V ≥ θ_min where q is rolling verified
accuracy over a window of decisions.

**Before enrichment:** factors are exogenous (given by input,
independent of scorer state). This is the standard assumption.

**After enrichment:** factors become partially endogenous
(enrichment computed from decisions, which depend on scoring).

**Does this break conservation?**

No. The formula remains valid because:

1. **q is operational rolling accuracy** — computed from the
   scorer's predictions compared to analyst outcomes over a window
   of W recent verified decisions. (This is distinct from held-out
   benchmark accuracy used in tests.) The analyst provides the
   ground truth through verification, regardless of factor source.

2. **The formula doesn't assume exogenous factors.** It only
   assumes q is a meaningful accuracy measure. As long as verified
   decisions are genuinely verified (analyst reviewed), q is valid.

3. **In the pathological case** (bad enrichment → bad factors →
   low accuracy → conservation AMBER), conservation correctly
   pauses automation. Recovery requires analyst verifications on
   the new (bad) factor distribution, which generates correct
   training data that eventually fixes the centroids AND (through
   the enrichment loop) fixes the enrichment.

**Recovery is two-stage, not single-loop.** Unlike the centroid-only
loop where re-convergence happens as fast as outcomes arrive, the
enrichment loop recovery has two stages: (1) analyst verifications
provide correct outcomes → centroids begin recovering, (2) the
corrected outcomes feed enrichment recomputation → enriched factor
values improve. With gradual enrichment (continuous recomputation),
both stages happen in parallel. With batch enrichment, stage 2
has a lag until the next batch runs.

**What conservation CANNOT catch:** If analysts rubber-stamp
decisions (automation bias), "verified" echoes the scorer's prior.
Enrichment then encodes the scorer's assumptions, q stays GREEN,
and the system detaches from ground truth while appearing healthy.
Conservation's q measures accuracy against ANALYST outcomes — if
the analyst is not genuinely verifying, q is meaningless.

**Mitigation (not conservation):** Override-rate monitor (if
analyst override rate drops below a floor, flag for review) +
periodic independently-labeled probes (sample decisions re-labeled
by a second reviewer) + verified-only as an enforced invariant in
the enrichment API. This is a FIRST-CLASS RISK, not a footnote.

### 2.3 DK Weight Estimation During Enrichment Transition

DK estimates the diagonal kernel weights w ∈ ℝ^D using the
James-Stein shrinkage estimator, which compares between-category
variance (signal) to within-category variance (noise) for each
factor dimension.

**For fixture factors (pre-enrichment):**

x_j = c for all entities. Between-category variance = 0.
Within-category variance = 0. The James-Stein shrinkage estimator
sees a 0/0 ratio for this dimension. In practice, the DK estimator
assigns w_j close to the uniform baseline (1/D) because there is
no evidence to deviate from the prior. The factor contributes to
centroid distance but carries no discriminative signal — it shifts
all distances equally.

**For enriched factors (post-enrichment):**

x_j varies by entity. Between-category variance > 0 if different
categories have different enrichment patterns. DK should assign
higher w_j — the enriched factor now carries information.

**The transition period is the problem.**

When fraction p of entities have enriched x_j and (1-p) still have
fixture x_j, the marginal distribution of x_j is bimodal:

```
P(x_j) = p × F_j(enriched) + (1-p) × δ(c)
```

The variance of this mixture is:

Var(x_j) = p × Var(F_j) + p(1-p) × (E[F_j] - c)²

This variance is ARTIFICIAL — it comes from mixing two populations,
not from real information content. The DK estimator would see high
variance and potentially assign high w_j, even though the variance
is from the transition, not from genuine signal.

**Gate:**

```python
def should_reestimate_dk_for_factor(factor_index, enrichment_coverage):
    """Only re-estimate DK when enrichment coverage is sufficient.
    Coverage = fraction of entities IN THE CURRENT DK ESTIMATION
    WINDOW (not all-time) that have enriched values for this factor.
    An entity enriched 6 months ago but absent from the recent
    window doesn't count. Below 80%, the distribution is bimodal
    from mixing enriched and fixture — DK estimates are unreliable."""
    return enrichment_coverage.get(factor_index, 0.0) >= 0.80
```

When coverage IN THE ESTIMATION WINDOW crosses 80%, the distribution
is dominated by enriched values and the variance estimate is
reliable. Below 80%, hold w_j at its current value (do not
re-estimate on mixed data).

**This is a gate, not a formula change.** DK estimation itself is
unchanged. It simply waits until the input distribution is stable.

### 2.4 Enrichment Threshold (N_min)

An entity's enrichment becomes a factor source ONLY after N_min
verified decisions for that entity. Below N_min, enrichment is
display-only.

**Statistical justification:**

If the true exception rate is p, the standard error after N
verified decisions is SE = √(p(1-p)/N).

| N_min | SE at p=0.15 | SE at p=0.50 |
|---|---|---|
| 5 | 0.160 | 0.224 |
| 10 | 0.113 | 0.158 |
| 20 | 0.080 | 0.112 |
| 50 | 0.050 | 0.071 |

At N_min = 20, a 15% exception rate has SE ≈ 8% (95% CI roughly
0%-31%, clipped at zero). Noisy but directionally useful — good
enough for a factor input that the scorer will learn to weight
appropriately through DK. At N_min = 5, SE = 16% — the enrichment
value is too noisy to serve as a stable factor input.

**Domain-specific N_min values:**

```
S2P:        20 verified decisions per supplier
SOC:        50 verified decisions per entity
Purchasing: 10 verified orders per vendor (smaller volumes)
DataOps:    30 verified decisions per data source
Trading:    N/A (no entity enrichment in v1)
```

**Implementation:**

```python
@dataclass(frozen=True)
class ProvenancedValue:
    value: Any
    source: str
    provenance_tier: str
    source_count: int
    factor_eligible: bool  # True only if source_count >= N_min
    ...

# In factor computation:
def compute_supplier_risk_factor(enrichment: ProvenancedValue) -> float:
    if enrichment.factor_eligible:
        return enrichment.value  # measured, sufficient data
    else:
        return DEFAULT_FIXTURE_VALUE  # fixture, insufficient data
```

### 2.5 Summary: What Changes in the Math Framework

| Aspect | Change? | Detail |
|---|---|---|
| Centroid update rule | **No** | Same η-weighted update toward verified outcome |
| DK shrinkage estimator | **No** | Same James-Stein formula |
| Conservation formula | **No formula change** | Same α·q·V ≥ θ_min. New documentation: endogenous-factor caveat + two-stage recovery mechanism |
| Re-convergence theorem | **No** | Same proof paths; enrichment is a special case of distribution shift |
| Stationarity assumption | **Qualified** | Breaks during transition; add gate + recovery bound |
| DK estimation conditions | **New gate** | Skip enrichment-dependent factors until >80% coverage |
| Factor eligibility | **New concept** | N_min threshold on ProvenancedValue |
| Recovery bound | **New result** | N_recovery ≈ log₂(δ/τ) × N_half per centroid (logarithmic, not quadratic) |
| Effective dimensionality | **New characterization** | D_eff increases as fixture degeneracies are removed |
| Conservation endogenous caveat | **New documentation** | Recovery needs analyst verification + enrichment recomputation |

**The math framework gains 4 new items (gate, threshold, bound,
characterization) but no changes to existing formulas.**

---

## §3 — Architecture

### 3.1 The Enrichment Write API (P39A)

The storage substrate. Domain-neutral, provenance-safe.

```python
# GraphStore protocol extension

def write_entity_enrichment(
    self,
    *,
    domain: str,
    entity_type: str,       # "Supplier", "User", "Vendor"
    entity_id: str,
    namespace: str,          # "s2p_supplier_metrics"
    metrics: dict[str, ProvenancedValue],
    computed_from: EnrichmentSourceSet,
    dry_run: bool = False,
    idempotency_key: str | None = None,
) -> EntityEnrichmentReceipt:
    """Write enrichment metrics to graph.
    Enrichment namespace is separated from base entity fields.
    Protected fields cannot be overwritten."""

def read_entity_enrichment(
    self,
    *,
    domain: str,
    entity_type: str,
    entity_id: str,
    namespace: str | None = None,
) -> dict[str, ProvenancedValue]:
    """Read enrichment metrics. Returns empty dict if not enriched."""
```

**Key constraint:** Enrichment writes NEVER touch base entity
identity fields (id, name, created_at, domain). Enrichment lives
in a namespace, separated from canonical entity data.

**Why `namespace` exists (not premature abstraction):**

Namespace enables multiple enrichment producers per domain. S2P
examples today all use `"s2p_supplier_metrics"`, but the intended
pattern supports:

```
s2p_supplier_metrics       ← P39B: exception_rate, accuracy, trend
s2p_supplier_financial     ← future: payment terms, credit risk
s2p_supplier_external      ← Rowboat/connector: industry, ESG
```

Each namespace is an independent enrichment producer with its own
provenance lineage. Without namespace, all enrichment for an entity
is a single flat dict — producers overwrite each other.

### 3.2 ProvenancedValue (Extended for Factor Eligibility)

**Relationship to Provenanced[T]:** Product Integrity v2.4 defines
`Provenanced[T]` with 3 fields (value, source, label) — a minimal
type for evidence-builder boundaries. `ProvenancedValue` below is
the enrichment-specific extension with full provenance metadata.
Import paths stay separate: `copilot_sdk.evidence.provenance` for
`Provenanced[T]`, `copilot_sdk.graph.enrichment` for
`ProvenancedValue`. Never re-export one from the other's module.

```python
@dataclass(frozen=True)
class ProvenancedValue:
    value: Any
    source: str              # verified_outcomes | graph_store | fixture | scorer | integration
    provenance_tier: str     # learned | measured_verified | context | integration_pending | unavailable
    source_count: int        # how many verified decisions/outcomes
    factor_eligible: bool    # True only if source_count >= N_min
    provenance_label: str = ""     # human-readable, e.g. "computed from 150 verified decisions"
    measured: bool = False         # backed by real measurement?
    verified: bool = False         # backed by verified outcomes?
    computed_at: str = ""          # ISO timestamp
    warnings: list[str] = field(default_factory=list)

    # --- Factory methods (make legal states easy, illegal states hard) ---

    @classmethod
    def from_verified(cls, value, source_count: int,
                      n_min: int = 20, label: str = "",
                      **kwargs) -> 'ProvenancedValue':
        """Construct from verified outcomes. Provenance is automatic."""
        return cls(
            value=value, source="verified_outcomes",
            provenance_tier="learned",
            source_count=source_count,
            factor_eligible=source_count >= n_min,
            measured=True, verified=True,
            provenance_label=label or f"computed from {source_count} verified decisions",
            **kwargs)

    @classmethod
    def from_fixture(cls, value,
                     label: str = "integration pending",
                     **kwargs) -> 'ProvenancedValue':
        """Construct from fixture/context data. Cannot claim verified."""
        return cls(
            value=value, source="fixture",
            provenance_tier="context",
            source_count=0, factor_eligible=False,
            measured=False, verified=False,
            provenance_label=f"supplier context · {label}",
            **kwargs)

    @classmethod
    def unavailable(cls, label: str = "unavailable",
                    **kwargs) -> 'ProvenancedValue':
        """Construct for missing data. Honest absence."""
        return cls(
            value=None, source="unavailable",
            provenance_tier="unavailable",
            source_count=0, factor_eligible=False,
            measured=False, verified=False,
            provenance_label=label,
            **kwargs)
```

The `factor_eligible` field is the gate between display-only and
factor-input enrichment. Below N_min verified decisions, the
enrichment appears in the evidence chain but does NOT feed scoring.

**`to_display()` method (type reconciliation):**

```python
def to_display(self) -> 'Provenanced':
    """Downcast to the evidence-rendering type (3 fields).
    Used by P38 context builder and evidence templates."""
    from copilot_sdk.evidence.provenance import Provenanced
    return Provenanced(
        value=self.value,
        source=self.source,
        label=self.provenance_label or f"{self.provenance_tier}"
    )
```

### 3.3 The Enrichment-as-Factor Pipeline

```
                    DISPLAY ONLY                    FACTOR INPUT
                    (always)                        (after N_min)
                    
Verified            Evidence chain:                 Factor computation:
decisions     →     "exception_rate: 15%            supplier_risk = f(
accumulate          (150 verified decisions)"         exception_rate,
                    source: learned ██               accuracy, trend)
                                                    
                    Provenance rendering             Centroid learning
                    in evidence panel                on enriched factors
```

**The transition from display-only to factor-input is automatic
when source_count crosses N_min.** No manual intervention needed.
But the DK re-estimation gate (§2.3) prevents premature trust
recalibration during the transition.

### 3.4 Architecture Layering

```
Layer 0: GraphStore Entity Enrichment API (P39A)
         write_entity_enrichment / read_entity_enrichment
         SQLite + Memory + AGE implementations
         Domain-neutral. Provenance-safe.

Layer 1: Domain Enrichment Service (P39B, P44, ...)
         S2P: S2PSupplierEnrichmentService
         SOC: SOCEntityEnrichmentService (future)
         Computes enrichment from domain-specific decisions/outcomes
         ** Runs as BACKGROUND JOB (periodic or on-demand) **
         ** NOT on the hot scoring path **

Layer 2: Factor Integration (new — this document)
         FactorEnrichmentAdapter per copilot
         Reads enrichment, gates on factor_eligible
         Supplies enriched factor values to scorer
         ** Runs on the scoring path — must be fast (cache read) **

Layer 3: Evidence Integration (P38, existing)
         Context builder reads enrichment for display
         Provenance tags rendered in evidence panel
```

### 3.5 Supporting Data Types

```python
@dataclass(frozen=True)
class EnrichmentSourceSet:
    """What the enrichment was computed from. Prevents
    'computed from what?' ambiguity."""
    verified_decision_count: int = 0
    unverified_decision_count: int = 0
    decision_ids: list[str] = field(default_factory=list)
    outcome_ids: list[str] = field(default_factory=list)
    fixture_sources: list[str] = field(default_factory=list)
    integration_sources: list[str] = field(default_factory=list)
    computation_version: str = ""

@dataclass(frozen=True)
class EntityEnrichmentReceipt:
    """Returned from every write. Auditable proof of what happened."""
    domain: str
    entity_type: str
    entity_id: str
    namespace: str
    persisted: bool           # False if dry_run
    dry_run: bool
    metrics_written: list[str]
    metrics_rejected: list[str]
    protected_fields_rejected: list[str]
    idempotency_key: str = ""
    computed_at: str = ""
    warnings: list[str] = field(default_factory=list)
```

### 3.6 External Enrichment Sources (Rowboat Pattern)

External enrichment (NLP extraction, document analysis, connector
integration) flows through the same API but with different
provenance:

```python
# CGA internal enrichment (from verified decisions):
write_entity_enrichment(
    metrics={"exception_rate": ProvenancedValue(
        value=0.15, source="verified_outcomes",
        provenance_tier="learned", factor_eligible=True,
        source_count=150, measured=True, verified=True)},
    computed_from=EnrichmentSourceSet(
        verified_decision_count=150, ...)
)

# External enrichment (Rowboat-style extraction):
write_entity_enrichment(
    metrics={"industry_classification": ProvenancedValue(
        value="electronics_manufacturing", source="integration",
        provenance_tier="context", factor_eligible=False,
        source_count=0, measured=False, verified=False,
        provenance_label="extracted from supplier website")},
    computed_from=EnrichmentSourceSet(
        integration_sources=["rowboat_nlp_v2"], ...)
)
```

External enrichment starts as context (fixture-equivalent). It can
become factor-eligible ONLY if validated against verified decisions
(e.g., the NLP-extracted industry classification is confirmed by
decision patterns across 50+ invoices).

---

## §4 — Impact Assessment

### 4.1 Innovation Impact

| Claim | Before enrichment loop | After enrichment loop |
|---|---|---|
| "System gets smarter" | Scorer interpretation improves | Scorer AND inputs improve |
| "Scoring engine" | 6 pathways (all modify scorer state) | **7 pathways** (6 state + 1 input) |
| "Graph-based reasoning" | Graph stores decisions | Graph stores decisions + learned entity knowledge |
| "15,000 decisions survive" | Centroids persist | Centroids + enriched entity profiles persist |

**Entity enrichment completes the scoring engine.** It's the 7th
scoring pathway and the only one that improves the FACTOR SPACE
rather than the scorer STATE. The scoring engine is now:

```
6 STATE pathways + 1 INPUT pathway
= higher effective dimensionality (D_eff) × better-calibrated scorer
```

Note: the interaction between enriched inputs and improved scoring
is not proven to be multiplicative — that would require showing
the gains are independent and non-redundant. The defensible claim
is that enrichment increases D_eff (§2.0), giving the scorer more
discriminative dimensions to learn from.

**Terminology reconciliation with CI blog v15:** The blog lists
"five compounding pathways." This document adds 7 SCORING pathways
(a different category). Recommended alignment for next blog/paper
update: "five compounding pathways built on a 7-pathway scoring
engine." Scoring pathways make decisions better; compounding
pathways create emergent capabilities.

This is distinct from the COMPOUNDING INTELLIGENCE story
(AgentEvolver, SituationAnalysis, ProcessTechFusion, cross-copilot
transfer, RL), which creates emergent capabilities. The enrichment
loop makes decisions better; compounding intelligence makes the
system capable of things it couldn't do before.

### 4.2 Commercial Impact Per Copilot

**S2P (first adopter):**
- "After 150 invoices from Chen-Lin, the system knows their
  exception rate, accuracy pattern, and trend — computed from
  YOUR AP team's verified decisions, not from a database lookup."
- This is demonstrably different from Coupa/Zycus, which use
  static supplier master data.

**SOC (future):**
- "After 500 alerts from source 10.0.0.42, the system knows its
  attack pattern distribution, false positive rate, and behavioral
  trend — compiled from YOUR analysts' verified triage decisions."
- CrowdStrike has threat intelligence. CGA has FIRM-SPECIFIC
  entity intelligence.

**Purchasing (future):**
- "After 200 orders from Sysco, the system knows their delivery
  reliability, price variance, and day-of-week patterns — from
  YOUR kitchen's verified orders."

**DataOps (future):**
- "After 100 quality incidents on pipeline_inventory_api, the
  system knows its failure modes, resolution patterns, and
  cross-system impact — from YOUR data team's verified responses."

### 4.3 Paper Impact

The enrichment loop adds a section to the arxiv paper (v7.6) and
the judgment memory paper (v9). Note: this is a SCORING ENGINE
extension, not a new compounding pathway.

```
§X — Entity Enrichment: The Input Pathway

The CGA scoring engine has 6 pathways that modify the scorer's
internal state (centroids, kernel weights, conservation, referral,
learning rate, distance metric). Entity enrichment adds a 7th
pathway that modifies the scorer's INPUTS: as verified decisions
accumulate for an entity, the system computes entity-level metrics
and feeds them back as factor values.

This is mathematically distinct from state pathways because it
changes the effective dimensionality of the factor space (§X.1)
rather than the scorer's parameters. The existing convergence
results apply to the post-enrichment steady state, with a
transition period governed by the enrichment-graduality strategy
(§X.2) and protected by conservation (§X.3) and a DK estimation
gate (§X.4).
```

### 4.4 Competitive Moat Impact

Entity enrichment deepens the scoring moat (not the compounding
moat — that's AgentEvolver/ProcessTechFusion territory):

```
Without enrichment:
  Scoring moat = centroids + DK weights
  Replicable by: fine-tuning a model on decision history

With enrichment:
  Scoring moat = centroids + DK weights + enriched entity profiles
  NOT replicable by: fine-tuning (model doesn't enrich entities)
  NOT replicable by: knowledge graph alone (graph doesn't learn
    from decisions)
  
  Requires: the same feedback architecture PLUS the customer's
  verified decisions PLUS the entity enrichment loop
```

---

## §5 — Execution Plan (For Codex Session)

### 5.0 Scope Boundary (Bright Line)

The work splits into two halves. Build Half 1 now. Defer Half 2.

| | Half 1: Write + Display (NOW) | Half 2: Factor Feedback (DEFERRED) |
|---|---|---|
| What | Persist enrichment, render with provenance | Feed enriched values into scorer |
| Needs experiments? | No — plumbing + honesty | Yes — recovery, DK gate, conservation |
| Needs pilot data? | No — useful from first decision | Yes — entities must cross N_min |
| Fixes live DD risk? | Yes — kills fixture-as-real | No (different concern) |
| Solves substrate? | Yes — this IS P39A | Consumes the substrate |
| Effort | ~2-3d | ~1-2d + experiments |

The write API is the seam. Build it now, and turning on factor-
feedback later is "flip a consumer on," not "rebuild the substrate."

### 5.1 Implementation Sequence

```
Step 1: P39A design prompt → Codex produces API contract    (~0.5d)
Step 2: Design review (Roadmap or GPT-5.5)                  (~0.5d)
Step 3: P39A implementation                                  (~1d)
Step 4: Code review (GPT-5.5 mandatory)                      (~0.5d)
Step 5: P39B implementation                                  (~1d)
Step 6: P39B review (product integrity + provenance)         (~0.5d)
Step 7: Live API E2E                                         (~0.5d)
```

### 5.2 Step 1 — P39A Design Prompt

```
WORKING DIRECTORY: copilot-sdk
VENV: .venv (activate before running)
TASK: Design the GraphStore Entity Enrichment API (P39A).
TASK TYPE: Design document + data model definitions (no implementation yet).

Read this document (cga_entity_enrichment_loop — current version
in docs/design/) §3.1-§3.6
for the API contract, data models, and architecture layering.

Produce:
1. Protocol method signatures for GraphStore:
   - write_entity_enrichment(domain, entity_type, entity_id,
     namespace, metrics, computed_from, dry_run, idempotency_key)
     → EntityEnrichmentReceipt
   - read_entity_enrichment(domain, entity_type, entity_id, namespace)
     → dict[str, ProvenancedValue]
   - list_entity_enrichments(domain, entity_type, namespace, limit)
     → list[EntityEnrichmentRecord]

2. Data model files:
   - ProvenancedValue (see §3.2 — required fields first, optional
     with defaults. factor_eligible defined but NOT consumed.)
   - EnrichmentSourceSet (see §3.5)
   - EntityEnrichmentReceipt (see §3.5)

3. SQLite table schema:
   entity_enrichments(
     domain TEXT NOT NULL,
     entity_type TEXT NOT NULL,
     entity_id TEXT NOT NULL,
     namespace TEXT NOT NULL,
     metric_name TEXT NOT NULL,
     value_json TEXT NOT NULL,
     provenance_json TEXT NOT NULL,
     source_set_json TEXT NOT NULL,
     computed_at TEXT NOT NULL,
     idempotency_key TEXT,
     PRIMARY KEY (domain, entity_type, entity_id, namespace, metric_name)
   )

4. Memory implementation shape (dict keyed by tuple)

5. AGE semantics (documented, stub/guard if not implemented):
   Preferred: (Entity)-[:HAS_ENRICHMENT]->(EntityEnrichment {...})
   NOT property mutation on base entity nodes.
   Advisory-lock + MATCH-then-CREATE (NOT MERGE).

6. Protected fields list:
   id, entity_id, supplier_id, canonical_id, domain, entity_type,
   source_system, created_at, updated_at, name, supplier_name,
   primary foreign keys, graph labels, edge identity fields.

7. Test plan for P39A (see §5.5 test gates below).

OUTPUT: Design document ready for Step 2 review.
Do NOT implement yet.
```

### 5.3 Step 3 — P39A Implementation Prompt

```
WORKING DIRECTORY: copilot-sdk
VENV: .venv (activate before running)
TASK: Implement the GraphStore Entity Enrichment API (P39A).
TASK TYPE: Protocol extension + SQLite + Memory implementations + tests.

Files to create:
  copilot_sdk/graph/enrichment.py
    - ProvenancedValue, EnrichmentSourceSet, EntityEnrichmentReceipt
    - Protected fields registry (PROTECTED_ENTITY_FIELDS set)
    - ProvenancedValue.to_display() → Provenanced[T] method
      (downcasts for evidence rendering; maps source→source,
       provenance_label→label, value→value)

  copilot_sdk/graph/graph_store.py (modify)
    - Add write_entity_enrichment, read_entity_enrichment,
      list_entity_enrichments to protocol
    - CRITICAL: methods MUST have DEFAULT IMPLEMENTATIONS, not
      abstract. This prevents breaking existing tests across all
      repos. Defaults:
        write → raise NotImplementedError("{cls} does not support enrichment")
        read  → return {}  (empty dict = no enrichment, honest)
        list  → return []
    - Only SQLite/Memory/AGE override these. Existing test mocks
      and fakes inherit the defaults and continue passing.

  copilot_sdk/graph/sqlite_store.py (modify)
    - entity_enrichments table: CREATE TABLE IF NOT EXISTS
      (handles existing databases without migration script)
    - Upsert by primary key (domain, entity_type, entity_id,
      namespace, metric_name)
    - Dry-run returns receipt without write
    - Protected fields rejected before write
    - No raw sqlite3 from feature code — all through this method

  copilot_sdk/graph/memory_store.py (modify)
    - Dict-based implementation matching SQLite behavior
    - Enforce protected fields, dry-run, receipts

  tests/test_entity_enrichment.py
    - Full test gates from §5.5

BLAST RADIUS CHECK (verify before marking done):
  - Run existing tests in copilot-sdk: zero new failures
  - Run existing tests in s2p-copilot: zero new failures
  - Run existing tests in gen-ai-roi-demo: zero new failures
  - If ANY existing test fails because of the protocol change,
    the default implementations are wrong. Fix them.
  - Check from_preset() parsing: if strict (rejects unknown
    fields), add n_min_enrichment to ALL 5 copilot presets now.
    If permissive (ignores unknown), only S2P needs it in P39B.

PROVENANCED TYPE RECONCILIATION:
  Product Integrity v2.4 defines Provenanced[T] (3 fields) in
  copilot_sdk/evidence/provenance.py. This task defines
  ProvenancedValue (10 fields) in copilot_sdk/graph/enrichment.py.
  Relationship: ProvenancedValue is the enrichment-specific
  extension. Add to_display() method that returns Provenanced[T]
  for evidence rendering. Import Provenanced from evidence module.

Write semantics:
  - Upsert by primary key
  - Replace value + provenance atomically
  - Dry-run returns receipt, writes nothing
  - Protected fields → receipt.protected_fields_rejected
  - Fixture values CANNOT claim measured=True or verified=True
  - Idempotent: re-running produces same result
  - No raw sqlite3 from S2P or feature code

Read semantics:
  - Returns dict[str, ProvenancedValue] for entity/namespace
  - Absent enrichment → empty dict (NOT fabricated defaults)
  - List returns all enrichments for domain/entity_type/namespace

NON-NEGOTIABLES:
  - No MERGE in AGE adapter (advisory-lock + MATCH-then-CREATE)
  - No raw sqlite3 from feature code (sqlite3 usage is confined to
    sqlite_store.py — the GraphStore implementation layer — never
    from S2P routers, services, or enrichment consumers)
  - No overwrite of canonical entity identity fields
  - No fixture metric claiming measured/verified provenance
  - No GraphStore protocol bypass
  - No silent write failure with persisted=true
  - Dry-run must write nothing and return honest receipt
  - Protocol methods have defaults (not abstract) — zero existing test breakage

RUN: pytest tests/test_entity_enrichment.py -v
ALSO: pytest tests/ -q (verify zero regressions)
EXIT: All tests pass. Zero new failures across existing tests.
```

### 5.4 Step 5 — P39B Implementation Prompt

```
WORKING DIRECTORY: s2p-copilot
VENV: .venv (activate before running)
TASK: Implement S2P Supplier Enrichment (P39B) — write + display only.
TASK TYPE: Service + router + tests + E2E.

Files to create:
  backend/app/services/s2p_enrichment.py
    - S2PSupplierEnrichmentService
    - Runs as BACKGROUND computation (not hot-path)
    - Reads verified decisions from GraphStore
      (get_verified_decisions or equivalent verified join)
    - Computes: exception_rate, accuracy, verified_count,
      unverified_count, category_distribution, trend (if sufficient data)
    - Fixture fields (OTIF, lead time unless ERP-verified):
      source="fixture", provenance_tier="context",
      measured=False, verified=False
    - Writes through GraphStore.write_entity_enrichment()
    - dry_run=True computes without persisting

  backend/app/routers/enrichment_router.py
    - POST /api/s2p/enrichment/run (compute + persist, or dry_run)
    - GET /api/s2p/enrichment/supplier/{supplier_id}
    - GET /api/s2p/enrichment/summary
    - GET /api/s2p/enrichment/alerts
    Endpoint rules:
    - response includes write_target, persisted, receipt data
    - supplier endpoint: 404 or empty-safe if not enriched
    - alerts: only measured/verified metrics for measured claims
    - fixture alerts labeled integration-pending

  backend/tests/test_s2p_enrichment.py
    - Full test gates from §5.6

  E2E: s2p_enrichment_api.spec.ts
    - dry-run, summary, supplier, alerts, provenance visible

Files to MODIFY:
  backend/app/services/<evidence_builder>.py
    - Stage 1: discover actual file name. P38 may have created
      s2p_graph_traversal.py, s2p_context_builder.py, or
      s2p_situation_pattern.py. Run:
      grep -rl "situation_context\|build.*context" \
        backend/app/services/ --include="*.py"
    - Add OPTIONAL enrichment read:
      enrichment = graph_store.read_entity_enrichment(
        domain="s2p", entity_type="Supplier",
        entity_id=supplier_id, namespace="s2p_supplier_metrics")
    - If enrichment exists: use ProvenancedValue.to_display()
      to render with learned/measured tags
    - If enrichment empty: fall back to fixture values with
      context/integration_pending tags (existing P38 behavior)
    - Existing P38 test suite MUST continue passing
    - This is a SMALL change: read enrichment if available,
      fall back to existing behavior if not

CRITICAL CONSTRAINTS:
  - factor_eligible is DEFINED on each ProvenancedValue but NOT
    consumed by the scorer. Display-only in this scope.
  - GraphStore read ≠ verified outcome. Use get_verified_decisions()
    or equivalent. Do not count unverified rows as verified.
  - P36/P37 compatibility: existing evidence and trust endpoints
    must continue working unchanged.
  - P38 compatibility: context builder behavior unchanged when
    no enrichment has been persisted. Enrichment is ADDITIVE —
    it provides richer values where available, falls back to
    fixture where not.
  - No raw sqlite3 or raw Cypher from this service.

VERIFIED-ONLY DISCIPLINE:
  Metrics claiming learned/measured provenance MUST be computed
  from verified outcomes only. Unverified GraphStore rows are
  excluded from accuracy, exception_rate, and trend calculations.
  GraphStore-read count reported separately from verified count.

RUN:
  pytest tests/test_s2p_enrichment.py -v --timeout=60
  pytest tests/ -q --timeout=120
  Start S2P: python demo.py --s2p --no-browser
  Hit endpoints manually: curl localhost:8002/api/s2p/enrichment/summary
  Run E2E: npx playwright test s2p_enrichment_api.spec.ts

EXIT: All tests pass. Live API E2E passes. Provenance tags visible.
```

### 5.5 P39A Test Gates

P39A is not done until ALL of these pass:

**Protocol / model tests:**
- ProvenancedValue shape and required fields
- EnrichmentSourceSet shape
- EntityEnrichmentReceipt shape
- Protected fields cannot be written (receipt shows rejection)
- Fixture values cannot claim measured=True or verified=True
- Verified metrics require verified=True + source="verified_outcomes"
- factor_eligible field present and defaults to False

**SQLiteGraphStore tests:**
- Write enrichment → read back matches
- Update same metric idempotently (upsert)
- Dry-run writes nothing (verify DB unchanged)
- Protected field rejected (receipt.protected_fields_rejected)
- Provenance round-trips through JSON serialization
- Source-set round-trips through JSON serialization
- Zero/empty enrichment → empty dict returned (not error)
- List enrichments by domain/entity/namespace

**MemoryGraphStore tests:**
- Same behavior as SQLite (protocol conformance)

**AGE adapter:**
- AGE semantics documented
- AGE write path either implemented with tests OR explicitly
  returns NotImplementedError with clear message
- No silent fake success (persisted=True when nothing written)

**Backward compatibility (P39A must not break existing code):**
- Decision writes unaffected by enrichment table
- Outcome writes unaffected
- Verified-decision reads unaffected
- L5 writes unaffected
- P38 context builder unaffected (P39A is SDK-only; S2P modification is P39B)
- P37 evidence unaffected
- ALL existing tests pass with zero new failures (protocol defaults guarantee this)

### 5.6 P39B Test Gates

P39B is not done until ALL of these pass:

- Verified metrics computed from verified outcomes ONLY
- Unverified GraphStore rows EXCLUDED from accuracy/exception_rate
- GraphStore-read count reported SEPARATELY from verified count
- Fixture supplier fields labeled context / integration_pending
- Lead-time provenance honest (fixture vs ERP-verified)
- Exception rate computation correct (verified only)
- Accuracy computation correct (verified only)
- Category distribution correct
- Quarterly distribution handles year boundaries
- Trend handles insufficient data (warning, not fabrication)
- Trend uses verified history only
- Dry-run does not persist
- Persist uses GraphStore.write_entity_enrichment() (not raw SQL)
- Supplier endpoint safe for missing/unknown supplier
- Summary endpoint sorted correctly
- Alerts use only appropriate metric provenance
- Zero-decision supplier → safe response (not error)
- Missing supplier → safe response (not error)
- Idempotency: run twice, same result
- **Context builder: enrichment read integrated (to_display() used)**
- **Context builder: falls back to fixture when no enrichment persisted**
- **Context builder: existing P38 tests still pass**
- **Context builder regression: output with empty enrichment store is
  identical to pre-P39B output (byte-for-byte regression proof)**
- P36/P37 compatibility retained
- API E2E: dry-run, summary, supplier, alerts, provenance visible

### 5.7 What is Explicitly DEFERRED (Pilot-Gated)

Do NOT build now. Record for when pilot data exists:

| Item | Why deferred | Build when |
|---|---|---|
| FactorEnrichmentAdapter | Needs N_min + DK gate + math review | Pilot entities cross N_min |
| Corrected N_recovery bound | Route through math poll | Before arxiv/math_synopsis update |
| DK ≥80% coverage gate | Needs real enrichment coverage data | Factor-feedback implementation |
| Conservation endogenous caveat | Documentation, not code | Math framework update |
| Distribution-shift recovery experiment | Needs held-out benchmark | Factor-feedback implementation |
| Override-rate circularity monitor | Design hook now, wire later | Factor-feedback + real analyst patterns |

**Hooks to build NOW (for later):**
- `factor_eligible` field on ProvenancedValue (defined, not consumed)
- N_min values in copilot presets (configured, not enforced as gates)
- Enrichment coverage tracking (count enriched vs total per factor)

### 5.8 Execution Summary

```
NOW (2.5-3.5d):
  Step 1: P39A design prompt                    → design doc
  Step 2: Design review                          → approved contract
  Step 3: P39A implementation                    → SDK enrichment API
  Step 4: Code review                            → verified implementation
  Step 5: P39B implementation                    → S2P write + display
  Step 6: P39B review                            → product integrity verified
  Step 7: Live API E2E                           → enrichment visible with provenance

DEFERRED TO PILOT:
  Phase 3: math framework update (N_recovery, DK gate, conservation)
  Phase 4: factor integration (FactorEnrichmentAdapter)
  Phase 5: document updates (math_synopsis, innovation_note, arxiv)

DEPENDENCIES:
  P44 (SDK GraphEnricher) depends on P39A — reuses the API
  P40 auto-approve may consume honest DISPLAY metrics but
    must NOT depend on factor-feedback
```

### 5.9 Blast Radius Assessment

| Change | Repos affected | Risk | Control |
|---|---|---|---|
| GraphStore protocol (3 new methods) | All 5 (if abstract) | **ZERO** with defaults | Default implementations — NOT abstract |
| SQLite enrichment table | copilot-sdk | Low | CREATE TABLE IF NOT EXISTS |
| Two ProvenancedValue types | copilot-sdk | Medium | `to_display()` method reconciles |
| P38 context builder modification | s2p-copilot | Low | Optional read + fallback to fixture |
| Preset configuration (N_min) | Depends on parsing | Low-Medium | Check `from_preset()` strict vs permissive |
| AGE adapter | ci-platform | Low | Stub with NotImplementedError |
| SOC/Trading/Purchasing/DataOps | None | **ZERO** | Default implementations |

**The critical control: protocol methods have default implementations.**
This is the difference between "P39A breaks 50 tests across 4 repos"
and "P39A breaks zero tests." Verify by running the full test suite
in copilot-sdk, s2p-copilot, and gen-ai-roi-demo AFTER the protocol
change, BEFORE implementing the enrichment features.

---

### 6.1 Enrichment Provenance (from Product Integrity v2.4)

Every enriched value carries provenance. The provenance rendering
makes the enrichment loop VISIBLE to the buyer:

```
██ exception_rate: 15%
   learned from 150 verified decisions by YOUR AP team

██ accuracy: 87%
   learned from 150 verified decisions

░░ OTIF score: 94%
   supplier context · integration pending

██ trend: rising (last 3 quarters)
   learned from quarterly verified decision distribution
```

The ██ learned lines are the moat. No competitor has them because
no competitor derives entity knowledge from verified decisions.

### 6.2 Factor Eligibility Gate

```python
# Product Integrity test (add to test_innovation_claims.py):

def test_enrichment_below_nmin_is_display_only():
    """Enrichment with < N_min decisions must NOT feed scoring."""
    enrichment = ProvenancedValue(
        value=0.50, source="verified_outcomes",
        source_count=5,  # below N_min=20 for S2P
        factor_eligible=False)
    
    # Factor computation must use default, not enrichment
    factor = compute_supplier_risk(enrichment)
    assert factor == DEFAULT_FIXTURE_VALUE, \
        "Enrichment below N_min fed scoring — unsafe"

def test_enrichment_above_nmin_feeds_scoring():
    """Enrichment with >= N_min decisions feeds scoring."""
    enrichment = ProvenancedValue(
        value=0.15, source="verified_outcomes",
        source_count=150,  # above N_min=20
        factor_eligible=True)
    
    factor = compute_supplier_risk(enrichment)
    assert factor == 0.15, "Enrichment above N_min not used"
```

### 6.3 Distribution Shift Recovery Test

**Depends on:** Phase 4 test infrastructure (functions below are
built as part of `test_enrichment_factor_integration.py`, not the
Phase 3 benchmark fixture).

```python
def test_scoring_recovers_after_enrichment_activation():
    """When enrichment activates (fixture → measured factors),
    accuracy temporarily drops then recovers.
    BOTH scorers measured on the SAME enriched eval set.
    CRITICAL: recovery starts from FIXTURE-TRAINED centroids,
    not fresh initialization — otherwise this measures cold-start,
    not recovery."""
    
    # Phase 1: train on fixture factors
    scorer_fixture = train_scorer(fixture_factors, seed=42)
    fixture_centroids = scorer_fixture.get_all_centroids()  # snapshot
    
    # Phase 2: activate enrichment (shift factor distribution)
    enriched_eval = apply_enrichment(eval_set, enrichments)
    acc_shifted = measure_accuracy(scorer_fixture, enriched_eval)
    # Accuracy drops here (centroids misaligned with enriched factors)
    
    # Verify starting point is fixture-trained, not fresh
    assert np.allclose(scorer_fixture.get_all_centroids(), fixture_centroids), \
        "Centroids were reset — this measures cold-start, not recovery"
    
    # Phase 3: retrain on enriched factors FROM fixture starting point
    enriched_train = apply_enrichment(train_set, enrichments)
    scorer_enriched = continue_training(scorer_fixture, enriched_train, 100)
    acc_recovered = measure_accuracy(scorer_enriched, enriched_eval)
    
    # CORRECT baseline: recovered vs shifted (same eval set)
    assert acc_recovered > acc_shifted, \
        "Enriched factors didn't improve over shifted baseline"
    
    # ALSO: measure actual N_recovery rather than asserting a formula
    n_actual = count_decisions_to_recovery(scorer_fixture, enriched_train,
                                           enriched_eval, threshold=acc_shifted)
```

### 6.4 N_min Per-Metric Caveat

N_min = 20 (S2P) is justified by the SE formula √(p(1-p)/N) which
applies to PROPORTIONS (exception_rate, accuracy). It does NOT
apply to:

- **Trend** ("rising last 3 quarters"): slope estimation needs far
  more data than a proportion. A trend from 20 decisions spanning
  3 quarters is not statistically defensible.
- **Distribution** (category distribution): needs enough decisions
  per category, not just total.

N_min should be per-metric-type in the final implementation:

| Metric type | N_min basis | Suggested N_min (S2P) |
|---|---|---|
| Proportion (exception_rate, accuracy) | SE = √(p(1-p)/N) | 20 |
| Count (verified_decisions, unverified) | Exact, no threshold | 1 |
| Distribution (category_distribution) | Min 5 per category | 5 × num_categories |
| Trend (slope, direction) | Regression SE, needs time span | 50 + ≥3 time periods |

This is a carry-forward for Phase 4 (factor integration). For
Phase 2 (display-only), all metrics are shown with source_count
and the buyer can judge whether the count is sufficient.

### 6.5 FORBIDDEN Additions

| ID | Forbidden claim | Correct alternative |
|---|---|---|
| F-11 | Enrichment with < N_min decisions used as scoring factor | Display-only until factor_eligible=True |
| F-12 | DK re-estimated on mixed enriched/fixture distribution | Gate: >80% enrichment coverage before re-estimation |
| F-13 | External enrichment (Rowboat/connector) labeled as "learned" | `source="integration"`, `provenance_tier="context"` |
| F-14 | "Self-healing enrichment" or "conservation catches all enrichment errors" | Conservation catches accuracy drops from bad factors. It CANNOT catch automation bias (analysts rubber-stamping). Override-rate monitor + independent probes required. |
| F-15 | "Multiplicative" scoring improvement from enrichment (unbacked) | "Enrichment increases effective discriminative dimensionality (D_eff)" |

### 6.6 CANONICAL Additions

| ID | Approved claim | Evidence |
|---|---|---|
| C-11 | "The system learns about YOUR suppliers from YOUR team's decisions" | ProvenancedValue with source="verified_outcomes" |
| C-12 | "Supplier intelligence accumulates — 150 decisions deep" | source_count visible in evidence |
| C-13 | "Better data × better scoring = the 7th scoring pathway" | Two-loop diagram, factor-eligibility gate |
| C-14 | "Conservation proves enrichment is safe" | α·q·V gates automation during distribution shifts |

---

## §7 — What This Changes in Existing Documents

| Document | Change | Priority |
|---|---|---|
| math_synopsis v18 → v19 | Add enrichment as 7th scoring pathway. New items: effective dimensionality characterization, DK 80% coverage gate, N_min threshold, N_recovery bound, conservation endogenous caveat. NO changes to existing formulas. | P1 (before factor integration) |
| innovation_note v6 → v7 | Add enrichment to scoring engine section (7 pathways). Distinguish scoring pathways from compounding pathways. | P2 |
| cga_arxiv_short v7.6 | Add enrichment section: input pathway, transition analysis, conservation safety | P2 |
| Product Integrity v2.4 → v2.5 | Add enrichment tests, F-11..F-14, C-11..C-14 | P2 |
| copilot_analyze_route_architecture v4.2 | No change (enrichment is background, not hot path) | None |
| P39 forward queue | Split: P39A (API) + P39B (S2P implementation) | P1 |
| P44 (SDK enrichment framework) | Depends on P39A; reuses same API | Track |

---

## §8 — Risk Analysis

### What Could Go Wrong

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Enrichment-induced accuracy drop | Medium | Conservation catches → AMBER | Gradual enrichment, not batch |
| DK miscalibration on mixed distribution | Medium | Suboptimal factor weighting | 80% coverage gate |
| Enrichment from too few decisions | High (early) | Noisy factor values | N_min threshold |
| External enrichment overclaimed as learned | Medium | DD failure | Provenance type enforcement |
| **Self-confirming loop (automation bias)** | **Medium** | **q stays GREEN while detaching from ground truth** | **Override-rate monitor + periodic independent probes + verified-only invariant. Conservation CANNOT catch this — if analysts rubber-stamp, "verified" echoes the scorer.** |
| Implementation complexity exceeds estimate | Medium | Schedule slip | Phase 2 is display-only (ships without factor integration) |

### Why the Risk Is Manageable

The math shows the system is stable under gradual enrichment:
- Re-convergence handles distribution shifts
- Conservation catches accuracy degradation
- N_min prevents noisy enrichment
- DK gate prevents premature trust recalibration
- Provenance prevents overclaiming

And Phase 2 ships display-only — the factor integration (Phase 4)
only proceeds after the math review (Phase 3) passes. No factor
feedback without mathematical proof that it's safe.

---

## Document Control

| Version | Date | Change |
|---|---|---|
| v1.0 | June 13, 2026 | Initial architecture. Two-loop model. Math implications. P39A/P39B split. 5-phase execution plan. Rowboat Labs connection. |
| v1.1 | June 13, 2026 | **Scoring vs compounding distinction.** Enrichment reclassified as 7th SCORING pathway (improves factor inputs), not a compounding pathway (compounding = emergent capabilities like AgentEvolver, ProcessTechFusion). §2 math deepened: effective dimensionality, N_recovery bound, bimodal variance, SE table. |
| v1.1.1 | June 13, 2026 | Comprehensive review: 13 issues fixed. DK zero-variance behavior. CI precision. ProvenancedValue relationship. Background job layer. Supporting types. Stale references. |
| v1.1.2 | June 13, 2026 | **Consolidated review applied.** (1) N_recovery bound CORRECTED: log₂(δ/τ)×N_half per centroid (logarithmic, not quadratic). k' was wrong (parallel recovery, not sequential). Gradual-vs-batch argument now rests on conservation-dip and DK-variance, not recovery time. (2) Self-confirming loop PROMOTED from Low to first-class risk. Conservation cannot catch automation bias — override-rate monitor + independent probes required. (3) "Multiplicative" SOFTENED to D_eff (effective-dimensionality) statement per FORBIDDEN standard. (4) Recovery test FIXED: compare acc_recovered > acc_shifted (same eval set), measure actual N_recovery. (5) N_min PER-METRIC: proportions=20, trends=50+3 periods, counts=1, distributions=5×categories. (6) SCOPE BOUNDARY added: write+display NOW, factor-feedback DEFERRED to pilot with explicit rationale. (7) P39A LEVERAGE noted: canonical AGE idempotent-write pattern shared by counters + migration. (8) Phase 4 DEFERRED with hooks (factor_eligible defined, not consumed). (9) F-15 added: "multiplicative" is forbidden unbacked claim. |
| v1.2 | June 13, 2026 | **Made executable for Codex session.** §5 rewritten as 7-step implementation sequence with 3 paste-ready Codex prompts (P39A design, P39A implementation, P39B implementation). Each prompt includes WORKING DIRECTORY, VENV, file paths, non-negotiables, write/read semantics, and exit criteria. §5.5/§5.6: complete P39A + P39B test gates from the P39 roadmap note. §5.7: deferred items table with "build when" triggers. SQLite table schema, protected fields list, AGE semantics, and verified-only discipline embedded in prompts. P40 auto-approve dependency constraint added. Port 8002 for S2P. |
| v1.3 | June 14, 2026 | **Blast radius review + final fixes for handoff.** (1) §5.3: Protocol methods MUST have default implementations (not abstract) — zero existing test breakage. (2) §5.3: SQLite uses CREATE TABLE IF NOT EXISTS. (3) §5.3: ProvenancedValue.to_display() → Provenanced[T] for evidence rendering. §3.2: method implementation shown. (4) §5.3: from_preset() strict/permissive check added. (5) §5.4: P39B MODIFIES P38 context builder (optional enrichment read + fallback). File discovery step included. (6) §5.5: backward compat clarified — P38 unaffected by P39A (SDK only), modified by P39B. (7) §5.6: 3 new context-builder test gates added. (8) §5.9: blast radius assessment table with controls. (9) §5.3: BLAST RADIUS CHECK block — run existing tests across repos before proceeding. |
| v1.4 | June 14, 2026 | **A+ review — 12 items applied.** (1) §2.1: N_recovery units specified (δ=absolute centroid shift, τ=0.01), 4 worked examples. (2) §2.3: DK coverage = "in current DK estimation window" not all-time. (3) §3.1: namespace multi-producer pattern documented. (4) §3.2: ProvenancedValue factory methods — from_verified(), from_fixture(), unavailable() — make legal states easy, illegal states hard. (5) §5.3: sqlite3 clarification — infrastructure (sqlite_store.py) vs feature code (services/routers). (6) §5.6: context builder regression test added — output with empty enrichment store must be byte-for-byte identical. (7) §6.3: recovery test verifies starting centroids are fixture-trained, not fresh init. (8) §2.5: conservation row — "No formula change" + "New documentation: endogenous caveat + two-stage recovery." (9) §2.1: enrichment degradation case documented (measured = fixture value → neutral, DK handles correctly). (10) §4.1: CI blog terminology reconciliation note. (11) §1.4: Rowboat promotion path defined (integration → learned requires N_min decisions + outcome correlation). (12) §3.2: import path separation verified (evidence.provenance vs graph.enrichment, never re-exported). |
