//
//  HtnPlannerTests_Integration.cpp
//  TestLib
//
//  Created by Eric Zinda on 1/8/19.
//  Copyright © 2019 Eric Zinda. All rights reserved.
//
//  Real-world scenarios and resource management tests.
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
    TEST(PlannerShopTransportationScenarioTest)
    {
        shared_ptr<HtnTermFactory> factory = shared_ptr<HtnTermFactory>(new HtnTermFactory());
        shared_ptr<HtnRuleSet> state = shared_ptr<HtnRuleSet>(new HtnRuleSet());
        shared_ptr<HtnPlanner> planner = shared_ptr<HtnPlanner>(new HtnPlanner());
        shared_ptr<HtnCompiler> compiler;
        shared_ptr<HtnPlanner::SolutionsType> result;
        string finalFacts;
        string finalFacts2;
        string finalPlan;
        string finalPlan2;
        string example;
        string testState;
        string sharedState;
        string goals;

//                SetTraceFilter((int) SystemTraceType::Solver | (int) SystemTraceType::Planner, TraceDetail::Diagnostic);
//                SetTraceLevelOfDetail(TraceDetail::Diagnostic);

        // Original(ish) data from: http://www.cs.umd.edu/projects/shop/description.html
        //        ";;; To have enough money for a taxi, we need at least $1.50 + $1 for each mile to be traveled.\r\n" +
        //        "(:- (have-taxi-fare ?dist) ((have-cash ?m) (eval (>= ?m (+ 1.5 ?dist)))))\r\n" +
        //        ";;; We are within walking distance of our destination if the weather is good and the distance is 3 miles, or if the weather is bad and the distance is 1/2 mile.\r\n" +
        //        "(:- (walking-distance ?u ?v) ((weather-is good) (distance ?u ?v ?w) (eval (=< ?w 3))) ((distance ?u ?v ?w) (eval (=< ?w 0.5))))\r\n"  +
        //        "(:operator (!hail ?vehicle ?location) ( (at-taxi-stand ?vehicle ?location) ) ((at ?vehicle ?location)) )                       ;This is the operator for hailing a vehicle. It brings the vehicle to our current location.\r\n" +
        //        "(:operator (!wait-for ?bus ?location) () ((at ?bus ?location)))                            ;This is the operator for waiting for a bus. It brings the bus to our current location.\r\n" +
        //        "(:operator (!ride ?vehicle ?a ?b) ((at ?a) (at ?vehicle ?a)) ((at ?b) (at ?vehicle ?b)))   ;This is the operator for riding a vehicle to a location. It puts both us and the vehicle at that location.\r\n" +
        //        "(:operator (!set-cash ?old ?new) ((have-cash ?old)) ((have-cash ?new)))                    ;This is the operator for changing how much cash we have left.\r\n" +
        //        "(:operator (!walk ?here ?there) ((at ?here)) ((at ?there)))                                ;This is the operator for walking to a location. It puts us at that location.\r\n" +
        //        "(:method (pay-driver ?fare) ((have-cash ?m) (eval (>= ?m ?fare))) ((!set-cash ?m (- ?m ?fare)))) ;If we have enough money to pay the taxi driver, then we can pay the driver by subtracting the taxi fare from our cash-on-hand.\r\n" +
        //        "(:method (travel-to ?q) ((at ?p) (walking-distance ?p ?q)) ((!walk ?p ?q)))                ;If q is within walking distance, then one way to travel there is to walk there directly.\r\n" +
        //        "(:method (travel-to ?y) ((at ?x) (at-taxi-stand ?t ?x) (distance ?x ?y ?d) (have-taxi-fare ?d)) ((!hail ?t ?x) (!ride ?t ?x ?y) (pay-driver (+ 1.50 ?d))))" +
        //        "(:facts ((have-cash 50) (at home) (at-taxi-stand taxi1 home) (distance home work 5)) )\r\n" +
        //        "(:goals ((travel-to work)) )\r\n";

        // The fact that :first is used means that the prover follows all branches and returns them
        example = string() +
        // Axioms
        "have-taxi-fare(?distance) :- have-cash(?m), >=(?m, +(1.5, ?distance)). \r\n" +
        "walking-distance(?u,?v) :- weather-is(good), distance(?u,?v,?w), =<(?w, 3). \r\n"+
        "walking-distance(?u,?v) :- distance(?u,?v,?w), =<(?w, 0.5). \r\n"+
        // Methods
        "pay-driver(?fare) :- if(have-cash(?m), >=(?m, ?fare)), do(set-cash(?m, -(?m,?fare))). \r\n"+
        "travel-to(?q) :- if(at(?p), walking-distance(?p, ?q)), do(walk(?p, ?q)). \r\n"+
        // Use first() so we only hail one taxi
        "travel-to(?y) :- if(first(at(?x), at-taxi-stand(?t, ?x), distance(?x, ?y, ?d), have-taxi-fare(?d))), do(hail(?t,?x), ride(?t, ?x, ?y), pay-driver(+(1.50, ?d))). \r\n"+
        "travel-to(?y) :- if(at(?x), bus-route(?bus, ?x, ?y)), do(wait-for(?bus, ?x), pay-driver(1.00), ride(?bus, ?x, ?y)). \r\n"+
        // Operators
        "hail(?vehicle, ?location) :- del(), add(at(?vehicle, ?location)). \r\n"+
        "wait-for(?bus, ?location) :- del(), add(at(?bus, ?location)). \r\n"+
        "ride(?vehicle, ?a, ?b) :- del(at(?a), at(?vehicle, ?a)), add(at(?b), at(?vehicle, ?b)). \r\n"+
        "set-cash(?old, ?new) :- del(have-cash(?old)), add(have-cash(?new)). \r\n"+
        "walk(?here, ?there) :- del(at(?here)), add(at(?there)). \r\n"+
        "";

        // State for all tests
        sharedState = string() +
        "distance(downtown, park, 2). \r\n"+
        "distance(downtown, uptown, 8). \r\n"+
        "distance(downtown, suburb, 12). \r\n"+
        "at-taxi-stand(taxi1, downtown). \r\n"+
        "at-taxi-stand(taxi2, downtown). \r\n"+
        "bus-route(bus1, downtown, park). \r\n"+
        "bus-route(bus2, downtown, uptown). \r\n"+
        "bus-route(bus3, downtown, suburb). \r\n"+
        "";

        // **** Next Test
        state = shared_ptr<HtnRuleSet>(new HtnRuleSet()); planner->ClearAll();
        compiler = shared_ptr<HtnCompiler>(new HtnCompiler(factory.get(), state.get(), planner.get()));

        // State for this test
        testState = string() +
        "at(downtown). \r\n" +
        "weather-is(good). \r\n" +
        "have-cash(12). \r\n" +
        "";

        // Goal for this test
        goals =  string() +
        "goals(travel-to(suburb)).\r\n" +
        "";

        CHECK(compiler->Compile(example + sharedState + testState + goals));
        result = planner->FindAllPlans(factory.get(), state, compiler->goals());
        CHECK(result->size() == 1);
        finalFacts = (*result)[0]->second->ToStringFacts();
        finalPlan = HtnTerm::ToString((*result)[0]->first);
        CHECK_EQUAL(finalPlan, "(wait-for(bus3,downtown), set-cash(12,11.000000000), ride(bus3,downtown,suburb))");
        CHECK_EQUAL(finalFacts,  "distance(downtown,park,2) => ,distance(downtown,uptown,8) => ,distance(downtown,suburb,12) => ,at-taxi-stand(taxi1,downtown) => ,at-taxi-stand(taxi2,downtown) => ,bus-route(bus1,downtown,park) => ,bus-route(bus2,downtown,uptown) => ,bus-route(bus3,downtown,suburb) => ,weather-is(good) => ,have-cash(11.000000000) => ,at(suburb) => ,at(bus3,suburb) => ");

        // **** Next Test
        state = shared_ptr<HtnRuleSet>(new HtnRuleSet()); planner->ClearAll();
        compiler = shared_ptr<HtnCompiler>(new HtnCompiler(factory.get(), state.get(), planner.get()));

        // State for this test
        testState = string() +
        "at(downtown). \r\n" +
        "weather-is(good). \r\n" +
        "have-cash(0). \r\n" +
        "";

        // Goal for this test
        goals =  string() +
        "goals(travel-to(park)).\r\n" +
        "";

        CHECK(compiler->Compile(example + sharedState + testState + goals));
        result = planner->FindAllPlans(factory.get(), state, compiler->goals());
        CHECK(result->size() == 1);
        finalFacts = (*result)[0]->second->ToStringFacts();
        finalPlan = HtnTerm::ToString((*result)[0]->first);
        CHECK_EQUAL(finalPlan, "(walk(downtown,park))");
        CHECK_EQUAL(finalFacts,  "distance(downtown,park,2) => ,distance(downtown,uptown,8) => ,distance(downtown,suburb,12) => ,at-taxi-stand(taxi1,downtown) => ,at-taxi-stand(taxi2,downtown) => ,bus-route(bus1,downtown,park) => ,bus-route(bus2,downtown,uptown) => ,bus-route(bus3,downtown,suburb) => ,weather-is(good) => ,have-cash(0) => ,at(park) => ");



        // **** Next Test
        state = shared_ptr<HtnRuleSet>(new HtnRuleSet()); planner->ClearAll();
        compiler = shared_ptr<HtnCompiler>(new HtnCompiler(factory.get(), state.get(), planner.get()));

        // State for this test
        testState = string() +
        "at(downtown). \r\n" +
        "have-cash(0). \r\n" +
        "";

        // Goal for this test
        goals =  string() +
        "goals(travel-to(park)).\r\n" +
        "";

        CHECK(compiler->Compile(example + sharedState + testState + goals));
        result = planner->FindAllPlans(factory.get(), state, compiler->goals());
        CHECK(result == nullptr); // can't afford a taxi and too far to walk


        // **** Next Test
        state = shared_ptr<HtnRuleSet>(new HtnRuleSet()); planner->ClearAll();
        compiler = shared_ptr<HtnCompiler>(new HtnCompiler(factory.get(), state.get(), planner.get()));

        // State for this test
        testState = string() +
        "at(downtown). \r\n" +
        "weather-is(good). \r\n" +
        "have-cash(12). \r\n" +
        "";

        // Goal for this test
        goals =  string() +
        "goals(travel-to(park)).\r\n" +
        "";

        CHECK(compiler->Compile(example + sharedState + testState + goals));
        result = planner->FindAllPlans(factory.get(), state, compiler->goals());
        CHECK(result->size() == 3);
        finalFacts = (*result)[0]->second->ToStringFacts();
        finalPlan = HtnTerm::ToString((*result)[0]->first);
        finalFacts2 = (*result)[1]->second->ToStringFacts();
        finalPlan2 = HtnTerm::ToString((*result)[1]->first);
        string finalFacts3 = (*result)[2]->second->ToStringFacts();
        string finalPlan3 = HtnTerm::ToString((*result)[2]->first);
        CHECK_EQUAL(finalPlan, "(walk(downtown,park))");
        CHECK_EQUAL(finalFacts,  "distance(downtown,park,2) => ,distance(downtown,uptown,8) => ,distance(downtown,suburb,12) => ,at-taxi-stand(taxi1,downtown) => ,at-taxi-stand(taxi2,downtown) => ,bus-route(bus1,downtown,park) => ,bus-route(bus2,downtown,uptown) => ,bus-route(bus3,downtown,suburb) => ,weather-is(good) => ,have-cash(12) => ,at(park) => ");
        CHECK(finalPlan2 == "(hail(taxi1,downtown), ride(taxi1,downtown,park), set-cash(12,8.500000000))");
        CHECK(finalFacts2 == "distance(downtown,park,2) => ,distance(downtown,uptown,8) => ,distance(downtown,suburb,12) => ,at-taxi-stand(taxi1,downtown) => ,at-taxi-stand(taxi2,downtown) => ,bus-route(bus1,downtown,park) => ,bus-route(bus2,downtown,uptown) => ,bus-route(bus3,downtown,suburb) => ,weather-is(good) => ,at(park) => ,at(taxi1,park) => ,have-cash(8.500000000) => ");
        CHECK(finalPlan3 == "(wait-for(bus1,downtown), set-cash(12,11.000000000), ride(bus1,downtown,park))");
        CHECK(finalFacts3 == "distance(downtown,park,2) => ,distance(downtown,uptown,8) => ,distance(downtown,suburb,12) => ,at-taxi-stand(taxi1,downtown) => ,at-taxi-stand(taxi2,downtown) => ,bus-route(bus1,downtown,park) => ,bus-route(bus2,downtown,uptown) => ,bus-route(bus3,downtown,suburb) => ,weather-is(good) => ,have-cash(11.000000000) => ,at(park) => ,at(bus1,park) => ");


        // **** Next Test
        state = shared_ptr<HtnRuleSet>(new HtnRuleSet()); planner->ClearAll();
        compiler = shared_ptr<HtnCompiler>(new HtnCompiler(factory.get(), state.get(), planner.get()));

        // State for this test
        testState = string() +
        "at(downtown). \r\n" +
        "weather-is(good). \r\n" +
        "have-cash(80). \r\n" +
        "";

        // Goal for this test
        goals =  string() +
        "goals(travel-to(park)).\r\n" +
        "";

        CHECK(compiler->Compile(example + sharedState + testState + goals));
        result = planner->FindAllPlans(factory.get(), state, compiler->goals());
        CHECK(result->size() == 3);
        finalFacts = (*result)[0]->second->ToStringFacts();
        finalPlan = HtnTerm::ToString((*result)[0]->first);
        finalFacts2 = (*result)[1]->second->ToStringFacts();
        finalPlan2 = HtnTerm::ToString((*result)[1]->first);
        finalFacts3 = (*result)[2]->second->ToStringFacts();
        finalPlan3 = HtnTerm::ToString((*result)[2]->first);
        CHECK_EQUAL(finalPlan, "(walk(downtown,park))");
        CHECK_EQUAL(finalFacts,  "distance(downtown,park,2) => ,distance(downtown,uptown,8) => ,distance(downtown,suburb,12) => ,at-taxi-stand(taxi1,downtown) => ,at-taxi-stand(taxi2,downtown) => ,bus-route(bus1,downtown,park) => ,bus-route(bus2,downtown,uptown) => ,bus-route(bus3,downtown,suburb) => ,weather-is(good) => ,have-cash(80) => ,at(park) => ");
        CHECK(finalPlan2 == "(hail(taxi1,downtown), ride(taxi1,downtown,park), set-cash(80,76.500000000))");
        CHECK(finalFacts2 == "distance(downtown,park,2) => ,distance(downtown,uptown,8) => ,distance(downtown,suburb,12) => ,at-taxi-stand(taxi1,downtown) => ,at-taxi-stand(taxi2,downtown) => ,bus-route(bus1,downtown,park) => ,bus-route(bus2,downtown,uptown) => ,bus-route(bus3,downtown,suburb) => ,weather-is(good) => ,at(park) => ,at(taxi1,park) => ,have-cash(76.500000000) => ");
        CHECK(finalPlan3 == "(wait-for(bus1,downtown), set-cash(80,79.000000000), ride(bus1,downtown,park))"  );
        CHECK(finalFacts3 == "distance(downtown,park,2) => ,distance(downtown,uptown,8) => ,distance(downtown,suburb,12) => ,at-taxi-stand(taxi1,downtown) => ,at-taxi-stand(taxi2,downtown) => ,bus-route(bus1,downtown,park) => ,bus-route(bus2,downtown,uptown) => ,bus-route(bus3,downtown,suburb) => ,weather-is(good) => ,have-cash(79.000000000) => ,at(park) => ,at(bus1,park) => ");



        // **** Next Test
        state = shared_ptr<HtnRuleSet>(new HtnRuleSet()); planner->ClearAll();
        compiler = shared_ptr<HtnCompiler>(new HtnCompiler(factory.get(), state.get(), planner.get()));

        // State for this test
        testState = string() +
        "at(downtown). \r\n" +
        "weather-is(good). \r\n" +
        "have-cash(0). \r\n" +
        "";

        // Goal for this test
        goals =  string() +
        "goals(travel-to(uptown)).\r\n" +
        "";

        CHECK(compiler->Compile(example + sharedState + testState + goals));
        result = planner->FindAllPlans(factory.get(), state, compiler->goals());
        CHECK(result == nullptr); // can't afford a taxi or bus, and too far to walk


        // **** Next Test
        state = shared_ptr<HtnRuleSet>(new HtnRuleSet()); planner->ClearAll();
        compiler = shared_ptr<HtnCompiler>(new HtnCompiler(factory.get(), state.get(), planner.get()));

        // State for this test
        testState = string() +
        "at(downtown). \r\n" +
        "weather-is(good). \r\n" +
        "have-cash(12). \r\n" +
        "";

        // Goal for this test
        goals =  string() +
        "goals(travel-to(uptown)).\r\n" +
        "";

        CHECK(compiler->Compile(example + sharedState + testState + goals));
        result = planner->FindAllPlans(factory.get(), state, compiler->goals());
        CHECK(result->size() == 2);
        finalFacts = (*result)[0]->second->ToStringFacts();
        finalPlan = HtnTerm::ToString((*result)[0]->first);
        finalFacts2 = (*result)[1]->second->ToStringFacts();
        finalPlan2 = HtnTerm::ToString((*result)[1]->first);
        CHECK_EQUAL(finalPlan, "(hail(taxi1,downtown), ride(taxi1,downtown,uptown), set-cash(12,2.500000000))");
        CHECK_EQUAL(finalFacts,  "distance(downtown,park,2) => ,distance(downtown,uptown,8) => ,distance(downtown,suburb,12) => ,at-taxi-stand(taxi1,downtown) => ,at-taxi-stand(taxi2,downtown) => ,bus-route(bus1,downtown,park) => ,bus-route(bus2,downtown,uptown) => ,bus-route(bus3,downtown,suburb) => ,weather-is(good) => ,at(uptown) => ,at(taxi1,uptown) => ,have-cash(2.500000000) => ");
        CHECK(finalPlan2 == "(wait-for(bus2,downtown), set-cash(12,11.000000000), ride(bus2,downtown,uptown))");
        CHECK(finalFacts2 == "distance(downtown,park,2) => ,distance(downtown,uptown,8) => ,distance(downtown,suburb,12) => ,at-taxi-stand(taxi1,downtown) => ,at-taxi-stand(taxi2,downtown) => ,bus-route(bus1,downtown,park) => ,bus-route(bus2,downtown,uptown) => ,bus-route(bus3,downtown,suburb) => ,weather-is(good) => ,have-cash(11.000000000) => ,at(uptown) => ,at(bus2,uptown) => ");
    }

    TEST(HtnPlannerMemoryBudgetTest)
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

