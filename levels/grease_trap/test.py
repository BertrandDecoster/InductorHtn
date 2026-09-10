"""Tests for the Grease Trap level."""

import json
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../src/Python")))

from htn_test_framework import HtnTestSuite


class GreaseTrapTest(HtnTestSuite):

    def setup(self):
        self.load_component("core/goals/defeat_group", reset_first=True)
        self.verify_contracts()
        self._loader.load_level_htn(os.path.dirname(os.path.abspath(__file__)))

    def _all_plans(self, goal):
        error, result = self._planner.FindAllPlansCustomVariables(goal)
        assert error is None, error
        solutions = json.loads(result)
        if not solutions or (isinstance(solutions[0], dict) and "false" in solutions[0]):
            return []
        return solutions

    # ---------------------------------------------------------------- examples

    def test_example_1_the_burn_takes_the_swarm(self):
        self.assert_plan("defeatGroup(swarm).", contains=[
            "opPush(player, swarm, gallery, corridor)",
            "opCastRegion(player, ignite, corridor, oil, scorched)",
        ])
        self.assert_state_after("theBurn(swarm).",
                                has=["regionHas(corridor,scorched)", "status(swarm,dead)"])

    def test_example_2_the_slipstream_takes_the_bearer(self):
        self.assert_plan("theSlipstream(bearer).", contains=[
            "opCastRegion(arcanist, freeze, corridor, oil, sludge)",
            "opAnchor(warden)",
            "opLure(warden, bearer, exit, corridor)",
            "opStatus(warden, bearer, snared)",
            "opCastEntity(player, ignite, bearer, dead)",
        ])

    def test_example_3_the_whole_encounter(self):
        self.assert_state_after("clearGreaseTrap.",
                                has=["status(swarm,dead)", "status(bearer,dead)"])

    # -------------------------------------------------------------- properties

    def test_property_p1_no_companion_carries_a_plan_alone(self):
        """Every plan needs at least two companions, and the controlled one
        is among them - by the level's role structure, not by any rule that
        names the player."""
        plans = self._all_plans("clearGreaseTrap.")
        assert plans, "the encounter must be solvable"
        for plan in plans:
            actors = {list(op[list(op.keys())[0]][0].keys())[0] for op in plan}
            allies = actors & {"player", "warden", "arcanist"}
            assert len(allies) >= 2, f"one companion carries this plan alone: {plan}"
            assert "player" in allies, f"the controlled companion is idle: {plan}"
        self._record(True, "P1: no companion carries a plan alone")

    def test_property_p2_a_gust_does_not_move_iron(self):
        """The bearer is the Warden's problem: no push plan for it."""
        self.assert_no_plan("push(bearer, corridor).")

    def test_property_p3_burned_oil_cannot_be_frozen(self):
        self.run_goal("theBurn(swarm)")
        self.assert_no_plan("theSlipstream(bearer).")


def run_tests():
    suite = GreaseTrapTest()
    for method_name in sorted(dir(suite)):
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
    sys.exit(0 if run_tests() else 1)
