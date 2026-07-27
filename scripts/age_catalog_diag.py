"""AGE catalog diagnostic — why did the inventory query return 0 labels?

Tries multiple approaches to discover the ag_label schema and
find the correct query for vertex vs edge label distinction.
"""
import psycopg

DSN = "host=localhost port=5433 dbname=soc_copilot user=postgres password=postgres"


def section(title):
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}")


def main():
    conn = psycopg.connect(DSN)
    conn.autocommit = True
    conn.execute("LOAD 'age'")
    conn.execute('SET search_path = ag_catalog, "$user", public')

    # ================================================================
    # 1. ag_label column schema via pg_attribute (more reliable than information_schema)
    # ================================================================
    section("1. ag_label columns (pg_attribute)")

    try:
        rows = conn.execute("""
            SELECT a.attname, t.typname, a.attnum
            FROM pg_attribute a
            JOIN pg_class c ON a.attrelid = c.oid
            JOIN pg_namespace n ON c.relnamespace = n.oid
            JOIN pg_type t ON a.atttypid = t.oid
            WHERE n.nspname = 'ag_catalog'
            AND c.relname = 'ag_label'
            AND a.attnum > 0
            AND NOT a.attisdropped
            ORDER BY a.attnum
        """).fetchall()
        print(f"  {len(rows)} columns:")
        col_names = []
        for r in rows:
            print(f"    {r[2]}. {r[0]} ({r[1]})")
            col_names.append(r[0])
        print(f"  Column names: {col_names}")
    except Exception as e:
        print(f"  Error: {e}")
        col_names = []

    # ================================================================
    # 2. ag_label raw contents (first 15 rows, ALL columns)
    # ================================================================
    section("2. ag_label raw (first 15)")

    try:
        rows = conn.execute("SELECT * FROM ag_label LIMIT 15").fetchall()
        print(f"  {len(rows)} rows, {len(rows[0]) if rows else 0} columns per row")
        for r in rows:
            print(f"  {r}")
    except Exception as e:
        print(f"  Error: {e}")

    # ================================================================
    # 3. ag_graph contents
    # ================================================================
    section("3. ag_graph (all graphs)")

    try:
        rows = conn.execute("SELECT * FROM ag_graph").fetchall()
        for r in rows:
            print(f"  {r}")
    except Exception as e:
        print(f"  Error: {e}")

    # ================================================================
    # 4. Reproduce the EXACT query from the inventory script
    # ================================================================
    section("4. Reproduce inventory query (with kind filter)")

    try:
        rows = conn.execute("""
            SELECT name, kind FROM ag_label
            WHERE graph = (SELECT graphid FROM ag_graph WHERE name = 'soc_graph')
            AND name NOT LIKE '_%'
            ORDER BY kind, name
        """).fetchall()
        print(f"  Result: {len(rows)} rows")
        for r in rows[:5]:
            print(f"    {r}")
    except Exception as e:
        print(f"  ERROR (this is why inventory returned 0): {e}")

    # ================================================================
    # 5. Try alternative column names for vertex/edge distinction
    # ================================================================
    section("5. Alternative vertex/edge distinction approaches")

    # 5a. Try without kind filter
    try:
        rows = conn.execute("""
            SELECT name FROM ag_label
            WHERE graph = (SELECT graphid FROM ag_graph WHERE name = 'soc_graph')
            AND name NOT LIKE '_%'
        """).fetchall()
        print(f"  5a. Without kind filter: {len(rows)} labels")
        for r in rows[:5]:
            print(f"    {r[0]}")
    except Exception as e:
        print(f"  5a. Error: {e}")

    # 5b. Try 'labkind' column
    if "labkind" in col_names:
        try:
            rows = conn.execute("""
                SELECT name, labkind FROM ag_label
                WHERE graph = (SELECT graphid FROM ag_graph WHERE name = 'soc_graph')
                AND name NOT LIKE '_%'
                LIMIT 10
            """).fetchall()
            print(f"\n  5b. Using 'labkind': {len(rows)} rows")
            for r in rows[:5]:
                print(f"    name={r[0]}, labkind={r[1]}")
        except Exception as e:
            print(f"\n  5b. labkind error: {e}")

    # 5c. Try 'label_kind' column
    if "label_kind" in col_names:
        try:
            rows = conn.execute("""
                SELECT name, label_kind FROM ag_label
                WHERE graph = (SELECT graphid FROM ag_graph WHERE name = 'soc_graph')
                AND name NOT LIKE '_%'
                LIMIT 10
            """).fetchall()
            print(f"\n  5c. Using 'label_kind': {len(rows)} rows")
            for r in rows[:5]:
                print(f"    name={r[0]}, label_kind={r[1]}")
        except Exception as e:
            print(f"\n  5c. label_kind error: {e}")

    # 5d. Try inferring vertex vs edge by checking if label can be used in MATCH (n:Label)
    print(f"\n  5d. Inference approach — test known vertex and edge labels:")
    test_labels = {
        "vertex": ["Decision", "Alert", "Outcome"],
        "edge": ["DECIDED_ON", "HAS_OUTCOME", "INVOLVES"],
    }
    for expected_kind, labels in test_labels.items():
        for label in labels:
            try:
                rows = conn.execute(f"""
                    SELECT * FROM cypher('soc_graph', $$
                        MATCH (n:{label}) RETURN count(n) AS c
                    $$) as (c agtype)
                """).fetchall()
                print(f"    {label}: vertex query OK (count={rows[0][0]})")
            except Exception:
                try:
                    rows = conn.execute(f"""
                        SELECT * FROM cypher('soc_graph', $$
                            MATCH ()-[r:{label}]->() RETURN count(r) AS c
                        $$) as (c agtype)
                    """).fetchall()
                    print(f"    {label}: edge query OK (count={rows[0][0]})")
                except Exception as e2:
                    print(f"    {label}: neither query worked — {e2}")

    # ================================================================
    # 6. If no kind column: try to distinguish by relation_id or seq_id patterns
    # ================================================================
    section("6. Label classification by catalog properties")

    if col_names:
        # Show all ag_label rows for soc_graph with all columns
        try:
            rows = conn.execute("""
                SELECT * FROM ag_label
                WHERE graph = (SELECT graphid FROM ag_graph WHERE name = 'soc_graph')
                AND name NOT LIKE '_%'
                ORDER BY name
            """).fetchall()
            print(f"  {len(rows)} labels for soc_graph")
            print(f"  Columns: {col_names}")
            print()

            # Print all rows with column names
            for r in rows:
                parts = []
                for i, col in enumerate(col_names):
                    if i < len(r):
                        parts.append(f"{col}={r[i]}")
                print(f"    {', '.join(parts)}")

        except Exception as e:
            print(f"  Error: {e}")

    conn.close()
    print("\n  DONE")


if __name__ == "__main__":
    main()
