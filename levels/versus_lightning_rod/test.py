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
POOL = ["taunt", "blindingFlash", "hook", "vortex", "tidalWave", "fireball"]

# The measured matrix: the pairs that win, and nothing else does.
WINNING = {
    frozenset(p) for p in [
        # a hook soaks the robot (into the fountain), a taunt lures the golem
        # onto it, and the hook drags the taunter out of the discharge
        ("hook", "taunt"),
        # soaked and brought together by a mover, set off by a flash
        ("hook", "blindingFlash"), ("vortex", "blindingFlash"), ("tidalWave", "blindingFlash"),
    ]
}


def _solutions(planner, goal):
    error, result = planner.FindAllPlansCustomVariables(goal)
    assert error is None, error
    solutions = json.loads(result)
    if not solutions or (isinstance(solutions[0], dict) and "false" in solutions[0]):
        return []
    return solutions


def plans_with(player, mage):
    """All winning plans with the player knowing `player` and the mage `mage`, on a fresh
    planner (a failed search locks the rule set)."""
    with open(os.path.join(HERE, "level.htn"), encoding="utf-8") as f:
        text = f.read()
    text = re.sub(r"^knows\((player|mage), \w+\)\.\n", "", text, flags=re.M)
    planner = HtnPlanner(False)
    planner.SetMemoryBudget(256 * 1024 * 1024)
    loader = ComponentLoader(planner, ROOT, warn=lambda m: None)
    loader.load("abilities/goals/neutralize")
    loader.load("abilities/primitives/ab_catalog")
    kit = f"knows(player, {player}).\nknows(mage, {mage}).\n"
    assert planner.HtnCompileCustomVariables(text + kit) is None
    return _solutions(planner, "win.")


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

    def test_example_1_hook_it_in_taunt_the_golem_hook_the_taunter_out(self):
        ops = ops_text(plans_with("hook", "taunt"))
        for op in ["opForcedMove(player,robot,hall,fountain)", "opCast(mage,taunt,golem)",
                   "opForcedMove(mage,golem,forge,fountain)", "opWindUp(golem,discharge,fountain)",
                   "opCast(player,hook,mage)", "opForcedMove(player,mage,fountain,hall)",
                   "opExploit(golem,robot,electrocuted,dead)"]:
            assert op in ops, f"missing {op}"
        self._record(True, "Example 1: hook the robot into the fountain, taunt, hook the taunter out")

    def test_example_2_wash_the_golem_over_and_flash_it(self):
        ops = ops_text(plans_with("tidalWave", "blindingFlash"))
        for op in ["opForcedMove(player,robot,hall,fountain)", "opForcedMove(player,golem,forge,fountain)",
                   "opCast(mage,blindingFlash,mage)", "opWindUp(golem,discharge,fountain)",
                   "opExploit(golem,robot,electrocuted,dead)"]:
            assert op in ops, f"missing {op}"
        self._record(True, "Example 2: wash the robot and the golem into the fountain, flash")

    def test_example_3_vortex_both_and_flash_from_inside(self):
        plans = plans_with("vortex", "blindingFlash")
        ops = ops_text(plans)
        for op in ["opCast(player,vortex,fountain)", "opCast(player,vortex,hall)",
                   "opForcedMove(player,golem,forge,hall)", "opBlow(golem,discharge,hall,hall)",
                   "opExploit(golem,robot,electrocuted,dead)"]:
            assert op in ops, f"missing {op}"
        # the mage was drawn into the hall by the vortex and flashes from inside: disjoint
        inside = [p for p in plans if "opForcedMove(player,mage,gallery,hall)" in ops_list(p)
                  and not any(o.startswith("opNavigate(mage") for o in ops_list(p))]
        assert inside, "no plan flashes from inside the struck hall"
        self._record(True, "Example 3: vortex the robot into the pool, then both into the hall; flash")

    # -------------------------------------------------------------- properties

    def test_property_p1_no_single_skill_wins(self):
        winners = [s for s in POOL if plans_with(s, s)]
        assert not winners, f"a single skill wins: {winners}"
        self._record(True, "P1: no skill wins alone, even held by both companions")

    def test_property_p2_measured_pairs_win(self):
        found = {frozenset((a, b)) for a, b in itertools.combinations(POOL, 2) if plans_with(a, b)}
        assert found == WINNING, f"extra: {found - WINNING}, missing: {WINNING - found}"
        self._record(True, f"P2: exactly the {len(WINNING)} measured pairs win")

    def test_property_p3_the_taunter_is_always_pulled_out(self):
        """Every hook + taunt plan has the hook cast on the taunter inside the window."""
        plans = plans_with("hook", "taunt")
        assert plans
        for p in plans:
            ops = ops_list(p)
            w = next(i for i, o in enumerate(ops) if o.startswith("opWindUp(golem"))
            b = next(i for i, o in enumerate(ops) if o.startswith("opBlow(golem"))
            assert "opCast(player,hook,mage)" in ops[w:b], ops
        self._record(True, "P3: the taunter is hooked out between the wind-up and the blow")

    def test_property_p4_no_rescue_but_a_hook(self):
        """A wave or a vortex cast to save the taunter moves the robot out too."""
        assert not plans_with("taunt", "tidalWave") and not plans_with("taunt", "vortex")
        self._record(True, "P4: taunt with a wave or a vortex: no plan")

    def test_property_p5_fire_dries(self):
        """Fireball never helps: steam on the soaked robot, or its own fire put out in the pool."""
        assert not any(plans_with("fireball", s) for s in POOL if s != "fireball")
        self._record(True, "P5: fireball wins with nothing")


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
