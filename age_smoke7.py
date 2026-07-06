import psycopg

dsn = "host=localhost port=5433 dbname=postgres user=postgres password=postgres connect_timeout=5 sslmode=disable"
print(f"Connecting with: {dsn}")
conn = psycopg.connect(dsn, autocommit=True)
cur = conn.cursor()
cur.execute("SELECT 1")
print("OK:", cur.fetchone())
conn.close()
print("Done")