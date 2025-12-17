# Test Review: Python HTN Tests

## Summary
- Tests analyzed: 8 test files
- Files reviewed: 11 (including infrastructure)
- Issues found: 12 (2 critical, 6 medium, 4 low)

## Files Reviewed

| File | Framework | Test Count | Purpose |
|------|-----------|------------|---------|
| `src/Python/tests/test_taxi.py` | HtnTestSuite (custom) | ~45 assertions | Taxi domain HTN tests |
| `src/Python/tests/test_game.py` | HtnTestSuite (custom) | ~60 assertions | Game domain HTN tests |
| `src/Python/tests/test_failure_analyzer.py` | unittest.TestCase | 21 tests | Failure analyzer unit tests |
| `src/Python/tests/test_failure_integration.py` | Manual test functions | 2 tests | Integration tests |
| `src/Python/tests/test_linter.py` | Custom LinterTestSuite | ~23 assertions | HTN linter tests |
| `src/Python/tests/test_analyzer.py` | Custom AnalyzerTestSuite | ~20 assertions | Semantic analyzer tests |
| `src/Python/tests/test_htn_service.py` | unittest.TestCase | 18 tests | HtnService unit tests |
| `src/Python/tests/__init__.py` | N/A | N/A | Package init |

**Infrastructure Files:**
- `src/Python/htn_test_framework.py` - Custom HtnTestSuite class (615 lines)
- `src/Python/htn_test_suite.py` - CLI test runner (308 lines)
- `src/Python/indhtnpy.py` - Python bindings (647 lines)

---

## Critique

### What's Working Well

1. **Domain-Specific Test Framework (HtnTestSuite)**
   - Well-designed assertion methods: `assert_plan()`, `assert_query()`, `assert_state_after()`, `assert_decomposition()`
   - Automatic state reset via `_reload_file()` before each test
   - Good abstraction over the complex indhtnpy bindings
   - JSON result parsing handled transparently
   - Location: `src/Python/htn_test_framework.py:35-588`

2. **Comprehensive Domain Test Coverage**
   - `test_taxi.py`: Tests walking, bus, taxi routes, state changes, decomposition trees
   - `test_game.py`: Tests grid positions, movement, AI planning, invariants
   - Both include edge case tests (invalid destinations, boundary conditions)

3. **State Invariant Testing**
   - `no_duplicate_positions()` helper function for game invariants
   - Custom invariant support via `assert_state_invariant()`
   - Location: `src/Python/htn_test_framework.py:592-614`

4. **Failure Analyzer Tests (test_failure_analyzer.py)**
   - Good use of unittest.TestCase with proper setUp methods
   - Tests cover data classes, enums, and analyzer logic
   - Thorough testing of categorization logic

5. **HtnService Tests (test_htn_service.py)**
   - Well-structured with separate test classes by concern
   - Uses `unittest.subTest()` for parameterized-style tests (line 129)
   - Good edge case coverage (empty queries, invalid indices)

6. **Unified Test Runner**
   - `htn_test_suite.py` supports multiple test frameworks
   - CLI with --verbose, --json, --list options
   - Handles HtnTestSuite, unittest.TestCase, and custom suite classes

---

### Issues Found

#### 1. [CRITICAL] Three Different Custom Test Frameworks
   - **File:** Multiple
   - **Details:** The codebase has THREE custom test frameworks:
     - `HtnTestSuite` in `htn_test_framework.py`
     - `LinterTestSuite` in `test_linter.py:21-146`
     - `AnalyzerTestSuite` in `test_analyzer.py:22-104`
   - These are nearly identical in structure but duplicated
   - **Impact:** Maintenance burden, inconsistent behavior, code duplication

#### 2. [CRITICAL] Integration Tests Not Using Standard Framework
   - **File:** `src/Python/tests/test_failure_integration.py`
   - **Details:** Uses raw `print()` statements and manual test orchestration (lines 19-168)
   - No assertions, just print-based verification
   - Return values (True/False) for pass/fail instead of assertions
   - Won't be discovered by pytest or unittest runners properly

