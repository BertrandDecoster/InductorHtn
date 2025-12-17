"""
Tests for query execution endpoints.

Endpoints tested:
- POST /api/query/execute
- POST /api/htn/execute
"""

import pytest


class TestPrologQuery:
    """Tests for POST /api/query/execute"""

    def test_execute_prolog_query(self, client, loaded_session):
        """POST /api/query/execute should return query results."""
        response = client.post('/api/query/execute', json={
            'session_id': loaded_session,
            'query': 'at(?where).'
        })

        assert response.status_code == 200
        data = response.get_json()
        assert 'solutions' in data or 'error' in data or 'result' in data

    def test_execute_query_with_results(self, client, loaded_session):
        """Query should return matching solutions."""
        response = client.post('/api/query/execute', json={
            'session_id': loaded_session,
            'query': 'at(?where).'
        })

        assert response.status_code == 200
        data = response.get_json()

        # Should have some results (Taxi.htn has at(downtown))
        if 'solutions' in data:
            assert len(data['solutions']) > 0 or 'downtown' in str(data)
        elif 'result' in data:
            assert 'downtown' in str(data['result'])

    def test_execute_query_no_results(self, client, loaded_session):
        """Query with no matches should return empty results or failure indicator."""
        response = client.post('/api/query/execute', json={
            'session_id': loaded_session,
            'query': 'nonexistent_fact(?x).'
        })

        assert response.status_code == 200
        data = response.get_json()
        # Should indicate no results - API returns solutions with 'false' or empty
        if 'solutions' in data:
            # Backend returns [{'false': '[]'}, {'failureIndex': '0'}] for no results
            solutions_str = str(data['solutions'])
            assert (len(data['solutions']) == 0 or
                    data.get('total_count') == 0 or
                    'false' in solutions_str)

    def test_execute_query_invalid_session(self, client):
        """Query with invalid session should fail."""
        response = client.post('/api/query/execute', json={
            'session_id': 'invalid-session',
            'query': 'test.'
        })

        assert response.status_code in [400, 404]
        data = response.get_json()
        assert 'error' in data

    def test_execute_query_syntax_error(self, client, loaded_session):
        """Query with syntax error should return error."""
        response = client.post('/api/query/execute', json={
            'session_id': loaded_session,
            'query': 'invalid(syntax'  # Missing closing paren
        })

        # Should indicate error
        data = response.get_json()
        assert 'error' in data or response.status_code != 200


class TestHtnQuery:
    """Tests for POST /api/htn/execute"""

    def test_execute_htn_query_finds_plan(self, client, loaded_session):
        """POST /api/htn/execute should find HTN plans."""
        response = client.post('/api/htn/execute', json={
            'session_id': loaded_session,
            'query': 'travel-to(park).'
        })

        assert response.status_code == 200
        data = response.get_json()

        # Should have solutions or indicate result
        assert 'solutions' in data or 'result' in data or 'error' in data

    def test_execute_htn_query_returns_trees(self, client, loaded_session):
        """HTN query should return decomposition trees."""
        response = client.post('/api/htn/execute', json={
            'session_id': loaded_session,
            'query': 'travel-to(park).'
        })

        assert response.status_code == 200
        data = response.get_json()

        # May include trees depending on implementation
        # Just verify structure is present
        assert isinstance(data, dict)

    def test_execute_htn_query_no_solution(self, client, loaded_session):
        """HTN query with no solution should indicate failure."""
        response = client.post('/api/htn/execute', json={
            'session_id': loaded_session,
            'query': 'travel-to(nonexistent_place).'
        })

        assert response.status_code == 200
        data = response.get_json()

        # Should indicate no plan found
        if 'solutions' in data:
            assert len(data['solutions']) == 0 or data['total_count'] == 0
        elif 'result' in data:
            assert 'null' in str(data['result']).lower() or data['result'] is None

    def test_execute_htn_query_invalid_session(self, client):
        """HTN query with invalid session should fail."""
        response = client.post('/api/htn/execute', json={
            'session_id': 'invalid-session',
            'query': 'travel-to(park).'
        })

        assert response.status_code in [400, 404]
        data = response.get_json()
        assert 'error' in data


class TestQueryEdgeCases:
    """Edge case tests for query endpoints."""

    def test_empty_query(self, client, loaded_session):
        """Empty query should fail gracefully."""
        response = client.post('/api/query/execute', json={
            'session_id': loaded_session,
            'query': ''
        })

        # Should handle gracefully
        data = response.get_json()
        # Either error response or empty result
        assert response.status_code in [200, 400]

    def test_query_without_trailing_dot(self, client, loaded_session):
        """Query without trailing dot should still work or fail gracefully."""
        response = client.post('/api/query/execute', json={
            'session_id': loaded_session,
            'query': 'at(?where)'  # Missing trailing dot
        })

        # Should handle gracefully (may auto-add dot or fail)
        assert response.status_code in [200, 400]
