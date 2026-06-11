# Trading CLI Spec Coverage Audit

Date: 2026-06-07
Model: gpt-5.3
Task Type: SPEC COVERAGE AUDIT. NO IMPLEMENTATION CHANGES.
Repo: copilot-sdk
PD File: docs/design/trading_copilot_product_definition_v1.md
CLI File: apps/trading/backend/cli.py

## Executive Summary
- P52 TRD-CLI-CORE verdict: SUPPLEMENT
- P61 TRD-CLI-FULL verdict: SUPPLEMENT
- CLI entrypoint help status: PASS for `python .\cli.py --help`
- Biggest gaps: `connect`, `patterns`, and `dashboard` are absent from the backend CLI parser/help; `import`, `score`, `trust`, and `conservation` are reachable but do not fully implement the PD behavior; `backup` does not back up centroids + weights.
- Recommended next prompt: Write a targeted CLI supplement prompt.

## Path Resolution
- Repo path: C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\kaggle_experiments\claude_projects\copilot-sdk
- PD file found: True, docs/design/trading_copilot_product_definition_v1.md
- CLI file found: True, apps/trading/backend/cli.py
- implementation_plans path: True, docs/implementation_plans
- pyproject / entrypoint evidence: apps/trading/pyproject.toml lines 51-52 define `[project.scripts]` and `ci-trading = "ci_trading.cli:main"`. apps/trading/ci_trading/cli.py loads apps/trading/backend/cli.py and calls its `main()`.

## CLAUDE.md Relevant Notes
Relevant instructions: docs are aspirational until proven in code; cite file and line for behavioral claims; code and tests beat docs; do not use git directly. The repo also normally requires pytest after code changes, but this audit made no application code changes and the task explicitly forbids pytest.

## PD Command Requirements
Command: init
Scope: P52
PD section: 10.3 CLI Design
PD quote: `ci-trading init                          # creates ~/.ci-trading/`
Line evidence: docs/design/trading_copilot_product_definition_v1.md:1312

Command: connect
Scope: P52 by user audit scope; also first-use CLI in PD
PD section: 10.3 CLI Design
PD quote: `ci-trading connect alpaca --paper        # OAuth flow`
Line evidence: docs/design/trading_copilot_product_definition_v1.md:1313

Command: import
Scope: P52
PD section: F8 and 10.3 CLI Design
PD quote: `ci-trading import --broker alpaca --days 365`
Line evidence: docs/design/trading_copilot_product_definition_v1.md:747
PD quote: `ci-trading import --days 365             # import last year`
Line evidence: docs/design/trading_copilot_product_definition_v1.md:1314

Command: score
Scope: P52
PD section: F8 and 10.3 CLI Design
PD quote: `ci-trading score --trade-id TRD-1847`
Line evidence: docs/design/trading_copilot_product_definition_v1.md:748
PD quote: `ci-trading score                         # score today's trades`
Line evidence: docs/design/trading_copilot_product_definition_v1.md:1318

Command: trust
Scope: P52
PD section: F8 and 10.3 CLI Design
PD quote: `ci-trading trust --show-radar`
Line evidence: docs/design/trading_copilot_product_definition_v1.md:749
PD quote: `ci-trading trust                         # show signal trust analysis`
Line evidence: docs/design/trading_copilot_product_definition_v1.md:1319

Command: conservation
Scope: P52 by user audit scope; Phase 1 dependency in PD
PD section: F8 and 10.3 CLI Design
PD quote: `ci-trading conservation --strategy trend_following`
Line evidence: docs/design/trading_copilot_product_definition_v1.md:750
PD quote: `ci-trading conservation                  # show strategy safety`
Line evidence: docs/design/trading_copilot_product_definition_v1.md:1321

Command: patterns
Scope: P61
PD section: F8 and 10.3 CLI Design
PD quote: `ci-trading patterns --min-significance 0.05`
Line evidence: docs/design/trading_copilot_product_definition_v1.md:751
PD quote: `ci-trading patterns                      # show detected patterns`
Line evidence: docs/design/trading_copilot_product_definition_v1.md:1320

Command: dashboard
Scope: P61
PD section: 10.3 CLI Design
PD quote: `ci-trading dashboard                     # opens local web UI`
Line evidence: docs/design/trading_copilot_product_definition_v1.md:1317

Command: export
Scope: P61
PD section: 10.3 CLI Design and API table
PD quote: `ci-trading export --format csv           # export all data`
Line evidence: docs/design/trading_copilot_product_definition_v1.md:1324
PD quote: `/api/trading/export | GET | Full data export (CSV/JSON) | v1.0`
Line evidence: docs/design/trading_copilot_product_definition_v1.md:1301

