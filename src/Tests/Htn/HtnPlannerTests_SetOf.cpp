//
//  HtnPlannerTests_SetOf.cpp
//  TestLib
//
//  Created by Eric Zinda on 1/8/19.
//  Copyright © 2019 Eric Zinda. All rights reserved.
//
//  Tests for anyOf/allOf semantics.
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
    TEST(PlannerSetOfTest)
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

        // A AllSetOf method that modifies state which is in the condition
        // Since the AllSetOf condition alternatives are run at the beginning, all alternatives are still run
        compiler->ClearWithNewRuleSet();
        testState = string() +
        "IsTrue(Test1). Alternative(Alternative1). Alternative(Alternative2).\r\n" +
        "trace(?Value, ?Value2, ?Value3) :- del(), add(item(?Value, ?Value2, ?Value3)). \r\n" +
        "deleteTrueIfExists(?Value) :- if(IsTrue(?Value)), do(deleteTrue(?Value)). \r\n" +
        "deleteTrue(?Value) :- del(IsTrue(?Value)), add(). \r\n" +
        "method(?Value) :- allOf, if(IsTrue(?Value), Alternative(?Alt)), do(try(deleteTrueIfExists(?Value)), trace(?Value, Method1, ?Alt)). \r\n" +
        "";
        goals = string() +
        "goals(method(Test1)).\r\n" +
        "";
        CHECK(compiler->Compile(sharedState + testState + goals));
        result = planner->FindAllPlans(factory.get(), compiler->compilerOwnedRuleSet(), compiler->goals());
        finalPlan = HtnPlanner::ToStringSolutions(result);
        CHECK_EQUAL(finalPlan, "[ { (deleteTrue(Test1), trace(Test1,Method1,Alternative1), trace(Test1,Method1,Alternative2)) } ]");
        finalFacts = HtnPlanner::ToStringFacts(result);
        CHECK_EQUAL(finalFacts,  "[ { Alternative(Alternative1) => ,Alternative(Alternative2) => ,item(Test1,Method1,Alternative1) => ,item(Test1,Method1,Alternative2) =>  } ]");

        // A single AllSetOf method with no condition (which means it will only get run once) where all subtasks succeed
        compiler->ClearWithNewRuleSet();
        testState = string() +
        "IsTrue(Test1). Alternative(Alternative1). Alternative(Alternative2).\r\n" +
        "trace(?Value, ?Value2, ?Value3) :- del(), add(item(?Value, ?Value2, ?Value3)). \r\n" +
        "method(?Value) :- allOf, if(), do(trace(?Value, Method1, None)). \r\n" +
        "";
        goals = string() +
        "goals(method(Test1)).\r\n" +
        "";
        CHECK(compiler->Compile(sharedState + testState + goals));
        result = planner->FindAllPlans(factory.get(), compiler->compilerOwnedRuleSet(), compiler->goals());
        finalPlan = HtnPlanner::ToStringSolutions(result);
        CHECK_EQUAL(finalPlan, "[ { (trace(Test1,Method1,None)) } ]");
        finalFacts = HtnPlanner::ToStringFacts(result);
        CHECK_EQUAL(finalFacts,  "[ { IsTrue(Test1) => ,Alternative(Alternative1) => ,Alternative(Alternative2) => ,item(Test1,Method1,None) =>  } ]");

        // A single AllSetOf method where all subtasks succeed
        compiler->ClearWithNewRuleSet();
        testState = string() +
        "IsTrue(Test1). Alternative(Alternative1). Alternative(Alternative2).\r\n" +
        "trace(?Value, ?Value2, ?Value3) :- del(), add(item(?Value, ?Value2, ?Value3)). \r\n" +
        "method(?Value) :- allOf, if(IsTrue(?Value), Alternative(?Alt)), do(trace(?Value, Method1, ?Alt)). \r\n" +
        "";
        goals = string() +
        "goals(method(Test1)).\r\n" +
        "";
        CHECK(compiler->Compile(sharedState + testState + goals));
        result = planner->FindAllPlans(factory.get(), compiler->compilerOwnedRuleSet(), compiler->goals());
        finalPlan = HtnPlanner::ToStringSolutions(result);
        CHECK_EQUAL(finalPlan, "[ { (trace(Test1,Method1,Alternative1), trace(Test1,Method1,Alternative2)) } ]");
        finalFacts = HtnPlanner::ToStringFacts(result);
        CHECK_EQUAL(finalFacts,  "[ { IsTrue(Test1) => ,Alternative(Alternative1) => ,Alternative(Alternative2) => ,item(Test1,Method1,Alternative1) => ,item(Test1,Method1,Alternative2) =>  } ]");

        // A single AllSetOf method that fails along with another method of the same name that is *not* setof that succeeds
        // The second method should get run
        compiler->ClearWithNewRuleSet();
        testState = string() +
        "IsTrue(Test1). Alternative(Alternative1). Alternative(Alternative2).\r\n" +
        "trace(?Value, ?Value2, ?Value3) :- del(), add(item(?Value, ?Value2, ?Value3)). \r\n" +
        "method(?Value) :- allOf, if(IsTrue(Test2), Alternative(?Alt)), do(trace(?Value, MethodAllOf, ?Alt)). \r\n" +
        "method(?Value) :- if(IsTrue(?Value), Alternative(?Alt)), do(trace(?Value, MethodNormal, ?Alt)). \r\n" +
        "";
        goals = string() +
        "goals(method(Test1)).\r\n" +
        "";
        CHECK(compiler->Compile(sharedState + testState + goals));
        result = planner->FindAllPlans(factory.get(), compiler->compilerOwnedRuleSet(), compiler->goals());
        finalPlan = HtnPlanner::ToStringSolutions(result);
        CHECK_EQUAL(finalPlan, "[ { (trace(Test1,MethodNormal,Alternative1)) } { (trace(Test1,MethodNormal,Alternative2)) } ]");
        finalFacts = HtnPlanner::ToStringFacts(result);
        CHECK_EQUAL(finalFacts,  "[ { IsTrue(Test1) => ,Alternative(Alternative1) => ,Alternative(Alternative2) => ,item(Test1,MethodNormal,Alternative1) =>  } { IsTrue(Test1) => ,Alternative(Alternative1) => ,Alternative(Alternative2) => ,item(Test1,MethodNormal,Alternative2) =>  } ]");

        // A single AllSetOf method where all subtasks succeed preceeded and followed by an operator
        compiler->ClearWithNewRuleSet();
        testState = string() +
        "IsTrue(Test1). Alternative(Alternative1). Alternative(Alternative2).\r\n" +
        "trace(?Value, ?Value2, ?Value3) :- del(), add(item(?Value, ?Value2, ?Value3)). \r\n" +
        "method(?Value) :- allOf, if(IsTrue(?Value), Alternative(?Alt)), do(trace(?Value, Method1, ?Alt)). \r\n" +
        "";
        goals = string() +
        "goals(trace(Finish, Finish1, Finish2), method(Test1), trace(Finish3, Finish4, Finish5)).\r\n" +
        "";
        CHECK(compiler->Compile(sharedState + testState + goals));
        result = planner->FindAllPlans(factory.get(), compiler->compilerOwnedRuleSet(), compiler->goals());
        finalPlan = HtnPlanner::ToStringSolutions(result);
        CHECK_EQUAL(finalPlan, "[ { (trace(Finish,Finish1,Finish2), trace(Test1,Method1,Alternative1), trace(Test1,Method1,Alternative2), trace(Finish3,Finish4,Finish5)) } ]");
        finalFacts = HtnPlanner::ToStringFacts(result);
        CHECK_EQUAL(finalFacts,  "[ { IsTrue(Test1) => ,Alternative(Alternative1) => ,Alternative(Alternative2) => ,item(Finish,Finish1,Finish2) => ,item(Test1,Method1,Alternative1) => ,item(Test1,Method1,Alternative2) => ,item(Finish3,Finish4,Finish5) =>  } ]");

        // Two AllSetOf methods where all subtasks succeed
        compiler->ClearWithNewRuleSet();
        testState = string() +
        "IsTrue(Test1). IsTrue(Test2). Alternative(Alternative1). Alternative(Alternative2).\r\n" +
        "trace(?Value, ?Value2, ?Value3) :- del(), add(item(?Value, ?Value2, ?Value3)). \r\n" +
        "method(?Value) :- allOf, if(IsTrue(?Value), Alternative(?Alt)), do(trace(?Value, Method1, ?Alt)). \r\n" +
        "";
        goals = string() +
        "goals(method(Test1), method(Test2)).\r\n" +
        "";
        CHECK(compiler->Compile(sharedState + testState + goals));
        result = planner->FindAllPlans(factory.get(), compiler->compilerOwnedRuleSet(), compiler->goals());
        finalPlan = HtnPlanner::ToStringSolutions(result);
        CHECK_EQUAL(finalPlan, "[ { (trace(Test1,Method1,Alternative1), trace(Test1,Method1,Alternative2), trace(Test2,Method1,Alternative1), trace(Test2,Method1,Alternative2)) } ]");
        finalFacts = HtnPlanner::ToStringFacts(result);
        CHECK_EQUAL(finalFacts,  "[ { IsTrue(Test1) => ,IsTrue(Test2) => ,Alternative(Alternative1) => ,Alternative(Alternative2) => ,item(Test1,Method1,Alternative1) => ,item(Test1,Method1,Alternative2) => ,item(Test2,Method1,Alternative1) => ,item(Test2,Method1,Alternative2) =>  } ]");

        // One AllSetOf methods Followed by a normal method with two solutions
        compiler->ClearWithNewRuleSet();
        testState = string() +
        "IsTrue(Test1). IsTrue(Test2). Alternative(Alternative1). Alternative(Alternative2).\r\n" +
        "trace(?Value, ?Value2, ?Value3) :- del(), add(item(?Value, ?Value2, ?Value3)). \r\n" +
        "method(?Value) :- allOf, if(IsTrue(?Value), Alternative(?Alt)), do(trace(AllSet, ?Value, ?Alt)). \r\n" +
        "method2(?Value) :- if(IsTrue(?Value), Alternative(?Alt)), do(trace(Normal, ?Value, ?Alt)). \r\n" +
        "";
        goals = string() +
        "goals(method(Test1), method2(Test2)).\r\n" +
        "";
        CHECK(compiler->Compile(sharedState + testState + goals));
        result = planner->FindAllPlans(factory.get(), compiler->compilerOwnedRuleSet(), compiler->goals());
        finalPlan = HtnPlanner::ToStringSolutions(result);
        CHECK_EQUAL(finalPlan, "[ { (trace(AllSet,Test1,Alternative1), trace(AllSet,Test1,Alternative2), trace(Normal,Test2,Alternative1)) } { (trace(AllSet,Test1,Alternative1), trace(AllSet,Test1,Alternative2), trace(Normal,Test2,Alternative2)) } ]");
        finalFacts = HtnPlanner::ToStringFacts(result);
        CHECK_EQUAL(finalFacts,  "[ { IsTrue(Test1) => ,IsTrue(Test2) => ,Alternative(Alternative1) => ,Alternative(Alternative2) => ,item(AllSet,Test1,Alternative1) => ,item(AllSet,Test1,Alternative2) => ,item(Normal,Test2,Alternative1) =>  } { IsTrue(Test1) => ,IsTrue(Test2) => ,Alternative(Alternative1) => ,Alternative(Alternative2) => ,item(AllSet,Test1,Alternative1) => ,item(AllSet,Test1,Alternative2) => ,item(Normal,Test2,Alternative2) =>  } ]");

        // A single AllSetOf method where one subtasks fail
        compiler->ClearWithNewRuleSet();
        testState = string() +
        "IsTrue(Test1). Alternative(Alternative1). Alternative(Alternative2).Combo(Test1,Alternative1).\r\n" +
        "trace(?Value, ?Value2, ?Value3) :- del(), add(item(?Value, ?Value2, ?Value3)). \r\n" +
        "method(?Value) :- allOf, if(IsTrue(?Value), Alternative(?Alt)), do(subtask(?Value, ?Alt)). \r\n" +
        "subtask(?Value1, ?Value2) :- if(Combo(?Value1, ?Value2)), do(trace(?Value1, ?Value2)).\r\n" +
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

        // Two methods of the same name, one is AllSetOf which partially succeeds before it fails and the other method succeeds
        // Testing that an AllSetOf is clearing out previously successful solutions if it eventually fails
        compiler->ClearWithNewRuleSet();
        testState = string() +
        "IsTrue(Test1). IsTrue(Test2). Alternative(Alternative1). Alternative(Alternative2).\r\n" +
        "IsTrue(Test1, Alternative1). \r\n" +
        "trace(?Value, ?Value2, ?Value3) :- del(), add(item(?Value, ?Value2, ?Value3)). \r\n" +
        // condition unifies two ways, one of which fails when method2 is called
        "method(?Value) :- allOf, if(Alternative(?Alt)), do(method2(?Value, ?Alt)). \r\n" +
        "method(?Value) :- if(IsTrue(?Value), Alternative(?Alt)), do(trace(Normal, ?Value, ?Alt)). \r\n" +
        "method2(?Value, ?Alt) :- if(IsTrue(?Value, ?Alt)), do(trace(Method2, ?Value, ?Alt)).\r\n" +
        "";
        goals = string() +
        "goals(method(Test1)).\r\n" +
        "";
        CHECK(compiler->Compile(sharedState + testState + goals));
        result = planner->FindAllPlans(factory.get(), compiler->compilerOwnedRuleSet(), compiler->goals());
        finalPlan = HtnPlanner::ToStringSolutions(result);
        CHECK_EQUAL(finalPlan, "[ { (trace(Normal,Test1,Alternative1)) } { (trace(Normal,Test1,Alternative2)) } ]");
        finalFacts = HtnPlanner::ToStringFacts(result);
        CHECK_EQUAL(finalFacts,  "[ { IsTrue(Test1) => ,IsTrue(Test2) => ,Alternative(Alternative1) => ,Alternative(Alternative2) => ,IsTrue(Test1,Alternative1) => ,item(Normal,Test1,Alternative1) =>  } { IsTrue(Test1) => ,IsTrue(Test2) => ,Alternative(Alternative1) => ,Alternative(Alternative2) => ,IsTrue(Test1,Alternative1) => ,item(Normal,Test1,Alternative2) =>  } ]");

        // One AllSetOf methods Followed by a normal method with two solutions where one fails
        compiler->ClearWithNewRuleSet();
        testState = string() +
        "IsTrue(Test1). IsTrue(Test2). Alternative(Alternative1). Alternative(Alternative2).\r\n" +
        "IsTrue(Test2, Alternative2). \r\n" +
        "trace(?Value, ?Value2, ?Value3) :- del(), add(item(?Value, ?Value2, ?Value3)). \r\n" +
        "method(?Value) :- allOf, if(IsTrue(?Value), Alternative(?Alt)), do(trace(AllSet, ?Value, ?Alt)). \r\n" +
        "method2(?Value) :- if(IsTrue(?Value), Alternative(?Alt)), do(method3(?Value, ?Alt)). \r\n" +
        "method3(?Value, ?Alt) :- if(IsTrue(?Value, ?Alt)), do(trace(Normal, ?Value, ?Alt)). \r\n" +
        "";
        goals = string() +
        "goals(method(Test1), method2(Test2)).\r\n" +
        "";
        CHECK(compiler->Compile(sharedState + testState + goals));
        result = planner->FindAllPlans(factory.get(), compiler->compilerOwnedRuleSet(), compiler->goals());
        finalPlan = HtnPlanner::ToStringSolutions(result);
        CHECK_EQUAL(finalPlan, "[ { (trace(AllSet,Test1,Alternative1), trace(AllSet,Test1,Alternative2), trace(Normal,Test2,Alternative2)) } ]");
        finalFacts = HtnPlanner::ToStringFacts(result);
        CHECK_EQUAL(finalFacts,  "[ { IsTrue(Test1) => ,IsTrue(Test2) => ,Alternative(Alternative1) => ,Alternative(Alternative2) => ,IsTrue(Test2,Alternative2) => ,item(AllSet,Test1,Alternative1) => ,item(AllSet,Test1,Alternative2) => ,item(Normal,Test2,Alternative2) =>  } ]");

        // A single AnySetOf method where all subtasks succeed
        compiler->ClearWithNewRuleSet();
        testState = string() +
        "IsTrue(Test1). Alternative(Alternative1). Alternative(Alternative2).\r\n" +
        "trace(?Value, ?Value2, ?Value3) :- del(), add(item(?Value, ?Value2, ?Value3)). \r\n" +
        "method(?Value) :- anyOf, if(IsTrue(?Value), Alternative(?Alt)), do(trace(?Value, Method1, ?Alt)). \r\n" +
        "";
        goals = string() +
        "goals(method(Test1)).\r\n" +
        "";
        CHECK(compiler->Compile(sharedState + testState + goals));
        result = planner->FindAllPlans(factory.get(), compiler->compilerOwnedRuleSet(), compiler->goals());
        finalPlan = HtnPlanner::ToStringSolutions(result);
        CHECK_EQUAL(finalPlan, "[ { (trace(Test1,Method1,Alternative1), trace(Test1,Method1,Alternative2)) } ]");
        finalFacts = HtnPlanner::ToStringFacts(result);
        CHECK_EQUAL(finalFacts,  "[ { IsTrue(Test1) => ,Alternative(Alternative1) => ,Alternative(Alternative2) => ,item(Test1,Method1,Alternative1) => ,item(Test1,Method1,Alternative2) =>  } ]");

        // A single AnySetOf method where all subtasks succeed preceeded and followed by an operator
        compiler->ClearWithNewRuleSet();
        testState = string() +
        "IsTrue(Test1). Alternative(Alternative1). Alternative(Alternative2).\r\n" +
        "trace(?Value, ?Value2, ?Value3) :- del(), add(item(?Value, ?Value2, ?Value3)). \r\n" +
        "method(?Value) :- anyOf, if(IsTrue(?Value), Alternative(?Alt)), do(trace(?Value, Method1, ?Alt)). \r\n" +
        "";
        goals = string() +
        "goals(trace(Finish, Finish1, Finish2), method(Test1), trace(Finish3, Finish4, Finish5)).\r\n" +
        "";
        CHECK(compiler->Compile(sharedState + testState + goals));
        result = planner->FindAllPlans(factory.get(), compiler->compilerOwnedRuleSet(), compiler->goals());
        finalPlan = HtnPlanner::ToStringSolutions(result);
        CHECK_EQUAL(finalPlan, "[ { (trace(Finish,Finish1,Finish2), trace(Test1,Method1,Alternative1), trace(Test1,Method1,Alternative2), trace(Finish3,Finish4,Finish5)) } ]");
        finalFacts = HtnPlanner::ToStringFacts(result);
        CHECK_EQUAL(finalFacts,  "[ { IsTrue(Test1) => ,Alternative(Alternative1) => ,Alternative(Alternative2) => ,item(Finish,Finish1,Finish2) => ,item(Test1,Method1,Alternative1) => ,item(Test1,Method1,Alternative2) => ,item(Finish3,Finish4,Finish5) =>  } ]");

        // Two AnySetOf methods where all subtasks succeed
        compiler->ClearWithNewRuleSet();
        testState = string() +
        "IsTrue(Test1). IsTrue(Test2). Alternative(Alternative1). Alternative(Alternative2).\r\n" +
        "trace(?Value, ?Value2, ?Value3) :- del(), add(item(?Value, ?Value2, ?Value3)). \r\n" +
        "method(?Value) :- anyOf, if(IsTrue(?Value), Alternative(?Alt)), do(trace(?Value, Method1, ?Alt)). \r\n" +
        "";
        goals = string() +
        "goals(method(Test1), method(Test2)).\r\n" +
        "";
        CHECK(compiler->Compile(sharedState + testState + goals));
        result = planner->FindAllPlans(factory.get(), compiler->compilerOwnedRuleSet(), compiler->goals());
        finalPlan = HtnPlanner::ToStringSolutions(result);
        CHECK_EQUAL(finalPlan, "[ { (trace(Test1,Method1,Alternative1), trace(Test1,Method1,Alternative2), trace(Test2,Method1,Alternative1), trace(Test2,Method1,Alternative2)) } ]");
        finalFacts = HtnPlanner::ToStringFacts(result);
        CHECK_EQUAL(finalFacts,  "[ { IsTrue(Test1) => ,IsTrue(Test2) => ,Alternative(Alternative1) => ,Alternative(Alternative2) => ,item(Test1,Method1,Alternative1) => ,item(Test1,Method1,Alternative2) => ,item(Test2,Method1,Alternative1) => ,item(Test2,Method1,Alternative2) =>  } ]");

        // One AnySetOf methods Followed by a normal method with two solutions
        compiler->ClearWithNewRuleSet();
        testState = string() +
        "IsTrue(Test1). IsTrue(Test2). Alternative(Alternative1). Alternative(Alternative2).\r\n" +
        "trace(?Value, ?Value2, ?Value3) :- del(), add(item(?Value, ?Value2, ?Value3)). \r\n" +
        "method(?Value) :- anyOf, if(IsTrue(?Value), Alternative(?Alt)), do(trace(AllSet, ?Value, ?Alt)). \r\n" +
        "method2(?Value) :- if(IsTrue(?Value), Alternative(?Alt)), do(trace(Normal, ?Value, ?Alt)). \r\n" +
        "";
        goals = string() +
        "goals(method(Test1), method2(Test2)).\r\n" +
        "";
        CHECK(compiler->Compile(sharedState + testState + goals));
        result = planner->FindAllPlans(factory.get(), compiler->compilerOwnedRuleSet(), compiler->goals());
        finalPlan = HtnPlanner::ToStringSolutions(result);
        CHECK_EQUAL(finalPlan, "[ { (trace(AllSet,Test1,Alternative1), trace(AllSet,Test1,Alternative2), trace(Normal,Test2,Alternative1)) } { (trace(AllSet,Test1,Alternative1), trace(AllSet,Test1,Alternative2), trace(Normal,Test2,Alternative2)) } ]");
        finalFacts = HtnPlanner::ToStringFacts(result);
        CHECK_EQUAL(finalFacts,  "[ { IsTrue(Test1) => ,IsTrue(Test2) => ,Alternative(Alternative1) => ,Alternative(Alternative2) => ,item(AllSet,Test1,Alternative1) => ,item(AllSet,Test1,Alternative2) => ,item(Normal,Test2,Alternative1) =>  } { IsTrue(Test1) => ,IsTrue(Test2) => ,Alternative(Alternative1) => ,Alternative(Alternative2) => ,item(AllSet,Test1,Alternative1) => ,item(AllSet,Test1,Alternative2) => ,item(Normal,Test2,Alternative2) =>  } ]");

        // A single AnySetOf method where one subtasks fail
        compiler->ClearWithNewRuleSet();
        testState = string() +
        "IsTrue(Test1). Alternative(Alternative1). Alternative(Alternative2).Combo(Test1,Alternative1).\r\n" +
        "trace(?Value, ?Value2) :- del(), add(item(?Value, ?Value2)). \r\n" +
        "method(?Value) :- anyOf, if(IsTrue(?Value), Alternative(?Alt)), do(subtask(?Value, ?Alt)). \r\n" +
        "subtask(?Value1, ?Value2) :- if(Combo(?Value1, ?Value2)), do(trace(?Value1, ?Value2)).\r\n" +
        "";
        goals = string() +
        "goals(method(Test1)).\r\n" +
        "";
        CHECK(compiler->Compile(sharedState + testState + goals));
        result = planner->FindAllPlans(factory.get(), compiler->compilerOwnedRuleSet(), compiler->goals());
        finalPlan = HtnPlanner::ToStringSolutions(result);
        CHECK_EQUAL(finalPlan, "[ { (trace(Test1,Alternative1)) } ]");
        finalFacts = HtnPlanner::ToStringFacts(result);
        CHECK_EQUAL(finalFacts,  "[ { IsTrue(Test1) => ,Alternative(Alternative1) => ,Alternative(Alternative2) => ,Combo(Test1,Alternative1) => ,item(Test1,Alternative1) =>  } ]");

        // One AnySetOf methods Followed by a normal method with two solutions where one fails
        compiler->ClearWithNewRuleSet();
        testState = string() +
        "IsTrue(Test1). IsTrue(Test2). Alternative(Alternative1). Alternative(Alternative2).\r\n" +
        "IsTrue(Test2, Alternative2). \r\n" +
        "trace(?Value, ?Value2, ?Value3) :- del(), add(item(?Value, ?Value2, ?Value3)). \r\n" +
        "method(?Value) :- anyOf, if(IsTrue(?Value), Alternative(?Alt)), do(trace(AllSet, ?Value, ?Alt)). \r\n" +
        "method2(?Value) :- if(IsTrue(?Value), Alternative(?Alt)), do(method3(?Value, ?Alt)). \r\n" +
        "method3(?Value, ?Alt) :- if(IsTrue(?Value, ?Alt)), do(trace(Normal, ?Value, ?Alt)). \r\n" +
        "";
        goals = string() +
        "goals(method(Test1), method2(Test2)).\r\n" +
        "";
        CHECK(compiler->Compile(sharedState + testState + goals));
        result = planner->FindAllPlans(factory.get(), compiler->compilerOwnedRuleSet(), compiler->goals());
        finalPlan = HtnPlanner::ToStringSolutions(result);
        CHECK_EQUAL(finalPlan, "[ { (trace(AllSet,Test1,Alternative1), trace(AllSet,Test1,Alternative2), trace(Normal,Test2,Alternative2)) } ]");
        finalFacts = HtnPlanner::ToStringFacts(result);
        CHECK_EQUAL(finalFacts,  "[ { IsTrue(Test1) => ,IsTrue(Test2) => ,Alternative(Alternative1) => ,Alternative(Alternative2) => ,IsTrue(Test2,Alternative2) => ,item(AllSet,Test1,Alternative1) => ,item(AllSet,Test1,Alternative2) => ,item(Normal,Test2,Alternative2) =>  } ]");
    }

    TEST(PlannerSingleSolutionTest)
    {
        shared_ptr<HtnTermFactory> factory = shared_ptr<HtnTermFactory>(new HtnTermFactory());
        shared_ptr<HtnRuleSet> state = shared_ptr<HtnRuleSet>(new HtnRuleSet());
        shared_ptr<HtnPlanner> planner = shared_ptr<HtnPlanner>(new HtnPlanner());
        shared_ptr<HtnCompiler> compiler = shared_ptr<HtnCompiler>(new HtnCompiler(factory.get(), state.get(), planner.get()));
        shared_ptr<HtnPlanner::SolutionType> result;
        string example;
        string finalFacts;
        string finalFacts2;
        string finalPlan;
        string finalPlan2;
        string testState;
        string sharedState;
        string goals;
        shared_ptr<vector<UnifierType>> unifier;

        // State true for all tests
        sharedState = string() +
        "";

        // Asking for Single solution from planner should still return all AnyOf and AllOf answers, but only first alternative
        // Single Solution, One AnySetOf methods Followed by a normal method with two solutions
        compiler->ClearWithNewRuleSet();
        testState = string() +
        "IsTrue(Test1). IsTrue(Test2). Alternative(Alternative1). Alternative(Alternative2).\r\n" +
        "trace(?Value, ?Value2, ?Value3) :- del(), add(item(?Value, ?Value2, ?Value3)). \r\n" +
        "method(?Value) :- anyOf, if(IsTrue(?Value), Alternative(?Alt)), do(trace(AllSet, ?Value, ?Alt)). \r\n" +
        "method2(?Value) :- if(IsTrue(?Value), Alternative(?Alt)), do(trace(Normal, ?Value, ?Alt)). \r\n" +
        "";
        goals = string() +
        "goals(method(Test1), method2(Test2)).\r\n" +
        "";
        CHECK(compiler->Compile(sharedState + testState + goals));
        result = planner->FindPlan(factory.get(), compiler->compilerOwnedRuleSet(), compiler->goals());
        finalPlan = HtnPlanner::ToStringSolution(result);
        CHECK_EQUAL(finalPlan, "(trace(AllSet,Test1,Alternative1), trace(AllSet,Test1,Alternative2), trace(Normal,Test2,Alternative1))");
        finalFacts = HtnPlanner::ToStringFacts(result);
        CHECK_EQUAL(finalFacts,  "IsTrue(Test1) => ,IsTrue(Test2) => ,Alternative(Alternative1) => ,Alternative(Alternative2) => ,item(AllSet,Test1,Alternative1) => ,item(AllSet,Test1,Alternative2) => ,item(Normal,Test2,Alternative1) => ");

        // Asking for Single solution from planner should still return all AnyOf and AllOf answers, but only first alternative
        // One AllSetOf methods Followed by a normal method with two solutions
        compiler->ClearWithNewRuleSet();
        testState = string() +
        "IsTrue(Test1). IsTrue(Test2). Alternative(Alternative1). Alternative(Alternative2).\r\n" +
        "trace(?Value, ?Value2, ?Value3) :- del(), add(item(?Value, ?Value2, ?Value3)). \r\n" +
        "method(?Value) :- allOf, if(IsTrue(?Value), Alternative(?Alt)), do(trace(AllSet, ?Value, ?Alt)). \r\n" +
        "method2(?Value) :- if(IsTrue(?Value), Alternative(?Alt)), do(trace(Normal, ?Value, ?Alt)). \r\n" +
        "";
        goals = string() +
        "goals(method(Test1), method2(Test2)).\r\n" +
        "";
        CHECK(compiler->Compile(sharedState + testState + goals));
        result = planner->FindPlan(factory.get(), compiler->compilerOwnedRuleSet(), compiler->goals());
        finalPlan = HtnPlanner::ToStringSolution(result);
        CHECK_EQUAL(finalPlan, "(trace(AllSet,Test1,Alternative1), trace(AllSet,Test1,Alternative2), trace(Normal,Test2,Alternative1))");
        finalFacts = HtnPlanner::ToStringFacts(result);
        CHECK_EQUAL(finalFacts,  "IsTrue(Test1) => ,IsTrue(Test2) => ,Alternative(Alternative1) => ,Alternative(Alternative2) => ,item(AllSet,Test1,Alternative1) => ,item(AllSet,Test1,Alternative2) => ,item(Normal,Test2,Alternative1) => ");
    }
}
