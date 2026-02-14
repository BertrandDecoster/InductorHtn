"""
Reproduces HtnGoalResolverTests_Meta.cpp tests.
Tests meta-predicates: cut, assert/retract, findall, min, max, sum, distinct, count.

Uses CustomVarPrologTestHelper because C++ tests use ?-prefix variable syntax
with uppercase atom constants (Name1, Name2, Bad, One, etc.).
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
from conftest import CustomVarPrologTestHelper


class TestCut:
    def test_fail_before_cut(self):
        h = CustomVarPrologTestHelper()
        assert h.solve("rule(?X) :- itemsInBag(?X), !. rule(?X) :- =(?X, good). trace(x) :- . goals( rule(?X) ).") == "((?X = good))"

    def test_cut_succeeds(self):
        h = CustomVarPrologTestHelper()
        assert h.solve("itemsInBag(Name1). itemsInBag(Name2). rule(?X) :- itemsInBag(?X), !. rule(?X) :- =(?X, Bad). trace(x) :- . goals( rule(?X) ).") == "((?X = Name1))"

    def test_cut_with_backtrack_after(self):
        h = CustomVarPrologTestHelper()
        result = h.solve("itemsInBag(Name1). itemsInBag(Name2). itemsInPurse(lipstick). itemsInPurse(tissues). rule(?X, ?Y) :- itemsInBag(?X), !, itemsInPurse(?Y). rule(?X, ?Y) :- =(?X, Bad), =(?Y, Bad). trace(x) :- . goals( rule(?X, ?Y) ).")
        assert result == "((?X = Name1, ?Y = lipstick), (?X = Name1, ?Y = tissues))"

    def test_two_cuts(self):
        h = CustomVarPrologTestHelper()
        result = h.solve("itemsInBag(Name1). itemsInBag(Name2). itemsInPurse(lipstick). itemsInPurse(tissues). rule(?X, ?Y) :- itemsInBag(?X), !, itemsInPurse(?Y), !. rule(?X, ?Y) :- =(?X, Bad), =(?Y, Bad). trace(x) :- . goals( rule(?X, ?Y) ).")
        assert result == "((?X = Name1, ?Y = lipstick))"

    def test_cut_at_beginning(self):
        h = CustomVarPrologTestHelper()
        result = h.solve("itemsInBag(Name1). itemsInBag(Name2). itemsInPurse(lipstick). itemsInPurse(tissues). rule(?X, ?Y) :- itemsInBag(?X), itemsInPurse(?Y). rule(?X, ?Y) :- !. rule(?X, ?Y) :- =(?X, Bad), =(?Y, Bad). trace(x) :- . goals( rule(?X, ?Y) ).")
        assert result == "((?X = Name1, ?Y = lipstick), (?X = Name1, ?Y = tissues), (?X = Name2, ?Y = lipstick), (?X = Name2, ?Y = tissues), ())"

    def test_cut_in_initial_goals(self):
        h = CustomVarPrologTestHelper()
        result = h.solve("itemsInBag(Name1). itemsInBag(Name2). goals( itemsInBag(?X), ! ).")
        assert result == "((?X = Name1))"


class TestAssertRetract:
    def test_assert(self):
        h = CustomVarPrologTestHelper()
        result = h.solve("itemsInBag(Name1). itemsInBag(Name2). trace(x) :- . goals( assert(itemsInBag(Name3)), itemsInBag(?After) ).")
        assert result == "((?After = Name1), (?After = Name2), (?After = Name3))"

    def test_assert_with_variable(self):
        h = CustomVarPrologTestHelper()
        result = h.solve("itemsInBag(Name1). itemsInBag(Name2). rule(?X) :- assert(itemsInBag(?X)). trace(x) :- . goals( rule(Name3), itemsInBag(?After) ).")
        assert result == "((?After = Name1), (?After = Name2), (?After = Name3))"

    def test_retract(self):
        h = CustomVarPrologTestHelper()
        result = h.solve("itemsInBag(Name1). itemsInBag(Name2). trace(x) :- . goals( retract(itemsInBag(Name1)), itemsInBag(?After) ).")
        assert result == "((?After = Name2))"

    def test_retract_with_variable(self):
        h = CustomVarPrologTestHelper()
        result = h.solve("itemsInBag(Name1). itemsInBag(Name2). rule(?X) :- retract(itemsInBag(?X)). trace(x) :- . goals( rule(Name1), itemsInBag(?After) ).")
        assert result == "((?After = Name2))"

    def test_retractall(self):
        h = CustomVarPrologTestHelper()
        result = h.solve("itemsInBag(Name1). itemsInBag(Name2). goals( retractall(itemsInBag(?X)) ).")
        assert result == "(())"

    def test_retract_nonexistent(self):
        h = CustomVarPrologTestHelper()
        result = h.solve("itemsInBag(Name1). itemsInBag(Name2). goals( retract(itemsInBag(Name3)) ).")
        assert result == "null"


class TestFindAll:
    def test_no_solutions(self):
        h = CustomVarPrologTestHelper()
        result = h.solve("child(martha,charlotte). child(charlotte,caroline). child(caroline,laura). child(laura,rose). descend(?X,?Y) :- child(?X,?Y). descend(?X,?Y) :- child(?X,?Z), descend(?Z,?Y). trace(x) :- . goals( findall(?X,descend(rose,?X),?Z) ).")
        assert result == "((?Z = []))"

    def test_simple(self):
        h = CustomVarPrologTestHelper()
        result = h.solve("child(martha,charlotte). child(charlotte,caroline). child(caroline,laura). child(laura,rose). descend(?X,?Y) :- child(?X,?Y). descend(?X,?Y) :- child(?X,?Z), descend(?Z,?Y). trace(x) :- . goals( child(charlotte, ?A), findall(?X,descend(martha,?X),?Z), child(?A, ?B) ).")
        assert result == "((?A = caroline, ?Z = [charlotte,caroline,laura,rose], ?B = laura))"

    def test_complex_template(self):
        h = CustomVarPrologTestHelper()
        result = h.solve("child(martha,charlotte). child(charlotte,caroline). child(caroline,laura). child(laura,rose). descend(?X,?Y) :- child(?X,?Y). descend(?X,?Y) :- child(?X,?Z), descend(?Z,?Y). trace(x) :- . goals( findall(fromMartha(?X),descend(martha,?X),?Z) ).")
        assert result == "((?Z = [fromMartha(charlotte),fromMartha(caroline),fromMartha(laura),fromMartha(rose)]))"

    def test_unify_list(self):
        h = CustomVarPrologTestHelper()
        result = h.solve("child(martha,charlotte). child(charlotte,caroline). child(caroline,laura). child(laura,rose). descend(?X,?Y) :- child(?X,?Y). descend(?X,?Y) :- child(?X,?Z), descend(?Z,?Y). trace(x) :- . goals( findall(?X,descend(laura,?X),[?Z]) ).")
        assert result == "((?Z = rose))"


class TestMin:
    def test_no_solutions(self):
        h = CustomVarPrologTestHelper()
        assert h.solve("trace(x) :- . goals( min(?Total, ?ItemCount, itemsInBag(?Name, ?ItemCount)) ).") == "null"

    def test_wrong_variable(self):
        h = CustomVarPrologTestHelper()
        assert h.solve("itemsInBag(Name1, 1). itemsInBag(Name2, 2). trace(x) :- . goals( min(?Total, ?NotThere, itemsInBag(?Name, ?ItemCount)) ).") == "null"

    def test_success(self):
        h = CustomVarPrologTestHelper()
        assert h.solve("itemsInBag(Name1, 1). itemsInBag(Name2, 2). trace(x) :- . goals( min(?Total, ?ItemCount, itemsInBag(?Name, ?ItemCount)) ).") == "((?Total = 1))"

    def test_with_other_goals(self):
        h = CustomVarPrologTestHelper()
        assert h.solve("itemsInBag(Name1, 1). itemsInBag(Name2, 2). countToString(1, One). trace(x) :- . goals( itemsInBag(Name1, ?X), min(?Total, ?ItemCount, itemsInBag(?Name, ?ItemCount)), countToString(?X, ?Name) ).") == "((?X = 1, ?Total = 1, ?Name = One))"


class TestMax:
    def test_no_solutions(self):
        h = CustomVarPrologTestHelper()
        assert h.solve("trace(x) :- . goals( max(?Total, ?ItemCount, itemsInBag(?Name, ?ItemCount)) ).") == "null"

    def test_wrong_variable(self):
        h = CustomVarPrologTestHelper()
        assert h.solve("itemsInBag(Name1, 1). itemsInBag(Name2, 2). trace(x) :- . goals( max(?Total, ?NotThere, itemsInBag(?Name, ?ItemCount)) ).") == "null"

    def test_success(self):
        h = CustomVarPrologTestHelper()
        assert h.solve("itemsInBag(Name1, 1). itemsInBag(Name2, 2). trace(x) :- . goals( max(?Total, ?ItemCount, itemsInBag(?Name, ?ItemCount)) ).") == "((?Total = 2))"

    def test_with_other_goals(self):
        h = CustomVarPrologTestHelper()
        assert h.solve("itemsInBag(Name1, 1). itemsInBag(Name2, 2). countToString(1, One). trace(x) :- . goals( itemsInBag(Name1, ?X), max(?Total, ?ItemCount, itemsInBag(?Name, ?ItemCount)), countToString(?X, ?Name) ).") == "((?X = 1, ?Total = 2, ?Name = One))"


class TestSum:
    def test_no_solutions(self):
        h = CustomVarPrologTestHelper()
        assert h.solve("trace(x) :- . goals( sum(?Total, ?ItemCount, itemsInBag(?Name, ?ItemCount)) ).") == "null"

    def test_wrong_variable(self):
        h = CustomVarPrologTestHelper()
        assert h.solve("itemsInBag(Name1, 1). itemsInBag(Name2, 2). trace(x) :- . goals( sum(?Total, ?NotThere, itemsInBag(?Name, ?ItemCount)) ).") == "null"

    def test_success(self):
        h = CustomVarPrologTestHelper()
        assert h.solve("itemsInBag(Name1, 1). itemsInBag(Name2, 2). trace(x) :- . goals( sum(?Total, ?ItemCount, itemsInBag(?Name, ?ItemCount)) ).") == "((?Total = 3))"

    def test_with_other_goals(self):
        h = CustomVarPrologTestHelper()
        assert h.solve("itemsInBag(Name1, 1). itemsInBag(Name2, 2). countToString(1, One). trace(x) :- . goals( itemsInBag(Name1, ?X), sum(?Total, ?ItemCount, itemsInBag(?Name, ?ItemCount)), countToString(?X, ?Name) ).") == "((?X = 1, ?Total = 3, ?Name = One))"


class TestDistinct:
    def test_no_variables(self):
        h = CustomVarPrologTestHelper()
        # Use _ (not ?_) for anonymous variable
        assert h.solve("letter(c). letter(b). letter(a). test(_) :- letter(_). trace(x) :- . goals( distinct(_, test(_)) ).") == "(())"

    def test_single_variable(self):
        h = CustomVarPrologTestHelper()
        assert h.solve("letter(c). letter(b). letter(a). trace(x) :- . goals( distinct(_, letter(?X)) ).") == "((?X = c), (?X = b), (?X = a))"

    def test_with_domain(self):
        h = CustomVarPrologTestHelper()
        assert h.solve("letter(c). letter(b). letter(a). trace(x) :- . goals( distinct(?X, letter(?X)) ).") == "((?X = c), (?X = b), (?X = a))"

    def test_multiple_with_domain(self):
        h = CustomVarPrologTestHelper()
        assert h.solve("letter(c). letter(b). letter(a). trace(x) :- . goals( distinct(?X, letter(?X), letter(?Y)) ).") == "((?X = c, ?Y = c), (?X = b, ?Y = c), (?X = a, ?Y = c))"


class TestCount:
    def test_no_matches(self):
        h = CustomVarPrologTestHelper()
        assert h.solve("letter(c). letter(b). letter(a). trace(x) :- . goals( count(?Count, capitol(?X)) ).") == "((?Count = 0))"

    def test_matches(self):
        h = CustomVarPrologTestHelper()
        assert h.solve("letter(c). letter(b). letter(a). capital(c). capital(b). capital(a). cost(c, 1). cost(b, 2). cost(a, 3). trace(x) :- . goals( count(?Count, letter(?X)) ).") == "((?Count = 3))"

    def test_in_math(self):
        h = CustomVarPrologTestHelper()
        assert h.solve("letter(c). letter(b). letter(a). capital(c). capital(b). capital(a). cost(c, 1). cost(b, 2). cost(a, 3). trace(x) :- . goals( count(?Count, letter(?X)), is(?Result, *(1, ?Count)) ).") == "((?Count = 3, ?Result = 3))"
