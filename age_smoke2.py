import socket
import sys

print("=== Test 1: Raw socket to 127.0.0.1:5433 ===")
try:
    s = socket.create_connection(("127.0.0.1", 5433), timeout=5)
    print("Raw socket: CONNECTED")
    s.close()
except Exception as e:
    print(f"Raw socket: FAILED - {e}")
    print("Problem is below Python — Windows networking can't reach WSL")
    sys.exit(1)

print("\n=== Test 2: psycopg with hostaddr (skip DNS) ===")
try:
    import psycopg
    conn = psycopg.connect(
        "hostaddr=127.0.0.1 port=5433 dbname=postgres user=postgres password=postgres connect_timeout=5"
    )
    conn.autocommit = True
    cur = conn.cursor()
    cur.execute("SELECT 1")
    print("psycopg hostaddr: OK", cur.fetchone())
    conn.close()
except Exception as e:
    print(f"psycopg hostaddr: FAILED - {e}")

print("\n=== Test 3: psycopg2 (if installed) ===")
try:
    import psycopg2
    conn = psycopg2.connect(
        host="127.0.0.1", port=5433, dbname="postgres",
        user="postgres", password="postgres", connect_timeout=5
    )
    cur = conn.cursor()
    cur.execute("SELECT 1")
    print("psycopg2: OK", cur.fetchone())
    conn.close()
except ImportError:
    print("psycopg2: not installed (skip)")
except Exception as e:
    print(f"psycopg2: FAILED - {e}")