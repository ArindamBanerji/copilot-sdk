#!/usr/bin/env python3
"""
Compounding Intelligence Platform Launcher.

Usage:
    python demo.py                  # Start all 5 copilots, open browsers
    python demo.py --playwright     # Start SOC + S2P only (Playwright prereqs)
    python demo.py --soc            # SOC only (requires AGE)
    python demo.py --s2p            # S2P only
    python demo.py --sdk            # Trading + Purchasing + DataOps only
    python demo.py --dataops        # DataOps only
    python demo.py --stop           # Stop all copilot processes
    python demo.py --status         # Show what's running + persistent data
    python demo.py --reset          # Wipe ALL persistent data, fresh start
    python demo.py --reset trading  # Wipe one copilot's data only
    python demo.py --reset --sdk    # Wipe SDK copilot data; run --sdk separately to restart
    python demo.py --preseed        # Pre-seed after start (deprecated)
    python demo.py --graph          # AGE graph mode for DataOps
    python demo.py --no-browser     # Don't open browser tabs
    python demo.py --kill-all       # Kill all known copilot ports
"""

import argparse
import importlib
import json
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import time
import webbrowser
from pathlib import Path
from urllib.request import urlopen

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# --- Configuration ---

SCRIPT_DIR = Path(__file__).resolve().parent
CI_PLATFORM = SCRIPT_DIR.parent / "ci-platform"
KEEPALIVE_PID_FILE = SCRIPT_DIR / ".wsl_keepalive.pid"

IS_WINDOWS = sys.platform == "win32"
CREATE_FLAGS = subprocess.CREATE_NEW_CONSOLE if IS_WINDOWS else 0

# --- Persistent Storage ---
# One data directory per copilot. Backend constructs its own db
# filename (e.g. trading.db) matching its DEFAULT_DB_PATH pattern.
# demo.py passes CI_DATA_DIR only — backend owns the filename.
# See docs/storage_architecture.md.
DEFAULT_DATA_DIR = Path.home() / ".ci-platform"

# AGE connection parameters
AGE_DSN_SOC = "host=127.0.0.1 port=5433 dbname=soc_copilot user=postgres password=postgres"
AGE_DSN_DATAOPS = "host=localhost port=5433 dbname=soc_graph user=postgres password=postgres"

COPILOTS = [
    {
        "name": "SOC",
        "be_port": 8001,
        "fe_port": 5173,
        "be_path": Path(os.environ.get(
            "CLAUDE_SOC",
            str(SCRIPT_DIR.parent / "gen-ai-roi-demo-v4-v50"),
        )) / "backend",
        "fe_path": Path(os.environ.get(
            "CLAUDE_SOC",
            str(SCRIPT_DIR.parent / "gen-ai-roi-demo-v4-v50"),
        )) / "frontend",
        "requires_age": True,
        "graph_dsn": AGE_DSN_SOC,
        "env": {
            "GRAPH_BACKEND": "age",
            "GRAPH_DSN": AGE_DSN_SOC,
        },
        "persistent": False,  # SOC uses AGE, not file-backed SQLite
        "db_filename": None,
    },
    {
        "name": "Trading",
        "be_port": 8010,
        "fe_port": 5174,
        "be_path": SCRIPT_DIR / "apps" / "trading" / "backend",
        "fe_path": SCRIPT_DIR / "apps" / "trading" / "frontend",
        "persistent": True,
        "db_filename": "trading.db",
    },
    {
        "name": "Purchasing",
        "be_port": 8020,
        "fe_port": 5175,
        "be_path": SCRIPT_DIR / "apps" / "purchasing" / "backend",
        "fe_path": SCRIPT_DIR / "apps" / "purchasing" / "frontend",
        "persistent": True,
        "db_filename": "purchasing.db",
    },
    {
        "name": "DataOps",
        "be_port": 8030,
        "fe_port": 5176,
        "be_path": SCRIPT_DIR / "apps" / "dataops" / "backend",
        "fe_path": SCRIPT_DIR / "apps" / "dataops" / "frontend",
        "persistent": True,
        "db_filename": "dataops.db",
    },
    {
        "name": "S2P",
        "be_port": 8002,
        "fe_port": 5177,
        "be_path": Path(os.environ.get(
            "CLAUDE_S2P",
            str(SCRIPT_DIR.parent / "s2p-copilot"),
        )) / "backend",
        "fe_path": SCRIPT_DIR / "apps" / "s2p" / "frontend",
        "persistent": True,
        "db_filename": "s2p.db",
    },
]

# Named groups for convenience flags
SDK_NAMES = {"trading", "purchasing", "dataops"}
PLAYWRIGHT_NAMES = {"soc", "s2p"}

