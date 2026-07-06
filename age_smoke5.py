import psycopg

print("psycopg3 connecting...")
conn = psycopg.connect(
    "hostaddr=127.0.0.1 port=5433 dbname=soc_copilot user=postgres password=postgres connect_timeout=5 sslmode=disable"
)
conn.autocommit = True
cur = conn.cursor()
cur.execute("SELECT 1")
print("psycopg3 OK:", cur.fetchone())

cur.execute("LOAD 'age'")
cur.execute("SET search_path = ag_catalog, public")
cur.execute("SELECT * FROM ag_catalog.ag_graph")
graphs = cur.fetchall()
print(f"AGE graphs: {len(graphs)}")
for g in graphs:
    print(f"  {g}")

conn.close()
print("All good")