"""Tests for the Ring-Out level."""

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
COMPANIONS = {"player", "mage"}
DEPS = ("abilities/goals/neutralize", "abilities/primitives/ab_catalog")

BRINGERS = ("hook", "taunt")
KNOCKERS = ("fireball", "tidalWave", "shieldBash", "vortex")
# The measured matrix, unordered: one bringer and one knocker, each way round.
WINNING = {frozenset((b, k)) for b in BRINGERS for k in KNOCKERS}

_REPORT = []


def combos_report():
    """One parallel `combos` run, shared by the properties that read it."""
    if not _REPORT:
        _REPORT.append(run_combos(HERE, ROOT))
    return _REPORT[0]


def _solutions(planner, goal):
    error, result = planner.FindAllPlansCustomVariables(goal)
    assert error is None, error
    solutions = json.loads(result)
    if not solutions or (isinstance(solutions[0], dict) and "false" in solutions[0]):
        return []
    return solutions


def _casters(plan):
    """The companions who cast in a plan (walking is not a second pair of hands)."""
    out = set()
    for op in plan:
        name = list(op.keys())[0]
        if name == "opCast":
            out.add(list(op[name][0].keys())[0])
    return out & COMPANIONS


def _planner(extra="", strip_kit=True, replace=()):
    with open(os.path.join(HERE, "level.htn"), encoding="utf-8") as f:
        text = f.read()
    for old, new in replace:
        assert old in text, old
        text = text.replace(old, new)
    if strip_kit:
        text = re.sub(r"^knows\((player|mage), \w+\)\.\n", "", text, flags=re.M)
    planner = HtnPlanner(False)
    planner.SetMemoryBudget(256 * 1024 * 1024)
    loader = ComponentLoader(planner, ROOT)
    for dep in DEPS:
        loader.load(dep)
    assert planner.HtnCompileCustomVariables(text + extra) is None
    return planner


def plans_with(player, mage, goal="win.", **kw):
    """Plans with the player knowing `player` and the mage `mage`, on a fresh
    planner (a failed search locks the rule set)."""
    kit = f"knows(player, {player}).\nknows(mage, {mage}).\n"
    return _solutions(_planner(kit, **kw), goal)


def _ops(plans):
    return " ".join(json.dumps(p) for p in plans).replace(" ", "")


def _op(name, *args):
    return f'"{name}":[' + ",".join('{"%s":[]}' % a for a in args) + "]"


def _fell(plan, who):
    """`who` went over in this plan."""
    return ('{"%s":[]},{"fell":[]}' % who) in _ops([plan])


class RingOutTest(HtnTestSuite):

    def setup(self):
        for i, dep in enumerate(DEPS):
            self.load_component(dep, reset_first=(i == 0))
        self.verify_contracts()
        self._loader.load_level_htn(HERE)
        self._planner.SetMemoryBudget(256 * 1024 * 1024)

    # ---------------------------------------------------------------- examples

    def test_example_1_hook_it_onto_the_brink_then_knock_it_over(self):
        self.assert_state_after("win.", has=["tag(ogre,fell)"])
        self.assert_plan("win.", contains=[
            "opCast(mage, hook, ogre)", "opForcedMove(mage, ogre, plinth, brink)",
            "opKnock(player, ogre, verge)", "opExploit(player, ogre, chasm, fell)"])

    def test_example_2_taunt_it_and_knock_it_over_before_the_slam(self):
        ops = _ops(plans_with("taunt", "fireball"))
        assert _op("opWindUp", "ogre", "groundSlam", "brink") in ops, ops[:400]
        assert (_op("opCast", "mage", "fireball", "ogre") + "},{" +
                _op("opSpill", "mage", "brink", "flames")) in ops
        assert _op("opMiss", "ogre", "groundSlam", "brink") in ops
        self._record(True, "Example 2: taunted onto the brink, it winds up; the fireball knocks it "
                           "over the verge before the slam lands")

    def test_example_3_a_wave_on_the_brink(self):
        ops = _ops(plans_with("hook", "tidalWave"))
        assert _op("opCast", "mage", "tidalWave", "mage") in ops, ops[:400]
        assert _op("opKnock", "mage", "ogre", "verge") in ops
        self._record(True, "Example 3: hooked onto the brink, the wave washes it over")

    def test_example_4_take_the_slam_then_the_vortex(self):
        plans = plans_with("taunt", "vortex")
        ops = _ops(plans)
        assert _op("opBlow", "ogre", "groundSlam", "brink", "brink") in ops, ops[:400]
        assert _op("opCast", "mage", "vortex", "verge") in ops
        self._record(True, "Example 4: the taunter takes the slam; the vortex draws the ogre over")

    # -------------------------------------------------------------- properties

    def test_property_p1_no_companion_carries_a_plan_alone(self):
        plans = _solutions(self._planner, "win.")
        assert plans, "the level must be winnable"
        for plan in plans:
            assert len(_casters(plan)) >= 2, f"one companion carries this plan alone: {plan}"
        self._record(True, f"P1: {len(plans)} plans, each with two or more casters")

    def test_property_p2_no_single_skill_wins(self):
        report = combos_report()
        assert not report.singles_winning, f"a single skill wins: {report.singles_winning}"
        self._record(True, "P2: no pool skill wins alone, even held by both")

    def test_property_p3_the_measured_pairs_win(self):
        report = combos_report()
        found = {frozenset((w["player"][0], w["mage"][0])) for w in report.winning}
        assert found == WINNING, f"extra: {found - WINNING}, missing: {WINNING - found}"
        assert len(report.winning) == 2 * len(WINNING), "each pair should win in both seat orders"
        assert not report.failures, report.failures
        assert not report.dead_skills, report.dead_skills
        self._record(True, f"P3: exactly the {len(WINNING)} bringer x knocker pairs win")

    def test_property_p4_the_plinth_has_no_edge(self):
        """A knock on the plinth goes nowhere: two knockers never win."""
        assert not plans_with("fireball", "shieldBash")
        planner = _planner("knows(player, fireball).\nknows(mage, hook).\n")
        plans = _solutions(planner, "castFrom(player, fireball, ogre, yard).")
        assert plans and "opExploit" not in _ops(plans)
        self._record(True, "P4: the plinth has nothing to knock the ogre into")

    def test_property_p5_the_taunter_may_be_sacrificed(self):
        """Taking the slam is allowed: some plans lose the taunter over the
        verge, and some keep everyone."""
        plans = plans_with("taunt", "shieldBash")
        lost = [p for p in plans if _fell(p, "player")]
        kept = [p for p in plans if not _fell(p, "player")]
        assert lost and kept, (len(lost), len(kept))
        self._record(True, f"P5: {len(lost)} plans sacrifice the taunter, {len(kept)} do not")

    def test_property_p6_step_back_before_the_vortex(self):
        """The vortex draws in everyone on the brink: the hooker steps back
        first, or goes over with the ogre."""
        ops = _ops(plans_with("hook", "vortex"))
        assert _op("opNavigate", "player", "brink", "yard") in ops, ops[:400]
        assert _op("opKnock", "mage", "player", "verge") in ops
        self._record(True, "P6: step back, or the vortex takes the hooker too")


def run_tests():
    suite = RingOutTest()
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
