"""Tests for the Idol level (stealth and avoidance)."""

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
GOAL = "heist."
POOL = ["blink", "lightningFlash", "turnToMist", "taunt", "hook", "vortex", "blindingFlash", "shieldBash"]
NAVE = ["blink", "lightningFlash"]
CRYPT = ["blindingFlash", "shieldBash", "taunt", "hook", "vortex"]
# turnToMist takes the keeper's `heavy` for a moment; a mover that drags or
# draws him then serves both watchers.
MIST_MOVERS = ["taunt", "hook", "vortex"]


def _both_ways(pairs):
    return set(pairs) | {(b, a) for a, b in pairs}


# The measured matrix (htn_components combos): a way into the nave and a way
# past the skeleton, or turnToMist and a mover, held by either companion.
WINNING = _both_ways([(a, b) for a in NAVE for b in CRYPT] +
                     [("turnToMist", m) for m in MIST_MOVERS])

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


class IdolTest(HtnTestSuite):

    def setup(self):
        self.load_component("abilities/goals/neutralize", reset_first=True)
        self.load_component("abilities/primitives/ab_catalog", reset_first=False)
        self.verify_contracts()
        self._loader.load_level_htn(HERE)

    # ---------------------------------------------------------------- examples

    def test_example_1_blink_in_and_taunt_the_skeleton(self):
        plans = plans_with("blink", "taunt")
        assert some_plan_has(plans, "opTeleport(player, entry, nave)",
                             "opRemove(player, player, disjoint)", "opGrant(player, player, silenced)",
                             "opForcedMove(mage, skeleton, crypt, ledge)",
                             "opNavigate(player, crypt, exit)"), plans[:2]
        self._record(True, "Example 1: the player blinks into the nave for the idol; the mage taunts the skeleton up to the ledge")

    def test_example_2_a_dash_and_a_bash(self):
        plans = plans_with("lightningFlash", "shieldBash")
        assert some_plan_has(plans, "opDash(player, entry, nave)",
                             "opNavigate(mage, entry, ledge)",
                             "opGrant(mage, skeleton, stunned)",
                             "opNavigate(player, crypt, exit)"), plans[:2]
        self._record(True, "Example 2: a lightning dash into the nave; a bash from the ledge stuns the skeleton")

    def test_example_3_mist_and_a_taunt(self):
        plans = plans_with("turnToMist", "taunt")
        assert some_plan_has(plans, "opRemove(player, keeper, heavy)",
                             "opForcedMove(mage, keeper, altar, entry)",
                             "opForcedMove(mage, skeleton, crypt, ledge)"), plans[:2]
        self._record(True, "Example 3: the keeper turns to mist and is taunted off the altar; the same taunt drags the skeleton")

    def test_example_4_a_vortex_into_the_ossuary(self):
        plans = plans_with("blink", "vortex")
        assert some_plan_has(plans, "opCast(mage, vortex, ossuary)",
                             "opExploit(mage, skeleton, chasm, fell)",
                             "opNavigate(player, crypt, exit)"), plans[:2]
        self._record(True, "Example 4: a vortex on the ossuary draws the skeleton into the pit")

    # -------------------------------------------------------------- properties

    def test_property_p1_no_single_skill_wins(self):
        report = combos_report()
        assert not report.singles_winning, report.singles_winning
        assert not plans_with("blink", "blink")
        self._record(True, "P1: no skill wins alone, even held by both companions")

    def test_property_p2_measured_assignments_win(self):
        report = combos_report()
        found = {(w["player"][0], w["mage"][0]) for w in report.winning}
        assert found == WINNING, f"extra: {found - WINNING}, missing: {WINNING - found}"
        assert report.solo_plans == 0 and not report.dead_skills and not report.failures
        self._record(True, f"P2: exactly the {len(WINNING)} measured assignments win, none solo")

    def test_property_p3_the_idol_silences(self):
        # Every carrier is silenced, and the skill that got it in is spent:
        # no plan has a cast by the carrier after it took the idol.
        for kit in [("blink", "hook"), ("lightningFlash", "blindingFlash")]:
            plans = plans_with(*kit)
            assert plans
            for p in plans:
                carrier = next(o.split("(")[1].split(",")[0] for o in p
                               if o.startswith("opGrant(") and o.endswith(", silenced)"))
                after = p[p.index(next(o for o in p if o.endswith(", silenced)"))):]
                assert not any(o.startswith(f"opCast({carrier},") for o in after), p
        self._record(True, "P3: the idol silences its bearer - the crypt is the other companion's, or answered first")

    def test_property_p4_the_heavy_keeper(self):
        # Movers and stuns alone never clear the nave: the keeper is heavy and
        # the altar is next to the nave alone.
        assert not plans_with("hook", "shieldBash")
        assert not plans_with("taunt", "vortex")
        self._record(True, "P4: nothing moves the keeper unless he is mist; no bash or flash reaches the altar")

    def test_property_p5_the_skeleton_cannot_be_leapt(self):
        # A way in twice: nothing gets the silenced thief past the skeleton.
        assert not plans_with("blink", "lightningFlash")
        self._record(True, "P5: two ways in leave the skeleton watching the crypt")


def run_tests():
    suite = IdolTest()
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