#### 3. [MEDIUM] sys.path Manipulation in Every Test File
   - **Files:** All test files
   - **Details:** Every test file has:
     ```python
     sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
     sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../gui/backend')))
     ```
   - Location examples: `test_taxi.py:17-19`, `test_failure_analyzer.py:13-14`
   - **Impact:** Fragile, breaks if files move, hard to maintain

#### 4. [MEDIUM] No tearDown or Resource Cleanup
   - **Files:** `test_failure_analyzer.py`, `test_htn_service.py`
   - **Details:** `setUp()` creates HtnService instances but no cleanup
   - Each test class creates new service instances without verification of cleanup
   - **Impact:** Potential resource leaks with C++ binding objects

#### 5. [MEDIUM] Inconsistent Test Execution Models
   - **File:** `test_linter.py`, `test_analyzer.py`
   - **Details:** Tests run via function calls like `run_syntax_error_tests(suite)` instead of test discovery
   - Location: `test_linter.py:149-366`, `test_analyzer.py:107-287`
   - **Impact:** Cannot run individual tests, no IDE integration

#### 6. [MEDIUM] Test Data Hardcoded in Test Files
   - **Files:** `test_taxi.py:132-166`, `test_analyzer.py:171-177`
   - **Details:** Large HTN programs embedded as multi-line strings
   - Example: 30+ line HTN program in test_taxi.py for "no money" scenario
   - **Impact:** Hard to read, maintain, and share test fixtures

#### 7. [MEDIUM] No Parameterization for Similar Tests
   - **File:** `test_taxi.py`
   - **Details:** Many similar query tests could be parameterized:
     ```python
     # Lines 184-200: Three nearly identical distance queries
     suite.assert_query("distance(downtown, park, ?d).", bindings={"d": "2"}, ...)
     suite.assert_query("distance(downtown, uptown, ?d).", bindings={"d": "8"}, ...)
     suite.assert_query("distance(downtown, suburb, ?d).", bindings={"d": "12"}, ...)
     ```
   - **Impact:** Code duplication, harder to add new test cases

#### 8. [MEDIUM] Error Message Tests Are Fragile
   - **File:** `test_linter.py`
   - **Details:** Tests check for substrings in error messages:
     ```python
     expected_message_contains='paren'  # Line 156
     expected_message_contains=':-'     # Line 175
     ```
   - **Impact:** Tests break if error message wording changes

#### 9. [LOW] Missing Test Isolation Verification
   - **Files:** `test_taxi.py`, `test_game.py`
   - **Details:** Tests rely on `_reload_file()` but no verification that state is actually reset
   - No tests verify that running tests in different orders produces same results
   - **Impact:** Potential for test order dependencies

#### 10. [LOW] Verbose Mode Inconsistency
   - **Files:** All test files
   - **Details:** Some use `verbose=args.verbose`, others use hardcoded defaults
   - `test_failure_integration.py` has no verbose option at all
   - **Impact:** Inconsistent debugging experience

#### 11. [LOW] No Type Hints in Test Framework
   - **File:** `src/Python/htn_test_framework.py`
   - **Details:** Limited type hints, especially for return types
   - Example: `_bindings_match()` at line 314 lacks return type annotation
   - **Impact:** IDE support limitations, harder to catch type errors

#### 12. [LOW] Test File Discovery Pattern Mismatch
   - **File:** `src/Python/htn_test_suite.py:42-52`
   - **Details:** Only discovers `test_*.py` files, but some tests are functions not classes
   - `test_failure_integration.py` has `test_*` functions, not `Test*` classes

---

## Coverage Gaps

### Untested Scenarios

1. **Error Recovery**
   - No tests for planner recovery after memory budget exceeded
   - No tests for handling corrupted HTN files

2. **Concurrency**
   - No tests for multiple HtnPlanner instances running simultaneously
   - HtnService session management not tested under load

3. **Edge Cases in Bindings**
   - Unicode in fact names/values not tested
   - Very long variable names not tested
   - Empty argument lists in predicates

4. **Performance Regression Tests**
   - No benchmarks or performance assertions
   - `GetLastResolutionStepCount()` available but not used in tests

5. **Decomposition Tree Edge Cases**
   - Trees with deep nesting (>10 levels) not tested
   - Trees with many siblings not tested

