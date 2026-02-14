"""
Reproduces HtnGoalResolverTests_Comparison.cpp tests.
Tests comparison and control flow: sortBy, ==, \\==, is, not, first, print.

Uses CustomVarPrologTestHelper because C++ tests use ?-prefix variable syntax
with uppercase atom constants (A, B, ComboA, ComboB, etc.).
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
from conftest import CustomVarPrologTestHelper


class TestSortBy:
    def test_failure(self):
        h = CustomVarPrologTestHelper()
        assert h.solve("letter(c). letter(b). letter(a). trace(x) :- . goals(sortBy(?C, <(letter(?X), capital(?X), cost(?X, ?C)))).") == "null"

    def test_success(self):
        h = CustomVarPrologTestHelper()
        assert h.solve("letter(c). letter(b). letter(a). capital(c). capital(b). capital(a). cost(c, 1). cost(b, 2). cost(a, 3). trace(x) :- . goals(sortBy(?C, <(letter(?X), capital(?X), cost(?X, ?C)))).") == "((?X = c, ?C = 1), (?X = b, ?C = 2), (?X = a, ?C = 3))"

    def test_with_other_goals(self):
        h = CustomVarPrologTestHelper()
        assert h.solve("letter(c). letter(b). letter(a). capital(c). capital(b). capital(a). cost(c, 1). cost(b, 2). cost(a, 3). highCost(3). trace(x) :- . goals(highCost(?HighCost), sortBy(?C, <(letter(?X), capital(?X), cost(?X, ?C))), highCost(?C)).") == "((?HighCost = 3, ?X = a, ?C = 3))"


class TestIdentical:
    def test_fail(self):
        h = CustomVarPrologTestHelper()
        assert h.solve("goals(==(letter(a), letter(b))).") == "null"

    def test_success(self):
        h = CustomVarPrologTestHelper()
        assert h.solve("goals( ==(letter(a), letter(a)) ).") == "(())"

    def test_with_variables(self):
        h = CustomVarPrologTestHelper()
        assert h.solve("letter(c). letter(B). letter(A). capital(B). capital(A). trace(x) :- . goals(==(letter(?X), letter(?X))).") == "(())"

    def test_numbers(self):
        h = CustomVarPrologTestHelper()
        assert h.solve("letter(c). letter(B). letter(A). capital(B). capital(A). trace(x) :- . goals(==(0, 0)).") == "(())"

    def test_with_unification(self):
        h = CustomVarPrologTestHelper()
        assert h.solve("letter(c). letter(B). letter(A). capital(B). capital(A). combo(A, X). combo(B, Y). trace(x) :- . goals(capital(?Capital), letter(?X), ==(?X, ?Capital), combo(?X, ?Combo)).") == "((?Capital = B, ?X = B, ?Combo = Y), (?Capital = A, ?X = A, ?Combo = X))"

    def test_with_unification_v2(self):
        h = CustomVarPrologTestHelper()
        assert h.solve("letter(c). letter(B). letter(A). capital(B). capital(A). combo(A, ComboA). combo(B, ComboB). trace(x) :- . goals(capital(?Capital), letter(?X), ==(?X, ?Capital), combo(?X, ?Combo)).") == "((?Capital = B, ?X = B, ?Combo = ComboB), (?Capital = A, ?X = A, ?Combo = ComboA))"

    def test_not_identical_fail(self):
        h = CustomVarPrologTestHelper()
        assert h.solve("goals(\\==(letter(a), letter(a))).") == "null"

    def test_not_identical_success(self):
        h = CustomVarPrologTestHelper()
        assert h.solve("goals(\\==(letter(a), letter(b))).") == "(())"

    def test_not_identical_with_other(self):
        h = CustomVarPrologTestHelper()
        assert h.solve("letter(c). letter(B). letter(A). capital(B). capital(A). combo(A, ComboA). combo(B, ComboB). trace(x) :- . goals(capital(?Capital), \\==(letter(?Capital), letter(B)), combo(?Capital, ?Combo)).") == "((?Capital = A, ?Combo = ComboA))"


class TestIs:
    def test_equality(self):
        h = CustomVarPrologTestHelper()
        assert h.solve("goals(is(1, 1)).") == "(())"

    def test_arithmetic_equality(self):
        h = CustomVarPrologTestHelper()
        assert h.solve("goals(is(+(1, 1), +(0, 2))).") == "(())"

    def test_unify(self):
        h = CustomVarPrologTestHelper()
        assert h.solve("goals(is(?X, 1)).") == "((?X = 1))"

    def test_arithmetic(self):
        h = CustomVarPrologTestHelper()
        assert h.solve("goals(is(?X, +(1,2))).") == "((?X = 3))"

    def test_with_bound(self):
        h = CustomVarPrologTestHelper()
        assert h.solve("goals(=(?X, 5), is(?X, 5)).") == "((?X = 5))"

    def test_mismatch(self):
        h = CustomVarPrologTestHelper()
        assert h.solve("goals(=(?X, a), is(?X, 5)).") == "null"


class TestNot:
    def test_not_false(self):
        h = CustomVarPrologTestHelper()
        assert h.solve("letter(c). letter(b). letter(a). trace(x) :- . goals(not(letter(a))).") == "null"

    def test_not_true(self):
        h = CustomVarPrologTestHelper()
        assert h.solve("letter(c). letter(b). letter(a). trace(x) :- . goals(not(letter(d))).") == "(())"

    def test_not_with_goals(self):
        h = CustomVarPrologTestHelper()
        assert h.solve("letter(c). letter(b). letter(a). capital(A). trace(x) :- . goals(capital(?Capital), not(letter(d)), letter(?y)).") == "((?Capital = A, ?y = c), (?Capital = A, ?y = b), (?Capital = A, ?y = a))"

    def test_not_with_variable(self):
        h = CustomVarPrologTestHelper()
        assert h.solve("letter(c). letter(b). letter(a). option(c). option(d). option(e). trace(x) :- . goals(option(?x), not(letter(?x)), letter(?y)).") == "((?x = d, ?y = c), (?x = d, ?y = b), (?x = d, ?y = a), (?x = e, ?y = c), (?x = e, ?y = b), (?x = e, ?y = a))"


class TestFirst:
    def test_first(self):
        h = CustomVarPrologTestHelper()
        assert h.solve("letter(c). letter(b). letter(a). trace(x) :- . goals(first(letter(?x))).") == "((?x = c))"

    def test_first_with_other(self):
        h = CustomVarPrologTestHelper()
        assert h.solve("letter(c). letter(b). letter(a). capital(A). trace(x) :- . goals(capital(?Capital), first(letter(?x)), letter(?y)).") == "((?Capital = A, ?x = c, ?y = c), (?Capital = A, ?x = c, ?y = b), (?Capital = A, ?x = c, ?y = a))"

    def test_nested_first(self):
        h = CustomVarPrologTestHelper()
        assert h.solve("letter(c). letter(b). letter(a). capital(A). trace(x) :- . goals(first(capital(?Capital), first(letter(?x)), letter(?y))).") == "((?Capital = A, ?x = c, ?y = c))"


class TestPrint:
    def test_print(self):
        h = CustomVarPrologTestHelper()
        assert h.solve("letter(c). letter(b). letter(A). capital(A). trace(x) :- . goals(letter(?X), print(?X), capital(?X)).") == "((?X = A))"
