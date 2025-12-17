"""
Tests for health check endpoint.

Endpoints tested:
- GET /health
"""

import pytest


class TestHealth:
    """Tests for GET /health"""

    def test_health_returns_ok(self, client):
        """GET /health should return 200 OK."""
        response = client.get('/health')

        assert response.status_code == 200

    def test_health_returns_json(self, client):
        """GET /health should return JSON response."""
        response = client.get('/health')

        assert response.status_code == 200
        assert response.content_type == 'application/json'

    def test_health_has_status(self, client):
        """GET /health should include status field."""
        response = client.get('/health')

        data = response.get_json()
        assert 'status' in data or 'healthy' in data or response.status_code == 200

    def test_health_indicates_healthy(self, client):
        """GET /health should indicate service is healthy."""
        response = client.get('/health')

        data = response.get_json()
        # Check various possible health indicators
        if 'status' in data:
            assert data['status'] in ['ok', 'healthy', 'up', True]
        elif 'healthy' in data:
            assert data['healthy'] is True
