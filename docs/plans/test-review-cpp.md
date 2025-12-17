# Test Review: C++ Tests

## Summary
- **Tests analyzed**: ~100+ individual test cases
- **Files reviewed**: 13 test files
- **Issues found**: 18 (4 critical, 8 medium, 6 low)

## Files Reviewed

### HTN Tests
| File | Test Count | Purpose |
|------|------------|---------|
| `src/Tests/Htn/HtnPlannerTests.cpp` | ~20 | Core HTN planner functionality |
| `src/Tests/Htn/HtnAdvancedFeaturesTests.cpp` | 20 | anyOf, allOf, first(), try(), else, hidden |
| `src/Tests/Htn/HtnBasicFeaturesTests.cpp` | 16 | Basic HTN method decomposition |
| `src/Tests/Htn/HtnWorkingFeaturesTests.cpp` | 16 | Documentation of working features |
| `src/Tests/Htn/HtnCompilerTests.cpp` | 2 | Missing rule and loop detection |
| `src/Tests/Htn/DebugHtnTest.cpp` | 1 | Simple debug test |
| `src/Tests/Htn/PlannerTestBase.cpp` | 0 | Test infrastructure utilities |

### Prolog Tests
| File | Test Count | Purpose |
|------|------------|---------|
| `src/Tests/Prolog/HtnGoalResolverTests.cpp` | ~30 | SLD resolution, unification |
| `src/Tests/Prolog/BuiltInPredicateCoverageTests.cpp` | ~25 | Built-in predicate testing |
| `src/Tests/Prolog/BuiltInPredicateCoverageTests_Extended.cpp` | ~15 | Extended predicate tests |
| `src/Tests/Prolog/PrologCompilerTests.cpp` | ~12 | Prolog parsing and compilation |
| `src/Tests/Prolog/HtnRuleSetTests.cpp` | 3 | Rule set operations and copying |
| `src/Tests/Prolog/HtnTermTests.cpp` | 4 | Term comparison, JSON, lists |

---

## Critique

### What's Working Well

1. **Consistent Test Infrastructure**
   - Helper classes (`HtnAdvancedTestHelper`, `HtnBasicTestHelper`, `BuiltInTestHelper`) provide clean setup/teardown patterns
   - `ClearWithNewRuleSet()` usage is generally consistent in newer test files
   - Clear separation between HTN and Prolog tests

2. **Good Coverage of Core Functionality**
   - Comprehensive unification tests in `HtnGoalResolverTests.cpp` with well-documented edge cases
   - Thorough testing of arithmetic operations and comparisons
   - Good coverage of list compilation and ToString roundtrips

3. **Realistic Test Scenarios**
   - `HtnGoalResolverSquareScenarioTest` demonstrates complex recursive patterns
   - Integration tests combine multiple predicates effectively
   - Real-world inspired scenarios (e.g., unit AI decision making)

4. **Clear Expected Result Formats**
   - Consistent use of `CHECK_EQUAL` with expected string values
   - Documented expected formats: `"[ { operator(args) } ]"`, `"null"`, `"(())"`

5. **Documentation of Known Issues**
   - `HtnBasicFeaturesTests.cpp` contains documented bug reports with dates
   - `HtnWorkingFeaturesTests.cpp` documents what works vs what doesn't

---

### Issues Found

#### CRITICAL Issues

