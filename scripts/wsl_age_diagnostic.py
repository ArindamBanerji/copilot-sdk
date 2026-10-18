#!/usr/bin/env python3
"""
wsl_age_diagnostic.py — Diagnose and fix WSL2 + PostgreSQL + AGE connectivity.

Run from Windows PowerShell:
    python wsl_age_diagnostic.py diagnose
    python wsl_age_diagnostic.py fix
    python wsl_age_diagnostic.py diagnose   # verify fix worked

What it checks:
  1. Is WSL2 distro running?
  2. Is PostgreSQL process actually running (not /bin/true stub)?
  3. Is PostgreSQL listening on TCP (listen_addresses)?
  4. What does pg_hba.conf say for age_user?
  5. Is AGE extension installed?
  6. Can Windows connect on port 5433 (IPv4 + IPv6)?
  7. What is the skip condition in test_store_parity.py?

What 'fix' does:
  1. Sets listen_addresses = '*' in postgresql.conf
  2. Adds md5 auth line for age_user in pg_hba.conf
  3. Sets/resets age_user password
  4. Restarts PostgreSQL inside WSL2
  5. Sets up Windows->WSL2 port forwarding (netsh)
"""

import subprocess
import sys
import socket
import os
import time

WSL_DISTRO = "Ubuntu-24.04"
PG_PORT = 5433
PG_USER = "age_user"
PG_DB = "age_graph"
PG_VERSION = "17"


# == helpers ===========================================================

def wsl_run(cmd: str, timeout: int = 15) -> tuple:
    """Run a command inside WSL2 and return (returncode, stdout, stderr)."""
    try:
        r = subprocess.run(
            ["wsl", "-d", WSL_DISTRO, "-e", "bash", "-c", cmd],
            capture_output=True, text=True, timeout=timeout
        )
        return r.returncode, r.stdout.strip(), r.stderr.strip()
    except subprocess.TimeoutExpired:
        return -1, "", "TIMEOUT"
    except FileNotFoundError:
        return -2, "", "wsl.exe not found"


def win_run(cmd: list, timeout: int = 10) -> tuple:
    """Run a Windows command."""
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return r.returncode, r.stdout.strip(), r.stderr.strip()
    except subprocess.TimeoutExpired:
        return -1, "", "TIMEOUT"
    except FileNotFoundError:
        return -2, "", f"{cmd[0]} not found"


def tcp_probe(host: str, port: int, timeout: float = 3.0) -> str:
    """Try TCP connect. Returns 'OK', 'REFUSED', 'TIMEOUT', or error."""
    family = socket.AF_INET6 if ":" in host else socket.AF_INET
    s = socket.socket(family, socket.SOCK_STREAM)
    s.settimeout(timeout)
    try:
        s.connect((host, port))
        s.close()
        return "OK"
    except socket.timeout:
        return "TIMEOUT"
    except ConnectionRefusedError:
        return "REFUSED"
    except OSError as e:
        return f"ERROR: {e}"
    finally:
        s.close()


def header(msg: str):
    print(f"\n{'='*60}")
    print(f"  {msg}")
    print(f"{'='*60}")


def check(label: str, ok: bool, detail: str = "") -> bool:
    icon = "PASS" if ok else "FAIL"
    print(f"  [{icon}] {label}")
    if detail:
        for line in detail.splitlines():
            print(f"         {line}")
    return ok


# == diagnose ==========================================================

