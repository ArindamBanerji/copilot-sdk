p = 'helpers/capture-content.ts'
with open(p) as f:
    s = f.read()

s = s.replace(
    'import * as path from "path";\n',
    ''
)
s = s.replace(
    'const outPath = path.join(__dirname, "..", `tab-content-${config.name}.json`);',
    'const outPath = `C:\\\\Users\\\\baner\\\\CopyFolder\\\\IoT_thoughts\\\\python-projects\\\\kaggle_experiments\\\\claude_projects\\\\copilot-sdk\\\\e2e\\\\tab-content-${config.name}.json`;'
)
s = s.replace(
    'const combinedPath = path.join(__dirname, "..", "tab-content-all.json");',
    'const combinedPath = `C:\\\\Users\\\\baner\\\\CopyFolder\\\\IoT_thoughts\\\\python-projects\\\\kaggle_experiments\\\\claude_projects\\\\copilot-sdk\\\\e2e\\\\tab-content-all.json`;'
)

with open(p, 'w') as f:
    f.write(s)
print("Fixed")
