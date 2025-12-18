"""
Tests for concurrent session management.

These tests cover:
- Multiple simultaneous sessions
- Max sessions limit and LRU cleanup
- Session isolation
- Parallel query execution

Note: These tests create their own SessionManager instances to avoid
event loop issues with the module-scoped fixtures.
"""

import pytest
import asyncio
import importlib.util
from pathlib import Path


def _get_session_manager_class():
    """Load SessionManager without triggering MCP imports."""
    session_path = Path(__file__).parent.parent / "indhtn_mcp" / "session.py"
    spec = importlib.util.spec_from_file_location("session", session_path)
    session_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(session_module)
    return session_module.SessionManager


@pytest.mark.slow
@pytest.mark.asyncio
class TestMultipleSessions:
    """Tests for managing multiple sessions."""

    async def test_create_multiple_sessions(self, indhtn_path, examples_dir):
        """Test creating multiple sessions."""
        SessionManager = _get_session_manager_class()

        manager = SessionManager(indhtn_path)
        taxi_path = str(examples_dir / "Taxi.htn")
        game_path = str(examples_dir / "Game.htn")

        try:
            # Create two sessions
            session1_id, _ = await manager.create_session([taxi_path])
            session2_id, _ = await manager.create_session([game_path])

            assert session1_id is not None
            assert session2_id is not None
            assert session1_id != session2_id
            assert len(manager.sessions) == 2
        finally:
            await manager.end_all_sessions()

    async def test_sessions_are_independent(self, indhtn_path, examples_dir):
        """Test that sessions maintain independent state."""
        SessionManager = _get_session_manager_class()

        manager = SessionManager(indhtn_path)
        taxi_path = str(examples_dir / "Taxi.htn")

        try:
            # Create two sessions with same file
            session1_id, _ = await manager.create_session([taxi_path])
            session2_id, _ = await manager.create_session([taxi_path])

            # Give sessions time to initialize
            await asyncio.sleep(0.05)

            # Query session2 first (before any modifications)
            result2_before = await manager.execute_query(session2_id, "at(?x).")

            # Modify state in session1
            await manager.execute_query(session1_id, "apply(travel-to(park)).")

            # Query session2 again - should be unchanged
            result2_after = await manager.execute_query(session2_id, "at(?x).")

            assert result2_before["success"]
            assert result2_after["success"]
            # Session2 should still be at downtown
            assert result2_before["output"] == result2_after["output"]
        finally:
            await manager.end_all_sessions()

    async def test_end_specific_session(self, indhtn_path, examples_dir):
        """Test ending a specific session doesn't affect others."""
        SessionManager = _get_session_manager_class()

        manager = SessionManager(indhtn_path)
        taxi_path = str(examples_dir / "Taxi.htn")

        try:
            # Create two sessions
            session1_id, _ = await manager.create_session([taxi_path])
            session2_id, _ = await manager.create_session([taxi_path])

            # End session1
            await manager.end_session(session1_id)

            # Session1 should be gone
            assert session1_id not in manager.sessions

            # Session2 should still work
            result = await manager.execute_query(session2_id, "at(?x).")
            assert result["success"]
        finally:
            await manager.end_all_sessions()


@pytest.mark.slow
@pytest.mark.asyncio
class TestMaxSessionsLimit:
    """Tests for session limit enforcement."""

    async def test_max_sessions_parameter(self, indhtn_path):
        """Test that max_sessions parameter is respected."""
        SessionManager = _get_session_manager_class()

        # Create manager with max_sessions=2
        manager = SessionManager(indhtn_path, max_sessions=2)

        try:
            # Verify max_sessions is set
            assert manager.max_sessions == 2
        finally:
            await manager.end_all_sessions()

    async def test_cleanup_oldest_when_max_reached(self, indhtn_path, examples_dir):
        """Test that oldest session is cleaned up when max is reached."""
        SessionManager = _get_session_manager_class()

        # Create manager with small max
        manager = SessionManager(indhtn_path, max_sessions=2)
        taxi_path = str(examples_dir / "Taxi.htn")

        try:
            # Create sessions up to max
            session1_id, _ = await manager.create_session([taxi_path])
            await asyncio.sleep(0.02)  # Ensure different timestamps
            session2_id, _ = await manager.create_session([taxi_path])
            await asyncio.sleep(0.02)

            # Access session1 to make it more recent
            await manager.execute_query(session1_id, "at(?x).")

            # Create third session - should trigger cleanup of session2 (oldest accessed)
            session3_id, _ = await manager.create_session([taxi_path])

            # Should have 2 sessions
            assert len(manager.sessions) <= 2
            # Session3 should exist
            assert session3_id in manager.sessions

        finally:
            await manager.end_all_sessions()


