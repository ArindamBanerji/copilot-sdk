import psycopg2

print("Connecting with psycopg2...")
conn = psycopg2.connect(
    host="127.0.0.1",
    port=5433,
    dbname="postgres",
    user="postgres",
    password="postgres",
    connect_timeout=5,
)
conn.autocommit = True
cur = conn.cursor()
cur.execute("SELECT 1")
print("psycopg2 OK:", cur.fetchone())
cur.close()
conn.close()
print("Done")