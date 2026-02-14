"""
Test helpers for C++ parity tests.

Mirrors the C++ test helper classes (HtnBasicTestHelper, HtnAdvancedTestHelper,
BuiltInTestHelper) and provides format conversion from Python JSON to C++ string formats.
"""
import sys
import os
import json
import re

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src', 'Python'))

from indhtnpy import (
    HtnPlanner,
    findAllPlansResultToPrologStringList,
    queryResultToPrologStringList,
    termToString,
    termName,
    termArgs,
    termIsList,
    termIsConstant,
)


def _strip_atom_quotes(name: str) -> str:
    """Strip single quotes from atom names that the C++ JSON wraps around capitalized atoms."""
    if len(name) >= 2 and name.startswith("'") and name.endswith("'"):
        return name[1:-1]
    return name


def cpp_term_to_string(term) -> str:
    """Convert a JSON term to C++ ToString format (no spaces after commas, no atom quotes)."""
    if isinstance(term, str):
        return _strip_atom_quotes(term)
    elif termIsList(term):
        parts = [cpp_term_to_string(item) for item in term]
        return "[" + ",".join(parts) + "]"
    else:
        name = _strip_atom_quotes(termName(term))
        if termIsConstant(term):
            return name
        args = [cpp_term_to_string(arg) for arg in termArgs(term)]
        return name + "(" + ",".join(args) + ")"


def split_goals_from_program(program: str):
    """Split a program string into (rules, goals_query).

    The C++ tests include goals(...). in the program. The Python API
    needs them separated: rules compiled via HtnCompileCustomVariables,
    goals passed to FindAllPlansCustomVariables.

    Returns (rules_str, goals_query_str) where goals_query_str is the inner
    content of goals(), e.g. "travel(park)." for FindAllPlansCustomVariables.
    """
    # Find the last goals(...). in the program
    pattern = r'goals\('
    matches = list(re.finditer(pattern, program))
    if not matches:
        return program, None

    last_match = matches[-1]
    start = last_match.start()
    goals_inner_start = last_match.end()  # position after "goals("

    # Find matching closing paren for goals(
    depth = 1
    for j in range(goals_inner_start, len(program)):
        if program[j] == '(':
            depth += 1
        elif program[j] == ')':
            depth -= 1
            if depth == 0:
                # Extract inner content
                inner = program[goals_inner_start:j]

                # Find the dot after the closing paren
                end = j + 1
                while end < len(program) and program[end] in ' \t\r\n':
                    end += 1
                if end < len(program) and program[end] == '.':
                    end += 1

                rules = program[:start] + program[end:]
                # Return inner content as query with trailing dot
                return rules.strip(), inner.strip() + "."

    return program, None


def _cpp_term_list_to_string(term_list) -> str:
    """Convert a JSON term list to C++ format string (no spaces, no quotes)."""
    return ", ".join(cpp_term_to_string(term) for term in term_list)


def json_plans_to_cpp_str(json_str: str) -> str:
    """Convert FindAllPlans JSON result to C++ ToStringSolutions format.

    C++ format: "[ { (op1(a), op2(b)) } { (op3(c)) } ]"
    or "null" for failure.
    """
    parsed = json.loads(json_str)

    # Check for failure
    if len(parsed) > 0 and isinstance(parsed[0], dict) and "false" in parsed[0]:
        return "null"

    if not parsed:
        return "null"

    parts = []
    for solution in parsed:
        s = _cpp_term_list_to_string(solution)
        parts.append("{ (" + s + ") }")
    return "[ " + " ".join(parts) + " ]"


def json_facts_to_cpp_str(facts_json: str) -> str:
    """Convert GetSolutionFacts JSON result to C++ ToStringFacts format.

    C++ format: "[ { fact1(a) => ,fact2(b) =>  } ]"
    Facts JSON is a list of strings like ["fact1(a)", "fact2(b)"]
    """
    facts = json.loads(facts_json)
    parts = []
    for f in facts:
        parts.append(f + " => ")
    return "[ { " + ",".join(parts) + " } ]"


