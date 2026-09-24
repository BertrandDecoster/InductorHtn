"""Tests for the Doorman level (stealth and avoidance)."""

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
GOAL = "win."
POOL = ["blink", "blindingFlash", "shieldBash", "turnToMist", "taunt", "hook", "vortex", "fireball"]
SENTRY = ["blink", "blindingFlash", "shieldBash"]
DOORMAN = ["taunt", "hook", "vortex", "fireball"]
# turnToMist takes the sentry's bracing for a moment; a mover that drags or
# draws him then serves both guards (fireball has no line off the wall).
MIST_MOVERS = ["taunt", "hook", "vortex"]


def _both_ways(pairs):
    return set(pairs) | {(b, a) for a, b in pairs}


# The measured matrix (htn_components combos): a sentry answer and a doorman
# answer, or turnToMist and a mover, held by either companion.
WINNING = _both_ways([(s, d) for s in SENTRY for d in DOORMAN] +
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


class DoormanTest(HtnTestSuite):

    def setup(self):
        self.load_component("abilities/goals/neutralize", reset_first=True)
        self.load_component("abilities/primitives/ab_catalog", reset_first=False)
        self.verify_contracts()
        self._loader.load_level_htn(HERE)

    # ---------------------------------------------------------------- examples

    def test_example_1_blink_and_taunt(self):
        plans = plans_with("blink", "taunt")
        assert some_plan_has(plans, "opTeleport(player, yard, court)",
                             "opNavigate(mage, yard, garden)",
                             "opForcedMove(mage, doorman, door, garden)",
                             "opNavigate(player, door, vault)"), plans[:2]
        self._record(True, "Example 1: the player blinks into the courtyard; the mage taunts the doorman into the garden")

    def test_example_2_bash_and_fireball(self):
        plans = plans_with("shieldBash", "fireball")
        assert some_plan_has(plans, "opGrant(player, sentry, stunned)",
                             "opForcedMove(mage, doorman, door, cellar)",
                             "opNavigate(player, door, vault)"), plans[:2]
        self._record(True, "Example 2: a bash stuns the sentry; a fireball blows the doorman down the cellar steps")

    def test_example_3_mist_and_taunt(self):
        plans = plans_with("turnToMist", "taunt")
        assert some_plan_has(plans, "opRemove(player, sentry, heavy)",
                             "opForcedMove(mage, sentry, wall, yard)",
                             "opForcedMove(mage, doorman, door, garden)"), plans[:2]
        self._record(True, "Example 3: the sentry turns to mist and is taunted down; the same taunt clears the door")

    def test_example_4_flash_and_vortex(self):
        plans = plans_with("blindingFlash", "vortex")
        assert some_plan_has(plans, "opGrant(player, sentry, blinded)",
                             "opCast(mage, vortex, cellar)",
                             "opForcedMove(mage, doorman, door, cellar)"), plans[:2]
        self._record(True, "Example 4: a flash blinds the sentry; a vortex draws the doorman down the cellar steps")

    # -------------------------------------------------------------- properties

    def test_property_p1_no_single_skill_wins(self):
        report = combos_report()
        assert not report.singles_winning, report.singles_winning
        for s in ["blink", "taunt", "hook"]:
            assert not plans_with(s, s), s
        self._record(True, "P1: no skill wins alone, even held by both companions")

    def test_property_p2_measured_assignments_win(self):
        report = combos_report()
        found = {(w["player"][0], w["mage"][0]) for w in report.winning}
        assert found == WINNING, f"extra: {found - WINNING}, missing: {WINNING - found}"
        assert report.solo_plans == 0 and not report.dead_skills and not report.failures
        self._record(True, f"P2: exactly the {len(WINNING)} measured assignments win, none solo")

    def test_property_p3_the_doorman_watches_the_vault(self):
        # blink + blindingFlash: the thief can blink into the doorway, but
        # nothing blinds the doorman, and nobody sees into the vault.
        assert not plans_with("blink", "blindingFlash")
        self._record(True, "P3: a blink into the doorway is still under the doorman's eyes")

    def test_property_p4_the_braced_sentry(self):
        # Two movers leave the sentry on the wall; fireball has no line off it,
        # even after turnToMist.
        assert not plans_with("taunt", "vortex")
        assert not plans_with("turnToMist", "fireball")
        self._record(True, "P4: nothing moves the braced sentry unless he is mist and dragged or drawn")

    def test_property_p5_one_skill_two_roles(self):
        plans = plans_with("turnToMist", "hook")
        assert plans and all("opCast(player, turnToMist, sentry)" in p and
                             "opCast(mage, hook, sentry)" in p and
                             "opCast(mage, hook, doorman)" in p for p in plans), plans[:2]
        self._record(True, "P5: with turnToMist, one hook clears both guards")


def run_tests():
    suite = DoormanTest()
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
