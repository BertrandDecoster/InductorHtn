#!/usr/bin/env python3
"""
Comprehensive test runner for InductorHTN.
Runs all test suites with section headers and summary.

Usage:
    python run_all_tests.py              # Run all tests
    python run_all_tests.py --release    # Use Release build (default)
    python run_all_tests.py --debug      # Use Debug build
    python run_all_tests.py --skip-mcp   # Skip MCP tests
"""

import argparse
import os
import subprocess
import sys
import time
from pathlib import Path

# ANSI colors (works in most terminals)
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
BOLD = "\033[1m"
RESET = "\033[0m"


def print_header(title: str):
    """Print a section header."""
    print(f"\n{CYAN}{BOLD}{'=' * 60}{RESET}")
    print(f"{CYAN}{BOLD}  {title}{RESET}")
    print(f"{CYAN}{BOLD}{'=' * 60}{RESET}\n")


def print_result(name: str, passed: bool, details: str = ""):
    """Print a test result."""
    status = f"{GREEN}PASS{RESET}" if passed else f"{RED}FAIL{RESET}"
    print(f"[{status}] {name}")
    if details and not passed:
        print(f"       {details}")


def run_cpp_tests(build_config: str) -> tuple[bool, int, int]:
    """Run C++ unit tests."""
    print_header(f"C++ Unit Tests ({build_config})")

    exe_path = Path(f"build/{build_config}/runtests.exe")
    if not exe_path.exists():
        # Try without .exe for Unix
        exe_path = Path(f"build/{build_config}/runtests")

    if not exe_path.exists():
        print(f"{RED}Error: Test executable not found at {exe_path}{RESET}")
        print(f"Run: cmake --build ./build --config {build_config}")
        return False, 0, 0

    start = time.time()
    result = subprocess.run([str(exe_path)], capture_output=True, text=True)
    elapsed = time.time() - start

    print(result.stdout)
    if result.stderr:
        print(result.stderr)

    # Parse results from output like "Success: 130 tests passed."
    passed = 0
    total = 0
    for line in result.stdout.split('\n'):
        if 'tests passed' in line.lower():
            # Extract number
            parts = line.split()
            for i, p in enumerate(parts):
                if p.isdigit():
                    passed = total = int(p)
                    break

    success = result.returncode == 0
    print(f"\nTime: {elapsed:.2f}s")
    return success, passed, total


def run_python_htn_tests() -> tuple[bool, int, int]:
    """Run Python HTN test suite."""
    print_header("Python HTN Tests")

    test_script = Path("src/Python/htn_test_suite.py")
    if not test_script.exists():
        print(f"{RED}Error: Test script not found at {test_script}{RESET}")
        return False, 0, 0

    start = time.time()
    result = subprocess.run(
        [sys.executable, str(test_script)],
        capture_output=True,
        text=True,
        cwd=str(Path.cwd())
    )
    elapsed = time.time() - start

    # Only print summary lines, not every query debug line
    output_lines = result.stdout.split('\n')
    in_summary = False
    for line in output_lines:
        # Skip verbose query debug lines
        if 'Query ' in line and ' is a ' in line and ' syntax query' in line:
            continue
        # Print test results and summaries
        if line.strip():
            print(line)

    if result.stderr:
        print(result.stderr)

    # Parse results from "TOTAL: 87/87 tests passed"
    passed = 0
    total = 0
    for line in output_lines:
        if 'TOTAL:' in line and 'tests passed' in line:
            # Extract X/Y
            parts = line.split()
            for p in parts:
                if '/' in p:
                    try:
                        passed, total = map(int, p.split('/'))
                    except ValueError:
                        pass

    success = result.returncode == 0 and passed == total
    print(f"\nTime: {elapsed:.2f}s")
    return success, passed, total


def run_pytest_tests(test_dir: str, name: str, fast: bool = False) -> tuple[bool, int, int]:
    """Run pytest tests in a directory."""
    print_header(f"{name} (pytest)")

    test_path = Path(test_dir)
    if not test_path.exists():
        print(f"{YELLOW}Skipping: {test_dir} not found{RESET}")
        return True, 0, 0

    start = time.time()
    env = os.environ.copy()
    env['PYTHONIOENCODING'] = 'utf-8'

    # Build pytest command
    pytest_args = [sys.executable, "-m", "pytest", test_dir, "-v", "--tb=short"]
    if fast:
        pytest_args.extend(["-m", "not slow"])

    result = subprocess.run(
        pytest_args,
        capture_output=True,
        text=True,
        cwd=str(Path.cwd()),
        env=env
    )
    elapsed = time.time() - start

    print(result.stdout)
    if result.stderr:
        print(result.stderr)

    # Parse pytest output for "X passed" and "X failed"
    passed = 0
    failed = 0
    import re
    for line in result.stdout.split('\n'):
        match = re.search(r'(\d+) passed', line)
        if match:
            passed = int(match.group(1))
        match = re.search(r'(\d+) failed', line)
        if match:
            failed = int(match.group(1))

    total = passed + failed
    success = result.returncode == 0 and failed == 0

    if total == 0:
        # No tests found or pytest not available
        print(f"{YELLOW}No pytest tests found or pytest not installed{RESET}")
        return True, 0, 0

    print(f"\nTime: {elapsed:.2f}s")
    return success, passed, total


