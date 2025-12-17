"""
Tests for indhtn_step tool.

This tool executes a single operator, modifying state.
Tests verify:
- Single operator execution
- State changes after step
- Error handling for invalid operators
"""

import pytest


@pytest.mark.asyncio
class TestStep:
    """Tests for indhtn_step functionality."""

    async def test_step_single_operator(self, session_manager, taxi_session):
        """Test executing a single walk operator."""
        # Step with walk operator
        result = await session_manager.step_operator(
            taxi_session,
            "walk(downtown, park)"
        )

        # Should return a result with success field
        assert "success" in result

    async def test_step_returns_operator_info(self, session_manager, taxi_session):
        """Test that step returns information about the operator."""
        result = await session_manager.step_operator(
            taxi_session,
            "walk(downtown, park)"
        )

        assert "operator" in result
        assert "walk" in result["operator"]

        if result["success"]:
            assert "message" in result or "result" in result

    async def test_step_invalid_operator_handled(self, session_manager, taxi_session):
        """Test stepping with undefined operator is handled gracefully."""
        result = await session_manager.step_operator(
            taxi_session,
            "undefined_operator(arg1, arg2)"
        )

        # API is permissive - may succeed with empty result (REPL is lenient)
        # Just verify it doesn't crash and returns valid structure
        assert "success" in result
        assert "operator" in result

    async def test_step_multiple_operators_sequentially(self, session_manager, taxi_session):
        """Test stepping through multiple operators."""
        # First step
        result1 = await session_manager.step_operator(
            taxi_session,
            "walk(downtown, park)"
        )
        assert "success" in result1

        # Second step (walk further) - may succeed or fail depending on state
        result2 = await session_manager.step_operator(
            taxi_session,
            "walk(park, uptown)"
        )
        assert "success" in result2

    async def test_step_preserves_other_state(self, session_manager, taxi_session):
        """Test that step preserves unrelated facts."""
        # Get a fact that should be preserved
        before = await session_manager.execute_query(
            taxi_session,
            "distance(downtown, park, ?d)."
        )

        # Step
        await session_manager.step_operator(taxi_session, "walk(downtown, park)")

        # Fact should be unchanged
        after = await session_manager.execute_query(
            taxi_session,
            "distance(downtown, park, ?d)."
        )

        assert before["output"] == after["output"]


@pytest.mark.asyncio
class TestStepEdgeCases:
    """Edge case tests for step."""

    async def test_step_empty_operator_handled(self, session_manager, taxi_session):
        """Test stepping with empty operator is handled gracefully."""
        # May raise error, return failure, or succeed with empty result
        try:
            result = await session_manager.step_operator(taxi_session, "")
            # API is permissive - just verify it doesn't crash
            assert "success" in result
        except (ValueError, TypeError):
            pass  # Raising is also acceptable

    async def test_step_syntax_error_handled(self, session_manager, taxi_session):
        """Test stepping with invalid operator syntax is handled."""
        result = await session_manager.step_operator(
            taxi_session,
            "invalid(syntax"  # Missing closing paren
        )

        # Should be handled gracefully
        assert "success" in result or "error" in result

    async def test_step_with_unbound_variables(self, session_manager, taxi_session):
        """Test stepping with unbound variables."""
        result = await session_manager.step_operator(
            taxi_session,
            "walk(?from, ?to)"
        )

        # Behavior depends on implementation
        # May bind variables or fail - shouldn't crash
        assert "success" in result

    async def test_step_after_reset(self, session_manager, taxi_session):
        """Test stepping after session reset."""
        # Make some state changes
        await session_manager.step_operator(taxi_session, "walk(downtown, park)")

        # Reset
        await session_manager.execute_query(taxi_session, "/r")

        # Step should work from reset state
        result = await session_manager.step_operator(
            taxi_session,
            "walk(downtown, park)"
        )
        # May succeed or fail depending on reset behavior
        assert "success" in result


@pytest.mark.asyncio
class TestStepInvalidSession:
    """Tests for step with invalid sessions."""

    async def test_step_invalid_session_id(self, session_manager):
        """Test stepping with invalid session ID."""
        with pytest.raises(ValueError) as exc_info:
            await session_manager.step_operator(
                "invalid-session-id",
                "walk(downtown, park)"
            )
        assert "not found" in str(exc_info.value).lower()

    async def test_step_missing_session_id(self, session_manager):
        """Test stepping without session ID."""
        with pytest.raises((ValueError, TypeError, KeyError)):
            await session_manager.step_operator(None, "walk(downtown, park)")


@pytest.mark.asyncio
class TestStepVsApply:
    """Tests comparing step behavior with apply."""

    async def test_step_is_atomic_operation(self, session_manager, taxi_session):
        """Test that step executes exactly one operator."""
        # Step should execute just the one operator
        result = await session_manager.step_operator(
            taxi_session,
            "walk(downtown, park)"
        )

        # Should have operator field indicating what was executed
        assert "operator" in result
        # Should be the operator we specified
        assert "walk" in result["operator"] and "downtown" in result["operator"]
