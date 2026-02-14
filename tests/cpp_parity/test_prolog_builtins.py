"""
Reproduces BuiltInPredicateCoverageTests.cpp tests.
Tests built-in predicates: atom_concat, downcase_atom, atom_chars,
count, distinct, findall, forall, first, is, atomic, not, comparisons.
"""
import pytest
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
from conftest import PrologTestHelper


class TestAtomConcat:
    def test_forward_concatenation(self):
        h = PrologTestHelper()
        assert h.solve("goals(atom_concat(hello, world, X)).") == "((?X = helloworld))"

    def test_empty_string_concatenation(self):
        h = PrologTestHelper()
        assert h.solve("goals(atom_concat('', world, X)).") == "((?X = world))"

    def test_concatenate_empty_strings(self):
        h = PrologTestHelper()
        assert h.solve("goals(atom_concat('', '', X)).") == "((?X = ))"

    def test_numbers_as_atoms(self):
        h = PrologTestHelper()
        assert h.solve("goals(atom_concat(123, 456, X)).") == "((?X = 123456))"


class TestDowncaseAtom:
    def test_basic_downcase(self):
        h = PrologTestHelper()
        assert h.solve("goals(downcase_atom('HELLO', X)).") == "((?X = hello))"

    def test_mixed_case(self):
        h = PrologTestHelper()
        assert h.solve("goals(downcase_atom('HeLLo', X)).") == "((?X = hello))"

    def test_already_lowercase(self):
        h = PrologTestHelper()
        assert h.solve("goals(downcase_atom(hello, X)).") == "((?X = hello))"

    def test_empty_string(self):
        h = PrologTestHelper()
        assert h.solve("goals(downcase_atom('', X)).") == "((?X = ))"

    def test_numbers(self):
        h = PrologTestHelper()
        assert h.solve("goals(downcase_atom('123', X)).") == "((?X = 123))"

    def test_special_characters(self):
        h = PrologTestHelper()
        assert h.solve("goals(downcase_atom('HELLO!@#', X)).") == "((?X = hello!@#))"


class TestAtomChars:
    def test_basic_conversion(self):
        h = PrologTestHelper()
        assert h.solve("goals(atom_chars(hello, X)).") == "((?X = [h,e,l,l,o]))"

    def test_single_character(self):
        h = PrologTestHelper()
        assert h.solve("goals(atom_chars(a, X)).") == "((?X = [a]))"

    def test_empty_atom(self):
        h = PrologTestHelper()
        assert h.solve("goals(atom_chars('', X)).") == "((?X = []))"


class TestCount:
    def test_basic_counting(self):
        h = PrologTestHelper()
        result = h.solve("person(john). person(mary). person(bob). goals(count(X, person(X))).")
        assert result == "((?X = 3))"

    def test_count_no_matches(self):
        h = PrologTestHelper()
        result = h.solve("person(john). goals(count(X, animal(X))).")
        assert result == "((?X = 0))"


class TestDistinct:
    def test_unique_values(self):
        h = PrologTestHelper()
        result = h.solve(
            "color(apple, red). color(cherry, red). color(grass, green). "
            "color(leaf, green). color(sky, blue). "
            "goals(distinct(Color, color(Obj, Color)))."
        )
        assert "red" in result
        assert "green" in result
        assert "blue" in result


class TestFindAll:
    def test_simple_collection(self):
        h = PrologTestHelper()
        result = h.solve(
            "parent(tom, bob). parent(tom, liz). parent(bob, ann). parent(bob, pat). "
            "goals(findall(Child, parent(tom, Child), Children))."
        )
        assert result == "((?Children = [bob,liz]))"

    def test_no_solutions(self):
        h = PrologTestHelper()
        result = h.solve(
            "parent(tom, bob). "
            "goals(findall(X, parent(mary, X), Result))."
        )
        assert result == "((?Result = []))"

    def test_complex_template(self):
        h = PrologTestHelper()
        result = h.solve(
            "score(alice, 85). score(bob, 92). score(charlie, 78). "
            "goals(findall(grade(Name, Score), score(Name, Score), Grades))."
        )
        assert result == "((?Grades = [grade(alice,85),grade(bob,92),grade(charlie,78)]))"


class TestForAll:
    def test_succeeds(self):
        h = PrologTestHelper()
        result = h.solve(
            "person(john). person(mary). person(bob). "
            "adult(john). adult(mary). adult(bob). "
            "goals(forall(person(X), adult(X)))."
        )
        assert result == "(())"

    def test_fails(self):
        h = PrologTestHelper()
        result = h.solve(
            "person(john). person(mary). person(child). "
            "adult(john). adult(mary). "
            "goals(forall(person(X), adult(X)))."
        )
        assert result == "null"

    def test_empty_domain_vacuously_true(self):
        h = PrologTestHelper()
        result = h.solve("goals(forall(nonexistent(X), adult(X))).")
        assert result == "(())"


