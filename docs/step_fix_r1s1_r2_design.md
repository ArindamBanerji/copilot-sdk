# FIX-R1S1-R2 design and verification refresh

Date: 2026-10-07. Design prepared before this refresh's code changes.

## Preconditions and scope

REV-R1S1 is completed with 0 P1, 4 P2, 0 P3 (session_state.md:6517, summary at 6670). Round 1 is recorded as PASS at the SCRIPTS FIXER entry. The October 3 FIX-R1S1-R2 entry at 6813 already records all four fixes, 92 additional cases, and successful verification; REV-R1S1-R2 at 6852 reports zero findings. Latest recorded SDK baseline: **4,407 passed, 1 xfailed, 0 failures**. These are existing tests, not tests added by this refresh.

The user confirmed on October 7 that all 13 pipeline steps were completed and missing Steps 1–4 entries are bookkeeping only, not dependencies. The user explicitly authorized this design, fresh verification, and the remaining HTTP diagnostic fix. The shared worktree contains prior uncommitted work, including the target files; preserve it. Target/protected files were snapshotted in `.codex_tmp/fix_r1s1_r2_refresh/`; no merge-conflict markers were found. Recheck hashes before edits and after verification to detect overlapping changes.

Read completely: scripts/demo_truth_preflight.py, tests/test_demo_truth_preflight.py, scripts/hero_moments.py. Historical buggy snippets below are from the preserved pre-R2 source `.codex_tmp/fix_r1s1_r2/demo_truth_preflight.py`, not falsely presented as current bugs. Existing fixes need verification, not duplication. The only proposed source change is diagnostic enrichment in PreflightClient.get. No hero, gauntlet, preseed, backend, dependency, or validation-policy changes.

## P2-1 — promotion records

Historical location: scripts/demo_truth_preflight.py:_has_artifact:181–183:

```python
if any(isinstance(item.get(key), list) and any(isinstance(row, dict) and bool(row) for row in item[key])
       for key in ("candidates", "promotions")):
    return True
```

Current corrected locations: `_promotion_record`:185–205 and `_has_promotion_artifact`:208–223. Keep the existing implementation:

```python
collections = [payload[key] for key in ("candidates", "promotions", "records") if key in payload]
if collections:
    return all(isinstance(rows, list) and bool(rows) and all(_promotion_record(row) for row in rows)
               for rows in collections)
```

Required fields verified against producers:

| Producer / response family | Required identifying fields and types |
| --- | --- |
| copilot_sdk/promotion/core.py:51–81, PromotionRecord.to_dict; Purchasing router promotion_state:64–66; DataOps dataops_governance.py:146–150 | Nonblank record_id, copilot, decision_class; current_stage in discovered/shadowing/promoted/measuring/kept/rolled_back/transferred |
| apps/trading/backend/app/services/promotion_engine.py:_evaluation_payload:222–243 | Nonblank category; current_stage in paper/small_live/full_live; boolean ready |
| Existing compact response compatibility | Boolean promoted/eligible; recognized stage; rule_id plus canonical status; candidate id plus finite numeric score |

The latter compact forms are compatibility contracts already covered by callers/tests, not a claim that each is a full shared PromotionRecord. Extra fields remain supported. No single copilot identity is hardcoded into shared record validation. Empty/error/unrelated or mixed malformed collections remain rejected.

Tests: existing positive real-record and Trading dashboard cases; empty dictionaries/collections; missing or mistyped fields; extras from actual producer records. Add shared-record integration regression for each of all five copilot identities, using PromotionRecord.to_dict (5 cases); no redundant replacement of the existing malformed matrices.

## P2-2 — Purchasing schemas

Historical locations: `_has_artifact`:161–183 (twin/promotion branches); configured routes at SPECS:55–58. The promotion branch above did not recognize records. Historical twin condition:

```python
if (has_id and has_comparison) or has_status:
    return True
```

Corrected current code: `_purchasing_twin_status`:226–238; `_has_artifact`:270–277:

```python
if (has_id and has_comparison) or has_status or _purchasing_twin_status(item):
    return True
```

Keep this additive alternative and the records collection validation from P2-1. Actual Purchasing router `promotion_state` returns `{"records": [record.to_dict(), ...], "observation_only": True}`. Router `frozen_twin`:39–41 calls `PurchasingControlService.frozen_status`:281–288, returning available=True, status=FROZEN, snapshot_time, checksum, evidence_tier and paired learning_curve/frozen_curve lists. `_twin_curves`:290 onward emits finite cumulative accuracy points in [0,1]; both curves may be empty immediately after freeze. NOT_INITIALIZED is explicitly unavailable and must not pass this alternative.

Existing validator requires true available, exact FROZEN status, nonblank checksum, nonblank timestamp or finite nonnegative numeric timestamp (not bool), equally sized lists of dictionaries with finite accuracy in [0,1]. Existing Trading/DataOps twin alternatives remain intact. Accepting this verified real schema is a correction, not permission for empty/unrelated/error envelopes.

