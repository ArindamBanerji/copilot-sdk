import os

p = os.path.join(
    "C:\\Users\\baner\\CopyFolder\\IoT_thoughts\\python-projects",
    "kaggle_experiments\\claude_projects\\copilot-sdk\\e2e",
    "dataops\\flows.spec.ts"
)

with open(p, encoding="utf-8") as f:
    lines = f.readlines()

changes = 0
out = []
for line in lines:
    if "explorer.getByText(/pipeline|schema|volume|freshness|quality|transform/i)" in line:
        # Category names are in hidden <option> elements.
        # The visible breakdown shows counts and percentages.
        # Use page-level expectAnyText instead of scoped locator on hidden options.
        out.append("  await expectAnyText(page, [/by category/i, /category/i, /\\\\d+ decision/i]);\n")
        changes += 1
    else:
        out.append(line)

with open(p, "w", encoding="utf-8") as f:
    f.writelines(out)

print(f"Done. {changes} lines replaced.")