Command: backup
Scope: P61
PD section: 10.3 CLI Design and API table
PD quote: `ci-trading backup                        # backup centroids + weights`
Line evidence: docs/design/trading_copilot_product_definition_v1.md:1325
PD quote: `/api/trading/backup | POST | Backup centroids + weights | v1.0`
Line evidence: docs/design/trading_copilot_product_definition_v1.md:1302

Command: restore
Scope: P61
PD section: 10.3 CLI Design and API table
PD quote: `ci-trading restore --from backup.json    # restore profile`
Line evidence: docs/design/trading_copilot_product_definition_v1.md:1326
PD quote: `/api/trading/restore | POST | Restore from backup | v1.0`
Line evidence: docs/design/trading_copilot_product_definition_v1.md:1303

Additional scope evidence:
PD line 1370: `| 0.5 | CLI: init + import + score + trust | 2 | 0.2-0.4 |`
PD line 1462: `| T5 | **TRD-CLI-CORE** | CLI: `ci-trading init`, `import`, `score`, `trust`, `conservation`. Click/Typer framework. | 2d | SDK | T2+T4 | Ready |`
PD line 1384: `| 1.8 | Full CLI (F8) | 0.5 | 1.1-1.5 |`
PD line 1477: `| T14 | **TRD-CLI-FULL** | Full CLI (F8): all commands + `export`, `backup`, `restore`. Man page. | 3d | SDK | T7-T11 | — |`

## CLI Entrypoint Help Output
```text
usage: ci-trading [-h] [--config-dir CONFIG_DIR]
                  {init,import,score,trust,conservation,journal,regime,correlation,vix-timing,promote,export,backup,restore,retag,order,orders,positions,account,sync,evolution}
                  ...

positional arguments:
  {init,import,score,trust,conservation,journal,regime,correlation,vix-timing,promote,export,backup,restore,retag,order,orders,positions,account,sync,evolution}
    init                Initialize local Trading CLI storage.
    import              Import trades from CSV.
    score               Compute offline factor scores.
    trust               Summarize factor computer coverage.
    conservation        Show an offline conservation proxy.
    journal             Show local imported trade journal.
    regime              Show current market regime and local regime accuracy.
    correlation         Monitor cross-position correlation concentration.
    vix-timing          Analyze hold periods across VIX conditions.
    promote             Show or evaluate strategy promotion tiers.
    export              Export local trades.
    backup              Back up local CLI state.
    restore             Restore local CLI state from backup.
    retag               Update a trade category.
    order               Place a broker order.
    orders              List broker orders.
    positions           List broker positions.
    account             Show broker account summary.
    sync                Sync filled broker orders to the local journal.
    evolution           Inspect Trading evolution variants.

options:
  -h, --help            show this help message and exit
  --config-dir CONFIG_DIR
```

## Command Coverage Matrix
Command | Scope | PD Requirement Summary | Function/Parser Found | Line | Reachable | Actual Behavior | Real Service/API | Stub/Hardcoded Signals | Verdict
init | P52 | creates ~/.ci-trading/ | `cmd_init`; parser `init` | apps/trading/backend/cli.py:206,951 | YES | Creates config and trades JSON store in config dir | PARTIAL | Local file setup only | PRESENT
connect | P52 | OAuth flow for Alpaca paper connection | none found | N/A | NO | No command implementation or parser entry | NO | Absent from help | ABSENT
import | P52 | import broker trades, including Alpaca `--broker alpaca --days 365` / last year | `cmd_import`; parser `import` | apps/trading/backend/cli.py:231,954 | YES | Imports CSV via CSVConnector or IBKR via IBKRConnector; unsupported broker otherwise | PARTIAL | Parser choices are csv/ibkr; PD Alpaca command unsupported | PARTIAL
score | P52 | score a trade or today's trades | `cmd_score`; parser `score` | apps/trading/backend/cli.py:271,961 | YES | Computes local factor summaries and prints "Offline factor scoring only; no decision recorded." | PARTIAL | Explicit offline-only message | PARTIAL
trust | P52 | show signal trust analysis / radar | `cmd_trust`; parser `trust` | apps/trading/backend/cli.py:310,965 | YES | Prints implemented/neutral factor coverage and variance for sample trades | PARTIAL | No `--show-radar`; no DK weights/radar output | PARTIAL
conservation | P52 | show strategy safety / strategy-specific conservation | `cmd_conservation`; parser `conservation` | apps/trading/backend/cli.py:336,968 | YES | Counts trades by category and prints GREEN/AMBER/RED proxy | PARTIAL | Prints "Offline conservation proxy" and "Full conservation requires the scoring server." | PARTIAL
patterns | P61 | show detected behavioral patterns with significance option | none found | N/A | NO | No command implementation or parser entry | NO | Absent from help | ABSENT
dashboard | P61 | opens local web UI | none found | N/A | NO | No command implementation or parser entry | NO | Absent from help | ABSENT
export | P61 | export all data CSV/JSON | `cmd_export`; parser `export` | apps/trading/backend/cli.py:698,998 | YES | Exports local trades to JSON or CSV | PARTIAL | Local trades only; not API full data export | PARTIAL
backup | P61 | backup centroids + weights | `cmd_backup`; parser `backup` | apps/trading/backend/cli.py:721,1003 | YES | Writes config and trades to local backup JSON | PARTIAL | No centroid/weight backup found | PARTIAL
restore | P61 | restore profile from backup | `cmd_restore`; parser `restore` | apps/trading/backend/cli.py:742,1006 | YES | Restores config/trades from local backup JSON | PARTIAL | Restores local state; no profile/centroid/weight restore evidence | PARTIAL