def diagnose() -> dict:
    results = {}

    # 1. WSL2 distro running?
    header("1. WSL2 Distro")
    rc, out, err = win_run(["wsl", "-l", "-v"])
    if rc != 0:
        check("WSL available", False, err)
        results["wsl"] = False
        return results
    out_clean = out.replace("\x00", "")
    running = WSL_DISTRO in out_clean and "Running" in out_clean
    check(f"{WSL_DISTRO} is Running", running, out_clean)
    results["wsl"] = running
    if not running:
        print("  -> Start it: wsl -d Ubuntu-24.04")
        return results

    # 2. PostgreSQL process (not /bin/true stub)
    header("2. PostgreSQL Process")
    rc, out, _ = wsl_run("ps aux | grep -E 'postgres|postmaster' | grep -v grep")
    real_pg = "postgres" in out and "/bin/true" not in out
    check("Real PostgreSQL process running", real_pg,
          out[:500] if out else "(no output)")
    results["pg_process"] = real_pg

    rc, out, _ = wsl_run("pg_lsclusters")
    check("pg_lsclusters", rc == 0, out)
    results["pg_cluster"] = "online" in out.lower() if out else False

    # 3. listen_addresses in postgresql.conf
    header("3. PostgreSQL listen_addresses")
    conf_path = f"/etc/postgresql/{PG_VERSION}/main/postgresql.conf"
    rc, out, _ = wsl_run(f"grep -n 'listen_addresses' {conf_path}")
    if rc == 0:
        active_lines = [l for l in out.splitlines()
                        if not l.strip().startswith("#")]
        listens_all = any("*" in l or "0.0.0.0" in l for l in active_lines)
        check("listen_addresses includes TCP", len(active_lines) > 0, out)
        check("listen_addresses = '*' or '0.0.0.0'", listens_all,
              "Needed for Windows->WSL2 connections" if not listens_all else "")
        results["listen_addresses"] = listens_all
    else:
        check("postgresql.conf found", False, f"Could not read {conf_path}")
        results["listen_addresses"] = False

    rc, out, _ = wsl_run(f"grep -E '^port' {conf_path}")
    check("Port config", True,
          out if out else f"(default, check pg_lsclusters for actual port)")

    # 4. pg_hba.conf for age_user
    header("4. pg_hba.conf Authentication")
    hba_path = f"/etc/postgresql/{PG_VERSION}/main/pg_hba.conf"
    rc, out, _ = wsl_run(f"grep -n -v '^#' {hba_path} | grep -v '^$'")
    if rc == 0:
        check("pg_hba.conf active lines", True, out)
        has_age_user = "age_user" in out
        has_tcp_md5 = any(
            ("md5" in l or "scram" in l) and ("host" in l)
            for l in out.splitlines()
        )
        check("age_user-specific rule exists", has_age_user,
              "Explicit rule for age_user" if has_age_user
              else "No specific rule -- relies on catch-all")
        check("TCP md5/scram auth available", has_tcp_md5,
              "" if has_tcp_md5
              else "Only peer/ident auth -> Windows connections will fail")
        results["hba_age_user"] = has_age_user
        results["hba_tcp_md5"] = has_tcp_md5
    else:
        check("pg_hba.conf readable", False)
        results["hba_age_user"] = False
        results["hba_tcp_md5"] = False

    # 5. AGE extension
    header("5. AGE Extension")
    rc, out, _ = wsl_run(
        f"sudo -u postgres psql -p {PG_PORT} -d {PG_DB} -c "
        f"\"SELECT extname, extversion FROM pg_extension "
        f"WHERE extname='age';\" 2>&1"
    )
    has_age = "age" in out and "extversion" in out
    check("AGE extension loaded in age_graph", has_age, out[:300])
    results["age_ext"] = has_age

    if not has_age:
        rc2, out2, _ = wsl_run(
            f"sudo -u postgres psql -p {PG_PORT} -l 2>&1 | grep age_graph"
        )
        check("age_graph database exists", rc2 == 0,
              out2 if out2 else "(not found)")
        results["age_db"] = rc2 == 0

    # 6. WSL2 network + TCP from inside
    header("6. WSL2 Network")
    rc, out, _ = wsl_run("hostname -I")
    wsl_ip = out.split()[0] if out else None
    check("WSL2 IP", wsl_ip is not None, wsl_ip or "(could not determine)")
    results["wsl_ip"] = wsl_ip

    rc, out, _ = wsl_run(f"ss -tlnp | grep {PG_PORT}")
    pg_tcp = rc == 0 and str(PG_PORT) in out
    check(f"PostgreSQL listening on TCP :{PG_PORT} inside WSL",
          pg_tcp, out)
    results["pg_tcp_listen"] = pg_tcp

    # 7. Windows -> WSL2 TCP connectivity
    header("7. Windows -> WSL2 TCP Connectivity")
    for host_label, host in [("IPv4 127.0.0.1", "127.0.0.1"),
                              ("IPv6 ::1", "::1")]:
        result = tcp_probe(host, PG_PORT, timeout=3.0)
        check(f"{host_label}:{PG_PORT}", result == "OK", result)
        results[f"tcp_{host_label}"] = result

    if wsl_ip:
        result = tcp_probe(wsl_ip, PG_PORT, timeout=3.0)
        check(f"WSL IP {wsl_ip}:{PG_PORT}", result == "OK", result)
        results["tcp_wsl_ip"] = result

    # 8. Windows port forwarding (netsh)
    header("8. Windows Port Forwarding (netsh)")
    rc, out, _ = win_run(
        ["netsh", "interface", "portproxy", "show", "v4tov4"]
    )
    has_proxy = str(PG_PORT) in out if out else False
    check(f"netsh portproxy for {PG_PORT}", has_proxy,
          out if out else "(none configured)")
    results["netsh_proxy"] = has_proxy

    # 9. test_store_parity.py skip condition
    header("9. test_store_parity.py Skip Condition")
    graph_dsn = os.environ.get("GRAPH_DSN", None)
    check("GRAPH_DSN env var set", graph_dsn is not None,
          f"Value: {graph_dsn}" if graph_dsn
          else "NOT SET -- this is likely why gate_2_1 skipped cleanly")
    results["graph_dsn"] = graph_dsn

    sdk_root = os.environ.get("CLAUDE_SDK", None)
    if sdk_root:
        parity_file = os.path.join(sdk_root, "tests", "test_store_parity.py")
        if os.path.exists(parity_file):
            with open(parity_file, "r") as f:
                content = f.read()
            skip_lines = [
                (i + 1, line.rstrip())
                for i, line in enumerate(content.splitlines())
                if any(kw in line.lower()
                       for kw in ["skip", "skipif", "graph_dsn",
                                  "psycopg", "pytest.mark"])
            ]
            if skip_lines:
                detail = "\n".join(f"  L{n}: {l}"
                                   for n, l in skip_lines[:15])
                check("Skip conditions found in test_store_parity.py",
                      True, detail)
            else:
                check("Skip conditions in test_store_parity.py", False,
                      "No skip markers found -- tests always run")
            results["parity_skip_lines"] = skip_lines
        else:
            check("test_store_parity.py found", False,
                  f"Not at {parity_file}")
    else:
        check("CLAUDE_SDK env var", False,
              "Cannot locate test_store_parity.py without it")

    # == Summary ==
    header("DIAGNOSIS SUMMARY")
    problems = []
    if not results.get("pg_process"):
        problems.append(
            "PostgreSQL not actually running (may be /bin/true stub)")
    if not results.get("listen_addresses"):
        problems.append(
            "listen_addresses not set to '*' -- PG only on Unix socket")
    if not results.get("hba_tcp_md5"):
        problems.append(
            "pg_hba.conf has no TCP md5/scram auth -- "
            "Windows connections rejected")
    if not results.get("pg_tcp_listen"):
        problems.append(
            f"PostgreSQL not listening on TCP port {PG_PORT} inside WSL")
    if not results.get("netsh_proxy"):
        problems.append(
            f"No Windows portproxy for {PG_PORT} -> WSL2 IP")
    if results.get("graph_dsn") is None:
        problems.append(
            "GRAPH_DSN not set -- gate_2_1 likely skipped because of this; "
            "gate_2_2/gate_2_3 may have had it set to a stale DSN")

    if problems:
        print("\n  PROBLEMS FOUND:")
        for i, p in enumerate(problems, 1):
            print(f"    {i}. {p}")
        print(f"\n  Run: python {sys.argv[0]} fix")
    else:
        print("\n  [PASS] All checks passed. "
              "WSL+AGE+PostgreSQL should be reachable.")

    return results


