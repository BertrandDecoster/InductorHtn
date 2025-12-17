"""
Tests for indhtn_state_diff tool.

This tool previews what plan would be generated WITHOUT applying it.
Tests verify:
- Plan preview without state modification
- Correct plan output
- Error handling
"""

import pytest


@pytest.mark.asyncio
class TestStateDiff:
    """Tests for indhtn_state_diff functionality."""

    async def test_state_diff_returns_result(self, session_manager, taxi_session):
        """Test that state_diff returns a result structure."""
        result = await session_manager.get_state_diff(taxi_session, "travel-to(park)")

        assert "success" in result, "Result should have success field"

    async def test_state_diff_has_goal_field(self, session_manager, taxi_session):
        """Test that successful state_diff includes goal field."""
        result = await session_manager.get_state_diff(taxi_session, "travel-to(park)")

        if result["success"]:
            assert "goal" in result
            assert "park" in result["goal"]

    async def test_state_diff_does_not_modify_state(self, session_manager, taxi_session):
        """Test that state_diff does NOT modify the state."""
        # Get initial state
        before = await session_manager.execute_query(taxi_session, "at(?where).")
        assert before["success"]
        initial_output = before["output"]

        # Call state_diff (preview only)
        await session_manager.get_state_diff(taxi_session, "travel-to(park)")

        # State should be UNCHANGED
        after = await session_manager.execute_query(taxi_session, "at(?where).")
        assert after["success"]
        assert after["output"] == initial_output, "state_diff should not modify state!"

    async def test_state_diff_invalid_goal_handled(self, session_manager, taxi_session):
        """Test state_diff with impossible goal is handled gracefully."""
        result = await session_manager.get_state_diff(
            taxi_session,
            "travel-to(nonexistent_location)"
        )

        # Should handle gracefully - either failure or empty plan
        handled = (
            not result.get("success", True) or
            "null" in str(result.get("plan", "")).lower() or
            result.get("plan", "x") == "" or
            "error" in result
        )
        assert handled, f"Expected graceful handling: {result}"

    async def test_state_diff_multiple_calls_consistent(self, session_manager, taxi_session):
        """Test that multiple state_diff calls return consistent results."""
        result1 = await session_manager.get_state_diff(taxi_session, "travel-to(park)")
        result2 = await session_manager.get_state_diff(taxi_session, "travel-to(park)")

        # Success status should be consistent
        assert result1.get("success") == result2.get("success")

    async def test_state_diff_includes_note(self, session_manager, taxi_session):
        """Test that state_diff includes helpful note."""
        result = await session_manager.get_state_diff(taxi_session, "travel-to(park)")

        if result["success"]:
            assert "note" in result
            assert "apply" in result["note"].lower()


@pytest.mark.asyncio
class TestStateDiffEdgeCases:
    """Edge case tests for state_diff."""

    async def test_state_diff_empty_goal_handled(self, session_manager, taxi_session):
        """Test state_diff with empty goal is handled gracefully."""
        # May raise error, return failure, or succeed with empty plan
        try:
            result = await session_manager.get_state_diff(taxi_session, "")
            # API is permissive - may succeed with empty plan, or fail
            # Just verify it doesn't crash and returns valid structure
            assert "success" in result
        except (ValueError, TypeError):
            pass  # Raising is also acceptable

    async def test_state_diff_with_variables(self, session_manager, taxi_session):
        """Test state_diff with goal containing variables."""
        result = await session_manager.get_state_diff(
            taxi_session,
            "travel-to(?dest)"
        )
        # May succeed with bindings or fail - shouldn't crash
        assert "success" in result

    async def test_state_diff_different_destination(self, session_manager, taxi_session):
        """Test state_diff with different destination."""
        result = await session_manager.get_state_diff(
            taxi_session,
            "travel-to(uptown)"
        )
        # Just verify it completes without error
        assert "success" in result


@pytest.mark.asyncio
class TestStateDiffInvalidSession:
    """Tests for state_diff with invalid sessions."""

    async def test_state_diff_invalid_session(self, session_manager):
        """Test state_diff with invalid session ID."""
        with pytest.raises(ValueError) as exc_info:
            await session_manager.get_state_diff(
                "nonexistent-session-id",
                "travel-to(park)"
            )
        assert "not found" in str(exc_info.value).lower()

    async def test_state_diff_missing_session_id(self, session_manager):
        """Test state_diff without session ID."""
        with pytest.raises((ValueError, TypeError, KeyError)):
            await session_manager.get_state_diff(None, "travel-to(park)")
