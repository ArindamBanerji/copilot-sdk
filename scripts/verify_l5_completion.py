"""L5 completion proof script.

Verifies that L5 persistence cells exist and carry valid values in AGE.

Cell breakdown from the DK runtime plan:
  C9A: 12 cells - centroids and conservation state
  C9B: 3 cells - DK weights for variance-learning categories
  Total: 15 cells

Usage:
  python scripts/verify_l5_completion.py
  python scripts/verify_l5_completion.py --dsn "host=localhost port=5433 ... sslmode=disable"
  python scripts/verify_l5_completion.py --json
"""

from __future__ import annotations

import argparse
import json
import sys
import warnings
from datetime import datetime
from typing import Any

DEFAULT_DSN = "host=localhost port=5433 dbname=soc_copilot user=postgres password=postgres sslmode=disable"
GRAPH_NAME = "soc_graph"
L5_LABELS = ("L5Centroid", "L5DKWeight", "L5ConservationState")


def _agtype_to_python(value: Any) -> Any:
    """Best-effort conversion for psycopg AGE scalar/property values."""
    if value is None or isinstance(value, (dict, list, int, float, bool)):
        return value
    text = str(value).strip()
    if not text:
        return None
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return text.strip('"')


def _jsonish_to_python(value: Any) -> Any:
    """Parse values that may already be Python values or JSON strings."""
    value = _agtype_to_python(value)
    if isinstance(value, str):
        stripped = value.strip()
        if stripped.startswith(("[", "{")):
            try:
                return json.loads(stripped)
            except json.JSONDecodeError:
                return value
    return value


def _flatten_numbers(value: Any) -> list[float]:
    """Collect numeric values from nested JSON arrays/dicts."""
    value = _jsonish_to_python(value)
    if isinstance(value, bool):
        return []
    if isinstance(value, (int, float)):
        return [float(value)]
    if isinstance(value, list):
        numbers: list[float] = []
        for item in value:
            numbers.extend(_flatten_numbers(item))
        return numbers
    if isinstance(value, dict):
        numbers = []
        for item in value.values():
            numbers.extend(_flatten_numbers(item))
        return numbers
    return []


def _timestamp_from_props(props: dict[str, Any]) -> float | None:
    for key in ("timestamp_epoch", "updated_at_epoch", "computed_at", "created_at"):
        value = props.get(key)
        if value is not None:
            try:
                return float(value)
            except (TypeError, ValueError):
                pass
    updated_at = props.get("updated_at")
    if isinstance(updated_at, str):
        try:
            return datetime.fromisoformat(updated_at.replace("Z", "+00:00")).timestamp()
        except ValueError:
            return None
    return None


