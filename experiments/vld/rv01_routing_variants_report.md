# RV-0/RV-1 Routing Variant Report

## 1. Protocol and Pre-Registration

RV-0 compared STATIC, RNN, GRU, and LSTM routing on DataOps exported centroids with 10 seeds, 500 decisions, 10 checkpoints, 50 evaluation scenarios per checkpoint, and budget sweeps B=1..4. LSTM is kept only if it exceeds GRU by at least 2 percentage points at matched scorer-evaluation cost.

RV-1 compared greedy Q, Thompson Q, and UCB Q across DataOps, Trading, Purchasing, SOC, and S2P. A bandit variant is kept only if it lowers worst-copilot starvation by at least 10 percentage points, does not reduce final routing quality, and reaches the K-learning asymptote in no more decisions than greedy.

## 2. RV-0 Results -- GRU vs LSTM

| Variant | Routing | Accuracy | Accuracy / scorer eval | Starvation | Evals/decision |
|---|---:|---:|---:|---:|---:|
| STATIC | 57.8% +/- 7.8% | 73.6% | 0.2453 | 5.6% | 3.00 |
| RNN | 56.3% +/- 7.1% | 77.6% | 0.1940 | 8.6% | 4.00 |
| GRU | 48.8% +/- 5.1% | 69.2% | 0.1730 | 8.6% | 4.00 |
| LSTM | 47.0% +/- 4.6% | 66.4% | 0.1660 | 5.8% | 4.00 |

Verdict: **GRU**. LSTM margin over GRU was -1.80pp, below the pre-registered 2pp keep threshold.

Budget sensitivity: the budget sweep is written in `rv0_gru_ablation_results.json` and charted in `pub_rv0_budget_sweep.png`. The paper decision should use B=2 unless a deployment explicitly operates at B=1 or B=4.

## 3. RV-1 Results -- Bandit Exploration

| Copilot | Variant | Routing | Accuracy | Starvation | Decisions to 90% |
|---|---|---:|---:|---:|---:|
| dataops | greedy | 56.3% | 77.8% | 7.5% | 150 |
| dataops | thompson | 54.4% | 76.8% | 0.0% | 250 |
| dataops | ucb | 54.1% | 74.8% | 0.0% | 200 |
| trading | greedy | 73.6% | 91.4% | 48.2% | 150 |
| trading | thompson | 53.0% | 67.8% | 0.0% | 350 |
| trading | ucb | 65.0% | 82.0% | 0.0% | 250 |
| purchasing | greedy | 66.4% | 75.2% | 31.4% | 150 |
| purchasing | thompson | 51.7% | 58.0% | 0.0% | 400 |
| purchasing | ucb | 64.4% | 73.8% | 0.0% | 350 |
| soc | greedy | 81.0% | 92.4% | 32.2% | 100 |
| soc | thompson | 60.1% | 69.4% | 0.0% | 400 |
| soc | ucb | 81.1% | 91.6% | 0.0% | 300 |
| s2p | greedy | 66.3% | 79.8% | 20.5% | 50 |
| s2p | thompson | 51.2% | 73.4% | 0.0% | 400 |
| s2p | ucb | 66.6% | 80.6% | 0.0% | 250 |

Trading starvation: greedy=48.2%, Thompson=0.0%, UCB=0.0%.

Verdict: **greedy**. No bandit variant met all pre-registered keep criteria on Trading starvation, routing quality, and speed.

## 4. Combined Verdict

Recommended paper configuration from these experiments: **STATIC + greedy**. RV-0 keeps GRU over LSTM for the specific recurrent-cell ablation, but the best tested RV-0 routing quality at B=2 was STATIC. RV-1 determines whether greedy selection should be replaced with exploration.

## 5. Three-Metric Summary

M-VALUE: RV-0 value is final informative-read routing quality; RV-1 value is final routing quality plus decisions to 90% asymptote. M-COST is accuracy per scorer evaluation for RV-0 and unchanged budget/scorer loop for RV-1. M-GOV remains pass for all tested variants because each hidden/exploration state is dimension-aligned to named factors.

## 6. Implications for Section 12.2

The routing section should report the pre-registered kill/keep criteria, then cite the exact RV-0 and RV-1 verdicts above. If GRU is retained, describe LSTM as an ablated higher-cost recurrence. If a bandit is retained, frame it as an exploration guardrail for high-starvation domains, with Trading as the motivating case.
