import pytest
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
from conftest import HtnTestHelper


class TestAnyOf:
    def test_basic_usage(self):
        h = HtnTestHelper()
        program = (
            "attackEnemies() :- anyOf, if(isInRange(?unit)), do(attack(?unit))."
            "isInRange(enemy1). isInRange(enemy2). isInRange(enemy3). "
            "attack(?target) :- del(), add(attacked(?target))."
            "goals(attackEnemies())."
        )
        result = h.find_first_plan(program)
        assert "attack" in result
        assert "enemy" in result

    def test_multiple_variable_bindings(self):
        h = HtnTestHelper()
        program = (
            "collectItems() :- anyOf, if(availableItem(?item)), do(collect(?item))."
            "availableItem(gold). availableItem(food). availableItem(wood). "
            "collect(gold) :- del(), add(has(gold))."
            "collect(food) :- del(), add(cantCollectFood)."
            "collect(wood) :- del(), add(has(wood))."
            "goals(collectItems())."
        )
        result = h.find_first_plan(program)
        assert "collect" in result

    def test_no_valid_bindings(self):
        h = HtnTestHelper()
        program = (
            "doNothing() :- anyOf, if(nonExistentCondition(?x)), do(action(?x))."
            "action(?x) :- del(), add(did(?x))."
            "goals(doNothing())."
        )
        result = h.find_first_plan(program)
        assert result == "null"


class TestAllOf:
    def test_basic_usage(self):
        h = HtnTestHelper()
        program = (
            "repairAllDamaged() :- allOf, if(isDamaged(?unit)), do(repair(?unit))."
            "isDamaged(unit1). isDamaged(unit2). isDamaged(unit3). "
            "repair(?target) :- del(isDamaged(?target)), add(repaired(?target))."
            "goals(repairAllDamaged())."
        )
        result = h.find_first_plan(program)
        assert "repair(unit1)" in result
        assert "repair(unit2)" in result
        assert "repair(unit3)" in result

    def test_with_variable_bindings(self):
        h = HtnTestHelper()
        program = (
            "healWounded() :- allOf, if(isWounded(?soldier)), do(heal(?soldier))."
            "isWounded(soldier1). isWounded(soldier3). "
            "heal(?s) :- del(isWounded(?s)), add(healthy(?s))."
            "goals(healWounded())."
        )
        result = h.find_first_plan(program)
        assert "heal(soldier1)" in result
        assert "heal(soldier3)" in result
        assert "heal(soldier2)" not in result

    def test_no_matching_bindings(self):
        h = HtnTestHelper()
        program = (
            "cleanupOptional() :- allOf, if(needsCleanup(?item)), do(cleanup(?item))."
            "cleanup(?x) :- del(), add(cleaned(?x))."
            "goals(cleanupOptional())."
        )
        result = h.find_first_plan(program)
        assert result == "null"


class TestFirst:
    def test_basic_usage(self):
        h = HtnTestHelper()
        program = (
            "findNearestTaxi() :- if(first(at(?location), taxiAt(?taxi, ?location), distance(?location, ?dist))), do(hail(?taxi, ?location))."
            "taxiAt(taxi1, downtown). taxiAt(taxi2, uptown). taxiAt(taxi3, suburb). "
            "distance(downtown, 1). distance(uptown, 3). distance(suburb, 5). "
            "at(downtown). at(uptown). at(suburb). "
            "hail(?taxi, ?loc) :- del(), add(hired(?taxi, ?loc))."
            "goals(findNearestTaxi())."
        )
        result = h.find_first_plan(program)
        assert "hail" in result
        assert result.count("hail") == 1

    def test_no_solutions(self):
        h = HtnTestHelper()
        program = (
            "findSomething() :- if(first(item(?x), available(?x))), do(take(?x))."
            "take(?item) :- del(), add(taken(?item))."
            "goals(findSomething())."
        )
        result = h.find_first_plan(program)
        assert result == "null"

    def test_complex_conditions(self):
        h = HtnTestHelper()
        program = (
            "quickestRoute() :- if(first(location(?loc), reachable(?loc), travelTime(?loc, ?time), <(?time, 30))), do(goTo(?loc))."
            "location(downtown). location(uptown). location(suburb). location(airport). "
            "reachable(downtown). reachable(uptown). reachable(airport). "
            "travelTime(downtown, 45). travelTime(uptown, 25). travelTime(airport, 60). "
            "goTo(?loc) :- del(), add(wentTo(?loc))."
            "goals(quickestRoute())."
        )
        result = h.find_first_plan(program)
        assert "goTo(uptown)" in result


