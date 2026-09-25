"""The linter's built-in list must match what the C++ engine registers.

An unknown predicate is silently false in InductorHTN, so a linter that accepts an
SWI-Prolog built-in the engine lacks hides a bug, and one that rejects a real engine
built-in cries wolf.
"""

import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(ROOT, "gui", "backend"))

from htn_linter import BUILTIN_PREDICATES, SWI_ONLY_PREDICATES, lint_htn  # noqa: E402


def engine_builtins():
    src = open(os.path.join(ROOT, "src", "FXPlatform", "Prolog", "HtnGoalResolver.cpp"),
               encoding="utf-8").read()
    names = re.findall(r'AddCustomRule\("((?:[^"\\]|\\.)+)"', src)
    return {n.replace("\\\\", "\\") for n in names}


def linter_names():
    return {key.rsplit("/", 1)[0] for key in BUILTIN_PREDICATES}


def test_every_engine_builtin_is_known_to_the_linter():
    missing = engine_builtins() - linter_names()
    assert not missing, f"engine built-ins the linter would flag as undefined: {sorted(missing)}"


def test_the_linter_accepts_nothing_the_engine_lacks():
    extra = linter_names() - engine_builtins() - {"true", "!", "<", ">", "=<", ">="}
    assert not extra, f"linter accepts built-ins the engine does not have: {sorted(extra)}"


def test_swi_only_names_are_not_engine_builtins():
    clash = set(SWI_ONLY_PREDICATES) & engine_builtins()
    assert not clash, f"listed as SWI-only but the engine has them: {sorted(clash)}"


def _codes(source):
    return [(d["code"], d["severity"]) for d in lint_htn(source)]


def test_swi_builtins_in_a_condition_are_errors():
    source = ("item(a). item(b).\n"
              "pick :- if(item(?x), member(?x, [a, b]), \\+(bad(?x))), do(take(?x)).\n"
              "take(?x) :- del(), add(has(?x)).\n")
    codes = _codes(source)
    assert codes.count(("SEM008", "error")) == 2, codes


def test_engine_builtins_are_not_flagged():
    source = ("linked(a, b). linked(b, a). at(me, a).\n"
              "go(?to) :- if(at(me, ?here), pathNext(?here, ?to, ?next), count(?n, linked(?x, ?y)),\n"
              "              sum(?s, ?n, linked(?x, ?y)), \\==(?here, ?to)), do(step(?here, ?next)).\n"
              "step(?a, ?b) :- del(at(me, ?a)), add(at(me, ?b)).\n")
    flagged = [d for d in lint_htn(source) if d["code"] in ("SEM002", "SEM008")
               and any(b in d["message"] for b in ("pathNext", "count", "sum", "\\=="))]
    assert not flagged, flagged
