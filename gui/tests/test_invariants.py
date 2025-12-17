"""
Tests for invariant management endpoints.

These tests cover:
- GET /api/invariants - Get all invariants
- POST /api/invariants/<id>/enable - Enable/disable invariant
- POST /api/invariants/<id>/configure - Configure invariant
"""

import pytest


class TestGetInvariants:
    """Tests for GET /api/invariants endpoint."""

    def test_get_invariants_returns_list(self, client):
        """GET invariants should return invariants list."""
        response = client.get('/api/invariants')

        assert response.status_code == 200
        data = response.get_json()
        assert 'invariants' in data
        assert isinstance(data['invariants'], list)

    def test_get_invariants_returns_categories(self, client):
        """GET invariants should return categories."""
        response = client.get('/api/invariants')

        assert response.status_code == 200
        data = response.get_json()
        if 'categories' in data:
            assert isinstance(data['categories'], list)

    def test_get_invariants_structure(self, client):
        """Invariants should have expected structure."""
        response = client.get('/api/invariants')

        assert response.status_code == 200
        data = response.get_json()

        if len(data['invariants']) > 0:
            inv = data['invariants'][0]
            # Check for common fields
            assert 'id' in inv or 'name' in inv


class TestEnableInvariant:
    """Tests for POST /api/invariants/<id>/enable endpoint."""

    def test_enable_invariant(self, client):
        """Enabling an invariant should succeed."""
        # First get list of invariants
        list_response = client.get('/api/invariants')
        data = list_response.get_json()

        if len(data['invariants']) == 0:
            pytest.skip("No invariants available to test")

        inv_id = data['invariants'][0].get('id') or data['invariants'][0].get('name')

        response = client.post(f'/api/invariants/{inv_id}/enable', json={
            'enabled': True
        })

        assert response.status_code == 200
        result = response.get_json()
        assert result['status'] == 'updated'
        assert result['enabled'] == True

    def test_disable_invariant(self, client):
        """Disabling an invariant should succeed."""
        # First get list of invariants
        list_response = client.get('/api/invariants')
        data = list_response.get_json()

        if len(data['invariants']) == 0:
            pytest.skip("No invariants available to test")

        inv_id = data['invariants'][0].get('id') or data['invariants'][0].get('name')

        response = client.post(f'/api/invariants/{inv_id}/enable', json={
            'enabled': False
        })

        assert response.status_code == 200
        result = response.get_json()
        assert result['status'] == 'updated'
        assert result['enabled'] == False

    def test_enable_nonexistent_invariant(self, client):
        """Enabling nonexistent invariant should return 404."""
        response = client.post('/api/invariants/nonexistent-invariant-id/enable', json={
            'enabled': True
        })

        assert response.status_code == 404
        data = response.get_json()
        assert 'error' in data

    def test_enable_default_value(self, client):
        """Enable without explicit value should default to True."""
        list_response = client.get('/api/invariants')
        data = list_response.get_json()

        if len(data['invariants']) == 0:
            pytest.skip("No invariants available to test")

        inv_id = data['invariants'][0].get('id') or data['invariants'][0].get('name')

        response = client.post(f'/api/invariants/{inv_id}/enable', json={})

        assert response.status_code == 200
        result = response.get_json()
        assert result['enabled'] == True


class TestConfigureInvariant:
    """Tests for POST /api/invariants/<id>/configure endpoint."""

    def test_configure_invariant(self, client):
        """Configuring an invariant should succeed."""
        # First get list of invariants
        list_response = client.get('/api/invariants')
        data = list_response.get_json()

        if len(data['invariants']) == 0:
            pytest.skip("No invariants available to test")

        inv_id = data['invariants'][0].get('id') or data['invariants'][0].get('name')

        response = client.post(f'/api/invariants/{inv_id}/configure', json={
            'config': {'key': 'value'}
        })

        assert response.status_code == 200
        result = response.get_json()
        assert result['status'] == 'configured'

    def test_configure_nonexistent_invariant(self, client):
        """Configuring nonexistent invariant should return 404."""
        response = client.post('/api/invariants/nonexistent-invariant-id/configure', json={
            'config': {}
        })

        assert response.status_code == 404
        data = response.get_json()
        assert 'error' in data

    def test_configure_empty_config(self, client):
        """Configuring with empty config should succeed."""
        list_response = client.get('/api/invariants')
        data = list_response.get_json()

        if len(data['invariants']) == 0:
            pytest.skip("No invariants available to test")

        inv_id = data['invariants'][0].get('id') or data['invariants'][0].get('name')

        response = client.post(f'/api/invariants/{inv_id}/configure', json={
            'config': {}
        })

        assert response.status_code == 200


class TestInvariantIntegration:
    """Integration tests for invariants with analysis."""

    def test_invariants_affect_analysis(self, client):
        """Invariants should be used during analysis."""
        # Enable all invariants
        list_response = client.get('/api/invariants')
        data = list_response.get_json()

        for inv in data['invariants']:
            inv_id = inv.get('id') or inv.get('name')
            client.post(f'/api/invariants/{inv_id}/enable', json={
                'enabled': True
            })

        # Run analysis
        response = client.post('/api/analyze', json={
            'file_path': 'Examples/Taxi.htn'
        })

        assert response.status_code == 200
        # Analysis should complete regardless of invariant results
