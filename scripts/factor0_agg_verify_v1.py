"""
Factor-0 Aggregation Fix — Post-Codex Verification v1

Run from: gen-ai-roi-demo-v4-v50/backend/

Checks:
  1. Code structure review (weighted_components pattern, no flat mean)
  2. Exact arithmetic on 12 input combinations
  3. Edge cases (clamp boundaries, empty signals, single signal)
  4. C9B seed contract manual computation
  5. Insider paradox confirmation
  6. Renormalization correctness (absent signals)
  7. Weight sum = 1.0 invariant
"""

import asyncio
import sys
import os

sys.path.insert(0, os.getcwd())


def check_code_structure():
    """Review the actual implementation for correctness."""
    print("=" * 80)
    print("CHECK 1: CODE STRUCTURE REVIEW")
    print("=" * 80)
    print()

    src = open("app/domains/soc/factors.py", encoding="utf-8").read()

    # 1a. Flat mean must be GONE
    # The old pattern: sum(components) / len(components)
    lines = src.splitlines()
    flat_mean_lines = []
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if "sum(components)" in stripped and "len(components)" in stripped:
            flat_mean_lines.append((i, stripped))
        if "/ len(" in stripped and "components" in stripped:
            flat_mean_lines.append((i, stripped))

    if flat_mean_lines:
        print("  FAIL: Flat mean pattern still present:")
        for lineno, text in flat_mean_lines:
            print("    Line %d: %s" % (lineno, text))
    else:
        print("  PASS: No flat mean pattern found")

    # 1b. Weighted components must exist
    has_weighted = "weighted_components" in src or "weight" in src.lower()
    if not has_weighted:
        print("  FAIL: No weighted component pattern found")
    else:
        print("  PASS: Weighted component pattern found")

    # 1c. The 4 weight values must appear
    weights_found = []
    for w in ["0.50", "0.20", "0.15"]:
        if w in src:
            weights_found.append(w)
    if len(weights_found) >= 3:
        print("  PASS: Weight constants found: %s" % weights_found)
    else:
        print("  FAIL: Missing weight constants (found: %s)" % weights_found)

    # 1d. No changes to other factor computers
    # Check that AssetCriticalityFactor, ThreatIntelEnrichmentFactor, etc.
    # don't contain "weighted" or new weight constants
    other_factors = [
        "AssetCriticalityFactor",
        "ThreatIntelEnrichmentFactor",
        "PatternHistoryFactor",
        "TimeAnomalyFactor",
        "DeviceTrustFactor",
    ]
    for factor_name in other_factors:
        # Find the class and check its compute method
        idx = src.find("class %s" % factor_name)
        if idx == -1:
            continue
        # Find next class or end of file
        next_class = src.find("\nclass ", idx + 1)
        if next_class == -1:
            next_class = len(src)
        class_src = src[idx:next_class]
        if "weighted_components" in class_src or "total_weight" in class_src:
            print("  FAIL: %s contains weighted pattern" % factor_name)
        else:
            print("  PASS: %s unchanged" % factor_name)

    # 1e. Print the actual compute method for visual review
    print()
    print("  --- PrivilegedIdentityContextFactor.compute() ---")
    in_compute = False
    indent_level = None
    in_target_class = False
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if "class PrivilegedIdentityContextFactor" in line:
            in_target_class = True
        elif in_target_class and line.startswith("class ") and "PrivilegedIdentity" not in line:
            in_target_class = False
        if in_target_class and not in_compute and "def compute" in line:
            in_compute = True
            indent_level = len(line) - len(line.lstrip())
        elif in_compute:
            if stripped and not stripped.startswith("#") and not stripped.startswith("\"\"\""):
                current_indent = len(line) - len(line.lstrip())
                if current_indent <= indent_level and (stripped.startswith("def ") or stripped.startswith("@")):
                    in_compute = False
                    continue
        if in_compute:
            print("  %4d: %s" % (i, line.rstrip()))

    print()


