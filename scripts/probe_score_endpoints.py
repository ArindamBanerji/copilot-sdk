"""
Probe script for /api/score (DataOps) and /api/s2p/score (S2P).
Captures full HTTP response (status, headers, body) to diagnose
whether payloads are malformed vs endpoints unimplemented.

Run: python probe_score_endpoints.py
Requires: requests (pip install requests)
Backends must be running: DataOps on 8030, S2P on 8002.
"""

import json
import sys
import requests

DATAOPS = "http://127.0.0.1:8030"
S2P = "http://127.0.0.1:8002"

PROBES = [
    {
        "label": "MACH-01 (DataOps /api/score — billing_api data_quality)",
        "url": f"{DATAOPS}/api/score",
        "payload": {
            "alert_id": "MACH-TRACE-001",
            "system": "billing_api",
            "severity": "high",
            "category": "data_quality",
            "description": "Decision trace test — schema mismatch in downstream join",
        },
    },
    {
        "label": "MACH-02 (DataOps /api/score — novel system)",
        "url": f"{DATAOPS}/api/score",
        "payload": {
            "alert_id": "MACH-NOVEL-001",
            "system": "unknown_system_novel",
            "severity": "critical",
            "category": "data_quality",
            "description": "Novel alert pattern with no prior precedent in system",
        },
    },
    {
        "label": "MACH-06 (S2P /api/s2p/score — price_variance)",
        "url": f"{S2P}/api/s2p/score",
        "payload": {
            "event_id": "MACH-INV-001",
            "category": "price_variance",
            "factors": {
                "match_status": 0.85,
                "amount_variance_ratio": 0.05,
                "duplicate_score": 0.02,
                "supplier_exception_history": 0.90,
                "payment_terms_impact": 0.80,
                "commodity_index_correlation": 0.75,
                "tax_regulatory_compliance": 0.92,
            },
        },
    },
    {
        "label": "S2P-01 (S2P /api/s2p/score — price_variance, INV-0001)",
        "url": f"{S2P}/api/s2p/score",
        "payload": {
            "event_id": "S2P-INV-0001",
            "category": "price_variance",
            "factors": {
                "match_status": 0.85,
                "amount_variance_ratio": 0.08,
                "duplicate_score": 0.02,
                "supplier_exception_history": 0.90,
                "payment_terms_impact": 0.80,
                "commodity_index_correlation": 0.75,
                "tax_regulatory_compliance": 0.92,
            },
        },
    },
    {
        "label": "S2P-02 (S2P /api/s2p/score — quantity_mismatch, INV-FIRST)",
        "url": f"{S2P}/api/s2p/score",
        "payload": {
            "event_id": "S2P-INV-FIRST",
            "category": "quantity_mismatch",
            "factors": {
                "match_status": 0.95,
                "amount_variance_ratio": 0.03,
                "duplicate_score": 0.01,
                "supplier_exception_history": 0.94,
                "payment_terms_impact": 0.85,
                "commodity_index_correlation": 0.80,
                "tax_regulatory_compliance": 0.99,
            },
        },
    },
]


def probe(entry):
    label = entry["label"]
    url = entry["url"]
    payload = entry["payload"]
    print(f"\n{'='*70}")
    print(f"PROBE: {label}")
    print(f"POST {url}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    print(f"{'='*70}")
    try:
        resp = requests.post(url, json=payload, timeout=10)
        print(f"Status: {resp.status_code}")
        print(f"Content-Type: {resp.headers.get('content-type', 'N/A')}")
        try:
            body = resp.json()
            print(f"Body (JSON):\n{json.dumps(body, indent=2)}")
        except Exception:
            print(f"Body (text):\n{resp.text[:2000]}")

        if resp.status_code == 200:
            print("VERDICT: ENDPOINT WORKS — un-skip candidate")
        elif resp.status_code == 422:
            print("VERDICT: 422 Validation Error — check required fields")
        elif resp.status_code == 400:
            print("VERDICT: 400 Bad Request — check payload shape")
        elif resp.status_code == 404:
            print("VERDICT: 404 Not Found — endpoint not mounted")
        elif resp.status_code == 405:
            print("VERDICT: 405 Method Not Allowed — endpoint exists but wrong method")
        elif resp.status_code == 500:
            print("VERDICT: 500 Internal Server Error — endpoint exists but crashes")
        else:
            print(f"VERDICT: Unexpected status {resp.status_code}")
    except requests.exceptions.ConnectionError:
        print("VERDICT: CONNECTION REFUSED — backend not running")
    except requests.exceptions.Timeout:
        print("VERDICT: TIMEOUT — backend not responding")
    except Exception as e:
        print(f"VERDICT: ERROR — {e}")


def main():
    print("Score Endpoint Probe — DataOps (:8030) + S2P (:8002)")
    print(f"Probing {len(PROBES)} endpoints...\n")

    results = {}
    for entry in PROBES:
        probe(entry)
        results[entry["label"]] = True

    print(f"\n{'='*70}")
    print("SUMMARY")
    print(f"{'='*70}")
    print("Run complete. Review verdicts above.")
    print("If 200: un-skip the test in the spec file.")
    print("If 422/400 with validation detail: fix payload shape and un-skip.")
    print("If 404/500/connection refused: keep skipped.")


if __name__ == "__main__":
    main()
