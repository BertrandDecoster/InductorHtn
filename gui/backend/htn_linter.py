"""
HTN Linter - Syntax and Semantic Checks
Analyzes parsed HTN rules for common errors and warnings.
"""

import re
from typing import List, Dict, Set, Optional, Tuple
from dataclasses import dataclass, field
from collections import defaultdict

from htn_parser import parse_htn, Rule, Term, Diagnostic


# Authoritative list of Prolog/HTN built-in predicates.
# Used by the linter's undefined-predicate check and by the component-system
# contract auto-inference. When adding a new built-in to InductorHTN, update
# this set (there is no other source of truth in the Python tooling).
BUILTIN_PREDICATES = {
    # Control flow
    'true/0', 'fail/0', 'false/0', '!/0',

    # Comparison operators
    '=/2', '\\=/2', '==/2', '\\==/2',
    '</2', '>/2', '=</2', '>=/2', '=:=/2', '=\\=/2',

    # Arithmetic
    'is/2', '+/2', '-/2', '*/2', '//2', 'mod/2',
    '+/1', '-/1',  # unary

    # Negation
    'not/1', '\\+/1',

    # Meta-predicates
    'call/1', 'call/2', 'call/3',
    'findall/3', 'bagof/3', 'setof/3',
    'forall/2',

    # Type checking
    'atom/1', 'number/1', 'atomic/1', 'compound/1',
    'var/1', 'nonvar/1', 'is_list/1', 'integer/1', 'float/1',

    # Database (assert/retract)
    'assert/1', 'retract/1', 'retractall/1', 'abolish/1',

    # String manipulation
    'atom_chars/2', 'atom_concat/3', 'downcase_atom/2',
    'upcase_atom/2', 'atom_length/2', 'atom_string/2',
    'char_code/2', 'number_chars/2', 'number_codes/2',

    # HTN-specific built-ins from InductorHTN
    'count/2',      # count(?count, goal) - count solutions
    'distinct/3',   # distinct(_, term1, term2) - distinct pairs
    'and/1', 'and/2', 'and/3', 'and/4', 'and/5',  # and(goals...) - conjunction as single term
    'first/1', 'first/2', 'first/3', 'first/4', 'first/5',  # first(goals...) - get first solution only
    'sortBy/3',     # sortBy(?sorted, ?key, term) - sort results

    # List operations
    'append/3', 'member/2', 'length/2', 'nth0/3', 'nth1/3',
    'reverse/2', 'sort/2', 'msort/2', 'last/2',

    # Printing (for debugging)
    'write/1', 'writeln/1', 'print/1', 'nl/0',

    # Misc
    'copy_term/2', 'ground/1', 'functor/3', 'arg/3',
    '=../2',  # univ
}


@dataclass
class SymbolInfo:
    """Information about a symbol (method, operator, predicate)"""
    name: str
    arity: int
    line: int
    col: int = 0
    is_method: bool = False
    is_operator: bool = False
    is_fact: bool = False
    callers: List[str] = field(default_factory=list)


def _is_numeric_literal(name: str) -> bool:
    """True if name parses as a number (handles ints, floats, negatives).

    Numeric literals never carry a sort, so they are never type-checked."""
    if not name:
        return False
    try:
        float(name)
        return True
    except (ValueError, TypeError):
        return False


def _is_plain_constant(term: Term) -> bool:
    """A bare atom/constant: not a variable, not a compound, not a list."""
    return (not term.is_variable) and (not term.args) and (not term.is_list)


# Fact predicates that are NOT type declarations even at arity 1.
_NON_TYPE_FACT_PREDICATES = {'goals'}

# Term names that wrap goals rather than being calls themselves. Type
# inference and flagging descend THROUGH these to reach the real calls.
_GOAL_WRAPPERS = {
    'try', 'first', 'and', 'parallel', 'forall',
    'else', 'anyOf', 'allOf', 'not', '\\+',
}


def _is_builtin_call(name: str, arity: int) -> bool:
    """True if name/arity is a Prolog/HTN built-in (skipped by inference)."""
    return f"{name}/{arity}" in BUILTIN_PREDICATES