6. **Linter Coverage**
   - No tests for linting partially valid files
   - No tests for linting very large files

7. **Taxi Domain Missing Tests**
   - No test for running out of cash mid-plan
   - No test for weather changing between plans
   - No test for taxi unavailability

8. **Game Domain Missing Tests**
   - No capture mechanics tested (unit taking enemy position)
   - No test for king check/checkmate scenarios
   - No AI decision priority verification

---

## pytest Migration Plan

### Phase 1: Setup (Day 1-2)

- [ ] Add pytest to requirements.txt
  ```
  pytest>=7.0.0
  pytest-cov>=4.0.0
  ```

- [ ] Create `conftest.py` with shared fixtures
  ```
  File: src/Python/tests/conftest.py

  Contents:
  - @pytest.fixture(scope="module") def taxi_planner()
  - @pytest.fixture(scope="module") def game_planner()
  - @pytest.fixture def htn_service()
  - @pytest.fixture def failure_analyzer()
  ```

- [ ] Configure pytest in `pyproject.toml` or `pytest.ini`
  ```ini
  [pytest]
  testpaths = src/Python/tests
  python_files = test_*.py
  python_classes = Test*
  python_functions = test_*
  addopts = -v --tb=short
  ```

### Phase 2: Gradual Migration (Day 3-7)

#### Step 2.1: Convert unittest tests (easiest)
- [ ] `test_failure_analyzer.py` - Already unittest, pytest runs it unchanged
- [ ] `test_htn_service.py` - Already unittest, pytest runs it unchanged
- [ ] Add `@pytest.mark.parametrize` where beneficial:
  ```python
  @pytest.mark.parametrize("goal,expected", [
      ("travel-to(nonexistent).", 0),
      ("travel-to(xyz123).", 0),
  ])
  def test_impossible_goals(htn_service, goal, expected):
      result = htn_service.execute_htn_query(goal)
      assert result['total_count'] == expected
  ```

#### Step 2.2: Convert integration tests
- [ ] Rewrite `test_failure_integration.py` as proper pytest tests
  - Replace print statements with assertions
  - Use fixtures for HtnService setup
  - Add proper error messages

#### Step 2.3: Create pytest adapter for HtnTestSuite
- [ ] Create `pytest_htn_adapter.py`:
  ```python
  def htn_test_suite_to_pytest(suite: HtnTestSuite):
      """Convert HtnTestSuite results to pytest assertions."""
      for result in suite.results:
          if not result.passed:
              pytest.fail(f"{result.message}: {result.details}")
  ```

#### Step 2.4: Migrate domain tests
- [ ] Convert `test_taxi.py` to pytest format:
  ```python
  class TestTaxiDomain:
      @pytest.fixture(autouse=True)
      def setup(self, taxi_planner):
          self.planner = taxi_planner

      def test_walk_to_park(self):
          # Use assert statements directly
  ```

- [ ] Convert `test_game.py` similarly

#### Step 2.5: Consolidate custom test frameworks
- [ ] Merge LinterTestSuite and AnalyzerTestSuite into HtnTestSuite
- [ ] Or create pytest fixtures that replace them

### Phase 3: Cleanup (Day 8-10)

- [ ] Remove sys.path manipulations
- [ ] Move test data to fixtures or YAML files
- [ ] Add conftest.py to handle path setup
- [ ] Remove unittest.TestCase inheritance where not needed
- [ ] Delete redundant test framework code

### Phase 4: Enhancement (Optional)

- [ ] Add `pytest-xdist` for parallel test execution
- [ ] Add coverage reporting with `pytest-cov`
- [ ] Create test markers for slow tests: `@pytest.mark.slow`
- [ ] Add CI integration configuration

---

## Improvement Plan (Prioritized)

### P0 - Must Fix

1. **Consolidate Test Frameworks**
   - File: `src/Python/tests/test_linter.py`, `src/Python/tests/test_analyzer.py`
   - Action: Extract common functionality into a base class or use pytest fixtures
   - Why: Critical for maintainability

2. **Fix Integration Tests**
   - File: `src/Python/tests/test_failure_integration.py`
   - Action: Rewrite with proper assertions, make discoverable by test runner
   - Why: Currently untested by CI, gives false confidence

