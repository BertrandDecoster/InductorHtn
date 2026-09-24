"""Tests for the Lightning Rod level."""

import itertools
import json
import os
import re
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../src/Python")))

from htn_test_framework import HtnTestSuite
from indhtnpy import HtnPlanner
from htn_components.loader import ComponentLoader

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "../.."))
POOL = ["hook", "taunt", "tidalWave", "vortex", "shieldBash", "fireball", "blink"]

# The measured matrix: the pairs that win, and nothing else does.
WINNING = {
    frozenset(p) for p in [
        # soak the robot, then taunt the golem into the hall: it discharges on arrival
        ("taunt", "tidalWave"), ("taunt", "vortex"), ("taunt", "shieldBash"), ("taunt", "blink"),
        # the fire trap, beaten: the second fireball's knock alone soaks the robot
        ("taunt", "fireball"),
        # hook the golem into the hall; water on both sets it off (a wave, a vortex,
        # or the flooded hall it is dragged into)
        ("hook", "tidalWave"), ("hook", "vortex"), ("hook", "blink"),
    ]
}


def _solutions(planner, goal):
    error, result = planner.FindAllPlansCustomVariables(goal)
    assert error is None, error
    solutions = json.loads(result)
    if not solutions or (isinstance(solutions[0], dict) and "false" in solutions[0]):
        return []
    return solutions


def plans_with(player, mage, extra="", goal="win."):
    """All plans of `goal` with the player knowing `player` and the mage `mage`, on a fresh
    planner (a failed search locks the rule set)."""
    with open(os.path.join(HERE, "level.htn"), encoding="utf-8") as f:
        text = f.read()
    text = re.sub(r"^knows\((player|mage), \w+\)\.\n", "", text, flags=re.M)
    planner = HtnPlanner(False)
    planner.SetMemoryBudget(256 * 1024 * 1024)
    loader = ComponentLoader(planner, ROOT, warn=lambda m: None)
    loader.load("abilities/goals/neutralize")
    loader.load("abilities/primitives/ab_catalog")
    kit = f"knows(player, {player}).\nknows(mage, {mage}).\n" + extra
    assert planner.HtnCompileCustomVariables(text + kit) is None
    return _solutions(planner, goal)


def ops_list(plan):
    out = []
    for op in plan:
        name = list(op.keys())[0]
        args = [list(a.keys())[0] if isinstance(a, dict) else str(a) for a in op[name]]
        out.append(f"{name}({','.join(args)})")
    return out


def ops_text(plans):
    """Every operator of every plan, as `name(a,b,...)` strings joined by spaces."""
    return " ".join(" ".join(ops_list(p)) for p in plans)


class LightningRodTest(HtnTestSuite):

    def setup(self):
        self.load_component("abilities/goals/neutralize", reset_first=True)
        self.load_component("abilities/primitives/ab_catalog", reset_first=False)
        self.verify_contracts()
        self._loader.load_level_htn(HERE)

    # ---------------------------------------------------------------- examples

    def test_example_1_flood_the_hall_and_hook_the_golem_in(self):
        ops = ops_list(plans_with("hook", "blink")[0])
        for op in ["opTeleport(mage,gallery,pumps)", "opStepOn(mage,mage,valve)",
                   "opSpill(mage,hall,puddle)", "opGrant(mage,robot,wet)",
                   "opForcedMove(player,golem,forge,hall)", "opGrant(player,golem,wet)",
                   "opBlow(golem,discharge,hall,hall)", "opExploit(golem,robot,electrocuted,dead)"]:
            assert op in ops, f"missing {op}"
        self._record(True, "Example 1: blink onto the valve, hook the golem into the flooded hall")

    def test_example_2_bash_it_into_the_fountain_then_taunt(self):
        ops = ops_list(plans_with("taunt", "shieldBash")[0])
        for op in ["opCast(mage,shieldBash,robot)", "opKnock(mage,robot,fountain)",
                   "opCast(player,taunt,golem)", "opNavigate(golem,forge,hall)",
                   "opWindUp(golem,discharge,hall)", "opExploit(golem,robot,electrocuted,dead)"]:
            assert op in ops, f"missing {op}"
        self._record(True, "Example 2: bash the robot into the fountain, taunt the golem in")

    def test_example_3_hook_then_vortex_both_into_the_fountain(self):
        ops = ops_text(plans_with("hook", "vortex"))
        for op in ["opForcedMove(player,golem,forge,hall)", "opCast(mage,vortex,fountain)",
                   "opKnock(mage,golem,fountain)", "opProvoked(golem,wet,discharge)",
                   "opExploit(golem,robot,electrocuted,dead)"]:
            assert op in ops, f"missing {op}"
        self._record(True, "Example 3: hook the golem in, vortex both into the fountain")

    def test_example_4_the_second_fireball(self):
        ops = ops_list(plans_with("taunt", "fireball")[0])
        assert "opReact(mage,robot,burning,wet,extinguish)" in ops, ops
        w = ops.index("opWindUp(golem,discharge,hall)")
        b = ops.index("opBlow(golem,discharge,hall,hall)")
        assert "opCast(mage,fireball,robot)" in ops[w:b], ops
        self._record(True, "Example 4: the first fireball dries the robot; the second, in the window, soaks it")

    # -------------------------------------------------------------- properties

    def test_property_p1_no_single_skill_wins(self):
        winners = [s for s in POOL if plans_with(s, s)]
        assert not winners, f"a single skill wins: {winners}"
        self._record(True, "P1: no skill wins alone, even held by both companions")

    def test_property_p2_measured_pairs_win(self):
        found = {frozenset((a, b)) for a, b in itertools.combinations(POOL, 2) if plans_with(a, b)}
        assert found == WINNING, f"extra: {found - WINNING}, missing: {WINNING - found}"
        self._record(True, f"P2: exactly the {len(WINNING)} measured pairs win")

    def test_property_p3_one_charge(self):
        """The discharge spends the golem: on a dry robot it only stuns it, and nothing
        sets it off again."""
        plans = plans_with("taunt", "hook", goal="walkTo(player, hall), cast(player, taunt, golem).")
        ops = ops_text(plans)
        assert "opExploit(golem,robot,electrocuted,stunned)" in ops and "opGrant(golem,golem,silenced)" in ops
        assert not plans_with("taunt", "hook")
        self._record(True, "P3: one charge - wasted on a dry robot")

    def test_property_p4_a_stunned_golem_never_discharges(self):
        assert not plans_with("hook", "shieldBash")
        assert not plans_with("hook", "tidalWave", "tag(golem, stunned).\n")
        self._record(True, "P4: a bash stuns the golem (silenced): no discharge")

    def test_property_p5_water_in_the_forge_spends_the_charge(self):
        assert not plans_with("blink", "tidalWave")
        self._record(True, "P5: flood the hall and wave the golem in its forge: spent there")


def run_tests():
    suite = LightningRodTest()
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
