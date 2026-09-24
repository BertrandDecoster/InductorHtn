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
POOL = ["blink", "lightningFlash", "blindingFlash", "turnToMist", "hook", "shieldBash", "fireball",
        "vortex"]
# Into the nave: slip in, or blind the keeper.
NAVE = ["blink", "lightningFlash", "blindingFlash"]
# Past the skeleton, from the gallery.
CRYPT = ["hook", "shieldBash", "fireball", "vortex"]


def _both_ways(pairs):
    return set(pairs) | {(b, a) for a, b in pairs}


# The measured matrix (htn_components combos): a way into the nave and a way
# past the skeleton, or turnToMist and a crypt answer (which then also moves
# the misted keeper), held by either companion.
WINNING = _both_ways([(a, b) for a in NAVE for b in CRYPT] +
                     [("turnToMist", m) for m in CRYPT])

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

    def test_example_1_blink_in_hook_the_skeleton(self):
        plans = plans_with("blink", "hook")
        assert some_plan_has(plans, "opTeleport(player, entry, shrine)",
                             "opGrant(player, player, silenced)",
                             "opFall(mage, skeleton, crypt, gallery)",
                             "opNavigate(player, crypt, exit)"), plans[:2]
        self._record(True, "Example 1: the player blinks through the temple wall into the shrine; "
                           "the mage hooks the skeleton into the drop")

    def test_example_2_blind_the_keeper(self):
        plans = plans_with("vortex", "blindingFlash")
        assert some_plan_has(plans, "opGrant(mage, keeper, blinded)",
                             "opKnock(player, skeleton, ossuary)",
                             "opNavigate(player, crypt, exit)"), plans[:2]
        self._record(True, "Example 2: the thief clears the crypt on the way in (a vortex on the "
                           "ossuary); the mage blinds the keeper from the side aisle")

    def test_example_3_mist_and_bash(self):
        plans = plans_with("turnToMist", "shieldBash")
        assert some_plan_has(plans, "opRemove(player, keeper, heavy)",
                             "opKnock(mage, keeper, well)",
                             "opCast(mage, shieldBash, skeleton)"), plans[:2]
        self._record(True, "Example 3: the keeper turns to mist and is bashed into the well; the "
                           "same bash takes the skeleton")

    def test_example_4_a_dash_and_a_fireball(self):
        plans = plans_with("lightningFlash", "fireball")
        assert some_plan_has(plans, "opDash(player, entry, nave)",
                             "opCast(mage, fireball, skeleton)",
                             "opGrant(mage, skeleton, fell)"), plans[:2]
        self._record(True, "Example 4: the player dashes into the nave; the mage blows the "
                           "skeleton off its floor")

    # -------------------------------------------------------------- properties

    def test_property_p1_no_single_skill_wins(self):
        report = combos_report()
        assert not report.singles_winning, report.singles_winning
        for s in ["blink", "shieldBash"]:
            assert not plans_with(s, s), s
        self._record(True, "P1: no skill wins alone, even held by both companions")

    def test_property_p2_measured_assignments_win(self):
        report = combos_report()
        found = {(w["player"][0], w["mage"][0]) for w in report.winning}
        assert found == WINNING, f"extra: {found - WINNING}, missing: {WINNING - found}"
        assert report.solo_plans == 0 and not report.dead_skills and not report.failures
        assert len(report.methods) == 16, report.methods
        self._record(True, f"P2: exactly the {len(WINNING)} measured assignments win "
                           f"({len(report.methods)} methods), none solo, no dead skill")

    def test_property_p3_the_idol_silences(self):
        for kit in [("blink", "hook"), ("blindingFlash", "fireball")]:
            plans = plans_with(*kit)
            assert plans, kit
            for p in plans:
                thief = "player" if "opGrant(player, player, silenced)" in p else "mage"
                hushed = p.index(f"opGrant({thief}, {thief}, silenced)")
                assert not any(o.startswith(f"opCast({thief},") for o in p[hushed:]), p
        self._record(True, "P3: the idol silences its bearer - the crypt is the lookout's, or "
                           "answered first")

    def test_property_p4_the_keeper_is_a_heavy_boss(self):
        assert not plans_with("hook", "shieldBash")
        assert not plans_with("fireball", "vortex")
        self._record(True, "P4: no stun lands on the boss, and nothing moves him unless he is mist")

    def test_property_p5_two_ways_in_are_no_way_out(self):
        assert not plans_with("blink", "lightningFlash")
        assert not plans_with("blink", "blindingFlash")
        self._record(True, "P5: nothing that gets the thief in answers the skeleton")


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
