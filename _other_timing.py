import time, urllib.request

for name, port, endpoints in [
    ("PURCHASING", 8020, [
        "/health",
        "/api/conservation/status",
        "/api/purchasing/waste/analysis",
        "/api/purchasing/waste/summary",
        "/api/self/accuracy-by-category",
        "/api/self/centroid-history",
        "/api/self/decisions",
    ]),
    ("DATAOPS", 8030, [
        "/health",
        "/api/conservation/status",
        "/api/context/pipelines",
        "/api/context/transformations/snowflake",
        "/api/context/process-timeline",
        "/api/self/accuracy-by-category",
        "/api/self/decisions",
    ]),
]:
    print(f"=== {name} (:{port}) ===")
    for r in range(2):
        print(f"Round {r+1}:")
        for ep in endpoints:
            s = time.time()
            try:
                urllib.request.urlopen(f"http://127.0.0.1:{port}{ep}", timeout=60)
                t = time.time() - s
                ok = "OK" if t < 2.0 else "SLOW"
                print(f"  {t:.2f}s  {ok}  {ep}")
            except Exception as e:
                t = time.time() - s
                print(f"  {t:.2f}s  ERR  {ep}: {type(e).__name__}")
        print()