## P52 TRD-CLI-CORE Verdict
Verdict: SUPPLEMENT
Core commands:
- init: PRESENT
- connect: ABSENT
- import: PARTIAL
- score: PARTIAL
- trust: PARTIAL
- conservation: PARTIAL

Gaps:
- command: connect
- PD requirement: `ci-trading connect alpaca --paper        # OAuth flow`
- actual implementation: no `connect` parser or `cmd_connect` found; not shown by `python .\cli.py --help`.
- recommended supplement: add reachable `connect` command for Alpaca paper OAuth/config flow or explicitly reconcile PD if OAuth is out of scope.

- command: import
- PD requirement: `ci-trading import --broker alpaca --days 365`
- actual implementation: reachable parser only allows `--broker csv` or `--broker ibkr`; unsupported brokers print an error.
- recommended supplement: support Alpaca import path and PD-compatible default/arguments, or update product scope.

- command: score
- PD requirement: `ci-trading score --trade-id TRD-1847` and score today's trades.
- actual implementation: computes local factor tables/summaries and prints "Offline factor scoring only; no decision recorded."
- recommended supplement: wire scoring to the real decision scoring behavior/API or document this as an offline-only subset.

- command: trust
- PD requirement: signal trust analysis and `--show-radar`.
- actual implementation: summarizes factor implementation coverage and variance; no radar option or DK weight trust analysis is implemented.
- recommended supplement: add DK weight trust analysis output and `--show-radar` behavior.

- command: conservation
- PD requirement: strategy safety and `--strategy trend_following`.
- actual implementation: counts local trades per category and labels by thresholds; explicitly says full conservation requires server.
- recommended supplement: wire to ConservationMonitor/API and add strategy filtering.

## P61 TRD-CLI-FULL Verdict
Verdict: SUPPLEMENT
Full commands:
- patterns: ABSENT
- dashboard: ABSENT
- export: PARTIAL
- backup: PARTIAL
- restore: PARTIAL

Gaps:
- command: patterns
- PD requirement: `ci-trading patterns --min-significance 0.05`
- actual implementation: no `patterns` parser or command function found; absent from help.
- recommended supplement: add reachable behavioral pattern detection command with minimum significance option.

- command: dashboard
- PD requirement: `ci-trading dashboard                     # opens local web UI`
- actual implementation: no `dashboard` parser or command function found; absent from help.
- recommended supplement: add command that opens or starts the local web UI in the repo's expected dev/runtime mode.

- command: export
- PD requirement: export all data; API table says full data export CSV/JSON.
- actual implementation: exports only local `trades.json` records to CSV/JSON.
- recommended supplement: include full profile/trading data or route through the export service/API if that is the intended canonical behavior.

- command: backup
- PD requirement: backup centroids + weights.
- actual implementation: backs up config and trades only.
- recommended supplement: include centroids, weights, and any profile state required to satisfy PD restore semantics.

- command: restore
- PD requirement: restore profile.
- actual implementation: restores local config/trades only.
- recommended supplement: restore the full profile state backed up by the corrected backup command, including centroids and weights.

## Audit Limitations
- This audit does not run mutating CLI commands.
- This audit does not validate live broker/API connectivity.
- This audit does not run pytest.
- DROP CANDIDATE means source/help coverage appears complete, not that live CLI behavior has been E2E tested.

## Recommended Next Step
Write a targeted CLI supplement prompt.
