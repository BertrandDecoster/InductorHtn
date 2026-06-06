"""Tests for nav_obstacle challenge component."""

import os
import sys

# Add parent directories to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../src/Python")))

from htn_test_framework import HtnTestSuite


class NavObstacleTest(HtnTestSuite):
    """Test suite for nav_obstacle challenge."""

    def setup(self):
        """Load the nav_obstacle component (resets planner for clean state)."""
        self.load_component("challenges/nav_obstacle")

    # =========================================================================
    # Example Tests (from design.md)
    # =========================================================================

    def test_example_1_direct_unblocked_path(self):
        """Example 1: Direct unblocked path

        Given: at(agent, locA), connected(locA, locB)
        When: navigateTo(agent, locB)
        Then: Plan contains opMoveTo, agent ends at locB
        """
        self.set_state([
            "at(agent, locA)",
            "connected(locA, locB)"
        ])

        self.assert_plan("navigateTo(agent, locB).",
            contains=["opMoveTo(agent, locA, locB)"])

        self.assert_state_after("navigateTo(agent, locB).",
            has=["at(agent,locB)"],
            not_has=["at(agent,locA)"])

    def test_example_2_direct_blocked_detour_available(self):
        """Example 2: Direct path blocked, detour through safe intermediate

        Given: locB is blocked, but locA->locC->locB is safe
        When: navigateTo(agent, locB)
        Then: Plan routes through locC
        """
        self.set_state([
            "at(agent, locA)",
            "connected(locA, locB)",
            "blocked(locB)",
            "connected(locA, locC)",
            "connected(locC, locB)"
        ])

        # locB is the destination — it is NOT blocked once we route correctly.
        # But since blocked(locB) is set, the direct path is refused.
        # Let's use a scenario where locB itself is NOT blocked but locA->locB direct is
        # blocked because the intermediate is. Use locD as safe dest instead.
        # Reset to cleaner scenario:
        self.set_state([])  # clear previous facts by reloading

        # Reload component and set fresh state
        self.load_component("challenges/nav_obstacle")
        self.set_state([
            "at(agent, locA)",
            "connected(locA, locB)",
            "blocked(locB)",
            "connected(locA, locC)",
            "connected(locC, locD)",
            "connected(locB, locD)"
        ])

        # Route: locA -> locC -> locD (locB is blocked so can't go direct locA->locB->locD)
        self.assert_plan("navigateTo(agent, locD).",
            contains=["opMoveTo(agent, locA, locC)", "opMoveTo(agent, locC, locD)"])

    def test_example_3_all_paths_blocked_no_plan(self):
        """Example 3: All paths blocked — no valid plan

        Given: only path to destination is blocked
        When: navigateTo(agent, locB)
        Then: Planning fails
        """
        self.set_state([
            "at(agent, locA)",
            "connected(locA, locB)",
            "blocked(locB)"
        ])

        self.assert_no_plan("navigateTo(agent, locB).")

    def test_example_4_already_at_destination(self):
        """Example 4: Already at destination — no-op

        Given: agent already at locA
        When: navigateTo(agent, locA)
        Then: Plan is empty
        """
        self.set_state([
            "at(agent, locA)"
        ])

        self.assert_plan("navigateTo(agent, locA).",
            not_contains=["opMoveTo"])

    # =========================================================================
    # Property Tests
    # =========================================================================

    def test_property_p1_destination_reached(self):
        """P1: After successful plan, agent is at destination."""
        self.set_state([
            "at(agent, locA)",
            "connected(locA, locB)"
        ])

        self.run_goal("navigateTo(agent, locB)")
        state = self.get_state()

        at_dest = any("at(agent,locB)" in f for f in state)
        assert at_dest, "P1 violated: agent not at destination after navigateTo"

    def test_property_p2_no_blocked_visits(self):
        """P2: Plan never routes agent into a blocked location."""
        self.set_state([
            "at(agent, locA)",
            "connected(locA, locB)",
            "blocked(locB)",
            "connected(locA, locC)",
            "connected(locC, locD)"
        ])

        # navigateTo(agent, locD) should go A->C->D, never through blocked locB
        self.assert_plan("navigateTo(agent, locD).",
            not_contains=["opMoveTo(agent, locA, locB)"])

    def test_property_p3_single_location(self):
        """P3: Agent is at exactly one location after moving."""
        self.set_state([
            "at(agent, locA)",
            "connected(locA, locB)"
        ])

        self.run_goal("navigateTo(agent, locB)")
        state = self.get_state()

        agent_locs = [f for f in state if f.startswith("at(agent,")]
        assert len(agent_locs) == 1, \
            f"P3 violated: agent at {len(agent_locs)} locations: {agent_locs}"

    def test_property_p4_idempotent_at_destination(self):
        """P4: navigateTo when already at destination produces no operators."""
        self.set_state([
            "at(agent, locA)"
        ])

        initial_state = set(self.get_state())
        self.run_goal("navigateTo(agent, locA)")
        final_state = set(self.get_state())

        assert initial_state == final_state, \
            f"P4 violated: state changed. Added: {final_state - initial_state}, Removed: {initial_state - final_state}"


def run_tests():
    """Run all tests in this file."""
    suite = NavObstacleTest()
    suite.setup()

    for method_name in dir(suite):
        if method_name.startswith("test_"):
            suite.setup()
            method = getattr(suite, method_name)
            try:
                method()
            except AssertionError as e:
                suite._record(False, method_name, str(e))
            except Exception as e:
                suite._record(False, method_name, f"Error: {e}")

    print(suite.summary())
    return suite.all_passed()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