3. **Create conftest.py**
   - File: `src/Python/tests/conftest.py` (new)
   - Action: Add fixtures for HtnPlanner, HtnService, file loading
   - Why: Eliminates sys.path hacking, centralizes setup

### P1 - Should Fix

4. **Add Resource Cleanup**
   - Files: `test_failure_analyzer.py`, `test_htn_service.py`
   - Action: Add tearDown methods or use context managers
   - Why: Prevent resource leaks from C++ bindings

5. **Parameterize Repetitive Tests**
   - File: `src/Python/tests/test_taxi.py`
   - Action: Use `@pytest.mark.parametrize` for distance, location, bus route tests
   - Why: ~15 tests could become 3 parameterized tests

6. **Extract Test Data**
   - Files: `test_taxi.py`, `test_analyzer.py`
   - Action: Move HTN programs to `tests/fixtures/` directory
   - Why: Improves readability, enables sharing

7. **Add Type Hints**
   - File: `src/Python/htn_test_framework.py`
   - Action: Add return type hints to all public methods
   - Why: Better IDE support, catches errors earlier

### P2 - Nice to Have

8. **Add Performance Tests**
   - File: `src/Python/tests/test_performance.py` (new)
   - Action: Use `GetLastResolutionStepCount()` to assert performance bounds
   - Why: Catch performance regressions early

9. **Add Unicode Tests**
   - File: `src/Python/tests/test_unicode.py` (new)
   - Action: Test HTN files with unicode characters
   - Why: Ensure international support

10. **Add Capture/Checkmate Tests**
    - File: `src/Python/tests/test_game.py`
    - Action: Add tests for unit capture mechanics
    - Why: Core game functionality not tested

11. **Improve Error Message Tests**
    - File: `src/Python/tests/test_linter.py`
    - Action: Use error codes instead of message substrings
    - Why: More robust to message changes

12. **Add Test Order Independence Verification**
    - File: `src/Python/tests/conftest.py`
    - Action: Add pytest plugin to randomize test order
    - Why: Catches hidden dependencies

---

## conftest.py Example

```python
# src/Python/tests/conftest.py
import pytest
import sys
import os

# Fix import paths once at the package level
_project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
_python_dir = os.path.join(_project_root, 'src/Python')
_backend_dir = os.path.join(_project_root, 'gui/backend')

sys.path.insert(0, _python_dir)
sys.path.insert(0, _backend_dir)

from htn_test_framework import HtnTestSuite
from htn_service import HtnService


@pytest.fixture(scope="module")
def project_root():
    return _project_root


@pytest.fixture(scope="function")
def taxi_suite():
    """Fresh HtnTestSuite for Taxi.htn tests."""
    return HtnTestSuite("Examples/Taxi.htn", verbose=False)


@pytest.fixture(scope="function")
def game_suite():
    """Fresh HtnTestSuite for Game.htn tests."""
    return HtnTestSuite("Examples/Game.htn", verbose=False)


@pytest.fixture(scope="function")
def htn_service():
    """Fresh HtnService instance."""
    service = HtnService()
    yield service
    # Cleanup handled by service destructor


@pytest.fixture
def loaded_taxi_service(htn_service):
    """HtnService with Taxi.htn pre-loaded."""
    success, error = htn_service.load_file('Examples/Taxi.htn')
    assert success, f"Failed to load Taxi.htn: {error}"
    return htn_service
```

---

## Summary Recommendations

1. **Short-term (This Week):**
   - Create `conftest.py` to fix import issues
   - Fix `test_failure_integration.py` to use assertions
   - Run existing tests with pytest (they work unchanged)

2. **Medium-term (This Month):**
   - Consolidate the three custom test frameworks
   - Add parameterization to repetitive tests
   - Extract test data to fixtures

3. **Long-term (This Quarter):**
   - Full migration to pytest idioms
   - Add performance regression tests
   - Achieve >90% code coverage

The test infrastructure is well-designed for HTN-specific testing but suffers from fragmentation and Python testing anti-patterns. A gradual migration to pytest will improve maintainability while preserving the valuable domain-specific assertions in HtnTestSuite.