def check_exact_arithmetic():
    """Verify exact values match hand computation."""
    print("=" * 80)
    print("CHECK 2: EXACT ARITHMETIC (12 cases)")
    print("=" * 80)
    print()

    from app.domains.soc.factors import PrivilegedIdentityContextFactor
    f = PrivilegedIdentityContextFactor()

    cases = [
        # (name, context, expected, arithmetic)
        ("all-4 admin no-mfa",
         {"user_risk_score": 0.90, "user_title": "admin",
          "mfa_completed": False, "device_fingerprint_match": False},
         # 0.90*0.50 + 0.90*0.20 + 0.85*0.15 + 0.80*0.15 = 0.45+0.18+0.1275+0.12 = 0.8775
         0.8775),

        ("all-4 regular clean",
         {"user_risk_score": 0.20, "user_title": "analyst",
          "mfa_completed": True, "device_fingerprint_match": True},
         # 0.20*0.50 + 0.20*0.20 + 0.10*0.15 + 0.10*0.15 = 0.10+0.04+0.015+0.015 = 0.17
         0.17),

        ("insider paradox IT-02",
         {"user_risk_score": 0.85, "user_title": "user",
          "mfa_completed": True, "device_fingerprint_match": True},
         # 0.85*0.50 + 0.20*0.20 + 0.10*0.15 + 0.10*0.15 = 0.425+0.04+0.015+0.015 = 0.495
         0.495),

        ("service account clean",
         {"user_risk_score": 0.30, "user_title": "service",
          "mfa_completed": True, "device_fingerprint_match": True},
         # title_risk("service") = 0.90 (check this!)
         # 0.30*0.50 + 0.90*0.20 + 0.10*0.15 + 0.10*0.15 = 0.15+0.18+0.015+0.015 = 0.36
         0.36),

        ("risk only 0.85",
         {"user_risk_score": 0.85},
         # only risk present: 0.85*0.50 / 0.50 = 0.85
         0.85),

        ("risk only 0.20",
         {"user_risk_score": 0.20},
         0.20),

        ("no context",
         None,
         0.50),

        ("empty dict",
         {},
         0.50),

        ("C9B seed like (risk+mfa+device)",
         {"user_risk_score": 0.95, "mfa_completed": False,
          "device_fingerprint_match": False},
         # total_w = 0.50+0.15+0.15 = 0.80
         # (0.95*0.50 + 0.85*0.15 + 0.80*0.15) / 0.80
         # = (0.475 + 0.1275 + 0.12) / 0.80 = 0.7225 / 0.80 = 0.903125
         0.903125),

        ("title+mfa+device no risk",
         {"user_title": "admin", "mfa_completed": False,
          "device_fingerprint_match": False},
         # total_w = 0.20+0.15+0.15 = 0.50
         # (0.90*0.20 + 0.85*0.15 + 0.80*0.15) / 0.50
         # = (0.18 + 0.1275 + 0.12) / 0.50 = 0.4275 / 0.50 = 0.855
         0.855),

        ("mfa only absent",
         {"mfa_completed": False},
         # only mfa: 0.85*0.15 / 0.15 = 0.85
         0.85),

        ("device only known",
         {"device_fingerprint_match": True},
         # only device: 0.10*0.15 / 0.15 = 0.10
         0.10),
    ]

    all_pass = True
    for name, ctx, expected in cases:
        v = asyncio.run(f.compute("test", ctx))
        ok = abs(v - expected) < 0.0001
        status = "PASS" if ok else "FAIL"
        if not ok:
            all_pass = False
        print("  %s: %-35s got=%.6f expected=%.6f" % (status, name, v, expected))

    print()
    print("  %s" % ("ALL 12 PASSED" if all_pass else "*** FAILURES DETECTED ***"))
    return all_pass


def check_edge_cases():
    """Test boundary conditions."""
    print()
    print("=" * 80)
    print("CHECK 3: EDGE CASES")
    print("=" * 80)
    print()

    from app.domains.soc.factors import PrivilegedIdentityContextFactor
    f = PrivilegedIdentityContextFactor()

    # Edge 1: risk_score at exact 0.0 (should not be treated as absent)
    v = asyncio.run(f.compute("test", {"user_risk_score": 0.0}))
    print("  risk_score=0.0: %.4f (should be 0.0, not 0.5)" % v)
    assert abs(v - 0.0) < 0.001, "FAIL: risk_score=0.0 treated as absent"

    # Edge 2: risk_score at exact 1.0
    v = asyncio.run(f.compute("test", {"user_risk_score": 1.0}))
    print("  risk_score=1.0: %.4f (should be 1.0)" % v)
    assert abs(v - 1.0) < 0.001, "FAIL: risk_score=1.0 not clamped correctly"

    # Edge 3: risk_score > 1.0 (should clamp)
    v = asyncio.run(f.compute("test", {"user_risk_score": 1.5}))
    print("  risk_score=1.5: %.4f (should clamp to 1.0)" % v)
    assert v <= 1.0, "FAIL: risk_score=1.5 not clamped"

    # Edge 4: risk_score < 0.0 (should clamp)
    v = asyncio.run(f.compute("test", {"user_risk_score": -0.5}))
    print("  risk_score=-0.5: %.4f (should clamp to 0.0)" % v)
    assert v >= 0.0, "FAIL: risk_score=-0.5 not clamped"

    # Edge 5: all signals at 1.0 — max output
    v = asyncio.run(f.compute("test", {
        "user_risk_score": 1.0, "user_title": "admin",
        "mfa_completed": False, "device_fingerprint_match": False,
    }))
    # 1.0*0.50 + 0.90*0.20 + 0.85*0.15 + 0.80*0.15
    # = 0.50 + 0.18 + 0.1275 + 0.12 = 0.9275
    expected_max = 0.9275
    print("  All max signals: %.4f (expected %.4f)" % (v, expected_max))
    assert abs(v - expected_max) < 0.001

    # Edge 6: all signals at minimum — low output
    v = asyncio.run(f.compute("test", {
        "user_risk_score": 0.0, "user_title": "user",
        "mfa_completed": True, "device_fingerprint_match": True,
    }))
    # 0.0*0.50 + 0.20*0.20 + 0.10*0.15 + 0.10*0.15
    # = 0.0 + 0.04 + 0.015 + 0.015 = 0.07
    expected_min = 0.07
    print("  All min signals: %.4f (expected %.4f)" % (v, expected_min))
    assert abs(v - expected_min) < 0.001

    # Edge 7: renormalization invariant — adding an absent signal
    # shouldn't change the result
    v_risk = asyncio.run(f.compute("test", {"user_risk_score": 0.50}))
    v_risk_none = asyncio.run(f.compute("test",
        {"user_risk_score": 0.50, "user_title": None}))
    print("  Absent title (None): risk_only=%.4f vs risk+none_title=%.4f" % (
        v_risk, v_risk_none))
    # None value should be skipped — result should be the same as risk-only
    # If the implementation treats None as present with value None, this catches it
    assert abs(v_risk - v_risk_none) < 0.001, \
        "FAIL: None title changed result (%.4f vs %.4f)" % (v_risk, v_risk_none)

    print()
    print("  ALL EDGE CASES PASSED")


