"""Tests for the Ember Swarm level (crowd control)."""

import functools
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
POOL = ["tidalWave", "blizzard", "vortex", "taunt", "hook", "shieldBash"]

# The measured matrix (htn_components combos: 18 of 36). A douse and a chill:
# tidalWave only douses; blizzard only chills (a first blizzard on the burning
# nest only quenches it, and the nest ices once); vortex and shieldBash douse
# (into the spring) or chill (into the frost vent); taunt and hook herd the
# swarm through the ford (a douse) and up to the vent.
WINNING = {
    frozenset(p) for p in [
        ("tidalWave", "blizzard"), ("blizzard", "vortex"), ("blizzard", "taunt"),
        ("blizzard", "hook"), ("blizzard", "shieldBash"), ("vortex", "taunt"),
        ("vortex", "hook"), ("taunt", "shieldBash"), ("hook", "shieldBash"),
    ]
}


def _solutions(planner, goal):
    error, result = planner.FindAllPlansCustomVariables(goal)
    assert error is None, error
    solutions = json.loads(result)
    if not solutions or (isinstance(solutions[0], dict) and "false" in solutions[0]):
        return []
    return solutions


@functools.lru_cache(maxsize=None)
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
    return tuple(_solutions(planner, "win."))


def op_list(plan):
    """[(name, [args])] for one plan."""
    out = []
    for op in plan:
        name = list(op.keys())[0]
        out.append((name, [list(a.keys())[0] if isinstance(a, dict) else str(a) for a in op[name]]))
    return out


def has_op(plans, name, args):
    return any((name, args) in op_list(p) for p in plans)


class EmberSwarmTest(HtnTestSuite):

    def setup(self):
        self.load_component("abilities/goals/neutralize", reset_first=True)
        self.load_component("abilities/primitives/ab_catalog", reset_first=False)
        self.verify_contracts()
        self._loader.load_level_htn(HERE)

    # ---------------------------------------------------------------- examples

    def test_example_1_wave_then_blizzard(self):
        self.assert_plan("win.", contains=[
            "opCast(player, tidalWave, player)", "opReact(player, b1, burning, wet, extinguish)",
            "opReact(player, b3, burning, wet, extinguish)", "opCast(mage, blizzard, b1)",
            "opExploit(mage, b1, chilled, dead)", "opExploit(mage, b3, chilled, dead)"])

    def test_example_2_herd_through_the_ford_into_the_vent(self):
        plans = plans_with("taunt", "vortex")
        assert plans
        for b in ("b1", "b2", "b3"):
            assert has_op(plans, "opNavigate", [b, "nest", "ford"]), b
            assert has_op(plans, "opReact", [b, b, "burning", "wet", "extinguish"]), b
            assert has_op(plans, "opExploit", ["mage", b, "chilled", "dead"]), b
        assert has_op(plans, "opCast", ["mage", "vortex", "frostVent"])
        self._record(True, "Example 2: the taunted swarm wades the ford, then the vortex throws it into the vent")

    def test_example_3_one_skill_two_roles(self):
        assert has_op(plans_with("vortex", "blizzard"), "opCast", ["player", "vortex", "spring"])
        assert has_op(plans_with("vortex", "taunt"), "opCast", ["player", "vortex", "frostVent"])
        assert has_op(plans_with("shieldBash", "blizzard"), "opKnock", ["player", "b1", "spring"])
        assert has_op(plans_with("shieldBash", "taunt"), "opKnock", ["player", "b1", "frostVent"])
        self._record(True, "Example 3: vortex and shieldBash douse (spring) or chill (vent)")

    def test_example_4_traps(self):
        assert not plans_with("blizzard", "blizzard"), "the nest ices once"
        assert not plans_with("tidalWave", "taunt"), "herded through the ford after the wave: wet"
        assert not plans_with("tidalWave", "vortex"), "nothing chills"
        assert not plans_with("taunt", "hook"), "two movers: nothing chills"
        self._record(True, "Example 4: cold twice, wet after the douse, two movers")

    # -------------------------------------------------------------- properties

    def test_property_p1_no_single_skill_wins(self):
        winners = [s for s in POOL if plans_with(s, s)]
        assert not winners, f"a single skill wins: {winners}"
        self._record(True, "P1: no skill wins alone, even held by both companions")

    def test_property_p2_the_measured_pairs_win(self):
        found = {frozenset((a, b)) for a, b in itertools.combinations(POOL, 2) if plans_with(a, b)}
        assert found == WINNING, f"extra: {found - WINNING}, missing: {WINNING - found}"
        self._record(True, f"P2: exactly the {len(WINNING)} measured pairs win")

    def test_property_p3_each_hand_matters(self):
        for a, b in [tuple(p) for p in WINNING]:
            assert plans_with(a, b) and plans_with(b, a), f"{a}+{b}"
        self._record(True, "P3: the pairs win whichever companion holds which half")

    def test_property_p4_douse_before_chill(self):
        """In every winning plan the whole swarm's fire is out before the first beetle dies,
        and every beetle dies of the cold."""
        for a, b in [tuple(p) for p in WINNING]:
            for plan in plans_with(a, b):
                ops = op_list(plan)
                doused = [i for i, (n, args) in enumerate(ops)
                          if n == "opReact" and args[-1] in ("extinguish", "quench")]
                dead = [i for i, (n, args) in enumerate(ops)
                        if n == "opExploit" and args[2:] == ["chilled", "dead"]]
                assert len(dead) == 3 and len(doused) >= 3 and max(doused) < min(dead), f"{a}+{b}"
        self._record(True, "P4: every plan douses all three before any dies, then chills them")


def run_tests():
    suite = EmberSwarmTest()
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
