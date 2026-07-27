"""Verify the ag_label fix: find the correct way to get the graph OID
and query vertex/edge labels.

The inventory script's query used 'graphid' which doesn't exist.
This tries: oid, each named column, and direct OID from raw data.
"""
import psycopg

DSN = "host=localhost port=5433 dbname=soc_copilot user=postgres password=postgres"


def main():
    conn = psycopg.connect(DSN)
    conn.autocommit = True
    conn.execute("LOAD 'age'")
    conn.execute('SET search_path = ag_catalog, "$user", public')

    # ================================================================
    # 1. Discover ag_graph column names
    # ================================================================
    print("=== ag_graph columns ===")
    try:
        graph_cols = conn.execute("""
            SELECT a.attname, t.typname
            FROM pg_attribute a
            JOIN pg_class c ON a.attrelid = c.oid
            JOIN pg_namespace n ON c.relnamespace = n.oid
            JOIN pg_type t ON a.atttypid = t.oid
            WHERE n.nspname = 'ag_catalog' AND c.relname = 'ag_graph'
            AND a.attnum > 0 AND NOT a.attisdropped
            ORDER BY a.attnum
        """).fetchall()
        graph_col_names = [r[0] for r in graph_cols]
        for r in graph_cols:
            print(f"  {r[0]} ({r[1]})")
        print(f"  Column names: {graph_col_names}")
    except Exception as e:
        print(f"  Error: {e}")
        graph_col_names = []

    # ================================================================
    # 2. Try every approach to get the graph OID
    # ================================================================
    print("\n=== Finding soc_graph OID ===")
    graph_oid = None

    # 2a. Try system oid column
    try:
        rows = conn.execute("SELECT oid FROM ag_graph WHERE name = 'soc_graph'").fetchall()
        if rows:
            graph_oid = rows[0][0]
            print(f"  2a. SELECT oid: {graph_oid}")
    except Exception as e:
        print(f"  2a. SELECT oid failed: {e}")

    # 2b. Try each named column that could be an OID
    if graph_oid is None:
        for col in graph_col_names:
            try:
                rows = conn.execute(
                    f"SELECT {col} FROM ag_graph WHERE name = 'soc_graph'"
                ).fetchall()
                if rows:
                    val = rows[0][0]
                    print(f"  2b. SELECT {col}: {val} (type: {type(val).__name__})")
                    if isinstance(val, int) and val > 0:
                        graph_oid = val
                        print(f"  >>> Using {col} = {val} as graph OID")
                        break
            except Exception as e:
                print(f"  2b. SELECT {col} failed: {e}")

    # 2c. Try raw first column from SELECT *
    if graph_oid is None:
        try:
            rows = conn.execute("SELECT * FROM ag_graph WHERE name = 'soc_graph'").fetchall()
            if rows:
                print(f"  2c. Raw row: {rows[0]}")
                # First column is typically the OID
                graph_oid = rows[0][0]
                print(f"  >>> Using first column = {graph_oid} as graph OID")
        except Exception as e:
            print(f"  2c. SELECT * failed: {e}")

    if graph_oid is None:
        print("  FATAL: Cannot determine graph OID")
        conn.close()
        return

    print(f"\n  Graph OID resolved: {graph_oid}")

    # ================================================================
    # 3. Query ag_label with the resolved OID
    # ================================================================

    # 3a. Without kind filter first (isolate which filter causes 0 results)
    print(f"\n=== ag_label WHERE graph = {graph_oid} (no kind filter) ===")
    try:
        rows = conn.execute(f"""
            SELECT name FROM ag_label
            WHERE graph = {graph_oid}
            AND name NOT LIKE '_%'
            ORDER BY name
        """).fetchall()
        print(f"  Labels found: {len(rows)}")
        for r in rows[:10]:
            print(f"    {r[0]}")
        if len(rows) > 10:
            print(f"    ... and {len(rows) - 10} more")
    except Exception as e:
        print(f"  Error: {e}")

    # 3b. With kind = 'v' (vertex)
    print(f"\n=== ag_label WHERE graph = {graph_oid} AND kind = 'v' ===")
    try:
        rows = conn.execute(f"""
            SELECT name FROM ag_label
            WHERE graph = {graph_oid}
            AND kind = 'v'
            AND name NOT LIKE '_%'
            ORDER BY name
        """).fetchall()
        print(f"  Vertex labels: {len(rows)}")
        for r in rows:
            print(f"    {r[0]}")
    except Exception as e:
        print(f"  Error with kind='v': {e}")
        # Try with cast
        try:
            rows = conn.execute(f"""
                SELECT name FROM ag_label
                WHERE graph = {graph_oid}
                AND kind::text = 'v'
                AND name NOT LIKE '_%'
                ORDER BY name
            """).fetchall()
            print(f"  Vertex labels (with cast): {len(rows)}")
            for r in rows:
                print(f"    {r[0]}")
        except Exception as e2:
            print(f"  Error with cast: {e2}")

    # 3c. With kind = 'e' (edge)
    print(f"\n=== ag_label WHERE graph = {graph_oid} AND kind = 'e' ===")
    try:
        rows = conn.execute(f"""
            SELECT name FROM ag_label
            WHERE graph = {graph_oid}
            AND kind = 'e'
            AND name NOT LIKE '_%'
            ORDER BY name
        """).fetchall()
        print(f"  Edge labels: {len(rows)}")
        for r in rows:
            print(f"    {r[0]}")
    except Exception as e:
        print(f"  Error with kind='e': {e}")

    # ================================================================
    # 4. If kind filter works: print the working query for the inventory script
    # ================================================================
    print("\n=== WORKING QUERY FOR INVENTORY SCRIPT ===")
    print(f"""
    # Use this in age_complete_inventory.py:
    graph_oid = conn.execute(
        "SELECT oid FROM ag_graph WHERE name = 'soc_graph'"
    ).fetchone()[0]
    # OR if oid doesn't work:
    graph_oid = conn.execute(
        "SELECT * FROM ag_graph WHERE name = 'soc_graph'"
    ).fetchone()[0]

    vertex_rows = conn.execute(f\"\"\"
        SELECT name FROM ag_label
        WHERE graph = {{graph_oid}}
        AND kind = 'v'
        AND name NOT LIKE '_%'
        ORDER BY name
    \"\"\").fetchall()
    """)

    conn.close()
    print("DONE")


if __name__ == "__main__":
    main()
