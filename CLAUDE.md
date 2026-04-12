# CLAUDE.md — Copilot SDK
# License: Apache 2.0 — public package

## Purpose
Public SDK for building domain copilots on the GAE engine.
Defines protocols. Does not implement domain logic.

## 4 Protocols
- ScorerProtocol — wraps ProfileScorer
- MonitorProtocol — wraps ConservationMonitor
- ConfigProtocol — wraps DomainConfig
- LedgerProtocol — wraps Evidence Ledger

## After any change
1. python -m pytest tests/ -v (10 tests must pass)
2. Verify: pip install . && python -c
   "from copilot_sdk import CopilotFramework; print('OK')"

## Discipline rules
- Never import from app.domains.soc or app.domains.s2p
- Never import from gen-ai-roi-demo-v4-v50
- Only import from gae (Apache 2.0) and ci-platform (Apache 2.0)
- If a class name contains "SOC", "Alert", or "Triage", it does
  not belong here