ACTIVE_GRAPH_APPS = {
    "trading": {
        "prefix": "TRADING_ACTIVE_",
        "domain": "trading",
    },
    "purchasing": {
        "prefix": "PURCHASING_ACTIVE_",
        "domain": "purchasing",
    },
    "dataops": {
        "prefix": "DATAOPS_ACTIVE_",
        "domain": "dataops",
    },
    "s2p": {
        "prefix": "S2P_ACTIVE_",
        "domain": "s2p",
    },
}
DEFAULT_ACTIVE_AGE_GRAPH = "governed_copilot_graph"


# --- Persistent Data Helpers ---

def _copilot_data_dir(copilot_name: str, data_root: Path = DEFAULT_DATA_DIR) -> Path:
    """Get or create persistent data directory for a copilot."""
    d = data_root / copilot_name.lower()
    d.mkdir(parents=True, exist_ok=True)
    return d


def _copilot_db_path(copilot: dict, data_root: Path = DEFAULT_DATA_DIR) -> Path | None:
    """Full path to a copilot's db file, or None if not persistent."""
    if not copilot.get("persistent") or not copilot.get("db_filename"):
        return None
    return _copilot_data_dir(copilot["name"], data_root) / copilot["db_filename"]


def _decision_count(db_path: Path) -> int | None:
    try:
        conn = sqlite3.connect(str(db_path))
        try:
            return conn.execute("SELECT COUNT(*) FROM decisions").fetchone()[0]
        finally:
            conn.close()
    except Exception:
        return None


def _backup_db_path(db_path: Path) -> Path:
    backup = db_path.with_suffix(db_path.suffix + ".bak")
    if not backup.exists():
        return backup
    stamp = time.strftime("%Y%m%d-%H%M%S")
    counter = 1
    while True:
        candidate = db_path.with_suffix(db_path.suffix + f".{stamp}.{counter}.bak")
        if not candidate.exists():
            return candidate
        counter += 1


def _maybe_migrate_dev_db(copilot: dict, copilot_dir: Path, data_root: Path) -> None:
    """Copy a richer repo-local dev DB into empty/tiny persistent storage."""
    if not copilot.get("persistent"):
        return
    db_filename = copilot.get("db_filename") or f"{copilot['name'].lower()}.db"
    persistent_db = copilot_dir / db_filename
    persistent_size = persistent_db.stat().st_size if persistent_db.exists() else 0
    persistent_decisions = _decision_count(persistent_db) if persistent_db.exists() else None
    if persistent_db.exists() and persistent_size >= 1024:
        if persistent_decisions is None:
            print(
                f"  Skipping {copilot['name']} dev DB migration: "
                "persistent DB exists but decision count is unreadable"
            )
            return
        if persistent_decisions > 1:
            return

    be_path = copilot.get("be_path")
    if not be_path:
        return
    dev_candidates = []
    if copilot.get("dev_db_path"):
        dev_candidates.append(Path(copilot["dev_db_path"]))
    dev_candidates.extend([
        Path(be_path) / "app" / "data" / db_filename,
        Path(be_path) / "data" / db_filename,
    ])

    for dev_db in dev_candidates:
        if not dev_db.exists() or dev_db.stat().st_size <= 1024:
            continue
        dev_decisions = _decision_count(dev_db)
        if dev_decisions is None:
            continue
        if persistent_decisions is not None and dev_decisions <= max(persistent_decisions, 1):
            continue
        copilot_dir.mkdir(parents=True, exist_ok=True)
        if persistent_db.exists():
            backup = _backup_db_path(persistent_db)
            shutil.copy2(persistent_db, backup)
            print(f"  Backed up {copilot['name']} persistent DB to {backup}")
        shutil.copy2(dev_db, persistent_db)
        size_kb = persistent_db.stat().st_size // 1024
        print(
            f"  Migrated {copilot['name']} data from dev location "
            f"({size_kb}KB, {dev_decisions} decisions)"
        )
        return


def _read_copilot_data_stats(copilot: dict, data_root: Path = DEFAULT_DATA_DIR) -> dict:
    """Read decision count from a copilot's persistent DB."""
    result = {"copilot": copilot["name"], "db_exists": False, "decisions": 0, "archived": 0}
    db_path = _copilot_db_path(copilot, data_root)
    if db_path is None or not db_path.exists():
        return result
    result["db_exists"] = True
    try:
        conn = sqlite3.connect(str(db_path))
        try:
            result["decisions"] = conn.execute(
                "SELECT COUNT(*) FROM decisions"
            ).fetchone()[0]
        except sqlite3.OperationalError:
            pass
        try:
            result["archived"] = conn.execute(
                "SELECT COUNT(*) FROM decisions_archive"
            ).fetchone()[0]
        except sqlite3.OperationalError:
            pass
        conn.close()
    except Exception:
        pass
    return result


