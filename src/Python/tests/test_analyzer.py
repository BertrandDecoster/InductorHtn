"""
Analyzer Test Suite
Tests the HTN semantic analyzer against various files.
"""

import os
import sys

# Add paths for imports
script_dir = os.path.dirname(os.path.abspath(__file__))
python_dir = os.path.dirname(script_dir)
backend_dir = os.path.abspath(os.path.join(python_dir, '../../gui/backend'))
project_root = os.path.abspath(os.path.join(python_dir, '../..'))

sys.path.insert(0, backend_dir)
sys.path.insert(0, python_dir)

from htn_analyzer import analyze_file, analyze_htn
from invariants import get_registry, StateInvariant, InvariantDefinition


class AnalyzerTestSuite:
    """Test suite for the HTN analyzer"""

    def __init__(self, verbose=False):
        self.verbose = verbose
        self.passed = 0
        self.failed = 0
        self.errors = []
        self.examples_dir = os.path.join(project_root, 'Examples')
        self.error_tests_dir = os.path.join(project_root, 'Examples', 'ErrorTests')

    def assert_true(self, condition: bool, test_name: str, msg: str = ""):
        """Assert a condition is true"""
        if condition:
            self.passed += 1
            if self.verbose:
                print(f"PASS: {test_name}")
            return True
        else:
            self.failed += 1
            error = f"FAIL: {test_name}"
            if msg:
                error += f" - {msg}"
            self.errors.append(error)
            if self.verbose:
                print(error)
            return False

    def assert_has_nodes(self, result: dict, expected_count: int = None,
                        test_name: str = "", msg: str = ""):
        """Assert analysis has nodes"""
        nodes = result.get('nodes', {})
        if expected_count:
            return self.assert_true(
                len(nodes) == expected_count,
                test_name,
                f"Expected {expected_count} nodes, got {len(nodes)}"
            )
        return self.assert_true(len(nodes) > 0, test_name, msg or "No nodes found")

    def assert_detects_cycle(self, result: dict, test_name: str = "", msg: str = ""):
        """Assert analysis detects at least one cycle"""
        cycles = result.get('cycles', [])
        return self.assert_true(len(cycles) > 0, test_name, msg or "No cycles detected")

    def assert_no_cycles(self, result: dict, test_name: str = "", msg: str = ""):
        """Assert analysis detects no cycles"""
        cycles = result.get('cycles', [])
        return self.assert_true(len(cycles) == 0, test_name, msg or f"Found {len(cycles)} cycles")

    def assert_has_unreachable(self, result: dict, test_name: str = "", msg: str = ""):
        """Assert analysis finds unreachable code"""
        unreachable = result.get('unreachable', [])
        return self.assert_true(len(unreachable) > 0, test_name, msg or "No unreachable code found")

    def assert_stats(self, result: dict, key: str, expected: int,
                    test_name: str = "", msg: str = ""):
        """Assert a specific stat value"""
        stats = result.get('stats', {})
        actual = stats.get(key, 0)
        return self.assert_true(
            actual == expected,
            test_name,
            msg or f"Expected {key}={expected}, got {actual}"
        )

    def assert_invariant_violation(self, result: dict, test_name: str = "", msg: str = ""):
        """Assert analysis finds invariant violations"""
        violations = result.get('invariant_violations', [])
        return self.assert_true(len(violations) > 0, test_name, msg or "No invariant violations found")

    def summary(self) -> str:
        """Return test summary"""
        total = self.passed + self.failed
        result = f"\n{'='*60}\n"
        result += f"Analyzer Tests: {self.passed}/{total} passed"
        if self.failed > 0:
            result += f" ({self.failed} failed)"
            result += "\n\nFailures:\n"
            for error in self.errors:
                result += f"  {error}\n"
        result += f"{'='*60}\n"
        return result


def run_basic_analysis_tests(suite: AnalyzerTestSuite):
    """Test basic analysis functionality"""
    print("\n--- Basic Analysis Tests ---")

    # Test Taxi.htn analysis
    result = analyze_file(os.path.join(suite.examples_dir, 'Taxi.htn'))
    suite.assert_has_nodes(result, test_name="Taxi.htn has nodes")
    suite.assert_true(
        result.get('stats', {}).get('methods', 0) > 0,
        "Taxi.htn has methods"
    )
    suite.assert_true(
        result.get('stats', {}).get('operators', 0) > 0,
        "Taxi.htn has operators"
    )
    suite.assert_true(
        len(result.get('initial_facts', [])) > 0,
        "Taxi.htn has initial facts"
    )

    # Test Game.htn analysis
    result = analyze_file(os.path.join(suite.examples_dir, 'Game.htn'))
    suite.assert_has_nodes(result, test_name="Game.htn has nodes")
    suite.assert_true(
        result.get('stats', {}).get('methods', 0) > 5,
        "Game.htn has multiple methods"
    )


