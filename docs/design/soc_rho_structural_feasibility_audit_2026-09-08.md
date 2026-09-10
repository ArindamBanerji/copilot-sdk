# SOC ρ Structural Feasibility Audit

Date: 2026-09-08

**ρ cannot be measured defensibly from the available offline data.** The repository supports a synthetic decision inventory and an offline scoring diagnostic. It does **not** supply observed investigation trajectories, independently labelled correct branches, or an implemented scorer-to-investigation-branch policy.

Two distinctions are decisive:

- **R1 measures routing from v₁, after the first evidence read.** A v₀-only experiment measures initial routing, a different quantity.
- **SOC’s scorer chooses an action within an externally supplied category.** It does not currently infer a category and dispatch an auth-trail or process-tree investigation.

Evidence: `copilot-sdk/docs/design/vld_graph_reasoning_architecture_v3.md:350–363`; `gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py:580–582`.

The underlying investigation used read-only inspection and offline Python probes. No AGE connection, code changes, git operations, or files were created during that investigation. This report was subsequently saved at the user's request.

For compact citations below, paths are relative to the supplied repository root:

`C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\kaggle_experiments\claude_projects\`

- `SOC` = `gen-ai-roi-demo-v4-v50/backend`
- `SDK` = `copilot-sdk`
- `CI` = `ci-platform`
- `GAE` = `graph-attention-engine-v50`
- `SEED` = `SOC/support/setup/zero_day_decisions_v5.json`

## PART A: Inventory

### What exists

| Inventory measure | Result | Evidence |
|---|---:|---|
| Real verified decisions with confirmed linked Outcome nodes | **Unknown offline** | `CI/ci_platform/graph/age_graph_store.py:2633` |
| Synthetic outcome-labelled decisions in the campaign-bearing seed | **4,862** | `SEED:2`, decision array at `SEED:11722` |
| Synthetic decision IDs across the current and older seed versions, deduplicating interim snapshots | **9,722** | `SEED:8`; `SOC/support/setup/zero_day_decisions.json:6` |
| Current-seed decisions linked to a campaign through their alert | **432 / 4,862 = 8.89%** | Join `SEED:11725` to campaign member lists at `SEED:525`, `583`, `641`, `699` |
| Distinct campaign-member alerts | **48** across **4 campaigns** | Campaign definitions at `SEED:503`, `561`, `619`, `677` |
| Candidates accepted by the existing SOC SA pattern’s `supports()` | **432 / 432** | `SOC/app/services/soc_situation_pattern.py:179` |
| Candidates with an ordered first-read record and a correct-investigation-branch label | **0 found** | Seed record schema at `SEED:11724`; generator at `SOC/app/seed/decisions.py:47` |
| Evaluable score-keyed conditional cases | **0 established** | Same missing trajectory fields; existing dispatch at `SDK/copilot_sdk/situation/analyzer.py:131` |
| Enough data for a meaningful empirical ρ estimate? | **NO** | Missing intermediate observations, branch labels, and routing policy |

These counts distinguish **seed rows that can be materialized as verified graph decisions** from evidence that they currently exist in AGE. The seed loader writes a Decision, an Outcome, and a `DECIDED_ON` edge for each row. It does not establish that those writes have succeeded in the inaccessible graph. Also, `get_verified_decisions()` uses an **optional** Outcome match, so that method alone does not enforce the strict “linked Outcome exists” criterion.

Sources: `SOC/app/graph_schema.py:834`, `855`, `864`; `CI/ci_platform/graph/age_graph_store.py:2641`.

The older 4,860-row seed and its interim snapshots are another synthetic generation, not additional observed investigations. They should not be combined with the campaign-bearing seed by matching alert IDs across versions. Their metadata explicitly identifies a centroid-derived oracle and stochastic action generation.

Source: `SOC/support/setup/zero_day_decisions.json:9`, `36`.

### Campaign-bearing candidates

| Campaign | Distinct alerts | Decision rows | Labelled correct | Labelled incorrect |
|---|---:|---:|---:|---:|
| CAMP-001 | 12 | 108 | 86 | 22 |
| CAMP-002 | 12 | 108 | 82 | 26 |
| CAMP-003 | 12 | 108 | 76 | 32 |
| CAMP-004 | 12 | 108 | 88 | 20 |
| **Total** | **48** | **432** | **332** | **100** |

These are computed joins over the campaign lists and decision array cited above. They are **not 432 independent investigation episodes**: each member alert has nine synthetic decision rows.

Examples:

| Decision | Alert type / category | Campaign | Recorded action and label | Evidence reads |
|---|---|---|---|---|
| DEC-JDOE-001 | credential_stuffing / credential_access | CAMP-001 | escalate; correct | One supported bulk-context pattern; actual read sequence unknown |
| DEC-JDOE-002 | privilege_escalation / lateral_movement | CAMP-001 | monitor; correct | Same |
| SYN-DEC-c8b7fb97 | anomalous_login / credential_access | CAMP-001 | suppress; correct | Same |

Sources: `SEED:525`, `737`, `11724`, `11747`, `11770`. The skeleton in Part D emits the requested inventory for **all 432 candidates**.

**“One supported pattern” is not “one observed evidence read,” nor is it one productive branch.** The adapter calls `get_security_context(alert_id)` in bulk. Its reported `nodes_consulted = 47` is a query literal, not a measured count of distinct nodes or reads.

Sources: `SOC/app/services/soc_situation_pattern.py:206`; `CI/ci_platform/graph/age_client.py:595`.

### Why the correctness labels are insufficient

The current generator:

1. Chooses an action.
2. Assigns `correct` using a target accuracy schedule.
3. Generates the factor vector by adding noise around that action’s configured centroid.

It does not simulate an analyst reading evidence and selecting an investigation branch.

Sources: `SOC/app/seed/decisions.py:36`, `39`, `52`, `99`.

Furthermore, the loader writes `actual_action=d["action"]` even when `correct=False`. Therefore, the 100 incorrect campaign-linked rows do **not** identify the alternative correct action, much less the correct investigation branch.

Source: `SOC/app/graph_schema.py:855`.

Other inspected artifacts do not fill that gap:

| Artifact | What it supplies | Why it is insufficient |
|---|---|---|
| `app/data/soc_eval_scenarios.json` | 36 factor/action scenarios | Expected terminal actions; no investigation histories |
| `app/data/gae_learning_state.json` | Legacy W-matrix update history | No joinable decision/alert/campaign identifiers or ordered reads |
| `tests/test_soc_situation_pattern.py` | A fake alert/user/asset/campaign context | Tests context mapping; not verified branch correctness |
| `backend/data/*.sqlite3` | Authority/promotion and process-variant storage | No decision/outcome corpus in the inspected immutable database snapshots |

Sources: `SOC/app/data/soc_eval_scenarios.json:3`; `SOC/app/data/gae_learning_state.json:48`; `SOC/tests/test_soc_situation_pattern.py:58`, `95`; `SOC/app/services/authority_ladder.py:128`, `143`; `SDK/copilot_sdk/evolution/variant_store.py:216`.

## PART B: Architecture trace

### 1. Factor extraction

The actual call is:

```python
vector, provenance = await get_factor_vector_provider().compute(
    alert_data,
    graph_client,
)
```

The provider invokes `compute_factor_vector_with_provenance()`, which calls each factor computer and assembles the ordered vector.

Sources: `SOC/app/services/triage_providers.py:27`, `41`; `SOC/app/domains/soc/orchestrator.py:37`, `47`, `64`.

The six coordinates are:

| Coordinate | Main inputs | Source |
|---|---|---|
| Privileged identity context | User risk, title, MFA, device fingerprint | `SOC/app/domains/soc/factors.py:130` |
| Asset criticality | Alert → Asset → DataClass query | Same file, `:266` |
| Threat-intel enrichment | Indicators and campaign membership | Same file, `:327`, `357` |
| Pattern history | Prior evolution/decision factor snapshots | Same file, `:512`, `559` |
| Time anomaly | Weekend/business-hours fields | Same file, `:606` |
| Device trust | MFA, fingerprint, VPN fields | Same file, `:647` |

Order: `SOC/app/domains/soc/config.py:120`, `743`.

**This is not an existing surface-only extractor.** Several coordinates consult graph evidence. Production triage also retrieves the bulk security context before factor extraction and scoring. A replay must explicitly define which fields and graph responses are visible at S₀, S₁, and S_L.

Source: `SOC/app/routers/triage.py:510`, `557`.

### 2. Scoring

The production sequence is:

```text
alert_type
  → explicit category lookup
  → six-factor vector
  → score against that category’s four action centroids
  → escalate / investigate / suppress / monitor
  → confidence-based referral and automation handling
```

Sources: `SOC/app/routers/triage.py:519`, `580`, `582`, `596`, `603`.

The centroid tensor is **6 categories × 4 actions × 6 factors**. The fifth routing action, `refer_to_analyst`, has no centroid.

Source: `SOC/app/domains/soc/config.py:153`, `705`.

Within the supplied category:

```text
p(a | v, c) = softmax(-d(v, μ[c, a]) / τ)
a* = argmax_a p(a | v, c)
```

The implementation supports phase-dependent diagonal weighting as well as its base distance kernel. Historical μ alone is consequently insufficient for exact historical scoring.

Source: `GAE/gae/profile_scorer.py:455`, `480`, `487`, `496`.

### 3. SA dispatch

The generic `SituationAnalyzer` selects the **first registered pattern whose `supports(intent)` returns true**. It does not inspect a factor vector, scorer probabilities, or a centroid-selected action.

Source: `SDK/copilot_sdk/situation/analyzer.py:123`.

The SOC adapter provides one pattern:

```text
soc_alert_context
  supports: domain == "soc" and an alert identifier is present
  traversal: get_security_context(alert_id)
```

Source: `SOC/app/services/soc_situation_pattern.py:169`, `179`, `206`.

I found its explicit registration in the SOC mapping tests, not a production triage registration. Production triage calls the separate legacy `analyze_situation(alert_type, context)` function. That function classifies the situation and ranks response options; it does not dispatch a scorer-selected evidence branch.

Sources: `SOC/tests/test_soc_situation_pattern.py:95`; `SOC/app/routers/triage.py:520`; `SOC/app/services/situation.py:193`.

### 4. Campaign branching

The requested `domains/soc/campaigns/` directory is actually a **`campaigns.py` module** in this checkout.

Its correlation engine applies deterministic rules in this order:

1. Technique sequence.
2. Shared entity.
3. Temporal grouping.

Each alert is assigned to at most one winning campaign. `CONTINUES` links adjacent campaign buckets. These supply potentially useful topology, but they are **not alternatives selected by the scorer’s intermediate state**.

Sources: `SOC/app/domains/soc/campaigns.py:694`, `709`, `722`, `1148`.

**The missing operator is explicit:** there is no implemented mapping from `a*(v₁)` or the scorer’s intermediate geometry to an auth-trail/process-tree investigation choice. The architecture memo describes such a controller as R3 work.

Source: `SDK/docs/design/vld_graph_reasoning_architecture_v3.md:389`.

### Offline reconstruction result

I ran the real provider over all 48 campaign-member alert fixtures with an explicitly empty evidence adapter. All produced:

```text
v_empty = [0.5, 0.5, 0.0, 0.4, 0.7, 1.0]
```

That collapse follows the current factor defaults cited above. It is an **empty-evidence diagnostic**, not reconstructed historical v₀.

Using the configured reference centroids:

| Category | Candidate rows | Action from `v_empty` |
|---|---:|---|
| credential_access | 144 | suppress |
| malware_execution | 54 | suppress |
| lateral_movement | 99 | suppress |
| data_exfiltration | 90 | monitor |
| insider_threat | 27 | suppress |
| cloud_infrastructure | 18 | monitor |

The scorer used here is the configuration’s documented **test/reference** builder, not a recovered live trained model.

Source: `SOC/app/domains/soc/config.py:705`, `720`.

## PART C: Content-keyed versus score-keyed audit

The implemented **category routing** is content-keyed for every campaign-linked candidate:

| Category | Observed alert types in the 432 candidates | Category-routing mechanism |
|---|---|---|
| credential_access | credential_stuffing, anomalous_login, ambiguous_login_location, brute_force, credential_access | Literal map |
| malware_execution | malware_execution, c2_beacon, threat_intel_match, phishing | Literal map |
| lateral_movement | privilege_escalation, lateral_movement, internal_scan_ambiguous | Literal map |
| data_exfiltration | data_exfil, data_exfiltration | Literal map |
| insider_threat | insider_threat, anomalous_behavior | Literal map |
| cloud_infrastructure | cloud_config, cloud_config_drift | Literal map |

Evidence for the mappings: `SOC/app/domains/soc/config.py:266–302`; implementation: `:308`. Observed types and counts come from the seed alert/decision join.

The literal map agrees with the stored category for **432/432 rows**.

However:

- **100% content-keyed category assignment does not establish 100% content-keyed investigation branching.**
- Names such as `ambiguous_login_location` do not establish a score-keyed case.
- A campaign’s multiple members do not establish multiple candidate branches with different investigative value.
- Matching an existing category assignment is not evidence that the correct branch was selected.

The memo’s distinction concerns whether the **evidence identifies the productive next branch**, not whether an alert already has a category label.

Source: `SDK/docs/design/vld_graph_reasoning_architecture_v3.md:180`.

Therefore, the defensible fraction summary is:

| Quantity | Result |
|---|---|
| Content-keyed category assignments among campaign candidates | **100%** |
| Content-keyed conditional investigation fraction | **Unknown** |
| Score-keyed conditional investigation fraction | **Unknown** |
| Cases with sufficient evidence to measure score-keyed routing | **0** |

**The “>80% content-keyed investigation” warning cannot be established from these fixtures.** Neither a large nor a small VLD addressable fraction is demonstrated.

## PART D: ρ computation specification

### Exact available calls

| Purpose | Call | Source |
|---|---|---|
| Resolve category | `resolve_alert_category(alert_type)` | `SOC/app/domains/soc/config.py:308` |
| Extract factors | `await get_factor_vector_provider().compute(alert, evidence_adapter)` | `SOC/app/services/triage_providers.py:27`, `41` |
| Construct offline reference scorer | `SOCDomainConfig().build_profile_scorer()` | `SOC/app/domains/soc/config.py:705` |
| Score an array | `profile.score(vector, category_index=cfg.get_category_index(category))` | `GAE/gae/profile_scorer.py:408`; `SOC/app/domains/soc/config.py:679` |
| Score an initialized SDK scorer without persisting a Decision | `scorer.score_read_only(factors, category)` | `SDK/copilot_sdk/scoring/scorer.py:475` |
| Alternate-centroid scoring | `scorer.score_with_centroids(mu, factors, category)` | Same file, `:500` |
| Historical-model API | `scorer.score_with_model_state(mu, factors, category, dk_weights=..., temperature=...)` | Same file, `:519` |
| Test SOC pattern eligibility | `SocAlertTraversalPattern().supports(intent)` | `SOC/app/services/soc_situation_pattern.py:179` |
| Read one bulk SOC context through an offline adapter | `await pattern.traverse_async(intent, graph_store=adapter)` | Same file, `:206` |

The alternate-centroid API explicitly describes itself as **an ablation, not point-in-time replay**. Full replay must also reproduce feature semantics, factor masks, distance kernel, weighting phase, temperature, and evidence visibility.

Sources: `SDK/copilot_sdk/scoring/scorer.py:506`; `GAE/gae/profile_scorer.py:455`.

### Runnable offline inventory/scoring skeleton

Run from the supplied repository root in a fresh Python process with bytecode writing disabled. This prints all candidate rows to stdout. It deliberately reports ρ as unavailable.

```python
import sys
sys.dont_write_bytecode = True

import asyncio
import json
from pathlib import Path

import numpy as np

ROOT = Path.cwd()
for folder in (
    "gen-ai-roi-demo-v4-v50/backend",
    "copilot-sdk",
    "graph-attention-engine-v50",
):
    sys.path.insert(0, str(ROOT / folder))

from app.domains.soc.config import SOCDomainConfig, resolve_alert_category
from app.services.triage_providers import get_factor_vector_provider
from app.services.soc_situation_pattern import SocAlertTraversalPattern
from copilot_sdk.situation import TypedIntent


class EmptyEvidence:
    """Explicit ablation: no graph evidence is visible."""
    async def run_query(self, *args, **kwargs):
        return []


async def main():
    seed_path = ROOT / (
        "gen-ai-roi-demo-v4-v50/backend/support/setup/"
        "zero_day_decisions_v5.json"
    )
    data = json.loads(seed_path.read_text(encoding="utf-8"))
    alerts = {a["alert_id"]: a for a in data["alerts"]}

    membership = {}
    for campaign in data["campaigns"]:
        for alert_id in campaign["member_alert_ids"]:
            membership.setdefault(alert_id, []).append(campaign["campaign_id"])

    cfg = SOCDomainConfig()
    profile = cfg.build_profile_scorer()  # Configured reference, NOT live μ.
    provider = get_factor_vector_provider()
    pattern = SocAlertTraversalPattern()
    cache = {}
    rows = []

    for decision in data["decisions"]:
        aid = decision["alert_id"]
        if aid not in membership:
            continue

        alert = alerts[aid]
        category = resolve_alert_category(alert["alert_type"])

        if aid not in cache:
            # Explicit replay normalization for factor computers expecting "id".
            vector, provenance = await provider.compute(
                dict(alert, id=aid), EmptyEvidence()
            )
            prediction = profile.score(
                vector,
                category_index=cfg.get_category_index(category),
            )
            cache[aid] = vector, provenance, prediction

        vector, provenance, prediction = cache[aid]
        intent = TypedIntent(
            domain="soc",
            intent_type="alert_context",
            verb="explain",
            subject="alert",
            scope={"alert_id": aid},
            source_event_id=aid,
            decision_id=decision["decision_id"],
            trace_id="offline-rho-inventory",
        )

        rows.append({
            "decision_id": decision["decision_id"],
            "alert_id": aid,
            "alert_type": alert["alert_type"],
            "category": category,
            "campaign_ids": membership[aid],
            "recorded_action": decision["action"],
            "synthetic_correctness": decision["correct"],
            "labelled_correct_action": (
                decision["action"] if decision["correct"] is True else None
            ),
            "supported_bulk_patterns": int(pattern.supports(intent)),
            "observed_evidence_reads": None,
            "correct_investigation_branch": None,
            "v_empty_evidence": vector.tolist(),
            "action_reference_mu": prediction.action_name,
            "factor_provenance": provenance,
            "stored_vector_gap": float(np.linalg.norm(
                np.asarray(decision["factor_vector"]) - vector
            )),
            "rho_case": None,
        })

    print(json.dumps({
        "model": "configured reference centroids",
        "surface_policy": "empty-evidence/defaulted ablation",
        "total_seed_decisions": len(data["decisions"]),
        "candidate_decisions": len(rows),
        "candidate_fraction": len(rows) / len(data["decisions"]),
        "evaluable_rho_cases": 0,
        "rho": None,
        "rows": rows,
    }, indent=2))


asyncio.run(main())
```

I exercised the imports, provider, reference scorer, pattern eligibility, and full 432-candidate loop offline.

### What must be supplied for actual ρ

A usable episode needs:

| Required field | Why |
|---|---|
| Decision/alert/campaign identifiers and timestamps | Join records and prevent cross-version or future-data leakage |
| Initial observation snapshot S₀ | Reconstruct actual surface features |
| First read: request, returned evidence, timestamp | Reconstruct S₁, rather than the final graph |
| Available next branches at S₁ | Define the choice set |
| Independently adjudicated productive branch or acceptable branch set | Supply routing ground truth |
| Actual analyst read sequence, if available | Describe behaviour; it is not automatically ground truth |
| Versioned scorer-to-branch policy | Turn intermediate scoring into an actual branch prediction |
| Frozen model state and feature schema | Reproduce scoring |
| Training/evaluation partition and campaign grouping | Avoid leakage and account for dependence |

The memo itself calls for selected/candidate edges and trajectory storage; terminal outcomes alone are insufficient.

Sources: `SDK/docs/design/vld_graph_reasoning_architecture_v3.md:97`, `134`, `483`.

The intended measurement is:

```python
v0 = extract(S0)
first_read = fixed_first_read_policy(S0)
v1 = extract(S0 + first_read.result)

score1 = frozen_scorer(v1, category)
predicted_branch = frozen_branch_policy(score1, available_branches)

rho_case = int(predicted_branch in adjudicated_correct_branches)
```

`frozen_branch_policy` is a **required new policy definition**, not an existing SOC function.

For the follow-up evaluator, this executable core avoids assuming that terminal actions are branch labels:

```python
from statistics import mean

def evaluate_routing(cases, score, route, content_rule, majority_by_category):
    """
    cases: held-out, independently annotated score-keyed episodes.
    score(v1, category): read-only scoring with a frozen model.
    route(result, case): frozen policy returning an available branch ID.
    """
    rows = []

    for case in cases:
        assert case["branching_kind"] == "score_keyed"
        available = set(case["available_branches"])
        correct = set(case["correct_branches"])
        assert available and correct and correct <= available

        result = score(case["v1"], case["category"])
        choices = {
            "vld": route(result, case),
            "content_rule": content_rule(case),
            "majority": majority_by_category[case["category"]],
        }

        # Report invalid predictions; do not silently repair them with labels.
        row = {
            "decision_id": case["decision_id"],
            "campaign_id": case["campaign_id"],
            "random_expected_accuracy": len(correct) / len(available),
        }
        for policy, branch in choices.items():
            row[f"{policy}_valid"] = branch in available
            row[f"{policy}_correct"] = int(branch in correct)
        rows.append(row)

    if not rows:
        return {"n": 0, "rho": None, "rows": []}

    return {
        "n": len(rows),
        "rho": mean(r["vld_correct"] for r in rows),
        "majority_accuracy": mean(r["majority_correct"] for r in rows),
        "content_rule_accuracy": mean(r["content_rule_correct"] for r in rows),
        "random_expected_accuracy": mean(
            r["random_expected_accuracy"] for r in rows
        ),
        "rows": rows,
    }
```

The missing annotations and branch policy must be supplied before that evaluator can produce a meaningful result.

### Preseed adequacy

The current `preseed_all_copilots.py` does **not** provide the proposed 80 SOC decisions:

- The configured count is **200**.
- Its SDK targets are Trading, Purchasing, and DataOps.
- S2P has a separate path.
- There is no SOC target.

Sources: `SDK/scripts/preseed_all_copilots.py:27`, `145`, `155`, `165`, `365`.

Even an 80-row SOC action/outcome seed would not solve the missing investigation-label problem.

### Temporal reconstruction

**Decision-time μ is not recoverable for this seed from the local backups.**

The 4,862 seed timestamps span **March 4–June 1, 2025**. The 1,586 local centroid-backup files span **April 24–August 24, 2026**. None predates the last seed decision.

Sources: `SEED:11739`, `123542`; `SOC/app/data/centroid_backups/centroid_backup_1777069884690_fdc0eeb0.json:1`; `SOC/app/data/centroid_backups/centroid_backup_1787612422787_b91a72be.json:1`.

Those files contain μ, shape, timestamps, step and metadata, rather than complete evidence and scoring-state snapshots. The `latest` alias also contains test-associated metadata; it is not proof of the current production model.

Source: `SOC/app/data/centroid_backups/centroid_backup_latest.json:1`.

Live checkpoint access exists, but using it would require an authorized graph/runtime export and still would not create historical evidence-read logs.

Source: `SOC/app/services/gae_state.py:654`, `664`.

### Sample size

**Usable sample size now: zero.**

Even after annotation, 432 rows cannot be treated as 432 independent investigations: they represent 48 alerts in four campaigns.

For orientation, under independent Bernoulli sampling, worst-case approximate 95% half-widths are:

- 80 cases: ±11 percentage points.
- 432 cases: ±4.7 points.
- 48 cases: ±14.1 points.

These are precision calculations, **not power estimates**. Power to beat the comparator requires an expected paired improvement and disagreement rate. Evaluation should split by campaign/time and report paired uncertainty; four campaign clusters are inadequate for a strong generalization claim.

## PART E: Comparator baselines

No defensible routing accuracy can currently be computed for any policy, because correct-branch labels and branch sets are absent.

| Policy | Required computation | Current result |
|---|---|---|
| VLD | Score v₁, apply frozen branch policy, compare with adjudicated branch | **Unavailable** |
| Majority branch | Fit most common correct branch per category on training cases; evaluate on held-out campaigns | **Unavailable** |
| Content-keyed rule | Apply a frozen alert/evidence routing rule using the same visible evidence and budget | **Unavailable** |
| Uniform random | Average 1/Kᵢ, or the number of acceptable branches divided by Kᵢ | **Unavailable** |

The literal alert-type category rule achieves **100% agreement with stored categories** on the 432 candidates. That is a useful consistency check, **not a routing baseline accuracy**.

Source: `SOC/app/domains/soc/config.py:266`, `308`; seed joins cited in Part A.

Existing SOC rules worth including as comparators are:

- Literal alert-type category resolution.
- Legacy situation classification using context such as travel/MFA and campaign signatures.
- Deterministic campaign correlation rules.

Sources: `SOC/app/domains/soc/config.py:308`; `SOC/app/domains/soc/situations.py:238`, `266`; `SOC/app/domains/soc/campaigns.py:694`.

For fairness, the rule comparator must receive the **same first-read evidence** as VLD. Comparing an evidence-informed VLD controller only against an alert-type-only rule would not establish superiority over existing context-informed routing.

## PART F: Verdict

| Question | Answer |
|---|---|
| Can the structural audit and offline inventory be completed? | **YES** |
| Can empirical ρ be measured from the available artifacts? | **NO** |
| Are score-keyed conditional cases established? | **NO; none is sufficiently documented to evaluate** |
| Is the investigation content-keyed fraction above 80%? | **Unknown** |
| Is historical v₀ reconstructable? | **Not from these fixtures; only a declared ablation is available** |
| Is historical v₁ reconstructable? | **No ordered first-read evidence is available** |
| Is decision-time μ available for this seed? | **No matching historical backup** |
| Are surface-trained centroids available? | **None identified** |

### μ skew

The bootstrap artifact named `mu_zero` is an initialization tensor, not evidence of centroids trained on surface-only observations.

Source: `SOC/app/data/iks_bootstrap_soc.json:2`; configured priors: `SOC/app/domains/soc/config.py:153`.

I computed the diagnostic distance between each of the 432 stored synthetic vectors and the empty-evidence vector:

| Statistic | Distance |
|---|---:|
| Minimum | 0.509 |
| 25th percentile | 0.656 |
| Median | 0.741 |
| 75th percentile | 1.152 |
| Maximum | 1.372 |
| Mean | 0.858 |

**These are not measurements of ‖v_L − v₀‖.** The stored vectors were generated around action centroids; the comparison vectors come from missing-evidence defaults. Their difference measures neither observed investigative movement nor the direction or magnitude of routing-accuracy bias.

Sources: `SOC/app/seed/decisions.py:99`; factor defaults cited in Part B.

### Recommended follow-up Codex prompt

> Perform a read-only SOC R1 replay using an exported, versioned investigation dataset. First require linked outcomes, initial observations, ordered first-read evidence, available branch sets, independently adjudicated correct branches, and complete frozen scoring state. Require an explicit scorer-to-branch policy; do not infer investigation branches from terminal action labels or category agreement.
>
> If any required input is absent, report ρ as unavailable. Otherwise reconstruct v₀ and v₁, evaluate routing from v₁, and compare against training-only majority routing and existing content-informed rules on held-out campaigns. Report paired accuracy differences, invalid/abstaining predictions, coverage, and campaign-level uncertainty. Evaluate surface-trained versus fully-investigated-trained μ only when both models and their training provenance exist.

**The next step is data acquisition and branch-policy specification, not a numerical ρ run.** A live AGE export may supply linked decisions and model checkpoints; it is not sufficient by itself unless the missing investigation histories and branch ground truth were recorded.
