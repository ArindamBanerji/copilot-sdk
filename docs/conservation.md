# Conservation

Conservation controls whether learning should continue. It prevents a copilot from compounding weak or unsafe outcome streams.

## Formula

```text
alpha * q * V >= 23.53
```

The threshold comes from the James-Stein theory used by the GAE conservation discipline.

## Variables

| Variable | Meaning |
|---|---|
| `alpha` | Shrinkage intensity, with `0 < alpha < 1` |
| `q` | Quality signal, derived from correct/incorrect verified outcomes |
| `V` | Decision volume, the verified outcome count |

## States

| State | Meaning |
|---|---|
| GREEN | Learning active |
| AMBER | Warning state; applications may auto-pause |
| RED | Learning paused |

## Current SDK Preset Penalty Ratios

These values are read from the current preset code.

| Copilot | penalty_ratio |
|---|---:|
| SOC | 20.0 |
| Trading | 3.0 |
| Purchasing | 3.0 |
| DataOps | 10.0 |
| S2P | 5.0 |

## Why Conservation Is Path-Sensitive

Conservation depends on verified outcomes in sequence. Two copilots can have the same final number of correct and incorrect decisions but move through different AMBER or RED intervals depending on ordering. That matters because learning can pause during unsafe intervals, so the path affects which outcomes are allowed to reshape the model.

## auto_pause_on_amber

When `auto_pause_on_amber` is enabled, AMBER stops learning early instead of waiting for RED. This is useful when a domain has high downside risk or when early pilot data is noisy.

## Recovery

Conservation can recover when verified accuracy improves. A domain should resume learning only when the conservation monitor reports that the quality and volume terms are strong enough again.

## Practical Guidance

- Track `V` as verified outcome count, not raw score count.
- Do not double-count outcomes.
- Treat missing or failed conservation checks as unsafe in production paths.
- Surface conservation state with provenance so users can tell whether learning is live, paused, or degraded.
