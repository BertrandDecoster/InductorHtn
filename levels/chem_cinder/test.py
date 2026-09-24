"""Tests for the Cinder level (elemental chemistry)."""

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
POOL = ["tidalWave", "blizzard", "fireball", "shieldBash", "vortex", "hook", "taunt"]
DRAG = ["hook", "taunt"]

# The measured matrix: the pairs that win, and nothing else does.
WINNING = (
    {frozenset(("tidalWave", x)) for x in ["blizzard"] + DRAG}        # douse, then chill
    | {frozenset(("blizzard", x)) for x in DRAG}                      # quench, then onto the pond
    | {frozenset(("blizzard", x)) for x in ["fireball", "shieldBash", "vortex"]}  # dunk, then ice
    | {frozenset(("fireball", x)) for x in DRAG}                      # dunk, then onto the pond
    | {frozenset((x, "hook")) for x in ["shieldBash", "vortex"]}      # dunk, then hook
)


def _solutions(planner, goal):
    error, result = planner.FindAllPlansCustomVariables(goal)
    assert error is None, error
    solutions = json.loads(result)
    if not solutions or (isinstance(solutions[0], dict) and "false" in solutions[0]):
        return []
    return solutions


def names(plan):
    """A plan as a list of 'op(a, b, ...)' strings."""
    out = []
    for op in plan:
        n = list(op.keys())[0]
        args = [list(a.keys())[0] if isinstance(a, dict) else str(a) for a in op[n]]
        out.append(f"{n}({', '.join(args)})")
    return out


def plans_with(player, mage, goal="win."):
    """All plans for `goal` with the player knowing `player` and the mage `mage`, on a
    fresh planner (a failed search locks the rule set), as lists of operator strings."""
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
    return [names(p) for p in _solutions(planner, goal)]


def some_plan_has(plans, *ops):
    return any(all(o in p for o in ops) for p in plans)


class CinderTest(HtnTestSuite):

    def setup(self):
        self.load_component("abilities/goals/neutralize", reset_first=True)
        self.load_component("abilities/primitives/ab_catalog", reset_first=False)
        self.verify_contracts()
        self._loader.load_level_htn(HERE)

    # ---------------------------------------------------------------- examples

    def test_example_1_douse_then_chill(self):
        self.assert_plan("win.", contains=[
            "opNavigate(player, court, yard)", "opCast(player, tidalWave, player)",
            "opReact(player, imp, burning, wet, extinguish)", "opCast(mage, blizzard, imp)",
            "opExploit(mage, imp, chilled, dead)"])

    def test_example_2_dunk_then_lure_onto_the_ice(self):
        plans = plans_with("fireball", "taunt")
        assert some_plan_has(plans, "opKnock(player, imp, fountain)",
                             "opReact(player, imp, burning, wet, extinguish)",
                             "opCast(mage, taunt, imp)", "opNavigate(imp, yard, pond)",
                             "opExploit(imp, imp, chilled, dead)")
        self._record(True, "Example 2: blown into the fountain; lured onto the pond")

    def test_example_3_light_then_ice_twice(self):
        plans = plans_with("fireball", "blizzard")
        assert some_plan_has(plans, "opCast(player, fireball, yard)",
                             "opReshape(mage, yard, flames, puddle)",
                             "opReact(mage, imp, burning, wet, extinguish)",
                             "opReshape(mage, yard, puddle, iceSheet)",
                             "opExploit(mage, imp, chilled, dead)")
        self._record(True, "Example 3: flames, iced to a puddle, iced again: a dry chill")

    def test_example_4_vortex_then_hook_onto_the_ice(self):
        plans = plans_with("vortex", "hook")
        assert some_plan_has(plans, "opCast(player, vortex, fountain)",
                             "opReact(player, imp, burning, wet, extinguish)",
                             "opForcedMove(mage, imp, yard, pond)",
                             "opExploit(mage, imp, chilled, dead)")
        self._record(True, "Example 4: pulled into the fountain, then hooked onto the pond")

    def test_example_5_cold_twice_only_quenches(self):
        assert not plans_with("blizzard", "blizzard")
        self._record(True, "Example 5: two blizzards: a quench, then ice already there")

    # -------------------------------------------------------------- properties

    def test_property_p1_no_single_skill_wins(self):
        winners = [s for s in POOL if plans_with(s, s)]
        assert not winners, f"a single skill wins: {winners}"
        self._record(True, "P1: no skill wins alone, even held by both companions")

    def test_property_p2_twelve_pairs_win_in_either_hand(self):
        wins = {(a, b): bool(plans_with(a, b)) for a, b in itertools.permutations(POOL, 2)}
        found = {frozenset(k) for k, w in wins.items() if w}
        assert found == WINNING, f"extra: {found - WINNING}, missing: {WINNING - found}"
        one_way = sorted(k for k, w in wins.items() if w != wins[(k[1], k[0])])
        assert not one_way, f"win in one order only: {one_way}"
        self._record(True, f"P2: exactly the {len(WINNING)} measured pairs win, in either hand")

    def test_property_p3_the_wave_can_soak_it_again(self):
        """Aimed into the fountain, the wave's own knockback soaks the doused imp: the
        blizzard then only freezes it (stunned)."""
        plans = plans_with("tidalWave", "blizzard",
                           "cast(player, tidalWave, imp), cast(mage, blizzard, imp).")
        assert some_plan_has(plans, "opKnock(player, imp, fountain)", "opGrant(player, imp, wet)",
                             "opReact(mage, imp, wet, chilled, freeze)")
        assert some_plan_has(plans, "opExploit(mage, imp, chilled, dead)")
        self._record(True, "P3: knocked into the fountain after the douse, it only freezes")

    def test_property_p4_rooted_it_cannot_follow(self):
        """Shield Bash stuns it and the vortex roots it for a moment: taunted then, it
        does not walk onto the pond."""
        for first, goal in [("shieldBash", "cast(player, shieldBash, imp), "),
                            ("vortex", "cast(player, vortex, fountain), ")]:
            assert not plans_with(first, "taunt")
            plans = plans_with(first, "taunt", goal + "castFrom(mage, taunt, imp, pond).")
            assert plans and not any("opNavigate(imp, yard, pond)" in p for p in plans)
        self._record(True, "P4: a stunned or rooted imp does not follow the taunt")

    def test_property_p5_the_pond_takes_it_once(self):
        """Brought onto the pond while burning, it is only quenched: hook + taunt lose."""
        assert not plans_with("hook", "taunt")
        plans = plans_with("hook", "taunt", "bringTo(imp, pond, none).")
        assert plans and all("opReact(" in " ".join(p) and not any("dead" in o for o in p)
                             for p in plans)
        assert some_plan_has(plans, "opReact(player, imp, burning, chilled, quench)")
        self._record(True, "P5: the first arrival on the ice only quenches it")


def run_tests():
    suite = CinderTest()
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