1. **[CRITICAL] Contradictory Test Files: HtnBasicFeaturesTests vs HtnAdvancedFeaturesTests**
   - **File**: `src/Tests/Htn/HtnBasicFeaturesTests.cpp` (lines 479-526)
   - **File**: `src/Tests/Htn/HtnAdvancedFeaturesTests.cpp` (entire file)
   - **Details**: `HtnBasicFeaturesTests.cpp` contains comments stating that anyOf/allOf/first/try/else features "cause Crash! exceptions" and are "not implemented" (BUG REPORT #8-15). However, `HtnAdvancedFeaturesTests.cpp` has passing tests for ALL these features. This creates significant confusion about actual system capabilities. One set of tests is fundamentally incorrect.
   - **Impact**: Developers cannot trust the test suite to accurately represent system behavior.

2. **[CRITICAL] Missing State Clearing in BuiltInPredicateCoverageTests.cpp**
   - **File**: `src/Tests/Prolog/BuiltInPredicateCoverageTests.cpp`
   - **Details**: The `BuiltInTestHelper::SolveGoals()` method does NOT call `compiler->Clear()` before compilation (line 37-41). Only some tests manually call `helper.Clear()`. This causes state leakage between tests where facts from previous tests persist.
   - **Example**: Tests at lines 62-84 call `helper.Clear()` manually, but many tests don't, leading to potential false positives.
   - **Impact**: Tests may pass due to leftover state from previous tests.

3. **[CRITICAL] Inconsistent Use of Clear() vs ClearWithNewRuleSet()**
   - **Files**: Multiple
   - **Details**: Some tests use `compiler->Clear()`, others use `compiler->ClearWithNewRuleSet()`, and some use `state->ClearAll()`. These have different behaviors:
     - `Clear()`: Clears only compilation state
     - `ClearWithNewRuleSet()`: Creates fresh rule set
     - `state->ClearAll()`: Directly clears state
   - **Locations**:
     - `HtnCompilerTests.cpp` line 34: uses `compiler->Clear()` (not `ClearWithNewRuleSet()`)
     - `PrologCompilerTests.cpp` line 36: uses `state->ClearAll()` then creates new compiler
     - `HtnAdvancedFeaturesTests.cpp` line 37: correctly uses `ClearWithNewRuleSet()`
   - **Impact**: Potential cross-test contamination.

4. **[CRITICAL] Tests Document Bugs That Don't Appear to Exist**
   - **File**: `src/Tests/Htn/HtnWorkingFeaturesTests.cpp` (lines 417-433, 471-495)
   - **Details**: Test `DISABLED_HTNMethods_DocumentedAsNotWorking` claims HTN methods don't work, but `HtnPlannerTests.cpp` and `HtnAdvancedFeaturesTests.cpp` have extensive passing tests for methods. The documentation at lines 471-495 claims "HTN methods (if/do syntax)" and "Method decomposition" are NOT WORKING, contradicting other test files.
   - **Impact**: Severe confusion about system state; documentation is misleading.

#### MEDIUM Issues

5. **[MEDIUM] Duplicate Helper Class Definitions**
   - **Files**: `HtnAdvancedFeaturesTests.cpp`, `HtnBasicFeaturesTests.cpp`, `HtnWorkingFeaturesTests.cpp`, `BuiltInPredicateCoverageTests.cpp`, `BuiltInPredicateCoverageTests_Extended.cpp`
   - **Details**: Each file defines its own nearly-identical helper class (`HtnAdvancedTestHelper`, `HtnBasicTestHelper`, `HtnWorkingTestHelper`, `BuiltInTestHelper`). These should be consolidated into a shared test fixture.
   - **Impact**: Code duplication, maintenance burden, inconsistent implementations.

6. **[MEDIUM] Weak Assertions Using String Find**
   - **File**: `src/Tests/Htn/HtnAdvancedFeaturesTests.cpp` (lines 85-86, 110-111, many others)
   - **File**: `src/Tests/Prolog/BuiltInPredicateCoverageTests.cpp` (lines 217-221, many others)
   - **Details**: Many tests use `CHECK(result.find("keyword") != string::npos)` instead of `CHECK_EQUAL`. This can lead to false positives if the keyword appears in unexpected places.
   - **Example**: Line 85-86: `CHECK(result.find("attack") != string::npos)` would pass even if "attackWrongTarget" was in the result.
   - **Impact**: Tests may pass when behavior is incorrect.

7. **[MEDIUM] Missing Error Message Tests**
   - **Files**: All test files
   - **Details**: When compilation fails or planning returns null, tests don't verify the error message. Example: `HtnCompilerTests.cpp` correctly checks error detection but doesn't validate error message content.
   - **Impact**: Regression in error messages would go undetected.

8. **[MEDIUM] No Tests for Memory Budget Enforcement**
   - **File**: `src/Tests/Htn/HtnPlannerTests.cpp`
   - **Details**: While `FindAllPlans` accepts a memory budget parameter (line 55), there are no tests that verify the planner correctly stops when memory is exceeded and returns partial solutions.
   - **Impact**: Memory-related bugs would go undetected.

9. **[MEDIUM] Inconsistent Test for Division by Zero**
   - **File**: `src/Tests/Prolog/BuiltInPredicateCoverageTests.cpp` (lines 391-392)
   - **File**: `src/Tests/Prolog/BuiltInPredicateCoverageTests_Extended.cpp` (lines 272-280, commented out)
   - **Details**: One file expects `"null"` for division by zero, the other has a commented-out test expecting `"((?X = 0))"` with a note "BUG #5: Division by zero returns 0 instead of failing". The expected behavior is unclear.
   - **Impact**: Unclear system behavior for edge case.

10. **[MEDIUM] Order-Dependent Result Checking**
    - **File**: `src/Tests/Prolog/BuiltInPredicateCoverageTests.cpp` (line 252, others)
    - **Details**: Some tests like `CHECK_EQUAL("((?Children = [bob,liz]))", result)` assume a specific ordering of results. Prolog doesn't guarantee ordering in all cases.
    - **Impact**: Tests may fail if internal implementation changes ordering.

11. **[MEDIUM] No Negative Tests for Syntax Errors**
    - **Files**: All test files
    - **Details**: Tests compile valid programs but rarely test invalid syntax to ensure proper error handling. `HtnCompilerTests.cpp` tests logic errors but not syntax errors.
    - **Impact**: Parser error handling is untested.

12. **[MEDIUM] Missing tests for the `hidden` keyword effect verification**
    - **File**: `src/Tests/Htn/HtnAdvancedFeaturesTests.cpp` (lines 378-426)
    - **Details**: Tests verify hidden operators don't appear in plan output, but don't verify that the hidden operators' effects ARE still applied to the state. Line 400-401 has a comment acknowledging this: "However, the effects should still be in final state (This would require checking final facts, not just the plan)"
    - **Impact**: Hidden operator state changes are not verified.

#### LOW Issues

13. **[LOW] Commented-Out Tests**
    - **File**: `src/Tests/Prolog/HtnGoalResolverTests.cpp` (lines 78-110)
    - **File**: `src/Tests/Prolog/BuiltInPredicateCoverageTests.cpp` (lines 587-592)
    - **Details**: Several tests are commented out without explanation (e.g., `AdventureScenarioTests`, `write`/`writeln` tests).
    - **Impact**: Reduced coverage, unclear if intentional or forgotten.

14. **[LOW] Magic Numbers in Tests**
    - **File**: `src/Tests/Htn/HtnPlannerTests.cpp` (line 55: `5000000`)
    - **Details**: Memory budget passed as literal number without explanation.
    - **Impact**: Unclear why specific values are used.

15. **[LOW] Test Name Inconsistency**
    - **Files**: Various
    - **Details**: Test naming conventions vary:
      - `PlannerOperatorTest` vs `BasicOperator_SimpleExecution`
      - `HtnCompilerMissingTests` vs `AtomConcat_BasicUsage`
    - **Impact**: Harder to navigate test suite.

16. **[LOW] No Performance/Regression Tests**
    - **Files**: All
    - **Details**: No tests that measure or validate execution time or resolution step counts.
    - **Impact**: Performance regressions would go undetected.

17. **[LOW] Hardcoded Windows Line Endings**
    - **Files**: Multiple (e.g., `HtnPlannerTests.cpp`)
    - **Details**: Test strings use `\r\n` explicitly, may cause issues on non-Windows platforms.
    - **Impact**: Cross-platform portability issues.

18. **[LOW] PlannerTestBase.h Minimal**
    - **File**: `src/Tests/Htn/PlannerTestBase.h`
    - **Details**: Only declares `DiffSolutionInOrder` function but this utility is underutilized in actual tests.
    - **Impact**: Useful test utility goes unused.

---

## Coverage Gaps

### HTN Features Not Tested
1. **Recursive methods** - Methods that call themselves with different parameters
2. **Deep method nesting** - Methods calling methods calling methods (3+ levels)
3. **Method backtracking** - When first method fails and alternative is tried
4. **Memory limit behavior** - What happens when memory budget is exceeded
5. **Concurrent planning** - Multiple plans being computed simultaneously
6. **Large-scale planning** - Plans with 100+ operators

### Prolog Features Not Tested
1. **atom_chars reverse conversion** - Converting list back to atom (documented as potentially unsupported in test)
2. **write/writeln predicates** - Commented out in tests
3. **Complex sortBy scenarios** - Multi-key sorting
4. **Deeply nested lists** - Lists within lists within lists
5. **Unicode/special character handling** - Non-ASCII atoms

### Edge Cases Not Tested
1. **Empty input handling** - Empty programs, empty goals
2. **Maximum recursion depth** - Deeply recursive rules
3. **Circular variable references** - Beyond basic occurs check
4. **Very large numbers** - Integer overflow, floating point precision
5. **Very long atoms** - Memory behavior with long strings

---

## Improvement Plan (Prioritized)

### P0 - Must Fix

- [ ] **Resolve test file contradictions** (`HtnBasicFeaturesTests.cpp` vs `HtnAdvancedFeaturesTests.cpp`)
  - File: `src/Tests/Htn/HtnBasicFeaturesTests.cpp`
  - Action: Delete or update the incorrect bug reports at lines 479-526. If advanced features work, remove the claims they don't. Run all tests to verify.

- [ ] **Fix state clearing in BuiltInPredicateCoverageTests.cpp**
  - File: `src/Tests/Prolog/BuiltInPredicateCoverageTests.cpp`
  - Action: Add `compiler->Clear()` call in `SolveGoals()` method at line 37, or ensure each test creates fresh state.

- [ ] **Remove misleading documentation in HtnWorkingFeaturesTests.cpp**
  - File: `src/Tests/Htn/HtnWorkingFeaturesTests.cpp`
  - Action: Update or remove the summary at lines 471-495 that claims HTN methods don't work.

- [ ] **Standardize state clearing pattern across all test files**
  - Files: All test files
  - Action: Document the correct pattern (`ClearWithNewRuleSet()`) in a test guide and update all tests to use it consistently.

### P1 - Should Fix

- [ ] **Consolidate duplicate helper classes into shared test fixture**
  - Files: All HTN test files
  - Action: Create `src/Tests/Htn/HtnTestFixture.h` with shared helper class.

- [ ] **Replace string find assertions with exact matches where possible**
  - Files: `HtnAdvancedFeaturesTests.cpp`, `BuiltInPredicateCoverageTests.cpp`
  - Action: Use `CHECK_EQUAL` with full expected strings, or create helper to parse and compare structured results.

- [ ] **Add memory budget tests**
  - File: `src/Tests/Htn/HtnPlannerTests.cpp`
  - Action: Add tests that set low memory budget and verify partial solution is returned.

- [ ] **Add hidden operator state verification**
  - File: `src/Tests/Htn/HtnAdvancedFeaturesTests.cpp`
  - Action: After plan execution, query final state to verify hidden operator effects were applied.

- [ ] **Clarify division by zero behavior**
  - Files: `BuiltInPredicateCoverageTests.cpp`, `BuiltInPredicateCoverageTests_Extended.cpp`
  - Action: Decide on expected behavior, document it, and write consistent test.

### P2 - Nice to Have

- [ ] **Add negative syntax error tests**
  - File: Create `src/Tests/Htn/HtnCompilerSyntaxErrorTests.cpp`
  - Action: Test various malformed inputs and verify appropriate errors.

- [ ] **Add performance regression tests**
  - File: Create `src/Tests/Htn/HtnPerformanceTests.cpp`
  - Action: Test known scenarios with resolution step counting (feature exists per CLAUDE.md).

- [ ] **Remove or uncomment commented-out tests**
  - Files: `HtnGoalResolverTests.cpp`, `BuiltInPredicateCoverageTests.cpp`
  - Action: Either enable tests or delete with explanation.

- [ ] **Standardize test naming convention**
  - Files: All test files
  - Action: Adopt consistent naming like `Category_Scenario` (e.g., `AllOf_BasicUsage`).

- [ ] **Add cross-platform line ending handling**
  - Files: All test files using `\r\n`
  - Action: Use platform-agnostic line endings or normalize in test helper.

- [ ] **Utilize DiffSolutionInOrder utility more widely**
  - Files: All planner tests
  - Action: Use `PlannerTestBase::DiffSolutionInOrder` for solution comparison instead of string comparison where appropriate.

---

## Appendix: Test Framework Reference

### UnitTest++ Macros Used
```cpp
SUITE(SuiteName) { }           // Group related tests
TEST(TestName) { }             // Define a test
TEST_FIXTURE(Fixture, Name)    // Test with fixture
CHECK(bool)                    // Assert true
CHECK_EQUAL(expected, actual)  // Assert equality
CHECK_CLOSE(exp, act, tol)     // Float comparison
CHECK_THROW(expr, Exception)   // Expect exception
```

### Expected Result Formats (per CLAUDE.md)
- Success with operators: `"[ { operator1(args) } ]"`
- Multiple solutions: `"[ { sol1 } { sol2 } ]"`
- Empty plan: `"[ { () } ]"`
- Failure: `"null"`
- Variable bindings: `"((?X = value))"`
- Empty success: `"(())"`