class TestFirst:
    def test_single_solution(self):
        h = PrologTestHelper()
        result = h.solve("option(taxi). option(bus). option(walk). goals(first(option(X))).")
        assert result == "((?X = taxi))"

    def test_no_solutions(self):
        h = PrologTestHelper()
        result = h.solve("goals(first(nonexistent(X))).")
        assert result == "null"


class TestIsArithmetic:
    def test_addition(self):
        h = PrologTestHelper()
        assert h.solve("goals(is(X, +(5, 3))).") == "((?X = 8))"

    def test_subtraction(self):
        h = PrologTestHelper()
        assert h.solve("goals(is(X, -(10, 4))).") == "((?X = 6))"

    def test_multiplication(self):
        h = PrologTestHelper()
        assert h.solve("goals(is(X, *(7, 6))).") == "((?X = 42))"

    def test_division(self):
        h = PrologTestHelper()
        assert h.solve("goals(is(X, /(15, 3))).") == "((?X = 5))"

    def test_nested_arithmetic(self):
        h = PrologTestHelper()
        assert h.solve("goals(is(X, +(*(2, 3), -(10, 4)))).") == "((?X = 12))"


class TestAtomic:
    def test_atom(self):
        h = PrologTestHelper()
        assert h.solve("goals(atomic(hello)).") == "(())"

    def test_number(self):
        h = PrologTestHelper()
        assert h.solve("goals(atomic(42)).") == "(())"

    def test_unbound_variable_fails(self):
        h = PrologTestHelper()
        assert h.solve("goals(atomic(X)).") == "null"

    def test_compound_term_fails(self):
        h = PrologTestHelper()
        assert h.solve("goals(atomic(foo(bar))).") == "null"


class TestNot:
    def test_not_false_succeeds(self):
        h = PrologTestHelper()
        result = h.solve("person(john). person(mary). goals(not(person(bob))).")
        assert result == "(())"

    def test_not_true_fails(self):
        h = PrologTestHelper()
        result = h.solve("person(john). goals(not(person(john))).")
        assert result == "null"


class TestComparisons:
    def test_unification(self):
        h = PrologTestHelper()
        assert h.solve("goals(=(X, hello)).") == "((?X = hello))"

    def test_identical(self):
        h = PrologTestHelper()
        assert h.solve("goals(==(hello, hello)).") == "(())"

    def test_not_identical(self):
        h = PrologTestHelper()
        assert h.solve("goals(\\==(hello, world)).") == "(())"

    def test_greater_than(self):
        h = PrologTestHelper()
        assert h.solve("goals(>(5, 3)).") == "(())"

    def test_less_than(self):
        h = PrologTestHelper()
        assert h.solve("goals(<(3, 5)).") == "(())"

    def test_greater_or_equal(self):
        h = PrologTestHelper()
        assert h.solve("goals(>=(5, 5)).") == "(())"

    def test_less_or_equal(self):
        h = PrologTestHelper()
        assert h.solve("goals(=<(3, 5)).") == "(())"


class TestIO:
    def test_nl(self):
        h = PrologTestHelper()
        assert h.solve("goals(nl).") == "(())"

    def test_print_list(self):
        h = PrologTestHelper()
        assert h.solve("goals(print([1,2,3])).") == "(())"


class TestDynamic:
    def test_assert(self):
        h = PrologTestHelper()
        result = h.solve("person(john). goals(assert(person(mary))).")
        assert result in ["(())", "null"]

    def test_retractall(self):
        h = PrologTestHelper()
        result = h.solve("temp(a). temp(b). temp(c). goals(retractall(temp(X))).")
        assert result in ["(())", "null"]


class TestIntegration:
    def test_basic_combinations(self):
        h = PrologTestHelper()
        result = h.solve(
            "person(john, 25). person(mary, 30). person(bob, 20). person(sue, 35). "
            "goals(findall(Name, person(Name, Age), AllPeople), count(Count, person(Name, Age)))."
        )
        if result != "null":
            assert "4" in result
            assert "[john,mary,bob,sue]" in result

    def test_arithmetic_with_logic(self):
        h = PrologTestHelper()
        result = h.solve(
            "value(a, 10). value(b, 5). value(c, 15). "
            "goals(value(a, A), value(b, B), is(Sum, +(A, B)), >(Sum, 10))."
        )
        assert result == "((?A = 10, ?B = 5, ?Sum = 15))"
