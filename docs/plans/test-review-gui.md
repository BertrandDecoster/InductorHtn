# Test Review: GUI/Backend Tests

## Summary
- Tests analyzed: 2 files (test_backend.py, test_htn_api.py)
- Files reviewed: 6 (test files + app.py, htn_service.py, htn_linter.py, invariants.py)
- Issues found: 15 (5 critical, 7 medium, 3 low)

## Current State Assessment

The existing "test" files (`gui/test_backend.py` and `gui/test_htn_api.py`) are **not automated tests** - they are manual verification scripts that:
1. Require the Flask server to be running externally on port 5000
2. Use `requests` library to make HTTP calls to a live server
3. Print results to stdout without assertions
4. Have no test isolation or cleanup
5. Cannot be run as part of CI/CD pipeline

## Endpoint Coverage Matrix

| Endpoint | Method | Tested? | Happy Path | Error Cases | Notes |
|----------|--------|---------|------------|-------------|-------|
| `/api/session/create` | POST | Partial | Yes (manual) | No | Only in manual scripts |
| `/api/session/delete/<id>` | DELETE | No | No | No | **UNTESTED** |
| `/api/file/load` | POST | Partial | Yes (manual) | No | No error case testing |
| `/api/file/save` | POST | No | No | No | **UNTESTED** |
| `/api/file/content` | POST | No | No | No | **UNTESTED** |
| `/api/file/list` | GET | No | No | No | **UNTESTED** |
| `/api/query/execute` | POST | Partial | Yes (manual) | No | Only happy path |
| `/api/htn/execute` | POST | Partial | Yes (manual) | No | Only happy path |
| `/api/state/get` | POST | No | No | No | **UNTESTED** |
| `/api/state/diff` | POST | No | No | No | **UNTESTED** |
| `/api/lint` | POST | No | No | No | **UNTESTED** |
| `/api/lint/batch` | POST | No | No | No | **UNTESTED** |
| `/api/analyze` | POST | No | No | No | **UNTESTED** |
| `/api/analyze/batch` | POST | No | No | No | **UNTESTED** |
| `/api/invariants` | GET | No | No | No | **UNTESTED** |
| `/api/invariants/<id>/enable` | POST | No | No | No | **UNTESTED** |
| `/api/invariants/<id>/configure` | POST | No | No | No | **UNTESTED** |
| `/api/callgraph` | POST | No | No | No | **UNTESTED** |
| `/health` | GET | No | No | No | **UNTESTED** |

**Coverage Summary:**
- Total Endpoints: 19
- Partially Tested (manual only): 4 (21%)
- Completely Untested: 15 (79%)
- Automated Test Coverage: 0%

## Critique

### What's Working Well

1. **Manual scripts demonstrate API usage** - The scripts in `test_backend.py` and `test_htn_api.py` show how the API is intended to be used, which can serve as documentation.

2. **Tree visualization output** - The `test_htn_api.py` script includes useful tree printing logic that helps visualize decomposition trees.

3. **Session workflow demonstrated** - The scripts show the correct order of operations: create session -> load file -> execute query.

### Issues Found

#### Critical Issues

1. **[CRITICAL] No Automated Tests Exist**
   - Files: `gui/test_backend.py`, `gui/test_htn_api.py`
   - Both test files are manual scripts requiring external server
   - No pytest, unittest, or any test framework usage
   - Cannot be integrated into CI/CD
   - Impact: Zero automated test coverage for entire GUI backend

2. **[CRITICAL] 79% of Endpoints Completely Untested**
   - 15 out of 19 endpoints have no test coverage at all
   - Critical endpoints like `/api/session/delete`, `/api/file/save`, all linting endpoints
   - Impact: Regressions will go undetected

3. **[CRITICAL] No Error Case Testing**
   - No tests for invalid session IDs (400 responses)
   - No tests for missing files (404 responses)
   - No tests for malformed JSON (500 responses)
   - Impact: Error handling may be broken without detection

4. **[CRITICAL] No Test Isolation**
   - Scripts depend on global state
   - Sessions not cleaned up
   - Tests depend on Examples/Taxi.htn existing
   - Impact: Flaky tests, cannot run in parallel

5. **[CRITICAL] No Assertions**
   - Scripts only print results, no actual assertions
   - A failing API could still show "success" if it returns 200
   - Impact: Tests don't actually verify correctness

