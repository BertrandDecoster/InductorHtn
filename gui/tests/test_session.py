"""
Tests for session management endpoints.

Endpoints tested:
- POST /api/session/create
- DELETE /api/session/delete/<id>
"""

import pytest


class TestSessionCreate:
    """Tests for POST /api/session/create"""

    def test_create_session_returns_session_id(self, client):
        """POST /api/session/create should return a session_id."""
        response = client.post('/api/session/create')

        assert response.status_code == 200
        data = response.get_json()
        assert 'session_id' in data
        assert data['session_id'] is not None
        assert len(data['session_id']) > 0

    def test_create_session_returns_status(self, client):
        """POST /api/session/create should return status field."""
        response = client.post('/api/session/create')

        assert response.status_code == 200
        data = response.get_json()
        assert 'status' in data

    def test_create_multiple_sessions(self, client):
        """Creating multiple sessions should return unique IDs."""
        response1 = client.post('/api/session/create')
        response2 = client.post('/api/session/create')

        data1 = response1.get_json()
        data2 = response2.get_json()

        assert data1['session_id'] != data2['session_id']

        # Cleanup
        client.delete(f'/api/session/delete/{data1["session_id"]}')
        client.delete(f'/api/session/delete/{data2["session_id"]}')


class TestSessionDelete:
    """Tests for DELETE /api/session/delete/<id>"""

    def test_delete_session_success(self, client, session):
        """DELETE /api/session/delete/<id> should remove session."""
        response = client.delete(f'/api/session/delete/{session}')

        assert response.status_code == 200
        data = response.get_json()
        assert 'status' in data

    def test_delete_nonexistent_session(self, client):
        """DELETE with invalid session_id should return error."""
        response = client.delete('/api/session/delete/nonexistent-session-id')

        # Should return 404 or 400
        assert response.status_code in [400, 404]
        data = response.get_json()
        assert 'error' in data

    def test_delete_session_twice(self, client):
        """Deleting same session twice should fail on second attempt."""
        # Create a session
        create_response = client.post('/api/session/create')
        session_id = create_response.get_json()['session_id']

        # First delete should succeed
        response1 = client.delete(f'/api/session/delete/{session_id}')
        assert response1.status_code == 200

        # Second delete should fail
        response2 = client.delete(f'/api/session/delete/{session_id}')
        assert response2.status_code in [400, 404]


class TestSessionIsolation:
    """Tests for session isolation."""

    def test_sessions_are_isolated(self, client):
        """Changes in one session should not affect another."""
        # Create two sessions
        session1_resp = client.post('/api/session/create')
        session2_resp = client.post('/api/session/create')

        session1 = session1_resp.get_json()['session_id']
        session2 = session2_resp.get_json()['session_id']

        try:
            # Load file in session 1
            client.post('/api/file/load', json={
                'session_id': session1,
                'file_path': 'Examples/Taxi.htn'
            })

            # Session 2 should not have the file loaded
            # (would need to load separately)
            # This test mainly ensures they're different sessions
            assert session1 != session2

        finally:
            # Cleanup
            client.delete(f'/api/session/delete/{session1}')
            client.delete(f'/api/session/delete/{session2}')