def _redact_dsn(value: str | None) -> str:
    """Redact credentials while preserving the useful host/db shape."""
    if not value:
        return ""
    text = str(value)
    text = re.sub(r"://([^:/?#@]+):([^@/?#]+)@", r"://***:***@", text)
    text = re.sub(
        r"(?i)(^|\s|[?&;])(user|username|password|passwd|pwd|token|secret)=([^&;\s]+)",
        lambda match: f"{match.group(1)}{match.group(2)}=***",
        text,
    )
    return text


def _active_graph_arg_name(app_name: str) -> str:
    return f"{app_name.lower()}_graph_backend"


def _requested_graph_backend(app_name: str, args=None, env: dict[str, str] | None = None) -> str:
    app_key = app_name.lower()
    if app_key not in ACTIVE_GRAPH_APPS:
        return "soc-age" if app_key == "soc" else "sqlite"
    if args is not None:
        requested = getattr(args, _active_graph_arg_name(app_key), None)
        if requested:
            return str(requested).lower()
    source = os.environ if env is None else env
    prefix = ACTIVE_GRAPH_APPS[app_key]["prefix"]
    return (source.get(f"{prefix}GRAPH_BACKEND") or "sqlite").strip().lower()


def _active_graph_status_label(app_name: str, args=None, env: dict[str, str] | None = None) -> str:
    app_key = app_name.lower()
    if app_key == "soc":
        return "AGE"
    backend = _requested_graph_backend(app_key, args=args, env=env)
    if backend == "age":
        return "AGE new-writes + SQLite history"
    return "SQLite"


def _inject_active_graph_env(copilot_env: dict[str, str], app_name: str, args) -> dict[str, str]:
    app_key = app_name.lower()
    if app_key not in ACTIVE_GRAPH_APPS:
        return copilot_env
    requested = getattr(args, _active_graph_arg_name(app_key), None)
    if requested in (None, "", "sqlite"):
        return copilot_env
    if requested != "age":
        raise RuntimeError(f"Unsupported graph backend for {app_name}: {requested}")

    config = ACTIVE_GRAPH_APPS[app_key]
    prefix = config["prefix"]
    dsn_key = f"{prefix}AGE_DSN"
    graph_key = f"{prefix}AGE_GRAPH"
    domain_key = f"{prefix}AGE_DOMAIN"
    dsn = os.environ.get(dsn_key, "").strip()
    if not dsn:
        raise RuntimeError(f"{dsn_key} is required when --{app_key}-graph-backend=age")
    graph = (os.environ.get(graph_key) or DEFAULT_ACTIVE_AGE_GRAPH).strip()
    if not graph:
        raise RuntimeError(f"{graph_key} must not be blank")
    if graph == "soc_graph":
        raise RuntimeError(f"{graph_key}=soc_graph is forbidden for {app_name}")

    copilot_env[f"{prefix}GRAPH_BACKEND"] = "age"
    copilot_env[dsn_key] = dsn
    copilot_env[graph_key] = graph
    copilot_env[domain_key] = config["domain"]
    test_mode_key = f"{prefix}AGE_TEST_MODE"
    live_test_key = f"{prefix}LIVE_AGE_TEST"
    if test_mode_key in os.environ:
        copilot_env[test_mode_key] = os.environ[test_mode_key]
    if live_test_key in os.environ:
        copilot_env[live_test_key] = os.environ[live_test_key]
    return copilot_env


def _prepare_copilot_env(copilot: dict, args, base_env: dict[str, str] | None = None) -> dict[str, str]:
    env = dict(os.environ if base_env is None else base_env)
    if copilot.get("env"):
        env.update(copilot["env"])
    return _inject_active_graph_env(env, copilot["name"], args)


def _active_age_dsn_from_env(copilot: dict, env: dict[str, str], args) -> str | None:
    app_key = copilot["name"].lower()
    if app_key not in ACTIVE_GRAPH_APPS:
        return None
    if _requested_graph_backend(app_key, args=args, env=env) != "age":
        return None
    prefix = ACTIVE_GRAPH_APPS[app_key]["prefix"]
    return env.get(f"{prefix}AGE_DSN")


def _age_precheck_dsns(prepared: list[dict], args) -> list[str]:
    dsns: list[str] = []
    for item in prepared:
        copilot = item["copilot"]
        env = item["env"]
        if copilot.get("requires_age"):
            dsn = copilot.get("graph_dsn") or env.get("GRAPH_DSN")
            if dsn:
                dsns.append(dsn)
        active_dsn = _active_age_dsn_from_env(copilot, env, args)
        if active_dsn:
            dsns.append(active_dsn)

    unique: list[str] = []
    seen: set[str] = set()
    for dsn in dsns:
        if dsn not in seen:
            unique.append(dsn)
            seen.add(dsn)
    return unique