def run_gui_tests() -> tuple[bool, int, int]:
    """Run GUI backend tests using pytest."""
    return run_pytest_tests("gui/tests", "GUI Backend Tests")


def run_gui_frontend_tests() -> tuple[bool, int, int]:
    """Run GUI frontend tests using vitest."""
    print_header("GUI Frontend Tests (vitest)")

    frontend_dir = Path("gui/frontend")
    if not frontend_dir.exists():
        print(f"{YELLOW}Skipping: gui/frontend not found{RESET}")
        return True, 0, 0

    # Check if node_modules exists
    if not (frontend_dir / "node_modules").exists():
        print(f"{YELLOW}Skipping: node_modules not found. Run 'npm install' in gui/frontend{RESET}")
        return True, 0, 0

    start = time.time()
    result = subprocess.run(
        ["npm", "run", "test:run"],
        capture_output=True,
        text=True,
        cwd=str(frontend_dir),
        shell=True  # Required for npm on Windows
    )
    elapsed = time.time() - start

    print(result.stdout)
    if result.stderr:
        print(result.stderr)

    # Parse vitest output for "X passed"
    passed = 0
    failed = 0
    import re
    for line in result.stdout.split('\n'):
        # Match "11 passed" or similar
        match = re.search(r'(\d+) passed', line)
        if match:
            passed = int(match.group(1))
        match = re.search(r'(\d+) failed', line)
        if match:
            failed = int(match.group(1))

    total = passed + failed
    success = result.returncode == 0 and failed == 0

    if total == 0:
        print(f"{YELLOW}No vitest tests found or vitest not installed{RESET}")
        return True, 0, 0

    print(f"\nTime: {elapsed:.2f}s")
    return success, passed, total


def main():
    parser = argparse.ArgumentParser(description="Run all InductorHTN tests")
    parser.add_argument("--release", action="store_true", default=True,
                        help="Use Release build (default)")
    parser.add_argument("--debug", action="store_true",
                        help="Use Debug build")
    parser.add_argument("--skip-mcp", action="store_true",
                        help="Skip MCP server tests")
    parser.add_argument("--skip-python", action="store_true",
                        help="Skip Python HTN tests")
    parser.add_argument("--skip-cpp", action="store_true",
                        help="Skip C++ tests")
    parser.add_argument("--fast", action="store_true",
                        help="Skip slow tests (MCP concurrent session tests)")
    args = parser.parse_args()

    build_config = "Debug" if args.debug else "Release"

    print(f"{BOLD}InductorHTN Test Suite{RESET}")
    print(f"Build: {build_config}")
    print(f"Python: {sys.executable}")

    results = []
    total_passed = 0
    total_tests = 0
    all_success = True

    # C++ Tests
    if not args.skip_cpp:
        success, passed, total = run_cpp_tests(build_config)
        results.append(("C++ Unit Tests", success, passed, total))
        total_passed += passed
        total_tests += total
        all_success = all_success and success

    # Python HTN Tests
    if not args.skip_python:
        success, passed, total = run_python_htn_tests()
        results.append(("Python HTN Tests", success, passed, total))
        total_passed += passed
        total_tests += total
        all_success = all_success and success

    # MCP Tests
    if not args.skip_mcp:
        mcp_test_dir = Path("mcp-server/tests")
        if mcp_test_dir.exists():
            success, passed, total = run_pytest_tests("mcp-server/tests", "MCP Server Tests", fast=args.fast)
            if total > 0:
                results.append(("MCP Server Tests", success, passed, total))
                total_passed += passed
                total_tests += total
                all_success = all_success and success

    # GUI Backend Tests
    gui_test_dir = Path("gui/tests")
    if gui_test_dir.exists():
        success, passed, total = run_gui_tests()
        if total > 0:
            results.append(("GUI Backend Tests", success, passed, total))
            total_passed += passed
            total_tests += total
            all_success = all_success and success

    # GUI Frontend Tests
    gui_frontend_dir = Path("gui/frontend")
    if gui_frontend_dir.exists():
        success, passed, total = run_gui_frontend_tests()
        if total > 0:
            results.append(("GUI Frontend Tests", success, passed, total))
            total_passed += passed
            total_tests += total
            all_success = all_success and success

    # Summary
    print_header("Test Summary")

    for name, success, passed, total in results:
        status = f"{GREEN}PASS{RESET}" if success else f"{RED}FAIL{RESET}"
        if total > 0:
            print(f"  [{status}] {name}: {passed}/{total}")
        else:
            print(f"  [{status}] {name}")

    print(f"\n{BOLD}Total: {total_passed}/{total_tests} tests passed{RESET}")

    if all_success:
        print(f"\n{GREEN}{BOLD}All tests passed!{RESET}")
        return 0
    else:
        print(f"\n{RED}{BOLD}Some tests failed!{RESET}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