@dataclass
class TypeInference:
    """Whole-program type inference for the HTN linter.

    Types come from unary ground facts: `skill(frostNova).` means
    `frostNova : skill`. A constant carries the SET of every unary-fact
    predicate it appears under. Predicate-argument positions get inferred
    type sets to a fixpoint (see `run_fixpoint`); arguments are later flagged
    only when provably disjoint from a well-determined position type.
    """
    # constant -> set of types (unary-fact predicate names)
    const_types: Dict[str, Set[str]] = field(default_factory=lambda: defaultdict(set))
    # the universe of type names == unary-fact predicate names (the sorts)
    type_universe: Set[str] = field(default_factory=set)
    # sort -> every sort that co-occurs with it on some instance (incl. itself).
    # Two sorts are "compatible" (not disjoint) if any constant has both, so
    # `agent`+`enemy` are compatible when some instance is both an agent and an
    # enemy, even though the names differ.
    cooccur: Dict[str, Set[str]] = field(default_factory=lambda: defaultdict(set))
    # (pred/arity, position-index) -> inferred type set. Empty = unknown.
    pos_types: Dict[Tuple[str, int], Set[str]] = field(default_factory=dict)
    # anchors from signature/2 facts and %:: directives: position -> type set
    overrides: Dict[Tuple[str, int], Set[str]] = field(default_factory=dict)
    # %:: directive head-var bindings: id(rule) -> {varname -> type set}
    directive_var_types: Dict[int, Dict[str, Set[str]]] = field(default_factory=dict)
    # final per-position contributor type-sets (for leave-one-out flagging)
    contributors: Dict[Tuple[str, int], List[Set[str]]] = field(default_factory=dict)

    MAX_ITERS = 10

    @classmethod
    def from_source(cls, source: str) -> 'TypeInference':
        rules, _ = parse_htn(source)
        return cls.from_rules(rules)

    @classmethod
    def from_rules(cls, rules: List[Rule], overrides: Optional[Dict] = None,
                   directive_var_types: Optional[Dict] = None) -> 'TypeInference':
        ti = cls()
        if overrides:
            ti.overrides = dict(overrides)
        if directive_var_types:
            ti.directive_var_types = dict(directive_var_types)
        ti._seed_from_facts(rules)
        ti._build_cooccurrence()
        ti.run_fixpoint(rules)
        return ti

    def _build_cooccurrence(self) -> None:
        for sorts in self.const_types.values():
            for a in sorts:
                self.cooccur[a].update(sorts)

    def sorts_disjoint(self, a: Set[str], b: Set[str]) -> bool:
        """True iff NO sort in `a` is compatible with any sort in `b` — i.e.
        no instance is ever known to be both. Subsumes set-intersection
        (a shared sort co-occurs with itself)."""
        for s in a:
            if self.cooccur.get(s, {s}) & b:
                return False
        return True

    def _seed_from_facts(self, rules: List[Rule]) -> None:
        """Phase A: every unary ground fact `T(c).` declares `c : T` — EXCEPT
        unary predicates that operators add/delete, which are transient state
        (e.g. `at/1` in `del(at(?h)), add(at(?t))`), not a stable sort."""
        mutable = self._mutable_unary_predicates(rules)
        for rule in rules:
            if rule.body:
                continue
            head = rule.head
            if head.name in _NON_TYPE_FACT_PREDICATES or head.name in mutable:
                continue
            if len(head.args) != 1:
                continue
            arg = head.args[0]
            if not _is_plain_constant(arg) or _is_numeric_literal(arg.name):
                continue
            self.type_universe.add(head.name)
            self.const_types[arg.name].add(head.name)

    @staticmethod
    def _mutable_unary_predicates(rules: List[Rule]) -> Set[str]:
        """Names of unary predicates that appear in any operator's del()/add()
        (directly or inside increase/decrease) — i.e. state, not a sort."""
        mut: Set[str] = set()

        def scan(term: Term) -> None:
            if term.is_variable or term.is_list:
                return
            if term.name in ('increase', 'decrease') and term.args:
                scan(term.args[0])
                return
            if len(term.args) == 1:
                mut.add(term.name)

        for rule in rules:
            for clause in (rule.del_clause, rule.add_clause):
                if clause:
                    for t in clause.args:
                        scan(t)
        return mut

    # --- goal collection (recurses through wrappers) --------------------

    def _iter_goal_terms(self, term: Term):
        """Yield real call terms, descending through goal wrappers."""
        if term.is_variable or term.is_list:
            return
        if term.name in _GOAL_WRAPPERS:
            for a in term.args:
                yield from self._iter_goal_terms(a)
            return
        yield term

    def _clause_top_terms(self, rule: Rule) -> List[Term]:
        """The top-level terms of a rule's clauses (if/do/del/add or body),
        before wrapper unwrapping."""
        out: List[Term] = []
        if rule.is_method:
            if rule.if_clause:
                out += rule.if_clause.args
            if rule.do_clause:
                out += rule.do_clause.args
        elif rule.is_operator:
            if rule.del_clause:
                out += rule.del_clause.args
            if rule.add_clause:
                out += rule.add_clause.args
        else:
            out += rule.body or []
        return out

    def _collect_goal_terms(self, rule: Rule) -> List[Term]:
        out: List[Term] = []
        for term in self._clause_top_terms(rule):
            out.extend(self._iter_goal_terms(term))
        return out

    def _guard_clause_terms(self, rule: Rule) -> List[Term]:
        """Terms that act as preconditions: a method's `if`, a plain rule's
        body. Operators have no preconditions (their `del`/`add` are effects)."""
        if rule.is_method:
            return rule.if_clause.args if rule.if_clause else []
        if rule.is_operator:
            return []
        return rule.body or []

    def positive_unary_guards(self, rule: Rule) -> Dict[str, Set[str]]:
        """Map each variable to the unary type-predicates that DEFINITELY guard
        it in the precondition — `enemy(?e)` gives `?e: {enemy}`. Only direct
        conjuncts count: we descend plain `and(...)` but not `not`/`try`/
        `first`/`forall`/etc., where a goal is negated, optional, or binds a
        quantifier-local variable rather than the head's. Only sorts (in
        `type_universe`) count. This is the basis for treating a rule head
        parameter as an authored type contract."""
        guards: Dict[str, Set[str]] = defaultdict(set)

        def walk(term: Term) -> None:
            if term.is_variable or term.is_list:
                return
            if term.name == 'and':  # plain conjunction preserves the binding
                for a in term.args:
                    walk(a)
                return
            if (len(term.args) == 1 and term.name in self.type_universe
                    and term.args[0].is_variable):
                guards[term.args[0].name].add(term.name)

        for term in self._guard_clause_terms(rule):
            walk(term)
        return guards

    # --- fixpoint -------------------------------------------------------

    @staticmethod
    def _fold_var(acc: Optional[Set[str]], t: Set[str]) -> Optional[Set[str]]:
        """Fold a variable's type across the positions it occupies: genuine
        intersection, but an unknown (empty) position contributes nothing."""
        if not t:
            return acc
        if acc is None:
            return set(t)
        return acc & t

    def _pos_type(self, pos: Tuple[str, int]) -> Set[str]:
        """Purely inferred type of a position. Overrides deliberately do NOT
        participate in propagation — they would flow backward through a wrong
        argument and erase the very conflict we want to flag. Overrides are
        applied only as the authoritative EXPECTED type at flagging time."""
        return self.pos_types.get(pos, set())

    def _arg_type(self, arg: Term, var_types: Dict[str, Optional[Set[str]]]) -> Set[str]:
        """The inferred type set of a single argument occurrence."""
        if arg.is_variable:
            return var_types.get(arg.name) or set()
        if _is_plain_constant(arg) and not _is_numeric_literal(arg.name):
            return self.const_types.get(arg.name, set())
        return set()

    def _pass1_var_types(self, rule: Rule):
        """Type each variable in `rule` by folding the positions it occupies
        (genuine intersection, unknown positions skipped). Returns the var
        map and the term list (head + goals) so callers avoid recomputing."""
        var_types: Dict[str, Optional[Set[str]]] = {}
        for v, t in self.directive_var_types.get(id(rule), {}).items():
            var_types[v] = set(t)
        terms = [rule.head] + self._collect_goal_terms(rule)
        for term in terms:
            arity = len(term.args)
            if _is_builtin_call(term.name, arity):
                continue
            key = f"{term.name}/{arity}"
            for i, arg in enumerate(term.args):
                if arg.is_variable:
                    var_types[arg.name] = self._fold_var(
                        var_types.get(arg.name), self._pos_type((key, i)))
        return var_types, terms

    def _recompute_positions(self, contributors):
        """A position's type is the shared core (intersection) of its
        contributors when one exists, else their union (a polymorphic
        position; the union keeps propagation permissive)."""
        new_pos: Dict[Tuple[str, int], Set[str]] = {}
        for pos, sets in contributors.items():
            core = set.intersection(*sets)
            new_pos[pos] = core if core else set().union(*sets)
        return new_pos

    def run_fixpoint(self, rules: List[Rule]) -> None:
        for _ in range(self.MAX_ITERS):
            contributors: Dict[Tuple[str, int], List[Set[str]]] = defaultdict(list)
            for rule in rules:
                var_types, terms = self._pass1_var_types(rule)
                for term in terms:
                    arity = len(term.args)
                    if _is_builtin_call(term.name, arity):
                        continue
                    key = f"{term.name}/{arity}"
                    for i, arg in enumerate(term.args):
                        c = self._arg_type(arg, var_types)
                        if c:
                            contributors[(key, i)].append(set(c))

            new_pos = self._recompute_positions(contributors)
            self.contributors = contributors
            if new_pos == self.pos_types:
                break
            self.pos_types = new_pos