def _run_replay_outbox_if_requested(enabled: bool) -> bool:
    if not enabled:
        return False
    try:
        module = importlib.import_module("copilot_sdk.outbox.replay")
    except ModuleNotFoundError:
        print("Outbox replay requested but copilot_sdk.outbox replay is not available yet; not run.")
        return False
    replay = getattr(module, "replay_outbox", None)
    if not callable(replay):
        print("Outbox replay requested but replay_outbox() is not available; not run.")
        return False
    replay()
    print("Outbox replay completed.")
    return True


# --- Helpers ---

def check_port(port: int) -> bool:
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(2)
    try:
        s.connect(("localhost", port))
        s.close()
        return True
    except Exception:
        return False


def check_health(port: int, path: str = "/health") -> dict | None:
    try:
        r = urlopen(f"http://localhost:{port}{path}", timeout=5)
        return json.loads(r.read())
    except Exception:
        return None


def verify_age(dsn: str) -> bool:
    try:
        import psycopg
        conn = psycopg.connect(dsn, autocommit=True)
        conn.close()
        return True
    except Exception:
        return False


def verify_wsl2_running() -> bool:
    try:
        result = subprocess.run(
            ["wsl", "--list", "--running"],
            capture_output=True, text=True, timeout=5,
        )
        output = result.stdout + result.stderr
        if "no running" in output.lower() or not result.stdout.strip():
            return False
        return True
    except Exception:
        return False


def start_wsl2_postgres() -> bool:
    print("  Starting WSL2 + PostgreSQL...")
    try:
        result = subprocess.run(
            ["wsl", "-d", "Ubuntu-24.04", "-u", "root", "--",
             "bash", "-c",
             "service postgresql start 2>/dev/null; sleep 3; "
             "su -c 'pg_isready -h 127.0.0.1 -p 5433 -q' postgres "
             "&& echo PG_READY || echo PG_FAIL"],
            capture_output=True, text=True, timeout=30,
        )
        if "PG_READY" not in result.stdout:
            output = (result.stdout + result.stderr).strip()
            print(f"  ✗ PostgreSQL did not start: {output[:200]}")
            return False
        print("  ✓ PostgreSQL started in WSL2")
        _start_wsl2_keepalive()
        return True
    except subprocess.TimeoutExpired:
        print("  ✗ WSL2 start timed out (30s)")
        return False
    except Exception as e:
        print(f"  ✗ WSL2 start failed: {e}")
        return False


_wsl_keepalive_proc = None


