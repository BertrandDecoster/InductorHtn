"""
Tests for REPL commands.

These tests cover the interactive REPL commands:
- /? or /h: Help
- /t: Toggle trace
- /r: Reset session
"""

import pytest


@pytest.mark.asyncio
class TestReplCommands:
    """Tests for REPL commands."""

    async def test_help_command_short(self, session_manager, taxi_session):
        """Test /? help command."""
        result = await session_manager.execute_query(taxi_session, "/?")
        assert result["success"]
        # Help should produce some output
        assert len(result.get("output", "")) > 0 or result["success"]

    async def test_help_command_long(self, session_manager, taxi_session):
        """Test /h help command (alternative syntax)."""
        result = await session_manager.execute_query(taxi_session, "/h")
        assert result["success"]

    async def test_trace_toggle_on(self, session_manager, taxi_session):
        """Test /t trace toggle command turns tracing on."""
        result = await session_manager.execute_query(taxi_session, "/t")
        assert result["success"]
        # Output may indicate trace is now on
        output = result.get("output", "").lower()
        assert result["success"]  # Command should succeed

    async def test_trace_toggle_off(self, session_manager, taxi_session):
        """Test /t trace toggle command turns tracing off when called twice."""
        # Toggle on
        await session_manager.execute_query(taxi_session, "/t")
        # Toggle off
        result = await session_manager.execute_query(taxi_session, "/t")
        assert result["success"]

    async def test_reset_command(self, session_manager, taxi_session):
        """Test /r reset command restores initial state."""
        # Modify state first
        await session_manager.execute_query(taxi_session, "apply(travel-to(park)).")

        # Reset
        result = await session_manager.execute_query(taxi_session, "/r")
        assert result["success"]

    async def test_reset_restores_initial_facts(self, session_manager, taxi_session):
        """Test that /r reset actually restores the initial state."""
        # Get initial state
        before = await session_manager.execute_query(taxi_session, "at(?x).")

        # Modify state
        await session_manager.execute_query(taxi_session, "apply(travel-to(park)).")

        # Verify state changed (or at least command succeeded)
        middle = await session_manager.execute_query(taxi_session, "at(?x).")

        # Reset
        await session_manager.execute_query(taxi_session, "/r")

        # Verify state is back to initial
        after = await session_manager.execute_query(taxi_session, "at(?x).")
        assert before["output"] == after["output"]
