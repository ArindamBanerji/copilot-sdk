"""Check if gold line source/target IDs match node IDs."""

from urllib.request import urlopen
import json

r = urlopen("http://127.0.0.1:8030/api/di/intelligence-map", timeout=5)
d = json.loads(r.read())

node_ids = {n.get("id") for n in d.get("nodes", [])}
print("Node IDs:", sorted(node_ids))
print()

gold_lines = d.get("gold_lines", [])
print(f"Gold lines: {len(gold_lines)}")
for gl in gold_lines:
    src = gl.get("source", "?")
    tgt = gl.get("target", "?")
    val = gl.get("value", 0)
    src_ok = src in node_ids
    tgt_ok = tgt in node_ids
    status = "OK" if (src_ok and tgt_ok) else "BROKEN"
    print(f"  {status}: {src} ({'found' if src_ok else 'MISSING'}) -> {tgt} ({'found' if tgt_ok else 'MISSING'}): ${val:,.0f}")

if not gold_lines:
    print("  NO GOLD LINES RETURNED")

print()
print("Nodes by type:")
by_type = {}
for n in d.get("nodes", []):
    t = n.get("type", "unknown")
    by_type.setdefault(t, []).append(n.get("id", "?"))
for t, ids in sorted(by_type.items()):
    print(f"  {t}: {ids[:5]}{'...' if len(ids) > 5 else ''}")

edges = d.get("edges", [])
print(f"\nEdges: {len(edges)}")
if edges:
    print(f"  Sample: {edges[0]}")
