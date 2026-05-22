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


if __name__ == '__main__':
    test_empty_source_yields_empty_registry()
    test_extracts_type_facts()
    test_extracts_signature_facts()
    test_type_lookup()
    test_signature_arities()
    test_instance_belongs_to_multiple_types()
    test_signature_with_variable_in_list_is_dropped()
    test_type_facts_with_body_are_excluded()
    print("All TypeRegistry tests passed.")