class L5CompletionProof:
    """Verify all expected L5 completion cells exist and are valid."""

    def __init__(self, dsn: str = DEFAULT_DSN):
        if dsn == DEFAULT_DSN:
            warnings.warn(
                "No DSN supplied - using localhost fallback. "
                "Set --dsn with WSL2 NAT IP per Rule #40.",
                stacklevel=2,
            )
        self.dsn = dsn
        self._conn: Any | None = None

    def connect(self) -> None:
        """Connect to PostgreSQL+AGE. Raises on failure."""
        import psycopg

        self._conn = psycopg.connect(self.dsn, autocommit=True, connect_timeout=5)
        self._conn.execute("LOAD 'age'")
        self._conn.execute("SET search_path = ag_catalog, '$user', public")

    def close(self) -> None:
        if self._conn:
            self._conn.close()

    def verify(self) -> dict[str, Any]:
        """Run full verification and return a proof dictionary."""
        results: dict[str, Any] = {
            "total_expected": 15,
            "l5_centroids": self._verify_centroids(),
            "l5_dk_weights": self._verify_dk_weights(),
            "l5_conservation": self._verify_conservation(),
            "l5_edges": self._verify_edges(),
            "l5_welford": self._verify_welford_fields(),
            "l5_timestamps": self._verify_timestamp_ordering(),
        }

        total_found = (
            results["l5_centroids"]["count"]
            + results["l5_dk_weights"]["count"]
            + results["l5_conservation"]["count"]
        )
        results["total_found"] = total_found
        results["complete"] = total_found >= results["total_expected"]

        missing: list[str] = []
        invalid: list[str] = []
        for section in ("l5_centroids", "l5_dk_weights", "l5_conservation"):
            missing.extend(results[section].get("missing", []))
            invalid.extend(results[section].get("invalid", []))

        if not results["l5_edges"]["all_linked"]:
            invalid.append("Some L5 nodes lack provenance edges")
        if not results["l5_welford"]["all_valid"]:
            invalid.append("Some L5DKWeight nodes lack Welford fields")
        if not results["l5_timestamps"]["sequential"]:
            invalid.append("L5 timestamps are out of order")

        results["missing_cells"] = missing
        results["invalid_cells"] = invalid

        if invalid:
            results["proof_status"] = "INVALID"
        elif missing or total_found < results["total_expected"]:
            results["proof_status"] = "INCOMPLETE"
        else:
            results["proof_status"] = "COMPLETE"
        return results

    def _fetchone(self, query: str) -> Any:
        return self._conn.execute(query).fetchone()

    def _fetchall(self, query: str) -> list[Any]:
        return list(self._conn.execute(query).fetchall())

    def _count_label(self, label: str) -> int:
        row = self._fetchone(
            f"""SELECT * FROM cypher('{GRAPH_NAME}', $$
               MATCH (n:{label}) RETURN count(n)
            $$) AS (cnt agtype)"""
        )
        return int(str(row[0])) if row else 0

    def _props_for_label(self, label: str, order_by: str | None = None) -> list[dict[str, Any]]:
        order_clause = f"ORDER BY n.{order_by}" if order_by else ""
        rows = self._fetchall(
            f"""SELECT * FROM cypher('{GRAPH_NAME}', $$
               MATCH (n:{label}) RETURN properties(n) {order_clause}
            $$) AS (props agtype)"""
        )
        props: list[dict[str, Any]] = []
        for row in rows:
            parsed = _agtype_to_python(row[0])
            if isinstance(parsed, dict):
                props.append(parsed)
        return props

    def _verify_centroids(self) -> dict[str, Any]:
        count = self._count_label("L5Centroid")
        invalid: list[str] = []
        for props in self._props_for_label("L5Centroid"):
            values = []
            for key in ("vector_json", "centroid_json", "centroid", "centroid_vector"):
                if key in props:
                    values.extend(_flatten_numbers(props[key]))
            for key, val in props.items():
                if key.startswith("centroid_"):
                    values.extend(_flatten_numbers(val))
            for value in values:
                if value < 0.0 or value > 1.0:
                    invalid.append(
                        f"L5Centroid {props.get('category', '?')}: value={value}"
                    )

        return {
            "count": count,
            "expected": ">=6 (one per category minimum)",
            "valid_range": not invalid,
            "invalid": invalid,
            "missing": [],
        }

    def _verify_dk_weights(self) -> dict[str, Any]:
        count = self._count_label("L5DKWeight")
        invalid: list[str] = []
        for props in self._props_for_label("L5DKWeight"):
            values = []
            for key in ("weight_json", "weights_json", "weights", "weight"):
                if key in props:
                    values.extend(_flatten_numbers(props[key]))
            for key, val in props.items():
                if key.startswith("weight_"):
                    values.extend(_flatten_numbers(val))
            for value in values:
                if value < 0.0 or value > 1.0:
                    invalid.append(
                        f"L5DKWeight {props.get('category', props.get('domain', '?'))}: value={value}"
                    )

        missing = []
        if count < 3:
            missing.append(f"L5DKWeight: found {count}, expected >=3 (C9B)")

        return {
            "count": count,
            "expected": ">=3 (C9B: categories past VARIANCE_LEARNING)",
            "valid_range": not invalid,
            "invalid": invalid,
            "missing": missing,
        }

    def _verify_conservation(self) -> dict[str, Any]:
        count = self._count_label("L5ConservationState")
        invalid: list[str] = []
        for props in self._props_for_label("L5ConservationState"):
            alpha = props.get("alpha")
            volume = props.get("v", props.get("V"))
            if alpha is not None and (float(alpha) <= 0.0 or float(alpha) > 1.0):
                invalid.append(f"Conservation alpha={alpha} out of (0,1]")
            if volume is not None and float(volume) <= 0.0:
                invalid.append(f"Conservation V={volume} not positive")

        return {
            "count": count,
            "expected": ">=1",
            "valid_range": not invalid,
            "invalid": invalid,
            "missing": [],
        }

    def _verify_edges(self) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for rel in ("SHAPED_BY", "TRIGGERED_BY"):
            row = self._fetchone(
                f"""SELECT * FROM cypher('{GRAPH_NAME}', $$
                    MATCH ()-[r:{rel}]->() RETURN count(r)
                $$) AS (cnt agtype)"""
            )
            result[rel] = int(str(row[0])) if row else 0
        result["all_linked"] = all(int(result[rel]) > 0 for rel in ("SHAPED_BY", "TRIGGERED_BY"))
        return result

    def _verify_welford_fields(self) -> dict[str, Any]:
        missing_welford: list[str] = []
        for props in self._props_for_label("L5DKWeight"):
            has_mean = any(k in props for k in ("mean", "all_mean_json", "confirmed_mean_json"))
            has_m2 = any(k in props for k in ("M2", "m2", "all_m2_json", "confirmed_m2_json"))
            has_count = any(k in props for k in ("count", "n_decisions_used", "n_confirmed"))
            missing = []
            if not has_mean:
                missing.append("mean")
            if not has_m2:
                missing.append("M2")
            if not has_count:
                missing.append("count")
            if missing:
                missing_welford.append(
                    f"{props.get('category', props.get('domain', 'unknown'))}: missing {sorted(missing)}"
                )

        return {
            "total_checked": len(self._props_for_label("L5DKWeight")),
            "missing_welford": missing_welford,
            "all_valid": not missing_welford,
        }

    def _verify_timestamp_ordering(self) -> dict[str, Any]:
        timestamps_by_label: dict[str, list[float]] = {}
        order_fields = {
            "L5Centroid": "updated_at_epoch",
            "L5DKWeight": "computed_at",
            "L5ConservationState": "updated_at",
        }
        for label in L5_LABELS:
            timestamps: list[float] = []
            for props in self._props_for_label(label, order_by=order_fields[label]):
                timestamp = _timestamp_from_props(props)
                if timestamp is not None:
                    timestamps.append(timestamp)
            timestamps_by_label[label] = timestamps
        sequential = all(
            values[i] <= values[i + 1]
            for values in timestamps_by_label.values()
            for i in range(len(values) - 1)
        )
        return {
            "total_timestamps": sum(len(values) for values in timestamps_by_label.values()),
            "sequential": sequential,
        }


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="L5 Completion Proof")
    parser.add_argument("--dsn", default=DEFAULT_DSN)
    parser.add_argument("--json", action="store_true", help="Machine-readable output")
    args = parser.parse_args(argv)

    proof = L5CompletionProof(dsn=args.dsn)
    try:
        proof.connect()
    except Exception as exc:
        payload = {"error": str(exc), "proof_status": "AGE_UNAVAILABLE"}
        if args.json:
            print(json.dumps(payload))
        else:
            print(f"Cannot connect to AGE: {exc}")
            print("Ensure PostgreSQL+AGE is running on port 5433.")
        raise SystemExit(1)

    try:
        result = proof.verify()
    finally:
        proof.close()

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print("L5 Completion Proof")
        print(f"  Status: {result['proof_status']}")
        print(f"  Cells: {result['total_found']}/{result['total_expected']}")
        print(f"  Centroids: {result['l5_centroids']['count']}")
        print(f"  DK Weights: {result['l5_dk_weights']['count']}")
        print(f"  Conservation: {result['l5_conservation']['count']}")
        print(
            "  Edges: "
            f"SHAPED_BY={result['l5_edges'].get('SHAPED_BY', 0)}, "
            f"TRIGGERED_BY={result['l5_edges'].get('TRIGGERED_BY', 0)}"
        )
        print(f"  Welford: {'PASS' if result['l5_welford']['all_valid'] else 'ISSUES'}")
        print(
            "  Timestamps: "
            f"{'sequential' if result['l5_timestamps']['sequential'] else 'OUT OF ORDER'}"
        )
        if result["missing_cells"]:
            print(f"  Missing: {result['missing_cells']}")
        if result["invalid_cells"]:
            print(f"  Invalid: {result['invalid_cells']}")

    raise SystemExit(0 if result["proof_status"] == "COMPLETE" else 1)


if __name__ == "__main__":
    main()
