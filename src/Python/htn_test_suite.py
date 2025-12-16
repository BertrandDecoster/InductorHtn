#!/usr/bin/env python3
"""
HTN Test Suite CLI Runner

Usage:
    python htn_test_suite.py                    # Run all tests
    python htn_test_suite.py --file Taxi.htn    # Run tests for specific file
    python htn_test_suite.py --verbose          # Enable debug tracing
    python htn_test_suite.py --json             # Output as JSON
    python htn_test_suite.py --list             # List available test files
"""

import argparse
import json
import os
import sys
import importlib.util
from typing import List, Dict, Any

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

from htn_test_framework import HtnTestSuite


def discover_test_files(tests_dir: str) -> List[str]:
    """Find all test_*.py files in the tests directory."""
    if not os.path.exists(tests_dir):
        return []

    test_files = []
    for filename in os.listdir(tests_dir):
        if filename.startswith("test_") and filename.endswith(".py"):
            test_files.append(filename[:-3])  # Remove .py extension

    return sorted(test_files)


def load_test_module(tests_dir: str, module_name: str):
    """Dynamically load a test module."""
    module_path = os.path.join(tests_dir, f"{module_name}.py")
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def run_test_module(module, verbose: bool = False) -> HtnTestSuite:
    """Run tests from a module, looking for run_tests() or test_* functions."""
    # First, look for a run_tests() function
    if hasattr(module, 'run_tests'):
        return module.run_tests(verbose=verbose)

    # Otherwise, look for get_suite() function
    if hasattr(module, 'get_suite'):
        return module.get_suite(verbose=verbose)

    # Fallback: look for any test_* functions
    suite = HtnTestSuite(verbose=verbose)
    for name in dir(module):
        if name.startswith('test_') and callable(getattr(module, name)):
            func = getattr(module, name)
            try:
                result = func(verbose=verbose)
                if isinstance(result, HtnTestSuite):
                    # Merge results
                    suite.results.extend(result.results)
            except TypeError:
                # Try without verbose argument
                result = func()
                if isinstance(result, HtnTestSuite):
                    suite.results.extend(result.results)

    return suite


def main():
    parser = argparse.ArgumentParser(
        description="HTN Test Suite - Run tests for HTN rulesets"
    )
    parser.add_argument(
        "--file", "-f",
        help="Run tests for specific .htn file (e.g., Taxi.htn)"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable debug tracing"
    )
    parser.add_argument(
        "--json", "-j",
        action="store_true",
        help="Output results as JSON"
    )
    parser.add_argument(
        "--list", "-l",
        action="store_true",
        help="List available test files"
    )
    parser.add_argument(
        "--tests-dir",
        default=os.path.join(os.path.dirname(__file__), "tests"),
        help="Directory containing test files"
    )

    args = parser.parse_args()

    # Find tests directory
    tests_dir = args.tests_dir

    # List mode
    if args.list:
        test_files = discover_test_files(tests_dir)
        if not test_files:
            print(f"No test files found in {tests_dir}")
            print("Expected files like: test_taxi.py, test_game.py")
            return 0

        print("Available test files:")
        for tf in test_files:
            print(f"  {tf}")
        return 0

    # Discover test files
    test_files = discover_test_files(tests_dir)

    if not test_files:
        print(f"No test files found in {tests_dir}")
        print("Create test files like: tests/test_taxi.py")
        return 1

    # Filter by specific file if requested
    if args.file:
        # Convert "Taxi.htn" to "test_taxi"
        htn_name = args.file.replace(".htn", "").lower()
        matching = [tf for tf in test_files if htn_name in tf.lower()]
        if not matching:
            print(f"No test file found for '{args.file}'")
            print(f"Available: {test_files}")
            return 1
        test_files = matching

    # Run tests
    all_results: List[Dict[str, Any]] = []
    total_passed = 0
    total_run = 0

    for test_module_name in test_files:
        try:
            module = load_test_module(tests_dir, test_module_name)
            suite = run_test_module(module, verbose=args.verbose)

            total_passed += suite.tests_passed
            total_run += suite.tests_run

            if args.json:
                result = suite.to_json()
                result["test_module"] = test_module_name
                all_results.append(result)
            else:
                print(suite.summary())
                print()

        except Exception as e:
            if args.json:
                all_results.append({
                    "test_module": test_module_name,
                    "error": str(e),
                    "tests_run": 0,
                    "tests_passed": 0,
                    "tests_failed": 0
                })
            else:
                print(f"Error running {test_module_name}: {e}")
                import traceback
                traceback.print_exc()

    # Output
    if args.json:
        output = {
            "total_run": total_run,
            "total_passed": total_passed,
            "total_failed": total_run - total_passed,
            "suites": all_results
        }
        print(json.dumps(output, indent=2))
    else:
        print("=" * 50)
        print(f"TOTAL: {total_passed}/{total_run} tests passed")
        if total_run > total_passed:
            print(f"       {total_run - total_passed} FAILED")
            return 1

    return 0 if total_passed == total_run else 1


if __name__ == "__main__":
    sys.exit(main())