def json_multi_facts_to_cpp_str(all_facts: list) -> str:
    """Convert multiple solution facts to C++ ToStringFacts format.

    C++ format: "[ { fact1 => ,fact2 =>  } { fact3 => ,fact4 =>  } ]"
    """
    if not all_facts:
        return "null"

    solution_parts = []
    for facts_json in all_facts:
        facts = json.loads(facts_json)
        parts = []
        for f in facts:
            parts.append(f + " => ")
        solution_parts.append("{ " + ",".join(parts) + " }")
    return "[ " + " ".join(solution_parts) + " ]"


def json_unifier_to_cpp_str(json_str: str) -> str:
    """Convert PrologSolveGoals JSON result to C++ HtnGoalResolver::ToString format.

    C++ format: "((?X = val, ?Y = val2))" for single solution
                "((?X = val), (?Y = val2))" for multiple solutions
                "(())" for success with no bindings
                "null" for failure
    """
    parsed = json.loads(json_str)

    # Check for failure
    if parsed is None:
        return "null"
    if len(parsed) > 0 and isinstance(parsed[0], dict) and "false" in parsed[0]:
        return "null"

    solution_strs = []
    for solution in parsed:
        if not isinstance(solution, dict):
            continue
        bindings = []
        for var_name, value in solution.items():
            bindings.append(f"{var_name} = {cpp_term_to_string(value)}")
        solution_strs.append("(" + ", ".join(bindings) + ")")

    if not solution_strs:
        return "null"
    return "(" + ", ".join(solution_strs) + ")"


class HtnTestHelper:
    """Mirrors C++ HtnBasicTestHelper / HtnAdvancedTestHelper.

    Compiles HTN programs with goals, finds plans, returns C++ format strings.
    """

    def __init__(self):
        self.planner = HtnPlanner(False)
        self._last_result_json = None
        self._num_solutions = 0

    def find_first_plan(self, program: str) -> str:
        """Compile program with goals, find first plan.
        Returns plan string matching C++ ToStringSolution format.
        """
        self.planner = HtnPlanner(False)  # Fresh planner each call (like C++ ClearWithNewRuleSet)
        rules, goals = split_goals_from_program(program)

        if rules.strip():
            err = self.planner.HtnCompileCustomVariables(rules)
            if err is not None:
                raise RuntimeError(f"Compile error: {err}")

        if goals is None:
            return "null"

        err, result = self.planner.FindAllPlansCustomVariables(goals)
        if err is not None:
            return "null"

        self._last_result_json = result
        parsed = json.loads(result)

        # Check for failure
        if len(parsed) > 0 and isinstance(parsed[0], dict) and "false" in parsed[0]:
            self._num_solutions = 0
            return "null"

        self._num_solutions = len(parsed)
        if not parsed:
            return "null"

        # Return first solution as string using C++ format
        first_solution = parsed[0]
        s = _cpp_term_list_to_string(first_solution)
        return "(" + s + ")"

    def find_all_plans(self, program: str) -> str:
        """Compile program with goals, find all plans.
        Returns string matching C++ ToStringSolutions format.
        """
        self.planner = HtnPlanner(False)
        rules, goals = split_goals_from_program(program)

        if rules.strip():
            err = self.planner.HtnCompileCustomVariables(rules)
            if err is not None:
                raise RuntimeError(f"Compile error: {err}")

        if goals is None:
            return "null"

        err, result = self.planner.FindAllPlansCustomVariables(goals)
        if err is not None:
            return "null"

        self._last_result_json = result
        return json_plans_to_cpp_str(result)

    def get_solution_facts(self, index: int = 0) -> str:
        """Get facts after solution. Returns C++ ToStringFacts format for single solution."""
        err, facts = self.planner.GetSolutionFacts(index)
        if err is not None:
            return "null"
        return facts

    def get_all_solution_facts(self) -> str:
        """Get facts for all solutions in C++ ToStringFacts format."""
        if self._last_result_json is None:
            return "null"

        parsed = json.loads(self._last_result_json)
        if len(parsed) > 0 and isinstance(parsed[0], dict) and "false" in parsed[0]:
            return "null"

        all_facts = []
        for i in range(len(parsed)):
            err, facts = self.planner.GetSolutionFacts(i)
            if err is not None:
                return "null"
            all_facts.append(facts)

        return json_multi_facts_to_cpp_str(all_facts)

    def apply_solution(self, index: int = 0) -> bool:
        """Apply solution to update world state."""
        return self.planner.ApplySolution(index)

    def query_state(self, query: str) -> str:
        """Run a Prolog query against current state."""
        if not query.endswith('.'):
            query = query + '.'
        err, result = self.planner.PrologQuery(query)
        if err is not None:
            return "null"
        parsed = json.loads(result)
        if len(parsed) > 0 and isinstance(parsed[0], dict) and "false" in parsed[0]:
            return "null"
        return result