Tests: retain Purchasing records and real service frozen-status builder tests, malformed-field matrix and empty-paired-curves case; retain Trading/DataOps regression tests. Add the all-copilot shared-record test described above, including actual DataOps record shape. No source changes needed.

## P2-3 — fallback and HTTP diagnostics

Historical locations: `PreflightClient.get`:69–76 and `_first_available`:79–86; metric loop in `check_copilot`:216–220:

```python
except (error.HTTPError, error.URLError, TimeoutError, json.JSONDecodeError) as exc:
    raise RuntimeError(str(exc)) from exc
# Alias loop:
except RuntimeError:
    continue
```

Already corrected: `_first_available`:99–106 allows only classified HTTP 404/405. `check_copilot.probe`:292–302 records all other errors, and metric probing:319–328 uses the same restriction. Hero ApiClient.first/first_post:81–97 already use only 404/405; no hero change required.

Remaining current gap: `PreflightClient.get`:86–87 reports only path/status/reason:

```python
except error.HTTPError as exc:
    raise PreflightApiError(path, "http_error", f"HTTP {exc.code} {exc.reason}", exc.code) from exc
```

Proposed replacement:

```python
except error.HTTPError as exc:
    try:
        raw = exc.read(513)
        snippet = raw[:512].decode("utf-8", errors="replace")
        if len(raw) > 512:
            snippet += "... [truncated]"
        body_detail = repr(snippet) if snippet else "<empty>"
    except (OSError, HTTPException, ValueError) as body_error:
        body_detail = f"<unavailable: {type(body_error).__name__}: {body_error}>"
    finally:
        try:
            exc.close()
        except (OSError, HTTPException) as close_error:
            body_detail += f"; close failed: {type(close_error).__name__}: {close_error}"
    detail = f"HTTP {exc.code} {exc.reason}; body={body_detail}"
    raise PreflightApiError(req.full_url, "http_error", detail, exc.code) from exc
```

Also pass req.full_url instead of path in the existing transport/invalid-response exception branches. Preserve classification, status and exception chaining. Reading/decoding the diagnostic body must never turn 503 into a timeout or enable fallback. Reading at most 513 bytes bounds the snippet at 512 bytes and detects truncation; repr escapes line breaks/control characters. Invalid UTF-8 uses replacement. Empty or unreadable bodies remain explicit. The original HTTP status takes priority even when diagnostic body reading fails. Standard urllib HTTPError owns the response stream and is closed afterward.

Example preflight failure: `trading: claim registry request failed [http_error]: GET http://127.0.0.1:8010/api/trading/claims: http_error: HTTP 503 Service Unavailable; body='{"detail":"backend starting"}'`.

Callers: gauntlet executes preflight as a subprocess, records its output/status; CLI prints failures and exits 1. Existing direct helpers receive classified exceptions. No searched caller parses the old error string as a contract. Trading/DataOps valid responses never enter these exception branches. HTTP 404/405 may read diagnostic bodies but still trigger the same fallback. Startup 503 could justify retrying the same endpoint in an explicit readiness orchestration, but preflight has no such retry policy: report it and allow a later preflight rerun; never switch aliases to hide it.

Tests: retain all existing 404/405, all-surface 503, timeout, connection, malformed-response and CLI failure regressions. Add 503 status + full URL + body through check_copilot; bounded read/truncation; empty body; invalid UTF-8; body-read timeout/OSError/HTTPException (3 cases); full URL on transport timeout; response-close failure retaining the HTTP status. These are 9 new diagnostic cases.

## P2-4 — list metric scanning

Historical location: `_check_no_sample`:123–129:

```python
if not isinstance(payload, (dict, list)):
    return
if scan_for_sample is not None and isinstance(payload, dict):
    findings = scan_for_sample(payload)
```

Current corrected location: `_check_no_sample`:142–173. Keep the shared recursion:

```python
if isinstance(payload, list):
    for index, item in enumerate(payload):
        item_path = f"{path}[{index}]"
        if isinstance(item, dict):
            _check_no_sample(name, item_path, item, failures)
        else:
            print(f"WARNING: {name} {item_path}: unexpected metric response shape "
                  f"{type(item).__name__}; expected a dictionary element", file=sys.stderr)
            if isinstance(item, list):
                _check_no_sample(name, item_path, item, failures)
    return
```

The same function scans single dicts and list dicts; F-26 is not reimplemented. F-27 remains active. Empty list: no dicts to scan, no warning. Nested lists: warning and recursion, preserving both scanners and index paths. All non-dict entries warn; following dictionaries still scanned. Scalar top-level payloads warn without converting warnings to new failures.

Tests: keep all existing dict/list/mixed/scalar/nested-list tests. Add empty list, all-non-dict list, and invalid element *before* valid sampled dict (3 cases). Total refresh additions: **17 cases** (5 promotion identity, 9 diagnostic, 3 list edges). The original 92 R2 cases remain unchanged.

## Verification plan

