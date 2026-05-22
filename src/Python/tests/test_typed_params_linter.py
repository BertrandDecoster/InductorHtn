"""Tests for TYP001 typed-parameters linter rule."""
import os
import sys

script_dir = os.path.dirname(os.path.abspath(__file__))
python_dir = os.path.dirname(script_dir)
backend_dir = os.path.abspath(os.path.join(python_dir, '../../gui/backend'))
sys.path.insert(0, backend_dir)
sys.path.insert(0, python_dir)

from htn_linter import HtnLinter, TypeRegistry


def test_empty_source_yields_empty_registry():
    reg = TypeRegistry.from_source("")
    assert reg.signatures == {}
    assert reg.types == {}


def test_extracts_type_facts():
    src = """
    type(agent, player).
    type(agent, gob1).
    type(cell, c5).
    """
    reg = TypeRegistry.from_source(src)
    assert reg.types == {
        'agent': {'player', 'gob1'},
        'cell': {'c5'},
    }


def test_extracts_signature_facts():
    src = """
    signature(moveTo, [agent, cell]).
    signature(applyTag, [agent, tag]).
    """
    reg = TypeRegistry.from_source(src)
    assert reg.signatures == {
        'moveTo/2': ['agent', 'cell'],
        'applyTag/2': ['agent', 'tag'],
    }


def test_type_lookup():
    src = "type(agent, player). type(cell, c5)."
    reg = TypeRegistry.from_source(src)
    assert reg.type_of('player') == {'agent'}
    assert reg.type_of('c5') == {'cell'}
    assert reg.type_of('unknown') == set()


def test_signature_arities():
    """Arity is derived from the type list, not hardcoded to 2."""
    src = """
    signature(noargs, []).
    signature(one, [agent]).
    signature(three, [agent, cell, tag]).
    """
    reg = TypeRegistry.from_source(src)
    assert reg.signatures == {
        'noargs/0': [],
        'one/1': ['agent'],
        'three/3': ['agent', 'cell', 'tag'],
    }


def test_instance_belongs_to_multiple_types():
    src = "type(agent, x). type(target, x)."
    reg = TypeRegistry.from_source(src)
    assert reg.type_of('x') == {'agent', 'target'}


def test_signature_with_variable_in_list_is_dropped():
    src = "signature(bad, [agent, ?Wat])."
    reg = TypeRegistry.from_source(src)
    assert reg.signatures == {}


def test_type_facts_with_body_are_excluded():
    """Rules with bodies are not facts; do not register as type declarations."""
    src = """
    type(agent, ?X) :- player(?X).
    player(p).
    """
    reg = TypeRegistry.from_source(src)
    assert reg.types == {}


def _diag_codes(diags):
    return [d.get('code') if isinstance(d, dict) else d.code for d in diags]


def test_typ001_clean_call_no_diagnostic():
    src = """
    type(agent, player).
    type(cell, c5).
    signature(moveTo, [agent, cell]).
    goalA :- if(), do(moveTo(player, c5)).
    """
    diags = HtnLinter(src).lint()
    assert 'TYP001' not in _diag_codes(diags)


def test_typ001_swapped_args_flagged():
    src = """
    type(agent, player).
    type(cell, c5).
    signature(moveTo, [agent, cell]).
    goalA :- if(), do(moveTo(c5, player)).
    """
    diags = HtnLinter(src).lint()
    typ_diags = [d for d in diags if (d.get('code') if isinstance(d, dict) else d.code) == 'TYP001']
    assert len(typ_diags) == 2  # both args wrong


def test_typ001_untyped_constant_flagged():
    src = """
    type(agent, player).
    type(cell, c5).
    signature(moveTo, [agent, cell]).
    goalA :- if(), do(moveTo(wat, c5)).
    """
    diags = HtnLinter(src).lint()
    assert 'TYP001' in _diag_codes(diags)


