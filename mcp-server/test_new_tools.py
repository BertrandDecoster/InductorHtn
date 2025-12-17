#!/usr/bin/env python3
"""Test script for new MCP tools."""

import asyncio
import sys
from pathlib import Path

# Add paths
sys.path.insert(0, str(Path(__file__).parent / "indhtn_mcp"))
sys.path.insert(0, str(Path(__file__).parent.parent / "gui" / "backend"))

from htn_linter import lint_htn
from htn_parser import parse_htn


TEST_SOURCE = """
travel-to(?dest) :-
    if(at(?start)),
    do(walk(?start, ?dest)).

walk(?from, ?to) :- del(at(?from)), add(at(?to)).

at(downtown).
"""


def test_lint():
    """Test linting functionality."""
    print("=== Testing Lint ===")
    diagnostics = lint_htn(TEST_SOURCE)
    print(f"Found {len(diagnostics)} diagnostics:")
    for d in diagnostics:
        print(f"  [{d.get('severity')}] Line {d.get('line')}: {d.get('message')}")
    return len([d for d in diagnostics if d.get("severity") == "error"]) == 0


def test_introspect():
    """Test introspection functionality."""
    print("\n=== Testing Introspect ===")
    rules, errors = parse_htn(TEST_SOURCE)

    methods = [r for r in rules if r.is_method]
    operators = [r for r in rules if r.is_operator]
    facts = [r for r in rules if r.is_fact]

    print(f"Methods ({len(methods)}):")
    for m in methods:
        print(f"  {m.head.name}/{len(m.head.args)} at line {m.line}")

    print(f"Operators ({len(operators)}):")
    for o in operators:
        print(f"  {o.head.name}/{len(o.head.args)} at line {o.line}")

    print(f"Facts ({len(facts)}):")
    for f in facts:
        print(f"  {f.head.name}/{len(f.head.args)} at line {f.line}")

    return len(methods) == 1 and len(operators) == 1 and len(facts) == 1


def main():
    tests = {
        "lint": test_lint,
        "introspect": test_introspect,
    }

    if len(sys.argv) > 2 and sys.argv[1] == "--test":
        test_name = sys.argv[2]
        if test_name in tests:
            success = tests[test_name]()
            sys.exit(0 if success else 1)
        else:
            print(f"Unknown test: {test_name}")
            sys.exit(1)
    else:
        # Run all tests
        all_passed = True
        for name, test_fn in tests.items():
            try:
                if not test_fn():
                    all_passed = False
                    print(f"FAILED: {name}")
            except Exception as e:
                all_passed = False
                print(f"ERROR in {name}: {e}")

        print("\n" + ("All tests passed!" if all_passed else "Some tests failed."))
        sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