1. Read this design and append design review before implementation.
2. No-op preservation for P2-1/P2-2/P2-4; edit P2-3 diagnostics, immediately run `python -m mypy scripts/demo_truth_preflight.py --config-file pyproject.toml`.
3. Append tests only to tests/test_demo_truth_preflight.py; immediately run its configured mypy.
4. `python -m pytest tests/test_demo_truth_preflight.py -v --timeout=120` (expected 173 passed).
5. `python -m pytest tests/ -q --timeout=120` (expected 4,424 passed, 1 xfailed if shared baseline unchanged).
6. Final individual mypy; protected source hash checks and pre-existing test AST comparison; scoped whitespace check.
7. No run_preflight callable exists: requested function-based D.4 is SKIP. Also run the existing CLI dry-run for Trading and DataOps (configuration only) and actual check_copilot contract tests (mocked HTTP; not a claim of live backend availability).
8. Append measured results to session_state.md, attributing only new tests to this refresh.

## DESIGN REVIEW

Reviewed 2026-10-07, before implementation. Findings and resolutions:

- Scope: four P2 behavioral fixes already exist and have regression coverage. Reapplying them would add unnecessary changes. Preserve them; enrich only P2-3 diagnostics. No changes to hero_moments.py, loom_gauntlet.py or preseed_hero_scenarios.py.
- Validation: no predicate or accepted response family changes in this refresh. Purchasing acceptance was verified against router and service construction; Trading dashboard and DataOps shared PromotionRecord have distinct supported shapes. Neither is replaced by a Purchasing-only schema. The all-copilot record test checks compatibility, not whether each live route emits that same envelope.
- HTTP body reads and close may themselves fail. Revised the proposed code above to retain original HTTP status/classification on both failures. Added a close-failure regression (17 total additions). This also preserves 404/405 alias behavior when diagnostic reading fails. Decoding invalid bytes does not conceal the status.
- Timeout without HTTP response has no status/body to report; report full request URL and timeout classification. Startup retries are outside this read-only preflight; a startup 503 remains an explicit failed check.
- List scanning uses the identical dict-scanning path and retains nested F-27 semantics. Added missing edge assertions without changing warning/failure policy.
- No `run_preflight` API exists. Record that exact requested smoke as SKIP; CLI configuration smoke and existing Trading/DataOps check_copilot contract tests remain useful separate checks.
- Location corrections after exact line lookup: current `_check_no_sample` begins at 143; `_purchasing_twin_status` at 225; `_has_artifact` at 239; Trading `_evaluation_payload` at 220. All line references describe the pre-refresh source; diagnostics will shift following lines.

Review outcome: ready to implement the scoped diagnostic change. No unresolved design findings.

Implementation verification refinement: the first focused run exposed an existing fixture that raises the same HTTPError twice (trajectory is also a metric route). Its response stream is already closed on the second read, raising ValueError. Treat that body-read failure as unavailable diagnostics while retaining the original HTTP status, exactly as for socket/body-read failures. Added ValueError to the narrow diagnostic-read exception tuple above; existing tests remain unchanged. First focused result: 172 passed, 1 failed; rerun required after this correction.

## Verification results

- Final focused suite: **173 passed**, including 17 added parameter cases across 11 new test functions. All 57 pre-existing function/class definitions are AST-identical to the pre-refresh snapshot.
- Both changed Python files pass configured mypy. Existing CLI dry-run for Trading and DataOps passes; targeted contract regressions pass. The nonexistent `run_preflight(..., dry_run=True)` API check is skipped as instructed.
- First full SDK attempt used the requested `--timeout=120` and was terminated by pytest-timeout in unchanged `tests/integrity/test_counterfactual.py::test_dk_weights_change_scoring_sensitivity`. No functional failure preceded it. Source hashes confirmed no concurrent scorer, memory-store, or test edits; session history already notes this slow-test risk. An isolated retry at the same 120-second limit passed in 66.27 seconds (66.89 seconds total). Full suite rerun uses the same command and unchanged sources; no timeout relaxation or assertion changes.
- Final full-suite rerun: **4,424 passed, 1 xfailed, 0 failures, 0 errors, 0 skipped**, 8,976 warnings, exit 0 in 2,176.19 seconds (36:16), using `python -m pytest tests/ -q --timeout=120`. Baseline 4,407 -> 4,424 passed; exactly 17 additional cases. The existing module-specific slow-test timeout markers were left unchanged.
- Final individual mypy: PASS for both changed Python files. Scoped `git diff --check`: PASS (only normal LF/CRLF notices). Tested source hashes stayed unchanged through the full suite; all three protected scripts are byte-identical to the pre-refresh snapshots. Hash comparison across 1,277 Python files found no unrelated source edits; 1,642 snapshotted tracked app/demo data files are unchanged. Other work appended session-state documentation during verification; those entries are preserved.
- Evidence: `.codex_tmp/fix_r1s1_r2_refresh/targeted_final.log`, `sdk_full.log` (initial timeout), `timeout_recheck.log`, `sdk_full_retry.log` (final passing gate), `tested_hashes.json`, `final_preservation.json`, and `refresh.diff`.
