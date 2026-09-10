"""Tests for core_attunement."""

import json
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../src/Python")))

from htn_test_framework import HtnTestSuite


WORLD = [
    "region(pit)", "region(ledge)", "lineOfSight(ledge, pit)",
    "role(player, player)", "role(arcanist, companion)", "role(gob, enemy)",
    "at(player, ledge)", "at(arcanist, ledge)", "at(gob, pit)",
    "regionHas(pit, oil)",
    "skillElement(ignite, fire)", "skillElement(freeze, freeze)", "skillElement(lightning, lightning)",
    "reacts(fire, oil, scorched)", "reacts(freeze, oil, sludge)",
    "blast(fire, oil, dead)", "terrain(sludge, snared)",
    "strike(fire, dead)", "strike(lightning, dead)",
    "hasSkill(arcanist, freeze)", "signature(arcanist, freeze)",
]


class CoreAttunementTest(HtnTestSuite):

    def setup(self):
        self.load_component("core/primitives/core_attunement", reset_first=True)
        self.verify_contracts()
        self.set_state(WORLD)

    def _all_plans(self, goal):
        error, result = self._planner.FindAllPlansCustomVariables(goal)
        assert error is None, error
        solutions = json.loads(result)
        if not solutions or (isinstance(solutions[0], dict) and "false" in solutions[0]):
            return []
        return solutions

    # ---------------------------------------------------------------- examples

    def test_example_1_a_companion_primes(self):
        self.assert_plan("prime(freeze, pit).",
                         contains=["opCastRegion(arcanist, freeze, pit, oil, sludge)"])

    def _actors(self, plans, op_name):
        out = set()
        for plan in plans:
            for op in plan:
                name = list(op.keys())[0]
                if name == op_name:
                    out.add(list(op[name][0].keys())[0])
        return out

    def test_example_2_anyone_detonates_but_the_primer(self):
        self.set_state(["hasSkill(arcanist, ignite)", "charge(arcanist, ignite, a1)",
                        "hasSkill(player, ignite)", "charge(player, ignite, p1)"])
        actors = self._actors(self._all_plans("detonate(fire, pit)."), "opCastRegion")
        assert actors == {"player", "arcanist"}, f"any companion may detonate: {actors}"
        excluded = self._actors(self._all_plans("detonate(fire, pit, arcanist)."), "opCastRegion")
        assert excluded == {"player"}, f"the primer may not pay off: {excluded}"
        self._record(True, "Example 2: anyone detonates but the primer")

    def test_example_3_finish_a_snared_enemy(self):
        self.set_state(["status(gob, snared)", "hasSkill(player, lightning)",
                        "charge(player, lightning, l1)"])
        self.assert_plan("finish(gob).", contains=["opCastEntity(player, lightning, gob, dead)"])

    # -------------------------------------------------------------- properties

    def test_property_p1_two_roles_two_companions(self):
        """With one fire holder, that holder cannot both prime and pay off."""
        self.set_state(["hasSkill(arcanist, ignite)", "charge(arcanist, ignite, a1)"])
        self.assert_plan("detonate(fire, pit).",
                         contains=["opCastRegion(arcanist, ignite, pit, oil, scorched)"])
        self.assert_no_plan("detonate(fire, pit, arcanist).")

    def test_property_p2_immunity_is_respected(self):
        self.set_state(["status(gob, snared)", "immune(gob, fire)",
                        "hasSkill(player, ignite)", "charge(player, ignite, p1)"])
        self.assert_no_plan("finish(gob).")


def run_tests():
    suite = CoreAttunementTest()
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