class PrologTestHelper:
    """Mirrors C++ BuiltInTestHelper.

    Compiles Prolog programs with goals, solves, returns C++ format strings.
    """

    def __init__(self):
        self.planner = HtnPlanner(False)

    def solve(self, program: str) -> str:
        """Compile Prolog program with goals, solve.
        Returns unifier string in C++ HtnGoalResolver::ToString format.
        """
        self.planner = HtnPlanner(False)  # Fresh planner each call

        # Use PrologCompile (standard syntax) since SolveGoals uses m_prologCompiler
        err = self.planner.PrologCompile(program)
        if err is not None:
            raise RuntimeError(f"Compile error: {err}")

        err, result = self.planner.PrologSolveGoals()
        if err is not None:
            return "null"

        if result is None:
            return "null"

        return json_unifier_to_cpp_str(result)


class CustomVarPrologTestHelper:
    """Like PrologTestHelper but uses ?-prefix variable syntax.

    Uses PrologCompileCustomVariables + PrologQuery instead of
    PrologCompile + PrologSolveGoals. This supports:
    - Uppercase atoms as constants (Name1, A, B)
    - Lowercase variables with ? prefix (?x, ?y)
    - assert/retract through PrologQuery
    - Full variable binding returns (including cut variables)
    """

    def __init__(self):
        self.planner = HtnPlanner(False)

    def solve(self, program: str) -> str:
        """Compile program with goals using ?-prefix syntax, solve.
        Returns unifier string in C++ HtnGoalResolver::ToString format.
        """
        self.planner = HtnPlanner(False)

        rules, goals = split_goals_from_program(program)

        if rules and rules.strip():
            err = self.planner.PrologCompileCustomVariables(rules)
            if err is not None:
                raise RuntimeError(f"Compile error: {err}")

        if goals is None:
            return "null"

        # Remove trailing dot for PrologQuery
        query = goals
        if not query.endswith('.'):
            query = query + '.'

        err, result = self.planner.PrologQuery(query)
        if err is not None:
            return "null"

        if result is None:
            return "null"

        return json_unifier_to_cpp_str(result)


class PrologQueryHelper:
    """Helper for Prolog tests that use direct queries (? prefix variables)."""

    def __init__(self):
        self.planner = HtnPlanner(False)

    def compile_and_query(self, program: str, query: str) -> str:
        """Compile program, run query, return C++ format result."""
        self.planner = HtnPlanner(False)

        if program.strip():
            err = self.planner.PrologCompileCustomVariables(program)
            if err is not None:
                raise RuntimeError(f"Compile error: {err}")

        if not query.endswith('.'):
            query = query + '.'

        err, result = self.planner.PrologQuery(query)
        if err is not None:
            return "null"

        parsed = json.loads(result)
        if len(parsed) > 0 and isinstance(parsed[0], dict) and "false" in parsed[0]:
            return "null"

        return result
