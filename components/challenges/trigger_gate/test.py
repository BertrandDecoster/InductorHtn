"""Tests for trigger_gate challenge component."""

import os
import sys

# Add parent directories to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../src/Python")))

from htn_test_framework import HtnTestSuite


class TriggerGateTest(HtnTestSuite):
    """Test suite for trigger_gate challenge."""

    def setup(self):
        """Load trigger_gate and its dependency nav_obstacle."""
        self.load_component("challenges/nav_obstacle", reset_first=True)
        self.load_component("challenges/trigger_gate", reset_first=False)

    # =========================================================================
    # Example Tests (from design.md)
    # =========================================================================

    def test_example_1_standard_gate_and_switch(self):
        """Example 1: Standard gate-and-switch puzzle

        Given: Gate blocks exitRoom, switch in sideRoom controls the gate
        When: reachThroughGate(agent, exitRoom)
        Then: Agent activates switch, gate opens, agent reaches exitRoom
        """
        self.set_state([
            "at(agent, entrance)",
            "gateBlocking(gate1, exitRoom)",
            "switchControls(switch1, gate1)",
            "switchAt(switch1, sideRoom)",
            "switchIdle(switch1)",
            "connected(entrance, sideRoom)",
            "connected(sideRoom, exitRoom)"
        ])

        self.assert_plan("reachThroughGate(agent, exitRoom).",
            contains=["opActivateSwitch(switch1)", "opOpenGate(gate1, exitRoom)"])

        self.assert_state_after("reachThroughGate(agent, exitRoom).",
            has=["switchTriggered(switch1)", "gateOpen(gate1,exitRoom)", "at(agent,exitRoom)"],
            not_has=["gateBlocking(gate1,exitRoom)", "switchIdle(switch1)"])

    def test_example_2_gate_already_open(self):
        """Example 2: Gate already open — direct navigation

        Given: Gate is already open
        When: reachThroughGate(agent, exitRoom)
        Then: No switch activation, direct nav
        """
        self.set_state([
            "at(agent, entrance)",
            "gateOpen(gate1, exitRoom)",
            "connected(entrance, exitRoom)"
        ])

        self.assert_plan("reachThroughGate(agent, exitRoom).",
            not_contains=["opActivateSwitch"])

        self.assert_state_after("reachThroughGate(agent, exitRoom).",
            has=["at(agent,exitRoom)"])

    def test_example_3_no_switch_no_plan(self):
        """Example 3: No switch available for blocking gate — no plan

        Given: Gate blocks destination, no switch fact
        When: reachThroughGate(agent, exitRoom)
        Then: Planning fails
        """
        self.set_state([
            "at(agent, entrance)",
            "gateBlocking(gate1, exitRoom)",
            "connected(entrance, exitRoom)"
            # No switchControls fact — cannot open gate
        ])

        self.assert_no_plan("reachThroughGate(agent, exitRoom).")

    # =========================================================================
    # Property Tests
    # =========================================================================

    def test_property_p1_agent_reaches_destination(self):
        """P1: After successful plan, agent is at destination."""
        self.set_state([
            "at(agent, entrance)",
            "gateBlocking(gate1, exitRoom)",
            "switchControls(switch1, gate1)",
            "switchAt(switch1, sideRoom)",
            "switchIdle(switch1)",
            "connected(entrance, sideRoom)",
            "connected(sideRoom, exitRoom)"
        ])

        self.run_goal("reachThroughGate(agent, exitRoom)")
        state = self.get_state()

        at_dest = any("at(agent,exitRoom)" in f for f in state)
        assert at_dest, "P1 violated: agent not at exitRoom after reachThroughGate"

    def test_property_p2_gate_opened(self):
        """P2: After plan, gateOpen fact exists for the activated gate."""
        self.set_state([
            "at(agent, entrance)",
            "gateBlocking(gate1, exitRoom)",
            "switchControls(switch1, gate1)",
            "switchAt(switch1, sideRoom)",
            "switchIdle(switch1)",
            "connected(entrance, sideRoom)",
            "connected(sideRoom, exitRoom)"
        ])

        self.run_goal("reachThroughGate(agent, exitRoom)")
        state = self.get_state()

        gate_open = any("gateOpen(gate1,exitRoom)" in f for f in state)
        assert gate_open, "P2 violated: gateOpen fact not present after plan"

    def test_property_p3_switch_consumed(self):
        """P3: switchIdle removed, switchTriggered added after activation."""
        self.set_state([
            "at(agent, entrance)",
            "gateBlocking(gate1, exitRoom)",
            "switchControls(switch1, gate1)",
            "switchAt(switch1, sideRoom)",
            "switchIdle(switch1)",
            "connected(entrance, sideRoom)",
            "connected(sideRoom, exitRoom)"
        ])

        self.run_goal("reachThroughGate(agent, exitRoom)")
        state = self.get_state()

        still_idle = any("switchIdle(switch1)" in f for f in state)
        now_triggered = any("switchTriggered(switch1)" in f for f in state)
        assert not still_idle, "P3 violated: switchIdle still present"
        assert now_triggered, "P3 violated: switchTriggered not added"

    def test_property_p4_already_open_no_activation(self):
        """P4: If gate already open, no opActivateSwitch in plan."""
        self.set_state([
            "at(agent, entrance)",
            "gateOpen(gate1, exitRoom)",
            "connected(entrance, exitRoom)"
        ])

        self.assert_plan("reachThroughGate(agent, exitRoom).",
            not_contains=["opActivateSwitch"])


def run_tests():
    """Run all tests in this file."""
    suite = TriggerGateTest()
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
