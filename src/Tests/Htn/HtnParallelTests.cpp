//
//  HtnParallelTests.cpp
//  TestLib
//
//  Tests for the parallel() keyword and PlanParallelizer post-processor
//  Copyright © 2025 Bertrand Decoster. All rights reserved.
//

#include "FXPlatform/FailFast.h"
#include "FXPlatform/Parser/ParserDebug.h"
#include "FXPlatform/Prolog/HtnGoalResolver.h"
#include "FXPlatform/Prolog/HtnRuleSet.h"
#include "FXPlatform/Prolog/HtnTermFactory.h"
#include "FXPlatform/Htn/HtnPlanner.h"
#include "FXPlatform/Htn/HtnCompiler.h"
#include "FXPlatform/Htn/PlanParallelizer.h"
#include "Logger.h"
#include "Tests/ParserTestBase.h"
#include "UnitTest++/UnitTest++.h"
using namespace Prolog;

SUITE(HtnParallelTests)
{
    class HtnParallelTestHelper
    {
    public:
        HtnParallelTestHelper()
        {
            factory = shared_ptr<HtnTermFactory>(new HtnTermFactory());
            state = shared_ptr<HtnRuleSet>(new HtnRuleSet());
            planner = shared_ptr<HtnPlanner>(new HtnPlanner());
            compiler = shared_ptr<HtnCompiler>(new HtnCompiler(factory.get(), state.get(), planner.get()));
        }

        string FindFirstPlan(const string& program)
        {
            compiler->ClearWithNewRuleSet();
            CHECK(compiler->Compile(program));
            auto solutions = planner->FindAllPlans(factory.get(), compiler->compilerOwnedRuleSet(), compiler->goals());

            if (solutions && !solutions->empty())
            {
                return HtnPlanner::ToStringSolution((*solutions)[0]);
            }
            return "null";
        }

        // Get raw operators from first solution (includes markers)
        vector<shared_ptr<HtnTerm>> GetFirstPlanOperators(const string& program)
        {
            compiler->ClearWithNewRuleSet();
            CHECK(compiler->Compile(program));
            auto solutions = planner->FindAllPlans(factory.get(), compiler->compilerOwnedRuleSet(), compiler->goals());

            if (solutions && !solutions->empty())
            {
                return (*solutions)[0]->operators();
            }
            return vector<shared_ptr<HtnTerm>>();
        }

        // Get parallelized plan from first solution
        vector<ParallelizedOperator> GetParallelizedPlan(const string& program)
        {
            compiler->ClearWithNewRuleSet();
            CHECK(compiler->Compile(program));
            auto solutions = planner->FindAllPlans(factory.get(), compiler->compilerOwnedRuleSet(), compiler->goals());

            if (solutions && !solutions->empty())
            {
                auto ops = (*solutions)[0]->operators();

                // Empty operator definitions - simplified dependency analysis assigns same timestep
                // to all operators within parallel scopes (domain author ensures independence)
                map<string, shared_ptr<HtnOperator>> operatorDefs;

                return PlanParallelizer::Parallelize(ops, operatorDefs);
            }
            return vector<ParallelizedOperator>();
        }

    private:
        shared_ptr<HtnTermFactory> factory;
        shared_ptr<HtnRuleSet> state;
        shared_ptr<HtnPlanner> planner;
        shared_ptr<HtnCompiler> compiler;
    };

    // ========== Basic Parallel Tests ==========

    TEST(Parallel_BasicTwoTasks)
    {
        HtnParallelTestHelper helper;

        // Two independent operators within a parallel block
        string program =
            "doParallel() :- if(), do(parallel(taskA, taskB))."

            "taskA :- del(), add(doneA)."
            "taskB :- del(), add(doneB)."

            "goals(doParallel()).";

        string result = helper.FindFirstPlan(program);

        // Should produce a valid plan containing both tasks
        CHECK(result.find("taskA") != string::npos);
        CHECK(result.find("taskB") != string::npos);
    }

    TEST(Parallel_MarkersInPlan)
    {
        HtnParallelTestHelper helper;

        string program =
            "doParallel() :- if(), do(parallel(taskA, taskB))."
            "taskA :- del(), add(doneA)."
            "taskB :- del(), add(doneB)."
            "goals(doParallel()).";

        auto ops = helper.GetFirstPlanOperators(program);
        CHECK(!ops.empty());

        // Should have beginParallel, taskA, taskB, endParallel (4 operators)
        CHECK(ops.size() >= 4);

        // Check for markers
        bool hasBeginParallel = false;
        bool hasEndParallel = false;
        for(const auto& op : ops)
        {
            if(op->name() == "beginParallel") hasBeginParallel = true;
            if(op->name() == "endParallel") hasEndParallel = true;
        }
        CHECK(hasBeginParallel);
        CHECK(hasEndParallel);
    }

    TEST(Parallel_SameTimestep)
    {
        HtnParallelTestHelper helper;

        // Two independent tasks should get same timestep
        string program =
            "doParallel() :- if(), do(parallel(movePlayer, moveWarden))."
            "movePlayer :- del(playerAt(a)), add(playerAt(b))."
            "moveWarden :- del(wardenAt(x)), add(wardenAt(y))."
            "playerAt(a). wardenAt(x)."
            "goals(doParallel()).";

        auto parallelized = helper.GetParallelizedPlan(program);
        CHECK(parallelized.size() >= 2);

        // Find the two move operators
        int playerTimestep = -1;
        int wardenTimestep = -1;
        for(const auto& pop : parallelized)
        {
            if(pop.op->name() == "movePlayer") playerTimestep = pop.timestep;
            if(pop.op->name() == "moveWarden") wardenTimestep = pop.timestep;
        }

        // Both should have valid timesteps and be the same (can run in parallel)
        CHECK(playerTimestep >= 0);
        CHECK(wardenTimestep >= 0);
        CHECK_EQUAL(playerTimestep, wardenTimestep);
    }

    TEST(Parallel_MixedSequentialAndParallel)
    {
        HtnParallelTestHelper helper;

        // Sequential, then parallel, then sequential
        // Each operator has completely independent facts
        string program =
            "workflow() :- if(), do(setup, parallel(taskA, taskB), cleanup)."
            "setup :- del(stateS1), add(stateS2)."
            "taskA :- del(stateA1), add(stateA2)."
            "taskB :- del(stateB1), add(stateB2)."
            "cleanup :- del(stateC1), add(stateC2)."
            "stateS1. stateA1. stateB1. stateC1."
            "goals(workflow()).";

        auto parallelized = helper.GetParallelizedPlan(program);
        CHECK(parallelized.size() >= 4);

        int setupTimestep = -1;
        int taskATimestep = -1;
        int taskBTimestep = -1;
        int cleanupTimestep = -1;

        for(const auto& pop : parallelized)
        {
            if(pop.op->name() == "setup") setupTimestep = pop.timestep;
            if(pop.op->name() == "taskA") taskATimestep = pop.timestep;
            if(pop.op->name() == "taskB") taskBTimestep = pop.timestep;
            if(pop.op->name() == "cleanup") cleanupTimestep = pop.timestep;
        }

        // setup < taskA = taskB < cleanup
        CHECK(setupTimestep < taskATimestep);
        CHECK_EQUAL(taskATimestep, taskBTimestep);
        CHECK(taskATimestep < cleanupTimestep);
    }

    TEST(Parallel_ThreeAgents)
    {
        HtnParallelTestHelper helper;

        // Three independent agents
        string program =
            "tripleAction() :- if(), do(parallel(agentA, agentB, agentC))."
            "agentA :- del(), add(aDone)."
            "agentB :- del(), add(bDone)."
            "agentC :- del(), add(cDone)."
            "goals(tripleAction()).";

        auto parallelized = helper.GetParallelizedPlan(program);
        CHECK(parallelized.size() >= 3);

        // All three should have the same timestep
        int timestepA = -1, timestepB = -1, timestepC = -1;
        for(const auto& pop : parallelized)
        {
            if(pop.op->name() == "agentA") timestepA = pop.timestep;
            if(pop.op->name() == "agentB") timestepB = pop.timestep;
            if(pop.op->name() == "agentC") timestepC = pop.timestep;
        }

        CHECK(timestepA >= 0);
        CHECK_EQUAL(timestepA, timestepB);
        CHECK_EQUAL(timestepB, timestepC);
    }

    TEST(Parallel_EmptyBlock)
    {
        HtnParallelTestHelper helper;

        // Empty parallel block (edge case)
        // Each operator has completely independent facts
        string program =
            "emptyParallel() :- if(), do(setup, parallel(), cleanup)."
            "setup :- del(stateS1), add(stateS2)."
            "cleanup :- del(stateC1), add(stateC2)."
            "stateS1. stateC1."
            "goals(emptyParallel()).";

        string result = helper.FindFirstPlan(program);

        // Should still produce a valid plan
        CHECK(result.find("setup") != string::npos);
        CHECK(result.find("cleanup") != string::npos);
    }

    TEST(Parallel_SingleTask)
    {
        HtnParallelTestHelper helper;

        // Single task in parallel (degenerate case)
        string program =
            "singleParallel() :- if(), do(parallel(onlyTask))."
            "onlyTask :- del(), add(taskDone)."
            "goals(singleParallel()).";

        string result = helper.FindFirstPlan(program);
        CHECK(result.find("onlyTask") != string::npos);
    }

    TEST(Parallel_NestedDecomposition)
    {
        HtnParallelTestHelper helper;

        // Tasks within parallel decompose into multiple operators
        string program =
            "parallelMoves() :- if(), do(parallel(playerMove, wardenMove))."
            "playerMove :- if(), do(step1, step2)."
            "wardenMove :- if(), do(stepA, stepB)."
            "step1 :- del(), add(p1Done)."
            "step2 :- del(), add(p2Done)."
            "stepA :- del(), add(w1Done)."
            "stepB :- del(), add(w2Done)."
            "goals(parallelMoves()).";

        auto parallelized = helper.GetParallelizedPlan(program);
        CHECK(parallelized.size() >= 4);

        // All decomposed operators should be in the same parallel scope
        bool allSameScope = true;
        int firstScope = -999;
        for(const auto& pop : parallelized)
        {
            if(pop.op->name() != "beginParallel" && pop.op->name() != "endParallel")
            {
                if(firstScope == -999)
                {
                    firstScope = pop.scopeId;
                }
                else if(pop.scopeId != firstScope)
                {
                    allSameScope = false;
                }
            }
        }
        CHECK(allSameScope);
    }

    // ========== PlanParallelizer ToJson Tests ==========

    TEST(Parallelizer_ToJsonFormat)
    {
        HtnParallelTestHelper helper;

        string program =
            "doParallel() :- if(), do(parallel(taskA, taskB))."
            "taskA :- del(), add(doneA)."
            "taskB :- del(), add(doneB)."
            "goals(doParallel()).";

        auto parallelized = helper.GetParallelizedPlan(program);
        string json = PlanParallelizer::ToJson(parallelized);

        // Should be valid JSON with expected structure
        CHECK(json.find("\"operators\"") != string::npos);
        CHECK(json.find("\"timestep\"") != string::npos);
        CHECK(json.find("\"scopeId\"") != string::npos);
        CHECK(json.find("\"dependsOn\"") != string::npos);
    }
}