def _start_wsl2_keepalive():
    global _wsl_keepalive_proc
    if _wsl_keepalive_proc and _wsl_keepalive_proc.poll() is None:
        return
    _wsl_keepalive_proc = subprocess.Popen(
        ["wsl", "-d", "Ubuntu-24.04", "-u", "root", "--",
         "bash", "-c", "while true; do sleep 300; done"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    try:
        KEEPALIVE_PID_FILE.write_text(str(_wsl_keepalive_proc.pid))
    except Exception:
        pass
    print(f"  ✓ WSL2 keepalive started (PID {_wsl_keepalive_proc.pid})")


def _stop_wsl2_keepalive():
    global _wsl_keepalive_proc
    if _wsl_keepalive_proc and _wsl_keepalive_proc.poll() is None:
        _wsl_keepalive_proc.terminate()
        print("  Stopped WSL2 keepalive")
        _wsl_keepalive_proc = None
    if KEEPALIVE_PID_FILE.exists():
        try:
            pid = int(KEEPALIVE_PID_FILE.read_text().strip())
            if IS_WINDOWS:
                subprocess.run(["taskkill", "/F", "/PID", str(pid)],
                               capture_output=True, timeout=5)
            else:
                os.kill(pid, 9)
            print(f"  Stopped prior WSL2 keepalive (PID {pid})")
        except Exception:
            pass
        KEEPALIVE_PID_FILE.unlink(missing_ok=True)


def ensure_age_available(dsn: str) -> bool:
    if verify_age(dsn):
        print("  ✓ AGE connection verified")
        _start_wsl2_keepalive()
        return True
    print("  AGE not reachable. Checking WSL2...")
    if not start_wsl2_postgres():
        print()
        print("  ╔════════════════════════════════════════════╗")
        print("  ║  AGE/PostgreSQL is not available.          ║")
        print("  ║                                            ║")
        print("  ║  Manual fix (Rule #38):                    ║")
        print("  ║  1. wsl -d Ubuntu-24.04 -u root            ║")
        print("  ║  2. service postgresql start                ║")
        print("  ║  3. Keep that terminal open                ║")
        print("  ║  4. Re-run demo.py                        ║")
        print("  ╚════════════════════════════════════════════╝")
        return False
    for attempt in range(5):
        time.sleep(2)
        if verify_age(dsn):
            print("  ✓ AGE connection verified")
            return True
        print(f"  Waiting for AGE... ({attempt + 1}/5)")
    print("  ✗ AGE not reachable after PostgreSQL start")
    return False


def wait_for_health(name: str, port: int, timeout: int = 30) -> bool:
    for i in range(timeout):
        time.sleep(1)
        h = check_health(port)
        if h:
            status = h.get("status", "ok")
            domain = h.get("domain", "")
            print(f"  ✓ {name}: {status} {domain}")
            return True
    print(f"  ✗ {name}: not healthy after {timeout}s on :{port}")
    return False


def wait_for_frontend(name: str, port: int, timeout: int = 15) -> bool:
    for _ in range(timeout):
        time.sleep(1)
        if check_port(port):
            print(f"  ✓ {name} frontend ready on :{port}")
            return True
    print(f"  ✗ {name} frontend not ready on :{port} after {timeout}s")
    return False


def find_pids_on_port(port: int) -> list[int]:
    pids: set[int] = set()
    target_port = str(port)
    try:
        result = subprocess.run(
            ["netstat", "-ano"],
            capture_output=True, text=True, timeout=5,
        )
        for line in result.stdout.splitlines():
            parts = line.split()
            if len(parts) < 5 or parts[0].upper() != "TCP":
                continue
            if parts[-2].upper() != "LISTENING":
                continue
            local_address = parts[1]
            if _port_from_local_address(local_address) != target_port:
                continue
            try:
                pids.add(int(parts[-1]))
            except ValueError:
                pass
    except Exception as e:
        print(f"  WARN: Could not inspect port :{port}: {e}")
    return sorted(pids)


def _port_from_local_address(local_address: str) -> str | None:
    if local_address.startswith("[") and "]:" in local_address:
        return local_address.rsplit("]:", 1)[-1]
    if ":" not in local_address:
        return None
    return local_address.rsplit(":", 1)[-1]


def kill_port(port: int, name: str = "") -> bool:
    pids = find_pids_on_port(port)
    if not pids:
        return False
    attempted = False
    for pid in pids:
        try:
            attempted = True
            if IS_WINDOWS:
                result = subprocess.run(
                    ["taskkill", "/F", "/PID", str(pid)],
                    capture_output=True, text=True, timeout=5,
                )
                if result.returncode != 0:
                    message = (result.stderr or result.stdout or "").strip()
                    print(f"  WARN: Could not stop PID {pid} on :{port}: {message}")
                    continue
            else:
                os.kill(pid, 9)
            label = f" ({name})" if name else ""
            print(f"  Killed stale PID {pid} on :{port}{label}")
        except Exception as e:
            print(f"  WARN: Could not stop PID {pid} on :{port}: {e}")
    return attempted


def known_ports(selected: list[dict] | None = None) -> list[int]:
    copilots = selected or COPILOTS
    ports: list[int] = []
    for c in copilots:
        ports.append(c["be_port"])
        if c.get("fe_port") is not None:
            ports.append(c["fe_port"])
    return ports


# --- Commands ---

def cmd_stop(selected: list[dict]):
    print("Stopping copilots...")
    for c in selected:
        kill_port(c["be_port"], f"{c['name']} backend")
        if c.get("fe_port") is not None:
            kill_port(c["fe_port"], f"{c['name']} frontend")
    _stop_wsl2_keepalive()
    time.sleep(2)
    print("Done.")


def cmd_kill_all():
    print("Killing all copilot port listeners...")
    killed_any = False
    for port in known_ports():
        killed_any = kill_port(port) or killed_any
    if not killed_any:
        print("  No copilot port listeners found.")
    print("Done.")


def cmd_reset(target: str, selected: list[dict], data_root: Path = DEFAULT_DATA_DIR):
    """Reset persistent data. Stops affected copilots first."""
    print()
    if target == "ALL":
        # Stop all persistent copilots before wiping
        for c in selected:
            if c.get("persistent") and check_port(c["be_port"]):
                print(f"  Stopping {c['name']} before reset...")
                kill_port(c["be_port"], f"{c['name']} backend")
                if c.get("fe_port") is not None:
                    kill_port(c["fe_port"], f"{c['name']} frontend")
        time.sleep(1)
        if data_root.exists():
            shutil.rmtree(data_root)
            print(f"  Reset: wiped {data_root} (all copilots)")
        else:
            print("  Reset: no persistent data to wipe")
    else:
        target_lower = target.lower()
        for c in COPILOTS:
            if c["name"].lower() == target_lower and check_port(c["be_port"]):
                print(f"  Stopping {c['name']} before reset...")
                kill_port(c["be_port"], f"{c['name']} backend")
                if c.get("fe_port") is not None:
                    kill_port(c["fe_port"], f"{c['name']} frontend")
                time.sleep(1)
                break
        copilot_dir = data_root / target_lower
        if copilot_dir.exists():
            shutil.rmtree(copilot_dir)
            print(f"  Reset: wiped {copilot_dir}")
        else:
            print(f"  Reset: no data for {target}")
    print()


def cmd_status(selected: list[dict], data_root: Path = DEFAULT_DATA_DIR, args=None):
    print()
    print("╔══════════════════════════════════════════════════════╗")
    print("║  Copilot Platform Status                             ║")
    print("╚══════════════════════════════════════════════════════╝")

    age_ok = verify_age(AGE_DSN_SOC)
    wsl_ok = verify_wsl2_running()
    print(f"  AGE/PostgreSQL  {'UP ✓' if age_ok else 'DOWN ✗':8s}  "
          f"WSL2 {'running' if wsl_ok else 'stopped'}")
    print()

    for c in selected:
        be_up = check_port(c["be_port"])
        fe_port = c.get("fe_port")
        fe_up = check_port(fe_port) if fe_port is not None else False
        h = check_health(c["be_port"]) if be_up else None

        be_status = "UP ✓" if h else ("UP ?" if be_up else "DOWN")
        fe_status = "UP ✓" if fe_up else ("N/A" if fe_port is None else "DOWN")
        fe_label = f":{fe_port}" if fe_port is not None else "N/A"
        domain = h.get("domain", "") if h else ""
        graph_label = _active_graph_status_label(c["name"], args=args)

        print(f"  {c['name']:12s}  backend :{c['be_port']} {be_status:8s}"
              f"  frontend {fe_label:>5s} {fe_status:8s}"
              f"  {domain} [{graph_label}]")

    # Persistent data
    print()
    print("  Persistent Data:")
    has_any = False
    for c in selected:
        if c.get("persistent"):
            has_any = True
            stats = _read_copilot_data_stats(c, data_root)
            if not stats["db_exists"]:
                print(f"    {c['name']:12s}  no data (will auto-seed on first start)")
            else:
                parts = [f"{stats['decisions']} decisions"]
                if stats["archived"] > 0:
                    parts.append(f"+{stats['archived']} archived")
                db_path = _copilot_db_path(c, data_root)
                if db_path and db_path.exists():
                    size_kb = db_path.stat().st_size // 1024
                    parts.append(f"{size_kb}KB")
                print(f"    {c['name']:12s}  {', '.join(parts)}")
        elif c.get("requires_age"):
            has_any = True
            print(f"    {c['name']:12s}  managed by AGE (PostgreSQL)")
    if not has_any:
        print("    (no persistent copilots selected)")
    print()


def cmd_start(selected: list[dict], args, data_root: Path = DEFAULT_DATA_DIR):
    print()
    print("╔══════════════════════════════════════════════════════╗")
    print(f"║  Starting {len(selected)} copilot(s)...                        ║")
    print("╚══════════════════════════════════════════════════════╝")
    print()

    prepared: list[dict] = []
    for c in selected:
        try:
            prepared.append({"copilot": c, "env": _prepare_copilot_env(c, args)})
        except RuntimeError as exc:
            print(f"  ✗ {c['name']} AGE startup aborted: {_redact_dsn(str(exc))}")
            return

    # AGE pre-check
    age_dsns = _age_precheck_dsns(prepared, args)
    if age_dsns or args.graph:
        dsns_to_check = age_dsns or [AGE_DSN_DATAOPS]
        print("Checking AGE/PostgreSQL...")
        for dsn in dsns_to_check:
            if not ensure_age_available(dsn):
                print()
                print("Cannot start AGE-dependent copilots. Exiting.")
                if any(item["copilot"].get("requires_age") for item in prepared) and not any(
                    _active_age_dsn_from_env(item["copilot"], item["env"], args)
                    for item in prepared
                ):
                    non_age = [item for item in prepared if not item["copilot"].get("requires_age")]
                    if non_age:
                        print(f"Starting {len(non_age)} non-AGE copilot(s) instead...")
                        prepared = non_age
                        break
                    return
                return
        print()

    if args.graph:
        setup_graph_mode()

    # Start backends
    print("Starting backends...")
    started: list[dict] = []
    for item in prepared:
        c = item["copilot"]
        env = item["env"]
        port = c["be_port"]
        kill_port(port, f"{c['name']} backend")
        if check_port(port):
            print(f"  {c['name']} backend already on :{port}")
            started.append(item)
            continue

        be_path = c["be_path"]
        if not (be_path / "app" / "main.py").exists():
            print(f"  ✗ {c['name']}: main.py not found at {be_path}")
            continue

        # Persistent storage: pass data DIRECTORY to backend.
        # Backend constructs its own db filename (e.g. trading.db).
        if c.get("persistent"):
            copilot_dir = _copilot_data_dir(c["name"], data_root)
            _maybe_migrate_dev_db(c, copilot_dir, data_root)
            env["CI_DATA_DIR"] = str(copilot_dir)

        proc = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "app.main:app",
              "--host", "127.0.0.1", "--port", str(port)],
              cwd=str(be_path),
              env=env,
              creationflags=CREATE_FLAGS,
        )
        print(f"  {c['name']} backend starting on :{port} (PID {proc.pid})")
        started.append(item)

    # Wait for health
    print()
    print("Waiting for backends...")
    all_healthy = True
    for item in started:
        c = item["copilot"]
        timeout = 60 if c.get("requires_age") else 30
        if not wait_for_health(c["name"], c["be_port"], timeout=timeout):
            all_healthy = False

    if not all_healthy:
        print()
        print("Some backends failed. Check the console windows for errors.")

    # Pre-seed (deprecated)
    if args.preseed:
        print()
        print("  NOTE: --preseed is deprecated. Backends auto-seed on first start.")
        print("  Use --reset to wipe and re-seed on next start.")
        print("  Running legacy preseed for backward compatibility...")
        run_preseed([item["copilot"] for item in started])

    # Start frontends
    print()
    print("Starting frontends...")
    for item in started:
        c = item["copilot"]
        fe_port = c.get("fe_port")
        if fe_port is None:
            print(f"  {c['name']} has no frontend; skipping")
            continue
        kill_port(fe_port, f"{c['name']} frontend")
        if check_port(fe_port):
            print(f"  {c['name']} frontend already on :{fe_port}")
            continue
        fe_path = c.get("fe_path")
        if not fe_path or not (fe_path / "package.json").exists():
            print(f"  ✗ {c['name']}: package.json not found at {fe_path}")
            continue
        subprocess.Popen(
            ["npx", "vite", "--port", str(fe_port), "--host", "127.0.0.1"],
            cwd=str(fe_path),
            creationflags=CREATE_FLAGS,
            shell=IS_WINDOWS,
        )
        print(f"  {c['name']} frontend starting on :{fe_port}")

    # Wait for frontends
    print()
    print("Waiting for frontends...")
    for item in started:
        c = item["copilot"]
        fe_port = c.get("fe_port")
        if fe_port is not None:
            wait_for_frontend(c["name"], fe_port, timeout=15)

    # Open browsers
    if not args.no_browser:
        urls = []
        for item in started:
            c = item["copilot"]
            fe_port = c.get("fe_port")
            if fe_port is not None:
                urls.append((c["name"], f"http://localhost:{fe_port}"))
        if urls:
            print()
            print("Opening browsers...")
            url_list = [url for _, url in urls]
            edge = Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe")
            chrome = Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe")
            if edge.exists():
                subprocess.Popen([str(edge), "--inprivate"] + url_list)
                print("  Opened in Edge InPrivate:")
            elif chrome.exists():
                subprocess.Popen([str(chrome), "--incognito"] + url_list)
                print("  Opened in Chrome Incognito:")
            else:
                for _, url in urls:
                    webbrowser.open_new_tab(url)
                    time.sleep(1)
                print("  Opened in default browser:")
            for name, url in urls:
                print(f"    {name}: {url}")

    # Summary
    print()
    print("╔══════════════════════════════════════════════════════╗")
    print("║  Platform Ready                                      ║")
    print("╚══════════════════════════════════════════════════════╝")
    for item in started:
        c = item["copilot"]
        fe_port = c.get("fe_port")
        graph_label = _active_graph_status_label(c["name"], args=args)
        persist_flag = " [persistent]" if c.get("persistent") else ""
        if fe_port is None:
            print(f"  {c['name']:12s}  backend http://localhost:{c['be_port']} [{graph_label}]")
        else:
            print(f"  {c['name']:12s}  http://localhost:{fe_port}"
                  f"  (backend :{c['be_port']}) [{graph_label}]{persist_flag}")
    print()
    print("  Stop:       python demo.py --stop")
    print("  Status:     python demo.py --status")
    print("  Reset:      python demo.py --reset [copilot]")
    print("  Playwright: python demo.py --playwright --no-browser")
    print()


