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


if __name__ == '__main__':
    test_empty_source_yields_empty_registry()
    test_extracts_type_facts()
    test_extracts_signature_facts()
    test_type_lookup()
    print("All TypeRegistry tests passed.")
