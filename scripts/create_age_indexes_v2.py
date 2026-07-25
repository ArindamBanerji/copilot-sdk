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

    # Load AGE extension — required for agtype operations
    cur.execute("LOAD 'age'")
    cur.execute('SET search_path = ag_catalog, "$user", public')

    table = f'{schema}."Decision"'

    # Discover column type
    cur.execute(
        "SELECT column_name, data_type, udt_name FROM information_schema.columns "
        "WHERE table_schema = %s AND table_name = %s ORDER BY ordinal_position",
        (schema, "Decision"),
    )
    columns = cur.fetchall()
    print(f"Decision columns in {schema}:")
    for col_name, col_type, udt_name in columns:
        print(f"  {col_name}: {col_type} ({udt_name})")

    print(f"\nCreating indexes on {table}...")

    # AGE properties are agtype. Three strategies to try:
    # 1. Cast to jsonb then extract (most compatible)
    # 2. agtype_access_operator with LOAD 'age' (AGE-native)
    # 3. Direct -> operator on agtype

    strategies = [
        ("jsonb cast", {
            "decision_domain_idx": f"((properties::jsonb->>'domain'))",
            "decision_archived_idx": f"((properties::jsonb->>'archived'))",
        }),
        ("agtype accessor", {
            "decision_domain_idx": f"(ag_catalog.agtype_access_operator(properties, '\"domain\"'::ag_catalog.agtype))",
            "decision_archived_idx": f"(ag_catalog.agtype_access_operator(properties, '\"archived\"'::ag_catalog.agtype))",
        }),
        ("direct arrow", {
            "decision_domain_idx": f"((properties->'domain'))",
            "decision_archived_idx": f"((properties->'archived'))",
        }),
    ]

    created = False
    for strategy_name, indexes in strategies:
        print(f"\n  Trying strategy: {strategy_name}")
        all_ok = True
        for idx_name, expr in indexes.items():
            try:
                cur.execute(f"CREATE INDEX IF NOT EXISTS {idx_name} ON {table} {expr}")
                print(f"    {idx_name}: created")
            except Exception as e:
                print(f"    {idx_name}: FAILED — {e}")
                all_ok = False
                break
        if all_ok:
            created = True
            print(f"  Strategy '{strategy_name}' succeeded.")
            break
        else:
            # Drop any partial indexes from this strategy before trying next
            for idx_name in indexes:
                try:
                    cur.execute(f"DROP INDEX IF EXISTS {schema}.{idx_name}")
                except Exception:
                    pass

    if not created:
        print("\n  ERROR: all index strategies failed.")
        print("  Manual investigation required.")

    # Verify
    cur.execute(
        "SELECT indexname, indexdef FROM pg_indexes WHERE schemaname = %s AND tablename = %s",
        (schema, "Decision"),
    )
    print("\nDecision indexes:")
    for name, defn in cur.fetchall():
        print(f"  {name}: {defn[:120]}")

    conn.close()
    print("\nDone.")


if __name__ == "__main__":
    main()
