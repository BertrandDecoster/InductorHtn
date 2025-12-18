//
//  HtnGoalResolverTests_Core.cpp
//  TestLib
//
//  Core solver behavior: failure context, unification, recursion, arithmetic, lists
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

bool CheckSolution(UnifierType solution, UnifierType expectedSolution)
{
    StaticFailFastAssert(solution.size() == expectedSolution.size());
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

SUITE(HtnGoalResolverTests)
{
    TEST(GoalResolverFailureContextTest)
    {
        // failureContext is a HtnGoalSolver keyword, ony used for debugging
        HtnGoalResolver resolver;
        shared_ptr<HtnTermFactory> factory = shared_ptr<HtnTermFactory>(new HtnTermFactory());
        shared_ptr<HtnRuleSet> state = shared_ptr<HtnRuleSet>(new HtnRuleSet());
        shared_ptr<PrologCompiler> compiler = shared_ptr<PrologCompiler>(new PrologCompiler(factory.get(), state.get()));
        shared_ptr<vector<UnifierType>> unifier;
        string testState;
        string sharedState;
        string goals;
        string finalUnifier;
        string example;
        int furthestFailureIndex;
        std::vector<std::shared_ptr<HtnTerm>> farthestFailureContext;

        example =
            "test(?X) :- tile(?X, 1)."
            "test2(?X) :- failureContext(1, foo), tile(?X, 1)."
            "test3(?X) :- failureContext(1, foo), tile(0, 1), failureContext(2, foo2), tile(?X, 1)."
            ;
        testState = "tile(0,0). tile(0,1). \r\n";

        // If there is no use of FailureContext, nothing is returned but index still works
        compiler->Clear();
        goals = "goals(test(0), test(1)).";
        CHECK(compiler->Compile(example + sharedState + testState + goals));
        unifier = compiler->SolveGoals(&resolver, 1000000, nullptr, &furthestFailureIndex, &farthestFailureContext);
        finalUnifier = HtnGoalResolver::ToString(unifier.get());
        CHECK_EQUAL(finalUnifier, "null");
        CHECK_EQUAL(1, furthestFailureIndex);
        CHECK_EQUAL(0, farthestFailureContext.size());

        // FailureContext is returned if used
        compiler->Clear();
        goals = "goals(test2(0), test2(1)).";
        CHECK(compiler->Compile(example + sharedState + testState + goals));
        unifier = compiler->SolveGoals(&resolver, 1000000, nullptr, &furthestFailureIndex, &farthestFailureContext);
        finalUnifier = HtnGoalResolver::ToString(unifier.get());
        CHECK_EQUAL(finalUnifier, "null");
        CHECK_EQUAL(1, furthestFailureIndex);
        CHECK_EQUAL(2, farthestFailureContext.size());
        CHECK_EQUAL("{\"1\":[]}, {\"foo\":[]}", HtnTerm::ToString(farthestFailureContext, false, true));

        // The highest FailureContext is returned in a function
        compiler->Clear();
        goals = "goals(test3(0), test3(1)).";
        CHECK(compiler->Compile(example + sharedState + testState + goals));
        unifier = compiler->SolveGoals(&resolver, 1000000, nullptr, &furthestFailureIndex, &farthestFailureContext);
        finalUnifier = HtnGoalResolver::ToString(unifier.get());
        CHECK_EQUAL(finalUnifier, "null");
        CHECK_EQUAL(1, furthestFailureIndex);
        CHECK_EQUAL(2, farthestFailureContext.size());
        CHECK_EQUAL("{\"2\":[]}, {\"foo2\":[]}", HtnTerm::ToString(farthestFailureContext, false, true));

        // FailureContext is still active if it isn't cleared
        compiler->Clear();
        goals = "goals(test3(0), test3(0), test(1)).";
        CHECK(compiler->Compile(example + sharedState + testState + goals));
        unifier = compiler->SolveGoals(&resolver, 1000000, nullptr, &furthestFailureIndex, &farthestFailureContext);
        finalUnifier = HtnGoalResolver::ToString(unifier.get());
        CHECK_EQUAL("null", finalUnifier);
        CHECK_EQUAL(2, furthestFailureIndex);
        CHECK_EQUAL(2, farthestFailureContext.size());
        CHECK_EQUAL("{\"2\":[]}, {\"foo2\":[]}", HtnTerm::ToString(farthestFailureContext, false, true));
    }

    TEST(HtnGoalResolverSquareScenarioTest)
    {
//        SetTraceFilter((int) SystemTraceType::Solver | (int) SystemTraceType::System, TraceDetail::Diagnostic);

        HtnGoalResolver resolver;
        shared_ptr<HtnTermFactory> factory = shared_ptr<HtnTermFactory>(new HtnTermFactory());
        shared_ptr<HtnRuleSet> state = shared_ptr<HtnRuleSet>(new HtnRuleSet());
        shared_ptr<PrologCompiler> compiler = shared_ptr<PrologCompiler>(new PrologCompiler(factory.get(), state.get()));
        string finalFacts;
        string finalFacts2;
        string finalPlan;
        string finalPlan2;
        string example;
        string testState;
        string sharedState;
        string goals;
        string finalUnifier;
        shared_ptr<vector<UnifierType>> unifier;

        // Should only return tiles "in range" that actually exist on the map
        example = string() +
        "gen(?Cur, ?Top, ?Cur) :- =<(?Cur, ?Top).\r\n" +
        "gen(?Cur, ?Top, ?Next):- =<(?Cur, ?Top), is(?Cur1, +(?Cur, 1)), gen(?Cur1, ?Top, ?Next).\r\n" +
        // hLine and vLine create a set of tiles in a line vertically or horizontally
        "hLineTile(?X1,?X2,?Y,tile(?S,?T)) :- gen(?X1,?X2,?S), tile(?S,?Y), is(?T,?Y).\r\n" +
        "vLineTile(?X,?Y1,?Y2,tile(?S,?T)) :- gen(?Y1,?Y2,?T), tile(?X,?T), is(?S,?X).\r\n" +
        // Square generates a square by using the trick that Prolog unifies with ALL rules, so it will get all 4 rules, each representing an edge of the squre
        "square(?X,?Y,?R,tile(?S,?T)) :- is(?Y1, -(?Y, ?R)), is(?X1,-(?X,?R)),is(?X2, +(?X,?R)), hLineTile(?X1, ?X2, ?Y1, tile(?S,?T)).\r\n" +
        "square(?X,?Y,?R,tile(?S,?T)) :- is(?Y1, +(?Y, ?R)), is(?X1,-(?X,?R)),is(?X2, +(?X,?R)), hLineTile(?X1, ?X2, ?Y1, tile(?S,?T)).\r\n" +
        "square(?X,?Y,?R,tile(?S,?T)) :- is(?X1, -(?X,?R)), is(?Y1,-(?Y,-(?R,1))), is(?Y2, +(?Y, -(?R,1))), vLineTile(?X1, ?Y1, ?Y2, tile(?S,?T)).\r\n" +
        "square(?X,?Y,?R,tile(?S,?T)) :- is(?X1, +(?X,?R)), is(?Y1,-(?Y,-(?R,1))), is(?Y2, +(?Y, -(?R,1))), vLineTile(?X1, ?Y1, ?Y2, tile(?S,?T)).\r\n" +
        // attackRangeTiles returns the range of tiles around ?X and ?Y that are in attack range
        // attackRangeTiles uses the same trick as gen to iterate through a set of numbers, in this case min -> max radius.
        "attackRangeTiles(?Min,?Max,tile(?X,?Y),tile(?S,?T)) :- =<(?Min, ?Max), square(?X,?Y,?Min,tile(?S,?T)).\r\n" +
        "attackRangeTiles(?Min,?Max,tile(?X,?Y),tile(?S,?T)) :- =<(?Min, ?Max), is(?Min1, +(?Min, 1)), attackRangeTiles(?Min1,?Max,tile(?X,?Y),tile(?S,?T)).\r\n" +        "";

        compiler->Clear();
        testState = string() +
        "tile(0,0). tile(0,1). \r\n" +
        "goals(attackRangeTiles(1, 1, tile(0,0), ?X)).";
        CHECK(compiler->Compile(example + sharedState + testState + goals));
        unifier = compiler->SolveGoals();
        finalUnifier = HtnGoalResolver::ToString(unifier.get());
        CHECK_EQUAL(finalUnifier, "((?X = tile(0,1)))" );

        compiler->Clear();
        testState = string() +
        "tile(0,0). tile(0,1). tile(1,0).tile(1,1).\r\n" +
        "goals(attackRangeTiles(1, 1, tile(0,0), ?X)).";
        CHECK(compiler->Compile(example + sharedState + testState + goals));
        unifier = compiler->SolveGoals();
        finalUnifier = HtnGoalResolver::ToString(unifier.get());
        CHECK_EQUAL(finalUnifier, "((?X = tile(0,1)), (?X = tile(1,1)), (?X = tile(1,0)))");

        // Should work for multiple radii
        compiler->Clear();
        testState = string() +
        "tile(0,0).tile(1,0).tile(2,0).tile(3,0).tile(4,0).tile(5,0).tile(6,0).tile(7,0).\r\n" +
        "tile(0,1).tile(1,1).tile(2,1).tile(3,1).tile(4,1).tile(5,1).tile(6,1).tile(7,1).\r\n" +
        "tile(0,2).tile(1,2).tile(2,2).tile(3,2).tile(4,2).tile(5,2).tile(6,2).tile(7,2).\r\n" +
        "tile(0,3).tile(1,3).tile(2,3).tile(3,3).tile(4,3).tile(5,3).tile(6,3).tile(7,3).\r\n" +
        "tile(0,4).tile(1,4).tile(2,4).tile(3,4).tile(4,4).tile(5,4).tile(6,4).tile(7,4).\r\n" +
        "tile(0,5).tile(1,5).tile(2,5).tile(3,5).tile(4,5).tile(5,5).tile(6,5).tile(7,5).\r\n" +
        "tile(0,6).tile(1,6).tile(2,6).tile(3,6).tile(4,6).tile(5,6).tile(6,6).tile(7,6).\r\n" +
        "tile(0,7).tile(1,7).tile(2,7).tile(3,7).tile(4,7).tile(5,7).tile(6,7).tile(7,7).\r\n" +
        "goals(attackRangeTiles(1, 2, tile(0,0), ?X)).";
        CHECK(compiler->Compile(example + sharedState + testState + goals));
        unifier = compiler->SolveGoals();
        finalUnifier = HtnGoalResolver::ToString(unifier.get());
        CHECK_EQUAL(finalUnifier, "((?X = tile(0,1)), (?X = tile(1,1)), (?X = tile(1,0)), (?X = tile(0,2)), (?X = tile(1,2)), (?X = tile(2,2)), (?X = tile(2,0)), (?X = tile(2,1)))");
    }

    TEST(HtnGoalResolverRecursionTests)
    {
        HtnGoalResolver resolver;
        shared_ptr<HtnTermFactory> factory = shared_ptr<HtnTermFactory>(new HtnTermFactory());
        shared_ptr<HtnRuleSet> state = shared_ptr<HtnRuleSet>(new HtnRuleSet());
        shared_ptr<PrologCompiler> compiler = shared_ptr<PrologCompiler>(new PrologCompiler(factory.get(), state.get()));
        string finalFacts;
        string finalFacts2;
        string finalPlan;
        string finalPlan2;
        string example;
        string testState;
        string sharedState;
        string goals;
        string finalUnifier;
        shared_ptr<vector<UnifierType>> unifier;

        //        SetTraceFilter((int) SystemTraceType::Planner | (int)SystemTraceType::Solver | (int) SystemTraceType::Unifier,  TraceDetail::Diagnostic);
        //        SetTraceFilter((int) SystemTraceType::Planner | (int)SystemTraceType::Solver,  TraceDetail::Diagnostic);

        // ***** recursive iterator to generate a sequence of numbers
        // https://stackoverflow.com/questions/12109558/simple-prolog-generator
        compiler->Clear();
        testState = string() +
        "gen(?Cur, ?Top, ?Cur) :- =<(?Cur, ?Top).\r\n" +
        "gen(?Cur, ?Top, ?Next):- =<(?Cur, ?Top), is(?Cur1, +(?Cur, 1)), gen(?Cur1, ?Top, ?Next).\r\n" +
        "hLineTile(?X1,?X2,?Y,tile(?S,?T)) :- gen(?X1,?X2,?S), is(?T,?Y).\r\n" +
        "vLineTile(?X,?Y1,?Y2,tile(?S,?T)) :- gen(?Y1,?Y2,?T), is(?S,?X).\r\n" +
        "square(?X,?Y,?R,tile(?S,?T)) :- is(?Y1, -(?Y, ?R)), is(?X1,-(?X,?R)),is(?X2, +(?X,?R)), hLineTile(?X1, ?X2, ?Y1, tile(?S,?T)).\r\n" +
        "square(?X,?Y,?R,tile(?S,?T)) :- is(?Y1, +(?Y, ?R)), is(?X1,-(?X,?R)),is(?X2, +(?X,?R)), hLineTile(?X1, ?X2, ?Y1, tile(?S,?T)).\r\n" +
        "square(?X,?Y,?R,tile(?S,?T)) :- is(?X1, -(?X,?R)), is(?Y1,-(?Y,-(?R,1))), is(?Y2, +(?Y, -(?R,1))), vLineTile(?X1, ?Y1, ?Y2, tile(?S,?T)).\r\n" +
        "square(?X,?Y,?R,tile(?S,?T)) :- is(?X1, +(?X,?R)), is(?Y1,-(?Y,-(?R,1))), is(?Y2, +(?Y, -(?R,1))), vLineTile(?X1, ?Y1, ?Y2, tile(?S,?T)).\r\n" +
        "attackRange(?Min,?Max,?X,?Y,tile(?S,?T)) :- =<(?Min, ?Max), square(?X,?Y,?Min,tile(?S,?T)).\r\n" +
        "attackRange(?Min,?Max,?X,?Y,tile(?S,?T)) :- =<(?Min, ?Max), is(?Min1, +(?Min, 1)), attackRange(?Min1,?Max,?X,?Y,tile(?S,?T)).\r\n" +
        "goals(attackRange(1,2,0,0,?Tile)).\r\n";
        CHECK(compiler->Compile(testState));
        unifier = compiler->SolveGoals();
        finalUnifier = HtnGoalResolver::ToString(unifier.get());
        CHECK_EQUAL(finalUnifier, "((?Tile = tile(-1,-1)), (?Tile = tile(0,-1)), (?Tile = tile(1,-1)), (?Tile = tile(-1,1)), (?Tile = tile(0,1)), (?Tile = tile(1,1)), (?Tile = tile(-1,0)), (?Tile = tile(1,0)), (?Tile = tile(-2,-2)), (?Tile = tile(-1,-2)), (?Tile = tile(0,-2)), (?Tile = tile(1,-2)), (?Tile = tile(2,-2)), (?Tile = tile(-2,2)), (?Tile = tile(-1,2)), (?Tile = tile(0,2)), (?Tile = tile(1,2)), (?Tile = tile(2,2)), (?Tile = tile(-2,-1)), (?Tile = tile(-2,0)), (?Tile = tile(-2,1)), (?Tile = tile(2,-1)), (?Tile = tile(2,0)), (?Tile = tile(2,1)))");

        // ***** recursive iterator to generate a sequence of numbers
        compiler->Clear();
        testState = string() +
        "gen(?Cur, ?Top, ?Cur) :- <(?Cur, ?Top). \r\n" +
        "gen(?Cur, ?Top, ?Next):- <(?Cur, ?Top), is(?Cur1, +(?Cur, 1)), gen(?Cur1, ?Top, ?Next).\r\n" +
        "goals(gen(0, 5, ?Num)).\r\n";
        CHECK(compiler->Compile(testState));
        unifier = compiler->SolveGoals();
        finalUnifier = HtnGoalResolver::ToString(unifier.get());
        CHECK_EQUAL(finalUnifier, "((?Num = 0), (?Num = 1), (?Num = 2), (?Num = 3), (?Num = 4))");
    }

    TEST(HtnGoalResolverUnifierTests)
    {
        shared_ptr<HtnTermFactory> factory = shared_ptr<HtnTermFactory>(new HtnTermFactory());

        // Check obvious boundary cases
        CHECK(HtnGoalResolver::Unify(factory.get(),nullptr, nullptr) == nullptr);
        CHECK(HtnGoalResolver::Unify(factory.get(),nullptr, factory->CreateConstant("x")) == nullptr);
        CHECK(HtnGoalResolver::Unify(factory.get(),factory->CreateConstant("x"), nullptr) == nullptr);

        // ****** Examples from here: http://www.dai.ed.ac.uk/groups/ssp/bookpages/quickprolog/node12.html
        // Two constants of the same name have a valid, empty solution
        shared_ptr<UnifierType> solution = HtnGoalResolver::Unify(factory.get(),factory->CreateConstant("a"), factory->CreateConstant("a"));
        CHECK(CheckSolution(*solution, { } ));

        // Two constants of diff name, no solution
        solution = HtnGoalResolver::Unify(factory.get(),factory->CreateConstant("a"), factory->CreateConstant("b"));
        CHECK(solution == nullptr);

        // Unification instantiates a variable to an atom
        solution = HtnGoalResolver::Unify(factory.get(),factory->CreateVariable("X"), factory->CreateConstant("b"));
        CHECK(CheckSolution(*solution, { pair<shared_ptr<HtnTerm>,shared_ptr<HtnTerm>>(factory->CreateVariable("X"), factory->CreateConstant("b")) } ));

        // woman(mia) and woman(X) unify because X can be set to mia which results in identical terms.
        solution = HtnGoalResolver::Unify(factory.get(),factory->CreateFunctor("woman", { factory->CreateConstant("mia") }),
                                        factory->CreateFunctor("woman", { factory->CreateVariable("X") }));
        CHECK(CheckSolution(*solution, { pair<shared_ptr<HtnTerm>,shared_ptr<HtnTerm>>(factory->CreateVariable("X"), factory->CreateConstant("mia")) } ));

        // Two identical complex terms unify foo(a,b) = foo(a,b)
        solution = HtnGoalResolver::Unify(factory.get(),factory->CreateFunctor("foo", { factory->CreateConstant("a"), factory->CreateConstant("b") }),
                                        factory->CreateFunctor("foo", { factory->CreateConstant("a"), factory->CreateConstant("b") }));
        CHECK(CheckSolution(*solution, { } ));

        // Two complex terms unify if they are of the same arity, have the same principal functor and their arguments unify foo(a,b) = foo(X,Y)
        solution = HtnGoalResolver::Unify(factory.get(),factory->CreateFunctor("foo", { factory->CreateConstant("a"), factory->CreateConstant("b") }),
                                        factory->CreateFunctor("foo", { factory->CreateVariable("X"), factory->CreateVariable("Y") }));
        CHECK(CheckSolution(*solution, { pair<shared_ptr<HtnTerm>,shared_ptr<HtnTerm>>(factory->CreateVariable("X"), factory->CreateConstant("a")),
                                    pair<shared_ptr<HtnTerm>,shared_ptr<HtnTerm>>(factory->CreateVariable("Y"), factory->CreateConstant("b")) }));

        // Instantiation of variables may occur in either of the terms to be unified foo(a,Y) = foo(X,b)
        solution = HtnGoalResolver::Unify(factory.get(),factory->CreateFunctor("foo", { factory->CreateConstant("a"), factory->CreateVariable("Y") }),
                                        factory->CreateFunctor("foo", { factory->CreateVariable("X"), factory->CreateConstant("b") }));
        CHECK(CheckSolution(*solution, { pair<shared_ptr<HtnTerm>,shared_ptr<HtnTerm>>(factory->CreateVariable("X"), factory->CreateConstant("a")),
                                    pair<shared_ptr<HtnTerm>,shared_ptr<HtnTerm>>(factory->CreateVariable("Y"), factory->CreateConstant("b")) }));

        // In this case there is no unification because foo(X,X)  must have the same 1st and 2nd arguments foo(a,b) = foo(X,X)
        shared_ptr<HtnTerm>variable1 = factory->CreateVariable("X");
        solution = HtnGoalResolver::Unify(factory.get(),factory->CreateFunctor("foo", { factory->CreateConstant("a"), factory->CreateConstant("b") }),
                                        factory->CreateFunctor("foo", { variable1, variable1 }));
        CHECK(solution == nullptr);

        // Unification binds two differently named variables to a single, unique variable name
        shared_ptr<HtnTerm>variableX = factory->CreateVariable("X");
        shared_ptr<HtnTerm>variableY = factory->CreateVariable("Y");
        solution = HtnGoalResolver::Unify(factory.get(),variableX, variableY);
        CHECK(CheckSolution(*solution, { pair<shared_ptr<HtnTerm>,shared_ptr<HtnTerm>>(variableX, variableY)}));

        // Occurs check stops recursion     father(X) = X
        variableX = factory->CreateVariable("X");
        solution = HtnGoalResolver::Unify(factory.get(),factory->CreateFunctor("father", { variableX }),
                                        variableX);
        CHECK(solution == nullptr);

        // f(g(X, h(X, b)), Z) and f(g(a, Z), Y) unifies to: {X=a,Z=h(a,b),Y=h(a,b)}
        variableX = factory->CreateVariable("X");
        variableY = factory->CreateVariable("Y");
        shared_ptr<HtnTerm>variableZ = factory->CreateVariable("Z");
        solution = HtnGoalResolver::Unify(factory.get(),factory->CreateFunctor("f",
                                                            {
                                                                factory->CreateFunctor("g",
                                                                                       {
                                                                                           variableX,
                                                                                           factory->CreateFunctor("h",
                                                                                                                  {
                                                                                                                      variableX,
                                                                                                                      factory->CreateConstant("b")
                                                                                                                  })
                                                                                       }),
                                                                variableZ
                                                            }),
                                               factory->CreateFunctor("f",
                                                             {
                                                                 factory->CreateFunctor("g",
                                                                                        {
                                                                                            factory->CreateConstant("a"),
                                                                                            variableZ
                                                                                        }),
                                                                 variableY
                                                             })
                                        );
        CHECK(CheckSolution(*solution, {
            pair<shared_ptr<HtnTerm>,shared_ptr<HtnTerm>>(factory->CreateVariable("X"), factory->CreateConstant("a")),
            pair<shared_ptr<HtnTerm>,shared_ptr<HtnTerm>>(factory->CreateVariable("Z"), factory->CreateFunctor("h",
                                                                                         {
                                                                                             factory->CreateConstant("a"),
                                                                                             factory->CreateConstant("b")
                                                                                         })),
            pair<shared_ptr<HtnTerm>,shared_ptr<HtnTerm>>(factory->CreateVariable("Y"), factory->CreateFunctor("h",
                                                                                         {
                                                                                             factory->CreateConstant("a"),
                                                                                             factory->CreateConstant("b")
                                                                                         })),

            // [('='(X,Y),'='(X,abc)),[[X <-- abc, Y <-- abc]]].

    //        ['='(g(X),f(f(X))), failure].
    //        ['='(f(X,1),f(a(X))), failure].
    //        ['='(f(X,Y,X),f(a(X),a(Y),Y,2)), failure].
    //        ['='(f(A,B,C),f(g(B,B),g(C,C),g(D,D))),
    //         [[A <-- g(g(g(D,D),g(D,D)),g(g(D,D),g(D,D))),
    //           B <-- g(g(D,D),g(D,D)),
    //           C <-- g(D,D)]]].
        }));



        CHECK(true);
    }

    TEST(HtnGoalResolverSubstituteUnifiersTests)
    {
        shared_ptr<HtnTermFactory> factory = shared_ptr<HtnTermFactory>(new HtnTermFactory());
        shared_ptr<HtnTerm>variableX = factory->CreateVariable("X");
        shared_ptr<HtnTerm>variableY = factory->CreateVariable("Y");
        shared_ptr<HtnTerm>variableZ = factory->CreateVariable("Z");

        // src: X = Y dest: Z = X answer: Z = Y
        shared_ptr<UnifierType> result = HtnGoalResolver::SubstituteUnifiers(factory.get(),
            { UnifierItemType(variableX,  variableY) },
            { UnifierItemType(variableZ,  variableX) });
        CheckSolution(*result, { UnifierItemType(variableZ,  variableY) });

        // src: X = foo(bar) dest: Y = goo(X) answer: Y = goo(foo(bar))
        result = HtnGoalResolver::SubstituteUnifiers(factory.get(),
                                                   { UnifierItemType(variableX,  factory->CreateFunctor("foo", { factory->CreateConstant("bar")})) },
                                                   { UnifierItemType(variableY,  factory->CreateFunctor("goo", { variableX})) });
        CheckSolution(*result, { UnifierItemType(variableY,  factory->CreateFunctor("goo", { factory->CreateFunctor("foo", { factory->CreateConstant("bar")})})) });


    }

    bool IsFalse(shared_ptr<vector<UnifierType>> result)
    {
        return result == nullptr;
    }

    bool IsTrue(shared_ptr<vector<UnifierType>> result)
    {
        return result != nullptr && result->size() == 1 && (*result)[0].size() == 0;
    }

    TEST(HtnGoalResolverArithmeticFunctionsTests)
    {
        shared_ptr<HtnTermFactory> factory = shared_ptr<HtnTermFactory>(new HtnTermFactory());
        shared_ptr<HtnTerm>falseTerm = factory->CreateConstant("false");
        shared_ptr<HtnTerm>trueTerm = factory->CreateConstant("true");

        // Make sure basic type inferencing works
        CHECK(factory->CreateConstant("foo")->GetTermType() == HtnTermType::Atom);
        CHECK(factory->CreateConstant("1")->GetTermType() == HtnTermType::IntType);
        CHECK(factory->CreateConstant("1.1")->GetTermType() == HtnTermType::FloatType);
        CHECK(factory->CreateConstant("1.0")->GetTermType() == HtnTermType::FloatType);
        CHECK(factory->CreateConstant("1.")->GetTermType() == HtnTermType::FloatType);
        CHECK(factory->CreateConstant("1-1")->GetTermType() == HtnTermType::Atom);
        CHECK(factory->CreateConstant("1+1")->GetTermType() == HtnTermType::Atom);
        CHECK(factory->CreateVariable("foo")->GetTermType() == HtnTermType::Variable);
        CHECK(factory->CreateConstantFunctor("foo", { "bar" })->GetTermType() == HtnTermType::Compound);

        shared_ptr<HtnTerm> result = factory->CreateFunctor(">",
        {
            factory->CreateConstant("1"),
            factory->CreateConstant("2")
        });
        CHECK(*result->Eval(factory.get()) == *falseTerm);

        result = factory->CreateFunctor(">",
                                                 {
                                                     factory->CreateConstant("1"),
                                                     factory->CreateConstant("1")
                                                 });
        CHECK(*result->Eval(factory.get()) == *falseTerm);

        result = factory->CreateFunctor(">",
                                                 {
                                                     factory->CreateConstant("2"),
                                                     factory->CreateConstant("1")
                                                 });
        CHECK(*result->Eval(factory.get()) == *trueTerm);

        result = factory->CreateFunctor(">=",
                                        {
                                            factory->CreateConstant("-17"),
                                            factory->CreateConstant("0")
                                        });
        CHECK(*result->Eval(factory.get()) == *falseTerm);

        // Make sure conversions work
        shared_ptr<HtnTerm> result2;
        // float
        result = factory->CreateConstantFunctor("float", { "1.1" } );
        result2 = result->Eval(factory.get());
        CHECK(*result2 == *factory->CreateConstant("1.100000000"));

        result = factory->CreateConstantFunctor("float", { "-1.1" } );
        result2 = result->Eval(factory.get());
        CHECK(*result2 == *factory->CreateConstant("-1.100000000"));

        // integer
        result = factory->CreateConstantFunctor("integer", { "1.1" } );
        result2 = result->Eval(factory.get());
        CHECK(*result2 == *factory->CreateConstant("1"));

        result = factory->CreateConstantFunctor("integer", { "-1.1" } );
        result2 = result->Eval(factory.get());
        CHECK(*result2 == *factory->CreateConstant("-1"));

        // abs
        result = factory->CreateConstantFunctor("abs", { "1.1" } );
        result2 = result->Eval(factory.get());
        CHECK(*result2 == *factory->CreateConstant("1.100000000"));
        result = factory->CreateConstantFunctor("abs", { "-1.1" } );
        result2 = result->Eval(factory.get());
        CHECK(*result2 == *factory->CreateConstant("1.100000000"));

        // basic math
        result = factory->CreateFunctor("-", { factory->CreateConstant("-3"), factory->CreateConstant("13")  });
        result2 = result->Eval(factory.get());
        CHECK(*result2 == *factory->CreateConstant("-16"));
    }

    TEST(HtnGoalResolverUnifierOperatorTests)
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

        // ***** single =() goal that fails
        compiler->Clear();
        testState = string() +
        "trace(?x) :- .\r\n"
        "goals( =(mia, vincent) ).\r\n";
        CHECK(compiler->Compile(testState));
        unifier = compiler->SolveGoals();
        finalUnifier = HtnGoalResolver::ToString(unifier.get());
        CHECK_EQUAL(finalUnifier, "null");

        // ***** single =() goal that succeeds
        compiler->Clear();
        testState = string() +
        "trace(?x) :- .\r\n"
        "goals( =(?X, vincent) ).\r\n";
        CHECK(compiler->Compile(testState));
        unifier = compiler->SolveGoals();
        finalUnifier = HtnGoalResolver::ToString(unifier.get());
        CHECK_EQUAL(finalUnifier, "((?X = vincent))");

        // ***** single =() goal that is preceeded and succeeded by more goals to make sure unifiers flow through properly
        compiler->Clear();
        testState = string() +
        "letter(c). letter(b). letter(a).\r\n" +
        "capital(c). capital(b). capital(a).\r\n" +
        "cost(c, 1). cost(b, 2). cost(a, 3).\r\n" +
        "highCost(3).\r\n" +
        "trace(?x) :- .\r\n"
        "goals( letter(?X), =(?Y, ?X), cost(?Y, ?Cost) ).\r\n";
        CHECK(compiler->Compile(testState));
        unifier = compiler->SolveGoals();
        finalUnifier = HtnGoalResolver::ToString(unifier.get());
        CHECK_EQUAL(finalUnifier, "((?X = c, ?Y = c, ?Cost = 1), (?X = b, ?Y = b, ?Cost = 2), (?X = a, ?Y = a, ?Cost = 3))");

        // ***** make sure terms with variables can be unified, and the unifications work in both terms
        compiler->Clear();
        testState = string() +
        "letter(c). letter(b). letter(a).\r\n" +
        "capital(c). capital(b). capital(a).\r\n" +
        "cost(c, 1). cost(b, 2). cost(a, 3).\r\n" +
        "highCost(3).\r\n" +
        "trace(?x) :- .\r\n"
        "goals( =(?Y, letter(?X)), =(capital(?X), ?Z) ).\r\n";
        CHECK(compiler->Compile(testState));
        unifier = compiler->SolveGoals();
        finalUnifier = HtnGoalResolver::ToString(unifier.get());
        CHECK_EQUAL(finalUnifier, "((?Y = letter(?X), ?Z = capital(?X)))");
    }

    TEST(HtnGoalResolverListTests)
    {
        HtnGoalResolver resolver;
        shared_ptr<HtnTermFactory> factory = shared_ptr<HtnTermFactory>(new HtnTermFactory());
        shared_ptr<HtnRuleSet> state = shared_ptr<HtnRuleSet>(new HtnRuleSet());
        shared_ptr<PrologCompiler> compiler = shared_ptr<PrologCompiler>(new PrologCompiler(factory.get(), state.get()));
        string testState;
        string goals;
        string finalUnifier;
        shared_ptr<vector<UnifierType>> unifier;

//                SetTraceFilter((int) SystemTraceType::Planner | (int)SystemTraceType::Solver | (int) SystemTraceType::Unifier,  TraceDetail::Diagnostic);
//        SetTraceFilter( (int)SystemTraceType::Solver,  TraceDetail::Diagnostic);

        // ***** simplest positive case
        compiler->Clear();
        testState = string() +
            "split([?Head | ?Tail], ?Head, ?Tail). "
            "goals(split([a, b, c, d], ?Head, ?Tail)).\r\n";
        CHECK(compiler->Compile(testState));
        unifier = compiler->SolveGoals();
        finalUnifier = HtnGoalResolver::ToString(unifier.get());
        CHECK_EQUAL(finalUnifier, "((?Tail = [b,c,d], ?Head = a))");

        // ***** classic list rule: member/2
        compiler->Clear();
        testState = string() +
            "member(?X, [?X|_]).        % member(X, [Head|Tail]) is true if X = Head \r\n"
            "                         % that is, if X is the head of the list\r\n"
            "member(?X, [_|?Tail]) :-   % or if X is a member of Tail,\r\n"
            "  member(?X, ?Tail).       % ie. if member(X, Tail) is true.\r\n"
            "goals( member(a, [b, c, a, [d, e, f]]), not(member(d, [b, c, a, [d, e, f]])) ).\r\n";
        CHECK(compiler->Compile(testState));
        unifier = compiler->SolveGoals();
        finalUnifier = HtnGoalResolver::ToString(unifier.get());
        CHECK_EQUAL(finalUnifier, "(())");

        // ***** classic list rule: append/3
        compiler->Clear();
        testState = string() +
            "append([], ?Ys, ?Ys)."
            "append([?X|?Xs], ?Ys, [?X|?Zs]) :- append(?Xs, ?Ys, ?Zs)."
            "goals( append(?ListLeft, ?ListRight, [a, b, c]) ).\r\n";
        CHECK(compiler->Compile(testState));
        unifier = compiler->SolveGoals();
        finalUnifier = HtnGoalResolver::ToString(unifier.get());
        CHECK_EQUAL(finalUnifier, "((?ListRight = [a,b,c], ?ListLeft = []), (?ListLeft = [a], ?ListRight = [b,c]), (?ListLeft = [a,b], ?ListRight = [c]), (?ListLeft = [a,b,c], ?ListRight = []))");

        // ***** classic list rule: reverse/2
        compiler->Clear();
        testState = string() +
        "append([], ?Ys, ?Ys)."
        "append([?X|?Xs], ?Ys, [?X|?Zs]) :- append(?Xs, ?Ys, ?Zs)."
        "reverse([],[])."
        "reverse([?X|?Xs],?YsX) :- reverse(?Xs,?Ys), append(?Ys,[?X],?YsX)."
        "goals( reverse([a, b, foo(a, [a, b, c])], ?X) ).\r\n";
        CHECK(compiler->Compile(testState));
        unifier = compiler->SolveGoals();
        finalUnifier = HtnGoalResolver::ToString(unifier.get());
        CHECK_EQUAL(finalUnifier, "((?X = [foo(a,[a,b,c]),b,a]))");

        // ***** class list rule: Len
        compiler->Clear();
        testState = string() +
        "len([], 0).\r\n"
        "len([_ | ?Tail], ?Length) :-\r\n"
        "    len(?Tail, ?Length1),\r\n"
        "    is(?Length, +(?Length1, 1)),!.\r\n"
        "goals( len([[], b, foo(a, [a, b, c])], ?X) ).\r\n";
        CHECK(compiler->Compile(testState));
        unifier = compiler->SolveGoals();
        finalUnifier = HtnGoalResolver::ToString(unifier.get());
        CHECK_EQUAL(finalUnifier, "((?X = 3))");

    }
}
