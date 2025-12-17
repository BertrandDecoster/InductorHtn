#!/usr/bin/env python3
"""
Test script to validate Prolog/HTN optimization patterns by measuring resolution steps.
Resolution step tracking is enabled by default (INDHTN_TRACK_RESOLUTION_STEPS=ON).

Uses standard Prolog syntax (capitalized variables like X, Y, Z).
"""

import sys
import os

# Add paths for the Python bindings
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src', 'Python'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'build', 'Release'))

from indhtnpy import HtnPlanner


def test_pattern(name, slow_code, fast_code, query):
    """Test a pattern and return step counts for slow and fast versions."""
    print(f"\n{'='*60}")
    print(f"Pattern: {name}")
    print(f"{'='*60}")

    # Test slow version
    planner_slow = HtnPlanner(False)
    error = planner_slow.PrologCompile(slow_code)
    if error:
        print(f"  SLOW compile error: {error}")
        return None, None

    error, result = planner_slow.PrologQuery(query)
    slow_steps = planner_slow.GetLastResolutionStepCount()
    print(f"  SLOW: {slow_steps} steps (result: {str(result)[:50] if result else 'None'}...)")
    if slow_steps == -1:
        print("  WARNING: Resolution tracking not enabled. Rebuild without -DINDHTN_TRACK_RESOLUTION_STEPS=OFF")

    # Test fast version
    planner_fast = HtnPlanner(False)
    error = planner_fast.PrologCompile(fast_code)
    if error:
        print(f"  FAST compile error: {error}")
        return slow_steps, None

    error, result = planner_fast.PrologQuery(query)
    fast_steps = planner_fast.GetLastResolutionStepCount()
    print(f"  FAST: {fast_steps} steps (result: {str(result)[:50] if result else 'None'}...)")

    if slow_steps and slow_steps > 0 and fast_steps is not None and fast_steps >= 0:
        if slow_steps > fast_steps:
            improvement = ((slow_steps - fast_steps) / slow_steps) * 100
            print(f"  Improvement: {improvement:.1f}%")
            if improvement >= 20:
                print(f"  [VALIDATED] {slow_steps} -> {fast_steps}")
        elif slow_steps == fast_steps:
            print(f"  No improvement (same steps)")
        else:
            print(f"  Fast is SLOWER (negative improvement)")

    return slow_steps, fast_steps


def main():
    print("Prolog/HTN Optimization Pattern Validation")
    print("=" * 60)

    # Check if resolution tracking is enabled
    planner = HtnPlanner(False)
    planner.PrologCompile("test.")
    planner.PrologQuery("test.")
    if planner.GetLastResolutionStepCount() == -1:
        print("\nERROR: Resolution step tracking is not enabled!")
        print("Rebuild without -DINDHTN_TRACK_RESOLUTION_STEPS=OFF (it's ON by default)")
        return 1

    results = []

    # Pattern 1: first() for single-result queries
    # In standard Prolog, first() limits backtracking to first solution
    slow = """
available(taxi1).
available(taxi2).
available(taxi3).
available(taxi4).
available(taxi5).
getTaxi(T) :- available(T).
"""
    fast = """
available(taxi1).
available(taxi2).
available(taxi3).
available(taxi4).
available(taxi5).
getTaxi(T) :- first(available(T)).
"""
    results.append(("first() for single-result", *test_pattern(
        "first() for single-result queries",
        slow, fast, "getTaxi(X)."
    )))

    # Pattern 2: Goal ordering - constraining goal first
    slow = """
person(alice).
person(bob).
person(carol).
person(dave).
rich(dave).
findRichPerson(P) :- person(P), rich(P).
"""
    fast = """
person(alice).
person(bob).
person(carol).
person(dave).
rich(dave).
findRichPerson(P) :- rich(P), person(P).
"""
    results.append(("Goal ordering - constraining first", *test_pattern(
        "Goal ordering - constraining goal first",
        slow, fast, "findRichPerson(X)."
    )))

    # Pattern 3: First-argument indexing
    # Prolog indexes on first argument - put discriminating value first
    slow = """
data(1, a, x).
data(2, b, y).
data(3, c, z).
data(4, d, w).
data(5, e, v).
lookup(Val, Key) :- data(Key, Val, Extra).
"""
    fast = """
dataByVal(a, 1, x).
dataByVal(b, 2, y).
dataByVal(c, 3, z).
dataByVal(d, 4, w).
dataByVal(e, 5, v).
lookup(Val, Key) :- dataByVal(Val, Key, Extra).
"""
    results.append(("First-argument indexing", *test_pattern(
        "First-argument indexing",
        slow, fast, "lookup(c, K)."
    )))

    # Pattern 4: Negation - not() with bound vs unbound
    slow = """
item(a).
item(b).
item(c).
item(d).
excluded(b).
findNonExcluded(X) :- item(X), not(excluded(X)).
"""
    # Pre-computed is faster than runtime not()
    fast = """
item(a).
item(b).
item(c).
item(d).
excluded(b).
nonExcluded(a).
nonExcluded(c).
nonExcluded(d).
findNonExcluded(X) :- nonExcluded(X).
"""
    results.append(("Pre-computed negation", *test_pattern(
        "Pre-computed vs runtime negation",
        slow, fast, "findNonExcluded(X)."
    )))

    # Pattern 5: Count - direct vs redundant findall
    slow = """
member(a, team1).
member(b, team1).
member(c, team1).
member(d, team2).
member(e, team2).
teamSize(Team, Size) :- findall(M, member(M, Team), List), count(Size, member(X, Team)).
"""
    fast = """
member(a, team1).
member(b, team1).
member(c, team1).
member(d, team2).
member(e, team2).
teamSize(Team, Size) :- count(Size, member(X, Team)).
"""
    results.append(("Direct count vs findall+count", *test_pattern(
        "Direct count vs findall+count",
        slow, fast, "teamSize(team1, S)."
    )))

    # Pattern 6: Cut for deterministic choice
    # Using InductorHTN's comparison syntax: >(X, 0) instead of X > 0
    slow = """
classify(X, positive) :- >(X, 0).
classify(X, zero) :- ==(X, 0).
classify(X, negative) :- <(X, 0).
getClassification(X, C) :- classify(X, C).
"""
    fast = """
classify(X, positive) :- >(X, 0), !.
classify(X, zero) :- ==(X, 0), !.
classify(X, negative) :- <(X, 0).
getClassification(X, C) :- classify(X, C).
"""
    results.append(("Cut for determinism", *test_pattern(
        "Cut for deterministic choice",
        slow, fast, "getClassification(5, C)."
    )))

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"{'Pattern':<40} {'Slow':>8} {'Fast':>8} {'Improvement':>12}")
    print("-" * 70)

    validated_count = 0
    for name, slow_steps, fast_steps in results:
        if slow_steps is not None and fast_steps is not None and slow_steps > 0:
            if slow_steps > fast_steps:
                improvement = ((slow_steps - fast_steps) / slow_steps) * 100
                validated = "[VALIDATED]" if improvement >= 20 else ""
                if improvement >= 20:
                    validated_count += 1
                print(f"{name:<40} {slow_steps:>8} {fast_steps:>8} {improvement:>10.1f}% {validated}")
            else:
                print(f"{name:<40} {slow_steps:>8} {fast_steps:>8} {'N/A':>12}")
        else:
            print(f"{name:<40} {'N/A':>8} {'N/A':>8} {'N/A':>12}")

    print("-" * 70)
    print(f"Validated patterns: {validated_count}/{len(results)}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
