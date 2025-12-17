# Test Review: MCP Server Tests

## Summary
- Tests analyzed: 4 test files
- Files reviewed: 6 (4 test files + 2 source files)
- Issues found: 14 (4 critical, 6 medium, 4 low)

## Tool Coverage Matrix

The MCP server exposes 11 tools (7 original + 4 new). Current test coverage:

| Tool | Tested? | Happy Path | Error Cases | Edge Cases |
|------|---------|------------|-------------|------------|
| indhtn_start_session | Yes | Yes | Partial | No |
| indhtn_query | Yes | Yes | Partial | No |
| indhtn_find_plans | Yes | Yes | No | No |
| indhtn_apply_plan | No | No | No | No |
| indhtn_reset | Yes | Yes | No | No |
| indhtn_toggle_trace | Yes | Yes | No | No |
| indhtn_end_session | Yes | Yes | No | No |
| indhtn_lint | Yes | Yes | No | No |
| indhtn_introspect | Yes | Yes | No | No |
| indhtn_state_diff | No | No | No | No |
| indhtn_step | No | No | No | No |

**Coverage Score: 8/11 tools have any test coverage (73%)**
**Quality Score: 2/11 tools have error/edge case coverage (18%)**

## Critique

### What's Working Well

1. **Basic session lifecycle tested** - `test_session_only.py` and `test_server.py` both verify session creation, query execution, and cleanup.

2. **Platform-aware executable discovery** - Tests correctly handle Windows vs Unix executable paths.

3. **Error classification exists** - `test_server.py` includes `test_error_handling()` that tests invalid session IDs and syntax errors.

4. **Optimization pattern validation** - `test_optimization_patterns.py` is well-designed with clear before/after comparisons and quantitative metrics.

5. **Parser integration tests** - `test_new_tools.py` validates lint and introspect functionality against real HTN source.

### Issues Found

#### Critical Issues

1. **[CRITICAL] No pytest framework - Manual print-based assertions**
   - File: All test files
   - Issue: Tests use `print("[PASS]")` / `print("[FAIL]")` instead of proper assertions
   - Impact: No test discovery, no CI integration, no test isolation guarantees
   - Evidence:
     ```python
     # test_session_only.py:51
     print(f"[PASS] Session created: {session_id}")
     # Should be:
     assert session_id is not None
     ```

2. **[CRITICAL] Missing coverage for indhtn_apply_plan**
   - File: All test files
   - Issue: The `indhtn_apply_plan` tool has zero test coverage
   - Impact: State modification is untested - a core feature
   - This tool actually modifies world state, making it the highest-risk untested tool

3. **[CRITICAL] Missing coverage for indhtn_state_diff**
   - File: All test files
   - Issue: The `indhtn_state_diff` tool (added in recent commit a50f1a2) is not tested
   - Impact: New functionality shipped without tests

4. **[CRITICAL] Missing coverage for indhtn_step**
   - File: All test files
   - Issue: The `indhtn_step` tool (added in recent commit d0773a2) is not tested
   - Impact: Step-by-step debugging functionality has no coverage

#### Medium Issues

5. **[MEDIUM] No async test isolation**
   - File: `test_server.py`, `test_session_only.py`
   - Issue: Tests run sequentially in a single async function, sharing state
   - Evidence:
     ```python
     # test_server.py:141
     success = loop.run_until_complete(test_session())
     if success:
         loop.run_until_complete(test_error_handling())
     ```
   - Impact: Test failures can cascade; no isolation between test cases

6. **[MEDIUM] Hardcoded file paths**
   - File: All test files
   - Issue: Tests use relative paths like `"../Examples/Taxi.htn"` without validation
   - Impact: Tests fail silently if run from different directory

7. **[MEDIUM] No concurrent session testing**
   - File: All test files
   - Issue: `SessionManager.max_sessions` and `_cleanup_oldest_session` are untested
   - Impact: Concurrent usage patterns could have race conditions

8. **[MEDIUM] No timeout edge case testing**
   - File: All test files
   - Issue: `execute_query` timeout handling is never tested
   - Evidence: `session.py:205-213` has timeout handling code that's never exercised

9. **[MEDIUM] Missing error recovery testing**
   - File: All test files
   - Issue: `_attempt_recovery()` method in `session.py:288-308` is never tested
   - Impact: Session crash recovery is untested

10. **[MEDIUM] test_new_tools.py is not async**
    - File: `test_new_tools.py`
    - Issue: Tests lint/introspect directly but not through MCP tool handlers
    - Impact: The actual MCP interface for these tools is untested

#### Low Issues