#### Medium Issues

6. **[MEDIUM] No Session Lifecycle Testing**
   - Session deletion never tested
   - Session expiration/limits not tested
   - Multiple session handling not tested

7. **[MEDIUM] HtnService Has Complex Logic Without Unit Tests**
   - `_is_failure_result()` method has complex logic
   - `_transform_decomp_tree()` has recursive tree building
   - `_format_prolog_results()` has parsing logic
   - All only tested indirectly via manual scripts

8. **[MEDIUM] Linter/Analyzer Have Zero Test Coverage**
   - `htn_linter.py` has 600+ lines of lint checking code
   - `htn_analyzer.py` has 500+ lines of semantic analysis
   - `invariants.py` has pattern-based invariant checking
   - None of these have any test coverage

9. **[MEDIUM] No CORS Testing**
   - CORS is enabled but not tested
   - Cross-origin requests not verified

10. **[MEDIUM] No Boundary Testing**
    - Empty files
    - Very large files
    - Malformed HTN syntax
    - Unicode content

11. **[MEDIUM] No Concurrent Request Testing**
    - Multiple simultaneous sessions
    - Race conditions in session management

12. **[MEDIUM] Missing Response Schema Validation**
    - JSON structure not validated
    - Missing fields not detected

#### Low Issues

13. **[LOW] Test Scripts Not Discoverable**
    - Not named with `test_` prefix in pytest-compatible way
    - Located in gui/ root, not in tests/ directory

14. **[LOW] No Test Documentation**
    - No comments explaining what tests verify
    - No setup/teardown documentation

15. **[LOW] Hardcoded URLs and Paths**
    - `BASE_URL = "http://localhost:5000"` hardcoded
    - `Examples/Taxi.htn` hardcoded

## Coverage Gaps

### Endpoint-Level Gaps

1. **Session Management**
   - DELETE `/api/session/delete/<session_id>` - never tested
   - Invalid session ID handling
   - Session cleanup

2. **File Operations**
   - POST `/api/file/save` - never tested
   - POST `/api/file/content` - never tested
   - GET `/api/file/list` - never tested
   - Non-existent file handling
   - Permission errors
   - Path traversal prevention

3. **State Management**
   - POST `/api/state/get` - never tested
   - POST `/api/state/diff` - never tested
   - State after applying plans

4. **Linting and Analysis**
   - POST `/api/lint` - never tested
   - POST `/api/lint/batch` - never tested
   - POST `/api/analyze` - never tested
   - POST `/api/analyze/batch` - never tested
   - POST `/api/callgraph` - never tested
   - Syntax error detection
   - Semantic warnings

5. **Invariants**
   - GET `/api/invariants` - never tested
   - POST `/api/invariants/<id>/enable` - never tested
   - POST `/api/invariants/<id>/configure` - never tested
   - Invariant violation detection

6. **Health**
   - GET `/health` - never tested

### Functional Gaps

1. **Error Responses**
   - 400 Bad Request (invalid session, missing params)
   - 404 Not Found (missing files, invalid invariant IDs)
   - 500 Internal Server Error (exceptions)

2. **Input Validation**
   - SQL injection (not applicable but patterns worth testing)
   - Path traversal attacks
   - JSON parsing errors
   - Oversized requests

3. **Edge Cases**
   - Empty HTN files
   - HTN files with only comments
   - Circular dependencies in rules
   - Very deep decomposition trees

## pytest Migration Plan

### Phase 1: Setup (Priority: P0)

```
gui/
  tests/
    __init__.py
    conftest.py           # Fixtures for Flask test client
    test_session.py       # Session endpoint tests
    test_file.py          # File operation tests
    test_query.py         # Query execution tests
    test_state.py         # State management tests
    test_lint.py          # Linting tests
    test_analyze.py       # Analyzer tests
    test_invariants.py    # Invariant tests
    test_health.py        # Health check tests
    fixtures/
      Taxi.htn            # Test HTN file
      invalid.htn         # Invalid syntax file
      empty.htn           # Empty file
```

#### conftest.py Structure