class TestTry:
    def test_successful_operation(self):
        h = HtnTestHelper()
        program = (
            "attemptTask() :- if(), do(try(riskyOperation))."
            "riskyOperation :- if(canSucceed), do(succeed)."
            "canSucceed. "
            "succeed :- del(), add(succeeded)."
            "goals(attemptTask())."
        )
        result = h.find_first_plan(program)
        assert "succeed" in result

    def test_failed_operation(self):
        h = HtnTestHelper()
        program = (
            "attemptWithFallback() :- if(), do(try(riskyOperation), fallbackOperation)."
            "riskyOperation :- if(canSucceed), do(succeed)."
            "succeed :- del(), add(succeeded)."
            "fallbackOperation :- del(), add(usedFallback)."
            "goals(attemptWithFallback())."
        )
        result = h.find_first_plan(program)
        assert "fallbackOperation" in result
        assert "succeed" not in result

    def test_nested_try_blocks(self):
        h = HtnTestHelper()
        program = (
            "complexOperation() :- if(), do(try(try(innerRisky), outerFallback), finalFallback)."
            "innerRisky :- if(innerCondition), do(innerSuccess)."
            "outerFallback :- if(outerCondition), do(outerSuccess)."
            "innerSuccess :- del(), add(innerDone)."
            "outerSuccess :- del(), add(outerDone)."
            "finalFallback :- del(), add(finalDone)."
            "goals(complexOperation())."
        )
        result = h.find_first_plan(program)
        assert "finalFallback" in result
        assert "innerSuccess" not in result
        assert "outerSuccess" not in result

    def test_with_multiple_subtasks(self):
        h = HtnTestHelper()
        program = (
            "multiStepProcess() :- if(), do(try(step1, step2, step3), recovery)."
            "step1 :- if(step1OK), do(doStep1)."
            "step2 :- if(step2OK), do(doStep2)."
            "step3 :- if(step3OK), do(doStep3)."
            "step1OK. step3OK. "
            "doStep1 :- del(), add(step1Done)."
            "doStep2 :- del(), add(step2Done)."
            "doStep3 :- del(), add(step3Done)."
            "recovery :- del(), add(recovered)."
            "goals(multiStepProcess())."
        )
        result = h.find_first_plan(program)
        assert "recovery" in result


class TestHiddenOperators:
    def test_not_in_plan(self):
        h = HtnTestHelper()
        program = (
            "doWork() :- if(), do(publicWork, privateWork)."
            "publicWork :- del(), add(publicDone)."
            "privateWork :- hidden, del(), add(privateDone)."
            "goals(doWork())."
        )
        result = h.find_first_plan(program)
        assert "publicWork" in result
        assert "privateWork" not in result

    def test_multiple_hidden(self):
        h = HtnTestHelper()
        program = (
            "setupSystem() :- if(), do(visibleSetup, hiddenInit, hiddenConfig, visibleFinish)."
            "visibleSetup :- del(), add(setupVisible)."
            "hiddenInit :- hidden, del(), add(initDone)."
            "hiddenConfig :- hidden, del(), add(configDone)."
            "visibleFinish :- del(), add(finishVisible)."
            "goals(setupSystem())."
        )
        result = h.find_first_plan(program)
        assert "visibleSetup" in result
        assert "visibleFinish" in result
        assert "hiddenInit" not in result
        assert "hiddenConfig" not in result


