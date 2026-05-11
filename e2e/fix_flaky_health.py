import os

p = os.path.join(
    "C:\\Users\\baner\\CopyFolder\\IoT_thoughts\\python-projects",
    "kaggle_experiments\\claude_projects\\copilot-sdk\\e2e",
    "fixtures\\copilot-fixture.ts"
)

with open(p, encoding="utf-8") as f:
    content = f.read()

# Find the health check try/catch block and add retry logic
old = """      const resp = await request.get(healthUrl);
      if (!resp.ok()) {
        throw new Error(
          `${projectName} backend returned ${resp.status()} at ${healthUrl}. Start the live stack before running E2E tests.`,
        );
      }
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      throw new Error(
        `${projectName} backend is not healthy at ${healthUrl}. Start the live stack before running E2E tests. ${message}`,
      );
    }"""

new = """      let lastError: string = "";
      for (let attempt = 0; attempt < 3; attempt++) {
        try {
          const resp = await request.get(healthUrl);
          if (resp.ok()) {
            lastError = "";
            break;
          }
          lastError = `${projectName} backend returned ${resp.status()} at ${healthUrl}.`;
        } catch (err) {
          lastError = err instanceof Error ? err.message : String(err);
        }
        if (attempt < 2) await new Promise((r) => setTimeout(r, 1000 * (attempt + 1)));
      }
      if (lastError) {
        throw new Error(
          `${projectName} backend is not healthy at ${healthUrl}. Start the live stack before running E2E tests. ${lastError}`,
        );
      }
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      throw new Error(
        `${projectName} backend is not healthy at ${healthUrl}. Start the live stack before running E2E tests. ${message}`,
      );
    }"""

if old in content:
    content = content.replace(old, new)
    with open(p, "w", encoding="utf-8") as f:
        f.write(content)
    print("Fixed: added 3-attempt retry with backoff to health check.")
else:
    print("Exact text not found. Showing lines around health check:")
    lines = content.split("\n")
    for i, line in enumerate(lines):
        if "healthUrl" in line or "backendHealth" in line:
            print(f"  {i+1}: {line}")
