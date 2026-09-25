"""Tests for pushable challenge component."""

import os
import sys

# Add parent directories to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../src/Python")))

from htn_test_framework import HtnTestSuite


class PushableTest(HtnTestSuite):
    """Test suite for pushable challenge."""

    def setup(self):
        """Load pushable and its dependency nav_obstacle."""
        self.load_component("challenges/nav_obstacle", reset_first=True)
        self.load_component("challenges/pushable", reset_first=False)

    # =========================================================================
    # Example Tests (from design.md)
    # =========================================================================

    def test_example_1_single_push_to_target(self):
        """Example 1: Single push from agent-adjacent position

        Given: agent at startLoc, box at midLoc, target at goalLoc
        When: pushToTarget(box1)
        Then: Plan contains opPush, box ends at goalLoc
        """
        self.set_state([
            "at(agent, startLoc)",
            "objectAt(box1, midLoc)",
            "targetFor(box1, goalLoc)",
            "connected(startLoc, midLoc)",
            "connected(midLoc, goalLoc)"
        ])

        self.assert_plan("pushToTarget(box1).",
            contains=["opPush(box1, midLoc, goalLoc)"])

        self.assert_state_after("pushToTarget(box1).",
            has=["objectAt(box1,goalLoc)"],
            not_has=["objectAt(box1,midLoc)"])

    def test_example_2_no_push_position_no_plan(self):
        """Example 2: No valid push-from position -- planning fails

        Given: No location connects to box position from the push side
        When: pushToTarget(box1)
        Then: Planning fails
        """
        self.set_state([
            "at(agent, startLoc)",
            "objectAt(box1, midLoc)",
            "targetFor(box1, goalLoc)",
            "connected(midLoc, goalLoc)"
            # No connection into midLoc -- cannot get behind box
        ])

        self.assert_no_plan("pushToTarget(box1).")

    def test_example_3_two_push_sequence(self):
        """Example 3: Two-push sequence through intermediate

        Given: box must be pushed through an intermediate location
        When: pushToTarget(box1)
        Then: Plan contains two opPush operations
        """
        self.set_state([
            "at(agent, a)",
            "objectAt(box1, b)",
            "targetFor(box1, d)",
            "connected(a, b)",
            "connected(b, c)",
            "connected(a, c)",
            "connected(c, d)"
        ])

        self.assert_plan_complexity("pushToTarget(box1).",
            min_operators=2)

    # =========================================================================
    # Property Tests
    # =========================================================================

    def test_property_p1_object_at_target(self):
        """P1: After successful plan, object is at its target location."""
        self.set_state([
            "at(agent, startLoc)",
            "objectAt(box1, midLoc)",
            "targetFor(box1, goalLoc)",
            "connected(startLoc, midLoc)",
            "connected(midLoc, goalLoc)"
        ])

        self.run_goal("pushToTarget(box1)")
        state = self.get_state()

        at_target = any("objectAt(box1,goalLoc)" in f for f in state)
        assert at_target, "P1 violated: object not at target after pushToTarget"

    def test_property_p2_object_not_at_origin(self):
        """P2: After plan, object is no longer at original location."""
        self.set_state([
            "at(agent, startLoc)",
            "objectAt(box1, midLoc)",
            "targetFor(box1, goalLoc)",
            "connected(startLoc, midLoc)",
            "connected(midLoc, goalLoc)"
        ])

        self.run_goal("pushToTarget(box1)")
        state = self.get_state()

        still_at_origin = any("objectAt(box1,midLoc)" in f for f in state)
        assert not still_at_origin, "P2 violated: object still at original location"

    def test_property_p3_plan_has_push_operator(self):
        """P3: A successful plan always contains an opPush operator."""
        self.set_state([
            "at(agent, startLoc)",
            "objectAt(box1, midLoc)",
            "targetFor(box1, goalLoc)",
            "connected(startLoc, midLoc)",
            "connected(midLoc, goalLoc)"
        ])

        self.assert_plan("pushToTarget(box1).",
            contains=["opPush"])


def run_tests():
    """Run all tests in this file."""
    suite = PushableTest()
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
