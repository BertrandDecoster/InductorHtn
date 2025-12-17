"""
pytest configuration and shared fixtures for InductorHTN Python tests.

This conftest.py handles:
- Path setup (eliminating sys.path manipulation in individual test files)
- Shared fixtures for HtnPlanner, HtnTestSuite, HtnService
- Project root detection
"""

import pytest
import sys
import os
from pathlib import Path

# ============================================================================
# Path Setup - Do this ONCE at the package level
# ============================================================================

# Find project root (contains Examples/)
_current_dir = Path(__file__).parent
_project_root = _current_dir.parent.parent.parent  # src/Python/tests -> project root

# Verify we found the right directory
if not (_project_root / "Examples").exists():
    # Fallback: search upward
    _search = _current_dir
    while _search != _search.parent:
        if (_search / "Examples").exists():
            _project_root = _search
            break
        _search = _search.parent

# Add necessary paths
_python_dir = _project_root / "src" / "Python"
_backend_dir = _project_root / "gui" / "backend"

sys.path.insert(0, str(_python_dir))
sys.path.insert(0, str(_backend_dir))

# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture(scope="session")
def project_root():
    """Return the project root directory."""
    return _project_root


@pytest.fixture(scope="session")
def examples_dir(project_root):
    """Return the Examples directory path."""
    return project_root / "Examples"


@pytest.fixture(scope="function")
def htn_planner():
    """Create a fresh HtnPlanner instance for each test."""
    from indhtnpy import HtnPlanner
    planner = HtnPlanner(False)  # No debug output
    yield planner
    # Cleanup handled by garbage collection


@pytest.fixture(scope="function")
def htn_planner_debug():
    """Create a fresh HtnPlanner instance with debug enabled."""
    from indhtnpy import HtnPlanner
    planner = HtnPlanner(True)  # Debug output enabled
    yield planner


@pytest.fixture(scope="function")
def taxi_suite(project_root):
    """Create HtnTestSuite loaded with Taxi.htn."""
    from htn_test_framework import HtnTestSuite
    suite = HtnTestSuite(str(project_root / "Examples" / "Taxi.htn"), verbose=False)
    yield suite


@pytest.fixture(scope="function")
def game_suite(project_root):
    """Create HtnTestSuite loaded with Game.htn."""
    from htn_test_framework import HtnTestSuite
    suite = HtnTestSuite(str(project_root / "Examples" / "Game.htn"), verbose=False)
    yield suite


@pytest.fixture(scope="function")
def empty_suite():
    """Create an empty HtnTestSuite (no file loaded)."""
    from htn_test_framework import HtnTestSuite
    suite = HtnTestSuite(verbose=False)
    yield suite


@pytest.fixture(scope="function")
def htn_service():
    """Create a fresh HtnService instance."""
    try:
        from htn_service import HtnService
        service = HtnService()
        yield service
    except ImportError:
        pytest.skip("HtnService not available (gui/backend not in path)")


@pytest.fixture(scope="function")
def loaded_taxi_service(htn_service, project_root):
    """HtnService with Taxi.htn pre-loaded."""
    taxi_path = str(project_root / "Examples" / "Taxi.htn")
    success, error = htn_service.load_file(taxi_path)
    if not success:
        pytest.fail(f"Failed to load Taxi.htn: {error}")
    return htn_service


@pytest.fixture(scope="function")
def loaded_game_service(htn_service, project_root):
    """HtnService with Game.htn pre-loaded."""
    game_path = str(project_root / "Examples" / "Game.htn")
    success, error = htn_service.load_file(game_path)
    if not success:
        pytest.fail(f"Failed to load Game.htn: {error}")
    return htn_service


# ============================================================================
# Pytest Configuration
# ============================================================================

def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers based on test names."""
    for item in items:
        # Mark integration tests
        if "integration" in item.nodeid.lower():
            item.add_marker(pytest.mark.integration)

        # Mark slow tests (can be customized based on known slow tests)
        if "performance" in item.nodeid.lower():
            item.add_marker(pytest.mark.slow)
