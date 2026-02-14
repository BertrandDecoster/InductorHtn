"""
Reproduces HtnGoalResolverTests_Core.cpp tests.
Tests core Prolog features: recursion, unification, lists.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
from conftest import PrologTestHelper


class TestRecursion:
    def test_generate(self):
        h = PrologTestHelper()
        assert h.solve("gen(Cur, Top, Cur) :- <(Cur, Top). gen(Cur, Top, Next):- <(Cur, Top), is(Cur1, +(Cur, 1)), gen(Cur1, Top, Next). goals(gen(0, 5, Num)).") == "((?Num = 0), (?Num = 1), (?Num = 2), (?Num = 3), (?Num = 4))"


class TestUnifierOperator:
    def test_fail(self):
        h = PrologTestHelper()
        assert h.solve("trace(x) :- . goals( =(mia, vincent) ).") == "null"

    def test_success(self):
        h = PrologTestHelper()
        assert h.solve("trace(x) :- . goals( =(X, vincent) ).") == "((?X = vincent))"

    def test_with_goals(self):
        h = PrologTestHelper()
        assert h.solve("letter(c). letter(b). letter(a). capital(c). capital(b). capital(a). cost(c, 1). cost(b, 2). cost(a, 3). highCost(3). trace(x) :- . goals( letter(X), =(Y, X), cost(Y, Cost) ).") == "((?X = c, ?Y = c, ?Cost = 1), (?X = b, ?Y = b, ?Cost = 2), (?X = a, ?Y = a, ?Cost = 3))"

    def test_compound(self):
        h = PrologTestHelper()
        assert h.solve("letter(c). letter(b). letter(a). capital(c). capital(b). capital(a). cost(c, 1). cost(b, 2). cost(a, 3). highCost(3). trace(x) :- . goals( =(Y, letter(X)), =(capital(X), Z) ).") == "((?Y = letter(X), ?Z = capital(X)))"


class TestLists:
    def test_split(self):
        h = PrologTestHelper()
        assert h.solve("split([Head | Tail], Head, Tail). goals(split([a, b, c, d], Head, Tail)).") == "((?Tail = [b,c,d], ?Head = a))"

    def test_member(self):
        h = PrologTestHelper()
        assert h.solve("member(X, [X|_]). member(X, [_|Tail]) :- member(X, Tail). goals( member(a, [b, c, a, [d, e, f]]), not(member(d, [b, c, a, [d, e, f]])) ).") == "(())"

    def test_append(self):
        h = PrologTestHelper()
        assert h.solve("append([], Ys, Ys). append([X|Xs], Ys, [X|Zs]) :- append(Xs, Ys, Zs). goals( append(ListLeft, ListRight, [a, b, c]) ).") == "((?ListRight = [a,b,c], ?ListLeft = []), (?ListLeft = [a], ?ListRight = [b,c]), (?ListLeft = [a,b], ?ListRight = [c]), (?ListLeft = [a,b,c], ?ListRight = []))"

    def test_reverse(self):
        h = PrologTestHelper()
        assert h.solve("append([], Ys, Ys). append([X|Xs], Ys, [X|Zs]) :- append(Xs, Ys, Zs). reverse([]  ,[]). reverse([X|Xs],YsX) :- reverse(Xs,Ys), append(Ys,[X],YsX). goals( reverse([a, b, foo(a, [a, b, c])], X) ).") == "((?X = [foo(a,[a,b,c]),b,a]))"

    def test_length(self):
        h = PrologTestHelper()
        assert h.solve("len([], 0). len([_ | Tail], Length) :- len(Tail, Length1), is(Length, +(Length1, 1)),!. goals( len([[], b, foo(a, [a, b, c])], X) ).") == "((?X = 3))"
