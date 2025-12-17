"""
pytest configuration and shared fixtures for MCP server tests.

This conftest.py provides:
- pytest-asyncio configuration
- Fixtures for SessionManager and MCP server
- Automatic session cleanup
"""

import pytest
import asyncio
import sys
import os
import platform
from pathlib import Path

# ============================================================================
# Path Setup
# ============================================================================

_current_dir = Path(__file__).parent
_mcp_server_dir = _current_dir.parent
_project_root = _mcp_server_dir.parent

# Add MCP server package to path
sys.path.insert(0, str(_mcp_server_dir))

# ============================================================================
# pytest-asyncio Configuration
# ============================================================================

@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for the entire test session."""
    if platform.system() == "Windows":
        # Use ProactorEventLoop on Windows for subprocess support
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# ============================================================================
# Path Fixtures
# ============================================================================

@pytest.fixture(scope="session")
def project_root():
    """Return the project root directory."""
    return _project_root


@pytest.fixture(scope="session")
def examples_dir(project_root):
    """Return the Examples directory."""
    return project_root / "Examples"


@pytest.fixture(scope="session")
def indhtn_path(project_root):
    """Get path to indhtn executable."""
    exe_suffix = ".exe" if platform.system() == "Windows" else ""

    # Try Release first, then Debug
    paths = [
        project_root / "build" / "Release" / f"indhtn{exe_suffix}",
        project_root / "build" / "Debug" / f"indhtn{exe_suffix}",
    ]

    for p in paths:
        if p.exists():
            return str(p)

    pytest.skip(f"indhtn executable not found. Build the project first.")


# ============================================================================
# Session Manager Fixtures
# ============================================================================

@pytest.fixture(scope="module")
async def session_manager(indhtn_path):
    """Create a SessionManager shared across module tests."""
    # Import directly from session.py to avoid loading server.py
    # (which has mcp module dependencies that may not be available)
    import importlib.util
    session_path = _mcp_server_dir / "indhtn_mcp" / "session.py"
    spec = importlib.util.spec_from_file_location("session", session_path)
    session_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(session_module)
    SessionManager = session_module.SessionManager

    manager = SessionManager(indhtn_path)
    yield manager

    # Cleanup: end all sessions
    await manager.end_all_sessions()


@pytest.fixture(scope="module")
async def taxi_session(session_manager, examples_dir):
    """Create a session with Taxi.htn loaded, shared across module tests."""
    taxi_path = str(examples_dir / "Taxi.htn")
    session_id, output = await session_manager.create_session([taxi_path])

    if session_id is None:
        pytest.fail(f"Failed to create session: {output}")

    yield session_id
    # Cleanup handled by session_manager fixture


@pytest.fixture
async def game_session(session_manager, examples_dir):
    """Create a session with Game.htn loaded."""
    game_path = str(examples_dir / "Game.htn")
    session_id, output = await session_manager.create_session([game_path])

    if session_id is None:
        pytest.fail(f"Failed to create session: {output}")

    yield session_id


# ============================================================================
# MCP Server Fixtures
# ============================================================================

@pytest.fixture
async def mcp_server(indhtn_path):
    """Create an MCP server instance."""
    try:
        from indhtn_mcp.server import create_server
        server = create_server(indhtn_path)
        yield server
        # Cleanup
        if hasattr(server, 'session_manager'):
            await server.session_manager.end_all_sessions()
    except ImportError:
        pytest.skip("MCP server module not available")


# ============================================================================
# Helper Fixtures
# ============================================================================

@pytest.fixture
def taxi_htn_content(examples_dir):
    """Return the content of Taxi.htn file."""
    taxi_path = examples_dir / "Taxi.htn"
    if taxi_path.exists():
        return taxi_path.read_text()
    pytest.skip("Taxi.htn not found")


@pytest.fixture
def sample_htn_source():
    """Return a simple HTN source for testing."""
    return """
    % Simple test domain
    at(downtown).
    distance(downtown, park, 2).

    walk(?from, ?to) :- del(at(?from)), add(at(?to)).

    travel-to(?dest) :- if(at(?start)), do(walk(?start, ?dest)).

    goals(travel-to(park)).
    """


# ============================================================================
# pytest Configuration
# ============================================================================

def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )


# Mark all tests in this directory as asyncio by default
pytest_plugins = ('pytest_asyncio',)
