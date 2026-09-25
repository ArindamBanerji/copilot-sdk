# VLD Q Equation Reference — 2026-09-12

This document records the exact Q computation implemented in `copilot_sdk/scoring/investigation.py` as of this run. It is derived from the code, not from older paper phrasing.

## 1. The Exact Q Equation

The implementation lives in `VLDInvestigator.compute_Q()` at `copilot_sdk/scoring/investigation.py:131-160`. Inputs are normalized at lines 138-148, top actions are selected at lines 143-145, and the per-dimension score is computed at lines 149-159.

For each dimension `d` that has not already been attempted in the current investigation episode:

```text
Q_d = precision_d + discriminative_d + leverage_d
```

where the code defines:

```text
precision_d      = (1 / max(σ_d^2, 0.001)) / 100
discriminative_d = | μ_{a1,d} - μ_{a2,d} |
leverage_d       = | (v_d - μ_{a1,d})^2 - (v_d - μ_{a2,d})^2 |
```

Then, if K weights are provided:

```text
Q_d = K_d * (precision_d + discriminative_d + leverage_d)
```

Definitions:

- `σ_d` is `self.sigma[d]`, copied into the investigator at `investigation.py:57`. It is a per-dimension scale/uncertainty vector. The Q precision term uses a floor of `0.001` on `σ_d^2`, then divides by `100` (`investigation.py:154`).
- `μ_{a,d}` is `self.mu[a, d]`, copied into the investigator at `investigation.py:54`. `self.mu` has shape `(actions, factors)` and is read-only within the investigator.
- `a1` is the highest-probability action under the current probability vector `P`; `a2` is the second-highest-probability action (`investigation.py:143-145`).
- `v_d` is the current factor value for dimension `d`; it is taken from `vector = self._vector(v)` at `investigation.py:138`.
- `K_d` is the optional per-dimension utility weight supplied as `K_weights`; it must have the same shape as the factor dimension (`investigation.py:146-148`).
- `τ` is not directly in `compute_Q()`. It affects Q indirectly when the investigator's fallback scorer converts centroid distances into probabilities, because those probabilities determine `a1` and `a2`. The fallback scorer uses `logits = -dists / self.tau` at `investigation.py:71`. When a production `score_fn` is supplied, `τ` is not used for action probabilities; the production scorer's returned probabilities determine `a1` and `a2`.

The fallback scoring path used when `score_fn is None` computes distances at `investigation.py:67-75`:

```text
dist_a = Σ_d [ (1 / max(σ_d^2, 0.001)) * (v_d - μ_{a,d})^2 ]
P(a | v) = softmax(-dist_a / τ)
```

The production-scoring path is selected through `predict()` at `investigation.py:84-96`; it calls the supplied `score_fn` and normalizes the result at `investigation.py:98-129`.

## 2. K Modulation

K modulation is multiplicative. The additive base score is computed first, then line 159 multiplies by `K_d` if K weights are present:

```text
Q_d ← Q_d * K_d
```

Uniform K changes the absolute scale of all available dimensions but does not change their ranking. With the default K baseline of `0.5`, every non-excluded Q value is halved, and `argmax(Q)` is unchanged as long as all dimensions have the same K.

At the lower bound `K_d = 0.1`, a dimension keeps only 20% of the baseline-0.5 priority and 1/30 of the upper-bound priority. At the upper bound `K_d = 3.0`, a dimension receives 6× the baseline-0.5 priority and 30× the lower-bound priority. K therefore acts as a learned attention multiplier over dimensions, not as an additive reward term.

## 3. Dimension Selection

The next dimension is chosen in `VLDInvestigator.investigate()` at `investigation.py:179-184`:

```text
q = self.compute_Q(v, p_before, enriched, K_weights)
k_star = int(np.argmax(q))
if q[k_star] <= 0: break
```

Attempted dimensions are tracked in `enriched`. Inside `compute_Q()`, any dimension in `enriched` receives `Q_d = -1.0` at `investigation.py:150-153`, excluding it from future selection while any unattempted dimension has positive Q.

Tie-breaking is NumPy's default `argmax`: the first maximum index is selected. There is no random tie-breaker.

When all dimensions have been attempted, all Q values are `-1.0`, so the next selected value would fail `q[k_star] <= 0` and the loop stops.

## 4. Post-Read Q Recomputation

Q is recomputed on every loop iteration. At the top of each step, `predict()` scores the current vector `v` (`investigation.py:180`), then `compute_Q()` receives that same current vector and current probabilities (`investigation.py:181`). After evidence is applied, `v[k_star]` is updated at `investigation.py:214-221`, and the action is re-scored at `investigation.py:222`.

The recomputation uses the updated factor vector, not the original surface vector. It also uses the updated probability ranking, so `a1` and `a2` can change after a read.

Sigma does not change within an investigation episode. It is copied into the investigator during construction and treated as fixed. K also does not change within an episode unless the caller supplies different K weights in a separate investigation call. The K learning store updates happen outside the episode after traces are evaluated.

Empty and error reads still mark the dimension as attempted (`investigation.py:193`) and append a trace step with status `empty` or `error` (`investigation.py:194-213`). That means failed reads consume budget and force the next Q recomputation to choose among remaining dimensions.

## 5. Comparison to Paper Formulations

Older prompt language and some paper notes describe Q as a product or as a temperature-scaled expression. The code is different in two ways:

1. The implemented base Q is additive:

```text
precision + discriminative + leverage
```

It is not multiplicative. This matters because a dimension can remain selectable when one component is small or zero.

2. Temperature `τ` is not a direct multiplier or divisor in `compute_Q()`. It only affects Q indirectly through the action probabilities `P` if the fallback scorer is used. With production scorer parity, `score_fn` supplies probabilities, and Q receives only those probabilities plus the current vector, mu, sigma, and K.

The pre-paper should therefore avoid claiming that Q is `sigma * centroid gap / tau`, unless it is explicitly describing an older approximation or a separate analytical simplification. The code's implemented priority is the additive three-term formula above, optionally multiplied by K.

## 6. Recommended Paper Formulation

Use this wording for the implementation-backed description:

> At each investigation step, VLD scores the current factor vector with the production scorer, takes the top two actions under the returned action probabilities, and computes a per-dimension read priority. For an unattempted dimension d, the priority is the sum of a precision term, a top-two centroid-discrimination term, and a leverage term measuring how much d changes the relative squared error to the top two action centroids. Learned K weights multiply this priority. The next read is the unattempted dimension with maximum K-weighted priority. After evidence is read and the factor vector is updated, VLD re-scores and recomputes Q from the updated vector and updated top-two action ranking.

Mathematically:

```text
Q_d(v, P, K) = K_d [ 1/(100 * max(σ_d^2, 0.001))
                    + |μ_{a1,d} - μ_{a2,d}|
                    + |(v_d - μ_{a1,d})^2 - (v_d - μ_{a2,d})^2| ]
```

where `a1 = argmax_a P(a | v)` and `a2` is the second-highest-probability action. If no K vector is supplied, use `K_d = 1` for this equation. In the K-learning experiments, the fixed control starts from uniform `K_d = 0.5`, which preserves the same ranking while changing scale.
