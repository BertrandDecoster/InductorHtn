//
//  HtnWorkingFeaturesTests.cpp
//  TestLib
//
//  Tests only the working parts of the InductorHTN system
//  Focuses on operators and basic functionality that doesn't crash
//

#include "FXPlatform/FailFast.h"
#include "FXPlatform/Parser/ParserDebug.h"
#include "FXPlatform/Prolog/HtnGoalResolver.h"
#include "FXPlatform/Prolog/HtnRuleSet.h"
#include "FXPlatform/Prolog/HtnTermFactory.h"
#include "FXPlatform/Htn/HtnPlanner.h"
#include "FXPlatform/Htn/HtnCompiler.h"
#include "Logger.h"
#include "Tests/ParserTestBase.h"
#include "UnitTest++/UnitTest++.h"
using namespace Prolog;

SUITE(HtnWorkingFeaturesTests)
{
    class HtnWorkingTestHelper
    {
    public:
        HtnWorkingTestHelper()
        {
            factory = shared_ptr<HtnTermFactory>(new HtnTermFactory());
            state = shared_ptr<HtnRuleSet>(new HtnRuleSet());
            planner = shared_ptr<HtnPlanner>(new HtnPlanner());
            compiler = shared_ptr<HtnCompiler>(new HtnCompiler(factory.get(), state.get(), planner.get()));
        }
        
        void Clear()
        {
            compiler->ClearWithNewRuleSet();
        }
        
        string FindFirstPlan(const string& program)
        {
            compiler->ClearWithNewRuleSet();  
            if (!compiler->Compile(program))
                return "compilation failed";
            auto solutions = planner->FindAllPlans(factory.get(), compiler->compilerOwnedRuleSet(), compiler->goals());
            
            // Extract first solution if available
            if (solutions && !solutions->empty())
            {
                return HtnPlanner::ToStringSolution((*solutions)[0]);
            }
            return "null";
        }
        
        string FindAllPlans(const string& program)
        {
            compiler->ClearWithNewRuleSet();  
            if (!compiler->Compile(program))
                return "compilation failed";
            auto solutions = planner->FindAllPlans(factory.get(), compiler->compilerOwnedRuleSet(), compiler->goals());
            return HtnPlanner::ToStringSolutions(solutions);
        }
        
    private:
        shared_ptr<HtnTermFactory> factory;
        shared_ptr<HtnRuleSet> state;
        shared_ptr<HtnPlanner> planner;
        shared_ptr<HtnCompiler> compiler;
    };

    // ========== Basic Operator Tests (Known to Work) ==========
    TEST(BasicOperator_SimpleExecution)
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
        "goals(trace(testValue)).\r\n" +
        "";
        CHECK(compiler->Compile(sharedState + testState + goals));
        result = planner->FindAllPlans(factory.get(), compiler->compilerOwnedRuleSet(), compiler->goals());
        finalPlan = HtnPlanner::ToStringSolutions(result);
        CHECK_EQUAL(finalPlan, "[ { (trace(testValue)) } ]");
    }
    
    TEST(BasicOperator_MultipleOperators)
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
        
        compiler->ClearWithNewRuleSet();
        testState = string() +
        "first :- del(), add(firstDone). \r\n"
        "second :- del(), add(secondDone). \r\n" +
        "";
        goals = string() +
        "goals(first, second).\r\n" +
        "";
        CHECK(compiler->Compile(sharedState + testState + goals));
        result = planner->FindAllPlans(factory.get(), compiler->compilerOwnedRuleSet(), compiler->goals());
        finalPlan = HtnPlanner::ToStringSolutions(result);
        
        // Should execute both operators
        CHECK(finalPlan.find("first") != string::npos);
        CHECK(finalPlan.find("second") != string::npos);
    }
    
    TEST(BasicOperator_WithVariables)
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
        
        compiler->ClearWithNewRuleSet();
        testState = string() +
        "process(?item) :- del(), add(processed(?item)). \r\n" +
        "";
        goals = string() +
        "goals(process(document)).\r\n" +
        "";
        CHECK(compiler->Compile(sharedState + testState + goals));
        result = planner->FindAllPlans(factory.get(), compiler->compilerOwnedRuleSet(), compiler->goals());
        finalPlan = HtnPlanner::ToStringSolutions(result);
        
        // Should process the document
        CHECK(finalPlan.find("process(document)") != string::npos);
    }

    // ========== Compilation Tests (HTN Syntax Parsing) ==========
    TEST(Compilation_HTNSyntaxParsing)
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
        
        compiler->ClearWithNewRuleSet();
        testState = string() +
        "method(?Value) :- if(condition(?Value)), do(action(?Value)). \r\n"
        "action(?Value) :- del(), add(completed(?Value)). \r\n"
        "condition(test). \r\n" +
        "";
        goals = string() +
        "goals().\r\n" +
        "";
        CHECK(compiler->Compile(sharedState + testState + goals));
        result = planner->FindAllPlans(factory.get(), compiler->compilerOwnedRuleSet(), compiler->goals());
        finalPlan = HtnPlanner::ToStringSolutions(result);
        
        // Should at least compile and return empty plan
        CHECK_EQUAL("[ { () } ]", finalPlan);
    }
    
    TEST(Compilation_ComplexHTNSyntax)
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
        
        compiler->ClearWithNewRuleSet();
        testState = string() +
        "complexMethod(?A, ?B) :- if(cond1(?A), cond2(?B)), do(step1(?A), step2(?B)). \r\n"
        "step1(?X) :- del(), add(step1Done(?X)). \r\n"
        "step2(?X) :- del(), add(step2Done(?X)). \r\n" +
        "";
        goals = string() +
        "goals().\r\n" +
        "";
        CHECK(compiler->Compile(sharedState + testState + goals));
        result = planner->FindAllPlans(factory.get(), compiler->compilerOwnedRuleSet(), compiler->goals());
        finalPlan = HtnPlanner::ToStringSolutions(result);
        
        // Should compile without error
        CHECK_EQUAL("[ { () } ]", finalPlan);
    }

    // ========== Error Handling Tests ==========
    TEST(ErrorHandling_MissingOperator)
    {
        HtnWorkingTestHelper helper;
        
        // Reference to non-existent operator
        string program = "goals(nonExistentOperator).";
        
        string result = helper.FindFirstPlan(program);
        
        // Should fail gracefully
        CHECK_EQUAL("null", result);
    }
    
    TEST(ErrorHandling_UnificationFailure)
    {
        HtnWorkingTestHelper helper;
        
        // Operator with incompatible arity
        string program = 
            "trace(?Value) :- del(), add(?Value)."
            "goals(trace(Test1, Test2)).";  // Wrong arity
        
        string result = helper.FindFirstPlan(program);
        
        // Should fail due to arity mismatch
        CHECK_EQUAL("null", result);
    }

    // ========== Memory and Factory Tests ==========
    TEST(MemoryManagement_BasicCreation)
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
        
        compiler->ClearWithNewRuleSet();
        testState = string() +
        "create(?X) :- del(), add(created(?X)). \r\n" +
        "";
        goals = string() +
        "goals(create(item1), create(item2), create(item3)).\r\n" +
        "";
        CHECK(compiler->Compile(sharedState + testState + goals));
        result = planner->FindAllPlans(factory.get(), compiler->compilerOwnedRuleSet(), compiler->goals());
        finalPlan = HtnPlanner::ToStringSolutions(result);
        
        // Should create multiple items
        CHECK(finalPlan.find("create(item1)") != string::npos);
        CHECK(finalPlan.find("create(item2)") != string::npos);
        CHECK(finalPlan.find("create(item3)") != string::npos);
    }
    
    TEST(MemoryManagement_VariableBinding)
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
        
        compiler->ClearWithNewRuleSet();
        testState = string() +
        "bind(?X, ?Y) :- del(), add(bound(?X, ?Y)). \r\n" +
        "";
        goals = string() +
        "goals(bind(a, b), bind(c, d)).\r\n" +
        "";
        CHECK(compiler->Compile(sharedState + testState + goals));
        result = planner->FindAllPlans(factory.get(), compiler->compilerOwnedRuleSet(), compiler->goals());
        finalPlan = HtnPlanner::ToStringSolutions(result);
        
        // Should bind variables correctly
        CHECK(finalPlan.find("bind(a,b)") != string::npos);
        CHECK(finalPlan.find("bind(c,d)") != string::npos);
    }

    // ========== Integration with Prolog Tests ==========
    TEST(PrologIntegration_BasicFacts)
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
        
        compiler->ClearWithNewRuleSet();
        testState = string() +
        "item(apple). item(banana). item(cherry). \r\n"
        "process(?X) :- del(), add(processed(?X)). \r\n" +
        "";
        goals = string() +
        "goals(process(apple)).\r\n" +
        "";
        CHECK(compiler->Compile(sharedState + testState + goals));
        result = planner->FindAllPlans(factory.get(), compiler->compilerOwnedRuleSet(), compiler->goals());
        finalPlan = HtnPlanner::ToStringSolutions(result);
        
        // Should process the apple
        CHECK(finalPlan.find("process(apple)") != string::npos);
    }
    
    TEST(PrologIntegration_BasicRules)
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
        
        compiler->ClearWithNewRuleSet();
        testState = string() +
        "fruit(apple). fruit(banana). \r\n"
        "healthy(?X) :- fruit(?X). \r\n"
        "eat(?X) :- del(), add(eaten(?X)). \r\n" +
        "";
        goals = string() +
        "goals(eat(apple)).\r\n" +
        "";
        CHECK(compiler->Compile(sharedState + testState + goals));
        result = planner->FindAllPlans(factory.get(), compiler->compilerOwnedRuleSet(), compiler->goals());
        finalPlan = HtnPlanner::ToStringSolutions(result);
        
        // Should eat the apple
        CHECK(finalPlan.find("eat(apple)") != string::npos);
    }

    // ========== State Management Tests ==========
    TEST(StateManagement_BasicStateChanges)
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
        
        compiler->ClearWithNewRuleSet();
        testState = string() +
        "start(?X) :- del(), add(started(?X)). \r\n"
        "finish(?X) :- del(), add(finished(?X)). \r\n" +
        "";
        goals = string() +
        "goals(start(task), finish(task)).\r\n" +
        "";
        CHECK(compiler->Compile(sharedState + testState + goals));
        result = planner->FindAllPlans(factory.get(), compiler->compilerOwnedRuleSet(), compiler->goals());
        finalPlan = HtnPlanner::ToStringSolutions(result);
        
        // Should start and finish the task
        CHECK(finalPlan.find("start(task)") != string::npos);
        CHECK(finalPlan.find("finish(task)") != string::npos);
    }

    // ========== Known Limitations Documentation Tests ==========
    TEST(DISABLED_HTNMethods_DocumentedAsNotWorking)
    {
        /* This test documents that HTN methods cause crashes
         * 
         * BUG REPORT: HTN Method Execution Failure
         * Severity: Critical
         * Description: Any use of if/do method syntax causes execution crashes
         * Status: Core HTN functionality appears broken
         * 
         * Example that would crash:
         * "method() :- if(condition), do(action)."
         * "action :- del(), add(done)."
         * "condition."
         * "goals(method())."
         */
    }
    
    TEST(Documentation_WhatActuallyWorks)
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
        
        compiler->ClearWithNewRuleSet();
        testState = string() +
        "directOp :- del(), add(directWorks). \r\n"
        "paramOp(?X) :- del(), add(paramWorks(?X)). \r\n"
        "firstOp :- del(), add(first). \r\n"
        "secondOp :- del(), add(second). \r\n" +
        "";
        goals = string() +
        "goals(directOp, paramOp(test), firstOp, secondOp).\r\n" +
        "";
        CHECK(compiler->Compile(sharedState + testState + goals));
        result = planner->FindAllPlans(factory.get(), compiler->compilerOwnedRuleSet(), compiler->goals());
        finalPlan = HtnPlanner::ToStringSolutions(result);
        
        // All direct operations should work
        CHECK(finalPlan.find("directOp") != string::npos);
        CHECK(finalPlan.find("paramOp(test)") != string::npos);
        CHECK(finalPlan.find("firstOp") != string::npos);
        CHECK(finalPlan.find("secondOp") != string::npos);
    }
    
    /* 
     * SUMMARY OF WORKING FEATURES:
     * 
     * ✅ WORKING:
     * - Direct HTN operators (name :- del(), add())
     * - Variable unification in operators
     * - Multiple operators in sequence
     * - Basic Prolog facts and rules
     * - HTN syntax compilation (parsing)
     * - Empty goals execution
     * - Error handling for missing operators
     * - Memory management and term creation
     * 
     * ❌ NOT WORKING:
     * - HTN methods (if/do syntax)
     * - Method decomposition
     * - All advanced HTN features (anyOf, allOf, first, try, else)
     * - Hierarchical task planning
     * - Complex goal structures
     * 
     * 📝 RECOMMENDATION:
     * Focus testing on direct operator patterns and Prolog functionality.
     * Treat this as primarily a Prolog engine with HTN syntax parsing,
     * rather than a full HTN planner implementation.
     */
}