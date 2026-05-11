"""
Add create_conservation_router to Trading and Purchasing backends.
Pattern copied from DataOps main.py.
"""
import os, re

SDK_ROOT = r"C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\kaggle_experiments\claude_projects\copilot-sdk"

def fix_main(copilot):
    path = os.path.join(SDK_ROOT, "apps", copilot, "backend", "app", "main.py")
    with open(path, encoding="utf-8") as f:
        content = f.read()

    if "create_conservation_router" in content:
        print(f"{copilot}: conservation router already present. Skipping.")
        return

    # 1. Add create_conservation_router to SDK import
    old_import = "from copilot_sdk.backend import create_scoring_router"
    if "create_evolution_router" in content:
        old_import = re.search(r"from copilot_sdk\.backend import [^\n]+", content).group(0)

    if "create_conservation_router" not in old_import:
        # Add to existing import
        new_import = old_import.replace(
            "from copilot_sdk.backend import",
            "from copilot_sdk.backend import create_conservation_router,"
        )
        content = content.replace(old_import, new_import)

    # 2. Add conservation state provider before the app setup
    # Find the line with create_scoring_router and add conservation after the scoring router block
    lines = content.split("\n")
    new_lines = []
    added_provider = False
    added_router = False

    for i, line in enumerate(lines):
        new_lines.append(line)

        # Add state provider function before app.include_router(create_scoring_router(
        if not added_provider and "create_scoring_router(" in line:
            # Find the right spot - add provider before this block
            # Insert conservation state provider before the scoring router
            pass

        # Add router mounting after the scoring router block
        if not added_router and "app.include_router(context_router" in line:
            # Insert conservation router BEFORE context_router
            indent = "    "
            new_lines.insert(-1, "")
            new_lines.insert(-1, f"{indent}# Conservation router")
            new_lines.insert(-1, f'{indent}app.include_router(')
            new_lines.insert(-1, f'{indent}    create_conservation_router("{copilot}"),')
            new_lines.insert(-1, f'{indent}    prefix="/api/conservation",')
            new_lines.insert(-1, f'{indent})')
            added_router = True

    if added_router:
        content = "\n".join(new_lines)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"{copilot}: conservation router ADDED.")
    else:
        print(f"{copilot}: could not find insertion point. Manual fix needed.")
        print(f"  Add these lines before context_router mounting:")
        print(f'    app.include_router(')
        print(f'        create_conservation_router("{copilot}"),')
        print(f'        prefix="/api/conservation",')
        print(f'    )')

fix_main("trading")
fix_main("purchasing")

print("\nDone. Restart backends and verify:")
print('  Invoke-RestMethod "http://localhost:8010/api/conservation/status"')
print('  Invoke-RestMethod "http://localhost:8020/api/conservation/status"')
