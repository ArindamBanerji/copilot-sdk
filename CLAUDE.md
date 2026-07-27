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

| # | Rule |
|---|---|
| 66 | Rule 63 EXTENDED — substantiation tier required alongside provenance tier. Every user-facing value carries BOTH: provenance (Rule 63) AND substantiation (T-A/T-S/T-O/T-R). No magnitude claim below REAL (F-24). |
| 67 | Generated-data labeling by kind (K1-K4). K1/K2 oracle data NEVER surfaces. K3 demo-fixtures labeled `sample`, NEVER in a metric/score/par/claim. K4 scraped labeled `scraped_external`/░░. |

## Forbidden Product Integrity Violations

| ID | Forbidden |
|---|---|
| F-24 | Claim at a tier higher than its evidence: magnitude claimed as REAL without pilot `evidence_ref`. |
| F-25 | Scraped/external (░░) presented as customer-learned (██). |
| F-26 | K3 demo-fixture in a metric/score/par/claim. |
| F-27 | K1/K2 oracle output surfaced to user or as magnitude claim. |

## Testing Rules

### Playwright Selector Stability

No position-dependent Playwright selectors. Do NOT use
`page.locator("main section").first()` or `.nth(N)` to select components by
layout position. Use `data-testid` on every component root. Position-based
selectors break when panels are added or reordered, as proven by the P75 trust
radar mount. SAFE: `getByTestId("x").first()` to disambiguate multiple matching
testids. FRAGILE: `locator("tag").first()` to assume layout order.

### No Mock/Fake Scorer, Store, or Conservation

Tests MUST NOT fake, mock, stub, or monkeypatch any of the following:

- `CompoundingScorer` or any scorer `.learn()` / `.score()` methods
- `GraphStore`, `SQLiteGraphStore`, or any store `.write_decision()` / `.write_outcome()` methods
- Conservation status helpers such as `_conservation_status`
- `EvidenceLedger` or any audit chain methods

Why: A fake scorer that bypassed conservation-pause hid a real bug where
double-verify returned 200 instead of 409. Mocks that do not match production
behavior give false confidence.

Use real scorer and store paths instead:

- Create a real scorer: `CompoundingScorer.from_preset(domain, db_path=tmp_db)`
- Seed decisions with `scorer.score()` + `scorer.learn()` in a loop
- Use `conftest.py` shared fixtures for common seeded states
- 50 score+learn cycles is acceptable test setup cost

Acceptable mocks:

- External APIs such as Toast, QBO, and broker connectors
- Environment variables through `monkeypatch.setenv`
- File system paths
- Network/HTTP calls
- Clock/time through freezegun

CI check: `scripts/check_no_scorer_mocks.py` scans test files for forbidden
patterns and fails the build if found. Allowed exceptions must be marked on the
same line with `# MOCK-OK: reason`.

## After Any Change

1. `python -m pytest tests/ -v` (18 tests must pass)
2. Verify: `pip install . && python -c "from copilot_sdk import CopilotFramework; print('OK')"`
3. If you changed a protocol: grep for it in gen-ai-roi-demo-v4-v50 and s2p-copilot.

## graphify

This project has a graphify knowledge graph at graphify-out/.

Rules:
- Before answering architecture or codebase questions, read graphify-out/GRAPH_REPORT.md for god nodes and community structure
- If graphify-out/wiki/index.md exists, navigate it instead of reading raw files
- For cross-module "how does X relate to Y" questions, prefer `graphify query "<question>"`, `graphify path "<A>" "<B>"`, or `graphify explain "<concept>"` over grep — these traverse the graph's EXTRACTED + INFERRED edges instead of scanning files
- After modifying code files in this session, run `graphify update .` to keep the graph current (AST-only, no API cost)

## Rule #63 — Test Double Completeness

No mock/monkeypatch in test code unless the external dependency is
truly unreachable (network, hardware, paid API). Test doubles must
be complete — track state and answer queries from their own state.

If a test double needs monkeypatching to work with new code, the
test double is incomplete. Fix the double, not the caller.

Retroactive audit needed: check all existing monkeypatch usage
against this rule. Violations are technical debt, not exceptions.
