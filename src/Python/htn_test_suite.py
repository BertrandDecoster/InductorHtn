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
import io
import json
import os
import sys
import unittest
import importlib.util
from typing import List, Dict, Any, Optional

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

from htn_test_framework import HtnTestSuite


class TestResult:
    """Unified test result for all frameworks."""

    def __init__(self, name: str, passed: int, failed: int, output: str = ""):
        self.name = name
        self.passed = passed
        self.failed = failed
        self.output = output

    @property
    def total(self) -> int:
        return self.passed + self.failed


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


def run_unittest_module(module, verbose: bool = False) -> Optional[TestResult]:
    """Run unittest.TestCase classes in a module."""
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromModule(module)

    if suite.countTestCases() == 0:
        return None

    stream = io.StringIO()
    verbosity = 2 if verbose else 1
    runner = unittest.TextTestRunner(stream=stream, verbosity=verbosity)
    result = runner.run(suite)

    passed = result.testsRun - len(result.failures) - len(result.errors)
    failed = len(result.failures) + len(result.errors)

    # Format output
    output = f"Test Suite: {module.__name__}\n"
    output += "=" * 50 + "\n"
    if verbose:
        output += stream.getvalue()
    for test, _ in result.failures:
        output += f"[FAIL] {test}\n"
    for test, _ in result.errors:
        output += f"[ERROR] {test}\n"
    if passed > 0 and not verbose:
        output += f"[PASS] {passed} tests passed\n"
    output += "=" * 50 + "\n"
    output += f"Total: {passed}/{result.testsRun} passed\n"

    return TestResult(
        name=module.__name__,
        passed=passed,
        failed=failed,
        output=output
    )


def run_custom_suite_module(module, verbose: bool = False) -> Optional[TestResult]:
    """Run modules with custom test suite classes (LinterTestSuite, AnalyzerTestSuite)."""
    # Check for known custom suite classes
    suite_classes = ['LinterTestSuite', 'AnalyzerTestSuite']

    for class_name in suite_classes:
        if hasattr(module, class_name):
            suite_class = getattr(module, class_name)
            suite = suite_class(verbose=verbose)

            # Run the test functions that populate the suite
            # Look for run_*_tests functions
            for name in dir(module):
                if name.startswith('run_') and name.endswith('_tests') and callable(getattr(module, name)):
                    func = getattr(module, name)
                    try:
                        func(suite)
                    except TypeError:
                        pass

            # Also try run_good_file_tests pattern
            if hasattr(module, 'run_good_file_tests'):
                try:
                    module.run_good_file_tests(suite)
                except TypeError:
                    pass

            output = suite.summary() if hasattr(suite, 'summary') else ""

            return TestResult(
                name=module.__name__,
                passed=suite.passed,
                failed=suite.failed,
                output=output
            )

    return None


def run_test_module(module, verbose: bool = False) -> Optional[TestResult]:
    """Run tests from a module, trying multiple test frameworks."""
    # 1. Try HtnTestSuite (run_tests() or get_suite())
    if hasattr(module, 'run_tests'):
        result = module.run_tests(verbose=verbose)
        if isinstance(result, HtnTestSuite):
            return TestResult(
                name=module.__name__,
                passed=result.tests_passed,
                failed=result.tests_run - result.tests_passed,
                output=result.summary()
            )

    if hasattr(module, 'get_suite'):
        result = module.get_suite(verbose=verbose)
        if isinstance(result, HtnTestSuite):
            return TestResult(
                name=module.__name__,
                passed=result.tests_passed,
                failed=result.tests_run - result.tests_passed,
                output=result.summary()
            )

    # 2. Try unittest.TestCase classes
    unittest_result = run_unittest_module(module, verbose)
    if unittest_result:
        return unittest_result

    # 3. Try custom suite classes (LinterTestSuite, AnalyzerTestSuite)
    custom_result = run_custom_suite_module(module, verbose)
    if custom_result:
        return custom_result

    # 4. No compatible tests found
    return None


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
            result = run_test_module(module, verbose=args.verbose)

            # Skip modules with no compatible tests
            if result is None:
                continue

            total_passed += result.passed
            total_run += result.total

            if args.json:
                all_results.append({
                    "test_module": test_module_name,
                    "tests_run": result.total,
                    "tests_passed": result.passed,
                    "tests_failed": result.failed
                })
            else:
                print(result.output)
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
