//
//  HtnGoalResolverTests_Comparison.cpp
//  TestLib
//
//  Comparison, logic, and advanced features: sortBy, identical, is, not, first, print, fatal errors, resolve, custom predicates
//
//  Created by Eric Zinda on 9/25/18.
//  Copyright (c) 2018 Eric Zinda. All rights reserved.
//

#include <iostream>
#include "FXPlatform/Logger.h"
#include "FXPlatform/Prolog/HtnGoalResolver.h"
#include "FXPlatform/Prolog/HtnRuleSet.h"
#include "FXPlatform/Prolog/HtnTerm.h"
#include "FXPlatform/Prolog/HtnTermFactory.h"
#include "FXPlatform/Prolog/PrologParser.h"
#include "FXPlatform/Prolog/PrologCompiler.h"
#include "Tests/ParserTestBase.h"
#include "UnitTest++/UnitTest++.h"
using namespace Prolog;

// Helper functions for these tests
namespace {
    bool IsFalse(shared_ptr<vector<UnifierType>> result)
    {
        return result == nullptr;
    }

    bool IsTrue(shared_ptr<vector<UnifierType>> result)
    {
        return result != nullptr && result->size() == 1 && (*result)[0].size() == 0;
    }

    bool CheckSolution(UnifierType solution, UnifierType expectedSolution)
    {
        if(solution.size() != expectedSolution.size()) return false;
        for(pair<shared_ptr<HtnTerm>, shared_ptr<HtnTerm>> expected : expectedSolution)
        {
            UnifierType::iterator solutionIter;
            for(solutionIter = solution.begin(); solutionIter != solution.end(); ++solutionIter)
            {
                if(*expected.first == *solutionIter->first && *expected.second == *solutionIter->second)
                {
                    break;
                }
            }

            if(solutionIter != solution.end())
            {
                solution.erase(solutionIter);
                continue;
            }
            else
            {
                break;
            }
        }

        return(solution.size() == 0);
    }

    bool CheckSolutions(vector<UnifierType> solution, vector<UnifierType> expectedSolution)
    {
        for(auto expected : expectedSolution)
        {
            bool found = false;
            for(vector<UnifierType>::iterator foundIter = solution.begin(); foundIter != solution.end(); ++foundIter)
            {
                if(CheckSolution(*foundIter, expected))
                {
                    solution.erase(foundIter);
                    found = true;
                    break;
                }
            }

            if(!found)
            {
                return false;
            }
        }

        return solution.size() == 0;
    }
}