11. **[LOW] Inconsistent test output format**
    - Files: `test_session_only.py` uses `[PASS]`/`[FAIL]`, `test_server.py` uses checkmarks
    - Impact: Inconsistent test output makes manual review harder

12. **[LOW] No cleanup on test failure**
    - File: `test_session_only.py`, `test_server.py`
    - Issue: If a test fails mid-way, sessions may not be cleaned up
    - Evidence: No finally blocks or cleanup fixtures

13. **[LOW] test_optimization_patterns.py tests Python bindings, not MCP**
    - File: `test_optimization_patterns.py`
    - Issue: Tests `indhtnpy` directly, not the MCP server
    - Impact: Misplaced in mcp-server directory; should be in src/Python/

14. **[LOW] Missing docstrings in test functions**
    - Files: Most test files have minimal function documentation
    - Impact: Test purpose not clear from code

## Coverage Gaps

### Untested Scenarios by Tool

**indhtn_start_session**
- File not found error
- Invalid file format
- Working directory validation
- Maximum sessions reached

**indhtn_query**
- Query timeout
- Process crash during query
- Very long output handling
- Special characters in query

**indhtn_find_plans**
- No plans found (null result)
- maxPlans parameter functionality
- Complex nested plans
- Plan parsing edge cases

**indhtn_apply_plan**
- Everything (completely untested)
- State modification verification
- Rollback on failure

**indhtn_reset**
- Reset after state modification
- Reset with trace enabled
- Reset of crashed session

**indhtn_toggle_trace**
- Trace output verification
- Multiple toggle cycles
- Trace with long output

**indhtn_end_session**
- End non-existent session (should error)
- Double-end same session
- End session with pending query

**indhtn_lint** (via MCP)
- Empty source
- Very large source
- Linter unavailable fallback

**indhtn_introspect** (via MCP)
- Empty source
- Malformed HTN
- Parser unavailable fallback

**indhtn_state_diff**
- Everything (completely untested)

**indhtn_step**
- Everything (completely untested)

### Session Manager Untested Methods

- `_cleanup_oldest_session()` - LRU cleanup never tested
- `_attempt_recovery()` - Crash recovery never tested
- `_classify_error()` - Error classification never tested
- `end_all_sessions()` - Bulk cleanup never tested

## pytest-asyncio Migration Plan

### Phase 1: Setup (Day 1)

- [ ] Add `pytest-asyncio>=0.23.0` to mcp-server/requirements.txt
- [ ] Add `pytest>=8.0.0` to requirements
- [ ] Create `mcp-server/conftest.py` with shared fixtures:

```python
import pytest
import asyncio
from pathlib import Path

@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for entire test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def indhtn_path():
    """Get path to indhtn executable."""
    import platform
    exe_suffix = ".exe" if platform.system() == "Windows" else ""
    paths = [
        Path(__file__).parent.parent / "build" / "Release" / f"indhtn{exe_suffix}",
        Path(__file__).parent.parent / "build" / "Debug" / f"indhtn{exe_suffix}",
    ]
    for p in paths:
        if p.exists():
            return str(p)
    pytest.skip("indhtn executable not found")

@pytest.fixture
async def session_manager(indhtn_path):
    """Create a session manager and clean up after test."""
    from indhtn_mcp.session import SessionManager
    manager = SessionManager(indhtn_path)
    yield manager
    await manager.end_all_sessions()

@pytest.fixture
async def taxi_session(session_manager):
    """Create a session with Taxi.htn loaded."""
    session_id, _ = await session_manager.create_session(
        ["../Examples/Taxi.htn"]
    )
    yield session_id
    # Cleanup handled by session_manager fixture
```

### Phase 2: Migrate test_session_only.py (Day 2)

- [ ] Rename to `test_session_lifecycle.py`
- [ ] Convert to pytest-asyncio format:

```python
import pytest

@pytest.mark.asyncio
async def test_session_creation(session_manager):
    """Test that a session can be created successfully."""
    session_id, output = await session_manager.create_session(
        ["../Examples/Taxi.htn"]
    )
    assert session_id is not None
    assert len(session_id) == 36  # UUID format
    assert "Compilation" in output or output == ""

@pytest.mark.asyncio
async def test_query_execution(taxi_session, session_manager):
    """Test basic Prolog query execution."""
    result = await session_manager.execute_query(taxi_session, "at(?where).")
    assert result["success"] is True
    assert "downtown" in result["output"]

@pytest.mark.asyncio
async def test_session_cleanup(session_manager):
    """Test that sessions are properly cleaned up."""
    session_id, _ = await session_manager.create_session(
        ["../Examples/Taxi.htn"]
    )
    assert session_id in session_manager.sessions

    await session_manager.end_session(session_id)
    assert session_id not in session_manager.sessions
```

