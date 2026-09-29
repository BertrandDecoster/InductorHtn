"""CrissCross: each companion holds the plate that opens the door the other needs."""

import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(ROOT, "src", "Python"))

from htn_test_framework import HtnTestSuite  # noqa: E402

GOAL = "everyoneReaches(exit)."


def _gap(who, way):
    """`who` crosses the gap into the ledge and holds the ledge plate (the gate opens)."""
    cross = (f"opDashTo({who}, hall, ledge), " if way == "dash"
             else f"opFillHole({who}, crateA, hall, ledge), opMoveTo({who}, hall, ledge), ")
    return cross + f"opPressPlate({who}, ledgePlate), opUnlock(gate), "


def _yard(who, holder):
    """`who` walks through the gate; `who` or crateB holds the yard plate (the hatch opens)."""
    hold = (f"opPressPlate({who}, yardPlate), " if holder == who
            else f"opPushOntoPlate({who}, crateB, yardPlate), ")
    return f"opMoveTo({who}, hall, yard), " + hold + "opUnlock(hatch), "


def _out(ledge, yard, holder, way):
    """The ledge companion leaves through the hatch, then the yard companion crosses the pit."""
    plan = f"opLeavePlate({ledge}, ledgePlate), opLock(gate), opMoveTo({ledge}, ledge, exit), "
    if holder == yard:
        plan += f"opLeavePlate({yard}, yardPlate), opLock(hatch), "
    return plan + (f"opDashTo({yard}, yard, exit)" if way == "dash"
                   else f"opFillHole({yard}, crateB, yard, exit), opMoveTo({yard}, yard, exit)")


def _plan(ledge, gap, yard, holder, pit):
    return _gap(ledge, gap) + _yard(yard, holder) + _out(ledge, yard, holder, pit)


SPARK_DASH_IN = _plan("spark", "dash", "player", "player", "crateB")
SPARK_CRATE_IN = _plan("spark", "crateA", "player", "player", "crateB")
PLAYER_IN_SPARK_DASHES_OUT = _plan("player", "crateA", "spark", "spark", "dash")
PLAYER_IN_SPARK_FILLS_OUT = _plan("player", "crateA", "spark", "spark", "crateB")
CRATE_HOLDS_HATCH = _plan("player", "crateA", "spark", "crateB", "dash")


def _suite(tmp_path, drop=(), replace=(), add=""):
    """The example, with facts dropped, text replaced (old, new) and facts added."""
    path = os.path.join(ROOT, "Examples", "CrissCross.htn")
    if drop or replace or add:
        source = open(path, encoding="utf-8").read()
        for old, new in [(fact, "") for fact in drop] + list(replace):
            assert old in source, old
            source = source.replace(old, new)
        path = str(tmp_path / "CrissCross.htn")
        open(path, "w", encoding="utf-8").write(source + add)
    return HtnTestSuite(path)


def _rules_on(tmp_path, world):
    """The example's rules, without its world, on another map."""
    source = open(os.path.join(ROOT, "Examples", "CrissCross.htn"), encoding="utf-8").read()
    rules = source[:source.index("% World:")]
    path = str(tmp_path / "OtherMap.htn")
    open(path, "w", encoding="utf-8").write(rules + world)
    return HtnTestSuite(path)


def test_five_ways_both_companions_hold_a_door(tmp_path):
    suite = _suite(tmp_path)
    assert suite.assert_plan_set(GOAL, [SPARK_DASH_IN, SPARK_CRATE_IN, PLAYER_IN_SPARK_DASHES_OUT,
                                        PLAYER_IN_SPARK_FILLS_OUT, CRATE_HOLDS_HATCH]), \
        suite.results[-1].details


# Spark also teleports. pathNext breaks a tie by name and would route ledge -> yard through the
# exit; the weight sends it back through the hall, so the no-plan tests don't hang on the route.
SOLO_EXTRAS = "\nhasSkill(spark, blinkSkill). skillHasTag(blinkSkill, teleport).\nsize(exit, 2).\n"
ALONE = ("companion(player).", "at(player, hall).")
ONE_PLAYS_BOTH_ROLES = (("companion(?a2), \\==(?a1, ?a2)", "=(?a2, ?a1)"),)


def test_one_companion_alone_has_no_plan(tmp_path):
    # Alone, spark dashes and teleports over both holes, but a locked door guards every way out.
    suite = _suite(tmp_path, drop=ALONE, add=SOLO_EXTRAS)
    assert suite.assert_no_plan(GOAL), suite.results[-1].details