SUITE(HtnGoalResolverTests)
{
    TEST(HtnGoalResolverSortByTests)
    {
        HtnGoalResolver resolver;
        shared_ptr<HtnTermFactory> factory = shared_ptr<HtnTermFactory>(new HtnTermFactory());
        shared_ptr<HtnRuleSet> state = shared_ptr<HtnRuleSet>(new HtnRuleSet());
        shared_ptr<PrologCompiler> compiler = shared_ptr<PrologCompiler>(new PrologCompiler(factory.get(), state.get()));
        string testState;
        string goals;
        string finalUnifier;
        shared_ptr<vector<UnifierType>> unifier;

        //        SetTraceFilter((int)SystemTraceType::Solver | (int) SystemTraceType::Unifier,  TraceDetail::Diagnostic);
//        SetTraceFilter( (int)SystemTraceType::Solver,  TraceDetail::Diagnostic);

        // ***** single sortBy() goal where all items fail
        compiler->Clear();
        testState = string() +
        "letter(c). letter(b). letter(a).\r\n" +
        "trace(?x) :- .\r\n"
        "goals(sortBy(?C, <(letter(?X), capital(?X), cost(?X, ?C)))).\r\n";
        CHECK(compiler->Compile(testState));
        unifier = compiler->SolveGoals();
        finalUnifier = HtnGoalResolver::ToString(unifier.get());
        CHECK_EQUAL(finalUnifier, "null");

        // ***** single sortBy() goal where all items succeed
        compiler->Clear();
        testState = string() +
        "letter(c). letter(b). letter(a).\r\n" +
        "capital(c). capital(b). capital(a).\r\n" +
        "cost(c, 1). cost(b, 2). cost(a, 3).\r\n" +
        "trace(?x) :- .\r\n"
        "goals(sortBy(?C, <(letter(?X), capital(?X), cost(?X, ?C)))).\r\n";
        CHECK(compiler->Compile(testState));
        unifier = compiler->SolveGoals();
        finalUnifier = HtnGoalResolver::ToString(unifier.get());
        CHECK_EQUAL(finalUnifier, "((?X = c, ?C = 1), (?X = b, ?C = 2), (?X = a, ?C = 3))");

        // ***** single sortBy() goal that is preceeded and succeeded by more goals to make sure unifiers flow through properly
        compiler->Clear();
        testState = string() +
        "letter(c). letter(b). letter(a).\r\n" +
        "capital(c). capital(b). capital(a).\r\n" +
        "cost(c, 1). cost(b, 2). cost(a, 3).\r\n" +
        "highCost(3).\r\n" +
        "trace(?x) :- .\r\n"
        "goals(highCost(?HighCost), sortBy(?C, <(letter(?X), capital(?X), cost(?X, ?C))), highCost(?C)).\r\n";
        CHECK(compiler->Compile(testState));
        unifier = compiler->SolveGoals();
        finalUnifier = HtnGoalResolver::ToString(unifier.get());
        CHECK_EQUAL(finalUnifier, "((?HighCost = 3, ?X = a, ?C = 3))");
    }

    TEST(HtnGoalResolverIdenticalTests)
    {
        HtnGoalResolver resolver;
        shared_ptr<HtnTermFactory> factory = shared_ptr<HtnTermFactory>(new HtnTermFactory());
        shared_ptr<HtnRuleSet> state = shared_ptr<HtnRuleSet>(new HtnRuleSet());
        shared_ptr<PrologCompiler> compiler = shared_ptr<PrologCompiler>(new PrologCompiler(factory.get(), state.get()));
        string testState;
        string goals;
        string finalUnifier;
        shared_ptr<vector<UnifierType>> unifier;

//        SetTraceFilter( (int)SystemTraceType::Solver,  TraceDetail::Diagnostic);

        // ***** single ==() goal that fails
        compiler->Clear();
        testState = string() +
        "goals(==(letter(a), letter(b))).\r\n";
        CHECK(compiler->Compile(testState));
        unifier = compiler->SolveGoals();
        finalUnifier = HtnGoalResolver::ToString(unifier.get());
        CHECK_EQUAL(finalUnifier, "null");

        // ***** single ==() goal that succeeds
        compiler->Clear();
        testState = string() +
        "goals( ==(letter(a), letter(a)) ).\r\n";
        CHECK(compiler->Compile(testState));
        unifier = compiler->SolveGoals();
        finalUnifier = HtnGoalResolver::ToString(unifier.get());
        CHECK_EQUAL(finalUnifier, "(())");

        // ***** single ==() goal with variables that are the same.
        // They aren't resolved so there are no variables in the unifier, just checked for being identical
        compiler->Clear();
        testState = string() +
        "letter(c). letter(B). letter(A).\r\n" +
        "capital(B). capital(A).\r\n" +
        "trace(?x) :- .\r\n"
        "goals(==(letter(?X), letter(?X))).\r\n";
        CHECK(compiler->Compile(testState));
        unifier = compiler->SolveGoals();
        finalUnifier = HtnGoalResolver::ToString(unifier.get());
        CHECK_EQUAL(finalUnifier, "(())");

        // ***** single ==() goal with arithmetic terms.
        compiler->Clear();
        testState = string() +
        "letter(c). letter(B). letter(A).\r\n" +
        "capital(B). capital(A).\r\n" +
        "trace(?x) :- .\r\n"
        "goals(==(0, 0)).\r\n";
        CHECK(compiler->Compile(testState));
        unifier = compiler->SolveGoals();
        finalUnifier = HtnGoalResolver::ToString(unifier.get());
        CHECK_EQUAL(finalUnifier, "(())");

        // ***** make sure variables that have been unified compare their values, not just the variable name
        // ***** single ==() goal preceeded and followed by other goals to make sure unifiers flow through properly
        compiler->Clear();
        testState = string() +
        "letter(c). letter(B). letter(A).\r\n" +
        "capital(B). capital(A).\r\n" +
        "combo(A, X). combo(B, Y).\r\n"
        "trace(?x) :- .\r\n"
        "goals(capital(?Capital), letter(?X), ==(?X, ?Capital), combo(?X, ?Combo)).\r\n";
        CHECK(compiler->Compile(testState));
        unifier = compiler->SolveGoals();
        finalUnifier = HtnGoalResolver::ToString(unifier.get());
        CHECK_EQUAL(finalUnifier, "((?Capital = B, ?X = B, ?Combo = Y), (?Capital = A, ?X = A, ?Combo = X))");

        // ***** make sure variables that have been unified compare their values, not just the variable name
        // ***** single ==() goal preceeded and followed by other goals to make sure unifiers flow through properly
        compiler->Clear();
        testState = string() +
        "letter(c). letter(B). letter(A).\r\n" +
        "capital(B). capital(A).\r\n" +
        "combo(A, ComboA). combo(B, ComboB).\r\n"
        "trace(?x) :- .\r\n"
        "goals(capital(?Capital), letter(?X), ==(?X, ?Capital), combo(?X, ?Combo)).\r\n";
        CHECK(compiler->Compile(testState));
        unifier = compiler->SolveGoals();
        finalUnifier = HtnGoalResolver::ToString(unifier.get());
        CHECK_EQUAL(finalUnifier, "((?Capital = B, ?X = B, ?Combo = ComboB), (?Capital = A, ?X = A, ?Combo = ComboA))");

        // ***** single \==() goal that fails
        compiler->Clear();
        testState = string() +
        "goals(\\==(letter(a), letter(a))).\r\n";
        CHECK(compiler->Compile(testState));
        unifier = compiler->SolveGoals();
        finalUnifier = HtnGoalResolver::ToString(unifier.get());
        CHECK_EQUAL(finalUnifier, "null");

        // ***** single \==() goal that succeeds
        compiler->Clear();
        testState = string() +
        "goals(\\==(letter(a), letter(b))).\r\n";
        CHECK(compiler->Compile(testState));
        unifier = compiler->SolveGoals();
        finalUnifier = HtnGoalResolver::ToString(unifier.get());
        CHECK_EQUAL(finalUnifier, "(())");

        // ***** single \==() goal preceeded and followed by other goals to make sure unifiers flow through properly
        compiler->Clear();
        testState = string() +
        "letter(c). letter(B). letter(A).\r\n" +
        "capital(B). capital(A).\r\n" +
        "combo(A, ComboA). combo(B, ComboB).\r\n"
        "trace(?x) :- .\r\n"
        "goals(capital(?Capital), \\==(letter(?Capital), letter(B)), combo(?Capital, ?Combo)).\r\n";
        CHECK(compiler->Compile(testState));
        unifier = compiler->SolveGoals();
        finalUnifier = HtnGoalResolver::ToString(unifier.get());
        CHECK_EQUAL(finalUnifier, "((?Capital = A, ?Combo = ComboA))");
    }

    TEST(HtnGoalResolverIsTests)
    {
        HtnGoalResolver resolver;
        shared_ptr<HtnTermFactory> factory = shared_ptr<HtnTermFactory>(new HtnTermFactory());
        shared_ptr<HtnRuleSet> state = shared_ptr<HtnRuleSet>(new HtnRuleSet());
        shared_ptr<PrologCompiler> compiler = shared_ptr<PrologCompiler>(new PrologCompiler(factory.get(), state.get()));
        string testState;
        string goals;
        string finalUnifier;
        shared_ptr<vector<UnifierType>> unifier;

        //        SetTraceFilter((int)SystemTraceType::Solver | (int) SystemTraceType::Unifier,  TraceDetail::Diagnostic);
//        SetTraceFilter( (int)SystemTraceType::Solver,  TraceDetail::Diagnostic);

        // ***** is/2 with two arithmetic arguments succeeds
        compiler->Clear();
        testState = string() +
        "goals(is(1, 1)).\r\n";
        CHECK(compiler->Compile(testState));
        unifier = compiler->SolveGoals();
        finalUnifier = HtnGoalResolver::ToString(unifier.get());
        CHECK_EQUAL(finalUnifier, "(())");

        compiler->Clear();
        testState = string() +
        "goals(is(+(1, 1), +(0, 2))).\r\n";
        CHECK(compiler->Compile(testState));
        unifier = compiler->SolveGoals();
        finalUnifier = HtnGoalResolver::ToString(unifier.get());
        CHECK_EQUAL(finalUnifier, "(())");

        // ***** is/2 with variable lvalue and arithmetic argument unifies
        compiler->Clear();
        testState = string() +
        "goals(is(?X, 1)).\r\n";
        CHECK(compiler->Compile(testState));
        unifier = compiler->SolveGoals();
        finalUnifier = HtnGoalResolver::ToString(unifier.get());
        CHECK_EQUAL(finalUnifier, "((?X = 1))");

        compiler->Clear();
        testState = string() +
        "goals(is(?X, +(1,2))).\r\n";
        CHECK(compiler->Compile(testState));
        unifier = compiler->SolveGoals();
        finalUnifier = HtnGoalResolver::ToString(unifier.get());
        CHECK_EQUAL(finalUnifier, "((?X = 3))");

        // ***** is/2 with variable lvalue that has been set and arithmetic argument works
        compiler->Clear();
        testState = string() +
        "goals(=(?X, 5), is(?X, 5)).\r\n";
        CHECK(compiler->Compile(testState));
        unifier = compiler->SolveGoals();
        finalUnifier = HtnGoalResolver::ToString(unifier.get());
        CHECK_EQUAL(finalUnifier, "((?X = 5))");

        // ***** is/2 with variable lvalue that has been set with non-arithmetic term and arithmetic argument fails
        // but doesn't throw
        compiler->Clear();
        testState = string() +
        "goals(=(?X, a), is(?X, 5)).\r\n";
        CHECK(compiler->Compile(testState));
        unifier = compiler->SolveGoals();
        finalUnifier = HtnGoalResolver::ToString(unifier.get());
        CHECK_EQUAL(finalUnifier, "null");

        // ***** is/2 with non-arithmetic arguments throws
        bool caught = false;
        try {
            compiler->Clear();
            testState = string() +
            "goals(is(b, b)).\r\n";
            CHECK(compiler->Compile(testState));
            unifier = compiler->SolveGoals();
            finalUnifier = HtnGoalResolver::ToString(unifier.get());
            CHECK_EQUAL(finalUnifier, "null");
        }
        catch(...)
        {
            caught = true;
        }
        CHECK(caught);
    }

    TEST(HtnGoalResolverNotTests)
    {
        HtnGoalResolver resolver;
        shared_ptr<HtnTermFactory> factory = shared_ptr<HtnTermFactory>(new HtnTermFactory());
        shared_ptr<HtnRuleSet> state = shared_ptr<HtnRuleSet>(new HtnRuleSet());
        shared_ptr<PrologCompiler> compiler = shared_ptr<PrologCompiler>(new PrologCompiler(factory.get(), state.get()));
        string testState;
        string goals;
        string finalUnifier;
        shared_ptr<vector<UnifierType>> unifier;

        //        SetTraceFilter((int)SystemTraceType::Solver | (int) SystemTraceType::Unifier,  TraceDetail::Diagnostic);
//        SetTraceFilter( (int)SystemTraceType::Solver,  TraceDetail::Diagnostic);

        // ***** single not() goal that fails
        compiler->Clear();
        testState = string() +
        "letter(c). letter(b). letter(a).\r\n" +
        "trace(?x) :- .\r\n"
        "goals(not(letter(a))).\r\n";
        CHECK(compiler->Compile(testState));
        unifier = compiler->SolveGoals();
        finalUnifier = HtnGoalResolver::ToString(unifier.get());
        CHECK_EQUAL(finalUnifier, "null");

        // ***** single not() goal that succeeds
        compiler->Clear();
        testState = string() +
        "letter(c). letter(b). letter(a).\r\n" +
        "trace(?x) :- .\r\n"
        "goals(not(letter(d))).\r\n";
        CHECK(compiler->Compile(testState));
        unifier = compiler->SolveGoals();
        finalUnifier = HtnGoalResolver::ToString(unifier.get());
        CHECK_EQUAL(finalUnifier, "(())");

        // ***** single not() goal preceeded and followed by other goals to make sure unifiers flow through properly
        compiler->Clear();
        testState = string() +
        "letter(c). letter(b). letter(a).\r\n" +
        "capital(A)." +
        "trace(?x) :- .\r\n" +
        "goals(capital(?Capital), not(letter(d)), letter(?y)).\r\n";
        CHECK(compiler->Compile(testState));
        unifier = compiler->SolveGoals();
        finalUnifier = HtnGoalResolver::ToString(unifier.get());
        CHECK_EQUAL(finalUnifier, "((?Capital = A, ?y = c), (?Capital = A, ?y = b), (?Capital = A, ?y = a))");

        // ***** single not() goal filled with substitutions followed by other goals with multiple solutions
        compiler->Clear();
        testState = string() +
        "letter(c). letter(b). letter(a).\r\n" +
        "option(c). option(d). option(e).\r\n" +
        "trace(?x) :- .\r\n"
        "goals(option(?x), not(letter(?x)), letter(?y)).\r\n";
        CHECK(compiler->Compile(testState));
        unifier = compiler->SolveGoals();
        finalUnifier = HtnGoalResolver::ToString(unifier.get());
        CHECK_EQUAL(finalUnifier, "((?x = d, ?y = c), (?x = d, ?y = b), (?x = d, ?y = a), (?x = e, ?y = c), (?x = e, ?y = b), (?x = e, ?y = a))");
    }

    TEST(HtnGoalResolverFirstTests)
    {
        HtnGoalResolver resolver;
        shared_ptr<HtnTermFactory> factory = shared_ptr<HtnTermFactory>(new HtnTermFactory());
        shared_ptr<HtnRuleSet> state = shared_ptr<HtnRuleSet>(new HtnRuleSet());
        shared_ptr<PrologCompiler> compiler = shared_ptr<PrologCompiler>(new PrologCompiler(factory.get(), state.get()));
        string testState;
        string goals;
        string finalUnifier;
        shared_ptr<vector<UnifierType>> unifier;

        //        SetTraceFilter((int) SystemTraceType::Planner | (int)SystemTraceType::Solver | (int) SystemTraceType::Unifier,  TraceDetail::Diagnostic);
//        SetTraceFilter( (int)SystemTraceType::Solver,  TraceDetail::Diagnostic);

        // ***** single first() goal
        compiler->Clear();
        testState = string() +
        "letter(c). letter(b). letter(a).\r\n" +
        "trace(?x) :- .\r\n"
        "goals(first(letter(?x))).\r\n";
        CHECK(compiler->Compile(testState));
        unifier = compiler->SolveGoals();
        finalUnifier = HtnGoalResolver::ToString(unifier.get());
        CHECK_EQUAL(finalUnifier, "((?x = c))");

        // ***** single first() goal preceeded and followed by other goals to make sure unifiers flow through properly
        compiler->Clear();
        testState = string() +
        "letter(c). letter(b). letter(a).\r\n" +
        "capital(A)." +
        "trace(?x) :- .\r\n"
        "goals(capital(?Capital), first(letter(?x)), letter(?y)).\r\n";
        CHECK(compiler->Compile(testState));
        unifier = compiler->SolveGoals();
        finalUnifier = HtnGoalResolver::ToString(unifier.get());
        CHECK_EQUAL(finalUnifier, "((?Capital = A, ?x = c, ?y = c), (?Capital = A, ?x = c, ?y = b), (?Capital = A, ?x = c, ?y = a))");

        // Two firsts inside each other
        compiler->Clear();
        testState = string() +
        "letter(c). letter(b). letter(a).\r\n" +
        "capital(A)." +
        "trace(?x) :- .\r\n"
        "goals(first(capital(?Capital), first(letter(?x)), letter(?y))).\r\n";
        CHECK(compiler->Compile(testState));
        unifier = compiler->SolveGoals();
        finalUnifier = HtnGoalResolver::ToString(unifier.get());
        CHECK_EQUAL(finalUnifier, "((?Capital = A, ?x = c, ?y = c))");
    }

    TEST(HtnGoalResolverPrintTests)
    {
        HtnGoalResolver resolver;
        shared_ptr<HtnTermFactory> factory = shared_ptr<HtnTermFactory>(new HtnTermFactory());
        shared_ptr<HtnRuleSet> state = shared_ptr<HtnRuleSet>(new HtnRuleSet());
        shared_ptr<PrologCompiler> compiler = shared_ptr<PrologCompiler>(new PrologCompiler(factory.get(), state.get()));
        string testState;
        string goals;
        string finalUnifier;
        shared_ptr<vector<UnifierType>> unifier;

        //        SetTraceFilter((int) SystemTraceType::Planner | (int)SystemTraceType::Solver | (int) SystemTraceType::Unifier,  TraceDetail::Diagnostic);
//        SetTraceFilter( (int)SystemTraceType::Solver,  TraceDetail::Diagnostic);

        // ***** print goal with previous and next terms
        compiler->Clear();
        testState = string() +
        "letter(c). letter(b). letter(A).\r\n" +
        "capital(A)." +
        "trace(?x) :- .\r\n"
        "goals(letter(?X), print(?X), capital(?X)).\r\n";
        CHECK(compiler->Compile(testState));
        unifier = compiler->SolveGoals();
        finalUnifier = HtnGoalResolver::ToString(unifier.get());
        CHECK_EQUAL(finalUnifier, "((?X = A))");
    }


    TEST(HtnGoalResolverFatalErrors)
    {
        shared_ptr<HtnTermFactory> factory = shared_ptr<HtnTermFactory>(new HtnTermFactory());
        shared_ptr<HtnRuleSet> prog = shared_ptr<HtnRuleSet>(new HtnRuleSet());
        shared_ptr<HtnGoalResolver> resolver = shared_ptr<HtnGoalResolver>(new HtnGoalResolver());
        shared_ptr<vector<UnifierType>> result;

        // Program(sunny) Query(X) -> fail since X cannot be a query
        prog->ClearAll();
        prog->AddRule(factory->CreateConstant("sunny"), {});
        bool caught = false;
        try
        {
            result = resolver->ResolveAll(factory.get(), prog.get(), { factory->CreateVariable("X") });
        }
        catch(...)
        {
            caught = true;
        }
        CHECK(caught);
    }

    TEST(HtnGoalResolverResolveTests)
    {
//        SetTraceFilter(SystemTraceType::Solver, TraceDetail::Diagnostic);

        shared_ptr<HtnTermFactory> factory = shared_ptr<HtnTermFactory>(new HtnTermFactory());
        shared_ptr<HtnRuleSet> prog = shared_ptr<HtnRuleSet>(new HtnRuleSet());
        shared_ptr<HtnGoalResolver> resolver = shared_ptr<HtnGoalResolver>(new HtnGoalResolver());
        shared_ptr<vector<UnifierType>> result;

        shared_ptr<HtnTerm>variableX = factory->CreateVariable("X");
        shared_ptr<HtnTerm>variableY = factory->CreateVariable("Y");
        shared_ptr<HtnTerm>variableZ = factory->CreateVariable("Z");

        // Check the base cases where the query is just a fact
        // Program(sunny, man(billy))
        // Queries:
        //      sunny
        //      man(billy)
        // Should return non-null but empty (which means true)
        prog->AddRule(factory->CreateConstant("sunny"), {});
        prog->AddRule(factory->CreateFunctor("man", {factory->CreateConstant("billy")}), {});
        result = resolver->ResolveAll(factory.get(), prog.get(), { factory->CreateConstant("sunny") });
        CHECK(IsTrue(result));
        result = resolver->ResolveAll(factory.get(), prog.get(), { factory->CreateFunctor("man", {factory->CreateConstant("billy")}) });
        CHECK(IsTrue(result));

        // Program(weather(sunny)) Query(weather(X)) -> X = sunny
        prog->ClearAll();
        prog->AddRule(factory->CreateFunctor("weather", {factory->CreateConstant("sunny")}), {});
        result = resolver->ResolveAll(factory.get(), prog.get(), { factory->CreateFunctor("weather", { variableX }) } );
        CHECK(CheckSolutions(*result, { { UnifierItemType(variableX,  factory->CreateConstant("sunny"))} }));

        // Program(weather(sunny), weather(rainy)) Query(weather(X)) -> X = sunny; X = rainy
        prog->AddRule(factory->CreateFunctor("weather", {factory->CreateConstant("rainy")}), {});
        result = resolver->ResolveAll(factory.get(), prog.get(), { factory->CreateFunctor("weather", { variableX }) } );
        CHECK(CheckSolutions(*result, {
            { UnifierItemType(variableX,  factory->CreateConstant("sunny"))},
            { UnifierItemType(variableX,  factory->CreateConstant("rainy"))}
        }));

        // mortal(X) :- human(X)
        // human(socrates)
        // ? mortal(socrates)
        // => true
        prog->ClearAll();
        prog->AddRule(factory->CreateFunctor("mortal", {factory->CreateVariable("X") }), { factory->CreateFunctor("human", {factory->CreateVariable("X") }) });
        prog->AddRule(factory->CreateFunctor("human", {factory->CreateConstant("socrates") }), { });
        result = resolver->ResolveAll(factory.get(), prog.get(), { factory->CreateFunctor("mortal", {factory->CreateConstant("socrates") })});
        CHECK(IsTrue(result));

        // mortal(X) :- human(X)
        // human(socrates)
        // ? mortal(X)
        // => Y = socrates
        prog->ClearAll();
        prog->AddRule(factory->CreateFunctor("mortal", {factory->CreateVariable("X") }), { factory->CreateFunctor("human", {factory->CreateVariable("X") }) });
        prog->AddRule(factory->CreateFunctor("human", {factory->CreateConstant("socrates") }), { });
        result = resolver->ResolveAll(factory.get(), prog.get(), { factory->CreateFunctor("mortal", { variableX })});
        CHECK(CheckSolutions(*result, {
            { UnifierItemType(variableX,  factory->CreateConstant("socrates")) }
        }));

        //        doubleTerm(X, Y) :- term(Y)
        //        doubleTerm(a, b)
        //        term(c)
        //        Query: doubleTerm(a, X)
        //        Expected: X = b, X = c
        prog->ClearAll();
        prog->AddRule(factory->CreateFunctor("doubleTerm", { variableX, variableY }),
                      { factory->CreateFunctor("term", { variableY }) });
        prog->AddRule(factory->CreateFunctor("doubleTerm", { factory->CreateConstant("a"), factory->CreateConstant("b") }), {});
        prog->AddRule(factory->CreateFunctor("term", { factory->CreateConstant("c") }), {});
        result = resolver->ResolveAll(factory.get(), prog.get(), {factory->CreateFunctor("doubleTerm", { factory->CreateConstant("a"), variableX })});
        CHECK(CheckSolutions(*result, {
            { UnifierItemType(variableX,  factory->CreateConstant("b")) },
            { UnifierItemType(variableX,  factory->CreateConstant("c")) }
        }));

        //        grandMotherOf(X,Z) :-
        //            motherOf(X,Y),
        //            motherOf(Y,Z).
        //        motherOf(tom,judy).
        //        motherOf(judy,mary).
        //        Query: grandMotherOf(tom, X)
        prog->ClearAll();
        prog->AddRule(factory->CreateFunctor("grandMotherOf", { variableX, variableZ }),
                      { factory->CreateFunctor("motherOf", { variableX, variableY }) ,
                          factory->CreateFunctor("motherOf", { variableY, variableZ }) });
        prog->AddRule(factory->CreateFunctor("motherOf", { factory->CreateConstant("tom"), factory->CreateConstant("judy") }), {});
        prog->AddRule(factory->CreateFunctor("motherOf", { factory->CreateConstant("judy"), factory->CreateConstant("mary") }), {});
        result = resolver->ResolveAll(factory.get(), prog.get(), {factory->CreateFunctor("grandMotherOf", { factory->CreateConstant("tom"), variableX })});
        CHECK(CheckSolutions(*result, {
            { UnifierItemType(variableX,  factory->CreateConstant("mary")) }
        }));

        // Test built-in print
        prog->ClearAll();
        result = resolver->ResolveAll(factory.get(), prog.get(), { factory->CreateFunctor("print", { factory->CreateConstant("2"), factory->CreateConstant("1") })});
        CHECK(IsTrue(result));

        // Test arithmetic functions
        // X < Y
        // Query: greater(2, 1)
        prog->ClearAll();
        prog->AddRule(factory->CreateFunctor("greater", { variableX, variableY }), { factory->CreateFunctor(">", { variableX, variableY }) });
        result = resolver->ResolveAll(factory.get(), prog.get(), { factory->CreateFunctor("greater", { factory->CreateConstant("2"), factory->CreateConstant("1") })});
        CHECK(IsTrue(result));

        // Test recursion, the "is" statement and clauses and arithmetic
        // factorial(0,1).
        // factorial(N,F) :-
        //    N>0,
        //    N1 is N-1,
        //    factorial(N1,F1),
        //    F is N * F1.
        prog->ClearAll();
        prog->AddRule(factory->CreateFunctor("factorial", { factory->CreateConstant("0"), factory->CreateConstant("1") }), {});
        shared_ptr<HtnTerm>term1 = factory->CreateFunctor(">", { factory->CreateVariable("N"), factory->CreateConstant("0") });
        shared_ptr<HtnTerm>term2 = factory->CreateFunctor("is", { factory->CreateVariable("N1"),
                                                       factory->CreateFunctor("-", { factory->CreateVariable("N"), factory->CreateConstant("1") }) });
        shared_ptr<HtnTerm>term3 = factory->CreateFunctor("factorial", { factory->CreateVariable("N1"), factory->CreateVariable("F1") });
        shared_ptr<HtnTerm>term4 = factory->CreateFunctor("is", { factory->CreateVariable("F"),
            factory->CreateFunctor("-", { factory->CreateVariable("N"), factory->CreateVariable("F1") }) });
        prog->AddRule(factory->CreateFunctor("factorial", { factory->CreateVariable("N"), factory->CreateVariable("F") }),
        {
            term1, term2, term3, term4
        });
        result = resolver->ResolveAll(factory.get(), prog.get(), { factory->CreateFunctor("factorial", { factory->CreateConstant("2"), factory->CreateVariable("X") })});
        CHECK(CheckSolutions(*result, {{ UnifierItemType(variableX, factory->CreateConstant("2")) }}));

        //        vertical(line(point(X,Y),point(X,Z))).
        //        horizontal(line(point(X,Y),point(Z,Y))).
        prog->ClearAll();
        shared_ptr<HtnTerm>pointXY = factory->CreateFunctor("point", { variableX, variableY });
        shared_ptr<HtnTerm>pointXZ = factory->CreateFunctor("point", { variableX, variableZ });
        shared_ptr<HtnTerm>pointZY = factory->CreateFunctor("point", { variableZ, variableY });
        prog->AddRule(factory->CreateFunctor("vertical", { factory->CreateFunctor("line", { pointXY, pointXZ }) }), {});
        prog->AddRule(factory->CreateFunctor("horizontal", { factory->CreateFunctor("line", { pointXY, pointZY }) }), {});
        // vertical(line(point(1,1),point(1,3))) => true
        result = resolver->ResolveAll(factory.get(), prog.get(),
        {
            factory->CreateFunctor("vertical",
                                   {
                                       factory->CreateFunctor("line",
                                                              {
                                                                  factory->CreateFunctor("point", { factory->CreateConstant("1"), factory->CreateConstant("1") }),
                                                                  factory->CreateFunctor("point", { factory->CreateConstant("1"), factory->CreateConstant("3") })
                                                              })
                                   })
        });
        CHECK(IsTrue(result));

        // horizontal(line(point(1,1),point(2,Y))).
        result = resolver->ResolveAll(factory.get(), prog.get(),
                                 {
                                     factory->CreateFunctor("horizontal",
                                                            {
                                                                factory->CreateFunctor("line",
                                                                                       {
                                                                                           factory->CreateFunctor("point", { factory->CreateConstant("1"), factory->CreateConstant("1") }),
                                                                                           factory->CreateFunctor("point", { factory->CreateConstant("2"), variableY })
                                                                                       })
                                                            })
                                 });
        CHECK(CheckSolutions(*result, {
            { UnifierItemType(variableY,  factory->CreateConstant("1")) }
        }));

        // add_3_and_double(X,Y) :- Y is (X+3)*2.
    }


    TEST(HtnGoalResolverCustomPredicate)
    {
        HtnGoalResolver resolver;
        shared_ptr<HtnTermFactory> factory = shared_ptr<HtnTermFactory>(new HtnTermFactory());
        shared_ptr<HtnRuleSet> state = shared_ptr<HtnRuleSet>(new HtnRuleSet());
        shared_ptr<PrologCompiler> compiler = shared_ptr<PrologCompiler>(new PrologCompiler(factory.get(), state.get()));
        string testState;
        string goals;
        string finalUnifier;
        shared_ptr<vector<UnifierType>> unifier;

//        SetTraceFilter((int) SystemTraceType::Planner | (int)SystemTraceType::Solver | (int) SystemTraceType::Unifier,  TraceDetail::Diagnostic);
//        SetTraceFilter( (int)SystemTraceType::Solver,  TraceDetail::Diagnostic);


        // compiler->Clear();
        // testState = string() +
        //     "goals(atomic(mia)).\r\n";
        // CHECK(compiler->Compile(testState));
        // unifier = compiler->SolveGoals();
        // finalUnifier = HtnGoalResolver::ToString(unifier.get());
        // CHECK_EQUAL(finalUnifier, "(())");

        // ***** print goal with previous and next terms
        compiler->Clear();
        testState = string() +
        "letter(c). letter(b). letter(A).\r\n" +
        "capital(A).\r\n" +
        "trace(?x) :- .\r\n"
        "goals(custom(1,2)).\r\n";
        CHECK(compiler->Compile(testState));
        unifier = compiler->SolveGoals();
        finalUnifier = HtnGoalResolver::ToString(unifier.get());
        CHECK_EQUAL(finalUnifier, "(())");

        compiler->Clear();
        testState = string() +
        "letter(c). letter(b). letter(A).\r\n" +
        "capital(A).\r\n" +
        "trace(?x) :- .\r\n"
        "goals(custom(1,1)).\r\n";
        CHECK(compiler->Compile(testState));
        unifier = compiler->SolveGoals();
        finalUnifier = HtnGoalResolver::ToString(unifier.get());
        CHECK_EQUAL(finalUnifier, "(())");

        compiler->Clear();
        testState = string() +
        "letter(c). letter(b). letter(A).\r\n" +
        "capital(A).\r\n" +
        "trace(?x) :- .\r\n"
        "goals(custom(2,1)).\r\n";
        CHECK(compiler->Compile(testState));
        unifier = compiler->SolveGoals();
        finalUnifier = HtnGoalResolver::ToString(unifier.get());
        CHECK_EQUAL(finalUnifier, "(())");

        compiler->Clear();
        testState = string() +
        "letter(c). letter(b). letter(A).\r\n" +
        "capital(A).\r\n" +
        "trace(?x) :- .\r\n"
        "goals(custom(3,1)).\r\n";
        CHECK(compiler->Compile(testState));
        unifier = compiler->SolveGoals();
        finalUnifier = HtnGoalResolver::ToString(unifier.get());
        CHECK_EQUAL(finalUnifier, "null");
    }
}
