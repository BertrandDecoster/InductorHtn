//
//  HtnPlannerTests_Basics.cpp
//  TestLib
//
//  Created by Eric Zinda on 1/8/19.
//  Copyright © 2019 Eric Zinda. All rights reserved.
//
//  Core planner fundamentals: error context, operators, methods, arithmetic.
//
#include "AIHarness.h"
#include "Prolog/HtnGoalResolver.h"
#include "FXPlatform/Htn/HtnCompiler.h"
#include "FXPlatform/Htn/HtnPlanner.h"
#include "FXPlatform/Prolog/HtnRuleSet.h"
#include "FXPlatform/Prolog/HtnTerm.h"
#include "FXPlatform/Prolog/HtnTermFactory.h"
#include "Tests/ParserTestBase.h"
#include "Logger.h"
#include <thread>
#include "UnitTest++/UnitTest++.h"
using namespace Prolog;

SUITE(HtnPlannerTests)
{
    TEST(ErrorContextTest)
    {
        shared_ptr<HtnTermFactory> factory = shared_ptr<HtnTermFactory>(new HtnTermFactory());
        shared_ptr<HtnRuleSet> state = shared_ptr<HtnRuleSet>(new HtnRuleSet());
        shared_ptr<HtnPlanner> planner = shared_ptr<HtnPlanner>(new HtnPlanner());
        shared_ptr<HtnCompiler> compiler = shared_ptr<HtnCompiler>(new HtnCompiler(factory.get(), state.get(), planner.get()));
        shared_ptr<HtnPlanner::SolutionsType> result;
        string finalFacts;
        string finalPlan;
        string testState;
        string sharedState;
        string goals;
        shared_ptr<vector<UnifierType>> unifier;
        int64_t memoryUsed;
        int deepestFailureIndex;
        std::vector<std::shared_ptr<HtnTerm>> deepestFailureContext;
        string failureContext;

        // State true for all tests
        sharedState = string() +
        "";

        // no failure context
        compiler->ClearWithNewRuleSet();
        testState = string() +
        "failInCriteria(?Value) :- if(false), do(trace(?Value))."
        "trace(?Value) :- del(), add(?Value). \r\n" +
        "";
        goals = string() +
        "goals(failInCriteria(test)).\r\n" +
        "";
        CHECK(compiler->Compile(sharedState + testState + goals));
        result = planner->FindAllPlans(factory.get(), compiler->compilerOwnedRuleSet(), compiler->goals(), 5000000,
                                       &memoryUsed, &deepestFailureIndex, &deepestFailureContext);
        finalPlan = HtnPlanner::ToStringSolutions(result);
        failureContext = HtnTerm::ToString(deepestFailureContext);
        CHECK_EQUAL("null", finalPlan);
        CHECK_EQUAL("()", failureContext);

        // simplest case
        compiler->ClearWithNewRuleSet();
        testState = string() +
        "failInCriteria(?Value) :- if(failureContext(tag, 1), false), do(trace(?Value))."
        "trace(?Value) :- del(), add(?Value). \r\n" +
        "";
        goals = string() +
        "goals(failInCriteria(test)).\r\n" +
        "";
        CHECK(compiler->Compile(sharedState + testState + goals));
        result = planner->FindAllPlans(factory.get(), compiler->compilerOwnedRuleSet(), compiler->goals(), 5000000,
                                       &memoryUsed, &deepestFailureIndex, &deepestFailureContext);
        finalPlan = HtnPlanner::ToStringSolutions(result);
        failureContext = HtnTerm::ToString(deepestFailureContext);
        CHECK_EQUAL("null", finalPlan);
        CHECK_EQUAL("(tag, 1)", failureContext);

        // first criteria fails further in the criteria term list
        compiler->ClearWithNewRuleSet();
        testState = string() +
        "failInCriteria(?Value) :- if(=(?X, 1), failureContext(tag, 1), failTask([1,2,3]) ), do(trace(?Value))."
        "failInCriteria(?Value) :- if(failureContext(tag, 2), failTask([1,2]) ), do(trace(?Value))."
        "trace(?Value) :- del(), add(?Value). \r\n"
        "failTask([]) :- false."
        "failTask([_|T]) :- failTask(T)."
        "";
        goals = string() +
        "goals(failInCriteria(test)).\r\n" +
        "";
        CHECK(compiler->Compile(sharedState + testState + goals));
        result = planner->FindAllPlans(factory.get(), compiler->compilerOwnedRuleSet(), compiler->goals(), 5000000,
                                       &memoryUsed, &deepestFailureIndex, &deepestFailureContext);
        finalPlan = HtnPlanner::ToStringSolutions(result);
        failureContext = HtnTerm::ToString(deepestFailureContext);
        CHECK_EQUAL("null", finalPlan);
        CHECK_EQUAL("(tag, 1)", failureContext);

        // second criteria fails further in the criteria term list
        compiler->ClearWithNewRuleSet();
        testState = string() +
        "failInCriteria(?Value) :- if(failureContext(tag, 1), failTask([1,2]) ), do(trace(?Value))."
        "failInCriteria(?Value) :- if(=(?X, 1), failureContext(tag, 2), failTask([1,2,3]) ), do(trace(?Value))."
        "trace(?Value) :- del(), add(?Value). \r\n"
        "failTask([]) :- false."
        "failTask([_|T]) :- failTask(T)."
        "";
        goals = string() +
        "goals(failInCriteria(test)).\r\n" +
        "";
        CHECK(compiler->Compile(sharedState + testState + goals));
        result = planner->FindAllPlans(factory.get(), compiler->compilerOwnedRuleSet(), compiler->goals(), 5000000,
                                       &memoryUsed, &deepestFailureIndex, &deepestFailureContext);
        finalPlan = HtnPlanner::ToStringSolutions(result);
        failureContext = HtnTerm::ToString(deepestFailureContext);
        CHECK_EQUAL("null", finalPlan);
        CHECK_EQUAL("(tag, 2)", failureContext);
    }

    TEST(PlannerOperatorTest)
    {
        shared_ptr<HtnTermFactory> factory = shared_ptr<HtnTermFactory>(new HtnTermFactory());
        shared_ptr<HtnRuleSet> state = shared_ptr<HtnRuleSet>(new HtnRuleSet());
        shared_ptr<HtnPlanner> planner = shared_ptr<HtnPlanner>(new HtnPlanner());
        shared_ptr<HtnCompiler> compiler = shared_ptr<HtnCompiler>(new HtnCompiler(factory.get(), state.get(), planner.get()));
        shared_ptr<HtnPlanner::SolutionsType> result;
        string finalFacts;
        string finalPlan;
        string testState;
        string sharedState;
        string goals;
        shared_ptr<vector<UnifierType>> unifier;

        // State true for all tests
        sharedState = string() +
        "";

        // No goals
        compiler->ClearWithNewRuleSet();
        testState = string() +
        "trace(?Value) :- del(), add(?Value). \r\n" +
        "";
        goals = string() +
        "goals().\r\n" +
        "";
        CHECK(compiler->Compile(sharedState + testState + goals));
        result = planner->FindAllPlans(factory.get(), compiler->compilerOwnedRuleSet(), compiler->goals());
        finalPlan = HtnPlanner::ToStringSolutions(result);
        CHECK_EQUAL(finalPlan, "[ { () } ]");
        finalFacts = HtnPlanner::ToStringFacts(result);
        CHECK_EQUAL(finalFacts,  "[ {  } ]");

        // first operator doesn't unify
        compiler->ClearWithNewRuleSet();
        testState = string() +
        "trace(?Value) :- del(), add(?Value). \r\n" +
        "";
        goals = string() +
        "goals(trace(Test1, Test3), trace(Test2)).\r\n" +
        "";
        CHECK(compiler->Compile(sharedState + testState + goals));
        result = planner->FindAllPlans(factory.get(), compiler->compilerOwnedRuleSet(), compiler->goals());
        finalPlan = HtnPlanner::ToStringSolutions(result);
        CHECK_EQUAL(finalPlan, "null");
        finalFacts = HtnPlanner::ToStringFacts(result);
        CHECK_EQUAL(finalFacts,  "null");

        // last operator doesn't unify
        compiler->ClearWithNewRuleSet();
        testState = string() +
        "trace(?Value) :- del(), add(?Value). \r\n" +
        "";
        goals = string() +
        "goals(trace(Test1), trace(Test2, Test3)).\r\n" +
        "";
        CHECK(compiler->Compile(sharedState + testState + goals));
        result = planner->FindAllPlans(factory.get(), compiler->compilerOwnedRuleSet(), compiler->goals());
        finalPlan = HtnPlanner::ToStringSolutions(result);
        CHECK_EQUAL(finalPlan, "null");
        finalFacts = HtnPlanner::ToStringFacts(result);
        CHECK_EQUAL(finalFacts,  "null");

        // One successful operator
        compiler->ClearWithNewRuleSet();
        testState = string() +
        "trace(?Value) :- del(), add(?Value). \r\n" +
        "";
        goals = string() +
        "goals(trace(Test1)).\r\n" +
        "";
        CHECK(compiler->Compile(sharedState + testState + goals));
        result = planner->FindAllPlans(factory.get(), compiler->compilerOwnedRuleSet(), compiler->goals());
        finalPlan = HtnPlanner::ToStringSolutions(result);
        CHECK_EQUAL(finalPlan, "[ { (trace(Test1)) } ]");
        finalFacts = HtnPlanner::ToStringFacts(result);
        CHECK_EQUAL(finalFacts,  "[ { Test1 =>  } ]");

        // Just two successful operators
        compiler->ClearWithNewRuleSet();
        testState = string() +
        "trace(?Value) :- del(), add(?Value). \r\n" +
        "";
        goals = string() +
        "goals(trace(Test1), trace(Test2)).\r\n" +
        "";
        CHECK(compiler->Compile(sharedState + testState + goals));
        result = planner->FindAllPlans(factory.get(), compiler->compilerOwnedRuleSet(), compiler->goals());
        finalPlan = HtnPlanner::ToStringSolutions(result);
        CHECK_EQUAL(finalPlan, "[ { (trace(Test1), trace(Test2)) } ]");
        finalFacts = HtnPlanner::ToStringFacts(result);
        CHECK_EQUAL(finalFacts,  "[ { Test1 => ,Test2 =>  } ]");
    }

    TEST(PlannerNormalMethodTest)
    {
//                SetTraceFilter((int) SystemTraceType::Solver | (int) SystemTraceType::System, TraceDetail::Diagnostic);

        shared_ptr<HtnTermFactory> factory = shared_ptr<HtnTermFactory>(new HtnTermFactory());
        shared_ptr<HtnRuleSet> state = shared_ptr<HtnRuleSet>(new HtnRuleSet());
        shared_ptr<HtnPlanner> planner = shared_ptr<HtnPlanner>(new HtnPlanner());
        shared_ptr<HtnCompiler> compiler = shared_ptr<HtnCompiler>(new HtnCompiler(factory.get(), state.get(), planner.get()));
        shared_ptr<HtnPlanner::SolutionsType> result;
        string finalFacts;
        string finalPlan;
        string testState;
        string sharedState;
        string goals;
        shared_ptr<vector<UnifierType>> unifier;

        // State true for all tests
        sharedState = string() +
        "";

        // Single goal that does not match any methods
        compiler->ClearWithNewRuleSet();
        testState = string() +
        "trace(?Value) :- del(), add(?Value). \r\n" +
        "method(?Value) :- if(IsTrue(?Value)), do(trace(?Value)). \r\n" +
        "";
        goals = string() +
        "goals(method1(Test1)).\r\n" +
        "";
        CHECK(compiler->Compile(sharedState + testState + goals));
        result = planner->FindAllPlans(factory.get(), compiler->compilerOwnedRuleSet(), compiler->goals());
        finalPlan = HtnPlanner::ToStringSolutions(result);
        CHECK_EQUAL(finalPlan, "null");
        finalFacts = HtnPlanner::ToStringFacts(result);
        CHECK_EQUAL(finalFacts,  "null");

        // Single method with one condition which does not resolve to ground
        compiler->ClearWithNewRuleSet();
        testState = string() +
        "trace(?Value) :- del(), add(?Value). \r\n" +
        "method(?Value) :- if(IsTrue(?Value)), do(trace(?Value)). \r\n" +
        "";
        goals = string() +
        "goals(method(Test1)).\r\n" +
        "";
        CHECK(compiler->Compile(sharedState + testState + goals));
        result = planner->FindAllPlans(factory.get(), compiler->compilerOwnedRuleSet(), compiler->goals());
        finalPlan = HtnPlanner::ToStringSolutions(result);
        CHECK_EQUAL(finalPlan, "null");
        finalFacts = HtnPlanner::ToStringFacts(result);
        CHECK_EQUAL(finalFacts,  "null");

        // Single method with one binding
        compiler->ClearWithNewRuleSet();
        testState = string() +
        "IsTrue(Test1). \r\n" +
        "trace(?Value) :- del(), add(?Value). \r\n" +
        "method(?Value) :- if(IsTrue(?Value)), do(trace(?Value)). \r\n" +
        "";
        goals = string() +
        "goals(method(Test1)).\r\n" +
        "";
        CHECK(compiler->Compile(sharedState + testState + goals));
        result = planner->FindAllPlans(factory.get(), compiler->compilerOwnedRuleSet(), compiler->goals());
        finalPlan = HtnPlanner::ToStringSolutions(result);
        CHECK_EQUAL(finalPlan, "[ { (trace(Test1)) } ]");
        finalFacts = HtnPlanner::ToStringFacts(result);
        CHECK_EQUAL(finalFacts,  "[ { IsTrue(Test1) => ,Test1 =>  } ]");

        // Two methods with single bindings: 2 separate answers
        compiler->ClearWithNewRuleSet();
        testState = string() +
        "IsTrue(Test1). \r\n" +
        "trace(?Value, ?Value2) :- del(), add(?Value, ?Value2). \r\n" +
        "method(?Value) :- if(IsTrue(?Value)), do(trace(?Value, Method1)). \r\n" +
        "method(?Value) :- if(IsTrue(?Value)), do(trace(?Value, Method2)). \r\n" +
        "";
        goals = string() +
        "goals(method(Test1)).\r\n" +
        "";
        CHECK(compiler->Compile(sharedState + testState + goals));
        result = planner->FindAllPlans(factory.get(), compiler->compilerOwnedRuleSet(), compiler->goals());
        finalPlan = HtnPlanner::ToStringSolutions(result);
        CHECK_EQUAL(finalPlan, "[ { (trace(Test1,Method1)) } { (trace(Test1,Method2)) } ]");
        finalFacts = HtnPlanner::ToStringFacts(result);
        CHECK_EQUAL(finalFacts,  "[ { IsTrue(Test1) => ,Test1 => ,Method1 =>  } { IsTrue(Test1) => ,Test1 => ,Method2 =>  } ]");

        // Two methods with two condition bindings each: 4 separate answers
        compiler->ClearWithNewRuleSet();
        testState = string() +
        "IsTrue(Test1). Alternative(Alternative1). Alternative(Alternative2).\r\n" +
        "trace(?Value, ?Value2, ?Value3) :- del(), add(?Value, ?Value2). \r\n" +
        "method(?Value) :- if(IsTrue(?Value), Alternative(?Alt)), do(trace(?Value, Method1, ?Alt)). \r\n" +
        "method(?Value) :- if(IsTrue(?Value), Alternative(?Alt)), do(trace(?Value, Method2, ?Alt)). \r\n" +
        "";
        goals = string() +
        "goals(method(Test1)).\r\n" +
        "";
        CHECK(compiler->Compile(sharedState + testState + goals));
        result = planner->FindAllPlans(factory.get(), compiler->compilerOwnedRuleSet(), compiler->goals());
        finalPlan = HtnPlanner::ToStringSolutions(result);
        CHECK_EQUAL(finalPlan, "[ { (trace(Test1,Method1,Alternative1)) } { (trace(Test1,Method1,Alternative2)) } { (trace(Test1,Method2,Alternative1)) } { (trace(Test1,Method2,Alternative2)) } ]");
        finalFacts = HtnPlanner::ToStringFacts(result);
        CHECK_EQUAL(finalFacts,  "[ { IsTrue(Test1) => ,Alternative(Alternative1) => ,Alternative(Alternative2) => ,Test1 => ,Method1 =>  } { IsTrue(Test1) => ,Alternative(Alternative1) => ,Alternative(Alternative2) => ,Test1 => ,Method1 =>  } { IsTrue(Test1) => ,Alternative(Alternative1) => ,Alternative(Alternative2) => ,Test1 => ,Method2 =>  } { IsTrue(Test1) => ,Alternative(Alternative1) => ,Alternative(Alternative2) => ,Test1 => ,Method2 =>  } ]");

        // ***** Variables should be properly scoped such that reusing the same name in different terms works (i.e. you can use X in the do() part of a method
        // and a different X in a different method and they will unify properly
        string example = string() +
        "test(?X) :- if(), do(successTask(10, ?X)) .\r\n" +
        "successTask(?X, ?Y) :- if(number(?X)), do(debugWatch(?X)).\r\n" +
        "debugWatch(?x) :- del(), add().\r\n" +
        "";
        compiler->ClearWithNewRuleSet();
        testState = string() +
        "number(10).number(12).number(1). \r\n" +
        "goals(test(100)).";
        CHECK(compiler->Compile(example + testState));
        result = planner->FindAllPlans(factory.get(), compiler->compilerOwnedRuleSet(), compiler->goals());
        finalPlan = HtnPlanner::ToStringSolutions(result);
        CHECK_EQUAL(finalPlan, "[ { (debugWatch(10)) } ]");
    }

    TEST(PlannerArithmeticTermsTest)
    {
        shared_ptr<HtnTermFactory> factory = shared_ptr<HtnTermFactory>(new HtnTermFactory());
        shared_ptr<HtnRuleSet> state = shared_ptr<HtnRuleSet>(new HtnRuleSet());
        shared_ptr<HtnPlanner> planner = shared_ptr<HtnPlanner>(new HtnPlanner());
        shared_ptr<HtnCompiler> compiler = shared_ptr<HtnCompiler>(new HtnCompiler(factory.get(), state.get(), planner.get()));
        shared_ptr<HtnPlanner::SolutionsType> result;
        string finalFacts;
        string finalPlan;
        string testState;
        string sharedState;
        string goals;
        shared_ptr<vector<UnifierType>> unifier;

        // State true for all tests
        sharedState = string() +
        "";

        // Terms that are arithmetic are always automatically evaluated before attempting to match with operators and rules
        compiler->ClearWithNewRuleSet();
        testState = string() +
        "trace(?Value, ?Value2) :- del(), add(?Value, ?Value2). \r\n" +
        "method(?Value) :- if(), do(trace(?Value, Method)). \r\n" +
        "";
        goals = string() +
        "goals(method(-(1,2))).\r\n" +
        "";
        CHECK(compiler->Compile(sharedState + testState + goals));
        result = planner->FindAllPlans(factory.get(), compiler->compilerOwnedRuleSet(), compiler->goals());
        finalPlan = HtnPlanner::ToStringSolutions(result);
        CHECK_EQUAL(finalPlan, "[ { (trace(-1,Method)) } ]");
        finalFacts = HtnPlanner::ToStringFacts(result);
        CHECK_EQUAL(finalFacts,  "[ { -1 => ,Method =>  } ]");
    }
}
