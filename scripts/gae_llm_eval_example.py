"""
GAE for LLM Evals — running example.

Same eval rubric. One system scores and archives.
GAE scores, learns, and tells you which criteria actually matter.

Run with:
    pip install graph-attention-engine
    python gae_llm_eval_example.py
"""

import numpy as np
from gae import (
    ProfileScorer,
    EvaluationScenario,
    run_evaluation,
    run_ablation,
    compute_judgment,
    check_conservation,
    compute_theta_min,
)

# ── Domain: LLM eval rubric ─────────────────────────────────────────
#
# Categories = task types your LLM handles
# Actions    = quality verdicts (what the eval decides)
# Factors    = rubric criteria (what the LLM-as-judge scores)
#
# The question GAE answers: which criteria actually predict
# whether users are satisfied — not which criteria score high.

CATEGORIES = ["summarization", "qa", "code_review"]
ACTIONS    = ["poor", "fair", "good", "excellent"]
FACTORS    = ["correctness", "grounding", "conciseness",
              "fluency", "relevance"]

N_CAT, N_ACT, N_FAC = len(CATEGORIES), len(ACTIONS), len(FACTORS)
cat_idx = {c: i for i, c in enumerate(CATEGORIES)}
act_idx = {a: i for i, a in enumerate(ACTIONS)}

print(f"Domain: LLM evals")
print(f"  Task types:  {CATEGORIES}")
print(f"  Verdicts:    {ACTIONS}")
print(f"  Criteria:    {FACTORS}")
print(f"  Tensor:      ({N_CAT}, {N_ACT}, {N_FAC}) = "
      f"{N_CAT * N_ACT * N_FAC} centroid values\n")

# ── Step 1: Initial centroids (uniform prior) ───────────────────────
#
# Start with a mild prior: we think all criteria matter equally.
# GAE will learn the real weights from verified outcomes.

mu = np.full((N_CAT, N_ACT, N_FAC), 0.5, dtype=np.float64)

# Seed obvious anchors — high scores → excellent, low → poor
for c in range(N_CAT):
    mu[c, act_idx["excellent"], :] = [0.9, 0.9, 0.7, 0.8, 0.9]
    mu[c, act_idx["good"],      :] = [0.7, 0.7, 0.6, 0.7, 0.7]
    mu[c, act_idx["fair"],      :] = [0.4, 0.4, 0.5, 0.5, 0.4]
    mu[c, act_idx["poor"],      :] = [0.2, 0.1, 0.3, 0.3, 0.1]

scorer = ProfileScorer(mu=mu, actions=ACTIONS)
print(f"ProfileScorer built: shape {mu.shape}")

# ── Step 2: Simulate LLM-as-judge scores + verified outcomes ────────
#
# In production these come from your eval pipeline (LangSmith, Braintrust,
# etc.) paired with user feedback, A/B results, or human review.
#
# The pattern: eval gives you scores. A human or A/B test tells you
# the REAL quality. GAE learns the gap.

eval_data = [
    # (task_type,        factor_scores,                      verified_quality)
    # — Summarization: "conciseness" scores high, but users prefer
    #   the grounded version even when it's longer
    ("summarization", [0.8, 0.9, 0.3, 0.8, 0.9], "excellent"),  # grounded, long → users loved it
    ("summarization", [0.7, 0.2, 0.9, 0.9, 0.6], "fair"),       # concise but ungrounded → users didn't
    ("summarization", [0.9, 0.8, 0.4, 0.7, 0.8], "good"),       # correct + grounded wins
    ("summarization", [0.3, 0.1, 0.8, 0.6, 0.3], "poor"),       # concise but wrong → bad

    # — QA: correctness + relevance dominate; fluency is noise
    ("qa",            [0.9, 0.7, 0.5, 0.4, 0.9], "excellent"),  # right answer, rough wording → fine
    ("qa",            [0.3, 0.5, 0.8, 0.9, 0.3], "poor"),       # fluent but wrong → bad
    ("qa",            [0.7, 0.6, 0.6, 0.7, 0.8], "good"),
    ("qa",            [0.5, 0.3, 0.7, 0.8, 0.4], "fair"),

    # — Code review: correctness is everything; conciseness helps
    ("code_review",   [0.9, 0.6, 0.8, 0.5, 0.7], "excellent"),  # correct + actionable
    ("code_review",   [0.2, 0.3, 0.9, 0.9, 0.4], "poor"),       # fluent nonsense
    ("code_review",   [0.7, 0.5, 0.7, 0.6, 0.6], "good"),
    ("code_review",   [0.4, 0.2, 0.5, 0.7, 0.3], "fair"),
]

