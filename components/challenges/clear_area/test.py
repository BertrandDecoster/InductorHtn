"""Tests for clear_area challenge component."""

import os
import sys

# Add parent directories to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../src/Python")))

from htn_test_framework import HtnTestSuite


class ClearAreaTest(HtnTestSuite):
    """Test suite for clear_area challenge."""

    def setup(self):
        """Load clear_area and its dependency nav_obstacle."""
        self.load_component("challenges/nav_obstacle", reset_first=True)
        self.load_component("challenges/clear_area", reset_first=False)

    # =========================================================================
    # Example Tests (from design.md)
    # =========================================================================

    def test_example_1_single_blocker(self):
        """Example 1: Clear a zone with one blocker

        Given: one blocker in zone1
        When: clearZone(zone1)
        Then: Plan eliminates enemy1, cleared fact added
        """
        self.set_state([
            "at(agent, start)",
            "blocker(enemy1, zone1)",
            "zoneEntry(zone1, zoneEntrance)",
            "connected(start, zoneEntrance)"
        ])

        self.assert_plan("clearZone(zone1).",
            contains=["opEliminate(enemy1, zone1)"])

        self.assert_state_after("clearZone(zone1).",
            has=["cleared(enemy1)"],
            not_has=["blocker(enemy1,zone1)"])

    def test_example_2_multiple_blockers(self):
        """Example 2: Clear a zone with multiple blockers

        Given: three blockers in zone1
        When: clearZone(zone1)
        Then: All three enemies are cleared
        """
        self.set_state([
            "at(agent, start)",
            "blocker(enemy1, zone1)",
            "blocker(enemy2, zone1)",
            "blocker(enemy3, zone1)",
            "zoneEntry(zone1, zoneEntrance)",
            "connected(start, zoneEntrance)"
        ])

        self.assert_plan("clearZone(zone1).",
            contains=["opEliminate(enemy1, zone1)",
                      "opEliminate(enemy2, zone1)",
                      "opEliminate(enemy3, zone1)"])

        self.assert_state_after("clearZone(zone1).",
            has=["cleared(enemy1)", "cleared(enemy2)", "cleared(enemy3)"])

    def test_example_3_empty_zone_succeeds(self):
        """Example 3: Zone with no blockers -- plan succeeds with no elimination ops

        Given: no blocker facts for zone1
        When: clearZone(zone1)
        Then: Planning succeeds (vacuously), no opEliminate in plan
        """
        self.set_state([
            "at(agent, start)",
            "zoneEntry(zone1, zoneEntrance)"
        ])

        self.assert_plan("clearZone(zone1).",
            not_contains=["opEliminate"])

    # =========================================================================
    # Property Tests
    # =========================================================================

    def test_property_p1_all_blockers_cleared(self):
        """P1: After plan, no blocker facts remain for the cleared zone."""
        self.set_state([
            "at(agent, start)",
            "blocker(enemy1, zone1)",
            "blocker(enemy2, zone1)",
            "zoneEntry(zone1, zoneEntrance)",
            "connected(start, zoneEntrance)"
        ])

        self.run_goal("clearZone(zone1)")
        state = self.get_state()

        remaining_blockers = [f for f in state if f.startswith("blocker(") and "zone1" in f]
        assert len(remaining_blockers) == 0, \
            f"P1 violated: blockers still present: {remaining_blockers}"

    def test_property_p2_cleared_markers_added(self):
        """P2: Every blocker gets a cleared(entity) fact after elimination."""
        self.set_state([
            "at(agent, start)",
            "blocker(enemy1, zone1)",
            "blocker(enemy2, zone1)",
            "zoneEntry(zone1, zoneEntrance)",
            "connected(start, zoneEntrance)"
        ])

        self.run_goal("clearZone(zone1)")
        state = self.get_state()

        cleared_e1 = any("cleared(enemy1)" in f for f in state)
        cleared_e2 = any("cleared(enemy2)" in f for f in state)
        assert cleared_e1, "P2 violated: cleared(enemy1) not added"
        assert cleared_e2, "P2 violated: cleared(enemy2) not added"

    def test_property_p3_plan_scales_with_blockers(self):
        """P3: Number of opEliminate calls equals number of blockers."""
        self.set_state([
            "at(agent, start)",
            "blocker(e1, zone1)",
            "blocker(e2, zone1)",
            "blocker(e3, zone1)",
            "zoneEntry(zone1, entry)",
            "connected(start, entry)"
        ])

        # Three blockers means at least 3 operators (the eliminates)
        self.assert_plan_complexity("clearZone(zone1).", min_operators=3)


def run_tests():
    """Run all tests in this file."""
    suite = ClearAreaTest()
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
