# ⚠️ GROUNDING CONTRACT (non-negotiable)

**These rules apply to every AI coding agent working in this repo.**

1. **Docs are aspirational until proven in code.** Check actual source files.
2. **Cite file + line for every behavioral claim.**
3. **Code and tests beat docs.** Discrepancy = DRIFT, report and stop.
4. **Verify after every change:** `python -m pytest tests/ -v`

---

## How to Think (read first, every session)

1. State assumptions before coding. Never silently pick a field name.
2. Minimum code that solves the problem.
3. Surgical changes only.
4. Verify after every step — "this should work" is not verification.
5. Before adding a constant: grep to check if it exists under a different name.

---

## What This Repo Is

Copilot SDK — a **public package** (Apache 2.0) for building domain copilots
on the GAE engine. Defines protocols. Does not implement domain logic.

- No database dependencies. No domain-specific code. No UI.
- Only imports from gae (Apache 2.0) and ci-platform (Apache 2.0).

### 4 Protocols

- `ScorerProtocol` — wraps ProfileScorer
- `MonitorProtocol` — wraps ConservationMonitor
- `ConfigProtocol` — wraps DomainConfig
- `LedgerProtocol` — wraps Evidence Ledger

---

## Protocol Discipline (critical)

The SDK is the public interface. It must never leak domain internals.

- **Never** import from `app.domains.soc` or `app.domains.s2p`.
- **Never** import from gen-ai-roi-demo-v4-v50.
- **Only** import from gae and ci-platform.
- If a class name contains "SOC", "Alert", or "Triage", it does not belong here.
- SDK protocols must match GAE Tier 1 API. If they don't: fix the protocol.

---

## Rules

- Do NOT use git directly. User handles all git operations.
- asyncio.run() not asyncio.get_event_loop() (Windows Python 3.11+).

## After Any Change

1. `python -m pytest tests/ -v` (18 tests must pass)
2. Verify: `pip install . && python -c "from copilot_sdk import CopilotFramework; print('OK')"`
3. If you changed a protocol: grep for it in gen-ai-roi-demo-v4-v50 and s2p-copilot.
