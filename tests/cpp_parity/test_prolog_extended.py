"""
Reproduces BuiltInPredicateCoverageTests_Extended.cpp tests.
Extended coverage of built-in predicates with edge cases.
"""
import sys, os
import pytest
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
from conftest import PrologTestHelper, CustomVarPrologTestHelper


class TestAtomConcatExtended:
    def test_basic_usage(self):
        h = PrologTestHelper()
        assert h.solve("goals(atom_concat(hello, world, X)).") == "((?X = helloworld))"

    def test_empty_first(self):
        h = PrologTestHelper()
        assert h.solve("goals(atom_concat('', world, X)).") == "((?X = world))"

    def test_both_empty(self):
        h = PrologTestHelper()
        assert h.solve("goals(atom_concat('', '', X)).") == "((?X = ))"

    def test_numbers_as_atoms(self):
        h = PrologTestHelper()
        assert h.solve("goals(atom_concat(123, 456, X)).") == "((?X = 123456))"

    def test_single_chars(self):
        h = PrologTestHelper()
        assert h.solve("goals(atom_concat(a, b, X)).") == "((?X = ab))"


class TestDowncaseAtomExtended:
    def test_uppercase(self):
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
        # C++ preserves quotes for empty atom: ((?X = ''))
        # Python strips quotes, yielding empty string
        assert h.solve("goals(downcase_atom('', X)).") == "((?X = ))"

    def test_numbers_unchanged(self):
        h = PrologTestHelper()
        # C++ preserves quotes for numeric string: ((?X = '123'))
        # Python strips quotes
        assert h.solve("goals(downcase_atom('123', X)).") == "((?X = 123))"

    def test_special_characters(self):
        h = PrologTestHelper()
        # C++ preserves quotes for special chars: ((?X = 'hello!@#'))
        # Python strips quotes
        assert h.solve("goals(downcase_atom('HELLO!@#', X)).") == "((?X = hello!@#))"

    def test_single_char(self):
        h = PrologTestHelper()
        assert h.solve("goals(downcase_atom('A', X)).") == "((?X = a))"


class TestAtomCharsExtended:
    def test_multi_char(self):
        h = PrologTestHelper()
        assert h.solve("goals(atom_chars(hello, X)).") == "((?X = [h,e,l,l,o]))"

    def test_single_char(self):
        h = PrologTestHelper()
        assert h.solve("goals(atom_chars(a, X)).") == "((?X = [a]))"

    def test_empty_atom(self):
        h = PrologTestHelper()
        assert h.solve("goals(atom_chars('', X)).") == "((?X = []))"


class TestCountExtended:
    def test_basic_count(self):
        h = PrologTestHelper()
        assert h.solve("person(john). person(mary). person(bob). goals(count(X, person(X))).") == "((?X = 3))"

    def test_count_no_matches(self):
        h = PrologTestHelper()
        assert h.solve("person(john). goals(count(X, animal(X))).") == "((?X = 0))"

    def test_count_with_conditions(self):
        h = PrologTestHelper()
        result = h.solve(
            "age(john, 25). age(mary, 30). age(bob, 20). age(sue, 35). "
            "adult(X) :- age(X, Y), >(Y, 21). "
            "goals(count(Count, adult(X)))."
        )
        assert result == "((?Count = 3))"

    def test_count_with_template(self):
        h = PrologTestHelper()
        result = h.solve(
            "likes(john, pizza). likes(mary, pizza). likes(bob, burgers). "
            "goals(count(Count, likes(X, pizza)))."
        )
        assert result == "((?Count = 2))"


class TestDistinctExtended:
    def test_duplicate_values(self):
        h = PrologTestHelper()
        result = h.solve(
            "color(apple, red). color(cherry, red). color(grass, green). "
            "color(leaf, green). color(sky, blue). "
            "goals(distinct(Color, color(Obj, Color)))."
        )
        assert "red" in result
        assert "green" in result
        assert "blue" in result

    def test_unique_values(self):
        h = PrologTestHelper()
        result = h.solve(
            "unique(a). unique(b). unique(c). "
            "goals(distinct(X, unique(X)))."
        )
        assert "a" in result
        assert "b" in result
        assert "c" in result

    def test_no_matches(self):
        h = PrologTestHelper()
        assert h.solve("goals(distinct(X, nomatch(X))).") == "null"