### Phase 3: Migrate test_server.py (Day 3)

- [ ] Rename to `test_mcp_tools.py`
- [ ] Add MCP server fixture:

```python
@pytest.fixture
async def mcp_server(indhtn_path):
    """Create MCP server instance."""
    from indhtn_mcp.server import IndHTNMCPServer
    server = IndHTNMCPServer(indhtn_path)
    yield server
    await server.session_manager.end_all_sessions()
```

- [ ] Convert error handling tests to parametrized tests

### Phase 4: Add Missing Tool Tests (Days 4-5)

- [ ] Create `test_apply_plan.py` - Full coverage for indhtn_apply_plan
- [ ] Create `test_state_diff.py` - Full coverage for indhtn_state_diff
- [ ] Create `test_step.py` - Full coverage for indhtn_step
- [ ] Create `test_lint_introspect.py` - MCP-level tests for lint/introspect

### Phase 5: Add Edge Case Tests (Day 6)

- [ ] Create `test_concurrency.py` - Concurrent session tests
- [ ] Create `test_recovery.py` - Timeout and crash recovery tests
- [ ] Create `test_errors.py` - Comprehensive error handling tests

## Improvement Plan (Prioritized)

### P0 - Must Fix (Before Next Release)

- [ ] **Add pytest-asyncio framework** - Foundation for all other improvements
  - Create conftest.py with fixtures
  - Add requirements.txt dependencies

- [ ] **Add tests for indhtn_apply_plan** - Critical untested functionality
  - Test successful plan application
  - Verify state changes
  - Test application failure

- [ ] **Add tests for indhtn_state_diff** - New feature untested
  - Test plan preview
  - Verify state is NOT modified
  - Test with invalid goals

- [ ] **Add tests for indhtn_step** - New feature untested
  - Test single operator execution
  - Verify state changes after step
  - Test invalid operator

### P1 - Should Fix (Next Sprint)

- [ ] **Add concurrent session tests**
  - Test max_sessions limit
  - Test LRU cleanup behavior
  - Test multiple parallel queries

- [ ] **Add timeout and recovery tests**
  - Test query timeout handling
  - Test session recovery after timeout
  - Test SIGINT recovery

- [ ] **Convert print-based tests to assertions**
  - Replace all `print("[PASS]")` with `assert` statements
  - Add meaningful assertion messages

- [ ] **Add cleanup fixtures**
  - Ensure sessions are cleaned up even on test failure
  - Add teardown hooks

### P2 - Nice to Have (Future)

- [ ] **Move test_optimization_patterns.py** to src/Python/tests/
  - It tests Python bindings, not MCP server

- [ ] **Add test coverage reporting**
  - Configure pytest-cov
  - Add coverage threshold requirements

- [ ] **Add parametrized tests for error types**
  - Test all error_type classifications
  - Test error message formatting

- [ ] **Add integration tests with real MCP protocol**
  - Test actual MCP message handling
  - Test tool listing response
  - Test end-to-end tool invocation

## Test File Relocation Recommendations

| Current Location | Recommended Location | Reason |
|------------------|---------------------|--------|
| mcp-server/test_optimization_patterns.py | src/Python/tests/test_optimization.py | Tests Python bindings, not MCP |
| mcp-server/test_new_tools.py | mcp-server/tests/test_lint_introspect.py | Should be in tests/ subdirectory |
| mcp-server/test_server.py | mcp-server/tests/test_mcp_tools.py | Should be in tests/ subdirectory |
| mcp-server/test_session_only.py | mcp-server/tests/test_session.py | Should be in tests/ subdirectory |

## Appendix: Server Tool Method Mapping

For reference, here is the mapping between MCP tools and their implementation methods:

| MCP Tool | Handler Method | Session Manager Method |
|----------|----------------|------------------------|
| indhtn_start_session | `_start_session` | `create_session` |
| indhtn_query | `_query` | `execute_query` |
| indhtn_find_plans | `_find_plans` | `execute_query` (with goals) |
| indhtn_apply_plan | `_apply_plan` | `execute_query` (with apply) |
| indhtn_reset | `_reset` | `execute_query` (/r) |
| indhtn_toggle_trace | `_toggle_trace` | `execute_query` (/t) |
| indhtn_end_session | `_end_session` | `end_session` |
| indhtn_lint | `_lint` | N/A (direct lint_htn call) |
| indhtn_introspect | `_introspect` | N/A (direct parse_htn call) |
| indhtn_state_diff | `_state_diff` | `get_state_diff` |
| indhtn_step | `_step` | `step_operator` |
