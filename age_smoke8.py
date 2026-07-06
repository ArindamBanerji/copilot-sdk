import psycopg
import subprocess

ip = subprocess.check_output(["wsl", "-u", "root", "hostname", "-I"]).decode().strip().split()[0]
print(f"WSL IP: {ip}")

dsn = f"host={ip} port=5433 dbname=postgres user=postgres password=postgres connect_timeout=5 sslmode=disable"
print(f"Connecting to: {dsn}")
conn = psycopg.connect(dsn, autocommit=True)
cur = conn.cursor()
cur.execute("SELECT 1")
print("OK:", cur.fetchone())
conn.close()
print("Done")