//
//  HtnPlannerTests_ControlFlow.cpp
//  TestLib
//
//  Created by Eric Zinda on 1/8/19.
//  Copyright © 2019 Eric Zinda. All rights reserved.
//
//  Control flow constructs: try, else, first, sortBy, not, and state tests.
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
    TEST(PlannerTryTest)
    {
        shared_ptr<HtnTermFactory> factory = shared_ptr<HtnTermFactory>(new HtnTermFactory());
        shared_ptr<HtnRuleSet> state = shared_ptr<HtnRuleSet>(new HtnRuleSet());
        shared_ptr<HtnPlanner> planner = shared_ptr<HtnPlanner>(new HtnPlanner());
        shared_ptr<HtnCompiler> compiler = shared_ptr<HtnCompiler>(new HtnCompiler(factory.get(), state.get(), planner.get()));
        shared_ptr<HtnPlanner::SolutionsType> result;
        string example;
        string finalFacts;
        string finalPlan;
        string testState;
        string sharedState;
        string goals;
        shared_ptr<vector<UnifierType>> unifier;

        // State true for all tests
        sharedState = string() +
        "";

        // ***** Empty Try should work (for completeness)
        compiler->ClearWithNewRuleSet();
        testState = string() +
        "number(10).number(12).number(1). \r\n" +
        "test() :- if(), do(try(successTask()), try(failTask()), try(failTask()), try(successTask(?Y)) ).\r\n" +
        "failTask() :- if(<(2, 1)), do(debugWatch(fail)).\r\n" +
        "successTask() :- if(<(1, 2)), do(debugWatch(success)).\r\n" +
        "successTask(?X) :- if(number(?X)), do(debugWatch(?X)).\r\n" +
        "debugWatch(?x) :- del(), add(item(?x)).\r\n" +
        "";
        goals = string() +
        "goals(try(), successTask()).\r\n" +
        "";;
        CHECK(compiler->Compile(sharedState + testState + goals));
        result = planner->FindAllPlans(factory.get(), compiler->compilerOwnedRuleSet(), compiler->goals());
        finalPlan = HtnPlanner::ToStringSolutions(result);
        CHECK_EQUAL(finalPlan, "[ { (debugWatch(success)) } ]");
        finalFacts = HtnPlanner::ToStringFacts(result);
        CHECK_EQUAL(finalFacts,  "[ { number(10) => ,number(12) => ,number(1) => ,item(success) =>  } ]");

        // try() condition terms should return all successful solutions
        // method2(Test2) should return two alternatives
        compiler->ClearWithNewRuleSet();
        testState = string() +
        "IsTrue(Test1). IsTrue(Test2). Alternative(Alternative1). Alternative(Alternative2).\r\n" +
        "trace(?Value, ?Value2, ?Value3) :- del(), add(item(?Value, ?Value2, ?Value3)). \r\n" +
        "method(?Value) :- allOf, if(IsTrue(?Value), Alternative(?Alt)), do(trace(AllSet, ?Value, ?Alt)). \r\n" +
        "method2(?Value) :- if(IsTrue(?Value), Alternative(?Alt)), do(trace(Normal, ?Value, ?Alt)). \r\n" +
        "";
        goals = string() +
        "goals(try(method2(Test2))).\r\n" +
        "";
        CHECK(compiler->Compile(sharedState + testState + goals));
        result = planner->FindAllPlans(factory.get(), compiler->compilerOwnedRuleSet(), compiler->goals());
        finalPlan = HtnPlanner::ToStringSolutions(result);
        CHECK_EQUAL(finalPlan, "[ { (trace(Normal,Test2,Alternative1)) } { (trace(Normal,Test2,Alternative2)) } ]");
        finalFacts = HtnPlanner::ToStringFacts(result);
        CHECK_EQUAL(finalFacts,  "[ { IsTrue(Test1) => ,IsTrue(Test2) => ,Alternative(Alternative1) => ,Alternative(Alternative2) => ,item(Normal,Test2,Alternative1) =>  } { IsTrue(Test1) => ,IsTrue(Test2) => ,Alternative(Alternative1) => ,Alternative(Alternative2) => ,item(Normal,Test2,Alternative2) =>  } ]");

        // try() condition followed by a failed normal condition should fail
        compiler->ClearWithNewRuleSet();
        testState = string() +
        "IsTrue(Test1). IsTrue(Test2). Alternative(Alternative1). Alternative(Alternative2).\r\n" +
        "trace(?Value, ?Value2, ?Value3) :- del(), add(item(?Value, ?Value2, ?Value3)). \r\n" +
        "method(?Value) :- allOf, if(IsTrue(?Value), Alternative(?Alt)), do(trace(AllSet, ?Value, ?Alt)). \r\n" +
        "method2(?Value) :- if(IsTrue(?Value), Alternative(?Alt)), do(trace(Normal, ?Value, ?Alt)). \r\n" +
        "";
        goals = string() +
        "goals(try(method(Test3)), method(Test3)).\r\n" +
        "";
        CHECK(compiler->Compile(sharedState + testState + goals));
        result = planner->FindAllPlans(factory.get(), compiler->compilerOwnedRuleSet(), compiler->goals());
        finalPlan = HtnPlanner::ToStringSolutions(result);
        CHECK_EQUAL(finalPlan, "null");
        finalFacts = HtnPlanner::ToStringFacts(result);
        CHECK_EQUAL(finalFacts,  "null");

        // try() condition terms should ignore failure and be transparent to success
        // method() is allOf and always fails
        // method2(Test2) should return two alternatives
        compiler->ClearWithNewRuleSet();
        testState = string() +
        "IsTrue(Test1). IsTrue(Test2). Alternative(Alternative1). Alternative(Alternative2).\r\n" +
        "trace(?Value, ?Value2, ?Value3) :- del(), add(item(?Value, ?Value2, ?Value3)). \r\n" +
        "method(?Value) :- allOf, if(IsTrue(?Value), Alternative(?Alt)), do(trace(AllSet, ?Value, ?Alt)). \r\n" +
        "method2(?Value) :- if(IsTrue(?Value), Alternative(?Alt)), do(trace(Normal, ?Value, ?Alt)). \r\n" +
        "";
        goals = string() +
        "goals(try(method(Test3)), try(method2(Test2))).\r\n" +
        "";
        CHECK(compiler->Compile(sharedState + testState + goals));
        result = planner->FindAllPlans(factory.get(), compiler->compilerOwnedRuleSet(), compiler->goals());
        finalPlan = HtnPlanner::ToStringSolutions(result);
        CHECK_EQUAL(finalPlan, "[ { (trace(Normal,Test2,Alternative1)) } { (trace(Normal,Test2,Alternative2)) } ]");
        finalFacts = HtnPlanner::ToStringFacts(result);
        CHECK_EQUAL(finalFacts,  "[ { IsTrue(Test1) => ,IsTrue(Test2) => ,Alternative(Alternative1) => ,Alternative(Alternative2) => ,item(Normal,Test2,Alternative1) =>  } { IsTrue(Test1) => ,IsTrue(Test2) => ,Alternative(Alternative1) => ,Alternative(Alternative2) => ,item(Normal,Test2,Alternative2) =>  } ]");

        // try() condition terms should ignore failure in the do() clause too
        // One AnySetOf methods Followed by a normal method with one solution which fails
        compiler->ClearWithNewRuleSet();
        testState = string() +
        "IsTrue(Test1). IsTrue(Test2). Alternative(Alternative1). Alternative(Alternative2).\r\n" +
        "IsTrue(Test2, Alternative2). \r\n" +
        "trace(?Value, ?Value2, ?Value3) :- del(), add(item(?Value, ?Value2, ?Value3)). \r\n" +
        "method(?Value) :- anyOf, if(IsTrue(?Value), Alternative(?Alt)), do(trace(AllSet, ?Value, ?Alt)). \r\n" +
        "method2(?Value) :- if(IsTrue(?Value), Alternative(?Alt)), do(trace(Method2, ?Value, ?Alt), try(method3(?Value, ?Alt))). \r\n" +
        "method3(?Value, ?Alt) :- if(IsTrue(?Value, ?Alt)), do(trace(Normal, ?Value, ?Alt)). \r\n" +
        "";
        goals = string() +
        "goals(method(Test1), method2(Test2)).\r\n" +
        "";
        CHECK(compiler->Compile(sharedState + testState + goals));
        result = planner->FindAllPlans(factory.get(), compiler->compilerOwnedRuleSet(), compiler->goals());
        finalPlan = HtnPlanner::ToStringSolutions(result);
        CHECK_EQUAL(finalPlan, "[ { (trace(AllSet,Test1,Alternative1), trace(AllSet,Test1,Alternative2), trace(Method2,Test2,Alternative1)) } { (trace(AllSet,Test1,Alternative1), trace(AllSet,Test1,Alternative2), trace(Method2,Test2,Alternative2), trace(Normal,Test2,Alternative2)) } ]");
        finalFacts = HtnPlanner::ToStringFacts(result);
        CHECK_EQUAL(finalFacts,  "[ { IsTrue(Test1) => ,IsTrue(Test2) => ,Alternative(Alternative1) => ,Alternative(Alternative2) => ,IsTrue(Test2,Alternative2) => ,item(AllSet,Test1,Alternative1) => ,item(AllSet,Test1,Alternative2) => ,item(Method2,Test2,Alternative1) =>  } { IsTrue(Test1) => ,IsTrue(Test2) => ,Alternative(Alternative1) => ,Alternative(Alternative2) => ,IsTrue(Test2,Alternative2) => ,item(AllSet,Test1,Alternative1) => ,item(AllSet,Test1,Alternative2) => ,item(Method2,Test2,Alternative2) => ,item(Normal,Test2,Alternative2) =>  } ]");

        // ***** Try should ignore failures and continue other tasks.  Should properly return multiple solutions
        compiler->ClearWithNewRuleSet();
        testState = string() +
        "number(10).number(12).number(1). \r\n" +
        "test() :- if(), do(try(successTask()), try(failTask()), try(failTask()), try(successTask(?Y)) ).\r\n" +
        "failTask() :- if(<(2, 1)), do(debugWatch(fail)).\r\n" +
        "successTask() :- if(<(1, 2)), do(debugWatch(success)).\r\n" +
        "successTask(?X) :- if(number(?X)), do(debugWatch(?X)).\r\n" +
        "debugWatch(?x) :- del(), add(item(?x)).\r\n" +
        "";
        goals = string() +
        "goals(test()).\r\n" +
        "";;
        CHECK(compiler->Compile(sharedState + testState + goals));
        result = planner->FindAllPlans(factory.get(), compiler->compilerOwnedRuleSet(), compiler->goals());
        finalPlan = HtnPlanner::ToStringSolutions(result);
        CHECK_EQUAL(finalPlan, "[ { (debugWatch(success), debugWatch(10)) } { (debugWatch(success), debugWatch(12)) } { (debugWatch(success), debugWatch(1)) } ]");
        finalFacts = HtnPlanner::ToStringFacts(result);
        CHECK_EQUAL(finalFacts,  "[ { number(10) => ,number(12) => ,number(1) => ,item(success) => ,item(10) =>  } { number(10) => ,number(12) => ,number(1) => ,item(success) => ,item(12) =>  } { number(10) => ,number(12) => ,number(1) => ,item(success) => ,item(1) =>  } ]");
    }

    TEST(PlannerElseTest)
    {
        shared_ptr<HtnTermFactory> factory = shared_ptr<HtnTermFactory>(new HtnTermFactory());
        shared_ptr<HtnRuleSet> state = shared_ptr<HtnRuleSet>(new HtnRuleSet());
        shared_ptr<HtnPlanner> planner = shared_ptr<HtnPlanner>(new HtnPlanner());
        shared_ptr<HtnCompiler> compiler = shared_ptr<HtnCompiler>(new HtnCompiler(factory.get(), state.get(), planner.get()));
        shared_ptr<HtnPlanner::SolutionsType> result;
        string example;
        string finalFacts;
        string finalPlan;
        string testState;
        string sharedState;
        string goals;
        shared_ptr<vector<UnifierType>> unifier;

        // State true for all tests
        sharedState = string() +
        "";

        // ***** If a subtask fails, the planner should backtrack and run the else clause of the task that spawned it
        example = string() +
        "test() :- if(), do(failTask()).\r\n" +
        "test() :- else, if(), do(success()).\r\n" +
        "failTask() :- if( <(2,1) ), do().\r\n" +
        "success() :- del(), add(item(success)).\r\n" +
        "";
        compiler->ClearWithNewRuleSet();
        testState = string() +
        "goals(test()).";
        CHECK(compiler->Compile(example + sharedState + testState + goals));
        result = planner->FindAllPlans(factory.get(), compiler->compilerOwnedRuleSet(), compiler->goals());
        finalPlan = HtnPlanner::ToStringSolutions(result);
        CHECK_EQUAL(finalPlan, "[ { (success) } ]");
        finalFacts = HtnPlanner::ToStringFacts(result);
        CHECK_EQUAL(finalFacts,  "[ { item(success) =>  } ]");

        // ***** If a subtask of an allof task fails, the planner should backtrack and run the else clause of the task that spawned it
        example = string() +
        "test() :- allOf, if(), do(failTask()).\r\n" +
        "test() :- else, if(), do(success()).\r\n" +
        "failTask() :- if( <(2,1) ), do().\r\n" +
        "success() :- del(), add(item(success)).\r\n" +
        "";
        compiler->ClearWithNewRuleSet();
        testState = string() +
        "goals(test()).";
        CHECK(compiler->Compile(example + sharedState + testState + goals));
        result = planner->FindAllPlans(factory.get(), compiler->compilerOwnedRuleSet(), compiler->goals());
        finalPlan = HtnPlanner::ToStringSolutions(result);
        CHECK_EQUAL(finalPlan, "[ { (success) } ]");
        finalFacts = HtnPlanner::ToStringFacts(result);
        CHECK_EQUAL(finalFacts,  "[ { item(success) =>  } ]");

        // ***** If ALL subtasks of an anyof task fails, the planner should backtrack and run the else clause of the task that spawned it
        example = string() +
        "test() :- anyOf, if(), do(failTask()).\r\n" +
        "test() :- else, if(), do(elseSuccess()).\r\n" +
        "failTask() :- if( <(2,1) ), do(success()).\r\n" +
        "success() :- del(), add(item(success)).\r\n" +
        "elseSuccess() :- del(), add(item(elseEuccess)).\r\n" +
        "";
        compiler->ClearWithNewRuleSet();
        testState = string() +
        "goals(test()).";
        CHECK(compiler->Compile(example + sharedState + testState + goals));
        result = planner->FindAllPlans(factory.get(), compiler->compilerOwnedRuleSet(), compiler->goals());
        finalPlan = HtnPlanner::ToStringSolutions(result);
        CHECK_EQUAL(finalPlan, "[ { (elseSuccess) } ]");
        finalFacts = HtnPlanner::ToStringFacts(result);
        CHECK_EQUAL(finalFacts,  "[ { item(elseEuccess) =>  } ]");

        // ***** If an anyOf only has one subtask that succeeds it should only return one solution and not run the else clause
        example = string() +
        "test() :- anyOf, if(unit(?X)), do(success()).\r\n" +
        "test() :- else, if(), do(elseSuccess()).\r\n" +
        "success() :- del(), add(item(success)).\r\n" +
        "elseSuccess() :- del(), add(item(elseEuccess)).\r\n" +
        "";
        compiler->ClearWithNewRuleSet();
        testState = string() +
        "unit(Queen). \r\n" +
        "goals(test()).";
        CHECK(compiler->Compile(example + sharedState + testState + goals));
        result = planner->FindAllPlans(factory.get(), compiler->compilerOwnedRuleSet(), compiler->goals());
        finalPlan = HtnPlanner::ToStringSolutions(result);
        CHECK_EQUAL(finalPlan, "[ { (success) } ]");
        finalFacts = HtnPlanner::ToStringFacts(result);
        CHECK_EQUAL(finalFacts,  "[ { unit(Queen) => ,item(success) =>  } ]");

        // ***** If at least one subtask of an anyof task succeeds, the planner should NOT backtrack and run the else clause of the task that spawned it
        example = string() +
        "test() :- anyOf, if(unit(?X)), do(failTask(?X)).\r\n" +
        "test() :- else, if(), do(elseSuccess()).\r\n" +
        "failTask(?Unit) :- if( shouldWork(?Unit) ), do(success()).\r\n" +
        "success() :- del(), add(item(success)).\r\n" +
        "elseSuccess() :- del(), add(item(elseEuccess)).\r\n" +
        "";
        compiler->ClearWithNewRuleSet();
        testState = string() +
        "unit(Queen). \r\n" +
        "unit(Worker). \r\n" +
        "shouldWork(Queen). \r\n" +
        "goals(test()).";
        CHECK(compiler->Compile(example + sharedState + testState + goals));
        result = planner->FindAllPlans(factory.get(), compiler->compilerOwnedRuleSet(), compiler->goals());
        finalPlan = HtnPlanner::ToStringSolutions(result);
        CHECK_EQUAL(finalPlan, "[ { (success) } ]");
        finalFacts = HtnPlanner::ToStringFacts(result);
        CHECK_EQUAL(finalFacts,  "[ { unit(Queen) => ,unit(Worker) => ,shouldWork(Queen) => ,item(success) =>  } ]");
    }

    TEST(PlannerFirstSortByNot)
    {
        HtnGoalResolver resolver;
        shared_ptr<HtnTermFactory> factory = shared_ptr<HtnTermFactory>(new HtnTermFactory());
        shared_ptr<HtnRuleSet> state = shared_ptr<HtnRuleSet>(new HtnRuleSet());
        shared_ptr<HtnPlanner> planner = shared_ptr<HtnPlanner>(new HtnPlanner());
        shared_ptr<HtnCompiler> compiler = shared_ptr<HtnCompiler>(new HtnCompiler(factory.get(), state.get(), planner.get()));
        shared_ptr<HtnPlanner::SolutionsType> result;
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

        // ***** first: with terms after first()
        example = string() +
        "test() :- if( first(number(?A)), is(?B, +(?A, ?A)) ), do(debugWatch(?B)).\r\n" +
        "debugWatch(?x) :- del(), add(item(?x)).\r\n" +
        "";
        compiler->ClearWithNewRuleSet();
        testState = string() +
        "number(10).number(12).number(1). \r\n" +
        "goals(test()).";
        CHECK(compiler->Compile(example + sharedState + testState + goals));
        result = planner->FindAllPlans(factory.get(), compiler->compilerOwnedRuleSet(), compiler->goals());
        finalPlan = HtnPlanner::ToStringSolutions(result);
        CHECK_EQUAL(finalPlan, "[ { (debugWatch(20)) } ]");
        finalFacts = HtnPlanner::ToStringFacts(result);
        CHECK_EQUAL(finalFacts,  "[ { number(10) => ,number(12) => ,number(1) => ,item(20) =>  } ]");

        // ***** sortBy
        example = string() +
        "test() :- if( sortBy(?A, <(number(?A))) ), do(debugWatch(?A)).\r\n" +
        "debugWatch(?x) :- del(), add(item(?x)).\r\n" +
        "";
        compiler->ClearWithNewRuleSet();
        testState = string() +
        "number(10).number(12).number(0). \r\n" +
        "goals(test()).";
        CHECK(compiler->Compile(example + sharedState + testState + goals));
        result = planner->FindAllPlans(factory.get(), compiler->compilerOwnedRuleSet(), compiler->goals());
        finalPlan = HtnPlanner::ToStringSolutions(result);
        CHECK_EQUAL(finalPlan, "[ { (debugWatch(0)) } { (debugWatch(10)) } { (debugWatch(12)) } ]");
        finalFacts = HtnPlanner::ToStringFacts(result);
        CHECK_EQUAL(finalFacts,  "[ { number(10) => ,number(12) => ,number(0) => ,item(0) =>  } { number(10) => ,number(12) => ,number(0) => ,item(10) =>  } { number(10) => ,number(12) => ,number(0) => ,item(12) =>  } ]");

        // ***** sortBy
        example = string() +
        "test() :- if( sortBy(?A, <(number(?A))) ), do(debugWatch(?A)).\r\n" +
        "debugWatch(?x) :- del(), add(item(?x)).\r\n" +
        "";
        compiler->ClearWithNewRuleSet();
        testState = string() +
        "number(10).number(12).number(0). \r\n" +
        "goals(test()).";
        CHECK(compiler->Compile(example + sharedState + testState + goals));
        result = planner->FindAllPlans(factory.get(), compiler->compilerOwnedRuleSet(), compiler->goals());
        finalPlan = HtnPlanner::ToStringSolutions(result);
        CHECK_EQUAL(finalPlan, "[ { (debugWatch(0)) } { (debugWatch(10)) } { (debugWatch(12)) } ]");
        finalFacts = HtnPlanner::ToStringFacts(result);
        CHECK_EQUAL(finalFacts,  "[ { number(10) => ,number(12) => ,number(0) => ,item(0) =>  } { number(10) => ,number(12) => ,number(0) => ,item(10) =>  } { number(10) => ,number(12) => ,number(0) => ,item(12) =>  } ]");

        // ***** using variables from head that are not in if
        example = string() +
        "test(?C) :- if( first( sortBy(?A, <(number(?A)))), is(?B, +(?A, ?A)) ), do(debugWatch(?C)).\r\n" +
        "debugWatch(?x) :- del(), add(item(?x)).\r\n" +
        "";
        compiler->ClearWithNewRuleSet();
        testState = string() +
        "number(10).number(12).number(1). \r\n" +
        "goals(test(99)).";
        CHECK(compiler->Compile(example + sharedState + testState + goals));
        result = planner->FindAllPlans(factory.get(), compiler->compilerOwnedRuleSet(), compiler->goals());
        finalPlan = HtnPlanner::ToStringSolutions(result);
        CHECK_EQUAL(finalPlan, "[ { (debugWatch(99)) } ]");
        finalFacts = HtnPlanner::ToStringFacts(result);
        CHECK_EQUAL(finalFacts,  "[ { number(10) => ,number(12) => ,number(1) => ,item(99) =>  } ]");

        // ***** first and sortby: with terms after
        example = string() +
        "test() :- if( first( sortBy(?A, <(number(?A)))), is(?B, +(?A, ?A)) ), do(debugWatch(?B)).\r\n" +
        "debugWatch(?x) :- del(), add(item(?x)).\r\n" +
        "";
        compiler->ClearWithNewRuleSet();
        testState = string() +
        "number(10).number(12).number(1). \r\n" +
        "goals(test()).";
        CHECK(compiler->Compile(example + sharedState + testState + goals));
        result = planner->FindAllPlans(factory.get(), compiler->compilerOwnedRuleSet(), compiler->goals());
        finalPlan = HtnPlanner::ToStringSolutions(result);
        CHECK_EQUAL(finalPlan, "[ { (debugWatch(2)) } ]");
        finalFacts = HtnPlanner::ToStringFacts(result);
        CHECK_EQUAL(finalFacts,  "[ { number(10) => ,number(12) => ,number(1) => ,item(2) =>  } ]");

        // ***** Not
        example = string() +
        "test() :- if( person(?X), not(isFunny(?X)) ), do(debugWatch(?X)).\r\n" +
        "debugWatch(?x) :- del(), add(item(?x)).\r\n" +
        "";
        compiler->ClearWithNewRuleSet();
        testState = string() +
        "person(Jim).person(Mary).isFunny(Mary). \r\n" +
        "goals(test()).";
        CHECK(compiler->Compile(example + sharedState + testState + goals));
        result = planner->FindAllPlans(factory.get(), compiler->compilerOwnedRuleSet(), compiler->goals());
        finalPlan = HtnPlanner::ToStringSolutions(result);
        CHECK_EQUAL(finalPlan, "[ { (debugWatch(Jim)) } ]");
        finalFacts = HtnPlanner::ToStringFacts(result);
        CHECK_EQUAL(finalFacts,  "[ { person(Jim) => ,person(Mary) => ,isFunny(Mary) => ,item(Jim) =>  } ]");
    }

    TEST(PlannerStateTest)
    {
        shared_ptr<HtnTermFactory> factory = shared_ptr<HtnTermFactory>(new HtnTermFactory());
        shared_ptr<HtnRuleSet> state = shared_ptr<HtnRuleSet>(new HtnRuleSet());
        shared_ptr<HtnPlanner> planner = shared_ptr<HtnPlanner>(new HtnPlanner());
        shared_ptr<HtnCompiler> compiler = shared_ptr<HtnCompiler>(new HtnCompiler(factory.get(), state.get(), planner.get()));
        shared_ptr<HtnPlanner::SolutionsType> result;
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

//        // No goals
//        compiler->ClearWithNewRuleSet();
//        testState = string() +
//        "trace(?Value) :- del(), add(?Value). \r\n" +
//        "";
//        goals = string() +
//        "goals().\r\n" +
//        "";
//        CHECK(compiler->Compile(sharedState + testState + goals));
//        result = planner->FindAllPlans(factory.get(), compiler->compilerOwnedRuleSet(), compiler->goals());
//        finalPlan = HtnPlanner::ToStringSolutions(result);
//        CHECK_EQUAL(finalPlan, "null");
    }
}
