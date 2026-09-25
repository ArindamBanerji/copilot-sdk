# RL-CTRL-1 Option B — Fork Harness

Sanity passed: True
Core diff lines: 12 (total including controller/output: 159)

| Copilot | Arm | Plateau height | Trajectory variance |
|---|---|---:|---:|
| soc | A0_fixed | 0.730 | 0.0000 |
| soc | A1_rule_based | 0.740 | 0.0000 |
| soc | A2_learned | 0.727 | 0.0000 |
| dataops | A0_fixed | 0.680 | 0.0000 |
| dataops | A1_rule_based | 0.647 | 0.0000 |
| dataops | A2_learned | 0.650 | 0.0000 |

## K-state divergence

{
  "dataops": {
    "A1_rule_based": {
      "1000": 0.8893564466014373,
      "500": 0.9880925960998163
    },
    "A2_learned": {
      "1000": 0.20909474995331767,
      "500": 0.11989149474420503
    }
  },
  "soc": {
    "A1_rule_based": {
      "1000": 0.4489571087905082,
      "500": 0.6839663996417672
    },
    "A2_learned": {
      "1000": 0.10295277877110309,
      "500": 0.07624274047074363
    }
  }
}

## Verdict

A0 preserves the original loop; controller arms are exploratory and conservation-constrained.
