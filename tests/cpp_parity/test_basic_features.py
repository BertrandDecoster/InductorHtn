import pytest
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
from conftest import HtnTestHelper

class TestBasicMethod:
    def test_simple_decomposition(self):
        h = HtnTestHelper()
        program = (
            "travel(?destination) :- if(canWalk(?destination)), do(walk(?destination))."
            "canWalk(park). "
            "walk(?dest) :- del(), add(at(?dest))."
            "goals(travel(park))."
        )
        result = h.find_first_plan(program)
        assert "walk(park)" in result

    def test_multiple_steps(self):
        h = HtnTestHelper()
        program = (
            "cookMeal() :- if(), do(prepareIngredients, cookFood, serveMeal)."
            "prepareIngredients :- del(), add(ingredientsReady)."
            "cookFood :- del(), add(foodCooked)."
            "serveMeal :- del(), add(mealServed)."
            "goals(cookMeal())."
        )
        result = h.find_first_plan(program)
        assert "prepareIngredients" in result
        assert "cookFood" in result
        assert "serveMeal" in result

    def test_conditional_execution(self):
        h = HtnTestHelper()
        program = (
            "makePayment(?amount) :- if(hasMoney(?available), >=(?available, ?amount), is(?remaining, -(?available, ?amount))), do(payAmount(?amount, ?available, ?remaining))."
            "hasMoney(100). "
            "payAmount(?amt, ?available, ?remaining) :- del(hasMoney(?available)), add(hasMoney(?remaining), paid(?amt))."
            "goals(makePayment(25))."
        )
        result = h.find_first_plan(program)
        assert "payAmount(25,100,75)" in result or "payAmount(25, 100, 75)" in result

    def test_failed_precondition(self):
        h = HtnTestHelper()
        program = (
            "buyExpensive() :- if(hasMoney(1000)), do(purchase(expensive))."
            "hasMoney(10). "
            "purchase(?item) :- del(), add(bought(?item))."
            "goals(buyExpensive())."
        )
        result = h.find_first_plan(program)
        assert result == "null"


class TestMultipleMethods:
    def test_first_applicable(self):
        h = HtnTestHelper()
        program = (
            "transport(?dest) :- if(hasCarKey), do(drive(?dest))."
            "transport(?dest) :- if(hasBusPass), do(takeBus(?dest))."
            "transport(?dest) :- if(), do(walk(?dest))."
            "hasCarKey. "
            "drive(?dest) :- del(), add(droveTO(?dest))."
            "takeBus(?dest) :- del(), add(busTo(?dest))."
            "walk(?dest) :- del(), add(walkedTo(?dest))."
            "goals(transport(downtown))."
        )
        result = h.find_first_plan(program)
        assert "drive(downtown)" in result
        assert "takeBus" not in result
        assert "walk" not in result

    def test_second_applicable(self):
        h = HtnTestHelper()
        program = (
            "getFood() :- if(canCook), do(cookMeal)."
            "getFood() :- if(hasDeliveryMenu), do(orderDelivery)."
            "getFood() :- if(), do(goToStore)."
            "hasDeliveryMenu. "
            "cookMeal :- del(), add(cookedMeal)."
            "orderDelivery :- del(), add(deliveryOrdered)."
            "goToStore :- del(), add(wentToStore)."
            "goals(getFood())."
        )
        result = h.find_first_plan(program)
        assert "orderDelivery" in result
        assert "cookMeal" not in result
        assert "goToStore" not in result

    def test_fallback_to_last(self):
        h = HtnTestHelper()
        program = (
            "communicate(?person) :- if(hasPhone(?person)), do(callPerson(?person))."
            "communicate(?person) :- if(hasEmail(?person)), do(emailPerson(?person))."
            "communicate(?person) :- if(), do(visitPerson(?person))."
            "callPerson(?p) :- del(), add(called(?p))."
            "emailPerson(?p) :- del(), add(emailed(?p))."
            "visitPerson(?p) :- del(), add(visited(?p))."
            "goals(communicate(friend))."
        )
        result = h.find_first_plan(program)
        assert "visitPerson(friend)" in result
        assert "callPerson" not in result
        assert "emailPerson" not in result


