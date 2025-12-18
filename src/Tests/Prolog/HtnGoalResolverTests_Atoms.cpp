//
//  HtnGoalResolverTests_Atoms.cpp
//  TestLib
//
//  String/atom operations and control flow: atom_chars, downcase, concat, write, variables, forall, atomic, true/false
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
    TEST(HtnGoalResolverAtomCharsTests)
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

        // ***** single atom_chars() goal that succeeds: variable on right
        // with unifiers on left and right to make sure they flow
        compiler->Clear();
        testState = string() +
            "goals(=(?X, pre), atom_chars(foo, ?List), =(?Y, ?X), =(?Z, ?List) ).\r\n";
        CHECK(compiler->Compile(testState));
        unifier = compiler->SolveGoals();
        finalUnifier = HtnGoalResolver::ToString(unifier.get());
        CHECK_EQUAL(finalUnifier, "((?X = pre, ?List = [f,o,o], ?Y = pre, ?Z = [f,o,o]))");

        // ***** single atom_chars() goal that succeeds: variable on left
        // with unifiers on left and right to make sure they flow
        compiler->Clear();
        testState = string() +
            "goals(=(?X, pre), atom_chars(?List, [f, o, o]), =(?Y, ?X), =(?Z, ?List) ).\r\n";
        CHECK(compiler->Compile(testState));
        unifier = compiler->SolveGoals();
        finalUnifier = HtnGoalResolver::ToString(unifier.get());
        CHECK_EQUAL(finalUnifier, "((?X = pre, ?List = foo, ?Y = pre, ?Z = foo))");

        // ***** single atom_chars() goal that succeeds: more advanced case
        // with unifiers on left and right to make sure they flow
        compiler->Clear();
        testState = string() +
            "goals(=(?X, pre), atom_chars(foo, [?FirstChar | _]), =(?Y, ?X), =(?Z, ?FirstChar) ).\r\n";
        CHECK(compiler->Compile(testState));
        unifier = compiler->SolveGoals();
        finalUnifier = HtnGoalResolver::ToString(unifier.get());
        CHECK_EQUAL(finalUnifier, "((?X = pre, ?FirstChar = f, ?Y = pre, ?Z = f))");
    }

    TEST(HtnGoalResolverAtomDowncaseTests)
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

        // ***** single downcase_atom() goal that succeeds
        compiler->Clear();
        testState = string() +
            "goals(downcase_atom('THIS IS A TEST', ?x) ).\r\n";
        CHECK(compiler->Compile(testState));
        unifier = compiler->SolveGoals();
        finalUnifier = HtnGoalResolver::ToString(unifier.get());
        CHECK_EQUAL(finalUnifier, "((?x = this is a test))");

        // ***** single downcase_atom() goal that is preceeded and succeeded by more goals to make sure unifiers flow through properly
        compiler->Clear();
        testState = string() +
            "letter(C). letter(B). letter(A).\r\n" +
            "capital(c). capital(b). capital(a).\r\n" +
            "cost(c, 1). cost(ab, 2). cost(a, 3).\r\n" +
            "highCost(3).\r\n" +
            "trace(?x) :- .\r\n"
            "goals( letter(?X), downcase_atom(?X, ?Y), cost(?Y, ?Cost) ).\r\n";
        CHECK(compiler->Compile(testState));
        unifier = compiler->SolveGoals();
        finalUnifier = HtnGoalResolver::ToString(unifier.get());
        CHECK_EQUAL(finalUnifier, "((?X = C, ?Y = c, ?Cost = 1), (?X = A, ?Y = a, ?Cost = 3))");
    }

    TEST(HtnGoalResolverAtomConcatTests)
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

        // ***** single atom_concat() goal that succeeds
        compiler->Clear();
        testState = string() +
            "goals(atom_concat(a, b, ?x) ).\r\n";
        CHECK(compiler->Compile(testState));
        unifier = compiler->SolveGoals();
        finalUnifier = HtnGoalResolver::ToString(unifier.get());
        CHECK_EQUAL(finalUnifier, "((?x = ab))");

        // ***** single atom_concat() goal that is preceeded and succeeded by more goals to make sure unifiers flow through properly
        compiler->Clear();
        testState = string() +
            "letter(c). letter(b). letter(a).\r\n" +
            "capital(c). capital(b). capital(a).\r\n" +
            "cost(c, 1). cost(ab, 2). cost(a, 3).\r\n" +
            "highCost(3).\r\n" +
            "trace(?x) :- .\r\n"
            "goals( letter(?X), atom_concat(?X, b, ?Y), cost(?Y, ?Cost) ).\r\n";
        CHECK(compiler->Compile(testState));
        unifier = compiler->SolveGoals();
        finalUnifier = HtnGoalResolver::ToString(unifier.get());
        CHECK_EQUAL(finalUnifier, "((?X = a, ?Y = ab, ?Cost = 2))");
    }

    TEST(HtnGoalResolverWriteTests)
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

        // ***** Make sure string literals work
        compiler->Clear();
        testState = string() +
        "goals( write('Test \"of the emergency\"') ).\r\n";
        CHECK(compiler->Compile(testState));

        // Redirect cout to catch output
        std::stringstream out;
        std::streambuf *coutbuf = std::cout.rdbuf(); //save old buf
        std::cout.rdbuf(out.rdbuf()); //redirect std::cout to out.txt!

        unifier = compiler->SolveGoals();
        finalUnifier = HtnGoalResolver::ToString(unifier.get());
        CHECK_EQUAL(finalUnifier, "(())");
        CHECK_EQUAL(out.str(), "Test \"of the emergency\"");
        std::cout.rdbuf(coutbuf); //reset to standard output again

        // ***** Make sure nl works
        compiler->Clear();
        testState = string() +
        "goals( nl ).\r\n";
        CHECK(compiler->Compile(testState));

        // Redirect cout to catch output
        out = stringstream();
        coutbuf = std::cout.rdbuf(); //save old buf
        std::cout.rdbuf(out.rdbuf()); //redirect std::cout to out.txt!

        unifier = compiler->SolveGoals();
        finalUnifier = HtnGoalResolver::ToString(unifier.get());
        CHECK_EQUAL(finalUnifier, "(())");
        stringstream newline;
        newline << endl;
        CHECK_EQUAL(out.str(), newline.str());
        std::cout.rdbuf(coutbuf); //reset to standard output again

        // ***** Make sure writeln works
        compiler->Clear();
        testState = string() +
        "goals( writeln('test') ).\r\n";
        CHECK(compiler->Compile(testState));

        // Redirect cout to catch output
        out = stringstream();
        coutbuf = std::cout.rdbuf(); //save old buf
        std::cout.rdbuf(out.rdbuf()); //redirect std::cout to out.txt!

        unifier = compiler->SolveGoals();
        finalUnifier = HtnGoalResolver::ToString(unifier.get());
        CHECK_EQUAL(finalUnifier, "(())");
        newline = stringstream();
        newline << "test" << endl;
        CHECK_EQUAL(out.str(), newline.str());
        std::cout.rdbuf(coutbuf); //reset to standard output again

        // ***** Make sure variables aren't unified
        compiler->Clear();
        testState = string() +
        "itemsInBag(Name1, Name1). \r\n" +
        "itemsInBag(Name2, Name3). \r\n" +
        "goals( write(itemsInBag(?X)) ).\r\n";
        CHECK(compiler->Compile(testState));

        // Redirect cout to catch output
        out = stringstream();
        coutbuf = std::cout.rdbuf(); //save old buf
        std::cout.rdbuf(out.rdbuf()); //redirect std::cout to out.txt!

        unifier = compiler->SolveGoals();
        finalUnifier = HtnGoalResolver::ToString(unifier.get());
        CHECK_EQUAL(finalUnifier, "(())");
        CHECK_EQUAL(out.str(), "itemsInBag(?orig*X)");
        std::cout.rdbuf(coutbuf); //reset to standard output again
    }

	TEST(HtnGoalResolverVariableTests)
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
        // ***** Make sure the same variables in terms of a conjunction get mapped to the same renamed variables
        compiler->Clear();
        testState = string() +
        "name(Name1). \r\n" +
        "name(Name4). \r\n" +
        "itemsInBag(Name1, Name1). \r\n" +
        "itemsInBag(Name2, Name3). \r\n" +
        "goals( itemsInBag(?X, ?X), name(?X) ).\r\n";
        CHECK(compiler->Compile(testState));
        unifier = compiler->SolveGoals();
        finalUnifier = HtnGoalResolver::ToString(unifier.get());
        CHECK_EQUAL(finalUnifier, "((?X = Name1))");

		// ***** Make sure the same variables get mapped to the same renamed variables
		compiler->Clear();
		testState = string() +
			"itemsInBag(Name1, Name1). \r\n" +
			"itemsInBag(Name2, Name3). \r\n" +
			"goals( itemsInBag(?X, ?X) ).\r\n";
		CHECK(compiler->Compile(testState));
		unifier = compiler->SolveGoals();
		finalUnifier = HtnGoalResolver::ToString(unifier.get());
		CHECK_EQUAL(finalUnifier, "((?X = Name1))");

		// ***** dontcare variables match anything and aren't returned
		compiler->Clear();
		testState = string() +
			"itemsInBag(Name1). \r\n" +
			"itemsInBag(Name2). \r\n" +
			"rule(?X) :- itemsInBag(_), itemsInBag(?X)."
			"goals( rule(?X) ).\r\n";
		CHECK(compiler->Compile(testState));
		unifier = compiler->SolveGoals();
		finalUnifier = HtnGoalResolver::ToString(unifier.get());
		CHECK_EQUAL(finalUnifier, "((?X = Name1), (?X = Name2), (?X = Name1), (?X = Name2))");

		// ***** dontcare variables in a query aren't returned
		compiler->Clear();
		testState = string() +
			"itemsInBag(Name1). \r\n" +
			"itemsInBag(Name2). \r\n" +
			"rule(?X) :- itemsInBag(_), itemsInBag(?X)."
			"goals( rule(_) ).\r\n";
		CHECK(compiler->Compile(testState));
		unifier = compiler->SolveGoals();
		finalUnifier = HtnGoalResolver::ToString(unifier.get());
		CHECK_EQUAL(finalUnifier, "((), (), (), ())");

        // ***** Don't care variables aren't mapped to be the same name, they are always different
        // Also: Need to work in initial goal
        compiler->Clear();
        testState = string() +
            "itemsInBag(Name1, Name1). \r\n" +
            "itemsInBag(Name2, Name3). \r\n" +
            "goals( itemsInBag(_, _) ).\r\n";
        CHECK(compiler->Compile(testState));
        unifier = compiler->SolveGoals();
        finalUnifier = HtnGoalResolver::ToString(unifier.get());
        CHECK_EQUAL(finalUnifier, "((), ())");

        // Rules with don't care variables should be matched by goals with anything
        compiler->Clear();
        testState = string() +
            "test(_, _). \r\n" +
            "goals( test(a, b) ).\r\n";
        CHECK(compiler->Compile(testState));
        unifier = compiler->SolveGoals();
        finalUnifier = HtnGoalResolver::ToString(unifier.get());
        CHECK_EQUAL("(())", finalUnifier);

        // Once a variable is renamed it shouldn't be again
        compiler->Clear();
        testState = string() +
        "valid(a, b)."
        "valid(a, c)."
        "valid(b, c)."
        "test(?X, ?Y) :- valid(?X, ?Y), test2(?X, ?Y)."
        "test2(?X, ?Y) :- valid(?X, b)."
        "goals( test(_, ?X) ).\r\n";
        CHECK(compiler->Compile(testState));
        unifier = compiler->SolveGoals();
        finalUnifier = HtnGoalResolver::ToString(unifier.get());
        CHECK_EQUAL("((?X = b), (?X = c))", finalUnifier);

        // Rules with don't care variables should be matched by goals with don't care variables
        compiler->Clear();
        testState = string() +
            "test(_, _) :- test2(_, _). \r\n" +
            "test2(_, _). \r\n" +
            "goals( test(_, _) ).\r\n";
        CHECK(compiler->Compile(testState));
        unifier = compiler->SolveGoals();
        finalUnifier = HtnGoalResolver::ToString(unifier.get());
        CHECK_EQUAL("(())", finalUnifier);
