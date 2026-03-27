# copilot-sdk

Build compounding intelligence copilots on any domain.

The engine is open. The framework is open. The protocols are open.
The domain expertise, calibrated values, and accumulated geometry are the product.

## Quick Start

```
pip install git+https://github.com/ArindamBanerji/copilot-sdk.git
```

```python
from copilot_sdk.protocols import DomainConfig, FactorComputer
```

See `examples/hello_world/` for a minimal working copilot.

## Validated Domains

- SOC Copilot (security operations) — +40.93pp Day-1 accuracy lift
- S2P Copilot (procurement) — +54.98pp Day-1 accuracy lift

Platform claim: +40-55pp Day-1 accuracy lift, domain-agnostic.

## Architecture

Three tiers:

- **Tier 1**: GAE (math library, open, Apache 2.0)
- **Tier 2**: copilot-sdk (framework + protocols, open, Apache 2.0)
- **Tier 3**: Domain copilots (SOC, S2P) — domain expertise, proprietary
