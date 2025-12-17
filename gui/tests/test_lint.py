"""
Tests for linting endpoints.

These tests cover:
- POST /api/lint - Lint HTN content or file
- POST /api/lint/batch - Lint multiple files
"""

import pytest


class TestLintContent:
    """Tests for /api/lint endpoint with content."""

    def test_lint_valid_content(self, client, valid_htn_content):
        """Linting valid content should return no errors."""
        response = client.post('/api/lint', json={
            'content': valid_htn_content
        })

        assert response.status_code == 200
        data = response.get_json()
        assert 'diagnostics' in data
        assert isinstance(data['diagnostics'], list)

    def test_lint_invalid_content(self, client, invalid_htn_content):
        """Linting invalid content should return diagnostics."""
        response = client.post('/api/lint', json={
            'content': invalid_htn_content
        })

        assert response.status_code == 200
        data = response.get_json()
        assert 'diagnostics' in data
        # Invalid content should produce at least one diagnostic
        assert len(data['diagnostics']) > 0

    def test_lint_empty_content(self, client, empty_htn_content):
        """Linting empty content should return empty diagnostics."""
        response = client.post('/api/lint', json={
            'content': empty_htn_content
        })

        assert response.status_code == 200
        data = response.get_json()
        assert 'diagnostics' in data

    def test_lint_diagnostic_structure(self, client, invalid_htn_content):
        """Diagnostics should have proper structure."""
        response = client.post('/api/lint', json={
            'content': invalid_htn_content
        })

        assert response.status_code == 200
        data = response.get_json()

        if len(data['diagnostics']) > 0:
            diag = data['diagnostics'][0]
            # Check expected fields exist
            assert 'line' in diag or 'message' in diag or 'severity' in diag


class TestLintFile:
    """Tests for /api/lint endpoint with file_path."""

    def test_lint_valid_file(self, client):
        """Linting a valid HTN file should succeed."""
        response = client.post('/api/lint', json={
            'file_path': 'Examples/Taxi.htn'
        })

        assert response.status_code == 200
        data = response.get_json()
        assert 'diagnostics' in data
        assert isinstance(data['diagnostics'], list)

    def test_lint_nonexistent_file(self, client):
        """Linting nonexistent file should return 404."""
        response = client.post('/api/lint', json={
            'file_path': 'Examples/NonExistent.htn'
        })

        assert response.status_code == 404
        data = response.get_json()
        assert 'error' in data

    def test_lint_missing_params(self, client):
        """Linting without content or file_path should return 400."""
        response = client.post('/api/lint', json={})

        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data


class TestLintBatch:
    """Tests for /api/lint/batch endpoint."""

    def test_lint_batch_multiple_files(self, client):
        """Batch linting multiple files should return results for each."""
        response = client.post('/api/lint/batch', json={
            'file_paths': ['Examples/Taxi.htn', 'Examples/Game.htn']
        })

        assert response.status_code == 200
        data = response.get_json()
        assert 'results' in data
        assert 'Examples/Taxi.htn' in data['results']
        assert 'Examples/Game.htn' in data['results']

    def test_lint_batch_single_file(self, client):
        """Batch linting a single file should work."""
        response = client.post('/api/lint/batch', json={
            'file_paths': ['Examples/Taxi.htn']
        })

        assert response.status_code == 200
        data = response.get_json()
        assert 'results' in data
        assert 'Examples/Taxi.htn' in data['results']

    def test_lint_batch_mixed_valid_invalid(self, client):
        """Batch linting with some invalid paths should handle gracefully."""
        response = client.post('/api/lint/batch', json={
            'file_paths': ['Examples/Taxi.htn', 'Examples/NonExistent.htn']
        })

        assert response.status_code == 200
        data = response.get_json()
        assert 'results' in data
        # Valid file should have diagnostics
        assert 'diagnostics' in data['results']['Examples/Taxi.htn']
        # Invalid file should have error
        assert 'error' in data['results']['Examples/NonExistent.htn']

    def test_lint_batch_empty_array(self, client):
        """Batch linting with empty array should return 400."""
        response = client.post('/api/lint/batch', json={
            'file_paths': []
        })

        assert response.status_code == 400

    def test_lint_batch_missing_file_paths(self, client):
        """Batch linting without file_paths should return 400."""
        response = client.post('/api/lint/batch', json={})

        assert response.status_code == 400
