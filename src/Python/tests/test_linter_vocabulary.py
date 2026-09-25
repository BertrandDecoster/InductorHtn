"""The linter accepts the vocabulary's no-op operators and a verb's shared head parameters."""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..", "..", "gui", "backend")))

from htn_linter import lint_htn  # noqa: E402


def _codes(source):
    return [(d["code"], d["message"]) for d in lint_htn(source)]


def test_already_true_operators_are_not_bookkeeping():
    source = """
goToLocation(?a, ?l) :- if(at(?a, ?l)), do(opStayInLocation(?a)).
goToLocation(?a, ?l) :- if(at(?a, ?from), \\==(?from, ?l)), do(opMoveTo(?a, ?from, ?l)).
applyTag(?tag, ?t) :- if(hasTag(?t, ?tag)), do(opTagAlreadyOnTarget(?tag, ?t)).
loseAggro(?e, ?a) :- if(not(hasAggro(?e, ?a))), do(opTargetNotAggroed(?e, ?a)).
opStayInLocation(?a) :- del(), add().
opTagAlreadyOnTarget(?tag, ?t) :- del(), add().
opTargetNotAggroed(?e, ?a) :- del(), add().
opMoveTo(?a, ?from, ?to) :- del(at(?a, ?from)), add(at(?a, ?to)).
opBookkeeping(?a) :- del(), add().
"""
    flagged = [m for code, m in _codes(source) if code == "HTN006"]
    assert len(flagged) == 1 and "opBookkeeping" in flagged[0]


def test_a_parameter_one_method_does_not_need_is_not_a_singleton():
    source = """
bringEnemyTo(?lurer, ?e, ?l) :- if(at(?e, ?l)), do(opEnemyAlreadyAtLocation(?e, ?l)).
bringEnemyTo(?lurer, ?e, ?l) :- if(at(?e, ?from), \\==(?from, ?l)), do(opLure(?lurer, ?e, ?l)).
single(?x, ?y) :- if(p(?x)), do(opLure(?x, ?x, ?x)).
opEnemyAlreadyAtLocation(?e, ?l) :- del(), add().
opLure(?a, ?e, ?l) :- del(), add(lured(?e)).
p(a).
at(gob, hut).
"""
    singletons = [m for code, m in _codes(source) if code == "VAR003"]
    assert len(singletons) == 1 and "?y" in singletons[0]
