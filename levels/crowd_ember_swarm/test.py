"""Tests for the Ember Swarm level (crowd control)."""

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
POOL = ["rainCall", "glaciate", "iceStorm", "gust", "roar", "provoke", "taunt"]

# The measured matrix: a douse and a freeze. rainCall and gust only douse;
# roar, provoke and taunt only freeze (they move the swarm into the ice cave);
# glaciate and iceStorm do either (a chill quenches a burning nest, or freezes
# a doused one) - but never both, since the nest ices only once.
DOUSERS = ["rainCall", "gust"]
FREEZERS = ["roar", "provoke", "taunt"]
COLD = ["glaciate", "iceStorm"]
WINNING = (
    {frozenset((d, f)) for d in DOUSERS for f in COLD + FREEZERS}
    | {frozenset((c, f)) for c in COLD for f in FREEZERS}
)


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


def ops_text(plans):
    return " ".join(json.dumps(p) for p in plans)


def op_list(plan):
    """[(name, [args])] for one plan."""
    out = []
    for op in plan:
        name = list(op.keys())[0]
        out.append((name, [list(a.keys())[0] if isinstance(a, dict) else str(a) for a in op[name]]))
    return out


class EmberSwarmTest(HtnTestSuite):

    def setup(self):
        self.load_component("abilities/goals/neutralize", reset_first=True)
        self.load_component("abilities/primitives/ab_catalog", reset_first=False)
        self.verify_contracts()
        self._loader.load_level_htn(HERE)

    # ---------------------------------------------------------------- examples

    def test_example_1_rain_then_roar_into_the_ice(self):
        self.assert_plan("win.", contains=[
            "opCast(player, rainCall, nest)", "opReact(player, b1, burning, wet, extinguish)",
            "opCast(mage, roar, b1)", "opForcedMove(mage, b1, nest, icecave)",
            "opExploit(mage, b1, chilled, frozen)", "opExploit(mage, b3, chilled, frozen)"])

    def test_example_2_quench_then_drag_into_the_ice(self):
        plans = plans_with("glaciate", "provoke")
        ops = ops_text(plans)
        assert plans and "quench" in ops and "icecave" in ops and "frozen" in ops
        self._record(True, "Example 2: glaciate quenches the nest; provoke drags it into the ice cave")

    def test_example_3_blow_them_out_then_freeze(self):
        plans = plans_with("gust", "iceStorm")
        ops = ops_text(plans)
        assert plans and ops.count('"gust"') >= 3 and "frozen" in ops
        self._record(True, "Example 3: gust blows out each flame; one iceStorm freezes the swarm")

    def test_example_4_trap_cold_twice(self):
        assert not plans_with("glaciate", "iceStorm"), "the nest ices once: the second chill is lost"
        assert not plans_with("roar", "provoke"), "burning beetles reach the ice and only slow"
        self._record(True, "Example 4: two colds, or two herders, leave the swarm standing")

    # -------------------------------------------------------------- properties

    def test_property_p1_no_single_skill_wins(self):
        winners = [s for s in POOL if plans_with(s, s)]
        assert not winners, f"a single skill wins: {winners}"
        self._record(True, "P1: no skill wins alone, even held by both companions")

    def test_property_p2_sixteen_pairs_win(self):
        found = {frozenset((a, b)) for a, b in itertools.combinations(POOL, 2) if plans_with(a, b)}
        assert found == WINNING, f"extra: {found - WINNING}, missing: {WINNING - found}"
        self._record(True, f"P2: exactly the {len(WINNING)} measured pairs win")

    def test_property_p3_each_hand_matters(self):
        assert plans_with("roar", "rainCall") and plans_with("provoke", "glaciate")
        self._record(True, "P3: the pairs win whichever companion holds which half")

    def test_property_p4_douse_before_freeze(self):
        """In every winning plan the whole swarm's fire is out before the first beetle freezes."""
        douse = {"extinguish", "quench"}
        for a, b in [tuple(p) for p in WINNING]:
            for plan in plans_with(a, b):
                ops = op_list(plan)
                doused = [i for i, (n, args) in enumerate(ops)
                          if (n == "opReact" and args[-1] in douse)
                          or (n == "opRemove" and args[-1] == "burning")]
                frozen = [i for i, (n, args) in enumerate(ops) if n == "opExploit" and args[-1] == "frozen"]
                assert frozen and len(doused) >= 3 and max(doused) < min(frozen), f"{a}+{b}"
        self._record(True, "P4: every plan douses all three before freezing any")


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
