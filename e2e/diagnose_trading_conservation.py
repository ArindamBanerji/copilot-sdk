"""
Diagnose and fix Trading conservation endpoint.
Run from copilot-sdk root.
"""
import os, re

SDK_ROOT = r"C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\kaggle_experiments\claude_projects\copilot-sdk"

# 1. Check which backends mount conservation router
for copilot in ["trading", "purchasing", "dataops"]:
    main_path = os.path.join(SDK_ROOT, "apps", copilot, "backend", "app", "main.py")
    if os.path.exists(main_path):
        with open(main_path, encoding="utf-8") as f:
            content = f.read()
        has_conservation = "conservation" in content.lower()
        print(f"{copilot} main.py: conservation={'YES' if has_conservation else 'NO'}")
        # Show router includes
        for line in content.split("\n"):
            if "router" in line.lower() or "include" in line.lower() or "mount" in line.lower():
                print(f"  {line.strip()}")
    else:
        print(f"{copilot} main.py: NOT FOUND")

# 2. Check SDK conservation router
conservation_path = os.path.join(SDK_ROOT, "copilot_sdk", "backend", "conservation_router.py")
if os.path.exists(conservation_path):
    print(f"\nSDK conservation_router.py: EXISTS")
    with open(conservation_path, encoding="utf-8") as f:
        for line in f.readlines()[:20]:
            if "router" in line.lower() or "prefix" in line.lower() or "def " in line:
                print(f"  {line.rstrip()}")
else:
    print(f"\nSDK conservation_router.py: NOT FOUND")
    # Check alternative locations
    for root, dirs, files in os.walk(os.path.join(SDK_ROOT, "copilot_sdk")):
        for f in files:
            if "conserv" in f.lower():
                print(f"  Found: {os.path.join(root, f)}")

# 3. Check what Purchasing does that Trading doesn't
print("\n--- Purchasing main.py conservation wiring ---")
p_main = os.path.join(SDK_ROOT, "apps", "purchasing", "backend", "app", "main.py")
if os.path.exists(p_main):
    with open(p_main, encoding="utf-8") as f:
        for i, line in enumerate(f.readlines()):
            if "conserv" in line.lower() or "router" in line.lower():
                print(f"  L{i+1}: {line.rstrip()}")

print("\n--- Trading main.py full router setup ---")
t_main = os.path.join(SDK_ROOT, "apps", "trading", "backend", "app", "main.py")
if os.path.exists(t_main):
    with open(t_main, encoding="utf-8") as f:
        for i, line in enumerate(f.readlines()):
            if "router" in line.lower() or "include" in line.lower() or "app." in line:
                print(f"  L{i+1}: {line.rstrip()}")
