//
//  DebugHtnTest.cpp
//  TestLib
//
//  Simple HTN test to debug the API differences
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
#include "UnitTest++/UnitTest++.h"
using namespace Prolog;

SUITE(DebugHtnTests)
{
    TEST(ExactCopyFromHtnPlannerTests)
    {
        shared_ptr<HtnTermFactory> factory = shared_ptr<HtnTermFactory>(new HtnTermFactory());
        shared_ptr<HtnRuleSet> state = shared_ptr<HtnRuleSet>(new HtnRuleSet());
        shared_ptr<HtnPlanner> planner = shared_ptr<HtnPlanner>(new HtnPlanner());
        shared_ptr<HtnCompiler> compiler = shared_ptr<HtnCompiler>(new HtnCompiler(factory.get(), state.get(), planner.get()));
        shared_ptr<HtnPlanner::SolutionsType> result;
        string finalPlan;
        string testState;
        string sharedState;
        string goals;
        
        // State true for all tests
        sharedState = string() + "";
        
        // Just one successful operator - EXACT copy from HtnPlannerTests.cpp line 184-194
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
    }
}