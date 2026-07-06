import psycopg

print("Connecting with sslmode=disable...")
conn = psycopg.connect(
    "hostaddr=127.0.0.1 port=5433 dbname=postgres user=postgres password=postgres connect_timeout=5 sslmode=disable"
)
conn.autocommit = True
cur = conn.cursor()
cur.execute("SELECT 1")
print("OK:", cur.fetchone())
conn.close()
print("Done")