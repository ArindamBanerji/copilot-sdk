# VLD Experiments — Cross-Copilot Graph Reasoning
**Location:** `copilot-sdk/experiments/vld/`
**Authority:** MAP VLD Addendum v6

---

## Directory Structure

```
experiments/vld/
├── README.md                      ← This file
├── data/                          ← Astra-generated Stage 1 scenarios (canonical)
│   ├── soc_stage1.json            ← 50 SOC instances (Astra)
│   ├── dataops_stage1.json        ← 50 DataOps instances (Astra)
│   ├── s2p_stage1.json            ← 50 S2P instances (Astra)
│   ├── trading_stage1.json        ← 50 Trading instances (Astra)
│   └── purchasing_stage1.json     ← 50 Purchasing instances (Astra)
├── scripts/                       ← Experiment + chart generation scripts
│   ├── generate_all_pub_charts.py ← PUB-1 to PUB-16 (simulation, v1)
│   ├── vld_graph_reasoning_experiments_v2.py ← PUB-17 to PUB-25 (recurrence)
│   ├── vld_with_without_v2.py     ← Per-copilot case studies + 4 charts each
│   ├── validate_astra_scenarios.py ← Generic Astra output validator
│   └── merge_supplement.py        ← Merge base + supplement datasets
├── results/                       ← With-without + evaluation outputs
│   ├── case_studies_soc_astra.md
│   ├── case_studies_dataops_astra.md
│   ├── case_studies_s2p_astra.md
│   ├── case_studies_trading_astra.md
│   └── case_studies_purchasing_astra.md
├── pub_charts/                    ← All publication charts (PNG)
│   ├── pub1_routing_comparators.png    ... PUB-16
│   ├── pub17_depth_accuracy_confidence.png ... PUB-25
│   └── pub_ww_{copilot}_*.png         (4 charts × 5 copilots)
├── docs/                          ← Design documents and addenda
│   ├── map_vld_addendum_v6.md
│   ├── vld_recurrence_addendum_v1.md
│   └── astra_prompts/             ← Astra generation prompts (reproducibility)
│       ├── astra_soc_full_50.md
│       ├── astra_dataops_full_50.md
│       ├── astra_s2p_full_50.md
│       ├── astra_trading_full_50.md
│       └── astra_purchasing_full_50.md
└── prompts/                       ← Codex prompts (evaluation scripts)
    ├── codex_e2_dataops_evaluation.md
    ├── codex_e3_s2p_evaluation.md
    ├── codex_e4_trading_evaluation.md
    ├── codex_e5_purchasing_evaluation.md
    └── codex_w1_soc_graph_wiring.md
```

## Cross-Copilot Results (Astra Data)

| Copilot | Scenarios | VLD saves | VLD hurts | Ratio | Data source |
|---|---|---|---|---|---|
| SOC | 50 | 43 | 0 | inf | Astra |
| DataOps | 50 | 38 | 0 | inf | Astra |
| S2P | 50 | 40 | 0 | inf | Astra |
| Trading | 50 | 39 | 0 | inf | Astra |
| Purchasing | 50 | 40 | 0 | inf | Astra |
| **Total** | **250** | **200** | **0** | **inf** | |

## Per-Copilot Evaluators (in app directories, not here)

These remain in their copilot app directories since Codex built them there:

```
apps/dataops/backend/scripts/evaluate_multihop_stage1.py
apps/trading/backend/scripts/evaluate_multihop_stage1.py
apps/purchasing/backend/scripts/evaluate_multihop_stage1.py
```

SOC evaluator: `gen-ai-roi-demo-v4-v50/backend/scripts/evaluate_multihop_stage1.py`
S2P evaluator: `s2p-copilot/backend/scripts/evaluate_multihop_stage1.py`

## How to Regenerate Charts

```bash
# From copilot-sdk root:

# PUB-1 through PUB-16 (no data dependency — hardcoded simulation values)
python experiments/vld/scripts/generate_all_pub_charts.py experiments/vld/pub_charts

# PUB-17 through PUB-25 (needs SOC stage1 data)
python experiments/vld/scripts/vld_graph_reasoning_experiments_v2.py experiments/vld/data/soc_stage1.json experiments/vld/pub_charts

# With-without per copilot
python experiments/vld/scripts/vld_with_without_v2.py experiments/vld/data/soc_stage1.json soc_astra experiments/vld/pub_charts
python experiments/vld/scripts/vld_with_without_v2.py experiments/vld/data/dataops_stage1.json dataops_astra experiments/vld/pub_charts
python experiments/vld/scripts/vld_with_without_v2.py experiments/vld/data/s2p_stage1.json s2p_astra experiments/vld/pub_charts
python experiments/vld/scripts/vld_with_without_v2.py experiments/vld/data/trading_stage1.json trading_astra experiments/vld/pub_charts
python experiments/vld/scripts/vld_with_without_v2.py experiments/vld/data/purchasing_stage1.json purchasing_astra experiments/vld/pub_charts
```

## Publication Chart Inventory (33 charts)

| Range | Source | Count |
|---|---|---|
| PUB-1 to PUB-8, PUB-14 to PUB-16 | Simulation | 11 |
| PUB-17, PUB-17b, PUB-18 to PUB-25 | Recurrence experiments | 10 |
| pub_ww_{copilot}_* | With-without (5 copilots × 4) | 20 |
| case_studies_{copilot}.md | Narrative case studies | 5 |
| **Total** | | **46 files** |
