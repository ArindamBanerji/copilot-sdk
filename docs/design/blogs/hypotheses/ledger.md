# Hypothesis ledger

| ID | Hypothesis | Status | Result tier | Evidence / note |
|---|---|---|---|---|
| H-TRUST | Reliability-weighted metric beats cosine and uniform L2 on bounded magnitude-bearing features, with gain increasing under per-factor noise heterogeneity. | re-defining | C1 INVALIDATED; C2 INVALIDATED on Credit/Adult, COIL UNTESTABLE | v2.1 factorial run: F1/F2'/F3 fired or failed their robustness gates. See `h-trust/results_v1.md`; scope is now a negative/re-defining result. |
| H-CURVE | Re-convergence is faster than first convergence above the firm-mismatch threshold, with γ direction independent of the scoring threshold. | re-defining | INVALIDATED by F3; θ-free γ INCONCLUSIVE due 9/9 censored cells | v3 parametric run: all construction gates and persistence gates passed, but all 18 raw phase trajectories had monotonicity violations; γ_dist was censored in all 9 cells. See h-curve/results_v1.md. |
