"""
pytest configuration and shared fixtures for GUI backend tests.

This conftest.py provides:
- Flask test client fixtures
- Session management fixtures with automatic cleanup
- Test data fixtures
"""

import pytest
import sys
import os
from pathlib import Path

# ============================================================================
# Path Setup
# ============================================================================

_current_dir = Path(__file__).parent
_gui_dir = _current_dir.parent
_backend_dir = _gui_dir / "backend"
_project_root = _gui_dir.parent

# Add backend to path
sys.path.insert(0, str(_backend_dir))
sys.path.insert(0, str(_project_root / "src" / "Python"))

# ============================================================================
# Flask App Fixtures
# ============================================================================

@pytest.fixture(scope="session")
def app():
    """Create Flask application for testing."""
    from app import app as flask_app

    flask_app.config.update({
        "TESTING": True,
        "DEBUG": False,
    })

    yield flask_app


@pytest.fixture(scope="function")
def client(app):
    """Create a Flask test client for each test."""
    with app.test_client() as test_client:
        yield test_client


@pytest.fixture(scope="function")
def runner(app):
    """Create a Flask CLI runner for testing CLI commands."""
    return app.test_cli_runner()


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
def fixtures_dir():
    """Return the test fixtures directory."""
    return _current_dir / "fixtures"


# ============================================================================
# Session Fixtures
# ============================================================================

@pytest.fixture(scope="function")
def session(client):
    """Create a session and return session_id, cleanup after test."""
    # Create session
    response = client.post('/api/session/create')
    assert response.status_code == 200, f"Failed to create session: {response.data}"

    data = response.get_json()
    session_id = data.get('session_id')
    assert session_id is not None, "No session_id in response"

    yield session_id

    # Cleanup: delete session
    client.delete(f'/api/session/delete/{session_id}')


@pytest.fixture(scope="function")
def loaded_session(client, session, examples_dir):
    """Session with Taxi.htn loaded."""
    taxi_path = str(examples_dir / "Taxi.htn")

    response = client.post('/api/file/load', json={
        'session_id': session,
        'file_path': taxi_path
    })

    if response.status_code != 200:
        pytest.fail(f"Failed to load Taxi.htn: {response.data}")

    return session


@pytest.fixture(scope="function")
def game_loaded_session(client, session, examples_dir):
    """Session with Game.htn loaded."""
    game_path = str(examples_dir / "Game.htn")

    response = client.post('/api/file/load', json={
        'session_id': session,
        'file_path': game_path
    })

    if response.status_code != 200:
        pytest.fail(f"Failed to load Game.htn: {response.data}")

    return session


# ============================================================================
# Test Data Fixtures
# ============================================================================

@pytest.fixture
def valid_htn_content():
    """Return valid HTN content for testing."""
    return """
    % Simple test domain
    at(downtown).
    distance(downtown, park, 2).

    walk(?from, ?to) :- del(at(?from)), add(at(?to)).

    travel-to(?dest) :- if(at(?start)), do(walk(?start, ?dest)).

    goals(travel-to(park)).
    """


@pytest.fixture
def invalid_htn_content():
    """Return invalid HTN content for testing linter."""
    return """
    % Missing closing parenthesis
    at(downtown.

    % Invalid syntax
    walk(?from, ?to) :- del(at(?from), add(at(?to)).
    """


@pytest.fixture
def empty_htn_content():
    """Return empty HTN content."""
    return ""


# ============================================================================
# Helper Functions
# ============================================================================

def assert_json_response(response, status_code=200):
    """Assert response is valid JSON with expected status code."""
    assert response.status_code == status_code, \
        f"Expected {status_code}, got {response.status_code}: {response.data}"
    assert response.content_type == 'application/json', \
        f"Expected JSON, got {response.content_type}"
    return response.get_json()


def assert_error_response(response, expected_status=400):
    """Assert response is an error with expected status code."""
    assert response.status_code == expected_status, \
        f"Expected {expected_status}, got {response.status_code}"
    data = response.get_json()
    assert 'error' in data, f"Expected 'error' in response: {data}"
    return data


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
