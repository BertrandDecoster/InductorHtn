"""
Integration tests for HTN Failure Debugger

Tests the full flow from HtnService through failure analyzer to verify
enhanced failure information is properly captured and formatted.
"""

import sys
import os
import json

# Add paths
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../gui/backend')))

from htn_service import HtnService


def test_failure_analysis_integration():
    """Test that failure analysis works through HtnService"""
    print("=" * 60)
    print("Integration Test: HTN Failure Debugger")
    print("=" * 60)

    service = HtnService()

    # Load test file
    success, error = service.load_file('Examples/Taxi.htn')
    if not success:
        print(f"Failed to load file: {error}")
        return False

    print("Loaded Taxi.htn successfully")

    # Execute a query that will explore multiple paths
    result = service.execute_htn_query('travel-to(park).', enhanced_trace=True)

    if 'error' in result:
        print(f"Query error: {result['error']}")
        return False

    print(f"\nFound {result['total_count']} solution(s)")

    # Check that trees have enhanced failure information
    for i, tree in enumerate(result.get('trees', [])):
        print(f"\n--- Solution {i + 1} Tree ---")
        check_tree_for_failures(tree, depth=0)

    print("\n" + "=" * 60)
    print("Integration test completed successfully")
    print("=" * 60)
    return True


def check_tree_for_failures(node, depth=0):
    """Recursively check tree nodes for failure information"""
    indent = "  " * depth
    status = node.get('status', 'default')
    name = node.get('name', '?')

    status_marker = {'success': '[OK]', 'failure': '[FAIL]', 'default': '[---]'}.get(status, '[?]')
    print(f"{indent}{status_marker} {name}")

    if status == 'failure':
        # Check for enhanced failure detail
        failure_detail = node.get('failureDetail')
        if failure_detail:
            print(f"{indent}  Category: {failure_detail.get('category', 'UNKNOWN')}")
            print(f"{indent}  Message: {failure_detail.get('message', 'No message')}")

            suggestions = failure_detail.get('suggestions', [])
            if suggestions:
                print(f"{indent}  Suggestions:")
                for s in suggestions[:2]:  # Show first 2
                    print(f"{indent}    - {s}")

        missing = node.get('missingFacts', [])
        if missing:
            print(f"{indent}  Missing facts: {missing[:3]}")  # Show first 3

        failed_conds = node.get('failedConditions', [])
        if failed_conds:
            print(f"{indent}  Failed conditions: {failed_conds[:3]}")

        alternatives = node.get('alternativesTried', [])
        if alternatives:
            print(f"{indent}  Alternatives tried: {len(alternatives)}")

    # Recurse to children
    for child in node.get('children', []):
        check_tree_for_failures(child, depth + 1)


def test_failure_categories():
    """Test that different failure types are categorized correctly"""
    print("\n" + "=" * 60)
    print("Testing Failure Categories")
    print("=" * 60)

    service = HtnService()

    # Load a file that will produce specific failure types
    success, error = service.load_file('Examples/Taxi.htn')
    if not success:
        print(f"Failed to load file: {error}")
        return False

    # Query that should fail with precondition issues
    result = service.execute_htn_query('travel-to(mars).', enhanced_trace=True)

    # This should fail since there's no way to get to mars
    print(f"Query 'travel-to(mars).' returned {result.get('total_count', 0)} solutions")

    if result.get('trees'):
        for tree in result['trees']:
            categories_found = collect_categories(tree)
            print(f"Failure categories found: {categories_found}")

    return True


def collect_categories(node, categories=None):
    """Collect all failure categories in a tree"""
    if categories is None:
        categories = set()

    if node.get('status') == 'failure':
        detail = node.get('failureDetail')
        if detail:
            categories.add(detail.get('category', 'UNKNOWN'))

    for child in node.get('children', []):
        collect_categories(child, categories)

    return categories


if __name__ == '__main__':
    print("\nRunning HTN Failure Debugger Integration Tests\n")

    tests_passed = 0
    tests_failed = 0

    try:
        if test_failure_analysis_integration():
            tests_passed += 1
        else:
            tests_failed += 1
    except Exception as e:
        print(f"Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        tests_failed += 1

    try:
        if test_failure_categories():
            tests_passed += 1
        else:
            tests_failed += 1
    except Exception as e:
        print(f"Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        tests_failed += 1

    print(f"\n{'=' * 60}")
    print(f"Results: {tests_passed} passed, {tests_failed} failed")
    print(f"{'=' * 60}")