class TestNestedMethods:
    def test_two_levels(self):
        h = HtnTestHelper()
        program = (
            "completeMission() :- if(), do(prepareForMission, executeMission)."
            "prepareForMission() :- if(), do(gatherSupplies, briefTeam)."
            "gatherSupplies :- del(), add(suppliesGathered)."
            "briefTeam :- del(), add(teamBriefed)."
            "executeMission :- del(), add(missionExecuted)."
            "goals(completeMission())."
        )
        result = h.find_first_plan(program)
        assert "gatherSupplies" in result
        assert "briefTeam" in result
        assert "executeMission" in result

    def test_conditional_nesting(self):
        h = HtnTestHelper()
        program = (
            "handleEmergency() :- if(isFireEmergency), do(handleFire)."
            "handleEmergency() :- if(), do(handleGeneral)."
            "handleFire() :- if(), do(callFireDept, evacuate)."
            "handleGeneral() :- if(), do(callPolice, assessSituation)."
            "isFireEmergency. "
            "callFireDept :- del(), add(fireDeptCalled)."
            "evacuate :- del(), add(evacuated)."
            "callPolice :- del(), add(policeCalled)."
            "assessSituation :- del(), add(situationAssessed)."
            "goals(handleEmergency())."
        )
        result = h.find_first_plan(program)
        assert "callFireDept" in result
        assert "evacuate" in result
        assert "callPolice" not in result
        assert "assessSituation" not in result


class TestVariableBinding:
    def test_through_methods(self):
        h = HtnTestHelper()
        program = (
            "processItem(?item) :- if(needsProcessing(?item)), do(prepareItem(?item), executeProcess(?item))."
            "needsProcessing(document). "
            "prepareItem(?x) :- del(), add(prepared(?x))."
            "executeProcess(?x) :- del(), add(processed(?x))."
            "goals(processItem(document))."
        )
        result = h.find_first_plan(program)
        assert "prepareItem(document)" in result
        assert "executeProcess(document)" in result

    def test_complex_conditions(self):
        h = HtnTestHelper()
        program = (
            "assignTask(?person, ?task) :- if(canPerform(?person, ?task), available(?person)), do(assign(?person, ?task))."
            "canPerform(alice, programming). canPerform(bob, testing). "
            "available(alice). available(charlie). "
            "assign(?p, ?t) :- del(), add(assigned(?p, ?t))."
            "goals(assignTask(alice, programming))."
        )
        result = h.find_first_plan(program)
        assert "assign(alice,programming)" in result or "assign(alice, programming)" in result


class TestPrologIntegration:
    def test_arithmetic_conditions(self):
        h = HtnTestHelper()
        program = (
            "buyItem(?item, ?price) :- if(budget(?available), >=(?available, ?price)), do(purchase(?item, ?price))."
            "budget(100). "
            "purchase(?item, ?cost) :- del(), add(bought(?item, ?cost))."
            "goals(buyItem(book, 25))."
        )
        result = h.find_first_plan(program)
        assert "purchase(book,25)" in result or "purchase(book, 25)" in result

    def test_complex_reasoning(self):
        h = HtnTestHelper()
        program = (
            "planRoute(?from, ?to) :- if(connected(?from, ?to)), do(directTravel(?from, ?to))."
            "planRoute(?from, ?to) :- if(connected(?from, ?via), connected(?via, ?to)), do(travelVia(?from, ?via, ?to))."
            "connected(home, station). connected(station, downtown). connected(station, airport). "
            "directTravel(?a, ?b) :- del(), add(traveledDirect(?a, ?b))."
            "travelVia(?a, ?via, ?b) :- del(), add(traveledVia(?a, ?via, ?b))."
            "goals(planRoute(home, downtown))."
        )
        result = h.find_first_plan(program)
        assert "travelVia(home,station,downtown)" in result or "travelVia(home, station, downtown)" in result


class TestErrorHandling:
    def test_no_applicable_methods(self):
        h = HtnTestHelper()
        program = (
            "impossibleTask() :- if(impossible1), do(action1)."
            "impossibleTask() :- if(impossible2), do(action2)."
            "action1 :- del(), add(did1)."
            "action2 :- del(), add(did2)."
            "goals(impossibleTask())."
        )
        result = h.find_first_plan(program)
        assert result == "null"

    def test_missing_operator(self):
        h = HtnTestHelper()
        program = (
            "doSomething() :- if(), do(nonExistentOperator)."
            "goals(doSomething())."
        )
        result = h.find_first_plan(program)
        assert result == "null"