class TestElseKeyword:
    def test_basic_priority(self):
        h = HtnTestHelper()
        program = (
            "doAI(?player) :- if(enemyNearKing(?player)), do(defendKing(?player))."
            "doAI(?player) :- else, if(canAttack(?player)), do(attack(?player))."
            "doAI(?player) :- else, if(), do(wander(?player))."
            "canAttack(player1). "
            "defendKing(?p) :- del(), add(defending(?p))."
            "attack(?p) :- del(), add(attacking(?p))."
            "wander(?p) :- del(), add(wandering(?p))."
            "goals(doAI(player1))."
        )
        result = h.find_first_plan(program)
        assert "attack(player1)" in result
        assert "defending" not in result
        assert "wandering" not in result

    def test_highest_priority_takes_precedence(self):
        h = HtnTestHelper()
        program = (
            "chooseTactic(?player) :- if(criticalSituation(?player)), do(emergencyAction(?player))."
            "chooseTactic(?player) :- else, if(goodOpportunity(?player)), do(opportunisticAction(?player))."
            "chooseTactic(?player) :- else, if(), do(defaultAction(?player))."
            "criticalSituation(player1). goodOpportunity(player1). "
            "emergencyAction(?p) :- del(), add(emergency(?p))."
            "opportunisticAction(?p) :- del(), add(opportunistic(?p))."
            "defaultAction(?p) :- del(), add(default(?p))."
            "goals(chooseTactic(player1))."
        )
        result = h.find_first_plan(program)
        assert "emergencyAction" in result
        assert "opportunisticAction" not in result
        assert "defaultAction" not in result

    def test_fallback_chain(self):
        h = HtnTestHelper()
        program = (
            "selectAction() :- if(bestOption), do(bestAction)."
            "selectAction() :- else, if(goodOption), do(goodAction)."
            "selectAction() :- else, if(okayOption), do(okayAction)."
            "selectAction() :- else, if(), do(lastResort)."
            "bestAction :- del(), add(best)."
            "goodAction :- del(), add(good)."
            "okayAction :- del(), add(okay)."
            "lastResort :- del(), add(lastResort)."
            "goals(selectAction())."
        )
        result = h.find_first_plan(program)
        assert "lastResort" in result
        assert "best" not in result.replace("lastResort", "")
        assert "good" not in result.replace("lastResort", "")
        assert "okay" not in result.replace("lastResort", "")


class TestDocumentOrder:
    def test_without_else(self):
        h = HtnTestHelper()
        program = (
            "ambiguousTask() :- if(), do(firstMethod)."
            "ambiguousTask() :- if(), do(secondMethod)."
            "ambiguousTask() :- if(), do(thirdMethod)."
            "firstMethod :- del(), add(first)."
            "secondMethod :- del(), add(second)."
            "thirdMethod :- del(), add(third)."
            "goals(ambiguousTask())."
        )
        result = h.find_first_plan(program)
        assert "firstMethod" in result
        assert "secondMethod" not in result
        assert "thirdMethod" not in result