//        SetTraceFilter((int) SystemTraceType::Planner | (int)SystemTraceType::Solver,  TraceDetail::Diagnostic);

        // State true for all tests
        sharedState = string() +
        "";

        // Create a rule that allocates a BUNCH of memory and surely blows out the budget
        // Ensure that all the operators returned up to that point get returned and others don't
        compiler->ClearWithNewRuleSet();
        testState = string() +
        // Generates a sequence of numbers
        "gen(?Cur, ?Top, ?Cur) :- =<(?Cur, ?Top).\r\n" +
        "gen(?Cur, ?Top, ?Next):- =<(?Cur, ?Top), is(?Cur1, +(?Cur, 1)), gen(?Cur1, ?Top, ?Next).\r\n" +
        "blowBudget() :- if(gen(0, 10000,?S)), do(trace(SHOULDNEVERHAPPEN)).\r\n" +
        "trace(?Value) :- del(), add(?Value). \r\n" +
        "";
        goals = string() +
        "goals(trace(Test), blowBudget()).\r\n" +
        "";
        CHECK(compiler->Compile(sharedState + testState + goals));
        result = planner->FindAllPlans(factory.get(), compiler->compilerOwnedRuleSet(), compiler->goals(), 5000);
        CHECK(factory->outOfMemory());
        finalPlan = HtnPlanner::ToStringSolutions(result);
        CHECK_EQUAL(finalPlan, "[ { (trace(Test)) } ]");
        finalFacts = HtnPlanner::ToStringFacts(result);
        CHECK_EQUAL(finalFacts,  "[ { Test =>  } ]");

        // Goals will return 3 solutions but the second one fails partway through, make sure we get all of the first and part of the second
        // solutions
        factory->outOfMemory(false);
        compiler->ClearWithNewRuleSet();
        testState = string() +
        // Generates a sequence of numbers
        "BlowBudget(Green). Color(Blue). Color(Green). Color(Red).\r\n" +
        "gen(?Cur, ?Top, ?Cur) :- =<(?Cur, ?Top).\r\n" +
        "gen(?Cur, ?Top, ?Next):- =<(?Cur, ?Top), is(?Cur1, +(?Cur, 1)), gen(?Cur1, ?Top, ?Next).\r\n" +
        "blowBudget() :- if(gen(0, 10000,?S)), do(trace(SHOULDNEVERHAPPEN)).\r\n" +
        "trace(?Value) :- del(), add(item(?Value)). \r\n" +
        "trace2(?Value, ?Value2) :- del(), add(item(?Value, ?Value2)). \r\n" +
        "sizeColors() :- if(Color(?X)), do(trace(?X), outcome(?X)).\r\n" +
        "outcome(?X) :- if(BlowBudget(?X)), do(blowBudget()).\r\n" +
        "outcome(?X) :- if(), do(trace2(SUCCESS, ?X)).\r\n" +
        "";
        goals = string() +
        "goals(trace(Test), sizeColors()).\r\n" +
        "";
        CHECK(compiler->Compile(sharedState + testState + goals));
        result = planner->FindAllPlans(factory.get(), compiler->compilerOwnedRuleSet(), compiler->goals(), 200000);
        CHECK(factory->outOfMemory());
        finalPlan = HtnPlanner::ToStringSolutions(result);
        CHECK_EQUAL(finalPlan, "[ { (trace(Test), trace(Blue), trace2(SUCCESS,Blue)) } { (trace(Test), trace(Green)) } ]");
        finalFacts = HtnPlanner::ToStringFacts(result);
        CHECK_EQUAL(finalFacts,  "[ { BlowBudget(Green) => ,Color(Blue) => ,Color(Green) => ,Color(Red) => ,item(Test) => ,item(Blue) => ,item(SUCCESS,Blue) =>  } { BlowBudget(Green) => ,Color(Blue) => ,Color(Green) => ,Color(Red) => ,item(Test) => ,item(Green) =>  } ]");
    }
}