class HtnLinter:
    """Linter for HTN/Prolog files"""

    def __init__(self, source: str, external_signatures: Optional[Set[str]] = None):
        """
        Args:
            source: HTN source text.
            external_signatures: Optional set of `name/arity` strings defined
                outside this source but available at load time (e.g. provided
                by a declared dependency, or listed in the manifest's
                `requires` contract). Such signatures are NOT flagged as
                undefined.
        """
        self.source = source
        self.external_signatures: Set[str] = set(external_signatures or ())
        self.rules: List[Rule] = []
        self.diagnostics: List[Diagnostic] = []

        # Symbol tables
        self.methods: Dict[str, List[SymbolInfo]] = defaultdict(list)
        self.operators: Dict[str, List[SymbolInfo]] = defaultdict(list)
        self.facts: Dict[str, List[SymbolInfo]] = defaultdict(list)
        self.predicates: Dict[str, List[SymbolInfo]] = defaultdict(list)

        # Call graph
        self.calls: Dict[str, Set[str]] = defaultdict(set)  # caller -> callees
        self.called_by: Dict[str, Set[str]] = defaultdict(set)  # callee -> callers

        # Goals
        self.goals: List[Term] = []

    def lint(self) -> List[Diagnostic]:
        """Run all lint checks and return diagnostics"""
        # Parse
        self.rules, parse_errors = parse_htn(self.source)
        self.diagnostics.extend(parse_errors)

        # Build symbol tables
        self._build_symbol_tables()

        # Run checks
        self._check_variable_binding()
        self._check_htn_syntax()
        self._check_undefined_references()
        self._check_arity_consistency()
        self._check_duplicate_definitions()
        self._check_dead_code()
        self._check_cycles()
        self._check_else_usage()
        self._check_empty_clauses()
        self._check_singleton_variables()
        self._check_type_inference()

        return self.diagnostics

    def _build_symbol_tables(self):
        """Build symbol tables from parsed rules"""
        for rule in self.rules:
            head_name = rule.head.name
            head_arity = len(rule.head.args)
            key = f"{head_name}/{head_arity}"

            info = SymbolInfo(
                name=head_name,
                arity=head_arity,
                line=rule.line,
                is_method=rule.is_method,
                is_operator=rule.is_operator,
                is_fact=rule.is_fact
            )

            if rule.is_method:
                self.methods[key].append(info)
            elif rule.is_operator:
                self.operators[key].append(info)
            elif rule.is_fact:
                self.facts[key].append(info)
            else:
                # Pure Prolog rule
                self.predicates[key].append(info)

            # Extract goals
            if head_name == 'goals':
                for arg in rule.head.args:
                    self.goals.append(arg)

            # Build call graph from do() clause
            if rule.do_clause:
                for task in rule.do_clause.args:
                    self._add_call(key, task)

            # Also track predicates used in if() conditions
            if rule.if_clause:
                for cond in rule.if_clause.args:
                    self._track_predicate_usage(key, cond)

    def _get_fact_atoms(self) -> Set[str]:
        """
        Get atoms used as arguments in facts.

        For example, in "at(person, downtown).", this returns {"person/0", "downtown/0"}
        so they won't be flagged as undefined when used as predicates.
        """
        atoms: Set[str] = set()

        def collect_atoms(term: Term):
            if term.is_variable:
                return
            # If this term has no arguments and isn't a variable, it's an atom
            if len(term.args) == 0:
                atoms.add(f"{term.name}/0")
            # Recurse into arguments
            for arg in term.args:
                collect_atoms(arg)

        # Collect from all facts
        for rule in self.rules:
            if rule.is_fact:
                for arg in rule.head.args:
                    collect_atoms(arg)

        return atoms

    def _add_call(self, caller: str, task: Term):
        """Add a call relationship to the call graph"""
        # Handle try()/parallel() and other wrappers: the wrapped tasks are
        # the real callees (parallel is an engine keyword, not a task).
        if task.name in ('try', 'first', 'and', 'parallel'):
            for arg in task.args:
                self._add_call(caller, arg)
            return

        callee = f"{task.name}/{len(task.args)}"
        self.calls[caller].add(callee)
        self.called_by[callee].add(caller)

    def _track_predicate_usage(self, caller: str, term: Term):
        """Track predicate usage in conditions"""
        if term.is_variable:
            return

        key = f"{term.name}/{len(term.args)}"
        self.called_by[key].add(caller)

        # Recurse into nested terms
        for arg in term.args:
            self._track_predicate_usage(caller, arg)

    def _check_variable_binding(self):
        """Check that variables are properly bound"""
        for rule in self.rules:
            if not rule.is_method:
                continue

            # Get variables from head and if clause
            head_vars = rule.head.get_variables()
            if_vars = rule.if_clause.get_variables() if rule.if_clause else set()
            bound_vars = head_vars | if_vars

            # Check variables in do clause
            if rule.do_clause:
                for task in rule.do_clause.args:
                    do_vars = task.get_variables()
                    unbound = do_vars - bound_vars
                    for var in unbound:
                        self.diagnostics.append(Diagnostic(
                            task.line, task.col, len(var), 'error',
                            f"Variable '{var}' in do() is not bound in head or if()",
                            'VAR001'
                        ))

        # Check operators
        for rule in self.rules:
            if not rule.is_operator:
                continue

            head_vars = rule.head.get_variables()

            # del() variables should generally exist (could be bound by head)
            # add() variables must be bound somewhere

            if rule.add_clause:
                add_vars = rule.add_clause.get_variables()
                unbound = add_vars - head_vars
                if rule.del_clause:
                    del_vars = rule.del_clause.get_variables()
                    unbound = unbound - del_vars

                for var in unbound:
                    self.diagnostics.append(Diagnostic(
                        rule.add_clause.line, rule.add_clause.col, len(var), 'error',
                        f"Variable '{var}' in add() is not bound",
                        'VAR002'
                    ))

    def _check_htn_syntax(self):
        """Check for HTN-specific syntax issues"""
        for rule in self.rules:
            # Method should have if() and do()
            if rule.is_method:
                # Check for operator syntax in method
                if rule.del_clause or rule.add_clause:
                    self.diagnostics.append(Diagnostic(
                        rule.line, 1, 10, 'error',
                        f"Method '{rule.head.name}' uses operator syntax (del/add). Use if/do instead.",
                        'HTN001'
                    ))

            # Operator should have del() or add(), not if/do
            if rule.is_operator:
                if rule.if_clause or rule.do_clause:
                    self.diagnostics.append(Diagnostic(
                        rule.line, 1, 10, 'error',
                        f"Operator '{rule.head.name}' uses method syntax (if/do). Use del/add instead.",
                        'HTN002'
                    ))

            # allOf/anyOf only make sense on methods
            if rule.is_operator and (rule.has_allof or rule.has_anyof):
                modifier = 'allOf' if rule.has_allof else 'anyOf'
                self.diagnostics.append(Diagnostic(
                    rule.line, 1, 10, 'warning',
                    f"'{modifier}' modifier on operator '{rule.head.name}' has no effect",
                    'HTN003'
                ))

    def _check_undefined_references(self):
        """Check for calls to undefined methods/operators"""
        all_defined = set()
        all_defined.update(self.methods.keys())
        all_defined.update(self.operators.keys())
        all_defined.update(self.facts.keys())
        all_defined.update(self.predicates.keys())

        all_defined.update(BUILTIN_PREDICATES)
        all_defined.update(self.external_signatures)

        # Also add atoms that appear as arguments in facts
        # (e.g., "person" in "at(person, downtown)" should be recognized)
        all_defined.update(self._get_fact_atoms())

        for rule in self.rules:
            if rule.do_clause:
                for task in rule.do_clause.args:
                    self._check_task_defined(task, all_defined)

            if rule.if_clause:
                for cond in rule.if_clause.args:
                    self._check_predicate_defined(cond, all_defined, rule)

    def _check_task_defined(self, task: Term, defined: Set[str]):
        """Check if a task is defined"""
        if task.name in ('try', 'first', 'and', 'parallel'):
            for arg in task.args:
                self._check_task_defined(arg, defined)
            return

        if task.is_variable:
            return

        key = f"{task.name}/{len(task.args)}"
        if key not in defined:
            self.diagnostics.append(Diagnostic(
                task.line, task.col, len(task.name), 'error',
                f"Undefined method or operator: {task.name}/{len(task.args)}",
                'SEM001'
            ))

    def _check_predicate_defined(self, pred: Term, defined: Set[str], rule: Rule):
        """Check if a predicate is defined"""
        if pred.is_variable:
            return

        # Skip comparison operators and arithmetic
        if pred.name in ('=', '\\=', '==', '\\==', '<', '>', '=<', '>=', '=:=', '=\\=',
                         'is', '+', '-', '*', '/', 'mod', 'not', '\\+'):
            for arg in pred.args:
                self._check_predicate_defined(arg, defined, rule)
            return

        key = f"{pred.name}/{len(pred.args)}"
        if key not in defined:
            self.diagnostics.append(Diagnostic(
                pred.line, pred.col, len(pred.name), 'warning',
                f"Undefined predicate: {pred.name}/{len(pred.args)}",
                'SEM002'
            ))

        for arg in pred.args:
            self._check_predicate_defined(arg, defined, rule)

    def _check_arity_consistency(self):
        """Check for arity mismatches in predicate usage"""
        # Group by name only - include all usages
        by_name: Dict[str, Set[int]] = defaultdict(set)
        usage_locations: Dict[str, List[Tuple[int, int]]] = defaultdict(list)  # name -> [(line, arity)]

        # Collect from definitions
        for key in self.methods:
            name, arity = key.rsplit('/', 1)
            by_name[name].add(int(arity))

        for key in self.operators:
            name, arity = key.rsplit('/', 1)
            by_name[name].add(int(arity))

        for key in self.predicates:
            name, arity = key.rsplit('/', 1)
            by_name[name].add(int(arity))

        for key in self.facts:
            name, arity = key.rsplit('/', 1)
            by_name[name].add(int(arity))

        # Collect from usages in if/del/add clauses
        for rule in self.rules:
            if rule.if_clause:
                self._collect_term_arities(rule.if_clause, by_name, usage_locations)
            if rule.del_clause:
                self._collect_term_arities(rule.del_clause, by_name, usage_locations)
            if rule.add_clause:
                self._collect_term_arities(rule.add_clause, by_name, usage_locations)

        # Check for multiple arities
        for name, arities in by_name.items():
            if len(arities) > 1:
                arities_str = ', '.join(str(a) for a in sorted(arities))
                # Find first occurrence
                for rule in self.rules:
                    if rule.head.name == name:
                        self.diagnostics.append(Diagnostic(
                            rule.line, 1, len(name), 'warning',
                            f"'{name}' used with multiple arities: {arities_str}",
                            'SEM003'
                        ))
                        break

    def _collect_term_arities(self, term: Term, by_name: Dict[str, Set[int]],
                              locations: Dict[str, List[Tuple[int, int]]]):
        """Recursively collect term arities from a term tree"""
        if term.is_variable:
            return
        if term.name not in ('=', '\\=', '==', '\\==', '<', '>', '=<', '>=',
                             'is', '+', '-', '*', '/', 'mod', 'not', '\\+'):
            by_name[term.name].add(len(term.args))
            locations[term.name].append((term.line, len(term.args)))
        for arg in term.args:
            self._collect_term_arities(arg, by_name, locations)

    def _check_duplicate_definitions(self):
        """Check for duplicate operator definitions"""
        # Operators with same signature defined multiple times
        for key, infos in self.operators.items():
            if len(infos) > 1:
                name = infos[0].name
                lines = [str(info.line) for info in infos]
                # Report on second and subsequent definitions
                for info in infos[1:]:
                    self.diagnostics.append(Diagnostic(
                        info.line, 1, len(name), 'warning',
                        f"Duplicate operator '{name}/{infos[0].arity}' (also defined on line {infos[0].line})",
                        'SEM007'
                    ))

    def _check_dead_code(self):
        """Check for unreachable methods/operators"""
        # Build set of all called methods/operators
        all_called: Set[str] = set()
        for callees in self.calls.values():
            all_called.update(callees)

        if self.goals:
            # If we have goals, do full reachability analysis
            reachable: Set[str] = set()
            worklist: List[str] = []

            for goal in self.goals:
                key = f"{goal.name}/{len(goal.args)}"
                worklist.append(key)

            while worklist:
                current = worklist.pop()
                if current in reachable:
                    continue
                reachable.add(current)

                # Add callees
                for callee in self.calls.get(current, []):
                    if callee not in reachable:
                        worklist.append(callee)

            # Check for unreachable
            for key, infos in self.methods.items():
                if key not in reachable and infos:
                    info = infos[0]
                    self.diagnostics.append(Diagnostic(
                        info.line, 1, len(info.name), 'warning',
                        f"Method '{info.name}' is never called (dead code)",
                        'SEM004'
                    ))

            for key, infos in self.operators.items():
                if key not in reachable and infos:
                    info = infos[0]
                    self.diagnostics.append(Diagnostic(
                        info.line, 1, len(info.name), 'warning',
                        f"Operator '{info.name}' is never called (dead code)",
                        'SEM005'
                    ))
        else:
            # Without goals, check for operators never called by any method
            for key, infos in self.operators.items():
                if key not in all_called and infos:
                    info = infos[0]
                    self.diagnostics.append(Diagnostic(
                        info.line, 1, len(info.name), 'warning',
                        f"Operator '{info.name}' is never called by any method (dead code)",
                        'SEM005'
                    ))

            # Also check for methods never called by any other method
            for key, infos in self.methods.items():
                if key not in all_called and infos:
                    info = infos[0]
                    self.diagnostics.append(Diagnostic(
                        info.line, 1, len(info.name), 'warning',
                        f"Method '{info.name}' is never called (dead code)",
                        'SEM004'
                    ))

    def _check_cycles(self):
        """Check for cycles in the call graph (potential infinite recursion)"""
        visited: Set[str] = set()
        rec_stack: Set[str] = set()
        cycles_found: Set[str] = set()

        def dfs(node: str, path: List[str]) -> bool:
            # try/finally guarantees rec_stack/path are popped on every exit;
            # earlier versions skipped cleanup on the early return after
            # recording a cycle, leaking stale rec_stack entries that produced
            # spurious cycle reports on later DFS roots.
            visited.add(node)
            rec_stack.add(node)
            path.append(node)
            try:
                for callee in self.calls.get(node, []):
                    if callee not in visited:
                        if dfs(callee, path):
                            return True
                    elif callee in rec_stack:
                        cycle_start = path.index(callee)
                        cycle = path[cycle_start:]
                        cycle_key = '->'.join(sorted(cycle))
                        if cycle_key not in cycles_found:
                            cycles_found.add(cycle_key)
                            # Report on first node in cycle
                            name = callee.split('/')[0]
                            for rule in self.rules:
                                if rule.head.name == name:
                                    cycle_names = [c.split('/')[0] for c in cycle]
                                    self.diagnostics.append(Diagnostic(
                                        rule.line, 1, len(name), 'warning',
                                        f"Potential infinite recursion: {' -> '.join(cycle_names)} -> {name}",
                                        'SEM006'
                                    ))
                                    break
                        return False
                return False
            finally:
                path.pop()
                rec_stack.remove(node)

        for node in self.calls:
            if node not in visited:
                dfs(node, [])

    def _check_else_usage(self):
        """Check for proper else usage"""
        # Group methods by name/arity
        method_groups: Dict[str, List[Tuple[int, Rule]]] = defaultdict(list)

        for i, rule in enumerate(self.rules):
            if rule.is_method:
                key = f"{rule.head.name}/{len(rule.head.args)}"
                method_groups[key].append((i, rule))

        for key, methods in method_groups.items():
            if len(methods) == 1:
                rule = methods[0][1]
                if rule.has_else:
                    self.diagnostics.append(Diagnostic(
                        rule.line, 1, 10, 'error',
                        f"'else' on first/only method '{rule.head.name}' - nothing to be else to",
                        'HTN004'
                    ))
            else:
                # Check that else methods come after non-else methods
                first_idx, first_rule = methods[0]
                if first_rule.has_else:
                    self.diagnostics.append(Diagnostic(
                        first_rule.line, 1, 10, 'error',
                        f"'else' on first method '{first_rule.head.name}' - nothing to be else to",
                        'HTN004'
                    ))

    def _check_empty_clauses(self):
        """Check for empty if/do/del/add clauses"""
        for rule in self.rules:
            if rule.is_method:
                # Empty do() is problematic
                if rule.do_clause and len(rule.do_clause.args) == 0:
                    self.diagnostics.append(Diagnostic(
                        rule.line, 1, 10, 'warning',
                        f"Method '{rule.head.name}' has empty do() clause - does nothing",
                        'HTN005'
                    ))

            if rule.is_operator:
                # Empty del() and empty add() might be intentional but worth warning
                if rule.del_clause and len(rule.del_clause.args) == 0 and \
                   rule.add_clause and len(rule.add_clause.args) == 0:
                    self.diagnostics.append(Diagnostic(
                        rule.line, 1, 10, 'warning',
                        f"Operator '{rule.head.name}' has empty del() and add() - does nothing",
                        'HTN006'
                    ))

    def _check_singleton_variables(self):
        """Check for variables that appear only once (typo warning)"""
        for rule in self.rules:
            var_counts: Dict[str, int] = defaultdict(int)

            # Count in head
            for var in rule.head.get_variables():
                var_counts[var] += 1

            # Count in body
            for term in rule.body:
                for var in term.get_variables():
                    var_counts[var] += 1

            # Report singletons (except _ which is intentionally ignored)
            for var, count in var_counts.items():
                if count == 1 and not var.startswith('_') and var != '?_':
                    self.diagnostics.append(Diagnostic(
                        rule.line, 1, len(var), 'warning',
                        f"Singleton variable '{var}' appears only once (typo?)",
                        'VAR003'
                    ))

    _DIRECTIVE_RE = re.compile(r'^\s*%::\s*(\w+)\s*\(([^)]*)\)\s*$')

    def _collect_overrides_and_directives(self):
        """Optional type contracts via `%:: pred(?v: type, ...)` comment
        directives placed directly above a rule (the engine ignores comments).
        A directive anchors each position's expected type AND binds the named
        head variables. Returns (overrides, directive_var_types).

        (`signature/2` and `type/2` facts are NOT read — types come from unary
        facts; the directive is the one optional override mechanism.)
        """
        overrides: Dict[Tuple[str, int], Set[str]] = {}
        directive_var_types: Dict[int, Dict[str, Set[str]]] = defaultdict(dict)

        # %:: directives: regex pre-pass (the lexer discards comments).
        directives = {}
        for idx, raw in enumerate(self.source.splitlines(), start=1):
            m = self._DIRECTIVE_RE.match(raw)
            if not m:
                continue
            entries = []
            for part in m.group(2).split(','):
                part = part.strip()
                if not part:
                    continue
                if ':' in part:
                    var, typ = part.split(':', 1)
                    entries.append((var.strip(), typ.strip()))
                else:
                    entries.append((None, part))
            directives[idx] = (m.group(1), entries)

        if directives:
            rules_by_line = sorted(self.rules, key=lambda r: r.line)
            for dline, (pred, entries) in directives.items():
                arity = len(entries)
                key = f"{pred}/{arity}"
                target = next(
                    (r for r in rules_by_line
                     if r.line > dline and r.head.name == pred
                     and len(r.head.args) == arity), None)
                for i, (var, typ) in enumerate(entries):
                    overrides[(key, i)] = {typ}
                    if var and target is not None:
                        directive_var_types[id(target)][var] = {typ}
        return overrides, directive_var_types

    def _check_type_inference(self) -> None:
        """TYP010: flag a call-site argument whose inferred type is provably
        disjoint from a well-determined position type. High-signal:

          * A position's EXPECTED type is taken from its *definitions* — rule
            heads whose variable the body constrains (1 is enough; an authored
            contract), or >=2 facts that agree. Conflicting definitions mean
            the position is polymorphic and are silenced.
          * If a position has no definitional type (e.g. an operator that never
            touches the argument), fall back to the consensus of >=2 call sites.
          * Every occurrence is typed EXCLUDING its own position, so a wrong
            call cannot poison the type it is being checked against.
        """
        overrides, directive_var_types = self._collect_overrides_and_directives()
        ti = TypeInference.from_rules(
            self.rules, overrides=overrides,
            directive_var_types=directive_var_types)

        def outside_type(arg, pos, var_positions, dvt):
            """Type of an argument occurrence, excluding this position."""
            if not arg.is_variable:
                return ti._arg_type(arg, {})
            acc = set(dvt[arg.name]) if arg.name in dvt else None
            poslist = list(var_positions.get(arg.name, []))
            if pos in poslist:
                poslist.remove(pos)
            for p in poslist:
                acc = ti._fold_var(acc, ti._pos_type(p))
            return acc or set()

        rule_def: Dict[Tuple[str, int], List[Set[str]]] = defaultdict(list)
        fact_def: Dict[Tuple[str, int], List[Set[str]]] = defaultdict(list)
        use_occs: Dict[Tuple[str, int], List[Tuple[Term, Set[str]]]] = defaultdict(list)

        for rule in self.rules:
            dvt = ti.directive_var_types.get(id(rule), {})
            goals = ti._collect_goal_terms(rule)
            guards = ti.positive_unary_guards(rule)  # var -> type-guard sorts
            # variable -> positions it occupies (head + goals), for folding
            var_positions: Dict[str, List[Tuple[str, int]]] = defaultdict(list)
            terms = [(rule.head, True)] + [(g, False) for g in goals]
            for term, _is_head in terms:
                arity = len(term.args)
                if _is_builtin_call(term.name, arity):
                    continue
                key = f"{term.name}/{arity}"
                for i, arg in enumerate(term.args):
                    if arg.is_variable:
                        var_positions[arg.name].append((key, i))
            for term, is_head in terms:
                arity = len(term.args)
                if _is_builtin_call(term.name, arity):
                    continue
                key = f"{term.name}/{arity}"
                for i, arg in enumerate(term.args):
                    pos = (key, i)
                    if is_head:
                        if rule.is_fact:
                            # facts define a position by their ground data
                            t = outside_type(arg, pos, var_positions, dvt)
                            if t:
                                fact_def[pos].append(t)
                        elif arg.is_variable:
                            # A rule head parameter is an authored contract ONLY
                            # when a positive unary type-guard binds it (the
                            # `disableEnemy(?e):-if(enemy(?e))` case). A param
                            # bound only by a polymorphic relation (e.g.
                            # `at(?a,?l)`) is NOT a contract — skip it.
                            t = guards.get(arg.name)
                            if t:
                                rule_def[pos].append(set(t))
                        else:  # constant in a rule head
                            t = ti._arg_type(arg, {})
                            if t:
                                rule_def[pos].append(t)
                    else:
                        t = outside_type(arg, pos, var_positions, dvt)
                        use_occs[pos].append((arg, t))

        for pos, occs in use_occs.items():
            # Only flag against an AUTHORITATIVE expected type (>=2 agreeing
            # facts, a type-guarded rule parameter, or a %:: directive). We do
            # NOT flag on mere call-site consensus: a predicate applied to two
            # rooms and one enemy is usually legitimately polymorphic, not a
            # bug — flagging the minority there is a false positive.
            expected = self._expected_position_type(pos, ti, rule_def, fact_def)
            if expected:  # authoritative, non-empty
                for arg, t in occs:
                    if t and ti.sorts_disjoint(t, expected):
                        self._emit_typ010(arg, pos, t, expected,
                                          f"declared {{{', '.join(sorted(expected))}}}")

    def _expected_position_type(self, pos, ti, rule_def, fact_def):
        """Authoritative type for a position, or None if it must fall back to
        call-site consensus. An empty set means 'silenced' (polymorphic)."""
        if pos in ti.overrides:
            # An override only bites on types that actually have instances. A
            # phantom type (no constant is known to be one — e.g. a stale
            # `signature(at,[actor])` whose `actor` sort was never migrated to
            # unary facts) gives no basis to call anything "not an actor", so
            # we drop it and fall through to inference instead of false-flagging.
            real = {t for t in ti.overrides[pos] if t in ti.type_universe}
            if real:
                return real
        defs = rule_def.get(pos)
        if defs:
            return set.intersection(*defs)  # empty => conflicting => silence
        facts = fact_def.get(pos)
        if facts and len(facts) >= 2:
            return set.intersection(*facts)
        return None  # no usable definition => use consensus

    def _emit_typ010(self, arg, pos, actual, expected, why):
        key, i = pos
        kind = 'variable' if arg.is_variable else 'constant'
        self.diagnostics.append(Diagnostic(
            line=arg.line,
            col=arg.col,
            length=len(arg.name),
            severity='warning',
            code='TYP010',
            message=(f"Argument {i+1} of '{key}': {kind} '{arg.name}' has type "
                     f"{{{', '.join(sorted(actual))}}}, but this position is {why}"),
        ))


def lint_htn(source: str) -> List[Dict]:
    """Convenience function to lint HTN source and return diagnostics as dicts"""
    linter = HtnLinter(source)
    diagnostics = linter.lint()
    return [d.to_dict() for d in diagnostics]


def lint_file(file_path: str) -> List[Dict]:
    """Lint an HTN file and return diagnostics"""
    with open(file_path, 'r', encoding='utf-8') as f:
        source = f.read()
    return lint_htn(source)
