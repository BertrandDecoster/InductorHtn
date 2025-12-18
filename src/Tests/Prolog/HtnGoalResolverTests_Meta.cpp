//
//  HtnGoalResolverTests_Meta.cpp
//  TestLib
//
//  Meta-predicates and collection operations: cut, assert/retract, findall, min, max, sum, distinct, count
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

SUITE(HtnGoalResolverTests)
{
	TEST(HtnGoalResolverCutTests)
	{
		HtnGoalResolver resolver;
		shared_ptr<HtnTermFactory> factory = shared_ptr<HtnTermFactory>(new HtnTermFactory());
		shared_ptr<HtnRuleSet> state = shared_ptr<HtnRuleSet>(new HtnRuleSet());
		shared_ptr<PrologCompiler> compiler = shared_ptr<PrologCompiler>(new PrologCompiler(factory.get(), state.get()));
		string testState;
		string goals;
		string finalUnifier;
		shared_ptr<vector<UnifierType>> unifier;

//        SetTraceFilter((int)SystemTraceType::Solver, TraceDetail::Diagnostic);

        // ***** multiple rules, fail before cut should run second rule like normal
        compiler->Clear();
        testState = string() +
        "rule(?X) :- itemsInBag(?X), !."
        "rule(?X) :- =(?X, good)."
        "trace(?x) :- .\r\n"
        "goals( rule(?X) ).\r\n";
        CHECK(compiler->Compile(testState));
        unifier = compiler->SolveGoals();
        finalUnifier = HtnGoalResolver::ToString(unifier.get());
        CHECK_EQUAL(finalUnifier, "((?X = good))");

		// ***** multiple rules, second rule doesn't run after cut
		compiler->Clear();
		testState = string() +
			"itemsInBag(Name1). \r\n" +
			"itemsInBag(Name2). \r\n" +
			"rule(?X) :- itemsInBag(?X), !."
			"rule(?X) :- =(?X, Bad)."
			"trace(?x) :- .\r\n"
			"goals( rule(?X) ).\r\n";
		CHECK(compiler->Compile(testState));
		unifier = compiler->SolveGoals();
		finalUnifier = HtnGoalResolver::ToString(unifier.get());
		CHECK_EQUAL(finalUnifier, "((?X = Name1))");

		// ***** multiple rules, second rule doesn't run after cut, but backtracking AFTER cut still works
		compiler->Clear();
		testState = string() +
			"itemsInBag(Name1). \r\n" +
			"itemsInBag(Name2). \r\n" +
			"itemsInPurse(lipstick). \r\n" +
			"itemsInPurse(tissues). \r\n" +
			"rule(?X, ?Y) :- itemsInBag(?X), !, itemsInPurse(?Y)."
			"rule(?X, ?Y) :- =(?X, Bad), =(?Y, Bad)."
			"trace(?x) :- .\r\n"
			"goals( rule(?X, ?Y) ).\r\n";
		CHECK(compiler->Compile(testState));
		unifier = compiler->SolveGoals();
		finalUnifier = HtnGoalResolver::ToString(unifier.get());
		CHECK_EQUAL(finalUnifier, "((?X = Name1, ?Y = lipstick), (?X = Name1, ?Y = tissues))");

		// Cut in zero argument built-in function that does standalone eval should work
		compiler->Clear();
		testState = string() +
			"itemsInBag(Name1). \r\n" +
			"itemsInBag(Name2). \r\n" +
			"goals( count(?Count, itemsInBag(?X), !) ).\r\n";
		CHECK(compiler->Compile(testState));
		unifier = compiler->SolveGoals();
		finalUnifier = HtnGoalResolver::ToString(unifier.get());
		CHECK_EQUAL(finalUnifier, "((?Count = 1))");

		// Cut in two argument built-in function that does standalone eval should work
		compiler->Clear();
		testState = string() +
			"itemsInBag(Name1, 5). \r\n" +
			"itemsInBag(Name2, 4). \r\n" +
			"goals( min(?Min, ?Size, itemsInBag(?X, ?Size), !) ).\r\n";
		CHECK(compiler->Compile(testState));
		unifier = compiler->SolveGoals();
		finalUnifier = HtnGoalResolver::ToString(unifier.get());
		CHECK_EQUAL(finalUnifier, "((?Min = 5))");

		// Two cuts works
		compiler->Clear();
		testState = string() +
			"itemsInBag(Name1). \r\n" +
			"itemsInBag(Name2). \r\n" +
			"itemsInPurse(lipstick). \r\n" +
			"itemsInPurse(tissues). \r\n" +
			"rule(?X, ?Y) :- itemsInBag(?X), !, itemsInPurse(?Y), !."
			"rule(?X, ?Y) :- =(?X, Bad), =(?Y, Bad)."
			"trace(?x) :- .\r\n"
			"goals( rule(?X, ?Y) ).\r\n";
		CHECK(compiler->Compile(testState));
		unifier = compiler->SolveGoals();
		finalUnifier = HtnGoalResolver::ToString(unifier.get());
		CHECK_EQUAL(finalUnifier, "((?X = Name1, ?Y = lipstick))");

		// Cuts at the begining of a rule work
		compiler->Clear();
		testState = string() +
			"itemsInBag(Name1). \r\n" +
			"itemsInBag(Name2). \r\n" +
			"itemsInPurse(lipstick). \r\n" +
			"itemsInPurse(tissues). \r\n" +
			"rule(?X, ?Y) :- itemsInBag(?X), itemsInPurse(?Y)."
			"rule(?X, ?Y) :- !."
			"rule(?X, ?Y) :- =(?X, Bad), =(?Y, Bad)."
			"trace(?x) :- .\r\n"
			"goals( rule(?X, ?Y) ).\r\n";
		CHECK(compiler->Compile(testState));
		unifier = compiler->SolveGoals();
		finalUnifier = HtnGoalResolver::ToString(unifier.get());
		CHECK_EQUAL(finalUnifier, "((?X = Name1, ?Y = lipstick), (?X = Name1, ?Y = tissues), (?X = Name2, ?Y = lipstick), (?X = Name2, ?Y = tissues), ())");

		// ***** works with initial goals
		compiler->Clear();
		testState = string() +
			"itemsInBag(Name1). \r\n" +
			"itemsInBag(Name2). \r\n" +
			"goals( itemsInBag(?X), ! ).\r\n";
		CHECK(compiler->Compile(testState));
		unifier = compiler->SolveGoals();
		finalUnifier = HtnGoalResolver::ToString(unifier.get());
		CHECK_EQUAL(finalUnifier, "((?X = Name1))");
	}

	TEST(HtnGoalResolverAssertRetractTests)
	{
		HtnGoalResolver resolver;
		shared_ptr<HtnTermFactory> factory = shared_ptr<HtnTermFactory>(new HtnTermFactory());
		shared_ptr<HtnRuleSet> state = shared_ptr<HtnRuleSet>(new HtnRuleSet());
		shared_ptr<PrologCompiler> compiler = shared_ptr<PrologCompiler>(new PrologCompiler(factory.get(), state.get()));
		string testState;
		string goals;
		string finalUnifier;
		shared_ptr<vector<UnifierType>> unifier;

		//SetTraceFilter((int)SystemTraceType::Solver, TraceDetail::Diagnostic);

		// ***** single assert() goal
		compiler->Clear();
		testState = string() +
			"itemsInBag(Name1). \r\n" +
			"itemsInBag(Name2). \r\n" +
			"trace(?x) :- .\r\n"
			"goals( assert(itemsInBag(Name3)), itemsInBag(?After) ).\r\n";
		CHECK(compiler->Compile(testState));
		unifier = compiler->SolveGoals();
		finalUnifier = HtnGoalResolver::ToString(unifier.get());
		CHECK_EQUAL(finalUnifier, "((?After = Name1), (?After = Name2), (?After = Name3))");
		// Should be permanently changed in the ruleset now
		CHECK(state->DebugHasRule("itemsInBag(Name3)", ""));

		// ***** single assert() goal with a variable that needs to be bound
		compiler->Clear();
		testState = string() +
			"itemsInBag(Name1). \r\n" +
			"itemsInBag(Name2). \r\n" +
			"rule(?X) :- assert(itemsInBag(?X))."
			"trace(?x) :- .\r\n"
			"goals( rule(Name3), itemsInBag(?After) ).\r\n";
		CHECK(compiler->Compile(testState));
		unifier = compiler->SolveGoals();
		finalUnifier = HtnGoalResolver::ToString(unifier.get());
		CHECK_EQUAL(finalUnifier, "((?After = Name1), (?After = Name2), (?After = Name3))");
		// Should be permanently changed in the ruleset now
		CHECK(state->DebugHasRule("itemsInBag(Name3)", ""));

		// ***** single retract() goal
		compiler->Clear();
		testState = string() +
			"itemsInBag(Name1). \r\n" +
			"itemsInBag(Name2). \r\n" +
			"trace(?x) :- .\r\n"
			"goals( retract(itemsInBag(Name1)), itemsInBag(?After) ).\r\n";
		CHECK(compiler->Compile(testState));
		unifier = compiler->SolveGoals();
		finalUnifier = HtnGoalResolver::ToString(unifier.get());
		CHECK_EQUAL(finalUnifier, "((?After = Name2))");
		// Should be permanently changed in the ruleset now
		CHECK(!state->DebugHasRule("itemsInBag(Name1)", ""));

		// ***** single retract() goal with a variable that needs to be bound
		compiler->Clear();
		testState = string() +
			"itemsInBag(Name1). \r\n" +
			"itemsInBag(Name2). \r\n" +
			"rule(?X) :- retract(itemsInBag(?X))."
			"trace(?x) :- .\r\n"
			"goals( rule(Name1), itemsInBag(?After) ).\r\n";
		CHECK(compiler->Compile(testState));
		unifier = compiler->SolveGoals();
		finalUnifier = HtnGoalResolver::ToString(unifier.get());
		CHECK_EQUAL(finalUnifier, "((?After = Name2))");
		CHECK(!state->DebugHasRule("itemsInBag(Name1)", ""));

        // ***** single retractall() goal with a variable that needs to be bound
        compiler->Clear();
        testState = string() +
        "itemsInBag(Name1). \r\n" +
        "itemsInBag(Name2). \r\n" +
        "goals( retractall(itemsInBag(?X)) ).\r\n";
        CHECK(compiler->Compile(testState));
        unifier = compiler->SolveGoals();
        finalUnifier = HtnGoalResolver::ToString(unifier.get());
        CHECK_EQUAL(finalUnifier, "(())");
        CHECK(!state->DebugHasRule("itemsInBag(Name1)", ""));
        CHECK(!state->DebugHasRule("itemsInBag(Name2)", ""));

        // ***** single retract() goal with a fact that doesn't exist
        compiler->Clear();
        testState = string() +
        "itemsInBag(Name1). \r\n" +
        "itemsInBag(Name2). \r\n" +
        "goals( retract(itemsInBag(Name3)) ).\r\n";
        CHECK(compiler->Compile(testState));
        unifier = compiler->SolveGoals();
        finalUnifier = HtnGoalResolver::ToString(unifier.get());
        CHECK_EQUAL(finalUnifier, "null");
	}


    TEST(HtnGoalResolverFindAllTests)
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

        // ***** if there are no solutions, we get an empty list
        compiler->Clear();
        testState = string() +
        "child(martha,charlotte)."
        "child(charlotte,caroline)."
        "child(caroline,laura)."
        "child(laura,rose)."
        "descend(?X,?Y)  :-  child(?X,?Y)."
        "descend(?X,?Y)  :-  child(?X,?Z),"
        "                    descend(?Z,?Y)."
        "trace(?x) :- .\r\n"
        "goals( findall(?X,descend(rose,?X),?Z) ).\r\n";
        CHECK(compiler->Compile(testState));
        unifier = compiler->SolveGoals();
        finalUnifier = HtnGoalResolver::ToString(unifier.get());
        CHECK_EQUAL(finalUnifier, "((?Z = []))");

        // ***** simple single variable scenario with solutions and an extra goal to make sure
        // unifiers flow
        compiler->Clear();
        testState = string() +
        "child(martha,charlotte)."
        "child(charlotte,caroline)."
        "child(caroline,laura)."
        "child(laura,rose)."
        "descend(?X,?Y)  :-  child(?X,?Y)."
        "descend(?X,?Y)  :-  child(?X,?Z),"
        "                    descend(?Z,?Y)."
        "trace(?x) :- .\r\n"
        "goals( child(charlotte, ?A), findall(?X,descend(martha,?X),?Z), child(?A, ?B) ).\r\n";
        CHECK(compiler->Compile(testState));
        unifier = compiler->SolveGoals();
        finalUnifier = HtnGoalResolver::ToString(unifier.get());
        CHECK_EQUAL(finalUnifier, "((?A = caroline, ?Z = [charlotte,caroline,laura,rose], ?B = laura))");

        // ***** complex template single variable scenario that succeeds
        compiler->Clear();
        testState = string() +
        "child(martha,charlotte)."
        "child(charlotte,caroline)."
        "child(caroline,laura)."
        "child(laura,rose)."
        "descend(?X,?Y)  :-  child(?X,?Y)."
        "descend(?X,?Y)  :-  child(?X,?Z),"
        "                    descend(?Z,?Y)."
        "trace(?x) :- .\r\n"
        "goals( findall(fromMartha(?X),descend(martha,?X),?Z) ).\r\n";
        CHECK(compiler->Compile(testState));
        unifier = compiler->SolveGoals();
        finalUnifier = HtnGoalResolver::ToString(unifier.get());
        CHECK_EQUAL(finalUnifier, "((?Z = [fromMartha(charlotte),fromMartha(caroline),fromMartha(laura),fromMartha(rose)]))");

        // ***** simple template multi variable scenario that succeeds
        compiler->Clear();
        testState = string() +
        "child(martha,charlotte)."
        "child(charlotte,caroline)."
        "child(caroline,laura)."
        "child(laura,rose)."
        "descend(?X,?Y)  :-  child(?X,?Y)."
        "descend(?X,?Y)  :-  child(?X,?Z),"
        "                    descend(?Z,?Y)."
        "trace(?x) :- .\r\n"
        "goals( findall(?X,descend(?X,?Y),?Z) ).\r\n";
        CHECK(compiler->Compile(testState));
        unifier = compiler->SolveGoals();
        finalUnifier = HtnGoalResolver::ToString(unifier.get());
        CHECK_EQUAL(finalUnifier, "((?Z = [martha,charlotte,caroline,laura,martha,martha,martha,charlotte,charlotte,caroline]))");


        // ***** last argument should be unified with
        compiler->Clear();
        testState = string() +
        "child(martha,charlotte)."
        "child(charlotte,caroline)."
        "child(caroline,laura)."
        "child(laura,rose)."
        "descend(?X,?Y)  :-  child(?X,?Y)."
        "descend(?X,?Y)  :-  child(?X,?Z),"
        "                    descend(?Z,?Y)."
        "trace(?x) :- .\r\n"
        "goals( findall(?X,descend(laura,?X),[?Z]) ).\r\n";
        CHECK(compiler->Compile(testState));
        unifier = compiler->SolveGoals();
        finalUnifier = HtnGoalResolver::ToString(unifier.get());
        CHECK_EQUAL(finalUnifier, "((?Z = rose))");

        // ***** scenario
        // from: https://www.cpp.edu/~jrfisher/www/prolog_tutorial/2_15.html
        compiler->Clear();
        testState = string() +
        "edge(1,2)."
        "edge(1,4)."
        "edge(1,3)."
        "edge(2,3)."
        "edge(2,5)."
        "edge(3,4)."
        "edge(3,5)."
        "edge(4,5)."
        "member(?X, [?X|_])."
        "member(?X, [_|?Tail]) :-"
        "  member(?X, ?Tail)."
        "reverse([],[])."
        "reverse([?X|?Xs],?YsX) :- reverse(?Xs,?Ys), append(?Ys,[?X],?YsX)."
        "append([], ?Ys, ?Ys)."
        "append([?X|?Xs], ?Ys, [?X|?Zs]) :- append(?Xs, ?Ys, ?Zs)."
        "path(?A,?B,?Path) :-"
        "       travel(?A,?B,[?A],?Q),"
        "       reverse(?Q,?Path)."
        "connected(?X,?Y) :- edge(?X,?Y)."
        "connected(?X,?Y) :- edge(?Y,?X)."
        "travel(?A,?B,?P,[?B|?P]) :-"
        "       connected(?A,?B)."
        "travel(?A,?B,?Visited,?Path) :-"
        "       connected(?A,?C),"
        "       \\==(?C, ?B),"
        "       not(member(?C,?Visited)),"
        "       travel(?C,?B,[?C|?Visited],?Path).";
        goals = "goals( path(1, 2, ?Path) ).\r\n";
        CHECK(compiler->Compile(testState + goals));
        unifier = compiler->SolveGoals();
        finalUnifier = HtnGoalResolver::ToString(unifier.get());
        CHECK_EQUAL(finalUnifier, "((?Path = [1,2]), (?Path = [1,4,5,2]), (?Path = [1,4,5,3,2]), (?Path = [1,4,3,2]), (?Path = [1,4,3,5,2]), (?Path = [1,3,2]), (?Path = [1,3,4,5,2]), (?Path = [1,3,5,2]))");
    }

    TEST(HtnGoalResolverMinTests)
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

        // ***** single min() goal where all terms fail
        compiler->Clear();
        testState = string() +
        "trace(?x) :- .\r\n"
        "goals( min(?Total, ?ItemCount, itemsInBag(?Name, ?ItemCount)) ).\r\n";
        CHECK(compiler->Compile(testState));
        unifier = compiler->SolveGoals();
        finalUnifier = HtnGoalResolver::ToString(unifier.get());
        CHECK_EQUAL(finalUnifier, "null");

        // ***** single min() goal where all terms succeed, but the wrong variable is used for totalling
        compiler->Clear();
        testState = string() +
        "itemsInBag(Name1, 1). \r\n" +
        "itemsInBag(Name2, 2). \r\n" +
        "trace(?x) :- .\r\n"
        "goals( min(?Total, ?NotThere, itemsInBag(?Name, ?ItemCount)) ).\r\n";
        CHECK(compiler->Compile(testState));
        unifier = compiler->SolveGoals();
        finalUnifier = HtnGoalResolver::ToString(unifier.get());
        CHECK_EQUAL(finalUnifier, "null");

        // ***** single min() goal where all terms succeed, but the variable is not ground
        compiler->Clear();
        testState = string() +
        "itemsInBag(Name1, ?Count) :- . \r\n" +
        "trace(?x) :- .\r\n" +
        "goals( min(?Total, ?ItemCount, itemsInBag(?Name, ?ItemCount)) ).\r\n";
        CHECK(compiler->Compile(testState));
        unifier = compiler->SolveGoals();
        finalUnifier = HtnGoalResolver::ToString(unifier.get());
        CHECK_EQUAL(finalUnifier, "null");

        // ***** single min() goal where all terms succeed
        compiler->Clear();
        testState = string() +
        "itemsInBag(Name1, 1). \r\n" +
        "itemsInBag(Name2, 2). \r\n" +
        "trace(?x) :- .\r\n" +
        "goals( min(?Total, ?ItemCount, itemsInBag(?Name, ?ItemCount)) ).\r\n";
        CHECK(compiler->Compile(testState));
        unifier = compiler->SolveGoals();
        finalUnifier = HtnGoalResolver::ToString(unifier.get());
        CHECK_EQUAL(finalUnifier, "((?Total = 1))");

        // ***** single min() goal that is preceeded and succeeded by more goals to make sure unifiers flow through properly
        compiler->Clear();
        testState = string() +
        "itemsInBag(Name1, 1). \r\n" +
        "itemsInBag(Name2, 2). \r\n" +
        "countToString(1, One). \r\n"
        "trace(?x) :- .\r\n" +
        "goals( itemsInBag(Name1, ?X), min(?Total, ?ItemCount, itemsInBag(?Name, ?ItemCount)), countToString(?X, ?Name) ).\r\n";
        CHECK(compiler->Compile(testState));
        unifier = compiler->SolveGoals();
        finalUnifier = HtnGoalResolver::ToString(unifier.get());
        CHECK_EQUAL(finalUnifier, "((?X = 1, ?Total = 1, ?Name = One))");
    }

    TEST(HtnGoalResolverMaxTests)
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

        // ***** single max() goal where all terms fail
        compiler->Clear();
        testState = string() +
        "trace(?x) :- .\r\n"
        "goals( max(?Total, ?ItemCount, itemsInBag(?Name, ?ItemCount)) ).\r\n";
        CHECK(compiler->Compile(testState));
        unifier = compiler->SolveGoals();
        finalUnifier = HtnGoalResolver::ToString(unifier.get());
        CHECK_EQUAL(finalUnifier, "null");

        // ***** single max() goal where all terms succeed, but the wrong variable is used for totalling
        compiler->Clear();
        testState = string() +
        "itemsInBag(Name1, 1). \r\n" +
        "itemsInBag(Name2, 2). \r\n" +
        "trace(?x) :- .\r\n"
        "goals( max(?Total, ?NotThere, itemsInBag(?Name, ?ItemCount)) ).\r\n";
        CHECK(compiler->Compile(testState));
        unifier = compiler->SolveGoals();
        finalUnifier = HtnGoalResolver::ToString(unifier.get());
        CHECK_EQUAL(finalUnifier, "null");

        // ***** single max() goal where all terms succeed, but the variable is not ground
        compiler->Clear();
        testState = string() +
        "itemsInBag(Name1, ?Count) :- . \r\n" +
        "trace(?x) :- .\r\n" +
        "goals( max(?Total, ?ItemCount, itemsInBag(?Name, ?ItemCount)) ).\r\n";
        CHECK(compiler->Compile(testState));
        unifier = compiler->SolveGoals();
        finalUnifier = HtnGoalResolver::ToString(unifier.get());
        CHECK_EQUAL(finalUnifier, "null");

        // ***** single max() goal where all terms succeed
        compiler->Clear();
        testState = string() +
        "itemsInBag(Name1, 1). \r\n" +
        "itemsInBag(Name2, 2). \r\n" +
        "trace(?x) :- .\r\n" +
        "goals( max(?Total, ?ItemCount, itemsInBag(?Name, ?ItemCount)) ).\r\n";
        CHECK(compiler->Compile(testState));
        unifier = compiler->SolveGoals();
        finalUnifier = HtnGoalResolver::ToString(unifier.get());
        CHECK_EQUAL(finalUnifier, "((?Total = 2))");

        // ***** single max() goal that is preceeded and succeeded by more goals to make sure unifiers flow through properly
        compiler->Clear();
        testState = string() +
        "itemsInBag(Name1, 1). \r\n" +
        "itemsInBag(Name2, 2). \r\n" +
        "countToString(1, One). \r\n"
        "trace(?x) :- .\r\n" +
        "goals( itemsInBag(Name1, ?X), max(?Total, ?ItemCount, itemsInBag(?Name, ?ItemCount)), countToString(?X, ?Name) ).\r\n";
        CHECK(compiler->Compile(testState));
        unifier = compiler->SolveGoals();
        finalUnifier = HtnGoalResolver::ToString(unifier.get());
        CHECK_EQUAL(finalUnifier, "((?X = 1, ?Total = 2, ?Name = One))");
    }

    TEST(HtnGoalResolverSumTests)
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

        // ***** single sum() goal where all terms fail
        compiler->Clear();
        testState = string() +
        "trace(?x) :- .\r\n"
        "goals( sum(?Total, ?ItemCount, itemsInBag(?Name, ?ItemCount)) ).\r\n";
        CHECK(compiler->Compile(testState));
        unifier = compiler->SolveGoals();
        finalUnifier = HtnGoalResolver::ToString(unifier.get());
        CHECK_EQUAL(finalUnifier, "null");

        // ***** single sum() goal where all terms succeed, but the wrong variable is used for totalling
        compiler->Clear();
        testState = string() +
        "itemsInBag(Name1, 1). \r\n" +
        "itemsInBag(Name2, 2). \r\n" +
        "trace(?x) :- .\r\n"
        "goals( sum(?Total, ?NotThere, itemsInBag(?Name, ?ItemCount)) ).\r\n";
        CHECK(compiler->Compile(testState));
        unifier = compiler->SolveGoals();
        finalUnifier = HtnGoalResolver::ToString(unifier.get());
        CHECK_EQUAL(finalUnifier, "null");

        // ***** single sum() goal where all terms succeed, but the variable is not ground
        compiler->Clear();
        testState = string() +
        "itemsInBag(Name1, ?Count) :- . \r\n" +
        "trace(?x) :- .\r\n" +
        "goals( sum(?Total, ?ItemCount, itemsInBag(?Name, ?ItemCount)) ).\r\n";
        CHECK(compiler->Compile(testState));
        unifier = compiler->SolveGoals();
        finalUnifier = HtnGoalResolver::ToString(unifier.get());
        CHECK_EQUAL(finalUnifier, "null");

        // ***** single sum() goal where all terms succeed
        compiler->Clear();
        testState = string() +
        "itemsInBag(Name1, 1). \r\n" +
        "itemsInBag(Name2, 2). \r\n" +
        "trace(?x) :- .\r\n" +
        "goals( sum(?Total, ?ItemCount, itemsInBag(?Name, ?ItemCount)) ).\r\n";
        CHECK(compiler->Compile(testState));
        unifier = compiler->SolveGoals();
        finalUnifier = HtnGoalResolver::ToString(unifier.get());
        CHECK_EQUAL(finalUnifier, "((?Total = 3))");

        // ***** single sum() goal that is preceeded and succeeded by more goals to make sure unifiers flow through properly
        compiler->Clear();
        testState = string() +
        "itemsInBag(Name1, 1). \r\n" +
        "itemsInBag(Name2, 2). \r\n" +
        "countToString(1, One). \r\n"
        "trace(?x) :- .\r\n" +
        "goals( itemsInBag(Name1, ?X), sum(?Total, ?ItemCount, itemsInBag(?Name, ?ItemCount)), countToString(?X, ?Name) ).\r\n";
        CHECK(compiler->Compile(testState));
        unifier = compiler->SolveGoals();
        finalUnifier = HtnGoalResolver::ToString(unifier.get());
        CHECK_EQUAL(finalUnifier, "((?X = 1, ?Total = 3, ?Name = One))");
    }

    TEST(HtnGoalResolverDistinctTests)
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

        // ***** no variables, no domain
        compiler->Clear();
        testState = string() +
        "letter(c). letter(b). letter(a).\r\n"
        "test(_) :- letter(_).\r\n"
        "trace(?x) :- .\r\n"
        "goals( distinct(_, test(_)) ).\r\n";
        CHECK(compiler->Compile(testState));
        unifier = compiler->SolveGoals();
        finalUnifier = HtnGoalResolver::ToString(unifier.get());
        CHECK_EQUAL(finalUnifier, "(())");

        // ***** single variable, no domain
        compiler->Clear();
        testState = string() +
        "letter(c). letter(b). letter(a).\r\n" +
        "trace(?x) :- .\r\n"
        "goals( distinct(_, letter(?X)) ).\r\n";
        CHECK(compiler->Compile(testState));
        unifier = compiler->SolveGoals();
        finalUnifier = HtnGoalResolver::ToString(unifier.get());
        CHECK_EQUAL(finalUnifier, "((?X = c), (?X = b), (?X = a))");

        // ***** multiple variables, no domain
        compiler->Clear();
        testState = string() +
        "letter(c). letter(b). letter(a).\r\n" +
        "trace(?x) :- .\r\n"
        "goals( distinct(_, letter(?X), letter(?Y)) ).\r\n";
        CHECK(compiler->Compile(testState));
        unifier = compiler->SolveGoals();
        finalUnifier = HtnGoalResolver::ToString(unifier.get());
        CHECK_EQUAL(finalUnifier, "((?X = c, ?Y = c), (?X = c, ?Y = b), (?X = c, ?Y = a), (?X = b, ?Y = c), (?X = b, ?Y = b), (?X = b, ?Y = a), (?X = a, ?Y = c), (?X = a, ?Y = b), (?X = a, ?Y = a))");

        // ***** single variable, with domain
        compiler->Clear();
        testState = string() +
        "letter(c). letter(b). letter(a).\r\n" +
        "trace(?x) :- .\r\n"
        "goals( distinct(?X, letter(?X)) ).\r\n";
        CHECK(compiler->Compile(testState));
        unifier = compiler->SolveGoals();
        finalUnifier = HtnGoalResolver::ToString(unifier.get());
        CHECK_EQUAL(finalUnifier, "((?X = c), (?X = b), (?X = a))");

        // ***** multiple variables (one unbound), with domain
        // which unbound gets chosen is indeterminate
        compiler->Clear();
        testState = string() +
        "letter(c). letter(b). letter(a).\r\n" +
        "trace(?x) :- .\r\n"
        "goals( distinct(?X, letter(?X), letter(?Y)) ).\r\n";
        CHECK(compiler->Compile(testState));
        unifier = compiler->SolveGoals();
        finalUnifier = HtnGoalResolver::ToString(unifier.get());
        CHECK_EQUAL(finalUnifier, "((?X = c, ?Y = c), (?X = b, ?Y = c), (?X = a, ?Y = c))");
    }

    TEST(HtnGoalResolverCountTests)
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

        // ***** single count() goal where all items fail
        compiler->Clear();
        testState = string() +
        "letter(c). letter(b). letter(a).\r\n" +
        "trace(?x) :- .\r\n"
        "goals( count(?Count, capitol(?X)) ).\r\n";
        CHECK(compiler->Compile(testState));
        unifier = compiler->SolveGoals();
        finalUnifier = HtnGoalResolver::ToString(unifier.get());
        CHECK_EQUAL(finalUnifier, "((?Count = 0))");

        // ***** single count() goal where all items succeed
        compiler->Clear();
        testState = string() +
        "letter(c). letter(b). letter(a).\r\n" +
        "capital(c). capital(b). capital(a).\r\n" +
        "cost(c, 1). cost(b, 2). cost(a, 3).\r\n" +
        "trace(?x) :- .\r\n"
        "goals( count(?Count, letter(?X)) ).\r\n";
        CHECK(compiler->Compile(testState));
        unifier = compiler->SolveGoals();
        finalUnifier = HtnGoalResolver::ToString(unifier.get());
        CHECK_EQUAL(finalUnifier, "((?Count = 3))");

        // Make sure count() can be used in math
        // ***** single count() goal where all items succeed
        compiler->Clear();
        testState = string() +
        "letter(c). letter(b). letter(a).\r\n" +
        "capital(c). capital(b). capital(a).\r\n" +
        "cost(c, 1). cost(b, 2). cost(a, 3).\r\n" +
        "trace(?x) :- .\r\n"
        "goals( count(?Count, letter(?X)), is(?Result, *(1, ?Count)) ).\r\n";
        CHECK(compiler->Compile(testState));
        unifier = compiler->SolveGoals();
        finalUnifier = HtnGoalResolver::ToString(unifier.get());
        CHECK_EQUAL(finalUnifier, "((?Count = 3, ?Result = 3))");

        // ***** single count() goal that is preceeded and succeeded by more goals to make sure unifiers flow through properly
        compiler->Clear();
        testState = string() +
        "letter(c). letter(b). letter(a).\r\n" +
        "capital(c). capital(b). capital(a).\r\n" +
        "cost(c, 1). cost(b, 2). cost(a, 3).\r\n" +
        "highCost(3).\r\n" +
        "trace(?x) :- .\r\n"
        "goals(letter(?X), count(?Count, letter(?Y)), capital(?Z) ).\r\n";
        CHECK(compiler->Compile(testState));
        unifier = compiler->SolveGoals();
        finalUnifier = HtnGoalResolver::ToString(unifier.get());
        // ?Y should not show up since it is in the count() clause
        CHECK_EQUAL(finalUnifier, "((?X = c, ?Count = 3, ?Z = c), (?X = c, ?Count = 3, ?Z = b), (?X = c, ?Count = 3, ?Z = a), (?X = b, ?Count = 3, ?Z = c), (?X = b, ?Count = 3, ?Z = b), (?X = b, ?Count = 3, ?Z = a), (?X = a, ?Count = 3, ?Z = c), (?X = a, ?Count = 3, ?Z = b), (?X = a, ?Count = 3, ?Z = a))");
    }
}
