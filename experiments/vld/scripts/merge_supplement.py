"""Merge DataOps base (50) + supplement (25) = 75 scenarios."""
import json, sys

base_path = sys.argv[1] if len(sys.argv) > 1 else "dataops_multihop_stage1.json"
sup_path = sys.argv[2] if len(sys.argv) > 2 else "dataops_strong_conditional_supplement_25.json"
out_path = sys.argv[3] if len(sys.argv) > 3 else "dataops_multihop_stage1_merged_75.json"

with open(base_path, encoding="utf-8") as f:
    base = json.load(f)
with open(sup_path, encoding="utf-8") as f:
    sup = json.load(f)

base["scenarios"].extend(sup["scenarios"])
base["_stage"] = "Stage 1: 50 base + 25 supplement = 75 DataOps instances"

with open(out_path, "w", encoding="utf-8") as f:
    json.dump(base, f, indent=2)

n = len(base["scenarios"])
print("Merged: " + str(n) + " scenarios -> " + out_path)