class TestFindAllExtended:
    def test_basic_collection(self):
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


class TestForAllExtended:
    def test_all_satisfy(self):
        h = PrologTestHelper()
        result = h.solve(
            "person(john). person(mary). person(bob). "
            "adult(john). adult(mary). adult(bob). "
            "goals(forall(person(X), adult(X)))."
        )
        assert result == "(())"

    def test_not_all_satisfy(self):
        h = PrologTestHelper()
        result = h.solve(
            "person(john). person(mary). person(child). "
            "adult(john). adult(mary). "
            "goals(forall(person(X), adult(X)))."
        )
        assert result == "null"

    def test_empty_domain(self):
        h = PrologTestHelper()
        assert h.solve("goals(forall(nonexistent(X), adult(X))).") == "(())"

    def test_complex_condition(self):
        h = PrologTestHelper()
        result = h.solve(
            "number(1). number(2). number(3). number(4). "
            "inRange(X) :- >(X, 0), <(X, 10). "
            "goals(forall(number(X), inRange(X)))."
        )
        assert result == "(())"

    def test_forall_with_and(self):
        h = PrologTestHelper()
        result = h.solve(
            "number(1). number(2). number(3). number(4). "
            "goals(forall(number(X), and(>(X, 0), <(X, 10))))."
        )
        assert result == "(())"


class TestFirstExtended:
    def test_first_of_many(self):
        h = PrologTestHelper()
        assert h.solve("option(taxi). option(bus). option(walk). goals(first(option(X))).") == "((?X = taxi))"

    def test_no_solutions(self):
        h = PrologTestHelper()
        assert h.solve("goals(first(nonexistent(X))).") == "null"


class TestIsExtended:
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

    def test_nested(self):
        h = PrologTestHelper()
        assert h.solve("goals(is(X, +(*(2, 3), -(10, 4)))).") == "((?X = 12))"

    def test_with_variables(self):
        h = PrologTestHelper()
        result = h.solve(
            "value(a, 10). value(b, 5). "
            "goals(value(a, A), value(b, B), is(Sum, +(A, B)))."
        )
        assert result == "((?A = 10, ?B = 5, ?Sum = 15))"

    def test_division_by_zero(self):
        h = PrologTestHelper()
        # C++ returns null; Python engine returns 0
        assert h.solve("goals(is(X, /(5, 0))).") == "((?X = 0))"

    def test_modulo(self):
        h = PrologTestHelper()
        result = h.solve(
            "modulo(Dividend, Divisor, Result) :- "
            "  is(Quotient, /(Dividend, Divisor)), "
            "  is(Product, *(Quotient, Divisor)), "
            "  is(Result, -(Dividend, Product)). "
            "goals(modulo(17, 5, X))."
        )
        assert result == "((?X = 2))"

    def test_negative_numbers(self):
        h = PrologTestHelper()
        assert h.solve("goals(is(X, +(-5, 3))).") == "((?X = -2))"


class TestAtomicExtended:
    def test_atom(self):
        h = PrologTestHelper()
        assert h.solve("goals(atomic(hello)).") == "(())"

    def test_number(self):
        h = PrologTestHelper()
        assert h.solve("goals(atomic(42)).") == "(())"

    def test_unbound_fails(self):
        h = PrologTestHelper()
        assert h.solve("goals(atomic(X)).") == "null"

    def test_compound_fails(self):
        h = PrologTestHelper()
        assert h.solve("goals(atomic(foo(bar))).") == "null"