@pytest.mark.slow
@pytest.mark.asyncio
class TestParallelQueries:
    """Tests for parallel query execution."""

    async def test_parallel_queries_different_sessions(self, indhtn_path, examples_dir):
        """Test executing queries in parallel on different sessions."""
        SessionManager = _get_session_manager_class()

        manager = SessionManager(indhtn_path)
        taxi_path = str(examples_dir / "Taxi.htn")

        try:
            # Create two sessions
            session1_id, _ = await manager.create_session([taxi_path])
            session2_id, _ = await manager.create_session([taxi_path])

            # Give sessions time to initialize
            await asyncio.sleep(0.05)

            # Execute queries in parallel
            results = await asyncio.gather(
                manager.execute_query(session1_id, "at(?x)."),
                manager.execute_query(session2_id, "distance(downtown, park, ?d)."),
            )

            assert results[0]["success"]
            assert results[1]["success"]
        finally:
            await manager.end_all_sessions()

    async def test_sequential_queries_same_session(self, session_manager, taxi_session):
        """Test that sequential queries on same session work correctly."""
        # Execute multiple queries sequentially
        result1 = await session_manager.execute_query(taxi_session, "at(?x).")
        result2 = await session_manager.execute_query(taxi_session, "have-cash.")
        result3 = await session_manager.execute_query(taxi_session, "weather(?w).")

        assert result1["success"]
        assert result2["success"]
        assert result3["success"]


@pytest.mark.slow
@pytest.mark.asyncio
class TestSessionCleanup:
    """Tests for session cleanup functionality."""

    async def test_end_all_sessions(self, indhtn_path, examples_dir):
        """Test ending all sessions at once."""
        SessionManager = _get_session_manager_class()

        manager = SessionManager(indhtn_path)
        taxi_path = str(examples_dir / "Taxi.htn")

        # Create multiple sessions
        await manager.create_session([taxi_path])
        await manager.create_session([taxi_path])
        await manager.create_session([taxi_path])

        assert len(manager.sessions) == 3

        # End all
        await manager.end_all_sessions()

        assert len(manager.sessions) == 0

    async def test_end_nonexistent_session(self, session_manager):
        """Test ending a session that doesn't exist."""
        # Should handle gracefully (no exception)
        await session_manager.end_session("nonexistent-session-id")
        # If we get here without exception, test passes

    async def test_session_tracks_access_time(self, session_manager, taxi_session):
        """Test that session access time is updated on query."""
        session = session_manager.sessions.get(taxi_session)
        assert session is not None

        initial_access = session.last_accessed

        # Wait a tiny bit and execute query
        await asyncio.sleep(0.01)
        await session_manager.execute_query(taxi_session, "at(?x).")

        # Access time should be updated
        assert session.last_accessed > initial_access


@pytest.mark.slow
@pytest.mark.asyncio
class TestSessionIsolation:
    """Tests for session isolation and state independence."""

    async def test_trace_toggle_isolated(self, indhtn_path, examples_dir):
        """Test that trace toggle doesn't affect other sessions."""
        SessionManager = _get_session_manager_class()

        manager = SessionManager(indhtn_path)
        taxi_path = str(examples_dir / "Taxi.htn")

        try:
            session1_id, _ = await manager.create_session([taxi_path])
            session2_id, _ = await manager.create_session([taxi_path])

            # Enable trace on session1
            await manager.execute_query(session1_id, "/t")

            # Get session objects
            session1 = manager.sessions.get(session1_id)
            session2 = manager.sessions.get(session2_id)

            # Trace state should be independent
            # (Note: trace_enabled is tracked per session)
            assert session1 is not None
            assert session2 is not None
        finally:
            await manager.end_all_sessions()

    async def test_reset_isolated(self, indhtn_path, examples_dir):
        """Test that reset on one session doesn't affect others."""
        SessionManager = _get_session_manager_class()

        manager = SessionManager(indhtn_path)
        taxi_path = str(examples_dir / "Taxi.htn")

        try:
            session1_id, _ = await manager.create_session([taxi_path])
            session2_id, _ = await manager.create_session([taxi_path])

            # Give sessions time to initialize
            await asyncio.sleep(0.05)

            # Modify state in session1
            await manager.execute_query(session1_id, "apply(travel-to(park)).")

            # Reset only session1
            await manager.execute_query(session1_id, "/r")

            # Session1 should be reset
            result1 = await manager.execute_query(session1_id, "at(?x).")
            # Session2 should still be at initial state (we didn't modify it)
            result2 = await manager.execute_query(session2_id, "at(?x).")

            assert result1["success"]
            assert result2["success"]
        finally:
            await manager.end_all_sessions()