def setup_graph_mode():
    print("Setting up graph mode...")
    os.environ["GRAPH_DSN"] = AGE_DSN_DATAOPS
    seed_script = CI_PLATFORM / "scripts" / "seed_dataops_graph.py"
    if seed_script.exists():
        print("  Seeding DataOps graph...")
        try:
            subprocess.run(
                [sys.executable, str(seed_script), "--force"],
                cwd=str(CI_PLATFORM), timeout=30, check=True,
            )
            print("  ✓ Graph seeded")
        except Exception as e:
            print(f"  WARN: Graph seed failed: {e}")
            del os.environ["GRAPH_DSN"]
    else:
        print(f"  WARN: Seed script not found: {seed_script}")
    print()


def run_preseed(selected: list[dict]):
    """Run pre-seeding script (deprecated — backends auto-seed now)."""
    print()
    print("Pre-seeding copilots...")
    script = SCRIPT_DIR / "scripts" / "preseed_all_copilots.py"
    if not script.exists():
        print(f"  WARN: Pre-seed script not found: {script}")
        return
    cmd = [sys.executable, str(script)]
    preseed_names = {"trading", "purchasing", "dataops"}
    names = {c["name"].lower() for c in selected if c["name"].lower() in preseed_names}
    if not names:
        print("  No selected copilots support pre-seed; skipping")
        return
    if names != preseed_names:
        for name in names:
            cmd.append(f"--{name}-only")
    try:
        subprocess.run(cmd, cwd=str(SCRIPT_DIR), timeout=600)
    except Exception as e:
        print(f"  WARN: Pre-seed failed: {e}")
    print()