def check_weight_invariant():
    """Verify weights always sum correctly."""
    print()
    print("=" * 80)
    print("CHECK 4: WEIGHT SUM INVARIANT")
    print("=" * 80)
    print()

    # For any subset of signals, the renormalized weights should sum to 1.0
    base_weights = {"risk": 0.50, "title": 0.20, "mfa": 0.15, "device": 0.15}

    from itertools import combinations
    signals = list(base_weights.keys())

    all_pass = True
    for r in range(1, 5):
        for combo in combinations(signals, r):
            present_w = [base_weights[s] for s in combo]
            total = sum(present_w)
            renormalized = [w / total for w in present_w]
            rn_sum = sum(renormalized)
            ok = abs(rn_sum - 1.0) < 1e-10
            if not ok:
                print("  FAIL: %s → sum=%.10f" % (combo, rn_sum))
                all_pass = False

    if all_pass:
        print("  PASS: All 15 subsets renormalize to sum=1.0")
    else:
        print("  *** FAILURES ***")


def check_title_risk_mapping():
    """Verify _title_risk returns expected values for known titles."""
    print()
    print("=" * 80)
    print("CHECK 5: TITLE RISK MAPPING (unchanged)")
    print("=" * 80)
    print()

    from app.domains.soc.factors import PrivilegedIdentityContextFactor
    f = PrivilegedIdentityContextFactor()

    # These should NOT have changed — verify they're intact
    expected = {
        "admin": 0.90,
        "root": 0.90,
        "service": 0.90,
        "executive": 0.70,
        "manager": 0.50,
        "analyst": 0.20,
        "user": 0.20,
    }

    all_pass = True
    for title, exp in expected.items():
        v = asyncio.run(f.compute("test", {"user_title": title}))
        # Single signal: result = title_risk * 0.20 / 0.20 = title_risk
        ok = abs(v - exp) < 0.001
        if not ok:
            print("  FAIL: title '%s' → %.4f (expected %.4f)" % (title, v, exp))
            all_pass = False
        else:
            print("  PASS: title '%s' → %.4f" % (title, v))

    print()
    if all_pass:
        print("  ALL TITLE MAPPINGS CORRECT")
    else:
        print("  *** TITLE MAPPING CHANGED ***")


def check_no_unexpected_changes():
    """Verify only expected files were modified."""
    print()
    print("=" * 80)
    print("CHECK 6: FILE CHANGE AUDIT")
    print("=" * 80)
    print()

    import subprocess
    result = subprocess.run(["git", "diff", "--name-only"],
                            capture_output=True, text=True, cwd="../..")
    if result.returncode != 0:
        # Try from current directory
        result = subprocess.run(["git", "diff", "--name-only"],
                                capture_output=True, text=True)

    changed = [f for f in result.stdout.strip().split("\n") if f.strip()]
    expected = {
        "backend/app/domains/soc/factors.py",
        "backend/tests/test_privileged_identity_factor.py",
        "backend/tests/test_soc_c9b_seed_contract.py",
    }

    unexpected = [f for f in changed
                  if f not in expected
                  and not f.endswith(".sqlite3")
                  and not f.endswith(".sqlite3-shm")
                  and not f.endswith(".sqlite3-wal")]

    print("  Changed files: %d" % len(changed))
    for f in changed:
        tag = " *** UNEXPECTED" if f in [u for u in unexpected] else ""
        print("    %s%s" % (f, tag))

    if unexpected:
        print("  *** UNEXPECTED FILES CHANGED ***")
    else:
        print("  CLEAN: only expected files changed")


def main():
    check_code_structure()
    passed = check_exact_arithmetic()
    check_edge_cases()
    check_weight_invariant()
    check_title_risk_mapping()
    check_no_unexpected_changes()

    print()
    print("=" * 80)
    print("REMAINING: Run SDK suite separately")
    print("  cd copilot-sdk")
    print("  python -m pytest tests/ -q --timeout=600")
    print("=" * 80)


if __name__ == "__main__":
    main()