class TestIntegration:
    def test_complex_method_combinations(self):
        h = HtnTestHelper()
        # Test without highPriorityCondition - should use normal sequence
        program = (
            "executeComplexPlan() :- if(highPriorityCondition), do(try(criticalSequence, emergencyFallback))."
            "executeComplexPlan() :- else, if(), do(normalSequence)."
            "criticalSequence() :- anyOf, if(criticalValid(?c)), do(criticalSequence_routine(?c))."
            "normalSequence() :- if(first(option(?x), available(?x), cost(?x, ?c), <(?c, 10))), do(selectOption(?x))."
            "needA. needB. "
            "option(cheap). option(expensive). option(free). "
            "available(cheap). available(expensive). available(free). "
            "cost(free, 0). cost(cheap, 5). cost(expensive, 15). "
            "criticalValid(doA). criticalValid(doB)."
            "emergencyFallback :- del(), add(emergency)."
            "selectOption(?opt) :- del(), add(selected(?opt))."
            "criticalSequence_routine(?c) :- del(), add(?c)."
            "goals(executeComplexPlan())."
        )
        result = h.find_first_plan(program)
        assert "selectOption(cheap)" in result

    def test_complex_method_combinations_with_high_priority(self):
        h = HtnTestHelper()
        # Test WITH highPriorityCondition
        program = (
            "executeComplexPlan() :- if(highPriorityCondition), do(try(criticalSequence, emergencyFallback))."
            "executeComplexPlan() :- else, if(), do(normalSequence)."
            "criticalSequence() :- anyOf, if(criticalValid(?c)), do(criticalSequence_routine(?c))."
            "normalSequence() :- if(first(option(?x), available(?x), cost(?x, ?c), <(?c, 10))), do(selectOption(?x))."
            "needA. needB. "
            "option(cheap). option(expensive). option(free). "
            "available(cheap). available(expensive). available(free). "
            "cost(free, 0). cost(cheap, 5). cost(expensive, 15). "
            "criticalValid(doA). criticalValid(doB)."
            "emergencyFallback :- del(), add(emergency)."
            "selectOption(?opt) :- del(), add(selected(?opt))."
            "criticalSequence_routine(?c) :- del(), add(?c)."
            "highPriorityCondition. "
            "goals(executeComplexPlan())."
        )
        result = h.find_first_plan(program)
        assert "doA" in result
        assert "doB" in result

    def test_real_world_scenario(self):
        h = HtnTestHelper()
        program = (
            "unitAction(?unit) :- if(inCombat(?unit)), do(try(combatAction(?unit), retreatAction(?unit)))."
            "unitAction(?unit) :- else, if(canExplore(?unit)), do(exploreAction(?unit))."
            "unitAction(?unit) :- else, if(), do(idleAction(?unit))."
            "combatAction(?unit) :- anyOf, if(hasRangedWeapon(?unit), canAttackRanged(?unit)), do(rangedAttack(?unit))."
            "combatAction(?unit) :- anyOf, if(hasCloseWeapon(?unit), canAttackMelee(?unit)), do(meleeAttack(?unit))."
            "exploreAction(?unit) :- allOf, if(needSupplies(?unit)), do(gatherSupplies(?unit))."
            "exploreAction(?unit) :- allOf, if(needScout(?unit)), do(scoutAhead(?unit))."
            "exploreAction(?unit) :- allOf, if(), do(moveForward(?unit))."
            "inCombat(unit1). hasRangedWeapon(unit1). canAttackRanged(unit1). "
            "hasCloseWeapon(unit1). "
            "rangedAttack(?u) :- del(), add(attacked(?u, ranged))."
            "meleeAttack(?u) :- del(), add(attacked(?u, melee))."
            "retreatAction(?u) :- del(), add(retreated(?u))."
            "gatherSupplies(?u) :- del(), add(gatheredSupplies(?u))."
            "scoutAhead(?u) :- del(), add(scouted(?u))."
            "moveForward(?u) :- del(), add(moved(?u))."
            "idleAction(?u) :- del(), add(idle(?u))."
            "goals(unitAction(unit1))."
        )
        result = h.find_first_plan(program)
        assert "rangedAttack(unit1)" in result
        assert "meleeAttack" not in result
        assert "exploreAction" not in result
        assert "idle" not in result

    def test_error_recovery_chain(self):
        h = HtnTestHelper()
        program = (
            "robustOperation() :- if(), do(try(primaryMethod), try(secondaryMethod), try(tertiaryMethod))."
            "primaryMethod :- if(primaryCondition), do(primaryAction)."
            "secondaryMethod :- if(secondaryCondition), do(secondaryAction)."
            "tertiaryMethod :- if(), do(tertiaryAction)."
            "primaryAction :- del(), add(primary)."
            "secondaryAction :- del(), add(secondary)."
            "tertiaryAction :- del(), add(tertiary)."
            "goals(robustOperation())."
        )
        result = h.find_first_plan(program)
        assert "tertiaryAction" in result
        assert "primaryAction" not in result
        assert "secondaryAction" not in result
