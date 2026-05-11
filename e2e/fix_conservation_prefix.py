import os

SDK_ROOT = r"C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\kaggle_experiments\claude_projects\copilot-sdk"

for copilot in ["trading", "purchasing"]:
    path = os.path.join(SDK_ROOT, "apps", copilot, "backend", "app", "main.py")
    with open(path, encoding="utf-8") as f:
        content = f.read()
    
    old = '        prefix="/api/conservation",'
    new = '        prefix="/api",'
    
    if old in content:
        content = content.replace(old, new)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"{copilot}: fixed prefix /api/conservation -> /api")
    else:
        print(f"{copilot}: pattern not found, check manually")
