#!/usr/bin/env python3
"""
Compounding Intelligence Platform Launcher.

Usage:
    python demo.py                  # Start everything, open browsers
    python demo.py --stop           # Stop all copilot processes
    python demo.py --status         # Show what's running
    python demo.py --dataops        # DataOps only
    python demo.py --preseed        # Pre-seed after start
    python demo.py --graph          # AGE graph mode for DataOps
    python demo.py --no-browser     # Don't open browser tabs
"""

import argparse
import json
import os
import subprocess
import sys
import time
import webbrowser
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# --- Configuration ---

SCRIPT_DIR = Path(__file__).resolve().parent
CI_PLATFORM = SCRIPT_DIR.parent / "ci-platform"

IS_WINDOWS = sys.platform == "win32"
CREATE_FLAGS = subprocess.CREATE_NEW_CONSOLE if IS_WINDOWS else 0

COPILOTS = [
    {
        "name": "Trading",
        "be_port": 8010,
        "fe_port": 5174,
        "be_path": SCRIPT_DIR / "apps" / "trading" / "backend",
        "fe_path": SCRIPT_DIR / "apps" / "trading" / "frontend",
    },
    {
        "name": "Purchasing",
        "be_port": 8020,
        "fe_port": 5175,
        "be_path": SCRIPT_DIR / "apps" / "purchasing" / "backend",
        "fe_path": SCRIPT_DIR / "apps" / "purchasing" / "frontend",
    },
    {
        "name": "DataOps",
        "be_port": 8030,
        "fe_port": 5176,
        "be_path": SCRIPT_DIR / "apps" / "dataops" / "backend",
        "fe_path": SCRIPT_DIR / "apps" / "dataops" / "frontend",
    },
    {
        "name": "S2P",
        "be_port": 8002,
        "fe_port": None,
        "be_path": Path(os.environ.get("CLAUDE_S2P", str(SCRIPT_DIR.parent / "s2p-copilot"))) / "backend",
        "fe_path": None,
        "health_path": "/health",
    },
]


# --- Helpers ---

def check_port(port: int) -> bool:
    """Check if a port is responding to HTTP."""
    try:
        urlopen(f"http://localhost:{port}/", timeout=2)
        return True
    except Exception:
        # Port might be open but not HTTP — try raw connect
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(1)
        try:
            s.connect(("localhost", port))
            s.close()
            return True
        except Exception:
            return False


def check_health(port: int) -> dict | None:
    """Check backend /health endpoint."""
    try:
        r = urlopen(f"http://localhost:{port}/health", timeout=5)
        return json.loads(r.read())
    except Exception:
        return None


def wait_for_health(name: str, port: int, timeout: int = 30) -> bool:
    """Poll /health until healthy or timeout."""
    for i in range(timeout):
        time.sleep(1)
        h = check_health(port)
        if h and h.get("status") == "ok":
            print(f"  ✓ {name}: {h['status']} ({h.get('domain', '?')})")
            return True
    print(f"  ✗ {name}: not healthy after {timeout}s on :{port}")
    return False


def wait_for_frontend(name: str, port: int, timeout: int = 15) -> bool:
    """Poll frontend port until it responds or timeout."""
    for _ in range(timeout):
        time.sleep(1)
        if check_port(port):
            print(f"  ✓ {name} frontend ready on :{port}")
            return True
    print(f"  ✗ {name} frontend not ready on :{port} after {timeout}s")
    return False