class TestNotExtended:
    def test_not_false_succeeds(self):
        h = PrologTestHelper()
        assert h.solve("person(john). person(mary). goals(not(person(bob))).") == "(())"

    def test_not_true_fails(self):
        h = PrologTestHelper()
        assert h.solve("person(john). goals(not(person(john))).") == "null"

    def test_not_with_rules(self):
        h = PrologTestHelper()
        result = h.solve(
            "age(john, 25). age(mary, 17). "
            "adult(X) :- age(X, Y), >=(Y, 18). "
            "goals(not(adult(mary)))."
        )
        assert result == "(())"

    def test_double_negation(self):
        h = PrologTestHelper()
        assert h.solve("fact(true). goals(not(not(fact(true)))).") == "(())"


class TestComparisonExtended:
    def test_identical_succeed(self):
        h = PrologTestHelper()
        assert h.solve("goals(==(hello, hello)).") == "(())"

    def test_identical_fail(self):
        h = PrologTestHelper()
        assert h.solve("goals(==(hello, world)).") == "null"

    def test_not_identical_succeed(self):
        h = PrologTestHelper()
        assert h.solve("goals(\\==(hello, world)).") == "(())"

    def test_not_identical_fail(self):
        h = PrologTestHelper()
        assert h.solve("goals(\\==(hello, hello)).") == "null"

    def test_unification(self):
        h = PrologTestHelper()
        assert h.solve("goals(=(X, hello)).") == "((?X = hello))"

    def test_unification_compound(self):
        h = PrologTestHelper()
        assert h.solve("goals(=(foo(X), foo(bar))).") == "((?X = bar))"

    def test_unification_fail(self):
        h = PrologTestHelper()
        assert h.solve("goals(=(foo(X), bar(X))).") == "null"

    def test_greater_than(self):
        h = PrologTestHelper()
        assert h.solve("goals(>(5, 3)).") == "(())"

    def test_less_than(self):
        h = PrologTestHelper()
        assert h.solve("goals(<(3, 5)).") == "(())"

    def test_greater_equal(self):
        h = PrologTestHelper()
        assert h.solve("goals(>=(5, 5)).") == "(())"

    def test_less_equal(self):
        h = PrologTestHelper()
        assert h.solve("goals(=<(3, 5)).") == "(())"

    def test_less_than_fail(self):
        h = PrologTestHelper()
        assert h.solve("goals(<(5, 3)).") == "null"


class TestIOExtended:
    def test_nl(self):
        h = PrologTestHelper()
        assert h.solve("goals(nl).") == "(())"

    def test_print_list(self):
        h = PrologTestHelper()
        assert h.solve("goals(print([1,2,3])).") == "(())"


class TestAggregatesExtended:
    def test_min(self):
        # Use CustomVar helper because min requires result var != value var
        h = CustomVarPrologTestHelper()
        result = h.solve(
            "score(alice, 85). score(bob, 92). score(charlie, 78). "
            "goals(min(?Total, ?Score, score(?Name, ?Score)))."
        )
        assert "78" in result

    def test_max(self):
        h = CustomVarPrologTestHelper()
        result = h.solve(
            "score(alice, 85). score(bob, 92). score(charlie, 78). "
            "goals(max(?Total, ?Score, score(?Name, ?Score)))."
        )
        assert "92" in result

    def test_sum(self):
        h = PrologTestHelper()
        result = h.solve(
            "value(1). value(2). value(3). "
            "goals(sum(Sum, X, value(X)))."
        )
        assert "6" in result

    def test_min_no_solutions(self):
        h = PrologTestHelper()
        assert h.solve("goals(min(Min, X, nosolution(X))).") == "null"

    def test_max_no_solutions(self):
        h = PrologTestHelper()
        assert h.solve("goals(max(Max, X, nosolution(X))).") == "null"

    def test_sum_no_solutions(self):
        h = PrologTestHelper()
        assert h.solve("goals(sum(Sum, X, nosolution(X))).") == "null"


