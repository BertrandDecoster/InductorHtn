"""Tests for the Sync: Decoy level."""

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
from htn_components.manifest import Manifest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "../.."))
POOL = ["taunt", "hook", "fireball", "vortex", "blindingFlash", "lightningFlash"]

# The measured matrix: every golem answer with the blinding flash; the
# lightning flash past the gargoyle with each knock into the well; the decoy
# with its one rescuer.
WINNING = ({frozenset((a, "blindingFlash")) for a in ["hook", "fireball", "vortex", "lightningFlash"]}
           | {frozenset(("lightningFlash", a)) for a in ["fireball", "vortex"]}
           | {frozenset(("taunt", "hook"))})


@functools.lru_cache(maxsize=None)
def plans_with(player, mage):
    """All winning plans (lists of (operator, args)) with the player knowing `player` and
    the mage `mage`, on a fresh planner (a failed search locks the rule set)."""
    with open(os.path.join(HERE, "level.htn"), encoding="utf-8") as f:
        text = f.read()
    text = re.sub(r"^knows\((player|mage), \w+\)\.\n", "", text, flags=re.M)
    planner = HtnPlanner(False)
    planner.SetMemoryBudget(256 * 1024 * 1024)
    loader = ComponentLoader(planner, ROOT, warn=lambda m: None)
    for dep in Manifest.load(os.path.join(HERE, "manifest.json")).dependencies:
        loader.load(dep)
    kit = f"knows(player, {player}).\nknows(mage, {mage}).\n"
    assert planner.HtnCompileCustomVariables(text + kit) is None
    error, result = planner.FindAllPlansCustomVariables("win.")
    assert error is None, error
    solutions = json.loads(result)
    if not solutions or (isinstance(solutions[0], dict) and "false" in solutions[0]):
        return []
    plans = []
    for sol in solutions:
        plan = []
        for op in sol:
            name = list(op.keys())[0]
            plan.append((name, tuple(list(a.keys())[0] if isinstance(a, dict) else str(a)
                                     for a in op[name])))
        plans.append(plan)
    return plans


def has(plans, name, *args):
    return any((name, tuple(args)) in plan for plan in plans)


def index(plan, name, *args):
    return plan.index((name, tuple(args)))


class SyncDecoyTest(HtnTestSuite):

    def setup(self):
        self.load_component("abilities/goals/neutralize", reset_first=True)
        self.load_component("abilities/strategies/passage", reset_first=False)
        self.load_component("abilities/primitives/ab_catalog", reset_first=False)
        self.verify_contracts()
        self._loader.load_level_htn(HERE)

    # ---------------------------------------------------------------- examples

    def test_example_1_bait_the_slam_and_hook_the_decoy_out(self):
        self.assert_plan("win.", contains=[
            "opNavigate(mage, camp, nook)", "opCast(player, taunt, golem)",
            "opNavigate(golem, nook, balcony)", "opWindUp(golem, groundSlam, balcony)",
            "opCast(mage, hook, player)", "opForcedMove(mage, player, balcony, nook)",
            "opBlow(golem, groundSlam, balcony, balcony)", "opGrant(golem, gargoyle, stunned)",
            "opStepOn(player, player, lever)", "opOpen(player, portcullis)"])

    def test_example_2_flash_past_the_gargoyle_vortex_the_golem(self):
        plans = plans_with("lightningFlash", "vortex")
        assert has(plans, "opCast", "mage", "vortex", "well"), plans[:1]
        assert has(plans, "opExploit", "mage", "golem", "chasm", "fell")
        assert has(plans, "opDash", "player", "camp", "hall")
        assert has(plans, "opOpen", "player", "portcullis")
        self._record(True, "Example 2: the vortex drops the golem in the well; the player "
                           "lightning-flashes into the watched hall and walks on")

    def test_example_3_blind_the_gargoyle_flash_past_the_golem(self):
        plans = plans_with("blindingFlash", "lightningFlash")
        assert has(plans, "opGrant", "player", "gargoyle", "blinded"), plans[:1]
        assert has(plans, "opDash", "mage", "hall", "arch")
        assert has(plans, "opStepOn", "mage", "mage", "lever")
        assert not has(plans, "opForcedMove", "mage", "golem", "arch", "hall")
        self._record(True, "Example 3: the gargoyle is blinded; the mage flashes past the "
                           "golem, which never moves")

    # -------------------------------------------------------------- properties

    def test_property_p1_no_single_skill_wins(self):
        winners = [s for s in POOL if plans_with(s, s)]
        assert not winners, f"a single skill wins: {winners}"
        self._record(True, "P1: no skill wins alone, even held by both companions")

    def test_property_p2_the_measured_pairs_win(self):
        found = {frozenset((a, b)) for a, b in itertools.combinations(POOL, 2) if plans_with(a, b)}
        assert found == WINNING, f"extra: {found - WINNING}, missing: {WINNING - found}"
        self._record(True, f"P2: exactly the {len(WINNING)} measured pairs win")

    def test_property_p3_either_seat(self):
        assert plans_with("taunt", "hook") and plans_with("hook", "taunt")
        assert plans_with("fireball", "lightningFlash") and plans_with("lightningFlash", "fireball")
        self._record(True, "P3: a pair wins whichever companion holds which half")

    def test_property_p4_the_rescue_is_the_one_cast_in_the_window(self):
        """In every taunt plan the slam is wound up on the balcony, the
        hook pulls the decoy out between the wind-up and the blow, and the
        blow stuns the gargoyle."""
        plans = plans_with("taunt", "hook")
        assert plans
        for plan in plans:
            up = index(plan, "opWindUp", "golem", "groundSlam", "balcony")
            blow = index(plan, "opBlow", "golem", "groundSlam", "balcony", "balcony")
            window = [args for name, args in plan[up:blow] if name == "opCast"]
            assert window == [("mage", "hook", "player")], window
            assert ("opGrant", ("golem", "gargoyle", "stunned")) in plan[blow:]
        self._record(True, "P4: the slam lands on the gargoyle; the friend's one cast saves the decoy")

    def test_property_p5_no_one_else_saves_the_decoy(self):
        """Only a hook takes the decoy out of the struck area: a flash is
        disjoint for its own caster, a knockback never leaves the area, and a
        knock that drops the golem cancels the slam the gargoyle needed."""
        for partner in ["fireball", "vortex", "blindingFlash", "lightningFlash"]:
            assert not plans_with("taunt", partner), partner
        self._record(True, "P5: taunt wins only with a hook")

    def test_property_p6_one_lightning_flash_each(self):
        """Two mana each: a lightning flash gets you into the hall or past the
        golem, not both."""
        assert not plans_with("lightningFlash", "lightningFlash")
        assert not plans_with("lightningFlash", "hook")
        self._record(True, "P6: one costly cast per companion")

    def test_property_p7_companions_cannot_be_taunted(self):
        self.assert_query("receptive(mage, taunted).", min_solutions=0, max_solutions=0)
        self._record(True, "P7: a taunt never drags a friend out of the blast")


def run_tests():
    suite = SyncDecoyTest()
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
