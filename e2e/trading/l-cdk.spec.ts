import { expect, test } from "@playwright/test";
import { readFile } from "node:fs/promises";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const repoRoot = resolve(dirname(fileURLToPath(import.meta.url)), "../..");

async function readRepoFile(relativePath: string): Promise<string> {
  return readFile(resolve(repoRoot, relativePath), "utf-8");
}

test.describe("L-CDK SDK developer cut", () => {
  test("L-CDK: SDK scaffold documentation is accessible", async () => {
    const [quickstart, gettingStarted] = await Promise.all([
      readRepoFile("docs/quickstart.md"),
      readRepoFile("docs/getting-started.md"),
    ]);
    expect(quickstart).toMatch(/quickstart|5-minute|install/i);
    expect(gettingStarted).toMatch(/getting started|scaffold|developer/i);
  });

  test("L-CDK: hello-gae and build-your-own references exist", async () => {
    const scenario = await readRepoFile("docs/design/product/demo_scenarios_and_usecases_v2_7.md");
    expect(scenario).toMatch(/hello-gae/i);
    expect(scenario).toMatch(/build-your-own/i);
  });

  test("L-CDK: open-source SDK developer entry point exists", async () => {
    const [scaffoldMain, scaffoldGenerator] = await Promise.all([
      readRepoFile("copilot_sdk/scaffold/__main__.py"),
      readRepoFile("copilot_sdk/scaffold/generator.py"),
    ]);
    expect(scaffoldMain).toMatch(/scaffold|generate/i);
    expect(scaffoldGenerator).toMatch(/CopilotScaffold|open-source|developer/i);
  });
});