print(f"\n── Learning from {len(eval_data)} verified evals ──\n")

for task_type, scores, verified in eval_data:
    f = np.array(scores, dtype=np.float64)
    ci = cat_idx[task_type]

    # Score: what does GAE currently think?
    result = scorer.score(f, ci)

    # Was GAE's verdict correct?
    correct = (result.action_name == verified)
    gt_ai = act_idx[verified]

    # Update: shift centroids toward reality
    update = scorer.update(
        f=f, category_index=ci,
        action_index=result.action_index,
        correct=correct,
        gt_action_index=gt_ai,
    )
    tag = "✓" if correct else "✗"
    print(f"  {tag} {task_type:14s} predicted={result.action_name:10s} "
          f"actual={verified:10s} Δ={update.centroid_delta_norm:.4f}")

# ── Step 3: What did GAE learn? ──────────────────────────────────────
#
# Ablation: drop each criterion, measure accuracy impact.
# This is how you find out which rubric criteria actually matter.

print(f"\n── Ablation: which criteria predict quality? ──\n")

scenarios = [
    EvaluationScenario(
        scenario_id=f"E{i}",
        domain="llm_eval",
        category=task,
        category_index=cat_idx[task],
        factors=np.array(scores, dtype=np.float64),
        expected_action=verified,
        expected_action_index=act_idx[verified],
    )
    for i, (task, scores, verified) in enumerate(eval_data)
]

ablation = run_ablation(scorer, scenarios, FACTORS)

print(f"  Baseline accuracy: {ablation.baseline_accuracy:.0%}")
for r in ablation.results:
    bar = "█" * max(1, int(abs(r.accuracy_drop) * 40))
    print(f"  #{r.importance_rank} {r.factor_name:14s} "
          f"drop={r.accuracy_drop:+.1%}  {bar}")

print(f"\n  Most important:  {ablation.most_important}")
print(f"  Least important: {ablation.least_important}")

# ── Step 4: Conservation gate ────────────────────────────────────────
#
# α·q·V ≥ θ_min — don't update rubric weights when feedback
# is too thin to be reliable.

alpha = 0.08          # 8% override rate
q     = 0.85          # 85% override quality
V     = len(eval_data) * 10   # verified decisions per day (scale up for demo)

theta = compute_theta_min(alpha=alpha, V=V)
check = check_conservation(alpha=alpha, q=q, V=V, theta_min=theta)

print(f"\n── Conservation gate ──")
print(f"  signal = α·q·V = {check.signal:.3f}")
print(f"  θ_min  = {theta:.3f}")
print(f"  headroom = {check.headroom:.3f}")
print(f"  status = {check.status}")
print(f"  {'Safe to update rubric weights' if check.passed else 'Feedback volume too thin — weights frozen'}")

# ── Step 5: Score a new eval with judgment ───────────────────────────
#
# Now score something new. GAE tells you the verdict,
# which criteria drove it, and how confident it is.

print(f"\n── Score a new eval ──\n")

new_scores = np.array([0.85, 0.9, 0.3, 0.7, 0.8])  # grounded but verbose
result = scorer.score(new_scores, cat_idx["summarization"])

judgment = compute_judgment(
    scoring_result=result,
    f=new_scores,
    mu=scorer.centroids,
    category_index=cat_idx["summarization"],
    factor_names=FACTORS,
    actions=ACTIONS,
)
print(f"  New summarization eval:")
print(f"    Scores:     {dict(zip(FACTORS, [float(x) for x in new_scores]))}")
print(f"    Verdict:    {judgment.action} ({judgment.confidence:.0%} confidence)")
print(f"    Key factors: {judgment.dominant_factors}")
print(f"    Rationale:  {judgment.rationale}")
print(f"\n  Action scores:")
for action, score in judgment.action_scores.items():
    print(f"    {action:12s}: {score:.4f}")

# ── Step 6: Full evaluation report ──────────────────────────────────

report = run_evaluation(scorer, scenarios)
print(f"\n── Evaluation report ──")
print(f"  Accuracy: {report.accuracy:.0%} ({report.n_correct}/{report.n_scenarios})")
print(f"  ECE:      {report.ece:.4f}")
print(f"  By task type:")
for cat, acc in report.by_category.items():
    print(f"    {cat:14s}: {acc:.0%}")

print(f"\n── Done ──")
print(f"LangSmith tracked the experiment.")
print(f"GAE learned from it.")
