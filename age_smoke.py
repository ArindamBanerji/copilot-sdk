import psycopg
import sys

print("Connecting...")
try:
    conn = psycopg.connect(
        host="localhost",
        port=5433,
        dbname="postgres",
        user="postgres",
        password="postgres",
        connect_timeout=5,
    )
    print("Connected to postgres db")
    conn.autocommit = True
    cur = conn.cursor()
    cur.execute("SELECT 1")
    print("SELECT 1:", cur.fetchone())
    conn.close()
    print("Basic connection OK")
except Exception as e:
    print(f"Failed: {e}")
    sys.exit(1)

print("\nNow trying soc_copilot + AGE...")
try:
    conn = psycopg.connect(
        host="localhost",
        port=5433,
        dbname="soc_copilot",
        user="postgres",
        password="postgres",
        connect_timeout=5,
    )
    conn.autocommit = True
    cur = conn.cursor()
    cur.execute("LOAD 'age'")
    cur.execute("SET search_path = ag_catalog, public")
    cur.execute("SELECT * FROM ag_catalog.ag_graph")
    graphs = cur.fetchall()
    print(f"AGE graphs: {len(graphs)}")
    for g in graphs:
        print(f"  {g}")
    conn.close()
    print("AGE OK")
except Exception as e:
    print(f"AGE failed: {e}")