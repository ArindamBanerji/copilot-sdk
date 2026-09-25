import os, json

key = os.environ.get("ANTHROPIC_API_KEY", "")
print(f"Key: {key[:15]}... ({len(key)} chars)" if key else "NOT SET")

if not key:
    print("Set it first: $env:ANTHROPIC_API_KEY = 'sk-ant-...'")
else:
    import anthropic
    print(f"anthropic package: {anthropic.__version__}")
    client = anthropic.Anthropic()
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=10,
        messages=[{"role": "user", "content": "Reply with exactly: HELLO"}]
    )
    print(f"Response: {response.content[0].text}")
    print(f"Model: {response.model}")
    print("API OK — ready for K2 generation")
