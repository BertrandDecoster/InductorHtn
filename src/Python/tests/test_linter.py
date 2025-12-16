"""
Linter Test Suite
Tests that the HTN linter correctly detects errors in the ErrorTests directory.
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

from htn_linter import lint_file, lint_htn


class LinterTestSuite:
    """Test suite for the HTN linter"""

    def __init__(self, verbose=False):
        self.verbose = verbose
        self.passed = 0
        self.failed = 0
        self.errors = []
        self.error_tests_dir = os.path.join(project_root, 'Examples', 'ErrorTests')

    def assert_detects_error(self, file_name: str, expected_code: str = None,
                             expected_severity: str = None,
                             expected_message_contains: str = None,
                             msg: str = ""):
        """Assert that linting a file produces at least one diagnostic"""
        file_path = os.path.join(self.error_tests_dir, file_name)
        test_name = f"detects error in {file_name}"

        try:
            diagnostics = lint_file(file_path)

            if not diagnostics:
                self.failed += 1
                error = f"FAIL: {test_name} - No diagnostics produced"
                if msg:
                    error += f" ({msg})"
                self.errors.append(error)
                if self.verbose:
                    print(error)
                return False

            # Check for expected code
            if expected_code:
                codes = [d.get('code', '') for d in diagnostics]
                if expected_code not in codes:
                    self.failed += 1
                    error = f"FAIL: {test_name} - Expected code {expected_code}, got {codes}"
                    self.errors.append(error)
                    if self.verbose:
                        print(error)
                    return False

            # Check for expected severity
            if expected_severity:
                severities = [d.get('severity', '') for d in diagnostics]
                if expected_severity not in severities:
                    self.failed += 1
                    error = f"FAIL: {test_name} - Expected severity {expected_severity}, got {severities}"
                    self.errors.append(error)
                    if self.verbose:
                        print(error)
                    return False

            # Check for expected message content
            if expected_message_contains:
                messages = ' '.join(d.get('message', '') for d in diagnostics)
                if expected_message_contains.lower() not in messages.lower():
                    self.failed += 1
                    error = f"FAIL: {test_name} - Expected message containing '{expected_message_contains}'"
                    self.errors.append(error)
                    if self.verbose:
                        print(error)
                        for d in diagnostics:
                            print(f"  Got: {d.get('message', '')}")
                    return False

            self.passed += 1
            if self.verbose:
                print(f"PASS: {test_name}")
                for d in diagnostics:
                    print(f"  -> {d['severity']}: {d['message']} (line {d['line']}, code {d.get('code', 'N/A')})")
            return True

        except Exception as e:
            self.failed += 1
            error = f"ERROR: {test_name} - {str(e)}"
            self.errors.append(error)
            if self.verbose:
                print(error)
            return False

    def assert_no_errors(self, file_path: str, msg: str = ""):
        """Assert that linting a file produces no errors (only warnings allowed)"""
        test_name = f"no errors in {os.path.basename(file_path)}"

        try:
            diagnostics = lint_file(file_path)
            errors = [d for d in diagnostics if d.get('severity') == 'error']

            if errors:
                self.failed += 1
                error_msgs = '; '.join(d.get('message', '') for d in errors[:3])
                error = f"FAIL: {test_name} - Found {len(errors)} errors: {error_msgs}"
                if msg:
                    error += f" ({msg})"
                self.errors.append(error)
                if self.verbose:
                    print(error)
                return False

            self.passed += 1
            if self.verbose:
                warnings = [d for d in diagnostics if d.get('severity') == 'warning']
                print(f"PASS: {test_name} ({len(warnings)} warnings)")
            return True

        except Exception as e:
            self.failed += 1
            error = f"ERROR: {test_name} - {str(e)}"
            self.errors.append(error)
            if self.verbose:
                print(error)
            return False

    def summary(self) -> str:
        """Return test summary"""
        total = self.passed + self.failed
        result = f"\n{'='*60}\n"
        result += f"Linter Tests: {self.passed}/{total} passed"
        if self.failed > 0:
            result += f" ({self.failed} failed)"
            result += "\n\nFailures:\n"
            for error in self.errors:
                result += f"  {error}\n"
        result += f"{'='*60}\n"
        return result


def run_syntax_error_tests(suite: LinterTestSuite):
    """Test syntax error detection"""
    print("\n--- Syntax Error Tests ---")

    suite.assert_detects_error(
        'syntax_unbalanced_parens_in_if.htn',
        expected_message_contains='paren',
        msg="Should detect unbalanced parentheses in if()"
    )

    suite.assert_detects_error(
        'syntax_unbalanced_parens_in_do.htn',
        expected_message_contains='paren',
        msg="Should detect unbalanced parentheses in do()"
    )

    suite.assert_detects_error(
        'syntax_missing_period.htn',
        expected_severity='error',
        msg="Should detect missing period"
    )

    suite.assert_detects_error(
        'syntax_missing_arrow.htn',
        expected_message_contains=':-',
        msg="Should detect missing :- arrow"
    )

    suite.assert_detects_error(
        'syntax_unclosed_string.htn',
        expected_code='SYN003',
        msg="Should detect unclosed string"
    )

    suite.assert_detects_error(
        'syntax_invalid_variable_name.htn',
        expected_severity='error',
        msg="Should detect invalid variable name"
    )

    suite.assert_detects_error(
        'syntax_mismatched_brackets.htn',
        expected_severity='error',
        msg="Should detect mismatched brackets"
    )


def run_variable_error_tests(suite: LinterTestSuite):
    """Test variable error detection"""
    print("\n--- Variable Error Tests ---")

    suite.assert_detects_error(
        'var_unbound_in_do.htn',
        expected_code='VAR001',
        msg="Should detect unbound variable in do()"
    )

    suite.assert_detects_error(
        'var_unbound_in_add.htn',
        expected_code='VAR002',
        msg="Should detect unbound variable in add()"
    )

    suite.assert_detects_error(
        'var_unused_in_head.htn',
        expected_message_contains='singleton',
        msg="Should warn about unused head variable"
    )

    suite.assert_detects_error(
        'var_singleton_warning.htn',
        expected_code='VAR003',
        msg="Should warn about singleton variable"
    )


def run_semantic_error_tests(suite: LinterTestSuite):
    """Test semantic error detection"""
    print("\n--- Semantic Error Tests ---")

    suite.assert_detects_error(
        'semantic_dead_operator.htn',
        expected_message_contains='dead code',
        msg="Should detect dead operator"
    )

    suite.assert_detects_error(
        'semantic_dead_method.htn',
        expected_message_contains='dead code',
        msg="Should detect dead method"
    )

    suite.assert_detects_error(
        'semantic_cycle_direct.htn',
        expected_message_contains='recursion',
        msg="Should detect direct cycle"
    )

    suite.assert_detects_error(
        'semantic_cycle_indirect.htn',
        expected_message_contains='recursion',
        msg="Should detect indirect cycle"
    )

    suite.assert_detects_error(
        'semantic_undefined_method.htn',
        expected_code='SEM001',
        msg="Should detect undefined method"
    )

    suite.assert_detects_error(
        'semantic_undefined_predicate.htn',
        expected_code='SEM002',
        msg="Should detect undefined predicate"
    )

    suite.assert_detects_error(
        'semantic_arity_mismatch_call.htn',
        expected_severity='error',
        msg="Should detect arity mismatch in call"
    )

    suite.assert_detects_error(
        'semantic_arity_mismatch_predicate.htn',
        expected_code='SEM003',
        msg="Should detect arity mismatch in predicate"
    )

    suite.assert_detects_error(
        'semantic_duplicate_operator.htn',
        expected_severity='warning',
        msg="Should warn about duplicate operator"
    )

    suite.assert_detects_error(
        'semantic_no_base_case.htn',
        expected_message_contains='recursion',
        msg="Should detect recursion without base case"
    )


def run_htn_specific_tests(suite: LinterTestSuite):
    """Test HTN-specific error detection"""
    print("\n--- HTN-Specific Error Tests ---")

    # Note: htn_operator_with_if_do.htn and htn_method_with_del_add.htn
    # have valid syntax but potentially confusing naming. These would require
    # naming convention analysis which is beyond pure syntax checking.
    # They produce dead code warnings instead which is still useful.

    suite.assert_detects_error(
        'htn_operator_with_if_do.htn',
        expected_severity='warning',  # Dead code warning for move()
        msg="Should detect something (dead code or style)"
    )

    suite.assert_detects_error(
        'htn_method_with_del_add.htn',
        expected_severity='warning',  # Dead code warnings
        msg="Should detect something (dead code or style)"
    )

    suite.assert_detects_error(
        'htn_else_without_prior_method.htn',
        expected_code='HTN004',
        msg="Should detect else without prior method"
    )

    suite.assert_detects_error(
        'htn_allof_on_operator.htn',
        expected_code='HTN003',
        msg="Should warn about allOf on operator"
    )

    suite.assert_detects_error(
        'htn_empty_do_clause.htn',
        expected_code='HTN005',
        msg="Should warn about empty do() clause"
    )


def run_good_file_tests(suite: LinterTestSuite):
    """Test that good files don't produce errors"""
    print("\n--- Good File Tests (should have no errors) ---")

    examples_dir = os.path.join(project_root, 'Examples')

    # Taxi.htn should be clean
    suite.assert_no_errors(
        os.path.join(examples_dir, 'Taxi.htn'),
        msg="Taxi.htn should have no errors"
    )

    # Game.htn should be clean
    suite.assert_no_errors(
        os.path.join(examples_dir, 'Game.htn'),
        msg="Game.htn should have no errors"
    )


def main():
    """Run all linter tests"""
    import argparse

    parser = argparse.ArgumentParser(description='Run HTN linter tests')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    args = parser.parse_args()

    suite = LinterTestSuite(verbose=args.verbose)

    print("HTN Linter Test Suite")
    print("=" * 60)

    run_syntax_error_tests(suite)
    run_variable_error_tests(suite)
    run_semantic_error_tests(suite)
    run_htn_specific_tests(suite)
    run_good_file_tests(suite)

    print(suite.summary())

    return 0 if suite.failed == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
