# VLD-TIER5 Implementation Summary

Implemented VLD-TIER5 in `copilot-sdk`.

Changed:

- `copilot_sdk/scoring/investigation.py`
  - Added `EpisodeSnapshot` with frozen centroids, sigma, K weights, factor/action names, geometry hash, conservation status, and timestamp.
  - Added faithful `contrast` computed from the original surface vector using the same geometry snapshot.
  - Added C4 halt reasons on trace steps: `budget_exhausted`, `residual_below_threshold`, `oscillation_detected`.
  - Empty reads remain recorded with `status="empty"`.
  - Residual halt now acts as a convergence guard after two acquired reads, so it does not prematurely stop wrong-first-step recovery.

- `copilot_sdk/backend/investigation_router.py`
  - Freezes centroid tensor at request start.
  - Uses `score_with_model_state(...)` when available so investigation scoring uses the production scorer path against the frozen snapshot.
  - Returns `snapshot` and `halt_reason`.
  - Preserves existing contrast keys while adding the faithful single-pass contrast under `single_pass`.

- `tests/test_investigation.py`
  - Added snapshot, contrast, residual halt, oscillation halt, and halt metadata tests.

Validation passed:

- `python -m pytest tests\test_investigation.py -q --timeout=120`  
  `52 passed`

- `python -m pytest tests\test_vld_integration.py -v --timeout=180`  
  `37 passed`

- `python -m pytest tests\ -q --timeout=120`  
  `3467 passed`

- `python -m pytest apps\trading\backend\tests\ -q --timeout=120`  
  `1335 passed`

- `python -m pytest apps\purchasing\backend\tests\ -q --timeout=120`  
  `741 passed, 1 skipped`

- `python -m pytest apps\dataops\backend\tests\ -q --timeout=120`  
  `386 passed`

Smoke checks passed for snapshot/contrast presence and residual early halt.

Final key hashes:

- `copilot_sdk/scoring/investigation.py`: `3441dcbdb67a93e231ceda9827db36b46413e5d2fd29e750e3310caf1a2df6b4`
- `copilot_sdk/backend/investigation_router.py`: `08f4df7ad872a6cf0dc53c0bd7250fe854ca7481e508aa592b35fe06440a744b`
- `copilot_sdk/scoring/scorer.py`: `24ac9e49a070e0f9421fa0e3e7417a828c0ec88610ef906ce4987311c721b460`

`scorer.py` was not modified. No `main.py`, preseed, evidence provider, database, SOC repo, or S2P repo files were modified.
