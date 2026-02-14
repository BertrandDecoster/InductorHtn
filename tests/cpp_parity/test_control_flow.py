"""
Reproduces HtnPlannerTests_ControlFlow.cpp tests.
Tests: try, else, first, sortBy, not, and state.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
from conftest import HtnTestHelper


class TestPlannerTry:
    """Reproduces PlannerTryTest from HtnPlannerTests_ControlFlow.cpp"""

    def test_empty_try_should_work(self):
        h = HtnTestHelper()
        program = (
            "number(10).number(12).number(1). \r\n"
            "test() :- if(), do(try(successTask()), try(failTask()), try(failTask()), try(successTask(?Y)) ).\r\n"
            "failTask() :- if(<(2, 1)), do(debugWatch(fail)).\r\n"
            "successTask() :- if(<(1, 2)), do(debugWatch(success)).\r\n"
            "successTask(?X) :- if(number(?X)), do(debugWatch(?X)).\r\n"
            "debugWatch(?x) :- del(), add(item(?x)).\r\n"
            "goals(try(), successTask()).\r\n"
        )
        result = h.find_all_plans(program)
        assert result == "[ { (debugWatch(success)) } ]"
        facts = h.get_all_solution_facts()
        assert facts == "[ { number(10) => ,number(12) => ,number(1) => ,item(success) =>  } ]"

    def test_try_returns_all_successful_solutions(self):
        h = HtnTestHelper()
        program = (
            "IsTrue(Test1). IsTrue(Test2). Alternative(Alternative1). Alternative(Alternative2).\r\n"
            "trace(?Value, ?Value2, ?Value3) :- del(), add(item(?Value, ?Value2, ?Value3)). \r\n"
            "method(?Value) :- allOf, if(IsTrue(?Value), Alternative(?Alt)), do(trace(AllSet, ?Value, ?Alt)). \r\n"
            "method2(?Value) :- if(IsTrue(?Value), Alternative(?Alt)), do(trace(Normal, ?Value, ?Alt)). \r\n"
            "goals(try(method2(Test2))).\r\n"
        )
        result = h.find_all_plans(program)
        assert result == "[ { (trace(Normal,Test2,Alternative1)) } { (trace(Normal,Test2,Alternative2)) } ]"
        facts = h.get_all_solution_facts()
        assert facts == "[ { IsTrue(Test1) => ,IsTrue(Test2) => ,Alternative(Alternative1) => ,Alternative(Alternative2) => ,item(Normal,Test2,Alternative1) =>  } { IsTrue(Test1) => ,IsTrue(Test2) => ,Alternative(Alternative1) => ,Alternative(Alternative2) => ,item(Normal,Test2,Alternative2) =>  } ]"

    def test_try_followed_by_failed_normal_should_fail(self):
        h = HtnTestHelper()
        program = (
            "IsTrue(Test1). IsTrue(Test2). Alternative(Alternative1). Alternative(Alternative2).\r\n"
            "trace(?Value, ?Value2, ?Value3) :- del(), add(item(?Value, ?Value2, ?Value3)). \r\n"
            "method(?Value) :- allOf, if(IsTrue(?Value), Alternative(?Alt)), do(trace(AllSet, ?Value, ?Alt)). \r\n"
            "method2(?Value) :- if(IsTrue(?Value), Alternative(?Alt)), do(trace(Normal, ?Value, ?Alt)). \r\n"
            "goals(try(method(Test3)), method(Test3)).\r\n"
        )
        result = h.find_all_plans(program)
        assert result == "null"
        facts = h.get_all_solution_facts()
        assert facts == "null"

    def test_try_ignores_failure_transparent_to_success(self):
        h = HtnTestHelper()
        program = (
            "IsTrue(Test1). IsTrue(Test2). Alternative(Alternative1). Alternative(Alternative2).\r\n"
            "trace(?Value, ?Value2, ?Value3) :- del(), add(item(?Value, ?Value2, ?Value3)). \r\n"
            "method(?Value) :- allOf, if(IsTrue(?Value), Alternative(?Alt)), do(trace(AllSet, ?Value, ?Alt)). \r\n"
            "method2(?Value) :- if(IsTrue(?Value), Alternative(?Alt)), do(trace(Normal, ?Value, ?Alt)). \r\n"
            "goals(try(method(Test3)), try(method2(Test2))).\r\n"
        )
        result = h.find_all_plans(program)
        assert result == "[ { (trace(Normal,Test2,Alternative1)) } { (trace(Normal,Test2,Alternative2)) } ]"
        facts = h.get_all_solution_facts()
        assert facts == "[ { IsTrue(Test1) => ,IsTrue(Test2) => ,Alternative(Alternative1) => ,Alternative(Alternative2) => ,item(Normal,Test2,Alternative1) =>  } { IsTrue(Test1) => ,IsTrue(Test2) => ,Alternative(Alternative1) => ,Alternative(Alternative2) => ,item(Normal,Test2,Alternative2) =>  } ]"

    def test_try_ignores_failure_in_do_clause(self):
        h = HtnTestHelper()
        program = (
            "IsTrue(Test1). IsTrue(Test2). Alternative(Alternative1). Alternative(Alternative2).\r\n"
            "IsTrue(Test2, Alternative2). \r\n"
            "trace(?Value, ?Value2, ?Value3) :- del(), add(item(?Value, ?Value2, ?Value3)). \r\n"
            "method(?Value) :- anyOf, if(IsTrue(?Value), Alternative(?Alt)), do(trace(AllSet, ?Value, ?Alt)). \r\n"
            "method2(?Value) :- if(IsTrue(?Value), Alternative(?Alt)), do(trace(Method2, ?Value, ?Alt), try(method3(?Value, ?Alt))). \r\n"
            "method3(?Value, ?Alt) :- if(IsTrue(?Value, ?Alt)), do(trace(Normal, ?Value, ?Alt)). \r\n"
            "goals(method(Test1), method2(Test2)).\r\n"
        )
        result = h.find_all_plans(program)
        assert result == "[ { (trace(AllSet,Test1,Alternative1), trace(AllSet,Test1,Alternative2), trace(Method2,Test2,Alternative1)) } { (trace(AllSet,Test1,Alternative1), trace(AllSet,Test1,Alternative2), trace(Method2,Test2,Alternative2), trace(Normal,Test2,Alternative2)) } ]"
        facts = h.get_all_solution_facts()
        assert facts == "[ { IsTrue(Test1) => ,IsTrue(Test2) => ,Alternative(Alternative1) => ,Alternative(Alternative2) => ,IsTrue(Test2,Alternative2) => ,item(AllSet,Test1,Alternative1) => ,item(AllSet,Test1,Alternative2) => ,item(Method2,Test2,Alternative1) =>  } { IsTrue(Test1) => ,IsTrue(Test2) => ,Alternative(Alternative1) => ,Alternative(Alternative2) => ,IsTrue(Test2,Alternative2) => ,item(AllSet,Test1,Alternative1) => ,item(AllSet,Test1,Alternative2) => ,item(Method2,Test2,Alternative2) => ,item(Normal,Test2,Alternative2) =>  } ]"

    def test_try_ignores_failures_multiple_solutions(self):
        h = HtnTestHelper()
        program = (
            "number(10).number(12).number(1). \r\n"
            "test() :- if(), do(try(successTask()), try(failTask()), try(failTask()), try(successTask(?Y)) ).\r\n"
            "failTask() :- if(<(2, 1)), do(debugWatch(fail)).\r\n"
            "successTask() :- if(<(1, 2)), do(debugWatch(success)).\r\n"
            "successTask(?X) :- if(number(?X)), do(debugWatch(?X)).\r\n"
            "debugWatch(?x) :- del(), add(item(?x)).\r\n"
            "goals(test()).\r\n"
        )
        result = h.find_all_plans(program)
        assert result == "[ { (debugWatch(success), debugWatch(10)) } { (debugWatch(success), debugWatch(12)) } { (debugWatch(success), debugWatch(1)) } ]"
        facts = h.get_all_solution_facts()
        assert facts == "[ { number(10) => ,number(12) => ,number(1) => ,item(success) => ,item(10) =>  } { number(10) => ,number(12) => ,number(1) => ,item(success) => ,item(12) =>  } { number(10) => ,number(12) => ,number(1) => ,item(success) => ,item(1) =>  } ]"


class TestPlannerElse:
    """Reproduces PlannerElseTest from HtnPlannerTests_ControlFlow.cpp"""

    def test_subtask_fails_backtrack_to_else(self):
        h = HtnTestHelper()
        program = (
            "test() :- if(), do(failTask()).\r\n"
            "test() :- else, if(), do(success()).\r\n"
            "failTask() :- if( <(2,1) ), do().\r\n"
            "success() :- del(), add(item(success)).\r\n"
            "goals(test())."
        )
        result = h.find_all_plans(program)
        assert result == "[ { (success) } ]"
        facts = h.get_all_solution_facts()
        assert facts == "[ { item(success) =>  } ]"

    def test_allof_subtask_fails_backtrack_to_else(self):
        h = HtnTestHelper()
        program = (
            "test() :- allOf, if(), do(failTask()).\r\n"
            "test() :- else, if(), do(success()).\r\n"
            "failTask() :- if( <(2,1) ), do().\r\n"
            "success() :- del(), add(item(success)).\r\n"
            "goals(test())."
        )
        result = h.find_all_plans(program)
        assert result == "[ { (success) } ]"
        facts = h.get_all_solution_facts()
        assert facts == "[ { item(success) =>  } ]"

    def test_anyof_all_fail_backtrack_to_else(self):
        h = HtnTestHelper()
        program = (
            "test() :- anyOf, if(), do(failTask()).\r\n"
            "test() :- else, if(), do(elseSuccess()).\r\n"
            "failTask() :- if( <(2,1) ), do(success()).\r\n"
            "success() :- del(), add(item(success)).\r\n"
            "elseSuccess() :- del(), add(item(elseEuccess)).\r\n"
            "goals(test())."
        )
        result = h.find_all_plans(program)
        assert result == "[ { (elseSuccess) } ]"
        facts = h.get_all_solution_facts()
        assert facts == "[ { item(elseEuccess) =>  } ]"

    def test_anyof_one_succeeds_no_else(self):
        h = HtnTestHelper()
        program = (
            "test() :- anyOf, if(unit(?X)), do(success()).\r\n"
            "test() :- else, if(), do(elseSuccess()).\r\n"
            "success() :- del(), add(item(success)).\r\n"
            "elseSuccess() :- del(), add(item(elseEuccess)).\r\n"
            "unit(Queen). \r\n"
            "goals(test())."
        )
        result = h.find_all_plans(program)
        assert result == "[ { (success) } ]"
        facts = h.get_all_solution_facts()
        assert facts == "[ { unit(Queen) => ,item(success) =>  } ]"

    def test_anyof_at_least_one_succeeds_no_else(self):
        h = HtnTestHelper()
        program = (
            "test() :- anyOf, if(unit(?X)), do(failTask(?X)).\r\n"
            "test() :- else, if(), do(elseSuccess()).\r\n"
            "failTask(?Unit) :- if( shouldWork(?Unit) ), do(success()).\r\n"
            "success() :- del(), add(item(success)).\r\n"
            "elseSuccess() :- del(), add(item(elseEuccess)).\r\n"
            "unit(Queen). \r\n"
            "unit(Worker). \r\n"
            "shouldWork(Queen). \r\n"
            "goals(test())."
        )
        result = h.find_all_plans(program)
        assert result == "[ { (success) } ]"
        facts = h.get_all_solution_facts()
        assert facts == "[ { unit(Queen) => ,unit(Worker) => ,shouldWork(Queen) => ,item(success) =>  } ]"


class TestPlannerFirstSortByNot:
    """Reproduces PlannerFirstSortByNot from HtnPlannerTests_ControlFlow.cpp"""

    def test_first_with_terms_after(self):
        h = HtnTestHelper()
        program = (
            "test() :- if( first(number(?A)), is(?B, +(?A, ?A)) ), do(debugWatch(?B)).\r\n"
            "debugWatch(?x) :- del(), add(item(?x)).\r\n"
            "number(10).number(12).number(1). \r\n"
            "goals(test())."
        )
        result = h.find_all_plans(program)
        assert result == "[ { (debugWatch(20)) } ]"
        facts = h.get_all_solution_facts()
        assert facts == "[ { number(10) => ,number(12) => ,number(1) => ,item(20) =>  } ]"

    def test_sort_by_ascending(self):
        h = HtnTestHelper()
        program = (
            "test() :- if( sortBy(?A, <(number(?A))) ), do(debugWatch(?A)).\r\n"
            "debugWatch(?x) :- del(), add(item(?x)).\r\n"
            "number(10).number(12).number(0). \r\n"
            "goals(test())."
        )
        result = h.find_all_plans(program)
        assert result == "[ { (debugWatch(0)) } { (debugWatch(10)) } { (debugWatch(12)) } ]"
        facts = h.get_all_solution_facts()
        assert facts == "[ { number(10) => ,number(12) => ,number(0) => ,item(0) =>  } { number(10) => ,number(12) => ,number(0) => ,item(10) =>  } { number(10) => ,number(12) => ,number(0) => ,item(12) =>  } ]"

    def test_variables_from_head_not_in_if(self):
        h = HtnTestHelper()
        program = (
            "test(?C) :- if( first( sortBy(?A, <(number(?A)))), is(?B, +(?A, ?A)) ), do(debugWatch(?C)).\r\n"
            "debugWatch(?x) :- del(), add(item(?x)).\r\n"
            "number(10).number(12).number(1). \r\n"
            "goals(test(99))."
        )
        result = h.find_all_plans(program)
        assert result == "[ { (debugWatch(99)) } ]"
        facts = h.get_all_solution_facts()
        assert facts == "[ { number(10) => ,number(12) => ,number(1) => ,item(99) =>  } ]"

    def test_first_and_sortby_with_terms_after(self):
        h = HtnTestHelper()
        program = (
            "test() :- if( first( sortBy(?A, <(number(?A)))), is(?B, +(?A, ?A)) ), do(debugWatch(?B)).\r\n"
            "debugWatch(?x) :- del(), add(item(?x)).\r\n"
            "number(10).number(12).number(1). \r\n"
            "goals(test())."
        )
        result = h.find_all_plans(program)
        assert result == "[ { (debugWatch(2)) } ]"
        facts = h.get_all_solution_facts()
        assert facts == "[ { number(10) => ,number(12) => ,number(1) => ,item(2) =>  } ]"

    def test_not(self):
        h = HtnTestHelper()
        program = (
            "test() :- if( person(?X), not(isFunny(?X)) ), do(debugWatch(?X)).\r\n"
            "debugWatch(?x) :- del(), add(item(?x)).\r\n"
            "person(Jim).person(Mary).isFunny(Mary). \r\n"
            "goals(test())."
        )
        result = h.find_all_plans(program)
        assert result == "[ { (debugWatch(Jim)) } ]"
        facts = h.get_all_solution_facts()
        assert facts == "[ { person(Jim) => ,person(Mary) => ,isFunny(Mary) => ,item(Jim) =>  } ]"
