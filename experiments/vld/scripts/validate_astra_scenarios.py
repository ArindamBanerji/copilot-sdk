"""Validate Astra-generated Stage 1 scenarios — any copilot."""
import json, collections, sys

path = sys.argv[1] if len(sys.argv) > 1 else "scenarios.json"
d = json.load(open(path, encoding="utf-8"))

if "scenarios" not in d:
    print("FAIL: no 'scenarios' key. Keys: " + str(list(d.keys())))
    sys.exit(1)

S = d["scenarios"]
fails = []

print("Instances: " + str(len(S)))
if len(S) == 0:
    print("FAIL: 0 scenarios")
    sys.exit(1)

print("Provenance: " + str(d.get("provenance", "MISSING")))
if d.get("provenance") != "sample":
    fails.append("Missing provenance: sample")

# Copilot
copilots = set(x.get("copilot", "?") for x in S)
print("Copilot(s): " + str(copilots))

# Kinds
kinds = collections.Counter(x["branching_kind"] for x in S)
print("Kinds: " + str(dict(kinds)))

# Rho
rhos = collections.Counter(x["rho_planted"] for x in S)
print("Rho dist: " + str(dict(sorted(rhos.items()))))
low_rho = [x["scenario_id"] for x in S if x["rho_planted"] < 0.30]
if low_rho:
    print("WARNING: " + str(len(low_rho)) + " below 0.30")

# Actions
actions = collections.Counter(x["decision_tree"]["ground_truth_action"] for x in S)
print("Actions: " + str(dict(actions)))
n_actions = len(actions)
print("Action count: " + str(n_actions) + " (chance = " + str(round(1/n_actions, 3)) + ")")
missing_actions = [a for a, c in actions.items() if c < 3]
if missing_actions:
    print("WARNING: actions with <3 instances: " + str(missing_actions))

# Factors
sample = S[0]["alert"]["surface_factors"]
fkeys = sorted(sample.keys())
print("Factors: " + str(fkeys) + " (" + str(len(fkeys)) + ")")

# IDs
ids = [x["scenario_id"] for x in S]
if len(ids) != len(set(ids)):
    fails.append("Duplicate IDs")
    print("WARNING: duplicate IDs!")
else:
    print("IDs: all unique")

# Schema
required_all = ["scenario_id", "copilot", "branching_kind", "rho_planted",
                "alert", "available_branches", "correct_branches", "budget",
                "decision_tree"]
required_nonflat = ["graph_nodes", "graph_edges"]
schema_fails = 0
for s in S:
    is_flat = s.get("surface_only_resolvable", False)
    check = required_all if is_flat else required_all + required_nonflat
    missing = [f for f in check if f not in s]
    if missing:
        schema_fails += 1
        print("  Schema: " + str(s.get("scenario_id", "?")) + " missing " + str(missing))
    dt = s.get("decision_tree", {})
    if "ground_truth_action" not in dt:
        schema_fails += 1
    if not is_flat:
        hops = dt.get("hops", [])
        if not hops:
            schema_fails += 1
            print("  Schema: " + str(s.get("scenario_id", "?")) + " non-flat but hops empty")
print("Schema issues: " + str(schema_fails))
if schema_fails > 0:
    fails.append(str(schema_fails) + " schema issues")

# Factor shifts
weak_shifts = 0
for s in S:
    if s.get("surface_only_resolvable"):
        continue
    surface = s["alert"]["surface_factors"]
    for hop in s["decision_tree"].get("hops", []):
        ef = hop.get("factor_enriched")
        nv = hop.get("factor_new_value")
        if ef and nv is not None and ef in surface:
            shift = abs(nv - surface[ef])
            if shift < 0.15:
                weak_shifts += 1
                print("  Weak: " + s["scenario_id"] + " " + ef + " shift=" + str(round(shift, 2)))
print("Weak shifts (<0.15): " + str(weak_shifts))
if weak_shifts > 3:
    fails.append(str(weak_shifts) + " weak shifts")

# Overlaps
overlap_count = 0
for s in S:
    enriched = [h.get("factor_enriched") for h in s["decision_tree"].get("hops", []) if h.get("factor_enriched")]
    if len(enriched) != len(set(enriched)):
        overlap_count += 1
        print("  Overlap: " + s["scenario_id"])
print("Factor overlap: " + str(overlap_count) + "/" + str(len(S)))
if overlap_count > 0:
    fails.append(str(overlap_count) + " factor overlaps")

# Flat controls
flats = [s for s in S if s.get("surface_only_resolvable")]
print("Flat controls: " + str(len(flats)))
if len(flats) < 5:
    fails.append("Only " + str(len(flats)) + " flat controls (need 5)")

# Rho=0.50 controls
rho50 = [s for s in S if s["rho_planted"] == 0.50 and not s.get("surface_only_resolvable")]
print("Rho=0.50 controls: " + str(len(rho50)))
if len(rho50) < 5:
    fails.append("Only " + str(len(rho50)) + " rho=0.50 controls (need 5)")

# Hop distribution
hop_counts = collections.Counter(len(s["decision_tree"].get("hops", [])) for s in S)
print("Hop dist: " + str(dict(sorted(hop_counts.items()))))

# Summary
if len(S) != 50:
    fails.append("Expected 50, got " + str(len(S)))

print("")
if not fails:
    print("PASS: " + str(len(S)) + " instances, " + str(weak_shifts) + " weak, " + str(overlap_count) + " overlaps")
else:
    print("FAIL:")
    for f in fails:
        print("  " + f)
