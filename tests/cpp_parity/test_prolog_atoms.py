"""
Reproduces HtnGoalResolverTests_Atoms.cpp tests.
Tests atom handling: atomic/1, true, false.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
from conftest import PrologTestHelper


class TestAtomicPredicate:
    def test_atom(self):
        h = PrologTestHelper()
        assert h.solve("goals(atomic(mia)).") == "(())"

    def test_compound_zero_arg(self):
        h = PrologTestHelper()
        assert h.solve("goals(atomic(mia())).") == "(())"

    def test_int(self):
        h = PrologTestHelper()
        assert h.solve("goals(atomic(8)).") == "(())"

    def test_float(self):
        h = PrologTestHelper()
        assert h.solve("goals(atomic(3.25)).") == "(())"

    def test_compound_fails(self):
        h = PrologTestHelper()
        assert h.solve("goals(atomic(loves(vincent, mia))).") == "null"

    def test_unbound_fails(self):
        h = PrologTestHelper()
        assert h.solve("goals(atomic(X)).") == "null"

    def test_bound(self):
        h = PrologTestHelper()
        assert h.solve("goals(=(X, mia), atomic(X)).") == "((?X = mia))"


class TestTrueFalse:
    def test_true(self):
        h = PrologTestHelper()
        assert h.solve("goals( true ).") == "(())"

    def test_false(self):
        h = PrologTestHelper()
        assert h.solve("goals( false ).") == "null"
