"""Create AGE indexes on Decision.domain and Decision.archived.

Usage:
    python scripts/create_age_indexes.py
"""
import os

import psycopg2


def main():
    dsn = os.environ.get("GRAPH_DSN", "host=localhost port=5433 dbname=soc_copilot user=postgres password=postgres")
    schema = os.environ.get("GRAPH_NAME", "soc_graph")

    try:
        conn = psycopg2.connect(dsn)
    except Exception as e:
        print(f"ERROR: cannot connect — {e}")
        return

    conn.autocommit = True
    cur = conn.cursor()

    table = f'{schema}."Decision"'

    # Discover column type
    cur.execute(
        "SELECT column_name, data_type FROM information_schema.columns "
        "WHERE table_schema = %s AND table_name = %s ORDER BY ordinal_position",
        (schema, "Decision"),
    )
    columns = cur.fetchall()
    print(f"Decision columns in {schema}:")
    for col_name, col_type in columns:
        print(f"  {col_name}: {col_type}")

    # AGE uses 'properties' column of type 'agtype'
    prop_col = next((c for c, t in columns if c == "properties"), None)
    if not prop_col:
        print("ERROR: no 'properties' column found on Decision table")
        conn.close()
        return

    print(f"\nCreating indexes on {table}...")

    for idx_name, expr in [
        ("decision_domain_idx", "ag_catalog.agtype_access_operator(properties, '\"domain\"'::agtype)"),
        ("decision_archived_idx", "ag_catalog.agtype_access_operator(properties, '\"archived\"'::agtype)"),
    ]:
        try:
            cur.execute(
                f"CREATE INDEX IF NOT EXISTS {idx_name} ON {table} (({expr}))"
            )
            print(f"  {idx_name}: created")
        except Exception as e:
            print(f"  {idx_name}: FAILED — {e}")
            # Try jsonb-style fallback
            fallback_expr = expr.replace("ag_catalog.agtype_access_operator(properties, '\"", "properties->'").rstrip("'::agtype)") + "')"
            print(f"  Trying fallback: {fallback_expr}")
            try:
                conn.rollback() if not conn.autocommit else None
                cur.execute(
                    f"CREATE INDEX IF NOT EXISTS {idx_name} ON {table} (({fallback_expr}))"
                )
                print(f"  {idx_name}: created (fallback)")
            except Exception as e2:
                print(f"  {idx_name}: fallback also FAILED — {e2}")

    # Verify
    cur.execute(
        "SELECT indexname, indexdef FROM pg_indexes WHERE schemaname = %s AND tablename = %s",
        (schema, "Decision"),
    )
    print("\nDecision indexes:")
    for name, defn in cur.fetchall():
        print(f"  {name}")

    conn.close()
    print("\nDone.")


if __name__ == "__main__":
    main()
