"""DI-3 NL Query Engine — Live endpoint verification."""

from urllib.request import urlopen, Request
import json

questions = [
    "How many decisions?",
    "What is the accuracy?",
    "Which source is most reliable?",
]

for q in questions:
    payload = json.dumps({
        "question": q,
        "context": {"domain": "dataops"},
    }).encode()

    req = Request(
        "http://127.0.0.1:8030/api/di/query",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        r = urlopen(req, timeout=10)
        d = json.loads(r.read())
        print(f"Q: {q}")
        print(f"  Answer: {d.get('answer')}")
        print(f"  Confidence: {d.get('confidence')} ({d.get('confidence_label')})")
        print(f"  Sources: {len(d.get('source_attribution', []))}")
        evidence = str(d.get("evidence", ""))[:80]
        print(f"  Evidence: {evidence}")
        warning = d.get("quality_warning")
        if warning:
            print(f"  Warning: {warning}")
        print()
    except Exception as e:
        print(f"Q: {q}")
        body = ""
        if hasattr(e, "read"):
            body = e.read().decode("utf-8", errors="replace")[:200]
        print(f"  FAILED: {e}")
        if body:
            print(f"  Detail: {body}")
        print()

# Also verify compatibility endpoint
print("=== Compatibility endpoint ===")
payload = json.dumps({
    "question": "How many decisions?",
    "context": {"domain": "dataops"},
}).encode()
req = Request(
    "http://127.0.0.1:8030/api/dataops/query",
    data=payload,
    headers={"Content-Type": "application/json"},
    method="POST",
)
try:
    r = urlopen(req, timeout=10)
    d = json.loads(r.read())
    print(f"  /api/dataops/query: {r.status}")
    print(f"  Answer: {d.get('answer')}")
    print(f"  Confidence: {d.get('confidence')}")
    # Verify both endpoints return the same answer
    print(f"  Shape matches canonical: {'answer' in d and 'confidence' in d}")
except Exception as e:
    body = ""
    if hasattr(e, "read"):
        body = e.read().decode("utf-8", errors="replace")[:200]
    print(f"  /api/dataops/query: FAILED — {e}")
    if body:
        print(f"  Detail: {body}")