# --- Main ---

def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Compounding Intelligence Platform Launcher",
    )
    parser.add_argument("--stop", action="store_true", help="Stop all copilots")
    parser.add_argument("--status", action="store_true", help="Show status")
    parser.add_argument("--kill-all", action="store_true",
                        help="Kill listeners on all known copilot ports")
    parser.add_argument("--reset", nargs="?", const="ALL", default=None,
                        help="Reset persistent data. No arg=all, or specify copilot name")

    parser.add_argument("--soc", action="store_true", help="SOC only")
    parser.add_argument("--trading", action="store_true", help="Trading only")
    parser.add_argument("--purchasing", action="store_true", help="Purchasing only")
    parser.add_argument("--dataops", action="store_true", help="DataOps only")
    parser.add_argument("--s2p", action="store_true", help="S2P only")

    parser.add_argument("--sdk", action="store_true",
                        help="SDK copilots only (Trading + Purchasing + DataOps)")
    parser.add_argument("--playwright", action="store_true",
                        help="Playwright prereqs only (SOC + S2P)")

    for app_name in ("trading", "purchasing", "dataops", "s2p"):
        parser.add_argument(
            f"--{app_name}-graph-backend",
            choices=("sqlite", "age"),
            default=None,
            help=f"{app_name.title()} scorer graph backend override",
        )

    parser.add_argument("--graph", action="store_true", help="AGE graph mode for DataOps")
    parser.add_argument("--replay-outbox", action="store_true", default=False,
                        help="Attempt outbox replay if a replay worker is available")
    parser.add_argument("--preseed", action="store_true",
                        help="Pre-seed after start (deprecated: backends auto-seed)")
    parser.add_argument("--no-browser", action="store_true", help="Don't open browsers")
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR,
                        help=f"Override data directory (default: {DEFAULT_DATA_DIR})")
    return parser