def test_one_companion_cannot_hold_both_plates(tmp_path):
    # The strategy played by one companion: whoever holds the ledge plate never gets past the gate,
    # and no crate can reach the ledge to hold it instead (crateA is used up in the gap).
    suite = _suite(tmp_path, drop=ALONE, replace=ONE_PLAYS_BOTH_ROLES, add=SOLO_EXTRAS)
    assert suite.assert_no_plan(GOAL), suite.results[-1].details


def test_a_spare_crate_on_the_ledge_lets_one_companion_solo_it(tmp_path):
    # The control for the two tests above: the ledge is what keeps the puzzle cooperative.
    suite = _suite(tmp_path, drop=ALONE, replace=ONE_PLAYS_BOTH_ROLES,
                   add=SOLO_EXTRAS + "object(crateC). at(crateC, ledge).\n")
    assert suite.assert_plan(GOAL, contains=["opPushOntoPlate(spark, crateC, ledgePlate)"]), \
        suite.results[-1].details


def test_without_the_dash_the_crates_fill_both_holes(tmp_path):
    suite = _suite(tmp_path, drop=("hasSkill(spark, lightningDashSkill).",))
    assert suite.assert_plan_set(GOAL, [SPARK_CRATE_IN, PLAYER_IN_SPARK_FILLS_OUT]), \
        suite.results[-1].details


def test_without_crate_b_spark_must_dash_out_of_the_yard(tmp_path):
    suite = _suite(tmp_path, drop=("object(crateB).", "canFillHole(crateB).", "at(crateB, yard)."))
    assert suite.assert_plan_set(GOAL, [PLAYER_IN_SPARK_DASHES_OUT]), suite.results[-1].details


def test_without_crate_a_spark_must_dash_onto_the_ledge(tmp_path):
    suite = _suite(tmp_path, drop=("object(crateA).", "canFillHole(crateA).", "at(crateA, hall)."))
    assert suite.assert_plan_set(GOAL, [SPARK_DASH_IN]), suite.results[-1].details


def test_the_gate_stays_locked_until_the_ledge_plate_is_held(tmp_path):
    suite = _suite(tmp_path)
    assert suite.assert_no_plan("reachLocation(player, yard)."), suite.results[-1].details


# Another map: the plates are listed in the other order, the second door is not next to the
# goal, and the hole is teleported over.
#
#   start --[gate]-- east              westPlate opens the gate
#     |               |  (drop)        eastPlate opens the hatch
#   west --[hatch]-- corridor -- exit
VAULT = """
companion(ann). companion(bo).
object(box). canFillHole(box).
location(start). location(west). location(east). location(corridor). location(exit).
linked(start, west). linked(west, start). linked(start, east). linked(east, start).
linked(west, corridor). linked(corridor, west). linked(east, corridor). linked(corridor, east).
linked(corridor, exit). linked(exit, corridor).
blockedLink(start, east, door(gate)). blockedLink(east, start, door(gate)).
blockedLink(west, corridor, door(hatch)). blockedLink(corridor, west, door(hatch)).
blockedLink(east, corridor, hole). blockedLink(corridor, east, hole).
locked(gate). locked(hatch).
plateOpens(eastPlate, hatch). at(eastPlate, east).
plateOpens(westPlate, gate). at(westPlate, west).
at(ann, start). at(bo, start). at(box, east).
hasSkill(ann, blinkSkill). skillHasTag(blinkSkill, teleport).
"""


def _vault(west, east, holder, way):
    plan = (f"opMoveTo({west}, start, west), opPressPlate({west}, westPlate), opUnlock(gate), "
            f"opMoveTo({east}, start, east), ")
    plan += (f"opPressPlate({east}, eastPlate), " if holder == east
             else f"opPushOntoPlate({east}, box, eastPlate), ")
    plan += (f"opUnlock(hatch), opLeavePlate({west}, westPlate), opLock(gate), "
             f"opMoveTo({west}, west, corridor), opMoveTo({west}, corridor, exit), ")
    if holder == east:
        plan += f"opLeavePlate({east}, eastPlate), opLock(hatch), "
    plan += (f"opTeleportTo({east}, east, corridor), " if way == "teleport"
             else f"opFillHole({east}, box, east, corridor), opMoveTo({east}, east, corridor), ")
    return plan + f"opMoveTo({east}, corridor, exit)"


def test_the_rules_are_generic_on_another_map(tmp_path):
    suite = _rules_on(tmp_path, VAULT)
    assert suite.assert_plan_set(GOAL, [
        _vault("ann", "bo", "bo", "box"),
        _vault("bo", "ann", "ann", "teleport"),
        _vault("bo", "ann", "ann", "box"),
        _vault("bo", "ann", "box", "teleport"),
    ]), suite.results[-1].details
