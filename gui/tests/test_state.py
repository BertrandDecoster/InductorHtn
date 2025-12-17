"""
Tests for state management endpoints.

These tests cover:
- GET /api/state/get - Get current facts
- POST /api/state/diff - Get state diff after solution
"""

import pytest


class TestStateGet:
    """Tests for /api/state/get endpoint."""

    def test_get_state_returns_facts(self, client, loaded_session):
        """GET state should return current facts."""
        response = client.post('/api/state/get', json={
            'session_id': loaded_session
        })

        assert response.status_code == 200
        data = response.get_json()
        assert 'facts' in data
        assert isinstance(data['facts'], list)

    def test_get_state_includes_initial_facts(self, client, loaded_session):
        """State should include facts from loaded HTN file."""
        response = client.post('/api/state/get', json={
            'session_id': loaded_session
        })

        assert response.status_code == 200
        data = response.get_json()
        facts = data['facts']

        # Taxi.htn should have at(downtown) as initial fact
        fact_strings = [str(f) for f in facts]
        has_at_downtown = any('at' in s and 'downtown' in s for s in fact_strings)
        assert has_at_downtown, f"Expected 'at(downtown)' in facts from Taxi.htn, got: {fact_strings}"

    def test_get_state_invalid_session(self, client):
        """GET state with invalid session should return 400."""
        response = client.post('/api/state/get', json={
            'session_id': 'invalid-session-id'
        })

        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data

    def test_get_state_missing_session_id(self, client):
        """GET state without session_id should return 400."""
        response = client.post('/api/state/get', json={})

        assert response.status_code == 400


class TestStateDiff:
    """Tests for /api/state/diff endpoint."""

    def test_get_state_diff_structure(self, client, loaded_session):
        """State diff should return proper structure."""
        # First execute a plan to have a solution
        client.post('/api/htn/execute', json={
            'session_id': loaded_session,
            'query': 'travel-to(park).'
        })

        response = client.post('/api/state/diff', json={
            'session_id': loaded_session,
            'solution_index': 0
        })

        assert response.status_code == 200
        data = response.get_json()
        # Should have some diff structure
        assert isinstance(data, dict)

    def test_get_state_diff_default_index(self, client, loaded_session):
        """State diff should default to solution_index 0."""
        # Execute a plan
        client.post('/api/htn/execute', json={
            'session_id': loaded_session,
            'query': 'travel-to(park).'
        })

        # Call without solution_index
        response = client.post('/api/state/diff', json={
            'session_id': loaded_session
        })

        assert response.status_code == 200

    def test_get_state_diff_invalid_session(self, client):
        """State diff with invalid session should return 400."""
        response = client.post('/api/state/diff', json={
            'session_id': 'invalid-session-id',
            'solution_index': 0
        })

        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data

    def test_get_state_diff_without_plan(self, client, loaded_session):
        """State diff without executing plan should handle gracefully."""
        response = client.post('/api/state/diff', json={
            'session_id': loaded_session,
            'solution_index': 0
        })

        # Should return 200 even if no solution exists (may have empty diff)
        assert response.status_code == 200


class TestStateAfterPlan:
    """Tests for state changes after plan execution."""

    def test_htn_execute_returns_valid_response(self, client, loaded_session):
        """HTN execute should return valid plan response."""
        # Execute a travel plan
        plan_response = client.post('/api/htn/execute', json={
            'session_id': loaded_session,
            'query': 'travel-to(park).'
        })

        assert plan_response.status_code == 200
        data = plan_response.get_json()
        # Should have some response data
        assert data is not None

    def test_state_endpoint_works_after_htn_execute(self, client, loaded_session):
        """State endpoint should work after HTN execution."""
        # Execute a plan first
        client.post('/api/htn/execute', json={
            'session_id': loaded_session,
            'query': 'travel-to(park).'
        })

        # State endpoint should still work
        state_response = client.post('/api/state/get', json={
            'session_id': loaded_session
        })

        assert state_response.status_code == 200
        data = state_response.get_json()
        assert 'facts' in data
        assert isinstance(data['facts'], list)