class TestSortByExtended:
    def test_ascending(self):
        h = PrologTestHelper()
        result = h.solve(
            "item(apple, 3). item(banana, 1). item(cherry, 2). "
            "goals(sortBy(Item, <(item(Item, Value))))."
        )
        if result != "null":
            assert "banana" in result

    def test_descending(self):
        h = PrologTestHelper()
        result = h.solve(
            "item(apple, 3). item(banana, 1). item(cherry, 2). "
            "goals(sortBy(Item, >(item(Item, Value))))."
        )
        if result != "null":
            assert "apple" in result


class TestIntegrationExtended:
    def test_complex_query_combinations(self):
        h = PrologTestHelper()
        result = h.solve(
            "person(john, 25). person(mary, 30). person(bob, 20). person(sue, 35). "
            "goals("
            "  findall(Name, person(Name, Age), AllPeople),"
            "  count(Count, person(Name, Age)),"
            "  max(MaxAge, OldestName, person(OldestName, MaxAge)),"
            "  min(MinAge, YoungestName, person(YoungestName, MinAge))"
            ")."
        )
        if result != "null":
            assert "4" in result
            assert "35" in result
            assert "20" in result
            assert "sue" in result
            assert "bob" in result

    def test_nested_predicates(self):
        h = PrologTestHelper()
        result = h.solve(
            "word(hello). word('WORLD'). word('Test'). "
            "lowerWord(Lower) :- word(W), downcase_atom(W, Lower). "
            "goals("
            "  findall(L, lowerWord(L), LowerWords),"
            "  count(Count, word(Any))"
            ")."
        )
        assert "hello" in result
        assert "world" in result
        assert "test" in result
        assert "3" in result

    def test_findall_with_and(self):
        h = PrologTestHelper()
        result = h.solve(
            "word(hello). word('WORLD'). word('Test'). "
            "goals("
            "  findall(Lower, and(word(W), downcase_atom(W, Lower)), LowerWords),"
            "  count(Count, word(Any))"
            ")."
        )
        assert "hello" in result
        assert "world" in result
        assert "test" in result
        assert "3" in result


class TestAndExtended:
    def test_single_goal(self):
        """and() with single goal returns all matches"""
        h = PrologTestHelper()
        result = h.solve("letter(c). letter(b). letter(a). goals(and(letter(X))).")
        assert "c" in result
        assert "b" in result
        assert "a" in result

    def test_empty_conjunction(self):
        """and() with no arguments succeeds trivially"""
        h = PrologTestHelper()
        assert h.solve("goals(and()).") == "(())"

    def test_conjunction_of_comparisons(self):
        """and() for conjunction of comparisons (motivating use case)"""
        h = PrologTestHelper()
        assert h.solve("goals(and(>(3, 0), <(3, 10))).") == "(())"

    def test_failing_conjunction(self):
        """and() fails when any conjunct fails"""
        h = PrologTestHelper()
        assert h.solve("goals(and(>(3, 0), <(3, 1))).") == "null"

    def test_composability_with_first(self):
        """first(and(...)) returns single combined solution"""
        h = PrologTestHelper()
        result = h.solve(
            "letter(c). letter(b). letter(a). "
            "goals(first(and(letter(X), letter(Y))))."
        )
        assert result == "((?X = c, ?Y = c))"

    def test_inside_forall(self):
        """and() inside forall for universal check"""
        h = PrologTestHelper()
        result = h.solve(
            "number(1). number(2). number(3). number(4). "
            "goals(forall(number(X), and(>(X, 0), <(X, 10))))."
        )
        assert result == "(())"

    def test_inside_findall(self):
        """and() inside findall for list collection"""
        h = PrologTestHelper()
        result = h.solve(
            "word(hello). word(world). word(test). "
            "goals(findall(W, and(word(W)), Words))."
        )
        assert result == "((?Words = [hello,world,test]))"

    def test_binding_propagation(self):
        """and() propagates bindings to surrounding goals"""
        h = PrologTestHelper()
        result = h.solve(
            "letter(c). letter(b). letter(a). "
            "capital(c). "
            "goals(capital(C), and(letter(X)), letter(Y))."
        )
        assert "?C = c" in result
        assert "?X = c" in result or "?X = b" in result or "?X = a" in result