```python
import pytest
import sys
import os

# Add paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app import app

@pytest.fixture
def client():
    """Create Flask test client"""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

@pytest.fixture
def session(client):
    """Create a session and return session_id, cleanup after test"""
    response = client.post('/api/session/create')
    data = response.get_json()
    session_id = data['session_id']
    yield session_id
    # Cleanup
    client.delete(f'/api/session/delete/{session_id}')

@pytest.fixture
def loaded_session(client, session):
    """Session with Taxi.htn loaded"""
    client.post('/api/file/load', json={
        'session_id': session,
        'file_path': 'Examples/Taxi.htn'
    })
    return session
```

#### Dependencies to Add

```
# gui/backend/requirements.txt (add)
pytest>=7.0.0
pytest-cov>=4.0.0
```

### Phase 2: Implement Tests (Priority: P0-P1)

#### P0 - Core Endpoint Tests

- [ ] `test_session.py`
  - [ ] `test_create_session_returns_session_id`
  - [ ] `test_create_session_returns_201_or_200`
  - [ ] `test_delete_session_removes_session`
  - [ ] `test_delete_nonexistent_session_returns_404`
  - [ ] `test_session_isolation` (different sessions don't interfere)

- [ ] `test_file.py`
  - [ ] `test_load_valid_file`
  - [ ] `test_load_nonexistent_file_returns_error`
  - [ ] `test_load_with_invalid_session_returns_400`
  - [ ] `test_save_file_writes_content`
  - [ ] `test_get_file_content`
  - [ ] `test_get_file_content_missing_file_returns_404`
  - [ ] `test_list_files_returns_htn_files`

- [ ] `test_query.py`
  - [ ] `test_execute_prolog_query`
  - [ ] `test_execute_prolog_query_no_results`
  - [ ] `test_execute_htn_query_finds_plan`
  - [ ] `test_execute_htn_query_no_solution`
  - [ ] `test_query_invalid_session_returns_400`
  - [ ] `test_query_without_loading_file`

- [ ] `test_health.py`
  - [ ] `test_health_returns_healthy`
  - [ ] `test_health_includes_session_count`

#### P1 - Extended Coverage Tests

- [ ] `test_state.py`
  - [ ] `test_get_state_returns_facts`
  - [ ] `test_get_state_diff_after_plan`
  - [ ] `test_state_invalid_session`

- [ ] `test_lint.py`
  - [ ] `test_lint_valid_content`
  - [ ] `test_lint_syntax_error`
  - [ ] `test_lint_file_path`
  - [ ] `test_lint_batch_multiple_files`
  - [ ] `test_lint_missing_file_returns_404`

- [ ] `test_analyze.py`
  - [ ] `test_analyze_returns_nodes_and_edges`
  - [ ] `test_analyze_detects_unreachable_code`
  - [ ] `test_analyze_batch`
  - [ ] `test_callgraph_endpoint`

- [ ] `test_invariants.py`
  - [ ] `test_get_invariants_list`
  - [ ] `test_enable_invariant`
  - [ ] `test_disable_invariant`
  - [ ] `test_configure_invariant`
  - [ ] `test_enable_nonexistent_invariant_returns_404`

### Phase 3: Integration with run_all_tests.py

Add to `run_all_tests.py`:

```python
def run_gui_tests() -> tuple[bool, int, int]:
    """Run GUI backend tests."""
    print_header("GUI Backend Tests")

    test_dir = Path("gui/tests")
    if not test_dir.exists():
        print(f"{YELLOW}Skipping: GUI tests not found{RESET}")
        return True, 0, 0

    start = time.time()
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "gui/tests", "-v", "--tb=short"],
        capture_output=True,
        text=True,
        cwd=str(Path.cwd())
    )
    elapsed = time.time() - start

    print(result.stdout)
    if result.stderr:
        print(result.stderr)

    # Parse pytest output
    # Look for "X passed" or "X passed, Y failed"
    passed = 0
    failed = 0
    for line in result.stdout.split('\n'):
        if 'passed' in line:
            import re
            match = re.search(r'(\d+) passed', line)
            if match:
                passed = int(match.group(1))
            match = re.search(r'(\d+) failed', line)
            if match:
                failed = int(match.group(1))

    total = passed + failed
    success = result.returncode == 0 and failed == 0

    print(f"\nTime: {elapsed:.2f}s")
    return success, passed, total
```

## Improvement Plan (Prioritized)

### P0 - Must Fix (Blocking Issues)

- [ ] Create `gui/tests/` directory structure
- [ ] Create `gui/tests/conftest.py` with Flask test client fixture
- [ ] Add pytest and pytest-cov to `gui/backend/requirements.txt`
- [ ] Implement `test_session.py` with basic CRUD tests
- [ ] Implement `test_file.py` with file operation tests
- [ ] Implement `test_query.py` with query execution tests
- [ ] Implement `test_health.py` for health endpoint
- [ ] Add GUI tests to `run_all_tests.py`
- [ ] Ensure all tests can run without external server

### P1 - Should Fix (Quality Issues)

- [ ] Implement `test_state.py` for state management
- [ ] Implement `test_lint.py` for linter endpoints
- [ ] Implement `test_analyze.py` for analyzer endpoints
- [ ] Implement `test_invariants.py` for invariant endpoints
- [ ] Add error case tests (400, 404, 500 responses)
- [ ] Add test fixtures (valid/invalid HTN files)
- [ ] Add unit tests for HtnService methods
- [ ] Add unit tests for HtnLinter class
- [ ] Add unit tests for HtnAnalyzer class

### P2 - Nice to Have (Enhancements)

- [ ] Add test coverage reporting
- [ ] Add CORS testing
- [ ] Add concurrent request testing
- [ ] Add performance benchmarks
- [ ] Add integration tests with real HTN planning
- [ ] Add snapshot testing for API responses
- [ ] Migrate manual scripts to executable documentation

## Appendix: Test Example Templates

### Flask Test Client Example

```python
# gui/tests/test_session.py
import pytest

class TestSessionEndpoints:
    """Test session management endpoints"""

    def test_create_session_returns_session_id(self, client):
        """POST /api/session/create should return a session_id"""
        response = client.post('/api/session/create')

        assert response.status_code == 200
        data = response.get_json()
        assert 'session_id' in data
        assert 'status' in data
        assert data['status'] == 'created'
        assert len(data['session_id']) == 36  # UUID format

    def test_delete_session_removes_session(self, client, session):
        """DELETE /api/session/delete/<id> should remove session"""
        # Session exists
        response = client.post('/api/file/load', json={
            'session_id': session,
            'file_path': 'Examples/Taxi.htn'
        })
        assert response.status_code == 200

        # Delete it
        response = client.delete(f'/api/session/delete/{session}')
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'deleted'

        # Now session should not exist
        response = client.post('/api/file/load', json={
            'session_id': session,
            'file_path': 'Examples/Taxi.htn'
        })
        assert response.status_code == 400

    def test_delete_nonexistent_session_returns_404(self, client):
        """DELETE with invalid session_id should return 404"""
        response = client.delete('/api/session/delete/invalid-session-id')

        assert response.status_code == 404
        data = response.get_json()
        assert 'error' in data
```

### Query Test Example

```python
# gui/tests/test_query.py
import pytest

class TestQueryEndpoints:
    """Test query execution endpoints"""

    def test_execute_prolog_query(self, client, loaded_session):
        """POST /api/query/execute should return query results"""
        response = client.post('/api/query/execute', json={
            'session_id': loaded_session,
            'query': 'at(?where).'
        })

        assert response.status_code == 200
        data = response.get_json()
        assert 'solutions' in data
        assert 'total_count' in data
        assert data['total_count'] > 0

    def test_execute_htn_query_finds_plan(self, client, loaded_session):
        """POST /api/htn/execute should return plan and trees"""
        response = client.post('/api/htn/execute', json={
            'session_id': loaded_session,
            'query': 'travel-to(uptown).'
        })

        assert response.status_code == 200
        data = response.get_json()
        assert 'solutions' in data
        assert 'trees' in data
        assert 'total_count' in data
        assert data['total_count'] >= 1

    def test_query_invalid_session_returns_400(self, client):
        """Query with invalid session should return 400"""
        response = client.post('/api/query/execute', json={
            'session_id': 'invalid-session',
            'query': 'test.'
        })

        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
        assert 'Invalid session' in data['error']
```

## Conclusion

The GUI/Backend test suite requires a complete rewrite to move from manual verification scripts to automated pytest tests. The migration should prioritize:

1. **Infrastructure first**: Set up pytest fixtures and test client
2. **Core endpoints next**: Session, file, and query operations
3. **Extended coverage last**: Linting, analysis, and invariants

The current 0% automated coverage is a significant risk for the project. The proposed plan addresses this systematically while providing clear examples and priorities for implementation.