# == fix ===============================================================

def fix():
    header("FIX: WSL2 + PostgreSQL + AGE Connectivity")

    conf_path = f"/etc/postgresql/{PG_VERSION}/main/postgresql.conf"
    hba_path = f"/etc/postgresql/{PG_VERSION}/main/pg_hba.conf"

    # Step 1: listen_addresses = '*'
    print("\n  [1/6] Setting listen_addresses = '*' ...")
    wsl_run(
        f"sudo sed -i \"s/^listen_addresses/#listen_addresses/\" {conf_path}"
    )
    wsl_run(
        f"echo \"listen_addresses = '*'\" | sudo tee -a {conf_path}"
    )
    rc, out, _ = wsl_run(
        f"grep -n 'listen_addresses' {conf_path} | tail -3"
    )
    print(f"      {out}")

    # Step 2: port = 5433
    print("\n  [2/6] Confirming port = 5433 ...")
    rc, out, _ = wsl_run(f"grep -E '^port' {conf_path}")
    if not out or "5433" not in out:
        wsl_run(f"sudo sed -i \"s/^port/#port/\" {conf_path}")
        wsl_run(
            f"echo \"port = {PG_PORT}\" | sudo tee -a {conf_path}"
        )
    rc, out, _ = wsl_run(
        f"grep -E 'port' {conf_path} | grep -v '#' | tail -1"
    )
    print(f"      {out}")

    # Step 3: md5 auth for age_user in pg_hba.conf
    print("\n  [3/6] Adding md5 auth for age_user in pg_hba.conf ...")
    rc, out, _ = wsl_run(f"grep 'age_user' {hba_path}")
    if "age_user" not in (out or ""):
        local_line = f"local   {PG_DB}    {PG_USER}                 md5"
        hba_v4 = f"host    {PG_DB}    {PG_USER}    0.0.0.0/0    md5"
        hba_v6 = f"host    {PG_DB}    {PG_USER}    ::0/0        md5"
        wsl_run(f"echo '{local_line}' | sudo tee -a {hba_path}")
        wsl_run(f"echo '{hba_v4}' | sudo tee -a {hba_path}")
        wsl_run(f"echo '{hba_v6}' | sudo tee -a {hba_path}")
        print(f"      Added: {local_line}")
        print(f"      Added: {hba_v4}")
        print(f"      Added: {hba_v6}")
    else:
        print(f"      Already present: {out}")

    # Step 4: age_user password
    print("\n  [4/6] Setting age_user password ...")
    pw = "age_user_pw"
    rc, out, err = wsl_run(
        f"sudo -u postgres psql -p {PG_PORT} -c "
        f"\"ALTER USER {PG_USER} PASSWORD '{pw}';\" 2>&1"
    )
    if "ALTER ROLE" in (out + err):
        print(f"      Password set to '{pw}'")
    else:
        print(f"      ALTER result: {out} {err}")
        rc2, out2, err2 = wsl_run(
            f"sudo -u postgres psql -p {PG_PORT} -c "
            f"\"CREATE USER {PG_USER} WITH PASSWORD '{pw}'; "
            f"GRANT ALL ON DATABASE {PG_DB} TO {PG_USER};\" 2>&1"
        )
        print(f"      Create attempt: {out2} {err2}")

    # Step 5: Restart PostgreSQL
    print("\n  [5/6] Restarting PostgreSQL ...")
    rc, out, err = wsl_run(
        f"sudo pg_ctlcluster {PG_VERSION} main restart 2>&1",
        timeout=20
    )
    print(f"      {out} {err}")
    time.sleep(2)

    rc, out, _ = wsl_run(f"ss -tlnp | grep {PG_PORT}")
    tcp_ok = rc == 0 and str(PG_PORT) in out
    print(f"      TCP listen: {'PASS' if tcp_ok else 'FAIL'} {out}")

    # Step 6: Windows port forwarding
    print("\n  [6/6] Setting up Windows portproxy ...")
    rc, wsl_ip_out, _ = wsl_run("hostname -I")
    wsl_ip = wsl_ip_out.split()[0] if wsl_ip_out else None
    if wsl_ip:
        win_run(["netsh", "interface", "portproxy", "delete", "v4tov4",
                 f"listenport={PG_PORT}", "listenaddress=127.0.0.1"])
        rc, out, err = win_run([
            "netsh", "interface", "portproxy", "add", "v4tov4",
            f"listenport={PG_PORT}", "listenaddress=127.0.0.1",
            f"connectport={PG_PORT}", f"connectaddress={wsl_ip}"
        ])
        if rc == 0:
            print(f"      [PASS] 127.0.0.1:{PG_PORT} -> {wsl_ip}:{PG_PORT}")
        else:
            print(f"      [FAIL] netsh failed (need admin?): {err}")
            print(f"      -> Run PowerShell as Admin and re-run")
    else:
        print(f"      [FAIL] Could not get WSL2 IP")

    # == Post-fix verification ==
    header("POST-FIX VERIFICATION")
    time.sleep(1)

    for host in ["127.0.0.1", "::1"]:
        result = tcp_probe(host, PG_PORT, timeout=3.0)
        icon = "PASS" if result == "OK" else "FAIL"
        print(f"  [{icon}] {host}:{PG_PORT} -> {result}")

    if wsl_ip:
        result = tcp_probe(wsl_ip, PG_PORT, timeout=3.0)
        icon = "PASS" if result == "OK" else "FAIL"
        print(f"  [{icon}] {wsl_ip}:{PG_PORT} -> {result}")

    print("\n  Testing psycopg connect ...")
    try:
        import psycopg
        dsn = (f"host=127.0.0.1 port={PG_PORT} dbname={PG_DB} "
               f"user={PG_USER} password={pw} connect_timeout=5")
        conn = psycopg.connect(dsn, autocommit=True)
        cur = conn.execute("SELECT 1")
        row = cur.fetchone()
        print(f"  [PASS] psycopg connected! SELECT 1 = {row}")

        cur2 = conn.execute(
            "SELECT extname FROM pg_extension WHERE extname='age'"
        )
        age_row = cur2.fetchone()
        if age_row:
            print(f"  [PASS] AGE extension present")
        else:
            print(f"  [WARN] AGE extension not loaded -- "
                  f"run: CREATE EXTENSION age;")
        conn.close()
    except ImportError:
        print("  [WARN] psycopg not installed in this Python -- "
              "install with: pip install psycopg[binary]")
    except Exception as e:
        print(f"  [FAIL] psycopg connect failed: {e}")

    print(f"\n  GRAPH_DSN for pytest:")
    print(f'    $env:GRAPH_DSN = "host=127.0.0.1 port={PG_PORT} '
          f'dbname={PG_DB} user={PG_USER} password={pw}"')
    print(f"\n  Then re-run SDK Root tests:")
    print(f"    cd $env:CLAUDE_SDK; "
          f"python -m pytest tests/ -q --timeout=120")


# == main ==============================================================

if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in ("diagnose", "fix"):
        print(f"Usage: python {sys.argv[0]} diagnose|fix")
        print(f"  diagnose  -- check everything, report problems")
        print(f"  fix       -- fix pg_hba, listen_addresses, "
              f"portproxy, password")
        sys.exit(1)

    if sys.argv[1] == "diagnose":
        diagnose()
    elif sys.argv[1] == "fix":
        fix()
