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
POOL = ["tidalWave", "blizzard", "vortex", "taunt", "hook", "fireball"]

# The measured matrix (htn_components combos: 14 of 36). A douse and a freeze:
# tidalWave only douses; taunt and hook only freeze (they drag into the ice);
# blizzard and vortex do either - blizzard quenches the nest or ices the
# doused swarm, vortex sucks the swarm into the brook or into the ice - but
# never both halves alone. Fireball wins nothing (it relights the nest).
WINNING = {
    frozenset(p) for p in [
        ("tidalWave", "blizzard"), ("tidalWave", "vortex"), ("tidalWave", "taunt"),
        ("tidalWave", "hook"), ("blizzard", "vortex"), ("blizzard", "taunt"),
        ("blizzard", "hook"),
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

    def test_example_1_wave_then_vortex_into_the_ice(self):
        self.assert_plan("win.", contains=[
            "opCast(player, tidalWave, player)", "opReact(player, b1, burning, wet, extinguish)",
            "opCast(mage, vortex, icecave)", "opForcedMove(mage, b1, nest, icecave)",
            "opExploit(mage, b1, chilled, dead)", "opExploit(mage, b3, chilled, dead)"])

    def test_example_2_quench_then_drag_into_the_ice(self):
        plans = plans_with("blizzard", "taunt")
        ops = ops_text(plans)
        assert plans and "quench" in ops and ops.count('"taunt"') >= 3 and "icecave" in ops
        self._record(True, "Example 2: the blizzard quenches the nest; three taunts drag them into the ice")

    def test_example_3_vortex_into_the_brook_then_ice_it(self):
        plans = plans_with("vortex", "blizzard")
        routes = set()
        for plan in plans:
            ops = op_list(plan)
            if ("opCast", ["player", "vortex", "brook"]) in ops and \
                    any(n == "opReshape" and a[1:] == ["brook", "deepWater", "iceSheet"] for n, a in ops):
                routes.add("brook")
            if ("opCast", ["player", "vortex", "icecave"]) in ops:
                routes.add("icecave")
        assert routes == {"brook", "icecave"}, routes
        self._record(True, "Example 3: vortex douses (into the brook) or freezes (into the ice)")

    def test_example_4_traps(self):
        assert not plans_with("blizzard", "blizzard"), "the nest ices once: the second chill is lost"
        assert not plans_with("vortex", "vortex"), "a vortexed swarm is pinned"
        assert not plans_with("taunt", "hook"), "the brook and the ice cave do not see each other"
        assert not plans_with("tidalWave", "tidalWave"), "wet beetles only freeze"
        assert not plans_with("fireball", "blizzard"), "fire relights the nest"
        self._record(True, "Example 4: cold twice, two vortices, two draggers, two waves, fire")

    # -------------------------------------------------------------- properties

    def test_property_p1_no_single_skill_wins(self):
        winners = [s for s in POOL if plans_with(s, s)]
        assert not winners, f"a single skill wins: {winners}"
        self._record(True, "P1: no skill wins alone, even held by both companions")

    def test_property_p2_seven_pairs_win(self):
        found = {frozenset((a, b)) for a, b in itertools.combinations(POOL, 2) if plans_with(a, b)}
        assert found == WINNING, f"extra: {found - WINNING}, missing: {WINNING - found}"
        self._record(True, f"P2: exactly the {len(WINNING)} measured pairs win")

    def test_property_p3_each_hand_matters(self):
        for a, b in [tuple(p) for p in WINNING]:
            assert plans_with(a, b) and plans_with(b, a), f"{a}+{b}"
        self._record(True, "P3: the pairs win whichever companion holds which half")

    def test_property_p4_douse_before_freeze(self):
        """In every winning plan the whole swarm's fire is out before the first beetle dies,
        and no companion is left frozen."""
        douse = {"extinguish", "quench"}
        for a, b in [tuple(p) for p in WINNING]:
            for plan in plans_with(a, b):
                ops = op_list(plan)
                doused = [i for i, (n, args) in enumerate(ops) if n == "opReact" and args[-1] in douse]
                dead = [i for i, (n, args) in enumerate(ops) if n == "opExploit" and args[-1] == "dead"]
                assert len(dead) == 3 and len(doused) >= 3 and max(doused) < min(dead), f"{a}+{b}"
                stunned = [args for n, args in ops if n == "opGrant" and args[1] in ("player", "mage")
                           and args[2] == "stunned"]
                assert not stunned, f"{a}+{b}: {stunned}"
        self._record(True, "P4: every plan douses all three before any dies; nobody on the team frozen")


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
