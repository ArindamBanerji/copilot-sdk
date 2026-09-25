import time, urllib.request, socket

print("=== PORT CHECK ===")
for port in [8010, 8020, 8030, 8002, 8001]:
    try:
        s = socket.create_connection(("127.0.0.1", port), timeout=5)
        s.close()
        print(f"  {port}: UP")
    except:
        print(f"  {port}: DOWN — wait and retry")

print()
print("=== QUICK TIMING (warm-up + verify) ===")
for r in range(2):
    print(f"Round {r+1}:")
    for name, port, ep in [
        ("Trading", 8010, "/api/context/analytics"),
        ("Purchasing", 8020, "/api/purchasing/waste/summary"),
        ("DataOps", 8030, "/api/context/pipelines"),
        ("S2P", 8002, "/api/s2p/preview/queue"),
        ("SOC", 8001, "/api/conservation/status"),
    ]:
        s = time.time()
        try:
            urllib.request.urlopen(f"http://127.0.0.1:{port}{ep}", timeout=30)
            t = time.time() - s
            ok = "OK" if t < 2.0 else "SLOW"
            print(f"  {t:.2f}s  {ok}  {name}")
        except Exception as e:
            print(f"  ERR  {name}: {type(e).__name__}")
    print()
