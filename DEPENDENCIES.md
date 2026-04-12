# Copilot SDK Dependencies

## Consumed by
- External developers building domain copilots on the GAE engine
- gen-ai-roi-demo-v4-v50 (consumes protocol definitions; must not be imported by the SDK)

## Depends on
- `gae` / graph-attention-engine (Apache 2.0) — GAE Tier 1 types and scoring engine
- `ci-platform` (Apache 2.0, optional) — infrastructure protocols
- `numpy>=1.24.0` — required by GAE numerics

## Discipline
- Never import from `app.domains.soc` or `app.domains.s2p`
- Never import from `gen-ai-roi-demo-v4-v50`
- Only import from `gae` (Apache 2.0) and `ci-platform` (Apache 2.0)
- Protocols match GAE Tier 1 API: `DomainConfig`, `FactorComputer`, `SourceConnector`, `ReferralRule`
- Class names must not contain `SOC`, `Alert`, or `Triage`

## Verification after any change
1. python -m pytest tests/ -v (18 tests must pass)
2. pip install . && python -c
   "from copilot_sdk import CopilotFramework; print('OK')"
