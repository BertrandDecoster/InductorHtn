"""
Tests for semantic analysis endpoints.

These tests cover:
- POST /api/analyze - Analyze HTN content or file
- POST /api/analyze/batch - Analyze multiple files
- POST /api/callgraph - Get call graph for visualization
"""

import pytest


class TestAnalyzeContent:
    """Tests for /api/analyze endpoint with content."""

    def test_analyze_valid_content(self, client, valid_htn_content):
        """Analyzing valid content should return analysis results."""
        response = client.post('/api/analyze', json={
            'content': valid_htn_content
        })

        assert response.status_code == 200
        data = response.get_json()
        # Check expected fields
        assert 'nodes' in data
        assert 'edges' in data

    def test_analyze_returns_nodes_and_edges(self, client, valid_htn_content):
        """Analysis should return nodes and edges for call graph."""
        response = client.post('/api/analyze', json={
            'content': valid_htn_content
        })

        assert response.status_code == 200
        data = response.get_json()
        assert isinstance(data['nodes'], (dict, list))
        assert isinstance(data['edges'], list)

    def test_analyze_returns_stats(self, client, valid_htn_content):
        """Analysis should return statistics."""
        response = client.post('/api/analyze', json={
            'content': valid_htn_content
        })

        assert response.status_code == 200
        data = response.get_json()
        if 'stats' in data:
            assert isinstance(data['stats'], dict)

    def test_analyze_empty_content(self, client, empty_htn_content):
        """Analyzing empty content should handle gracefully."""
        response = client.post('/api/analyze', json={
            'content': empty_htn_content
        })

        assert response.status_code == 200


class TestAnalyzeFile:
    """Tests for /api/analyze endpoint with file_path."""

    def test_analyze_valid_file(self, client):
        """Analyzing a valid HTN file should succeed."""
        response = client.post('/api/analyze', json={
            'file_path': 'Examples/Taxi.htn'
        })

        assert response.status_code == 200
        data = response.get_json()
        assert 'nodes' in data
        assert 'edges' in data

    def test_analyze_complex_file(self, client):
        """Analyzing a complex file should return rich analysis."""
        response = client.post('/api/analyze', json={
            'file_path': 'Examples/Game.htn'
        })

        assert response.status_code == 200
        data = response.get_json()
        # Game.htn is complex, should have multiple nodes
        assert 'nodes' in data

    def test_analyze_nonexistent_file(self, client):
        """Analyzing nonexistent file should return 404."""
        response = client.post('/api/analyze', json={
            'file_path': 'Examples/NonExistent.htn'
        })

        assert response.status_code == 404
        data = response.get_json()
        assert 'error' in data

    def test_analyze_missing_params(self, client):
        """Analyzing without content or file_path should return 400."""
        response = client.post('/api/analyze', json={})

        assert response.status_code == 400


class TestAnalyzeBatch:
    """Tests for /api/analyze/batch endpoint."""

    def test_analyze_batch_multiple_files(self, client):
        """Batch analyzing multiple files should return results for each."""
        response = client.post('/api/analyze/batch', json={
            'file_paths': ['Examples/Taxi.htn', 'Examples/Game.htn']
        })

        assert response.status_code == 200
        data = response.get_json()
        assert 'results' in data
        assert 'Examples/Taxi.htn' in data['results']
        assert 'Examples/Game.htn' in data['results']

    def test_analyze_batch_single_file(self, client):
        """Batch analyzing a single file should work."""
        response = client.post('/api/analyze/batch', json={
            'file_paths': ['Examples/Taxi.htn']
        })

        assert response.status_code == 200
        data = response.get_json()
        assert 'results' in data

    def test_analyze_batch_mixed_valid_invalid(self, client):
        """Batch analyzing with invalid paths should handle gracefully."""
        response = client.post('/api/analyze/batch', json={
            'file_paths': ['Examples/Taxi.htn', 'Examples/NonExistent.htn']
        })

        assert response.status_code == 200
        data = response.get_json()
        assert 'results' in data
        # Valid file should have analysis
        assert 'nodes' in data['results']['Examples/Taxi.htn']
        # Invalid file should have error
        assert 'error' in data['results']['Examples/NonExistent.htn']

    def test_analyze_batch_empty_array(self, client):
        """Batch analyzing with empty array should return 400."""
        response = client.post('/api/analyze/batch', json={
            'file_paths': []
        })

        assert response.status_code == 400


class TestCallgraph:
    """Tests for /api/callgraph endpoint."""

    def test_callgraph_valid_content(self, client, valid_htn_content):
        """Callgraph should return nodes and edges."""
        response = client.post('/api/callgraph', json={
            'content': valid_htn_content
        })

        assert response.status_code == 200
        data = response.get_json()
        assert 'nodes' in data
        assert 'edges' in data

    def test_callgraph_valid_file(self, client):
        """Callgraph from file should return nodes and edges."""
        response = client.post('/api/callgraph', json={
            'file_path': 'Examples/Taxi.htn'
        })

        assert response.status_code == 200
        data = response.get_json()
        assert 'nodes' in data
        assert 'edges' in data

    def test_callgraph_returns_goals(self, client):
        """Callgraph should return goals."""
        response = client.post('/api/callgraph', json={
            'file_path': 'Examples/Taxi.htn'
        })

        assert response.status_code == 200
        data = response.get_json()
        if 'goals' in data:
            assert isinstance(data['goals'], list)

    def test_callgraph_returns_reachability(self, client):
        """Callgraph should return reachable/unreachable info."""
        response = client.post('/api/callgraph', json={
            'file_path': 'Examples/Taxi.htn'
        })

        assert response.status_code == 200
        data = response.get_json()
        if 'reachable' in data:
            assert isinstance(data['reachable'], list)

    def test_callgraph_nonexistent_file(self, client):
        """Callgraph with nonexistent file should return 404."""
        response = client.post('/api/callgraph', json={
            'file_path': 'Examples/NonExistent.htn'
        })

        assert response.status_code == 404

    def test_callgraph_missing_params(self, client):
        """Callgraph without content or file_path should return 400."""
        response = client.post('/api/callgraph', json={})

        assert response.status_code == 400
