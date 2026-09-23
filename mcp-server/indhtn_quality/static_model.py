"""Static operator/method templates extracted with the linter's parser.

The decomposition tree gives every plan step its emitting method clause and
ground bindings, but operator nodes carry only the head — del()/add() effects
live in the source. This module parses the source once (same gui/backend
parser the linter uses) and grounds effects by unifying a plan's raw operator
terms against the templates.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

# Same sys.path injection as indhtn_mcp/server.py: the parser lives in
# gui/backend and is not a package.
_REPO_ROOT = Path(__file__).resolve().parents[2]
_GUI_BACKEND = str(_REPO_ROOT / "gui" / "backend")
if _GUI_BACKEND not in sys.path:
    sys.path.insert(0, _GUI_BACKEND)

from htn_parser import Term, parse_htn  # type: ignore  # noqa: E402


@dataclass
class OpTemplate:
    name: str
    arity: int
    params: List[Term]
    dels: List[Term]
    adds: List[Term]
    line: int


@dataclass
class MethodClause:
    name: str
    arity: int
    clause_index: int
    params: List[Term]
    if_literals: List[Term]
    do_tasks: List[Term]
    line: int


@dataclass
class StaticModel:
    ops: Dict[Tuple[str, int], OpTemplate] = field(default_factory=dict)
    methods: Dict[Tuple[str, int], List[MethodClause]] = field(default_factory=dict)
    # Predicates that appear in any operator del()/add(): the mutable state.
    fluent_preds: Set[Tuple[str, int]] = field(default_factory=set)


def _clause_args(clause: Optional[Term]) -> List[Term]:
    return list(clause.args) if clause is not None else []


def build_static_model(source: str) -> StaticModel:
    rules, _errors = parse_htn(source)
    model = StaticModel()
    for rule in rules:
        key = (rule.head.name, len(rule.head.args))
        if rule.is_operator:
            dels = _clause_args(rule.del_clause)
            adds = _clause_args(rule.add_clause)
            model.ops[key] = OpTemplate(
                name=key[0], arity=key[1], params=list(rule.head.args),
                dels=dels, adds=adds, line=rule.line,
            )
            for eff in dels + adds:
                model.fluent_preds.add((eff.name, len(eff.args)))
        elif rule.is_method:
            clauses = model.methods.setdefault(key, [])
            clauses.append(MethodClause(
                name=key[0], arity=key[1], clause_index=len(clauses),
                params=list(rule.head.args),
                if_literals=_clause_args(rule.if_clause),
                do_tasks=_clause_args(rule.do_clause),
                line=rule.line,
            ))
    return model


def term_from_raw(raw: dict) -> Term:
    """Convert one operatorsRaw entry ({"opMove": [{"player": []}, ...]}) to a Term."""
    (name, args), = raw.items()
    return Term(name=name, args=[term_from_raw(a) for a in args])


def term_to_str(term: Term) -> str:
    """Canonical rendering: no spaces, matches the tree's taskName format."""
    if term.is_list:
        return "[" + ",".join(term_to_str(a) for a in term.args) + "]"
    if not term.args:
        return term.name
    return term.name + "(" + ",".join(term_to_str(a) for a in term.args) + ")"


def _is_var(term: Term) -> bool:
    return term.is_variable or term.name.startswith("?")


def match_ground_op(model: StaticModel, ground: Term) -> Optional[Tuple[OpTemplate, Dict[str, str]]]:
    """Unify a ground operator term against its template head.

    Operator heads in this dialect are flat variable tuples, so matching is a
    positional bind. Returns None for unknown operators (e.g. beginParallel).
    """
    tmpl = model.ops.get((ground.name, len(ground.args)))
    if tmpl is None:
        return None
    bindings: Dict[str, str] = {}
    for param, actual in zip(tmpl.params, ground.args):
        if _is_var(param):
            bindings[param.name] = term_to_str(actual)
        elif term_to_str(param) != term_to_str(actual):
            return None
    return tmpl, bindings


def substitute(term: Term, bindings: Dict[str, str]) -> str:
    """Render a template term with variables replaced by their bindings.

    Unbound variables render as-is (?name), letting callers detect
    partially-ground literals.
    """
    if _is_var(term):
        return bindings.get(term.name, term.name)
    if not term.args:
        return term.name
    return term.name + "(" + ",".join(substitute(a, bindings) for a in term.args) + ")"


def ground_effects(tmpl: OpTemplate, bindings: Dict[str, str]) -> Tuple[List[str], List[str]]:
    dels = [substitute(t, bindings) for t in tmpl.dels]
    adds = [substitute(t, bindings) for t in tmpl.adds]
    return dels, adds