def run_cycle_detection_tests(suite: AnalyzerTestSuite):
    """Test cycle detection"""
    print("\n--- Cycle Detection Tests ---")

    # Direct cycle
    result = analyze_file(os.path.join(suite.error_tests_dir, 'semantic_cycle_direct.htn'))
    suite.assert_detects_cycle(result, test_name="Detects direct cycle")

    # Indirect cycle
    result = analyze_file(os.path.join(suite.error_tests_dir, 'semantic_cycle_indirect.htn'))
    suite.assert_detects_cycle(result, test_name="Detects indirect cycle")

    # No cycle in Taxi.htn
    result = analyze_file(os.path.join(suite.examples_dir, 'Taxi.htn'))
    suite.assert_no_cycles(result, test_name="Taxi.htn has no cycles")


def run_dead_code_tests(suite: AnalyzerTestSuite):
    """Test dead code detection"""
    print("\n--- Dead Code Detection Tests ---")

    # Dead operator
    result = analyze_file(os.path.join(suite.error_tests_dir, 'semantic_dead_operator.htn'))
    suite.assert_has_unreachable(result, test_name="Detects dead operator")

    # Dead method
    result = analyze_file(os.path.join(suite.error_tests_dir, 'semantic_dead_method.htn'))
    suite.assert_has_unreachable(result, test_name="Detects dead method")


def run_call_graph_tests(suite: AnalyzerTestSuite):
    """Test call graph construction"""
    print("\n--- Call Graph Tests ---")

    # Test call graph edges
    source = """
    main() :- if(), do(step1(), step2()).
    step1() :- if(), do(action1()).
    step2() :- if(), do(action2()).
    action1() :- del(), add(done1).
    action2() :- del(), add(done2).
    """
    result = analyze_htn(source)

    nodes = result.get('nodes', {})
    suite.assert_true('main/0' in nodes, "main/0 node exists")
    suite.assert_true('step1/0' in nodes, "step1/0 node exists")
    suite.assert_true('action1/0' in nodes, "action1/0 node exists")

    # Check edges
    if 'main/0' in nodes:
        calls = nodes['main/0'].get('calls', [])
        suite.assert_true('step1/0' in calls, "main calls step1")
        suite.assert_true('step2/0' in calls, "main calls step2")


def run_state_flow_tests(suite: AnalyzerTestSuite):
    """Test state flow analysis"""
    print("\n--- State Flow Tests ---")

    source = """
    move(?from, ?to) :- del(at(?from)), add(at(?to)).
    pickup(?item) :- del(on-ground(?item)), add(holding(?item)).
    at(home).
    """
    result = analyze_htn(source)

    state_changes = result.get('state_changes', {})
    suite.assert_true('move/2' in state_changes, "move/2 has state changes")

    if 'move/2' in state_changes:
        changes = state_changes['move/2']
        suite.assert_true(len(changes.get('deletes', [])) > 0, "move deletes facts")
        suite.assert_true(len(changes.get('adds', [])) > 0, "move adds facts")


def run_invariant_tests(suite: AnalyzerTestSuite):
    """Test invariant checking"""
    print("\n--- Invariant Tests ---")

    # Custom invariant that should trigger
    def check_no_teleport(op_name, deletes, adds, facts, config):
        if 'teleport' in op_name.lower():
            return "Teleportation is not allowed"
        return None

    invariant = StateInvariant(
        InvariantDefinition(
            id='no_teleport',
            name='No Teleport',
            description='Teleportation operators are forbidden',
            category='test'
        ),
        check_no_teleport
    )

    source = """
    travel(?dest) :- if(at(?here)), do(teleport(?here, ?dest)).
    teleport(?from, ?to) :- del(at(?from)), add(at(?to)).
    at(home).
    """

    from htn_analyzer import HtnAnalyzer
    analyzer = HtnAnalyzer(source)
    result = analyzer.analyze([invariant])

    suite.assert_invariant_violation(
        result.to_dict(),
        test_name="Custom invariant detects violation"
    )


def run_statistics_tests(suite: AnalyzerTestSuite):
    """Test statistics computation"""
    print("\n--- Statistics Tests ---")

    source = """
    m1() :- if(), do(op1()).
    m2() :- if(), do(op2()).
    op1() :- del(), add(done1).
    op2() :- del(), add(done2).
    fact1.
    fact2.
    fact3.
    """
    result = analyze_htn(source)

    suite.assert_stats(result, 'methods', 2, test_name="Counts methods correctly")
    suite.assert_stats(result, 'operators', 2, test_name="Counts operators correctly")
    suite.assert_stats(result, 'facts', 3, test_name="Counts facts correctly")


def main():
    """Run all analyzer tests"""
    import argparse

    parser = argparse.ArgumentParser(description='Run HTN analyzer tests')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    args = parser.parse_args()

    suite = AnalyzerTestSuite(verbose=args.verbose)

    print("HTN Analyzer Test Suite")
    print("=" * 60)

    run_basic_analysis_tests(suite)
    run_cycle_detection_tests(suite)
    run_dead_code_tests(suite)
    run_call_graph_tests(suite)
    run_state_flow_tests(suite)
    run_invariant_tests(suite)
    run_statistics_tests(suite)

    print(suite.summary())

    return 0 if suite.failed == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
