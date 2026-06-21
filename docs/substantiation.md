# Substantiation

Substantiation is the discipline that every surfaced value must be traceable to evidence. A score, metric, badge, threshold, or claim should say where it came from and what kind of proof supports it.

## Four-Tier Provenance Model

| Tier | Label | Meaning |
|---|---|---|
| T-A | Analytic | Mathematically derived and fully reproducible |
| T-S | Scraped | External data, cached, may go stale |
| T-O | Operator | Human-configured thresholds, labels, or workflow choices |
| T-R | Real-pending | From live decisions, but not yet statistically proven |

Frontend badges may render these as compact labels with tooltips. The important contract is that the tier travels with the value.

## ClaimRegistry

`ClaimRegistry` stores claim-level provenance. The default registry currently contains 32 entries across:

- cross-copilot
- trading
- purchasing
- s2p
- dataops
- soc

Each claim has:

- `claim_id`
- copilot
- text
- tier
- evidence reference
- optional promotion history

## Core Rules

| Rule | Contract |
|---|---|
| C-21 | All surfaced values carry `provenance_tier` |
| C-22 | No K3 fixture data appears in metrics |
| F-24 | No magnitude claim below REAL evidence |
| F-25 | Scraped/external data is not presented as customer-learned data |
| F-26 | K3 demo fixture data is blocked from metrics, scores, PAR, and claims |
| F-27 | K1/K2 oracle output is not surfaced to users as a magnitude claim |

## DayZeroReadiness

`DayZeroReadiness` tracks measurement-gated features before pilot proof exists. The default readiness list currently has seven entries. SOC campaign intelligence is marked proven; the other entries are populated and instrumented but still need proof.

Each entry records:

- feature
- copilot
- populated
- proven
- instrumented
- real path committed
- honest labels

## F-26 Gate

Production metric paths should use an F-26 gate such as:

```python
assert_no_sample_in_metric(records, metric_name)
```

The gate rejects records with `provenance == "sample"` before they feed metrics or claims. K3 fixture data may support demos, but it must not silently become a production metric.

## Domain Oracles

Oracles validate the measurement pipeline. They do not prove customer-specific lift.

SDK oracle classes include:

- `TraderOracle`
- `ChefOracle`
- `DataOpsOracle`

Application-level oracle implementations include:

- `AnalystOracle`
- `BuyerOracle`

The common pattern is:

1. Generate synthetic treatment and control outcomes with a known injected effect.
2. Run those outcomes through the pipeline.
3. Measure lift.
4. Gate success on positive lift and treatment accuracy at least as good as control.

## Holdout Protocol

| Class | Behavior |
|---|---|
| `UnconditionalHoldout` | SHA-256 deterministic split, often 15% |
| `ConditionalHoldout` | Split is triggered only when a domain event or enrichment condition applies |

The holdout assignment must be deterministic for a given entity id and seed.

## K4 Connectors

K4 connector work adds real external inputs with `scraped_external` provenance. Current connector families include:

| Source | Purpose |
|---|---|
| yfinance | Market data |
| FRED | Macro data |
| QBO | Accounting data |
| MITRE ATT&CK + NVD | Threat intelligence |
| SEC EDGAR + FDA | Supplier intelligence |
| ISO 8000 + Schema.org | Data quality standards |

## ProvenanceBadge

`ProvenanceBadge` is a frontend pattern for showing T-A/T-S/T-O/T-R to users. The badge should include a tooltip that explains the source and whether the value is analytic, scraped, operator-configured, or real-pending.

## Part 5 Extraction

The SDK-level substantiation protocol classes live in:

- `oracle.py`
- `holdout.py`
- `instrument.py`

These files define the portable interfaces used by domain apps without importing app-specific SOC, S2P, Trading, Purchasing, or DataOps code.