def find_pids_on_port(port: int) -> list[int]:
    """Find process IDs listening on a port."""
    pids: set[int] = set()
    target_port = str(port)
    try:
        result = subprocess.run(
            ["netstat", "-ano"],
            capture_output=True, text=True, timeout=5
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
    """Extract the port from netstat's local address column."""
    if local_address.startswith("[") and "]:" in local_address:
        return local_address.rsplit("]:", 1)[-1]
    if ":" not in local_address:
        return None
    return local_address.rsplit(":", 1)[-1]


def kill_port(port: int, name: str = "") -> bool:
    """Kill processes on a specific port."""
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
                    capture_output=True, text=True, timeout=5
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
    """Return configured backend and frontend ports without duplicating constants."""
    copilots = selected or COPILOTS
    ports: list[int] = []
    for c in copilots:
        ports.append(c["be_port"])
        if c["fe_port"] is not None:
            ports.append(c["fe_port"])
    return ports


# --- Commands ---

def cmd_stop(selected: list[dict]):
    """Stop all selected copilot processes."""
    print("Stopping copilots...")
    for c in selected:
        kill_port(c["be_port"], f"{c['name']} backend")
        if c["fe_port"] is not None:
            kill_port(c["fe_port"], f"{c['name']} frontend")
    time.sleep(2)
    print("Done.")


def cmd_kill_all():
    """Kill listeners on all configured copilot ports."""
    print("Killing all copilot port listeners...")
    killed_any = False
    for port in known_ports():
        killed_any = kill_port(port) or killed_any
    if not killed_any:
        print("  No copilot port listeners found.")
    print("Done.")


def cmd_status(selected: list[dict]):
    """Show status of selected copilots."""
    print()
    print("╔══════════════════════════════════════════════╗")
    print("║  Copilot Platform Status                     ║")
    print("╚══════════════════════════════════════════════╝")
    for c in selected:
        be_up = check_port(c["be_port"])
        fe_port = c["fe_port"]
        fe_up = check_port(fe_port) if fe_port is not None else False
        h = check_health(c["be_port"]) if be_up else None

        be_status = "UP ✓" if h else ("UP ?" if be_up else "DOWN")
        fe_status = "UP ✓" if fe_up else ("N/A" if fe_port is None else "DOWN")
        fe_label = f":{fe_port}" if fe_port is not None else "N/A"
        domain = h.get("domain", "") if h else ""

        print(f"  {c['name']:12s}  backend :{c['be_port']} {be_status:8s}"
              f"  frontend {fe_label:>5s} {fe_status:8s}"
              f"  {domain}")
    print()


def cmd_start(selected: list[dict], args):
    """Start selected copilots."""
    print()
    print("╔══════════════════════════════════════════════╗")
    print(f"║  Starting {len(selected)} copilot(s)...                    ║")
    print("╚══════════════════════════════════════════════╝")
    print()

    # --- Graph mode ---
    if args.graph:
        setup_graph_mode()

    # --- Start backends ---
    print("Starting backends...")
    procs = {}
    for c in selected:
        port = c["be_port"]
        kill_port(port, f"{c['name']} backend")
        if check_port(port):
            print(f"  {c['name']} backend already on :{port}")
            continue

        be_path = c["be_path"]
        if not (be_path / "app" / "main.py").exists():
            print(f"  ✗ {c['name']}: main.py not found at {be_path}")
            continue

        proc = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "app.main:app",
             "--host", "127.0.0.1", "--port", str(port)],
            cwd=str(be_path),
            creationflags=CREATE_FLAGS,
        )
        procs[c["name"]] = proc
        print(f"  {c['name']} backend starting on :{port} (PID {proc.pid})")

    # --- Wait for health ---
    print()
    print("Waiting for backends...")
    all_healthy = True
    for c in selected:
        if not wait_for_health(c["name"], c["be_port"], timeout=30):
            all_healthy = False

    if not all_healthy:
        print()
        print("Some backends failed. Check the console windows for errors.")
        return

    # --- Pre-seed ---
    if args.preseed:
        run_preseed(selected)

    # --- Start frontends ---
    print()
    print("Starting frontends...")
    for c in selected:
        if c["fe_port"] is None:
            print(f"  {c['name']} has no frontend; skipping")
            continue
        port = c["fe_port"]
        kill_port(port, f"{c['name']} frontend")
        if check_port(port):
            print(f"  {c['name']} frontend already on :{port}")
            continue

        fe_path = c["fe_path"]
        if not (fe_path / "package.json").exists():
            print(f"  ✗ {c['name']}: package.json not found at {fe_path}")
            continue

        subprocess.Popen(
            ["npx", "vite", "--port", str(port), "--host", "127.0.0.1"],
            cwd=str(fe_path),
            creationflags=CREATE_FLAGS,
            shell=IS_WINDOWS,  # npx needs shell on Windows
        )
        print(f"  {c['name']} frontend starting on :{port}")

    # --- Wait for frontends to be ready ---
    print()
    print("Waiting for frontends...")
    for c in selected:
        if c["fe_port"] is None:
            continue
        wait_for_frontend(c["name"], c["fe_port"], timeout=15)

    # --- Open browsers ---
    if not args.no_browser:
        urls = []
        for c in selected:
            if c["fe_port"] is not None:
                urls.append((c["name"], f"http://localhost:{c['fe_port']}"))
        if urls:
            print()
            print("Opening browsers...")
            url_list = [url for _, url in urls]

            # Edge InPrivate: reliable multi-tab in one call (pre-installed on Windows)
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

    # --- Summary ---
    print()
    print("╔══════════════════════════════════════════════╗")
    print("║  Platform Ready                              ║")
    print("╚══════════════════════════════════════════════╝")
    for c in selected:
        if c["fe_port"] is None:
            print(f"  {c['name']:12s}  backend http://localhost:{c['be_port']}")
        else:
            print(f"  {c['name']:12s}  http://localhost:{c['fe_port']}"
                  f"  (backend :{c['be_port']})")
    print()
    print("  Stop:   python demo.py --stop")
    print("  Status: python demo.py --status")
    print()


