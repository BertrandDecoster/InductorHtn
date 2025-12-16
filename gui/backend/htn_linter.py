"""
HTN Linter - Syntax and Semantic Checks
Analyzes parsed HTN rules for common errors and warnings.
"""

from typing import List, Dict, Set, Optional, Tuple
from dataclasses import dataclass, field
from collections import defaultdict

from htn_parser import parse_htn, Rule, Term, Diagnostic


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


class HtnLinter:
    """Linter for HTN/Prolog files"""

    def __init__(self, source: str):
        self.source = source
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
        # Handle try() and other wrappers
        if task.name in ('try', 'first'):
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

        # Built-in predicates and HTN keywords
        builtins = {
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
        all_defined.update(builtins)

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
        if task.name in ('try', 'first'):
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
            visited.add(node)
            rec_stack.add(node)
            path.append(node)

            for callee in self.calls.get(node, []):
                if callee not in visited:
                    if dfs(callee, path):
                        return True
                elif callee in rec_stack:
                    # Found cycle
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

            path.pop()
            rec_stack.remove(node)
            return False

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