//
        // Rules with don't care variables should be matched by goals with anything
        compiler->Clear();
        testState = string() +
            "test(_, _) :- test2(_, _). \r\n" +
            "test2(_, _). \r\n" +
            "goals( test(a, b) ).\r\n";
        CHECK(compiler->Compile(testState));
        unifier = compiler->SolveGoals();
        finalUnifier = HtnGoalResolver::ToString(unifier.get());
        CHECK_EQUAL("(())", finalUnifier);
	}

    TEST(HtnGoalResolverForAllTests)
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

        std::stringstream out;
        std::stringstream expectedOut;
        std::streambuf *coutbuf;

        // Make sure we loop over all alternatives
        compiler->Clear();
        testState = string() +
        "item(a)." +
        "item(b)." +
        "has(item(a)).    "
        "has(item(b)).    "
        "rule(?A) :- has(?A), writeln(?A)."
        "goals( forall(item(?X), rule(item(?X))) ).\r\n";
        CHECK(compiler->Compile(testState));

        // Redirect cout to catch output
        out = std::stringstream();
        coutbuf = std::cout.rdbuf(); //save old buf
        std::cout.rdbuf(out.rdbuf()); //redirect std::cout to out.txt!

        unifier = compiler->SolveGoals();
        finalUnifier = HtnGoalResolver::ToString(unifier.get());
        CHECK_EQUAL(finalUnifier, "(())");
        expectedOut = std::stringstream();
        expectedOut << "item(a)" << endl << "item(b)" << endl;
        CHECK_EQUAL(out.str(), expectedOut.str());
        std::cout.rdbuf(coutbuf); //reset to standard output again

        // Make sure we don't bind variables outside the foreach()
        compiler->Clear();
        testState = string() +
        "item(a)." +
        "item(b)." +
        "has(item(a)).    "
        "has(item(b)).    "
        "rule(?A) :- has(?A), writeln(?A)."
        "goals( forall( item(?X), rule(item(?X)) ), writeln(item(?X)) ).\r\n";
        CHECK(compiler->Compile(testState));

        // Redirect cout to catch output
        out = std::stringstream();
        coutbuf = std::cout.rdbuf(); //save old buf
        std::cout.rdbuf(out.rdbuf()); //redirect std::cout to out.txt!

        unifier = compiler->SolveGoals();
        finalUnifier = HtnGoalResolver::ToString(unifier.get());
        CHECK_EQUAL(finalUnifier, "(())");
        expectedOut = std::stringstream();
        expectedOut << "item(a)" << endl << "item(b)" << endl << "item(?orig*X)" << endl;
        string temp = out.str();
        CHECK_EQUAL(out.str(), expectedOut.str());
        std::cout.rdbuf(coutbuf); //reset to standard output again


        // Make sure we stop immediately when we fail and don't backtrack over other solutions
        compiler->Clear();
        testState = string() +
        "item(a)." +
        "item(b)." +
        "has(item(b)).	"
        "rule(?A) :- has(?A), writeln(?A)."
        "goals( forall(item(?X), rule(item(?X))) ).\r\n";
        CHECK(compiler->Compile(testState));

        // Redirect cout to catch output
        out = std::stringstream();
        coutbuf = std::cout.rdbuf(); //save old buf
        std::cout.rdbuf(out.rdbuf()); //redirect std::cout to out.txt!

        unifier = compiler->SolveGoals();
        finalUnifier = HtnGoalResolver::ToString(unifier.get());
        CHECK_EQUAL(finalUnifier, "null");
        CHECK_EQUAL(out.str(), "");
        std::cout.rdbuf(coutbuf); //reset to standard output again
    }

    TEST(HtnGoalResolverAtomicTests)
    {
        HtnGoalResolver resolver;
        shared_ptr<HtnTermFactory> factory = shared_ptr<HtnTermFactory>(new HtnTermFactory());
        shared_ptr<HtnRuleSet> state = shared_ptr<HtnRuleSet>(new HtnRuleSet());
        shared_ptr<PrologCompiler> compiler = shared_ptr<PrologCompiler>(new PrologCompiler(factory.get(), state.get()));
        string testState;
        string goals;
        string finalUnifier;
        shared_ptr<vector<UnifierType>> unifier;

        // ***** atomic(mia). should resolve to true
        compiler->Clear();
        testState = string() +
            "goals(atomic(mia)).\r\n";
        CHECK(compiler->Compile(testState));
        unifier = compiler->SolveGoals();
        finalUnifier = HtnGoalResolver::ToString(unifier.get());
        CHECK_EQUAL(finalUnifier, "(())");

        // ***** atomic(mia()). should resolve to true
        compiler->Clear();
        testState = string() +
            "goals(atomic(mia())).\r\n";
        CHECK(compiler->Compile(testState));
        unifier = compiler->SolveGoals();
        finalUnifier = HtnGoalResolver::ToString(unifier.get());
        CHECK_EQUAL(finalUnifier, "(())");

        // ***** atomic(8). should resolve to true
        compiler->Clear();
        testState = string() +
            "goals(atomic(8)).\r\n";
        CHECK(compiler->Compile(testState));
        unifier = compiler->SolveGoals();
        finalUnifier = HtnGoalResolver::ToString(unifier.get());
        CHECK_EQUAL(finalUnifier, "(())");

        // ***** atomic(3.25). should resolve to true
        compiler->Clear();
        testState = string() +
            "goals(atomic(3.25)).\r\n";
        CHECK(compiler->Compile(testState));
        unifier = compiler->SolveGoals();
        finalUnifier = HtnGoalResolver::ToString(unifier.get());
        CHECK_EQUAL(finalUnifier, "(())");

        // ***** atomic(loves(vincent, mia)). should resolve to false
        compiler->Clear();
        testState = string() +
            "goals(atomic(loves(vincent, mia))).\r\n";
        CHECK(compiler->Compile(testState));
        unifier = compiler->SolveGoals();
        finalUnifier = HtnGoalResolver::ToString(unifier.get());
        CHECK_EQUAL(finalUnifier, "null");

        // ***** atomic(?X) (unbound variable) should resolve to False
        compiler->Clear();
        testState = string() +
            "goals(atomic(?X)).\r\n";
        CHECK(compiler->Compile(testState));
        unifier = compiler->SolveGoals();
        finalUnifier = HtnGoalResolver::ToString(unifier.get());
        CHECK_EQUAL(finalUnifier, "null");

        // ***** atomic(?X) (bound variable) should resolve to True
        compiler->Clear();
        testState = string() +
            "goals(=(?X, mia), atomic(?X)).\r\n";
        CHECK(compiler->Compile(testState));
        unifier = compiler->SolveGoals();
        finalUnifier = HtnGoalResolver::ToString(unifier.get());
        CHECK_EQUAL(finalUnifier, "((?X = mia))");
    }

    TEST(HtnGoalResolverTrueFalseTests)
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

        // ***** true should resolve to true
        compiler->Clear();
        testState = string() +
        "goals( true ).\r\n";
        CHECK(compiler->Compile(testState));
        unifier = compiler->SolveGoals();
        finalUnifier = HtnGoalResolver::ToString(unifier.get());
        CHECK_EQUAL(finalUnifier, "(())");

        // ***** false should resolve to false
        compiler->Clear();
        testState = string() +
        "goals( false ).\r\n";
        CHECK(compiler->Compile(testState));
        unifier = compiler->SolveGoals();
        finalUnifier = HtnGoalResolver::ToString(unifier.get());
        CHECK_EQUAL(finalUnifier, "null");
    }
}
