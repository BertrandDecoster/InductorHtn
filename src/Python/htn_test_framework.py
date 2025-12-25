"""
HTN Test Framework - Validates HTN rulesets using existing Python bindings

This framework provides assertion methods for testing HTN planning behavior,
query results, state changes, and decomposition trees.
"""

import json
import os
import sys
from typing import List, Dict, Callable, Optional, Any, Tuple

# Add the current directory to path for imports
sys.path.insert(0, os.path.dirname(__file__))

from indhtnpy import HtnPlanner, findAllPlansResultToPrologStringList, termToString, termName, termArgs


class TestResult:
    """Represents the result of a single test assertion."""

    def __init__(self, passed: bool, message: str, details: str = ""):
        self.passed = passed
        self.message = message
        self.details = details

    def __str__(self):
        status = "PASS" if self.passed else "FAIL"
        result = f"[{status}] {self.message}"
        if not self.passed and self.details:
            result += f"\n       Details: {self.details}"
        return result


class HtnTestSuite:
    """
    Test suite for validating HTN rulesets.

    Usage:
        suite = HtnTestSuite("Examples/Taxi.htn")
        suite.assert_plan("travel-to(park).", contains=["walk(downtown, park)"])
        print(suite.summary())
    """

    def __init__(self, htn_file: str = None, verbose: bool = False):
        """
        Initialize test suite.

        Args:
            htn_file: Path to .htn file to test (relative to project root or absolute)
            verbose: Enable debug tracing
        """
        self.verbose = verbose
        self.results: List[TestResult] = []
        self.htn_file = htn_file
        self._planner = None
        self._project_root = self._find_project_root()

        if htn_file:
            self.load_file(htn_file)

    def _find_project_root(self) -> str:
        """Find the project root directory (contains Examples/)."""
        current = os.path.dirname(os.path.abspath(__file__))
        while current != os.path.dirname(current):  # Not at filesystem root
            if os.path.exists(os.path.join(current, "Examples")):
                return current
            current = os.path.dirname(current)
        # Fallback to parent of src/Python
        return os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))

    def _resolve_path(self, path: str) -> str:
        """Resolve a path relative to project root."""
        if os.path.isabs(path):
            return path
        return os.path.join(self._project_root, path)

    def load_file(self, htn_file: str) -> bool:
        """
        Load an HTN file into the planner.

        Args:
            htn_file: Path to .htn file

        Returns:
            True if loaded successfully
        """
        self.htn_file = htn_file
        abs_path = self._resolve_path(htn_file)

        if not os.path.exists(abs_path):
            self._record(False, f"Load file: {htn_file}", f"File not found: {abs_path}")
            return False

        with open(abs_path, 'r', encoding='utf-8') as f:
            content = f.read()

        self._planner = HtnPlanner(self.verbose)
        error = self._planner.HtnCompileCustomVariables(content)

        if error is not None:
            self._record(False, f"Load file: {htn_file}", f"Compile error: {error}")
            return False

        return True

    def _reload_file(self):
        """Reload the HTN file to reset state."""
        if self.htn_file:
            self.load_file(self.htn_file)

    def _record(self, passed: bool, message: str, details: str = "") -> bool:
        """Record a test result and return whether it passed."""
        self.results.append(TestResult(passed, message, details))
        return passed

    def _ensure_planner(self) -> bool:
        """Ensure planner is initialized."""
        if self._planner is None:
            self._record(False, "Test setup", "No HTN file loaded. Call load_file() first.")
            return False
        return True

    # =========================================================================
    # Component Loading (for component-based testing)
    # =========================================================================

    def reset(self):
        """
        Reset the planner to a fresh state.

        Call this before each test to ensure clean state.
        """
        self._planner = None
        self._loaded_components = set()

    def load_component(self, component_path: str, reset_first: bool = True) -> bool:
        """
        Load a component and its dependencies.

        Args:
            component_path: Path like "primitives/locomotion" or just "locomotion"
            reset_first: If True, resets planner before loading (default True)

        Returns:
            True if loaded successfully
        """
        # Track loaded components to avoid duplicates
        if not hasattr(self, '_loaded_components'):
            self._loaded_components = set()

        # Reset planner if requested (for fresh state)
        if reset_first:
            self._planner = HtnPlanner(self.verbose)
            self._loaded_components = set()

        # Skip if already loaded
        if component_path in self._loaded_components:
            return True

        components_root = os.path.join(self._project_root, "components")

        # Resolve component path
        full_path = None

        # Try direct path first
        direct = os.path.join(components_root, component_path)
        if os.path.isdir(direct):
            full_path = direct
        else:
            # Search in layer directories
            for layer in ["primitives", "strategies", "goals"]:
                layer_path = os.path.join(components_root, layer, component_path)
                if os.path.isdir(layer_path):
                    full_path = layer_path
                    break

        if full_path is None:
            self._record(False, f"Load component: {component_path}",
                        f"Component not found in {components_root}")
            return False

        # Load manifest to get dependencies
        manifest_path = os.path.join(full_path, "manifest.json")
        if os.path.exists(manifest_path):
            with open(manifest_path, 'r') as f:
                manifest = json.load(f)

            # Load dependencies first (recursively, without resetting)
            for dep in manifest.get("dependencies", []):
                if not self.load_component(dep, reset_first=False):
                    return False

        # Load the component's src.htn
        src_path = os.path.join(full_path, "src.htn")
        if not os.path.exists(src_path):
            self._record(False, f"Load component: {component_path}",
                        f"No src.htn found in {full_path}")
            return False

        with open(src_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Initialize planner if needed
        if self._planner is None:
            self._planner = HtnPlanner(self.verbose)

        # Compile component (appends to existing ruleset)
        error = self._planner.HtnCompileCustomVariables(content)
        if error is not None:
            self._record(False, f"Load component: {component_path}",
                        f"Compile error: {error}")
            return False

        # Mark as loaded
        self._loaded_components.add(component_path)

        return True

    def set_state(self, facts: List[str]) -> bool:
        """
        Set the initial state by compiling facts.

        Note: This ADDS facts to the current state. For a clean state,
        reload the file or component first.

        Args:
            facts: List of fact strings, e.g., ["at(player, room1)", "hasTag(enemy, burning)"]

        Returns:
            True if all facts compiled successfully
        """
        if self._planner is None:
            self._planner = HtnPlanner(self.verbose)

        # Compile each fact
        for fact in facts:
            # Ensure fact ends with period
            fact_str = fact.strip()
            if not fact_str.endswith('.'):
                fact_str += '.'

            error = self._planner.HtnCompileCustomVariables(fact_str)
            if error is not None:
                self._record(False, f"Set state: {fact}", f"Compile error: {error}")
                return False

        return True

    def get_state(self) -> List[str]:
        """
        Get current state as a list of fact strings.

        Returns:
            List of fact strings, e.g., ["at(player, room1)", "hasTag(enemy, burning)"]
        """
        if not self._ensure_planner():
            return []

        error, facts_json = self._planner.GetStateFacts()
        if error is not None:
            return []

        return json.loads(facts_json)

    def query_all(self, query: str) -> List[Dict[str, str]]:
        """
        Execute a query and return all solutions as variable bindings.

        Useful for property-based testing where you need to iterate over
        all possible bindings.

        Args:
            query: Prolog query, e.g., "tagCombines(?a, ?b, ?result)"

        Returns:
            List of dicts mapping variable names to values,
            e.g., [{"?a": "burning", "?b": "wet", "?result": "steam"}, ...]
        """
        if not self._ensure_planner():
            return []

        # Ensure query ends with period
        query_str = query.strip()
        if not query_str.endswith('.'):
            query_str += '.'

        error, result = self._planner.PrologQuery(query_str)
        if error is not None:
            return []

        solutions = json.loads(result)

        # Check for failure
        if solutions and isinstance(solutions[0], dict) and "false" in solutions[0]:
            return []

        # Convert solution format to simple string bindings
        result_list = []
        for solution in solutions:
            bindings = {}
            for var_name, value in solution.items():
                if isinstance(value, dict):
                    bindings[var_name] = termToString(value)
                else:
                    bindings[var_name] = str(value)
            result_list.append(bindings)

        return result_list

    def run_goal(self, goal: str, solution_index: int = 0) -> bool:
        """
        Execute a goal, find a plan, and apply the solution.

        This modifies the planner's state. Use get_state() after to
        inspect the result.

        Args:
            goal: HTN goal, e.g., "defeatEnemy(enemy1)"
            solution_index: Which solution to apply (default: first)

        Returns:
            True if goal succeeded and solution was applied
        """
        if not self._ensure_planner():
            return False

        # Ensure goal ends with period
        goal_str = goal.strip()
        if not goal_str.endswith('.'):
            goal_str += '.'

        # Find plans
        error, result = self._planner.FindAllPlansCustomVariables(goal_str)
        if error is not None:
            return False

        solutions = json.loads(result)
        if not solutions or (isinstance(solutions[0], dict) and "false" in solutions[0]):
            return False

        # Apply solution
        return self._planner.ApplySolution(solution_index)

    def compile_additional(self, content: str) -> bool:
        """
        Compile additional HTN/Prolog content into the current ruleset.

        Useful for adding test-specific rules or facts.

        Args:
            content: HTN/Prolog code to compile

        Returns:
            True if compiled successfully
        """
        if self._planner is None:
            self._planner = HtnPlanner(self.verbose)

        error = self._planner.HtnCompileCustomVariables(content)
        return error is None

    # =========================================================================
    # Compilation Assertions
    # =========================================================================

    def assert_compiles(self, content: str, msg: str = "") -> bool:
        """
        Assert that HTN content compiles without errors.

        Args:
            content: HTN/Prolog code to compile
            msg: Optional test message
        """
        planner = HtnPlanner(self.verbose)
        error = planner.HtnCompileCustomVariables(content)

        message = msg or "Content compiles successfully"
        if error is None:
            return self._record(True, message)
        else:
            return self._record(False, message, f"Compile error: {error}")

    def assert_compile_error(self, content: str, contains: str = "", msg: str = "") -> bool:
        """
        Assert that HTN content produces a compile error.

        Args:
            content: HTN/Prolog code that should fail to compile
            contains: Substring that should appear in error message
            msg: Optional test message
        """
        planner = HtnPlanner(self.verbose)
        error = planner.HtnCompileCustomVariables(content)

        message = msg or "Content produces compile error"

        if error is None:
            return self._record(False, message, "Expected compile error but compilation succeeded")

        if contains and contains not in error:
            return self._record(False, message,
                f"Error message '{error}' does not contain '{contains}'")

        return self._record(True, message)

    # =========================================================================
    # Planning Assertions
    # =========================================================================

    def assert_plan(self, goal: str,
                    contains: List[str] = None,
                    not_contains: List[str] = None,
                    min_solutions: int = 1,
                    max_solutions: int = None,
                    msg: str = "") -> bool:
        """
        Assert that planning produces expected results.

        Args:
            goal: HTN goal to plan (e.g., "travel-to(park).")
            contains: Operator substrings that must appear in at least one solution
            not_contains: Operator substrings that must NOT appear in any solution
            min_solutions: Minimum number of solutions required
            max_solutions: Maximum number of solutions allowed (None = no limit)
            msg: Optional test message
        """
        if not self._ensure_planner():
            return False

        self._reload_file()  # Reset state before each plan

        message = msg or f"Plan: {goal}"

        error, result = self._planner.FindAllPlansCustomVariables(goal)

        if error is not None:
            return self._record(False, message, f"Planning error: {error}")

        solutions = json.loads(result)

        # Check for failure result
        if solutions and isinstance(solutions[0], dict) and "false" in solutions[0]:
            if min_solutions > 0:
                return self._record(False, message, "Planning failed - no solutions found")
            return self._record(True, message)

        num_solutions = len(solutions)

        # Check solution count
        if num_solutions < min_solutions:
            return self._record(False, message,
                f"Expected at least {min_solutions} solutions, got {num_solutions}")

        if max_solutions is not None and num_solutions > max_solutions:
            return self._record(False, message,
                f"Expected at most {max_solutions} solutions, got {num_solutions}")

        # Convert solutions to string representation for checking
        solution_strs = findAllPlansResultToPrologStringList(result)
        all_solutions_str = " ".join(solution_strs)

        # Check contains
        if contains:
            for pattern in contains:
                if pattern not in all_solutions_str:
                    return self._record(False, message,
                        f"Expected '{pattern}' in solutions but not found.\n"
                        f"       Solutions: {solution_strs[:3]}...")

        # Check not_contains
        if not_contains:
            for pattern in not_contains:
                if pattern in all_solutions_str:
                    return self._record(False, message,
                        f"Did not expect '{pattern}' in solutions but found it.\n"
                        f"       Solutions: {solution_strs[:3]}...")

        return self._record(True, message)

    def assert_no_plan(self, goal: str, msg: str = "") -> bool:
        """
        Assert that planning fails (no valid plan exists).

        Args:
            goal: HTN goal that should fail
            msg: Optional test message
        """
        return self.assert_plan(goal, min_solutions=0, max_solutions=0, msg=msg)

    # =========================================================================
    # Query Assertions
    # =========================================================================

    def assert_query(self, query: str,
                     bindings: Dict[str, str] = None,
                     min_solutions: int = 1,
                     max_solutions: int = None,
                     msg: str = "") -> bool:
        """
        Assert that a Prolog query returns expected results.

        Args:
            query: Prolog query (e.g., "at(?where).")
            bindings: Expected variable bindings in at least one solution
            min_solutions: Minimum solutions required (0 = query should fail)
            max_solutions: Maximum solutions allowed
            msg: Optional test message
        """
        if not self._ensure_planner():
            return False

        message = msg or f"Query: {query}"

        error, result = self._planner.PrologQuery(query)

        if error is not None:
            return self._record(False, message, f"Query error: {error}")

        solutions = json.loads(result)

        # Check for failure
        if solutions and isinstance(solutions[0], dict) and "false" in solutions[0]:
            if min_solutions == 0:
                return self._record(True, message)
            return self._record(False, message, "Query failed - no solutions")

        num_solutions = len(solutions)

        # Check solution count
        if num_solutions < min_solutions:
            return self._record(False, message,
                f"Expected at least {min_solutions} solutions, got {num_solutions}")

        if max_solutions is not None and num_solutions > max_solutions:
            return self._record(False, message,
                f"Expected at most {max_solutions} solutions, got {num_solutions}")

        # Check bindings if specified
        if bindings:
            found_match = False
            for solution in solutions:
                if self._bindings_match(solution, bindings):
                    found_match = True
                    break

            if not found_match:
                return self._record(False, message,
                    f"Expected bindings {bindings} not found in solutions")

        return self._record(True, message)

    def _bindings_match(self, solution: Dict, expected: Dict[str, str]) -> bool:
        """Check if a solution contains expected bindings."""
        for var, expected_val in expected.items():
            # Normalize variable name (add ? if missing)
            var_key = var if var.startswith("?") else f"?{var}"

            if var_key not in solution:
                return False

            actual = solution[var_key]
            # Convert actual to string for comparison
            if isinstance(actual, dict):
                actual_str = termToString(actual)
            else:
                actual_str = str(actual)

            if expected_val not in actual_str:
                return False

        return True

    # =========================================================================
    # State Assertions
    # =========================================================================

    def assert_state_after(self, goal: str,
                           has: List[str] = None,
                           not_has: List[str] = None,
                           solution_index: int = 0,
                           msg: str = "") -> bool:
        """
        Assert facts exist/don't exist after applying a plan.

        Args:
            goal: HTN goal to plan and apply
            has: Fact patterns that must exist in final state
            not_has: Fact patterns that must NOT exist
            solution_index: Which solution to apply (default: first)
            msg: Optional test message
        """
        if not self._ensure_planner():
            return False

        self._reload_file()  # Reset state

        message = msg or f"State after: {goal}"

        # First, find plans
        error, result = self._planner.FindAllPlansCustomVariables(goal)

        if error is not None:
            return self._record(False, message, f"Planning error: {error}")

        solutions = json.loads(result)
        if not solutions or (isinstance(solutions[0], dict) and "false" in solutions[0]):
            return self._record(False, message, "No plan found to apply")

        # Get facts for the solution's final state
        error, facts_json = self._planner.GetSolutionFacts(solution_index)

        if error is not None:
            return self._record(False, message, f"Error getting solution facts: {error}")

        facts = json.loads(facts_json)
        facts_str = " ".join(facts)

        # Check has
        if has:
            for pattern in has:
                if pattern not in facts_str:
                    return self._record(False, message,
                        f"Expected fact '{pattern}' not found in state.\n"
                        f"       State: {facts[:10]}...")

        # Check not_has
        if not_has:
            for pattern in not_has:
                if pattern in facts_str:
                    return self._record(False, message,
                        f"Unexpected fact '{pattern}' found in state.\n"
                        f"       State: {facts[:10]}...")

        return self._record(True, message)

    def assert_state_invariant(self, check_fn: Callable[[List[str]], bool],
                               description: str) -> bool:
        """
        Assert a custom invariant holds on current state.

        Args:
            check_fn: Function that takes list of facts and returns True if valid
            description: Description of the invariant
        """
        if not self._ensure_planner():
            return False

        error, facts_json = self._planner.GetStateFacts()

        if error is not None:
            return self._record(False, f"Invariant: {description}",
                f"Error getting facts: {error}")

        facts = json.loads(facts_json)

        try:
            if check_fn(facts):
                return self._record(True, f"Invariant: {description}")
            else:
                return self._record(False, f"Invariant: {description}",
                    "Invariant check returned False")
        except Exception as e:
            return self._record(False, f"Invariant: {description}",
                f"Invariant check raised exception: {e}")

    # =========================================================================
    # Decomposition Tree Assertions
    # =========================================================================

    def assert_decomposition(self, goal: str,
                             uses_method: List[str] = None,
                             uses_operator: List[str] = None,
                             avoids_method: List[str] = None,
                             avoids_operator: List[str] = None,
                             solution_index: int = 0,
                             msg: str = "") -> bool:
        """
        Assert properties about the decomposition tree.

        Args:
            goal: HTN goal to plan
            uses_method: Method names that must appear in decomposition
            uses_operator: Operator names that must appear
            avoids_method: Method names that must NOT appear
            avoids_operator: Operator names that must NOT appear
            solution_index: Which solution's tree to check
            msg: Optional test message
        """
        if not self._ensure_planner():
            return False

        self._reload_file()

        message = msg or f"Decomposition: {goal}"

        # First, find plans
        error, result = self._planner.FindAllPlansCustomVariables(goal)

        if error is not None:
            return self._record(False, message, f"Planning error: {error}")

        solutions = json.loads(result)
        if not solutions or (isinstance(solutions[0], dict) and "false" in solutions[0]):
            return self._record(False, message, "No plan found")

        # Get decomposition tree
        error, tree_json = self._planner.GetDecompositionTree(solution_index)

        if error is not None:
            return self._record(False, message, f"Error getting tree: {error}")

        tree_nodes = json.loads(tree_json)

        # Extract method and operator names from tree
        methods_used = set()
        operators_used = set()

        for node in tree_nodes:
            # Extract method name
            method_sig = node.get('methodSignature', '')
            if method_sig:
                # Extract just the name before (
                method_name = method_sig.split('(')[0] if '(' in method_sig else method_sig
                methods_used.add(method_name)

            # Extract operator name
            op_sig = node.get('operatorSignature', '')
            if op_sig:
                op_name = op_sig.split('(')[0] if '(' in op_sig else op_sig
                operators_used.add(op_name)

            # Also check taskName for operators
            if node.get('isOperator', False):
                task_name = node.get('taskName', '')
                if task_name:
                    op_name = task_name.split('(')[0] if '(' in task_name else task_name
                    operators_used.add(op_name)

        # Check uses_method
        if uses_method:
            for method in uses_method:
                if method not in methods_used:
                    return self._record(False, message,
                        f"Expected method '{method}' not used.\n"
                        f"       Methods used: {methods_used}")

        # Check uses_operator
        if uses_operator:
            for op in uses_operator:
                if op not in operators_used:
                    return self._record(False, message,
                        f"Expected operator '{op}' not used.\n"
                        f"       Operators used: {operators_used}")

        # Check avoids_method
        if avoids_method:
            for method in avoids_method:
                if method in methods_used:
                    return self._record(False, message,
                        f"Method '{method}' should not be used but was")

        # Check avoids_operator
        if avoids_operator:
            for op in avoids_operator:
                if op in operators_used:
                    return self._record(False, message,
                        f"Operator '{op}' should not be used but was")

        return self._record(True, message)

    # =========================================================================
    # Reporting
    # =========================================================================

    @property
    def tests_run(self) -> int:
        return len(self.results)

    @property
    def tests_passed(self) -> int:
        return sum(1 for r in self.results if r.passed)

    @property
    def tests_failed(self) -> int:
        return sum(1 for r in self.results if not r.passed)

    def summary(self) -> str:
        """Return a summary of test results."""
        lines = []

        if self.htn_file:
            lines.append(f"Test Suite: {self.htn_file}")
        lines.append("=" * 50)

        for result in self.results:
            lines.append(str(result))

        lines.append("=" * 50)
        lines.append(f"Total: {self.tests_passed}/{self.tests_run} passed")

        if self.tests_failed > 0:
            lines.append(f"       {self.tests_failed} FAILED")

        return "\n".join(lines)

    def all_passed(self) -> bool:
        """Return True if all tests passed."""
        return self.tests_failed == 0

    def to_json(self) -> Dict[str, Any]:
        """Return results as JSON-serializable dict."""
        return {
            "file": self.htn_file,
            "tests_run": self.tests_run,
            "tests_passed": self.tests_passed,
            "tests_failed": self.tests_failed,
            "results": [
                {
                    "passed": r.passed,
                    "message": r.message,
                    "details": r.details
                }
                for r in self.results
            ]
        }


# Utility functions for common invariants

def no_duplicate_positions(facts: List[str], predicate: str = "at") -> bool:
    """
    Check that no two entities share the same position.
    Useful for game invariant "one unit per tile".
    """
    positions = []
    for fact in facts:
        if fact.startswith(f"{predicate}("):
            # Extract position part (everything after first comma or the second arg)
            # at(Unit, Position) -> Position
            inner = fact[len(predicate)+1:-1]  # Remove "at(" and ")"
            parts = inner.split(", ", 1)
            if len(parts) >= 2:
                pos = parts[1]
                if pos in positions:
                    return False
                positions.append(pos)
    return True


def fact_count(facts: List[str], pattern: str) -> int:
    """Count facts matching a pattern prefix."""
    return sum(1 for f in facts if f.startswith(pattern))
