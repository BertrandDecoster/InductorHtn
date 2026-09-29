"""Tests for indhtn_quality.static_model — the parser-backed operator/method
template model the DAG tool grounds plan steps against.

Pure static analysis: no engine, no session. Uses the same gui/backend parser
as the linter (via the conftest sys.path setup mirrored in the module).
"""

from __future__ import annotations

import sys
from pathlib import Path

_HERE = Path(__file__).resolve()
_MCP_SERVER = _HERE.parents[1]
_REPO = _MCP_SERVER.parent
sys.path.insert(0, str(_MCP_SERVER))

from indhtn_quality.static_model import (  # noqa: E402
    build_static_model,
    ground_effects,
    match_ground_op,
    term_from_raw,
    term_to_str,
)

# A miniature of the fortress shapes: one static fact, one initial fluent,
# ops with empty del(), ops with both del and add, a method with a mixed
# static/fluent if(), and a second clause for the same method head.
_SOURCE = """
area(home).
area(cave).
connected(home, cave).
at(hero, home).

opMove(?actor, ?from, ?to) :- del(at(?actor, ?from)), add(at(?actor, ?to)).
opLight(?t) :- del(), add(lit(?t)).

goTo(?actor, ?area) :-
    if(at(?actor, ?loc), connected(?loc, ?area)),
    do(opMove(?actor, ?loc, ?area)).
goTo(?actor, ?area) :-
    if(at(?actor, ?loc), portal(?loc, ?area)),
    do(opJump(?actor, ?loc, ?area)).
"""


def test_op_templates_extracted():
    model = build_static_model(_SOURCE)
    assert ("opMove", 3) in model.ops
    assert ("opLight", 1) in model.ops
    move = model.ops[("opMove", 3)]
    assert [term_to_str(t) for t in move.dels] == ["at(?actor,?from)"]
    assert [term_to_str(t) for t in move.adds] == ["at(?actor,?to)"]
    light = model.ops[("opLight", 1)]
    assert light.dels == []
    assert [term_to_str(t) for t in light.adds] == ["lit(?t)"]


def test_fluent_predicates_are_union_of_del_add():
    model = build_static_model(_SOURCE)
    assert model.fluent_preds == {("at", 2), ("lit", 1)}


def test_method_clauses_extracted_in_order():
    model = build_static_model(_SOURCE)
    clauses = model.methods[("goTo", 2)]
    assert len(clauses) == 2
    first = clauses[0]
    assert [term_to_str(t) for t in first.if_literals] == [
        "at(?actor,?loc)",
        "connected(?loc,?area)",
    ]
    assert [term_to_str(t) for t in first.do_tasks] == ["opMove(?actor,?loc,?area)"]
    assert clauses[1].clause_index == 1


def test_term_from_raw_and_canonical_string():
    raw = {"opMove": [{"player": []}, {"fortress_entrance": []}, {"fortress_area1": []}]}
    term = term_from_raw(raw)
    assert term_to_str(term) == "opMove(player,fortress_entrance,fortress_area1)"


def test_match_and_ground_effects():
    model = build_static_model(_SOURCE)
    raw = {"opMove": [{"hero": []}, {"home": []}, {"cave": []}]}
    tmpl, bindings = match_ground_op(model, term_from_raw(raw))
    assert bindings == {"?actor": "hero", "?from": "home", "?to": "cave"}
    dels, adds = ground_effects(tmpl, bindings)
    assert dels == ["at(hero,home)"]
    assert adds == ["at(hero,cave)"]


def test_match_unknown_operator_returns_none():
    model = build_static_model(_SOURCE)
    assert match_ground_op(model, term_from_raw({"opWarp": [{"x": []}]})) is None
