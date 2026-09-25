"""Export real scorer snapshots to stdout; never write a production store.

Run: python tests/extract_real_centroids.py > real_centroids_v1.json

mu is the first category slice, explicitly labelled mu_category. Every category
is exported in all_category_mu. Consumers MUST select the scenario's category.
SOC's offline bootstrap and all unit-sigma fallbacks are labelled in provenance;
this file must not be represented as an export of live, learned AGE state.
"""

from datetime import datetime, timezone
import json
import sys

from vld_validation_report import collect_all


def build_export():
    results = collect_all()
    errors = {name: row["error"] for name, row in results.items() if row["error"]}
    payload = {"extracted_at": datetime.now(timezone.utc).isoformat(),
               "scope": "offline real CompoundingScorer: local checkpoint snapshots or labelled bootstrap",
               "live_age_validated": False, "complete": not errors,
               "errors": errors, "copilots": {}, "scenarios": {}}
    for name, result in results.items():
        if result["error"]:
            payload["copilots"][name] = {"error": result["error"]}
            payload["scenarios"][name] = {}
            continue
        payload["copilots"][name] = {key: result[key] for key in (
            "mu", "mu_category", "all_category_mu", "sigma", "factor_names", "action_names",
            "category_names", "n_actions", "n_factors", "tau", "tensor_shape",
            "pre_restore_hash", "post_restore_hash", "l5_rows_total", "l5_rows_applied",
            "provenance")}
        payload["scenarios"][name] = {
            row["scenario"]: {key: row[key] for key in (
                "category", "factor_vector", "claimed_surface_action", "claimed_vld_action",
                "evidence_dims", "evidence", "surface_action", "final_action", "surface_margin",
                "final_margin", "source", "provider_source")}
            for row in result["scenarios"]}
    return payload


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    export = build_export()
    print(json.dumps(export, indent=2, allow_nan=False))
    if export["errors"]:
        print("P0 WIRING: incomplete centroid export; inspect errors field", file=sys.stderr)
        raise SystemExit(1)
