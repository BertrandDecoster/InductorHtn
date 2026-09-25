"""Tests for escort challenge component."""

import os
import sys

# Add parent directories to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../src/Python")))

from htn_test_framework import HtnTestSuite


class EscortTest(HtnTestSuite):
    """Test suite for escort challenge."""

    def setup(self):
        """Load escort and its dependency nav_obstacle."""
        self.load_component("challenges/nav_obstacle", reset_first=True)
        self.load_component("challenges/escort", reset_first=False)

    # =========================================================================
    # Example Tests (from design.md)
    # =========================================================================

    def test_example_1_direct_escort_to_safe_destination(self):
        """Example 1: Direct escort to safe destination

        Given: agent and NPC at different locations, destination is safe
        When: escortTo(villager, safeExit)
        Then: NPC ends at safeExit
        """
        self.set_state([
            "at(agent, agentStart)",
            "npcAt(villager, npcStart)",
            "safeFor(villager, safeExit)",
            "connected(agentStart, npcStart)",
            "connected(npcStart, safeExit)"
        ])

        self.assert_plan("escortTo(villager, safeExit).",
            contains=["opEscort(villager, npcStart, safeExit)"])

        self.assert_state_after("escortTo(villager, safeExit).",
            has=["npcAt(villager,safeExit)"],
            not_has=["npcAt(villager,npcStart)"])

    def test_example_2_unsafe_destination_no_plan(self):
        """Example 2: Unsafe destination -- no plan

        Given: Destination has no safeFor fact for the NPC
        When: escortTo(villager, dangerZone)
        Then: Planning fails
        """
        self.set_state([
            "at(agent, agentStart)",
            "npcAt(villager, npcStart)",
            "connected(agentStart, npcStart)",
            "connected(npcStart, dangerZone)"
            # No safeFor(villager, dangerZone) -- cannot escort here
        ])

        self.assert_no_plan("escortTo(villager, dangerZone).")

    def test_example_3_already_at_destination(self):
        """Example 3: NPC already at destination -- no-op

        Given: NPC already at safeExit
        When: escortTo(villager, safeExit)
        Then: Plan is empty
        """
        self.set_state([
            "at(agent, agentStart)",
            "npcAt(villager, safeExit)"
        ])

        self.assert_plan("escortTo(villager, safeExit).",
            not_contains=["opEscort"])

    # =========================================================================
    # Property Tests
    # =========================================================================

    def test_property_p1_npc_at_destination(self):
        """P1: After successful plan, NPC is at destination."""
        self.set_state([
            "at(agent, agentStart)",
            "npcAt(villager, npcStart)",
            "safeFor(villager, safeExit)",
            "connected(agentStart, npcStart)",
            "connected(npcStart, safeExit)"
        ])

        self.run_goal("escortTo(villager, safeExit)")
        state = self.get_state()

        npc_at_dest = any("npcAt(villager,safeExit)" in f for f in state)
        assert npc_at_dest, "P1 violated: NPC not at destination after escortTo"

    def test_property_p2_two_hop_uses_safe_intermediate(self):
        """P2: Two-hop escort routes NPC through a safe intermediate only."""
        self.set_state([
            "at(agent, a)",
            "npcAt(villager, b)",
            "connected(b, safeMid)",
            "safeFor(villager, safeMid)",
            "connected(safeMid, dest)",
            "safeFor(villager, dest)",
            "connected(a, b)"
        ])

        # Plan should route through safeMid, not through any unsafe location
        self.assert_plan("escortTo(villager, dest).",
            contains=["opEscort(villager, b, safeMid)", "opEscort(villager, safeMid, dest)"])

    def test_property_p3_idempotent_at_destination(self):
        """P3: No operators produced when NPC already at destination."""
        self.set_state([
            "npcAt(villager, safeExit)"
        ])

        initial_state = set(self.get_state())
        self.run_goal("escortTo(villager, safeExit)")
        final_state = set(self.get_state())

        assert initial_state == final_state, \
            f"P3 violated: state changed. Added: {final_state - initial_state}, Removed: {initial_state - final_state}"


def run_tests():
    """Run all tests in this file."""
    suite = EscortTest()
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