def test_typ001_variable_arg_skipped():
    src = """
    type(agent, player).
    type(cell, c5).
    signature(moveTo, [agent, cell]).
    move(?x, ?y) :- if(), do(moveTo(?x, ?y)).
    """
    diags = HtnLinter(src).lint()
    typ_diags = [d for d in diags if (d.get('code') if isinstance(d, dict) else d.code) == 'TYP001']
    assert typ_diags == []


def test_typ001_no_signature_no_diagnostic():
    src = """
    type(agent, player).
    type(cell, c5).
    goalA :- if(), do(moveTo(c5, player)).
    """
    # No signature(moveTo, ...) declared → rule does not engage
    diags = HtnLinter(src).lint()
    assert 'TYP001' not in _diag_codes(diags)


def test_typ001_fires_in_if_clause():
    src = """
    type(agent, player). type(cell, c5).
    signature(at, [agent, cell]).
    goal :- if(at(c5, player)), do().
    """
    diags = HtnLinter(src).lint()
    assert any((d.get('code') if isinstance(d, dict) else d.code) == 'TYP001' for d in diags)


def test_typ001_fires_in_operator_del():
    src = """
    type(agent, player). type(cell, c5).
    signature(at, [agent, cell]).
    op() :- del(at(c5, player)), add().
    """
    diags = HtnLinter(src).lint()
    assert any((d.get('code') if isinstance(d, dict) else d.code) == 'TYP001' for d in diags)


def test_typ001_fires_in_operator_add():
    src = """
    type(agent, player). type(cell, c5).
    signature(at, [agent, cell]).
    op() :- del(), add(at(c5, player)).
    """
    diags = HtnLinter(src).lint()
    assert any((d.get('code') if isinstance(d, dict) else d.code) == 'TYP001' for d in diags)


def test_typ001_mvp_skips_calls_inside_try():
    """MVP scope cut: calls inside try() are not recursed into."""
    src = """
    type(agent, player). type(cell, c5).
    signature(moveTo, [agent, cell]).
    goal :- if(), do(try(moveTo(c5, player))).
    """
    diags = HtnLinter(src).lint()
    typ_diags = [d for d in diags if (d.get('code') if isinstance(d, dict) else d.code) == 'TYP001']
    assert typ_diags == []


def test_typ001_diagnostic_points_at_argument():
    src = "type(agent, player).\ntype(cell, c5).\nsignature(moveTo, [agent, cell]).\ngoalA :- if(), do(moveTo(c5, player)).\n"
    typ_diags = [d for d in HtnLinter(src).lint() if (d.get('code') if isinstance(d, dict) else d.code) == 'TYP001']
    assert len(typ_diags) == 2
    # Pull out .line/.length whether dataclass or dict
    def _attr(d, name):
        return d.get(name) if isinstance(d, dict) else getattr(d, name)
    assert _attr(typ_diags[0], 'line') == 4
    assert _attr(typ_diags[0], 'length') == 2    # 'c5'
    assert _attr(typ_diags[1], 'length') == 6    # 'player'


if __name__ == '__main__':
    test_empty_source_yields_empty_registry()
    test_extracts_type_facts()
    test_extracts_signature_facts()
    test_type_lookup()
    test_signature_arities()
    test_instance_belongs_to_multiple_types()
    test_signature_with_variable_in_list_is_dropped()
    test_type_facts_with_body_are_excluded()
    test_typ001_clean_call_no_diagnostic()
    test_typ001_swapped_args_flagged()
    test_typ001_untyped_constant_flagged()
    test_typ001_variable_arg_skipped()
    test_typ001_no_signature_no_diagnostic()
    test_typ001_fires_in_if_clause()
    test_typ001_fires_in_operator_del()
    test_typ001_fires_in_operator_add()
    test_typ001_mvp_skips_calls_inside_try()
    test_typ001_diagnostic_points_at_argument()
    print("All TypeRegistry + TYP001 tests passed.")