def setup_graph_mode():
    """Set GRAPH_DSN and optionally seed the DataOps graph."""
    print("Setting up graph mode...")
    dsn = "host=localhost port=5433 dbname=soc_graph user=postgres password=postgres"
    os.environ["GRAPH_DSN"] = dsn

    seed_script = CI_PLATFORM / "scripts" / "seed_dataops_graph.py"
    if seed_script.exists():
        print("  Seeding DataOps graph...")
        try:
            subprocess.run(
                [sys.executable, str(seed_script), "--force"],
                cwd=str(CI_PLATFORM),
                timeout=30,
                check=True,
            )
            print("  ✓ Graph seeded")
        except Exception as e:
            print(f"  WARN: Graph seed failed: {e}")
            del os.environ["GRAPH_DSN"]
    else:
        print(f"  WARN: Seed script not found: {seed_script}")

    print()


def run_preseed(selected: list[dict]):
    """Run pre-seeding script."""
    print()
    print("Pre-seeding copilots...")
    script = SCRIPT_DIR / "scripts" / "preseed_all_copilots.py"
    if not script.exists():
        print(f"  WARN: Pre-seed script not found: {script}")
        return

    cmd = [sys.executable, str(script)]

    # Pass subset flags if not all copilots selected
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

def main():
    parser = argparse.ArgumentParser(
        description="Compounding Intelligence Platform Launcher"
    )
    parser.add_argument("--stop", action="store_true", help="Stop all copilots")
    parser.add_argument("--status", action="store_true", help="Show status")
    parser.add_argument("--trading", action="store_true", help="Trading only")
    parser.add_argument("--purchasing", action="store_true", help="Purchasing only")
    parser.add_argument("--dataops", action="store_true", help="DataOps only")
    parser.add_argument("--s2p", action="store_true", help="S2P backend only")
    parser.add_argument("--graph", action="store_true", help="AGE graph mode")
    parser.add_argument("--preseed", action="store_true", help="Pre-seed after start")
    parser.add_argument("--no-browser", action="store_true", help="Don't open browsers")
    parser.add_argument("--kill-all", action="store_true",
                        help="Kill listeners on all known copilot ports")

    args = parser.parse_args()

    # Select copilots
    do_all = not (args.trading or args.purchasing or args.dataops or args.s2p)
    selected = []
    for c in COPILOTS:
        name_lower = c["name"].lower()
        if do_all or getattr(args, name_lower, False):
            selected.append(c)

    if args.kill_all:
        cmd_kill_all()
    elif args.stop:
        cmd_stop(selected)
    elif args.status:
        cmd_status(selected)
    else:
        cmd_start(selected, args)


if __name__ == "__main__":
    main()
