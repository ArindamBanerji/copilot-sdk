"""Substantiation declaration template for surfaced claims."""

DECLARATION_TEMPLATE = """
SUBSTANTIATION DECLARATION (Rule 66):
- Surfaced values/claims: [every metric/badge/advisory this feature shows a user]
- Tier per value:  proven(T-A) | scraped(T-S,context) | sample(K3) | real-pending(T-R,learned)
- Generated data this prompt creates: none | K1-oracle | K2-factor-oracle | K3-demo-fixture
- Labeling (Rule 67): every surfaced value carries learned / context / proven / sample
- Magnitude guard (F-24): no value asserted at REAL(learned) without a pilot evidence_ref
- K3 guard (F-26): demo-fixture values NEVER appear in a metric, score, par, or claim
- If measurement-gated: decision-node fields = [treatment_flag, outcome_var, accuracy_var];
  holdout assigner = <name>; K1 oracle class = <name>; pipeline smoke-test = <test file>
"""
