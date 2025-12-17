//
//  HtnBasicFeaturesTests.cpp
//  TestLib
//
//  Working HTN features tests based on actual implementation
//  Focuses on features that are known to work (not anyOf/allOf/first/try)
//  Copyright © 2025 Bertrand Decoster. All rights reserved.

#include "FXPlatform/FailFast.h"
#include "FXPlatform/Parser/ParserDebug.h"
#include "FXPlatform/Prolog/HtnGoalResolver.h"
#include "FXPlatform/Prolog/HtnRuleSet.h"
#include "FXPlatform/Prolog/HtnTermFactory.h"
#include "FXPlatform/Htn/HtnPlanner.h"
#include "FXPlatform/Htn/HtnCompiler.h"
#include "FXPlatform/Prolog/PrologQueryCompiler.h"
#include "Logger.h"
#include "Tests/ParserTestBase.h"
#include "UnitTest++/UnitTest++.h"
using namespace Prolog;

SUITE(HtnBasicFeaturesTests)
{
    class HtnBasicTestHelper
    {
    public:
        HtnBasicTestHelper()
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
            CHECK(compiler->Compile(program));
            //lastSolutions = planner->FindAllPlans(factory.get(), compiler->compilerOwnedRuleSet(), compiler->goals());
            auto solution = planner->FindPlan(factory.get(), compiler->compilerOwnedRuleSet(), compiler->goals());
            // Extract first solution if available
            lastSolutions = make_shared<HtnPlanner::SolutionsType>();
            if(solution)
            {
                lastSolutions->push_back(solution);
                return HtnPlanner::ToStringSolution(solution);
            }
            return "null";
        }
        
        string FindAllPlans(const string& program)
        {
            compiler->ClearWithNewRuleSet();  
            CHECK(compiler->Compile(program));
            lastSolutions = planner->FindAllPlans(factory.get(), compiler->compilerOwnedRuleSet(), compiler->goals());
            return HtnPlanner::ToStringSolutions(lastSolutions);
        }
        
        bool ApplySolution(int solutionIndex = 0)
        {
            if (lastSolutions && solutionIndex < lastSolutions->size())
            {
                // Update the state with the final state from the solution
                state = (*lastSolutions)[solutionIndex]->finalState();
                return true;
            }
            return false;
        }
        
        string QueryState(const string& query)
        {
            // Create a Prolog query compiler to directly query the state
            shared_ptr<PrologQueryCompiler> queryCompiler = shared_ptr<PrologQueryCompiler>(new PrologQueryCompiler(factory.get()));
            if (queryCompiler->Compile(query + "."))
            {
                HtnGoalResolver resolver;
                auto queryResult = resolver.ResolveAll(factory.get(), state.get(), queryCompiler->result());
                string result = HtnGoalResolver::ToString(queryResult.get());
                return result;
            }
            return "null";
        }
        
    private:
        shared_ptr<HtnTermFactory> factory;
        shared_ptr<HtnRuleSet> state;
        shared_ptr<HtnPlanner> planner;
        shared_ptr<HtnCompiler> compiler;
        shared_ptr<HtnPlanner::SolutionsType> lastSolutions;
    };

    // ========== Basic HTN Method Tests ==========
    TEST(BasicMethod_SimpleDecomposition)
    {
        HtnBasicTestHelper helper;
        
        // Basic HTN method decomposition
        string program = 
            "travel(?destination) :- if(canWalk(?destination)), do(walk(?destination))."
            
            // State: can walk to park
            "canWalk(park). "
            
            // Operator
            "walk(?dest) :- del(), add(at(?dest))."
            
            "goals(travel(park)).";
        
        string result = helper.FindFirstPlan(program);
        
        // Should execute walk operator
        CHECK(result.find("walk(park)") != string::npos);
    }
    
    TEST(BasicMethod_MultipleSteps)
    {
        HtnBasicTestHelper helper;
        
        // Method with multiple subtasks  
        string program = 
            "cookMeal() :- if(), do(prepareIngredients, cookFood, serveMeal)."
            
            // Operators
            "prepareIngredients :- del(), add(ingredientsReady)."
            "cookFood :- del(), add(foodCooked)."
            "serveMeal :- del(), add(mealServed)."
            
            "goals(cookMeal()).";
        
        string result = helper.FindFirstPlan(program);
        
        // Should execute all three operators in order
        CHECK(result.find("prepareIngredients") != string::npos);
        CHECK(result.find("cookFood") != string::npos);
        CHECK(result.find("serveMeal") != string::npos);
    }
    
    TEST(BasicMethod_ConditionalExecution)
    {
        HtnBasicTestHelper helper;
        
        // Method with preconditions - properly check if we have enough money and calculate remaining amount
        string program = 
            "makePayment(?amount) :- if(hasMoney(?available), >=(?available, ?amount), is(?remaining, -(?available, ?amount))), do(payAmount(?amount, ?available, ?remaining))."
            
            // State
            "hasMoney(100). "
            
            // Operator - properly updates money state by deleting old amount and adding new amount
            "payAmount(?amt, ?available, ?remaining) :- del(hasMoney(?available)), add(hasMoney(?remaining), paid(?amt))."
            
            "goals(makePayment(25)).";  // Pay 25, should have 75 left
        
        string result = helper.FindFirstPlan(program);
        
        // Should execute payment with the available amount and calculated remaining amount
        CHECK(result.find("payAmount(25,100,75)") != string::npos);
        
        // Now apply the plan to update the world state
        CHECK(helper.ApplySolution(0));  // Apply the first (and only) solution
        
        // Verify the money was properly updated to 75
        string moneyQuery = helper.QueryState("hasMoney(75)");
        CHECK(moneyQuery != "null");  // Should find hasMoney(75)
        
        // Verify the payment was recorded
        string paymentQuery = helper.QueryState("paid(25)");
        CHECK(paymentQuery != "null");  // Should find paid(25)
        
        // Verify the old money amount is gone
        string oldMoneyQuery = helper.QueryState("hasMoney(100)");
        CHECK_EQUAL("null", oldMoneyQuery);  // Should not find hasMoney(100)
    }
    
    TEST(BasicMethod_FailedPrecondition)
    {
        HtnBasicTestHelper helper;
        
        // Method with failing precondition
        string program = 
            "buyExpensive() :- if(hasMoney(1000)), do(purchase(expensive))."
            
            // Not enough money
            "hasMoney(10). "
            
            // Operator
            "purchase(?item) :- del(), add(bought(?item))."
            
            "goals(buyExpensive()).";
        
        string result = helper.FindFirstPlan(program);
        
        // Should fail due to unmet precondition
        CHECK_EQUAL("null", result);
    }

    // ========== Multiple Method Tests ==========
    TEST(MultipleMethods_FirstApplicable)
    {
        HtnBasicTestHelper helper;
        
        // Multiple methods, first one applicable
        string program = 
            "transport(?dest) :- if(hasCarKey), do(drive(?dest))."
            "transport(?dest) :- if(hasBusPass), do(takeBus(?dest))."
            "transport(?dest) :- if(), do(walk(?dest))."
            
            // State: have car key
            "hasCarKey. "
            
            // Operators
            "drive(?dest) :- del(), add(droveTO(?dest))."
            "takeBus(?dest) :- del(), add(busTo(?dest))."
            "walk(?dest) :- del(), add(walkedTo(?dest))."
            
            "goals(transport(downtown)).";
        
        string result = helper.FindFirstPlan(program);
        
        // Should use first applicable method (drive)
        CHECK(result.find("drive(downtown)") != string::npos);
        CHECK(result.find("takeBus") == string::npos);
        CHECK(result.find("walk") == string::npos);
    }
    
    TEST(MultipleMethods_SecondApplicable)
    {
        HtnBasicTestHelper helper;
        
        // Multiple methods, second one applicable
        string program = 
            "getFood() :- if(canCook), do(cookMeal)."
            "getFood() :- if(hasDeliveryMenu), do(orderDelivery)."
            "getFood() :- if(), do(goToStore)."
            
            // State: have delivery menu but can't cook
            "hasDeliveryMenu. "
            
            // Operators
            "cookMeal :- del(), add(cookedMeal)."
            "orderDelivery :- del(), add(deliveryOrdered)."
            "goToStore :- del(), add(wentToStore)."
            
            "goals(getFood()).";
        
        string result = helper.FindFirstPlan(program);
        
        // Should use second applicable method (order delivery)
        CHECK(result.find("orderDelivery") != string::npos);
        CHECK(result.find("cookMeal") == string::npos);
        CHECK(result.find("goToStore") == string::npos);
    }
    
    TEST(MultipleMethods_FallbackToLast)
    {
        HtnBasicTestHelper helper;
        
        // Multiple methods, fall back to last one
        string program = 
            "communicate(?person) :- if(hasPhone(?person)), do(callPerson(?person))."
            "communicate(?person) :- if(hasEmail(?person)), do(emailPerson(?person))."
            "communicate(?person) :- if(), do(visitPerson(?person))."
            
            // No phone or email available
            
            // Operators
            "callPerson(?p) :- del(), add(called(?p))."
            "emailPerson(?p) :- del(), add(emailed(?p))."
            "visitPerson(?p) :- del(), add(visited(?p))."
            
            "goals(communicate(friend)).";
        
        string result = helper.FindFirstPlan(program);
        
        // Should fall back to last method (visit)
        CHECK(result.find("visitPerson(friend)") != string::npos);
        CHECK(result.find("callPerson") == string::npos);
        CHECK(result.find("emailPerson") == string::npos);
    }

    // ========== Nested Method Tests ==========
    TEST(NestedMethods_TwoLevels)
    {
        HtnBasicTestHelper helper;
        
        // Method that calls another method
        string program = 
            "completeMission() :- if(), do(prepareForMission, executeMission)."
            "prepareForMission() :- if(), do(gatherSupplies, briefTeam)."
            
            // Operators
            "gatherSupplies :- del(), add(suppliesGathered)."
            "briefTeam :- del(), add(teamBriefed)."
            "executeMission :- del(), add(missionExecuted)."
            
            "goals(completeMission()).";
        
        string result = helper.FindFirstPlan(program);
        
        // Should execute all operators from nested methods
        CHECK(result.find("gatherSupplies") != string::npos);
        CHECK(result.find("briefTeam") != string::npos);
        CHECK(result.find("executeMission") != string::npos);
    }
    
    TEST(NestedMethods_ConditionalNesting)
    {
        HtnBasicTestHelper helper;
        
        // Nested method with conditions
        string program = 
            "handleEmergency() :- if(isFireEmergency), do(handleFire)."
            "handleEmergency() :- if(), do(handleGeneral)."
            "handleFire() :- if(), do(callFireDept, evacuate)."
            "handleGeneral() :- if(), do(callPolice, assessSituation)."
            
            // Fire emergency
            "isFireEmergency. "
            
            // Operators
            "callFireDept :- del(), add(fireDeptCalled)."
            "evacuate :- del(), add(evacuated)."
            "callPolice :- del(), add(policeCalled)."
            "assessSituation :- del(), add(situationAssessed)."
            
            "goals(handleEmergency()).";
        
        string result = helper.FindFirstPlan(program);
        
        // Should handle fire emergency
        CHECK(result.find("callFireDept") != string::npos);
        CHECK(result.find("evacuate") != string::npos);
        CHECK(result.find("callPolice") == string::npos);
        CHECK(result.find("assessSituation") == string::npos);
    }

    // ========== Variable Binding Tests ==========
    TEST(VariableBinding_ThroughMethods)
    {
        HtnBasicTestHelper helper;
        
        // Variables passed through method hierarchy
        string program = 
            "processItem(?item) :- if(needsProcessing(?item)), do(prepareItem(?item), executeProcess(?item))."
            
            // State
            "needsProcessing(document). "
            
            // Operators
            "prepareItem(?x) :- del(), add(prepared(?x))."
            "executeProcess(?x) :- del(), add(processed(?x))."
            
            "goals(processItem(document)).";
        
        string result = helper.FindFirstPlan(program);
        
        // Should bind document through all operations
        CHECK(result.find("prepareItem(document)") != string::npos);
        CHECK(result.find("executeProcess(document)") != string::npos);
    }
    
    TEST(VariableBinding_ComplexConditions)
    {
        HtnBasicTestHelper helper;
        
        // Complex variable binding in conditions
        string program = 
            "assignTask(?person, ?task) :- if(canPerform(?person, ?task), available(?person)), do(assign(?person, ?task))."
            
            // State
            "canPerform(alice, programming). canPerform(bob, testing). "
            "available(alice). available(charlie). "
            
            // Operator
            "assign(?p, ?t) :- del(), add(assigned(?p, ?t))."
            
            "goals(assignTask(alice, programming)).";
        
        string result = helper.FindFirstPlan(program);
        
        // Should successfully assign alice to programming
        CHECK(result.find("assign(alice,programming)") != string::npos);
    }

    // ========== Integration with Prolog Tests ==========
    TEST(PrologIntegration_ArithmeticConditions)
    {
        HtnBasicTestHelper helper;
        
        // HTN method with arithmetic conditions
        string program = 
            "buyItem(?item, ?price) :- if(budget(?available), >=(?available, ?price)), do(purchase(?item, ?price))."
            
            // State
            "budget(100). "
            
            // Operator
            "purchase(?item, ?cost) :- del(), add(bought(?item, ?cost))."
            
            "goals(buyItem(book, 25)).";
        
        string result = helper.FindFirstPlan(program);
        
        // Should successfully purchase book
        CHECK(result.find("purchase(book,25)") != string::npos);
    }
    
    TEST(PrologIntegration_ComplexReasoning)
    {
        HtnBasicTestHelper helper;
        
        // HTN with complex Prolog reasoning
        string program = 
            "planRoute(?from, ?to) :- if(connected(?from, ?to)), do(directTravel(?from, ?to))."
            "planRoute(?from, ?to) :- if(connected(?from, ?via), connected(?via, ?to)), do(travelVia(?from, ?via, ?to))."
            
            // Route network
            "connected(home, station). connected(station, downtown). connected(station, airport). "
            
            // Operators
            "directTravel(?a, ?b) :- del(), add(traveledDirect(?a, ?b))."
            "travelVia(?a, ?via, ?b) :- del(), add(traveledVia(?a, ?via, ?b))."
            
            "goals(planRoute(home, downtown)).";
        
        string result = helper.FindFirstPlan(program);
        
        // Should find route via station
        CHECK(result.find("travelVia(home,station,downtown)") != string::npos);
    }

    // ========== Error Handling Tests ==========
    TEST(ErrorHandling_NoApplicableMethods)
    {
        HtnBasicTestHelper helper;
        
        // No methods can execute
        string program = 
            "impossibleTask() :- if(impossible1), do(action1)."
            "impossibleTask() :- if(impossible2), do(action2)."
            
            // No conditions are true
            
            // Operators
            "action1 :- del(), add(did1)."
            "action2 :- del(), add(did2)."
            
            "goals(impossibleTask()).";
        
        string result = helper.FindFirstPlan(program);
        
        // Should fail
        CHECK_EQUAL("null", result);
    }
    
    TEST(ErrorHandling_MissingOperator)
    {
        HtnBasicTestHelper helper;
        
        // Method refers to non-existent operator
        string program = 
            "doSomething() :- if(), do(nonExistentOperator)."
            
            "goals(doSomething()).";
        
        string result = helper.FindFirstPlan(program);
        
        // Should fail due to missing operator
        CHECK_EQUAL("null", result);
    }

    // ========== Advanced Features ==========
    // NOTE: Advanced HTN features (anyOf, allOf, first(), try(), else) ARE implemented
    // and working. See HtnAdvancedFeaturesTests.cpp for comprehensive tests of these features.
}