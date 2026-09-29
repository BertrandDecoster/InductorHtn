"""The linter's call graph must follow parallel(...) like try/first/and.

Before this fix, an operator called only inside parallel(...) was invisible
to the call graph: SEM001 (undefined task) never checked it, and SEM004/005
falsely flagged it (and methods reached only through it) as dead code.
prototypes/fortress-loadout/level.htn hit this on opPullLever, opHoldUnder,
opDistract, opSlipBehind, opLureToEdge, ...
"""

import os
import sys

script_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.abspath(os.path.join(script_dir, '../../../gui/backend'))
sys.path.insert(0, backend_dir)

from htn_linter import lint_htn  # noqa: E402

_SOURCE = """
goals(mission()).

mission() :- if(), do(parallel(opLeft(), opRight()), opFinish()).

opLeft() :- del(), add(leftDone).
opRight() :- del(), add(rightDone).
opFinish() :- del(), add(done).
"""

_SOURCE_UNDEFINED = """
goals(mission()).

mission() :- if(), do(parallel(opLeft(), opMissing()), opFinish()).

opLeft() :- del(), add(leftDone).
opFinish() :- del(), add(done).
"""


def _codes(source):
    return [(d["code"], d["message"]) for d in lint_htn(source)]


def test_ops_called_only_inside_parallel_are_not_dead_code():
    diags = _codes(_SOURCE)
    dead = [(c, m) for c, m in diags
            if c in ("SEM004", "SEM005") and ("opLeft" in m or "opRight" in m)]
    assert dead == [], f"parallel-only callees flagged dead: {dead}"


def test_undefined_task_inside_parallel_is_reported():
    diags = _codes(_SOURCE_UNDEFINED)
    assert any(c == "SEM001" and "opMissing" in m for c, m in diags), \
        f"undefined task inside parallel() not caught: {diags}"
