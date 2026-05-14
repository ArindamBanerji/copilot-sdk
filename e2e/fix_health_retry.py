"""Fix copilot-fixture.ts health check to retry 3 times with 2s backoff.

Run from copilot-sdk/e2e/:
    python fix_health_retry.py
"""
from pathlib import Path

p = Path("fixtures/copilot-fixture.ts")
c = p.read_text(encoding="utf-8")

if "attempt" in c:
    print("ALREADY FIXED")
    raise SystemExit(0)

# Find the try/catch block and wrap it in a retry loop
old_lines = [
    "      try {",
    '        const response = await request.get(healthUrl, { timeout: 5_000 });',
]

# Check the pattern exists
if old_lines[0] in c and old_lines[1] in c:
    # Strategy: find the "try {" that contains healthUrl and wrap it
    lines = c.split("\n")
    try_idx = None
    for i, line in enumerate(lines):
        if line.strip() == "try {" and i + 1 < len(lines) and "healthUrl" in lines[i + 1]:
            try_idx = i
            break

    if try_idx is None:
        print("NOT FOUND: could not locate try block with healthUrl")
        raise SystemExit(1)

    # Find the matching catch
    catch_idx = None
    for i in range(try_idx + 1, len(lines)):
        if lines[i].strip().startswith("} catch"):
            catch_idx = i
            break

    if catch_idx is None:
        print("NOT FOUND: could not locate catch block")
        raise SystemExit(1)

    # Find the throw new Error inside catch (the final rethrow)
    throw_idx = None
    for i in range(catch_idx + 1, len(lines)):
        if "throw new Error(" in lines[i]:
            throw_idx = i
            break

    if throw_idx is None:
        print("NOT FOUND: could not locate throw inside catch")
        raise SystemExit(1)

    # Get indentation
    indent = "      "

    # Build new lines
    new_lines = []
    # Everything before the try
    new_lines.extend(lines[:try_idx])
    # Add retry loop
    new_lines.append(f"{indent}for (let attempt = 0; attempt < 3; attempt++) {{")
    # Re-indent the try block
    new_lines.append(f"{indent}  try {{")
    for i in range(try_idx + 1, catch_idx):
        new_lines.append("  " + lines[i])
    # Add break after successful health check
    new_lines.append(f"{indent}    break;")
    # catch with retry logic
    new_lines.append(f"{indent}  }} catch (error) {{")
    new_lines.append(f"{indent}    if (attempt < 2) {{")
    new_lines.append(f"{indent}      await new Promise(r => setTimeout(r, 2000));")
    new_lines.append(f"{indent}      continue;")
    new_lines.append(f"{indent}    }}")
    # Original catch body (message extraction + throw)
    for i in range(catch_idx + 1, len(lines)):
        # Find the closing brace of the original catch
        stripped = lines[i].strip()
        new_lines.append("  " + lines[i])
        if stripped == "}" and i > throw_idx:
            # This is the closing brace of the catch — also close the for loop
            new_lines.append(f"{indent}}}")
            # Add everything after
            new_lines.extend(lines[i + 1:])
            break

    result = "\n".join(new_lines)
    p.write_text(result, encoding="utf-8")
    print("FIXED: health check now retries 3 times with 2s backoff")
else:
    print("NOT FOUND: expected pattern missing from file")
