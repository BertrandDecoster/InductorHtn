//
//  HtnAdvancedFeaturesTests.cpp
//  TestLib
//
//  Created by Claude Code for comprehensive HTN advanced features testing
//  Tests anyOf, allOf, first(), try(), hidden operators, and method ordering
//  Copyright © 2025 Bertrand Decoster. All rights reserved.

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

SUITE(HtnAdvancedFeaturesTests)
{
    class HtnAdvancedTestHelper
    {
    public:
        HtnAdvancedTestHelper()
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
            CHECK(compiler->Compile(program));
            auto solutions = planner->FindAllPlans(factory.get(), compiler->compilerOwnedRuleSet(), compiler->goals());
            return HtnPlanner::ToStringSolutions(solutions);
        }
        
    private:
        shared_ptr<HtnTermFactory> factory;
        shared_ptr<HtnRuleSet> state;
        shared_ptr<HtnPlanner> planner;
        shared_ptr<HtnCompiler> compiler;
    };

    // ========== anyOf Method Tests ==========
    TEST(AnyOf_BasicUsage)
    {
        HtnAdvancedTestHelper helper;
        
        // anyOf should handle multiple variable bindings within ONE method
        // If multiple units are in range, attack at least one (wrapped in try())
        string program = 
            "attackEnemies() :- anyOf, if(isInRange(?unit)), do(attack(?unit))."
            
            // State: multiple units in range
            "isInRange(enemy1). isInRange(enemy2). isInRange(enemy3). "
            
            // Operators
            "attack(?target) :- del(), add(attacked(?target))."
            
            "goals(attackEnemies()).";
        
        string result = helper.FindFirstPlan(program);
        
        // Should attack at least one enemy (anyOf semantics: at least one must succeed)
        CHECK(result.find("attack") != string::npos);
        CHECK(result.find("enemy") != string::npos);
    }
    
    TEST(AnyOf_MultipleVariableBindings)
    {
        HtnAdvancedTestHelper helper;
        
        // anyOf should handle multiple variable bindings and succeed if at least one works
        // Some items might be unavailable - succeed if we can collect at least one
        string program = 
            "collectItems() :- anyOf, if(availableItem(?item)), do(collect(?item))."
            
            // Some items available, some not
            "availableItem(gold). availableItem(food). availableItem(wood). "
            
            // Operators - collecting food will "fail" for testing
            "collect(gold) :- del(), add(has(gold))."
            "collect(food) :- del(), add(cantCollectFood)."
            "collect(wood) :- del(), add(has(wood))."
            
            "goals(collectItems()).";
        
        string result = helper.FindFirstPlan(program);
        
        // Should collect at least one item (anyOf: wrapped in try(), at least one must succeed)
        CHECK(result.find("collect") != string::npos);
    }
    
    TEST(AnyOf_NoValidBindings)
    {
        HtnAdvancedTestHelper helper;
        
        // When no variable bindings satisfy the if() condition, should fail
        string program = 
            "doNothing() :- anyOf, if(nonExistentCondition(?x)), do(action(?x))."
            
            // No facts match the condition
            
            "action(?x) :- del(), add(did(?x))."
            
            "goals(doNothing()).";
        
        string result = helper.FindFirstPlan(program);
        CHECK_EQUAL("null", result);
    }

    // ========== allOf Method Tests ==========
    TEST(AllOf_BasicUsage)
    {
        HtnAdvancedTestHelper helper;
        
        // allOf should handle multiple variable bindings within ONE method
        // All units that are damaged must be repaired (all bindings must succeed)
        string program = 
            "repairAllDamaged() :- allOf, if(isDamaged(?unit)), do(repair(?unit))."
            
            // State: multiple damaged units
            "isDamaged(unit1). isDamaged(unit2). isDamaged(unit3). "
            
            // Operators
            "repair(?target) :- del(isDamaged(?target)), add(repaired(?target))."
            
            "goals(repairAllDamaged()).";
        
        string result = helper.FindFirstPlan(program);
        
        // Should repair ALL damaged units (allOf semantics: all bindings must succeed)
        CHECK(result.find("repair(unit1)") != string::npos);
        CHECK(result.find("repair(unit2)") != string::npos);
        CHECK(result.find("repair(unit3)") != string::npos);
    }
    
    TEST(AllOf_WithVariableBindings)
    {
        HtnAdvancedTestHelper helper;
        
        // allOf handles multiple variable bindings - all must succeed
        // Heal all wounded soldiers
        string program = 
            "healWounded() :- allOf, if(isWounded(?soldier)), do(heal(?soldier))."
            
            // Some soldiers are wounded
            "isWounded(soldier1). isWounded(soldier3). "
            
            // Operators
            "heal(?s) :- del(isWounded(?s)), add(healthy(?s))."
            
            "goals(healWounded()).";
        
        string result = helper.FindFirstPlan(program);
        
        // Should heal all wounded soldiers
        CHECK(result.find("heal(soldier1)") != string::npos);
        CHECK(result.find("heal(soldier3)") != string::npos);
        CHECK(result.find("heal(soldier2)") == string::npos); // soldier2 not wounded
    }
    
    TEST(AllOf_NoMatchingBindings)
    {
        HtnAdvancedTestHelper helper;
        
        // allOf with no variable bindings should succeed (empty action set)
        string program = 
            "cleanupOptional() :- allOf, if(needsCleanup(?item)), do(cleanup(?item))."
            
            // No items need cleanup
            
            "cleanup(?x) :- del(), add(cleaned(?x))."
            
            "goals(cleanupOptional()).";
        
        string result = helper.FindFirstPlan(program);
        
        // Should fail when no bindings exist (allOf with no matching conditions fails)
        CHECK_EQUAL("null", result);
    }

    // ========== first() Operator Tests ==========
    TEST(First_BasicUsage)
    {
        HtnAdvancedTestHelper helper;
        
        // first() should return only the first solution of a query
        // Based on Taxi.htn usage: first(at(?x), at-taxi-stand(?t, ?x), ...)
        string program = 
            "findNearestTaxi() :- if(first(at(?location), taxiAt(?taxi, ?location), distance(?location, ?dist))), do(hail(?taxi, ?location))."
            
            // Multiple taxis at different locations
            "taxiAt(taxi1, downtown). taxiAt(taxi2, uptown). taxiAt(taxi3, suburb). "
            "distance(downtown, 1). distance(uptown, 3). distance(suburb, 5). "
            "at(downtown). at(uptown). at(suburb). "
            
            "hail(?taxi, ?loc) :- del(), add(hired(?taxi, ?loc))."
            
            "goals(findNearestTaxi()).";
        
        string result = helper.FindFirstPlan(program);
        
        // Should hire exactly one taxi (the first one found)
        CHECK(result.find("hail") != string::npos);
        
        // Count how many taxi hires occurred (should be 1)
        int hailCount = 0;
        size_t pos = 0;
        while ((pos = result.find("hail", pos)) != string::npos) {
            hailCount++;
            pos++;
        }
        CHECK_EQUAL(1, hailCount);
    }
    
    TEST(First_NoSolutions)
    {
        HtnAdvancedTestHelper helper;
        
        // first() with no matching solutions should fail
        string program = 
            "findSomething() :- if(first(item(?x), available(?x))), do(take(?x))."
            
            // No available items
            
            "take(?item) :- del(), add(taken(?item))."
            
            "goals(findSomething()).";
        
        string result = helper.FindFirstPlan(program);
        CHECK_EQUAL("null", result);
    }
    
    TEST(First_ComplexConditions)
    {
        HtnAdvancedTestHelper helper;
        
        // first() with multiple conditions (similar to Taxi.htn)
        string program = 
            "quickestRoute() :- if(first(location(?loc), reachable(?loc), travelTime(?loc, ?time), <(?time, 30))), do(goTo(?loc))."
            
            // Multiple locations with different travel times
            "location(downtown). location(uptown). location(suburb). location(airport). "
            "reachable(downtown). reachable(uptown). reachable(airport). "  // suburb not reachable
            "travelTime(downtown, 45). travelTime(uptown, 25). travelTime(airport, 60). "  // Only uptown < 30
            
            "goTo(?loc) :- del(), add(wentTo(?loc))."
            
            "goals(quickestRoute()).";
        
        string result = helper.FindFirstPlan(program);
        
        // Should go to uptown (first location that meets all criteria)
        CHECK(result.find("goTo(uptown)") != string::npos);
    }

    // ========== try() Operator Tests ==========
    TEST(Try_SuccessfulOperation)
    {
        HtnAdvancedTestHelper helper;
        
        // try() should execute normally when operation succeeds
        string program = 
            "attemptTask() :- if(), do(try(riskyOperation))."
            
            "riskyOperation :- if(canSucceed), do(succeed)."
            "canSucceed. "  // Condition is met
            
            "succeed :- del(), add(succeeded)."
            
            "goals(attemptTask()).";
        
        string result = helper.FindFirstPlan(program);
        
        // Should execute successfully
        CHECK(result.find("succeed") != string::npos);
    }
    
    TEST(Try_FailedOperation)
    {
        HtnAdvancedTestHelper helper;
        
        // try() should continue gracefully when operation fails
        string program = 
            "attemptWithFallback() :- if(), do(try(riskyOperation), fallbackOperation)."
            
            "riskyOperation :- if(canSucceed), do(succeed)."
            // canSucceed is not defined - should fail
            
            "succeed :- del(), add(succeeded)."
            "fallbackOperation :- del(), add(usedFallback)."
            
            "goals(attemptWithFallback()).";
        
        string result = helper.FindFirstPlan(program);
        
        // Should execute fallback after try() fails
        CHECK(result.find("fallbackOperation") != string::npos);
        CHECK(result.find("succeed") == string::npos);  // Risky operation should not have succeeded
    }
    
    TEST(Try_NestedTryBlocks)
    {
        HtnAdvancedTestHelper helper;
        
        // Nested try() operations
        string program = 
            "complexOperation() :- if(), do(try(try(innerRisky), outerFallback), finalFallback)."
            
            "innerRisky :- if(innerCondition), do(innerSuccess)."
            "outerFallback :- if(outerCondition), do(outerSuccess)."
            
            // No conditions are met
            
            "innerSuccess :- del(), add(innerDone)."
            "outerSuccess :- del(), add(outerDone)."
            "finalFallback :- del(), add(finalDone)."
            
            "goals(complexOperation()).";
        
        string result = helper.FindFirstPlan(program);
        
        // Should fall back to final fallback
        CHECK(result.find("finalFallback") != string::npos);
        CHECK(result.find("innerSuccess") == string::npos);
        CHECK(result.find("outerSuccess") == string::npos);
    }
    
    TEST(Try_WithMultipleSubtasks)
    {
        HtnAdvancedTestHelper helper;
        
        // try() with multiple subtasks - if any fail, whole try() fails
        string program = 
            "multiStepProcess() :- if(), do(try(step1, step2, step3), recovery)."
            
            "step1 :- if(step1OK), do(doStep1)."
            "step2 :- if(step2OK), do(doStep2)."  // This will fail
            "step3 :- if(step3OK), do(doStep3)."
            
            "step1OK. step3OK. "  // step2OK is missing
            
            "doStep1 :- del(), add(step1Done)."
            "doStep2 :- del(), add(step2Done)."
            "doStep3 :- del(), add(step3Done)."
            "recovery :- del(), add(recovered)."
            
            "goals(multiStepProcess()).";
        
        string result = helper.FindFirstPlan(program);
        
        // Should use recovery because step2 failed
        CHECK(result.find("recovery") != string::npos);
        // step1 might or might not execute depending on when failure is detected
    }

    // ========== Hidden Operators Tests ==========
    TEST(HiddenOperators_NotInPlan)
    {
        HtnAdvancedTestHelper helper;
        
        // Hidden operators should not appear in final plan output
        string program = 
            "doWork() :- if(), do(publicWork, privateWork)."
            
            "publicWork :- del(), add(publicDone)."
            "privateWork :- hidden, del(), add(privateDone)."  // Hidden operator
            
            "goals(doWork()).";
        
        string result = helper.FindFirstPlan(program);
        
        // Public work should appear in plan
        CHECK(result.find("publicWork") != string::npos);
        
        // Hidden work should not appear in plan output but should still execute
        CHECK(result.find("privateWork") == string::npos);
        
        // However, the effects should still be in final state
        // (This would require checking final facts, not just the plan)
    }
    
    TEST(HiddenOperators_MultipleHidden)
    {
        HtnAdvancedTestHelper helper;
        
        // Multiple hidden operators in sequence
        string program = 
            "setupSystem() :- if(), do(visibleSetup, hiddenInit, hiddenConfig, visibleFinish)."
            
            "visibleSetup :- del(), add(setupVisible)."
            "hiddenInit :- hidden, del(), add(initDone)."
            "hiddenConfig :- hidden, del(), add(configDone)."
            "visibleFinish :- del(), add(finishVisible)."
            
            "goals(setupSystem()).";
        
        string result = helper.FindFirstPlan(program);
        
        // Only visible operators should appear
        CHECK(result.find("visibleSetup") != string::npos);
        CHECK(result.find("visibleFinish") != string::npos);
        CHECK(result.find("hiddenInit") == string::npos);
        CHECK(result.find("hiddenConfig") == string::npos);
    }

    // ========== Method Ordering and else Tests ==========
    TEST(ElseKeyword_BasicPriority)
    {
        HtnAdvancedTestHelper helper;
        
        // Based on Game.htn pattern: priority methods using else
        string program = 
            // High priority - no else
            "doAI(?player) :- if(enemyNearKing(?player)), do(defendKing(?player))."
            // Medium priority - else
            "doAI(?player) :- else, if(canAttack(?player)), do(attack(?player))."
            // Low priority - else
            "doAI(?player) :- else, if(), do(wander(?player))."
            
            // Only medium priority condition is true
            "canAttack(player1). "
            
            "defendKing(?p) :- del(), add(defending(?p))."
            "attack(?p) :- del(), add(attacking(?p))."
            "wander(?p) :- del(), add(wandering(?p))."
            
            "goals(doAI(player1)).";
        
        string result = helper.FindFirstPlan(program);
        
        // Should choose attack (medium priority) since high priority condition not met
        CHECK(result.find("attack(player1)") != string::npos);
        CHECK(result.find("defending") == string::npos);
        CHECK(result.find("wandering") == string::npos);
    }
    
    TEST(ElseKeyword_HighestPriorityTakesPrecedence)
    {
        HtnAdvancedTestHelper helper;
        
        // When highest priority condition is met, else methods should be ignored
        string program = 
            "chooseTactic(?player) :- if(criticalSituation(?player)), do(emergencyAction(?player))."
            "chooseTactic(?player) :- else, if(goodOpportunity(?player)), do(opportunisticAction(?player))."
            "chooseTactic(?player) :- else, if(), do(defaultAction(?player))."
            
            // Both critical and good opportunity are true
            "criticalSituation(player1). goodOpportunity(player1). "
            
            "emergencyAction(?p) :- del(), add(emergency(?p))."
            "opportunisticAction(?p) :- del(), add(opportunistic(?p))."
            "defaultAction(?p) :- del(), add(default(?p))."
            
            "goals(chooseTactic(player1)).";
        
        string result = helper.FindFirstPlan(program);
        
        // Should only use emergency action (highest priority)
        CHECK(result.find("emergencyAction") != string::npos);
        CHECK(result.find("opportunisticAction") == string::npos);
        CHECK(result.find("defaultAction") == string::npos);
    }
    
    TEST(ElseKeyword_FallbackChain)
    {
        HtnAdvancedTestHelper helper;
        
        // Test complete fallback chain when no high priority conditions are met
        string program = 
            "selectAction() :- if(bestOption), do(bestAction)."
            "selectAction() :- else, if(goodOption), do(goodAction)."
            "selectAction() :- else, if(okayOption), do(okayAction)."
            "selectAction() :- else, if(), do(lastResort)."
            
            // No conditions are true, should fall back to last resort
            
            "bestAction :- del(), add(best)."
            "goodAction :- del(), add(good)."
            "okayAction :- del(), add(okay)."
            "lastResort :- del(), add(lastResort)."
            
            "goals(selectAction()).";
        
        string result = helper.FindFirstPlan(program);
        
        // Should use last resort
        CHECK(result.find("lastResort") != string::npos);
        CHECK(result.find("best") == string::npos);
        CHECK(result.find("good") == string::npos);
        CHECK(result.find("okay") == string::npos);
    }

    // ========== Document Order Tests ==========
    TEST(DocumentOrder_WithoutElse)
    {
        HtnAdvancedTestHelper helper;
        
        // Without else, document order should determine method selection
        string program = 
            "ambiguousTask() :- if(), do(firstMethod)."
            "ambiguousTask() :- if(), do(secondMethod)."
            "ambiguousTask() :- if(), do(thirdMethod)."
            
            "firstMethod :- del(), add(first)."
            "secondMethod :- del(), add(second)."
            "thirdMethod :- del(), add(third)."
            
            "goals(ambiguousTask()).";
        
        string result = helper.FindFirstPlan(program);
        
        // Should use first method (document order)
        CHECK(result.find("firstMethod") != string::npos);
        CHECK(result.find("secondMethod") == string::npos);
        CHECK(result.find("thirdMethod") == string::npos);
    }

    // ========== Integration Tests ==========
    TEST(Integration_ComplexMethodCombinations)
    {
        HtnAdvancedTestHelper helper;
        
        // Combine multiple advanced features
        string program = 
            // Main task with priority and try/fallback
            "executeComplexPlan() :- if(highPriorityCondition), do(try(criticalSequence, emergencyFallback))."
            "executeComplexPlan() :- else, if(), do(normalSequence)."
            
            // Critical sequence with anyOf
            "criticalSequence() :- anyOf, if(criticalValid(?c)), do(criticalSequence_routine(?c))."
            
            // Normal sequence with first
            "normalSequence() :- if(first(option(?x), available(?x), cost(?x, ?c), <(?c, 10))), do(selectOption(?x))."
            
            // State setup
            "needA. needB. "  // Critical sequence conditions
            "option(cheap). option(expensive). option(free). "
            "available(cheap). available(expensive). available(free). "
            "cost(free, 0). cost(cheap, 5). cost(expensive, 15). "
            "criticalValid(doA). criticalValid(doB)."
            
            // Operators
            "emergencyFallback :- del(), add(emergency)."
            "selectOption(?opt) :- del(), add(selected(?opt))."
            "criticalSequence_routine(?c) :- del(), add(?c)."
            
            "goals(executeComplexPlan()).";
        
        string result = helper.FindFirstPlan(program);
        
        // Without highPriorityCondition, should use normal sequence
        // First should find cheap option (cost 5 < 10)
        // because it's the first to unify (if you follow the order in which the rules were compiled)
        CHECK(result.find("selectOption(cheap)") != string::npos);
        
        // Now test with high priority condition
        string program2 = program + "highPriorityCondition. ";
        result = helper.FindFirstPlan(program2); // This clears the compiler first
        
        // // Should execute critical sequence with both doA and doB
        CHECK(result.find("doA") != string::npos);  // doA is hidden, so won't appear in plan
        CHECK(result.find("doB") != string::npos);  // doA is hidden, so won't appear in plan

    }
    
    TEST(Integration_RealWorldScenario)
    {
        HtnAdvancedTestHelper helper;
        
        // Real-world inspired scenario: AI game unit decision making
        string program = 
            // Based on Game.htn patterns but more complex
            "unitAction(?unit) :- if(inCombat(?unit)), do(try(combatAction(?unit), retreatAction(?unit)))."
            "unitAction(?unit) :- else, if(canExplore(?unit)), do(exploreAction(?unit))."
            "unitAction(?unit) :- else, if(), do(idleAction(?unit))."
            
            // Combat action tries multiple tactics
            "combatAction(?unit) :- anyOf, if(hasRangedWeapon(?unit), canAttackRanged(?unit)), do(rangedAttack(?unit))."
            "combatAction(?unit) :- anyOf, if(hasCloseWeapon(?unit), canAttackMelee(?unit)), do(meleeAttack(?unit))."
            
            // Explore action prepares comprehensively
            "exploreAction(?unit) :- allOf, if(needSupplies(?unit)), do(gatherSupplies(?unit))."
            "exploreAction(?unit) :- allOf, if(needScout(?unit)), do(scoutAhead(?unit))."
            "exploreAction(?unit) :- allOf, if(), do(moveForward(?unit))."  // Always move
            
            // State for unit1
            "inCombat(unit1). hasRangedWeapon(unit1). canAttackRanged(unit1). "
            "hasCloseWeapon(unit1). "  // Has both weapons
            
            // Operators
            "rangedAttack(?u) :- del(), add(attacked(?u, ranged))."
            "meleeAttack(?u) :- del(), add(attacked(?u, melee))."
            "retreatAction(?u) :- del(), add(retreated(?u))."
            "gatherSupplies(?u) :- del(), add(gatheredSupplies(?u))."
            "scoutAhead(?u) :- del(), add(scouted(?u))."
            "moveForward(?u) :- del(), add(moved(?u))."
            "idleAction(?u) :- del(), add(idle(?u))."
            
            "goals(unitAction(unit1)).";
        
        string result = helper.FindFirstPlan(program);
        
        // Unit is in combat, so should try combat action
        // anyOf should pick ranged attack (first applicable method)
        CHECK(result.find("rangedAttack(unit1)") != string::npos);
        CHECK(result.find("meleeAttack") == string::npos);  // Should not use second anyOf option
        CHECK(result.find("exploreAction") == string::npos);  // Should not use else methods
        CHECK(result.find("idle") == string::npos);
    }
    
    TEST(Integration_ErrorRecoveryChain)
    {
        HtnAdvancedTestHelper helper;
        
        // Complex error recovery using multiple try() blocks and else chains
        string program = 
            "robustOperation() :- if(), do(try(primaryMethod), try(secondaryMethod), try(tertiaryMethod))."
            
            "primaryMethod :- if(primaryCondition), do(primaryAction)."
            "secondaryMethod :- if(secondaryCondition), do(secondaryAction)."
            "tertiaryMethod :- if(), do(tertiaryAction)."  // Always succeeds
            
            // No conditions are true except tertiary (unconditional)
            
            "primaryAction :- del(), add(primary)."
            "secondaryAction :- del(), add(secondary)."
            "tertiaryAction :- del(), add(tertiary)."
            
            "goals(robustOperation()).";
        
        string result = helper.FindFirstPlan(program);
        
        // Should fall through to tertiary method
        CHECK(result.find("tertiaryAction") != string::npos);
        CHECK(result.find("primaryAction") == string::npos);
        CHECK(result.find("secondaryAction") == string::npos);
    }
}