def main():
    parser = create_parser()
    args = parser.parse_args()
    data_root = args.data_dir

    # Select copilots
    individual = args.soc or args.trading or args.purchasing or args.dataops or args.s2p
    group = args.sdk or args.playwright
    if individual or group:
        selected_names = set()
        if args.soc:
            selected_names.add("soc")
        if args.trading:
            selected_names.add("trading")
        if args.purchasing:
            selected_names.add("purchasing")
        if args.dataops:
            selected_names.add("dataops")
        if args.s2p:
            selected_names.add("s2p")
        if args.sdk:
            selected_names |= SDK_NAMES
        if args.playwright:
            selected_names |= PLAYWRIGHT_NAMES
        selected = [c for c in COPILOTS if c["name"].lower() in selected_names]
    else:
        selected = list(COPILOTS)

    # Handle reset FIRST (combinable with other actions)
    if args.reset is not None:
        cmd_reset(args.reset, selected, data_root)

    _run_replay_outbox_if_requested(args.replay_outbox)

    # Dispatch
    if args.kill_all:
        cmd_kill_all()
    elif args.stop:
        cmd_stop(selected)
    elif args.status:
        cmd_status(selected, data_root, args=args)
    elif args.reset is not None:
        # Reset already done above, no other action → exit
        pass
    else:
        cmd_start(selected, args, data_root)


if __name__ == "__main__":
    main()
