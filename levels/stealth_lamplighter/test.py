"""Tests for the Lamplighter level (stealth and avoidance)."""

import json
import os
import re
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../src/Python")))

from htn_test_framework import HtnTestSuite
from indhtnpy import HtnPlanner
from htn_components.loader import ComponentLoader
from htn_components.combos import run_combos

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "../.."))
GOAL = "escape."
POOL = ["vanish", "smokeBomb", "flashbang", "sleepDart", "gust", "taunt", "pebble"]
LEVER = ["vanish", "smokeBomb", "flashbang", "sleepDart", "gust"]
HALL = ["gust", "taunt", "pebble"]

# The measured matrix (htn_components combos): a lever answer and a hall
# answer, held by either companion - but not gust twice: there is one crate.
WINNING = ({(a, b) for a in LEVER for b in HALL if a != b}
           | {(b, a) for a in LEVER for b in HALL if a != b})

_REPORT = None


def combos_report():
    global _REPORT
    if _REPORT is None:
        _REPORT = run_combos(HERE, ROOT)
    return _REPORT


def flat(plan):
    out = []
    for op in plan:
        name = list(op.keys())[0]
        args = [list(a.keys())[0] if isinstance(a, dict) else str(a) for a in op[name]]
        out.append(f"{name}({', '.join(args)})")
    return out


def plans_with(player, mage):
    """All winning plans with the player knowing `player` and the mage `mage`,
    on a fresh planner (a failed search locks the rule set)."""
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
    error, result = planner.FindAllPlansCustomVariables(GOAL)
    assert error is None, error
    sols = json.loads(result)
    if not sols or (isinstance(sols[0], dict) and "false" in sols[0]):
        return []
    return [flat(s) for s in sols]


def some_plan_has(plans, *ops):
    return any(all(o in p for o in ops) for p in plans)


class LamplighterTest(HtnTestSuite):

    def setup(self):
        self.load_component("abilities/goals/neutralize", reset_first=True)
        self.load_component("abilities/primitives/ab_catalog", reset_first=False)
        self.verify_contracts()
        self._loader.load_level_htn(HERE)

    # ---------------------------------------------------------------- examples

    def test_example_1_crate_on_the_lever_and_a_taunt(self):
        plans = plans_with("gust", "taunt")
        assert some_plan_has(plans, "opForcedMove(player, crate, yard, guardroom)",
                             "opOpen(player, gate)",
                             "opForcedMove(mage, lamplighter, post, start)",
                             "opNavigate(player, gate, exit)", "opNavigate(mage, gate, exit)"), plans[:2]
        self._record(True, "Example 1: the crate goes onto the lever; a taunt drags the lamplighter off his post")

    def test_example_2_sneak_to_the_lever_and_a_pebble(self):
        plans = plans_with("vanish", "pebble")
        assert some_plan_has(plans, "opCast(player, vanish, player)",
                             "opNavigate(player, start, guardroom)",
                             "opProvoked(lamplighter, curious, lookDownWell)",
                             "opForcedMove(lamplighter, lamplighter, post, well)"), plans[:2]
        self._record(True, "Example 2: the player vanishes onto the lever; a pebble sends the lamplighter to the well")

    def test_example_3_blind_the_warden_and_take_cover(self):
        plans = plans_with("flashbang", "gust")
        assert some_plan_has(plans, "opGrant(player, warden, blinded)",
                             "opForcedMove(mage, crate, yard, hall)",
                             "opNavigate(mage, gate, exit)"), plans[:2]
        self._record(True, "Example 3: a flash blinds the warden; the crate shoved into the hall is cover")

    # -------------------------------------------------------------- properties

    def test_property_p1_no_single_skill_wins(self):
        report = combos_report()
        assert not report.singles_winning, report.singles_winning
        assert not plans_with("gust", "gust")
        self._record(True, "P1: no skill wins alone, even held by both companions - not even gust")

    def test_property_p2_measured_assignments_win(self):
        report = combos_report()
        found = {(w["player"][0], w["mage"][0]) for w in report.winning}
        assert found == WINNING, f"extra: {found - WINNING}, missing: {WINNING - found}"
        assert report.solo_plans == 0 and not report.dead_skills and not report.failures
        self._record(True, f"P2: exactly the {len(WINNING)} measured assignments win, none solo")

    def test_property_p3_the_lamps_undo_stealth(self):
        assert not plans_with("vanish", "smokeBomb")
        plans = plans_with("vanish", "taunt")
        assert plans and all("opRemove(player, player, stealthed)" in p for p in plans)
        self._record(True, "P3: two sneaks never cross the hall; the lamps strip the thief's stealth")

    def test_property_p4_the_lantern_and_the_heavy_warden(self):
        assert not plans_with("flashbang", "sleepDart")
        assert not plans_with("taunt", "pebble")
        self._record(True, "P4: nothing dazzles the lamplighter; nothing lures the warden")

    def test_property_p5_gust_has_two_roles(self):
        lever = plans_with("gust", "pebble")
        cover = plans_with("sleepDart", "gust")
        assert lever and all("opForcedMove(player, crate, yard, guardroom)" in p for p in lever)
        assert cover and all("opForcedMove(mage, crate, yard, hall)" in p for p in cover)
        self._record(True, "P5: gust puts the crate on the lever, or in the hall as cover")


def run_tests():
    suite = LamplighterTest()
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
