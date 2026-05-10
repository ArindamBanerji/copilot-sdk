p = 'trading/dashboard.spec.ts'
with open(p) as f:
    s = f.read()
old = 'await expect(page.getByText("Win Rate")).toBeVisible();'
new = 'await expect(page.getByText("Win Rate", { exact: true }).first()).toBeVisible();'
if old in s:
    s = s.replace(old, new)
    with open(p, 'w') as f:
        f.write(s)
    print("Fixed")
else:
    print("Text not found")
