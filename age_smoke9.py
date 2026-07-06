import psycopg
import subprocess

ip = subprocess.check_output(["wsl", "-u", "root", "hostname", "-I"]).decode().strip().split()[0]
print(f"WSL IP: {ip}")

dsn = f"host={ip} port=5433 dbname=soc_copilot user=postgres password=postgres connect_timeout=5 sslmode=disable"
conn = psycopg.connect(dsn, autocommit=True)
cur = conn.cursor()
cur.execute("LOAD 'age'")
cur.execute("SET search_path = ag_catalog, public")
cur.execute("SELECT * FROM ag_catalog.ag_graph")
graphs = cur.fetchall()
print(f"AGE graphs: {len(graphs)}")
for g in graphs:
    print(f"  {g}")
conn.close()
print("All good")